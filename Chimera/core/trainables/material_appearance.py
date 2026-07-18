"""material_appearance — trainable domain for matter library appearance entries.

Trains material appearance parameters against captured reality (photogrammetry scans,
3DGS captures) instead of guessing. The genome is one library entry's appearance params;
the measure function computes descriptor distances between our emitted splat population
and the reference scan population.

THE LOOP NEVER RENDERS — statistics space only, thousands of evals/sec.
THE WITNESS IS UE SUBSTRATE (rung D-prime, tb-0170): final judgment is the in-engine
render beside the scan.

DOMAIN CONTRACT:
  seed(rng) -> genome
  mutate(genome, rng) -> mutated_genome  
  measure(genome) -> {descriptor_name: float}   # facts only, no opinions
"""

from __future__ import annotations

import json
import math
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]   # core/trainables/x.py -> project root
# (parents[1] was core/ — one level too shallow: load_reference_descriptors built
#  core/docs/matter/... which never exists, so it silently returned None for every
#  scan. Found by sub-31 (surprise_43c5a16e0f439c80); the sibling rule of thumb:
#  count your own depth — core/material_harvester.py's parents[1] IS correct.)


# --- genome structure -----------------------------------------------------------
# Each appearance entry in the library has these trainable fields:
#   - albedo_mean_rgb: [R, G, B] — mean base colour (3 values)
#   - albedo_mottle_var: float — variance of per-particle luma factor
#   - roughness_mean: float — surface roughness (0-1)
#   - roughness_var: float — variance of roughness distribution
#   - grain_size_mm: {mean, spread} — particle size distribution

GENOME_SCHEMA = {
    "albedo_r": {"min": 0.0, "max": 1.0, "init": 0.5},
    "albedo_g": {"min": 0.0, "max": 1.0, "init": 0.5},
    "albedo_b": {"min": 0.0, "max": 1.0, "init": 0.5},
    "albedo_mottle_var": {"min": 0.001, "max": 0.2, "init": 0.04},
    "roughness_mean": {"min": 0.0, "max": 1.0, "init": 0.5},
    "roughness_var": {"min": 0.001, "max": 0.2, "init": 0.03},
}


def seed(rng=None) -> dict:
    """Create a random genome from the schema."""
    if rng is None:
        rng = np.random.RandomState()
    
    def _rand():
        return rng.random() if hasattr(rng, 'random') else rng.rand()
    
    genome = {}
    for field, spec in GENOME_SCHEMA.items():
        low, high = spec["min"], spec["max"]
        genome[field] = float(low + _rand() * (high - low))
    
    return genome


def mutate(genome: dict, rng) -> dict:
    """Mutate a genome by perturbing each field independently."""
    mutated = genome.copy()
    for field in GENOME_SCHEMA:
        spec = GENOME_SCHEMA[field]
        low, high = spec["min"], spec["max"]
        
        # Gaussian perturbation (10% of range)
        sigma = (high - low) * 0.1
        if hasattr(rng, 'normal'):
            val = genome[field] + rng.normal(0, sigma)
        else:
            val = genome[field] + rng.gauss(0, sigma)
        
        # Clamp to bounds
        mutated[field] = max(low, min(high, float(val)))
    
    return mutated


