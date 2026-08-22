"""stickfigure_quad.py — the QUADRUPED stick figure (koala = workflow instance #2).

Same operator directive as stickfigure.py (MEASURE, then fit a SYMMETRIC figure), but a
quadruped is a different measurement problem: the spine is HORIZONTAL (along z, front=+z),
there are FOUR legs (front pair / back pair), and the neck is the width minimum between
the head and the chest along z. The teddy's rules (arm axis from extreme-x, crotch from
the center column) do not transfer; the rules below are the quadruped equivalents, each a
stated measurement over the point distribution.

THEORY (Rule 0):
  STATEMENT  — a standing quadruped is readable from its own point distribution: the feet
               are the four clusters of the bottom band, the back is the flat top of the
               trunk profile, the neck is the z-profile width minimum between the chest and
               the head, the ears are a width excursion ABOVE the head (excluded from the
               neck rule), and left == right by symmetry.
  PREDICTION — the fitted joints land on anatomically sensible positions (overlay gate).
  FALSIFIER  — if the overlay shows bones outside the body or joints off their junctions,
               the profile rules are wrong for this asset.

CONSTRUCTION POINTS (stated, not measured — a smooth mesh hides internal joints):
  elbow/knee sit at ANATOMICAL ratios along the leg column (koala osteology research,
  docs/research/koala_anatomy_reference.md), NOT midpoints.

STAGES: build (measure + fit -> skeleton JSON), overlay (the gate).
Usage (from the repo root):
  python ChimeraEngine/native/stickfigure_quad.py build models/koala/koala_500k_front.splat \
      --out models/koala/rig/skeleton_quad.json
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
from stickfigure import hinge_axes, _dash   # noqa: E402  (mechanical axis lines)

ENGINE = "http://localhost:8080"


# ── MEASURE ---------------------------------------------------------------------------

def _kmeans(P: np.ndarray, k: int, iters: int = 80, seed: int = 0) -> tuple:
    rng = np.random.default_rng(seed)
    C = P[rng.choice(len(P), k, replace=False)]
    a = np.zeros(len(P), dtype=int)
    for _ in range(iters):
        a = ((P[:, None, :] - C[None]) ** 2).sum(2).argmin(1)
        for i in range(k):
            if (a == i).any():
                C[i] = P[a == i].mean(0)
    return C, a


def measure(splat_path: str) -> dict:
    """Rules (each stated): feet = 4 clusters of the bottom band; floor = 3rd percentile y;
    back = the trunk's flat top; neck = the z-profile width minimum between chest and head,
    rejecting the EAR excursion (ears flare wider than the head above it); leg columns =
    the vertical splat columns above each foot cluster."""
    buf = cb.load_splat(splat_path)
    pos = buf[:, 0:3].astype(np.float64)
    floor_y = float(np.percentile(pos[:, 1], 3))

    # feet: bottom band, k-means k=4 on (x,z) — symmetric by construction of the asset
    band = pos[pos[:, 1] < floor_y + 0.05][:, [0, 2]]
    C, a = _kmeans(band, 4)
    feet = []
    for i in range(4):
        pt = np.array([C[i][0], floor_y, C[i][1]])
        feet.append(pt)
    front = sorted([f for f in feet if f[2] > np.median([f[2] for f in feet])], key=lambda f: f[0])
    back = sorted([f for f in feet if f[2] <= np.median([f[2] for f in feet])], key=lambda f: f[0])
    foot_fl, foot_fr = front[0], front[1]          # x- = left
    foot_bl, foot_br = back[0], back[1]

    # z profile of the trunk: width + top per bin
    zbins = np.linspace(pos[:, 2].min(), pos[:, 2].max(), 41)
    prof = []
    for i in range(40):
        sel = (pos[:, 2] >= zbins[i]) & (pos[:, 2] < zbins[i + 1])
        if sel.sum() < 50:
            continue
        zc = 0.5 * (zbins[i] + zbins[i + 1])
        prof.append((zc, float(np.percentile(np.abs(pos[sel, 0]), 90) * 2),
                     float(np.percentile(pos[sel, 1], 95)),
                     float(np.percentile(pos[sel, 1], 5))))
    prof = np.array(prof)

    # neck: width minimum between the chest and the head. The EARS are the widest excursion
    # of the front region and sit ON the head — so: ear_z = the width maximum in front of
    # the chest, and the neck is the width minimum strictly between chest and ear_z. (An
    # unbounded minimum runs into the head and grabs the narrowing snout instead.)
    back_top = float(np.median(prof[(prof[:, 0] > foot_bl[2]) & (prof[:, 0] < foot_fl[2]), 2]))
    front_mask = prof[:, 0] > foot_fl[2]
    ear_z = float(prof[front_mask][np.argmax(prof[front_mask, 1]), 0])
    cand = (prof[:, 0] > foot_fl[2]) & (prof[:, 0] < ear_z)
    neck_i = np.flatnonzero(cand)[np.argmin(prof[cand, 1])]
    neck_z = float(prof[neck_i, 0])

    # head: the lobe in front of the neck
    head = pos[(pos[:, 2] > neck_z + 0.02)]
    head_center = np.array([0.0, float(np.percentile(head[:, 1], 60)), float(np.median(head[:, 2]))])

    # spine: from the hind feet z to the neck, at mid-body height
    chest_z = float(foot_fl[2])
    pelvis_z = float(foot_br[2])
    spine_y = float(back_top - 0.35 * (back_top - np.median(prof[:, 3])))

    m = {
        "floor_y": floor_y,
        "foot_fl": foot_fl.tolist(), "foot_fr": foot_fr.tolist(),
        "foot_bl": foot_bl.tolist(), "foot_br": foot_br.tolist(),
        "back_top": back_top, "spine_y": spine_y,
        "neck_z": neck_z, "head_center": head_center.tolist(),
        "chest_z": chest_z, "pelvis_z": pelvis_z,
        "stance_x": float(np.mean([abs(foot_fl[0]), abs(foot_fr[0]), abs(foot_bl[0]), abs(foot_br[0])])),
        "profile": prof.tolist(),
    }
    return m


# ── FIT (symmetric quadruped, anatomical construction points) --------------------------

# construction ratios along the leg column (foot -> body joint), from koala osteology
# (docs/research/koala_anatomy_reference.md §1, Hawkins 2022 + Finch & Freedman 1988 via
# Black et al. 2012, scaled): elbow = radius/(humerus+radius) = 126.7/241.0 = 0.526 up the
# column; knee = tibia/(femur+tibia) = 109.8/248.8 = 0.441 (the tibia is markedly SHORTER
# than the femur — the knee sits below the midpoint).
LEG_MID_FRAC = {"front": 0.526, "back": 0.441}

def fit(m: dict) -> dict:
    def mirror_avg(pa, pb):
        pa, pb = np.array(pa, float), np.array(pb, float)
        return (abs(pa[0]) + abs(pb[0])) / 2, (pa[1] + pb[1]) / 2, (pa[2] + pb[2]) / 2

    fxl, fy, fz = mirror_avg(m["foot_fl"], m["foot_fr"])
    bxl, by, bz = mirror_avg(m["foot_bl"], m["foot_br"])
    foot_f = np.array([fxl, fy, fz])
    foot_b = np.array([bxl, by, bz])
    neck = np.array([0.0, m["head_center"][1] - 0.05, m["neck_z"]])
    head_c = np.array(m["head_center"])
    chest = np.array([0.0, m["spine_y"], m["chest_z"]])
    pelvis = np.array([0.0, m["spine_y"], m["pelvis_z"]])

    # leg root joints (shoulder / hip): inside the body above each foot pair, at spine height
    shoulder = np.array([fxl, m["spine_y"], fz])
    hip = np.array([bxl, m["spine_y"], bz])
    elbow = foot_f + LEG_MID_FRAC["front"] * (shoulder - foot_f)     # construction (ratio)
    knee = foot_b + LEG_MID_FRAC["back"] * (hip - foot_b)            # construction (ratio)

    def L(p): return [-float(p[0]), float(p[1]), float(p[2])]

    return {"joints": {
        "head_center": head_c.tolist(), "neck": neck.tolist(),
        "chest": chest.tolist(), "pelvis": pelvis.tolist(),
        "shoulder_f_right": shoulder.tolist(), "elbow_f_right": elbow.tolist(), "foot_f_right": foot_f.tolist(),
        "shoulder_f_left": L(shoulder), "elbow_f_left": L(elbow), "foot_f_left": L(foot_f),
        "hip_b_right": hip.tolist(), "knee_b_right": knee.tolist(), "foot_b_right": foot_b.tolist(),
        "hip_b_left": L(hip), "knee_b_left": L(knee), "foot_b_left": L(foot_b),
    }, "measurements": m, "symmetric": True, "species": "quadruped",
        "notes": "elbow/knee are construction points at anatomical leg-column ratios "
                 "(koala osteology), left joints are mirrors of the measured right."}


# ── OVERLAY (the gate) ----------------------------------------------------------------

BONES = [("neck", "head_center"), ("neck", "chest"), ("chest", "pelvis"),
         ("chest", "shoulder_f_right"), ("shoulder_f_right", "elbow_f_right"), ("elbow_f_right", "foot_f_right"),
         ("chest", "shoulder_f_left"), ("shoulder_f_left", "elbow_f_left"), ("elbow_f_left", "foot_f_left"),
         ("pelvis", "hip_b_right"), ("hip_b_right", "knee_b_right"), ("knee_b_right", "foot_b_right"),
         ("pelvis", "hip_b_left"), ("hip_b_left", "knee_b_left"), ("knee_b_left", "foot_b_left")]
VIEWS = [("front", 3.14159265, 0.1), ("back", 0.0, 0.1),
         ("right", 1.5707963, 0.1), ("left", 4.7123889, 0.1)]


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
        axes = hinge_axes(J) if False else {}   # quadruped hinge axes: TODO with anatomy
        d = ImageDraw.Draw(im)
        for a, b in BONES:
            if a in px and b in px:
                d.line([px[a], px[b]], fill=(0, 255, 0), width=2)
        for k, (u, v) in px.items():
            d.ellipse([u - 4, v - 4, u + 4, v + 4], outline=(255, 40, 40), width=2)
            d.text((u + 5, v - 5), k.split("_")[0][:4], fill=(255, 220, 0))
        im.save(out_dir / f"overlay_{name}.png")
        print(f"overlay_{name} -> {out_dir / f'overlay_{name}.png'}")


# ── CLI ---------------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("stage", choices=["build", "overlay"])
    ap.add_argument("target", help="path to the .splat")
    ap.add_argument("--out", default=None, help="build: output skeleton JSON")
    ap.add_argument("--skeleton", default=None, help="overlay: skeleton JSON")
    ap.add_argument("--dir", default=None, help="overlay: output dir")
    a = ap.parse_args()

    if a.stage == "build":
        m = measure(a.target)
        skel = fit(m)
        out = Path(a.out) if a.out else Path(a.target).with_name(Path(a.target).stem + "_quad.json")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(skel, indent=1), encoding="utf-8")
        for k in sorted(skel["joints"]):
            print(f"  {k:18s} {[round(v, 4) for v in skel['joints'][k]]}")
        print(f"quadruped stick figure -> {out}")
    else:
        if not a.skeleton:
            raise SystemExit("overlay needs --skeleton")
        overlay(a.target, a.skeleton, Path(a.dir) if a.dir else
                Path(a.target).with_name(Path(a.target).stem + "_quad"))


if __name__ == "__main__":
    main()
