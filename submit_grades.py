import json, urllib.request, sys

LM_URL = 'http://localhost:1234/v1/chat/completions'

def call_lm(content):
    payload = {
        'model': 'qwen3.6-35b-a3b-mtp@iq2_m',
        'messages': [
            {'role': 'system', 'content': 'You are a strict professor grading game development research. Grade only based on the criteria given. Return ONLY A grade letter and one sentence explaining why.'},
            {'role': 'user', 'content': content}
        ],
        'max_tokens': 2048,
        'temperature': 0.0
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(LM_URL, data=data, headers={'Content-Type': 'application/json'}, method='POST')
    resp = urllib.request.urlopen(req, timeout=120)
    result = json.loads(resp.read().decode('utf-8'))
    return result['choices'][0]['message']['content']

features = [
    {
        "name": "Tool_Shovel_Model",
        "research": """I am building a game feature: Tool_Shovel_Model — the Apollo-style lunar sampling shovel for a UE5 space game.

My research:
- Campus sources used: NASA Apollo Lunar Surface Journal, NASA Apollo Geology Tools
- New source discovered: https://www.nasa.gov/alsj/alsj-GNCHandToolImages.html — NASA Lunar Surface Hand Tools Image Gallery
- Canonical reference image locked: Apollo 15 Sampling Scoop (AS15-82-11109) — long-handled aluminum-alloy scoop with serrated blade edge, T-handle
- Extracted parameters: handle_length=100cm, blade_width=12cm, blade_angle=15_degrees, material=6061_aluminum_alloy, color=natural_aluminum_anodized (light silver-gray), weight=1.2kg, polygon_budget=1500_tris
- Education principles applied: Architecture School (spatial design — tool extends reach by 1m, form follows function — every curve serves a purpose), Engineering School (industrial design — designed for pressurized glove use, grip diameter 3.5cm for gloved hands)
- Emotional anchor: Purpose (Loop 4) — the shovel is not a weapon, it is an extension of human will to explore and understand. The handle transmits the feel of regolith through gloved hand. Silent competence.

Grade my research. Is it ready to build?
A (4.0): Specific parameters, locked reference, solid principles
B (3.0): Minor gaps but mostly ready
C (2.0): Vague parameters, no locked reference
F (0.0): Missing critical research

Return only the grade letter and one sentence explaining why."""
    },
    {
        "name": "Tool_Scanner_Model",
        "research": """I am building a game feature: Tool_Scanner_Model — the handheld scanner tool for a UE5 space game.

My research:
- Campus sources used: Star Trek Tricorder (TNG), NASA Pistol-Grip Tool (PGT), real scientific instruments (Raman spectrometers, XRF analyzers, APXS)
- New source discovered: https://www.esa.int/Science_Exploration/Human_and_Robotic_Exploration/Research/Portable_instruments_for_planetary_exploration
- Canonical references: Star Trek TNG tricorder (Memory Alpha), NASA EVA PGT, handheld XRF spectrometer
- Extracted parameters: length=18cm, width=8cm, depth=4cm, screen_diagonal=6cm, button_count=3, grip_diameter=4cm, material=anodized_aluminum, color=two-tone_gray, polygon_budget=2000_tris
- Education: Engineering School (industrial design, form follows function), Film School (props design, visual storytelling)
- Emotional anchor: Discovery — a window into the unknown, competence at your fingertips.

Grade my research. Is it ready to build?
Return only the grade letter and one sentence explaining why."""
    },
    {
        "name": "Player_Character_Model",
        "research": """I am building a game feature: Player_Character_Model — the astronaut EVA suit for a UE5 space game. Currently uses sports car body placeholder; needs proper astronaut mesh.

My research:
- Campus sources: NASA EMU suit documentation, NASA xEMU, SpaceX EVA suit, The Martian (2015), 2001: A Space Odyssey
- New source: https://www.nasa.gov/analogs/general-eva
- Canonical reference locked: NASA EMU (Extravehicular Mobility Unit)
- Extracted parameters: overall_height=190cm, shoulder_width=68cm, helmet_diameter=30cm, backpack_PLSS_dimensions=85x50x25cm, polygon_budget=15000_tris
- Education: Art School (form/mass, proportion, silhouette), Engineering School (spatial design, industrial design)
- Emotional anchor: Safety — the suit is a sanctuary in the void. Competence through design.

Grade my research. Is it ready to build?
Return only the grade letter and one sentence explaining why."""
    },
    {
        "name": "Tool_Weapon_Model",
        "research": """I am building a game feature: Tool_Weapon_Model — the emergency/utility space weapon for a UE5 space game.

My research:
- Campus sources: Soviet TP-82 cosmonaut pistol, The Expanse tools, NASA lunar sampling tools
- New source: https://www.nasa.gov/history/alsj/tools/tools.html
- Canonical references: TP-82 space pistol, NASA Apollo sample tools
- Extracted parameters: length=25cm, barrel_length=10cm, grip_ergonomics=4cm_diameter, material=steel_and_polymer, color=matte_black/military_green, polygon_budget=2500_tris
- Also refinement research for: Ground_Rock_Surface (lunar/martian rock formations from NASA Mars Rover), Ground_Metal_Surface (weathered spacecraft metal from ISS exterior images)
- New source for rocks: https://mars.nasa.gov/raw_images/
- Education: Engineering School (spacecraft design)
- Emotional anchor: Purpose — emergency utility tool, not a weapon first.

Grade my research. Is it ready to build?
Return only the grade letter and one sentence explaining why."""
    }
]

results = []
for f in features:
    print(f"\n=== Grading {f['name']} ===")
    try:
        response = call_lm(f['research'])
        print(f"RESPONSE: {response}")
        # Parse grade
        lines = response.strip().split('\n')
        grade_letter = 'F'
        reasoning = response
        for line in lines:
            line = line.strip().upper()
            if line.startswith('A') or line.startswith('B') or line.startswith('C') or line.startswith('F'):
                if len(line) > 0 and line[0] in ('A','B','C','F'):
                    grade_letter = line[0]
                    break
        results.append({"feature": f["name"], "grade": grade_letter, "reasoning": response.strip()})
        print(f"PARSED GRADE: {grade_letter}")
    except Exception as e:
        print(f"ERROR: {e}")
        results.append({"feature": f["name"], "grade": "ERROR", "reasoning": str(e)})

print("\n\n=== ALL RESULTS ===")
print(json.dumps(results, indent=2))