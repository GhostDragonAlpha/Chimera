"""stickfigure.py — MEASURE the object, FIT a symmetric stick figure to it.

THE METHOD (operator directive, 2026-08-18): do not ask the eye to guess joints. MEASURE
the splat cloud's geometry, build a canonical SYMMETRIC stick figure, and PROPORTION it to
the measurements. Every landmark below is a rule over the point distribution — no number is
chosen by taste; each is a percentile, an extremum, a centroid, or a profile feature.

THEORY (Rule 0):
  STATEMENT  — a plush T-pose body is readable from its own point distribution: the neck is
               the width minimum between head and arm-span, the arm axis is the height of
               the extreme-x splats, the crotch is where the center column empties, the legs
               are the two lower lobes, and left == right by symmetry.
  PREDICTION — the fitted joints land on anatomically sensible positions (checked by the
               overlay render: bones run down the middle of limbs, joints at junctions).
  FALSIFIER  — if the overlay shows bones outside the body or joints off their junctions,
               the profile rules are wrong for this asset, not the proportions.

STAGES:
    build    measure + fit -> <out> (skeleton.json: {"joints": {name: [x,y,z]}})
    overlay  render front/back/left/right with joints+bones drawn -> <dir>/overlay_*.png

Usage (from the repo root):
    python ChimeraEngine/native/stickfigure.py build   models/imagegen/tpose2_640.splat --out models/imagegen/tpose2_640_rig/skeleton_sym.json
    python ChimeraEngine/native/stickfigure.py overlay models/imagegen/tpose2_640.splat --skeleton models/imagegen/tpose2_640_rig/skeleton_sym.json
"""
from __future__ import annotations

import argparse
import io
import json
import sys
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

_HERE = Path(__file__).resolve().parent
_CHIMERA_ENGINE = _HERE.parent
if str(_CHIMERA_ENGINE) not in sys.path:
    sys.path.insert(0, str(_CHIMERA_ENGINE))

import cpp_bridge as cb                     # noqa: E402
from active_labeler import project          # noqa: E402  (the engine's exact camera)

ENGINE = "http://localhost:8080"


# ── MEASURE -----------------------------------------------------------------------

