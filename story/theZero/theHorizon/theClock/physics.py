"""theClock -- the law of duration. Every membrane below derives its own tick from this.

theHorizon produced the first tick, t_P. This is what a tick IS at every scale above it, and there
is only one formula: a self-gravitating thing falls through itself in t ~ 1/sqrt(G rho). Only the
DENSITY appears -- not the size, not the mass -- which is why one expression gives a planet's orbit,
a cloud's collapse and a star's pulsation.

The game is a state machine and a state machine must know WHAT CHANGES WHEN. These are the rates.
"""
from math import pi, sqrt

G = 6.67430e-11
C = 2.99792458e8
YEAR = 3.1557e7
M_SUN = 1.98892e30
R_SUN = 6.957e8


def dynamical_time(rho):
    """THE clock. The time a self-gravitating thing takes to fall through itself.

        t_ff = sqrt(3 pi / (32 G rho))

    Substitute M = rho (4/3) pi a^3 into the orbital period T = 2 pi sqrt(a^3/GM) and every length
    CANCELS, leaving sqrt(3 pi / G rho). A satellite skimming any body's surface orbits in a time set
    by that body's density alone -- pebble or star, the same number."""
    return sqrt(3.0 * pi / (32.0 * G * max(rho, 1e-30)))


def orbital_period(a, M):
    """Kepler, for when you have a mass and a radius rather than a density."""
    return 2.0 * pi * sqrt(a ** 3 / (G * M))


def light_crossing(r):
    """How long news takes to cross the thing. Sets whether it can act as ONE thing at all."""
    return r / C


def burn_time(energy, power):
    """Stored energy over the rate it is spent -- a star's life, a battery's, a fire's."""
    return energy / max(power, 1e-30)


def density(M, R):
    return M / ((4.0 / 3.0) * pi * R ** 3)


def clock_of(M, R):
    """The full set of clocks for a body of mass M and radius R -- what a membrane calls to get its
    own tick. Returns seconds."""
    rho = density(M, R)
    return {
        "rho": rho,
        "t_dyn_s": dynamical_time(rho),
        "t_light_s": light_crossing(R),
        "coherent": dynamical_time(rho) > light_crossing(R),   # can it settle before news escapes?
    }


def derive(parent, free):
    if parent is None or "t_P" not in parent:
        raise ValueError("theClock requires theHorizon as its parent -- it made the first tick")
    t_P = float(parent["t_P"])
    # THE SAME FORMULA, at the densities this story has already derived. Nothing here is looked up.
    sun = clock_of(M_SUN, R_SUN)
    earth = clock_of(5.9722e24, 6.371e6)
    galaxy_rho = (1.045e11 * M_SUN) / ((4.0 / 3.0) * pi * (15.0 * 3.0857e19) ** 3)
    cloud_rho = 1.103e-18                                       # theCloud's own number, kg/m^3
    return {
        # ITS REAL SIZE: its ceiling. Everything emits at radius ~1 locally, so this is
        # the only place the true scale is recorded -- and a human needs it to know what they see.
        "extent_m": float(parent["r_s"]),
        # ITS OWN DURATION: the law itself is instantaneous; it is the tick. t=1 in emit() means this much real time.
        "duration_s": t_P,
        # PASSED THROUGH, because a child may only read its parent: theDensityClock lives inside
        # this membrane now and its ceiling is still the horizon's radius.
        "r_s": float(parent["r_s"]),
        "l_P": float(parent["l_P"]),
        "t_planck_s": t_P,                                      # the smallest tick there is
        "t_dyn_sun_s": sun["t_dyn_s"],                          # ~1 hour
        "t_dyn_earth_s": earth["t_dyn_s"],                      # ~1 hour too -- similar density!
        "t_dyn_galaxy_myr": dynamical_time(galaxy_rho) / YEAR / 1e6,
        "t_dyn_cloud_myr": dynamical_time(cloud_rho) / YEAR / 1e6,
        "t_light_sun_s": sun["t_light_s"],
        "sun_coherent": sun["coherent"],
        "orders_of_magnitude": 60.0,                            # Planck tick to a star's burn
        "law": "t_dyn ~ 1/sqrt(G rho) -- only the density appears",
    }


def emit(nums, t=1.0):
    """The matter of theClock, in its own local units.

    There is nothing here to draw but RATE, so the movie draws rates: nested rings, each turning at
    the speed its own density gives it. The inner ones are dense and whip round; the outer ones are
    thin and barely move. Same law on every ring -- only rho changes -- which is the whole point."""
    import numpy as np
    from matter import blank, paint, GLOW

    tt = float(t)
    rng = np.random.default_rng(41)
    rings, per = 7, 2600
    parts = []
    for i in range(rings):
        r = 0.16 + 0.84 * (i / (rings - 1)) ** 0.9
        # denser inward -> faster: phase advances as 1/sqrt(rho) with rho ~ r^-3, so as r^-1.5
        omega = (0.16 / r) ** 1.5
        th = rng.random(per) * 2.0 * pi + omega * tt * 9.0
        b = blank(per)
        b[:, 0] = r * np.cos(th)
        b[:, 1] = r * np.sin(th)
        b[:, 2] = rng.normal(0.0, 0.010, per)
        heat = min(1.0, omega / 6.0)                            # fast rings run hot
        paint(b, (0.35 + 0.65 * heat, 0.55 + 0.25 * (1 - heat), 1.0 - 0.55 * heat),
              0.16 + 0.30 * heat, 0.012, GLOW)
        parts.append(b)
    return np.concatenate(parts, axis=0)


def measure(nums):
    """The check that it is ONE law and not three: the Sun and the Earth have similar densities, so
    despite a 100x difference in size their dynamical clocks must agree to within a factor of a few.
    And the Sun must be coherent -- it settles faster than light crosses it, which is why it is a
    thing at all."""
    ratio = nums["t_dyn_sun_s"] / nums["t_dyn_earth_s"]
    return {"sun_earth_clock_ratio": ratio,
            "one_law_not_three": 0.2 < ratio < 5.0,
            "sun_is_coherent": nums["sun_coherent"],
            "galactic_dynamical_myr": nums["t_dyn_galaxy_myr"]}
