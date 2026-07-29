"""theGalaxy -- the clumps fall into each other and build an island of stars.

The parent handed down bound clouds of ~6e5 suns that cannot stop falling. They do not become solar
systems on their own: they merge into a galaxy first, and a system forms inside one of its arms.
This is the level HIERARCHIES.md says belongs here, and it was skipped once.

Everything below follows from one fact the parent already established -- angular momentum survives a
collapse -- plus one it could not: gas can radiate its heat away, and stars cannot.
"""
from math import pi, sqrt

G = 6.67430e-11
M_SUN = 1.98892e30
KPC = 3.0856775814913673e19       # metres
KM = 1.0e3

N_CLOUDS = 1.7e5                  # how many parent-sized clouds merge -- the free number (see derive)
V_FLAT = 220.0 * KM               # measured flat rotation speed of a disk galaxy, m/s
R_DISK_KPC = 15.0                 # where the stellar disk fades out
BULGE_FRAC = 0.20                 # mass that stayed round because stars cannot radiate away spin
R_SUN_KPC = 8.2                   # where a system like ours sits, kpc from centre


def orbital_period(r_kpc, v=V_FLAT):
    """A flat rotation curve means the period grows LINEARLY with radius, T = 2 pi r / v -- unlike a
    solar system, where it grows as r^1.5. That difference is the rotation-curve fact."""
    return 2.0 * pi * (r_kpc * KPC) / v


def enclosed_mass(r_kpc, v=V_FLAT):
    """From the curve itself: v^2 = GM/r  ->  M = v^2 r / G. Because v does not fall with r, the
    enclosed mass keeps RISING with radius -- which is the measurement, not an assumption."""
    return v * v * (r_kpc * KPC) / G


def winding_turns(r_kpc, dr_kpc=5.0, v=V_FLAT, age_yr=1.0e10):
    """THE WINDING PROBLEM, as a number. If the arms were material, the inner edge would lap the
    outer one and wrap them shut. Returns how many extra turns the inner radius makes in a galaxy's
    lifetime -- if it is much more than one, the arms cannot be solid objects."""
    t = age_yr * 3.1557e7
    return t * (1.0 / orbital_period(r_kpc, v) - 1.0 / orbital_period(r_kpc + dr_kpc, v))


import clock as _clk


FREE = {
    # How many parent-sized clouds merged. Drag it and the galaxy's mass moves, which moves the
    # rotation curve, the dark ratio, and everything the system below inherits.
    "n_clouds": {"label": "clouds merged", "default": 1.7e5,
                 "lo": 1.0e4, "hi": 1.0e6, "unit": "", "log": True,
                 # DECLARED LOCAL, with the reason, so the audit stops reporting it as a break.
                 # A silent non-propagation is indistinguishable from a bug; a written claim is
                 # reviewable. This one says: how many clouds merged sets how much GALAXY there is
                 # -- its rotation curve, its dark ratio -- and has no bearing on how cold a core
                 # can get, which is what fixes a star's mass. If that is wrong, argue with this
                 # line rather than with the tool.
                 "local": "sets the galaxy's mass, not its star-forming conditions"},
    # HOW ENRICHED THIS GALAXY'S GAS IS -- and this is the dial that reaches all the way down to a
    # star's mass. It is genuinely free: it depends on how many generations have already lived and
    # died here, which is a fact about this galaxy's HISTORY, not about its physics. Nothing in the
    # tree above can tell you it.
    #
    # (Honest note: `n_clouds` deliberately does NOT move the stellar mass. It sets how much galaxy
    # there is -- the rotation curve, the dark ratio -- not how cold a core can get. Manufacturing a
    # link would have been a nicer audit report and a worse model.)
    "metallicity_zsun": {"label": "enrichment", "default": 1.0,
                         "lo": 1.0e-5, "hi": 3.0, "unit": "x solar", "log": True},
}



# ── WHERE FRAGMENTATION STOPS, AND THEREFORE WHAT A STAR WEIGHS ─────────────────────────────────
# The parent handed down clouds of 6e5 suns. Nothing has yet explained why the things that form
# inside them weigh ONE sun rather than a hundred thousand. This is that step, and it is the edge
# that used to be missing: without it the system's mass was a free-floating dial and NOTHING about
# the galaxy reached the solar system at all.
K_B = 1.380649e-23
M_H = 1.6726219e-27
MU_MOL = 2.33                # H2 plus helium, by number -- a cold molecular cloud

