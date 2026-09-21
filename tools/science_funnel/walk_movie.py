"""walk_movie.py -- the WALKER as a movie: the walk-movie prestage
(lane agent/walk-movie-prestage-20260920).

RULE 0 receipt (pre-registered BEFORE the first render and before any
judgment): tools/science_funnel/validation/walk_movie_20260920/receipt.json.
The judgment vocabulary (gait, body-plan, size/proportion -- the P2 lesson)
is banked in that directory's vocab_bank.json, hash-committed into the
receipt before any judgment file existed; the scorer below (vocab_align) reads
ONLY that bank.

MISSION (lane bank): the gait walker is not at tick 426 yet -- refusal tick 105
is the wave-26 head's honest number. This instrument PRE-STAGES the hour a
walk passes 426: the gait lane's run leaves the same two artifacts consumed
here (the compiled scene JSON + the GAIT_STATE_DUMP full-q stream from this
lane's marked gait_unit_statedump variant, at
tools/science_funnel/walk_movie_20260920/native/), and the movie chain below
runs UNCHANGED -- only --ticks widens. Everything is proven today on the
trace that lives: ticks 60..104, the walk taking steps, then collapsing.

RENDER PATH (the standing law, reused -- not reimplemented):
  ct_skeleton_triangle.post_layer_mesh  -> ONE indexed triangle mesh per frame
     through /mesh_bin (depth-tested, stencil-marking; NO splat route exists
     in this file: the only wire this module sends is verts9+tris -- F1).
  skeleton_movie._set_camera/_settle_capture/_fetch_frame/encode -> the banked
     quiesced-capture + ffmpeg protocol.
  pixel_truth (deterministic, no vision model) -> coverage/grain/clip_scan.
  measure_triangle_monkey.project_points -> the engine camera law for the
     projected hulls.
  workflow_commands.start_engine/stop_engine -> own bind-tested port, the
     operator's live scene refused by code; only own processes stopped (F6).

GEOMETRY LAW: the walker's bodies (pelvis trunk, thigh/shank/foot/toe per hind
leg, upperarm/forearm per fore leg) are placed by THIS FILE's forward
kinematics -- a faithful re-implementation of the engine's Model::evaluate
frame composition (coupled_articulation.hpp: Rodrigues rotation, frame(),
inverse_rigid(), product(), axes in declared order, translation applied at
the motion's origin) -- from the SCENE's own model JSON and the runtime's
dumped state vector q (recipe coordinate order). Segment SHAPES are derived
from the assembly's own attachment points: every segment spans the model's
joint-to-joint line (child joint parent_location_m, contact-point geometry,
Table-1 length for the childless toe); cross-sections are DECLARED
presentation parameters (recorded in the render record). The FK itself is
verified against the engine's own geometry readback (the [dvf] shoulder world
seats of the run trace) to <= 1e-6 m -- F7; a movie of wrong geometry is
refused, not rendered. MEASURED (this lane): max |err| 9.22e-07 m over 90
seat checks (the trace prints 6 decimals; the residual IS the print rounding).

THE ANIMATED-GEOMETRY EXCEPTION (honest note against matter-kernel law 5):
the skeleton movie uploads ONCE per condition and only moves the camera; a
WALK changes geometry every frame, so each frame re-posts its mesh. 45 tiny
meshes (234 verts) at ~0.64 s/frame is the measured cost.

FRAMING (recorded, measured on the first render): ONE translation for the
whole movie -- the union bbox x/z is centred on the orbit origin (the WALK
TRANSLATION IS PRESERVED, never per-frame re-framed) and the body is raised so
its lowest point stands just ABOVE the engine's floor grid, with the camera
target aimed at the raised body's centre. The naive bbox-centre recenter
bisects the body with the grid line -- measured defect, repaired here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

ROOT = Path(__file__).resolve().parents[2]
LANE_DIR = ROOT / "tools/science_funnel/walk_movie_20260920"
VALIDATION = ROOT / "tools/science_funnel/validation/walk_movie_20260920"
TABLE1 = LANE_DIR / "derived_numbers.json"          # the wave-26 pinned Table-1

ENGINE_FOV_Y_DEG = 45.0
CAMERA_MARGIN = 1.35
ORBIT_PHI = 0.35            # a walking-witness elevation (slightly above)
WATCH_WIDTH_PX = 384
FLOOR_STAND_Y = 0.005       # the paw boxes' lowest point above the grid line

# declared presentation cross-sections (metres, radii) -- the LONG axes are
# the model's own attachment points; these are the visual hull's thickness only
SECTION = {"trunk": 0.045, "limb": 0.018, "palm": 0.020, "foot": 0.018,
           "target": 0.006, "marker": 0.012}
# declared warm tints (r>g>b so pixel_truth.warm_mask sees every body)
COLOR = {"trunk": (0.80, 0.60, 0.40), "hind": (0.84, 0.74, 0.56),
         "fore": (0.74, 0.62, 0.46), "paw": (0.58, 0.44, 0.30),
         "palm": (0.62, 0.48, 0.34), "target": (0.90, 0.30, 0.20)}

FK_BAR_M = 1e-6             # F7: rendered geometry == simulated geometry


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ── the FK (a faithful re-implementation of Model::evaluate's frames) ───────

def _skew(v: np.ndarray) -> np.ndarray:
    x, y, z = v
    return np.array([[0., -z, y], [z, 0., -x], [-y, x, 0.]])


def _rotation(axis, angle: float) -> np.ndarray:
    """coupled_articulation.hpp rotation(): I + sin(v) K + (1-cos(v)) K^2."""
    a = np.asarray(axis, dtype=float)
    k = _skew(a)
    return np.eye(3) + math.sin(angle) * k + (1.0 - math.cos(angle)) * (k @ k)


def _frame(p, q) -> np.ndarray:
    """coupled_articulation.hpp frame(): Rx(q0) Ry(q1) Rz(q2), translation p."""
    t = np.eye(4)
    r = np.eye(3)
    for i in range(3):
        axis = np.zeros(3)
        axis[i] = 1.0
        r = r @ _rotation(axis, float(q[i]))
    t[:3, :3] = r
    t[:3, 3] = np.asarray(p, dtype=float)
    return t


def _inverse_rigid(t: np.ndarray) -> np.ndarray:
    out = np.eye(4)
    out[:3, :3] = t[:3, :3].T
    out[:3, 3] = -out[:3, :3] @ t[:3, 3]
    return out


class WalkerFK:
    """Bodies in dependency order; frames exactly as the engine composes them:
    T_body = T_parent @ fixed(parent_location) @ motion @ fixed(child^-1),
    with rotational axes composed in declared order and the accumulated
    translation applied at the motion's origin (the joint frame, not the
    rotated body frame)."""

    def __init__(self, model: dict, coord_order: list):
        self.coord_order = list(coord_order)
        self.slot = {c: i for i, c in enumerate(self.coord_order)}
        bodies = {b["name"]: b for b in model["bodies"]}
        self.order = []                    # (name, parent, fp, fc, axes)
        pending = set(bodies) - {"ground"}
        placed = {"ground"}
        while pending:
            ready = [n for n in sorted(pending)
                     if bodies[n]["joint"]["parent"] in placed]
            if not ready:
                raise ValueError("walk_movie refusal: cyclic_body_hierarchy")
            for n in ready:
                j = bodies[n]["joint"]
                fp = _frame(j["parent_location_m"], j["parent_orientation_rad"])
                fc = _inverse_rigid(
                    _frame(j["child_location_m"], j["child_orientation_rad"]))
                axes = []
                for ax in j["axes"]:
                    f = ax["function"]
                    if f["type"] == "LinearFunction":
                        slope, const = float(f["coefficients"][0]), float(f["coefficients"][1])
                    else:
                        slope, const = 0.0, float(f["coefficients"][0])
                    axes.append({"rotational": ax["name"].startswith("rotation"),
                                 "axis": np.asarray(ax["axis"], dtype=float),
                                 "slot": self.slot.get(ax["coordinate"], -1),
                                 "slope": slope, "const": const})
                self.order.append((n, j["parent"], fp, fc, axes))
                placed.add(n)
                pending.remove(n)

    def frames(self, q) -> dict:
        q = np.asarray(q, dtype=float)
        out = {"ground": np.eye(4)}
        for name, parent, fp, fc, axes in self.order:
            motion = np.eye(4)
            translation = np.zeros(3)
            for ax in axes:
                angle = ax["const"] + (ax["slope"] * q[ax["slot"]]
                                       if ax["slot"] >= 0 else 0.0)
                if ax["rotational"]:
                    r = np.eye(4)
                    r[:3, :3] = _rotation(ax["axis"], angle)
                    motion = motion @ r
                else:
                    translation += ax["axis"] * angle
            motion[:3, 3] = translation
            out[name] = out[parent] @ fp @ motion @ fc
        return out


# ── the segment shapes (the assembly's own attachment points) ────────────────

def segment_spec(scene: dict) -> list:
    """Per-body local segments: (body, family, p0, p1, radius). Endpoints are
    the model's own joint/attachment geometry; nothing is eyeballed."""
    g = scene["gait_controller"]
    model, recipe = g["model"], g["recipe"]
    jpoints = {}                       # parent body -> [child joint anchors]
    for b in model["bodies"]:
        j = b.get("joint")
        if j:
            jpoints.setdefault(j["parent"], []).append(
                np.asarray(j["parent_location_m"], dtype=float))
    cpts = {}                          # body -> contact-point anchors
    for p in recipe["contact_points"]:
        cpts.setdefault(p["body"], []).append(np.asarray(p["point_m"], dtype=float))
    table1 = json.loads(TABLE1.read_text(encoding="utf-8"))["body_model"]["segments_Table1"]
    toe_len = float(table1["phalanges"]["length_m"])

    spec = []
    for side in ("left", "right"):
        spec.append((f"thigh_{side}", "hind",
                     np.zeros(3), jpoints[f"thigh_{side}"][0], SECTION["limb"]))
        spec.append((f"shank_{side}", "hind",
                     np.zeros(3), jpoints[f"shank_{side}"][0], SECTION["limb"]))
        fpts = cpts[f"foot_{side}"]                  # heel + MP head = the sole
        spec.append((f"foot_{side}", "paw", fpts[1], fpts[0], SECTION["foot"]))
        spec.append((f"toe_{side}", "paw",                       # the childless toe
                     np.zeros(3), np.array([toe_len, 0., 0.]), SECTION["foot"]))
        spec.append((f"upperarm_fore_{side}", "fore",
                     np.zeros(3), jpoints[f"upperarm_fore_{side}"][0], SECTION["limb"]))
        hpts = cpts[f"forearm_fore_{side}"]          # the palm line
        spec.append((f"forearm_fore_{side}", "palm",
                     np.zeros(3), np.mean(hpts, axis=0), SECTION["palm"]))
    # the trunk: hip root -> the SHOULDER anchor (the upperarm mounts), the
    # model's own front-limb root (the z sides averaged away)
    ups = [np.asarray(b["joint"]["parent_location_m"], dtype=float)
           for b in model["bodies"] if b["name"].startswith("upperarm")]
    sh = np.mean(ups, axis=0)
    spec.append(("pelvis", "trunk", np.zeros(3), sh, SECTION["trunk"]))
    return spec


