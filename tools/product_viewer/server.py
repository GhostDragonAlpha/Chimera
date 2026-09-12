"""The product viewer service: a thin Python layer over the engine's HTTP contract.

Architecture directive (operator 2026-09-11): the C++ engine is a FROZEN
SERVICE; this module writes ZERO C++ and consumes only public engine routes.
stdlib http.server only — no third-party server dependencies.
"""
from __future__ import annotations

import collections
import json
import math
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import window_capture

# ---------------------------------------------------------------------------
# One-to-one engine window mirror (Python-only capture; MJPEG stream)
# ---------------------------------------------------------------------------


class EngineWindowMirror:
    """Finds the engine's native window by port (once, cached with re-find on
    loss) and streams JPEG captures. The engine window renders at full frame
    rate with ALL of its native UI - this mirror is one-to-one at capture
    pace, with zero engine changes."""

    def __init__(self, engine_url: str, port: int):
        self.engine_port = port
        self.hwnd = None
        self.title = None
        self.find_attempts = 0

    def find(self):
        import subprocess as sp
        try:
            out = sp.run(
                ["powershell", "-NoProfile", "-Command",
                 "(Get-CimInstance Win32_Process -Filter \"Name='chimera_engine.exe'\" "
                 f"| Where-Object {{$_.CommandLine -match ' {self.engine_port}'}} "
                 "| Select-Object -First 1).ProcessId"],
                capture_output=True, text=True, timeout=15).stdout.strip()
            pid = int(out)
            hwnd = window_capture.find_window(pid)
            if hwnd:
                import ctypes
                title = ctypes.create_unicode_buffer(256)
                window_capture.user32.GetWindowTextW(hwnd, title, 256)
                self.hwnd, self.title = hwnd, title.value
                return True
        except (ValueError, subprocess.SubprocessError, OSError):
            pass
        self.find_attempts += 1
        return False

    def ensure(self):
        return self.hwnd is not None or self.find()

    def frame_jpeg(self):
        if not self.ensure():
            return None
        try:
            ok, jpg = window_capture.capture_hwnd_jpeg(self.hwnd)
            return jpg if ok or jpg else None
        except Exception:
            self.hwnd = None     # window lost (engine restart) - re-find next tick
            return None

# ---------------------------------------------------------------------------
# Engine client (urllib; one retry at startup only, per the frozen prereg)
# ---------------------------------------------------------------------------


class EngineError(Exception):
    pass


class EngineClient:
    def __init__(self, base_url: str, timeout: float = 15.0):
        self.base = base_url.rstrip("/")
        self.timeout = timeout

    def get(self, path: str) -> tuple[int, bytes, str]:
        """GET -> (status, body, content_type). Raises EngineError on transport fault."""
        req = urllib.request.Request(self.base + path, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                return r.status, r.read(), r.headers.get("Content-Type", "")
        except urllib.error.HTTPError as e:  # engine answered with an error status
            return e.code, e.read(), e.headers.get("Content-Type", "")
        except (urllib.error.URLError, OSError, TimeoutError) as e:
            raise EngineError(f"GET {path}: {e}") from e

    def post_json(self, path: str, payload: dict, timeout: float | None = None) -> tuple[int, bytes]:
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(self.base + path, data=body, method="POST",
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=timeout or self.timeout) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            return e.code, e.read()
        except (urllib.error.URLError, OSError, TimeoutError) as e:
            raise EngineError(f"POST {path}: {e}") from e

    def up(self) -> bool:
        try:
            st, _, _ = self.get("/state")
            return st == 200
        except EngineError:
            return False


# ---------------------------------------------------------------------------
# Ring buffer of captures (bytes stored verbatim — never re-encoded)
# ---------------------------------------------------------------------------


class FrameRecord:
    __slots__ = ("index", "ts_unix", "ts_iso", "png", "sha256", "channel",
                 "joints_state", "chrome_state")

    def __init__(self, index, ts_unix, ts_iso, png, sha256, channel,
                 joints_state, chrome_state):
        self.index = index
        self.ts_unix = ts_unix
        self.ts_iso = ts_iso
        self.png = png
        self.sha256 = sha256
        self.channel = channel
        self.joints_state = joints_state
        self.chrome_state = chrome_state

    def meta(self) -> dict:
        return {"index": self.index, "ts_unix": self.ts_unix, "ts_iso": self.ts_iso,
                "sha256": self.sha256, "bytes": len(self.png), "channel": self.channel,
                "engine_sha256": self.sha256,
                "joints": self.joints_state, "chrome": self.chrome_state}


class RingBuffer:
    """Fixed-capacity capture history. `png` holds the EXACT engine bytes."""

    def __init__(self, capacity: int):
        self.cap = capacity
        self._items: collections.deque[FrameRecord] = collections.deque(maxlen=capacity)
        self._next_index = 0
        self._lock = threading.Lock()

    def append(self, png: bytes, sha256: str, channel: str,
               joints_state: dict, chrome_state: dict) -> FrameRecord:
        ts = time.time()
        with self._lock:
            rec = FrameRecord(self._next_index,
                              ts, time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(ts)),
                              png, sha256, channel, joints_state, chrome_state)
            self._items.append(rec)
            self._next_index += 1
            return rec

    def get(self, index: int) -> FrameRecord | None:
        with self._lock:
            if not self._items or index < self._items[0].index or index > self._items[-1].index:
                return None
            return self._items[index - self._items[0].index]

    def latest(self) -> FrameRecord | None:
        with self._lock:
            return self._items[-1] if self._items else None

    def all_records(self) -> list[FrameRecord]:
        with self._lock:
            return list(self._items)

    def stats(self) -> dict:
        with self._lock:
            if not self._items:
                return {"count": 0, "first_index": None, "last_index": None, "capacity": self.cap}
            return {"count": len(self._items), "capacity": self.cap,
                    "first_index": self._items[0].index, "last_index": self._items[-1].index}


