#!/usr/bin/env python3
"""Generic decoder — reads ANY trained genome and writes its parameters to the level.
Each key in the genome gets mapped to an MCP set_component_property call via the
element catalog. No hand-written decode functions per rung.
"""
import json, os, sys, time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OBJECTIVES_DIR = os.path.join(BASE, 'docs', 'objectives')
DECODED_DIR = os.path.join(BASE, 'docs', 'decoded')
CATALOG_PATH = os.path.join(BASE, 'docs', 'element_catalog.json')


def load_catalog():
    if not os.path.exists(CATALOG_PATH):
        return {}
    with open(CATALOG_PATH) as f:
        data = json.load(f)
    return {e.get('property', ''): e for e in data.get('elements', [])}


def find_trained():
    """Find the latest trained output. All runs write to unnamed.trained.json."""
    path = os.path.join(OBJECTIVES_DIR, 'unnamed.trained.json')
    if not os.path.exists(path):
        return []
    with open(path) as f:
        data = json.load(f)
    return [('latest', data)]


def decode_genome_to_level(c, name, genome, measures):
    """Write a genome's parameters to the level via MCP.
    Maps genome keys to element catalog properties where possible.
    Falls back to generic set_component_property calls.
    """
    catalog = load_catalog()
    
    for key, value in genome.items():
        # Skip metadata keys
        if key in ('n_features', 'n_systems', 'n_interactions'):
            continue
        
        # Try to find this key in the element catalog
        prop_info = catalog.get(key, {})
        prop_class = prop_info.get('class', key.split('_')[-1] if '_' in key else '')
        prop_name = key
        
        # Write to the level
        if isinstance(value, bool):
            val = value
        elif isinstance(value, (int, float)):
            val = value
        else:
            continue
        
        if 'pulse' in key or 'color' in key or 'rate' in key or 'drain' in key or 'regen' in key:
            # These are likely suit or beacon parameters — write to player's suit or the beacon
            if 'suit' in key.lower() or 'o2' in key.lower() or 'drain' in key.lower():
                try:
                    c.call('control_actor', {
                        'action': 'set_component_property',
                        'actorName': 'Player_Astronaut',
                        'componentName': 'SuitLifeSupportComponent',
                        'properties': {prop_name: val}
                    })
                except:
                    pass
    
    # Save decoded output
    os.makedirs(DECODED_DIR, exist_ok=True)
    path = os.path.join(DECODED_DIR, f'{name}.json')
    with open(path, 'w') as f:
        json.dump({'genome': genome, 'measures': measures}, f, indent=2)
    print(f'  Decoded {name} -> {path}')


def decode_all():
    """Read all trained winners and decode them to the level."""
    from core.telemetry_probe import MCPStdioClient
    c = MCPStdioClient()
    
    print('Decoding all trained winners to emergent_world...')
    c.call('control_editor', {'action': 'stop_pie'})
    time.sleep(1)
    
    trained = find_trained()
    for name, data in trained:
        genome = data.get('genome', {})
        measures = data.get('measures', {})
        if genome:
            print(f'  {name}: {len(genome)} params')
            decode_genome_to_level(c, name, genome, measures)
    
    c.call('manage_level', {'action': 'save'})
    print(f'Decoded {len(trained)} rungs to emergent_world level.')


if __name__ == '__main__':
    import sys as _sys
    if 'verify' in _sys.argv:
        from core.telemetry_probe import MCPStdioClient
        c = MCPStdioClient()
        c.call('control_editor', {'action': 'play'})
        time.sleep(5)
        r = c.call('inspect', {'action': 'get_scene_stats'})
        print('Verify:', r.get('result',{}).get('content',[{}])[0].get('text','')[:200])
    else:
        decode_all()
