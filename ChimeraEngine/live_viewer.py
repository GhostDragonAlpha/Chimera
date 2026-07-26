"""live_viewer.py -- the LIVE INTERACTIVE viewer, served into the gallery's HTTP page.

A still is a photograph; a term is a slice of the timeline UNFOLDING, and you cannot verify a 3D world
from one flat frame. This turns the term's SETTLED splat scene in real time (the time axis) and lets the
operator ORBIT it with the mouse (verify it is a true volume -- a far side, poles top and bottom -- not a
painted disk). That is the 4th dimension made checkable.

Architecture (the documented engine loop, put behind HTTP):
  * ONE background render thread does ALL GPU work -- `pipe.render_from_gpu(cam, params)` each tick, the
    same call every ParticleEngine viewer makes. CUDA is happiest single-threaded, so no other thread
    touches the GPU. Rendering is physics; it stays on the 4090, never shipped to the browser.
  * The frame is JPEG-encoded and pushed to the browser as an MJPEG stream (multipart/x-mixed-replace) --
    a plain <img> shows live video, no client-side decoder.
  * The browser sends mouse drag / wheel back as tiny /input requests; the render thread consumes them.
The physics (agent) and the human (operator) watch the SAME 127.0.0.1 stream -- the shared view, in motion.
"""
from __future__ import annotations

import io
import math
import sys
import threading
import time
from pathlib import Path
from urllib.parse import urlparse, parse_qs

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

# DYNAMIC-RESOLUTION LOD. The composite is per-pixel, so pixel count IS the cost. While the view is MOVING
# we render small and let the browser upscale -- fast + smooth, and the bigger effective splats keep the
# coverage gaps sub-pixel so they stop crawling ("migrating dots"). When the view settles we render full-res
# for sharpness. (LOD = level of detail = level of resolution; don't draw more pixels than the motion warrants.)
_W, _H = 1920, 1080        # IDLE/settled internal res (sharp on a 2K monitor)
_LO_W, _LO_H = 1152, 648   # MOVING internal res (upscaled) -- ~2x fewer pixels => ~2x the fps while you drag/spin
_AUTO_SPIN = 0.12          # rad/sec -- a GENTLE drift so the movie plays without making the surface crawl


def _blank_jpeg() -> bytes:
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (_W, _H), (4, 5, 11)).save(buf, "JPEG", quality=70)
    return buf.getvalue()


class LiveViewer:
    """One persistent GPU pipeline + camera, turned by a single render thread; frames read under a lock."""

    def __init__(self, term: str = "aPlanet"):
        import splat_appearance
        self._sa = splat_appearance
        self._lock = threading.Lock()
        self._latest = _blank_jpeg()
        self._term = term
        self._pending = term
        self._loaded = None
        # orbit state (spherical, aimed at the origin)
        self._azim = 0.0
        self._elev = 0.18
        self._radius = splat_appearance.scene_cam_distance(term)
        self._radius0 = self._radius
        self._in = {"dazim": 0.0, "delev": 0.0, "zoom": 0.0}
        self._last_input = 0.0     # wall-time of the last drag/zoom -> drives the moving-vs-settled LOD
        self._clients = 0                                          # active /stream connections
        self._running = True
        self._err = None
        self._t = threading.Thread(target=self._loop, name="live-render", daemon=True)
        self._t.start()

    # ── the render thread (sole owner of the GPU) ──
    def _loop(self):
        try:
            from ParticleEngine.gpu_pipeline import FullGPUPipeline
            from ParticleEngine.camera import FirstPersonCamera
            import numpy as np
            from PIL import Image
            pipe = FullGPUPipeline(bg=(0.015, 0.015, 0.04))
            cam = FirstPersonCamera((0.0, -self._radius, 0.0))
            params_hi = cam.params(_W, _H)        # settled: full res, sharp
            params_lo = cam.params(_LO_W, _LO_H)  # moving: fewer pixels, smooth (camera is unchanged; only the raster size)
            last = time.time()
            while self._running:
                now = time.time(); dt = min(0.1, now - last); last = now
                if self._clients <= 0:                                  # nobody watching -> free the shared 4090 (LM Studio needs it)
                    time.sleep(0.1); continue
                if self._pending != self._loaded:                       # (re)load the scene, on this thread
                    buf = self._sa.scene_buffer(self._pending)
                    if buf is not None:
                        pipe.upload(np.ascontiguousarray(buf, dtype=np.float32))
                        self._radius = self._radius0 = self._sa.scene_cam_distance(self._pending)
                        self._loaded = self._pending
                # apply input + auto-spin, then place the camera on the orbit sphere aimed at origin
                with self._lock:
                    self._azim += self._in["dazim"] + _AUTO_SPIN * dt
                    self._elev = max(-1.35, min(1.35, self._elev + self._in["delev"]))
                    self._radius = max(self._radius0 * 0.45, min(self._radius0 * 2.5,
                                       self._radius * (1.0 + self._in["zoom"])))
                    self._in["dazim"] = self._in["delev"] = self._in["zoom"] = 0.0
                    az, el, r = self._azim, self._elev, self._radius
                ce = math.cos(el)
                pos = (r * ce * math.sin(az), -r * ce * math.cos(az), r * math.sin(el))
                n = math.sqrt(pos[0] ** 2 + pos[1] ** 2 + pos[2] ** 2) or 1.0
                fx, fy, fz = -pos[0] / n, -pos[1] / n, -pos[2] / n     # look at the origin
                cam.position = np.array(pos, dtype=np.float32)
                cam.yaw = math.atan2(fy, fx)
                cam.pitch = math.atan2(fz, math.hypot(fx, fy))
                if self._loaded is None:
                    time.sleep(0.05); continue
                moving = (now - self._last_input) < 0.30               # dragging/zooming in the last 0.3s
                params = params_lo if moving else params_hi           # LOD: small while moving, full when settled
                img = pipe.render_from_gpu(cam, params)
                buf = io.BytesIO(); Image.fromarray(img).save(buf, "JPEG", quality=(72 if moving else 85))
                with self._lock:
                    self._latest = buf.getvalue()
                time.sleep(max(0.0, 1 / 60 - (time.time() - now)))    # cap 60fps so the fast (moving) LOD stays smooth
        except Exception as e:                                          # a dead render thread must be visible, not silent
            import traceback
            self._err = f"{e}\n{traceback.format_exc()}"
            print(f"[live_viewer] render thread died: {self._err}")

    # ── read/control surface (called from HTTP threads) ──
    def frame(self) -> bytes:
        with self._lock:
            return self._latest

    def input(self, dazim=0.0, delev=0.0, zoom=0.0):
        with self._lock:
            self._in["dazim"] += dazim; self._in["delev"] += delev; self._in["zoom"] += zoom
            if dazim or delev or zoom:
                self._last_input = time.time()   # mark "moving" -> the render thread drops to the fast LOD

    def set_scene(self, term: str):
        if term in self._sa.SCENES:
            self._pending = term

    @property
    def term(self) -> str:
        return self._loaded or self._pending


