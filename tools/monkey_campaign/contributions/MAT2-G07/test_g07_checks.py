"""MAT2-G07 named checks: the executable done_when suite.

Every check consumes the committed receipts and the committed trace
(zero live-state assertions; the freeze-state honesty law). No test is
skipped: G12 accounting is "N executed, 0 skipped" and the suite is run
by batch_gates via `unittest discover`. Semantics co-change with the
receipts that carry them (the stale-named-check law).
"""
from __future__ import annotations

import json
import pathlib
import unittest

HERE = pathlib.Path(__file__).resolve().parent

WIN_ENERGY = 1e-12
WIN_DRIFT = 1e-9
WIN_CONT = 1e-9
WIN_RECURSION_V = 1e-9
WIN_DISP = 1e-9
WIN_RELEASE_SCALE = 1e-10
WIN_F32 = 1e-6
WIN_POSE_ID = 1e-9
HOLD_TICKS = 20
RELEASE_TICKS = 40
TOTAL_TICKS = 60
SCENARIOS = 13
DELIVERIES = 780
STICK_CASES = {('band_lo', 2), ('band_lo', 3), ('band_mid', 2),
               ('band_mid', 3), ('band_hi', 2), ('band_hi', 3),
               ('scene', 3)}
SLIP_CASES = {('band_lo', 1), ('band_mid', 1), ('band_hi', 1),
              ('scene', 1), ('scene', 2)}


def _load(name):
    return json.loads((HERE / name).read_text(encoding='utf-8'))


def _case(label):
    base = label.rsplit('|mu=0', 1)[0]
    reading, n_str = base.split('|n=')
    return reading, int(n_str)


