"""Synthetic packaging/unit tests only; never evidence of live geometry or grasp."""
import ast
from copy import deepcopy
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import replay as r


def fixture_rows(n=2):
    stage1 = {"postures": {}}
    stage2 = {"postures": {}}
    for posture in r.POSTURES:
        a, b = [], []
        for i in range(n):
            pad_class = "PAD_ABSORBED" if i == 0 else "PAD_CONTACT"
            pad_u = 0.0 if i == 0 else 0.001
            a.append({"theta_index": i, "mirror": i % 2,
                      "o": [0.0, 0.0, 0.0], "u": [0.0, 0.0, 1.0],
                      "s_star": 0.01, "pad_body": "distal_thumb",
                      "pad_class": pad_class, "pad_u": pad_u,
                      "bodies": [["distph3", "TOUCHING", 0.0, None]],
                      "anchor_envelope": {"cls": "GENUINE_PENETRATION", "d": None,
                                          "depth": 0.02, "flag": True}})
            b.append({"theta_index": i, "mirror": i % 2, "pad_body": "distal_thumb",
                      "pad_class": pad_class, "pad_u": pad_u, "cls": "CAP_SATISFIED"})
        stage1["postures"][posture] = {"survivors": a}
        stage2["postures"][posture] = {"capacity_rows": b}
    return stage1, stage2


def raw_class(cls, depth=None, margin=None):
    return {"class": cls, "d": margin, "depth": depth,
            "level1": {"flag": cls != "CLEAR"}}


def fixture_unit(row):
    manifest = r.inputs()
    records = {name: raw_class("CLEAR") for name in manifest["body_census"]}
    records["distph3"] = raw_class("TOUCHING", margin=0.0)
    records["distal_thumb"] = raw_class("GENUINE_PENETRATION", depth=0.003)
    records["macaque_hand_anchor"] = raw_class("GENUINE_PENETRATION", depth=0.02)
    # Test the inherited predicate itself, imported byte-unmodified, on fixtures.
    sys.path.insert(0, str(r.ROOT / r.INHERITED))
    gs = importlib.import_module("grasp_screen")
    frames = {name: {"position_m": [0.0, 0.0, 0.0],
                     "rotation": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
                     "represented_mesh_sha256": "0" * 64,
                     "is_envelope": name == "macaque_hand_anchor", "vertex_count": 3, "triangle_count": 1}
              for name in manifest["body_census"]}
    return r.unit_payload(row, records, r.declared_postures()[row["key"][0]], manifest, frames,
                          gs.classify_placement_bones)


