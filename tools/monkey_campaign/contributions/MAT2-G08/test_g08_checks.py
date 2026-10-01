"""test_g08_checks -- MAT2-G08 named checks (the executable done_when
battery; prereg section 6, amendment a1). Zero skips planned; every check
executes. Run: python -B -m unittest test_g08_checks -v
"""
from __future__ import annotations

import json
import pathlib
import unittest

HERE = pathlib.Path(__file__).resolve().parent

TOTAL_TICKS_EXPECTED = 9 * 229 + 13 * 60
WINDOWS_FROZEN = {
    'press_establishment_jn_eq_P': 1e-9,
    'stick_arrest_vt': 1e-12,
    'handover_jt_share_g_DT': 1e-9,
    'flight_closed_form': 1e-12,
    'full_tick_ledger_identity': 1e-12,
    'release_jn_bar': 1.0,
    'release_jt_bar': 1.0,
    'release_anchor_bar': 1.0,
    'velocity_recursion': 1e-9,
    'displacement_closed_form': 1e-9,
    'impulse_work_identity': 1e-12,
    'friction_loss_split': 1e-12,
    'stored_energy_account': 1e-9,
    'impulse_replay_closure': 1e-12,
    'pose_continuity': 1e-9,
    'seam_timing_t_seconds': 1e-12,
}


def load(name):
    return json.loads((HERE / name).read_text(encoding='utf-8'))


class PreregistrationFreeze(unittest.TestCase):

    def test_prereg_frozen_markers(self):
        text = (HERE / 'PREREGISTRATION.md').read_text(encoding='utf-8')
        flat = ' '.join(text.split())
        self.assertIn('done_when (verbatim): "Accepted mechanics pass '
                      'CPU/GPU and runtime identity gates relevant to '
                      'climbing"', flat)
        for marker in ('A1 line_identity', 'A4 unsupported_ledger',
                       'A9 numerical_budget', 'COMPOSITION BINDING WINDOW',
                       'declared_establishing',
                       'Amendments - a1 (pre-experiment'):
            self.assertIn(marker, flat)


