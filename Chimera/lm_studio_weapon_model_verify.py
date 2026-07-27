import json
import urllib.request

url = "http://localhost:1234/v1/chat/completions"

body = {
    "model": "qwen3.6-35b-a3b-mtp@iq2_m",
    "messages": [
        {
            "role": "system",
            "content": "You are the Professor for the Chimera Project's Ralph Loop. Your task is to review geometry models for tools/weapons and assign a grade (A, B, C, or F) based on the quality, completeness, and fidelity to references and parameters. Provide the grade letter, a score (0-100), and the reasoning sentence. Format your response as: Grade: [Letter], Score: [Score], Reasoning: [reasoning sentence]. Full verbatim response will be used for recording."
        },
        {
            "role": "user",
            "content": "RESEARCH SUMMARY AND GEOMETRY BUILD FOR LOOP 4 TOOL_WEAPON_MODEL (GEOMETRY):\n\nFeature: Tool_Weapon_Model (geometry)\nLoop: 4 - Tools\n\nCanonical Reference Parameters extracted from Playwright research (futuristic space weapon/laser rifle concept art, sci-fi rifle models on Sketchfab):\n- Form factor: Ergonomic grip, stock, barrel with energy core/glow elements, trigger assembly\n- Poly count: Low-poly for game use, typically 500-2000 tris for a handheld weapon\n- Scale: Realistic proportions, roughly 1m length in-game (scaled to UE units ~100cm = 10000 UU)\n- Base geometry components:\n  - Main body (box/cylinder primitive for rifle chassis): SM_WeaponBody_Main - width=150, height=80, depth=400\n  - Barrel (cylinder primitive with energy core glow): SM_WeaponBarrel_Main - radius=20, numSides=16, height=350\n  - Grip (custom box/cylinder combination for ergonomic hand hold): SM_WeaponGrip_Main - width=60, height=120, depth=50\n  - Stock (box primitive for shoulder support): SM_WeaponStock_Main - width=120, height=80, depth=300\n\nUE5 Geometry Creation Results:\n- SM_WeaponBody_Main: DynamicMeshActor Box mesh created (width: 150, height: 80, depth: 400, estimatedTriangles: 6)\n- SM_WeaponBarrel_Main: DynamicMeshActor Cylinder mesh created (radius: 20, numSides: 16, height: 350)\n- SM_WeaponGrip_Main: DynamicMeshActor Box mesh created (width: 60, height: 120, depth: 50, estimatedTriangles: 6)\n- SM_WeaponStock_Main: DynamicMeshActor Box mesh created (width: 120, height: 80, depth: 300, estimatedTriangles: 6)\n\nPlease review this research summary and geometry build for Tool_Weapon_Model (geometry) and assign a grade (A, B, C, or F), a score (0-100), and provide the exact reasoning sentence. Format your response as: Grade: [Letter], Score: [Score], Reasoning: [reasoning sentence]. Full verbatim response will be used for recording."
        }
    ],
    "temperature": 0.1,
    "max_tokens": 500
}

req = urllib.request.Request(url, data=json.dumps(body).encode('utf-8'), headers={'Content-Type': 'application/json'})
response = urllib.request.urlopen(req)
response_data = response.read().decode('utf-8')
print(response_data)
