"""
Final verification cycle: Send screenshot to LM Studio, record to DNA graph.
Uses pyautogui screenshot (not MCP) as instructed by orchestrator.
"""
import os, sys, base64, json
from datetime import datetime
import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))
from graphify_interface import graphify_mutate

SCREENSHOT_PATH = r"E:\PythonChimera\Chimera\Saved\Screenshots\Player_Character_Suit_verified.png"
LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
MODEL = "qwen3.6-35b-a3b-mtp@iq2_m"

# Verify file size
size = os.path.getsize(SCREENSHOT_PATH)
print(f"Screenshot size: {size} bytes ({size/1024:.1f} KB)")
if size < 100000:
    print("FATAL: Screenshot too small. Report failure.")
    sys.exit(1)

with open(SCREENSHOT_PATH, "rb") as f:
    screenshot_b64 = base64.b64encode(f.read()).decode("utf-8")

# Also load canonical reference
canonical_path = r"E:\PythonChimera\Chimera\research\loop0\Player_Character_Suit\CANONICAL_REFERENCE.jpg"
canonical_b64 = None
if os.path.exists(canonical_path):
    with open(canonical_path, "rb") as f:
        canonical_b64 = base64.b64encode(f.read()).decode("utf-8")
    print(f"Canonical reference loaded: {os.path.getsize(canonical_path)} bytes")
else:
    print("No canonical reference image found, using text description")

prompt = (
    "You are evaluating a gold visor material applied to an NPC helmet mesh in Unreal Engine 5.\n\n"
    "The material is configured with:\n"
    "- BaseColor: Gold (RGB 1.0, 0.85, 0.4)\n"
    "- Metallic: 1.0\n"
    "- Roughness: 0.1\n"
    "- Blend Mode: Translucent\n\n"
    "Canonical reference: Apollo 17 EVA suit gold-coated polycarbonate sun visor.\n"
    "Warm golden reflective appearance, semi-translucent, metallic gold sheen.\n\n"
    "Does the gold visor in the screenshot match the Apollo reference?\n\n"
    "Output EXACTLY one of these as your final line:\n"
    "VERIFIED\n"
    "NEEDS_REFINEMENT: <one specific change>"
)

content_parts = [{"type": "text", "text": prompt}]
content_parts.append({
    "type": "image_url",
    "image_url": {"url": f"data:image/png;base64,{screenshot_b64}"}
})
if canonical_b64:
    content_parts.append({
        "type": "image_url",
        "image_url": {"url": f"data:image/png;base64,{canonical_b64}"}
    })

body = {
    "model": MODEL,
    "messages": [{"role": "user", "content": content_parts}],
    "temperature": 0.0,
    "max_tokens": 100
}

print(f"Sending to LM Studio ({len(screenshot_b64)} bytes base64)...")
resp = requests.post(LM_STUDIO_URL, json=body,
                     headers={"Content-Type": "application/json"}, timeout=120)
resp.raise_for_status()
data = resp.json()
lm_response = data.get("choices", [{}])[0].get("message", {}).get("content", "")
if not lm_response:
    lm_response = data.get("choices", [{}])[0].get("message", {}).get("reasoning_content", "")

print("\n" + "=" * 60)
print("LM STUDIO RESPONSE:")
print(lm_response)
print("=" * 60)

# Parse result
verified = "VERIFIED" in lm_response.upper() and "NEEDS_REFINEMENT" not in lm_response.upper()
result = "VERIFIED" if verified else \
         ("NEEDS_REFINEMENT" if "NEEDS_REFINEMENT" in lm_response.upper() else "UNCLEAR")
print(f"\nResult: {result}")

# Record to DNA graph
details = {
    "feature": "Player_Character_Suit",
    "screenshot_path": SCREENSHOT_PATH,
    "screenshot_size_bytes": size,
    "screenshot_method": "pyautogui",
    "verified": verified,
    "lm_studio_response": lm_response,
    "description": f"Final verification cycle. Screenshot via pyautogui ({size} bytes). Result={result}"
}
node_id = graphify_mutate("visual_verification", result="pass" if verified else "fail", details=details)
print(f"DNA graph node: {node_id}")

# Save report
report = {
    "timestamp": datetime.utcnow().isoformat(),
    "feature": "Player_Character_Suit",
    "screenshot_path": SCREENSHOT_PATH,
    "screenshot_size_bytes": size,
    "screenshot_method": "pyautogui",
    "verified": verified,
    "result": result,
    "lm_studio_response": lm_response,
    "dna_node_id": node_id
}
with open(r"E:\PythonChimera\Chimera\verify_visor_result.json", 'w') as f:
    json.dump(report, f, indent=2)

print(f"\nReport saved. Result: {result}")
