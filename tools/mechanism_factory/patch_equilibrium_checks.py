"""patch_equilibrium_checks.py -- THE REGISTERED FALSIFIER BATTERY for the
patch boundary/load equilibrium solve (§11.18 P1 reference layer).

Six checks, each with a STATEMENT and a FALSIFIER (Rule 0), run through the
house harness (tools/port_registry.py port_test/expect, the pattern of
surface_energy_checks.py). ALL tolerances are preregistered in
patch_equilibrium.PREREGISTERED_ALLOWANCES, frozen in code before any run;
a failing check gets the SOLVER fixed, never the tolerance.

  C1 single-triangle ANALYTIC anchor. Two pinned vertices b, c (edge length
     L), one loaded free vertex a, dead load f. Equilibrium of
     U = gamma*A(x) - f.x at a reads f = gamma*grad_a A. Geometry:
     grad_a A = cross(b-c, n)/2 has magnitude |b-c|/2 = L/2 EXACTLY (b-c lies
     in the plane, n is the plane normal) and lies in-plane, perpendicular to
     bc. Hence equilibrium exists iff f is perpendicular to bc with
     |f| = gamma*L/2 (the "pin-reaction cone" collapses to a circle here);
     the equilibrium set is then the RAY {a : (a - mid(bc)) parallel to f},
     along which U = 0 EXACTLY (flat direction: moving
     a along f grows gamma*A by |f| ds and lowers -f.x by the same). The
     check asserts: n.f = 0, height direction parallel to f, reactions
     R_b, R_c match +gamma*grad A (pin cancels surface force) computed by INDEPENDENT Heron finite
     differences (the lab's F1 instrument), and the reaction sum identity
     R_b + R_c + f = 0.
  C2 zero-load equivalence: solve_equilibrium(..., loads=[]) reproduces
     overdamped_descent.run_descent's final energy and stationarity exactly
     (same preconditioner, same Armijo, same guard -> same trajectory).
  C3 balance identity on an ASYMMETRIC fixture: sum(reactions) + sum(loads)
     = 0 and sum(x x (reaction + f)) = 0 (moment about the ORIGIN -- exact
     because the surface law's torque invariance is origin-independent).
     FIXTURE NOTE (physics finding, reported not tuned away): the task
     prescribed "irregular_patch, partial-rim pins". Under the pure
     constant-gamma CURRENT-area law a FREE boundary vertex is NOT
     force-free -- the film contracts its free edge (line tension gamma;
     measured |F| = gamma*spacing on a straight free rim) -- so partial-rim
     pins have NO equilibrium and the loaded irregular mesh additionally
     carries soft tangential (reparametrization) modes with Hessian
     condition number ~1e7 that the lab's own fixed preconditioner cannot
     descend (verified: run_descent itself stagnates/step-limits there).
     C3 therefore uses an asymmetric composite of three loaded apex patches
     (different rim counts/radii/heights/loads) -- asymmetric, multi-load,
     and honestly convergent. The partial-rim case is kept as an honesty
     witness in C6.
  C4 asymmetry is real: per-block reaction norms differ by > 10% (a
     symmetric artifact gives ~0).
  C5 refusals: every named refusal fires under the right name.
  C6 convergence honesty: unsolvable cases (load beyond the reaction cone;
     free-rim contraction) return step_limit/stagnated -- NEVER a fake
     stationary -- while a solvable control on the same machinery does
     converge (the solver is not simply giving up).

Run:  python tools/mechanism_factory/patch_equilibrium_checks.py
      exit 0 = all PASS, 1 = a check failed, 2 = evidence-path refusal.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
_TOOLS = _HERE.parent
sys.path.insert(0, str(_TOOLS))                    # port_registry lives here
sys.path.insert(0, str(_TOOLS / "membrane_scale_lab"))  # law/solver/fixtures

from port_registry import port_test, expect        # noqa: E402  house harness
import surface_energy_reference as ser             # noqa: E402
import overdamped_descent as od                    # noqa: E402
import fixture_generator as fg                     # noqa: E402
import patch_equilibrium as pe                     # noqa: E402

A = pe.PREREGISTERED_ALLOWANCES                    # frozen allowances
EXPECTED_CHECKS = 6


# ── fixtures ────────────────────────────────────────────────────────────────

def anchor_triangle():
    """Two pins b,c (L=1 on the x axis) + loaded free vertex a."""
    V = np.array([[-0.5, 0.0, 0.0], [0.5, 0.0, 0.0], [0.0, 0.3, 0.4]])
    F = np.array([[0, 1, 2]], dtype=np.int64)
    return V, F                                     # pins 0,1; free 2


def heron_area_grad_fd(pos, face, h=ser.FD_H):
    """INDEPENDENT instrument (lab F1 style): grad of the Heron area w.r.t.
    each corner by central differences. No cross products, no normals."""
    def area(p):
        la = np.linalg.norm(p[1] - p[2])
        lb = np.linalg.norm(p[2] - p[0])
        lc = np.linalg.norm(p[0] - p[1])
        s = 0.5 * (la + lb + lc)
        return math.sqrt(max(s * (s - la) * (s - lb) * (s - lc), 0.0))
    g = np.zeros((3, 3))
    for k in range(3):
        for c in range(3):
            pp = [p.copy() for p in pos]; pp[k][c] += h
            pm = [p.copy() for p in pos]; pm[k][c] -= h
            g[k, c] = (area(pp) - area(pm)) / (2.0 * h)
    return g


def loaded_apex_composite():
    """Asymmetric composite: three apex patches (6/5/8-rim fans of different
    radius/height/offset), rims pinned, apexes loaded -- the C3/C4 fixture
    (see module docstring for why not partial-rim irregular_patch)."""
    def block(off, n_rim, radius, height):
        th = 2.0 * np.pi * np.arange(n_rim) / n_rim
        rim = np.stack([radius * np.cos(th), radius * np.sin(th),
                        np.zeros(n_rim)], axis=1) + off
        V = np.vstack([rim, np.array([[0.0, 0.0, height]]) + off])
        F = np.array([[n_rim, k, (k + 1) % n_rim] for k in range(n_rim)],
                     dtype=np.int64)
        return V, F, n_rim
    blocks = [block(np.array([-1.4, 0.0, 0.0]), 6, 1.00, 0.25),
              block(np.array([0.7, 0.9, 0.1]), 5, 0.70, 0.15),
              block(np.array([0.6, -1.0, -0.05]), 8, 0.85, 0.30)]
    Vs, Fs, pins, apex, off = [], [], [], [], 0
    for V, F, n_rim in blocks:
        Vs.append(V); Fs.append(F + off)
        pins += [off + i for i in range(n_rim)]
        apex.append(off + n_rim)
        off += V.shape[0]
    loads = [(apex[0], (0.0, 0.0, -0.15)),
             (apex[1], (0.0, 0.0, 0.08)),
             (apex[2], (0.0, 0.0, -0.10))]
    return np.vstack(Vs), np.vstack(Fs), pins, loads


def partial_rim_case():
    """irregular_patch with three rim vertices left FREE (the task's literal
    C3 prescription) -- kept as the C6 honesty witness: under this law the
    free rim contracts and no equilibrium exists."""
    fx = fg.irregular_patch(n_vertices=24, seed=1)
    side = 4
    nb = fx.stats.n_vertices - side * side
    grid = lambda i, j: nb + i * side + j          # noqa: E731
    rim = sorted(set([grid(0, j) for j in range(side)]
                     + [grid(side - 1, j) for j in range(side)]
                     + [grid(i, 0) for i in range(1, side - 1)]
                     + [grid(i, side - 1) for i in range(1, side - 1)]))
    free_rim = [grid(0, 2), grid(side - 1, 1), grid(2, 0)]
    pins = [v for v in rim if v not in free_rim]
    return fx.positions.copy(), fx.faces, pins, fx.gamma


# ── C1 ──────────────────────────────────────────────────────────────────────

@port_test(
    "C1_analytic_anchor",
    "Single triangle, pins b,c, loaded vertex a with |f| = gamma*L/2 exactly: "
    "the solve lands on the analytic equilibrium -- final normal perpendicular "
    "to f, height direction parallel to f, pin reactions match +gamma*grad(A) "
    "(the pin cancels the surface force) from independent Heron finite "
    "differences, and R_b + R_c + f = 0.",
    "Any identity exceeds C1_identity_tol, the status is a crash/no-descent, "
    "or the free residual exceeds C1_residual_tol.")
def c1_analytic_anchor() -> dict:
    V, F = anchor_triangle()
    gamma, L = 1.0, 1.0
    f = np.array([0.0, 0.0, gamma * L / 2.0])       # |f| = gamma*L/2 exactly
    r = pe.solve_equilibrium(V, F, gamma, [0, 1], [(2, f)], max_steps=5000)
    tol = A["C1_identity_tol"]
    x = r.positions
    b, c, a = x[0], x[1], x[2]
    n = np.cross(b - a, c - a); n /= np.linalg.norm(n)
    mid = 0.5 * (b + c)
    # the along-edge component of (a - mid) is EXACTLY flat (f perp bc), so
    # the equilibrium invariant is on the perpendicular component only:
    t_hat = (c - b) / np.linalg.norm(c - b)
    height = (a - mid) - np.dot(a - mid, t_hat) * t_hat
    height /= np.linalg.norm(height)
    # reactions vs INDEPENDENT Heron-FD gradients. Sign law: the pin applies
    # the force that CANCELS the surface force on its vertex,
    # R = -F_surface = -(-gamma*grad A) = +gamma*grad A.
    grad = heron_area_grad_fd([a, b, c], (0, 1, 2))
    Rb_ind = gamma * grad[1]
    Rc_ind = gamma * grad[2]
    R = r.reaction_forces
    Rb, Rc = R[0], R[1]
    rows = {
        "status": r.status,
        "free_residual": r.free_residual,
        "normal_dot_fhat": abs(float(np.dot(n, f / np.linalg.norm(f)))),
        "height_cross_fhat": float(np.linalg.norm(np.cross(height,
                                                           f / np.linalg.norm(f)))),
        "Rb_vs_heron_fd": float(np.linalg.norm(Rb - Rb_ind)),
        "Rc_vs_heron_fd": float(np.linalg.norm(Rc - Rc_ind)),
        "reaction_sum_identity": float(np.linalg.norm(Rb + Rc + f)),
    }
    ok = (r.status in (pe.STATIONARY, pe.STAGNATED)
          and r.free_residual <= A["C1_residual_tol"]
          and all(rows[k] <= tol for k in
                  ("normal_dot_fhat", "height_cross_fhat", "Rb_vs_heron_fd",
                   "Rc_vs_heron_fd", "reaction_sum_identity")))
    return {"pass": bool(ok), "allowances": {"residual": A["C1_residual_tol"],
            "identity": tol}, "measured": rows,
            "reactions": R.tolist(), "final_positions": x.tolist()}


# ── C2 ──────────────────────────────────────────────────────────────────────

@port_test(
    "C2_zero_load_equivalence",
    "solve_equilibrium(..., loads=[]) reproduces run_descent's final energy "
    "(<= 1e-9 J) and the SAME terminal status and free residual (<= 1e-12 wu) "
    "on a flat disk (both stationary) and a bumped disk (both same status): "
    "zero loads must reduce the loaded solver to the lab solver exactly.",
    "Energy difference exceeds C2_energy_equiv_tol, statuses disagree, or "
    "residuals differ beyond 1e-12.")
def c2_zero_load_equivalence() -> dict:
    rows = {}
    ok = True
    for name, fx in (("flat_disk", fg.regular_disk(n_ring=8, bump=0.0)),
                     ("bump_disk", fg.regular_disk(n_ring=8, bump=0.3))):
        r_lab = od.run_descent(fx.positions, fx.faces, fx.gamma,
                               fixed_vertices=fx.stats.pinned, max_steps=2000)
        r_mine = pe.solve_equilibrium(fx.positions, fx.faces, fx.gamma,
                                      fx.stats.pinned, [], max_steps=2000)
        dE = abs(r_lab.energy - r_mine.energy)
        dR = abs(r_lab.free_residual - r_mine.free_residual)
        same = (r_lab.status == r_mine.status)
        rows[name] = {"lab_status": r_lab.status, "mine_status": r_mine.status,
                      "dE": dE, "d_residual": dR,
                      "lab_residual": r_lab.free_residual}
        ok = ok and same and dE <= A["C2_energy_equiv_tol"] and dR <= 1.0e-12
    return {"pass": bool(ok), "allowances": {"energy": A["C2_energy_equiv_tol"],
            "residual": 1.0e-12}, "measured": rows}


# ── C3 ──────────────────────────────────────────────────────────────────────

@port_test(
    "C3_balance_identity",
    "Asymmetric loaded composite (three apex patches, 6/5/8 rims, three "
    "point loads): at the solve, |sum(reactions) + sum(loads)| <= "
    "1e-6*max(1,sum|f|) and |sum x x (reaction + f)| <= 1e-6*max(1,sum|x||f|) "
    "(moment about the origin -- exact by the law's torque invariance).",
    "Either balance residual exceeds its preregistered tolerance, or the "
    "solve crashes / reports no_descent_step.")
def c3_balance_identity() -> dict:
    V, F, pins, loads = loaded_apex_composite()
    r = pe.solve_equilibrium(V, F, 1.0, pins, loads, max_steps=6000)
    R = r.reaction_forces
    x = r.positions
    fsum = np.zeros(3)
    mom = np.zeros(3)
    for i, v in loads:
        fsum += np.asarray(v)
    for k, i in enumerate(r.fixed_indices):
        mom += np.cross(x[i], R[k])
    for i, v in loads:
        mom += np.cross(x[i], np.asarray(v))
    scale_f = max(1.0, float(sum(np.linalg.norm(v) for _, v in loads)))
    scale_m = max(1.0, float(sum(np.linalg.norm(x[i]) * np.linalg.norm(v)
                                 for i, v in loads)))
    fb = float(np.linalg.norm(R.sum(axis=0) + fsum))
    mb = float(np.linalg.norm(mom))
    ok = (r.status in (pe.STATIONARY, pe.STAGNATED)
          and r.free_residual <= 1.0e-6
          and fb <= A["C3_force_balance_tol"] * scale_f
          and mb <= A["C3_moment_balance_tol"] * scale_m)
    return {"pass": bool(ok), "status": r.status,
            "free_residual": r.free_residual, "steps": r.n_accepted,
            "force_balance": fb, "moment_balance": mb,
            "force_balance_tol": A["C3_force_balance_tol"] * scale_f,
            "moment_balance_tol": A["C3_moment_balance_tol"] * scale_m,
            "reactions": R.tolist(),
            "fixture": {"n_vertices": int(V.shape[0]),
                        "n_faces": int(F.shape[0]),
                        "pin_set": "all rim vertices of three apex fans "
                                   "(6+5+8 = 19 pins), apexes free",
                        "loads": [[int(i), list(map(float, v))]
                                  for i, v in loads]}}


# ── C4 ──────────────────────────────────────────────────────────────────────

@port_test(
    "C4_asymmetry_real",
    "On the same asymmetric fixture the per-block mean reaction norms differ "
    "by more than C4_asymmetry_margin (10%): the loaded geometry is not a "
    "symmetric artifact -- the heavily loaded block carries more pin load.",
    "The near/far block reaction-norm margin is at or below 10%, or the "
    "fixture's loads/geometry are symmetric (artifact guard).")
def c4_asymmetry_real() -> dict:
    V, F, pins, loads = loaded_apex_composite()
    r = pe.solve_equilibrium(V, F, 1.0, pins, loads, max_steps=6000)
    R = r.reaction_forces
    rn = np.linalg.norm(R, axis=1)
    idx = np.asarray(r.fixed_indices)
    blocks = {"block0_6rim": idx < 6,
              "block1_5rim": (idx >= 6) & (idx < 11),
              "block2_8rim": idx >= 11}
    means = {k: float(rn[m].mean()) for k, m in blocks.items()}
    hi, lo = max(means.values()), min(means.values())
    margin = (hi - lo) / hi
    # artifact guard: loads differ in magnitude and geometry differs
    mags = sorted(float(np.linalg.norm(v)) for _, v in loads)
    asymmetric_inputs = (mags[-1] - mags[0]) / mags[-1] > 0.10
    ok = margin > A["C4_asymmetry_margin"] and asymmetric_inputs
    return {"pass": bool(ok), "block_mean_reaction_norms": means,
            "margin": margin, "margin_required": A["C4_asymmetry_margin"],
            "load_magnitudes": mags}


# ── C5 ──────────────────────────────────────────────────────────────────────

@port_test(
    "C5_refusals",
    "Every named refusal fires BEFORE any iteration under its exact name: "
    "load_on_fixed_vertex, load_nonfinite, load_index_out_of_range, "
    "load_index_fractional, load_index_repeated, load_zero_tension, "
    "fixed_index_fractional, fixed_index_out_of_range, fixed_index_repeated, "
    "and the reused law names negative_gamma, nonfinite_positions, "
    "collapsed_triangle; a valid loaded solve is NOT refused.",
    "Any malformed input is accepted, refused under the wrong name, or a "
    "valid case is refused.")
def c5_refusals() -> dict:
    V, F = anchor_triangle()
    L = pe.LoadRejectionReason
    RR = ser.RejectionReason
    cases = []

    def add(name, fn, want):
        cases.append((name, fn, want))

    add("load_on_fixed_vertex",
        lambda: pe.solve_equilibrium(V, F, 1.0, [0, 1], [(0, (1., 0., 0.))]),
        L.LOAD_ON_FIXED_VERTEX)
    add("nan_load",
        lambda: pe.solve_equilibrium(V, F, 1.0, [0, 1],
                                     [(2, (np.nan, 0., 0.))]),
        L.LOAD_NONFINITE)
    add("inf_load",
        lambda: pe.solve_equilibrium(V, F, 1.0, [0, 1],
                                     [(2, (np.inf, 0., 0.))]),
        L.LOAD_NONFINITE)
    add("load_index_out_of_range",
        lambda: pe.solve_equilibrium(V, F, 1.0, [0, 1],
                                     [(9, (1., 0., 0.))]),
        L.LOAD_INDEX_OUT_OF_RANGE)
    add("load_index_fractional",
        lambda: pe.solve_equilibrium(V, F, 1.0, [0, 1],
                                     [(1.5, (1., 0., 0.))]),
        L.LOAD_INDEX_FRACTIONAL)
    add("load_index_repeated",
        lambda: pe.solve_equilibrium(V, F, 1.0, [0, 1],
                                     [(2, (1., 0., 0.)), (2, (0., 1., 0.))]),
        L.LOAD_INDEX_REPEATED)
    add("zero_tension_with_load",
        lambda: pe.solve_equilibrium(V, F, 0.0, [0, 1],
                                     [(2, (0., 0., 1.))]),
        L.LOAD_ZERO_TENSION)
    add("fixed_index_fractional",
        lambda: pe.solve_equilibrium(V, F, 1.0, [0.5],
                                     [(2, (0., 0., 1.))]),
        L.FIXED_INDEX_FRACTIONAL)
    add("fixed_index_out_of_range",
        lambda: pe.solve_equilibrium(V, F, 1.0, [0, 7],
                                     [(2, (0., 0., 1.))]),
        L.FIXED_INDEX_OUT_OF_RANGE)
    add("fixed_index_repeated",
        lambda: pe.solve_equilibrium(V, F, 1.0, [0, 0, 1],
                                     [(2, (0., 0., 1.))]),
        L.FIXED_INDEX_REPEATED)
    add("negative_gamma",
        lambda: pe.solve_equilibrium(V, F, -1.0, [0, 1],
                                     [(2, (0., 0., 1.))]),
        RR.NEGATIVE_GAMMA)
    add("nan_gamma",
        lambda: pe.solve_equilibrium(V, F, np.nan, [0, 1],
                                     [(2, (0., 0., 1.))]),
        RR.NONFINITE_GAMMA)

    def _nan_pos():
        Vb = V.copy(); Vb[2, 0] = np.nan
        pe.solve_equilibrium(Vb, F, 1.0, [0, 1], [(2, (0., 0., 1.))])
    add("nan_positions", _nan_pos, RR.NONFINITE_POSITIONS)

    def _collapsed():
        Vc = np.array([[0., 0., 0.], [1., 0., 0.], [2., 0., 0.]])
        pe.solve_equilibrium(Vc, np.array([[0, 1, 2]]), 1.0, [0, 1],
                             [(2, (0., 0., 1.))])
    add("collapsed_triangle", _collapsed, RR.COLLAPSED_TRIANGLE)

    rows, ok = {}, True
    for name, fn, want in cases:
        try:
            fn()
            rows[name] = {"refused": False, "expected": want}
            ok = False
        except ser.InvalidSurface as ex:
            good = ex.reason == want
            rows[name] = {"refused": True, "reason": ex.reason,
                          "expected": want, "name_ok": good}
            ok = ok and good
        except Exception as ex:                 # a crash is not a refusal
            rows[name] = {"refused": True,
                          "reason": f"WRONG-TYPE {type(ex).__name__}"}
            ok = False
    # control: the valid anchor solve must NOT be refused
    try:
        r = pe.solve_equilibrium(V, F, 1.0, [0, 1],
                                 [(2, (0., 0., 0.5))], max_steps=5000)
        rows["valid_control_accepted"] = {"status": r.status}
    except ser.InvalidSurface as ex:
        rows["valid_control_accepted"] = {"refused": True, "reason": ex.reason}
        ok = False
    return {"pass": bool(ok), "cases": rows}


# ── C6 ──────────────────────────────────────────────────────────────────────

@port_test(
    "C6_convergence_honesty",
    "Unsolvable cases never fake a stationary: (a) a load beyond the pin-"
    "reaction cone (|f| > gamma*L/2 on the single triangle) and (b) the "
    "partial-rim irregular patch (free rim contracts -- no equilibrium under "
    "this law) both end step_limit/stagnated/no_descent_step with free "
    "residual ABOVE C6_unconverged_residual_floor, while (c) the solvable "
    "apex control on the same machinery converges (the solver is not simply "
    "giving up).",
    "Any unsolvable case reports stationary, or its residual is below the "
    "floor (meaning it was near-equilibrium after all), or the control fails "
    "to converge.")
def c6_convergence_honesty() -> dict:
    floor = A["C6_unconverged_residual_floor"]
    rows = {}
    # (a) overload: |f| = 0.6 > gamma*L/2 = 0.5
    V, F = anchor_triangle()
    ra = pe.solve_equilibrium(V, F, 1.0, [0, 1], [(2, (0., 0., 0.6))],
                              max_steps=400)
    rows["overload"] = {"status": ra.status,
                        "free_residual": ra.free_residual,
                        "steps": ra.n_accepted}
    ok_a = (ra.status != pe.STATIONARY
            and ra.free_residual > floor)
    # (b) partial-rim pins: free rim contracts, no equilibrium exists
    pos, faces, pins, gam = partial_rim_case()
    rb = pe.solve_equilibrium(pos, faces, gam, pins, [], max_steps=1500)
    rows["partial_rim"] = {"status": rb.status,
                           "free_residual": rb.free_residual,
                           "steps": rb.n_accepted}
    ok_b = rb.status != pe.STATIONARY and rb.free_residual > floor
    # (c) control: the solvable composite converges on the same machinery
    Vc, Fc, pc, lc = loaded_apex_composite()
    rc = pe.solve_equilibrium(Vc, Fc, 1.0, pc, lc, max_steps=6000)
    rows["control"] = {"status": rc.status,
                       "free_residual": rc.free_residual,
                       "steps": rc.n_accepted}
    ok_c = (rc.status in (pe.STATIONARY, pe.STAGNATED)
            and rc.free_residual <= 1.0e-6)
    return {"pass": bool(ok_a and ok_b and ok_c),
            "floor": floor, "measured": rows,
            "note": "partial-rim non-convergence is PHYSICS under the pure "
                    "area law (free boundary carries line tension gamma), "
                    "not a solver defect -- reported as stagnation/step_limit"}


expect(EXPECTED_CHECKS)


# ── runner (evidence law first, like surface_energy_checks.main) ────────────

ORDER = ["C1_analytic_anchor", "C2_zero_load_equivalence",
         "C3_balance_identity", "C4_asymmetry_real", "C5_refusals",
         "C6_convergence_honesty"]


def main(argv: list[str]) -> int:
    from evidence_output import (EVIDENCE_REFUSAL_EXIT, EvidencePathExists,
                                 resolve_evidence_path)
    out_dir = _TOOLS.parent / "docs" / "evidence" / "mechanism_factory"
    try:
        out_path = resolve_evidence_path(out_dir,
                                         "patch_equilibrium_receipt", argv)
    except EvidencePathExists as ex:
        print(f"REFUSAL: {ex}")
        print("Nothing was computed or written; historical evidence intact.")
        return EVIDENCE_REFUSAL_EXIT

    from port_registry import TESTS
    results, failed = {}, 0
    print("=" * 100)
    print("  PATCH EQUILIBRIUM (boundary/load solve): falsifier battery")
    print(f"  allowances (preregistered): "
          f"C1 res {A['C1_residual_tol']:.1e} id {A['C1_identity_tol']:.1e}; "
          f"C2 E {A['C2_energy_equiv_tol']:.1e}; "
          f"C3 {A['C3_force_balance_tol']:.0e} rel; "
          f"C4 margin {A['C4_asymmetry_margin']}; "
          f"C6 floor {A['C6_unconverged_residual_floor']:.0e}")
    print("=" * 100)
    for name in ORDER:
        rec = TESTS[name]
        print(f"\n[{name}]\n  STATEMENT : {rec['statement'][:96]}...")
        try:
            r = rec["fn"]()
            results[name] = r
            verdict = "PASS" if r.get("pass") else "FAIL"
            if not r.get("pass"):
                failed += 1
            meas = {k: v for k, v in r.items()
                    if k not in ("pass",) and not isinstance(v, dict)}
            print(f"  FALSIFIER : {rec['falsifier'][:96]}...")
            print(f"  -> {verdict}   {json.dumps(meas, default=str)[:400]}")
        except Exception as ex:            # a crash is a FAIL, never a skip
            failed += 1
            results[name] = {"pass": False,
                             "error": f"{type(ex).__name__}: {ex}"}
            print(f"  -> FAIL (exception) {type(ex).__name__}: {ex}")
    print("\n" + "-" * 100)
    print(f"  {len(ORDER) - failed}/{len(ORDER)} checks PASS. Tolerances "
          f"preregistered in patch_equilibrium.PREREGISTERED_ALLOWANCES; "
          f"none widened after seeing results.")

    # receipt (schema chimera-mechanism-factory-patch-equilibrium-v1)
    checks_summary = {n: {"pass": bool(results[n].get("pass"))}
                      for n in ORDER}
    case_records = {
        "C1_single_triangle_anchor": results["C1_analytic_anchor"],
        "C2_zero_load_equivalence": results["C2_zero_load_equivalence"],
        "C3_asymmetric_composite": results["C3_balance_identity"],
        "C4_asymmetry": results["C4_asymmetry_real"],
        "C6_honesty": results["C6_convergence_honesty"],
    }
    pe.write_receipt(out_path, case_records, checks_summary)
    print(f"  receipt: {out_path}")
    if "--json" in argv:
        print(json.dumps(results, indent=1, default=str))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
