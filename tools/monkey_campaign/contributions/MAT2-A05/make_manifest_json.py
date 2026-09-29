"""Generate mutation_manifest.json (machine-readable mirror of MUTATION_MANIFEST.md).

Every hash is computed from the files on disk at run time; nothing hand-typed.
Read-only over the pinned sources. Writes only into this directory.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODEL = 'macaque_arm_hand_mutation'


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    st = json.loads((HERE / 'mutation_structure.json').read_text(encoding='utf-8'))
    receipt = json.loads((HERE / 'validation_receipt.json').read_text(encoding='utf-8'))
    al = st['allometry']
    manifest = {
        'schema': 'chimera.mutation_manifest.v1',
        'task_id': 'MAT2-A05',
        'attempt_id': 'b4ad70883ac2480a928dcc828f33c65f',
        'arrival_id': 'arrival-b22e42ce0ecf4204acb2f99d0aecff97',
        'date': '2026-09-28',
        'captain_decision': {
            'decision_id': st['captain_decision']['decision_id'],
            'record': st['captain_decision']['record'],
            'sha256': sha256_file(Path(st['captain_decision']['record'])),
            'authority': 'Captain (highest)',
            'verbatim_excerpt': 'use a human data then modify it to fit macaque data ... '
                                'our first mutation where we take something like a human hand and '
                                'augment it with what you would call macaque DNA ... take what '
                                'exists and then modify',
        },
        'model': {'id': f'model.{MODEL}',
                  'structure_record': 'mutation_structure.json',
                  'structure_record_sha256': sha256_file(HERE / 'mutation_structure.json'),
                  'mjcf_record': 'macaque_hand_mutation.xml',
                  'mjcf_record_sha256': sha256_file(HERE / 'macaque_hand_mutation.xml'),
                  'units': st['units'],
                  'frame': st['frame']['frame_id'],
                  'species_disclosure': st['species_disclosure']},
        'human_derived_base': {
            'vendor_rev': '33f3ded946f55adbdcf963c99999587aadaf975f',
            'vendor_tree': 'E:/PythonChimera/vendor/myo_sim (read-only, unpinned upstream clone; rev+sha256 pinned at use)',
            'pins': st['sources'][0]['pins'],
            'taken_verbatim': ['per-digit body topology (5 digits, 5 mc + 14 phalanges)',
                               'joint names, axes and ranges',
                               'inter-segment directions (magnitudes scaled by s)',
                               '19 digit STL bone shapes at recorded uniform scale s',
                               'per-body relative mass fractions (renormalized to macaque hand mass)'],
        },
        'macaque_constraints': {
            'pins': st['sources'][1]['pins'],
            'applied': [
                {'constraint': 'hand body mass/center/inertia', 'value': {'mass_kg': 0.049,
                 'mass_center_m': st['anchor_body']['physical']['mass_center_m'],
                 'inertia_kg_m2': st['anchor_body']['physical']['inertia_kg_m2']},
                 'source': 'monkeyArm_current.osim Body "hand" verbatim'},
                {'constraint': 'wrist_flexion range rad', 'value': [-1.30899694, 1.57079633],
                 'source': 'osim wrist Coordinate'},
                {'constraint': 'wrist_abduction range rad', 'value': [-1.04719755, 0.78539816],
                 'source': 'osim wrist Coordinate'},
                {'constraint': 'MACAQUE_HAND_LENGTH m', 'value': al['macaque_hand_length_m'],
                 'source': 'geom.macaque_arm.hand bounds_m Y extent (hand.vtp sha256-pinned, mm->m 0.001)'},
                {'constraint': 'MUTATION_SCALE s', 'value': al['mutation_scale'],
                 'formula': f"s = {al['macaque_hand_length_m']:.8f} / {al['human_hand_length_m']:.6f}"},
                {'constraint': 'forearm references m', 'value': {'ulna': al['macaque_ulna_m']},
                 'source': 'geom.macaque_arm.ulna bounds_m'},
                {'constraint': 'digit-named muscle anchors', 'value': st['muscle_anchor_mapping'],
                 'source': 'osim Schutte1993Muscle_Deprecated ext_digitorum / flex_digit_profundus hand-frame PathPoints'},
            ],
        },
        'stated_formula': {
            'human_hand_length_m': al['human_hand_length_m'],
            'macaque_hand_length_m': al['macaque_hand_length_m'],
            'mutation_scale': al['mutation_scale'],
            'rule': 'mutant offset = s * human offset (componentwise); s = MACAQUE_HAND_LENGTH / HUMAN_HAND_LENGTH',
            'mass_prior_rule': 'mass_prior_i = 0.049 kg * human_mass_i / 0.1589 kg',
            'allometry': {'human_ratio': al['human_ratio'], 'macaque_ratio': al['macaque_ratio'],
                          'mutant_ratio': al['mutant_ratio'],
                          'tolerances': {'hand_length_identity': 1e-9, 'ratio': 1e-3}},
        },
        'derived_structure': {
            'body_count': 19, 'phalanx_count': 14, 'metacarpal_count': 5,
            'digit_joint_count': 20, 'wrist_dof': 2,
            'bodies': [
                {'name': b['name'], 'parent': b['parent'],
                 'pos_m': b['mutation']['pos_m'],
                 'mass_prior_kg': b['mutation']['mass_prior_kg'],
                 'joints': b['joints'],
                 'geometry_asset': b['geometry'][0]['asset_id']}
                for b in st['bodies']],
            'chain_lengths_m': {'thumb': 0.055887, 'digit2': 0.081837, 'digit3': 0.083606,
                                'digit4': 0.078262, 'digit5': 0.070343},
            'fingertips_m': st['envelope_check']['fingertip_positions_m'],
        },
        'declared_deviations': [
            'species mixing: human base structure/shapes with macaque frame numbers; declared hybrid per Captain decision (not species-true, not REALITY-category)',
            'uniform allometric scale s instead of macaque per-phalanx proportions (no such data in-repo)',
            'carpal chain folded into the palm anchor; macaque hand body owns carpus mass/geometry',
            'radial (X/Z) fingertip overshoot vs hand.vtp envelope recorded (thumb X +0.030681 vs +0.020731 max; d2/d3 Z ~+0.0106 vs +0.00464 max; d5 X -0.014887 vs -0.0124375 min); Y-span coherence holds (preregistered falsifier)',
            'masses are proportional training priors, not measured per-phalanx masses (anchor mass and digit priors are alternative views of the same 0.049 kg, not additive)',
            'muscle/tendon paths are anchor points only; no volume, skin or wrap geometry',
            'digit joint ranges remain human base values (no macaque per-digit ROM in-repo); only the wrist is macaque-ranged',
            'geometry = vendor STLs at recorded scale s + explicit scaled segment vectors; no fabricated mesh; macaque hand.vtp bound via graph record only (VTP not MuJoCo-loadable)',
        ],
        'validation': {
            'validator': 'validate_mutation.py',
            'validator_sha256': sha256_file(HERE / 'validate_mutation.py'),
            'receipt': 'validation_receipt.json',
            'receipt_sha256': sha256_file(HERE / 'validation_receipt.json'),
            'summary': receipt['summary'],
            'note': 'First validation run reported 2 FAILs caused by validator-side defects '
                    '(phalanx name filter missed the thumb bodies; connectivity walk did not '
                    'treat the anchor as terminal). Corrected in validate_mutation.py; the '
                    'structure values were unaffected and the corrected run passes '
                    f"{receipt['summary']['passed']}/{receipt['summary']['total']}.",
        },
        'preregistration': {'path': 'PREREGISTRATION.md',
                            'sha256': sha256_file(HERE / 'PREREGISTRATION.md')},
        'derivation_log': {'path': 'derivation_output.txt',
                           'sha256': sha256_file(HERE / 'derivation_output.txt')},
    }
    (HERE / 'mutation_manifest.json').write_text(
        json.dumps(manifest, indent=1) + '\n', encoding='utf-8')
    print('wrote mutation_manifest.json sha256=' + sha256_file(HERE / 'mutation_manifest.json'))


if __name__ == '__main__':
    main()
