"""Diagnostic paint-by-part: color a settled coat by part_id.

Loads a .splat + its .meta.npz sidecar (part_id, uv from settle_coat) and
paints every part a distinct color, so the eye can verify the gravity settle
partitioned the paint correctly (forearm paint ON the forearm, nowhere else).

Usage: python tools/paint_parts.py in.splat out.splat
"""
import sys

import numpy as np

sys.path.insert(0, r"E:\PythonChimera\ChimeraEngine")
import cpp_bridge as cb  # noqa: E402

# distinct categorical colors (0-1 rgb), one per catalog slot order
PALETTE = {
    "torso":       (0.55, 0.35, 0.20),  # brown
    "head":        (0.85, 0.65, 0.40),  # tan
    "muzzle":      (0.95, 0.55, 0.55),  # pink
    "ear_L":       (0.30, 0.45, 0.95),  # blue
    "ear_R":       (0.30, 0.85, 0.40),  # green
    "eye_L":       (1.00, 1.00, 1.00),  # white
    "eye_R":       (0.05, 0.05, 0.05),  # black
    "upper_arm_L": (0.90, 0.20, 0.20),  # red
    "forearm_L":   (0.95, 0.60, 0.10),  # orange
    "upper_arm_R": (0.60, 0.25, 0.85),  # purple
    "forearm_R":   (0.90, 0.30, 0.70),  # magenta
    "thigh_L":     (0.15, 0.80, 0.85),  # cyan
    "shin_L":      (0.10, 0.50, 0.55),  # teal
    "thigh_R":     (0.95, 0.90, 0.20),  # yellow
    "shin_R":      (0.60, 0.85, 0.20),  # lime
}


def main(inp, outp):
    import teddy_body as tb  # parts order = assembly order
    buf = cb.load_splat(inp)
    meta = np.load(inp.replace(".splat", ".meta.npz"))
    pid = meta["part_id"]
    assert len(pid) == len(buf), f"meta {len(pid)} != splats {len(buf)}"
    names = [p["name"] for p in tb.PARTS]
    for i, name in enumerate(names):
        m = pid == i
        buf[m, 3:6] = PALETTE.get(name, (1.0, 1.0, 1.0))
        print(f"  {name:12s} {int(m.sum()):6d} splats -> {PALETTE.get(name)}")
    cb.save_splat(outp, buf)
    print(f"wrote {outp}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
