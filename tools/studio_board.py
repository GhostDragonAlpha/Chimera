#!/usr/bin/env python3
"""studio_board.py — THE ENGINE STUDIO's board feed (B1/B2).

Reads the repo's own gate truth — docs/THE_BODY_PIPELINE.md (the B0-B10 table
+ the Monkey status board) — and writes the JSON the engine's overlay polls
(studio_board.json next to chimera_engine.exe by default).

The tool COMPUTES, the engine READS: nothing in the overlay owns gate state,
and nothing here invents it — every status string below is classified from the
pipeline doc's own "Monkey status" cells. The standing rule (B2) is derived:
the earliest stage whose classification is not green.

Usage:
    python tools/studio_board.py [--out PATH] [--doc PATH]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DOC = REPO_ROOT / "docs" / "THE_BODY_PIPELINE.md"
DEFAULT_OUT = (REPO_ROOT / "ChimeraEngine" / "engine" / "build" / "Release"
               / "studio_board.json")


def classify(cell: str) -> str:
    """Map a Monkey-status cell to the overlay's status vocabulary.

    green | partial | next | pending | blocked | rolling — the words come from
    THE_ENGINE_STUDIO.md B1; the mapping is from the doc's own phrasing.
    """
    c = cell.strip().lower()
    if "next" in c and "pending" not in c:
        return "next"
    if "blocked" in c:
        return "blocked"
    if "rolling" in c:
        return "rolling"
    has_done = ("done" in c) or ("green" in c)
    has_pending = "pending" in c
    has_live = ("live" in c) or ("walks" in c)
    if has_done and not has_pending:
        return "green"
    if has_pending and (has_done or has_live):
        return "partial"
    return "pending"


def parse_pipeline(doc: Path):
    text = doc.read_text(encoding="utf-8")
    stages = []
    # The B0-B10 table rows: | **B5** | ANATOMY REFEREE | ... | Monkey status |
    for m in re.finditer(r"^\|\s*\*\*(B\d+)\*\*\s*\|([^|]+)\|(.*)\|$",
                         text, flags=re.MULTILINE):
        sid = m.group(1)
        name = m.group(2).strip()
        cells = [c.strip() for c in m.group(3).split("|")]
        status_cell = cells[-1] if cells else ""
        stages.append({"id": sid, "name": name, "status": classify(status_cell),
                       "cell": status_cell})

    # The "Monkey status board" section is the doc's own summary — it OUTRANKS
    # per-cell prose (B0's cell mentions a *teddy* gate pending the operator;
    # the board section says B0-B4, B9 green for the monkey).
    by_id = {s["id"]: s for s in stages}
    gm = re.search(r"B(\d+)–B(\d+)(?:,\s*B(\d+))?\s*:\s*\*\*green", text)
    if gm:
        lo, hi = int(gm.group(1)), int(gm.group(2))
        for n in range(lo, hi + 1):
            sid = f"B{n}"
            if sid in by_id:
                by_id[sid]["status"] = "green"
        if gm.group(3) and f"B{gm.group(3)}" in by_id:
            by_id[f"B{gm.group(3)}"]["status"] = "green"
    nm = re.search(r"\*\*(B\d+) is the next stage\.\*\*", text)
    if nm and nm.group(1) in by_id:
        by_id[nm.group(1)]["status"] = "next"

    # The status board's own date, e.g. "## Monkey status board (2026-08-29)"
    dm = re.search(r"Monkey status board \(([^)]+)\)", text)
    updated = dm.group(1) if dm else ""
    return stages, updated


def standing_rule(stages):
    """B2: the earliest non-green gate — computed, never edited."""
    def order_key(s):
        m = re.match(r"B(\d+)", s["id"])
        return int(m.group(1)) if m else 99
    for s in sorted(stages, key=order_key):
        if s["status"] != "green":
            return (f"EARLIEST NON-GREEN GATE: {s['id']} {s['name'].lower()} "
                    f"-- the next stage  [{s['status']}]")
    return "ALL GATES GREEN -- the dyad's window is the last gate (B10)"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--doc", default=str(DEFAULT_DOC))
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    args = ap.parse_args()

    doc = Path(args.doc)
    if not doc.exists():
        print(f"FAIL: pipeline doc not found: {doc}")
        return 1
    stages, updated = parse_pipeline(doc)
    if not stages:
        print(f"FAIL: no B-stage rows parsed from {doc}")
        return 1

    board = {
        "stages": [{"id": s["id"], "name": s["name"], "status": s["status"]}
                   for s in stages],
        "standing": standing_rule(stages),
        "source": "docs/THE_BODY_PIPELINE.md",
        "updated": updated,
        "generated": datetime.now().isoformat(timespec="seconds"),
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(board, indent=1), encoding="utf-8")

    print(f"board: {len(stages)} stages from {doc.name} (status board {updated})")
    for s in stages:
        print(f"  {s['id']:>4} {s['name']:<18} {s['status']:<8} | {s['cell'][:70]}")
    print(f"standing: {board['standing']}")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
