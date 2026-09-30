"""MAT2-M12 named checks: the executable done_when suite.

One named check per done_when clause (prereg section 7 gate map) plus the
capture gates. Every check reads the COMMITTED receipts and re-derives the
decisive quantities where affordable. The suite must run with ZERO skips:
    python -B test_lod.py
prints 'named checks: N executed, 0 skipped, ...' and exits non-zero on any
failure OR any skip (the G12 accounting law).
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sqlite3
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, 'E:/PythonChimera/tools/monkey_campaign')

import m12_lod as ml  # noqa: E402
import limb_world as lw  # noqa: E402
from visual_capture import validate_manifest  # noqa: E402

RES_ORDER = ml.RESOLUTION_ORDER


def load_json(name):
    return json.loads((HERE / name).read_text(encoding='utf-8'))


RECEIPT = load_json('experiment_receipt.json')
FALSIFIERS = load_json('falsifier_receipt.json')
DETERMINISM = load_json('determinism_receipt.json')
CAPTURE_MANIFEST = load_json('capture_manifest.json')
CAPTURE_CONTEXT = load_json('capture_context.json')
CAPTURE_RECEIPT = load_json('capture_validation_receipt.json')
CAPTURE_EVIDENCE = load_json('capture/evidence/capture_evidence.json')

CRITERIA_SHA256 = ('1e98a4f4465d4a50f21ce5c1d42b5ab51e9a7f96482f8f711d2'
                   'c66ca4c53b5b7')


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False)
REQUIRED_CAMERA_FIELDS = (
    'frame_id', 'coordinate_unit', 'position',
    'orientation_convention_and_values', 'target', 'distance_to_target',
    'projection', 'vertical_fov_or_orthographic_span', 'near_far_planes',
    'aspect_ratio', 'viewport_resolution',
    'camera_motion_or_bookmark_sequence', 'visibility_layers', 'label_ids',
    'occlusion_or_xray_mode', 'state_or_tick_interval')


def sha256_file(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def registry_card():
    con = sqlite3.connect(
        'file:E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3?mode=ro',
        uri=True)
    try:
        payload = con.execute(
            'SELECT payload FROM state WHERE id=1').fetchone()[0]
    finally:
        con.close()
    return json.loads(payload)['kanban']['cards']['MAT2-M12']


class M12Checks(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None

    # ------------------------------------------------ done_when clause 1
    def test_Y1_two_mechanical_resolutions_one_code_path(self):
        y1 = RECEIPT['Y1_resolution_identity']
        self.assertTrue(y1['Y1a_config_purity']['ok'],
                        'config writes outside configure_resolution')
        self.assertTrue(y1['Y1b_law_digest_equal'])
        identities = y1['Y1b_run_identities']
        self.assertEqual(len(identities), 6)
        for key, ident in identities.items():
            self.assertEqual(ident['law_module_sha256'], ml.SEALED_RIG_SHA)
            self.assertEqual(ident['law_module'], 'MAT2-M11/limb_world.py')
        for kind in ('loaded', 'off', 'released'):
            ids = {identities['%s:%s' % (kind, res)]['schedule_id']
                   for res in RES_ORDER}
            self.assertEqual(len(ids), 1,
                             'schedule id differs across resolutions')
        for res in RES_ORDER:
            audit = y1['Y1c_build_audits'][res]
            self.assertTrue(audit['counts_match_declared'])
        # live re-derivation: a fresh build reproduces the declared counts
        real = lw.load_real_data()
        for res in RES_ORDER:
            world, cfg = ml.build_world(res, lw.off_schedule, 1, 'off',
                                        real=real)
            self.assertEqual(world.rest.shape[0],
                             ml.DECLARED_COUNTS[res]['n_vertices'])
            self.assertEqual(cfg['chord_section_m2'],
                             ml.chord_section_for(res))

    # ------------------------------------------------ done_when clause 2
    def test_Y2_declared_mass_inertia_preserved(self):
        y2 = RECEIPT['Y2_mass_inertia']
        self.assertTrue(y2['Y2a_bitwise_equal'])
        self.assertTrue(y2['Y2b_per_vertex_split_exact'])
        totals = y2['Y2a_totals']
        for res in RES_ORDER:
            self.assertEqual(totals[res]['tissue_total_kg'],
                             lw.LIMB_TISSUE_MASS_KG)
            self.assertEqual(totals[res]['load_mass_kg'],
                             lw.M_LOAD_LIMB_KG)
            self.assertEqual(totals[res]['chain_masses_kg'][0],
                             0.02250842664849005)
        y2c = y2['Y2c_inertia']
        self.assertTrue(y2c['within'])
        self.assertLessEqual(y2c['rel_diff'], ml.I_LOD_REL)
        # live re-derivation of the inertia at the declared referent
        real = lw.load_real_data()
        inertias = {}
        for res in RES_ORDER:
            world, _ = ml.build_world(res, lw.off_schedule, 1, 'off',
                                      real=real)
            inertias[res] = ml.transverse_inertia(world)
        rel = abs(inertias['coarse'] - inertias['reference']) / \
            abs(inertias['reference'])
        self.assertLessEqual(rel, ml.I_LOD_REL)
        self.assertAlmostEqual(rel, y2c['rel_diff'], delta=1e-12)

    def test_Y2d_declared_belt_strength(self):
        y2d = RECEIPT['Y2_mass_inertia']['Y2d_belt_edge_law_audits']
        for res in RES_ORDER:
            row = y2d[res]
            self.assertTrue(row['belt_section_within_declaration'])
            self.assertLessEqual(row['belt_split_abs_error_m2'],
                                 row['belt_split_floor_m2'])
            self.assertTrue(row['chord_k_bitwise_lawform'])
            self.assertTrue(row['edge_k_bitwise_lawform'])
            self.assertAlmostEqual(
                row['chord_section_m2'] *
                ml.DECLARED_COUNTS[res]['n_chords'],
                ml.A_CHORD_TOTAL_M2, delta=ml.BELT_SPLIT_FLOOR_M2)

    # ------------------------------------------------ done_when clause 3
    def test_Y3_interfaces_bitwise_identical(self):
        y3 = RECEIPT['Y3_interfaces']
        self.assertTrue(y3['Y3a_invariants_equal'])
        real = lw.load_real_data()
        digests = {}
        for res in RES_ORDER:
            world, _ = ml.build_world(res, lw.off_schedule, 1, 'off',
                                      real=real)
            digests[res] = ml.digest(ml.interface_invariants(world))
        self.assertEqual(digests['coarse'], digests['reference'])
        # the receipt's stored invariants digest to the same value
        self.assertEqual(
            digests['coarse'],
            ml.digest(y3['Y3a_invariants']['coarse']))

    # ------------------------------------------------ done_when clause 4
    def test_Y4_force_response_within_frozen_tolerances(self):
        y4 = RECEIPT['Y4_force_response']
        for res in RES_ORDER:
            row = y4[res]
            for name, stat in row['statics'].items():
                self.assertTrue(stat['within'],
                                'statics %s %s: resid %r bound %r'
                                % (res, name, stat['residual_n'],
                                   stat['bound_n']))
            self.assertTrue(row['t1_within'])
            self.assertTrue(row['contact_hold_positive'])
            self.assertTrue(row['gap_off_within'])
            self.assertTrue(row['off_contact_bitwise0'])
            self.assertTrue(row['X8_ledger']['within'])
            # window arithmetic re-derivation (constant pairs)
            t1_bound_n = lw.REL * 0.41057777106371945 + \
                lw.K_CONTACT * lw.X_FLOOR_M
            self.assertAlmostEqual(row['t1_window_n'], t1_bound_n,
                                   delta=0.0)
            self.assertLessEqual(abs(row['t1_hold_n'] -
                                     row['t1_static_bound_n']),
                                 t1_bound_n)

    def test_Y5_cross_resolution_agreement(self):
        y5 = RECEIPT['Y5_cross_resolution']
        self.assertTrue(y5['t1_hold']['within'])
        self.assertTrue(y5['contact_hold']['within'])
        self.assertTrue(y5['gap_off']['within'])
        for res in RES_ORDER:
            self.assertTrue(y5['recovery'][res]['within'])

    # ------------------------------------------------ done_when clause 5
    def test_Y6_control_meaning_both_resolutions(self):
        y6 = RECEIPT['Y6_control_meaning']
        for res in RES_ORDER:
            row = y6[res]
            self.assertTrue(row['drop_within'])
            self.assertTrue(row['released_t2_bitwise0'])
            self.assertTrue(row['departure_bit'])
            self.assertGreaterEqual(row['max_departure_m'], ml.BITE_M)
            self.assertTrue(row['double_release_refused'])
            for element in row['distal_landing']:
                self.assertTrue(element['within'],
                                'distal landing %s %s'
                                % (res, element['element']))
            # the T1 drop identity re-derivation (constant pairs)
            w_ur = 0.1898455088713045
            win = lw.REL * w_ur + lw.K_CONTACT * lw.X_FLOOR_M
            self.assertAlmostEqual(row['drop_window_n'], win, delta=0.0)
            self.assertLessEqual(abs(row['t1_drop_n'] - w_ur), win)

    # ------------------------------------------------ done_when clause 6
    def test_Y7_render_mapping_attached_under_large_motion(self):
        y7 = RECEIPT['Y7_render_binding']
        for res in RES_ORDER:
            row = y7[res]
            self.assertTrue(row['coverage_ok'])
            self.assertTrue(row['identity_binding_bitwise'])
            for tick_row in row['per_tick']:
                self.assertTrue(tick_row['ok'])
                self.assertEqual(tick_row['deviation_m'], 0.0)
            # the record must BE large motion (the gate is not vacuous)
            self.assertGreaterEqual(row['max_motion_from_rest_m'],
                                    ml.BITE_M)

    # ------------------------------------------------ done_when clause 7
    def test_Y8_costs_recorded_and_selection_derived(self):
        y8 = RECEIPT['Y8_costs']
        selection = RECEIPT['Y8_selection']
        for res in RES_ORDER:
            row = y8[res]
            for key in ('sim_seconds_per_tick', 'vram_payload_bytes',
                        'limits', 'tick_within_limit',
                        'peak_working_set_bytes', 'off', 'released'):
                self.assertIn(key, row)
            self.assertGreater(row['sim_seconds_per_tick'], 0.0)
            self.assertEqual(
                row['vram_payload_bytes'],
                ml.DECLARED_COUNTS[res]['n_vertices'] * 3 * 8 +
                ml.DECLARED_COUNTS[res]['n_triangles'] * 3 * 4 +
                ml.CAPTURE_VIEWPORT[0] * ml.CAPTURE_VIEWPORT[1] * 3)
            self.assertEqual(row['limits']['tick_budget_s'],
                             ml.TICK_BUDGET_S)
            self.assertEqual(row['limits']['frame_budget_s'],
                             ml.FRAME_BUDGET_S)
            self.assertEqual(row['tick_within_limit'],
                             row['sim_seconds_per_tick'] <=
                             ml.TICK_BUDGET_S)
        # the selection rule re-derivation (argmin over qualified;
        # ties by vram payload)
        qualified = [res for res in RES_ORDER
                     if selection['qualified'][res]]
        self.assertTrue(qualified)
        expected = min(qualified,
                       key=lambda r: (y8[r]['sim_seconds_per_tick'],
                                      y8[r]['vram_payload_bytes']))
        self.assertEqual(selection['selected'], expected)
        # the ranking is a strict order (no vacuous comparison)
        self.assertNotEqual(y8['coarse']['sim_seconds_per_tick'],
                            y8['reference']['sim_seconds_per_tick'])

    # ------------------------------------------------ falsifier / truth
    def test_falsifiers_all_arms_bit_with_clean_controls(self):
        self.assertTrue(FALSIFIERS['all_arms_bit'])
        for arm in ('FB1_stale_render', 'FB2_dropped_ring_remap',
                    'FB3_undeclared_strength_change',
                    'FB4_silent_mass_drift',
                    'FB5_area_independent_forces',
                    'FB6_unaccounted_energy'):
            row = FALSIFIERS[arm]
            self.assertTrue(row['bit'], arm)
            self.assertIn('clean_control', row)
            self.assertTrue(row['clean_control']['within_tolerance'])
        self.assertGreaterEqual(FALSIFIERS['FB1_stale_render']
                                ['tampered_deviation_m'], ml.BITE_M)
        self.assertEqual(FALSIFIERS['FB2_dropped_ring_remap']
                         ['tampered_refusal'],
                         'render_vertex_coverage_refused:coarse')
        self.assertFalse(FALSIFIERS['FB3_undeclared_strength_change']
                         ['tampered_refusal_fires'] is False)

    def test_determinism_byte_identical(self):
        self.assertTrue(DETERMINISM['all_byte_identical'])
        for res in RES_ORDER:
            row = DETERMINISM['per_resolution'][res]
            self.assertTrue(row['byte_identical'])
            self.assertEqual(row['main_dynamic_sha256'],
                             row['rerun_dynamic_sha256'])
        self.assertEqual(RECEIPT['trace_sha256'],
                         sha256_file(HERE / 'experiment_trace.json'))
        self.assertEqual(RECEIPT['criteria_sha256'], CRITERIA_SHA256)

    def test_criteria_identity_across_authorities(self):
        card = registry_card()
        self.assertEqual(card['criteria_sha256'], CRITERIA_SHA256)
        attempt = card['attempts']['22954da7b9704483960b563273e77b4a']
        self.assertEqual(attempt['criteria_sha256'], CRITERIA_SHA256)
        self.assertEqual(attempt['agent_id'], 'arrival-glm53f-m12-w1')
        prereg = (HERE / 'PREREGISTRATION.md').read_text(
            encoding='utf-8')
        self.assertIn(CRITERIA_SHA256, prereg)

    # ------------------------------------------------ capture gates
    def test_capture_bindings_and_state_hash_uniformity(self):
        video = HERE / 'capture' / 'capture_mat2_m12_lod.mkv'
        self.assertTrue(video.exists())
        video_sha = sha256_file(video)
        self.assertEqual(video_sha, CAPTURE_MANIFEST['capture_sha256'])
        self.assertEqual(video_sha, CAPTURE_CONTEXT['capture_sha256'])
        self.assertEqual(video_sha, CAPTURE_RECEIPT['video_sha256'])
        trace_sha = sha256_file(HERE / 'experiment_trace.json')
        self.assertEqual(trace_sha, CAPTURE_RECEIPT['trace_sha256'])
        self.assertEqual(CAPTURE_MANIFEST['task_id'], 'M12')
        self.assertEqual(CAPTURE_CONTEXT['task_id'], 'M12')
        self.assertEqual(CAPTURE_RECEIPT['frame_count'], 24)
        self.assertEqual(len(CAPTURE_MANIFEST['views']), 6)
        for row in CAPTURE_MANIFEST['views']:
            self.assertEqual(row['state_binding']['sha256'], trace_sha)
            self.assertEqual(row['state_binding']['kind'], 'trace')
            self.assertIn(row['mode'], ('diagnostic', 'clean'))
        # state-hash uniformity: the per-resolution subtree shas recorded
        # in the manifest match a live recompute of the committed trace
        trace = json.loads((HERE / 'experiment_trace.json').read_text(
            encoding='utf-8'))
        for res in RES_ORDER:
            live = hashlib.sha256(canonical(
                trace['runs'][res]).encode('utf-8')).hexdigest()
            self.assertEqual(CAPTURE_MANIFEST['resolution_bindings'][res],
                             live)
            self.assertEqual(CAPTURE_RECEIPT['resolution_bindings'][res],
                             live)
        # every diagnostic/clean pair shares the state (pair_id equality
        # of the bound trace sha) -- view toggles preserve the state hash
        pairs = {}
        for row in CAPTURE_MANIFEST['views']:
            pairs.setdefault(row['pair_id'], set()).add(
                row['state_binding']['sha256'])
        for pair_id, shas in pairs.items():
            self.assertEqual(len(shas), 1, pair_id)

    def test_capture_camera_records_carry_registry_fields(self):
        con = sqlite3.connect(
            'file:E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3?mode=ro',
            uri=True)
        try:
            payload = con.execute(
                'SELECT payload FROM state WHERE id=1').fetchone()[0]
        finally:
            con.close()
        profile = json.loads(payload)['kanban']['cards']['MAT2-M12'][
            'spec']['ontology_qualification']['task'][
            'verification_profile']
        for field in profile['camera_required_fields']:
            self.assertIn(field, REQUIRED_CAMERA_FIELDS,
                          'registry field missing from the declared set: '
                          + field)
        cameras = CAPTURE_EVIDENCE['cameras']
        for res in ('coarse', 'reference'):
            for cam_name, rec in cameras[res].items():
                for field in REQUIRED_CAMERA_FIELDS:
                    self.assertIn(field, rec,
                                  '%s/%s missing %s' % (res, cam_name,
                                                        field))

    def test_capture_camera_consistency_and_layers(self):
        proof = CAPTURE_EVIDENCE['camera_consistency_proof']
        self.assertTrue(proof['per_still'])
        for fname, per in proof['per_still'].items():
            for vp in ('whole', 'closeup'):
                self.assertTrue(per[vp]['consistent'])
                self.assertGreater(per[vp]['signed_row_delta_below_minus_above'], 0.0)
            self.assertEqual(per['leakage']['pixels_outside_viewports'], 0)
        layers = CAPTURE_EVIDENCE['layer_presence_proof']
        self.assertEqual(len(layers['per_layer']), 5)
        for layer_name, row in layers['per_layer'].items():
            for res in ('coarse', 'reference'):
                self.assertTrue(row['per_resolution'][res]['present'])
                self.assertGreaterEqual(
                    row['per_resolution'][res]['pixels_present'], 1)
        row_order = CAPTURE_EVIDENCE['row_order_proof']
        self.assertTrue(row_order)
        for fname, row in row_order.items():
            self.assertTrue(row['bmp_rows_match_payload'])
            self.assertTrue(row['topdown_misread_does_not_match'])
        # recompute one committed still's marker order from disk bytes
        still = CAPTURE_EVIDENCE['still_hashes']['frame_00']
        data = (HERE / 'capture' / 'frames' /
                'frame_00.bmp').read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), still['sha256'])

    def test_capture_validator_refuses_unbound_media(self):
        tampered = json.loads(json.dumps(CAPTURE_MANIFEST))
        tampered['capture_sha256'] = 'f' * 64
        con = sqlite3.connect(
            'file:E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3?mode=ro',
            uri=True)
        try:
            payload = con.execute(
                'SELECT payload FROM state WHERE id=1').fetchone()[0]
        finally:
            con.close()
        profile = json.loads(payload)['kanban']['cards']['MAT2-M12'][
            'spec']['ontology_qualification']['task'][
            'verification_profile']
        with self.assertRaises(ValueError) as ctx:
            validate_manifest(tampered, CAPTURE_CONTEXT, profile)
        self.assertIn('capture_identity_mismatch', str(ctx.exception))
        self.assertEqual(CAPTURE_RECEIPT['structurally_valid'], True)


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.discover(
        str(HERE), pattern='test_lod.py')
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    executed = result.testsRun
    skipped = len(result.skipped) + len(
        getattr(result, 'expectedFailures', []))
    failures = len(result.failures)
    errors = len(result.errors)
    print('named checks: %d executed, %d skipped, failures=%d errors=%d'
          % (executed, skipped, failures, errors))
    if skipped or failures or errors:
        sys.exit(1)
    sys.exit(0)
