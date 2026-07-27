"""geology.py — Rock type and strata classification for procedural terrain.

Takes the output of matter_gpu.assemble_3d_gpu() and assigns rock types
based on elevation/strata depth bands. The player can read the geology
from the terrain — canyon walls show visible rock layers.

Teaches: Geology — rock types, strata formation, erosion patterns.
"""

import numpy as np
from typing import Optional

# Rock type definitions
ROCK_TYPES = [
    "regolith_breccia",       # 0: surface rubble
    "sedimentary_sandstone",  # 1: upper crust
    "sedimentary_limestone",  # 2: mid crust
    "metamorphic_schist",     # 3: lower crust
    "igneous_granite",        # 4: deep bedrock
    "igneous_basalt",         # 5: mantle
]

# Strata layers: each is a fraction of total terrain height
# (z_fraction_min, z_fraction_max, rock_type_index)
STRATA = [
    (0.00, 0.10, 0),  # surface: regolith
    (0.10, 0.30, 1),  # upper: sandstone
    (0.30, 0.50, 2),  # mid: limestone
    (0.50, 0.70, 3),  # lower: schist
    (0.70, 0.90, 4),  # deep: granite
    (0.90, 1.00, 5),  # mantle: basalt
]


def assign_strata(terrain_grid: np.ndarray, terrain_height: Optional[int] = None) -> np.ndarray:
    """Assign rock type indices to each frozen/terrain cell based on z-depth.
    
    Args:
        terrain_grid: int16 array from assemble_3d_gpu(). Cells > 0 are terrain.
        terrain_height: Total terrain depth in cells. If None, inferred from grid.
        
    Returns:
        int8 array of same shape with rock type indices (-1 for non-terrain).
    """
    rock_grid = np.full(terrain_grid.shape, -1, dtype=np.int8)
    
    if terrain_height is None:
        # Infer terrain height from grid z-extent of frozen cells
        frozen_mask = terrain_grid > 0
        if not frozen_mask.any():
            return rock_grid
        z_coords = np.where(frozen_mask)[2]
        terrain_height = int(z_coords.max() - z_coords.min()) + 1 if len(z_coords) > 0 else 32
    
    frozen_mask = terrain_grid > 0
    if not frozen_mask.any():
        return rock_grid
    
    z_indices = np.where(frozen_mask)[2]
    z_min = z_indices.min()
    
    for z in range(terrain_height):
        z_fraction = z / max(terrain_height, 1)
        layer = np.where(
            frozen_mask & (np.indices(terrain_grid.shape, dtype=int)[2] == z_min + z)
        )
        for z_min_frac, z_max_frac, rock_idx in STRATA:
            if z_min_frac <= z_fraction < z_max_frac:
                rock_grid[layer] = rock_idx
                break
    
    return rock_grid


def geology_description(rock_grid: np.ndarray) -> str:
    """Generate a human-readable geology description.
    
    Args:
        rock_grid: int8 array from assign_strata().
        
    Returns:
        String like "Surface: regolith over sandstone over limestone over granite"
    """
    unique_rocks = sorted(set(rock_grid[rock_grid >= 0].flatten()))
    if not unique_rocks:
        return "Uniform substrate (no visible strata)"
    
    layers = [ROCK_TYPES[r] for r in unique_rocks]
    if len(layers) == 1:
        return f"Homogeneous {layers[0]} substrate"
    
    description = "Visible strata: "
    description += " over ".join(
        f"{r} ({_layer_description(r)})" for r in layers
    )
    return description


def _layer_description(rock_type: str) -> str:
    """One-line educational note about a rock type."""
    descriptions = {
        "regolith_breccia": "broken surface debris, wind-deposited",
        "sedimentary_sandstone": "compressed ancient dune beds, cross-bedding visible",
        "sedimentary_limestone": "marine fossil layer, calcium carbonate precipitate",
        "metamorphic_schist": "heat/pressure altered, foliation planes visible",
        "igneous_granite": "slow-cooled magma chamber, large crystal grains",
        "igneous_basalt": "rapid-cooled volcanic flow, columnar jointing",
    }
    return descriptions.get(rock_type, "")


def surface_rock_type(rock_grid: np.ndarray) -> str:
    """Return the rock type at the terrain surface (topmost layer)."""
    for x in range(rock_grid.shape[0]):
        for y in range(rock_grid.shape[1]):
            for z in range(rock_grid.shape[2] - 1, -1, -1):
                if rock_grid[x, y, z] >= 0:
                    return ROCK_TYPES[int(rock_grid[x, y, z])]
    return "unknown"


def rock_hardness(rock_type_idx: int) -> float:
    """Hardness scale 1-10 for a rock type. Higher = harder to erode."""
    hardness = {
        0: 1.0,   # regolith
        1: 3.0,   # sandstone
        2: 4.0,   # limestone
        3: 6.0,   # schist
        4: 8.0,   # granite
        5: 9.0,   # basalt
    }
    return hardness.get(rock_type_idx, 1.0)
