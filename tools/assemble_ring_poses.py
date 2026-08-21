"""assemble_ring_poses.py -- scan ring_* dirs -> poses.json for sv3d_to_colmap.py.

gen_ring.py writes frames + GIFs but no poses.json; this reconstructs it from the
ring dirs (the commanded orbit IS the ground truth -- sv3d_to_colmap.py consumes
elevation_deg/azimuth_deg per frame). Frame_00 of every ring is ~the anchor image
(SV3D is image-conditioned); it is dropped for non-equatorial rings so the anchor
view enters the dataset exactly once.

Usage:
  .venv-gs/Scripts/python.exe tools/assemble_ring_poses.py --src capture/sv3d_real
"""
from __future__ import annotations

import argparse
import datetime
import json
import math
from pathlib import Path

RINGS = {"eq": 0.0, "el20": 20.0, "elm20": -20.0, "top": 40.0, "bot": -40.0}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--rings", default=",".join(RINGS), help="comma-separated ring subset (eq,el20,elm20,top,bot)")
    args = ap.parse_args()
    src = Path(args.src)

    poses = []
    for ring, elev in RINGS.items():
        if ring not in args.rings.split(","):
            continue
        ring_dir = src / f"ring_{ring}"
        frames = sorted(ring_dir.glob("frame_*.png"))
        if not frames:
            print(f"[skip] {ring_dir} empty or missing")
            continue
        n = len(frames)
        azimuths = [i * 360.0 / n for i in range(n)]
        for i, (f, az) in enumerate(zip(frames, azimuths)):
            if i == 0 and ring != "eq":
                continue  # duplicate anchor view
            poses.append({
                "ring": ring,
                "frame_index": i,
                "frame_filename": f"ring_{ring}/{f.name}",
                "elevation_deg": elev,
                "azimuth_deg": az,
                "polar_rad": math.radians(90.0 - elev),
                "azimuth_rad": math.radians(az),
            })
        print(f"[{ring}] {n} frames at el={elev:+.1f} -> {n - (0 if ring == 'eq' else 1)} poses")

    out = src / "poses.json"
    out.write_text(json.dumps({
        "model": "stabilityai/sv3d",
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "poses": poses,
    }, indent=2))
    print(f"poses.json -> {out} ({len(poses)} poses)")


if __name__ == "__main__":
    main()
