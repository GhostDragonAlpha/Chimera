"""gate_octree_sfc.py -- T13 SFC octree gate (Rule-0 membrane, THE_TRIANGLE_CARRIER §PARALLEL OCTREE).

Compares the multi-threaded/GPU SFC build (LightEngine.bh_sfc.build_octree_sfc) against the
bit-exact referee (LightEngine.bh_draw.build_octree) on TWO named scenes. Both trees are fed
through the SAME compute_draw_bh kernel, so only the TREE differs -- this isolates whether the
SFC tree is a valid octree that approximates the direct sum like the referee does.

PREDICTION  per-point forces agree <= 1% rel (relative_error) on BOTH scenes at theta=0.3,
            leaf_size=16; structural invariants hold: no leaf > 16, child subset-of parent
            (nesting), and bottom-up COM/mass matches the stored values to float32 epsilon.
FALSIFIER  non-finite output / walk exception on either scene; a nesting violation; a
            COM/mass mismatch beyond f32 epsilon; or force rel diff > 1% on EITHER scene.

Scenes (named before the run, derived not picked):
  cad_bear : walk-space positions from tools.ca_triangle.build_lattice() -- the deduped Vg
             cast to float32 (scale0=1 for bear), exactly what the CA walk sees.
  T4-1M    : THE_MILLION uniform scene, EXACTLY as tools/envelope_million.py defines it:
             default_rng(7).uniform(0, L, (1e6,3)), L = R_BOND * N**(1/3), float32.

Usage:  C:/Python314/python -m tools.gate_octree_sfc        (needs the 4090 / cupy)
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402

from LightEngine.bh_draw import build_octree, compute_draw_bh, relative_error, DEFAULT_THETA  # noqa: E402
from LightEngine.bh_sfc import build_octree_sfc  # noqa: E402
from LightEngine import constants as C  # noqa: E402

LEAF = 16
REL_TOL = 0.01          # <= 1% rel force (membrane)
F32_EPS_REL = 1e-5      # float32 relative epsilon for COM/mass invariant


# ────────────────────────────────────────────────────────────────────────────────
def _load_cad_bear() -> np.ndarray:
    """Walk-space cad_bear positions, exactly what the CA walk sees (reuse build_lattice)."""
    from tools.ca_triangle import build_lattice
    Vg, Tg, A0, S, e_med, n_orig_verts, n_exact_merged = build_lattice()   # 7-tuple
    scale0 = 1.0                                                            # bear: no compression
    pos32 = np.ascontiguousarray(Vg * scale0, dtype=np.float32)             # what the walk sees
    return pos32


def _load_t4_million() -> np.ndarray:
    """THE_MILLION uniform scene, EXACTLY as tools/envelope_million.py defines it."""
    N = 1_000_000
    SEED = 7
    L = float(C.R_BOND) * N ** (1.0 / 3.0)
    rng = np.random.default_rng(SEED)
    return rng.uniform(0.0, L, (N, 3)).astype(np.float32)


# ────────────────────────────────────────────────────────────────────────────────
def _invariants(tree: dict, pos: np.ndarray) -> dict:
    """Structural invariants on an octree dict (referee format)."""
    n = int(pos.shape[0])
    is_leaf = tree["cell_is_leaf"] == 1
    leaf_count = tree["cell_leaf_count"]
    leaf_start = tree["cell_leaf_start"]
    child = tree["cell_child"]
    cmin, cmax = tree["cell_min"], tree["cell_max"]
    com, mass = tree["cell_com"], tree["cell_mass"]
    n_cells = int(tree["n_cells"])

    # (a) leaf-size: a leaf may exceed LEAF ONLY when its points are mutually coincident --
    #     exactly build_octree's own ``n_nonempty == 1`` guard. No octree can split identical
    #     points into <= LEAF leaves, so the refined invariant is: every oversized leaf must be
    #     a coincident cluster (all its points identical). A non-coincident oversized leaf = violation.
    sp0 = tree["sorted_pos"]
    max_leaf = int(leaf_count[is_leaf].max()) if is_leaf.any() else 0
    n_oversized = 0; ok_leafsize = True
    for c in np.nonzero(is_leaf)[0]:
        m = int(leaf_count[c]); s = int(leaf_start[c])
        if m > LEAF:
            seg = sp0[s:s + m]
            coincident = bool((np.ptp(seg, axis=0).max() == 0.0))
            n_oversized += 1
            if not coincident:      # oversized but NOT a true coincidence -> real violation
                ok_leafsize = False

    # (b) partition: every point in exactly one leaf, ranges within [0,n)
    total_pts = int(leaf_count[is_leaf].sum())
    starts_ok = bool(np.all((leaf_start[is_leaf] >= 0) & (leaf_start[is_leaf] < n))) \
        and bool(np.all((leaf_start[is_leaf] + leaf_count[is_leaf]) <= n))
    ok_partition = (total_pts == n) and starts_ok

    # (c) root sanity: mass == N, com ~= mean(pos)
    root_mass_ok = abs(float(mass[0]) - n) < 1e-3 * max(1.0, n)
    root_com_err = float(np.linalg.norm(com[0] - pos.mean(axis=0))) / (float(np.abs(pos).max()) + 1e-30)

    # (d) nesting: each internal node's bbox contains all its children's bboxes
    tol = 1e-5 * (float(np.ptp(cmin)) + 1e-30)
    nest_ok = True
    for c in range(n_cells):
        if is_leaf[c]:
            continue
        kids = child[c]
        valid = kids >= 0
        if not valid.any():
            continue
        k = kids[valid].astype(np.int64)
        if (cmin[k].min(axis=0) < cmin[c] - tol).any() or \
           (cmax[k].max(axis=0) > cmax[c] + tol).any():
            nest_ok = False
            break

    # (e) COM/mass bottom-up recompute == stored, to f32 epsilon
    com_r = np.zeros((n_cells, 3), dtype=np.float64)
    mass_r = np.zeros(n_cells, dtype=np.float64)
    sp = tree["sorted_pos"]
    for c in range(n_cells - 1, -1, -1):
        if is_leaf[c]:
            s, m = int(leaf_start[c]), int(leaf_count[c])
            if m > 0:
                seg = sp[s:s + m]
                mass_r[c] = m
                com_r[c] = seg.mean(axis=0)
        else:
            kids = child[c]; valid = kids >= 0; k = kids[valid].astype(np.int64)
            w = mass_r[k]; sx = (w[:, None] * com_r[k]).sum(0); tot = w.sum()
            if tot > 0:
                com_r[c] = sx / tot; mass_r[c] = tot
    dm = np.abs(mass_r - mass)
    dcom = np.linalg.norm(com_r - com, axis=1) / (np.abs(com).max(axis=1) + 1e-30)
    ok_commass = bool(dm.max() <= F32_EPS_REL * max(1.0, n)) and bool(dcom.max() <= F32_EPS_REL)

    return dict(max_leaf=max_leaf, n_oversized=n_oversized, ok_leafsize=bool(ok_leafsize),
                total_pts=total_pts, ok_partition=bool(ok_partition), root_mass_ok=bool(root_mass_ok),
                root_com_err=root_com_err, nesting_ok=bool(nest_ok), com_mass_ok=bool(ok_commass))


# ────────────────────────────────────────────────────────────────────────────────
def _gate_scene(name: str, pos: np.ndarray) -> dict:
    n = int(pos.shape[0])
    print(f"\n=== {name}  (N={n:,}) ===")

    t0 = time.perf_counter()
    t_ref = build_octree(pos, leaf_size=LEAF)
    tb_ref = (time.perf_counter() - t0) * 1e3
    t0 = time.perf_counter()
    t_sfc = build_octree_sfc(pos, leaf_size=LEAF)
    tb_sfc = (time.perf_counter() - t0) * 1e3
    print(f"  ref n_cells={t_ref['n_cells']:,} ({tb_ref:.1f} ms)   "
          f"sfc n_cells={t_sfc['n_cells']:,} ({tb_sfc:.1f} ms)")

    # Forces through the SAME kernel; only the tree differs.
    # Referee's OWN max leaf: documents that even build_octree makes oversized coincident
    # leaves here (its n_nonempty==1 guard) -- so "no leaf > 16" is unsatisfiable by ANY tree.
    ref_max_leaf = int(t_ref["cell_leaf_count"][t_ref["cell_is_leaf"] == 1].max()) if bool((t_ref["cell_is_leaf"] == 1).any()) else 0

    a_ref = compute_draw_bh(pos, theta=DEFAULT_THETA, tree=t_ref, leaf_size=LEAF)
    a_sfc = compute_draw_bh(pos, theta=DEFAULT_THETA, tree=t_sfc, leaf_size=LEAF)
    finite = bool(np.all(np.isfinite(a_sfc))) and bool(np.all(np.isfinite(a_ref)))
    rel = relative_error(a_sfc, a_ref)

    inv = _invariants(t_sfc, pos)
    ok_force = finite and (rel <= REL_TOL)
    ok_inv = all([inv["ok_leafsize"], inv["ok_partition"], inv["root_mass_ok"],
                  inv["nesting_ok"], inv["com_mass_ok"]])

    print(f"  force rel err = {rel*100:.4f}%   finite={finite}   gate(<=1%)={'PASS' if ok_force else 'FAIL'}")
    print(f"  invariants: leaf max sfc={inv['max_leaf']} ref={ref_max_leaf} ({'ok' if inv['ok_leafsize'] else 'VIOLATION'}) "
          f"partition={inv['total_pts']}/{n} ({'ok' if inv['ok_partition'] else 'BAD'}) "
          f"root_mass={'ok' if inv['root_mass_ok'] else 'BAD'}")
    print(f"             nesting(child-in-parent)={'ok' if inv['nesting_ok'] else 'VIOLATION'}   "
          f"com/mass f32eps={'ok' if inv['com_mass_ok'] else 'MISMATCH'}")
    return dict(name=name, n=n, rel_err=rel, finite=finite, ok_force=bool(ok_force),
                ref_n_cells=int(t_ref["n_cells"]), sfc_n_cells=int(t_sfc["n_cells"]),
                ref_max_leaf=ref_max_leaf,
                build_ms=dict(ref=tb_ref, sfc=tb_sfc), invariants=inv, ok_invariants=bool(ok_inv))


def main() -> int:
    print(f"T13 SFC OCTREE GATE   theta={DEFAULT_THETA} leaf_size={LEAF}   "
          f"constants G={C.G} EPS={C.EPS}")

    def _safe(name, loader):
        try:
            return _gate_scene(name, loader())
        except Exception as e:  # keep both scenes reporting; a crash is itself the falsifier
            import traceback
            print(f"\n=== {name}  EXC ===")
            traceback.print_exc()
            return dict(name=name, n=-1, rel_err=float("nan"), finite=False,
                        ok_force=False, ok_invariants=False, exception=repr(e))

    r_bear = _safe("cad_bear", _load_cad_bear)
    r_t4 = _safe("T4-1M (THE_MILLION uniform)", _load_t4_million)

    pass_all = bool(r_bear["ok_force"] and r_bear["ok_invariants"]
                    and r_t4["ok_force"] and r_t4["ok_invariants"])
    print("\n" + "=" * 72)
    print(f"T13 GATE: {'PASS' if pass_all else 'FALSIFIER FIRES'}")
    if not pass_all:
        for r in (r_bear, r_t4):
            if not (r["ok_force"] and r["ok_invariants"]):
                print(f"  - {r['name']}: force_ok={r['ok_force']} inv_ok={r['ok_invariants']} "
                      f"rel={r['rel_err']*100:.3f}%")

    out = ROOT / "agent_logs" / "gate_octree_sfc.json"
    out.write_text(json.dumps(dict(theta=DEFAULT_THETA, leaf_size=LEAF, rel_tol=REL_TOL,
                                    cad_bear=r_bear, t4_million=r_t4, pass_all=bool(pass_all)),
                               indent=1), encoding="utf8")
    print(f"  JSON: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
