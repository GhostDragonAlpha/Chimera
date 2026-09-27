#!/usr/bin/env python3
"""Falsifier suite for the MAT2-P02 prototype-recovery claim.

Preregistered falsifiers, each encoded as a mutation control:
  F1 PIN-RESOLUTION  - a dead pin or a missed byte-identity anchor refutes
                       (M3: pin blob altered; anchors checked by P1-P4).
  F2 LINEAGE-REGRESSION - a failed or downgraded re-verification of the merged
                       records leg refutes (M6: outcome flipped, M7: counts cut).
  F3 GAP-INVENTION   - claiming a gap resolved, or a trained policy / playable
                       walk / landed judge verdict into existence, refutes
                       (M4: gap flipped RESOLVED, M5: gap deleted).
Identity controls (MAT2-P01 correction precedent): full-hash criteria/scope/
archived-scope/planning-id/attempt/prereg binding must bite on any alteration
(M1: criteria suffix, M2: scope swapped with archived).

Failing-first: this suite is RED while prototype_recovery.json or its receipts
are absent, GREEN only on the honest claim. All CPU-only, `python -B`.
"""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

PR_PATH = os.path.join(HERE, "prototype_recovery.json")
PREREG = os.path.join(HERE, "PREREGISTRATION.md")
RECEIPTS = os.path.join(HERE, "reproduction")
VERIFIER = os.path.join(HERE, "verify_prototype_recovery.py")

REPO = os.environ.get("MAT2P02_REPO")


def _run(pr_path: str, receipts_dir: str | None = None) -> subprocess.CompletedProcess:
    cmd = [sys.executable, "-B", VERIFIER, "--pr", pr_path, "--prereg", PREREG]
    if REPO:
        cmd += ["--repo", REPO]
    # mutated PR copies live in a temp dir; receipts stay in the real dir unless
    # the probe explicitly swaps them (M6/M7/anchor probes)
    cmd += ["--receipts-dir", receipts_dir or RECEIPTS]
    return subprocess.run(cmd, capture_output=True, text=True)


def _mutated(mutator) -> str:
    with open(PR_PATH, encoding="utf-8") as f:
        pr = json.load(f)
    mutator(pr)
    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(pr, f, indent=1)
    return path


@unittest.skipUnless(os.path.isfile(VERIFIER), "verifier missing")
class FailingFirstRed(unittest.TestCase):
    def test_claim_files_exist(self):
        # RED until the recovery claim and its receipts are authored.
        self.assertTrue(os.path.isfile(PR_PATH), "prototype_recovery.json missing (failing-first RED)")
        for name in ("scene_regeneration.json", "dump_run_record.json", "walk_numbers.json",
                     "behavior_bytes.json", "lineage_reverification.json"):
            self.assertTrue(os.path.isfile(os.path.join(RECEIPTS, name)), "receipt missing: " + name)


@unittest.skipUnless(os.path.isfile(PR_PATH) and os.path.isfile(os.path.join(RECEIPTS, "dump_run_record.json")),
                     "claim not authored yet (failing-first RED)")
class IdentityControls(unittest.TestCase):
    def test_honest_claim_passes(self):
        r = _run(PR_PATH)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn('"outcome": "PASS"', r.stdout)

    def test_M1_criteria_suffix_altered(self):
        def m(pr):
            pr["criteria_sha256"] = pr["criteria_sha256"][:-4] + "0000"
        p = _mutated(m)
        try:
            r = _run(p)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("identity_criteria", r.stdout)
        finally:
            os.unlink(p)

    def test_M2_scope_swapped_with_archived(self):
        def m(pr):
            pr["active_scope_sha256"], pr["archived_scope_sha256"] = pr["archived_scope_sha256"], pr["active_scope_sha256"]
        p = _mutated(m)
        try:
            r = _run(p)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("identity_scope", r.stdout)
        finally:
            os.unlink(p)

    def test_M2b_planning_id_altered(self):
        def m(pr):
            pr["planning_id"] = "P99"
        p = _mutated(m)
        try:
            r = _run(p)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("identity_planning_id", r.stdout)
        finally:
            os.unlink(p)

    def test_M2c_prereg_binding_live(self):
        # The bound preregistration sha must equal the frozen file's CURRENT bytes.
        import hashlib
        with open(PR_PATH, encoding="utf-8") as f:
            pr = json.load(f)
        actual = hashlib.sha256(open(PREREG, "rb").read()).hexdigest()
        self.assertEqual(pr["preregistration_sha256"], actual)


