"""hertz.py -- Stage 11: the contact law that vanishes at zero load, and the tangential half.

WHY THIS EXISTS. Stage 9 measured the linear overlap law reading E_eff = 31.1 GPa under a foot --
near-solid rock, because its stiffness k = pi B R / 2 does NOT vanish at zero penetration. That
was recorded as the honest tell and Hertz was named as the refinement. This is that refinement,
plus the tangential force the seam needed to hold a body on a slope.

TWO CITED CONSTANTS, AND EXACTLY TWO. An isotropic elastic solid is specified by two independent
moduli; bulk modulus alone cannot produce a contact theory. So `story/matter.py` publishes B and
G (both measured) and E, nu follow. Water has no G and this module REFUSES it rather than
substituting a number -- a fluid has no Hertzian contact, and that is a scope boundary, not a gap.

THE NORMAL LAW (Hertz, two spheres):
    F(h)  = (4/3) E* sqrt(R_eff) h^{3/2}          a(h)   = sqrt(R_eff h)
    k_n(h)= dF/dh = 2 E* a(h)                     R_eff  = R/2 for equal spheres
    1/E*  = 2(1-nu^2)/E   for identical materials

THE TANGENTIAL LAW (Mindlin, with a Coulomb ceiling):
    k_t = 8 G* a(h),      1/G* = 2(2-nu)/G,       |F_t| <= mu |F_n|
mu comes from the repose angle this world GREW (40.03 degrees, granular trainer), so the only
inputs are two cited moduli and one emergent angle.

THE IDENTITY THAT FALLS OUT, and it is the cleanest check here -- every constant cancels:
    k_t / k_n = 8 G* / (2 E*) = 2(1 - nu) / (2 - nu)
a pure function of Poisson's ratio. Checked two ways in test_hertz.py rather than trusted.

WHAT HERTZ PREDICTS THAT LINEAR CONTACT CANNOT. Because k_n ~ sqrt(h) ~ F^{1/3}, the stiffness of
a granular pack rises with the load it carries, so the speed of sound in it goes as
    c ~ sqrt(k) ~ F^{1/6}
-- the textbook granular P^{1/6} scaling, which this module was never fitted to and which the
linear law cannot produce at all (its exponent is exactly 0). That contrast is the falsifier.
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


def elastic_constants(material: str):
    """(B, G, E, nu) for a material that HAS a shear modulus. Refuses one that does not."""
    b = matter.BULK_MODULUS_PA.get(material)
    g = matter.SHEAR_MODULUS_PA.get(material)
    if b is None:
        raise KeyError(f"no bulk modulus published for {material!r}")
    if g is None:
        raise KeyError(
            f"{material!r} publishes no shear modulus -- a fluid has none, and Hertzian contact "
            f"is an elastic-SOLID theory. This is a scope boundary, not a missing number: do not "
            f"substitute one.")
    return b, g, matter.youngs_modulus(b, g), matter.poisson_ratio(b, g)


def contact_modulus(e: float, nu: float) -> float:
    """E* for two bodies of the SAME material: 1/E* = 2(1-nu^2)/E."""
    return float(e) / (2.0 * (1.0 - float(nu) ** 2))


def shear_contact_modulus(g: float, nu: float) -> float:
    """G* for two bodies of the same material: 1/G* = 2(2-nu)/G."""
    return float(g) / (2.0 * (2.0 - float(nu)))


def p_wave_speed(b: float, g: float, rho: float) -> float:
    """The LONGITUDINAL wave speed of an elastic solid, c_p = sqrt((B + 4G/3)/rho).

    Not the same as Stage 9's sqrt(B/rho): that is the fluid sound speed, correct for water and
    wrong for a solid, which resists shear as well as compression. With quartz's two cited moduli
    this returns ~6000 m/s, which is what quartz measures -- a free check on both constants."""
    return math.sqrt((float(b) + 4.0 * float(g) / 3.0) / float(rho))


def radiation_impedance_per_area(b: float, g: float, rho: float) -> float:
    """rho * c_p -- the impedance a half-space presents PER UNIT AREA of contact. Stage 10's
    Z = sqrt(km) was the same quantity for a chain; this is its continuum form, and it is what a
    contact PATCH radiates through."""
    return float(rho) * p_wave_speed(b, g, rho)


def r_eff(r1: float, r2: float = None) -> float:
    r2 = r1 if r2 is None else r2
    return 1.0 / (1.0 / float(r1) + 1.0 / float(r2))


def contact_radius(h, re: float):
    h = np.asarray(h, dtype=np.float64)
    return np.sqrt(np.clip(h, 0.0, None) * float(re))


def hertz_force(h, re: float, e_star: float):
    """F = (4/3) E* sqrt(R_eff) h^{3/2}; zero (never tensile) out of contact."""
    h = np.asarray(h, dtype=np.float64)
    hp = np.clip(h, 0.0, None)
    return (4.0 / 3.0) * float(e_star) * math.sqrt(float(re)) * hp ** 1.5


def hertz_stiffness(h, re: float, e_star: float):
    """k_n = dF/dh = 2 E* a(h) -- and it VANISHES at h = 0, which is the whole point."""
    return 2.0 * float(e_star) * contact_radius(h, re)


def tangential_stiffness(h, re: float, g_star: float):
    """k_t = 8 G* a(h) (Mindlin, no-slip branch)."""
    return 8.0 * float(g_star) * contact_radius(h, re)


def stiffness_ratio(nu: float) -> float:
    """k_t/k_n = 2(1-nu)/(2-nu) -- every modulus cancels; only Poisson's ratio survives."""
    return 2.0 * (1.0 - float(nu)) / (2.0 - float(nu))


