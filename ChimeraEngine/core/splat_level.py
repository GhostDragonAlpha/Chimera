"""splat_level — builds the emergent world ENTIRELY from Gaussian splats.

Everything in the game is a Gaussian splat:
  - Ground terrain = Cellular Potts grid → surface voxels → splats
  - Resources = small splat clusters with material properties
  - Shelter = matter-assembled walls → splats
  - NPCs = Matter-grown bodies → splats
  - Beacon = splat tower with signal light
  - Sun = warm splat cloud

No static meshes. No triangles. No UE5 primitives. The splat is the atom.

Usage:
    python -m core.splat_level                    # build entire splat world
    python -m core.splat_level --ground-only       # just the ground
    python -m core.splat_level --beacon-only       # just the beacon
"""

from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DECODED_DIR = ROOT / 'docs/decoded'
OUT_DIR = ROOT / 'Saved' / 'SplatEmit'

# Splat type constructors (from splat_types)
from core.splat_types import (
    SPLAT_TYPES,
    emit_surface, emit_fiber, emit_point,
    emit_beam, emit_cloud, emit_glow, emit_shell
)

# Load material splat compositions from the library
with open(ROOT / 'Chimera/docs/rep_batteries/matter_library.json') as f:
    _MATTER_LIB = json.load(f)


def _get_optical(material_name):
    """Get optical properties for a material from the library."""
    mat = _MATTER_LIB['materials'].get(material_name)
    if mat is None:
        return {'albedo': (0.5, 0.5, 0.5), 'roughness': 0.5, 'alpha': 1.0, 'subsurface': 0.0}
    app = mat.get('appearance', {})
    alb = app.get('albedo_mean_rgb', [0.5, 0.5, 0.5])
    if isinstance(alb, list):
        alb = tuple(alb)
    return {
        'albedo': alb,
        'roughness': app.get('roughness_mean', 0.5),
        'alpha': app.get('alpha', 1.0),
        'subsurface': app.get('subsurface_strength', 0.0),
        'metallic': app.get('metallic', 0.0),
    }


def _get_composition(material_name):
    """Get splat composition layers for a material."""
    mat = _MATTER_LIB['materials'].get(material_name)
    if mat is None:
        return [{'type': 'surface', 'weight': 1.0, 'scale': 1.0}]
    comp = mat.get('splat_composition', {})
    return comp.get('layers', [{'type': 'surface', 'weight': 1.0, 'scale': 1.0}])


