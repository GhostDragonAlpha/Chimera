import requests
import json
import sys
import re
from pathlib import Path

sys.path.insert(0, r'E:\PythonChimera\Chimera\core')
from graphify_interface import graphify_mutate

research_summary = """I am building a game feature: Ground_Sand_Sound (Loop 1: The Ground — Touch).

My research:
- Campus sources used: 
  * NASA Technical Reports Server: Bone Conduction Headphone Research and Testing for xEMU (2024) — lunar suit audio constraints, 800-2000 Hz filtering, 40-60 dB SPL voice comms, acoustic coupling avoidance
  * Apollo 11 EVA FD Loop Audio (NASA History Office, 46 min audio loop)
  * Apollo 17 Lunar Rover Deployment Audio (Apollo Journals, NASA Johnson Space Center) — rover wheel impacts on regolith transmitted via suit structure
- New source discovered: Apollo 17 LRV Audio Clips at apollojournals.org + archive.org Apollo17 mission audio (public domain NASA recordings)
- Canonical reference locked: Apollo 17 Lunar Rover Deployment Audio (public domain NASA Johnson Space Center). Principle validated: no airborne sound in lunar vacuum, only suit-transmitted vibrations and radio communications.
- Extracted parameters:
  * External environment: Vacuum = airborne sound attenuation -60 dB (no propagation)
  * Internal suit audio: Low-pass filtered, dominant frequencies 50-500 Hz (helmet structural damping)
  * Bone conduction window: 800-2000 Hz with 40-60 dB SPL for situational awareness
  * Impact sound type: Low-frequency thuds (50-200 Hz) via suit chassis transmission
  * Radio interference: VHF whistles near 2-4 kHz (Apollo 10 "space music" phenomenon — radio coupling between LM and CM)
  * UE5 implementation: UAudioComponent with UAttenuation, volume multiplier 0.3-0.6, low-pass filter enabled
- Education principles applied:
  * Engineering School: NASA xEMU audio specifications, bone conduction limits, acoustic coupling
  * Game Development School: Audio feedback confirms tactile interaction (ground contact)
  * Emotion-to-Parameter: Lonely = Silence externally; Safe = soft transmitted suit hum internally

Grade my research. Is it ready to build?
A (4.0): Specific parameters, locked reference, solid principles
B (3.0): Minor gaps but mostly ready
C (2.0): Vague parameters, no locked reference
F (0.0): Missing critical research

Return only the grade letter and one sentence explaining why."""

try:
    response = requests.post(
        "http://localhost:1234/v1/chat/completions",
        headers={"Content-Type": "application/json"},
        json={
            "model": "qwen3.6-35b-a3b-mtp@iq2_m",
            "messages": [
                {"role": "user", "content": research_summary}
            ],
            "max_tokens": 800,
            "temperature": 0.0
        },
        timeout=120
    )
    response.raise_for_status()
    result = response.json()
    content = result["choices"][0]["message"].get("content", "") or ""
    reasoning = result["choices"][0]["message"].get("reasoning_content", "") or ""
    
    print(f"Content: {content!r}")
    print(f"Reasoning preview: {reasoning[:300]!r}")
    
    # Try to parse grade from reasoning content
    grade = None
    if reasoning:
        match = re.search(r'Conclusion:.*?criteria for an ([A-F])', reasoning, re.IGNORECASE)
        if match:
            grade = match.group(1).upper()
            explanation = re.search(r'The research is graded an A because (.*)', reasoning)
            if explanation:
                reasoning_text = explanation.group(1).strip() + "."
            else:
                reasoning_text = reasoning[:300]
        else:
            reasoning_text = reasoning[:300]
    elif content:
        first_char = content.strip()[0].upper()
        if first_char in ('A', 'B', 'C', 'D', 'F'):
            grade = first_char
        reasoning_text = content
    
    print(f"\nParsed grade: {grade}")
    print(f"Reasoning text: {reasoning_text[:300]}")
    
    if grade:
        grade_id = graphify_mutate("professor_grade", details={
            "feature": "Ground_Sand_Sound",
            "grade": grade,
            "reasoning": reasoning_text[:200],
            "lm_studio_raw": (content + "\n\n[REASONING]\n" + reasoning)[:1000]
        })
        print(f"\nGrade recorded: {grade} (ID: {grade_id})")
    else:
        print("Could not parse grade from response")
        with open('tmp_lm_studio_grade.json', 'w') as f:
            json.dump(result, f, indent=2)
        print("Saved raw response to tmp_lm_studio_grade.json")
        
except Exception as e:
    print(f"Error calling LM Studio: {e}")
