#!/usr/bin/env python3
"""MAT2-F06: the one-job driver (the runner's single command).

Order: the gated arms (terrain_walking.main) -> the capture (run_capture)
-> the report (make_report) -> the lint (the numbers traceable).  Any named
refusal fails the job.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import terrain_walking            # noqa: E402
import run_capture                # noqa: E402
import make_report                # noqa: E402
import lint_report_numbers        # noqa: E402


DECLARED_OUTPUTS = [
    "receipts/walking_receipt.json",
    "checks_receipt.json",
    "capture/trace_a0_cert.json", "capture/trace_a0_ext.json",
    "capture/trace_a1.json", "capture/trace_a2.json",
    "capture/trace_a3.json", "capture/trace_a4.json",
    "capture/capture_manifest.json", "capture/capture_context.json",
    "report.md",
]


def export_outputs():
    """Copy the declared artifacts into the runner's CHIMERA_OUTPUT_DIR
    (the --keep paths resolve there; the undeclared scratch is disposable)."""
    import os
    import shutil
    out = os.environ.get("CHIMERA_OUTPUT_DIR", "")
    if not out:
        return
    card = Path(__file__).resolve().parent
    bases = [Path(out), Path(out).parent]   # outputs/ and the scratch root
    for rel in DECLARED_OUTPUTS:
        src = card / rel
        if src.exists():
            for base in bases:
                dst = base / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src, dst)


def main() -> int:
    rc = terrain_walking.main()
    if rc:
        return rc
    rc = run_capture.main()
    if rc:
        return rc
    rc = make_report.main()
    if rc:
        return rc
    rc = lint_report_numbers.main()
    if rc:
        return rc
    rc = lint_report_numbers.selftest()
    if rc:
        return rc
    # the named checks: the receipt semantics (zero skips by design)
    import unittest
    loader = unittest.TestLoader()
    suite = loader.discover(str(Path(__file__).resolve().parent),
                            pattern="test_f06_terrain_walking.py")
    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(suite)
    if result.skipped:
        require(False, "named_check_skipped:" + repr(result.skipped))
    if not result.wasSuccessful():
        for _, tb in result.failures + result.errors:
            print(tb, file=sys.stderr)
        return 1
    export_outputs()
    return rc


def require(condition, code):
    if not condition:
        print("REFUSAL: " + code, file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    sys.exit(main())
