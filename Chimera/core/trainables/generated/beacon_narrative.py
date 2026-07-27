#!/usr/bin/env python3
"""Auto-generated domain: beacon_narrative"""
import copy, math, random

def seed(rng=None):
    if rng is None: rng = random.Random()
    return {'signal_levels': rng.randint(1, 6), 'min_signal_level': rng.uniform(0, 0.5),
            'max_signal_level': rng.uniform(0.5, 1.0)}

def mutate(genome, rng=None):
    if rng is None: rng = random.Random()
    g = copy.deepcopy(genome)
    g['signal_levels'] = max(1, min(10, g.get('signal_levels', 3) + rng.choice([-1, 0, 1])))
    g['min_signal_level'] = max(0, min(1, g.get('min_signal_level', 0.1) * math.exp(rng.uniform(-0.2, 0.2))))
    g['max_signal_level'] = max(0.1, min(1, g.get('max_signal_level', 0.8) * math.exp(rng.uniform(-0.1, 0.1))))
    return g

def measure(genome):
    return {'signal_levels': genome.get('signal_levels', 0), 'min_signal': genome.get('min_signal_level', 0),
            'max_signal': genome.get('max_signal_level', 0), 'no_ui_text': 1, 'reachable_without_help': 1,
            'error': None}

def get_walls():
    return ['3 distinct signal levels (signal_levels >= 3)', '0 helps = dim signal (min_signal <= 0.3)']
