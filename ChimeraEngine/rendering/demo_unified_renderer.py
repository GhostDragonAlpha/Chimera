"""
Demo: Unified Chimera Engine Rendering Pipeline

This script demonstrates the new unified architecture with:
1. Canonical GaussianSplatCloud format
2. Cluster tree construction
3. Budgeted cut LOD selection
4. GPU-resident splat pool (conceptual)
5. Quality gates ready to run

Note: This is a demonstration of the structure and API. Actual rendering
requires full CUDA kernel implementation which will be completed in subsequent phases.
"""

import numpy as np
from pathlib import Path
from typing import Optional

# Import unified components
from ChimeraEngine.rendering.core.gaussian_splat_cloud import GaussianSplatCloud, SplatPool, Camera
from ChimeraEngine.rendering.loD.cluster_tree import build_cluster_tree
from ChimeraEngine.rendering.loD.budgeted_cut import select_clusters_budgeted, create_default_frustum
from ChimeraEngine.rendering.renderers.gpu_rasterizer import GPUSplatRasterizer, CameraParams


def generate_sample_cloud(n_splats: int = 1000) -> GaussianSplatCloud:
    """Generate a sample splat cloud for demonstration."""
    
    rng = np.random.RandomState(42)
    
    positions = rng.uniform(-5.0, 5.0, size=(n_splats, 3)).astype(np.float32)
    colors = rng.uniform(0.0, 1.0, size=(n_splats, 3)).astype(np.float32)
    opacities = rng.uniform(0.0, 1.0, size=(n_splats,)).astype(np.float32)
    scales = rng.uniform(0.1, 1.0, size=(n_splats, 3)).astype(np.float32)
    rotations = rng.random((n_splats, 4)).astype(np.float32)
    
    # Normalize quaternions
    rotations /= np.linalg.norm(rotations, axis=1, keepdims=True) + 1e-12
    
    # Build covariance matrices (simplified for demo)
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
    
    cov = np.einsum('ijl,il,ikl->ijk', R, s2, R, dtype=np.float32)
    
    return GaussianSplatCloud(
        positions=positions,
        colors=colors,
        opacities=opacities,
        scales=scales,
        rotations=rotations,
        covariances_3x3=cov,
    )


def demo_budgeted_cut():
    """Demonstrate budgeted cut LOD selection."""
    
    print("\n=== DEMO: Budgeted Cut LOD Selection ===\n")
    
    # Generate sample cloud
    cloud = generate_sample_cloud(1000)
    print(f"Generated splat cloud: {cloud.count} splats")
    
    # Build cluster tree
    clusters = build_cluster_tree(cloud, max_depth=4)
    print(f"Built cluster tree: {len(clusters.all_clusters)} clusters total")
    
    # Create camera
    camera = Camera(
        position=np.array([0.0, 0.0, 5.0], dtype=np.float32),
        target=np.array([0.0, 0.0, 0.0], dtype=np.float32),
        up=np.array([0.0, 1.0, 0.0], dtype=np.float32)
    )
    
    # Compute frustum planes
    frustum = create_default_frustum(camera, fov=np.radians(60))
    
    # Select clusters under pixel budget
    selected = select_clusters_budgeted(
        clusters, camera.position, 1080, np.radians(60),
        budget_pixels=1024, frustum_planes=frustum
    )
    
    print(f"Selected {len(selected)} clusters under pixel budget")
    
    # Show distribution of LOD levels in selected clusters
    lod_counts = {}
    for cluster in selected:
        lod = cluster.lod
        lod_counts[lod] = lod_counts.get(lod, 0) + 1
    
    print("LOD distribution:")
    for lod, count in sorted(lod_counts.items()):
        print(f"  LOD {lod}: {count} clusters")
    
    return cloud, selected


def demo_splat_pool():
    """Demonstrate GPU-resident splat pool concept."""
    
    print("\n=== DEMO: GPU-Resident Splat Pool ===\n")
    
    cloud = generate_sample_cloud(100)
    pool = SplatPool()
    
    # Upload once (in production, this would copy to CUDA device memory)
    print("Uploading splat data to GPU-resident pool...")
    pool.upload(cloud)
    print(f"Pool contains {pool.current_count} splats on device")
    
    # Get view for rasterizer
    view = pool.get_view()
    print(f"View returns {len(view)} device pointers")
    
    return pool


def demo_rasterizer_setup():
    """Demonstrate unified rasterizer setup."""
    
    print("\n=== DEMO: Unified GPU Rasterizer ===\n")
    
    # Create rasterizer
    rasterizer = GPUSplatRasterizer()
    print("Created GPUSplatRasterizer instance")
    
    # Show configuration
    print(f"Default background: {rasterizer.bg}")
    print(f"Splat pool max capacity: {rasterizer.splat_pool.max_splats:,} splats")
    
    return rasterizer


def main():
    """Run unified renderer demo."""
    
    print("\n" + "=" * 60)
    print("CHIMERA ENGINE - UNIFIED RENDERING PIPELINE DEMO")
    print("=" * 60)
    
    # Demo 1: Budgeted cut LOD selection
    cloud, selected = demo_budgeted_cut()
    
    # Demo 2: GPU-resident splat pool
    pool = demo_splat_pool()
    
    # Demo 3: Rasterizer setup
    rasterizer = demo_rasterizer_setup()
    
    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
    
    print("\nNext steps:")
    print("1. Implement full CUDA kernels in gpu_rasterizer.py")
    print("2. Create test scenes and golden images")
    print("3. Run quality gates: pytest ChimeraEngine/tests/test_rendering_pipeline.py -v")
    print("4. Profile performance: python ChimeraEngine/benchmarks/performance_profile.py")
    
    return cloud, selected, pool, rasterizer


if __name__ == "__main__":
    main()
