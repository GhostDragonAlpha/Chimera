"""session_legibility.py -- M9's measuring instrument: the same scene, two cameras.

The second recorded session (docs/THE_RECORDED_SESSION_2.md) showed the physics reporting stone,
pile, and tuft while the hero frames showed none of them. The isolated legibility probes
(stone_legibility.py) passed. Both were measured; they disagree. This instrument settles which
question each was answering, per the ABSENT-OR-ILLEGIBLE membrane:

    ONE scene -- the exact buffers the live viewer uploads in third person (ground + body +
    touchables, same sun, same exposure) -- rendered from TWO cameras per object:

      * CLOSE: a diagnostic camera 2 m out, aimed at the object. If nothing shows even here,
        the object is absent from the buffer (falsifier: spawn/upload defect).
      * SESSION: the live_viewer third-person formula (D 3.2 m, SIDE 1.15, pitch 0.55 high,
        aimed at the chest) with the walker standing at the beat position and the body in
        frame. If the object shows clearly HERE, the scene is fine and the defect is the
        recorder's capture path.

    Plus CARRIED: the stone at the waist, the session camera -- does the head occlude it?

    python tools/session_legibility.py    # -> ChimeraEngine/output/session_legibility/*.jpg
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))                    # ParticleEngine package
sys.path.insert(0, str(REPO / "ChimeraEngine"))  # walker, touchables

OUT = REPO / "ChimeraEngine" / "output" / "session_legibility"
W, H = 1920, 1080

STONE = (3.0, 5.0)          # touchables.spawn()'s own placements -- not chosen here
TUFT = (-3.5, 8.0)
PILE = (4.0, 12.0)


def _aim(cam, target):
    dx, dy, dz = (target[0] - cam.position[0], target[1] - cam.position[1],
                  target[2] - cam.position[2])
    cam.yaw = math.atan2(dy, dx)
    cam.pitch = math.atan2(dz, math.hypot(dx, dy))


def _session_cam(cam, w):
    """The live_viewer third-person formula, verbatim (live_viewer.py:167-186): D 3.2 behind,
    SIDE 1.15 shoulder-side, raised by the look pitch, aimed at the chest."""
    e = max(-0.35, min(1.25, 0.55))          # DOWN_LOOK's settled pitch
    f = (-math.sin(w.yaw), math.cos(w.yaw))
    r = (math.cos(w.yaw), math.sin(w.yaw))
    D, SIDE = 3.2, 1.15
    pivot = (w.x, w.y, w.z + 0.70 * w.eye + w.crouch)
    cx = w.x - f[0] * D * math.cos(e) + r[0] * SIDE
    cy = w.y - f[1] * D * math.cos(e) + r[1] * SIDE
    cz = pivot[2] + D * math.sin(e)
    import walker as _wk
    cz = max(cz, _wk.height_at(cx, cy) + 0.4)
    cam.position = np.array([cx, cy, cz], dtype=np.float32)
    _aim(cam, pivot)


def _face(w, dx, dy):
    """Walker yaw that faces direction (dx, dy): f = (-sin yaw, cos yaw)."""
    w.yaw = math.atan2(-dx, dy)


def main() -> int:
    from PIL import Image
    from ParticleEngine.gpu_pipeline import FullGPUPipeline
    from ParticleEngine.camera import FirstPersonCamera
    import walker as _wk
    import touchables as _to

    print("[session_legibility] carving the ground (~13 s, once)...")
    w = _wk.Walker()
    objs = _to.spawn()
    stone = next(o for o in objs if isinstance(o, _to.Stone))

    # THE GROUND ONCE, at the origin: the near shell is 180 m across and every object sits
    # within 15 m of spawn, so one build is the ground every frame here stands on.
    w.x, w.y = 0.0, 0.0
    w.z = _wk.height_at(0.0, 0.0)
    ground = np.ascontiguousarray(_wk.scene_around(w), dtype=np.float32)
    print(f"[session_legibility] ground {len(ground)} splats")

    pipe = FullGPUPipeline(bg=(0.015, 0.015, 0.04))
    cam = FirstPersonCamera((0.0, 0.0, 0.0))
    OUT.mkdir(parents=True, exist_ok=True)

    def shoot(name, carried=False):
        body = _wk.body_buffer(w)
        buf = np.concatenate([ground, body, _to.touchables_buffer(objs, w)], axis=0)
        pipe.upload(np.ascontiguousarray(buf, dtype=np.float32))
        img = pipe.render_from_gpu(cam, cam.params(W, H))
        out = OUT / f"{name}.jpg"
        Image.fromarray(img).save(out, quality=92)
        print(f"[session_legibility] {out.name}  ({len(buf)} splats)")

    def place(wx, wy, face):
        w.x, w.y = wx, wy
        w.z = _wk.height_at(wx, wy)
        w.vx = w.vy = w.vz = 0.0
        _face(w, *face)

    # -- STONE --------------------------------------------------------------------------------
    gz = _wk.height_at(*STONE)
    place(STONE[0] - 3.0, STONE[1] - 4.0, (3.0, 4.0))   # out of frame, facing it
    cam.position = np.array([STONE[0] - 1.4, STONE[1] - 1.4, gz + 1.0], dtype=np.float32)
    _aim(cam, (STONE[0], STONE[1], gz + stone.r))
    shoot("stone_close")

    place(*STONE, (3.0, 5.0))                            # the beat: standing ON the stone spot,
    _session_cam(cam, w)                                 # facing the approach from spawn
    shoot("stone_session")

    stone.carried = True                                 # the picked beat: at the waist
    stone.step(w, 1 / 60)
    shoot("stone_carried")
    stone.carried = False
    stone.x, stone.y = STONE
    stone.z = gz + stone.r

    # -- TUFT ---------------------------------------------------------------------------------
    gz = _wk.height_at(*TUFT)
    place(TUFT[0] + 3.0, TUFT[1] - 4.0, (-3.0, 4.0))
    cam.position = np.array([TUFT[0] + 1.4, TUFT[1] - 1.4, gz + 0.8], dtype=np.float32)
    _aim(cam, (TUFT[0], TUFT[1], gz + 0.2))
    shoot("tuft_close")

    place(*TUFT, (-7.5, -4.0))                           # approached from the pile's side
    _session_cam(cam, w)
    shoot("tuft_session")

    # -- PILE ---------------------------------------------------------------------------------
    gz = _wk.height_at(*PILE)
    place(PILE[0] - 3.0, PILE[1] - 5.0, (3.0, 5.0))
    cam.position = np.array([PILE[0] - 2.2, PILE[1] - 2.2, gz + 1.6], dtype=np.float32)
    _aim(cam, (PILE[0], PILE[1], gz + 0.4))
    shoot("pile_close")

    place(*PILE, (1.0, 7.0))                             # approached from the stone's side
    _session_cam(cam, w)
    shoot("pile_session")

    print("[session_legibility] done -- read every frame before believing any number.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
