"""
Verify Tool_Shovel_Model geometry against Apollo Lunar Sample Tool reference using LM Studio client.
"""
import sys
sys.path.insert(0, 'Chimera/Python')

from lmstudio_client import send_to_lmstudio

prompt = """VERIFY LOOP 4 TOOL_SHOVEL_MODEL (GEOMETRY):

Generated Geometry:
- Handle Box: width=0.03m, height=0.35m, depth=0.03m. Transform: location={x:0,y:0,z:0.175}, rotation={pitch:90,yaw:0,roll:0}
- Scoop Box: width=0.12m, height=0.08m, depth=0.06m. Transform: location={x:0,y:0,z:-0.04}, rotation={pitch:0,yaw:0,roll:0}
Both boxes form an L-shaped shovel/scoop geometry.

Canonical Reference: Apollo Lunar Sample Tool (Lunar Soil Sampler / Trowel-Scoop combination) as documented in NASA's Apollo Lunar Surface Journal and NTRS reports. Specific mesh reference: SM_ApolloLunarScoop.obj in Chimera/Content/Meshes/.

Please verify if the generated geometry matches the canonical reference parameters and assign a status (VERIFIED or NEEDS_REFINEMENT) with reasoning. Format your response as: Status: [VERIFIED|NEEDS_REFINEMENT], Reasoning: [reasoning sentence]."""

screenshot_path = 'Chimera/Saved/Screenshots/Screenshot_20260704_184629.png'

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
        
        if content:
            print(f"\nLM Studio Response:\n{content}")
        elif reasoning_content:
            print(f"\nLM Studio Reasoning:\n{reasoning_content}")
    else:
        print("Failed to get response from LM Studio.")
except Exception as e:
    print(f"Error: {e}")
