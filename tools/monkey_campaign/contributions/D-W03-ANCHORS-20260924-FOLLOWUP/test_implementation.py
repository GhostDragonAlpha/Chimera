"""test_implementation.py -- D-W03-ANCHORS-20260924-FOLLOWUP targeted tests.

Covers the preregistered predictions: real-tree conversion + verification
(the honest INCOMPLETE), anchor-hash mutation, mismatched/missing source,
missing device receipt, CPU-evidence rejection, complete synthetic fixture
(QUALIFIED), and structural refusals. Fixtures are SYNTHETIC and labeled
"fixture"; no output of this suite is native acceptance.

Run:  python -B -m unittest test_implementation -v   (from this directory)
"""
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
IMPL = HERE / "implementation.py"

PLAY_REPO = pathlib.Path("E:/ChimeraWork/monkey-play-20260924")
PARENT_DIR = pathlib.Path("E:/ChimeraWork/monkey-coordination/kanban-attempts/"
                          "D-W03-ANCHORS-20260924/f7fd439796784e7e980a33cd90978c0d")
MANIFEST = PARENT_DIR / "anchor_manifest_v2.proposal.json"
TIE2_ROOT = PLAY_REPO / "tools/monkey_campaign/agents/TIE2"

PROV = "a62b286effa27ee2db7bbcb65507a2ac45ad0d0c"


def run_impl(argv, timeout=110):
    proc = subprocess.run([sys.executable, "-B", str(IMPL), *argv],
                          capture_output=True, timeout=timeout)
    return {"exit": proc.returncode,
            "stdout": proc.stdout.decode("utf-8", "replace"),
            "stderr": proc.stderr.decode("utf-8", "replace")}


def git(repo, *argv):
    proc = subprocess.run(["git", "-C", str(repo), *argv], capture_output=True)
    assert proc.returncode == 0, proc.stderr.decode("utf-8", "replace")
    return proc.stdout.decode("utf-8", "replace").strip()


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def to_crlf(data: bytes) -> bytes:
    return data.replace(b"\n", b"\r\n")


