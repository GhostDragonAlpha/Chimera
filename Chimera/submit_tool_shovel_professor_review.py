import json
import urllib.request
import re

url = "http://localhost:1234/v1/chat/completions"

with open("research/loop4/Tool_Shovel_Model/parameters.json", 'r') as f:
    researchJson = f.read()

gradeBody = {
    "model": "qwen3.6-35b-a3b-mtp@iq2_m",
    "messages": [{
        "role": "user",
        "content": f"""Grade this research summary for feature: Tool_Shovel_Model

Research:
{researchJson}

Grading Criteria:
A (4.0): Complete research with specific technical parameters (exact numbers, not ranges), real-world references (actual URLs, not generic names), and clear implementation path (specific MCP tools and steps).
B (3.0): Good research but missing some specific parameters or references.
C (2.0): Basic research with vague parameters, no real references.
F (0.0): Inadequate or missing research.

Output EXACTLY this format with no other text:
Grade: [A/B/C/F]
Score: [0-100]
Reasoning: [one sentence explaining the grade based on the criteria]
"""
    }],
    "temperature": 0.0,
    "max_tokens": 1024
}

req = urllib.request.Request(url, data=json.dumps(gradeBody).encode('utf-8'), headers={'Content-Type': 'application/json'})
try:
    response = urllib.request.urlopen(req, timeout=60)
    response_data = response.read().decode('utf-8')
    print("LM Studio Response:")
    print(response_data)
except Exception as e:
    print("ERROR: LM Studio request failed:", e)
