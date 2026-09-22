"""divergence.py -- the earliest relevant divergence vs a reference run.

Compares the failed run's first-walk trace families against a reference run's,
per tick, in the trace's own causal order.  READ-ONLY alignment: nothing is cut
or reordered -- a difference is reported where the physics produces it.
"""
from __future__ import annotations

from .trace_io import Trace

_RELEVANT = ("[hindstep]", "[dvp]", "[dvq]", "[dvj]", "[ledger10]", "[dv]", "[ledger]", "[refusal]")


def earliest_divergence(fail: Trace, ref: Trace) -> dict:
    """First tick whose relevant-family content differs, plus the first
    calendar ([hindstep]) and energy ([ledger10]) difference ticks."""
    ticks = sorted(set(fail.events_by_tick) & set(ref.events_by_tick))
    first_any = first_calendar = first_energy = None
    first_family = None
    for t in ticks:
        f_fam = {}
        r_fam = {}
        for fam, line in fail.events_by_tick[t]:
            f_fam.setdefault(fam, []).append(line)
        for fam, line in ref.events_by_tick[t]:
            r_fam.setdefault(fam, []).append(line)
        for fam in _RELEVANT:
            if f_fam.get(fam) != r_fam.get(fam):
                if first_any is None:
                    first_any, first_family = t, fam
                if fam == "[hindstep]" and first_calendar is None:
                    first_calendar = t
                if fam == "[ledger10]" and first_energy is None:
                    first_energy = t
        if first_calendar is not None and first_energy is not None and first_any is not None:
            break
    # the tail ticks only one side reached (a shorter/longer walk is itself divergence)
    if first_any is None:
        only_fail = (set(fail.events_by_tick) - set(ref.events_by_tick))
        only_ref = (set(ref.events_by_tick) - set(fail.events_by_tick))
        if only_fail:
            first_any, first_family = min(only_fail), "(tail: failed run only)"
        elif only_ref:
            first_any, first_family = min(only_ref), "(tail: reference only)"
    return dict(first_tick=first_any, first_family=first_family,
                first_calendar_tick=first_calendar, first_energy_tick=first_energy,
                reference_sha256=ref.sha256, reference_path=ref.path)
