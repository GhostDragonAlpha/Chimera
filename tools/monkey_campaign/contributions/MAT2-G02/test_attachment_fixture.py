"""MAT2-G02 named checks (M08 pattern) - the executable done_when clauses.

Each check reads the COMMITTED receipts and asserts the frozen claims.
THE LAW (M08, earned twice): receipt-semantics changes land TOGETHER with the
named check that asserts them, in the SAME change.

Naming: C<n>_<clause> for done_when executions, X<n> for agreement/
determinism, F<n> for falsifier arms, P_... for probes.
Run:  python -B test_attachment_fixture.py
"""
from __future__ import annotations

import json
import pathlib
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import run_experiments as rx  # noqa: E402

CAMERA_REQUIRED_FIELDS = [
    'frame_id', 'coordinate_unit', 'position',
    'orientation_convention_and_values', 'target', 'distance_to_target',
    'projection', 'vertical_fov_or_orthographic_span', 'near_far_planes',
    'aspect_ratio', 'viewport_resolution', 'camera_motion_or_bookmark_sequence',
    'visibility_layers', 'label_ids', 'occlusion_or_xray_mode',
    'state_or_tick_interval',
]


def load(name):
    path = HERE / name
    if not path.exists():
        raise FileNotFoundError(name + ' (run the experiment modes first)')
    return json.loads(path.read_bytes().decode('utf-8'))


class X1ElementAgreement(unittest.TestCase):
    """X1: closed-form element agreement + the exact T-series probes."""

    def setUp(self):
        self.receipt = load('experiment_receipt.json')

    def test_X1_pass(self):
        self.assertTrue(self.receipt['X1_pass'])

    def test_X1_element_closed_form_agreement(self):
        self.assertLessEqual(self.receipt['worst_agreement_rel'], 1e-15)
        self.assertTrue(self.receipt['element_within_window'])

    def test_X1_probe_series(self):
        for key in ('T1_pass', 'T2_pass', 'T3_pass', 'T4_pass', 'T5_pass',
                    'T7_pass', 'T9_pass'):
            self.assertTrue(self.receipt[key], key)


class C1TwoSidedEntry(unittest.TestCase):
    """Clause: finite-area attachment forces AND moments enter BOTH
    connected material states."""

    def setUp(self):
        self.receipt = load('experiment_receipt.json')
        self.trace = load('experiment_trace.json')

    def test_C1_reciprocity_exact(self):
        self.assertTrue(self.receipt['T3_pass'])

    def test_C1_moments_enter_both_states(self):
        row = self.trace['rows'][232]   # tick 233, bound, loaded patch
        self.assertTrue(row['patch_bound'])
        ma = row['moment_about_com_a_N_m']
        mb = row['moment_about_com_b_N_m']
        self.assertGreater(max(abs(x) for x in ma), 0.0)
        self.assertGreater(max(abs(x) for x in mb), 0.0)
        self.assertEqual(row['interface_force_sum_N'], [0.0, 0.0, 0.0])


class C2RemovalSemantics(unittest.TestCase):
    """Clause: physical bond/removal semantics match the limb experiment
    (M09): bitwise post-release zero, energy dissipated at the release tick,
    remaining contact persists, documents bond_count 1 -> 0."""

    def setUp(self):
        self.receipt = load('experiment_receipt.json')

    def test_C2_bitwise_release_identity(self):
        t8 = self.receipt['T8']
        self.assertTrue(t8['bitwise_release_identity'])
        self.assertGreater(t8['U233_J'], 0.0)
        self.assertEqual(t8['U_release_J'], t8['U233_J'])

    def test_C2_post_release_bitwise_zero(self):
        self.assertTrue(self.receipt['T8']['post_release_bitwise_zero'])

    def test_C2_documents_bond_removed_contact_persists(self):
        docs = self.receipt['documents']
        self.assertEqual(docs['bound_document_bond_count'], 1)
        self.assertEqual(docs['released_document_bond_count'], 0)
        self.assertEqual(docs['bound_document_contact_count'], 1)
        self.assertEqual(docs['released_document_contact_count'], 1)
        self.assertTrue(docs['both_validate_m01'])

    def test_C2_separation_permitted_recontact_without_patch(self):
        t8 = self.receipt['T8']
        self.assertTrue(t8['separation_demonstrated'])
        self.assertTrue(t8['recontact_in_window'])
        self.assertGreaterEqual(t8['min_penetration_m'], -0.015)


class C3PatchGeometryStiffness(unittest.TestCase):
    """Clause: actual patch geometry, stiffness meet declared physical
    requirements (declared placeholders, area-scaled, falsifiably unequal
    triangles)."""

    def setUp(self):
        self.receipt = load('experiment_receipt.json')

    def test_C3_area_scaling_exact(self):
        self.assertTrue(self.receipt['T2_pass'])

    def test_C3_weights_and_rotational_resistance(self):
        self.assertTrue(self.receipt['T4_pass'])
        self.assertTrue(self.receipt['T5_pass'])