class ReplayTests(unittest.TestCase):
    def setUp(self):
        self.a, self.b = fixture_rows()
        self.expected = {p: 2 for p in r.POSTURES}
        self.rows = r.join_rows(self.a, self.b, self.expected)
        self.manifest = r.inputs()
        self.seal_patch = patch.object(r, "current_seal_sha256", return_value="d" * 64)
        self.seal_patch.start()
        self.addCleanup(self.seal_patch.stop)

    def test_atomic_write_retries_transient_windows_sharing_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "progress.json"
            real_replace = os.replace
            with patch.object(r.os, "replace", side_effect=[PermissionError("synthetic sharing"), None]) as replace:
                r.atomic_json(p, {"complete": False})
                self.assertEqual(replace.call_count, 2)
                self.assertTrue(p.with_name("progress.json.tmp").exists())
            real_replace(p.with_name("progress.json.tmp"), p)
            self.assertEqual(r.read_json(p), {"complete": False})

    def test_atomic_write_permanent_failure_not_swallowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "progress.json"
            with patch.object(r.os, "replace", side_effect=PermissionError("permanent")), \
                 patch.object(r.time, "monotonic", side_effect=[0.0, 2.0]):
                with self.assertRaisesRegex(PermissionError, "permanent"):
                    r.atomic_json(p, {"complete": False})
                self.assertTrue(p.with_name("progress.json.tmp").exists())
                self.assertFalse(p.exists())

    def test_canonical_order_independent_of_source_order(self):
        for posture in r.POSTURES:
            self.a["postures"][posture]["survivors"].reverse()
            self.b["postures"][posture]["capacity_rows"].reverse()
        self.assertEqual(r.canonical(self.rows), r.canonical(r.join_rows(self.a, self.b, self.expected)))

    def test_duplicate_missing_and_extra_keys_refused(self):
        for kind in ("duplicate", "missing", "foreign"):
            with self.subTest(kind=kind):
                b = deepcopy(self.b)
                rows = b["postures"][r.POSTURES[0]]["capacity_rows"]
                if kind == "duplicate":
                    rows[1] = deepcopy(rows[0])
                elif kind == "missing":
                    rows.pop()
                else:
                    rows[1]["theta_index"] = 719
                with self.assertRaises(r.Refused):
                    r.join_rows(self.a, b, self.expected)

    def test_joined_pad_metadata_drift_refused(self):
        for field, value in (("pad_body", "distph3"), ("pad_class", "PAD_CONTACT"), ("pad_u", 0.5)):
            b = deepcopy(self.b)
            b["postures"][r.POSTURES[0]]["capacity_rows"][0][field] = value
            with self.assertRaisesRegex(r.Refused, "joined_metadata_drift"):
                r.join_rows(self.a, b, self.expected)

    def test_unsafe_keys_nonfinite_and_shapes_refused(self):
        for field, value in (("theta_index", True), ("theta_index", -1), ("mirror", 2),
                             ("o", [0.0]), ("u", [0.0, float("inf"), 1.0]), ("s_star", None)):
            a = deepcopy(self.a)
            a["postures"][r.POSTURES[0]]["survivors"][0][field] = value
            with self.assertRaises(r.Refused):
                r.join_rows(a, self.b, self.expected)

    def test_json_duplicate_and_nonfinite_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "bad.json"
            for data in ('{"a":1,"a":2}', '{"a":NaN}', '{"a":Infinity}'):
                p.write_text(data)
                with self.assertRaises(r.Refused):
                    r.read_json(p)

    def test_all_20_bodies_pad_and_anchor_present_without_masking(self):
        unit = fixture_unit(self.rows[0])
        self.assertEqual(len(unit["body_records"]), 20)
        self.assertIn("S2_REJECT_DEEP:distal_thumb", unit["bone_diagnostic"]["reasons"])
        self.assertIn("S1_REJECT_NONCONTACT_PENETRATE:macaque_hand_anchor",
                      unit["anchor_inclusive_diagnostic"]["reasons"])
        self.assertFalse(unit["physical_grasp_qualified"])
        self.assertEqual(unit["source_stage1"]["pad_class"], "PAD_ABSORBED")
        self.assertEqual(unit["body_records"][0]["body"], sorted(self.manifest["body_census"])[0])

    def test_contact_depth_boundary_preserved(self):
        pi_c = self.manifest["constants"]["PI_C"]
        for depth, expected in ((pi_c, []), (pi_c + 1e-12, ["S2_REJECT_DEEP:distal_thumb"])):
            self.assertEqual(r.rejection_reasons({"distal_thumb": raw_class("GENUINE_PENETRATION", depth)},
                                                 pi_c), expected)

    def test_noncontact_touch_and_contact_clear_refuse(self):
        records = {"distph3": raw_class("CLEAR"), "firstmc": raw_class("TOUCHING")}
        self.assertEqual(r.rejection_reasons(records, 1e-3),
                         ["S2_REJECT_NO_CONTACT:distph3", "S1_REJECT_NONCONTACT_TOUCH:firstmc"])

    def test_unknown_raw_class_refused(self):
        with self.assertRaisesRegex(r.Refused, "unknown_collision_class"):
            r.rejection_reasons({"firstmc": raw_class("UNRESOLVED_GEOMETRY")}, 1e-3)

    def test_canonical_combination_reversed_and_partitioned(self):
        units = [fixture_unit(row) for row in self.rows]
        first = r.combine_units(units, self.rows, self.manifest)
        reversed_result = r.combine_units(list(reversed(units)), self.rows, self.manifest)
        partitioned = r.combine_units(units[::2] + units[1::2], self.rows, self.manifest)
        self.assertEqual(r.canonical(first), r.canonical(reversed_result))
        self.assertEqual(r.canonical(first), r.canonical(partitioned))
        self.assertEqual(first["body_record_count"], 80)
        self.assertEqual(first["anchor_inclusive_rejected"], 4)

    def test_partial_and_duplicate_combination_refused(self):
        units = [fixture_unit(row) for row in self.rows]
        with self.assertRaisesRegex(r.Refused, "partial_result_not_full_replay"):
            r.combine_units(units[:-1], self.rows, self.manifest)
        with self.assertRaisesRegex(r.Refused, "duplicate_unit_key"):
            r.combine_units(units + units[:1], self.rows, self.manifest)

    def test_missing_pad_or_anchor_records_refuse(self):
        for body in ("distal_thumb", "macaque_hand_anchor"):
            unit = fixture_unit(self.rows[0])
            unit["body_records"] = [x for x in unit["body_records"] if x["body"] != body]
            with self.assertRaisesRegex(r.Refused, "unit_body_census_mismatch"):
                r.validate_unit(unit, self.rows[0], self.manifest)

    def test_source_identity_and_foreign_prereg_refuse(self):
        for kind in ("pose", "prereg", "source"):
            unit = fixture_unit(self.rows[0])
            if kind == "pose":
                unit["pose_sha256"] = "0" * 64
            elif kind == "prereg":
                unit["preregistration_sha256"] = "0" * 64
            else:
                unit["source_stage1"] = deepcopy(unit["source_stage1"])
                unit["source_stage1"]["o"][0] = 0.123
            with self.assertRaises(r.Refused):
                r.validate_unit(unit, self.rows[0], self.manifest)

    def test_diagnostic_tamper_and_promotion_refuse(self):
        for kind in ("verdict", "reasons", "promotion", "drift"):
            unit = fixture_unit(self.rows[0])
            if kind == "verdict":
                unit["bone_diagnostic"]["verdict"] = "SURVIVOR"
            elif kind == "reasons":
                unit["bone_diagnostic"]["reasons"] = []
            elif kind == "promotion":
                unit["physical_grasp_qualified"] = True
            else:
                unit["inherited_record_drifts"] = [{"wrong": True}]
            with self.assertRaises(r.Refused):
                r.validate_unit(unit, self.rows[0], self.manifest)

    def test_inherited_float_and_anchor_flags_compared_exactly(self):
        unit = fixture_unit(self.rows[0])
        records = {x["body"]: x["collision"] for x in unit["body_records"]}
        self.assertEqual(r.record_identity_drift(self.rows[0]["stage1"], records, "macaque_hand_anchor"), [])
        records["distph3"]["d"] = 1e-20
        records["macaque_hand_anchor"]["level1"]["flag"] = False
        self.assertEqual(len(r.record_identity_drift(self.rows[0]["stage1"], records, "macaque_hand_anchor")), 2)

    def test_no_release_refuses_before_geometry_import(self):
        args = type("Args", (), {"op": "control", "release": None})()
        with tempfile.TemporaryDirectory() as tmp, patch.object(r, "import_physics") as physics:
            with self.assertRaisesRegex(r.Refused, "published_prereg_and_lt_release_required"):
                r.execute(args, Path(tmp))
            physics.assert_not_called()

    def fixture_release(self):
        return {"schema": "chimera.exact_pose_replay.release.v1", **r.identities(),
                "authority": "Lieutenant", "authority_reference": "SYNTHETIC_TEST_ONLY",
                "source_input_commit": self.manifest["input_commit"],
                "published_prereg_commit": "a" * 40, "sealed_base_commit": "b" * 40,
                "operations": ["control", "compare-control", "replay", "combine"],
                "anchor_policy": "DIAGNOSTIC_ONLY_NO_SOLID_ANATOMY_RULING",
                "owner": "Buffy-Freebuff-20261004", "ownership_rechecked": True,
                "release_id": "SYNTHETIC-RELEASE", "observed_utc": "SYNTHETIC-TIME",
                "sealed_manifest_sha256": "d" * 64,
                "resource_profile_sha256": r.sha(Path(
                    "E:/PythonChimera/tools/monkey_campaign/runner_profile.json").read_bytes()),
                "unit_timeout_seconds": 600,
                "geometry_scope": "EXACT_STORED_STAGE1_POSES_NO_PLACEMENT_SOLVE",
                "independent_approval_claimed": False}

    def test_release_checks_pin_base_hash_and_operation(self):
        good = self.fixture_release()
        for field, value in (("schema", "wrong"), ("task", "foreign"), ("preregistration_sha256", "0" * 64),
                             ("authority", "Buffy"), ("authority_reference", ""),
                             ("published_prereg_commit", "pending"), ("source_input_commit", "c" * 40),
                             ("operations", []), ("sealed_base_commit", "c" * 40),
                             ("anchor_policy", "SOLID_ANATOMY"), ("owner", ""),
                             ("ownership_rechecked", False), ("sealed_manifest_sha256", "e" * 64),
                             ("implementation_sha256", "e" * 64), ("resource_profile_sha256", "e" * 64),
                             ("unit_timeout_seconds", 900), ("geometry_scope", "R2"),
                             ("independent_approval_claimed", True)):
            release = deepcopy(good)
            release[field] = value
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "fixture.json"
                r.atomic_json(path, release)
                with self.assertRaises(r.Refused):
                    r.release_gate(path, "control", self.manifest, runner_base="b" * 40,
                                   git_reader=lambda *a: (r.HERE / "PREREGISTRATION.md").read_bytes())

    def test_release_rejects_published_bytes_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fixture.json"
            r.atomic_json(path, self.fixture_release())
            with self.assertRaisesRegex(r.Refused, "published_prereg_bytes_drift"):
                r.release_gate(path, "control", self.manifest, runner_base="b" * 40,
                               git_reader=lambda *a: b"not the prereg")

    def test_release_rejects_seal_before_new_prereg_pin(self):
        release = self.fixture_release()
        release["sealed_base_commit"] = self.manifest["input_commit"]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fixture.json"
            r.atomic_json(path, release)
            with self.assertRaisesRegex(r.Refused, "new_prereg_pin_not_in_sealed_base"):
                r.release_gate(path, "control", self.manifest, runner_base=self.manifest["input_commit"],
                               git_reader=lambda *a: b"")

    def test_scaling_requires_actual_serial_gate(self):
        with self.assertRaisesRegex(r.Refused, "serial_control_gate_required_before_scaling"):
            r.check_control_gate(None, self.rows, self.manifest)

    def test_local_pin_drift_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "code.py"
            p.write_bytes(b"changed")
            manifest = {"schema": "chimera.exact_pose_replay.inputs.v1",
                        "local_files": {"code.py": r.sha(b"original")}}
            with self.assertRaisesRegex(r.Refused, "input_pin_drift"):
                r.check_files(manifest, root=Path(tmp), external=False)

    def test_retained_failed_or_tampered_control_refuses(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / ("f" * 32)
            root.mkdir()
            with patch.object(r, "RUNNER_RESULTS", root.parent):
                r.atomic_json(root / "receipt.json", {"job": root.name, "state": "FAILED", "cleanup_verified": True})
                with self.assertRaisesRegex(r.Refused, "control_runner_not_completed"):
                    r.retained_run(root)
                r.atomic_json(root / "receipt.json", {"job": root.name, "state": "PASSED", "cleanup_verified": True,
                    "artifacts": {"outputs/replay/control.json": r.sha(b"original")}})
                r.atomic_json(root / "artifacts/outputs/replay/control.json", {"tampered": True})
                with self.assertRaisesRegex(r.Refused, "control_runner_artifact_drift"):
                    r.retained_run(root)

    def test_noncanonical_results_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(r.Refused, "noncanonical_runner_result_refused"):
                r.retained_receipt(tmp)

    def synthetic_control_runs(self, root):
        rows = r.control_rows(self.rows)
        result = r.combine_units([fixture_unit(row) for row in rows], rows, self.manifest)
        paths = []
        for job, route in (("a" * 32, "serial"), ("b" * 32, "units_reversed")):
            path = root / job
            payload = {"schema": "chimera.exact_pose_replay.control.v1", "route": route,
                       "geometry_executed": True, "run_base_commit": "c" * 40, "result": result}
            output = path / "artifacts/outputs/replay/control.json"
            r.atomic_json(output, payload)
            r.atomic_json(path / "receipt.json", {"job": job, "state": "PASSED",
                "cleanup_verified": True, "base": "c" * 40, "sealed_manifest_sha256": "d" * 64,
                "command": ["C:/Python314/python.exe", "-B", r.REL + "/replay.py", "control",
                            "--route", route, "--release", "SYNTHETIC_RELEASE"],
                "artifacts": {"outputs/replay/control.json": r.sha(output.read_bytes())}})
            paths.append(path)
        return paths

    def test_control_gate_fixture_parity_and_negative_cases(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch.object(r, "RUNNER_RESULTS", root):
                serial, units = self.synthetic_control_runs(root)
                gate = r.control_gate(serial, units, self.rows, self.manifest)
                self.assertEqual(gate["state"], "PASSED")
                self.assertFalse(gate["independent_approval"])
                self.assertEqual(gate["control_pose_count"], 2)
                for field, value, reason in (("route", "serial", "control_routes_not_distinct"),
                                           ("geometry_executed", False, "fixture_not_control_runtime_evidence"),
                                           ("run_base_commit", "e" * 40, "control_declared_base_mismatch")):
                    path = units / "artifacts/outputs/replay/control.json"
                    original = r.read_json(path)
                    altered = deepcopy(original)
                    altered[field] = value
                    r.atomic_json(path, altered)
                    receipt = r.read_json(units / "receipt.json")
                    receipt["artifacts"]["outputs/replay/control.json"] = r.sha(path.read_bytes())
                    r.atomic_json(units / "receipt.json", receipt)
                    with self.assertRaisesRegex(r.Refused, reason):
                        r.control_gate(serial, units, self.rows, self.manifest)
                    r.atomic_json(path, original)
                    receipt["artifacts"]["outputs/replay/control.json"] = r.sha(path.read_bytes())
                    r.atomic_json(units / "receipt.json", receipt)

    def test_control_gate_fixture_raw_byte_mismatch_refuses(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch.object(r, "RUNNER_RESULTS", root):
                serial, units = self.synthetic_control_runs(root)
                path = units / "artifacts/outputs/replay/control.json"
                value = r.read_json(path)
                changed = deepcopy(value["result"]["units"])
                for unit in changed:
                    unit["body_frames"]["distph3"]["position_m"][0] = 0.001
                value["result"] = r.combine_units(changed, r.control_rows(self.rows), self.manifest)
                r.atomic_json(path, value)
                receipt = r.read_json(units / "receipt.json")
                receipt["artifacts"]["outputs/replay/control.json"] = r.sha(path.read_bytes())
                r.atomic_json(units / "receipt.json", receipt)
                with self.assertRaisesRegex(r.Refused, "serial_control_payload_not_byte_identical"):
                    r.control_gate(serial, units, self.rows, self.manifest)

    def test_pose_posture_and_mesh_markers_bound_in_units(self):
        for field in ("cylinder", "posture", "mesh", "marker", "shape"):
            unit = fixture_unit(self.rows[0])
            if field == "cylinder":
                unit["cylinder"]["o"][0] = 0.05
            elif field == "posture":
                unit["posture_q"]["cmc_flexion"] = 0.05
            elif field == "mesh":
                unit["body_frames"]["distph3"]["represented_mesh_sha256"] = "short"
            elif field == "marker":
                unit["body_records"][0]["pad_substituted_in_stage1"] = False
            else:
                unit["body_frames"]["distph3"]["rotation"] = [[1.0]]
            with self.assertRaises(r.Refused):
                r.validate_unit(unit, self.rows[0], self.manifest, posture_values=r.declared_postures())

    def test_same_posture_frames_cannot_drift_between_units(self):
        units = [fixture_unit(row) for row in self.rows]
        units[0]["body_frames"]["distph3"]["position_m"][0] = 0.01
        with self.assertRaisesRegex(r.Refused, "same_posture_frame_identity_drift"):
            r.combine_units(units, self.rows, self.manifest)

    def test_retained_unit_hash_candidate_and_failure_gates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run = root / ("a" * 32)
            units = run / "artifacts/outputs/replay/units"
            path = units / "fixture.json"
            r.atomic_json(path, fixture_unit(self.rows[0]))
            receipt = {"job": run.name, "state": "PASSED", "cleanup_verified": True,
                       "base": "b" * 40, "sealed_manifest_sha256": "c" * 64,
                       "artifacts": {"outputs/replay/units/fixture.json": r.sha(path.read_bytes())}}
            r.atomic_json(run / "receipt.json", receipt)
            with patch.object(r, "RUNNER_RESULTS", root):
                self.assertEqual(len(r.retained_units([units], "c" * 64, "b" * 40)), 1)
                with self.assertRaisesRegex(r.Refused, "unit_runner_wrong_candidate"):
                    r.retained_units([units], "e" * 64, "b" * 40)
                with self.assertRaisesRegex(r.Refused, "duplicate_unit_input_path"):
                    r.retained_units([units, units], "c" * 64, "b" * 40)
                path.write_bytes(b"tampered")
                with self.assertRaisesRegex(r.Refused, "unit_runner_artifact_drift"):
                    r.retained_units([units], "c" * 64, "b" * 40)
                receipt["state"] = "FAILED"
                r.atomic_json(run / "receipt.json", receipt)
                with self.assertRaisesRegex(r.Refused, "unit_runner_not_completed"):
                    r.retained_units([units], "c" * 64, "b" * 40)

    def test_work_unit_preserves_each_body_on_injected_failure(self):
        from types import SimpleNamespace
        frames = {n: SimpleNamespace(name=n) for n in self.manifest["body_census"]}
        seen = []
        def synthetic_primitive(frame, o, u, tau):
            if len(seen) == 5:
                raise RuntimeError("SYNTHETIC_FAILURE_AFTER_5_BODIES")
            seen.append(frame.name)
            return raw_class("CLEAR")
        iv = SimpleNamespace(TAU=1e-4, adjudicate_body_vs_cylinder=synthetic_primitive)
        checkpoints = []
        with self.assertRaisesRegex(RuntimeError, "SYNTHETIC_FAILURE_AFTER_5_BODIES"):
            r.evaluate_unit(self.rows[0], frames, {}, self.manifest, iv, None,
                            frame_table={}, checkpoint=lambda records: checkpoints.append(deepcopy(records)))
        self.assertEqual([len(x) for x in checkpoints], [1, 2, 3, 4, 5])
        self.assertEqual(list(checkpoints[-1]), sorted(frames)[:5])

    def test_current_runner_lease_hash_read_only(self):
        self.seal_patch.stop()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "slot-2/scratch"
            root.mkdir(parents=True)
            job = "a" * 32
            (root / ".chimera-runner-id").write_text(job)
            r.atomic_json(root.parent / "lease.json", {"schema": "chimera.runner_lease.v1",
                                                      "job": job, "sealed_manifest_sha256": "b" * 64})
            with patch.object(r, "ROOT", root):
                self.assertEqual(r.current_seal_sha256(), "b" * 64)
                r.atomic_json(root.parent / "lease.json", {"schema": "chimera.runner_lease.v1", "job": "c" * 32})
                with self.assertRaisesRegex(r.Refused, "runner_lease_identity_mismatch"):
                    r.current_seal_sha256()
        self.seal_patch.start()

    def test_cli_scientific_refusal_nonzero_and_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = subprocess.run([sys.executable, "-B", str(r.HERE / "replay.py"), "control", "--route", "serial"],
                               env={**os.environ, "CHIMERA_OUTPUT_DIR": tmp}, capture_output=True, timeout=30)
            self.assertNotEqual(p.returncode, 0)
            error = r.read_json(Path(tmp) / "replay/error.json")
            self.assertEqual(error["reason"], "published_prereg_and_lt_release_required")
            self.assertFalse(r.read_json(Path(tmp) / "replay/progress.json")["geometry_executed"])

    def test_inherited_systemexit_refusal_preserved_and_reraised(self):
        sys.path.insert(0, str(r.ROOT / r.INHERITED))
        iv = importlib.import_module("instrument_v2")
        with tempfile.TemporaryDirectory() as tmp, patch.object(r, "output_dir", return_value=Path(tmp)), \
             patch.object(sys, "argv", ["replay.py", "preflight"]), \
             patch.object(r, "execute", side_effect=iv.GateRefusal("SYNTHETIC_GATE", "synthetic detail")):
            with self.assertRaises(iv.GateRefusal):
                r.main()
            error = r.read_json(Path(tmp) / "error.json")
            self.assertEqual(error["instrument_code"], "SYNTHETIC_GATE")
            self.assertEqual(error["instrument_detail"], "synthetic detail")
            self.assertFalse(error["full_result"])

    def test_source_parses_and_has_no_placement_solve_calls(self):
        for path in (r.HERE / "replay.py", Path(__file__)):
            ast.parse(path.read_text(), filename=str(path))
        tree = ast.parse((r.HERE / "replay.py").read_text())
        forbidden = {"solve_s_star", "placement_family", "axis_basis"}
        calls = [n.func.attr for n in ast.walk(tree) if isinstance(n, ast.Call)
                 and isinstance(n.func, ast.Attribute)]
        self.assertFalse(forbidden.intersection(calls))

    def test_fixture_release_success_is_not_authority_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fixture.json"
            r.atomic_json(path, self.fixture_release())
            def fixture_git(*args):
                return (r.HERE / "PREREGISTRATION.md").read_bytes() if args[0] == "show" else b""
            got = r.release_gate(path, "control", self.manifest, runner_base="b" * 40, git_reader=fixture_git)
            self.assertEqual(got["authority_reference"], "SYNTHETIC_TEST_ONLY")


def main():
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ReplayTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    # Syntax compilation is this stdlib-only task's type/syntax check; no
    # typechecker is configured for this contribution. Never create .pyc files.
    out = Path(os.environ["CHIMERA_OUTPUT_DIR"]) / "replay"
    r.atomic_json(out / "tests.json", {"schema": "chimera.exact_pose_replay.tests.v1",
        **r.identities(), "execution_class": "SYNTHETIC_PACKAGING_TESTS_NOT_GEOMETRY",
        "tests_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
        "skipped": len(result.skipped), "passed": result.wasSuccessful(),
        "geometry_executed": False, "independent_approval": False})
    raise SystemExit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    main()