def box_verts(p0, p1, radius: float, color):
    """Octagonal prism p0->p1 + cap fans: 18 verts, 40 tris."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    axis = p1 - p0
    L = float(np.linalg.norm(axis))
    if L < 1e-9:
        axis, L = np.array([1., 0., 0.]), 1e-9
    a = axis / L
    ref = np.array([0., 1., 0.]) if abs(a[1]) < 0.9 else np.array([1., 0., 0.])
    u = np.cross(a, ref)
    u /= (np.linalg.norm(u) or 1.0)
    v = np.cross(a, u)
    c = (p0 + p1) / 2.0
    hl = max(L / 2.0, radius)
    ring = 8
    verts: list = []
    lower, upper = [], []
    for k in range(ring):
        th = 2.0 * math.pi * k / ring
        off = radius * (math.cos(th) * u + math.sin(th) * v)
        lower.append(c - a * hl + off)
        upper.append(c + a * hl + off)
    verts.extend(lower)
    verts.extend(upper)
    c0i, c1i = len(verts), len(verts) + 1
    verts.extend([c - a * hl, c + a * hl])
    tris: list = []
    for k in range(ring):
        k2 = (k + 1) % ring
        tris.append((k, k2, ring + k2))
        tris.append((k, ring + k2, ring + k))
        tris.append((c0i, k2, k))                  # lower cap (faces -a)
        tris.append((c1i, ring + k, ring + k2))    # upper cap (faces +a)
    vv = np.asarray(verts, dtype=np.float64)
    cols = np.tile(np.asarray(color, dtype=np.float64), (vv.shape[0], 1))
    return vv, np.asarray(tris, dtype=np.int64), cols


def mesh_normals(verts: np.ndarray, tris: np.ndarray) -> np.ndarray:
    v0, v1, v2 = verts[tris[:, 0]], verts[tris[:, 1]], verts[tris[:, 2]]
    fn = np.cross(v1 - v0, v2 - v0)
    n = np.zeros_like(verts)
    for k in range(3):
        np.add.at(n, tris[:, k], fn)
    ln = np.linalg.norm(n, axis=1, keepdims=True)
    ln[ln == 0] = 1.0
    return n / ln


def frame_mesh(fk_frames: dict, spec: list) -> tuple:
    """One frame's merged indexed mesh: (verts9 [pos3 normal3 color3], tris)."""
    verts, cols, tris, off = [], [], [], 0
    for body, family, p0, p1, radius in spec:
        t = fk_frames[body]
        rv, rt, rc = box_verts(
            t[:3, :3] @ np.asarray(p0, float) + t[:3, 3],
            t[:3, :3] @ np.asarray(p1, float) + t[:3, 3],
            radius, COLOR[family])
        verts.append(rv)
        cols.append(rc)
        tris.append(rt + off)
        off += rv.shape[0]
    v = np.concatenate(verts)
    c = np.concatenate(cols)
    tri = np.concatenate(tris)
    n = mesh_normals(v, tri)
    v9 = np.zeros((v.shape[0], 9), dtype=np.float32)
    v9[:, 0:3] = v
    v9[:, 3:6] = n
    v9[:, 6:9] = c
    return v9, tri.astype(np.uint32).ravel()