def emit_splat_cloud(pos, material, count=1, spread=1.0, seed=42,
                      fiber_dir=None):
    """Emit Gaussian splats using the material's splat composition.
    
    Reads the material's splat_composition from the matter library
    and emits the correct combination of splat types (surface, fiber,
    point, shell, etc.) with correct weights.
    """
    rng = np.random.RandomState(seed)
    optical = _get_optical(material)
    layers = _get_composition(material)
    
    n = max(count, 1)
    
    # Distribute splats across layers by weight
    total_weight = sum(l['weight'] for l in layers)
    
    all_splats = []
    for layer in layers:
        layer_n = max(1, int(n * layer['weight'] / total_weight))
        if layer_n == 0:
            continue
        
        # Positions: jittered around center
        lpos = np.tile(pos, (layer_n, 1)) + rng.randn(layer_n, 3) * spread * layer.get('scale', 1.0)
        
        # Normals: upward by default
        norm = np.zeros((layer_n, 3))
        norm[:, 2] = 1.0
        
        # Build covariance for this layer's splat type
        stype = layer['type']
        if stype == 'surface':
            cov = emit_surface(norm, tangent_scale=spread * layer.get('scale', 1.0) * 0.5,
                               normal_scale=spread * 0.15)
        elif stype == 'fiber':
            fd = fiber_dir if fiber_dir is not None else norm
            if len(fd.shape) == 1:
                fd = np.tile(fd, (layer_n, 1))
            cov = emit_fiber(norm, tangent_scale=spread * 0.5,
                             normal_scale=spread * 0.15,
                             fiber_dir=fd, elongation=layer.get('elongation', 3.0))
        elif stype == 'point':
            cov = emit_point(lpos, radius=spread * layer.get('scale', 0.3))
        elif stype == 'shell':
            cov = emit_shell(lpos, norm, thickness=layer.get('thickness', 0.2),
                             spread=spread * layer.get('scale', 1.0) * 0.5)
        elif stype == 'beam':
            fd = fiber_dir if fiber_dir is not None else norm
            if len(fd.shape) == 1:
                fd = np.tile(fd, (layer_n, 1))
            cov = emit_beam(fd, length=layer.get('length', spread * 2),
                           thickness=layer.get('thickness', spread * 0.1))
        elif stype == 'cloud':
            cov = emit_cloud(lpos, radius=spread * layer.get('scale', 2.0))
        elif stype == 'glow':
            cov = emit_glow(lpos, radius=spread * layer.get('scale', 0.5))
        else:
            # Fallback: isotropic
            cov = emit_point(lpos, radius=spread * 0.3)
        
        all_splats.append({
            'pos': lpos.astype(np.float64),
            'normal': norm.astype(np.float64),
            'cov': cov.astype(np.float64) if isinstance(cov, np.ndarray) else cov,
            'albedo': np.tile(optical['albedo'], (layer_n, 1)).astype(np.float64),
            'roughness': np.full(layer_n, optical['roughness'], dtype=np.float64),
            'alpha': np.full(layer_n, optical['alpha'], dtype=np.float64),
            'subsurface': np.full(layer_n, optical['subsurface'], dtype=np.float64),
            'metallic': np.full(layer_n, optical.get('metallic', 0.0), dtype=np.float64),
        })
    
    # Merge layers
    out = {}
    for k in ['pos', 'normal', 'cov', 'albedo', 'roughness', 'alpha', 'subsurface', 'metallic']:
        arrays = [s[k] for s in all_splats if s is not None]
        out[k] = np.concatenate(arrays, axis=0) if arrays else np.zeros((0, 3) if k in ('pos','normal','cov','albedo') else 0)
    return out


def build_ground_terrain(decoded, extent=2000, density=200000):
    """Build the ground entirely from splats at high density."""
    print(f'  Building ground terrain ({density:,} splats)...')
    gt = decoded.get('ground_terrain', {})
    origin = gt.get('origin', (0, 0, -50)) if isinstance(gt, dict) else (0, 0, -50)
    
    rng = np.random.RandomState(0)
    
    # Jittered grid for better ground coverage
    side = int(math.sqrt(density))
    spacing = extent / side
    xs = np.linspace(-extent/2 + spacing/2, extent/2 - spacing/2, side)
    ys = np.linspace(-extent/2 + spacing/2, extent/2 - spacing/2, side)
    xx, yy = np.meshgrid(xs, ys)
    
    # Add jitter
    xx += rng.uniform(-spacing*0.3, spacing*0.3, size=xx.shape)
    yy += rng.uniform(-spacing*0.3, spacing*0.3, size=yy.shape)
    
    positions = np.stack([xx.ravel(), yy.ravel(), np.full(side*side, origin[2])], axis=1)
    n = len(positions)
    
    # Layer materials: sand (base), rock (clusters), ground (sandy mix)
    mat = rng.choice(['sand', 'rock', 'ground'], size=n, p=[0.5, 0.2, 0.3])
    
    all_splats = []
    for m in set(mat):
        mask = mat == m
        pts = positions[mask]
        # Each splat covers a small area
        spread_val = spacing * 0.45
        chunk = emit_splat_cloud(pts.mean(axis=0), m, count=len(pts), spread=spread_val, seed=int(rng.randint(0,1000)))
        all_splats.append(chunk)
    
    return _merge(all_splats)


