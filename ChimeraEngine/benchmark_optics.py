"""benchmark_optics.py -- what the specular term COSTS, measured the way §5b demands.

    python ChimeraEngine/benchmark_optics.py

INTERLEAVED A/B (docs/RENDER_COST_MODEL.md §5b): light-off and light-on frames alternate inside
one process, same buffer, same camera, same GPU hour -- so contention lands on both arms equally
and the difference is the term, not the machine. Single-run performance claims are banned here;
the documented frame-noise floor is ±13-44% between sweeps, and the per-arm std is printed so the
delta can be judged against it.

WORST CASE BY CONSTRUCTION: every grain faces both the camera and the light (normals all +y,
light +y, camera on +y), F0 and slope populated -- so the specular block's full arithmetic runs
for every grain. A mixed scene costs less than what is measured here.

PRE-STATED DECISION RULE (written before the first run, per the plan):
  - if the A/B delta at the largest N clears its own noise (|delta| > 2*sigma of the paired
    differences), the slope MS_PER_LIT_GRAIN is fitted over N and lands in perf_guard with an
    inversion, exactly like MS_PER_EXPANSION;
  - if it does NOT clear the noise, the honest record is an UPPER BOUND (noise floor / N), the
    light term is declared NOT THE BINDING CONSTRAINT, and NO guard check is added -- a wall
    derived from an unmeasurable slope would be decorative, which is the exact failure
    perf_guard's own FALSIFIER names.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT), str(ROOT / "story")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import matter                                              # noqa: E402
from ParticleEngine import gpu_pipeline as gp              # noqa: E402
from ParticleEngine.camera import FirstPersonCamera        # noqa: E402


def worst_case_buffer(n: int) -> np.ndarray:
    """n grains in a thin slab, every normal +y: all face the camera AND the light."""
    rng = np.random.default_rng(11)
    b = matter.blank(n)
    b[:, matter.PX] = rng.uniform(-1.0, 1.0, n)
    b[:, matter.PY] = rng.uniform(-0.05, 0.05, n)
    b[:, matter.PZ] = rng.uniform(-1.0, 1.0, n)
    b[:, matter.NY] = 1.0
    matter.paint(b, (0.2, 0.2, 0.2), 1.0, 0.01, matter.SOLID)
    matter.paint_specular(b, 0.02149, 0.1233)          # aSaltOcean's own derived numbers
    return b


def measure(n: int, pairs: int = 24, warmup: int = 6, term: str = "specular"):
    """Interleaved A/B for one optics term. term='specular' toggles set_light;
    term='refraction' toggles set_refraction (worst case: every grain is an interface)."""
    buf = worst_case_buffer(n)
    cam = FirstPersonCamera(position=(0.0, -2.5, 0.0), yaw=np.pi / 2, pitch=0.0)
    prm = cam.params(width=640, height=480)
    light = ((0.0, 1.0, 0.15), (1.0, 0.97, 0.92))

    pipe = gp.FullGPUPipeline()
    if term == "refraction":
        from ChimeraEngine.core import optics
        buf[:, matter.REFRACT] = 1.0
        floor = matter.blank(96 * 96)
        f = np.linspace(-1.2, 1.2, 96)
        fx, fy = np.meshgrid(f, f)
        floor[:, matter.PX] = fx.ravel(); floor[:, matter.PY] = fy.ravel()
        floor[:, matter.CR] = 0.5; floor[:, matter.CG] = 0.4; floor[:, matter.CB] = 0.3
        origin, cell, grid_rgb, grid_has = optics.build_floor_grid(floor, float(f[1] - f[0]))
        eta = 1.0 / 1.3436
        arm_on = lambda: pipe.set_refraction((eta, eta, eta), -1.0, (0.32, 0.06, 0.0145),
                                             origin, cell, grid_rgb, grid_has)
        arm_off = lambda: pipe.set_refraction(None)
    else:
        arm_on = lambda: pipe.set_light(*light)
        arm_off = lambda: pipe.set_light(None)
    pipe.upload(buf)

    for _ in range(warmup):                       # JIT + allocator + cache warm, both arms
        arm_off(); pipe.render_from_gpu(cam, prm)
        arm_on(); pipe.render_from_gpu(cam, prm)

    off = np.empty(pairs); on = np.empty(pairs)
    for k in range(pairs):                        # interleaved: A B A B ...
        arm_off()
        t0 = time.perf_counter(); pipe.render_from_gpu(cam, prm); off[k] = time.perf_counter() - t0
        arm_on()
        t0 = time.perf_counter(); pipe.render_from_gpu(cam, prm); on[k] = time.perf_counter() - t0

    d = (on - off) * 1000.0
    return dict(n=n, off_ms=float(off.mean() * 1000), off_sd=float(off.std() * 1000),
                on_ms=float(on.mean() * 1000), on_sd=float(on.std() * 1000),
                delta_ms=float(d.mean()), delta_sd=float(d.std()),
                sem=float(d.std() / np.sqrt(pairs)))


def main() -> int:
    import sys as _sys
    term = "refraction" if "--refraction" in _sys.argv else "specular"
    print(f"[{term}]")
    print(f"{'N grains':>10} {'off ms':>10} {'on ms':>10} {'delta ms':>10} {'±sem':>8}   verdict")
    rows = []
    for n in (4096, 65536, 262144):
        r = measure(n, term=term)
        rows.append(r)
        clears = abs(r["delta_ms"]) > 2.0 * r["sem"]
        verdict = "MEASURABLE" if clears else "below noise"
        print(f"{r['n']:>10,} {r['off_ms']:>10.3f} {r['on_ms']:>10.3f} "
              f"{r['delta_ms']:>+10.4f} {r['sem']:>8.4f}   {verdict}", flush=True)

    big = rows[-1]
    if abs(big["delta_ms"]) > 2.0 * big["sem"] and big["delta_ms"] > 0:
        slope = big["delta_ms"] / big["n"]
        print(f"\nMS_PER_LIT_GRAIN = {slope:.3e}  (fit at N={big['n']:,}; wire into perf_guard)")
    else:
        bound = (2.0 * big["sem"]) / big["n"]
        print(f"\nThe {term} term DOES NOT CLEAR THE NOISE at N={big['n']:,}: "
              f"delta {big['delta_ms']:+.4f} ± {big['sem']:.4f} ms.")
        print(f"Honest record: MS_PER_LIT_GRAIN <= {bound:.3e} ms/grain (2-sigma upper bound).")
        print("Per the pre-stated rule: the light term is NOT the binding constraint; "
              "no guard check is added -- it would be decorative.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
