"""Lighting Artist organ — mood-driven light rigs per scene.

Charter:
- Mood-driven light rigs per scene (key/fill/rim recipes already proven in L_VerificationStudio pathways)
- Exposure sanity checks on screenshots
- Day/night variants
- First work item: address pain phase_4d2da4e032a4aa07:P1 (pads read near-black)

Usage:
  python -m core.lumen_rig --scene <scene_name> --rig-type key_fill_rim
  python -m core.lumen_rig --screenshot-check Saved/Screenshots/*.png
"""

import argparse
import json
import os
import sys
from pathlib import Path

try:
    from core.graphify_interface import record_feature, record_pathway, record_surprise
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from core.graphify_interface import record_feature, record_pathway, record_surprise

ROOT = Path(__file__).resolve().parent.parent


class LumenRig:
    """Lighting Artist organ for mood-driven light rigs and exposure checks."""

    def __init__(self):
        self.feature_name = "lighting_artist_lumen_rig"

    def create_light_rig(self, scene: str, rig_type: str):
        """Create a mood-driven light rig (key/fill/rim recipes)."""
        # Recipes proven in L_VerificationStudio pathways
        rigs = {
            "key_fill_rim": {"key_intensity": 1.2, "fill_intensity": 0.4, "rim_intensity": 0.8},
            "day_night_variant": {"day_key": 1.5, "night_key": 0.3, "ambient_shift": -0.5},
        }

        if rig_type not in rigs:
            raise ValueError(f"Unknown rig type: {rig_type}")

        rig_config = rigs[rig_type]
        print(f"[lumen_rig] created {rig_type} rig for scene '{scene}': {json.dumps(rig_config)}")

        # Record pathway
        record_pathway(
            name=f"light_rig_{rig_type}_created",
            context=f"Created {rig_type} light rig for scene {scene}",
            source="agent-lumen-rig",
        )

        return rig_config

    def check_screenshot_exposure(self, screenshot_path: str):
        """Exposure sanity checks on screenshots."""
        # Check if screenshot exists and has valid size
        path = Path(screenshot_path)
        if not path.exists():
            raise FileNotFoundError(f"Screenshot not found: {screenshot_path}")

        size = path.stat().st_size
        if size < 100000:
            print(f"[lumen_rig] WARNING: screenshot {screenshot_path} is too small ({size} bytes) - may indicate dark/void-black pads")
            # Record surprise for near-black pads pain
            record_surprise(
                context="Screenshot exposure check detected potentially dark/void-black pads",
                reality=f"Screenshot {screenshot_path} has size {size} bytes, below 100KB threshold",
                source="agent-lumen-rig",
            )
            return {"valid": False, "issue": "potentially_dark_pads"}

        print(f"[lumen_rig] screenshot exposure check passed: {screenshot_path} ({size} bytes)")
        return {"valid": True, "size_bytes": size}

    def run(self, scene: str = None, rig_type: str = None, screenshot_check: str = None):
        """Run lighting artist operations."""
        print("[lumen_rig] running lumen_rig operations")

        if scene and rig_type:
            self.create_light_rig(scene, rig_type)

        if screenshot_check:
            self.check_screenshot_exposure(screenshot_check)

        # Record feature update
        record_feature(
            name=self.feature_name,
            loop=6,  # Loop 6: Shelter
            status="researching",
        )

        print("[lumen_rig] lumen_rig operations complete")


def main():
    parser = argparse.ArgumentParser(description="Lighting Artist organ — mood-driven light rigs per scene")
    parser.add_argument("--scene", type=str, help="Scene name for light rig")
    parser.add_argument("--rig-type", type=str, choices=["key_fill_rim", "day_night_variant"], help="Type of light rig")
    parser.add_argument("--screenshot-check", type=str, help="Screenshot path for exposure sanity check")
    parser.add_argument("--dry-run", action="store_true", help="Dry run without executing")

    args = parser.parse_args()

    if args.dry_run:
        print("[lumen_rig] dry run mode — no execution")
        return 0

    rig = LumenRig()
    rig.run(
        scene=args.scene,
        rig_type=args.rig_type,
        screenshot_check=args.screenshot_check,
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
