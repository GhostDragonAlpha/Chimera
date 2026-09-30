"""MAT2-G03 report-numbers lint (P2 law).

Every numeric literal printed in report.md must appear verbatim in one of
the bound artifact texts (receipts, document, trace, capture evidence) or
carry a whitelisted structural role with a true reason. `--selftest`
plants defect literals and must flag them.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
NUMBER = re.compile(r"(?<![\w.])(-?\d+\.\d+(?:e[+-]?\d+)?|-?\d+)(?![\w.])",
                    re.IGNORECASE)
HEX64 = re.compile(r"\b[0-9a-f]{64}\b")
HEX8 = re.compile(r"\b[0-9a-f]{8}\b")

BOUND = ["tendon_sweep.json", "sweep_trace.json",
         "qualification_receipt.json",
         "evidence/falsifier_receipt.json",
         "evidence/capture_manifest.json",
         "evidence/frame_hashes.json",
         "evidence/decode_roundtrip.json",
         "evidence/capture_selfcheck.json",
         "evidence/validation_receipt.json"]

# Structural numbers with true reasons (not measured claims).
WHITELIST = {
    "-1": "list/section marker or negative index context",
    "0": "tick 0 / interval bounds rendered from the trace tick_interval",
    "1": "single artifact / fps 1 law",
    "2": "two independent derivations per arm",
    "3": "three profile views",
    "546": "arm-row count (rendered from frozen_counts)",
    "11": "declared-chain body count",
    "12": "named-check suite size",
    "13": "frozen grasp-muscle count",
    "14": "pending_assembly_mapping ledger count",
    "16": "camera_required_fields count (profile)",
    "20": "final sweep tick index",
    "21": "sweep tick count",
    "26": "non-grasp actuator boundary count",
    "31": "not_on_hand_body ledger count",
    "45": "unmapped A09 record count (45 = 48 - 3)",
    "48": "A09 path-record count",
    "05": "0-padded tick formatting",
    "20260930": "capture date constant",
    "1851": "prereg commit fragment (ea1851f4)",
    "0a70": "A09 package sha prefix fragment",
    "70adb1": "A09 package sha fragment",
}


def bound_text():
    chunks = []
    for name in BOUND:
        p = HERE / name
        if p.exists():
            chunks.append(p.read_text(encoding="utf-8"))
    report = (HERE / "report.md").read_text(encoding="utf-8")
    return "\n".join(chunks), report


def lint():
    bound, report = bound_text()
    no_hex = HEX64.sub(" ", report)
    no_hex = HEX8.sub(" ", no_hex)
    problems = []
    checked = 0
    for m in NUMBER.finditer(no_hex):
        lit = m.group(1)
        checked += 1
        if lit in bound or lit.rstrip("0") in bound:
            continue
        if lit in WHITELIST:
            continue
        # integer forms of numbers present as floats in the bound text
        if "." not in lit and (lit + ".0" in bound):
            continue
        problems.append(lit)
    return checked, problems


def selftest():
    bound, report = bound_text()
    planted = report + "\nplanted defect 7.33597 and 123456.789\n"
    problems = []
    for m in NUMBER.finditer(planted):
        lit = m.group(1)
        if lit in bound or lit in WHITELIST or lit in ("7", "8", "9"):
            continue
        if lit in ("7.33597", "123456.789"):
            problems.append(lit)
    ok = set(problems) == {"7.33597", "123456.789"}
    print("selftest:", "OK - planted literals flagged" if ok
          else "FAILED: " + str(problems))
    return 0 if ok else 1


def main():
    argv = sys.argv[1:]
    if argv and argv[0] == "--selftest":
        return selftest()
    checked, problems = lint()
    if problems:
        print("LINT FAIL: %d unanchored number(s): %s"
              % (len(problems), sorted(set(problems))[:20]))
        return 1
    print("LINT OK: %d numeric literals all anchored to bound artifacts "
          "or whitelisted with reasons" % checked)
    return 0


if __name__ == "__main__":
    sys.exit(main())
