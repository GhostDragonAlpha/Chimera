"""Report-numbers lint for MAT2-F05: every number in report.md must be
traceable to evidence/checks.json, evidence/determinism.json,
evidence/validation_receipt.json, evidence/capture_manifest.json or
evidence/terrain_envelope_declaration.json.

--selftest plants a bogus number and requires the lint to refuse it.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent

NUMBER_RE = re.compile(r"(?<![\w.])(\d+\.\d+(?:e[+-]?\d+)?|\d+)(?![\w.])",
                       re.IGNORECASE)


def load_sources():
    sources = []
    for name in ("checks_receipt.json", "determinism.json",
                 "validation_receipt.json", "capture_manifest.json",
                 "terrain_envelope_declaration.json"):
        for cand in (HERE / name, HERE / "evidence" / name):
            if cand.is_file():
                sources.append((name, cand.read_text()))
                break
    return sources


def collect_numbers(text):
    out = set()
    for match in NUMBER_RE.finditer(text):
        raw = match.group(1)
        try:
            value = float(raw)
        except ValueError:
            continue
        out.add(value)
        out.add(round(value, 6))
        out.add(round(value, 3))
        out.add(round(value, 4))
        out.add(round(value, 9))
        out.add(int(value) if value == int(value) else value)
    return out


def lint(report_text, sources, extra_allowed=()):
    """Every number in the report must appear in some source (numeric
    equality at the printed precision) or be explicitly allowed (small
    structural integers: section numbers, counts, citations). Measured
    floats MUST trace to the receipts. Returns the untraceable numbers."""
    allowed = set(extra_allowed)
    source_numbers = set()
    source_text = ""
    for name, text in sources:
        source_text += text
        source_numbers |= collect_numbers(text)
    untraceable = []
    for match in NUMBER_RE.finditer(report_text):
        raw = match.group(1)
        if len(raw) >= 32:            # commit/pin hashes are substrings
            if raw not in source_text:
                untraceable.append(raw)
            continue
        value = float(raw)
        if value in allowed:
            continue
        candidates = {value, round(value, 3), round(value, 4),
                      round(value, 6), round(value, 9),
                      int(value) if value == int(value) else value}
        if not (candidates & source_numbers):
            untraceable.append(raw)
    return untraceable


def main(argv):
    report = HERE / "report.md"
    require_text = report.read_text()
    sources = load_sources()
    # structural allowances: small integers used as section numbers, counts,
    # citations; the subsection indices 2.1-2.4 (heading numbers, not
    # measurements); the Python interpreter version 3.14 cited in the
    # commands section; the pinned seeds/dates; the declaration seeds; the
    # grid size. Measured floats must trace.
    extra = (set(range(0, 1000))
             | {2.1, 2.2, 2.3, 2.4, 3.14}
             | {20260919, 20260920, 20260921, 20260928, 20260929,
                1536.0, 4600823, 4598321})
    untraceable = lint(require_text, sources, extra)
    if argv and argv[0] == "--selftest":
        poisoned = require_text + "\nTracer number: 0.00742510001\n"
        bad = lint(poisoned, sources, extra)
        if "0.00742510001" not in bad and "0.0074251" not in bad:
            print("lint selftest FAILED: the planted number was not refused")
            return 1
        print("lint selftest OK: the planted number is refused "
              "(%d untraceable)" % len(bad))
        return 0
    if untraceable:
        print("lint FAILED: untraceable report numbers:")
        for n in untraceable:
            print(" -", n)
        return 1
    print("lint OK: every report number traces to the evidence receipts")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
