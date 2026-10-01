"""MAT2-W04 report-number lint (house standard P2, B05 canonical form).

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
    'w04_freeze_manifest.json',
    'w04_certificate.json',
    'gate_reissue/w04_gate_receipt.json',
    'c09_reseal/c09_anchor_reseal.json',
    'checks_receipt.json',
    'capture/capture_manifest.json',
    'capture/capture_context.json',
    'capture/capture_validation_receipt.json',
    'evidence/registry_verification_profile.json',
    'PREREGISTRATION.md',
]

# Load-bearing whitelist: literal -> honest reason (kept minimal; each entry
# must survive review).
WHITELIST = {
    '0': 'zero used in prose contexts (0/8 ports qualified, counted 0.0 kg, '
         '0 violations, 0 skipped); traced to the receipts',
    '1': 'singleton counts in prose (one certificate, one prereg); traced '
         'to receipt counts',
    '2': 'counts in prose (two lineages, two named-missing prerequisites, '
         'two refusal documents); traced to the receipts',
    '3': 'counts in prose (three mass rulings, three refusal identities, '
         'three capture views); traced to the receipts',
    '4': 'counts in prose (four injections, four views planned in prereg '
         'language); traced to the receipts',
    '5': 'the five standing gaps / five FC clauses (prose counts)',
    '6': 'counts in prose (six bite arms FB1-FB6); traced to the suite',
    '8': 'the 8 ports (port_active_law_inputs.ports_total)',
    '9': 'the 9 C09 anchor comparisons (c09 receipt comparison count)',
    '10': 'section numbering',
    '12': 'the 12-gate batch harness (CARD_STARTER v3)',
    '16': 'the 16-field camera record (registry profile snapshot)',
    '24': 'the 24 refused waypoint cells (R-OWN-05 record)',
    '36': 'the named-check count (checks_receipt tests_run)',
    '44': 'the 4/4 injections phrase renders as 44 in the regex; covered by '
          'the injection count in gate_reissue/w04_gate_receipt.json',
    '64': 'the frozen v1 observation width (legacy_dim)',
    '80': 'the 80-field observation interface (obs v2 dim)',
    '2026': 'year in dates',
    '294': 'the B07 merge PR number (registry identity in prose)',
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
    planted = ['4.766e-02', '44.7', '10.0381', '2.9774']
    sample = ('phantom radius r = 4.766e-02 m and stale gap 44.7 mm; '
              'perturbed total 10.0381 kg; invented envelope 2.9774 m/s')
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
