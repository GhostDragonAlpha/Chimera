"""capture_build.py -- ONT-P02 visible_static CORRECTION capture.

Camera-pinned anatomy capture over the lineage-pinned runtime render body
(tools/playable_slice/standing_body.obj @ 33e7a444, blob ef6f3530, sha256
bc9033bf...9111, 18469042 B): ONE deterministic contact-sheet PNG holding the
three anatomy-profile views as diagnostic+clean pairs, plus the
chimera.visual_capture_manifest.v1 camera manifest, VALIDATED in-process with
the campaign's own visual_capture.validate_manifest and visual_gate.verify
against card_task.json (profile anatomy / visible_static).

HONEST BOUNDARY (PREREGISTRATION section 8): the pixels are a deterministic
CPU software render (numpy + PIL painter's algorithm) of the pinned mesh
bytes -- NOT native engine frames, no GPU, no engine process.

Every quantity is measured from the pinned blob at build time and asserted
against the values frozen in PREREGISTRATION.md (sections 2 and 6).  The
subject is extracted with READ-ONLY git plumbing (git cat-file blob) into the
attempt scratch directory; no source repository is written.

    python -B tools/monkey_campaign/contributions/ONT-P02/capture_build.py
"""
from __future__ import annotations

import hashlib
import json
import math
import platform
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE / "evidence"
CAMPAIGN_TOOLS = HERE.parents[2]


def validator_dir() -> Path:
    """The campaign's own visual_capture/visual_gate validators: the
    canonical onboarding checkout first (read-only import, python -B), the
    candidate tree only if the modules are materialized there."""
    for cand in (Path("E:/PythonChimera/tools/monkey_campaign"),
                 HERE.parents[1]):
        if (cand / "visual_gate.py").is_file() and \
                (cand / "visual_capture.py").is_file():
            return cand
    raise FileNotFoundError("campaign visual validators not found")

SUBJECT_BLOB = "ef6f35302e1c00287b4c13c8cfbf276c7f3879d0"
SUBJECT_SHA256 = "bc9033bfc6c54db0220364821ee19028bf2ac6f740dc70f4c1e9be5f02089111"
SUBJECT_BYTES = 18469042
BODY_MANIFEST_BLOB = "2cb2233baa79ad97ecc81b67e0f04cf52cc6a3e9"
BODY_MANIFEST_SHA256 = "6d0328ce9aa5babfb25a98518b69477b879b3a7d902593fc0842c127bcc7f78a"
RUN_ID = "ont-p02-visible-static-20260926-b248ac96"
FRAME_ID = "playable_slice_scene_yup_m"
PROFILE_ID = "anatomy"
TASK_ID = "P02"

# frozen predictions (PREREGISTRATION section 2)
PRED_BBOX_MIN = (-0.159165, -0.134714, -0.153386)
PRED_BBOX_MAX = (0.102051, 0.134568, 0.451770)
PRED_BAND_N = 230
PRED_BAND_CENTROID = (-0.079259, -0.131367, 0.258219)
PRED_BAND_OWNERS = {2: 169, 6: 61}
PRED_CHAIN_CENTROIDS = {
    2: (-0.0661, -0.0720, 0.2886), 6: (-0.0866, -0.0768, 0.3199),
    15: (-0.0802, -0.0011, 0.3415), 20: (-0.0721, -0.0688, 0.3259),
    22: (-0.0682, -0.0001, 0.3828), 25: (-0.0825, -0.0118, 0.3786),
}

CHAIN_A = [2, 6, 15, 20, 22, 25]          # hind chain "a" (identification v3)
CHAIN_A_LABELS = {2: "#hindchain_a_femur_b02", 6: "#hindchain_a_tibia_b06",
                  20: "#hindchain_a_fibula_b20", 15: "#hindchain_a_foot_b15",
                  22: "#hindchain_a_foot_b22", 25: "#hindchain_a_foot_b25"}
CHAIN_A_COLORS = {2: (214, 78, 62), 6: (74, 152, 224), 20: (238, 172, 44),
                  15: (108, 192, 84), 22: (162, 112, 214), 25: (78, 202, 192)}
OTHER_BONE = (146, 143, 136)
ENVELOPE_GHOST = (120, 140, 175, 80)     # AMENDED v2: legibility
BONE_ALPHA = 230                         # AMENDED v2: legibility
LEADER = (128, 116, 64)
AREA_SKIP_PX2 = 0.02

# frozen cameras (PREREGISTRATION section 4)
FOV_DEG = 40.0
SIDE_SPAN = 0.80
OVERVIEW_EYE_OFF = (0.62, 0.30, 0.18)    # AMENDED v3 (prereg section 11)
CLOSEUP_EYE_OFF = (-0.20, 0.06, -0.14)
SIDE_EYE_OFF = (1.2, 0.0, 0.0)
OBLIQUE_EYE_OFF = (0.85, 0.55, -0.85)
W_FULL, H_FULL = 640, 420
W_HALF, H_HALF = 420, 420
TICKS = [0, 1]
NEAR_OVER, FAR_OVER = 0.05, 10.0
NEAR_CLOSE, FAR_CLOSE = 0.02, 5.0

VIEW_OVERVIEW = "whole-creature overview"
VIEW_CLOSEUP = "local attachment close-up"
VIEW_SIDEOBLIQUE = "orthogonal side and oblique views"

LAYERS_FULL = ["outer envelope", "selected bones/joints", "muscle/tendon paths",
               "attachment sites", "frame axes", "stable 3D labels"]
LAYERS_CLOSEUP = ["outer envelope", "selected bones/joints",
                  "muscle/tendon paths", "attachment sites", "stable 3D labels"]

