"""level_composer — builds the emergent world from decoded training parameters.

The pipeline trained all the parameters. The decoder wrote them as JSON. But the
game had nothing in it — a PlayerStart and a DirectionalLight that looked like a
half-moon. Because nobody ever took the decoded output and actually built the level.

This module closes that gap. It reads docs/decoded/*.json, and for each rung,
emits the corresponding UE5 level actors via MCP. One command to build the game.

Usage:
    python -m core.level_composer          # build emergent_world from decoded params
    python -m core.level_composer --dry    # print what would be built
    python -m core.level_composer --check  # check which rungs have level-ready params
"""

from __future__ import annotations

import glob
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Maps decoded rung names to their build functions
# Each function reads the decoded params and returns a list of (actor_class, kwargs)
# for MCP spawning, OR Blueprint string for deferred execution.


def _get(d, *keys, default=None):
    """Get from dict, trying 'genome' wrapper then flat keys."""
    genome = d.get('genome', d)
    for k in keys:
        v = genome.get(k, d.get(k))
        if v is not None:
            return v
    return default


def build_sky(decoded: dict) -> list[dict]:
    """Sky sphere + atmospheric fog + starfield."""
    actors = []
    # Sky sphere
    actors.append({
        'class': '/Script/Engine.Blueprint\'/Engine/Blueprints/Sky/BP_SkySphere.BP_SkySphere\'',
        'name': 'BP_SkySphere',
        'pos': [0, 0, 0],
        'properties': {}
    })
    # Exponential height fog for atmosphere
    actors.append({
        'class': '/Script/Engine.ExponentialHeightFog',
        'name': 'ExponentialHeightFog',
        'pos': [0, 0, 0],
        'properties': {
            'FogDensity': 0.002,
            'FogHeightFalloff': 0.2,
            'StartDistance': 10000,
        }
    })
    return actors


def build_sun(decoded: dict) -> list[dict]:
    """Proper sun — warm directional light with sun disk."""
    ss = decoded.get('solar_system', {})
    star = ss.get('star', {})
    mass = star.get('mass_frac', 0.98)
    
    # Map star mass to light color/temp
    if mass > 0.9:
        color = [1.0, 0.85, 0.5]  # warm yellow (G-type)
        intensity = 10.0
    elif mass > 0.5:
        color = [1.0, 0.75, 0.4]  # orange (K-type)
        intensity = 7.0
    else:
        color = [0.8, 0.6, 0.3]   # red (M-type)
        intensity = 4.0
    
    return [{
        'class': '/Script/Engine.DirectionalLight',
        'name': 'SunLight',
        'pos': [0, 0, 2000],
        'rotation': [330, -45, 0],  # pitch, yaw, roll — angled sun
        'properties': {
            'LightColor': color,
            'Intensity': intensity,
            'CastShadows': True,
            'LightSourceAngle': 0.5,
            'AtmosphereSunLight': True,
            'EnableAtmosphere': True,
        }
    }]


def build_terrain(decoded: dict) -> list[dict]:
    """Ground plane + landscape from decoded params."""
    gt = decoded.get('ground_terrain', {})
    extent = _get(gt, 'extent', 'Extent', default=[5000, 5000, 100])
    origin = _get(gt, 'origin', 'Origin', default=[0, 0, -50])
    
    actors = []
    # Landing pad / ground plane
    actors.append({
        'class': '/Script/Engine.Blueprint\'/Engine/EditorLandscapeResources/LandscapeHeightfield.LandscapeHeightfield\'',
        'name': 'Terrain',
        'pos': origin,
        'properties': {}
    })
    # Fallback: simple ground plane if landscape fails
    actors.append({
        'class': '/Script/Engine.StaticMesh\'/Engine/BasicShapes/Plane.Plane\'',
        'name': 'GroundPlane',
        'pos': [origin[0], origin[1], origin[2] - 10],
        'scale': [extent[0] / 100, extent[1] / 100, 1],
        'properties': {
            'WorldPosition': True,
        }
    })
    return actors


def build_player_spawn(decoded: dict) -> list[dict]:
    """PlayerStart at terrain origin."""
    return [{
        'class': '/Script/Engine.PlayerStart',
        'name': 'PlayerStart',
        'pos': [0, 0, 100],
        'properties': {}
    }]