T_PRIMORDIAL_K = 200.0       # metal-free gas can only cool through H2, and it is bad at it
T_COOLED_K = 10.0            # with dust and CO in the mix a core reaches ~10 K and stops
Z_CRIT = 1.0e-3              # critical metallicity for fragmentation (Bromm & Loeb 2003), in Z_sun


def core_temperature(z_zsun):
    """HOW COLD A CORE CAN GET, and therefore how heavy a star is.

    Cooling is what lets a collapsing fragment stay cold, and cooling needs COOLANTS. Metal-free gas
    has only molecular hydrogen, which is a poor radiator, so the first clouds sat near 200 K. Once
    a few generations have made carbon, oxygen and dust, CO and grain emission take over and a core
    settles at ~10 K.

    THE PREDICTION NOBODY FITTED: M_J goes as T^1.5, so metal-free gas fragments at ~90x the mass.
    That is why the FIRST STARS WERE HUNDREDS OF SOLAR MASSES -- a fact this law was not built from
    and returns anyway."""
    return T_COOLED_K + (T_PRIMORDIAL_K - T_COOLED_K) / (1.0 + z_zsun / Z_CRIT)
N_CORE_CM3 = 1.0e5           # the density a core reaches before it goes opaque
CORE_EFFICIENCY = 0.33       # MEASURED: a core loses ~2/3 of itself to outflow; the star gets a third
M_OPACITY_FLOOR = 0.010      # solar masses -- Low & Lynden-Bell 1976, Rees 1976
M_IMF_MAX = 150.0            # above this radiation pressure unbinds the envelope faster than it falls
IMF_SLOPE_HIGH = -2.3        # Salpeter/Kroupa, above the characteristic mass
IMF_SLOPE_MID = -1.3         # below it
IMF_SLOPE_LOW = -0.3         # below the degeneracy limit: the brown-dwarf tail flattens
M_BROWN = 0.08               # where the mid and low segments meet


def jeans_mass(T, n_cm3, mu=MU_MOL):
    """THE SAME LAW THE PARENT USED, at a different place on the ladder.

        M_J = (5kT / G mu m_H)^{3/2} * (3 / 4 pi rho)^{1/2}

    The point is what it does under collapse. While the gas can still radiate away the heat of its
    own compression it stays COLD, so T is fixed and M_J falls as rho^-1/2: every hundredfold gain
    in density cuts the fragment tenfold. A cloud therefore does not collapse -- it SHATTERS, again
    and again, and the pieces get smaller all the way down."""
    rho = n_cm3 * 1e6 * mu * M_H
    return (5.0 * K_B * T / (G * mu * M_H)) ** 1.5 * (3.0 / (4.0 * pi * rho)) ** 0.5


def imf_grid(m_lo, m_hi, m_char, n=2400):
    """The initial mass function as a number-weighted CDF on a log grid.

    Three segments, and the breaks are physical rather than fitted: the slope steepens above the
    characteristic mass (which is the core Jeans mass), and flattens again below the degeneracy limit
    where the objects are no longer stars. Kroupa 2001's exponents."""
    xs, ws = [], []
    for i in range(n):
        m = m_lo * (m_hi / m_lo) ** (i / (n - 1.0))
        if m >= m_char:
            w = (m / m_char) ** IMF_SLOPE_HIGH
        elif m >= M_BROWN:
            w = (m / m_char) ** IMF_SLOPE_MID
        else:
            w = (M_BROWN / m_char) ** IMF_SLOPE_MID * (m / M_BROWN) ** IMF_SLOPE_LOW
        xs.append(m)
        ws.append(w * m)                     # dN/dlogM = M dN/dM, because the grid is logarithmic
    tot, run, cdf = sum(ws), 0.0, []
    for w in ws:
        run += w
        cdf.append(run / tot)
    return xs, cdf


