"""Tests for the MUSCLE-PATHS lane 20260918 derivation.

The derivation is deterministic; these tests pin the pre-registered falsifier
outcomes, the synthetic cylinder-wrap geometry, and the source-pin identity.
A change here means a membrane was re-derived on purpose, not silently.
"""
import hashlib
import json
import tempfile
from pathlib import Path
import unittest

import numpy as np

from tools.science_funnel.validation.muscle_paths_20260918 import \
    derive_muscle_paths as dmp


def derive():
    with tempfile.TemporaryDirectory() as tmp:
        deliverable, path = dmp.derive_all(Path(tmp))
        return deliverable


class ArmPaths(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = derive()

    def test_fd_matches_geometric_exactly_on_straight_paths(self):
        validation = self.out['validation']['arm']
        self.assertEqual(validation['violations'], [])
        self.assertLessEqual(validation['worst_fd_vs_geometric_m'],
                             validation['moment_arm_tolerance_m'])

    def test_arm_muscles_and_poses_complete(self):
        self.assertEqual(len(self.out['arm']['neutral']['muscles']), 39)
        self.assertEqual(len(self.out['arm']['walking']['muscles']), 39)
        for pose in ('neutral', 'walking'):
            for muscle in self.out['arm'][pose]['muscles'].values():
                self.assertTrue(np.isfinite(muscle['length_m']))
                self.assertGreater(muscle['length_m'], 0.0)
                for coord, arm in muscle['moment_arm_fd_m'].items():
                    self.assertTrue(np.isfinite(arm), (pose, coord))

    def test_unresolved_wraps_carry_bounds_only(self):
        for pose in ('neutral', 'walking'):
            for muscle in self.out['arm'][pose]['muscles'].values():
                for wrap in muscle['unresolved_wraps']:
                    self.assertGreaterEqual(wrap['segments_contacting'], 0)
                    bound = wrap['length_lower_bound_error_m']
                    self.assertGreaterEqual(bound, 0.0)
                    # at most 2 contacting segments, largest r_eff is the
                    # RADIUS_SUP ellipsoid major semi-axis 0.025 m
                    self.assertLessEqual(
                        bound, 2 * 0.025 * (np.pi - 2) + 1e-12)

    def test_elbow_moment_arms_physiological_sign_and_scale(self):
        neutral = self.out['arm']['neutral']['muscles']
        self.assertGreater(neutral['bicep_lh']['moment_arm_fd_m']['elbow_flexion'], 0.0)
        self.assertLess(neutral['tricep_lon']['moment_arm_fd_m']['elbow_flexion'], 0.0)
        for name in ('bicep_lh', 'tricep_lon'):
            arm = abs(neutral[name]['moment_arm_fd_m']['elbow_flexion'])
            self.assertGreater(arm, 0.002)
            self.assertLess(arm, 0.05)

    def test_conditional_point_jump_measured_within_bound(self):
        validation = self.out['validation']['arm']
        jumps = validation['conditional_point_jumps']
        self.assertEqual(len(jumps), 1)
        self.assertLessEqual(jumps[0]['jump_m'],
                             validation['conditional_jump_bound_m'])
        self.assertEqual(validation['conditional_jump_violations'], [])

    def test_arm_torque_envelope_sides_disjoint_and_finite(self):
        for pose in ('neutral', 'walking'):
            for coord, env in self.out['arm'][pose]['torque_envelope_N_m'].items():
                self.assertGreaterEqual(env['positive_N_m'], 0.0)
                self.assertLessEqual(env['negative_N_m'], 0.0)

    def test_derivation_is_byte_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            first, path1 = dmp.derive_all(Path(tmp) / 'a')
            second, path2 = dmp.derive_all(Path(tmp) / 'b')
            self.assertEqual(path1.read_bytes(), path2.read_bytes())


class WrapCylinder(unittest.TestCase):
    def setUp(self):
        self.geom = {'name': 'TEST', 'tag': 'WrapCylinder', 'quadrant': 'all',
                     'radius_m': 0.01, 'length_m': 0.04,
                     'to_body': np.eye(4)}

    def test_tangent_wrap_geometry_closes(self):
        p1 = np.array([-0.05, 0.002, 0.001])
        p2 = np.array([0.05, -0.001, -0.001])
        out = dmp.wrap_cylinder(p1, p2, self.geom)
        self.assertIsNotNone(out)
        e1, e2, arc, direction = out
        self.assertGreater(arc, 0.0)
        self.assertLessEqual(arc, np.pi + 1e-9)
        axis = np.array([0., 0., 1.])
        for exit in (e1, e2):
            self.assertAlmostEqual(float(np.linalg.norm(dmp._perp(exit, axis))),
                                   self.geom['radius_m'], places=12)
        chord = float(np.linalg.norm(e2 - e1))
        planar = 2.0 * self.geom['radius_m'] * np.sin(arc / 2.0)
        axial = p2[2] - p1[2]
        self.assertAlmostEqual(chord, np.hypot(planar, axial), places=10)

    def test_no_contact_when_segment_clears_cylinder(self):
        p1 = np.array([-0.05, 0.05, 0.0])
        p2 = np.array([0.05, 0.05, 0.0])
        self.assertIsNone(dmp.wrap_cylinder(p1, p2, self.geom))

    def test_endpoint_inside_is_flagged(self):
        p1 = np.array([0.0, 0.0, 0.0])
        p2 = np.array([0.05, 0.0, 0.0])
        self.assertEqual(dmp.wrap_cylinder(p1, p2, self.geom), 'ENDPOINT_INSIDE')

    def test_wrapped_length_is_smooth_across_small_pose_changes(self):
        p2 = np.array([0.05, -0.001, -0.001])
        lengths = []
        for shift in (-1e-3, 0.0, 1e-3):
            p1 = np.array([-0.05, 0.006 + shift, 0.001])
            out = dmp.wrap_cylinder(p1, p2, self.geom)
            self.assertIsNotNone(out)
            e1, e2, arc, _ = out
            lengths.append(float(np.linalg.norm(e1 - p1))
                           + self.geom['radius_m'] * arc
                           + float(np.linalg.norm(p2 - e2)))
        self.assertLess(abs(lengths[0] - lengths[1]), 1e-3)
        self.assertLess(abs(lengths[1] - lengths[2]), 1e-3)


class HindlimbEstimate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = derive()
        cls.neutral = cls.out['hindlimb']['poses']['neutral']['muscles']

    def test_spanning_filter_matches_anatomy(self):
        spans = {name: record['spanned_joints']
                 for name, record in self.neutral.items()}
        self.assertEqual(spans['SOL'], ['ankle'])
        self.assertEqual(spans['MG'], ['knee', 'ankle'])
        self.assertEqual(spans['VI'], ['knee'])
        self.assertEqual(spans['GMax'], ['hip'])
        self.assertEqual(spans['FDL'], ['ankle', 'mtp'])
        self.assertEqual(spans['BFL'], ['hip'])

    def test_plantarflexors_have_plantar_side_arms(self):
        for name in ('SOL', 'MG', 'LG'):
            arm = self.neutral[name]['moment_arms_m_flexion_positive']['ankle']
            self.assertGreater(arm, 0.0, name)
            self.assertLess(arm, 0.04, name)

    def test_specific_tension_is_derived_with_published_ratios(self):
        sigma = self.out['hindlimb']['specific_tension']
        self.assertGreater(sigma['specific_tension_Pa'], 0.0)
        self.assertEqual(len(sigma['groups']), 8)
        lo, hi = sigma['implied_tension_range_Pa']
        self.assertLessEqual(lo, sigma['specific_tension_Pa'] * 8 ** 0.5)
        self.assertGreaterEqual(hi, sigma['specific_tension_Pa'] / 8 ** 0.5)
        self.assertAlmostEqual(sigma['mass_ratio_mulatta_over_fuscata'],
                               8.0 / 10.038, places=12)

    def test_coverage_falsifier_outcomes_are_pinned(self):
        coverage = self.out['validation']['hindlimb']['coverage']
        for key in ('hip_extension', 'hip_flexion', 'knee_extension',
                    'knee_flexion', 'ankle_plantarflexion',
                    'ankle_dorsiflexion', 'mtp_flexion'):
            self.assertIn(key, coverage)
            self.assertIsNotNone(coverage[key]['ratio'])
        # Frozen honest outcomes of the pre-registered falsifier: the
        # straight-line proxy covers hip/knee-flexion/ankle directions and
        # FAILS knee extension and mtp flexion (no patella, no mtp pulley).
        self.assertGreater(coverage['hip_extension']['ratio'], 1.0)
        self.assertGreater(coverage['knee_flexion']['ratio'], 1.0)
        self.assertGreaterEqual(coverage['ankle_plantarflexion']['ratio'],
                                1.0 - self.out['validation']['hindlimb']['declared_uncertainty_fraction'])
        self.assertLess(coverage['knee_extension']['ratio'], 1.0)
        self.assertLess(coverage['mtp_flexion']['ratio'], 1.0)
        self.assertEqual(self.out['falsifier_verdicts']['hindlimb_torque_coverage'],
                         'falsified: [\'knee_extension\', \'mtp_flexion\']')

    def test_quarantined_source_rows_survive(self):
        quarantined = self.out['quarantined_guimaraes_rows']
        self.assertEqual(len(quarantined), 49)
        mulatta = [q for q in quarantined if 'Macaca mulatta' in q['location']]
        self.assertEqual(len(mulatta), 6)


class SourcePins(unittest.TestCase):
    def test_pinned_bytes_match_receipts(self):
        pins = dmp.source_pins()
        for family, files in pins.items():
            for name, record in files.items():
                self.assertEqual(record['sha256'], record['receipt_sha256'], name)
                self.assertGreater(record['bytes'], 0)

    def test_deliverable_json_round_trips(self):
        out = derive()
        raw = json.dumps(out, indent=1, sort_keys=True) + '\n'
        self.assertEqual(hashlib.sha256(raw.encode()).hexdigest(),
                         hashlib.sha256((json.dumps(
                             json.loads(raw), indent=1,
                             sort_keys=True) + '\n').encode()).hexdigest())


if __name__ == '__main__':
    unittest.main()
