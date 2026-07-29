"""scale.py -- every membrane's real SIZE, so a human can tell what they are looking at.

clock.py answers "how long"; this answers "how big". Both are needed for the same reason: every
membrane emits at radius ~1 in its OWN units, so on screen a galaxy and a star are the same size.
Without a label you cannot tell 15 kiloparsecs from 700,000 kilometres, and a person will misread
what the thing IS.

TWO HANDLES, and the second is the honest one at large scales:

  * a HUMAN COMPARISON -- said in the biggest unit a person actually holds (a person, a city, an
    Earth, an AU, a light-year).
  * LIGHT-CROSSING TIME -- how long light takes to get across it. At these sizes distance stops
    being a length you can picture and becomes a WAIT, which is the same thing a ship's thruster
    experiences. A galaxy is not "big", it is "a hundred thousand years wide".

Once both are labelled, gameplay becomes computable: a thruster's acceleration, a real distance and
a real duration give a real travel time, in numbers the player can feel.
"""
from __future__ import annotations

C = 2.99792458e8
YEAR = 3.1557e7

HUMAN_M = 1.7                      # a person, the unit everything else is felt against
EARTH_R = 6.371e6
SUN_R = 6.957e8
AU = 1.495978707e11
LY = C * YEAR
PC = 3.0856775814913673e16
KPC = PC * 1e3


def human_length(m: float) -> str:
    """A size, said the way a person would say it."""
    x = abs(float(m))
    if x == 0.0:
        return "a point"
    for unit, name in ((KPC, "kpc"), (PC, "pc"), (LY, "light-years"), (AU, "AU"),
                       (SUN_R, "solar radii"), (EARTH_R, "Earth radii"),
                       (1e3, "km"), (1.0, "m")):
        if x >= unit:
            return f"{x / unit:.3g} {name}"
    if x >= 1e-3:
        return f"{x * 1e3:.3g} mm"
    if x >= 1e-9:
        return f"{x * 1e9:.3g} nm"
    return f"{x:.3g} m"


def against_a_person(m: float) -> str:
    """The same size, in people. The only unit nobody has to imagine."""
    n = abs(float(m)) / HUMAN_M
    if n == 0.0:
        return "no size at all"
    if n < 1.0:
        return f"{1.0 / n:.3g}x smaller than a person"
    if n < 1e4:
        return f"{n:.3g} people tall"
    return f"{n:.3g} people, end to end"


def light_time(m: float) -> float:
    """A distance, as the wait it really is."""
    return abs(float(m)) / C


def crossing(m: float) -> str:
    """How long light takes to get across it -- the honest handle above planetary scale."""
    import clock as _clk
    return _clk.human(light_time(m))


def travel_time(distance_m: float, accel_ms2: float) -> float:
    """WHY THE SIZES MATTER FOR PLAY. A ship that accelerates for half the distance and decelerates
    for the other half arrives in t = 2*sqrt(d/a). Real size plus real thrust equals a real wait --
    which is the number a player actually feels."""
    a = max(abs(float(accel_ms2)), 1e-9)
    return 2.0 * (abs(float(distance_m)) / a) ** 0.5
