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
# THE ALBEDO A GRAIN IS MADE OF, as opposed to the colour it currently shows. A membrane that will be
# RELIT somewhere else (a body carried onto terrain, under that terrain's own sun) has to hand over
# what it is made of, not what it looked like in its own scene -- otherwise the relighting flattens
# every material into one. Optional: zero here means "no separate albedo, reuse the colour".
AR, AG, AB = 24, 25, 26

SOLID = 3.0                     # opaque, isotropic grain -- matter you can see the surface of
GLOW = 5.0                      # big soft blob -- light, plasma, a field

# THE SIZE YOU WRITE IS THE SIZE THAT RENDERS. That was not true until 2026-07-29.
#
# GLOW used to carry a hidden 6x multiplier in `gpu_pipeline._profile()`, so
# `paint(b, colour, alpha, 0.055, GLOW)` drew a 0.33 splat and no author could tell. It put seven
# membranes over the rasteriser's per-tile cap, silently invalidated both helpers below (they return
# the size you should ASK for, which was not the size that LANDED), and gave theStar a six-fold pop
# in grain size at t=0.8 where its type switched.
#
# It is gone. Every GLOW call in the tree was multiplied by 6 in the same commit, so the pictures did
# not move -- only the honesty did. **A membrane states its own grain size and is believed.**


def blank(n: int) -> np.ndarray:
    """n grains of nothing, ready to be given a place, a colour and a size."""
    return np.zeros((n, NCOLS), dtype=np.float32)


def grains_for(radius: float, extent: float, full: int = 900, floor: int = 16,
               screen_px: int = 1080, per_px: float = 0.5) -> int:
    """HOW MANY GRAINS A BODY DESERVES AT THIS FRAMING. The pixel-budget law, and it is a
    CORRECTNESS rule, not an optimisation.

    A thing that occupies one pixel does not need a thousand grains to say so -- and if you give it
    a thousand anyway they all land in the same 32-px tile, overrun the rasteriser's MAX_PER_TILE,
    and the cap evicts everything ELSE in that tile. The result is a BLACK, TILE-SHAPED HOLE next to
    the object: not a dim patch, a hard-edged rectangle on the tile grid, which is the tell.

    MEASURED, and this is what the law is written from: thePlanets drew each of eleven worlds with
    900 grains. At a framing 11.2 units across, the inner worlds are 0.0096 units in radius -- a
    QUARTER OF A PIXEL. Five of them within 36 px of screen centre put 4,801 splats into one tile
    that allows 4,096, and tile 989 (x 928-959, y 512-543) rendered as background.

    The same law is what the star above already obeys. It was written down there and not applied
    here, which is how a rule that is only prose gets broken twice.

    Grains scale with PROJECTED AREA -- a body twice as wide on screen deserves four times as many.
    The floor keeps a sub-pixel body visible as a dot; the cap stops a close one from exploding.

    `extent` is the membrane's own drawn extent (its 99th-percentile radius), and the 2.8 is the
    camera-distance rule the viewer uses, so this needs nothing the emit does not already know."""
    px_r = abs(float(radius)) / max(abs(float(extent)), 1e-12) * (screen_px / 2.0) / 2.8
    n = int(per_px * np.pi * px_r * px_r)
    return int(min(max(n, floor), full))


def surface_grain(n: int, radius: float = 1.0, cover: float = 0.58) -> float:
    """HOW BIG A GRAIN HAS TO BE TO CLOSE A SURFACE. Not a taste setting -- arithmetic.

    n grains spread over a sphere of radius r sit `sqrt(4*pi*r^2/n)` apart. A splat narrower than
    about half that spacing leaves gaps, and because there is nothing behind a planet, the gaps are
    BLACK: the ocean reads as loose grit floating in space instead of as water. Wider than the
    spacing and the surface goes soft and every feature blurs.

    So the grain is a CONSEQUENCE of how many you asked for, and computing it here means changing
    the count can never silently reopen the holes. The same rule inverted is the reason a shell must
    be sampled finely enough to be thinner than its own grains are wide -- an atmosphere drawn with
    coarse splats renders as a halo the planet does not have."""
    spacing = (4.0 * np.pi * radius * radius / max(n, 1)) ** 0.5
    return float(cover * spacing)


def fibonacci_sphere(n: int, jitter: float = 0.0, seed: int = 0) -> np.ndarray:
    """n unit vectors spread evenly over a sphere (the golden-angle spiral). Deterministic.

    JITTER BREAKS THE LATTICE. The golden-angle spiral is REGULAR, and a regular sampling pattern is
    visible -- zoom in and its arms read as faint curved streaks, which is what makes a smooth
    surface look like a crappy voxel calculation. This displaces each grain TANGENTIALLY (in the
    surface, then renormalised back onto the shell) by a fraction of the mean spacing, turning the
    spiral into blue noise. Tangential ON PURPOSE: radial jitter scatters grains in DEPTH and lets
    the background speckle through between them, which is a worse artifact."""
    i = np.arange(n, dtype=np.float64)
    z = 1.0 - 2.0 * (i + 0.5) / n
    r = np.sqrt(np.clip(1.0 - z * z, 0.0, 1.0))
    th = np.pi * (1.0 + 5.0 ** 0.5) * i
    d = np.stack([r * np.cos(th), r * np.sin(th), z], axis=1)
    if jitter > 0.0:
        rng = np.random.default_rng(seed)
        spacing = 2.0 / np.sqrt(max(n, 1))
        v = rng.normal(0.0, 1.0, (n, 3))
        v -= (v * d).sum(1, keepdims=True) * d                   # into the TANGENT plane
        v /= (np.linalg.norm(v, axis=1, keepdims=True) + 1e-12)
        d = d + v * (jitter * spacing * rng.random((n, 1)) ** 0.5)
        d /= (np.linalg.norm(d, axis=1, keepdims=True) + 1e-12)  # back onto the shell: no depth change
    return d


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
