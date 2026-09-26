#!/usr/bin/env python3
"""Falsifier suite for the ONT-S01 provenance registry verifier (card ONT-S01).

Every mutation control encodes a preregistered falsifier: a dead pin (F1), an
identity mismatch (F2), a coverage hole / blanket-clearance violation (F3, F5),
unsupported terms (F4), or a verifier blind spot (F6). The live-records
integration proves the shipped registry passes against the real git object
store and on-disk evidence, and that the verifier is idempotent (P-6).

CPU-only, offline (git plumbing against the local object store only).
"""
from __future__ import annotations

import copy
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import verify_provenance as vp  # noqa: E402

REGISTRY_PATH = os.path.join(HERE, "provenance_registry.json")
# mutation copies live in a temp dir outside any worktree, so the object store
# under test is pinned explicitly to the store that resolves the shipped registry
REPO = vp._resolve_repo(None, REGISTRY_PATH)


def _write(tmpdir: str, reg: dict) -> str:
    path = os.path.join(tmpdir, "mutated_registry.json")
    with open(path, "wb") as fh:
        fh.write(json.dumps(reg, indent=2, ensure_ascii=False).encode("utf-8"))
    return path


def _expect_refusal(self: unittest.TestCase, reg: dict, fragment: str) -> str:
    with tempfile.TemporaryDirectory() as td:
        path = _write(td, reg)
        try:
            vp.verify(path, repo=REPO, disk_root=HERE)
        except vp.Refusal as exc:
            message = str(exc)
            self.assertIn(fragment, message,
                          f"refusal {message!r} does not name {fragment!r}")
            return message
    self.fail(f"expected refusal naming {fragment!r}; verifier passed a mutated registry")
    raise AssertionError("unreachable")


def _row(reg: dict, rid: str) -> dict:
    return next(r for r in reg["rows"] if r["id"] == rid)


def _pin(reg: dict, pid: str) -> dict:
    return next(p for p in reg["pins"] if p["id"] == pid)


class LiveRecordsIntegration(unittest.TestCase):
    """The shipped registry must pass against the real records, twice."""

    def test_live_registry_passes(self):
        report = vp.verify(REGISTRY_PATH, repo=REPO)
        self.assertEqual(report["outcome"], "PASS")
        self.assertEqual(report["pins_resolved"], 12)
        self.assertEqual(report["deep_checks_resolved"], 3)
        self.assertEqual(report["rows_checked"], 18)
        self.assertEqual(report["explicit_surface_paths"], 20)
        self.assertEqual(report["set_coverage_rows"], 1)
        self.assertEqual(report["restricted_rows"], ["R3", "R4", "R5", "R6"])
        self.assertTrue(report["closure_rule_enforced"])
        self.assertGreaterEqual(report["verdicts"].get("CLEAR", 0), 6)

    def test_live_registry_passes_idempotently(self):
        first = vp.verify(REGISTRY_PATH, repo=REPO)
        second = vp.verify(REGISTRY_PATH, repo=REPO)
        self.assertEqual(first, second)

    def test_criteria_identity_bound(self):
        with self.assertRaises(vp.Refusal) as ctx:
            vp.verify(REGISTRY_PATH, repo=REPO, expected_criteria="0" * 64)
        self.assertIn("criteria_mismatch", str(ctx.exception))

    def test_scope_identity_bound(self):
        reg = copy.deepcopy(_REG)
        reg["scope_sha256"] = "0" * 64
        _expect_refusal(self, reg, "scope_mismatch")

    def test_observation_is_load_bearing(self):
        reg = copy.deepcopy(_REG)
        reg["observation_enforced"] = "Existing license receipts clear everything"
        _expect_refusal(self, reg, "observation_dropped")


class F1DeadPin(unittest.TestCase):
    def test_mutated_pin_sha256_refused(self):
        reg = copy.deepcopy(_REG)
        _pin(reg, "ev_ship_surface_hashes")["sha256"] = "0" * 64
        _expect_refusal(self, reg, "pin_sha256_mismatch")

    def test_mutated_pin_blob_refused(self):
        reg = copy.deepcopy(_REG)
        _pin(reg, "ev_download_receipt")["blob"] = "0" * 40
        _expect_refusal(self, reg, "pin_blob_mismatch")

    def test_dead_commit_refused(self):
        reg = copy.deepcopy(_REG)
        _pin(reg, "ev_ship_request")["commit"] = "0" * 40
        _expect_refusal(self, reg, "pin_dead")

    def test_mutated_pin_marker_refused(self):
        reg = copy.deepcopy(_REG)
        _pin(reg, "ev_repo_license")["markers"] = ["GNU AFFERO GENERAL PUBLIC LICENSE", "Version 4"]
        _expect_refusal(self, reg, "pin_marker_missing")

    def test_deep_check_identity_refused(self):
        reg = copy.deepcopy(_REG)
        next(c for c in reg["deep_checks"] if c["id"] == "deep_agreement_pdf")["sha256"] = "1" * 64
        _expect_refusal(self, reg, "deep_identity_mismatch")


class F2DiskIdentity(unittest.TestCase):
    @unittest.skipUnless(os.path.isfile("C:/Python314/LICENSE.txt"),
                         "recorded on-disk evidence not present on this machine")
    def test_disk_sha_drift_refused(self):
        reg = copy.deepcopy(_REG)
        next(i for i in reg["on_disk_evidence"] if i["id"] == "disk_psf_license")["sha256"] = "2" * 64
        _expect_refusal(self, reg, "disk_evidence_sha256_mismatch")

    @unittest.skipUnless(os.path.isfile("C:/Python314/LICENSE.txt"),
                         "recorded on-disk evidence not present on this machine")
    def test_disk_evidence_file_absent_refused(self):
        reg = copy.deepcopy(_REG)
        next(i for i in reg["on_disk_evidence"] if i["id"] == "disk_psf_license")["path"] = \
            "C:/Python314/DEFINITELY_NOT_HERE_LICENSE.txt"
        _expect_refusal(self, reg, "disk_evidence_missing")


