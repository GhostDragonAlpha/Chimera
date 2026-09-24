"""W1 verifier test suite (frozen in prereg.md before implementation).

Covers, per the preregistered falsifiers:
  F-W1-1  every B7 report-level value-class mutation (M01..M14) -> MISMATCH
  F-W1-2  missing sources / bad pin / unusable sources -> UNAVAILABLE-SOURCE
          (never a pass); pinned producer infrastructure failure -> PRODUCER-ERROR
  F-W1-3  identity-layer separation: a delivered report differing ONLY by a
          trailing CRLF (or missing trailing newline) must still VERIFY, while
          the raw-bytes layer would have rejected it (negative control asserted
          explicitly), and any 1-content-byte change is rejected.

Plus the decision's caveat demonstration: the B7 input-mutation controls
(M07b/M09b reports regenerated from their mutated inputs) VERIFY — producer
agreement — while surfacing blocked/not_admitted statuses and the caveat.

Run: python tests/test_source_verify.py
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

W1 = Path(__file__).resolve().parent.parent
REPO = Path("E:/ChimeraWork/mvc-20260924")
TOOLS = REPO / "tools"
CORPUS = W1 / "tests" / "corpus"
VERIFY = W1 / "material_volume_source_verify.py"
PIN = "1af0bbdee68d6ddfdd02bf9bd948f7b22f914d56"

EXAMPLE = {
    "manifest": TOOLS / "material_volume_body_export_manifest_example.json",
    "partition": TOOLS / "material_volume_body_export_partition_example.json",
    "groups": TOOLS / "material_volume_body_export_groups_example.json",
}
# Receipt identities (B4 crosscheckout + export verification receipt):
CANONICAL_REPORT_SHA = "5485c8c4fe73d679eb73f16a09e5e50778cb2d53cbe446515c971b36c57dda73"
DISK_REPORT_SHA = "d71f7621ba00701c"  # first 16 of the CRLF-materialized sha


def verify(report, manifest=None, partition=None, groups=None, revision=PIN,
           extra=()):
    cmd = [sys.executable, str(VERIFY), "--report", str(report),
           "--manifest", str(manifest or EXAMPLE["manifest"]),
           "--partition", str(partition or EXAMPLE["partition"]),
           "--groups", str(groups or EXAMPLE["groups"]),
           "--revision", revision,
           *extra]
    proc = subprocess.run(cmd, capture_output=True, cwd=str(W1),
                          env=dict(__import__("os").environ,
                                   PYTHONDONTWRITEBYTECODE="1"))
    try:
        out = json.loads(proc.stdout.decode("utf-8", "replace"))
    except json.JSONDecodeError:
        out = {"_stdout": proc.stdout.decode("utf-8", "replace")[-2000:],
               "_stderr": proc.stderr.decode("utf-8", "replace")[-2000:]}
    return proc.returncode, out


class W1VerifierSuite(unittest.TestCase):
    maxDiff = None

    # ---------- happy path + layer separation (F-W1-3) ----------

    def test_happy_path_genuine_example_verifies(self):
        code, out = verify(TOOLS / "material_volume_body_export_example_report.json")
        self.assertEqual(code, 0, out)
        self.assertEqual(out["verdict"], "VERIFIED", out)
        # Layer separation, live: the delivered file is the CRLF-materialized
        # disk form; its RAW bytes are not identity and would fail a raw-layer
        # comparison, yet it VERIFIES under the exporter's canonical layer.
        raw = (TOOLS / "material_volume_body_export_example_report.json").read_bytes()
        raw_sha = hashlib.sha256(raw).hexdigest()
        self.assertNotEqual(raw_sha, CANONICAL_REPORT_SHA)
        self.assertTrue(raw_sha.startswith(DISK_REPORT_SHA))
        identity_row = next(c for c in out["checks"]
                            if c["name"] == "report_canonical_identity")
        self.assertIn(CANONICAL_REPORT_SHA, identity_row["detail"])
        # Caveat + identity labeling, always present (decision requirement).
        self.assertEqual(out["caveat"],
                         "Regeneration proves agreement with the producer, not "
                         "correctness of the physical inputs or producer.")
        self.assertIn("NOT disk bytes", out["identity"]["report_identity_layer"])
        self.assertIn("Independent", out["independent_checks_note"])
        self.assertEqual(out["delivered_export_status"], "complete")

    def test_layer_separation_trailing_crlf_and_lf_only_still_verify(self):
        raw = (CORPUS / "valid_report.json").read_bytes()
        self.assertTrue(raw.endswith(b"\n"))
        variants = {"crlf_ending": raw[:-1] + b"\r\n",
                    "no_trailing_newline": raw[:-1],
                    "crlf_everywhere": raw.replace(b"\n", b"\r\n")}
        for label, data in variants.items():
            with self.subTest(variant=label):
                path = CORPUS / f"materialization_{label}.json"
                path.write_bytes(data)
                code, out = verify(path)
                self.assertEqual(code, 0, out)
                self.assertEqual(out["verdict"], "VERIFIED", out)

    def test_single_content_byte_change_is_mismatch(self):
        # F-W1-3 negative direction: under the canonical layer a 1-content-byte
        # change IS a mismatch (the raw-layer separation above must not be read
        # as lenience).
        raw = (CORPUS / "valid_report.json").read_text(encoding="utf-8")
        self.assertEqual(raw.count('"value":2.0}'), 1, "tamper anchor unique")
        tampered = raw.replace('"value":2.0}', '"value":2.0000000001}', 1)
        self.assertNotEqual(raw, tampered)
        path = CORPUS / "tampered_one_ulp.json"
        path.write_text(tampered, encoding="utf-8", newline="\n")
        code, out = verify(path)
        self.assertEqual(code, 1, out)
        self.assertEqual(out["verdict"], "MISMATCH", out)
        self.assertTrue(out["mismatches"], out)

    # ---------- F-W1-1: the B7 value-class matrix ----------

    def test_all_b7_value_class_report_mutations_are_caught(self):
        results = {}
        for i in range(1, 15):
            mid = f"M{i:02d}"
            with self.subTest(mutation=mid):
                code, out = verify(CORPUS / f"corrupt_{mid}.json")
                results[mid] = (code, out.get("verdict"))
                self.assertEqual(code, 1, f"{mid}: {out}")
                self.assertEqual(out["verdict"], "MISMATCH", f"{mid}: {out}")
                self.assertTrue(out["mismatches"], f"{mid} not itemized")
        self.assertEqual(sorted(results), [f"M{i:02d}" for i in range(1, 15)])

    # ---------- the decision's caveat: input-mutation controls ----------

    def test_input_mutation_controls_verify_with_caveat_surfaced(self):
        for mid in ("M07b", "M09b"):
            with self.subTest(control=mid):
                src = CORPUS / f"inputs_mutated_{mid}"
                code, out = verify(CORPUS / f"regenerated_{mid}.json",
                                   manifest=src / "manifest.json",
                                   partition=src / "partition.json",
                                   groups=src / "groups.json")
                # Producer agreement is the contract; the tampered inputs are
                # flagged by the RETAINED analytic layer, surfaced here as the
                # report's own blocked/not_admitted statuses.
                self.assertEqual(code, 0, out)
                self.assertEqual(out["verdict"], "VERIFIED", out)
                self.assertEqual(out["delivered_export_status"], "blocked", mid)
                self.assertIn(out["delivered_admission_status"],
                              {"not_admitted", "refused"}, mid)
                self.assertIn("not correctness of the physical inputs",
                              out["caveat"])

    # ---------- F-W1-2: missing/unusable source is never a pass ----------

    def test_missing_sources_and_bad_pin_are_unavailable(self):
        cases = {}
        for label in ("manifest", "partition", "groups"):
            cases[f"missing_{label}"] = verify(
                CORPUS / "valid_report.json",
                **{label: CORPUS / "does_not_exist.json"})
        code, out = verify(CORPUS / "does_not_exist.json")
        cases["missing_report"] = (code, out)
        code, out = verify(CORPUS / "valid_report.json",
                           revision="deadbeef" + "0" * 32)
        cases["unresolvable_revision"] = (code, out)
        for label, (code, out) in cases.items():
            with self.subTest(case=label):
                self.assertEqual(code, 2, f"{label}: {out}")
                self.assertEqual(out["verdict"], "UNAVAILABLE-SOURCE",
                                 f"{label}: {out}")

    def test_unusable_sources_duplicate_key_and_nan_literal(self):
        dup = CORPUS / "unusable_duplicate_key.json"
        dup.write_text('{"schema_version": "chimera.fitting_manifest.v1", '
                       '"fitting_id": "x", "fitting_id": "y"}\n',
                       encoding="utf-8", newline="\n")
        for label, path in (("duplicate_json_key", dup),):
            code, out = verify(CORPUS / "valid_report.json", manifest=path)
            with self.subTest(case=label):
                self.assertEqual(code, 2, out)
                self.assertEqual(out["verdict"], "UNAVAILABLE-SOURCE", out)
        nan = CORPUS / "unusable_nan_source.json"
        nan.write_text((CORPUS / "valid_report.json").read_text(encoding="utf-8")
                       .replace('"export_status":"complete"',
                                '"export_status":"complete","x":NaN', 1),
                       encoding="utf-8", newline="\n")
        code, out = verify(CORPUS / "valid_report.json", groups=nan)
        self.assertEqual(code, 2, out)
        self.assertEqual(out["verdict"], "UNAVAILABLE-SOURCE", out)

    # ---------- PRODUCER-ERROR: pinned producer itself fails ----------

    def test_broken_pinned_producer_is_producer_error_not_pass(self):
        scratch = W1 / "work" / "scratch_broken_repo"
        tools = scratch / "tools"
        if not (tools / "material_volume_body_export.py").exists():
            tools.mkdir(parents=True, exist_ok=True)
            (tools / "material_volume.py").write_text(
                '"""scratch repo stub"""\n', encoding="utf-8", newline="\n")
            (tools / "material_volume_admission.py").write_text(
                "import material_volume  # noqa: F401\n",
                encoding="utf-8", newline="\n")
            (tools / "material_volume_body_export.py").write_text(
                'import sys\nsys.stdout.write("not json at all")\n'
                'raise SystemExit(3)\n', encoding="utf-8", newline="\n")
            def git(*args, check=True):
                return subprocess.run(["git", *args], cwd=str(scratch),
                                      capture_output=True, check=check)
            git("init")
            git("add", "tools")
            git("-c", "user.name=w1", "-c", "user.email=w1@example.com",
                "commit", "-m", "broken producer stub")
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(scratch),
                              capture_output=True, check=True)\
            .stdout.decode().strip()
        code, out = verify(CORPUS / "valid_report.json", revision=head,
                           extra=("--repo", str(scratch)))
        self.assertEqual(code, 3, out)
        self.assertEqual(out["verdict"], "PRODUCER-ERROR", out)
        self.assertIn("failed to regenerate", out["detail"])

    # ---------- producer honesty: the PINNED bytes are what runs ----------

    def test_pinned_materialization_is_blob_bytes_not_worktree_disk(self):
        work = W1 / "work" / "pinned_pincheck"
        code, out = verify(CORPUS / "valid_report.json",
                           extra=("--work-dir", str(work)))
        self.assertEqual(code, 0, out)
        pinned_exporter = Path(out["pinned_materialization"]["tools_dir"]) \
            / "material_volume_body_export.py"
        blob = subprocess.run(
            ["git", "cat-file", "blob",
             f"{PIN}:tools/material_volume_body_export.py"],
            cwd=str(REPO), capture_output=True, check=True).stdout
        self.assertEqual(hashlib.sha256(pinned_exporter.read_bytes()).hexdigest(),
                         hashlib.sha256(blob).hexdigest(),
                         "the verifier must run the pinned blob bytes; the "
                         "worktree disk file is a CRLF materialization")
        self.assertNotEqual(pinned_exporter.read_bytes(),
                            (TOOLS / "material_volume_body_export.py").read_bytes())


if __name__ == "__main__":
    unittest.main(verbosity=2)
