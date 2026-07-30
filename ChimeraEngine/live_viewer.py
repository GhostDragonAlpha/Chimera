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
        # THE TIME AXIS, held rather than auto-played. A membrane's movie runs t = 0 -> 1 over its
        # own real duration; scrubbing it is how you inspect a moment instead of watching it pass.
        self._t = 1.0
        self._loaded_t = None
        self._reload = False
        # orbit state (spherical, aimed at the origin)
        self._azim = 0.0
        self._elev = 0.18
        self._radius = splat_appearance.scene_cam_distance(term)
        self._radius0 = self._radius
        self._in = {"dazim": 0.0, "delev": 0.0, "zoom": 0.0}
        # WALK MODE. Every other membrane in this story is looked AT; this is the one you are
        # looked OUT of. The body's numbers come from theHuman and the planet -- nothing is set here.
        self._walk = None                 # a walker.Walker once someone asks to stand up
        self._walk_in = {"fwd": 0.0, "strafe": 0.0, "sprint": False,
                         "jump": False, "crouch": False, "mx": 0.0, "my": 0.0}
        self._walk_dirty = True
        self._view = "first"              # 'first' = through the eyes; 'third' = watching the body
        self._last_input = 0.0     # wall-time of the last drag/zoom -> drives the moving-vs-settled LOD
        self._clients = 0                                          # active /stream connections
        self._running = True
        self._err = None
        # NAMED IN FULL, deliberately: `_t` is the story's TIME axis. The thread that draws it is a
        # different thing, and when both were called `_t` the render loop handed a Thread object to
        # emit(t) and every frame came back blank.
        self._thread = threading.Thread(target=self._loop, name="live-render", daemon=True)
        self._thread.start()

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
                if self._walk is not None:
                    # ── STANDING IN IT ──────────────────────────────────────────────────────────
                    with self._lock:
                        wi = dict(self._walk_in)
                        self._walk_in["mx"] = self._walk_in["my"] = 0.0
                        self._walk_in["jump"] = False
                    self._walk.look(wi["mx"], wi["my"])
                    self._walk.move(wi["fwd"], wi["strafe"], wi["sprint"],
                                    wi["jump"], wi["crouch"], dt)
                    # the ground is rebuilt around the player only when they have moved far enough
                    # to matter -- the near shell is 180 m across, so a stride does not need one.
                    # Rebuilt when the player has moved far enough to matter, OR when the sun has --
                    # the clock runs 1:1 here, so at 15 deg/hour a half-degree is about two minutes.
                    # Standing still must not freeze the light; it is a real sky on a real rotation.
                    import walker as _wk
                    sun_moved = abs(self._walk.clock - getattr(self, "_walk_clock", -1e18)) > 120.0
                    if self._walk_dirty or self._walk_moved() > 12.0 or sun_moved:
                        self._ground_np = np.ascontiguousarray(_wk.scene_around(self._walk),
                                                               dtype=np.float32)
                        if self._view != "third":
                            pipe.upload(self._ground_np)
                        self._walk_anchor = (self._walk.x, self._walk.y)
                        self._walk_clock = self._walk.clock
                        self._walk_dirty = False
                    wx, wy = self._walk.x, self._walk.y
                    if self._view == "third":
                        # THE BODY CHANGES EVERY FRAME (the gait phase is the distance walked), so
                        # third person re-uploads ground+body each tick. The ground array is cached;
                        # the body is ~2,900 grains from a 48-pose cache -- the upload is the cost,
                        # and it is the same ~7 MB the rebuild path already pays.
                        body = _wk.body_buffer(self._walk)
                        pipe.upload(np.ascontiguousarray(
                            np.concatenate([self._ground_np, body], axis=0), dtype=np.float32))
                        # an over-the-shoulder orbit: behind the facing, raised by the look pitch,
                        # aimed at the chest -- and never below the ground it is looking across.
                        f = (-math.sin(self._walk.yaw), math.cos(self._walk.yaw))
                        r = (math.cos(self._walk.yaw), math.sin(self._walk.yaw))
                        e = max(-0.35, min(1.25, self._walk.pitch))
                        # 3.2 m, chest-high -- and OFF THE AXIS OF THE STRIDE. The legs swing in
                        # the sagittal plane (forward-up); a camera dead behind looks straight
                        # down that plane and the entire gait projects to a vertical line -- the
                        # "body all down the centre". 0.9 m to shoulder-side gives a three-quarter
                        # view: ~16 degrees off-axis, enough for the swing to show while forward
                        # stays forward.
                        D = 3.2
                        SIDE = 1.15
                        pivot = (wx, wy, self._walk.z + 0.70 * self._walk.eye + self._walk.crouch)
                        cx = wx - f[0] * D * math.cos(e) + r[0] * SIDE
                        cy = wy - f[1] * D * math.cos(e) + r[1] * SIDE
                        cz = pivot[2] + D * math.sin(e)
                        cz = max(cz, _wk.height_at(cx, cy) + 0.4)
                        cam.position = np.array([cx, cy, cz], dtype=np.float32)
                        dx, dy, dz = pivot[0] - cx, pivot[1] - cy, pivot[2] - cz
                        cam.yaw = math.atan2(dy, dx)
                        cam.pitch = math.atan2(dz, math.hypot(dx, dy))
                    else:
                        ex, ey, ez = self._walk.eye_pos
                        cam.position = np.array([ex, ey, ez], dtype=np.float32)
                        # yaw 0 looks along +Y, which is how the walker's own frame is defined
                        cam.yaw = self._walk.yaw + math.pi / 2.0
                        cam.pitch = self._walk.pitch
                    self._publish(pipe.render_from_gpu(cam, params_hi))
                    time.sleep(max(0.0, 1 / 60 - (time.time() - now)))
                    continue

                if (self._pending != self._loaded or self._t != self._loaded_t
                        or self._reload):                                # (re)load, on this thread
                    want_t = self._t
                    buf = self._sa.membrane_buffer(self._pending, want_t)
                    if buf is None:
                        buf = self._sa.scene_buffer(self._pending)       # a painted scene has no time axis
                    if buf is not None:
                        pipe.upload(np.ascontiguousarray(buf, dtype=np.float32))
                        if self._pending != self._loaded:                # keep the framing while scrubbing
                            self._radius = self._radius0 = self._sa.scene_cam_distance(self._pending)
                        self._loaded = self._pending
                        self._loaded_t = want_t
                        self._reload = False
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
                # ONE RESOLUTION, ALWAYS. This used to drop to 1152x648 whenever you touched the
                # mouse and snap back to 1920x1080 0.3s after you stopped. But the browser scales
                # both to the same display size, so the low pass MAGNIFIES every splat by 1.67x --
                # grains near pixel-size go visibly chunky the instant you drag, then shrink again.
                # That is the "inexplicable splat magnification" and the POP: the surface jumps
                # discontinuously because its rasterisation changed, not because anything moved.
                # A resolution switch can never be smooth -- pixels are discrete -- so the only
                # honest fix is not to switch. (Nothing offline ever reproduced this, because the
                # offline path renders at one size: max/median frame delta was 1.1x, flat.)
                # AND IT WAS BUYING ALMOST NOTHING. Measured on this scene, warm:
                #     1920x1080  128.5 ms   7.8 fps        1152x648  103.1 ms   9.7 fps
                #     1280x720    97.8 ms  10.2 fps         960x540  100.2 ms  10.0 fps
                # Nearly FLAT -- the cost is per-SPLAT work (project, bin, sort), not pixels. So the
                # switch traded a visible pop for 25 ms. Deleted.
                params = params_hi
                img = pipe.render_from_gpu(cam, params)
                self._publish(img)
                time.sleep(max(0.0, 1 / 60 - (time.time() - now)))    # cap 60fps so the fast (moving) LOD stays smooth
        except Exception as e:                                          # a dead render thread must be visible, not silent
            import traceback
            self._err = f"{e}\n{traceback.format_exc()}"
            print(f"[live_viewer] render thread died: {self._err}")

    def _publish(self, img):
        from PIL import Image
        buf = io.BytesIO(); Image.fromarray(img).save(buf, "JPEG", quality=85)
        with self._lock:
            self._latest = buf.getvalue()

    def _walk_moved(self) -> float:
        ax, ay = getattr(self, "_walk_anchor", (1e18, 1e18))
        return math.hypot(self._walk.x - ax, self._walk.y - ay)

    # ── read/control surface (called from HTTP threads) ──
    def frame(self) -> bytes:
        with self._lock:
            return self._latest

    def set_time(self, t: float):
        with self._lock:
            self._t = max(0.0, min(1.0, float(t)))

    def force_reload(self):
        with self._lock:
            self._reload = True

    def input(self, dazim=0.0, delev=0.0, zoom=0.0):
        with self._lock:
            self._in["dazim"] += dazim; self._in["delev"] += delev; self._in["zoom"] += zoom
            if dazim or delev or zoom:
                self._last_input = time.time()   # mark "moving" -> the render thread drops to the fast LOD

    def stand(self, on: bool = True, day=None, minute=None, lat=None, lon=None) -> dict:
        """Enter (or leave) the body. Standing up is EXPENSIVE -- aTerrain has to carve its
        drainage network before there is ground to stand on -- so it happens once, here, and
        never on the render thread's per-frame path."""
        if not on:
            with self._lock:
                self._walk = None
                self._reload = True          # the orbit view must reload its own buffer
            return {"walking": False}
        import walker as _wk
        # A DIFFERENT PLACE IS A DIFFERENT GROUND. If the picker moved, the old walker's field is
        # the wrong planet's-worth of hills -- drop it and carve the new place (cached per place,
        # so returning somewhere is instant).
        want = _wk._place_key(lat, lon)
        if self._walk is not None and getattr(self._walk, "_place_key", None) != want:
            with self._lock:
                self._walk = None
        if self._walk is None:
            w = _wk.Walker(lat, lon)         # spawns at the middle of that place's patch
            w._place_key = want
            with self._lock:
                self._walk = w
                self._walk_dirty = True
        if day is not None and minute is not None:
            # the date and hour chosen BEFORE play -- same formula as /clock, applied at entry
            with self._lock:
                w = self._walk
                w.clock = float(day) * w.day_s + (float(minute) / 1440.0) * w.day_s
                self._walk_dirty = True
        return {"walking": True, **self._walk.readout()}

    def walk_input(self, fwd=0.0, strafe=0.0, sprint=False, jump=False, crouch=False, mx=0.0, my=0.0):
        with self._lock:
            if self._walk is None:
                return {"walking": False}
            self._walk_in["fwd"] = float(fwd)
            self._walk_in["strafe"] = float(strafe)
            self._walk_in["sprint"] = bool(sprint)
            self._walk_in["crouch"] = bool(crouch)
            self._walk_in["jump"] = self._walk_in["jump"] or bool(jump)   # never drop a jump between frames
            self._walk_in["mx"] += float(mx)
            self._walk_in["my"] += float(my)
            w = self._walk
        return {"walking": True, "view": self._view, **w.readout()}

    def set_view(self, mode):
        """First person or third. Switching INTO third forces one upload on the next tick even if
        nothing else changed (the cached ground alone is on the GPU; the body must join it)."""
        with self._lock:
            self._view = "third" if str(mode) == "third" else "first"
            self._walk_dirty = True
        return {"view": self._view}

    def set_walk_rate(self, x):
        """Gear the standing body's clock. Held on the walker itself so the sun, the seasons and
        the readout all move together -- there is one clock, so there is one place to gear it."""
        with self._lock:
            if self._walk is None:
                return {"walking": False}
            self._walk.rate = max(0.0, float(x))
            w = self._walk
        return {"walking": True, **w.readout()}

    def set_walk_clock(self, day, minute):
        """Jump the standing body's clock to a chosen day and minute. Sets the dirty flag directly:
        the render loop's own rebuild gate is 'has the sun moved 2 minutes', and a small hour-scrub
        can sit under it -- a slider that sometimes does nothing teaches the user it never does."""
        with self._lock:
            if self._walk is None:
                return {"walking": False}
            w = self._walk
            w.clock = float(day) * w.day_s + (float(minute) / 1440.0) * w.day_s
            self._walk_dirty = True
        return {"walking": True, **w.readout()}

    def set_scene(self, term: str):
        # Accept anything the viewer OFFERS, not just the hand-authored SCENES dict. A membrane in
        # story/ emits its own matter and appears in scene_terms(); gating on SCENES silently
        # refused it -- the label changed and the scene did not, which is the worst kind of failure
        # because it looks like it worked.
        if term in self._sa.scene_terms():
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
        blind = (qs.get("blind") or ["0"])[0] not in ("0", "", "false")
        _send(handler, 200, "text/html; charset=utf-8", _page(blind).encode("utf-8")); return True
    if path == "/terms":
        import json, splat_appearance
        _send(handler, 200, "application/json", json.dumps(splat_appearance.scene_terms()).encode()); return True
    if path == "/input":
        v = get_viewer()
        v.input(dazim=_f(qs, "dazim"), delev=_f(qs, "delev"), zoom=_f(qs, "zoom"))
        _send(handler, 204, "text/plain", b""); return True
    if path == "/stand":
        # STAND UP / SIT DOWN. This is the only place in the viewer where the camera stops being a
        # thing that looks AT a membrane and becomes a thing INSIDE one.
        import json as _json
        on = (qs.get("on") or ["1"])[0] not in ("0", "", "false")
        try:
            day = _f(qs, "day") if "day" in qs else None
            minute = _f(qs, "minute") if "minute" in qs else None
            lat = _f(qs, "lat") if "lat" in qs else None
            lon = _f(qs, "lon") if "lon" in qs else None
            r = get_viewer().stand(on, day, minute, lat, lon)
        except Exception as e:
            import traceback; traceback.print_exc()
            r = {"walking": False, "error": str(e)}
        _send(handler, 200, "application/json", _json.dumps(r).encode()); return True
    if path == "/walk":
        import json as _json
        r = get_viewer().walk_input(
            fwd=_f(qs, "fwd"), strafe=_f(qs, "strafe"),
            sprint=(qs.get("sprint") or ["0"])[0] == "1",
            jump=(qs.get("jump") or ["0"])[0] == "1",
            crouch=(qs.get("crouch") or ["0"])[0] == "1",
            mx=_f(qs, "mx"), my=_f(qs, "my"))
        _send(handler, 200, "application/json", _json.dumps(r).encode()); return True
    if path == "/view":
        import json as _json
        r = get_viewer().set_view((qs.get("mode") or ["first"])[0])
        _send(handler, 200, "application/json", _json.dumps(r).encode()); return True
    if path == "/place":
        # WHAT IS THERE, before you go: the planet's own numbers read at a latitude. Instant --
        # no carving -- so the picker can narrate while you drag.
        import json as _json
        import walker as _wk
        info = _wk.place_info(_f(qs, "lat") if "lat" in qs else None,
                              _f(qs, "lon") if "lon" in qs else None)
        _send(handler, 200, "application/json", _json.dumps(info).encode()); return True
    if path == "/rate":
        import json as _json
        r = get_viewer().set_walk_rate(_f(qs, "x"))
        _send(handler, 200, "application/json", _json.dumps(r).encode()); return True
    if path == "/clock":
        # THE WALKER'S CLOCK, SCRUBBED. Day + minute-of-day rather than a bare fraction, because the
        # year is 383.21 days: a fraction lands mid-day and drags the hour with it (the bug that
        # opened the game at 04:16). Whole days and minutes keep the two dials orthogonal.
        import json as _json
        r = get_viewer().set_walk_clock(_f(qs, "day"), _f(qs, "minute"))
        _send(handler, 200, "application/json", _json.dumps(r).encode()); return True
    if path == "/time":
        get_viewer().set_time(_f(qs, "t"))
        _send(handler, 204, "text/plain", b""); return True
    if path == "/free":
        # THE HUMAN'S DIALS. Writing a free parameter regrows the membrane AND EVERYTHING BELOW IT,
        # because that is what a free parameter IS: the one input a subtree's numbers are not
        # determined by. Move it and the whole cascade re-derives -- which is the fastest way to see
        # what a variable actually does.
        import json as _json, subprocess, sys as _sys
        term = (qs.get("term") or [""])[0]
        name = (qs.get("name") or [""])[0]
        try:
            val = float((qs.get("value") or ["0"])[0])
        except ValueError:
            val = 0.0
        import splat_appearance as _sa
        folder = _sa._find_membrane(term)
        if folder is not None and name:
            tj = folder / "trained.json"
            cur = _json.loads(tj.read_text()) if tj.exists() else {}
            cur[name] = val
            tj.write_text(_json.dumps(cur, indent=2))
            subprocess.run([_sys.executable, str(_HERE.parent / "story" / "grow.py")],
                           capture_output=True, cwd=str(_HERE.parent))
            get_viewer().force_reload()
        _send(handler, 204, "text/plain", b""); return True
    if path == "/lens":
        # THE LENS. Deliberately a DIFFERENT endpoint from /free, because it is a different kind of
        # act: /free changes what the world IS and re-derives the whole subtree; /lens changes only
        # what the camera does with it. Nothing is regrown, because nothing downstream depends on a
        # camera setting -- which is exactly the property that makes an exaggeration honest.
        import json as _json
        term = (qs.get("term") or [""])[0]
        name = (qs.get("name") or [""])[0]
        try:
            val = float((qs.get("value") or ["1"])[0])
        except ValueError:
            val = 1.0
        import splat_appearance as _sa
        folder = _sa._find_membrane(term)
        if folder is not None and name:
            lj = folder / "lens.json"
            cur = _json.loads(lj.read_text()) if lj.exists() else {}
            cur[name] = val
            lj.write_text(_json.dumps(cur, indent=2))
            get_viewer().force_reload()
        _send(handler, 204, "text/plain", b""); return True
    if path == "/scene":
        term = (qs.get("term") or [""])[0]
        get_viewer().set_scene(term)
        _send(handler, 204, "text/plain", b""); return True
    if path == "/stream":
        _stream(handler); return True
    if path == "/frame":
        # ONE REQUEST = ONE PICTURE. It is a web server; you ask it for the page.
        # `/frame?term=theCooling` sets the scene, waits for the renderer to actually produce that
        # scene, and returns a single JPEG. No browser, no clicking, and no stale frame -- which is
        # what made the shared view read the RIGHT label over the WRONG picture.
        v = get_viewer()
        term = (qs.get("term") or [""])[0]
        if term:
            v.set_scene(term)
        before = v.frame()
        with v._lock:
            v._clients += 1                                          # wake the render thread (it idles the GPU otherwise)
        try:
            # WHAT A REFRESH ACTUALLY IS. `_latest` starts as a BLANK jpeg, and the thread must
            # (a) notice a client, (b) upload the scene to the GPU, (c) draw. Grab too early and you
            # get black. And `v.term` returns `_loaded or _pending`, so it reports the NEW name
            # instantly and proves nothing. Wait for the scene to be LOADED and a NEW frame drawn.
            deadline = time.time() + 30.0
            while time.time() < deadline:
                if ((not term) or v._loaded == term) and v.frame() is not before:
                    break
                time.sleep(0.05)
            time.sleep(0.20)                                          # one more frame, so it is settled
            jpg = v.frame()
        finally:
            with v._lock:
                v._clients = max(0, v._clients - 1)
        _send(handler, 200, "image/jpeg", jpg); return True
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


