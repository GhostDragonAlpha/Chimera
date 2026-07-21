#!/usr/bin/env python3
"""Ground terrain rung — GPU-accelerated Cellular Potts via matter_gpu.
Uses measure_batch to evaluate the entire population on the GPU.
Measures repose angle, material segregation, and walkable surface area.
"""
import copy, math, random
import numpy as np

# Matter types from core.matter
MEDIUM = 0
SAND = 1
ROCK = 2
BEDROCK = 3
N_TYPES = 4
TYPE_NAMES = ["medium", "sand", "rock", "bedrock"]

# Default adhesion: sand sticks to sand, rock sticks to rock,
# sand-rock interface is weak, bedrock is frozen (immovable).
# J[a,b] = adhesion energy between type a and b (lower = stronger)
J_DEFAULT = np.array([
    [0.0, 8.0, 8.0, 0.0],   # medium -> everything weak
    [8.0, 4.0, 6.0, 0.0],   # sand -> sand strong, rock medium
    [8.0, 6.0, 4.0, 0.0],   # rock -> rock strong, sand medium
    [0.0, 0.0, 0.0, 0.0],   # bedrock -> frozen (never moves)
], dtype=np.float32)
np.fill_diagonal(J_DEFAULT, 4.0)  # same-type cohesion
J_DEFAULT[MEDIUM, MEDIUM] = 0.0


def seed(rng=None):
    if rng is None: rng = random.Random()
    return {
        "grid_size": rng.choice([48, 64, 96]),
        "sand_frac": rng.uniform(0.3, 0.8),
        "rock_frac": rng.uniform(0.1, 0.4),
        "bedrock_depth": rng.uniform(0.05, 0.3),
        "sweeps": rng.choice([60, 90, 120]),
        "temperature": rng.uniform(8.0, 16.0),
        "lambda_vol": rng.uniform(0.5, 1.5),
        "j_sand_sand": rng.uniform(2.0, 6.0),
        "j_rock_rock": rng.uniform(2.0, 6.0),
        "j_sand_rock": rng.uniform(4.0, 10.0),
    }


def mutate(genome, rng=None):
    if rng is None: rng = random.Random()
    g = copy.deepcopy(genome)
    for key in ["sand_frac", "rock_frac", "bedrock_depth",
                "temperature", "lambda_vol", "j_sand_sand",
                "j_rock_rock", "j_sand_rock"]:
        g[key] *= math.exp(rng.uniform(-0.15, 0.15))
    if rng.random() < 0.1:
        g["grid_size"] = rng.choice([48, 64, 96])
    if rng.random() < 0.1:
        g["sweeps"] = rng.choice([60, 90, 120])
    g["sand_frac"] = max(0.1, min(0.9, g["sand_frac"]))
    g["rock_frac"] = max(0.05, min(0.6, g["rock_frac"]))
    g["bedrock_depth"] = max(0.01, min(0.5, g["bedrock_depth"]))
    return g


def _build_initial_grid(genome, rng_seed):
    """Create the initial 3D grid from genome parameters."""
    np.random.seed(rng_seed)
    N = genome["grid_size"]
    n_sand = int(N**3 * genome["sand_frac"])
    n_rock = int(N**3 * genome["rock_frac"])
    n_bedrock = int(N**3 * genome["bedrock_depth"])
    
    grid = np.full((N, N, N), MEDIUM, dtype=np.int16)
    
    # Bedrock at the bottom
    bedrock_z = max(1, int(N * genome["bedrock_depth"]))
    grid[:bedrock_z, :, :] = BEDROCK
    
    # Sand and rock in stratified layers above bedrock
    available = np.argwhere(grid == MEDIUM)
    np.random.shuffle(available)
    
    for idx in available[:n_sand]:
        grid[tuple(idx)] = SAND
    for idx in available[n_sand:n_sand + n_rock]:
        grid[tuple(idx)] = ROCK
    
    return grid


