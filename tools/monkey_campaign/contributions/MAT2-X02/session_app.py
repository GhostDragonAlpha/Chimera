"""session_app.py -- MAT2-X02: the app-level session wiring (archived M1 fix).

The pinned playable-slice app (8550b634) ships no player session flow: no
session_flow/input_mapper import, no pause/exit control, no Escape/Q/Enter
binding (the archived ONT-X02 integrated run MEASURED this as missing
integration M1). This module wires the pinned, byte-exact SessionFlow
(f30f2224, sha 30e06c04) into that app additively:

  * ONE session object: SessionFlow(mapper, restart_scene=World.boot,
    teardown=World.shutdown_engine) -- exactly the flow's own docstring
    prescription, over the REAL World lifecycle seam of the pinned
    slice_server.
  * FOUR new routes only (everything legacy is forwarded untouched):
      GET  /api/session       state read (state, held keys, record count)
      POST /api/session/key   the player's key event -> SessionFlow.key
      POST /api/session/tick  the player-paced decision boundary -> tick
      GET  /session_overlay.js  the additive page script
  * The served page is the PINNED index.html bytes with EXACTLY ONE
    disclosed additive script tag injected (inject_overlay); without the
    tag the bytes are byte-identical to the pin.

THE NO-DEVELOPER-COMMANDS LAW IS UNCHANGED: every state change is caused by
SessionFlow.key (the flow's public mutator); /api/session/tick passes through
only in `playing` and can never transition; the clock used for record
timestamps is a timestamp, never a transition driver. The overlay intercepts
the flow-bound keys in the browser CAPTURE phase so the flow has single
authority on the wired page; the pinned page handlers stay byte-identical and
fully functional whenever this overlay is not served.

The mapper record stream is session diagnostics (archived M4 stands: no
locomotion consumer exists; none is fabricated).
"""
from __future__ import annotations

import json
import sys
import time
from http.server import BaseHTTPRequestHandler
from pathlib import Path

_ROOT = Path(__file__).resolve().parent / "reference"
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# The pinned modules: imported, never redeclared (the frozen-number law).
from tools.monkey_campaign.product.input_mapper import InputMapper  # noqa: E402
from tools.monkey_campaign.product.session_flow import SessionFlow  # noqa: E402

__all__ = [
    "SESSION_APP_SCHEMA", "OVERLAY_ROUTE", "OVERLAY_TAG",
    "SliceSession", "SessionRoutes", "make_wired_handler",
    "inject_overlay", "overlay_js", "monotonic_ms",
]

SESSION_APP_SCHEMA = "chimera.mat2-x02.session-app.v1"

OVERLAY_ROUTE = "/session_overlay.js"
OVERLAY_TAG = "<script src=\"/session_overlay.js\"></script>"

# page key -> flow key (the flow's own DEFAULT_FLOW_BINDINGS names)
_FLOW_KEYS = {"Enter": "Return", "Return": "Return",
              "Escape": "Escape", "q": "Q", "Q": "Q", "r": "R", "R": "R"}
# gameplay keys the mapper knows (input_mapper.DEFAULT_BINDINGS), canonicalized
_GAME_KEYS = {" ": "Space", "w": "W", "W": "W", "a": "A", "A": "A",
              "s": "S", "S": "S", "d": "D", "D": "D",
              "ArrowLeft": "ArrowLeft", "ArrowRight": "ArrowRight",
              "ArrowUp": "ArrowUp", "ArrowDown": "ArrowDown"}


def monotonic_ms() -> int:
    """Injected-time law: a record TIMESTAMP, never a transition driver."""
    return time.monotonic_ns() // 1_000_000


class RecordingSink:
    """Session diagnostics sink (the archived M4 law: this is NOT a locomotion
    consumer; it records the mapper's CommandRecords for the session read)."""

    def __init__(self):
        self.records = []

    def emit(self, record):
        self.records.append(record)


class SliceSession:
    """The flow over a World seam, with an injected clock and canonical keys.

    Construct exactly as session_flow's docstring prescribes; every state
    change still flows through SessionFlow.key -- this class adds no mutator
    of its own.
    """

    def __init__(self, world, mapper=None, sink=None, clock=None, bindings=None):
        self._clock = clock if clock is not None else monotonic_ms
        self.sink = sink if sink is not None else RecordingSink()
        self.mapper = mapper if mapper is not None else InputMapper(self.sink)
        self.flow = SessionFlow(self.mapper,
                                restart_scene=world.boot,
                                teardown=world.shutdown_engine,
                                bindings=bindings)

    # ── the player surface (delivery only; the flow owns every transition) ──
    def key(self, name, down):
        return self.flow.key(name, down, int(self._clock()))

    def mouse(self, dx_counts):
        return self.flow.mouse(dx_counts)

    def tick(self, now_ms=None):
        return self.flow.tick(int(self._clock() if now_ms is None else now_ms))

    # ── the state read (resource/session diagnostics) ────────────────────────
    def snapshot(self, extra=None):
        trace = self.flow.last_trace
        out = {
            "schema": SESSION_APP_SCHEMA,
            "state": self.flow.state,
            "held": sorted(self.mapper.held),
            "records": len(getattr(self.sink, "records", [])),
            "quiesces": len(trace.get("quiesced", [])),
            "restarts": len(trace.get("restart_path", [])),
            "dropped": len(trace.get("dropped", [])),
            "transitions": [list(t) for t in trace.get("transitions", [])],
        }
        if extra:
            out.update(extra)
        return out


