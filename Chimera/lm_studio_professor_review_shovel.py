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
            "content": "RESEARCH SUMMARY FOR LOOP 4 TOOLS FEATURES - Tool_Shovel_Model and Tool_Shovel_Material:\n\nSelected features: Tool_Shovel_Model (geometry) and Tool_Shovel_Material (material) from Loop 4 (Tools).\n\nCanonical references found: \n1. Apollo Lunar Sample Return Container (ALSRC) - National Air and Space Museum: aluminum sample box with triple seal aluminum mesh liner for shock absorption, closed under vacuum to approximate lunar ambient pressure. URL: https://airandspace.si.edu/collection-objects/alsrc-apollo-lunar-sample-return-container-apollo-11/nasm_A19710814000\n2. ORNL 'Moon Scoop' - Oak Ridge National Laboratory: metal scoop used during Apollo 11 for lunar regolith collection. URL: https://www.ornl.gov/news/fifty-years-apollo-11-ornl-moon-scoop-remains-source-family-pride\n3. Caltech \"One Metal Scoop, Slightly Used\": reference to astronaut metal scoop. URL: https://www.caltech.edu/about/news/one-metal-scoop-slightly-used-37551\n\nExtracted parameters:\n- Tool_Shovel_Model (geometry): Metal scoop with handle and scoop head (small hand shovel/trowel design), aluminum or stainless steel construction.\n- Tool_Shovel_Material (material): Base color silver/gray metallic (#C0C0C0 or #A8A8A8), Metallic: 0.9-1.0, Roughness: 0.2-0.4 (brushed metal finish), subtle brushed metal normal map.\n\nNew campus source discovered (Campus +1): \"Collecting Moon Rocks: Sample Collection Tools\" - Lunar and Planetary Institute (LPI): https://www.lpi.usra.edu/lunar/samples/apollo/tools/index.shtml (Quality Rating: A+, Engineering School / Science Research Campus)\n\nPathway attempts/failures: Playwright successfully navigated to Google Images search for \"Apollo Lunar Sample Return Scoop image\" and captured relevant references snapshot. Playwright navigation to LPI tools page timed out (MCP error -32001: Request timed out). This failure recorded as pathway_attempt; LPI URL still identified as A+ source from search results snapshot.\n\nPlease review this research summary and assign a grade (A, B, C, or F), a score (0-100), and provide the exact reasoning sentence. Format your response as: Grade: [Letter], Score: [Score], Reasoning: [reasoning sentence]. Full verbatim response will be used for recording."
        }
    ],
    "temperature": 0.1,
    "max_tokens": 500
}

req = urllib.request.Request(url, data=json.dumps(body).encode('utf-8'), headers={'Content-Type': 'application/json'})
try:
    response = urllib.request.urlopen(req)
    response_data = response.read().decode('utf-8')
    print(response_data)
except Exception as e:
    print(f"Error: {e}")