def build_resources(decoded):
    """Scatter resource splat clusters."""
    print('  Building resources...')
    br = decoded.get('biome_resources', {})
    n_types = br.get('n_types', 7) if isinstance(br, dict) else 7
    n_types = min(int(n_types), 12)
    
    all_splats = []
    for i in range(n_types):
        angle = i * 2 * math.pi / n_types
        dist = 300 + i * 150
        x = math.cos(angle) * dist
        y = math.sin(angle) * dist
        cluster = emit_splat_cloud(np.array([x, y, 50]), 'resource', count=20, spread=30, seed=i)
        all_splats.append(cluster)
    
    return _merge(all_splats)


def build_shelter(decoded):
    """Build shelter as a ring of splats."""
    print('  Building shelter...')
    st = decoded.get('shelter_threshold', {})
    pos = st.get('pos', (0, -800, 0)) if isinstance(st, dict) else (0, -800, 0)
    radius = st.get('radius', 300) if isinstance(st, dict) else 300
    
    all_splats = []
    # Ring of shelter splats
    n_ring = 60
    for i in range(n_ring):
        angle = i * 2 * math.pi / n_ring
        x = pos[0] + math.cos(angle) * radius
        y = pos[1] + math.sin(angle) * radius
        cluster = emit_splat_cloud(np.array([x, y, pos[2] + 50]), 'shelter', count=5, spread=20, seed=i)
        all_splats.append(cluster)
    
    # Roof
    roof = emit_splat_cloud(np.array([pos[0], pos[1], pos[2] + 200]), 'shelter', count=100, spread=radius*0.7)
    all_splats.append(roof)
    
    return _merge(all_splats)


def build_npcs(decoded):
    """Build NPC bodies entirely from splats."""
    print('  Building NPCs...')
    ns = decoded.get('npc_social', {})
    n_npcs = ns.get('n_npcs', 3) if isinstance(ns, dict) else 3
    n_npcs = min(int(n_npcs), 6)
    
    all_splats = []
    for i in range(n_npcs):
        angle = i * 2 * math.pi / n_npcs + 0.5
        dist = 600 + i * 100
        x = math.cos(angle) * dist
        y = math.sin(angle) * dist
        
        # Body: vertical column of splats
        for z in range(5):
            body = emit_splat_cloud(np.array([x, y, 50 + z * 30]), 'npc', count=10, spread=15, seed=i*10+z)
            all_splats.append(body)
    
    return _merge(all_splats)


def build_beacon(decoded):
    """Build the beacon entirely from splats."""
    print('  Building beacon...')
    bn = decoded.get('beacon_narrative', {})
    sig = decoded.get('beacon_narrative_signal', decoded.get('latest', {}))
    
    pos = bn.get('pos', (2000, 0, 0)) if isinstance(bn, dict) else (2000, 0, 0)
    height = bn.get('height', 50) if isinstance(bn, dict) else 50
    
    all_splats = []
    # Tower: vertical column
    for z in range(int(height / 20)):
        tower = emit_splat_cloud(np.array([pos[0], pos[1], pos[2] + z * 20]), 'beacon', count=8, spread=10, seed=z)
        all_splats.append(tower)
    
    # Signal light on top
    light = emit_splat_cloud(np.array([pos[0], pos[1], pos[2] + height]), 'beacon', count=100, spread=30, seed=999)
    all_splats.append(light)
    
    return _merge(all_splats)


def build_sun(decoded):
    """Build the sun as a warm splat cloud."""
    print('  Building sun...')
    ss = decoded.get('solar_system', {})
    star = ss.get('star', {}) if isinstance(ss, dict) else {}
    mass = star.get('mass_frac', 0.98) if isinstance(star, dict) else 0.98
    
    # Warm glow at Z=2000
    sun = emit_splat_cloud(np.array([0, 0, 2000]), 'sun', count=500, spread=200, seed=0)
    return sun


def _merge(splat_list):
    """Merge a list of splat dicts into one."""
    if not splat_list:
        return None
    keys = ['pos', 'normal', 'cov', 'albedo', 'roughness', 'alpha', 'subsurface', 'metallic']
    out = {}
    for k in keys:
        arrays = [s[k] for s in splat_list if s is not None and k in s]
        out[k] = np.concatenate(arrays, axis=0) if arrays else np.zeros((0, 3) if k in ('pos','normal','cov','albedo') else 0)
    return out


