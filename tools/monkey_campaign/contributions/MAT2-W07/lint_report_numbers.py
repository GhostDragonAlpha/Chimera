"""MAT2-W07 report-number lint (house standard P2, B05 canonical form).

A generated report may contain NO numeric literal that is not traceable to a
bound artifact at the literal's printed precision (half unit of the last
stated digit, plus a 1e-15 relative floor that only covers float-repr
last-ulp drift), or an exact substring of a bound artifact, or a whitelist
entry with an honest, load-bearing reason.

Bound artifacts: this card's receipts + capture set + checks receipt +
prereg, AND the pinned upstream artifacts (the sealed W06 evaluation
summary, the W04 certificate and C09 anchor re-seal in the evidence store)
— the report is GENERATED from these; the lint proves it.

Run:  python -B lint_report_numbers.py            (exit 0 = all traceable)
      python -B lint_report_numbers.py --selftest (proves the detector still
                                                   flags planted defects)
"""
from __future__ import annotations

import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
STORE_W04 = pathlib.Path("E:/ChimeraWork/monkey-coordination/evidence-store"
                         "/MAT2-W04")
UPSTREAM_W06 = HERE.parent / "MAT2-W06"
UPSTREAM_W05 = HERE.parent / "MAT2-W05"

LOCAL_ARTIFACT_PATHS = [
    'PREREGISTRATION.md',
    'checks_receipt.json',
    'receipts/native_load_receipt.json',
    'capture/load_capture_receipt.json',
    'capture/capture_manifest.json',
    'capture/capture_context.json',
    'capture/capture_validation_receipt.json',
    'capture/trace.json',
    'capture/frame_hashes.json',
]

UPSTREAM_ARTIFACT_PATHS = [
    (UPSTREAM_W06, 'receipts/evaluation_summary.json'),
    (UPSTREAM_W06, 'checks_receipt.json'),
    (UPSTREAM_W06, 'capture/replay_receipt.json'),
    (UPSTREAM_W05, 'receipts/deploy_check_receipt.json'),
    (STORE_W04, 'numerical/w04_certificate.json'),
    (STORE_W04, 'numerical/c09_anchor_reseal.json'),
    (STORE_W04, 'numerical/w04_freeze_manifest.json'),
]

# Load-bearing whitelist: literal -> honest reason (kept minimal; each entry
# must survive review).
WHITELIST = {
    '0': 'zero used in prose contexts (0 trained bundles loaded, 0 '
         'violations, 0 skipped, 0 recipe/ masked-channel/ report '
         'mismatches, falsifier classes not fired); traced to the receipts',
    '1': 'singleton counts in prose (one prereg, one capture arm, one '
         'publication commit); traced to receipt counts',
    '2': 'counts in prose (two capture modes, two deploy directions, the '
         'two NAMED_MISSING certificate prerequisites); traced to the '
         'receipts',
    '3': 'counts in prose (three certified baseline anchors, three deploy '
         'negative controls, three record-space views); traced to the '
         'receipts',
    '4': 'counts in prose (four predictions rows P1-P7 format, four '
         'N-records); traced to the receipts',
    '7': 'counts in prose (seven predictions P1-P7); traced to the report '
         'structure',
    '8': 'the 8-command actuation vector (the manifest action dim); traced '
         'to the certificate relation',
    '9': 'the 9 C09 anchor verdicts (pinned re-seal receipt); traced to '
         'c09_anchor_reseal.json',
    '11': 'the named-check count (checks_receipt tests_run)',
    '12': 'the 12-char sha prefixes in tables (rendering convention); the '
          'full shas are pinned in the receipts',
    '17': 'the 17-field camera vocabulary per capture row (the profile '
          'camera_required_fields)',
}


def _artifact_texts():
    texts = {}
    for name in LOCAL_ARTIFACT_PATHS:
        path = HERE / name
        if path.exists():
            texts[name] = path.read_text(encoding='utf-8')
    for base, name in UPSTREAM_ARTIFACT_PATHS:
        path = base / name
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
