import sys
sys.path.insert(0, r'E:\PythonChimera\Chimera\core')

from graphify_interface import (
    graphify_query, graphify_mutate, load_dna_graph, _query_gpa, _query_campus
)
from pathlib import Path

dna_path = Path(r'E:\PythonChimera\Chimera\docs/chimera_dna_graph.json')
dna = load_dna_graph()
nodes = dna.get('nodes', [])
edges = dna.get('edges', [])

print('=== PRE-FLIGHT CHECKLIST ===')
print(f'DNA Nodes: {len(nodes)}')
print(f'DNA Edges: {len(edges)}')

# Recent health checks
health_nodes = [n for n in nodes if n.get('type') == 'Health']
print(f'Health checks on record: {len(health_nodes)}')
for h in health_nodes[-3:]:
    print(f'  {h.get("status", "")}: {h.get("details", "")}')

# GPA trend
gpa_trend = _query_gpa("trend")
print(f'\nGPA Trend: {gpa_trend}')

# Find next feature in spiral order
feature_nodes = [n for n in nodes if n.get('type') == 'Feature']

def get_loop_num(node):
    loop = node.get('spiral_loop', '')
    if loop.startswith('Loop '):
        return int(loop.split(' ')[1])
    return 99

def prefix_loop(name):
    for prefix, ln in [('Player_', 0), ('Ground_', 1), ('Verb_', 2), ('Sky_', 3),
                        ('Tool_', 4), ('NPC_', 5), ('Social_', 5), ('Shelter_', 6),
                        ('Travel_', 7), ('System_', 8), ('Universe_', 9)]:
        if name.startswith(prefix):
            return ln
    return 9

sorted_features = sorted(feature_nodes, key=lambda n: (prefix_loop(n.get('name', '')), n.get('name', '')))

print('\n=== SPIRAL ORDER FEATURES ===')
for f in sorted_features:
    status = f.get('status', 'unknown')
    print(f"  {f.get('name', '')}: {status} (loop {f.get('spiral_loop', '')})")

# Next pending feature
pending = [f for f in sorted_features if f.get('status') in ('not_started', 'needs_refinement')]
print(f'\n=== NEXT PENDING FEATURE ===')
if pending:
    next_f = pending[0]
    print(f'Feature: {next_f.get("name", "")}')
    print(f'Status: {next_f.get("status", "")}')
    print(f'Loop: {next_f.get("spiral_loop", "")}')
    print(f'Type: {next_f.get("feature_type", "")}')
else:
    print('No pending features found')

# Query campus
print('\n=== RESEARCH CAMPUS (Game Development) ===')
campus = _query_campus("game_development")
for s in campus.get('seed_sources', []):
    print(f"  {s.get('name', '')} ({s.get('quality', '')})")

print('\n=== RESEARCH CAMPUS (Film School) ===')
campus2 = _query_campus("film_school")
for s in campus2.get('seed_sources', []):
    print(f"  {s.get('name', '')} ({s.get('quality', '')})")

# Query pattern
print('\n=== PATTERN FOR AActor (general geometry) ===')
pattern = graphify_query("pattern", "AActor")
print(pattern)

# Query relevant mutations
print('\n=== MUTATIONS FOR SOUND/ATMOSPHERE ===')
mutations = graphify_query("mutation", "sound")
for m in mutations[:5]:
    print(f'  {m.get("error_signature", "")} | {m.get("fix_description", "")}')
