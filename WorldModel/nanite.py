"""
Nanite-inspired hierarchical Gaussian splat system.

Concept (from UE5 Nanite):
  1. Objects are decomposed into CLUSTERS of fixed size (e.g., 1024 splats)
  2. Clusters form a LOD HIERARCHY (coarse → fine)
  3. At render time, CLUSTER SELECTION based on screen-space error
  4. Only visible clusters at the right LOD are rendered
  5. Clusters can be STREAMED from disk/network

This makes the world model SCALABLE:
  - Train a VAE per cluster level (not per object)
  - Generate clusters on demand
  - Assemble into infinite worlds

Cluster tree:
  LOD 0: 1 cluster    (1024 splats)  — whole object, coarse
  LOD 1: 4 clusters   (4096 splats)  — quadrants
  LOD 2: 16 clusters  (16K splats)   — sub-quadrants
  LOD 3: 64 clusters  (65K splats)   — fine detail
"""

import numpy as np
import math
from dataclasses import dataclass, field
from typing import Optional


SPLATS_PER_CLUSTER = 1024
MAX_LOD = 6


@dataclass
class Cluster:
    """A fixed-size group of Gaussian splats at a specific LOD level."""
    lod: int                    # 0 = coarsest
    spatial_bounds: np.ndarray  # (2, 3) — [[min_x,min_y,min_z], [max_x,max_y,max_z]]
    parent: Optional["Cluster"] = None
    children: list["Cluster"] = field(default_factory=list)
    splat_indices: list[int] = field(default_factory=list)  # indices into splat pool
    screen_error: float = 0.0   # computed at render time
    visible: bool = True

    @property
    def centroid(self) -> np.ndarray:
        return self.spatial_bounds.mean(axis=0)

    @property
    def extent(self) -> float:
        return float(np.linalg.norm(
            self.spatial_bounds[1] - self.spatial_bounds[0]))


@dataclass
class ClusterTree:
    """Hierarchical LOD tree for a single object or region."""
    root: Cluster
    all_clusters: list[Cluster] = field(default_factory=list)

    def select_clusters(self, camera_pos: np.ndarray, screen_height: int,
                        fov: float, distance: float) -> list[Cluster]:
        """
        Nanite-style cluster selection.
        Walk the tree; for each cluster, compute screen-space error.
        If error > threshold, descend to children. Otherwise, render this cluster.
        """
        selected = []
        self._select_recursive(self.root, camera_pos, screen_height, fov,
                                distance, selected)
        return selected

    def _select_recursive(self, cluster: Cluster, cam_pos, screen_h, fov,
                          distance, selected):
        # Screen-space error: how many pixels does this cluster's extent cover?
        extent = cluster.extent
        dist = max(np.linalg.norm(cluster.centroid - cam_pos), 0.01)
        angular_size = extent / dist
        pixels = angular_size * screen_h / fov  # approximate pixel coverage

        # If this cluster covers few pixels or we're at max LOD, use it
        if pixels < 50 or cluster.lod >= MAX_LOD or not cluster.children:
            if cluster.visible:
                cluster.screen_error = pixels
                selected.append(cluster)
            return

        # Otherwise, descend to children for more detail
        for child in cluster.children:
            self._select_recursive(child, cam_pos, screen_h, fov, distance, selected)


def build_cluster_tree(positions: np.ndarray, indices: np.ndarray = None,
                        max_depth: int = 4) -> ClusterTree:
    """
    Build a Nanite-style cluster tree from a point cloud.

    positions: (N, 3) world positions of all splats
    indices: (N,) optional global index mapping
    max_depth: maximum LOD depth

    Algorithm: recursive octree subdivision.
    Each node holds up to SPLATS_PER_CLUSTER splats.
    If a node exceeds capacity, subdivide into 8 children.
    """
    if indices is None:
        indices = np.arange(len(positions))

    bounds_min = positions.min(axis=0)
    bounds_max = positions.max(axis=0)
    bounds = np.stack([bounds_min, bounds_max])

    all_clusters = []
    root = _subdivide(positions, indices, bounds, depth=0, max_depth=max_depth,
                      all_clusters=all_clusters)
    return ClusterTree(root=root, all_clusters=all_clusters)