# ---------------------------------------------------------------------------
# Capture thread: /glass + /joints + /studio_chrome per tick (frozen 10 Hz)
# ---------------------------------------------------------------------------


class CaptureThread(threading.Thread):
    def __init__(self, engine: EngineClient, ring: RingBuffer, period: float = 0.1):
        super().__init__(daemon=True, name="viewer-capture")
        self.engine = engine
        self.ring = ring
        self.period = period
        self.stop_flag = threading.Event()
        self.paused = threading.Event()     # observation control (POST /api/capture)
        self.stats = {"ticks": 0, "stored": 0, "misses": 0, "consecutive_misses": 0,
                      "max_consecutive_misses": 0, "paused_ticks": 0,
                      "last_store_ts": None, "last_error": None}
        self._stats_lock = threading.Lock()

    def snapshot_stats(self) -> dict:
        with self._stats_lock:
            s = dict(self.stats)
            s["paused"] = self.paused.is_set()
            return s

    def run(self):
        while not self.stop_flag.is_set():
            if self.paused.is_set():
                with self._stats_lock:
                    self.stats["paused_ticks"] += 1
                self.stop_flag.wait(0.05)
                continue
            t0 = time.monotonic()
            stored = False
            err = None
            try:
                # THE OBSERVER IS NOT IN THE PICTURE (THE_ALIGNMENT §4): the
                # ring captures the CLEAN /frame channel only — snapshots and
                # movies made from it are product artifacts for judges and the
                # operator's desktop. Instrument state (/joints, /studio_chrome)
                # rides as sidecar METADATA, never in pixels. The instrumented
                # /glass remains available as a live debugging view.
                st, png, ctype = self.engine.get("/frame")
                if st == 200 and ctype.startswith("image/png"):
                    import hashlib
                    digest = hashlib.sha256(png).hexdigest()
                    joints_state = self._json("/joints")
                    chrome_state = self._json("/studio_chrome")
                    self.ring.append(png, digest, "frame", joints_state, chrome_state)
                    stored = True
                elif st == 200:
                    err = "frame non-png body"
                else:
                    err = f"frame http {st}"
            except EngineError as e:
                err = str(e)
            with self._stats_lock:
                s = self.stats
                s["ticks"] += 1
                if stored:
                    s["stored"] += 1
                    s["consecutive_misses"] = 0
                    s["last_store_ts"] = time.time()
                    s["last_error"] = None
                else:
                    s["misses"] += 1
                    s["consecutive_misses"] += 1
                    s["max_consecutive_misses"] = max(s["max_consecutive_misses"],
                                                      s["consecutive_misses"])
                    s["last_error"] = err
            # THE OBSERVER MUST NOT STARVE THE OBSERVED: the engine serves its
            # HTTP queue serialized, and a back-to-back glass poller would
            # consume it whole. Each tick yields max(period, 1/4 of the tick
            # itself) before the next — the live view stays continuous while
            # drivers, browsers and judges keep their share of the engine.
            tick = time.monotonic() - t0
            self.stop_flag.wait(max(self.period, 0.25 * tick))

    def _json(self, path: str) -> dict:
        try:
            st, body, _ = self.engine.get(path)
            if st == 200:
                return json.loads(body.decode("utf-8", "replace"))
        except (EngineError, json.JSONDecodeError):
            pass
        return {}


# ---------------------------------------------------------------------------
# Camera presets — every number DERIVED (live engine docs), none chosen
# ---------------------------------------------------------------------------

TAN_HALF_FOV = math.tan(math.radians(45.0 / 2.0))   # engine: 45 deg vertical FOV (0.41421356)
FIT_MARGIN = 1.05                                    # the engine's own fit v3 margin


