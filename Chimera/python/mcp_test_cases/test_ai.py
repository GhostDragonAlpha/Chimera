"""Test cases for the AI tool category."""

import json
import os
import sys
import time
from typing import Any, Dict, List


sys.path.insert(0, r"E:\PythonChimera\Chimera\Python")

from mcp_automation_client import MCPTestClient


class AITests:

    def __init__(self, client: MCPTestClient):
        self.client = client
        self.results: List[Dict[str, Any]] = []
        self.test_count = 0
        self.pass_count = 0
        self.fail_count = 0

    def _record_result(self, test_name: str, status: str, detail: str, response: Dict = None):
        entry = {
            "test": test_name, "category": "ai", "status": status,
            "detail": detail, "response": json.dumps(response) if response else None,
            "timestamp": time.time()
        }
        self.results.append(entry)
        self.test_count += 1
        if status == "PASS":
            self.pass_count += 1
            icon = "[OK]"
        elif status == "FAIL":
            self.fail_count += 1
            icon = "[FAIL]"
        else:
            icon = "[SKIP]"
        print(f"  {icon} {test_name}: {detail}")

    def test_spawn_controllers(self) -> bool:
        print("\n[TEST] Spawn Controllers")
        try:
            response = self.client.call_tool("ai", {"action": "spawn_controller", "controller_type": "AI_Controller_Enemy", "name": "TestAIController"})
            if response is None:
                self._record_result("spawn_controllers", "FAIL", "No response from spawn_controller action")
                return False
            content = response.get("content", [])
            text_items = [item for item in content if item.get("type") == "text"]
            if not text_items:
                self._record_result("spawn_controllers", "FAIL", "No text items in spawn_controller response")
                return False
            text_content = text_items[0].get("text", "")
            has_controller_info = ("controller" in text_content.lower() or "ai" in text_content.lower() or "spawned" in text_content.lower())
            if has_controller_info:
                self._record_result("spawn_controllers", "PASS", f"AI controller spawned successfully ({len(text_content)} chars)")
                return True
            else:
                self._record_result("spawn_controllers", "FAIL", "No controller information in spawn response")
                return False
        except Exception as e:
            self._record_result("spawn_controllers", "FAIL", f"Exception during AI controller spawn: {e}")
            return False

    def test_set_behaviors(self) -> bool:
        print("\n[TEST] Set Behaviors")
        try:
            response = self.client.call_tool("ai", {"action": "set_behavior", "actor_name": "TestAIController", "behavior_type": "CombatBehavior", "parameters": {"aggression": 0.8, "detection_range": 50.0}})
            if response is None:
                self._record_result("set_behaviors", "FAIL", "No response from set_behavior action")
                return False
            content = response.get("content", [])
            text_items = [item for item in content if item.get("type") == "text"]
            if not text_items:
                self._record_result("set_behaviors", "FAIL", "No text items in set_behavior response")
                return False
            text_content = text_items[0].get("text", "")
            has_behavior_info = ("behavior" in text_content.lower() or "combat" in text_content.lower() or "aggression" in text_content.lower())
            if has_behavior_info:
                self._record_result("set_behaviors", "PASS", f"Behavior set successfully ({len(text_content)} chars)")
                return True
            else:
                self._record_result("set_behaviors", "FAIL", "No behavior information in response")
                return False
        except Exception as e:
            self._record_result("set_behaviors", "FAIL", f"Exception during behavior setting: {e}")
            return False

    def test_assign_patrol_routes(self) -> bool:
        print("\n[TEST] Assign Patrol Routes")
        try:
            response = self.client.call_tool("ai", {"action": "assign_patrol", "actor_name": "TestAIController", "route_points": [{"x": 0, "y": 0, "z": 0}, {"x": 100, "y": 0, "z": 0}, {"x": 100, "y": 100, "z": 0}], "looping": True})
            if response is None:
                self._record_result("assign_patrol_routes", "FAIL", "No response from assign_patrol action")
                return False
            content = response.get("content", [])
            text_items = [item for item in content if item.get("type") == "text"]
            if not text_items:
                self._record_result("assign_patrol_routes", "FAIL", "No text items in assign_patrol response")
                return False
            text_content = text_items[0].get("text", "")
            has_patrol_info = ("patrol" in text_content.lower() or "route" in text_content.lower() or "looping" in text_content.lower())
            if has_patrol_info:
                self._record_result("assign_patrol_routes", "PASS", f"Patrol route assigned successfully ({len(text_content)} chars)")
                return True
            else:
                self._record_result("assign_patrol_routes", "FAIL", "No patrol information in response")
                return False
        except Exception as e:
            self._record_result("assign_patrol_routes", "FAIL", f"Exception during patrol route assignment: {e}")
            return False

    def run_all(self) -> List[Dict[str, Any]]:
        print("\n" + "=" * 60)
        print("AI TESTS")
        self.test_spawn_controllers()
        self.test_set_behaviors()
        self.test_assign_patrol_routes()
        return self.results


def run_ai_tests(client: MCPTestClient) -> List[Dict[str, Any]]:
    tester = AITests(client)
    return tester.run_all()
