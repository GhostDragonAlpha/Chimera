"""Standalone smoke test for collapse_proxy.py's _indicted_by_simtest() (no pytest --
matches this repo's existing convention). Uses a fabricated in-memory node list only --
never touches the real DNA graph. Run directly:

    python core/test_collapse_proxy_rejection.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.collapse_proxy import _indicted_by_simtest

FAKE_NODES = [
    {
        "type": "SimPlaytest",
        "id": "simtest_fake_001",
        "outcomes": [
            {"beat": "spawn_on_metal_pad", "outcome": "reached",
             "features": ["Player_Character_Model"], "evidence": [{"ok": True, "note": "fine"}]},
            {"beat": "walk_metal_to_rock", "outcome": "failed",
             "features": ["Verb_Step", "Ground_Rock_Surface"],
             "evidence": [{"ok": False, "note": "dist=2000uu (loc x=0, y=0)"}]},
        ],
    },
    {
        # A different simtest naming a different feature -- must NOT be indicted when
        # querying simtest_fake_001.
        "type": "SimPlaytest",
        "id": "simtest_fake_002",
        "outcomes": [
            {"beat": "other_beat", "outcome": "blocked",
             "features": ["System_Economy"], "evidence": [{"ok": False, "note": "unrelated"}]},
        ],
    },
]


def test_only_non_reached_outcomes_indicted():
    indicted = _indicted_by_simtest(FAKE_NODES, "simtest_fake_001")
    assert "Player_Character_Model" not in indicted, "a 'reached' outcome must not indict its features"
    assert "Verb_Step" in indicted and "Ground_Rock_Surface" in indicted
    assert "dist=2000uu" in indicted["Verb_Step"][0]


def test_scoped_to_named_simtest_only():
    indicted = _indicted_by_simtest(FAKE_NODES, "simtest_fake_001")
    assert "System_Economy" not in indicted, "a different simtest's failures must not leak in"


def test_unknown_simtest_indicts_nothing():
    indicted = _indicted_by_simtest(FAKE_NODES, "simtest_does_not_exist")
    assert indicted == {}


if __name__ == "__main__":
    tests = [test_only_non_reached_outcomes_indicted, test_scoped_to_named_simtest_only,
             test_unknown_simtest_indicts_nothing]
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
