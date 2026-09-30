"""MAT2-M09 report-numbers lint (P2 heritage).

Every numeric literal in report.md must be traceable, at its printed
precision, to at least one bound artifact on disk (experiment_receipt.json,
determinism_receipt.json, falsifier_receipt.json, regression_receipt.json,
capture_validation_receipt.json, experiment_trace.json, capture_manifest,
capture_context, PREREGISTRATION.md, checks identity) as an exact
substring of the artifact's raw text — or be whitelisted with a
load-bearing reason. --selftest proves the lint still flags the original
defect literals (planted phantom/stale numbers).
Run: python -B lint_report_numbers.py [--selftest]
"""
from __future__ import annotations

import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent

ARTIFACTS = ['experiment_receipt.json', 'determinism_receipt.json',
             'falsifier_receipt.json', 'regression_receipt.json',
             'capture_validation_receipt.json', 'experiment_trace.json',
             'capture_manifest.json', 'capture_context.json',
             'PREREGISTRATION.md']

WHITELIST = {
    '90': 'run length in ticks (declared constant, DECLARATION.ticks)',
    '85': 'release tick (declared constant, DECLARATION.release_tick)',
    '84': 'held tick (Amendment A1 schedule)',
    '74': 'end of press window (Amendment A1 schedule)',
    '66': 'measured first joint contact tick (receipts)',
    '45': 'bind tick (declared constant, DECLARATION.bind_tick)',
    '1': 'unity (windows floors, single viewport)',
    '2': 'pair rows / two elements / two bones',
    '3': 'restraint count scale / camera columns',
    '4': 'camera columns / substeps-per-tick scale reference',
    '5': 'five diagnostic layers',
    '6': 'view count in the capture manifest',
    '10': 'area ratio numerator (unequal head-face triangles)',
    '7': 'area ratio denominator (unequal head-face triangles)',
    '0': 'zero (bitwise identities, exits)',
    '0.0': 'bitwise zero forces/energies (T4)',
    '1e-12': 'momentum ledger bound (declared)',
    '1e-18': 'release identity window (declared)',
    '1e-15': 'restraint recompute window (declared)',
    '1e-9': 'scalar agreement window (declared, X3 frozen)',
    '0.015': 'release displacement window (Amendment A1)',
    '4.0': 'max speed bound m/s (declared T7)',
    '0.010': 'T10-era displacement reference retained from the frozen '
             'preregistration text',
    '31': 'frozen T7 window bound (bone_a ground contact)',
    '24': 'frozen T7 window bound (both bones)',
    '17': 'frozen T7 window bound (bone_b ground contact)',
    '46': 'frozen T7 window bound (joint contact) + doc tick',
    '300': 'tick rate denominator (300 Hz pin)',
    '20260929': 'date in artifact identifiers',
    '16': 'sha display width marker in the report (hex truncation)',
}

NUM_RE = re.compile(r'(?<![\w.])-?\d+\.\d+(?:[eE][+-]?\d+)?'
                    r'|-?\d+[eE][+-]?\d+'
                    r'|(?<![\w.])\d+(?![\w.])')


def check_text(text, corpus, extra_banned=()):
    defects = []
    for m in NUM_RE.finditer(text):
        token = m.group(0).lstrip('-')
        if token in WHITELIST:
            continue
        if any(token in doc for doc in corpus):
            continue
        if extra_banned and any(token == b for b in extra_banned):
            defects.append(token)
            continue
        defects.append(token)
    return defects


def main(argv):
    report = (HERE / 'report.md')
    require = report.exists(), 'm09_lint_report_missing'
    text = report.read_text(encoding='utf-8')
    corpus = []
    for name in ARTIFACTS:
        p = HERE / name
        if p.exists():
            corpus.append(p.read_text(encoding='utf-8', errors='replace'))
    defects = check_text(text, corpus)
    if '--selftest' in argv:
        planted = text + '\nphantom radius r = 4.766e-02 m and a stale '
        planted += 'gap of 44.7 mm that exists in no artifact.\n'
        d2 = check_text(planted, corpus, extra_banned=('4.766e-02', '44.7'))
        flagged = '4.766e-02' in d2 and '44.7' in d2
        print('selftest flagged planted literals:', flagged)
        if not flagged:
            print('SELFTEST FAILED', d2)
            return 2
        real = [d for d in d2 if d not in ('4.766e-02', '44.7')]
        print('non-planted defects in selftest run:', real)
        return 0
    print('untraceable numeric literals:', defects)
    if defects:
        return 1
    print('lint OK: every number traces to a bound artifact at its '
          'printed precision or a load-bearing whitelist entry')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
