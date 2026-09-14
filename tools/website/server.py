"""website/server.py -- THE PUBLIC FRONT DOOR (R9).

One small stdlib server: serves the landing page and the folder's
static files, takes sign-ups (name + email) as one honest JSON line
apiece in signups.jsonl, and counts them back for the page's
"join N explorers" line. No store, no gate -- a stranger plays the
free demo first and signs up afterwards.

Run:  python tools/website/server.py [port] [--host H]
      (default port 8210; default host 127.0.0.1 -- pass --host 0.0.0.0
      ONLY when you mean to serve the public; see docs/DEPLOY_RUNBOOK.md)
The PLAY THE DEMO button expects the game shell on 127.0.0.1:8206.

Hardening (public deployment):
  --host    binds 127.0.0.1 unless 0.0.0.0 is passed explicitly.
  limits    one token bucket per (visitor IP, class): api routes
            30 req/min, static files 120 req/min; over the bucket is 429.
  bodies    a signup is <200 bytes so its body is capped at 4 KB; any
            request body is capped at 5 MB; both answers are 413 and the
            unread body is never read (the connection just closes).
  paths     percent-escapes are decoded FIRST, then any '..' segment,
            backslash separator or drive letter is refused; the folder
            containment check (resolve + parents) stays as the wall.
  secrets   signups.jsonl is append-only PII -- it is NEVER web-readable.
  listing   only real files are served; a directory asks for a 404 and
            gets one.
"""
from __future__ import annotations

import json
import mimetypes
import threading
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
SIGNUPS = HERE / "signups.jsonl"

TEXT_TYPES = ("text/", "application/javascript", "application/json")

# -- hardening: numbers with reasons --------------------------------------
# api   30 req/min: the signup door and the count readout. A landing
#       visitor fires ~5 requests total; 30/min is 6x that, honest use
#       never brushes it, a for-loop does.
# static 120 req/min: a page load is a handful of files; 120/min is a
#       page per few seconds, forever, per IP -- generous for people.
RATE_LIMITS = {"api": (30, 15), "static": (120, 60)}  # class -> (per minute, burst)
MAX_BODY = 5 * 1024 * 1024   # no honest request body here is bigger
MAX_SIGNUP_BODY = 4 * 1024   # a signup is <200 bytes; 20x headroom

_BUCKETS: dict = {}          # (ip, class) -> (tokens left, last seen)
_BUCKET_LOCK = threading.Lock()


def _rate_class(path: str) -> str:
    return "api" if path.startswith("/api/") else "static"


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
    # do not advertise the interpreter to every stranger
    server_version = "ChimeraR9"
    sys_version = ""

    def log_message(self, *a):  # quiet: the page reads the count on load
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
        self._json({"ok": False, "error": msg}, code)
        self.close_connection = True

    def _serve_file(self, rel: str):
        # THE GUARD: decode percent-escapes FIRST, then refuse anything
        # that could leave this folder -- '..' segments, backslash
        # separators (Windows reads those as paths of their own), drive
        # letters, and signups.jsonl (append-only PII, never public).
        rel = urllib.parse.unquote(rel).replace("\\", "/")
        segs = rel.split("/")
        if any(s == ".." for s in segs) or any(":" in s for s in segs):
            self._send(b"not found", "text/plain; charset=utf-8", 404)
            return
        try:
            f = (HERE / rel).resolve()
        except (OSError, ValueError):  # e.g. an embedded NUL byte
            self._send(b"not found", "text/plain; charset=utf-8", 404)
            return
        if HERE not in f.parents or not f.is_file() or f == SIGNUPS:
            self._send(b"not found", "text/plain; charset=utf-8", 404)
            return
        ctype = mimetypes.guess_type(f.name)[0] or "application/octet-stream"
        if ctype.startswith(TEXT_TYPES):
            ctype += "; charset=utf-8"
        self._send(f.read_bytes(), ctype)

    # -- verbs ------------------------------------------------------------
    def do_GET(self):
        p = self.path.split("?", 1)[0]
        if not _allow(self._client_ip(), p):
            self._deny(429, "too many requests -- slow down")
            return
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
        try:
            n = int(self.headers.get("Content-Length", 0) or 0)
        except ValueError:
            n = -1
        if n < 0 or n > MAX_SIGNUP_BODY:
            self._deny(413, "body too large")
            return
        if not _allow(self._client_ip(), p):
            self._deny(429, "too many requests -- slow down")
            return
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
    import argparse
    ap = argparse.ArgumentParser(description="Chimera website front door (R9)")
    ap.add_argument("port", nargs="?", type=int, default=8210)
    ap.add_argument("--host", default="127.0.0.1",
                    help="bind address (default 127.0.0.1; 0.0.0.0 serves the public)")
    a = ap.parse_args()
    server = ThreadingHTTPServer((a.host, a.port), Handler)
    server.daemon_threads = True
    print(f"THE FRONT DOOR -- http://{a.host}:{a.port}  (game shell: 8206)",
          flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
