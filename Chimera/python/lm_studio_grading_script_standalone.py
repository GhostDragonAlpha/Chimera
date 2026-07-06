"""
LM Studio Grading Script for Apollo LRV / Lunar Rover (Travel_Vehicle_Basic - Loop 7)
Sends research summary to LM Studio for grading and records the professor grade in the DNA graph.
Uses urllib.request directly to bypass config.py logging initialization.
"""

import sys
import os
import json
import re
import urllib.request
import urllib.error
import hashlib
from datetime import datetime, timezone

# Define paths
DNA_GRAPH_PATH = os.path.join(os.path.dirname(__file__), 'Chimera', 'docs', 'chimera_dna_graph.json')

def load_dna_graph():
    if os.path.exists(DNA_GRAPH_PATH):
        with open(DNA_GRAPH_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"nodes": [], "edges": []}

def save_dna_graph(graph):
    dna_dir = os.path.dirname(DNA_GRAPH_PATH)
    os.makedirs(dna_dir, exist_ok=True)
    with open(DNA_GRAPH_PATH, 'w', encoding='utf-8') as f:
        json.dump(graph, f, indent=2)

def hash_node_id(node_type: str, identifier: str) -> str:
    return hashlib.sha256(f"{node_type}:{identifier}".encode('utf-8')).hexdigest()[:16]

def _update_cumulative_gpa(nodes, edges, scope: str):
    """Updates or creates cumulative GPA node for the given scope."""
    if scope is None:
        return
    
    # Find all ProfessorGrade nodes within this scope
    if scope == "project_overall":
        relevant_grades = [n for n in nodes if n.get("type") == "ProfessorGrade"]
    elif scope.startswith("loop_"):
        loop_num = scope.split("_")[1]
        loop_prefixes_keys = [k for k, v in {
            "Player_": 0, "Ground_": 1, "Verb_": 2, "Sky_": 3,
            "Tool_": 4, "NPC_": 5, "Social_": 5, "Shelter_": 6,
            "Travel_": 7, "System_": 8, "Universe_": 9
        }.items() if str(v) == loop_num]
        relevant_grades = [
            n for n in nodes if n.get("type") == "ProfessorGrade" 
            and any(n.get("feature", "").startswith(p) for p in loop_prefixes_keys)
        ]
    else:
        return
    
    if not relevant_grades:
        return
    
    scores = [g.get("score", 0) for g in relevant_grades]
    gpa = sum(scores) / len(scores)
    
    # Find previous GPA node for trend calculation
    previous_nodes = [n for n in nodes if n.get("type") == "ProfessorGPA" and n.get("scope") == scope]
    previous = sorted(previous_nodes, key=lambda x: x.get("timestamp", ""), reverse=True)
    previous_gpa = previous[0].get("gpa", 0.0) if previous else None
    
    # Determine trend
    if previous_gpa is not None:
        if gpa > previous_gpa + 0.05:
            trend = "rising"
        elif gpa < previous_gpa - 0.05:
            trend = "falling"
        else:
            trend = "flat"
    else:
        trend = "flat"
    
    # Create GPA node
    now_utc = datetime.now(timezone.utc)
    gpa_node_id = f"professor_gpa_{hashlib.sha256(f'{scope}_{now_utc.isoformat()}'.encode()).hexdigest()[:16]}"
    gpa_node = {
        "id": gpa_node_id,
        "type": "ProfessorGPA",
        "timestamp": now_utc.isoformat(),
        "scope": scope,
        "gpa": round(gpa, 2),
        "grades_count": len(scores),
        "trend": trend,
        "previous_gpa": previous_gpa,
        "date": now_utc.strftime("%Y-%m-%d"),
        "error_signature": "success_no_error",
        "template_file": f"gpa/{scope}",
        "error_category": "none",
        "fix_description": f"GPA for {scope}: {round(gpa, 2)} ({trend}), based on {len(scores)} grades",
        "compilation_result": "pass",
        "links": []
    }
    
    # Remove old GPA nodes for this scope and add the new one
    nodes = [n for n in nodes if not (n.get("type") == "ProfessorGPA" and n.get("scope") == scope)]
    nodes.append(gpa_node)


# Research summary for Apollo LRV / Lunar Rover (Travel_Vehicle_Basic - Loop 7)
research_summary = """Feature: Travel_Vehicle_Basic (Loop 7: Travel)
Reference: Apollo LRV (Lunar Roving Vehicle)

Extracted Parameters:
- Dimensions: Length ~9 ft (2.74 m), Width ~8.5 ft (2.6 m), Height ~3.75 ft (1.14 m) when upright, wheelbase ~7.5 ft (2.29 m)
- Suspension: Independent suspension with rocker-bogie design, each wheel had its own motor and suspension
- Wheels: 8 wire-mesh tires with titanium chevron treads, 0.5m (16 in) diameter
- Power system: 36-volt silver-zinc batteries, providing about 121 ampere-hours of power, enough for 100 km (62 miles) or 3 hours of continuous operation
- Habitat integration: Stowed in the lunar module descent stage, deployed after moon landing"""

# Grading prompt for LM Studio
grading_prompt = f"""You are the Professor reviewing research summaries for the Chimera project's Feature Ledger. 

Feature: Travel_Vehicle_Basic (Loop 7: Travel)
Reference: Apollo LRV (Lunar Roving Vehicle)

Research Summary and Extracted Parameters:
{research_summary}

Please evaluate this research summary and Apollo LRV reference parameters for `Travel_Vehicle_Basic`. Return a grade letter (A, B, C, or F), score (4.0, 3.0, 2.0, or 0.0), reasoning, and verbatim assessment.

Format your response exactly as:
Grade: [Letter]
Score: [Score]
Reasoning: [Exact LM Studio reasoning sentence]
Assessment: [Verbatim assessment]
"""

