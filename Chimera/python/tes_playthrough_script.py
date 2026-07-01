"""
TES Automated Playthrough Script — Holodeck Convergence

Simulates automated flight through Earth-scale landscape with edge wrapping,
flat-to-sphere morphing, and Lagrange transition zones. Captures screenshots
at defined waypoints for Screenshot TES analysis.

Usage:
    python tes_playthrough_script.py [--waypoints all] [--screenshot-dir E:\\PythonChimera\\Chimera\\Saved\\Screenshots]
"""

import argparse
import json
import os
import sys
import time

sys.path.insert(0, r"E:\PythonChimera\Chimera\Python")

from config import LM_STUDIO_MODEL, CHIMERA_SAVED_SCREENSHOTS_DIR
from lmstudio_client import send_to_lmstudio, display_response


# ---------------------------------------------------------------------------
# Waypoint Definitions (Flight Path)
# ---------------------------------------------------------------------------

WAYPOINTS = {
    "edge_wrapping": [
        {"name": "EdgeApproach", "location": (-49500.0, -49500.0, 100.0), "description": "Player approaches landscape edge"},
        {"name": "EdgeCrossing", "location": (-50000.0, -50000.0, 100.0), "description": "Player crosses edge boundary (wrapping triggers)"},
        {"name": "EdgeWrapped", "location": (49500.0, 49500.0, 100.0), "description": "Player wrapped to opposite side of landscape"}
    ],
    "ascent_morph": [
        {"name": "GroundLevel", "location": (0.0, 0.0, 100.0), "description": "Player at ground level (flat terrain)"},
        {"name": "LowAltitude", "location": (0.0, 0.0, 5000.0), "description": "Player ascending to low altitude (morph begins)"},
        {"name": "MidAltitude", "location": (0.0, 0.0, 25000.0), "description": "Player at mid altitude (spherical morph visible)"},
        {"name": "HighAltitude", "location": (0.0, 0.0, 100000.0), "description": "Player at high altitude (full spherical terrain)"}
    ],
    "lagrange_transition": [
        {"name": "EarthApproach", "location": (0.0, 50000000.0, 100.0), "description": "Player near Earth center"},
        {"name": "TransitionEntry", "location": (0.0, 200000000.0, 100.0), "description": "Player enters Lagrange transition zone"},
        {"name": "TransitionMidpoint", "location": (0.0, 300000000.0, 100.0), "description": "Player at midpoint of Earth-Moon transition"},
        {"name": "MoonApproach", "location": (0.0, 384400000.0, 100.0), "description": "Player approaches Moon center"}
    ]
}


# ---------------------------------------------------------------------------
# Screenshot Capture and TES Analysis
# ---------------------------------------------------------------------------

def capture_screenshot(waypoint_name, screenshot_dir):
    """Simulate screenshot capture at a waypoint (in real UE Editor, this would use MCP control_editor)."""
    # In actual implementation, this would call MCP control_editor action=screenshot
    # For now, we simulate by checking if AutoScreenshot.png exists and copying it with waypoint name
    
    source_path = os.path.join(CHIMERA_SAVED_SCREENSHOTS_DIR, "AutoScreenshot.png")
    
    if not os.path.exists(source_path):
        print(f"[WARN] No screenshot found at {source_path} — simulating capture for waypoint {waypoint_name}")
        return None
    
    dest_path = os.path.join(screenshot_dir, f"tes_{waypoint_name}.png")
    import shutil
    shutil.copy2(source_path, dest_path)
    
    print(f"[CAPTURE] Screenshot saved to {dest_path} for waypoint {waypoint_name}")
    return dest_path


