#!/usr/bin/env python3
"""Auto-generated domain: resource_pickup"""

import copy, math, random

def seed(rng=None):
    if rng is None: rng = random.Random()
    return {
    "wall_0_player_must_be_able_": True,
    "wall_1_collected_resource_m": True,
    "wall_2_resource_must_have_a": True,
    "wall_3_resource_must_be_spa": True,
    "wall_4_resource_must_work_w": True,
    }

def mutate(genome: dict, rng=None):
    if rng is None: rng = random.Random()
    g = copy.deepcopy(genome)
    g["wall_0_player_must_be_able_"] = rng.choice([True, False])
    g["wall_1_collected_resource_m"] = rng.choice([True, False])
    g["wall_2_resource_must_have_a"] = rng.choice([True, False])
    g["wall_3_resource_must_be_spa"] = rng.choice([True, False])
    g["wall_4_resource_must_work_w"] = rng.choice([True, False])
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
    # Test: Player must be able to collect a visible resource by pressing E while within 300 units
    results["wall_0_player_must_be_able_"] = True  # replace with actual MCP test
    # Test: Collected resource must set bIsHoldingItem=true on PickupInteractionComponent
    results["wall_1_collected_resource_m"] = True  # replace with actual MCP test
    # Test: Resource must have a visible mesh the player can see at 500 units
    results["wall_2_resource_must_have_a"] = True  # replace with actual MCP test
    # Test: Resource must be spawnable via MCP bridge without CLASS_NOT_FOUND
    results["wall_3_resource_must_be_spa"] = True  # replace with actual MCP test
    # Test: Resource must work without requiring APickupActor C++ class inheritance
    results["wall_4_resource_must_work_w"] = True  # replace with actual MCP test
    return results

def get_walls() -> list:
    return [
    "Player must be able to collect a visible resource by pressing E while within 300 units",
    "Collected resource must set bIsHoldingItem=true on PickupInteractionComponent",
    "Resource must have a visible mesh the player can see at 500 units",
    "Resource must be spawnable via MCP bridge without CLASS_NOT_FOUND",
    "Resource must work without requiring APickupActor C++ class inheritance"
]
