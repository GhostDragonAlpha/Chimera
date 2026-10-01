import copy
import unittest

import visual_capture as v


def fixture(motion=False, orthographic=False):
    ticks = [10, 20] if motion else [10, 10]
    context = {'task_id': 'W10', 'subject_sha256': 'a' * 64, 'run_id': 'capture-test',
               'capture_sha256': 'b' * 64, 'tick_interval': ticks}
    profile = {'id': 'walking', 'kind': 'motion' if motion else 'visible_static',
               'views': ['overview', 'foot close-up'], 'diagnostic_layers': ['contacts'],
               'clean_view_required': True}
    camera = {'frame_id': 'world', 'coordinate_unit': 'm', 'handedness': 'right',
              'orientation_convention': 'quaternion_wxyz_camera_to_frame',
              'forward_axis': '-Z', 'up_axis': '+Y',
              'projection': 'perspective', 'vertical_fov_degrees': 60,
              'near_far_planes': [0.1, 100], 'aspect_ratio': 16 / 9,
              'viewport_resolution': [1920, 1080], 'sample_mode': 'fixed_bookmark',
              'samples': [{'tick': tick, 'position': [0, 0, 5], 'target': [0, 0, 0],
                           'distance_to_target': 5, 'orientation': [1, 0, 0, 0]}
                          for tick in sorted(set(ticks))]}
    if orthographic:
        camera.update(projection='orthographic', orthographic_span=8)
        del camera['vertical_fov_degrees']
    rows = []
    for view_id in profile['views']:
        for mode in ('diagnostic', 'clean'):
            rows.append({'view_id': view_id, 'mode': mode, 'pair_id': view_id + '-pair',
                         'state_binding': {'kind': 'trace' if motion else 'state', 'sha256': 'c' * 64},
                         'artifact_locator': {'kind': 'video', 'seconds': [len(rows) * 2, len(rows) * 2 + 2]}
                         if motion else {'kind': 'image', 'region': 'whole_frame'},
                         'camera': copy.deepcopy(camera),
                         'visibility': {'layers': ['contacts'] if mode == 'diagnostic' else [],
                                        'selected_ids': [], 'label_ids': ['foot-tag'] if mode == 'diagnostic' else [],
                                        'required_subject_ids': ['foot'], 'observed_subject_ids': ['foot'],
                                        'missing_subject_ids': [], 'occlusion_mode': 'depth_tested',
                                        'tag_bindings': [{'label_id': 'foot-tag', 'subject_id': 'foot'}]
                                        if mode == 'diagnostic' else []}})
    manifest = {'schema': v.SCHEMA, **copy.deepcopy(context), 'profile_id': profile['id'], 'views': rows}
    return manifest, context, profile


