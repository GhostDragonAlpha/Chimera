"""MAT2-D-MASSREG report-number lint (house standard P2, B05 canonical form).

A generated report may contain NO numeric literal that is not traceable to a
bound artifact at the literal's printed precision (half unit of the last
stated digit, plus a 1e-15 relative floor that only covers float-repr
last-ulp drift), or an exact substring of a bound artifact, or a whitelist
entry with an honest, load-bearing reason.

Bound artifacts: the register, the receipts, and PREREGISTRATION.md (the
report is GENERATED from these; the lint proves it).

Run:  python -B lint_report_numbers.py            (exit 0 = all traceable)
      python -B lint_report_numbers.py --selftest (proves the detector still
                                                   flags planted defects)
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent

ARTIFACT_PATHS = [
    'mass_register.json',
    'enumeration_receipt.json',
    'implied_bw_receipt.json',
    'zero_mass_delta_receipt.json',
    'determinism_receipt.json',
    'falsifier_receipt.json',
    'regression_receipt.json',
    'PREREGISTRATION.md',
]

# Load-bearing whitelist: literal -> honest reason (kept minimal; each entry
# must survive review).
WHITELIST = {
    '0': 'zero used in prose contexts (zero mass delta, zero rows); traced '
         'conceptually to the register double_count_scan zero and the '
         'declared-zero rows',
    '1': 'singleton counts in prose (one measurement, one receipt, one '
         'commit); traced to the enumeration family counts of 1',
    '2': 'the two lawful systems (PREREGISTRATION-frozen vocabulary)',
    '3': 'section numbering / the three frozen specimen classes',
    '4': 'the four falsifier arms (PREREGISTRATION section 7.4)',
    '12': 'the 12-gate batch harness (CARD_STARTER v3)',
    '17': 'truncated prose form of the pinned 17.039978509953905 kg total '
          '(the full-precision literal appears beside it from the receipt)',
    '10': 'truncated prose form of the pinned 10.038 kg scene total',
    '5': 'the five counted B03 bone regions (pinned b03 counted_set)',
    '6': 'section numbering',
    '7': 'section numbering / commit shas containing 7',
    '8': 'section numbering',
    '9': 'section numbering / nine unresolved bodies count',
    '14': 'the frozen scene.walk family count of 14 bodies',
    '15': 'the frozen scene-side family total (14 walk + 1 denominator)',
    '16': 'anchored input copies count',
    '18': 'the frozen buffy family total (9 transported + 9 unresolved)',
    '51': 'the frozen register entry count (enumeration_receipt '
          'entry_count=51)',
    '33': 'attempt id hex fragment',
    '2026': 'year in dates',
    '30': 'day-of-month in dates',
    '09': 'month in dates',
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
