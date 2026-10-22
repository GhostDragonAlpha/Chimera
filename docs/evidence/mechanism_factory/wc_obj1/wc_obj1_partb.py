"""WC-OBJ-1 part B receipts: step-window measure() + INCOMPLETE demos +
solution-B (pillar-on-pad tower) regression under the revised corner rule.

Uses workshop_challenge1's OWN analytic builders (scene_doc / pillar_doc /
crate_doc chain='tower') and its OWN Run harness — the published recipe — so
the receipt exercises the real measure()/check() against the real scene.
Challenge 2 inherits check/measure via Run2 (wc2 imports wc1), so these
receipts cover both challenges; no workshop_challenge2.py edit.

Usage: python wc_obj1_partb.py --port 8847
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / "tools" / "construction_packet"))

import workshop_challenge1 as wc1  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8847)
    args = ap.parse_args()

    out = HERE / "partb_run"
    run = wc1.Run(out, args.port)
    rec = {"label": "part B: step-window measure + corner-rule check "
                    "(challenge 2 inherits check/measure via Run2 — no wc2 "
                    "edit)",
           "window_rule_declared": None, "dt_substep_s": None,
           "results": {}}
    try:
        run.boot()
        run.log("boot", engine_sha256=run.exe_sha)
        r = run.eng.post("/tick_b2_admit", wc1.scene_doc())
        assert r.get("ok"), f"admit refused: {r}"
        run.pause(True)
        # solution B tower, analytic spawns, edits PAUSED on the analytic
        # base (the challenge's own discipline)
        r = run.eng.post("/tick_b2_place", wc1.pillar_doc())
        assert r.get("ok"), f"pillar refused: {r}"
        r = run.eng.post("/tick_b2_place", wc1.crate_doc(chain="tower"))
        assert r.get("ok"), f"crate refused: {r}"
        run.anchor("partB_tower_spawn")
        run.pause(False)
        st = run.settle(timeout=12.0)
        run.pause(True)
        rec["dt_substep_s"] = st["dt_substep_s"]
        assert st["dt_substep_s"] == 0.00025, \
            f"dt_substep_s changed: {st['dt_substep_s']}"
        rec["window_rule_declared"] = (
            f"WINDOW_STEPS {wc1.WINDOW_STEPS} substeps = "
            f"{wc1.WINDOW_STEPS * 0.00025:.0f} s physical at dt_substep_s "
            f"{st['dt_substep_s']}; judged by first->last row step span; "
            f"wall deadline HISTORY_S {wc1.HISTORY_S} s; deadline-first "
            "records INCOMPLETE, never a physics pass")

        # ── B2 + B1 pass: the pillar-on-pad tower under the revised
        #    corner rule, window judged by steps ──
        passed_b, fin_b = run.measure("solution_B_stepwindow")
        st = run.state()
        ok, clear, in_region, bottom, tipped = run.check(st)
        rec["results"]["solution_B_stepwindow"] = {
            "passed": passed_b,
            "incomplete": run.rec["predicate"]["solution_B_stepwindow"]
            ["incomplete"],
            "window_steps_span": run.rec["predicate"]["solution_B_stepwindow"]
            ["window_steps_span"],
            "window_rows": run.rec["predicate"]["solution_B_stepwindow"]
            ["window_rows"],
            "settled_clearance_m": fin_b["clearance_m"],
            "check_on_settled_state": {
                "ok": ok, "clearance_m": clear, "in_region": in_region,
                "tipped_wording_only": tipped},
            "n_parts": len(st["parts"]),
            "pillar_on_pad": True,
        }
        print("solution_B_stepwindow:", json.dumps(
            rec["results"]["solution_B_stepwindow"]))

        # ── B1 INCOMPLETE demo 1: pause mid-window — the frozen stretch
        #    accrues no steps, so the deadline expires before the span ──
        threading.Timer(2.0, lambda: run.pause(True)).start()
        threading.Timer(6.0, lambda: run.pause(False)).start()
        passed_p, fin_p = run.measure("window_paused_midwindow")
        pred_p = run.rec["predicate"]["window_paused_midwindow"]
        paused_rows = [r for r in run.rec["histories"]
                       ["window_paused_midwindow"] if r["paused"]]
        rec["results"]["window_paused_midwindow"] = {
            "passed": passed_p, "incomplete": pred_p["incomplete"],
            "window_steps_span": pred_p["window_steps_span"],
            "rows_showing_paused_true": len(paused_rows),
            "frozen_steps_evidence": (
                [r["steps"] for r in paused_rows[:3]] + ["..."] +
                [r["steps"] for r in paused_rows[-3:]]) if paused_rows else [],
        }
        print("window_paused_midwindow:", json.dumps(
            rec["results"]["window_paused_midwindow"]))

        # ── B1 INCOMPLETE demo 2: absurdly short wall deadline ──
        wc1.HISTORY_S = 0.6
        passed_s, fin_s = run.measure("window_short_deadline")
        wc1.HISTORY_S = 8.0
        pred_s = run.rec["predicate"]["window_short_deadline"]
        rec["results"]["window_short_deadline"] = {
            "passed": passed_s, "incomplete": pred_s["incomplete"],
            "window_steps_span": pred_s["window_steps_span"],
            "deadline_s": 0.6,
        }
        print("window_short_deadline:", json.dumps(
            rec["results"]["window_short_deadline"]))
    except Exception:
        (HERE / "partb_receipt_partial.json").write_text(
            json.dumps(run.rec, indent=1), encoding="utf-8")
        raise
    finally:
        if hasattr(run, "proc") and run.proc.poll() is None:
            run.proc.terminate()
            try:
                run.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                run.proc.kill()
        time.sleep(1.0)
    (HERE / "partb_receipt.json").write_text(
        json.dumps({"summary": rec, "run": run.rec}, indent=1),
        encoding="utf-8")
    print("receipt written:", HERE / "partb_receipt.json")
    ok_all = (rec["results"]["solution_B_stepwindow"]["passed"]
              and not rec["results"]["solution_B_stepwindow"]["incomplete"]
              and rec["results"]["window_paused_midwindow"]["incomplete"]
              and not rec["results"]["window_paused_midwindow"]["passed"]
              and rec["results"]["window_short_deadline"]["incomplete"]
              and not rec["results"]["window_short_deadline"]["passed"])
    print("PART B1+B2:", "PASS" if ok_all else "FAIL")
    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
