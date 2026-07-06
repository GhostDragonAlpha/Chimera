import json
import urllib.request

url = "http://localhost:1234/v1/chat/completions"

body = {
    "model": "qwen3.6-35b-a3b-mtp@iq2_m",
    "messages": [
        {
            "role": "system",
            "content": "You are the Professor for the Chimera Project's Ralph Loop. Your task is to review research summaries for features and assign a grade (A, B, C, or F) based on the quality, completeness, and fidelity to references and parameters. Provide the grade letter, a score (0-100), and the reasoning sentence. Format your response as: Grade: [Letter], Score: [Score], Reasoning: [reasoning sentence]. Full verbatim response will be used for recording."
        },
        {
            "role": "user",
            "content": "RESEARCH SUMMARY FOR GROUND_ROCK_SURFACE GEOMETRY ADJUSTMENT:\n\nFeature: Ground_Rock_Surface (geometry) - cone mesh scale/polygon count adjustment\nReference sources: NASA lunar surface imagery, standard 3D modeling practices for rocky planetary surfaces\nParameters extracted:\n- Cone radius: 75 UU (small to medium rocks)\n- Cone height: 45 UU (proportional to radius for natural rock appearance)\n- Polygon count (numSides): 7 sides (low-poly angular rock proxy matching lunar/asteroid basaltic rock formations)\n\nPlease review this research summary and assign a grade (A, B, C, or F), a score (0-100), and provide the exact reasoning sentence. Format your response as: Grade: [Letter], Score: [Score], Reasoning: [reasoning sentence]. Full verbatim response will be used for recording."
        }
    ],
    "temperature": 0.1,
    "max_tokens": 500
}

req = urllib.request.Request(url, data=json.dumps(body).encode('utf-8'), headers={'Content-Type': 'application/json'})
response = urllib.request.urlopen(req)
response_data = response.read().decode('utf-8')
print(response_data)