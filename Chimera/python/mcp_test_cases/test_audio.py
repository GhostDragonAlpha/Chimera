"""Test cases for the audio tool category."""

import json
import os
import sys
import time
from typing import Any, Dict, List


sys.path.insert(0, r"E:\PythonChimera\Chimera\Python")

from mcp_automation_client import MCPTestClient


class AudioTests:

    def __init__(self, client: MCPTestClient):
        self.client = client
        self.results: List[Dict[str, Any]] = []
        self.test_count = 0
        self.pass_count = 0
        self.fail_count = 0

    def _record_result(self, test_name: str, status: str, detail: str, response: Dict = None):
        entry = {
            "test": test_name, "category": "audio", "status": status,
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

    def test_play_sounds(self) -> bool:
        print("\n[TEST] Play Sounds")
        try:
            response = self.client.call_tool("audio", {"action": "play_sound", "sound_asset": "SoundEvent_Footstep", "location": {"x": 0, "y": 0, "z": 0}, "looping": False})
            if response is None:
                self._record_result("play_sounds", "FAIL", "No response from play_sound action")
                return False
            content = response.get("content", [])
            text_items = [item for item in content if item.get("type") == "text"]
            if not text_items:
                self._record_result("play_sounds", "FAIL", "No text items in play_sound response")
                return False
            text_content = text_items[0].get("text", "")
            has_sound_info = ("sound" in text_content.lower() or "play" in text_content.lower() or "footstep" in text_content.lower())
            if has_sound_info:
                self._record_result("play_sounds", "PASS", f"Sound played successfully ({len(text_content)} chars)")
                return True
            else:
                self._record_result("play_sounds", "FAIL", "No sound information in playback response")
                return False
        except Exception as e:
            self._record_result("play_sounds", "FAIL", f"Exception during sound playback: {e}")
            return False

    def test_set_volume(self) -> bool:
        print("\n[TEST] Set Volume")
        try:
            response = self.client.call_tool("audio", {"action": "set_volume", "source_name": "AmbientAudioSource", "volume_level": 0.75, "fade_duration": 1.0})
            if response is None:
                self._record_result("set_volume", "FAIL", "No response from set_volume action")
                return False
            content = response.get("content", [])
            text_items = [item for item in content if item.get("type") == "text"]
            if not text_items:
                self._record_result("set_volume", "FAIL", "No text items in set_volume response")
                return False
            text_content = text_items[0].get("text", "")
            has_volume_info = ("volume" in text_content.lower() or "level" in text_content.lower() or "fade" in text_content.lower())
            if has_volume_info:
                self._record_result("set_volume", "PASS", f"Volume set successfully ({len(text_content)} chars)")
                return True
            else:
                self._record_result("set_volume", "FAIL", "No volume information in response")
                return False
        except Exception as e:
            self._record_result("set_volume", "FAIL", f"Exception during volume setting: {e}")
            return False

    def test_apply_mixes(self) -> bool:
        print("\n[TEST] Apply Mixes")
        try:
            response = self.client.call_tool("audio", {"action": "apply_mix", "mix_name": "ReverbMix_Cave", "area_bounds": {"min": {"x": -100, "y": -100, "z": 0}, "max": {"x": 100, "y": 100, "z": 200}}, "blend_time": 2.0})
            if response is None:
                self._record_result("apply_mixes", "FAIL", "No response from apply_mix action")
                return False
            content = response.get("content", [])
            text_items = [item for item in content if item.get("type") == "text"]
            if not text_items:
                self._record_result("apply_mixes", "FAIL", "No text items in apply_mix response")
                return False
            text_content = text_items[0].get("text", "")
            has_mix_info = ("mix" in text_content.lower() or "reverb" in text_content.lower() or "area" in text_content.lower())
            if has_mix_info:
                self._record_result("apply_mixes", "PASS", f"Audio mix applied successfully ({len(text_content)} chars)")
                return True
            else:
                self._record_result("apply_mixes", "FAIL", "No mix information in response")
                return False
        except Exception as e:
            self._record_result("apply_mixes", "FAIL", f"Exception during audio mix application: {e}")
            return False

    def run_all(self) -> List[Dict[str, Any]]:
        print("\n" + "=" * 60)
        print("AUDIO TESTS")
        self.test_play_sounds()
        self.test_set_volume()
        self.test_apply_mixes()
        return self.results


def run_audio_tests(client: MCPTestClient) -> List[Dict[str, Any]]:
    tester = AudioTests(client)
    return tester.run_all()
