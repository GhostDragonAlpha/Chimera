#!/usr/bin/env python3
"""MAT2-X04: the sealed-run driver (the ONE command the runner executes).

Order is law: 1 the gated presentation-verification experiment (pins ->
registry/profile BEFORE capture -> prereg-commit law -> certified-line gate
-> arms A1/A2 -> state derivation + material-mapping audit -> predictions
P1-P12 -> bites FB1-FB5 -> receipts + traces) -> 2 the named-check suite
(checks_receipt.json) -> 3 the bounded capture (FFV1 video + manifest +
pinned validator; the frozen prereg law, unchanged) -> 3b the standing
two-stage capture gate (capture_card/ template: palette + object-ID mask
co-location over the ACTUAL committed frames, 3 production + 4 defect
cases; assigned by the resumed dispatch, disclosed in
capture_card/card/card_prereg.json) -> 4 the generated report -> 5 the
report-number lint. Every stage must exit green; the first failure stops
the driver with that stage's own exit code. No subprocess is ever launched
except run_capture_x04.py's DECLARED ffmpeg capture-tool calls; each
stage's main() runs in-process.

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
    ("presentation_verification", "run_presentation_verification.py"),
    ("named_checks", "run_checks.py"),
    ("capture", "run_capture_x04.py"),
    ("capture_gate", "run_capture_gate_x04.py"),
    ("report_generation", "make_report.py"),
    ("report_lint", "lint_report_numbers.py"),
]


def run_stage(name, module):
    import importlib.util
    path = CARD / module
    spec = importlib.util.spec_from_file_location("x04_stage_" + name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["x04_stage_" + name] = mod
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
        "schema": "chimera.x04_sealed_run.v1",
        "card": "MAT2-X04",
        "attempt_id": "50ff462483fd487db3ec9d38fa656f92",
        "stages": results,
        "pass": failed == 0,
        "determinism": {"canonical_json": True, "newline": "\n",
                        "command": "python -B tools/monkey_campaign/"
                                   "contributions/MAT2-X04/run_all.py"},
    }
    (out_dir / "result.json").write_bytes(
        json.dumps(summary, ensure_ascii=False, sort_keys=True,
                   separators=(",", ":"), allow_nan=False).encode("utf-8")
        + b"\n")
    print("sealed-run summary:", summary["pass"])
    sys.exit(failed)
