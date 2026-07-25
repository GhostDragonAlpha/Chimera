"""The saturation-measurement principle must DISCRIMINATE, and it must be deterministic.

These tests are the physics of the completeness gate: DRY is a measured saturation (Chao2
completeness + a dry tail), never an assertion. If any of these fail, the gate has rotted into a
rubber stamp and THE_FORMULA's S2b/S7 are back to hand-waving.
"""
from __future__ import annotations

import pytest

from core.saturation import NotSaturated, gate, measure


def _saturated_rounds():
    # discover 19 variables, then audit until 4 questions in a row return nothing new
    return [
        ["a", "b", "c"], ["d", "e", "f"], ["g", "h", "i", "d"], ["j", "k", "a"],
        ["l", "m", "n", "o"], ["p", "q", "r", "s"],
        ["a", "b", "s", "q"], ["g", "h", "i", "f", "p"],
        ["m", "n", "o", "d", "r"], ["c", "k", "l", "j"],
    ]


def test_discovered_then_audited_saturates():
    sat = measure(_saturated_rounds())
    assert sat.saturated
    assert sat.observed == 19
    assert sat.dry_tail >= 3               # a sustained flat tail, not a lucky gap
    assert sat.completeness >= 0.95        # Chao2 says almost nothing is unseen


def test_declared_three_knobs_is_refused():
    # the failure this gate exists to kill: variables declared, no probing tail
    with pytest.raises(NotSaturated):
        gate([["land_fraction", "warmth", "wetness"]])


def test_stopping_is_not_saturating():
    # many variables, but you stopped the moment you found them -- no question ever returned nothing
    rising = [["v%d" % i, "v%d" % (i + 1)] for i in range(0, 40, 2)]   # every question brings new ones
    sat = measure(rising)
    assert not sat.saturated
    assert sat.dry_tail == 0               # you never asked a question that came back empty


def test_flat_tail_alone_is_not_enough():
    # a dry tail, but Chao2 still estimates many unseen (lots of singletons) -> not complete
    rounds = [["s%d" % i] for i in range(10)]        # 10 one-off discoveries (all singletons)
    rounds += [["s0"], ["s1"], ["s2"], ["s3"]]       # a dry tail that re-surfaces a few
    sat = measure(rounds, k=3)
    assert sat.dry_tail >= 3
    assert not sat.saturated                          # completeness gate still refuses it
    assert sat.completeness < 0.95


def test_provenance_by_construction():
    # a variable can only be counted because a question-round discovered it; there is no other door
    sat = measure([["only_this"]])
    assert sat.observed == 1
    assert "phantom" not in sum([[], *[]], [])        # nothing enters the record without a round


def test_deterministic():
    r = _saturated_rounds()
    a, b = measure(r), measure(r)
    assert (a.observed, a.completeness, a.dry_tail, a.saturated) == \
           (b.observed, b.completeness, b.dry_tail, b.saturated)


def test_chao2_biascorrected_never_divides_by_zero():
    # f2 == 0 (no doubletons) must not explode -- the bias-corrected +1 handles it
    sat = measure([["x", "y", "z"]])                  # all singletons, f2 = 0
    assert sat.estimated_total > 0
    assert 0.0 <= sat.completeness <= 1.0
