"""THE TWO SEARCHES (operator datum 7, 2026-08-08, THE HUMAN terminal,
recorded verbatim in docs/THE_CATEGORIES.md):

    "Everything has a beginning and an end.  We need two methods:
    1 that searches for these beginnings and these endings, and the
    other that searches everything in between the beginning and the
    end."

Method 1 -- find_bounds: the BEGINNING of an event is the first index
the signal crosses its bar; the END is the last index it is still
across.  An event that never returns runs to the trace's end -- that
is itself data (the fall that does not recover).  A trace that never
crosses has no event: the honest answer is None, not index 0.

Method 2 -- read_interval: given the beginning and the end, read
everything between them: the count, the endpoints, the mean, the
slope, the sign consistency, and the extrema -- with indices handed
back in ABSOLUTE trace coordinates, so an interior event lands back
on the timeline where it was found.

The discipline this replaces: probes hard-coding their windows
(ticks 100-800) instead of finding them.  The window is a
measurement, not a choice -- RULE 1 applies to time too: derive the
bounds, don't pick them.
"""

from __future__ import annotations

from typing import Any

import numpy as np


def find_bounds(trace: Any, bar: float, *, side: str = "above"
                ) -> tuple[int, int] | None:
    """Method 1: the beginning and the end of the bar-crossing event.

    trace : the signal, one value per tick.
    bar   : the crossing level.
    side  : "above" -- the event is trace >= bar;
            "below" -- the event is trace <= bar.

    Returns (begin, end), absolute indices: the first and the last
    crossing.  None when the signal never crosses -- no beginning,
    no event.
    """
    x = np.asarray(trace, dtype=np.float64)
    if x.size == 0:
        return None
    over = x >= bar if side == "above" else x <= bar
    idx = np.flatnonzero(over)
    if idx.size == 0:
        return None
    return int(idx[0]), int(idx[-1])


def read_interval(trace: Any, begin: int, end: int) -> dict[str, Any]:
    """Method 2: read everything between the beginning and the end.

    Both indices are inclusive, absolute trace coordinates (the pair
    find_bounds returns).  The extrema indices come back absolute as
    well, so the interval's interior events stay on the timeline.
    """
    x = np.asarray(trace, dtype=np.float64)[begin:end + 1]
    n = int(x.size)
    if n == 0:
        raise ValueError("empty interval: begin/end outside the trace")
    slope = float(np.polyfit(np.arange(n, dtype=np.float64), x, 1)[0]) \
        if n > 1 else 0.0
    mean = float(x.mean())
    i_min = int(x.argmin())
    i_max = int(x.argmax())
    first = float(x[0])
    last = float(x[-1])
    return {
        "begin": int(begin),
        "end": int(end),
        "count": n,
        "first": first,
        "last": last,
        "mean": mean,
        "slope": slope,
        "min": float(x[i_min]),
        "argmin": int(begin) + i_min,
        "max": float(x[i_max]),
        "argmax": int(begin) + i_max,
        "sign_consistency": float((np.sign(x) == np.sign(mean)).mean())
        if mean != 0.0 else 1.0,
        "growth": last / first if first != 0.0 else float("inf"),
    }


def search_event(trace: Any, bar: float, *, side: str = "above"
                 ) -> dict[str, Any] | None:
    """The two methods composed: find the event's bounds, then read
    the interval.  None when the event never begins."""
    bounds = find_bounds(trace, bar, side=side)
    if bounds is None:
        return None
    return read_interval(trace, bounds[0], bounds[1])