def measure(splat_path: str) -> dict:
    """Landmarks from the point distribution. Left/right measured independently here;
    the SYMMETRIZATION happens in fit()."""
    buf = cb.load_splat(splat_path)
    pos = buf[:, 0:3].astype(np.float64)
    mag = np.cbrt(np.maximum(buf[:, 7] * buf[:, 8] * buf[:, 9], 1e-30).astype(np.float64))
    body = mag <= 10.0 * float(np.median(mag))     # drop giant filler splats (see section.py)
    P = pos[body]
    x, y, z = P[:, 0], P[:, 1], P[:, 2]

    y_top, y_bot = np.percentile(y, 99.5), np.percentile(y, 0.5)
    H = y_top - y_bot

    # height profile: 60 bins, width = p95(x)-p05(x) per bin (needs >= 20 splats)
    bins = np.linspace(y_bot, y_top, 61)
    width = np.full(60, np.nan)
    for i in range(60):
        sel = (y >= bins[i]) & (y < bins[i + 1])
        if sel.sum() >= 20:
            width[i] = np.percentile(x[sel], 95) - np.percentile(x[sel], 5)
    centers = (bins[:-1] + bins[1:]) / 2

    # NECK: narrowest bin between the head and the arm-span bulge
    band = (centers > y_top - 0.50 * H) & (centers < y_top - 0.22 * H) & ~np.isnan(width)
    neck_y = float(centers[band][np.argmin(width[band])])

    # HEAD: everything above the neck
    head = P[y > neck_y]
    head_center = head.mean(0)

    # ARM AXIS: the extreme-x splats (hands) set the arm height; tips set the span
    x_tip_r, x_tip_l = np.percentile(x, 99.5), np.percentile(x, 0.5)
    span = x_tip_r - x_tip_l
    hands_band = np.abs(x) > 0.80 * np.percentile(np.abs(x), 99)
    shoulder_y = float(np.median(y[hands_band]))

    # PAW centers: centroid of the distal 15% of each arm
    paw_r = P[x > x_tip_r - 0.15 * (x_tip_r - 0.0)].mean(0)
    paw_l = P[x < x_tip_l + 0.15 * (0.0 - x_tip_l)].mean(0)

    # SHOULDER: the torso's own half-width — the MEDIAN width of the torso band (neck to
    # crotch), robust to drooping arms that contaminate any band near the arm height.
    # (A plush shoulder is as wide as its torso; the arms attach at its top corners.)
    # Computed AFTER the crotch; see below.

    # CROTCH: scanning DOWN from just below the neck, the center column (|x| < 5% of span)
    # is full through the torso and empties between the legs — the crotch is the last
    # non-empty bin before a SUSTAINED empty run (3 bins, so a stray splat can't fake it).
    center = np.abs(x) < 0.05 * span
    torso_sel = center & (y < neck_y) & (y > neck_y - 0.3 * H)
    torso_center = float(np.median(np.bincount(
        np.digitize(y[torso_sel], bins) - 1, minlength=60))) if torso_sel.any() else 20.0
    threshold = max(5, 0.10 * torso_center)
    crotch_y = y_bot + 0.25 * H   # fallback if the legs never separate
    last_full, empty_run = None, 0
    for i in range(int(np.argmin(np.abs(centers - neck_y))), -1, -1):
        sel = center & (y >= bins[i]) & (y < bins[i + 1])
        if sel.sum() >= threshold:
            last_full, empty_run = i, 0
        else:
            empty_run += 1
            if last_full is not None and empty_run >= 3:
                crotch_y = float(centers[last_full])
                break

    # SHOULDER (deferred: needs crotch_y): torso width = median profile width of the torso
    # band; the shoulder joints are the top corners of that torso.
    torso_band = (centers < neck_y - 0.03 * H) & (centers > crotch_y + 0.03 * H)
    w_torso = float(np.nanmedian(width[torso_band]))
    z_torso = float(np.median(z[(y < neck_y) & (y > crotch_y)]))
    shoulder_r = np.array([w_torso / 2, shoulder_y, z_torso])
    shoulder_l = np.array([-w_torso / 2, shoulder_y, z_torso])
    hip_y = crotch_y + 0.05 * H
    hip = np.array([0.0, hip_y, float(np.median(z[(np.abs(x) < 0.1 * span) &
                                                  (np.abs(y - hip_y) < 0.05 * H)]))])

    # LEGS: two lobes below the crotch, split at x=0; lobe centroid x = leg axis x
    legs = P[y < crotch_y]
    leg_r = legs[legs[:, 0] > 0]
    leg_l = legs[legs[:, 0] < 0]
    leg_rx, leg_lx = float(np.median(leg_r[:, 0])), float(np.median(leg_l[:, 0]))

    # FOOT: the bottom 15% of each leg; ANKLE: top of that foot segment
    leg_len = crotch_y - y_bot
    foot_r = leg_r[leg_r[:, 1] < y_bot + 0.15 * leg_len].mean(0)
    foot_l = leg_l[leg_l[:, 1] < y_bot + 0.15 * leg_len].mean(0)

    return {
        "n_body": int(len(P)), "y_top": float(y_top), "y_bot": float(y_bot), "H": float(H),
        "neck_y": neck_y, "head_center": head_center.tolist(),
        "shoulder_y": shoulder_y, "x_tips": [float(x_tip_l), float(x_tip_r)],
        "shoulder_r": shoulder_r.tolist(), "shoulder_l": shoulder_l.tolist(),
        "paw_r": paw_r.tolist(), "paw_l": paw_l.tolist(),
        "crotch_y": crotch_y, "hip": hip.tolist(),
        "leg_x": [leg_lx, leg_rx], "foot_l": foot_l.tolist(), "foot_r": foot_l.tolist(),
        "leg_len": float(leg_len),
    }


# ── FIT (symmetric stick figure, proportioned to the measurements) ------------------

