"""matter.py -- the buffer a membrane's law emits its matter into.

The Chimera Engine renders Gaussian splats: an (N, 28) array where each row is one grain of matter.
This is the only thing a folder needs to know about the renderer, so it lives once, here, and every
membrane's `physics.py` emits into it.

EVERY MEMBRANE WORKS IN ITS OWN LOCAL UNITS. A horizon is 2.3e-35 m and a planet is 6.4e6 m; if
both were emitted in metres one of them would be lost to float precision. But a boundary supplies a
local unit -- a coordinate cannot exceed its own membrane's extent -- so each law emits at radius ~1
in its own frame, and the parent scales its children when it composes them. Precision stops being
a problem the moment the membrane is the unit.
"""
from __future__ import annotations

import numpy as np

NCOLS = 28
PX, PY, PZ = 0, 1, 2
TYPE = 11
CR, CG, CB, ALPHA, SIZE = 16, 17, 18, 19, 20
NX, NY, NZ = 21, 22, 23        # optional outward normal -> the pipeline back-face-culls the far side

SOLID = 3.0                     # opaque, isotropic grain -- matter you can see the surface of
GLOW = 5.0                      # big soft blob -- light, plasma, a field


def blank(n: int) -> np.ndarray:
    """n grains of nothing, ready to be given a place, a colour and a size."""
    return np.zeros((n, NCOLS), dtype=np.float32)


def fibonacci_sphere(n: int) -> np.ndarray:
    """n unit vectors spread evenly over a sphere (the golden-angle spiral). Deterministic."""
    i = np.arange(n, dtype=np.float64)
    z = 1.0 - 2.0 * (i + 0.5) / n
    r = np.sqrt(np.clip(1.0 - z * z, 0.0, 1.0))
    th = np.pi * (1.0 + 5.0 ** 0.5) * i
    return np.stack([r * np.cos(th), r * np.sin(th), z], axis=1)


def paint(buf: np.ndarray, rgb, alpha: float, size: float, kind: float = SOLID) -> np.ndarray:
    buf[:, CR], buf[:, CG], buf[:, CB] = rgb
    buf[:, ALPHA] = alpha
    buf[:, SIZE] = size
    buf[:, TYPE] = kind
    return buf


def lit(albedo, irradiance, e_ref: float = 1.0, tone: float = 0.25):
    """A SPLAT IS A MEASUREMENT OF LIGHT, not a coloured object.

    What leaves a grain is `albedo * E / pi` -- the matter says what FRACTION it returns, the light
    says HOW MUCH arrives. So the same rock is brilliant near a star and near-black far from one,
    and neither is a different material.

        albedo     (3,) or (N,3)   the matter's response  -- this is the material DNA
        irradiance  scalar or (N,) W/m^2 arriving         -- this is the light
        e_ref                      irradiance treated as "correctly exposed"

    TONE, DECLARED: real irradiance spans thousands to one across a disk while a display spans about
    a hundred to one, so a curve is unavoidable -- exactly what a camera does. `tone` is that curve
    (0.25 = fourth root), and it is the ONE human parameter here. Everything else is measured."""
    import numpy as np
    a = np.asarray(albedo, dtype=np.float32)
    e = np.asarray(irradiance, dtype=np.float32)
    scale = np.clip(e / max(e_ref, 1e-30), 0.0, None) ** tone
    if a.ndim == 1:
        a = a[None, :]
    return np.clip(a * scale.reshape(-1, 1), 0.0, 1.0)


def blackbody_rgb(T: float) -> tuple:
    """A crude but honest colour for a temperature: the colour is a MEASUREMENT of the physics,
    never a choice. Cool -> red, ~5800 K -> white, very hot -> blue-white."""
    t = float(np.clip(T, 1000.0, 40000.0))
    if t < 5800.0:
        f = (t - 1000.0) / 4800.0
        return (1.0, 0.35 + 0.6 * f, 0.1 + 0.85 * f)
    f = min(1.0, (t - 5800.0) / 20000.0)
    return (1.0 - 0.35 * f, 1.0 - 0.15 * f, 1.0)
