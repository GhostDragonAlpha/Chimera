"""MAT2-G05 named checks: the executable done_when suite.

Every check consumes the committed receipts and the committed trace
(zero live-state assertions; the freeze-state honesty law). The X3 test
re-derives every delivered value from the committed trace rows -- the
independent recomputation. No test is skipped: G12 accounting is
"N executed, 0 skipped" and the suite is run by batch_gates via
`unittest discover`. Semantics co-change with the receipts that carry
them (the stale-named-check law).
"""
from __future__ import annotations

import json
import pathlib
import unittest

HERE = pathlib.Path(__file__).resolve().parent

WIN_F32 = 1e-6
WIN_POSE_ID = 1e-9
WIN_TIME = 1e-12
HOLD_TICKS = 20
TOTAL_TICKS = 30
SCENARIOS = 13
SAMPLES = 390
STICK_CASES = {('band_lo', 2), ('band_lo', 3), ('band_mid', 2),
               ('band_mid', 3), ('band_hi', 2), ('band_hi', 3),
               ('scene', 3)}
SLIP_CASES = {('band_lo', 1), ('band_mid', 1), ('band_hi', 1),
              ('scene', 1), ('scene', 2)}


def _load(name):
    return json.loads((HERE / name).read_text(encoding='utf-8'))


def _f32_ok(delivered, raw):
    return abs(delivered - raw) <= WIN_F32 * max(1.0, abs(raw))


def _case(label):
    base = label.rsplit('|mu=0', 1)[0]
    reading, n_str = base.split('|n=')
    return reading, int(n_str)


