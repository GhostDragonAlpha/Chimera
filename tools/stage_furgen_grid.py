#!/usr/bin/env python
"""Stage the furgen-generated patches as ONE orbitable 3D splat.

The eye judged the 2D sheet; the operator judges in 3D. Loads every
.tmp/furgen/genNNN.npy (raw patch layout: u,v,h,rgb,alpha,log_s*3,quat*4),
converts each through qualify_corpus.patch_buffer (proper -90deg frame change
with quat conjugation), centers each patch, and lays them out in a 4x2 grid on
the ground plane so all eight can be orbited/zoomed in a single viewer window.

Writes models/triposplat/static/viewer/_qualify/furgen_grid.splat via
cpp_bridge.save_splat (which inverts SPLAT_ORIENT so viewer orient=0 is right).
"""
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "ChimeraEngine"))
import cpp_bridge as cb  # noqa: E402
from qualify_corpus import patch_buffer  # noqa: E402

GEN_DIR = Path(".tmp/furgen")
OUT = Path("models/triposplat/static/viewer/_qualify/furgen_grid.splat")
SPACING = 0.08  # m between patch centers (patches are 0.05 m wide)


def main() -> int:
    files = sorted(GEN_DIR.glob("gen*.npy"))
    if not files:
        print("REFUSED: no gen*.npy in .tmp/furgen")
        return 1
    parts = []
    for k, f in enumerate(files):
        buf = patch_buffer(np.load(f))
        buf[:, 0:3] -= buf[:, 0:3].mean(0)
        col, row = k % 4, k // 4
        buf[:, 0] += (col - 1.5) * SPACING   # u -> x
        buf[:, 2] += (row - 0.5) * SPACING   # -v -> z
        parts.append(buf.astype(np.float32))
        print(f"{f.name}: {len(buf)} splats -> grid ({col},{row})")
    grid = np.concatenate(parts)
    cb.save_splat(str(OUT), grid)
    print(f"WROTE {OUT} ({len(grid)} splats, 4x2 grid, spacing {SPACING} m)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
