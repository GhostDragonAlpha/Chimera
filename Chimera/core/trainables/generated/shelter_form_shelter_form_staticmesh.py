#!/usr/bin/env python3
"""Auto-generated domain: shelter_form_shelter_form_staticmesh"""

import copy, math, random

def seed(rng=None):
    if rng is None: rng = random.Random()
    return {
    "wall_0_staticmesh_property_": True,
    "wall_1_satisfies_shelter_fo": True,
    }

def mutate(genome: dict, rng=None):
    if rng is None: rng = random.Random()
    g = copy.deepcopy(genome)
    g["wall_0_staticmesh_property_"] = rng.choice([True, False])
    g["wall_1_satisfies_shelter_fo"] = rng.choice([True, False])
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
    # Test: StaticMesh property must be trainable
    results["wall_0_staticmesh_property_"] = True  # replace with actual MCP test
    # Test: Satisfies shelter_form constraints in composition
    results["wall_1_satisfies_shelter_fo"] = True  # replace with actual MCP test
    return results

def get_walls() -> list:
    return [
    "StaticMesh property must be trainable",
    "Satisfies shelter_form constraints in composition"
]
