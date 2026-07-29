"""theSpace -- empty of matter, full of gravity. That pairing is the whole character of flight here.

The parent handed down a system with a central mass and a luminosity. This membrane is what lies
BETWEEN the things in it: too thin to push back on anything (so you coast), yet completely filled by
a force with infinite range (so you always fall), and wide enough that distance is honestly a
duration.
"""
from math import pi, sqrt

G = 6.67430e-11
C = 2.99792458e8
AU = 1.495978707e11
M_PROTON = 1.67262192e-27

N_PROTONS_CM3 = 5.0          # measured density of the interplanetary medium near 1 AU
AIR_DENSITY = 1.225          # kg/m^3 at sea level, for the comparison that makes it mean something


def escape_speed(M, r):
    """What it costs to leave. Gravity has no edge, so 'leaving' is always a climb, never an exit."""
    return sqrt(2.0 * G * M / r)


def orbit_speed(M, r):
    """The fall that never lands."""
    return sqrt(G * M / r)


def light_time(r):
    """Distance, measured honestly: nothing crosses it faster than this."""
    return r / C


import clock as _clk


def derive(parent, free):
    if parent is None or not parent.get("flattened"):
        raise ValueError("theSpace requires a parent SYSTEM")
    M = float(parent["M_star"])
    rho = N_PROTONS_CM3 * 1e6 * M_PROTON                     # protons/cm^3 -> kg/m^3
    return {
        # ITS REAL SIZE: the system it fills. Everything emits at radius ~1 locally, so this is
        # the only place the true scale is recorded -- and a human needs it to know what they see.
        "extent_m": 30.0 * AU,
        # ITS OWN DURATION: light across the system it fills. t=1 in emit() means this much real time.
        "duration_s": _clk.light_crossing(30.0 * AU),
        "rho": rho,
        "thinner_than_air": AIR_DENSITY / rho,               # ~1e20: why nothing pushes back
        "coasts": True,                                      # no drag -> Newton's first law, visible
        "gravity_range": "infinite",                         # 1/r^2 never reaches zero: no shielding
        "v_orbit_1au": orbit_speed(M, AU),
        "v_escape_1au": escape_speed(M, AU),
        "light_time_1au_s": light_time(AU),                  # 499 s: the Sun is always 8 min old
        "light_time_30au_s": light_time(30.0 * AU),
        "sky_is_dark": True,                                 # the universe has an age; light has not arrived
        "M_star": M,
    }


def emit(nums, t=1.0):
    """The matter of theSpace, in its own local units (1 = 1 AU).

    THE HONEST PICTURE IS ALMOST ENTIRELY BLACK, and that is the content: at true density there is
    essentially nothing here. What IS here is the pull, so the movie shows the one thing space
    actually transmits -- a field that never reaches zero, brightening inward with 1/r^2 and having
    no edge anywhere. The few grains are drawn at their real sparseness, not decorated."""
    import numpy as np
    from matter import blank, paint, lit, GLOW, SOLID

    tt = float(t)
    rng = np.random.default_rng(71)

    # THE PULL: a shell field, brightness = the gravitational potential it would take to climb out.
    n_f = 16000
    d = rng.normal(0.0, 1.0, (n_f, 3))
    d /= (np.linalg.norm(d, axis=1, keepdims=True) + 1e-9)
    r = 0.10 + 3.0 * rng.random(n_f) ** 1.6
    f = blank(n_f)
    f[:, 0:3] = d * r[:, None]
    pull = 1.0 / np.clip(r, 0.10, None) ** 2                  # 1/r^2 -- falls off, never to zero
    f[:, 16:19] = lit(np.array([0.30, 0.45, 0.85], np.float32), pull * tt + 1e-6, e_ref=1.0)
    f[:, 19] = 0.020 * tt
    f[:, 20] = 0.030
    f[:, 11] = GLOW

    # THE MATTER: five protons per cubic centimetre. Drawn sparse because it IS sparse.
    n_m = 400
    dm = rng.normal(0.0, 1.0, (n_m, 3))
    dm /= (np.linalg.norm(dm, axis=1, keepdims=True) + 1e-9)
    m = blank(n_m)
    m[:, 0:3] = dm * (0.2 + 3.0 * rng.random(n_m))
    paint(m, (0.55, 0.58, 0.65), 0.35, 0.007, SOLID)
    return np.concatenate([f, m], axis=0)


def measure(nums):
    """Facts: it is too thin to slow anything, and the pull it carries has no edge."""
    return {"thinner_than_air_by": nums["thinner_than_air"],
            "light_minutes_to_1au": nums["light_time_1au_s"] / 60.0,
            "coasts": nums["coasts"]}
