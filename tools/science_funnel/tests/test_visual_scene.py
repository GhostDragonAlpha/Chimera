"""Falsifier tests for the dyad visual-verification harness (visual_scene).

No live engine is touched: the renderers and judgement templates are pure
functions of a numeric state, so the F1 determinism and F3 wrong-state-catch
falsifiers are exercisable on synthetic states anchored to the same pinned
FK model the engine runs.
"""
import copy
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from tools.science_funnel.visual_scene import (  # noqa: E402
    SCENARIOS, Skeleton, checks_contact_press, render_energy, render_state,
    snapshot_of, _fmt)
from tools.science_funnel.visual_proof import read_png  # noqa: E402

PLANE_Y = 0.35
RADIUS_M = 0.007
HAND_LOCAL = [0.001777657291666502, -0.036138621093750024,
              0.002310406250000002]


def synthesize_press_state(skeleton, elbow_deg=None, shift_y=0.0,
                           reaction=0.8, mu=0.0, mode='free'):
    """A self-consistent press state from the REAL pinned FK: the hand sits
    exactly at the plane (gap 0, elbow bisected on the FK) unless shift_y
    lowers it."""
    if elbow_deg is None:
        lo, hi = 20.5, 60.0  # 20.5 penetrates, 60 clears (measured)
        for _ in range(64):
            mid = (lo + hi) / 2
            p = skeleton.points(20.0, mid)
            g = p['hand_point'][1] + RADIUS_M - PLANE_Y
            if g < 0:
                lo = mid
            else:
                hi = mid
        elbow_deg = (lo + hi) / 2
    pts = skeleton.points(20.0, elbow_deg)
    hand = [float(v) for v in pts['hand_point']]
    hand[1] += shift_y
    gap = hand[1] + RADIUS_M - PLANE_Y
    return {
        'sim_time_s': 12.0, 'ticks': 3600,
        'joints': [
            {'name': 'shoulder_flexion', 'angle_deg': 20.0,
             'target_deg': 20.0, 'speed_rad_s': 0.0,
             'motor_torque_N_m': 0.0, 'gravity_torque_N_m': 0.0,
             'limit_reaction_N_m': 0.0, 'drive_enabled': True,
             'torque_limit_N_m': 0.6},
            {'name': 'elbow_flexion', 'angle_deg': elbow_deg,
             'target_deg': 20.0, 'speed_rad_s': 0.0,
             'motor_torque_N_m': 0.0, 'gravity_torque_N_m': 0.0,
             'limit_reaction_N_m': 0.0, 'drive_enabled': True,
             'torque_limit_N_m': 0.3},
        ],
        'config': {'shoulder_target_deg': 20.0, 'elbow_target_deg': 20.0,
                   'contact_enabled': True, 'contact_friction': mu,
                   'power': True},
        'mode': 'native_coupled_arm', 'epoch': 1,
        'contact': {'enabled': True, 'friction': mu > 0, 'friction_mu': mu,
                    'grasp': False, 'plane_world_up_m': PLANE_Y,
                    'proxy_radius_m': RADIUS_M, 'gap_m': gap,
                    'closing_speed_m_s': 0.0, 'touching': abs(gap) <= 1e-5,
                    'jacobian_m_per_rad': [-0.1, -0.3],
                    'reaction_N': reaction, 'impact_impulse_N_s': 0.001,
                    'impact_heat_J': 0.01, 'friction_force_N': 0.0,
                    'friction_impact_impulse_N_s': 0.0, 'slip_speed_m_s': 0.0,
                    'mode': mode,
                    'generalized_reaction_N_m': [0.0, -reaction * 0.3]},
        'body': {'position_m': hand, 'velocity_m_s': [0.0, 0.0, 0.0],
                 'radius_m': RADIUS_M},
        'energy': {'kinetic_J': 0.0, 'gravitational_J': -0.02,
                   'potential_reference': 'reset pose',
                   'mechanical_J': -0.02, 'actuator_work_J': 0.1,
                   'external_work_J': 0.0, 'damping_heat_J': 0.08,
                   'impact_heat_J': 0.01, 'contact_impact_heat_J': 0.01,
                   'friction_heat_J': 0.0, 'brake_heat_J': 0.0,
                   'battery_J': 1.9, 'battery_initial_J': 2.0,
                   'battery_usable': True, 'balance_error_J': 0.0,
                   'store_balance_error_J': 0.0},
        'coupling': {'mass_matrix_kg_m2': [[0.01, 0.002], [0.002, 0.004]],
                     'bias_torque_N_m': [0.0, 0.0]},
        'scene_sha256': '0' * 64,
    }


def make_series(hand_x0, hand_x1, slips, heat0, heat1, n=8):
    """A settle-poll series shaped like the measured live ones."""
    out = []
    for i in range(n):
        f = i / (n - 1)
        out.append({'sim_time_s': float(i), 'ticks': i * 75,
                    'hand_x_m': hand_x0 + (hand_x1 - hand_x0) * f,
                    'hand_y_m': 0.343, 'gap_m': -5e-6, 'reaction_N': 1.4,
                    'slip': slips[0] if i == 0 else slips[1],
                    'friction_heat_J': heat0 + (heat1 - heat0) * f,
                    'mode': 'stick', 't_wall': 0.0, 'shoulder_deg': 21.0,
                    'elbow_deg': 34.4})
    return out


class VisualSceneTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skeleton = Skeleton()

    def test_fmt_never_raises_and_fits_font(self):
        for value in (0.0, -0.0, 1e-12, -3.5e-7, 12.3456, 2.0, -1e9):
            text = _fmt(value, 5)
            self.assertIsInstance(text, str)
            self.assertLessEqual(len(text), 18)

    def test_render_is_deterministic_and_wellformed(self):
        scenario = next(s for s in SCENARIOS if s['key'] == 'contact_press')
        snap = snapshot_of(scenario, synthesize_press_state(self.skeleton))
        png1 = render_state(scenario, snap, self.skeleton)
        png2 = render_state(scenario, snap, self.skeleton)
        self.assertEqual(png1, png2, 'render must be a pure function of snap')
        width, height, rgb = read_png(png1)
        self.assertEqual((width, height, len(rgb)), (720, 560, 720 * 560 * 3))
        bars1 = render_energy(snap)
        bars2 = render_energy(snap)
        self.assertEqual(bars1, bars2)
        read_png(bars1)

    def test_press_template_passes_a_touching_state(self):
        scenario = next(s for s in SCENARIOS if s['key'] == 'contact_press')
        state = synthesize_press_state(self.skeleton)
        checks = scenario['checks'](state, [], {})
        failed = [c for c in checks if not c['pass']]
        self.assertEqual(failed, [], f'unexpected failures: {failed}')

    def test_wrong_state_catch_f3(self):
        """F3: a penetrating hand with zero reaction MUST fail the template."""
        scenario = next(s for s in SCENARIOS if s['key'] == 'contact_press')
        corrupted = synthesize_press_state(self.skeleton, shift_y=-0.05,
                                           reaction=0.0)
        checks = scenario['checks'](corrupted, [], {})
        names = {c['name'] for c in checks if not c['pass']}
        self.assertIn('no_penetration', names)
        self.assertIn('reaction_nonzero', names)
        self.assertIn('gap_near_zero', names)
        # and the corrupted state renders VISIBLE evidence: distinct bytes
        good = snapshot_of(scenario, synthesize_press_state(self.skeleton))
        bad = snapshot_of(scenario, corrupted)
        self.assertNotEqual(render_state(scenario, good, self.skeleton),
                            render_state(scenario, bad, self.skeleton))

    def test_friction_templates_carry_coulomb_bound(self):
        for key in ('friction_stick', 'friction_slide'):
            scenario = next(s for s in SCENARIOS if s['key'] == key)
            mu = 1.0 if key == 'friction_stick' else 0.05
            state = synthesize_press_state(self.skeleton, mu=mu,
                                           mode='stick' if mu > 0.5
                                           else 'stick')
            names = [c['name'] for c in scenario['checks'](state, [], {})]
            self.assertIn('coulomb_bound', names)

    def test_stick_template_passes_measured_stick_behavior(self):
        """The measured stick run: landing heat booked once, then frozen hand,
        zero slip, constant heat."""
        scenario = next(s for s in SCENARIOS if s['key'] == 'friction_stick')
        state = synthesize_press_state(self.skeleton, mu=1.0, reaction=3.3778,
                                       mode='stick')
        state['energy']['friction_heat_J'] = 4.790e-3
        series = make_series(0.17522, 0.17522, (0.0, 0.0),
                             4.790e-3, 4.790e-3)
        failed = [c for c in scenario['checks'](state, series, {})
                  if not c['pass']]
        self.assertEqual(failed, [], f'unexpected failures: {failed}')

    def test_slide_template_passes_measured_slide_behavior(self):
        """The measured slide run: big early slip, hand displaced ~6.5 mm,
        heat grows 1.86e-3 -> 2.00e-3, final mode stick (held)."""
        scenario = next(s for s in SCENARIOS if s['key'] == 'friction_slide')
        state = synthesize_press_state(self.skeleton, mu=0.05, reaction=1.4015,
                                       mode='stick')
        state['energy']['friction_heat_J'] = 1.996e-3
        state['contact']['friction_force_N'] = 0.042
        state['contact']['slip_speed_m_s'] = 4.6e-5
        series = make_series(0.18876, 0.19528, (6.0e-2, 4.6e-5),
                             1.862e-3, 2.002e-3)
        failed = [c for c in scenario['checks'](state, series, {})
                  if not c['pass']]
        self.assertEqual(failed, [], f'unexpected failures: {failed}')

    def test_slide_template_rejects_frozen_hand(self):
        """A stick-like frozen hand must NOT pass the slide template."""
        scenario = next(s for s in SCENARIOS if s['key'] == 'friction_slide')
        state = synthesize_press_state(self.skeleton, mu=0.05, reaction=1.4,
                                       mode='stick')
        series = make_series(0.17522, 0.17522, (0.0, 0.0), 0.0, 0.0)
        names = {c['name'] for c in scenario['checks'](state, series, {})
                 if not c['pass']}
        self.assertIn('hand_slid', names)
        self.assertIn('slipped', names)

    def test_every_scenario_has_expected_and_checks(self):
        for scenario in SCENARIOS:
            self.assertTrue(scenario['expected'])
            self.assertTrue(callable(scenario['checks']))
            self.assertTrue(scenario['control'].get('reset') is True)


if __name__ == '__main__':
    unittest.main()
