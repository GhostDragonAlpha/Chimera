"""rebuild_poses.py — rewrite capture/sv3d_bear/poses.json for the 5-ring dataset.

Rings: eq (0°), el20 (+20°), top (+40°), elm20 (-20°, flip trick), bot (-40°, flip trick).
SV3D frame_00 of every ring is ~the anchor image at el≈0 regardless of the commanded
polar (verified visually: ring_top/frame_00 == front view), so frame_00 is kept ONLY
for the eq ring; frames 1..20 carry their commanded ring elevation.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "capture" / "sv3d_bear"

RINGS = [("eq", 0.0, True), ("el20", 20.0, False), ("top", 40.0, False),
         ("elm20", -20.0, False), ("bot", -40.0, False)]
N = 21

poses = []
for ring, el, keep_f0 in RINGS:
    for i in range(N):
        if i == 0 and not keep_f0:
            continue
        az = 360.0 * i / N
        poses.append({
            "ring": ring,
            "frame_index": i,
            "frame_filename": f"ring_{ring}/frame_{i:02d}.png",
            "elevation_deg": el,
            "azimuth_deg": az,
        })

out = {"model": "stabilityai/sv3d", "checkpoint": "sv3d_p.safetensors",
       "num_frames_per_ring": N, "resolution": 576, "seed": 42,
       "note": "5 rings; frame_00 dropped for non-eq rings (SV3D frame_00 == anchor pose)",
       "poses": poses}
(SRC / "poses.json").write_text(json.dumps(out, indent=2))
print(f"poses.json rewritten: {len(poses)} poses "
      f"(eq 21 + 4 rings x 20)")
