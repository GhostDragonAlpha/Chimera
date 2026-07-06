import os
import glob
from datetime import datetime
import base64
import requests

screenshot_path = r"E:\PythonChimera\Chimera\Saved\Screenshots\sun_lighting_verification.png"
print(f"Screenshot (fallback): {screenshot_path}")
size = os.path.getsize(screenshot_path) if os.path.exists(screenshot_path) else 0
print(f"Screenshot size: {size} bytes")

# LM Studio Visual Verification
verifyText = "VERIFICATION_FAILED: LM Studio unavailable or screenshot missing"
if os.path.exists(screenshot_path):
    with open(screenshot_path, "rb") as f:
        img = base64.b64encode(f.read()).decode('utf-8')

    verifyBody = {
        "model": "qwen3.6-35b-a3b-mtp@iq2_m",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": "Compare this screenshot against the canonical reference. Reference: NASA space suit visor with clear polycarbonate substrate + thin gold top layer for spectral/thin-film shader. Does the built feature match the reference in the ways that matter? Output: VERIFIED or NEEDS_REFINEMENT. If NEEDS_REFINEMENT: state the ONE most important change needed."},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img}"}}
            ]
        }],
        "temperature": 0.0,
        "max_tokens": 500
    }

    try:
        verifyResponse = requests.post("http://localhost:1234/v1/chat/completions", json=verifyBody, timeout=60)
        verifyResponse.raise_for_status()
        verifyText = verifyResponse.json().get('choices', [{}])[0].get('message', {}).get('content', '')
        if not verifyText:
            verifyText = verifyResponse.json().get('choices', [{}])[0].get('message', {}).get('reasoning_content', '')
        print(f"LM Studio Verification:\n{verifyText}")
    except Exception as e:
        print(f"ERROR: LM Studio verification failed: {e}")
        verifyText = "VERIFICATION_FAILED: LM Studio unavailable"

# Parse Verification Result
verified = "VERIFIED" in verifyText.upper()
needs_refinement = "NEEDS_REFINEMENT" in verifyText.upper()

if verified:
    result = "VERIFIED"
elif needs_refinement:
    result = "NEEDS_REFINEMENT"
else:
    result = "UNCLEAR"

print(f"Verification result: {result}")

# Record verification data for Graphify mutation
verification_data = {
    "feature": "Player_Character_Suit_Visor",
    "screenshot_path": screenshot_path,
    "verified": verified,
    "result": result,
    "lm_studio_response": verifyText,
    "iterations": 1
}

print(f"Verification data prepared for Graphify mutation: {verification_data}")
