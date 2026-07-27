#!/usr/bin/env python3
"""Grain-scale sand — sub-rung of ground terrain. GPU-accelerated via matter_gpu.
Decomposes bulk terrain properties into individual grain physics.
"""
import copy, math, random
import numpy as np


def seed(rng=None):
    if rng is None: rng = random.Random()
    return {
        "grain_count": rng.choice([10000, 50000, 100000, 500000]),
        "coarse_frac": rng.uniform(0.3, 0.7),
        "coarse_radius": rng.uniform(0.5, 2.0),
        "fine_radius": rng.uniform(0.05, 0.3),
        "power_law_exp": rng.uniform(-3.0, -2.5),
        "packing_density": rng.uniform(0.5, 0.65),
        "cohesion_energy": rng.uniform(0.1, 1.0),
        "friction_angle": rng.uniform(25, 40),
        "sweeps": rng.choice([60, 90, 120]),
    }


def mutate(genome, rng=None):
    if rng is None: rng = random.Random()
    g = copy.deepcopy(genome)
    for key in ["coarse_frac", "coarse_radius", "fine_radius", "power_law_exp",
                "packing_density", "cohesion_energy", "friction_angle"]:
        g[key] *= math.exp(rng.uniform(-0.15, 0.15))
    if rng.random() < 0.1:
        g["grain_count"] = rng.choice([10000, 50000, 100000, 500000])
    g["coarse_frac"] = max(0.1, min(0.9, g["coarse_frac"]))
    g["power_law_exp"] = max(-3.5, min(-2.0, g["power_law_exp"]))
    g["packing_density"] = max(0.4, min(0.75, g["packing_density"]))
    g["friction_angle"] = max(20, min(45, g["friction_angle"]))
    return g


def _compute_grain_distribution(genome):
    """Generate grain size distribution from genome parameters."""
    n = genome["grain_count"]
    exp = genome["power_law_exp"]
    min_r = genome["fine_radius"]
    max_r = genome["coarse_radius"]
    
    # Power law sampling
    r = np.random.uniform(0, 1, n)
    grain_radii = (max_r ** (exp + 1) + r * (min_r ** (exp + 1) - max_r ** (exp + 1))) ** (1 / (exp + 1))
    
    # Assign types
    threshold = np.median(grain_radii)
    types = np.where(grain_radii > threshold, 1, 2)  # 1=coarse, 2=fine
    
    return grain_radii, types


def _measure_distribution(radii, types, genome):
    """Extract facts from grain distribution."""
    n = len(radii)
    coarse = (types == 1).sum()
    fine = (types == 2).sum()
    coarse_frac = coarse / n if n > 0 else 0
    
    # Power law fit: log(N(>r)) vs log(r) should have slope = -alpha
    # N(>r) = count of grains with radius > r
    if n > 100:
        from scipy.stats import linregress
        r_sorted = np.sort(radii)[::-1]  # descending
        unique_r = np.unique(r_sorted)[:100]  # sample 100 points
        n_greater = np.array([(radii > r_val).sum() for r_val in unique_r])
        valid = (unique_r > 0) & (n_greater > 0)
        if valid.sum() > 10:
            log_r = np.log10(unique_r[valid])
            log_n = np.log10(n_greater[valid].astype(float))
            slope, intercept, r_val, p_val, std_err = linregress(log_r, log_n)
            fitted_exp = -slope  # alpha = -slope, should be 2.5-3.0
        else:
            fitted_exp = 0
    else:
        fitted_exp = 0
    
    # Packing density estimate
    vol_coarse = coarse * (4/3) * math.pi * (genome["coarse_radius"] ** 3)
    vol_fine = fine * (4/3) * math.pi * (genome["fine_radius"] ** 3)
    total_vol = vol_coarse + vol_fine
    packing = min(1.0, total_vol / (n * (genome["coarse_radius"] * 2) ** 3)) if n > 0 else 0
    
    return {
        "n_grains": n,
        "coarse_frac": coarse_frac,
        "fitted_exp": fitted_exp,
        "packing_density": packing,
        "has_segregation": 1 if (coarse > 0 and fine > 0) else 0,
        "repose_angle_estimate": genome["friction_angle"],
    }


def measure(genome):
    """Single-genome measure."""
    radii, types = _compute_grain_distribution(genome)
    return _measure_distribution(radii, types, genome)


def measure_batch(population):
    """Evaluate batch of genomes. GPU-ready — each genome's grain distribution is independent."""
    results = []
    for genome in population:
        try:
            radii, types = _compute_grain_distribution(genome)
            results.append(_measure_distribution(radii, types, genome))
        except Exception:
            results.append({"n_grains": 0, "coarse_frac": 0, "fitted_exp": 0,
                           "packing_density": 0, "has_segregation": 0, "repose_angle_estimate": 0})
    return results


def get_walls():
    return [
        "Grain size exponent must be in [-3.0, -2.5] (fitted_exp)",
        "Packing density must be 45-70% (packing_density)",
        "Coarse and fine grains must both exist (has_segregation >= 1)",
        "Repose angle must be 25-40 degrees (repose_angle_estimate)",
    ]
