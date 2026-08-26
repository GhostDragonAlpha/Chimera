"""skeleton.py — vision-model photogrammetry -> skeleton -> splat rigging.

REPEATABLE STAGES. Each writes an artifact to a working directory; run them in order
and re-run any one of them alone (artifacts are JSON, humans and agents both read them):

    analyze       render N views + vision-DESCRIBE the pose   -> <dir>/analysis.json
    mark          render N views + vision-MARK joint 2D coords -> <dir>/marks.json
    triangulate   marks + camera model -> 3D joints           -> <dir>/skeleton.json
    assign        nearest-bone splat assignment               -> <dir>/assignment.json

The camera model is the C++ engine's EXACT orbit camera (radius/theta/phi, 45 deg FOV,
Vulkan Y-down projection). Marks are un-projected against the same math the renderer uses,
so a 2D mark from the eye is a ray in the engine's frame.

Usage (from the repo root):
    python ChimeraEngine/native/skeleton.py analyze  models/triposplat/static/viewer/teddy_tpose.splat
    python ChimeraEngine/native/skeleton.py mark     <splat>            # 13 teddy joints by default
    python ChimeraEngine/native/skeleton.py triangulate --marks <dir>/marks.json
    python ChimeraEngine/native/skeleton.py assign   <splat> --skeleton <dir>/skeleton.json
"""
from __future__ import annotations

import argparse
import io
import json
import math
import re
import struct
import sys
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image

_HERE = Path(__file__).resolve().parent
_CHIMERA_ENGINE = _HERE.parent
if str(_CHIMERA_ENGINE) not in sys.path:
    sys.path.insert(0, str(_CHIMERA_ENGINE))

import cpp_bridge as cb          # noqa: E402
import senses                     # noqa: E402

ENGINE = "http://localhost:8090"
W, H = 1920.0, 1080.0
FOV = math.radians(45.0)
ASPECT = W / H
F = 1.0 / math.tan(FOV / 2.0)

# the ring every stage uses: 8 azimuths + 2 elevated (matches how the operator looks at it)
RING = [(math.radians(k * 45), 0.1) for k in range(8)] + [(0.0, 0.5), (math.radians(90), 0.5)]

DEFAULT_JOINTS = [
    "head_center", "neck",
    "shoulder_left", "shoulder_right",
    "elbow_left", "elbow_right",
    "hand_left", "hand_right",
    "hip_center",
    "knee_left", "knee_right",
    "foot_left", "foot_right",
]


# ── engine camera ---------------------------------------------------------------

def _set_camera(r, th, ph):
    payload = json.dumps({"cam_radius": r, "cam_theta": th, "cam_phi": ph}).encode()
    req = urllib.request.Request(ENGINE + "/camera", data=payload,
                                 headers={"Content-Type": "application/json"}, method="POST")
    urllib.request.urlopen(req, timeout=15).read()


def _fetch_frame():
    return urllib.request.urlopen(ENGINE + "/frame", timeout=30).read()


def _camera(th, ph, radius):
    c, s = math.cos(ph), math.sin(ph)
    cx, sx = math.cos(th), math.sin(th)
    eye = np.array([radius * c * sx, radius * s, -radius * c * cx])
    up = np.array([-s * sx, c, s * cx])
    z = eye / np.linalg.norm(eye)             # backward (center -> eye)
    x = np.cross(up, z); x /= np.linalg.norm(x)
    y = np.cross(z, x)
    return eye, x, y, z


def _ray(th, ph, nx, ny, radius):
    eye, x, y, z = _camera(th, ph, radius)
    vx = (2.0 * nx - 1.0) * ASPECT / F
    vy = -(2.0 * ny - 1.0) / F
    d = vx * x + vy * y - z
    d /= np.linalg.norm(d)
    return eye, d


def triangulate(rays):
    """Least-squares intersection of (eye, dir) rays -> a 3D point."""
    A = np.zeros((3, 3)); b = np.zeros(3)
    for eye, d in rays:
        P = np.eye(3) - np.outer(d, d)
        A += P; b += P @ eye
    return np.linalg.solve(A, b)


# ── helpers ---------------------------------------------------------------------

def _load_pos(splat_path):
    return cb.load_splat(splat_path)[:, 0:3].astype(np.float64)


