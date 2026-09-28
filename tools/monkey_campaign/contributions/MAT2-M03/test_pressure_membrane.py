"""MAT2-M03 tests: named probes P1-P10 and falsifier bites F1-F6.

Mirrors the frozen preregistration (PREREGISTRATION.md, corrections A1-A6) and
the receipt (run_experiment.py). Run from this directory:
    python -B -m unittest test_pressure_membrane -v
"""
from __future__ import annotations

import math
import pathlib
import sys
import unittest

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'MAT2-M01'))

import pressure_membrane as pm  # noqa: E402
import material_state as ms     # noqa: E402  (M01 validator, unmodified)

DT = 1.0 / 300.0
SOURCE_DECL = ('authored demonstrator pressure source (PREREGISTRATION.md T6)')


def src(p_int, p_ext=0.0):
    return pm.PressureSource('t', p_int, p_ext, 5000.0, 1e-3, SOURCE_DECL)


class PressureMembraneTests(unittest.TestCase):
    def setUp(self):
        self.tetra = pm.load_m02_tetra(str(HERE.parent))
        self.field = pm.LinearField(101325.0,
                                    [0.0, 0.0, -pm.RHO_KG_M3 * pm.G_M_S2])

    # ---- closure and volume (P1) -------------------------------------------
    def test_P1_m02_tetra_closure_exact(self):
        rep = self.tetra.closure_report()
        self.assertEqual(rep['open_edge_count'], 0)
        self.assertEqual(rep['duplicate_directed_edges'], 0)
        self.assertEqual(rep['vertex_count'], 4)
        self.assertEqual(rep['triangle_count'], 4)
        self.assertLess(abs(rep['signed_volume_m3']
                            - pm.M02_TETRA_RECORDED_VOLUME_M3), 1e-18)
        self.assertLess(abs(rep['surface_area_m2']
                            - pm.M02_TETRA_RECORDED_AREA_M2), 1e-18)
        self.assertLess(abs(rep['signed_volume_m3'] - 1.0 / 6000.0), 1e-18)

    # ---- traction law (P2) --------------------------------------------------
    def test_P2_area_scaled_traction(self):
        forces, _ = self.tetra.triangle_tractions(src(100.0))
        per_tri = np.linalg.norm(forces, axis=1)
        self.assertLess(np.max(np.abs(per_tri
                                      - np.array([0.5, 0.5, 0.5,
                                                  0.8660254037844386]))),
                        1e-12)
        for i in range(4):
            expect = 100.0 * self.tetra.areas[i]
            self.assertLess(abs(per_tri[i] - expect), 1e-15)

    # ---- zero net loading from uniform pressure (P3) ------------------------
    def test_P3_uniform_pressure_zero_net_everywhere(self):
        meshes = {'m02_tetra': self.tetra,
                  'tetra_L2': pm.subdivide(pm.right_tetra(0.1), 2),
                  'cube_n4': pm.cube_grid(4),
                  'icosphere_L2': pm.icosphere(2, 0.1)}
        for name, mem in meshes.items():
            loads, forces, _ = mem.vertex_loads(src(100.0))
            nf, nt = mem.net_force_torque(forces)
            self.assertLess(float(np.linalg.norm(nf)), 1e-12, name)
            self.assertLess(float(np.linalg.norm(nt)), 1e-12, name)
            self.assertLess(float(np.linalg.norm(loads.sum(axis=0))), 1e-12,
                            name + ' lumped')

    # ---- external linear-field loading (P4) ---------------------------------
    def test_P4_buoyancy_exact_and_torque_free(self):
        s = src(101425.0, 101325.0)
        for name, mem, refined in (('cube_n2', pm.cube_grid(2), True),
                                   ('icosphere_L1', pm.icosphere(1, 1.0),
                                    True),
                                   ('m02_tetra', self.tetra, False)):
            forces, _ = mem.triangle_tractions(s, self.field)
            nf, nt = mem.net_force_torque(forces)
            ref = mem.linear_field_reference(self.field)
            self.assertLess(float(np.linalg.norm(nf - ref['force_n']))
                            / np.linalg.norm(ref['force_n']), 1e-12, name)
            tau_c = nt - np.cross(ref['volume_centroid_m'], nf)
            # torque quadrature converges h^2 (correction A7): refined members
            # are exact to 1e-9; the coarse 4-triangle tetra is bounded and
            # strictly monotone under subdivision
            self.assertLess(float(np.linalg.norm(tau_c)),
                            1e-9 if refined else 1.0e-1, name)
        taus = []
        for mem in (self.tetra, pm.subdivide(self.tetra, 1),
                    pm.subdivide(self.tetra, 2)):
            forces, _ = mem.triangle_tractions(s, self.field)
            nf2, nt = mem.net_force_torque(forces)
            ref = mem.linear_field_reference(self.field)
            tau_c = nt - np.cross(ref['volume_centroid_m'], nf2)
            taus.append(float(np.linalg.norm(tau_c)))
        self.assertGreater(taus[0], taus[1])
        self.assertGreater(taus[1], taus[2])
        cube = pm.cube_grid(2)
        forces, _ = cube.triangle_tractions(s, self.field)
        nf, _ = cube.net_force_torque(forces)
        rgv = pm.RHO_KG_M3 * pm.G_M_S2 * 1.0
        self.assertLess(float(np.linalg.norm(nf - [0.0, 0.0, rgv])) / rgv,
                        1e-12)

    # ---- refinement consistency (P5) ----------------------------------------
    def test_P5_refinement_monotone_volume_convergence(self):
        errs = [abs(pm.icosphere(level, 1.0).signed_volume()
                    - 4.0 / 3.0 * math.pi) / (4.0 / 3.0 * math.pi)
                for level in (0, 1, 2)]
        self.assertGreater(errs[0], errs[1])
        self.assertGreater(errs[1], errs[2])
        self.assertLess(errs[2], 6.0e-2)
        for n in (1, 2, 4):
            self.assertLess(abs(pm.cube_grid(n).signed_volume() - 1.0), 1e-12)

    # ---- P-V work (P6) -------------------------------------------------------
    def test_P6_quasi_static_work_identity(self):
        work = self.tetra.quasi_static_scaling_work(src(101475.0, 101325.0),
                                                    s_final=1.1, steps=2000)
        self.assertLess(work['max_step_traction_volume_diff_j'], 1e-15)
        self.assertLess(abs(work['work_volume_sum_j']
                            - work['work_closed_form_j']), 1e-14)
        self.assertLess(abs(work['work_closed_form_j'] - 8.275e-3), 1e-12)

    # ---- source power and limits (P7) ---------------------------------------
    def test_P7_power_and_named_limits(self):
        power = src(101475.0, 101325.0).power_watts(2.0e-4)
        self.assertLess(abs(power - 0.03), 1e-16)
        with self.assertRaisesRegex(ValueError,
                                    'pressure_source_negative_absolute'):
            pm.PressureSource('bad', -1.0, 0.0, 5000.0, 1e-3, SOURCE_DECL)
        with self.assertRaisesRegex(ValueError,
                                    'pressure_source_delta_p_limit_exceeded'):
            src(6000.0).enforce_delta_p()
        with self.assertRaisesRegex(ValueError,
                                    'pressure_source_flow_limit_exceeded'):
            src(150.0).power_watts(2.0e-3)
        with self.assertRaisesRegex(ValueError,
                                    'pressure_source_undeclared'):
            self.tetra.triangle_tractions(None)

    # ---- dynamic run (P8, P9) ------------------------------------------------
    def test_P8_dynamic_run_frozen_observables(self):
        dyn_source = pm.PressureSource('mem', 120.0, 0.0, 5000.0, 1e-3,
                                       SOURCE_DECL)
        schedule = [120.0 * max(0.0, math.sin(math.pi * tick / 16.0))
                    if tick <= 16 else 0.0 for tick in range(24)]
        run = pm.InflatableRun(pm.icosphere(1, 0.10), dyn_source, 0.05,
                               2.5e-2, 240.0, 8, DT)
        dyn = run.run(schedule)
        drift = max(t['com_drift_m'] for t in dyn['ticks'])
        self.assertLess(drift, 1e-6)
        v0 = dyn['volume_start_m3']
        self.assertGreaterEqual(dyn['volume_peak_m3'] / v0, 1.02)
        self.assertLess(abs(dyn['volume_final_m3'] / v0 - 1.0), 1.0e-2)
        for t in dyn['ticks']:
            allowance = max(1.0 * (abs(t['w_pressure_j'])
                                   + t['e_diss_damping_j'] + t['e_kinetic_j']
                                   + t['e_elastic_j']), 1e-6)
            self.assertLessEqual(abs(t['residual_r_j']), allowance)

    def test_P9_determinism_byte_identical_replay(self):
        def once():
            run = pm.InflatableRun(pm.icosphere(1, 0.10),
                                   pm.PressureSource('mem', 120.0, 0.0,
                                                     5000.0, 1e-3,
                                                     SOURCE_DECL),
                                   0.05, 2.5e-2, 240.0, 8, DT)
            return run.run([120.0 * max(0.0, math.sin(math.pi * tick / 16.0))
                            if tick <= 16 else 0.0 for tick in range(24)])
        self.assertEqual(pm.digest(once()), pm.digest(once()))

    # ---- material_state gate (P10) ------------------------------------------
    def test_P10_experiment_document_validates_under_m01(self):
        receipt = __import__('json').loads(
            (HERE / 'qualification_receipt.json').read_text(encoding='utf-8'))
        doc = __import__('json').loads(
            (HERE / 'pressure_state.json').read_text(encoding='utf-8'))
        summary = ms.validate_material_state(doc)
        self.assertEqual(summary['region_count'], 1)
        self.assertEqual(summary['law_count'], 1)
        self.assertEqual(summary['matter_count'], 1)
        self.assertEqual(summary['reference_count'], 0)
        self.assertAlmostEqual(summary['total_mass_kg'], 0.05, places=12)
        self.assertIn('checks', receipt)
        self.assertTrue(all(c['passed'] for c in receipt['checks']))
        self.assertTrue(all(f['bit'] for f in receipt['falsifier_bites']))

    # ---- falsifier bites (F1-F6) ---------------------------------------------
    def test_F1_area_independent_tamper_changes_net_loading(self):
        forces, _ = self.tetra.triangle_tractions(src(100.0))
        correct = float(np.linalg.norm(forces.sum(axis=0)))
        tampered = (100.0 * float(self.tetra.areas.mean())) \
            * self.tetra.normals
        tampered_net = float(np.linalg.norm(tampered.sum(axis=0)))
        self.assertLess(correct, 1e-12)
        self.assertGreaterEqual(tampered_net, 1e-2)

    def test_F2_uniform_pressure_propels_only_tampered_free_body(self):
        good = pm.InflatableRun(self.tetra, src(100.0), 0.05, 1e-8, 0.0, 4,
                                DT).run([100.0] * 12)
        bad = pm.InflatableRun(self.tetra, src(100.0), 0.05, 1e-8, 0.0, 4,
                               DT,
                               load_mode='constant_per_triangle').run(
                                   [100.0] * 12)
        self.assertLess(good['com_drift_final_m'], 1e-6)
        self.assertGreaterEqual(bad['com_drift_final_m'], 1e-3)

    def test_F4_deleted_triangle_refused(self):
        broken = pm.Membrane(self.tetra.vertices, self.tetra.triangles[:3],
                             'broken')
        with self.assertRaisesRegex(ValueError, 'closure_open_edges'):
            broken.require_closed()
        with self.assertRaisesRegex(ValueError, 'closure_open_edges'):
            broken.triangle_tractions(src(100.0))

    def test_F5_flipped_winding_refused(self):
        tris = self.tetra.triangles.copy()
        tris[3] = tris[3][::-1]
        flipped = pm.Membrane(self.tetra.vertices, tris, 'flipped')
        with self.assertRaisesRegex(ValueError, 'orientation_inconsistent'):
            flipped.require_closed()
        self.assertLess(flipped.signed_volume(), self.tetra.signed_volume())

    def test_F6_area_factor_omitted_breaks_work_account(self):
        template = self.tetra.vertices
        v_unit = self.tetra.signed_volume()
        delta_s = 0.1 / 2000
        buggy = 0.0
        for k in range(1, 2001):
            s_mid = 1.0 + delta_s * (k - 0.5)
            mid = pm.Membrane(template * s_mid, self.tetra.triangles, 'm')
            forces_buggy = 150.0 * mid.normals
            loads = np.zeros_like(mid.vertices)
            np.add.at(loads, self.tetra.triangles[:, 0], forces_buggy / 3.0)
            np.add.at(loads, self.tetra.triangles[:, 1], forces_buggy / 3.0)
            np.add.at(loads, self.tetra.triangles[:, 2], forces_buggy / 3.0)
            buggy += float((loads * delta_s * template).sum())
        correct_w = 150.0 * v_unit * (1.1 ** 3 - 1.0)
        self.assertGreaterEqual(abs(buggy - correct_w), 1e-6)


if __name__ == '__main__':
    unittest.main()
