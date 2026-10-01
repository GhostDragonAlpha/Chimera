"""MAT2-G06 named checks: the executable done_when suite.

Every check consumes the committed receipts and the committed trace
(zero live-state assertions; the freeze-state honesty law). No test is
skipped: G12 accounting is "N executed, 0 skipped" and the suite is run by
batch_gates via `unittest discover`. Semantics co-change with the receipts
that carry them (the stale-named-check law).
"""
from __future__ import annotations

import json
import pathlib
import unittest

HERE = pathlib.Path(__file__).resolve().parent

BATTERY = 9
TOTAL_TICKS = 229
CLOSING = (('band_lo', 3), ('band_mid', 3), ('band_hi', 3))
NONCLOSING = (('scene', 3), ('band_lo', 2), ('band_mid', 2),
              ('band_hi', 2), ('scene', 2))
CRITERIA_SHA256 = ('244ec17a4265b1eff67a541566bc68764ca37e4597554e4ddd62218'
                   '96ca30b83')
BASE_COMMIT = '39ee4884dbd096259298b4b1bb7e84088acdad7f'
WIN_JN = 1e-9
WIN_JT = 1e-9
WIN_LEDGER = 1e-12
WIN_FLIGHT = 1e-12
WIN_RECURSION = 1e-9
WIN_DISP = 1e-9
CAPTURE_WINDOW_M = 5e-3
D_MAX_REACH_M = 0.5


def _load(name):
    return json.loads((HERE / name).read_text(encoding='utf-8'))


def _case_of(label):
    base = label.rsplit('|mu=0', 1)[0]
    reading, n_str = base.split('|n=')
    return reading, int(n_str)


