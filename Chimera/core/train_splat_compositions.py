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


def _load_40q(material_name: str) -> dict:
    """Load the 40Q document for a material and extract wall constraints."""
    path = ROOT / 'docs' / 'forty_questions' / f'{material_name}.json'
    if not path.exists():
        return {}
    with open(path) as f:
        doc = json.load(f)
    
    # Extract constraints from 40Q answers
    constraints = {}
    for q in doc['questions']:
        if not q.get('answered') or not q.get('a'):
            continue
        text = q['q'].lower() + ' ' + q['a'].lower()
        
        # Detect splat type mentions
        for st in ['surface', 'fiber', 'point', 'shell', 'beam', 'cloud', 'glow']:
            if st in text:
                constraints[f'uses_{st}'] = constraints.get(f'uses_{st}', 0) + 1
        
        # Detect scale/roughness mentions
        if 'grain' in text or 'rough' in text or 'granular' in text:
            constraints['rough'] = constraints.get('rough', 0) + 1
            constraints['uses_point'] = constraints.get('uses_point', 0) + 1
        if 'smooth' in text or 'uniform' in text or 'clean' in text:
            constraints['smooth'] = constraints.get('smooth', 0) + 1
        if 'fiber' in text or 'streak' in text or 'brush' in text or 'striation' in text:
            constraints['uses_fiber'] = constraints.get('uses_fiber', 0) + 2
        if 'subsurface' in text or 'translucen' in text or 'scatter' in text:
            constraints['subsurface'] = constraints.get('subsurface', 0) + 1
            constraints['uses_shell'] = constraints.get('uses_shell', 0) + 1
        if 'porous' in text or 'trabecular' in text:
            constraints['porous'] = constraints.get('porous', 0) + 1
            constraints['uses_point'] = constraints.get('uses_point', 0) + 1
        if 'fracture' in text or 'sharp' in text or 'broken' in text:
            constraints['fracture'] = constraints.get('fracture', 0) + 1
            constraints['uses_shell'] = constraints.get('uses_shell', 0) + 1
        if 'transparent' in text or 'clear' in text or 'ice' in text:
            constraints['transparent'] = constraints.get('transparent', 0) + 1
    
    return constraints


def measure(material_name: str, genome: np.ndarray) -> dict:
    """Measure how well a splat composition matches a material's 40Q walls.
    
    Instead of optimizing against the library's own numbers (circular),
    this reads the 40Q document and checks how well the composition
    satisfies the RESEARCHED constraints.
    """
    mat = MATTER_LIB['materials'].get(material_name)
    if mat is None:
        return {}
    
    constraints = _load_40q(material_name)
    app = mat.get('appearance', {})
    target_albedo = np.array(app.get('albedo_mean_rgb', [0.5, 0.5, 0.5]))
    target_roughness = app.get('roughness_mean', 0.5)
    target_subsurface = app.get('subsurface_strength', 0.0)
    target_alpha = app.get('alpha', 1.0)
    
    n = len(genome) // 2
    weights = genome[:n]
    scales = genome[n:]
    
    active = weights > 0.05
    if not active.any():
        return {'n_active': 0}
    
    w = weights / weights.sum()
    active_types = [SPLAT_NAMES[i] for i in range(N_TYPES) if active[i]]
    
    # --- Satisfy 40Q constraints ---
    constraint_score = 0.0
    max_score = 0.0
    
    for constraint, strength in constraints.items():
        max_score += strength
        
        if constraint == 'uses_surface' and w[0] > 0.1:
            constraint_score += strength
        elif constraint == 'uses_fiber' and w[1] > 0.1:
            constraint_score += strength
        elif constraint == 'uses_point' and w[2] > 0.05:
            constraint_score += strength
        elif constraint == 'uses_shell' and w[3] > 0.1:
            constraint_score += strength
        elif constraint == 'uses_beam' and w[4] > 0.05:
            constraint_score += strength
        elif constraint == 'uses_cloud' and w[5] > 0.05:
            constraint_score += strength
        elif constraint == 'uses_glow' and w[6] > 0.05:
            constraint_score += strength
        elif constraint == 'smooth' and w[0] + w[1] + w[3] > 0.7:
            constraint_score += strength * 0.5  # smooth = structured, not rough
        elif constraint == 'rough' and w[2] > 0.05:
            constraint_score += strength  # rough = has point splats
        elif constraint == 'subsurface' and w[3] > 0.2:
            constraint_score += strength  # subsurface = shell splats
        elif constraint == 'porous' and w[2] > 0.1:
            constraint_score += strength  # porous = point splats
    
    constraint_fraction = constraint_score / max(max_score, 1)
    
    # --- Optical match (from library, but weighted lower) ---
    surface_frac = w[0] + w[1] + w[3]
    point_frac = w[2] + w[4] + w[5] + w[6]
    eff_albedo = surface_frac * np.array(target_albedo) + point_frac * np.array([0.5, 0.5, 0.5])
    active_scales = scales[active]
    eff_roughness = np.clip(np.mean(active_scales) * 0.3, 0.1, 1.0)
    eff_subsurface = target_subsurface * w[3]  # shell splats carry subsurface
    eff_alpha = target_alpha * surface_frac + 0.5 * point_frac
    
    albedo_error = float(np.mean(np.abs(eff_albedo - target_albedo)))
    roughness_error = float(abs(eff_roughness - target_roughness))
    
    # Total: 70% constraint satisfaction, 30% optical match
    total_error = (1.0 - constraint_fraction) * 0.7 + (albedo_error + roughness_error) * 0.3
    
    # Type penalty
    n_active = int(active.sum())
    type_penalty = 0.0
    if n_active < 2:
        type_penalty = 0.2
    if n_active > 5:
        type_penalty = 0.1 * (n_active - 5)
    total_error += type_penalty
    
    return {
        'n_active': n_active,
        'constraint_fraction': constraint_fraction,
        'albedo_error': albedo_error,
        'roughness_error': roughness_error,
        'type_penalty': type_penalty,
        'total_error': total_error,
        'surface_frac': float(surface_frac),
        'point_frac': float(point_frac),
        'active_types': active_types,
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
