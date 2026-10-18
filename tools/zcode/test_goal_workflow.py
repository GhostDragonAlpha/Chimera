"""Focused tests for purpose propagation, lead freedom and compact instruction loading."""
import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent

class WorkflowTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location("purpose_hook", HERE / "role_gate.py")
        self.hook = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.hook)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.hook.STATE = Path(self.temp.name) / "sessions"
    def event(self, kind, sid="parent", **more):
        return self.hook.respond(dict(hook_event_name=kind,session_id=sid,**more))
    def test_startup_and_active_session_migration(self):
        r=self.event("SessionStart")
        self.assertIn("playable matter-simulator game",r["additionalContext"])
        self.assertIn("recursively improve",r["additionalContext"])
        self.assertEqual(self.event("PreToolUse",tool_name="Read",tool_input={}),{})
        fresh=self.event("PreToolUse",sid="existing",tool_name="Read",tool_input={})
        self.assertIn("purpose",fresh["additionalContext"])
    def test_any_available_profile_gets_purpose_without_changing_task(self):
        for profile in ["chimera-worker","chimera-maya","chimera-step37","chimera-researcher","general-purpose"]:
            args={"subagent_type":profile,"description":"Restore a build","prompt":"Why: retry the same construction without losing it. Fix restore.","run_in_background":False}
            r=self.event("PreToolUse",tool_name="Agent",tool_input=args)
            updated=r["hookSpecificOutput"]["updatedInput"]
            self.assertEqual(updated["subagent_type"],profile)
            self.assertTrue(updated["prompt"].endswith(args["prompt"]))
            self.assertIn("decision",updated["prompt"])
            self.assertIn("compression",updated["prompt"])
            again=self.event("PreToolUse",tool_name="Agent",tool_input=updated)
            self.assertNotIn("updatedInput",again.get("hookSpecificOutput",{}))
    def test_followup_keeps_target_and_purpose(self):
        args={"to":"agent_abc","message":"Keep the current task. Diagnose the restore failure."}
        r=self.event("PreToolUse",tool_name="SendMessage",tool_input=args)
        updated=r["hookSpecificOutput"]["updatedInput"]
        self.assertEqual(updated["to"],args["to"])
        self.assertTrue(updated["message"].endswith(args["message"]))
    def test_lead_can_research_implement_and_use_available_tools(self):
        self.event("SessionStart")
        for tool in ["WebSearch","WebFetch","Edit","Bash","js","Browser","GoalUpdate","ReadSessionContext"]:
            self.assertEqual(self.event("PreToolUse",tool_name=tool,tool_input={}),{})
    def test_readonly_researcher_and_no_nested_delegation_survive_resume(self):
        self.event("SessionStart",sid="research",agent_type="chimera-researcher")
        self.assertEqual(self.event("PreToolUse",sid="research",tool_name="WebSearch",tool_input={}),{})
        r=self.event("PreToolUse",sid="research",tool_name="Bash",tool_input={"agent_type":"main"})
        self.assertEqual(r["hookSpecificOutput"]["permissionDecision"],"deny")
        self.event("SessionStart",sid="worker",agent_type="chimera-maya")
        r=self.event("PreToolUse",sid="worker",tool_name="Agent",tool_input={})
        self.assertEqual(r["hookSpecificOutput"]["permissionDecision"],"deny")
    def test_native_goal_continuation_without_extra_stop_marker(self):
        self.event("SessionStart")
        self.assertEqual(self.event("Stop",responseText="The task is done."),{})
    def test_gpu_foreground_policy(self):
        r=self.event("PreToolUse",tool_name="Agent",tool_input={"run_in_background":True})
        self.assertEqual(r["hookSpecificOutput"]["permissionDecision"],"deny")
    def test_child_result_reminder_does_not_force_review(self):
        self.event("SessionStart")
        r=self.event("PostToolUse",tool_name="Agent",tool_input={})
        self.assertIn("no automatic review round",r["additionalContext"])
        self.assertNotIn("decision",r.get("hookSpecificOutput",{}))

if __name__ == "__main__":
    unittest.main(verbosity=2)
