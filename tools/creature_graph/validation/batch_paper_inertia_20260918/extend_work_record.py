"""Rule 0: extend work.creature.macaque_whole_body_sources with the
PAPER-TABLE-INERTIA-INTAKE admission record BEFORE the batch apply
(append-only, idempotent: a second run with identical content writes nothing).

Run:  python -B tools/creature_graph/validation/batch_paper_inertia_20260918/extend_work_record.py
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LANE = HERE.parents[3]
PROGRAM = LANE / 'tools' / 'creature_graph' / 'data' / 'authored' / 'project_program.json'
WORK_ID = 'work.creature.macaque_whole_body_sources'
STAMP = 'admission_20260918_paper_table_inertial'

RECORD = {
    'stamp': STAMP,
    'lane': 'PAPER-TABLE-INERTIA-INTAKE (thread 4, 2026-09-18)',
    'kind': 'R3-adjacent paper-table intake, NOT the Ogihara model release '
            '(the model itself stays ON_REQUEST per the banked dossier)',
    'statement': 'Oku, Ide & Ogihara 2021 (Commun Biol 4:1831, DOI '
                 '10.1038/s42003-021-01831-w) Table 1 "Dimensions and inertial '
                 'parameters of the limb segments" (single adult male Macaca '
                 'fuscata cadaver, Ogihara 2009 lineage) is admitted through the '
                 'batch membrane as 20 property_assertion records (one per '
                 'segment x quantity: mass kg, length m, COM fraction, moment of '
                 'inertia kg*m2 for HAT/thigh/shank/foot/phalanges) plus one '
                 'table-summary record (implied whole-body mass 9.111 kg), under '
                 'the paper-table class contract batch.property.paper_table_inertial.',
    'prediction': 'Every banked value matches the live page digit-for-digit (one '
                  'recorded normalization: exponent case, U+2212, zero padding); '
                  'the count identity closes fetched == admitted + quarantined + '
                  'conflicts at 21 == 21 + 0 + 0; a corrupted cell quarantines '
                  'exactly its segment row (and the dependent summary) and refuses '
                  'the batch; a second full run creates zero objects and reproduces '
                  'the graph hash byte-identically.',
    'falsifiers': {
        'corrupted_table_value': 'one digit altered in the pinned table XML must '
                                 'quarantine exactly that segment row with '
                                 'digit_mismatch (and the dependent summary), close '
                                 'the count identity, and refuse the batch',
        'count_identity': 'fetched == admitted + quarantined + conflicts, asserted '
                          'per connector run',
        'idempotent_apply': 're-running the batch apply against the rebuilt graph '
                            'must be a no-op (same hash, no new identities)',
    },
    'closures_derived_before_admission': {
        'mass_sum': '5 published masses sum to 9.111 kg = the implied whole-body '
                    'mass; rounding tolerance +/-0.0025 kg (5 x 0.0005 kg at the '
                    'table\'s stated 0.001 kg precision); whole-body mass is not '
                    'published by the table',
        'dimensional': 'units kg / m / dimensionless fraction / kg*m2 with '
                       'per-quantity envelopes derived and enforced per record',
        'plausibility': 'implied mass 9.111 kg sits INSIDE the declared +/-10% '
                        'envelope around the PanTHERIA 1.0 Macaca fuscata species '
                        'mean (10.11476 kg, pinned ECOL_90_184.zip) at -9.92%, '
                        'margin 0.0077160 kg -- tight; comparison only, never '
                        'fused or scaled',
    },
    'not_implemented': [
        'forelimbs are folded into HAT in this table: structural gap of the '
        'source, recorded on every record, never patched',
        'whole-body mass not published; implied mass is the five-segment sum, '
        '~1 kg below the species mean (open specimen-coverage question)',
        'single cadaver: no population variance, no per-segment uncertainty '
        'columns',
        'inertia axis basis is "about the COM" per the table footnote; axial vs '
        'transverse axis distinction not published',
        'no bilateral pairing: the table is single-limb/agnostic',
    ],
    'provenance': {
        'pinned_artifact': 'tools/science_funnel/data/oku_paper_table/'
                           'PMC7940622_fulltext.xml',
        'artifact_sha256': 'fcf9fff5df51f6608724039726575dd41ca32e7a026824d3564e91803b55131d',
        'route': 'EuropePMC fullTextXML (PMC version of record); nature.com/'
                 'tables/1 refuses non-browser fetchers (recorded)',
        'license': 'CC BY 4.0, sentence quoted verbatim from the pinned page and '
                   'carried on every record',
        'verification': 'tools/creature_graph/validation/'
                        'batch_paper_inertia_20260918/verification.json (verdict '
                        'CLOSED, 20/20 cells MATCH)',
        'closures': 'tools/creature_graph/validation/'
                    'batch_paper_inertia_20260918/closures.json',
    },
    'classification': 'Admission record banked before the batch apply; not a '
                      'claim of runtime readiness.',
}


def main():
    raw = PROGRAM.read_bytes().decode('utf-8-sig')
    program = json.loads(raw)
    work = next((obj for obj in program['objects'] if obj.get('id') == WORK_ID),
                None)
    if work is None:
        print('REFUSAL: work record not found:', WORK_ID)
        return 2
    physical = work.setdefault('physical', {})
    observation = physical.setdefault('observation', {})
    existing = observation.get('paper_table_admissions', [])
    for prior in existing:
        if prior.get('stamp') == STAMP:
            if prior == RECORD:
                print('idempotent: admission record already present, no write')
                return 0
            print('REFUSAL: stamp exists with different content:', STAMP)
            return 2
    existing.append(RECORD)
    observation['paper_table_admissions'] = existing
    out = (json.dumps(program, ensure_ascii=False, indent=1) + '\n').encode()
    PROGRAM.write_bytes(out)
    print('extended', WORK_ID, 'with', STAMP,
          '(program bytes:', len(out), ')')
    return 0


if __name__ == '__main__':
    sys.exit(main())
