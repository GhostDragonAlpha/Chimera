"""MAT2-M05 unit tests: frozen probes P1-P10 and falsifier bites F1-F6.

Run from this directory:
    python -B test_interface_exchange.py
or
    python -B -m unittest test_interface_exchange -v
"""
from __future__ import annotations

import json
import pathlib
import sys
import unittest

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import interface_exchange as ix  # noqa: E402
import material_state  # noqa: E402


def fresh_rig():
    a, b = ix.build_bodies()
    c = ix.ContactInterface('contact:ab_seam', a, b,
                            {'body_a': 'port:seam', 'body_b': 'port:seam'})
    bond = ix.BondElement('bond:strap', a, b,
                          {'body_a': 'port:bond_anchor',
                           'body_b': 'port:bond_anchor'}, 'force_moment')
    run = ix.TwoBodyRun((a, b), c, bond)
    origins = {'world': np.zeros(3), 'anchor_a': a.anchor, 'anchor_b': b.anchor}
    return run, origins


class P1Geometry(unittest.TestCase):
    def test_exact_interface_geometry(self):
        a, b = ix.build_bodies()
        self.assertAlmostEqual(float(a.iface_areas[0]), 0.0100, places=15)
        self.assertAlmostEqual(float(a.iface_areas[1]), 0.0075, places=15)
        self.assertAlmostEqual(a.iface_area, 0.0175, places=15)
        self.assertAlmostEqual(b.iface_area, 0.0175, places=15)
        for body in (a, b):
            rep = body.membrane.closure_report()
            self.assertEqual(rep['open_edge_count'], 0)
            self.assertAlmostEqual(rep['signed_volume_m3'],
                                   0.0175 * 0.16 / 3.0, places=18)
        # face normals bitwise +-x
        for n in a.membrane.normals[:2]:
            self.assertTrue(np.all(n == np.array([1.0, 0.0, 0.0])))
        for n in b.membrane.normals[:2]:
            self.assertTrue(np.all(n == np.array([-1.0, 0.0, 0.0])))
        # anchors coincide bitwise at gap 0
        self.assertTrue(np.array_equal(a.anchor, b.anchor))


class P2ContactReciprocity(unittest.TestCase):
    def test_bitwise_reciprocity_and_area_scaling(self):
        a, b = ix.build_bodies()
        c = ix.ContactInterface('contact:ab_seam', a, b, {})
        b.x[:, 0] -= 5.0e-4                      # declared penetration
        f_a, f_b, p = c.tractions()
        self.assertTrue(np.array_equal(f_a, -f_b))
        self.assertGreater(p, 0.0)
        self.assertAlmostEqual(p, ix.K_CONTACT_PA_PER_M * 5.0e-4, places=9)
        # per-triangle area ratio 4/3 (area scaling, never area-independent)
        ratio = abs(f_b[0, 0]) / abs(f_b[1, 0])
        self.assertAlmostEqual(ratio, a.iface_areas[0] / a.iface_areas[1],
                               places=12)
        # summed interface force bitwise zero and torque <= 1e-15 about origins
        net = f_a.sum(axis=0) + f_b.sum(axis=0)
        self.assertTrue(np.all(net == 0.0))
        for origin in (np.zeros(3), a.anchor, b.anchor):
            tau = (np.cross(b.anchor - origin, f_b.sum(axis=0))
                   + np.cross(a.anchor - origin, f_a.sum(axis=0)))
            self.assertLessEqual(float(np.abs(tau).max()), 1e-15)
        # undeclared contact refused
        c2 = ix.ContactInterface('x', a, b, {})
        c2.declared = False
        with self.assertRaisesRegex(ValueError, 'contact_interface_undeclared'):
            c2.tractions()