_STORY = Path(__file__).resolve().parent.parent / "story"
_PLAIN = "**In plain words —**"


def _plain_of(folder) -> str:
    s = folder / "story.md"
    if not s.exists():
        return ""
    txt = s.read_text(encoding="utf-8", errors="replace")
    for line in txt.splitlines():
        t = line.strip()
        if t.startswith(_PLAIN):
            return t[len(_PLAIN):].strip()
    return ""


def _tree_of(folder):
    """The membrane tree, as the FILESYSTEM has it -- name, its plain words, the numbers it hands
    down, and its children. THE HIERARCHY IS THE NAVIGATION: a flat row of buttons cannot show that
    theStar and thePlanets live INSIDE theSolarSystem, which is the one fact the whole method is
    built on."""
    import json
    node = {"name": folder.name, "plain": _plain_of(folder), "children": [], "numbers": {}}
    nj = folder / "numbers.json"
    if nj.exists():
        try:
            n = json.loads(nj.read_text())
            node["numbers"] = {k: v for k, v in list(n.items())[:10]}
        except Exception:
            pass
    node["membrane"] = (folder / "physics.py").exists()
    node["duration_s"] = node["numbers"].get("duration_s")
    node["extent_m"] = node["numbers"].get("extent_m")
    # WHICH OF THIS MEMBRANE'S INPUTS ARE ACTUALLY FREE. Only these get sliders: a handle on a
    # DERIVED number would let a human set a value the physics forbids, which is the one thing the
    # whole method exists to prevent. The absence of a handle is itself the lesson -- that number
    # belongs to the universe, not to you.
    #
    # LENS is the other list, and it is deliberately kept separate rather than merged into one
    # "settings" panel: a FREE dial changes what the world IS and re-derives everything below it;
    # a LENS dial changes only what the camera does with what is already there. Showing them in one
    # box would teach a person that relief exaggeration and day length are the same kind of thing,
    # and they are opposites -- one is a fact you may choose, the other is a lie you may see through.
    node["free"] = {}
    node["lens"] = {}
    py = folder / "physics.py"
    if py.exists():
        try:
            import ast as _ast
            tree = _ast.parse(py.read_text(encoding="utf-8", errors="replace"))
            for st in tree.body:
                if isinstance(st, _ast.Assign):
                    nm = getattr(st.targets[0], "id", "")
                    if nm in ("FREE", "LENS"):
                        node[nm.lower()] = _ast.literal_eval(st.value)
        except Exception:
            pass
    tj = folder / "trained.json"
    if tj.exists():
        try:
            node["free_set"] = json.loads(tj.read_text())
        except Exception:
            node["free_set"] = {}
    lj = folder / "lens.json"
    if lj.exists():
        try:
            node["lens_set"] = json.loads(lj.read_text())
        except Exception:
            node["lens_set"] = {}
    for c in sorted(d for d in folder.iterdir() if d.is_dir() and not d.name.startswith((".", "_"))):
        if (c / "story.md").exists():
            node["children"].append(_tree_of(c))
    return node


