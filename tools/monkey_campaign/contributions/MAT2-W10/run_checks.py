#!/usr/bin/env python3
"""MAT2-W10: the named-check suite entry (receipt-semantics co-change law).

Runs the pinned-input verification and the executable done_when checks
(test_w10_walking_demo) against the COMMITTED receipts. The suite is the
G12 skip-accounting subject: zero skips by design.

Run:  python -B run_checks.py
Exit: 0 green / 1 checks red / 2 named refusal.
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import verify_inputs as vi          # noqa: E402


def main() -> int:
    vi.verify()
    reg = vi.verify_registry()
    suite = unittest.defaultTestLoader.discover(str(HERE),
                                                pattern="test_*.py")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    checks = {
        "schema": "chimera.w10_checks.v1",
        "task_id": "W10",
        "card_id": "MAT2-W10",
        "attempt_id": vi.ATTEMPT_ID,
        "preregistration_sha256": vi.prereg_sha256(),
        "amendment_a1_sha256": vi.amendment_a1_sha256(),
        "amendment_a2_sha256": vi.amendment_a2_sha256(),
        "criteria_sha256": vi.CRITERIA_SHA256,
        "registry_revision": reg.get("registry_revision"),
        "executed": result.testsRun,
        "skipped": len(result.skipped),
        "failures": len(result.failures),
        "errors": len(result.errors),
        "pass": result.wasSuccessful(),
        "accounting_claim": "%d executed, %d skipped"
                            % (result.testsRun, len(result.skipped)),
        "known_skips": "none (zero skips by design)",
        "determinism": {"canonical_json": True, "newline": "\n",
                        "command": "python -B run_checks.py"},
    }
    (HERE / "checks_receipt.json").write_bytes(
        json.dumps(checks, indent=1, sort_keys=True).encode("utf-8") + b"\n")
    print("checks:", checks["accounting_claim"], "| pass:", checks["pass"])
    return 0 if checks["pass"] else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except vi.Refusal as refusal:
        print("REFUSAL: " + str(refusal), file=sys.stderr)
        sys.exit(2)
