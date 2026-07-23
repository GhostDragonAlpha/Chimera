#!/usr/bin/env python3
"""Process additional materials to expand the genetics library."""

import sys
from pathlib import Path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from Construction.export_genome import cluster_genomes, merge_specimens, FEATURES
from Chimera.core.progeny import spawn_children, heritability
from Chimera.core.render_world import render_orbit
import numpy as np
import json

def emit_fiber(dirs, tangent_scale, normal_scale, fiber_dir=None, elongation=1.0):
    n = len(dirs)
    cov = np.zeros((n, 3, 3))
    for i in range(n):
        d = dirs[i]
        T = np.array([
            [d[1], -d[2], d[0]],
            [d[2], d[0], -d[1]],
            [d[0], d[1], d[2]]
        ]) / np.linalg.norm(d) + 1e-9
        cov[i] = T @ np.diag([tangent_scale, normal_scale, tangent_scale]) @ T.T
    return cov

def emit_point(pos, radius):
    n = len(pos)
    cov = np.eye(3) * (radius ** 2)
    return np.tile(cov[None], (n, 1, 1))

def emit_surface(dirs, tangent_scale, normal_scale):
    n = len(dirs)
    cov = np.zeros((n, 3, 3))
    for i in range(n):
        d = dirs[i] / (np.linalg.norm(dirs[i]) + 1e-9)
        if abs(d[0]) > 0.9:
            t1 = np.array([0, 1, 0])
        else:
            t1 = np.cross(d, [1, 0, 0])
            t1 /= np.linalg.norm(t1)
        t2 = np.cross(d, t1)
        t2 /= np.linalg.norm(t2)
        M = np.column_stack([t1, t2, d])
        cov[i] = M @ np.diag([tangent_scale, tangent_scale, normal_scale]) @ M.T
    return cov

def build_child(child: dict, form: str = 'tuft', n_splats: int = 400) -> dict:
    s = child['sampled']
    rng = np.random.default_rng(child['seed'])
    scale = s['_scale']
    size = max(float(s.get('size', 0.02)), 1e-4)

    if form == 'tuft':
        n_blade = max(6, int(14 * scale))
        per = max(3, n_splats // n_blade)
        P, D = [], []
        for _ in range(n_blade):
            a = rng.uniform(0, 2 * np.pi)
            lean = rng.uniform(0.15, 0.75)
            L = scale * rng.uniform(0.6, 1.4)
            t = np.linspace(0, 1, per)[:, None]
            tip = np.array([np.cos(a) * lean, np.sin(a) * lean, 1.0]) * L
            arc = np.array([0, 0, -0.25 * L])
            pts = t * tip + (t ** 2) * arc
            P.append(pts)
            d = np.tile(tip / (np.linalg.norm(tip) + 1e-9), (per, 1))
            D.append(d)
        pos = np.vstack(P); dirs = np.vstack(D)
        cov = emit_fiber(dirs, tangent_scale=size * 6, normal_scale=size * 1.2, fiber_dir=dirs, elongation=4.0)

    elif form == 'clump':
        pos = rng.standard_normal((n_splats, 3)) * 0.35 * scale
        pos[:, 2] = np.abs(pos[:, 2])
        dirs = pos / (np.linalg.norm(pos, axis=1, keepdims=True) + 1e-9)
        cov = emit_point(pos, radius=size * 3 * scale)

    else:
        pos = rng.standard_normal((n_splats, 3)) * np.array([0.5, 0.5, 0.12]) * scale
        dirs = np.zeros_like(pos); dirs[:, 2] = 1.0
        cov = emit_surface(dirs, tangent_scale=size * 5 * scale, normal_scale=size * 0.6)

    cy, sy = np.cos(s['_yaw']), np.sin(s['_yaw'])
    Rz = np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1.0]])
    cl, sl = np.cos(s['_lean']), np.sin(s['_lean'])
    Rx = np.array([[1, 0, 0], [0, cl, -sl], [0, sl, cl]])
    R = Rz @ Rx
    pos = pos @ R.T
    cov = R @ cov @ R.T

    rgb = np.clip([s.get('R', 0.5), s.get('G', 0.5), s.get('B', 0.5)], 0, 1)
    alpha = float(np.clip(s.get('opacity', 0.9), 0.05, 1.0))
    n = len(pos)
    return {
        'pos': pos, 'normal': dirs, 'cov': cov,
        'albedo': np.tile(rgb, (n, 1)),
        'roughness': np.full(n, float(np.clip(s.get('aniso', 0.5), 0, 1))),
        'alpha': np.full(n, alpha),
        'subsurface': np.zeros(n),
        'metallic': np.zeros(n),
        '_form': form, '_child': child['index'], '_honest': child.get('honest', True),
    }

