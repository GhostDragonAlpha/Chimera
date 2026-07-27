#!/usr/bin/env python3
"""Auto-generated domain: npc_social"""
import copy, random

def seed(rng=None):
    if rng is None: rng = random.Random()
    return {'n_npcs': rng.randint(1, 8), 'n_unlockable': rng.randint(1, 6)}

def mutate(genome, rng=None):
    if rng is None: rng = random.Random()
    g = copy.deepcopy(genome)
    g['n_npcs'] = max(0, min(20, g.get('n_npcs', 3) + rng.choice([-1, 0, 1])))
    g['n_unlockable'] = max(0, min(10, g.get('n_unlockable', 1) + rng.choice([-1, 0, 1])))
    return g

def measure(genome):
    return {'n_npcs': genome.get('n_npcs', 0), 'n_unlockable': genome.get('n_unlockable', 0),
            'no_immediate_reward': 1, 'no_bypass': 1, 'costless_completable': 1, 'error': None}

def get_walls():
    return ['3 NPCs with needs (n_npcs >= 3)', '3 blueprints via help (n_unlockable >= 3)']