_VIEWER: LiveViewer | None = None
_VLOCK = threading.Lock()


def get_viewer() -> LiveViewer:
    global _VIEWER
    with _VLOCK:
        if _VIEWER is None:
            _VIEWER = LiveViewer()
        return _VIEWER


# ═══════════════════════════════════════════════════════════════════════
#  HTTP routing -- gallery.py delegates here; returns True if it handled the path
# ═══════════════════════════════════════════════════════════════════════
def handle(handler) -> bool:
    path = urlparse(handler.path).path
    qs = parse_qs(urlparse(handler.path).query)
    if path in ("/live", "/live.html"):
        _send(handler, 200, "text/html; charset=utf-8", _page().encode("utf-8")); return True
    if path == "/terms":
        import json, splat_appearance
        _send(handler, 200, "application/json", json.dumps(splat_appearance.scene_terms()).encode()); return True
    if path == "/input":
        v = get_viewer()
        v.input(dazim=_f(qs, "dazim"), delev=_f(qs, "delev"), zoom=_f(qs, "zoom"))
        _send(handler, 204, "text/plain", b""); return True
    if path == "/scene":
        term = (qs.get("term") or [""])[0]
        get_viewer().set_scene(term)
        _send(handler, 204, "text/plain", b""); return True
    if path == "/stream":
        _stream(handler); return True
    return False


def _f(qs, k) -> float:
    try:
        return float((qs.get(k) or ["0"])[0])
    except ValueError:
        return 0.0


def _send(handler, code, ctype, body: bytes):
    handler.send_response(code)
    handler.send_header("Content-Type", ctype)
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-cache")
    handler.end_headers()
    if body:
        handler.wfile.write(body)


def _stream(handler):
    v = get_viewer()
    handler.send_response(200)
    handler.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
    handler.send_header("Cache-Control", "no-cache, private")
    handler.send_header("Connection", "close")
    handler.end_headers()
    with v._lock:
        v._clients += 1                                             # wake the render thread
    try:
        while True:
            jpg = v.frame()
            handler.wfile.write(b"--frame\r\nContent-Type: image/jpeg\r\n")
            handler.wfile.write(f"Content-Length: {len(jpg)}\r\n\r\n".encode())
            handler.wfile.write(jpg)
            handler.wfile.write(b"\r\n")
            time.sleep(1 / 30)
    except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
        pass                                                            # the browser closed the tab -- fine
    finally:
        with v._lock:
            v._clients = max(0, v._clients - 1)                     # last viewer left -> render thread idles the GPU