# LM Studio API endpoint - try both localhost and 127.0.0.1
LM_STUDIO_BASE_URLS = [
    "http://localhost:1234",
    "http://127.0.0.1:1234",
    "http://192.168.3.169:1234"
]

LM_STUDIO_CHAT_ENDPOINTS = [f"{base}/v1/chat/completions" for base in LM_STUDIO_BASE_URLS]

print(f"Attempting to send research summary to LM Studio at endpoints: {LM_STUDIO_CHAT_ENDPOINTS}...")

# Prepare the request payload
payload = {
    "model": "",  # Let LM Studio choose the default model
    "messages": [
        {
            "role": "user",
            "content": grading_prompt
        }
    ],
    "temperature": 0.3,
    "max_tokens": 2048
}

payload_json = json.dumps(payload).encode('utf-8')

# Create the request and try each endpoint
lm_studio_raw = None
success_endpoint = None

for endpoint in LM_STUDIO_CHAT_ENDPOINTS:
    print(f"Trying endpoint: {endpoint}")
    req = urllib.request.Request(
        endpoint,
        data=payload_json,
        headers={
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            result_json = json.loads(response.read().decode('utf-8'))
            
        # Extract the content from the response
        if 'choices' in result_json and len(result_json['choices']) > 0:
            lm_studio_raw = result_json['choices'][0]['message']['content']
            success_endpoint = endpoint
            break
        else:
            print(f"Failed to get valid response structure from LM Studio at {endpoint}.")
            print(f"Response: {result_json}")
    except urllib.error.HTTPError as e:
        print(f"HTTP Error from LM Studio API at {endpoint}: {e.code} - {e.reason}")
    except urllib.error.URLError as e:
        print(f"URL Error connecting to LM Studio API at {endpoint}: {e.reason}")
    except Exception as e:
        print(f"Exception connecting to LM Studio API at {endpoint}: {e}")

if lm_studio_raw is None or not lm_studio_raw.strip():
    print("\nFailed to get a valid response from any LM Studio endpoint.")
    print("Ensure LM Studio is running and accessible. Check the endpoints tried above.")
    sys.exit(1)

print(f"\nSuccessfully received response from LM Studio at {success_endpoint}")
print("\n=== LM Studio Raw Response ===")
print(lm_studio_raw)
print("=== End LM Studio Raw Response ===\n")

# Parse the grade, score, and reasoning
grade_match = re.search(r'Grade:\s*([A-F])', lm_studio_raw, re.IGNORECASE)
score_match = re.search(r'Score:\s*(\d+\.\d+)', lm_studio_raw)
reasoning_match = re.search(r'Reasoning:\s*(.+?)(?:Assessment:|$)', lm_studio_raw, re.IGNORECASE | re.DOTALL)

parsed_letter = grade_match.group(1).upper() if grade_match else 'F'
parsed_score = float(score_match.group(1)) if score_match else 0.0

reasoning = reasoning_match.group(1).strip() if reasoning_match else "No reasoning provided"

print(f"\n=== Parsed Grade Details ===")
print(f"Feature: Travel_Vehicle_Basic")
print(f"Grade: {parsed_letter}")
print(f"Score: {parsed_score}")
print(f"Reasoning: {reasoning}")
print("=== End Parsed Grade Details ===\n")

# Record in Graphify via g.mutate("professor_grade", {...})
grade_details = {
    "feature": "Travel_Vehicle_Basic",
    "grade": parsed_letter,
    "score": parsed_score,
    "reasoning": reasoning,
    "lm_studio_raw": lm_studio_raw
}

print("Recording professor grade in Graphify...")

# Load DNA graph
dna_graph = load_dna_graph()
nodes = dna_graph.get("nodes", [])
edges = dna_graph.get("edges", [])

feature = grade_details.get("feature", "unknown_feature")
grade = grade_details.get("grade", "F")
reasoning_text = grade_details.get("reasoning", "")

# Map grade to score
grade_scores = {"A": 4.0, "B": 3.0, "C": 2.0, "F": 0.0}
score = grade_scores.get(grade.upper(), 0.0)

# Determine loop from feature name (Travel_ -> 7)
feature_loop = None
if feature.startswith("Travel_"):
    feature_loop = 7

now_utc = datetime.now(timezone.utc)

# Create professor_grade node
grade_node_id = f"professor_grade_{hashlib.sha256(f'{feature}_{now_utc.isoformat()}'.encode()).hexdigest()[:16]}"
grade_node = {
    "id": grade_node_id,
    "type": "ProfessorGrade",
    "timestamp": now_utc.isoformat(),
    "feature": feature,
    "grade": grade.upper(),
    "score": score,
    "reasoning": reasoning_text,
    "lm_studio_raw": lm_studio_raw,
    "error_signature": "success_no_error",
    "template_file": f"professor_grade/{feature}",
    "error_category": "none",
    "fix_description": f"Professor grade recorded: {feature} = {grade} ({score}) — {reasoning_text}",
    "compilation_result": "pass",
    "links": []
}

nodes.append(grade_node)

# Update cumulative GPA for loop_7 and project_overall
_update_cumulative_gpa(nodes, edges, scope=f"loop_{feature_loop}" if feature_loop is not None else None)
_update_cumulative_gpa(nodes, edges, scope="project_overall")

save_dna_graph({"nodes": nodes, "edges": edges})

print(f"Mutation recorded successfully. Node ID: {grade_node_id}\n")
