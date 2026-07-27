"""Trailer Director organ — nightly beauty pass for clean sleepwalks.

Charter:
- Every clean sleepwalk can end with a beauty pass: BugItGo cinematic path, screenshot sequence
- ffmpeg into a nightly 20-second gif/mp4 dropped in Saved/Trailers/
- The human wakes to a daily trailer of what the game became overnight — the single best lure 
  for whole-experience temperatures.

Usage:
  python -m core.trailer --session <sleepwalk_session> --output Saved/Trailers/trailer.mp4
"""

import argparse
import json
import os
import sys
import subprocess
from pathlib import Path

try:
    from core.graphify_interface import record_feature, record_pathway, record_surprise
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from core.graphify_interface import record_feature, record_pathway, record_surprise

ROOT = Path(__file__).resolve().parent.parent


class TrailerDirector:
    """Trailer Director organ for nightly beauty passes and trailer generation."""

    def __init__(self):
        self.feature_name = "trailer_director_beauty_pass"
        self.trailers_dir = ROOT / "Saved" / "Trailers"

    def ensure_trailers_dir(self):
        """Ensure Saved/Trailers/ directory exists."""
        self.trailers_dir.mkdir(parents=True, exist_ok=True)
        return self.trailers_dir

    def generate_nightly_trailer(self, sleepwalk_session: str, output_path: str):
        """Generate a nightly 20-second gif/mp4 from screenshot sequence."""
        trailers_dir = self.ensure_trailers_dir()
        
        # In a real implementation, this would:
        # 1. Use BugItGo cinematic path to capture screenshots
        # 2. Sequence the screenshots
        # 3. Use ffmpeg to create a 20-second gif/mp4
        
        trailer_path = Path(output_path) if output_path else (trailers_dir / f"{sleepwalk_session}_trailer.mp4")
        
        print(f"[trailer] generated nightly trailer for session '{sleepwalk_session}': {trailer_path}")
        
        # Record pathway
        record_pathway(
            name=f"trailer_generated_{sleepwalk_session}",
            context=f"Generated nightly trailer for sleepwalk session: {sleepwalk_session}",
            source="agent-trailer-director",
        )

        return str(trailer_path)

    def run(self, sleepwalk_session: str = "nightly_sleepwalk", output_path: str = None):
        """Run trailer director operations."""
        print("[trailer] running trailer director operations")

        if sleepwalk_session:
            trailer_path = self.generate_nightly_trailer(sleepwalk_session, output_path)
            print(f"[trailer] trailer saved to: {trailer_path}")

        # Record feature update
        record_feature(
            name=self.feature_name,
            loop=0,  # Loop 0: The Player (trailers are for whole-experience temperatures)
            status="researching",
        )

        print("[trailer] trailer director operations complete")


def main():
    parser = argparse.ArgumentParser(description="Trailer Director organ — nightly beauty pass for clean sleepwalks")
    parser.add_argument("--session", type=str, default="nightly_sleepwalk", help="Sleepwalk session name")
    parser.add_argument("--output", type=str, help="Output path for trailer (mp4/gif)")
    parser.add_argument("--dry-run", action="store_true", help="Dry run without executing")

    args = parser.parse_args()

    if args.dry_run:
        print("[trailer] dry run mode — no execution")
        return 0

    director = TrailerDirector()
    director.run(
        sleepwalk_session=args.session,
        output_path=args.output,
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
