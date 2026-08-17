"""orient.py -- the ONE live read: engine tree + verdict ledger + git, together.

The session used to start with `python Chimera/core/grow.py --read --depth 2` -- a command
that does not exist. The engine's ORIENT (mcp `orient`) reads the engine store but
not the verdict lane, and the verdict lane (LightEngine/JOINT_ATLAS) has no single
read at all. This is the replacement: both halves of the dyad, one command, machine-
readable with --json.

    python tools/orient.py            # the day starts here
    python tools/orient.py --json     # for a second system to consume

Reads, all live:
  - ChimeraEngine/engine_state.json   (the term hierarchy, gate progress, current)
  - tools/verdict_registry.json       (the Rule-0 verdict ledger)
  - git HEAD                           (the last membrane that landed)
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ChimeraEngine"))
sys.path.insert(0, str(ROOT / "tools"))

from engine_state import Engine   # noqa: E402
from verdict import VerdictLedger  # noqa: E402


def _git(log: bool = False) -> str:
    try:
        r = subprocess.run(["git", "log", "--oneline", "-5" if log else "-1"],
                           capture_output=True, text=True, cwd=ROOT)
        return r.stdout.strip()
    except Exception:
        return "(no git)"


def main() -> int:
    ap = argparse.ArgumentParser(description="the one live read -- engine + verdicts + git")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    a = ap.parse_args()

    eng = Engine()
    ledger = VerdictLedger()
    st = ledger.status()

    if a.json:
        out = {
            "current": eng.state.get("current"),
            "next_term": eng.next_term(),
            "open_terms": len([1 for v in eng.state["hierarchy"].values()
                               if v.get("status") not in ("proven", "decided")]),
            "proven_terms": len([1 for v in eng.state["hierarchy"].values()
                                 if v.get("status") in ("proven", "decided")]),
            "verdicts": {"open": len(st["open"]), "closed": len(st["closed"]),
                         "next_number": st["next_number"]},
            "head": _git(),
        }
        print(json.dumps(out, indent=2, sort_keys=True))
        return 0

    head = _git()
    print(f"ORIENT -- {head}")
    print("=" * 100)
    print(eng.orient())
    print("=" * 100)
    ledger.print_status()

    # The bridge: verdicts that still name no engine term are orphans of the joining
    orphans = [v for v in st["closed"] if not v.get("term")]
    if orphans:
        print()
        print(f"  {len(orphans)} CLOSED verdict(s) not linked to any engine term "
              f"(`python tools/verdict.py link <n> <term>`).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
