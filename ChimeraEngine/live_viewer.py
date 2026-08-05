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
import os as _os
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
        # MUJOCO STAND SIM MODE. `_sim` is a walker.StandSimulator once /sim is asked for; it
        # runs the real MuJoCo body under the trained stand policy instead of the story Walker.
        self._sim = None
        self._sim_theta = None
        self._view = "first"              # 'first' = through the eyes; 'third' = watching the body
        self._last_input = 0.0     # wall-time of the last drag/zoom -> drives the moving-vs-settled LOD
        self._clients = 0                                          # active /stream connections
        # ── PAUSE / STEP / SCRUB (Task 9) ──
        self._paused = False       # True = time is FROZEN (the render thread keeps producing the same frame)
        self._step_requested = False  # True -> advance ONE tick then re-freeze
        self._ticks = 0            # granted render ticks -- the observable /step is measured against
        # LOD state, declared here rather than conjured by getattr in the loop: a reader should be
        # able to see every field the render thread owns without running it.
        self._lod_base = None      # the full-detail buffer the pyramid was built from
        self._lod_levels = None    # coarse -> fine mip levels, rebuilt only on load
        self._lod_n = None         # grain count currently on the GPU (None = nothing uploaded)
        self._lod_level = None     # which mip rung is active (len-1 == the base, full detail)
        self._lod_levels_n = None  # how many rungs this body's pyramid has
        self._grains = 0           # grains in the last rendered frame (read off the pipeline)
        self._expansions = 0       # (splat, tile) pairs the binner emitted for that frame
        self._eps = 0.0            # ... per visible splat: the shape-free form of "grains too big"
        self._ms_hist = []         # last 30 RENDER times, ms -- the rolling fps
        self._pub_hist = []        # ... and the JPEG encode beside it, so the two never merge again
        self._scrub_t = None           # set to a specific t for scrubbing a membrane's own timeline
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
            import lod as LOD
            import numpy as np
            import perf_guard as _pg
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

                # ── TIME IS DRIVABLE ─────────────────────────────────────────────────────────────
                # /pause, /step and /scrub have existed in handle() for a while and set flags the
                # render thread never read, so pausing did nothing. Frozen means: publish the same
                # frame and do no work -- the MJPEG stream holds on its last frame because nothing
                # new is produced.
                #
                # THE STEP IS CONSUMED HERE, NOT AT THE END OF THE ITERATION, and that is the whole
                # correctness argument. This loop has THREE exits -- the walk branch ends with its
                # own `continue`, so does the `self._loaded is None` guard, and the orbit path falls
                # through to the 60 fps cap. A re-freeze written at "the end" sits on ONE of them,
                # so a step taken in walk mode would advance forever and the falsifier (`/step
                # advances more than one frame`) would fire on the mode nobody tested.
                #
                # Consuming the request and re-arming the pause in the SAME locked block makes the
                # invariant hold on every path: whatever this iteration does afterwards, exactly one
                # tick has been granted.
                #
                # AND THE SLEEP IS OUTSIDE THE LOCK. Sleeping while holding it would block /pause,
                # /step and /scrub for 50 ms per iteration -- the controls would fight the loop they
                # are trying to drive.
                # `_ticks` EXISTS SO THE FALSIFIER CAN BE MEASURED. The claim is "/step advances
                # EXACTLY one frame"; nothing in this loop counted frames, so the claim could only
                # be eyeballed against an MJPEG stream -- and an unmeasurable claim is a
                # description, which survives any result. One monotonic counter, incremented once
                # per GRANTED tick, turns it into an arithmetic check: ticks after == ticks before
                # + 1, or the port fired.
                with self._lock:
                    frozen = self._paused and not self._step_requested
                    if not frozen:
                        if self._step_requested:
                            self._step_requested = False
                            self._paused = True      # one tick is granted; we are paused again
                        self._ticks += 1
                if frozen:
                    time.sleep(0.05); continue
                if self._sim is not None:
                    # ── THE MUJOCO STAND SIM -- the real body, standing under its policy. ──────
                    # The StandSimulator owns the physics; the viewer's only job is to step it at
                    # a fixed cadence and render the body + a flat ground as splats.
                    import walker as _wk
                    st = self._sim.step(1)
                    ground = np.ascontiguousarray(
                        _wk.scene_around(self._ground_walker) if getattr(self, "_ground_walker", None)
                        else self._sim_floor(), dtype=np.float32)
                    body = self._sim.body_splats()
                    pipe.upload(np.ascontiguousarray(
                        np.concatenate([ground, body], axis=0), dtype=np.float32))
                    # a fixed third-person camera: 3 m out, chest-high, aimed at the pelvis
                    cam.position = np.array([1.5, -2.6, 0.85], dtype=np.float32)
                    cam.yaw = math.atan2(2.6, 1.5)   # look toward -Y/0.0
                    cam.pitch = -0.05
                    self._sim_state = st
                    self._publish(pipe.render_from_gpu(cam, params_hi))
                    time.sleep(max(0.0, 1 / 60 - (time.time() - now)))
                    continue
                if self._walk is not None:
                    # ── STANDING IN IT -- through THE STATE MACHINE (controller.py). The keys map
                    # onto named states (walk, sidestep, steer, jump), and the states drive the
                    # walker's process law. The mouse stays the look; the keyboard stays the feet.
                    import controller as _ctl
                    if getattr(self, "_controller", None) is None:
                        self._controller = _ctl.Controller()
                    with self._lock:
                        wi = dict(self._walk_in)
                        self._walk_in["mx"] = self._walk_in["my"] = 0.0
                        self._walk_in["jump"] = False
                    self._walk.look(wi["mx"], wi["my"])
                    _ctl.drive_walker_vector(self._walk, self._controller,
                                             wi["fwd"], wi["strafe"], wi["sprint"],
                                             wi["crouch"], wi["jump"], dt)
                    # THE WORLD ANSWERS (Phase E, rung 2 -- TOUCH). The three passive classes take
                    # the player's commanded velocity at contact; their own equations decide the
                    # rest. If any of them visibly changed, the frame must show it.
                    touch_moved = False
                    if getattr(self, "_touch", None):
                        import touchables as _to
                        for ob in self._touch:
                            touch_moved = ob.step(self._walk, dt) or touch_moved
                    # the ground is rebuilt around the player only when they have moved far enough
                    # to matter -- the near shell is 180 m across, so a stride does not need one.
                    # Rebuilt when the player has moved far enough to matter, OR when the sun has --
                    # the clock runs 1:1 here, so at 15 deg/hour a half-degree is about two minutes.
                    # Standing still must not freeze the light; it is a real sky on a real rotation.
                    import walker as _wk
                    sun_moved = abs(self._walk.clock - getattr(self, "_walk_clock", -1e18)) > 120.0
                    rebuilt = False
                    if self._walk_dirty or self._walk_moved() > 12.0 or sun_moved:
                        self._ground_np = np.ascontiguousarray(_wk.scene_around(self._walk),
                                                               dtype=np.float32)
                        if self._view != "third":
                            buf = self._ground_np
                            if getattr(self, "_touch", None):
                                buf = np.concatenate(
                                    [buf, _to.touchables_buffer(self._touch, self._walk)], axis=0)
                            pipe.upload(np.ascontiguousarray(buf, dtype=np.float32))
                        self._walk_anchor = (self._walk.x, self._walk.y)
                        self._walk_clock = self._walk.clock
                        self._walk_dirty = False
                        rebuilt = True
                    # A TOUCHABLE MOVES ONLY WHEN THE PLAYER IS NEXT TO IT -- metres, always far
                    # inside the 12 m ground-rebuild threshold, so the cached ground is the right
                    # ground; only the objects' own splats join it anew.
                    if touch_moved and not rebuilt and self._view != "third":
                        pipe.upload(np.ascontiguousarray(np.concatenate(
                            [self._ground_np, _to.touchables_buffer(self._touch, self._walk)],
                            axis=0), dtype=np.float32))
                    wx, wy = self._walk.x, self._walk.y
                    if self._view == "third":
                        # THE BODY CHANGES EVERY FRAME (the gait phase is the distance walked), so
                        # third person re-uploads ground+body each tick. The ground array is cached;
                        # the body is ~2,900 grains from a 48-pose cache -- the upload is the cost,
                        # and it is the same ~7 MB the rebuild path already pays.
                        body = _wk.body_buffer(self._walk)
                        layers = [self._ground_np, body]
                        if getattr(self, "_touch", None):
                            layers.append(_to.touchables_buffer(self._touch, self._walk))
                        pipe.upload(np.ascontiguousarray(
                            np.concatenate(layers, axis=0), dtype=np.float32))
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
                    self._density_check(self._pending, buf)
                    if buf is not None:
                        # ── THE MIP PYRAMID IS BUILT ONCE PER LOAD, NOT ONCE PER FRAME ───────────
                        # `LOD.build_mips` clusters on the sphere; running it every frame would
                        # cost more than the grains it saves. It belongs HERE, in the reload
                        # branch, which fires on a term change, a `t` change or a forced reload --
                        # never on a mere camera move.
                        #
                        # AND THAT IS WHY SELECTION CANNOT ALSO LIVE HERE. Selecting the level at
                        # load time would freeze LOD at whatever radius the camera happened to have
                        # when the term was loaded, so zooming in would never restore detail and the
                        # membrane's own prediction -- "at 0.5x zoom it switches to the full base
                        # count" -- could not come true. Build here, SELECT below, every frame,
                        # against the radius the camera actually has.
                        self._lod_base = buf
                        try:
                            self._lod_levels = LOD.build_mips(buf, LOD.body_radius(buf)) \
                                if LOD.should_lod(buf) else None
                        except Exception:
                            self._lod_levels = None      # LOD is an optimisation, never a blocker
                        self._lod_n = None               # force the first selection to upload
                        # THE TERM IS `_pending`, NOT `_loaded`. `_pending != _loaded` is the
                        # condition that triggered this reload, so `_loaded` still names the
                        # membrane being REPLACED -- tagging the buffer with it would report a
                        # budget overage against the wrong membrane, and the report would look
                        # entirely plausible. The walk-mode uploads below stay untagged on purpose:
                        # they are composites (ground + body + touchables) belonging to no single
                        # membrane, and a per-surface budget has nothing to say about a composite.
                        pipe.upload(np.ascontiguousarray(buf, dtype=np.float32),
                                    term=self._pending or "")
                        self._lod_n = buf.shape[0]
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

                # ── THE LOD SWITCH, KEYED TO THE RADIUS THE CAMERA ACTUALLY HAS ─────────────────
                # `lod_switch()` existed and nothing called it, so every body rendered at its base
                # count at every distance. Selection is cheap -- a walk over the precomputed levels
                # -- so it runs every frame; the UPLOAD only happens when the chosen level CHANGES.
                # That is what makes this a switch rather than a re-upload loop: crossing a mip
                # boundary costs one upload, and staying inside one costs nothing.
                # THE DISTANCE MUST BE IN THE BUFFER'S OWN UNITS, and feeding it `self._radius`
                # would have been a silent catastrophe. `membrane_buffer`'s docstring says it
                # plainly -- "the buffer is in the membrane's own local units (radius ~1)" -- while
                # `scene_cam_distance` returns `extent_m * 2.8`, WORLD METRES. Measured: aBlueWorld
                # has body_radius 1.03 against a camera distance of 1.47e7, seven orders apart. Fed
                # to projected_radius_px that gives r_px = 0.0000655, so `select` returns the
                # COARSEST mip and EVERY body in the game collapses to ONE SPLAT -- with no
                # exception raised, because dividing by a large number is perfectly legal.
                #
                #     A FOLD/BOND MISFOLD: the right two quantities at an interface where their
                #     units do not agree. It would have looked like LOD working.
                #
                # The zoom is a RATIO (`_radius / _radius0`) and a ratio is unit-free, so the
                # local-space distance is the viewer's own default framing -- 2.8 body radii --
                # scaled by it. Nothing here converts between the two spaces, because the
                # conversion is exactly the thing that is broken; it stays inside one of them.
                lv = self._lod_levels
                if lv:
                    R_local = LOD.body_radius(self._lod_base)
                    zoom = r / max(self._radius0, 1e-30)
                    d_local = 2.8 * R_local * zoom
                    r_px = LOD.projected_radius_px(R_local, d_local, _H, cam.fov)
                    sel = LOD.select(lv, r_px)
                    # THE LEVEL INDEX, NOT JUST THE COUNT. A count alone cannot say whether LOD is
                    # doing anything: "43000" reads identically whether the base was selected or
                    # the switch was never called. The index says WHICH rung, and `len(lv)-1` is
                    # always the base, so `lod_level == base_level` is the readable form of "full
                    # detail" without having to compare two grain counts.
                    self._lod_level = next((i for i, l in enumerate(lv)
                                            if l.shape[0] == sel.shape[0]), len(lv) - 1)
                    self._lod_levels_n = len(lv)
                    if sel.shape[0] != self._lod_n:
                        pipe.upload(np.ascontiguousarray(sel, dtype=np.float32),
                                    term=self._loaded or "")
                        self._lod_n = sel.shape[0]

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
                t_r0 = time.time()
                img = pipe.render_from_gpu(cam, params)
                t_render_ms = (time.time() - t_r0) * 1000.0
                # ── THE PUBLISH IS TIMED SEPARATELY, AND IT WAS NOT ────────────────────────────
                # The comment below has always said "RENDER TIME IS TIMED AROUND THE RENDER", and
                # it was not true: `_publish` sat inside the timed region, so every fps number
                # this viewer has ever reported included a 1920x1080 JPEG encode. MEASURED, that
                # is most of the frame -- theZero renders in ~38 ms offline and the viewer
                # reported 141.9 ms for the same scene, against 23.9 ms predicted by the cost
                # model. Six times off, and the excess was the encoder.
                #
                # THE ENCODE IS REAL WORK AND IT IS NOT A RENDER. It sets how fast the MJPEG
                # stream can go and belongs on screen, but attributing it to the render made the
                # GPU look slow and made the expansion model look wrong -- a measurement blaming
                # the wrong stage cannot be argued with, only re-measured.
                t_p0 = time.time()
                self._publish(img)
                t_publish_ms = (time.time() - t_p0) * 1000.0
                # ── THE FRAME BUDGET, MEASURED WHERE IT IS SPENT ────────────────────────────────
                # The grain count is read off `pipe._n` rather than bookkept at each upload site.
                # There are four of those and one of them is the LOD switch, which uploads a
                # DIFFERENT count from the one the reload branch put there -- a hand-maintained
                # counter would have gone stale exactly when LOD started working, and a HUD that
                # reports a stale count is worse than no HUD.
                #
                # RENDER TIME IS TIMED AROUND THE RENDER, not the whole iteration: the loop also
                # sleeps to cap 60 fps, and including that would report the CAP as the cost and
                # hide the moment the render itself stopped fitting inside it.
                #
                # THE FRAME BUDGET IS CHECKED HERE AND NOWHERE EARLIER, because the quantity it
                # budgets does not exist until the frame has been binned. `check_frame_budget`
                # used to take a grain count and could therefore run at upload; it now takes tile
                # EXPANSIONS, which are produced by the render itself. Asking before the render
                # would mean asking a question the pipeline cannot yet answer, which is what the
                # grain-count budget was doing for as long as it existed.
                #
                # IT PRINTS, IT DOES NOT RAISE. The render thread owns the GPU for the whole
                # session; an exception here kills the viewer over a scene that is merely slow,
                # and a dead viewer reports nothing at all.
                _exp = int(pipe.expansion_count())
                try:
                    _pg.check_frame_budget(_exp)
                except Exception as _e:
                    if isinstance(_e, getattr(_pg, "PerfBudgetError", Exception)):
                        print(f"[PERF] {self._loaded or '<none>'}: {_e}", flush=True)
                self._note_frame(int(getattr(pipe, "_n", 0)), t_render_ms,
                                 _exp, float(pipe.expansions_per_splat()), t_publish_ms)
                time.sleep(max(0.0, 1 / 60 - (time.time() - now)))    # cap 60fps so the fast (moving) LOD stays smooth
        except Exception as e:                                          # a dead render thread must be visible, not silent
            import traceback
            self._err = f"{e}\n{traceback.format_exc()}"
            print(f"[live_viewer] render thread died: {self._err}")

    def _density_check(self, term: str, buf) -> None:
        """Warn to the TERMINAL when a loaded membrane is below its derived density floor.

        The floor is enforced on the UE transport path (`ParticleEngine/bridge`), and the viewer
        has its own upload path that never crossed it -- so the one surface a person actually
        LOOKS at was the one surface nobody checked. Purely informational: it never blocks a
        render, because a thin membrane is still the truth about that membrane.

        AN EMPTY BUFFER ALWAYS WARNS, whatever its class. `density_enforce` answers "is this above
        the floor for its surface type", and for a term that classifies as `general` there IS no
        floor -- so a buffer of ZERO grains would return True and say nothing. Nothing rendering
        at all is the loudest fact available about a membrane and it must not depend on whether
        the name happened to contain the word "sand".
        """
        n = 0 if buf is None else int(getattr(buf, "shape", [0])[0])
        if n == 0:
            print(f"[DENSITY] {term}: buffer is EMPTY ({'None' if buf is None else '0 grains'}) "
                  f"-- nothing will render", flush=True)
            return
        try:
            from ParticleEngine.bridge import density_enforce
        except Exception:
            return
        density_enforce(term, n)          # prints to stderr with the floor and the surface type

    def _note_frame(self, grains: int, ms: float, expansions: int = 0, eps: float = 0.0,
                    publish_ms: float = 0.0):
        """Record one rendered frame: its grain count, its tile work, and how long it took.

        THE FPS IS A ROLLING MEAN OVER THE LAST 30 RENDERS, not an instantaneous 1/dt. A single
        frame's time is dominated by whatever else the shared 4090 was doing that millisecond --
        this box runs LM Studio on the same card -- so an instantaneous figure flickers between
        4 and 12 fps on a scene that is not changing. Thirty frames is ~4 seconds at the rates
        this renders at: long enough to be stable, short enough to move when the scene does.
        """
        with self._lock:
            self._grains = grains
            # THE EXPANSION COUNT IS INSTANTANEOUS WHERE THE TIME IS ROLLED, and the asymmetry is
            # deliberate. The frame time is noisy because this box shares its 4090 with LM Studio,
            # so it needs 30 frames to mean anything. The expansion count is DETERMINISTIC for a
            # given (buffer, camera): the same view produces the same number every frame, and a
            # rolling mean over it would only blur the moment a camera move changed it.
            self._expansions = int(expansions)
            self._eps = float(eps)
            self._ms_hist.append(float(ms))
            self._pub_hist.append(float(publish_ms))
            if len(self._ms_hist) > 30:
                del self._ms_hist[:-30]
            if len(self._pub_hist) > 30:
                del self._pub_hist[:-30]

    def stats(self) -> dict:
        """The frame budget as a number, for the footer and for /stats.

        `budget_pct` is against MAX_GRAINS_PER_FRAME, which perf_guard derives; it is imported
        rather than copied so the HUD cannot disagree with the guard that raises.
        """
        try:
            from perf_guard import (MAX_GRAINS_PER_FRAME as _CAP, MAX_RENDER_MS as _MS,
                                    MAX_EXPANSIONS_PER_FRAME as _ECAP, predicted_ms as _pred)
        except Exception:
            _CAP, _MS, _ECAP = 250_000, 200, 6_154_729
            _pred = lambda e: 0.0
        try:
            from ParticleEngine.gpu_pipeline import TILE_SIZE as _TS, MAX_PER_TILE as _MPT
        except Exception:
            _TS, _MPT = 32, 16384
        with self._lock:
            hist = list(self._ms_hist)
            pub = list(self._pub_hist)
            g = int(self._grains)
            exp = int(self._expansions)
            eps = float(self._eps)
        ms = sum(hist) / len(hist) if hist else 0.0
        pub_ms = sum(pub) / len(pub) if pub else 0.0
        # HOW CLOSE THE WHOLE SCREEN IS TO ITS PER-TILE CEILING. `MAX_PER_TILE` evicts the far
        # splats in any tile that overflows, and an eviction is something NOT DRAWN -- so this is
        # the one number here that predicts a visual defect (hard-edged black rectangles on the
        # tile grid) rather than a slow frame.
        #
        # IT IS AN AVERAGE AND CANNOT SEE ONE HOT TILE. A scene at 3% here can still have a single
        # tile at 100%, which is why `CHIMERA_TILE_DIAG=1` reports the hottest five individually.
        # Reported anyway because the average moving is a cheap early signal, and the expensive
        # per-tile maximum costs a second GPU sync per frame on the live render thread.
        screen_tiles = max(1, ((_W + _TS - 1) // _TS) * ((_H + _TS - 1) // _TS))
        # `fps` IS THE FRAME RATE A VIEWER SEES, so it is 1000/(render + publish) -- both have to
        # happen before the next picture appears. `render_ms` is the render ALONE, which is what
        # `predicted_ms` models and the only one of the two the expansion budget governs.
        frame_ms = ms + pub_ms
        return {"fps": round(1000.0 / frame_ms, 2) if frame_ms > 1e-9 else 0.0,
                "render_ms": round(ms, 2),
                "publish_ms": round(pub_ms, 2),
                "frame_ms": round(frame_ms, 2),
                "grains": g,
                "grain_cap": int(_CAP),
                "budget_pct": round(100.0 * g / max(_CAP, 1), 1),
                "over_budget": bool(g > _CAP),
                "render_ms_cap": int(_MS),
                "over_time": bool(ms > _MS),
                # ── WHAT THE FRAME ACTUALLY COST (2026-08-04) ────────────────────────────────
                # `grains`/`budget_pct` above are the SUPERSEDED model, kept because the HUD and
                # existing callers read them. These four are the measured one.
                "expansions": exp,
                "expansions_per_splat": round(eps, 2),
                "expansion_cap": int(_ECAP),
                "expansion_pct": round(100.0 * exp / max(_ECAP, 1), 2),
                "over_expansions": bool(exp > _ECAP),
                "tile_expansion_ratio": round(exp / float(screen_tiles * _MPT), 6),
                "screen_tiles": screen_tiles,
                # The model's own guess, next to the measured time. A prediction on screen beside
                # the thing it predicts is a prediction somebody will notice going wrong.
                "predicted_ms": round(float(_pred(exp)), 2),
                "term": self._loaded or "",
                # LOD, so a caller can see WHICH rung is active rather than infer it from a count.
                "lod_level": self._lod_level,
                "lod_levels": self._lod_levels_n,
                "lod_count": self._lod_n,
                "base_count": (None if self._lod_base is None else int(self._lod_base.shape[0]))}

    def _publish(self, img):
        from PIL import Image
        buf = io.BytesIO(); Image.fromarray(img).save(buf, "JPEG", quality=85)
        with self._lock:
            self._latest = buf.getvalue()

    def _walk_moved(self) -> float:
        ax, ay = getattr(self, "_walk_anchor", (1e18, 1e18))
        return math.hypot(self._walk.x - ax, self._walk.y - ay)

    def _sim_floor(self):
        """A flat, featureless floor for the MuJoCo sim to stand on -- the myobody model has no
        terrain, and rendering it against the story's carved ground would show a body standing in
        the air. 61x61 grains at 0.15 m spacing covers a 9 m x 9 m pad under the body."""
        import numpy as _np
        import walker as _wk
        v = _np.arange(-4.5, 4.51, 0.15)
        XX, YY = _np.meshgrid(v, v)
        X, Y = XX.ravel(), YY.ravel()
        n = len(X)
        import sys as _sys
        _sys.path.insert(0, str(_wk._STORY))
        from matter import blank, lit, SOLID
        b = blank(n)
        b[:, 0], b[:, 1], b[:, 2] = X, Y, _np.full(n, 0.0)
        b[:, 21], b[:, 22], b[:, 23] = 0.0, 0.0, 1.0     # up normal
        alb = _np.array([0.34, 0.31, 0.27], _np.float32)
        sun = _np.array([0.3, 0.0, 0.95], _np.float32)
        lam = _np.clip(b[:, 21:24] @ sun, 0.0, None)
        b[:, 16:19] = lit(alb, 1.0 * lam + 0.15, e_ref=1.0, tone=0.45)
        b[:, 19] = 1.0
        b[:, 20] = 0.22          # grains close enough to read as a floor
        b[:, 11] = SOLID
        return np.ascontiguousarray(b, dtype=_np.float32)

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
                self._touch = None
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
            import touchables as _to
            with self._lock:
                self._walk = w
                # THE WORLD ANSWERS (Phase E, rung 2): the three passive classes spawn with the
                # body, placed near spawn as design placeholders -- the operator's to move.
                self._touch = _to.spawn()
                self._walk_dirty = True
        if day is not None and minute is not None:
            # the date and hour chosen BEFORE play -- same formula as /clock, applied at entry
            with self._lock:
                w = self._walk
                w.clock = float(day) * w.day_s + (float(minute) / 1440.0) * w.day_s
                self._walk_dirty = True
        return {"walking": True, **self._walk.readout()}

    def walk_input(self, fwd=0.0, strafe=0.0, sprint=False, jump=False, crouch=False, mx=0.0, my=0.0,
                   use=False):
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
            touch = ""
            if getattr(self, "_touch", None):
                import touchables as _to
                if use:                                  # E: GRAB -- the object in reach answers
                    for ob in self._touch:
                        ob.interact(w)
                    self._walk_dirty = True              # the pickup/drop must be visible at once
                touch = _to.hud_line(self._touch, w)
        return {"walking": True, "view": self._view, "touch": touch, **w.readout()}

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
    if path == "/sim":
        # MUJOCO STAND SIM. `on=1` enters sim mode (the real MuJoCo body under the trained stand
        # policy); `on=0` leaves it. `theta` optionally points at a different theta .npy.
        import json as _json
        on = (qs.get("on") or ["1"])[0] not in ("0", "", "false")
        try:
            if not on:
                v = get_viewer()
                with v._lock:
                    v._sim = None
                _send(handler, 200, "application/json", _json.dumps({"sim": False}).encode())
                return True
            import walker as _wk
            theta = qs.get("theta") or [None]
            theta_path = theta[0] if theta[0] else None
            sim = _wk.StandSimulator(theta_path=theta_path)
            v = get_viewer()
            with v._lock:
                v._sim = sim
                v._sim_theta = theta_path
            _send(handler, 200, "application/json",
                  _json.dumps({"sim": True, "nu": sim.nu, "g": round(sim.g, 3),
                               "pd": sim.is_pd, "theta": theta_path}).encode())
        except Exception as e:
            import traceback; traceback.print_exc()
            _send(handler, 200, "application/json",
                  _json.dumps({"sim": False, "error": str(e)}).encode())
        return True
    if path == "/walk":
        import json as _json
        r = get_viewer().walk_input(
            fwd=_f(qs, "fwd"), strafe=_f(qs, "strafe"),
            sprint=(qs.get("sprint") or ["0"])[0] == "1",
            jump=(qs.get("jump") or ["0"])[0] == "1",
            crouch=(qs.get("crouch") or ["0"])[0] == "1",
            use=(qs.get("use") or ["0"])[0] == "1",
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
            # THE DENSITY GUARD IS SKIPPED ON THIS PATH, deliberately. `grow.py` now runs it at the
            # end of a full grow, and it re-emits all 42 terms in a fresh process: 27 seconds. This
            # endpoint is a SLIDER -- the operator moves a free number and expects the world to
            # move with it -- so paying 27 s per nudge would make the one interactive control in
            # the world unusable. The guard belongs on a deliberate grow, not on every twitch.
            _env = dict(_os.environ, CHIMERA_SKIP_DENSITY_GUARD="1")
            subprocess.run([_sys.executable, str(_HERE.parent / "story" / "grow.py")],
                           capture_output=True, cwd=str(_HERE.parent), env=_env)
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
    # ── PAUSE / STEP / SCRUB (Task 9) ────────────────────────────────────────────────────────
    if path == "/pause":
        v = get_viewer()
        with v._lock:
            v._paused = (qs.get("on") or ["1"])[0] not in ("0", "", "false")
        _send(handler, 200, "application/json",
              json.dumps({"paused": v._paused, "t": v._t, "ticks": v._ticks}).encode()); return True
    if path == "/invalidate" or path == "/reload":
        # THE CACHES ARE KEYED ON THE TERM ALONE and nothing in the key mentions the numbers the
        # buffer was emitted from, so after `story/grow.py` the viewer keeps serving the buffer
        # built from the PREVIOUS numbers. The operator moves a slider, the world does not move,
        # and the slider looks broken. A stale render is a wrong answer that looks finished.
        import splat_appearance as _sa
        t = (qs.get("term") or [""])[0] if path == "/invalidate" else ""
        dropped = _sa.invalidate(t or None)
        v = get_viewer()
        with v._lock:
            v._reload = True                 # the render thread re-emits on its next tick
            if not t:
                v._loaded = None             # a full clear must not trust the loaded marker either
        _send(handler, 200, "application/json", json.dumps(dropped).encode()); return True
    if path == "/stats":
        _send(handler, 200, "application/json",
              json.dumps(get_viewer().stats()).encode()); return True
    if path == "/step":
        v = get_viewer()
        with v._lock:
            v._step_requested = True
            v._paused = True
            n0 = v._ticks
        # THE TICK COUNT IS RETURNED so a caller can check the claim instead of trusting it:
        # poll /pause afterwards and `ticks` must be exactly n0 + 1. A 204 with no body left
        # "/step advances exactly one frame" as something only an eye could judge.
        _send(handler, 200, "application/json",
              json.dumps({"stepped_from": n0}).encode()); return True
    if path == "/scrub":
        # SCRUB the membrane's own timeline: t from 0 to 1, driving the 4th dimension.
        # `/scrub?term=theCooling&t=0.5` loads theCooling at halfway through its movie.
        v = get_viewer()
        term = (qs.get("term") or [""])[0]
        t = _f(qs, "t")
        if term and term in v._sa.scene_terms():
            v.set_scene(term)
        v.set_time(t)
        _send(handler, 204, "text/plain", b""); return True
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
 aside p.sub{margin:0 16px 10px;color:var(--dim);font-size:12px}
 /* THE FILTER BAR, STICKY. The aside scrolls, and the deepest membrane (theBreath, depth 16) sits
    well below the fold on a 1080p window -- a search box you have to scroll back up to reach is a
    search box nobody uses. z-index because rows scroll UNDER it, not through it. */
 .find{position:sticky;top:0;z-index:2;background:var(--panel);padding:2px 12px 8px;
       border-bottom:1px solid var(--line);margin-bottom:6px}
 .find input[type=text]{width:100%;background:#070a12;color:var(--ink);border:1px solid var(--line);
       border-radius:6px;padding:5px 8px;font:12px system-ui;outline:none}
 .find input[type=text]:focus{border-color:#41527d}
 .find label{display:flex;align-items:center;gap:5px;margin-top:6px;color:var(--dim);
             font-size:11px;cursor:pointer}
 .find input[type=checkbox]{accent-color:#5f8ee0;margin:0}
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
 /* THE DISCLOSURE TRIANGLE, with its own hit box. A FIXED 12px width even when empty, so a leaf's
    name lines up with its siblings' -- otherwise the indent stops meaning depth. */
 .tw{flex:none;width:12px;color:#6b7899;font-size:9px;cursor:pointer;user-select:none;text-align:center}
 .tw:hover{color:#fff}
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
 /* THE BREADCRUMB. #hud above is pointer-events:none so a drag across the caption still orbits the
    world; the serial is the one strip that must RECEIVE clicks, so it takes them back for itself. */
 #serial{margin-top:6px;color:var(--dim);font:11px ui-monospace,Menlo,monospace;pointer-events:auto}
 #serial a{color:#8ea3c8;text-decoration:none;border-bottom:1px dotted #39415c}
 #serial a:hover{color:#fff;border-bottom-color:#8ea3c8}
 #serial a.here{color:var(--ink);border-bottom-color:transparent}
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
  <p class=sub>the story, as a hierarchy &mdash; click a name to go there,
     <span style="color:#8ea3c8">&#9654;</span> to open what it contains<br>
     <span style="color:#7fd18a">&#9679; the</span> = the law &nbsp;
     <span style="color:#e8705c">&#9679; a</span> = an instance &nbsp;
     <span style="color:#5c6683">&#9675;</span> = not built</p>
  <div class=find>
    <input id=q type=text placeholder="find a membrane" autocomplete=off spellcheck=false>
    <label><input type=checkbox id=builtonly> built only &mdash; hide what has no physics</label>
  </div>
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
  <footer><div id=nums></div><div class=num id=budget></div><div class=hint id=hint>drag to orbit &middot; scroll to zoom &middot; it turns on its own</div></footer>
</main>
<script>
const TREE=__TREE__, READINGS=__READINGS__, KINDS=__KINDS__, TERMS=__TERMS__;
let term=null, INDEX={}, PATH={};
function index(n,trail){INDEX[n.name]=n;PATH[n.name]=trail.concat(n.name);
  (n.children||[]).forEach(c=>index(c,PATH[n.name]));}
TREE.forEach(n=>index(n,[]));
/* ── THE TREE, AS A TREE YOU CAN CLOSE ────────────────────────────────────────────────────────
   MEASURED PROBLEM (2026-07-29, and the count grows with every chapter): story/ is 23 membranes,
   almost all of them ONE chain -- theZero -> ... -> theSweep sits at depth 17. Drawn fully open at
   the old 15 px/level its paddingLeft was 265 px and its NAME started at 285 px of a 300 px panel:
   past the scrollbar, invisible. The hierarchy was unreadable exactly where it matters most -- at
   the bottom, where a human stands. Three pieces of STATE fix it: a disclosure triangle per parent,
   a filter, and "the path to whatever is picked is always open". No new machinery -- still one
   row() and one pick().

   EVERY BINDING HERE IS `var` AND DECLARED ABOVE THE FIRST pick() CALL, deliberately. pick() runs
   at page load and now reaches OPEN/QUERY/VIS through paintTree(); a `let` still in its temporal
   dead zone throws a ReferenceError that kills the rest of the script SILENTLY -- the failure
   documented at the time slider below and again at the walk block, which twice cost the whole walk
   UI. `var` hoists as undefined, so the worst case here is a falsy read, never a dead page. */
var treeEl=document.getElementById('tree');
var OPEN={}, QUERY='', BUILT_ONLY=false, OPEN_SAVED=null, VIS={};

/* OPEN THE PATH, LEAVE THE REST SHUT. A term's ancestors are exactly the membranes whose numbers it
   inherited, so the open branch IS its serial -- nothing else has to be open for it to read. */
function openTo(t){ (PATH[t]||[]).forEach(function(a){ OPEN[a]=true; }); }

/* WHAT SURVIVES THE FILTER, bottom-up in one pass, cached by name (INDEX is already keyed by name,
   so uniqueness is an assumption this code inherits rather than adds). AN ANCESTOR OF A MATCH STAYS
   VISIBLE: a hit shown without its parents is the flat list again, and the parents are the reason
   the child's numbers are what they are. Same rule serves "built only" -- a folder with no
   physics.py that CONTAINS one is kept, because deleting it would orphan a proven membrane. */
function markVis(n){
  var self=(!QUERY||n.name.toLowerCase().indexOf(QUERY)>=0)&&(!BUILT_ONLY||n.membrane);
  var kid=false;
  (n.children||[]).forEach(function(c){ if(markVis(c)) kid=true; });
  VIS[n.name]=self||kid;
  return VIS[n.name];
}
function markAll(){ VIS={}; TREE.forEach(markVis); }
function openVis(n){ if(!VIS[n.name]) return; OPEN[n.name]=true; (n.children||[]).forEach(openVis); }

function row(n,depth){
  if(!VIS[n.name]) return;
  const kids=(n.children||[]).filter(function(c){ return VIS[c.name]; });
  const open=!!OPEN[n.name];
  const d=document.createElement('div');
  d.className='node'+(n.membrane?(n.name[0]==='a'&&n.name[1]===n.name[1].toUpperCase()?' inst':''):' paint')
             +(n.name===term?' on':'');
  /* 10 px A LEVEL, not 15. The triangle, dot and their two gaps spend a fixed 32 px before the name,
     so at depth 17 the old 15 px started the name at 285 px of a 300 px panel; 10 px puts it at
     208 px and leaves ~80 px, which is what "theSweep" needs at 13 px. */
  d.style.paddingLeft=(6+depth*10)+'px';
  d.innerHTML='<span class=tw>'+(kids.length?(open?'&#9660;':'&#9654;'):'')+'</span>'
             +'<span class=dot></span><span class=nm>'+n.name+'</span>';
  d.onclick=()=>pick(n.name);
  d.dataset.name=n.name;
  if(kids.length){
    /* THE TRIANGLE IS NOT THE NAME, and stopPropagation is the whole of that distinction: opening a
       branch must not switch the scene (pick() fires /scene, which reloads the GPU pipeline for a
       different membrane), and clicking the name must still do exactly what it did before this
       existed. Only this node's flag is touched -- one subtree, never a global expand. */
    d.firstChild.onclick=function(e){ e.stopPropagation(); OPEN[n.name]=!open; paintTree(); };
  }
  treeEl.appendChild(d);
  if(open) kids.forEach(function(c){ row(c,depth+1); });
}

function paintTree(){
  if(!treeEl) return;
  markAll();
  treeEl.innerHTML='';
  TREE.forEach(function(n){ row(n,0); });
  // terms that exist as scenes but have no folder (painted) get listed after the tree. Measured
  // today that is exactly ONE of 24 scene terms -- aPlanet -- and it looked identical to the 23
  // proven membranes above it; "built only" is what makes that one row's absence say so.
  TERMS.filter(t=>!INDEX[t]).forEach(t=>{
    if(QUERY&&t.toLowerCase().indexOf(QUERY)<0) return;
    if(BUILT_ONLY&&KINDS[t]!=='membrane') return;
    const d=document.createElement('div');
    d.className='node paint'+(t===term?' on':'');d.style.paddingLeft='6px';
    d.innerHTML='<span class=tw></span><span class=dot></span><span class=nm>'+t+'</span>';
    d.onclick=()=>pick(t);d.dataset.name=t;treeEl.appendChild(d);});
  /* KEEP THE PICKED ROW REACHABLE: a breadcrumb click can land 16 levels down, past the fold of a
     panel only as tall as the window. block:'nearest' scrolls only when it actually has to. */
  const cur=treeEl.querySelector('.node.on');
  if(cur&&cur.scrollIntoView) cur.scrollIntoView({block:'nearest'});
}

/* A QUERY IS A DIFFERENT SHAPE OF TREE, so it BORROWS the arrangement instead of destroying it: the
   human's expand state is copied on the first keystroke and handed back when the box empties. While
   it is live every surviving branch holds a hit, so every surviving branch opens -- a hit sitting
   inside a collapsed parent is not a search result. Triangles still work inside the filtered tree.

   "BUILT ONLY" DOES NOT FORCE ANYTHING OPEN, and that asymmetry is the point: a search is aimed at
   something specific and must reach it, while this is a MASK over the shape you already arranged.
   Forced open it would redraw all 23 membranes down to depth 17 -- the wall this whole block exists
   to remove. Masked, it answers a different question honestly: today it removes exactly one row of
   the eleven on screen, which is the page saying "everything else you are looking at is built." */
function refilter(){
  if(QUERY){
    if(!OPEN_SAVED) OPEN_SAVED=Object.assign({},OPEN);
    markAll(); TREE.forEach(openVis);
  }else if(OPEN_SAVED){
    OPEN=OPEN_SAVED; OPEN_SAVED=null; openTo(term);
  }
  paintTree();
}
var qEl=document.getElementById('q'), builtEl=document.getElementById('builtonly');
if(qEl) qEl.addEventListener('input',function(){ QUERY=qEl.value.trim().toLowerCase(); refilter(); });
if(builtEl) builtEl.addEventListener('change',function(){ BUILT_ONLY=builtEl.checked; refilter(); });
paintTree();
/* THE FRAME BUDGET, IN THE FOOTER. The page already shows what the membrane IS; this shows what
   it COSTS. Polled at 1 Hz rather than per frame: the number it reads is a 30-frame rolling mean,
   so asking faster than the mean can move only spends requests on the same answer. */
(function budgetHUD(){
  const el=document.getElementById('budget');
  if(!el) return;
  const tick=()=>fetch('/stats').then(r=>r.json()).then(s=>{
    const g=(s.grains||0).toLocaleString();
    const e=(s.expansions||0).toLocaleString(), ecap=(s.expansion_cap||0).toLocaleString();
    /* GRAINS ARE STILL SHOWN AND ARE NO LONGER THE BUDGET. The wall is EXPANSIONS -- (splat,tile)
       pairs -- which the 35-row sweep put at R^2 0.995 against frame time where grain count sat at
       0.472. The grain count stays on screen because it is the number a person changes when they
       edit an emit(), and watching it move independently of the cost is the fastest way to learn
       that a few huge splats outrank many small ones. */
    const over=s.over_expansions||s.over_time;
    const what=s.over_expansions?'EXPANSIONS OVER':(s.over_time?'TOO SLOW':'OK');
    el.innerHTML='fps: <i>'+(s.fps||0).toFixed(1)+'</i> &middot; '+(s.render_ms||0).toFixed(0)+' ms'+
                 ' (pred '+(s.predicted_ms||0).toFixed(0)+')'+
                 ' &middot; grains: <i>'+g+'</i>'+
                 ' &middot; expansions: <i>'+e+'</i> / '+ecap+' ('+(s.expansion_pct||0).toFixed(1)+'%)'+
                 ' &middot; '+(s.expansions_per_splat||0).toFixed(1)+' tiles/splat'+
                 ' &middot; budget: <i>'+what+'</i>';
    el.style.color = over ? '#ff5555' : '';
  }).catch(()=>{});
  tick(); setInterval(tick,1000);
})();
function pick(t){
  if(WALKING && t!=='theHuman') sitDown();   /* WALKING is `var` below: undefined here on first load, never a throw */
  term=t;
  fetch('/scene?term='+encodeURIComponent(t));
  /* THE TREE FOLLOWS THE PICK, it does not merely highlight it: opening this term's ancestors is
     what makes a jump from anywhere -- a breadcrumb, a search hit -- land somewhere legible. The
     `on` class is applied by row() from `term`, so the highlight has one source of truth. */
  openTo(t); paintTree();
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
  // THE SERIAL IS THE COMPRESSED STORY, so every step of it is a place you can GO. These are the
  // membranes this one's numbers came through, in order, and clicking one walks back UP the
  // derivation -- which is the question a person actually has in front of a picture ("where did that
  // number come from?"). Same text as before, duration and size untouched: only the names became
  // links, and the last one is marked `here` because you are already standing on it.
  const trail=(PATH[t]||[t]), ser=document.getElementById('serial');
  ser.innerHTML=trail.map((a,i)=>'<a href="#" data-go="'+a+'"'
        +(i===trail.length-1?' class=here':'')+'>'+a+'</a>').join(' / ')
      +(dur?('   ·   its movie spans '+dur):'')+size;
  ser.querySelectorAll('a[data-go]').forEach(a=>{
    a.onclick=e=>{ e.preventDefault(); pick(a.dataset.go); };
    /* the crumbs sit inside #stage, whose mousedown starts an orbit drag -- stop it here so
       clicking an ancestor never also spins the world you are about to leave. */
    a.onmousedown=e=>e.stopPropagation();
  });
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
var KEY={}, WALKING=false, mdx=0, mdy=0, jumped=false, used=false, clockDrag=false, clockTimer=null;
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
  /* A TEXT BOX OWNS ITS OWN KEYS. This handler preventDefaults W/A/S/D, so typing "theHuman" into
     the tree filter while the body is standing would steer the body AND swallow the letters. Focus
     is the arbiter: the sliders are type=range and unaffected (they use arrows, which are not
     bound here), and pointer-locked play never has a text box focused. */
  if(e.target&&e.target.tagName==='INPUT'&&e.target.type==='text') return;
  if(!WALKING) return;
  if(e.code==='Space'){ jumped=true; e.preventDefault(); }
  /* E IS EDGE-TRIGGERED LIKE SPACE: one press, one use=1 -- GRAB is a toggle, not a hold. */
  if(e.code==='KeyE' && !KEY['KeyE']){ used=true; }
  if(e.code==='KeyV' && !KEY['KeyV']){ toggleView(); }
  KEY[e.code]=true;
  if(['KeyW','KeyA','KeyS','KeyD','ShiftLeft','ControlLeft','KeyC','KeyV','KeyE'].includes(e.code)) e.preventDefault();
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
    'g <i>'+r.g.toFixed(2)+'</i> m/s&sup2; &middot; walk <i>'+r.walk.toFixed(2)+'</i> &middot; run <i>'+r.run.toFixed(2)+'</i> m/s'+
    (r.touch?'<br>'+r.touch:'');
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
/* THE THUMBSTICK, with its 360 degrees (the operator's law: the stick's angle is the step
   direction, its deflection the speed). Left stick: move vector, full analog. Right stick: look.
   A/cross: jump. RB/R1: sprint. The keyboard's 8 combinations are eight of those directions --
   whichever input has the bigger magnitude wins each tick. */
function readPad(){
  if(!navigator.getGamepads) return null;
  for(const p of navigator.getGamepads()){
    if(!p||!p.connected) continue;
    const dz=v=>Math.abs(v)<0.12?0:v;
    const lx=dz(p.axes[0]||0), ly=dz(p.axes[1]||0), rx=dz(p.axes[2]||0), ry=dz(p.axes[3]||0);
    if(lx||ly||rx||ry||p.buttons.some(b=>b.pressed))
      return {fwd:-ly, strafe:lx, mx:rx*LOOK*6, my:ry*LOOK*6,
              jump:!!(p.buttons[0]&&p.buttons[0].pressed),
              sprint:!!((p.buttons[5]&&p.buttons[5].pressed)||(p.buttons[7]&&p.buttons[7].value>0.5))};
  }
  return null;
}
setInterval(async()=>{
  if(!WALKING) return;
  let fwd=(KEY['KeyW']?1:0)-(KEY['KeyS']?1:0),
      str=(KEY['KeyD']?1:0)-(KEY['KeyA']?1:0),
      mx=mdx*LOOK, my=mdy*LOOK,
      sprint=!!KEY['ShiftLeft'], j=jumped, u=used;
  mdx=0; mdy=0; jumped=false; used=false;
  const pad=readPad();
  if(pad){
    if(Math.hypot(pad.fwd,pad.strafe)>Math.hypot(fwd,str)){ fwd=pad.fwd; str=pad.strafe; }
    mx+=pad.mx; my+=pad.my;
    sprint=sprint||pad.sprint; j=j||pad.jump;
  }
  const q='/walk?fwd='+fwd.toFixed(3)+'&strafe='+str.toFixed(3)+'&sprint='+(sprint?1:0)+
          '&jump='+(j?1:0)+'&crouch='+((KEY['ControlLeft']||KEY['KeyC'])?1:0)+'&use='+(u?1:0)+'&mx='+mx+'&my='+my;
  try{ paintWalk(await fetch(q).then(x=>x.json())); }catch(e){}
},33);

</script>
"""
