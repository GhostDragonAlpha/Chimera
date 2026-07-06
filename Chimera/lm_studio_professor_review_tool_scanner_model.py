import json
import urllib.request

url = "http://localhost:1234/v1/chat/completions"

body = {
    "model": "qwen3.6-35b-a3b-mtp@iq2_m",
    "messages": [
        {
            "role": "system",
            "content": "You are the Professor for the Chimera Project's Ralph Loop. Your task is to review research summaries for features and assign a grade (A, B, C, or F) based on the quality, completeness, and fidelity to references and parameters. You must output ONLY the exact format: 'Grade: [Letter], Score: [Score], Reasoning: [reasoning sentence]'. Do not generate any internal thinking, reasoning_content, or any other text. Start your response immediately with 'Grade:'."
        },
        {
            "role": "user",
            "content": "RESEARCH SUMMARY FOR LOOP 4 TOOL_SCANNER_MODEL:\n\nContext from Research Summary:\n- Feature: Tool_Scanner_Model (Loop 4 — Tools)\n- Canonical references found via Playwright Google Images search: Creaform EVO Series Handheld 3D Scanner, Hexagon ATLASCAN Pro / Handheld 3D Scanners, Honeywell SF61B Cordless Industrial Handheld Pocket Scanner & TEEMI IH50 Barcode Scanner, Garrett THD Tactical Hand Held Metal Detector.\n- Geometry: Ergonomic pistol-grip or straight-grip handle transitioning into a scanning head at the front. Dimensions: Length ~200-250 mm, Width ~60-80 mm, Depth/Height ~40-60 mm. Scanning window: rectangular or slightly curved transparent polycarbonate cover at the front housing laser lines or sensor array. Trigger on pistol-grip handle. Status LEDs as small circular indentations.\n- Material: Body - matte black or dark grey polymer/composite (IP67 rating style), roughness ~0.8, metallic ~0.05. Scanning window - clear polycarbonate substrate with slight reflectivity and transmission. Grip - textured rubber or elastomer overlay, roughness ~0.9, metallic ~0.0.\n- Colors: Primary body - matte black (#1A1A1A) or dark grey (#2C2C2C). Accents - orange (#FF6600) or yellow for trigger accents and status LED rings. Scanning window - clear/translucent.\n- Lighting/Functional Elements: Status LEDs (small point lights with emissive material: blue/green for active, red for error). Scanning laser line (thin blue or red laser line across the scanning window for 3D scanner reference).\n\nPlease review this research summary and assign a grade (A, B, C, or F), a score (0-100), and provide the exact reasoning sentence. Format your response EXACTLY as: Grade: [Letter], Score: [Score], Reasoning: [reasoning sentence]. Output ONLY this format. Do not generate any internal thinking or reasoning_content."
        }
    ],
    "temperature": 0.1,
    "max_tokens": 150
}

req = urllib.request.Request(url, data=json.dumps(body).encode('utf-8'), headers={'Content-Type': 'application/json'})
try:
    response = urllib.request.urlopen(req)
    response_data = response.read().decode('utf-8')
    with open('lm_studio_professor_review_tool_scanner_model_response.json', 'w', encoding='utf-8') as f:
        f.write(response_data)
    print("Response saved to lm_studio_professor_review_tool_scanner_model_response.json")
except Exception as e:
    print(f"Error: {e}")
