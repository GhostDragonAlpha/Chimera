"""demo_sheet.py -- D1 material-response demo: the elastic sheet under a pinned shear.

Three phases (PREREGISTRATION.md D1, amended A4b):
    A. PINNED SHEAR  : left edge pinned at rest, right edge imposed +0.25 in y. Evaluate the
                       elastic internal force at the pinned pose. The net right-edge reaction
                       must OPPOSE the imposed displacement (sign asserted, magnitude reported).
    B. RELEASE       : the right edge is unpinned; gradient_descent minimizes the elastic energy
                       back toward the pinned rest shape. Assert final max|free displacement| <=
                       1e-4*L and U_final <= ALG * energy_scale, under the labeled optimizer
                       (outcome stationary/stagnated/failed/max_iter -- optimization steps, NOT
                       physical time).
    C. LAW CONTRAST  : on the phase-A pose, compare the elastic shear resistance (right-edge
                       vertex forces) against the constant-gamma area law's in-plane interior
                       forces (gamma = 1, exact grad-A formula, local implementation of the
                       reference law U = sum_t gamma*A_t). The pure-shear map has unit determinant,
                       so the area law is blind to it: assert elastic resistance / (gamma
                       interior force) >= 10. The two laws visibly disagree on the same pose.

Evidence: each run writes docs/evidence/elastic_foundation/demo_<UTC>[_<suffix>]/results.json +
demo_report.txt. Exit 0 iff every named number holds.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from . import geometry as G
from . import law as L
from . import materials as M
from . import optimizers as O
from . import run_falsify as RF

ALG = 512.0 * float(np.finfo(np.float64).eps)
EPS64 = float(np.finfo(np.float64).eps)

W, H = 2.0, 1.0
SHEAR_Y = 0.25
NX, NY = 8, 4
GAMMA = 1.0  # area-law coefficient, one common convention (gamma = energy/area)

IMPOSED = "+0.25 y"  # D1 (a)


def gamma_area_forces(pos, faces, gamma=GAMMA):
    """Constant-gamma area law forces (force ON vertex = -dU/dy, U = gamma * sum A_t).

    Exact analytic gradient of the unsigned triangle area w.r.t. its corners (the reference
    surface law's `evaluate_surface` force for the planar case; see
    docs/THE_SURFACE_ENERGY_TRANSLATION.md). For an in-plane map with unit determinant every
    interior vertex sees cancellation -> forces ~0 (that is the D1(c') contrast mechanism).
    """
    f = np.zeros_like(pos)
    d1 = pos[faces[:, 1]] - pos[faces[:, 0]]
    d2 = pos[faces[:, 2]] - pos[faces[:, 0]]
    n = np.cross(d1, d2)
    n = n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), np.finfo(np.float64).tiny)
    # dA/dy0 = +0.5*(y1 - y2) x n  (in faces of unit area-normal orientation)
    for v in range(3):
        a = (pos[faces[:, (v + 1) % 3]] - pos[faces[:, (v + 2) % 3]])
        g = 0.5 * np.cross(a, n)            # gradA at corner v (CCW orientation)
        np.add.at(f, faces[:, v], -gamma * g)
    return f, n


def phase_a(geom, material, y_shear, ev):
    """PINNED SHEAR -- reaction sign and magnitude at the imposed pose."""
    right = np.abs(geom.positions[:, 0] - W) < 1e-12
    react_y = float(np.sum(ev.vertex_forces[right, 1]))   # internal force is the reaction state
    opposes = react_y < 0.0                                 # imposed +y -> internal force pulls -y
    facts = {"imposed": IMPOSED,
             "right_edge_vertices": int(np.count_nonzero(right)),
             "net_internal_y_reaction": react_y,
             "opposes_imposed": bool(opposes),
             "energy": ev.energy,
             "max_abs_force": ev.max_abs_vertex_force}
    ok = opposes and abs(react_y) >= 1e-6  # any non-degenerate opposing reaction
    return ok, facts


def phase_b_react(geom, material, obj, x0_flat, fixed, fixed_flat, x_rest):
    """RELEASE -- relax the free (right-edge + interior) vertices from the sheared pose."""
    res = O.conjugate_gradient(obj, x0_flat, fixed_flat, max_iter=20000, grad_tol_rel=1e-12)
    xf = res.x.reshape(-1, 3)
    free_vert = ~fixed
    dev = np.linalg.norm(xf[free_vert] - x_rest[free_vert], axis=1)
    f_gamma_r, _ = gamma_area_forces(xf, geom.faces, GAMMA)
    gam_relax = float(np.max(np.abs(f_gamma_r[free_vert])))
    L = max(W, H)
    u_lim = ALG * material.stiffness_scale * geom.total_area0
    facts = {"outcome": res.outcome, "iters": res.iters, "accepted": res.accepted,
             "rejected_steps": res.rejected_steps, "final_grad_norm": res.final_grad_norm,
             "max_free_dev_from_rest": float(np.max(dev)),
             "dev_limit": 1e-4 * L,
             "energy_final": res.energy, "energy_limit": u_lim,
             "gamma_max_free_force_at_relax": gam_relax,
             "energy_scale": material.stiffness_scale * geom.total_area0}
    ok = res.outcome in ("stationary", "stagnated") and float(np.max(dev)) <= 1e-4 * L and \
        res.energy <= u_lim
    return ok, facts


def phase_c(geom, material, y_shear, ev):
    """LAW CONTRAST -- elastic shear resistance vs constant-gamma area force on the same pose."""
    f_gamma, _ = gamma_area_forces(y_shear, geom.faces, GAMMA)
    interior = (np.abs(y_shear[:, 0] - 0.5 * W) < 0.5 * W - 1e-9) & \
               (np.abs(y_shear[:, 1] - 0.5 * H) < 0.5 * H - 1e-9)
    right = np.abs(y_shear[:, 0] - W) < 1e-12
    el_resist = float(np.max(np.abs(ev.vertex_forces[right, 1])))
    gam_max_int = float(np.max(np.abs(f_gamma[interior])))
    facts = {"elastic_right_edge_shear_resistance": el_resist,
             "gamma_max_interior_force": gam_max_int,
             "interior_vertices": int(np.count_nonzero(interior)),
             "resistance_floor": 0.1,
             "gamma_blind_ceiling": 1e-12}
    ok = el_resist >= 0.1 and gam_max_int <= 1e-12
    return ok, facts


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="elastic-foundation D1 material-response demo")
    ap.add_argument("--suffix", default="", help="extra evidence tag suffix")
    args = ap.parse_args(argv)

    material = M.synthetic(E=1.0, nu=0.3, h=1.0)
    pos, faces = G.unit_make_grid(W, H, NX, NY)
    geom = G.build_rest_geometry(pos, faces, build_info={"units": "m", "kind": "demo_sheet"})

    # phase A pose: shear the right edge by +0.25 in y, everything else at rest.
    y_shear = np.array(pos, dtype=np.float64)
    y_shear[np.abs(y_shear[:, 0] - W) < 1e-12, 1] = pos[np.abs(pos[:, 0] - W) < 1e-12, 1] + SHEAR_Y
    ev = L.evaluate_elastic(geom, material, y_shear)

    okA, fA = phase_a(geom, material, y_shear, ev)

    # phase B: unpin the right edge, leave only the left (x=0) edge pinned at REST.
    fixed = np.abs(pos[:, 0]) < 1e-12
    fixed_flat = np.repeat(fixed, 3)
    x0_flat = np.array(y_shear, copy=True).reshape(-1)

    def obj(p):
        e = L.evaluate_elastic(geom, material, p.reshape(-1, 3))
        return e.energy, -e.vertex_forces.reshape(-1)

    okB, fB = phase_b_react(geom, material, obj, x0_flat, fixed, fixed_flat, geom.positions)

    okC, fC = phase_c(geom, material, y_shear, ev)

    ok_all = okA and okB and okC
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    tag = f"demo_{stamp}" + (f"_{args.suffix}" if args.suffix else "")
    out_dir = Path(__file__).resolve().parent.parent.parent / "docs" / "evidence" / \
        "elastic_foundation" / tag
    out_dir.mkdir(parents=True, exist_ok=False)
    results = {"meta": {"tag": tag, "timestamp_utc": stamp, "sheet": {"W": W, "H": H,
               "nx": NX, "ny": NY, "gamma": GAMMA, "imposed_shear_y": SHEAR_Y},
               "python": sys.version.split()[0], "numpy": np.version.version,
               "eps64": EPS64, "alg_budget": ALG,
               "git_e_pythonchimera": RF.git_facts(
                   Path(__file__).resolve().parent.parent.parent)},
               "phases": {"A_pinned_shear": fA, "B_release": fB, "C_law_contrast": fC},
               "all_named_numbers_hold": bool(ok_all)}
    (out_dir / "results.json").write_text(json.dumps(results, indent=2), encoding="utf8")
    lines = [
        "elastic-foundation D1 material-response demo",
        "=" * 60,
        f"run tag           : {tag}",
        f"python / numpy    : {sys.version.split()[0]} / {np.version.version}",
        f"sheet             : {W} x {H} m, {NX}x{NY} grid, gamma={GAMMA}, imposed +{SHEAR_Y} y",
        "-" * 60,
        "A PINNED SHEAR",
        f"  net right-edge internal y-reaction : {fA['net_internal_y_reaction']:+.6e}",
        f"  opposes implied displacement       : {fA['opposes_imposed']}",
        "B RELEASE (optimization steps, not time)",
        f"  outcome       : {fB['outcome']} (iters {fB['iters']}, accepted {fB['accepted']}, "
        f"rejected {fB['rejected_steps']})",
        f"  final |grad|  : {fB['final_grad_norm']:.3e}",
        f"  max free dev  : {fB['max_free_dev_from_rest']:.3e} m  (limit {fB['dev_limit']:.1e})",
        f"  energy final  : {fB['energy_final']:.3e}  (limit {fB['energy_limit']:.3e})",
        "C LAW CONTRAST (same pose)",
        f"  elastic shear resistance (right edge) : {fC['elastic_right_edge_shear_resistance']:.3e}"
        f"  (floor {fC['resistance_floor']})",
        f"  gamma max interior force              : {fC['gamma_max_interior_force']:.3e}"
        f"  (ceiling {fC['gamma_blind_ceiling']})",
        "-" * 60,
        f"all named numbers hold: {ok_all}",
        "=" * 60,
    ]
    (out_dir / "demo_report.txt").write_text("\n".join(lines), encoding="utf8")
    print("\n".join(lines))
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())