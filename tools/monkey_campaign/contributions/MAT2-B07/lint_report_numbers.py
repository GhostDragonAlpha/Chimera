"""MAT2-B07 report-number lint (house standard P2, B05 canonical form).

A generated report may contain NO numeric literal that is not traceable to a
bound artifact at the literal's printed precision (half unit of the last
stated digit, plus a 1e-15 relative floor that only covers float-repr
last-ulp drift), or an exact substring of a bound artifact, or a whitelist
entry with an honest, load-bearing reason.

Bound artifacts: the receipts and PREREGISTRATION.md (the report is
GENERATED from these; the lint proves it).

Run:  python -B lint_report_numbers.py            (exit 0 = all traceable)
      python -B lint_report_numbers.py --selftest (proves the detector still
                                                   flags planted defects)
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent

ARTIFACT_PATHS = [
    'ownership_mappings.json',
    'frame_bindings.json',
    'adoption_record.json',
    'c09_anchor_rerun/c09_anchor_rerun.json',
    'capture/capture_receipt.json',
    'checks_receipt.json',
    'PREREGISTRATION.md',
]

# Load-bearing whitelist: literal -> honest reason (kept minimal; each entry
# must survive review).
WHITELIST = {
    '0': 'zero used in prose contexts (admitted mass 0.0, refused '
         'certificate, no skips); traced to the receipts',
    '1': 'singleton counts in prose (one receipt, one record class); '
         'traced to receipt counts of 1',
    '2': 'counts in prose (2 refusal rows, decode pair); traced to the '
         'per-row table refusal_stands rows and decode checks',
    '3': 'counts in prose (3 work-closed rows, 3 views); traced to the '
         'closure table classes and capture rows',
    '4': 'counts in prose (4 satisfied rows / 4 binding rows / 4 TC-12 '
         'prerequisites); traced to the receipts',
    '8': 'the 8-item authorization package (adoption_record '
         'authorization_package length)',
    '10': 'section numbering',
    '12': 'the 12-gate batch harness (CARD_STARTER v3)',
    '14': 'the sealed B06 receipt row count / the 14 hand mapping records '
          '(both traced to receipts)',
    '16': 'the 16-field camera record (registry profile snapshot in the '
          'capture receipt)',
    '31': 'the 31 forearm correspondence records (ownership_mappings '
          'counts.forearm_records)',
    '2026': 'year in dates',
    '6': 'capture view rows (capture receipt rows=6)',
    '24': 'capture frame count (capture receipt frame_count=24)',
    '9': 'the C09 anchor comparison count (c09 receipt 9 anchors)',
}

NUMBER_RE = re.compile(
    r'(?<![\w.=/-])(-?\d+\.\d+(?:[eE][+-]?\d+)?|-?\d+)(?![\w.=])')


def _artifact_texts():
    texts = {}
    for name in ARTIFACT_PATHS:
        path = HERE / name
        if path.exists():
            texts[name] = path.read_text(encoding='utf-8')
    return texts


def _half_unit(token):
    if 'e' in token or 'E' in token:
        return 0.0
    if '.' in token:
        decimals = len(token.split('.')[1])
        return 0.5 * (10 ** -decimals)
    return 0.5


def check_text(text, artifacts=None):
    """Return the list of untraceable numeric literals."""
    texts = artifacts if artifacts is not None else _artifact_texts()
    values_by_text = []
    for name, body in texts.items():
        values_by_text.append((name, [float(m.group(1)) for m in
                                      NUMBER_RE.finditer(body)]))
    untraceable = []
    for m in NUMBER_RE.finditer(text):
        token = m.group(1)
        if token in WHITELIST:
            continue
        traced = False
        # exact substring in a bound artifact (same printed precision)
        for name, body in texts.items():
            if re.search(r'(?<![\w.])' + re.escape(token) + r'(?![\w.])',
                         body):
                traced = True
                break
        if traced:
            continue
        # printed-precision match against a parsed artifact value
        value = float(token)
        tol = _half_unit(token)
        for name, values in values_by_text:
            for candidate in values:
                if abs(candidate - value) <= max(tol, 1e-15
                                                 * max(1.0, abs(value))):
                    traced = True
                    break
            if traced:
                break
        if not traced:
            untraceable.append(token)
    return untraceable


def selftest():
    """Prove the lint still flags planted defect literals (the B05 class)."""
    planted = ['4.766e-02', '44.7', '10.0381']
    sample = ('phantom radius r = 4.766e-02 m and stale gap 44.7 mm; '
              'perturbed total 10.0381 kg')
    flagged = check_text(sample, artifacts={'none.txt': 'no numbers here'})
    ok = all(p in flagged for p in planted)
    print('selftest: planted %r -> flagged %r' % (planted, flagged))
    return ok and len(flagged) == len(planted)


def main():
    report = HERE / 'report.md'
    if not report.exists():
        print('REFUSED: report.md missing (run make_report.py first)')
        return 2
    if '--selftest' in sys.argv:
        if not selftest():
            print('SELFTEST FAILED')
            return 1
        print('selftest OK: detector still flags planted defect literals')
    text = report.read_text(encoding='utf-8')
    untraceable = check_text(text)
    if untraceable:
        print('LINT RED: %d untraceable numeric literal(s):' % len(
            untraceable))
        for token in untraceable:
            print('  UNTRACEABLE ' + token)
        return 1
    print('lint OK: every numeric literal in report.md traces to a bound '
          'artifact at its printed precision or a whitelisted reason')
    return 0


if __name__ == '__main__':
    sys.exit(main())
