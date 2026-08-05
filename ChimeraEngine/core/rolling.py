"""rolling.py -- Stage 12: contact torque, and rolling resistance derived instead of fitted.

CONTACT TORQUE is not a new law. The tangential force of Stage 11 acts at the contact, a lever arm
R from the centre, so it exerts tau = R * F_t on the body. That is the moment of a force already
derived -- and it is the whole reason a grain can SPIN rather than merely translate.

ROLLING RESISTANCE is where every engine in the world plugs in a coefficient. It is derivable here
because Stage 10 already derived the dissipation:

    A rolling sphere LOADS the material at the front of its contact patch and UNLOADS it at the
    back. The radiative damping pressure is proportional to the local indentation RATE, which is
    antisymmetric across the patch -- positive ahead of centre, negative behind. An antisymmetric
    pressure adds NO net force and a net MOMENT. Rolling resistance is that moment.

With the local indentation h(s) = h0 - s^2/(2R) across a patch of radius a, a point at station s
sees dh/dt = v s / R as the sphere rolls at v, so the damping pressure is zeta_A v s / R and

    tau_r = INT s * (zeta_A v s / R) dA = (zeta_A v / R) * (pi a^4 / 4)

with dA = 2 sqrt(a^2 - s^2) ds. Nothing was chosen: zeta_A = rho c_p is the half-space impedance
per unit area (hertz.py), a comes from Hertz, R and v are the state.

TWO PREDICTIONS THIS MAKES THAT THE TEXTBOOK CONSTANT-mu_r MODEL DOES NOT:
  * tau_r is VISCOUS -- proportional to v -- and therefore EXACTLY ZERO at rest. A constant-mu_r
    model resists a parked sphere, which is wrong and is why such models need a stiction hack.
  * tau_r ~ a^4 ~ N^(4/3), so it stiffens faster than the load.

THE HONEST SCOPE, stated before anyone measures around it. This is the RADIATIVE FLOOR of rolling
resistance and nothing more. Real rolling resistance is dominated by BULK HYSTERESIS -- a material
that returns less than it stores over a load cycle -- which needs a published loss tangent, and no
membrane in this world publishes one. Expect this to land orders of magnitude below a handbook
mu_r, and read that gap as the missing measurement it is. Plastic rearrangement (the mechanism
theGround's Terzaghi footprint uses) is likewise absent here.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parents[2]
_STORY = _ROOT / "story"
if str(_STORY) not in sys.path:
    sys.path.insert(0, str(_STORY))

from ChimeraEngine.core import hertz  # noqa: E402


def sphere_inertia(m: float, r: float) -> float:
    """I = (2/5) m R^2 for a uniform solid sphere. The 2/5 is geometry, and it is the ONLY thing
    the sliding-to-rolling transition depends on -- see `sliding_to_rolling`."""
    return 0.4 * float(m) * float(r) ** 2


def contact_torque(r: float, f_t: float) -> float:
    """tau = R * F_t. The moment of Stage 11's tangential force about the body's own centre."""
    return float(r) * float(f_t)


def rolling_torque(v: float, a: float, r: float, zeta_a: float) -> float:
    """tau_r = zeta_A v pi a^4 / (4 R) -- the moment of the radiative damping pressure."""
    return float(zeta_a) * float(v) * math.pi * float(a) ** 4 / (4.0 * float(r))


def rolling_torque_numeric(v: float, a: float, r: float, zeta_a: float, n: int = 200001) -> float:
    """The same moment by quadrature over the patch -- the referee for the closed form above."""
    s = np.linspace(-a, a, n)
    width = 2.0 * np.sqrt(np.clip(a * a - s * s, 0.0, None))
    p_damp = zeta_a * v * s / r
    return float(np.trapezoid(s * p_damp * width, s))


def rolling_dissipation_power(v: float, a: float, r: float, zeta_a: float,
                              n: int = 200001) -> float:
    """Power the damping pressure actually removes: INT zeta_A (dh/dt)^2 dA.

    THIS IS AN INDEPENDENT ROUTE. The torque above is a MOMENT integral; this is an ENERGY
    integral. A consistent dissipative model must satisfy tau_r * omega = P with omega = v/R, and
    checking it is how the algebra is caught if it is wrong."""
    s = np.linspace(-a, a, n)
    width = 2.0 * np.sqrt(np.clip(a * a - s * s, 0.0, None))
    hdot = v * s / r
    return float(np.trapezoid(zeta_a * hdot * hdot * width, s))


def rolling_resistance_coefficient(v: float, a: float, r: float, zeta_a: float,
                                   normal_force: float) -> float:
    """mu_r = tau_r / (N R) -- the dimensionless form, for comparison against sliding friction."""
    return rolling_torque(v, a, r, zeta_a) / (float(normal_force) * float(r))


def sliding_to_rolling(m: float, r: float, g: float, v0: float, mu: float,
                       e_star: float, g_star: float, steps_per_period: int = 200,
                       max_periods: float = 400.0):
    """THE FLAGSHIP EXPERIMENT: launch a sphere sliding (v = v0, no spin) and let the contact
    decide when it starts rolling.

    Friction at the contact does two things at once -- it slows the centre of mass AND it spins the
    body up -- and the two meet at a velocity that depends on NOTHING but the sphere's moment of
    inertia:

        m dv/dt = F,   I d(sigma)/dt = -R F   =>   v_roll = v0 / (1 + m R^2 / I) = (5/7) v0

    The 5/7 appears nowhere in this code. mu, g, R, m and the material all cancel out of it, so
    measuring it tests the lever arm, the Coulomb ceiling, the inertia and the integrator at once
    against a number none of them contains. Returns (v_roll/v0, slip_time, n_steps).
    """
    inertia = sphere_inertia(m, r)
    re = float(r)                                   # sphere on a flat: R_eff = R
    n_force = m * g
    h = hertz.penetration_for_force(n_force, re, e_star)
    kt = float(hertz.tangential_stiffness(h, re, g_star))
    dt = (2.0 * math.pi * math.sqrt(m / kt)) / float(steps_per_period)

    v, sigma, disp, t = float(v0), 0.0, 0.0, 0.0
    for step in range(int(max_periods * steps_per_period)):
        slip = v - sigma * r                        # contact-point velocity over the ground
        if slip <= 0.0:
            return v / v0, t, step
        disp += slip * dt
        mag, sliding, _ = hertz.tangential_response(h, disp, mu, re, g_star, e_star)
        f = -abs(mag)                               # opposes the forward slip
        v += dt * f / m
        sigma += dt * (-r * f) / inertia            # a backward force at the bottom spins it UP
        t += dt
    raise RuntimeError("the sphere never reached rolling -- do not widen a tolerance around this")
