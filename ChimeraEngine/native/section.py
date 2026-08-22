"""section.py — marker-based 3DGS sectioning: the "UV unwrap" for a splat cloud.

THE METHOD (operator directive, 2026-08-18): orbit the ORIGINAL splat, let the EYE place
markers point-to-point naming parts (leg, arm, head, eye, ear, lips, ...), and CUT the cloud
along those markers — exactly how a UV unwrap cuts a mesh along seams, except the islands
are 3D splat regions and the seams are marker chains. Color clustering (extract_materials.py)
cannot do this: an ear and a forearm are the same tan to it. Parts are SPATIAL, and only
markers on the rotating original define them.

THEORY (Rule 0):
  STATEMENT  — a part is (a) a feature patch bounded by a ring of markers anchored to the
               surface (eye, nose, muzzle, ear: the ring polygon on the surface + a shallow
               tube around it IS the part), or (b) a volume flood-filled from a seed marker
               on a nearest-neighbor graph where edges crossing a band seam (neck, shoulder,
               wrist, hip, ankle) are blocked (head, torso, arms, hands, legs, feet).
  PREDICTION — a part sectioned this way renders ALONE with no neighbor bleed (no muzzle
               color on the back of the head — the z-slab bug of single-view polygons is
               impossible here: the ring tube is shallow by construction).
  FALSIFIER  — if the eye sees bleed or split parts in the verify movie, the barrier rule
               is wrong (then: tighten tube / enlarge seam locality, or go full geodesic).

TOKEN DISCIPLINE (operator directive): ALL perception runs on LOCAL qwen3.8 via senses.py.
The eye gets ONE watch() call over a 16-frame numbered orbit (senses sizes num_ctx to the
frames + answer — the model loads only what it needs, everything stays on the GPU). This
agent only ever sees compact JSON and the final verdict. If the single watch() yields
unusable JSON, `mark --per-frame` falls back to one see() per frame.

STAGES (each writes JSON artifacts to the workdir; run in order, re-run any alone):
    movie    render a numbered 16-frame orbit of the ORIGINAL splat   -> <dir>/movie/fXX.png
    mark     the eye watches the orbit -> seeds/rings/bands JSON      -> <dir>/marks2d.json
             then anchored to the surface against the exact camera    -> <dir>/marks3d.json
    cut      ring prisms + seam-barrier graph flood                   -> <dir>/part_assignment.npy
    verify   recolor by part, orbit, the eye judges bleed/coherence   -> <dir>/verdict.txt
    isolate  render ONE part alone (debugging a bleed report)         -> <dir>/isolate_<part>/fXX.png

Requires: the C++ engine on :8080 and Ollama qwen3.8 (the eye). Neither is started here.

Usage (from the repo root):
    python ChimeraEngine/native/section.py movie   models/imagegen/tpose2_640.splat
    python ChimeraEngine/native/section.py mark    models/imagegen/tpose2_640.splat
    python ChimeraEngine/native/section.py cut     models/imagegen/tpose2_640.splat
    python ChimeraEngine/native/section.py verify  models/imagegen/tpose2_640.splat
    python ChimeraEngine/native/section.py isolate models/imagegen/tpose2_640.splat --part ear_left
"""
from __future__ import annotations

import argparse
import heapq
import io
import json
import math
import re
import struct
import sys
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from matplotlib.path import Path as MplPath

_HERE = Path(__file__).resolve().parent
_CHIMERA_ENGINE = _HERE.parent
if str(_CHIMERA_ENGINE) not in sys.path:
    sys.path.insert(0, str(_CHIMERA_ENGINE))

import cpp_bridge as cb          # noqa: E402
import senses                    # noqa: E402
from skeleton import _ray, _set_camera, _fetch_frame   # noqa: E402  (the engine's EXACT camera)

ENGINE = "http://localhost:8080"

# ── the orbit every stage uses ---------------------------------------------------
FRAMES = 16                       # one level ring; frame i -> theta = 2*pi*i/FRAMES
PHI = 0.1
RADIUS = 2.2
# theta=0 puts the camera at -z: the bear's BACK. So f08 = front, f00 = back,
# f04 = the bear's right side, f12 = its left side. The mark prompt tells the eye this.

# ── the sectioning spec (teddy = instance #1; other assets get their own spec) ----
# RING parts: a marker ring on a surface bounds a shallow prism -> the part.
RING_PARTS = ["eye_left", "eye_right", "nose", "mouth", "muzzle", "ear_left", "ear_right"]
# FLOOD parts: a seed marker + graph flood, stopped by band seams.
FLOOD_PARTS = ["head", "torso",
               "arm_left", "arm_right", "hand_left", "hand_right",
               "leg_left", "leg_right", "foot_left", "foot_right"]
# BAND seams: a marker ring around a junction; edges crossing it are blocked.
BAND_SEAMS = ["neck", "shoulder_left", "shoulder_right",
              "wrist_left", "wrist_right",
              "hip_left", "hip_right",
              "ankle_left", "ankle_right"]

# which flood parts each band separates (seed A side | seed B side). The eye's ring gives
# the junction POSITION; the limb axis (seed->seed) gives the plane NORMAL — measured
# 2026-08-18: PCA normals from sloppy eye rings leak (arm_right flooded the back, 36k vs
# 6.8k), seed-axis normals are the derived anatomy.
BAND_PARTS = {
    "neck": ("head", "torso"),
    "shoulder_left": ("arm_left", "torso"), "shoulder_right": ("arm_right", "torso"),
    "wrist_left": ("hand_left", "arm_left"), "wrist_right": ("hand_right", "arm_right"),
    "hip_left": ("leg_left", "torso"), "hip_right": ("leg_right", "torso"),
    "ankle_left": ("foot_left", "leg_left"), "ankle_right": ("foot_right", "leg_right"),
}

PARTS = FLOOD_PARTS + RING_PARTS