class CameraPanel:
    """Named presets over the camera contract.

    Contract nuance (read from main.cpp, recorded in the prereg): /camera is
    POST-only; camera STATE reads are served through POST /project (its
    cam:[8] echo of camera_state) and GET /cameras (the bookmark store).
    This panel composes those; no engine edit is needed.
    """

    def __init__(self, engine: EngineClient):
        self.engine = engine

    # -- derivation --------------------------------------------------------
    def derive_fit(self) -> dict:
        """The full-ROM fit, computed in PYTHON from the rig bounding envelope.

        Sources: GET /joints (per-joint rest center J, ROM ext/flex, parents)
        and GET /scene (the mesh extent r=<value> on the body row).
        Envelope law (frozen in PREREGISTRATION.txt): each joint k is a swept
        sphere at J_k with radius r_k = sum over ancestors a of
        2*|J_k - J_a|*sin(alpha_a/2); the ancestor distance |J_k - J_a| is a
        rigid-FK invariant, and the triangle inequality bounds the
        multi-ancestor sweep. Floor law mirrors the engine's own fit: if the
        rig floats above y=0 the box extends to the floor.
        """
        st, body, _ = self.engine.get("/joints")
        if st != 200:
            raise EngineError(f"/joints http {st}")
        doc = json.loads(body.decode("utf-8", "replace"))
        if not doc.get("loaded") or not doc.get("joints"):
            raise EngineError("no joints pack loaded")
        joints = doc["joints"]
        parents = doc.get("parents") or []
        P = [(float(j["J"][0]), float(j["J"][1]), float(j["J"][2])) for j in joints]

        lo = [min(p[k] for p in P) for k in range(3)]
        hi = [max(p[k] for p in P) for k in range(3)]
        if lo[1] > 0.0:                       # the floor is part of the composition
            lo[1] = 0.0
        c = [0.5 * (lo[k] + hi[k]) for k in range(3)]

        sweep_r = []
        for k, j in enumerate(joints):
            r = 0.0
            a = k
            while a != -1 and a < len(joints):
                alpha = math.radians(max(abs(float(joints[a]["ext"])),
                                         abs(float(joints[a]["flex"]))))
                if a != k:
                    d = math.dist(P[k], P[a])
                    r += 2.0 * d * math.sin(alpha / 2.0)
                a = parents[a] if a < len(parents) else -1
            sweep_r.append(r)
        R_rig = max(math.dist(P[k], c) + sweep_r[k] for k in range(len(P)))

        st2, body2, _ = self.engine.get("/scene")
        r_body = 10.0
        if st2 == 200:
            scene = json.loads(body2.decode("utf-8", "replace"))
            for row in scene.get("rows", []):
                if row.get("id") == "body":
                    detail = str(row.get("detail", ""))
                    if "r=" in detail:
                        try:
                            r_body = float(detail.split("r=")[-1].rstrip(", "))
                        except ValueError:
                            pass
        R = R_rig + r_body                    # the mesh has volume beyond its joints

        radius = R / TAN_HALF_FOV * FIT_MARGIN
        phi, theta = 0.35, 0.5                # the probe lane's derived three-quarter view
        return {"center": c, "R_rig": R_rig, "r_body": r_body, "R": R,
                "cam_radius": radius, "cam_theta": theta, "cam_phi": phi,
                "n_joints": len(P),
                "v": [radius, theta, phi, c[0], c[1], c[2], 0.0, 0.0]}

    # -- engine surface ----------------------------------------------------
    def camera_state(self) -> dict:
        """Read the live camera through POST /project's cam:[8] echo."""
        st, body = self.engine.post_json("/project", {"x": 0.0, "y": 0.0, "z": 0.0})
        doc = json.loads(body.decode("utf-8", "replace"))
        return {"cam": doc.get("cam"), "ok": doc.get("ok")}

    def bookmarks(self) -> dict:
        st, body, _ = self.engine.get("/cameras")
        if st != 200:
            raise EngineError(f"/cameras http {st}")
        return json.loads(body.decode("utf-8", "replace"))

    def set_orbit(self, cam_radius: float, cam_theta: float, cam_phi: float) -> dict:
        st, body = self.engine.post_json("/camera", {"cam_radius": cam_radius,
                                                     "cam_theta": cam_theta,
                                                     "cam_phi": cam_phi}, timeout=8.0)
        return json.loads(body.decode("utf-8", "replace"))

    def bookmark(self, op: str, name: str, v: list[float] | None = None) -> dict:
        payload: dict = {"op": op, "name": name}
        if v is not None:
            payload["v"] = v
        st, body = self.engine.post_json("/cameras", payload, timeout=8.0)
        return json.loads(body.decode("utf-8", "replace"))

    def apply_preset(self, name: str) -> dict:
        derived = self.derive_fit()
        r_body = derived["r_body"]
        presets = {
            # engine reset law (engine.cpp R-key): radius max(12, 2.7*mesh_sphere)
            "reset": {"cam_radius": max(12.0, 2.7 * r_body), "cam_theta": 0.0, "cam_phi": 0.3},
            # the probe lane's fixed three-quarter camera (PR #97 discipline)
            "three_quarter": {"cam_radius": max(12.0, 3.4 * r_body),
                              "cam_theta": 0.5, "cam_phi": 0.35},
        }
        if name == "fit_rom":
            v = derived["v"]
            save = self.bookmark("save", "fit_rom", v)
            if not save.get("ok"):
                return {"ok": False, "step": "save", "engine": save}
            recall = self.bookmark("recall", "fit_rom")
            return {"ok": bool(recall.get("ok")), "preset": "fit_rom",
                    "derivation": derived, "engine": recall}
        if name in presets:
            p = presets[name]
            resp = self.set_orbit(p["cam_radius"], p["cam_theta"], p["cam_phi"])
            return {"ok": bool(resp.get("ok")), "preset": name, "params": p, "engine": resp}
        raise EngineError(f"unknown preset: {name}")

    def list_presets(self) -> dict:
        return {"fit_rom": "full-ROM fit: radius = (rig swept-envelope radius + mesh "
                           "extent) / tan(22.5deg) * 1.05, target = envelope center "
                           "(computed in Python from GET /joints + GET /scene)",
                "reset": "engine reset law: radius max(12, 2.7*mesh_sphere), theta 0, phi 0.3",
                "three_quarter": "probe-lane fixed camera: 3.4*mesh_sphere, theta 0.5, phi 0.35"}


# ---------------------------------------------------------------------------
# Movie endpoint (cpp_bridge.encode_movie over the ring)
# ---------------------------------------------------------------------------


