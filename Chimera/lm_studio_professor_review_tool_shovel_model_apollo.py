import json
import urllib.request

url = "http://localhost:1234/v1/chat/completions"

body = {
    "model": "qwen3.6-35b-a3b-mtp@iq2_m",
    "messages": [
        {
            "role": "system",
            "content": "You are the Professor for the Chimera Project's Ralph Loop. Your task is to review research summaries for features and assign a grade (A, B, C, or F) based on the quality, completeness, and fidelity to references and parameters. Provide the grade letter, a score (0-100), and the reasoning sentence. Format your response EXACTLY as: Grade: [Letter], Score: [Score], Reasoning: [reasoning sentence]. Do not generate internal thinking or reasoning_content before this format. Full verbatim response will be used for recording."
        },
        {
            "role": "user",
            "content": "RESEARCH SUMMARY FOR LOOP 4 TOOL_SHOVEL_MODEL (Apollo lunar scoop):\n\nContext from Research Summary:\n- Feature: Tool_Shovel_Model (Loop 4 — Tools)\n- Reference type: Apollo lunar sample scoop / soil scoop\n- Geometry: T-shaped or straight grip handle, ~18-24 inches total length, scoop blade ~6-8 inches long x ~2-3 inches wide x ~1-2 inches deep, rectangular metal blade with slightly curved or flat bottom, serrated/cutting edge on one side\n- Material: Stainless steel (AISI 304 or 316 grade), polished or brushed metallic finish, no paint/coatings, micro-scratches from abrasive lunar regolith\n- Scale: Handle diameter ~1-1.5 inches for graspability through Apollo A7L space suit gloves, tool weight ~1-2 lbs total\n\nPlease review this research summary and assign a grade (A, B, C, or F), a score (0-100), and provide the exact reasoning sentence. Format your response EXACTLY as: Grade: [Letter], Score: [Score], Reasoning: [reasoning sentence]. Full verbatim response will be used for recording."
        }
    ],
    "temperature": 0.1,
    "max_tokens": 1000
}

req = urllib.request.Request(url, data=json.dumps(body).encode('utf-8'), headers={'Content-Type': 'application/json'})
try:
    response = urllib.request.urlopen(req)
    response_data = response.read().decode('utf-8')
    with open('lm_studio_professor_review_tool_shovel_model_apollo_response.json', 'w', encoding='utf-8') as f:
        f.write(response_data)
    print("Response saved to lm_studio_professor_review_tool_shovel_model_apollo_response.json")
except Exception as e:
    print(f"Error: {e}")