class G07DoneWhen(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls):
        cls.rec = _load('experiment_receipt.json')
        cls.trace = _load('experiment_trace.json')
        cls.det = _load('determinism_receipt.json')
        cls.fal = _load('falsifier_receipt.json')
        cls.reg = _load('regression_receipt.json')

    def test_00_receipts_declare_pass(self):
        self.assertTrue(self.rec['X_all_pass'], self.rec['x_checks'])
        self.assertTrue(self.rec['vacuous_guard_selftest'])

    def test_x1_release_removes_support(self):
        """The done_when force clause: on every unobstructed release tick
        of all 13 scenarios the recorded pad impulses sit inside the
        sealed share-scaled noise bars, the press work is EXACTLY zero
        through the release phase, the trunk anchor sits inside its bar,
        and the delivered agg_release_flag flips exactly at tick 21.
        Recorded CCD collision events (real transient contacts with the
        trunk surface) are carried as evidence, never as support."""
        x = self.rec['x_checks']
        self.assertTrue(x['X1_release_removes_support'])
        ev = self.rec['x_evidence']
        worst = ev['release_bars_worst']
        bar_max = 10.037998 * WIN_RELEASE_SCALE   # the largest share bar
        anchor_bar_max = 3 * 10.037998 * WIN_RELEASE_SCALE
        self.assertGreater(worst['jn_max_Ns'], 0.0)   # the bars BITE (a
        # zero would mean the predicate never measured anything)
        self.assertLessEqual(worst['jn_max_Ns'], bar_max)
        self.assertLessEqual(worst['jt_max_Ns'], bar_max)
        self.assertLessEqual(worst['anchor_max_Ns'], anchor_bar_max)
        for label, s in self.trace['scenarios'].items():
            rel = s['release']
            share = s['header']['pad_share_kg']
            n = s['header']['n_channels']
            self.assertLessEqual(rel['jn_max_Ns'],
                                 share * WIN_RELEASE_SCALE, label)
            self.assertLessEqual(rel['jt_max_Ns'],
                                 share * WIN_RELEASE_SCALE, label)
            self.assertLessEqual(rel['anchor_max_Ns'],
                                 share * n * WIN_RELEASE_SCALE, label)
            self.assertEqual(rel['press_work_release_J'], 0.0, label)
            self.assertEqual(rel['unobstructed_release_ticks']
                             + rel['collision_count'], RELEASE_TICKS,
                             label)
            for sample in s['samples']:
                self.assertEqual(sample['agg_release_flag'],
                                 0.0 if sample['t_tick'] <= HOLD_TICKS
                                 else 1.0,
                                 '%s tick %s' % (label, sample['t_tick']))

    def test_x2_motion_accounted(self):
        """The done_when motion clause: the free-fall velocity recursion
        and the gravity-only closed-form displacement hold inside the
        sealed G04 windows on every unobstructed release tick (closed
        form on the unobstructed prefix), and the pose-continuity
        identity holds on every unobstructed tick of every scenario --
        no teleport, no hidden reset. Collision events are recorded."""
        x = self.rec['x_checks']
        self.assertTrue(x['X2_motion_accounted'])
        ev = self.rec['x_evidence']
        self.assertLessEqual(ev['recursion_worst_mps'], WIN_RECURSION_V)
        self.assertLessEqual(ev['disp_closed_form_worst_m'], WIN_DISP)
        self.assertLessEqual(ev['continuity_worst_m'], WIN_CONT)
        self.assertGreater(ev['recursion_worst_mps'], 0.0)   # measured
        total_collisions = 0
        for label, s in self.trace['scenarios'].items():
            rel = s['release']
            total_collisions += rel['collision_count']
            want_prefix = (rel['collision_events'][0]['tick']
                           - HOLD_TICKS - 1) if rel['collision_count'] \
                else RELEASE_TICKS
            self.assertEqual(rel['closed_form_prefix_ticks'], want_prefix,
                             label)
            for arow in s['acct_rows']:
                for pad in arow['pads']:
                    if pad['unobstructed']:
                        self.assertLessEqual(pad['continuity_residual_m'],
                                             WIN_CONT,
                                             '%s tick %s' % (label,
                                                             arow['tick']))
        self.assertEqual(total_collisions, 2)   # the recorded events

    def test_x3_energy_account_exact(self):
        """The done_when energy clause (C13): the exact discrete
        impulse-work identity KE(t)-KE(t-1) == W_press + W_weld +
        W_gravity + W_contact + W_anchor closes within 1e-12 J for every
        body and tick of every scenario; the impulse replay reproduces
        the post-solve velocity; the friction split matches the solver's
        recorded w_f_ke_J losses; the hold-phase press work is positive
        and the release-phase press work is exactly zero."""
        x = self.rec['x_checks']
        self.assertTrue(x['X3_energy_account_exact'])
        ev = self.rec['x_evidence']
        self.assertLessEqual(ev['energy_residual_worst_J'], WIN_ENERGY)
        self.assertLessEqual(ev['replay_delta_worst_mps'], 1e-12)
        self.assertLessEqual(ev['loss_identity_worst_J'], 1e-12)
        self.assertGreater(ev['press_work_hold_total_J'], 0.0)
        for label, s in self.trace['scenarios'].items():
            acc = s['account']
            self.assertGreater(acc['hold']['work_press_J'], 0.0, label)
            self.assertEqual(acc['release']['work_press_J'], 0.0, label)
            self.assertEqual(acc['hold']['work_weld_J'], 0.0, label)
            self.assertEqual(acc['release']['work_weld_J'], 0.0, label)
            # the account closes per phase to the measured residual
            self.assertAlmostEqual(
                acc['release']['ke_delta_J'],
                acc['release']['work_gravity_J']
                + acc['release']['work_contact_J'],
                delta=WIN_ENERGY, msg=label)

    def test_x4_fall_energy_account(self):
        """C13's stored-energy account: with PE = m*g*(z - z_ref), every
        unobstructed tick satisfies the declared symplectic
        discretization identity inside WIN_DRIFT; the stick class's
        release-phase stored-energy drop equals the analytic
        -(m/2)(g*DT)^2-per-tick sum. Collision-tick residuals are
        recorded evidence (the impact's stored-energy exchange)."""
        x = self.rec['x_checks']
        self.assertTrue(x['X4_fall_energy_account'])
        ev = self.rec['x_evidence']
        self.assertLessEqual(ev['drift_residual_worst_J'], WIN_DRIFT)
        by_class = ev['drift_release_totals_by_class_J']
        self.assertLess(abs(by_class['stick']), 1e-12)   # the exact
        # discretization prediction, measured over the stick class
        self.assertLessEqual(ev['collision_tick_drift_worst_J'], 1e-3)
        for label, s in self.trace['scenarios'].items():
            for arow in s['acct_rows']:
                for pad in arow['pads']:
                    if pad['unobstructed']:
                        self.assertLessEqual(abs(pad['drift_residual_J']),
                                             WIN_DRIFT,
                                             '%s tick %s' % (label,
                                                             arow['tick']))

    def test_x5_seam_delivery_composition(self):
        """Every scenario is delivered through the sealed G05 seam: 780
        accepted deliveries, 0 refusals, the exact declared key set on
        every sample, the delivered cumulative displacement slot bound
        to the measured account inside the float32 window, and the
        measured-vs-derived pose identity inside 1e-9 m."""
        x = self.rec['x_checks']
        self.assertTrue(x['X5_seam_delivery_composition'])
        totals = self.rec['battery_totals']
        self.assertEqual(totals['accepted'], DELIVERIES)
        self.assertEqual(totals['refusals'], 0)
        self.assertEqual(totals['scenarios'], SCENARIOS)
        ev = self.rec['x_evidence']
        self.assertLessEqual(ev['disp_binding_worst_relative'], WIN_F32)
        declared = self.rec['measurement']['declared_keys']
        self.assertEqual(ev['delivered_key_union'], declared)
        for label, s in self.trace['scenarios'].items():
            self.assertEqual(s['census']['accepted'], TOTAL_TICKS, label)
            self.assertEqual(s['census']['refusals'], [], label)
            for sample in s['samples']:
                self.assertEqual(set(sample), set(declared), label)
            for prow in s['pose_check']:
                self.assertLessEqual(prow['delta'], WIN_POSE_ID, label)

    def test_x6_phase_separation(self):
        """C20: hold (static) and release (dynamic) metrics are extracted
        only through the keyed per-phase extractor (20 + 40 tagged rows
        per scenario); the hold and release accounts are reported
        separately; the zero-mu control is the missed-grasp control:
        never supported, honestly slipped from tick 1, its release still
        removes the press, and its account closes like every other
        case."""
        x = self.rec['x_checks']
        self.assertTrue(x['X6_phase_separation'])
        seen_stick = set()
        seen_slip = set()
        for label, s in self.trace['scenarios'].items():
            acc = s['account']
            self.assertEqual(acc['hold']['ticks'], HOLD_TICKS, label)
            self.assertEqual(acc['release']['ticks'], RELEASE_TICKS,
                             label)
            case = _case(label)
            is_zero = label.endswith('|mu=0')
            stick_case = case in STICK_CASES and not is_zero
            supported_any = False
            for sample in s['samples']:
                hold = sample['t_tick'] <= HOLD_TICKS
                want = 1.0 if (stick_case and hold) else 0.0
                self.assertEqual(sample['agg_supported_flag'], want,
                                 '%s tick %s' % (label, sample['t_tick']))
                if want == 1.0:
                    supported_any = True
            if is_zero:
                # the missed-grasp control: never supported, classified
                # separately from the sealed slip rows
                self.assertFalse(supported_any, label)
                continue
            (seen_stick if supported_any else seen_slip).add(case)
        self.assertEqual(seen_stick, STICK_CASES)
        self.assertEqual(seen_slip, SLIP_CASES)

    def test_x7_named_absent_law(self):
        """The ten named absent variables are carried ABSENT with
        verbatim provenance from the pinned G04 module; no absent slot
        was ever occupied in the battery."""
        x = self.rec['x_checks']
        self.assertTrue(x['X7_named_absent_law'])
        absent = {v['name']: v for v in self.rec['named_absent_variables']}
        for v in ('x_press', 'x_share', 'x_aperture', 'x_reach', 'x_com',
                  'x_inertia', 'x_trajectory', 'x_sequence', 'x_losses',
                  'x_trunk_strength'):
            self.assertIn(v, absent)
            self.assertEqual(absent[v]['status'], 'ABSENT')
            self.assertTrue(absent[v]['provenance_verbatim'])
        declared = self.rec['measurement']['declared_keys']
        for name in absent:
            self.assertNotIn(name, declared)

    def test_u_upstream_identity(self):
        """All three upstream modules are recorded imported-not-forked at
        their pinned shas; the seam records the G05 composition law (not
        a re-declaration)."""
        up = self.rec['upstream']
        self.assertTrue(up['solver']['imported_not_forked'])
        self.assertEqual(up['solver']['sha256'],
                         '1cd662b30343011eb4a0a01e461a1e82b00482d0371857c8e4'
                         '2d6bec8f9a28dc')
        self.assertTrue(up['grip_physics']['imported_not_forked'])
        self.assertEqual(up['grip_physics']['sha256'],
                         '0d6375484c350039468b31a2f7db2895d3365412aee52ce98d'
                         'e72b4173d69245')
        self.assertTrue(up['observation_seam']['imported_not_forked'])
        self.assertEqual(up['observation_seam']['sha256'],
                         '3dae0a3805cec86bba8dbae9a6fc563f43cddc98fcd01a693'
                         'f725e4f31c46bd3')
        self.assertIn('NOT', up['observation_seam']['composition'])

    def test_f_falsifiers_all_bite(self):
        """Every arm ran its clean control FIRST and bites on the
        tampered build (a non-biting falsifier fails the build)."""
        self.assertTrue(self.fal['F_all_green'])
        self.assertEqual(self.fal['arm_count'], 5)
        for name, arm in self.fal['arms'].items():
            self.assertTrue(arm['bites'], name)
            self.assertTrue(arm['clean_control'], name)
            self.assertIn('premature', arm['premature_guard'], name)

    def test_d_determinism(self):
        """Two independent main runs: trace byte-identical, receipt delta
        scoped to the declared augmentation keys."""
        self.assertTrue(self.det['X2_pass'])
        self.assertTrue(self.det['X2_trace_byte_identical'])
        self.assertEqual(self.det['declared_augmentation_keys'], [])

    def test_r_regression_green(self):
        """The three upstream suites re-ran UNMODIFIED on this revision
        and exited 0."""
        self.assertTrue(self.reg['P_regression_suite_green'])
        self.assertEqual(len(self.reg['suites']), 3)
        for row in self.reg['suites']:
            self.assertEqual(row['exit_code'], 0, row['suite'])
            self.assertTrue(row['suite_unmodified'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
