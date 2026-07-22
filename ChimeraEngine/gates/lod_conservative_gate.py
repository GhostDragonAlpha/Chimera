"""
LOD conservation gate for Chimera Engine rendering pipeline.

Ensures that LOD transitions preserve visual fidelity - the merged cut's
opacity-weighted mass should be within a few percent of the full set.
This is "LOD of meaning" as an assertion.
"""

import numpy as np
from dataclasses import dataclass
from typing import Callable, Optional


@dataclass
class GateResult:
    """Result from a quality gate."""
    
    name: str
    passed: bool
    metrics: dict
    message: str
    
    def __str__(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        return f"[{status}] {self.name}: {self.message}"


def check_lod_conservation(render_func_with_lod: Callable[[], np.ndarray],
                           render_func_full: Callable[[], np.ndarray],
                           threshold: float = 0.05) -> GateResult:
    """
    Check that LOD rendering preserves visual fidelity compared to full resolution.
    
    Parameters
    ----------
    render_func_with_lod : Callable[[], np.ndarray]
        Function that renders with cluster tree LOD enabled
    render_func_full : Callable[[], np.ndarray]
        Function that renders all splats (no LOD)
    threshold : float
        Maximum allowed difference in mean absolute error (0.05 = 5% difference)
        
    Returns
    -------
    GateResult
        Pass/fail result with metrics and message
    """
    
    # Render both versions
    lod_image = render_func_with_lod()
    full_image = render_func_full()
    
    # Ensure same dimensions
    if lod_image.shape != full_image.shape:
        return GateResult(
            name="lod_conservative",
            passed=False,
            metrics={},
            message=f"Dimension mismatch: LOD {lod_image.shape} vs full {full_image.shape}"
        )
    
    # Calculate difference
    diff = np.abs(lod_image.astype(int) - full_image.astype(int))
    mean_diff = float(np.mean(diff))
    max_diff = float(np.max(diff))
    
    # Normalize by 255 to get percentage difference
    normalized_diff = mean_diff / 255.0
    
    passed = normalized_diff <= threshold
    
    # Build message
    if passed:
        message = f"LOD preserves visual fidelity (MAE: {mean_diff:.1f}, " \
                  f"{normalized_diff*100:.2f}% difference). LOD of meaning conserved."
    else:
        message = f"LOD loses too much detail (MAE: {mean_diff:.1f}, " \
                  f"{normalized_diff*100:.2f}% difference exceeds threshold of {threshold*100:.2f}%)"
    
    return GateResult(
        name="lod_conservative",
        passed=passed,
        metrics={
            "mean_absolute_error": mean_diff,
            "max_difference": max_diff,
            "normalized_diff": normalized_diff,
            "threshold": threshold,
            "image_shape": lod_image.shape,
        },
        message=message
    )


def check_lod_mass_conservation(cloud: 'GaussianSplatCloud',
                                selected_clusters: list,
                                tolerance: float = 0.02) -> GateResult:
    """
    Check that the LOD cut preserves total opacity-weighted mass within tolerance.
    
    This is a more fundamental check - the merged clusters should represent
    approximately the same visual weight as the full splat cloud.
    
    Parameters
    ----------
    cloud : GaussianSplatCloud
        Full splat cloud
    selected_clusters : list
        Clusters selected by budgeted cut algorithm
    tolerance : float
        Maximum allowed difference in opacity-weighted mass (0.02 = 2%)
        
    Returns
    -------
    GateResult
        Pass/fail result with metrics and message
    """
    
    # Calculate total opacity of full cloud
    total_opacity = np.sum(cloud.opacities)
    total_mass = total_opacity * len(cloud.positions)
    
    # Calculate opacity-weighted mass of selected clusters
    selected_mass = 0.0
    for cluster in selected_clusters:
        cluster_opacities = cloud.opacities[cluster.splat_indices]
        cluster_mass = np.sum(cluster_opacities) * len(cluster.splat_indices)
        selected_mass += cluster_mass
    
    # Calculate difference
    if total_mass > 0:
        mass_diff = abs(selected_mass - total_mass) / total_mass
    else:
        mass_diff = 0.0
    
    passed = mass_diff <= tolerance
    
    # Build message
    if passed:
        message = f"LOD conserves opacity-weighted mass (difference: {mass_diff*100:.2f}%). " \
                  f"Selected {len(selected_clusters)} clusters from full cloud."
    else:
        message = f"LOD loses too much mass (difference: {mass_diff*100:.2f}% exceeds threshold of {tolerance*100:.2f}%)"
    
    return GateResult(
        name="lod_mass_conservation",
        passed=passed,
        metrics={
            "total_opacity": float(total_opacity),
            "selected_mass": float(selected_mass),
            "mass_difference": float(mass_diff),
            "tolerance": tolerance,
            "num_clusters": len(selected_clusters),
            "total_splats": len(cloud.positions),
        },
        message=message
    )


if __name__ == "__main__":
    # Simple test - would need actual cloud and cluster data in context
    print("LOD conservation gate module loaded successfully.")
