"""Test cases for the combat tool category."""

import json
import os
import sys
import time
from typing import Any, Dict, List


sys.path.insert(0, r"E:\PythonChimera\Chimera\Python")

from mcp_automation_client import MCPTestClient


class CombatTests:

    def __init__(self, client: MCPTestClient):
        self.client = client
        self.results: List[Dict[str, Any]] = []
        self.test_count = 0
        self.pass_count = 0
        self.fail_count = 0

    def _record_result(self, test_name: str, status: str, detail: str, response: Dict = None):
        entry = {
            "test": test_name, "category": "combat", "status": status,
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

    def test_spawn_weapons(self) -> bool:
        print("\n[TEST] Spawn Weapons")
        try:
            response = self.client.call_tool("combat", {"action": "spawn_weapon", "weapon_type": "Weapon_Rifle", "name": "TestWeapon_Spawned"})
            if response is None:
                self._record_result("spawn_weapons", "FAIL", "No response from spawn_weapon action")
                return False
            content = response.get("content", [])
            text_items = [item for item in content if item.get("type") == "text"]
            if not text_items:
                self._record_result("spawn_weapons", "FAIL", "No text items in spawn_weapon response")
                return False
            text_content = text_items[0].get("text", "")
            has_weapon_info = ("weapon" in text_content.lower() or "spawned" in text_content.lower() or "rifle" in text_content.lower())
            if has_weapon_info:
                self._record_result("spawn_weapons", "PASS", f"Weapon spawned successfully ({len(text_content)} chars)")
                return True
            else:
                self._record_result("spawn_weapons", "FAIL", "No weapon information in spawn response")
                return False
        except Exception as e:
            self._record_result("spawn_weapons", "FAIL", f"Exception during weapon spawn: {e}")
            return False

    def test_apply_damage(self) -> bool:
        print("\n[TEST] Apply Damage")
        try:
            response = self.client.call_tool("combat", {"action": "apply_damage", "target_name": "ChimeraPawn", "damage_amount": 25.0, "damage_type": "Bullet"})
            if response is None:
                self._record_result("apply_damage", "FAIL", "No response from apply_damage action")
                return False
            content = response.get("content", [])
            text_items = [item for item in content if item.get("type") == "text"]
            if not text_items:
                self._record_result("apply_damage", "FAIL", "No text items in apply_damage response")
                return False
            text_content = text_items[0].get("text", "")
            has_damage_info = ("damage" in text_content.lower() or "health" in text_content.lower() or "bullet" in text_content.lower())
            if has_damage_info:
                self._record_result("apply_damage", "PASS", f"Damage applied successfully ({len(text_content)} chars)")
                return True
            else:
                self._record_result("apply_damage", "FAIL", "No damage information in response")
                return False
        except Exception as e:
            self._record_result("apply_damage", "FAIL", f"Exception during damage application: {e}")
            return False

    def test_heal_actors(self) -> bool:
        print("\n[TEST] Heal Actors")
        try:
            response = self.client.call_tool("combat", {"action": "heal", "target_name": "ChimeraPawn", "heal_amount": 50.0, "heal_type": "Medical"})
            if response is None:
                self._record_result("heal_actors", "FAIL", "No response from heal action")
                return False
            content = response.get("content", [])
            text_items = [item for item in content if item.get("type") == "text"]
            if not text_items:
                self._record_result("heal_actors", "FAIL", "No text items in heal action response")
                return False
            text_content = text_items[0].get("text", "")
            has_heal_info = ("heal" in text_content.lower() or "health" in text_content.lower() or "medical" in text_content.lower())
            if has_heal_info:
                self._record_result("heal_actors", "PASS", f"Healing applied successfully ({len(text_content)} chars)")
                return True
            else:
                self._record_result("heal_actors", "FAIL", "No healing information in response")
                return False
        except Exception as e:
            self._record_result("heal_actors", "FAIL", f"Exception during heal action: {e}")
            return False

    def run_all(self) -> List[Dict[str, Any]]:
        print("\n" + "=" * 60)
        print("COMBAT TESTS")
        self.test_spawn_weapons()
        self.test_apply_damage()
        self.test_heal_actors()
        return self.results


def run_combat_tests(client: MCPTestClient) -> List[Dict[str, Any]]:
    tester = CombatTests(client)
    return tester.run_all()