# ── STICK-FIGURE spec (the operator's pivot, 2026-08-18): bones from skeleton.py's
# triangulated joints instead of eye seam rings — joints triangulate cleanly (13/13 on all
# 10 views), seam rings never did. NOTE: skeleton.py's "_left" is the eye's image-left on
# the front view = the bear's ANATOMICAL RIGHT (its mark stage only swaps on back views).
SKEL_BONES = [  # (part, jointA, jointB) — the part IS the bone's region
    ("head", "neck", "head_center"),
    ("torso", "neck", "hip_center"),
    ("uparm_left", "shoulder_left", "elbow_left"), ("farm_left", "elbow_left", "hand_left"),
    ("uparm_right", "shoulder_right", "elbow_right"), ("farm_right", "elbow_right", "hand_right"),
    ("thigh_left", "hip_center", "knee_left"), ("shin_left", "knee_left", "foot_left"),
    ("thigh_right", "hip_center", "knee_right"), ("shin_right", "knee_right", "foot_right"),
]
# junction planes: at this joint, normal = this bone axis — the flood stops at the joint.
SKEL_JUNCTIONS = [  # (joint, axisJointA, axisJointB)
    ("neck", "neck", "head_center"),
    ("shoulder_left", "shoulder_left", "elbow_left"), ("shoulder_right", "shoulder_right", "elbow_right"),
    ("elbow_left", "elbow_left", "hand_left"), ("elbow_right", "elbow_right", "hand_right"),
    ("hip_center", "hip_center", "knee_left"), ("hip_center", "hip_center", "knee_right"),
    ("knee_left", "knee_left", "foot_left"), ("knee_right", "knee_right", "foot_right"),
]
# extremity split: splats flooded onto this bone BEYOND its end joint become this part.
SKEL_TIPS = {"farm_left": ("hand_left", "hand_left"), "farm_right": ("hand_right", "hand_right"),
             "shin_left": ("foot_left", "foot_left"), "shin_right": ("foot_right", "foot_right")}
SKEL_PARTS = [b[0] for b in SKEL_BONES] + ["hand_left", "hand_right", "foot_left", "foot_right"]

# QUADRUPED spec (koala = instance #2, stickfigure_quad.py joints, spine HORIZONTAL along z).
# The torso bone runs pelvis->NECK (not pelvis->chest): the neck joint sits in front of the
# chest, and a pelvis->chest bone would orphan the shoulder region between them. Shoulder/hip
# root planes point DOWN the leg (root joint -> foot), head's points neck -> head_center.
QUAD_SKEL_BONES = [  # (part, jointA, jointB)
    ("head", "neck", "head_center"),
    ("torso", "pelvis", "neck"),
    ("thigh_f_left", "shoulder_f_left", "elbow_f_left"), ("shin_f_left", "elbow_f_left", "foot_f_left"),
    ("thigh_f_right", "shoulder_f_right", "elbow_f_right"), ("shin_f_right", "elbow_f_right", "foot_f_right"),
    ("thigh_b_left", "hip_b_left", "knee_b_left"), ("shin_b_left", "knee_b_left", "foot_b_left"),
    ("thigh_b_right", "hip_b_right", "knee_b_right"), ("shin_b_right", "knee_b_right", "foot_b_right"),
]
QUAD_SKEL_TIPS = {f"shin_{p}_{s}": (f"foot_{p}_{s}", f"foot_{p}_{s}")
                  for p in ("f", "b") for s in ("left", "right")}
QUAD_ROOT_PLANE = {  # bone part -> (root joint, axis joint): claim only splats beyond the root
    "head": ("neck", "head_center"),
    **{f"{seg}_{p}_{s}": (f"{'shoulder' if p == 'f' else 'hip'}_{p}_{s}", f"foot_{p}_{s}")
       for seg in ("thigh", "shin") for p in ("f", "b") for s in ("left", "right")},
}
QUAD_SKEL_PARTS = [b[0] for b in QUAD_SKEL_BONES] + [f"foot_{p}_{s}" for p in ("f", "b")
                                                     for s in ("left", "right")]
SPECIES_SPECS = {  # species -> (bones, tips, root_plane, parts)
    "biped": (SKEL_BONES, SKEL_TIPS, None, SKEL_PARTS),   # None -> biped ROOT_PLANE below
    "quadruped": (QUAD_SKEL_BONES, QUAD_SKEL_TIPS, QUAD_ROOT_PLANE, QUAD_SKEL_PARTS),
}

PALETTE = {  # garish on purpose — verification colors, never final materials
    "head": (0.90, 0.75, 0.20), "torso": (0.15, 0.55, 0.90),
    "arm_left": (0.90, 0.20, 0.20), "arm_right": (0.85, 0.45, 0.10),
    "hand_left": (0.95, 0.55, 0.60), "hand_right": (0.60, 0.20, 0.70),
    "leg_left": (0.15, 0.80, 0.25), "leg_right": (0.10, 0.55, 0.25),
    "foot_left": (0.55, 0.85, 0.55), "foot_right": (0.20, 0.90, 0.75),
    "uparm_left": (0.90, 0.20, 0.20), "uparm_right": (0.85, 0.45, 0.10),
    "farm_left": (0.95, 0.45, 0.45), "farm_right": (0.70, 0.25, 0.60),
    "thigh_left": (0.15, 0.80, 0.25), "thigh_right": (0.10, 0.55, 0.25),
    "shin_left": (0.45, 0.85, 0.40), "shin_right": (0.15, 0.75, 0.60),
    "eye_left": (0.05, 0.05, 0.05), "eye_right": (0.30, 0.30, 0.30),
    "nose": (1.00, 1.00, 1.00), "mouth": (0.70, 0.10, 0.35),
    "muzzle": (0.98, 0.90, 0.65), "ear_left": (0.40, 0.20, 0.05), "ear_right": (0.65, 0.40, 0.15),
    # quadruped (koala) — front legs warm, back legs cool, feet bright
    "thigh_f_left": (0.90, 0.20, 0.20), "thigh_f_right": (0.85, 0.45, 0.10),
    "shin_f_left": (0.95, 0.45, 0.45), "shin_f_right": (0.70, 0.25, 0.60),
    "thigh_b_left": (0.15, 0.80, 0.25), "thigh_b_right": (0.10, 0.55, 0.25),
    "shin_b_left": (0.45, 0.85, 0.40), "shin_b_right": (0.15, 0.75, 0.60),
    "foot_f_left": (0.95, 0.55, 0.60), "foot_f_right": (0.60, 0.20, 0.70),
    "foot_b_left": (0.55, 0.85, 0.55), "foot_b_right": (0.20, 0.90, 0.75),
}

BARRIER = 1.0e6   # big-M: > any legitimate in-part geodesic (cloud diameter ~1, edge ~spacing)


# ── shared helpers ---------------------------------------------------------------

def _upload(buf14: np.ndarray):
    n = len(buf14)
    payload = struct.pack("<I3f", n, RADIUS, 0.0, PHI) + buf14.astype(np.float32).tobytes()
    req = urllib.request.Request(ENGINE + "/membrane_bin", data=payload,
                                 headers={"Content-Type": "application/octet-stream", }, method="POST")
    body = urllib.request.urlopen(req, timeout=60).read()
    if b'"ok":true' not in body:
        raise RuntimeError(f"engine rejected upload: {body[:200]}")


