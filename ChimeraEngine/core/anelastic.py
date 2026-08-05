"""anelastic.py -- Stage 15: the bulk loss tangent, DERIVED, with the microstructure cancelling.

WHAT STAGE 14 LEFT OPEN. Its `rolling_coefficient` takes tan d as an ARGUMENT, deliberately, so
that a measured loss tangent could plug in later. It is filled here by a DERIVATION instead -- the
third time in this lane that a "needs a citation" note turned out to be reachable, and the reason
is the same each time: the question was never what value the constant should take, but what
physical thing it is.

WHAT ANELASTIC LOSS IS, IN A GRANULAR SOLID. The dominant internal-friction mechanism in rock and
soil is not dislocation motion -- it is frictional sliding on internal surfaces. In a granular
medium those internal surfaces are the GRAIN CONTACTS, and Stage 13 already derived what one
contact dissipates per cycle. So the bulk loss is that, summed over the contacts a cubic metre
contains -- and the contact count comes from theGround's own published porosity and median grain
size (Stage 9), not from anything new.

THE DERIVATION, and its ending is the surprise:

    one contact      dW    = 2 T^3 / (9 mu F_n k_t)             (Stage 13, asymptotic)
    stress -> forces T     = tau / n_area,   F_n = sigma / n_area
    contacts per m^3 n_c   = n_area / (2R)
    dissipated       dW_vol = n_c dW  = tau^3 / (9 R mu sigma k_t n_area)
    pack stiffness   G_pack = 2 R n_area k_t
    stored           W_vol  = tau^2 / (2 G_pack) = tau^2 / (4 R n_area k_t)

    tan d = dW_vol / (2 pi W_vol) = 2 tau / (9 pi mu sigma)

EVERY MICROSTRUCTURAL TERM CANCELS. Grain size, porosity, contact stiffness, both elastic moduli --
all gone. The bulk anelastic loss of a frictional granular medium depends on nothing but the ratio
of shear amplitude to confining stress, and on the friction coefficient. That is not a
simplification anyone chose; it is what the sum does, and it is why measured Q for granular
materials is so stubbornly universal across wildly different mineralogies. The cancellation is
verified NUMERICALLY as well as algebraically (vary d50 and porosity tenfold; tan d does not move).

TWO SIGNATURES THAT MAKE THIS DISTINGUISHABLE FROM STAGE 14, and they are orthogonal:

    frictional (here)      tan d ~ AMPLITUDE,     frequency-INDEPENDENT (no rate anywhere in it)
    thermoelastic (S14)    amplitude-INDEPENDENT, tan d PEAKS in frequency

So a medium's damping can be decomposed by experiment rather than by assumption: sweep amplitude at
fixed frequency to see one, sweep frequency at fixed amplitude to see the other. A single fitted
loss tangent could not have told them apart.

THE HONEST REMAINDER. This is the FRICTIONAL contribution. Dislocation damping (Granato-Lucke) and
point-defect relaxation are separate mechanisms needing dislocation densities and activation
energies that no membrane publishes -- genuinely UNBUILT, and for room-temperature quartz genuinely
small. The asymptotic ceiling 2/(9 pi) = 0.0707 is an extrapolation of a small-amplitude formula to
full slip and should be read as an order of magnitude, not a limit: `loss_tangent_summed` uses the
EXACT loop and exceeds it there.
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

from ChimeraEngine.core import hertz, hysteresis, seam  # noqa: E402

# The asymptotic ceiling: tan d at tau = mu sigma, where the small-amplitude formula is already out
# of its regime. Kept as a named constant so nobody mistakes it for a measured limit.
ASYMPTOTIC_CEILING = 2.0 / (9.0 * math.pi)


def loss_tangent_closed(tau_amp: float, sigma_conf: float, mu: float) -> float:
    """tan d = 2 tau / (9 pi mu sigma). The whole microstructure has cancelled out of this."""
    return 2.0 * float(tau_amp) / (9.0 * math.pi * float(mu) * float(sigma_conf))


def contact_areal_density(porosity: float, r: float) -> float:
    """Contacts per unit AREA -- Stage 9's count, from published porosity and grain radius."""
    return seam.grain_areal_density(porosity, r)


def contact_volume_density(porosity: float, r: float) -> float:
    """Contacts per unit VOLUME. A chain crossing a cube of side L holds L/(2R) contacts and there
    are n_area L^2 chains, so n_c = n_area/(2R). Derived, not counted by hand."""
    return contact_areal_density(porosity, r) / (2.0 * float(r))


def pack_shear_modulus(porosity: float, r: float, kt: float) -> float:
    """G_pack = 2 R n_area k_t -- the same column construction Stage 9 used for E_eff, in shear.

    KNOWN AND STATED OVER-STIFFNESS: this assumes every contact is load-bearing and aligned with
    the load, where a real pack carries stress on force chains at a coordination number below the
    geometric maximum. Expect it high by roughly an order against a measured small-strain G. It
    does NOT contaminate the loss tangent, because G_pack cancels out of tan d -- which is exactly
    what makes the cancellation worth having."""
    return 2.0 * float(r) * contact_areal_density(porosity, r) * float(kt)


def _contact_state(sigma_conf: float, porosity: float, r: float, e_star: float, g_star: float):
    """(F_n, k_t, n_area) for one grain contact under a confining stress. R_eff = R/2: grain on
    grain, not grain on a flat."""
    n_area = contact_areal_density(porosity, r)
    f_n = float(sigma_conf) / n_area
    re = hertz.r_eff(r)
    h = hertz.penetration_for_force(f_n, re, e_star)
    kt = float(hertz.tangential_stiffness(h, re, g_star))
    return f_n, kt, n_area


def loss_tangent_summed(tau_amp: float, sigma_conf: float, mu: float, porosity: float,
                        r: float, e_star: float, g_star: float) -> float:
    """THE REFEREE: the same loss tangent built explicitly -- Stage 13's EXACT hysteresis loop at
    one contact, multiplied by the contacts in a cubic metre, divided by the energy that cubic
    metre stores. Uses the exact loop rather than the cubic asymptote, so it must agree with
    `loss_tangent_closed` at small amplitude and EXCEED it as full slip approaches."""
    f_n, kt, n_area = _contact_state(sigma_conf, porosity, r, e_star, g_star)
    t_amp = float(tau_amp) / n_area
    dw = hysteresis.loop_energy(t_amp, mu, f_n, kt)
    dw_vol = contact_volume_density(porosity, r) * dw
    w_vol = float(tau_amp) ** 2 / (2.0 * pack_shear_modulus(porosity, r, kt))
    return dw_vol / (2.0 * math.pi * w_vol)


def quality_factor(tan_delta: float) -> float:
    """Q = 1/tan d -- how seismology and rock physics usually quote the same number."""
    return 1.0 / float(tan_delta)


def strain_amplitude(tau_amp: float, porosity: float, r: float, sigma_conf: float,
                     e_star: float, g_star: float) -> float:
    """The shear strain a given stress amplitude produces in the pack, for reporting tan d against
    strain the way a rock-mechanics measurement would."""
    _, kt, _ = _contact_state(sigma_conf, porosity, r, e_star, g_star)
    return float(tau_amp) / pack_shear_modulus(porosity, r, kt)
