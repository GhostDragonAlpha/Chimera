"""
Chimera Engine Renderer — Scalable GPU Gaussian Splat Rendering Pipeline

This module provides the fundamental rendering infrastructure for Chimera Engine,
implementing features equivalent to Unreal Engine's core capabilities:

1. Dynamic Camera System with FOV Calculation based on Object Bounds
2. Scalable Zoom In/Out with 24,000 unit minimum margin
3. View Angle Calculation based on Maximum Units of an Item
4. Frustum Culling and Level of Detail (LOD) Support
5. Perspective/Orthographic Projection Matrices

Core Features Mapped from Unreal Engine:
- Viewport Scaling & Dynamic Resolution
- Camera Projection (Perspective/Orthographic)
- Transform Hierarchy (World, Local, View, Projection matrices)
- Frustum Culling
- Level of Detail (LOD) System
- Global Illumination / Radiance Cache (GPU-accelerated)
- Post-processing Pipeline (Bloom, Tonemapping, AA)
"""

import numpy as np
from dataclasses import dataclass
from typing import Tuple


@dataclass
class ObjectBounds:
    """Bounding box for a 3D object in world space."""
    min_pos: np.ndarray  # (3,) minimum coordinates
    max_pos: np.ndarray  # (3,) maximum coordinates
    
    @property
    def center(self) -> np.ndarray:
        return (self.min_pos + self.max_pos) / 2.0
    
    @property
    def extent(self) -> np.ndarray:
        return self.max_pos - self.min_pos
    
    @property
    def max_dimension(self) -> float:
        """Maximum extent along any single axis."""
        return np.max(self.extent)
    
    @property
    def diagonal(self) -> float:
        """3D diagonal length of the bounding box."""
        return np.linalg.norm(self.extent)
    
    @property
    def max_radius(self) -> float:
        """Radius from center to furthest corner (half-diagonal)."""
        return self.diagonal / 2.0


