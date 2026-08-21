"""littlebear_regions.py -- cut the approved donor into MATERIAL REGIONS.

The rule (operator, 2026-08-21): RGB on a wheel, take angular sections, THEN
cross-reference with the splat pattern itself (aniso separates knit from fur
where hues collide). The statistical distributions per region are the training
targets. Fur is sampled ONLY from head + paws (no clipped regions -- clipping
is noise).

  .venv-gs/Scripts/python.exe tools/littlebear_regions.py

FRAME WARNING (earned 2026-08-21): donor.splat raw bytes ARE the canonical
frame (+Y up, face +Z, height 0.3m) -- orient_splat.py wrote it that way.
cpp_bridge.load_splat applies SPLAT_ORIENT on top, which for THIS file means
loaded = (raw.z, -raw.y, raw.x): an upside-down side-facing frame. An entire
probe cycle was wasted measuring "the head" in loaded space -- it was the LEGS.
This script therefore parses the .splat bytes directly and never calls
cpp_bridge. Positions/scales/colors stay in the frame the viewer renders.

Outputs: models/littlebear/genomes/<region>.npz  (full per-splat attributes)
         models/littlebear/genomes/regions.json  (the region definitions + stats)
         viewer _qualify/regions.splat           (painted verification)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent

DONOR = ROOT / "models/littlebear/donor.splat"
OUTDIR = ROOT / "models/littlebear/genomes"
VERIFY = ROOT / "models/triposplat/static/viewer/_qualify/regions.splat"

# --- region constants, all measured in the RAW canonical frame (2026-08-21) ---
# head: warm mass owns y>0.03 (green vanishes above +0.03); volume spans
# y 0.04..0.15, x +/-0.10, z -0.11..+0.06 -> ellipsoid below.
HEAD_C = np.array([0.0, 0.095, -0.025])
HEAD_R = np.array([0.105, 0.06, 0.10])
# face front: the muzzle/cheeks jut forward of the cranium ellipsoid (at y~0.05,
# z~0.05 they fall outside it) -- a second volume covers them. Above y=0.03 the
# green count is ~zero, so this box is fur-clean.
FACE_FRONT = dict(x=0.085, y=(0.03, 0.10), z=0.0)
# crown cap: cranium + ears above y~0.112 (ears reach |x|~0.10, z -0.09..0.0).
# Up here the cloud is 100% warm fur (green count at y>0.09: 2 splats).
CROWN = dict(x=0.105, y=0.112, z=(-0.115, 0.01))
# back of head: the head-back juts to the cloud's z extreme (-0.111) at mid
# heights, past the ellipsoid's reach. All fur there (green above y=0.03: ~zero).
HEAD_BACK = dict(x=0.10, y=(0.035, 0.115), z=-0.075)
# paws: bare tips at the arm extremes; sleeves are green, paws are warm.
# |x|>0.09 mid-body, EXCLUDING the head ellipsoid (its side edges reach |x|~0.107).
PAW_X_MIN = 0.09
PAW_Y = (-0.04, 0.03)
# sweater: green hue 70-100 saturated, torso band y -0.10..+0.04, outside the head.
SWEATER_Y = (-0.10, 0.04)
# cream: achromatic light (chroma<=0.03, val>0.35) inside the snout/feet boxes only;
# unbounded it claims the face's lit outer fibers and veils the fur.
SNOUT = dict(z=0.04, x=0.05, y=(0.0, 0.10))     # front-center face
FEET = dict(z=0.05, y=-0.06)                    # front-bottom soles
# dark: near-black inside the face box only: eyes + nose (ground shadow is dark too;
# the face box + ground margin keep it out)
FACE = dict(z=0.02, x=0.08, y=(0.0, 0.12))
# GROUND MARGIN (operator, 2026-08-21): the band where the bear touches the ground
# is NEVER data -- contact shadow + static live there. Bottom 5% of the Y range is
# excluded from EVERY region, no exceptions.
GROUND_MARGIN_FRAC = 0.05


def load_raw(path: Path):
    b = np.fromfile(path, dtype=np.uint8)
    n = b.size // 32
    a = b[: n * 32].reshape(n, 32)
    pos = a[:, 0:12].copy().view(np.float32).reshape(n, 3).astype(np.float64)
    scale = a[:, 12:24].copy().view(np.float32).reshape(n, 3).astype(np.float64)
    rgba = a[:, 24:28].astype(np.float64) / 255.0
    return a, pos, scale, rgba


def main() -> int:
    raw, pos, scale, rgba = load_raw(DONOR)
    rgb, alpha = rgba[:, :3], rgba[:, 3]

    mx, mn = rgb.max(1), rgb.min(1)
    d = mx - mn
    sat = np.where(mx > 1e-9, d / np.maximum(mx, 1e-9), 0)
    val = mx
    r, g, b = rgb[:, 0], rgb[:, 1], rgb[:, 2]
    h = np.zeros(len(rgb))
    m = d > 1e-9
    rm, gm, bm = (mx == r) & m, (mx == g) & m, (mx == b) & m
    h[rm] = (60 * ((g - b)[rm] / d[rm])) % 360
    h[gm] = (60 * ((b - r)[gm] / d[gm]) + 120) % 360
    h[bm] = (60 * ((r - g)[bm] / d[bm]) + 240) % 360

    geo = np.cbrt(scale.prod(1))
    aniso = scale.max(1) / np.maximum(scale.min(1), 1e-12)
    ok = (sat > 0.15) & (val > 0.08)

    head_ell = (((pos - HEAD_C) / HEAD_R) ** 2).sum(1) <= 1
    face_front = ((np.abs(pos[:, 0]) < FACE_FRONT["x"]) & (pos[:, 2] > FACE_FRONT["z"])
                  & (pos[:, 1] > FACE_FRONT["y"][0]) & (pos[:, 1] < FACE_FRONT["y"][1]))
    head_ell = head_ell | face_front
    crown = ((pos[:, 1] > CROWN["y"]) & (np.abs(pos[:, 0]) < CROWN["x"])
             & (pos[:, 2] > CROWN["z"][0]) & (pos[:, 2] < CROWN["z"][1]))
    head_ell = head_ell | crown
    head_back = ((pos[:, 2] < HEAD_BACK["z"]) & (np.abs(pos[:, 0]) < HEAD_BACK["x"])
                 & (pos[:, 1] > HEAD_BACK["y"][0]) & (pos[:, 1] < HEAD_BACK["y"][1]))
    head_ell = head_ell | head_back
    paws = (np.abs(pos[:, 0]) > PAW_X_MIN) & (pos[:, 1] > PAW_Y[0]) & (pos[:, 1] < PAW_Y[1]) & ~head_ell
    snout = ((pos[:, 2] > SNOUT["z"]) & (np.abs(pos[:, 0]) < SNOUT["x"])
             & (pos[:, 1] > SNOUT["y"][0]) & (pos[:, 1] < SNOUT["y"][1]))
    feet = (pos[:, 2] > FEET["z"]) & (pos[:, 1] < FEET["y"])
    face = ((pos[:, 2] > FACE["z"]) & (np.abs(pos[:, 0]) < FACE["x"])
            & (pos[:, 1] > FACE["y"][0]) & (pos[:, 1] < FACE["y"][1]))
    y0, y1 = pos[:, 1].min(), pos[:, 1].max()
    above_ground = pos[:, 1] > (y0 + GROUND_MARGIN_FRAC * (y1 - y0))
    print(f"ground margin: y < {y0 + GROUND_MARGIN_FRAC * (y1 - y0):.3f} excluded "
          f"({(~above_ground).sum()} splats never data)")

    regions = {
        # name: (mask, definition prose) -- every mask ANDs the ground margin
        # fur: inside the head ellipsoid EVERYTHING except snout-box and dark-face
        # is fur (washed-out lit tips AND shadowed dark fibers included -- both
        # were the veil); at the paws, warm hue 10-65 only (the sleeves are green).
        "fur": (((head_ell & ~snout & ~((val <= 0.1) & face))
                 | (paws & (h >= 10) & (h < 65) & (d > 0.02))) & above_ground,
                "head = ellipsoid (0,0.095,-0.025)r(0.105,0.06,0.10) + face-front box "
                "(z>0, y 0.03..0.10) + crown cap (y>0.112) + back-of-head (z<-0.075): "
                "everything but snout/eyes; paws |x|>0.09 mid-y outside head: warm 10-65 chroma-gated"),
        "sweater": ((ok & (h >= 70) & (h < 100)
                     & (pos[:, 1] > SWEATER_Y[0]) & (pos[:, 1] < SWEATER_Y[1])
                     & ~head_ell & above_ground),
                    "hue 70-100 saturated, torso band y -0.10..+0.04, outside the head "
                    "-- hue+space, no aniso gate (knit aniso is broad; aniso is a "
                    "training TARGET, not a selector)"),
        "cream": (((d <= 0.03) & (val > 0.35) & (snout | feet) & above_ground),
                  "achromatic light (chroma<=0.03) inside the snout/feet boxes only"),
        "dark": ((val <= 0.1) & face & above_ground,
                 "near-black inside the face box only: eyes + nose"),
    }

    OUTDIR.mkdir(parents=True, exist_ok=True)
    PAINT = {"fur": (255, 38, 0), "sweater": (0, 229, 51), "cream": (255, 255, 255), "dark": (26, 26, 26)}
    meta = {}
    painted = raw.copy()
    painted[:, 27] = 38  # unpainted fades back (alpha 0.15)
    for name, (mask, defn) in regions.items():
        sel = np.where(mask)[0]
        np.savez(OUTDIR / f"{name}.npz",
                 idx=sel, pos=pos[sel], rgb=rgb[sel], alpha=alpha[sel],
                 scale=scale[sel], aniso=aniso[sel], geo=geo[sel],
                 hue=h[sel], sat=sat[sel], val=val[sel])
        meta[name] = {
            "definition": defn,
            "n": int(mask.sum()),
            "color_mean": rgb[mask].mean(0).round(4).tolist() if mask.any() else None,
            "log_size": float(np.log(np.maximum(geo[mask], 1e-12)).mean()) if mask.any() else None,
            "aniso_mean": float(aniso[mask].mean()) if mask.any() else None,
            "opacity_mean": float(alpha[mask].mean()) if mask.any() else None,
        }
        painted[mask, 24:27] = PAINT[name]
        painted[mask, 27] = 255
        print(f"{name:8s} n={mask.sum():6d}  {defn}")

    (OUTDIR / "regions.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    VERIFY.write_bytes(painted.tobytes())
    print(f"genomes -> {OUTDIR}")
    print(f"verification paint -> {VERIFY.name} (unpainted = matched no region, faded)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