class C4NoAutoBond(unittest.TestCase):
    def setUp(self):
        self.receipt = load('experiment_receipt.json')

    def test_C4_auto_bond_refused(self):
        self.assertTrue(self.receipt['T7_pass'])


class C5C17Terminal(unittest.TestCase):
    """Clause: the biological attachment debt closes explicitly-unresolved;
    every fixture constant is a declared placeholder; no lambda_min; no
    fitting (sealed A07 gate)."""

    def setUp(self):
        self.receipt = load('experiment_receipt.json')

    def test_C5_terminal_record(self):
        c17 = self.receipt['c17_terminal']
        self.assertEqual(c17['biological_ports']['terminal_state'],
                         'explicitly_unresolved')
        self.assertEqual(c17['biological_ports']['c17_status_carried_open'],
                         26)
        self.assertFalse(c17['biological_ports']['synthetic_lambda_min_used'])
        self.assertIn('A07', c17['biological_ports']['reason'])

    def test_C5_fixture_constants_declared_placeholder(self):
        fixture = self.receipt['c17_terminal']['fixture_constants']
        self.assertEqual(fixture['provenance_class'], 'declared_placeholder')
        self.assertTrue(fixture['never_biological'])
        self.assertIn('MAT2-M05', fixture['derivation'])


class X2Determinism(unittest.TestCase):
    def test_X2_scoped_determinism(self):
        receipt = load('determinism_receipt.json')
        self.assertTrue(receipt['X2_trace_byte_identical'])
        self.assertTrue(receipt['X2_pass'])
        self.assertEqual(receipt['receipt_keys_only_in_rerun'], [])
        self.assertEqual(receipt['receipt_shared_keys_differing'], [])


class Falsifiers(unittest.TestCase):
    def test_F_all_arms_bite_with_clean_controls(self):
        receipt = load('falsifier_receipt.json')
        self.assertTrue(receipt['F_all_green'])
        self.assertTrue(receipt['vacuous_guard_selftest'])
        for name, arm in receipt['arms'].items():
            self.assertTrue(arm['bit'], f'arm {name} did not bite')
            self.assertTrue(arm['discriminating'], f'arm {name} not '
                            'discriminating')
            self.assertTrue(arm['clean_control']['within_tolerance'],
                            f'arm {name} clean control failed')


class Probes(unittest.TestCase):
    def test_P_input_pins(self):
        rx.verify_input_pins()

    def test_P_vacuous_guard(self):
        self.assertTrue(rx.vacuous_guard_selftest())

    def test_P_gates_declared(self):
        receipt = load('experiment_receipt.json')
        gates = receipt['p_gates_declared']
        self.assertEqual(gates['count'], len(set(gates['gate_codes'])))
        self.assertGreaterEqual(gates['count'], 10)

    def test_P_regression_suite(self):
        receipt = load('regression_receipt.json')
        self.assertEqual(receipt['exit_code'], 0)
        self.assertTrue(receipt['P_regression_suite_green'])

    def test_P_upstream_constants_unchanged(self):
        """The declared areal densities derive from the sealed M05 carrier
        (A1 repair): the module constants must equal 60/0.0175 etc."""
        import attachment_patch as ap
        self.assertEqual(ap.KA_T, 60.0 / 0.0175)
        self.assertEqual(ap.KA_S, 40.0 / 0.0175)
        self.assertEqual(ap.KA_THETA, 0.8 / 0.0175)


class CaptureChecks(unittest.TestCase):
    """Capture-law checks (only assert when the capture has been built; the
    mode chain runs them before submission)."""

    def setUp(self):
        self.capture_ready = (HERE /
                              'capture_validation_receipt.json').exists()

    def test_C6_camera_record_and_clean_pairs(self):
        if not self.capture_ready:
            raise unittest.SkipTest('capture not built yet')
        manifest = load('capture_manifest.json')
        self.assertEqual(manifest['task_id'], 'G02')
        for view in manifest['views']:
            cam = view['camera']
            for field in CAMERA_REQUIRED_FIELDS:
                self.assertIn(field, cam, f'{field} missing in '
                              f"{view['view_id']}/{view['mode']}")
        pairs = {}
        for view in manifest['views']:
            pairs.setdefault(view['pair_id'], {})[view['mode']] = view
        for pair_id, pair in pairs.items():
            self.assertIn('diagnostic', pair, pair_id)
            self.assertIn('clean', pair, pair_id)
            self.assertEqual(pair['diagnostic']['camera'],
                             pair['clean']['camera'], pair_id)

    def test_C6_clean_diagnostic_state_hash(self):
        if not self.capture_ready:
            raise unittest.SkipTest('capture not built yet')
        receipt = load('capture_validation_receipt.json')
        self.assertTrue(receipt['structurally_valid'])
        self.assertTrue(receipt['state_hash_preserved_across_view_toggles'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
