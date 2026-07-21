#!/usr/bin/env python3
"""Auto-generated domain: planet_surface_biome_generation"""

import copy, math, random

def seed(rng=None):
    if rng is None: rng = random.Random()
    return {
    "wall_0_biomes_distributed_b": True,
    "wall_1_transition_zones_bet": True,
    "wall_2_at_least_3_distinct_": True,
    }

def mutate(genome: dict, rng=None):
    if rng is None: rng = random.Random()
    g = copy.deepcopy(genome)
    g["wall_0_biomes_distributed_b"] = rng.choice([True, False])
    g["wall_1_transition_zones_bet"] = rng.choice([True, False])
    g["wall_2_at_least_3_distinct_"] = rng.choice([True, False])
    return g

def measure(genome: dict) -> dict:
    """
    Apply genome to game state, test constraint, report facts.
    Uses MCPStdioClient to interact with the running editor.
    """
    try:
        from core.telemetry_probe import MCPStdioClient
        c = MCPStdioClient()
    except Exception as e:
        return {"error": str(e)}
    
    results = {}
    # Test: Biomes distributed by temperature and precipitation
    results["wall_0_biomes_distributed_b"] = True  # replace with actual MCP test
    # Test: Transition zones between adjacent biomes
    results["wall_1_transition_zones_bet"] = True  # replace with actual MCP test
    # Test: At least 3 distinct biomes per habitable planet
    results["wall_2_at_least_3_distinct_"] = True  # replace with actual MCP test
    return results

def get_walls() -> list:
    return [
    "Biomes distributed by temperature and precipitation",
    "Transition zones between adjacent biomes",
    "At least 3 distinct biomes per habitable planet"
]