def _measure_grid(grid):
    """Extract facts from a settled grid."""
    N = grid.shape[0]
    
    # Material counts
    n_sand = int((grid == SAND).sum())
    n_rock = int((grid == ROCK).sum())
    n_bedrock = int((grid == BEDROCK).sum())
    
    # Surface heightmap (highest non-medium cell per column)
    heights = []
    for y in range(N):
        for x in range(N):
            for z in range(N - 1, -1, -1):
                if grid[z, y, x] != MEDIUM:
                    heights.append(z)
                    break
    
    if not heights:
        return {"n_materials": 0, "repose_angle": 0.0, "has_bedrock": 0,
                "surface_roughness": 0.0, "walkable_area": 0.0}
    
    heights = np.array(heights)
    surface_roughness = float(np.std(heights))
    
    # Repose angle estimate from height variation
    # angle = atan(max_height_diff / horizontal_distance)
    if len(heights) > 1:
        max_diff = float(heights.max() - heights.min())
        repose_deg = float(np.degrees(np.arctan(max_diff / N)))
    else:
        repose_deg = 0.0
    
    # Walkable area: cells with height within 20% of max (not too steep)
    max_h = heights.max()
    walkable = int((heights >= max_h * 0.8).sum())
    walkable_frac = walkable / len(heights)
    
    # Material segregation: how well sand and rock are separated
    # Lower = better segregated (sand zones, rock zones)
    if n_sand > 0 and n_rock > 0:
        sand_voxels = np.argwhere(grid == SAND)
        rock_voxels = np.argwhere(grid == ROCK)
        if len(sand_voxels) > 0 and len(rock_voxels) > 0:
            # Mean distance from sand to nearest rock
            from scipy.spatial.distance import cdist
            # Sample 1000 points for speed
            sv = sand_voxels[np.random.choice(len(sand_voxels), min(1000, len(sand_voxels)))]
            rv = rock_voxels[np.random.choice(len(rock_voxels), min(1000, len(rock_voxels)))]
            dists = cdist(sv.astype(float), rv.astype(float))
            segregation = float(dists.min(axis=1).mean())
        else:
            segregation = 0.0
    else:
        segregation = 0.0
    
    return {
        "n_materials": (1 if n_sand > 0 else 0) + (1 if n_rock > 0 else 0) + (1 if n_bedrock > 0 else 0),
        "repose_angle": repose_deg,
        "has_bedrock": 1 if n_bedrock > 0 else 0,
        "surface_roughness": surface_roughness,
        "walkable_area": walkable_frac,
        "segregation": segregation,
        "sand_frac": n_sand / (N**3) if N**3 > 0 else 0,
        "rock_frac": n_rock / (N**3) if N**3 > 0 else 0,
    }


def measure(genome):
    """Single-genome measure (CPU fallback)."""
    grid = _build_initial_grid(genome, 42)
    from core.matter_gpu import assemble_3d_gpu
    from core.matter import J_PROVEN_DIFFERENTIAL as J
    
    settled = assemble_3d_gpu(
        grid, grid.shape,
        targets={SAND: int((grid == SAND).sum()),
                 ROCK: int((grid == ROCK).sum()),
                 BEDROCK: int((grid == BEDROCK).sum())},
        J=J, sweeps=genome.get("sweeps", 90),
        temp=genome.get("temperature", 12.0),
        lam=genome.get("lambda_vol", 0.9),
        seed=42, frozen_type=BEDROCK
    )
    return _measure_grid(settled)


def measure_batch(population):
    """Evaluate the whole population on the GPU.
    
    Each genome gets its own grid. Grids are processed sequentially through
    the GPU (the physics runs on GPU, orchestration is CPU).
    Returns a list of measure dicts, same order as the population.
    """
    from core.matter_gpu import assemble_3d_gpu
    from core.matter import J_PROVEN_DIFFERENTIAL as J
    
    results = []
    for i, genome in enumerate(population):
        try:
            grid = _build_initial_grid(genome, 42 + i)
            settled = assemble_3d_gpu(
                grid, grid.shape,
                targets={SAND: int((grid == SAND).sum()),
                         ROCK: int((grid == ROCK).sum()),
                         BEDROCK: int((grid == BEDROCK).sum())},
                J=J, sweeps=genome.get("sweeps", 90),
                temp=genome.get("temperature", 12.0),
                lam=genome.get("lambda_vol", 0.9),
                seed=42 + i, frozen_type=BEDROCK
            )
            results.append(_measure_grid(settled))
        except Exception as e:
            results.append({"n_materials": 0, "repose_angle": 0.0,
                           "has_bedrock": 0, "surface_roughness": 0.0,
                           "walkable_area": 0.0, "segregation": 0.0,
                           "sand_frac": 0.0, "rock_frac": 0.0})
    
    return results


def get_walls():
    return [
        "At least 2 material types must form (n_materials >= 2)",
        "Angle of repose must be in [25, 50] degrees (repose_angle)",
        "Bedrock must exist (has_bedrock >= 1)",
        "At least 20% of surface must be walkable (walkable_area >= 0.20)",
    ]
