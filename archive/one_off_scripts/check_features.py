import json
from pathlib import Path

dna_path = Path("docs/chimera_dna_graph.json")
with open(dna_path, 'r', encoding='utf-8') as f:
    dna = json.load(f)

features = [n for n in dna.get('nodes', []) if n.get('type') == 'FeatureUpdate']
print(f"Total FeatureUpdates: {len(features)}")

# Print all feature names and loops
print("\nAll Features:")
for f in features[-20:]:  # Show last 20 features
    loop_num = f.get('loop_number') or 'None'
    status = f.get('status')
    if isinstance(status, dict):
        current_status = status.get('current_status', 'unknown')
    else:
        current_status = str(status) if status else 'unknown'
    print(f"  - {f.get('feature_name')} (Loop {loop_num}, Status: {current_status})")

# Look for shovel, scanner, weapon features
shovel_scanner_weapon = [f for f in features if any(word in str(f.get('feature_name', '')).lower() for word in ['shovel', 'scanner', 'weapon'])]
print(f"\nShovel/Scanner/Weapon Features: {len(shovel_scanner_weapon)}")
for f in shovel_scanner_weapon:
    status = f.get('status')
    if isinstance(status, dict):
        current_status = status.get('current_status', 'unknown')
    else:
        current_status = str(status) if status else 'unknown'
    print(f"  - {f.get('feature_name')} (Loop {f.get('loop_number')}, Status: {current_status})")


# Look for tool-related features
tool_features = [f for f in features if 'Tool_' in str(f) or ('tool' in f.get('feature_name', '').lower() and 'model' in f.get('feature_name', '').lower())]
print(f"\nTool Features: {len(tool_features)}")
for f in tool_features:
    print(f"  - {f.get('feature_name')} (Loop {f.get('loop_number')}, Status: {f.get('status', {}).get('current_status', 'unknown')})")
