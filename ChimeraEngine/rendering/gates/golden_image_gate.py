"""
Golden image gate for Chimera Engine rendering pipeline.

Compares rendered images to a golden reference to catch visual regressions.
Uses SSIM (Structural Similarity Index) for perceptual comparison.
"""

import numpy as np
from dataclasses import dataclass
from typing import Callable, Optional
from pathlib import Path


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


def calculate_ssim(img1: np.ndarray, img2: np.ndarray) -> float:
    """
    Calculate Structural Similarity Index between two images.
    
    Parameters
    ----------
    img1 : np.ndarray
        First image (height, width, 3) uint8 or float32
    img2 : np.ndarray
        Second image (height, width, 3) uint8 or float32
        
    Returns
    -------
    float
        SSIM value between 0 and 1 (1 = identical)
    """
    
    # Convert to float32 for calculation
    img1 = img1.astype(np.float64)
    img2 = img2.astype(np.float64)
    
    # Constants for SSIM
    K1, K2 = 0.01, 0.03
    L = 255.0  # Dynamic range of images
    
    # Gaussian filter parameters
    sigma = 1.5
    window_size = int(6 * sigma + 1)
    
    # Create Gaussian kernel
    def gaussian_kernel(size, sigma):
        ax = np.linspace(-(size // 2), size // 2, size)
        xx, yy = np.meshgrid(ax, ax)
        kernel = np.exp(-0.5 * ((xx ** 2 + yy ** 2) / (sigma ** 2)))
        return kernel / np.sum(kernel)
    
    kernel = gaussian_kernel(window_size, sigma)
    
    def ssim_per_channel(c1, c2):
        # Apply Gaussian filter
        mu1 = np.convolve(c1, kernel, mode='valid')
        mu2 = np.convolve(c2, kernel, mode='valid')
        
        mu1_sq = mu1 ** 2
        mu2_sq = mu2 ** 2
        mu1_mu2 = mu1 * mu2
        
        sigma1_sq = np.convolve(c1**2, kernel, mode='valid') - mu1_sq
        sigma2_sq = np.convolve(c2**2, kernel, mode='valid') - mu2_sq
        sigma12 = np.convolve(c1*c2, kernel, mode='valid') - mu1_mu2
        
        # SSIM formula
        c1 = (K1 * L) ** 2
        c2 = (K2 * L) ** 2
        
        ssim = ((2*mu1_mu2 + c1) * (2*sigma12 + c2)) / \
               ((mu1_sq + mu2_sq + c1) * (sigma1_sq + sigma2_sq + c2))
        
        return np.mean(ssim)
    
    # Calculate SSIM for each channel and average
    ssim_r = ssim_per_channel(img1[:, :, 0], img2[:, :, 0])
    ssim_g = ssim_per_channel(img1[:, :, 1], img2[:, :, 1])
    ssim_b = ssim_per_channel(img1[:, :, 2], img2[:, :, 2])
    
    return float((ssim_r + ssim_g + ssim_b) / 3.0)


def check_golden_image(render_func: Callable[[], np.ndarray],
                       golden_path: str,
                       threshold: float = 5.0,
                       allow_ssim: bool = True) -> GateResult:
    """
    Compare rendered image to a golden reference image.
    
    Parameters
    ----------
    render_func : Callable[[], np.ndarray]
        Function that renders a scene and returns an image (height, width, 3) uint8
    golden_path : str
        Path to the golden reference image (.png or .jpg)
    threshold : float
        Maximum allowed mean absolute difference per pixel (0-255 scale)
    allow_ssim : bool
        Also use SSIM comparison for perceptual similarity
        
    Returns
    -------
    GateResult
        Pass/fail result with metrics and message
    """
    
    # Render current image
    current = render_func()
    
    # Load golden image
    golden_path = Path(golden_path)
    if not golden_path.exists():
        return GateResult(
            name="golden_image",
            passed=False,
            metrics={},
            message=f"Golden image not found: {golden_path}"
        )
    
    # Load images (simplified - would use PIL/Pillow in production)
    import cv2
    
    golden = cv2.imread(str(golden_path))
    if golden is None:
        return GateResult(
            name="golden_image",
            passed=False,
            metrics={},
            message=f"Failed to load golden image: {golden_path}"
        )
    
    # Convert BGR to RGB if needed
    if len(golden.shape) == 3 and golden.shape[2] == 3:
        golden = cv2.cvtColor(golden, cv2.COLOR_BGR2RGB)
    
    # Ensure same dimensions
    if current.shape != golden.shape:
        return GateResult(
            name="golden_image",
            passed=False,
            metrics={},
            message=f"Dimension mismatch: current {current.shape} vs golden {golden.shape}"
        )
    
    # Calculate differences
    diff = np.abs(current.astype(int) - golden.astype(int))
    mean_diff = float(np.mean(diff))
    max_diff = float(np.max(diff))
    pixels_different = int(np.sum(diff > threshold))
    
    # Calculate SSIM if enabled
    ssim = None
    if allow_ssim:
        ssim = calculate_ssim(current, golden)
    
    passed = mean_diff <= threshold and (ssim is None or ssim >= 0.95)
    
    # Build message
    if passed:
        msg_parts = [f"Mean difference: {mean_diff:.2f} (threshold: ≤{threshold})"]
        if ssim is not None:
            msg_parts.append(f"SSIM: {ssim:.4f}")
        message = " | ".join(msg_parts) + " - Matches golden image."
    else:
        msg_parts = [f"Mean difference: {mean_diff:.2f} exceeds threshold of {threshold}",
                     f"Max difference: {max_diff:.2f}",
                     f"Different pixels: {pixels_different}"]
        if ssim is not None:
            msg_parts.append(f"SSIM: {ssim:.4f}")
        message = " | ".join(msg_parts) + " - Significant deviation from golden."
    
    return GateResult(
        name="golden_image",
        passed=passed,
        metrics={
            "mean_diff": mean_diff,
            "max_diff": max_diff,
            "pixels_different": pixels_different,
            "ssim": ssim if ssim is not None else None,
            "threshold": threshold,
        },
        message=message
    )


if __name__ == "__main__":
    # Simple test - would need actual render function and golden image in context
    print("Golden image gate module loaded successfully.")
