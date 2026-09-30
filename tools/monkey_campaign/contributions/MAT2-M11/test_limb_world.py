"""MAT2-M11 named checks (run after run_experiments.py modes + capture).

One check class per done_when clause (prereg section 7 gate map):
  same law on two distinct shapes, no shape-specific motion code
      -> X1a AST audit, X1b run identity, X1c synthetic statics
  then on the selected monkey limb
      -> X2a real-mass, X2b real-frame, X2c real-attachment, X2d ports
  tissue-to-bone-to-foot-to-ground transmission
      -> X3 whole-system + stage identities + hold contact active
  activation-off control
      -> X4 bitwise-0 vs positive discriminator + recovery
  connection-removal control
      -> X5 release of T2 at the declared tick
  pressure limits / power-off
      -> X6 the four M03 named refusals
  determinism / energy honesty
      -> X7 byte identity; X8 settled cumulative ledger
  falsifiers
      -> FB1-FB6 bite with clean controls (P1)
  capture (material/motion profile)
      -> P4 transform-list gate, stdlib row order, camera consistency,
         per-layer pixel presence, G8 single capture identity
  registry identity (G7)
      -> criteria sha across prereg, receipts and the registry card row

Run:  python -B test_limb_world.py
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sqlite3
import subprocess
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
CAPTURE = HERE / 'capture'

CRITERIA = ('0588c4140a9968160cd640507e02a5b0cefefa6238ff3107de4c232'
            'f0d7ea72e')
ATTEMPT = '8de1349ae67840fc8b8a15fb647c5e4a'


def load(name):
    path = HERE / name
    if not path.exists():
        raise FileNotFoundError(name + ' (run the experiment modes first)')
    return json.loads(path.read_text(encoding='utf-8'))


def lw():
    sys.path.insert(0, str(HERE))
    import limb_world
    return limb_world


class SameLawTwoShapes(unittest.TestCase):
    def test_x1a_x1b_x1c(self):
        b = load('experiment_receipt.json')
        self.assertTrue(b['X1_pass'])
        self.assertTrue(b['X1_shape_identity']['X1a_ast']['ok'])
        self.assertEqual(
            b['X1_shape_identity']['X1a_ast']['violations'], [])
        self.assertTrue(
            b['X1_shape_identity']['X1b_run_identity']['all_identical'])
        for shape in ('icosphere', 'cube'):
            self.assertTrue(
                b['X1_shape_identity']['X1c_synthetic_statics'][shape]
                ['X1c_within_all_windows'], shape)


class RealLimbAssembly(unittest.TestCase):
    def test_x2_mass_frames_attachments_ports(self):
        b = load('experiment_receipt.json')
        self.assertTrue(b['X2_pass'])
        x2 = b['X2_real_data']
        self.assertTrue(x2['X2a_mass']['bitwise_matches_pinned_b03'])
        self.assertEqual(x2['X2a_mass']['hand_counted_mass_kg'], 0.0)
        for k, v in x2['X2b_frames']['audit'][
                'transform_residuals_m'].items():
            self.assertLessEqual(v, 1e-12, k)
        self.assertTrue(x2['X2c_attachments']
                        ['all_sites_are_a06_attachment_records'])
        self.assertEqual(x2['X2c_attachments']['tie_count'], 4)
        self.assertEqual(x2['X2d_ports']['port_count'], 8)
        self.assertEqual(
            len(x2['X2d_ports']['unresolved_terminals']), 1)
        self.assertEqual(x2['X2d_ports']['unresolved_terminals'][0]
                         ['status'], 'explicitly_unresolved_terminal')


class Transmission(unittest.TestCase):
    def test_x3_whole_system_and_stage(self):
        b = load('experiment_receipt.json')
        self.assertTrue(b['X3_pass'])
        for shape, wins in b['X3_statics']['per_shape'].items():
            for label, row in wins.items():
                self.assertTrue(row['within'], (shape, label))
        stage = b['X3_statics']['stage_limb']
        for label in ('HOLD', 'OFF'):
            self.assertTrue(stage[label]['foot_identity_within'], label)
            self.assertTrue(stage[label]['chain_top_identity_within'],
                            label)
        # contact active in the loaded window (penetration > 0, force > 0)
        self.assertGreater(stage['HOLD']['f_contact_n'], 0.0)


class ActivationOff(unittest.TestCase):
    def test_x4_bitwise_discriminator_and_recovery(self):
        b = load('experiment_receipt.json')
        self.assertTrue(b['X4_pass'])
        for shape, row in b['X4_activation_off'].items():
            self.assertTrue(row['p0_contact_bitwise_zero'], shape)
            self.assertTrue(row['off_contact_bitwise_zero'], shape)
            self.assertTrue(
                row['dedicated_off_run_contact_bitwise_zero'], shape)
            self.assertTrue(row['hold_contact_positive'], shape)
            self.assertTrue(row['recovery_within'], shape)
            self.assertLessEqual(row['recovery_gap_m'],
                                 row['recovery_window_m'], shape)


class ConnectionRemoval(unittest.TestCase):
    def test_x5_release_t2(self):
        b = load('experiment_receipt.json')
        self.assertTrue(b['X5_pass'])
        x5 = b['X5_connection_removal']
        self.assertEqual(x5['release_tie_id'], 'T2')
        self.assertEqual(x5['release_tick'], 450)
        self.assertTrue(x5['released_tie_tension_bitwise_zero'])
        self.assertGreaterEqual(x5['max_departure_m'],
                                x5['bite_window_m'])
        self.assertTrue(x5['t1_drop_within'])
        self.assertTrue(x5['distal_pickup_within'])
        self.assertTrue(x5['double_release_refusal_fired'])
        self.assertEqual(x5['double_release_refusal_code'],
                         'release_of_unbound_bond')
        self.assertTrue(x5['clean_control']['within_tolerance'])


class PressureLimits(unittest.TestCase):
    def test_x6_named_refusals_fire(self):
        b = load('experiment_receipt.json')
        self.assertTrue(b['X6_pass'])
        for name, row in b['X6_limits']['refusals'].items():
            self.assertTrue(row['fired'], name)


class Determinism(unittest.TestCase):
    def test_x7_byte_identity(self):
        b = load('determinism_receipt.json')
        self.assertTrue(b['X7_trace_byte_identical'])
        self.assertTrue(b['X7_pass'])


class EnergyHonesty(unittest.TestCase):
    def test_x8_settled_cumulative_gate(self):
        b = load('experiment_receipt.json')
        self.assertTrue(b['X8_pass'])
        for shape, row in b['X8_ledger'].items():
            self.assertTrue(row['settled_within'], shape)
            self.assertLessEqual(abs(row['settled_cumulative_residual_j']),
                                 row['cumulative_bound_j'], shape)
            # the full-run residual is REPORTED (never hidden), not gated
            self.assertIsInstance(row['full_run_residual_j'], float)


class FalsifierArms(unittest.TestCase):
    def test_all_arms_bite_with_clean_controls(self):
        f = load('falsifier_receipt.json')
        self.assertTrue(f['all_arms_bit'])
        for name in ('FB1_overlay_driven_motion',
                     'FB2_area_independent_forces',
                     'FB3_clipped_load_path', 'FB4_hidden_support',
                     'FB5_unaccounted_energy',
                     'FB6_synthetic_port_standin'):
            self.assertTrue(f[name]['bit'], name)
        self.assertEqual(set(f['arms']),
                         {n + '_fires' for n in (
                             'FB1_overlay_driven_motion',
                             'FB2_area_independent_forces',
                             'FB3_clipped_load_path', 'FB4_hidden_support',
                             'FB5_unaccounted_energy',
                             'FB6_synthetic_port_standin')})
        for flag, fired in f['arms'].items():
            self.assertTrue(fired, flag)
            self.assertIn('clean_control', f[name], name)
            self.assertTrue(f[name]['clean_control']['within_tolerance'],
                            name)
            self.assertIn('guard', f[name]['clean_control'], name)


class ReceiptSchemas(unittest.TestCase):
    """batch-gate law: every bank *receipt*.json carries a
    chimera.*.vN schema string (receipt-semantics co-change law)."""

    EXPECTED = {
        'experiment_receipt.json': 'chimera.m11.experiment_receipt.v1',
        'falsifier_receipt.json': 'chimera.m11.falsifier_receipt.v1',
        'determinism_receipt.json': 'chimera.m11.determinism_receipt.v1',
        'regression_receipt.json': 'chimera.m11.regression_receipt.v1',
    }

    def test_bank_receipts_carry_schema(self):
        import re
        for name, schema in self.EXPECTED.items():
            doc = load(name)
            self.assertEqual(doc.get('schema'), schema, name)
            self.assertRegex(schema, r'^chimera\.[a-z0-9_]+(\.[a-z0-9_]+)*'
                                     r'\.v\d+$')


class G7RegistryIdentity(unittest.TestCase):
    def test_criteria_sha_identity(self):
        expected = CRITERIA
        for name in ('experiment_receipt.json', 'falsifier_receipt.json',
                     'determinism_receipt.json',
                     'regression_receipt.json'):
            doc = load(name)
            self.assertEqual(doc.get('criteria_sha256'), expected, name)
            self.assertEqual(doc.get('attempt_id'), ATTEMPT, name)
        prereg = (HERE / 'PREREGISTRATION.md').read_text(
            encoding='utf-8')
        self.assertIn(expected, prereg)
        con = sqlite3.connect(
            'file:E:/ChimeraWork/monkey-coordination/'
            'agent_slots.sqlite3?mode=ro', uri=True)
        try:
            reg = json.loads(con.execute(
                'SELECT payload FROM state WHERE id=1').fetchone()[0])
        finally:
            con.close()
        card = reg['kanban']['cards']['MAT2-M11']
        self.assertEqual(card.get('criteria_sha256'), expected)
        attempt = card['attempts'][ATTEMPT]
        self.assertEqual(attempt.get('criteria_sha256'), expected)


class P4CaptureGate(unittest.TestCase):
    """Transform-list capture gate (F04 heritage): decoded video frames ==
    committed stills under IDENTITY only; identity diff 0 px, every other
    transform > 0 px. Plus the stdlib row-order proof."""

    STILL_INDICES = (0, 4, 10, 16)
    W, H = 960, 540

    def _decode_frames(self):
        video = CAPTURE / 'capture' / 'capture_mat2_m11_limb.mkv'
        if not video.exists():
            self.skipTest('capture video not present')
        proc = subprocess.run(
            ['ffmpeg', '-v', 'error', '-i', str(video),
             '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
            capture_output=True, timeout=600)
        self.assertEqual(proc.returncode, 0)
        data = proc.stdout
        frame_bytes = self.W * self.H * 3
        self.assertEqual(len(data) % frame_bytes, 0)
        return [data[i * frame_bytes:(i + 1) * frame_bytes]
                for i in range(len(data) // frame_bytes)]

    def _still_rgb(self, frame_index):
        import numpy as np
        sys.path.insert(0, str(HERE))
        from render_run import read_bmp_rgb
        path = CAPTURE / 'frames' / ('frame_%02d.bmp' % frame_index)
        self.assertTrue(path.exists(), str(path))
        return read_bmp_rgb(path.read_bytes())

    def test_identity_only_match_and_row_order(self):
        import numpy as np
        frames = self._decode_frames()
        self.assertEqual(len(frames), 18)
        evidence = load(str(CAPTURE / 'evidence' / 'capture_evidence.json'))
        recorded = evidence['frame_raw_sha256']
        for fi in self.STILL_INDICES:
            still = self._still_rgb(fi)
            payload = still.tobytes()
            self.assertEqual(
                hashlib.sha256(payload).hexdigest(),
                recorded['frame_%02d' % fi]['raw_payload_sha256'], fi)
            decoded = np.frombuffer(frames[fi], dtype=np.uint8)
            identity = int(np.count_nonzero(
                decoded.reshape(still.shape) != still))
            self.assertEqual(identity, 0, 'identity diff at %d' % fi)
            w, h = self.W, self.H
            vflip = np.frombuffer(frames[fi][::-1], dtype=np.uint8)
            hflip = np.frombuffer(b''.join(
                frames[fi][y * w * 3:(y + 1) * w * 3][::-1]
                for y in range(h)), dtype=np.uint8)
            self.assertGreater(int(np.count_nonzero(
                vflip.reshape(still.shape) != still)), 0, 'vflip %d' % fi)
            self.assertGreater(int(np.count_nonzero(
                hflip.reshape(still.shape) != still)), 0, 'hflip %d' % fi)
        for fname, row in evidence['row_order_proof'].items():
            self.assertTrue(row['bmp_rows_match_payload'], fname)
            self.assertTrue(row['topdown_misread_does_not_match'], fname)


class CameraConsistencyGate(unittest.TestCase):
    """M10 F2 heritage: signed row order per perspective viewport
    (declared-above marker above the declared-below marker under the
    declared up), declared close-up content, zero cross-viewport leakage,
    independently recomputed from the committed BMP stills."""

    RECTS = {'whole': (4, 4, 479, 263), 'side': (484, 4, 959, 263),
             'front': (4, 268, 479, 527), 'closeup': (484, 268, 959, 527)}
    CLAMP = (255, 70, 70)
    LOAD = (60, 60, 225)
    POLE = (255, 200, 60)
    CONTACT = (0, 220, 120)
    TIE = (0, 170, 255)

    def _marker(self, arr, rect, rgb):
        import numpy as np
        x0, y0, x1, y1 = rect
        sub = arr[y0:y1 + 1, x0:x1 + 1]
        mask = np.all(sub == np.array(rgb, dtype=np.uint8), axis=2)
        rows, _ = np.nonzero(mask)
        return rows

    def test_signed_row_order_content_and_leakage(self):
        import numpy as np
        evidence = load(str(CAPTURE / 'evidence' / 'capture_evidence.json'))
        proof = evidence['camera_consistency_proof']
        self.assertIsNotNone(proof)
        for fname, row in proof['per_still'].items():
            for vp in ('whole', 'closeup'):
                self.assertTrue(row[vp]['consistent'], (fname, vp))
                self.assertGreater(
                    row[vp]['signed_row_delta_below_minus_above'],
                    0.0, (fname, vp))
            self.assertEqual(
                row['leakage']['pixels_outside_viewports'], 0, fname)
        sys.path.insert(0, str(HERE))
        from render_run import read_bmp_rgb
        for fname in sorted(proof['per_still']):
            path = CAPTURE / 'frames' / (fname + '.bmp')
            self.assertTrue(path.exists(), str(path))
            arr = read_bmp_rgb(path.read_bytes())
            for vp, above_rgb in (('whole', self.CLAMP),
                                  ('closeup', self.POLE)):
                above = self._marker(arr, self.RECTS[vp], above_rgb)
                below = self._marker(arr, self.RECTS[vp], self.LOAD
                                     if vp == 'whole' else self.CONTACT)
                self.assertGreater(above.size, 0, (fname, vp, 'above'))
                self.assertGreater(below.size, 0, (fname, vp, 'below'))
                self.assertLess(float(above.mean()), float(below.mean()),
                                (fname, vp, 'row order'))
            tie = self._marker(arr, self.RECTS['closeup'], self.TIE)
            self.assertGreater(tie.size, 0, (fname, 'closeup tie'))
            mask = np.all(arr == np.array(self.TIE, dtype=np.uint8),
                          axis=2)
            allowed = np.zeros_like(mask)
            for rect in self.RECTS.values():
                x0, y0, x1, y1 = rect
                allowed[y0:y1 + 1, x0:x1 + 1] = True
            self.assertEqual(
                int(np.count_nonzero(mask & ~allowed)), 0,
                (fname, 'viewport leakage'))


class LayerPresenceGate(unittest.TestCase):
    """Prereg section 8: each declared diagnostic layer, rendered ALONE,
    must place >= 1 pixel of a layer key color (probe receipt)."""

    def test_layer_presence_proof(self):
        evidence = load(str(CAPTURE / 'evidence' / 'capture_evidence.json'))
        proof = evidence['layer_presence_proof']
        sys.path.insert(0, str(HERE))
        from render_run import LAYERS
        layers = LAYERS
        for idx, layer in enumerate(layers):
            row = proof['per_layer'][layer]
            self.assertTrue(row['present'], layer)
            self.assertEqual(row['layer_index'], idx)
            self.assertGreaterEqual(row['pixels_present'], 1, layer)
        self.assertEqual(len(proof['per_layer']), 5)


class G8SingleCaptureIdentity(unittest.TestCase):
    """Exactly one gate-bound capture identity: ONE video; every view row
    an artifact of it; every view row carries the same state_binding sha
    (the canonical dynamic_run trace sha)."""

    def test_single_video_binding(self):
        manifest = load('capture_manifest.json')
        context = load('capture_context.json')
        crec = load('capture_validation_receipt.json')
        videos = [v for v in manifest['views']
                  if v['artifact_locator']['kind'] == 'video']
        self.assertEqual(len(manifest['views']), 6)
        self.assertEqual(len(videos), 6)
        locators = {str(v['artifact_locator']) for v in videos}
        self.assertEqual(len(locators), 1)
        bindings = {v['state_binding']['sha256']
                    for v in manifest['views']}
        self.assertEqual(len(bindings), 1)
        trace_sha = hashlib.sha256(
            (HERE / 'experiment_trace.json').read_bytes()).hexdigest()
        self.assertEqual(list(bindings)[0], trace_sha)
        self.assertEqual(manifest['capture_sha256'],
                         context['capture_sha256'])
        self.assertEqual(crec.get('video_sha256'),
                         manifest['capture_sha256'])
        self.assertEqual(manifest['task_id'], 'M11')
        self.assertEqual(context['task_id'], 'M11')


def _default(o):
    import numpy as np
    if isinstance(o, (np.floating, np.integer)):
        return float(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError(type(o))


if __name__ == '__main__':
    unittest.main()
