"""complex_fresnel.py -- Stage 20: the full complex amplitudes. TIR's phase, circularity, metals.

WHAT THE REAL-ARITHMETIC MODULE COULD NOT SAY. Stage 17 tracks two POWER fractions, so it knows
R_s and R_p but not their relative PHASE -- and phase is where two named-unbuilt items live:

  * Under TOTAL INTERNAL REFLECTION |r| = 1 for both polarizations, but each picks up a different
    phase. The relative retardance Delta = delta_p - delta_s converts linear polarization toward
    CIRCULAR -- which is how a Fresnel rhomb makes a quarter-wave plate out of nothing but glass
    and geometry. The maximum single-bounce retardance is closed-form in the index ratio alone:

        tan(Delta_max / 2) = (1 - n^2) / (2 n),   at sin^2(theta) = 2 n^2 / (1 + n^2),  n = n2/n1

    Glass (1.51) gives 45.94 degrees -- two bounces make a quarter wave, which IS the rhomb, at
    the classic 54.6-degree cut. Water's internal ratio gives only 33.4 degrees: A FRESNEL RHOMB
    CANNOT BE MADE OF WATER in two bounces, and that impossibility is a derived, testable fact.

  * A METAL is a complex index N = n + ik, and the SAME amplitude formulas handle it once the
    arithmetic is complex. Cited constants (Johnson & Christy 1972) enter the way B and G did --
    and colour comes OUT: copper's R rises from 62% (blue) to 94% (red) with nothing tuned, which
    is WHY copper is copper-coloured. A colour is a measurement, again. Metals also lose the
    Brewster ZERO -- R_p keeps a nonzero pseudo-Brewster minimum, which is why metallic glare
    never fully polarizes and a polarising filter cannot kill it.

The dielectric-power limit of this module must agree with Stage 17's real-arithmetic module to
float precision -- two implementations, one physics, checked not assumed.
"""
from __future__ import annotations

import cmath
import math
import sys
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parents[2]
_STORY = _ROOT / "story"
if str(_STORY) not in sys.path:
    sys.path.insert(0, str(_STORY))


def amplitudes(n1: complex, n2: complex, cos_i: float):
    """(r_s, r_p) as COMPLEX amplitudes. The branch of the complex square root with
    non-negative imaginary part keeps the transmitted wave decaying, which is the physical one."""
    n1, n2 = complex(n1), complex(n2)
    ci = complex(cos_i)
    st2 = (n1 / n2) ** 2 * (1.0 - ci * ci)
    ct = cmath.sqrt(1.0 - st2)
    if ct.imag < 0.0:
        ct = -ct
    r_s = (n1 * ci - n2 * ct) / (n1 * ci + n2 * ct)
    r_p = (n2 * ci - n1 * ct) / (n2 * ci + n1 * ct)
    return r_s, r_p


def powers(n1: complex, n2: complex, cos_i: float):
    r_s, r_p = amplitudes(n1, n2, cos_i)
    return abs(r_s) ** 2, abs(r_p) ** 2


def tir_retardance(n1: float, n2: float, cos_i: float) -> float:
    """Delta = delta_p - delta_s under TIR, from the complex amplitudes' own phases."""
    r_s, r_p = amplitudes(n1, n2, cos_i)
    d = cmath.phase(r_p) - cmath.phase(r_s)
    while d <= -math.pi:
        d += 2.0 * math.pi
    while d > math.pi:
        d -= 2.0 * math.pi
    return d


def max_retardance(n1: float, n2: float):
    """(Delta_max, theta_at_max): the closed forms quoted in the module docstring."""
    n = float(n2) / float(n1)
    if n >= 1.0:
        return 0.0, None
    d = 2.0 * math.atan((1.0 - n * n) / (2.0 * n))
    th = math.asin(math.sqrt(2.0 * n * n / (1.0 + n * n)))
    return d, th


def rhomb_angle(n_glass: float, target: float = math.pi / 4.0):
    """The incidence at which ONE internal bounce retards by target (45 deg for the classic
    two-bounce quarter-wave rhomb). Found on the retardance curve itself; None if unreachable."""
    d_max, th_max = max_retardance(n_glass, 1.0)
    if d_max < target:
        return None
    th_c = math.asin(1.0 / n_glass)
    lo, hi = th_c + 1e-9, th_max          # retardance rises from 0 at theta_c to the max
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if abs(tir_retardance(n_glass, 1.0, math.cos(mid))) < target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def stokes_after(r_s: complex, r_p: complex, in_s: complex = 1.0, in_p: complex = 1.0):
    """Normalised Stokes (Q, U, V) of the outgoing field for a given incident (s, p) amplitude
    pair. V is the circular fraction -- the number a quarter-wave device must drive to 1."""
    es, ep = r_s * complex(in_s), r_p * complex(in_p)
    i = abs(es) ** 2 + abs(ep) ** 2
    if i <= 0.0:
        return 0.0, 0.0, 0.0
    q = (abs(es) ** 2 - abs(ep) ** 2) / i
    u = 2.0 * (es * ep.conjugate()).real / i
    v = 2.0 * (es * ep.conjugate()).imag / i
    return q, u, v


def metal_reflectance_rgb(nk_rgb, cos_i: float = 1.0):
    """(R_r, R_g, R_b) for a metal from its cited per-channel (n, k) -- unpolarized average.
    This is where a metal's COLOUR comes from, with nothing tuned."""
    out = []
    for n, k in nk_rgb:
        rs, rp = powers(1.0, complex(n, k), cos_i)
        out.append(0.5 * (rs + rp))
    return tuple(out)


def pseudo_brewster(n: float, k: float):
    """(theta_min, R_p_min) for a metal: R_p dips but never reaches zero -- the reason a
    polarising filter cannot kill metallic glare the way it kills water glare."""
    best_t, best_r = None, float("inf")
    for t in np.radians(np.linspace(0.1, 89.9, 1797)):
        _, rp = powers(1.0, complex(n, k), math.cos(t))
        if rp < best_r:
            best_r, best_t = rp, float(t)
    return best_t, best_r