def penetration_for_force(f: float, re: float, e_star: float) -> float:
    """Invert Hertz: h = (3F / (4 E* sqrt(R_eff)))^{2/3}."""
    return (3.0 * float(f) / (4.0 * float(e_star) * math.sqrt(float(re)))) ** (2.0 / 3.0)


def column_modulus_hertz(pressure_Pa: float, n_area: float, r: float,
                         e_star: float) -> float:
    """The granular column's effective Young's modulus under a stated pressure.

    Same construction as seam.column_modulus, with Hertz in place of the linear law: one contact
    carries F = sigma/n_area, penetrates h(F), and the column strains h/(2R). The result rises as
    sigma^{1/3} instead of standing still -- which is exactly the light-load defect being fixed."""
    f = float(pressure_Pa) / float(n_area)
    h = penetration_for_force(f, r_eff(r), e_star)
    return float(pressure_Pa) * (2.0 * float(r)) / h


def measure_mode_speed_hertz(n_grains: int, m: float, r: float, e_star: float, h0: float,
                             amp_frac: float = 0.05, steps_per_period: int = 200,
                             n_periods: float = 4.0):
    """Stage 9's threshold-free instrument, driven by a HERTZIAN chain pre-compressed to h0.

    The instrument is unchanged on purpose -- it was validated in Stage 9 against a case whose
    answer is known in closed form, so re-using it here tests the CONTACT LAW rather than
    re-testing the measurement. Returns (c_measured, c_predicted, contact_force).
    """
    re = r_eff(r)
    a0 = 2.0 * r - h0
    k0 = float(hertz_stiffness(h0, re, e_star))
    f0 = float(hertz_force(h0, re, e_star))
    length = (n_grains - 1) * a0
    q = math.pi / length
    theta = q * a0 / 2.0
    c_pred = a0 * math.sqrt(k0 / m)
    omega_pred = 2.0 * math.sqrt(k0 / m) * math.sin(theta)
    dt = (2.0 * math.pi * math.sqrt(m / k0)) / float(steps_per_period)
    n_steps = int(n_periods * (2.0 * math.pi / omega_pred) / dt)

    j = np.arange(n_grains, dtype=np.float64)
    x0 = j * a0
    x = x0 + amp_frac * h0 * np.sin(math.pi * j / (n_grains - 1))
    v = np.zeros(n_grains)
    mid = (n_grains - 1) // 2

    def forces(xx):
        fp = hertz_force(2.0 * r - (xx[1:] - xx[:-1]), re, e_star)
        f = np.zeros(n_grains)
        f[:-1] -= fp
        f[1:] += fp
        f[0] = 0.0
        f[-1] = 0.0
        return f

    f = forces(x)
    prev = x[mid] - x0[mid]
    crossings = []
    for s in range(n_steps):
        v += 0.5 * dt * f / m
        x += dt * v
        f = forces(x)
        v += 0.5 * dt * f / m
        v[0] = v[-1] = 0.0
        cur = x[mid] - x0[mid]
        if prev != 0.0 and (cur < 0.0) != (prev < 0.0):
            crossings.append((s + 1) * dt - dt * cur / (cur - prev))
        prev = cur
    if len(crossings) < 3:
        raise RuntimeError(f"only {len(crossings)} crossings -- the mode did not oscillate")
    period = 2.0 * float(np.mean(np.diff(crossings)))
    omega = 2.0 * math.pi / period
    return (omega / q) * (theta / math.sin(theta)), c_pred, f0