def load_decoded():
    decoded = {}
    for f in DECODED_DIR.glob('*.json'):
        try:
            decoded[f.stem] = json.load(open(f))
        except:
            pass
    return decoded


def build_all(parts=None):
    """Build the complete splat world."""
    decoded = load_decoded()
    print(f'Loaded {len(decoded)} decoded rungs')
    
    builders = {
        'sun': lambda: build_sun(decoded),
        'ground': lambda: build_ground_terrain(decoded),
        'resources': lambda: build_resources(decoded),
        'shelter': lambda: build_shelter(decoded),
        'npcs': lambda: build_npcs(decoded),
        'beacon': lambda: build_beacon(decoded),
    }
    
    if parts:
        names = [p for p in parts if p in builders]
    else:
        names = list(builders.keys())
    
    all_splats = []
    for name in names:
        splats = builders[name]()
        if splats and len(splats['pos']) > 0:
            all_splats.append(splats)
            print(f'  {name}: {len(splats["pos"]):,} splats')
    
    world = _merge(all_splats)
    if world:
        n = len(world['pos'])
        print(f'\nTotal: {n:,} splats')
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        path = OUT_DIR / 'splat_world.npz'
        np.savez_compressed(path, **{k: world[k] for k in world})
        print(f'Saved to {path}')
    
    return world


def render_preview(world):
    """Render the splat world from a high angle."""
    from core.matter_items import frame_of, CAM
    from core.splat_gpu import rasterize, available
    
    if not available():
        print('GPU rasterizer unavailable')
        return
    
    center, radius = frame_of(world)
    print(f'Frame: center={center} radius={radius:.0f}')
    
    # Top-down overview
    _ = rasterize(world, center, radius, 0, 90, 110, 45, w=1024, h=1024)
    t0 = time.time()
    img = rasterize(world, center, radius, 0, 90, 110, 45, w=1024, h=1024)
    dt = time.time() - t0
    
    from PIL import Image
    preview = (np.clip(img, 0, 1) * 255).astype(np.uint8)
    path = OUT_DIR / 'splat_world_preview.png'
    Image.fromarray(preview, 'RGB').save(path)
    print(f'Rendered {dt*1000:.0f}ms -> {path}')


def main():
    import argparse
    ap = argparse.ArgumentParser(description='Build splat-based emergent world')
    ap.add_argument('--sun-only', action='store_true')
    ap.add_argument('--ground-only', action='store_true')
    ap.add_argument('--beacon-only', action='store_true')
    ap.add_argument('--preview', action='store_true', help='Render a preview image')
    ap.add_argument('--save-glb', action='store_true', help='Export as GLB for UE5')
    
    args = ap.parse_args()
    
    parts = []
    if args.sun_only: parts.append('sun')
    if args.ground_only: parts.append('ground')
    if args.beacon_only: parts.append('beacon')
    
    world = build_all(parts if parts else None)
    
    if world and args.preview:
        render_preview(world)
    
    if world and args.save_glb:
        from core.splat_mesh import write_splat_glb
        from core.matter_items import frame_of
        center, radius = frame_of(world)
        glb_path = OUT_DIR / 'splat_world.glb'
        try:
            # Build quad mesh and write GLB. NOTE 2026-08-25: this branch had been dead by
            # signature since tb-0183 -- quad_cloud returns a Scene, not (verts, colors), and
            # write_splat_glb takes (splats, scale, path); the except below swallowed it.
            write_splat_glb(world, 1.0, str(glb_path), tangent_scale=1.0, soft_edge=False)
            print(f'GLB exported: {glb_path} ({len(world["pos"]) * 4:,} verts)')
        except Exception as e:
            print(f'GLB export failed: {e}')


if __name__ == '__main__':
    sys.exit(main())
