"""Standalone assert-script for core/backlog_burn.py (matches this repo's non-pytest
convention, e.g. test_wind_system_integration.py). Run: python core/test_backlog_burn.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.backlog_burn import _dedupe_pains, _classify_next_item, NEXT_ITEM_RE


def test_dedupe_pains_groups_references_to_root():
    open_pains = [
        {"id": "phase_aaa111:P1", "text": "Distiller token-coverage will false-suppress genuinely new lessons.", "age_days": 5},
        {"id": "phase_bbb222:P1", "text": "phase_aaa111:P1", "age_days": 3},
        {"id": "phase_ccc333:P1", "text": "phase_aaa111:P1 distiller token-coverage suppression", "age_days": 1},
        {"id": "phase_ddd444:P1", "text": "Tri-pad materials read uniformly dark at walk height.", "age_days": 2},
    ]
    groups = _dedupe_pains(open_pains)
    assert len(groups) == 2, f"expected 2 distinct root issues, got {len(groups)}: {groups}"
    by_root = {g["root_id"]: g for g in groups}
    assert "phase_aaa111:P1" in by_root
    assert by_root["phase_aaa111:P1"]["reaffirm_count"] == 3
    assert by_root["phase_aaa111:P1"]["max_age_days"] == 5
    assert "Distiller token-coverage" in by_root["phase_aaa111:P1"]["text"]
    assert "phase_ddd444:P1" in by_root
    assert by_root["phase_ddd444:P1"]["reaffirm_count"] == 1
    print("PASS: test_dedupe_pains_groups_references_to_root")


def test_dedupe_pains_handles_empty():
    assert _dedupe_pains([]) == []
    print("PASS: test_dedupe_pains_handles_empty")


def test_dedupe_pains_no_infinite_loop_on_self_reference():
    # Defensive: a pain whose text happens to reference its own id must not recurse forever.
    open_pains = [{"id": "phase_xxx:P1", "text": "phase_xxx:P1 (self-referential, malformed)", "age_days": 0}]
    groups = _dedupe_pains(open_pains)
    assert len(groups) == 1
    print("PASS: test_dedupe_pains_no_infinite_loop_on_self_reference")


def test_classify_next_item_catches_known_bug_language():
    text = ("Drop-then-repickup is not wired -- ADropActor doesn't inherit APickupActor, "
            "so a dropped item can never be picked back up under the current design.")
    hits = _classify_next_item(text)
    assert hits, "expected at least one bug-signal keyword to match"
    assert any("wired" in h or "inherit" in h or "never" in h for h in hits), hits
    print(f"PASS: test_classify_next_item_catches_known_bug_language ({hits})")


def test_classify_next_item_ignores_process_language():
    text = ("Get explicit human authorization to close the shared UnrealEditor.exe, "
            "then run a real cold build.")
    hits = _classify_next_item(text)
    assert hits == [], f"expected no bug-signal match on a process/authorization item, got {hits}"
    print("PASS: test_classify_next_item_ignores_process_language")


def test_classify_next_item_catches_shovel_gap():
    # Real task_progress.md phrasing wraps code identifiers in markdown backticks --
    # the regex must span "no `Dig()` method", not just the unformatted "no Dig() method".
    text = ("`ATool_Shovel` has `DigRadius`/`DigDepth` properties that are never read "
            "anywhere and no `Dig()` method -- confirmed still true tonight.")
    hits = _classify_next_item(text)
    assert hits, "expected the 'no `Dig()` method' pattern to match"
    assert any("function|method" in h for h in hits), (
        f"matched for the wrong reason -- expected the no-method pattern specifically, got {hits}")
    print(f"PASS: test_classify_next_item_catches_shovel_gap ({hits})")


def test_next_item_regex_splits_numbered_list():
    block = (
        "1. **First item** spans one line.\n"
        "2. **Second item** spans\n"
        "   multiple lines of prose\n"
        "   before the next number.\n"
        "3. Third and final item.\n"
        "\n---\n\n# Next session\n"
    )
    items = [" ".join(m.group(1).split()) for m in NEXT_ITEM_RE.finditer(block)]
    assert len(items) == 3, f"expected 3 items, got {len(items)}: {items}"
    assert items[0].startswith("**First item**")
    assert "multiple lines of prose" in items[1]
    assert items[2] == "Third and final item."
    print("PASS: test_next_item_regex_splits_numbered_list")


if __name__ == "__main__":
    test_dedupe_pains_groups_references_to_root()
    test_dedupe_pains_handles_empty()
    test_dedupe_pains_no_infinite_loop_on_self_reference()
    test_classify_next_item_catches_known_bug_language()
    test_classify_next_item_ignores_process_language()
    test_classify_next_item_catches_shovel_gap()
    test_next_item_regex_splits_numbered_list()
    print("\nAll backlog_burn tests passed.")