def analyze_waypoint_screenshot(screenshot_path, waypoint_data):
    """Send screenshot to LM Studio for TES analysis at a specific waypoint."""
    if not screenshot_path or not os.path.exists(screenshot_path):
        print(f"[FAIL] No screenshot available for waypoint {waypoint_data['name']}")
        return None

    prompt = (
        f"You are the Screenshot TES analyzing a gameplay screenshot from the Holodeck Convergence.\n\n"
        f"Waypoint: {waypoint_data['name']}\n"
        f"Description: {waypoint_data['description']}\n"
        f"Player Location: ({waypoint_data['location'][0]}, {waypoint_data['location'][1]}, {waypoint_data['location'][2]})\n\n"
    )

    if "edge" in waypoint_data['name'].lower():
        prompt += (
            "Analyze the following for edge wrapping verification:\n"
            "1. Does the terrain appear continuous at all edges of the viewport?\n"
            "2. Is there any pop, tearing, or visual discontinuity where the player wraps around?\n"
            "3. Does the landscape geometry flow seamlessly across screen boundaries?\n\n"
            "Provide a clear verdict: Edge wrapping is seamless? Yes or No."
        )
    elif "ascent" in waypoint_data['name'].lower() or "altitude" in waypoint_data['name'].lower():
        prompt += (
            "Analyze the following for flat-to-sphere morph formula verification:\n"
            "1. Does the terrain appear to curve into a sphere shape?\n"
            "2. Is the curvature consistent with apparent_radius = actual_radius / distance formula?\n"
            "3. Are there any seams, artifacts, or discontinuities in the vertex shader morph?\n"
            "4. Does the horizon show spherical curvature rather than flat plane?\n\n"
            "Provide a clear verdict: Flat-to-sphere morph is correct? Yes or No."
        )
    elif "lagrange" in waypoint_data['name'].lower() or "transition" in waypoint_data['name'].lower():
        prompt += (
            "Analyze the following for Lagrange transition zone verification:\n"
            "1. Is there any pop, stutter, or lighting change during the coordinate/level switch?\n"
            "2. Does the celestial body (Moon) appear at correct distance with appropriate apparent size?\n"
            "3. Does the transition feel seamless and invisible to the player?\n\n"
            "Provide a clear verdict: Lagrange transition is seamless? Yes or No."
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


# ---------------------------------------------------------------------------
# Playthrough Execution
# ---------------------------------------------------------------------------

def run_playthrough(waypoint_groups=None, screenshot_dir=None):
    """Run automated flight playthrough through all defined waypoints."""
    
    if waypoint_groups is None:
        waypoint_groups = ["edge_wrapping", "ascent_morph", "lagrange_transition"]
    
    if screenshot_dir is None:
        screenshot_dir = os.path.join(CHIMERA_SAVED_SCREENSHOTS_DIR, "tes_waypoints")
    
    os.makedirs(screenshot_dir, exist_ok=True)
    
    results = {
            "waypoints": [],
            "summary": {}
        }

    print("=" * 60)
    print("TES AUTOMATED PLAYTHROUGH (Holodeck Convergence)")
    print("=" * 60)

    for group_name in waypoint_groups:
        if group_name not in WAYPOINTS:
            print(f"[WARN] Unknown waypoint group: {group_name}")
            continue
        
        waypoints = WAYPOINTS[group_name]
        print(f"\n[GROUP] Running {group_name} waypoints...")
        
        for i, waypoint_data in enumerate(waypoints):
            print(f"\n[{i+1}/{len(waypoints)}] Processing waypoint: {waypoint_data['name']}")
            
            # Capture screenshot at waypoint
            screenshot_path = capture_screenshot(waypoint_data["name"], screenshot_dir)
            
            # Analyze with TES
            tes_result = analyze_waypoint_screenshot(screenshot_path, waypoint_data)
            
            # Store result
            results["waypoints"].append({
                "group": group_name,
                "waypoint": waypoint_data["name"],
                "location": waypoint_data["location"],
                "screenshot": screenshot_path,
                "tes_result": str(tes_result)[:256] if tes_result else None,
                "timestamp": time.time()
            })

    # Generate summary
    total = len(results["waypoints"])
    passed = sum(1 for wp in results["waypoints"] if wp.get("tes_result") and ("Yes" in str(wp["tes_result"]).lower() or "seamless" in str(wp["tes_result"]).lower()))
    
    results["summary"] = {
        "total_waypoints": total,
        "passed": passed,
        "failed": total - passed,
        "pass_rate": (passed / total * 100) if total > 0 else 0.0
    }

    print("\n" + "=" * 60)
    print("PLAYTHROUGH COMPLETE")
    print("=" * 60)
    print(f"Total waypoints: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Pass rate: {results['summary']['pass_rate']:.1f}%")

    # Save results to JSON
    results_path = os.path.join(screenshot_dir, "tes_playthrough_results.json")
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=4)
    
    print(f"\nResults saved to {results_path}")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TES Automated Playthrough Script")
    parser.add_argument("--waypoints", nargs="+", default=["edge_wrapping", "ascent_morph", "lagrange_transition"],
                        help="Waypoint groups to run (default: all)")
    parser.add_argument("--screenshot-dir", default=None,
                        help="Directory for screenshot capture (default: CHIMERA_SAVED_SCREENSHOTS_DIR/tes_waypoints)")
    
    args = parser.parse_args()
    
    run_playthrough(waypoint_groups=args.waypoints, screenshot_dir=args.screenshot_dir)