def scatter(children: list, count: int = 500, area: float = 100.0, seed: int = 0,
            height_fn=None, jitter_scale: float = 0.25) -> dict:
    rng = np.random.default_rng(seed)
    xy = rng.uniform(-area, area, (count, 2))
    z = np.zeros(count) if height_fn is None else np.asarray(
        [float(height_fn(float(a), float(b))) for a, b in xy])
    pos = np.column_stack([xy, z])
    scales = 1.0 + rng.standard_normal(count) * jitter_scale
    return place(children, pos, np.clip(scales, 0.3, 2.2), rng.uniform(0, 2 * np.pi, count))

def place(children: list, positions, scales=None, yaws=None) -> dict:
    positions = np.asarray(positions, dtype=np.float64).reshape(-1, 3)
    M = len(positions)
    scales = np.ones(M) if scales is None else np.asarray(scales, dtype=float).reshape(M)
    yaws = np.zeros(M) if yaws is None else np.asarray(yaws, dtype=float).reshape(M)
    if not children:
        raise ValueError('no children to place')

    keys = ('pos', 'normal', 'cov', 'albedo', 'roughness', 'alpha', 'subsurface', 'metallic')
    acc = {k: [] for k in keys}
    for i in range(M):
        kid = children[i % len(children)]
        k = float(scales[i])
        cy, sy = np.cos(yaws[i]), np.sin(yaws[i])
        R = np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1.0]])
        acc['pos'].append(kid['pos'] @ R.T * k + positions[i])
        acc['normal'].append(kid['normal'] @ R.T)
        acc['cov'].append((R @ kid['cov'] @ R.T) * (k * k))
        for f in ('albedo', 'roughness', 'alpha', 'subsurface', 'metallic'):
            acc[f].append(kid[f])
    out = {k: np.concatenate(v, axis=0) for k, v in acc.items()}
    out['_instances'] = M
    out['_unique_children'] = len(children)
    return out

def match_clusters(genomes_a, genomes_b, max_matches=3):
    feature_names = ['size', 'aniso', 'R', 'G', 'B', 'opacity']
    clusters_a = []
    for name, data in genomes_a.items():
        vec = np.array([data['features'][f]['mean'] for f in feature_names])
        clusters_a.append((name, vec, data))
    clusters_b = []
    for name, data in genomes_b.items():
        vec = np.array([data['features'][f]['mean'] for f in feature_names])
        clusters_b.append((name, vec, data))
    all_vecs = np.vstack([c[1] for c in clusters_a + clusters_b])
    mins = all_vecs.min(axis=0)
    maxs = all_vecs.max(axis=0)
    range_ = maxs - mins
    range_[range_ == 0] = 1
    normalized_a = np.array([c[1] / range_ for c in clusters_a])
    normalized_b = np.array([c[1] / range_ for c in clusters_b])
    distances = np.linalg.norm(normalized_a[:, None, :] - normalized_b[None, :, :], axis=2)
    matches = []
    used_a, used_b = set(), set()
    for _ in range(min(max_matches, len(clusters_a), len(clusters_b))):
        mask = np.ones(distances.shape, dtype=bool)
        mask[np.ix_(list(used_a), list(used_b))] = False
        if not mask.any():
            break
        idx = np.argmin(distances[mask])
        i, j = np.unravel_index(idx, mask.shape)
        matches.append((clusters_a[i][0], clusters_b[j][0], distances[i, j]))
        used_a.add(i)
        used_b.add(j)
    return matches