def fit(m: dict) -> dict:
    """One canonical, SYMMETRIC skeleton: paired joints are mirror-averaged (|x|, y, z
    averaged; x mirrored). Segment joints that a plush body does not measure (elbow, knee)
    are CONSTRUCTION points — stated as such: the midpoint of the measured endpoints."""
    def mirror_avg(pa, pb):
        pa, pb = np.array(pa, dtype=float), np.array(pb, dtype=float)
        xm = (abs(pa[0]) + abs(pb[0])) / 2
        ym = (pa[1] + pb[1]) / 2
        zm = (pa[2] + pb[2]) / 2
        return xm, ym, zm

    sx, sy, sz = mirror_avg(m["shoulder_r"], m["shoulder_l"])
    hx, hy, hz = mirror_avg(m["paw_r"], m["paw_l"])
    fx, fy, fz = mirror_avg(m["foot_r"], m["foot_l"])
    lx = (abs(m["leg_x"][0]) + abs(m["leg_x"][1])) / 2

    neck = np.array([0.0, m["neck_y"], m["head_center"][2]])
    head_c = np.array([0.0, m["head_center"][1], m["head_center"][2]])
    hip = np.array([0.0, m["hip"][1], m["hip"][2]])
    shoulder_r = np.array([sx, sy, sz])
    hand_r = np.array([hx, hy, hz])
    elbow_r = (shoulder_r + hand_r) / 2                      # construction point (plush arm)
    foot_r = np.array([fx, fy, fz])
    ankle_y = foot_r[1] + 0.15 * m["leg_len"]
    knee_y = (hip[1] + ankle_y) / 2                          # construction point (plush leg)
    knee_r = np.array([lx, knee_y, foot_r[2]])

    def L(p): return [-float(p[0]), float(p[1]), float(p[2])]

    return {"joints": {
        "head_center": head_c.tolist(), "neck": neck.tolist(), "hip_center": hip.tolist(),
        "shoulder_right": shoulder_r.tolist(), "elbow_right": elbow_r.tolist(), "hand_right": hand_r.tolist(),
        "shoulder_left": L(shoulder_r), "elbow_left": L(elbow_r), "hand_left": L(hand_r),
        "knee_right": knee_r.tolist(), "foot_right": foot_r.tolist(),
        "knee_left": L(knee_r), "foot_left": L(foot_r),
    }, "measurements": m, "symmetric": True,
        "notes": "elbow/knee are construction midpoints (plush limbs have no measured joint); "
                 "left joints are mirrors of the measured right."}


# ── OVERLAY (the gate: does the stick figure sit right?) -----------------------------

BONES = [("head_center", "neck"), ("neck", "hip_center"),
         ("shoulder_right", "elbow_right"), ("elbow_right", "hand_right"),
         ("shoulder_left", "elbow_left"), ("elbow_left", "hand_left"),
         ("neck", "shoulder_right"), ("neck", "shoulder_left"),
         ("hip_center", "knee_right"), ("knee_right", "foot_right"),
         ("hip_center", "knee_left"), ("knee_left", "foot_left")]
VIEWS = [("front", 3.14159265, 0.1), ("back", 0.0, 0.1),
         ("right", 1.5707963, 0.1), ("left", 4.7123889, 0.1)]


def hinge_axes(J: dict) -> dict:
    """Each joint's hinge axis, mechanical-drawing style: the line about which the joint
    ROTATES. Derivation rule (stated, not tuned): axis = bone_dir x world_up (the flap/
    hinge normal for a level limb), falling back to bone_dir x world_front when the bone
    is vertical (legs: kick forward/back about x). Endpoint joints (hand, foot) use their
    incoming bone. Axis length = +/-40% of the bone's length past the joint."""
    up = np.array([0.0, 1.0, 0.0])
    front = np.array([0.0, 0.0, 1.0])
    touch = {}                                    # joint -> (bone_dir, bone_len)
    for a, b in BONES:
        if a in J and b in J:
            d = np.array(J[b]) - np.array(J[a])
            n = float(np.linalg.norm(d))
            if n > 1e-9:
                touch.setdefault(a, (d / n, n))   # prefer the outgoing bone
                touch.setdefault(b, (d / n, n))   # endpoints: the incoming bone
    axes = {}
    for j, (d, ln) in touch.items():
        ax = np.cross(d, up)
        if np.linalg.norm(ax) < 1e-6:
            ax = np.cross(d, front)
        n = float(np.linalg.norm(ax))
        if n < 1e-9:
            continue
        axes[j] = (np.array(J[j]), ax / n, 0.4 * ln)
    return axes


def _dash(d: ImageDraw.ImageDraw, p0, p1, fill, width=1, dash=7, gap=5):
    """Mechanical centerline: long dashes with gaps (ImageDraw has no dashed line)."""
    p0, p1 = np.array(p0), np.array(p1)
    L = float(np.linalg.norm(p1 - p0))
    if L < 1e-6:
        return
    u = (p1 - p0) / L
    t = 0.0
    while t < L:
        d.line([tuple(p0 + u * t), tuple(p0 + u * min(t + dash, L))], fill=fill, width=width)
        t += dash + gap


