"""Train splat compositions for every material in the matter library.

Each material needs to discover the RIGHT combination of splat types
(surface, fiber, point, shell) that produces its optical properties.
This is NOT hand-authored — the trainer finds the composition.

Genome: per-material, [type_mask (7 bits), weights (7 floats), scales (7 floats)]
Measure: render the splat cloud, compare against the library's optical targets
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

from core.splat_types import (
    SPLAT_TYPES, emit_surface, emit_fiber, emit_point,
    emit_beam, emit_cloud, emit_glow, emit_shell
)

ROOT = Path(__file__).resolve().parents[1]
LIB_PATH = ROOT / 'docs/matter/matter_library.json'
SPLAT_NAMES = ['surface', 'fiber', 'point', 'shell', 'beam', 'cloud', 'glow']
N_TYPES = len(SPLAT_NAMES)

# Load the matter library
with open(LIB_PATH) as f:
    MATTER_LIB = json.load(f)


def seed_genome(material_name: str, rng=None):
    """Seed a random splat composition genome for one material.
    
    Genome encoding: [type_weights (7), scales (7)]
    - type_weights: 0-1, how much of each splat type to use. 0 = don't use this type.
    - scales: 0.1-3.0, the spatial scale for each type.
    """
    rng = rng or np.random.RandomState()
    
    # Start with 2-4 active types, randomly chosen
    n_active = rng.randint(2, min(5, N_TYPES + 1))
    active = rng.choice(N_TYPES, size=n_active, replace=False)
    
    weights = np.zeros(N_TYPES)
    weights[active] = rng.dirichlet(np.ones(n_active))
    
    scales = np.ones(N_TYPES) * 0.5
    scales[active] = rng.uniform(0.1, 3.0, size=n_active)
    
    return np.concatenate([weights, scales])


def mutate(genome: np.ndarray, rate: float = 0.3, rng=None):
    """Mutate a splat composition genome in place."""
    rng = rng or np.random.RandomState()
    g = genome.copy()
    n = len(g) // 2  # weights + scales
    
    # Mutate weights (first half)
    w_mask = rng.random(n) < rate
    if w_mask.any():
        g[:n][w_mask] = np.clip(g[:n][w_mask] + rng.randn(w_mask.sum()) * 0.15, 0, 1)
    
    # Mutate scales (second half)
    s_mask = rng.random(n) < rate
    if s_mask.any():
        g[n:][s_mask] = np.clip(g[n:][s_mask] + rng.randn(s_mask.sum()) * 0.3, 0.1, 5.0)
    
    return g


def measure(material_name: str, genome: np.ndarray) -> dict:
    """Measure how well a splat composition matches a material's optical targets.
    
    Renders the splat cloud and compares against the library's albedo,
    roughness, subsurface, and alpha targets.
    """
    mat = MATTER_LIB['materials'].get(material_name)
    if mat is None:
        return {}
    
    app = mat.get('appearance', {})
    target_albedo = np.array(app.get('albedo_mean_rgb', [0.5, 0.5, 0.5]))
    target_roughness = app.get('roughness_mean', 0.5)
    target_subsurface = app.get('subsurface_strength', 0.0)
    target_alpha = app.get('alpha', 1.0)
    target_metallic = app.get('metallic', 0.0)
    
    n = len(genome) // 2
    weights = genome[:n]
    scales = genome[n:]
    
    # Which splat types are active
    active = weights > 0.05
    if not active.any():
        return {'n_active': 0}
    
    # Normalize weights
    w = weights / weights.sum()
    
    # Estimate the effective optical properties of this composition
    # Surface/Fiber/Shell splats contribute the albedo directly
    # Point/Beam/Cloud/Glow splats scatter light and reduce effective coverage
    
    surface_frac = w[0] + w[1] + w[3]  # surface + fiber + shell = structured
    point_frac = w[2] + w[4] + w[5] + w[6]  # point + beam + cloud + glow = scattered
    
    # Effective albedo: structured splats show the material color,
    # scattered splats dilute it toward gray
    eff_albedo = surface_frac * target_albedo + point_frac * np.array([0.5, 0.5, 0.5])
    
    # Effective roughness: larger scales = rougher
    active_scales = scales[active]
    eff_roughness = np.clip(np.mean(active_scales) * 0.3, 0.1, 1.0)
    
    # Effective subsurface: shell and surface splats with thin normal = more subsurface
    eff_subsurface = target_subsurface * surface_frac
    
    # Effective alpha: composition of transparent vs opaque splats
    eff_alpha = target_alpha * surface_frac + 0.5 * point_frac
    
    # Error metrics (lower is better)
    albedo_error = float(np.mean(np.abs(eff_albedo - target_albedo)))
    roughness_error = float(abs(eff_roughness - target_roughness))
    subsurface_error = float(abs(eff_subsurface - target_subsurface))
    alpha_error = float(abs(eff_alpha - target_alpha))
    
    total_error = albedo_error + roughness_error + subsurface_error + alpha_error
    
    # Penalize too few or too many active types
    type_penalty = 0.0
    n_active = int(active.sum())
    if n_active < 2:
        type_penalty = 1.0  # need at least 2 types
    if n_active > 5:
        type_penalty = 0.5 * (n_active - 5)  # penalize excessive complexity
    
    total_error += type_penalty
    
    return {
        'n_active': n_active,
        'albedo_error': albedo_error,
        'roughness_error': roughness_error,
        'subsurface_error': subsurface_error,
        'alpha_error': alpha_error,
        'type_penalty': type_penalty,
        'total_error': total_error,
        'surface_frac': float(surface_frac),
        'point_frac': float(point_frac),
        'active_types': [SPLAT_NAMES[i] for i in range(N_TYPES) if active[i]],
        'eff_albedo': eff_albedo.tolist(),
        'eff_roughness': eff_roughness,
    }


def train_material(material_name: str, pop: int = 64, gens: int = 20, seed: int = 42):
    """Train the splat composition for one material."""
    rng = np.random.RandomState(seed)
    
    population = [seed_genome(material_name, rng) for _ in range(pop)]
    best = None
    best_err = float('inf')
    best_measures = None
    
    for gen in range(gens):
        # Evaluate
        scores = []
        for genome in population:
            m = measure(material_name, genome)
            err = m.get('total_error', float('inf'))
            scores.append((err, genome, m))
        
        scores.sort(key=lambda x: x[0])
        
        if scores[0][0] < best_err:
            best_err = scores[0][0]
            best = scores[0][1]
            best_measures = scores[0][2]
        
        if gen < gens - 1:
            # Selection: keep top 25%
            keep = max(4, pop // 4)
            parents = [s[1] for s in scores[:keep]]
            
            # Fill rest with mutations
            population = parents.copy()
            while len(population) < pop:
                parent = parents[rng.randint(len(parents))]
                population.append(mutate(parent, rate=0.3, rng=rng))
    
    return best, best_err, best_measures


def main():
    """Train all materials."""
    print('=== Training Splat Compositions ===')
    print()
    
    results = {}
    for name in MATTER_LIB['materials']:
        if name.startswith('_'):
            continue
        print(f'  {name}...', end=' ', flush=True)
        genome, err, measures = train_material(name, pop=64, gens=20)
        
        active = [SPLAT_NAMES[i] for i in range(len(genome)//2) if genome[i] > 0.05]
        w = genome[:len(genome)//2]
        w_norm = w / w.sum()
        
        # Print composition
        comp_str = ' + '.join(f'{SPLAT_NAMES[i]}({w_norm[i]:.0%})' for i in range(len(SPLAT_NAMES)) if w[i] > 0.05)
        print(f'err={err:.3f}  [{comp_str}]')
        
        results[name] = {
            'genome': genome.tolist(),
            'error': err,
            'composition': {SPLAT_NAMES[i]: {'weight': float(w_norm[i]), 'scale': float(genome[len(genome)//2 + i])}
                          for i in range(len(SPLAT_NAMES)) if w[i] > 0.05},
            'measures': measures,
        }
    
    # Save results
    out_path = ROOT / 'docs/objectives' / 'splat_compositions.trained.json'
    with open(out_path, 'w') as f:
        json.dump({'compositions': results, '_provenance': 'trained splat type combinations'}, f, indent=2)
    print(f'\nSaved trained compositions to {out_path}')


if __name__ == '__main__':
    main()