# ── the trace-side inputs (engine geometry readback + joint targets) ────────

def parse_trace_dvf(trace_err: Path) -> dict:
    """[dvf] per tick per fore leg: world paw target tgt=(x,y) + the engine's
    own shoulder world seat sh=(x,y)."""
    pat = re.compile(r"\[dvf\] t=(\d+) leg=(\d) mode=\d tgt=\(([-0-9.e+]+),([-0-9.e+]+)\) "
                     r"sh=\(([-0-9.e+]+),([-0-9.e+]+)\)")
    out = {}
    for line in trace_err.read_text(encoding="utf-8", errors="replace").splitlines():
        m = pat.match(line)
        if m:
            t, leg = int(m.group(1)), int(m.group(2))
            d = out.setdefault(t, {"fore_tgt": {}, "sh": {}})
            d["fore_tgt"][leg] = (float(m.group(3)), float(m.group(4)))
            d["sh"][leg] = (float(m.group(5)), float(m.group(6)))
    return out


def parse_trace_dvj(trace_err: Path) -> dict:
    """[dvj] per tick: the eight hind drives' actual + TARGET angles (deg)."""
    pat = re.compile(r"\[dvj\] t=(\d+) k=(\d) ang=(\S+) tgt=(\S+) spd=")
    out = {}
    for line in trace_err.read_text(encoding="utf-8", errors="replace").splitlines():
        m = pat.match(line)
        if m:
            t, k = int(m.group(1)), int(m.group(2))
            out.setdefault(t, [None] * 8)[k] = float(m.group(4))
    return out


