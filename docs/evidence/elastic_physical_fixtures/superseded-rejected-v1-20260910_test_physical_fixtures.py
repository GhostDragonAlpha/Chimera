"""Full-vector CPU fixture packet tests and mutation controls."""
from __future__ import annotations
import hashlib, json, tempfile, unittest
from dataclasses import replace
from pathlib import Path
import numpy as np
from tools.elastic_foundation import physical_fixtures as P

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "docs/evidence/elastic_foundation/fixtures/v1/run_20260908T231140Z"

class PhysicalFixtureTests(unittest.TestCase):
    def test_both_frozen_fixtures_full_reference(self):
        for name in ("trisingle_stretch.npz", "patch_8x4_shear.npz"):
            with self.subTest(name=name):
                f = P.load_fixture(RUN / name)
                r = P.verify_frozen_fixture(f.path)
                self.assertTrue(r["all_ok"], r)
                self.assertTrue(r["finite"])
                self.assertEqual(r["source_npz_sha256"], hashlib.sha256(f.path.read_bytes()).hexdigest())

    def test_mutated_component_is_rejected(self):
        f = P.load_fixture(RUN / "patch_8x4_shear.npz")
        good = P.evaluate_fixture(f)
        forces = good.evaluation.vertex_forces.copy()
        forces[17, 2] += 1.0
        bad = replace(good.evaluation, vertex_forces=forces)
        report = P.validate_result(f, replace(good, evaluation=bad))
        self.assertFalse(report["full_vertex_equal"])
        self.assertFalse(report["all_ok"])

    def test_mutated_energy_and_nonfinite_are_rejected(self):
        f = P.load_fixture(RUN / "trisingle_stretch.npz")
        good = P.evaluate_fixture(f)
        altered = replace(good.evaluation, energy=good.energy_j + 1.0)
        self.assertFalse(P.validate_result(f, replace(good, evaluation=altered))["all_ok"])
        nan = replace(good.evaluation, energy=float("nan"))
        self.assertFalse(P.validate_result(f, replace(good, evaluation=nan))["finite"])

    def test_physical_thickness_scales_full_arrays_once(self):
        f = P.load_fixture(RUN / "trisingle_stretch.npz")
        a = P.evaluate_fixture(f).evaluation
        b = P.evaluate_fixture(replace(f, thickness_m=2.0)).evaluation
        self.assertEqual(b.energy, 2.0 * a.energy)
        np.testing.assert_array_equal(b.corner_forces, 2.0 * a.corner_forces)
        np.testing.assert_array_equal(b.vertex_forces, 2.0 * a.vertex_forces)
        np.testing.assert_array_equal(b.per_face.w_vol, a.per_face.w_vol)
        np.testing.assert_array_equal(b.per_face.F, a.per_face.F)

    def test_output_refuses_overwrite_and_records_provenance(self):
        f = P.load_fixture(RUN / "trisingle_stretch.npz")
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "reference.json"
            P.write_reference(f, out)
            before = out.read_bytes()
            try:
                P.write_reference(f, out)
            except P.FixtureRefusal as caught:
                self.assertEqual(caught.reason, "output_exists")
            else:
                self.fail("existing output was overwritten")
            self.assertEqual(before, out.read_bytes())
            data = json.loads(out.read_text())
            self.assertEqual(data["source_npz_sha256"], f.source_sha256)
            self.assertEqual(data["input_dtype"], "float32")
            self.assertEqual(data["gpu_certification"], "open; CPU reference only")

    def test_reader_rejects_nonfinite_fields(self):
        f = RUN / "trisingle_stretch.npz"
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / f.name
            with np.load(f) as z: fields = {k: z[k] for k in z.files}
            fields["exp_vertex_f64"] = fields["exp_vertex_f64"].copy()
            fields["exp_vertex_f64"][0, 0] = np.nan
            np.savez(p, **fields)
            with self.assertRaisesRegex(P.FixtureRefusal, "nonfinite"):
                P.load_fixture(p)

if __name__ == "__main__": unittest.main()


