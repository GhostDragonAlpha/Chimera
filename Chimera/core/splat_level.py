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

# Tissue/color map for every game element
MATERIALS = {
    'ground':  {'albedo': (0.55, 0.47, 0.38), 'roughness': 0.95, 'alpha': 1.0, 'subsurface': 0.0},
    'sand':    {'albedo': (0.65, 0.57, 0.40), 'roughness': 0.90, 'alpha': 1.0, 'subsurface': 0.0},
    'rock':    {'albedo': (0.32, 0.30, 0.28), 'roughness': 0.85, 'alpha': 1.0, 'subsurface': 0.0},
    'resource':{'albedo': (0.40, 0.60, 0.30), 'roughness': 0.70, 'alpha': 1.0, 'subsurface': 0.1},
    'metal':   {'albedo': (0.56, 0.57, 0.58), 'roughness': 0.35, 'alpha': 1.0, 'subsurface': 0.0},
    'shelter': {'albedo': (0.50, 0.55, 0.65), 'roughness': 0.60, 'alpha': 1.0, 'subsurface': 0.0},
    'npc':     {'albedo': (0.80, 0.62, 0.47), 'roughness': 0.70, 'alpha': 0.88, 'subsurface': 0.55},
    'beacon':  {'albedo': (0.99, 0.20, 0.10), 'roughness': 0.50, 'alpha': 1.0, 'subsurface': 0.0},
    'sun':     {'albedo': (1.00, 0.85, 0.50), 'roughness': 0.20, 'alpha': 1.0, 'subsurface': 0.0},
}


def emit_splat_cloud(pos, material, count=1, spread=1.0, seed=42):
    """Emit a cloud of Gaussian splats at position with material properties.
    Returns a splat dict compatible with splat_gpu.rasterize() and splat_to_ue5."""
    rng = np.random.RandomState(seed)
    mat = MATERIALS[material]
    
    n = max(count, 1)
    pos_arr = np.tile(pos, (n, 1)) + rng.randn(n, 3) * spread
    norm = np.zeros((n, 3))
    norm[:, 2] = 1.0  # upward
    
    # Random orientation in tangent plane
    t1 = np.zeros((n, 3))
    t1[:, 0] = 1.0
    t2 = np.zeros((n, 3))
    t2[:, 1] = 1.0
    
    # Covariance: isotropic disk
    scale = spread * 0.5
    cov = np.zeros((n, 3, 3))
    cov[:, 0, 0] = scale ** 2
    cov[:, 1, 1] = scale ** 2
    cov[:, 2, 2] = (scale * 0.3) ** 2
    
    return {
        'pos': pos_arr.astype(np.float64),
        'normal': norm.astype(np.float64),
        'cov': cov.astype(np.float64),
        'albedo': np.tile(mat['albedo'], (n, 1)).astype(np.float64),
        'roughness': np.full(n, mat['roughness'], dtype=np.float64),
        'alpha': np.full(n, mat['alpha'], dtype=np.float64),
        'subsurface': np.full(n, mat['subsurface'], dtype=np.float64),
        'metallic': np.zeros(n, dtype=np.float64),
    }


def build_ground_terrain(decoded, extent=2000, density=5000):
    """Build the ground entirely from splats."""
    print('  Building ground terrain...')
    gt = decoded.get('ground_terrain', {})
    origin = gt.get('origin', (0, 0, -50)) if isinstance(gt, dict) else (0, 0, -50)
    
    # Grid of splats across the ground plane
    side = int(math.sqrt(density))
    xs = np.linspace(-extent/2, extent/2, side)
    ys = np.linspace(-extent/2, extent/2, side)
    xx, yy = np.meshgrid(xs, ys)
    
    positions = np.stack([xx.ravel(), yy.ravel(), np.full(side*side, origin[2])], axis=1)
    
    # Mix sand and rock
    n = len(positions)
    mat = np.random.RandomState(0).choice(['sand', 'rock', 'ground'], size=n, p=[0.4, 0.3, 0.3])
    
    all_splats = []
    for m in set(mat):
        mask = mat == m
        pts = positions[mask]
        chunk = emit_splat_cloud(pts.mean(axis=0), m, count=len(pts), spread=extent/side*0.6)
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
        from core.splat_to_ue5 import write_splat_glb, quad_cloud
        from core.matter_items import frame_of
        center, radius = frame_of(world)
        glb_path = OUT_DIR / 'splat_world.glb'
        try:
            # Build quad mesh and write GLB
            verts, colors = quad_cloud(world, scale=1.0, tangent_scale=1.0)
            write_splat_glb(str(glb_path), verts, colors, soft_edge=False)
            print(f'GLB exported: {glb_path} ({len(verts):,} verts)')
        except Exception as e:
            print(f'GLB export failed: {e}')


if __name__ == '__main__':
    sys.exit(main())
