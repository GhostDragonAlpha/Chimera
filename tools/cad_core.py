#!/usr/bin/env python
"""cad_core.py -- the CAD INNER CORE for littlebear: measured primitives, darker shades.

Milestone A (operator-authorized 2026-08-21): fitted CAD core ALONE, no fur --
proves proportions before any fiber exists.

Every constant below is MEASURED from models/littlebear/donor.splat raw bytes
(canonical frame: +Y up, face +Z, 0.3 m bear) -- the 2026-08-21 probe printed
per-part p5/median/p95 extents; cores are then SYMMETRIZED L/R and generalized
(the sitting bear's ground-flattened butt is rounded back out; the head is
embedded into the torso at the neck -- connection overshoot is deliberate).

Colors: each part is the DARKER SHADE of its material (operator rule: the core
must read as depth through any gap between fibers, never as a hole):
  fur ~ (0.71,0.60,0.45) -> x0.45 ; sweater green -> dark green ; cream -> dim ;
  eyes/nose -> near-black. Cores are OPAQUE (alpha 1) small isotropic splats.

  .venv-gs/Scripts/python.exe tools/cad_core.py

Output: models/triposplat/static/viewer/_qualify/cad_core.splat (orbitable).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent

OUT = ROOT / "models/triposplat/static/viewer/_qualify/cad_core.splat"
SPACING = 0.0009  # m between core splats on a surface (~1 mm: solid at bear scale)


def save_splat_raw(path: Path, buf: np.ndarray) -> None:
    """Pack (n,14) CANONICAL-frame rows -> 32-byte .splat with NO frame change.

    FRAME TRAP (earned twice, 2026-08-21): viewer.html at orient=0 shows raw
    bytes AS-IS (the donor proves it: raw bytes = +Y up, face +Z, renders
    upright). cpp_bridge.save_splat pre-applies SPLAT_ORIENT for the ENGINE's
    load_splat convention -- feeding it canonical-frame content bakes in a
    rotation (S is an involution: flip Y, swap X/Z). It went unnoticed on flat
    fur tiles; a whole bear exposes it instantly. Viewer-bound canonical
    content must be packed RAW."""
    buf = np.asarray(buf, dtype=np.float64)
    dt = np.dtype([("pos", "<f4", 3), ("scale", "<f4", 3), ("rgba", "u1", 4), ("rot", "u1", 4)])
    arr = np.zeros(len(buf), dtype=dt)
    arr["pos"] = buf[:, 0:3].astype(np.float32)
    arr["scale"] = buf[:, 7:10].astype(np.float32)
    arr["rgba"][:, 0:3] = (np.clip(buf[:, 3:6], 0, 1) * 255.0).round().astype(np.uint8)
    arr["rgba"][:, 3] = (np.clip(buf[:, 6], 0, 1) * 255.0).round().astype(np.uint8)
    arr["rot"] = (np.clip(buf[:, 10:14], -1, 1) * 128.0 + 128.0).round().astype(np.uint8)
    path.write_bytes(arr.tobytes())

# measured material shades (darkened) -----------------------------------------
FUR = (0.32, 0.27, 0.20)      # x0.45 of the fur_brown GMM mean (0.71,0.60,0.45)
SWEATER = (0.03, 0.16, 0.06)  # dark knit green
CREAM = (0.50, 0.47, 0.40)    # dim snout/soles
DARK = (0.02, 0.02, 0.02)     # eyes + nose


def _dirs(n: int, rng: np.random.Generator) -> np.ndarray:
    d = rng.normal(size=(n, 3))
    return d / np.linalg.norm(d, axis=1, keepdims=True)


def ellipsoid(c, r, color, n=None, clip=None) -> np.ndarray:
    """Shell of an ellipsoid. clip: optional fn(world_pts)->bool keep-mask."""
    area = 4 * np.pi * (np.mean(r) ** 2)
    n = n or int(area / SPACING**2)
    rng = np.random.default_rng(0)
    pts = c + _dirs(n, rng) * np.asarray(r)
    if clip is not None:
        pts = pts[clip(pts)]
    return _splat_rows(pts, color)


def capsule(a, b, radius, color) -> np.ndarray:
    """Capsule (cylinder + hemisphere caps) from a to b -- arms and legs."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    axis = b - a
    L = np.linalg.norm(axis)
    w = axis / L
    u = np.cross(w, [0, 0, 1.0])
    u /= np.linalg.norm(u)
    v = np.cross(w, u)
    area = 2 * np.pi * radius * L + 4 * np.pi * radius**2
    n = int(area / SPACING**2)
    rng = np.random.default_rng(0)
    t = rng.random(n)
    th = rng.random(n) * 2 * np.pi
    side = t < (L / (L + radius))  # most points on the cylinder wall
    pts = np.empty((n, 3))
    ns = side.sum()
    pts[side] = (a + (t[side] * L)[:, None] * w
                 + radius * (np.cos(th[side])[:, None] * u + np.sin(th[side])[:, None] * v))
    d = _dirs(n - ns, rng)
    cap = np.sign(d @ w)  # round half to each end
    pts[~side] = np.where((cap > 0)[:, None], b, a) + radius * d
    return _splat_rows(pts, color)


