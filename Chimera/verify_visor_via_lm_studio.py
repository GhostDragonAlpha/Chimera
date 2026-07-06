"""
Step 7 & 8: Send screenshot to LM Studio for visual verification.
Record result to DNA graph. Using text description of canonical reference.
"""
import os
import sys
import base64
import json
import hashlib
from datetime import datetime
import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))
from graphify_interface import graphify_mutate

SCREENSHOT_PATH = r"E:\PythonChimera\Chimera\Saved\Screenshots\Player_Character_Suit_verified.png"
LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
MODEL = "qwen3.6-35b-a3b-mtp@iq2_m"

def load_image_b64(path):
    if not os.path.exists(path):
        print(f"ERROR: File not found: {path}")
        return None
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')

def main():
    print("=" * 60)
    print("PLAYER CHARACTER SUIT VISOR - LM STUDIO VERIFICATION")
    print("=" * 60)
    
    screenshot_b64 = load_image_b64(SCREENSHOT_PATH)
    if not screenshot_b64:
        print("FATAL: Cannot proceed without screenshot.")
        sys.exit(1)
    
    print(f"Screenshot: {SCREENSHOT_PATH} ({len(screenshot_b64)} bytes base64)")

    # Send just the screenshot with a detailed text description of the canonical reference
    prompt = (
        "CRITICAL: You MUST output EXACTLY one of these two verdicts as your FINAL line, preceded by a brief analysis:\n"
        "VERIFIED\n"
        "NEEDS_REFINEMENT: <one specific change>\n\n"
        "Evaluate this UE5 gold visor material applied to an NPC helmet mesh.\n\n"
        "CANONICAL REFERENCE (text description):\n"
        "The Apollo/Skylab A7L EVA suit visor consists of:\n"
        "- A gold-coated polycarbonate sun visor with a warm golden reflective appearance\n"
        "- Semi-translucent quality allowing the astronaut's face to be partially visible\n"
        "- Thin-film interference coating producing a metallic gold sheen\n"
        "- The gold tone is approximately RGB (1.0, 0.85, 0.45) - warm golden\n"
        "- Surface is highly polished (low roughness ~0.1) with strong specular reflections\n\n"
        "BUILT FEATURE (from screenshot):\n"
        "The helmet mesh in Unreal Engine 5 with MAT_GoldVisor material applied.\n"
        "Look for:\n"
        "1. Gold/tinted reflective appearance\n"
        "2. Metallic sheen appropriate for gold-coated polycarbonate\n"
        "3. The gold color tone matching warm gold (not orange, not yellow)\n"
        "4. Visible specular highlights on the curved surface\n\n"
        "Your output format:\n"
        "Analysis: <brief one-sentence analysis of what you see>\n"
        "VERIFIED\n"
        "OR\n"
        "Analysis: <brief one-sentence analysis>\n"
        "NEEDS_REFINEMENT: <one specific change>"
    )
    
    body = {
        "model": MODEL,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{screenshot_b64}"}}
            ]
        }],
        "temperature": 0.0,
        "max_tokens": 500
    }
    
    print(f"Sending to LM Studio at {LM_STUDIO_URL}...")
    
    try:
        resp = requests.post(LM_STUDIO_URL, json=body, headers={"Content-Type": "application/json"}, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        lm_response = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        if not lm_response:
            lm_response = data.get("choices", [{}])[0].get("message", {}).get("reasoning_content", "")
    except Exception as e:
        print(f"ERROR: LM Studio request failed: {e}")
        lm_response = "VERIFICATION_FAILED: LM Studio unavailable"
    
    print("\n" + "=" * 60)
    print("LM STUDIO RESPONSE:")
    print("-" * 60)
    print(lm_response)
    print("-" * 60)
    
    # Parse result - look for VERIFIED or NEEDS_REFINEMENT
    verified = "VERIFIED" in lm_response.upper() and "NEEDS_REFINEMENT" not in lm_response.upper()
    needs_refinement = "NEEDS_REFINEMENT" in lm_response.upper()
    
    if verified:
        result = "VERIFIED"
    elif needs_refinement:
        result = "NEEDS_REFINEMENT"
    else:
        result = "UNCLEAR"
    
    print(f"\nResult: {result}")
    
    # Record to DNA graph
    print("\n" + "=" * 60)
    print("RECORDING TO DNA GRAPH...")
    details = {
        "feature": "Player_Character_Suit",
        "screenshot_path": SCREENSHOT_PATH,
        "verified": verified,
        "lm_studio_response": lm_response,
        "description": f"Gold visor material verification (MAT_GoldVisor on NPC Helmet). Result={result}"
    }
    node_id = graphify_mutate("visual_verification", result="pass" if verified else "fail", details=details)
    print(f"DNA graph mutation recorded. Node ID: {node_id}")
    
    # Save verification data
    verification_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "feature": "Player_Character_Suit",
        "screenshot_path": SCREENSHOT_PATH,
        "verified": verified,
        "result": result,
        "lm_studio_response": lm_response,
        "dna_node_id": node_id
    }
    
    output_path = r"E:\PythonChimera\Chimera\verify_visor_result.json"
    with open(output_path, 'w') as f:
        json.dump(verification_data, f, indent=2)
    print(f"Verification data saved to {output_path}")
    
    print("\n" + "=" * 60)
    print("VERIFICATION COMPLETE")
    print(f"Result: {result}")
    if needs_refinement:
        refinement = lm_response.split("NEEDS_REFINEMENT:")[-1].strip() if ":" in lm_response else "Unknown"
        print(f"Suggestion: {refinement}")
    print("=" * 60)

if __name__ == "__main__":
    main()
