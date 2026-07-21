#!/usr/bin/env python3
"""Auto-generated domain: audio_response"""

import copy, math, random

def seed(rng=None):
    if rng is None: rng = random.Random()
    return {
    "wall_0_footstep_frequency_s": True,
    "wall_1_footstep_frequency_s": True,
    "wall_2_footstep_frequency_s": True,
    "wall_3_amplitude_must_scale": True,
    "wall_4_left_and_right_foots": True,
    "wall_5_audio_must_not_clip_": True,
    }

def mutate(genome: dict, rng=None):
    if rng is None: rng = random.Random()
    g = copy.deepcopy(genome)
    g["wall_0_footstep_frequency_s"] = rng.choice([True, False])
    g["wall_1_footstep_frequency_s"] = rng.choice([True, False])
    g["wall_2_footstep_frequency_s"] = rng.choice([True, False])
    g["wall_3_amplitude_must_scale"] = rng.choice([True, False])
    g["wall_4_left_and_right_foots"] = rng.choice([True, False])
    g["wall_5_audio_must_not_clip_"] = rng.choice([True, False])
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
    # Test: Footstep frequency spectrum must peak at 200-800Hz on sand
    results["wall_0_footstep_frequency_s"] = True  # replace with actual MCP test
    # Test: Footstep frequency spectrum must peak at 800-2000Hz on rock
    results["wall_1_footstep_frequency_s"] = True  # replace with actual MCP test
    # Test: Footstep frequency spectrum must peak at 2000-5000Hz on metal
    results["wall_2_footstep_frequency_s"] = True  # replace with actual MCP test
    # Test: Amplitude must scale with player velocity (faster = louder)
    results["wall_3_amplitude_must_scale"] = True  # replace with actual MCP test
    # Test: Left and right footstep sounds must alternate (no stomp)
    results["wall_4_left_and_right_foots"] = True  # replace with actual MCP test
    # Test: Audio must not clip (peak amplitude < 0.95)
    results["wall_5_audio_must_not_clip_"] = True  # replace with actual MCP test
    return results

def get_walls() -> list:
    return [
    "Footstep frequency spectrum must peak at 200-800Hz on sand",
    "Footstep frequency spectrum must peak at 800-2000Hz on rock",
    "Footstep frequency spectrum must peak at 2000-5000Hz on metal",
    "Amplitude must scale with player velocity (faster = louder)",
    "Left and right footstep sounds must alternate (no stomp)",
    "Audio must not clip (peak amplitude < 0.95)"
]
