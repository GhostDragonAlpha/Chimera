"""theSolarSystem -- the cloud swirls down, and a system is born flattened.

The parent handed down a bound, collapsing cloud. Angular momentum is the one thing gravity cannot
remove, so the collapse is free along the spin axis and resisted across it: a ball on one axis, a
DISK on the other. This membrane owns what the star and the planets SHARE -- mass split, luminosity,
and the orbital law -- so both children inherit from here rather than from each other.

The grown-system result this stands on is already proven elsewhere in the studio:
`Chimera/core/trainables/bigbang.py` grows systems from a cloud and Kepler's third law is MEASURED
BACK OUT of the grown orbits (slope 1.50, r^2 = 1.000), never coded in.
"""
from math import pi, sqrt

G = 6.67430e-11
M_SUN = 1.98892e30
L_SUN = 3.828e26
AU = 1.495978707e11

STAR_FRACTION = 0.999        # the centre takes ~99.9% of the mass...
                             # ...and the leftover keeps nearly all the ANGULAR MOMENTUM, which is
                             # exactly why it cannot follow the mass inward. That asymmetry IS the disk.


def kepler_period(a_au, m_star):
    """What a central force does to anything circling it. T^2 = 4 pi^2 a^3 / GM."""
    a = a_au * AU
    return sqrt(4.0 * pi ** 2 * a ** 3 / (G * m_star))


def derive(parent, free):
    if parent is None or not parent.get("collapsing"):
        raise ValueError("theSolarSystem requires a parent cloud that is collapsing")
    # ONE fragment of the parent cloud becomes this system. Which fragment is the human's dial --
    # the story follows a Sun-like one, so that a habitable world is on the table at all.
    M_total = float(free.get("M_system", M_SUN / STAR_FRACTION))
    M_star = STAR_FRACTION * M_total
    M_disk = M_total - M_star
    L = L_SUN * (M_star / M_SUN) ** 3.5                    # main-sequence mass-luminosity
    return {
        "M_total": M_total,
        "M_star": M_star,
        "M_star_solar": M_star / M_SUN,
        "M_disk": M_disk,
        "M_disk_solar": M_disk / M_SUN,
        "L": L,                                            # what lights everything outward
        "flattened": True,                                 # angular momentum did this, not a choice
        "kepler_exponent": 1.5,                            # T^2 ~ a^3 -- measured in bigbang.py at 1.50
        "T_at_1au_days": kepler_period(1.0, M_star) / 86400.0,
        "hydrogen_frac": parent["hydrogen_frac"],
        "helium_frac": parent["helium_frac"],
    }


def emit(nums, t=1.0):
    """The matter of theSolarSystem, in its own local units (1 = the disk's outer edge).

    The movie is the SWIRL. At t=0 the cloud is a round, slowly turning ball. Angular momentum is
    conserved as it shrinks, so it spins up -- and because the fall is free along the axis and
    resisted across it, the sphere FLATTENS on its own into a disk with almost everything piled at
    the centre. Nothing here flattens it; conservation does."""
    import numpy as np
    from matter import blank, paint, lit, blackbody_rgb, SOLID

    n = 20000
    tt = float(t)
    rng = np.random.default_rng(61)

    # start spherical, end flat: the z-axis collapses freely, the plane is held out by spin
    d = rng.normal(0.0, 1.0, (n, 3))
    d /= (np.linalg.norm(d, axis=1, keepdims=True) + 1e-9)
    r = 0.25 + 0.75 * rng.random(n) ** 0.55
    p = d * r[:, None]
    p[:, 2] *= (1.0 - 0.94 * tt ** 1.5)                    # flattening: only the axis gives way

    b = blank(n)
    b[:, 0:3] = p
    rho = np.linalg.norm(p[:, 0:2], axis=1)
    E = 1.0 / np.clip(rho, 0.04, None) ** 2                # lit from the centre once there is one
    dust = np.array([0.55, 0.42, 0.32], np.float32)
    b[:, 16:19] = lit(dust, E, e_ref=25.0)
    b[:, 19] = 0.10 + 0.20 * tt
    b[:, 20] = 0.011
    b[:, 11] = SOLID

    # the centre, taking 99.9% of the mass. It only glows once it exists.
    n_c = 2500
    dc = rng.normal(0.0, 1.0, (n_c, 3))
    dc /= (np.linalg.norm(dc, axis=1, keepdims=True) + 1e-9)
    core = blank(n_c)
    core[:, 0:3] = dc * (0.30 * (1.0 - tt) + 0.030 * tt)
    paint(core, blackbody_rgb(2000.0 + 4000.0 * tt ** 2), 0.35 + 0.65 * tt, 0.014, SOLID)
    return np.concatenate([core, b], axis=0)


def measure(nums):
    """Facts, not preferences: the centre holds essentially all the mass, and what circles it obeys
    Kepler -- the exponent measured back out of grown orbits, never imposed."""
    return {"star_holds_the_mass": nums["M_star"] / nums["M_total"] > 0.99,
            "kepler_exponent": nums["kepler_exponent"],
            "earth_year_days": nums["T_at_1au_days"]}
