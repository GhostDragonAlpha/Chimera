"""
Quick screenshot analysis — sends AutoScreenshot.png to LM Studio for vehicle lift-off verification.

Uses the shared lmstudio_client module for all LM Studio HTTP requests.
"""

import os
import sys

sys.path.insert(0, r"E:\PythonChimera\Chimera\Python")

from config import LM_STUDIO_MODEL, CHIMERA_SAVED_SCREENSHOTS_DIR
from lmstudio_client import send_to_lmstudio, display_response


def analyze_screenshot():
    screenshot_path = os.path.join(CHIMERA_SAVED_SCREENSHOTS_DIR, "AutoScreenshot.png")

    if not os.path.exists(screenshot_path):
        print("[FAIL] No screenshot found at", screenshot_path)
        return None

    prompt = (
        "Analyze this gameplay screenshot from the Chimera vehicle test.\n\n"
        "I need you to specifically confirm whether the vehicle has lifted off the ground or is in flight mode:\n\n"
        "1. Is the vehicle's wheels/tires touching the ground surface?\n"
        "2. What is the approximate height of the vehicle above the ground (estimate in meters)?\n"
        "3. Describe the vehicle's orientation — is it flying upward, level, or tilted?\n"
        "4. Note any visual indicators that suggest flight mode (elevated position, no wheel contact, etc.)\n\n"
        "Provide a clear verdict: Has the vehicle lifted off the ground? Yes or No."
    )

    result = send_to_lmstudio(
        prompt=prompt,
        image_path=screenshot_path,
        model_id=LM_STUDIO_MODEL,
        temperature=0.3,
        max_tokens=1024,
        timeout=120
    )

    if result:
        display_response(result)

    return result


if __name__ == "__main__":
    analyze_screenshot()
