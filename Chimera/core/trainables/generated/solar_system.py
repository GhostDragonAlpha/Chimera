#!/usr/bin/env python3
"""Auto-generated domain: solar_system"""

import copy, math, random

def seed(rng=None):
    if rng is None: rng = random.Random()
    return {
    "wall_0_star_must_contain_at": True,
    "wall_1_at_least_3_orbiting_": True,
    "wall_2_orbits_must_obey_kep": True,
    "wall_3_bodies_must_have_dis": True,
    "wall_4_system_must_be_stabl": True,
    "wall_5_inner_bodies_must_be": True,
    }

def mutate(genome: dict, rng=None):
    if rng is None: rng = random.Random()
    g = copy.deepcopy(genome)
    g["wall_0_star_must_contain_at"] = rng.choice([True, False])
    g["wall_1_at_least_3_orbiting_"] = rng.choice([True, False])
    g["wall_2_orbits_must_obey_kep"] = rng.choice([True, False])
    g["wall_3_bodies_must_have_dis"] = rng.choice([True, False])
    g["wall_4_system_must_be_stabl"] = rng.choice([True, False])
    g["wall_5_inner_bodies_must_be"] = rng.choice([True, False])
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
    # Test: Star must contain at least 90% of system mass (CelestialBodySpecComponent RadiusKm dominates)
    results["wall_0_star_must_contain_at"] = True  # replace with actual MCP test
    # Test: At least 3 orbiting bodies must be present and visible
    results["wall_1_at_least_3_orbiting_"] = True  # replace with actual MCP test
    # Test: Orbits must obey Kepler's third law when verified through CelestialMaths
    results["wall_2_orbits_must_obey_kep"] = True  # replace with actual MCP test
    # Test: Bodies must have distinct visual properties (size, color, atmosphere)
    results["wall_3_bodies_must_have_dis"] = True  # replace with actual MCP test
    # Test: System must be stable under UE5 physics tick for 60 seconds
    results["wall_4_system_must_be_stabl"] = True  # replace with actual MCP test
    # Test: Inner bodies must be smaller and rockier than outer bodies (terrestrial vs gas giant pattern)
    results["wall_5_inner_bodies_must_be"] = True  # replace with actual MCP test
    return results

def get_walls() -> list:
    return [
    "Star must contain at least 90% of system mass (CelestialBodySpecComponent RadiusKm dominates)",
    "At least 3 orbiting bodies must be present and visible",
    "Orbits must obey Kepler's third law when verified through CelestialMaths",
    "Bodies must have distinct visual properties (size, color, atmosphere)",
    "System must be stable under UE5 physics tick for 60 seconds",
    "Inner bodies must be smaller and rockier than outer bodies (terrestrial vs gas giant pattern)"
]
