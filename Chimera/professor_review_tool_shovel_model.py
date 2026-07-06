import json
import urllib.request

url = "http://localhost:1234/v1/chat/completions"

body = {
    "model": "qwen3.6-35b-a3b-mtp@iq2_m",
    "messages": [
        {
            "role": "system",
            "content": "You are the Professor for the Chimera Project's Ralph Loop. Your task is to review research summaries for features and assign a grade (A, B, C, or F) based on the quality, completeness, and fidelity to references and parameters. Provide the grade letter, a score (0-100), and the reasoning sentence. Format your response as: Grade: [Letter], Score: [Score], Reasoning: [reasoning sentence]. Full verbatim response will be used for recording."
        },
        {
            "role": "user",
            "content": "RESEARCH SUMMARY FOR LOOP 4 TOOL_SHOVEL_MODEL (GEOMETRY):\n\nCanonical Reference: National Air and Space Museum - 'Tool, Trenching, Lunar Surface' with accession numbers nasm_A19810709000 and nasm_A19810587000. Also Apollo 12 Surveyor III soil mechanics surface sampler scoop shovel references from DVIDS.\n\nGeometry Parameters Extracted:\n- Shovel blade: Rectangular or slightly curved scoop shape, approximately 12-18 inches width, 6-8 inches depth\n- Handle: Telescoping or fixed-length metal tube, approximately 3-4 feet length for astronaut use in low gravity\n- Materials: Aluminum alloy or titanium for lightweight strength, with possible insulating grip sections\n- Design features: Trenching capability, regolith scooping, possibly dual-ended (scoop on one side, spike/edge on other)\n- Scale relative to astronaut suit: Blade width ~1/3 of shoulder width, handle length allowing standing operation\n\nPlease review this research summary and assign a grade (A, B, C, or F), a score (0-100), and provide the exact reasoning sentence. Format your response as: Grade: [Letter], Score: [Score], Reasoning: [reasoning sentence]. Full verbatim response will be used for recording."
        }
    ],
    "temperature": 0.1,
    "max_tokens": 500
}

req = urllib.request.Request(url, data=json.dumps(body).encode('utf-8'), headers={'Content-Type': 'application/json'})
response = urllib.request.urlopen(req)
response_data = response.read().decode('utf-8')
print(response_data)