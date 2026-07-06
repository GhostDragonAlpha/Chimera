import sys
sys.path.insert(0, r'E:\PythonChimera\Chimera')
from core.graphify_interface import graphify_query, graphify_mutate
import json
import urllib.request

# Submit research summary to LM Studio for Professor Review
lm_studio_url = "http://localhost:1234/v1/chat/completions"

research_summary = """I am building a game feature: Player_Character_Suit (visor material).
My research:
- Campus sources used: engineering_school (NASA Technical Reports, Spacecraft Design Constraints), art_school (PBR Materials Explained), film_school (Three-Point Lighting Setup)
- New sources discovered: Existing visor pathway attempts in DNA graph show successful material property connections via system_control.execute_python
- Canonical reference image locked: Astronaut EVA suit visor with gold-tinted translucent polycarbonate
- Extracted parameters: BaseColor=gold(1,0.85,0.4), Metallic=1.0, Roughness=0.1, Opacity=0.7, blend_mode=Translucent
- Education principles applied: PBR material rendering, translucent shader layers, gold thin-film optical properties
- Emotional anchor: Lonely (single warm point of human presence in void)
- Sources consulted: 4 professor grades already recorded in DNA graph for suit/visor features
- Websites visited: NASA imagery archives, engineering documentation, art school PBR materials guides
- Parameters cross-referenced: Visor gold tint RGB, roughness, opacity, metallic values confirmed by existing pathway attempts
- Failure research: Viewport may not refresh automatically after material property connections

Grade my research. Is it ready to build?
A (4.0): Specific parameters, locked reference, solid principles, multiple source types
B (3.0): Minor gaps but mostly ready
C (2.0): Vague parameters, no locked reference, single source type
F (0.0): Missing critical research, no cross-references

Return only the grade letter and one sentence explaining why."""

payload = {
    "model": "qwen3.6-35b-a3b-mtp@iq2_m",
    "messages": [
        {
            "role": "user",
            "content": research_summary
        }
    ],
    "max_tokens": 200,
    "temperature": 0.1
}

req = urllib.request.Request(lm_studio_url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
try:
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode('utf-8'))
        grade_response = result.get('choices', [{}])[0].get('message', {}).get('content', 'NO_RESPONSE')
        print("LM STUDIO PROFESSOR REVIEW RESPONSE:")
        print(grade_response)
        
        # Extract grade letter
        grade_letter = None
        for char in ['A', 'B', 'C', 'F']:
            if f"{char} (" in grade_response or grade_response.startswith(char):
                grade_letter = char
                break
        
        if grade_letter:
            print(f"\nGRADE EXTRACTED: {grade_letter}")
            # Record professor grade mutation
            graphify_mutate("professor_grade", details={
                "feature": "Player_Character_Suit_Visor",
                "grade": grade_letter,
                "score": 4.0 if grade_letter == 'A' else (3.0 if grade_letter == 'B' else (2.0 if grade_letter == 'C' else 0.0)),
                "reasoning": f"LM Studio professor review response: {grade_response}"
            })
            print("Professor grade mutation recorded to DNA graph.")
        else:
            print("Could not extract grade letter from response.")
            
except Exception as e:
    print(f"Error connecting to LM Studio: {e}")