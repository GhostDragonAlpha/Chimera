import json
import urllib.request
import re
import sys

# Add Chimera/core to path for graphify_interface
sys.path.append('Chimera/core')
from graphify_interface import graphify_mutate, load_dna_graph, save_dna_graph

url = "http://localhost:1234/v1/chat/completions"

with open("Chimera/research/loop4/Tool_Shovel_Model/parameters.json", 'r') as f:
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
response_data = None
try:
    response = urllib.request.urlopen(req, timeout=60)
    response_data = response.read().decode('utf-8')
    # Save to file to avoid console encoding issues
    with open("lm_studio_response_tool_shovel.txt", "w", encoding="utf-8") as f:
        f.write(response_data)
    print("LM Studio Response saved to lm_studio_response_tool_shovel.txt")
except Exception as e:
    print("ERROR: LM Studio request failed:", e)
    response_data = None

# Retry once if failed
if response_data is None:
    print("Retrying once...")
    try:
        response = urllib.request.urlopen(req, timeout=60)
        response_data = response.read().decode('utf-8')
        with open("lm_studio_response_tool_shovel.txt", "w", encoding="utf-8") as f:
            f.write(response_data)
        print("LM Studio Response saved to lm_studio_response_tool_shovel.txt (retry)")
    except Exception as e:
        print("FATAL: LM Studio unavailable. Cannot proceed with Professor review.")
        response_data = None

# Parse the grade response - find the LAST occurrence of Grade:, Score:, and Reasoning:
grade_letter = 'C'
score = 70
reasoning = "LM Studio unavailable, default grade assigned."

if response_data:
    grade_match = re.search(r'Grade:\s*([A/B/C/F])', response_data, re.IGNORECASE)
    score_match = re.search(r'Score:\s*(\d+)', response_data)
    reasoning_match = re.search(r'Reasoning:\s*(.+?)(?:\n|$)', response_data, re.IGNORECASE | re.DOTALL)
    
    grade_letter = grade_match.group(1).upper() if grade_match else 'C'
    score = int(score_match.group(1)) if score_match else 70
    reasoning = reasoning_match.group(1).strip() if reasoning_match else "LM Studio response parsing failed or incomplete."
    
    print(f"\nParsed Grade: {grade_letter}")
    print(f"Parsed Score: {score}")
    print(f"Parsed Reasoning: {reasoning}")

# Record grade via Graphify mutation
mutate_result = graphify_mutate("professor_grade", details={
    "feature": "Tool_Shovel_Model",
    "grade": grade_letter,
    "score": score,
    "reasoning": reasoning,
    "lm_studio_raw": response_data if response_data else ""
})

print(f"\nGraphify mutation result: {mutate_result}")

# Gate check
if grade_letter in ["A", "B"]:
    print("\nGate Check: PASSED. Proceed to Apply phase.")
else:
    print("\nGate Check: FAILED. Research needs refinement, do NOT proceed to Apply phase.")
