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
R_STAR_SUN = 6.957e8      # the Sun's photosphere -- the normalisation for R ~ M^0.8
AU = 1.495978707e11

DISK_EDGE_AU = 30.0          # where this system's disk stops holding together
STAR_FRACTION = 0.999        # the centre takes ~99.9% of the mass...
                             # ...and the leftover keeps nearly all the ANGULAR MOMENTUM, which is
                             # exactly why it cannot follow the mass inward. That asymmetry IS the disk.


def kepler_period(a_au, m_star):
    """What a central force does to anything circling it. T^2 = 4 pi^2 a^3 / GM."""
    a = a_au * AU
    return sqrt(4.0 * pi ** 2 * a ** 3 / (G * m_star))


import clock as _clk


FREE = {
    # WHICH FRAGMENT this system is -- said as a POSITION IN THE GALAXY'S OWN DISTRIBUTION, not as a
    # mass in kilograms.
    #
    # It used to be a mass, and that was the last broken edge in the tree: `audit.py --slider` showed
    # theGalaxy's dial moving NOTHING below it, because the system's mass did not come from the
    # galaxy at all -- it was a free number with a typed default, and the galaxy->system edge carried
    # nothing. A percentile fixes it, because the mass it maps to is the galaxy's answer: the
    # characteristic mass comes from the Jeans mass of a cold core, and change the galaxy's core
    # conditions and every system in it moves.
    #
    # The default is where the SUN sits in this galaxy's IMF: heavier than about 93% of stars. That
    # is a fact, not a preference -- and it is why "an ordinary star" is already an unusual one.
    "imf_percentile": {"label": "which fragment", "default": 0.933,
                       "lo": 0.02, "hi": 0.9995, "unit": "of stars are lighter"},
}


def _imf_mass(p, m_lo, m_hi, m_char, slope_high, n=2400):
    """Invert the galaxy's mass function: percentile -> fragment mass, in solar masses.

    The SHAPE is the parent's -- its characteristic mass, its floor, its slope all arrive through
    `numbers`. This only reads the distribution off; it does not decide what the distribution is.
    (Restating the law here would be two authorities for one curve, which is how they drift.)"""
    SLOPE_MID, SLOPE_LOW, M_BROWN = -1.3, -0.3, 0.08
    xs, ws = [], []
    for i in range(n):
        m = m_lo * (m_hi / m_lo) ** (i / (n - 1.0))
        if m >= m_char:
            w = (m / m_char) ** slope_high
        elif m >= M_BROWN:
            w = (m / m_char) ** SLOPE_MID
        else:
            w = (M_BROWN / m_char) ** SLOPE_MID * (m / M_BROWN) ** SLOPE_LOW
        xs.append(m); ws.append(w * m)
    tot, run = sum(ws), 0.0
    p = min(max(float(p), 1e-6), 1.0 - 1e-9)
    for x, w in zip(xs, ws):
        run += w
        if run / tot >= p:
            return x
    return xs[-1]


