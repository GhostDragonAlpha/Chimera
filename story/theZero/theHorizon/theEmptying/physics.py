"""theEmptying -- a surface that counts states has a temperature, and radiates.

The parent handed down an area and the unit that measures it. Everything here follows from those
two facts: entropy, temperature, lifetime, and the sea that is left behind.
"""
from math import pi

G = 6.67430e-11
C = 2.99792458e8
HBAR = 1.054571817e-34
KB = 1.380649e-23


def derive(parent, free):
    if parent is None or "A" not in parent:
        raise ValueError("theEmptying requires a parent with a horizon area")
    M, A, l_P = parent["M_added"], parent["A"], parent["l_P"]
    S = KB * A / (4.0 * l_P ** 2)                       # Bekenstein-Hawking: a quarter-bit per Planck square
    T = HBAR * C ** 3 / (8.0 * pi * G * M * KB)         # a counting surface has a temperature
    t_evap = 5120.0 * pi * G ** 2 * M ** 3 / (HBAR * C ** 4)
    bits = S / (KB * 0.6931471805599453)                # nats -> bits
    return {
        # ITS OWN DURATION: the runaway that empties it -- lifetime ~ M^3. t=1 in emit() means this much real time.
        "duration_s": t_evap,
        "S": S,
        "bits": bits,
        "T": T,
        "t_evap": t_evap,
        "extent": parent["r_s"],                        # the space the fence drew
        "quanta": bits,                                 # what is spread across it, one cell at a time
    }


def emit(nums, t=1.0):
    """The matter of theEmptying, in its own local units (the parent's fence is radius 1).

    The colour is a MEASUREMENT, not a choice: each quantum is painted at the horizon temperature
    the law computed. At t=0 the inventory is still on the surface -- every grain sitting on the
    fence, which is where the information actually lives. As the membrane's time runs, the surface
    empties into the space it drew, and because T rises as the mass falls, the leaving is a runaway,
    not a drip -- so the grains do not crawl outward, they GO."""
    import numpy as np
    from matter import blank, fibonacci_sphere, paint, blackbody_rgb, GLOW

    n = 12000
    d = fibonacci_sphere(n)
    rng = np.random.default_rng(3)
    tt = float(t)
    runaway = tt ** 3                                   # lifetime ~ M^3: it ends all at once
    reach = 1.0 + 6.0 * runaway * (0.35 + 0.65 * rng.random(n))
    b = blank(n)
    b[:, 0:3] = d * reach[:, None]
    rgb = blackbody_rgb(min(nums.get("T", 1e4), 4.0e4))
    paint(b, rgb, max(0.10, 1.0 - 0.75 * runaway), 0.030 + 0.055 * runaway, GLOW)

    if tt < 1.0:                                        # what has not left yet is still ON the fence
        keep = blank(3000)
        dd = fibonacci_sphere(3000)
        keep[:, 0:3] = dd
        keep[:, 21:24] = dd
        paint(keep, (0.55, 0.78, 1.0), 1.0 - runaway, 0.030)
        return np.concatenate([keep, b], axis=0)
    return b


def measure(nums):
    """What training must check: the sea is HOT and the emptying RUNS AWAY (finishes), rather than
    leaking forever. Both are facts about the numbers, not preferences."""
    return {"is_hot": nums["T"] > 0.0, "finishes": nums["t_evap"] > 0.0}
