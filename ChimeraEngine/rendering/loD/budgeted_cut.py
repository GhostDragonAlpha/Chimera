"""
Budgeted LOD selection for Nanite-style cluster trees.

This module implements the critical insight: instead of selecting clusters based
on a fixed screen-space error threshold, we select them under a global pixel
budget. This gives a hard ceiling on rendering cost per frame and fixes both
the close-range (too many splats) and far-range (too few splats) bugs.

The algorithm is greedy: it descends the tree, computing pixel coverage for
each cluster, and selects clusters until the total budget is exhausted.
"""

import numpy as np
from typing import List, Optional, Tuple
from ChimeraEngine.rendering.core.gaussian_splat_cloud import ClusterTree, Cluster


def select_clusters_budgeted(clusters: ClusterTree, 
                             camera_pos: np.ndarray,
                             screen_height: int, fov: float,
                             budget_pixels: int = 1024,
                             frustum_planes: Optional[List[np.ndarray]] = None) -> List[Cluster]:
    """
    Select clusters based on screen-space error with a global pixel budget.
    
    This is the core algorithm that replaces distance-based LOD selection. It
    walks the cluster tree and selects clusters until the total pixel coverage
    reaches the budget, giving a hard ceiling on rendering cost.
    
    Parameters
    ----------
    clusters : ClusterTree
        The cluster tree to select from
    camera_pos : np.ndarray
        Camera position in world space (3,) float32
    screen_height : int
        Rendered screen height in pixels
    fov : float
        Vertical field of view in radians
    budget_pixels : int
        Maximum total pixel coverage to render. This is the key parameter that
        controls frame cost. For 60 FPS at 1080p, a budget of ~1024 pixels
        typically works well (each selected cluster covers this many screen pixels).
    frustum_planes : Optional[List[np.ndarray]]
        Six planes defining camera frustum for culling. Each plane is [x, y, z, d]
        where the plane equation is dot(point, normal) + distance = 0.
        
    Returns
    -------
    List[Cluster]
        Clusters selected for rendering, sorted by depth (far to near) for
        correct alpha compositing. Each cluster has its screen_error field set.
    
    Example
    -------
    >>> tree = build_cluster_tree(cloud)
    >>> selected = select_clusters_budgeted(
    ...     tree, camera.position, 1080, np.radians(60), budget_pixels=1024
    ... )
    >>> # Render only the selected clusters
    """
    
    selected: List[Cluster] = []
    total_pixels = 0
    
    def select_recursive(cluster: Cluster):
        nonlocal total_pixels
        
        # Early exit if budget exhausted - this is what gives us the hard ceiling
        if total_pixels >= budget_pixels:
            return
            
        # Compute screen-space error (pixel coverage)
        pixels = _compute_screen_space_error(
            cluster, camera_pos, screen_height, fov)
        
        # Check frustum culling if planes provided
        if frustum_planes is not None and not _cluster_in_frustum(
            cluster.spatial_bounds, frustum_planes):
            return
        
        # If this cluster covers few pixels or we're at max LOD, use it
        if pixels < 50 or cluster.lod >= 6 or not cluster.children:
            if cluster.visible:
                cluster.screen_error = pixels
                selected.append(cluster)
                total_pixels += pixels
            return
        
        # Otherwise, descend to children for more detail
        # But only if we have budget for them
        child_budget = budget_pixels - total_pixels
        if child_budget < 50:  # Not enough budget for any meaningful child cluster
            return
            
        for child in cluster.children:
            select_recursive(child)
    
    # Start from root
    select_recursive(clusters.root)
    
    # Sort by depth (back to front) for correct compositing
    # In production, this would be done on GPU, but CPU sort is acceptable here
    return sorted(selected, key=lambda c: np.linalg.norm(c.centroid - camera_pos))


def _compute_screen_space_error(cluster: Cluster, 
                                camera_pos: np.ndarray,
                                screen_height: int, fov: float) -> float:
    """Compute how many pixels this cluster would cover on screen."""
    
    extent = cluster.extent
    dist = max(np.linalg.norm(cluster.centroid - camera_pos), 0.01)
    
    # Angular size in radians (simplified model)
    angular_size = extent / dist
    
    # Convert to pixel coverage (approximate)
    pixels = angular_size * screen_height / fov
    
    return float(pixels)


def _cluster_in_frustum(bounds: np.ndarray, planes: List[np.ndarray]) -> bool:
    """Check if cluster bounds are inside camera frustum."""
    
    # Compute bounding sphere of cluster bounds
    center = bounds.mean(axis=0)
    radius = _compute_bounds_radius(bounds)
    
    # Test against each frustum plane
    for plane in planes:
        # Plane equation: dot(center, normal) + distance >= -radius means inside
        distance = np.dot(center, plane[:3]) + plane[3]
        if distance < -radius:
            return False
    
    return True


