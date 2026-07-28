"""theDisk -- a temperature gradient sorts the matter, and one line decides the architecture.

The parent handed down a star with a luminosity, and the leftover that could not fall in. Heating
the disk from its centre gives it T ~ r^-1/2, and because every substance condenses at its own
temperature, that single gradient decides what is solid where -- and therefore what can be built.
"""
from math import pi

SIGMA_SB = 5.670374419e-8
AU = 1.495978707e11
M_EARTH = 5.9722e24
L_SUN = 3.828e26

T_ICE = 170.0                # water condenses here: the one temperature that matters most
ICE_TO_ROCK = 4.2            # water is ~4x as abundant as rock -> the solid inventory JUMPS
SIGMA_ROCK_1AU = 7.0         # minimum-mass nebula: rock surface density at 1 AU, g/cm^2
R_IN, R_OUT = 0.4, 30.0      # where the disk holds together, AU
M_CRIT_CORE = 10.0           # Earth masses: past this a core takes gas faster than it arrives


def temperature(r_au, L):
    """A disk lit from its centre. Nothing sorts the material -- this gradient does."""
    r = r_au * AU
    return (L / (16.0 * pi * SIGMA_SB * r * r)) ** 0.25


def snow_line(L, t_ice=T_ICE):
    """The radius where the star's own light has dimmed to water's condensation temperature.
    Solved from L, never placed: invert T(r) = t_ice."""
    return ((L / (16.0 * pi * SIGMA_SB * t_ice ** 4)) ** 0.5) / AU


def solid_mass(r0_au, r1_au, sigma_1au):
    """Mass of solids in an annulus for Sigma(r) = sigma_1au * (r/AU)^{-3/2} (minimum-mass nebula).

        M = int 2*pi*r*Sigma dr = 4*pi*sigma_1au*AU^2*(sqrt(r1) - sqrt(r0))     [r in AU]
    """
    sigma_si = sigma_1au * 10.0                              # g/cm^2 -> kg/m^2
    return 4.0 * pi * sigma_si * AU ** 2 * (r1_au ** 0.5 - r0_au ** 0.5)


def derive(parent, free):
    if parent is None or not parent.get("leftover_disk"):
        raise ValueError("theDisk requires a parent star that left a disk behind")
    L = float(parent["L"])
    r_snow = snow_line(L)
    m_in = solid_mass(R_IN, r_snow, SIGMA_ROCK_1AU)                       # rock only
    m_out = solid_mass(r_snow, R_OUT, SIGMA_ROCK_1AU * ICE_TO_ROCK)       # rock AND ice
    return {
        "L": L,
        "snow_line_au": r_snow,                       # ~2.7 AU: computed, and it is the asteroid belt
        "T_at_1au": temperature(1.0, L),
        "T_at_snow": temperature(r_snow, L),
        "solid_inside_earths": m_in / M_EARTH,        # ~3: enough for small worlds, nothing more
        "solid_outside_earths": m_out / M_EARTH,      # ~54: enough to pass the runaway threshold
        "inventory_jump": ICE_TO_ROCK,
        "giants_possible": (m_out / M_EARTH) > M_CRIT_CORE,
        "rocky_inside": True,
        "r_rocky_au": 0.5 * (R_IN + r_snow),          # where the rocky world this story follows sits
        "T_star_surface": float(parent["T_surface"]),  # the star is the CAUSE of the gradient; carry it
        "R_star": float(parent["R"]),
    }


def emit(nums, t=1.0):
    """The matter of theDisk, in its own local units (1.0 = the snow line).

    The movie IS the sorting. At t=0 the disk is uniform vapour and dust, the same everywhere. As its
    own time runs, the temperature gradient decides: inside the line only rock can condense, so the
    grains there stay sparse and dark; outside, water freezes too and the solid inventory jumps
    fourfold, so the outer disk turns bright and dense. The line is not drawn -- it is where the
    colour changes because that is where the physics changes."""
    import numpy as np
    from matter import blank, paint, SOLID

    n = 24000
    tt = float(t)
    rng = np.random.default_rng(7)
    r_snow = float(nums.get("snow_line_au", 2.7))
    r_in, r_out = R_IN / r_snow, R_OUT / r_snow                # in units of the snow line
    # sample r ~ Sigma*r ~ r^-1/2  ->  r = (u*(r_out^1.5 - r_in^1.5) + r_in^1.5)^(2/3)
    u = rng.random(n)
    rr = (u * (r_out ** 1.5 - r_in ** 1.5) + r_in ** 1.5) ** (2.0 / 3.0)
    th = rng.random(n) * 2.0 * pi
    b = blank(n)
    b[:, 0] = rr * np.cos(th)
    b[:, 1] = rr * np.sin(th)
    b[:, 2] = rng.normal(0.0, 0.05 * rr * (1.0 - 0.6 * tt), n)  # it settles thinner as it cools

    icy = rr > 1.0                                              # beyond the snow line water is solid
    rock = np.array([0.62, 0.45, 0.32], np.float32)
    ice = np.array([0.80, 0.90, 1.00], np.float32)
    col = np.where(icy[:, None], ice, rock)
    # at t=0 nothing has condensed yet: uniform warm vapour. the sorting APPEARS as time runs.
    warm = np.array([0.75, 0.62, 0.50], np.float32)
    b[:, 16:19] = warm * (1.0 - tt) + col * tt

    # The fourfold jump shown as DENSITY, not brightness -- and kept below saturation, or the ice
    # reads as a solid sheet and hides that a disk is overwhelmingly empty space.
    b[:, 19] = np.where(icy, 0.14 + 0.34 * tt, 0.45)
    b[:, 20] = 0.010 + np.where(icy, 0.005 * tt, 0.004)
    b[:, 11] = SOLID

    # THE STAR ITSELF. Leaving it out drew the effect without its cause -- and worse, the rocky inner
    # disk then read as a dim brown object at the centre, which is a render telling a lie about what
    # kind of star this is. Its colour is its own surface temperature, carried down from the parent.
    from matter import fibonacci_sphere, blackbody_rgb
    n_s = 2500
    d = fibonacci_sphere(n_s)
    star = blank(n_s)
    # SCALE, DECLARED RATHER THAN HIDDEN. True size here is R_star / snow_line = 6.96e8 / 4.01e11
    # = 0.0017 -- SUB-PIXEL, invisible. This draws it at 0.055, an exaggeration of ~32x, for the same
    # reason games draw mountains 40x too tall: at true scale the thing that matters most cannot be
    # seen. The number is written down so the lie is auditable and can be replaced by a point light
    # (which is the honest fix: a star at this scale is not a sphere, it is a source).
    STAR_EXAGGERATION = 32.0
    star[:, 0:3] = d * (float(nums.get("R_star", 6.957e8)) / (nums["snow_line_au"] * 1.495978707e11)
                        * STAR_EXAGGERATION)
    star[:, 21:24] = d
    paint(star, blackbody_rgb(float(nums.get("T_star_surface", 5772.0))), 1.0, 0.006, SOLID)
    return np.concatenate([star, b], axis=0)


def measure(nums):
    """What training must check -- facts: the snow line lands where the belt is, and only the outer
    disk can pass the runaway-core threshold. Both follow from L alone."""
    return {"snow_line_at_belt": 2.0 < nums["snow_line_au"] < 3.5,
            "giants_only_outside": nums["solid_outside_earths"] > 10.0 > nums["solid_inside_earths"]}
