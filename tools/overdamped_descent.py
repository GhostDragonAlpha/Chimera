"""overdamped_descent.py -- THE OVERDAMPED OPTIMIZATION LAW. (G01-R4)

SUPERSEDES the R3 implementation for publication (R3 history preserved:
docs/evidence/g01/r3_snapshot/, hash-verified; R3's convergence evidence
remains valid — the same descent/acceptance machinery, corrected units).

R4 UNITS TABLE (carried explicitly; the R3 audit found min_edge^2/gamma_max
is wu^4/J, not wu^2/J -- the error was numerically masked at unit scale):

    position   x      [wu]            (world unit; never redefined)
    gamma      gamma  [J/wu^2]        (energy per area; never redefined)
    energy     U      [J]
    force      F      [J/wu]          (exact gradient of U)
    preconditioner P   [wu^2/J]    P = 1/gamma_max  (dimensionally exact:
               multiplying a force by an inverse energy density gives a
               length:  [wu^2/J]·[J/wu] = [wu])
    direction  p = P·F [wu]
    step param alpha  dimensionless   x+ = x + alpha*p
    residual   R = max_free ||P.F||_inf  [wu]  (the stationarity measure)

NO TIME VARIABLE EXISTS ANYWHERE IN THIS MODULE. Iterations are ITERATIONS;
they are never elapsed simulation time, and no 'dt' appears in any
signature. gamma_max = 0 is handled BEFORE any division (R4-U1).

SCOPE (unchanged from R3): an OPTIMIZATION experiment on U = sum gamma_t
A_t. No inertia, no velocity, no claim about inertial dynamics (handoff
6.0 correction 3 stands). Constant-gamma energy has NO remembered rest
shape; nothing here 'restores' a pose.

ACCEPTANCE LAW (unchanged in substance from R3, preregistered D3): a
trial x+ = x + alpha*p is ACCEPTED iff
  (a) Armijo sufficient decrease  U(x+) <= U(x) - c1*alpha*<F, p>,
      c1 = 1e-4, <F, p> = F^T P F >= 0 computed from the CURRENT force and
      the FIXED direction p;
  (b) geometry validity -- evaluate_surface(x+, ...) succeeds under the
      reference's OWN named-refusal floor (64*eps*max_edge^2).
Rejected trials backtrack alpha <- alpha/2 (budget 50). Exhaustion ends
the step with the named refusal "no_descent_step", geometry unchanged.

STOPPING TAXONOMY (R4-U2, preregistered): a run ends in exactly one of
FIVE named states --
  stationary        free-DOF residual ||P.F_free||_inf <= RESIDUAL_TOL
                    (residual-based; a small step or small decrease alone
                    NEVER establishes this). Pinned vertices are excluded
                    by construction; the force the pins carry is reported
                    separately as reaction forces (never added to the
                    test, never silently dropped).
  stagnated         accepted-step decrease below machine scale (8*eps*
                    max(U,1)) WITHOUT the residual test passing:
                    numerical stagnation reported AS stagnation.
  step_limit        iteration budget exhausted.
  no_descent_step   backtracking exhaustion (geometry bit-unchanged).
  invalid_surface   the reference's refusal, reason passed through.
R3's single word 'converged' is retired and SPLIT into stationary vs
stagnated: small displacement or small decrease alone is not equilibrium.

CONSTANTS AUDIT (R4-U3): every constant below is a NUMERICAL ALGORITHM
CHOICE of the optimizer, none is a derived physical constant, none was
tuned to make a fixture pass --
  ARMIJO_C1          1e-4   standard backtracking-Armijo coefficient (the
                            literature's conservative end).
  BACKTRACK_FACTOR   0.5    bracket halving.
  MAX_BACKTRACKS     50     budget; spans ~10^15 in alpha -- deep enough
                            for any admissible scale on these fixtures.
  GUARD_FRAC         1e-3   the demoted R2/R3 displacement bound, kept
                            ONLY as the initial trial-scale cap (first
                            trial moves <= half a min_edge).
   RESIDUAL_TOL_FRAC  1e-12  stationarity length scale, x mean_edge_length
                            (A1-6: translation/rotation invariant; the old
                            `max(1, max|coord|)` was origin-dependent)
  STAGNATION_FRAC    8      machine-precision decrease scale (R3
                            stagnation amendment, f64-derived).
  DEFAULT_MAX_STEPS  200    iteration budget (a resource cap).

numpy + stdlib only; depends only on surface_energy_reference (the
certified law of record). No new tolerance, no material constant, no new
degeneracy floor.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from surface_energy_reference import (
    Evaluation,
    InvalidSurface,
    evaluate_surface,
    EPS as _EPS,
)

# Re-exported for checks/reports: the f64 unit roundoff the stagnation law
# is derived from.
EPS = _EPS

__all__ = [
    "DescentResult", "descent_step", "preconditioner", "run_descent",
    "STATIONARY", "STAGNATED", "STEP_LIMIT", "NO_DESCENT_STEP",
    "INVALID_SURFACE",
]

# The five named terminal states (R4-U2). Machine-readable; nothing else.
STATIONARY = "stationary"
STAGNATED = "stagnated"
STEP_LIMIT = "step_limit"
NO_DESCENT_STEP = "no_descent_step"
INVALID_SURFACE = "invalid_surface"

ARMIJO_C1 = 1.0e-4          # algorithm choice (see module audit)
BACKTRACK_FACTOR = 0.5      # algorithm choice
MAX_BACKTRACKS = 50         # algorithm choice
GUARD_FRAC = 1.0e-3         # algorithm choice (demoted R2/R3 bound)
RESIDUAL_TOL_FRAC = 1.0e-12  # algorithm choice (stopping scale)
STAGNATION_FRAC = 8.0       # algorithm choice (f64-derived decrease scale)
DEFAULT_MAX_STEPS = 200     # algorithm choice


@dataclass
class DescentResult:
    """One run_descent() outcome. `status` is exactly one of the five named
    states above; a caller can switch on it. There is no implicit 'ok'."""
    status: str
    reason: str                      # "" or the named refusal reason
    positions: np.ndarray            # final geometry [wu]
    energy: float                    # final U [J]
    energies: list = field(default_factory=list)   # U after each accepted step [J]
    free_residual: float = 0.0       # final free-DOF residual [wu]
    reaction_forces: np.ndarray | None = None      # (nPinned,3) [J/wu]
    # SIGN CONVENTION (R4, corrected after the bogus 'balance' identity was
    # caught in review): reaction_forces[i] = -F_i(pinned vertex, FINAL
    # geometry) -- the force each pin must APPLY to hold its vertex. The
    # always-true invariance law is sum(F_all) = 0; at true stationarity
    # the NET pin load vanishes (sum(reaction) = 0) while individual
    # boundary pins carry the local surface tension.
    fixed_indices: list = field(default_factory=list)
    n_accepted: int = 0
    n_trials: int = 0
    step_trail: list = field(default_factory=list)  # per accepted step:
    # {alpha, f_dot_p, U_before, U_after} -- the record R4f verifies
    # POST-HOC (the Armijo inequality is re-checked from this trail, not
    # trusted from the acceptor).
    last_step_scale: float = 0.0     # alpha of the last accepted trial (1)
    last_displacement_norm: float = 0.0            # [wu]
    max_displacement_norm: float = 0.0             # [wu]
    constants_audit: dict = field(default_factory=dict)  # the R4-U3 record


def preconditioner(positions, faces, gamma) -> float:
    """P = 1/gamma_max [wu^2/J]; the dimensionally exact inverse energy
    density. gamma_max = 0 is handled BEFORE division: the caller only
    reaches here with max(gamma) > 0 (run_descent returns `stationary`
    first -- F is exactly zero and no preconditioner is needed)."""
    gam = np.asarray(gamma, dtype=np.float64)
    gamma_max = float(np.max(gam)) if gam.size else 0.0
    if gamma_max <= 0.0:                     # R4-U1: before any division
        raise InvalidSurface_check_never_called()  # pragma: no cover
    return 1.0 / gamma_max


class InvalidSurface_check_never_called(Exception):
    """Guard: run_descent must never reach the zero-gamma preconditioner
    branch. If this raises, the zero-gamma handling was bypassed -- a bug
    report, not a user-facing refusal."""


def descent_step(positions, faces, gamma, preconditioner_value: float,
                 alpha: float, fixed_vertices=None):
    """ONE trial step. See module docstring for the acceptance law.

    Returns (accepted, x_plus, energy_plus, reason). `reason` is "" on
    acceptance; on rejection it is the reference's own named refusal string
    for invalid trial geometry, or "armijo_not_met" for a valid trial that
    fails the sufficient-decrease condition (a).

    Pinned vertices receive EXACTLY zero displacement (R3 D5, unchanged):
    the direction is zeroed at the fixed indices before the geometry is
    formed -- equality by construction, not a clamp after drift.

    A1-7: preconditioner_value and alpha are validated at the door --
    non-positive or non-finite values are refused with a NAMED ValueError
    before any geometry is touched.
    """
    # A1-7: validate optimizer arguments at the door (reject 0, -1, nan, inf
    # preconditioner or alpha before any geometry is formed or evaluated).
    for label, v in (("preconditioner_value", preconditioner_value),
                     ("alpha", alpha)):
        try:
            fv = float(v)
        except (TypeError, ValueError):
            raise ValueError(
                f"{label} must be a finite number, got {v!r}")
        if not math.isfinite(fv) or fv <= 0:
            raise ValueError(
                f"{label} must be positive and finite, got {v}")
    pos = np.asarray(positions, dtype=np.float64)
    ev = evaluate_surface(pos, faces, gamma)   # current state must be valid
    F = ev.vertex_forces                       # [J/wu]
    p = preconditioner_value * F               # [wu]
    if fixed_vertices is not None and len(fixed_vertices) > 0:
        p = p.copy()
        p[_as_fixed_mask(pos, fixed_vertices)] = 0.0   # exact pin

    trial = pos + alpha * p
    try:
        ev_plus = evaluate_surface(trial, faces, gamma)
    except InvalidSurface as ex:               # (b): the reference's own law
        return False, None, None, ex.reason

    f_dot_p = float(np.sum(F * p))             # >= 0 by construction of P
    if not (ev_plus.energy <= ev.energy - ARMIJO_C1 * alpha * f_dot_p):
        return False, None, None, "armijo_not_met"   # (a) failed, named
    return True, trial, ev_plus.energy, ""


def _free_residual(ev: Evaluation, free_mask: np.ndarray,
                   P: float) -> float:
    """The free-DOF residual max_free ||P.F||_inf [wu]. Pinned vertices are
    excluded BY CONSTRUCTION (mask), not clamped after the fact."""
    if not free_mask.any():
        return 0.0
    return float(np.max(np.abs(P * ev.vertex_forces[free_mask])))


def run_descent(positions, faces, gamma, fixed_vertices=None,
                max_steps: int = DEFAULT_MAX_STEPS,
                max_backtracks: int = MAX_BACKTRACKS) -> DescentResult:
    """Run the derived optimization until one of the FIVE named states.

    fixed_vertices: indices pinned to EXACTLY zero displacement every step.
    max_backtracks: halvings allowed PER STEP before no_descent_step.

    Units per the R4 table: positions [wu], gamma [J/wu^2], energies [J],
    residual/reaction [J/wu] and [wu] as labeled on DescentResult.
    """
    pos = np.asarray(positions, dtype=np.float64)
    try:
        ev = evaluate_surface(pos, faces, gamma)
    except InvalidSurface as ex:               # named pass-through (R4-U2.5)
        return DescentResult(status=INVALID_SURFACE, reason=ex.reason,
                             positions=pos, energy=float("nan"),
                             constants_audit=_audit())

    fixed = (np.zeros(pos.shape[0], dtype=bool) if fixed_vertices is None
             else _as_fixed_mask(pos, fixed_vertices))
    free_mask = ~fixed

    # Reaction forces (reported, never part of the stationarity test): the
    # surface force accumulated on pinned vertices, signed as the pin's
    # APPLIED reaction at close-out (see DescentResult note).
    reaction = (ev.vertex_forces[fixed].copy() if fixed.any() else None)

    gam = ev.gamma
    gamma_max = float(np.max(gam)) if gam.size else 0.0
    if gamma_max <= 0.0:                       # R4-U1: BEFORE any division
        # F is exactly zero (D2): stationary with zero steps, no P needed.
        return _finish(DescentResult(
            status=STATIONARY, reason="", positions=pos, energy=ev.energy,
            energies=[ev.energy], free_residual=0.0,
            reaction_forces=(reaction * 0.0 if reaction is not None else None),
            fixed_indices=[int(i) for i in np.flatnonzero(fixed)],
            n_accepted=0, n_trials=0, constants_audit=_audit()), ev,
            free_mask, 0.0)

    P = 1.0 / gamma_max                        # [wu^2/J] -- dimensionally exact

    # A1-6: mean-edge-length is the translation- and rotation-invariant,
    # scale-covariant geometric length that anchors the stationarity
    # tolerance. The old law `max(1, max|coord|)` imposed a one-world-unit
    # floor and was origin-dependent: the same triangle at the origin and
    # translated by 1e12 produced different verdicts. mean_edge is the
    # arithmetic mean of all edge lengths; no 1-unit floor is needed
    # because a zero-edge mesh is already refused by the reference.
    # min_edge for the step-scale guard (a GUARD, not a descent proof)
    tri = np.asarray(faces)
    a, b, c = pos[tri[:, 0]], pos[tri[:, 1]], pos[tri[:, 2]]
    e_sq = np.stack([np.sum((b - a) ** 2, axis=1),
                     np.sum((c - b) ** 2, axis=1),
                     np.sum((a - c) ** 2, axis=1)])
    mean_edge = float(np.mean(np.sqrt(e_sq)))
    min_edge = float(np.sqrt(e_sq.min()))
    residual_tol = RESIDUAL_TOL_FRAC * mean_edge      # [wu]

    result = DescentResult(status="", reason="", positions=pos,
                           energy=ev.energy, energies=[ev.energy],
                           free_residual=_free_residual(ev, free_mask, P),
                           reaction_forces=reaction,
                           fixed_indices=[int(i) for i in
                                          np.flatnonzero(fixed)],
                           constants_audit=_audit())

    for _ in range(max_steps):
        F = ev.vertex_forces
        p = P * F
        if fixed.any():
            p = p.copy()
            p[fixed] = 0.0                      # exact pin
        p_norm = float(np.max(np.linalg.norm(p, axis=1))) if p.size else 0.0

        if p_norm == 0.0:                       # exactly stationary (D2)
            result.status = STATIONARY
            result.free_residual = _free_residual(ev, free_mask, P)
            break

        # step-scale GUARD: first trial moves at most GUARD_FRAC*min_edge
        alpha_max = min(1.0, (GUARD_FRAC * min_edge) / p_norm)

        accepted = False
        alpha = alpha_max
        for _bt in range(max_backtracks + 1):
            result.n_trials += 1
            ok, x_plus, u_plus, why = descent_step(pos, faces, gam, P,
                                                   alpha, fixed_vertices)
            if ok:
                accepted = True
                break
            alpha *= BACKTRACK_FACTOR

        if not accepted:                        # (iv) named refusal (R4-U2)
            result.status = NO_DESCENT_STEP
            result.reason = "no_descent_step"
            break

        d = x_plus - pos
        step_norm = float(np.max(np.linalg.norm(d, axis=1)))
        prev_energy = result.energy
        result.positions = x_plus
        result.energy = u_plus
        result.energies.append(u_plus)
        result.n_accepted += 1
        result.step_trail.append({
            "alpha": alpha,
            "f_dot_p": float(np.sum(F * p)),
            "U_before": prev_energy, "U_after": u_plus,
        })
        result.last_step_scale = alpha
        result.last_displacement_norm = step_norm
        result.max_displacement_norm = max(result.max_displacement_norm,
                                           step_norm)
        pos = x_plus
        ev = evaluate_surface(pos, faces, gam)   # cannot fail: (b) verified

        # R4-U2.1 FIRST (residual-based stationarity, free DOFs only):
        res = _free_residual(ev, free_mask, P)
        result.free_residual = res
        if res <= residual_tol:
            result.status = STATIONARY
            break

        # R4-U2.2 stagnation (decrease-based) -- reported AS stagnation,
        # never as equilibrium:
        if prev_energy - u_plus <= STAGNATION_FRAC * EPS * max(prev_energy,
                                                               1.0):
            result.status = STAGNATED
            result.reason = "decrease_below_machine_scale"
            break
    else:
        result.status = STEP_LIMIT               # (iii) budget exhausted

    if result.status == "":                      # pragma: no cover
        result.status = STEP_LIMIT

    # Reaction forces are reported for the FINAL geometry (R4 fix, exposed
    # by r4b: the run may accept steps after the initial evaluation, so the
    # initial-state snapshot would misreport what the pins now carry),
    # with the pin's APPLIED sign: reaction = -F(pinned, final).
    if fixed.any():
        result.reaction_forces = -ev.vertex_forces[fixed].copy()
    return result


def _as_fixed_mask(pos, fixed_vertices) -> np.ndarray:
    """Validate the pin list. Out-of-range, FRACTIONAL, or repeated indices
    are a named ValueError (a pinned vertex list is a claim about the mesh;
    a bad claim is refused, not clamped). A1-7: fractional indices are
    checked BEFORE integer conversion -- the old np.asarray(..., int64)
    truncated [0.9] to 0 silently pinning vertex 0; the law now refuses."""
    raw = np.asarray(fixed_vertices)
    if raw.ndim != 1:
        raise ValueError("fixed_vertices must be a 1-D index list")
    # A1-7: finite + integral BEFORE the int cast. numpy floor-then-equal is
    # exact for representable floats; a fractional index is a refuse.
    try:
        raw_f = raw.astype(np.float64)
    except (TypeError, ValueError):
        raise ValueError("fixed_vertices indices must be real numbers")
    if not np.all(np.isfinite(raw_f)):
        raise ValueError("fixed_vertices must be finite")
    if raw_f.size and not np.all(np.equal(raw_f, np.floor(raw_f))):
        bad = raw_f[np.where(~np.equal(raw_f, np.floor(raw_f)))[0]]
        raise ValueError(
            f"fixed_vertices contains a fractional index {bad.tolist()} -- "
            f"a vertex index is an integer; refusing to truncate it")
    idx = raw_f.astype(np.int64)
    if idx.size and (idx.min() < 0 or idx.max() >= pos.shape[0]):
        raise ValueError(f"fixed_vertices index out of [0,{pos.shape[0]})")
    if len(set(idx.tolist())) != idx.size:
        raise ValueError("fixed_vertices contains repeats -- a repeated pin "
                         "is an ambiguous claim, refused")
    mask = np.zeros(pos.shape[0], dtype=bool)
    mask[idx] = True
    return mask


def _audit() -> dict:
    """The R4-U3 constants audit, attached to every result: the caller can
    see exactly which algorithm choices produced the run."""
    return {
        "kind": "numerical_algorithm_choices_not_physical_constants",
        "ARMIJO_C1": ARMIJO_C1,
        "BACKTRACK_FACTOR": BACKTRACK_FACTOR,
        "MAX_BACKTRACKS": MAX_BACKTRACKS,
        "GUARD_FRAC": GUARD_FRAC,
        "RESIDUAL_TOL_FRAC": RESIDUAL_TOL_FRAC,
        "STAGNATION_FRAC": STAGNATION_FRAC,
        "DEFAULT_MAX_STEPS": DEFAULT_MAX_STEPS,
    }


def _finish(result: DescentResult, ev: Evaluation, free_mask,
            P: float) -> DescentResult:
    """Close out a run that took zero steps: residual is measured, not
    assumed."""
    result.free_residual = _free_residual(ev, free_mask, P) if P else 0.0
    return result
