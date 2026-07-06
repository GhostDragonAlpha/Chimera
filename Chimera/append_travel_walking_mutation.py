import json
import hashlib
from datetime import datetime

# Load existing DNA graph
with open('docs/chimera_dna_graph.json', 'r') as f:
    graph = json.load(f)

# Create mutation node for successful Travel_Walking build
new_node = {
    "id": f"mutation_{hashlib.sha256(f'travel_walking_success_{datetime.utcnow().isoformat()}'.encode()).hexdigest()[:12]}",
    "type": "Mutation",
    "timestamp": datetime.utcnow().isoformat(),
    "error_signature": "success_no_error",
    "template_file": "MovementComponent.h/cpp",
    "template_line": 0,
    "error_category": "none",
    "fix_description": "N/A — clean compilation of new Travel_Walking component",
    "compilation_result": "succeeded",
    "links": []
}

# Append to nodes array
graph['nodes'].append(new_node)

# Write back with proper formatting
with open('docs/chimera_dna_graph.json', 'w') as f:
    json.dump(graph, f, indent=2)

print(f"Successfully appended mutation node: {new_node['id']}")
print(f"Total nodes in graph: {len(graph['nodes'])}")
