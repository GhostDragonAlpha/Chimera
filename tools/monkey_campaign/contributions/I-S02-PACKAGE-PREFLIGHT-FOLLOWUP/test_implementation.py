"""test_implementation.py -- I-S02-PACKAGE-PREFLIGHT-FOLLOWUP (CPU-only, synthetic).

Every test builds a synthetic minimal package under TemporaryDirectory. No
repository source file is opened; the only contribution-owned bytes any test reads
are THIS contribution's own vendored ``reference/`` copy (F5 pin check) and this
contribution's own ``implementation.py`` (F4 vocabulary scan). No network, no GPU,
no junction/symlink creation (the pinned checker's junction coverage is inherited,
not re-tested). Fixtures are fixtures -- nothing here is native-acceptance evidence.

Falsifiers (PREREGISTRATION.md section 4, frozen before implementation):
  F1 relocation      -> test_f1_*  (byte-identical manifests, identical verdicts)
  F2 missing assets  -> test_f2_*  (refuse production / P-MISSING)
  F3 undeclared dev  -> test_f3_*  (P-DEVROOT / STAGE-UNDECLARED)
  F4 externality     -> test_f4_*  (admission refs required; no permission verdict)
  F5 byte-pin        -> test_f5_*  (vendored bytes == frozen #153 pin)
  F6 exact admission -> test_f6_*  (manifest declares exactly the admitted set)
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

import implementation as impl
from implementation import (PRODUCED, REFUSED, AdapterRefusal, REFERENCE_SHA256,
                            audit_staging, load_pinned_preflight,
                            produce_manifest, run_preflight)

PINNED = load_pinned_preflight()
PASS, FAIL = PINNED.VERDICTS

# --- synthetic minimal package (a stand-in for the demo-lane shape) ----------

DEMO_BAT = ("@echo off\r\ntitle DEMO\r\n"
            "powershell -NoProfile -ExecutionPolicy Bypass -File "
            "\"%~dp0tools\\run_demo.ps1\" %*\r\n").encode("ascii")
RUN_DEMO = ("$ErrorActionPreference = 'Stop'\n"
            "$Root = Split-Path -Parent $PSScriptRoot\n"
            "$gallery = Join-Path $Root 'ChimeraEngine\\gallery.py'\n"
            "if (-not (Test-Path $gallery)) { exit 1 }\n").encode("ascii")
GALLERY = ("import json\nimport pathlib\n"
           "print('gallery')\n").encode("ascii")

DEVROOT_CONFIG = ("# fixture config\n"
                  "log_to = 'E:/PythonChimera/dev_out'\n").encode("ascii")

#: The synthetic launcher names powershell, so a PASSING preflight needs it
#: declared (the pinned checker's P-EXT-TOOL law, exercised honestly).
DEPS = {"modules": [], "system": ["powershell"]}

ADMISSION_SOURCE = ("fixture: synthetic admission record (s01-matrix shape), "
                    "no real asset admitted")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def admission(*rows) -> dict:
    return {"source": ADMISSION_SOURCE, "entries": list(rows)}


def demo_rows(text_configs=True):
    launcher = {"path": "DEMO.bat", "role": "launcher",
                "decision_ref": "fixture-admission#demo-bat"}
    ps1 = {"path": "tools/run_demo.ps1", "role": "launcher",
           "decision_ref": "fixture-admission#run-demo"}
    if text_configs:
        launcher["text_config"] = True
        ps1["text_config"] = True
    return [launcher, ps1,
            {"path": "ChimeraEngine/gallery.py", "role": "runtime",
             "decision_ref": "fixture-admission#gallery"}]


def stage(root: Path, files: dict):
    for rel, data in files.items():
        target = root.joinpath(*rel.split("/"))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return root


def build_demo(root: Path, gallery: bytes = GALLERY) -> Path:
    return stage(root, {"DEMO.bat": DEMO_BAT,
                        "tools/run_demo.ps1": RUN_DEMO,
                        "ChimeraEngine/gallery.py": gallery})


def produce_deps(root: Path, rows=None):
    return produce_manifest(root, admission(*(rows or demo_rows())),
                            package_name="fixture", declared_dependencies=DEPS)


class FalsifierTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="s02_followup_")
        self.base = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    # ---- F1: relocation -----------------------------------------------------
    def test_f1_manifest_bytes_identical_across_roots(self):
        a = build_demo(self.base / "a" / "deep" / "nest")
        b = build_demo(self.base / "b")
        prod_a = produce_deps(a)
        prod_b = produce_deps(b)
        self.assertEqual(prod_a.verdict, PRODUCED, prod_a.refusals_json())
        self.assertEqual(prod_b.verdict, PRODUCED, prod_b.refusals_json())
        self.assertEqual(prod_a.canonical_json(), prod_b.canonical_json(),
                         "identical content at two roots must give identical manifest")

    def test_f1_preflight_pass_identical_at_both_roots(self):
        manifest = produce_deps(build_demo(self.base / "x")).manifest
        self.assertIsNotNone(manifest)
        at_a = run_preflight(build_demo(self.base / "p1" / "one"), manifest)
        at_b = run_preflight(build_demo(self.base / "p2"), manifest)
        self.assertEqual(at_a.verdict, PASS, at_a.findings_json())
        self.assertEqual(at_b.verdict, PASS)
        self.assertEqual(at_a.findings_json(), at_b.findings_json())

    def test_f1_corruption_fails_identically_at_both_roots(self):
        manifest = produce_deps(build_demo(self.base / "src")).manifest
        ra = run_preflight(build_demo(self.base / "c1", gallery=GALLERY + b"# t\n"),
                           manifest)
        rb = run_preflight(build_demo(self.base / "c2" / "deep",
                                      gallery=GALLERY + b"# t\n"), manifest)
        self.assertEqual(ra.verdict, FAIL)
        self.assertEqual(rb.verdict, FAIL)
        self.assertEqual(ra.findings_json(), rb.findings_json(),
                         "corruption must break identically at both roots")

    # ---- F2: missing assets -------------------------------------------------
    def test_f2_missing_admitted_file_refuses_production(self):
        root = build_demo(self.base / "partial")
        rows = demo_rows() + [{"path": "ChimeraEngine/missing.bin", "role": "runtime",
                               "decision_ref": "fixture-admission#missing"}]
        prod = produce_manifest(root, admission(*rows), package_name="fixture")
        self.assertEqual(prod.verdict, REFUSED)
        self.assertIsNone(prod.manifest,
                          "ALL-OR-NOTHING: no partial manifest may exist")
        codes = {c for c, _, _ in prod.refusals}
        self.assertIn("SOURCE-MISSING", codes)
        self.assertEqual([p for c, p, _ in prod.refusals if c == "SOURCE-MISSING"],
                         ["ChimeraEngine/missing.bin"])

    def test_f2_deleted_after_production_fires_p_missing(self):
        root = build_demo(self.base / "vanish")
        manifest = produce_deps(root).manifest
        (root / "ChimeraEngine" / "gallery.py").unlink()
        result = run_preflight(root, manifest)
        self.assertEqual(result.verdict, FAIL)
        self.assertEqual([f.check for f in result.findings], ["P-MISSING"])
        self.assertEqual(result.findings[0].path, "ChimeraEngine/gallery.py")

    # ---- F3: undeclared development paths -----------------------------------
    def test_f3_devroot_string_fires_p_devroot(self):
        root = stage(self.base / "leaky", {"config/settings.txt": DEVROOT_CONFIG,
                                           "DEMO.bat": DEMO_BAT})
        rows = [{"path": "config/settings.txt", "role": "config", "text_config": True,
                 "decision_ref": "fixture-admission#settings"},
                {"path": "DEMO.bat", "role": "launcher", "text_config": True,
                 "decision_ref": "fixture-admission#demo-bat"}]
        prod = produce_manifest(root, admission(*rows), package_name="fixture",
                                declared_dependencies=DEPS)
        self.assertEqual(prod.verdict, PRODUCED, prod.refusals_json())
        entry = [e for e in prod.manifest["entries"]
                 if e["path"] == "config/settings.txt"][0]
        self.assertEqual(entry["sha256"], sha(DEVROOT_CONFIG),
                         "producer declares faithfully; content gating is the "
                         "checker's job, not the producer's")
        result = run_preflight(root, prod.manifest)
        self.assertEqual(result.verdict, FAIL)
        dev = [f for f in result.findings if f.check == "P-DEVROOT"]
        self.assertTrue(dev, result.findings_json())
        self.assertIn("e:/pythonchimera", dev[0].detail.lower())

    def test_f3_undeclared_staged_file_named_and_excluded(self):
        root = build_demo(self.base / "stray")
        (root / "gallery_out.log").write_bytes(b"dev run leftover\n")
        prod = produce_deps(root)
        self.assertEqual(prod.verdict, PRODUCED, prod.refusals_json())
        declared = {e["path"] for e in prod.manifest["entries"]}
        self.assertNotIn("gallery_out.log", declared)
        audit = audit_staging(root, prod.manifest)
        undeclared = [f.path for f in audit.findings if f.check == "STAGE-UNDECLARED"]
        self.assertEqual(undeclared, ["gallery_out.log"])

    # ---- F4: admission decisions explicit and external ----------------------
    def test_f4_missing_decision_ref_refuses(self):
        root = build_demo(self.base / "norefs")
        rows = demo_rows()
        rows[0] = {"path": "DEMO.bat", "role": "launcher", "text_config": True}
        prod = produce_manifest(root, admission(*rows), package_name="fixture")
        self.assertEqual(prod.verdict, REFUSED)
        self.assertIsNone(prod.manifest)
        self.assertEqual([c for c, _, _ in prod.refusals], ["ADMISSION-INCOMPLETE"])
        self.assertIn("decision_ref", prod.refusals[0][2])

    def test_f4_missing_source_refuses(self):
        root = build_demo(self.base / "nosrc")
        prod = produce_manifest(root, {"entries": demo_rows()},
                                package_name="fixture")
        self.assertEqual(prod.verdict, REFUSED)
        self.assertEqual([c for c, _, _ in prod.refusals], ["ADMISSION-MALFORMED"])

    def test_f4_entries_carry_external_admission_refs(self):
        manifest = produce_deps(build_demo(self.base / "refs")).manifest
        self.assertEqual(manifest["admission"]["source"], ADMISSION_SOURCE)
        for entry in manifest["entries"]:
            self.assertIn("role", entry)
            self.assertIn("admission_ref", entry)
            self.assertTrue(entry["admission_ref"].startswith("fixture-admission#"))

    def test_f4_no_permission_verdict_in_producer_vocabulary(self):
        """The producer may declare facts and refuse; it may never grade a
        distribution permission -- the only PASS/FAIL vocabulary in the system is
        the pinned checker's structural verdict."""
        vocab = {PRODUCED, REFUSED,
                 "ADMISSION-MALFORMED", "ADMISSION-INCOMPLETE", "PRODUCER-DUP",
                 "PRODUCER-PATH", "SOURCE-MISSING", "SOURCE-NOT-FILE",
                 "PRODUCER-OVERSIZE", "PRODUCER-TEXT", "PRODUCER-DEPS",
                 "PIN-MISMATCH",
                 "STAGE-UNDECLARED", "STAGE-MISSING", "STAGE-NOT-FILE"}
        source = (_HERE / "implementation.py").read_text(encoding="utf-8")
        literals = set(re.findall(r'"([A-Z][A-Z-]{2,})"', source))
        literals = {s for s in literals
                    if s in vocab or any(t in s for t in
                                         ("PREFLIGHT", "APPROVE", "LICENSE",
                                          "PERMIT", "PERMISSION", "RIGHT"))}
        self.assertEqual(literals, vocab,
                         "producer vocabulary drifted from the frozen set")
        for word in ("PREFLIGHT-PASS", "PREFLIGHT-FAIL", "APPROVED",
                     "LICENSED", "PERMISSION"):
            self.assertNotIn(word, vocab)
        self.assertEqual(set(PINNED.VERDICTS), {PASS, FAIL})

    # ---- F5: byte-pin discipline --------------------------------------------
    def test_f5_vendored_bytes_match_pin(self):
        data = (_HERE / "reference" / "package_preflight__e0a0abc8.py").read_bytes()
        self.assertEqual(len(data), 11458)
        self.assertEqual(hashlib.sha256(data).hexdigest(), REFERENCE_SHA256,
                         "vendored checker must stay byte-pinned to #153 e0a0abc8")

    def test_f5_tampered_copy_refused(self):
        good = (_HERE / "reference" / "package_preflight__e0a0abc8.py").read_bytes()
        scratch = self.base / "tampered.py"
        scratch.write_bytes(good.replace(b"P-MISSING", b"P-MISSINGX", 1))
        with self.assertRaises(AdapterRefusal) as ctx:
            load_pinned_preflight(scratch)
        self.assertEqual(ctx.exception.code, "PIN-MISMATCH")

    def test_f5_schema_verdicts_come_from_pinned_module(self):
        self.assertEqual(impl.SCHEMA, PINNED.SCHEMA)
        self.assertEqual(impl.SCHEMA, "chimera.package.manifest.v1")
        result = run_preflight(build_demo(self.base / "smoke"),
                               produce_deps(build_demo(self.base / "smoke2")).manifest)
        self.assertEqual(result.verdict, PASS, result.findings_json())
        self.assertIn(result.verdict, PINNED.VERDICTS)

    # ---- F6: exact admission --------------------------------------------------
    def test_f6_manifest_declares_exactly_admitted_set(self):
        root = stage(self.base / "extra", {
            "DEMO.bat": DEMO_BAT,
            "tools/run_demo.ps1": RUN_DEMO,
            "ChimeraEngine/gallery.py": GALLERY,
            "assets/unapproved_model.bin": b"unapproved asset bytes",
        })
        prod = produce_deps(root)
        self.assertEqual(prod.verdict, PRODUCED, prod.refusals_json())
        declared = sorted(e["path"] for e in prod.manifest["entries"])
        self.assertEqual(declared, sorted(["DEMO.bat", "ChimeraEngine/gallery.py",
                                           "tools/run_demo.ps1"]))
        audit = audit_staging(root, prod.manifest)
        self.assertEqual([f.path for f in audit.findings if f.check == "STAGE-UNDECLARED"],
                         ["assets/unapproved_model.bin"])
        self.assertEqual(audit.stats["files_seen"], 4)


