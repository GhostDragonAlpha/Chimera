"""MAT2-G07 report-number lint (house pattern P2 / gate G2).

Every FLOAT literal printed in REPORT.md must trace to a bound receipt
(exact string match against the canonical receipt bytes at the printed
precision) or carry a whitelisted, load-bearing reason. Integers in prose
are counts/section numbers, not measurement claims, and are out of scope
by declaration. --selftest must flag the planted defect literals (the
stale-number class) while the clean report passes.

Run: python -B lint_report_numbers.py [--selftest]
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent

BOUND = ('experiment_receipt.json', 'experiment_trace.json',
         'determinism_receipt.json', 'falsifier_receipt.json',
         'regression_receipt.json',
         'evidence/capture/capture_manifest.json',
         'evidence/capture/capture_context.json',
         'evidence/capture/capture_validation_receipt.json',
         'evidence/capture/capture_recheck_receipt.json',
         'evidence/capture/pixel_presence.json',
         'evidence/capture/cameras.json')

# every whitelist entry: literal -> the true reason it is not a receipt
# number (load-bearing, reviewable; a whitelist entry without a real
# reason is a lint failure of this file's own review)
WHITELIST = {
    '1e-06': 'declared float32 delivery window (PREREGISTRATION section 2e '
             'dtype law)',
    '1e-09': 'declared motion/continuity/stored-energy windows '
             '(PREREGISTRATION sections 2b-2d)',
    '1e-10': 'the sealed G04 share-scaled release-bar scale N*s per kg '
             '(PREREGISTRATION section 2c)',
    '1e-12': 'declared energy-identity / losses / replay windows '
             '(PREREGISTRATION section 2a) and the timing window',
    '0.005': 'the pinned M06 DT (declared timing law; the receipts carry '
             'the same value at their own precision)',
    '9.81': 'the pinned M06 record-g (declared gravity convention; the '
            'solver module carries the constant)',
    '0.196': 'the continuous-form free-fall reference 0.5*g*t^2 quoted in '
             'the scenario rationale (the measured accounts use the exact '
             'DISCRETE closed form carried by the receipts)',
    '0.128': 'the continuous-form drop quoted for the capture snapshot '
             'tick 56 in the prereg capture plan (declared rationale '
             'text; the measured accounts are receipt-bound)',
    '0.033': 'the recorded collision impulse magnitude rounded for prose '
             '(the full-precision values are the receipt collision rows)',
    '0.0069': 'the recorded collision impulse magnitude rounded for prose '
              '(the full-precision values are the receipt collision rows)',
}

FLOAT_RE = re.compile(r'(?<![\w.])-?\d+\.\d+(?:[eE][-+]?\d+)?'
                      r'|-?\d+\.[eE][-+]?\d+'
                      r'|-?\d+(?:\.\d+)?[eE][-+]?\d+')


def collect_bound_text():
    parts = []
    for rel in BOUND:
        path = HERE / rel
        if path.exists():
            parts.append(path.read_text(encoding='utf-8'))
    return '\n'.join(parts)


def _norm(lit):
    if 'e' in lit or 'E' in lit:
        mant, _, exp = lit.partition('e' if 'e' in lit else 'E')
        return mant + 'e' + str(int(exp))
    return lit


def _in_hex_context(text, start, end):
    """True when the match is a fragment of a longer alphanumeric token
    (sha256 hex digests, identifiers) rather than a printed number."""
    head_ok = start == 0 or not (text[start - 1].isalnum()
                                 or text[start - 1] == '_')
    tail_ok = end >= len(text) or not (text[end].isalnum()
                                       or text[end] == '_')
    return not (head_ok and tail_ok)


def lint_report(report_text=None, bound_text=None):
    if report_text is None:
        report_text = (HERE / 'REPORT.md').read_text(encoding='utf-8')
    if bound_text is None:
        bound_text = collect_bound_text()
    wl = set()
    for key in WHITELIST:
        wl.add(key)
        wl.add(_norm(key))
    failures = []
    checked = 0
    for m in FLOAT_RE.finditer(report_text):
        lit = m.group(0)
        if _in_hex_context(report_text, m.start(), m.end()):
            continue
        norm = _norm(lit)
        checked += 1
        if norm in bound_text or lit in bound_text:
            continue
        if norm in wl or lit in wl:
            continue
        failures.append('untraceable_number:%s' % lit)
    return {'checked': checked, 'failures': failures,
            'whitelist_size': len(WHITELIST)}


def selftest():
    """The detector must fire on planted stale numbers and pass the
    clean fixtures (the P2 selftest law)."""
    clean = lint_report('no numbers here but 0.005 and 780 are bound\n')
    assert clean['failures'] == [], clean
    planted = lint_report('the stale dt literal 0.1234567 '
                          'and the invented drift 0.4137 must fail\n')
    assert any('0.1234567' in f for f in planted['failures']), \
        planted
    assert any('0.4137' in f for f in planted['failures']), planted
    assert '1e-12' not in lint_report(
        'declared energy window 1e-12 whitelisted\n')['failures']
    return True


def main(argv):
    if '--selftest' in argv:
        ok = selftest()
        print(json.dumps({'selftest': ok,
                          'whitelist_size': len(WHITELIST)}, indent=1))
        return 0
    res = lint_report()
    print(json.dumps(res, indent=1))
    if res['failures']:
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
