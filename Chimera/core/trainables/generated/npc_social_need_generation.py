#!/usr/bin/env python3
"""Auto-generated domain: npc_social_need_generation"""

import copy, math, random

def seed(rng=None):
    if rng is None: rng = random.Random()
    return {
    "wall_0_npc_needs_vary_by_ty": True,
    "wall_1_needs_become_urgent_": True,
    "wall_2_needs_are_visible_th": True,
    }

def mutate(genome: dict, rng=None):
    if rng is None: rng = random.Random()
    g = copy.deepcopy(genome)
    g["wall_0_npc_needs_vary_by_ty"] = rng.choice([True, False])
    g["wall_1_needs_become_urgent_"] = rng.choice([True, False])
    g["wall_2_needs_are_visible_th"] = rng.choice([True, False])
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
    # Test: NPC needs vary by type
    results["wall_0_npc_needs_vary_by_ty"] = True  # replace with actual MCP test
    # Test: Needs become urgent over time
    results["wall_1_needs_become_urgent_"] = True  # replace with actual MCP test
    # Test: Needs are visible through posture
    results["wall_2_needs_are_visible_th"] = True  # replace with actual MCP test
    return results

def get_walls() -> list:
    return [
    "NPC needs vary by type",
    "Needs become urgent over time",
    "Needs are visible through posture"
]
