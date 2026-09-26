"""test_correction.py — I-S02-PACKAGE-PREFLIGHT correction tests (failing-first).

R1-R5 reproduce the lead's CHANGES-REQUIRED findings against the BASE module
(they FAIL there — the defect proof), and must PASS after the fix. Run
together with the prior suite: python -B -m unittest test_package_preflight
test_correction
"""
import hashlib
import json
import pathlib
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import package_preflight as pp  # noqa: E402

SCHEMA = pp.SCHEMA


def make_package(tmp, files: dict, **manifest_over) -> tuple[Path, dict]:
    root = Path(tmp)
    entries = []
    for rel, data in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        entries.append({"path": rel, "bytes": len(data),
                        "sha256": hashlib.sha256(data).hexdigest(),
                        "text_config": True})
    manifest = {"schema": SCHEMA, "max_file_bytes": 65536,
                "declared_dependencies": {"modules": [], "system": []},
                "entries": entries}
    manifest.update(manifest_over)
    return root, manifest


class R1LeadReproducer(unittest.TestCase):
    def test_multi_name_import_is_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, manifest = make_package(
                tmp, {"config.py": b"import os, missing_dependency\n"})
            result = pp.preflight(manifest, root)
            self.assertNotEqual(result.verdict, "PREFLIGHT-PASS",
                                 "defect: multi-name import passed undeclared")
            deps = [f for f in result.findings if f.check == "P-DEP"]
            self.assertTrue(any("missing_dependency" in f.detail
                                for f in deps), result.findings)


class R2AstShapes(unittest.TestCase):
    def test_aliases_multiple_and_from_imports(self):
        text = (b"import numpy as np\n"
                b"import os, json\n"
                b"from foo import bar\n"
                b"from foo.bar import baz as qux\n"
                b"from . import sibling\n")
        with tempfile.TemporaryDirectory() as tmp:
            root, manifest = make_package(tmp, {"m.py": text})
            manifest["declared_dependencies"]["modules"] = ["os", "json"]
            result = pp.preflight(manifest, root)
            deps = " | ".join(f.detail for f in result.findings
                              if f.check == "P-DEP")
            self.assertIn("numpy", deps)
            self.assertIn("foo", deps)          # both from-imports -> foo
            self.assertNotIn("sibling", deps)   # relative: package-internal
            self.assertNotIn("os", deps)
            self.assertNotIn("json", deps)

    def test_stdlib_and_declared_still_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, manifest = make_package(tmp, {"ok.py": b"import os\n"})
            result = pp.preflight(manifest, root)
            self.assertEqual(result.verdict, "PREFLIGHT-PASS", result.findings)


class R3ParseRefusal(unittest.TestCase):
    def test_unparseable_py_is_named_refusal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, manifest = make_package(tmp, {"bad.py": b"def broken(:\n"})
            result = pp.preflight(manifest, root)
            texts = [f for f in result.findings if f.check == "P-TEXT"]
            self.assertTrue(texts, "silent skip: unparseable .py yielded "
                                   "nothing")
            self.assertIn("parse", texts[0].detail.lower())


class R4InvalidCapNoIO(unittest.TestCase):
    def test_invalid_cap_fails_before_any_io(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, manifest = make_package(
                tmp, {"a.py": b"import os\n"}, max_file_bytes="big")
            result = pp.preflight(manifest, root)
            self.assertNotEqual(result.verdict, "PREFLIGHT-PASS")
            self.assertEqual(result.stats.get("paths_opened", []), [],
                             "defect: files opened despite invalid cap")
            self.assertEqual(result.stats.get("bytes_read", {}), {},
                             "defect: bytes read despite invalid cap")
            self.assertTrue(any(f.check == "P-MANIFEST" for f in result.findings))


class R5ReadTimeCaps(unittest.TestCase):
    def test_oversize_enforced_at_read_time(self):
        with tempfile.TemporaryDirectory() as tmp:
            big = b"x" * 100
            root, manifest = make_package(tmp, {"big.py": big},
                                          max_file_bytes=50)
            # declared bytes honest -> the stat size-match check cannot fire;
            # only read-time enforcement can produce the cap finding
            result = pp.preflight(manifest, root)
            sizes = [f for f in result.findings if f.check == "P-SIZE"
                     and "max_file_bytes" in f.detail]
            self.assertTrue(sizes, result.findings)
            self.assertLessEqual(result.stats["bytes_read"]["big.py"], 51)
            # no digest verified for the oversize file: no P-HASH even if the
            # declared hash is garbage
            with tempfile.TemporaryDirectory() as tmp2:
                root2, manifest2 = make_package(tmp2, {"big.py": big},
                                                max_file_bytes=50)
                for e in manifest2["entries"]:
                    e["sha256"] = "0" * 64
                r2 = pp.preflight(manifest2, root2)
                self.assertFalse([f for f in r2.findings if f.check == "P-HASH"])

    def test_bounded_read_never_exceeds_cap_plus_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, manifest = make_package(
                tmp, {"small.py": b"import os\n", "edge.py": b"y" * 50},
                max_file_bytes=50)
            result = pp.preflight(manifest, root)
            for rel, n in result.stats["bytes_read"].items():
                self.assertLessEqual(n, 51, (rel, n))


if __name__ == "__main__":
    unittest.main(verbosity=2)
