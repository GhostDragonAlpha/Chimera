"""overdamped_descent_checks.py -- R3 BATTERY: the descent law's falsifiers.

Every check below asserts a STATEMENT/PREDICTION/FALSIFIER triplet registered
in docs/FOUNDATION_G01_REPORT.md section 9-R3 BEFORE this file existed.
Tolerances: the reference's own constants (DEGENERACY_FLOOR) and the house
algebraic allowance (INVARIANCE_LIMIT = 512*e). None was widened after
seeing results; no material calibration is invented.

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
from overdamped_descent import ARMIJO_C1, run_descent, descent_step


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
          and r.status == "converged")
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
    ok = (r.status == "converged" and r.n_accepted >= 1 and strict
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
    ok = (r.status == "converged" and r.n_accepted == 0
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
    pins = np.array([0, 6, 12, 18, int(boundary[0])], dtype=np.int64)
    r = run_descent(V, F, np.ones(len(F)), fixed_vertices=pins,
                    max_steps=150)
    moved = [int(i) for i in pins
             if not np.array_equal(r.positions[i], V[i])]
    ok = r.n_accepted >= 1 and not moved
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
                    max_backtracks=0, mobility=10.0)
    geom_unchanged = np.array_equal(r.positions, V)
    ok = (r.status == "no_descent_step" and r.reason == "no_descent_step"
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
             "r3_no_descent_step_budget", "r3_evidence_preservation"]
    results = {}
    failed = 0
    print("=" * 100)
    print("  OVERDAMPED DESCENT LAW: the R3 falsifier battery (G01-R3)")
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
