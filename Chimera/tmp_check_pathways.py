import json
from pathlib import Path

dna_path = Path(r'E:\PythonChimera\Chimera\docs\chimera_dna_graph.json')
dna = json.loads(dna_path.read_text(encoding='utf-8'))
nodes = dna.get('nodes', [])

print('=== PATHWAY NODES IN DNA GRAPH ===')
pathway_nodes = [n for n in nodes if n.get('type') == 'Pathway']
print(f'Count: {len(pathway_nodes)}')
for p in pathway_nodes:
    print(f'  {p.get("name", p.get("id", ""))}: {p.get("tool", "")} -> {p.get("action", "")}')
    print(f'    Desc: {p.get("description", "")}')
    print(f'    Result: {p.get("result", "")}')

print('\n=== PATHWAY EXECUTION NODES ===')
pe_nodes = [n for n in nodes if n.get('type') == 'PathwayExecution']
print(f'Count: {len(pe_nodes)}')
for pe in pe_nodes[:5]:
    print(f'  {pe.get("pathway_name", "")}: success={pe.get("success", "")}, tool={pe.get("tool", "")}')
