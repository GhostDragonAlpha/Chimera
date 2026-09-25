"""test_package_preflight.py -- I-S02 preflight tests (all synthetic packages; CPU-only).

Each test builds its package under a TemporaryDirectory; no repository source is opened,
no network, no GPU. The three falsifiers from PREREGISTRATION.md:

  F1 relocation      -> test_relocation_invariance
  F2 undeclared dep  -> test_undeclared_import_fires / test_undeclared_system_tool_fires
  F3 permission      -> test_verdict_vocabulary_cannot_claim_distribution_permission
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from package_preflight import (SCHEMA, VERDICTS, Finding, PreflightResult,
                               _contained, preflight)

LAUNCHER = "@echo off\r\ntitle CHIMERA\r\npowershell -NoProfile -File run.ps1\r\n"
RUNNER = "# runner\nimport json\nimport numpy\nprint(json.dumps({'ok': 1}))\n"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def entry(rel: str, data: bytes, **extra):
    e = {"path": rel, "sha256": sha(data), "bytes": len(data)}
    e.update(extra)
    return e


def clean_manifest(launcher: bytes = LAUNCHER.encode(), runner: bytes = RUNNER.encode()):
    return {
        "schema": SCHEMA,
        "package_name": "chimera-slice",
        "max_file_bytes": 1048576,
        "declared_dependencies": {"python": "3.14.3", "modules": ["numpy"],
                                  "system": ["powershell"]},
        "entries": [
            entry("PlayableSlice.bat", launcher, role="launcher", text_config=True),
            entry("server/runner.py", runner, role="runtime", text_config=True),
        ],
    }


def build(root: Path, manifest: dict):
    root.mkdir(parents=True, exist_ok=True)
    for e in manifest["entries"]:
        rel = e["path"]
        if rel == "server/runner.py":
            data = RUNNER.encode()
        else:
            data = LAUNCHER.encode()
        target = root / Path(*rel.split("/"))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return root


class PreflightTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="s02_preflight_")
        self.base = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    # ---- F1: relocation invariance -----------------------------------------
    def test_relocation_invariance(self):
        manifest = clean_manifest()
        root_a = build(self.base / "a" / "deep" / "nest", manifest)
        result_a = preflight(json.loads(json.dumps(manifest)), root_a)
        self.assertEqual(result_a.verdict, "PREFLIGHT-PASS")
        self.assertEqual(result_a.findings, [])
        root_b = build(self.base / "b", manifest)
        result_b = preflight(json.loads(json.dumps(manifest)), root_b)
        self.assertEqual(result_b.verdict, "PREFLIGHT-PASS")
        # Identical package, different root: identical findings serialization.
        self.assertEqual(result_a.findings_json(), result_b.findings_json())

    def test_relocation_invariance_with_findings(self):
        """A broken package must break IDENTICALLY at both roots (no root in details)."""
        manifest = clean_manifest()
        manifest["entries"][1]["sha256"] = "0" * 64  # wrong hash
        root_a = build(self.base / "x1", manifest)
        root_b = build(self.base / "x2" / "deeper", manifest)
        ra = preflight(manifest, root_a)
        rb = preflight(manifest, root_b)
        self.assertEqual(ra.verdict, rb.verdict, "PREFLIGHT-FAIL")
        self.assertEqual(ra.findings_json(), rb.findings_json())

    # ---- named defect -> named finding -------------------------------------
    def test_missing_file_fires_p_missing(self):
        manifest = clean_manifest()
        build(self.base / "pkg", manifest)
        (self.base / "pkg" / "server" / "runner.py").unlink()
        r = preflight(manifest, self.base / "pkg")
        self.assertEqual([f.check for f in r.findings], ["P-MISSING"])
        self.assertEqual(r.findings[0].path, "server/runner.py")

    def test_wrong_hash_fires_p_hash(self):
        manifest = clean_manifest()
        build(self.base / "pkg", manifest)
        manifest["entries"][0]["sha256"] = "f" * 64
        r = preflight(manifest, self.base / "pkg")
        self.assertEqual([f.check for f in r.findings], ["P-HASH"])

    def test_size_mismatch_fires_p_size(self):
        manifest = clean_manifest()
        build(self.base / "pkg", manifest)
        manifest["entries"][0]["bytes"] = 1
        r = preflight(manifest, self.base / "pkg")
        self.assertEqual([f.check for f in r.findings], ["P-SIZE"])

    def test_oversize_is_bounded_read(self):
        big = b"A" * (1024 * 1024 + 5)  # 1 MiB + 5 B against a 64 KiB cap
        manifest = {
            "schema": SCHEMA, "max_file_bytes": 65536,
            "declared_dependencies": {"modules": [], "system": []},
            "entries": [entry("data/big.bin", big)],
        }
        root = build(self.base / "pkg", manifest)
        (root / "data" / "big.bin").write_bytes(big)
        r = preflight(manifest, root)
        self.assertEqual([f.check for f in r.findings], ["P-SIZE"])
        self.assertEqual(r.stats["bytes_read"]["data/big.bin"], 65536,
                         "hashing must read at most max_file_bytes")

    def test_traversal_entry_fires_p_path(self):
        manifest = clean_manifest()
        manifest["entries"].append(entry("../outside.txt", b"x"))
        build(self.base / "pkg", manifest)
        r = preflight(manifest, self.base / "pkg")
        self.assertIn("P-PATH", [f.check for f in r.findings])
        det = [f for f in r.findings if f.check == "P-PATH"][0]
        self.assertIn("traversal", det.detail)

    def test_absolute_and_unc_entries_fire_p_path(self):
        manifest = clean_manifest()
        build(self.base / "pkg", manifest)
        for bad in ("E:/PythonChimera/tools/x.py", "\\\\server\\share\\x", "/abs/x"):
            m = json.loads(json.dumps(manifest))
            m["entries"].append({"path": bad, "sha256": "0" * 64, "bytes": 1})
            r = preflight(m, self.base / "pkg")
            self.assertIn("P-PATH", [f.check for f in r.findings], bad)

    def test_junction_escape_logic(self):
        """P-JUNCTION core is containment of the RESOLVED path (pure-function check),
        then a LIVE NTFS junction: a clean relative entry whose path traverses a
        junction pointing outside the package root must fire P-JUNCTION. Windows
        junctions need no elevation; if the OS refuses, the pure coverage stands."""
        root = (self.base / "pkg").resolve()
        inside = root / "server" / "runner.py"
        outside = (self.base / "elsewhere").resolve()
        self.assertTrue(_contained(inside, root))
        self.assertFalse(_contained(outside, root))
        link_root = build(self.base / "linked", clean_manifest())
        target_dir = self.base / "outside_dir"
        target_dir.mkdir()
        (target_dir / "leak.txt").write_bytes(b"leak")
        junction = link_root / "data"
        import subprocess
        made = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(junction), str(target_dir.resolve())],
            capture_output=True, text=True)
        if made.returncode != 0:
            self.skipTest(f"OS refused a junction ({made.stderr.strip()}); "
                          "containment logic covered purely above")
        try:
            manifest = clean_manifest()
            manifest["entries"].append(entry("data/leak.txt", b"leak"))
            r = preflight(manifest, link_root)
            self.assertIn("P-JUNCTION", [f.check for f in r.findings])
            finding = [f for f in r.findings if f.check == "P-JUNCTION"][0]
            self.assertEqual(finding.path, "data/leak.txt")
            self.assertNotIn(str(link_root), finding.detail,
                             "finding details must stay relocation-invariant")
        finally:
            subprocess.run(["cmd", "/c", "rmdir", str(junction)], capture_output=True)

    # ---- F2: undeclared dependencies must not pass ---------------------------
    def test_undeclared_import_fires(self):
        manifest = clean_manifest()
        manifest["declared_dependencies"]["modules"] = []  # numpy no longer declared
        root = build(self.base / "pkg", manifest)
        r = preflight(manifest, root)
        checks = [f.check for f in r.findings]
        self.assertIn("P-DEP", checks)
        self.assertIn("numpy", [f.detail for f in r.findings if f.check == "P-DEP"][0])
        self.assertEqual(r.verdict, "PREFLIGHT-FAIL")

    def test_undeclared_system_tool_fires(self):
        manifest = clean_manifest()
        manifest["declared_dependencies"]["system"] = []  # powershell no longer declared
        root = build(self.base / "pkg", manifest)
        r = preflight(manifest, root)
        self.assertIn("P-EXT-TOOL", [f.check for f in r.findings])

    def test_stdlib_import_needs_no_declaration(self):
        runner = "import json\nimport os\n"
        manifest = clean_manifest(runner=runner.encode())
        manifest["declared_dependencies"]["modules"] = []
        root = build(self.base / "pkg", manifest)
        (root / "server" / "runner.py").write_bytes(runner.encode())
        r = preflight(manifest, root)
        self.assertEqual(r.findings, [])

    # ---- development-root leakage -------------------------------------------
    def test_dev_root_reference_fires(self):
        ps1 = "# start\nCopy-Item E:/PythonChimera/tools/x.py .\n"
        manifest = clean_manifest()
        manifest["entries"][0] = entry("run.ps1", ps1.encode(), text_config=True)
        manifest["declared_dependencies"]["system"] = []
        root = build(self.base / "pkg", manifest)
        (root / "run.ps1").write_bytes(ps1.encode())
        r = preflight(manifest, root)
        checks = [f.check for f in r.findings]
        self.assertIn("P-DEVROOT", checks)
        det = [f for f in r.findings if f.check == "P-DEVROOT"][0]
        self.assertIn("line 2", det.detail)

    def test_undecodable_text_config_fires_p_text(self):
        blob = b"\xff\xfe\x00not-utf8"
        manifest = clean_manifest()
        manifest["entries"].append(entry("cfg/bad.txt", blob, text_config=True))
        root = build(self.base / "pkg", manifest)
        (root / "cfg" / "bad.txt").write_bytes(blob)
        r = preflight(manifest, root)
        self.assertIn("P-TEXT", [f.check for f in r.findings])

    def test_duplicate_entry_fires_p_dup(self):
        manifest = clean_manifest()
        manifest["entries"].append(dict(manifest["entries"][0]))
        root = build(self.base / "pkg", manifest)
        r = preflight(manifest, root)
        self.assertIn("P-DUP", [f.check for f in r.findings])

    # ---- scope law: nothing outside the package root is touched --------------
    def test_no_paths_outside_root_opened(self):
        manifest = clean_manifest()
        root = build(self.base / "pkg", manifest)
        (self.base / "sentinel-outside.txt").write_bytes(b"do not touch")
        r = preflight(manifest, root)
        root_abs = str(root.resolve()).lower()
        for rel in r.stats["paths_opened"]:
            self.assertNotIn("..", rel)
            self.assertFalse(Path(rel).is_absolute(), rel)
        self.assertEqual(len(r.stats["paths_opened"]), 2)

    # ---- F3: no distribution-permission state can exist ----------------------
    def test_verdict_vocabulary_cannot_claim_distribution_permission(self):
        self.assertEqual(VERDICTS, ("PREFLIGHT-PASS", "PREFLIGHT-FAIL"))
        src = Path(__file__).with_name("package_preflight.py").read_text(encoding="utf-8")
        forbidden = ("distributable", "licensed", "cleared", "approved-for")
        for word in forbidden:
            self.assertNotIn(word, src.lower(), word)
        # "permission"/"distribution" may appear ONLY inside the module docstring's
        # OUT-OF-SCOPE disclaimer — never in code, identifiers or output literals.
        import package_preflight
        doc = package_preflight.__doc__ or ""
        lines = [ln.strip() for ln in src.splitlines()
                 if "permission" in ln.lower() or "distribution" in ln.lower()]
        self.assertTrue(lines, "disclaimer expected")
        for ln in lines:
            self.assertIn(ln, doc, ln)
        result = PreflightResult(VERDICTS[0])
        for attr in dir(result):
            self.assertNotIn("permission", attr.lower())
            self.assertNotIn("license", attr.lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
