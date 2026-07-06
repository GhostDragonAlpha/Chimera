import json
import urllib.request
import re
import sys

# Read the parameters file
with open('Chimera/research/loop4/Tool_Weapon_Model/parameters.json', 'r') as f:
    research_json = f.read()

grade_body = {
    "model": "qwen3.6-35b-a3b-mtp@iq2_m",
    "messages": [{
        "role": "user",
        "content": f"""Grade this research summary for feature: Tool_Weapon_Model

Research:
{research_json}

Grading Criteria:
A (4.0): Complete research with specific technical parameters (exact numbers, not ranges), real-world references (actual URLs, not generic names), and clear implementation path (specific MCP tools and steps).
B (3.0): Good research but missing some specific parameters or references.
C (2.0): Basic research with vague parameters, no real references.
F (0.0): Inadequate or missing research.

Output EXACTLY this format with no other text:
Grade: [A/B/C/F]
Score: [0-100]
Reasoning: [one sentence explaining the grade based on the criteria]"""
    }],
    "temperature": 0.0,
    "max_tokens": 1024
}

url = "http://localhost:1234/v1/chat/completions"

req = urllib.request.Request(url, data=json.dumps(grade_body).encode('utf-8'), headers={'Content-Type': 'application/json'})
try:
    response = urllib.request.urlopen(req, timeout=60)
    response_data = response.read().decode('utf-8')
except Exception as e:
    print(f"ERROR: LM Studio request failed: {e}")
    print("Retrying once...")
    import time
    time.sleep(5)
    try:
        response = urllib.request.urlopen(req, timeout=60)
        response_data = response.read().decode('utf-8')
    except Exception as e2:
        print(f"FATAL: LM Studio unavailable. Cannot proceed with Professor review.")
        print("Grade set to C (default). Proceeding with caution.")
        grade_text = "Grade: C\nScore: 70\nReasoning: LM Studio unavailable, default grade assigned."
        response_data = grade_text

# Extract the message content from the JSON response
try:
    response_json = json.loads(response_data)
    if 'choices' in response_json and len(response_json['choices']) > 0:
        message = response_json['choices'][0].get('message', {})
        grade_text = message.get('content', '') or message.get('reasoning_content', '') or ''
except Exception:
    grade_text = response_data

# Write to file to avoid UnicodeEncodeError in console
with open('Chimera/lm_studio_weapon_grade_response.txt', 'w', encoding='utf-8') as f:
    f.write(grade_text)

print("LM Studio Response saved to Chimera/lm_studio_weapon_grade_response.txt")
print("-" * 40)

# Parse the response using regex to find the LAST occurrence of Grade:, Score:, and Reasoning:
grade_match = re.search(r'Grade:\s*([A/B/C/F])', grade_text, re.IGNORECASE)
score_match = re.search(r'Score:\s*(\d+)', grade_text)
reasoning_match = re.search(r'Reasoning:\s*(.+)', grade_text, re.DOTALL | re.IGNORECASE)

if grade_match and score_match and reasoning_match:
    grade_letter = grade_match.group(1).upper()
    score = int(score_match.group(1))
    reasoning = reasoning_match.group(1).strip()
    
    print(f"Parsed Grade: {grade_letter}")
    print(f"Parsed Score: {score}")
    print(f"Parsed Reasoning: {reasoning}")
    
    # Gate check
    if grade_letter in ["A", "B"]:
        print("\nGate check PASSED: Proceed to Apply phase")
        sys.exit(0)
    else:
        print("\nGate check FAILED: HALT - research needs refinement, do NOT proceed to Apply")
        sys.exit(1)
else:
    print("Failed to parse grade response")
    sys.exit(2)
