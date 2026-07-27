import urllib.request
import json

base_url = "http://localhost:1234"
models_endpoint = f"{base_url}/api/v1/models"

print(f"Testing LM Studio API at {models_endpoint}...")

try:
    req = urllib.request.Request(models_endpoint)
    with urllib.request.urlopen(req, timeout=10) as response:
        data = json.loads(response.read().decode('utf-8'))
        print("Success! Response:")
        print(json.dumps(data, indent=2)[:1000])
except Exception as e:
    print(f"Error: {e}")