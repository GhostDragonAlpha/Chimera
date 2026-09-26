"""test_motion_profile_probe.py -- ONT-X02 candidate suite (unittest).

Runs the frozen probe in-process and asserts every frozen check is green,
that the receipts are internally consistent (trace hash binding), and that
the camera manifest re-validates through the campaign's own gate against the
card's frozen profile. CPU-only, headless, deterministic.

    python -B -m unittest test_motion_profile_probe -v
"""
from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE / "evidence"
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE))

import motion_profile_probe as probe                    # noqa: E402


class MotionProfileQualification(unittest.TestCase):
    def test_01_pinned_sources_byte_exact(self):
        for rel, want in probe.PINNED_SHA.items():
            got = hashlib.sha256((probe.REFERENCE / rel).read_bytes()) \
                .hexdigest()
            self.assertEqual(got, want, rel)

    def test_02_probe_all_green(self):
        run = probe.run_probe()
        checks = probe.evaluate(run)
        failed = [c["name"] for c in checks if not c["ok"]]
        self.assertEqual(failed, [], "frozen checks failed")
        self.assertEqual(len(checks), 9)
        self.assertEqual(run["public_mutators"], ["key", "mouse", "tick"])
        self.assertEqual(run["boot_world"].calls, [("boot",)])
        self.assertEqual(run["teardown_world"].calls,
                         ["terminate", "wait", "kill"])

    def test_03_regenereated_trace_byte_identical(self):
        run = probe.run_probe()
        on_disk = (EVIDENCE / "trace.jsonl").read_bytes()
        self.assertEqual(hashlib.sha256(run["trace_bytes"]).hexdigest(),
                         hashlib.sha256(on_disk).hexdigest())

    def test_04_receipts_bind_the_trace(self):
        numerical = json.loads(
            (EVIDENCE / "numerical_receipt.json").read_text(encoding="utf-8"))
        runtime = json.loads(
            (EVIDENCE / "runtime_receipt.json").read_text(encoding="utf-8"))
        trace_sha = hashlib.sha256(
            (EVIDENCE / "trace.jsonl").read_bytes()).hexdigest()
        self.assertTrue(numerical["all_green"])
        self.assertTrue(runtime["all_green"])
        self.assertEqual(numerical["trace_raw_sha256"], trace_sha)
        self.assertEqual(runtime["artifacts"]["trace"]["raw_sha256"],
                         trace_sha)
        self.assertEqual(numerical["subject_sha256"], probe.SUBJECT_SHA256)
        self.assertEqual(len(numerical["prediction_deviations"]), 2)
        self.assertTrue(all(d["fired"] for d in
                            numerical["prediction_deviations"]))

    def test_05_capture_manifest_passes_campaign_gate(self):
        sys.path.insert(0, "E:/PythonChimera/tools/monkey_campaign")
        for stale in [k for k in sys.modules if k in ("visual_gate",
                                                      "visual_capture",
                                                      "integrity")]:
            del sys.modules[stale]
        import visual_gate                          # noqa: E402
        contract = json.loads(
            (HERE / "card_task.json").read_text(encoding="utf-8"))
        capture = json.loads(
            (EVIDENCE / "capture_receipt.json").read_text(encoding="utf-8"))
        receipt = {
            "evidence": {
                "camera": capture["manifest"],
                "visual": {"reference": capture["video"]["reference"],
                           "raw_sha256": capture["video"]["raw_sha256"]},
            },
            "capture_context": {
                "task_id": "X02",
                "subject_sha256": probe.SUBJECT_SHA256,
                "run_id": capture["run_id"],
                "capture_sha256": capture["video"]["raw_sha256"],
                "tick_interval": capture["state_binding"]["tick_interval"],
            },
        }
        result = visual_gate.verify(receipt, contract)
        self.assertTrue(result["structurally_valid"])
        self.assertEqual(result["profile_id"], "recovery")
        self.assertEqual(result["capture_kind"], "video")


if __name__ == "__main__":
    unittest.main(verbosity=2)
