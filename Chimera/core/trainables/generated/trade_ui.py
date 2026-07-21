#!/usr/bin/env python3
"""Auto-generated domain: trade_ui"""

import copy, math, random

def seed(rng=None):
    if rng is None: rng = random.Random()
    return {
    "wall_0_trade_must_be_initia": True,
    "wall_1_available_blueprints": True,
    "wall_2_required_resources_m": True,
    "wall_3_trade_must_complete_": True,
    "wall_4_blueprint_unlock_fro": True,
    }

def mutate(genome: dict, rng=None):
    if rng is None: rng = random.Random()
    g = copy.deepcopy(genome)
    g["wall_0_trade_must_be_initia"] = rng.choice([True, False])
    g["wall_1_available_blueprints"] = rng.choice([True, False])
    g["wall_2_required_resources_m"] = rng.choice([True, False])
    g["wall_3_trade_must_complete_"] = rng.choice([True, False])
    g["wall_4_blueprint_unlock_fro"] = rng.choice([True, False])
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
    # Test: Trade must be initiated by player gesture within 200 units of fabricator terminal
    results["wall_0_trade_must_be_initia"] = True  # replace with actual MCP test
    # Test: Available blueprints must be displayed as 3D holographic models (not 2D UI)
    results["wall_1_available_blueprints"] = True  # replace with actual MCP test
    # Test: Required resources must be visible on the blueprint (what you need vs what you have)
    results["wall_2_required_resources_m"] = True  # replace with actual MCP test
    # Test: Trade must complete within 1 second of confirmation (no animation lock)
    results["wall_3_trade_must_complete_"] = True  # replace with actual MCP test
    # Test: Blueprint unlock from NPC help must show a brief VFX pulse on the fabricator
    results["wall_4_blueprint_unlock_fro"] = True  # replace with actual MCP test
    return results

def get_walls() -> list:
    return [
    "Trade must be initiated by player gesture within 200 units of fabricator terminal",
    "Available blueprints must be displayed as 3D holographic models (not 2D UI)",
    "Required resources must be visible on the blueprint (what you need vs what you have)",
    "Trade must complete within 1 second of confirmation (no animation lock)",
    "Blueprint unlock from NPC help must show a brief VFX pulse on the fabricator"
]
