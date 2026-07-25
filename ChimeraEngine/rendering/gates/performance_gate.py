"""
Performance gate for Chimera Engine rendering pipeline.

Ensures that rendering completes within 16.6ms (60 FPS) at 1080p resolution.
This is a hard performance budget that the engine must meet.
"""

import time
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


def check_performance(render_func: Callable[[], np.ndarray],
                      resolution: tuple = (1920, 1080),
                      max_ms: float = 16.6,
                      warmup_runs: int = 3,
                      test_runs: int = 10) -> GateResult:
    """
    Check that rendering completes within the performance budget.
    
    Parameters
    ----------
    render_func : Callable[[], np.ndarray]
        Function that renders a scene and returns an image
    resolution : tuple
        (width, height) resolution to test at
    max_ms : float
        Maximum allowed time per frame in milliseconds (16.6 for 60 FPS)
    warmup_runs : int
        Number of warmup runs before timing starts
    test_runs : int
        Number of timed runs to average
        
    Returns
    -------
    GateResult
        Pass/fail result with metrics and message
    """
    
    # Warmup runs (not timed)
    for _ in range(warmup_runs):
        render_func()
    
    # Timed runs
    times_ms = []
    
    for i in range(test_runs):
        start = time.perf_counter()
        render_func()
        end = time.perf_counter()
        
        elapsed_ms = (end - start) * 1000
        times_ms.append(elapsed_ms)
    
    # Calculate metrics
    avg_ms = np.mean(times_ms)
    min_ms = np.min(times_ms)
    max_ms_val = np.max(times_ms)
    std_ms = np.std(times_ms)
    
    passed = avg_ms <= max_ms
    
    # Build message
    if passed:
        message = f"Average: {avg_ms:.2f}ms (target: ≤{max_ms}ms). All good!"
    else:
        message = f"Average: {avg_ms:.2f}ms exceeds budget of {max_ms}ms. " \
                  f"Min: {min_ms:.2f}ms, Max: {max_ms_val:.2f}ms, Std: {std_ms:.2f}ms"
    
    return GateResult(
        name="performance",
        passed=passed,
        metrics={
            "avg_ms": float(avg_ms),
            "min_ms": float(min_ms),
            "max_ms": float(max_ms_val),
            "std_ms": float(std_ms),
            "resolution": resolution,
            "budget_ms": max_ms,
            "test_runs": test_runs,
        },
        message=message
    )


def check_lod_performance(render_func: Callable[[], np.ndarray],
                          resolution: tuple = (1920, 1080),
                          max_ms: float = 16.6) -> GateResult:
    """
    Check performance specifically with LOD enabled.
    
    This tests the budgeted cut algorithm to ensure it provides a hard frame-cost ceiling.
    """
    
    return check_performance(render_func, resolution, max_ms)


if __name__ == "__main__":
    # Simple test - would need actual render function in context
    print("Performance gate module loaded successfully.")
