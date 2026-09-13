"""website/server.py -- THE PUBLIC FRONT DOOR (R9).

One small stdlib server: serves the landing page and the folder's
static files, takes sign-ups (name + email) as one honest JSON line
apiece in signups.jsonl, and counts them back for the page's
"join N explorers" line. No store, no gate -- a stranger plays the
free demo first and signs up afterwards.

Run:  python tools/website/server.py [port]   (default 8210)
The PLAY THE DEMO button expects the game shell on 127.0.0.1:8206.
"""
from __future__ import annotations

import json
import mimetypes
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
SIGNUPS = HERE / "signups.jsonl"

TEXT_TYPES = ("text/", "application/javascript", "application/json")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):  # quiet: the page reads the count on load
        pass

    # -- helpers ----------------------------------------------------------
    def _send(self, body: bytes, ctype: str, code: int = 200):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, code: int = 200):
        self._send(json.dumps(obj).encode(), "application/json", code)

    def _serve_file(self, rel: str):
        f = (HERE / rel).resolve()
        if HERE not in f.parents or not f.is_file():
            self._send(b"not found", "text/plain; charset=utf-8", 404)
            return
        ctype = mimetypes.guess_type(f.name)[0] or "application/octet-stream"
        if ctype.startswith(TEXT_TYPES):
            ctype += "; charset=utf-8"
        self._send(f.read_bytes(), ctype)

    # -- verbs ------------------------------------------------------------
    def do_GET(self):
        p = self.path.split("?", 1)[0]
        if p in ("/", "/index.html"):
            self._serve_file("index.html")
        elif p == "/api/signups/count":
            n = 0
            if SIGNUPS.exists():
                with SIGNUPS.open("rb") as f:
                    n = sum(1 for line in f if line.strip())
            self._json({"count": n})
        elif p == "/api/health":
            self._json({"ok": True, "t": time.time()})
        else:
            self._serve_file(p.lstrip("/"))

    def do_POST(self):
        p = self.path.split("?", 1)[0]
        if p != "/api/signup":
            self._json({"ok": False, "error": "no such door"}, 404)
            return
        n = int(self.headers.get("Content-Length", 0) or 0)
        try:
            data = json.loads(self.rfile.read(n) if n else b"{}")
        except Exception:
            self._json({"ok": False, "error": "that did not read as JSON"}, 400)
            return
        name = str(data.get("name", "")).strip()
        email = str(data.get("email", "")).strip()
        if not 1 <= len(name) <= 32:
            self._json({"ok": False, "error": "a name of 1 to 32 letters, please"}, 400)
            return
        if "@" not in email or "." not in email:
            self._json({"ok": False, "error": "that email does not look quite right"}, 400)
            return
        # simple append: a returning email earns a second line, honestly
        line = json.dumps({"name": name, "email": email,
                           "at": time.strftime("%Y-%m-%d %H:%M:%S")})
        with SIGNUPS.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
        self._json({"ok": True})


def main() -> None:
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8210
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.daemon_threads = True
    print(f"THE FRONT DOOR -- http://127.0.0.1:{port}  (game shell: 8206)", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
