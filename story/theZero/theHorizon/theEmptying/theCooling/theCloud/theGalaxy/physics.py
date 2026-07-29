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
                 "lo": 1.0e4, "hi": 1.0e6, "unit": "", "log": True},
}


def derive(parent, free):
    if parent is None or not parent.get("collapsing"):
        raise ValueError("theGalaxy requires a parent cloud that is collapsing")
    m_cloud = float(parent["M_jeans"])
    n = float(free.get("n_clouds", N_CLOUDS))          # how many merged -- the human's dial
    M_stars = n * m_cloud
    M_dyn = enclosed_mass(R_DISK_KPC)                  # what the rotation curve says is really there
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
    paint(b, blackbody_rgb(4200.0), 0.16, 0.010, GLOW)
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
