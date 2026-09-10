import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("demo_evidence", ROOT / "demo_evidence.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        image = self.root / "frame.png"
        image.write_bytes(b"PNG fixture bytes")
        digest = hashlib.sha256(image.read_bytes()).hexdigest()
        status = {"accepted_state_id": 77, "render_state_id": 0,
                  "iteration": 12, "energy": 2.5, "centre": [0.0, 0.0, 0.1]}
        self.record = {
            "source": {"commit": "a" * 40, "executable_sha256": "b" * 64,
                       "shader_sha256": "c" * 64},
            "endpoint": "http://127.0.0.1:8103",
            "process": {"pid": 1234, "exe": "engine.exe"},
            "before": dict(status), "after": dict(status),
            "capture": {"path": str(image), "sha256": digest},
            "request": {"started_utc": "2026-09-10T12:00:00Z",
                        "finished_utc": "2026-09-10T12:00:01Z"},
        }

    def tearDown(self):
        self.tmp.cleanup()

    def test_complete_unchanged_snapshot_is_bounded_and_unbound(self):
        result = mod.validate_record(self.record, self.record["source"])
        self.assertEqual(result["verdict"], "consistent_snapshot")
        self.assertEqual(result["render_submission_identity"], "unbound")
        self.assertFalse(result["physics_certified"])

    def test_changed_accepted_state_is_reported(self):
        self.record["after"]["accepted_state_id"] = 78
        self.assertEqual(mod.validate_record(self.record)["verdict"], "changed_during_capture")

    def test_swapped_capture_bytes_fail_hash_binding(self):
        (self.root / "frame.png").write_bytes(b"swapped bytes")
        result = mod.validate_record(self.record)
        self.assertEqual(result["verdict"], "insufficient_evidence")
        self.assertIn("capture_hash_mismatch", result["reasons"])

    def test_missing_or_nonfinite_status_fails(self):
        self.record["before"].pop("accepted_state_id")
        self.record["after"]["energy"] = float("nan")
        result = mod.validate_record(self.record)
        self.assertEqual(result["verdict"], "insufficient_evidence")
        self.assertIn("before_accepted_state_id_missing", result["reasons"])
        self.assertIn("after_energy_invalid", result["reasons"])

    def test_source_mismatch_fails(self):
        expected = dict(self.record["source"])
        expected["commit"] = "d" * 40
        result = mod.validate_record(self.record, expected)
        self.assertEqual(result["verdict"], "insufficient_evidence")
        self.assertIn("source_mismatch_commit", result["reasons"])

    def test_writer_refuses_overwrite(self):
        out = self.root / "result.json"
        mod.write_result({"verdict": "consistent_snapshot"}, out)
        with self.assertRaises(FileExistsError):
            mod.write_result({"verdict": "changed_during_capture"}, out)

    def test_required_status_shape_rejects_partial_status(self):
        self.record["before"] = {"accepted_state_id": 1}
        self.assertEqual(mod.validate_record(self.record)["verdict"], "insufficient_evidence")

    def test_status_numeric_strings_none_and_bool_are_rejected(self):
        self.record["before"]["energy"] = "nan"
        self.record["after"]["centre"] = [0, None, 0]
        self.record["before"]["accepted_state_id"] = True
        self.assertEqual(mod.validate_record(self.record)["verdict"], "insufficient_evidence")

    def test_ids_and_pid_must_be_positive_uint64_integers(self):
        self.record["before"]["accepted_state_id"] = -7
        self.record["process"]["pid"] = True
        self.assertEqual(mod.validate_record(self.record)["verdict"], "insufficient_evidence")

    def test_source_and_capture_hashes_require_exact_hex_lengths(self):
        self.record["source"]["commit"] = "x"
        self.record["capture"]["sha256"] = "short"
        self.assertEqual(mod.validate_record(self.record)["verdict"], "insufficient_evidence")


if __name__ == "__main__":
    unittest.main()
