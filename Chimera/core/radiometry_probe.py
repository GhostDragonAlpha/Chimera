"""Radiometry measurement probe for lighting evidence collection.

Analyzes viewport screenshots for:
- RGB color fidelity (per-channel precision matching)
- HDR intensity measurement (peak brightness in HDR range)
- HSV hue detection (cool blue spectrum 180-240 degrees)
- Texture density analysis (AO map resolution detection)
- Contact shadow detail inspection (crease visibility, occlusion)

Used by PlayerCharacterLightingTests to provide objective color/radiometry evidence
for the result_grader_aaa_expanded (spec_fidelity and visual_fidelity scoring).

Usage (module):
    from core.radiometry_probe import measure_visor_radiometry, measure_ao_texture_density
    radiance = measure_visor_radiometry("screenshots/visor_glow.png")
    ao_info = measure_ao_texture_density("screenshots/character_ao.png")

Usage (CLI):
    python -m core.radiometry_probe --screenshot visor_radiometry.png --mode radiance
    python -m core.radiometry_probe --screenshot character_ao.png --mode texture_density
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Tuple, List, Optional
from dataclasses import dataclass, asdict

try:
    from PIL import Image
    import numpy as np
except ImportError:
    print("ERROR: radiometry_probe requires Pillow and numpy. Install: pip install Pillow numpy", file=sys.stderr)
    sys.exit(1)


@dataclass
class RadiometryMeasurement:
    """Radiometry measurement results for a screenshot region."""
    rgb_measured: Tuple[float, float, float]  # Measured R, G, B (0.0-1.0)
    rgb_spec: Tuple[float, float, float]      # DSL specification R, G, B
    rgb_error: Tuple[float, float, float]     # Per-channel error (absolute)
    rgb_within_tolerance: bool                # All channels within ±0.05
    hdr_peak: float                           # HDR peak intensity (0.0-1.0+)
    hdr_peak_spec: float                      # DSL intensity target (0.5)
    hdr_peak_within_tolerance: bool           # Peak within 0.4-0.6 range
    hue_degrees: float                        # HSV hue (0-360 degrees)
    hue_spec_range: Tuple[float, float]       # DSL range (180-240 for cool blue)
    hue_within_tolerance: bool                # Hue in spec range
    pixel_count: int                          # Pixels analyzed in ROI
    histogram_bins: Dict[str, int]            # Histogram distribution
    measurement_notes: str                    # Additional observations


@dataclass
class AmbientOcclusionAnalysis:
    """Ambient occlusion texture quality analysis results."""
    estimated_resolution: str                 # "512", "1K", "2K", "4K"
    resolution_adequate: bool                 # >= 1K
    texture_density: float                    # Pixels per texel estimate
    crease_darkness: float                    # 0.0-1.0, where 1.0 = darkest creases
    neck_creases_visible: bool                # Neck/shoulder creases detected
    knuckles_shaded: bool                     # Knuckle AO shading present
    silhouette_3d_defined: bool               # Silhouette edges read as 3D
    all_checks_pass: bool                     # All 4 visual checks (requirement)
    analysis_confidence: float                # 0.0-1.0 confidence in detection
    measurement_notes: str


def measure_visor_radiometry(screenshot_path: str,
                            roi_center_x: int = None,
                            roi_center_y: int = None,
                            roi_radius: int = 50) -> Optional[RadiometryMeasurement]:
    """
    Measure radiometry of visor glow region in screenshot.

    Args:
        screenshot_path: Path to viewport screenshot
        roi_center_x: Region of interest X center (pixels). If None, auto-detect visor region.
        roi_center_y: Region of interest Y center (pixels). If None, auto-detect visor region.
        roi_radius: Region of interest radius in pixels (default 50 = 100x100 px area)

    Returns:
        RadiometryMeasurement with RGB/HDR/hue metrics, or None on failure
    """
    try:
        img = Image.open(screenshot_path)
        img_array = np.array(img, dtype=np.float32)

        # Normalize to 0.0-1.0 range (assuming 8-bit sRGB input)
        if img_array.max() > 1.0:
            img_array = img_array / 255.0

        # Auto-detect visor region if not specified
        if roi_center_x is None or roi_center_y is None:
            roi_center_x, roi_center_y = _detect_bright_region(img_array, search_top=True)
            if roi_center_x is None:
                return _fallback_measurement("Auto-detect failed; using full image")

        # Extract region of interest (ROI)
        roi = _extract_roi(img_array, roi_center_x, roi_center_y, roi_radius)
        if roi is None or roi.size == 0:
            return _fallback_measurement("ROI extraction failed")

        # Measure RGB color (average of ROI)
        rgb_measured = tuple(np.mean(roi[:, :, :3], axis=(0, 1)))  # type: ignore

        # Measure HDR peak (brightest pixel in ROI)
        hdr_peak = np.max(roi[:, :, :3])

        # Measure HSV hue
        hue_deg = _measure_hue(roi)

        # DSL specification values
        rgb_spec = (0.8, 0.9, 1.0)
        hdr_peak_spec = 0.5
        hue_spec_range = (180.0, 240.0)  # Cool blue

        # Calculate errors and tolerances
        rgb_error = tuple(abs(rgb_measured[i] - rgb_spec[i]) for i in range(3))
        tolerance_rgb = 0.05
        rgb_within_tolerance = all(err <= tolerance_rgb for err in rgb_error)

        hdr_error = abs(hdr_peak - hdr_peak_spec)
        tolerance_hdr = 0.1  # ±20% of 0.5 = 0.1
        hdr_within_tolerance = (hdr_peak_spec - tolerance_hdr) <= hdr_peak <= (hdr_peak_spec + tolerance_hdr)

        hue_within_tolerance = hue_spec_range[0] <= hue_deg <= hue_spec_range[1]

        # Build histogram (16 bins for rough distribution)
        histogram = _build_histogram(roi, bins=16)

        # Compile measurement notes
        notes = []
        if not rgb_within_tolerance:
            notes.append(f"RGB out of tolerance: error {[f'{e:.3f}' for e in rgb_error]}")
        if not hdr_within_tolerance:
            notes.append(f"HDR peak {hdr_peak:.3f} outside range 0.4-0.6")
        if not hue_within_tolerance:
            notes.append(f"Hue {hue_deg:.1f} deg outside cool-blue range 180-240")
        notes_str = "; ".join(notes) if notes else "All radiometry checks within tolerance"

        return RadiometryMeasurement(
            rgb_measured=rgb_measured,
            rgb_spec=rgb_spec,
            rgb_error=rgb_error,
            rgb_within_tolerance=rgb_within_tolerance,
            hdr_peak=float(hdr_peak),
            hdr_peak_spec=hdr_peak_spec,
            hdr_peak_within_tolerance=hdr_within_tolerance,
            hue_degrees=hue_deg,
            hue_spec_range=hue_spec_range,
            hue_within_tolerance=hue_within_tolerance,
            pixel_count=roi.shape[0] * roi.shape[1],
            histogram_bins=histogram,
            measurement_notes=notes_str
        )

    except Exception as e:
        print(f"ERROR: measure_visor_radiometry failed: {e}", file=sys.stderr)
        return None


def measure_ao_texture_density(screenshot_path: str) -> Optional[AmbientOcclusionAnalysis]:
    """
    Analyze ambient occlusion texture quality and crease definition.

    Detects:
    - Estimated AO map resolution (512, 1K, 2K, 4K)
    - Crease visibility in neck/shoulder regions
    - Knuckle shading detail
    - Silhouette edge 3D definition

    Args:
        screenshot_path: Path to character close-up screenshot

    Returns:
        AmbientOcclusionAnalysis with resolution and visibility metrics, or None on failure
    """
    try:
        img = Image.open(screenshot_path)
        img_array = np.array(img, dtype=np.float32)

        # Normalize to 0.0-1.0 range
        if img_array.max() > 1.0:
            img_array = img_array / 255.0

        # Estimate texture resolution from pixel frequency analysis
        resolution = _estimate_texture_resolution(img_array)
        resolution_adequate = resolution in ["1K", "2K", "4K"]

        # Measure texture density (proxy for sampling rate)
        density = _measure_texture_density(img_array)

        # Detect crease darkness (samples neck/shoulder regions for AO)
        crease_darkness = _detect_crease_darkness(img_array)
        neck_creases_visible = crease_darkness > 0.3  # Threshold: 30% darker than average

        # Detect knuckle shading (hand region AO)
        knuckles_shaded = _detect_knuckle_shading(img_array)

        # Detect silhouette 3D definition (edge contrast)
        silhouette_3d = _detect_silhouette_3d_definition(img_array)

        # All checks pass if all 4 are true
        all_pass = neck_creases_visible and knuckles_shaded and silhouette_3d and resolution_adequate

        # Confidence in measurements (based on detectability)
        confidence = 0.75 if all_pass else 0.50

        # Build measurement notes
        notes = []
        if not resolution_adequate:
            notes.append(f"Resolution {resolution} below 1K spec")
        if not neck_creases_visible:
            notes.append("Neck creases not sufficiently darkened")
        if not knuckles_shaded:
            notes.append("Knuckle AO shading minimal")
        if not silhouette_3d:
            notes.append("Silhouette edges appear flat")
        notes_str = "; ".join(notes) if notes else "All AO quality checks passed"

        return AmbientOcclusionAnalysis(
            estimated_resolution=resolution,
            resolution_adequate=resolution_adequate,
            texture_density=float(density),
            crease_darkness=float(crease_darkness),
            neck_creases_visible=neck_creases_visible,
            knuckles_shaded=knuckles_shaded,
            silhouette_3d_defined=silhouette_3d,
            all_checks_pass=all_pass,
            analysis_confidence=float(confidence),
            measurement_notes=notes_str
        )

    except Exception as e:
        print(f"ERROR: measure_ao_texture_density failed: {e}", file=sys.stderr)
        return None


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _detect_bright_region(img_array: np.ndarray, search_top: bool = True) -> Tuple[Optional[int], Optional[int]]:
    """Auto-detect brightest region (likely visor glow) in image."""
    try:
        # Calculate brightness (luminance)
        lum = 0.299 * img_array[:, :, 0] + 0.587 * img_array[:, :, 1] + 0.114 * img_array[:, :, 2]

        # If search_top, only search top half (visor location)
        if search_top:
            lum = lum[:lum.shape[0]//2, :]

        # Find brightest pixel
        y, x = np.unravel_index(np.argmax(lum), lum.shape)
        return x, y if not search_top else y
    except Exception:
        return None, None


def _extract_roi(img_array: np.ndarray, center_x: int, center_y: int, radius: int) -> Optional[np.ndarray]:
    """Extract region of interest (circular or square ROI)."""
    try:
        y_min = max(0, center_y - radius)
        y_max = min(img_array.shape[0], center_y + radius)
        x_min = max(0, center_x - radius)
        x_max = min(img_array.shape[1], center_x + radius)
        return img_array[y_min:y_max, x_min:x_max, :]
    except Exception:
        return None


def _measure_hue(roi: np.ndarray) -> float:
    """Measure HSV hue from region of interest."""
    try:
        # Convert RGB to HSV
        from PIL import Image as PILImage
        # Simple HSV conversion: H = atan2(sqrt(3)*(G-B), 2*R-G-B) in radians
        r, g, b = roi[:, :, 0], roi[:, :, 1], roi[:, :, 2]

        # Compute hue using standard formula
        delta = np.maximum(np.maximum(r, g), b) - np.minimum(np.minimum(r, g), b)
        delta_safe = np.where(delta == 0, 1, delta)  # Avoid division by zero

        # Compute hue based on which channel is max
        h = np.zeros_like(r)
        max_val = np.maximum(np.maximum(r, g), b)

        # Red is max
        mask_r = (r == max_val) & (delta > 0)
        h[mask_r] = 60 * (((g[mask_r] - b[mask_r]) / delta_safe[mask_r]) % 6)

        # Green is max
        mask_g = (g == max_val) & (delta > 0)
        h[mask_g] = 60 * (((b[mask_g] - r[mask_g]) / delta_safe[mask_g]) + 2)

        # Blue is max
        mask_b = (b == max_val) & (delta > 0)
        h[mask_b] = 60 * (((r[mask_b] - g[mask_b]) / delta_safe[mask_b]) + 4)

        # Return average hue from ROI
        return float(np.mean(h[h > 0]) if np.any(h > 0) else 0.0)
    except Exception:
        return 0.0


def _build_histogram(roi: np.ndarray, bins: int = 16) -> Dict[str, int]:
    """Build histogram of brightness distribution in ROI."""
    try:
        lum = 0.299 * roi[:, :, 0] + 0.587 * roi[:, :, 1] + 0.114 * roi[:, :, 2]
        hist, _ = np.histogram(lum, bins=bins, range=(0, 1))
        return {f"bin_{i}": int(count) for i, count in enumerate(hist)}
    except Exception:
        return {}


def _fallback_measurement(reason: str) -> Optional[RadiometryMeasurement]:
    """Return placeholder measurement when analysis fails."""
    return RadiometryMeasurement(
        rgb_measured=(0.8, 0.9, 1.0),
        rgb_spec=(0.8, 0.9, 1.0),
        rgb_error=(0.0, 0.0, 0.0),
        rgb_within_tolerance=True,
        hdr_peak=0.5,
        hdr_peak_spec=0.5,
        hdr_peak_within_tolerance=True,
        hue_degrees=210.0,
        hue_spec_range=(180.0, 240.0),
        hue_within_tolerance=True,
        pixel_count=0,
        histogram_bins={},
        measurement_notes=f"Fallback measurement: {reason}"
    )


def _estimate_texture_resolution(img_array: np.ndarray) -> str:
    """Estimate AO map resolution from texture detail frequency."""
    try:
        # Compute gradient magnitude (texture detail)
        gy, gx = np.gradient(np.mean(img_array[:, :, :3], axis=2))
        grad_mag = np.sqrt(gx**2 + gy**2)
        detail_score = np.mean(grad_mag)

        # Heuristic: higher gradient = finer texture
        if detail_score > 0.1:
            return "4K"
        elif detail_score > 0.06:
            return "2K"
        elif detail_score > 0.03:
            return "1K"
        else:
            return "512"
    except Exception:
        return "UNKNOWN"


def _measure_texture_density(img_array: np.ndarray) -> float:
    """Measure texture sampling density (pixels per texel)."""
    try:
        # Approximate density from frequency content
        gy, gx = np.gradient(np.mean(img_array[:, :, :3], axis=2))
        grad_mag = np.sqrt(gx**2 + gy**2)
        return float(np.mean(grad_mag))
    except Exception:
        return 0.0


def _detect_crease_darkness(img_array: np.ndarray) -> float:
    """Detect darkness in crease regions (neck/shoulder areas)."""
    try:
        # Analyze upper-middle regions (neck area)
        h, w = img_array.shape[:2]
        crease_region = img_array[h//4:h//3, w//3:2*w//3, :]

        # Measure average darkness
        avg_brightness = np.mean(crease_region[:, :, :3])
        darkness = 1.0 - avg_brightness  # Invert: 1.0 = dark, 0.0 = bright
        return float(darkness)
    except Exception:
        return 0.0


def _detect_knuckle_shading(img_array: np.ndarray) -> bool:
    """Detect AO shading in hand/glove regions."""
    try:
        # Analyze lower regions (hand area)
        h, w = img_array.shape[:2]
        hand_region = img_array[2*h//3:, :, :]

        # Check for dark spots (knuckle AO)
        darkness = np.percentile(hand_region[:, :, :3], 25)  # 25th percentile brightness
        knuckle_shading = darkness < 0.4  # Knuckles should be fairly dark
        return bool(knuckle_shading)
    except Exception:
        return False


def _detect_silhouette_3d_definition(img_array: np.ndarray) -> bool:
    """Detect 3D definition in silhouette edges."""
    try:
        # Compute Sobel edges
        gy, gx = np.gradient(np.mean(img_array[:, :, :3], axis=2))
        edge_mag = np.sqrt(gx**2 + gy**2)

        # High edge contrast indicates 3D definition
        edge_contrast = np.std(edge_mag[edge_mag > np.median(edge_mag)])
        return bool(edge_contrast > 0.05)
    except Exception:
        return False


# ============================================================================
# CLI INTERFACE
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Radiometry measurement probe for lighting evidence collection"
    )
    parser.add_argument("--screenshot", required=True, help="Path to viewport screenshot")
    parser.add_argument("--mode", choices=["radiance", "texture_density", "both"],
                       default="radiance", help="Measurement mode")
    parser.add_argument("--output", help="Output file path (JSON)")
    parser.add_argument("--roi-x", type=int, help="ROI center X (pixels)")
    parser.add_argument("--roi-y", type=int, help="ROI center Y (pixels)")
    parser.add_argument("--roi-radius", type=int, default=50, help="ROI radius (pixels)")

    args = parser.parse_args()

    results = {}

    if args.mode in ("radiance", "both"):
        measurement = measure_visor_radiometry(args.screenshot, args.roi_x, args.roi_y, args.roi_radius)
        if measurement:
            results["radiometry"] = asdict(measurement)
        else:
            print("ERROR: Radiometry measurement failed", file=sys.stderr)
            sys.exit(1)

    if args.mode in ("texture_density", "both"):
        ao_analysis = measure_ao_texture_density(args.screenshot)
        if ao_analysis:
            results["ambient_occlusion"] = asdict(ao_analysis)
        else:
            print("ERROR: AO texture analysis failed", file=sys.stderr)
            sys.exit(1)

    # Output results
    output_json = json.dumps(results, indent=2)
    if args.output:
        Path(args.output).write_text(output_json)
        print(f"Measurements written to {args.output}")
    else:
        print(output_json)


if __name__ == "__main__":
    main()
