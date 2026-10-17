import copy
import unittest
import tempfile
from pathlib import Path
import numpy as np
from .core import Refusal, digest, file_hash, recipe as recipe1
from .core2 import (recipe2, validate_recipe2, detailed2, measure_quadratic,
                    quadratic_from_measurements, Response2, equilibrium2, QUAD_DOMAIN)
from .verify2 import (heron_energy, heron_reaction, verify_samples2, stiffness_detailed,
                      stiffness_heron, verify_quadratic2, verify_equilibrium2, LIMITS2)
from .faa_port import patch_spec, admit, measure_transfer, equilibrium_loaded_port
from .runner2 import run2, check2, read, write

BOX = np.array([[-.25, .25], [-.25, .25]])
ANCHORS = [(-.08, -.06), (.07, .11)]

def detailed_piece(r):
    return lambda h: detailed2(r, float(h[0]), float(h[1]))

class TwoPortTests(unittest.TestCase):
    def test_heron_reference_agreement(self):
        cases = []
        for s in range(3):
            for scale in [.5, 1., 2.]:
                for hp, hq in [(-.31, .12), (0., 0.), (.27, -.33)]:
                    r = recipe2(s)
                    cases.append({'recipe': r, 'hp': hp*scale, 'hq': hq*scale, 'scale': scale, 'gamma': 1.})
        values = [detailed2(c['recipe'], c['hp'], c['hq'], c['scale']) for c in cases]
        report = verify_samples2(cases, values)
        self.assertLessEqual(report['max_energy_error_normalized'], LIMITS2['heron_energy'])
        self.assertLessEqual(report['max_reaction_error_normalized'], LIMITS2['heron_reaction'])

    def test_cross_stiffness_symmetric_and_coupled(self):
        for s in range(3):
            r = recipe2(s)
            for hp, hq in [(0.12, -0.18), (-0.25, 0.05), (0.3, 0.3)]:
                d = stiffness_detailed(r, hp, hq); h = stiffness_heron(r, hp, hq)
                self.assertLess(np.max(np.abs(d - d.T)), LIMITS2['hessian_symmetry'])
                self.assertLess(np.max(np.abs(d - h)), LIMITS2['cross_stiffness'])
                self.assertGreater(abs(d[0, 1]), LIMITS2['coupling_fraction']*min(d[0, 0], d[1, 1]))

    def test_recipe_validation_refusals(self):
        r = recipe2(); r['law'] = 'muscle'
        with self.assertRaises(Refusal): validate_recipe2(r)
        r = recipe2(); p, q = np.array(r['port_xy']); r['port_xy'] = [p.tolist(), (0.9*p).tolist()]
        with self.assertRaises(Refusal): validate_recipe2(r)      # same side of the axis
        r = recipe2(); r['port_xy'] = [[0.01, 0.05], [-0.3, -0.3]]
        with self.assertRaises(Refusal): validate_recipe2(r)      # too central
        r = recipe2(); r['rim_xy'][1] = r['rim_xy'][0]
        with self.assertRaises(Refusal): validate_recipe2(r)      # degenerate rim

    def test_quadratic_domain_spd_and_forgery(self):
        r = recipe2(0); K, e0 = measure_quadratic(r)
        a = quadratic_from_measurements(r, K, e0, measured_errors={'reaction': 1e-4, 'energy': 1e-5})
        fn = Response2(a)
        self.assertTrue(verify_quadratic2(r, a)['passes'])
        with self.assertRaises(Refusal): fn([QUAD_DOMAIN*1.01, 0.])
        with self.assertRaises(Refusal): fn([0., 0.], scale=3.)
        a['K'] = np.array([[1., 0.], [0., -1.]]).tolist(); a['sha256'] = digest({k: v for k, v in a.items() if k != 'sha256'})
        with self.assertRaises(Refusal): Response2(a)             # not SPD even with rewritten hash
        # energy_at_origin is a constant offset invisible in reactions; Response2
        # cannot detect its tampering. check2's independent recompute can, and does
        # (test_full_workflow... quadratic forgery below).
        a = quadratic_from_measurements(r, K, e0, measured_errors={'reaction': 1e-4, 'energy': 1e-5})
        a['energy_at_origin'] += 1; a['sha256'] = digest({k: v for k, v in a.items() if k != 'sha256'})
        Response2(a)   # accepted by design at artifact level

    def test_equilibrium_matches_independent_cg(self):
        a, b = recipe2(0), recipe2(1)
        pieces = [(detailed_piece(r), an) for r, an in zip([a, b], ANCHORS)]
        for loads in [(-0.3, 0.45), (0.5, -0.2)]:
            m = equilibrium2(pieces, loads, BOX)
            c = verify_equilibrium2([(a, ANCHORS[0]), (b, ANCHORS[1])], loads, BOX, m)
            self.assertLessEqual(c['q_error_m'], LIMITS2['equilibrium_m'])

    def test_reduced_equilibrium_within_budget(self):
        a, b = recipe2(0), recipe2(1)
        qs = []
        for r in (a, b):
            K, e0 = measure_quadratic(r)
            qs.append(quadratic_from_measurements(r, K, e0, measured_errors={'reaction': 0., 'energy': 0.}))
        red_anchors = [(-.008, -.006), (.006, .004)]
        box = np.array([[-.012, .012], [-.012, .012]])
        det = equilibrium2([(detailed_piece(r), an) for r, an in zip([a, b], red_anchors)], (0.02, -0.03), box)
        red = equilibrium2([(Response2(q), an) for q, an in zip(qs, red_anchors)], (0.02, -0.03), box)
        self.assertLessEqual(np.max(np.abs(np.array(det['q']) - np.array(red['q']))), LIMITS2['equilibrium_m'])

    def test_excessive_load_refused_and_inputs_unchanged(self):
        a, b = recipe2(0), recipe2(1)
        pieces = [(detailed_piece(r), an) for r, an in zip([a, b], ANCHORS)]
        with self.assertRaises(Refusal): equilibrium2(pieces, (1e6, 0.), BOX)

class FiniteAreaPortTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec, cls.area = patch_spec()
        cls.fan = recipe1(0)

    def test_admission_and_falsifiers(self):
        self.assertEqual(admit(self.spec, self.area)['verdict'], 'full')
        collinear, _ = patch_spec(collinear=True)
        with self.assertRaises(ValueError): collinear.assert_constrains_all_six()
        with self.assertRaises(ValueError): self.spec.assert_min_couple_stiffness(1e-3, kappa_areal=1e8, patch_area=self.area*1.7)

    def test_transfer_balances_and_moment_path(self):
        t = measure_transfer(self.spec, self.fan, [0., 0., 0.01], [0., 0., 0.])
        self.assertLess(t['wrench_balance_force_n'], 1e-9)
        self.assertLess(t['gradient_fd_max_error_relative'], 1e-6)
        self.assertGreater(abs(t['F_b_N'][2]), 0.25*self.spec.Kbar[0, 0]*0.01)
        m = measure_transfer(self.spec, self.fan, [0., 0., 0.], [0.02, 0., 0.])
        self.assertLess(m['wrench_balance_torque_nm'], 1e-9)
        self.assertGreater(max(abs(v) for v in m['tau_b_Nm']), 0.25*self.spec.couple_stiffness_eigen()[0]*0.02)

    def test_loaded_port_equilibrium(self):
        m = equilibrium_loaded_port(self.spec, self.fan, [0., 0., -50.], [0., 2., 0.])
        self.assertLessEqual(m['residual_force_n'], 1e-9)
        self.assertLessEqual(m['residual_torque_nm'], 1e-9)
        self.assertLess(m['carrier_balance_force_n'], 1e-9)
        self.assertLess(m['carrier_balance_torque_nm'], 1e-9)

class WorkflowTests(unittest.TestCase):
    def test_full_workflow_check_resume_and_forgery(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)/'run'; result = run2(out)
            self.assertEqual(result['status'], 'PASS')
            self.assertEqual(check2(out)['status'], 'PASS')
            self.assertEqual(run2(out, resume=True)['status'], 'PASS')
            original = read(out/'measurements.json')
            tampered = copy.deepcopy(original); tampered[0]['reaction'][0] += .1
            write(out/'measurements.json', tampered)
            receipt = read(out/'receipt.json'); receipt['artifacts']['measurements.json'] = file_hash(out/'measurements.json')
            write(out/'receipt.json', receipt)
            with self.assertRaises(Refusal): check2(out)
            write(out/'measurements.json', original)
            receipt = read(out/'receipt.json'); receipt['artifacts']['measurements.json'] = file_hash(out/'measurements.json')
            write(out/'receipt.json', receipt)
            quad = read(out/'ap02_0-quadratic.json'); quad['K'][0][0] *= 1.001
            quad['sha256'] = digest({k: v for k, v in quad.items() if k != 'sha256'})
            write(out/'ap02_0-quadratic.json', quad)
            receipt = read(out/'receipt.json'); receipt['artifacts']['ap02_0-quadratic.json'] = file_hash(out/'ap02_0-quadratic.json')
            write(out/'receipt.json', receipt)
            with self.assertRaises(Refusal): check2(out)

    def test_zero_gamma_control_and_no_extrapolation(self):
        r = recipe2(0)
        v = detailed2(r, .12, -.21, 1., 0.)
        self.assertEqual(v['energy'], 0.); self.assertEqual(v['reaction'], [0., 0.])
        with self.assertRaises(Refusal): detailed2(r, .5, 0.)

if __name__ == '__main__': unittest.main()