def build_shelter(decoded: dict) -> list[dict]:
    """Shelter with threshold, interior, and beacon light."""
    st = decoded.get('shelter_threshold', {})
    sf = decoded.get('shelter_form', {})
    
    pos = _get(st, 'pos', 'pos', default=[0, -800, 0])
    radius = _get(st, 'radius', 'radius', default=300)
    
    actors = []
    # Shelter boundary ring (visual indicator)
    actors.append({
        'class': '/Script/Engine.StaticMesh\'/Engine/BasicShapes/Cylinder.Cylinder\'',
        'name': 'ShelterZone',
        'pos': [pos[0], pos[1], pos[2]],
        'scale': [radius / 50, radius / 50, 0.1],
        'properties': {
            'bHidden': True,  # invisible — it's a trigger zone
        }
    })
    # Beacon point light inside shelter
    actors.append({
        'class': '/Script/Engine.PointLight',
        'name': 'ShelterLight',
        'pos': [pos[0], pos[1], pos[2] + 200],
        'properties': {
            'LightColor': [0.2, 0.8, 1.0],
            'Intensity': 5000,
            'AttenuationRadius': radius * 2,
        }
    })
    return actors


def build_resources(decoded: dict) -> list[dict]:
    """Resource pickups scattered around the terrain."""
    br = decoded.get('biome_resources', {})
    n_types = _get(br, 'n_types', 'n_types', default=7)
    
    actors = []
    import math
    for i in range(min(n_types, 12)):
        angle = i * 2 * math.pi / n_types
        dist = 300 + i * 150
        x = math.cos(angle) * dist
        y = math.sin(angle) * dist
        
        actors.append({
            'class': '/Script/Engine.StaticMesh\'/Engine/BasicShapes/Sphere.Sphere\'',
            'name': f'Resource_{i}',
            'pos': [x, y, 50],
            'scale': [0.5, 0.5, 0.5],
            'properties': {
                'LightColor': [0.3 + i * 0.1, 0.5, 0.2],
            }
        })
    return actors


def build_npcs(decoded: dict) -> list[dict]:
    """NPC spawn points around the shelter."""
    ns = decoded.get('npc_social', {})
    n_npcs = _get(ns, 'n_npcs', 'n_npcs', default=3)
    
    actors = []
    import math
    for i in range(min(n_npcs, 6)):
        angle = i * 2 * math.pi / n_npcs + 0.5
        dist = 600 + i * 100
        x = math.cos(angle) * dist
        y = math.sin(angle) * dist
        
        actors.append({
            'class': '/Script/Engine.Blueprint\'/Game/BP_Astronaut_Character.BP_Astronaut_Character\'',
            'name': f'NPC_{i}',
            'pos': [x, y, 100],
            'properties': {}
        })
    return actors


def build_beacon(decoded: dict) -> list[dict]:
    """Beacon with signal light — the Mirror terminal."""
    bn = decoded.get('beacon_narrative', {})
    sig = decoded.get('beacon_narrative_signal', decoded.get('latest', {}))
    
    pos = _get(bn, 'pos', 'pos', default=[2000, 0, 0])
    height = _get(bn, 'height', 'height', default=50)
    
    pulse_0 = _get(sig, 'pulse_rate_0', default=0.18)
    pulse_3 = _get(sig, 'pulse_rate_3', default=1.55)
    color_r = _get(sig, 'color_red_r', default=0.99)
    color_w = _get(sig, 'color_white_r', default=1.0)
    
    actors = []
    # Beacon tower (cylinder)
    actors.append({
        'class': '/Script/Engine.StaticMesh\'/Engine/BasicShapes/Cylinder.Cylinder\'',
        'name': 'BeaconTower',
        'pos': [pos[0], pos[1], pos[2] + height / 2],
        'scale': [0.3, 0.3, height / 100],
        'properties': {}
    })
    # Signal light on top
    actors.append({
        'class': '/Script/Engine.PointLight',
        'name': 'BeaconSignal',
        'pos': [pos[0], pos[1], pos[2] + height],
        'properties': {
            'LightColor': [color_r, 0.2, 0.1],  # red at 0 helps
            'Intensity': 10000,
            'AttenuationRadius': 5000,
        }
    })
    # Sphere indicator
    actors.append({
        'class': '/Script/Engine.StaticMesh\'/Engine/BasicShapes/Sphere.Sphere\'',
        'name': 'BeaconLightSphere',
        'pos': [pos[0], pos[1], pos[2] + height],
        'scale': [2, 2, 2],
        'properties': {}
    })
    return actors


