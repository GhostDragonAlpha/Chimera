"""MAT2-W05 report-number lint (house standard P2, B05 canonical form).

A generated report may contain NO numeric literal that is not traceable to a
bound artifact at the literal's printed precision (half unit of the last
stated digit, plus a 1e-15 relative floor that only covers float-repr
last-ulp drift), or an exact substring of a bound artifact, or a whitelist
entry with an honest, load-bearing reason.

Bound artifacts: the receipts, the runbook, the slot fill, the preregistration
(+ addendum) — the report is GENERATED from these; the lint proves it.

Run:  python -B lint_report_numbers.py            (exit 0 = all traceable)
      python -B lint_report_numbers.py --selftest (proves the detector still
                                                   flags planted defects)
"""
from __future__ import annotations

import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent

ARTIFACT_PATHS = [
    'runbook.json',
    'w05_freeze_fill.json',
    'receipts/baseline_receipt.json',
    'receipts/recipe_equivalence_receipt.json',
    'receipts/seed_20260919_receipt.json',
    'receipts/seed_20260920_receipt.json',
    'receipts/seed_20260921_receipt.json',
    'receipts/heldout_receipt.json',
    'receipts/deploy_check_receipt.json',
    'checks_receipt.json',
    'PREREGISTRATION.md',
    'PREREGISTRATION-ADDENDUM-1.md',
]

# Load-bearing whitelist: literal -> honest reason (kept minimal; each entry
# must survive review).
WHITELIST = {
    '0': 'zero used in prose contexts (0 GPU jobs, 0 retries, 0 skipped); '
         'traced to the receipts',
    '1': 'singleton counts in prose (one runbook, one prereg, one baseline '
         'arm); traced to receipt counts',
    '2': 'counts in prose (two antithetic evaluations per iteration, two '
         'addendum-corrected pins); traced to the receipts',
    '3': 'counts in prose (three seeds, three falsifier bites, three deploy '
         'decisions); traced to the receipts',
    '4': 'counts in prose (four executor phases after the baseline); traced '
         'to the receipts',
    '5': 'counts in prose (five prereg sections cited); traced to the prereg',
    '6': 'counts in prose (six hard gates); traced to runbook.json',
    '8': 'the 8-channel action interface (runbook actions.channels)',
    '9': 'the 9 held-out matrix cells (heldout_receipt cells)',
    '15': 'the 15-tick zero-order hold (runbook decisions.hold_ticks)',
    '16': 'section numbering',
    '19': 'the 19 pinned inputs (pin verifier pins_total)',
    '20': 'the 20 Hz policy clock (runbook decisions.policy_hz)',
    '64': 'the frozen v1 observation width (projection width)',
    '80': 'the 80-field observation interface v2 (prereg section 2 D)',
    '100': 'the first/last 100-iteration fitness windows (prereg section 4 P3)',
    '300': 'the 300 Hz physics clock (runbook decisions.physics_hz)',
    '3750': 'the evaluation-window ticks (runbook decisions ticks_per_eval '
            'path)',
    '2026': 'year in dates',
    '295': 'the W04 merge PR number (registry identity in prose)',
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
    planted = ['3.14159', '44.7', '10.0381', '2.9775']
    sample = ('phantom radius r = 3.14159 m and stale gap 44.7 mm; '
              'perturbed total 10.0381 kg; invented envelope 2.9775 m/s')
    flagged = check_text(sample, artifacts={'none.txt': 'no numbers here'})
    ok = all(p in flagged for p in planted)
    print('selftest: planted %r -> flagged %r' % (planted, flagged))
    return ok and len(flagged) == len(planted)


def main():
    report = HERE / 'REPORT.md'
    if not report.exists():
        print('REFUSED: REPORT.md missing (run make_report.py first)')
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
    print('lint OK: every numeric literal in REPORT.md traces to a bound '
          'artifact at its printed precision or a whitelisted reason')
    return 0


if __name__ == '__main__':
    sys.exit(main())