def story_tree():
    if not _STORY.is_dir():
        return []
    return [_tree_of(d) for d in sorted(_STORY.iterdir())
            if d.is_dir() and not d.name.startswith((".", "_")) and (d / "story.md").exists()]


def _page(blind: bool = False) -> str:
    """The shared view. `blind=1` withholds the physics's expected reading.

    THE LIGHT MUST COME FROM CHIMERA -- a dyad judges what the ENGINE renders, live and in motion,
    not a still someone chose the camera and the moment for. But this page normally prints
    "physics expects: ..." beside the render, because the OPERATOR is entitled to see both sides.
    A proxy eye is not: shown the expected answer, it would confirm rather than observe, and the
    dyad becomes theatre. So blind mode serves the identical picture with the caption withheld --
    same light, same scene, no answer."""
    try:
        from human_messenger import PHYSICS_READING
    except Exception:
        PHYSICS_READING = {}
    import splat_appearance
    terms = splat_appearance.scene_terms()
    readings = {} if blind else {t: PHYSICS_READING.get(t, "") for t in terms}
    # WHICH OF THESE IS REAL? A term with a folder in story/ is a MEMBRANE: its numbers are derived
    # from its parent and its picture is emitted by the same law. A term without one is a PAINTED
    # SCENE -- a hand-authored entry that merely shares a name with a term the story declares.
    # They looked identical here, so a painting could be mistaken for a proven world (theTerrain's
    # relief was 0.13 of its radius because someone PICKED 0.13 -- with no parent, nothing could
    # contradict it). The viewer now says which is which, so nobody has to guess.
    membranes = set(splat_appearance.membrane_terms())
    kinds = {t: ("membrane" if t in membranes else "painted") for t in terms}
    import json
    return (_PAGE.replace("__TERMS__", json.dumps(terms))
                 .replace("__READINGS__", json.dumps(readings))
                 .replace("__KINDS__", json.dumps(kinds))
                 .replace("__TREE__", json.dumps(story_tree())))


