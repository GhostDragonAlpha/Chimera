"""overlap.py -- Stage 8: contact pressure from the overlap of Gaussian density packets.

THE DECLARED MODEL (docs/THE_TWO_FORCES.md Part II Stage 8). Two grains are two density packets
rho_i(x) = rho0 * exp(-|x - c_i|^2 / (2 s_i^2)). Superposing them compresses matter, and
compressing matter costs energy at the rate the material itself publishes -- its bulk modulus B
(story/matter.py BULK_MODULUS_PA, cited measured constants). To lowest order in the overlap, the
elastic energy of the superposition is the CROSS TERM of the quadratic compression energy:

    U(d) = (B / rho0^2) * O(d),      O(d) = INT rho_1 rho_2 dV
    O(d) = m1 m2 / ((2 pi)^(3/2) (s1^2+s2^2)^(3/2)) * exp(-d^2 / (2 (s1^2+s2^2)))

-- Gaussian x Gaussian integrates in closed form (the Gaussians-close claim, and it is TESTED
against a brute-force 3D numeric integral in test_overlap.py, not assumed). The force follows by
differentiation, so the field is conservative by construction and the test checks that too:

    F(d) = -dU/dd = (B / rho0^2) * O(d) * d / (s1^2 + s2^2)      (repulsive, monotone in overlap)

EVERY CONSTANT IS READ: B cited, rho0 published by the membrane, m from grain_mass(rho0, s),
s the grain's own SIZE. There is NO picked stiffness anywhere -- which is exactly why the model
can LOSE, and it does: see THE VERDICT in test_overlap.py. The cross-term form is valid only
while the overlap is small (density saturation begins at d ~ 2.4 s where the summed peak reaches
rho0); a saturated-density (volume-exclusion) energy is the named successor, NOT built.
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

from matter import BULK_MODULUS_PA, grain_mass  # noqa: E402,F401


def overlap_integral(m1: float, s1: float, m2: float, s2: float, d: float) -> float:
    """Closed form of INT rho_1 rho_2 dV for two Gaussian packets a distance d apart."""
    S2 = s1 * s1 + s2 * s2
    return (m1 * m2 / (((2.0 * math.pi) ** 1.5) * S2 ** 1.5)) * math.exp(-d * d / (2.0 * S2))


def overlap_numeric(m1: float, s1: float, m2: float, s2: float, d: float,
                    n: int = 121, span: float = 6.0) -> float:
    """The brute-force referee: the same integral on a 3D grid, float64. Grid extent span*max(s)
    beyond each centre; discretisation error is the test's pre-registered tolerance."""
    s = max(s1, s2)
    lo = -span * s
    hi = d + span * s
    zs = np.linspace(lo, hi, n)
    xs = np.linspace(-span * s, span * s, n)
    dx = xs[1] - xs[0]
    dz = zs[1] - zs[0]
    X, Y, Z = np.meshgrid(xs, xs, zs, indexing="ij")
    rho1 = m1 / (((2 * math.pi) ** 1.5) * s1 ** 3) * np.exp(-(X * X + Y * Y + Z * Z) / (2 * s1 * s1))
    r2 = X * X + Y * Y + (Z - d) ** 2
    rho2 = m2 / (((2 * math.pi) ** 1.5) * s2 ** 3) * np.exp(-r2 / (2 * s2 * s2))
    return float(np.sum(rho1 * rho2) * dx * dx * dz)


def contact_energy(m1, s1, m2, s2, d, B, rho0) -> float:
    return (float(B) / (float(rho0) ** 2)) * overlap_integral(m1, s1, m2, s2, d)


def contact_force(m1, s1, m2, s2, d, B, rho0) -> float:
    """-dU/dd, analytic. Positive = repulsive (pushes the centres apart)."""
    S2 = s1 * s1 + s2 * s2
    return contact_energy(m1, s1, m2, s2, d, B, rho0) * float(d) / S2


# ═══ STAGE 8 v2 — THE SUCCESSOR: SATURATED-DENSITY (VOLUME-EXCLUSION) CONTACT ════════════════════
# THE DECLARED MODEL, built where v1's refutation said stiffness must live. Matter saturates at
# its rest density: a packet of mass m occupies the sphere of its own mass at rho0,
#
#     R = (3 m / (4 pi rho0))^(1/3)        -- for a Gaussian packet, R = 1.5550 sigma, DERIVED
#
# (the Gaussian is the packet's APPEARANCE; its matter is the rest volume -- which is exactly the
# v1 diagnosis: "a real density edge is sharper than its rendering Gaussian"). Contact is the
# LENS where two rest volumes intersect. The matter there is double-occupied -- strain
# (2 rho0 - rho0)/rho0 = 1 -- so the linear-elastic energy density is B/2, and
#
#     U(d) = (B / 2) * V_lens(d)           F(d) = -dU/dd = (pi B / 8) (4 R^2 - d^2)   [equal R]
#
# Stiffness at small penetration h = 2R - d: F ~ (pi B R / 2) h -- LINEAR IN B, which inverts
# v1's logarithmic pathology and is the sharpest measurable contrast between the two models.
# DECLARED SCOPE: uniform unit strain in the lens (DEM-style linear overlap contact); Hertzian
# half-space redistribution (F ~ h^1.5) is a named unbuilt refinement, not this model. The tails
# carry NO contact force in v2 -- v1's cross-term is superseded, not summed with.

