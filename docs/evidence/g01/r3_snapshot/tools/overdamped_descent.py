"""overdamped_descent.py -- THE DERIVED OVERDAMPED DESCENT LAW. (G01-R3, Task 1)

SCOPE (declared first, per the R3 preregistration): this is an OPTIMIZATION
experiment on U = sum_t gamma_t A_t. It has NO velocity state, NO inertia, and
predicts NOTHING about inertial dynamics. Physical dynamics remain
integrator-dependent (GPU handoff section 6.0). Nothing here repairs,
smooths, or "restores" a pose: constant-gamma energy has NO remembered rest
shape (handoff 6.0, correction 1).

WHY THIS MODULE EXISTS: the R2 handoff proposed the timestep gate
    dt * max||F|| <= 1e-3 * min_edge
as if bounding displacement per step implied monotone energy descent. It does
not: a bound on HOW FAR a step moves says nothing about WHICH WAY it moves,
and force is not velocity -- force needs an explicit mobility mapping before
it becomes motion. R3 replaces the implied claim with a derived update whose
descent property is VERIFIED at every step, not assumed from a bound.

THE DERIVATION (units carried; wu = world unit, J = energy unit, gamma in
J/wu^2 so that force = -grad U is in J/wu):

  Energy        U(x) = sum_t gamma_t * A_t(x)                    [J]
  Force         F(x) = -grad_x U(x), exact per G01 (reference)   [J/wu]
  Mobility      a diagonal, constant M = m * I, m > 0            [wu^2/J]
  Direction     p = M F(x)                                       [wu]
  Trial         x+ = x + s p,  0 < s <= s_max                    [wu]

  m has units wu^2/J: multiplying a force [J/wu] by m [wu^2/J] yields a
  length [wu]. Any constant positive m converges to the same stationary
  point (it only rescales the parameterization); the DEFAULT below derives
  one from the geometry so no magic number is installed.

  DEFAULT mobility (derived, not tuned): the natural force scale on a
  triangle of edge L is |F| ~ gamma_max * L (the area gradient of a face of
  size L^2 scales like L). A displacement of order L per full step
  corresponds to m0 = L^2 / gamma_max (dividing by gamma_max makes the
  scale energy-parameter-free). gamma_max = 0 is the stationary case
  (F = 0 exactly, D2) and never reaches the division; the default returns
  1.0 there, documented as unused.

ACCEPTANCE (D3, preregistered): a trial x+ = x + s p is ACCEPTED iff

  (a) sufficient decrease   U(x+) <= U(x) - c1 * s * <F, p>,
      with c1 = 1e-4 (Armijo constant, declared), <F, p> = F^T M F >= 0
      computed from the CURRENT force and the FIXED direction p.
  (b) geometry validity     evaluate_surface(x+, ...) succeeds under the
      reference's OWN named-refusal law (the 64*eps*max_edge^2 floor). A
      trial that lands a face at/below the floor is REJECTED with the
      reference's own reason string -- never patched, never widened.

Otherwise the trial is rejected and s <- s/2 (backtracking), at most
`max_backtracks` = 50 halvings. If no trial in the budget satisfies (a)+(b),
the STEP ends REFUSED with reason "no_descent_step" and the geometry is
returned unchanged. Refusals are named; nothing is silently dropped.

STEP-SCALE GUARD (not a descent guarantee -- R3 removes that claim): the
first trial scale s_max = min(1.0, (1e-3 * min_edge) / max||p||) when
max||p|| > 0. The old bound survives ONLY as this guard inside the
backtracking search; descent is guaranteed by the ACCEPTANCE TEST (a)+(b),
not by the guard.

TERMINATION (D4, preregistered), exactly four named terminal states:
  converged          last accepted displacement norm <= 1e-12 * scene_scale
                     (scene_scale = max(1, max|coord|)), OR the initial
                     force is exactly zero (a stationary point, zero steps)
  step_limit_reached max_steps accepted steps taken without convergence
  no_descent_step    a step's entire backtracking budget failed (a) or (b)
  invalid_surface    the INITIAL geometry is refused by the reference; the
                     reference's reason string is carried unchanged.

numpy + stdlib only; depends only on surface_energy_reference (the certified
law of record) -- it invents no tolerance, no material constant, and no new
degeneracy floor.
"""
from __future__ import annotations

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
    "DescentResult", "descent_step", "default_mobility", "run_descent",
]