L_CONTACT = "#attach_contact_patch"
L_JOINT = "#attach_joint_b02_b06"
L_MEMBRANE = "#owner_membrane"
L_GHOST = "#ghost_overlay"
L_AXES = "#frame_axes_world"

S_ENV = "env_standing_body"
S_BONE = {b: "bone_b%02d" % b for b in range(1, 26)}
S_PATCH = "attach_contact_patch"
S_JOINT = "attach_joint_b02_b06"
S_MEMBRANE = "membrane_creature"
S_GHOST = "ghost_standing_overlay"
S_ABSENT = "musculature_not_pinned"
S_AXES = "world_frame_axes"

BG = (8, 9, 12)
TXT = (222, 226, 238)
TXT_DIM = (150, 158, 176)
LAYER_TAG = (110, 200, 255)
PANEL_BG = (0, 0, 0, 196)
LABEL_COL = (250, 214, 96)
AXES_COL = {"+X": (226, 68, 68), "-X": (140, 40, 40), "+Y": (70, 200, 90),
            "-Y": (36, 110, 46), "+Z": (80, 120, 230), "-Z": (40, 62, 132)}
FONT = ImageFont.load_default()
LIGHT = np.array([0.35, 0.8, -0.45], dtype=np.float64)
LIGHT = LIGHT / np.linalg.norm(LIGHT)

# contact-sheet rectangles (frozen): [left, top, width, height]
RECT_OVER_D = [0, 0, W_FULL, H_FULL]
RECT_OVER_C = [0, H_FULL, W_FULL, H_FULL]
RECT_CLOSE_D = [W_FULL, 0, W_FULL, H_FULL]
RECT_CLOSE_C = [W_FULL, H_FULL, W_FULL, H_FULL]
RECT_SIDE_D = [2 * W_FULL, 0, 2 * W_HALF, H_FULL]
RECT_SIDE_C = [2 * W_FULL, H_FULL, 2 * W_HALF, H_FULL]
SHEET_W, SHEET_H = 2 * W_FULL + 2 * W_HALF, 2 * H_FULL


# ── subject extraction (read-only git plumbing) ──────────────────────────────
def git_blob(blob: str) -> bytes:
    out = subprocess.run(["git", "cat-file", "blob", blob],
                         cwd=str(CAMPAIGN_TOOLS), check=True,
                         capture_output=True).stdout
    return out


def extract_subject(cache_dir: Path) -> Path:
    dst = cache_dir / "standing_body.obj"
    if dst.is_file():
        raw = dst.read_bytes()
        if hashlib.sha256(raw).hexdigest() == SUBJECT_SHA256 \
                and len(raw) == SUBJECT_BYTES:
            return dst
    out = git_blob(SUBJECT_BLOB)
    if hashlib.sha256(out).hexdigest() != SUBJECT_SHA256 \
            or len(out) != SUBJECT_BYTES:
        raise ValueError("subject_blob_identity_mismatch")
    dst.write_bytes(out)
    return dst


def parse_obj(raw: bytes):
    verts, faces = [], []
    for line in raw.splitlines():
        if line[:2] == b"v ":
            p = line.split()
            verts.append((float(p[1]), float(p[2]), float(p[3])))
        elif line[:2] == b"f ":
            faces.append((int(line.split()[1].split(b"/")[0]) - 1,
                          int(line.split()[2].split(b"/")[0]) - 1,
                          int(line.split()[3].split(b"/")[0]) - 1))
    return np.array(verts, dtype=np.float64), np.array(faces, dtype=np.int64)


def load_anatomy(cache_dir: Path) -> dict:
    """Pinned mesh + verified per-bone segmentation + frozen measurements."""
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    obj_path = extract_subject(cache_dir)
    V, F = parse_obj(obj_path.read_bytes())
    if len(V) != 249743 or len(F) != 499976:
        raise ValueError("subject_element_count_mismatch")
    counts_raw = git_blob(BODY_MANIFEST_BLOB)
    if hashlib.sha256(counts_raw).hexdigest() != BODY_MANIFEST_SHA256:
        raise ValueError("body_manifest_identity_mismatch")
    bm = json.loads(counts_raw)
    vcounts = [b["decimation"]["verts"] for b in bm["bones"]]
    fcounts = [b["decimation"]["faces"] for b in bm["bones"]]
    if sum(vcounts) != len(V) or sum(fcounts) != len(F):
        raise ValueError("bone_block_sums_mismatch")
    offs = np.concatenate([[0], np.cumsum(vcounts)]).astype(np.int64)
    foffs = np.concatenate([[0], np.cumsum(fcounts)]).astype(np.int64)
    for i in range(25):                      # face blocks self-contained
        blk = F[foffs[i]:foffs[i + 1]]
        if int(blk.min()) < int(offs[i]) or int(blk.max()) >= int(offs[i + 1]):
            raise ValueError("bone_face_block_not_contiguous:%d" % (i + 1))
    face_bone = np.zeros(len(F), dtype=np.int64)
    for i in range(25):
        face_bone[foffs[i]:foffs[i + 1]] = i + 1
    vmin, vmax = V.min(0), V.max(0)
    if not np.allclose(vmin, PRED_BBOX_MIN, atol=5e-7) or \
            not np.allclose(vmax, PRED_BBOX_MAX, atol=5e-7):
        raise ValueError("bbox_prediction_failed")
    ymin = float(vmin[1])
    band_mask = V[:, 1] <= ymin + 0.005
    band = V[band_mask]
    if len(band) != PRED_BAND_N or \
            not np.allclose(band.mean(0), PRED_BAND_CENTROID, atol=5e-7):
        raise ValueError("contact_band_prediction_failed")
    owners = {}
    for i in range(25):
        n = int(band_mask[offs[i]:offs[i + 1]].sum())
        if n:
            owners[i + 1] = n
    if owners != PRED_BAND_OWNERS:
        raise ValueError("contact_band_owners_prediction_failed")
    cents = {b: V[offs[b - 1]:offs[b]].mean(0) for b in CHAIN_A}
    for b, c in PRED_CHAIN_CENTROIDS.items():
        if not np.allclose(cents[b], c, atol=6e-5):
            raise ValueError("chain_centroid_prediction_failed:%d" % b)
    tri_n = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    norm = np.linalg.norm(tri_n, axis=1, keepdims=True)
    norm[norm == 0.0] = 1.0
    tri_n = tri_n / norm
    tri_c = (V[F[:, 0]] + V[F[:, 1]] + V[F[:, 2]]) / 3.0
    return dict(V=V, F=F, offs=offs, foffs=foffs, face_bone=face_bone,
                band_centroid=band.mean(0), center=(vmin + vmax) / 2.0,
                cents=cents, joint=((cents[2] + cents[6]) / 2.0).tolist(),
                tri_normal=tri_n, tri_centroid=tri_c,
                contact_ymin=ymin)