_PAGE = """<!doctype html><meta charset=utf-8><title>Chimera</title>
<meta name=viewport content="width=device-width,initial-scale=1">
<style>
 :root{color-scheme:dark;--bg:#06070c;--panel:#0b0e17;--line:#1e2740;--ink:#cfe0ff;--dim:#6b7899;
       --law:#7fd18a;--inst:#e8705c;--paint:#5c6683;--hot:#ffd98a}
 *{box-sizing:border-box}
 body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.5 system-ui,-apple-system,sans-serif;
      height:100vh;display:grid;grid-template-columns:300px 1fr;grid-template-rows:100vh}
 aside{background:var(--panel);border-right:1px solid var(--line);overflow-y:auto;padding:14px 0 40px}
 aside h1{font-size:15px;margin:0 16px 2px;font-weight:650}
 aside p.sub{margin:0 16px 14px;color:var(--dim);font-size:12px}
 .node{padding:5px 10px 5px 0;cursor:pointer;border-left:2px solid transparent;display:flex;gap:7px;align-items:baseline}
 .node:hover{background:#121a2c}
 .node.on{background:#1b2942;border-left-color:#5f8ee0}
 .node .nm{font-size:13px}
 /* THE PREFIX IS A CLASSIFICATION. `the` names the LAW -- what a thing IS. `a` names the
    INSTANCE grown from it. They are different kinds of claim, so they get different colours. */
 .node.inst .nm{color:var(--inst)}
 .node.paint .nm{color:var(--paint)}
 .dot{width:6px;height:6px;border-radius:50%;background:var(--law);flex:none;margin-top:6px}
 .node.inst .dot{background:var(--inst)}
 .node.paint .dot{background:transparent;border:1px solid var(--paint)}
 .kids{overflow:hidden}
 main{display:grid;grid-template-rows:1fr auto;min-width:0}
 #stage{position:relative;background:#04050b;overflow:hidden;touch-action:none;cursor:grab}
 #stage.drag{cursor:grabbing}
 #view{width:100%;height:100%;object-fit:contain;display:block;user-select:none;-webkit-user-drag:none}
 #hud{position:absolute;left:16px;top:14px;pointer-events:none;max-width:60%}
 #hud b{font-size:20px;color:#fff;letter-spacing:.2px}
 #hud .tag{font-size:11px;padding:2px 7px;border-radius:99px;border:1px solid;margin-left:8px;vertical-align:3px}
 .t-law{color:var(--law);border-color:#2c5f3a}
 .t-inst{color:var(--inst);border-color:#6e392f}
 .t-paint{color:var(--paint);border-color:#39415c}
 #plain{margin-top:8px;color:#b9c8e6;font-size:14px;max-width:640px;text-shadow:0 1px 8px #000}
 #serial{margin-top:6px;color:var(--dim);font:11px ui-monospace,Menlo,monospace}
 footer{border-top:1px solid var(--line);background:var(--panel);padding:10px 16px;display:flex;
        gap:26px;align-items:center;flex-wrap:wrap;min-height:52px}
 footer .num{font:12px ui-monospace,Menlo,monospace;color:var(--dim);white-space:nowrap}
 footer .num i{color:var(--hot);font-style:normal}
 footer .hint{margin-left:auto;color:#4d587a;font-size:11px}
 /* THE ONLY HANDLES IN THE GAME. Free parameters and time -- never a derived number. */
 #dials{position:absolute;right:14px;top:14px;width:250px;background:#0b0e17dd;border:1px solid var(--line);
        border-radius:10px;padding:11px 13px 13px;backdrop-filter:blur(3px)}
 #dials h3{margin:0 0 3px;font-size:11px;letter-spacing:.7px;text-transform:uppercase;color:var(--dim)}
 #dials .note{margin:0 0 9px;font-size:10px;color:#4d587a;line-height:1.35}
 #dials label{display:block;font-size:11px;color:#9fb0d0;margin:9px 0 2px}
 #dials label i{float:right;font-style:normal;color:var(--hot);font-family:ui-monospace,Menlo,monospace}
 #dials input[type=range]{width:100%;accent-color:#5f8ee0;height:16px}
 #dials .free label i{color:#e8a05c}
 /* THE BODY. Only offered on theHuman's own ground -- you cannot stand on a star. */
 #body{position:absolute;left:16px;bottom:14px}
 #body button{background:#131a2b;color:#cfe0ff;border:1px solid #2b3552;border-radius:8px;
              padding:8px 14px;font-size:12px;cursor:pointer;letter-spacing:.3px}
 #body button:hover{background:#1b2540;border-color:#41527d}
 #body button.on{background:#2a1c12;border-color:#7a4b26;color:#e8a05c}
 #walkhud{margin-top:9px;font:11px ui-monospace,Menlo,monospace;color:#9fb0d0;line-height:1.6;
          text-shadow:0 1px 6px #000;display:none}
 #walkhud i{color:#e8a05c;font-style:normal}
 #walkhud.on{display:block}
 #stage.walking{cursor:none}
</style>
<aside>
  <h1>Chimera</h1>
  <p class=sub>the story, as a hierarchy &mdash; click any membrane<br>
     <span style="color:#7fd18a">&#9679; the</span> = the law &nbsp;
     <span style="color:#e8705c">&#9679; a</span> = an instance &nbsp;
     <span style="color:#5c6683">&#9675;</span> = not built</p>
  <div id=tree></div>
</aside>
<main>
  <div id=stage>
    <img id=view src="/stream" alt="live render">
    <div id=hud><div><b id=nm></b><span id=tag class=tag></span></div>
      <div id=plain></div><div id=serial></div></div>
    <div id=dials>
      <h3>time</h3>
      <div id=orbitclock>
        <p class=note>its movie, held still. t is this membrane's own beginning to its own settled end.</p>
        <label>t <i id=tval>1.000</i></label>
        <input type=range id=tslider min=0 max=1000 value=1000>
      </div>
      <div id=walkclock style="display:none">
        <p class=note>pick WHEN, then press play. once standing the clock runs at theHumanClock's
        gear for a body -- exactly 1:1, a second is a second -- and these two scrub it live:
        the day across the year for the seasons, the hour for the sun.</p>
        <label>day of the year <i id=dayval></i></label>
        <input type=range id=dayslider min=0 max=382 step=1 value=96>
        <label>time of day <i id=hourval></i></label>
        <input type=range id=hourslider min=0 max=1439 step=1 value=540>
        <label>latitude <i id=latval></i></label>
        <input type=range id=latslider min=-850 max=850 step=5 value=308>
        <label>longitude <i id=lonval></i></label>
        <input type=range id=lonslider min=-180 max=180 step=1 value=0>
        <p class=note id=placeinfo></p>
      </div>
      <div id=freebox></div>
      <div id=lensbox></div>
    </div>
    <div id=body>
      <button id=standbtn>&#9654; play</button>
      <div id=walkhud></div>
    </div>
  </div>
  <footer><div id=nums></div><div class=hint id=hint>drag to orbit &middot; scroll to zoom &middot; it turns on its own</div></footer>
</main>
<script>
const TREE=__TREE__, READINGS=__READINGS__, KINDS=__KINDS__, TERMS=__TERMS__;
let term=null, INDEX={}, PATH={};
function index(n,trail){INDEX[n.name]=n;PATH[n.name]=trail.concat(n.name);
  (n.children||[]).forEach(c=>index(c,PATH[n.name]));}
TREE.forEach(n=>index(n,[]));
const treeEl=document.getElementById('tree');
function row(n,depth){
  const d=document.createElement('div');
  d.className='node'+(n.membrane?(n.name[0]==='a'&&n.name[1]===n.name[1].toUpperCase()?' inst':''):' paint');
  d.style.paddingLeft=(10+depth*15)+'px';
  d.innerHTML='<span class=dot></span><span class=nm>'+n.name+'</span>';
  d.onclick=()=>pick(n.name);
  d.dataset.name=n.name;
  treeEl.appendChild(d);
  (n.children||[]).forEach(c=>row(c,depth+1));
}
TREE.forEach(n=>row(n,0));
// terms that exist as scenes but have no folder (painted) get listed after the tree
TERMS.filter(t=>!INDEX[t]).forEach(t=>{
  const d=document.createElement('div');
  d.className='node paint';d.style.paddingLeft='10px';
  d.innerHTML='<span class=dot></span><span class=nm>'+t+'</span>';
  d.onclick=()=>pick(t);d.dataset.name=t;treeEl.appendChild(d);});
function pick(t){
  if(WALKING && t!=='theHuman') sitDown();   /* WALKING is `var` below: undefined here on first load, never a throw */
  term=t;
  fetch('/scene?term='+encodeURIComponent(t));
  document.querySelectorAll('.node').forEach(e=>e.classList.toggle('on',e.dataset.name===t));
  const n=INDEX[t]||{}, live=(KINDS[t]==='membrane');
  const inst=(t[0]==='a'&&t[1]===t[1].toUpperCase());
  document.getElementById('nm').textContent=t;
  const tg=document.getElementById('tag');
  tg.textContent=live?(inst?'an instance':'the law'):'not built';
  tg.className='tag '+(live?(inst?'t-inst':'t-law'):'t-paint');
  document.getElementById('plain').textContent=n.plain||(READINGS[t]?('physics expects: '+READINGS[t]):'');
  // WHAT t=1 MEANS. Until the clocks were wired, every membrane's movie ran 0->1 in an arbitrary
  // unit and the fourth dimension was unlabelled. This says the real elapsed time.
  const d=n.duration_s;
  let dur='';
  if(typeof d==='number'&&d>0){
    const U=[[3.1557e16,'Gyr'],[3.1557e13,'Myr'],[3.1557e7,'yr'],[86400,'days'],[3600,'h'],[60,'min'],[1,'s']];
    for(const [u,nm] of U){ if(d>=u){ dur=(d/u).toPrecision(3)+' '+nm; break; } }
    if(!dur) dur=d.toExponential(2)+' s';
  }
  // AND HOW BIG IT IS. Every membrane emits at radius ~1 locally, so on screen a galaxy and a star
  // are the same size; without this a person cannot tell 15 kpc from 700,000 km. Light-crossing is
  // given too, because above planetary scale a distance is really a WAIT -- the same wait a ship's
  // thruster has to serve.
  const C_=2.99792458e8, YR=3.1557e7;
  const LEN=[[3.0857e19,'kpc'],[3.0857e16,'pc'],[C_*YR,'light-years'],[1.496e11,'AU'],
             [6.957e8,'solar radii'],[6.371e6,'Earth radii'],[1e3,'km'],[1,'m']];
  const TIM=[[3.1557e16,'Gyr'],[3.1557e13,'Myr'],[YR,'yr'],[86400,'days'],[3600,'h'],[60,'min'],[1,'s']];
  function say(v,tab){ for(const [u,nm] of tab){ if(v>=u) return (v/u).toPrecision(3)+' '+nm; }
                       return v.toExponential(2)+' '+tab[tab.length-1][1]; }
  const e=n.extent_m;
  let size='';
  if(typeof e==='number'&&e>0) size='   ·   '+say(e,LEN)+' across, light takes '+say(e/C_,TIM);
  document.getElementById('serial').textContent=(PATH[t]||[t]).join(' / ')
      +(dur?('   ·   its movie spans '+dur):'')+size;
  const nums=n.numbers||{};
  paintFree();
  if(typeof showStand==='function') showStand();
  tval.textContent=(tsl.value/1000).toFixed(3)+elapsed(tsl.value/1000);
  document.getElementById('nums').innerHTML=Object.keys(nums).slice(0,7).map(k=>{
    let v=nums[k]; if(typeof v==='number') v=(Math.abs(v)>=1e5||(v!==0&&Math.abs(v)<1e-3))?v.toExponential(3):(+v.toFixed(4));
    return '<span class=num>'+k+' <i>'+v+'</i></span>';}).join(' &nbsp; ');
}
// ── TIME: scrub the membrane's own movie ──────────────────────────────────────────
// DECLARED BEFORE THE FIRST pick() CALL, and that ordering is load-bearing: pick() reads `tval`,
// and a `const` is in its temporal dead zone until this line RUNS -- so with the call above this
// declaration, the initial pick() threw right there, the script died mid-file, and everything
// below (this slider's oninput, the orbit drag handlers, the whole walk block) silently never
// existed. The page LOOKED alive because pick's first lines -- set the term, fetch the scene --
// run before the throw: scenes switched while the script was a corpse from here down.
const tsl=document.getElementById('tslider'), tval=document.getElementById('tval');
let tTimer=null;
pick(TERMS.includes('theSolarSystem')?'theSolarSystem':TERMS[0]);
function elapsed(frac){
  const n=INDEX[term]||{}, d=n.duration_s;
  if(typeof d!=='number'||d<=0) return '';
  const v=d*frac, U=[[3.1557e16,'Gyr'],[3.1557e13,'Myr'],[3.1557e7,'yr'],[86400,'d'],[3600,'h'],[60,'min'],[1,'s']];
  for(const [u,nm] of U){ if(v>=u) return '  =  '+(v/u).toPrecision(3)+' '+nm; }
  return '  =  '+v.toExponential(2)+' s';
}
tsl.oninput=()=>{ const f=tsl.value/1000; tval.textContent=f.toFixed(3)+elapsed(f);
  clearTimeout(tTimer); tTimer=setTimeout(()=>fetch('/time?t='+f.toFixed(4)),90); };

// ── FREE PARAMETERS: the only other handles, and moving one re-derives the whole subtree ──
function paintFree(){
  const n=INDEX[term]||{}, F=n.free||{}, set=n.free_set||{}, box=document.getElementById('freebox');
  const keys=Object.keys(F);
  if(!keys.length){ box.innerHTML='<h3 style="margin-top:14px">no free dials</h3>'
    +'<p class=note>every number here is derived from its parent. that is not a limitation &mdash; '
    +'it is what makes them true.</p>'; return; }
  let h='<h3 style="margin-top:14px">the human’s dials</h3>'
       +'<p class=note>the only inputs this membrane is <i>not</i> determined by. move one and '
       +'everything below re-derives.</p><div class=free>';
  for(const k of keys){
    const f=F[k], cur=(k in set)?set[k]:f.default;
    const lo=Math.log10(f.lo), hi=Math.log10(f.hi), pos=Math.round(1000*(Math.log10(cur)-lo)/(hi-lo));
    h+='<label>'+f.label+' <i id="fv_'+k+'">'+cur.toPrecision(4)+' '+(f.unit||'')+'</i></label>'
      +'<input type=range data-k="'+k+'" data-lo="'+lo+'" data-hi="'+hi+'" min=0 max=1000 value="'+pos+'">';
  }
  box.innerHTML=h+'</div>';
  box.querySelectorAll('input[type=range]').forEach(el=>{
    let tm=null;
    el.oninput=()=>{
      const lo=+el.dataset.lo, hi=+el.dataset.hi, k=el.dataset.k;
      const v=Math.pow(10, lo+(hi-lo)*el.value/1000);
      document.getElementById('fv_'+k).textContent=v.toPrecision(4)+' '+((INDEX[term].free[k].unit)||'');
      clearTimeout(tm); tm=setTimeout(()=>{
        fetch('/free?term='+encodeURIComponent(term)+'&name='+encodeURIComponent(k)+'&value='+v)
          .then(()=>setTimeout(()=>location.reload(),1400));
      },420);
    };
  });
  paintLens();
}

// ── THE LENS: dials that change the PICTURE and nothing else ──────────────────────
// Kept in its own box, below the free dials, because it is the opposite kind of thing. A free dial
// is a fact you are allowed to choose; a lens dial is a LIE THE RENDER IS TELLING, shown to you with
// the handle to turn it off. Set them all to 1 and you see the world at true scale -- which is
// usually a smooth ball and an empty black disk, and that is the honest answer.
function paintLens(){
  const n=INDEX[term]||{}, L=n.lens||{}, set=n.lens_set||{}, box=document.getElementById('lensbox');
  if(!box) return;
  const keys=Object.keys(L);
  if(!keys.length){ box.innerHTML=''; return; }
  let h='<h3 style="margin-top:16px">the lens <span class=note style="font-weight:400">'
       +'&mdash; changes what you see, never what is</span></h3>'
       +'<p class=note>true scale is mostly invisible: this world&rsquo;s tallest mountain is two parts '
       +'in a thousand of its radius. every exaggeration is declared here and can be turned back.</p>'
       +'<div class=free>';
  for(const k of keys){
    const f=L[k], cur=(k in set)?set[k]:f.default;
    const lo=Math.log10(f.lo||0.01), hi=Math.log10(f.hi), pos=Math.round(1000*(Math.log10(Math.max(cur,f.lo||0.01))-lo)/(hi-lo));
    h+='<label>'+f.label+' <i id="lv_'+k+'">'+(+cur).toPrecision(3)+' '+(f.unit||'')+'</i></label>'
      +'<input type=range data-k="'+k+'" data-lo="'+lo+'" data-hi="'+hi+'" min=0 max=1000 value="'+pos+'">';
  }
  box.innerHTML=h+'</div><button id="truescale">show it at true scale</button>';
  box.querySelectorAll('input[type=range]').forEach(el=>{
    let tm=null;
    el.oninput=()=>{
      const lo=+el.dataset.lo, hi=+el.dataset.hi, k=el.dataset.k;
      const v=Math.pow(10, lo+(hi-lo)*el.value/1000);
      document.getElementById('lv_'+k).textContent=v.toPrecision(3)+' '+((INDEX[term].lens[k].unit)||'');
      // NO PAGE RELOAD. A lens change re-emits the same membrane; nothing downstream is regrown,
      // so the picture updates on the next frame and the panel keeps its state.
      clearTimeout(tm); tm=setTimeout(()=>{
        fetch('/lens?term='+encodeURIComponent(term)+'&name='+encodeURIComponent(k)+'&value='+v);
      },300);
    };
  });
  const b=document.getElementById('truescale');
  if(b) b.onclick=()=>{
    Promise.all(keys.map(k=>fetch('/lens?term='+encodeURIComponent(term)
      +'&name='+encodeURIComponent(k)+'&value='+(L[k].lo||1))))
      .then(()=>setTimeout(()=>location.reload(),900));
  };
}
let drag=false,lx=0,ly=0,pend={dazim:0,delev:0,zoom:0},sending=false;
const stage=document.getElementById('stage');
function flush(){if(pend.dazim||pend.delev||pend.zoom){
  fetch('/input?dazim='+pend.dazim.toFixed(4)+'&delev='+pend.delev.toFixed(4)+'&zoom='+pend.zoom.toFixed(4));
  pend={dazim:0,delev:0,zoom:0};}sending=false;}
function queue(){if(!sending){sending=true;requestAnimationFrame(flush);}}
function down(x,y){drag=true;lx=x;ly=y;stage.classList.add('drag');}
function move(x,y){if(!drag)return;
  if(WALKING){if(document.pointerLockElement!==stage){mdx+=x-lx;mdy+=y-ly;}lx=x;ly=y;return;}
  pend.dazim+=-(x-lx)*0.006;pend.delev+=(y-ly)*0.006;lx=x;ly=y;queue();}
function up(){drag=false;stage.classList.remove('drag');}
stage.addEventListener('mousedown',e=>down(e.clientX,e.clientY));
window.addEventListener('mousemove',e=>move(e.clientX,e.clientY));
window.addEventListener('mouseup',up);
stage.addEventListener('touchstart',e=>{const t=e.touches[0];down(t.clientX,t.clientY);},{passive:true});
stage.addEventListener('touchmove',e=>{const t=e.touches[0];move(t.clientX,t.clientY);},{passive:true});
stage.addEventListener('touchend',up);
stage.addEventListener('wheel',e=>{if(WALKING)return;e.preventDefault();pend.zoom+=(e.deltaY>0?0.06:-0.06);queue();},{passive:false});

/* ==========================================================================
   THE BODY -- Call of Duty controls, driving numbers nothing here chose.
   WASD, mouse look, shift sprint, space jump, ctrl/C crouch. Every SPEED comes
   from theHuman's derivation and this planet's g; the browser sends INTENT
   (-1..1 on two axes + four flags) and never a position. That is the project's
   own control law: command the process, never the final position.

   EVERY TOP-LEVEL BINDING HERE IS `var`, DELIBERATELY. pick() runs at page
   load, BEFORE this block, and its guard reads WALKING. A `let` in its
   temporal dead zone THROWS even on typeof -- the one case where typeof is not
   a safe probe -- and that single throw killed the initial pick(), halted the
   script right there, and left the stand button with no click handler at all:
   the button that "did nothing" was a button nothing was listening to. `var`
   hoists as undefined, the early guard reads falsy, the page survives its own
   load order.
   ========================================================================== */
var KEY={}, WALKING=false, mdx=0, mdy=0, jumped=false, clockDrag=false, clockTimer=null;
var standbtn=document.getElementById('standbtn'),
    walkhud=document.getElementById('walkhud'),
    hint=document.getElementById('hint'),
    orbitclock=document.getElementById('orbitclock'),
    walkclock=document.getElementById('walkclock'),
    dayslider=document.getElementById('dayslider'),
    hourslider=document.getElementById('hourslider'),
    dayval=document.getElementById('dayval'),
    hourval=document.getElementById('hourval');
var WALK_TERM='theHuman', LOOK=0.0022;
var latslider=document.getElementById('latslider'),
    lonslider=document.getElementById('lonslider'),
    latval=document.getElementById('latval'),
    lonval=document.getElementById('lonval'),
    placeinfo=document.getElementById('placeinfo'), placeTimer=null;

function fmtLat(v){ return Math.abs(v).toFixed(1)+'\u00B0'+(v<0?'S':'N'); }
function fmtLon(v){ return Math.abs(v).toFixed(0)+'\u00B0'+(v<0?'W':'E'); }
function placeLabels(){
  latval.textContent=fmtLat(latslider.value/10);
  lonval.textContent=fmtLon(+lonslider.value);
}
/* WHAT IS THERE, narrated while you drag: the planet's own numbers at that latitude */
function askPlace(){
  if(placeTimer) return;
  placeTimer=setTimeout(async()=>{ placeTimer=null;
    try{
      const r=await fetch('/place?lat='+(latslider.value/10)+'&lon='+lonslider.value).then(x=>x.json());
      let bits=[r.T_C.toFixed(0)+'\u00B0C'];
      if(r.snow) bits.push('snow -- above the ice line ('+r.ice_line_lat_deg.toFixed(1)+'\u00B0)');
      if(r.midnight_sun) bits.push('midnight sun in summer, polar night in winter');
      else if(r.sun_overhead) bits.push('the sun passes straight overhead here');
      placeinfo.textContent=bits.join(' \u00B7 ');
    }catch(e){}
  }, 150);
}
if(latslider){
  [latslider,lonslider].forEach(sl=>sl.addEventListener('input',()=>{ placeLabels(); askPlace(); }));
  placeLabels(); askPlace();
}

function canStand(){ return term===WALK_TERM; }
function showStand(){ if(!standbtn) return;
  var on = canStand()||WALKING;
  standbtn.style.display = on ? '' : 'none';
  /* the date+time pickers belong to play: visible from the moment play is possible, so WHEN is
     chosen before you enter, and still live afterwards */
  if(walkclock) walkclock.style.display = on ? '' : 'none'; }
standbtn.onclick=()=>{ WALKING ? sitDown() : standUp(); };

function lockMouse(){ try{ stage.requestPointerLock(); }catch(e){} }
function enterWalkUI(){
  WALKING=true; standbtn.textContent='\u23F9 stop'; standbtn.classList.add('on');
  walkhud.classList.add('on'); stage.classList.add('walking');
  orbitclock.style.display='none';
  /* the FREE dials regrow the world from its numbers -- but the ground underfoot is carved once
     and cached, so while standing they would change the paperwork and not the planet. Honest UI:
     hide what cannot act. */
  document.getElementById('freebox').style.display='none';
  document.getElementById('lensbox').style.display='none';
  hint.textContent='WASD move · mouse or drag to look · shift run · space jump · ctrl/C crouch · V first/third person · esc frees the mouse';  if(latslider){ latslider.disabled=true; lonslider.disabled=true; }   /* moving house is a re-carve: stop first */
}
function exitWalkUI(){
  WALKING=false; try{ document.exitPointerLock(); }catch(e){}
  standbtn.textContent='\u25B6 play'; standbtn.classList.remove('on');
  walkhud.classList.remove('on'); stage.classList.remove('walking');
  orbitclock.style.display='';
  document.getElementById('freebox').style.display='';
  document.getElementById('lensbox').style.display='';
  hint.textContent='drag to orbit · scroll to zoom · it turns on its own';
  if(latslider){ latslider.disabled=false; lonslider.disabled=false; }
  showStand();
}
async function standUp(){
  standbtn.textContent='carving the ground...'; standbtn.disabled=true;
  /* WHEN was chosen on the sliders before play -- send it with the entry */
  const q='/stand?on=1&day='+(dayslider?dayslider.value:96)+'&minute='+(hourslider?hourslider.value:540)
         +(latslider?('&lat='+(latslider.value/10)+'&lon='+lonslider.value):'');
  const r=await fetch(q).then(x=>x.json()).catch(e=>({error:''+e}));
  standbtn.disabled=false;
  if(!r.walking){ standbtn.textContent='\u25B6 play';
    walkhud.classList.add('on'); walkhud.textContent='could not stand: '+(r.error||'?'); return; }
  enterWalkUI(); lockMouse(); paintWalk(r);
}
async function sitDown(){
  exitWalkUI();
  await fetch('/stand?on=0').catch(()=>{});
}

stage.addEventListener('click',()=>{ if(WALKING && document.pointerLockElement!==stage) lockMouse(); });
window.addEventListener('mousemove',e=>{
  if(WALKING && document.pointerLockElement===stage){ mdx+=e.movementX; mdy+=e.movementY; }
});
window.addEventListener('keydown',e=>{
  if(!WALKING) return;
  if(e.code==='Space'){ jumped=true; e.preventDefault(); }
  if(e.code==='KeyV' && !KEY['KeyV']){ toggleView(); }
  KEY[e.code]=true;
  if(['KeyW','KeyA','KeyS','KeyD','ShiftLeft','ControlLeft','KeyC','KeyV'].includes(e.code)) e.preventDefault();
});
var VIEW='first';
async function toggleView(){
  try{ const r=await fetch('/view?mode='+(VIEW==='third'?'first':'third')).then(x=>x.json());
       VIEW=r.view; }catch(e){}
}
window.addEventListener('keyup',e=>{ KEY[e.code]=false; });

function pad2(n){ return String(n).padStart(2,'0'); }
function paintWalk(r){
  if(!r||!r.walking) return;
  walkhud.innerHTML =
    '<i>'+r.year+'</i> &middot; day <i>'+r.day+'</i> of '+(r.dpy||383)+' &middot; <i>'+pad2(r.hh)+':'+pad2(r.mm)+'</i> &middot; <i>'+r.season+'</i><br>'+
    'sun <i>'+r.sun_alt.toFixed(1)+'&deg;</i> &middot; daylight <i>'+r.daylight.toFixed(1)+'</i> h &middot; '+
      fmtLat(r.lat)+' '+fmtLon(r.lon)+' &middot; <i>'+r.T_C.toFixed(0)+'&deg;C</i>'+(r.snow?' &middot; snow':'')+'<br>'+
    'x <i>'+r.x.toFixed(1)+'</i> &nbsp;y <i>'+r.y.toFixed(1)+'</i> &nbsp;elev <i>'+r.elev.toFixed(1)+'</i> m &nbsp;slope <i>'+r.slope.toFixed(1)+'&deg;</i><br>'+
    'g <i>'+r.g.toFixed(2)+'</i> m/s&sup2; &middot; walk <i>'+r.walk.toFixed(2)+'</i> &middot; run <i>'+r.run.toFixed(2)+'</i> m/s';
  if(typeof r.view==='string') VIEW=r.view;
  if(!clockDrag){
    if(dayslider){ dayslider.max=(r.dpy||383)-1; dayslider.value=r.day; }
    if(hourslider) hourslider.value=r.hh*60+r.mm;
    if(dayval) dayval.textContent=r.day;
    if(hourval) hourval.textContent=pad2(r.hh)+':'+pad2(r.mm);
  }
}

/* THE YEAR IN YOUR HANDS. The 1:1 clock is the honest speed, and at that speed a season is 96
   days -- so the sliders exist to FOLD the year, not to fake it: they jump the same clock the sun
   and the seasons are computed from, throttled so a drag is a sweep, not a flood. */
function clockLabels(){
  dayval.textContent=dayslider.value;
  hourval.textContent=pad2(Math.floor(hourslider.value/60))+':'+pad2(hourslider.value%60);
}
function sendClock(){
  if(clockTimer) return;
  clockTimer=setTimeout(async()=>{ clockTimer=null;
    const q='/clock?day='+dayslider.value+'&minute='+hourslider.value;
    try{ paintWalk(await fetch(q).then(x=>x.json())); }catch(e){}
  }, 90);
}
if(dayslider){
  [dayslider,hourslider].forEach(sl=>{
    sl.addEventListener('pointerdown',()=>{clockDrag=true;});
    sl.addEventListener('pointerup',()=>{clockDrag=false;});
    sl.addEventListener('change',()=>{clockDrag=false;});
    sl.addEventListener('input',()=>{ clockLabels(); if(WALKING) sendClock(); });
  });
}

/* 30 Hz of INTENT. Deltas are consumed, never resent -- a dropped packet must not
   double a turn, and the sensitivity lives here because it is a preference, not a physics. */
showStand();
/* ADOPT THE SERVER'S TRUTH ON LOAD: if a previous page stood up and closed, the stream is already
   first-person -- a fresh page must join that state, not draw orbit UI over a walking world. */
fetch('/walk').then(x=>x.json()).then(r=>{ if(r&&r.walking){ enterWalkUI(); paintWalk(r); } }).catch(()=>{});
setInterval(async()=>{
  if(!WALKING) return;
  const fwd=(KEY['KeyW']?1:0)-(KEY['KeyS']?1:0),
        str=(KEY['KeyD']?1:0)-(KEY['KeyA']?1:0),
        mx=mdx*LOOK, my=mdy*LOOK;
  mdx=0; mdy=0;
  const j=jumped; jumped=false;
  const q='/walk?fwd='+fwd+'&strafe='+str+'&sprint='+(KEY['ShiftLeft']?1:0)+
          '&jump='+(j?1:0)+'&crouch='+((KEY['ControlLeft']||KEY['KeyC'])?1:0)+'&mx='+mx+'&my='+my;
  try{ paintWalk(await fetch(q).then(x=>x.json())); }catch(e){}
},33);

</script>
"""