def _orbit(workdir: Path, sub: str, tag: bool):
    """Render the FRAMES-frame orbit of whatever is currently uploaded; burn the frame
    index into each image so the eye can reference it (tag=True for eye consumption)."""
    out = workdir / sub
    out.mkdir(parents=True, exist_ok=True)
    paths = []
    for i in range(FRAMES):
        _set_camera(RADIUS, 2.0 * math.pi * i / FRAMES, PHI)
        im = Image.open(io.BytesIO(_fetch_frame())).convert("RGB").resize((640, 360))
        if tag:
            ImageDraw.Draw(im).text((6, 4), f"f{i:02d}", fill=(255, 70, 70))
        p = out / f"f{i:02d}.png"
        im.save(p)
        paths.append(str(p))
    return paths


def _theta(i: int) -> float:
    return 2.0 * math.pi * i / FRAMES


def _spacing(pos: np.ndarray) -> float:
    """Median nearest-neighbor distance (sampled) — the DERIVED yardstick for every
    tube/epsilon below. Voxel grid, no scipy."""
    rng = np.random.default_rng(0)
    samp = pos[rng.choice(len(pos), size=min(4000, len(pos)), replace=False)]
    cell = max(float(np.ptp(pos, axis=0).max()) / 64.0, 1e-6)
    vox = {}
    keys = np.floor(pos / cell).astype(np.int32)
    for k, p in zip(map(tuple, keys), pos):
        vox.setdefault(k, []).append(p)
    best = []
    for p in samp:
        k = tuple(np.floor(p / cell).astype(np.int32))
        cands = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    cands.extend(vox.get((k[0] + dx, k[1] + dy, k[2] + dz), ()))
        c = np.asarray(cands)
        d = np.linalg.norm(c - p, axis=1)
        d = d[d > 1e-12]
        best.append(d.min() if len(d) else np.nan)
    return float(np.nanmedian(best))


def _anchor(pos: np.ndarray, theta: float, nx: float, ny: float, spacing: float):
    """A 2D mark -> the SURFACE: splats within eps of the mark's ray, nearest to the eye.
    eps escalates from 3x spacing; if the ray still finds nothing (the eye misses limb
    extremities by 40-100 px, measured 2026-08-18), snap to the closest splat to the ray
    within a bounded 0.25 world units — beyond that the mark is treated as noise."""
    eye, d = _ray(theta, PHI, nx, ny, RADIUS)
    rel = pos - eye
    t = rel @ d
    perp = np.linalg.norm(rel - np.outer(t, d), axis=1)
    valid = t > 0
    eps = 3.0 * spacing
    for _ in range(4):
        sel = (perp < eps) & valid
        if sel.any():
            return pos[sel][t[sel].argmin()]
        eps *= 2.0
    perp_v = np.where(valid, perp, np.inf)
    i = int(perp_v.argmin())
    return pos[i] if perp_v[i] < 0.25 else None


def _plane_fit(pts: np.ndarray):
    """PCA plane through anchored seam points -> (centroid, normal, u, v in-plane basis)."""
    c = pts.mean(0)
    _, _, vt = np.linalg.svd(pts - c, full_matrices=False)
    n = vt[-1] / np.linalg.norm(vt[-1])
    u = vt[0] / np.linalg.norm(vt[0])
    v = np.cross(n, u)
    return c, n, u, v


def _robust_pts(pts: np.ndarray) -> np.ndarray:
    """Trim anchored seam/ring points: the eye's extremity marks carry outliers (measured
    2026-08-18: ankle rings spanning 0.17 world units). Two rounds of median-distance
    trimming (drop beyond 1.5x median) before any plane fit."""
    for _ in range(2):
        if len(pts) < 8:   # small rings need their spread — trimming 5-6 points collapses them
            break
        d = np.linalg.norm(pts - np.median(pts, axis=0), axis=1)
        pts = pts[d <= 1.5 * np.median(d)]
    return pts


def _hull(points2d: np.ndarray):
    """Monotonic-chain convex hull of 2D points -> (m,2) polygon, or None if degenerate."""
    P = sorted(set(map(tuple, points2d)))
    if len(P) < 3:
        return None

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower = []
    for p in P:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper = []
    for p in reversed(P):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return np.array(lower[:-1] + upper[:-1])


# ── STAGE: movie -----------------------------------------------------------------

def stage_movie(splat_path: str, workdir: Path):
    buf = cb.load_splat(splat_path)
    _upload(buf)
    paths = _orbit(workdir, "movie", tag=True)
    (workdir / "movie_meta.json").write_text(json.dumps(
        {"frames": FRAMES, "phi": PHI, "radius": RADIUS,
         "theta": {str(i): _theta(i) for i in range(FRAMES)},
         "orientation": "f08=front f00=back f04=bear's right f12=bear's left"}, indent=1))
    print(f"movie -> {workdir / 'movie'} ({len(paths)} frames, numbered)")


# ── STAGE: mark ------------------------------------------------------------------

_MARK_PROMPT = """You are watching a rotating 3D {subject}: {frames} frames in orbit order, each tagged f00..f{last} in the top-left corner.
Orientation: f08 faces the {subject}'s FRONT, f00 its BACK, f04 its LEFT side, f12 its RIGHT side.
Images are 640x360. All coordinates MUST be normalized 0..1 (divide pixels by 640 and 360), x=0 left edge, y=0 top edge.

Mark the {subject}'s body parts with points, in the frames where each is best visible:
1. "seeds": ONE center point per part, on its best single frame. Parts: {flood}.
2. "rings": 6-10 points tracing a closed ring AROUND each surface feature, on the 1-2 frames where it faces the camera most directly (face features near f08; ears near f04/f12/f08). Features: {rings}.
3. "bands": 6-10 points tracing a closed ring AROUND each joint junction (where two parts meet), on the 1-2 frames where the junction is best seen. Junctions: {bands}.

Output ONLY a JSON object, no markdown, no commentary:
{{"seeds": {{"head": [[frame,x,y]], ...}},
 "rings": {{"eye_left": [[frame,x,y],[frame,x,y],...], ...}},
 "bands": {{"neck": [[frame,x,y],...], ...}}}}
frame is the integer frame index. Skip anything truly not visible, but mark everything you can."""


def _parse_marks(text: str, n_frames: int):
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        return None
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    out = {"seeds": {}, "rings": {}, "bands": {}}
    for kind in out:
        for name, marks in (data.get(kind) or {}).items():
            good = []
            for mk in marks or []:
                try:
                    f, x, y = int(mk[0]), float(mk[1]), float(mk[2])
                except (TypeError, ValueError, IndexError):
                    continue
                if 0 <= f < n_frames and -0.05 <= x <= 1.05 and -0.05 <= y <= 1.05:
                    good.append([f, min(max(x, 0.0), 1.0), min(max(y, 0.0), 1.0)])
            if good:
                out[kind][name] = good
    return out


