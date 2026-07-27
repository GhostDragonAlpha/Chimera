"""One-shot: survey the game world state."""
from core.telemetry_probe import MCPStdioClient
import json, time

c = MCPStdioClient()

queries = [
    ("Player", "Player-related"),
    ("Verb", "Verb"),
    ("BP_", "Blueprint"),
    ("NPC", "NPC"),
    ("Character", "Character"),
    ("Astronaut", "Astronaut"),
    ("Erisaid", "Erisaid"),
    ("Shelter", "Shelter"),
    ("Scanner", "Scanner"),
    ("Shovel", "Shovel"),
    ("Ship", "Ship"),
    ("Weapon", "Weapon"),
    ("Tool", "Tool"),
    ("Light", "Light"),
    ("Sky", "Sky"),
    ("Ground", "Ground"),
    ("Sand", "Sand"),
    ("Water", "Water"),
    ("Cloud", "Cloud"),
    ("Star", "Star"),
    ("Sun", "Sun"),
    ("Moon", "Moon"),
]

for name, label in queries:
    r = c.call('control_actor', {'action': 'find_by_name', 'name': name})
    data = r.get('result',{}).get('structuredContent',{}).get('result',{}).get('data',{})
    count = data.get('count', 0)
    if count > 0:
        actors = data.get('actors', [])
        names = [a.get('label', a.get('name','?')) for a in actors[:5]]
        print(f"{label} ({count}): {', '.join(names)}")

print("\n--- Scene totals ---")
r = c.call('inspect', {'action': 'get_scene_stats'})
print(json.dumps(r.get('result',{}).get('structuredContent',{}).get('result',{}), indent=2))
