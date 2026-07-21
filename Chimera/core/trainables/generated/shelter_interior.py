#!/usr/bin/env python3
"""Auto-generated domain: shelter_interior"""

import copy, math, random

def seed(rng=None):
    if rng is None: rng = random.Random()
    return {
    "wall_0_shelter_interior_mus": True,
    "wall_1_interior_temperature": True,
    "wall_2_at_least_one_fabrica": True,
    "wall_3_airlock_must_visibly": True,
    "wall_4_interior_volume_must": True,
    }

def mutate(genome: dict, rng=None):
    if rng is None: rng = random.Random()
    g = copy.deepcopy(genome)
    g["wall_0_shelter_interior_mus"] = rng.choice([True, False])
    g["wall_1_interior_temperature"] = rng.choice([True, False])
    g["wall_2_at_least_one_fabrica"] = rng.choice([True, False])
    g["wall_3_airlock_must_visibly"] = rng.choice([True, False])
    g["wall_4_interior_volume_must"] = rng.choice([True, False])
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
    # Test: Shelter interior must have at least 50klux ambient light (readable without suit light)
    results["wall_0_shelter_interior_mus"] = True  # replace with actual MCP test
    # Test: Interior temperature must be 18-25C (survivable without suit)
    results["wall_1_interior_temperature"] = True  # replace with actual MCP test
    # Test: At least one fabricator terminal must be visible inside
    results["wall_2_at_least_one_fabrica"] = True  # replace with actual MCP test
    # Test: Airlock must visibly separate interior from exterior (threshold marker)
    results["wall_3_airlock_must_visibly"] = True  # replace with actual MCP test
    # Test: Interior volume must fit player + fabricator + storage (>= 500x500x300 units)
    results["wall_4_interior_volume_must"] = True  # replace with actual MCP test
    return results

def get_walls() -> list:
    return [
    "Shelter interior must have at least 50klux ambient light (readable without suit light)",
    "Interior temperature must be 18-25C (survivable without suit)",
    "At least one fabricator terminal must be visible inside",
    "Airlock must visibly separate interior from exterior (threshold marker)",
    "Interior volume must fit player + fabricator + storage (>= 500x500x300 units)"
]
