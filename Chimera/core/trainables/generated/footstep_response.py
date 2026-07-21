#!/usr/bin/env python3
"""Auto-generated domain: footstep_response"""

import copy, math, random

def seed(rng=None):
    if rng is None: rng = random.Random()
    return {
    "wall_0_footstep_must_displa": True,
    "wall_1_displacement_depth_m": True,
    "wall_2_audio_response_must_": True,
    "wall_3_footprint_must_persi": True,
    "wall_4_dust_puff_must_be_vi": True,
    }

def mutate(genome: dict, rng=None):
    if rng is None: rng = random.Random()
    g = copy.deepcopy(genome)
    g["wall_0_footstep_must_displa"] = rng.choice([True, False])
    g["wall_1_displacement_depth_m"] = rng.choice([True, False])
    g["wall_2_audio_response_must_"] = rng.choice([True, False])
    g["wall_3_footprint_must_persi"] = rng.choice([True, False])
    g["wall_4_dust_puff_must_be_vi"] = rng.choice([True, False])
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
    # Test: Footstep must displace grains within a 5-15cm radius of impact
    results["wall_0_footstep_must_displa"] = True  # replace with actual MCP test
    # Test: Displacement depth must be 0.5-3mm per step on loose sand
    results["wall_1_displacement_depth_m"] = True  # replace with actual MCP test
    # Test: Audio response must differ between sand, rock, and metal surfaces
    results["wall_2_audio_response_must_"] = True  # replace with actual MCP test
    # Test: Footprint must persist for at least 5 seconds before eroding
    results["wall_3_footprint_must_persi"] = True  # replace with actual MCP test
    # Test: Dust puff must be visible on sand impact (not on rock)
    results["wall_4_dust_puff_must_be_vi"] = True  # replace with actual MCP test
    return results

def get_walls() -> list:
    return [
    "Footstep must displace grains within a 5-15cm radius of impact",
    "Displacement depth must be 0.5-3mm per step on loose sand",
    "Audio response must differ between sand, rock, and metal surfaces",
    "Footprint must persist for at least 5 seconds before eroding",
    "Dust puff must be visible on sand impact (not on rock)"
]