def _subdivide(positions, indices, bounds, depth, max_depth, all_clusters):
    """Recursive cluster subdivision."""
    n = len(indices)

    # Create this cluster
    cluster = Cluster(
        lod=depth,
        spatial_bounds=bounds.copy(),
        splat_indices=indices.tolist(),
    )
    all_clusters.append(cluster)

    # If we're within capacity or at max depth, stop
    if n <= SPLATS_PER_CLUSTER or depth >= max_depth:
        return cluster

    # Subdivide into octants
    center = bounds.mean(axis=0)
    pos = positions[indices]

    for i in range(8):
        # Which octant?
        x_sign = 1 if (i & 1) else 0
        y_sign = 1 if (i & 2) else 0
        z_sign = 1 if (i & 4) else 0

        if x_sign:
            child_min_x = center[0]; child_max_x = bounds[1, 0]
        else:
            child_min_x = bounds[0, 0]; child_max_x = center[0]

        if y_sign:
            child_min_y = center[1]; child_max_y = bounds[1, 1]
        else:
            child_min_y = bounds[0, 1]; child_max_y = center[1]

        if z_sign:
            child_min_z = center[2]; child_max_z = bounds[1, 2]
        else:
            child_min_z = bounds[0, 2]; child_max_z = center[2]

        child_bounds = np.array([
            [child_min_x, child_min_y, child_min_z],
            [child_max_x, child_max_y, child_max_z],
        ])

        # Find splats in this octant
        mask = (
            (pos[:, 0] >= child_bounds[0, 0]) & (pos[:, 0] < child_bounds[1, 0]) &
            (pos[:, 1] >= child_bounds[0, 1]) & (pos[:, 1] < child_bounds[1, 1]) &
            (pos[:, 2] >= child_bounds[0, 2]) & (pos[:, 2] < child_bounds[1, 2])
        )
        child_indices = indices[mask]

        if len(child_indices) > 0:
            child = _subdivide(positions, child_indices, child_bounds,
                               depth + 1, max_depth, all_clusters)
            cluster.children.append(child)
            child.parent = cluster

    return cluster


def cluster_to_splat_cloud(cluster: Cluster, all_positions: np.ndarray,
                           all_colors: np.ndarray, all_opacities: np.ndarray,
                           all_scales: np.ndarray, all_rotations: np.ndarray):
    """Extract the splat data for a single cluster."""
    idx = np.array(cluster.splat_indices)
    from WorldModel.splat_io import SplatCloud
    return SplatCloud(
        positions=all_positions[idx],
        colors=all_colors[idx],
        opacities=all_opacities[idx],
        scales=all_scales[idx],
        rotations=all_rotations[idx],
    )


def generate_lod_level(cloud, target_lod: int,
                        base_scale: float = 1.0) -> "SplatCloud":
    """
    Generate a coarser LOD representation of a splat cloud.

    For LOD 0 (coarsest): merge splats within spatial bins, create
    fewer, larger splats that approximate the original.

    For LOD N: keep every (target_lod+1)^3 splats.
    """
    from WorldModel.splat_io import SplatCloud

    if target_lod == 0:
        # Coarsest: just keep a sparse subset
        stride = max(1, cloud.count // SPLATS_PER_CLUSTER)
        idx = np.arange(0, cloud.count, stride)[:SPLATS_PER_CLUSTER]
        return SplatCloud(
            positions=cloud.positions[idx],
            colors=cloud.colors[idx],
            opacities=cloud.opacities[idx],
            scales=cloud.scales[idx] * base_scale,
            rotations=cloud.rotations[idx],
        )

    # Higher LOD: keep more splats
    stride = max(1, 2 ** (MAX_LOD - target_lod))
    idx = np.arange(0, cloud.count, stride)
    return SplatCloud(
        positions=cloud.positions[idx],
        colors=cloud.colors[idx],
        opacities=cloud.opacities[idx],
        scales=cloud.scales[idx],
        rotations=cloud.rotations[idx],
    )
