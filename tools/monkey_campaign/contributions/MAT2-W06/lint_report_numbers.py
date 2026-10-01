"""MAT2-W06 report-number lint (house standard P2, B05 canonical form).

A generated report may contain NO numeric literal that is not traceable to a
bound artifact at the literal's printed precision (half unit of the last
stated digit, plus a 1e-15 relative floor that only covers float-repr
last-ulp drift), or an exact substring of a bound artifact, or a whitelist
entry with an honest, load-bearing reason.

Bound artifacts: this card's receipts + capture manifest + checks receipt +
prereg, AND the pinned upstream artifacts (the sealed W05 receipts, runbook
and prereg at their merged in-tree paths) — the report is GENERATED from
these; the lint proves it.

Run:  python -B lint_report_numbers.py            (exit 0 = all traceable)
      python -B lint_report_numbers.py --selftest (proves the detector still
                                                   flags planted defects)
"""
from __future__ import annotations

import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
UPSTREAM = HERE.parent / "MAT2-W05"

LOCAL_ARTIFACT_PATHS = [
    'PREREGISTRATION.md',
    'checks_receipt.json',
    'receipts/input_pins.json',
    'receipts/evaluation_summary.json',
    'receipts/seed_20260919_evaluation.json',
    'receipts/seed_20260920_evaluation.json',
    'receipts/seed_20260921_evaluation.json',
    'capture/capture_manifest.json',
    'capture/capture_context.json',
    'capture/capture_validation_receipt.json',
]

UPSTREAM_ARTIFACT_PATHS = [
    'runbook.json',
    'w05_freeze_fill.json',
    'PREREGISTRATION.md',
    'PREREGISTRATION-ADDENDUM-1.md',
    'checks_receipt.json',
    'receipts/baseline_receipt.json',
    'receipts/recipe_equivalence_receipt.json',
    'receipts/seed_20260919_receipt.json',
    'receipts/seed_20260920_receipt.json',
    'receipts/seed_20260921_receipt.json',
    'receipts/heldout_receipt.json',
    'receipts/deploy_check_receipt.json',
    'trained/trained_policy_manifest.json',
]

# Load-bearing whitelist: literal -> honest reason (kept minimal; each entry
# must survive review).
WHITELIST = {
    '0': 'zero used in prose contexts (0 runs of any kind by this card, 0 '
         'termination codes, 0 skipped); traced to the receipts',
    '1': 'singleton counts in prose (one prereg, one upstream runbook); '
         'traced to receipt counts',
    '2': 'counts in prose (two capture modes, the W04 merge reference); '
         'traced to the receipts',
    '3': 'counts in prose (three seeds, three deploy decisions, three '
         'record-space views); traced to the receipts',
    '4': 'counts in prose (four predictions E1-E4); traced to the summary',
    '5': 'counts in prose (five falsifier classes mapped); traced to the '
         'summary falsifier_mapping',
    '6': 'counts in prose (six hard gates, six held-out cells); traced to '
         'runbook.json / heldout_receipt',
    '9': 'the 9 held-out matrix cells (heldout_receipt cells)',
    '12': 'the 12-char sha prefixes in tables (rendering convention); the '
          'full shas are pinned in the receipts',
    '16': 'the 16-field camera vocabulary per capture row',
    '21': 'the 21 pinned inputs (pin verifier pins_total)',
    '100': 'the first/last 100-iteration fitness windows (frozen upstream)',
    '295': 'the MAT2-W04 merge PR number (registry identity in prose)',
    '297': 'the MAT2-W05 merge PR number (registry identity in prose)',
}


def _artifact_texts():
    texts = {}
    for name in LOCAL_ARTIFACT_PATHS:
        path = HERE / name
        if path.exists():
            texts[name] = path.read_text(encoding='utf-8')
    for name in UPSTREAM_ARTIFACT_PATHS:
        path = UPSTREAM / name
        if path.exists():
            texts['upstream/' + name] = path.read_text(encoding='utf-8')
    return texts


def _half_unit(token):
    if 'e' in token or 'E' in token:
        return 0.0
    if '.' in token:
        decimals = len(token.split('.')[1])
        return 0.5 * (10 ** -decimals)
    return 0.5


NUMBER_RE = re.compile(
    r'(?<![\w.=/-])(-?\d+\.\d+(?:[eE][+-]?\d+)?|-?\d+)(?![\w.=])')


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
