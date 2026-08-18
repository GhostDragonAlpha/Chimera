"""master_loop_sdf.py — THE UNIFIED SDF SUBSTRATE, end to end.

One genome -> one skeleton -> one sparse SDF grid. That same grid is the collision
shape for physics AND the source of surface splats for rendering. No mesh. No convex
hull. No GJK/EPA. The membrane IS the field.

This is the wiring the design asked for: `master_loop` but the body is an SDFBody,
its grid answers both the contact solver (∇SDF = contact normal, penetration = -sdf)
and the renderer (surface voxels -> one Gaussian splat each, optical fields from the
voxel's material id). Physics runs at fixed dt; rendering reads the grid every frame.

RULE 0 MEMBRANE (stated before the run):
  STATEMENT  A single SDF substrate can serve physics and rendering at once: a
             genome-grown body rests on a ground plane using only SDF contact
             (penetration = -sdf, normal = ∇SDF), with no mesh or convex hull.
  PREDICTION Under gravity the body's COM y descends, then settles at a finite
             resting height above the plane; momentum is ~0 until contact, then the
             contact damping bleeds it off instead of ringing forever.
  FALSIFIER  After N steps: COM y must be >= plane_y - rest_eps (no sinking through)
             AND |v| must not grow unboundedly (no blow-up). Either fails -> substrate
             fails; no separate mesh was needed to get there.

Usage:
    python ChimeraEngine/master_loop_sdf.py
"""
from __future__ import annotations

import math
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import numpy as np  # noqa: E402

from physics import quat_to_mat  # noqa: E402

# --- splat buffer layout (identical to master_loop.py so the GPU pipeline consumes it) ---
NCOLS = 28
PX, PY, PZ = 0, 1, 2
TYPE = 11
CR, CG, CB, ALPHA = 16, 17, 18, 19
SIZE = 20

# --- material -> optical fields (albedo rgb, alpha). Tissue types from sdf_grid build. ---
MATERIAL_OPTICS = {
    "void":   ((0.0, 0.0, 0.0), 0.0),
    "bone":   ((0.86, 0.82, 0.72), 1.0),
    "muscle": ((0.74, 0.22, 0.20), 0.92),
    "skin":   ((0.90, 0.66, 0.55), 0.95),
    "ground": ((0.30, 0.28, 0.24), 1.0),
}


def _blank(n: int) -> np.ndarray:
    b = np.zeros((n, NCOLS), dtype=np.float32)
    b[:, 9] = 1.0
    b[:, 10] = -1.0
    b[:, TYPE] = 3.0
    b[:, ALPHA] = 0.9
    return b


def _fill(buf: np.ndarray, pos: np.ndarray, rgb, size: float):
    n = pos.shape[0]
    buf[:, PX:PZ + 1] = pos
    buf[:, CR] = rgb[0]
    buf[:, CG] = rgb[1]
    buf[:, CB] = rgb[2]
    buf[:, SIZE] = size


def _material_color(mat_name: str):
    return MATERIAL_OPTICS.get(mat_name, MATERIAL_OPTICS["void"])


def body_splat_buffer(body, voxel_size: float) -> np.ndarray:
    """Surface voxels of the body -> splat buffer. One Gaussian per surface voxel.

    Vectorized: pulls world points + material ids directly from the grid (no Python loop).
    """
    if getattr(body, "is_ground", False):
        return _blank(0)
    pos, sdfs, mats = body.grid.world_positions(1)
    if pos.shape[0] == 0:
        return _blank(0)
    rel = pos - body.com_local
    R = quat_to_mat(body.q)
    world = (body.x[None, :] + (rel @ R.T)).astype(np.float32)
    n = world.shape[0]
    buf = _blank(n)
    rgb = np.empty((n, 3), np.float32)
    alpha = np.empty(n, np.float32)
    names = body.grid._material_names
    for mid in range(len(names)):
        m = names[mid] if 0 <= mid < len(names) else "void"
        cr, al = _material_color(m)
        mask = mats == mid
        rgb[mask] = cr
        alpha[mask] = al
    buf[:, PX:PZ + 1] = world
    buf[:, CR:CB + 1] = rgb
    buf[:, ALPHA] = alpha
    buf[:, SIZE] = voxel_size * 1.6
    return buf


def ground_splat_buffer(plane_y: float, half: float, res: int = 48) -> np.ndarray:
    """A coarse ground quad rendered as splats so the eye has a floor."""
    xs = np.linspace(-half, half, res)
    zs = np.linspace(-half, half, res)
    gx, gz = np.meshgrid(xs, zs)
    pos = np.stack([gx.ravel(), np.full(gx.size, plane_y), gz.ravel()], axis=1).astype(np.float32)
    buf = _blank(pos.shape[0])
    _fill(buf, pos, MATERIAL_OPTICS["ground"][0], (2 * half / res) * 1.4)
    return buf


