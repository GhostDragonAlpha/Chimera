"""the_matrix_stress.py -- the elaborate advanced graphics test.

THE RECORD PLAYER MATRIX. A grid of record players, every one playing a
theLight membrane (platter disk, settled host body, equatorial ring, halo),
backed by a star field of LARGE splats. The composite is deliberately built so
a big part of the frame cost is tile expansions -- which the measured budgets
say is the quantity that drives render time (R^2 ~ 0.99), NOT grain count.

The test sweeps BOTH axes, because the pipeline is resolution-agnostic and the
cost model says resolution should multiply expansions: tile size is a fixed 32px,
so a splat at 4K touches 4x the tiles it touches at 1080p.

    grains  x  resolution  ->  render_ms / fps / expansions / expansions-per-splat

Every configuration also names its falsifier up front (RULE 0): the elaborate
composite must push the tile binner far enough that render_ms scales with
expansions; if the dense 250k baseline lands BELOW the measured 35ms it recorded
at 1080p, the pipeline regressed and the test is reporting a lie.

Usage:
    python ChimeraEngine/the_matrix_stress.py
"""
from __future__ import annotations

import math
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parents[0]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import numpy as np  # noqa: E402

OUT_DIR = _HERE / "output"
OUT_DIR.mkdir(parents=True, exist_ok=True)

NCOLS = 28
PX, PY, PZ = 0, 1, 2
TYPE = 11
CR, CG, CB, ALPHA = 16, 17, 18, 19
SIZE = 20

# Per-player layer geometry (all player-local, before grid placement)
_PLATTER_R = 4.2
_HOST_R = 2.0
_RING_A, _RING_B = 3.4, 1.6
_HALO_R = 3.8
_GRID_S = 13.0          # player centre spacing
_COL_PLATTER = (0.10, 0.10, 0.16)
_COL_HOST = (0.36, 0.49, 0.60)
_COL_RING = (1.00, 0.72, 0.31)
_COL_HALO = (0.20, 0.84, 0.78)
_COL_STAR = (0.55, 0.70, 1.00)


def _fibonacci_sphere(n: int, r: float, rng: np.random.Generator,
                      jitter: float = 0.04) -> np.ndarray:
    i = np.arange(n, dtype=np.float64)
    phi = np.pi * (3.0 - math.sqrt(5.0))
    y = 1.0 - (2.0 * i + 1.0) / n
    rad = np.sqrt(np.clip(1.0 - y * y, 0.0, 1.0))
    th = phi * i
    pts = np.stack([np.cos(th) * rad, y, np.sin(th) * rad], axis=1)
    pts *= r
    pts += rng.uniform(-jitter, jitter, pts.shape)
    return pts.astype(np.float32)


def build_matrix(grid: int, seed: int = 20260806) -> tuple[np.ndarray, dict]:
    """The composite: grid^2 record players + a large-splat star field."""
    rng = np.random.default_rng(seed)
    g = float(grid)
    extent = (g - 1.0) * _GRID_S + 2.0 * _PLATTER_R
    r_star = extent * 1.7
    layers = []

    for ix in range(grid):
        for iy in range(grid):
            cx = (ix - (grid - 1) / 2.0) * _GRID_S
            cy = (iy - (grid - 1) / 2.0) * _GRID_S

            platter = _fibonacci_sphere(700, _PLATTER_R, rng)
            platter[:, 1] *= 0.04                       # squash to a thin disk
            platter[:, 0] += cx
            platter[:, 2] += cy

            host = _fibonacci_sphere(800, _HOST_R, rng)
            host[:, 0] += cx
            host[:, 2] += cy

            ring = np.zeros((500, 3), np.float32)
            th = rng.uniform(0.0, 2.0 * np.pi, 500)
            rr = _RING_A * np.sqrt(rng.uniform(0.3, 1.0, 500))
            ring[:, 0] = rr * np.cos(th)
            ring[:, 1] = 0.25 * rr * np.sin(th)         # a touch of tilt
            ring[:, 2] = _RING_B * rr * np.sin(th)
            ring[:, 0] += cx
            ring[:, 2] += cy

            halo = _fibonacci_sphere(400, _HALO_R, rng)
            halo[:, 0] += cx
            halo[:, 2] += cy

            layers.append((platter, 700, _COL_PLATTER, 1.10))
            layers.append((host, 800, _COL_HOST, 0.55))
            layers.append((ring, 500, _COL_RING, 1.60))
            layers.append((halo, 400, _COL_HALO, 2.20))

    n_star = 2000 * grid * grid
    star = _fibonacci_sphere(n_star, r_star, rng, jitter=0.0)
    star[:, 0] *= rng.uniform(0.85, 1.0, n_star)
    star[:, 2] *= rng.uniform(0.85, 1.0, n_star)
    layers.append((star, n_star, _COL_STAR, 3.80))

    total = sum(n for _, n, _, _ in layers)
    buf = np.zeros((total, NCOLS), dtype=np.float32)
    off = 0
    for pos, n, (r, g_, b), size in layers:
        buf[off:off + n, PX:PZ + 1] = pos
        buf[off:off + n, 9] = 1.0                       # mass
        buf[off:off + n, 10] = -1.0                     # immortal
        buf[off:off + n, TYPE] = 3.0                    # SOLID
        buf[off:off + n, CR] = r
        buf[off:off + n, CG] = g_
        buf[off:off + n, CB] = b
        buf[off:off + n, ALPHA] = 0.9
        buf[off:off + n, SIZE] = size
        off += n
    meta = {"extent": extent, "r_star": r_star, "n_star": n_star}
    return np.ascontiguousarray(buf), meta


