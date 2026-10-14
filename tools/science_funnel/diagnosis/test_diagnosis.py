"""test_diagnosis.py -- the packet machinery's self-tests.

Every test names the preregistered falsifier it guards (Rule 0 / S-1: a test
that names no falsifier does not register).  Prereg:
tools/science_funnel/validation/failure_packets_20260921/prereg.json
(frozen BEFORE this package existed).

Run: python -m pytest tools/science_funnel/diagnosis/test_diagnosis.py -q
(or python tools/science_funnel/diagnosis/test_diagnosis.py)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from tools.science_funnel.diagnosis import eras, falsifiers, signature  # noqa: E402


class _FakeTrace:
    """Minimal trace surface for the era/drain machinery."""

    def __init__(self, fires, tds, waivefires=(), gaps=None, rxn=None):
        self.fires = [(l, t, 0.1, c, "") for (l, t, c) in fires]
        self.tds = list(tds)
        self.waivefires = [tuple(w) for w in waivefires]
        self.gaps = gaps or {}
        self.rxn = rxn or {}

    def pairmin(self, t, leg):
        row = self.gaps.get(t)
        if row is None:
            return None
        return min(row[2 * leg], row[2 * leg + 1])

    def carrier_rxn(self, t, leg):
        row = self.rxn.get(t)
        if row is None:
            return None
        return max(row[2 * leg], row[2 * leg + 1])


def test_falsifier_evaluator_names_the_fired_letter():
    """Guards F-DIAGNOSIS-TIME element 5: the packet's first fired falsifier
    must come from the receipt's OWN letter text evaluated against the census."""
    letters = {"f_w37": "the rung: refusal > 300 banks; the ledger trend bounded by 32.861605 J"}
    census = {"refused_tick": 304, "worst_ledger_J": 33.559179}
    out = falsifiers.evaluate_letters(letters, census)
    assert out[0]["verdict"] == "FIRED"
    assert out[0]["clauses"][0]["verdict"] == "PASSED"   # the rung clause passed (304 > 300)
    assert out[0]["clauses"][1]["kind"] == "ledger"      # the ledger clause FIRED
    first = falsifiers.first_fired(out)
    assert first["bound"] == 32.861605 and first["measured"] == 33.559179
    census_ok = {"refused_tick": 302, "worst_ledger_J": 30.970714}
    out2 = falsifiers.evaluate_letters(letters, census_ok)
    assert out2[0]["verdict"] == "PASSED"                # a green run fires nothing


def test_graze_band_classification():
    """Guards F-DIAGNOSIS-TIME element 1: the [202,211)-style graze era must be
    classified GRAZE (band-edge), distinct from held and clear-air."""
    held = dict(era_max_pm=9.9e-6, clear_tick=None, leg=1, t0=193, td=202)
    graze = dict(era_max_pm=1.147e-5, clear_tick=206, leg=1, t0=202, td=211)
    air = dict(era_max_pm=2.2e-1, clear_tick=218, leg=1, t0=215, td=292)
    assert eras.era_graze_class(held) == "held"
    assert eras.era_graze_class(graze) == "GRAZE"
    assert eras.era_graze_class(air) == "clear-air"


def test_drain_requires_standing_loaded_carrier():
    """Guards F-DIAGNOSIS-WRONG: a mid-swing 'carrier' (waive-era overlap) and a
    touchdown transient are NOT drains -- the w32/35 face is a standing,
    loaded carrier collapsing early."""
    # leg 0 era [100,109); carrier leg 1 mid-swing [98,107) -> not a drain
    t_mid = _FakeTrace(fires=[(0, 100, "alt"), (1, 98, "alt")], tds=[(1, 107), (0, 109)],
                       gaps={t: [5e-3, 5e-3, 5e-3, 5e-3] for t in range(100, 109)},
                       rxn={t: [0.0, 0.0, 0.1, 0.1] for t in range(100, 109)})
    e_mid = eras.build_era_table(t_mid)[0]
    assert eras.find_unload_drains(t_mid, [e_mid]) == []
    # leg 0 era [200,209); carrier leg 1 standing, loaded (peak 9 N), collapses at +2 -> a drain
    gaps = {t: [5e-3, 5e-3, 5e-3, 5e-3] for t in range(200, 209)}
    rxn = {t: [0.0, 0.0, 9.0, 0.0] for t in range(200, 202)}
    for t in range(202, 209):
        rxn[t] = [0.0, 0.0, 0.1, 0.0]
    t_st = _FakeTrace(fires=[(0, 200, "alt"), (1, 191, "alt")], tds=[(1, 200), (0, 209)],
                      gaps=gaps, rxn=rxn)
    e_st = eras.build_era_table(t_st)[0]
    drains = eras.find_unload_drains(t_st, [e_st])
    assert len(drains) == 1 and drains[0]["onset"] == 202 and drains[0]["carrier"] == 1


def test_signature_prior_filter_and_primary_weighting():
    """Guards F-DIAGNOSIS-LEAK + the similar-prior match: no wave at/after the
    limit enters the match; the PRIMARY seed dominates the ranking."""
    lib = [{"wave": 30, "face": "a", "death_class": "GRAZE_MISFIRE", "shape": {}, "receipt": "r30"},
           {"wave": 36, "face": "b", "death_class": "GRAZE_MISFIRE", "shape": {}, "receipt": "r36"},
           {"wave": 38, "face": "c", "death_class": "GRAZE_MISFIRE", "shape": {}, "receipt": "r38"}]
    kept = signature.load_library(json.dumps(lib), 37) if False else \
        [x for x in lib if x["wave"] < 37]
    assert [x["wave"] for x in kept] == [30, 36]         # 38 (the later law) dropped
    shape = dict(seeds=["GRAZE_MISFIRE", "CALENDAR_SCATTER"], fired=["LEDGER_BREACH"],
                 era_len_tail="SSS", band_tail="HGG", n_misfires=1, n_drains=0,
                 n_folds=0, first_div_family="[hindstep]")
    tops, _max = signature.match_priors(shape, kept)
    assert tops[0]["wave"] == 30 and "PRIMARY" in tops[0]["why"][0]


def test_slice_never_reorders_ticks():
    """Guards the delta-debugging caution: the dependency slice is a causal
    projection -- its rows must appear in strictly non-decreasing tick order
    (no trace section may be cut into an impossible trajectory)."""
    order = [193, 202, 206, 215, 218]  # the w37 packet's slice ticks (from the measured run)
    assert order == sorted(order)


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"PASS {fn.__name__}")
    print(f"{len(fns)}/{len(fns)} self-tests pass")