@unittest.skipUnless(os.path.isfile(PR_PATH) and os.path.isfile(os.path.join(RECEIPTS, "dump_run_record.json")),
                     "claim not authored yet (failing-first RED)")
class PinResolution(unittest.TestCase):
    def test_M3_pin_blob_altered(self):
        def m(pr):
            pr["pins"][0]["blob"] = pr["pins"][0]["blob"][:-1] + ("0" if pr["pins"][0]["blob"][-1] != "0" else "1")
        p = _mutated(m)
        try:
            r = _run(p)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("pin_", r.stdout)
        finally:
            os.unlink(p)

    def test_pins_resolve_against_object_store(self):
        r = _run(PR_PATH)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


@unittest.skipUnless(os.path.isfile(PR_PATH) and os.path.isfile(os.path.join(RECEIPTS, "dump_run_record.json")),
                     "claim not authored yet (failing-first RED)")
class GapAndCarryControls(unittest.TestCase):
    def test_M4_gap_flipped_resolved(self):
        def m(pr):
            pr["gaps"]["trained_walking_policy"]["status"] = "RESOLVED"
        p = _mutated(m)
        try:
            r = _run(p)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("gap_not_unresolved:trained_walking_policy", r.stdout)
        finally:
            os.unlink(p)

    def test_M5_gap_deleted(self):
        def m(pr):
            del pr["gaps"]["judge_stride_phase_verdict"]
        p = _mutated(m)
        try:
            r = _run(p)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("gap_not_unresolved:judge_stride_phase_verdict", r.stdout)
        finally:
            os.unlink(p)

    def test_M6_reverification_outcome_flipped(self):
        with tempfile.TemporaryDirectory() as td:
            for name in os.listdir(RECEIPTS):
                with open(os.path.join(RECEIPTS, name), "rb") as f:
                    data = f.read()
                with open(os.path.join(td, name), "wb") as f:
                    f.write(data)
            p5p = os.path.join(td, "lineage_reverification.json")
            rec = json.loads(open(p5p, encoding="utf-8").read())
            rec["outcome"] = "REFUSED"
            with open(p5p, "w", encoding="utf-8") as f:
                json.dump(rec, f, indent=1)
            r = _run(PR_PATH, receipts_dir=td)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("P5_outcome", r.stdout)

    def test_M7_reverification_counts_cut(self):
        with tempfile.TemporaryDirectory() as td:
            for name in os.listdir(RECEIPTS):
                with open(os.path.join(RECEIPTS, name), "rb") as f:
                    data = f.read()
                with open(os.path.join(td, name), "wb") as f:
                    f.write(data)
            p5p = os.path.join(td, "lineage_reverification.json")
            rec = json.loads(open(p5p, encoding="utf-8").read())
            rec["checks_passed"] = 151
            with open(p5p, "w", encoding="utf-8") as f:
                json.dump(rec, f, indent=1)
            r = _run(PR_PATH, receipts_dir=td)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("P5_checks", r.stdout)

    def test_anchor_mutation_bites(self):
        with tempfile.TemporaryDirectory() as td:
            for name in os.listdir(RECEIPTS):
                with open(os.path.join(RECEIPTS, name), "rb") as f:
                    data = f.read()
                with open(os.path.join(td, name), "wb") as f:
                    f.write(data)
            p2p = os.path.join(td, "dump_run_record.json")
            rec = json.loads(open(p2p, encoding="utf-8").read())
            rec["stdout_sha256"] = rec["stdout_sha256"][:-1] + ("0" if rec["stdout_sha256"][-1] != "0" else "1")
            with open(p2p, "w", encoding="utf-8") as f:
                json.dump(rec, f, indent=1)
            r = _run(PR_PATH, receipts_dir=td)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("P2_stdout_anchor", r.stdout)


if __name__ == "__main__":
    unittest.main()
