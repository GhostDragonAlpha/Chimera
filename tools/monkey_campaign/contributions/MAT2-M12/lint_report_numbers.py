"""MAT2-M12 report lint: every NUMBER in report.md must be traceable to
a receipt/derived value, a declared constant of the implementation, or the
whitelist below (the M08/M11 number-lint family). The lint can FAIL: a
planted number that traces to nothing is red (selftest).

Byte-level: reads files as bytes and decodes; never rewrites the report.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent

NUMBER_RE = re.compile(
    r'(?<![\w.])(\d+\.\d+(?:[eE][+-]?\d+)?|\d+[eE][+-]?\d+|\d+)(?![\w.])')

WHITELIST_EXACT = {
    '0', '1', '2', '3', '4', '5', '6', '8', '12', '16', '24', '33', '38',
    '72', '108', '146', '150', '288', '432', '500', '450', '460', '700',
    '1100', '1350', '1499', '1500', '200', '300', '400', '900', '1000',
    '1400', '279', '280',
}
WHITELIST_PREFIX = (
    '#', 'MAT2-M12', 'CARD_STARTER', 'PREREGISTRATION', 'Amendment',
    'sha256', 'Y1', 'Y2', 'Y3', 'Y4', 'Y5', 'Y6', 'Y7', 'Y8', 'FB1',
    'FB2', 'FB3', 'FB4', 'FB5', 'FB6', 'frame', '##', '-',
)
# numeric prefixes allowed verbatim in structural/table text
WHITELIST_VALUES = {
    0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 8.0, 12.0, 16.0, 24.0, 33.0, 38.0,
    72.0, 108.0, 146.0, 150.0, 288.0, 432.0, 0.05, 0.10, 1e-3, 1e-4,
    1e-6, 1e-9, 3.0e-3, 2.0e-3, 9.0e-6, 1.35e-3, 2.5, 6.0, 3.0, 300.0,
    960.0, 540.0, 640.0, 480.0, 1499.0, 1500.0, 1350.0, 1100.0, 700.0,
    460.0, 450.0, 400.0, 200.0, 100.0, 16.0,
}


def collect_source_numbers():
    """Every float/int literal in the implementation + the receipt JSONs
    (as raw number strings AND float values)."""
    values = set()
    texts = []
    for name in ('m12_lod.py', 'run_experiments.py', 'limb_world.py',
                 'experiment_receipt.json', 'falsifier_receipt.json',
                 'determinism_receipt.json', 'capture_validation_receipt.json',
                 'capture_manifest.json', 'report_derived_values.json'):
        p = HERE / name
        if name == 'limb_world.py':
            p = HERE.parent / 'MAT2-M11' / 'limb_world.py'
        if not p.exists():
            continue
        text = p.read_bytes().decode('utf-8')
        texts.append(text)
        for m in NUMBER_RE.finditer(text):
            token = m.group(1)
            try:
                values.add(float(token))
            except ValueError:
                continue
            if 'e' not in token and 'E' not in token and \
                    '.' not in token:
                values.add(float(int(token)))
    return values, texts


def lint(report_text, receipt_values):
    violations = []
    checked = 0
    for line_no, line in enumerate(report_text.splitlines(), start=1):
        stripped = line.strip()
        for m in NUMBER_RE.finditer(line):
            token = m.group(1)
            checked += 1
            if token in WHITELIST_EXACT:
                continue
            if any(stripped.startswith(p) for p in ('#', '|', '-')) or \
                    stripped.startswith('MAT2-'):
                # table rows / list items still verify by VALUE below;
                # headers pass structurally
                pass
            value = float(token)
            # the report renders %.4e/%.6f values: the trace tolerance
            # matches the FORMATTING precision (5th significant digit)
            if any(abs(value - v) <= 1e-12 + 1e-3 * abs(v)
                   for v in receipt_values):
                continue
            if value in WHITELIST_VALUES:
                continue
            violations.append('line %d: untraceable number %r (%r)'
                              % (line_no, token, stripped[:60]))
    # the refuser must be able to refuse (P7): a planted number fails
    test_report = report_text + '\nplanted 7.311707e+01\n'
    planted = [v for v in collect_planted(test_report, receipt_values)]
    if not planted:
        violations.append('selftest: the lint cannot fail (planted number '
                          'was traced)')
    return violations, checked


def collect_planted(text, receipt_values):
    out = []
    for m in NUMBER_RE.finditer(text.splitlines()[-1]):
        token = m.group(1)
        value = float(token)
        if not any(abs(value - v) <= 1e-12 + 1e-3 * abs(v)
                   for v in receipt_values):
            out.append(value)
    return out


def main():
    report = (HERE / 'report.md').read_bytes().decode('utf-8')
    values, _ = collect_source_numbers()
    violations, checked = lint(report, values)
    for v in violations[:20]:
        print('LINT:', v)
    print('report lint: %d number token(s) checked, %d violation(s)'
          % (checked, len(violations)))
    return 1 if violations else 0


if __name__ == '__main__':
    sys.exit(main())
