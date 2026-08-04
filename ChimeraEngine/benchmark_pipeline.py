"""benchmark_pipeline.py -- what a frame costs, and WHICH quantity predicts it.

`docs/MEASURED_RENDER_BUDGETS.md` established that `MAX_GRAINS_PER_FRAME` was derived 3.64x wrong
and that a 64x increase in grains buys only 1.94x the time. That measurement was three zoom levels
on one body. This is the full sweep, and it also settles the follow-up question: if grain count is
not the predictor, what is?

TWO MODELS ARE FITTED AND BOTH ARE REPORTED, because "coverage is the real driver" was a
hypothesis formed from two data points and hypotheses formed that way are usually half right:

    render_ms ~ a*coverage + b        the proposed model
    render_ms ~ a*grains   + b        the model currently in perf_guard

R^2 for each, on the same rows, so the comparison is not between a fresh fit and a remembered one.

WHAT COVERAGE MEANS HERE: the fraction of frame pixels that are not background. It is measured off
the rendered image rather than predicted from the geometry, so it costs nothing extra and cannot
disagree with what was actually drawn.

    python ChimeraEngine/benchmark_pipeline.py            # full sweep -> docs/pipeline_benchmark.csv
    python ChimeraEngine/benchmark_pipeline.py --quick    # 3 classes, for a smoke check
"""
from __future__ import annotations

import csv
import math
import sys
import time
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE))

import splat_appearance as sa
import lod as LOD
import perf_guard as pg

W, H = 1920, 1080
FOV = 1.047
ZOOMS = (0.25, 0.5, 1.0, 2.0, 5.0)
N_FRAMES = 5          # 2 discarded as warm-up, 3 timed -- the task asks for 3
_BG = np.array([0.015, 0.015, 0.04], dtype=np.float32) * 255.0


def _aim(cam, dist):
    """Place the camera at `dist` on -y and point it at the origin.

    The aim-at-origin formula, not `atan2(-pos[1], pos[0])`. That expression is correct only where
    pos[0] == 0 and renders bare background elsewhere -- it cost this project two files' worth of
    silent empty frames, and a benchmark that times an empty frame reports the clear-screen cost
    as the render cost.
    """
    pos = (0.0, -dist, 0.0)
    cam.position = np.array(pos, dtype=np.float32)
    n = math.sqrt(sum(p * p for p in pos)) or 1.0
    fx, fy, fz = -pos[0] / n, -pos[1] / n, -pos[2] / n
    cam.yaw = math.atan2(fy, fx)
    cam.pitch = math.atan2(fz, math.hypot(fx, fy))


def coverage_of(img) -> float:
    """Fraction of pixels that are not background. Measured off the frame, not predicted."""
    a = img.astype(np.float32)
    return float(((a > _BG + 2.0).any(-1)).mean())


def heaviest_per_class() -> dict:
    """One representative per surface class: the term with the most grains in it.

    THE HEAVIEST, not a random member, because the budget question is about the worst case. A
    class represented by its median member would produce a benchmark that says everything is fine
    and tell you nothing about the frame that drops.
    """
    best: dict[str, tuple[int, str]] = {}
    for t in sa.scene_terms():
        b = sa.scene_buffer(t)
        if b is None or b.shape[0] == 0:
            continue
        k = pg._classify_type(t)
        if k not in best or b.shape[0] > best[k][0]:
            best[k] = (int(b.shape[0]), t)
    return {k: v[1] for k, v in best.items()}