class G06DoneWhen(unittest.TestCase):
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
        self.assertTrue(self.rec['x_evidence']['p_class_pass'],
                        self.rec['x_evidence']['p_class_fail'])

    def test_x1_done_when_transfer_envelope(self):
        """done_when (verbatim): at least one reachable transfer retains
        admissible support throughout its tested envelope. The three band
        n=3 transfers record supported=true at EVERY tick of the declared
        envelope [4, 219]; the receipt carries the tick-by-tick verdict
        rows (in the committed trace)."""
        x = self.rec['x_checks']
        self.assertTrue(x['X1_done_when_transfer_envelope'])
        self.assertIsNone(self.rec['x_evidence']['x1_fail'])
        totals = self.rec['delivery_totals']
        self.assertEqual(totals['scenarios'], BATTERY, totals)
        self.assertEqual(totals['refusals'], 0, totals)
        winners = 0
        for label, s in self.trace['scenarios'].items():
            case = _case_of(label)
            env = s['header']['envelope']
            if case in CLOSING and not label.endswith('|mu=0'):
                winners += 1
                in_env = [v for v in s['verdicts']
                          if env[0] <= v['tick'] <= env[1]]
                self.assertEqual(len(in_env), 216, label)
                for v in in_env:
                    self.assertTrue(v['supported'],
                                    '%s tick %s %s' % (label, v['tick'],
                                                       v['reason']))
            verdict_by_tick = {v['tick']: v for v in s['verdicts']}
            self.assertEqual(len(verdict_by_tick), s['header']
                             ['total_ticks'], label)
        self.assertEqual(winners, 3)
        self.assertGreaterEqual(winners, 1)   # the done_when clause itself

    def test_x2_sealed_boundary_composition(self):
        """The 8-case solver table == the closed-form table == the pinned
        G01 rows (reading, n-1); the two mass systems stay split; no row
        flips under record-g vs standard-g arithmetic."""
        x = self.rec['x_checks']
        self.assertTrue(x['X2_sealed_boundary_composition'])
        self.assertIsNone(self.rec['x_evidence']['x2_fail'])
        table = self.rec['boundary_table']
        self.assertEqual(len(table), BATTERY)
        seen_closing = set()
        seen_open = set()
        for label, row in table.items():
            case = _case_of(label)
            is_zero_mu = label.endswith('|mu=0')
            self.assertEqual(row['measured'], row['g01_row'], label)
            if not is_zero_mu:
                self.assertEqual(row['measured'],
                                 row['closed_form']['closes'], label)
                cf = row['closed_form']
                self.assertAlmostEqual(cf['required_Ns'],
                                       cf['holder_share_kg'] * 9.81 * 0.005,
                                       places=12, msg=label)
                (seen_closing if row['measured'] else seen_open).add(case)
        self.assertEqual(seen_closing, set(CLOSING))
        self.assertEqual(seen_open, set(NONCLOSING))
        ev = self.rec['x_evidence']
        self.assertLess(ev['record_g_delta_max_Ns'],
                        ev['row_margin_min_Ns'], ev)

    def test_x3_flight_kinematics(self):
        """P3: the flyer's face-centre z advances the declared schedule per
        tick (1e-12 on non-event ticks), dz stays inside the continuity
        ceiling at every flight tick, the climb channel is recorded every
        tick, and the stop lands inside the declared capture window."""
        x = self.rec['x_checks']
        self.assertTrue(x['X3_flight_kinematics'])
        self.assertIsNone(self.rec['x_evidence']['x3_fail'])
        self.assertLessEqual(self.rec['x_evidence']
                             ['flight_worst_non_event_m'], WIN_FLIGHT)
        self.assertLessEqual(self.rec['x_evidence']['stop_window_worst_m'],
                             CAPTURE_WINDOW_M)
        for label, s in self.trace['scenarios'].items():
            header = s['header']
            case = _case_of(label)
            is_zero_mu = label.endswith('|mu=0')
            closing = case in CLOSING and not is_zero_mu
            marks = header['marks']
            lo, hi = marks['transfer']
            ceiling = (header['v_climb_mps'] + 1e-2) * 0.005
            face = [r['pads'][0]['centroid_z_m'] - 0.025 for r in s['rows']]
            for i in range(1, len(s['rows'])):
                t = s['rows'][i]['tick']
                if not (lo <= t <= hi):
                    continue
                dz = face[i] - face[i - 1]
                self.assertGreaterEqual(dz, 0.0, '%s tick %s' % (label, t))
                self.assertLessEqual(dz, ceiling,
                                     '%s tick %s' % (label, t))
                self.assertIsNotNone(s['rows'][i]['flyer_v1z_mps'], label)
            if closing:
                stop = face[marks['reattach'] - 2]
                self.assertAlmostEqual(
                    stop, header['target_probe']['target_centroid_m06'][2],
                    delta=CAPTURE_WINDOW_M, msg=label)

    def test_x4_handover_and_force_telemetry(self):
        """P2 + P4: at every transfer tick of a closing case each holder
        records jn = P and jt = (m/(n-1))*g*DT with stick arrest; the
        holders hold their height; every pressed attached tick carries
        jn = P (the flyer from tick 4, outside the flight window) with the
        declared 60 N conversion; the full-tick identity and reciprocity
        residuals stay inside 1e-12 everywhere."""
        x = self.rec['x_checks']
        self.assertTrue(x['X4_handover_and_force_telemetry'])
        self.assertIsNone(self.rec['x_evidence']['x4_fail'])
        for label, s in self.trace['scenarios'].items():
            header = s['header']
            case = _case_of(label)
            is_zero_mu = label.endswith('|mu=0')
            closing = case in CLOSING and not is_zero_mu
            n = header['n_channels']
            marks = header['marks']
            jt_want = (header['reading_kg'] / (n - 1)) * 9.81 * 0.005
            if closing:
                for row in s['rows']:
                    if not (marks['transfer'][0] <= row['tick']
                            <= marks['transfer'][1]):
                        continue
                    for pd in row['pads']:
                        if pd['k'] == 0:
                            continue
                        where = '%s tick %s pad %s' % (label, row['tick'],
                                                       pd['k'])
                        self.assertAlmostEqual(pd['jn_sum_Ns'], 0.30,
                                               delta=WIN_JN, msg=where)
                        self.assertAlmostEqual(pd['jt_sum_Ns'], jt_want,
                                               delta=WIN_JT, msg=where)
                        self.assertLessEqual(pd['vt_post_mps'], 1e-12,
                                             where)
                for i in range(1, len(s['rows'])):
                    if not (header['handover_tick'] <= s['rows'][i]['tick']
                            < header['reattach_tick']):
                        continue
                    for pd in s['rows'][i]['pads']:
                        if pd['k'] == 0:
                            continue
                        drop = (s['rows'][i - 1]['pads'][pd['k']]
                                ['centroid_z_m'] - pd['centroid_z_m'])
                        self.assertLessEqual(drop, 1e-9,
                                             '%s tick %s pad %s'
                                             % (label, s['rows'][i]['tick'],
                                                pd['k']))
            est_tick = None
            for row in s['rows']:
                if row['flyer_events']:
                    est_tick = row['tick']
                    break
            for row in s['rows']:
                t = row['tick']
                self.assertLessEqual(row['residual_full_max'], WIN_LEDGER,
                                     '%s tick %s' % (label, t))
                self.assertLessEqual(
                    max(abs(v) for v in row['ledger']['reciprocity_residual']
                        ), WIN_LEDGER, '%s tick %s' % (label, t))
                for pd in row['pads']:
                    pressed = ((pd['k'] == 0
                                and t < marks['release'][0]
                                and not (header['handover_tick'] <= t
                                         < header['reattach_tick'])
                                and t >= 4)
                               or (pd['k'] != 0
                                   and t < marks['release'][0]))
                    if not pressed:
                        continue
                    if pd['k'] == 0 and t == est_tick:
                        continue
                    if pd['mode'] not in ('stick', 'still'):
                        continue
                    self.assertAlmostEqual(pd['jn_sum_Ns'], 0.30,
                                           delta=WIN_JN,
                                           msg='%s tick %s pad %s'
                                           % (label, t, pd['k']))
                    force = pd['jn_sum_Ns'] / 0.005
                    self.assertAlmostEqual(force, 60.0, delta=1e-6,
                                           msg='%s tick %s pad %s'
                                           % (label, t, pd['k']))

    def test_x5_release_law(self):
        """P5: at every release tick every pad records jn and jt inside the
        per-kg bars, the velocity follows the free-fall recursion, and the
        pads released from clean stick accumulate g*DT^2*(1+2+...+10)."""
        x = self.rec['x_checks']
        self.assertTrue(x['X5_release_law'])
        self.assertIsNone(self.rec['x_evidence']['x5_fail'])
        want_disp = 9.81 * 0.005 * 0.005 * 55.0
        for label, s in self.trace['scenarios'].items():
            header = s['header']
            case = _case_of(label)
            is_zero_mu = label.endswith('|mu=0')
            closing = case in CLOSING and not is_zero_mu
            marks = header['marks']
            lo, hi = marks['release']
            for i in range(1, len(s['rows'])):
                row = s['rows'][i]
                if not (lo <= row['tick'] <= hi):
                    continue
                prev = s['rows'][i - 1]
                for pd in row['pads']:
                    bar = pd['mass_kg'] * 1e-10
                    self.assertLessEqual(pd['jn_sum_Ns'], bar,
                                         '%s tick %s pad %s'
                                         % (label, row['tick'], pd['k']))
                    self.assertLessEqual(pd['jt_sum_Ns'], bar,
                                         '%s tick %s pad %s'
                                         % (label, row['tick'], pd['k']))
                    want = prev['pads'][pd['k']]['vz_mps'] - 9.81 * 0.005
                    self.assertAlmostEqual(pd['vz_mps'], want,
                                           delta=WIN_RECURSION,
                                           msg='%s tick %s pad %s'
                                           % (label, row['tick'], pd['k']))
            if closing:
                for k in range(header['n_channels']):
                    disp = (s['rows'][lo - 2]['pads'][k]['centroid_z_m']
                            - s['rows'][hi - 1]['pads'][k]['centroid_z_m'])
                    self.assertAlmostEqual(disp, want_disp, delta=WIN_DISP,
                                           msg='%s pad %s' % (label, k))

    def test_x6_reachability_and_identity(self):
        """P7: the transfer displacement sits inside the declared fixture
        reach envelope, the hold rows touch the source facet, the hold2
        rows touch the target facet, and the run-time coplanarity probe
        reproduced the declared geometry."""
        x = self.rec['x_checks']
        self.assertTrue(x['X6_reachability_and_identity'])
        self.assertIsNone(self.rec['x_evidence']['x6_fail'])
        for label, s in self.trace['scenarios'].items():
            header = s['header']
            probe = header['target_probe']
            self.assertLessEqual(abs(probe['travel_m']), D_MAX_REACH_M,
                                 label)
            self.assertLessEqual(probe['plane_offset_m'], 1e-12, label)
            marks = header['marks']
            hold_tris = set()
            hold2_tris = set()
            for row in s['rows']:
                if marks['hold'][0] <= row['tick'] <= marks['hold'][1]:
                    hold_tris.update(row['pads'][0]['tris'])
                if marks['hold2'][0] <= row['tick'] <= marks['hold2'][1]:
                    hold2_tris.update(row['pads'][0]['tris'])
            self.assertIn(0, hold_tris, label)
            self.assertIn(1, hold2_tris, label)

    def test_x7_determinism(self):
        """Two independent main runs: trace byte-identical, receipt delta
        scoped to the declared augmentation keys."""
        self.assertTrue(self.det['X2_pass'])
        self.assertTrue(self.det['X2_trace_byte_identical'])
        self.assertEqual(self.det['declared_augmentation_keys'], [])

    def test_p_seam_law(self):
        """The declared-only delivery: the delivered key universe equals the
        declared set (4 timing keys + the pinned 32-slot table), strictly
        monotone, bound timing, zero refusals; the pinned G05 seam accepts
        the hold/release projections (30 per scenario) and refuses the
        G06-only phases with timing_unbound."""
        ev = self.rec['x_evidence']
        self.assertTrue(ev['p_class_pass'])
        self.assertIsNone(ev['p_class_fail'])
        declared = self.rec['interface']['declared_keys']
        self.assertEqual(len(declared), 36)
        self.assertEqual(ev['delivered_key_union'], declared)
        self.assertEqual(self.rec['interface']['phase_universe'],
                         ['approach', 'attach', 'load', 'hold', 'transfer',
                          'attach2', 'load2', 'hold2', 'release'])
        for label, s in self.trace['scenarios'].items():
            self.assertEqual(s['census']['accepted'],
                             s['header']['total_ticks'], label)
            self.assertEqual(s['census']['refusals'], [], label)
            g05_acc = s['g05_census']['accepted']
            self.assertEqual(g05_acc, 30, label)
            self.assertEqual(set(s['g05_refusal_codes']),
                             {'timing_unbound'}, label)
            last = 0
            for sample in s['samples']:
                self.assertGreater(sample['t_tick'], last, label)
                last = sample['t_tick']

    def test_p_named_variable_law(self):
        """The ten named absent variables are carried ABSENT with verbatim
        provenance; no absent slot was ever occupied in the battery."""
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

    def test_p_prereg_identity(self):
        """criteria_sha256 is identical across this suite, the receipts and
        the registry card row (read mode=ro at run time)."""
        self.assertEqual(self.rec['criteria_sha256'], CRITERIA_SHA256)
        self.assertEqual(self.rec['base_commit'], BASE_COMMIT)
        import sqlite3
        con = sqlite3.connect(
            'file:E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3'
            '?mode=ro', uri=True)
        try:
            cur = con.cursor()
            cur.execute('SELECT payload FROM state WHERE id=1')
            state = json.loads(cur.fetchone()[0])
        finally:
            con.close()
        self.assertEqual(
            state['kanban']['cards']['MAT2-G06']['criteria_sha256'],
            CRITERIA_SHA256)

    def test_p_input_pins_verified(self):
        """Every declared input pin was verified at run time (the receipt
        records the pin census; the drift refusal is named)."""
        pins = self.rec['input_pins']
        self.assertGreaterEqual(len(pins), 15)
        for k, v in pins.items():
            self.assertEqual(v, 'ok', k)

    def test_u_upstream_identity(self):
        """All three upstream modules are recorded imported-not-forked at
        their pinned shas; the G05 table composition is recorded as NOT
        re-declared."""
        up = self.rec['upstream']
        self.assertTrue(up['solver']['imported_not_forked'])
        self.assertEqual(up['solver']['sha256'],
                         '1cd662b30343011eb4a0a01e461a1e82b00482d0371857c8e4'
                         '2d6bec8f9a28dc')
        self.assertTrue(up['grip_physics']['imported_not_forked'])
        self.assertEqual(up['grip_physics']['sha256'],
                         '0d6375484c350039468b31a2f7db2895d3365412aee52ce98d'
                         'e72b4173d69245')
        self.assertTrue(up['observation_table']['imported_not_forked'])
        self.assertEqual(up['observation_table']['sha256'],
                         '3dae0a3805cec86bba8dbae9a6fc563f43cddc98fcd01a693'
                         'f725e4f31c46bd3')
        self.assertIn('NOT re-declared',
                      up['observation_table']['composition'])

    def test_f_falsifiers_all_bite(self):
        """Every arm ran its clean control FIRST and bites on the tampered
        build (a non-biting falsifier fails the build)."""
        self.assertTrue(self.fal['F_all_green'])
        self.assertEqual(self.fal['arm_count'], 5)
        for name, arm in self.fal['arms'].items():
            self.assertTrue(arm['bites'], name)
            self.assertTrue(arm['clean_control'], name)
            self.assertIn('premature', arm['premature_guard'], name)

    def test_r_regression_green(self):
        """All three upstream suites re-ran UNMODIFIED on this revision and
        exited 0."""
        self.assertTrue(self.reg['P_regression_suite_green'])
        self.assertEqual(len(self.reg['suites']), 3)
        for row in self.reg['suites']:
            self.assertEqual(row['exit_code'], 0, row['suite'])
            self.assertTrue(row['suite_unmodified'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
