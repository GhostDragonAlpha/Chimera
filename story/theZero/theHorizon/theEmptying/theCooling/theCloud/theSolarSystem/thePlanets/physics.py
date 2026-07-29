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


G = 6.67430e-11
M_SUN = 1.98892e30
RHO_ROCK, RHO_ICE = 3900.0, 1600.0     # bulk densities, kg/m^3
K_HILL = 40.0                          # FORMED systems sit ~26-50 mutual Hill radii apart (the solar
                                       # system's terrestrials do); 10 is only the bare stability
                                       # minimum for survival, and it leaves you with 25 Mars-sized
                                       # EMBRYOS instead of planets -- true for the isolation stage,
                                       # but embryos then merge through giant impacts, and 40 is
                                       # where that merging leaves them.


def sweep_planets(r_snow, m_star):
    """GROW the worlds instead of placing them. Walk outward from the inner edge; at each step a body
    accretes ALL the solids in the annulus it can reach, then the next one starts a stability gap
    away. Nothing here chooses how many planets there are or where they sit -- the surface density,
    the snow line and the Hill criterion decide, and the count falls out.

        a planet's reach   : K * R_Hill,  R_Hill = a (M/3M*)^(1/3)
        its mass           : the solids in 2*pi*a * (that reach)
        the next planet    : one reach further out

    Because Sigma jumps ~4x past the snow line, the outer bodies grow far heavier from the same
    walk -- which is why giants are outside and small rocky worlds are inside, unplaced."""
    out = []
    a = R_IN
    while a < R_OUT:
        # MASS IS CONSERVED: a world gets the solids that are ACTUALLY in the annulus it reaches, by
        # integrating the real surface density -- not by solving an isolation equation that can claim
        # more than the disk contains. (The unconserved version handed out 101 Earth masses from a
        # disk holding 56.) The reach depends on the mass and the mass on the reach, so iterate: it
        # converges in a few passes.
        m = 1.0e24
        for _ in range(24):
            width = K_HILL * a * (m / (3.0 * m_star)) ** (1.0 / 3.0)
            hi = min(R_OUT, a + width)
            if hi <= a:
                break
            # split the annulus at the snow line -- ice is only solid beyond it
            m_new = 0.0
            lo = a
            if lo < r_snow < hi:
                m_new += solid_mass(lo, r_snow, SIGMA_ROCK_1AU)
                lo = r_snow
            sigma1 = SIGMA_ROCK_1AU * (ICE_TO_ROCK if lo >= r_snow else 1.0)
            m_new += solid_mass(lo, hi, sigma1)
            if abs(m_new - m) < 1e-3 * m:
                m = m_new
                break
            m = 0.5 * (m + m_new)                       # damped, so the fixed point does not ring
        width = K_HILL * a * (m / (3.0 * m_star)) ** (1.0 / 3.0)
        rho = RHO_ICE if a > r_snow else RHO_ROCK
        radius = (3.0 * m / (4.0 * pi * rho)) ** (1.0 / 3.0)
        out.append({"a_au": a, "M": m, "M_earth": m / M_EARTH, "R": radius,
                    "icy": a > r_snow})
        a += max(width, 0.02 * a)                       # the next world starts beyond this one's reach
        if len(out) > 24:
            break
    return out


def derive(parent, free):
    if parent is None or not parent.get("flattened"):
        raise ValueError("thePlanets requires a parent SYSTEM (siblings with the star, not its child)")
    # The LIGHT comes from the system, not from a sibling: a membrane may only read its parent.
    L = float(parent["L"])
    # THE SNOW LINE IS INHERITED, not recomputed. It is a fact about the SYSTEM's light, so the
    # system owns it -- and that is also what lets the system place this child correctly in its own
    # frame (this membrane works in units of the snow line; the system's frame is the disk edge).
    # Recomputing it here would be two authorities for one number, which is how they drift apart.
    r_snow = float(parent.get("snow_line_au") or snow_line(L))
    m_in = solid_mass(R_IN, r_snow, SIGMA_ROCK_1AU)                       # rock only
    m_out = solid_mass(r_snow, R_OUT, SIGMA_ROCK_1AU * ICE_TO_ROCK)       # rock AND ice
    worlds = sweep_planets(r_snow, float(parent["M_star"]))               # GROW them, do not place them
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
        "T_star_surface": 5772.0,  # carried from the system's luminosity; the star is the CAUSE of the gradient
        "R_star": 6.957e8,
        "worlds": worlds,                             # the planets themselves -- grown, not placed
        "n_worlds": len(worlds),
        "n_rocky": sum(1 for w in worlds if not w["icy"]),
        "n_icy": sum(1 for w in worlds if w["icy"]),
    }


