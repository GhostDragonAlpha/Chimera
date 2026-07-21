"""
Infinite World Generator — procedural + ML + Nanite LOD.

Architecture:
  World coordinate → hash → latent vector → VAE → clusters → render

Each region (e.g., 100m³) generates its own cluster tree.
Only regions near the camera are generated.
Cluster trees stream in/out based on camera position.

Minecraft meets Nanite meets 3DGS.
"""

import numpy as np
import math
import hashlib
from dataclasses import dataclass, field
from pathlib import Path


REGION_SIZE = 100.0  # meters per region
MAX_LOADED_REGIONS = 64


@dataclass
class WorldRegion:
    """A spatial region containing a cluster tree and splat data."""
    grid_x: int
    grid_y: int
    grid_z: int
    cluster_tree: "ClusterTree | None" = None
    positions: np.ndarray | None = None
    colors: np.ndarray | None = None
    opacities: np.ndarray | None = None
    scales: np.ndarray | None = None
    rotations: np.ndarray | None = None
    last_accessed: float = 0.0
    generated: bool = False

    @property
    def key(self) -> tuple:
        return (self.grid_x, self.grid_y, self.grid_z)

    @property
    def world_center(self) -> np.ndarray:
        return np.array([
            self.grid_x * REGION_SIZE + REGION_SIZE / 2,
            self.grid_y * REGION_SIZE + REGION_SIZE / 2,
            self.grid_z * REGION_SIZE + REGION_SIZE / 2,
        ], dtype=np.float32)

    @property
    def world_bounds(self) -> np.ndarray:
        c = self.world_center
        h = REGION_SIZE / 2
        return np.array([
            [c[0] - h, c[1] - h, c[2] - h],
            [c[0] + h, c[1] + h, c[2] + h],
        ], dtype=np.float32)


