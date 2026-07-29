"""theStar -- the fall is stopped by fire, and only above a mass that the physics fixes.

The parent handed down a collapsing cloud. It fragments as it falls, and each fragment contracts and
heats -- but degeneracy grows faster than heat, so every ball has a MAXIMUM temperature it will ever
reach. Whether that maximum clears hydrogen's ignition is a statement about mass alone, and the
threshold is not chosen here: it is solved.
"""
from math import pi

G = 6.67430e-11
KB = 1.380649e-23
HBAR = 1.054571817e-34
M_E = 9.1093837015e-31
M_H = 1.6735575e-27
SIGMA_SB = 5.670374419e-8
M_SUN = 1.98892e30
R_SUN = 6.957e8
L_SUN = 3.828e26

ALPHA = 0.5        # the ONE order-unity constant: virial T_c ~ ALPHA*G*M*mu*m_H/(k*R).
                   # Checked against the Sun: it returns T_c ~ 7e6 K where the real centre is
                   # 1.5e7 K -- right to a factor of 2, which is what "order unity" means and is
                   # stated rather than tuned away.
MU = 0.6           # mean molecular weight, ionized primordial gas
MU_E = 1.14        # electrons per nucleon^-1 for X = 0.75
T_IGNITE = 4.0e6   # pp-chain hydrogen burning becomes self-sustaining (standard value, NOT fitted)


def virial_temperature(M, R):
    """A self-gravitating ball converts its fall into heat: T ~ M/R."""
    return ALPHA * G * M * MU * M_H / (KB * R)


def fermi_temperature(M, R):
    """Electrons cannot share a state, so squeezing them costs energy whether or not they are hot.
    E_F ~ n_e^{2/3} ~ R^-2 -- it grows FASTER than the virial T ~ R^-1, so it always catches up."""
    n_e = 3.0 * M / (4.0 * pi * R ** 3 * MU_E * M_H)
    return (HBAR ** 2 / (2.0 * M_E * KB)) * (3.0 * pi ** 2 * n_e) ** (2.0 / 3.0)


def max_temperature(M):
    """The hottest a contracting ball of mass M will EVER get.

    Contraction raises both curves, but degeneracy rises faster, so they cross once -- and at that
    crossing the ball stops needing heat to hold itself up, so it stops getting hotter. Setting
    virial = Fermi and eliminating R gives T_max ~ M^{4/3}, closed form, no integration."""
    A = ALPHA * G * MU * M_H / KB                                    # T = A*M/R
    D = (HBAR ** 2 / (2.0 * M_E * KB)) * (9.0 * pi * M / (4.0 * MU_E * M_H)) ** (2.0 / 3.0)
    return (A * M) ** 2 / D                                          # T_max = (A M)^2 / D


def minimum_stellar_mass(t_ignite=T_IGNITE):
    """The least mass whose maximum temperature still clears ignition -- solved, not looked up."""
    lo, hi = 1e26, 1e30
    for _ in range(120):
        mid = 0.5 * (lo + hi)
        if max_temperature(mid) < t_ignite:
            lo = mid                                                 # too cold -> needs more mass
        else:
            hi = mid
    return 0.5 * (lo + hi)


