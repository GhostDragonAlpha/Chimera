#!/usr/bin/env python3
"""Beacon narrative signal — pulse frequency and color gradient based on NPC help count.
Trained parameters: pulse_rate_at_0, pulse_rate_at_3, color_red, color_white.
"""
import copy, math, random

def seed(rng=None):
    if rng is None: rng = random.Random()
    return {
        "pulse_rate_0": rng.uniform(0.05, 0.3),
        "pulse_rate_3": rng.uniform(0.5, 2.0),
        "color_red_r": rng.uniform(0.8, 1.0),
        "color_red_g": rng.uniform(0.0, 0.3),
        "color_red_b": rng.uniform(0.0, 0.2),
        "color_white_r": 1.0,
        "color_white_g": rng.uniform(0.8, 1.0),
        "color_white_b": rng.uniform(0.8, 1.0),
        "n_bands": rng.choice([2, 3, 4]),
    }

def mutate(genome, rng=None):
    if rng is None: rng = random.Random()
    g = copy.deepcopy(genome)
    for k in ["pulse_rate_0", "pulse_rate_3"]:
        g[k] = max(0.01, g[k] * math.exp(rng.uniform(-0.2, 0.2)))
    for k in ["color_red_r", "color_red_g", "color_red_b", "color_white_g", "color_white_b"]:
        g[k] = max(0, min(1, g[k] + rng.uniform(-0.1, 0.1)))
    return g

def measure(genome):
    try:
        # The signal at 0 helps must be qualitatively different from 3+ helps
        rate_0 = genome["pulse_rate_0"]
        rate_3 = genome["pulse_rate_3"]
        n_bands = genome["n_bands"]
        
        # Rate must increase with help (faster pulse = brighter signal)
        rate_ratio = rate_3 / rate_0 if rate_0 > 0 else 1.0
        
        # Color difference: red at 0 helps vs white at 3+ helps
        r_diff = abs(genome["color_red_r"] - genome["color_white_r"])
        g_diff = abs(genome["color_red_g"] - genome["color_white_g"])
        b_diff = abs(genome["color_red_b"] - genome["color_white_b"])
        color_dist = math.sqrt(r_diff**2 + g_diff**2 + b_diff**2)
        
        # Red at 0 helps should be visibly red
        red_dominance = genome["color_red_r"] / (genome["color_red_g"] + genome["color_red_b"] + 0.01)
        
        return {
            "rate_ratio": rate_ratio,
            "color_dist": color_dist,
            "red_dominance": red_dominance,
            "n_bands": n_bands,
            "signal_differs": 1 if (rate_ratio > 2.0 and color_dist > 0.3 and red_dominance > 2.0) else 0,
        }
    except Exception as e:
        return {"rate_ratio": 0, "color_dist": 0, "red_dominance": 0, "n_bands": 0, "signal_differs": 0}

def get_walls():
    return [
        "3-help signal must pulse faster than 0-help signal (rate_ratio > 2.0)",
        "0-help signal must be visibly red, 3-help signal visibly white (color_dist > 0.3)",
        "Red color must dominate at 0 helps (red_dominance > 2.0)",
        "Signal must be qualitatively different between 0 and 3 helps (signal_differs >= 1)",
    ]
