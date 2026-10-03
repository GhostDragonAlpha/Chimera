#!/usr/bin/env python3
"""MAT2-X05: the report-number lint (every REPORT.md number re-derived from
the receipts; a mismatch refuses).

Run:  python -B lint_report_numbers.py   (exit 0 green / 1 mismatch)
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = Path(os.environ.get("CHIMERA_OUTPUT_DIR", HERE / "outputs"))


def load(name):
    return json.loads((OUT / name).read_bytes().decode("utf-8"))


def main() -> int:
    report = (OUT / "REPORT.md").read_bytes().decode("utf-8")
    receipt = load("presentation_receipt.json")
    checks = load("checks_receipt.json")
    capture = load("capture_receipt.json")
    falsifier = load("falsifier_receipt.json")
    gate = load("capture_gate_summary.json")

    problems = []

    def need(cond, code):
        if not cond:
            problems.append(code)

    coupling = receipt["coupling_determination"]
    x5 = falsifier["X_P5_velocity_visible_in_clean"]
    x6 = falsifier["X_P6_flow_discriminates_speed"]

    # the headline numbers
    visible = str(x5["pairs_visible"]) + "/" + str(len(x5["rows"]))
    need(("**%s**" % ("VISIBLE" if x5["pairs_visible"] == len(x5["rows"])
                      and not x5["remediation_failed"]
                      else "NOT ESTABLISHED")) in report,
         "lint:L_pixel_verdict")
    need(visible in report, "lint:pairs_visible_fraction")
    need(coupling["phase_identity"] in report, "lint:phase_identity")
    need(coupling["com_v_divergence"] in report, "lint:com_v_divergence")
    need(coupling["disposition"] in report, "lint:disposition")
    run_ph = receipt["x_run_phase_determination"]
    need(run_ph["run_phase_divergence_observed"] is True,
         "lint:run_phase_finding_present")
    need("x_run_phase_divergence_observed" in report,
         "lint:run_phase_finding_disclosed")
    need(("t%s" % run_ph["first_divergent_tick"]) in report,
         "lint:run_phase_first_tick")
    first_counts = sorted(set(run_ph["identity_counts"].values()))
    need(first_counts[0] in report, "lint:run_phase_identity_counts")
    need(repr(receipt["anchor_base_x0"])[:10] in report.replace("x0 = ", "x0=")
         or ("%.6f" % receipt["anchor_base_x0"]) in report,
         "lint:anchor_x0")
    # the live-check minima
    min_clear = min(r["min_clearance_px"]
                    for r in receipt["landmark_live_checks"])
    min_sep = min(r["min_pairwise_separation_px"]
                  for r in receipt["landmark_live_checks"])
    need(("%.2f px" % min_clear) in report, "lint:min_clearance")
    need(("%.2f px" % min_sep) in report, "lint:min_separation")
    # gate + capture + checks
    need(gate["verdict"] in report, "lint:gate_verdict")
    need(str(gate["case_count"]) in report, "lint:gate_case_count")
    need(str(capture["video_count"]) in report, "lint:video_count")
    need(checks["claim"] in report, "lint:checks_claim")
    # the seam first-response worst + the finding count
    worst = max(p["seam"]["A"]["first_response_worst_ms"]
                for p in receipt["pairs"])
    need(("worst %s ms" % worst) in report, "lint:seam_worst")
    findings = sum(len(p["seam"]["A"]["x_p9_findings"])
                   for p in receipt["pairs"])
    need(str(findings) in report, "lint:x9_finding_count")
    # the X-P6 sums
    need((str(x6["short_brake_cum_sum_px"]) in report
          and str(x6["long_brake_cum_sum_px"]) in report),
         "lint:x6_sums")
    # the endpoint numbers re-derived from the coupling receipt
    for val in ("%.6f" % coupling["per_depth"]["SHORT"]["com_v_first_A"],
                "%.6f" % coupling["per_depth"]["SHORT"]["com_v_last_A"],
                "%.6f" % coupling["per_depth"]["LONG"]["com_v_last_A"]):
        need(val in report, "lint:endpoint:" + val)

    receipt_out = {
        "schema": "chimera.x05_lint_receipt.v1",
        "card_id": "MAT2-X05",
        "checks_total": 18,
        "problems": problems,
        "verdict": "GREEN" if not problems else "RED",
    }
    (OUT / "lint_receipt.json").write_bytes(
        json.dumps(receipt_out, indent=1, sort_keys=True).encode("utf-8")
        + b"\n")
    print("lint: %d problems -> %s" % (len(problems),
                                       receipt_out["verdict"]))
    for p in problems:
        print("lint problem:", p)
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