# ── vocab_align: the banked-vocabulary scorer (deterministic, no model) ─────

def vocab_align(report: str, bank: dict) -> dict:
    """Score a verbatim report against the BANKED vocabulary only."""
    text = (report or "").lower()
    cats = {}
    for name, cat in bank["categories"].items():
        hits = sorted({s for s in cat["stems"]
                       if re.search(r"\b" + re.escape(s), text)})
        cats[name] = {"hits": hits, "n_hits": len(hits),
                      "n_stems": len(cat["stems"]),
                      "ratio": round(len(hits) / len(cat["stems"]), 4),
                      "required": cat.get("required_for_pass", False)}
    required_ok = all(c["n_hits"] >= 1 for c in cats.values() if c["required"])
    return {"categories": cats,
            "required_categories_hit": required_ok,
            "dark_report": not bool((report or "").strip())}


# ── the judgment: one frame per call, policy lane first, ollama fallback ────

def load_senses():
    sys.path.insert(0, str(ROOT / "ChimeraEngine"))
    os.environ.setdefault("CHIMERA_VISION_URL", "http://localhost:11434")
    os.environ.setdefault("CHIMERA_VISION_MODEL", "qwen3.8")
    # sized so the ollama lane's per-slot context holds prompt + answer
    # (the skeleton-movie lane's measured Ollama parallel-slot lesson)
    os.environ.setdefault("CHIMERA_SENSES_MAX_TOKENS", "768")
    os.environ.setdefault("CHIMERA_SENSES_FRAME_TOKENS", "852")
    import senses
    if senses.available():
        return senses, "policy", senses.dyad_model(), None
    policy_error = "the permanent DYAD policy model is not loaded on the shared server"
    senses.VISION_BACKEND = "ollama"
    return senses, "ollama", senses.VISION_MODEL, policy_error


def judge_frames(senses, lane: str, frames_384: list, prompt: str) -> dict:
    """ONE FRAME PER CALL (the operator's one-image wall), every report
    recorded verbatim in frame order; a dark frame is None, recorded."""
    t0 = time.time()
    per = []
    for p in frames_384:
        try:
            r = senses.watch_one(p, prompt)
        except Exception as e:                                  # noqa: BLE001
            per.append({"frame": p, "report": None,
                        "error": f"{type(e).__name__}: {e}"})
            continue
        per.append({"frame": p, "report": r})
    return {
        "prompt": prompt,
        "lane": lane,
        "model": (senses.dyad_model() if lane == "policy" else senses.VISION_MODEL),
        "protocol": "one frame per call (senses.watch_one); reports joined verbatim "
                    "in frame order; a dark frame is recorded as null",
        "n_frames": len(frames_384),
        "n_dark_frames": sum(1 for x in per if not x.get("report")),
        "per_frame_reports": per,
        "report": "\n\n".join(f"[frame {i + 1}] {x['report']}"
                              for i, x in enumerate(per) if x.get("report")) or None,
        "finish_reason": senses.last_finish_reason(),
        "elapsed_s": round(time.time() - t0, 1),
    }


# ── the render loop (the proven protocol, one mesh POST per frame) ───────────

def _set_camera_targeted(url: str, radius: float, theta: float, phi: float,
                         target: tuple) -> bool:
    """/camera with an explicit target (render_creature's pattern; the mesh
    header carries only r/theta/phi with the implicit origin target)."""
    import urllib.request
    payload = json.dumps({"cam_radius": radius, "cam_theta": theta,
                          "cam_phi": phi, "target_x": target[0],
                          "target_y": target[1], "target_z": target[2]}).encode("utf-8")
    req = urllib.request.Request(url.rstrip("/") + "/camera", data=payload,
                                 headers={"Content-Type": "application/json"},
                                 method="POST")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.status == 200


