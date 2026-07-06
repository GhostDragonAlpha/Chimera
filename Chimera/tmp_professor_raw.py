import requests
import json

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
  * Game Development School: Audio feedback confirms tactile interaction (groundcontact)
  * Emotion-to-Parameter: Lonely = Silence externally; Safe = m transmitted Suitch hum internally

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
            "max_tokens": 500,
            "temperature": 0.0
        },
        timeout=60
    )
    print(f"Status: {response.status_code}")
    print(f"Raw response:")
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")
