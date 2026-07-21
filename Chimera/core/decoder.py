#!/usr/bin/env python3
"""Decoder — reads trained winners from all 9 rungs and writes them to the emergent_world level.
Uses MCP to spawn actors and set properties. Each rung's decoder is a method on this class.
"""
import json, os, sys, time
import numpy as np

DECODED_DIR = os.path.join(os.path.dirname(__file__), '..', 'docs', 'decoded')
OBJECTIVES_DIR = os.path.join(os.path.dirname(__file__), '..', 'docs', 'objectives')


def _load_trained(rung_name):
    """Load the trained objective for a rung."""
    path = os.path.join(OBJECTIVES_DIR, f'{rung_name}.trained.json')
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    # Fallback to unnamed (latest training run)
    alt = os.path.join(OBJECTIVES_DIR, 'unnamed.trained.json')
    if os.path.exists(alt):
        with open(alt) as f:
            return json.load(f)
    return None


def _save_decoded(rung_name, data):
    """Save decoded output for a rung."""
    os.makedirs(DECODED_DIR, exist_ok=True)
    path = os.path.join(DECODED_DIR, f'{rung_name}.json')
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f'  Decoded {rung_name} -> {path}')
    return path


def decode_solar_system(c):
    """Place star + planets from bigbang.systems.json."""
    systems_path = os.path.join(os.path.dirname(__file__), '..', 'docs', 'objectives', 'bigbang.systems.json')
    if not os.path.exists(systems_path):
        print('  No bigbang.systems.json found. Train the solar system first.')
        return
    
    with open(systems_path) as f:
        data = json.load(f)
    
    systems = data.get('systems', [])
    if not systems:
        print('  No systems in bigbang.systems.json')
        return
    
    system = systems[0]  # Take first system
    star_mass_frac = data.get('star_mass_frac', 0.98)
    SCALE = 500.0
    
    # Star at origin
    c.call('control_actor', {
        'action': 'spawn_actor',
        'actorName': 'Grown_Star',
        'classPath': '/Engine/BasicShapes/Sphere.Sphere',
        'location': {'x': 0.0, 'y': 0.0, 'z': 0.0},
        'scale': {'x': 30, 'y': 30, 'z': 30}
    })
    time.sleep(0.5)
    print(f'  Star placed ({star_mass_frac*100:.1f}% mass)')
    
    # Planets at their orbital positions
    for i, p in enumerate(system):
        a = p.get('a', 1.0)  # semi-major axis in AU
        e = p.get('e', 0.1)  # eccentricity
        x = a * SCALE
        y = e * SCALE * 0.5  # slight offset for eccentricity visualization
        sz = max(1.0, 2.0 * (1.0 - i * 0.15))
        
        c.call('control_actor', {
            'action': 'spawn_actor',
            'actorName': f'Planet_{i+1}',
            'classPath': '/Engine/BasicShapes/Sphere.Sphere',
            'location': {'x': float(x), 'y': float(y), 'z': 0.0},
            'scale': {'x': sz, 'y': sz, 'z': sz}
        })
        time.sleep(0.3)
        print(f'  Planet {i+1}: a={a:.3f} AU, e={e:.3f}')
    
    _save_decoded('solar_system', {
        'star': {'pos': [0, 0, 0], 'mass_frac': star_mass_frac},
        'n_planets': len(system),
        'planets': [{'a': p['a'], 'e': p['e'], 'm_rel': p['m_rel']} for p in system]
    })


def decode_all():
    """Run all decoders. Requires MCPStdioClient with editor running on emergent_world."""
    from core.telemetry_probe import MCPStdioClient
    c = MCPStdioClient()
    
    print('Decoding all rungs to emergent_world level...')
    
    # Stop PIE if running
    c.call('control_editor', {'action': 'stop_pie'})
    time.sleep(1)
    
    decode_solar_system(c)
    
    # Save level
    c.call('manage_level', {'action': 'save'})
    print('Level saved.')
    print('Decoding complete. Start PIE to verify: python -m core.decoder verify')


def verify():
    """Quick verification: start PIE and check basic state."""
    from core.telemetry_probe import MCPStdioClient
    c = MCPStdioClient()
    
    c.call('control_editor', {'action': 'play'})
    time.sleep(5)
    
    # Check scene stats
    r = c.call('inspect', {'action': 'get_scene_stats'})
    print('Scene:', r.get('result',{}).get('content',[{}])[0].get('text','')[:200])
    
    # Check for star
    r2 = c.call('control_actor', {'action': 'find_by_name', 'name': 'Grown_Star'})
    print('Star:', r2.get('result',{}).get('content',[{}])[0].get('text','')[:100])


if __name__ == '__main__':
    import sys as _sys
    if 'verify' in _sys.argv:
        verify()
    else:
        decode_all()
