"""game_shell/server.py -- THE GAME FRONT DOOR (R2).

One small stdlib server: serves the game page, proxies the world's
channels (frame/state/touch/pose) to the engine, and keeps each
player's progress in progress/<name>.json. The engine stays the frozen
world; this file is the doorplate, the doormat, and the sign-up sheet.

Run:  python tools/game_shell/server.py [port]   (default 8206)
Requires the engine on 127.0.0.1:8107 (launch_chimera.bat).
"""
from __future__ import annotations

import json
import re
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = "http://127.0.0.1:8107"
PROGRESS = HERE / "progress"
PROGRESS.mkdir(exist_ok=True)
NAME_RE = re.compile(r"[^A-Za-z0-9_\- ]+")


class Handler(BaseHTTPRequestHandler):
    engine_url = ENGINE

    def log_message(self, *a):  # quiet: the game page polls fast
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

    def _proxy(self, path: str, method: str, body: bytes | None):
        req = urllib.request.Request(ENGINE + path, data=body, method=method,
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                self._send(r.read(), r.headers.get("Content-Type", "application/json"))
        except Exception as e:
            self._json({"ok": False, "error": f"world unreachable: {e}"}, 502)

    # -- verbs ------------------------------------------------------------
    def do_GET(self):
        p = self.path.split("?", 1)[0]
        if p == "/" or p == "/index.html":
            self._send((HERE / "index.html").read_bytes(), "text/html")
        elif p == "/api/state":
            self._proxy("/tick_state", "GET", None)
        elif p == "/api/frame":
            self._proxy("/frame", "GET", None)
        elif p == "/api/progress":
            name = NAME_RE.sub("", self.path.split("?", 1)[1].replace("name=", "")
                               if "?" in self.path else "")[:32]
            f = PROGRESS / f"{name}.json"
            if name and f.exists():
                self._send(f.read_bytes(), "application/json")
            else:
                self._json({"name": name, "lessons": {}})
        elif p == "/api/health":
            self._json({"ok": True, "t": time.time()})

    def do_POST(self):
        p = self.path.split("?", 1)[0]
        n = int(self.headers.get("Content-Length", 0) or 0)
        body = self.rfile.read(n) if n else None
        if p in ("/api/touch", "/api/touch_clear", "/api/pose"):
            self._proxy({"/api/touch": "/tick_touch",
                         "/api/touch_clear": "/tick_touch_clear",
                         "/api/pose": "/tick_pose"}[p], "POST", body)
        elif p == "/api/progress":
            try:
                data = json.loads(body or b"{}")
                name = NAME_RE.sub("", str(data.get("name", "")))[:32].strip()
                if not name:
                    self._json({"ok": False, "error": "a name is required"}, 400)
                    return
                data["name"] = name
                data["saved_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
                (PROGRESS / f"{name}.json").write_text(json.dumps(data, indent=1))
                self._json({"ok": True})
            except Exception as e:
                self._json({"ok": False, "error": str(e)}, 400)


def main() -> None:
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8206
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.daemon_threads = True
    print(f"THE GAME -- http://127.0.0.1:{port}  (world: {ENGINE})", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