def _render_views(splat_path, angles, radius, workdir, prefix):
    """Load the splat into the engine and render each view to a PNG. Returns the PNG paths."""
    pos = _load_pos(splat_path)
    n = pos.shape[0]
    r, th0, ph0 = cb._spherical((0.0, 0.0, radius))
    payload = struct.pack("<I3f", n, r, th0, ph0) + cb.load_splat(splat_path).astype(np.float32).tobytes()
    req = urllib.request.Request(ENGINE + "/membrane_bin", data=payload,
                                 headers={"Content-Type": "application/octet-stream"}, method="POST")
    urllib.request.urlopen(req, timeout=60).read()

    paths = []
    for i, (th, ph) in enumerate(angles):
        _set_camera(radius, th, ph)
        png = _fetch_frame()
        p = workdir / f"{prefix}_{i:02d}.png"
        Image.open(io.BytesIO(png)).convert("RGB").resize((640, 360)).save(p)
        paths.append(p)
    return paths


def _parse_json(text):
    m = re.search(r"\{.*\}", text or "", re.S)
    return json.loads(m.group(0)) if m else None


# ── STAGE 1: analyze (verify the pose BEFORE rigging) ----------------------------

def stage_analyze(splat_path, angles, radius, workdir):
    workdir.mkdir(parents=True, exist_ok=True)
    pos = _load_pos(splat_path)
    report = {
        "splat": str(splat_path),
        "n": int(pos.shape[0]),
        "bbox": {
            "x": [round(float(pos[:, 0].min()), 4), round(float(pos[:, 0].max()), 4)],
            "y": [round(float(pos[:, 1].min()), 4), round(float(pos[:, 1].max()), 4)],
            "z": [round(float(pos[:, 2].min()), 4), round(float(pos[:, 2].max()), 4)],
        },
        "views": {},
    }
    prompt = ("Describe this 3D object in ONE sentence: what is it, and what pose is it in "
              "(standing upright / sitting / lying; arms out to the sides / down / raised)? "
              "Answer only the description.")
    paths = _render_views(splat_path, angles, radius, workdir, "analyze")
    for i, p in enumerate(paths):
        th, ph = angles[i]
        desc = senses.see(str(p), prompt, timeout=120)
        report["views"][i] = {"theta": round(th, 3), "phi": round(ph, 3), "description": desc}
        print(f"  view {i:02d} (th={th:.2f} ph={ph:.2f}): {desc}")
    out = workdir / "analysis.json"
    out.write_text(json.dumps(report, indent=1), encoding="utf-8")
    print(f"analysis -> {out}")
    return report


# ── STAGE 2: mark ----------------------------------------------------------------

def stage_mark(splat_path, joints, angles, radius, workdir):
    workdir.mkdir(parents=True, exist_ok=True)
    prompt = (
        "You are looking at a rendered 3D teddy bear on a dark background, 640x360. "
        "Output ONLY a JSON object locating these skeleton joints as normalized image coords [x,y] "
        "(x=0 left edge, x=1 right edge, y=0 top edge, y=1 bottom edge). Estimate occluded joints.\n"
        "Joints: " + ", ".join(joints) + ".\n"
        'Format exactly: {"head_center":[x,y], ...}'
    )
    paths = _render_views(splat_path, angles, radius, workdir, "mark")
    marks = {}
    for i, p in enumerate(paths):
        th, ph = angles[i]
        raw = senses.see(str(p), prompt, timeout=300)
        parsed = _parse_json(raw)
        if parsed:
            marks[i] = parsed
            print(f"  view {i:02d}: {len(parsed)}/{len(joints)} joints")
        else:
            print(f"  view {i:02d}: NO JSON")
    out = workdir / "marks.json"
    out.write_text(json.dumps(marks, indent=1), encoding="utf-8")
    print(f"marks -> {out}")
    return marks


# ── STAGE 3: triangulate ---------------------------------------------------------

_PAIRS = ["shoulder", "elbow", "hand", "knee", "foot"]


