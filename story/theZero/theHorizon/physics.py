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


FREE = {
    # THE HUMAN'S ONE DIAL AT THE SEED: how much is added to zero. Everything about the fence,
    # and every scale below it, follows from this single number.
    "M_added": {"label": "mass added to zero", "default": 1.539e-8,
                "lo": 1.0e-9, "hi": 1.0e-6, "unit": "kg", "log": True},
}


def derive(parent, free):
    if parent is None or parent.get("allowed") != "addition":
        raise ValueError("theHorizon requires a parent that permits addition")
    M = float(free.get("M_added", crossing()))      # THE HUMAN's dial: how much is added to zero
    l_P = sqrt(HBAR * G / C ** 3)
    t_P = l_P / C
    m_P = sqrt(HBAR * C / G)
    return {
        # ITS REAL SIZE: the fence it drew. Everything emits at radius ~1 locally, so this is
        # the only place the true scale is recorded -- and a human needs it to know what they see.
        "extent_m": schwarzschild(M),
        # ITS OWN DURATION: the first tick it made. t=1 in emit() means this much real time.
        "duration_s": t_P,
        "M_added": M,
        "r_s": schwarzschild(M),
        "lambda_C": compton(M),
        "M_crossing": crossing(),
        "l_P": l_P,
        "t_P": t_P,
        "m_P": m_P,
        "A": 4.0 * pi * schwarzschild(M) ** 2,
    }


def emit(nums, t=1.0):
    """The matter of theHorizon, in its own local units: the fence is drawn at radius 1 = r_s.

    At t=0 there is only the point (the parent's zero). As the membrane's time runs, the horizon
    the added mass demands appears around it -- the first LENGTH, hence the first boundary, hence
    the first membrane. The interior is left empty on purpose: it has no hair to draw."""
    import numpy as np
    from matter import blank, fibonacci_sphere, paint, GLOW

    n_shell, n_point = 9000, 500
    d = fibonacci_sphere(n_shell)
    shell = blank(n_shell)
    shell[:, 0:3] = d * float(t)                       # the fence grows to r_s (= 1 locally)
    shell[:, 21:24] = d                                # outward normal -> cull the far side
    paint(shell, (0.45, 0.70, 1.00), 1.0, 0.032)       # grain size is LOCAL: ~1/30 of the extent

    core = blank(n_point)
    core[:, 0:3] = fibonacci_sphere(n_point) * 0.012   # the point you may not divide by
    paint(core, (1.0, 1.0, 1.0), 1.0, 0.018)
    return np.concatenate([core, shell], axis=0)


def measure(nums):
    """What training must check: the crossing is where the two lengths agree, and it lands at the
    Planck scale. Exact, so the residual is a check on the arithmetic, not a fitted number."""
    Mx = nums["M_crossing"]
    return {"crossing_residual": abs(schwarzschild(Mx) - compton(Mx)) / compton(Mx),
            "crossing_over_planck_mass": Mx / nums["m_P"]}
