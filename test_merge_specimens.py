#!/usr/bin/env python3
"""Test script to demonstrate merge_specimens workflow with two bonsai scans."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from Construction.export_genome import cluster_genomes, merge_specimens, FEATURES
import numpy as np
from pathlib import Path

def match_clusters(genomes_a, genomes_b, max_matches=3):
    """Match clusters from two scans by feature similarity."""
    # Extract features for matching (size, aniso, R, G, B, opacity)
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
    range_[range_ == 0] = 1  # avoid division by zero
    
    normalized_a = np.array([c[1] / range_ for c in clusters_a])
    normalized_b = np.array([c[1] / range_ for c in clusters_b])
    
    # Compute pairwise distances
    distances = np.linalg.norm(normalized_a[:, None, :] - normalized_b[None, :, :], axis=2)
    
    # Find best matches (greedy assignment)
    matches = []
    used_a, used_b = set(), set()
    
    for _ in range(min(max_matches, len(clusters_a), len(clusters_b))):
        # Find minimum distance among unused pairs
        mask = np.ones(distances.shape, dtype=bool)
        mask[np.ix_(list(used_a), list(used_b))] = False
        if not mask.any():
            break
            
        idx = np.argmin(distances[mask])
        i, j = np.unravel_index(idx, mask.shape)
        while (i in used_a) or (j in used_b):  # should not happen with mask
            mask[i, j] = False
            idx = np.argmin(distances[mask])
            i, j = np.unravel_index(idx, mask.shape)
            
        matches.append((clusters_a[i][0], clusters_b[j][0], distances[i, j]))
        used_a.add(i)
        used_b.add(j)
    
    return matches

def main():
    # Two bonsai scans
    scan1 = Path('WorldModel/training_data/real_data/bonsai/bonsai.ksplat')
    scan2 = Path('WorldModel/training_data/downloads/dyl/bonsai_bonsai-7k.splat')
    
    print(f"Processing {scan1}...")
    genomes1 = cluster_genomes(str(scan1), k=8, sample=100000)
    print(f"  Found {len(genomes1)} clusters")
    
    print(f"\nProcessing {scan2}...")
    genomes2 = cluster_genomes(str(scan2), k=8, sample=100000)
    print(f"  Found {len(genomes2)} clusters")
    
    # Match clusters between scans
    matches = match_clusters(genomes1, genomes2, max_matches=3)
    print(f"\nBest matching cluster pairs:")
    for name_a, name_b, dist in matches:
        print(f"  {name_a} (scan1) <-> {name_b} (scan2): distance={dist:.4f}")
    
    # Extract matched specimens
    specimens = []
    for name_a, name_b, _ in matches[:2]:  # Use top 2 matches
        specimen1 = genomes1[name_a].copy()
        specimen2 = genomes2[name_b].copy()
        
        # Add metadata to identify source
        specimen1['_source'] = str(scan1)
        specimen2['_source'] = str(scan2)
        
        specimens.append(specimen1)
        specimens.append(specimen2)
    
    print(f"\nMerging {len(specimens)} specimens...")
    class_genome = merge_specimens(specimens, name='bonsai_material')
    
    print("\nClass genome structure:")
    print(f"  n_specimens: {class_genome['n_specimens']}")
    print(f"  n_splats: {class_genome['n_splats']}")
    print(f"  between_within_ratio: {class_genome['between_within_ratio']:.4f}")
    
    print("\nFeatures with heritability components:")
    for feat, data in class_genome['features'].items():
        print(f"  {feat}:")
        print(f"    mean: {data['mean']:.4f}")
        print(f"    within_std: {data['within_std']:.4f}")
        print(f"    between_std: {data['between_std']:.4f}")
    
    # Compute heritability using progeny.py's function
    from Chimera.core.progeny import heritability
    h2 = heritability(class_genome)
    print("\nHeritability (h²) per trait:")
    for feat, h2_val in h2.items():
        if h2_val is not None:
            print(f"  {feat}: {h2_val:.4f}")
        else:
            print(f"  {feat}: undefined (need more specimens)")
    
    return class_genome

if __name__ == '__main__':
    main()
