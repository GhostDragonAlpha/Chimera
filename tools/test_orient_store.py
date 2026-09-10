"""test_orient_store.py -- GLM-WF-01 R5 acceptance: orient must fail closed
when the per-checkout term store is absent or unreadable, and must never
mark synthetic output as recovered state.

STATEMENT: fail-closing tools/orient.py removes the silent-default hazard the
GLM-WF-01 record measured (F1: a store-less checkout exited 0 with a plausible
term tree).
PREDICTION:
  - default `orient.py` in a store-less checkout exits non-zero, prints the
    UNORIENTED marker, and prints NO plausible term tree;
  - `--allow-synthetic` (the explicit demo mode) exits 0 and labels the tree;
  - a corrupt store is reported as unreadable, not as recovered;
  - a store-present checkout orients with oriented:true and records store
    size + sha256 (R3).
FALSIFIER: any default invocation in a store-less checkout that exits 0 with a
plausible tree, or any corrupt-store invocation that marks oriented:true.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PY = sys.executable


def git(*args, cwd=REPO):
    return subprocess.run(["git", "-C", str(cwd), *args],
                          capture_output=True, text=True)


def run_orient(worktree: Path, *extra: str) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run([PY, str(worktree / "tools" / "orient.py"), *extra],
                          capture_output=True, text=True, env=env,
                          encoding="utf-8", errors="replace")


class OrientStoreTests(unittest.TestCase):
    """Uses a REAL linked worktree so the store-less checkout is genuine:
    uncommitted copies of the current orient.py + engine_state.py are dropped
    in as untracked files; the term store never exists there."""

    @classmethod
    def setUpClass(cls) -> None:
        head = git("rev-parse", "HEAD").stdout.strip()
        cls.head = head
        cls.tmp = Path(tempfile.mkdtemp(prefix="orient-store-test-"))
        cls.storeless = cls.tmp / "storeless"
        cp = git("worktree", "add", cls.storeless, head)
        if cp.returncode != 0:
            raise RuntimeError("worktree add failed: " + cp.stderr[-800:])
        shutil.copy2(REPO / "tools" / "orient.py", cls.storeless / "tools" / "orient.py")
        shutil.copy2(REPO / "ChimeraEngine" / "engine_state.py",
                     cls.storeless / "ChimeraEngine" / "engine_state.py")

    @classmethod
    def tearDownClass(cls) -> None:
        git("worktree", "remove", cls.storeless, "--force")
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_storeless_default_fails_closed(self):
        r = run_orient(self.storeless)
        self.assertNotEqual(r.returncode, 0, "store-less orient must exit non-zero")
        self.assertIn("UNORIENTED", r.stdout)
        self.assertNotIn("CURRENT TERM", r.stdout,
                         "a plausible term tree must not be printed as state")
        self.assertEqual((self.storeless / "ChimeraEngine" / "engine_state.json").exists(),
                         False)

    def test_storeless_allow_synthetic_explicit_mode(self):
        r = run_orient(self.storeless, "--allow-synthetic")
        self.assertEqual(r.returncode, 0, "--allow-synthetic is the explicit demo mode")
        self.assertIn("SYNTHETIC", r.stdout)
        self.assertIn("UNORIENTED", r.stdout)

    def test_storeless_json_labels_synthetic(self):
        r = run_orient(self.storeless, "--json")
        out = json.loads(r.stdout)
        self.assertIs(out["oriented"], False)
        self.assertIn("store", out)
        self.assertIs(out["store"]["exists"], False)
        self.assertIs(out["synthetic"], True)

    def test_corrupt_store_is_unreadable_not_recovered(self):
        corrupt = self.tmp / "corrupt"
        git("worktree", "add", corrupt, self.head)
        try:
            shutil.copy2(REPO / "tools" / "orient.py", corrupt / "tools" / "orient.py")
            shutil.copy2(REPO / "ChimeraEngine" / "engine_state.py",
                         corrupt / "ChimeraEngine" / "engine_state.py")
            (corrupt / "ChimeraEngine" / "engine_state.json").write_text(
                "{ this is not json", encoding="utf-8")
            r = run_orient(corrupt, "--json")
            self.assertNotEqual(r.returncode, 0, "corrupt store must fail closed")
            out = json.loads(r.stdout)
            self.assertIs(out["oriented"], False)
            self.assertIs(out["synthetic"], False)
            self.assertIn("unreadable", out["store"])
        finally:
            git("worktree", "remove", corrupt, "--force")

    def test_store_present_orients_with_r3_provenance(self):
        if not (REPO / "ChimeraEngine" / "engine_state.json").exists():
            self.skipTest("no authoritative store in this checkout")
        r = run_orient(REPO, "--json")
        self.assertEqual(r.returncode, 0)
        out = json.loads(r.stdout)
        self.assertIs(out["oriented"], True)
        self.assertIn("store", out)
        self.assertGreater(out["store"]["size_bytes"], 0)
        self.assertTrue(len(out["store"]["sha256"]) == 64)


if __name__ == "__main__":
    unittest.main()