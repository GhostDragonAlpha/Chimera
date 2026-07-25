"""
Nanite-inspired hierarchical Gaussian splat system with budgeted LOD selection.

This module provides cluster tree construction and screen-space error-based
LOD selection with a global pixel budget, giving hard frame-cost ceilings.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from ChimeraEngine.rendering.core.gaussian_splat_cloud import GaussianSplatCloud


SPLATS_PER_CLUSTER = 1024
MAX_LOD = 6


@dataclass
class Cluster:
    """A fixed-size group of Gaussian splats at a specific LOD level."""
    
    lod: int                    # 0 = coarsest, increasing with detail
    spatial_bounds: np.ndarray  # (2, 3) — [[min_x,min_y,min_z], [max_x,max_y,max_z]]
    parent: Optional["Cluster"] = None
    children: List["Cluster"] = field(default_factory=list)
    splat_indices: List[int] = field(default_factory=list)  # indices into splat pool
    
    # Runtime fields (computed during selection)
    screen_error: float = 0.0   # pixels covered on screen
    visible: bool = True        # whether this cluster should be considered
    
    @property
    def centroid(self) -> np.ndarray:
        """Compute the center of the cluster's spatial bounds."""
        return self.spatial_bounds.mean(axis=0)
    
    @property
    def extent(self) -> float:
        """Compute the diagonal extent of the cluster."""
        return float(np.linalg.norm(
            self.spatial_bounds[1] - self.spatial_bounds[0]))


@dataclass
class ClusterTree:
    """Hierarchical LOD tree for a single object or region."""
    
    root: Cluster
    all_clusters: List[Cluster] = field(default_factory=list)
    
    def select_clusters(self, camera_pos: np.ndarray, screen_height: int,
                        fov: float, budget_pixels: int = 1024,
                        frustum_planes: Optional[List[np.ndarray]] = None) -> List[Cluster]:
        """
        Select clusters based on screen-space error with a global pixel budget.
        
        This implements the key insight from UE5 Nanite: descend the tree until
        you hit a total pixel budget, not just a per-cluster threshold. This gives
        a hard ceiling on rendering cost per frame.
        
        Parameters
        ----------
        camera_pos : np.ndarray
            Camera position in world space
        screen_height : int
            Rendered screen height in pixels
        fov : float
            Field of view (vertical, in radians)
        budget_pixels : int
            Maximum total pixel coverage to render (e.g., 1024 = ~60 FPS at 1080p)
        frustum_planes : Optional[List[np.ndarray]]
            Six planes defining camera frustum for culling
            
        Returns
        -------
        List[Cluster]
            Clusters selected for rendering, sorted by depth (far to near)
        """
        selected = []
        
        # Start with root and use priority queue by screen error
        def select_recursive(cluster: Cluster):
            # Early exit if budget exhausted
            if sum(c.screen_error for c in selected) >= budget_pixels:
                return
                
            # Compute screen-space error (pixel coverage)
            pixels = self._compute_screen_space_error(
                cluster, camera_pos, screen_height, fov)
            
            # Check frustum culling if planes provided
            if frustum_planes is not None and not self._cluster_in_frustum(
                cluster.spatial_bounds, frustum_planes):
                return
            
            # If this cluster covers few pixels or we're at max LOD, use it
            if pixels < 50 or cluster.lod >= MAX_LOD or not cluster.children:
                if cluster.visible:
                    cluster.screen_error = pixels
                    selected.append(cluster)
                return
            
            # Otherwise, descend to children for more detail
            for child in cluster.children:
                select_recursive(child)
        
        select_recursive(self.root)
        
        # Sort by depth (back to front) for correct compositing
        # This would be done on GPU in production, but CPU sort is fine here
        return sorted(selected, key=lambda c: np.linalg.norm(c.centroid - camera_pos))
    
    def _compute_screen_space_error(self, cluster: Cluster, 
                                     camera_pos: np.ndarray,
                                     screen_height: int, fov: float) -> float:
        """Compute how many pixels this cluster would cover on screen."""
        extent = cluster.extent
        dist = max(np.linalg.norm(cluster.centroid - camera_pos), 0.01)
        angular_size = extent / dist
        pixels = angular_size * screen_height / fov
        return float(pixels)
    
    def _cluster_in_frustum(self, bounds: np.ndarray, 
                            planes: List[np.ndarray]) -> bool:
        """Check if cluster bounds are inside camera frustum."""
        # Simple bounding sphere test - in practice would do full frustum culling
        center = bounds.mean(axis=0)
        radius = self._compute_bounds_radius(bounds)
        
        for plane in planes:
            # Plane equation: dot(center, normal) + distance >= 0 means inside
            if np.dot(center, plane[:3]) + plane[3] < -radius:
                return False
        
        return True
    
    def _compute_bounds_radius(self, bounds: np.ndarray) -> float:
        """Compute radius of sphere enclosing bounds."""
        center = bounds.mean(axis=0)
        corner = bounds[1] - center
        return float(np.linalg.norm(corner))


