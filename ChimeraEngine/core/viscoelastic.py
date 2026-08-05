"""viscoelastic.py -- Stage 14: BULK hysteresis, and the part of it that is derivable.

THE THIRD AND LAST DISSIPATION MECHANISM. Stage 12 added radiation (energy leaving as sound),
Stage 13 added contact microslip (a slip annulus at the contact rim). This is the one that acts
inside the MATERIAL rather than at its surface: compress a solid and it warms; the warm region
conducts heat outward; on the return stroke that heat does not come back. Zener's thermoelastic
damping, and it needs no loss tangent to be handed to it -- only thermal constants.

    RELAXATION STRENGTH   Delta = E alpha^2 T / (rho c_p)        [dimensionless]
    DEBYE LOSS            tan d(w) = Delta * w tau / (1 + w^2 tau^2)
    RELAXATION TIME       tau = a^2 / D,   D = k/(rho c_p)

The temperature is READ, not assumed: aBlueWorld publishes T_surface, so warming the world raises
its materials' damping and the slider moves (checked in test_viscoelastic.py).

THE SHAPE IS THE PREDICTION, and it has two distinct physical ends. tan d -> 0 as w -> 0 because a
slow cycle stays ISOTHERMAL -- heat equilibrates continuously and no gradient ever forms. tan d ->
0 as w -> infinity because a fast cycle is ADIABATIC -- heat has no time to move at all. Loss
lives only in the awkward middle where diffusion and loading compete, peaking at w tau = 1 with
tan d = Delta/2. Two limits, two different reasons, one derived peak.

WHICH GIVES THE FLAGSHIP: for a ROLLING contact the loading frequency is set by the geometry,
w = pi v / a, so there is a ROLLING SPEED at which thermoelastic loss is maximal:

    v_peak = D / (pi a)

Roll slower or faster than that and the material dissipates less. Nothing in the constant-mu_r
model can express this, and nothing here was fitted to produce it.

HYSTERETIC ROLLING RESISTANCE. A Hertz contact stores U = (2/5) N h; a fraction 2 pi tan d of it
is lost per cycle; one cycle happens per 2a of travel. With h = a^2/R:

    mu_r = (2 pi / 5) tan d (a / R)       ~ N^(1/3), the classic hysteretic load scaling

THE HONEST REMAINDER, named rather than fitted. Thermoelastic loss is a DERIVED FLOOR on bulk
hysteresis, not the whole of it: dislocation motion, grain-boundary sliding and (in polymers)
chain relaxation all add anelastic loss that no derivation here reaches. `rolling_coefficient`
therefore takes tan d as an ARGUMENT -- hand it the derived thermoelastic value, or hand it a
measured total loss tangent the day a membrane publishes one, and the same machinery serves both.
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

import matter  # noqa: E402


def relaxation_strength(e_young: float, alpha: float, temperature_K: float,
                        rho: float, c_p: float) -> float:
    """Delta = E alpha^2 T / (rho c_p). Dimensionless, and PROPORTIONAL TO TEMPERATURE -- a colder
    world's rock is a better spring, which is a real and slightly surprising consequence."""
    return (float(e_young) * float(alpha) ** 2 * float(temperature_K)
            / (float(rho) * float(c_p)))


def relaxation_time(a: float, diffusivity: float) -> float:
    """tau = a^2 / D, the time heat needs to cross the contact.

    THE O(1) GEOMETRY FACTOR IS DECLARED, NOT HIDDEN. Beam theory carries a pi^2 for its
    particular mode shape; a contact patch is a different geometry and this uses the plain
    diffusion time across the contact radius. That choice moves tau -- and therefore the peak
    FREQUENCY -- by an O(1) amount; it does not move the peak VALUE (Delta/2), which is where the
    physics is. Stated so a reader knows which number to trust how far."""
    return float(a) ** 2 / float(diffusivity)


def loss_tangent(omega: float, delta: float, tau: float) -> float:
    """The Debye peak: tan d = Delta w tau / (1 + w^2 tau^2). Zero at both ends, Delta/2 at wt=1."""
    wt = float(omega) * float(tau)
    return float(delta) * wt / (1.0 + wt * wt)


def rolling_omega(v: float, a: float) -> float:
    """A material point is loaded and unloaded while the sphere advances 2a, so the cycle time is
    2a/v and w = 2 pi f = pi v / a."""
    return math.pi * float(v) / float(a)


def peak_rolling_speed(a: float, diffusivity: float) -> float:
    """THE FLAGSHIP: w tau = 1 with w = pi v/a and tau = a^2/D gives v = D/(pi a). The rolling
    speed at which the material dissipates most -- bigger contacts peak slower."""
    return float(diffusivity) / (math.pi * float(a))


def rolling_coefficient(tan_delta: float, a: float, r: float) -> float:
    """mu_r = (2 pi / 5) tan d (a/R). Takes tan d as an ARGUMENT on purpose: the derived
    thermoelastic value today, a measured total loss tangent whenever one is published."""
    return (2.0 * math.pi / 5.0) * float(tan_delta) * float(a) / float(r)


def thermoelastic_rolling(material: str, e_young: float, rho: float, temperature_K: float,
                          v: float, a: float, r: float):
    """The whole chain for one material at one speed: (mu_r, tan_delta, delta, tau, v_peak)."""
    alpha = matter.THERMAL_EXPANSION_PER_K[material]
    c_p = matter.SPECIFIC_HEAT_J_KG_K[material]
    k_th = matter.THERMAL_CONDUCTIVITY_W_M_K[material]
    d_th = matter.thermal_diffusivity(k_th, rho, c_p)
    delta = relaxation_strength(e_young, alpha, temperature_K, rho, c_p)
    tau = relaxation_time(a, d_th)
    td = loss_tangent(rolling_omega(v, a), delta, tau)
    return rolling_coefficient(td, a, r), td, delta, tau, peak_rolling_speed(a, d_th)