def _splat_rows(pts: np.ndarray, color) -> np.ndarray:
    n = len(pts)
    b = np.zeros((n, 14))
    b[:, 0:3] = pts
    b[:, 3:6] = color
    b[:, 6] = 1.0                       # opaque
    b[:, 7:10] = SPACING * 0.6          # isotropic, slightly overlapping
    b[:, 10] = 1.0                      # identity quat (w,x,y,z)
    return b


# --- parts: MEASURED constants (probe 2026-08-21), symmetrized, generalized ---
# PRIMS is the single source of truth: build() shells it for the viewer, and
# tools/bind_bear.py binds donor splats to it (nearest primitive) and poses it.
# kind "ell": c, r, optional clip ("neck" = keep y < 0.030).
# kind "cap": a, b, rad.
# group = pose chain: torso is root; limbs rotate about their pivot (a end).
PRIMS = [
    # torso+seat: cloud spans y -0.135..+0.04, x +/-0.085, z -0.105..+0.10;
    # butt generalized round (not ground-flattened); back extended to -0.095
    # (the back shell was 2-4cm off the primitive -> the neck fissure)
    dict(name="torso", kind="ell", c=(0, -0.050, 0.000), r=(0.072, 0.090, 0.095), color=FUR, group="torso"),
    # head: covers the NECK (bottom y 0.026) and the head-back jut (z -0.105) --
    # the shell must stay within the membrane band of SOME primitive everywhere
    dict(name="head", kind="ell", c=(0, 0.088, -0.030), r=(0.075, 0.062, 0.075), color=FUR, group="torso"),
    # ears: symmetrized ear_L/ear_R -> |x|~0.058, top y~0.144; root inside head
    dict(name="ear_L", kind="ell", c=(0.058, 0.128, -0.032), r=(0.024, 0.022, 0.022), color=FUR, group="torso"),
    dict(name="ear_R", kind="ell", c=(-0.058, 0.128, -0.032), r=(0.024, 0.022, 0.022), color=FUR, group="torso"),
    # muzzle/cheek mass: face-front fibers z 0..0.056 at y 0.03..0.10
    dict(name="muzzle", kind="ell", c=(0, 0.055, 0.005), r=(0.045, 0.035, 0.035), color=CREAM, group="torso"),
    # eyes: eye_L (+0.037,0.067,0.025) / eye_R (-0.022,0.076,0.031) -> sym
    dict(name="eye_L", kind="ell", c=(0.030, 0.073, 0.024), r=(0.009, 0.009, 0.009), color=DARK, group="torso"),
    dict(name="eye_R", kind="ell", c=(-0.030, 0.073, 0.024), r=(0.009, 0.009, 0.009), color=DARK, group="torso"),
    # nose: dark-face mass below the eyes
    dict(name="nose", kind="ell", c=(0, 0.045, 0.038), r=(0.011, 0.008, 0.008), color=DARK, group="torso"),
    # arms: shoulder (torso side, y~0) -> paw (|x|~0.12, y~-0.008); paws fwd
    dict(name="arm_L", kind="cap", a=(0.050, 0.000, -0.005), b=(0.118, -0.008, 0.0), rad=0.024, color=FUR, group="arm_L"),
    dict(name="arm_R", kind="cap", a=(-0.050, 0.000, -0.005), b=(-0.118, -0.008, 0.0), rad=0.024, color=FUR, group="arm_R"),
    dict(name="paw_L", kind="ell", c=(0.126, -0.008, 0.0), r=(0.022, 0.026, 0.028), color=FUR, group="arm_L"),
    dict(name="paw_R", kind="ell", c=(-0.126, -0.008, 0.0), r=(0.022, 0.026, 0.028), color=FUR, group="arm_R"),
    # legs: hip -> ankle forward (sitting pose, feet at z~0.09); feet cream soles
    dict(name="leg_L", kind="cap", a=(0.048, -0.095, 0.010), b=(0.058, -0.098, 0.075), rad=0.030, color=FUR, group="leg_L"),
    dict(name="leg_R", kind="cap", a=(-0.048, -0.095, 0.010), b=(-0.058, -0.098, 0.075), rad=0.030, color=FUR, group="leg_R"),
    # feet get a FLAT SOLE (sole=0.8: clip at y = c_y - 0.8*r_y, capped flat).
    # Derived (kernel_stand RUN 3 record): a curved/point contact under a body
    # whose COM rides 190 mm up is an inverted pendulum -- statically
    # unstable for ANY damping. Passive standing needs a flat patch holding
    # the COM projection with margin. Clip at 0.8 -> flat half-widths
    # 0.6*rx=16.8 mm, 0.6*rz=19.2 mm -> 33.6 x 38.4 mm patch per foot.
    # Foot center SOLVED by the stance solver over the real packet cloud
    # (pose = hip flexion 90 deg + ankle dorsiflexion 90 deg; constraints:
    # sole is the ONLY contact surface -- ankle pole clears it by >=5 mm,
    # and the COM projection sits >=16.6 mm = 190*tan(5deg) inside the
    # patch both directions; additionally the patch CENTER must sit under
    # the COM line -- uniform wall pressure on a flat sole puts the force
    # centroid at the patch centroid, and any offset is a permanent
    # tipping moment (RUN 3 measure: 24.6 N.m per meter of offset)).
    # Solved: y=-0.1138, z=+0.0638. Measured on the posed cloud: patch
    # z [-25.6,+17.0] mm vs COM -4.2 mm -> symmetric margins +21.4/+21.2 mm,
    # zero-tilt torque residual 0.02 N.m (packet-sampling noise scale).
    dict(name="foot_L", kind="ell", c=(0.058, -0.1138, 0.0638), r=(0.028, 0.024, 0.032), color=CREAM, group="leg_L", sole=0.8),
    dict(name="foot_R", kind="ell", c=(-0.058, -0.1138, 0.0638), r=(0.028, 0.024, 0.032), color=CREAM, group="leg_R", sole=0.8),
    # sweater: torso shell +6mm clipped below the neck + sleeves over arm cores
    dict(name="sweater_body", kind="ell", c=(0, -0.050, 0.000), r=(0.078, 0.096, 0.101), color=SWEATER, clip="neck", group="torso"),
    dict(name="sleeve_L", kind="cap", a=(0.050, 0.000, -0.005), b=(0.095, -0.006, -0.002), rad=0.029, color=SWEATER, group="arm_L"),
    dict(name="sleeve_R", kind="cap", a=(-0.050, 0.000, -0.005), b=(-0.095, -0.006, -0.002), rad=0.029, color=SWEATER, group="arm_R"),
]


def build() -> list[tuple[str, np.ndarray]]:
    parts = []
    for p in PRIMS:
        if p["kind"] == "ell":
            clip = (lambda q: q[:, 1] < 0.030) if p.get("clip") == "neck" else None
            parts.append((p["name"], ellipsoid(p["c"], p["r"], p["color"], clip=clip)))
        else:
            parts.append((p["name"], capsule(p["a"], p["b"], p["rad"], p["color"])))
    return parts


def main() -> int:
    parts = build()
    rows = []
    for name, b in parts:
        print(f"{name:14s} {len(b):6d} splats")
        rows.append(b.astype(np.float32))
    core = np.concatenate(rows)
    save_splat_raw(OUT, core)
    print(f"WROTE {OUT.name}: {len(core)} splats, {len(parts)} parts")
    return 0


if __name__ == "__main__":
    sys.exit(main())