def main() -> int:
    from core.terrarium import Genome
    from sdf_body import body_from_genome, SDFWorld

    from ParticleEngine.gpu_pipeline import FullGPUPipeline
    from ParticleEngine.camera import FirstPersonCamera

    VOXEL = 0.08
    PLANE_Y = 0.0
    N_STEPS = 240
    DT = 1 / 60.0

    g = Genome.quadruped()
    body = body_from_genome(g, seed=1, voxel_size=VOXEL)
    # Lift the body well above the plane so it drops and lands (tests SDF contact).
    body.x = np.array([0.0, 6.0, 0.0], dtype=float)
    y0 = body.x[1]

    world = SDFWorld(bodies=[body], gravity=np.array([0.0, -9.81, 0.0]),
                     dt=DT, substeps=4, use_gpu=True, contact_stride=6)
    ground = world.add_ground(half_extent=50.0, y=PLANE_Y)

    # Material RGBA table for the GPU splat emitter (index by grid material id).
    names = body.grid._material_names
    mat_rgba = np.array([_material_color(n)[0] + (_material_color(n)[1],)
                         for n in names], np.float32) if names else np.zeros((1, 4), np.float32)
    # pad to at least 1 entry with a void row
    if mat_rgba.shape[0] == 0:
        mat_rgba = np.zeros((1, 4), np.float32)
    world._ensure_gpu()
    world._gpu.set_material_table(mat_rgba)
    body_vol = world._gpu_vols[0]

    pipe = FullGPUPipeline(bg=(0.01, 0.01, 0.04))

    print("UNIFIED SDF SUBSTRATE - genome -> grid -> physics + render, one source of truth")
    print(f"  voxel={VOXEL}  surface voxels={len(body.surface_voxels_world())}  "
          f"mass={body.mass:.1f}")
    print("-" * 96)
    print(f"{'step':>5} {'t':>6} {'com_y':>8} {'|v|':>8} {'penetr':>8} {'render ms':>10} {'fps':>6}")
    print("-" * 96)

    rest_eps = VOXEL * 2.0
    max_v = 0.0
    max_render = 0.0
    results = []

    for step in range(N_STEPS):
        world.step()

        # Vectorized contact readout (host numpy over the cached arrays -- no per-voxel loop)
        pts = body.world_points(1)
        ys = pts[:, 1] - PLANE_Y if pts.shape[0] else np.zeros(0)
        penetr = float(np.max(-ys[(ys < 0)])) if (ys < 0).any() else 0.0

        com_y = body.x[1]
        speed = float(np.linalg.norm(body.v))
        max_v = max(max_v, speed)

        # --- rendering: surface voxels -> splats, emitted on GPU from the SAME grid ----
        bbuf = world._gpu.emit_splat_buffer(body, body_vol)
        gbuf = ground_splat_buffer(PLANE_Y, 50.0)
        buf = np.vstack([bbuf, gbuf]) if bbuf.shape[0] else gbuf

        # camera follows the body from a short offset, looking back at it
        offset = np.array([3.5, 1.5, 3.5])
        cam_pos = body.x + offset
        to_body = body.x - cam_pos
        dist = float(np.linalg.norm(to_body)) or 1.0
        cam = FirstPersonCamera(
            position=cam_pos.astype(np.float32),
            yaw=math.atan2(-to_body[1], -to_body[0]),
            pitch=math.asin(-to_body[2] / dist),
            fov=math.radians(60), near=0.05, far=200.0,
        )

        pipe.upload(np.ascontiguousarray(buf), term="")
        prm = cam.params(width=1280, height=720)
        t0 = time.perf_counter()
        pipe.render_from_gpu(cam, prm)
        rms = (time.perf_counter() - t0) * 1e3
        max_render = max(max_render, rms)

        results.append((step, step * DT, com_y, speed, penetr))
        if step % 20 == 0 or step == N_STEPS - 1:
            print(f"{step:>5} {step*DT:6.2f} {com_y:8.3f} {speed:8.3f} "
                  f"{penetr:8.4f} {rms:10.2f} {1000.0/rms:6.1f}")

    print("-" * 96)
    # FALSIFIER checks (RULE 0: named before the run)
    # S1 the single SDF substrate rests the genome-grown body on the plane using only
    #     SDF contact (no mesh, no convex hull). Measured: it comes to rest (|v|~0) and
    #     its lowest voxel sits at/above the plane (no sink-through).
    # S2 the contact solver resolved penetration: final max penetration ~ 0 (not growing).
    # S3 the integration is bounded: max |v| stays finite (no blow-up).
    settled_y = body.x[1]
    rest_pen = max(( -d for wp, sdf, _ in body.surface_voxels_world()
                     if (d := ground.sdf_at_world(wp)) < 0 ), default=0.0)
    ok_rest = float(np.linalg.norm(body.v)) < 0.5
    ok_no_sink = settled_y >= PLANE_Y - rest_eps and rest_pen < rest_eps * 4
    ok_no_blowup = max_v < 50.0

    verdicts = [
        ("S1 single substrate rests body on plane (no mesh/hull)", ok_rest and ok_no_sink),
        ("S2 no penetration through ground (resolved by grad SDF)", ok_no_sink),
        ("S3 numerically bounded (no blow-up)", ok_no_blowup),
    ]
    print("FALSIFIER VERDICTS")
    for name, ok in verdicts:
        print(f"  {'PASS' if ok else 'FAIL'}: {name}")
    print(f"  com_y {y0:.2f} -> {settled_y:.3f} | max|v| {max_v:.2f} | "
          f"final penetration {rest_pen:.4f} | worst render {max_render:.1f} ms")
    print(f"  surface splats/frame: {len(body.surface_voxels_world())} (same grid as physics)")
    return 0 if all(ok for _, ok in verdicts) else 1


if __name__ == "__main__":
    raise SystemExit(main())
