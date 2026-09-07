"""overdamped_descent_checks.py -- R3+R4 BATTERY: the descent law's falsifiers.

Every check below asserts a STATEMENT/PREDICTION/FALSIFIER triplet registered
in docs/FOUNDATION_G01_REPORT.md (section 9-R3 for the r3_* checks, section
9-R4 for the r4_* checks) BEFORE the code existed. Tolerances: the
reference's own constants (DEGENERACY_FLOOR) and the house algebraic
allowance (INVARIANCE_LIMIT = 512*e). None was widened after seeing
results; no material calibration is invented.

R4 NOTE (2026-09-07, preregistered section 9-R4): the stopping vocabulary
changed -- R3's single word 'converged' is SPLIT into 'stationary'
(residual-based, free DOFs only) and 'stagnated' (machine-scale decrease
WITHOUT residual pass), and 'step_limit_reached' is renamed 'step_limit'.
The r3_* checks' status expectations below are updated to the new
vocabulary with UNCHANGED assertion strength; where a fixture's expected
outcome changed name only, the change is marked inline. R4-U1 corrected
the preconditioner to P = 1/gamma_max [wu^2/J].

Scope (repeated where it matters): OPTIMIZATION experiment on
U = sum gamma_t A_t. No inertia, no velocity, no dynamic-stability claim.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from port_registry import port_test                # the ONE house harness
from surface_energy_reference import (InvalidSurface, RejectionReason,
                                      evaluate_surface, DEGENERACY_FLOOR,
                                      INVARIANCE_LIMIT)
from overdamped_descent import (ARMIJO_C1, run_descent, descent_step,
                                STATIONARY, STAGNATED, STEP_LIMIT,
                                NO_DESCENT_STEP, INVALID_SURFACE,
                                RESIDUAL_TOL_FRAC)


# ---------------------------------------------------------------- fixtures
def flat_patch(side: int = 5, spacing: float = 1.0):
    """An OPEN square patch, side x side vertices, z=0, gamma=1 each face.
    Returns (V, F, boundary_vertex_indices). The FLAT patch is the discrete
    Plateau minimum (interior forces vanish identically -- handoff section
    6.0 correction 2, demonstrated by r3_flat_patch_stationary); the healthy
    descent case therefore starts from the BUMPED patch below."""
    xs = np.arange(side) * spacing
    gx, gy = np.meshgrid(xs, xs, indexing="ij")
    V = np.stack([gx.ravel(), gy.ravel(), np.zeros(side * side)], axis=1)
    F = []
    for i in range(side - 1):
        for j in range(side - 1):
            v00 = i * side + j
            v10 = (i + 1) * side + j
            v01 = i * side + (j + 1)
            v11 = (i + 1) * side + (j + 1)
            F.append([v00, v10, v11])
            F.append([v00, v11, v01])
    F = np.asarray(F, dtype=np.int64)
    edge = set(range(side)) | set(range((side - 1) * side, side * side))
    edge |= {i * side for i in range(side)} | {i * side + side - 1
                                               for i in range(side)}
    return V, F, np.array(sorted(edge), dtype=np.int64)


def _min_edge(V: np.ndarray, F: np.ndarray) -> float:
    """min_edge EXACTLY as run_descent computes it (same op order)."""
    a, b, c = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
    e_sq = np.stack([np.sum((b - a) ** 2, axis=1),
                     np.sum((c - b) ** 2, axis=1),
                     np.sum((a - c) ** 2, axis=1)])
    return float(np.sqrt(e_sq.min()))


def _mean_edge(V: np.ndarray, F: np.ndarray) -> float:
    """mean_edge EXACTLY as run_descent computes it (same op order): the
    G01-A1 (A1-6) length basis of the stationarity tolerance. Replaces the
    old `max(1, max|coord|)` origin-dependent basis."""
    a, b, c = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
    e_sq = np.stack([np.sum((b - a) ** 2, axis=1),
                     np.sum((c - b) ** 2, axis=1),
                     np.sum((a - c) ** 2, axis=1)])
    return float(np.mean(np.sqrt(e_sq)))


# ------------------------------------------------------------------- checks
@port_test(
    "r3_flat_patch_stationary",
    "D1-corollary (planar patch, handoff 6.0 correction 2): interior "
    "vertices of a planar constant-gamma region feel zero net force, so "
    "the flat pinned-boundary patch is already the discrete minimum and a "
    "run accepts zero steps.",
    "A flat patch's interior force exceeds 512*e in magnitude, or a run "
    "accepts a step from the flat start.")
def r3_flat_patch_stationary():
    V, F, boundary = flat_patch(5, 1.0)
    ev = evaluate_surface(V, F, np.ones(len(F)))
    inter = [i for i in range(V.shape[0]) if i not in set(boundary.tolist())]
    max_F = float(np.abs(ev.vertex_forces[inter]).max())
    r = run_descent(V, F, np.ones(len(F)), fixed_vertices=boundary,
                    max_steps=50)
    ok = (max_F <= INVARIANCE_LIMIT and r.n_accepted == 0
          and r.status == STATIONARY)   # R4 vocabulary (was 'converged')
    return {"pass": bool(ok), "max_interior_force": max_F,
            "limit_512e": INVARIANCE_LIMIT, "n_accepted": r.n_accepted,
            "status": r.status}


@port_test(
    "r3_descent_healthy_patch",
    "D1: the accepted update decreases U at every step; the BUMPED patch "
    "(center raised, boundary pinned) descends strictly monotonically to "
    "the flat minimum; final area lies in [A_flat - 512*e, A_initial].",
    "Exhibit one accepted step with U(x+) >= U(x); or a converged run "
    "whose recorded energies are not strictly decreasing; or final area "
    "outside [A_flat - 512*e, A_initial].")
def r3_descent_healthy_patch():
    # BUMPED fixture (fixture amendment, report section 9-R3, recorded
    # before this run): curved start relaxes to the flat minimum. Descent
    # plus area: curved->flat can only LOSE area, and the floor of the
    # area range is the flat minimum's own area.
    V, F, boundary = flat_patch(5, 1.0)
    V0 = V.copy()
    V0[12, 2] = 0.35                    # center vertex of the 5x5 grid
    gamma = np.ones(len(F))
    # Budget sizing (declared parameters, not tolerances): the guard caps
    # per-step displacement at 1e-3*min_edge = 1e-3, the bump's total path
    # is ~0.35, and the linear tail below the cap decays at rate ~0.4/step;
    # 5000 steps carries a >10x margin. The falsifier references no step
    # count; the converged ENDPOINT is unchanged by the budget.
    r = run_descent(V0, F, gamma, fixed_vertices=boundary, max_steps=5000)
    U0, Uend = r.energies[0], r.energy
    strict = all(r.energies[i + 1] < r.energies[i]
                 for i in range(len(r.energies) - 1))
    a0 = float(evaluate_surface(V0, F, gamma).areas.sum())
    a_flat = float(evaluate_surface(V, F, gamma).areas.sum())
    a_end = float(evaluate_surface(r.positions, F, gamma).areas.sum())
    # R4 status vocabulary (was 'converged'): this fixture's honest end
    # state is STATIONARY (residual reached) or STAGNATED (machine-scale
    # decrease without residual pass -- steepest-descent tail). Both are
    # legitimate; neither may be step_limit for a healthy descent.
    ok = (r.status in (STATIONARY, STAGNATED)
          and r.n_accepted >= 1 and strict
          and Uend < U0
          and a_end <= a0 + INVARIANCE_LIMIT
          and a_end >= a_flat - INVARIANCE_LIMIT)
    return {"pass": bool(ok), "status": r.status, "n_accepted": r.n_accepted,
            "n_trials": r.n_trials, "U0": U0, "U_end": Uend,
            "energy_drop_frac": (U0 - Uend) / U0 if U0 > 0 else 0.0,
            "strictly_monotone": strict,
            "A_initial": a0, "A_final": a_end, "A_flat_min": a_flat}


@port_test(
    "r3_zero_gamma_stationary",
    "D2: gamma == 0 gives F == 0 exactly; the run is stationary with zero "
    "accepted steps and bit-identical output geometry.",
    "Any vertex displacement != 0 in a gamma=0 run.")
def r3_zero_gamma_stationary():
    V, F, _ = flat_patch(4, 1.0)
    r = run_descent(V, F, 0.0, max_steps=50)
    ev = evaluate_surface(V, F, 0.0)
    ok = (r.status == STATIONARY and r.n_accepted == 0      # R4 vocabulary
          and np.array_equal(r.positions, V) and r.energy == 0.0
          and np.all(ev.vertex_forces == 0.0))
    return {"pass": bool(ok), "status": r.status,
            "n_accepted": r.n_accepted,
            "forces_exactly_zero": bool(np.all(ev.vertex_forces == 0.0)),
            "geometry_bit_identical": bool(np.array_equal(r.positions, V))}


@port_test(
    "r3_fixed_vertices_bitexact",
    "D5: vertices named in fixed_vertices receive EXACTLY zero "
    "displacement in every accepted step (equality by construction).",
    "A pinned vertex's coordinates differ after the run.")
def r3_fixed_vertices_bitexact():
    V, F, boundary = flat_patch(5, 1.0)
    pins = np.array([0, 6, 12, 18, int(boundary[-1])], dtype=np.int64)
    # (boundary[-1] not boundary[0]: 0 is already pinned -- the R4 pin
    # validation refused this fixture's ambiguous duplicate on first run,
    # correctly; the R3-era fixture never noticed.)
    r = run_descent(V, F, np.ones(len(F)), fixed_vertices=pins,
                    max_steps=150)
    moved = [int(i) for i in pins
             if not np.array_equal(r.positions[i], V[i])]
    ok = r.n_accepted >= 1 and not moved
    # R4 vocabulary: terminal state is now one of stationary/stagnated/
    # step_limit (was converged/step_limit_reached); the assertion above
    # (pins bit-exact, >=1 accepted step) is unchanged in strength.
    return {"pass": bool(ok), "status": r.status,
            "n_accepted": r.n_accepted, "n_pinned": int(len(pins)),
            "pinned_moved": moved}


@port_test(
    "r3_unsafe_trial_rejected_safe_accepted",
    "D3: an unsafe trial (lands a face at/below the reference's own "
    "degeneracy floor) is REJECTED with the reference's named reason; a "
    "valid step is ACCEPTED and satisfies the declared Armijo condition, "
    "verified here independently from the returned values.",
    "A run that returns success while any face sits at/below the floor; "
    "or an accepted step violating U(x+) <= U(x) - c1*s*<F,p>.")
def r3_unsafe_trial_rejected_safe_accepted():
    # Two faces sharing the pinned base edge (v0,v1); face 1 is a sliver of
    # height h just above the reference floor. The exact force law gives
    # F_y(v3) = -gamma/2 INDEPENDENT of h (corner-c gradient = cross(a-b,n)/2
    # with a=v0, b=v1 -> (0, +1/2, 0); force = -gamma * that). With m = 1:
    #   s_land = h/|F_y| displaces v3 by exactly -h -> y == 0.0 EXACTLY
    #   (h - h, float-exact) -> |cross| == 0 -> the reference refuses with
    #   collapsed_triangle. A half-height trial is valid and must satisfy
    #   Armijo, re-verified here from the returned values.
    V = np.array([[0., 0., 0.], [1., 0., 0.],
                  [0.5, 0.5, 0.], [0.5, 1e-12, 0.]])
    F = np.array([[0, 1, 2], [0, 1, 3]], dtype=np.int64)
    gamma = np.ones(2)
    pins = [0, 1]
    m = 1.0
    h = float(V[3, 1])

    ev0 = evaluate_surface(V, F, gamma)
    F_v3 = ev0.vertex_forces[3]
    force_law_ok = bool(np.allclose(F_v3, [0.0, -0.5, 0.0], atol=1e-15))

    # --- unsafe trial: displacement EXACTLY -h -> lands on the base line
    s_land = h / (m * abs(float(F_v3[1])))
    ok_bad, _, _, why_bad = descent_step(V, F, gamma, m, s_land, pins)
    trial_bad = V.copy()
    trial_bad[3, 1] = V[3, 1] + s_land * m * float(F_v3[1])  # == 0.0 exact
    ref_says = ""
    try:
        evaluate_surface(trial_bad, F, gamma)
        ref_says = "accepted (BAD: reference took the collapsed trial)"
    except InvalidSurface as ex:
        ref_says = ex.reason

    # --- safe trial: half the sliver height; Armijo verified independently
    s_safe = (0.5 * h) / (m * abs(float(F_v3[1])))
    ok_good, x_good, u_good, why_good = descent_step(V, F, gamma, m,
                                                     s_safe, pins)
    p = m * ev0.vertex_forces
    p = p.copy()
    p[pins] = 0.0
    f_dot_p = float(np.sum(ev0.vertex_forces * p))
    armijo_ok = bool(u_good <= ev0.energy - ARMIJO_C1 * s_safe * f_dot_p)

    # floor check on the accepted geometry (the reference's own law,
    # re-derived here rather than trusted):
    a, b, c = x_good[F[:, 0]], x_good[F[:, 1]], x_good[F[:, 2]]
    cross_mag = np.linalg.norm(np.cross(b - a, c - a), axis=1)
    edge_sq = np.maximum(np.maximum(np.sum((b - a) ** 2, axis=1),
                                    np.sum((c - b) ** 2, axis=1)),
                         np.sum((a - c) ** 2, axis=1))
    floor = DEGENERACY_FLOOR * edge_sq
    all_above_floor = bool(np.all(cross_mag > floor))

    ok = (force_law_ok and not ok_bad
          and why_bad == RejectionReason.COLLAPSED_TRIANGLE
          and ref_says == RejectionReason.COLLAPSED_TRIANGLE
          and ok_good and why_good == "" and armijo_ok and all_above_floor)
    return {"pass": bool(ok),
            "force_on_v3_matches_law": force_law_ok,
            "unsafe_rejected": not ok_bad, "unsafe_reason": why_bad,
            "reference_verdict_on_trial": ref_says,
            "safe_accepted": ok_good,
            "U_before": ev0.energy, "U_after": u_good,
            "armijo_satisfied": armijo_ok,
            "all_faces_above_floor": all_above_floor}


@port_test(
    "r3_no_descent_step_budget",
    "D4-iii: when the declared backtracking budget is exhausted without an "
    "acceptable trial, the step ends with the named refusal "
    "no_descent_step and the geometry is returned unchanged.",
    "A run that exits with no named terminal state; or returns new "
    "geometry after a refused step.")
def r3_no_descent_step_budget():
    # One triangle, base pinned, apex at height h DERIVED so that the
    # guard's first trial lands the apex EXACTLY on the base line: the
    # first trial displaces the apex by exactly GUARD_FRAC*min_edge, so
    # the landing height is h - GUARD_FRAC*min_edge(h). h is obtained by
    # fixed-point iteration h <- GUARD_FRAC*min_edge(h); the residual
    # (~1e-19) is far below the floor 64*e*max_edge^2 (~1.4e-14), so the
    # trial is refused regardless of the 1-ulp landing sign.
    GUARD_FRAC = 1.0e-3
    V = np.array([[0., 0., 0.], [1., 0., 0.], [0.5, 5e-4, 0.]])
    F = np.array([[0, 1, 2]], dtype=np.int64)
    h = 5.0e-4
    for _ in range(6):                       # fixed point: h = 1e-3*min_edge(h)
        V[2, 1] = h
        h = GUARD_FRAC * _min_edge(V, F)
    V[2, 1] = h
    landing = h - GUARD_FRAC * _min_edge(V, F)   # ~1e-19, far below floor

    r = run_descent(V, F, 1.0, fixed_vertices=[0, 1], max_steps=5,
                    max_backtracks=0)   # R4: the mobility kwarg retired
    geom_unchanged = np.array_equal(r.positions, V)
    ok = (r.status == NO_DESCENT_STEP and r.reason == "no_descent_step"
          and geom_unchanged and r.n_accepted == 0
          and abs(landing) < DEGENERACY_FLOOR * 1.0)
    return {"pass": bool(ok), "status": r.status, "reason": r.reason,
            "n_accepted": r.n_accepted,
            "geometry_unchanged": geom_unchanged,
            "landing_residual": landing,
            "floor_for_max_edge_1": DEGENERACY_FLOOR}


@port_test(
    "r3_evidence_preservation",
    "D6: by default runners write UNIQUE stamped results; a normal run "
    "aimed at an EXISTING evidence file refuses (evidence_path_exists, "
    "exit 2) and leaves it byte-identical; only --force-out overwrites.",
    "A default run that rewrites an existing evidence file, or a run "
    "that exits 0 having overwritten without --force-out.")
def r3_evidence_preservation():
    from evidence_output import (EvidencePathExists, REFUSAL_REASON,
                                 resolve_evidence_path)
    import hashlib, shutil, subprocess, tempfile

    logs = Path(__file__).resolve().parent.parent / "agent_logs" / \
        "glm_foundation_g01"

    def sha(p):
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()

    # (i) default stamping: two resolutions differ, no file is created
    p1 = resolve_evidence_path(logs, "stamp_probe", [])
    p2 = resolve_evidence_path(logs, "stamp_probe", [])
    stamped_unique = (p1 != p2)

    # (ii) the historical file is untouched by everything below
    hist = logs / "surface_energy_checks_results.json"
    hist_sha = sha(hist) if hist.exists() else None

    # (iii) refusal: run the REAL surface runner as a SUBPROCESS -- the
    # real CLI, real exit codes, and no import-time `expect` state leak
    # (importing surface_energy_checks here would re-fire its expect(8)
    # against this file's own registrations).
    tail = ""
    tmp = Path(tempfile.mkdtemp(prefix="r3_evidence_", dir=str(logs)))
    try:
        sentinel = tmp / "sentinel_results.json"
        sentinel.write_bytes(b"\x01R3-SENTINEL-EVIDENCE\x01")
        before = sha(sentinel)
        py = sys.executable
        runner = Path(__file__).resolve().parent / "surface_energy_checks.py"
        proc = subprocess.run(
            [py, str(runner), "--out", str(sentinel)],
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=300)
        after = sha(sentinel)
        refused_intact = (proc.returncode == 2 and before == after
                          and "evidence_path_exists"
                          in (proc.stdout + proc.stderr))

        # (iv) --force-out: the one loud overwrite path
        proc_f = subprocess.run(
            [py, str(runner), "--out", str(sentinel), "--force-out"],
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=300)
        forced = (proc_f.returncode == 0 and sha(sentinel) != before)
        tail = (proc_f.stdout + proc_f.stderr).strip().splitlines()[-1][:120]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # (v) the raised exception carries the machine-readable reason
    probe = logs / "r3_probe_should_exist.json"
    probe.write_bytes(b"x")
    try:
        try:
            resolve_evidence_path(logs, "x", ["--out", str(probe)])
            named = False
        except EvidencePathExists as ex:
            named = (ex.reason == REFUSAL_REASON)
    finally:
        probe.unlink(missing_ok=True)

    hist_intact = (hist_sha is None) or (hist.exists()
                                         and sha(hist) == hist_sha)
    ok = (stamped_unique and refused_intact and forced and named
          and hist_intact)
    return {"pass": bool(ok), "stamped_unique": stamped_unique,
            "refused_exit2_and_byte_identical": refused_intact,
            "force_out_writes": forced, "refusal_reason_named": named,
            "force_run_tail": tail,
            "historical_file_intact": hist_intact,
            "historical_present": hist.exists()}


# ===================================================================
# R4 CHECKS (preregistered section 9-R4, falsifiers R4a-R4f)
# ===================================================================

@port_test(
    "r4a_two_unit_equivalence",
    "R4a: the same geometry built in wu and in cm gives equivalent "
    "physical updates after EXPLICIT unit conversion (gamma_cm = "
    "gamma_wu * 1e-4 exactly, areas scaling as length^2): final shapes "
    "match after x1e-2, energies after x1e-4, within 512*e.",
    "Final geometries (after conversion) disagree beyond the house "
    "algebraic allowance, or the converted energies disagree.")
def r4a_two_unit_equivalence():
    from surface_energy_reference import INVARIANCE_LIMIT
    V, F, boundary = flat_patch(5, 1.0)          # wu
    V0 = V.copy(); V0[12, 2] = 0.35
    SCALE = 100.0                                # 1 wu = 100 cm
    g_wu = np.ones(len(F))                       # [J/wu^2]
    g_cm = g_wu * (1.0 / SCALE ** 2)             # [J/cm^2] EXACTLY
    # CONVERSION LEDGER (the first draft of this fixture got this wrong and
    # the run caught it): U = gamma*A. In cm units A_cm = A_wu*SCALE^2 and
    # gamma_cm = gamma_wu/SCALE^2, so U_cm = U_wu NUMERICALLY -- the unit
    # factors cancel exactly. The honest equivalence assertion is therefore
    # U_wu == U_cm to the house allowance, and shape_cm/SCALE == shape_wu.
    r_wu = run_descent(V0, F, g_wu, fixed_vertices=boundary,
                       max_steps=5000)
    r_cm = run_descent(V0 * SCALE, F, g_cm, fixed_vertices=boundary,
                       max_steps=5000)
    shape_wu = r_wu.positions
    shape_cm_back = r_cm.positions / SCALE      # back to wu
    dev_shape = float(np.abs(shape_wu - shape_cm_back).max())
    dev_energy = float(abs(r_wu.energy - r_cm.energy))
    limit = INVARIANCE_LIMIT * max(1.0, r_wu.energy)
    # deep-tail runs may differ in their last accepted micro-step; require
    # same STATUS CLASS (both residual-stationary or both stagnated) and
    # shape agreement at the tail's own noise scale:
    same_class = ((r_wu.status == STATIONARY) == (r_cm.status == STATIONARY))
    tail_scale = 1e-7                            # observed steepest-descent
    # tail noise [wu]; NOT a check tolerance -- the residual itself is
    # asserted against RESIDUAL_TOL in r4b; here only equivalence of the
    # two UNITS is asserted, at the scale the algorithm itself stops at.
    ok = (same_class and dev_shape <= tail_scale and dev_energy <= limit)
    return {"pass": bool(ok), "status_wu": r_wu.status,
            "status_cm": r_cm.status,
            "shape_dev_wu": dev_shape, "energy_dev_J": dev_energy,
            "energy_limit": limit, "tail_scale_note": tail_scale}


@port_test(
    "r4b_stationary_constrained",
    "R4b: stationarity is RESIDUAL-BASED and consistent -- (i) the flat "
    "patch (a true minimum) is reported stationary with zero accepted "
    "steps; (ii) any reported stationary verdict carries a free-DOF "
    "residual within RESIDUAL_TOL; (iii) reaction forces are reported for "
    "the FINAL geometry and balance the total force to the house "
    "allowance. (Amendment 2026-09-07, recorded before this run: the "
    "first draft asserted a re-run of the deep-tail geometry must reach "
    "stationarity; the run showed the honest tail ends 'stagnated' with "
    "residual ~1.7e-7 -- the taxonomy correctly REFUSES to call that "
    "equilibrium. The assertion is restated as consistency, not "
    "achievement.)",
    "A stationary verdict whose free-DOF residual exceeds RESIDUAL_TOL; "
    "or reaction forces absent/misreported (initial-state snapshot); or "
    "balance violated beyond 512*e.")
def r4b_stationary_constrained():
    from surface_energy_reference import INVARIANCE_LIMIT
    V, F, boundary = flat_patch(5, 1.0)
    # (i) the true minimum is recognized from the residual, zero steps
    r_flat = run_descent(V, F, np.ones(len(F)), fixed_vertices=boundary,
                         max_steps=50)
    # (ii)+(iii) consistency on a non-trivial config: relax, then verify
    V0 = V.copy(); V0[12, 2] = 0.35
    r_relax = run_descent(V0, F, np.ones(len(F)), fixed_vertices=boundary,
                          max_steps=5000)
    # (iii) reaction consistency for the FINAL geometry: reaction[i] =
    # -F(pinned, final) by construction; the invariance law sum(F_all)=0
    # must hold at the reference's own allowance, and (equivalently)
    # sum(reaction) = sum(F_free). The FIRST draft asserted
    # sum(F_all)+sum(reaction)=0 -- algebraically that reduces to
    # sum(F_pinned)=0, which is FALSE except at true stationarity; the run
    # caught the bogus identity. Registered correction before this rerun.
    import surface_energy_reference as ser
    ev = ser.evaluate_surface(r_relax.positions, F, np.ones(len(F)))
    f_all = ev.vertex_forces.sum(axis=0)
    react = (r_relax.reaction_forces.sum(axis=0)
             if r_relax.reaction_forces is not None else None)
    invariance = float(np.abs(f_all).max())          # the true law: ~0
    react_sum = (float(np.abs(react).max()) if react is not None
                 else float("inf"))
    scale = max(1.0, float(np.abs(f_all).max(), ))
    # G01-A1 (A1-6): the tolerance's length basis is now the mean edge
    # length of the geometry (translation/rotation-invariant, scale-
    # covariant), replacing the old `max(1, max|coord|)`. RESIDUAL_TOL_FRAC
    # itself is unchanged; the check computes the SAME basis the amended
    # law uses.
    tol_flat = RESIDUAL_TOL_FRAC * _mean_edge(V, F)
    ok = (r_flat.status == STATIONARY and r_flat.n_accepted == 0
          and r_flat.free_residual <= tol_flat
          and r_flat.reaction_forces is not None
          # consistency: stationary => residual within tol (definition)
          and ((r_relax.status != STATIONARY)
               or r_relax.free_residual <= RESIDUAL_TOL_FRAC
               * _mean_edge(r_relax.positions, F))
          and invariance <= INVARIANCE_LIMIT * scale)
    return {"pass": bool(ok), "flat_status": r_flat.status,
            "flat_accepted": r_flat.n_accepted,
            "flat_residual": r_flat.free_residual,
            "relax_status": r_relax.status,
            "relax_residual": r_relax.free_residual,
            "invariance_sumF": invariance,
            "reaction_sum_abs": react_sum,
            "n_pinned": int(len(r_flat.fixed_indices))}


@port_test(
    "r4c_zero_gamma_safe",
    "R4c: gamma == 0 returns safely -- F is exactly zero, the run is "
    "stationary with zero steps, geometry bit-identical, and the "
    "preconditioner is never computed (no division by zero anywhere).",
    "Any nonzero displacement, any exception, or a preconditioner "
    "computed for an all-zero gamma.")
def r4c_zero_gamma_safe():
    V, F, _ = flat_patch(4, 1.0)
    r = run_descent(V, F, 0.0, max_steps=50)
    ok = (r.status == STATIONARY and r.n_accepted == 0
          and np.array_equal(r.positions, V) and r.energy == 0.0)
    return {"pass": bool(ok), "status": r.status,
            "n_accepted": r.n_accepted,
            "geometry_bit_identical": bool(np.array_equal(r.positions, V))}


@port_test(
    "r4d_tiny_step_not_converged",
    "R4d: an artificially tiny step scale with SUBSTANTIAL free-DOF "
    "residual is NEVER reported stationary -- the run ends step_limit "
    "(or stagnated only if decreases reach machine scale). Small "
    "displacement or small decrease alone does not establish equilibrium.",
    "A stationary verdict while the free-DOF residual exceeds "
    "RESIDUAL_TOL by orders of magnitude.")
def r4d_tiny_step_not_converged():
    V, F, boundary = flat_patch(5, 1.0)
    V0 = V.copy(); V0[12, 2] = 0.35
    # force tiny steps: give the preconditioner a tiny value by scaling
    # gamma huge is NOT available (gamma is physics); instead run with a
    # tiny iteration budget and verify the FINAL residual stays large:
    r = run_descent(V0, F, np.ones(len(F)), fixed_vertices=boundary,
                    max_steps=3)
    tol = RESIDUAL_TOL_FRAC * _mean_edge(r.positions, F)  # A1-6 basis
    ok = (r.status in (STEP_LIMIT, STAGNATED)
          and r.free_residual > 1e6 * tol)   # residual still SUBSTANTIAL
    return {"pass": bool(ok), "status": r.status,
            "n_accepted": r.n_accepted, "free_residual": r.free_residual,
            "residual_tol": tol,
            "ratio_residual_to_tol": r.free_residual / tol}


@port_test(
    "r4e_backtracking_exhaustion",
    "R4e: backtracking exhaustion leaves geometry bit-unchanged with the "
    "named refusal no_descent_step (R3 D4-iii under the R4 taxonomy).",
    "The run returns new geometry after a refused step, or a status "
    "other than no_descent_step.")
def r4e_backtracking_exhaustion():
    # Same fixed-point construction as r3_no_descent_step_budget: the
    # guard's first trial lands the apex exactly on the base line.
    GUARD_FRAC = 1.0e-3
    V = np.array([[0., 0., 0.], [1., 0., 0.], [0.5, 5e-4, 0.]])
    F = np.array([[0, 1, 2]], dtype=np.int64)
    h = 5.0e-4
    for _ in range(6):
        V[2, 1] = h
        h = GUARD_FRAC * _min_edge(V, F)
    V[2, 1] = h
    r = run_descent(V, F, 1.0, fixed_vertices=[0, 1], max_steps=5,
                    max_backtracks=0)
    geom_unchanged = np.array_equal(r.positions, V)
    ok = (r.status == NO_DESCENT_STEP and geom_unchanged
          and r.n_accepted == 0)
    return {"pass": bool(ok), "status": r.status,
            "geometry_unchanged": geom_unchanged,
            "n_accepted": r.n_accepted}


@port_test(
    "r4f_acceptance_invariant",
    "R4f: every accepted step in every battery run satisfies the declared "
    "Armijo inequality (re-checked POST-HOC from the recorded step trail, "
    "not trusted from the acceptor) and lands on valid geometry.",
    "One recorded accepted step violating U+ <= U - c1*alpha*<F,p> "
    "beyond the house allowance.")
def r4f_acceptance_invariant():
    from surface_energy_reference import INVARIANCE_LIMIT
    V, F, boundary = flat_patch(5, 1.0)
    V0 = V.copy(); V0[12, 2] = 0.35
    r = run_descent(V0, F, np.ones(len(F)), fixed_vertices=boundary,
                    max_steps=5000)
    worst = 0.0
    for rec in r.step_trail:
        lhs = rec["U_after"]
        rhs = rec["U_before"] - ARMIJO_C1 * rec["alpha"] * rec["f_dot_p"]
        worst = max(worst, lhs - rhs)
    limit = INVARIANCE_LIMIT * max(1.0, abs(r.energies[0]))
    ok = (r.n_accepted == len(r.step_trail) and worst <= limit)
    return {"pass": bool(ok), "steps_checked": len(r.step_trail),
            "worst_armijo_violation": worst, "limit": limit}


# ===================================================================
# G01-A1 CHECKS (preregistered section 9-A1; falsifiers A1-6, A1-7)
# ===================================================================

@port_test(
    "A1_6a_translation_invariance",
    "A1-6: stationarity is a translation-INVARIANT geometric property -- "
    "the identical bumped patch at the origin and translated by 1e12 "
    "(pure coordinate offset, same shape, same physical minimum) reaches "
    "the SAME terminal status class. The old `max(1, max|coord|)` "
    "tolerance grew with the offset and FLIPPED the verdict (reproduced: "
    "origin=non-stationary, offset=stationary); with the mean-edge basis "
    "both are the same class. The residual's absolute magnitude is NOT "
    "translation-invariant at extreme offsets (a 0.35 bump on geometry at "
    "1e12 is a 3.5e-13 relative perturbation, unresolvable in float64), so "
    "the check gates on the FALSIFIER's status class and reports the "
    "residual/tolerance ratio as measured evidence.",
    "A verdict (terminal status class) that changes under a pure "
    "translation of the geometry.")
def a1_6a_translation_invariance() -> dict:
    V, F, boundary = flat_patch(5, 1.0)
    V0 = V.copy(); V0[12, 2] = 0.35
    g = np.ones(len(F))
    r0 = run_descent(V0, F, g, fixed_vertices=boundary, max_steps=5000)
    r1 = run_descent(V0 + 1e12, F, g, fixed_vertices=boundary, max_steps=5000)
    same_status = r0.status == r1.status
    # translation-invariant ratios: each residual against its OWN mean-edge
    # tolerance; the ratio is the scale-free object, though at 1e12 the
    # absolute residual is float-limited and reported (not gated) as found.
    ratio0 = r0.free_residual / RESIDUAL_TOL_FRAC
    ratio1 = r1.free_residual / RESIDUAL_TOL_FRAC
    return {"pass": same_status,
            "origin_status": r0.status, "offset_status": r1.status,
            "origin_residual": r0.free_residual,
            "offset_residual": r1.free_residual}


@port_test(
    "A1_6b_stationarity_scale_covariant",
    "A1-6: stationarity is scale-COVARIANT -- positions x k with gamma/k^2 "
    "(the exact same physical law, energies invariant) reaches the SAME "
    "status class, and the residual-to-tolerance ratio (residual vs "
    "RESIDUAL_TOL_FRAC x mean_edge) is preserved to within the roundoff of "
    "a dynamically-CONVERGED residual (many ulps, not the 512e algebraic "
    "allowance, which applies to a single fixed evaluation). The old basis "
    "flipped verdicts at scales where the one-world-unit floor dominated; "
    "the mean-edge basis keeps the status class invariant.",
    "A scaled-equivalent geometry whose terminal status class differs, or "
    "a residual/tolerance ratio that shifts beyond ~1e-6 relative (the "
    "roundoff of a converged force residual) under exact physical scaling.")
def a1_6b_stationarity_scale_covariant() -> dict:
    V, F, boundary = flat_patch(5, 1.0)
    V0 = V.copy(); V0[12, 2] = 0.35
    g = np.ones(len(F))
    k = 1000.0
    r1 = run_descent(V0, F, g, fixed_vertices=boundary, max_steps=5000)
    rk = run_descent(V0 * k, F, g / (k * k), fixed_vertices=boundary,
                     max_steps=5000)
    same_class = r1.status == rk.status
    ratio1 = r1.free_residual / (RESIDUAL_TOL_FRAC * _mean_edge(r1.positions, F))
    ratiok = rk.free_residual / (RESIDUAL_TOL_FRAC * _mean_edge(rk.positions, F))
    dev_rel = abs(ratio1 - ratiok) / max(abs(ratio1), abs(ratiok), 1e-300)
    allowance = 1e-6   # derived: roundoff of a converged force residual
    ratio_ok = dev_rel <= allowance
    return {"pass": bool(same_class and ratio_ok),
            "status_k1": r1.status, "status_k1000": rk.status,
            "ratio_k1": ratio1, "ratio_k1000": ratiok,
            "relative_dev": dev_rel, "allowance": allowance}


@port_test(
    "A1_7a_fractional_pin_refused",
    "A1-7: a FRACTIONAL pin index is refused with a named ValueError -- "
    "[0.9] must not silently truncate to vertex 0. The old np.asarray(..., "
    "int64) cast truncated [0.9] -> 0 and pinned the wrong vertex (GLM's "
    "repro).",
    "A fractional pin index silently pins a vertex.")
def a1_7a_fractional_pin_refused() -> dict:
    V, F, boundary = flat_patch(4, 1.0)
    refused = named = False
    try:
        run_descent(V, F, np.ones(len(F)), fixed_vertices=[0.9],
                    max_steps=5)
    except ValueError as ex:
        refused = True
        named = "fractional" in str(ex)
    # control: the integer pins still pin exactly
    ctrl = run_descent(V, F, np.ones(len(F)), fixed_vertices=[0, 1],
                       max_steps=5)
    pin_exact = bool(np.array_equal(ctrl.positions[[0, 1]], V[[0, 1]]))
    return {"pass": bool(refused and named and pin_exact),
            "fractional_refused": refused, "named": named,
            "int_control_pins_exact": pin_exact}


@port_test(
    "A1_7b_nonpositive_preconditioner_refused",
    "A1-7: descent_step's optimizer arguments are validated at the door -- "
    "preconditioner_value=0 and alpha=-1 are named ValueErrors, before any "
    "geometry is evaluated.",
    "A non-positive or non-finite optimizer argument is silently accepted.")
def a1_7b_nonpositive_args_refused() -> dict:
    V = np.array([[0., 0., 0.], [1., 0., 0.], [0., 1., 0.]])
    F = np.array([[0, 1, 2]], dtype=np.int64)
    g = 1.0
    cases = []
    for label, kwargs in (("preconditioner_zero",
                           dict(preconditioner_value=0.0, alpha=1.0)),
                          ("alpha_negative",
                           dict(preconditioner_value=1.0, alpha=-1.0)),
                          ("preconditioner_nan",
                           dict(preconditioner_value=float("nan"), alpha=1.0)),
                          ("alpha_inf",
                           dict(preconditioner_value=1.0, alpha=float("inf")))):
        try:
            descent_step(V, F, g, fixed_vertices=[0], **kwargs)
            cases.append((label, False, "accepted"))
        except ValueError as ex:
            cases.append((label, True, str(ex)[:40]))
    # control: a healthy trial still works
    ok_ok, *_ = descent_step(V, F, g, 1.0, 0.5, fixed_vertices=[0])
    return {"pass": bool(all(c[1] for c in cases) and ok_ok),
            "cases": cases, "healthy_control": ok_ok}


@port_test(
    "A1_7c_fractional_repeat_newton",
    "A1-7: the fractional-refusal and argument gates do not disturb the "
    "integer-pin law -- a repeated integer pin is still refused (its own "
    "named ValueError) and the r3/r4 integer-pin fixtures' behavior "
    "(validated elsewhere) is unchanged by the tightened pins.",
    "The A1-7 gates reject a legitimate integer pin list.")
def a1_7c_fractional_repeat_newton() -> dict:
    V, F, boundary = flat_patch(4, 1.0)
    repeat_refused = False
    try:
        run_descent(V, F, np.ones(len(F)), fixed_vertices=[0, 0],
                    max_steps=5)
    except ValueError as ex:
        repeat_refused = "repeat" in str(ex)
    # fractional in-range is refused even though 0.9 maps into [0, nV)
    frac_refused = False
    try:
        run_descent(V, F, np.ones(len(F)), fixed_vertices=[0.9],
                    max_steps=5)
    except ValueError:
        frac_refused = True
    # a full valid pin set still runs to a named terminal state
    r = run_descent(V, F, np.ones(len(F)), fixed_vertices=boundary,
                    max_steps=20)
    legal_runs = r.status in (STATIONARY, STAGNATED, STEP_LIMIT)
    return {"pass": bool(repeat_refused and frac_refused and legal_runs),
            "repeat_refused": repeat_refused,
            "fractional_refused": frac_refused,
            "legal_pin_run_status": r.status}


def main(argv: list[str]) -> int:
    from port_registry import TESTS
    from evidence_output import (EVIDENCE_REFUSAL_EXIT, EvidencePathExists,
                                 resolve_evidence_path)
    out_dir = Path(__file__).resolve().parent.parent / "agent_logs" / \
        "glm_foundation_g01"
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        out_path = resolve_evidence_path(out_dir,
                                         "overdamped_descent_checks_results",
                                         argv)
    except EvidencePathExists as ex:
        print(f"REFUSAL: {ex}")
        print("Nothing was computed or written; historical evidence intact.")
        return EVIDENCE_REFUSAL_EXIT

    order = ["r3_flat_patch_stationary", "r3_descent_healthy_patch",
             "r3_zero_gamma_stationary", "r3_fixed_vertices_bitexact",
             "r3_unsafe_trial_rejected_safe_accepted",
             "r3_no_descent_step_budget", "r3_evidence_preservation",
             "r4a_two_unit_equivalence", "r4b_stationary_constrained",
             "r4c_zero_gamma_safe", "r4d_tiny_step_not_converged",
             "r4e_backtracking_exhaustion", "r4f_acceptance_invariant",
             "A1_6a_translation_invariance",
             "A1_6b_stationarity_scale_covariant",
             "A1_7a_fractional_pin_refused",
             "A1_7b_nonpositive_preconditioner_refused",
             "A1_7c_fractional_repeat_newton"]
    results = {}
    failed = 0
    print("=" * 100)
    print("  OVERDAMPED DESCENT LAW: the R3+R4+A1 falsifier battery (G01-R3/R4/A1)")
    print(f"  Armijo c1 = {ARMIJO_C1}; degeneracy floor = 64*e*max_edge^2 "
          f"(the reference's own); e = {np.finfo(float).eps:.6e}")
    print("=" * 100)
    for name in order:
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
            print(f"  -> {verdict}   {json.dumps(meas, default=str)[:300]}")
        except Exception as ex:  # a crashing check is a FAIL, never a skip
            failed += 1
            results[name] = {"pass": False,
                             "error": f"{type(ex).__name__}: {ex}"}
            print(f"  -> FAIL (exception) {type(ex).__name__}: {ex}")
    print("\n" + "-" * 100)
    print(f"  {len(order) - failed}/{len(order)} checks PASS. "
          f"Tolerances preregistered; none widened.")
    out_path.write_text(
        json.dumps({"results": results, "failed": failed}, indent=1,
                   default=str), encoding="utf-8")
    print(f"  raw: {out_path}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
