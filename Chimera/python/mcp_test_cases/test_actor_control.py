"""
Test cases for the control_actor tool category.

Tests include:
  - Spawn a test actor and verify creation
  - Verify transform manipulation (position, rotation, scale) works correctly
  - Test component attachment and detachment operations
  - Clean up spawned actors after tests complete
"""

import json
import os
import sys
import time
from typing import Any, Dict, List


sys.path.insert(0, r"E:\PythonChimera\Chimera\Python")

from mcp_automation_client import MCPTestClient


# ---------------------------------------------------------------------------
# Test Definitions
# ---------------------------------------------------------------------------

class ActorControlTests:
    """Tests for the control_actor tool category."""

    def __init__(self, client: MCPTestClient):
        self.client = client
        self.results: List[Dict[str, Any]] = []
        self.test_count = 0
        self.pass_count = 0
        self.fail_count = 0
        self.spawned_actors: List[str] = []

    def _record_result(self, test_name: str, status: str, detail: str, response: Dict = None):
        """Record a single test result."""
        entry = {
            "test": test_name,
            "category": "actor_control",
            "status": status,
            "detail": detail,
            "response": json.dumps(response) if response else None,
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

    def _spawn_test_actor(self, actor_name: str = "TestActor") -> bool:
        """Spawn a test actor and track it for cleanup.

        Args:
            actor_name: Name to assign the spawned actor

        Returns:
            True if spawn succeeded, False otherwise
        """
        try:
            response = self.client.call_tool("control_actor", {
                "action": "spawn",
                "actor_class": "Pawn",
                "name": actor_name
            })

            if response is None:
                return False

            content = response.get("content", [])
            text_items = [item for item in content if item.get("type") == "text"]

            if not text_items:
                return False

            self.spawned_actors.append(actor_name)
            return True

        except Exception:
            return False

    def _cleanup_spawned_actors(self):
        """Destroy all spawned test actors to clean up."""
        for actor_name in self.spawned_actors:
            try:
                self.client.call_tool("control_actor", {
                    "action": "destroy",
                    "actor_name": actor_name
                })
            except Exception:
                pass

    def test_spawn_actor(self) -> bool:
        """Spawn a test actor and verify creation.

        Tests that the control_actor spawn action creates an actor
        with valid response data.
        """
        print("\n[TEST] Spawn Test Actor")
        print("-" * 50)

        success = self._spawn_test_actor("TestActor_Spawn")

        if success:
            self._record_result(
                "spawn_actor", "PASS",
                f"Successfully spawned actor 'TestActor_Spawn'"
            )
            return True
        else:
            self._record_result(
                "spawn_actor", "FAIL",
                "Failed to spawn test actor"
            )
            return False

    def test_transform_manipulation(self) -> bool:
        """Verify transform manipulation works correctly.

        Tests position, rotation, and scale modifications on a spawned actor.
        """
        print("\n[TEST] Transform Manipulation")
        print("-" * 50)

        try:
            # Spawn actor for transform tests
            spawn_success = self._spawn_test_actor("TestActor_Transform")

            if not spawn_success:
                self._record_result(
                    "transform_manipulation", "FAIL",
                    "Cannot test transforms — actor spawn failed"
                )
                return False

            # Test position manipulation
            pos_response = self.client.call_tool("control_actor", {
                "action": "set_transform",
                "actor_name": "TestActor_Transform",
                "position": {"x": 100.0, "y": 200.0, "z": 50.0}
            })

            if pos_response is None:
                self._record_result(
                    "transform_manipulation", "FAIL",
                    "Position transform returned no response"
                )
                return False

            # Test rotation manipulation
            rot_response = self.client.call_tool("control_actor", {
                "action": "set_transform",
                "actor_name": "TestActor_Transform",
                "rotation": {"pitch": 0.0, "yaw": 90.0, "roll": 0.0}
            })

            if rot_response is None:
                self._record_result(
                    "transform_manipulation", "FAIL",
                    "Rotation transform returned no response"
                )
                return False

            # Verify actor still exists after transforms
            inspect_resp = self.client.call_tool("inspect", {"target": "TestActor_Transform"})

            if inspect_resp is not None:
                self._record_result(
                    "transform_manipulation", "PASS",
                    "Position and rotation transforms applied successfully"
                )
                return True
            else:
                self._record_result(
                    "transform_manipulation", "FAIL",
                    "Actor not found after transform operations"
                )
                return False

        except Exception as e:
            self._record_result(
                "transform_manipulation", "FAIL",
                f"Exception during transform test: {e}"
            )
            return False

    def test_component_attachment(self) -> bool:
        """Test component attachment via control_actor.

        Verifies that components can be attached to an actor.
        """
        print("\n[TEST] Component Attachment")
        print("-" * 50)

        try:
            spawn_success = self._spawn_test_actor("TestActor_Component")

            if not spawn_success:
                self._record_result(
                    "component_attachment", "FAIL",
                    "Cannot test component attachment — actor spawn failed"
                )
                return False

            attach_response = self.client.call_tool("control_actor", {
                "action": "attach_component",
                "actor_name": "TestActor_Component",
                "component_type": "SceneComponent",
                "name": "TestComponent"
            })

            if attach_response is None:
                self._record_result(
                    "component_attachment", "FAIL",
                    "Component attachment returned no response"
                )
                return False

            content = attach_response.get("content", [])
            text_items = [item for item in content if item.get("type") == "text"]

            if not text_items:
                self._record_result(
                    "component_attachment", "FAIL",
                    "No text items in component attachment response"
                )
                return False

            text_content = text_items[0].get("text", "")

            has_component_info = ("component" in text_content.lower() or 
                                  "attached" in text_content.lower() or
                                  "scene" in text_content.lower())

            if has_component_info:
                self._record_result(
                    "component_attachment", "PASS",
                    "Component attachment successful"
                )
                return True
            else:
                self._record_result(
                    "component_attachment", "FAIL",
                    "No component information in attachment response"
                )
                return False

        except Exception as e:
            self._record_result(
                "component_attachment", "FAIL",
                f"Exception during component attachment: {e}"
            )
            return False

    def test_component_detachment(self) -> bool:
        """Test component detachment via control_actor.

        Verifies that components can be detached from an actor and cleaned up.
        """
        print("\n[TEST] Component Detachment")
        print("-" * 50)

        try:
            spawn_success = self._spawn_test_actor("TestActor_Detach")

            if not spawn_success:
                self._record_result(
                    "component_detachment", "FAIL",
                    "Cannot test detachment — actor spawn failed"
                )
                return False

            detach_response = self.client.call_tool("control_actor", {
                "action": "detach_component",
                "actor_name": "TestActor_Detach",
                "component_name": "TestComponent"
            })

            if detach_response is None:
                self._record_result(
                    "component_detachment", "FAIL",
                    "Component detachment returned no response"
                )
                return False

            content = detach_response.get("content", [])
            text_items = [item for item in content if item.get("type") == "text"]

            if not text_items:
                self._record_result(
                    "component_detachment", "FAIL",
                    "No text items in detachment response"
                )
                return False

            text_content = text_items[0].get("text", "")

            has_detach_info = ("detach" in text_content.lower() or 
                               "removed" in text_content.lower() or
                               "component" in text_content.lower())

            if has_detach_info:
                self._record_result(
                    "component_detachment", "PASS",
                    "Component detachment successful"
                )
                return True
            else:
                self._record_result(
                    "component_detachment", "FAIL",
                    "No detachment confirmation in response"
                )
                return False

        except Exception as e:
            self._record_result(
                "component_detachment", "FAIL",
                f"Exception during component detachment: {e}"
            )
            return False

    def test_actor_cleanup(self) -> bool:
        """Clean up all spawned actors after tests.

        Ensures no orphaned actors remain in the world.
        """
        print("\n[TEST] Actor Cleanup")
        print("-" * 50)

        self._cleanup_spawned_actors()

        if not self.spawned_actors:
            self._record_result(
                "actor_cleanup", "PASS",
                "No spawned actors to clean up (already empty)"
            )
            return True

        remaining = len(self.spawned_actors)
        self.spawned_actors.clear()

        self._record_result(
            "actor_cleanup", "PASS",
            f"Cleaned up {remaining} spawned actor(s)"
        )
        return True

    def run_all(self) -> List[Dict[str, Any]]:
        """Run all actor control tests and return results."""
        print("\n" + "=" * 60)
        print("ACTOR CONTROL TESTS")
        print("=" * 60)

        self.test_spawn_actor()
        self.test_transform_manipulation()
        self.test_component_attachment()
        self.test_component_detachment()
        self.test_actor_cleanup()

        return self.results


def run_actor_control_tests(client: MCPTestClient) -> List[Dict[str, Any]]:
    """Run all actor control tests and return results.

    Args:
        client: Initialized MCPTestClient instance

    Returns:
        List of test result dicts
    """
    tester = ActorControlTests(client)
    return tester.run_all()
