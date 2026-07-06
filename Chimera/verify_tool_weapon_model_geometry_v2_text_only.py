"""
Verify Tool_Weapon_Model geometry (v2) against M41A Pulse Rifle reference using LM Studio API (text-only).
"""
import json
import urllib.request

url = "http://localhost:1234/v1/chat/completions"

prompt = """VERIFY LOOP 4 TOOL_WEAPON_MODEL (GEOMETRY V2):

Generated Geometry:
- Angular Chassis (SM_WeaponChassis_Angular_M41A)
- Power Pack Assembly (SM_WeaponPowerPack_M41A)
- Heat-Sink Barrel (SM_WeaponBarrel_HeatSink_M41A with 16 sides for fin structure)
- Pistol Grip (SM_WeaponGrip_Pistol_M41A)

Note: Materials were not successfully applied due to DynamicMeshActor limitations; geometry remains untextured.

Canonical Reference: M41A Pulse Rifle from the *Aliens* franchise combined with general energy weapon / laser rifle design principles from science fiction military weapons.

Please verify if the generated geometry matches the canonical reference parameters and assign a status (VERIFIED or NEEDS_REFINEMENT) with reasoning. DO NOT include any thinking process or step-by-step analysis. Provide only the final status and reasoning in the exact format: Status: [VERIFIED|NEEDS_REFINEMENT], Reasoning: [reasoning sentence]."""

body = {
    "model": "qwen3.6-35B-A3B-GGUF/Qwen-AgentWorld-35B-A3B-UD-Q3_K_M.gguf",
    "messages": [
        {
            "role": "system",
            "content": "You are the Professor for the Chimera Project's Ralph Loop. Your task is to verify if the generated feature matches the canonical reference. Provide a status: VERIFIED or NEEDS_REFINEMENT, and a reasoning sentence. DO NOT include any thinking process or step-by-step analysis. Format your response EXACTLY as: Status: [VERIFIED|NEEDS_REFINEMENT], Reasoning: [reasoning sentence]."
        },
        {
            "role": "user",
            "content": prompt + "\n\nNote: The current model does not support vision/image analysis. Sending text-only prompt for verification based on geometry description."
        }
    ],
    "temperature": 0.1,
    "max_tokens": 500
}

req = urllib.request.Request(url, data=json.dumps(body).encode('utf-8'), headers={'Content-Type': 'application/json'})
try:
    response = urllib.request.urlopen(req, timeout=120)
    response_data = response.read().decode('utf-8')
    
    # Parse JSON to extract content or reasoning_content
    resp_json = json.loads(response_data)
    choice = resp_json.get('choices', [{}])[0]
    message = choice.get('message', {})
    content = message.get('content', '')
    reasoning_content = message.get('reasoning_content', '')
    
    final_response = content if content else reasoning_content
    
    print(f"\nLM Studio Response:\n{final_response}")
    
    # Save response to file for recording
    with open('lm_studio_professor_review_tool_weapon_model_geometry_v2_response.json', 'w') as f:
        json.dump({
            "lm_studio_response": final_response,
            "screenshot_path": 'E:/PythonChimera/Chimera/Saved/Screenshots/tool_weapon_model_geometry_v2.png',
            "verification_mode": "text_only"
        }, f, indent=2)
except Exception as e:
    print(f"Error connecting to LM Studio: {e}")
