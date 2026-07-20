"""Diagnose why verb pickup doesn't work."""
from core.telemetry_probe import MCPStdioClient
import json

c = MCPStdioClient()

# Find pickup actor
r = c.call('control_actor', {'action': 'find_by_name', 'name': 'PickUp_T'})
data = r.get('result',{}).get('structuredContent',{}).get('result',{}).get('data',{})
for a in data.get('actors', []):
    name = a.get('name','?')
    label = a.get('label','?')
    r2 = c.call('control_actor', {'action': 'get_actor_details', 'actorName': name})
    detail = r2.get('result',{}).get('structuredContent',{}).get('result',{}).get('data',{})
    print(f'{label} ({name})')
    print(f'  class: {detail.get("class","?")}')
    location = detail.get('location', '?')
    print(f'  location: {location}')
    comps = detail.get('components', [])
    for comp in comps[:10]:
        print(f'  component: {comp}')

# Also check: can we read the pickup actor's blueprint to see if it has interaction logic?
print("\n--- Checking for interactable components ---")
r = c.call('control_actor', {'action': 'find_by_name', 'name': 'BP_Verb'})
data = r.get('result',{}).get('structuredContent',{}).get('result',{}).get('data',{})
print(f"BP_Verb actors: {data.get('count',0)}")
for a in data.get('actors', []):
    print(f"  {a.get('label','?')} ({a.get('name','?')})")
