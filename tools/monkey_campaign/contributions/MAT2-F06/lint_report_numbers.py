#!/usr/bin/env python3
"""MAT2-F06: the report-numbers lint (P2/G2).

The report is GENERATED from the bound receipts (make_report.py): every
number is rendered from the receipt JSON at recorded precision.  The lint
verifies traceability: every numeric literal in report.md must appear in
the bound receipts (the receipt values are the only allowed number source,
besides the structural constants: ticks, section numbers, the file's own
header values, and the declared zero/one).  --selftest plants a bogus
number into a scratch copy of the report and proves the detector refuses.

Run:  python -B lint_report_numbers.py            (exit 0 green)
      python -B lint_report_numbers.py --selftest (exit 0 if the detector
                                                   fires on the plant)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPORT = HERE / "report.md"
RECEIPTS = HERE / "receipts" / "walking_receipt.json"

STRUCTURAL = {
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10",
    "20260920",  # the certified seed
}
NUMBER_RE = re.compile(r"(?<![\w.])-?\d+\.\d+(?:e[-+]?\d+)?|(?<![\w.])\d+\b",
                       re.I)


def receipt_numbers():
    """Every numeric leaf of the bound receipt tree, as decimal strings."""
    doc = json.loads(RECEIPTS.read_bytes().decode("utf-8"))
    out = set()

    def walk(v):
        if isinstance(v, bool) or v is None:
            return
        if isinstance(v, (int, float)):
            out.add(repr(float(v)))
            out.add(str(v))
            out.add(f"{v:.6f}")
            out.add(f"{v:.17g}")
            return
        if isinstance(v, str):
            # string leaves render verbatim: their digit-runs are traceable
            for tok in NUMBER_RE.finditer(v):
                out.add(tok.group(0))
            return
        if isinstance(v, dict):
            for x in v.values():
                walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)
    walk(doc)
    return out


def check(text):
    """Returns the list of untraceable numeric literals."""
    allowed = receipt_numbers()
    bad = []
    for m in NUMBER_RE.finditer(text):
        token = m.group(0)
        if token in STRUCTURAL:
            continue
        context = text[max(0, m.start() - 50):m.end() + 30].replace(chr(10), " ")
        try:
            value = float(token)
        except ValueError:
            continue
        if repr(value) in allowed or token in allowed:
            continue
        # tolerance scan: a receipt value equal at the printed precision
        hit = False
        for a in allowed:
            try:
                if abs(float(a) - value) <= 1e-9 * max(1.0, abs(value)):
                    hit = True
                    break
            except ValueError:
                continue
        if not hit:
            bad.append(token + " @[" + context + "]")
    return bad


def selftest():
    """Plants a bogus number and proves the detector refuses."""
    text = REPORT.read_text(encoding="utf-8")
    planted = text.replace("# MAT2-F06 report",
                           "# MAT2-F06 report\n\nmeasured 12345.6789 m/s\n",
                           1)
    assert planted != text, "selftest plant failed"
    bad = check(planted)
    assert any(b.startswith("12345.6789") for b in bad),         "selftest detector did not fire: " + repr(bad[:5])
    print("selftest: the planted 12345.6789 is refused; the detector fires")
    return 0


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    text = REPORT.read_text(encoding="utf-8")
    bad = check(text)
    if bad:
        print("UNTRACEABLE REPORT NUMBERS: " + repr(bad[:20]), file=sys.stderr)
        return 1
    print("report numbers traceable: 0 untraceable literals")
    return 0


if __name__ == "__main__":
    sys.exit(main())
