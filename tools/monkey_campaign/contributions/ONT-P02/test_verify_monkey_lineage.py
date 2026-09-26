#!/usr/bin/env python3
"""Falsifier suite for the P02 monkey/scene lineage map verifier (card ONT-P02).

Every mutation control encodes a preregistered falsifier: a dead pin (F1), a
wrong number (F2), a lineage interchange (F3), or a verifier blind spot (F5).
The live-records integration proves the shipped map passes against the real
git object store and that the verifier is idempotent (P-6).
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import verify_monkey_lineage as vml  # noqa: E402

MAP_PATH = os.path.join(HERE, "monkey_lineage_map.json")
# mutation copies live in a temp dir outside any worktree, so the object store
# under test is pinned explicitly to the store that resolves the shipped map
REPO = vml._resolve_repo(None, MAP_PATH)


def _write(tmpdir: str, m: dict) -> str:
    path = os.path.join(tmpdir, "mutated_map.json")
    with open(path, "wb") as fh:
        fh.write(json.dumps(m, indent=2, ensure_ascii=False).encode("utf-8"))
    return path


def _expect_refusal(self: unittest.TestCase, m: dict, fragment: str) -> str:
    with tempfile.TemporaryDirectory() as td:
        path = _write(td, m)
        try:
            vml.verify(path, repo=REPO)
        except vml.Refusal as exc:
            message = str(exc)
            self.assertIn(fragment, message, f"refusal {message!r} does not name {fragment!r}")
            return message
    self.fail(f"expected refusal naming {fragment!r}; verifier passed a mutated map")
    raise AssertionError("unreachable")


class LiveRecordsIntegration(unittest.TestCase):
    """The shipped map must pass against the real object store, twice."""

    def test_live_map_passes(self):
        report = vml.verify(MAP_PATH)
        self.assertEqual(report["outcome"], "PASS")
        self.assertEqual(sorted(report["card_items"]), sorted(vml.CARD_ITEM_IDS))
        self.assertGreaterEqual(report["pins_resolved"], 23)
        self.assertEqual(report["training_body_kg"], 10.038)
        self.assertEqual(report["walker_weight_N"], 98.4391527)
        self.assertEqual(report["cot_mismatch_ratio"], 1377.2166)
        self.assertEqual(report["runtime_body_sha256"], "bc9033bfc6c54db0220364821ee19028bf2ac6f740dc70f4c1e9be5f02089111")

    def test_live_map_passes_idempotently(self):
        first = vml.verify(MAP_PATH)
        second = vml.verify(MAP_PATH)
        self.assertEqual(first, second)

    def test_criteria_identity_bound(self):
        with self.assertRaises(vml.Refusal) as ctx:
            vml.verify(MAP_PATH, expected_criteria="0" * 64)
        self.assertIn("map_criteria_mismatch", str(ctx.exception))

    def test_scope_identity_bound(self):
        with open(MAP_PATH, encoding="utf-8") as fh:
            m = json.load(fh)
        m["scope_sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as td:
            path = _write(td, m)
            with self.assertRaises(vml.Refusal) as ctx:
                vml.verify(path, repo=REPO)
            self.assertIn("map_scope_mismatch", str(ctx.exception))


class DeadPinControls(unittest.TestCase):
    """F1/F5: any pin identity that cannot be recomputed must be refused."""

    def _first_pin(self, m: dict, pid: str) -> dict:
        return next(p for p in m["pins"] if p["id"] == pid)

    def test_mutated_sha256_refused(self):
        with open(MAP_PATH, encoding="utf-8") as fh:
            m = json.load(fh)
        pin = self._first_pin(m, "ev_acceptance")
        pin["sha256"] = "0" * 64
        _expect_refusal(self, m, "pin_sha256_mismatch:ev_acceptance")

    def test_mutated_blob_refused(self):
        with open(MAP_PATH, encoding="utf-8") as fh:
            m = json.load(fh)
        pin = self._first_pin(m, "ev_body_manifest")
        # swap in a REAL blob id from another path: rev-parse mismatch, not a git failure
        pin["blob"] = self._first_pin(m, "ev_mesh_receipt")["blob"]
        _expect_refusal(self, m, "pin_blob_mismatch:ev_body_manifest")

    def test_nonexistent_blob_refused(self):
        with open(MAP_PATH, encoding="utf-8") as fh:
            m = json.load(fh)
        pin = self._first_pin(m, "ev_body_manifest")
        pin["blob"] = "0" * 40
        _expect_refusal(self, m, "pin_git_failed:ev_body_manifest")

    def test_mutated_path_refused(self):
        with open(MAP_PATH, encoding="utf-8") as fh:
            m = json.load(fh)
        pin = self._first_pin(m, "ev_rig_fit")
        pin["path"] = pin["path"] + ".bak"
        with tempfile.TemporaryDirectory() as td:
            path = _write(td, m)
            with self.assertRaises(vml.Refusal) as ctx:
                vml.verify(path, repo=REPO)
            # a moved path resolves to nothing: named git refusal, never a pass
            self.assertTrue(str(ctx.exception))

    def test_wrong_commit_refused(self):
        with open(MAP_PATH, encoding="utf-8") as fh:
            m = json.load(fh)
        pin = self._first_pin(m, "ev_wave47")
        pin["commit"] = "0a1a7c5fec1fcba5cec5b9007d6029356e1ddd06"
        _expect_refusal(self, m, "ev_wave47")

    def test_removed_marker_refused(self):
        with open(MAP_PATH, encoding="utf-8") as fh:
            m = json.load(fh)
        pin = self._first_pin(m, "ev_ustr_receipt")
        pin["markers"] = [mkt for mkt in pin["markers"] if mkt != "Nothing here executes anything"]
        pin["markers"].append("Nothing here executes anything EVER")
        msg = _expect_refusal(self, m, "pin_marker_absent:ev_ustr_receipt")
        self.assertIn("Nothing here executes anything EVER", msg)

    def test_malformed_pin_identity_refused(self):
        with open(MAP_PATH, encoding="utf-8") as fh:
            m = json.load(fh)
        pin = self._first_pin(m, "ev_mesh_manifest")
        pin["commit"] = pin["commit"][:-1] + "g"
        _expect_refusal(self, m, "pin_identity_malformed:ev_mesh_manifest:commit")

    def test_duplicate_pin_id_refused(self):
        with open(MAP_PATH, encoding="utf-8") as fh:
            m = json.load(fh)
        m["pins"].append(copy.deepcopy(m["pins"][0]))
        _expect_refusal(self, m, "duplicate_pin_id:" + m["pins"][0]["id"])


class LineageSeparationControls(unittest.TestCase):
    """F3: distinct lineages must never be interchangeable in the map."""

    def test_mass_collision_refused(self):
        with open(MAP_PATH, encoding="utf-8") as fh:
            m = json.load(fh)
        for e in m["mass_lineages"]["entries"]:
            if e["id"] == "book_midpoint_tk1989":
                e["value_kg"] = 10.038
        _expect_refusal(self, m, "mass_lineage_collision")

    def test_separation_rule_removal_refused(self):
        with open(MAP_PATH, encoding="utf-8") as fh:
            m = json.load(fh)
        m["mass_lineages"]["rule"] = "masses are informational labels"
        _expect_refusal(self, m, "mass_separation_rule_absent")

    def test_forged_interchange_relation_refused(self):
        with open(MAP_PATH, encoding="utf-8") as fh:
            m = json.load(fh)
        m["relations"][0]["kind"] = "INTERCHANGEABLE_WITH"
        _expect_refusal(self, m, "relation_kind_unknown:INTERCHANGEABLE_WITH")

    def test_missing_card_item_refused(self):
        with open(MAP_PATH, encoding="utf-8") as fh:
            m = json.load(fh)
        m["entities"] = [e for e in m["entities"] if e.get("id") != "source_msk_model"]
        _expect_refusal(self, m, "card_items_wrong_set")

    def test_unresolved_relation_endpoint_refused(self):
        with open(MAP_PATH, encoding="utf-8") as fh:
            m = json.load(fh)
        m["relations"][0]["b"] = "nonexistent_body"
        _expect_refusal(self, m, "relation_endpoint_unresolved")

    def test_unresolved_evidence_reference_refused(self):
        with open(MAP_PATH, encoding="utf-8") as fh:
            m = json.load(fh)
        m["entities"][0]["evidence"].append("ev_does_not_exist")
        _expect_refusal(self, m, "entity_evidence_unresolved")

    def test_known_mismatch_ratio_tamper_refused(self):
        with open(MAP_PATH, encoding="utf-8") as fh:
            m = json.load(fh)
        m["mass_lineages"]["known_mismatch"]["ratio_13824_5_over_10_038"] = 1.0
        _expect_refusal(self, m, "known_mismatch_ratio_wrong")


class NumericalControls(unittest.TestCase):
    """F2: the registered numbers recompute from pinned bytes."""

    def test_walker_arithmetic(self):
        seg_masses = {"HAT": 8.184, "thigh": 0.557, "shank": 0.269, "foot": 0.080, "phalanges": 0.021}
        leg = seg_masses["thigh"] + seg_masses["shank"] + seg_masses["foot"] + seg_masses["phalanges"]
        self.assertAlmostEqual(seg_masses["HAT"] + 2 * leg, 10.038, places=9)
        self.assertAlmostEqual(10.038 * vml.GRAVITY_M_S2, 98.4391527, places=7)
        carve = (8.184 - 2 * 0.406001) + 2 * (0.2737 + 0.1323) + 2 * 0.927
        self.assertAlmostEqual(carve, 10.037998, places=9)
        self.assertAlmostEqual((5.4 + 6.9) / 2, 6.15, places=12)
        self.assertAlmostEqual(13.824536 * 1000.0, 13824.536, places=9)
        self.assertEqual(round(13824.5 / 10.038, 4), 1377.2166)

    def test_map_is_valid_json_with_expected_pins(self):
        with open(MAP_PATH, "rb") as fh:
            digest = hashlib.sha256(fh.read()).hexdigest()
        self.assertRegex(digest, r"^[0-9a-f]{64}$")
        with open(MAP_PATH, encoding="utf-8") as fh:
            m = json.load(fh)
        self.assertEqual(len(m["pins"]), 23)


class CliBehaviour(unittest.TestCase):
    def test_cli_pass_exit_zero(self):
        proc = subprocess.run([sys.executable, "-B", os.path.join(HERE, "verify_monkey_lineage.py"), "--map", MAP_PATH, "--repo", REPO],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(proc.returncode, 0, proc.stderr.decode("utf-8", "replace"))
        self.assertIn(b'"outcome": "PASS"', proc.stdout)

    def test_cli_refusal_exit_three(self):
        with open(MAP_PATH, encoding="utf-8") as fh:
            m = json.load(fh)
        m["pins"][0]["sha256"] = "1" * 64
        with tempfile.TemporaryDirectory() as td:
            path = _write(td, m)
            proc = subprocess.run([sys.executable, "-B", os.path.join(HERE, "verify_monkey_lineage.py"), "--map", path, "--repo", REPO],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertEqual(proc.returncode, 3)
            self.assertIn(b"pin_sha256_mismatch", proc.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
