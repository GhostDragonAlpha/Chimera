import json
import re
import requests
from core.graphify_interface import load_dna_graph, save_dna_graph, graphify_mutate

# 1. Read the updated parameters file
with open('E:/PythonChimera/Chimera/research/loop0/Player_Character_Suit/parameters_updated.json', 'r') as f:
    research_json = f.read()

# 2. Submit to LM Studio
grade_body = {
    "model": "qwen3.6-35b-a3b-mtp@iq2_m",
    "messages": [{
        "role": "user",
        "content": f"""Grade this research summary for feature: Player_Character_Suit_Visor

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

def get_lm_studio_response():
    for attempt in range(2):
        try:
            response = requests.post(
                "http://localhost:1234/v1/chat/completions",
                json=grade_body,
                timeout=60
            )
            response.raise_for_status()
            data = response.json()
            grade_text = data['choices'][0]['message'].get('content', '')
            if not grade_text:
                grade_text = data['choices'][0]['message'].get('reasoning_content', '')
            return grade_text
        except Exception as e:
            print(f"ERROR: LM Studio request failed on attempt {attempt+1}: {e}")
            if attempt == 0:
                print("Retrying once...")
                import time
                time.sleep(5)
            else:
                print("FATAL: LM Studio unavailable. Cannot proceed with Professor review.")
                return "Grade: C\nScore: 70\nReasoning: LM Studio unavailable, default grade assigned."

grade_text = get_lm_studio_response()
print("Professor Response:")
print(grade_text)

# 3. Parse Grade (Handle Thinking Process) - find the LAST occurrence of Grade:, Score:, and Reasoning:
grade_match = re.search(r'Grade:\s*([A/B/C/F])', grade_text, re.IGNORECASE)
score_match = re.search(r'Score:\s*(\d+)', grade_text)
reasoning_match = re.search(r'Reasoning:\s*(.+)', grade_text, re.IGNORECASE)

grade_letter = grade_match.group(1).upper() if grade_match else 'C'
score_value = int(score_match.group(1)) if score_match else 70
reasoning = reasoning_match.group(1).strip() if reasoning_match else "LM Studio unavailable, default grade assigned."

print(f"\nParsed Grade: {grade_letter}")
print(f"Parsed Score: {score_value}")
print(f"Parsed Reasoning: {reasoning}")

# 4. Record Grade and Gate Check via Graphify mutation
mutation_data = {
    "feature": "Player_Character_Suit_Visor",
    "grade": grade_letter,
    "score": score_value,
    "reasoning": reasoning,
    "lm_studio_raw": grade_text
}

graphify_mutate("professor_grade", details=mutation_data)
print("\nGrade recorded via Graphify mutation: g.mutate('professor_grade', {...})")

# 5. Gate check
if grade_letter in ["A", "B"]:
    print(f"\nGATE CHECK PASSED: Grade is {grade_letter}. Proceeding to Apply phase (rebuild material with curved visor geometry).")
    gate_status = "proceed_to_apply"
elif grade_letter in ["C", "F"]:
    print(f"\nGATE CHECK FAILED: Grade is {grade_letter}. HALT - research needs refinement, do NOT proceed to Apply phase.")
    gate_status = "halt_research_refinement"

print(f"\nGate Check Status: {gate_status}")
