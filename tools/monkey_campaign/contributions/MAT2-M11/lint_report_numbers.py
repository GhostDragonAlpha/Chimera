"""MAT2-M11 report-numbers lint (P2, B05/M03/M10 heritage): every numeric
literal in report.md must be traceable to a bound artifact at its printed
precision (half a unit of the last printed digit + a 1e-15 relative
floor), appear as an exact substring of a bound artifact, or be a
whitelisted entry with an honest, load-bearing reason. --selftest proves
the lint still flags the original defect literals.

Receipt classes bound here (the m11 family; extended from the P2/M10
corpus in the same commit as the receipt-semantics change):
  experiment_receipt.json  chimera.m11.experiment_receipt.v1
  falsifier_receipt.json   chimera.m11.falsifier_receipt.v1
  determinism_receipt.json chimera.m11.determinism_receipt.v1
  regression_receipt.json  chimera.m11.regression_receipt.v1
  capture_validation_receipt.json (validator receipt)
  capture/evidence/cameras.json   (capture gate evidence)

Run:  python -B lint_report_numbers.py          (exit 0 = all traceable)
      python -B lint_report_numbers.py --selftest
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPORT = HERE / 'report.md'

ARTIFACT_PATHS = [
    HERE / 'experiment_receipt.json',
    HERE / 'experiment_trace.json',
    HERE / 'falsifier_receipt.json',
    HERE / 'determinism_receipt.json',
    HERE / 'regression_receipt.json',
    HERE / 'capture_validation_receipt.json',
    HERE / 'capture' / 'evidence' / 'cameras.json',
    HERE / 'PREREGISTRATION.md',
    HERE / 'capture_context.json',
    HERE / 'report_derived_values.json',
    HERE / 'evidence_anchors.json',
]

WHITELIST = {
    '5000': 'declared source limit Pa (prereg constant)',
    '0.001': 'declared source flow limit (prereg constant)',
    '1e-9': 'declared traction-ratio / motion-audit windows (prereg WIN)',
    '0.05': 'statics window rel term (prereg section 5)',
    '2': 'FB5 boost x2.0 (declared tamper gain)',
    '600': 'declared tie stiffness N/m (prereg constant)',
    '1e-3': 'release bite window m (prereg WIN) / X4 recovery (A2)',
    '1e-12': 'A06 site->world transform assertion (Amendment A1)',
    '1.0e-3': 'X4 recovery window m (A2 re-derivation)',
    '2.0e-3': 'X8 settled floor J (A2 re-derivation)',
    '1e-4': 'X5 distal landing window m (A3)',
    '1.01': 'FB6 synthetic stand-in factor (prereg FB6)',
    '1.43': 'X8 floor derivation factor (A2)',
    '1.9': 'X4 recovery window derivation factor (A2)',
    '0.05': 'X5/X8 window rel term',
    '960': 'sheet width px',
    '540': 'sheet height px',
    '18': 'video frame count (9 ticks x 2 sheets)',
    '16': 'registry camera fields',
    '1000': 'frozen work pressure Pa (A1)',
    '1500': 'total tick count (frozen schedule)',
    '450': 'declared release tick (prereg section 4)',
    '0.010': 'declared foot inertial mass kg (A1)',
    '5.0e-3': 'declared foot/bone contact radius m (A2)',
    '0.01': 'declared chain rest gap m (A2)',
    '3': 'viewport grid count markers in layout text',
    '4': 'chain tie count',
    '8': 'B05 port count',
    '1': 'unresolved terminal count',
    '5': 'declared diagnostic layer count',
    '2': 'fresh deterministic runs',
    '0': 'zero-violation / zero-residual phrasing',
}

NUMBER_RE = re.compile(r'(?<![\w.])-?\d+\.\d+(?:[eE][+-]?\d+)?|'
                       r'(?<![\w.])-?\d+[eE][+-]?\d+|'
                       r'(?<![\w.\-])\d+(?![\d.\w])')


def numbers_in(text):
    out = []
    for match in NUMBER_RE.finditer(text):
        literal = match.group(0)
        before = text[max(0, match.start() - 2):match.start()]
        if re.search(r'[0-9a-f]{2}$', before):
            continue  # inside a hex digest
        out.append(literal)
    return out


def leaf_numbers(value, out):
    if isinstance(value, bool):
        return
    if isinstance(value, (int, float)):
        out.append(float(value))
    elif isinstance(value, dict):
        for v in value.values():
            leaf_numbers(v, out)
    elif isinstance(value, list):
        for v in value:
            leaf_numbers(v, out)


def printed_precision_ok(literal, values):
    try:
        number = float(literal)
    except ValueError:
        return False
    if 'e' in literal or 'E' in literal:
        decimals = 0
        mantissa = re.split('[eE]', literal)[0]
        if '.' in mantissa:
            decimals = len(mantissa.split('.')[1])
    elif '.' in literal:
        decimals = len(literal.split('.')[1])
    else:
        decimals = 0
    tol = max(0.5 * (10.0 ** -decimals), abs(number) * 1e-15, 1e-300)
    return any(abs(number - v) <= tol for v in values)


def check_text(text, artifact_text, artifact_values, whitelist=WHITELIST):
    defects = []
    for literal in numbers_in(text):
        if literal in whitelist:
            continue
        if literal in artifact_text:
            continue
        if printed_precision_ok(literal, artifact_values):
            continue
        defects.append(literal)
    return defects


def collect_artifacts():
    artifact_text = '\n'.join(
        p.read_text(encoding='utf-8', errors='replace')
        for p in ARTIFACT_PATHS if p.exists())
    values = []
    for p in ARTIFACT_PATHS:
        if p.exists() and p.suffix == '.json':
            try:
                leaf_numbers(json.loads(p.read_text(encoding='utf-8')),
                             values)
            except Exception:
                pass
    return artifact_text, values


def main(argv):
    artifact_text, artifact_values = collect_artifacts()
    if '--selftest' in argv:
        canary = ('the phantom radius is 4.766e-02 m and the stale gap is '
                  '44.7 mm; efficiency 0.7771 is planted.')
        defects = check_text(canary, artifact_text, artifact_values)
        for planted in ('4.766e-02', '44.7', '0.7771'):
            assert any(planted in d for d in defects), \
                'selftest: planted literal not flagged: ' + planted
        print('selftest: planted defect literals flagged (%d defects)' %
              len(defects))
        return 0
    text = REPORT.read_text(encoding='utf-8')
    defects = check_text(text, artifact_text, artifact_values)
    if defects:
        print('LINT FAIL: %d untraceable numeric literals:' % len(defects))
        for d in defects:
            print('  -', d)
        return 1
    print('LINT OK: every numeric literal in report.md is traceable to a '
          'bound artifact at its printed precision or whitelisted with '
          'reason (%d whitelist entries)' % len(WHITELIST))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
