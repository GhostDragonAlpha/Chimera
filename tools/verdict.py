"""verdict.py -- the Rule-0 verdict ledger, a mechanism instead of prose.

The biomechanics lane records VERDICTs in commit messages and JOINT_ATLAS.md
sections. Prose rots and, worse, prose cannot refuse: a membrane could be
written down with a STATEMENT but no FALSIFIER and nothing would object. The
port lane already solved this -- `port_test()` REFUSES to register a test that
names no falsifier. This is that same refusal, for the verdict lane.

Every VERDICT here is RULE 0 AT MEMBRANE GRANULARITY:
  STATEMENT   -- the claim, something someone could disagree with
  PREDICTION  -- the number, declared BEFORE the run
  FALSIFIER   -- what would refute it, named BEFORE the run
`new` REFUSES all three are present. `close` records the result + an evidence
pointer. The ledger is machine-readable (`--json`); orient.py reads it.

    python tools/verdict.py new   --statement "..." --prediction "..." --falsifier "..."
    python tools/verdict.py close 61 --result PASS --evidence tools/probes/x.py
    python tools/verdict.py list
    python tools/verdict.py status
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEDGER = Path(__file__).resolve().parent / "verdict_registry.json"

VALID_RESULTS = ("PASS", "FALSIFIED", "MARGINAL")

# Sources the auto-numberer scans for the highest existing VERDICT number, so
# a new verdict can never collide with one already recorded in the prose lane.
_SCAN_PATHS = [ROOT / "docs" / "JOINT_ATLAS.md"]
_SCAN_RE = re.compile(r"\bVERDICT\s*(\d+)\b")


class VerdictLedger:
    def __init__(self, path: Path = LEDGER):
        self.path = Path(path)
        self.data = self._load()

    def _load(self) -> dict:
        if self.path.exists():
            return json.loads(self.path.read_text(encoding="utf-8"))
        return {"verdicts": {}, "next": None}

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    # -- numbering ----------------------------------------------------------
    def highest_recorded(self) -> int:
        """Highest VERDICT number anywhere in the repo: ledger + atlas."""
        nums = set()
        for p in _SCAN_PATHS:
            if p.exists():
                nums.update(int(m) for m in _SCAN_RE.findall(p.read_text(encoding="utf-8")))
        nums.update(int(n) for n in self.data["verdicts"])
        return max(nums) if nums else 0

    def next_number(self) -> int:
        return self.highest_recorded() + 1

    # -- verbs --------------------------------------------------------------
    def new(self, statement: str, prediction: str, falsifier: str,
            term: str = "", probe: str = "", number: int = 0) -> dict:
        """RULE 0 AS A COMMAND: all three parts required, or the VERDICT does not exist."""
        missing = [n for n, v in (("STATEMENT", statement), ("PREDICTION", prediction),
                                  ("FALSIFIER", falsifier)) if not v]
        if missing:
            return {"ok": False,
                    "error": f"REFUSED (RULE 0): missing {' and '.join(missing)}. A membrane "
                             f"without a falsifier is a description, and a description cannot be wrong."}
        n = number or self.next_number()
        if str(n) in self.data["verdicts"]:
            return {"ok": False, "error": f"REFUSED: VERDICT {n} is already in the ledger. "
                                          f"(highest recorded anywhere: {self.highest_recorded()})"}
        if n <= self.highest_recorded():
            return {"ok": False, "error": f"REFUSED: VERDICT {n} already exists in the prose lane "
                                          f"(atlas). Highest recorded: {self.highest_recorded()}"}
        rec = {
            "number": n,
            "statement": statement,
            "prediction": prediction,
            "falsifier": falsifier,
            "term": term or "",
            "probe": probe or "",
            "status": "OPEN",
            "result": None,
            "evidence": None,
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "closed_at": None,
        }
        self.data["verdicts"][str(n)] = rec
        self.data["next"] = n + 1
        self._save()
        return {"ok": True, "verdict": rec}

    def close(self, number: int, result: str, evidence: str, note: str = "") -> dict:
        key = str(number)
        if key not in self.data["verdicts"]:
            return {"ok": False, "error": f"no VERDICT {number} in the ledger -- open it with `new` first"}
        if result not in VALID_RESULTS:
            return {"ok": False, "error": f"REFUSED: result must be one of {VALID_RESULTS}, got {result!r}"}
        if not evidence:
            return {"ok": False, "error": "REFUSED: a verdict needs an EVIDENCE pointer (a file, "
                                          "an npz, a report) -- otherwise the result is prose"}
        ev = (ROOT / evidence)
        if ev.exists():
            evidence = ev.resolve().relative_to(ROOT).as_posix()
        rec = self.data["verdicts"][key]
        rec["status"] = "CLOSED"
        rec["result"] = result
        rec["evidence"] = evidence
        rec["note"] = note
        rec["closed_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self._save()
        return {"ok": True, "verdict": rec}

    def link(self, number: int, term: str) -> dict:
        """Bridge the two lanes: attach this verdict to an ENGINE term so prove()/why
        can walk to it as evidence instead of dead-ending at prose."""
        key = str(number)
        if key not in self.data["verdicts"]:
            return {"ok": False, "error": f"no VERDICT {number} in the ledger"}
        self.data["verdicts"][key]["term"] = term
        self._save()
        return {"ok": True, "verdict": self.data["verdicts"][key]}

    def status(self) -> dict:
        open_ = [v for v in self.data["verdicts"].values() if v["status"] == "OPEN"]
        closed = [v for v in self.data["verdicts"].values() if v["status"] == "CLOSED"]
        return {"open": open_, "closed": closed,
                "next_number": self.next_number(), "total": len(self.data["verdicts"])}

    # -- printing -----------------------------------------------------------
    def print_status(self) -> None:
        st = self.status()
        print(f"VERDICT LEDGER -- {len(st['closed'])} closed, {len(st['open'])} open, "
              f"next number {st['next_number']}")
        print("=" * 100)
        for v in st["closed"]:
            term = f"  -> term {v['term']}" if v.get("term") else ""
            print(f"  [x] V{v['number']:<4} {v['result']:<10} {v['statement'][:60]}{term}")
        if st["open"]:
            print()
            print("  OPEN (the next membranes, RULE 0 enforced):")
            for v in st["open"]:
                print(f"  [ ] V{v['number']:<4} {v['statement']}")
                print(f"        falsifier: {v['falsifier'][:90]}")

    def print_rows(self) -> None:
        for n in sorted(self.data["verdicts"], key=int):
            v = self.data["verdicts"][n]
            status = f"{v['status']:<6} {v['result'] or ''}"
            print(f"V{n:<4} {status:<18} {v['statement'][:70]}")


def _git_head() -> str:
    try:
        return subprocess.run(["git", "log", "--oneline", "-1"], capture_output=True,
                              text=True, cwd=ROOT).stdout.strip()
    except Exception:
        return "(no git)"


def main() -> int:
    ap = argparse.ArgumentParser(description="Rule-0 verdict ledger for the biomechanics lane")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("new", help="open a VERDICT -- all three Rule-0 parts required")
    p.add_argument("--statement", required=True)
    p.add_argument("--prediction", required=True)
    p.add_argument("--falsifier", required=True)
    p.add_argument("--term", default="", help="engine term this verdict feeds")
    p.add_argument("--probe", default="", help="probe script path")
    p.add_argument("--number", type=int, default=0, help="explicit number (default: max+1)")

    p = sub.add_parser("close", help="record the result + evidence of a VERDICT")
    p.add_argument("number", type=int)
    p.add_argument("--result", required=True, choices=VALID_RESULTS)
    p.add_argument("--evidence", required=True)
    p.add_argument("--note", default="")

    p = sub.add_parser("link", help="bridge a VERDICT to an engine term")
    p.add_argument("number", type=int)
    p.add_argument("term")

    sub.add_parser("list", help="print the whole ledger")
    sub.add_parser("status", help="print open + closed, and the next number")

    a = ap.parse_args()
    L = VerdictLedger()

    if a.cmd == "new":
        r = L.new(a.statement, a.prediction, a.falsifier, term=a.term, probe=a.probe, number=a.number)
        if not r["ok"]:
            print(r["error"]); return 1
        v = r["verdict"]
        print(f"VERDICT {v['number']} OPENED (Rule 0: statement + prediction + falsifier all named).")
        print(f"  statement:  {v['statement']}")
        print(f"  prediction: {v['prediction']}")
        print(f"  falsifier:  {v['falsifier']}")
        print(f"  ledger: {LEDGER.relative_to(ROOT).as_posix()}")
        return 0

    if a.cmd == "close":
        r = L.close(a.number, a.result, a.evidence, note=a.note)
        if not r["ok"]:
            print(r["error"]); return 1
        v = r["verdict"]
        print(f"VERDICT {v['number']} CLOSED -- {v['result']}  (evidence: {v['evidence']})")
        print(f"  statement: {v['statement']}")
        return 0

    if a.cmd == "link":
        r = L.link(a.number, a.term)
        if not r["ok"]:
            print(r["error"]); return 1
        print(f"VERDICT {a.number} -> term `{a.term}` (the engine lane can now walk to this verdict)")
        return 0

    if a.cmd == "list":
        L.print_rows(); return 0

    if a.cmd == "status":
        L.print_status()
        print()
        print(f"  HEAD: {_git_head()}")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
