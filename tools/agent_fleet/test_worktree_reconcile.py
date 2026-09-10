import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import worktree_reconcile as wr


class WorktreeReconcileTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()
        self.git("init", "-q")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "user.name", "reconcile-test")
        (self.repo / "tools").mkdir()
        (self.repo / "docs" / "evidence" / "agent_fleet").mkdir(parents=True)
        (self.repo / "tools" / "owned.py").write_text("base\n", encoding="utf-8")
        (self.repo / "docs" / "evidence" / "agent_fleet" / "HEAD_RECONCILE").mkdir()
        (self.repo / "docs" / "evidence" / "agent_fleet" / "HEAD_RECONCILE" / "old.txt").write_text("old\n", encoding="utf-8")
        self.git("add", "."); self.git("commit", "-qm", "base")
        self.expected = self.git("rev-parse", "HEAD").stdout.strip()

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.repo), *args], check=True,
                              capture_output=True, text=True, encoding="utf-8")

    def run_inspect(self):
        return wr.inspect(self.repo, self.expected, ["tools"],
                          "docs/evidence/agent_fleet/HEAD_RECONCILE")

    def test_clean_and_evidence_addition_are_read_only(self):
        self.assertTrue(self.run_inspect()["ok"])
        evidence = self.repo / "docs/evidence/agent_fleet/HEAD_RECONCILE" / "attempt.json"
        evidence.parent.mkdir(parents=True, exist_ok=True)
        evidence.write_text('{"failed": true}\n', encoding="utf-8")
        before = evidence.read_bytes()
        result = self.run_inspect()
        self.assertTrue(result["ok"])
        self.assertIn("evidence_only_added", result["classification"])
        self.assertEqual(before, evidence.read_bytes())
        self.assertIn("attempt.json", self.git("status", "--porcelain", "--ignored").stdout)

    def test_fast_forward_evidence_commit_continues(self):
        evidence = self.repo / "docs/evidence/agent_fleet/HEAD_RECONCILE/résumé run 1.json"
        evidence.write_text('{"attempt": "preserved"}\n', encoding="utf-8")
        self.git("add", str(evidence)); self.git("commit", "-qm", "record evidence")
        staged = self.repo / "docs/evidence/agent_fleet/HEAD_RECONCILE/résumé run 2.json"
        staged.write_text('{"attempt": "staged"}\n', encoding="utf-8")
        self.git("add", str(staged))
        index_before = (self.repo / ".git" / "index").read_bytes()
        files_before = {p: p.read_bytes() for p in (evidence, staged)}
        (self.repo / "Saved").mkdir()
        (self.repo / "Saved" / "foreign.log").write_text("keep\n", encoding="utf-8")
        result = self.run_inspect()
        self.assertTrue(result["ok"])
        self.assertIn("evidence_only_added", result["classification"])
        self.assertIn("head_advanced", result["classification"])
        self.assertIn("preserved_untracked_outside_scope", result["classification"])
        self.assertEqual(index_before, (self.repo / ".git" / "index").read_bytes())
        self.assertEqual(files_before, {p: p.read_bytes() for p in (evidence, staged)})

    def test_changed_index_during_read_is_unstable(self):
        def mutate():
            p = self.repo / "tools" / "late.py"
            p.write_text("late\n", encoding="utf-8")
            self.git("add", str(p))
        result = wr.inspect(self.repo, self.expected, ["tools"],
                            "docs/evidence/agent_fleet/HEAD_RECONCILE",
                            _between_reads=mutate)
        self.assertFalse(result["ok"])
        self.assertFalse(result["stable"])
        self.assertIn("unstable_read", result["classification"])

    def test_unreadable_index_fails_closed(self):
        original = wr._index_fingerprint
        try:
            wr._index_fingerprint = lambda repo: None
            result = self.run_inspect()
        finally:
            wr._index_fingerprint = original
        self.assertFalse(result["ok"])
        self.assertIn("index_unreadable", result["errors"])

    def test_filesystem_root_is_rejected_before_git(self):
        original = wr._git
        try:
            def unexpected(*args):
                raise AssertionError("Git must not be invoked for a drive root")
            wr._git = unexpected
            result = wr.inspect(Path(self.repo.anchor), self.expected, ["tools"],
                                "docs/evidence/agent_fleet/HEAD_RECONCILE")
        finally:
            wr._git = original
        self.assertIn("filesystem_root_is_not_a_checkout", result["errors"])

    def test_ignored_cache_is_preserved_without_blocking(self):
        # Git-ignored build/cache files are reported, not certified as inputs.
        self.git("config", "core.excludesfile", str(self.repo / ".git" / "test-ignore"))
        (self.repo / ".git" / "test-ignore").write_text("__pycache__/\n", encoding="utf-8")
        cache = self.repo / "tools" / "__pycache__" / "owned.pyc"
        cache.parent.mkdir()
        cache.write_bytes(b"preserve cached data")
        result = self.run_inspect()
        self.assertTrue(result["ok"])
        self.assertIn("preserved_ignored", result["classification"])
        self.assertEqual(cache.read_bytes(), b"preserve cached data")

    def test_staged_new_source_requires_revalidation(self):
        source = self.repo / "tools" / "new.py"
        source.write_text("new\n", encoding="utf-8")
        self.git("add", str(source))
        result = self.run_inspect()
        self.assertFalse(result["ok"])
        self.assertIn("source_changed_requires_revalidation", result["classification"])
        self.assertEqual(source.read_text(encoding="utf-8"), "new\n")

    def test_historical_modify_and_delete_are_distinct(self):
        old = self.repo / "docs/evidence/agent_fleet/HEAD_RECONCILE/old.txt"
        old.write_text("changed\n", encoding="utf-8")
        result = self.run_inspect()
        self.assertIn("historical_evidence_modified", result["classification"])
        old.unlink()
        result = self.run_inspect()
        self.assertIn("historical_evidence_deleted", result["classification"])

    def test_outside_scope_and_divergent_head(self):
        outside = self.repo / "README.md"
        outside.write_text("base\n", encoding="utf-8")
        self.git("add", str(outside)); self.git("commit", "-qm", "readme")
        outside.write_text("changed\n", encoding="utf-8")
        result = self.run_inspect()
        self.assertIn("outside_task_scope", result["classification"])
        self.git("checkout", "--orphan", "divergent")
        for child in self.repo.iterdir():
            if child.name != ".git":
                if child.is_dir():
                    import shutil; shutil.rmtree(child)
                else:
                    child.unlink()
        outside.write_text("divergent\n", encoding="utf-8")
        self.git("add", str(outside)); self.git("commit", "-qm", "divergent")
        result = wr.inspect(self.repo, self.expected, ["tools"], "docs/evidence/agent_fleet/HEAD_RECONCILE")
        self.assertFalse(result["ok"])
        self.assertIn("divergent_head", result["classification"])

    def test_unsafe_arguments_and_symlink_escape_refuse(self):
        result = wr.inspect(self.repo, self.expected, ["../outside"], "docs/evidence/agent_fleet/HEAD_RECONCILE")
        self.assertIn("invalid_path_argument", result["classification"])
        link = self.repo / "tools" / "escape"
        target = Path(self.tmp.name) / "outside.txt"
        target.write_text("outside\n", encoding="utf-8")
        try:
            os.symlink(target, link)
        except (OSError, NotImplementedError):
            self.skipTest("symlink creation unavailable")
        result = self.run_inspect()
        self.assertIn("path_escape", result["classification"])


if __name__ == "__main__":
    unittest.main()
