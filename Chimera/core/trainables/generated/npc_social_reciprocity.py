#!/usr/bin/env python3
"""Auto-generated domain: npc_social_reciprocity"""

import copy, math, random

def seed(rng=None):
    if rng is None: rng = random.Random()
    return {
    "wall_0_helped_npcs_provide_": True,
    "wall_1_no_immediate_reward_": True,
    "wall_2_blueprint_unlock_has": True,
    }

def mutate(genome: dict, rng=None):
    if rng is None: rng = random.Random()
    g = copy.deepcopy(genome)
    g["wall_0_helped_npcs_provide_"] = rng.choice([True, False])
    g["wall_1_no_immediate_reward_"] = rng.choice([True, False])
    g["wall_2_blueprint_unlock_has"] = rng.choice([True, False])
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
    # Test: Helped NPCs provide unique blueprints
    results["wall_0_helped_npcs_provide_"] = True  # replace with actual MCP test
    # Test: No immediate reward for helping
    results["wall_1_no_immediate_reward_"] = True  # replace with actual MCP test
    # Test: Blueprint unlock has visual feedback
    results["wall_2_blueprint_unlock_has"] = True  # replace with actual MCP test
    return results

def get_walls() -> list:
    return [
    "Helped NPCs provide unique blueprints",
    "No immediate reward for helping",
    "Blueprint unlock has visual feedback"
]
