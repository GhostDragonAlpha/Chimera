#!/usr/bin/env python3
"""Auto-generated domain: shelter_form"""
import copy, math, random

def seed(rng=None):
    if rng is None: rng = random.Random()
    return {'enclosed_volume': rng.uniform(1000000, 50000000), 'entrance_clearance': rng.uniform(100, 400),
            'visible_distance': rng.uniform(50, 300), 'b_has_entrance': rng.choice([True, False])}

def mutate(genome, rng=None):
    if rng is None: rng = random.Random()
    g = copy.deepcopy(genome)
    g['enclosed_volume'] = max(0, g.get('enclosed_volume', 1e6) * math.exp(rng.uniform(-0.2, 0.2)))
    g['entrance_clearance'] = max(50, min(500, g.get('entrance_clearance', 200) * math.exp(rng.uniform(-0.1, 0.1))))
    return g

def measure(genome):
    return {'enclosed_volume': genome.get('enclosed_volume', 0), 'entrance_clearance': genome.get('entrance_clearance', 0),
            'visible_dist': genome.get('visible_distance', 0), 'has_entrance': 1 if genome.get('b_has_entrance', False) else 0,
            'error': None}

def get_walls():
    return ['Enclosed volume >= 18M (enclosed_volume)', 'Entrance clearance >= 200 (entrance_clearance)']
