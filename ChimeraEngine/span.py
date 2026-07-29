"""span.py — a membrane's FOUR-DIMENSIONAL SPAN, in one image.

A still is a photograph and a turntable is only three dimensions. A membrane lives in four: three of
space and one of time. So the deliverable when a membrane is finished is a SPAN across both —

    columns  →  SPACE : the same instant seen from angles around it (it is a volume, not a picture)
    rows     ↓  TIME  : its own unfolding, t = 0 (beginning) to t = 1 (settled)

Read across a row and the thing turns; read down a column and it happens. One artifact, judged at a
glance, and it cannot hide either kind of lie: a flat sprite fails the row, a static scene fails the
column.

Rendered by the Chimera engine's own pipeline in the membrane's own local units, with the camera set
by its measured extent — nothing hand-framed.

Run:  python ChimeraEngine/span.py <term> [--cols 5] [--rows 3]
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

_TILE_W, _TILE_H = 480, 360
_PAD = 6


def span(term: str, cols: int = 5, rows: int = 3, out: Path | None = None) -> Path:
    import numpy as np
    from PIL import Image, ImageDraw
    import splat_appearance as SA
    from ParticleEngine.gpu_pipeline import FullGPUPipeline
    from ParticleEngine.camera import FirstPersonCamera

    buf1 = SA.scene_buffer(term)
    if buf1 is None:
        raise SystemExit(f"no scene for `{term}`")
    extent = float(np.linalg.norm(np.asarray(buf1)[:, 0:3], axis=1).max()) or 1.0
    R = 2.9 * extent
    pipe = FullGPUPipeline(bg=(0.015, 0.015, 0.04))

    sheet = Image.new("RGB", (cols * _TILE_W + (cols + 1) * _PAD,
                              rows * _TILE_H + (rows + 1) * _PAD + 26), (8, 9, 16))
    dr = ImageDraw.Draw(sheet)
    dr.text((_PAD + 2, 6), f"{term} — 4D span:  columns turn it (space),  rows unfold it (time)",
            fill=(190, 200, 220))

    for r in range(rows):
        t = 0.0 if rows == 1 else r / (rows - 1)
        b = SA.membrane_buffer(term, t)
        if b is None:                                   # a painted scene has no time axis of its own
            b = buf1
        pipe.upload(np.ascontiguousarray(b, dtype=np.float32))
        for c in range(cols):
            az = 2.0 * math.pi * c / cols
            el = 0.22
            pos = (R * math.cos(el) * math.sin(az), -R * math.cos(el) * math.cos(az), R * math.sin(el))
            n = math.sqrt(sum(v * v for v in pos)) or 1.0
            f = tuple(-v / n for v in pos)
            cam = FirstPersonCamera(pos, yaw=math.atan2(f[1], f[0]),
                                    pitch=math.atan2(f[2], math.hypot(f[0], f[1])))
            img = Image.fromarray(pipe.render_from_gpu(cam, cam.params(_TILE_W, _TILE_H)))
            sheet.paste(img, (_PAD + c * (_TILE_W + _PAD), 26 + _PAD + r * (_TILE_H + _PAD)))
        dr.text((_PAD + 4, 26 + _PAD + r * (_TILE_H + _PAD) + 4), f"t={t:.1f}", fill=(150, 165, 190))

    out = out or (HERE.parent / f"span_{term}.png")
    sheet.save(out)
    return out


if __name__ == "__main__":
    term = sys.argv[1] if len(sys.argv) > 1 else "theSolarSystem"
    cols = int(sys.argv[sys.argv.index("--cols") + 1]) if "--cols" in sys.argv else 5
    rows = int(sys.argv[sys.argv.index("--rows") + 1]) if "--rows" in sys.argv else 3
    print(span(term, cols, rows))
