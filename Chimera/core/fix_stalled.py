"""Fix stalled features in DNA graph so harness can process them."""
import json

g = json.load(open('Chimera/docs/chimera_dna_graph.json'))
prefix_map = {'Player_':0,'Ground_':1,'Verb_':2,'Sky_':3,'Tool_':4,'NPC_':5,'Social_':5,'Shelter_':6,'Travel_':7,'System_':8,'Universe_':9}

fixed = 0
for n in g['nodes']:
    if n.get('type') == 'FeatureUpdate':
        name = n.get('feature_name', '')
        old_status = n.get('status', '')
        raw_loop = n.get('loop')
        if old_status == 'stalled' or (isinstance(raw_loop, str) and raw_loop != '0'):
            # Reset status
            n['status'] = 'needs_refinement'
            # Fix loop to int
            for prefix, loop in prefix_map.items():
                if name.startswith(prefix):
                    n['loop'] = loop
                    break
            fixed += 1
            print(f"  Fixed: {name} ({old_status}, loop={raw_loop!r}) -> needs_refinement, loop={n['loop']}")

json.dump(g, open('Chimera/docs/chimera_dna_graph.json','w'), indent=2)
print(f"Total fixed: {fixed}")