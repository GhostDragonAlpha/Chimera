"""test_implementation.py -- ONT-F01 targeted qualification tests.

Wraps the implementation's reconcile/predict/bite machinery as unittest.
ORDER-INDEPENDENT: every test class materializes what it needs (pins are
re-materialized from git objects; evidence is rebuilt only when missing).

The suite asserts the frozen PREREGISTRATION (with disclosed amendments
A1-A6): falsifier bites B1-B4 bite, predictions P1-P8 hold on the pinned
bytes, the C01 frame chain checks close, and the honest boundary is declared.
Nothing here claims engine integration, runtime acceptance or training.

Run:  python -B -m unittest test_implementation -v   (from this directory)
"""
import json
import math
import pathlib
import subprocess
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import implementation as impl  # noqa: E402

REQUIRED_CAMERA_FIELDS = [
    "frame_id", "coordinate_unit", "position",
    "orientation_convention_and_values", "target", "distance_to_target",
    "projection", "vertical_fov_or_orthographic_span", "near_far_planes",
    "aspect_ratio", "viewport_resolution",
    "camera_motion_or_bookmark_sequence", "visibility_layers", "label_ids",
    "occlusion_or_xray_mode", "state_or_tick_interval"]


def ensure_evidence() -> None:
    """Order independence: rebuild evidence only when checks.json is missing."""
    if not (HERE / "evidence" / "checks.json").is_file():
        proc = subprocess.run(
            [sys.executable, "-B", str(HERE / "implementation.py"), "build"],
            capture_output=True, timeout=900)
        if proc.returncode != 0:
            raise AssertionError("implementation.py build failed: %s"
                                 % proc.stderr.decode()[-2000:])


def load_checks() -> dict:
    ensure_evidence()
    return json.loads((HERE / "evidence" / "checks.json").read_text(
        encoding="utf-8"))


class PinTests(unittest.TestCase):
    """Every pinned source materializes from git objects with raw equality."""

    @classmethod
    def setUpClass(cls):
        cls.pins = impl.materialize_pins()

    def test_all_eleven_pins_present(self):
        self.assertEqual(len(self.pins), 11)
        self.assertEqual(set(self.pins), set(impl.PINS))

    def test_raw_sha256_exact(self):
        for key, pin in self.pins.items():
            self.assertEqual(pin["sha256"], impl.PINS[key]["sha256"], key)
            self.assertTrue(pin["raw_match"], key)

    def test_via_repo_recorded(self):
        for key, pin in self.pins.items():
            self.assertTrue(pin["via_repo"], key)

    def test_materialized_files_round_trip(self):
        for key, pin in self.pins.items():
            again = pathlib.Path(pin["file"]).read_bytes()
            self.assertEqual(impl.sha_bytes(again), pin["sha256"], key)

    def test_three_convention_hashes_recorded(self):
        checks = load_checks()
        conv = checks["pins_hash_conventions"]
        self.assertEqual(set(conv), set(impl.PINS))
        for key, rec in conv.items():
            self.assertEqual(set(rec), {"raw", "lf_normalized",
                                        "crlf_normalized"}, key)


class BiteTests(unittest.TestCase):
    """The falsifier bites fail FIRST: each tampered world must be refused or
    visibly break the render/collision correspondence."""

    @classmethod
    def setUpClass(cls):
        pins = impl.materialize_pins()
        recipe, declaration, surface, trunk, tb = impl.load_sources(pins)
        cls.bites = impl.run_bites(pins, recipe, declaration, surface,
                                   trunk, tb)
        cls.by_name = {b["bite"]: b for b in cls.bites}

    def test_all_four_bites_bite(self):
        self.assertEqual(len(self.bites), 4)
        for b in self.bites:
            self.assertTrue(b.get("bites"), b)

    def test_b1_ghost_support_mismatches(self):
        b = self.by_name["B1_ghost_support"]
        self.assertTrue(b["loads_clean"])
        self.assertIn(b["outcome"],
                      ("VISIBLE_BUT_MISMATCH", "OCCLUDED", "UNRENDERED"))

    def test_b2_missing_boundary_refused(self):
        b = self.by_name["B2_missing_boundary"]
        self.assertTrue(b["refused"])
        self.assertTrue(str(b["code"]).startswith("f01_"), b["code"])

    def test_b3_unsafe_spawn_refused(self):
        b = self.by_name["B3_unsafe_spawn"]
        self.assertTrue(b["refused"])
        self.assertEqual(b["code"], "f01_mound_spawn_exclusion")

    def test_b4_off_frame_classifier(self):
        b = self.by_name["B4_off_frame"]
        self.assertEqual(b["outcome"], "OFF_FRAME")
        self.assertEqual(b["view"], "V2_seam_closeup")