def overlay(splat_path: str, skeleton_path: str, out_dir: Path):
    import struct
    buf = cb.load_splat(splat_path)
    n = len(buf)
    payload = struct.pack("<I3f", n, 2.2, 0.0, 0.1) + buf.astype(np.float32).tobytes()
    req = urllib.request.Request(ENGINE + "/membrane_bin", data=payload,
                                 headers={"Content-Type": "application/octet-stream"}, method="POST")
    urllib.request.urlopen(req, timeout=60).read()

    J = {k: np.array(v) for k, v in
         json.loads(Path(skeleton_path).read_text(encoding="utf-8"))["joints"].items()}
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, th, ph in VIEWS:
        cam = json.dumps({"cam_radius": 2.2, "cam_theta": th, "cam_phi": ph}).encode()
        req = urllib.request.Request(ENGINE + "/camera", data=cam,
                                     headers={"Content-Type": "application/json"}, method="POST")
        urllib.request.urlopen(req, timeout=15).read()
        im = Image.open(io.BytesIO(urllib.request.urlopen(ENGINE + "/frame", timeout=30).read())
                        ).convert("RGB").resize((640, 360))
        P = np.array([J[k] for k in J])
        nx, ny = project(P, th, ph, 2.2, W=640, H=360)
        px = {k: (float(nx[i] * 640), float(ny[i] * 360)) for i, k in enumerate(J)}
        axes = hinge_axes(J)
        if axes:
            pts3 = []
            spans = []
            for j, (c, ax, half) in axes.items():
                spans.append((j, len(pts3)))
                pts3 += [c - ax * half, c + ax * half]
            ax_nx, ax_ny = project(np.array(pts3), th, ph, 2.2, W=640, H=360)
            ax_px = {j: ((float(ax_nx[i] * 640), float(ax_ny[i] * 360)),
                         (float(ax_nx[i + 1] * 640), float(ax_ny[i + 1] * 360)))
                     for j, i in spans}
        d = ImageDraw.Draw(im)
        for a, b in BONES:
            if a in px and b in px:
                d.line([px[a], px[b]], fill=(0, 255, 0), width=2)
        if axes:
            for j, (p0, p1) in ax_px.items():
                if np.hypot(p1[0] - p0[0], p1[1] - p0[1]) < 6.0:
                    # axis seen END-ON (looking down the hinge): mechanical center cross
                    cx, cy = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
                    d.line([(cx - 5, cy), (cx + 5, cy)], fill=(255, 0, 255), width=2)
                    d.line([(cx, cy - 5), (cx, cy + 5)], fill=(255, 0, 255), width=2)
                else:
                    _dash(d, p0, p1, fill=(255, 0, 255), width=2)
        for k, (u, v) in px.items():
            d.ellipse([u - 4, v - 4, u + 4, v + 4], outline=(255, 40, 40), width=2)
            d.text((u + 5, v - 5), k.split("_")[0][:4], fill=(255, 220, 0))
        im.save(out_dir / f"overlay_{name}.png")
        print(f"overlay_{name} -> {out_dir / f'overlay_{name}.png'}")


# ── CLI -----------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("stage", choices=["build", "overlay"])
    ap.add_argument("target", help="path to the ORIGINAL .splat")
    ap.add_argument("--out", default=None, help="build: output skeleton JSON")
    ap.add_argument("--skeleton", default=None, help="overlay: skeleton JSON")
    ap.add_argument("--dir", default=None, help="overlay: output dir (default: <stem>_stick/)")
    a = ap.parse_args()

    if a.stage == "build":
        m = measure(a.target)
        skel = fit(m)
        out = Path(a.out) if a.out else Path(a.target).with_name(Path(a.target).stem + "_stick.json")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(skel, indent=1), encoding="utf-8")
        for k in sorted(skel["joints"]):
            print(f"  {k:16s} {[round(v, 4) for v in skel['joints'][k]]}")
        print(f"stick figure -> {out}")
    else:
        if not a.skeleton:
            raise SystemExit("overlay needs --skeleton")
        out_dir = Path(a.dir) if a.dir else Path(a.target).with_name(Path(a.target).stem + "_stick")
        overlay(a.target, a.skeleton, out_dir)


if __name__ == "__main__":
    main()
