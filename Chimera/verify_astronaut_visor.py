import os
import base64
import requests

screenshot_path = r"E:\PythonChimera\Chimera\Screenshots\astronaut_visor_v1.png"
print(f"Screenshot: {screenshot_path}")
size = os.path.getsize(screenshot_path) if os.path.exists(screenshot_path) else 0
print(f"Screenshot size: {size} bytes")

if not os.path.exists(screenshot_path):
    print("ERROR: Screenshot file not found!")
    exit(1)

with open(screenshot_path, "rb") as f:
    img = base64.b64encode(f.read()).decode('utf-8')

prompt = """I built a BP_Astronaut_Character in Unreal Engine 5 with the gold visor material (MAT_Player_Character_Suit_Visor) applied to its helmet mesh component. The material is Opaque PBR metal with BaseColor RGB(0.82, 0.70, 0.35), Metallic 1.0, Roughness 0.1 polished finish.

Compare this screenshot against the canonical reference of an EVA astronaut visor:
- Gold-tinted reflective surface (polycarbonate substrate with gold thin-film coating)
- Polished metallic appearance (Roughness ~0.1)
- Warm gold color (reflectance peak at 580nm)

Does the built character match the reference? Output exactly one of:
VERIFIED — the astronaut visor matches the canonical reference
NEEDS_REFINEMENT — [specific observation of what differs]"""

verifyBody = {
    "model": "qwen3.6-35b-a3b-mtp@iq2_m",
    "messages": [{"role": "user", "content": [
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img}"}}
    ]}],
    "temperature": 0.0,
    "max_tokens": 500
}

try:
    verifyResponse = requests.post("http://localhost:1234/v1/chat/completions", json=verifyBody, timeout=60)
    verifyResponse.raise_for_status()
    resp = verifyResponse.json()
    verifyText = resp.get('choices', [{}])[0].get('message', {}).get('content', '')
    if not verifyText:
        verifyText = resp.get('choices', [{}])[0].get('message', {}).get('reasoning_content', '')
    print(f"LM Studio Response:\n{verifyText}")
except Exception as e:
    print(f"ERROR: LM Studio verification failed: {e}")
    verifyText = "VERIFICATION_FAILED: LM Studio unavailable"

verified = "VERIFIED" in verifyText.upper()
needs_refinement = "NEEDS_REFINEMENT" in verifyText.upper()

if verified:
    result = "VERIFIED"
elif needs_refinement:
    result = "NEEDS_REFINEMENT"
else:
    result = "UNCLEAR"

print(f"\nVerification result: {result}")

# Save response for DNA graph recording
with open(r"E:\PythonChimera\Chimera\Saved\astronaut_visor_verify.json", "w") as f:
    import json
    json.dump({
        "feature": "Player_Character_Model_Visor_Apply",
        "screenshot_path": screenshot_path,
        "verified": verified,
        "result": result,
        "lm_studio_response": verifyText,
        "iterations": 1
    }, f)

print(f"Saved verification data to astronaut_visor_verify.json")