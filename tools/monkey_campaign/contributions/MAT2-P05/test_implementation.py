"""test_implementation.py -- MAT2-P05 fixture regressions (failing-first).

Written BEFORE implementation.py existed; the first execution of this file
failed with ModuleNotFoundError (captured in tests_failing_first.log). All
tests are hermetic fixture tests in temp directories (plus small temp git
repositories for the blob-identity seams); none reads or writes live
campaign state, and none requires the merged ONT-P05 artifact to be present.

The MAT2-specific seams under test:
  - winner-merge resolvability (git cat-file) with findings named
  - preservation verification of merged prior evidence (raw SHA-256 of
    git-shown bytes vs winner-receipt expectations), mismatch named
  - merged-module materialization with byte verification, refusal named
  - crosswalk row extraction with the no-promotion invariant
  - dependency verdict extraction from a read-only registry payload
  - checkpoint-store hash equality against the merged report's table
  - registry read gap naming (never silent)
  - first-unmet-clause selection
  - write-boundary refusal for paths outside the attempt workspace
  - own-identity constant consistency
  - no-silent-pass: findings from reused clause functions are preserved
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import struct
import subprocess
import sys
import tempfile
import types
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import implementation as impl  # noqa: E402  (failing-first target)


def _git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args],
                          capture_output=True, text=True)


def _init_temp_repo():
    tmp = tempfile.mkdtemp(prefix="mat2p05_repo_")
    assert _git(tmp, "init", "-q").returncode == 0
    _git(tmp, "-c", "user.name=t", "-c", "user.email=t@example",
         "commit", "--allow-empty", "-q", "-m", "base")
    return pathlib.Path(tmp)


def _commit_file(repo, rel, data):
    p = pathlib.Path(repo) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)
    _git(repo, "add", rel)
    _git(repo, "-c", "user.name=t", "-c", "user.email=t@example",
         "commit", "-q", "-m", rel)
    return _git(repo, "rev-parse", "HEAD").stdout.strip()


class WinnerMergeTests(unittest.TestCase):
    def test_unresolvable_merge_named(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = impl.resolve_winner_merges(pathlib.Path(tmp),
                                             {"X": "0" * 40})
            self.assertFalse(out[0]["resolvable_commit"])
            self.assertTrue(any(f.startswith("winner_merge_unresolvable:")
                                for f in out[0]["findings"]))

    def test_resolvable_merge(self):
        repo = _init_temp_repo()
        try:
            head = _git(repo, "rev-parse", "HEAD").stdout.strip()
            out = impl.resolve_winner_merges(repo, {"X": head})
            self.assertTrue(out[0]["resolvable_commit"])
            self.assertEqual(out[0]["findings"], [])
        finally:
            pass

    def test_checkout_head_unresolvable_named(self):
        with tempfile.TemporaryDirectory() as tmp:
            ident = pathlib.Path(tmp) / "checkout_identity.json"
            ident.write_text(json.dumps({"head_sha": "f" * 40}),
                             encoding="utf-8")
            findings = impl.check_checkout_head(pathlib.Path(tmp), ident)
            self.assertTrue(any(f.startswith("checkout_head_unresolvable")
                                for f in findings))


class PreservationTests(unittest.TestCase):
    def test_preserved_bytes_match(self):
        repo = _init_temp_repo()
        data = b"prior evidence bytes\n"
        head = _commit_file(repo, "contrib/impl.py", data)
        rows = [{"rel_path": "contrib/impl.py", "merge_hint": head,
                 "expected_raw_sha256": hashlib.sha256(data).hexdigest(),
                 "task": "ONT-P05"}]
        out = impl.verify_preservation(repo, rows)
        self.assertTrue(out[0]["match"], out)
        self.assertFalse(out[0]["findings"])

    def test_preservation_mismatch_named(self):
        repo = _init_temp_repo()
        head = _commit_file(repo, "contrib/impl.py", b"actual bytes\n")
        rows = [{"rel_path": "contrib/impl.py", "merge_hint": head,
                 "expected_raw_sha256": "a" * 64, "task": "ONT-P05"}]
        out = impl.verify_preservation(repo, rows)
        self.assertFalse(out[0]["match"])
        self.assertTrue(any(f.startswith("prior_evidence_hash_mismatch")
                            for f in out[0]["findings"]))

    def test_missing_prior_artifact_named(self):
        repo = _init_temp_repo()
        head = _git(repo, "rev-parse", "HEAD").stdout.strip()
        rows = [{"rel_path": "contrib/absent.py", "merge_hint": head,
                 "expected_raw_sha256": "a" * 64, "task": "ONT-P05"}]
        out = impl.verify_preservation(repo, rows)
        self.assertFalse(out[0]["match"])
        self.assertTrue(any(f.startswith("prior_evidence_absent")
                            for f in out[0]["findings"]))


class MergedModuleLoadTests(unittest.TestCase):
    def test_load_refuses_wrong_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = pathlib.Path(tmp) / "implementation.py"
            p.write_text("x = 1\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                impl.load_merged_module(p,
                                        expected_raw_sha256="b" * 64)

    def test_load_accepts_verified_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = pathlib.Path(tmp) / "implementation.py"
            p.write_text("VALUE = 41\n", encoding="utf-8")
            digest = hashlib.sha256(p.read_bytes()).hexdigest()
            mod = impl.load_merged_module(p, expected_raw_sha256=digest)
            self.assertEqual(mod.VALUE, 41)


class CrosswalkTests(unittest.TestCase):
    ROW = {
        "archived_id": "ONT-P05",
        "archived_state": "DONE",
        "mat2_id": "MAT2-P05",
        "clause_relation": "unchanged",
        "promoted_to_acceptance": False,
        "historical_evidence_only": True,
    }

    def test_row_unpromoted_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = pathlib.Path(tmp) / "reconciliation.json"
            p.write_text(json.dumps({"crosswalk": {"rows": [dict(self.ROW)]}}),
                         encoding="utf-8")
            row = impl.extract_crosswalk_row(p, "ONT-P05", "MAT2-P05")
            self.assertIs(row["promoted_to_acceptance"], False)
            self.assertIs(row["historical_evidence_only"], True)

    def test_promoted_row_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = pathlib.Path(tmp) / "reconciliation.json"
            bad = dict(self.ROW, promoted_to_acceptance=True)
            p.write_text(json.dumps({"crosswalk": {"rows": [bad]}}),
                         encoding="utf-8")
            with self.assertRaises(ValueError):
                impl.extract_crosswalk_row(p, "ONT-P05", "MAT2-P05")

    def test_missing_row_named(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = pathlib.Path(tmp) / "reconciliation.json"
            p.write_text(json.dumps({"crosswalk": {"rows": []}}),
                         encoding="utf-8")
            with self.assertRaises(KeyError):
                impl.extract_crosswalk_row(p, "ONT-P05", "MAT2-P05")


class DependencyVerdictTests(unittest.TestCase):
    def test_done_dependency_verified(self):
        card = {"state": "DONE",
                "criteria_sha256": "c" * 64,
                "winner": {"merge_commit_sha": "d" * 40,
                           "criteria_sha256": "c" * 64}}
        repo = _init_temp_repo()
        try:
            head = _git(repo, "rev-parse", "HEAD").stdout.strip()
            card["winner"]["merge_commit_sha"] = head
            out = impl.dependency_verdict(repo, "MAT2-P03", card)
            self.assertEqual(out["state"], "DONE")
            self.assertTrue(out["merge_resolvable"])
            self.assertEqual(out["findings"], [])
        finally:
            pass

    def test_undone_dependency_named(self):
        card = {"state": "OPEN", "criteria_sha256": None, "winner": None}
        with tempfile.TemporaryDirectory() as tmp:
            out = impl.dependency_verdict(pathlib.Path(tmp), "MAT2-P03",
                                          card)
            self.assertFalse(out["satisfied"])
            self.assertTrue(out["findings"])


class CheckpointStoreTests(unittest.TestCase):
    def test_store_hash_equality(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = pathlib.Path(tmp)
            (store / "a.npy").write_bytes(b"\x93NUMPY")
            digest = hashlib.sha256((store / "a.npy").read_bytes()).hexdigest()
            rows = impl.verify_store_hashes(
                store, [("a.npy", "role")],
                {"a.npy": digest})
            self.assertEqual(rows[0]["match"], True)
            self.assertEqual(rows[0]["findings"], [])

    def test_store_hash_mismatch_named(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = pathlib.Path(tmp)
            (store / "a.npy").write_bytes(b"\x93NUMPY")
            rows = impl.verify_store_hashes(
                store, [("a.npy", "role")], {"a.npy": "e" * 64})
            self.assertIs(rows[0]["match"], False)
            self.assertTrue(any(f.startswith("store_hash_mismatch")
                                for f in rows[0]["findings"]))

    def test_store_file_absent_named(self):
        with tempfile.TemporaryDirectory() as tmp:
            rows = impl.verify_store_hashes(pathlib.Path(tmp),
                                            [("absent.npy", "role")], {})
            self.assertIs(rows[0]["match"], False)
            self.assertTrue(any(f.startswith("store_file_absent")
                                for f in rows[0]["findings"]))


class RegistryTests(unittest.TestCase):
    def test_registry_unavailable_named(self):
        out = impl.read_registry_state(pathlib.Path(tempfile.mkdtemp())
                                       / "no-such-root")
        self.assertFalse(out["available"])
        self.assertTrue(out["findings"])

    def test_registry_payload_bound(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / "agent_slots.sqlite3").write_bytes(b"not sqlite")
            out = impl.read_registry_state(root)
            self.assertFalse(out["available"])
            self.assertTrue(any(f.startswith("registry_unreadable")
                                for f in out["findings"]))


class BoundaryAndPolicyTests(unittest.TestCase):
    def test_own_identity_constants_consistent(self):
        self.assertEqual(impl.OWN["task_id"], "MAT2-P05")
        self.assertEqual(
            hashlib.sha256(impl.OWN["arrival_id"].encode()).hexdigest(),
            impl.OWN["receipt_stem"])
        self.assertEqual(len(impl.OWN["criteria_sha256"]), 64)
        self.assertEqual(len(impl.OWN["base_sha256"]), 40)

    def test_first_unmet_clause(self):
        clauses = [{"clause": "a", "satisfied": True},
                   {"clause": "b", "satisfied": False},
                   {"clause": "c", "satisfied": False}]
        self.assertEqual(impl.first_unmet_clause(clauses), "b")
        self.assertIsNone(impl.first_unmet_clause(
            [{"clause": "a", "satisfied": True}]))

    def test_write_boundary_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            inside = pathlib.Path(tmp) / "out.json"
            outside = pathlib.Path(tempfile.mkdtemp()) / "elsewhere.json"
            self.assertTrue(impl.ensure_within(inside, pathlib.Path(tmp)))
            with self.assertRaises(ValueError):
                impl.ensure_within(outside, pathlib.Path(tmp))

    def test_no_silent_pass_on_findings(self):
        fake = types.SimpleNamespace(
            audit_startup_receipts=lambda *a, **k: {
                "clause": "recoverable_commits", "findings": ["boom"],
                "satisfied": True})
        row = impl.clause_from_tool("recoverable_commits",
                                    fake.audit_startup_receipts())
        self.assertEqual(row["verdict"], "findings_present")
        self.assertIn("boom", row["findings"])

    def test_clause_pass_verdict(self):
        fake = types.SimpleNamespace(
            audit_startup_receipts=lambda *a, **k: {
                "clause": "recoverable_commits", "findings": [],
                "satisfied": True})
        row = impl.clause_from_tool("recoverable_commits",
                                    fake.audit_startup_receipts())
        self.assertEqual(row["verdict"], "pass")


if __name__ == "__main__":
    unittest.main()
