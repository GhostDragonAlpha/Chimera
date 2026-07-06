import requests
import json
import sys
import re
from pathlib import Path

sys.path.insert(0, r'E:\PythonChimera\Chimera\core')
from graphify_interface import graphify_mutate

research_summary = """I am building a game feature: Ground_Sand_Sound (Loop 1: The Ground).

Research:
- NASA xEMU Bone Conduction Study (NTRS 20240005885): lunar suit audio 800-2000 Hz, 40-60 dB SPL, low-pass filtered
- Apollo 11 EVA FD Loop Audio (NASA): 46 min surface communications recording
- Apollo 17 LRV Audio (Apollo Journals): rover wheel impacts on regolith transmitted via suit
- New source: Apollo 17 rover audio archives (public domain NASA, apollojournals.org)
- Extracted parameters:
  * Lunar vacuum: airborne sound -60 dB (silent)
  * Helmet internal: low-pass 800 Hz, 40-60 dB SPL
  * Impact sound: 50-200 Hz low-frequency thuds
  * UE5: UAudioComponent + UAttenuation, volume 0.3-0.6, low-pass enabled
- Principles: NASA suit audio, game tactile feedback, Emotion-To-Parameter: Lonely = Silence (external), Safe = low hum (internal)

Grade: A(4.0) / B(3.0) / C(2.0) / F(0.0)
Return ONLY the grade letter and one sentence."""

try:
    response = requests.post(
        "http://localhost:1234/v1/chat/completions",
        headers={"Content-Type": "application/json"},
        json={
            "model": "qwen3.6-35b-a3b-mtp@iq2_m",
            "messages": [
                {"role": "user", "content": research_summary}
            ],
            "max_tokens": 1500,
            "temperature": 0.0
        },
        timeout=180
    )
    response.raise_for_status()
    result = response.json()
    content = result["choices"][0]["message"].get("content", "") or ""
    reasoning = result["choices"][0]["message"].get("reasoning_content", "") or ""
    
    print(f"Content length: {len(content)}")
    print(f"Content: {content!r}")
    print(f"Finish reason: {result['choices'][0]['message'].get('finish_reason', '')}")
    
    # Look for grade in content
    grade = None
    if content:
        match = re.search(r'\b([A-F])\b', content.strip()[:50])
        if match:
            grade = match.group(1)
    
    if grade:
        grade_id = graphify_mutate("professor_grade", details={
            "feature": "Ground_Sand_Sound",
            "grade": grade,
            "reasoning": content[:200],
            "lm_studio_raw": (content + "\n\n[REASONING]\n" + reasoning)[:1000]
        })
        print(f"\nGrade recorded: {grade} (ID: {grade_id})")
    else:
        print(f"No grade found in content. Checking reasoning for grade...")
        if reasoning:
            match = re.search(r'grade.*?([A-F])', reasoning, re.IGNORECASE)
            if match:
                grade = match.group(1).upper()
                print(f"Found grade in reasoning: {grade}")
                grade_id = graphify_mutate("professor_grade", details={
                    "feature": "Ground_Sand_Sound",
                    "grade": grade,
                    "reasoning": reasoning[:200],
                    "lm_studio_raw": reasoning[:1000]
                })
                print(f"Grade recorded: {grade} (ID: {grade_id})")
        if not grade:
            print("Could not parse grade. Raw saved to tmp_lm_studio_grade.json")
            with open('tmp_lm_studio_grade.json', 'w') as f:
                json.dump(result, f, indent=2)
                
except Exception as e:
    print(f"Error: {e}")
