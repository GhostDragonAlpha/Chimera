#!/usr/bin/env python3
"""Auto-generated domain: fabricator_economy"""
import copy, random

def seed(rng=None):
    if rng is None: rng = random.Random()
    return {'n_blueprints': rng.randint(2, 10), 'n_advanced': rng.randint(0, 5), 'cost_per_trip': rng.choice([1, 2, 3])}

def mutate(genome, rng=None):
    if rng is None: rng = random.Random()
    g = copy.deepcopy(genome)
    g['n_blueprints'] = max(1, min(20, g.get('n_blueprints', 5) + rng.choice([-2, -1, 0, 1, 2])))
    g['n_advanced'] = max(0, min(10, g.get('n_advanced', 1) + rng.choice([-1, 0, 1])))
    return g

def measure(genome):
    return {'n_blueprints': genome.get('n_blueprints', 0), 'n_advanced': genome.get('n_advanced', 0),
            'npc_locked': 1 if genome.get('n_advanced', 0) > 0 else 0,
            'force_choice': 1 if genome.get('cost_per_trip', 1) > 0 else 0, 'error': None}

def get_walls():
    return ['6 basic blueprints (n_blueprints >= 6)', '3 advanced blueprints (n_advanced >= 3)']
