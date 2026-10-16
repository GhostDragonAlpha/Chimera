"""solver_candidate.py -- THE VERSIONED CANDIDATE SOLVER
("patch-equilibrium-solver-v2-candidate", mechanism factory, 11.19 method
improvement round judged the §13.1/11.19 way).

ADOPTION POINTER (coordinator ruling, published 912f688f): this
candidate was ADOPTED -- its machinery now LIVES in
patch_equilibrium.solve_equilibrium as "patch-equilibrium-solver-v2"
(phase 1 = the v1 machinery verbatim on law-passing terminations,
phase 2 = the Newton-by-FD-diagonal continuation). THIS FILE IS KEPT
UNCHANGED as the historical candidate record; calling its
solve_equilibrium now routes through the adopted v2 (its phase 1 calls
the promoted solver), so it measures the same physics.

WHAT THE EVIDENCE SUPPORTS (the choice, documented):
The S1 scale-resolution study measured the incumbent's stagnation floor on
large-scale loaded solves: the star at 1.5x/2.0x stagnates at 1.45e-6 /
2.49e-6 N -- OVER the packet's 1e-6 N free-residual law -- with terminal
status "stagnated / decrease_below_machine_scale". The incumbent's
machinery (patch_equilibrium.solve_equilibrium, the lab's discipline:
scalar preconditioner P = 1/gamma_max, Armijo-on-U, stagnation trigger
"per-step decrease <= STAGNATION_FRAC*eps*max(|U|,1)") stops while the
SLOW, SOFT directions of the near-equilibrium still carry resolvable
curvature: a scalar-P gradient step is bounded by the STIFFEST local
scale, so the per-step energy decrease falls below the machine-scale
trigger while the residual is still orders of magnitude from the
machine floor. The floor grows with the energy scale (S1: 7.3e-7 N at
|U|=6.3 J -> 2.5e-6 N at |U|=25.1 J), exactly the sqrt(eps*|U|*kappa)
law.

THE CANDIDATE (convergence machinery ONLY; the energy law, the packet's
1e-6 N acceptance law and the refusal semantics are UNCHANGED):
  Phase 1 -- the incumbent, verbatim: the candidate CALLS
      patch_equilibrium.solve_equilibrium and, whenever the incumbent's
      own termination satisfies the packet's acceptance law
      (free_residual <= 1e-6 N), returns that result UNCHANGED. Same
      answers to the last bit on everything the incumbent already
      solves: a candidate that shifts converged answers is broken, not
      better.
  Phase 2 -- engaged ONLY when the incumbent terminates with the
      residual OVER the packet's law (stagnated/step_limit/
      no_descent_step at a failing residual): NEWTON-BY-FINITE-
      DIFFERENCE DIAGONAL PRECONDITIONING on the FREE vertices (the
      Jacobi blocks of dF_free/dx_free by exact-force central columns;
      the free-vertex set is tiny -- welded seams/apexes -- so the
      Jacobian is cheap), giving the step its LOCAL gradient scale
      instead of the global 1/gamma_max. Same discipline around it:
      GUARD_FRAC first-trial cap, geometric backtracking with
      restart-on-stall and a halved step ceiling, energy guard (a
      trial may not increase U by more than the incumbent's own
      machine-scale noise constant), residual-nonneutral acceptance
      (the residual may not increase), and the SAME five named
      terminal states: STATIONARY at the incumbent's own residual_tol,
      STAGNATED under the same machine-scale decrease trigger,
      NO_DESCENT_STEP when no acceptable step survives the restarts,
      STEP_LIMIT at the matched budget.

NO ADOPTION HERE: this module is a CANDIDATE. Adoption (chain
regeneration, pin changes, piece-record domain edits) is a separate
decision backed by the frozen-suite method comparison.

CPU only; numpy + stdlib; the law of record is imported, never edited.
"""
from __future__ import annotations