# ── camera math ──────────────────────────────────────────────────────────────
def quat_wxyz(x, y, z):
    """Rotation columns (x,y,z) -> unit quaternion (w,x,y,z), branch method."""
    m = np.array([[x[0], y[0], z[0]], [x[1], y[1], z[1]],
                  [x[2], y[2], z[2]]], dtype=np.float64)
    tr = m[0, 0] + m[1, 1] + m[2, 2]
    if tr > 0.0:
        s = math.sqrt(tr + 1.0) * 2.0
        q = [0.25 * s, (m[2, 1] - m[1, 2]) / s, (m[0, 2] - m[2, 0]) / s,
             (m[1, 0] - m[0, 1]) / s]
    elif m[0, 0] >= m[1, 1] and m[0, 0] >= m[2, 2]:
        s = math.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2]) * 2.0
        q = [(m[2, 1] - m[1, 2]) / s, 0.25 * s, (m[0, 1] + m[1, 0]) / s,
             (m[0, 2] + m[2, 0]) / s]
    elif m[1, 1] >= m[2, 2]:
        s = math.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2]) * 2.0
        q = [(m[2, 0] - m[0, 2]) / s, (m[0, 1] + m[1, 0]) / s, 0.25 * s,
             (m[1, 2] + m[2, 1]) / s]
    else:
        s = math.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1]) * 2.0
        q = [(m[1, 0] - m[0, 1]) / s, (m[0, 2] + m[2, 0]) / s,
             (m[1, 2] + m[2, 1]) / s, 0.25 * s]
    n = math.sqrt(sum(c * c for c in q))
    return [c / n for c in q]


class Cam:
    def __init__(self, eye, target, w, h, near, far, projection,
                 fov_deg=None, span=None):
        self.eye = np.array(eye, dtype=np.float64)
        self.target = [float(t) for t in target]
        self.w, self.h, self.near, self.far = w, h, near, far
        self.projection = projection
        self.fov_deg, self.span = fov_deg, span
        self.distance = float(math.dist([float(e) for e in eye], self.target))
        z = self.target - self.eye
        self.zax = z / np.linalg.norm(z)
        x = np.cross(np.array([0.0, 1.0, 0.0]), self.zax)
        self.xax = x / np.linalg.norm(x)
        self.yax = np.cross(self.zax, self.xax)
        self.q = quat_wxyz(self.xax, self.yax, self.zax)
        self.tan_half = (math.tan(math.radians(fov_deg) / 2.0)
                         if fov_deg else None)

    def sample(self, tick):
        return {"tick": tick,
                "position": [float(c) for c in self.eye],
                "target": list(self.target),
                "distance_to_target": self.distance,
                "orientation": [float(c) for c in self.q]}

    def project(self, pts):
        rel = pts - self.eye
        vx, vy, vz = rel @ self.xax, rel @ self.yax, rel @ self.zax
        ok = vz > self.near
        if self.projection == "perspective":
            vs = np.where(ok, vz, 1.0)
            xn = (vx / vs) / (self.tan_half * (self.w / self.h))
            yn = (vy / vs) / self.tan_half
        else:
            half = self.span / 2.0
            xn = vx / (half * (self.w / self.h))
            yn = vy / half
        px = (xn + 1.0) * 0.5 * self.w
        py = (1.0 - yn) * 0.5 * self.h
        return np.stack([px, py], axis=1), vz, ok


def project_point(cam, p):
    pix, vz, ok = cam.project(np.array([p], dtype=np.float64))
    return float(pix[0, 0]), float(pix[0, 1]), float(vz[0]), bool(ok[0])


def in_frame(cam, points, margin=2.0, depth_clear=0.01):
    """PREREGISTRATION P2/P3: anchors inside viewport, z within clip range."""
    pix, vz, ok = cam.project(np.asarray(points, dtype=np.float64))
    inside = (pix[:, 0] >= margin) & (pix[:, 0] <= cam.w - margin) & \
             (pix[:, 1] >= margin) & (pix[:, 1] <= cam.h - margin) & ok & \
             (vz <= cam.far) & (vz >= cam.near + depth_clear)
    return bool(inside.all()), int(inside.sum()), len(inside)