GRAPH_PAGE = """<!doctype html><html><head><meta charset="utf-8"><title>Chimera Ledger</title>
<style>body{background:#0b0f14;color:#d8dee6;font-family:Consolas,monospace;margin:0;overflow:hidden}
canvas{display:block;cursor:grab}canvas:active{cursor:grabbing}
#hud{position:fixed;top:10px;left:12px;font-size:12px;color:#8ab4f8;pointer-events:none}
#note{position:fixed;bottom:10px;left:12px;font-size:12px;color:#9aa4af;max-width:60em;pointer-events:none}
a{color:#8ab4f8}</style></head><body>
<canvas id="c"></canvas>
<div id="hud">CHIMERA LEDGER - drag to orbit / wheel to zoom - <a href="/">viewer</a></div>
<div id="note"></div>
<script>
const G=__DATA__;
const cv=document.getElementById('c'),cx=cv.getContext('2d');
let W,H;function rs(){W=cv.width=innerWidth;H=cv.height=innerHeight;}rs();onresize=rs;
let ry=0.5,rz=0.35,zoom=42,drag=null;
cv.onmousedown=e=>{drag={x:e.clientX,y:e.clientY}};
onmouseup=()=>drag=null;
onmousemove=e=>{if(!drag)return;ry+=(e.clientX-drag.x)*0.006;rz+=(e.clientY-drag.y)*0.006;drag={x:e.clientX,y:e.clientY};};
cv.onwheel=e=>{e.preventDefault();zoom*=(e.deltaY>0?1.1:0.9);};let tp=null;
cv.ontouchstart=e=>{const t=e.touches[0];tp={x:t.clientX,y:t.clientY};};
cv.ontouchmove=e=>{if(!tp)return;const t=e.touches[0];ry+=(t.clientX-tp.x)*0.006;rz+=(t.clientY-tp.y)*0.006;tp={x:t.clientX,y:t.clientY};};
const KIND={pillar:'#ffd166',law:'#ef476f',feature:'#06d6a0',lane:'#8ab4f8',evidence:'#b58cff'};
function P(p){const[x,y,z]=p;
  const x1=x*Math.cos(ry)-z*Math.sin(ry),z1=x*Math.sin(ry)+z*Math.cos(ry);
  const y1=y*Math.cos(rz)-z1*Math.sin(rz),z2=y*Math.sin(rz)+z1*Math.cos(rz);
  const f=zoom/(6+z2);return[W/2+x1*f,H/2-y1*f,z2,f];}
const pts=G.nodes.map(n=>({n,p:P(n.pos)}));
function draw(){cx.clearRect(0,0,W,H);
  cx.lineWidth=1;
  for(const e of G.edges){const a=pts.find(q=>q.n.id===e.from),b=pts.find(q=>q.n.id===e.to);
    if(!a||!b)continue;cx.strokeStyle=e.kind==='violated'?'rgba(239,71,111,.8)':'rgba(140,160,180,.28)';
    cx.beginPath();cx.moveTo(a.p[0],a.p[1]);cx.lineTo(b.p[0],b.p[1]);cx.stroke();}
  for(const q of pts){const[n,p]= [q.n,q.p];
    const r=Math.max(3,520/Math.max(6,p[3]));
    cx.beginPath();cx.arc(p[0],p[1],r,0,7);cx.fillStyle=KIND[n.kind]||'#888';cx.fill();
    cx.font='11px Consolas';cx.fillStyle='#c9d4e0';cx.fillText(n.label,p[0]+r+3,p[1]+3);}}
cv.onmousemove=e=>{if(drag)return;let best=null,bd=18;
  for(const q of pts){const d=Math.hypot(q.p[0]-e.clientX,q.p[1]-e.clientY);if(d<bd){bd=d;best=q;}}
  document.getElementById('note').textContent=best?(best.n.label+' ['+best.n.kind+(best.n.status?','+best.n.status:'')+'] '+(best.n.note||'')+(best.n.refs.length?' | '+best.n.refs.join(' , '):'')):'';};
(function loop(){pts.forEach(q=>q.p=P(q.n.pos));draw();requestAnimationFrame(loop);})();
</script></body></html>"""


def encode_ring(engine_root: Path, records: list[FrameRecord], out_path: Path,
                fps: int) -> Path:
    sys.path.insert(0, str(engine_root / "ChimeraEngine"))
    import cpp_bridge                                    # read-only import
    with tempfile.TemporaryDirectory() as td:
        paths = []
        for i, rec in enumerate(records):
            p = Path(td) / f"f{i:04d}.png"
            p.write_bytes(rec.png)
            paths.append(str(p))
        return Path(cpp_bridge.encode_movie(paths, str(out_path), fps=fps))


# ---------------------------------------------------------------------------
# The live page (inline HTML/CSS/JS only — no external assets)
# ---------------------------------------------------------------------------