def mass_at_percentile(p, m_lo, m_hi, m_char):
    """WHICH FRAGMENT this story follows -- a position in a distribution the galaxy derived, not a
    number somebody chose. p is number-weighted: p=0.5 is the median STAR."""
    xs, cdf = imf_grid(m_lo, m_hi, m_char)
    p = min(max(float(p), 1e-6), 1.0 - 1e-9)
    for x, c in zip(xs, cdf):
        if c >= p:
            return x
    return xs[-1]


def percentile_of_mass(m, m_lo, m_hi, m_char):
    xs, cdf = imf_grid(m_lo, m_hi, m_char)
    for x, c in zip(xs, cdf):
        if x >= m:
            return c
    return 1.0


def derive(parent, free):
    if parent is None or not parent.get("collapsing"):
        raise ValueError("theGalaxy requires a parent cloud that is collapsing")
    m_cloud = float(parent["M_jeans"])
    n = float(free.get("n_clouds", N_CLOUDS))          # how many merged -- the human's dial
    M_stars = n * m_cloud
    M_dyn = enclosed_mass(R_DISK_KPC)                  # what the rotation curve says is really there

    # THE CASCADE, run once. From the parent's own conditions down to a cold core, the SAME Jeans
    # law walks eight orders of magnitude -- 1.2e8 suns at recombination to under one at core
    # density -- and it stops there because the fragment goes opaque and can no longer stay cold.
    # That is the whole answer to why a star weighs about a sun.
    z = float(free.get("metallicity_zsun", 1.0))
    t_core = core_temperature(z)
    m_j_core = jeans_mass(t_core, N_CORE_CM3) / M_SUN
    m_char = m_j_core * CORE_EFFICIENCY
    return {
        # ITS REAL SIZE: where the stellar disk fades out. Everything emits at radius ~1 locally, so this is
        # the only place the true scale is recorded -- and a human needs it to know what they see.
        "extent_m": R_DISK_KPC * KPC,
        # ITS OWN DURATION: its own free-fall. t=1 in emit() means this much real time.
        "duration_s": _clk.dynamical_time(M_dyn / ((4.0/3.0)*pi*(R_DISK_KPC*KPC)**3)),
        "M_cloud_solar": m_cloud / M_SUN,
        "n_clouds": n,
        "M_stars_solar": M_stars / M_SUN,              # ~1e11 suns: a disk galaxy
        "M_dynamical_solar": M_dyn / M_SUN,            # what the ROTATION demands
        "dark_ratio": M_dyn / M_stars,                 # >1, and measured -- the curve does not fall
        "v_flat_kms": V_FLAT / KM,
        "R_disk_kpc": R_DISK_KPC,
        "bulge_frac": BULGE_FRAC,
        "r_system_kpc": R_SUN_KPC,
        "T_orbit_myr": orbital_period(R_SUN_KPC) / 3.1557e7 / 1e6,   # ~230 Myr: one galactic year
        "winding_turns": winding_turns(R_SUN_KPC),     # >> 1, so arms CANNOT be material
        "arms_are_waves": winding_turns(R_SUN_KPC) > 3.0,
        # THE EDGE TO THE SYSTEM BELOW -- what was missing entirely. A solar system is ONE FRAGMENT
        # of one of this galaxy's clouds, and its mass is not a free number: it is a draw from the
        # distribution these conditions produce. Change the core temperature or density and every
        # system in this galaxy changes mass with it.
        "metallicity_zsun": z,
        "T_core_K": t_core,
        "n_core_cm3": N_CORE_CM3,
        "M_jeans_core_solar": m_j_core,               # ~1.7 suns: where the shattering stops
        "core_efficiency": CORE_EFFICIENCY,
        "m_char_solar": m_char,                       # the IMF's characteristic mass
        "m_floor_solar": M_OPACITY_FLOOR,             # the opacity limit: the smallest fragment possible
        "m_max_solar": M_IMF_MAX,
        "imf_slope_high": IMF_SLOPE_HIGH,
        "sun_percentile": percentile_of_mass(1.0, M_OPACITY_FLOOR, M_IMF_MAX, m_char),
        "collapsing": True,
        "hydrogen_frac": parent["hydrogen_frac"],
        "helium_frac": parent["helium_frac"],
    }


