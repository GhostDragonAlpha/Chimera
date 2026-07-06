"""
Verify Tool_Weapon_Model geometry (v2) against M41A Pulse Rifle reference using LM Studio API (standalone).
"""
import json
import urllib.request
import base64
import os

url = "http://localhost:1234/v1/chat/completions"

prompt = """VERIFY LOOP 4 TOOL_WEAPON_MODEL (GEOMETRY V2):

Generated Geometry:
- Angular Chassis (SM_WeaponChassis_Angular_M41A)
- Power Pack Assembly (SM_WeaponPowerPack_M41A)
- Heat-Sink Barrel (SM_WeaponBarrel_HeatSink_M41A with 16 sides for fin structure)
- Pistol Grip (SM_WeaponGrip_Pistol_M41A)

Note: Materials were not successfully applied due to DynamicMeshActor limitations; geometry remains untextured.

Canonical Reference: M41A Pulse Rifle from the *Aliens* franchise combined with general energy weapon / laser rifle design principles from science fiction military weapons.

Please verify if the generated geometry matches the canonical reference parameters and assign a status (VERIFIED or NEEDS_REFINEMENT) with reasoning. Format your response as: Status: [VERIFIED|NEEDS_REFINEMENT], Reasoning: [reasoning sentence]."""

screenshot_path = 'E:/PythonChimera/Chimera/Saved/Screenshots/tool_weapon_model_geometry_v2.png'

# Read image and encode as base64
with open(screenshot_path, "rb") as image_file:
    encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

image_data_uri = f"data:image/png;base64,{encoded_image}"

body = {
    "model": "qwen3.6-35B-A3B-GGUF/Qwen-AgentWorld-35B-A3B-UD-Q3_K_M.gguf",
    "messages": [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": image_data_uri}}
            ]
        }
    ],
    "temperature": 0.1,
    "max_tokens": 300
}

req = urllib.request.Request(url, data=json.dumps(body).encode('utf-8'), headers={'Content-Type': 'application/json'})
try:
    response = urllib.request.urlopen(req, timeout=120)
    response_data = response.read().decode('utf-8')
    print(response_data)
    
    # Save response to file for recording
    with open('Chimera/lm_studio_professor_review_tool_weapon_model_geometry_v2_response.json', 'w') as f:
        json.dump({
            "lm_studio_response": response_data,
            "screenshot_path": screenshot_path
        }, f, indent=2)
except Exception as e:
    print(f"Error connecting to LM Studio: {e}")
