#!/usr/bin/env python3
"""Solar system rung — delegates to the existing bigbang domain.
The genome and physics are identical. The decoder writes the winner to UE5.

This domain exists to:
1. Document the solar system as the first rung of the ladder
2. Provide a clean import point for the decoder
3. Map bigbang's output to UE5 CelestialBodySpecComponent properties
"""

import sys, os, json
from ..bigbang import seed, mutate, measure


def decode_to_ue5(genome: dict, results: dict, output_path: str = None):
    """Decode a winning genome + its results to UE5 level placement commands.
    
    Reads the trained bigbang output (planets as mass, a, e triples) and produces
    MCP spawn commands for placing celestial bodies in the emergent_world level.
    
    Args:
        genome: The winning genome from training
        results: The measure() output containing system facts
        output_path: Where to write the MCP command script
    """
    # Load the trained system output
    systems_path = os.path.join(os.path.dirname(__file__), '..', '..', 'docs', 'objectives', 'bigbang.systems.json')
    if not os.path.exists(systems_path):
        return {"error": f"Trained output not found at {systems_path}"}
    
    with open(systems_path) as f:
        systems_data = json.load(f)
    
    systems = systems_data.get("systems", [])
    
    if not systems:
        return {"error": "No systems found in trained output"}
    
    # Take the first system
    system = systems[0]
    star_mass_frac = systems_data.get("star_mass_frac", 0.98)
    
    commands = []
    
    # Place the star at origin
    star_radius = genome.get("star_radius", 50)
    star_color_r = genome.get("star_color_r", 1.0)
    star_color_g = genome.get("star_color_g", 0.8)
    star_color_b = genome.get("star_color_b", 0.3)
    
    commands.append(f"# Star ({star_mass_frac*100:.1f}% of system mass)")
    commands.append(f"# ACTOR: spawn sphere at (0,0,0) scale={star_radius}")
    commands.append(f"# MATERIAL: emissive color ({star_color_r:.2f}, {star_color_g:.2f}, {star_color_b:.2f})")
    commands.append("")
    
    # Place each planet
    for i, planet in enumerate(system):
        m_rel = planet.get("m_rel", 0.001)
        a = planet.get("a", 1.0)  # semi-major axis in AU
        e = planet.get("e", 0.1)  # eccentricity
        
        # Scale AU to UE5 world units (1 AU = 500 units for staging)
        scale = 500.0
        x = a * scale
        y = 0
        
        # Color based on position (inner = rocky, outer = gas giant)
        if a < 0.5:
            color = f"({0.5:.2f}, {0.3:.2f}, {0.2:.2f})"  # rocky brown
            radius = 0.5 + m_rel * 100
        elif a < 0.8:
            color = f"({0.3:.2f}, {0.5:.2f}, {0.3:.2f})"  # greenish
            radius = 0.8 + m_rel * 100
        else:
            color = f"({0.4:.2f}, {0.4:.2f}, {0.6:.2f})"  # blueish gas
            radius = 1.5 + m_rel * 100
        
        commands.append(f"# Planet {i+1}: m_rel={m_rel:.4f}, a={a:.3f} AU, e={e:.3f}")
        commands.append(f"# ACTOR: spawn sphere at ({x:.0f}, {y:.0f}, 0) scale={radius:.1f}")
        commands.append(f"# MATERIAL: color={color}")
        commands.append("")
    
    # Write command file
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            f.write("\n".join(commands))
        return {"output_path": output_path, "n_planets": len(system)}
    
    return {"commands": commands, "n_planets": len(system)}


def get_walls() -> list:
    """Walls from the original bigbang objective, converted to walls-only."""
    return [
        "At least 3 bound planets must form (n_planets_worst >= 3)",
        "Star must contain at least 90% of system mass (central_frac_mean >= 0.90)",
        "Kepler slope must land in [1.3, 1.7] (kepler_slope_mean)",
        "Kepler R^2 must be at least 0.90 (kepler_r2_worst >= 0.90)",
        "Eccentricity must average below 0.30 (ecc_median_mean <= 0.30)",
        "Angular momentum drift must be under 5% (lz_drift_worst <= 0.05)",
        "At most 2 late mergers (merges_late_worst <= 2)",
        "At most 15% of mass may escape (escaped_frac_worst <= 0.15)",
    ]


def get_domain_info() -> dict:
    """Return metadata about this domain for the decoder."""
    return {
        "name": "solar_system",
        "rung": 0,
        "next_rung": "planet_surface",
        "output_file": "docs/objectives/bigbang.systems.json",
        "ue5_components": ["CelestialBodySpecComponent", "DirectionalLightComponent", "SkyAtmosphereComponent"],
        "description": "Grows a solar system from a protoplanetary disk. Outputs star+planet positions for UE5 level placement."
    }
