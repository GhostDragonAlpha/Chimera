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