class SessionRoutes:
    """The four additive routes, HTTP-shaped but testable without a socket."""

    def __init__(self, session: SliceSession, page_loader):
        self.session = session
        self._page_loader = page_loader

    # (handled, args-for-_send/_json)
    def handle_get(self, path: str):
        p = path.split("?")[0]
        if p in ("/", "/index.html"):
            return True, ("page", 200, inject_overlay(self._page_loader()),
                          "text/html")
        if p == OVERLAY_ROUTE:
            return True, ("page", 200, overlay_js(), "text/javascript")
        if p == "/api/session":
            return True, ("json", 200, self.session.snapshot(), None)
        return False, None

    def handle_post(self, path: str, body: bytes):
        p = path.split("?")[0]
        if p == "/api/session/key":
            data = json.loads(body.decode("utf-8") or "{}")
            name = self._canonical(data.get("key", ""))
            down = 1 if data.get("down", 1) else 0
            dest = self.session.key(name, down)
            return True, ("json", 200, {
                "ok": True, "key": name, "down": bool(down),
                "transition": dest, **self.session.snapshot(),
            }, None)
        if p == "/api/session/tick":
            data = json.loads(body.decode("utf-8") or "{}")
            emitted = self.session.tick(data.get("now_ms"))
            return True, ("json", 200, {
                "ok": True, "emitted": len(emitted),
                **self.session.snapshot(),
            }, None)
        return False, None

    @staticmethod
    def _canonical(name):
        if name in _FLOW_KEYS:
            return _FLOW_KEYS[name]
        if name in _GAME_KEYS:
            return _GAME_KEYS[name]
        return name


def make_wired_handler(base_handler, session):
    """Return a handler class whose ONLY deltas are the four additive routes;
    every other GET/POST reaches the base (pinned) handler untouched.
    `session` is a SliceSession or an already-built SessionRoutes."""
    routes = (session if isinstance(session, SessionRoutes)
              else SessionRoutes(session, _default_page_loader()))

    class WiredHandler(base_handler):
        session_routes = routes

        def _route_session(self):
            return self.session_routes

        def do_GET(self):
            handled, payload = self._route_session().handle_get(self.path)
            if handled:
                kind, code, body, ctype = payload
                if kind == "page":
                    self._send(code, body, ctype)
                else:
                    self._json(body, code)
                return
            super().do_GET()

        def do_POST(self):
            n = int(self.headers.get("Content-Length", 0) or 0)
            body = self.rfile.read(n) if n else b"{}"
            handled, payload = self._route_session().handle_post(self.path, body)
            if handled:
                kind, code, obj, _ctype = payload
                self._json(obj, code)
                return
            self.body = body
            super().do_POST()

    return WiredHandler


def _default_page_loader():
    here = Path(__file__).resolve().parent
    pinned = here / "reference" / "tools" / "playable_slice" / "index.html"
    return lambda: pinned.read_bytes()


def inject_overlay(pinned_html: bytes) -> bytes:
    """The pinned bytes with EXACTLY ONE disclosed script tag; nothing else."""
    tag = OVERLAY_TAG.encode("ascii")
    if tag in pinned_html:
        return pinned_html
    marker = b"</body>"
    idx = pinned_html.rfind(marker)
    if idx < 0:
        return pinned_html + tag
    return pinned_html[:idx] + tag + pinned_html[idx:]


def overlay_js() -> bytes:
    """The additive player script. Capture-phase for flow keys (single flow
    authority); gameplay keys pass through to the pinned page handlers while
    playing and are named-dropped by the flow otherwise; the session HUD is
    the on-screen resource/session diagnostics referent."""
    return r""";(function(){
  var state = 'attract';
  function post(path, body){
    try { return fetch(path, {method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify(body||{})}).then(function(r){return r.json();}).catch(function(){return null;}); }
    catch(e) { return null; }
  }
  function hud(){
    if (document.getElementById('sessionhud')) return;
    var d = document.createElement('div');
    d.id = 'sessionhud';
    d.setAttribute('data-t','sessionhud');
    d.style.cssText = 'position:absolute;bottom:10px;left:10px;color:#9fe89f;'+
      'font:12px monospace;background:rgba(0,0,0,.55);padding:4px 8px;'+
      'border-radius:4px;z-index:60;white-space:pre';
    document.body.appendChild(d);
  }
  function poll(){
    fetch('/api/session').then(function(r){return r.json();}).then(function(s){
      state = s.state;
      var el = document.getElementById('sessionhud');
      if (el) el.textContent = 'SESSION ' + String(s.state).toUpperCase() +
        ' records=' + s.records + ' held=' + (s.held.join('+')||'-') +
        '\n[Enter] start/resume  [Esc] pause  [R] reset (from pause)  [Q] exit';
    }).catch(function(){});
  }
  function boot(){
    hud(); poll();
    setInterval(poll, 500);            // state READ (diagnostics), never a write
    setInterval(function(){ post('/api/session/tick', {}); }, 50); // decision boundary transport
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
  var FLOW = {Enter:'Return', Escape:'Escape', q:'Q', Q:'Q', r:'R', R:'R'};
  var GAME = {' ':'Space', w:'W', a:'A', s:'S', d:'D',
              ArrowLeft:'ArrowLeft', ArrowRight:'ArrowRight',
              ArrowUp:'ArrowUp', ArrowDown:'ArrowDown'};
  window.addEventListener('keydown', function(e){
    var f = FLOW[e.key];
    if (f) { e.preventDefault(); e.stopPropagation(); post('/api/session/key', {key:f, down:1}); return; }
    var g = GAME[e.key];
    if (g) { post('/api/session/key', {key:g, down:1}); }   // demand record; legacy handlers also run
  }, true);
  window.addEventListener('keyup', function(e){
    var g = GAME[e.key];
    if (g && !FLOW[e.key]) { post('/api/session/key', {key:g, down:0}); }
  }, true);
  window.__SESSION_OVERLAY__ = true;
})();""".encode("ascii")
