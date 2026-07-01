"""
TES Screenshot Analysis - Earth-Scale Landscape Verification

Analyzes screenshots from the Holodeck Convergence project to verify:
1. Seamless edge wrapping at landscape boundaries
2. Flat-to-sphere morph formula (apparent_radius = actual_radius / distance)
3. No pop, stutter, or visual tearing during transitions

Uses LM Studio for AI-powered subjective analysis of rendered world state.
"""

import os
import sys

sys.path.insert(0, r"E:\PythonChimera\Chimera\Python")

from config import LM_STUDIO_MODEL, CHIMERA_SAVED_SCREENSHOTS_DIR
from lmstudio_client import send_to_lmstudio, display_response


def analyze_edge_wrapping():
    """Analyze screenshot for seamless edge wrapping verification."""
    screenshot_path = os.path.join(CHIMERA_SAVED_SCREENSHOTS_DIR, "AutoScreenshot.png")

    if not os.path.exists(screenshot_path):
        print("[FAIL] No screenshot found at", screenshot_path)
        return None

    prompt = (
        "You are the Screenshot TES analyzing a gameplay screenshot from the Holodeck Convergence.\n\n"
        "This is an Earth-scale landscape with seamless edge wrapping enabled.\n\n"
        "Analyze the following:\n"
        "1. Does the terrain appear continuous at all edges of the viewport?\n"
        "2. Is there any pop, tearing, or visual discontinuity where the player wraps around?\n"
        "3. Does the landscape geometry flow seamlessly across screen boundaries?\n\n"
        "Provide a clear verdict: Edge wrapping is seamless? Yes or No.\n"
        "Describe any artifacts or discontinuities you observe."
    )

    result = send_to_lmstudio(
        prompt=prompt,
        image_path=screenshot_path,
        model_id=LM_STUDIO_MODEL,
        temperature=0.3,
        max_tokens=1024,
        timeout=120
    )

    if result:
        display_response(result)

    return result


def analyze_flat_to_sphere_morph():
    """Analyze screenshot for flat-to-sphere morph formula verification."""
    screenshot_path = os.path.join(CHIMERA_SAVED_SCREENSHOTS_DIR, "AutoScreenshot.png")

    if not os.path.exists(screenshot_path):
        print("[FAIL] No screenshot found at", screenshot_path)
        return None

    prompt = (
        "You are the Screenshot TES analyzing a gameplay screenshot from the Holodeck Convergence.\n\n"
        "The player is ascending in a spaceship. The landscape should morph from flat to spherical via World Position Offset (WPO).\n\n"
        "Analyze the following:\n"
        "1. Does the terrain appear to curve into a sphere shape?\n"
        "2. Is the curvature consistent with apparent_radius = actual_radius / distance formula?\n"
        "3. Are there any seams, artifacts, or discontinuities in the vertex shader morph?\n"
        "4. Does the horizon show spherical curvature rather than flat plane?\n\n"
        "Provide a clear verdict: Flat-to-sphere morph is correct? Yes or No.\n"
        "Describe the apparent radius of curvature relative to player altitude."
    )

    result = send_to_lmstudio(
        prompt=prompt,
        image_path=screenshot_path,
        model_id=LM_STUDIO_MODEL,
        temperature=0.3,
        max_tokens=1024,
        timeout=120
    )

    if result:
        display_response(result)

    return result


def run_earth_scale_verification():
    """Run full TES verification for Earth-scale landscape features."""
    print("=" * 60)
    print("TES EARTH-SCALE LANDSCAPE VERIFICATION")
    print("=" * 60)

    results = {
        "edge_wrapping": None,
        "flat_to_sphere_morph": None
    }

    print("\n[1] Analyzing edge wrapping...")
    results["edge_wrapping"] = analyze_edge_wrapping()

    print("\n[2] Analyzing flat-to-sphere morph formula...")
    results["flat_to_sphere_morph"] = analyze_flat_to_sphere_morph()

    # Summary
    print("\n" + "=" * 60)
    print("TES VERIFICATION SUMMARY")
    print("=" * 60)

    for test_name, result in results.items():
        status = "PASS" if result and ("Yes" in str(result).lower() or "seamless" in str(result).lower()) else "FAIL"
        print(f"{test_name}: {status}")

    return results


if __name__ == "__main__":
    run_earth_scale_verification()
