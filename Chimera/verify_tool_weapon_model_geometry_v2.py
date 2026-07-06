"""
Verify Tool_Weapon_Model geometry (v2) against M41A Pulse Rifle reference using LM Studio client.
"""
import sys
import json

sys.path.insert(0, r"E:\PythonChimera\Chimera\Python")

from lmstudio_client import send_to_lmstudio

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

print(f"Sending screenshot and prompt to LM Studio...")
try:
    result = send_to_lmstudio(
        prompt=prompt,
        image_path=screenshot_path,
        model_id='qwen3.6-35B-A3B-GGUF/Qwen-AgentWorld-35B-A3B-UD-Q3_K_M.gguf',
        temperature=0.1,
        max_tokens=300,
        timeout=120
    )

    if result:
        content = result.get('content', '')
        reasoning_content = result.get('reasoning_content', '')
        
        response_text = content if content else reasoning_content
        
        print(f"\nLM Studio Response:\n{response_text}")
        
        # Save response to file for recording
        with open('Chimera/lm_studio_professor_review_tool_weapon_model_geometry_v2_response.json', 'w') as f:
            json.dump({
                "lm_studio_response": response_text,
                "screenshot_path": screenshot_path
            }, f, indent=2)
    else:
        print("Failed to get response from LM Studio.")
except Exception as e:
    print(f"Error: {e}")
