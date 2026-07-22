"""
Determinism gate for Chimera Engine rendering pipeline.

Ensures that same input produces byte-identical output across runs.
This is critical for reproducibility and debugging.
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


def check_determinism(render_func: Callable[[int], np.ndarray],
                      seed: int = 42,
                      comparison_threshold: float = 0.0) -> GateResult:
    """
    Check that rendering is deterministic - same seed produces identical output.
    
    Parameters
    ----------
    render_func : Callable[[int], np.ndarray]
        Function that takes a seed and returns an image (height, width, 3) uint8
    seed : int
        Random seed to use for testing
    comparison_threshold : float
        Maximum allowed difference per pixel (0.0 for byte-identical)
        
    Returns
    -------
    GateResult
        Pass/fail result with metrics and message
    """
    
    # Run twice with same seed
    np.random.seed(seed)
    result1 = render_func(seed)
    
    np.random.seed(seed)
    result2 = render_func(seed)
    
    # Compare results
    diff = np.abs(result1.astype(int) - result2.astype(int))
    max_diff = float(np.max(diff))
    mean_diff = float(np.mean(diff))
    pixels_different = int(np.sum(diff > comparison_threshold))
    total_pixels = result1.size
    
    passed = max_diff <= comparison_threshold
    
    # Build message
    if passed:
        message = f"Byte-identical output across runs (max diff: {max_diff:.2f}). " \
                  f"'Same seed, same world, forever' assertion satisfied."
    else:
        message = f"Non-deterministic output detected. Max difference: {max_diff:.2f}, " \
                  f"Mean difference: {mean_diff:.4f}, Pixels different: {pixels_different}/{total_pixels}"
    
    return GateResult(
        name="determinism",
        passed=passed,
        metrics={
            "seed": seed,
            "max_difference": max_diff,
            "mean_difference": mean_diff,
            "pixels_different": pixels_different,
            "total_pixels": total_pixels,
            "threshold": comparison_threshold,
        },
        message=message
    )


def check_gpu_determinism(render_func: Callable[[int], np.ndarray],
                          seed: int = 42) -> GateResult:
    """
    Check determinism specifically for GPU rendering.
    
    This tests that CUDA operations produce consistent results across runs.
    Note: Some GPU operations may be non-deterministic by design (e.g., atomic adds).
    """
    
    return check_determinism(render_func, seed, comparison_threshold=0.0)


if __name__ == "__main__":
    # Simple test - would need actual render function in context
    print("Determinism gate module loaded successfully.")