def watch_path(out_dir: Path, name: str) -> Path:
    w = out_dir / "watch"
    w.mkdir(exist_ok=True)
    return w / name


def render_movie(url: str, meshes: list, camera: dict, out_dir: Path,
                 tag: str) -> dict:
    from tools.science_funnel import ct_skeleton_triangle as cst
    from tools.science_funnel import skeleton_movie as sm
    from PIL import Image

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    target = camera.get("target", (0.0, 0.0, 0.0))
    n = len(meshes)
    paths, hashes, watch_paths = [], [], []
    prev = None
    t0 = time.time()
    for i, (v9, tris) in enumerate(meshes):
        theta = 2.0 * math.pi * (i / (n - 1)) if n > 1 else 0.0
        phi, radius = ORBIT_PHI, camera["radius_m"]
        if i == 0:
            pre = sm._fetch_frame(url)
            if not cst.post_layer_mesh(url, v9, tris, radius, theta, phi):
                raise RuntimeError("walk_movie refusal: mesh_post_refused (/mesh_bin)")
            if not _set_camera_targeted(url, radius, theta, phi, target):
                raise RuntimeError("walk_movie refusal: camera_post_refused")
            b = sm._settle_capture(url, pre)
        else:
            if not _set_camera_targeted(url, radius, theta, phi, target):
                raise RuntimeError("walk_movie refusal: camera_post_refused")
            b = sm._settle_capture(url, prev)
        prev = b
        png = out / f"{tag}_f{i:03d}.png"
        png.write_bytes(b)
        paths.append(str(png))
        hashes.append(sha256(b))
        im = Image.open(png)
        w, h = im.size
        if w > WATCH_WIDTH_PX:
            im = im.resize((WATCH_WIDTH_PX, round(h * WATCH_WIDTH_PX / w)),
                           Image.LANCZOS)
        small = watch_path(out, f"{tag}_f{i:03d}_384.png")
        im.save(small)
        watch_paths.append(str(small))
    return {"tag": tag, "pngs": paths, "watch_384": watch_paths,
            "frame_sha256": hashes, "render_seconds": round(time.time() - t0, 2)}


# ── orchestration ─────────────────────────────────────────────────────────────

def encode_movie_even(frames: list, out_mp4: Path, fps: int) -> str:
    """cpp_bridge.encode_movie's exact ffmpeg recipe with one addition: a crop
    to even dimensions. MEASURED (this lane): the engine renders 2560x1369 --
    an ODD height -- and libx264 yuv420p refuses odd dimensions ("Could not
    open encoder before EOF"); the crop drops the last pixel row/column.
    cpp_bridge.py itself stays byte-untouched."""
    import subprocess
    out_mp4 = Path(out_mp4)
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-y", "-framerate", str(fps),
           "-i", "%s", "-vf", "crop=trunc(iw/2)*2:trunc(ih/2)*2",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", str(out_mp4)]
    # frame list -> a concat-safe temp sequence (cpp_bridge's own pattern)
    import shutil, tempfile
    with tempfile.TemporaryDirectory() as td:
        for i, f in enumerate(frames):
            shutil.copy(f, Path(td) / f"f{i:04d}.png")
        cmd[5] = str(Path(td) / "f%04d.png")
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"walk_movie: ffmpeg failed: {r.stderr[-500:]}")
    return str(out_mp4)


def build_meshes(states: dict, ticks: list, fk: WalkerFK, spec: list):
    """Merged per-frame meshes + the movie framing (see module docstring)."""
    meshes, all_v, frames_fk = [], [], []
    for t in ticks:
        fr = fk.frames(states[t])
        frames_fk.append(fr)
        v9, tris = frame_mesh(fr, spec)
        meshes.append((v9, tris))
        all_v.append(v9[:, 0:3].astype(np.float64).copy())
    union = np.concatenate(all_v)
    umin, umax = union.min(axis=0), union.max(axis=0)
    center = (umin + umax) / 2.0
    lift = FLOOR_STAND_Y - float(umin[1] - center[1])   # paws onto the grid line
    for v9, _ in meshes:
        v9[:, 0:3] -= center.astype(np.float32)   # ONE translation: the walk
        v9[:, 1] += np.float32(lift)              # ...then raised onto the grid
    target = (0.0, float((umax[1] - umin[1]) / 2.0 + FLOOR_STAND_Y), 0.0)
    return meshes, all_v, frames_fk, center, lift, target