def rest_radius(m: float, rho0: float) -> float:
    """The sphere a packet's matter fills at rest density. No free parameter anywhere."""
    return (3.0 * float(m) / (4.0 * math.pi * float(rho0))) ** (1.0 / 3.0)


def lens_volume(r1: float, r2: float, d: float) -> float:
    """The intersection volume of two spheres a distance d apart -- the classic closed form
        V = pi (A - d)^2 (d^2 + 2 d A - 3 C^2) / (12 d),   A = r1 + r2,  C = r1 - r2
    valid for |r1 - r2| < d < r1 + r2; one sphere inside the other and no-overlap handled."""
    r1, r2, d = float(r1), float(r2), float(d)
    if d >= r1 + r2:
        return 0.0
    if d <= abs(r1 - r2):
        rmin = min(r1, r2)
        return 4.0 * math.pi * rmin ** 3 / 3.0
    a = r1 + r2
    c = r1 - r2
    return math.pi * (a - d) ** 2 * (d * d + 2.0 * d * a - 3.0 * c * c) / (12.0 * d)


def lens_volume_numeric(r1: float, r2: float, d: float, n: int = 200001) -> float:
    """The referee for the lens: V = pi INT max(0, min(r1^2 - z^2, r2^2 - (d-z)^2)) dz --
    a 1D quadrature, float64, accurate far past the closed form's float error."""
    z0 = min(-r1, d - r2)
    z1 = max(r1, d + r2)
    z = np.linspace(z0, z1, n)
    a = np.minimum(r1 * r1 - z * z, r2 * r2 - (d - z) ** 2)
    return float(np.trapezoid(math.pi * np.clip(a, 0.0, None), z))


def saturated_energy(m1: float, s1: float, m2: float, s2: float, d: float,
                     B: float, rho0: float) -> float:
    r1 = rest_radius(m1, rho0)
    r2 = rest_radius(m2, rho0)
    return 0.5 * float(B) * lens_volume(r1, r2, d)


def saturated_force(m1: float, s1: float, m2: float, s2: float, d: float,
                    B: float, rho0: float) -> float:
    """-dU/dd, analytic from the general lens formula. Positive = repulsive; exactly zero at and
    beyond first touch (d >= r1 + r2) -- the onset is continuous, not stepped."""
    r1 = rest_radius(m1, rho0)
    r2 = rest_radius(m2, rho0)
    d = float(d)
    if d >= r1 + r2 or d <= abs(r1 - r2) or d <= 0.0:
        return 0.0
    a = r1 + r2
    c = r1 - r2
    n_ = (a - d) ** 2 * (d * d + 2.0 * d * a - 3.0 * c * c)
    np_ = (-2.0 * (a - d) * (d * d + 2.0 * d * a - 3.0 * c * c)
           + (a - d) ** 2 * (2.0 * d + 2.0 * a))
    dv = math.pi * (np_ * d - n_) / (12.0 * d * d)
    return -0.5 * float(B) * dv


def saturated_equilibrium(load_N: float, m: float, s: float, B: float, rho0: float) -> float:
    """The separation where the saturated-contact force carries the load (equal packets).
    F is monotone in penetration on (0, 2R), so bisection; refuses an impossible load."""
    r = rest_radius(m, rho0)
    lo, hi = 1e-9 * r, 2.0 * r
    if saturated_force(m, s, m, s, lo, B, rho0) < load_N:
        raise ValueError(f"load {load_N:.3g} N exceeds the model's capacity at full overlap")
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if saturated_force(m, s, m, s, mid, B, rho0) > load_N:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def equilibrium_distance(load_N: float, m: float, s: float, B: float, rho0: float,
                         lo: float = None, hi: float = None) -> float:
    """The separation where the overlap force balances the load, for two equal grains --
    bisection on a force monotone-decreasing in d over [max force, tail]. Refuses if the load
    exceeds what the model can carry at the force peak (d = sqrt(S2))."""
    S2 = 2.0 * s * s
    d_peak = math.sqrt(S2)
    if lo is None:
        lo = d_peak
    if hi is None:
        hi = 20.0 * s
    if contact_force(m, s, m, s, lo, B, rho0) < load_N:
        raise ValueError(f"load {load_N:.3g} N exceeds the model's peak force "
                         f"{contact_force(m, s, m, s, lo, B, rho0):.3g} N -- no equilibrium")
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if contact_force(m, s, m, s, mid, B, rho0) > load_N:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)