class G05DoneWhen(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls):
        cls.rec = _load('experiment_receipt.json')
        cls.trace = _load('experiment_trace.json')
        cls.det = _load('determinism_receipt.json')
        cls.fal = _load('falsifier_receipt.json')
        cls.reg = _load('regression_receipt.json')

    def test_00_receipts_declare_pass(self):
        self.assertTrue(self.rec['X1_pass'], self.rec['x_checks'])
        self.assertTrue(self.rec['vacuous_guard_selftest'])

    def test_x1_declared_only_delivery(self):
        """The controller's received key universe is EXACTLY the declared
        set: 4 timing keys + 32 declared vector slots, 390 accepted
        deliveries, 0 refusals, every sample carrying the exact key set."""
        x = self.rec['x_checks']
        self.assertTrue(x['X1_declared_only_delivery'])
        declared = self.rec['interface']['declared_keys']
        union = self.rec['x_evidence']['delivered_key_union']
        self.assertEqual(sorted(union), sorted(declared))
        self.assertEqual(len(declared), 36)          # 4 timing + 32 vector
        self.assertEqual(self.rec['interface']['obs_dim'], 32)
        totals = self.rec['delivery_totals']
        self.assertEqual(totals['accepted'], SAMPLES, totals)
        self.assertEqual(totals['refusals'], 0, totals)
        self.assertEqual(totals['scenarios'], SCENARIOS)
        for label, s in self.trace['scenarios'].items():
            self.assertEqual(s['census']['accepted'], TOTAL_TICKS, label)
            self.assertEqual(s['census']['refusals'], [], label)
            for sample in s['samples']:
                self.assertEqual(set(sample), set(declared), label)

    def test_x2_explicit_timing(self):
        """Every delivered sample carries EXPLICIT, BOUND timing: tick in
        1..30, phase matching the tick's press state, dt = 0.005 s,
        t_seconds = tick*dt, strictly monotone delivery."""
        x = self.rec['x_checks']
        self.assertTrue(x['X2_explicit_timing'])
        for label, s in self.trace['scenarios'].items():
            last = 0
            for i, sample in enumerate(s['samples']):
                row = s['rows'][i]
                tick = sample['t_tick']
                self.assertEqual(tick, row['tick'], label)
                self.assertGreaterEqual(tick, 1)
                self.assertLessEqual(tick, TOTAL_TICKS)
                self.assertEqual(sample['t_phase'], row['phase'], label)
                self.assertEqual(sample['t_phase'],
                                 'hold' if tick <= HOLD_TICKS else 'release',
                                 label)
                self.assertEqual(sample['t_dt_s'], 0.005, label)
                self.assertAlmostEqual(sample['t_seconds'], tick * 0.005,
                                       delta=WIN_TIME)
                self.assertGreater(tick, last, label)
                last = tick

    def test_x3_measurable_traceability(self):
        """Every delivered value re-derives from the committed trace rows:
        the full per-sample comparison across the battery, the float32
        delivery window, the force conversion, the recorded trunk anchor,
        and the measured-vs-derived pose identity."""
        x = self.rec['x_checks']
        self.assertTrue(x['X3_measurable_traceability'])
        ev = self.rec['x_evidence']
        self.assertLessEqual(ev['f32_worst_relative'], WIN_F32)
        self.assertLessEqual(ev['pose_identity_worst_m'], WIN_POSE_ID)
        self.assertIsNone(ev['trace_fail'])
        for label, s in self.trace['scenarios'].items():
            n = s['header']['n_channels']
            for i, sample in enumerate(s['samples']):
                row = s['rows'][i]
                for k in range(n):
                    pd = row['pads'][k]
                    where = '%s ch%d tick %s' % (label, k, row['tick'])
                    self.assertAlmostEqual(
                        sample['ch%d_contact_flag' % k],
                        0.0 if pd['mode'] == 'no_contact' else 1.0, msg=where)
                    self.assertAlmostEqual(
                        sample['ch%d_stick_flag' % k],
                        1.0 if pd['mode'] == 'stick' else 0.0, msg=where)
                    self.assertAlmostEqual(
                        sample['ch%d_slip_flag' % k],
                        1.0 if pd['mode'] == 'slip' else 0.0, msg=where)
                    self.assertTrue(_f32_ok(sample['ch%d_jn_Ns' % k],
                                            pd['jn_sum_Ns']), where)
                    self.assertTrue(_f32_ok(sample['ch%d_jt_Ns' % k],
                                            pd['jt_sum_Ns']), where)
                    self.assertTrue(_f32_ok(
                        sample['ch%d_contact_force_N' % k],
                        pd['jn_sum_Ns'] / 0.005), where)
                    self.assertTrue(_f32_ok(sample['ch%d_disp_down_cum_m'
                                                    % k],
                                            pd['disp_down_m_cum']), where)
                self.assertTrue(_f32_ok(sample['agg_trunk_anchor_z_Ns'],
                                        row['ledger']['trunk_anchor'][2]),
                                label)
            for prow in s['pose_check']:
                self.assertLessEqual(prow['delta'], WIN_POSE_ID, label)

    def test_x4_support_state_law(self):
        """The declared support law: supported iff every available channel
        is recorded stick AND the phase is hold. The SEVEN sealed stick
        cases are supported through the hold and unsupported through the
        release; the five slip rows and the zero-mu control are honestly
        unsupported everywhere; release ticks are exactly 21..30."""
        x = self.rec['x_checks']
        self.assertTrue(x['X4_support_state_law'])
        self.assertIsNone(self.rec['x_evidence']['support_fail'])
        seen_stick = set()
        seen_slip = set()
        for label, s in self.trace['scenarios'].items():
            case = _case(label)
            is_zero_mu = label.endswith('|mu=0')
            n = s['header']['n_channels']
            for i, sample in enumerate(s['samples']):
                tick = sample['t_tick']
                hold = tick <= HOLD_TICKS
                want = 1.0 if (case in STICK_CASES and not is_zero_mu
                               and hold) else 0.0
                self.assertEqual(sample['agg_supported_flag'], want,
                                 '%s tick %d' % (label, tick))
                self.assertEqual(sample['agg_release_flag'],
                                 0.0 if hold else 1.0,
                                 '%s tick %d' % (label, tick))
                if hold and not is_zero_mu:
                    if want == 1.0:
                        self.assertEqual(sample['agg_support_count'],
                                         float(n), label)
            if is_zero_mu:
                continue
            supported_any = any(
                smp['agg_supported_flag'] == 1.0
                for smp in s['samples'])
            (seen_stick if supported_any else seen_slip).add(case)
        self.assertEqual(seen_stick, STICK_CASES)
        self.assertEqual(seen_slip, SLIP_CASES)

    def test_x5_w04_contract_composition(self):
        """The frozen W04 TC-2 contract is pinned and its declared laws are
        the laws this interface composes with; the task-owned table
        conforms (fixed dim, float32, privileged_forbidden, availability
        law, declared aliasing)."""
        x = self.rec['x_checks']
        self.assertTrue(x['X5_w04_contract_composition'])
        contract = self.rec['upstream']['observation_contract']
        self.assertEqual(contract['sha256'],
                         'e8c2d698dee0337414c48e8d2f6569c45f6f61828dabdeff6a'
                         '4f1188b1c0671c')
        law = contract['law']
        self.assertEqual(law['kind'], 'policy_observation_interface')
        self.assertEqual(law['obs_schema_version'], 2)
        self.assertEqual(law['dim'], 80)
        self.assertEqual(law['legacy_dim'], 64)
        self.assertEqual(law['dtype'], 'float32')
        self.assertTrue(law['privileged_forbidden'])
        self.assertEqual(law['history_ticks'], 0)
        self.assertTrue(law['availability_recipe'])
        interface = self.rec['interface']
        self.assertEqual(interface['obs_dim'], 32)
        self.assertEqual(interface['dtype'], 'float32')
        self.assertEqual(interface['history_ticks'], 0)
        self.assertTrue(interface['privileged_forbidden'])
        self.assertEqual(interface['aliasing_audit']['shared_source_count'],
                         7)
        self.assertTrue(interface['aliasing_audit']['declared_shared_sources']
                        )
        self.assertNotIn('solver_penetration_m',
                         interface['declared_keys'])

    def test_x6_no_hidden_state(self):
        """No hidden simulator information as sensed information: no
        privileged name delivered anywhere in the battery, no x_* name
        delivered, and the delivered universe equals the declared one."""
        x = self.rec['x_checks']
        self.assertTrue(x['X6_no_hidden_state'])
        ev = self.rec['x_evidence']
        self.assertEqual(ev['delivered_privileged'], [])
        declared = self.rec['interface']['declared_keys']
        self.assertEqual(ev['delivered_key_union'], declared)
        privileged = set(self.rec['interface']['privileged_non_grata'])
        for label, s in self.trace['scenarios'].items():
            for sample in s['samples']:
                for key in sample:
                    self.assertNotIn(key, privileged, label)
                    self.assertFalse(key.startswith('x_'), label)

    def test_x7_named_absent_law(self):
        """The ten named absent variables are carried ABSENT with verbatim
        provenance from the pinned G04 module; no absent slot was ever
        occupied in the battery."""
        x = self.rec['x_checks']
        self.assertTrue(x['X7_named_absent_law'])
        absent = {v['name']: v for v in self.rec['named_absent_variables']}
        for v in ('x_press', 'x_share', 'x_aperture', 'x_reach', 'x_com',
                  'x_inertia', 'x_trajectory', 'x_sequence', 'x_losses',
                  'x_trunk_strength'):
            self.assertIn(v, absent)
            self.assertEqual(absent[v]['status'], 'ABSENT')
            self.assertTrue(absent[v]['provenance_verbatim'])
        declared = self.rec['interface']['declared_keys']
        for name in absent:
            self.assertNotIn(name, declared)

    def test_u_upstream_identity(self):
        """Both upstream modules are recorded imported-not-forked at their
        pinned shas; the observation contract records the W04 composition
        law (not a re-declaration)."""
        up = self.rec['upstream']
        self.assertTrue(up['solver']['imported_not_forked'])
        self.assertEqual(up['solver']['sha256'],
                         '1cd662b30343011eb4a0a01e461a1e82b00482d0371857c8e4'
                         '2d6bec8f9a28dc')
        self.assertTrue(up['grip_physics']['imported_not_forked'])
        self.assertEqual(up['grip_physics']['sha256'],
                         '0d6375484c350039468b31a2f7db2895d3365412aee52ce98d'
                         'e72b4173d69245')
        self.assertIn('NOT re-declared', up['observation_contract']
                      ['composition'])

    def test_f_falsifiers_all_bite(self):
        """Every arm ran its clean control FIRST and bites on the tampered
        build (a non-biting falsifier fails the build)."""
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
        """Both upstream suites re-ran UNMODIFIED on this revision and
        exited 0."""
        self.assertTrue(self.reg['P_regression_suite_green'])
        self.assertEqual(len(self.reg['suites']), 2)
        for row in self.reg['suites']:
            self.assertEqual(row['exit_code'], 0, row['suite'])
            self.assertTrue(row['suite_unmodified'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