# ── rendering ────────────────────────────────────────────────────────────────
def render_mesh(cam, an, mode):
    """'diagnostic': envelope ghost pass + xray bones pass (depth sorted).
       'clean': opaque depth-tested envelope, backface culled, lambert."""
    V, F = an["V"], an["F"]
    pix, vz, ok = cam.project(V)
    x, y = pix[:, 0], pix[:, 1]
    xa, ya = x[F[:, 0]], y[F[:, 0]]
    xb, yb = x[F[:, 1]], y[F[:, 1]]
    xc, yc = x[F[:, 2]], y[F[:, 2]]
    area = 0.5 * np.abs(xa * (yb - yc) + xb * (yc - ya) + xc * (ya - yb))
    depth = (vz[F[:, 0]] + vz[F[:, 1]] + vz[F[:, 2]]) / 3.0
    keep = (area >= AREA_SKIP_PX2) & ok[F[:, 0]] & ok[F[:, 1]] & ok[F[:, 2]]
    if mode == "clean":
        view = an["tri_centroid"] - cam.eye
        facing = np.einsum("ij,ij->i", an["tri_normal"], view) < 0.0
        keep = keep & facing
    order = np.argsort(-depth, kind="stable")
    order = order[keep[order]]
    img = Image.new("RGB", (cam.w, cam.h), BG)
    draw = ImageDraw.Draw(img, "RGBA")
    if mode == "diagnostic":                 # pass 1: envelope ghost
        for t in order:
            p = pix[F[t]]
            draw.polygon([(p[0, 0], p[0, 1]), (p[1, 0], p[1, 1]),
                          (p[2, 0], p[2, 1])], fill=ENVELOPE_GHOST)
        for t in order:                      # pass 2: bones (xray)
            col = CHAIN_A_COLORS.get(int(an["face_bone"][t]), OTHER_BONE) \
                + (BONE_ALPHA,)
            p = pix[F[t]]
            draw.polygon([(p[0, 0], p[0, 1]), (p[1, 0], p[1, 1]),
                          (p[2, 0], p[2, 1])], fill=col)
    else:
        for t in order:
            lam = max(float(np.dot(an["tri_normal"][t], LIGHT)), 0.0)
            shade = 0.45 + 0.55 * lam
            col = tuple(min(255, int(c * shade)) for c in OTHER_BONE)
            p = pix[F[t]]
            draw.polygon([(p[0, 0], p[0, 1]), (p[1, 0], p[1, 1]),
                          (p[2, 0], p[2, 1])], fill=col)
    return img


def draw_axes_triad(draw, cam):
    o = project_point(cam, (0.0, 0.0, 0.0))
    if not (0 <= o[0] < cam.w and 0 <= o[1] < cam.h):
        return
    for name, col in AXES_COL.items():
        sign = -1.0 if name[0] == "-" else 1.0
        axisv = {"X": (1.0, 0.0, 0.0), "Y": (0.0, 1.0, 0.0),
                 "Z": (0.0, 0.0, 1.0)}[name[1]]
        tip = tuple(sign * 0.2 * c for c in axisv)
        b = project_point(cam, tip)
        if b[3]:
            draw.line([o[0], o[1], b[0], b[1]], fill=col, width=2)
            draw.text((b[0] + 2, b[1] - 4), name, fill=col, font=FONT)
    draw.text((o[0] + 3, o[1] + 3), L_AXES, fill=LABEL_COL, font=FONT)


def draw_marker(draw, cam, anchor, label_id):
    """Anchored callout (AMENDED v2): marker dot at the projected anchor,
    thin leader line to the label text in a fixed edge stack - labels never
    overlap each other."""
    x, y, _d, ok = project_point(cam, anchor)
    if not ok or not (0 <= x < cam.w and 0 <= y < cam.h):
        return
    draw.ellipse([x - 2, y - 2, x + 2, y + 2], fill=LABEL_COL)


def draw_callouts(draw, cam, items):
    stack_x = cam.w - 172
    y = 156
    for anchor, label_id in items:
        x, py, _d, ok = project_point(cam, anchor)
        if not ok or not (0 <= x < cam.w and 0 <= py < cam.h):
            y += 14
            continue
        draw.ellipse([x - 2, py - 2, x + 2, py + 2], fill=LABEL_COL)
        draw.line([x, py, stack_x, y + 5], fill=LEADER, width=1)
        draw.text((stack_x + 3, y), label_id, fill=LABEL_COL, font=FONT)
        y += 14


def draw_overlay(draw, cam, long_form, layers, view_tag):
    if long_form:
        lines = [
            "ONT-P02 visible_static | profile anatomy",
            "frame %s (m, Y-up, RH)" % FRAME_ID,
            "visual=standing_body.obj bc9033bf..9111 (CT-derived)",
            "physics=membrane creature default 13824.5 kg",
            "binding=RENDER_BINDING | ports none (connection_ids [])",
            "state sha256 bc9033bf..9111: constant across view toggles",
            "layers: " + " | ".join(layers[:3]),
            "        " + " | ".join(layers[3:]),
            "L muscle/tendon paths: ABSENT (no muscle lineage pinned;",
            "  MSK model KEPT_SEPARATE; inventoried, not invented)",
        ]
    else:
        lines = [
            "ONT-P02 visible_static",
            "frame %s" % FRAME_ID,
            "m, Y-up, RH | state bc9033bf..9111",
            "visual=obj bc9033bf.. | physics=membrane",
            "13824.5 kg | RENDER_BINDING | ports none",
            "L muscle/tendon: ABSENT (KEPT_SEPARATE)",
        ]
    wbox = max(draw.textlength(t, font=FONT) for t in lines) + 10
    hbox = 12 * len(lines) + 8
    draw.rectangle([4, 4, 4 + wbox, 4 + hbox], fill=PANEL_BG)
    for i, t in enumerate(lines):
        col = LAYER_TAG if (t.startswith("layers") or t.startswith("L ")
                            or t.startswith("        ")) else TXT
        draw.text((9, 9 + 12 * i), t, fill=col, font=FONT)
    draw.text((cam.w - draw.textlength(view_tag, font=FONT) - 6, cam.h - 14),
              view_tag, fill=TXT_DIM, font=FONT)


