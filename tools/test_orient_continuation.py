"""Regression tests for local-hierarchy continuation routing.

All state files are temporary. The tests call the real orient ``main`` and MCP
``next`` functions; no live controller, engine, or repository store is written.
"""
from __future__ import annotations

from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

from ChimeraEngine.engine_state import CONTINUATION_ACTION, Engine


CONTINUATION_KEYS = {
    "hierarchy_complete", "route", "authority", "action", "owner",
    "eligible_tasks",
}
EXPECTED_NORMALIZED_SOURCE_SHA256 = {
    "ChimeraEngine/engine_state.py": "c1a5f5781489b91488bcbf5777e822868f4d2c673da917d0af026c385596c01d",
    "ChimeraEngine/mcp_server.py": "d9944a0275ebea4687f665dc1b10d96d9ca13a9789c3645d56b5f6cb3483303c",
    "tools/orient.py": "3d899219c8cb277a8bc7be11bf53c9d10e2b31f569f0bca57a3368c127a01345",
}
REQUIRED_ACTION_FRAGMENTS = (
    "docs/AGENT_START.md",
    "current canonical Master/controller snapshot",
    "continue an owned milestone first",
    "only if approved capacity remains",
    "request an authenticated claim for an eligible READY task",
)


class ContinuationTests(unittest.TestCase):
    def test_imports_are_the_frozen_candidate_sources(self):
        import ChimeraEngine.engine_state as engine_state
        import ChimeraEngine.mcp_server as mcp_server
        import tools.orient as orient
        root = Path(__file__).resolve().parents[1]
        modules = {
            "ChimeraEngine/engine_state.py": engine_state,
            "ChimeraEngine/mcp_server.py": mcp_server,
            "tools/orient.py": orient,
        }
        for relative, module in modules.items():
            expected = (root / relative).resolve()
            actual = Path(module.__file__).resolve()
            self.assertEqual(actual, expected)
            normalized = actual.read_bytes().replace(b"\r\n", b"\n")
            self.assertEqual(hashlib.sha256(normalized).hexdigest(),
                             EXPECTED_NORMALIZED_SOURCE_SHA256[relative])
        engine_path = (root / "ChimeraEngine/engine_state.py").resolve()
        self.assertEqual(Path(sys.modules[orient.Engine.__module__].__file__).resolve(),
                         engine_path)
        self.assertEqual(Path(mcp_server.engine_state.__file__).resolve(), engine_path)

    def complete_store(self, path: Path) -> bytes:
        engine = Engine(path)
        for node in engine.state["hierarchy"].values():
            node["status"] = "decided"
        engine.state["current"] = engine.state["seed"]
        raw = json.dumps(engine.state, indent=2).encode("utf-8")
        path.write_bytes(raw)
        return raw

    def open_store(self, path: Path) -> bytes:
        engine = Engine(path)
        raw = json.dumps(engine.state, indent=2).encode("utf-8")
        path.write_bytes(raw)
        return raw

    def run_orient(self, store: Path, *arguments: str):
        import tools.orient as orient
        old_store, old_argv = orient.STORE, sys.argv
        try:
            orient.STORE = store
            sys.argv = ["orient.py", *arguments]
            output = io.StringIO()
            with redirect_stdout(output):
                code = orient.main()
            return code, output.getvalue()
        finally:
            orient.STORE, sys.argv = old_store, old_argv

    def assert_unclaimed(self, continuation: dict) -> None:
        self.assertEqual(set(continuation), CONTINUATION_KEYS)
        self.assertIsNone(continuation["owner"])
        self.assertIsNone(continuation["eligible_tasks"])

    def test_complete_engine_uses_canonical_owned_first_instruction(self):
        with tempfile.TemporaryDirectory() as directory:
            engine = Engine(Path(directory) / "state.json")
            for node in engine.state["hierarchy"].values():
                node["status"] = "decided"
            self.assertIsNone(engine.next_term())
            continuation = engine.continuation()
            self.assertTrue(continuation["hierarchy_complete"])
            self.assertEqual(continuation["route"], "canonical_master_controller")
            self.assertEqual(continuation["authority"], "controller_snapshot")
            self.assertEqual(continuation["action"], CONTINUATION_ACTION)
            for fragment in REQUIRED_ACTION_FRAGMENTS:
                self.assertIn(fragment, continuation["action"])
            self.assertIn(CONTINUATION_ACTION, engine.continuation_message())
            self.assertIn(CONTINUATION_ACTION, engine.next_action(None))
            self.assertIn(CONTINUATION_ACTION, engine.orient())
            self.assert_unclaimed(continuation)

    def test_open_engine_and_json_continue_the_exact_local_term_without_write(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            before = self.open_store(path)
            engine = Engine(path)
            expected = engine.next_term()
            self.assertIsNotNone(expected)
            continuation = engine.continuation()
            self.assertFalse(continuation["hierarchy_complete"])
            self.assertEqual(continuation["route"], "local_engine_hierarchy")
            self.assertEqual(continuation["authority"], "engine_state")
            self.assertEqual(continuation["action"],
                             f"continue local term `{expected}` and its gates")
            self.assertEqual(engine.next_action(None), continuation["action"])

            code, output = self.run_orient(path, "--json")
            data = json.loads(output)
            self.assertEqual(code, 0)
            self.assertEqual(data["next_term"], expected)
            self.assertEqual(data["continuation"], continuation)
            self.assertEqual(path.read_bytes(), before)
            self.assert_unclaimed(data["continuation"])

    def test_completed_cli_json_and_text_bind_same_store_and_do_not_write(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "complete.json"
            before = self.complete_store(path)
            expected_hash = hashlib.sha256(before).hexdigest()

            json_code, json_output = self.run_orient(path, "--json")
            data = json.loads(json_output)
            self.assertEqual(json_code, 0)
            self.assertIsNone(data["next_term"])
            self.assertTrue(data["continuation"]["hierarchy_complete"])
            self.assertEqual(data["continuation"]["action"], CONTINUATION_ACTION)
            self.assertEqual(data["store"]["path"], str(path))
            self.assertEqual(data["store"]["sha256"], expected_hash)
            self.assertEqual(path.read_bytes(), before)
            self.assert_unclaimed(data["continuation"])

            text_code, text_output = self.run_orient(path)
            self.assertEqual(text_code, 0)
            self.assertIn(CONTINUATION_ACTION, text_output)
            self.assertIn(str(path), text_output)
            self.assertIn(expected_hash[:12], text_output)
            self.assertEqual(path.read_bytes(), before)

    def test_missing_and_malformed_default_refuse_without_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing.json"
            code, output = self.run_orient(missing, "--json")
            data = json.loads(output)
            self.assertEqual(code, 3)
            self.assertFalse(data["oriented"])
            self.assertFalse(missing.exists())
            self.assert_unclaimed(data["continuation"])

            malformed = Path(directory) / "malformed.json"
            malformed.write_bytes(b"{not-json")
            before = malformed.read_bytes()
            code, output = self.run_orient(malformed, "--json")
            data = json.loads(output)
            self.assertEqual(code, 4)
            self.assertFalse(data["oriented"])
            self.assertIn("json decode failed", data["store"]["unreadable"])
            self.assertEqual(malformed.read_bytes(), before)
            self.assert_unclaimed(data["continuation"])

    def test_explicit_synthetic_is_labeled_unclaimed_and_does_not_create_store(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing.json"
            code, output = self.run_orient(missing, "--json", "--allow-synthetic")
            data = json.loads(output)
            self.assertEqual(code, 0)
            self.assertFalse(data["oriented"])
            self.assertTrue(data["synthetic"])
            self.assertFalse(missing.exists())
            self.assert_unclaimed(data["continuation"])

            code, output = self.run_orient(missing, "--allow-synthetic")
            self.assertEqual(code, 0)
            self.assertIn("SYNTHETIC/uninitialized engine", output)
            self.assertIn("NEXT MOVE -> term", output)
            self.assertNotIn("LOCAL HIERARCHY COMPLETE", output)
            self.assertFalse(missing.exists())

    def test_real_mcp_next_completed_does_not_save(self):
        import ChimeraEngine.mcp_server as server
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "complete.json"
            before = self.complete_store(path)
            engine = Engine(path)
            old_engine = server.ENG
            try:
                server.ENG = engine
                with mock.patch.object(engine, "_save", wraps=engine._save) as save:
                    result = server.next()
                    save.assert_not_called()
                self.assertIn(CONTINUATION_ACTION, result)
                self.assertEqual(path.read_bytes(), before)
            finally:
                server.ENG = old_engine

    def test_real_mcp_next_open_sets_current_and_saves_once(self):
        import ChimeraEngine.mcp_server as server
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "open.json"
            before = self.open_store(path)
            engine = Engine(path)
            expected = engine.next_term()
            old_engine = server.ENG
            try:
                server.ENG = engine
                with mock.patch.object(engine, "_save", wraps=engine._save) as save:
                    result = server.next()
                    save.assert_called_once_with()
                self.assertIn(f"NEXT TERM: `{expected}`", result)
                self.assertEqual(engine.state["current"], expected)
                self.assertEqual(Engine(path).state["current"], expected)
                self.assertNotEqual(path.read_bytes(), before)
            finally:
                server.ENG = old_engine

    def test_onboarding_is_strict_utf8_and_names_canonical_entry(self):
        root = Path(__file__).resolve().parents[1]
        text = (root / "ChimeraEngine" / "ONBOARDING.md").read_bytes().decode("utf-8")
        first_lines = "\n".join(text.splitlines()[:12])
        self.assertIn("docs/AGENT_START.md", first_lines)
        self.assertIn("owned milestones first", first_lines)
        self.assertIn("Only if approved capacity remains", first_lines)
        self.assertNotIn("\ufffd", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
