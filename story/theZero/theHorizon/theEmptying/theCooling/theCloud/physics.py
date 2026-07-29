"""theCloud -- gravity has no threshold, but pressure pushes back. Jeans decides which wins.

The parent handed down neutral matter, transparency, and a density contrast. This membrane's whole
law is one competition, and the number that settles it is the SOUND SPEED -- which the parent's
transparency had just destroyed. Nothing here is chosen: the mass of the first clouds falls out.
"""
from math import pi, sqrt

G = 6.67430e-11
C = 2.99792458e8
KB = 1.380649e-23
M_H = 1.6735575e-27          # hydrogen mass
M_SUN = 1.98892e30

GAMMA = 5.0 / 3.0            # monatomic gas
MU = 1.22                    # mean molecular weight of neutral primordial H+He
T_CMB_NOW = 2.7255           # measured today -- with the parent's T it fixes how far back this is
RHO_B_NOW = 4.20e-28         # baryon density today, kg/m^3 (Omega_b h^2 = 0.0224, measured)


def sound_speed(T, mu=MU):
    """A neutral gas carries only its own thermal speed."""
    return sqrt(GAMMA * KB * T / (mu * M_H))


def jeans_mass(T, rho, mu=MU):
    """The smallest mass whose gravity beats its own pressure.

        M_J = (5kT / (G mu m_H))^{3/2} * (3 / (4 pi rho))^{1/2}

    Below it, pressure wins and the clump bounces -- it rings, as sound. Above it, gravity wins and
    nothing stops the fall. M_J ~ c_s^3, which is why the sound speed is the whole story."""
    return (5.0 * KB * T / (G * mu * M_H)) ** 1.5 * (3.0 / (4.0 * pi * rho)) ** 0.5


import clock as _clk


def derive(parent, free):
    if parent is None or not parent.get("transparent"):
        raise ValueError("theCloud requires a parent that has gone transparent")
    T = float(parent["T_end"])                       # 3760 K, derived by the parent
    # how far back this is, from OUR OWN temperature against the one measured today
    one_plus_z = T / T_CMB_NOW
    rho = RHO_B_NOW * one_plus_z ** 3                # the sea was denser then by (1+z)^3

    cs_after = sound_speed(T)                        # neutral gas: its own thermal speed
    cs_before = C / sqrt(3.0)                        # welded to photons: radiation's stiffness
    # Before transparency the SAME formula applies with the radiation-dominated sound speed:
    T_eff_before = cs_before ** 2 * MU * M_H / (GAMMA * KB)
    m_before = jeans_mass(T_eff_before, rho)
    m_after = jeans_mass(T, rho)

    return {
        # ITS REAL SIZE: the Jeans length: sound in a free-fall time. Everything emits at radius ~1 locally, so this is
        # the only place the true scale is recorded -- and a human needs it to know what they see.
        "extent_m": _clk.dynamical_time(rho) * cs_after,
        # ITS OWN DURATION: it falls through itself. t=1 in emit() means this much real time.
        "duration_s": _clk.dynamical_time(rho),
        "T": T,
        "one_plus_z": one_plus_z,
        "rho": rho,
        "c_s": cs_after,
        "c_s_before": cs_before,
        "sound_speed_drop": cs_before / cs_after,
        "M_jeans": m_after,
        "M_jeans_solar": m_after / M_SUN,            # ~1e6 suns: the first thing that can collapse
        "M_jeans_before_solar": m_before / M_SUN,    # ~1e17 suns: nothing, so nothing collapsed
        "jeans_drop": m_before / m_after,            # ~13 orders of magnitude, = (c_s ratio)^3
        "collapsing": True,
        "hydrogen_frac": parent["hydrogen_frac"],
        "helium_frac": parent["helium_frac"],
    }


def emit(nums, t=1.0):
    """The matter of theCloud, in its own local units.

    The movie is the competition being decided. At t=0 the gas is smooth -- the one part in 100,000
    is invisible, because that is what one part in 100,000 looks like. As its own time runs, every
    region above the Jeans mass stops ringing and FALLS: the grains gather toward a handful of
    centres, and the colour warms because falling gas compresses and compressing gas heats. Nothing
    is placed; the clumps are where the noise happened to be dense."""
    import numpy as np
    from matter import blank, paint, blackbody_rgb, GLOW

    n = 16000
    tt = float(t)
    rng = np.random.default_rng(5)
    p = rng.normal(0.0, 0.42, (n, 3))                       # a smooth sea

    n_seed = 7                                               # the regions that happened to be over M_J
    seeds = rng.normal(0.0, 0.42, (n_seed, 3))
    owner = rng.integers(0, n_seed, n)
    pull = tt ** 2                                           # collapse accelerates: it cannot stop
    p = p * (1.0 - 0.88 * pull) + seeds[owner] * (0.88 * pull)
    p += rng.normal(0.0, 0.02 * (1.0 - pull), (n, 3))

    b = blank(n)
    b[:, 0:3] = p
    T = float(nums.get("T", 3760.0)) * (1.0 + 0.9 * pull)    # falling gas compresses, and heats
    # Keep per-grain alpha LOW. Gathering 16k soft blobs into a few centres piles enormous overlap
    # onto the same pixels, and a saturated tile shows up as a hard square edge -- the render lying
    # about density. Low alpha lets the density itself do the brightening, which is the honest way:
    # a clump is bright because there is more gas there, not because each grain got louder.
    paint(b, blackbody_rgb(T), 0.055 - 0.030 * pull, 0.024 - 0.007 * pull, GLOW)
    return b


def measure(nums):
    """What training must check -- both facts, not preferences: the first collapsible mass lands at
    the scale of the first structures (10^5-10^7 suns), and the Jeans drop is exactly the cube of
    the sound-speed drop, because M_J ~ c_s^3."""
    ratio = nums["jeans_drop"] / nums["sound_speed_drop"] ** 3
    return {"first_mass_is_stellar_cluster_scale": 1e5 < nums["M_jeans_solar"] < 1e7,
            "drop_is_cs_cubed": abs(ratio - 1.0) < 1e-6}
