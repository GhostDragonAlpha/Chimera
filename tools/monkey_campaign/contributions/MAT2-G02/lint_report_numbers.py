"""MAT2-G02 report-number lint (P2, B05/M03 lineage).

Every numeric literal in report.md must trace to a committed receipt at its
printed precision, or sit on a whitelist with a true reason. --selftest
plants a defect literal and must flag it.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
RECEIPTS = ('experiment_receipt.json', 'determinism_receipt.json',
            'falsifier_receipt.json', 'regression_receipt.json',
            'experiment_profile.json', 'capture_manifest.json',
            'capture_context.json', 'capture_validation_receipt.json')

# Whitelist: literal -> true reason (load-bearing only).
WHITELIST = {
    '1': 'section numbering',
    '2': 'section numbering',
    '3': 'section numbering',
    '4': 'section numbering',
    '5': 'section numbering',
    '16': 'registry camera field count (16 named fields)',
    '26': 'biological attachment_interface count carried from A09',
    '0': 'zero counts (bond_count 0, refusals)',
    '2026': 'date year',
    '9': 'month (2026-09-30)',
    '30': 'day (2026-09-30)',
    '356': 'declared fixture tick count (Amendment A2 schedule)',
    '234': 'declared release tick (Amendment A2 schedule)',
    '61': 'declared bind tick (Amendment A2 schedule)',
    '74': 'A09 connection count (74-connection anatomy, carried context)',
}


def _receipt_corpus():
    corpus = []
    for name in RECEIPTS:
        path = HERE / name
        if path.exists():
            corpus.append(path.read_bytes().decode('utf-8'))
    return corpus


def lint_report(report_text, corpus):
    numbers = re.findall(r'(?<![\w.])-?\d+\.\d+(?:[eE][+-]?\d+)?|'
                         r'(?<![\w.])\d+(?![\w.])', report_text)
    bad = []
    for token in numbers:
        if token in WHITELIST:
            continue
        if any(token in c for c in corpus):
            continue
        bad.append(token)
    return numbers, bad


def selftest():
    """The lint must FLAG a planted defect literal (F03 review law)."""
    planted = 'The patched fixture gap is 0.123456789 m at release.'
    _, bad = lint_report(planted, [])
    return '0.123456789' in bad


def main(argv):
    if '--selftest' in argv:
        ok = selftest()
        print('selftest:', 'PASS (defect literal flagged)' if ok
              else 'FAIL (defect literal NOT flagged)')
        return 0 if ok else 1
    report = HERE / 'report.md'
    if not report.exists():
        print('report.md missing (run make_report.py first)')
        return 1
    text = report.read_bytes().decode('utf-8')
    corpus = _receipt_corpus()
    numbers, bad = lint_report(text, corpus)
    print(f'numbers checked: {len(numbers)}; untraceable: {len(bad)}')
    for token in sorted(set(bad)):
        print('UNTRACEABLE:', token)
    return 0 if not bad else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))
