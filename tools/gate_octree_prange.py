"""gate_octree_prange.py -- T13 Phase B' step B2 (candidate A) gate, Rule-0 membrane.

Level-synchronous prange build (LightEngine.bh_octree_prange.build_octree_prange) vs the
bit-exact referee (LightEngine.bh_draw.build_octree) on TWO named scenes.

PREDICTION  BYTE-IDENTICAL: all 12 output keys agree in value + dtype + shape on BOTH scenes
            (induction: FIFO BFS == level order; children in parent-id x code order = the
            prefix-sum id merge). Speedup vs referee per §B2 PRE-REGISTERED ceiling ~3.1x on
            T4-1M (partition 98.2 ms is ~71% of the 138.1 ms floor; prange efficiency < 100%).
FALSIFIER  any key mismatch (value/dtype/shape) on either scene; non-finite output; an
            exception in the prange build; OR speedup ~= 1x again ("still one core").

Scenes: EXACTLY the loaders of tools/gate_octree_sfc.py (_load_cad_bear, _load_t4_million).
Timing: 1 warm-up rep per builder (triggers numba JIT + thread-layer init), then median over
REPS measured reps; perf_counter ms. NUMBA_NUM_THREADS=24 set BEFORE numba import (the box's
own cores, per §13 threading log -- not a picked parameter).

Usage:  C:/Python314/python -m tools.gate_octree_prange        (CPU only)
"""
from __future__ import annotations

import json
import os
import statistics
import sys
import time
from pathlib import Path

os.environ.setdefault("NUMBA_NUM_THREADS", "24")   # before numba import (thread-layer init)

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402

from LightEngine.bh_draw import build_octree  # noqa: E402
from LightEngine.bh_octree_prange import build_octree_prange  # noqa: E402
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
    """1 warm-up rep (JIT compile + thread-layer init excluded), then median of REPS reps."""
    builder(pos, leaf_size=LEAF)
    ts = []
    for _ in range(REPS):
        t0 = time.perf_counter()
        builder(pos, leaf_size=LEAF)
        ts.append((time.perf_counter() - t0) * 1e3)
    return float(statistics.median(ts))


def _gate_scene(name: str, pos: np.ndarray) -> dict:
    n = int(pos.shape[0])
    print(f"\n=== {name}  (N={n:,}) ===")

    t_ref = build_octree(pos, leaf_size=LEAF)         # referee output kept for identity check
    ms_ref = _median_build_ms(build_octree, pos)
    ms_prange = _median_build_ms(build_octree_prange, pos)
    t_pr = build_octree_prange(pos, leaf_size=LEAF)

    ok_id, bad = _byte_identical(t_ref, t_pr)
    finite = bool(np.all(np.isfinite(t_pr["cell_min"])) and np.all(np.isfinite(t_pr["cell_com"])))
    speedup = ms_ref / ms_prange if ms_prange > 0 else float("inf")
    print(f"  ref n_cells={t_ref['n_cells']:,}   prange n_cells={t_pr['n_cells']:,}")
    print(f"  byte-identity: {'PASS' if ok_id else 'MISMATCH ' + str(bad)}   finite={finite}")
    print(f"  build median ms: ref={ms_ref:.1f}   prange={ms_prange:.1f}   speedup={speedup:.2f}x")
    return dict(name=name, n=n, ok_byte_identity=bool(ok_id), mismatched=bad, finite=finite,
                n_cells=int(t_ref["n_cells"]), build_ms=dict(ref=round(ms_ref, 2), prange=round(ms_prange, 2)),
                speedup=round(speedup, 3))


def main() -> int:
    print("T13 PHASE B' B2 (candidate A) GATE -- level-synchronous prange build vs referee")

    def _safe(name, loader):
        try:
            return _gate_scene(name, loader())
        except Exception as e:  # a crash is itself the falsifier; keep both scenes reporting
            import traceback
            print(f"\n=== {name}  EXC ===")
            traceback.print_exc()
            return dict(name=name, n=-1, ok_byte_identity=False, mismatched=["exception"],
                        finite=False, exception=repr(e), speedup=None)

    r_bear = _safe("cad_bear", _load_cad_bear)
    r_t4 = _safe("T4-1M (THE_MILLION uniform)", _load_t4_million)

    pass_all = bool(r_bear["ok_byte_identity"] and r_bear["finite"]
                    and r_t4["ok_byte_identity"] and r_t4["finite"])
    print("\n" + "=" * 72)
    print(f"B2 (A) GATE: {'PASS' if pass_all else 'FALSIFIER FIRES'}")

    out = ROOT / "agent_logs" / "gate_octree_prange.json"
    out.write_text(json.dumps(dict(leaf_size=LEAF, reps=REPS, numba_threads=os.environ.get("NUMBA_NUM_THREADS"),
                                   cad_bear=r_bear, t4_million=r_t4, pass_all=bool(pass_all)),
                              indent=1), encoding="utf8")
    print(f"  JSON: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
