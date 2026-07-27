#!/usr/bin/env python3
"""Auto-generated domain: biome_resources"""
import copy, math, random

def seed(rng=None):
    if rng is None: rng = random.Random()
    return {'n_resource_types': rng.randint(3, 10), 'n_biomes': rng.randint(2, 6),
            'inventory_slots': rng.choice([4, 6, 8, 10]), 'resource_visibility_range': rng.uniform(200, 1000)}

def mutate(genome, rng=None):
    if rng is None: rng = random.Random()
    g = copy.deepcopy(genome)
    g['n_resource_types'] = max(1, min(15, g.get('n_resource_types', 3) + rng.choice([-1, 0, 1])))
    g['n_biomes'] = max(1, min(8, g.get('n_biomes', 2) + rng.choice([-1, 0, 1])))
    return g

def measure(genome):
    return {'n_resource_types': genome.get('n_resource_types', 0), 'n_biomes': genome.get('n_biomes', 0),
            'inventory_slots': genome.get('inventory_slots', 8),
            'resource_visible': 1 if genome.get('resource_visibility_range', 0) >= 500 else 0, 'error': None}

def get_walls():
    return ['6 resource types (n_resource_types >= 6)', '8 inventory max (inventory_slots <= 8)']
