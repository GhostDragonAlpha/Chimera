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
        self.assertIn("game that uses simulated matter",r["additionalContext"])
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
    def test_step_is_readonly_including_after_resume(self):
        self.event("SessionStart",sid="step",agent_type="chimera-step37")
        for tool in sorted(self.hook.RESEARCH_TOOLS):
            self.assertEqual(self.event("PreToolUse",sid="step",tool_name=tool,tool_input={}),{})
        for tool in ["Write","Edit","Bash","NotebookEdit","TodoWrite","js","js_reset",
                     "js_add_node_module_dir","Agent","Task","mcp__custom__mutate"]:
            result=self.event("PreToolUse",sid="step",tool_name=tool,tool_input={"agent_type":"main"})
            self.assertEqual(result["hookSpecificOutput"]["permissionDecision"],"deny",tool)
            self.assertIn("read-only",result["hookSpecificOutput"]["permissionDecisionReason"])
        resumed=self.event("SessionStart",sid="step")
        self.assertIn("strictly a read-only",resumed["additionalContext"])
        self.assertEqual(self.event("PreToolUse",sid="step",tool_name="Edit",tool_input={})
                         ["hookSpecificOutput"]["permissionDecision"],"deny")
    def test_existing_step_gets_new_policy_without_restricting_maya(self):
        self.event("SessionStart",sid="step-old",agent_type="chimera-step37")
        path,state=self.hook._load({"session_id":"step-old"})
        state["purpose_version"]="playable-purpose-20261018-v1"
        self.hook._save(path,state)
        result=self.event("PreToolUse",sid="step-old",tool_name="Write",tool_input={})
        self.assertIn("Step is strictly",result["additionalContext"])
        self.assertEqual(result["hookSpecificOutput"]["permissionDecision"],"deny")
        self.event("SessionStart",sid="maya",agent_type="chimera-maya")
        for tool in ["Write","Edit","Bash","js"]:
            self.assertEqual(self.event("PreToolUse",sid="maya",tool_name=tool,tool_input={}),{})
    def test_native_step_resume_model_restores_missing_role(self):
        self.event("SessionStart",sid="sess_subagent_old",model="chimera-step37/step-3.7-flash-iq4_xs")
        for tool in ["Write","Edit","Bash","js"]:
            result=self.event("PreToolUse",sid="sess_subagent_old",tool_name=tool,tool_input={})
            self.assertEqual(result["hookSpecificOutput"]["permissionDecision"],"deny")
        self.event("SessionStart",sid="lead-native",model="chimera-strata-q4km/qwen3.8-flash-next-agention-ap-q4_k_m")
        self.assertEqual(self.event("PreToolUse",sid="lead-native",tool_name="Edit",tool_input={}),{})
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

    def test_blender_mandate_migrates_existing_session_once_without_reset(self):
        self.event("SessionStart",sid="active-lead")
        path,state=self.hook._load({"session_id":"active-lead"})
        state.update(purpose_version="playable-purpose-20261021-v7-roles-and-reports",
                     retained_report="accepted existing report")
        self.hook._save(path,state)
        changed=self.event("PreToolUse",sid="active-lead",tool_name="Bash",
                           tool_input={"command":"run the scoped native dependency check"})
        self.assertIn("Blender is mandatory",changed["additionalContext"])
        self.assertNotIn("permissionDecision",changed.get("hookSpecificOutput",{}))
        _,state=self.hook._load({"session_id":"active-lead"})
        self.assertEqual(state["retained_report"],"accepted existing report")
        self.assertEqual(self.event("PreToolUse",sid="active-lead",tool_name="Read",tool_input={}),{})
    def test_blender_path_reaches_child_and_same_child_followup(self):
        args={"subagent_type":"chimera-maya","prompt":"Fix native loading for the Blender seam."}
        child=self.event("PreToolUse",tool_name="Agent",tool_input=args)["hookSpecificOutput"]["updatedInput"]
        self.assertIn("Mandatory delivery: Blender",child["prompt"])
        self.assertTrue(child["prompt"].endswith(args["prompt"]))
        follow={"to":"agent_existing","message":"Resume the same result; retain the saved construction."}
        resumed=self.event("PreToolUse",tool_name="SendMessage",tool_input=follow)["hookSpecificOutput"]["updatedInput"]
        self.assertEqual(resumed["to"],"agent_existing")
        self.assertIn("Mandatory delivery: Blender",resumed["message"])
        self.assertTrue(resumed["message"].endswith(follow["message"]))

    def test_all_child_identities_deny_delegation_and_keep_reports(self):
        identities=[{"agent_type":"Explore"},{"agent_type":"general-purpose"},
                    {"agentName":"zcode-any-custom-profile"},{"runtimeScope":"subagent"},
                    {"taskType":"workflow_child"},{"taskType":"nested_workflow_child"}]
        for i,identity in enumerate(identities):
            sid="builtin-child-"+str(i)
            self.event("SessionStart",sid=sid,**identity)
            for name in self.hook.DELEGATION:
                result=self.event("PreToolUse",sid=sid,tool_name=name,
                                  tool_input={"agent_type":"main","subagent_type":"Explore"})
                self.assertEqual(result["hookSpecificOutput"]["permissionDecision"],"deny",(identity,name))
            self.assertEqual(self.event("PreToolUse",sid=sid,tool_name="Read",tool_input={}),{})
            self.assertEqual(self.event("PreToolUse",sid=sid,tool_name="RespondToCoordinator",tool_input={}),{})
            self.event("SessionStart",sid=sid)
            self.assertEqual(self.event("PreToolUse",sid=sid,tool_name="SendMessage",tool_input={})
                             ["hookSpecificOutput"]["permissionDecision"],"deny")

    def test_reserved_child_id_and_parent_tool_arguments_do_not_confuse_caller(self):
        result=self.event("PreToolUse",sid="sess_subagent_existing",tool_name="Task",
                          tool_input={"agent_type":"main"})
        self.assertEqual(result["hookSpecificOutput"]["permissionDecision"],"deny")
        result=self.event("PreToolUse",sid="real-lead",tool_name="Agent",
                          tool_input={"agent_type":"Explore","prompt":"Find the existing owner."})
        self.assertNotIn("permissionDecision",result["hookSpecificOutput"])
        self.assertIn("updatedInput",result["hookSpecificOutput"])

if __name__ == "__main__":
    unittest.main(verbosity=2)
