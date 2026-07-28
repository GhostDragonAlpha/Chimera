"""theZero -- the law of the seed.

r = 0. Nothing is derived from a parent here, because there is no parent: this is the seed.
The law states which operations are legal, and that is the entire content of the membrane --
it is what shapes every membrane after it.
"""

FORBIDDEN = "division"          # rho = M/0, K = 48G^2M^2/c^4 r^6, dr^2/(1-2GM/rc^2) -- all one act
ALLOWED = "addition"


def derive(parent, free):
    """The seed takes nothing and hands down the rule that shapes the next membrane."""
    return {
        "r": 0.0,
        "volume": 0.0,
        "hair": 3,                       # mass, charge, angular momentum -- and nothing else
        "forbidden": FORBIDDEN,
        "allowed": ALLOWED,
    }


def emit(nums, t=1.0):
    """The matter of theZero, in its own local units. `t` runs the membrane's own time, 0 -> 1.

    There is nothing here to draw except the one fact: everything arrives at a single point and the
    point has no size. So the movie IS the collapse -- at t=0 the grains are spread, at t=1 they are
    all at r=0 -- and what you are looking at at the end is the thing you may not divide by."""
    import numpy as np
    from matter import blank, fibonacci_sphere, paint

    n = 4000
    d = fibonacci_sphere(n)
    rng = np.random.default_rng(0)
    r0 = 0.35 + 0.65 * rng.random(n)[:, None]          # spread, at the beginning of this membrane
    b = blank(n)
    b[:, 0:3] = d * r0 * (1.0 - float(t))              # -> exactly 0.0 at t=1: r = 0
    return paint(b, (0.85, 0.87, 1.0), 0.85, 0.030)   # grain size is LOCAL too: ~1/30 of the extent