def _page() -> str:
    try:
        from human_messenger import PHYSICS_READING
    except Exception:
        PHYSICS_READING = {}
    import splat_appearance
    terms = splat_appearance.scene_terms()
    readings = {t: PHYSICS_READING.get(t, "") for t in terms}
    import json
    return _PAGE.replace("__TERMS__", json.dumps(terms)).replace("__READINGS__", json.dumps(readings))


_PAGE = """<!doctype html><meta charset=utf-8><title>Chimera live viewer</title>
<meta name=viewport content="width=device-width,initial-scale=1">
<style>
 :root{color-scheme:dark}
 body{margin:0;background:#06070c;color:#cfe0ff;font-family:system-ui,-apple-system,sans-serif;
      display:flex;flex-direction:column;align-items:center;min-height:100vh}
 h1{font-weight:600;font-size:17px;margin:14px 0 2px}
 #bar{display:flex;gap:8px;flex-wrap:wrap;justify-content:center;margin:6px 0 10px}
 button{background:#111a2e;color:#cfe0ff;border:1px solid #2a3350;border-radius:8px;padding:6px 12px;
        font-size:13px;cursor:pointer}
 button.on{background:#24406e;border-color:#4a74c0;color:#fff}
 #stage{position:relative;width:1600px;max-width:96vw;aspect-ratio:16/9;background:#04050b;
        border:1px solid #2a3350;border-radius:12px;overflow:hidden;touch-action:none;cursor:grab}
 #stage.drag{cursor:grabbing}
 #view{width:100%;height:100%;display:block;user-select:none;-webkit-user-drag:none}
 #cap{max-width:720px;color:#8892b0;font-size:13px;text-align:center;margin:10px 14px 4px}
 #cap b{color:#ffe9a8}
 #hint{color:#59668a;font-size:12px;margin-bottom:20px}
</style>
<h1>Chimera &mdash; live interactive viewer <span style="color:#59668a;font-weight:400">(the shared view, in motion)</span></h1>
<div id=bar></div>
<div id=stage><img id=view src="/stream" alt="live render"></div>
<div id=cap></div>
<div id=hint>drag to orbit &middot; scroll to zoom &middot; it turns on its own so the movie plays</div>
<script>
const TERMS=__TERMS__, READINGS=__READINGS__;
let term=TERMS.includes("aPlanet")?"aPlanet":TERMS[0];
const bar=document.getElementById('bar'), cap=document.getElementById('cap'), stage=document.getElementById('stage');
function paintBar(){bar.innerHTML='';TERMS.forEach(t=>{const b=document.createElement('button');
  b.textContent=t;if(t===term)b.className='on';b.onclick=()=>{term=t;pick(t);};bar.appendChild(b);});}
function caption(){cap.innerHTML='<b>'+term+'</b>'+(READINGS[term]?' &mdash; physics expects: '+READINGS[term]:'');}
function pick(t){fetch('/scene?term='+encodeURIComponent(t));paintBar();caption();}
paintBar();caption();
// mouse / touch orbit -> /input (throttled by rAF)
let drag=false,lx=0,ly=0,pend={dazim:0,delev:0,zoom:0},sending=false;
function flush(){if(pend.dazim||pend.delev||pend.zoom){
  fetch('/input?dazim='+pend.dazim.toFixed(4)+'&delev='+pend.delev.toFixed(4)+'&zoom='+pend.zoom.toFixed(4));
  pend={dazim:0,delev:0,zoom:0};}sending=false;}
function queue(){if(!sending){sending=true;requestAnimationFrame(flush);}}
function down(x,y){drag=true;lx=x;ly=y;stage.classList.add('drag');}
function move(x,y){if(!drag)return;pend.dazim+=-(x-lx)*0.006;pend.delev+=(y-ly)*0.006;lx=x;ly=y;queue();}
function up(){drag=false;stage.classList.remove('drag');}
stage.addEventListener('mousedown',e=>down(e.clientX,e.clientY));
window.addEventListener('mousemove',e=>move(e.clientX,e.clientY));
window.addEventListener('mouseup',up);
stage.addEventListener('touchstart',e=>{const t=e.touches[0];down(t.clientX,t.clientY);},{passive:true});
stage.addEventListener('touchmove',e=>{const t=e.touches[0];move(t.clientX,t.clientY);},{passive:true});
stage.addEventListener('touchend',up);
stage.addEventListener('wheel',e=>{e.preventDefault();pend.zoom+=(e.deltaY>0?0.06:-0.06);queue();},{passive:false});
</script>
"""


if __name__ == "__main__":
    # standalone convenience: serve JUST the live viewer (gallery.py mounts it in the shared page)
    import functools, http.server

    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            if handle(self):
                return
            self.send_response(302); self.send_header("Location", "/live"); self.end_headers()

        def log_message(self, *a):
            pass

    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8766
    get_viewer()
    with http.server.ThreadingHTTPServer(("127.0.0.1", port), H) as srv:  # 127.0.0.1 only -- the studio's bind rule
        print(f"live viewer at http://127.0.0.1:{port}/live")
        srv.serve_forever()