def derive(parent, free):
    if parent is None or not parent.get("collapsing"):
        raise ValueError("theSolarSystem requires a parent cloud that is collapsing")
    if "m_char_solar" not in parent:
        raise ValueError("theSolarSystem requires a parent GALAXY carrying its mass function")
    # ONE fragment of the parent galaxy's clouds becomes this system, and its mass is DRAWN FROM THE
    # DISTRIBUTION THE GALAXY DERIVED -- not chosen here. The galaxy walked the Jeans mass down eight
    # orders of magnitude to where fragmentation stops, which is what fixes the characteristic
    # stellar mass; this membrane only picks a position in that distribution.
    p_imf = float(free.get("imf_percentile", 0.933))
    m_char = float(parent["m_char_solar"])
    m_lo, m_hi = float(parent["m_floor_solar"]), float(parent["m_max_solar"])
    M_frag_solar = _imf_mass(p_imf, m_lo, m_hi, m_char, float(parent["imf_slope_high"]))
    M_total = M_frag_solar * M_SUN / STAR_FRACTION
    M_star = STAR_FRACTION * M_total
    M_disk = M_total - M_star
    L = L_SUN * (M_star / M_SUN) ** 3.5                    # main-sequence mass-luminosity
    # THE SNOW LINE IS A FACT ABOUT THIS SYSTEM'S LIGHT, so it belongs here and the planets INHERIT
    # it rather than recomputing it. It is also the unit thePlanets works in, which is what lets
    # this membrane place that child correctly in its own frame.
    SIGMA_SB, T_ICE = 5.670374419e-8, 170.0
    r_snow_au = ((L / (16.0 * pi * SIGMA_SB * T_ICE ** 4)) ** 0.5) / AU
    return {
        # ITS REAL SIZE: where its disk stops holding together. Everything emits at radius ~1 locally, so this is
        # the only place the true scale is recorded -- and a human needs it to know what they see.
        "extent_m": DISK_EDGE_AU * AU,
        # ITS OWN DURATION -- and the TICK is not the MOVIE. The dynamical time here is 29 years
        # (an orbit out at the disk edge); that is how fast the system RINGS, not how long it takes
        # to BECOME. Formation runs for many dynamical times, and the number that bounds it is
        # measured: protoplanetary disks disperse in 3-10 Myr, so the gas is simply gone after that.
        "duration_s": 6.0e6 * 3.1557e7,
        "t_dyn_s": _clk.dynamical_time(M_total / ((4.0/3.0)*pi*(DISK_EDGE_AU*AU)**3)),
        "snow_line_au": r_snow_au,
        "disk_edge_au": DISK_EDGE_AU,
        "M_total": M_total,
        "M_star": M_star,
        "M_star_solar": M_star / M_SUN,
        "imf_percentile": p_imf,                           # where this system sits among all stars
        "M_fragment_solar": M_frag_solar,                  # the draw, before the disk is split off
        "m_char_solar": m_char,                            # carried: the galaxy's characteristic mass
        "M_disk": M_disk,
        "M_disk_solar": M_disk / M_SUN,
        "L": L,                                            # what lights everything outward
        # THE STAR'S SIZE AND COLOUR, CARRIED FOR ITS SIBLINGS -- and this is what a parent is FOR.
        # theStar and thePlanets are siblings: neither can read the other, and a membrane may only
        # read its parent. So if the SYSTEM does not carry the star's radius and surface temperature,
        # the planets cannot know the colour of their own sunlight -- and what they did instead was
        # TYPE 5772.0 as a literal under a comment claiming it was inherited. That is the same lie
        # as drawing a star-ball: an assertion wearing a derivation's clothes. Change the star's mass
        # and nothing downstream moved.
        #
        # Same empirical main-sequence scalings as the luminosity above, computed ONCE, here, because
        # this is the only membrane both children can see.
        "R_star": R_STAR_SUN * (M_star / M_SUN) ** 0.8,
        "T_star_surface": (L / (4.0 * pi * (R_STAR_SUN * (M_star / M_SUN) ** 0.8) ** 2
                                * 5.670374419e-8)) ** 0.25,
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

    # THE CENTRE IS NOT DRAWN HERE. It is theStar, and theStar is a CHILD of this membrane -- a
    # parent must not duplicate what its child provides, or the same matter exists twice. It also
    # broke the picture: 2500 grains packed into a 0.03 ball, plus the placed child, overran a
    # single 32px tile's MAX_PER_TILE, and the cap evicted the DISK's grains from that tile -- a
    # black, tile-shaped hole exactly where the star should be. This membrane emits the DISK; the
    # star arrives through layout().
    # While the system is still collapsing (t < 1) there IS no star yet, so the infalling matter is
    # all there is to draw -- which is why the swirl above starts spherical and only then flattens.
    return b


def layout(nums):
    """WHERE the things inside this membrane sit, in ITS frame (1.0 = the disk's outer edge).

    A parent is made of its children, so this says only WHERE each one goes and HOW BIG it is --
    structure, which is the parent's own physics. Their APPEARANCE is always their own.

    The star sits at the centre because it holds 99.9% of the mass, and its scale is its TRUE size
    against the disk: R_sun / 30 AU = 1.55e-4, which is sub-pixel. So it is drawn at a declared
    exaggeration, the same auditable lie as STAR_EXAGGERATION -- at this scale a star is a SOURCE,
    not a sphere, and until the renderer has point lights the alternative is not drawing it at all."""
    R_SUN, AU = 6.957e8, 1.495978707e11
    true_scale = R_SUN / (DISK_EDGE_AU * AU)          # 1.55e-4 -- invisible, and that is the truth
    STAR_EXAGGERATION = 260.0                          # declared, not hidden
    return {
        "theStar":    ((0.0, 0.0, 0.0), true_scale * STAR_EXAGGERATION),
        # thePlanets works in units of the SNOW LINE; this frame is units of the DISK EDGE.
        # Both are in AU, so the conversion is a ratio this membrane already knows.
        "thePlanets": ((0.0, 0.0, 0.0), nums["snow_line_au"] / nums["disk_edge_au"]),
    }


def measure(nums):
    """Facts, not preferences: the centre holds essentially all the mass, and what circles it obeys
    Kepler -- the exponent measured back out of grown orbits, never imposed."""
    return {"star_holds_the_mass": nums["M_star"] / nums["M_total"] > 0.99,
            "kepler_exponent": nums["kepler_exponent"],
            "earth_year_days": nums["T_at_1au_days"]}
