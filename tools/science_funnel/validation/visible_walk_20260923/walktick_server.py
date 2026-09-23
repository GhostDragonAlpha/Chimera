"""walktick_server.py v2 -- raw-socket HTTP/1.1 keep-alive server.

Same routes as v1; /walktick serves a zero-copy memoryview slice of the
packed tick file (no bytes() round trip), headers preformatted.
"""
import json
import mmap
import socket
import sys
import threading
import time
import urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent
SLICE = HERE.parents[3] / "tools" / "playable_slice"
DUMP = HERE.parents[3] / ".tmp" / "viswalk_dump"
LOG = open(HERE / "walktick_serves.log", "w", encoding="utf-8")
LOGLOCK = threading.Lock()

REST = HERE / "rest_stream.bin"
rest_bytes = REST.read_bytes()
POS = json.loads("{}")
PACKED_F = (DUMP / "packed_ticks.bin").open("rb")
PACKED = mmap.mmap(PACKED_F.fileno(), 0, access=mmap.ACCESS_READ)
NV = struct_unpack = int.from_bytes(PACKED[:4], "little")
STRIDE = 4 + NV * 36
NT = len(PACKED) // STRIDE

STATIC = {
    "/": ("text/html", (SLICE / "index.html").read_bytes()),
    "/index.html": ("text/html", (SLICE / "index.html").read_bytes()),
    "/standing_body.glb": ("application/octet-stream",
                           (SLICE / "standing_body.glb").read_bytes()),
    "/ghost.obj": ("text/plain", (SLICE / "ghost_standing.obj").read_bytes()),
    "/mock_registry.json": ("application/json",
                            (SLICE / "mock_registry.json").read_bytes()),
}
API_JSON = {
    "/api/health": b'{"world_booted":true}',
    "/api/status": b'{"scene":{"settled":true},"engine_state":{"root_y":0.124641,"gravity_on":true}}',
}


def serve_body(conn, ctype, body):
    if isinstance(body, memoryview):
        n = len(body)
    else:
        n = len(body)
    hdr = ("HTTP/1.1 200 OK\r\nContent-Type: %s\r\nContent-Length: %d\r\n"
           "Connection: keep-alive\r\n\r\n" % (ctype, n)).encode()
    conn.sendall(hdr)
    conn.sendall(body)


def serve_tick(conn, n, query):
    n = max(0, min(NT - 1, n))
    mv = memoryview(PACKED)[n * STRIDE:(n + 1) * STRIDE]
    with LOGLOCK:
        LOG.write("%d %.6f %d\n" % (n, time.perf_counter(), STRIDE))
        LOG.flush()
    serve_body(conn, "application/octet-stream", mv)


def handle(conn):
    conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    buf = b""
    try:
        while True:
            while b"\r\n\r\n" not in buf:
                chunk = conn.recv(65536)
                if not chunk:
                    return
                buf += chunk
            head, _, buf = buf.partition(b"\r\n\r\n")
            line = head.split(b"\r\n")[0].decode("latin-1")
            parts = line.split(" ")
            if len(parts) < 2:
                return
            path_q = parts[1]
            if parts[0] == "POST":
                cl = 0
                for h in head.split(b"\r\n")[1:]:
                    if h.lower().startswith(b"content-length:"):
                        cl = int(h.split(b":")[1])
                if cl:
                    need = cl - len(buf)
                    if need > 0:
                        buf += conn.recv(min(need, 1 << 20))
                    buf = buf[cl:]
                conn.sendall(b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n"
                             b"Content-Length: 2\r\nConnection: keep-alive\r\n\r\n{}")
                continue
            p = urllib.parse.urlparse(path_q)
            path, q = p.path, urllib.parse.parse_qs(p.query)
            try:
                if path == "/api/verts":
                    serve_body(conn, "application/octet-stream", rest_bytes)
                elif path in API_JSON:
                    serve_body(conn, "application/json", API_JSON[path])
                elif path == "/walktick":
                    serve_tick(conn, int(q.get("n", ["0"])[0]), q)
                elif path in STATIC:
                    serve_body(conn, STATIC[path][0], STATIC[path][1])
                else:
                    conn.sendall(b"HTTP/1.1 404 Not Found\r\nContent-Length: 0"
                                 b"\r\nConnection: keep-alive\r\n\r\n")
            except (BrokenPipeError, ConnectionResetError, OSError):
                return
    except (BrokenPipeError, ConnectionResetError, OSError, socket.timeout):
        pass
    finally:
        try:
            conn.close()
        except OSError:
            pass


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8247
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", port))
    srv.listen(16)
    print("raw server on %d ticks=%d verts=%d stride=%d" % (port, NT, NV, STRIDE),
          flush=True)
    while True:
        conn, _ = srv.accept()
        threading.Thread(target=handle, args=(conn,), daemon=True).start()


if __name__ == "__main__":
    main()
