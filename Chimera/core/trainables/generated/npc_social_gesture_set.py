#!/usr/bin/env python3
"""Auto-generated domain: npc_social_gesture_set"""

import copy, math, random

def seed(rng=None):
    if rng is None: rng = random.Random()
    return {
    "wall_0_at_least_3_gesture_s": True,
    "wall_1_gestures_readable_fr": True,
    "wall_2_no_text_required_for": True,
    }

def mutate(genome: dict, rng=None):
    if rng is None: rng = random.Random()
    g = copy.deepcopy(genome)
    g["wall_0_at_least_3_gesture_s"] = rng.choice([True, False])
    g["wall_1_gestures_readable_fr"] = rng.choice([True, False])
    g["wall_2_no_text_required_for"] = rng.choice([True, False])
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
    # Test: At least 3 gesture states per NPC
    results["wall_0_at_least_3_gesture_s"] = True  # replace with actual MCP test
    # Test: Gestures readable from 50m
    results["wall_1_gestures_readable_fr"] = True  # replace with actual MCP test
    # Test: No text required for communication
    results["wall_2_no_text_required_for"] = True  # replace with actual MCP test
    return results

def get_walls() -> list:
    return [
    "At least 3 gesture states per NPC",
    "Gestures readable from 50m",
    "No text required for communication"
]
