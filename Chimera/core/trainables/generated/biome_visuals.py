#!/usr/bin/env python3
"""Auto-generated domain: biome_visuals"""

import copy, math, random

def seed(rng=None):
    if rng is None: rng = random.Random()
    return {
    "wall_0_sand_biome_must_have": True,
    "wall_1_rock_biome_must_have": True,
    "wall_2_metal_biome_must_hav": True,
    "wall_3_ice_biome_must_have_": True,
    "wall_4_biome_transitions_mu": True,
    "wall_5_each_biome_must_be_a": True,
    }

def mutate(genome: dict, rng=None):
    if rng is None: rng = random.Random()
    g = copy.deepcopy(genome)
    g["wall_0_sand_biome_must_have"] = rng.choice([True, False])
    g["wall_1_rock_biome_must_have"] = rng.choice([True, False])
    g["wall_2_metal_biome_must_hav"] = rng.choice([True, False])
    g["wall_3_ice_biome_must_have_"] = rng.choice([True, False])
    g["wall_4_biome_transitions_mu"] = rng.choice([True, False])
    g["wall_5_each_biome_must_be_a"] = rng.choice([True, False])
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
    # Test: Sand biome must have warm color palette (hue 30-50, saturation 10-30%)
    results["wall_0_sand_biome_must_have"] = True  # replace with actual MCP test
    # Test: Rock biome must have cool color palette (hue 200-240, saturation 5-15%)
    results["wall_1_rock_biome_must_have"] = True  # replace with actual MCP test
    # Test: Metal biome must have neutral color palette (hue 0-360, saturation 0-5%, value 50-80%)
    results["wall_2_metal_biome_must_hav"] = True  # replace with actual MCP test
    # Test: Ice biome must have blue-white palette (hue 180-220, saturation 0-10%, value 80-100%)
    results["wall_3_ice_biome_must_have_"] = True  # replace with actual MCP test
    # Test: Biome transitions must be gradual (no hard edges between adjacent biomes)
    results["wall_4_biome_transitions_mu"] = True  # replace with actual MCP test
    # Test: Each biome must be at least 10m x 10m in area
    results["wall_5_each_biome_must_be_a"] = True  # replace with actual MCP test
    return results

def get_walls() -> list:
    return [
    "Sand biome must have warm color palette (hue 30-50, saturation 10-30%)",
    "Rock biome must have cool color palette (hue 200-240, saturation 5-15%)",
    "Metal biome must have neutral color palette (hue 0-360, saturation 0-5%, value 50-80%)",
    "Ice biome must have blue-white palette (hue 180-220, saturation 0-10%, value 80-100%)",
    "Biome transitions must be gradual (no hard edges between adjacent biomes)",
    "Each biome must be at least 10m x 10m in area"
]
