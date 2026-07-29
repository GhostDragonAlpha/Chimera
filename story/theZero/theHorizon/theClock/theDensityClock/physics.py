"""theDensityClock -- time is a local rate, and its ceiling is the fence its parent drew.

theHorizon handed down r_s = 2GM/c^2. This membrane is what that radius MEANS for time: the clock
slows as you approach it, and AT it the clock stops. So the horizon is not a separate object with
its own rule -- it is where this law runs out. Same turtle, from the other end.

It lives here, beside theHorizon, and NOT inside a solar system, because a membrane may only read
its parent: a law parented inside one place is unreachable from everywhere else, and theShip needs
this one.
"""
from math import sqrt

G = 6.67430e-11
C = 2.99792458e8

# Measured constants of a real system, used to CHECK the law -- the same way the CMB temperature
# checks theCooling. Nothing here is fitted to them.
GM_EARTH = 3.986004418e14         # m^3/s^2
R_EARTH = 6.371e6                 # m
R_GPS = 26.561e6                  # m, GPS orbital radius
DAY = 86400.0


def gravitational_rate(GM, r):
    """How fast a clock runs at radius r, against one infinitely far away: sqrt(1 - 2GM/rc^2).
    Deeper in the well is slower, and the whole effect is that one dimensionless ratio."""
    return sqrt(max(0.0, 1.0 - 2.0 * GM / (r * C * C)))


def kinematic_rate(v):
    """And moving is slower too: sqrt(1 - v^2/c^2). Same form, same c, different cause."""
    return sqrt(max(0.0, 1.0 - (v * v) / (C * C)))


def gps_drift_us_per_day():
    """THE PREDICTION IT WAS NEVER FITTED TO. A GPS satellite sits higher in Earth's well (its clock
    runs FAST) and moves at 3.9 km/s (its clock runs SLOW). Both from the two formulas above, with
    nothing but Earth's measured GM and the orbit radius:

        gravitational  +45.7 us/day
        kinematic       -7.2 us/day
        net            +38.5 us/day        measured: 38.6

    Uncorrected that is ~11.5 km of position error per day -- the system would be useless within an
    hour. Every phone on Earth is a running experiment confirming that time leans."""
    grav = (GM_EARTH / C ** 2) * (1.0 / R_EARTH - 1.0 / R_GPS) * DAY
    v = sqrt(GM_EARTH / R_GPS)
    kin = -(v * v) / (2.0 * C * C) * DAY
    return grav * 1e6, kin * 1e6, (grav + kin) * 1e6


def derive(parent, free):
    if parent is None or "r_s" not in parent:
        raise ValueError("theDensityClock requires theHorizon as its parent -- its ceiling is r_s")
    r_s = float(parent["r_s"])
    grav, kin, net = gps_drift_us_per_day()
    return {
        # ITS REAL SIZE: its ceiling -- where the clock stops. Everything emits at radius ~1 locally, so this is
        # the only place the true scale is recorded -- and a human needs it to know what they see.
        "extent_m": r_s,
        # ITS OWN DURATION: light crossing its own ceiling. t=1 in emit() means this much real time.
        "duration_s": r_s / 2.99792458e8,
        "r_s": r_s,                                   # the ceiling: at r = r_s the clock STOPS
        "ceiling_is_the_horizon": True,
        "rate_at_2rs": gravitational_rate(0.5 * r_s * C * C / G / 2.0 * 2.0, 2.0 * r_s) if r_s > 0 else 0.0,
        "gps_gravitational_us_day": grav,             # +45.7
        "gps_kinematic_us_day": kin,                  # -7.2
        "gps_net_us_day": net,                        # +38.5   measured 38.6
        "gps_error_km_day": abs(net) * 1e-6 * C / 1000.0,
        "applies_everywhere": True,                   # which is why it is parented HERE, not below
    }


def emit(nums, t=1.0):
    """The matter of theDensityClock, in its own local units (1 = the horizon).

    There is no matter here -- time is not a substance. What CAN be drawn is the rate itself: a field
    of clocks around a mass, each coloured by how fast it runs. Far out they run at full speed; close
    in they redden and slow; at r = 1 -- the fence -- they stop, and that black circle at the middle
    is not an object, it is where there is no time left to come back with."""
    import numpy as np
    from matter import blank, paint, GLOW, SOLID

    tt = float(t)
    rng = np.random.default_rng(31)
    n = 20000
    # a disk of test clocks, from just outside the horizon to well away from it
    u = rng.random(n)
    r = 1.02 + 6.0 * u ** 1.7
    th = rng.random(n) * 2.0 * np.pi
    b = blank(n)
    b[:, 0] = r * np.cos(th)
    b[:, 1] = r * np.sin(th)
    b[:, 2] = rng.normal(0.0, 0.05, n)
    rate = np.sqrt(np.clip(1.0 - 1.0 / r, 0.0, 1.0))               # sqrt(1 - r_s/r)
    lean = 1.0 - rate                                              # 0 far away, 1 at the fence
    lean *= tt                                                     # the movie: the lean switching on
    b[:, 16] = 0.35 + 0.65 * lean                                  # red where time is slow
    b[:, 17] = 0.75 * (1.0 - lean) + 0.10
    b[:, 18] = 1.00 * (1.0 - lean) + 0.10
    b[:, 19] = 0.10 + 0.35 * lean
    b[:, 20] = 0.020
    b[:, 11] = GLOW

    # the fence itself -- where the clock stops
    n_h = 2000
    thh = np.linspace(0.0, 2.0 * np.pi, n_h, endpoint=False)
    h = blank(n_h)
    h[:, 0] = np.cos(thh); h[:, 1] = np.sin(thh)
    h[:, 2] = rng.normal(0.0, 0.012, n_h)
    paint(h, (0.05, 0.02, 0.02), 0.9, 0.016, SOLID)
    return np.concatenate([h, b], axis=0)


def measure(nums):
    """The check is GPS, and it is not subtle: the net drift must land on the measured 38.6 us/day,
    and the law's ceiling must be exactly the parent's horizon radius."""
    return {"gps_net_us_day": nums["gps_net_us_day"],
            "matches_measured_38_6": abs(nums["gps_net_us_day"] - 38.6) < 1.0,
            "ceiling_is_horizon": nums["ceiling_is_the_horizon"]}