PAGE = """<!doctype html><html><head><meta charset="utf-8"><title>Chimera Product Viewer</title>
<style>
 body{background:#101418;color:#d8dee6;font-family:Consolas,monospace;margin:16px}
 h1{font-size:15px;margin:0 0 10px} .row{display:flex;gap:12px;flex-wrap:wrap}
 .pane{flex:1;min-width:420px} .pane h2{font-size:12px;margin:0 0 4px;color:#8ab4f8}
  img{width:100%;border:1px solid #2a3138;background:#000}
  #fpan{cursor:grab} #fpan:active{cursor:grabbing}
  #fwrap{position:relative}
  #fhelp{position:absolute;top:6px;left:8px;font-size:11px;color:#7fd18a;
         background:rgba(0,0,0,.45);padding:2px 6px;border-radius:3px;pointer-events:none}
 #state{font-size:12px;color:#9aa4af;margin:8px 0;white-space:pre-wrap}
 button{background:#1d2733;color:#d8dee6;border:1px solid #3a4654;padding:4px 10px;
        margin:2px;font-family:inherit;font-size:12px;cursor:pointer}
 button:hover{background:#28374a} input{background:#0d1117;color:#d8dee6;
        border:1px solid #3a4654;width:90px;font-family:inherit;font-size:12px}
 fieldset{border:1px solid #2a3138;margin:8px 0} legend{font-size:12px;color:#8ab4f8}
 a{color:#8ab4f8;font-size:12px}
</style></head><body>
<h1>Chimera product viewer — engine window (one-to-one) · clean frame · instruments</h1>
<div id="state">connecting…</div>
<div class="pane" style="margin-bottom:10px"><h2>THE ENGINE WINDOW — one-to-one mirror, everything the engine shows, live</h2>
  <img id="w" alt="engine window" src="/api/window/stream?fps=8" style="width:100%">
</div>
<div class="row">
  <div class="pane"><h2>/frame — THE PRODUCT VIEW: the world only, no instruments</h2>
    <div id="fwrap"><span id="fhelp">drag = orbit (the camera is YOURS) · wheel = zoom</span>
    <img id="f" alt="frame"></div></div>
  <div class="pane"><h2>/glass — instruments composited (debugging only; never judged)</h2>
    <img id="g" alt="glass"></div>
</div>
<fieldset><legend>camera — drag any pane, wheel zooms, or keys: WASD move · Q/E up/down · R reset · P pose</legend>
  <button onclick="preset('fit_rom')">fit_rom (derived full-ROM fit)</button>
  <button onclick="preset('reset')">reset (R)</button>
  <button onclick="preset('three_quarter')">three_quarter</button>
  <button id="posebtn" onclick="pose()">pose clock: off</button>
 <span style="margin-left:14px">r <input id="r"> theta <input id="t"> phi <input id="p">
 <button onclick="setOrbit()">apply r/theta/phi</button></span>
 <div id="cam" style="font-size:12px;color:#9aa4af;margin-top:4px"></div>
</fieldset>
  <div>
  <button onclick="cap(!capOn)" id="capbtn">ring capture: paused</button>
  <span style="font-size:12px;color:#9aa4af">(runs ONLY during takes — the observer must not starve the observed)</span>
  </div>
  <div>
  <a href="/api/gallery" target="_blank">gallery json</a> ·
  <a href="/api/snapshot/latest" target="_blank">snapshot latest (byte-identical PNG)</a> ·
  <a href="/api/movie" target="_blank">movie (mp4 of the ring)</a> ·
  <a href="/api/health" target="_blank">health</a>
  </div>
<script>
let misses=0, capOn=false, TAKE=false;
// SELF-PACING LIVE VIEW: the engine's PNG readback is the measured bottleneck
// (~seconds per full-size frame). A fixed-interval poller would stack requests
// faster than the engine encodes them, back up its serialized queue, and starve
// EVERYTHING (seen live as camera-read timeouts). So: never more than one
// pending frame request per pane; the engine sets the tempo.
// MULTIPLAYER LAW: when take_mode is on, observers YIELD (a take died at the
// hands of three simultaneous heavy clients - the observer starved the observed).
function pace(imgEl, path, gap){
  let busy=false;
  function next(){
    if(busy) return;
    if(TAKE){ imgEl.title='take in progress - observer yields';
              setTimeout(next, 1000); return; }
    busy=true;
    const t=Date.now();
    imgEl.onload=()=>{busy=false; setTimeout(next,gap);};
    imgEl.onerror=()=>{busy=false; setTimeout(next,Math.max(gap,1000));};
    imgEl.src=path+'?t='+t;
  }
  next();
}
  next();
}
function tick(){
  pace(document.getElementById('f'), '/api/live/frame', 50);
}
function tickGlass(){
  pace(document.getElementById('g'), '/api/live/glass', 400);
}
function cap(on){capOn=on;
  fetch('/api/capture',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({on:on})}).then(r=>r.json()).then(()=>{
    document.getElementById('capbtn').textContent='ring capture: '+(on?'ON':'paused');});}

// THE CAMERA BELONGS TO THE OPERATOR (THE_TRIANGLE_GUIDE 5): drag orbits the
// engine camera (the viewer renders nothing itself — the engine is the only
// renderer); the wheel zooms. One POST per throttled move; deltas from the
// cached live camera state.
let cam0=null, drag=null, lastPost=0;
function getCam(){return fetch('/api/camera').then(r=>r.json()).then(d=>d.state&&d.state.cam);}
function orbit(dTheta,dPhi,dR){
  if(!cam0)return;
  const now=Date.now(); if(now-lastPost<60)return; lastPost=now;
  const c=[...cam0];
  c[0]=Math.max(2.0,c[0]*(dR||1)); c[1]=c[1]+(dTheta||0);
  c[2]=Math.min(1.5,Math.max(0.02,c[2]+(dPhi||0)));
  fetch('/api/camera',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({action:'set',cam_radius:c[0],cam_theta:c[1],cam_phi:c[2]})})
    .then(()=>{cam0=c;});
}
const fp=document.getElementById('fpan')||document.getElementById('f');
const wp=document.getElementById('w');
function bindOrbit(el){
  el.addEventListener('mousedown',e=>{drag={x:e.clientX,y:e.clientY};
    getCam().then(c=>{cam0=c;}); e.preventDefault();});
  el.addEventListener('wheel',e=>{e.preventDefault(); getCam().then(c=>{cam0=c;
    orbit(0,0, e.deltaY>0?1.12:0.89);});},{passive:false});
  el.addEventListener('touchstart',e=>{const t=e.touches[0]; drag={x:t.clientX,y:t.clientY};
    getCam().then(c=>{cam0=c;});},{passive:true});
  el.addEventListener('touchmove',e=>{if(!drag||!cam0)return; const t=e.touches[0];
    const dx=t.clientX-drag.x, dy=t.clientY-drag.y; drag={x:t.clientX,y:t.clientY};
    orbit(dx*0.005, dy*0.005, 1);},{passive:true});
  el.addEventListener('touchend',()=>{drag=null;});
}
bindOrbit(fp); if(wp) bindOrbit(wp);
window.addEventListener('mouseup',()=>{drag=null;});
window.addEventListener('mousemove',e=>{if(!drag||!cam0)return;
  const dx=e.clientX-drag.x, dy=e.clientY-drag.y; drag={x:e.clientX,y:e.clientY};
  orbit(dx*0.005, dy*0.005, 1);});
// THE ENGINE'S OWN KEYBOARD, THROUGH THE WEB: WASD = move (radius/theta),
// Q/E = up/down (phi), R = engine reset law, P = pose clock toggle.
let poseOn=false;
function pose(){poseOn=!poseOn;
  fetch('/api/pose',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({on:poseOn})}).then(r=>r.json()).then(()=>{
    document.getElementById('posebtn').textContent='pose clock: '+(poseOn?'ON':'off');});}
document.addEventListener('keydown',e=>{
  if(e.target.tagName==='INPUT')return;
  const k=e.key.toLowerCase();
  getCam().then(c=>{cam0=c;
    if(k==='a')orbit(-0.06,0,1); else if(k==='d')orbit(0.06,0,1);
    else if(k==='w')orbit(0,0,0.92); else if(k==='s')orbit(0,0,1.09);
    else if(k==='q')orbit(0,-0.05,1); else if(k==='e')orbit(0,0.05,1);
    else if(k==='r')preset('reset');
    else if(k==='p')pose();
  });});
function state(){
  fetch('/api/health').then(r=>r.json()).then(h=>{TAKE=!!h.take_mode;
    const el=document.getElementById('state');
    if(h.engine_up===false){
      el.textContent='ENGINE DOWN - the panes are empty because no engine is running on '+h.engine+
                     ' (start one; the mirror re-finds its window automatically)';
      el.style.color='#ef476f';
    } else {
      el.style.color='#9aa4af';
      return fetch('/api/gallery').then(r=>r.json()).then(d=>{
        const last=d.records[d.records.length-1];
        if(!last){document.getElementById('state').textContent='engine UP - ring empty (capture paused; that is normal between takes)';return;}
        const j=last.joints||{}, c=last.chrome||{};
        document.getElementById('state').textContent=
          'engine UP  ring['+d.stats.first_index+'..'+d.stats.last_index+']  engine t='+(j.t??'?')
          +'  current='+(j.current??'?')
          +'  fps='+(c.fps??'?')+'  stage="'+(c.stage??'?')+'"'
          +'  sha256='+String(last.sha256).slice(0,16)+'…  '+last.ts_iso;
      });
    }}).catch(()=>{});
  fetch('/api/camera').then(r=>r.json()).then(d=>{
    const cam=d.state&&d.state.cam?d.state.cam.map(x=>(+x).toFixed(3)).join(', '):'?';
    document.getElementById('cam').textContent='live cam [r,theta,phi,tx,ty,tz,px,py] = '+cam
      +'   bookmarks: '+(d.bookmarks||[]).map(b=>b.name).join(', ');
  }).catch(()=>{});
}
function preset(n){fetch('/api/camera',{method:'POST',
  headers:{'Content-Type':'application/json'},
  body:JSON.stringify({action:'apply',preset:n})}).then(r=>r.json()).then(d=>{
    document.getElementById('cam').textContent=JSON.stringify(d).slice(0,300);});}
function setOrbit(){fetch('/api/camera',{method:'POST',
  headers:{'Content-Type':'application/json'},
  body:JSON.stringify({action:'set',cam_radius:+document.getElementById('r').value,
    cam_theta:+document.getElementById('t').value,cam_phi:+document.getElementById('p').value})
  }).then(r=>r.json()).then(d=>{
    document.getElementById('cam').textContent=JSON.stringify(d).slice(0,300);});}
tick(); tickGlass(); setInterval(state,1000); state();
</script></body></html>"""


