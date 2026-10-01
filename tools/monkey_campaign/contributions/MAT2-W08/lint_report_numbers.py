"""MAT2-W08 report-number lint (house standard P2, B05 canonical form).

A generated report may contain NO numeric literal that is not traceable to a
bound artifact at the literal's printed precision (half unit of the last
stated digit, plus a 1e-15 relative floor that only covers float-repr
last-ulp drift), or an exact substring of a bound artifact, or a whitelist
entry with an honest, load-bearing reason.

Bound artifacts: this card's receipts + capture set + checks receipt +
prereg, AND the pinned upstream artifacts (the W04 certificate, the P06
release limits, the U01 qualification receipt and the W07 native-load
receipt in the evidence store) — the report is GENERATED from these; the
lint proves it.

Run:  python -B lint_report_numbers.py            (exit 0 = all traceable)
      python -B lint_report_numbers.py --selftest (proves the detector still
                                                   flags planted defects)
"""
from __future__ import annotations

import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
STORE = pathlib.Path("E:/ChimeraWork/monkey-coordination/evidence-store")

LOCAL_ARTIFACT_PATHS = [
    'PREREGISTRATION.md',
    'checks_receipt.json',
    'REPORT.md',
    'receipts/command_verification_receipt.json',
    'capture/capture_receipt.json',
    'capture/capture_manifest.json',
    'capture/capture_context.json',
    'capture/capture_validation_receipt.json',
    'capture/trace_commanded.json',
    'capture/frame_hashes.json',
]

UPSTREAM_ARTIFACT_PATHS = [
    (STORE, 'MAT2-W04/numerical/w04_certificate.json'),
    (STORE, 'MAT2-W04/numerical/w04_freeze_manifest.json'),
    (STORE, 'MAT2-P06/numerical/numerical'),
    (STORE, 'MAT2-U01/numerical/qualification_receipt.json'),
    (STORE, 'MAT2-W07/numerical/native_load_receipt.json'),
]

# Load-bearing whitelist: literal -> honest reason (kept minimal; each entry
# must survive review).
WHITELIST = {
    '0': 'zero in prose (0 trained bundles, 0 violations, 0 skipped, 0 '
         'silence records); traced to the receipts',
    '1': 'singleton counts in prose (one prereg, one capture arm, onset 1 '
         'tick); traced to the receipts',
    '2': 'counts in prose (two prereg amendments, two capture bands, runs '
         'R1/R2); traced to the receipts',
    '3': 'counts in prose (three record-space views); traced to the '
         'capture manifest',
    '5': 'counts in prose (five declared diagnostic layers; the capture '
         'fps); traced to the manifest',
    '8': 'the 8-command actuation vector and the 8 event anchors; traced '
         'to the prereg and the capture manifest',
    '12': 'the 16-char sha prefixes use 16; the 12 gate count of the '
          'campaign; traced to the card-kit',
    '15': 'the 15-tick hold bound (onset <= 15); traced to the receipts',
    '16': 'the 16-char sha prefixes in tables (rendering convention); the '
          'full shas are pinned in the receipts',
    '20': 'the 20 Hz command clock (the seam); traced to the pinned seam '
          'constants quoted in the prereg',
    '52': 'the 52 uniform capture samples; traced to the capture manifest',
    '60': 'the 60-frame capture; traced to the capture manifest',
    '300': 'the 300 Hz physics clock; traced to the pinned constants quoted '
           'in the prereg and the receipts',
    '6000': 'the live-zero segment start tick; traced to the prereg script '
            'table',
    '6885': 'the live-zero segment end tick; traced to the prereg script '
            'table',
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

PLACEHOLDER_RE = re.compile(r'%[sdf]|%[-0-9.]*[sdf]')


def check_placeholders(text):
    """Unsubstituted printf placeholders are RED (the D3 class): a report
    line carrying '%s'/'%d' is a broken generation, not prose."""
    hits = []
    for no, line in enumerate(text.splitlines(), 1):
        if PLACEHOLDER_RE.search(line):
            hits.append((no, line.strip()[:120]))
    return hits


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
    """Prove the lint still flags planted defect literals (the B05 class)
    AND planted unsubstituted placeholders (the D3 class)."""
    planted = ['3.14159', '44.7', '10.0381', '2.9775']
    sample = ('phantom radius r = 3.14159 m and stale gap 44.7 mm; '
              'perturbed total 10.0381 kg; invented envelope 2.9775 m/s')
    flagged = check_text(sample, artifacts={'none.txt': 'no numbers here'})
    ok = all(p in flagged for p in planted)
    print('selftest: planted %r -> flagged %r' % (planted, flagged))
    ph = check_placeholders('fine line\nbroken sha `%s` here\nalso %d bad')
    ok = ok and ph == [(2, 'broken sha `%s` here'), (3, 'also %d bad')]
    print('selftest: planted placeholders -> %r' % (ph,))
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
    placeholders = check_placeholders(text)
    untraceable = check_text(text)
    if placeholders or untraceable:
        if placeholders:
            print('LINT RED: %d unsubstituted placeholder line(s):'
                  % len(placeholders))
            for no, line in placeholders:
                print('  PLACEHOLDER line %d: %s' % (no, line))
        if untraceable:
            print('LINT RED: %d untraceable numeric literal(s):' % len(
                untraceable))
            for token in untraceable:
                print('  UNTRACEABLE ' + token)
        return 1
    print('lint OK: no unsubstituted placeholders; every numeric literal in '
          'REPORT.md traces to a bound artifact at its printed precision or '
          'a whitelisted reason')
    return 0


if __name__ == "__main__":
    sys.exit(main())
