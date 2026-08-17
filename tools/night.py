"""night.py -- the NIGHT gate: a failure captured at PROVE time is distilled into a rule.

THE METHOD SAYS the loop ends in NIGHT, where a failure becomes a rule with a scar (the
failure it was earned from) and a FALSIFIER (the measurement that would kill it). This is
the half of the workflow that was prose: `prove()` now records every refusal into
`engine_state.json["nights"]`; an agent or the operator distills a failure into a rule via
`earn_rule` (taste bottoms out in THE HUMAN, so the rule text is a decision, not a search);
and `check` enforces earned rules with a `forbids` pattern so a violation is REFUSED instead
of re-learned.

Usage:
  python tools/night.py log
  python tools/night.py fail <term> <gate> <detail>
  python tools/night.py rule <term> --text "..." --falsifier "..." [--forbids "regex"]
  python tools/night.py check <file>
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ChimeraEngine"))
from engine_state import Engine  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="the NIGHT gate")
    sub = ap.add_subparsers(dest="act", required=True)

    sub.add_parser("log")

    pf = sub.add_parser("fail")
    pf.add_argument("term")
    pf.add_argument("gate")
    pf.add_argument("detail")

    pr = sub.add_parser("rule")
    pr.add_argument("term")
    pr.add_argument("--text", required=True)
    pr.add_argument("--falsifier", required=True)
    pr.add_argument("--forbids", default="")

    pc = sub.add_parser("check")
    pc.add_argument("path")

    a = ap.parse_args()
    eng = Engine()

    if a.act == "log":
        print("NIGHTS (failures captured at PROVE time):")
        nights = eng.nights()
        if not nights:
            print("  (none yet)")
        for n in nights:
            print(f"  [{n['term']}] {n['gate']}: {n['detail']}")
        print("\nRULES (distilled, each with a scar + falsifier):")
        rules = eng.rules()
        if not rules:
            print("  (none yet -- distill a failure into a rule)")
        for r in rules:
            extra = f"  [forbids: {r['forbids']}]" if r.get("forbids") else ""
            print(f"  {r['id']} [{r['term']}]: {r['text']}  | FALSIFIER: {r['falsifier']}{extra}")
        return 0

    if a.act == "fail":
        eng._record_failure(a.term, a.gate, a.detail)
        print(f"recorded failure for {a.term} at {a.gate}")
        return 0

    if a.act == "rule":
        r = eng.earn_rule(a.term, a.text, a.falsifier, a.forbids)
        print(f"earned {r['id']} from {a.term}")
        return 0

    if a.act == "check":
        p = pathlib.Path(a.path)
        if not p.exists():
            print(f"NIGHT CHECK: no such file {p}")
            return 1
        text = p.read_text(encoding="utf-8", errors="ignore")
        bad = []
        for r in eng.rules():
            fb = r.get("forbids")
            if not fb:
                continue
            try:
                if re.search(fb, text):
                    bad.append(r)
            except re.error:
                pass
        if bad:
            print(f"NIGHT GATE REFUSED: {p} reintroduces a forbidden pattern:")
            for r in bad:
                print(f"  {r['id']}: {r['text']}  | FALSIFIER: {r['falsifier']}")
            return 1
        print(f"NIGHT GATE PASS: {p} violates no earned rule.")
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
