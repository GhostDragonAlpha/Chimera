"""Fixture regressions for the ONT-P05 identity audit; temp dirs only, CPU-only.

Each test drives one falsifier from the frozen PREREGISTRATION: a gap the
audit must NAME (never silently pass) and a matching fixture the audit must
actually verify through its oracle.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import implementation as impl  # noqa: E402


def write(path: pathlib.Path, data) -> pathlib.Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, str):
        data = data.encode("utf-8")
    path.write_bytes(data)
    return path


class TempCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)


class StartupReceiptTests(TempCase):
    def receipt(self, arrival="arrival-abc", task="T1", criteria="c" * 64,
                name=None):
        doc = {"schema": "chimera.startup_recovery.v1", "arrival_id": arrival,
               "task_id": task, "assignment_id": impl.EXPECTED["attempt_id"],
               "criteria_sha256": criteria,
               "resume_command": "python -B worker_start.py --arrival-id " + arrival}
        stem = name or hashlib.sha256(arrival.encode()).hexdigest()
        return write(self.root / "startup-receipts" / (stem + ".json"),
                     json.dumps(doc))

    def test_matching_receipt_verifies_and_own_receipt_binds(self):
        self.receipt()
        stem = hashlib.sha256(impl.EXPECTED["arrival_id"].encode()).hexdigest()
        self.receipt(arrival=impl.EXPECTED["arrival_id"], task="ONT-P05",
                     criteria=impl.EXPECTED["criteria_sha256"], name=stem)
        row = impl.audit_startup_receipts(self.root / "startup-receipts")
        self.assertEqual([], row["findings"])
        self.assertTrue(row["satisfied"])
        self.assertEqual(2, row["receipt_count"])
        self.assertTrue(row["own_receipt"])

    def test_forged_filename_and_wrong_identity_are_named(self):
        self.receipt(name="deadbeef")
        stem = hashlib.sha256(impl.EXPECTED["arrival_id"].encode()).hexdigest()
        self.receipt(arrival=impl.EXPECTED["arrival_id"], task="OTHER",
                     criteria="0" * 64, name=stem)
        row = impl.audit_startup_receipts(self.root / "startup-receipts")
        self.assertFalse(row["satisfied"])
        self.assertTrue(any("receipt_filename_not_arrival_digest" in f
                            for f in row["findings"]))
        self.assertTrue(any("own_receipt_mismatch" in f for f in row["findings"]))

    def test_missing_own_receipt_is_a_finding_not_a_pass(self):
        self.receipt()
        row = impl.audit_startup_receipts(self.root / "startup-receipts")
        self.assertFalse(row["satisfied"])
        self.assertTrue(any("own_startup_receipt_absent" in f
                            for f in row["findings"]))


class ManifestTests(TempCase):
    def setUp(self):
        super().setUp()
        self.base = self.root / "repo"

    def _commit_all(self):
        subprocess.run(["git", "init", "-q", str(self.base)], check=True,
                       capture_output=True)
        subprocess.run(["git", "-C", str(self.base), "add", "-A"], check=True,
                       capture_output=True)
        subprocess.run(["git", "-C", str(self.base), "-c",
                        "user.email=f@x", "-c", "user.name=f",
                        "commit", "-qm", "gen"], check=True, capture_output=True)
        return subprocess.run(["git", "-C", str(self.base), "rev-parse", "HEAD"],
                              check=True, capture_output=True,
                              text=True).stdout.strip()

    def fleet(self, corrupt_last=False, with_generation=True):
        files = []
        for i in range(3):
            data = f"payload-{i}".encode()
            write(self.base / "docs" / f"f{i}.txt", data)
            files.append({"path": f"docs/f{i}.txt", "bytes": len(data),
                          "sha256": hashlib.sha256(data).hexdigest()})
        source_base = self._commit_all() if with_generation else "b" * 40
        if corrupt_last:
            write(self.base / "docs" / "f2.txt", b"tampered")
        # mirror the real record layout: <repo>/docs/evidence/agent_fleet/
        manifest = write(self.base / "docs" / "evidence" / "agent_fleet" / "MANIFEST.json",
                         json.dumps({"source_base": source_base,
                                     "files": files}))
        return manifest

    def test_generation_bound_entries_match_and_drift_is_auxiliary(self):
        manifest = self.fleet(corrupt_last=True)
        doc, sampled, findings = impl._sha_entries_fleet(manifest, 3,
                                                         generation_repo=self.base)
        self.assertEqual([], findings)
        self.assertEqual(["generation_match"] * 3,
                         [r["generation_verdict"] for r in sampled])
        self.assertEqual("stale", sampled[2]["worktree_drift"])

    def test_unreadable_generation_is_named(self):
        manifest = self.fleet(with_generation=False)  # "b"*40 is not a commit
        _, sampled, findings = impl._sha_entries_fleet(manifest, 3,
                                                       generation_repo=self.base)
        self.assertTrue(any("source_base_unresolvable" in f for f in findings))

    def test_unlabeled_entries_and_bad_source_base_are_findings(self):
        write(self.base / "docs" / "x.txt", b"hi")
        manifest = write(self.base / "docs" / "evidence" / "agent_fleet" / "MANIFEST.json",
                         json.dumps({"source_base": "nope",
                                     "files": [{"path": "docs/x.txt"}]}))
        _, _, findings = impl._sha_entries_fleet(manifest, 5,
                                                 generation_repo=self.base)
        self.assertTrue(any("source_base_not_commit_hash" in f for f in findings))
        self.assertTrue(any("unlabeled_entry" in f for f in findings))

    def test_walk_manifest_reports_stale_and_unlabeled_lines(self):
        root = self.root / "caps"
        write(root / "g000.png", b"frame0")
        write(root / "g001.png", b"frame1-changed")
        text = (hashlib.sha256(b"frame0").hexdigest() + "  g000.png\n"
                + hashlib.sha256(b"other").hexdigest() + "  g001.png\n"
                + "not-a-hash line\n")
        manifest = write(root / "MANIFEST_sha256.txt", text)
        rows, findings = impl._sha_entries_walk(manifest, 10)
        self.assertEqual(["match", "stale"], [r["verdict"] for r in rows])
        self.assertTrue(any("unlabeled_line" in f for f in findings))


class HashLabelTests(TempCase):
    def setUp(self):
        super().setUp()
        # a real (empty) repository so the Git blob identity path is exercised
        subprocess.run(["git", "init", "-q", str(self.root)], check=True,
                       capture_output=True)

    def lock_pair(self, subject=b"sealed-bytes"):
        """The lock dual-labels ONE subject: canonical digest + raw bytes."""
        data = {"tasks": [{"id": "P05"}], "blob": subject.decode()}
        canonical = impl.content_digest(data)
        text = json.dumps(data)
        map_path = write(self.root / "map.json", text)
        lock = {"algorithm": impl.ALGORITHM, "scope_sha256": canonical,
                "raw_file_sha256": hashlib.sha256(text.encode()).hexdigest()}
        scope_path = write(self.root / "APPROVED_SCOPE.json",
                           json.dumps(lock, indent=1))
        return map_path, scope_path, canonical

    def test_dual_labels_verify_and_three_labels_stay_distinct(self):
        map_path, scope_path, canonical = self.lock_pair()
        row = impl.audit_hash_labels(map_path, scope_path, self.root,
                                     anchor=canonical)
        self.assertEqual([], row["findings"])
        self.assertTrue(row["satisfied"])
        self.assertEqual(canonical,
                         row["labels"]["canonical_sha256_chimera_json_v1"])
        self.assertEqual(impl.raw_sha256(map_path),
                         row["labels"]["raw_sha256"])
        self.assertEqual(3, len(set(row["labels"].values())))
        self.assertEqual(row["labels"]["raw_sha256"],
                         row["lock_labels"]["raw_file_sha256"])

    def test_tampered_subject_fails_both_oracles(self):
        map_path, scope_path, canonical = self.lock_pair()
        map_path.write_text('{"tasks":[{"id":"TAMPERED"}]}', encoding="utf-8")
        row = impl.audit_hash_labels(map_path, scope_path, self.root,
                                     anchor=canonical)
        self.assertFalse(row["satisfied"])
        self.assertEqual("fail", row["oracle"]["verify_catalog"])
        self.assertTrue(any("raw_label_mismatch" in f for f in row["findings"]))

    def test_missing_algorithm_label_is_a_finding(self):
        data = {"a": 1}
        map_path = write(self.root / "m2.json", json.dumps(data))
        canonical = impl.content_digest(data)
        lock = {"scope_sha256": canonical,
                "raw_file_sha256": impl.raw_sha256(map_path)}
        scope_path = write(self.root / "lock2.json", json.dumps(lock, indent=1))
        row = impl.audit_hash_labels(map_path, scope_path, self.root,
                                     anchor=canonical)
        self.assertFalse(row["satisfied"])
        self.assertTrue(any("algorithm_label_missing" in f
                            for f in row["findings"]))


class RetryRuleTests(TempCase):
    def fake_battery(self, ok=True):
        return lambda m, c: {"module": m, "ok": ok, "summary": "fixture"}

    def plant_rules(self):
        for name, tokens in impl.RETRY_MARKERS.items():
            write(self.root / name, "|".join(tokens))
        for i in range(3):
            write(self.root / f"accept-{i}-result.json", b"{}")

    def test_missing_rule_marker_is_named(self):
        row = impl.audit_retry_rules(self.root, self.root,
                                     battery_runner=self.fake_battery())
        self.assertFalse(row["satisfied"])
        self.assertTrue(any("retry_rule_record_absent" in f
                            for f in row["findings"]))

    def test_green_batteries_and_receipts_satisfy(self):
        self.plant_rules()
        row = impl.audit_retry_rules(self.root, self.root,
                                     battery_runner=self.fake_battery())
        self.assertEqual([], row["findings"])
        self.assertTrue(row["satisfied"])
        self.assertEqual(4, len(row["batteries"]))
        self.assertEqual(3, len(row["merge_service_receipts"]))

    def test_failing_battery_is_a_finding(self):
        self.plant_rules()
        row = impl.audit_retry_rules(self.root, self.root,
                                     battery_runner=self.fake_battery(ok=False))
        self.assertFalse(row["satisfied"])
        self.assertTrue(any("battery_not_green" in f for f in row["findings"]))

    def test_sparse_merge_receipts_are_a_finding(self):
        self.plant_rules()
        (self.root / "accept-2-result.json").unlink()
        row = impl.audit_retry_rules(self.root, self.root,
                                     battery_runner=self.fake_battery())
        self.assertFalse(row["satisfied"])
        self.assertTrue(any("merge_service_retry_receipts_sparse" in f
                            for f in row["findings"]))


class CheckpointStoreTests(TempCase):
    """Correction fixtures: actual recoverable training-state checkpoints.

    Each test drives one falsifier arm of correction-addendum C1: an
    identification the audit must verify (path + recomputed hash + header
    load + run identity) and a gap it must NAME, never silently pass.
    """

    def npy_bytes(self, shape=(8,), descr="<f8"):
        header = repr({"descr": descr, "fortran_order": False,
                       "shape": shape}).encode("utf-8")
        # numpy writes a python literal header; v1 pads to 64-byte alignment
        pad = 64 - (10 + len(header)) % 64
        header = header + b" " * (pad - 1) + b"\n"
        body = b"\x00" * 8 * (shape[0] if shape else 1)
        return b"\x93NUMPY" + b"\x01\x00" + len(header).to_bytes(2, "little") \
            + header + body

    def plant_store(self, root, entrained_shape=(8,), omit=None,
                    forge=None):
        store = {}
        for name, role in impl.CHECKPOINT_STORE:
            if name == omit:
                continue
            shape = entrained_shape if name.startswith("walk_theta_entrained") \
                else ((6,) if name.startswith("walk_theta") else (4,))
            data = forge if (forge and name == "walk_theta_mult.npy") \
                else self.npy_bytes(shape)
            store[name] = write(root / "ports" / name, data)
        return store

    def plant_laws(self, root):
        write(root / "train_walk.py",
              b"np.save(OUTDIR / out_name, best_ever[1])")
        write(root / "walk_port.py",
              b'OSC_JOINTS = ("hip_flexion", "knee_angle", "ankle_angle")\n'
              b"N_FREE = 2 * len(OSC_JOINTS)\n")
        write(root / "f4_walk.py", b"python tools/f4_walk.py --theta <path>")

    def plant_records(self, root, verdict=False, name="walk_theta_entrained.npy",
                      tamper_site=None):
        """Plant the run record at preserved SITE ROOTS (production joins
        agent_logs/<record>.json onto each site root)."""
        sites = []
        doc = {"theta": name, "verdict": verdict, "speed_median": 0.46,
               "seed_ids": [0]}
        raw = json.dumps(doc).encode("utf-8")
        for i in range(2):
            payload = raw + str(i).encode() if i == tamper_site else raw
            write(root / f"site{i}" / "agent_logs"
                  / "f4_walk_walk_theta_entrained.json", payload)
            sites.append(str(root / f"site{i}"))
        return sites

    def clause(self, verdict=False, tamper_site=None, record_kw=None):
        record_kw = record_kw or {}
        return impl.audit_training_checkpoints(
            self.root / "absent_curriculum.json",
            [str(self.root / "none.log")],
            [(str(self.root / "law.py"), "token")],
            checkpoint_store=self.root / "ports",
            run_record_sites=self.plant_records(self.root, verdict=verdict,
                                                tamper_site=tamper_site,
                                                **record_kw),
            trainer_law_sources=[
                (str(self.root / "train_walk.py"),
                 "np.save(OUTDIR / out_name, best_ever[1])"),
                (str(self.root / "walk_port.py"),
                 "N_FREE = 2 * len(OSC_JOINTS)"),
                (str(self.root / "f4_walk.py"), "--theta <path>"),
            ])

    def test_identified_checkpoints_verify_without_rollout(self):
        self.plant_laws(self.root)
        self.plant_store(self.root)
        row = self.clause()
        self.assertEqual([], [f for f in row["findings"]
                              if not f.startswith(("curriculum_", "training_", "checkpoint_law_"))])
        self.assertEqual(4, len(row["checkpoint_artifacts"]))
        entrained = next(r for r in row["checkpoint_artifacts"]
                         if r["checkpoint"] == "walk_theta_entrained.npy")
        self.assertEqual(64, len(entrained["raw_sha256"]))
        self.assertEqual(8, entrained["load_evidence"]["shape"][0])
        self.assertEqual(6, entrained["width_law"]["n_free"])
        self.assertEqual(8, entrained["width_law"]["expected_width"])
        self.assertEqual(0, row["certified_policy_checkpoints"])
        self.assertIn("NOT executed", entrained["restore_consumer"])
        # the run identity is hash-stable across preserved sites
        self.assertEqual(1, len({r["raw_sha256"] for r in row["run_identity_records"]
                                 if r.get("raw_sha256")}))
        self.assertEqual(False, row["run_identity_records"][0]["verdict_verbatim"])

    def test_missing_store_file_is_named(self):
        self.plant_laws(self.root)
        self.plant_store(self.root, omit="step_theta.npy")
        row = self.clause()
        self.assertTrue(any("checkpoint_store_file_absent:step_theta.npy" in f
                            for f in row["findings"]))

    def test_forged_checkpoint_fails_structural_load(self):
        self.plant_laws(self.root)
        self.plant_store(self.root, forge=b"not an npy checkpoint at all")
        row = self.clause()
        self.assertTrue(any("checkpoint_load_refused:walk_theta_mult.npy" in f
                            for f in row["findings"]))

    def test_width_mismatch_is_named(self):
        self.plant_laws(self.root)
        self.plant_store(self.root, entrained_shape=(7,))
        row = self.clause()
        self.assertTrue(any("checkpoint_width_mismatch:walk_theta_entrained.npy" in f
                            for f in row["findings"]))

    def test_disagreeing_run_record_sites_are_named(self):
        self.plant_laws(self.root)
        self.plant_store(self.root)
        row = self.clause(tamper_site=1)
        self.assertTrue(any("run_record_sites_disagree" in f
                            for f in row["findings"]))

    def test_record_naming_another_checkpoint_is_named(self):
        self.plant_laws(self.root)
        self.plant_store(self.root)
        row = self.clause(record_kw={"name": "stand_theta.npy"})
        self.assertTrue(any("run_record_names_other_checkpoint" in f
                            for f in row["findings"]))

    def test_trainer_law_token_absent_is_named(self):
        write(self.root / "train_walk.py", b"np.save(OUTDIR / 'other.npy', x)")
        write(self.root / "walk_port.py",
              b'OSC_JOINTS = ("hip_flexion", "knee_angle", "ankle_angle")\n'
              b"N_FREE = 2 * len(OSC_JOINTS)\n")
        write(self.root / "f4_walk.py", b"python tools/f4_walk.py --theta <path>")
        self.plant_store(self.root)
        row = self.clause()
        self.assertTrue(any("trainer_law_token_absent:train_walk.py" in f
                            for f in row["findings"]))


class AuditDriverTests(TempCase):
    def test_driver_tables_clauses_and_reports_gaps(self):
        result = impl.audit({
            "checkout": self.root,
            "receipts_dir": self.root / "empty",
            "fleet_manifest": self.root / "absent.json",
            "walk_manifest": self.root / "absent.txt",
            "manifest_schema_sources": [(str(self.root / "none.py"), "token")],
            "curriculum": self.root / "absent_curriculum.json",
            "training_receipts": [str(self.root / "none.log")],
            "checkpoint_law_sources": [(str(self.root / "none2.py"), "law")],
            "map": self.root / "nomap.json",
            "scope_lock": self.root / "noscope.json",
            "campaign_dir": self.root,
            "merge_receipts_dir": self.root,
        }, battery_runner=lambda m, c: {"module": m, "ok": False,
                                        "summary": "fixture"})
        self.assertEqual(5, len(result["clauses"]))
        self.assertFalse(result["all_clauses_satisfied"])
        self.assertEqual(5, len(result["clause_satisfied"]))
        self.assertTrue(result["findings"])

    def test_tool_contract_is_read_only(self):
        self.assertIn("READ-ONLY", (impl.__doc__ or ""))


if __name__ == "__main__":
    unittest.main()