import hashlib
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
_TOOLS = _HERE.parent
_LAB = _TOOLS / "membrane_scale_lab"
for _p in (str(_TOOLS), str(_LAB)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import patch_equilibrium as pe                            # noqa: E402 incumbent
from surface_energy_reference import evaluate_surface      # noqa: E402 law
from overdamped_descent import (                           # noqa: E402 constants
    ARMIJO_C1, BACKTRACK_FACTOR, MAX_BACKTRACKS, GUARD_FRAC,
    RESIDUAL_TOL_FRAC, STAGNATION_FRAC,
    STATIONARY, STAGNATED, STEP_LIMIT, NO_DESCENT_STEP)

CANDIDATE_ID = "patch-equilibrium-solver-v2-candidate"

# THE JUDGE, quoted from the packet's acceptance law -- never moved here:
PACKET_LAW_FREE_RESIDUAL_N = 1e-6

# candidate machinery constants (algorithm choices, audited below):
FD_H_FRAC = 1.0e-7          # FD column step as a fraction of mean_edge
RESTARTS = 4                # stall restarts with a halved step ceiling
ENERGY_GUARD_FRAC = STAGNATION_FRAC   # U may not rise above the SAME
                                      # machine-scale noise constant the
                                      # incumbent's trigger uses


def solution_hash(result: pe.EquilibriumResult) -> str:
    """Determinism observable: sha256 over the final positions and pin
    reactions (canonical float64 bytes)."""
    h = hashlib.sha256()
    h.update(np.ascontiguousarray(result.positions).tobytes())
    if result.reaction_forces is not None:
        h.update(np.ascontiguousarray(result.reaction_forces).tobytes())
    h.update(np.float64(result.free_residual).tobytes())
    return h.hexdigest()[:16]


def solve_equilibrium(positions, faces, gamma, fixed_vertices, loads,
                      max_steps: int = pe.DEFAULT_MAX_STEPS,
                      max_backtracks: int = MAX_BACKTRACKS,
                      force_continuation: bool = False) -> pe.EquilibriumResult:
    """Same interface, statuses and refusals as the incumbent
    solve_equilibrium. Phase 1 = the incumbent verbatim; phase 2 = the
    Newton-Jacobi continuation, engaged only on an incumbent termination
    whose residual is OVER the packet's 1e-6 N law (or forced, for
    diagnostics only). force_continuation is a DIAGNOSTIC override for
    the method comparison's slack measurements -- the qualified candidate
    never uses it."""
    # Phase 1: the incumbent, verbatim -- every refusal, validation and
    # named terminal state comes from the law's own solver.
    r1 = pe.solve_equilibrium(positions, faces, gamma, fixed_vertices,
                              loads, max_steps=max_steps,
                              max_backtracks=max_backtracks)
    incumbent_ok = r1.free_residual <= PACKET_LAW_FREE_RESIDUAL_N
    if incumbent_ok and not force_continuation:
        audit = dict(r1.constants_audit)
        audit["candidate"] = {
            "candidate_id": CANDIDATE_ID,
            "phase2": "not_engaged",
            "why": "incumbent termination already satisfies the packet's "
                   "1e-6 N free-residual law; the result is returned "
                   "unchanged (same answers, to the last bit)",
        }
        return replace(r1, constants_audit=audit)
    return _continue(r1, faces, gamma, max_steps - int(r1.n_accepted),
                     max_backtracks, forced=force_continuation)


def _continue(r1: pe.EquilibriumResult, faces, gamma, budget: int,
              max_backtracks: int, forced: bool) -> pe.EquilibriumResult:
    """Phase 2: Newton-by-FD-diagonal continuation from the incumbent's
    endpoint. Same law, same named states, tightened machinery."""
    faces = np.asarray(faces, dtype=np.int64)
    gamma = np.asarray(gamma, dtype=np.float64)
    pos = np.array(r1.positions, dtype=np.float64)
    n_vertices = pos.shape[0]
    fixed = np.zeros(n_vertices, dtype=bool)
    fixed[r1.fixed_indices] = True
    free = ~fixed
    f_load = np.asarray(r1.loads, dtype=np.float64)

    idx = np.flatnonzero(free)
    n_free = idx.size

    # the same scales the incumbent derives (same formulas, same constants)
    tri = faces
    a, b, c = pos[tri[:, 0]], pos[tri[:, 1]], pos[tri[:, 2]]
    e_sq = np.stack([np.sum((b - a) ** 2, axis=1),
                     np.sum((c - b) ** 2, axis=1),
                     np.sum((a - c) ** 2, axis=1)])
    mean_edge = float(np.mean(np.sqrt(e_sq)))
    min_edge = float(np.sqrt(e_sq.min()))
    residual_tol = RESIDUAL_TOL_FRAC * mean_edge
    P = 1.0 / float(np.max(gamma))
    fd_h = FD_H_FRAC * mean_edge

    ev = evaluate_surface(pos, faces, gamma)
    F = ev.vertex_forces + f_load

    result = replace(r1)     # carries positions/energy/... from phase 1
    result.step_trail = list(r1.step_trail)

    def _res(Fx: np.ndarray) -> float:
        return float(np.max(np.abs(P * Fx[free]))) if n_free else 0.0

    res = _res(F)
    u_now = float(ev.energy) - float(np.sum(f_load * pos))
    u_noise = ENERGY_GUARD_FRAC * np.finfo(np.float64).eps * max(abs(u_now), 1.0)
    trail = []

    if budget <= 0:
        audit = dict(result.constants_audit)
        audit["candidate"] = {
            "candidate_id": CANDIDATE_ID,
            "phase2": "not_engaged_budget_exhausted",
            "why": "the incumbent consumed the matched step budget "
                   "(the case's own budget law); nothing continued",
        }
        return replace(result, constants_audit=audit)

    stall_restarts = 0
    status = ""
    while budget > 0:
        res = _res(F)
        if res <= residual_tol:
            status = STATIONARY
            break
        # ── Newton-by-FD diagonal system on the FREE vertices ──
        k = n_free
        cols = np.zeros((3 * k, 3 * k))
        F0 = F[idx].reshape(3 * k)              # rows: free force components
        for vi in range(k):
            for dim in range(3):
                xp = pos.copy()
                xp[idx[vi], dim] += fd_h
                Fp = evaluate_surface(xp, faces, gamma).vertex_forces + f_load
                cols[:, vi * 3 + dim] = (Fp[idx].reshape(3 * k) - F0) / fd_h
        try:
            d_free = np.linalg.solve(cols, -F0)
        except np.linalg.LinAlgError:
            d_free = None
        if d_free is None or not np.all(np.isfinite(d_free)):
            # singular/ill-conditioned Jacobian: fall back to the
            # incumbent's own gradient direction for this step (documented;
            # same law, machinery fallback)
            d_free = -(P * F0)
        d = np.zeros((n_vertices, 3))
        d[idx] = d_free.reshape(k, 3)
        if fixed.any():
            d[fixed] = 0.0                       # exact pin (same law)
        d_norm = float(np.max(np.linalg.norm(d, axis=1))) if k else 0.0
        if d_norm == 0.0:
            status = STATIONARY
            break

        # ── line search: same guard, same Armijo/geometric gate, plus the
        # energy guard and residual-nonincrease acceptance ──
        accepted = False
        alpha_ceiling = min(1.0, (GUARD_FRAC * min_edge) / d_norm)
        f_dot_d = float(-np.sum(F[idx] * d[idx]))       # >= 0 for descent
        for _restart in range(RESTARTS + 1):
            alpha = alpha_ceiling
            for _bt in range(max_backtracks + 1):
                trial = pos + alpha * d
                try:
                    ev_plus = evaluate_surface(trial, faces, gamma)
                except Exception:                        # geometry gate
                    alpha *= BACKTRACK_FACTOR
                    continue
                u_plus = (float(ev_plus.energy)
                          - float(np.sum(f_load * trial)))
                F_plus = ev_plus.vertex_forces + f_load
                res_plus = _res(F_plus)
                # accept: energy may not increase beyond the machine-scale
                # noise constant, and the residual may not increase
                if (u_plus <= u_now + u_noise
                        and (res_plus <= res or u_plus < u_now)):
                    accepted = True
                    break
                alpha *= BACKTRACK_FACTOR
            if accepted:
                break
            alpha_ceiling *= BACKTRACK_FACTOR            # restart, halved
            if alpha_ceiling <= 0.0:
                break
        if not accepted:
            status = NO_DESCENT_STEP
            result.reason = NO_DESCENT_STEP
            break

        prev_u = u_now
        pos = trial
        ev = ev_plus
        F = F_plus
        u_now = u_plus
        res = res_plus
        budget -= 1
        result.n_accepted += 1
        result.step_trail.append({"alpha": alpha, "phase": "candidate",
                                  "f_dot_d": f_dot_d,
                                  "U_before": prev_u, "U_after": u_now,
                                  "free_residual": res})
        trail.append({"alpha": alpha, "free_residual_after": res})
        result.positions = pos
        result.energy = u_now
        result.surface_energy = float(ev.energy)
        result.energies.append(u_now)
        result.free_residual = res
        if res <= residual_tol:
            status = STATIONARY
            break
        if prev_u - u_now <= STAGNATION_FRAC * np.finfo(np.float64).eps \
                * max(abs(prev_u), 1.0):
            status = STAGNATED
            result.reason = "decrease_below_machine_scale"
            break
    if status == "":
        status = STEP_LIMIT

    result.status = status
    if status == STATIONARY:
        result.reason = ""
    # reactions at the FINAL geometry, pin-APPLIED sign (same convention)
    if fixed.any():
        result.reaction_forces = -F[fixed].copy()
    result.free_residual = _res(F)
    audit = dict(result.constants_audit)
    audit["candidate"] = {
        "candidate_id": CANDIDATE_ID,
        "phase2": "engaged_forced" if forced else "engaged",
        "machinery": "Newton-by-FD-diagonal (Jacobi blocks of dF_free/"
                     "dx_free by exact-force columns) with restart-on-"
                     "stall, energy guard at the incumbent's own "
                     "machine-scale noise constant, residual-nonincrease "
                     "acceptance; the packet's 1e-6 N law is the judge "
                     "and was never moved",
        "fd_h_wu": fd_h,
        "incumbent_free_residual_N": r1.free_residual,
        "candidate_free_residual_N": result.free_residual,
        "continuation_steps": result.n_accepted - r1.n_accepted,
        "terminal_status": status,
    }
    return replace(result, constants_audit=audit)
