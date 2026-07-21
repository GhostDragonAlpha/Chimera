#!/usr/bin/env python3
"""Auto-generated domain: ground_terrain"""
import copy, math, random

def seed(rng=None):
    if rng is None: rng = random.Random()
    return {'n_materials': rng.randint(1, 5), 'repose_angle': rng.uniform(20, 50), 'bedrock_depth': rng.uniform(0, 10)}

def mutate(genome, rng=None):
    if rng is None: rng = random.Random()
    g = copy.deepcopy(genome)
    g['n_materials'] = max(1, min(10, g.get('n_materials', 1) + rng.choice([-1, 0, 1])))
    g['repose_angle'] = max(15, min(60, g.get('repose_angle', 30) * math.exp(rng.uniform(-0.1, 0.1))))
    return g

def measure(genome):
    return {'n_materials': genome.get('n_materials', 0), 'repose_angle': genome.get('repose_angle', 0),
            'has_bedrock': 1 if genome.get('bedrock_depth', 0) > 0 else 0, 'spawn_on_formed': 1, 'error': None}

def get_walls():
    return ['At least 2 material types (n_materials >= 2)', 'Angle of repose 30-45 (repose_angle)']
