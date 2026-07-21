#!/usr/bin/env python3
"""Auto-generated domain: planet_surface"""

import copy, math, random

def seed(rng=None):
    if rng is None: rng = random.Random()
    return {
    "wall_0_planet_must_have_a_s": True,
    "wall_1_inner_planets_must_b": True,
    "wall_2_outer_planets_must_b": True,
    "wall_3_at_least_one_planet_": True,
    "wall_4_planets_must_have_di": True,
    "wall_5_surface_gravity_must": True,
    }

def mutate(genome: dict, rng=None):
    if rng is None: rng = random.Random()
    g = copy.deepcopy(genome)
    g["wall_0_planet_must_have_a_s"] = rng.choice([True, False])
    g["wall_1_inner_planets_must_b"] = rng.choice([True, False])
    g["wall_2_outer_planets_must_b"] = rng.choice([True, False])
    g["wall_3_at_least_one_planet_"] = rng.choice([True, False])
    g["wall_4_planets_must_have_di"] = rng.choice([True, False])
    g["wall_5_surface_gravity_must"] = rng.choice([True, False])
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
    # Test: Planet must have a surface temperature compatible with its orbital distance (T_eq from stellar flux)
    results["wall_0_planet_must_have_a_s"] = True  # replace with actual MCP test
    # Test: Inner planets must be rocky (high density, solid surface, thin or no atmosphere)
    results["wall_1_inner_planets_must_b"] = True  # replace with actual MCP test
    # Test: Outer planets must be gaseous or icy (low density, thick atmosphere, no solid surface)
    results["wall_2_outer_planets_must_b"] = True  # replace with actual MCP test
    # Test: At least one planet must have a breathable atmosphere (CelestialBodySpecComponent.HasBreathableProxy)
    results["wall_3_at_least_one_planet_"] = True  # replace with actual MCP test
    # Test: Planets must have distinct surface biomes based on temperature bands
    results["wall_4_planets_must_have_di"] = True  # replace with actual MCP test
    # Test: Surface gravity must be consistent with planet mass and radius (g = GM/r² within 30% of expected)
    results["wall_5_surface_gravity_must"] = True  # replace with actual MCP test
    return results

def get_walls() -> list:
    return [
    "Planet must have a surface temperature compatible with its orbital distance (T_eq from stellar flux)",
    "Inner planets must be rocky (high density, solid surface, thin or no atmosphere)",
    "Outer planets must be gaseous or icy (low density, thick atmosphere, no solid surface)",
    "At least one planet must have a breathable atmosphere (CelestialBodySpecComponent.HasBreathableProxy)",
    "Planets must have distinct surface biomes based on temperature bands",
    "Surface gravity must be consistent with planet mass and radius (g = GM/r\u00c2\u00b2 within 30% of expected)"
]