# ── THE TANGENTIAL FORCE: Mindlin spring under a Coulomb ceiling ────────────────────────────────
def tangential_response(h: float, disp: float, mu: float, re: float,
                        g_star: float, e_star: float):
    """(F_t, sliding, preslip) for a contact at normal penetration h displaced tangentially
    by `disp`.

    The contact STICKS while the elastic force k_t*disp stays under mu*F_n and SLIDES at exactly
    mu*F_n beyond it. `preslip` = mu*F_n/k_t is the tangential displacement a contact genuinely
    undergoes BEFORE letting go -- a real, measured micron-scale quantity in tribology, not a
    numerical smoothing.
    """
    if h <= 0.0:
        return 0.0, False, 0.0
    kt = float(tangential_stiffness(h, re, g_star))
    fn = float(hertz_force(h, re, e_star))
    cap = mu * fn
    fe = kt * abs(float(disp))
    preslip = cap / kt
    if fe > cap:
        return math.copysign(cap, disp), True, preslip
    return math.copysign(fe, disp), False, preslip


def slide_dissipation(mu: float, fn: float, distance: float) -> float:
    """Energy a sliding contact turns into heat: mu*F_n*d, the Coulomb ceiling doing work."""
    return mu * float(fn) * float(distance)


def tilt_table(mu: float, m_body: float, g: float, re: float, g_star: float, e_star: float,
               lo_deg: float = 1.0, hi_deg: float = 80.0, n_bisect: int = 60) -> float:
    """THE SIMULATED EXPERIMENT: tilt a resting body until its contact lets go.

    Raising a table slowly is quasi-static by construction, so this needs no dynamics and no
    damping -- and it is literally how a friction angle is measured in a laboratory. At each
    angle the body's own weight sets the normal force, Hertz sets the penetration, Mindlin sets
    the tangential stiffness, and the Coulomb ceiling decides.

    WHAT THIS PROVES AND WHAT IT DOES NOT. Algebraically the release must land on atan(mu) --
    that much is Coulomb's law, and this is a round-trip test of the IMPLEMENTATION (that
    penetration_for_force inverts hertz_force, that the ceiling is taken on the true normal
    force). The physics content is elsewhere and it is real: this tilt-table experiment must
    return the same angle the granular trainer GREW by piling grains up. Two unrelated
    experiments, one number.
    """
    def slides(theta_deg: float) -> bool:
        th = math.radians(theta_deg)
        fn = m_body * g * math.cos(th)
        drive = m_body * g * math.sin(th)
        h = penetration_for_force(fn, re, e_star)
        kt = float(tangential_stiffness(h, re, g_star))
        _, sliding, _ = tangential_response(h, drive / kt, mu, re, g_star, e_star)
        return sliding
    lo, hi = lo_deg, hi_deg
    for _ in range(n_bisect):
        mid = 0.5 * (lo + hi)
        if slides(mid):
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)