def derive(parent, free):
    if parent is None or not parent.get("flattened"):
        raise ValueError("theStar requires a parent SYSTEM (the star is a sibling of the planets)")
    M_min = minimum_stellar_mass()
    M = float(parent["M_star"])                   # the system decides the split; the star inherits it
    # HONEST LABEL: these are EMPIRICAL main-sequence scalings (L ~ M^3.5, R ~ M^0.8) normalised on
    # the Sun, not derived here. So at 1 M_sun the surface temperature returning 5772 K is
    # definitional, not a prediction; the scalings predict only for OTHER masses. The derived,
    # predictive result of this membrane is M_min.
    L = L_SUN * (M / M_SUN) ** 3.5
    R = R_SUN * (M / M_SUN) ** 0.8
    T_surface = (L / (4.0 * pi * R ** 2 * SIGMA_SB)) ** 0.25         # what balance forces it to glow at
    return {
        # ITS OWN DURATION: contraction to ignition: ~30 Myr. t=1 in emit() means this much real time.
        "duration_s": 3.0e7 * 3.1557e7,
        "M_min_kg": M_min,
        "M_min_solar": M_min / M_SUN,             # ~0.07: below this, degeneracy wins and no fire
        "T_max_at_min": max_temperature(M_min),
        "T_ignite": T_IGNITE,
        "M_star_solar": M / M_SUN,
        # NOT the core temperature. It is the ceiling this ball would reach if NOTHING stopped it --
        # for anything above M_min, fusion arrests the contraction long before, which is why it
        # returns 1.4e8 K for the Sun whose real core is 1.5e7 K. The ceiling is what decides
        # whether fire lights at all; it is not what the burning star settles at.
        "T_max_if_never_ignited": max_temperature(M),
        "T_surface": T_surface,
        "L": L,
        "R": R,
        "burning": max_temperature(M) > T_IGNITE,
        "held_up_by": "fusion" if max_temperature(M) > T_IGNITE else "degeneracy",
        "leftover_disk": True,                    # angular momentum: what missed cannot vanish
    }


def emit(nums, t=1.0):
    """The matter of theStar, in its own local units.

    The movie is the fall being stopped. At t=0 the fragment is extended, cool and dim; as its own
    time runs it contracts, and the colour is the surface temperature the law computed -- so the
    star is not painted yellow, it is yellow because 5772 K is yellow. What did not fall in is left
    circling, because angular momentum has nowhere else to go."""
    import numpy as np
    from matter import blank, fibonacci_sphere, paint, blackbody_rgb, SOLID, GLOW

    tt = float(t)
    rng = np.random.default_rng(6)
    T_s = float(nums.get("T_surface", 5772.0))
    rgb = blackbody_rgb(T_s)

    # the contracting body: an extended cloud that becomes a sharp-edged star
    n = 11000
    d = fibonacci_sphere(n)
    spread = 1.0 - 0.88 * tt ** 2                              # it contracts HARD: a star is tiny beside its disk
    rad = spread * (0.25 + 0.75 * rng.random(n) ** 0.4)
    body = blank(n)
    body[:, 0:3] = d * rad[:, None]
    body[:, 21:24] = d * tt                                    # a surface appears only once it has one
    paint(body, rgb, 0.10 + 0.90 * tt ** 2, 0.030 - 0.008 * tt, SOLID if tt > 0.8 else GLOW)

    # the leftover: angular momentum flattens what missed into a disk that stays
    n_d = 9000
    th = rng.random(n_d) * 2.0 * pi
    rr = 0.30 + 1.00 * rng.random(n_d) ** 0.7
    disk = blank(n_d)
    disk[:, 0] = rr * np.cos(th)
    disk[:, 1] = rr * np.sin(th)
    disk[:, 2] = rng.normal(0.0, 0.16 * (1.0 - 0.82 * tt), n_d)    # it FLATTENS as it settles
    # SOLID, not GLOW. A soft-blob grain carries a 6x size multiplier, and 9000 of them over a ring
    # accumulate into a filled ball -- the render claiming matter where there is only orbit. Discrete
    # dust grains say the true thing: a disk is mostly EMPTY, which is why you can see the star in it.
    paint(disk, (0.72, 0.54, 0.36), 0.75, 0.012, SOLID)
    return np.concatenate([body, disk], axis=0)


def layout(nums):
    """WHAT IS CONTAINED HERE. theStar is the LAW -- what a star is, and the least mass that can be
    one. aYellowStar is the star that actually formed in this system -- named by the class its
    own temperature puts it in (G, yellow), so the name states a derived fact, so it sits at the centre of this
    membrane's frame at full size: at this scale the membrane IS the star."""
    return {"aYellowStar": ((0.0, 0.0, 0.0), 1.0)}


def measure(nums):
    """What training must check -- facts, not preferences: the minimum stellar mass lands at the
    measured brown-dwarf limit, and this star is actually held up by fire rather than crowding."""
    return {"min_mass_is_brown_dwarf_limit": 0.05 < nums["M_min_solar"] < 0.10,
            "held_up_by_fusion": nums["burning"]}
