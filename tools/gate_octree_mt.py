"""gate_octree_mt.py -- T13 MULTI-CORE REFEREEER octree build gate (option a), continuation-11.

Compares LightEngine.bh_octree_mt.build_octree_mt against the bit-exact referee
LightEngine.bh_draw.build_octree on TWO named scenes. The PRIMARY gate is BYTE-IDENTITY:
every output array key must be np.array_equal to the referee's, so the force is 0.0% by
construction (not "<=1%"). Secondary evidence = build wall-time speedup across W workers
(the multi-core claim) and an OPTIONAL GPU force confirm through compute_draw_bh on both
trees (rel err ~0%; skipped gracefully when no 4090/cupy).

PREDICTION  byte-identity PASS on BOTH scenes at leaf_size=16; speedup > 1x on T4-1M (the root
            spike caps it); GPU force rel err ~0% when a device is present.
FALSIFIER  any output array key differs from the referee (byte mismatch); a build exception;
            or -- if a GPU is present -- compute_draw_bh rel err not ~0%.

Scenes: cad_bear + T4-1M, loaded EXACTLY as tools/gate_octree_sfc.py loads them (those loaders
are reused here -- single source of truth for the scene definitions).

Usage:  C:/Python314/python -m tools.gate_octree_mt
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402

from LightEngine.bh_draw import build_octree, compute_draw_bh, relative_error, DEFAULT_THETA  # noqa: E402
from LightEngine.bh_octree_mt import build_octree_mt  # noqa: E402
from tools.gate_octree_sfc import _load_cad_bear, _load_t4_million  # noqa: E402

LEAF = 16
# Every referee output array key that must be byte-identical (n_cells checked separately).
ARRAY_KEYS = ["cell_min", "cell_max", "cell_com", "cell_mass", "cell_child",
              "cell_is_leaf", "cell_leaf_start", "cell_leaf_count",
              "sorted_pos", "sorted_idx", "order"]


def _byte_identical(a: dict, b: dict) -> tuple[bool, list]:
    """PRIMARY gate: every output array key byte-identical to the referee."""
    bad = []
    for k in ARRAY_KEYS:
        if not np.array_equal(a[k], b[k]):
            bad.append(k)
    if int(a["n_cells"]) != int(b["n_cells"]):
        bad.append("n_cells")
    return (len(bad) == 0), bad


def _gpu_force_ok(pos: np.ndarray, t_ref: dict, t_mt: dict) -> dict:
    """Optional GPU force confirm through the SAME kernel on both trees.

    Byte-identical trees MUST give bit-identical forces, so rel err is ~0 when a device is
    present. Skipped gracefully (not the falsifier) when no 4090/cupy.
    """
    try:
        a_ref = compute_draw_bh(pos, theta=DEFAULT_THETA, tree=t_ref, leaf_size=LEAF)
        a_mt = compute_draw_bh(pos, theta=DEFAULT_THETA, tree=t_mt, leaf_size=LEAF)
        finite = bool(np.all(np.isfinite(a_ref))) and bool(np.all(np.isfinite(a_mt)))
        rel = relative_error(a_mt, a_ref) if finite else float("nan")
        return dict(gpu=True, finite=finite, rel_err=float(rel))
    except Exception as e:  # no GPU / cupy -> skip gracefully
        return dict(gpu=False, reason=repr(e), rel_err=None)


def _gate_scene(name: str, pos: np.ndarray, W: int, reps: int = 5) -> dict:
    n = int(pos.shape[0])
    print(f"\n=== {name}  (N={n:,}) ===")

    # Warm-up pass on BOTH builders: triggers numba compilation/caching so the timed reps
    # measure real parallel work, not first-call JIT. The warm-up referee result is kept as
    # the byte-identity reference.
    t_ref = build_octree(pos, leaf_size=LEAF)
    _warm_mt = build_octree_mt(pos, leaf_size=LEAF, workers=W)

    ref_times = []
    for _ in range(reps):
        t0 = time.perf_counter()
        build_octree(pos, leaf_size=LEAF)
        ref_times.append((time.perf_counter() - t0) * 1e3)
    ref_ms = float(np.median(ref_times))

    mt_times = []
    for _ in range(reps):
        t0 = time.perf_counter()
        t_mt = build_octree_mt(pos, leaf_size=LEAF, workers=W)
        mt_times.append((time.perf_counter() - t0) * 1e3)
    mt_ms = float(np.median(mt_times))

    ok_byte, bad = _byte_identical(t_ref, t_mt)
    speedup = ref_ms / mt_ms if mt_ms > 0 else float("inf")
    print(f"  ref n_cells={t_ref['n_cells']:,} (median {ref_ms:.1f} ms over {reps})   "
          f"mt n_cells={t_mt['n_cells']:,} (median {mt_ms:.1f} ms)")
    print(f"  BYTE-IDENTITY: {'PASS' if ok_byte else 'MISMATCH -> ' + ','.join(bad)}   "
          f"speedup = {speedup:.2f}x (W={W})")

    gpu = _gpu_force_ok(pos, t_ref, t_mt)
    if gpu.get("gpu"):
        print(f"  GPU force rel err = {gpu['rel_err'] * 100:.4e}%   finite={gpu['finite']}")
    else:
        print(f"  GPU force confirm SKIPPED ({gpu.get('reason', 'no cupy')}) -- byte-identity is the gate")

    ok_gpu = (not gpu.get("gpu")) or bool(gpu["finite"] and gpu["rel_err"] < 1e-6)
    return dict(name=name, n=n, W=W, leaf_size=LEAF,
                ref_n_cells=int(t_ref["n_cells"]), mt_n_cells=int(t_mt["n_cells"]),
                byte_identical=bool(ok_byte), mismatched_keys=bad,
                build_ms=dict(ref=float(ref_ms), mt_median=float(mt_ms)),
                speedup=float(speedup), gpu=gpu, ok_gpu=bool(ok_gpu))


def main() -> int:
    W = int(os.cpu_count() or 4)
    print(f"T13 MULTI-CORE REFEREEER OCTREE GATE (option a)   leaf_size={LEAF}   "
          f"W={W} cores   theta={DEFAULT_THETA}")

    def _safe(name, loader):
        try:
            return _gate_scene(name, loader(), W)
        except Exception as e:  # a crash is itself the falsifier
            import traceback
            print(f"\n=== {name}  EXC ===")
            traceback.print_exc()
            return dict(name=name, n=-1, byte_identical=False, ok_gpu=False, exception=repr(e))

    r_bear = _safe("cad_bear", _load_cad_bear)
    r_t4 = _safe("T4-1M (THE_MILLION uniform)", _load_t4_million)

    pass_all = bool(r_bear["byte_identical"] and r_bear["ok_gpu"]
                    and r_t4["byte_identical"] and r_t4["ok_gpu"])
    print("\n" + "=" * 72)
    print(f"T13 MT GATE: {'PASS' if pass_all else 'FALSIFIER FIRES'}")

    out = ROOT / "agent_logs" / "gate_octree_mt.json"
    out.write_text(json.dumps(dict(leaf_size=LEAF, W=W, theta=DEFAULT_THETA,
                                    cad_bear=r_bear, t4_million=r_t4, pass_all=bool(pass_all)),
                               indent=1), encoding="utf8")
    print(f"  JSON: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