def stage_mark(splat_path: str, workdir: Path, per_frame: bool, topup: bool, anchor_only: bool,
               subject: str = "teddy bear", rings_only: bool = False):
    frames = sorted((workdir / "movie").glob("f*.png"))
    if len(frames) != FRAMES:
        raise SystemExit("run the movie stage first")
    existing = None
    flood, rings, bands = FLOOD_PARTS, RING_PARTS, BAND_SEAMS
    if rings_only:
        flood, bands = [], []   # the skeleton cut path uses only face rings + spacing
    if anchor_only:
        mp = workdir / "marks2d.json"
        if not mp.exists():
            raise SystemExit("--anchor-only needs an existing marks2d.json (run mark first)")
        existing = json.loads(mp.read_text(encoding="utf-8"))
        flood, rings, bands = [], [], []
    elif topup:
        mp = workdir / "marks2d.json"
        if not mp.exists():
            raise SystemExit("--topup needs an existing marks2d.json (run mark first)")
        existing = json.loads(mp.read_text(encoding="utf-8"))
        flood = [p for p in flood if not existing.get("seeds", {}).get(p)]
        rings = [p for p in rings if not existing.get("rings", {}).get(p)]
        bands = [p for p in bands if not existing.get("bands", {}).get(p)]
        if not (flood or rings or bands):
            print("topup: nothing missing")
        else:
            print(f"topup targets: seeds={flood} rings={rings} bands={bands}")
    prompt = _MARK_PROMPT.format(frames=FRAMES, last=FRAMES - 1, subject=subject,
                                 flood=", ".join(flood) or "(none)",
                                 rings=", ".join(rings) or "(none)",
                                 bands=", ".join(bands) or "(none)")
    if topup:
        prompt += "\nMark ONLY the groups listed above — do not re-mark anything else."
    marks = None
    if not anchor_only and ((flood or rings or bands) or not topup):
        if not per_frame:
            # ONE local call: senses sizes num_ctx to the 16 frames + the answer budget.
            content = [{"type": "text", "text": prompt}]
            for p in frames:
                content.append({"type": "image_url", "image_url": {
                    "url": "data:image/png;base64," + senses._b64(str(p))}})
            raw = senses._post(content, timeout=1800, max_tokens=6000)
            marks = _parse_marks(raw, FRAMES)
            got = sum(len(v) for k in ("seeds", "rings", "bands") for v in (marks or {}).get(k, {}).values())
            print(f"watch(): {got} mark groups parsed")
            need = max(1, min(8, len(flood) + len(rings) + len(bands)))
            if not marks or got < (1 if topup else need):
                print("watch() marks unusable — falling back to per-frame see()")
                marks = None
        if marks is None:
            marks = {"seeds": {}, "rings": {}, "bands": {}}
            for i, p in enumerate(frames):
                raw = senses.see(str(p), prompt + f"\n\nThis is frame f{i:02d}. Mark ONLY what is visible in THIS frame.", timeout=600)
                one = _parse_marks(raw, FRAMES) if raw else None
                if one:
                    for kind in marks:
                        for name, pts in one[kind].items():
                            marks[kind].setdefault(name, []).extend(pts)
                print(f"  f{i:02d}: seeds={len(one['seeds']) if one else 0} rings={len(one['rings']) if one else 0} bands={len(one['bands']) if one else 0}")
    else:
        marks = {"seeds": {}, "rings": {}, "bands": {}}

    if existing:
        for kind in marks:
            for name, pts in marks[kind].items():
                existing.setdefault(kind, {}).setdefault(name, []).extend(pts)
        marks = existing

    (workdir / "marks2d.json").write_text(json.dumps(marks, indent=1), encoding="utf-8")

    # anchor every 2D mark to the splat surface against the exact camera
    pos = cb.load_splat(splat_path)[:, 0:3].astype(np.float64)
    sp = _spacing(pos)
    print(f"splat spacing (median NN): {sp:.5f}")
    marks3d = {"spacing": sp, "seeds": {}, "rings": {}, "bands": {}}
    for kind in ("seeds", "rings", "bands"):
        for name, pts in marks[kind].items():
            anchored = []
            for f, x, y in pts:
                p3 = _anchor(pos, _theta(f), x, y, sp)
                if p3 is not None:
                    anchored.append([round(float(v), 5) for v in p3])
            if anchored:
                marks3d[kind][name] = anchored
        print(f"  {kind}: " + ", ".join(f"{k}({len(v)})" for k, v in marks3d[kind].items()) or "  (none)")
    (workdir / "marks3d.json").write_text(json.dumps(marks3d, indent=1), encoding="utf-8")
    print(f"marks -> {workdir / 'marks2d.json'}, {workdir / 'marks3d.json'}")


# ── STAGE: cut -------------------------------------------------------------------

def _knn_edges(pos: np.ndarray, spacing: float, k: int = 8):
    """kNN graph as CSR-ish edge arrays via a voxel grid (no scipy). Cell = 2x spacing
    guarantees the 27-cell neighborhood covers the k nearest surface neighbors."""
    cell = 2.0 * spacing
    keys = np.floor(pos / cell).astype(np.int32)
    vox: dict[tuple, list[int]] = {}
    for i, kk in enumerate(map(tuple, keys)):
        vox.setdefault(kk, []).append(i)
    ei, ej, ew = [], [], []
    for i in range(len(pos)):
        kk = tuple(keys[i])
        cand = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    cand.extend(vox.get((kk[0] + dx, kk[1] + dy, kk[2] + dz), ()))
        cand = np.asarray(cand, dtype=np.int64)
        d = np.linalg.norm(pos[cand] - pos[i], axis=1)
        keep = cand[d > 1e-12]
        dd = d[d > 1e-12]
        take = np.argsort(dd)[:k]
        for j in keep[take]:
            ei.append(i); ej.append(int(j)); ew.append(float(np.linalg.norm(pos[j] - pos[i])))
    return np.array(ei), np.array(ej), np.array(ew)


def _swap_lr(marks: dict) -> dict:
    """Swap every *_left <-> *_right key. Marks made under the ORIGINAL prompt (which had
    f04/f12 mirrored) are image-relative, i.e. anatomically swapped — measured on the verify
    render 2026-08-18. New marks made with the corrected prompt do NOT need this."""
    out = {}
    for kind, groups in marks.items():
        if not isinstance(groups, dict):
            out[kind] = groups
            continue
        swapped = {}
        for name, pts in groups.items():
            if name.endswith("_left"):
                swapped[name[:-5] + "_right"] = pts
            elif name.endswith("_right"):
                swapped[name[:-6] + "_left"] = pts
            else:
                swapped[name] = pts
        out[kind] = swapped
    return out