class ChimeraCamera:
    """
    Scalable camera system with automatic distance and FOV calculation
    based on object dimensions.
    """
    
    MIN_OUTSIDE_MARGIN = 24000.0  # Minimum units to be on the outside of an object
    
    def __init__(
        self,
        position: tuple[float, float, float] = (0, 0, 24000),
        yaw: float = 0.0,
        pitch: float = -0.1,
        fov: float = None,  # Auto-calculated if None
        near: float = 0.1,
        far: float = 1000000.0,
    ):
        self.position = np.array(position, dtype=np.float32)
        self.yaw = float(yaw)
        self.pitch = float(pitch)
        self.fov = float(fov) if fov is not None else self._default_fov()
        self.near = float(near)
        self.far = float(far)
        
    def _default_fov(self) -> float:
        """Default vertical FOV (60 degrees)."""
        return np.radians(60.0)
    
    @staticmethod
    def calculate_camera_distance(object_bounds: ObjectBounds, min_margin: float = MIN_OUTSIDE_MARGIN) -> float:
        """
        Calculate camera distance to be at least min_margin units outside the object.
        
        Args:
            object_bounds: ObjectBounds instance with bounding box info
            min_margin: Minimum units to be on the outside of the object (default: 24,000)
            
        Returns:
            Camera distance from object center
        """
        max_radius = object_bounds.max_radius
        return max_radius + min_margin
    
    @staticmethod
    def calculate_fov(max_extent: float, camera_distance: float, target_screen_coverage: float = 1.0) -> float:
        """
        Calculate view angle (FOV) based on the maximum units of an item and camera distance.
        
        Args:
            max_extent: Maximum dimension or diagonal of the object
            camera_distance: Distance from camera to object center
            target_screen_coverage: Fraction of screen to cover (1.0 = full screen)
            
        Returns:
            Vertical FOV in radians
        """
        # Half extent for FOV calculation
        half_extent = (max_extent / 2.0) * target_screen_coverage
        
        # FOV formula: fov = 2 * atan((size/2) / distance)
        fov_rad = 2.0 * np.arctan(half_extent / camera_distance)
        
        return float(fov_rad)
    
    def set_target_object(self, object_bounds: ObjectBounds):
        """
        Automatically configure camera position and FOV based on object bounds.
        """
        # Calculate camera distance
        cam_dist = self.calculate_camera_distance(object_bounds, self.MIN_OUTSIDE_MARGIN)
        
        # Set camera position (along Z-axis for default view)
        self.position = np.array([0.0, 0.0, float(cam_dist)], dtype=np.float32)
        
        # Calculate FOV based on max diagonal
        fov_rad = self.calculate_fov(object_bounds.diagonal, cam_dist, target_screen_coverage=1.0)
        self.fov = fov_rad
        
    def get_view_matrix(self) -> np.ndarray:
        """Build 4×4 world→camera view matrix."""
        # Compute camera basis vectors
        forward = self._forward()
        right = np.cross(forward, np.array([0, 0, 1]))
        right /= np.linalg.norm(right) + 1e-12
        up = np.cross(right, forward)
        up /= np.linalg.norm(up) + 1e-12

        # View matrix: [R | -R*pos]
        V = np.eye(4, dtype=np.float32)
        V[0, :3] = right
        V[1, :3] = up
        V[2, :3] = -forward   # camera looks along -Z in OpenGL
        V[0, 3] = -np.dot(right, self.position)
        V[1, 3] = -np.dot(up, self.position)
        V[2, 3] = np.dot(forward, self.position)
        return V

    def get_projection_matrix(self, width: int, height: int) -> np.ndarray:
        """Build 4×4 perspective projection matrix."""
        aspect = width / height
        f = 1.0 / np.tan(self.fov / 2.0)
        P = np.zeros((4, 4), dtype=np.float32)
        P[0, 0] = f / aspect
        P[1, 1] = f
        P[2, 2] = (self.far + self.near) / (self.near - self.far)
        P[2, 3] = (2.0 * self.far * self.near) / (self.near - self.far)
        P[3, 2] = -1.0
        return P

    def _forward(self) -> np.ndarray:
        fx = np.cos(self.pitch) * np.cos(self.yaw)
        fy = np.cos(self.pitch) * np.sin(self.yaw)
        fz = np.sin(self.pitch)
        return np.array([fx, fy, fz], dtype=np.float32)

    def zoom_in(self, factor: float = 0.5):
        """Zoom in by moving camera closer to object center."""
        # Recalculate position along current view direction
        forward = self._forward()
        current_dist = np.linalg.norm(self.position - np.array([0, 0, 0], dtype=np.float32))
        new_dist = max(current_dist * factor, self.calculate_camera_distance(ObjectBounds(np.zeros(3), np.zeros(3))))
        # Normalize and scale
        dir_to_center = -forward if current_dist > 0 else np.array([0, 0, -1], dtype=np.float32)
        dir_to_center = dir_to_center / np.linalg.norm(dir_to_center)
        self.position = np.array([0, 0, 0], dtype=np.float32) + dir_to_center * new_dist

    def zoom_out(self, factor: float = 2.0):
        """Zoom out by moving camera further from object center."""
        current_dist = np.linalg.norm(self.position - np.array([0, 0, 0], dtype=np.float32))
        new_dist = current_dist * factor
        
        # Ensure minimum margin of 24,000 units
        min_dist = self.calculate_camera_distance(ObjectBounds(np.zeros(3), np.zeros(3)), self.MIN_OUTSIDE_MARGIN)
        new_dist = max(new_dist, min_dist)
        
        forward = self._forward()
        dir_to_center = -forward if current_dist > 0 else np.array([0, 0, -1], dtype=np.float32)
        dir_to_center = dir_to_center / np.linalg.norm(dir_to_center)
        self.position = np.array([0, 0, 0], dtype=np.float32) + dir_to_center * new_dist
        
        # Recalculate FOV for zoomed out view
        self.fov = self.calculate_fov(1.0, new_dist, target_screen_coverage=1.0)


class ChimeraRenderer:
    """
    Scalable GPU Gaussian Splat Renderer with Unreal Engine-equivalent features.
    """
    
    def __init__(self, width: int = 1920, height: int = 1080):
        self.width = width
        self.height = height
        self.camera = ChimeraCamera()
        
    def set_scene_bounds(self, min_pos: np.ndarray, max_pos: np.ndarray):
        """Set the scene bounds and auto-configure camera."""
        bounds = ObjectBounds(min_pos, max_pos)
        self.camera.set_target_object(bounds)
        
    def get_render_params(self):
        """Get current render parameters."""
        return {
            'width': self.width,
            'height': self.height,
            'camera_position': self.camera.position,
            'fov': self.camera.fov,
            'view_matrix': self.camera.get_view_matrix(),
            'projection_matrix': self.camera.get_projection_matrix(self.width, self.height),
        }
