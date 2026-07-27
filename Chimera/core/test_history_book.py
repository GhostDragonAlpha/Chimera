"""Tests for core.history_book — run: python core/test_history_book.py"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.history_book import (entries_from_graph, entries_from_claude_md,
                               entries_from_drift, reindex, search, render_md,
                               _fts_quote, Entry)

PASS = TOTAL = 0


def check(name, cond):
    global PASS, TOTAL
    TOTAL += 1
    print(("  ok  " if cond else "FAIL  ") + name)
    PASS += cond


def main():
    nodes = [
        {"id": "elim_1", "type": "Elimination", "feature": "audio",
         "boundary": "beat schema as root cause", "observed": "schema valid",
         "eliminates": ["h1"], "survives": ["h2: attachment"],
         "evidence_ref": "sim_x", "timestamp": "2026-07-12T01:00:00"},
        {"id": "surprise_1", "type": "SurpriseMoment", "context": "triage",
         "expectation": "noise", "reality": "84% true drift",
         "lesson_hint": "spec aspirational", "source": "agent",
         "timestamp": "2026-07-12T02:00:00"},
        {"id": "grade_1", "type": "ProfessorGrade", "feature": "Verb_Shovel",
         "grade": "B", "reasoning": "criteria mostly covered",
         "timestamp": "2026-07-11T00:00:00"},
        {"id": "phase_1", "type": "PhaseComplete", "phase": "rep engine",
         "result": "shipped", "inheritance": "trust the red atoms",
         "phantom_pains": ["DSL noise"], "timestamp": "2026-07-12T03:00:00"},
    ]
    entries = entries_from_graph(nodes)
    chapters = {e.chapter for e in entries}
    check("graph entries built across 4 chapters",
          chapters == {"closed-doors", "surprises", "verdicts", "wills"})
    elim = next(e for e in entries if e.chapter == "closed-doors")
    check("elimination carries SURVIVES (the narrowed search space)",
          "SURVIVES" in elim.body and "attachment" in elim.body)

    md_entries = entries_from_claude_md(
        "- **[H-2, auto-promoted]** Never verify from desktop screenshots\n"
        "- **[H-34, auto-promoted]** Verify components are spawned")
    check("constitution parsed from CLAUDE.md", len(md_entries) == 2
          and md_entries[0].title == "H-2")

    drift_entries = entries_from_drift({
        "coverage": "33/169 (19%)", "note": "n", "triage": "t",
        "drift_by_spec": {"a.chimera": 2},
        "entries": [{"token": "shield_strength_points", "spec_file": "a.chimera",
                     "verdict": "drift"},
                    {"token": "weapon_slots", "spec_file": "a.chimera",
                     "verdict": "implemented"}]})
    check("drift chapter: coverage header + drift-only entries",
          len(drift_entries) == 2 and "unkept promise" in drift_entries[1].title)

    tmp_db = Path(tempfile.mkdtemp()) / "history.db"
    all_entries = entries + md_entries + drift_entries
    n = reindex(all_entries, tmp_db)
    check("reindex counts all entries", n == len(all_entries))
    rows = search("attachment", db_path=tmp_db)
    check("FTS search finds the elimination", rows
          and rows[0][0] == "elim_1")
    rows = search("desktop screenshots", chapter="constitution", db_path=tmp_db)
    check("chapter-filtered search", rows and rows[0][0] == "claude:H-2")
    check("fts quoting wraps hyphenated tokens",
          _fts_quote("audio-visual sync") == '"audio-visual" "sync"')
    rows = search("shield_strength_points", db_path=tmp_db)
    check("drift tokens searchable", bool(rows))

    md = render_md(all_entries)
    check("book renders all chapter headings + feature index",
          "II. Closed Doors" in md and "Index of Features" in md
          and "Verb_Shovel" in md)
    check("empty chapters admitted honestly",
          "not learned this kind of thing yet" in md)

    print(f"\n{PASS}/{TOTAL} tests passed")
    return 0 if PASS == TOTAL else 1


if __name__ == "__main__":
    raise SystemExit(main())
