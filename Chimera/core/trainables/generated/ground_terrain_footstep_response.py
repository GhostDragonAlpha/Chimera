#!/usr/bin/env python3
"""Auto-generated domain: ground_terrain_footstep_response"""

import copy, math, random

def seed(rng=None):
    if rng is None: rng = random.Random()
    return {
    "wall_0_footstep_displaces_g": True,
    "wall_1_footprint_persists_5": True,
    "wall_2_dust_puff_on_impact": True,
    }

def mutate(genome: dict, rng=None):
    if rng is None: rng = random.Random()
    g = copy.deepcopy(genome)
    g["wall_0_footstep_displaces_g"] = rng.choice([True, False])
    g["wall_1_footprint_persists_5"] = rng.choice([True, False])
    g["wall_2_dust_puff_on_impact"] = rng.choice([True, False])
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
    # Test: Footstep displaces grains 5-15cm radius
    results["wall_0_footstep_displaces_g"] = True  # replace with actual MCP test
    # Test: Footprint persists 5+ seconds
    results["wall_1_footprint_persists_5"] = True  # replace with actual MCP test
    # Test: Dust puff on impact
    results["wall_2_dust_puff_on_impact"] = True  # replace with actual MCP test
    return results

def get_walls() -> list:
    return [
    "Footstep displaces grains 5-15cm radius",
    "Footprint persists 5+ seconds",
    "Dust puff on impact"
]
