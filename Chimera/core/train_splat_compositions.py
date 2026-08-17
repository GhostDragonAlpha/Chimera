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
LIB_PATH = ROOT / 'Chimera/docs/rep_batteries/matter_library.json'
RECOVERED_PATH = ROOT / 'docs/matter/recovered_genomes.json'
SPLAT_NAMES = ['surface', 'fiber', 'point', 'shell', 'beam', 'cloud', 'glow']
N_TYPES = len(SPLAT_NAMES)

# Load the matter library
with open(LIB_PATH) as f:
    MATTER_LIB = json.load(f)

# ---------------------------------------------------------------------------
# RECOVERED GENOMES — measured from real scans by Construction/export_genome.py
#
# Before this existed, measure() scored a composition by KEYWORD-MATCHING the English
# text of a 40-questions document: if an answer contained the word "fiber", the
# composition was rewarded for using fiber splats. That grades an adjective, which is
# the studio's own named failure mode.
#
# A recovered genome is the measured splat-configuration DISTRIBUTION of real material
# — size, anisotropy, colour, opacity, each as mean + p10..p90. When one exists for a
# material we score against THAT instead: emit the composition's splats, compute the
# same features from their covariance eigenvalues, and compare distributions.
# ---------------------------------------------------------------------------
RECOVERED = {}
if RECOVERED_PATH.exists():
    try:
        RECOVERED = json.loads(RECOVERED_PATH.read_text()).get('genomes', {})
    except Exception:
        RECOVERED = {}


def _emit_cov(type_idx: int, n: int, scale: float, rng) -> np.ndarray:
    """Emit n covariance matrices of one splat type at a given spatial scale."""
    if n <= 0:
        return np.zeros((0, 3, 3))
    normal = rng.standard_normal((n, 3))
    normal /= np.clip(np.linalg.norm(normal, axis=1, keepdims=True), 1e-9, None)
    pos = rng.standard_normal((n, 3))
    name = SPLAT_NAMES[type_idx]
    if name == 'surface':
        return emit_surface(normal, tangent_scale=1.15 * scale, normal_scale=0.35 * scale)
    if name == 'fiber':
        # fiber_dir is REQUIRED for elongation — without it emit_fiber is byte-identical
        # to emit_surface (both aniso 0.696), so the trainer could never tell them apart.
        fd = rng.standard_normal((n, 3))
        fd /= np.clip(np.linalg.norm(fd, axis=1, keepdims=True), 1e-9, None)
        return emit_fiber(normal, tangent_scale=1.15 * scale, normal_scale=0.35 * scale,
                          fiber_dir=fd)
    if name == 'point':
        return emit_point(pos, radius=scale)
    if name == 'shell':
        return emit_shell(pos, normal, thickness=0.2 * scale, spread=scale)
    if name == 'beam':
        return emit_beam(normal, length=10.0 * scale, thickness=0.5 * scale)
    if name == 'cloud':
        return emit_cloud(pos, radius=100.0 * scale, alpha=0.1)
    return emit_glow(pos, radius=5.0 * scale)


def emitted_features(genome: np.ndarray, n_total: int = 4000, seed: int = 0) -> dict:
    """Emit the composition's splats and measure the SAME features the scan reports.

    Covariance eigenvalues are the squared principal scales, so:
        scales = sqrt(eigvals) -> sorted -> size = middle, aniso = 1 - min/max
    which is exactly what Construction/take_dna_full.py computes from a real scan.
    That identity is what makes the comparison meaningful rather than analogical.
    """
    rng = np.random.default_rng(seed)
    n = len(genome) // 2
    weights, scales = genome[:n], genome[n:]
    active = weights > 0.05
    if not active.any():
        return {}
    w = weights / weights.sum()

    covs = [_emit_cov(i, int(round(w[i] * n_total)), float(scales[i]), rng)
            for i in range(N_TYPES) if active[i]]
    covs = [c for c in covs if len(c)]
    if not covs:
        return {}
    C = np.concatenate(covs, 0)

    eig = np.linalg.eigvalsh(C)                      # ascending, per splat
    sc = np.sqrt(np.clip(eig, 1e-12, None))          # principal scales
    return {
        'size': sc[:, 1],                            # middle axis
        'aniso': 1.0 - sc[:, 0] / (sc[:, 2] + 1e-9),  # 0 = blob, 1 = flat/elongated
    }


