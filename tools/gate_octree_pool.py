"""gate_octree_pool.py -- T13 persistent buffer pool gate (Rule-0 membrane, THE_TRIANGLE_CARRIER §PERSISTENT BUFFER POOL).

Pooled path of LightEngine.bh_octree_njit.build_octree_njit(..., pool=OctreePool()) vs the
bit-exact referee (LightEngine.bh_draw.build_octree) on TWO named scenes, ONE shared pool
across both (exercises ensure-grow + re-fill: bear first, then T4-1M).

PREDICTION  BYTE-IDENTICAL: all 12 output keys agree in value + dtype + shape on BOTH scenes.
            Pooled build wall-time drops the measured wrapper remainder (~36.7 ms): T4-1M
            fresh-njit ~138.1 -> pooled ~101 ms (re-fill, not re-alloc).
FALSIFIER  any key mismatch (value/dtype/shape) on either scene; a non-finite output; an
            exception in the pooled build; or no meaningful wall-time drop (pooled median
            within 5% of fresh-njit median -- the pool would then be a no-op).

Scenes: EXACTLY the loaders of tools/gate_octree_sfc.py (_load_cad_bear, _load_t4_million) --
reused, not re-derived. Timing: 1 warm-up rep per builder (triggers numba JIT), then median
over REPS measured reps; perf_counter ms.

Usage:  C:/Python314/python -m tools.gate_octree_pool        (CPU only; no GPU needed)
"""
from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402

from LightEngine.bh_draw import build_octree  # noqa: E402
from LightEngine.bh_octree_njit import OctreePool, build_octree_njit  # noqa: E402
from tools.gate_octree_sfc import _load_cad_bear, _load_t4_million  # noqa: E402

LEAF = 16
REPS = 5            # measured reps after warm-up (median)
KEYS = ("cell_min", "cell_max", "cell_com", "cell_mass", "cell_child", "cell_is_leaf",
        "cell_leaf_start", "cell_leaf_count", "sorted_pos", "sorted_idx", "order")


def _byte_identical(a: dict, b: dict) -> tuple[bool, list]:
    """All keys agree in value + dtype + shape; n_cells as plain int."""
    bad = []
    if a["n_cells"] != b["n_cells"]:
        bad.append(f"n_cells {a['n_cells']} != {b['n_cells']}")
    for k in KEYS:
        da, db = np.asarray(a[k]), np.asarray(b[k])
        if da.dtype != db.dtype or da.shape != db.shape or not bool(np.array_equal(da, db)):
            bad.append(k)
    return (len(bad) == 0), bad


def _median_build_ms(builder, pos: np.ndarray) -> float:
    """1 warm-up rep (JIT compile excluded), then median of REPS measured reps, ms.

    ``builder`` takes ONLY pos (leaf_size already bound by the caller's lambda)."""
    builder(pos)                                      # warm-up: triggers numba JIT
    ts = []
    for _ in range(REPS):
        t0 = time.perf_counter()
        builder(pos)
        ts.append((time.perf_counter() - t0) * 1e3)
    return float(statistics.median(ts))


def _gate_scene(name: str, pos: np.ndarray, pool: OctreePool) -> dict:
    n = int(pos.shape[0])
    print(f"\n=== {name}  (N={n:,}) ===")

    t_ref = build_octree(pos, leaf_size=LEAF)         # referee output kept for identity check
    ms_fresh = _median_build_ms(lambda p: build_octree_njit(p, leaf_size=LEAF), pos)
    ms_pooled = _median_build_ms(lambda p: build_octree_njit(p, leaf_size=LEAF, pool=pool), pos)
    t_pooled = build_octree_njit(pos, leaf_size=LEAF, pool=pool)   # final build; views valid now

    ok_id, bad = _byte_identical(t_ref, t_pooled)     # compare IMMEDIATELY (contract hazard)
    finite = bool(np.all(np.isfinite(t_pooled["cell_min"])) and np.all(np.isfinite(t_pooled["cell_com"])))
    ok_perf = ms_pooled < 0.95 * ms_fresh            # meaningful drop, not a no-op
    print(f"  ref n_cells={t_ref['n_cells']:,}   pooled n_cells={t_pooled['n_cells']:,}")
    print(f"  byte-identity: {'PASS' if ok_id else 'MISMATCH ' + str(bad)}   finite={finite}")
    print(f"  build median ms: fresh-njit={ms_fresh:.1f}   pooled={ms_pooled:.1f}   "
          f"(drop {ms_fresh - ms_pooled:.1f} ms, {ms_pooled / max(ms_fresh, 1e-9) * 100:.1f}% of fresh)")
    return dict(name=name, n=n, ok_byte_identity=bool(ok_id), mismatched=bad, finite=finite,
                n_cells=int(t_ref["n_cells"]),
                build_ms=dict(fresh_njit=round(ms_fresh, 2), pooled=round(ms_pooled, 2)),
                ok_perf_meaningful_drop=bool(ok_perf))


def main() -> int:
    print("T13 PERSISTENT BUFFER POOL GATE -- pooled build vs referee (byte-identity + wrapper kill)")
    pool = OctreePool()                                # ONE shared pool across both scenes

    def _safe(name, loader):
        try:
            return _gate_scene(name, loader(), pool)
        except Exception as e:  # a crash is itself the falsifier; keep both scenes reporting
            import traceback
            print(f"\n=== {name}  EXC ===")
            traceback.print_exc()
            return dict(name=name, n=-1, ok_byte_identity=False, mismatched=["exception"],
                        finite=False, exception=repr(e), ok_perf_meaningful_drop=False)

    r_bear = _safe("cad_bear", _load_cad_bear)
    r_t4 = _safe("T4-1M (THE_MILLION uniform)", _load_t4_million)

    pass_all = bool(r_bear["ok_byte_identity"] and r_bear["finite"] and r_bear["ok_perf_meaningful_drop"]
                    and r_t4["ok_byte_identity"] and r_t4["finite"] and r_t4["ok_perf_meaningful_drop"])
    print("\n" + "=" * 72)
    print(f"POOL GATE: {'PASS' if pass_all else 'FALSIFIER FIRES'}")

    out = ROOT / "agent_logs" / "gate_octree_pool.json"
    out.write_text(json.dumps(dict(leaf_size=LEAF, reps=REPS, cad_bear=r_bear, t4_million=r_t4,
                                   pass_all=bool(pass_all)), indent=1), encoding="utf8")
    print(f"  JSON: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
