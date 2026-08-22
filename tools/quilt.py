#!/usr/bin/env python
"""quilt.py -- the SPLAT QUILTING kernel: rearrange REAL material tiles onto a part.

The method (operator, 2026-08-21): never invent fiber -- take the eye-qualified
REAL tiles cut from the donor (models/littlebear/corpus/*_qualified.npz) and
re-lay them on the CAD armature so the visible surface IS the original object's
material. Seamless = overlap + feather + free spin; bendable = splats are
POINTS, so a bend is a per-splat rotation field and nothing ever stretches.

Kernel facts:
  * tiles are (2048,14) rows in patch frame [u,v,h, rgb, alpha, log_s*3, quat*4],
    patch zero = the tile's p5 backing floor, half-window 0.025 m.
  * cylinder wrap is EXACT: (u,v) -> (angle about the axis, axial offset),
    h along the radial normal. The per-splat local frame F = [tangential, axial,
    radial] is right-handed (checked: t x w = n) and the tile quats are
    conjugated by F per-splat (each splat has its own angle).
  * feathering: keep-probability ramps down near tile borders so overlapping
    tiles sum to ~constant density -- no shingle lines.
  * bend(): a smoothstep rotation field about the joint; positions AND quats
    rotate together. The outside of a bend stretches tangentially -- if it ever
    shows, drop extra tiles in the stretch zone (operator's rule).

First proof (this file's main): one measured forearm capsule tiled with real
fur, straight vs bent 40 deg at the elbow, darker-shade core underneath.

  .venv-gs/Scripts/python.exe tools/quilt.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from cad_core import FUR, capsule, save_splat_raw  # noqa: E402

CORPUS = ROOT / "models/littlebear/corpus/fur_qualified.npz"
OUT = ROOT / "models/triposplat/static/viewer/_qualify/quilt_arm.splat"
HALF = 0.025          # tile half-window the corpus was cut with
OVERLAP = 0.55        # anchor spacing = 2*HALF*OVERLAP (~45% overlap: density)
LAYERS = 3            # tiles per anchor: the corpus was SUBSAMPLED to 2048 splats
                      # (cut_patches N_PTS) -- real pile is ~4x denser; layering
                      # independent tiles with micro-jitter restores it


# --- quaternion helpers (w,x,y,z), local so quilt never imports cpp_bridge ---
def quat_mul(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    w1, x1, y1, z1 = a.T
    w2, x2, y2, z2 = b.T
    return np.stack([w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
                     w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
                     w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
                     w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2], axis=1)


def mat_to_quat(m: np.ndarray) -> np.ndarray:
    """(n,3,3) rotation matrices -> (n,4) quats (w,x,y,z)."""
    t = m[:, 0, 0] + m[:, 1, 1] + m[:, 2, 2]
    q = np.zeros((len(m), 4))
    big = t > 0
    s = np.sqrt(np.maximum(t[big] + 1, 1e-12)) * 2
    q[big] = np.stack([0.25 * s, (m[big, 2, 1] - m[big, 1, 2]) / s,
                       (m[big, 0, 2] - m[big, 2, 0]) / s,
                       (m[big, 1, 0] - m[big, 0, 1]) / s], axis=1)
    for i in np.where(~big)[0]:  # rare path: pick the largest diagonal
        j = int(np.argmax([m[i, 0, 0], m[i, 1, 1], m[i, 2, 2]]))
        k, l = (j + 1) % 3, (j + 2) % 3
        s = np.sqrt(max(m[i, j, j] - m[i, k, k] - m[i, l, l] + 1, 1e-12)) * 2
        q[i, 0] = (m[i, l, k] - m[i, k, l]) / s
        q[i, j + 1] = 0.25 * s
        q[i, k + 1] = (m[i, k, j] + m[i, j, k]) / s
        q[i, l + 1] = (m[i, l, j] + m[i, j, l]) / s
    return q / np.linalg.norm(q, axis=1, keepdims=True)


def axis_angle(axis: np.ndarray, ang: np.ndarray) -> np.ndarray:
    s = np.sin(ang / 2)
    return np.stack([np.cos(ang / 2), axis[0] * s, axis[1] * s, axis[2] * s], axis=1)


def load_tiles(path=CORPUS):
    d = np.load(path)
    return d["patches"].astype(np.float64), d["weights"] / d["weights"].sum()


def wrap_tile_cylinder(tile: np.ndarray, anchor_t: float, anchor_th: float,
                       spin: float, radius: float, c: np.ndarray,
                       w: np.ndarray, u1: np.ndarray, u2: np.ndarray,
                       rng: np.random.Generator,
                       jitter: tuple[float, float] = (0.0, 0.0)) -> np.ndarray:
    """One REAL tile wrapped exactly onto the cylinder (axis w through c).

    u -> tangential (angle = anchor_th + spin + u/radius), v -> axial,
    h -> radial out. Border-feathered. Returns world-frame 14-float rows."""
    t = tile[tile[:, 6] > 0]                       # drop padding rows
    e = np.maximum(np.abs(t[:, 0]), np.abs(t[:, 1])) / HALF
    keep_p = np.where(e <= 0.6, 1.0, 1.0 - 0.6 * np.clip((e - 0.6) / 0.4, 0, 1))
    t = t[rng.random(len(t)) < keep_p]
    if len(t) == 0:
        return np.zeros((0, 14))
    th = anchor_th + spin + (t[:, 0] + jitter[0]) / radius
    nrm = np.cos(th)[:, None] * u1 + np.sin(th)[:, None] * u2   # radial
    tan = -np.sin(th)[:, None] * u1 + np.cos(th)[:, None] * u2  # tangential
    pos = c + (anchor_t + t[:, 1] + jitter[1])[:, None] * w + (radius + t[:, 2])[:, None] * nrm
    F = np.stack([tan, np.broadcast_to(w, tan.shape), nrm], axis=2)  # (n,3,3) cols
    q = quat_mul(mat_to_quat(F), t[:, 10:14])
    out = np.zeros((len(t), 14))
    out[:, 0:3] = pos
    out[:, 3:6] = t[:, 3:6]
    out[:, 6] = t[:, 6]
    out[:, 7:10] = np.exp(t[:, 7:10])              # log scales -> linear
    out[:, 10:14] = q
    return out


def quilt_cylinder(tiles, probs, a, b, radius, seed=0) -> np.ndarray:
    """Tile the full cylinder surface a->b with real tiles, 30% overlap."""
    rng = np.random.default_rng(seed)
    a, b = np.asarray(a, float), np.asarray(b, float)
    w = b - a
    L = np.linalg.norm(w)
    w /= L
    u1 = np.cross(w, [0, 0, 1.0])
    if np.linalg.norm(u1) < 1e-6:
        u1 = np.cross(w, [0, 1.0, 0.0])
    u1 /= np.linalg.norm(u1)
    u2 = np.cross(w, u1)
    step = 2 * HALF * OVERLAP
    rows = []
    for t_a in np.arange(-step / 2, L + step, step):      # overhang both ends
        for th_a in np.arange(0, 2 * np.pi, step / radius):
            for _ in range(LAYERS):
                k = rng.choice(len(tiles), p=probs)
                jit = (rng.uniform(-0.003, 0.003), rng.uniform(-0.003, 0.003))
                rows.append(wrap_tile_cylinder(tiles[k], t_a, th_a,
                                               rng.random() * 2 * np.pi,
                                               radius, a, w, u1, u2, rng, jit))
    return np.concatenate(rows), w, L


def bend(buf: np.ndarray, joint: np.ndarray, axis: np.ndarray, theta_max: float,
         t: np.ndarray, t_joint: float, blend: float) -> np.ndarray:
    """Per-splat smoothstep rotation field: the seamless bend. Positions and
    quats rotate together; nothing stretches."""
    s = np.clip((t - t_joint) / blend, 0, 1)
    ang = theta_max * (3 * s**2 - 2 * s**3)
    q = axis_angle(np.asarray(axis, float), ang)
    out = buf.copy()
    rel = out[:, 0:3] - joint
    x, y, z = rel.T
    qx, qy, qz, qw = q[:, 1], q[:, 2], q[:, 3], q[:, 0]
    # rotate rel by q (vectorized quaternion rotation)
    uvx = qy * z - qz * y
    uvy = qz * x - qx * z
    uvz = qx * y - qy * x
    uuvx = qy * uvz - qz * uvy
    uuvy = qz * uvx - qx * uvz
    uuvz = qx * uvy - qy * uvx
    rot = rel + 2 * (qw[:, None] * np.stack([uvx, uvy, uvz], 1)
                     + np.stack([uuvx, uuvy, uuvz], 1))
    out[:, 0:3] = joint + rot
    out[:, 10:14] = quat_mul(q, out[:, 10:14])
    return out


def main() -> int:
    tiles, probs = load_tiles()
    print(f"tiles: {len(tiles)} qualified fur patches")
    # measured forearm (cad_core.py): shoulder->wrist, r=0.024; scene CENTERED
    # on the origin (the viewer orbits the origin -- offset scenes break framing)
    a0 = np.array([-0.034, 0.0, 0.0])
    b0 = np.array([0.034, -0.008, 0.0])
    r = 0.024
    scenes = []
    for i, (zi, theta) in enumerate(((-0.055, 0.0), (0.055, np.radians(40)))):
        a, b = a0 + [0, 0, zi], b0 + [0, 0, zi]
        fur, w, L = quilt_cylinder(tiles, probs, a, b, r, seed=i)
        core = capsule(a, b, r - 0.0005, tuple(c_ * 0.5 for c_ in FUR))  # gaps read as DEPTH
        t_fur = (fur[:, 0:3] - a) @ w
        t_core = (core[:, 0:3] - a) @ w
        if theta:
            joint = a + w * (0.5 * L)
            fur = bend(fur, joint, [0, 0, 1.0], theta, t_fur, 0.5 * L, 0.02)
            core = bend(core, joint, [0, 0, 1.0], theta, t_core, 0.5 * L, 0.02)
        scenes += [fur, core]
        print(f"arm z={zi:+.2f} bend={np.degrees(theta):4.0f}deg: "
              f"{len(fur)} fur + {len(core)} core splats")
    scene = np.concatenate(scenes).astype(np.float32)
    save_splat_raw(OUT, scene)
    print(f"WROTE {OUT.name}: {len(scene)} splats (straight + bent 40deg)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