def stage_cut(splat_path: str, workdir: Path, swap_lr: bool):
    marks = json.loads((workdir / "marks3d.json").read_text(encoding="utf-8"))
    if swap_lr:
        marks = _swap_lr(marks)

    # symmetry fill: a missing seed (the eye skipped it) is mirrored across x from its L/R
    # pair — the bear is symmetric in T-pose, so this is DERIVED, not guessed.
    for name in FLOOD_PARTS:
        if marks["seeds"].get(name) or "_" not in name:
            continue
        base, side = name.rsplit("_", 1)
        if side not in ("left", "right"):
            continue
        other = base + ("_right" if side == "left" else "_left")
        if marks["seeds"].get(other):
            pts = np.array(marks["seeds"][other], dtype=np.float64)
            pts[:, 0] *= -1.0
            marks["seeds"][name] = [pts.mean(0).tolist()]
            print(f"  seed {name}: mirrored from {other}")
    sp = float(marks["spacing"])
    buf = cb.load_splat(splat_path)
    pos = buf[:, 0:3].astype(np.float64)
    n = len(pos)
    label = np.full(n, -1, dtype=np.int32)
    part_of = {name: i for i, name in enumerate(PARTS)}

    # BODY mask: TripoSplat emits a few hundred giant low-alpha filler splats (mag up to
    # 0.30 vs median 0.002, alpha ~0.02, some floating above the head — measured). They are
    # not sectionable surface: exclude them from rings AND the flood; they keep their
    # original (near-invisible) appearance everywhere downstream.
    mag = np.cbrt(np.maximum(buf[:, 7] * buf[:, 8] * buf[:, 9], 1e-30).astype(np.float64))
    body = mag <= 10.0 * float(np.median(mag))
    print(f"  body mask: {int(body.sum())}/{n} splats (excluded {int((~body).sum())} giant fillers)")

    # (a) RING parts: prism = inside the hull polygon on the ring plane, within a shallow
    # tube. The tube is shallow BY CONSTRUCTION — the single-view z-slab bleed is impossible.
    # Rings are applied SMALLEST-FIRST so a specific feature (nose, mouth) is claimed before
    # the general patch that contains it (muzzle) can steal it — measured: muzzle's prism
    # swallowed the mouth (329 splats -> 0) when applied in spec order.
    ring_geom = {}
    prepped = []
    for name in RING_PARTS:
        pts = _robust_pts(np.array(marks["rings"].get(name, []), dtype=np.float64))
        if len(pts) < 3:
            print(f"  ring {name}: skipped (only {len(pts)} anchored marks)")
            continue
        c, nv, u, v = _plane_fit(pts)
        poly2 = _hull(np.column_stack([(pts - c) @ u, (pts - c) @ v]))
        if poly2 is None:
            print(f"  ring {name}: degenerate polygon, skipped")
            continue
        ring_r = float(np.linalg.norm(np.column_stack([(pts - c) @ u, (pts - c) @ v]), axis=1).mean())
        prepped.append((ring_r, name, c, nv, u, v, poly2))
    for ring_r, name, c, nv, u, v, poly2 in sorted(prepped):
        tube = max(3.0 * sp, 0.6 * ring_r)
        ring_geom[name] = {"centroid": c.tolist(), "normal": nv.tolist(),
                           "ring_radius": ring_r, "tube": tube}
        rel = pos - c
        perp = rel @ nv
        poly = MplPath(poly2)
        inside = poly.contains_points(np.column_stack([rel @ u, rel @ v]))
        sel = inside & (np.abs(perp) < tube) & (label < 0) & body
        label[sel] = part_of[name]
        print(f"  ring {name}: {int(sel.sum())} splats (ring_r={ring_r:.4f}, tube={tube:.4f})")

    # (b) FLOOD parts: multi-source Dijkstra on the kNN graph; edges crossing a band seam
    # near the seam are blocked (big-M weight).
    ei, ej, ew = _knn_edges(pos, sp)
    for name in BAND_SEAMS:
        pts = _robust_pts(np.array(marks["bands"].get(name, []), dtype=np.float64))
        if len(pts) < 3:
            print(f"  band {name}: skipped (only {len(pts)} anchored marks)")
            continue
        c = pts.mean(0)
        a_part, b_part = BAND_PARTS[name]
        sa, sb = marks["seeds"].get(a_part), marks["seeds"].get(b_part)
        if sa and sb:
            axis = np.array(sb, dtype=np.float64).mean(0) - np.array(sa, dtype=np.float64).mean(0)
            nv = axis / np.linalg.norm(axis)
        else:
            _c, nv, _u, _v = _plane_fit(pts)   # no seeds -> fall back to the ring's own fit
        # locality = the BODY's actual cross-section extent at this plane (95th percentile
        # of slab-splat distances + margin), not the eye's ring radius — measured: ring
        # radii under-seal broad junctions (arm_right flooded half the back, 2026-08-18).
        slab = np.abs((pos - c) @ nv) < max(3.0 * sp, 0.02)
        if slab.any():
            r_local = 1.1 * float(np.percentile(np.linalg.norm(pos[slab] - c, axis=1), 95))
        else:
            r_local = 1.3 * float(np.median(np.linalg.norm(pts - c, axis=1)))
        r_local = max(r_local, 4.0 * sp)
        side = ((pos - c) @ nv) > 0
        mid_ok = np.linalg.norm((pos[ei] + pos[ej]) * 0.5 - c, axis=1) < r_local
        cross = (side[ei] != side[ej]) & mid_ok
        ew[cross] *= BARRIER
        print(f"  band {name}: {int(cross.sum())} edges blocked (r_local={r_local:.4f}, "
              f"normal={'seed-axis' if sa and sb else 'ring-fit'})")

    # CSR adjacency
    order = np.argsort(ei, kind="stable")
    ei, ej, ew = ei[order], ej[order], ew[order]
    indptr = np.zeros(n + 1, dtype=np.int64)
    np.add.at(indptr, ei + 1, 1)
    indptr = np.cumsum(indptr)

    free = (label < 0) & body
    dist = np.full(n, np.inf)
    src = np.full(n, -1, dtype=np.int32)
    heap = []
    for name in FLOOD_PARTS:
        pts = np.array(marks["seeds"].get(name, []), dtype=np.float64)
        if not len(pts):
            print(f"  seed {name}: MISSING — part will fall back to nearest other seed")
            continue
        seed3 = pts.mean(0)
        node = int(np.argmin(np.linalg.norm(pos - seed3, axis=1)))
        if not free[node]:            # a ring claimed it; take the nearest FREE node
            node = int(np.argmin(np.linalg.norm(pos - seed3, axis=1) + np.where(free, 0.0, 1e9)))
        dist[node] = 0.0
        src[node] = part_of[name]
        heapq.heappush(heap, (0.0, node))
        print(f"  seed {name}: node {node}")

    while heap:
        d, i = heapq.heappop(heap)
        if d != dist[i] or not free[i]:
            continue
        for e in range(indptr[i], indptr[i + 1]):
            j = ej[e]
            nd = d + ew[e]
            if nd < dist[j]:
                dist[j] = nd
                src[j] = src[i]
                heapq.heappush(heap, (nd, int(j)))

    got = free & (src >= 0)
    label[got] = src[got]
    # anything unreached (barrier-isolated, disconnected): nearest seed by Euclidean
    seeds = [(part_of[nm], np.array(marks["seeds"][nm], dtype=np.float64).mean(0))
             for nm in FLOOD_PARTS if marks["seeds"].get(nm)]
    lost = np.nonzero((label < 0) & body)[0]
    if len(lost) and seeds:
        S = np.array([s[1] for s in seeds])
        idx = np.argmin(np.linalg.norm(pos[lost][:, None, :] - S[None], axis=2), axis=1)
        label[lost] = [seeds[k][0] for k in idx]
    print(f"  flood fallback (nearest seed): {len(lost)} splats")

    np.save(workdir / "part_assignment.npy", label)
    counts = {nm: int((label == i).sum()) for nm, i in part_of.items()}
    (workdir / "parts.json").write_text(json.dumps(
        {"parts": PARTS, "counts": counts, "rings": ring_geom}, indent=1), encoding="utf-8")
    print("counts: " + ", ".join(f"{k}={v}" for k, v in counts.items() if v))
    print(f"cut -> {workdir / 'part_assignment.npy'}")