class F3CoverageHole(unittest.TestCase):
    def test_deleted_row_uncovered_path_refused(self):
        reg = copy.deepcopy(_REG)
        reg["rows"] = [r for r in reg["rows"] if r["id"] != "R4"]
        reg["surface_enumeration"]["expected_row_count"] = 17
        message = _expect_refusal(self, reg, "coverage_hole_unregistered_surface")
        self.assertIn("standing_body.glb", message)

    def test_extra_covered_path_refused(self):
        reg = copy.deepcopy(_REG)
        _row(reg, "R15")["covers"].append("tools/monkey_campaign/product/new_future_asset.obj")
        _expect_refusal(self, reg, "coverage_extra_unenumerated")

    def test_future_asset_on_surface_refused_via_enumeration_size(self):
        # a shipped surface that grows without a new row breaks the declared size
        reg = copy.deepcopy(_REG)
        reg["surface_enumeration"]["expected_explicit_path_count"] = 21
        _expect_refusal(self, reg, "surface_size_mismatch")

    def test_double_coverage_refused(self):
        reg = copy.deepcopy(_REG)
        _row(reg, "R2")["covers"].append("tools/playable_slice/standing_body.glb")
        _expect_refusal(self, reg, "coverage_double_claim")


class F4UnsupportedTerms(unittest.TestCase):
    def test_row_terms_without_evidence_refused(self):
        reg = copy.deepcopy(_REG)
        _row(reg, "R6")["terms"] = "trusted: everybody says these are fine"
        _expect_refusal(self, reg, "row_terms_without_evidence")

    def test_clear_verdict_without_evidence_refused(self):
        reg = copy.deepcopy(_REG)
        _row(reg, "R13")["terms"] = "clear because the project owns it, presumably"
        _expect_refusal(self, reg, "row_terms_without_evidence")

    def test_row_source_missing_refused(self):
        reg = copy.deepcopy(_REG)
        _row(reg, "R14")["source"] = ""
        _expect_refusal(self, reg, "row_source_or_artifact_missing")

    def test_restricted_row_without_gate_refused(self):
        reg = copy.deepcopy(_REG)
        _row(reg, "R3")["distribution_gate"] = ""
        _expect_refusal(self, reg, "restricted_row_without_gate")

    def test_pending_build_row_without_action_refused(self):
        reg = copy.deepcopy(_REG)
        _row(reg, "R7")["identity_action"] = ""
        _expect_refusal(self, reg, "pending_identity_without_action")

    def test_not_shipped_row_without_exclusion_refused(self):
        reg = copy.deepcopy(_REG)
        _row(reg, "R17")["structural_exclusion"] = ""
        _expect_refusal(self, reg, "not_shipped_without_exclusion")

    def test_unknown_verdict_refused(self):
        reg = copy.deepcopy(_REG)
        _row(reg, "R11")["verdict"] = "TRUST_ME"
        _expect_refusal(self, reg, "row_verdict_unknown")


class F5BlanketClearance(unittest.TestCase):
    def test_removed_future_asset_duty_refused(self):
        reg = copy.deepcopy(_REG)
        reg["closure_rule"]["future_asset_duty"] = "receipts carry over to any new asset"
        _expect_refusal(self, reg, "closure_rule_missing:no_future_asset_duty")

    def test_removed_closure_statement_refused(self):
        reg = copy.deepcopy(_REG)
        reg["closure_rule"]["statement"] = "coverage is advisory"
        _expect_refusal(self, reg, "closure_rule_missing:not_closed_world")

    def test_dropped_operator_gate_reference_refused(self):
        reg = copy.deepcopy(_REG)
        _row(reg, "R5")["distribution_gate"] = "some memo somewhere"
        _expect_refusal(self, reg, "restricted_row_without_gate")


class F6VerifierBlindSpot(unittest.TestCase):
    def test_set_coverage_count_refused(self):
        reg = copy.deepcopy(_REG)
        _row(reg, "R6")["covers_set"]["expected_files"] = 24
        _expect_refusal(self, reg, "set_coverage_count_mismatch")

    def test_row_count_drift_refused(self):
        reg = copy.deepcopy(_REG)
        reg["surface_enumeration"]["expected_row_count"] = 19
        _expect_refusal(self, reg, "row_count_mismatch")

    def test_declared_extra_without_marker_record_refused(self):
        reg = copy.deepcopy(_REG)
        reg["surface_enumeration"]["declared_extras"][0]["marker_source"] = "no_such_pin"
        _expect_refusal(self, reg, "extra_marker_source_unknown")

    def test_primary_enumeration_not_parseable_refused(self):
        reg = copy.deepcopy(_REG)
        # point the primary enumeration at a pin whose bytes carry no hash lines
        reg["surface_enumeration"]["primary_receipt"] = "ev_s01_report"
        message = _expect_refusal(self, reg, "surface_enumeration_size")
        self.assertIn("expected 11", message)

    def test_missing_primary_enumeration_pin_refused(self):
        reg = copy.deepcopy(_REG)
        reg["surface_enumeration"]["primary_receipt"] = "ev_no_such_pin"
        _expect_refusal(self, reg, "primary_enumeration_pin_missing")


_REG = json.loads(open(REGISTRY_PATH, "rb").read().decode("utf-8"))

if __name__ == "__main__":
    unittest.main(verbosity=2)
