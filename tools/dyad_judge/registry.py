"""registry.py -- the blind-judge lane's writer for tools/verdict_registry.json.

LIVE STATE LAW (operator directive 2026-09-14): the registry is never clobbered
and never rewritten wholesale by this lane. Every write goes through
tools/verdict.py's VerdictLedger -- the SAME load/validate/number/save path the
biomechanics lane uses -- so `python tools/verdict.py status` shows blind-judge
verdicts WITHOUT modification, and the Rule-0 refusal (no statement/prediction/
falsifier, no entry) applies to judges exactly as it does to probes.

SCHEMA ADDITION (additive; verdict.py reads a fixed key set and ignores the
rest, so plain `new`/`close`/`status` are untouched). A blind-judge entry is a
normal verdict record PLUS:

    lane            "blind-judge"          -- the lane marker the gate reads
    judge           judge name (R8 playbook identity)
    judge_kind      "agent" | "human-relayed"
    session_dir     absolute path of the run's artifacts
    recording       path of the MP4 movie (the dyad watched it)
    eye             {lane, model, reason}   -- which watch lane served
    metrics         {novelty, pay, pay25, dent_visible_frames, hold_frames,
                     recovery_ms, eye_reports, lessons_completed, stalls}
    quotes          the verdict's 3 sharpest, verbatim
    dyad_analysis   {number: {...the measured half...},
                     term:  "...the buyer term from the quotes...",
                     alignment: 0.0..1.0 | None}

THE $25 GATE (docs/THE_SHIP_GOAL.md: "the judge's verdict is the gate"): the
gate is no longer prose -- gate25() reads CLOSED lane=="blind-judge" verdicts
and passes iff the LATEST one carries metrics.pay25 == true.
"""
from __future__ import annotations

import json
import shutil
import sys
import time
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent
ROOT = TOOLS.parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import verdict  # tools/verdict.py -- the standing ledger machinery

REGISTRY = TOOLS / "verdict_registry.json"
LANE = "blind-judge"


def backup(dest: Path) -> Path:
    """Back the registry up ONCE (the first backup is never overwritten)."""
    dest = Path(dest)
    if dest.exists():
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(REGISTRY, dest)
    return dest


def open_membrane(statement: str, prediction: str, falsifier: str,
                  probe: str = "") -> dict:
    """Rule 0 as a command, BEFORE the run: number all three parts or no entry."""
    led = verdict.VerdictLedger(REGISTRY)
    r = led.new(statement, prediction, falsifier, probe=probe)
    if not r["ok"]:
        return r
    r["verdict"]["lane"] = LANE            # additive lane marker; ledger law intact
    led._save()
    return r


def close_membrane(number: int, result: str, evidence: str, note: str = "",
                   provenance: dict | None = None) -> dict:
    """Record the run: result + evidence pointer + this lane's provenance keys."""
    led = verdict.VerdictLedger(REGISTRY)
    r = led.close(number, result, evidence, note=note)
    if not r["ok"]:
        return r
    rec = led.data["verdicts"][str(number)]
    for k, v in (provenance or {}).items():
        if k in ("number", "statement", "prediction", "falsifier", "status",
                 "result", "evidence", "created_at", "closed_at"):
            continue                        # the ledger's own keys are not ours
        rec[k] = v
    led._save()
    return r


def gate25() -> dict:
    """The $25 go-live gate, read from the registry instead of from prose.
    PASSES iff the latest CLOSED blind-judge verdict has metrics.pay25 true."""
    led = verdict.VerdictLedger(REGISTRY)
    rows = []
    for n, v in sorted(led.data["verdicts"].items(), key=lambda kv: int(kv[0])):
        if v.get("lane") != LANE:
            continue
        rows.append({"number": v["number"], "status": v["status"], "result": v.get("result"),
                     "judge": v.get("judge"), "pay25": (v.get("metrics") or {}).get("pay25"),
                     "novelty": (v.get("metrics") or {}).get("novelty"),
                     "evidence": v.get("evidence"), "closed_at": v.get("closed_at")})
    closed = [r for r in rows if r["status"] == "CLOSED"]
    latest = closed[-1] if closed else None
    return {"gate": "PASS" if (latest or {}).get("pay25") is True else "OPEN",
            "rule": "latest CLOSED blind-judge verdict must carry metrics.pay25 == true",
            "latest": latest, "history": rows}


if __name__ == "__main__":
    g = gate25()
    print(f"$25 GATE: {g['gate']}  ({g['rule']})")
    for r in g["history"]:
        print(f"  V{r['number']:<4} {r['status']:<7} {str(r['result']):<10} "
              f"judge={r['judge']!r:<20} pay25={r['pay25']} novelty={r['novelty']} "
              f"-> {r['evidence']}")
    if not g["history"]:
        print("  (no blind-judge verdicts in the registry yet)")