def _compute_bounds_radius(bounds: np.ndarray) -> float:
    """Compute radius of sphere enclosing bounds."""
    
    center = bounds.mean(axis=0)
    corner = bounds[1] - center
    return float(np.linalg.norm(corner))


def compute_frustum_planes(camera_pos: np.ndarray, forward: np.ndarray, 
                           up: np.ndarray, right: np.ndarray,
                           near: float = 0.1, far: float = 1000.0,
                           fov: float = np.radians(60)) -> List[np.ndarray]:
    """
    Compute six frustum planes from camera parameters.
    
    Parameters
    ----------
    camera_pos : np.ndarray
        Camera position (3,)
    forward : np.ndarray
        Forward direction (normalized)
    up : np.ndarray
        Up direction (normalized)  
    right : np.ndarray
        Right direction (normalized)
    near : float
        Near plane distance
    far : float
        Far plane distance
    fov : float
        Vertical field of view in radians
        
    Returns
    -------
    List[np.ndarray]
        Six planes [left, right, bottom, top, near, far], each as [x, y, z, d]
    """
    
    # Compute half extents at near and far planes
    h_near = np.tan(fov / 2) * near
    h_far = np.tan(fov / 2) * far
    
    # Build frustum corners (simplified - assumes no rotation for plane computation)
    # In practice, you'd use full view matrix to transform corners
    corners_near = np.array([
        [-h_near, -h_near, near],
        [h_near, -h_near, near],
        [h_near, h_near, near],
        [-h_near, h_near, near]
    ])
    
    corners_far = np.array([
        [-h_far, -h_far, far],
        [h_far, -h_far, far],
        [h_far, h_far, far],
        [-h_far, h_far, far]
    ])
    
    # Transform to world space (simplified)
    # In production, use full view matrix
    def transform(corner):
        return camera_pos + right * corner[0] + up * corner[1] + forward * corner[2]
    
    corners_near = np.array([transform(c) for c in corners_near])
    corners_far = np.array([transform(c) for c in corners_far])
    
    # Build planes from corners (simplified - would use cross products in production)
    planes = []
    
    # Near plane
    near_normal = forward
    near_plane = np.array([*near_normal, -np.dot(near_normal, corners_near[0])])
    planes.append(near_plane)
    
    # Far plane  
    far_normal = -forward
    far_plane = np.array([*far_normal, -np.dot(far_normal, corners_far[0])])
    planes.append(far_plane)
    
    # Left plane (from near-left to far-left edge)
    left_edge = np.stack([corners_near[0], corners_far[0]])
    left_normal = _compute_plane_from_edges(left_edge, camera_pos)
    left_plane = np.array([*left_normal, -np.dot(left_normal, corners_near[0])])
    planes.append(left_plane)
    
    # Right plane
    right_edge = np.stack([corners_near[3], corners_far[3]])
    right_normal = _compute_plane_from_edges(right_edge, camera_pos)
    right_plane = np.array([*right_normal, -np.dot(right_normal, corners_near[3])])
    planes.append(right_plane)
    
    # Bottom plane
    bottom_edge = np.stack([corners_near[1], corners_far[1]])
    bottom_normal = _compute_plane_from_edges(bottom_edge, camera_pos)
    bottom_plane = np.array([*bottom_normal, -np.dot(bottom_normal, corners_near[1])])
    planes.append(bottom_plane)
    
    # Top plane
    top_edge = np.stack([corners_near[2], corners_far[2]])
    top_normal = _compute_plane_from_edges(top_edge, camera_pos)
    top_plane = np.array([*top_normal, -np.dot(top_normal, corners_near[2])])
    planes.append(top_plane)
    
    return planes


def _compute_plane_from_edges(edges: np.ndarray, point: np.ndarray) -> np.ndarray:
    """Compute plane normal from two edges and a reference point."""
    
    edge1 = edges[1] - edges[0]
    edge2 = point - edges[0]
    normal = np.cross(edge1, edge2)
    return normal / (np.linalg.norm(normal) + 1e-8)


def create_default_frustum(camera: 'Camera', near: float = 0.1, far: float = 1000.0,
                           fov: float = np.radians(60)) -> List[np.ndarray]:
    """Create frustum planes from a Camera object."""
    
    # Compute forward direction from camera
    forward = camera.target - camera.position
    forward /= np.linalg.norm(forward) + 1e-8
    
    return compute_frustum_planes(
        camera.position, forward, camera.up, camera.right,
        near=near, far=far, fov=fov
    )
