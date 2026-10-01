#!/usr/bin/env python3
"""MAT2-W08: the sealed-run driver (the ONE command the runner executes).

Order is law: 1 the gated command-verification experiment (receipts +
trace) -> 2 the checks suite (checks_receipt.json) -> 3 the motion capture
(capture/) -> 4 the generated report -> 5 the report-number lint. Every
stage must exit green; the first failure stops the driver with that stage's
own exit code. No subprocess is ever launched (each stage's main() runs
in-process); the declared ffmpeg capture-tool calls stay inside
run_capture.py exactly as declared (prereg FB9).

Run:  python -B run_all.py   (from the sealed root; the runner's cwd)
Exit: 0 green / the failing stage's exit code.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

CARD = Path(__file__).resolve().parent
sys.path.insert(0, str(CARD))

STAGES = [
    ("command_verification", "run_command_verification.py"),
    ("named_checks", "run_checks.py"),
    ("motion_capture", "run_capture.py"),
    ("report_generation", "make_report.py"),
    ("report_lint", "lint_report_numbers.py"),
]


def run_stage(name, module):
    import importlib.util
    path = CARD / module
    spec = importlib.util.spec_from_file_location("w08_stage_" + name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.main()


if __name__ == "__main__":
    os.chdir(CARD)
    results = []
    failed = 0
    for name, module in STAGES:
        rc = run_stage(name, module)
        results.append({"stage": name, "module": module,
                        "exit_code": rc,
                        "verdict": "GREEN" if rc == 0 else "RED"})
        print("stage %s -> %s" % (name, "GREEN" if rc == 0 else "RED %d" % rc))
        if rc != 0:
            failed = rc
            break
    out_dir = Path(os.environ.get("CHIMERA_OUTPUT_DIR", CARD / "outputs"))
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "schema": "chimera.w08_sealed_run.v1",
        "card": "MAT2-W08",
        "attempt_id": "c38b22e505874601aa3f3a3ba9035e4d",
        "stages": results,
        "pass": failed == 0,
        "determinism": {"canonical_json": True, "newline": "\n",
                        "command": "python -B tools/monkey_campaign/"
                                   "contributions/MAT2-W08/run_all.py"},
    }
    (out_dir / "result.json").write_bytes(
        json.dumps(summary, ensure_ascii=False, sort_keys=True,
                   separators=(",", ":"), allow_nan=False).encode("utf-8")
        + b"\n")
    print("sealed-run summary:", summary["pass"])
    sys.exit(failed)