class ReceiptIdentity(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.receipt = load('experiment_receipt.json')
        cls.trace = load('experiment_trace.json')

    def test_a01_line_identity(self):
        r = self.receipt
        self.assertIs(True, r['A1_line_identity'])
        self.assertEqual(9, len(r['A1_evidence']['t']))
        self.assertEqual(13, len(r['A1_evidence']['r']))
        for block in r['A1_evidence']['t'] + r['A1_evidence']['r']:
            self.assertTrue(block['row_hash_ok'], block['label'])
            self.assertTrue(block['identity_ok'], block['label'])

    def test_a02_transfer_envelope(self):
        r = self.receipt
        self.assertIs(True, r['A2_transfer_envelope'])
        for block in r['A1_evidence']['t']:
            self.assertTrue(block['verdict_ok'], block['label'])

    def test_a03_release_and_fall(self):
        r = self.receipt
        self.assertIs(True, r['A3_release_and_fall'])
        for block in r['A1_evidence']['r']:
            self.assertTrue(block['collision_ticks_ok'], block['label'])
            self.assertTrue(block['collision_values_ok'], block['label'])

    def test_a04_unsupported_ledger(self):
        r = self.receipt
        led = r['A4_evidence']
        self.assertIs(True, r['A4_unsupported_ledger'])
        self.assertEqual(TOTAL_TICKS_EXPECTED, led['total_ticks'])
        self.assertEqual(
            led['unsupported'],
            sum(led['response_classes'].values()))
        for name, row in led['per_scenario'].items():
            self.assertEqual(row['supported'] + row['unsupported'],
                             229 if row['segment'] == 'T' else 60, name)

    def test_a05_continuity(self):
        r = self.receipt
        self.assertIs(True, r['A5_continuity'])
        self.assertTrue(r['A5_evidence']['ok'])
        self.assertLessEqual(r['A5_evidence']['worst_m'], 1e-12)

    def test_a06_event_localization(self):
        r = self.receipt
        ev = r['A6_evidence']
        self.assertIs(True, r['A6_event_localization'])
        self.assertEqual([31], ev['t_handover_ticks'])
        self.assertEqual([193], ev['t_reattach_ticks'])
        self.assertEqual([220], ev['t_release_start_ticks'])
        self.assertEqual([21], ev['r_release_flip_ticks'])
        self.assertEqual({'band_mid|n=3|mu=0': [56], 'scene|n=1': [60]},
                         ev['r_collision_scenarios'])

    def test_a07_reference_math(self):
        r = self.receipt
        self.assertIs(True, r['A7_reference_math'])
        ev = r['A7_evidence']
        self.assertFalse(ev['any_flip'])
        self.assertTrue(ev['conversion_ok'])
        self.assertLessEqual(ev['conversion_worst_N'],
                             ev['conversion_window_N'])

    def test_a08_seam_union(self):
        r = self.receipt
        self.assertIs(True, r['A8_seam_union'])
        mv = r['A8_evidence']['measured_vs_certified']
        self.assertEqual(2061, mv['t_accepted']['measured'])
        self.assertEqual(0, mv['t_refused']['measured'])
        self.assertEqual(270, mv['t_g05_composition_accepted']['measured'])
        self.assertEqual(1791, mv['t_g05_composition_refused']['measured'])
        self.assertEqual(780, mv['r_accepted']['measured'])
        self.assertEqual(0, mv['r_refused']['measured'])
        self.assertEqual({'timing_unbound': 1791},
                         r['A8_evidence']['g05_refusal_codes_t'])

    def test_a09_numerical_budget(self):
        r = self.receipt
        self.assertIs(True, r['A9_numerical_budget'])
        ev = r['A9_evidence']
        seen = {}
        for op in ev['operations']:
            self.assertIn(op['operation'], WINDOWS_FROZEN,
                          'unfrozen budget operation')
            self.assertEqual(WINDOWS_FROZEN[op['operation']], op['window'],
                             op['operation'])
            self.assertTrue(op['within_window'], op['operation'])
            seen[op['operation']] = op['measured_worst']
        self.assertEqual(set(seen), set(WINDOWS_FROZEN),
                         'budget coverage mismatch')
        self.assertIn('operation', ev['tightest_margin_operation'])

    def test_a10_determinism(self):
        det = load('determinism_receipt.json')
        self.assertIs(True, det['trace_byte_identical'])
        self.assertEqual(det['trace_sha_main'], det['trace_sha_rerun'])
        self.assertEqual([], [k for k in det['receipt_delta_keys']
                              if k.split('.')[0] not in
                              det['augmentation_keys']])

    def test_battery_shape(self):
        b = self.receipt['battery']
        self.assertEqual(22, len(b['t_scenarios']) + len(b['r_scenarios']))
        self.assertEqual(TOTAL_TICKS_EXPECTED, b['total_ticks'])


class PClass(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.receipt = load('experiment_receipt.json')

    def test_criteria_identity(self):
        self.assertIs(True, self.receipt['criteria_registry_match'])
        self.assertEqual(
            'f2a89774038270b2665c70ec8ff2a8a521aec21fde5b9bc229e4faea84bdbb'
            'cb', self.receipt['criteria_sha256'])

    def test_prereg_chain_recorded(self):
        self.assertEqual(['f5ae83ce92cf6cb33c14151f491d2e339117ee7f',
                          '65bccc768b9f30be42d4253db3d4eeba6d9cdc61'],
                         self.receipt['prereg_commits'])

    def test_matter_identity(self):
        mi = self.receipt['matter_identity']
        self.assertEqual('wood_trunk_01', mi['trunk_matter'])
        self.assertEqual([0.6, 0.6], mi['f05_trunk_row'])
        self.assertEqual([0.6, 0.4], mi['f05_probe_row'])

    def test_named_absent_carried(self):
        names = [n['name'] for n in self.receipt['named_absent_variables']]
        self.assertEqual(10, len(names))
        self.assertTrue(all(n.startswith('x_') for n in names))

    def test_x_namespace_empty(self):
        self.assertEqual([], self.receipt['p_class']['x_namespace_delivered'])

    def test_vacuous_guard(self):
        self.assertIs(True, self.receipt['vacuous_guard_selftest'])

    def test_input_pins_verified(self):
        pins = self.receipt['input_pins']
        self.assertEqual(6, len(pins['host']))
        self.assertTrue(all(v == 'ok' for v in pins['host'].values()))

    def test_inventory_records_unresolved_gpu(self):
        inv = self.receipt['inventory']
        self.assertEqual('UNRESOLVED',
                         inv['gpu_device_leg_climb_contact_parity']
                         ['status'])
        self.assertNotIn('claim', json.dumps(
            inv['gpu_device_leg_climb_contact_parity']['status']).lower())


class Falsifier(unittest.TestCase):

    def test_f_all_green(self):
        f = load('falsifier_receipt.json')
        self.assertIs(True, f['F_all_green'])
        self.assertEqual(5, len(f['arms']))
        for arm in f['arms']:
            self.assertTrue(arm['bites'], arm['arm'])
            self.assertTrue(arm['clean']['clean_ok'], arm['arm'])
            self.assertIn('premature_guard', arm)


class Regression(unittest.TestCase):

    def test_regression_green(self):
        g = load('regression_receipt.json')
        self.assertIs(True, g['P_regression_suite_green'])
        self.assertEqual(6, len(g['suites']))
        for suite in g['suites']:
            self.assertEqual(0, suite['exit'], suite['suite'])
            self.assertTrue(suite['unmodified'])
        self.assertFalse(g['f05_note']['executed'])
        self.assertIn('data-bound', g['f05_note']['reason'])


if __name__ == '__main__':
    unittest.main()