ARMIJO_C1 = 1.0e-4          # declared in the R3 preregistration (D3)
MAX_BACKTRACKS = 50         # halvings per step before no_descent_step
CONVERGENCE_FRAC = 1.0e-12  # of scene_scale (D4)
GUARD_FRAC = 1.0e-3         # the old bound, DEMOTED to a step-scale guard
DEFAULT_MAX_STEPS = 200
# Machine-precision stagnation (D4, stagnation amendment): an accepted step
# whose ACTUAL decrease is at float-rounding scale is the minimum in double
# precision -- continuing only wiggles in the last ulps. Derived from the
# accumulation depth (~3d terms in a triangle force, d<=4 on fixtures =>
# 8x headroom over 4*e), not tuned.
STAGNATION_FRAC = 8.0


@dataclass
class DescentResult:
    """One run_descent() outcome. `status` is one of the four named terminal
    states in the module docstring -- a caller can switch on it; there is no
    implicit 'ok'."""
    status: str                      # converged | step_limit_reached |
                                     # no_descent_step | invalid_surface
    reason: str                      # "" or the named refusal reason
    positions: np.ndarray            # final geometry (valid or the input)
    energy: float                    # final U (== initial if no accepted step)
    energies: list = field(default_factory=list)   # U after every accepted step
    n_accepted: int = 0
    last_step_scale: float = 0.0     # s of the last accepted trial
    last_displacement_norm: float = 0.0
    max_displacement_norm: float = 0.0
    n_trials: int = 0                # every backtracking trial evaluated


def default_mobility(positions, faces, gamma) -> float:
    """The geometry-derived scalar mobility m [wu^2/J]: m0 = min_edge^2 /
    gamma_max over the mesh (fixed vertices are pinned AFTER the multiply,
    so no incident-to-free-vertex restriction is needed for the default).

    gamma_max = 0 has F = 0 exactly (the stationary case, D2) and never
    reaches this branch's division in a run; the function returns 1.0 there,
    documented as unused."""
    pos = np.asarray(positions, dtype=np.float64)
    tri = np.asarray(faces)
    gam = np.asarray(gamma, dtype=np.float64)
    a, b, c = pos[tri[:, 0]], pos[tri[:, 1]], pos[tri[:, 2]]
    e_sq = np.stack([np.sum((b - a) ** 2, axis=1),
                     np.sum((c - b) ** 2, axis=1),
                     np.sum((a - c) ** 2, axis=1)])
    min_edge = float(np.sqrt(e_sq.min()))
    gamma_max = float(np.max(gam)) if gam.size else 0.0
    if gamma_max <= 0.0 or min_edge <= 0.0:
        return 1.0   # unused: gamma=0 has exactly zero forces (D2)
    return (min_edge * min_edge) / gamma_max


def descent_step(positions, faces, gamma, mobility: float, s: float,
                 fixed_vertices=None):
    """ONE trial step. See module docstring for the acceptance law.

    Returns (accepted, x_plus, energy_plus, reason). `reason` is "" on
    acceptance; on rejection it is the reference's own named refusal string
    for invalid trial geometry, or "armijo_not_met" for a valid trial that
    fails the sufficient-decrease condition (a).

    Pinned vertices (D5) receive EXACTLY zero displacement: the displacement
    field is zeroed at the fixed indices before the geometry is formed --
    equality by construction, not a clamp after drift.
    """
    pos = np.asarray(positions, dtype=np.float64)
    ev = evaluate_surface(pos, faces, gamma)   # current state must be valid
    F = ev.vertex_forces
    p = mobility * F                           # [wu]
    if fixed_vertices is not None and len(fixed_vertices) > 0:
        p = p.copy()
        p[np.asarray(fixed_vertices, dtype=np.int64)] = 0.0   # exact pin (D5)

    trial = pos + s * p
    try:
        ev_plus = evaluate_surface(trial, faces, gamma)
    except InvalidSurface as ex:               # (b): the reference's own law
        return False, None, None, ex.reason

    f_dot_p = float(np.sum(F * p))             # >= 0 by construction of M
    if not (ev_plus.energy <= ev.energy - ARMIJO_C1 * s * f_dot_p):
        return False, None, None, "armijo_not_met"   # (a) failed, named
    return True, trial, ev_plus.energy, ""


