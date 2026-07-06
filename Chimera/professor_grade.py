import urllib.request
import json

data = json.dumps({
    "model": "qwen3.6-35b-a3b-mtp@iq2_m",
    "messages": [
        {"role": "user", "content": "NPC_Basic_Material research grading.\nParameters: Suit BaseColor (0.83,0.81,0.78) R 0.85 M 0.0. Dirt BaseColor (0.55,0.45,0.30) R 0.9. Visor BaseColor (0.6,0.45,0.1) M 0.1 E 0.05. Connectors R 0.3 M 0.9. PLSS BaseColor (0.15,0.15,0.18) R 0.6. Locked ref: NASA EMU. Campus: Art, Engineering, UE. New source: NASA ISS gallery. Anchor: Safe 3200K.\n\nFirst line of response: A, B, C, or F. Second line: explanation."}
    ],
    "max_tokens": 2048,
    "temperature": 0.0
}).encode('utf-8')

req = urllib.request.Request('http://localhost:1234/v1/chat/completions', data=data, headers={'Content-Type': 'application/json'})
try:
    with urllib.request.urlopen(req, timeout=300) as resp:
        result = json.loads(resp.read().decode('utf-8'))
        msg = result['choices'][0]['message']
        content = msg.get('content', '')
        reasoning = msg.get('reasoning_content', '')
        if content:
            print("CONTENT:", content)
        # Print the LAST 2000 chars of reasoning (contains the conclusion)
        if reasoning:
            print("REASONING_TAIL:", reasoning[-2000:])
except Exception as e:
    print(f"ERROR: {e}")