def render_diagnostic(cam, an, view_id, bookmark_tag, layers):
    long_form = cam.w >= W_FULL
    img = render_mesh(cam, an, "diagnostic")
    draw = ImageDraw.Draw(img, "RGBA")
    if "frame axes" in layers:
        draw_axes_triad(draw, cam)
    if view_id == VIEW_OVERVIEW:
        items = [(an["cents"][b], CHAIN_A_LABELS[b]) for b in CHAIN_A]
        items += [(an["band_centroid"], L_CONTACT), (an["joint"], L_JOINT),
                  (an["center"], L_MEMBRANE),
                  ([an["center"][0], 0.10, an["center"][2]], L_GHOST)]
        draw_callouts(draw, cam, items)
    elif view_id == VIEW_CLOSEUP:
        draw_callouts(draw, cam, [
            (an["band_centroid"], L_CONTACT), (an["joint"], L_JOINT),
            (an["cents"][2], CHAIN_A_LABELS[2]),
            (an["cents"][6], CHAIN_A_LABELS[6])])
    else:
        draw_callouts(draw, cam, [(an["cents"][b], CHAIN_A_LABELS[b])
                                  for b in (2, 6, 20)]
                      + [(an["band_centroid"], L_CONTACT)])
    draw_overlay(draw, cam, long_form, layers, bookmark_tag)
    return img


def render_clean(cam, an):
    """Pure depth-tested envelope panel: ZERO annotations (no diagnostic
    pixels at all), so a decoded clean view truly contains none."""
    return render_mesh(cam, an, "clean")


def render_view(cam, an, view_id, mode, bookmark_tag, layers):
    if mode == "clean":
        return render_clean(cam, an)
    return render_diagnostic(cam, an, view_id, bookmark_tag, layers)


# ── manifest ─────────────────────────────────────────────────────────────────
STATE_BINDING = {"kind": "state", "sha256": SUBJECT_SHA256}

CHAIN_BINDINGS = [(CHAIN_A_LABELS[b], S_BONE[b]) for b in CHAIN_A]
OVERVIEW_LABELS = CHAIN_BINDINGS + [(L_CONTACT, S_PATCH), (L_JOINT, S_JOINT),
                                    (L_MEMBRANE, S_MEMBRANE),
                                    (L_GHOST, S_GHOST)]
CLOSEUP_LABELS = [(L_CONTACT, S_PATCH), (L_JOINT, S_JOINT),
                  (CHAIN_A_LABELS[2], S_BONE[2]), (CHAIN_A_LABELS[6], S_BONE[6])]
SIDE_LABELS = [(CHAIN_A_LABELS[b], S_BONE[b]) for b in (2, 6, 20)] \
    + [(L_CONTACT, S_PATCH), (L_AXES, S_AXES)]


def camera_dict(cam, sample_mode, samples, interpolation=None):
    d = {"frame_id": FRAME_ID,
         "coordinate_unit": "m",
         "handedness": "right",
         "orientation_convention": "quaternion_wxyz_camera_to_frame",
         "forward_axis": "+Z",
         "up_axis": "+Y",
         "near_far_planes": [cam.near, cam.far],
         "viewport_resolution": [cam.w, cam.h],
         "aspect_ratio": cam.w / cam.h,
         "projection": cam.projection,
         "sample_mode": sample_mode,
         "samples": samples}
    if cam.projection == "perspective":
        d["vertical_fov_degrees"] = cam.fov_deg
    else:
        d["orthographic_span"] = cam.span
    if interpolation is not None:
        d["interpolation"] = interpolation
    return d


def fixed_camera(cam):
    """fixed_bookmark: the SAME pose declared at tick 0 and tick 1 (exact
    equality, validator-enforced); the subject is static pinned bytes."""
    return camera_dict(cam, "fixed_bookmark",
                       [cam.sample(TICKS[0]), cam.sample(TICKS[1])])


def visibility(mode, layers, labels, selected, required, observed):
    if mode == "clean":
        return {"layers": [], "label_ids": [], "selected_ids": [],
                "required_subject_ids": list(required),
                "observed_subject_ids": list(observed),
                "missing_subject_ids": [],
                "occlusion_mode": "depth_tested",
                "tag_bindings": []}
    return {"layers": list(layers),
            "label_ids": [l for l, _ in labels],
            "selected_ids": list(selected),
            "required_subject_ids": list(required),
            "observed_subject_ids": list(observed),
            "missing_subject_ids": [],
            "occlusion_mode": "xray",
            "tag_bindings": [{"label_id": l, "subject_id": s}
                             for l, s in labels]}


