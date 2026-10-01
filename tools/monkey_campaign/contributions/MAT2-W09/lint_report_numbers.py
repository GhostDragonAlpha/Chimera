#!/usr/bin/env python3
"""MAT2-W09: prove every numeric literal in REPORT.md traces to a bound
artifact.

The report is generated from the receipts; this linter re-proves the chain:
each numeric literal found in the report text must appear (at recorded
precision) inside one of the bound receipt bytes, or belong to the declared
allowance (structural section numbering, declared windows/labels quoted
verbatim from the prereg, and the shas/timestamps-like hex strings).

Run:  python -B lint_report_numbers.py
Exit: 0 green / 1 red (untraced literal) / 2 refusal.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = Path(os.environ.get("CHIMERA_OUTPUT_DIR") or (HERE / "receipts"))


def read(name_dir, name):
    for base in (OUT, HERE, HERE / "receipts"):
        p = base / name
        if p.exists():
            return p.read_bytes().decode("utf-8")
    raise SystemExit("lint refusal: missing " + name)

# Numeric literals that are part of the house markdown (table separators,
# section numbers, prereg-quoted declared constants) rather than measured
# values.
ALLOWED = {
    "1", "2", "3", "4", "5", "6", "7", "8", "9", "10",
    "0", "00", "000",
    "90",                # the declared fall horizon (scene REFLEX_TRIP_TICKS)
    "60",                # the sealed event count of the certified chain
    "300",               # the declared clock (physics_hz)
    "899", "900",        # the declared episode horizon (certified H)
    "0.2",               # the certified minimum drive (manifest bounds_lo)
    "0.008", "0.0081", "0.012",  # the declared gap algebra (scene constants)
    "8",                 # the certified command width
    "12",                # the receipt schema (w09)
}


def numeric_literals(text: str) -> list:
    out = []
    for m in re.finditer(r"(?<![\w.])-?\d+\.\d+(?:[eE][+-]?\d+)?"
                         r"|-?\d+(?![\w.])", text):
        token = m.group(0)
        out.append((token, text[:m.start()].count("\n") + 1))
    return out


def main() -> int:
    report = read(OUT, "REPORT.md")
    bound = []
    for name in ("out_of_envelope_receipt.json", "checks_receipt.json",
                 "falsifier_receipt.json", "capture_receipt.json",
                 "input_pins.json"):
        bound.append(read(OUT, name))
    haystack = "\n".join(bound)

    untraced = []
    for token, line in numeric_literals(report):
        if token in ALLOWED:
            continue
        if token in haystack:
            continue
        untraced.append((token, line))
    if untraced:
        for token, line in untraced[:20]:
            print("UNTRACED %s (report line %d)" % (token, line))
        print("untraced literals:", len(untraced))
        return 1
    print("lint OK: every numeric literal traces to a bound artifact "
          "(or the declared allowance)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
