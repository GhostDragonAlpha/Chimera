#!/usr/bin/env python3
"""MAT2-W05: run the named-check suite and emit checks_receipt.json.

The receipt carries the G12 accounting: every check id with its verdict, and
the claim string "N executed, M skipped" (a skipped test would RED the gate
unless KNOWN_SKIPS documents it; this card runs zero skips by design).

Run:  python -B run_checks.py
Exit: 0 green / 1 red suite / 2 refusal.
"""
from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent

PREREG_SHA256 = hashlib.sha256(
    (HERE / "PREREGISTRATION.md").read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def main():
    suite = unittest.defaultTestLoader.discover(start_dir=".",
                                                pattern="test_*.py")
    runner = unittest.TextTestRunner(verbosity=1, stream=sys.stdout)
    result = runner.run(suite)

    checks = []
    for case, outcome in getattr(result, "failures", []) + getattr(result, "errors", []):
        checks.append({"id": case.id(), "verdict": "FAIL",
                       "detail": outcome.splitlines()[-1][:200]})
    for case, reason in getattr(result, "skipped", []):
        checks.append({"id": case.id(), "verdict": "SKIPPED", "detail": reason})
    executed = result.testsRun - len(result.skipped)
    skipped = len(result.skipped)
    receipt = {
        "schema": "chimera.w05_checks_receipt.v1",
        "task_id": "W05",
        "card_id": "MAT2-W05",
        "suite": "test_w05_runbook.py (unittest discover -p test_*.py)",
        "preregistration_sha256": PREREG_SHA256,
        "checks": checks,
        "tests_run": result.testsRun,
        "executed": executed,
        "skipped": skipped,
        "accounting_claim": "%d executed, %d skipped" % (executed, skipped),
        "known_skips": "none (zero skips by design; no KNOWN_SKIPS entries)",
        "pass": result.wasSuccessful() and skipped == 0,
        "determinism": {"canonical_json": True, "newline": "\n",
                        "command": "python -B run_checks.py"},
    }
    out = HERE / "checks_receipt.json"
    out.write_bytes(canonical(receipt) + b"\n")
    print("wrote", out)
    print("accounting:", receipt["accounting_claim"])
    print("pass:", receipt["pass"])
    return 0 if receipt["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
