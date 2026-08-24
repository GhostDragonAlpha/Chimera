"""envelope_million.py -- THE_MILLION frame-rate envelope, the pre-registered run.

`docs/THE_FIELD_ASSEMBLY.md`, section "THE MILLION — ENVELOPE PRE-REGISTERED":

    STATEMENT   one million conserved points/frame, both force passes over ONE tree
                walk; the frame-rate envelope has never been measured and must be
                before any build claims the budget.
    PREDICTION  method per `docs/MEASURED_RENDER_BUDGETS.md` convention: 12 frames,
                first two discarded as warm-up, mean +/- sigma of the remaining ten;
                both passes drawn at exactly 1,000,000 elements on the operator's
                RTX 4090. No fps is named here -- naming one would be a free
                parameter. The number to be printed by THIS run.
    FALSIFIER   measured ms/frame breaches MAX_RENDER_MS = 200 at 1M => THE_MILLION
                is not hardware-true; successor pre-named in the section (the LOD
                reallocation doctrine already written in THE_LIGHT_SEED).

SCENE (named before the run, derived not picked):
    positions uniform in [0, L)^3 with L = R_BOND * N^(1/3) -- the domain side that
    makes the mean inter-point distance equal to R_BOND, the bond equilibrium
    `constants.py` derives. The resistance law is therefore active across the field:
    this is the walk's honest load, not a sparse one somebody chose for the number.
    velocities zero (the envelope measures the walk; velocity only feeds the wall-
    damping arithmetic of identical cost). SEED = 7, the repo's recorded seed
    (`ChimeraEngine/million_needles.py`).

MEASURED QUANTITY: one `LightEngine.modifier.compute_forces_mod` call per frame --
ONE modified Barnes-Hut tree walk computing DRAW + RESISTANCE (the two force passes)
over ONE octree at exactly 1,000,000 elements, as delivered by the interface on the
GPU. The octree is built ONCE before frame 0 and reused: a real frame's positions
move, so a live rebuild is part of the true per-frame cost; it is printed as an
HONESTY LINE below (not named in the pre-registration, not judged by its falsifier).

Usage:
    python tools/envelope_million.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402

N = 1_000_000          # THE_MILLION -- exactly one million conserved points/frame
FRAMES = 12            # MEASURED_RENDER_BUDGETS convention
WARMUP = 2             # first two discarded (JIT compile + allocation warm-up)
SEED = 7               # the repo's recorded seed

from LightEngine import constants as C        # noqa: E402
from LightEngine.bh_draw import build_octree, DEFAULT_THETA   # noqa: E402
from LightEngine.modifier import compute_forces_mod           # noqa: E402

L = float(C.R_BOND) * N ** (1.0 / 3.0)      # derived scene side, see module docstring


def main() -> int:
    from ChimeraEngine.perf_guard import MAX_RENDER_MS   # the declared wall, single source

    rng = np.random.default_rng(SEED)
    pos = rng.uniform(0.0, L, (N, 3)).astype(np.float32)
    vel = np.zeros((N, 3), dtype=np.float32)

    print(f"THE_MILLION ENVELOPE -- exactly {N:,} elements, one modified tree walk")
    print(f"  scene: uniform [0,{L:g})^3 (mean inter-point distance = R_BOND by derivation)")
    print(f"  theta={DEFAULT_THETA} leaf_size=16 seed={SEED}   "
          f"constants: G={C.G} EPS={C.EPS} R_WALL={C.R_WALL} R_C={C.R_C}")
    print(f"  method: {FRAMES} frames, first {WARMUP} discarded, mean+/-sigma of the remaining "
          f"{FRAMES - WARMUP}; wall MAX_RENDER_MS={MAX_RENDER_MS}")
    print("-" * 78)

    t0 = time.perf_counter()
    tree = build_octree(pos, leaf_size=16)
    t_build = (time.perf_counter() - t0) * 1e3
    n_cells = int(tree["n_cells"])
    print(f"  octree built: {n_cells:,} cells in {t_build:.1f} ms "
          f"(HONESTY LINE -- a live frame's tree moves with its points; not judged here)")

    # The walk, exactly as delivered by the interface (GPU kernel + bookkeeping).
    for _ in range(2):
        compute_forces_mod(pos, vel, tree=tree)   # warm-up calls also JIT-compile

    ms = []
    power_last = 0.0
    for k in range(FRAMES - WARMUP):
        t1 = time.perf_counter()
        acc, power_last = compute_forces_mod(pos, vel, tree=tree)
        ms.append((time.perf_counter() - t1) * 1e3)
        print(f"  frame {k + 1}: {ms[-1]:8.2f} ms   (radiated wall power "
              f"{power_last:.4g})")

    mean = float(np.mean(ms))
    sd = float(np.std(ms))
    worst = max(ms)
    fps_mean = 1000.0 / mean
    breach = mean > MAX_RENDER_MS

    print("-" * 78)
    print(f"  ENVELOPE: mean {mean:.2f} ms/frame +/- {sd:.2f}, worst {worst:.2f} "
          f"(~{fps_mean:.1f} fps at the mean)")
    print(f"  FALSIFIER (breach of MAX_RENDER_MS={MAX_RENDER_MS} at 1M): "
          + ("FIRES -- THE_MILLION is not hardware-true as walked; the pre-named "
             "successor is the LOD reallocation doctrine in THE_LIGHT_SEED."
             if breach else
             f"does not fire -- {mean:.2f} ms <= wall {MAX_RENDER_MS} ms at exactly 1M. "
             "THE_MILLION stands hardware-true for this walk and scene; no fps was "
             "named, only the printed mean."))

    # Finiteness of the delivered accelerations: the walk must not leak NaN.
    finite = bool(np.all(np.isfinite(acc)))
    print(f"  finiteness of delivered accelerations: {'HOLDS' if finite else 'BROKEN'}")

    out = ROOT / "agent_logs" / "envelope_million.json"
    out.write_text(json.dumps(dict(
        n=N, frames=FRAMES, warmup=WARMUP, seed=SEED, theta=DEFAULT_THETA,
        leaf_size=16, scene=f"uniform [0,{L:g})^3 (mean inter-point dist = R_BOND)",
        max_render_ms_wall=MAX_RENDER_MS, n_cells=n_cells, tree_build_ms=t_build,
        ms_frames=[float(v) for v in ms], mean_ms=mean, sigma_ms=sd, worst_ms=worst,
        fps_at_mean=fps_mean, falsifier_breach=bool(breach), finite=finite,
        wall_power_last=float(power_last)), indent=1), encoding="utf8")
    print(f"  JSON: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
