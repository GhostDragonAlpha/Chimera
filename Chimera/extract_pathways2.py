import json

dna = json.load(open('docs/chimera_dna_graph.json'))
geo_attempts = [n for n in dna['nodes'] if 'cylinder' in str(n).lower() or 'create_box' in str(n).lower()]
print(f"{len(geo_attempts)} geometry-related nodes")
for a in geo_attempts[-10:]:
    print(a.get('id'), a.get('type'))
