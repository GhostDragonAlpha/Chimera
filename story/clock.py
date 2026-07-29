"""clock.py -- every membrane's own duration, so `t = 0 -> 1` means a REAL elapsed time.

A membrane's movie runs t = 0 (its beginning) to t = 1 (its settled end). Until now `t` was
dimensionless, so theCooling's 380,000 years and theGalaxy's ten billion played in the same
arbitrary unit -- the fourth dimension was unlabelled and eleven membranes were eleven separate
clips. A `duration_s` makes them one nested performance.

THE LAW IS theClock's: a self-gravitating thing falls through itself in t ~ 1/sqrt(G rho). Only the
density appears, which is why one expression serves a cloud, a star and a galaxy.

TRUE RATES ARE NOT WATCHABLE -- the ladder spans 60 orders of magnitude -- so the viewer plays every
membrane over the same wall-clock span and LABELS what that span represents. What IS played at true
relative rates is the NESTING: a child whose duration is shorter than its parent's finishes early
inside the parent's movie, because that is what actually happens.
"""
from __future__ import annotations

from math import pi, sqrt

G = 6.67430e-11
C = 2.99792458e8

MINUTE = 60.0
HOUR = 3600.0
DAY = 86400.0
YEAR = 3.1557e7
MYR = YEAR * 1e6
GYR = YEAR * 1e9


def dynamical_time(rho: float) -> float:
    """theClock's law: t_ff = sqrt(3 pi / 32 G rho). Only the density appears."""
    return sqrt(3.0 * pi / (32.0 * G * max(rho, 1e-40)))


def dynamical_of(M: float, R: float) -> float:
    """The same, for a body given as a mass and a radius."""
    return dynamical_time(M / ((4.0 / 3.0) * pi * max(R, 1e-30) ** 3))


def light_crossing(r: float) -> float:
    """How long news takes to cross it -- the clock of anything held together by light, not gravity."""
    return r / C


def child_phase(parent_t: float, parent_duration_s: float, child_duration_s: float) -> float:
    """WHERE A CHILD IS, PART-WAY THROUGH ITS PARENT'S MOVIE.

    A child that takes less time than its parent is FINISHED long before the parent settles -- stars
    light while a galaxy is still assembling. So the child's own t runs faster by exactly the ratio
    of their durations, and clamps once it is done. This is the only place true relative rates are
    used, and it is the place they matter."""
    if child_duration_s <= 0.0 or parent_duration_s <= 0.0:
        return parent_t
    return max(0.0, min(1.0, parent_t * (parent_duration_s / child_duration_s)))


def human(seconds: float) -> str:
    """A duration, said the way a person would say it."""
    s = abs(float(seconds))
    if s == 0.0:
        return "instant"
    for unit, name in ((GYR, "Gyr"), (MYR, "Myr"), (YEAR, "yr"), (DAY, "days"),
                       (HOUR, "h"), (MINUTE, "min"), (1.0, "s")):
        if s >= unit:
            v = s / unit
            return f"{v:.3g} {name}"
    return f"{s:.3g} s"
