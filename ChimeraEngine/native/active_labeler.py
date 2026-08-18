"""active_labeler.py — the vision model as an ACTIVE agent with data tools.

The split: the eye decides WHERE to look and WHAT each region IS; this module gives it the
TOOLS to do so, and does the one thing the eye cannot — the actual splat math.

Tools exposed to the loop:
    look(theta, phi)          render a view -> image path
    query_region(polygon, theta, phi)  -> the splats inside a freeform 2D region,
                                          plus their shape (scale) and color distributions

The region is a freeform polygon the EYE draws on a view (its shape decision), not an
arbitrary oval/box. The projection uses the engine's exact camera, so a polygon the eye
draws maps to the same splats the renderer drew.
"""
from __future__ import annotations

import io
import json
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image

from matplotlib.path import Path as MplPath

ENGINE = "http://localhost:8080"
W, H = 1920.0, 1080.0
FOV = np.radians(45.0)


def project(P, theta, phi, radius, W=W, H=H):
    """World points -> normalized 2D (0..1, origin top-left) under the engine camera."""
    c, s = np.cos(phi), np.sin(phi)
    cx, sx = np.cos(theta), np.sin(theta)
    eye = np.array([radius * c * sx, radius * s, -radius * c * cx])
    up = np.array([-s * sx, c, s * cx])
    z = eye / np.linalg.norm(eye)
    x = np.cross(up, z); x /= np.linalg.norm(x)
    y = np.cross(z, x)
    d = P - eye
    vx = d @ x; vy = d @ y; vz = d @ z
    f = 1.0 / np.tan(FOV / 2.0); aspect = W / H
    return ((-(f / aspect) * vx / vz) + 1.0) / 2.0, ((f * vy / vz) + 1.0) / 2.0


def _dist(v):
    if len(v) == 0:
        return {"mean": None, "std": None, "p10": None, "p90": None}
    return {"mean": float(np.mean(v)), "std": float(np.std(v)),
            "p10": float(np.percentile(v, 10)), "p90": float(np.percentile(v, 90))}


class ActiveLabeler:
    def __init__(self, splat_path):
        import sys
        import cpp_bridge as cb
        self.buf = cb.load_splat(splat_path)
        self.pos = self.buf[:, 0:3]
        self.col = self.buf[:, 3:6]
        self.scale = self.buf[:, 7:10]
        self.n = self.pos.shape[0]

    def look(self, theta, phi, radius=2.2, path=None):
        payload = json.dumps({"cam_radius": radius, "cam_theta": theta, "cam_phi": phi}).encode()
        req = urllib.request.Request(ENGINE + "/camera", data=payload,
                                     headers={"Content-Type": "application/json"}, method="POST")
        urllib.request.urlopen(req, timeout=15).read()
        png = urllib.request.urlopen(ENGINE + "/frame", timeout=30).read()
        path = path or str(Path(__file__).parent / "_active_view.png")
        Image.open(io.BytesIO(png)).convert("RGB").resize((640, 360)).save(path)
        return path

    def query_region(self, polygon, theta, phi, radius=2.2):
        """The splats inside a freeform 2D polygon (normalized 0..1), plus shape + color."""
        nx, ny = project(self.pos, theta, phi, radius)
        pts = np.column_stack([nx, ny])
        inside = MplPath(np.asarray(polygon)).contains_points(pts)
        idx = np.nonzero(inside)[0]
        s = self.scale[idx]
        mag = (s[:, 0] * s[:, 1] * s[:, 2]) ** (1 / 3)
        aniso = s.max(1) / np.maximum(s.min(1), 1e-4)
        return {
            "n_splats": int(len(idx)),
            "indices": idx.astype(np.int32),
            "shape": {
                "log_size": _dist(np.log(np.maximum(mag, 1e-4))),
                "aniso": _dist(aniso),
            },
            "color": {
                "r": _dist(self.col[idx, 0]), "g": _dist(self.col[idx, 1]), "b": _dist(self.col[idx, 2]),
                "mean": [float(self.col[idx, 0].mean()), float(self.col[idx, 1].mean()), float(self.col[idx, 2].mean())],
            },
        }