def emit(nums, t=1.0):
    """The matter of theGalaxy, in its own local units (1 = the disk's edge).

    The movie is the same collapse the parent started, carried one level up -- and it separates as it
    goes. GAS can radiate its heat away, so it settles into a thin disk; STARS cannot radiate anything
    away, so the ones that formed early keep the round shape they collapsed with. A galaxy ends as
    both at once: a bulge that remembers and a disk that settled.

    The arms are drawn as a DENSITY WAVE, not as objects -- a slow pattern the stars drift through --
    because the winding number in numbers.json says material arms would have wrapped shut long ago.
    They are brighter because gas is compressed there and compressed gas makes stars."""
    import numpy as np
    from matter import blank, paint, lit, blackbody_rgb, SOLID, GLOW

    tt = float(t)
    rng = np.random.default_rng(71)
    ARMS, PITCH = 2, 0.22                     # a two-armed logarithmic spiral, tan(pitch) ~ 12 deg

    # ── the disk: young stars and gas, concentrated into the arms ──
    n = 26000
    u = rng.random(n)
    r = 0.06 + 0.94 * u ** 0.62                                  # more stars inward
    th = rng.random(n) * 2.0 * pi
    # pull each star toward the nearest arm -- a COMPRESSION, not a hard placement
    arm_phase = np.log(np.clip(r, 1e-3, None)) / PITCH
    k = np.round((th - arm_phase) * ARMS / (2 * pi))
    th_arm = arm_phase + k * 2 * pi / ARMS
    pull = 0.55 * tt                                             # the wave grows as the disk settles
    th = th * (1 - pull) + th_arm * pull + rng.normal(0, 0.10, n)
    z = rng.normal(0.0, 0.030 * (1.0 - 0.75 * tt), n)            # gas radiates -> the disk THINS
    d = blank(n)
    d[:, 0] = r * np.cos(th); d[:, 1] = r * np.sin(th); d[:, 2] = z
    # colour: young hot stars where the gas is compressed, cooler ones between the arms
    dens = np.exp(-((((th - th_arm + pi) % (2 * pi)) - pi) * 2.0) ** 2)
    T = 3600.0 + 6500.0 * dens * tt
    d[:, 16:19] = np.array([blackbody_rgb(x) for x in np.round(T, -2)], dtype=np.float32)
    d[:, 19] = 0.10 + 0.28 * dens
    d[:, 20] = 0.0075
    d[:, 11] = SOLID

    # ── the bulge: old stars, which cannot radiate away their spin, so they stay round ──
    n_b = int(9000 * float(nums.get("bulge_frac", 0.2)) / 0.2)
    v = rng.normal(0.0, 1.0, (n_b, 3))
    v /= np.linalg.norm(v, axis=1, keepdims=True) + 1e-12
    rb = 0.22 * rng.random(n_b) ** 0.45
    b = blank(n_b)
    b[:, 0:3] = v * rb[:, None] * (1.0 + 0.6 * (1.0 - tt))       # it was wider before it settled
    paint(b, blackbody_rgb(4200.0), 0.16, 0.060, GLOW)  # x6: GLOW no longer carries a hidden multiplier (gpu_pipeline._profile)
    return np.concatenate([b, d], axis=0)


def layout(nums):
    """WHERE the things inside sit. A system forms in an arm, ~8 kpc out -- so it is placed at that
    radius, and at true scale it is FAR beyond sub-pixel: 30 AU against a 15 kpc disk is 3e-10.
    It is drawn at a declared exaggeration; the alternative is not drawing it at all."""
    r = float(nums["r_system_kpc"]) / float(nums["R_disk_kpc"])
    import math
    th = math.log(max(r, 1e-3)) / 0.22                            # on an arm, by the same spiral
    SYSTEM_EXAGGERATION = 0.05                                    # declared: true scale is 3e-10
    return {"theSolarSystem": ((r * math.cos(th), r * math.sin(th), 0.0), SYSTEM_EXAGGERATION)}


def measure(nums):
    """Facts, not preferences: the arms cannot be material (the winding number settles it), and the
    rotation curve demands more mass than the stars provide."""
    return {"arms_must_be_waves": nums["arms_are_waves"],
            "winding_turns": nums["winding_turns"],
            "galactic_year_myr": nums["T_orbit_myr"],
            "dark_ratio": nums["dark_ratio"]}