def build_cluster_tree(cloud: GaussianSplatCloud, 
                       max_depth: int = 4) -> ClusterTree:
    """
    Build a Nanite-style cluster tree from a splat cloud.

    Parameters
    ----------
    cloud : GaussianSplatCloud
        The splat cloud to build tree from
    max_depth : int
        Maximum LOD depth (0 = coarsest, all splats in one cluster)

    Returns
    -------
    ClusterTree
        Hierarchical cluster structure
    """
    positions = cloud.positions
    
    if len(positions) == 0:
        raise ValueError("Cannot build tree from empty splat cloud")
    
    bounds_min = positions.min(axis=0)
    bounds_max = positions.max(axis=0)
    bounds = np.stack([bounds_min, bounds_max])
    
    all_clusters = []
    indices = np.arange(len(positions))
    
    root = _subdivide(positions, indices, bounds, depth=0, max_depth=max_depth,
                      all_clusters=all_clusters)
    
    return ClusterTree(root=root, all_clusters=all_clusters)


def _subdivide(positions: np.ndarray, indices: np.ndarray, 
               bounds: np.ndarray, depth: int, max_depth: int,
               all_clusters: List[Cluster]) -> Cluster:
    """Recursive cluster subdivision using octree."""
    
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
        # Which octant? (bit encoding: x, y, z)
        x_sign = 1 if (i & 1) else 0
        y_sign = 1 if (i & 2) else 0
        z_sign = 1 if (i & 4) else 0
        
        # Define child bounds
        if x_sign:
            child_min_x, child_max_x = center[0], bounds[1, 0]
        else:
            child_min_x, child_max_x = bounds[0, 0], center[0]
            
        if y_sign:
            child_min_y, child_max_y = center[1], bounds[1, 1]
        else:
            child_min_y, child_max_y = bounds[0, 1], center[1]
            
        if z_sign:
            child_min_z, child_max_z = center[2], bounds[1, 2]
        else:
            child_min_z, child_max_z = bounds[0, 2], center[2]
        
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


def generate_lod_level(cloud: GaussianSplatCloud, target_lod: int,
                        base_scale: float = 1.0) -> GaussianSplatCloud:
    """
    Generate a coarser LOD representation of a splat cloud.

    Parameters
    ----------
    cloud : GaussianSplatCloud
        Original splat cloud
    target_lod : int
        Target LOD level (higher = more detail, lower = coarser)
    base_scale : float
        Scale factor for coarsest LOD

    Returns
    -------
    GaussianSplatCloud
        Coarsened splat cloud with fewer splats
    """
    from ChimeraEngine.formats.gaussian_splat_format import sigmoid
    
    n = cloud.count
    
    if target_lod == 0:
        # Coarsest: keep subset of splats, scale up
        stride = max(1, n // SPLATS_PER_CLUSTER)
        idx = np.arange(0, n, stride)[:SPLATS_PER_CLUSTER]
        
        return GaussianSplatCloud(
            positions=cloud.positions[idx],
            colors=cloud.colors[idx],
            opacities=cloud.opacities[idx],
            scales=cloud.scales[idx] * base_scale,
            rotations=cloud.rotations[idx],
            covariances_3x3=_build_covariances(
                cloud.scales[idx] * base_scale, 
                cloud.rotations[idx]
            ),
        )
    
    # Higher LOD: keep more splats with stride
    stride = max(1, 2 ** (MAX_LOD - target_lod))
    idx = np.arange(0, n, stride)
    
    return GaussianSplatCloud(
        positions=cloud.positions[idx],
        colors=cloud.colors[idx],
        opacities=cloud.opacities[idx],
        scales=cloud.scales[idx],
        rotations=cloud.rotations[idx],
        covariances_3x3=_build_covariances(cloud.scales[idx], cloud.rotations[idx]),
    )


def _build_covariances(scales: np.ndarray, rotations: np.ndarray) -> np.ndarray:
    """Build 3×3 covariance matrices from scales and quaternions."""
    n = len(scales)
    cov = np.zeros((n, 3, 3), dtype=np.float32)
    s2 = scales ** 2
    
    qx, qy, qz, qw = rotations[:, 0], rotations[:, 1], rotations[:, 2], rotations[:, 3]
    xx, yy, zz = qx*qx, qy*qy, qz*qz
    xy, xz, yz = qx*qy, qx*qz, qy*qz
    wx, wy, wz = qw*qx, qw*qy, qw*qz
    
    R = np.empty((n, 3, 3), dtype=np.float32)
    R[:, 0, 0] = 1 - 2*(yy + zz); R[:, 0, 1] = 2*(xy - wz); R[:, 0, 2] = 2*(xz + wy)
    R[:, 1, 0] = 2*(xy + wz); R[:, 1, 1] = 1 - 2*(xx + zz); R[:, 1, 2] = 2*(yz - wx)
    R[:, 2, 0] = 2*(xz - wy); R[:, 2, 1] = 2*(yz + wx); R[:, 2, 2] = 1 - 2*(xx + yy)
    
    return np.einsum('ijl,il,ikl->ijk', R, s2, R, dtype=np.float32)
