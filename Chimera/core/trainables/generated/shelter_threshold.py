#!/usr/bin/env python3
"""Auto-generated domain: shelter_threshold"""

import copy, math, random

def seed(rng=None):
    if rng is None: rng = random.Random()
    return {
    "wall_0_player_must_be_withi": True,
    "wall_1_refill_must_start_wi": True,
    "wall_2_refill_must_stop_wit": True,
    "wall_3_shelter_zone_must_be": True,
    }

def mutate(genome: dict, rng=None):
    if rng is None: rng = random.Random()
    g = copy.deepcopy(genome)
    g["wall_0_player_must_be_withi"] = rng.choice([True, False])
    g["wall_1_refill_must_start_wi"] = rng.choice([True, False])
    g["wall_2_refill_must_stop_wit"] = rng.choice([True, False])
    g["wall_3_shelter_zone_must_be"] = rng.choice([True, False])
    return g

def measure(genome):
    try:
        return {
            'trigger_radius': genome.get('trigger_radius', 300),
            'refill_delay': genome.get('refill_delay', 2.0),
            'stop_delay': genome.get('stop_delay', 5.0),
            'has_marker': 1 if genome.get('b_has_visual_marker', False) else 0,
            'error': None
        }
    except Exception as e:
        return {'trigger_radius': 0, 'refill_delay': 99, 'stop_delay': 99, 'has_marker': 0, 'error': str(e)}

def get_walls() -> list:
    return [
    "Player must be within 300 units of shelter center to trigger refill",
    "Refill must start within 2 seconds of entering the zone",
    "Refill must stop within 5 seconds of leaving the zone",
    "Shelter zone must be visibly marked (structure, glow, or terrain feature)"
]
