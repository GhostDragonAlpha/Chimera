"""
First-person camera with Gaussian splat projection math.

Implements the 3DGS paper's projection pipeline:
  1. World → Camera transform (view matrix)
  2. Camera → Screen projection (perspective + Jacobian)
  3. 3D covariance → 2D screen-space covariance

The camera is a first-person controller: yaw/pitch angles,
position vector, and a standard perspective projection matrix.
"""

import numpy as np
from dataclasses import dataclass


@dataclass
class CameraParams:
    """Immutable camera state for a single frame."""
    position: np.ndarray       # (3,) world position
    yaw: float                 # radians, horizontal rotation
    pitch: float               # radians, vertical rotation (-π/2 to π/2)
    fov: float                 # vertical FOV in radians
    near: float                # near clipping plane
    far: float                 # far clipping plane
    width: int                 # viewport width in pixels
    height: int                # viewport height in pixels

    @property
    def aspect(self) -> float:
        return self.width / self.height


class FirstPersonCamera:
    """
    First-person camera that tracks yaw/pitch and builds view/projection
    matrices. Call .tick() each frame with mouse/input deltas, then use
    .params() for the current CameraParams.

    Usage:
        cam = FirstPersonCamera(position=(0,0,200), yaw=0, pitch=-0.2)
        cam.tick(dyaw=0.01, dpitch=0.0, forward=1.0)
        params = cam.params(width=800, height=600)
        # Pass params to rasterizer
    """

    def __init__(
        self,
        position: tuple[float, float, float] = (0, 0, 200),
        yaw: float = 0.0,           # radians
        pitch: float = 0.0,         # radians
        fov: float = np.radians(60),
        near: float = 0.1,
        far: float = 100000.0,
        sensitivity: float = 0.003,
        move_speed: float = 500.0,
    ):
        self.position = np.array(position, dtype=np.float32)
        self.yaw = float(yaw)
        self.pitch = float(pitch)
        self.fov = float(fov)
        self.near = float(near)
        self.far = float(far)
        self.sensitivity = sensitivity
        self.move_speed = move_speed

    def tick(
        self,
        dyaw: float = 0.0,
        dpitch: float = 0.0,
        forward: float = 0.0,
        right: float = 0.0,
        up: float = 0.0,
        dt: float = 1/60,
    ):
        """Update camera from input deltas. dyaw/dpitch are raw mouse deltas."""
        self.yaw += dyaw * self.sensitivity
        self.pitch = np.clip(
            self.pitch + dpitch * self.sensitivity,
            -np.pi / 2 + 0.01,
            np.pi / 2 - 0.01,
        )

        # Forward vector in horizontal plane
        fx = np.cos(self.pitch) * np.cos(self.yaw)
        fy = np.cos(self.pitch) * np.sin(self.yaw)
        fz = np.sin(self.pitch)
        f = np.array([fx, fy, fz], dtype=np.float32)

        # Right vector
        r = np.array([-np.sin(self.yaw), np.cos(self.yaw), 0.0], dtype=np.float32)

        # Up vector
        u = np.array([0.0, 0.0, 1.0], dtype=np.float32)

        self.position += (f * forward + r * right + u * up) * self.move_speed * dt

    def params(self, width: int, height: int) -> CameraParams:
        """Build the camera parameters for the current frame."""
        return CameraParams(
            position=self.position.copy(),
            yaw=self.yaw,
            pitch=self.pitch,
            fov=self.fov,
            near=self.near,
            far=self.far,
            width=width,
            height=height,
        )

    # ── View matrix ────────────────────────────────────────────────

    def view_matrix(self) -> np.ndarray:
        """Build 4×4 world→camera view matrix (column-major for OpenGL convention)."""
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

    def projection_matrix(self, width: int, height: int) -> np.ndarray:
        """Build 4×4 perspective projection matrix (OpenGL convention)."""
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

    # ── Splat projection helpers ───────────────────────────────────

    def project_points(
        self, points_3d: np.ndarray, width: int, height: int
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Project 3D world-space points to screen space.
        Returns: (screen_xy, depth, valid_mask)
          screen_xy: (N, 2) pixels (origin at top-left)
          depth: (N,) camera-space Z (positive = in front)
          valid_mask: (N,) bool — True if point is in front and within frustum
        """
        V = self.view_matrix()
        P = self.projection_matrix(width, height)

        # World → homogeneous clip space
        ones = np.ones((len(points_3d), 1), dtype=np.float32)
        pts_h = np.hstack([points_3d, ones])  # (N, 4)

        # View space
        pts_view = pts_h @ V.T  # (N, 4) — camera-space
        # Clip space
        pts_clip = pts_view @ P.T  # (N, 4)

        w = pts_clip[:, 3]
        valid = (w > 0) & (pts_view[:, 2] < 0)  # in front of camera

        # NDC
        ndc = pts_clip[:, :3] / w[:, np.newaxis]

        # Screen coordinates (pixel space, origin top-left)
        screen_x = (ndc[:, 0] * 0.5 + 0.5) * width
        screen_y = (1.0 - (ndc[:, 1] * 0.5 + 0.5)) * height  # flip Y

        depth = -pts_view[:, 2]  # positive depth

        screen_xy = np.stack([screen_x, screen_y], axis=1).astype(np.float32)
        return screen_xy, depth.astype(np.float32), valid

    def project_covariance(
        self,
        positions_3d: np.ndarray,   # (N, 3) world positions
        covariances_3d: np.ndarray, # (N, 3, 3) world-space covariances
        width: int,
        height: int,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Project 3D Gaussian covariances to 2D screen-space covariances.
        Implements the 3DGS paper's EWA splatting projection:

          Σ_2D = J * W * Σ_3D * Wᵀ * Jᵀ

        where W is the view matrix (rotation) and J is the projective Jacobian.

        Returns:
          screen_xy: (N, 2) pixel positions
          cov_2d:    (N, 2, 2) screen-space 2×2 covariances
          depth:     (N,) camera-space depth
          valid:     (N,) bool mask
        """
        V = self.view_matrix()
        W = V[:3, :3].astype(np.float32)  # 3×3 rotation part

        # Project positions
        screen_xy, depth, valid = self.project_points(positions_3d, width, height)
        if not valid.any():
            return screen_xy, np.zeros((len(positions_3d), 2, 2), dtype=np.float32), depth, valid

        n = len(positions_3d)

        # Camera-space positions (for Jacobian)
        ones = np.ones((n, 1), dtype=np.float32)
        pts_h = np.hstack([positions_3d, ones])
        pts_view = (pts_h @ V.T)[:, :3]  # (N, 3) camera-space xyz

        cx, cy, cz = pts_view[:, 0], pts_view[:, 1], pts_view[:, 2]

        # Projective Jacobian for each point
        # J = [[fx/z,   0,   -fx*x/z²],
        #      [  0,  fy/z,  -fy*y/z²]]
        focal_y = height / (2.0 * np.tan(self.fov / 2.0))
        focal_x = focal_y  # square pixels, aspect handled by viewport

        fx = focal_x
        fy = focal_y

        # Build Jacobian (N, 2, 3)
        J = np.zeros((n, 2, 3), dtype=np.float32)
        J[:, 0, 0] = fx / cz
        J[:, 0, 2] = -fx * cx / (cz * cz)
        J[:, 1, 1] = fy / cz
        J[:, 1, 2] = -fy * cy / (cz * cz)

        # Σ_camera = W * Σ_world * Wᵀ
        # Σ_cam[i] = W @ cov_3d[i] @ W.T
        cov_cam = W @ covariances_3d @ W.T  # broadcast: W @ (N,3,3) @ W.T → (N,3,3)

        # Σ_2D = J @ Σ_cam @ Jᵀ  (take upper-left 2×2 after transformation)
        # This is: Σ_2D[i] = J[i] @ Σ_cam[i] @ J[i].T
        cov_2d = J @ cov_cam @ J.transpose(0, 2, 1)  # (N, 2, 3) @ (N, 3, 3) @ (N, 3, 2) → (N, 2, 2)

        # Add a small diagonal to prevent degenerate covariances
        # Regularize: add σ²*I to ensure positive definiteness
        cov_2d[:, 0, 0] += 1.5
        cov_2d[:, 1, 1] += 1.5
        # Ensure positive diagonal (paranoid check)
        cov_2d[:, 0, 0] = np.maximum(cov_2d[:, 0, 0], 0.5)
        cov_2d[:, 1, 1] = np.maximum(cov_2d[:, 1, 1], 0.5)

        return screen_xy.astype(np.float32), cov_2d.astype(np.float32), depth.astype(np.float32), valid