def make_fixture_repo():
    """Throwaway git repo + on-disk receipts; everything labeled fixture."""
    root = pathlib.Path(tempfile.mkdtemp(prefix="d_w03_fixture_"))
    (root / "anchors").mkdir()
    (root / "scripts").mkdir()
    files = {
        "anchors/state_host.txt": b"fixture host state line1\nline2\n",
        "anchors/state_device.txt": b"fixture device state line1\nline2\n",
        "scripts/build_v2.ps1": b"# fixture build script\nwrite-output fixture\n",
    }
    for rel, data in files.items():
        (root / rel).write_bytes(data)
    git(root, "init", "-q")
    git(root, "config", "core.autocrlf", "false")
    git(root, "config", "user.email", "fixture@example.invalid")
    git(root, "config", "user.name", "fixture")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "fixture anchor sources")
    commit = git(root, "rev-parse", "HEAD")

    receipts = pathlib.Path(tempfile.mkdtemp(prefix="d_w03_receipts_"))
    (receipts / "device_replay_fresh.out").write_bytes(
        b"fixture FRESH device replay t=1..43 bit-identical\n")
    (receipts / "host_leg_historical.out").write_bytes(
        b"fixture HISTORICAL host parity capture\n")

    def certificate(with_device_receipt=True, device_nature="fresh",
                    close_gates=True, mutate_anchor=None, anchor_commit=None,
                    break_device_path=False):
        anchors = [{
            "anchor_id": "fx-state-host", "klass": "fixture",
            "commit": anchor_commit or commit, "repo_path": "anchors/state_host.txt",
            "convention": "raw", "expected_sha256": sha(files["anchors/state_host.txt"]),
        }, {
            "anchor_id": "fx-state-device-crlf", "klass": "fixture",
            "commit": commit, "repo_path": "anchors/state_device.txt",
            "convention": "lf-to-crlf",
            "expected_sha256": sha(to_crlf(files["anchors/state_device.txt"])),
        }]
        if mutate_anchor:
            anchors[0]["expected_sha256"] = "0" * 64
        outputs = [{
            "output_id": "fx-host-historical",
            "leg": "host", "nature": "historical",
            "location": {"type": "on_disk",
                         "path": str(receipts / "host_leg_historical.out"),
                         "expected_sha256": sha(b"fixture HISTORICAL host parity capture\n")},
        }]
        if with_device_receipt:
            dev_path = ((receipts / "deleted_device_replay_fresh.out")
                        if break_device_path
                        else (receipts / "device_replay_fresh.out"))
            outputs.append({
                "output_id": "fx-device-fresh",
                "leg": "device", "nature": device_nature,
                "location": {"type": "on_disk",
                             "path": str(dev_path),
                             "expected_sha256": sha(b"fixture FRESH device replay t=1..43 bit-identical\n")},
            })
        comparisons = [{
            "comparison_id": "fx-parity",
            "kind": "host_device_parity",
            "requires": ["device_leg_fresh"],
            "evidence": (["fx-device-fresh", "fx-host-historical"]
                         if with_device_receipt else ["fx-host-historical"]),
        }]
        ev = (["fx-device-fresh"] if (with_device_receipt and close_gates) else [])
        gates = [{"gate_id": "G1-fixture", "status": "CLOSED" if close_gates else "OPEN",
                  "evidence": ev},
                 {"gate_id": "G2-fixture", "status": "CLOSED" if close_gates else "OPEN",
                  "evidence": ev}]
        return {
            "schema": "chimera.walking_anchor_certificate.v1",
            "subject": {"card": "W03-fixture", "note": "synthetic fixture"},
            "source": {"provenance_commit": commit, "required_reachable": True},
            "anchors": anchors,
            "binaries": [{
                "binary_id": "fx-walker-dll", "anchoring": "source_build",
                "source_commit": commit,
                "build_script": {"repo_path": "scripts/build_v2.ps1",
                                 "convention": "raw",
                                 "expected_sha256": sha(files["scripts/build_v2.ps1"])},
                "on_disk": None if not close_gates else {
                    "path": str(receipts / "device_replay_fresh.out"),
                    "expected_sha256": sha(b"fixture FRESH device replay t=1..43 bit-identical\n")},
            }],
            "outputs": outputs,
            "comparisons": comparisons,
            "gates": gates,
            "device_proof_required": True,
        }

    return root, commit, receipts, certificate