def overlay_meshes(scene: dict, states: dict, ticks: list, fk: WalkerFK,
                   spec: list, targets: dict, meshes: list, lift: float):
    """Targets-vs-actuals diagnostic: the hind TARGET pose as thin sticks
    (FK of the dumped [dvj] target angles) + fore paw world-target markers
    (the [dvf] tgt seats) added to each frame's actual mesh."""
    pi = math.pi
    out = []
    hind_joints = [c for c in scene["gait_controller"]["recipe"]["drives"]
                   if c["leg"] in ("left", "right")]
    for i, t in enumerate(ticks):
        v9, tris = meshes[i]
        chunks_v, chunks_t, off = [v9.copy()], [tris.copy()], int(v9.shape[0])

        def add(p0w, p1w, radius, color):
            nonlocal off
            vv, tt, rc = box_verts(np.asarray(p0w, float),
                                   np.asarray(p1w, float), radius, color)
            block = np.zeros((vv.shape[0], 9), dtype=np.float32)
            block[:, 0:3] = vv.astype(np.float32)
            block[:, 6:9] = rc.astype(np.float32)
            block[:, 1] += np.float32(lift)
            chunks_v.append(block)
            chunks_t.append((tt + off).astype(np.uint32).ravel())
            off += vv.shape[0]

        tgt = targets.get(t, {})
        hind_tgt = tgt.get("hind_tgt") or []
        if any(h is not None for h in hind_tgt):
            q = np.array(states[t], dtype=float)
            for k, dr in enumerate(hind_joints):
                if k < len(hind_tgt) and hind_tgt[k] is not None:
                    q[fk.slot[dr["coordinate"]]] = hind_tgt[k] * pi / 180.0
            fr_t = fk.frames(q)
            for body, family, p0, p1, _r in spec:
                if family != "hind":        # the target sticks: thigh + shank
                    continue
                tf = fr_t[body]
                add(tf[:3, :3] @ p0 + tf[:3, 3], tf[:3, :3] @ p1 + tf[:3, 3],
                    SECTION["target"], COLOR["target"])
        plane_y = float(scene["gait_controller"]["recipe"]["contact_plane_height_m"])
        for leg, (x, y) in (tgt.get("fore_tgt") or {}).items():
            zc = 0.03 if leg == 0 else -0.03
            p = np.array([x, plane_y, zc])
            add(p, p + np.array([0.004, 0.0, 0.0]), SECTION["marker"],
                COLOR["target"])
        v9o = np.concatenate(chunks_v)
        triso = np.concatenate(chunks_t)
        n = mesh_normals(v9o[:, 0:3].astype(np.float64),
                         triso.reshape(-1, 3).astype(np.int64))
        v9o[:, 3:6] = n
        out.append((v9o, triso))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--from-states", type=Path, required=True,
                    help="states.jsonl from gait_unit_statedump (GAIT_STATE_DUMP)")
    ap.add_argument("--scene", type=Path, required=True,
                    help="the compiled gait scene JSON")
    ap.add_argument("--trace", type=Path, default=None,
                    help="the run's stderr trace (FK verification + overlay targets)")
    ap.add_argument("--ticks", default="60:104", help="inclusive tick window")
    ap.add_argument("--stride", type=int, default=1)
    ap.add_argument("--fps", type=int, default=12)
    ap.add_argument("--engine", default=None, help="engine URL; default self-start one")
    ap.add_argument("--engine-exe", default=str(Path(
        "E:/ChimeraWork/mcp-agent/.tmp/wfmcp_build/Release/chimera_engine.exe")))
    ap.add_argument("--out", type=Path, required=True,
                    help="scratch dir for frames/mp4 (keep bulk off the full E: drive)")
    ap.add_argument("--no-judge", action="store_true")
    ap.add_argument("--judge-only", action="store_true",
                    help="frames already rendered: judge + score only, no engine")
    ap.add_argument("--overlay", action="store_true",
                    help="also render the targets-vs-actuals diagnostic movie")
    args = ap.parse_args(argv)

    # F1 TRIANGLE CONFORMANCE (checked, recorded): the only engine upload in
    # this instrument is /mesh_bin through ct_skeleton_triangle.post_layer_mesh;
    # the splat route must be unreachable from this file. Checked over the
    # module's AST string constants (the check composes its own target token so
    # it never carries the thing it refuses).
    import ast as _ast
    tree = _ast.parse(Path(__file__).read_text(encoding="utf-8"))
    consts = " ".join(n.value for n in _ast.walk(tree)
                      if isinstance(n, _ast.Constant) and isinstance(n.value, str))
    bad = "mem" + "brane_bin"
    f1_ok = bad not in consts and "post_layer_mesh" in consts
    print(f"[0/6] F1 triangle conformance: splat route unreachable = {f1_ok}",
          flush=True)
    if not f1_ok:
        raise SystemExit("walk_movie refusal: conformance_splat_route_reachable")

    from tools.science_funnel import pixel_truth as pt
    from tools.science_funnel import skeleton_movie as sm
    from tools.science_funnel import measure_triangle_monkey as mtm

    args.out.mkdir(parents=True, exist_ok=True)
    scene = json.loads(args.scene.read_text(encoding="utf-8"))
    g = scene["gait_controller"]
    coord_order = list(g["recipe"]["coordinates"])
    spec = segment_spec(scene)
    fk = WalkerFK(g["model"], coord_order)

    states = {}
    for line in args.from_states.read_text(encoding="utf-8").splitlines():
        if line.strip():
            s = json.loads(line)
            states[int(s["tick"])] = s["q"]
    lo, hi = (int(x) for x in args.ticks.split(":"))
    ticks = [t for t in range(lo, hi + 1) if t in states][::max(1, args.stride)]
    if not ticks:
        raise SystemExit("walk_movie refusal: no states in the requested window")
    print(f"[1/6] FK on {len(ticks)} states (ticks {ticks[0]}..{ticks[-1]})...",
          flush=True)

    dvf = dvj = None
    if args.trace and args.trace.is_file():
        dvf = parse_trace_dvf(args.trace)
        dvj = parse_trace_dvj(args.trace)
        # F7: the FK is the engine's geometry -- verify against its own readback
        errs = []
        for t in ticks:
            if t not in dvf:
                continue
            fr = fk.frames(states[t])
            for leg, body in ((0, "upperarm_fore_left"), (1, "upperarm_fore_right")):
                if leg in dvf[t]["sh"]:
                    world = fr[body][:3, 3]
                    sx, sy = dvf[t]["sh"][leg]
                    errs.append(abs(world[0] - sx) + abs(world[1] - sy))
        fk_max_err = max(errs) if errs else None
        print(f"    FK vs engine shoulder seats: max|err| = {fk_max_err} m "
              f"({len(errs)} checks)", flush=True)
        if fk_max_err is None or fk_max_err > FK_BAR_M:
            raise SystemExit(f"walk_movie refusal: FK_verification_failed "
                             f"({fk_max_err} vs bar {FK_BAR_M} m) -- refusing to "
                             "render geometry that is not the simulation's")
    else:
        fk_max_err = None

    meshes, all_v, frames_fk, center, lift, target = build_meshes(
        states, ticks, fk, spec)
    union = np.concatenate(all_v)
    cam = sm.derive_camera(union - center)
    cam["target"] = [round(float(v), 6) for v in target]
    cam["framing"] = ("union bbox x/z centred on the orbit origin (the walk "
                      "translation preserved); body raised "
                      f"{round(lift, 4)} m so the paws stand at y={FLOOR_STAND_Y} "
                      "above the grid; camera target at the raised body centre")
    print(f"    vertices={meshes[0][0].shape[0]} triangles={meshes[0][1].size // 3} "
          f"radius={cam['radius_m']} bbox_h={cam['bbox_height_m']} "
          f"target_y={target[1]:.4f}", flush=True)

    overlay_run = None
    if args.judge_only:
        run = {"watch_384": sorted(str(p) for p in (args.out / "watch").glob(
            "walk_f*_384.png"))}
    else:
        handle = None
        if args.engine:
            url = args.engine
        else:
            from tools.science_funnel import workflow_commands as wc
            handle = wc.start_engine(args.engine_exe)
            url = handle.url
            print(f"[2/6] engine self-started: {url} (exe sha256 "
                  f"{(handle.exe_sha256 or '')[:16]}...)", flush=True)
        try:
            print(f"[3/6] rendering {len(meshes)} frames through /mesh_bin...",
                  flush=True)
            run = render_movie(url, meshes, cam, args.out, "walk")
            print(f"    {run['render_seconds']}s, {len(run['pngs'])} frames",
                  flush=True)
            if args.overlay and dvf is not None:
                targets = {t: {"hind_tgt": (dvj or {}).get(t),
                               "fore_tgt": dvf[t]["fore_tgt"] if t in dvf else {}}
                           for t in ticks}
                om = overlay_meshes(scene, states, ticks, fk, spec, targets,
                                    meshes, lift)
                overlay_run = render_movie(url, om, cam,
                                           args.out.parent / "movie_overlay", "walko")
                print(f"    overlay movie: {len(overlay_run['pngs'])} frames "
                      f"({overlay_run['render_seconds']}s)", flush=True)
        finally:
            if handle is not None:
                from tools.science_funnel import workflow_commands as wc
                wc.stop_engine(handle)

        print("[4/6] pixel_truth on the frames...", flush=True)
        counts, touches, covs, grains = [], [], [], []
        for i, png in enumerate(run["pngs"]):
            img = pt.load(png)
            m = pt.warm_mask(img)
            counts.append(int(m.sum()))
            touches.append(pt.boundary_touch(m))
            theta = 2.0 * math.pi * (i / (len(meshes) - 1)) if len(meshes) > 1 else 0.0
            pos = all_v[i] - center
            pos = pos + np.array([0.0, lift, 0.0])   # the ACTUAL rendered coords
            hull_pts = mtm.project_points(pos, cam["radius_m"],
                                          theta, ORBIT_PHI,
                                          img.shape[1], img.shape[0],
                                          target=target)
            covs.append(pt.coverage(m, pt.hull_mask(hull_pts, img.shape))["coverage"])
            grains.append(pt.grain(img, m)["grain_median_local_variance"])
        scan = pt.clip_scan(counts, touches)
        print(f"    coverage min/med/max = {min(covs)}/"
              f"{sorted(covs)[len(covs) // 2]}/{max(covs)}  clip={scan['clip']}",
              flush=True)
        mp4 = args.out / "walk_movie.mp4"
        encode_movie_even(run["pngs"], mp4, fps=args.fps)
        mp4_sha = sha256(mp4.read_bytes())
        print(f"    mp4 sha256 {mp4_sha[:16]}... ({mp4.stat().st_size} bytes)",
              flush=True)
        record = {
            "schema": "chimera.walk_movie.render.v1", "taken_utc": now_utc(),
            "lane": "agent/walk-movie-prestage-20260920",
            "scene": {"path": str(args.scene),
                      "sha256": sha256(args.scene.read_bytes())},
            "states": {"path": str(args.from_states),
                       "sha256": sha256(args.from_states.read_bytes()),
                       "window": [ticks[0], ticks[-1]], "n": len(ticks),
                       "stride": args.stride},
            "f1_conformance": {"splat_route_unreachable": f1_ok,
                               "rule": "no splat-endpoint string constant in the "
                                       "module AST; the sole uploader is "
                                       "post_layer_mesh (/mesh_bin)"},
            "fk": {"max_err_m": fk_max_err, "bar_m": FK_BAR_M,
                   "checks": "engine [dvf] shoulder world seats, per tick",
                   "note": "the walk refuses at tick 105: the window ends at the "
                           "last living state, 104 (the movie of a walk attempt "
                           "is itself the honest visual)"},
            "mesh": {"vertices": int(meshes[0][0].shape[0]),
                     "triangles": int(meshes[0][1].size // 3),
                     "segments": [s[0] for s in spec],
                     "endpoint_sources": "child joint parent_location_m / "
                                         "contact-point anchors / Table-1 toe length",
                     "sections_declared_m": SECTION, "colors_declared": COLOR},
            "camera": cam,
            "fps": args.fps,
            "frames": {"pngs": run["pngs"],
                       "frame_sha256": run["frame_sha256"],
                       "render_seconds": run["render_seconds"]},
            "pixel_truth": {"coverage_per_frame": covs,
                            "grain_per_frame": grains,
                            "clip_scan": scan},
            "mp4": {"path": str(mp4), "sha256": mp4_sha,
                    "bytes": mp4.stat().st_size},
            "overlay": ({"pngs": overlay_run["pngs"],
                         "frame_sha256": overlay_run["frame_sha256"],
                         "note": "targets-vs-actuals diagnostic: hind target-pose "
                                 "sticks + fore paw world-target markers; NOT the "
                                 "judged movie"}
                        if overlay_run else None),
        }
        (VALIDATION / "render_record.json").write_text(
            json.dumps(record, indent=1) + "\n", encoding="utf-8")
        if args.no_judge:
            print("done (--no-judge)", flush=True)
            return 0

    print("[5/6] judging (one frame per call)...", flush=True)
    senses, lane, model_id, policy_error = load_senses()
    print(f"    lane: {lane} model: {model_id}", flush=True)
    watch_stride = max(1, len(run["watch_384"]) // 12)
    watch = run["watch_384"][::watch_stride][:12]
    judgment = judge_frames(senses, lane, watch, sm.JUDGE_PROMPT)
    judgment.update({"lane_note": "policy lane = the permanent DYAD model "
                    "(one frame per call); ollama lane = the skeleton-movie "
                    "lane's documented fallback (qwen3.8, think:false, num_ctx "
                    "sized), same one-image wall",
                    "policy_lane_error": policy_error, "frames_used": watch})
    (VALIDATION / "judgement.json").write_text(
        json.dumps(judgment, indent=1) + "\n", encoding="utf-8")
    print("    ->", (judgment["report"] or "DARK")[:280].replace("\n", " "),
          flush=True)

    print("[6/6] vocab_align against the banked vocabulary...", flush=True)
    bank = json.loads((VALIDATION / "vocab_bank.json").read_text(encoding="utf-8"))
    agg = vocab_align(judgment["report"], bank)
    per = [vocab_align(x["report"], bank)
           for x in judgment["per_frame_reports"] if x.get("report")]
    scores = {
        "aggregated_report": agg,
        "per_frame_required_hit_rate": (round(sum(1 for s in per
                                                  if s["required_categories_hit"])
                                               / len(per), 4) if per else None),
        "bank_sha256": sha256((VALIDATION / "vocab_bank.json").read_bytes()),
        "scorer": "vocab_align: word-prefix stem match over the bank ONLY; "
                  "deterministic string arithmetic, no model",
    }
    (VALIDATION / "vocab_scores.json").write_text(
        json.dumps(scores, indent=1) + "\n", encoding="utf-8")
    cats = scores["aggregated_report"]["categories"]
    print(json.dumps({"lane": lane, "model": model_id,
                      "required_categories_hit": agg["required_categories_hit"],
                      "gait_hits": cats["gait"]["hits"],
                      "body_hits": cats["body_plan"]["hits"],
                      "size_hits": cats["size_proportion"]["hits"],
                      "collapse_hits": cats["posture_collapse"]["hits"]}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
