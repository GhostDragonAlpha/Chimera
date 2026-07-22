"""
Unified Gaussian Splat Cloud representation for Chimera Engine.

This is the canonical format that all rendering and LOD systems use.
Based on standard 3DGS .ply layout but with enhanced metadata.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Optional, List, Tuple


@dataclass
class GaussianSplatCloud:
    """In-memory representation of a 3D Gaussian splat cloud."""
    
    # Core attributes (required)
    positions: np.ndarray        # (N, 3) float32 - world positions
    colors: np.ndarray           # (N, 3) float32 - base color (RGB)
    opacities: np.ndarray        # (N,) float32 - opacity values [0, 1]
    scales: np.ndarray           # (N, 3) float32 - scaling factors (log-scale in storage)
    rotations: np.ndarray        # (N, 4) float32 - quaternions xyzw (normalized)
    covariances_3x3: np.ndarray  # (N, 3, 3) float32 - precomputed covariance matrices
    
    # Metadata (optional but recommended)
    id: Optional[int] = None     # Unique identifier for this cloud
    source_path: Optional[str] = None  # Original file path if loaded from disk
    created_at: Optional[float] = None  # Timestamp of creation
    
    @property
    def count(self) -> int:
        """Number of splats in the cloud."""
        return len(self.positions)
    
    def get_view(self) -> Tuple[np.ndarray, ...]:
        """Return tuple of device/host pointers for GPU access."""
        return (self.positions, self.colors, self.opacities, 
                self.scales, self.rotations, self.covariances_3x3)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization or debugging."""
        return {
            "count": int(self.count),
            "id": self.id,
            "positions_mean": self.positions.mean(axis=0).tolist(),
            "positions_std": self.positions.std(axis=0).tolist(),
            "extent": float(np.linalg.norm(
                self.positions.max(axis=0) - self.positions.min(axis=0))),
            "mean_opacity": float(self.opacities.mean()),
            "mean_scale": self.scales.mean(axis=0).tolist(),
        }


class SplatPool:
    """GPU-resident splat pool for efficient rendering.
    
    Uploads splat data once and keeps it on device, avoiding per-frame
    CPU↔GPU syncs that kill performance.
    """
    
    def __init__(self, max_splats: int = 10_000_000):
        self.max_splats = max_splats
        self.current_count = 0
        
        # Allocate device arrays once (will be filled on first upload)
        self.d_positions = None
        self.d_colors = None
        self.d_opacities = None
        self.d_scales = None
        self.d_rotations = None
        self.d_covariances = None
        
    def upload(self, cloud: GaussianSplatCloud) -> None:
        """Upload splat data once; keep on device for subsequent renders."""
        import numba.cuda as cuda
        
        n = len(cloud.positions)
        if n > self.max_splats:
            raise ValueError(f"Too many splats: {n} > {self.max_splats}")
        
        # Allocate device memory on first upload
        if self.d_positions is None:
            self.d_positions = cuda.device_array(self.max_splats, dtype=np.float32)
            self.d_colors = cuda.device_array(self.max_splats, dtype=np.float32)
            self.d_opacities = cuda.device_array(self.max_splats, dtype=np.float32)
            self.d_scales = cuda.device_array(self.max_splats, dtype=np.float32)
            self.d_rotations = cuda.device_array(self.max_splats, dtype=np.float32)
            self.d_covariances = cuda.device_array(
                (self.max_splats, 3, 3), dtype=np.float32)
        
        # Copy data to device (only first time or when changed)
        self.d_positions[:n] = cloud.positions.astype(np.float32)
        self.d_colors[:n] = cloud.colors.astype(np.float32)
        self.d_opacities[:n] = cloud.opacities.astype(np.float32)
        self.d_scales[:n] = cloud.scales.astype(np.float32)
        self.d_rotations[:n] = cloud.rotations.astype(np.float32)
        self.d_covariances[:n] = cloud.covariances_3x3.astype(np.float32)
        self.current_count = n
    
    def get_view(self) -> Tuple[cuda.DevicePointer, ...]:
        """Return device pointers for rasterizer."""
        if self.d_positions is None:
            raise RuntimeError("SplatPool not uploaded yet")
        
        return (self.d_positions, self.d_colors, self.d_opacities, 
                self.d_scales, self.d_rotations, self.d_covariances, 
                np.int32(self.current_count))


class Camera:
    """Simple camera representation for rendering."""
    
    def __init__(self, position: np.ndarray, target: np.ndarray, up: np.ndarray = None):
        self.position = np.array(position, dtype=np.float32)
        self.target = np.array(target, dtype=np.float32)
        self.up = np.array(up or [0.0, 1.0, 0.0], dtype=np.float32)
        
        # Derived view matrix (simplified)
        self.forward = self.target - self.position
        self.forward /= np.linalg.norm(self.forward) + 1e-8
        self.right = np.cross(self.forward, self.up)
        self.right /= np.linalg.norm(self.right) + 1e-8
        self.up = np.cross(self.right, self.forward)
        self.up /= np.linalg.norm(self.up) + 1e-8
    
    def project_point(self, point: np.ndarray) -> np.ndarray:
        """Project a world point to camera space."""
        # Simplified projection - in practice would use full view/projection matrices
        relative = point - self.position
        return np.array([
            np.dot(relative, self.right),
            np.dot(relative, self.up),
            np.dot(relative, self.forward)
        ], dtype=np.float32)
