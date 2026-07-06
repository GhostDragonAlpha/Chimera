import json
import re
import requests
import os
import sys

# Ensure stdout is utf-8 encoded
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Read the parameters file
script_dir = os.path.dirname(os.path.abspath(__file__))
params_path = os.path.join(script_dir, 'research/loop0/Player_Character_Model/parameters.json')
with open(params_path, 'r', encoding='utf-8') as f:
    research_json = f.read()

grade_prompt = f"""Grade this research summary for feature: Player_Character_Model

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
Reasoning: [one sentence explaining the grade based on the criteria]
"""

grade_body = {
    "model": "qwen3.6-35b-a3b-mtp@iq2_m",
    "messages": [{
        "role": "user",
        "content": grade_prompt
    }],
    "temperature": 0.0,
    "max_tokens": 1024
}

def get_grade():
    for attempt in range(2):
        try:
            response = requests.post("http://localhost:1234/v1/chat/completions", 
                                     json=grade_body, 
                                     timeout=60)
            response.raise_for_status()
            grade_text = response.json().get('choices', [{}])[0].get('message', {}).get('content')
            
            if not grade_text:
                grade_text = response.json().get('choices', [{}])[0].get('message', {}).get('reasoning_content')
            
            return grade_text
        except Exception as e:
            print(f"ERROR: LM Studio request failed on attempt {attempt+1}: {e}", file=sys.stdout)
            if attempt == 0:
                import time
                time.sleep(5)
    
    print("FATAL: LM Studio unavailable. Cannot proceed with Professor review.", file=sys.stdout)
    print("Grade set to C (default). Proceeding with caution.", file=sys.stdout)
    return "Grade: C\nScore: 70\nReasoning: LM Studio unavailable, default grade assigned."

grade_text = get_grade()
print("Professor Response:", file=sys.stdout)
print(grade_text, file=sys.stdout)

# Parse the grade response using regex to find the LAST occurrence of Grade:, Score:, and Reasoning:
grade_match = re.search(r'Grade:\s*([A/B/C/F])', grade_text, re.IGNORECASE)
score_match = re.search(r'Score:\s*(\d+)', grade_text)
reasoning_match = re.search(r'Reasoning:\s*(.+)', grade_text, re.IGNORECASE)

grade_letter = grade_match.group(1).upper() if grade_match else 'C'
score = int(score_match.group(1)) if score_match else 70
reasoning = reasoning_match.group(1).strip() if reasoning_match else "LM Studio unavailable, default grade assigned."

print(f"\nParsed Grade: {grade_letter}", file=sys.stdout)
print(f"Parsed Score: {score}", file=sys.stdout)
print(f"Parsed Reasoning: {reasoning}", file=sys.stdout)

# Gate check
if grade_letter in ['A', 'B']:
    print("\nGate Check: PASSED - Proceed to Apply phase", file=sys.stdout)
elif grade_letter in ['C', 'F']:
    print("\nGate Check: HALTED - Research needs refinement, do NOT proceed to Apply", file=sys.stdout)