class P3BondElement(unittest.TestCase):
    def test_exact_element_laws(self):
        a, b = ix.build_bodies()
        bond = ix.BondElement('bond:strap', a, b, {}, 'force_moment')
        with self.assertRaisesRegex(ValueError, 'bond_not_bound'):
            bond.force_on_b()
        bond.bind(0)
        with self.assertRaisesRegex(ValueError, 'bond_already_bound'):
            bond.bind(1)
        b.x[:, 0] += 0.024
        t = bond.tension()
        self.assertAlmostEqual(t, ix.K_TENSION_N_PER_M * 0.024, places=15)
        f_b = bond.force_on_b()
        self.assertTrue(np.array_equal(f_b, -t * ix.XHAT))
        self.assertTrue(np.array_equal(bond.force_on_b(),
                                       -bond.force_on_a()))
        self.assertAlmostEqual(bond.stored_energy(),
                               0.5 * ix.K_TENSION_N_PER_M * 0.024 ** 2,
                               places=15)
        # twist couple pair (element level, declared inputs)
        m = bond.twist_couple(0.1)
        self.assertAlmostEqual(m, ix.K_TWIST_N_M_PER_RAD * 0.1, places=15)
        u_twist = bond.stored_energy(0.1)
        self.assertAlmostEqual(u_twist,
                               0.5 * ix.K_TENSION_N_PER_M * 0.024 ** 2
                               + 0.5 * ix.K_TWIST_N_M_PER_RAD * 0.01,
                               places=15)
        # tension-only: compression carries nothing
        b.x[:, 0] -= 0.030
        self.assertEqual(bond.tension(), 0.0)
        self.assertEqual(bond.stored_energy(), 0.0)
        # release law
        b.x[:, 0] += 0.024
        u_at = bond.stored_energy()
        bond.release(1)
        with self.assertRaisesRegex(ValueError, 'release_of_unbound_bond'):
            bond.release(2)
        self.assertEqual(bond.force_on_b().tolist(), [0.0, 0.0, 0.0])
        self.assertEqual(bond.stored_energy(), 0.0)
        self.assertEqual(bond.e_release_j, u_at)


class P4NoAutoBond(unittest.TestCase):
    def test_proximity_and_containment_never_bond(self):
        a, b = ix.build_bodies()
        b.x[:, 0] -= 1.0e-3                     # overlapping neighbor
        doc = ix.state_document(1, (a, b), 'loaded', bond_bound=False)
        summary = material_state.validate_material_state(doc)
        self.assertEqual(summary['bond_count'], 0)
        self.assertEqual(summary['contact_count'], 1)
        contained = ix.state_document(1, (a, b), 'loaded', bond_bound=False,
                                      contained=True)
        s2 = material_state.validate_material_state(contained)
        self.assertEqual(s2['bond_count'], 0)
        self.assertEqual(s2['region_count'], 3)
        with self.assertRaisesRegex(ValueError, 'auto_bond_refused'):
            ix.refuse_auto_bond()


class P5Inventory(unittest.TestCase):
    def test_shared_face_and_mass_counted_once(self):
        a, b = ix.build_bodies()
        inv = ix.interface_inventory(a, b, bond_bound=True)
        self.assertAlmostEqual(inv['total_area_m2'],
                               a.membrane.surface_area()
                               + b.membrane.surface_area() - 0.0175, places=18)
        self.assertAlmostEqual(inv['total_mass_kg'], 0.072, places=15)
        roles = {r['matter_id']: r for r in inv['mass_rows']}
        self.assertEqual(roles['mat_iface']['owner_region'], 'body_a')
        self.assertEqual(roles['mat_iface']['referenced_by'], 'body_b')
        # double-count tamper shifts by exactly the shared face
        tampered = inv['total_area_m2'] + 0.0175
        self.assertAlmostEqual(tampered - inv['total_area_m2'], 0.0175,
                               places=18)
        # re-owning the shared matter trips M01's validator
        doc = ix.state_document(1, (a, b), 'loaded', bond_bound=True)
        doc['regions'][1]['matter_claims'][1]['role'] = 'owner'
        with self.assertRaisesRegex(ValueError, 'duplicate_matter_owner'):
            material_state.validate_material_state(doc)


