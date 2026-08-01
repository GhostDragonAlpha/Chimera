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
        # ITS REAL SIZE: a point. Everything emits at radius ~1 locally, so this is
        # the only place the true scale is recorded -- and a human needs it to know what they see.
        "extent_m": 0.0,
        # ITS OWN DURATION: a point has no duration. t=1 in emit() means this much real time.
        "duration_s": 0.0,
        # `r` AND `volume` USED TO BE HERE, both 0.0, and both are gone. They said what extent_m
        # already says -- that this is a point -- under two more names, and nothing consumed
        # either: theHorizon reads exactly one thing from this membrane, `allowed`. They were also
        # the only two numbers at the root of the whole story carrying no readable unit, so
        # folding.py skipped them silently and reported itself clean over the rest.
        #
        # ONE QUANTITY, ONE NAME. Three keys for one fact is how three leg lengths got into one
        # leg further down this tree, and it costs a day to find. A point has an extent, the extent
        # is zero, and the extent is called extent_m.
        # THE NO-HAIR THEOREM, and it is a THEOREM, not a number anybody here chose. A stationary,
        # asymptotically flat solution of Einstein-Maxwell is completely fixed by exactly three
        # externally measurable quantities -- mass, electric charge, angular momentum -- and by
        # nothing else whatever: Israel 1967/68, Carter 1971, Hawking 1972, Robinson 1975. Everything
        # else that fell in is not hidden, it is GONE from the outside description.
        #
        # THIS LITERAL IS LEGAL BECAUSE IT IS TRUE IN AN EMPTY UNIVERSE. It is not inherited because
        # theZero is the seed and has no parent to inherit from, and it is not a copy of anything a
        # parent derives -- it is a count of degrees of freedom proved from the field equations, so it
        # is the same 3 in any story anyone ever tells. It is also why the very next membrane can
        # exist: three numbers is few enough that a horizon can be pinned by them.
        "hair": 3,
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
