#!/usr/bin/env python3
"""Auto-generated domain: body_survival_o2_consumption"""

import copy, math, random

def seed(rng=None):
    if rng is None: rng = random.Random()
    return {
    "wall_0_o2_consumption_scale": True,
    "wall_1_sprint_burns_2x_walk": True,
    "wall_2_idle_drain_is_nonzer": True,
    }

def mutate(genome: dict, rng=None):
    if rng is None: rng = random.Random()
    g = copy.deepcopy(genome)
    g["wall_0_o2_consumption_scale"] = rng.choice([True, False])
    g["wall_1_sprint_burns_2x_walk"] = rng.choice([True, False])
    g["wall_2_idle_drain_is_nonzer"] = rng.choice([True, False])
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
    # Test: O2 consumption scales with exertion
    results["wall_0_o2_consumption_scale"] = True  # replace with actual MCP test
    # Test: Sprint burns 2x walk rate
    results["wall_1_sprint_burns_2x_walk"] = True  # replace with actual MCP test
    # Test: Idle drain is nonzero
    results["wall_2_idle_drain_is_nonzer"] = True  # replace with actual MCP test
    return results

def get_walls() -> list:
    return [
    "O2 consumption scales with exertion",
    "Sprint burns 2x walk rate",
    "Idle drain is nonzero"
]
