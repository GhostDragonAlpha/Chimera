"""MAT2-M10 named checks (run after run_experiments.py modes + capture).

Each check reads the committed receipts and asserts the frozen claims, so
the suite is the executable form of the done_when clauses:
  X1 directional contraction + controls (A1.4)
  X2 blocked-load reaction (monotone, sublinear, power-off)
  X3 Maxwell reciprocity (A1.9 fixed-p two-load family)
  X4 load-line superposition
  X5 work/ledger/power-off (cumulative no-source gate)
  X6 pressure limits
  X7 determinism (byte-identical dynamic_run)
  FB1-FB6 falsifier arms bite with clean controls (P1)
  P4 capture gate: ffmpeg decode == committed stills under identity ONLY
     (explicit transform list identity/vflip/hflip/rot180) + stdlib
     row-order proof (cameras.json row_order_proof)
  G7 registry identity: criteria sha across prereg/receipt/capture
Run:  python -B test_actuator_world.py
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
CAPTURE = HERE / 'capture'
FFMPEG_CANDIDATES = ('ffmpeg',)


def load(name):
    path = HERE / name
    if not path.exists():
        raise FileNotFoundError(name + ' (run the experiment modes first)')
    return json.loads(path.read_text(encoding='utf-8'))


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False)


class X1Directional(unittest.TestCase):
    def test_directional_contraction_and_controls(self):
        b = load('experiment_receipt.json')
        self.assertTrue(b['X1_pass'])
        self.assertLessEqual(b['X1_directional']['delta_gap']['braid'],
                             aw_window('gap_braid_max'))
        self.assertGreaterEqual(b['X1_directional']['delta_gap']['belt'],
                                aw_window('gap_belt_min'))
        self.assertGreaterEqual(b['X1_directional']['delta_gap']['iso'],
                                aw_window('gap_iso_min'))
        self.assertTrue(b['X1_directional']['X1d_dir_braid_vs_iso'])
        self.assertTrue(b['X1_directional']['X1d_dir_belt_vs_iso'])
        self.assertTrue(b['X1e_monotonicity']['ordered'])


class X2Blocked(unittest.TestCase):
    def test_blocked_reaction_family(self):
        b = load('experiment_receipt.json')
        self.assertTrue(b['X2_pass'])
        self.assertTrue(b['X2_blocked']['reaction_sign_positive'])
        self.assertTrue(b['X2_blocked']['monotone_nondecreasing'])
        self.assertTrue(b['X2_blocked']['sublinear_low_p'])
        self.assertTrue(b['X2_blocked']['magnitude_window'])
        self.assertTrue(b['X2d_power_off']['within'])


class X3Reciprocity(unittest.TestCase):
    def test_maxwell_reciprocity_fixed_p(self):
        b = load('experiment_receipt.json')
        self.assertTrue(b['X3_pass'])
        for level, row in b['X3_reciprocity'].items():
            self.assertLessEqual(row['relative_disagreement'],
                                 aw_window('reciprocity_rel'), level)


class X4Superposition(unittest.TestCase):
    def test_load_line_superposition(self):
        b = load('experiment_receipt.json')
        self.assertTrue(b['X4_pass'])
        self.assertTrue(b['X4_superposition']['tie_follow_within'])


class X5Work(unittest.TestCase):
    def test_work_ledger_lift_poweroff(self):
        b = load('experiment_receipt.json')
        self.assertTrue(b['X5_pass'])
        x5 = b['X5_work']
        self.assertTrue(x5['lift_positive'])
        self.assertTrue(x5['lift_within'])
        self.assertTrue(x5['eta_within'])
        self.assertTrue(x5['power_identity_within'])
        self.assertTrue(x5['power_off_within'])
        self.assertTrue(x5['tie_return_within'])
        self.assertLessEqual(x5['traction_ratio_worst'],
                             aw_window('traction_ratio_rel'))
        # per-phase keyed counts (P6)
        self.assertEqual(x5['phase_state_counts']['P0_presettle'], 200)
        self.assertEqual(x5['phase_state_counts']['B_hold'], 700)
        self.assertEqual(x5['phase_state_counts']['D_settled_off'], 200)


class X6Limits(unittest.TestCase):
    def test_pressure_limits_fire(self):
        b = load('experiment_receipt.json')
        self.assertTrue(b['X6_pass'])
        for name, row in b['X6_limits']['refusals'].items():
            self.assertTrue(row['fired'], name)


class X7Determinism(unittest.TestCase):
    def test_trace_byte_identity(self):
        b = load('determinism_receipt.json')
        self.assertTrue(b['X2_trace_byte_identical'])
        self.assertTrue(b['X2_pass'])


class FalsifierArms(unittest.TestCase):
    def test_all_arms_bite_with_clean_controls(self):
        f = load('falsifier_receipt.json')
        self.assertTrue(f['all_arms_bit'])
        for name in ('FB1_activation_writes_poses',
                     'FB2_isotropic_inflation',
                     'FB3_work_without_source',
                     'FB4_area_independent_forces',
                     'FB5_clipped_load_path',
                     'FB6_hidden_support'):
            self.assertTrue(f[name]['bit'], name)
            self.assertIn('clean_control', f[name], name)
            self.assertTrue(f[name]['clean_control']['within_tolerance'],
                            name)
            self.assertIn('guard', f[name]['clean_control'], name)


class G7RegistryIdentity(unittest.TestCase):
    def test_criteria_sha_identity(self):
        expected = '5e7560caa9efae9ec819c9127ab6ee6e7016e134bdf97e525f06cfedee31190c'
        for name in ('experiment_receipt.json', 'falsifier_receipt.json',
                     'determinism_receipt.json', 'regression_receipt.json',
                     'capture_validation_receipt.json'):
            doc = load(name)
            self.assertEqual(doc.get('criteria_sha256'), expected, name)
        # frozen in the preregistration text
        prereg = (HERE / 'PREREGISTRATION.md').read_text(encoding='utf-8')
        self.assertIn(expected, prereg)
        # and the attempt registry row (read-only)
        import sqlite3
        con = sqlite3.connect(
            'file:E:/ChimeraWork/monkey-coordination/'
            'agent_slots.sqlite3?mode=ro', uri=True)
        try:
            reg = json.loads(con.execute(
                'SELECT payload FROM state WHERE id=1').fetchone()[0])
        finally:
            con.close()
        card = reg['kanban']['cards']['MAT2-M10']
        self.assertEqual(card.get('criteria_sha256'), expected)
        attempt = card['attempts']['02cc9dbda6f3494f8d8de36e20b94c0f']
        self.assertEqual(attempt.get('criteria_sha256'), expected)


class P4CaptureGate(unittest.TestCase):
    """Transform-list capture gate (F04 heritage): decoded video frames ==
    committed stills under IDENTITY only; identity diff 0 px, every other
    transform > 0 px. Independently recomputable indices."""

    STILL_INDICES = (0, 8, 10, 16)  # frame indices (video frames)

    def _decode_frames(self):
        video = CAPTURE / 'capture' / 'capture_mat2_m10_jack.mkv'
        if not video.exists():
            self.skipTest('capture video not present')
        width, height = 960, 540
        proc = subprocess.run(
            ['ffmpeg', '-v', 'error', '-i', str(video),
             '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
            capture_output=True, timeout=600)
        self.assertEqual(proc.returncode, 0)
        data = proc.stdout
        frame_bytes = width * height * 3
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

    def test_identity_only_match(self):
        import numpy as np
        frames = self._decode_frames()
        self.assertEqual(len(frames), 18)
        evidence = load(str(CAPTURE / 'evidence' / 'cameras.json'))
        recorded = evidence['frame_raw_sha256']
        for fi in self.STILL_INDICES:
            still = self._still_rgb(fi)
            payload = still.tobytes()
            # the committed still equals the recorded frame payload
            self.assertEqual(
                hashlib.sha256(payload).hexdigest(),
                recorded['frame_%02d' % fi]['raw_payload_sha256'], fi)
            decoded = np.frombuffer(frames[fi], dtype=np.uint8)
            identity = int(np.count_nonzero(
                decoded.reshape(still.shape) != still))
            self.assertEqual(identity, 0, 'identity diff at %d' % fi)
            vflip = np.frombuffer(frames[fi][::-1], dtype=np.uint8)
            hflip = np.frombuffer(b''.join(
                frames[fi][y * 960 * 3:(y + 1) * 960 * 3][::-1]
                for y in range(540)), dtype=np.uint8)
            rot180 = np.frombuffer(frames[fi][::-1], dtype=np.uint8)
            self.assertGreater(int(np.count_nonzero(
                vflip.reshape(still.shape) != still)), 0, 'vflip %d' % fi)
            self.assertGreater(int(np.count_nonzero(
                hflip.reshape(still.shape) != still)), 0, 'hflip %d' % fi)
            self.assertGreater(int(np.count_nonzero(
                rot180.reshape(still.shape) != still)), 0, 'rot180 %d' % fi)

    def test_row_order_proof(self):
        evidence = load(str(CAPTURE / 'evidence' / 'cameras.json'))
        proof = evidence['row_order_proof']
        self.assertTrue(len(proof) >= 3)
        for fname, row in proof.items():
            self.assertTrue(row['bmp_rows_match_payload'], fname)
            self.assertTrue(row['topdown_misread_does_not_match'], fname)


def aw_window(key):
    sys.path.insert(0, str(HERE))
    import actuator_world as aw
    return aw.WIN[key]


if __name__ == '__main__':
    unittest.main()
