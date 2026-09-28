"""test_ont_a05.py -- unittest suite for the ONT-A05 candidate.

Runs the pinned-source laws on reduced workloads (the FULL frozen
measurements live in a05_hand_structure_probe.py: all six checks over the
complete pinned lineage, and the gate-validated capture). CPU-only, headless.

    python -B -m unittest test_ont_a05 -v
"""
from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
CAMPAIGN_TOOLS = Path("E:/PythonChimera/tools/monkey_campaign")


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


probe = load("ont_a05_probe", HERE / "a05_hand_structure_probe.py")
capture = load("ont_a05_capture", HERE / "capture_build.py")

sys.path.insert(0, str(CAMPAIGN_TOOLS))
sys.dont_write_bytecode = True
import visual_capture                                        # noqa: E402


class PinnedLineage(unittest.TestCase):
    def test_pinned_hashes_hold(self):
        # re-verifies every extracted reference byte against EXTRACTION.json
        probe.assert_pins()

    def test_a04_winner_head_is_the_merged_winner(self):
        m = probe.EXTRACTION
        self.assertEqual(m["a04_winner_head"],
                         "020c0a5c216a4182d0bed9c4ade59cb0beb585ad")

    def test_extraction_manifest_covers_a04_and_vendor(self):
        keys = probe.EXTRACTION["files"]
        self.assertTrue(any("chimanoid.xml" in k for k in keys))
        self.assertTrue(any("identity_table.md" in k for k in keys))
        self.assertTrue(any("myohand_body.xml" in k for k in keys))
        self.assertTrue(any("LICENSE" in k for k in keys))


class SourceHand(unittest.TestCase):
    def test_source_hand_is_one_rigid_body_with_wrist(self):
        bodies, joints, meshes, sites = probe.source_hand_structure()
        self.assertEqual(bodies, ["hand_r"])
        self.assertEqual([j[0] for j in joints],
                         ["wrist_dev_r", "wrist_flex_r", "wrist_3_r"])
        self.assertEqual(len(meshes), 27)
        self.assertEqual(sorted(sites), sorted(probe.SITES))


class VendorIdentity(unittest.TestCase):
    def test_all_27_vendor_stls_match_a04_pins(self):
        pins = probe.identity_pins()
        for b in probe.BONES:
            p = probe.VENDOR_STL_DIR / (b + ".stl")
            self.assertTrue(p.exists(), b)
            self.assertTrue(probe.sha256_file(p).startswith(pins[b]), b)


class VendorDigitStructure(unittest.TestCase):
    def test_19_digit_bodies_and_20_digit_joints(self):
        _bodies, digit_bodies, digit_joints = probe.vendor_digit_structure()
        self.assertEqual(sorted(digit_bodies), probe.EXPECTED_DIGIT_BODIES)
        self.assertEqual(len(digit_bodies), 19)
        self.assertEqual(sorted(j["name"] for j in digit_joints),
                         probe.EXPECTED_DIGIT_JOINTS)
        self.assertEqual(len(digit_joints), 20)
        self.assertTrue(all(j["range"] for j in digit_joints))


class CorrespondenceAndDelta(unittest.TestCase):
    def test_correspondence_covers_all_14_phalanges(self):
        mapped = {v: k for k, v in probe.CORRESPONDENCE.items()}
        self.assertEqual(len(mapped), 19)
        covered = [b for b in probe.PHALANGES if b in mapped]
        self.assertEqual(len(covered), 14)

    def test_delta_excludes_scale_runtime_palm(self):
        checks, delta = probe.evaluate()
        self.assertEqual(delta["excluded"],
                         ["scale number", "target-runtime binding",
                          "origin promotion", "palm-sign claim"])
        self.assertEqual(delta["new_bodies"], 19)
        self.assertEqual(delta["new_joints"], 20)
        by_name = {c["name"]: c for c in checks}
        self.assertTrue(by_name["C6_approval_status_honest"]["ok"])
        self.assertFalse(
            by_name["C6_approval_status_honest"]["measured"]
            ["adaptation_approved"])


class FullChecks(unittest.TestCase):
    def test_all_six_checks_green(self):
        checks, _delta = probe.evaluate()
        self.assertEqual(len(checks), 6)
        self.assertTrue(all(c["ok"] for c in checks),
                      [c["name"] for c in checks if not c["ok"]])


class ManifestStructure(unittest.TestCase):
    def test_built_manifest_validates_against_card_profile(self):
        manifest = json.loads((HERE / "evidence" / "capture_manifest.json")
                              .read_text(encoding="utf-8"))
        context = {
            "task_id": manifest["task_id"],
            "run_id": manifest["run_id"],
            "subject_sha256": manifest["subject_sha256"],
            "capture_sha256": manifest["capture_sha256"],
            "tick_interval": manifest["tick_interval"],
        }
        card = json.loads((HERE / "card_task.json").read_text(
            encoding="utf-8"))
        result = visual_capture.validate_manifest(
            manifest, context, card["task"]["verification_profile"])
        self.assertTrue(result["structurally_valid"])
        self.assertEqual(result["profile_id"], "anatomy")
        # a clean row carrying diagnostics must be REFUSED
        broken = json.loads(json.dumps(manifest))
        broken["views"][1]["visibility"]["layers"] = list(
            card["task"]["verification_profile"]["diagnostic_layers"])
        with self.assertRaises(ValueError):
            visual_capture.validate_manifest(
                broken, context,
                card["task"]["verification_profile"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
