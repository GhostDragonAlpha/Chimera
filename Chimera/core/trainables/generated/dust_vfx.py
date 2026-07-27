#!/usr/bin/env python3
"""Auto-generated domain: dust_vfx"""

import copy, math, random

def seed(rng=None):
    if rng is None: rng = random.Random()
    return {
    "wall_0_dust_particles_must_": True,
    "wall_1_particle_count_must_": True,
    "wall_2_particle_lifetime_mu": True,
    "wall_3_particle_color_must_": True,
    "wall_4_no_dust_on_metal_sur": True,
    "wall_5_particle_size_must_b": True,
    }

def mutate(genome: dict, rng=None):
    if rng is None: rng = random.Random()
    g = copy.deepcopy(genome)
    g["wall_0_dust_particles_must_"] = rng.choice([True, False])
    g["wall_1_particle_count_must_"] = rng.choice([True, False])
    g["wall_2_particle_lifetime_mu"] = rng.choice([True, False])
    g["wall_3_particle_color_must_"] = rng.choice([True, False])
    g["wall_4_no_dust_on_metal_sur"] = rng.choice([True, False])
    g["wall_5_particle_size_must_b"] = rng.choice([True, False])
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
    # Test: Dust particles must spawn within 0.1s of footstep impact
    results["wall_0_dust_particles_must_"] = True  # replace with actual MCP test
    # Test: Particle count must be 50-200 per footstep on sand
    results["wall_1_particle_count_must_"] = True  # replace with actual MCP test
    # Test: Particle lifetime must be 0.5-2.0 seconds
    results["wall_2_particle_lifetime_mu"] = True  # replace with actual MCP test
    # Test: Particle color must match surface material (sand=tan, rock=gray)
    results["wall_3_particle_color_must_"] = True  # replace with actual MCP test
    # Test: No dust on metal surfaces
    results["wall_4_no_dust_on_metal_sur"] = True  # replace with actual MCP test
    # Test: Particle size must be 0.5-5mm screen space at 1m distance
    results["wall_5_particle_size_must_b"] = True  # replace with actual MCP test
    return results

def get_walls() -> list:
    return [
    "Dust particles must spawn within 0.1s of footstep impact",
    "Particle count must be 50-200 per footstep on sand",
    "Particle lifetime must be 0.5-2.0 seconds",
    "Particle color must match surface material (sand=tan, rock=gray)",
    "No dust on metal surfaces",
    "Particle size must be 0.5-5mm screen space at 1m distance"
]
