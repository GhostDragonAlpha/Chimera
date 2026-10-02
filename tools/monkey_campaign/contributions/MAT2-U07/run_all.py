#!/usr/bin/env python3
"""MAT2-U07: the sealed-run driver (the ONE command the runner executes).

Order is law: 1 the gated controls-verification experiment (pins -> registry
-> certified-line gate -> arms R1-R5 -> render/present -> predictions P1-P12
-> receipts + traces) -> 2 the named-check suite (checks_receipt.json) ->
3 the bounded capture (views + manifest + mkv, pinned validator) -> 4 the
generated report -> 5 the report-number lint. Every stage must exit green;
the first failure stops the driver with that stage's own exit code. No
subprocess is ever launched except run_capture_u07.py's DECLARED ffmpeg
capture-tool calls (prereg FB9); each stage's main() runs in-process.

Run:  python -B run_all.py   (from the sealed root; the runner's cwd)
Exit: 0 green / the failing stage's exit code.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

CARD = Path(__file__).resolve().parent
sys.path.insert(0, str(CARD))

STAGES = [
    ("controls_verification", "run_controls_verification.py"),
    ("named_checks", "run_checks.py"),
    ("capture", "run_capture_u07.py"),
    ("report_generation", "make_report.py"),
    ("report_lint", "lint_report_numbers.py"),
]


def run_stage(name, module):
    import importlib.util
    path = CARD / module
    spec = importlib.util.spec_from_file_location("u07_stage_" + name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["u07_stage_" + name] = mod
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
        "schema": "chimera.u07_sealed_run.v1",
        "card": "MAT2-U07",
        "attempt_id": "5e2bc3cb1fec4305911a1048b600723d",
        "correction_round": {"round": "r1", "worker": "wk-u07-fix",
                             "package_base_sha256":
                             "69772e9143d582cdd0d2d56c990c0a5b0e697509",
                             "reason": "sgt-pr312-69772e91 CHANGES-REQUIRED "
                                       "(PIXEL-FAIL): U07_VIEWS follow law "
                                       "fixed; mechanical pixel-content "
                                       "gate added (AMENDMENT-A4)"},
        "stages": results,
        "pass": failed == 0,
        "determinism": {"canonical_json": True, "newline": "\n",
                        "command": "python -B tools/monkey_campaign/"
                                   "contributions/MAT2-U07/run_all.py"},
    }
    (out_dir / "result.json").write_bytes(
        json.dumps(summary, ensure_ascii=False, sort_keys=True,
                   separators=(",", ":"), allow_nan=False).encode("utf-8")
        + b"\n")
    print("sealed-run summary:", summary["pass"])
    sys.exit(failed)
