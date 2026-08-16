# SPIACE native relay — stdlib only. Serves the viewer HTML and streams the
# C++ core's NDJSON frames to it over Server-Sent Events.
#
#   python relay.py [tick_ms] [port] [genome.chimera]
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

TICK_MS = sys.argv[1] if len(sys.argv) > 1 else "30"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 8799
GENOME = sys.argv[3] if len(sys.argv) > 3 else str(HERE / "genomes" / "wall.chimera")

# per-port wire log: the test harness runs several relays in sequence; a shared
# log let a dying relay's late writes interleave with the next relay's stream
# (torn NDJSON line → JSONDecodeError in F-N8e's wire audit)
LOG = HERE / f"native_stream_{PORT}.log"

frames = []                 # full replay buffer (a wall is 210 cells; tiny)
frames_cv = threading.Condition()
proc = None
proc_lock = threading.RLock()
gen = 0                      # generation: bumped on every (re)spawn so a stale
                            # reader thread never injects its EOF marker


def spawn_proc(genome_path):
    """(re)spawn the core with the given genome. Same spawn the startup uses,
    exposed so the viewer can switch genomes at runtime (the genome is data;
    the core is the reader). Plumbing only — never touches ca_core physics."""
    global proc, gen
    with proc_lock:
        if proc is not None and proc.poll() is None:
            try:
                proc.terminate()
                proc.wait(timeout=2)
            except Exception:
                pass
        gen += 1
        frames.clear()
        LOG.write_text("", encoding="utf-8")
        proc = subprocess.Popen([str(EXE), TICK_MS, genome_path],
                                 stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE, text=True, bufsize=1)
        threading.Thread(target=reader, daemon=True).start()


def ensure_proc():
    global proc
    with proc_lock:
        if proc is not None:
            return
        spawn_proc(GENOME)


def reader():
    my_gen = gen
    for line in proc.stdout:
        line = line.strip()
        if not line:
            continue
        with frames_cv:
            if my_gen != gen:      # a newer spawn superseded this reader
                return
            frames.append(line)
            frames_cv.notify_all()
        with LOG.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    with frames_cv:           # EOF marker so late joiners see the end
        if my_gen == gen:     # only if this reader is still the current one
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
                    m = json.loads(line)
                    # cut only on a growth FRAME's done — embodiment genomes
                    # keep streaming anim frames after the final ledger
                    if m.get("type") == "frame" and m.get("done"):
                        return
            except (BrokenPipeError, ConnectionResetError):
                return
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        if self.path.startswith("/cmd"):
            n = int(self.headers.get("Content-Length") or 0)
            cmd = self.rfile.read(n).decode().strip()
            # genome switch (runtime reload): the viewer posts "genome:<name>"
            # and the relay respawns the core on that genome file. SAME spawn
            # the startup uses — the genome is data, the core is the reader.
            if cmd.startswith("genome:"):
                name = cmd[len("genome:"):].strip()
                if not name:
                    name = GENOME
                path = name if name.endswith(".chimera") else str(HERE / "genomes" / (name + ".chimera"))
                if not Path(path).exists():
                    self.send_response(404)
                    self.end_headers()
                    return
                spawn_proc(path)
                self.send_response(204)
                self.end_headers()
                return
            with proc_lock:
                live = proc is not None and proc.poll() is None
                if live and cmd:
                    try:
                        proc.stdin.write(cmd + "\n")
                        proc.stdin.flush()
                        self.send_response(204)
                    except (BrokenPipeError, OSError):
                        self.send_response(503)
                else:
                    self.send_response(503)
            self.end_headers()
            return
        self.send_response(404)
        self.end_headers()


if __name__ == "__main__":
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"relay on http://127.0.0.1:{PORT}  (tick {TICK_MS} ms)", flush=True)
    srv.serve_forever()
