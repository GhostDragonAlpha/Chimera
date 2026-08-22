#!/usr/bin/env python
"""bind_bear.py -- THE TRANSFORMER BIND (operator method, 2026-08-21).

Start with the ORIGINAL donor bear (all splats, fibers untouched). Fit the CAD
parts (cad_core.PRIMS) to the INNER surface of the splat shell. Bind every
splat to its nearest part, locked in the part's frame. Suck the shell a tiny
bit inward (compression clamp: anything past the outer membrane band is pulled
onto it -- floaters die, everything else keeps its EXACT relative position, so
the shape is preserved). Then pose: the bear is a transformer -- legs rotate at
the hips and the bear STANDS UP looking like the same bear. The butt/back of
the legs were never scanned (sitting contact) -- they will be missing in the
standing pose BY DESIGN; those holes get quilt-sprayed later (quilt.py).

FALSIFIER: the rebound (identity pose) must look identical to the donor.

  .venv-gs/Scripts/python.exe tools/bind_bear.py

Outputs: _qualify/bear_rebound.splat  (original pose -- must equal the donor)
         _qualify/bear_standing.splat (legs down, arms drooped, on its feet)
         models/littlebear/bind_map.npz (splat idx -> part, for the filler pass)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from cad_core import PRIMS, save_splat_raw  # noqa: E402

DONOR = ROOT / "models/littlebear/donor.splat"
QDIR = ROOT / "models/triposplat/static/viewer/_qualify"
BAND = 0.015            # membrane band reference (pile depth scale)
OUTER_HARD = 0.050      # only TRUE outliers (beyond 50mm: 460 splats) get pulled
BLEND = 0.025           # lattice morph: parts within d_min+25mm share the splat
GROUND_MARGIN = 0.05    # bottom 5% of Y: contact band, dropped in STANDING only

# standing pose: (group, pivot point, rotation axis, degrees)
LEG_DEG = 85.0          # sitting legs forward -> standing legs down (about X)
ARM_DEG = 25.0          # hug arms -> slight droop (about Z, mirrored)


def load_donor() -> np.ndarray:
    """Raw .splat bytes -> (n,14) CANONICAL frame (the viewer's orient=0 frame).
    Never cpp_bridge (the frame trap): raw bytes ARE +Y up, face +Z."""
    b = np.fromfile(DONOR, dtype=np.uint8)
    n = b.size // 32
    a = b[: n * 32].reshape(n, 32)
    buf = np.zeros((n, 14))
    buf[:, 0:3] = a[:, 0:12].copy().view(np.float32).reshape(n, 3)
    buf[:, 7:10] = a[:, 12:24].copy().view(np.float32).reshape(n, 3)
    buf[:, 3:6] = a[:, 24:27].astype(np.float64) / 255.0
    buf[:, 6] = a[:, 27].astype(np.float64) / 255.0
    rot = (a[:, 28:32].astype(np.float64) - 128.0) / 128.0
    buf[:, 10:14] = rot / np.linalg.norm(rot, axis=1, keepdims=True)
    return buf


def part_sdf(p: np.ndarray, prim: dict) -> np.ndarray:
    """Approximate SIGNED distance to the primitive surface (inside < 0)."""
    if prim["kind"] == "ell":
        c = np.asarray(prim["c"])
        r = np.asarray(prim["r"])
        k = np.linalg.norm((p - c) / r, axis=1)
        return (k - 1.0) * (r.min() + r.max()) / 2
    a = np.asarray(prim["a"])
    b = np.asarray(prim["b"])
    ab = b - a
    t = np.clip(((p - a) @ ab) / (ab @ ab), 0, 1)
    return np.linalg.norm(p - (a + t[:, None] * ab), axis=1) - prim["rad"]


def assign_compress_weights(buf: np.ndarray):
    """Nearest part per splat + LATTICE weights + true-outlier clamp only.

    The shell keeps its natural depth (p75 = 18mm -- that IS the fur). Only
    splats past OUTER_HARD from every part (static/floaters) are pulled in.
    Weights: parts within BLEND of the nearest share the splat, so posing
    MORPHS the lattice instead of splitting it (the neck-fissure fix)."""
    pos = buf[:, 0:3]
    d = np.stack([part_sdf(pos, p) for p in PRIMS], axis=1)
    part = d.argmin(1)
    dmin = d[np.arange(len(pos)), part]
    cut = dmin + BLEND
    w = np.clip((cut[:, None] - d) / BLEND, 0, None) ** 2
    w /= w.sum(1, keepdims=True)
    out = buf.copy()
    over = dmin > OUTER_HARD
    for i, prim in enumerate(PRIMS):
        m = (part == i) & over
        if not m.any():
            continue
        po = pos[m]
        if prim["kind"] == "ell":
            c = np.asarray(prim["c"])
            r = np.asarray(prim["r"])
            loc = po - c
            k = np.linalg.norm(loc / r, axis=1)
            kmax = 1.0 + OUTER_HARD / ((r.min() + r.max()) / 2)
            po = c + loc * (kmax / k)[:, None]
        else:
            a = np.asarray(prim["a"])
            b = np.asarray(prim["b"])
            ab = b - a
            t = np.clip(((po - a) @ ab) / (ab @ ab), 0, 1)
            nrm = po - (a + t[:, None] * ab)
            nrm /= np.linalg.norm(nrm, axis=1, keepdims=True)
            po = a + t[:, None] * ab + nrm * (prim["rad"] + OUTER_HARD)
        out[m, 0:3] = po
    print(f"bind: {len(buf)} splats -> {len(PRIMS)} parts; "
          f"{int(over.sum())} true outliers pulled to {OUTER_HARD*1000:.0f}mm "
          f"(shell depth untouched); lattice blend window {BLEND*1000:.0f}mm")
    for i, prim in enumerate(PRIMS):
        print(f"  {prim['name']:14s} {(part == i).sum():7d}")
    return out, part, w


def quat_mul(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    w1, x1, y1, z1 = a.T
    w2, x2, y2, z2 = b.T
    return np.stack([w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
                     w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
                     w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
                     w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2], axis=1)


def pose(buf: np.ndarray, part: np.ndarray, w: np.ndarray, standing: bool) -> np.ndarray:
    """LATTICE MORPH: each splat moves by the WEIGHTED blend of its parts'
    transforms (positions blend linearly, quats nlerp) -- joints deform
    continuously, no fissure can open between parts."""
    out = buf.copy()
    if standing:
        y0, y1 = buf[:, 1].min(), buf[:, 1].max()
        keep = buf[:, 1] > (y0 + GROUND_MARGIN * (y1 - y0))  # contact band stays behind
        specs = []
        for g, deg, axis in (("leg_L", LEG_DEG, (1, 0, 0)), ("leg_R", LEG_DEG, (1, 0, 0)),
                             ("arm_L", -ARM_DEG, (0, 0, 1)), ("arm_R", ARM_DEG, (0, 0, 1))):
            pivot = next(np.asarray(p["a"]) for p in PRIMS
                         if p["group"] == g and p["kind"] == "cap")
            specs.append((g, pivot, np.asarray(axis, float), np.radians(deg)))
        for g, pivot, axis, ang in specs:
            idx = [i for i, p in enumerate(PRIMS) if p["group"] == g]
            wg = w[:, idx].sum(1)                        # this group's share
            m = (wg > 1e-6) & keep
            if not m.any():
                continue
            q = np.array([np.cos(ang / 2), *(np.sin(ang / 2) * axis)])
            rel = out[m, 0:3] - pivot
            x, y, z = rel.T
            qw, qx, qy, qz = q
            uvx, uvy, uvz = qy * z - qz * y, qz * x - qx * z, qx * y - qy * x
            uuvx = qy * uvz - qz * uvy
            uuvy = qz * uvx - qx * uvz
            uuvz = qx * uvy - qy * uvx
            rotated = pivot + rel + 2 * (qw * np.stack([uvx, uvy, uvz], 1)
                                         + np.stack([uuvx, uuvy, uuvz], 1))
            delta = rotated - out[m, 0:3]
            out[m, 0:3] += wg[m, None] * delta           # the MORPH: partial moves
            rotated_q = quat_mul(np.broadcast_to(q, (m.sum(), 4)), out[m, 10:14])
            base = out[m, 10:14]
            blended = base + wg[m, None] * (rotated_q - base)  # nlerp
            out[m, 10:14] = blended / np.linalg.norm(blended, axis=1, keepdims=True)
        out = out[keep]
        part = part[keep]
        # stand on the feet: lowest foot splat touches the donor's ground plane
        foot_idx = [i for i, p in enumerate(PRIMS) if p["name"].startswith("foot")]
        ground = buf[:, 1].min()
        out[:, 1] -= out[np.isin(part, foot_idx), 1].min() - ground
    return out


def main() -> int:
    buf = load_donor()
    bound, part, w = assign_compress_weights(buf)
    save_splat_raw(QDIR / "bear_rebound.splat", bound)
    print(f"WROTE bear_rebound.splat ({len(bound)} splats) -- identity pose, "
          "FALSIFIER: must look identical to the donor")
    standing = pose(bound, part, w, standing=True)
    save_splat_raw(QDIR / "bear_standing.splat", standing)
    print(f"WROTE bear_standing.splat ({len(standing)} splats) -- legs {LEG_DEG}deg, "
          f"arms {ARM_DEG}deg, on its feet")
    np.savez(ROOT / "models/littlebear/bind_map.npz", part=part, weights=w.astype(np.float32))
    return 0


if __name__ == "__main__":
    sys.exit(main())