def measure_recovered(material_name: str, genome: np.ndarray) -> dict:
    """Score a composition against a MEASURED genome instead of keyword constraints.

    Distribution match, not mean match: a genome is a RANGE, so we compare mean AND
    spread. Being right on average while having the wrong spread is still wrong.
    """
    rec = RECOVERED.get(material_name)
    if rec is None:
        return {}
    feat = emitted_features(genome)
    if not feat:
        return {'n_active': 0, 'total_error': float('inf')}

    target = rec['features']
    errs = {}

    # ANISOTROPY is a RATIO — scale-invariant, so it compares directly across a scan and
    # an emitter that share no unit system. It also carries material identity most
    # strongly: a smooth panel and rough corrosion differ in anisotropy at equal brightness.
    a_got, a_want = feat['aniso'], target['aniso']
    errs['aniso_mean_error'] = abs(float(np.mean(a_got)) - a_want['mean'])
    got_spread = float(np.percentile(a_got, 90) - np.percentile(a_got, 10))
    errs['aniso_spread_error'] = abs(got_spread - (a_want['p90'] - a_want['p10']))

    # SIZE cannot be compared in absolute terms: a scan's world scale is arbitrary (the
    # truck scan reports ~0.012 while the emitters work in units of ~1). What IS a
    # material property is the SHAPE of the size distribution, so compare the coefficient
    # of variation (std/mean), which is scale-invariant.
    s_got = feat['size']
    cv_got = float(np.std(s_got) / (np.mean(s_got) + 1e-9))
    cv_want = target['size']['std'] / (abs(target['size']['mean']) + 1e-9)
    errs['size_cv_error'] = abs(cv_got - cv_want)

    n_active = int((genome[:len(genome) // 2] > 0.05).sum())
    penalty = 0.2 if n_active < 2 else (0.1 * (n_active - 5) if n_active > 5 else 0.0)

    total = (errs['aniso_mean_error'] * 1.0
             + errs['aniso_spread_error'] * 0.5
             + errs['size_cv_error'] * 0.4) + penalty

    return {
        'n_active': n_active,
        'source': 'recovered',
        'total_error': float(total),
        **{k: float(v) for k, v in errs.items()},
        'emitted_aniso_mean': float(np.mean(feat['aniso'])),
        'target_aniso_mean': target['aniso']['mean'],
        'emitted_size_cv': cv_got,
        'target_size_cv': float(cv_want),
    }


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
    """Measure how well a splat composition matches a material.

    PREFERENCE ORDER:
      1. a RECOVERED genome (measured from a real scan)  -- physics
      2. the 40Q keyword constraints                      -- an adjective, fallback only

    Rule 1 of docs/EXPERIMENTAL_METHOD.md: measure the thing, not a proxy. Keyword
    matching on English answers is a proxy for material identity; the splat-configuration
    distribution of the real material IS material identity.
    """
    if material_name in RECOVERED:
        return measure_recovered(material_name, genome)

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
    
    names = [n for n in MATTER_LIB['materials'] if not n.startswith('_')]
    names += [n for n in RECOVERED if n not in names]   # measured materials train too
    if RECOVERED:
        print(f'  {len(RECOVERED)} RECOVERED genomes available '
              f'(measured from real scans) — these score against physics, not keywords')
        print()

    results = {}
    for name in names:
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

    write_to_library(results)


def write_to_library(results: dict) -> None:
    """Write trained compositions back into the matter library.

    THIS IS THE LINK THAT WAS MISSING. splat_level.py builds the world by reading
    `matter_library['materials'][name]['splat_composition']['layers']`, and before this
    NO material had that field -- so every trained composition was written to
    splat_compositions.trained.json and read by nothing. The trainer ran, produced good
    numbers, and the world was emitted with the fallback
    [{'type': 'surface', 'weight': 1.0}] every time.

    Materials recovered from scans (cluster_*) are ADDED to the library as new entries so
    a measured material becomes usable world-building matter, carrying its provenance.
    """
    with open(LIB_PATH) as f:
        lib = json.load(f)

    wrote, added = 0, 0
    for name, res in results.items():
        comp = res.get('composition') or {}
        if not comp:
            continue
        layers = [{'type': t, 'weight': round(float(v['weight']), 4),
                   'scale': round(float(v['scale']), 4)}
                  for t, v in sorted(comp.items(), key=lambda kv: -kv[1]['weight'])]

        measured = res.get('measures', {}).get('source') == 'recovered'
        if name not in lib['materials']:
            if not measured:
                continue                      # never invent a library material from a fallback score
            # Carry the MEASURED optics across too. Without this the material lands in the
            # library with no appearance block, _get_optical() falls through to default
            # grey, and a scan-derived material renders as featureless putty -- the colour
            # was measured and then thrown away one step before it was used.
            feats = RECOVERED.get(name, {}).get('features', {})
            appearance = {}
            if feats:
                appearance = {
                    'albedo_mean_rgb': [round(feats[c]['mean'], 4) for c in ('R', 'G', 'B')],
                    'albedo_p10_rgb': [round(feats[c]['p10'], 4) for c in ('R', 'G', 'B')],
                    'albedo_p90_rgb': [round(feats[c]['p90'], 4) for c in ('R', 'G', 'B')],
                    'alpha': round(feats['opacity']['mean'], 4),
                    'roughness_mean': round(float(feats['aniso']['mean']), 4),
                    'subsurface_strength': 0.0,
                    'provenance': 'MEASURED from a real scan (mean + p10..p90 range)',
                }
            lib['materials'][name] = {
                'family': 'measured',
                '_provenance': 'RECOVERED from a real scan by Construction/export_genome.py',
                **({'appearance': appearance} if appearance else {}),
            }
            added += 1
        elif measured and 'appearance' not in lib['materials'][name]:
            feats = RECOVERED.get(name, {}).get('features', {})
            if feats:
                lib['materials'][name]['appearance'] = {
                    'albedo_mean_rgb': [round(feats[c]['mean'], 4) for c in ('R', 'G', 'B')],
                    'alpha': round(feats['opacity']['mean'], 4),
                    'roughness_mean': round(float(feats['aniso']['mean']), 4),
                    'subsurface_strength': 0.0,
                    'provenance': 'MEASURED from a real scan',
                }

        lib['materials'][name]['splat_composition'] = {
            'layers': layers,
            'error': round(float(res.get('error', 0.0)), 4),
            'provenance': 'MEASURED — scored against a recovered splat-configuration '
                          'distribution' if measured else
                          'researched — scored against 40Q constraints (no scan available)',
        }
        wrote += 1

    with open(LIB_PATH, 'w') as f:
        json.dump(lib, f, indent=2)
    print(f'Wrote splat_composition into {wrote} materials '
          f'({added} newly added from scans) -> {LIB_PATH.name}')
    print('  splat_level.py now emits trained compositions instead of the surface-only fallback.')


if __name__ == '__main__':
    main()