# ── STICK-FIGURE cut (the operator's pivot, 2026-08-18) ---------------------------
# Body parts = BONES of a measured, symmetric stick figure (stickfigure.py), NOT eye seam
# rings (unreliable on extremities — measured). Seeds = bone midpoints; barriers = joint
# planes (position = the joint, normal = the bone axis, locality = the body's measured
# cross-section at that plane). Only the face keeps its ring prisms (rings worked there).

def _body_mask(buf: np.ndarray) -> np.ndarray:
    """TripoSplat emits a few hundred giant low-alpha filler splats (mag up to 0.30 vs
    median 0.002, alpha ~0.02 — measured). Not sectionable surface; keep them out."""
    mag = np.cbrt(np.maximum(buf[:, 7] * buf[:, 8] * buf[:, 9], 1e-30).astype(np.float64))
    return mag <= 10.0 * float(np.median(mag))


def _apply_rings(marks: dict, pos: np.ndarray, sp: float, label: np.ndarray,
                 body: np.ndarray, part_of: dict) -> dict:
    """Ring prisms, smallest-first so specific features (nose, mouth) are claimed before the
    general patch containing them (muzzle). Shallow tube BY CONSTRUCTION — no z-slab bleed."""
    ring_geom = {}
    prepped = []
    for name in RING_PARTS:
        if name not in part_of:
            continue
        pts = _robust_pts(np.array(marks["rings"].get(name, []), dtype=np.float64))
        if len(pts) < 3:
            print(f"  ring {name}: skipped (only {len(pts)} anchored marks)")
            continue
        c, nv, u, v = _plane_fit(pts)
        poly2 = _hull(np.column_stack([(pts - c) @ u, (pts - c) @ v]))
        if poly2 is None:
            print(f"  ring {name}: degenerate polygon, skipped")
            continue
        ring_r = float(np.linalg.norm(np.column_stack([(pts - c) @ u, (pts - c) @ v]), axis=1).mean())
        prepped.append((ring_r, name, c, nv, u, v, poly2))
    for ring_r, name, c, nv, u, v, poly2 in sorted(prepped):
        tube = max(3.0 * sp, 0.6 * ring_r)
        ring_geom[name] = {"centroid": c.tolist(), "normal": nv.tolist(),
                           "ring_radius": ring_r, "tube": tube}
        rel = pos - c
        perp = rel @ nv
        inside = MplPath(poly2).contains_points(np.column_stack([rel @ u, rel @ v]))
        sel = inside & (np.abs(perp) < tube) & (label < 0) & body
        label[sel] = part_of[name]
        print(f"  ring {name}: {int(sel.sum())} splats (ring_r={ring_r:.4f}, tube={tube:.4f})")
    return ring_geom


def _flood_assign(pos: np.ndarray, sp: float, label: np.ndarray, body: np.ndarray,
                  seeds: dict, barriers: list, part_of: dict) -> np.ndarray:
    """Multi-source Dijkstra on the kNN graph from `seeds` (name -> 3D point); each barrier
    (name, point, normal) blocks edges crossing its plane within the body's measured
    cross-section at that plane (95th pct of slab-splat distances + 10%)."""
    n = len(pos)
    ei, ej, ew = _knn_edges(pos, sp)
    for name, c, nv in barriers:
        slab = np.abs((pos - c) @ nv) < max(3.0 * sp, 0.02)
        r_local = 1.1 * float(np.percentile(np.linalg.norm(pos[slab] - c, axis=1), 95)) \
            if slab.any() else 4.0 * sp
        r_local = max(r_local, 4.0 * sp)
        side = ((pos - c) @ nv) > 0
        mid_ok = np.linalg.norm((pos[ei] + pos[ej]) * 0.5 - c, axis=1) < r_local
        cross = (side[ei] != side[ej]) & mid_ok
        ew[cross] *= BARRIER
        print(f"  barrier {name}: {int(cross.sum())} edges blocked (r_local={r_local:.4f})")

    order = np.argsort(ei, kind="stable")
    ei, ej, ew = ei[order], ej[order], ew[order]
    indptr = np.zeros(n + 1, dtype=np.int64)
    np.add.at(indptr, ei + 1, 1)
    indptr = np.cumsum(indptr)

    free = (label < 0) & body
    dist = np.full(n, np.inf)
    src = np.full(n, -1, dtype=np.int32)
    heap = []
    for name, seed3 in seeds.items():
        node = int(np.argmin(np.linalg.norm(pos - seed3, axis=1) + np.where(free, 0.0, 1e9)))
        dist[node] = 0.0
        src[node] = part_of[name]
        heapq.heappush(heap, (0.0, node))
        print(f"  seed {name}: node {node}")

    while heap:
        d, i = heapq.heappop(heap)
        if d != dist[i] or not free[i]:
            continue
        for e in range(indptr[i], indptr[i + 1]):
            j = ej[e]
            nd = d + ew[e]
            if nd < dist[j]:
                dist[j] = nd
                src[j] = src[i]
                heapq.heappush(heap, (nd, int(j)))

    got = free & (src >= 0)
    label[got] = src[got]
    lost = np.nonzero((label < 0) & body)[0]
    if len(lost) and seeds:
        names = list(seeds)
        S = np.array([seeds[nm] for nm in names])
        idx = np.argmin(np.linalg.norm(pos[lost][:, None, :] - S[None], axis=2), axis=1)
        label[lost] = [part_of[names[k]] for k in idx]
    print(f"  flood fallback (nearest seed): {len(lost)} splats")
    return label