class PredictionTests(unittest.TestCase):
    """P1-P8 hold on the pinned bytes (never re-derived)."""

    @classmethod
    def setUpClass(cls):
        cls.checks = load_checks()

    def test_all_ok(self):
        self.assertTrue(self.checks["all_ok"])
        self.assertTrue(self.checks["all_bites_bite"])

    def test_p1_determinism_four_runs(self):
        p1 = self.checks["P1_determinism"]
        self.assertEqual(len(p1["runs"]), 4)
        self.assertTrue(all(r["identical"] for r in p1["runs"]))
        self.assertTrue(p1["ok"])

    def test_p2_safety_numbers_exact(self):
        p2 = self.checks["P2_numbers"]
        self.assertAlmostEqual(p2["spawn_clearance_m"],
                               11.729184690233646, places=12)
        self.assertGreaterEqual(p2["spawn_clearance_m"],
                                p2["required_clearance_m"])
        self.assertEqual(p2["required_clearance_m"], 1.5)
        self.assertAlmostEqual(p2["worst_grid_slope_m_per_m"], 0.034606,
                               places=9)
        self.assertLessEqual(p2["worst_triangle_slope_m_per_m"], 0.05)
        self.assertLessEqual(p2["continuous_slope_bound_m_per_m"],
                             0.0471 + 1e-12)
        self.assertEqual(p2["worst_grid_error_m"], 0.0)
        self.assertEqual(p2["grid_points"], 1681)
        self.assertEqual(p2["mounds"], 5)
        self.assertEqual(p2["posts"], 80)
        self.assertAlmostEqual(p2["worst_gap_to_post_m"], 1.0, places=9)
        self.assertEqual(p2["worst_on_edge_error_m"], 0.0)
        self.assertEqual(p2["trunk_site_m"], [11.976783, 0.0, 2.471766])
        self.assertTrue(p2["ok"])

    def test_p3_extent_strict_gt(self):
        p3 = self.checks["P3_extent"]
        self.assertEqual(p3["classify"]["just_outside_x"], "outside")
        self.assertEqual(p3["classify"]["just_outside_z"], "outside")
        self.assertEqual(p3["classify"]["corner_sw_inside"], "inside")
        self.assertEqual(p3["classify"]["corner_ne_inside"], "inside")
        self.assertTrue(all(r["refused"]
                            and r["code"] == "f02_outside_extent"
                            for r in p3["off_patch_refusals"]))
        self.assertEqual(len(p3["off_patch_refusals"]), 4)
        self.assertAlmostEqual(p3["ring_extent_m"], 20.0, places=6)
        self.assertTrue(p3["ok"])

    def test_c01_frame_chain(self):
        c01 = self.checks["C01_frames"]
        self.assertTrue(c01["all_ok"])
        self.assertEqual(c01["R_determinant_plus_one_right_handed"]["det"], 1.0)
        self.assertLessEqual(c01["trunk_mesh_roundtrip_worst_err_m"]["worst"],
                             1e-12)
        self.assertTrue(c01["trunk_site_matches_f01_declaration"]["ok"])
        self.assertLessEqual(
            c01["post_bases_on_collision_surface_worst_m"]["worst"], 1e-9)

    def test_p6_spawn_on_surface(self):
        p6 = self.checks["P6_spawn"]
        self.assertEqual(p6["first_hit_surface"], "monkey_clearing_ground")
        self.assertLessEqual(p6["err_m"], p6["bar"])
        self.assertTrue(p6["same_arrays_as_render"])

    def test_p7_all_80_posts_visible_in_overview(self):
        p7 = self.checks["P7_boundary"]
        self.assertEqual(p7["posts_recovered"], 80)
        self.assertEqual(p7["posts_in_mesh_section"], 4320)
        self.assertEqual(p7["visible_in_overview"], 80)
        self.assertEqual(p7["surface_id"], "monkey_clearing_boundary_posts")

    def test_p8_frames_and_manifest(self):
        p8 = self.checks["P8_frames"]
        self.assertEqual(len(p8["frames"]), 4)
        self.assertEqual(p8["camera_fields_order"], REQUIRED_CAMERA_FIELDS)
        manifest = json.loads((HERE / "evidence" / "camera_manifest.json")
                              .read_text(encoding="utf-8"))["views"]
        self.assertEqual(len(manifest), 8)
        for name, view in manifest.items():
            self.assertEqual(sorted(view.keys()), sorted(REQUIRED_CAMERA_FIELDS),
                             name)
            self.assertEqual(len(view), 16, name)
        for vname, rec in p8["frames"].items():
            for key in ("clean", "diagnostic", "depth"):
                path = HERE / "evidence" / rec[key]
                self.assertTrue(path.is_file(), path.name)
                self.assertGreater(path.stat().st_size, 2_000_000, path.name)