def stage_triangulate(marks_path, angles, radius, workdir):
    marks = json.loads(Path(marks_path).read_text(encoding="utf-8"))
    joints = sorted({j for v in marks.values() for j in v})
    pts = {j: [] for j in joints}
    for i, v in marks.items():
        th, ph = angles[int(i)]
        swap = math.cos(th) > 0.0   # back views: the eye's image-left/right is flipped
        for j in joints:
            name = j
            if swap and (j.endswith("_left") or j.endswith("_right")):
                base, side = j.rsplit("_", 1)
                name = base + ("_right" if side == "left" else "_left")
            if name in v:
                pts[j].append((th, ph, v[name][0], v[name][1]))

    out3d = {}
    for j in joints:
        rays = [_ray(th, ph, nx, ny, radius) for (th, ph, nx, ny) in pts[j]]
        if rays:
            out3d[j] = [round(float(x), 4) for x in triangulate(rays)]

    out = workdir / "skeleton.json"
    out.write_text(json.dumps({"joints": out3d}, indent=1), encoding="utf-8")
    print(f"skeleton ({len(out3d)} joints) -> {out}")
    for j in sorted(out3d):
        print(f"  {j:16s} {out3d[j]}")
    return out3d


# ── STAGE 4: assign --------------------------------------------------------------

def stage_assign(splat_path, skeleton_path, bones, workdir):
    skel = json.loads(Path(skeleton_path).read_text(encoding="utf-8"))["joints"]
    J = {k: np.array(v, dtype=np.float64) for k, v in skel.items()}
    bone_segs = [(n, J[a], J[b]) for n, a, b in bones]

    pos = _load_pos(splat_path)
    n = pos.shape[0]
    A = np.array([a for _, a, _b in bone_segs])
    B = np.array([b for _, _a, b in bone_segs])
    V = B - A; L2 = (V * V).sum(1)

    best = np.zeros(n, dtype=np.int32); best_d = np.full(n, np.inf)
    for k in range(len(bone_segs)):
        W = pos - A[k]
        t = np.clip((W @ V[k]) / L2[k], 0.0, 1.0)
        d = np.linalg.norm(W - t[:, None] * V[k], axis=1)
        upd = d < best_d
        best[upd] = k; best_d[upd] = d[upd]

    counts = {bone_segs[k][0]: int((best == k).sum()) for k in range(len(bone_segs))}
    out = workdir / "assignment.json"
    out.write_text(json.dumps({"counts": counts}, indent=1), encoding="utf-8")
    print(f"assignment -> {out}")
    for nm, c in counts.items():
        print(f"  {nm:10s} {c:7d} splats")
    return best, counts


# ── CLI --------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("stage", choices=["analyze", "mark", "triangulate", "assign"])
    ap.add_argument("target", help="splat path (analyze/mark/assign) or marks.json (triangulate)")
    ap.add_argument("--dir", default=None, help="working directory (default: <target stem>_rig/)")
    ap.add_argument("--radius", type=float, default=2.2)
    ap.add_argument("--joints", default=None, help="JSON file of joint names (default: 13 teddy joints)")
    ap.add_argument("--bones", default=None, help="JSON file of bones [[name,a,b],...] (assign only)")
    ap.add_argument("--skeleton", default=None, help="skeleton.json (assign only)")
    a = ap.parse_args()

    workdir = Path(a.dir) if a.dir else (Path(a.target).with_name(Path(a.target).stem + "_rig"))

    if a.stage == "triangulate":
        stage_triangulate(a.target, RING, a.radius, workdir)
        return

    joints = DEFAULT_JOINTS
    if a.joints:
        joints = json.loads(Path(a.joints).read_text(encoding="utf-8"))

    if a.stage == "analyze":
        stage_analyze(a.target, RING, a.radius, workdir)
    elif a.stage == "mark":
        stage_mark(a.target, joints, RING, a.radius, workdir)
    elif a.stage == "assign":
        bones = json.loads(Path(a.bones).read_text(encoding="utf-8")) if a.bones else [
            ["head", "neck", "head_center"], ["torso", "neck", "hip_center"],
            ["uparm_L", "shoulder_left", "elbow_left"], ["farm_L", "elbow_left", "hand_left"],
            ["uparm_R", "shoulder_right", "elbow_right"], ["farm_R", "elbow_right", "hand_right"],
            ["thigh_L", "hip_center", "knee_left"], ["shin_L", "knee_left", "foot_left"],
            ["thigh_R", "hip_center", "knee_right"], ["shin_R", "knee_right", "foot_right"],
        ]
        stage_assign(a.target, a.skeleton or str(workdir / "skeleton.json"), bones, workdir)


if __name__ == "__main__":
    main()
