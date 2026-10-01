"""MAT2-G04 named checks: the executable done_when suite.

Every check consumes the committed receipts (zero live-state assertions;
the freeze-state honesty law). No test is skipped: G12 accounting is
"N executed, 0 skipped" and the suite is run by batch_gates via
`unittest discover`. Semantics co-change with the receipts that carry
them (the stale-named-check law).
"""
from __future__ import annotations

import json
import pathlib
import unittest

HERE = pathlib.Path(__file__).resolve().parent


def _load(name):
    return json.loads((HERE / name).read_text(encoding='utf-8'))


class G04DoneWhen(unittest.TestCase):
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

    @staticmethod
    def _grip_labels(scn):
        """The 12 preregistered grip cases (the zero-mu control carries the
        '|mu=0' suffix and is excluded)."""
        return sorted(k for k in scn if '|mu=0' not in k)

    def test_x1_attachment_through_solver(self):
        """Attachment enters through solver contact records only: the press
        channel produces jn = P at every channel-tick, the trunk is the only
        pinned body, and every pad contact names trunk_01.lateral."""
        scn = self.trace['scenarios']
        grip = self._grip_labels(scn)
        self.assertEqual(len(grip), 12, grip)
        self.assertTrue(grip)
        for label in grip:
            s = scn[label]
            self.assertEqual(s['header']['pinned_bodies'],
                             ['trunk_01.lateral'], label)
            self.assertEqual(s['header']['trunk_surface'],
                             'trunk_01.lateral', label)
            self.assertLessEqual(s['summary']['jn_err_hold_max_Ns'], 1e-9,
                                 label)
            for row in s['rows']:
                if row['phase'] != 'hold':
                    continue
                for p in row['pads']:
                    self.assertIn('trunk_01.lateral', p['surfaces'], label)
                    self.assertIn(p['pad'], p['surfaces'], label)
        x = self.rec['x_checks']
        self.assertTrue(x['X1_attachment_through_solver'])

    def test_x2_friction_law(self):
        """Coulomb stick arrest and the exact slip recursion; the zero-mu
        control slides under full press (hold is friction-dependent)."""
        x = self.rec['x_checks']
        self.assertTrue(x['X2_friction_law'])
        self.assertTrue(x['X2_zero_mu_slides'])
        zero = self.trace['scenarios']['band_mid|n=3|mu=0']
        self.assertEqual(zero['header']['mu_s'], 0.0)
        self.assertGreater(zero['summary']['disp_hold_m'], 1e-3)
        self.assertEqual(zero['summary']['solver_mode_hold'], ['slip'])

    def test_x3_reaction_loads(self):
        """Trunk anchor reaction is recorded and re-verified every tick;
        reciprocity holds; the per-channel reaction at the operating point
        is 60 N."""
        x = self.rec['x_checks']
        self.assertTrue(x['X3_reaction_loads'])
        scn = self.trace['scenarios']
        for label, s in scn.items():
            self.assertLessEqual(s['summary']['reaction_err_max_Ns'], 1e-12,
                                 label)
            self.assertLessEqual(s['summary']['reciprocity_max_Ns'], 1e-12,
                                 label)
        hold = scn['scene|n=3']['rows'][0]
        # the trunk reaction is the VECTOR SUM over the loaded channels:
        # its axial (z) component carries the WHOLE supported reading's
        # per-tick weight impulse (the tangential support), here
        # 10.037998 * 9.81 * 0.005 N*s; anchor == -contact (summary bar).
        self.assertAlmostEqual(hold['ledger']['trunk_contact'][2],
                               -10.037998 * 9.81 * 0.005, places=9)
        self.assertAlmostEqual(
            self.rec['press_channel']['operating_force_N'], 60.0, places=9)

    def test_x4_release_opens(self):
        """After the press stops: jn = jt = 0 and the displacement follows
        free fall -- nothing retains a force (no hidden sticky
        constraint)."""
        x = self.rec['x_checks']
        self.assertTrue(x['X4_release_opens'])
        scn = self.trace['scenarios']
        for label in self._grip_labels(scn):
            s = scn[label]
            bar = s['header']['pad_share_kg'] * 1e-10
            self.assertLessEqual(s['summary']['jn_release_max_Ns'], bar,
                                 label)
            self.assertLessEqual(s['summary']['jt_release_max_Ns'], bar,
                                 label)
            self.assertLessEqual(
                s['summary']['release_freefall_disp_err_m'], 1e-9, label)

    def test_x5_boundary_agreement(self):
        """The solver reproduces the G01 OUTSIDE-CONDITIONAL boundary:
        single-channel support does not close at any lawful reading;
        multi-channel closes at n>=2 (band) / n=3 (scene); the two mass
        systems stay split; no row flips under the g convention."""
        x = self.rec['x_checks']
        self.assertTrue(x['X5_boundary_agreement'])
        self.assertTrue(x['X5_g_convention_no_flip'])
        table = {r['case']: r for r in self.rec['boundary_agreement']}
        self.assertEqual(table['scene|n=1']['g01_receipt'], 'SLIP')
        self.assertEqual(table['scene|n=2']['g01_receipt'], 'SLIP')
        self.assertEqual(table['scene|n=3']['g01_receipt'], 'STICK')
        self.assertEqual(table['band_lo|n=1']['g01_receipt'], 'SLIP')
        self.assertEqual(table['band_hi|n=1']['g01_receipt'], 'SLIP')
        self.assertEqual(table['band_hi|n=2']['g01_receipt'], 'STICK')
        self.assertEqual(table['band_mid|n=2']['g01_receipt'], 'STICK')
        self.assertEqual(table['band_lo|n=2']['g01_receipt'], 'STICK')
        self.assertEqual(table['band_lo|n=3']['g01_receipt'], 'STICK')
        self.assertEqual(table['band_mid|n=3']['g01_receipt'], 'STICK')
        self.assertEqual(table['band_hi|n=3']['g01_receipt'], 'STICK')

    def test_x6_ledger_identity(self):
        """The declared press channel is IN the ledger: the full-tick
        identity m*dv == press + weld + gravity + contact + anchor holds
        for every body, every tick, every scenario (an unrecorded impulse
        is the FB3 defect class)."""
        x = self.rec['x_checks']
        self.assertTrue(x['X6_ledger_identity'])
        for label, s in self.trace['scenarios'].items():
            self.assertLessEqual(s['summary']['ledger_residual_max_Ns'],
                                 1e-12, label)

    def test_x7_capacity_anchor(self):
        """The capacity formula bit-reproduces the sealed 3.6697247706422016
        kg at the sealed P; the measured-jn capacity sits inside the
        declared 1e-8 kg window; the ASTRA R1 wording is carried."""
        x = self.rec['x_checks']
        self.assertTrue(x['X7_capacity_anchor'])
        cap = self.rec['capacity_anchor']
        self.assertTrue(cap['formula_bit_reproduced'])
        self.assertEqual(cap['capacity_formula_value_kg'],
                         3.6697247706422016)
        self.assertAlmostEqual(cap['capacity_std_g_N'], 35.98770642201834,
                               places=9)
        self.assertIn('NOT a measured grip force', cap['wording_law'])

    def test_p_honesty_scan(self):
        """Interface honesty: no lambda_min / penalty-stiffness literal, no
        bond construction, the ten named variables are ABSENT with
        verbatim provenance, the placeholders are named, the interface pin
        is declared imported-not-forked, and the press is recorded as
        never actuator-qualified."""
        scan = self.rec['forbidden_literal_scan']
        for name, row in scan.items():
            if isinstance(row, dict) and 'forbidden_hits' in row:
                self.assertEqual(row['forbidden_hits'], [], name)
        self.assertTrue(scan['pinned_bodies_declared'])
        self.assertGreaterEqual(scan['weld_census']['count'], 1)
        self.assertTrue(scan['fb1_hook_default_false'])
        machinery = 0
        for row in scan['weld_census']['lines']:
            text = row['text'].replace('sticky_release_weld', '')
            text = text.replace('weld_recorded_ns', '')
            if 'weld' not in text:
                continue    # compound token only (hook parameter/record)
            if 'FB1' in text or 'weld + gravity' in text:
                continue    # documented hook comment
            # the ONLY remaining allowed form is the FB1 weld-dict
            # machinery (channel init, apply, identity use, ledger record)
            self.assertTrue(
                ('weld = {' in text or 'weld[' in text
                 or 'tuple(weld[' in text or 'weld.items()' in text),
                'weld line outside the FB1 channel: %s' % row)
            machinery += 1
        self.assertLessEqual(machinery, 4, machinery)
        absent = {v['name']: v for v in self.rec['named_absent_variables']}
        for v in ('x_press', 'x_share', 'x_aperture', 'x_reach', 'x_com',
                  'x_inertia', 'x_trajectory', 'x_sequence', 'x_losses',
                  'x_trunk_strength'):
            self.assertIn(v, absent)
            self.assertEqual(absent[v]['status'], 'ABSENT')
            self.assertTrue(absent[v]['provenance_verbatim'])
        self.assertFalse(self.rec['press_channel']['actuator_qualified'])
        self.assertTrue(self.rec['interface']['imported_not_forked'])
        self.assertIn('declared_placeholder', self.rec['placeholders']
                      ['provenance'])

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

    def test_r_regression_green(self):
        """The upstream M06 suite re-ran unmodified on this revision."""
        self.assertTrue(self.reg['P_regression_suite_green'])
        self.assertEqual(self.reg['exit_code'], 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