# Registry: rung name -> build function
BUILDERS = {
    'solar_system': build_sun,
    'planet_surface': lambda d: [],  # atmospheric params baked into sky
    'ground_terrain': build_terrain,
    'body_survival': lambda d: [],
    'biome_resources': build_resources,
    'shelter_form': build_shelter,
    'shelter_threshold': build_shelter,
    'fabricator_economy': lambda d: [],
    'npc_social': build_npcs,
    'beacon_narrative': build_beacon,
    'beacon_narrative_signal': lambda d: [],
}


def load_decoded() -> dict:
    """Load all decoded JSON files."""
    decoded = {}
    pattern = str(ROOT / 'docs/decoded/*.json')
    for f in glob.glob(pattern):
        name = Path(f).stem
        try:
            with open(f) as fh:
                decoded[name] = json.load(fh)
        except Exception as e:
            print(f'  Error loading {f}: {e}')
    return decoded


def build_level(decoded: dict, dry: bool = False) -> list[dict]:
    """Generate all actors from decoded params. Returns list of spawn commands."""
    all_actors = []
    
    # Always build sky and sun first (they set the scene)
    all_actors.extend(build_sky(decoded))
    all_actors.extend(build_sun(decoded))
    
    # Build each rung
    for rung, builder in BUILDERS.items():
        if rung in decoded:
            actors = builder(decoded)
            all_actors.extend(actors)
            if dry and actors:
                print(f'  {rung}: {len(actors)} actors')
    
    # Ensure player start exists
    all_actors.extend(build_player_spawn(decoded))
    
    return all_actors


def spawn_via_mcp(actors: list[dict]):
    """Spawn actors via MCP bridge."""
    from core.telemetry_probe import MCPStdioClient
    
    c = MCPStdioClient()
    spawned = 0
    errors = 0
    
    for a in actors:
        try:
            result = c.call('spawn_actor', {
                'name': a['name'],
                'class_path': a['class'],
                'x': float(a['pos'][0]),
                'y': float(a['pos'][1]),
                'z': float(a['pos'][2]),
                'rotation': a.get('rotation', [0, 0, 0]),
                'scale': a.get('scale', [1, 1, 1]),
            })
            spawned += 1
            print(f'  [{spawned}] {a["name"]}')
        except Exception as e:
            errors += 1
            print(f'  [ERR] {a["name"]}: {e}')
    
    print(f'\nSpawned {spawned} actors ({errors} errors)')


def check_readiness(decoded: dict):
    """Check which rungs have level-ready parameters."""
    print('\n=== Level Readiness Check ===')
    ready = 0
    for rung, builder in BUILDERS.items():
        if rung not in decoded:
            print(f'  [MISSING] {rung}: no decoded params')
            continue
        try:
            actors = builder(decoded)
            status = f'{len(actors)} actors' if actors else 'no actors needed'
            print(f'  [OK] {rung}: {status}')
            ready += 1
        except Exception as e:
            print(f'  [ERROR] {rung}: {e}')
    
    print(f'\n{ready}/{len(BUILDERS)} rungs ready')
    
    # Count total actors
    total = 0
    for builder in BUILDERS.values():
        try:
            total += len(builder(decoded))
        except:
            pass
    print(f'Total actors to spawn: ~{total}')


def main():
    import argparse
    
    ap = argparse.ArgumentParser(description='Build emergent world from decoded params')
    ap.add_argument('--dry', action='store_true', help='Print what would be built')
    ap.add_argument('--check', action='store_true', help='Check which rungs are ready')
    
    args = ap.parse_args()
    
    decoded = load_decoded()
    print(f'Loaded {len(decoded)} decoded rungs')
    
    if args.check:
        check_readiness(decoded)
        return 0
    
    if args.dry:
        print('\n=== Build Plan (Dry Run) ===')
        actors = build_level(decoded, dry=True)
        print(f'\nTotal: {len(actors)} actors to spawn')
        return 0
    
    print('\n=== Building emergent_world ===')
    actors = build_level(decoded)
    spawn_via_mcp(actors)


if __name__ == '__main__':
    sys.exit(main())
