"""MAT2-D-MASSREG named checks (card-kit test pattern).

Each check reads the COMMITTED receipts and asserts the frozen claims
(PREREGISTRATION.md, commit c5d44831). The suite is the executable form of
the done_when clauses; batch_gates.py re-runs it CPU-only at the candidate
head. ZERO skips: every check executes on this machine.

Naming: T<n>_<clause> done_when executions, FA<n> falsifier arms (asserted
from the committed falsifier receipt; the arms themselves run in
`build_register.py falsify` with the clean control FIRST in the same
executable), P_ probes.

THE LAW: receipt-semantics changes land TOGETHER with the named check that
asserts them. Run: python -B test_massreg_checks.py
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import build_register as br  # noqa: E402

STORE_MANIFEST = pathlib.Path(br.STORE, 'MANIFEST.json')

FROZEN = br.FROZEN
FAMILY_COUNTS = br.FAMILY_COUNTS


def sha256_file(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def load(name):
    path = HERE / name
    if not path.exists():
        raise FileNotFoundError(name + ' (run the generator modes first)')
    return json.loads(path.read_text(encoding='utf-8'))


REGISTER = load('mass_register.json')
ENUM = load('enumeration_receipt.json')
IMPLIES = load('implied_bw_receipt.json')
ZDELTA = load('zero_mass_delta_receipt.json')
FALS = load('falsifier_receipt.json')
REGRES = load('regression_receipt.json')
DETERM = load('determinism_receipt.json')

RECEIPTS_CTX = {
    'anchor_manifest': {row_path: row_sha for row_path, row_sha
                        in ENUM['anchor_manifest'].items()},
    'implied_bw_sha256': ENUM['implied_bw_receipt_sha256'],
    'enumeration': {'families': ENUM['families']},
}


class T1Schema(unittest.TestCase):
    def test_T1_register_schema_and_identity(self):
        self.assertEqual(REGISTER['schema'], 'chimera.massreg.register.v1')
        self.assertEqual(REGISTER['card'], 'MAT2-D-MASSREG')
        self.assertEqual(REGISTER['attempt_id'], br.ATTEMPT_ID)
        self.assertEqual(REGISTER['criteria_sha256'], br.CRITERIA_SHA256)
        self.assertEqual(ENUM['entry_count'], len(REGISTER['entries']))
        self.assertEqual(ENUM['entry_count'], 51)
        self.assertEqual(ENUM['declared_out_of_scope_count'], 7)


class T2Fields(unittest.TestCase):
    def test_T2_entry_fields_vocabularies_anchors(self):
        self.assertEqual(br.check_register(REGISTER, RECEIPTS_CTX), [])
        for row in REGISTER['entries']:
            self.assertIn(row['source_kind'],
                          ('pinned-producer', 'det-scaled',
                           'reference-constant'))
            self.assertIn(row['validation_state'],
                          ('validated', 'unvalidated-density',
                           'non-physical-reference'))
            self.assertIn(row['system'], ('scene', 'biological-reference'))
            self.assertTrue(row['evidence_anchor']['path'])
            self.assertRegex(row['evidence_anchor']['sha256'], r'^[0-9a-f]{64}$')
            self.assertRegex(row['producer_receipt_sha256'],
                             r'^[0-9a-f]{64}$')

    def test_T2b_family_counts_match_frozen(self):
        fams = {}
        for cid_prefix, fam in br.FAMILY_PREFIXES.items():
            n = sum(1 for e in REGISTER['entries']
                    if e['contributor_id'].startswith(cid_prefix))
            if n:
                fams[fam] = n
        self.assertEqual(fams, FAMILY_COUNTS)


class T3SpecimenClass(unittest.TestCase):
    def test_T3_scene_rows_backed_by_measurement_receipt(self):
        receipt_sha = sha256_file(HERE / 'implied_bw_receipt.json')
        self.assertEqual(receipt_sha, ENUM['implied_bw_receipt_sha256'])
        for row in REGISTER['entries']:
            if row['system'] == 'scene':
                self.assertEqual(row['specimen_class'],
                                 REGISTER['specimen_classification']
                                 ['scene_class'])
                self.assertEqual(row['specimen_class_receipt_sha256'],
                                 receipt_sha)


class T4BuffyTotals(unittest.TestCase):
    def test_T4_buffy_totals_bit_exact(self):
        tua = 0.0
        pelvis = None
        n_res = 0
        for row in REGISTER['entries']:
            cid = row['contributor_id']
            if cid.startswith('buffy.transported.'):
                if cid == 'buffy.transported.pelvis':
                    pelvis = row['value_kg']
                else:
                    tua += row['value_kg']
            elif cid.startswith('buffy.unresolved.'):
                n_res += 1
                self.assertEqual(row['value_kg'], 0.0)
        self.assertEqual(tua, 5.262978509953907)
        self.assertEqual(tua + pelvis, 17.039978509953905)
        self.assertEqual(tua + pelvis,
                         REGISTER['totals']['buffy_all_transported_kg']
                         ['value'])
        self.assertEqual(n_res, 9)
        self.assertEqual(REGISTER['totals']['buffy_root_reference_share']
                         ['value'], 0.6911393692850295)
        # every transported product identity, from the pinned role fields
        for row in REGISTER['entries']:
            if row['contributor_id'].startswith('buffy.transported.'):
                role = row['role']
                self.assertEqual(role['mass_src_kg'] * role['det_scale'],
                                 row['value_kg'])


class T5SceneTotals(unittest.TestCase):
    def test_T5_scene_totals_bit_exact(self):
        totals = REGISTER['totals']
        self.assertEqual(totals['scene_body_total_kg']['value'], 10.038)
        self.assertTrue(totals['scene_body_total_kg']
                        ['reproduced_bit_exact'])
        self.assertEqual(totals['scene_carve_sum_kg']['value'], 10.037998)
        self.assertTrue(totals['scene_carve_sum_kg']['reproduced_bit_exact'])
        # the honest builder-order disclosure (PREREG 7.2c)
        builder = totals['builder_order_sum_kg']
        self.assertEqual(builder['value'], 10.037998000000004)
        self.assertFalse(builder['bit_exact'])
        self.assertTrue(builder['within_float_floor'])
        facts = ENUM['families']['scene']
        self.assertTrue(facts['body_total_bit_exact'])
        self.assertTrue(facts['carve_sum_bit_exact'])
        self.assertFalse(facts['strut_pair_bit_equal_carve'])


class T6B03Counted(unittest.TestCase):
    def test_T6_b03_counted_set_bit_exact(self):
        total = 0.0
        for row in REGISTER['entries']:
            if row['contributor_id'].startswith('b03.counted.'):
                total += row['value_kg']
        self.assertEqual(total, 0.0447023937544344)
        self.assertEqual(REGISTER['totals']['b03_counted_set_kg']['value'],
                         0.0447023937544344)
        density = next(e for e in REGISTER['entries']
                       if e['contributor_id'] == 'b03.density.bone_assumed')
        self.assertEqual(density['value'], 1800.0)
        self.assertEqual(density['role']['density_band_kg_m3'],
                         [1650.0, 1950.0])
        self.assertEqual(density['validation_state'], 'unvalidated-density')


class T7ZeroDelta(unittest.TestCase):
    def test_T7_zero_mass_delta_receipt_green(self):
        self.assertTrue(ZDELTA['zero_mass_delta'])
        self.assertTrue(ZDELTA['Z1_all_changed_paths_under_card_prefix'])
        self.assertEqual(ZDELTA['changed_paths_outside_prefix'], [])
        for name, check in ZDELTA['Z2_producer_blobs_unchanged'].items():
            self.assertTrue(check['equal_at_both_extractions'], name)
            self.assertTrue(check['matches_pin'], name)
        for key, ok in ZDELTA['Z3_totals_bit_exact'].items():
            self.assertTrue(ok, key)
        self.assertEqual(ZDELTA['base_sha'], br.BASE_SHA)


class T8RegisterNotRepair(unittest.TestCase):
    def test_T8_two_systems_distinct_never_reconciled(self):
        self.assertTrue(REGISTER['law']['two_systems_declared_distinct'])
        self.assertFalse(REGISTER['law']['reconciliation_declared'])
        self.assertEqual(REGISTER['law']['text'], br.LAW_TEXT)
        self.assertEqual(sorted(REGISTER['systems']),
                         ['biological-reference', 'scene'])
        for name, system in REGISTER['systems'].items():
            self.assertFalse(system['reconciled_into_one'], name)
        self.assertEqual(REGISTER['specimen_classification']['branch'],
                         'escalation-flagged')
        self.assertTrue(REGISTER['specimen_classification']
                        ['reconciliation_claim']
                        .startswith('REFUSED:'))
        self.assertIn('SUBSUME', REGISTER['subsumption_hazard'])
        self.assertTrue(REGISTER['double_count_scan']['ledgers_disjoint'])
        self.assertEqual(
            REGISTER['double_count_scan']['assembly_counted_mass_kg'], 0.0)
        gap_ids = {g['gap_id'] for g in REGISTER['gaps']}
        self.assertEqual(gap_ids, {'GAP-2', 'GAP-3', 'GAP-4', 'GAP-8'})


class T9ImpliedBW(unittest.TestCase):
    def test_T9_implied_bw_receipt_and_decision(self):
        self.assertTrue(IMPLIES['calibration']['C1_matches_atlas'])
        self.assertTrue(IMPLIES['calibration']['C2_matches_atlas'])
        self.assertEqual(IMPLIES['calibration']['C1_m26_means_implied_bw_kg'],
                         {'upper_arm': 7.8779, 'forearm': 7.8795,
                          'hand': 7.7978})
        self.assertEqual(IMPLIES['calibration']['C2_osim_claims_implied_bw_kg'],
                         {'upper_arm': 5.2326, 'forearm': 6.0938,
                          'hand': 4.9097})
        e4 = IMPLIES['decision']['e4_primary_implied_bw_kg']
        low, high = FROZEN['female_band_window']
        self.assertGreaterEqual(e4, low)
        self.assertLessEqual(e4, high)
        self.assertEqual(IMPLIES['decision']['specimen_class'],
                         'internally-inconsistent-female-band')
        self.assertEqual(IMPLIES['decision']['branch'], 'escalation-flagged')
        self.assertIsNotNone(IMPLIES['decision']['escalation'])
        evals = {e['id']: e for e in IMPLIES['evaluations']}
        self.assertEqual(evals['E3_hand_at_scene_hand'].get('refusal'),
                         'hand_row_no_scene_mass')
        self.assertIn('E4_PRIMARY_split_free_per_arm', evals)
        self.assertIn('E5_stress_with_hand_row', evals)


class T10BitCopy(unittest.TestCase):
    def test_T10_register_values_bit_copied(self):
        verified = ENUM['value_bit_copy_verified']
        for family, ok in verified.items():
            self.assertTrue(ok, family)
        self.assertTrue(ENUM['vacuous_guard_selftest'])
        # spot literals straight from the pinned producers
        by_id = {e['contributor_id']: e for e in REGISTER['entries']}
        self.assertEqual(by_id['buffy.transported.pelvis']['value_kg'], 11.777)
        self.assertEqual(
            by_id['buffy.transported.femur_r']['value_kg'],
            1.4354939022274895)
        self.assertEqual(by_id['scene.walk.pelvis']['value_kg'], 7.371998)
        self.assertEqual(by_id['scene.walk.upperarm_fore_left']['value_kg'],
                         0.2737)
        self.assertEqual(
            by_id['scene.acceptance_denominator.membrane_inventory']
            ['value_kg'], 13824.5)
        self.assertEqual(by_id['reference.turnquist.band_midpoint']
                         ['value_kg'], 6.15)


class FAArms(unittest.TestCase):
    def test_FA_all_arms_bite_with_clean_controls(self):
        self.assertTrue(FALS['F_all_green'])
        for name, arm in FALS['arms'].items():
            self.assertTrue(arm['clean_control']['green'], name)
            self.assertTrue(arm['clean_control']['guard'].endswith('_premature'),
                            name)
            self.assertTrue(arm['bit'], name)
        self.assertEqual(
            sorted(FALS['arms']),
            ['FB1_row_omission_bites', 'FB2_value_perturbation_bites',
             'FB3_anchor_mismatch_bites',
             'FB4_reconciliation_declaration_bites'])


class Probes(unittest.TestCase):
    def test_P_input_pins_and_store_anchors(self):
        pins = br.verify_input_pins()
        self.assertEqual(len(pins), len(br.PINNED_FILES))
        manifest = json.loads(STORE_MANIFEST.read_text(encoding='utf-8'))
        rows = {r['stored_rel_path']: r for r in manifest['files']}
        for name in br.ANCHOR_PATHS:
            rel = br.ANCHOR_PATHS[name]
            self.assertIn(rel, rows, rel)
            self.assertEqual(rows[rel]['sha256'],
                             br.PIN_SHA_FOR_ANCHOR[name], rel)

    def test_P_vacuous_guard(self):
        self.assertTrue(br.vacuous_guard_selftest())

    def test_P_determinism_register_byte_identity(self):
        self.assertTrue(DETERM['X2_register_byte_identical'])
        self.assertTrue(DETERM['X2_pass'])
        self.assertEqual(DETERM['receipt_shared_keys_differing'], [])

    def test_P_regression_sealed_audit_rerun_green(self):
        self.assertEqual(REGRES['exit_code'], 0)
        self.assertTrue(REGRES['P_regression_suite_green'])
        self.assertTrue(REGRES['sealed_receipt_sha_unchanged'])
        self.assertEqual(REGRES['receipt_sha_before'],
                         br.PINNED_FILES['b06_audit_receipt'][1])

    def test_P_report_number_lint(self):
        proc = subprocess.run(
            [sys.executable, '-B', str(HERE / 'lint_report_numbers.py')],
            capture_output=True, text=True, timeout=300)
        self.assertEqual(proc.returncode, 0,
                         'report-number lint failed:\n' + proc.stdout
                         + proc.stderr)
        self.assertIn('lint OK', proc.stdout)


if __name__ == '__main__':
    unittest.main(verbosity=2)
