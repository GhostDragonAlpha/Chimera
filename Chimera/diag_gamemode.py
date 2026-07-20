"""Diagnose GameMode/PlayerController assignment."""
from core.telemetry_probe import MCPStdioClient
c = MCPStdioClient()

# Check GameMode
r = c.call('inspect', {'action': 'runtime_report'})
result = r.get('result',{}).get('structuredContent',{}).get('result',{}).get('data',{})
import json
print("Runtime report:")
print(json.dumps(result, indent=2)[:2000])

# Check what GameMode class is configured
print("\n--- Game Mode ---")
r = c.call('manage_level', {'action': 'get_world_settings'})
data = r.get('result',{}).get('structuredContent',{}).get('result',{}).get('data',{})
print(json.dumps(data, indent=2)[:2000])

# Check what pawn the player uses in PIE
print("\n--- PIE Pawn ---")
r = c.call('control_actor', {'action': 'get_pie_pawn'})
data = r.get('result',{}).get('structuredContent',{}).get('result',{}).get('data',{})
print(json.dumps(data, indent=2)[:2000])
