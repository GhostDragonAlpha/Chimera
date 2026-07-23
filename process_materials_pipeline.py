#!/usr/bin/env python3
"""Process multiple materials through the genetics pipeline: scan → class genome → children → render."""

import sys
from pathlib import Path
# Add both project root and Chimera directory to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'Chimera'))

import numpy as np
from Construction.export_genome import cluster_genomes, merge_specimens, FEATURES
from Chimera.core.progeny import spawn_children, build_child, scatter, place
from Chimera.core.render_world import render_orbit
import json

def match_clusters(genomes_a, genomes_b, max_matches=3):
    """Match clusters from two scans by feature similarity."""
    feature_names = ['size', 'aniso', 'R', 'G', 'B', 'opacity']
    
    # Build feature vectors for each cluster
    clusters_a = []
    for name, data in genomes_a.items():
        vec = np.array([data['features'][f]['mean'] for f in feature_names])
        clusters_a.append((name, vec, data))
    
    clusters_b = []
    for name, data in genomes_b.items():
        vec = np.array([data['features'][f]['mean'] for f in feature_names])
        clusters_b.append((name, vec, data))
    
    # Normalize features to [0,1] for distance calculation
    all_vecs = np.vstack([c[1] for c in clusters_a + clusters_b])
    mins = all_vecs.min(axis=0)
    maxs = all_vecs.max(axis=0)
    range_ = maxs - mins
    range_[range_ == 0] = 1
    
    normalized_a = np.array([c[1] / range_ for c in clusters_a])
    normalized_b = np.array([c[1] / range_ for c in clusters_b])
    
    # Compute pairwise distances
    distances = np.linalg.norm(normalized_a[:, None, :] - normalized_b[None, :, :], axis=2)
    
    # Find best matches (greedy assignment)
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
    """Process two scans of the same material into a class genome and render children."""
    print(f"\n{'='*60}")
    print(f"Processing: {material_name}")
    print(f"{'='*60}")
    
    # Load both scans
    print(f"Loading {scan1_path}...")
    genomes1 = cluster_genomes(str(scan1_path), k=8, sample=100000)
    print(f"  Found {len(genomes1)} clusters")
    
    print(f"\nLoading {scan2_path}...")
    genomes2 = cluster_genomes(str(scan2_path), k=8, sample=100000)
    print(f"  Found {len(genomes2)} clusters")
    
    # Match clusters
    matches = match_clusters(genomes1, genomes2, max_matches=3)
    print(f"\nBest matching cluster pairs:")
    for name_a, name_b, dist in matches:
        print(f"  {name_a} (scan1) <-> {name_b} (scan2): distance={dist:.4f}")
    
    if len(matches) < 2:
        print("ERROR: Need at least 2 good matches to merge specimens")
        return None
    
    # Extract matched specimens
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
    
    # Print heritability
    from Chimera.core.progeny import heritability
    h2 = heritability(class_genome)
    print("\nHeritability (h²) per trait:")
    for feat, val in h2.items():
        if val is not None:
            print(f"  {feat}: {val:.4f}")
    
    # Generate children from class genome
    print(f"\nGenerating {n_children} children...")
    kids_spec = spawn_children(class_genome, n=n_children, spread=1.0)
    
    # Build child splat clouds
    print("Building child geometries...")
    kids = [build_child(k, form='tuft', n_splats=n_splats) for k in kids_spec]
    
    # Scatter children over area
    scene = scatter(kids, count=200, area=10.0, seed=42)
    print(f"  Placed {scene['_instances']} instances of {scene['_unique_children']} unique children")
    
    # Render orbit views
    out_path = Path(f'Saved/SplatEmit/{material_name}_children.png')
    print(f"\nRendering to {out_path}...")
    render_orbit(scene, out_path=str(out_path), n_views=6, elev_deg=12.0)
    
    # Save class genome
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
    # Define materials to process with their scan pairs
    materials = [
        {
            'name': 'bonsai_vegetative',
            'scan1': 'WorldModel/training_data/real_data/bonsai/bonsai.ksplat',
            'scan2': 'WorldModel/training_data/downloads/dyl/bonsai_bonsai-7k.splat'
        },
        {
            'name': 'stump_wood',
            'scan1': 'WorldModel/training_data/downloads/stump.splat',
            'scan2': 'WorldModel/training_data/downloads/dyl/stump-7k.splat'
        },
        {
            'name': 'bicycle_metallic',
            'scan1': 'WorldModel/training_data/downloads/bicycle.splat',
            'scan2': 'WorldModel/training_data/downloads/garden.splat'  # Garden has metallic elements too
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
    
    # Summary report
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
