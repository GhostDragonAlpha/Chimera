#!/usr/bin/env python3
"""MAT2-X05: the named-check RUNNER: executes the gate-visible suite
(test_x05.py) and writes checks_receipt.json.

Run:  python -B run_checks.py   (writes checks_receipt.json; exit 0 green)
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

OUT = Path(os.environ.get("CHIMERA_OUTPUT_DIR", HERE / "outputs"))


def main() -> int:
    import test_x05 as suite_mod
    suite = unittest.defaultTestLoader.loadTestsFromModule(suite_mod)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    executed = result.testsRun
    skipped = len(result.skipped)
    failures = len(result.failures) + len(result.errors)
    receipt = {
        "schema": "chimera.x05_checks_receipt.v1",
        "card_id": "MAT2-X05",
        "preregistration_sha256":
            hashlib.sha256((HERE / "PREREGISTRATION.md").read_bytes())
            .hexdigest(),
        "executed": executed, "skipped": skipped, "failures": failures,
        "verdict": "GREEN" if failures == 0 and skipped == 0 else "RED",
        "claim": "%d executed, %d skipped" % (executed, skipped),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "checks_receipt.json").write_bytes(
        json.dumps(receipt, ensure_ascii=False, sort_keys=True,
                   separators=(",", ":"), allow_nan=False).encode("utf-8")
        + b"\n")
    print("checks: %d executed, %d skipped, %d failures -> %s"
          % (executed, skipped, failures, receipt["verdict"]))
    return 0 if failures == 0 and skipped == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
