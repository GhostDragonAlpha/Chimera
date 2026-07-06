"""
LM Studio Grading Script for Apollo LRV / Lunar Rover (Travel_Vehicle_Basic - Loop 7)
Sends research summary to LM Studio for grading and records the professor grade in the DNA graph.
"""

import sys
import os

# Add Chimera/Python and Chimera/core to path
chimera_python_dir = os.path.join(os.path.dirname(__file__), 'Chimera', 'Python')
chimera_core_dir = os.path.join(os.path.dirname(__file__), 'Chimera', 'core')
if chimera_python_dir not in sys.path:
    sys.path.insert(0, chimera_python_dir)
if chimera_core_dir not in sys.path:
    sys.path.insert(0, chimera_core_dir)

from lmstudio_client import send_to_lmstudio
from graphify_interface import graphify_mutate, load_dna_graph, save_dna_graph
import json
import re

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

print("Sending research summary to LM Studio for grading...")
result = send_to_lmstudio(
    prompt=grading_prompt,
    model_id=None,
    temperature=0.3,
    max_tokens=2048,
    timeout=120
)

if result and 'content' in result:
    lm_studio_raw = result['content']
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
    mutate_result = graphify_mutate("professor_grade", details=grade_details)
    print(f"Mutation recorded successfully. Node ID: {mutate_result}\n")
    
else:
    print("Failed to get response from LM Studio or no 'content' key in result.")
    if result:
        print(f"Result: {result}")
    sys.exit(1)
