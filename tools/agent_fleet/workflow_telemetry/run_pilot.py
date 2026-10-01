"""run_pilot.py -- orchestrate the Astra P0 workflow-telemetry pilot.

Read-only over the lanes; writes ONLY to this repo's validation receipt dir:
  ledger.jsonl            the append-only event ledger (schema.py)
  serial_path_35_38.json  the measured serial critical-path division
  f_event_gap.json        the reconciliation verdict
  RECEIPT.md              the human receipt (append-only, docs-last)

Usage:  python -m tools.agent_fleet.workflow_telemetry.run_pilot
"""
from __future__ import annotations

import io
import json
import os
import sys
from datetime import datetime

# allow direct-file execution as well as -m
if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))))))
    from tools.agent_fleet.workflow_telemetry import collectors as C  # noqa: E402
    from tools.agent_fleet.workflow_telemetry import reconstruct as R  # noqa: E402
    from tools.agent_fleet.workflow_telemetry.schema import append_all  # noqa: E402
else:
    from . import collectors as C
    from . import reconstruct as R
    from .schema import append_all

RECEIPT_DIR = os.path.join(C.CANON_REPO, "tools", "science_funnel", "validation",
                           "workflow_telemetry_20260921")


def main() -> int:
    t0 = datetime.now().astimezone().isoformat(timespec="seconds")
    receipts = C.collect_receipts()
    commits = C.collect_wave_commits()
    artifacts = C.collect_lane_artifacts()
    janitor = C.collect_janitor()

    attempts = R.build_attempts(receipts, commits)
    spath = R.serial_path(attempts, artifacts)
    gap = R.reconcile(attempts, receipts, commits, janitor)
    events = R.build_events(attempts, artifacts, spath)

    os.makedirs(RECEIPT_DIR, exist_ok=True)
    ledger_path = os.path.join(RECEIPT_DIR, "ledger.jsonl")
    if os.path.exists(ledger_path):
        os.remove(ledger_path)          # fresh pilot run; the file is the run's
    append_all(ledger_path, events)     # product -- append-only within the run

    with open(os.path.join(RECEIPT_DIR, "serial_path_35_38.json"), "w",
              encoding="utf-8") as fh:
        json.dump(spath, fh, indent=1, ensure_ascii=False)
    with open(os.path.join(RECEIPT_DIR, "f_event_gap.json"), "w",
              encoding="utf-8") as fh:
        json.dump(gap, fh, indent=1, ensure_ascii=False)

    # ---- console summary ----
    print(f"== workflow telemetry pilot == {t0}")
    print(f"attempts in ledger : {len(attempts)}  "
          f"({', '.join('wave-' + w for w in sorted(attempts, key=R._wave_sort))})")
    for wv in sorted(attempts, key=R._wave_sort):
        a = attempts[wv]
        sc = a["ship_commit"]
        print(f"  wave-{wv:<4} outcome={a['outcome']:<9} "
              f"ship={sc['sha'] if sc else '--'} "
              f"parent={a['parent_attempt'] or '--'}")
    print(f"events written     : {len(events)} -> {os.path.relpath(ledger_path, C.CANON_REPO)}")

    print("\n== serial path, waves 35-38 (seconds on the serial critical path) ==")
    tot = {}
    span_tot = 0.0
    for wv in sorted(spath, key=int):
        s = spath[wv]
        if "phases_seconds" not in s:
            print(f"  wave-{wv}: {s}")
            continue
        ph = s["phases_seconds"]
        span_tot += s["lane_span_seconds"] or 0.0
        line = f"  wave-{wv}: span {s['lane_span_seconds']:>6.0f}s | "
        for k in ("wait_for_lead", "reproduce", "mine_derive", "build_run",
                  "verify_decide"):
            v = ph[k]
            tot[k] = tot.get(k, 0.0) + (v or 0.0)
            line += f"{k}={v:.0f} " if v is not None else f"{k}=UNK "
        line += f"| F-TIME-ACCOUNTING {s['f_time_accounting']}" \
                f" (delta {s['f_time_accounting_delta_seconds']}s)"
        print(line)
    grand = sum(tot.values()) or 1
    print("  aggregate division of the timed phases:")
    for k in ("wait_for_lead", "reproduce", "mine_derive", "build_run",
              "verify_decide"):
        bar = "#" * int(round(60 * tot.get(k, 0) / grand))
        print(f"    {k:<14} {tot.get(k, 0):>8.0f}s  {100 * tot.get(k, 0) / grand:5.1f}%  {bar}")
    print(f"  total lane span 35-38: {span_tot:.0f}s "
          f"({span_tot / 60:.1f} min across 4 waves)")

    print(f"\nF-EVENT-GAP: {gap['verdict']}")
    if gap["missing_from_ledger"]:
        print(f"  missing from ledger: {gap['missing_from_ledger']}")
    if gap["unanchored_attempts"]:
        print(f"  unanchored attempts: {gap['unanchored_attempts']}")
    print(f"  independent records: "
          f"{ {k: len(v) for k, v in gap['independent_records'].items()} }")
    return 0 if gap["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
