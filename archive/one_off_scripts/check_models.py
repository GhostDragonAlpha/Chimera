"""Check LM Studio models."""

import urllib.request
import json

endpoint = "http://localhost:1234/api/v1/models"
try:
    with urllib.request.urlopen(endpoint, timeout=10) as resp:
        data = json.loads(resp.read().decode())
        for m in data.get("models", []):
            key = m["key"]
            loaded = bool(m.get("loaded_instances"))
            caps = m.get("capabilities", {})
            vision = caps.get("vision", False)
            print(f"{key} | loaded={loaded} | vision={vision}")
except Exception as e:
    print(f"Error: {e}")
