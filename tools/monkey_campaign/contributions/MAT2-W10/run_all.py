#!/usr/bin/env python3
"""MAT2-W10: the full card pipeline (order is law; every step gated).

pins -> walking_demo (the certified runs + P1-P12 + FB1/FB2/FB4)
     -> run_capture (profile check BEFORE capture; render + FFV1 + P13/FB5/FB6)
     -> run_checks (the named-check suite, zero skips)
     -> make_report (generated) -> lint_report_numbers (G2).

Run:  python -B run_all.py
Exit: nonzero on the first red (named refusal or failed prediction).
"""
from __future__ import annotations

import subprocess
import sys

HERE = __import__("pathlib").Path(__file__).resolve().parent
PY = sys.executable

STEPS = [
    ("walking_demo", "python -B walking_demo.py"),
    ("run_capture", "python -B run_capture.py"),
    ("run_checks", "python -B run_checks.py"),
    ("make_report", "python -B make_report.py"),
    ("lint", "python -B lint_report_numbers.py"),
]


def main() -> int:
    for name, cmd in STEPS:
        print("== " + name + " ==")
        proc = subprocess.run(cmd, shell=True, cwd=str(HERE))
        if proc.returncode != 0:
            print("STEP RED: " + name + " exit " + str(proc.returncode))
            return proc.returncode
    print("ALL STEPS GREEN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