class CorrespondenceTests(unittest.TestCase):
    """P5: render/collision correspondence with frozen bars, no tag-checking."""

    @classmethod
    def setUpClass(cls):
        cls.p5 = load_checks()["P5_correspondence"]

    def test_no_mismatch_anywhere(self):
        self.assertEqual(self.p5["failures"], [])
        for vname, rows in self.p5["per_view"].items():
            for pid, rec in rows.items():
                self.assertNotEqual(rec["outcome"], "VISIBLE_BUT_MISMATCH",
                                    (vname, pid))

    def test_probe_count_frozen(self):
        self.assertEqual(self.p5["probe_count"], 44)

    def test_ground_and_spawn_visible_somewhere(self):
        rows_by_id = {}
        for vname, rows in self.p5["per_view"].items():
            for pid, rec in rows.items():
                rows_by_id.setdefault(pid, []).append(rec["outcome"])
        for pid, outs in rows_by_id.items():
            if pid.startswith(("ground_", "spawn")):
                self.assertIn("VISIBLE_EXACT", outs, pid)

    def test_trunk_probes_visible_in_seam_view(self):
        rows = self.p5["per_view"]["V2_seam_closeup"]
        trunk = {pid: rec for pid, rec in rows.items()
                 if pid.startswith("trunk_")}
        self.assertEqual(len(trunk), 6)
        for pid, rec in trunk.items():
            self.assertEqual(rec["outcome"], "VISIBLE_EXACT", pid)
            self.assertLessEqual(rec["radial_err_m"], impl.TRUNK_RADIAL_BAR_M)
            self.assertLessEqual(
                rec["normal_angle_rad"],
                math.pi / impl.TRUNK_RING_SEGMENTS
                + impl.TRUNK_NORMAL_ANGULAR_SLACK)

    def test_seam_partition_matches_silhouette_rule(self):
        pins = impl.materialize_pins()
        recipe, declaration, surface, trunk, tb = impl.load_sources(pins)
        mesh = impl.SceneMesh(surface, trunk)
        cam = impl.Camera(impl.VIEWS["V2_seam_closeup"])
        axis = mesh.trunk["site"]["base_centre_m"]
        radius = mesh.trunk["collision_representation"]["solid"]["radius_m"]
        rows = self.p5["per_view"]["V2_seam_closeup"]
        seams = {pid: rec for pid, rec in rows.items()
                 if pid.startswith("seam_")}
        self.assertEqual(len(seams), 8)
        for pid, rec in seams.items():
            k = int(pid.split("_")[1])
            a = k * math.pi / 4.0
            base = axis
            px = base[0] + 0.05 * math.cos(a)
            pz = base[2] + 0.05 * math.sin(a)
            d = [px - cam.position[0], pz - cam.position[2]]
            l2 = d[0] * d[0] + d[1] * d[1]
            t = max(0.0, min(1.0, ((axis[0] - cam.position[0]) * d[0]
                                   + (axis[2] - cam.position[2]) * d[1]) / l2))
            dist = math.hypot(cam.position[0] + t * d[0] - axis[0],
                              cam.position[2] + t * d[1] - axis[2])
            if dist < radius:
                self.assertEqual(rec["outcome"], "OCCLUDED", pid)
                self.assertEqual(rec.get("occluder"), "trunk_01", pid)
            else:
                self.assertEqual(rec["outcome"], "VISIBLE_EXACT", pid)


class HonestBoundaryTests(unittest.TestCase):
    """The evidence never claims integration, runtime or training."""

    def test_honest_boundary_declares_pending_gates(self):
        checks = load_checks()
        hb = checks["honest_boundary"]
        for gate in ("native collision query route (#120 S1-3)",
                     "engine-side render upload (#120 S1-4)",
                     "engine walk replay or playable-build acceptance",
                     "trunk contact subsystem (Stage 2)",
                     "training or runtime acceptance"):
            self.assertIn(gate, hb["not_claimed"])

    def test_bites_recorded_in_evidence(self):
        ensure_evidence()
        bites = json.loads((HERE / "evidence" / "bites.json").read_text(
            encoding="utf-8"))
        self.assertTrue(bites["all_bite"])
        self.assertEqual({b["bite"] for b in bites["bites"]},
                         {"B1_ghost_support", "B2_missing_boundary",
                          "B3_unsafe_spawn", "B4_off_frame"})

    def test_preregistration_frozen_before_implementation(self):
        prereg = (HERE / "PREREGISTRATION.md").read_text(encoding="utf-8")
        self.assertIn("PREDICTIONS", prereg)
        self.assertIn("FALSIFIER BITES", prereg)
        self.assertIn("AMENDMENT A6", prereg)
        self.assertIn("HONEST BOUNDARY", prereg)


if __name__ == "__main__":
    unittest.main(verbosity=2)
