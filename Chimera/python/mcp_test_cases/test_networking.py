"""Test cases for the networking tool category."""

import json
import os
import sys
import time
from typing import Any, Dict, List


sys.path.insert(0, r"E:\PythonChimera\Chimera\Python")

from mcp_automation_client import MCPTestClient


class NetworkingTests:

    def __init__(self, client: MCPTestClient):
        self.client = client
        self.results: List[Dict[str, Any]] = []
        self.test_count = 0
        self.pass_count = 0
        self.fail_count = 0

    def _record_result(self, test_name: str, status: str, detail: str, response: Dict = None):
        entry = {
            "test": test_name, "category": "networking", "status": status,
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

    def test_host_game(self) -> bool:
        print("\n[TEST] Host Game")
        try:
            response = self.client.call_tool("networking", {"action": "host_game", "session_name": "TestSession_Host", "max_players": 8, "game_mode": "Deathmatch"})
            if response is None:
                self._record_result("host_game", "FAIL", "No response from host_game action")
                return False
            content = response.get("content", [])
            text_items = [item for item in content if item.get("type") == "text"]
            if not text_items:
                self._record_result("host_game", "FAIL", "No text items in host_game response")
                return False
            text_content = text_items[0].get("text", "")
            has_host_info = ("host" in text_content.lower() or "session" in text_content.lower() or "server" in text_content.lower())
            if has_host_info:
                self._record_result("host_game", "PASS", f"Game hosted successfully ({len(text_content)} chars)")
                return True
            else:
                self._record_result("host_game", "FAIL", "No session information in host response")
                return False
        except Exception as e:
            self._record_result("host_game", "FAIL", f"Exception during game hosting: {e}")
            return False

    def test_join_server(self) -> bool:
        print("\n[TEST] Join Server")
        try:
            response = self.client.call_tool("networking", {"action": "join_server", "server_address": "127.0.0.1:7777", "session_name": "TestSession_Host"})
            if response is None:
                self._record_result("join_server", "FAIL", "No response from join_server action")
                return False
            content = response.get("content", [])
            text_items = [item for item in content if item.get("type") == "text"]
            if not text_items:
                self._record_result("join_server", "FAIL", "No text items in join_server response")
                return False
            text_content = text_items[0].get("text", "")
            has_join_info = ("join" in text_content.lower() or "connected" in text_content.lower() or "server" in text_content.lower())
            if has_join_info:
                self._record_result("join_server", "PASS", f"Server join successful ({len(text_content)} chars)")
                return True
            else:
                self._record_result("join_server", "FAIL", "No connection information in join response")
                return False
        except Exception as e:
            self._record_result("join_server", "FAIL", f"Exception during server join: {e}")
            return False

    def test_get_player_list(self) -> bool:
        print("\n[TEST] Get Player List")
        try:
            response = self.client.call_tool("networking", {"action": "get_players", "session_name": "TestSession_Host"})
            if response is None:
                self._record_result("get_player_list", "FAIL", "No response from get_players action")
                return False
            content = response.get("content", [])
            text_items = [item for item in content if item.get("type") == "text"]
            if not text_items:
                self._record_result("get_player_list", "FAIL", "No text items in get_players response")
                return False
            text_content = text_items[0].get("text", "")
            has_player_info = ("player" in text_content.lower() or "list" in text_content.lower() or "connected" in text_content.lower())
            if has_player_info:
                self._record_result("get_player_list", "PASS", f"Player list retrieved successfully ({len(text_content)} chars)")
                return True
            else:
                self._record_result("get_player_list", "FAIL", "No player information in response")
                return False
        except Exception as e:
            self._record_result("get_player_list", "FAIL", f"Exception during player list retrieval: {e}")
            return False

    def run_all(self) -> List[Dict[str, Any]]:
        print("\n" + "=" * 60)
        print("NETWORKING TESTS")
        self.test_host_game()
        self.test_join_server()
        self.test_get_player_list()
        return self.results


def run_networking_tests(client: MCPTestClient) -> List[Dict[str, Any]]:
    tester = NetworkingTests(client)
    return tester.run_all()
