"""Regression tests for local-hierarchy continuation routing."""
import copy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

from ChimeraEngine.engine_state import Engine

class ContinuationTests(unittest.TestCase):
    def test_complete_engine_routes_without_fabricating_owner(self):
        with tempfile.TemporaryDirectory() as td:
            e=Engine(Path(td)/"state.json")
            for node in e.state["hierarchy"].values(): node["status"]="decided"
            e.state["current"]=e.state["seed"]
            self.assertIsNone(e.next_term())
            c=e.continuation()
            self.assertTrue(c["hierarchy_complete"])
            self.assertEqual(c["route"],"canonical_master_controller")
            self.assertIsNone(c["owner"])
            self.assertIn("does not end the project",e.next_action(None))
            self.assertIn("canonical Master/controller",e.orient())

    def test_orient_json_storeless_has_explicit_route(self):
        import tools.orient as orient
        old_store=orient.STORE
        try:
            with tempfile.TemporaryDirectory() as td:
                orient.STORE=Path(td)/"missing.json"
                old_argv=sys.argv; sys.argv=["orient.py","--json"]
                out=io.StringIO()
                with redirect_stdout(out): self.assertEqual(orient.main(),3)
                data=json.loads(out.getvalue())
                self.assertFalse(data["oriented"])
                self.assertEqual(data["continuation"]["route"],"canonical_master_controller")
                self.assertIsNone(data["continuation"]["owner"])
        finally:
            orient.STORE=old_store
            sys.argv=old_argv

    def test_open_engine_does_not_claim_controller_eligibility(self):
        with tempfile.TemporaryDirectory() as td:
            e=Engine(Path(td)/"state.json")
            c=e.continuation()
            self.assertIsNone(c["eligible_tasks"])
            self.assertEqual(c["authority"],"controller_snapshot")

    def test_mcp_next_uses_engine_continuation_surface(self):
        import ChimeraEngine.mcp_server as server
        class Completed:
            def next_term(self): return None
            def continuation_message(self): return "LOCAL HIERARCHY COMPLETE; CONTINUE via canonical Master/controller"
        old=server.ENG
        try:
            server.ENG=Completed()
            self.assertIn("CONTINUE via canonical Master/controller",server.next())
        finally:
            server.ENG=old

if __name__ == "__main__": unittest.main()