class InfiniteWorld:
    """
    Infinite world generator using spatial hashing + VAE + Nanite.

    Usage:
        world = InfiniteWorld()
        world.update(camera_position)
        clusters = world.visible_clusters(camera_position, camera_params)
        pipe.render_clusters(clusters)
    """

    def __init__(self, region_size: float = REGION_SIZE):
        self.region_size = region_size
        self.regions: dict[tuple, WorldRegion] = {}
        self._access_counter = 0
        self.seed = 42

    def world_to_grid(self, pos: np.ndarray) -> tuple[int, int, int]:
        """Convert world position to region grid coordinates."""
        return (
            int(math.floor(pos[0] / self.region_size)),
            int(math.floor(pos[1] / self.region_size)),
            int(math.floor(pos[2] / self.region_size)),
        )

    def _region_hash(self, gx: int, gy: int, gz: int) -> int:
        """Deterministic hash for a region's content."""
        key = f"{gx},{gy},{gz},{self.seed}"
        return int(hashlib.sha256(key.encode()).hexdigest()[:16], 16)

    def _generate_region(self, region: WorldRegion):
        """Generate splats for a region using procedural rules."""
        hash_val = self._region_hash(region.grid_x, region.grid_y, region.grid_z)
        rng = np.random.RandomState(hash_val % (2**31))

        c = region.world_center
        n = 2000  # splats per region

        # Terrain height based on world position (simple noise)
        terrain_h = c[2] + math.sin(c[0] * 0.02) * 30 + math.cos(c[1] * 0.02) * 30

        positions = np.zeros((n, 3), dtype=np.float32)
        colors = np.zeros((n, 3), dtype=np.float32)
        opacities = np.ones(n, dtype=np.float32) * 0.8
        scales = np.ones((n, 3), dtype=np.float32) * 2.0
        rotations = np.tile(np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32), (n, 1))

        # Ground layer
        for i in range(n // 2):
            x = c[0] + rng.uniform(-self.region_size/2, self.region_size/2)
            y = c[1] + rng.uniform(-self.region_size/2, self.region_size/2)
            h = terrain_h + math.sin(x*0.05)*math.cos(y*0.05)*10
            z = h - 10 + rng.uniform(0, 20)
            positions[i] = [x, y, z]
            # Brown/green ground
            g = rng.uniform(2, 8)/10
            colors[i] = [rng.uniform(2, 4)/10, rng.uniform(3, 7)/10, g]
            scales[i] = [rng.uniform(1, 3), rng.uniform(1, 3), rng.uniform(0.5, 2)]

        # Vegetation/atmosphere
        for i in range(n // 2, n):
            x = c[0] + rng.uniform(-self.region_size/2, self.region_size/2)
            y = c[1] + rng.uniform(-self.region_size/2, self.region_size/2)
            z = terrain_h + rng.uniform(0, 80)
            positions[i] = [x, y, z]
            colors[i] = [rng.uniform(1, 3)/10, rng.uniform(3, 7)/10, rng.uniform(1, 3)/10]
            opacities[i] = rng.uniform(0.1, 0.4)
            scales[i] = [rng.uniform(3, 8), rng.uniform(3, 8), rng.uniform(3, 8)]

        region.positions = positions
        region.colors = colors
        region.opacities = opacities
        region.scales = scales
        region.rotations = rotations

        # Build cluster tree
        from WorldModel.nanite import build_cluster_tree
        region.cluster_tree = build_cluster_tree(positions, max_depth=3)
        region.generated = True

    def update(self, camera_pos: np.ndarray):
        """Load/unload regions based on camera position."""
        grid = self.world_to_grid(camera_pos)

        # Which regions should be loaded? (3×3×3 cube around camera)
        needed = set()
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                for dz in range(-1, 2):
                    needed.add((grid[0] + dx, grid[1] + dy, grid[2] + dz))

        # Generate new regions
        for key in needed:
            if key not in self.regions:
                region = WorldRegion(*key)
                self._generate_region(region)
                self.regions[key] = region
            self.regions[key].last_accessed = self._access_counter

        # Unload distant regions
        if len(self.regions) > MAX_LOADED_REGIONS:
            sorted_regions = sorted(self.regions.values(),
                                    key=lambda r: r.last_accessed)
            for region in sorted_regions[:len(self.regions) - MAX_LOADED_REGIONS]:
                if region.key not in needed:
                    del self.regions[region.key]

        self._access_counter += 1

    def visible_clusters(self, camera_pos: np.ndarray,
                         screen_height: int, fov: float) -> list:
        """Get all visible clusters across loaded regions."""
        all_clusters = []
        for region in self.regions.values():
            if region.cluster_tree:
                clusters = region.cluster_tree.select_clusters(
                    camera_pos, screen_height, fov,
                    np.linalg.norm(camera_pos - region.world_center)
                )
                for c in clusters:
                    # Adjust indices to global splat pool (not implemented yet — return region+splat)
                    c._region = region
                    all_clusters.append(c)
        return all_clusters

    def get_splat_data(self, clusters: list) -> dict:
        """Extract splat data from selected clusters."""
        all_pos = []; all_col = []; all_opa = []; all_sca = []; all_rot = []
        for c in clusters:
            region = getattr(c, '_region', None)
            if region is None:
                continue
            idx = np.array(c.splat_indices)
            all_pos.append(region.positions[idx])
            all_col.append(region.colors[idx])
            all_opa.append(region.opacities[idx])
            all_sca.append(region.scales[idx])
            all_rot.append(region.rotations[idx])

        if not all_pos:
            return {"positions": np.empty((0,3)), "colors": np.empty((0,3)),
                    "opacities": np.empty(0), "scales": np.empty((0,3)),
                    "rotations": np.empty((0,4))}

        return {
            "positions": np.concatenate(all_pos),
            "colors": np.concatenate(all_col),
            "opacities": np.concatenate(all_opa),
            "scales": np.concatenate(all_sca),
            "rotations": np.concatenate(all_rot),
        }
