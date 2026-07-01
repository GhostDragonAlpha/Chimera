"""Test cases for the inventory tool category."""

import json
import os
import sys
import time
from typing import Any, Dict, List


sys.path.insert(0, r"E:\PythonChimera\Chimera\Python")

from mcp_automation_client import MCPTestClient


class InventoryTests:

    def __init__(self, client: MCPTestClient):
        self.client = client
        self.results: List[Dict[str, Any]] = []
        self.test_count = 0
        self.pass_count = 0
        self.fail_count = 0

    def _record_result(self, test_name: str, status: str, detail: str, response: Dict = None):
        entry = {
            "test": test_name, "category": "inventory", "status": status,
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

    def test_add_items(self) -> bool:
        print("\n[TEST] Add Items")
        try:
            response = self.client.call_tool("inventory", {"action": "add_item", "actor_name": "ChimeraPawn", "item_type": "Medkit", "quantity": 3})
            if response is None:
                self._record_result("add_items", "FAIL", "No response from add_item action")
                return False
            content = response.get("content", [])
            text_items = [item for item in content if item.get("type") == "text"]
            if not text_items:
                self._record_result("add_items", "FAIL", "No text items in add_item response")
                return False
            text_content = text_items[0].get("text", "")
            has_item_info = ("item" in text_content.lower() or "inventory" in text_content.lower() or "medkit" in text_content.lower())
            if has_item_info:
                self._record_result("add_items", "PASS", f"Item added successfully ({len(text_content)} chars)")
                return True
            else:
                self._record_result("add_items", "FAIL", "No item information in response")
                return False
        except Exception as e:
            self._record_result("add_items", "FAIL", f"Exception during add_item action: {e}")
            return False

    def test_list_inventory(self) -> bool:
        print("\n[TEST] List Inventory")
        try:
            response = self.client.call_tool("inventory", {"action": "list", "actor_name": "ChimeraPawn"})
            if response is None:
                self._record_result("list_inventory", "FAIL", "No response from list action")
                return False
            content = response.get("content", [])
            text_items = [item for item in content if item.get("type") == "text"]
            if not text_items:
                self._record_result("list_inventory", "FAIL", "No text items in list inventory response")
                return False
            text_content = text_items[0].get("text", "")
            has_inventory_data = ("inventory" in text_content.lower() or "item" in text_content.lower() or "quantity" in text_content.lower())
            if has_inventory_data:
                self._record_result("list_inventory", "PASS", f"Inventory listing returned valid data ({len(text_content)} chars)")
                return True
            else:
                self._record_result("list_inventory", "FAIL", "No inventory data found in response")
                return False
        except Exception as e:
            self._record_result("list_inventory", "FAIL", f"Exception during inventory listing: {e}")
            return False

    def test_equip_weapons(self) -> bool:
        print("\n[TEST] Equip Weapons")
        try:
            response = self.client.call_tool("inventory", {"action": "equip", "actor_name": "ChimeraPawn", "item_type": "Weapon_Rifle", "slot": "primary"})
            if response is None:
                self._record_result("equip_weapons", "FAIL", "No response from equip action")
                return False
            content = response.get("content", [])
            text_items = [item for item in content if item.get("type") == "text"]
            if not text_items:
                self._record_result("equip_weapons", "FAIL", "No text items in equip weapon response")
                return False
            text_content = text_items[0].get("text", "")
            has_equip_info = ("equip" in text_content.lower() or "weapon" in text_content.lower() or "slot" in text_content.lower())
            if has_equip_info:
                self._record_result("equip_weapons", "PASS", f"Weapon equipped successfully ({len(text_content)} chars)")
                return True
            else:
                self._record_result("equip_weapons", "FAIL", "No equipment information in response")
                return False
        except Exception as e:
            self._record_result("equip_weapons", "FAIL", f"Exception during weapon equip: {e}")
            return False

    def run_all(self) -> List[Dict[str, Any]]:
        print("\n" + "=" * 60)
        print("INVENTORY TESTS")
        self.test_add_items()
        self.test_list_inventory()
        self.test_equip_weapons()
        return self.results


def run_inventory_tests(client: MCPTestClient) -> List[Dict[str, Any]]:
    tester = InventoryTests(client)
    return tester.run_all()