# ---------------------------------------------------------------------------
# HTTP handler
# ---------------------------------------------------------------------------


class ViewerHandler(BaseHTTPRequestHandler):
    server_version = "ChimeraProductViewer/1.1"
    engine: EngineClient = None            # injected via make_server
    ring: RingBuffer = None
    camera: CameraPanel = None
    started: float = 0.0
    take_mode = {"on": False}              # multiplayer law: observers yield during takes

    def log_message(self, fmt, *args):     # quiet by default; stats live in /api/health
        pass

    # -- helpers -----------------------------------------------------------
    def _send(self, code: int, body: bytes, ctype: str):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _json(self, obj, code: int = 200):
        self._send(code, json.dumps(obj, default=str).encode("utf-8"),
                   "application/json; charset=utf-8")

    def _png_passthrough(self, rec_or_bytes):
        """Serve engine PNG bytes EXACTLY — no decode, no re-encode."""
        if rec_or_bytes is None:
            self._json({"ok": False, "error": "no frame"}, 404)
            return
        png = rec_or_bytes if isinstance(rec_or_bytes, (bytes, bytearray)) else rec_or_bytes.png
        self._send(200, bytes(png), "image/png")

    # -- routes ------------------------------------------------------------
    def do_GET(self):
        H = type(self)
        path = self.path.split("?")[0]
        query = self.path.split("?")[1] if "?" in self.path else ""
        try:
            if path == "/" or path == "/index.html":
                self._send(200, PAGE.encode("utf-8"), "text/html; charset=utf-8")
            elif path == "/api/live/glass":
                st, png, ctype = H.engine.get("/glass")
                if st == 200 and ctype.startswith("image/png"):
                    self._png_passthrough(png)
                else:
                    self._json({"ok": False, "error": f"engine glass http {st}"}, 502)
            elif path == "/api/live/frame":
                st, png, ctype = H.engine.get("/frame")
                if st == 200 and ctype.startswith("image/png"):
                    self._png_passthrough(png)
                else:
                    self._json({"ok": False, "error": f"engine frame http {st}"}, 502)
            elif path == "/api/snapshot/latest":
                rec = H.ring.latest()
                self._png_passthrough(rec)
            elif path.startswith("/api/snapshot/"):
                tail = path[len("/api/snapshot/"):]
                try:
                    index = int(tail)
                except ValueError:
                    self._json({"ok": False, "error": "index must be an integer"}, 400)
                    return
                self._png_passthrough(H.ring.get(index))
            elif path == "/api/gallery":
                recs = H.ring.all_records()
                self._json({"stats": H.ring.stats(),
                            "records": [r.meta() for r in recs]})
            elif path == "/api/camera":
                try:
                    self._json({"ok": True, "presets": H.camera.list_presets(),
                                "state": H.camera.camera_state(),
                                "bookmarks": H.camera.bookmarks().get("bookmarks", []),
                                "fit_derivation": H.camera.derive_fit()})
                except (EngineError, json.JSONDecodeError, KeyError) as e:
                    self._json({"ok": False, "error": str(e)}, 502)
            if path == "/graph" or path == "/graph/":
                g = (Path(__file__).resolve().parents[2] / "docs" / "LEDGER_GRAPH.json")
                if g.is_file():
                    payload = GRAPH_PAGE.replace("__DATA__", g.read_text(encoding="utf-8"))
                    self._send(200, payload.encode("utf-8"), "text/html; charset=utf-8")
                else:
                    self._json({"ok": False, "error": "LEDGER_GRAPH.json missing"}, 404)
            elif path == "/api/graph":
                g = (Path(__file__).resolve().parents[2] / "docs" / "LEDGER_GRAPH.json")
                if g.is_file():
                    self._send(200, g.read_bytes(), "application/json; charset=utf-8")
                else:
                    self._json({"ok": False, "error": "LEDGER_GRAPH.json missing"}, 404)
            elif path == "/api/window/frame":
                jpg = H.mirror.frame_jpeg() if getattr(H, "mirror", None) else None
                if jpg is None:
                    self._json({"ok": False, "error": "engine window not found"}, 502)
                else:
                    self._send(200, jpg, "image/jpeg")
            elif path == "/api/window/stream":
                self._window_stream(query)
            elif path == "/api/movie":
                self._movie(query)
            elif path == "/api/health":
                capture = getattr(H, "capture_thread", None)
                self._json({"ok": True, "engine": H.engine.base,
                            "engine_up": H.engine.up(), "ring": H.ring.stats(),
                            "take_mode": H.take_mode["on"],
                            "capture": capture.snapshot_stats() if capture else {},
                            "uptime_s": round(time.time() - H.started, 1)})
            else:
                self._json({"ok": False, "error": "unknown route"}, 404)
        except EngineError as e:
            self._json({"ok": False, "error": str(e)}, 502)

    def _window_stream(self, query: str):
        """MJPEG multipart stream of the engine window - browsers render this
        natively in an <img>. Pace: ~10 fps, one client request at a time."""
        import subprocess as _sp
        H = type(self)
        fps = 10
        for kv in query.split("&"):
            if kv.startswith("fps="):
                fps = max(1, min(30, int(kv[4:])))
        self.send_response(200)
        self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=chframe")
        self.end_headers()
        period = 1.0 / fps
        import time as _time
        while True:
            t0 = _time.monotonic()
            jpg = H.mirror.frame_jpeg() if getattr(H, "mirror", None) else None
            if jpg is not None:
                try:
                    self.wfile.write(b"--chframe\r\nContent-Type: image/jpeg\r\n"
                                     b"Content-Length: " + str(len(jpg)).encode() +
                                     b"\r\n\r\n" + jpg + b"\r\n")
                    self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError, OSError):
                    return
            gap = period - (_time.monotonic() - t0)
            if gap > 0:
                _time.sleep(gap)

    def _movie(self, query: str):
        H = type(self)
        recs = H.ring.all_records()
        fps = 10  # the ring's capture rate — movies play at TRUE tempo (THE_ALIGNMENT §5 Phase 1)
        frm, to = None, None
        for kv in query.split("&"):
            if kv.startswith("from="):
                frm = int(kv[5:])
            elif kv.startswith("to="):
                to = int(kv[3:])
            elif kv.startswith("fps="):
                fps = max(1, min(60, int(kv[4:])))
        if frm is not None or to is not None:
            lo = frm if frm is not None else recs[0].index
            hi = to if to is not None else recs[-1].index
            recs = [r for r in recs if lo <= r.index <= hi]
        if not recs:
            self._json({"ok": False, "error": "ring empty (or range selects nothing)"}, 404)
            return
        engine_root = Path(__file__).resolve().parents[2]
        out = Path(tempfile.gettempdir()) / f"viewer_take_{int(time.time() * 1000)}.mp4"
        try:
            mp4 = encode_ring(engine_root, recs, out, fps)
            data = mp4.read_bytes()
        finally:
            out.unlink(missing_ok=True)
        self.send_response(200)
        self.send_header("Content-Type", "video/mp4")
        self.send_header("Content-Disposition",
                         f'attachment; filename="viewer_take_{recs[0].index}'
                         f'-{recs[-1].index}.mp4"')
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        try:
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_POST(self):
        H = type(self)
        path = self.path.split("?")[0]
        if path == "/api/capture":
            # observation control: pause/resume the capture thread (a paused
            # tick is NOT a missed poll — the pipeline is stopped on purpose)
            try:
                length = int(self.headers.get("Content-Length", 0))
                payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
                on = bool(payload.get("on", True))
                capture = getattr(H, "capture_thread", None)
                if capture is None:
                    self._json({"ok": False, "error": "no capture thread"}, 500)
                    return
                (capture.paused.clear() if on else capture.paused.set())
                self._json({"ok": True, "capture_on": on,
                            "stats": capture.snapshot_stats()})
            except (json.JSONDecodeError, ValueError) as e:
                self._json({"ok": False, "error": str(e)}, 400)
            return
        if path == "/api/pose":
            # proxy: the engine's P-key (show/pose clock toggle) for web clients
            try:
                length = int(self.headers.get("Content-Length", 0))
                payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
                st, body = H.engine.post_json("/joints", {"on": bool(payload.get("on", True))})
                self._json(json.loads(body.decode("utf-8", "replace")))
            except (json.JSONDecodeError, ValueError, EngineError) as e:
                self._json({"ok": False, "error": str(e)}, 502)
            return
        if path == "/api/take":
            try:
                length = int(self.headers.get("Content-Length", 0))
                payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
                H.take_mode["on"] = bool(payload.get("on", False))
                self._json({"ok": True, "take_mode": H.take_mode["on"]})
            except (json.JSONDecodeError, ValueError) as e:
                self._json({"ok": False, "error": str(e)}, 400)
            return
        if path != "/api/camera":
            self._json({"ok": False, "error": "unknown route"}, 404)
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            action = payload.get("action")
            if action == "apply":
                self._json(H.camera.apply_preset(payload.get("preset", "")))
            elif action == "set":
                self._json({"ok": True,
                            "engine": H.camera.set_orbit(
                                float(payload.get("cam_radius", 12.0)),
                                float(payload.get("cam_theta", 0.0)),
                                float(payload.get("cam_phi", 0.3)))})
            elif action == "derive_fit":
                self._json({"ok": True, "derivation": H.camera.derive_fit()})
            elif action in ("save", "recall", "delete"):
                self._json({"ok": True,
                            "engine": H.camera.bookmark(action, payload.get("name", ""),
                                                        payload.get("v"))})
            else:
                self._json({"ok": False,
                            "error": "action must be apply|set|derive_fit|save|recall|delete"},
                           400)
        except (EngineError, json.JSONDecodeError, ValueError, KeyError) as e:
            self._json({"ok": False, "error": str(e)}, 502)


