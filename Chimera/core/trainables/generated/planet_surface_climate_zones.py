#!/usr/bin/env python3
"""Auto-generated domain: planet_surface_climate_zones"""

import copy, math, random

def seed(rng=None):
    if rng is None: rng = random.Random()
    return {
    "wall_0_equator_hotter_than_": True,
    "wall_1_atmospheric_circulat": True,
    "wall_2_axial_tilt_creates_s": True,
    }

def mutate(genome: dict, rng=None):
    if rng is None: rng = random.Random()
    g = copy.deepcopy(genome)
    g["wall_0_equator_hotter_than_"] = rng.choice([True, False])
    g["wall_1_atmospheric_circulat"] = rng.choice([True, False])
    g["wall_2_axial_tilt_creates_s"] = rng.choice([True, False])
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
    # Test: Equator hotter than poles
    results["wall_0_equator_hotter_than_"] = True  # replace with actual MCP test
    # Test: Atmospheric circulation creates climate bands
    results["wall_1_atmospheric_circulat"] = True  # replace with actual MCP test
    # Test: Axial tilt creates seasons
    results["wall_2_axial_tilt_creates_s"] = True  # replace with actual MCP test
    return results

def get_walls() -> list:
    return [
    "Equator hotter than poles",
    "Atmospheric circulation creates climate bands",
    "Axial tilt creates seasons"
]
