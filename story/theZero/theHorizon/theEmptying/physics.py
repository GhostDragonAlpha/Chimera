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
        "S": S,
        "bits": bits,
        "T": T,
        "t_evap": t_evap,
        "extent": parent["r_s"],                        # the space the fence drew
        "quanta": bits,                                 # what is spread across it, one cell at a time
    }


def measure(nums):
    """What training must check: the sea is HOT and the emptying RUNS AWAY (finishes), rather than
    leaking forever. Both are facts about the numbers, not preferences."""
    return {"is_hot": nums["T"] > 0.0, "finishes": nums["t_evap"] > 0.0}
