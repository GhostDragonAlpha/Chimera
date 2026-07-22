"""3D backend (the product surface).

A posed tree skeleton -> Gaussian splats -> ParticleEngine on the GPU.
Reads the SAME scene model and the SAME anchors as the HTML dev backend; the
only thing that differs is how it draws (DESIGN §6).
"""
from __future__ import annotations
import math
import numpy as np

from ParticleEngine.gpu_pipeline import FullGPUPipeline
from ParticleEngine.camera import FirstPersonCamera


def _tree_splats(posed: dict, wind: dict, origin, rng, P, C, A, S) -> None:
    """Emit bark splats along each posed branch (radius already capped in
    tree.build_skeleton) and a green puff at every leaf tip.  Leaf jitter scales
    with wind 'flutter' — the same knob the HTML backend reads."""
    ox, oy, oz = origin
    flutter = float(wind.get("flutter", 0.0))

    def emit(node):
        st, en = node["start"], node["end"]
        L = math.dist(st, en)
        dr = node["radius"]
        npts = max(6, int(L / 4))
        for i in range(npts):
            t = i / max(1, npts - 1)
            px = (st[0] + (en[0] - st[0]) * t,
                  st[1] + (en[1] - st[1]) * t,
                  st[2] + (en[2] - st[2]) * t)
            r = dr * (1.0 - t * 0.5) + 0.5
            k = max(2, int(r * 0.8))
            shade = 0.09 + node["depth"] * 0.02 - t * 0.015
            for _ in range(k):
                off = rng.normal(0, r * 0.45, 3)
                P.append((px[0] + off[0] + ox, px[1] + off[1] + oy, px[2] + off[2] + oz))
                C.append((0.26, 0.155, max(0.04, shade)))
                A.append(0.10)
                S.append(r * 0.5)
        if node["is_leaf"]:
            for _ in range(150):
                off = rng.normal(0, 1.0, 3) * np.array([19.0, 19.0, 15.0])
                off[0] += rng.normal(0, 7.0 * flutter)   # gusted leaves stream downwind (+X)
                off[2] += rng.normal(0, 4.0 * flutter)
                g = 0.38 + rng.random() * 0.30
                P.append((en[0] + off[0] + ox, en[1] + off[1] + oy, en[2] + off[2] + oz))
                C.append((0.08 + rng.random() * 0.10, g, 0.07 + rng.random() * 0.06))
                A.append(0.07 + rng.random() * 0.10)
                S.append(2.6 + rng.random() * 3.0)
        for c in node["children"]:
            emit(c)

    emit(posed)


def _look_at(cam, target, orbit_az, elev, dist):
    cam.position[0] = target[0] + math.cos(orbit_az) * math.cos(elev) * dist
    cam.position[1] = target[1] + math.sin(orbit_az) * math.cos(elev) * dist
    cam.position[2] = target[2] + math.sin(elev) * dist
    dx, dy, dz = (target[i] - cam.position[i] for i in range(3))
    cam.yaw = math.atan2(dy, dx)
    cam.pitch = math.atan2(dz, math.sqrt(dx * dx + dy * dy))


def render(posed_trees, wind: dict, width: int = 680, height: int = 620,
           seed: int = 7, orbit_az: float = -math.pi / 2, elev: float = 0.10) -> np.ndarray:
    """posed_trees: list of (posed_skeleton, origin).  Returns an RGB uint8 image.

    orbit_az / elev orbit the camera around the grove — turning orbit_az reveals
    depth (a flat sheet nearly vanishes edge-on; a 3D volume does not).

    The sky greys with wind 'sky' (blue -> overcast) — appearance derives from
    the same model state, no separate aesthetic pass (DESIGN §8)."""
    rng = np.random.default_rng(seed)
    P, C, A, S = [], [], [], []
    for posed, origin in posed_trees:
        _tree_splats(posed, wind, origin, rng, P, C, A, S)
    P = np.asarray(P, np.float32)
    C = np.asarray(C, np.float32)
    A = np.asarray(A, np.float32)
    S = np.asarray(S, np.float32)

    cov = np.zeros((len(P), 3, 3), np.float32)
    s2 = (S * 0.9) ** 2
    cov[:, 0, 0] = s2
    cov[:, 1, 1] = s2
    cov[:, 2, 2] = s2

    # This renderer composites ADDITIVELY over the background (emissive splats:
    # final = bg + Σ color·α·trans — the bg is never attenuated; measured).  So
    # saturated colour needs a DARK sky: on a light sky every splat only pushes
    # toward white and bark can never read dark.  A dusk palette lets bark read
    # brown and leaves green; the sky still greys with wind.  (A daylight 'over'
    # renderer is a separate backend concern — DESIGN §10.)
    sky = float(wind.get("sky", 0.0))
    bg = (0.16 * (1 - sky) + 0.22 * sky,
          0.22 * (1 - sky) + 0.22 * sky,
          0.32 * (1 - sky) + 0.24 * sky)
    pipe = FullGPUPipeline(bg=bg, base_scale=1.0)

    # auto-frame the whole grove from the splat bounds
    lo = P.min(0)
    hi = P.max(0)
    ctr = (lo + hi) / 2.0
    radius = float(np.linalg.norm(hi - lo)) / 2.0
    cam = FirstPersonCamera((0, -600, 0), fov=math.radians(52))
    dist = radius / math.tan(cam.fov / 2.0) * 1.15
    _look_at(cam, (float(ctr[0]), float(ctr[1]), float(ctr[2])), orbit_az, elev, dist)

    return pipe.render_splats(P, cov, C, A, cam, cam.params(width, height))
