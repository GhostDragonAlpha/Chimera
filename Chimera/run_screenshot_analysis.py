"""
Flight test screenshot analysis — sends AutoScreenshot.png to LM Studio.

Uses the shared lmstudio_client module for all LM Studio HTTP requests.
"""

import os
import sys

sys.path.insert(0, r"E:\PythonChimera\Chimera\Python")

from config import LM_STUDIO_MODEL, CHIMERA_SAVED_SCREENSHOTS_DIR

from lmstudio_client import send_to_lmstudio, display_response


def send_analysis():
    screenshot_path = os.path.join(CHIMERA_SAVED_SCREENSHOTS_DIR, "AutoScreenshot.png")

    if not os.path.exists(screenshot_path):
        print("[FAIL] No screenshot found")
        return None

    prompt = (
        "You are analyzing a gameplay screenshot from a vehicle test.\n\n"
        "Describe what you see in this image. Specifically:\n"
        "- Is there a vehicle? What type?\n"
        "- Is the vehicle on the ground or elevated?\n"
        "- Can you see the wheels touching the ground?\n"
        "- What is the approximate height above ground if visible?\n\n"
        "Be descriptive and specific about what you observe."
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
    send_analysis()