class FixtureCertificateTests(unittest.TestCase):
    """Predictions 5 + controls (mutation/mismatch/missing/CPU-substitution)."""

    @classmethod
    def setUpClass(cls):
        cls.root, cls.commit, cls.receipts, make = make_fixture_repo()
        cls.make_certificate = staticmethod(make)   # avoid method binding
        cls.tmp = pathlib.Path(tempfile.mkdtemp(prefix="d_w03_out_"))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.root, ignore_errors=True)
        shutil.rmtree(cls.receipts, ignore_errors=True)
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def _verify(self, cert, name):
        path = self.tmp / (name + ".json")
        path.write_text(json.dumps(cert), encoding="utf-8")
        out = self.tmp / (name + "_out")
        res = run_impl(["verify", "--certificate", str(path),
                        "--repo", str(self.root), "--out", str(out)])
        verdict = None
        if (out / "verdict.json").is_file():
            verdict = json.loads((out / "verdict.json").read_text(encoding="utf-8"))
        return res, verdict

    def test_complete_synthetic_certificate_qualifies(self):
        res, verdict = self._verify(self.make_certificate(), "complete")
        self.assertEqual(res["exit"], 0, res)
        self.assertEqual(verdict["verdict"], "QUALIFIED")
        self.assertEqual(verdict["findings"], [])
        self.assertTrue(all(c["satisfied"] for c in verdict["comparisons"]))

    def test_mutated_anchor_hash_fails_named(self):
        res, verdict = self._verify(self.make_certificate(mutate_anchor=True), "mutated")
        self.assertEqual(res["exit"], 1)
        self.assertEqual(verdict["verdict"], "INCOMPLETE")
        codes = [f["code"] for f in verdict["findings"]]
        self.assertIn("anchor_hash_mismatch", codes)
        subject = next(f for f in verdict["findings"]
                       if f["code"] == "anchor_hash_mismatch")["subject"]
        self.assertEqual(subject, "fx-state-host")

    def test_missing_device_receipt_reported_missing(self):
        """Device receipt listed (nature=fresh) but its file is gone."""
        res, verdict = self._verify(self.make_certificate(break_device_path=True,
                                                          close_gates=False),
                                    "nodevice")
        self.assertEqual(res["exit"], 1)
        self.assertEqual(verdict["verdict"], "INCOMPLETE")
        self.assertFalse(verdict["comparisons"][0]["satisfied"])
        self.assertIn("output_missing",
                      [f["code"] for f in verdict["findings"]])

    def test_cpu_only_evidence_rejected_named(self):
        """Only host/historical evidence offered -> named CPU rejection."""
        res, verdict = self._verify(self.make_certificate(with_device_receipt=False,
                                                          close_gates=False),
                                    "cpuonly")
        self.assertEqual(res["exit"], 1)
        self.assertFalse(verdict["comparisons"][0]["satisfied"])
        self.assertIn("cpu_evidence_not_device_proof",
                      [f["code"] for f in verdict["findings"]])

    def test_cpu_evidence_never_closes_device_comparison(self):
        """Historical host evidence present, device receipt historical-natured:
        comparison stays unsatisfied with the named CPU rejection."""
        res, verdict = self._verify(self.make_certificate(device_nature="historical",
                                                     close_gates=False),
                                    "cpu_subst")
        self.assertEqual(res["exit"], 1)
        self.assertFalse(verdict["comparisons"][0]["satisfied"])
        self.assertIn("cpu_evidence_not_device_proof",
                      [f["code"] for f in verdict["findings"]])

    def test_gate_evidence_downgrade(self):
        """CLOSED gate whose evidence vanished is reported effective OPEN."""
        cert = self.make_certificate()
        cert["gates"][0]["evidence"] = ["fx-nonexistent"]
        res, verdict = self._verify(cert, "gateev")
        self.assertEqual(res["exit"], 1)
        self.assertIn("gate_evidence_missing",
                      [f["code"] for f in verdict["findings"]])
        g = next(g for g in verdict["gates"] if g["gate_id"] == "G1-fixture")
        self.assertEqual((g["declared"], g["effective"]), ("CLOSED", "OPEN"))

    def test_unresolvable_commit_refuses(self):
        cert = self.make_certificate()
        cert["anchors"][0]["commit"] = "1" * 40
        path = self.tmp / "badpin.json"
        path.write_text(json.dumps(cert), encoding="utf-8")
        res = run_impl(["verify", "--certificate", str(path),
                        "--repo", str(self.root), "--out", str(self.tmp / "badpin_out")])
        self.assertEqual(res["exit"], 3)
        self.assertIn("PIN_UNRESOLVABLE", res["stderr"])
        self.assertFalse((self.tmp / "badpin_out" / "verdict.json").is_file())

    def test_wrong_schema_refuses(self):
        path = self.tmp / "badschema.json"
        path.write_text(json.dumps({"schema": "nope"}), encoding="utf-8")
        res = run_impl(["verify", "--certificate", str(path),
                        "--repo", str(self.root), "--out", str(self.tmp / "bs_out")])
        self.assertEqual(res["exit"], 3)
        self.assertIn("CERT_SCHEMA_UNKNOWN", res["stderr"])


