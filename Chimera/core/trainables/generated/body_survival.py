#!/usr/bin/env python3
"""Auto-generated domain: body_survival"""

import copy, math, random

def seed(rng=None):
    if rng is None: rng = random.Random()
    return {
    "wall_0_walking_player_must_": True,
    "wall_1_sprinting_must_drain": True,
    "wall_2_shelter_proximity_mu": True,
    "wall_3_battery_must_drain_o": True,
    "wall_4_death_must_be_recove": True,
    }

def mutate(genome: dict, rng=None):
    if rng is None: rng = random.Random()
    g = copy.deepcopy(genome)
    g["wall_0_walking_player_must_"] = rng.choice([True, False])
    g["wall_1_sprinting_must_drain"] = rng.choice([True, False])
    g["wall_2_shelter_proximity_mu"] = rng.choice([True, False])
    g["wall_3_battery_must_drain_o"] = rng.choice([True, False])
    g["wall_4_death_must_be_recove"] = rng.choice([True, False])
    return g

def measure(genome):
    try:
        return {
            'o2_drain_time': genome.get('o2_drain_time', 360),
            'sprint_mult': genome.get('sprint_mult', 2.0),
            'refill_rate': genome.get('refill_rate', 30),
            'night_drain': 1 if genome.get('battery_night_drain', 0) > 0 else 0,
            'has_respawn': 1 if genome.get('b_respawn_enabled', False) else 0,
            'error': None
        }
    except Exception as e:
        return {'o2_drain_time': 0, 'sprint_mult': 0, 'refill_rate': 0, 'night_drain': 0, 'has_respawn': 0, 'error': str(e)}

def get_walls() -> list:
    return [
    "Walking player must drain full O2 tank in 5-7 minutes",
    "Sprinting must drain O2 at least 2x walking rate",
    "Shelter proximity must refill O2 faster than it drains",
    "Battery must drain only at night",
    "Death must be recoverable (respawn at shelter with partial resources)"
]
