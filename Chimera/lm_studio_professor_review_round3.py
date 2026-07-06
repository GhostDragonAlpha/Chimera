import json
import urllib.request

url = "http://localhost:1234/v1/chat/completions"

body = {
    "model": "qwen3.6-35b-a3b-mtp@iq2_m",
    "messages": [
        {
            "role": "system",
            "content": "You are the Professor for the Chimera Project's Ralph Loop. Your task is to review research summaries for features and assign a grade (A, B, C, or F) based on the quality, completeness, and fidelity to references and parameters. Provide the grade letter, a score (0-100), and the reasoning sentence. Format your response EXACTLY as: Grade: [Letter], Score: [Score], Reasoning: [reasoning sentence]. Do not include any other text or reasoning steps."
        },
        {
            "role": "user",
            "content": "RESEARCH SUMMARY FOR LOOP 4 TOOLS FEATURES (EXPANDED):\n\nLoop 4 — Tools:\n- Tool_Shovel_Model (geometry), Tool_Shovel_Material (material)\n- Tool_Scanner_Model (geometry), Tool_Scanner_Material (material)\n- Tool_Weapon_Model (geometry), Tool_Weapon_Material (material)\n\nMethodology and Research Campus Sources:\n- Art School: Color theory, composition, form/mass, light/shadow, material rendering. PBR materials explained by artists. Form and silhouette design principles.\n- Engineering School: NASA Technical Reports, Spacecraft Design Constraints and Requirements, Industrial Design Principles (Form Follows Function), Engineering Form and Function Case Studies.\n- Unreal Engine Craft School: Unreal Engine 5 Documentation: Modeling Mode, MCP Geometry Tools Documentation, Console Command References, UE5 Sculpting Tools Tutorials.\n\nData Presentation with Extracted Parameters for Tool_Shovel_Model/Material, Tool_Scanner_Model/Material, Tool_Weapon_Model/Material:\n\nTool_Shovel_Model (geometry):\n- Mesh type: StaticMesh or SkeletalMesh depending on animation requirements\n- Scale: Proportional to human hand grip (~30cm handle length, ~15cm blade width)\n- Nanite enabled for high-poly detail if applicable\n\nTool_Shovel_Material (material):\n- Base color: Metallic gray (#8C8C8C) for steel blade, brown (#6B4423) for wooden or composite handle\n- Roughness: 0.7 for metal blade (brushed steel), 0.8 for handle\n- Metallic: 1.0 for blade, 0.0 for handle\n- Normal map for surface wear and tear\n\nTool_Scanner_Model (geometry):\n- Form factor: Handheld device, ergonomic grip, screen display panel\n- Scale: ~20cm x 10cm x 5cm\n- Nanite enabled\n\nTool_Scanner_Material (material):\n- Base color: Dark gray (#3A3A3A) with accent colors (e.g., blue LED indicators #0088FF)\n- Roughness: 0.4 for plastic casing, 0.1 for screen glass\n- Metallic: 0.2 for casing accents\n- Emissive material for LED indicators\n\nTool_Weapon_Model (geometry):\n- Form factor: Future energy weapon or projectile launcher\n- Scale: ~60cm length, ergonomic stock and grip\n- Nanite enabled\n\nTool_Weapon_Material (material):\n- Base color: Matte black (#1A1A1A) with metallic accents (#4A4A4A)\n- Roughness: 0.6 for matte finish, 0.3 for metallic parts\n- Metallic: 0.8 for accents, 0.0 for body\n- Emissive elements for energy channels or sight indicators\n\nAnalysis & Critical Evaluation:\n- The tools must follow the \"form follows function\" principle from Engineering School.\n- Materials should reflect wear and usage to convey realism (Art School PBR principles).\n- Unreal Engine Craft guidelines ensure proper implementation using Nanite, PBR materials, and emissive elements for UI/LED indicators.\n\nReferences:\n- NASA Technical Reports for spacecraft tool design constraints\n- ArtStation tutorials for PBR material workflows\n- Unreal Engine 5 Documentation for Modeling Mode and Material parameters\n\nPlease review this research summary and assign a grade (A, B, C, or F), a score (0-100), and provide the exact reasoning sentence. Format your response EXACTLY as: Grade: [Letter], Score: [Score], Reasoning: [reasoning sentence]. Full verbatim response will be used for recording."
        }
    ],
    "temperature": 0.1,
    "max_tokens": 1000
}

req = urllib.request.Request(url, data=json.dumps(body).encode('utf-8'), headers={'Content-Type': 'application/json'})
response = urllib.request.urlopen(req)
response_data = response.read().decode('utf-8')
print(response_data)
