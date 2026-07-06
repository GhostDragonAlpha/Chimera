import json
import sys
from pathlib import Path

sys.path.insert(0, r'E:\PythonChimera\Chimera\core')

kg_path = Path(r'E:\PythonChimera\Chimera\docs\chimera_knowledge_graph.json')
dna_path = Path(r'E:\PythonChimera\Chimera\docs\chimera_dna_graph.json')

kg = json.loads(kg_path.read_text(encoding='utf-8'))
dna = json.loads(dna_path.read_text(encoding='utf-8'))

print('=== KNOWLEDGE GRAPH HEALTH ===')
print(f'KG Nodes: {len(kg.get("nodes", []))}')
print(f'KG Edges: {len(kg.get("edges", []))}')
print(f'DNA Nodes: {len(dna.get("nodes", []))}')
print(f'DNA Edges: {len(dna.get("edges", []))}')

# Check metadata
meta = kg.get('metadata', {})
print(f'\nCanonical Output Dir: {meta.get("canonical_output_dir")}')
print(f'Module Name: {meta.get("module_name")}')
print(f'API Macro: {meta.get("api_macro")}')

# Feature ledger
feature_nodes = [n for n in kg.get('nodes', []) if n.get('type') in ('feature', 'FeatureUpdate')]
print(f'\n=== FEATURE LEDGER ({len(feature_nodes)} features) ===')

# Group by loop
from collections import defaultdict
by_loop = defaultdict(list)
for n in feature_nodes:
    loop = str(n.get('loop', n.get('data', {}).get('loop', '?')))
    by_loop[loop].append(n)

for loop in sorted(by_loop.keys()):
    names = [n.get('feature_name', n.get('data', {}).get('feature_name', n.get('id', '?'))) for n in by_loop[loop]]
    statuses = set(n.get('status', n.get('data', {}).get('status', 'unknown')) for n in by_loop[loop])
    print(f'\nLoop {loop} ({len(names)} features) — statuses: {statuses}')
    for n in by_loop[loop]:
        name = n.get('feature_name', n.get('data', {}).get('feature_name', n.get('id', '?')))
        status = n.get('status', n.get('data', {}).get('status', 'unknown'))
        print(f'  {name}: {status}')

# Find pending features
pending = [n for n in feature_nodes if n.get('status', n.get('data', {}).get('status')) in ('not_started', 'needs_refinement')]
print(f'\n=== PENDING FEATURES ({len(pending)}) ===')
for f in pending:
    name = f.get('feature_name', f.get('data', {}).get('feature_name', f.get('id', '?')))
    status = f.get('status', f.get('data', {}).get('status', '?'))
    loop = f.get('loop', f.get('data', {}).get('loop', '?'))
    print(f'  Loop {loop}: {name} — {status}')

# Check recent mutations
mutation_nodes = [n for n in dna.get('nodes', []) if n.get('type') == 'mutation']
print(f'\n=== RECENT MUTATIONS (last 10) ===')
for n in mutation_nodes[-10:]:
    print(n)

# Check for pathways
pathway_nodes = [n for n in dna.get('nodes', []) if n.get('type') == 'pathway']
print(f'\n=== MCP PATHWAYS ({len(pathway_nodes)} recorded) ===')
for n in pathway_nodes:
    print(f'  {n.get("name", n.get("id", "?"))}: {n.get("tool", "?")} -> {n.get("action", "?")}')
