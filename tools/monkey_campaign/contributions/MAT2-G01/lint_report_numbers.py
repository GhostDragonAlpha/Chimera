"""MAT2-G01 report-number lint (house standard P2/G2, canonical form).

A generated report may contain NO numeric literal that is not traceable to a
bound artifact at the literal's printed precision (half unit of the last
stated digit, plus a 1e-15 relative floor covering float-repr last-ulp drift),
or an exact substring of a bound artifact, or a whitelist entry with an
honest, load-bearing reason.

Bound artifacts: the receipts and PREREGISTRATION.md (the report is GENERATED
from these; the lint proves it).

Run:  python -B lint_report_numbers.py            (exit 0 = all traceable)
      python -B lint_report_numbers.py --selftest (proves the detector still
                                                   flags planted defects)
"""
from __future__ import annotations

import json
import math
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent

ARTIFACT_PATHS = [
    'feasibility_receipt.json',
    'feasibility_receipt_rerun2.json',
    'falsifier_receipt.json',
    'checks_accounting.json',
    'PREREGISTRATION.md',
]

REPORT = 'REPORT.md'

NUMBER_RE = re.compile(r'(?<![\w.])(-?\d+\.\d+(?:[eE][+-]?\d+)?|-?\d+)(?![\w.])')

# Load-bearing whitelist: literal -> honest reason (kept minimal; every entry
# must survive review).
WHITELIST = {
    '0': 'zero in prose contexts (zero external moment, zero skipped); traced to the '
         'receipt demonstrated-case moment and the suite skip count',
    '1': 'singleton counts in prose (one derivation, one receipt identity); traced to '
         'single-channel case rows and the single determinism unit',
    '2': 'the two lawful mass systems (PREREGISTRATION-frozen vocabulary) and the '
         'n=2 case column',
    '3': 'the n=3 case column and section numbering',
    '4': 'the four falsifier arms (PREREGISTRATION section 8) and section numbering',
    '5': 'the five supported fingertips (A09 grasp endpoints) and section numbering',
    '10': 'the ten named variables (PREREGISTRATION section 7.5) and section numbering',
    '12': 'the 12-gate batch harness (CARD_STARTER v3) and the 12 case-table rows',
    '17': 'section numbering',
    '24': 'the 24/24 waypoint refusals (B07 sealed counts; prereg-carried)',
}


def artifact_numbers() -> set[float]:
    values: set[float] = set()
    for name in ARTIFACT_PATHS:
        p = HERE / name
        if not p.exists():
            if name == 'checks_accounting.json':
                # written by make_report between the provisional and final
                # report passes; the FINAL report lint (gates) always sees it.
                print('note: checks_accounting.json not present yet '
                      '(pre-report bootstrap pass)')
                continue
            raise SystemExit(f'Refusal artifact_missing: {name}')
        text = p.read_text(encoding='utf-8', errors='strict')
        for tok in NUMBER_RE.findall(text):
            try:
                values.add(float(tok))
            except ValueError:
                continue
        if name.endswith('.json'):
            def walk(o):
                if isinstance(o, bool):
                    return
                if isinstance(o, (int, float)):
                    values.add(float(o))
                elif isinstance(o, dict):
                    for v in o.values():
                        walk(v)
                elif isinstance(o, list):
                    for v in o:
                        walk(v)
            walk(json.loads(text))
    return values


def parse_report_numbers(text: str):
    found = []
    for m in NUMBER_RE.finditer(text):
        tok = m.group(1)
        try:
            value = float(tok)
        except ValueError:
            continue
        if math.isnan(value) or math.isinf(value):
            continue
        found.append((tok, value, m.start()))
    return found


def traceable(value: float, artifacts: set[float]) -> bool:
    for a in artifacts:
        if a == value:
            return True
        digits = len(repr(value).split('.')[-1]) if '.' in repr(value) else 0
        if 'e' in repr(value) or 'E' in repr(value):
            half = abs(value) * 1e-15 + 1e-315
        else:
            half = 0.5 * (10 ** -digits)
        floor = max(abs(value) * 1e-15, 1e-315)
        if abs(a - value) <= max(half, floor):
            return True
        if a != 0 and value != 0 and abs(abs(a - value)) <= floor:
            return True
    return False


def run_lint() -> list[str]:
    artifacts = artifact_numbers()
    text = (HERE / REPORT).read_text(encoding='utf-8')
    problems = []
    for tok, value, pos in parse_report_numbers(text):
        if tok in WHITELIST:
            continue
        if value == int(value) and str(int(value)) in WHITELIST and '.' not in tok:
            continue
        if traceable(value, artifacts):
            continue
        line = text.count('\n', 0, pos) + 1
        problems.append(f'{REPORT}:{line}: untraceable numeric literal {tok}')
    return problems


def selftest() -> int:
    """Prove the detector still flags the original defect literals."""
    artifacts = artifact_numbers()
    planted = ['123.456', '9999.0', '0.777']
    undetected = []
    for tok in planted:
        if not (tok in WHITELIST or traceable(float(tok), artifacts)):
            continue
        undetected.append(tok)
    if undetected:
        print(f'SELFTEST FAIL: planted defects not flagged: {undetected}')
        return 1
    print('SELFTEST OK: planted defect literals 123.456 / 9999.0 / 0.777 are all flagged')
    return 0


def main(argv) -> int:
    if '--selftest' in argv:
        return selftest()
    problems = run_lint()
    if problems:
        print('LINT FAIL:')
        for p in problems:
            print(' ', p)
        return 1
    print('LINT PASS: every numeric literal in REPORT.md traces to a bound artifact '
          'at printed precision or carries a whitelisted load-bearing reason')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
