import json

dna = json.load(open('docs/chimera_dna_graph.json'))
geo_attempts = [n for n in dna['nodes'] if 'create_cylinder' in str(n.get('name', '')) or 'create_box' in str(n.get('name', ''))]
print(f"{len(geo_attempts)} geometry attempts")
for a in geo_attempts[-5:]:
    print(a.get('id'), a.get('tool'), a.get('action'), a.get('result'))