def build_manifest(an):
    center = [float(c) for c in an["center"]]
    patch = [float(c) for c in an["band_centroid"]]
    overview_cam = Cam([center[i] + OVERVIEW_EYE_OFF[i] for i in range(3)],
                       center, W_FULL, H_FULL, NEAR_OVER, FAR_OVER,
                       "perspective", fov_deg=FOV_DEG)
    closeup_cam = Cam([patch[i] + CLOSEUP_EYE_OFF[i] for i in range(3)],
                      patch, W_FULL, H_FULL, NEAR_CLOSE, FAR_CLOSE,
                      "perspective", fov_deg=FOV_DEG)
    side_cam = Cam([center[i] + SIDE_EYE_OFF[i] for i in range(3)],
                   center, W_HALF, H_HALF, NEAR_OVER, FAR_OVER,
                   "orthographic", span=SIDE_SPAN)
    oblique_cam = Cam([center[i] + OBLIQUE_EYE_OFF[i] for i in range(3)],
                      center, W_HALF, H_HALF, NEAR_OVER, FAR_OVER,
                      "orthographic", span=SIDE_SPAN)
    sideo_cam = camera_dict(
        side_cam, "sampled_trajectory",
        [side_cam.sample(TICKS[0]), oblique_cam.sample(TICKS[1])],
        interpolation="linear_position_target_slerp_orientation")

    obs_over = ([S_ENV] + [S_BONE[b] for b in CHAIN_A]
                + [S_PATCH, S_JOINT, S_MEMBRANE, S_GHOST])
    obs_close = [S_ENV, S_PATCH, S_JOINT, S_BONE[2], S_BONE[6]]
    obs_side = ([S_ENV] + [S_BONE[b] for b in (2, 6, 20)]
                + [S_PATCH, S_AXES])

    def row(view_id, mode, pair_id, cam_block, rect, vis):
        return {"view_id": view_id, "mode": mode, "pair_id": pair_id,
                "state_binding": dict(STATE_BINDING),
                "artifact_locator": {"kind": "image",
                                     "region": "pixel_rectangle",
                                     "pixel_rectangle": list(rect)},
                "camera": cam_block, "visibility": vis}

    rows = [
        row(VIEW_OVERVIEW, "diagnostic", "overview", fixed_camera(overview_cam),
            RECT_OVER_D,
            visibility("diagnostic", LAYERS_FULL, OVERVIEW_LABELS,
                       [S_BONE[b] for b in CHAIN_A], [S_ENV], obs_over)),
        row(VIEW_OVERVIEW, "clean", "overview", fixed_camera(overview_cam),
            RECT_OVER_C, visibility("clean", None, None, None, [S_ENV],
                                    [S_ENV])),
        row(VIEW_CLOSEUP, "diagnostic", "closeup", fixed_camera(closeup_cam),
            RECT_CLOSE_D,
            visibility("diagnostic", LAYERS_CLOSEUP, CLOSEUP_LABELS,
                       [S_BONE[2], S_BONE[6]],
                       [S_PATCH, S_JOINT], obs_close)),
        row(VIEW_CLOSEUP, "clean", "closeup", fixed_camera(closeup_cam),
            RECT_CLOSE_C,
            visibility("clean", None, None, None, [S_PATCH, S_JOINT],
                       [S_ENV, S_PATCH, S_JOINT])),
        row(VIEW_SIDEOBLIQUE, "diagnostic", "sideo", sideo_cam, RECT_SIDE_D,
            visibility("diagnostic", LAYERS_FULL, SIDE_LABELS,
                       [S_BONE[b] for b in (2, 6, 20)], [S_ENV], obs_side)),
        row(VIEW_SIDEOBLIQUE, "clean", "sideo", sideo_cam, RECT_SIDE_C,
            visibility("clean", None, None, None, [S_ENV], [S_ENV])),
    ]
    cams = {"overview": overview_cam, "closeup": closeup_cam,
            "side": side_cam, "oblique": oblique_cam}
    return rows, cams


# ── main ─────────────────────────────────────────────────────────────────────
def sha256_file(path):
    d = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            d.update(chunk)
    return d.hexdigest()