def _compute_descriptor_vector(genome: dict, n_samples: int = 5000) -> dict:
    """Compute descriptor vector from a genome by emitting splats and analyzing them.
    
    This is the core of the trainable domain: we emit splats with the given appearance
    parameters and compute statistical descriptors that can be compared against reference
    scan data.
    
    Returns a dict of {descriptor_name: float} — facts only, no opinions.
    """
    rng = np.random.RandomState(42)  # fixed seed for reproducibility
    
    albedo = np.array([genome["albedo_r"], genome["albedo_g"], genome["albedo_b"]])
    mottle_var = genome["albedo_mottle_var"]
    rough_mean = genome["roughness_mean"]
    rough_var = genome["roughness_var"]
    
    # Sample per-particle albedo from distribution (same as splat_emit variance sampling)
    luma_factors = rng.normal(1.0, math.sqrt(mottle_var), size=n_samples)
    luma_factors = np.clip(luma_factors, 0.5, 1.5)
    
    # Per-particle albedos
    albedo_per_particle = albedo[None, :] * luma_factors[:, None]
    
    # Compute descriptors from the emitted population
    luminance = 0.299 * albedo_per_particle[:, 0] + 0.587 * albedo_per_particle[:, 1] + 0.114 * albedo_per_particle[:, 2]
    
    descriptors = {
        "albedo_mean_luminance": float(np.mean(luminance)),
        "albedo_std_luminance": float(np.std(luminance)),
        "albedo_skew_luminance": float(_skewness(luminance)),
        "albedo_kurt_luminance": float(_kurtosis(luminance)),
        "luma_variance": float(np.var(luminance)),
        "chroma_variance": float(np.mean([np.var(albedo_per_particle[:, i] / (np.mean(albedo_per_particle[:, i]) + 1e-6)) for i in range(3)])),
        "luma_chroma_ratio": float(np.var(luminance) / (np.mean([np.var(albedo_per_particle[:, i]) for i in range(3)]) + 1e-6)),
        "roughness_mean": rough_mean,
        "roughness_var": rough_var,
    }
    
    return descriptors


def _skewness(x: np.ndarray) -> float:
    """Compute skewness of an array."""
    m = np.mean(x)
    s = np.std(x)
    if s < 1e-10:
        return 0.0
    return float(np.mean(((x - m) / s) ** 3))


def _kurtosis(x: np.ndarray) -> float:
    """Compute excess kurtosis of an array."""
    m = np.mean(x)
    s = np.std(x)
    if s < 1e-10:
        return 0.0
    return float(np.mean(((x - m) / s) ** 4) - 3)


def measure(genome: dict, reference_descriptors: dict | None = None) -> dict:
    """Measure a genome against optional reference descriptors.
    
    If reference_descriptors is provided, returns descriptor distances (for optimization).
    If not, returns raw descriptors (for reporting).
    
    Returns {metric_name: float} — facts only.
    """
    # Compute our descriptor vector
    our_desc = _compute_descriptor_vector(genome)
    
    if reference_descriptors is None:
        return our_desc
    
    # Compute distances against reference
    distances = {}
    for key in reference_descriptors:
        if key in our_desc:
            ref_val = reference_descriptors[key]
            our_val = our_desc[key]
            # Normalized distance (relative to reference magnitude)
            norm = abs(ref_val) + 1e-6
            distances[f"dist_{key}"] = float(abs(our_val - ref_val) / norm)
    
    return {**our_desc, **distances}


def load_reference_descriptors(scan_name: str) -> dict | None:
    """Load pre-computed reference descriptors from a scan.
    
    In production, this would read from docs/matter/reference_scans/<scan_name>.json
    For now, returns None (training without reference — just reports descriptors).
    """
    ref_path = ROOT / "docs" / "matter" / "reference_scans" / f"{scan_name}.json"
    if not ref_path.exists():
        return None
    
    with open(ref_path, 'r') as f:
        data = json.load(f)
    
    return data.get("descriptors", {})


def generate_reference_descriptors_from_scan(scan_data: dict) -> dict:
    """Generate reference descriptors from raw scan data (PBR maps or 3DGS captures).
    
    This is the ingestion pipeline step that converts raw scan data into descriptor vectors.
    
    Args:
        scan_data: dict with keys like 'albedo_texture', 'roughness_texture' (numpy arrays)
                   or 'splats' (list of dicts with position, color, opacity, covariance)
    
    Returns:
        dict of {descriptor_name: float} — the reference descriptor vector.
    """
    # For now, return empty — actual ingestion requires scan data files
    # This is a placeholder for the full pipeline
    return {}
