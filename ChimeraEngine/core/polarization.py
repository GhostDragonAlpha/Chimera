"""polarization.py -- Stage 17: the omission Stage 16 named, and the correction it forces.

WHAT STAGE 16 GOT WRONG, AND WHY IT MATTERS. It computed a chain's energy as the product of
UNPOLARIZED Fresnel coefficients, and flagged that as a real physical omission rather than a scope
choice. It was: s-polarized light (electric field perpendicular to the plane of incidence) always
reflects better than p-polarized light off a dielectric, so every bounce filters the beam further
toward s. A chain POLARISES ITSELF, and after a few bounces essentially all the surviving light is
in the strongly-reflecting state.

The consequence is not subtle and its direction is guaranteed by convexity:

    true    (R_s^n + R_p^n) / 2        >=      ((R_s + R_p)/2)^n     Stage 16's estimate

with equality only at n = 1 or R_s = R_p. So STAGE 16 UNDERESTIMATED CHAIN ENERGY, by more the
deeper the chain -- and `test_polarization.py` measures how much rather than arguing about it.

EVERYTHING HERE COMES FROM n, WHICH COMES FROM DENSITY. The exact Fresnel amplitudes need only the
two refractive indices, and Stage 0 derives n from a membrane's published density through
Lorentz-Lorenz. So the chain runs: published density -> n -> r_s, r_p -> Brewster's angle, the
critical angle, and the degree of polarization. Nothing new is cited.

    r_s = (n1 cos_i - n2 cos_t) / (n1 cos_i + n2 cos_t)
    r_p = (n2 cos_i - n1 cos_t) / (n2 cos_i + n1 cos_t)
    t_s = 2 n1 cos_i / (n1 cos_i + n2 cos_t)        T = (n2 cos_t)/(n1 cos_i) |t|^2
    t_p = 2 n1 cos_i / (n2 cos_i + n1 cos_t)

TWO ANGLES FALL OUT, both measurable facts about the world's own water:
  * BREWSTER, theta_B = arctan(n2/n1): R_p is EXACTLY zero, so the reflection is perfectly
    s-polarized after a single bounce. This is why a polarising filter kills glare off water.
  * CRITICAL, theta_c = arcsin(n2/n1) for n1 > n2: beyond it R_s = R_p = 1 exactly. This must agree
    with the TIR branch already living in Stage 4's refraction kernel -- two independent
    implementations of one piece of physics, and the test checks they do.

SCHLICK, HONESTLY ASSESSED. Stages 1, 11 and 16 all use Schlick's approximation, which is a fit to
the UNPOLARIZED average and cannot represent the split at all -- it is one scalar. Its error against
exact Fresnel is measured here across every angle rather than assumed small, so the earlier stages'
approximation is either validated or quantified.

NAMED UNBUILT:
  * CIRCULAR AND ELLIPTICAL polarization. This tracks two real power fractions, not complex
    amplitudes with a relative phase, so it cannot represent handedness. TIR in particular imparts
    a phase shift that this model drops.
  * METALS. A conductor has a COMPLEX refractive index; these real-arithmetic formulas are for
    dielectrics only, and the module refuses rather than silently returning nonsense.
  * THE RENDER STATE. The GPU kernel carries one scalar F0 per grain. Threading a genuine
    polarization state through it would need two columns and a per-grain incidence-plane frame;
    what IS integrated is the polarization-corrected CHAIN coefficient, which needs neither.
"""
from __future__ import annotations

import math

import numpy as np


def _cos_t(n1: float, n2: float, cos_i: float):
    """cos(theta_t) by Snell, or None under total internal reflection."""
    sin_i2 = max(0.0, 1.0 - float(cos_i) ** 2)
    sin_t2 = (float(n1) / float(n2)) ** 2 * sin_i2
    if sin_t2 >= 1.0:
        return None
    return math.sqrt(1.0 - sin_t2)


def fresnel_exact(n1: float, n2: float, cos_i: float):
    """(R_s, R_p) exactly. Under total internal reflection both are 1.0 -- not approximately."""
    ct = _cos_t(n1, n2, cos_i)
    if ct is None:
        return 1.0, 1.0
    a, b = float(n1) * float(cos_i), float(n2) * ct
    c, d = float(n2) * float(cos_i), float(n1) * ct
    r_s = (a - b) / (a + b)
    r_p = (c - d) / (c + d)
    return r_s * r_s, r_p * r_p


