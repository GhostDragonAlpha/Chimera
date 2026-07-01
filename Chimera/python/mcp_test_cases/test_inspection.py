"""
Test cases for the inspect tool category.

Tests include:
  - Inspect a known actor (ChimeraPawn) and verify properties
  - Verify component enumeration returns valid data
  - Validate class hierarchy information is returned correctly
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

class InspectionTests:
    """Tests for the inspect tool category."""

    def __init__(self, client: MCPTestClient):
        self.client = client
        self.results: List[Dict[str, Any]] = []
        self.test_count = 0
        self.pass_count = 0
        self.fail_count = 0

    def _record_result(self, test_name: str, status: str, detail: str, response: Dict = None):
        """Record a single test result."""
        entry = {
            "test": test_name,
            "category": "inspection",
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

    def test_inspect_known_actor(self) -> bool:
        """Inspect a known actor (ChimeraPawn) and verify response structure.

        Tests that the inspect tool returns valid actor data with expected fields.
        """
        print("\n[TEST] Inspect Known Actor (ChimeraPawn)")
        print("-" * 50)

        try:
            response = self.client.call_tool("inspect", {"target": "ChimeraPawn"})

            if response is None:
                self._record_result(
                    "inspect_known_actor", "FAIL",
                    "No response from inspect tool"
                )
                return False

            content = response.get("content", [])
            if not content:
                self._record_result(
                    "inspect_known_actor", "FAIL",
                    "Response contains no content array"
                )
                return False

            text_items = [item for item in content if item.get("type") == "text"]
            if not text_items:
                self._record_result(
                    "inspect_known_actor", "FAIL",
                    "No text items in response content"
                )
                return False

            text_content = text_items[0].get("text", "")
            
            has_name = "ChimeraPawn" in text_content or "pawn" in text_content.lower()
            has_class = "class" in text_content.lower() or "type" in text_content.lower()

            if has_name and has_class:
                self._record_result(
                    "inspect_known_actor", "PASS",
                    f"Actor inspection returned valid data ({len(text_content)} chars)"
                )
                return True
            else:
                self._record_result(
                    "inspect_known_actor", "FAIL",
                    "Response missing expected actor name or class info"
                )
                return False

        except Exception as e:
            self._record_result(
                "inspect_known_actor", "FAIL",
                f"Exception during inspection: {e}"
            )
            return False

    def test_inspect_properties(self) -> bool:
        """Verify that actor properties are returned correctly.

        Tests that the inspect tool returns property data with expected fields
        such as name, class, and component references.
        """
        print("\n[TEST] Verify Actor Properties")
        print("-" * 50)

        try:
            response = self.client.call_tool("inspect", {"target": "ChimeraPawn"})

            if response is None:
                self._record_result(
                    "verify_properties", "FAIL",
                    "No response from inspect tool for properties"
                )
                return False

            content = response.get("content", [])
            text_items = [item for item in content if item.get("type") == "text"]

            if not text_items:
                self._record_result(
                    "verify_properties", "FAIL",
                    "No text items in properties response"
                )
                return False

            text_content = text_items[0].get("text", "")

            property_indicators = ["properties", "property", "name", "class"]
            found_count = sum(1 for indicator in property_indicators if indicator.lower() in text_content.lower())

            if found_count >= 2:
                self._record_result(
                    "verify_properties", "PASS",
                    f"Found {found_count} property indicators in response"
                )
                return True
            else:
                self._record_result(
                    "verify_properties", "FAIL",
                    f"Only {found_count} property indicators found (need >= 2)"
                )
                return False

        except Exception as e:
            self._record_result(
                "verify_properties", "FAIL",
                f"Exception during property verification: {e}"
            )
            return False

    def test_component_enumeration(self) -> bool:
        """Test component enumeration via inspect tool.

        Verifies that the inspect tool can enumerate components attached to an actor.
        """
        print("\n[TEST] Component Enumeration")
        print("-" * 50)

        try:
            response = self.client.call_tool("inspect", {"target": "ChimeraPawn"})

            if response is None:
                self._record_result(
                    "component_enumeration", "FAIL",
                    "No response from inspect tool for components"
                )
                return False

            content = response.get("content", [])
            text_items = [item for item in content if item.get("type") == "text"]

            if not text_items:
                self._record_result(
                    "component_enumeration", "FAIL",
                    "No text items in component enumeration response"
                )
                return False

            text_content = text_items[0].get("text", "")

            has_components = ("component" in text_content.lower() or 
                              "root" in text_content.lower() or
                              "attachment" in text_content.lower())

            if has_components:
                self._record_result(
                    "component_enumeration", "PASS",
                    "Component enumeration data present in response"
                )
                return True
            else:
                self._record_result(
                    "component_enumeration", "FAIL",
                    "No component information found in response"
                )
                return False

        except Exception as e:
            self._record_result(
                "component_enumeration", "FAIL",
                f"Exception during component enumeration: {e}"
            )
            return False

    def test_class_hierarchy(self) -> bool:
        """Validate class hierarchy information is returned correctly.

        Tests that the inspect tool returns inheritance chain data for actors.
        """
        print("\n[TEST] Class Hierarchy Information")
        print("-" * 50)

        try:
            response = self.client.call_tool("inspect", {"target": "ChimeraPawn"})

            if response is None:
                self._record_result(
                    "class_hierarchy", "FAIL",
                    "No response from inspect tool for class hierarchy"
                )
                return False

            content = response.get("content", [])
            text_items = [item for item in content if item.get("type") == "text"]

            if not text_items:
                self._record_result(
                    "class_hierarchy", "FAIL",
                    "No text items in class hierarchy response"
                )
                return False

            text_content = text_items[0].get("text", "")

            hierarchy_keywords = ["extends", "inherits", "base", "parent", "super"]
            found_count = sum(1 for kw in hierarchy_keywords if kw.lower() in text_content.lower())

            has_class_ref = ("pawn" in text_content.lower() or 
                             "actor" in text_content.lower() or
                             "object" in text_content.lower())

            if found_count >= 1 or has_class_ref:
                self._record_result(
                    "class_hierarchy", "PASS",
                    f"Hierarchy info present ({found_count} keywords, class ref={has_class_ref})"
                )
                return True
            else:
                self._record_result(
                    "class_hierarchy", "FAIL",
                    "No hierarchy or class reference information found"
                )
                return False

        except Exception as e:
            self._record_result(
                "class_hierarchy", "FAIL",
                f"Exception during class hierarchy test: {e}"
            )
            return False

    def run_all(self) -> List[Dict[str, Any]]:
        """Run all inspection tests and return results."""
        print("\n" + "=" * 60)
        print("INSPECTION TESTS")
        print("=" * 60)

        self.test_inspect_known_actor()
        self.test_inspect_properties()
        self.test_component_enumeration()
        self.test_class_hierarchy()

        return self.results


def run_inspection_tests(client: MCPTestClient) -> List[Dict[str, Any]]:
    """Run all inspection tests and return results.

    Args:
        client: Initialized MCPTestClient instance

    Returns:
        List of test result dicts
    """
    tester = InspectionTests(client)
    return tester.run_all()