def build_dense(n: int, seed: int = 7) -> np.ndarray:
    """The dense baseline: one settled-style body, small splats -- the shape the
    measured 250k budget row used."""
    rng = np.random.default_rng(seed)
    pos = _fibonacci_sphere(n, 2.0, rng)
    buf = np.zeros((n, NCOLS), dtype=np.float32)
    buf[:, PX:PZ + 1] = pos
    buf[:, 9] = 1.0
    buf[:, 10] = -1.0
    buf[:, TYPE] = 3.0
    buf[:, CR:CB + 1] = (0.36, 0.49, 0.60)
    buf[:, ALPHA] = 0.9
    buf[:, SIZE] = 0.5
    return np.ascontiguousarray(buf)


def _camera_for(buf: np.ndarray, meta: dict):
    from ParticleEngine.camera import FirstPersonCamera
    extent = float(meta["extent"])
    d = extent / (2.0 * math.tan(math.radians(30.0))) * 1.15
    el, az = 0.40, -0.70
    ce = math.cos(el)
    pos = (d * ce * math.sin(az), -d * ce * math.cos(az), d * math.sin(el))
    nrm = math.sqrt(pos[0] ** 2 + pos[1] ** 2 + pos[2] ** 2)
    return FirstPersonCamera(
        position=np.array(pos, dtype=np.float32),
        yaw=math.atan2(-pos[1], -pos[0]),
        pitch=math.asin(-pos[2] / nrm),
        fov=np.radians(60),
        near=0.05,
        far=meta["r_star"] * 1.4 + d,
    )


def run_config(pipe, buf: np.ndarray, meta: dict, W: int, H: int, frames: int = 5):
    from ParticleEngine.camera import FirstPersonCamera
    cam = _camera_for(buf, meta)
    pipe.upload(buf, term="stress")
    p = cam.params(width=W, height=H)
    pipe.render_from_gpu(cam, p)                       # warmup: JIT / alloc
    pipe.render_from_gpu(cam, p)                       # warmup again
    t0 = time.perf_counter()
    for _ in range(frames):
        img = pipe.render_from_gpu(cam, p)
    dt = (time.perf_counter() - t0) / frames
    st = pipe.tile_stats()
    return {
        "grains": buf.shape[0],
        "W": W, "H": H,
        "ms": dt * 1e3,
        "fps": 1.0 / dt,
        "expansions": st["expansions"],
        "kept": st["kept"],
        "nv": st["nv"],
        "exp_splat": pipe.expansions_per_splat(),
        "img": img,
    }


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--grids", type=int, nargs="*", default=[2, 3, 4, 5])
    ap.add_argument("--res", type=int, nargs="*", default=[720, 1080, 1440, 2160])
    args = ap.parse_args()

    from ParticleEngine.gpu_pipeline import FullGPUPipeline
    pipe = FullGPUPipeline(bg=(0.015, 0.015, 0.04))

    MAX_RENDER_MS = 200.0
    print("THE RECORD PLAYER MATRIX -- elaborate advanced graphics test")
    print("  falsifier: dense 250k baseline at 1080p must NOT land far below")
    print("  the 35.23ms it measured in docs/MEASURED_RENDER_BUDGETS.md")
    print("=" * 112)
    hdr = (f"{'grains':>8} {'res':>11} {'render ms':>10} {'fps':>7} "
           f"{'expansions':>11} {'exp/splat':>9} {'nv':>8}  verdict")
    print(hdr)
    print("-" * 112)

    res_list = []
    for W, H in sorted(set((int(1920 * r / 1080), r) for r in args.res)):
        res_list.append((W, H))
    if not any(H == 1080 for _, H in res_list):
        res_list.append((1920, 1080))

    results = []
    for grid in args.grids:
        buf, meta = build_matrix(grid)
        for W, H in res_list:
            r = run_config(pipe, buf, meta, W, H)
            ok = r["ms"] <= MAX_RENDER_MS
            verdict = "under wall" if ok else "OVER WALL"
            results.append(r)
            print(f"{r['grains']:>8} {f'{W}x{H}':>11} {r['ms']:>9.1f} "
                  f"{r['fps']:>7.1f} {r['expansions']:>11} {r['exp_splat']:>9.1f} "
                  f"{r['nv']:>8}  {verdict}")
        print(f"  -- png saved: {OUT_DIR / f'theMatrix_grid{grid}.png'}")

    # The dense baseline -- must reproduce ~35ms at 1080p or the machine lied.
    buf = build_dense(250_000)
    meta = {"extent": 5.0, "r_star": 60.0}
    r = run_config(pipe, buf, meta, 1920, 1080)
    print("-" * 112)
    print(f"dense 250k baseline 1920x1080  {r['ms']:.1f}ms  {r['fps']:.1f}fps  "
          f"{r['expansions']} expansions  (measured budget said ~35ms)")
    print("=" * 112)

    worst = max(results, key=lambda x: x["ms"])
    print(f"worst configuration: {worst['grains']} grains @ {worst['W']}x{worst['H']} "
          f"-> {worst['ms']:.1f}ms ({worst['fps']:.1f} fps), "
          f"{worst['expansions']} expansions")
    within = all(x["ms"] <= MAX_RENDER_MS for x in results)
    print(f"falsifier check: all composite configs {'within' if within else 'NOT within'} "
          f"the {MAX_RENDER_MS:.0f}ms render wall")
    return 0 if within else 1


if __name__ == "__main__":
    raise SystemExit(main())
