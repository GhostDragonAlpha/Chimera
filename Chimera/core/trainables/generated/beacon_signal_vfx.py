#!/usr/bin/env python3
"""Auto-generated domain: beacon_signal_vfx"""

import copy, math, random

def seed(rng=None):
    if rng is None: rng = random.Random()
    return {
    "wall_0_beacon_signal_must_p": True,
    "wall_1_signal_color_must_tr": True,
    "wall_2_signal_must_be_visib": True,
    "wall_3_beacon_must_have_a_v": True,
    "wall_4_after_activation,_a_": True,
    }

def mutate(genome: dict, rng=None):
    if rng is None: rng = random.Random()
    g = copy.deepcopy(genome)
    g["wall_0_beacon_signal_must_p"] = rng.choice([True, False])
    g["wall_1_signal_color_must_tr"] = rng.choice([True, False])
    g["wall_2_signal_must_be_visib"] = rng.choice([True, False])
    g["wall_3_beacon_must_have_a_v"] = rng.choice([True, False])
    g["wall_4_after_activation,_a_"] = rng.choice([True, False])
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
    # Test: Beacon signal must pulse at a frequency proportional to NPCs helped (0 helps = no pulse, 3+ = steady 1Hz)
    results["wall_0_beacon_signal_must_p"] = True  # replace with actual MCP test
    # Test: Signal color must transition from red (0 helps) through yellow (1-2 helps) to white (3+ helps)
    results["wall_1_signal_color_must_tr"] = True  # replace with actual MCP test
    # Test: Signal must be visible from the shelter location (2000m)
    results["wall_2_signal_must_be_visib"] = True  # replace with actual MCP test
    # Test: Beacon must have a visible beam extending into the sky
    results["wall_3_beacon_must_have_a_v"] = True  # replace with actual MCP test
    # Test: After activation, a 5-second countdown must play before the ending sequence
    results["wall_4_after_activation,_a_"] = True  # replace with actual MCP test
    return results

def get_walls() -> list:
    return [
    "Beacon signal must pulse at a frequency proportional to NPCs helped (0 helps = no pulse, 3+ = steady 1Hz)",
    "Signal color must transition from red (0 helps) through yellow (1-2 helps) to white (3+ helps)",
    "Signal must be visible from the shelter location (2000m)",
    "Beacon must have a visible beam extending into the sky",
    "After activation, a 5-second countdown must play before the ending sequence"
]
