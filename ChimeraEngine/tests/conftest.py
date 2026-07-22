"""
Pytest configuration and fixtures for Chimera Engine rendering tests.
"""

import pytest
import numpy as np
from pathlib import Path
from typing import Optional

from ChimeraEngine.core.gaussian_splat_cloud import GaussianSplatCloud
from ChimeraEngine.loD.cluster_tree import build_cluster_tree


@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    """Path to test data directory."""
    return Path(__file__).parent / "data"


@pytest.fixture(scope="session")
def golden_dir() -> Path:
    """Path to golden image reference directory."""
    return Path(__file__).parent / "golden"


@pytest.fixture
def sample_cloud() -> GaussianSplatCloud:
    """Create a sample splat cloud for testing."""
    
    n = 1000
    
    # Generate random but deterministic data
    rng = np.random.RandomState(42)
    
    positions = rng.uniform(-5.0, 5.0, size=(n, 3)).astype(np.float32)
    colors = rng.uniform(0.0, 1.0, size=(n, 3)).astype(np.float32)
    opacities = rng.uniform(0.0, 1.0, size=(n,)).astype(np.float32)
    scales = rng.uniform(0.1, 1.0, size=(n, 3)).astype(np.float32)
    rotations = rng.random((n, 4)).astype(np.float32)
    
    # Normalize quaternions
    rotations /= np.linalg.norm(rotations, axis=1, keepdims=True) + 1e-12
    
    # Build covariance matrices (simplified)
    covariances_3x3 = _build_sample_covariances(scales, rotations)
    
    return GaussianSplatCloud(
        positions=positions,
        colors=colors,
        opacities=opacities,
        scales=scales,
        rotations=rotations,
        covariances_3x3=covariances_3x3,
    )


@pytest.fixture
def sample_cluster_tree(sample_cloud) -> 'ClusterTree':
    """Build a cluster tree from the sample cloud."""
    
    return build_cluster_tree(sample_cloud, max_depth=4)


def _build_sample_covariances(scales: np.ndarray, rotations: np.ndarray) -> np.ndarray:
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


@pytest.fixture
def camera() -> 'Camera':
    """Create a sample camera for testing."""
    
    from ChimeraEngine.core.gaussian_splat_cloud import Camera
    
    position = np.array([0.0, 0.0, 5.0], dtype=np.float32)
    target = np.array([0.0, 0.0, 0.0], dtype=np.float32)
    up = np.array([0.0, 1.0, 0.0], dtype=np.float32)
    
    return Camera(position, target, up)


def pytest_configure(config):
    """Configure pytest with custom markers."""
    
    config.addinivalue_line(
        "markers", "performance: performance tests (may be slow)"
    )
    config.addinivalue_line(
        "markers", "determinism: determinism tests"
    )
    config.addinivalue_line(
        "markers", "golden: golden image comparison tests"
    )
    config.addinivalue_line(
        "markers", "lod: LOD conservation tests"
    )