class AdapterContractTests(unittest.TestCase):
    """Named refusal paths and the manifest contract (PREREGISTRATION.md section 3)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="s02_followup_contract_")
        self.base = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def produce_ok(self, name="pkg"):
        root = build_demo(self.base / name)
        prod = produce_deps(root)
        self.assertEqual(prod.verdict, PRODUCED, prod.refusals_json())
        return root, prod

    def test_producer_path_refusals(self):
        root = build_demo(self.base / "paths")
        for bad in ("E:/abs/x.txt", "../back.txt", "/abs/x.txt",
                    "//server/share/x", "safe/../escape.txt"):
            rows = demo_rows() + [{"path": bad, "role": "runtime",
                                   "decision_ref": "fixture-admission#bad"}]
            prod = produce_manifest(root, admission(*rows), package_name="fixture")
            self.assertEqual(prod.verdict, REFUSED, bad)
            self.assertEqual([c for c, _, _ in prod.refusals], ["PRODUCER-PATH"], bad)
            self.assertIsNone(prod.manifest)

    def test_producer_dup_refusal(self):
        root = build_demo(self.base / "dup")
        rows = demo_rows()
        rows.append(dict(rows[2]))
        prod = produce_manifest(root, admission(*rows), package_name="fixture")
        self.assertEqual([c for c, _, _ in prod.refusals], ["PRODUCER-DUP"])
        self.assertIsNone(prod.manifest)

    def test_producer_oversize_refusal(self):
        root = build_demo(self.base / "big")
        (root / "big.bin").write_bytes(b"\0" * 2048)
        rows = demo_rows() + [{"path": "big.bin", "role": "data",
                               "decision_ref": "fixture-admission#big"}]
        prod = produce_manifest(root, admission(*rows), package_name="fixture",
                                max_file_bytes=1024)
        self.assertEqual([c for c, _, _ in prod.refusals], ["PRODUCER-OVERSIZE"])
        self.assertIn("1024 B", prod.refusals[0][2])

    def test_producer_text_refusal(self):
        root = stage(self.base / "bin", {"DEMO.bat": DEMO_BAT,
                                         "config/blob.txt": b"\xff\xfe\x00"})
        rows = [{"path": "DEMO.bat", "role": "launcher", "text_config": True,
                 "decision_ref": "fixture-admission#demo-bat"},
                {"path": "config/blob.txt", "role": "config", "text_config": True,
                 "decision_ref": "fixture-admission#blob"}]
        prod = produce_manifest(root, admission(*rows), package_name="fixture")
        self.assertEqual([c for c, _, _ in prod.refusals], ["PRODUCER-TEXT"])

    def test_producer_deps_refusal_and_passthrough(self):
        root = build_demo(self.base / "deps")
        prod = produce_manifest(root, admission(*demo_rows()), package_name="fixture",
                                declared_dependencies={"modules": "numpy"})
        self.assertEqual([c for c, _, _ in prod.refusals], ["PRODUCER-DEPS"])
        root_default = build_demo(self.base / "deps_default")
        default = produce_manifest(root_default, admission(*demo_rows()),
                                   package_name="fixture")
        self.assertEqual(default.manifest["declared_dependencies"],
                         {"modules": [], "system": []})
        custom = produce_manifest(build_demo(self.base / "deps2"),
                                  admission(*demo_rows()), package_name="fixture",
                                  declared_dependencies={"modules": ["numpy"],
                                                         "system": ["powershell"]})
        self.assertEqual(custom.manifest["declared_dependencies"]["system"],
                         ["powershell"])

    def test_manifest_entries_carry_relative_paths_hashes_and_sizes(self):
        _, prod = self.produce_ok("contract")
        by_path = {e["path"]: e for e in prod.manifest["entries"]}
        self.assertEqual(by_path["DEMO.bat"]["sha256"], sha(DEMO_BAT))
        self.assertEqual(by_path["DEMO.bat"]["bytes"], len(DEMO_BAT))
        self.assertEqual(by_path["tools/run_demo.ps1"]["bytes"], len(RUN_DEMO))
        self.assertEqual(by_path["ChimeraEngine/gallery.py"]["sha256"], sha(GALLERY))
        for entry in prod.manifest["entries"]:
            self.assertNotIn("\\", entry["path"])
            self.assertNotIn(":", entry["path"])
            self.assertFalse(entry["path"].startswith("/"))
        raw = prod.canonical_json().decode("ascii")
        self.assertNotIn("\\", raw, "no backslash anywhere in canonical manifest")
        self.assertNotIn(self.base.name, raw,
                         "the package root's own name must not leak into the manifest")

    def test_audit_staging_missing_and_not_file(self):
        _, prod = self.produce_ok("audit")
        manifest = json.loads(json.dumps(prod.manifest))
        # a DECLARED entry absent from disk -> STAGE-MISSING;
        # a DECLARED path that exists but is a directory -> STAGE-NOT-FILE.
        manifest["entries"].append({"path": "ghost/missing.txt", "role": "data",
                                    "sha256": "0" * 64, "bytes": 1,
                                    "text_config": False,
                                    "admission_ref": "fixture-admission#ghost"})
        manifest["entries"].append({"path": "ghost", "role": "data",
                                    "sha256": "0" * 64, "bytes": 1,
                                    "text_config": False,
                                    "admission_ref": "fixture-admission#ghost-dir"})
        (self.base / "audit" / "ghost").mkdir()
        audit = audit_staging(self.base / "audit", manifest)
        checks = sorted((f.check, f.path) for f in audit.findings)
        self.assertEqual(checks, [("STAGE-MISSING", "ghost/missing.txt"),
                                  ("STAGE-NOT-FILE", "ghost")])

    def test_stats_and_canonical_form(self):
        _, prod = self.produce_ok("stats")
        self.assertEqual(prod.stats["entries_declared"], 3)
        self.assertEqual(prod.stats["bytes_hashed"],
                         len(DEMO_BAT) + len(RUN_DEMO) + len(GALLERY))
        self.assertTrue(prod.canonical_json().endswith(b"\n"))
        self.assertEqual(json.loads(prod.canonical_json()), prod.manifest)
        self.assertEqual(prod.manifest["schema"], PINNED.SCHEMA)
        self.assertIsInstance(prod.manifest["max_file_bytes"], int)

    def test_run_preflight_passes_dev_root_patterns_through(self):
        root = stage(self.base / "patterns", {"config/dev.txt": b"out = 'Z:/build'\n",
                                              "DEMO.bat": DEMO_BAT})
        rows = [{"path": "config/dev.txt", "role": "config", "text_config": True,
                 "decision_ref": "fixture-admission#dev"},
                {"path": "DEMO.bat", "role": "launcher", "text_config": True,
                 "decision_ref": "fixture-admission#demo-bat"}]
        prod = produce_manifest(root, admission(*rows), package_name="fixture",
                                declared_dependencies=DEPS,
                                extra_dev_root_patterns=("z:/build",))
        self.assertEqual(prod.manifest["dev_root_patterns"], ["z:/build"])
        result = run_preflight(root, prod.manifest)
        self.assertEqual(result.verdict, FAIL)
        dev = [f for f in result.findings if f.check == "P-DEVROOT"]
        self.assertEqual(len(dev), 1, result.findings_json())
        self.assertIn("z:/build", dev[0].detail)


if __name__ == "__main__":
    unittest.main()
