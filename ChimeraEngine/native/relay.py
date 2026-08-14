# SPIACE native relay — stdlib only. Serves the viewer HTML and streams the
# C++ core's NDJSON frames to it over Server-Sent Events.
#
#   python relay.py [tick_ms] [port]
#
# The exe is spawned lazily on the FIRST /stream connection (the sim starts
# when a viewer arrives), and every frame is also appended to
# native_stream.log — the Playwright oracle reads that file and recomputes
# the blueprint independently (the wire itself is under test, not just the
# page's belief about it).

import json
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXE = HERE / "ca_core.exe"
VIEWER = HERE.parent / "engine" / "spiace_native.html"
LOG = HERE / "native_stream.log"

TICK_MS = sys.argv[1] if len(sys.argv) > 1 else "30"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 8799

frames = []                 # full replay buffer (a wall is 210 cells; tiny)
frames_cv = threading.Condition()
proc = None
proc_lock = threading.Lock()


def ensure_proc():
    global proc
    with proc_lock:
        if proc is not None:
            return
        LOG.write_text("", encoding="utf-8")
        proc = subprocess.Popen([str(EXE), TICK_MS], stdout=subprocess.PIPE,
                                text=True, bufsize=1)
        threading.Thread(target=reader, daemon=True).start()


def reader():
    for line in proc.stdout:
        line = line.strip()
        if not line:
            continue
        with frames_cv:
            frames.append(line)
            frames_cv.notify_all()
        with LOG.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    with frames_cv:           # EOF marker so late joiners see the end
        frames.append("")
        frames_cv.notify_all()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        if self.path == "/" or self.path.startswith("/?"):
            body = VIEWER.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path.startswith("/stream"):
            ensure_proc()
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()
            idx = 0
            try:
                while True:
                    with frames_cv:
                        while idx >= len(frames):
                            frames_cv.wait(timeout=30)
                            if idx >= len(frames):
                                self.wfile.write(b": keepalive\n\n")
                                self.wfile.flush()
                        line = frames[idx]
                        idx += 1
                    if line == "":      # core exited
                        return
                    self.wfile.write(f"data: {line}\n\n".encode())
                    self.wfile.flush()
                    if json.loads(line).get("done"):
                        return
            except (BrokenPipeError, ConnectionResetError):
                return
            return
        self.send_response(404)
        self.end_headers()


if __name__ == "__main__":
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"relay on http://127.0.0.1:{PORT}  (tick {TICK_MS} ms)", flush=True)
    srv.serve_forever()
