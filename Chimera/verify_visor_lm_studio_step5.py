import base64
import urllib.request
import json
import os

# Read screenshot
screenshot_path = r'E:\PythonChimera\Chimera\Screenshots\player_character_suit_visor_verify_correct.png'
with open(screenshot_path, 'rb') as f:
    image_data_b64 = base64.b64encode(f.read()).decode('utf-8')

image_data = f'data:image/png;base64,{image_data_b64}'

# LM Studio verification prompt
prompt = '''Compare these two images. The first is a canonical reference of gold-tinted translucent polycarbonate EVA visor with polished surface (roughness 0.15, transmission 0.85, base_color RGB(0.85, 0.72, 0.36)). 
The second is what I built in Unreal Engine 5.

Does the built version match the reference in terms of:
- Color accuracy (hue, saturation, brightness)
- Material properties (roughness, metallic, opacity/transmission)
- Lighting (temperature, direction, intensity)
- Proportions and scale
- Overall visual fidelity

Output exactly one of:
VERIFIED — the build matches the reference
NEEDS_REFINEMENT — [specific observation of what differs]

Be specific about what needs to change if refinement is needed.'''

# Create request payload
payload = {
    'model': 'qwen3.6-35b-a3b-mtp@iq2_m',
    'messages': [
        {
            'role': 'user',
            'content': [
                {'type': 'text', 'text': prompt},
                {'type': 'image_url', 'image_url': {'url': image_data}}
            ]
        }
    ],
    'max_tokens': 500,
    'temperature': 0.1
}

# POST to LM Studio
req = urllib.request.Request(
    'http://localhost:1234/v1/chat/completions',
    data=json.dumps(payload).encode('utf-8'),
    headers={'Content-Type': 'application/json'},
    method='POST'
)

try:
    with urllib.request.urlopen(req, timeout=60) as response:
        result = json.loads(response.read().decode('utf-8'))
        lm_studio_response = result['choices'][0]['message']['content']
        
        # Save to file
        with open(r'E:\PythonChimera\Chimera\lm_studio_visor_verification_result.txt', 'w') as f:
            f.write(lm_studio_response)
            
        print("LM Studio verification result saved to lm_studio_visor_verification_result.txt")
        print(lm_studio_response)
except Exception as e:
    error_msg = f'Error: {e}'
    with open(r'E:\PythonChimera\Chimera\lm_studio_visor_verification_result.txt', 'w') as f:
        f.write(error_msg)
    print(error_msg)
