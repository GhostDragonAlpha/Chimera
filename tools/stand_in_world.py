"""stand_in_world.py -- THE STAND, IN THE PLACE: the two rigs composed into one frame.

The musculoskeletal stand (MuJoCo, the proven stand_theta, the real parser) rendered INSIDE the
carved splat ground the session records. The physics is f3_stand's, unchanged, on its own flat
plane -- the composition is RENDER-ONLY and says so: the body's geoms are emitted as splats
(mesh vertices, capsule chains; zero-normal tubes for shape, touchables._shade's one sun for
light) and composited with walker.scene_around + touchables. The membrane is stated in
docs/THE_RECORDED_SESSION_2.md; the falsifier is the frames.

    python tools/stand_in_world.py     # -> ChimeraEngine/output/ports/stand_in_world/
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))                    # ParticleEngine package
sys.path.insert(0, str(REPO / "ChimeraEngine"))  # walker, touchables
sys.path.insert(0, str(Path(__file__).resolve().parent))
from world import load_body
from stand_port import derive_stand_port, MYOBODY
from train_stand import joint_ids, seat_in_limits
from parser import Parser, default_registry
from f3_stand import THETA, CTRL_EVERY, PHASE1_SECS, PHASE2_MAX

OUTDIR = REPO / "ChimeraEngine" / "output" / "ports" / "stand_in_world"
FRAME_DT = 0.25
W, H = 1920, 1080
BODY_AT = (1.5, 3.0)          # the carved-ground spot the body is drawn at, near spawn (THE HUMAN
                              # render placement; the physics plane it stands on is flat, so any
                              # flat-ish spot is the same claim)
_BODY_VERTS_PER_GEOM = 220    # subsample budget per mesh geom -- shape without flooding the GPU
_BODY_SPLAT = 0.028           # m, display width of a body splat (render row, legibility)


def body_splats(m, d, mujoco, offset, walker):
    """The body's geoms as a splat buffer, translated by `offset` (render-only composition).
    Mesh geoms contribute their vertices (the myo body's geoms ARE the flesh); capsules and
    spheres contribute axis chains; the plane is skipped. Normals are faked UP for lighting and
    then ZEROED for shape -- the tuft's tube trick (docs/THE_VEGETATION_GEOMETRY.md, membrane 3).
    """
    from matter import blank, SOLID
    import touchables as _to
    pts, sizes, albs = [], [], []
    for gi in range(m.ngeom):
        gt = m.geom_type[gi]
        if gt == mujoco.mjtGeom.mjGEOM_PLANE:
            continue
        pos = np.asarray(d.geom_xpos[gi])
        mat = np.asarray(d.geom_xmat[gi]).reshape(3, 3)
        rgba = np.asarray(m.geom_rgba[gi])
        alb = rgba[:3].astype(np.float32)
        if gt == mujoco.mjtGeom.mjGEOM_MESH:
            mid = int(m.geom_dataid[gi])
            a0, nv = int(m.mesh_vertadr[mid]), int(m.mesh_vertnum[mid])
            if nv <= 0:
                continue
            v = np.asarray(m.mesh_vert)[a0:a0 + nv]          # (nv, 3) -- already row-major
            stride = max(1, nv // _BODY_VERTS_PER_GEOM)
            v = v[::stride]
            world = pos + v @ mat.T
            pts.append(world)
            sizes += [_BODY_SPLAT] * len(world)
            albs += [alb] * len(world)
        elif gt in (mujoco.mjtGeom.mjGEOM_CAPSULE, mujoco.mjtGeom.mjGEOM_SPHERE,
                    mujoco.mjtGeom.mjGEOM_BOX):
            size = np.asarray(m.geom_size[gi])
            if gt == mujoco.mjtGeom.mjGEOM_SPHERE:
                chain = [pos]
            elif gt == mujoco.mjtGeom.mjGEOM_CAPSULE:
                half = float(size[1])
                axis = mat[:, 2]
                n = max(3, int(2.0 * half / _BODY_SPLAT) + 1)
                chain = [pos + axis * (f * 2.0 - 1.0) * half for f in np.linspace(0, 1, n)]
            else:               # box: the eight corners and the centre
                corners = np.array([[sx, sy, sz] for sx in (-1, 1) for sy in (-1, 1)
                                    for sz in (-1, 1)]) * size
                chain = [pos + c @ mat.T for c in corners] + [pos]
            pts.append(np.array(chain))
            sizes += [_BODY_SPLAT] * len(chain)
            albs += [alb] * len(chain)
    if not pts:
        return None
    P = np.concatenate(pts, axis=0) + np.array(offset, dtype=np.float64)
    b = blank(len(P))
    b[:, 0], b[:, 1], b[:, 2] = P[:, 0], P[:, 1], P[:, 2]
    b[:, 21:24] = (0.0, 0.0, 1.0)            # the LIGHTING claim
    b[:, 20] = np.array(sizes, dtype=np.float32)
    b[:, 11] = SOLID
    _to._shade(b, np.array(albs, dtype=np.float32), walker)   # per-geom colour: muscle reads red
    b[:, 21:24] = 0.0                        # the SHAPE claim: isotropic balls, un-cullable tubes
    return b


def run() -> int:
    import mujoco
    from PIL import Image, ImageDraw
    from ParticleEngine.gpu_pipeline import FullGPUPipeline
    from ParticleEngine.camera import FirstPersonCamera
    import walker as _wk
    import touchables as _to
    if not THETA.exists():
        raise SystemExit(f"no {THETA} -- run `python tools/train_stand.py` first (rule 20).")

    print("[stand_in_world] carving the ground (~13 s, once)...")
    w = _wk.Walker()
    w.x, w.y = 0.0, 0.0
    w.z = _wk.height_at(0.0, 0.0)
    ground = np.ascontiguousarray(_wk.scene_around(w), dtype=np.float32)
    objs = _to.spawn()
    gz = float(_wk.height_at(*BODY_AT))
    offset = (BODY_AT[0], BODY_AT[1], gz)

    theta = np.load(THETA)
    P = derive_stand_port()
    m, g = load_body(MYOBODY, mujoco)
    d = mujoco.MjData(m)
    nu, jids = m.nu, joint_ids(m, mujoco)
    tgt = P["OUT pelvis_target_m"]
    parser = Parser(default_registry(theta, tgt, nu))
    mujoco.mj_resetDataKeyframe(m, d, 0)
    mujoco.mj_forward(m, d)
    seat_in_limits(m, d, mujoco, jids)

    pipe = FullGPUPipeline(bg=(0.015, 0.015, 0.04))
    cam = FirstPersonCamera((0.0, 0.0, 0.0))
    # the session's third-person camera, standing 3.2 m south of the body, looking north at it
    cam.position = np.array([BODY_AT[0] + 1.15, BODY_AT[1] - 3.2 * math.cos(0.55),
                             gz + 1.25 + 3.2 * math.sin(0.55)], dtype=np.float32)
    dx, dy, dz = BODY_AT[0] - cam.position[0], BODY_AT[1] - cam.position[1], \
        gz + 0.9 - cam.position[2]
    cam.yaw = math.atan2(dy, dx)
    cam.pitch = math.atan2(dz, math.hypot(dx, dy))

    steps = int((PHASE1_SECS + PHASE2_MAX) / m.opt.timestep)
    phase2_start = int(PHASE1_SECS / m.opt.timestep)
    grab_every = int(FRAME_DT / m.opt.timestep)
    frames, zs = [], []
    slumped_at = None
    OUTDIR.mkdir(parents=True, exist_ok=True)
    for stale in OUTDIR.glob("frame_*.jpg"):
        stale.unlink()
    for k in range(steps):
        stand_on = k < phase2_start
        if k % CTRL_EVERY == 0:
            z = float(d.qpos[2])
            q = d.qpos[3:7]
            pitch = float(np.arctan2(2 * (q[0] * q[2] - q[3] * q[1]),
                                     1 - 2 * (q[1] ** 2 + q[2] ** 2)))
            roll = float(np.arctan2(2 * (q[0] * q[1] + q[2] * q[3]),
                                    1 - 2 * (q[1] ** 2 + q[2] ** 2)))
            parser.set_verb("STAND", stand_on)
            u, _ = parser.command({"z": z, "pitch": pitch, "roll": roll})
            d.ctrl[:] = u if u is not None else 0.0
        mujoco.mj_step(m, d)
        if k % CTRL_EVERY == 0:
            zs.append(float(d.qpos[2]))
        if k % grab_every == 0 or k == steps - 1:
            body = body_splats(m, d, mujoco, offset, w)
            layers = [ground, _to.touchables_buffer(objs, w)]
            if body is not None:
                layers.append(body)
            pipe.upload(np.ascontiguousarray(np.concatenate(layers, axis=0), dtype=np.float32))
            img = Image.fromarray(pipe.render_from_gpu(cam, cam.params(W, H)))
            draw = ImageDraw.Draw(img)
            t = k * m.opt.timestep
            draw.text((10, 8), f"t={t:4.2f}s  STAND {'ON ' if stand_on else 'OFF'}  "
                               f"pelvis {100.0 * float(d.qpos[2]) / tgt:.0f}%",
                      fill=(255, 255, 255))
            frames.append(img)
        if not stand_on and float(d.qpos[2]) < 0.5 * tgt:
            slumped_at = k * m.opt.timestep - PHASE1_SECS
            break

    for i, img in enumerate(frames):
        img.save(OUTDIR / f"frame_{i:02d}.jpg", quality=90)
    cols = 4
    rows = (len(frames) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * W // 4, rows * H // 4), (10, 10, 20))
    for i, img in enumerate(frames):
        sheet.paste(img.resize((W // 4, H // 4)), ((i % cols) * W // 4, (i // cols) * H // 4))
    sheet_path = OUTDIR / "stand_in_world_sheet.jpg"
    sheet.save(sheet_path, quality=92)

    held = 100.0 * min(zs[:int(PHASE1_SECS / (CTRL_EVERY * m.opt.timestep)) + 1]) / tgt
    print(f"[stand_in_world] {len(frames)} frames -> {OUTDIR}")
    print(f"[stand_in_world] phase 1 pelvis MIN {held:.1f}% of target (bar: >= 90%)")
    print(f"[stand_in_world] phase 2: "
          + (f"slumped in {slumped_at:.2f}s after release" if slumped_at is not None
             else "still upright -- FALSIFIER FIRED"))
    print(f"[stand_in_world] sheet: {sheet_path} -- read it before believing this log.")
    return 0


if __name__ == "__main__":
    sys.exit(run())