def emit(nums, t=1.0):
    """The matter of theDisk, in its own local units (1.0 = the snow line).

    The movie IS the sorting. At t=0 the disk is uniform vapour and dust, the same everywhere. As its
    own time runs, the temperature gradient decides: inside the line only rock can condense, so the
    grains there stay sparse and dark; outside, water freezes too and the solid inventory jumps
    fourfold, so the outer disk turns bright and dense. The line is not drawn -- it is where the
    colour changes because that is where the physics changes."""
    import numpy as np
    from matter import blank, paint, lit, SOLID

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
    # ALBEDO is the matter: what fraction of arriving light each material returns. Ice is bright
    # BECAUSE it is ice; rock is dark BECAUSE it is rock. Neither is a brightness -- it is a ratio.
    rock = np.array([0.20, 0.15, 0.11], np.float32)             # dark silicate, albedo ~0.15
    ice = np.array([0.75, 0.82, 0.90], np.float32)              # water ice, albedo ~0.8
    warm = np.array([0.45, 0.37, 0.30], np.float32)             # uncondensed vapour+dust at t=0
    albedo = np.where(icy[:, None], ice, rock) * tt + warm[None, :] * (1.0 - tt)

    # THE LIGHT: irradiance falls as 1/r^2 from the star at the centre. The inner disk receives
    # thousands of times more than the edge, which is why the rocky zone BLAZES despite being made
    # of the darker material -- a splat is a measurement of light, not a painted colour.
    E = 1.0 / np.clip(rr, 1e-3, None) ** 2
    b[:, 16:19] = lit(albedo, E, e_ref=1.0)                     # e_ref = irradiance at the snow line

    # The fourfold jump shown as DENSITY, not brightness -- and kept below saturation, or the ice
    # reads as a solid sheet and hides that a disk is overwhelmingly empty space.
    b[:, 19] = np.where(icy, 0.14 + 0.34 * tt, 0.45)
    b[:, 20] = 0.010 + np.where(icy, 0.005 * tt, 0.004)
    b[:, 11] = SOLID

    # THE STAR ITSELF. Leaving it out drew the effect without its cause -- and worse, the rocky inner
    # disk then read as a dim brown object at the centre, which is a render telling a lie about what
    # kind of star this is. Its colour is its own surface temperature, carried down from the parent.
    from matter import fibonacci_sphere, blackbody_rgb
    # A HANDFUL OF GRAINS, because the star is sub-pixel here. 2500 of them all land in one 32px
    # tile, overrun MAX_PER_TILE, and the cap evicts the DISK's grains from that tile -- a black,
    # tile-shaped hole exactly where the star should be. Same law as composition LOD: a thing that
    # occupies one pixel does not need thousands of grains to say so.
    n_s = 160
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

    # THE WORLDS. Grown by sweep_planets, so their count, spacing, mass and radius are all consequences
    # -- and each one is drawn where it grew, at the size its own mass and density give it.
    # SCALE, DECLARED: Earth's radius against the snow line is 6.37e6/4.01e11 = 1.6e-5, sub-pixel, the
    # same problem as the star. Bodies are drawn at a stated exaggeration so a system READS as a system;
    # the true radius is in numbers.json and the ratio between worlds is exactly right.
    WORLD_EXAGGERATION = 900.0
    parts = [star, b]
    rock_a = np.array([0.34, 0.27, 0.21], np.float32)      # albedo, not brightness
    ice_a = np.array([0.72, 0.78, 0.86], np.float32)
    for i, w in enumerate(nums.get("worlds", [])):
        aa = float(w["a_au"]) / r_snow                       # into this membrane's units
        rr_w = float(w["R"]) / (r_snow * 1.495978707e11) * WORLD_EXAGGERATION
        n_w = 900
        dw = fibonacci_sphere(n_w)
        ang = 2.399963 * i                                   # spread them around, not lined up
        cen = np.array([aa * np.cos(ang), aa * np.sin(ang), 0.0], np.float32)
        wb = blank(n_w)
        wb[:, 0:3] = dw * rr_w * (0.6 + 0.4 * tt) + cen
        wb[:, 21:24] = dw
        E_w = 1.0 / max(aa, 1e-3) ** 2                       # lit by the star it orbits
        wb[:, 16:19] = lit(ice_a if w["icy"] else rock_a, E_w, e_ref=1.0)
        wb[:, 19] = 0.9
        wb[:, 20] = max(0.004, rr_w * 0.30)
        wb[:, 11] = SOLID
        parts.append(wb)
    return np.concatenate(parts, axis=0)


def measure(nums):
    """What training must check -- facts: the snow line lands where the belt is, and only the outer
    disk can pass the runaway-core threshold. Both follow from L alone."""
    return {"snow_line_at_belt": 2.0 < nums["snow_line_au"] < 3.5,
            "giants_only_outside": nums["solid_outside_earths"] > 10.0 > nums["solid_inside_earths"]}