class RealTreeTests(unittest.TestCase):
    """Predictions 1-2: convert the parent manifest; verify the real tree."""

    @classmethod
    def setUpClass(cls):
        if not (PLAY_REPO.is_dir() and MANIFEST.is_file()):
            raise unittest.SkipTest("play repo or parent manifest absent")
        cls.tmp = pathlib.Path(tempfile.mkdtemp(prefix="d_w03_real_"))
        cls.cert_path = cls.tmp / "certificate.json"
        res = run_impl(["from-manifest", "--manifest", str(MANIFEST),
                        "--tie2-disk-root", str(TIE2_ROOT),
                        "--out", str(cls.cert_path)])
        assert res["exit"] == 0, res
        cls.cert = json.loads(cls.cert_path.read_text(encoding="utf-8"))
        cls.out = cls.tmp / "out"
        cls.res = run_impl(["verify", "--certificate", str(cls.cert_path),
                            "--repo", str(PLAY_REPO), "--out", str(cls.out)])
        cls.verdict = json.loads((cls.out / "verdict.json").read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_real_tree_incomplete_exit_1(self):
        self.assertEqual(self.res["exit"], 1)
        self.assertEqual(self.verdict["verdict"], "INCOMPLETE")

    def test_all_18_git_anchors_verify(self):
        self.assertEqual(self.verdict["checked"]["anchors"], 18)
        self.assertNotIn("anchor_hash_mismatch",
                         [f["code"] for f in self.verdict["findings"]])
        self.assertNotIn("anchor_path_missing",
                         [f["code"] for f in self.verdict["findings"]])

    def test_provenance_orphan_reported_g1(self):
        codes = [f["code"] for f in self.verdict["findings"]]
        self.assertIn("provenance_commit_unreachable", codes)
        self.assertEqual(self.verdict["findings"][0]["subject"], PROV[:12])

    def test_binaries_not_rebuilt_g2(self):
        codes = [f["code"] for f in self.verdict["findings"]]
        self.assertEqual(codes.count("binary_not_rebuilt"), 4)

    def test_tie2_outputs_verify_but_device_proofs_missing(self):
        # The live worktree is MUTABLE (it advanced past the parent card's
        # evidence day): assert the honest outcome for whichever state the
        # TIE2 battery files are in -- 5/5 verified when present (the
        # parent card's recorded state), or named output_missing findings
        # when the worktree has moved on. Either way the device-proof law
        # holds: no comparison is satisfied by CPU evidence.
        tie2_files = ("run/tie_boundary_probe.cxx", "run/tie_boundary_probe.exe",
                      "run/build_tie_probe.cmd",
                      "receipts/case123_tie_boundary_host.out",
                      "receipts/case5_replay_host_v2.out")
        present = all((TIE2_ROOT / rel).is_file() for rel in tie2_files)
        if present:
            self.assertEqual(self.verdict["checked"]["outputs"], 5)
        else:
            self.assertEqual(self.verdict["checked"]["outputs"], 0)
            missing = [f for f in self.verdict["findings"]
                       if f["code"] == "output_missing"]
            self.assertTrue(missing, "absent receipts must be named, not silent")
        codes_all = [f["code"] for f in self.verdict["findings"]]
        if present:
            self.assertIn("cpu_evidence_not_device_proof", codes_all)
        satisfied = {c["comparison_id"]: c["satisfied"]
                     for c in self.verdict["comparisons"]}
        self.assertFalse(satisfied["host_device_parity_t1_t43"])
        self.assertFalse(satisfied["c3_bars_remeasure"])
        codes = [f["code"] for f in self.verdict["findings"]]
        self.assertIn("output_missing", codes)

    def test_certificate_structure_from_manifest(self):
        self.assertEqual(len(self.cert["anchors"]), 18)
        self.assertEqual(len(self.cert["binaries"]), 4)
        convs = {a["convention"] for a in self.cert["anchors"]}
        self.assertEqual(convs, {"raw", "lf-to-crlf"})

    def test_mutated_real_anchor_fails_named(self):
        cert = dict(self.cert)
        cert = json.loads(json.dumps(self.cert))
        cert["anchors"][0]["expected_sha256"] = "0" * 64
        path = self.tmp / "cert_mut.json"
        path.write_text(json.dumps(cert), encoding="utf-8")
        res = run_impl(["verify", "--certificate", str(path),
                        "--repo", str(PLAY_REPO), "--out", str(self.tmp / "out_mut")])
        self.assertEqual(res["exit"], 1)
        v = json.loads((self.tmp / "out_mut" / "verdict.json").read_text(encoding="utf-8"))
        f = next(f for f in v["findings"] if f["code"] == "anchor_hash_mismatch")
        self.assertEqual(f["subject"], self.cert["anchors"][0]["anchor_id"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
