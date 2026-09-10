"""optimizers.py -- a separately-labeled optimizer for the material-response DEMO only.

Iterations here are OPTIMIZATION steps, never physical time (PREREGISTRATION D1 membrane).
Simple steepest descent with Armijo backtracking over the elastic total energy, with vertices
masked fixed. Outcomes are labeled: stationary / stagnated / failed / max_iter.

This module exists to demonstrate a material response (section E); it is not part of the
constitutive law and not a simulator.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Tuple

import numpy as np

Objective = Callable[[np.ndarray], Tuple[float, np.ndarray]]


@dataclass
class DescentResult:
    outcome: str                  # stationary | stagnated | failed | max_iter
    x: np.ndarray                 # final positions
    energy: float
    iters: int
    accepted: int
    rejected_steps: int
    final_grad_norm: float
    history_energy: list = field(default_factory=list)
    history_grad: list = field(default_factory=list)


def gradient_descent(objective: Objective, x0: np.ndarray, fixed_mask: np.ndarray,
                     *, max_iter: int = 4000, alpha0: float = 0.125,
                     armijo_c: float = 1e-4, halving: float = 0.5,
                     max_halvings: int = 20, grad_tol_rel: float = 1e-10) -> DescentResult:
    """Steepest descent on the free (non-fixed) vertices with Armijo backtracking.

    stationary: gradient fell below grad_tol_rel of its first-to-nonzero scale.
    stagnated  : an Armijo line probe could not find ANY acceptable step this iteration.
    failed     : the objective refused a step (named refusal) at the probe point.
    max_iter   : step budget spent (which may still be a good approximation, caller decides).
    """
    x = np.array(x0, dtype=np.float64, copy=True)
    free = ~fixed_mask
    n_free = int(np.count_nonzero(free))
    E0, g0 = objective(x)
    if not np.all(np.isfinite(g0)):
        return DescentResult("failed", x, float(E0), 0, 0, 0, float("nan"))
    gscale = max(float(np.max(np.abs(g0[free]))), 1e-300)

    result = DescentResult("max_iter", x, float(E0), 0, 0, 0, float(gscale))
    result.history_energy.append(float(E0))
    result.history_grad.append(float(gscale))
    E = E0
    accepted = 0
    rejected = 0
    for it in range(1, max_iter + 1):
        E, g = objective(x)
        gn = float(np.max(np.abs(g[free]))) if n_free else 0.0
        if not np.all(np.isfinite(g)):
            return DescentResult("stagnated" if n_free == 0 else "failed",
                                 x, float(E), it, accepted, rejected, gn)
        if gn <= grad_tol_rel * gscale or (n_free == 0):
            return DescentResult("stationary", x, float(E), it, accepted, rejected, gn)
        p = np.zeros_like(x)
        p[free] = -g[free]
        dEdir = float(np.sum(g[free] * p[free]))    # negative for descent
        alpha = alpha0
        step_ok = False
        for _ in range(max_halvings + 1):
            xp = x + alpha * p
            try:
                Ep, _ = objective(xp)
            except Exception:
                # a named refusal at the probe point is a FAILED (not stagnated) outcome
                return DescentResult("failed", x, float(E), it, accepted, rejected, gn)
            if np.all(np.isfinite(Ep)) and Ep <= E + armijo_c * alpha * dEdir:
                step_ok = True
                break
            alpha *= halving
            rejected += 1
        if not step_ok:
            return DescentResult("stagnated", x, float(E), it, accepted, rejected, gn)
        x = xp
        E = Ep
        accepted += 1
        result.history_energy.append(float(E))
        result.history_grad.append(gn)
        result.x = np.array(x, copy=True)
        result.energy = float(E)
        result.iters = it
        result.accepted = accepted
        result.rejected_steps = rejected
        result.final_grad_norm = gn
    return result


def conjugate_gradient(objective: Objective, x0: np.ndarray, fixed_mask: np.ndarray,
                       *, max_iter: int = 4000, max_halvings: int = 20,
                       grad_tol_rel: float = 1e-10, restart_freq: int = 200) -> DescentResult:
    """Nonlinear Fletcher-Reeves CG on the free vertices with Armijo backtracking.

    Same outcome labels and semantics as gradient_descent (stationary / stagnated / failed /
    max_iter); gradient_descent remains for the battery-style probes. Steps are optimization
    steps, never physical time. Restart periodically to keep the search well-scaled.
    """
    x = np.array(x0, dtype=np.float64, copy=True)
    free = ~fixed_mask
    n_free = int(np.count_nonzero(free))
    E, g = objective(x)
    if not np.all(np.isfinite(g)):
        return DescentResult("failed", x, float(E), 0, 0, 0, float("nan"))
    gscale = max(float(np.max(np.abs(g[free]))), 1e-300)

    result = DescentResult("max_iter", x, float(E), 0, 0, 0, float(gscale))
    result.history_energy.append(float(E))
    result.history_grad.append(float(gscale))
    accepted = 0
    rejected = 0
    p = np.zeros_like(x)
    gp = None  # previous gradient (for the Fletcher-Reeves beta term)
    for it in range(1, max_iter + 1):
        E, g = objective(x)
        gj = g.copy()
        gj[~free] = 0.0
        gn = float(np.max(np.abs(g[free]))) if n_free else 0.0
        if not np.all(np.isfinite(g)):
            return DescentResult("failed", x, float(E), it, accepted, rejected, gn)
        if gn <= grad_tol_rel * gscale or n_free == 0:
            return DescentResult("stationary", x, float(E), it, accepted, rejected, gn)
        p[~free] = 0.0
        if it == 1 or gp is None or (it % restart_freq) == 0:
            p[free] = -g[free]
        else:
            beta = max(float(np.sum(g[free] * g[free]) /
                             max(float(np.sum(gp[free] * gp[free])), 1e-300)), 0.0)
            p[free] = -g[free] + beta * p[free]
        gp = g.copy()
        dEdir = float(np.sum(g[free] * p[free]))        # negative for descent
        if dEdir >= 0.0:
            p[free] = -g[free]
            dEdir = float(np.sum(g[free] * p[free]))
        alpha = min(1.0, 2.0 * max(abs(E), 1e-300) / max(-dEdir, 1e-300))
        step_ok = False
        for _ in range(max_halvings + 1):
            xp = x + alpha * p
            try:
                Ep, _ = objective(xp)
            except Exception:
                return DescentResult("failed", x, float(E), it, accepted, rejected, gn)
            if np.all(np.isfinite(Ep)) and Ep <= E + 1e-4 * alpha * dEdir:
                step_ok = True
                break
            alpha *= 0.5
            rejected += 1
        if not step_ok:
            return DescentResult("stagnated", x, float(E), it, accepted, rejected, gn)
        x = xp
        E = Ep
        accepted += 1
        result.history_energy.append(float(E))
        result.history_grad.append(gn)
        result.x = np.array(x, copy=True)
        result.energy = float(E)
        result.iters = it
        result.accepted = accepted
        result.rejected_steps = rejected
        result.final_grad_norm = gn
    return result