def transmittance_exact(n1: float, n2: float, cos_i: float):
    """(T_s, T_p) as POWER fractions, including the (n2 cos_t)/(n1 cos_i) geometry factor that a
    naive |t|^2 omits. R + T must equal 1 for each polarization, which is the test that catches a
    dropped factor or a sign convention error."""
    ct = _cos_t(n1, n2, cos_i)
    if ct is None:
        return 0.0, 0.0
    a, b = float(n1) * float(cos_i), float(n2) * ct
    c, d = float(n2) * float(cos_i), float(n1) * ct
    t_s = 2.0 * a / (a + b)
    t_p = 2.0 * a / (c + d)
    geom = b / a
    return geom * t_s * t_s, geom * t_p * t_p


def fresnel_unpolarized(n1: float, n2: float, cos_i: float) -> float:
    r_s, r_p = fresnel_exact(n1, n2, cos_i)
    return 0.5 * (r_s + r_p)


def brewster_angle_rad(n1: float, n2: float) -> float:
    """theta_B = arctan(n2/n1) -- where R_p vanishes and the reflection is purely s-polarized."""
    return math.atan(float(n2) / float(n1))


def critical_angle_rad(n1: float, n2: float):
    """arcsin(n2/n1), or None when n1 <= n2 (no total internal reflection exists that way)."""
    if float(n1) <= float(n2):
        return None
    return math.asin(float(n2) / float(n1))


def chain_energy_polarized(n1: float, n2: float, cos_i: float, depth: int) -> float:
    """(R_s^n + R_p^n)/2 -- an initially UNPOLARIZED beam down an n-bounce chain, tracking the two
    components separately instead of averaging first. Averaging first is what Stage 16 did."""
    r_s, r_p = fresnel_exact(n1, n2, cos_i)
    return 0.5 * (r_s ** int(depth) + r_p ** int(depth))


def chain_energy_unpolarized(n1: float, n2: float, cos_i: float, depth: int) -> float:
    """((R_s+R_p)/2)^n -- Stage 16's estimate, kept so the two can be compared rather than
    described."""
    return fresnel_unpolarized(n1, n2, cos_i) ** int(depth)


def degree_of_polarization(n1: float, n2: float, cos_i: float, depth: int) -> float:
    """(I_s - I_p)/(I_s + I_p) after n bounces. Reaches 1 at Brewster after a SINGLE bounce, and
    approaches 1 with depth at any other angle -- the chain filtering itself."""
    r_s, r_p = fresnel_exact(n1, n2, cos_i)
    s, p = r_s ** int(depth), r_p ** int(depth)
    if s + p <= 0.0:
        return 0.0
    return (s - p) / (s + p)


def polarized_chain_f0(n1: float, n2: float, cos_i: float, depth: int) -> float:
    """The chain coefficient to hand `story/matter.paint_specular` -- Stage 16's collapse-to-one-lobe
    trick, with the polarization-correct energy in place of the unpolarized product. The renderer
    needs no polarization state to benefit from this."""
    return chain_energy_polarized(n1, n2, cos_i, depth)


def max_visible_depth_polarized(n1: float, n2: float, cos_i: float, floor: float,
                                cap: int = 4096) -> int:
    """The deepest chain that can still move a pixel, with the polarization-correct energy.

    Must come out >= Stage 16's unpolarized bound, because the s-component decays more slowly than
    the average does -- so Stage 16 under-counted visible bounces as well as energy."""
    for n in range(1, cap + 1):
        if chain_energy_polarized(n1, n2, cos_i, n) < floor:
            return n - 1
    return cap


def refuse_conductor(n_complex_imag: float) -> None:
    """A conductor has a COMPLEX refractive index and these real formulas do not apply to it.
    Refuse rather than return a plausible-looking number -- the same discipline that keeps water
    out of `hertz.elastic_constants`."""
    if abs(float(n_complex_imag)) > 0.0:
        raise ValueError(
            "a complex refractive index means an absorbing medium (a metal): these real-arithmetic "
            "Fresnel formulas are for DIELECTRICS only. This is a scope boundary, not a gap.")