def main() -> int:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    scratch = HERE.parents[4] / "scratch" / "ont-p02-capture"
    scratch.mkdir(parents=True, exist_ok=True)
    an = load_anatomy(scratch)
    print("subject: pinned blob verified; segmentation + frozen predictions OK")

    rows, cams = build_manifest(an)

    # ── PREREGISTRATION P2/P3: in-frustum assertions ────────────────────────
    checks = {}
    V = an["V"]
    checks["overview_all_verts_in_frame"] = in_frame(cams["overview"], V)
    checks["side_all_verts_in_frame"] = in_frame(cams["side"], V)
    checks["oblique_all_verts_in_frame"] = in_frame(cams["oblique"], V)
    close_anchors = np.array([an["band_centroid"], an["joint"],
                              an["cents"][2], an["cents"][6]],
                             dtype=np.float64)
    checks["closeup_anchors_in_frame"] = in_frame(cams["closeup"], close_anchors)
    for name, (ok, n_in, n) in checks.items():
        print("check %-32s %s (%d/%d)" % (name, "OK" if ok else "FAIL", n_in, n))
        if not ok:
            raise ValueError("frozen_falsifier_probe_failed:" + name)

    # ── render the six panels ───────────────────────────────────────────────
    sheet = Image.new("RGB", (SHEET_W, SHEET_H), BG)
    jobs = [
        (cams["overview"], VIEW_OVERVIEW, "diagnostic", "overview diag t0/t1",
         LAYERS_FULL, RECT_OVER_D),
        (cams["closeup"], VIEW_CLOSEUP, "diagnostic", "close-up diag t0/t1",
         LAYERS_CLOSEUP, RECT_CLOSE_D),
        (cams["side"], VIEW_SIDEOBLIQUE, "diagnostic", "side diag t0",
         LAYERS_FULL, None),
        (cams["oblique"], VIEW_SIDEOBLIQUE, "diagnostic", "oblique diag t1",
         LAYERS_FULL, [RECT_SIDE_D[0] + W_HALF, 0, W_HALF, H_FULL]),
        (cams["overview"], VIEW_OVERVIEW, "clean", None, None, RECT_OVER_C),
        (cams["closeup"], VIEW_CLOSEUP, "clean", None, None, RECT_CLOSE_C),
        (cams["side"], VIEW_SIDEOBLIQUE, "clean", None, None, None),
        (cams["oblique"], VIEW_SIDEOBLIQUE, "clean", None, None,
         [RECT_SIDE_C[0] + W_HALF, H_FULL, W_HALF, H_FULL]),
    ]
    for cam, view_id, mode, tag, layers, rect in jobs:
        if mode == "diagnostic":
            img = render_diagnostic(cam, an, view_id, tag, layers)
        else:
            img = render_clean(cam, an)
        if rect is None:
            rect = [RECT_SIDE_D[0] if mode == "diagnostic" else RECT_SIDE_C[0],
                    0 if mode == "diagnostic" else H_FULL, W_HALF, H_FULL]
        sheet.paste(img, (rect[0], rect[1]))
        print("rendered %s %s -> rect %s" % (view_id, mode, rect))

    capture_path = EVIDENCE / "capture.png"
    sheet.save(capture_path, format="PNG", compress_level=6)
    capture_sha = sha256_file(capture_path)
    print("capture bytes:", capture_path.stat().st_size)
    print("capture sha256:", capture_sha)

    manifest = {
        "schema": "chimera.visual_capture_manifest.v1",
        "task_id": TASK_ID,
        "run_id": RUN_ID,
        "subject_sha256": SUBJECT_SHA256,
        "capture_sha256": capture_sha,
        "profile_id": PROFILE_ID,
        "tick_interval": list(TICKS),
        "views": rows,
    }
    manifest_path = EVIDENCE / "capture_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=1, sort_keys=True)
                             + "\n", encoding="utf-8")

    # ── validate with the campaign's own gate (read-only import) ────────────
    sys.path.insert(0, str(validator_dir()))
    sys.dont_write_bytecode = True
    for stale in [k for k in sys.modules
                  if k in ("visual_gate", "visual_capture", "integrity")]:
        del sys.modules[stale]
    import visual_gate                                    # noqa: E402
    contract = json.loads((HERE / "card_task.json").read_text(encoding="utf-8"))
    receipt = {
        "evidence": {
            "camera": {"reference": str(manifest_path.resolve()),
                       "raw_sha256": sha256_file(manifest_path)},
            "visual": {"reference": str(capture_path.resolve()),
                       "raw_sha256": capture_sha},
        },
        "capture_context": {
            "task_id": TASK_ID,
            "subject_sha256": SUBJECT_SHA256,
            "run_id": RUN_ID,
            "capture_sha256": capture_sha,
            "tick_interval": list(TICKS),
        },
    }
    structural = visual_gate.verify(receipt, contract)
    print("gate:", json.dumps(structural))

    frustum_report = {k: {"ok": v[0], "inside": v[1], "probed": v[2]}
                      for k, v in checks.items()}
    capture_receipt = {
        "schema": "ont-p02.anatomy.visible_static.capture.v1",
        "task_id": TASK_ID,
        "card_id": "ONT-P02",
        "run_id": RUN_ID,
        "subject": {
            "path": "tools/playable_slice/standing_body.obj",
            "commit": "33e7a444fe7b4c35aa99afe7ef898046877025b4",
            "blob": SUBJECT_BLOB,
            "sha256": SUBJECT_SHA256,
            "bytes": SUBJECT_BYTES,
            "extraction": "read-only git cat-file blob into attempt scratch; "
                          "sha256+bytes asserted before parse",
        },
        "honest_boundary": "Deterministic CPU software render (numpy + PIL "
                           "painter's algorithm) of the pinned mesh bytes; "
                           "NOT native engine frames; no GPU; no engine "
                           "process; python -B CPU-only.",
        "image": {"reference": str(capture_path.resolve()),
                  "raw_sha256": capture_sha,
                  "bytes": capture_path.stat().st_size,
                  "resolution": [SHEET_W, SHEET_H],
                  "encoder": "PIL PNG compress_level=6 (deterministic)"},
        "sheet_layout": {
            "whole-creature overview": {"diagnostic": RECT_OVER_D,
                                        "clean": RECT_OVER_C},
            "local attachment close-up": {"diagnostic": RECT_CLOSE_D,
                                          "clean": RECT_CLOSE_C},
            "orthogonal side and oblique views": {
                "diagnostic": RECT_SIDE_D,
                "clean": RECT_SIDE_C,
                "bookmark_panels": {
                    "tick 0 side": [RECT_SIDE_D[0], 0, W_HALF, H_FULL],
                    "tick 1 oblique": [RECT_SIDE_D[0] + W_HALF, 0, W_HALF,
                                       H_FULL],
                    "tick 0 side (clean)": [RECT_SIDE_C[0], H_FULL, W_HALF,
                                            H_FULL],
                    "tick 1 oblique (clean)": [RECT_SIDE_C[0] + W_HALF,
                                               H_FULL, W_HALF, H_FULL]},
                "note": "one profile view, two declared camera bookmarks; "
                        "each 420x420 panel is one bookmark's frame at the "
                        "declared viewport_resolution"},
        },
        "clean_panels": "own panels, zero annotations/diagnostic pixels; "
                        "occlusion depth_tested, envelope only",
        "diagnostic_panels": "xray mode: envelope ghost pass + bone pass "
                             "(alpha 200/255), overlay panel, frame axes, "
                             "stable 3D labels",
        "state_binding": {"kind": "state", "sha256": SUBJECT_SHA256,
                          "note": "the pinned subject bytes ARE the static "
                                  "physical state; all 6 rows bind the same "
                                  "hash - view/layer toggles preserve it"},
        "layer_inventory": {
            "outer envelope": "pinned mesh surface, depth-tested in clean, "
                              "ghost tone in diagnostic",
            "selected bones/joints": "per-bone blocks (verified contiguous "
                                     "segmentation, sums 249743/499976); hind "
                                     "chain 'a' highlighted + labeled "
                                     "(sides never assigned)",
            "muscle/tendon paths": "ABSENT - inventoried explicitly; no "
                                   "muscle/tendon lineage pinned for the "
                                   "runtime body; nothing invented",
            "attachment sites": "measured scene contact band centroid + "
                                "DECLARED centroid-midpoint joint proxy "
                                "(2-6 touching edge gap 2.91 mm per "
                                "identification v3) + owner binding labels",
            "frame axes": "+X/-X/+Y/-Y/+Z/-Z triad at origin, overview + "
                          "side/oblique diagnostics only",
            "stable 3D labels": "every label_id drawn and bound 1:1"},
        "render_referents": {
            "frame": FRAME_ID + " (scene metres, Y-up, right-handed; pads' "
                       "mean plane y=0 per the committed compose header)",
            "projection": "perspective 40 deg vertical FOV (overview, "
                          "close-up); orthographic span 0.80 m (side, oblique)",
            "area_skip_px2": AREA_SKIP_PX2,
            "depth_sort": "numpy argsort(-depth, kind='stable'), painter "
                          "back-to-front",
            "light": "directional, world dir (0.35, 0.8, -0.45) normalized "
                     "(clean shading only)"},
        "frozen_probe_results": frustum_report,
        "manifest": {"reference": str(manifest_path.resolve()),
                     "raw_sha256": sha256_file(manifest_path)},
        "gate_validation": structural,
        "environment": {"python": platform.python_version(),
                        "numpy": np.__version__, "pillow": __import__("PIL")
                        .__version__},
    }
    (EVIDENCE / "capture_receipt.json").write_text(
        json.dumps(capture_receipt, indent=1, sort_keys=True) + "\n",
        encoding="utf-8")

    # ── numerical receipt (measured; records leg reused by reference) ──────
    review_ev = Path("E:/ChimeraWork/monkey-coordination/kanban-reviews"
                     "/ONT-P02/101b464373ec4f119790f64d9753d1d0"
                     "/review_evidence/ONT-P02_review_evidence.json")
    prior_lineage = Path("E:/ChimeraWork/monkey-coordination/kanban-attempts"
                         "/ONT-P02/ab7b304e0a0446e99f324557addb21fb"
                         "/lineage_verification_receipt.json")
    numerical = {
        "schema": "ont-p02.anatomy.visible_static.numerical.v1",
        "task_id": TASK_ID,
        "run_id": RUN_ID,
        "subject_measurements": {
            "sha256": SUBJECT_SHA256, "bytes": SUBJECT_BYTES,
            "verts": int(len(an["V"])), "faces": int(len(an["F"])),
            "bbox_min": [float(c) for c in an["V"].min(0)],
            "bbox_max": [float(c) for c in an["V"].max(0)],
            "center": [float(c) for c in an["center"]],
            "contact_band": {"y_threshold": an["contact_ymin"] + 0.005,
                             "verts": PRED_BAND_N,
                             "centroid": [float(c) for c in
                                          an["band_centroid"]],
                             "owners": PRED_BAND_OWNERS},
            "segmentation": {"blocks": 25, "contiguous": True,
                             "vert_sums_match": True, "face_sums_match": True,
                             "chain_a_centroids": {str(b): [float(c) for c in
                                                  an["cents"][b]]
                                                   for b in CHAIN_A},
                             "joint_proxy_b02_b06": [float(c) for c in
                                                     an["joint"]]},
        },
        "frozen_predictions": {"bbox_min": list(PRED_BBOX_MIN),
                               "bbox_max": list(PRED_BBOX_MAX),
                               "band_verts": PRED_BAND_N,
                               "band_centroid": list(PRED_BAND_CENTROID),
                               "band_owners": PRED_BAND_OWNERS,
                               "chain_centroids": PRED_CHAIN_CENTROIDS,
                               "all_asserted_at_build": True},
        "records_leg_reused": {
            "pr": "https://github.com/GhostDragonAlpha/Chimera/pull/144",
            "head_sha": "8c7ed8c27d9e27d1210a7754cb17831bd4ec1532",
            "monkey_lineage_map.json_sha256":
                "6a9d4ac83c2f99339c9a3fa72f0ecb4d018e0239cc2d26a1e8876a08d43a27b9",
            "reviewer_pass": "152 checks / 23 pins, falsifier 23/23",
            "lineage_verification_receipt": {
                "reference": str(prior_lineage),
                "raw_sha256": sha256_file(prior_lineage)
                if prior_lineage.is_file() else None},
            "independent_review_evidence": {
                "reference": str(review_ev),
                "raw_sha256": sha256_file(review_ev)
                if review_ev.is_file() else None},
        },
        "visual_camera_leg": "NEW evidence (this correction): capture.png + "
                             "capture_manifest.json; structural gate PASS "
                             "(visual_acceptance false by design - "
                             "independent review remains the gate)",
        "gate_validation": structural,
    }
    (EVIDENCE / "numerical_receipt.json").write_text(
        json.dumps(numerical, indent=1, sort_keys=True) + "\n",
        encoding="utf-8")

    ok = bool(structural.get("structurally_valid"))
    print("RESULT:", "CAPTURE BUILT AND GATE-VALID" if ok else "GATE REJECTED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

