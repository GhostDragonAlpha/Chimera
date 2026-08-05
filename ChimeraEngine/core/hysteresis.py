"""hysteresis.py -- Stage 13: the hysteretic loss, and it needed no new constant after all.

THE CORRECTION THIS MODULE EXISTS TO MAKE. Stage 12 recorded that hysteretic rolling loss "needs a
published loss tangent that no membrane has". That was TOO BROAD, and building it is how the error
surfaced. There are two hysteresis mechanisms, not one:

  * CONTACT MICROSLIP (Mindlin-Deresiewicz) -- DERIVABLE from mu and G*, both already in hand.
    This module.
  * BULK VISCOELASTIC LOSS (a material loss tangent) -- genuinely needs a cited constant, and
    still does. Remains UNBUILT, and the distinction is now sharp instead of lumped.

WHY STAGE 11 HAD NO HYSTERESIS, precisely. Its tangential law is a LINEAR spring under a hard
Coulomb cap: loading traces d = T/k_t and unloading traces d = T/k_t -- the SAME path. A loop that
retraces its outward path encloses zero area, so the absence of dissipation was a consequence of
the linear approximation, not of a missing material property. Mindlin's actual contact does not
stick uniformly: an annulus at the rim slips while the centre holds, and it grows as the tangential
load rises, so the unloading path differs from the loading path and the loop has area.

THE SOFTENING CURVE, written so its initial slope IS Stage 11's k_t (no convention mismatch):

    d(T) = (3 mu N / (2 k_t)) [ 1 - (1 - T/(mu N))^(2/3) ]        d'(0) = 1/k_t

Full slip arrives at d = 3 mu N/(2 k_t) -- 1.5x further out than the linear model's mu N/k_t, which
is exactly what Stage 11 approximated away. Cyclic response follows MASING's rule: an unloading
branch is the virgin curve scaled by two in both axes.

THE ASYMPTOTE, DERIVED HERE AND CHECKED NUMERICALLY. Expanding v'(x) = (1/k_t)(1 - x/(mu N))^(-1/3)
to first order and integrating the Masing loop:

    dW = INT T [v'((T+T*)/2) - v'((T*-T)/2)] dT  ~  2 T*^3 / (9 mu N k_t)

CUBIC in the tangential amplitude -- the known signature of fretting/microslip damping, and a
prediction nothing here was fitted to. `loop_energy` integrates the exact loop and must converge
to this.

ROLLING. A material point stays in contact while the sphere advances 2a, so one load cycle happens
per 2a of travel and the dissipation per unit distance is a FORCE:

    F_r = dW / (2a)        mu_r = F_r / N

Because dW ~ T^3, this loss grows CUBICALLY with transmitted tractive force -- which is why a
coasting wheel is so much cheaper than a driven one, and it is a statement the constant-mu_r model
cannot make at all.
"""
from __future__ import annotations

import math

import numpy as np


def full_slip_displacement(mu: float, n_force: float, kt: float) -> float:
    """Where Mindlin's contact finally lets go: 3 mu N / (2 k_t). Stage 11's linear law put it at
    mu N / k_t -- a factor 2/3 nearer, which is the approximation stated as a number."""
    return 3.0 * float(mu) * float(n_force) / (2.0 * float(kt))


def virgin_displacement(t, mu: float, n_force: float, kt: float):
    """The Mindlin-Deresiewicz loading curve. Softens as the slip annulus grows; its tangent at
    the origin is exactly Stage 11's linear law."""
    t = np.asarray(t, dtype=np.float64)
    cap = float(mu) * float(n_force)
    u = np.clip(t / cap, 0.0, 1.0)
    return full_slip_displacement(mu, n_force, kt) * (1.0 - (1.0 - u) ** (2.0 / 3.0))


def masing_loop(t_star: float, mu: float, n_force: float, kt: float, n_pts: int = 20001):
    """The closed cycle between -T* and +T*, by Masing's rule (unloading = virgin scaled by 2).
    Returns (T_loading, d_loading, T_unloading, d_unloading)."""
    v = lambda x: virgin_displacement(x, mu, n_force, kt)
    d_star = float(v(t_star))
    t_up = np.linspace(-t_star, t_star, n_pts)
    d_up = -d_star + 2.0 * v((t_up + t_star) / 2.0)
    t_dn = np.linspace(t_star, -t_star, n_pts)
    d_dn = d_star - 2.0 * v((t_star - t_dn) / 2.0)
    return t_up, d_up, t_dn, d_dn


def loop_energy(t_star: float, mu: float, n_force: float, kt: float, n_pts: int = 20001) -> float:
    """Energy dissipated per cycle: the enclosed area, integrated as the closed loop INT T dd."""
    t_up, d_up, t_dn, d_dn = masing_loop(t_star, mu, n_force, kt, n_pts)
    return abs(float(np.trapezoid(t_up, d_up) + np.trapezoid(t_dn, d_dn)))


def loop_energy_asymptote(t_star: float, mu: float, n_force: float, kt: float) -> float:
    """dW ~ 2 T*^3 / (9 mu N k_t) -- derived in this module's docstring, checked against the
    exact loop integral rather than trusted."""
    return 2.0 * float(t_star) ** 3 / (9.0 * float(mu) * float(n_force) * float(kt))


def linear_cap_loop_energy(t_star: float, mu: float, n_force: float, kt: float,
                           n_pts: int = 20001) -> float:
    """The SAME loop integral applied to Stage 11's linear-spring-with-a-cap law.

    It returns zero below the cap, and it is computed rather than asserted: the point is to SHOW
    that the earlier model could not dissipate, not to claim it."""
    cap = float(mu) * float(n_force)
    if t_star >= cap:
        raise ValueError("above the cap the linear model slides; this compares the STUCK regime")
    t_up = np.linspace(-t_star, t_star, n_pts)
    d_up = t_up / kt
    t_dn = np.linspace(t_star, -t_star, n_pts)
    d_dn = t_dn / kt
    return abs(float(np.trapezoid(t_up, d_up) + np.trapezoid(t_dn, d_dn)))


def microslip_rolling_force(t_star: float, mu: float, n_force: float, kt: float,
                            a: float) -> float:
    """F_r = dW / (2a): one load cycle per 2a of travel makes the per-cycle energy a force."""
    return loop_energy(t_star, mu, n_force, kt) / (2.0 * float(a))


def microslip_rolling_coefficient(t_star: float, mu: float, n_force: float, kt: float,
                                  a: float) -> float:
    return microslip_rolling_force(t_star, mu, n_force, kt, a) / float(n_force)