def run_descent(positions, faces, gamma, mobility=None, fixed_vertices=None,
                max_steps: int = DEFAULT_MAX_STEPS,
                max_backtracks: int = MAX_BACKTRACKS) -> DescentResult:
    """Run the derived descent until one of the four named terminal states.

    mobility: scalar m [wu^2/J]; default from default_mobility() on the input.
    fixed_vertices: indices pinned to EXACTLY zero displacement every step.
    max_backtracks: halvings allowed PER STEP before no_descent_step (the
      declared budget; the default is MAX_BACKTRACKS). Exposed because the
      budget-exhaustion refusal (D4-iii) is part of the certified behavior
      and must be demonstrable, not merely documented.
    """
    pos = np.asarray(positions, dtype=np.float64)
    try:
        ev = evaluate_surface(pos, faces, gamma)
    except InvalidSurface as ex:               # named pass-through
        return DescentResult(status="invalid_surface", reason=ex.reason,
                             positions=pos, energy=float("nan"))

    gam = ev.gamma
    if mobility is None:
        mobility = default_mobility(pos, faces, gam)

    scene_scale = max(1.0, float(np.abs(pos).max()))
    converge_tol = CONVERGENCE_FRAC * scene_scale

    # min_edge for the step-scale guard (a GUARD, not a descent proof)
    tri = np.asarray(faces)
    a, b, c = pos[tri[:, 0]], pos[tri[:, 1]], pos[tri[:, 2]]
    e_sq = np.stack([np.sum((b - a) ** 2, axis=1),
                     np.sum((c - b) ** 2, axis=1),
                     np.sum((a - c) ** 2, axis=1)])
    min_edge = float(np.sqrt(e_sq.min()))

    result = DescentResult(status="", reason="", positions=pos,
                           energy=ev.energy, energies=[ev.energy])

    for _ in range(max_steps):
        F = ev.vertex_forces
        p = mobility * F
        if fixed_vertices is not None and len(fixed_vertices) > 0:
            p = p.copy()
            p[np.asarray(fixed_vertices, dtype=np.int64)] = 0.0
        p_norm = float(np.max(np.linalg.norm(p, axis=1))) if p.size else 0.0

        if p_norm == 0.0:                      # exactly stationary (D2)
            result.status = "converged"
            break

        # step-scale GUARD: first trial displaces at most GUARD_FRAC*min_edge
        s_max = min(1.0, (GUARD_FRAC * min_edge) / p_norm)

        accepted = False
        s = s_max
        for _bt in range(max_backtracks + 1):
            result.n_trials += 1
            ok, x_plus, u_plus, why = descent_step(pos, faces, gam,
                                                   mobility, s,
                                                   fixed_vertices)
            if ok:
                accepted = True
                break
            s *= 0.5                           # backtracking, both reasons

        if not accepted:
            result.status = "no_descent_step"  # (iii) named refusal (D4)
            result.reason = "no_descent_step"
            break

        d = x_plus - pos
        step_norm = float(np.max(np.linalg.norm(d, axis=1)))
        prev_energy = result.energy
        result.positions = x_plus
        result.energy = u_plus
        result.energies.append(u_plus)
        result.n_accepted += 1
        result.last_step_scale = s
        result.last_displacement_norm = step_norm
        result.max_displacement_norm = max(result.max_displacement_norm,
                                           step_norm)
        pos = x_plus
        ev = evaluate_surface(pos, faces, gam)   # cannot fail: (b) verified

        if step_norm <= converge_tol:            # (i) converged (D4)
            result.status = "converged"
            break
        if prev_energy - u_plus <= STAGNATION_FRAC * EPS * max(prev_energy,
                                                               1.0):
            # machine-precision stagnation: the minimum in f64 (D4,
            # stagnation amendment) -- further accepted steps only wiggle
            # within float rounding
            result.status = "converged"
            break
    else:
        result.status = "step_limit_reached"     # (ii) budget exhausted (D4)

    if result.status == "":                      # pragma: no cover
        result.status = "step_limit_reached"
    return result
