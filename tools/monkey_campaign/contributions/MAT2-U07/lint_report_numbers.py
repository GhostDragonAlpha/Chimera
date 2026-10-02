#!/usr/bin/env python3
"""MAT2-U07: the report-number lint (every number in REPORT.md must exist in
a stage receipt; every preregistered bound must appear verbatim).

Run:  python -B lint_report_numbers.py   (exit 0 green / 1 lint failure)
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = Path(os.environ.get("CHIMERA_OUTPUT_DIR", HERE / "outputs"))


def main() -> int:
    report = (OUT / "REPORT.md").read_bytes().decode("utf-8")
    # sha-like hex tokens (16+ hex chars) are identities, not numbers
    report_scan = re.sub(r"[0-9a-fA-F]{16,}", "SHA", report)
    receipt = json.loads((OUT / "controls_receipt.json").read_bytes())
    checks = json.loads((OUT / "checks_receipt.json").read_bytes())
    capture = json.loads(
        (OUT / "capture" / "capture_receipt.json").read_bytes())
    pred = receipt["predictions"]

    def numbers(doc):
        blob = json.dumps(doc, sort_keys=True)
        return set(re.findall(r"-?\d+\.\d+(?:e-?\d+)?|-?\d+\b", blob))

    pool = numbers(receipt) | numbers(checks) | numbers(capture)
    # the limits/bounds that are PREREGISTERED caller data, not receipt data
    allowed_prereg = {"50.0", "300", "15", "100", "30", "31", "1", "0",
                      "4365", "4665", "4500", "4650", "4351", "4651",
                      "16", "960", "540",
                      # preregistered IDENTITIES, not measurements: the
                      # frozen prediction ordinals P1-P12, arm ordinals
                      # R1-R5 and amendment ordinals A1-A4. (Correction r1:
                      # "11" surfaced when the named-check count stopped
                      # carrying it incidentally; the ID ordinals are
                      # declared here so identity tokens never depend on
                      # incidental receipt arithmetic.)
                      "2", "3", "4", "5", "6", "7", "8", "9", "10",
                      "11", "12"}
    failures = []
    for num in set(re.findall(r"-?\d+\.\d+(?:e-?\d+)?|-?\d+\b",
                              report_scan)):
        if num not in pool and num not in allowed_prereg:
            failures.append("unbacked_number:" + num)
    lowered = report.lower()
    for token in ("unqualified", "absent", "not measured",
                  "does not close the card"):
        if token not in lowered:
            failures.append("missing_honesty_marker:" + token)
    pred_ids = sorted(pred.keys())
    for n in range(1, 13):
        if not any(k.startswith("P%d_" % n) for k in pred_ids):
            failures.append("missing_prediction:P%d" % n)
    if failures:
        for f in failures:
            print("LINT:" + f, file=sys.stderr)
        return 1
    (OUT / "lint_receipt.json").write_bytes(json.dumps(
        {"schema": "chimera.u07_lint_receipt.v1", "verdict": "GREEN",
         "backed_numbers": len(pool)}, sort_keys=True,
        separators=(",", ":")).encode("utf-8") + b"\n")
    print("lint: GREEN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
