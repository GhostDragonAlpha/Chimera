import os
import base64
import requests
from datetime import datetime

screenshot_path = r"E:\PythonChimera\Chimera\Saved\Screenshots\Screenshot_20260704_113210.png"

if not os.path.exists(screenshot_path):
    print(f"ERROR: Screenshot not found at {screenshot_path}")
    print("Cannot proceed with visual verification.")
    exit(1)

with open(screenshot_path, "rb") as f:
    img_bytes = f.read()

img_base64 = base64.b64encode(img_bytes).decode('utf-8')

verify_body = {
    "model": "qwen3.6-35b-a3b-mtp@iq2_m",
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Compare this screenshot against the canonical reference. Reference: NASA space suit visor with clear polycarbonate substrate + thin gold top layer for spectral/thin-film shader, curved helmet visor geometry (radius 120, width 240, height 180, depth 100). Does the built feature match the reference in the ways that matter? Output: VERIFIED or NEEDS_REFINEMENT. If NEEDS_REFINEMENT: state the ONE most important change needed."
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{img_base64}"
                    }
                }
            ]
        }
    ],
    "temperature": 0.0,
    "max_tokens": 500
}

try:
    response = requests.post(
        "http://localhost:1234/v1/chat/completions",
        json=verify_body,
        headers={"Content-Type": "application/json"},
        timeout=60
    )
    response.raise_for_status()
    
    result = response.json()
    verify_text = result.get("choices", [{}])[0].get("message", {}).get("content")
    
    if not verify_text:
        verify_text = result.get("choices", [{}])[0].get("message", {}).get("reasoning_content")
        
    print("LM Studio Verification:")
    print(verify_text)
except Exception as e:
    print(f"ERROR: LM Studio verification failed: {e}")
    verify_text = "VERIFICATION_FAILED: LM Studio unavailable"

# Parse verification result
verified = "VERIFIED" in verify_text.upper()
needs_refinement = "NEEDS_REFINEMENT" in verify_text.upper()

if verified:
    result_status = "VERIFIED"
elif needs_refinement:
    result_status = "NEEDS_REFINEMENT"
else:
    result_status = "UNCLEAR"

print(f"\nVerification result: {result_status}")
