#!/usr/bin/env python3
"""Auto-generated domain: fabricator_economy_fabricator_economy_widget"""

import copy, math, random

def seed(rng=None):
    if rng is None: rng = random.Random()
    return {
    "wall_0_widget_property_must": True,
    "wall_1_satisfies_fabricator": True,
    }

def mutate(genome: dict, rng=None):
    if rng is None: rng = random.Random()
    g = copy.deepcopy(genome)
    g["wall_0_widget_property_must"] = rng.choice([True, False])
    g["wall_1_satisfies_fabricator"] = rng.choice([True, False])
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
    # Test: Widget property must be trainable
    results["wall_0_widget_property_must"] = True  # replace with actual MCP test
    # Test: Satisfies fabricator_economy constraints in composition
    results["wall_1_satisfies_fabricator"] = True  # replace with actual MCP test
    return results

def get_walls() -> list:
    return [
    "Widget property must be trainable",
    "Satisfies fabricator_economy constraints in composition"
]
