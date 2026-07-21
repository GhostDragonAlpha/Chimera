#!/usr/bin/env python3
"""Auto-generated domain: solar_system_habitable_zone"""

import copy, math, random

def seed(rng=None):
    if rng is None: rng = random.Random()
    return {
    "wall_0_habitable_zone_radiu": True,
    "wall_1_at_least_one_planet_": True,
    "wall_2_atmospheric_retentio": True,
    }

def mutate(genome: dict, rng=None):
    if rng is None: rng = random.Random()
    g = copy.deepcopy(genome)
    g["wall_0_habitable_zone_radiu"] = rng.choice([True, False])
    g["wall_1_at_least_one_planet_"] = rng.choice([True, False])
    g["wall_2_atmospheric_retentio"] = rng.choice([True, False])
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
    # Test: Habitable zone radius depends on star luminosity
    results["wall_0_habitable_zone_radiu"] = True  # replace with actual MCP test
    # Test: At least one planet must be in habitable zone
    results["wall_1_at_least_one_planet_"] = True  # replace with actual MCP test
    # Test: Atmospheric retention requires sufficient gravity
    results["wall_2_atmospheric_retentio"] = True  # replace with actual MCP test
    return results

def get_walls() -> list:
    return [
    "Habitable zone radius depends on star luminosity",
    "At least one planet must be in habitable zone",
    "Atmospheric retention requires sufficient gravity"
]
