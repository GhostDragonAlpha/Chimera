"""
Verify Tool_Shovel_Model geometry against Apollo Lunar Sample Tool reference.
"""
import json
import urllib.request
import os

url = "http://localhost:1234/v1/chat/completions"

prompt = """VERIFY LOOP 4 TOOL_SHOVEL_MODEL (GEOMETRY):

Generated Geometry:
- Handle Box: width=0.03m, height=0.35m, depth=0.03m. Transform: location={x:0,y:0,z:0.175}, rotation={pitch:90,yaw:0,roll:0}
- Scoop Box: width=0.12m, height=0.08m, depth=0.06m. Transform: location={x:0,y:0,z:-0.04}, rotation={pitch:0,yaw:0,roll:0}
Both boxes form an L-shaped shovel/scoop geometry.

Canonical Reference: Apollo Lunar Sample Tool (Lunar Soil Sampler / Trowel-Scoop combination) as documented in NASA's Apollo Lunar Surface Journal and NTRS reports. Specific mesh reference: SM_ApolloLunarScoop.obj in Chimera/Content/Meshes/.

Please verify if the generated geometry matches the canonical reference parameters and assign a status (VERIFIED or NEEDS_REFINEMENT) with reasoning. Format your response as: Status: [VERIFIED|NEEDS_REFINEMENT], Reasoning: [reasoning sentence]."""

body = {
    "model": "qwen3.6-35B-A3B-GGUF/Qwen-AgentWorld-35B-A3B-UD-Q3_K_M.gguf",
    "messages": [
        {
            "role": "system",
            "content": "You are the Professor for the Chimera Project's Ralph Loop. Your task is to verify if the generated feature matches the canonical reference. Compare the generated geometry with the Apollo Lunar Sample Tool (Lunar Soil Sampler / Trowel-Scoop combination) reference. Provide a status: VERIFIED or NEEDS_REFINEMENT, and a reasoning sentence. Format your response as: Status: [VERIFIED|NEEDS_REFINEMENT], Reasoning: [reasoning sentence]."
        },
        {
            "role": "user",
            "content": prompt
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
except Exception as e:
    print(f"Error connecting to LM Studio: {e}")