class P6StateDocuments(unittest.TestCase):
    def test_m01_validation_bound_and_released(self):
        a, b = ix.build_bodies()
        doc = ix.state_document(1, (a, b), 'loaded', bond_bound=True)
        s1 = material_state.validate_material_state(doc)
        self.assertEqual(s1['region_count'], 2)
        self.assertEqual(s1['port_count'], 4)
        self.assertEqual(s1['matter_count'], 3)
        self.assertEqual(s1['owner_count'], 3)
        self.assertEqual(s1['reference_count'], 1)
        self.assertAlmostEqual(s1['total_mass_kg'], 0.072, places=15)
        self.assertEqual(s1['contact_count'], 1)
        self.assertEqual(s1['bond_count'], 1)
        released = ix.state_document(2, (a, b), 'loaded', bond_bound=False)
        s2 = material_state.validate_material_state(released)
        self.assertEqual(s2['bond_count'], 0)
        self.assertEqual(s2['contact_count'], 1)


class P7DynamicRun(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        run, origins = fresh_rig()
        cls.ticks = run.run(24, origins)
        run2, origins2 = fresh_rig()
        cls.ticks_replay = run2.run(24, origins2)

    def test_t9_bounds(self):
        g11 = self.ticks[11]['gap_m']
        self.assertGreaterEqual(g11, 0.008)
        self.assertLessEqual(g11, 0.020)
        g13 = self.ticks[13]['gap_m']
        self.assertGreaterEqual(g13, 0.015)
        self.assertLessEqual(g13, 0.045)
        peak = max(t['gap_m'] for t in self.ticks)
        self.assertGreaterEqual(peak, 0.025)
        self.assertLessEqual(peak, 0.045)
        self.assertLessEqual(min(t['gap_m'] for t in self.ticks), -0.004)
        self.assertGreaterEqual(min(t['gap_m'] for t in self.ticks), -0.012)
        self.assertLessEqual(max(t['max_speed_m_per_s'] for t in self.ticks),
                             6.0)
        last = self.ticks[-1]
        self.assertEqual(last['contact_state'], 'loaded')
        self.assertFalse(last['bond_active'])
        for t in self.ticks:
            self.assertTrue(t['residual_within_bound'], t['tick'])
            self.assertLessEqual(t['transverse_anchor_offset_m'], 3.0e-3)

    def test_t10_held_then_separated(self):
        window = [self.ticks[t]['bond_tension_n'] for t in (7, 8, 9, 10)]
        for x, y in zip(window, window[1:]):
            self.assertGreater(y, x)
            self.assertGreater(y, 0.0)
        peak = max(t['gap_m'] for t in self.ticks[11:])
        release_gap = self.ticks[11]['gap_m']
        self.assertGreaterEqual(peak - release_gap, 0.005)

    def test_t7_per_tick_reciprocity(self):
        for t in self.ticks:
            net = t['interface_net_force_n']
            self.assertTrue(np.all(np.asarray(net) == 0.0), t['tick'])
            # derived couple bound: equal/opposite pairs at transverse port
            # offset d carry the net couple |d| * F_pair (A2)
            bound = (t['interface_pair_force_n']
                     * t['transverse_anchor_offset_m'] + 1e-14)
            for vec in t['interface_torque_nm'].values():
                self.assertLessEqual(max(abs(v) for v in vec), bound,
                                     t['tick'])

    def test_t8_determinism(self):
        h1 = ix.replay_hash(self.ticks)
        h2 = ix.replay_hash(self.ticks_replay)
        self.assertEqual(h1, h2)


class FalsifierBites(unittest.TestCase):
    def _ticks(self, mutate):
        ix_tmp_schedule = dict(ix.SCHEDULE)
        ix_tmp_release = ix.RELEASE_TICK
        try:
            return mutate()
        finally:
            ix.SCHEDULE = ix_tmp_schedule
            ix.RELEASE_TICK = ix_tmp_release

    def test_f1_hidden_hinge_after_release(self):
        def real():
            run, origins = fresh_rig()
            return run.run(24, origins)
        real_ticks = self._ticks(real)

        def tampered():
            original_force = ix.BondElement.force_on_b

            def stale(self):
                if not self.active and self.released_tick is not None:
                    d = self.delta()
                    e = float(np.dot(d, ix.XHAT)) - ix.BOND_REST_LENGTH_M
                    return -ix.K_TENSION_N_PER_M * max(0.0, e) * ix.XHAT
                return original_force(self)
            ix.BondElement.force_on_b = stale
            try:
                run, origins = fresh_rig()
                return run.run(24, origins)
            finally:
                ix.BondElement.force_on_b = original_force
        tam_ticks = self._ticks(tampered)
        # real code: bitwise zero after release; tamper: residual >= 1e-3 N
        for t in real_ticks[12:]:
            self.assertEqual(t['bond_force_n'], [0.0, 0.0, 0.0])
        worst = max(max(abs(v) for v in t['bond_force_n'])
                    for t in tam_ticks[12:])
        self.assertGreaterEqual(worst, 1e-3)

    def test_f2_auto_bond_on_proximity(self):
        a, b = ix.build_bodies()
        b.x[:, 0] -= 1.0e-3
        clean = ix.state_document(1, (a, b), 'loaded', bond_bound=False)
        self.assertEqual(
            material_state.validate_material_state(clean)['bond_count'], 0)
        tampered = ix.state_document(1, (a, b), 'loaded', bond_bound=True)
        # the auto-bond defect: a bond exists with no bind call
        self.assertEqual(
            material_state.validate_material_state(tampered)['bond_count'], 1)
        # the same T5 probe that passes on clean data fails on the tamper
        with self.assertRaises(AssertionError):
            self.assertEqual(
                material_state.validate_material_state(
                    tampered)['bond_count'], 0)

    def test_f3_nonreciprocal_transfer(self):
        a, b = ix.build_bodies()
        c = ix.ContactInterface('contact:ab_seam', a, b, {})
        b.x[:, 0] -= 5.0e-4
        f_a, f_b, _ = c.tractions()
        net = f_a.sum(axis=0) + f_b.sum(axis=0)
        self.assertTrue(np.all(net == 0.0))
        tampered_a = f_a * 0.5                # drop the exact negation
        net_t = tampered_a.sum(axis=0) + f_b.sum(axis=0)
        self.assertGreaterEqual(float(np.abs(net_t).max()), 1e-3)

    def test_f4_shared_double_count_detected(self):
        a, b = ix.build_bodies()
        inv = ix.interface_inventory(a, b, bond_bound=True)
        self.assertAlmostEqual(inv['total_mass_kg'], 0.072, places=15)
        double = inv['total_mass_kg'] + ix.MASS_IFACE_KG
        self.assertGreater(double - inv['total_mass_kg'], 1e-12)
        doc = ix.state_document(1, (a, b), 'loaded', bond_bound=True)
        doc['regions'][1]['matter_claims'][1]['role'] = 'owner'
        with self.assertRaises(ValueError):
            material_state.validate_material_state(doc)

    def test_f5_area_independent_contact_detected(self):
        a, b = ix.build_bodies()
        c = ix.ContactInterface('contact:ab_seam', a, b, {})
        b.x[:, 0] -= 5.0e-4
        _, f_b, p = c.tractions()
        ratio = abs(f_b[0, 0]) / abs(f_b[1, 0])
        self.assertAlmostEqual(ratio, 4.0 / 3.0, places=9)
        areas = c.shared_partition()
        tampered = np.array([p * areas.sum() / 2.0] * 2)   # equal split
        ratio_t = abs(tampered[0]) / abs(tampered[1])
        self.assertAlmostEqual(ratio_t, 1.0, places=12)
        self.assertNotAlmostEqual(ratio_t, 4.0 / 3.0, places=3)

    def test_f6_unaccounted_release_energy(self):
        run, origins = fresh_rig()
        ticks = run.run(24, origins)
        rel = ticks[11]
        self.assertGreater(rel['e_diss_release_j'], 0.0)
        self.assertLessEqual(abs(rel['residual_r_j']),
                             rel['residual_bound_j'])
        # dropping the release dissipation must exceed the release bound
        omitted = abs(rel['residual_r_j'] + rel['e_diss_release_j'])
        self.assertGreater(
            omitted, max(5e-2 * rel['e_diss_release_j'], 1e-12))


if __name__ == '__main__':
    unittest.main(verbosity=2)
