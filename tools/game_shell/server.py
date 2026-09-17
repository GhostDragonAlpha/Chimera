"""game_shell/server.py -- THE GAME FRONT DOOR (R2).

One small stdlib server: serves the game page, proxies the world's
channels (frame/state/touch/pose) to the engine, and keeps each
player's progress in progress/<name>.json. The engine stays the frozen
world; this file is the doorplate, the doormat, and the sign-up sheet.

Run:  python tools/game_shell/server.py [port] [--host H] [--engine URL]
      (default port 8206; default host 127.0.0.1 -- pass --host 0.0.0.0
      ONLY when you mean to serve the public; see docs/DEPLOY_RUNBOOK.md)
The world's URL is CHIMERA_ENGINE_URL (or --engine), default
http://127.0.0.1:8107 -- scratch shells for other agents point the env
var at their own private engine and never touch the live one.

Hardening (public deployment):
  --host    binds 127.0.0.1 unless 0.0.0.0 is passed explicitly.
  limits    one token bucket per (player IP, class). The game page polls
            /api/verts at 3 Hz and /api/state at ~1.4 Hz -- 264 req/min
            for ONE player -- and the page now backs off exponentially on
            any failed poll (H7), so a starving client slows itself down
            instead of hammering.
            THE SHARED-NAT TRADEOFF (H7, chosen deliberately): the bucket
            stays keyed per IP -- NOT per session -- so a stranger cannot
            mint unlimited sessions to bypass the budget; the price is
            that one home IP is one bucket. Stream class raised
            600 -> 1200 req/min (burst 480), which serves ~4 honest
            players behind one router (4 x 264 = 1056 < 1200) 429-free.
            The cost of raising it: a single hammering client may pull
            1200 req/min INTO THIS PROXY -- it never reaches the engine
            at more than that rate, and backoff makes the hammering
            self-defeating. 429 answers carry Retry-After.
  bodies    request bodies are capped at 5 MB (413, connection closed,
            body never read).
  paths     exact-name dispatch only; the progress name is stripped to
            [A-Za-z0-9_- ] so it cannot walk out of progress/; unknown
            paths get a real 404 (they used to get silence).
"""
from __future__ import annotations

import json
import os
import re
import threading
import time
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = os.environ.get("CHIMERA_ENGINE_URL", "http://127.0.0.1:8107").rstrip("/")
PROGRESS = HERE / "progress"
PROGRESS.mkdir(exist_ok=True)
NAME_RE = re.compile(r"[^A-Za-z0-9_\- ]+")

# -- hardening: numbers with reasons --------------------------------------
# stream 1200 req/min: the measured gameplay poll is verts 3 Hz + state
#         1.4 Hz = 264 req/min per player. 1200/min keeps FOUR real
#         players behind one home NAT (shared IP bucket) 429-free while
#         still shedding a hammering client before it reaches the engine
#         proxy; the page's own backoff (H7) is the first line of defense.
# api      30 req/min: health/topology/cam/progress -- a handful per
#         session; 30/min is many times that, and a for-loop is not a
#         session.
# static  120 req/min: page + sound.js + lessons.json per load.
RATE_LIMITS = {  # class -> (per minute, burst)
    "stream": (1200, 480),
    "api": (30, 15),
    "static": (120, 60),
}
STREAM_PATHS = {"/api/verts", "/api/state", "/api/frame", "/api/topology",
                "/api/touch", "/api/touch_clear", "/api/touch_hit",
                "/api/pose", "/api/gravity"}
MAX_BODY = 5 * 1024 * 1024   # no honest request body here is bigger

_BUCKETS: dict = {}          # (ip, class) -> (tokens left, last seen)
_BUCKET_LOCK = threading.Lock()


def _rate_class(path: str) -> str:
    if path.startswith("/api/"):
        return "stream" if path in STREAM_PATHS else "api"
    return "static"


def _allow(ip: str, path: str) -> bool:
    """Consume one token from this IP's bucket. False = over the limit."""
    cls = _rate_class(path)
    rate, burst = RATE_LIMITS[cls]
    now = time.monotonic()
    with _BUCKET_LOCK:
        if len(_BUCKETS) > 4096:  # memory cap: drop buckets idle 10 min
            for k in [k for k, v in _BUCKETS.items() if now - v[1] > 600]:
                del _BUCKETS[k]
        tokens, last = _BUCKETS.get((ip, cls), (float(burst), now))
        tokens = min(float(burst), tokens + (now - last) * rate / 60.0)
        ok = tokens >= 1.0
        _BUCKETS[(ip, cls)] = (tokens - 1.0 if ok else tokens, now)
        return ok


