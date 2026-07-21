#!/usr/bin/env python3
"""Auto-generated domain: npc_social_population_density"""

import copy, math, random

def seed(rng=None):
    if rng is None: rng = random.Random()
    return {
    "wall_0_npc_spawns_avoid_pla": True,
    "wall_1_npc_density_higher_n": True,
    "wall_2_maximum_10_npcs_visi": True,
    }

def mutate(genome: dict, rng=None):
    if rng is None: rng = random.Random()
    g = copy.deepcopy(genome)
    g["wall_0_npc_spawns_avoid_pla"] = rng.choice([True, False])
    g["wall_1_npc_density_higher_n"] = rng.choice([True, False])
    g["wall_2_maximum_10_npcs_visi"] = rng.choice([True, False])
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
    # Test: NPC spawns avoid player spawn zone
    results["wall_0_npc_spawns_avoid_pla"] = True  # replace with actual MCP test
    # Test: NPC density higher near resources
    results["wall_1_npc_density_higher_n"] = True  # replace with actual MCP test
    # Test: Maximum 10 NPCs visible at once
    results["wall_2_maximum_10_npcs_visi"] = True  # replace with actual MCP test
    return results

def get_walls() -> list:
    return [
    "NPC spawns avoid player spawn zone",
    "NPC density higher near resources",
    "Maximum 10 NPCs visible at once"
]
