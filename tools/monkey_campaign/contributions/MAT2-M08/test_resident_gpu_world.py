"""MAT2-M08 named checks (GPU box; runs after run_experiments.py modes).

Each check reads the committed receipts and asserts the frozen claims, so
the suite is the executable form of the done_when clauses:
  X1_gpu_direct_reference_agreement
  X2_determinism_byte_identity
  X3_residency_profile_within_budget
  X4_bh_law_error_nearfield
  F1_F2_F3_falsifier_arms_bite_with_clean_controls
  P_input_pins / P_single_writer / P_gates_declared / P_vacuous_guard
Run:  python -B test_resident_gpu_world.py
"""
from __future__ import annotations

import json
import pathlib
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import run_experiments as rx  # noqa: E402


def load(name):
    path = HERE / name
    if not path.exists():
        raise FileNotFoundError(name + ' (run the experiment modes first)')
    return json.loads(path.read_text(encoding='utf-8'))


class X1Agreement(unittest.TestCase):
    def test_X1_gpu_direct_reference_agreement(self):
        receipt = load('experiment_receipt.json')
        self.assertTrue(receipt['X1_pass'])
        self.assertLessEqual(receipt['worst_membrane_position_diff_m'],
                             receipt['windows']['position_m'])
        self.assertLessEqual(receipt['worst_plate_position_diff_m'],
                             receipt['windows']['position_m'])
        self.assertTrue(receipt['telemetry']['within_budget'])


class X2Determinism(unittest.TestCase):
    def test_X2_determinism_byte_identity(self):
        receipt = load('determinism_receipt.json')
        self.assertTrue(receipt['X2_byte_identical'])


class X3Profile(unittest.TestCase):
    def test_X3_residency_profile_within_budget(self):
        receipt = load('profile_receipt.json')
        self.assertTrue(receipt['residency_within_budget'])
        self.assertGreater(receipt['state_bytes_total'], 0)
        self.assertLess(receipt['max_up_bytes_per_tick'],
                        receipt['state_bytes_total'])
        self.assertLess(receipt['max_down_bytes_per_tick'],
                        receipt['state_bytes_total'])
        self.assertGreater(receipt['step_ms_p50'], 0.0)
        self.assertGreater(receipt['step_ms_max'],
                           receipt['step_ms_p50'])


class X4BH(unittest.TestCase):
    def test_X4_bh_law_error_nearfield(self):
        receipt = load('bh_receipt.json')
        self.assertTrue(receipt['two_body_identity_within_1e-12'])
        self.assertTrue(receipt['X4_bh_within_window'])
        self.assertTrue(receipt['X4_near_field_within_window'])
        for row in receipt['measurements']:
            self.assertLessEqual(row['bh_rel_err_max'],
                                 receipt['bh_error_window'])
            self.assertLessEqual(row['near_theta0_rel_err_max'],
                                 receipt['near_field_window'])


class Falsifiers(unittest.TestCase):
    def test_F1_F2_F3_falsifier_arms_bite_with_clean_controls(self):
        receipt = load('falsifier_receipt.json')
        arms = receipt['arms']
        self.assertTrue(arms['F1_state_roundtrip_fires'])
        self.assertTrue(arms['F1_clean_within_budget'])
        self.assertTrue(arms['F2a_exceeds_window'])
        self.assertTrue(arms['F2_clean_theta_within_window'])
        self.assertTrue(arms['F2_clean_theta0_within_window'])
        self.assertTrue(arms['F3_stale_diagnostics_caught'])
        self.assertTrue(arms['F3_clean_chain_green'])
        self.assertTrue(receipt['F_all_green'])


class Probes(unittest.TestCase):
    def test_P_input_pins(self):
        rx.verify_input_pins()

    def test_P_single_writer(self):
        scan = rx.p_single_writer()
        self.assertTrue(scan['ok'], scan['violations'])

    def test_P_gates_declared(self):
        gates = rx.p_gates_declared()
        self.assertEqual(gates['count'], 12)

    def test_P_vacuous_guard(self):
        self.assertTrue(rx.vacuous_guard_selftest())

    def test_P_regression_m07_suite(self):
        receipt = load('regression_receipt.json')
        self.assertEqual(receipt['exit_code'], 0)
        self.assertTrue(receipt['P4_m07_suite_green'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
