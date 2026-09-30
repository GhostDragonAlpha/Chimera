"""MAT2-M09 unit suite (python -B test_assembly.py).

Covers the frozen identities and gates that do not need the full 90-tick
trajectory: geometry, element laws, refusals, restraint derivation,
M01 document validation in all three states, the momentum ledger on a
short bound run, and the render/frame-source binding probes.
"""
import json
import pathlib
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import assembly as asm  # noqa: E402
# assembly's upstream path inserts shadow this directory; put it back in
# front so run_experiments resolves to THIS card's module
sys.path.insert(0, str(HERE))
import run_experiments as rexp  # noqa: E402


class Geometry(unittest.TestCase):
    def test_probe_green(self):
        g = rexp.geometry_probe()
        self.assertTrue(g['ok'])

    def test_bones_differ(self):
        a = asm.BoneBody('bone_a', asm.bone_a_vertices(), asm.MASS_A_KG)
        b = asm.BoneBody('bone_b', asm.bone_b_vertices(), asm.MASS_B_KG)
        self.assertNotEqual(asm.MASS_A_KG, asm.MASS_B_KG)
        self.assertGreater(float(abs(a.rest - b.rest).max()), 0.0)


class Elements(unittest.TestCase):
    def test_element_tests_green(self):
        et = asm.element_tests()
        self.assertTrue(all(v for k, v in et.items() if k != 'refusals'))
        self.assertEqual(et['refusals'], {
            'bond_not_bound': True, 'bond_already_bound': True,
            'release_of_unbound_bond': True, 'auto_bond_refused': True})

    def test_release_bitwise(self):
        run = asm.AssemblyRun()
        for t in range(asm.RELEASE_TICK + 1):
            run.step(t)
        self.assertGreater(run.lig.e_release_j, 0.0)
        self.assertEqual(run.lig.tension(), 0.0)
        self.assertTrue(all(c == 0.0 for c in run.lig.force_on_b()))
        self.assertEqual(run.lig.stored_energy(), 0.0)


class Restraint(unittest.TestCase):
    def test_bound_then_zero(self):
        k, contrib = asm.restraint_matrix(None, None)
        self.assertEqual(k.sum(), 0.0)
        self.assertEqual(asm.restrained_direction_count(k), 0)
        bones = (asm.BoneBody('bone_a', asm.bone_a_vertices(),
                              asm.MASS_A_KG),
                 asm.BoneBody('bone_b', asm.bone_b_vertices(),
                              asm.MASS_B_KG))
        lig = asm.LigamentElement('l', bones[0], bones[1])
        lig.bind(0)
        k2, _ = asm.restraint_matrix(lig, None)
        k2r = asm.restraint_matrix_recomputed(lig, None)
        self.assertGreater(asm.restrained_direction_count(k2), 0)
        self.assertLessEqual(float(abs(k2 - k2r).max())
                             / max(1.0, float(abs(k2).max())), 1e-15)


class Documents(unittest.TestCase):
    def test_three_states_validate(self):
        run = asm.AssemblyRun()
        for t in range(87):
            run.step(t)
        self.assertEqual(run.documents[0]['validator_summary']
                         ['bond_count'], 0)
        self.assertEqual(run.documents[46]['validator_summary']
                         ['bond_count'], 2)
        self.assertEqual(run.documents[86]['validator_summary']
                         ['bond_count'], 0)
        self.assertEqual(
            len(run.documents[46]['document']['contacts']), 1)
        self.assertEqual(
            len(run.documents[86]['document']['bonds']), 0)


class ShortRun(unittest.TestCase):
    def test_ledger_and_gates(self):
        run = asm.AssemblyRun()
        for t in range(70):
            run.step(t)
        worst = max(r['ledger_residual_worst_N_s'] for r in run.ticks)
        self.assertLessEqual(worst, 1e-12)
        self.assertTrue(all(abs(r['residual_r_j'])
                            <= r['residual_bound_j'] for r in run.ticks))
        # the joint contact material loads during the press window (A1)
        self.assertGreater(max(r['joint_jn_Ns'] for r in run.ticks), 0.0)
        ground = max(max(r['ground_jn_N_s'].values()) for r in run.ticks)
        self.assertGreater(ground, 0.0)


class Bindings(unittest.TestCase):
    def test_snapshot_binding(self):
        bone = asm.BoneBody('bone_a', asm.bone_a_vertices(),
                            asm.MASS_A_KG)
        state = {('com', i): float(bone.x.mean(axis=0)[i])
                 for i in range(3)}
        self.assertTrue(rexp.assert_snapshot_binding(bone.x, state))
        with self.assertRaises(ValueError) as cm:
            rexp.assert_snapshot_binding(bone.x + 0.05, state)
        self.assertEqual(str(cm.exception), 'render_unbound_to_state')

    def test_frame_source(self):
        snap = {'tick': 7, 'state_hash': 'abc'}
        self.assertTrue(rexp.assert_frame_source(snap, snap))
        with self.assertRaises(ValueError) as cm:
            rexp.assert_frame_source({'tick': 7, 'state_hash': 'zzz'},
                                     snap)
        self.assertEqual(str(cm.exception), 'overlay_motion_detected')


class Probes(unittest.TestCase):
    def test_ast_probes_green(self):
        self.assertTrue(rexp.p_ast_restraint()['ok'])
        self.assertTrue(rexp.p_ast_no_joint()['ok'])
        self.assertTrue(rexp.p_single_writer()['ok'])


if __name__ == '__main__':
    unittest.main(verbosity=1)
