"""theHorizon -- the first addition creates a length.

The parent forbids division and permits addition. So this membrane's law is what addition
produces: a horizon radius, a quantum length, their crossing, and the units that crossing sets.
"""
from math import pi, sqrt

G = 6.67430e-11          # m^3 kg^-1 s^-2
C = 2.99792458e8         # m/s
HBAR = 1.054571817e-34   # J s


def schwarzschild(M):
    """The horizon a mass draws around a point."""
    return 2.0 * G * M / C ** 2


def compton(M):
    """The same mass read as a quantum."""
    return HBAR / (M * C)


def crossing():
    """The one mass where the two lengths are equal -- black hole and electron the same SIZE."""
    return sqrt(HBAR * C / (2.0 * G))


def derive(parent, free):
    if parent is None or parent.get("allowed") != "addition":
        raise ValueError("theHorizon requires a parent that permits addition")
    M = float(free.get("M_added", crossing()))      # THE HUMAN's dial: how much is added to zero
    l_P = sqrt(HBAR * G / C ** 3)
    t_P = l_P / C
    m_P = sqrt(HBAR * C / G)
    return {
        "M_added": M,
        "r_s": schwarzschild(M),
        "lambda_C": compton(M),
        "M_crossing": crossing(),
        "l_P": l_P,
        "t_P": t_P,
        "m_P": m_P,
        "A": 4.0 * pi * schwarzschild(M) ** 2,
    }


def measure(nums):
    """What training must check: the crossing is where the two lengths agree, and it lands at the
    Planck scale. Exact, so the residual is a check on the arithmetic, not a fitted number."""
    Mx = nums["M_crossing"]
    return {"crossing_residual": abs(schwarzschild(Mx) - compton(Mx)) / compton(Mx),
            "crossing_over_planck_mass": Mx / nums["m_P"]}