class Handler(BaseHTTPRequestHandler):
    engine_url = ENGINE
    # do not advertise the interpreter to every stranger
    server_version = "ChimeraR2"
    sys_version = ""

    def log_message(self, *a):  # quiet: the game page polls fast
        pass

    # -- helpers ----------------------------------------------------------
    def _client_ip(self) -> str:
        """The IP the buckets key on. Behind a LOCAL tunnel (cloudflared,
        ngrok, ssh -R) every visitor's socket peer is 127.0.0.1, so only
        for loopback peers do we read the forwarded header the tunnel
        itself wrote (Cloudflare overwrites CF-Connecting-IP; a direct
        remote client can never be loopback, so it cannot spoof this)."""
        peer = self.client_address[0]
        if peer in ("127.0.0.1", "::1"):
            real = (self.headers.get("CF-Connecting-IP")
                    or self.headers.get("X-Forwarded-For", ""))
            if real:
                return real.split(",")[0].strip()
        return peer

    def _send(self, body: bytes, ctype: str, code: int = 200,
              close: bool = False):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        if close:  # a rejected request's unread body would poison the pipe
            self.send_header("Connection", "close")
            self.close_connection = True
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, code: int = 200):
        self._send(json.dumps(obj).encode(), "application/json", code)

    def _deny(self, code: int, msg: str):
        """H7: rejections carry Retry-After so a backoff-capable client
        (the game page is, since the D6 fix) waits instead of hammering."""
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(json.dumps({"ok": False, "error": msg}).encode())))
        self.send_header("Retry-After", "1")
        self.send_header("Connection", "close")
        self.close_connection = True
        self.end_headers()
        self.wfile.write(json.dumps({"ok": False, "error": msg}).encode())

    def _proxy(self, path: str, method: str, body: bytes | None):
        req = urllib.request.Request(self.engine_url + path, data=body, method=method,
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                self._send(r.read(), r.headers.get("Content-Type", "application/json"))
        except Exception as e:
            self._json({"ok": False, "error": f"world unreachable: {e}"}, 502)

    # -- verbs ------------------------------------------------------------
    def do_GET(self):
        p = self.path.split("?", 1)[0]
        if not _allow(self._client_ip(), p):
            self._deny(429, "too many requests -- slow down")
            return
        if p == "/" or p == "/index.html":
            self._send((HERE / "index.html").read_bytes(), "text/html")
        elif p == "/api/state":
            self._proxy("/tick_state", "GET", None)
        elif p in ("/api/topology", "/api/verts"):
            # THE WEB KERNEL: state for the browser's own renderer. The
            # query rides through (C3's ?delta=1 / ?delta=key stream).
            tgt = {"/api/topology": "/topology", "/api/verts": "/verts"}[p]
            q = self.path.split("?", 1)[1] if "?" in self.path else ""
            self._proxy(tgt + (("?" + q) if q else ""), "GET", None)
        elif p == "/api/frame":
            q = self.path.split("?", 1)[1] if "?" in self.path else ""
            self._proxy("/frame" + (("?" + q) if q else ""), "GET", None)
        elif p == "/api/cam":
            # the live camera, read through /project's cam echo; set through
            # the bookmark save/recall pair (the engine's own discipline)
            if method(self) == "GET":
                req = urllib.request.Request(
                    self.engine_url + "/project",
                    data=json.dumps({"x": 0, "y": 0, "z": 0}).encode(),
                    method="POST", headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=15) as r:
                    self._send(r.read(), "application/json")
            else:
                n = int(self.headers.get("Content-Length", 0) or 0)
                data = json.loads(self.rfile.read(n) if n else b"{}")
                v = data.get("v", [])
                if len(v) != 8:
                    self._json({"ok": False, "error": "need v[8]"}, 400)
                    return
                save = json.dumps({"op": "save", "name": "__game__", "v": v}).encode()
                urllib.request.urlopen(urllib.request.Request(
                        self.engine_url + "/cameras", data=save, method="POST",
                        headers={"Content-Type": "application/json"}), timeout=15)
                rec = json.dumps({"op": "recall", "name": "__game__"}).encode()
                with urllib.request.urlopen(urllib.request.Request(
                        self.engine_url + "/cameras", data=rec, method="POST",
                        headers={"Content-Type": "application/json"}), timeout=15) as r:
                    self._send(r.read(), "application/json")
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
        elif p in ("/sound.js", "/lessons.json"):
            # static game assets (containment: exact names only)
            f = HERE / p.lstrip("/")
            if f.exists():
                ctype = "application/javascript" if f.suffix == ".js" else "application/json"
                self._send(f.read_bytes(), ctype)
            else:
                self._json({"ok": False, "error": "not found"}, 404)
        else:
            self._json({"ok": False, "error": "not found"}, 404)

    def do_POST(self):
        p = self.path.split("?", 1)[0]
        try:
            n = int(self.headers.get("Content-Length", 0) or 0)
        except ValueError:
            n = -1
        if n < 0 or n > MAX_BODY:
            self._deny(413, "body too large")
            return
        if not _allow(self._client_ip(), p):
            self._deny(429, "too many requests -- slow down")
            return
        body = self.rfile.read(n) if n else None
        # W1 (R4): /api/gravity joins the pose pattern -- the page's own
        # gravity verb for the_stand, proxied to the engine's /tick_gravity.
        if p in ("/api/touch", "/api/touch_clear", "/api/pose", "/api/touch_hit",
                 "/api/gravity"):
            self._proxy({"/api/touch": "/tick_touch",
                         "/api/touch_clear": "/tick_touch_clear",
                         "/api/pose": "/tick_pose",
                         "/api/touch_hit": "/tick_touch",
                         "/api/gravity": "/tick_gravity"}[p], "POST", body)
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
        else:
            self._json({"ok": False, "error": "no such door"}, 404)


def method(h) -> str:
    return h.command


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(description="Chimera game front door (R2)")
    ap.add_argument("port", nargs="?", type=int, default=8206)
    ap.add_argument("--host", default="127.0.0.1",
                    help="bind address (default 127.0.0.1; 0.0.0.0 serves the public)")
    ap.add_argument("--engine", default=None,
                    help="world URL (default: env CHIMERA_ENGINE_URL, else "
                         "http://127.0.0.1:8107) -- scratch shells point at "
                         "their own private engine")
    a = ap.parse_args()
    if a.engine:
        Handler.engine_url = a.engine.rstrip("/")
    server = ThreadingHTTPServer((a.host, a.port), Handler)
    server.daemon_threads = True
    print(f"THE GAME -- http://{a.host}:{a.port}  (world: {Handler.engine_url})",
          flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