def _write_cut(workdir: Path, label: np.ndarray, parts: list, ring_geom: dict):
    part_of = {name: i for i, name in enumerate(parts)}
    np.save(workdir / "part_assignment.npy", label)
    counts = {nm: int((label == i).sum()) for nm, i in part_of.items()}
    (workdir / "parts.json").write_text(json.dumps(
        {"parts": parts, "counts": counts, "rings": ring_geom}, indent=1), encoding="utf-8")
    print("counts: " + ", ".join(f"{k}={v}" for k, v in counts.items() if v))
    print(f"cut -> {workdir / 'part_assignment.npy'}")


def _symmetrize_eyes(marks: dict):
    """Measured 2026-08-19: the eye's two eye rings anchored asymmetrically (eye_left
    centroid x=-0.042 vs eye_right x=+0.126 — one eye read as 'on the snout' in the verify
    render). A close-up of the face shows the true eyes symmetric at |x|~0.07, y~0.29.
    Same fix as the stick figure (fit()): mirror-average the pair across x=0 and
    synthesize two symmetric rings — pooled evidence, symmetric construction."""
    la = _robust_pts(np.array(marks["rings"].get("eye_left", []), dtype=np.float64).reshape(-1, 3))
    ra = _robust_pts(np.array(marks["rings"].get("eye_right", []), dtype=np.float64).reshape(-1, 3))
    mirror = np.array([-1.0, 1.0, 1.0])
    pool = np.concatenate([p for p in (la, ra * mirror) if len(p)] or [np.zeros((0, 3))])
    if len(pool) < 3:
        return
    if len(la) < 3 or len(ra) < 3:
        print(f"  eye evidence asymmetric (L={len(la)} R={len(ra)}) — pooling what exists")
    c, nv, u, v = _plane_fit(pool)
    if c[0] > 0:                                       # keep the pooled ring on the left
        c, u, v = c * mirror, -u, v

    def _r(pts):                                       # per-ring radius about its OWN centroid
        cc, _n, uu, vv = _plane_fit(pts)
        return float(np.linalg.norm(np.column_stack([(pts - cc) @ uu, (pts - cc) @ vv]), axis=1).mean())
    radii = [_r(p) for p in (la, ra) if len(p) >= 3]
    ring_r = float(np.mean(radii))                     # bead size, NOT the pooled spread
    ang = np.linspace(0.0, 2.0 * np.pi, 8, endpoint=False)
    ring = c + ring_r * (np.cos(ang)[:, None] * u + np.sin(ang)[:, None] * v)
    marks["rings"]["eye_left"] = ring.tolist()
    marks["rings"]["eye_right"] = (ring * mirror).tolist()
    print(f"  symmetrized eyes: |x|={abs(c[0]):.3f} y={c[1]:.3f} z={c[2]:.3f} r={ring_r:.3f}")


def stage_cut_skel(splat_path: str, workdir: Path, skeleton_path: str):
    """Parts = bones of the stick figure via NEAREST-BONE assignment (rigid skinning — the
    same rule skeleton.py assign uses; the graph-flood variant leaked through big-M
    barriers, measured 2026-08-18: barrier locality balls overlapped, thigh_right flooded
    half the body). Tips (hands/feet) = the region beyond the last joint of the arm/shin
    bones. Face features keep their ring prisms."""
    marks = json.loads((workdir / "marks3d.json").read_text(encoding="utf-8"))
    skel = json.loads(Path(skeleton_path).read_text(encoding="utf-8"))
    J = {k: np.array(v, dtype=np.float64) for k, v in skel["joints"].items()}
    species = skel.get("species", "biped")
    if species not in SPECIES_SPECS:
        raise SystemExit(f"unknown skeleton species: {species!r} (known: {sorted(SPECIES_SPECS)})")
    skel_bones, skel_tips, quad_root_plane, skel_parts = SPECIES_SPECS[species]
    print(f"  species: {species} ({len(skel_bones)} bones)")
    need = {j for b in skel_bones for j in b[1:]}
    missing = [j for j in need if j not in J]
    if missing:
        raise SystemExit(f"skeleton is missing joints: {missing}")
    sp = float(marks["spacing"])
    buf = cb.load_splat(splat_path)
    pos = buf[:, 0:3].astype(np.float64)
    parts = skel_parts + RING_PARTS
    part_of = {name: i for i, name in enumerate(parts)}
    label = np.full(len(pos), -1, dtype=np.int32)
    body = _body_mask(buf)
    print(f"  body mask: {int(body.sum())}/{len(pos)} splats (excluded {int((~body).sum())} giant fillers)")

    _symmetrize_eyes(marks)
    ring_geom = _apply_rings(marks, pos, sp, label, body, part_of)

    # nearest-bone over the still-free body splats (segment Voronoi — junctions resolve by
    # geometry: a shoulder splat is simply nearer to the arm bone than to the spine)
    free = (label < 0) & body
    A = np.array([J[a] for _, a, _b in skel_bones])
    B = np.array([J[b] for _, _a, b in skel_bones])
    V = B - A
    L2 = (V * V).sum(1)
    # limb-root plane rule (measured 2026-08-19): a limb claims only splats BEYOND its root
    # joint along the limb axis — without it, the short uparm stub's endpoint sits nearer
    # to the armpit/chest wedge than the spine is, the wedge binds to the arm, and it
    # STREAKS when the arm is posed. (A radial cap failed first: the wedge is contiguous
    # with the arm cylinder, so no percentile of the radial distribution separates it.)
    ROOT_PLANE = {  # bone part -> (root joint, axis: root -> this joint)
        "head": ("neck", "head_center"),
        "uparm_left": ("shoulder_left", "hand_left"), "farm_left": ("shoulder_left", "hand_left"),
        "uparm_right": ("shoulder_right", "hand_right"), "farm_right": ("shoulder_right", "hand_right"),
        "thigh_left": ("hip_center", "knee_left"), "thigh_right": ("hip_center", "knee_right"),
        "shin_left": ("knee_left", "foot_left"), "shin_right": ("knee_right", "foot_right"),
    }
    if quad_root_plane is not None:
        ROOT_PLANE = quad_root_plane
    best = np.full(len(pos), np.inf)
    bone_idx = np.full(len(pos), -1, dtype=np.int32)
    for k, (part, _a, _b) in enumerate(skel_bones):
        W = pos - A[k]
        t = np.clip((W @ V[k]) / L2[k], 0.0, 1.0)
        d = np.linalg.norm(W - t[:, None] * V[k], axis=1)
        elig = free
        if part in ROOT_PLANE:
            rj, aj = ROOT_PLANE[part]
            ax = J[aj] - J[rj]
            ax = ax / float(np.linalg.norm(ax))
            elig = free & (((pos - J[rj]) @ ax) >= 0.0)
            print(f"  root plane {part}: {int((free & ~elig).sum())} splats behind the root excluded")
        upd = elig & (d < best)
        best[upd] = d[upd]
        bone_idx[upd] = k
    for k, (part, _a, _b) in enumerate(skel_bones):
        sel = bone_idx == k
        label[sel] = part_of[part]
        print(f"  bone {part}: {int(sel.sum())} splats")

    # extremity tips: splats on a bone BEYOND its end joint -> the tip part
    for bone, (tip_joint, tip_part) in skel_tips.items():
        k = [i for i, b in enumerate(skel_bones) if b[0] == bone][0]
        axis = B[k] - A[k]
        t = (pos - A[k]) @ axis / float(axis @ axis)
        sel = (label == part_of[bone]) & (t > 1.0)
        label[sel] = part_of[tip_part]
        print(f"  tip {tip_part}: {int(sel.sum())} splats beyond {tip_joint}")

    _write_cut(workdir, label, parts, ring_geom)