class VisualCaptureTests(unittest.TestCase):
    def reject(self, mutate, error, motion=False):
        manifest, context, profile = fixture(motion)
        mutate(manifest, context, profile)
        with self.assertRaisesRegex(ValueError, '^' + error + '$'):
            v.validate_manifest(manifest, context, profile)

    def test_valid_static_and_motion_do_not_claim_visual_acceptance_or_mutate(self):
        for motion in (False, True):
            for orthographic in (False, True):
                with self.subTest(motion=motion, orthographic=orthographic):
                    args = fixture(motion, orthographic)
                    before = copy.deepcopy(args)
                    result = v.validate_manifest(*args)
                    self.assertEqual(before, args)
                    self.assertTrue(result['structurally_valid'])
                    self.assertFalse(result['visual_acceptance'])
                    self.assertIn('No pixels', result['limits'])

    def test_identity_and_capture_binding(self):
        for key in ('subject_sha256', 'capture_sha256', 'task_id', 'run_id'):
            with self.subTest(key=key):
                self.reject(lambda m, c, p: m.update({key: 'wrong'}), 'capture_identity_mismatch:' + key)
        self.reject(lambda m, c, p: m.update(profile_id='wrong'), 'capture_profile_mismatch')
        self.reject(lambda m, c, p: m.update(tick_interval=[9, 9]), 'capture_interval_mismatch')

    def test_missing_or_malformed_camera_is_named(self):
        for value in (None, [], 'side view'):
            with self.subTest(value=value):
                self.reject(lambda m, c, p: m['views'][0].update(camera=value), 'camera_missing_or_invalid')

    def test_camera_geometry_refusals(self):
        cases = [
            ('vertical_fov_degrees', 180, 'camera_fov_invalid'),
            ('vertical_fov_degrees', True, 'camera_fov_invalid'),
            ('vertical_fov_degrees', float('nan'), 'camera_fov_invalid'),
            ('vertical_fov_degrees', 10 ** 1000, 'camera_fov_invalid'),
            ('near_far_planes', [1, 1], 'camera_clip_planes_invalid'),
            ('near_far_planes', [0, 10], 'camera_clip_planes_invalid'),
            ('viewport_resolution', [1920, 0], 'camera_resolution_invalid'),
            ('viewport_resolution', [True, 100], 'camera_resolution_invalid'),
            ('aspect_ratio', 1, 'camera_aspect_resolution_mismatch'),
            ('orientation_convention', 'roughly front', 'camera_orientation_convention_invalid'),
            ('coordinate_unit', 'unknown', 'camera_coordinate_unit_invalid'),
            ('frame_id', '', 'camera_frame_missing'),
        ]
        for key, value, error in cases:
            with self.subTest(key=key, value=value):
                self.reject(lambda m, c, p: m['views'][0]['camera'].update({key: value}), error)

    def test_projection_parameters_cannot_be_mixed(self):
        self.reject(lambda m, c, p: m['views'][0]['camera'].update(orthographic_span=5),
                    'camera_projection_parameters_conflict')
        args = fixture(orthographic=True)
        args[0]['views'][0]['camera']['orthographic_span'] = -1
        with self.assertRaisesRegex(ValueError, 'camera_orthographic_span_invalid'):
            v.validate_manifest(*args)

    def test_camera_local_axes_are_explicit_and_independent(self):
        for forward, up in ((None, '+Y'), ('Z', '+Y'), ('+Z', '-Z'), ('+X', '+X')):
            with self.subTest(forward=forward, up=up):
                self.reject(lambda m, c, p: m['views'][0]['camera'].update(
                    forward_axis=forward, up_axis=up), 'camera_local_axes_invalid')

    def test_video_locator_is_numeric_and_has_motion_duration(self):
        for seconds in ([0, 0], [2, 1], [-1, 2], [0, float('inf')], ['start', 'end'], [0]):
            with self.subTest(seconds=seconds):
                self.reject(lambda m, c, p: m['views'][0]['artifact_locator'].update(seconds=seconds),
                            'capture_video_seconds_invalid', True)
        self.reject(lambda m, c, p: m['views'][0].pop('artifact_locator'),
                    'capture_artifact_locator_missing', True)
        self.reject(lambda m, c, p: m['views'][0].update(
            artifact_locator={'kind': 'image', 'region': 'whole_frame'}),
                    'motion_artifact_locator_requires_video', True)

    def test_image_locator_supports_whole_frame_or_pixel_rectangle(self):
        args = fixture()
        args[0]['views'][0]['artifact_locator'] = {
            'kind': 'image', 'region': 'pixel_rectangle', 'pixel_rectangle': [50, 20, 640, 480]}
        self.assertTrue(v.validate_manifest(*args)['structurally_valid'])
        for rectangle in ([0, 0, 0, 10], [-1, 0, 10, 10], [0, 0, True, 10], [0, 0, 1.5, 10]):
            with self.subTest(rectangle=rectangle):
                self.reject(lambda m, c, p: m['views'][0].update(artifact_locator={
                    'kind': 'image', 'region': 'pixel_rectangle', 'pixel_rectangle': rectangle}),
                            'capture_image_rectangle_invalid')

    def test_paired_views_may_use_different_segments_of_same_capture(self):
        args = fixture(True)
        self.assertNotEqual(args[0]['views'][0]['artifact_locator'],
                            args[0]['views'][1]['artifact_locator'])
        self.assertTrue(v.validate_manifest(*args)['structurally_valid'])

    def test_actual_pose_distance_and_unit_quaternion(self):
        cases = [('position', [0, 0], 'camera_position_invalid'),
                 ('target', [0, float('inf'), 0], 'camera_target_invalid'),
                 ('distance_to_target', 4.99, 'camera_target_distance_mismatch'),
                 ('orientation', [2, 0, 0, 0], 'camera_quaternion_not_unit'),
                 ('orientation', [0, 0, 0], 'camera_orientation_invalid')]
        for key, value, error in cases:
            with self.subTest(key=key):
                self.reject(lambda m, c, p: m['views'][0]['camera']['samples'][0].update({key: value}), error)

    def test_motion_requires_interval_and_numeric_trajectory(self):
        self.reject(lambda m, c, p: m['views'][0]['camera'].update(samples='orbit smoothly'),
                    'camera_samples_missing_or_invalid', True)
        self.reject(lambda m, c, p: m['views'][0]['camera']['samples'].pop(),
                    'motion_camera_samples_required', True)
        self.reject(lambda m, c, p: m['views'][0]['camera']['samples'][1].update(tick=19),
                    'camera_samples_do_not_cover_interval', True)
        self.reject(lambda m, c, p: m['views'][0]['camera']['samples'][1].update(tick=10),
                    'camera_sample_tick_invalid', True)
        self.reject(lambda m, c, p: m['views'][0]['camera'].update(samples=[None, None]),
                    'camera_sample_invalid', True)

    def test_trajectory_interpolation_is_explicit(self):
        self.reject(lambda m, c, p: m['views'][0]['camera'].update(sample_mode='sampled_trajectory'),
                    'camera_interpolation_missing', True)
        self.reject(lambda m, c, p: m['views'][0]['camera'].update(
            sample_mode='sampled_trajectory', interpolation='recorded_each_tick'),
                    'camera_recorded_ticks_missing', True)
        args = fixture(True)
        for row in args[0]['views']:
            row['camera'].update(sample_mode='sampled_trajectory',
                                 interpolation='linear_position_target_slerp_orientation')
            row['camera']['samples'][1].update(position=[0, 0, 6], distance_to_target=6)
        self.assertTrue(v.validate_manifest(*args)['structurally_valid'])

    def test_fixed_bookmark_must_remain_fixed(self):
        self.reject(lambda m, c, p: m['views'][0]['camera']['samples'][1].update(
            position=[0, 0, 6], distance_to_target=6), 'fixed_camera_bookmark_changes', True)

    def test_required_views_and_layers_are_not_waived(self):
        self.reject(lambda m, c, p: m['views'].pop(0), 'required_diagnostic_view_missing:overview')
        self.reject(lambda m, c, p: m['views'].pop(1), 'required_clean_view_missing:overview')
        self.reject(lambda m, c, p: p['diagnostic_layers'].append('unrecorded joints'),
                    'required_diagnostic_layers_missing')
        self.reject(lambda m, c, p: m['views'].append(copy.deepcopy(m['views'][0])), 'capture_view_duplicate')

    def test_pairs_bind_same_state_and_camera(self):
        self.reject(lambda m, c, p: m['views'][1]['state_binding'].update(sha256='d' * 64),
                    'capture_pair_state_mismatch')
        self.reject(lambda m, c, p: m['views'][1]['camera'].update(vertical_fov_degrees=65),
                    'capture_pair_camera_mismatch')
        self.reject(lambda m, c, p: m['views'][0]['state_binding'].update(kind='state'),
                    'motion_state_trace_required', True)

    def test_internal_debug_subjects_need_not_be_visible_in_clean_gameplay(self):
        args = fixture()
        args[0]['views'][0]['visibility'].update(
            required_subject_ids=['foot-bone'], observed_subject_ids=['foot-bone'])
        args[0]['views'][0]['visibility']['tag_bindings'][0]['subject_id'] = 'foot-bone'
        self.assertTrue(v.validate_manifest(*args)['structurally_valid'])

    def test_visibility_and_tag_claims_are_explicit(self):
        self.reject(lambda m, c, p: m['views'][0]['visibility'].update(observed_subject_ids=[]),
                    'required_subject_visibility_not_declared')
        self.reject(lambda m, c, p: m['views'][0]['visibility'].update(occlusion_mode='unknown'),
                    'visibility_occlusion_mode_invalid')
        self.reject(lambda m, c, p: m['views'][0]['visibility'].update(tag_bindings=[]),
                    'tag_binding_identity_mismatch')
        self.reject(lambda m, c, p: m['views'][1]['visibility'].update(layers=['skeleton']),
                    'clean_view_contains_diagnostics')

    def test_optional_clean_pair_does_not_create_impossible_requirement(self):
        args = fixture()
        args[2]['clean_view_required'] = False
        args[0]['views'] = [row for row in args[0]['views'] if row['mode'] == 'diagnostic']
        self.assertTrue(v.validate_manifest(*args)['structurally_valid'])

    def test_profile_offline_and_bad_roots_are_refused(self):
        self.reject(lambda m, c, p: p.update(kind='offline'), 'capture_profile_not_visual')
        args = fixture()
        for index, code in ((0, 'capture_manifest_invalid'), (1, 'capture_context_invalid'),
                            (2, 'capture_profile_invalid')):
            changed = list(args)
            changed[index] = []
            with self.assertRaisesRegex(ValueError, code):
                v.validate_manifest(*changed)


if __name__ == '__main__':
    unittest.main()
