"""theSeed -- the generated teddy bear, shown so that no side is unobserved.

S0 FRAME (recorded at the engine): "A teddy bear generated from controlled
multi-view AI imagery has no unobserved side." A single still cannot carry
that claim -- a still HAS an unobserved side by construction. So the
membrane's movie is the bear itself, turntabled a half-turn: t=0 is the
front (the anchor view the generator saw), t=1 is the back (the view no
generator ever saw). The blind eye watches two frames of the SAME asset;
if the back were hallucinated void the end frame would not read as the
same bear.

RULE 0 -- stated before the scene was authored:
    STATEMENT : the genbear2 asset (controlled multi-view stills ->
                AnySplat -> refine -> blob-keep) is a closed solid: front
                AND back carry the same fur, colour, and silhouette.
    PREDICTION: a blind eye watching [front, back] reports the same
                animal in both frames -- head up, four limbs, brown fur --
                with no frame reading as hollow, flat, or a different
                object.
    FALSIFIER : the eye reads the back as a different object, a shell, a
                hole, or refuses "same animal" -- the source lane failed
                and the answer is a better generator (SV3D lane), not a
                prettier render.

THE ASSET IS THE PHYSICS. emit() does not synthesise geometry; it loads
the measured artifact `models/genbear2/genbear2_final_engine.splat`
(182,724 splats, packed 32B 3DGS, engine convention) and re-expresses it
in the membrane buffer layout. Two derivations, no chosen numbers:
  - grain size = median nearest-neighbour spacing of the cloud (the
    inter-grain distance IS the tiling pitch; smaller leaves voids,
    larger double-covers).
  - opacity cut at alpha >= 0.5: the 7-float grain path cannot blend,
    so carrying a sub-half-opacity splat as an opaque grain FABRICATES
    matter the asset does not claim. Half-opacity is the honest cut.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parents[1]                       # story/theSeed -> repo root
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

SPLAT_PATH = _ROOT / "models" / "genbear2" / "genbear2_final_engine.splat"

# ── buffer layout (ParticleEngine.core.COL) ──────────────────────────
NCOLS = 28
PX, PY, PZ = 0, 1, 2
TYPE = 11
CR, CG, CB, ALPHA = 16, 17, 18, 19
SIZE = 20

_CACHE_BUF: np.ndarray | None = None


def _decode() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Packed 32B 3DGS -> (pos, rgb, alpha). NO SPLAT_ORIENT: this export was
    already rotated into the engine's frame (orient_splat.py --ry -90)."""
    raw = np.fromfile(SPLAT_PATH, dtype=np.uint8)
    n = len(raw) // 32
    rec = raw[: n * 32].reshape(n, 32)
    pos = rec[:, 0:12].view(np.float32).reshape(n, 3).astype(np.float64)
    rgba = rec[:, 24:28].astype(np.float32) / 255.0
    return pos, rgba[:, 0:3], rgba[:, 3]


def _base_buffer() -> np.ndarray:
    """The settled asset as a 28-col grain buffer, Z-up (membrane convention).

    The asset file is Y-up (unit-normalised height on Y); the membrane scene
    convention (and the C++ camera framing) is Z-up, so positions map
    (x, y, z) -> (x, -z, y): a -90 deg rotation about X.
    """
    global _CACHE_BUF
    if _CACHE_BUF is not None:
        return _CACHE_BUF
    pos, rgb, alpha = _decode()
    keep = alpha >= 0.5
    pos, rgb = pos[keep], rgb[keep]

    # grain pitch from the cloud's own spacing (derived, not chosen)
    sub = pos[:: max(1, len(pos) // 4000)]
    d = np.linalg.norm(sub[None, :, :] - sub[:, None, :], axis=2)
    d[d == 0.0] = np.inf
    pitch = float(np.median(d.min(axis=1)))

    n = len(pos)
    buf = np.zeros((n, NCOLS), dtype=np.float32)
    buf[:, PX] = pos[:, 0]
    buf[:, PY] = -pos[:, 2]
    buf[:, PZ] = pos[:, 1]
    buf[:, TYPE] = 3.0
    buf[:, CR] = rgb[:, 0]
    buf[:, CG] = rgb[:, 1]
    buf[:, CB] = rgb[:, 2]
    buf[:, ALPHA] = 1.0
    buf[:, SIZE] = pitch
    _CACHE_BUF = buf
    return buf


def _ground(z_floor: float, radius: float) -> np.ndarray:
    """A fixed dark slab under the bear's feet -- the REFERENCE FRAME.

    The blind eye watched the bare rotation and read "tumbling end over end IN THE AIR"
    (2026-08-19, twice): with no static reference, a yaw turntable is visually ambiguous
    with a tumble. A ground the bear rotates ABOVE (never WITH) makes the inspection
    unambiguous -- the same fix class as theVerbs' "a change a blind eye cannot miss":
    the failure named it, the scene answers it."""
    n_g = 900
    rng = np.random.default_rng(7)
    th = rng.random(n_g) * 2.0 * np.pi
    rr = radius * np.sqrt(rng.random(n_g))
    g = np.zeros((n_g, NCOLS), dtype=np.float32)
    g[:, PX] = rr * np.cos(th)
    g[:, PY] = rr * np.sin(th)
    g[:, PZ] = z_floor
    g[:, TYPE] = 3.0
    g[:, ALPHA] = 1.0
    g[:, SIZE] = radius * 0.06
    g[:, CR], g[:, CG], g[:, CB] = 0.16, 0.15, 0.14
    return g


def emit(nums: dict, t: float) -> np.ndarray:
    """The bear, turntabled: t=0 front (the anchored view), t=1 back.

    Rotation is a half-turn about the scene's up axis (+Z), applied to the
    settled buffer. The GROUND does not rotate -- it is the fixed world the
    bear turns within. begin and end are the SAME grains -- only the viewing
    side changes, which is exactly the claim on trial.
    """
    buf = _base_buffer().copy()
    ang = np.pi * float(np.clip(t, 0.0, 1.0))
    if ang != 0.0:
        c, s = np.cos(ang), np.sin(ang)
        x = buf[:, PX].copy()
        y = buf[:, PY].copy()
        buf[:, PX] = c * x - s * y
        buf[:, PY] = s * x + c * y
    z_floor = float(_base_buffer()[:, PZ].min()) - 0.02
    r_xy = float(np.abs(_base_buffer()[:, PX:PY + 1]).max()) * 1.5
    return np.concatenate([buf, _ground(z_floor, r_xy)], axis=0)
