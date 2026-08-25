"""gate_octree_njit.py -- T13 Phase B' step B1 gate (Rule-0 membrane, THE_TRIANGLE_CARRIER §PHASE B').

De-Pythoned single-njit octree build (LightEngine.bh_octree_njit.build_octree_njit) vs the
bit-exact referee (LightEngine.bh_draw.build_octree) on TWO named scenes.

PREDICTION  BYTE-IDENTICAL: all 12 output keys agree in value + dtype + shape on BOTH scenes
            (same partition, same FIFO BFS cell order, same com/mass -- by construction).
            Serial build wall-time drops well under the referee's ~2405 ms T4 number, because
            B1 removes per-cell Python orchestration (numba dispatch + list appends), NOT the
            root partition (~18 ms) or com-mass (~8 ms).
FALSIFIER  any key mismatch (value/dtype/shape) on either scene; a non-finite output; an
            exception in the njit build; or the njit median build not strictly faster than the
            referee's median (B1 would then be a no-op, like v1 mt -- recorded honestly).

Scenes: EXACTLY the loaders of tools/gate_octree_sfc.py (_load_cad_bear, _load_t4_million) --
reused, not re-derived. Timing: 1 warm-up rep per builder (triggers numba JIT), then median
over REPS measured reps; perf_counter ms.

Usage:  C:/Python314/python -m tools.gate_octree_njit        (CPU only; no GPU needed)
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
from LightEngine.bh_octree_njit import build_octree_njit  # noqa: E402
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
    """1 warm-up rep (JIT compile excluded), then median of REPS measured reps, ms."""
    builder(pos, leaf_size=LEAF)                       # warm-up: triggers numba JIT
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
    ms_ref = _median_build_ms(build_octree, pos)      # includes one more ref build inside warm-up
    ms_njit = _median_build_ms(build_octree_njit, pos)
    t_njit = build_octree_njit(pos, leaf_size=LEAF)

    ok_id, bad = _byte_identical(t_ref, t_njit)
    finite = bool(np.all(np.isfinite(t_njit["cell_min"])) and np.all(np.isfinite(t_njit["cell_com"])))
    ok_perf = ms_njit < ms_ref
    print(f"  ref n_cells={t_ref['n_cells']:,}   njit n_cells={t_njit['n_cells']:,}")
    print(f"  byte-identity: {'PASS' if ok_id else 'MISMATCH ' + str(bad)}   finite={finite}")
    print(f"  build median ms: ref={ms_ref:.1f}   njit={ms_njit:.1f}   "
          f"(drop {ms_ref - ms_njit:.1f} ms, {ms_njit / ms_ref * 100:.1f}% of referee)")
    return dict(name=name, n=n, ok_byte_identity=bool(ok_id), mismatched=bad, finite=finite,
                n_cells=int(t_ref["n_cells"]), build_ms=dict(ref=round(ms_ref, 2), njit=round(ms_njit, 2)),
                ok_perf_strictly_faster=bool(ok_perf))


def main() -> int:
    print("T13 PHASE B' B1 GATE -- single-njit de-Pythoned octree build vs referee (byte-identity)")

    def _safe(name, loader):
        try:
            return _gate_scene(name, loader())
        except Exception as e:  # a crash is itself the falsifier; keep both scenes reporting
            import traceback
            print(f"\n=== {name}  EXC ===")
            traceback.print_exc()
            return dict(name=name, n=-1, ok_byte_identity=False, mismatched=["exception"],
                        finite=False, exception=repr(e), ok_perf_strictly_faster=False)

    r_bear = _safe("cad_bear", _load_cad_bear)
    r_t4 = _safe("T4-1M (THE_MILLION uniform)", _load_t4_million)

    pass_all = bool(r_bear["ok_byte_identity"] and r_bear["finite"] and r_bear["ok_perf_strictly_faster"]
                    and r_t4["ok_byte_identity"] and r_t4["finite"] and r_t4["ok_perf_strictly_faster"])
    print("\n" + "=" * 72)
    print(f"B1 GATE: {'PASS' if pass_all else 'FALSIFIER FIRES'}")

    out = ROOT / "agent_logs" / "gate_octree_njit.json"
    out.write_text(json.dumps(dict(leaf_size=LEAF, reps=REPS, cad_bear=r_bear, t4_million=r_t4,
                                   pass_all=bool(pass_all)), indent=1), encoding="utf8")
    print(f"  JSON: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