# ── STAGES: verify / isolate ------------------------------------------------------

def _colored_buf(splat_path: str, label: np.ndarray, only: int | None, parts: list):
    buf = cb.load_splat(splat_path)
    for i, name in enumerate(parts):
        sel = label == i
        if only is not None:
            buf[sel, 3:6] = PALETTE.get(name, (0.5, 0.5, 0.5))
            buf[sel, 6] = 0.9 if i == only else 0.0
        else:
            buf[sel, 3:6] = PALETTE.get(name, (0.5, 0.5, 0.5))
            buf[sel, 6] = np.maximum(buf[sel, 6], 0.6)
    return buf


def _parts_list(workdir: Path) -> list:
    pj = workdir / "parts.json"
    if pj.exists():
        return json.loads(pj.read_text(encoding="utf-8"))["parts"]
    return PARTS


def stage_verify(splat_path: str, workdir: Path):
    parts = _parts_list(workdir)
    label = np.load(workdir / "part_assignment.npy")
    _upload(_colored_buf(splat_path, label, None, parts))
    frames = _orbit(workdir, "verify", tag=True)
    legend = "; ".join(f"{nm}={'/'.join(str(int(c * 255)) for c in PALETTE.get(nm, (0.5, 0.5, 0.5)))}"
                       for nm, i in enumerate(parts) if (label == i).any())
    prompt = (f"You are watching a rotating 3D teddy bear whose splats are recolored by SECTIONED BODY PART "
              f"(each color = one part; f08=front, f00=back). Color legend (RGB): {legend}.\n"
              "Answer briefly:\n"
              "1. Does each colored region sit where that body part belongs (eyes/nose/muzzle/ears on the head, "
              "arms at the shoulders, hands at arm ends, legs at the hips, feet at leg ends)?\n"
              "2. BLEED: does any color appear where it does NOT belong (e.g. a face color on the back of the head, "
              "arm color inside the torso)? List each bleed. NOTE: on the side views (f04/f12 and neighbors) the "
              "T-pose arms point at/away from the camera, so each arm appears as a small END-ON DISC at the "
              "shoulder — that disc is the hand/forearm seen down its axis, NOT a bleed.\n"
              "3. SPLIT: is any single part broken into disjoint blobs?\n"
              "4. Verdict: PASS (no bleed, no splits, all parts in place) or FAIL (list the defects).")
    content = [{"type": "text", "text": prompt}]
    for p in frames:
        content.append({"type": "image_url", "image_url": {"url": "data:image/png;base64," + senses._b64(p)}})
    verdict = senses._post(content, timeout=1800, max_tokens=2048) or "(eye dark)"
    (workdir / "verdict.txt").write_text(verdict, encoding="utf-8")
    print("VERIFY VERDICT:\n" + verdict)


def stage_isolate(splat_path: str, workdir: Path, part: str):
    parts = _parts_list(workdir)
    if part not in parts:
        raise SystemExit(f"unknown part {part!r}; parts: {parts}")
    label = np.load(workdir / "part_assignment.npy")
    _upload(_colored_buf(splat_path, label, parts.index(part), parts))
    paths = _orbit(workdir, f"isolate_{part}", tag=True)
    print(f"isolate {part} -> {workdir / ('isolate_' + part)} ({len(paths)} frames)")


# ── CLI --------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("stage", choices=["movie", "mark", "cut", "verify", "isolate"])
    ap.add_argument("target", help="path to the ORIGINAL .splat (unpainted)")
    ap.add_argument("--dir", default=None, help="workdir (default: <target stem>_section/)")
    ap.add_argument("--per-frame", action="store_true", help="mark: skip watch(), one see() per frame")
    ap.add_argument("--topup", action="store_true", help="mark: only fill in groups missing from marks2d.json")
    ap.add_argument("--anchor-only", action="store_true", help="mark: re-anchor marks2d.json, no eye calls")
    ap.add_argument("--part", default=None, help="isolate: part name")
    ap.add_argument("--no-swap", action="store_true",
                    help="cut: do NOT swap _left/_right (use for marks made with the corrected prompt)")
    ap.add_argument("--subject", default="teddy bear",
                    help="mark: the animal name the eye sees in the prompt (e.g. 'koala')")
    ap.add_argument("--rings-only", action="store_true",
                    help="mark: ask the eye for face rings only (skeleton cut path needs nothing else)")
    ap.add_argument("--skeleton", default=None,
                    help="cut: STICK-FIGURE path — joints JSON from stickfigure.py/skeleton.py "
                         "(bones instead of eye seam rings)")
    a = ap.parse_args()

    workdir = Path(a.dir) if a.dir else (Path(a.target).with_name(Path(a.target).stem + "_section"))
    workdir.mkdir(parents=True, exist_ok=True)

    if a.stage == "movie":
        stage_movie(a.target, workdir)
    elif a.stage == "mark":
        stage_mark(a.target, workdir, a.per_frame, a.topup, a.anchor_only,
                   subject=a.subject, rings_only=a.rings_only)
    elif a.stage == "cut":
        if a.skeleton:
            stage_cut_skel(a.target, workdir, a.skeleton)
        else:
            stage_cut(a.target, workdir, swap_lr=not a.no_swap)
    elif a.stage == "verify":
        stage_verify(a.target, workdir)
    elif a.stage == "isolate":
        stage_isolate(a.target, workdir, a.part)


if __name__ == "__main__":
    main()