def process_material(scan1_path, scan2_path, material_name, n_children=12, n_splats=400):
    print(f"\n{'='*60}")
    print(f"Processing: {material_name}")
    print(f"{'='*60}")
    
    print(f"Loading {scan1_path}...")
    genomes1 = cluster_genomes(str(scan1_path), k=8, sample=100000)
    print(f"  Found {len(genomes1)} clusters")
    
    print(f"\nLoading {scan2_path}...")
    genomes2 = cluster_genomes(str(scan2_path), k=8, sample=100000)
    print(f"  Found {len(genomes2)} clusters")
    
    matches = match_clusters(genomes1, genomes2, max_matches=3)
    print(f"\nBest matching cluster pairs:")
    for name_a, name_b, dist in matches:
        print(f"  {name_a} (scan1) <-> {name_b} (scan2): distance={dist:.4f}")
    
    if len(matches) < 2:
        print("ERROR: Need at least 2 good matches to merge specimens")
        return None
    
    specimens = []
    for name_a, name_b, _ in matches[:2]:
        specimen1 = genomes1[name_a].copy()
        specimen2 = genomes2[name_b].copy()
        specimen1['_source'] = str(scan1_path)
        specimen2['_source'] = str(scan2_path)
        specimens.append(specimen1)
        specimens.append(specimen2)
    
    print(f"\nMerging {len(specimens)} specimens into class genome...")
    class_genome = merge_specimens(specimens, name=material_name)
    
    h2 = heritability(class_genome)
    print("\nHeritability (h²) per trait:")
    for feat, val in h2.items():
        if val is not None:
            print(f"  {feat}: {val:.4f}")
    
    print(f"\nGenerating {n_children} children...")
    kids_spec = spawn_children(class_genome, n=n_children, spread=1.0)
    
    print("Building child geometries...")
    kids = [build_child(k, form='tuft', n_splats=n_splats) for k in kids_spec]
    
    scene = scatter(kids, count=200, area=10.0, seed=42)
    print(f"  Placed {scene['_instances']} instances of {scene['_unique_children']} unique children")
    
    out_path = Path(f'Saved/SplatEmit/{material_name}_children.png')
    print(f"\nRendering to {out_path}...")
    render_orbit(scene, out_path=str(out_path), n_views=6, elev_deg=12.0)
    
    genomes_file = Path('Chimera/docs/matter/recovered_genomes.json')
    if genomes_file.exists():
        with open(genomes_file, 'r') as f:
            payload = json.load(f)
    else:
        payload = {}
    
    payload.setdefault("genomes", {}).update({material_name: class_genome})
    payload["_provenance"] = "Merged from real scans via genetics pipeline"
    
    with open(genomes_file, 'w') as f:
        json.dump(payload, f, indent=2)
    print(f"\nSaved class genome to {genomes_file}")
    
    return {
        'material': material_name,
        'class_genome': class_genome,
        'heritability': h2,
        'children_count': n_children,
        'render_path': str(out_path),
        'matches': matches[:2]
    }

def main():
    materials = [
        {
            'name': 'garden_plants',
            'scan1': 'WorldModel/training_data/garden.splat',
            'scan2': 'WorldModel/training_data/downloads/dyl/garden-7k.splat'
        },
        {
            'name': 'treehill_wood',
            'scan1': 'WorldModel/training_data/treehill.splat',
            'scan2': 'WorldModel/training_data/downloads/treehill.splat'
        },
        {
            'name': 'plush_fabric',
            'scan1': 'WorldModel/training_data/downloads/plush.splat',
            'scan2': 'WorldModel/training_data/downloads/nike.splat'  # Both fabric-like
        },
        {
            'name': 'truck_metallic',
            'scan1': 'WorldModel/training_data/downloads/truck.splat',
            'scan2': 'WorldModel/training_data/downloads/train.splat'  # Both metallic vehicles
        }
    ]
    
    results = []
    for material in materials:
        try:
            result = process_material(
                material['scan1'],
                material['scan2'],
                material['name'],
                n_children=12,
                n_splats=400
            )
            if result:
                results.append(result)
        except Exception as e:
            print(f"ERROR processing {material['name']}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*60)
    print("PIPELINE COMPLETE - SUMMARY")
    print("="*60)
    for res in results:
        print(f"\n{res['material']}:")
        print(f"  Heritability range: {min(res['heritability'].values()):.3f} - {max(res['heritability'].values()):.3f}")
        print(f"  Children rendered: {res['children_count']}")
        print(f"  Render path: {res['render_path']}")
    
    print(f"\nTotal materials processed: {len(results)}")
    print("All class genomes saved to Chimera/docs/matter/recovered_genomes.json")

if __name__ == '__main__':
    main()
