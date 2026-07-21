#!/usr/bin/env python3
"""Auto-generated domain: bigbang"""

import copy, math, random

def seed(rng=None):
    if rng is None: rng = random.Random()
    return {
    "wall_0_period_must_scale_as": True,
    "wall_1_the_fitted_kepler_ex": True,
    "wall_2_every_restart_must_p": True,
    "wall_3_at_least_90%_of_tota": True,
    "wall_4_planets_must_carry_a": True,
    "wall_5_late_mergers_must_be": True,
    "wall_6_eccentricity_must_be": True,
    "wall_7_orbital_inclination_": True,
    "wall_8_angular_momentum_mus": True,
    "wall_9_at_most_15%_of_mass_": True,
    }

def mutate(genome: dict, rng=None):
    if rng is None: rng = random.Random()
    g = copy.deepcopy(genome)
    g["wall_0_period_must_scale_as"] = rng.choice([True, False])
    g["wall_1_the_fitted_kepler_ex"] = rng.choice([True, False])
    g["wall_2_every_restart_must_p"] = rng.choice([True, False])
    g["wall_3_at_least_90%_of_tota"] = rng.choice([True, False])
    g["wall_4_planets_must_carry_a"] = rng.choice([True, False])
    g["wall_5_late_mergers_must_be"] = rng.choice([True, False])
    g["wall_6_eccentricity_must_be"] = rng.choice([True, False])
    g["wall_7_orbital_inclination_"] = rng.choice([True, False])
    g["wall_8_angular_momentum_mus"] = rng.choice([True, False])
    g["wall_9_at_most_15%_of_mass_"] = rng.choice([True, False])
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
    # Test: Period MUST scale as radius^1.5 across the WORST restart (kepler_r2_worst >= 0.90)
    results["wall_0_period_must_scale_as"] = True  # replace with actual MCP test
    # Test: The fitted Kepler exponent MUST land in [1.3, 1.7] (kepler_slope_mean)
    results["wall_1_the_fitted_kepler_ex"] = True  # replace with actual MCP test
    # Test: Every restart MUST produce at least 3 bound, orbiting planets (n_planets_worst >= 3)
    results["wall_2_every_restart_must_p"] = True  # replace with actual MCP test
    # Test: At least 90% of total mass MUST collapse to the central body (central_frac_mean >= 0.90)
    results["wall_3_at_least_90%_of_tota"] = True  # replace with actual MCP test
    # Test: Planets must carry at least 0.1% of system mass (planet_mass_frac_worst >= 0.001)
    results["wall_4_planets_must_carry_a"] = True  # replace with actual MCP test
    # Test: Late mergers MUST be rare — at most 2 (merges_late_worst <= 2)
    results["wall_5_late_mergers_must_be"] = True  # replace with actual MCP test
    # Test: Eccentricity must be below 0.30 (ecc_median_mean <= 0.30)
    results["wall_6_eccentricity_must_be"] = True  # replace with actual MCP test
    # Test: Orbital inclination RMS must stay under 15 degrees (incl_rms_deg_mean <= 15.0)
    results["wall_7_orbital_inclination_"] = True  # replace with actual MCP test
    # Test: Angular momentum MUST be conserved: L_z drift under 5% (lz_drift_worst <= 0.05)
    results["wall_8_angular_momentum_mus"] = True  # replace with actual MCP test
    # Test: At most 15% of mass may escape the system (escaped_frac_worst <= 0.15)
    results["wall_9_at_most_15%_of_mass_"] = True  # replace with actual MCP test
    return results

def get_walls() -> list:
    return [
    "Period MUST scale as radius^1.5 across the WORST restart (kepler_r2_worst >= 0.90)",
    "The fitted Kepler exponent MUST land in [1.3, 1.7] (kepler_slope_mean)",
    "Every restart MUST produce at least 3 bound, orbiting planets (n_planets_worst >= 3)",
    "At least 90% of total mass MUST collapse to the central body (central_frac_mean >= 0.90)",
    "Planets must carry at least 0.1% of system mass (planet_mass_frac_worst >= 0.001)",
    "Late mergers MUST be rare \u00e2\u20ac\u201d at most 2 (merges_late_worst <= 2)",
    "Eccentricity must be below 0.30 (ecc_median_mean <= 0.30)",
    "Orbital inclination RMS must stay under 15 degrees (incl_rms_deg_mean <= 15.0)",
    "Angular momentum MUST be conserved: L_z drift under 5% (lz_drift_worst <= 0.05)",
    "At most 15% of mass may escape the system (escaped_frac_worst <= 0.15)"
]
