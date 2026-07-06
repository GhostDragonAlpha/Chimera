import json
import urllib.request

url = "http://localhost:1234/v1/chat/completions"

body = {
    "model": "qwen3.6-35B-A3B-GGUF/Qwen-AgentWorld-35B-A3B-UD-Q3_K_M.gguf",
    "messages": [
        {
            "role": "system",
            "content": "You are the Professor for the Chimera Project's Ralph Loop. Your task is to verify if the generated feature matches the canonical reference. Compare the generated geometry with the NASM 'Tool, Trenching, Lunar Surface' reference. Provide a status: VERIFIED or NEEDS_REFINEMENT, and a reasoning sentence. Format your response as: Status: [VERIFIED|NEEDS_REFINEMENT], Reasoning: [reasoning sentence]."
        },
        {
            "role": "user",
            "content": "VERIFY LOOP 4 TOOL_SHOVEL_MODEL (GEOMETRY):\n\nGenerated Geometry:\n- Shovel blade: Box mesh, width=40 units, height=1 unit, depth=20 units\n- Handle: Cylinder mesh, radius=2 units, height=120 units, 16 sides\n- Materials: Not yet applied (geometry only)\n\nCanonical Reference: National Air and Space Museum - 'Tool, Trenching, Lunar Surface' with accession numbers nasm_A19810709000 and nasm_A19810587000.\n\nPlease verify if the generated geometry matches the canonical reference parameters and assign a status (VERIFIED or NEEDS_REFINEMENT) with reasoning."
        }
    ],
    "temperature": 0.1,
    "max_tokens": 300
}

req = urllib.request.Request(url, data=json.dumps(body).encode('utf-8'), headers={'Content-Type': 'application/json'})
response = urllib.request.urlopen(req)
response_data = response.read().decode('utf-8')
print(response_data)