def bench(quick: bool = False) -> list[dict]:
    from ParticleEngine.gpu_pipeline import FullGPUPipeline
    from ParticleEngine.camera import FirstPersonCamera
    pipe = FullGPUPipeline(bg=(0.015, 0.015, 0.04))
    cam = FirstPersonCamera((0.0, -3.0, 0.0))

    reps = heaviest_per_class()
    if quick:
        reps = dict(list(reps.items())[:3])
    rows = []
    for kind, term in sorted(reps.items()):
        buf = sa.scene_buffer(term)
        R = LOD.body_radius(buf)
        mips = LOD.build_mips(buf, R) if LOD.should_lod(buf) else None
        for z in ZOOMS:
            dist = 2.8 * R * z
            _aim(cam, dist)
            draw = buf
            if mips and len(mips) > 1:
                draw = LOD.select(mips, LOD.projected_radius_px(R, dist, H, FOV))
            pipe.upload(np.ascontiguousarray(draw, dtype=np.float32))
            params = cam.params(W, H)
            ts, img = [], None
            for i in range(N_FRAMES):
                t0 = time.perf_counter()
                img = pipe.render_from_gpu(cam, params)
                ts.append((time.perf_counter() - t0) * 1000.0)
            ts = ts[2:]                          # discard JIT warm-up
            ms, sd = float(np.mean(ts)), float(np.std(ts))
            cov = coverage_of(img)
            rows.append({"class": kind, "term": term, "zoom": z,
                         "n_base": int(buf.shape[0]), "n_lod": int(draw.shape[0]),
                         "coverage_frac": round(cov, 6), "render_ms": round(ms, 3),
                         "render_ms_std": round(sd, 3), "fps": round(1000.0 / ms, 2)})
            print(f"  {term:22s} {z:5.2f}x  base={buf.shape[0]:>7d} lod={draw.shape[0]:>7d} "
                  f"cover={100*cov:6.2f}%  {ms:7.2f} +- {sd:5.2f} ms  {1000.0/ms:6.1f} fps",
                  flush=True)
    return rows


def _fit(x, y):
    """Least squares y = a*x + b, returning (a, b, R^2). R^2 against the mean, the usual sense."""
    x = np.asarray(x, float); y = np.asarray(y, float)
    if len(x) < 3 or np.ptp(x) == 0:
        return 0.0, float(np.mean(y)), 0.0
    a, b = np.polyfit(x, y, 1)
    pred = a * x + b
    ss_res = float(((y - pred) ** 2).sum())
    ss_tot = float(((y - y.mean()) ** 2).sum())
    return float(a), float(b), (1.0 - ss_res / ss_tot) if ss_tot > 0 else 0.0


def model_report(rows) -> dict:
    cov = [r["coverage_frac"] for r in rows]
    gr = [r["n_lod"] for r in rows]
    ms = [r["render_ms"] for r in rows]
    a_c, b_c, r2_c = _fit(cov, ms)
    a_g, b_g, r2_g = _fit(gr, ms)
    print("\n" + "=" * 92)
    print("  WHICH QUANTITY PREDICTS THE FRAME TIME?   (same rows, both fits)")
    print("=" * 92)
    print(f"  coverage model   render_ms = {a_c:9.3f} * coverage + {b_c:7.3f}    R^2 = {r2_c:.4f}")
    print(f"  grain    model   render_ms = {a_g:.3e} * grains   + {b_g:7.3f}    R^2 = {r2_g:.4f}")
    win = "coverage" if r2_c > r2_g else "grains"
    print(f"  -> {win} wins by dR^2 = {abs(r2_c - r2_g):.4f}")
    if max(r2_c, r2_g) < 0.5:
        print("  NEITHER MODEL IS GOOD (best R^2 < 0.5). The cost is dominated by something these")
        print("  two do not name -- kernel launch overhead, the tile sort, or per-frame fixed work.")
    # THE FIXED FLOOR IS ITS OWN FINDING: if b dominates over the whole measured range, the frame
    # cost is mostly NOT a function of the scene at all, and no scene-derived budget can control it.
    span = max(ms) - min(ms)
    print(f"  intercept {b_c:.2f} ms against a measured span of {span:.2f} ms "
          f"({100*b_c/max(max(ms),1e-9):.0f}% of the worst frame is fixed cost)")
    return {"coverage": {"a": a_c, "b": b_c, "r2": r2_c},
            "grains": {"a": a_g, "b": b_g, "r2": r2_g},
            "winner": win, "d_r2": abs(r2_c - r2_g),
            "ms_min": min(ms), "ms_max": max(ms)}


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    quick = "--quick" in argv
    print("PIPELINE BENCHMARK -- heaviest term per surface class, 5 zoom levels")
    print("=" * 92)
    rows = bench(quick)
    m = model_report(rows)
    out = _HERE.parent / "docs" / "pipeline_benchmark.csv"
    with open(out, "w", newline="", encoding="utf8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"\n  wrote {out}  ({len(rows)} rows)")
    return 0 if len(rows) >= 30 or quick else 1


if __name__ == "__main__":
    sys.exit(main())
