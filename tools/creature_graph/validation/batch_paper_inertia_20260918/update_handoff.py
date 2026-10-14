"""S7: append this lane's report to doc.handoff.zcode in the authored program
(append-only, idempotent: a second run with identical content writes nothing).

Run:  python -B tools/creature_graph/validation/batch_paper_inertia_20260918/update_handoff.py
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LANE = HERE.parents[3]
PROGRAM = LANE / 'tools' / 'creature_graph' / 'data' / 'authored' / 'project_program.json'
DOC_ID = 'doc.handoff.zcode'
STAMP = 'lane_report_20260918_paper_table_inertia'

REPORT = {
    'stamp': STAMP,
    'lane': 'PAPER-TABLE-INERTIA-INTAKE (thread 4, branch '
            'lane/paper-inertia-20260918, 2026-09-18)',
    'changed_behavior': 'Oku, Ide & Ogihara 2021 Table 1 (Macaca fuscata segment '
                        'inertial parameters, single adult male cadaver, Ogihara '
                        '2009 lineage) is now admitted through the batch membrane: '
                        'connector oku_paper_table, adapter oku_paper_table, class '
                        'contract batch.property.paper_table_inertial (paper-table '
                        'variant authored because the shared measurement class '
                        'cannot express a mixed kg/m/dimensionless/kg*m2 source '
                        'without re-gating other lanes).',
    'counts': '21 property_assertion records (20 segment x quantity + 1 '
              'table-summary implied whole-body mass 9.111 kg), 0 quarantined, '
              'count identity closed; every banked value verified digit-for-digit '
              'against the live page (PMC version of record; nature.com serves a '
              'JS client-challenge to non-browser fetchers, recorded).',
    'candidate': 'bundle 1ad2c92f0b1e (content-addressed), store objects_added 0 '
                 'on re-apply, idempotent replay no-op, graphify round-trip HONEST '
                 '(7 checks), receipt tools/science_funnel/validation/'
                 'batch_paper_inertia_20260918/receipt.json',
    'closures': 'mass sum 9.111 kg +/-0.0025 kg (table rounding); implied mass '
                'INSIDE the declared +/-10% PanTHERIA Macaca fuscata envelope '
                '(mean 10.11476 kg) at -9.92%, margin 0.0077160 kg -- tight, '
                'recorded as an open specimen-coverage question; comparison only, '
                'never fused',
    'not_implemented': 'forelimbs folded into HAT (structural, on every record); '
                       'whole-body mass implied not published; single cadaver, no '
                       'population variance; inertia axis basis "about the COM" '
                       'per footnote, axial vs transverse not published',
    'qualified_scope': 'paper-table intake and mechanical batch proof only; no '
                       'runtime, no organism claim, Ogihara model release remains '
                       'ON_REQUEST (this lane is R3-adjacent intake, not the '
                       'release)',
    'blockers': 'none for this lane; host contention with parallel lanes required '
                'detached runs (integrator timeout directive followed)',
    'next_executable': 'reductions over the admitted inertias (segment sum -> '
                       'candidate whole-body parameters) are NOT done and are the '
                       'natural next lane; free-root balance work follows '
                       'whole-body inertias per the banked proposal',
    'unit_tests': 'tools/science_funnel/tests/test_batch_paper.py (11 tests) green',
}


def main():
    raw = PROGRAM.read_bytes().decode('utf-8-sig')
    program = json.loads(raw)
    doc = next((o for o in program['objects'] if o.get('id') == DOC_ID), None)
    if doc is None:
        print('REFUSAL: doc not found:', DOC_ID)
        return 2
    observation = doc.setdefault('physical', {}).setdefault('observation', {})
    lane_reports = observation.setdefault('lane_reports', [])
    for prior in lane_reports:
        if prior.get('stamp') == STAMP:
            if prior == REPORT:
                print('idempotent: lane report already present, no write')
                return 0
            print('REFUSAL: stamp exists with different content:', STAMP)
            return 2
    lane_reports.append(REPORT)
    out = (json.dumps(program, ensure_ascii=False, indent=1) + '\n').encode()
    PROGRAM.write_bytes(out)
    print('appended lane report to', DOC_ID, '(program bytes:', len(out), ')')
    return 0


if __name__ == '__main__':
    sys.exit(main())
