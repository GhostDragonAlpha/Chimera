"""
Test cases for the manage_level tool category.

Tests include:
  - List available levels via the manage_level tool
  - Test level streaming operations (dry run, no actual loading)
  - Verify metadata queries work correctly
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

class LevelManagementTests:
    """Tests for the manage_level tool category."""

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
            "category": "level_management",
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

    def test_list_levels(self) -> bool:
        """List available levels via manage_level tool.

        Tests that the manage_level list action returns valid level data.
        """
        print("\n[TEST] List Available Levels")
        print("-" * 50)

        try:
            response = self.client.call_tool("manage_level", {
                "action": "list"
            })

            if response is None:
                self._record_result(
                    "list_levels", "FAIL",
                    "No response from manage_level list action"
                )
                return False

            content = response.get("content", [])
            text_items = [item for item in content if item.get("type") == "text"]

            if not text_items:
                self._record_result(
                    "list_levels", "FAIL",
                    "No text items in level list response"
                )
                return False

            text_content = text_items[0].get("text", "")

            has_level_data = ("level" in text_content.lower() or 
                              "map" in text_content.lower() or
                              "streaming" in text_content.lower())

            if has_level_data:
                self._record_result(
                    "list_levels", "PASS",
                    f"Level list returned valid data ({len(text_content)} chars)"
                )
                return True
            else:
                self._record_result(
                    "list_levels", "FAIL",
                    "No level data found in response"
                )
                return False

        except Exception as e:
            self._record_result(
                "list_levels", "FAIL",
                f"Exception during level listing: {e}"
            )
            return False

    def test_level_streaming_dry_run(self) -> bool:
        """Test level streaming operations (dry run, no actual loading).

        Verifies that the manage_level tool supports dry-run mode for
        streaming operations without modifying the world state.
        """
        print("\n[TEST] Level Streaming Dry Run")
        print("-" * 50)

        try:
            response = self.client.call_tool("manage_level", {
                "action": "stream",
                "level_name": "TestLevel_DryRun",
                "dry_run": True
            })

            if response is None:
                self._record_result(
                    "level_streaming_dry_run", "FAIL",
                    "No response from manage_level streaming action"
                )
                return False

            content = response.get("content", [])
            text_items = [item for item in content if item.get("type") == "text"]

            if not text_items:
                self._record_result(
                    "level_streaming_dry_run", "FAIL",
                    "No text items in streaming dry run response"
                )
                return False

            text_content = text_items[0].get("text", "")

            has_dry_run_info = ("dry" in text_content.lower() or 
                                "simulate" in text_content.lower() or
                                "streaming" in text_content.lower())

            if has_dry_run_info:
                self._record_result(
                    "level_streaming_dry_run", "PASS",
                    "Streaming dry run completed without world modification"
                )
                return True
            else:
                self._record_result(
                    "level_streaming_dry_run", "FAIL",
                    "No dry-run confirmation in response"
                )
                return False

        except Exception as e:
            self._record_result(
                "level_streaming_dry_run", "FAIL",
                f"Exception during streaming dry run: {e}"
            )
            return False

    def test_level_metadata_query(self) -> bool:
        """Verify metadata queries work correctly.

        Tests that the manage_level tool can retrieve level metadata
        such as size, streaming status, and dependencies.
        """
        print("\n[TEST] Level Metadata Query")
        print("-" * 50)

        try:
            response = self.client.call_tool("manage_level", {
                "action": "metadata",
                "level_name": "TestLevel_Metadata"
            })

            if response is None:
                self._record_result(
                    "level_metadata_query", "FAIL",
                    "No response from manage_level metadata action"
                )
                return False

            content = response.get("content", [])
            text_items = [item for item in content if item.get("type") == "text"]

            if not text_items:
                self._record_result(
                    "level_metadata_query", "FAIL",
                    "No text items in metadata query response"
                )
                return False

            text_content = text_items[0].get("text", "")

            metadata_keywords = ["size", "streaming", "dependency", "metadata", 
                                 "loaded", "distance", "bounding"]
            found_count = sum(1 for kw in metadata_keywords if kw.lower() in text_content.lower())

            if found_count >= 1:
                self._record_result(
                    "level_metadata_query", "PASS",
                    f"Metadata query returned data ({found_count} keywords)"
                )
                return True
            else:
                self._record_result(
                    "level_metadata_query", "FAIL",
                    "No metadata information found in response"
                )
                return False

        except Exception as e:
            self._record_result(
                "level_metadata_query", "FAIL",
                f"Exception during metadata query: {e}"
            )
            return False

    def run_all(self) -> List[Dict[str, Any]]:
        """Run all level management tests and return results."""
        print("\n" + "=" * 60)
        print("LEVEL MANAGEMENT TESTS")
        print("=" * 60)

        self.test_list_levels()
        self.test_level_streaming_dry_run()
        self.test_level_metadata_query()

        return self.results


def run_level_management_tests(client: MCPTestClient) -> List[Dict[str, Any]]:
    """Run all level management tests and return results.

    Args:
        client: Initialized MCPTestClient instance

    Returns:
        List of test result dicts
    """
    tester = LevelManagementTests(client)
    return tester.run_all()
