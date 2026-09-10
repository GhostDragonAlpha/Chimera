"""CPU-only tests for the proposed physical fixture packet v2."""
from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import numpy as np


REPO = Path(os.environ.get("CHIMERA_FIXTURE_REPO", r"E:/ChimeraWork/slot-03")).resolve()
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
_candidate_path = os.environ.get("CHIMERA_FIXTURE_CANDIDATE")
CANDIDATE = Path(_candidate_path).resolve() if _candidate_path else Path(__file__).with_name("physical_fixtures.py")
SPEC = importlib.util.spec_from_file_location("physical_fixture_v2_proposal", CANDIDATE)
P = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = P
SPEC.loader.exec_module(P)

LEGACY = REPO / "docs/evidence/elastic_foundation/fixtures/v1/run_20260908T231140Z"
LEGACY_MANIFEST_SHA = "6ce4116b8bab3b6b2e6820e66dfe457e307a4f2266e2f2497f75d9c0359537bc"
LEGACY_PACKET_SHA = {
    "trisingle_stretch.npz": "2cb83077485447909e22e4322152bdfd8baa835f43dea973604a111024035ded",
    "patch_8x4_shear.npz": "73aaad4a030e7a60b418b07f819a61abe6ac4344c97fee64e23aaa35e7533fd7",
}


def f64_fraction(rows):
    return np.asarray([[float(value) for value in row] for row in rows], dtype=np.float64)


TRI_F = np.asarray([[[6 / 5, 0], [0, 4 / 5], [0, 0]]], dtype=np.float64)
TRI_ENERGY = float(Fraction(713, 22750))
TRI_WBAR = np.asarray([float(Fraction(713, 11375))])
TRI_WVOL = np.asarray([float(Fraction(2852, 91))])
TRI_VERTEX = f64_fraction([
    [Fraction(498, 2275), Fraction(-228, 2275), 0],
    [Fraction(-498, 2275), 0, 0],
    [0, Fraction(228, 2275), 0],
])


class PacketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        cls.packet_dir = cls.root / "packet"
        P.generate(cls.packet_dir, LEGACY, LEGACY_MANIFEST_SHA)
        cls.manifest = cls.packet_dir / "manifest.json"
        cls.manifest_sha = P.sha256_file(cls.manifest)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def packet(self, fixture="rational_triangle"):
        return P.load_packet(self.manifest, self.manifest_sha, fixture)

    def assertBound(self, actual, expected, scale):
        actual, expected, scale = (np.asarray(x, dtype=np.float64) for x in
                                   (actual, expected, scale))
        self.assertEqual(actual.shape, expected.shape)
        bound = P.CPU_GAMMA * scale
        ok = np.where(scale == 0, actual == expected, np.abs(actual - expected) <= bound)
        self.assertTrue(np.all(ok), f"max error={np.max(np.abs(actual-expected))}, bound={np.max(bound)}")

    def rewrite(self, fixture, changes, *, update_inner_hashes=False):
        target = self.root / f"mutated-{fixture}-{len(list(self.root.glob('mutated-*')))}"
        target.mkdir()
        manifest = json.loads(self.manifest.read_text(encoding="utf-8"))
        for source in self.packet_dir.glob("*.npz"):
            destination = target / source.name
            with np.load(source, allow_pickle=False) as z:
                arrays = {key: z[key] for key in z.files}
            if source.stem == fixture:
                arrays.update(changes)
            np.savez_compressed(destination, **arrays)
            entry = manifest["fixtures"][source.stem]
            entry["sha256"] = P.sha256_file(destination)
            if source.stem == fixture and update_inner_hashes:
                entry["source_sha256"] = P.sha256_bytes(arrays["source_json_u8"].tobytes())
                entry["provenance_sha256"] = P.sha256_bytes(arrays["provenance_json_u8"].tobytes())
        (target / "manifest.json").write_bytes(P.canonical_json(manifest) + b"\n")
        return target / "manifest.json", P.sha256_file(target / "manifest.json")

    def test_explicit_material_rounding_and_provenance(self):
        packet = self.packet()
        self.assertEqual(packet.original_material,
                         P.MaterialStream(1000.0, 0.002, 2.0, 0.3, "float64"))
        upload = packet.upload_material
        self.assertEqual(upload.stored_dtype, "float32")
        self.assertEqual(upload.h_m, float(np.float32(0.002)))
        self.assertEqual(upload.nu, float(np.float32(0.3)))
        self.assertEqual(upload.E2_n_per_m,
                         float(np.float32(np.float64(np.float32(1000.0)) *
                                          np.float64(np.float32(0.002)))))
        self.assertEqual(packet.provenance["kind"], "synthetic")
        self.assertEqual(P.sha256_bytes(P.canonical_json(packet.provenance)),
                         packet.provenance_sha256)
        self.assertNotEqual(packet.current_original.tobytes(),
                            packet.current_upload.astype(np.float64).tobytes())

    def test_original_triangle_full_rational_oracle(self):
        packet = self.packet()
        result = P.evaluate_packet(packet, "original")
        ref = packet.original_reference
        self.assertBound(result.evaluation.per_face.F, TRI_F, ref.scale_F)
        self.assertBound(result.energy_j, TRI_ENERGY, ref.scale_energy)
        self.assertBound(result.surface_energy_j_per_m2, TRI_WBAR, ref.scale_Wbar)
        self.assertBound(result.volume_energy_j_per_m3, TRI_WVOL, ref.scale_wvol)
        self.assertBound(result.corner_forces_n, TRI_VERTEX[None, :, :], ref.scale_corner)
        self.assertBound(result.vertex_forces_n, TRI_VERTEX, ref.scale_vertex)

    def test_canonical_patch_complete_original_and_upload_references(self):
        packet = self.packet("canonical_patch_8x4")
        self.assertEqual(packet.rest_original.shape, (45, 3))
        self.assertEqual(packet.faces.shape, (64, 3))
        self.assertEqual(packet.source["legacy_usage"],
                         "geometry compatibility only; material and expected fields unread")
        for mode, reference in (("original", packet.original_reference),
                                ("upload", packet.upload_reference)):
            result = P.evaluate_packet(packet, mode)
            self.assertTrue(np.any(reference.F != 0))
            self.assertTrue(np.any(reference.Wbar != 0))
            self.assertTrue(np.any(reference.wvol != 0))
            self.assertTrue(np.any(reference.corner != 0))
            self.assertTrue(np.any(reference.vertex != 0))
            self.assertNotEqual(reference.energy, 0)
            P.validate_evaluation(packet, mode, result)

    def test_upload_reference_consumes_stored_binary32_values(self):
        packet = self.packet()
        self.assertFalse(np.array_equal(packet.original_reference.F, packet.upload_reference.F))
        self.assertNotEqual(packet.original_reference.energy, packet.upload_reference.energy)
        upload = P.evaluate_packet(packet, "upload")
        self.assertBound(upload.energy_j, packet.upload_reference.energy,
                         packet.upload_reference.scale_energy)
        self.assertEqual(upload.material.input_modulus_unit, "N/m")
        self.assertEqual(upload.material.thickness_m, packet.upload_material.h_m)

    def test_in_memory_B_area_and_csr_mutations_are_refused(self):
        packet = self.packet("canonical_patch_8x4")
        B = packet.B_upload.copy(); B[0, 0, 0] += np.float32(0.5)
        with self.assertRaisesRegex(P.FixtureRefusal, "stored B/area"):
            P.evaluate_packet(replace(packet, B_upload=B), "upload")
        area = packet.areas_upload.copy(); area[0] *= np.float32(2)
        with self.assertRaisesRegex(P.FixtureRefusal, "stored B/area"):
            P.evaluate_packet(replace(packet, areas_upload=area), "upload")
        corners = packet.csr_corners_upload.copy(); corners[[0, 1]] = corners[[1, 0]]
        with self.assertRaises(P.FixtureRefusal) as caught:
            P.evaluate_packet(replace(packet, csr_corners_upload=corners), "upload")
        self.assertEqual(caught.exception.reason, P.FixtureReason.CSR)

    def test_reader_rejects_malformed_csr_even_with_new_manifest_anchor(self):
        packet = self.packet("canonical_patch_8x4")
        bad = packet.csr_offsets_upload.copy(); bad[1] = np.uint32(99)
        manifest, anchor = self.rewrite("canonical_patch_8x4",
                                        {"csr_offsets_upload_u32": bad})
        with self.assertRaises(P.FixtureRefusal) as caught:
            P.load_packet(manifest, anchor, "canonical_patch_8x4")
        self.assertEqual(caught.exception.reason, P.FixtureReason.CSR)

    def test_reader_rejects_f64_upload_positions_and_bool_thickness(self):
        packet = self.packet()
        for field, value in (
            ("rest_pos_upload_f32", packet.rest_upload.astype(np.float64)),
            ("h_original_f64", np.asarray(True, dtype=np.bool_)),
            ("h_upload_f32", np.asarray(True, dtype=np.bool_)),
        ):
            with self.subTest(field=field):
                manifest, anchor = self.rewrite("rational_triangle", {field: value})
                with self.assertRaises(P.FixtureRefusal) as caught:
                    P.load_packet(manifest, anchor, "rational_triangle")
                self.assertEqual(caught.exception.reason, P.FixtureReason.DTYPE)

    def test_adjacent_manifest_cannot_replace_external_trust_anchor(self):
        changed = P._u8({"kind": "synthetic", "declaration_id": "changed",
                         "purpose": "changed"})
        manifest, new_anchor = self.rewrite("rational_triangle",
                                            {"provenance_json_u8": changed},
                                            update_inner_hashes=True)
        self.assertNotEqual(new_anchor, self.manifest_sha)
        with self.assertRaises(P.FixtureRefusal) as caught:
            P.load_packet(manifest, self.manifest_sha, "rational_triangle")
        self.assertEqual(caught.exception.reason, P.FixtureReason.TRUST_ANCHOR)

    def test_source_and_provenance_inner_hashes_are_enforced(self):
        for field, reason in (("source_json_u8", P.FixtureReason.SOURCE),
                              ("provenance_json_u8", P.FixtureReason.PROVENANCE)):
            with self.subTest(field=field):
                manifest, anchor = self.rewrite("rational_triangle", {field: P._u8({"x": 1})})
                with self.assertRaises(P.FixtureRefusal) as caught:
                    P.load_packet(manifest, anchor, "rational_triangle")
                self.assertEqual(caught.exception.reason, reason)

    def test_rehashed_source_and_canonical_geometry_mutations_are_refused(self):
        source = P._u8({"kind": "analytic_recipe", "recipe": "wrong",
                        "legacy_usage": "none"})
        manifest, anchor = self.rewrite("rational_triangle", {"source_json_u8": source},
                                        update_inner_hashes=True)
        with self.assertRaises(P.FixtureRefusal) as caught:
            P.load_packet(manifest, anchor, "rational_triangle")
        self.assertEqual(caught.exception.reason, P.FixtureReason.SOURCE)

        packet = self.packet()
        current = packet.current_original.copy(); current[1, 0] = 1.1
        upload = current.astype(np.float32)
        manifest, anchor = self.rewrite("rational_triangle", {
            "cur_pos_original_f64": current,
            "cur_pos_upload_f32": upload,
        })
        with self.assertRaises(P.FixtureRefusal) as caught:
            P.load_packet(manifest, anchor, "rational_triangle")
        self.assertEqual(caught.exception.reason, P.FixtureReason.GEOMETRY)

    def test_zero_Wbar_wvol_actual_evaluator_mutant_is_killed(self):
        packet = self.packet()
        real = P._evaluate_physical

        def zero_density(rest, material, positions):
            result = real(rest, material, positions)
            face = replace(result.evaluation.per_face,
                           Wbar=np.zeros_like(result.evaluation.per_face.Wbar),
                           w_vol=np.zeros_like(result.evaluation.per_face.w_vol))
            return replace(result, evaluation=replace(result.evaluation, per_face=face))

        with mock.patch.object(P, "_evaluate_physical", side_effect=zero_density):
            with self.assertRaises(P.FixtureRefusal) as caught:
                P.evaluate_packet(packet, "original")
        self.assertEqual(caught.exception.reason, P.FixtureReason.REFERENCE)

    def test_malformed_actual_evaluator_result_is_named_refusal(self):
        packet = self.packet()
        with mock.patch.object(P, "_evaluate_physical", return_value=SimpleNamespace()):
            with self.assertRaises(P.FixtureRefusal) as caught:
                P.evaluate_packet(packet, "upload")
        self.assertEqual(caught.exception.reason, P.FixtureReason.REFERENCE)

    def test_omit_and_double_thickness_actual_evaluator_mutants_are_killed(self):
        packet = self.packet()
        real = P.evaluate_physical_v1

        def mutated(factor):
            def run(rest, material, positions):
                bad = P.admit_surface_v1(
                    material.surface_young_modulus_n_per_m * factor,
                    material.thickness_m, material.poisson_ratio,
                    provenance=material.provenance,
                )
                return real(rest, bad, positions)
            return run

        # omit h: use E3d as E2 => x500. double h: multiply E2 by h => x0.002.
        for label, factor in (("omit", 500.0), ("double", packet.original_material.h_m)):
            with self.subTest(label=label), mock.patch.object(
                    P, "_evaluate_physical", side_effect=mutated(factor)):
                with self.assertRaises(P.FixtureRefusal) as caught:
                    P.evaluate_packet(packet, "original")
                self.assertEqual(caught.exception.reason, P.FixtureReason.REFERENCE)

    def test_dropped_provenance_actual_evaluator_mutant_is_killed(self):
        packet = self.packet()
        real = P._evaluate_physical

        def drop(rest, material, positions):
            result = real(rest, material, positions)
            bad_material = SimpleNamespace(provenance=SimpleNamespace(declaration_id="dropped"))
            return replace(result, material=bad_material)

        with mock.patch.object(P, "_evaluate_physical", side_effect=drop):
            with self.assertRaises(P.FixtureRefusal) as caught:
                P.evaluate_packet(packet, "upload")
        self.assertEqual(caught.exception.reason, P.FixtureReason.PROVENANCE)

    def test_reference_mutation_is_rejected_after_valid_reader_path(self):
        packet = self.packet()
        zeros = np.zeros_like(packet.original_reference.Wbar)
        manifest, anchor = self.rewrite("rational_triangle", {
            "ref_original_Wbar_f64": zeros,
            "ref_original_wvol_f64": zeros,
        })
        mutated = P.load_packet(manifest, anchor, "rational_triangle")
        with self.assertRaises(P.FixtureRefusal) as caught:
            P.evaluate_packet(mutated, "original")
        self.assertEqual(caught.exception.reason, P.FixtureReason.REFERENCE)

    def test_material_inconsistency_and_extra_schema_field_are_refused(self):
        manifest, anchor = self.rewrite("rational_triangle",
                                        {"E2_original_f64": np.asarray(3.0)})
        with self.assertRaises(P.FixtureRefusal) as caught:
            P.load_packet(manifest, anchor, "rational_triangle")
        self.assertEqual(caught.exception.reason, P.FixtureReason.MATERIAL)
        manifest, anchor = self.rewrite("rational_triangle", {"unused": np.asarray(1.0)})
        with self.assertRaises(P.FixtureRefusal) as caught:
            P.load_packet(manifest, anchor, "rational_triangle")
        self.assertEqual(caught.exception.reason, P.FixtureReason.SCHEMA)

    def test_legacy_bytes_unchanged_and_only_geometry_compatibility_is_declared(self):
        before = {name: hashlib.sha256((LEGACY / name).read_bytes()).hexdigest()
                  for name in LEGACY_PACKET_SHA}
        self.assertEqual(before, LEGACY_PACKET_SHA)
        packet = self.packet("canonical_patch_8x4")
        self.assertEqual(packet.source["legacy_fields_read"], list(P.LEGACY_GEOMETRY_FIELDS))
        self.assertNotIn("E_f64", packet.source["legacy_fields_read"])
        after = {name: hashlib.sha256((LEGACY / name).read_bytes()).hexdigest()
                 for name in LEGACY_PACKET_SHA}
        self.assertEqual(after, before)

    def test_generate_and_verify_refuse_overwrite_and_cli_errors_are_nonzero(self):
        existing = self.root / "existing"
        existing.mkdir(exist_ok=True)
        marker = existing / "marker"; marker.write_text("unchanged", encoding="utf-8")
        with self.assertRaises(P.FixtureRefusal) as caught:
            P.generate(existing, LEGACY, LEGACY_MANIFEST_SHA)
        self.assertEqual(caught.exception.reason, P.FixtureReason.OUTPUT_EXISTS)
        self.assertEqual(marker.read_text(encoding="utf-8"), "unchanged")

        report = self.root / "report.json"
        with mock.patch("sys.stdout", io.StringIO()):
            self.assertEqual(P.main(["verify", "--manifest", str(self.manifest),
                                     "--manifest-sha256", self.manifest_sha,
                                     "--output", str(report)]), 0)
        first = report.read_bytes()
        with mock.patch("sys.stderr", io.StringIO()):
            self.assertNotEqual(P.main(["verify", "--manifest", str(self.manifest),
                                        "--manifest-sha256", self.manifest_sha,
                                        "--output", str(report)]), 0)
        self.assertEqual(report.read_bytes(), first)

        failed = self.root / "failed-generation"
        with self.assertRaises(P.FixtureRefusal):
            P.generate(failed, LEGACY, "0" * 64)
        self.assertFalse(failed.exists())

    def test_cli_process_returns_nonzero_for_bad_trust_anchor(self):
        output = self.root / "cli-bad.json"
        env = os.environ.copy(); env["PYTHONDONTWRITEBYTECODE"] = "1"
        completed = subprocess.run(
            [sys.executable, str(CANDIDATE), "verify", "--manifest", str(self.manifest),
             "--manifest-sha256", "0" * 64, "--output", str(output)],
            cwd=REPO, env=env, capture_output=True, text=True,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertFalse(output.exists())
        self.assertIn(P.FixtureReason.TRUST_ANCHOR, completed.stderr)


if __name__ == "__main__":
    unittest.main()

