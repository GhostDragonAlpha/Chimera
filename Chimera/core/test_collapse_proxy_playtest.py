"""Standalone smoke test for collapse_proxy.py's _indicted_by_playtest() (no pytest --
matches this repo's existing convention; sibling to test_collapse_proxy_rejection.py,
which covers the SimPlaytest-sourced _indicted_by_simtest()). Uses a fabricated
in-memory node list only -- never touches the real DNA graph. Run directly:

    python core/test_collapse_proxy_playtest.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.collapse_proxy import _indicted_by_playtest

FAKE_NODES = [
    {
        "type": "PlaytestObservation",
        "id": "playtest_fake_001",
        "notes": "economy grinds too slowly near the trading post",
        "observer": "human",
    },
    # Directly-named rejection attributed to playtest_fake_001 (the normal branch-B
    # flow: graphify_record observe --derived-from playtest_fake_001 --quote "...").
    {
        "type": "Observation",
        "id": "observation_fake_a",
        "feature_name": "System_Economy",
        "verdict": "rejected",
        "derived_from": "playtest_fake_001",
        "quote": "economy grinds too slowly near the trading post",
        "tacit": False,
    },
    # Accepted-tacit attribution to the SAME playtest -- must NOT be indicted.
    {
        "type": "Observation",
        "id": "observation_fake_b",
        "feature_name": "Docking_Sequence",
        "verdict": "accepted",
        "derived_from": "playtest_fake_001",
        "quote": "",
        "tacit": True,
    },
    # A rejection attributed to a DIFFERENT playtest -- must not leak into
    # playtest_fake_001's indictment.
    {
        "type": "Observation",
        "id": "observation_fake_c",
        "feature_name": "Mission_Board",
        "verdict": "rejected",
        "derived_from": "playtest_fake_002",
        "quote": "mission board never refreshes",
        "tacit": False,
    },
    # A SimPlaytest-derived rejection -- must not leak in either (different node type
    # entirely, mirrors _indicted_by_simtest's own "SimPlaytest only" filter in reverse).
    {
        "type": "Observation",
        "id": "observation_fake_d",
        "feature_name": "Verb_Step",
        "verdict": "rejected",
        "derived_from": "simtest_fake_001",
        "quote": "dist=2000uu",
        "tacit": False,
    },
]


def test_only_rejected_observations_derived_from_playtest_indicted():
    indicted = _indicted_by_playtest(FAKE_NODES, "playtest_fake_001")
    assert "System_Economy" in indicted, "a rejected Observation derived_from this playtest must indict its feature"
    assert "economy grinds too slowly" in indicted["System_Economy"][0]


def test_accepted_observations_not_indicted():
    indicted = _indicted_by_playtest(FAKE_NODES, "playtest_fake_001")
    assert "Docking_Sequence" not in indicted, "an accepted-tacit observation must not indict its feature"


def test_scoped_to_named_playtest_only():
    indicted = _indicted_by_playtest(FAKE_NODES, "playtest_fake_001")
    assert "Mission_Board" not in indicted, "a different playtest's rejections must not leak in"
    assert "Verb_Step" not in indicted, "a simtest-derived rejection must not leak into a playtest sweep"


def test_unknown_playtest_indicts_nothing():
    indicted = _indicted_by_playtest(FAKE_NODES, "playtest_does_not_exist")
    assert indicted == {}


if __name__ == "__main__":
    tests = [test_only_rejected_observations_derived_from_playtest_indicted,
             test_accepted_observations_not_indicted,
             test_scoped_to_named_playtest_only,
             test_unknown_playtest_indicts_nothing]
    failed = 0
    for test in tests:
        try:
            test()
            print(f"PASS  {test.__name__}")
        except Exception as exc:
            failed += 1
            print(f"FAIL  {test.__name__}: {exc}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
