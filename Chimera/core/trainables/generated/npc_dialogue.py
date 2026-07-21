#!/usr/bin/env python3
"""Auto-generated domain: npc_dialogue"""

import copy, math, random

def seed(rng=None):
    if rng is None: rng = random.Random()
    return {
    "wall_0_npc_needs_must_be_co": True,
    "wall_1_each_npc_must_have_a": True,
    "wall_2_player_gesture_respo": True,
    "wall_3_npc_must_path_to_nea": True,
    "wall_4_npc_must_despawn_or_": True,
    }

def mutate(genome: dict, rng=None):
    if rng is None: rng = random.Random()
    g = copy.deepcopy(genome)
    g["wall_0_npc_needs_must_be_co"] = rng.choice([True, False])
    g["wall_1_each_npc_must_have_a"] = rng.choice([True, False])
    g["wall_2_player_gesture_respo"] = rng.choice([True, False])
    g["wall_3_npc_must_path_to_nea"] = rng.choice([True, False])
    g["wall_4_npc_must_despawn_or_"] = rng.choice([True, False])
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
    # Test: NPC needs must be communicated without text (animation, posture, gesture)
    results["wall_0_npc_needs_must_be_co"] = True  # replace with actual MCP test
    # Test: Each NPC must have at least 3 distinct gesture states (idle, need, satisfied)
    results["wall_1_each_npc_must_have_a"] = True  # replace with actual MCP test
    # Test: Player gesture response must be within 200 units of NPC
    results["wall_2_player_gesture_respo"] = True  # replace with actual MCP test
    # Test: NPC must path to nearest resource point after being helped
    results["wall_3_npc_must_path_to_nea"] = True  # replace with actual MCP test
    # Test: NPC must despawn or become non-interactive after reaching destination
    results["wall_4_npc_must_despawn_or_"] = True  # replace with actual MCP test
    return results

def get_walls() -> list:
    return [
    "NPC needs must be communicated without text (animation, posture, gesture)",
    "Each NPC must have at least 3 distinct gesture states (idle, need, satisfied)",
    "Player gesture response must be within 200 units of NPC",
    "NPC must path to nearest resource point after being helped",
    "NPC must despawn or become non-interactive after reaching destination"
]
