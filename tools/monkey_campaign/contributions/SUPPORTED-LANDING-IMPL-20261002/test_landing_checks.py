"""Named checks over the SUPPORTED-LANDING receipt/trace (in-process
unittest; defense in depth on top of the in-run enforcement)."""
import unittest

STATE = {}


class LandingReceiptChecks(unittest.TestCase):
    def setUp(self):
        self.receipt = STATE['receipt']
        self.trace = STATE['trace']

    def test_prereg_sha_embedded(self):
        self.assertEqual(self.receipt['preregistration_sha256'],
                         '40caec008862e79407eab409967406c1b6dc02aa63b9de08a'
                         '5b00cf02c57dcdd')
        self.assertEqual(self.receipt['base_sha'],
                         '10b05f9ff912edd2c3fc1f2d8f4fcc8c261d01ed')

    def test_verdicts_present(self):
        for key in ('P1_hold_prefix_reproduces_sealed_windows',
                    'P2_release_fall_identity_to_declared_floor',
                    'P3_floor_contact_nonpenetration_at_margin',
                    'P4_supporting_impulse_two_term_law',
                    'P5_rest_stability_declared_window',
                    'P6_energy_destination_through_impact',
                    'P7_fences_not_run'):
            self.assertIn(key, self.receipt['verdicts'])

    def test_fences_recorded(self):
        self.assertEqual(
            self.receipt['verdicts']['P7_fences_not_run']['verdict'],
            'FENCED_NOT_RUN')

    def test_fixture_label_carried(self):
        self.assertIn('FIXTURE-CLASS', self.receipt['card_label'])
        self.assertIn('NEVER a grasp-chain', self.receipt['card_label'])

    def test_scene_extension_declared(self):
        ext = self.receipt['scene_extension']
        self.assertIsNotNone(ext)
        self.assertEqual(ext['pinned_bodies_declared'],
                         ['trunk_01.lateral', 'landing.ground_plane'])
        self.assertIn('records', ext['captured_side_channel'])

    def test_floor_declared_values(self):
        ext = self.receipt['scene_extension']['floor_body']
        self.assertEqual(ext['matter_id'], 'declared_fixture_ground')
        self.assertEqual(ext['pinned'], True)
        self.assertEqual(ext['triangles'], 2)
        self.assertEqual(ext['extent_m'], [0.6, 0.6])

    def test_derived_constants_match_corpus(self):
        d = self.receipt['derivation']
        self.assertEqual(d['d60_closed_form_m'], 0.4488075)
        self.assertEqual(d['v60_closed_form_mps'], 2.943)
        self.assertEqual(d['support_per_channel_ns'], 0.1641212673)
        self.assertEqual(d['impact_jn_scene_ns'], 9.847276038)
        self.assertEqual(d['ke_closed_pad_J'], 14.490266689917)
        self.assertEqual(d['ke_closed_total_J'], 43.470800069751)

    def test_presence_all_found(self):
        presence = self.receipt['derivation_presence']
        for key, row in presence.items():
            if key == 'values':
                continue
            self.assertTrue(row['found_in'],
                            'presence miss: %s' % key)

    def test_retracted_quotes_absent(self):
        self.assertEqual(
            self.receipt['retracted_quote_absence']['status'], 'ABSENT_OK')

    def test_no_undeclared_contact_sites(self):
        census = self.receipt['scene_checks']['site_census']
        self.assertEqual(census['undeclared'], [])
        self.assertIn('landing.ground_plane', census['declared_sites'])

    def test_annotation_law(self):
        ann = self.receipt['declared_annotations']
        self.assertEqual(ann['hold_seconds'], 0.1)
        self.assertEqual(ann['fall_seconds'], 0.3)
        self.assertEqual(ann['rest_seconds'], 0.3)

    def test_overall_verdict_shape(self):
        overall = self.receipt['overall_verdict']
        self.assertTrue(
            overall in ('CONFIRMING_MIXED_AS_PREDICTED',
                        'SEALED_LAW_REFUSAL_PRESERVED')
            or overall.startswith('PREDICTION_FALSIFIED_PRESERVED'))

    def test_mu_label_present(self):
        self.assertIn('NAMED PLACEHOLDERS',
                      self.receipt['mu_label']['pad_and_floor_0_6_0_4'])
        self.assertIn('never tuned',
                      self.receipt['mu_label']['pad_and_floor_0_6_0_4'])

    def test_capture_summary_embedded_when_present(self):
        if self.receipt.get('capture_summary_sha256') is not None:
            self.assertIn(self.receipt['capture_verdict'],
                          ('PASS', 'FAIL'))

    def test_landing_run_recorded(self):
        arm = self.trace['landing']
        self.assertIn('scene_extension', arm)
        self.assertEqual(arm['scene_extension']['floor_body'][
            'body_id'], 'landing.ground_plane')

    def test_regression_green_in_scope(self):
        self.assertTrue(STATE['regression']['green'])