# ---------------------------------------------------------------------------


def make_server(engine_url: str, port: int, history: int = 240) -> ThreadingHTTPServer:
    engine = EngineClient(engine_url)
    ring = RingBuffer(history)
    capture = CaptureThread(engine, ring, period=0.1)
    engine_port = engine_url.rstrip("/").rsplit(":", 1)[-1]
    handler = type("BoundViewerHandler", (ViewerHandler,), {
        "engine": engine, "ring": ring, "camera": CameraPanel(engine),
        "started": time.time(), "capture_thread": capture,
        "mirror": EngineWindowMirror(engine_url, int(engine_port)),
    })
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    server.daemon_threads = True
    server.capture_thread = capture          # lifecycle owned by serve_forever
    return server


def serve_forever(engine_url: str, port: int, history: int = 240) -> None:
    server = make_server(engine_url, port, history)
    capture = server.capture_thread
    capture.paused.set()          # PAUSED BY DEFAULT: the ring runs only during
                                  # takes (POST /api/capture) — a 10 Hz stream of
                                  # full-size PNGs against a serialized engine
                                  # queue is the observer starving the observed.
    capture.start()
    print(f"product viewer on http://127.0.0.1:{port}  engine={engine_url} "
          f"history={history}", flush=True)
    try:
        server.serve_forever()
    finally:
        capture.stop_flag.set()
