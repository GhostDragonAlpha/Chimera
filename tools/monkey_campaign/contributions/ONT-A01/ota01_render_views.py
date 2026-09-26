"""ONT-A01 visual capture: deterministic CPU raster of the frozen anatomy views.

Honesty label (also carried in the manifest `render` block): geometry is
rasterized by a numpy z-buffer software rasterizer (true per-pixel depth test,
fixed light, no randomness) and composed/labeled with matplotlib Agg on CPU.
These are NOT native engine frames; nothing here claims an application run.
The claim subject is anatomy evidence (records), which the anatomy profile
serves with component evidence.

Views (PREREGISTRATION, frozen):
  V1 whole-creature overview          - target pack mesh (birth), frame axes,
                                        forearm region box (target world frame, m)
  V2 local attachment close-up        - source ulna (authored scale), six labeled
                                        sites, ECU tendon course, volar/dorsal
                                        arrows (source rest frame, mm)
  V3 orthogonal side and oblique      - source ulna, 4-bookmark sampled trajectory:
                                        anterior, posterior, left-lateral oblique,
                                        superior (source rest frame, mm)
Each declared view gets a diagnostic + clean pair (identical camera/state per
pair). Diagnostic rows: occlusion 'mixed' (mesh depth-tested, overlay markers and
labels intentionally unoccluded = xray semantics). Clean rows: 'depth_tested'
(true z-buffer).

Writes: evidence/capture_sheet.png, evidence/capture_manifest.json,
evidence/visual_provenance.json. Validates the manifest structurally with the
canonical campaign validator before writing the receipt.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE / "evidence"
sys.path.insert(0, str(HERE))
import ota01_roll_sign as core  # noqa: E402

PANEL_W, PANEL_H = 480, 360
SHEET_COLS, SHEET_ROWS = 4, 3
SHEET_W, SHEET_H = PANEL_W * SHEET_COLS, PANEL_H * SHEET_ROWS
RUN_ID = "ONT-A01-ota01-deterministic-cpu-20260926"

PROFILE = {
    "id": "anatomy",
    "kind": "visible_static",
    "subject": "Creature structure, bone/muscle/skin correspondence and attachment ownership",
    "views": ["whole-creature overview", "local attachment close-up",
              "orthogonal side and oblique views"],
    "diagnostic_layers": ["outer envelope", "selected bones/joints", "muscle/tendon paths",
                          "attachment sites", "frame axes", "stable 3D labels"],
    "clean_view_required": True,
    "numerical_evidence_required": True,
}

# fixed light (frame coords, normalized) and base colors (deterministic)
LIGHT = np.array([0.35, 0.8, 0.5])
LIGHT = LIGHT / np.linalg.norm(LIGHT)
CLEAN_COLOR = np.array([0.72, 0.70, 0.66])
BONE_COLOR = np.array([0.80, 0.78, 0.74])
SKIN_COLOR = np.array([0.62, 0.58, 0.52])
FLEXOR_COLOR = (220, 30, 60)     # crimson, O1 convention
EXTENSOR_COLOR = (30, 60, 220)   # blue, O1 convention
VOLAR_COLOR = (200, 20, 20)
DORSAL_COLOR = (20, 20, 120)
COURSE_COLOR = (240, 140, 20)


# ------------------------------------------------------------ quaternion ----
def mat_to_quat_wxyz(R):
    """Rotation matrix (columns = camera axes in frame coords) -> unit quat w,x,y,z.
    Shepperd's method; deterministic."""
    t = np.trace(R)
    if t > 0:
        s = np.sqrt(t + 1.0)
        w = 0.5 * s
        x = (R[2, 1] - R[1, 2]) / (2 * s)
        y = (R[0, 2] - R[2, 0]) / (2 * s)
        z = (R[1, 0] - R[0, 1]) / (2 * s)
    else:
        i = int(np.argmax(np.diag(R)))
        j, k = (i + 1) % 3, (i + 2) % 3
        s = np.sqrt(R[i, i] - R[j, j] - R[k, k] + 1.0)
        q = [0.0, 0.0, 0.0, 0.0]
        q[i + 1] = 0.5 * s
        w = (R[k, j] - R[j, k]) / (2 * s)
        q[j + 1] = (R[j, i] + R[i, j]) / (2 * s)
        q[k + 1] = (R[k, i] + R[i, k]) / (2 * s)
        x, y, z = q[1], q[2], q[3]
    q = np.array([w, x, y, z])
    return q / np.linalg.norm(q)


def camera_basis(position, target, up_hint):
    """Orthographic camera axes in frame coords. Camera looks along
    forward = unit(target - position); forward_axis '-Z', up '+Y'.
    Returns (Xc, Yc, Zc, forward)."""
    forward = core.unit(np.asarray(target, float) - np.asarray(position, float))
    Zc = -forward
    up = np.asarray(up_hint, float)
    Yc = core.unit(up - (up @ Zc) * Zc)
    Xc = np.cross(Yc, Zc)
    return Xc, Yc, Zc, forward


def cam_sample(position, target, up_hint):
    Xc, Yc, Zc, forward = camera_basis(position, target, up_hint)
    q = mat_to_quat_wxyz(np.column_stack([Xc, Yc, Zc]))
    pos = [float(v) for v in position]
    tgt = [float(v) for v in target]
    return {
        "position": pos, "target": tgt,
        "distance_to_target": float(np.linalg.norm(np.subtract(pos, tgt))),
        "orientation": [float(v) for v in q],
    }


# ---------------------------------------------------------- z-buffer pass ----
def render_mesh(rgb, zbuf, V, F, cam, span, color, W, H, x0, y0):
    """Orthographic z-buffer raster into the sheet region (x0,y0) panel offset.
    depth = distance along the view direction; nearest wins."""
    pos, fwd = np.array(cam["position"]), None
    Xc, Yc, Zc, fwd = camera_basis(cam["position"], cam["target"], [0, 1, 0])
    rel = V - pos
    xc, yc, dc = rel @ Xc, rel @ Yc, rel @ fwd
    aspect = W / H
    px = (xc / (span * aspect) + 0.5) * W
    py = (1.0 - (yc / span + 0.5)) * H
    tri_px, tri_py, tri_d = px[F], py[F], dc[F]
    # face normals in frame coords for lambert shading
    e1 = V[F[:, 1]] - V[F[:, 0]]
    e2 = V[F[:, 2]] - V[F[:, 0]]
    n = np.cross(e1, e2)
    nn = np.linalg.norm(n, axis=1)
    ok = nn > 1e-14
    shade = np.ones(len(F))
    shade[ok] = np.abs((n[ok] / nn[ok, None]) @ LIGHT)
    base = color * (0.35 + 0.65 * shade)[:, None] * 255.0
    for k in range(len(F)):
        xs, ys, ds = tri_px[k], tri_py[k], tri_d[k]
        if not np.isfinite(ds).all():
            continue
        lox = max(int(np.floor(xs.min())), 0)
        hix = min(int(np.ceil(xs.max())), W - 1)
        loy = max(int(np.floor(ys.min())), 0)
        hiy = min(int(np.ceil(ys.max())), H - 1)
        if lox > hix or loy > hiy:
            continue
        gx, gy = np.meshgrid(np.arange(lox, hix + 1) + 0.0,
                             np.arange(loy, hiy + 1) + 0.0)
        # edge functions: e01 -> sub-area (p0,p1,q); e12 -> (p1,p2,q); e20 -> (p2,p0,q)
        e01 = (xs[1] - xs[0]) * (gy - ys[0]) - (ys[1] - ys[0]) * (gx - xs[0])
        e12 = (xs[2] - xs[1]) * (gy - ys[1]) - (ys[2] - ys[1]) * (gx - xs[1])
        e20 = (xs[0] - xs[2]) * (gy - ys[2]) - (ys[0] - ys[2]) * (gx - xs[2])
        area2 = ((xs[1] - xs[0]) * (ys[2] - ys[0]) - (ys[1] - ys[0]) * (xs[2] - xs[0]))
        if abs(area2) < 1e-12:
            continue
        inside = ((e01 >= 0) & (e12 >= 0) & (e20 >= 0)) | \
                 ((e01 <= 0) & (e12 <= 0) & (e20 <= 0))
        if not inside.any():
            continue
        # weights: q = (e12*p0 + e20*p1 + e01*p2) / area2
        w0 = e12 / area2
        w1 = e20 / area2
        w2 = e01 / area2
        depth = w0 * ds[0] + w1 * ds[1] + w2 * ds[2]
        sub_z = zbuf[loy:hiy + 1, lox:hix + 1]
        sub_rgb = rgb[loy:hiy + 1, lox:hix + 1]
        m = inside & (depth < sub_z)
        sub_z[m] = depth[m]
        col = base[k]
        sub_rgb[m] = col[None, :]


def project(points, cam, span, W, H):
    Xc, Yc, Zc, fwd = camera_basis(cam["position"], cam["target"], [0, 1, 0])
    rel = np.asarray(points, float) - np.asarray(cam["position"])
    xc, yc = rel @ Xc, rel @ Yc
    aspect = W / H
    px = (xc / (span * aspect) + 0.5) * W
    py = (1.0 - (yc / span + 0.5)) * H
    depth = rel @ fwd
    return np.column_stack([px, py, depth])


# --------------------------------------------------------------- panels ----
def draw_arrow_2d(fig, p0, p1, color, label=None, lpos=None):
    fig.annotate("", xy=(p1[0], p1[1]), xytext=(p0[0], p0[1]),
                 xycoords="data", textcoords="data",
                 arrowprops=dict(arrowstyle="->", color=color, lw=1.6))
    if label:
        fig.text(lpos[0], lpos[1], label, color=color, fontsize=7,
                 ha=lpos[2], va="center")


def axis_triad_panel(fig, origin_w, cam, span, W, H, axes, tick_labels,
                     color=(0.08, 0.08, 0.08), anchor_px=(46, 46), arm_px=24):
    """Screen-anchored world-axis triad: each world direction is projected to its
    on-screen direction (orthographic), then drawn as unoccluded overlay arrows
    from a fixed pixel anchor so the triad can never clip the subject."""
    o = np.array([origin_w], float)
    o2 = project(o, cam, span, W, H)[0]
    ax0, ay0 = anchor_px
    for d, lab in axes:
        tip3 = o + np.array(d, float) * span * 0.14
        t2 = project(tip3, cam, span, W, H)[0]
        v = np.array([t2[0] - o2[0], -(t2[1] - o2[1])])
        n = np.linalg.norm(v)
        if n < 1e-9:
            continue
        v = v / n * arm_px
        tip = (ax0 + v[0], ay0 + v[1])
        draw_arrow_2d(fig, (ax0, ay0), tip, color)
        fig.text(tip[0] + 3, tip[1] + 3, lab, color=color, fontsize=7.5,
                 ha="left", va="bottom")


def compose_panel(fig, rgb, zbuf_region, title, mode):
    fig.imshow(np.clip(rgb, 0, 255).astype(np.uint8), extent=[0, PANEL_W, 0, PANEL_H],
               interpolation="nearest", zorder=0)
    fig.set_xlim(0, PANEL_W)
    fig.set_ylim(0, PANEL_H)
    fig.axis("off")
    tag = "DIAGNOSTIC" if mode == "diagnostic" else "CLEAN"
    fig.text(4, PANEL_H - 4, f"{title} [{tag}]", fontsize=7, color="black",
             ha="left", va="top", zorder=10,
             bbox=dict(fc="white", ec="none", alpha=0.75, pad=1.2))


def render_pair(V, F, cam, span, W, H, diag_overlay=None, mesh_color=CLEAN_COLOR):
    """Returns (diag_rgb, clean_rgb) panels with true z-buffer occlusion."""
    outs = []
    for mode in ("diagnostic", "clean"):
        rgb = np.full((H, W, 3), 255, dtype=np.float64)
        zbuf = np.full((H, W), np.inf)
        render_mesh(rgb, zbuf, V, F, cam, span, mesh_color, W, H, 0, 0)
        if mode == "diagnostic" and diag_overlay:
            diag_overlay(rgb)  # overlay painters intentionally skip zbuf (xray semantics)
        outs.append(rgb)
    return outs


def label_xy(points3, cam, span, W, H, dy=8, side="right"):
    p = project(np.asarray(points3, float), cam, span, W, H)
    return p


# ------------------------------------------------------------------ build ----
def build_everything():
    state, receipt = core.write_receipts()
    EVIDENCE.mkdir(exist_ok=True)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    sheet = np.full((SHEET_H, SHEET_W, 3), 255, dtype=np.uint8)
    manifest_views = []
    state_binding = {"kind": "state",
                     "sha256": hashlib.sha256(
                         (EVIDENCE / "state_snapshot.json").read_bytes()).hexdigest()}

    # ---------------- V1: whole-creature overview (target world frame, m) ----
    mt = core.load_birth_pack()
    V, F = mt.V, mt.F
    center = (V.min(0) + V.max(0)) / 2.0
    diag = float(np.linalg.norm(V.max(0) - V.min(0)))
    span1 = diag * 1.02
    cam1 = cam_sample(center + core.unit([0.30, 0.35, 1.0]) * diag * 1.15, center, [0, 1, 0])
    elbow, wrist = mt.joint_pos("elbow_R"), mt.joint_pos("wrist_R")
    origin1 = np.array([V[:, 0].min(), V[:, 1].min(), V[:, 2].max()]) + np.array([0.02, 0.02, -0.02])

    box_lo = np.minimum(elbow, wrist) - np.array([0.045, 0.03, 0.045])
    box_hi = np.maximum(elbow, wrist) + np.array([0.045, 0.03, 0.045])
    corner_pts = np.array([box_lo + np.array([bool((a >> s) & 1) for s in range(3)],
                                             float) * (box_hi - box_lo)
                           for a in range(8)])
    box_edges = [(a, b) for a in range(8) for b in range(8)
                 if sum(1 for s in range(3) if ((a >> s) & 1) != ((b >> s) & 1)) == 1]

    labels1 = [("target_monkey_mesh", "macaque render mesh (CT-derived)",
                center + [0, -0.42, 0], (4, -4)),
               ("target_joint_elbow_R", "elbow_R", elbow, (-70, 14)),
               ("target_joint_wrist_R", "wrist_R", wrist, (-70, -14)),
               ("target_forearm_region_box", "U-STR forearm region (boxed)",
                np.array([box_hi[0], box_hi[1], box_lo[2]]) + [0, 0.02, 0], (8, 10))]

    # raster both modes
    panels = {}
    for mode in ("diagnostic", "clean"):
        rgb = np.full((PANEL_H, PANEL_W, 3), 255, dtype=np.float64)
        zbuf = np.full((PANEL_H, PANEL_W), np.inf)
        render_mesh(rgb, zbuf, V, F, cam1, span1, SKIN_COLOR, PANEL_W, PANEL_H, 0, 0)
        panels[mode] = (rgb, zbuf)

    fig = plt.figure(figsize=(PANEL_W / 100, PANEL_H / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    rgb, zbuf = panels["diagnostic"]
    ax.imshow(np.clip(rgb, 0, 255).astype(np.uint8), extent=[0, PANEL_W, 0, PANEL_H],
              interpolation="nearest", zorder=0)
    # box (unoccluded overlay)
    corners = project(corner_pts, cam1, span1, PANEL_W, PANEL_H)
    for a, b in box_edges:
        ax.plot([corners[a, 0], corners[b, 0]],
                [PANEL_H - corners[a, 1], PANEL_H - corners[b, 1]],
                color=(0.1, 0.4, 0.9), lw=1.2, zorder=6)
    axis_triad_panel(ax, origin1, cam1, span1, PANEL_W, PANEL_H,
                     [([0, 0, 1], "+z anterior"), ([0, 1, 0], "+y up"), ([-1, 0, 0], "-x right")],
                     None, anchor_px=(52, PANEL_H - 52))
    for subj, text, anchor, (dx, dy) in labels1:
        p = project(np.array([anchor]), cam1, span1, PANEL_W, PANEL_H)[0]
        ax.plot([p[0]], [PANEL_H - p[1]], "+", ms=3, color="black", zorder=7)
        ax.text(p[0] + dx, PANEL_H - p[1] + dy, text, fontsize=6.4, color="black",
                zorder=8, ha="left",
                bbox=dict(fc="white", ec="none", alpha=0.7, pad=0.8))
    compose_panel(ax, rgb, zbuf, "V1 whole-creature overview (target frame, m)", "diagnostic")
    fig.canvas.draw()
    buf = np.asarray(fig.canvas.buffer_rgba())[:, :, :3]
    sheet[0:PANEL_H, 0:PANEL_W] = buf
    plt.close(fig)

    fig = plt.figure(figsize=(PANEL_W / 100, PANEL_H / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    rgb, zbuf = panels["clean"]
    compose_panel(ax, rgb, zbuf, "V1 whole-creature overview", "clean")
    fig.canvas.draw()
    buf = np.asarray(fig.canvas.buffer_rgba())[:, :, :3]
    sheet[0:PANEL_H, PANEL_W:2 * PANEL_W] = buf
    plt.close(fig)

    near1, far1 = 0.01, round(float(diag * 3.0), 3)

    def v1_visibility(mode):
        if mode == "clean":
            return {
                "layers": [], "label_ids": [], "selected_ids": [],
                "required_subject_ids": ["target_monkey_mesh"],
                "observed_subject_ids": ["target_monkey_mesh"],
                "missing_subject_ids": [],
                "occlusion_mode": "depth_tested",
                "tag_bindings": [],
            }
        layers = ["outer envelope", "selected bones/joints", "frame axes", "stable 3D labels"]
        labels = ["L-mesh", "L-elbow_R", "L-wrist_R", "L-region-box",
                  "L-ax-z", "L-ax-y", "L-ax-x"]
        subjects = ["target_monkey_mesh", "target_joint_elbow_R", "target_joint_wrist_R",
                    "target_forearm_region_box", "target_frame_axis_anterior_z",
                    "target_frame_axis_up_y", "target_frame_axis_right_x"]
        bindings = [{"label_id": l, "subject_id": s} for l, s in
                    zip(labels, ["target_monkey_mesh", "target_joint_elbow_R",
                                 "target_joint_wrist_R", "target_forearm_region_box",
                                 "target_frame_axis_anterior_z", "target_frame_axis_up_y",
                                 "target_frame_axis_right_x"])]
        return {
            "layers": layers, "label_ids": labels, "selected_ids":
                ["target_monkey_mesh", "target_forearm_region_box"],
            "required_subject_ids": ["target_monkey_mesh", "target_forearm_region_box"],
            "observed_subject_ids": subjects,
            "missing_subject_ids": [],
            "occlusion_mode": "mixed",
            "tag_bindings": bindings,
        }

    cam1_meta = {
        "frame_id": "target_world_frame(+z anterior,+y up,-x right; O1 sec.1)",
        "coordinate_unit": "m", "handedness": "right",
        "orientation_convention": "quaternion_wxyz_camera_to_frame",
        "forward_axis": "-Z", "up_axis": "+Y",
        "near_far_planes": [near1, far1],
        "viewport_resolution": [PANEL_W, PANEL_H],
        "aspect_ratio": PANEL_W / PANEL_H,
        "projection": "orthographic",
        "orthographic_span": float(span1),
        "sample_mode": "fixed_bookmark",
        "samples": [dict(cam1, tick=t) for t in (0, 3)],
    }
    manifest_views.append({"view_id": PROFILE["views"][0], "mode": "diagnostic",
                           "pair_id": "V1",
                           "state_binding": state_binding,
                           "artifact_locator": {"kind": "image", "region": "pixel_rectangle",
                                                "pixel_rectangle": [0, 0, PANEL_W, PANEL_H]},
                           "camera": cam1_meta,
                           "visibility": v1_visibility("diagnostic")})
    manifest_views.append({"view_id": PROFILE["views"][0], "mode": "clean",
                           "pair_id": "V1",
                           "state_binding": state_binding,
                           "artifact_locator": {"kind": "image", "region": "pixel_rectangle",
                                                "pixel_rectangle": [PANEL_W, 0, PANEL_W, PANEL_H]},
                           "camera": cam1_meta,
                           "visibility": v1_visibility("clean")})

    # ---------------- V2: local attachment close-up (source rest frame, mm) --
    Vu, Fu, _ = core.ulna_mesh_scaled()
    Vmm, Fmm = Vu * 1000.0, Fu
    src = json.loads((core.RECEIPTS / "o1_source_split.json").read_text())
    site_local = {s["site"]: np.array(s["pos_local_m"]) * 1000.0 for s in src["site_table"]}
    target2 = np.mean([site_local[s] for s in ("ANC-P2", "BRA-P4", "BRA-P3", "PT-P2")], axis=0)
    span2 = 130.0
    cam2 = cam_sample(target2 + core.unit([1.0, 0.45, 0.30]) * 180.0, target2, [0, 1, 0])
    near2, far2 = 1.0, 1000.0

    def render_v2(mode):
        rgb = np.full((PANEL_H, PANEL_W, 3), 255, dtype=np.float64)
        zbuf = np.full((PANEL_H, PANEL_W), np.inf)
        render_mesh(rgb, zbuf, Vmm, Fmm, cam2, span2, BONE_COLOR, PANEL_W, PANEL_H, 0, 0)
        return rgb, zbuf

    fig = plt.figure(figsize=(PANEL_W / 100, PANEL_H / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    rgb2, zbuf2 = render_v2("diagnostic")
    ax.imshow(np.clip(rgb2, 0, 255).astype(np.uint8), extent=[0, PANEL_W, 0, PANEL_H],
              interpolation="nearest", zorder=0)
    # ECU tendon course polyline (muscle/tendon paths layer)
    course = project(np.array([site_local[s] for s in core.ECU_COURSE]), cam2, span2,
                     PANEL_W, PANEL_H)
    ax.plot(course[:, 0], PANEL_H - course[:, 1], color=tuple(c / 255 for c in COURSE_COLOR),
            lw=1.6, ls="--", zorder=6)
    cpt = project(np.array([site_local["ECU-P3"]]), cam2, span2, PANEL_W, PANEL_H)[0]
    ax.text(cpt[0] + 4, PANEL_H - cpt[1], "ECU tendon course (measured waypoints)",
            fontsize=6, color=tuple(c / 255 for c in COURSE_COLOR), zorder=8,
            bbox=dict(fc="white", ec="none", alpha=0.7, pad=0.8))
    # sites (unoccluded xray markers)
    site_offsets = {"TRIlat-P5": (6, 18), "ANC-P2": (-72, 26), "BRA-P4": (14, 28),
                    "BRA-P3": (-78, -12), "PT-P2": (12, -22), "ECU-P2": (-84, -34)}
    for s in core.RENDER_SITES:
        p = project(np.array([site_local[s]]), cam2, span2, PANEL_W, PANEL_H)[0]
        col = FLEXOR_COLOR if s in core.FLEXORS else EXTENSOR_COLOR
        ax.plot([p[0]], [PANEL_H - p[1]], "o", ms=4.5, color=tuple(c / 255 for c in col),
                zorder=7, markeredgecolor="black", markeredgewidth=0.4)
        dx, dy = site_offsets[s]
        ax.plot([p[0], p[0] + dx * 0.85], [PANEL_H - p[1], PANEL_H - p[1] + dy * 0.85],
                lw=0.6, color="gray", zorder=7)
        ax.text(p[0] + dx, PANEL_H - p[1] + dy, s, fontsize=6, color="black", zorder=8,
                bbox=dict(fc="white", ec="none", alpha=0.7, pad=0.6))
    # volar / dorsal arrows from ulna origin (+x volar, -x dorsal; rest frame)
    o2 = project(np.array([[0, 0, 0]]), cam2, span2, PANEL_W, PANEL_H)[0]
    for d, lab, col in ((np.array([46.0, 0, 0]), "volar +x", VOLAR_COLOR),
                        (np.array([-46.0, 0, 0]), "dorsal -x", DORSAL_COLOR)):
        tip = project(np.array([d]), cam2, span2, PANEL_W, PANEL_H)[0]
        draw_arrow_2d(ax, o2[:2], tip[:2], tuple(c / 255 for c in col))
        ax.text(tip[0] + 3, PANEL_H - tip[1] + 8, lab, fontsize=7,
                color=tuple(c / 255 for c in col), zorder=8)
    compose_panel(ax, rgb2, zbuf2, "V2 ulna attachment close-up (source rest frame, mm)",
                  "diagnostic")
    fig.canvas.draw()
    buf = np.asarray(fig.canvas.buffer_rgba())[:, :, :3]
    sheet[0:PANEL_H, 2 * PANEL_W:3 * PANEL_W] = buf
    plt.close(fig)

    fig = plt.figure(figsize=(PANEL_W / 100, PANEL_H / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    rgb2c, zbuf2c = render_v2("clean")
    compose_panel(ax, rgb2c, zbuf2c, "V2 ulna attachment close-up", "clean")
    fig.canvas.draw()
    buf = np.asarray(fig.canvas.buffer_rgba())[:, :, :3]
    sheet[0:PANEL_H, 3 * PANEL_W:4 * PANEL_W] = buf
    plt.close(fig)

    def v2_visibility(mode):
        if mode == "clean":
            return {
                "layers": [], "label_ids": [], "selected_ids": [],
                "required_subject_ids": ["source_ulna_mesh"],
                "observed_subject_ids": ["source_ulna_mesh"],
                "missing_subject_ids": [], "occlusion_mode": "depth_tested",
                "tag_bindings": [],
            }
        subjects = ["source_ulna_mesh", "site_TRIlat-P5", "site_ANC-P2", "site_BRA-P4",
                    "site_BRA-P3", "site_PT-P2", "site_ECU-P2", "ecu_tendon_course",
                    "source_volar_axis_x", "source_dorsal_axis_x"]
        labels = ["L-ulna"] + [f"L-{s}" for s in subjects[1:7]] + \
                 ["L-ecu-course", "L-volar", "L-dorsal"]
        bindings = [{"label_id": l, "subject_id": s} for l, s in zip(labels, subjects)]
        return {
            "layers": ["selected bones/joints", "muscle/tendon paths", "attachment sites",
                       "frame axes", "stable 3D labels"],
            "label_ids": labels, "selected_ids": subjects[:7],
            "required_subject_ids": ["source_ulna_mesh", "site_PT-P2", "source_volar_axis_x"],
            "observed_subject_ids": subjects, "missing_subject_ids": [],
            "occlusion_mode": "mixed", "tag_bindings": bindings,
        }

    cam2_meta = {
        "frame_id": "source_rest_frame(+x volar,+y up,+z right; chimanoid.xml rest, axis-aligned asserted)",
        "coordinate_unit": "mm", "handedness": "right",
        "orientation_convention": "quaternion_wxyz_camera_to_frame",
        "forward_axis": "-Z", "up_axis": "+Y",
        "near_far_planes": [near2, far2],
        "viewport_resolution": [PANEL_W, PANEL_H],
        "aspect_ratio": PANEL_W / PANEL_H,
        "projection": "orthographic",
        "orthographic_span": float(span2),
        "sample_mode": "fixed_bookmark",
        "samples": [dict(cam2, tick=t) for t in (0, 3)],
    }
    manifest_views.append({"view_id": PROFILE["views"][1], "mode": "diagnostic",
                           "pair_id": "V2", "state_binding": state_binding,
                           "artifact_locator": {"kind": "image", "region": "pixel_rectangle",
                                                "pixel_rectangle": [2 * PANEL_W, 0, PANEL_W, PANEL_H]},
                           "camera": cam2_meta, "visibility": v2_visibility("diagnostic")})
    manifest_views.append({"view_id": PROFILE["views"][1], "mode": "clean",
                           "pair_id": "V2", "state_binding": state_binding,
                           "artifact_locator": {"kind": "image", "region": "pixel_rectangle",
                                                "pixel_rectangle": [3 * PANEL_W, 0, PANEL_W, PANEL_H]},
                           "camera": cam2_meta, "visibility": v2_visibility("clean")})

    # ------------- V3: orthogonal side and oblique views (trajectory) --------
    target3 = Vmm.mean(0)
    span3 = 360.0
    dirs = [  # (direction from target, up hint, name)
        (core.unit([1.0, 0.0, 0.0]), "anterior (+x view)"),
        (core.unit([-1.0, 0.0, 0.0]), "posterior (-x view)"),
        (core.unit([-0.55, 0.25, -1.0]), "left-lateral oblique (-z,+x up-tilt)"),
        (core.unit([0.35, 1.0, 0.0]), "superior (+y view)"),
    ]
    dist3 = 320.0
    cams3 = [cam_sample(target3 + d * dist3, target3, [0, 1, 0]) for d, _ in dirs]
    near3, far3 = 1.0, 2000.0

    for row, mode in ((1, "diagnostic"), (2, "clean")):
        for k, (cam3, (_, name)) in enumerate(zip(cams3, dirs)):
            rgb = np.full((PANEL_H, PANEL_W, 3), 255, dtype=np.float64)
            zbuf = np.full((PANEL_H, PANEL_W), np.inf)
            render_mesh(rgb, zbuf, Vmm, Fmm, cam3, span3, BONE_COLOR, PANEL_W, PANEL_H, 0, 0)
            fig = plt.figure(figsize=(PANEL_W / 100, PANEL_H / 100), dpi=100)
            ax = fig.add_axes([0, 0, 1, 1])
            if mode == "diagnostic":
                ax.imshow(np.clip(rgb, 0, 255).astype(np.uint8),
                          extent=[0, PANEL_W, 0, PANEL_H], interpolation="nearest", zorder=0)
                # frame axes at the ulna origin (unoccluded overlay)
                origin3 = np.array([0.0, 0.0, 0.0])
                o3 = project(np.array([origin3]), cam3, span3, PANEL_W, PANEL_H)[0]
                for d3, lab, col in ((np.array([60.0, 0, 0]), "volar +x", VOLAR_COLOR),
                                     (np.array([-60.0, 0, 0]), "dorsal -x", DORSAL_COLOR),
                                     (np.array([0, 60.0, 0]), "+y", (0, 0, 0)),
                                     (np.array([0, 0, 60.0]), "+z right", (0, 120, 0))):
                    tip = project(np.array([d3]), cam3, span3, PANEL_W, PANEL_H)[0]
                    draw_arrow_2d(ax, o3[:2], tip[:2], tuple(c / 255 for c in col))
                    ax.text(tip[0] + 2, PANEL_H - tip[1] + 2, lab, fontsize=5.6,
                            color=tuple(c / 255 for c in col), zorder=8)
                compose_panel(ax, rgb, zbuf, f"V3 {name}", "diagnostic")
            else:
                compose_panel(ax, rgb, zbuf, "V3 trajectory frame", "clean")
            fig.canvas.draw()
            buf = np.asarray(fig.canvas.buffer_rgba())[:, :, :3]
            y0 = row * PANEL_H
            x0 = k * PANEL_W
            sheet[y0:y0 + PANEL_H, x0:x0 + PANEL_W] = buf
            plt.close(fig)

    def v3_visibility(mode):
        if mode == "clean":
            return {
                "layers": [], "label_ids": [], "selected_ids": [],
                "required_subject_ids": ["source_ulna_mesh"],
                "observed_subject_ids": ["source_ulna_mesh"],
                "missing_subject_ids": [], "occlusion_mode": "depth_tested",
                "tag_bindings": [],
            }
        subjects = ["source_ulna_mesh", "source_volar_axis_x", "source_dorsal_axis_x",
                    "source_frame_axis_up_y", "source_frame_axis_right_z"]
        labels = ["L-ulna", "L-volar", "L-dorsal", "L-up", "L-right"]
        bindings = [{"label_id": l, "subject_id": s} for l, s in zip(labels, subjects)]
        return {
            "layers": ["selected bones/joints", "frame axes", "stable 3D labels"],
            "label_ids": labels, "selected_ids": ["source_ulna_mesh"],
            "required_subject_ids": ["source_ulna_mesh"],
            "observed_subject_ids": subjects, "missing_subject_ids": [],
            "occlusion_mode": "mixed", "tag_bindings": bindings,
        }

    cam3_meta = {
        "frame_id": "source_rest_frame(+x volar,+y up,+z right; chimanoid.xml rest, axis-aligned asserted)",
        "coordinate_unit": "mm", "handedness": "right",
        "orientation_convention": "quaternion_wxyz_camera_to_frame",
        "forward_axis": "-Z", "up_axis": "+Y",
        "near_far_planes": [near3, far3],
        "viewport_resolution": [PANEL_W, PANEL_H],
        "aspect_ratio": PANEL_W / PANEL_H,
        "projection": "orthographic",
        "orthographic_span": float(span3),
        "sample_mode": "sampled_trajectory",
        "interpolation": "linear_position_target_slerp_orientation",
        "samples": [dict(c, tick=t) for t, c in enumerate(cams3)],
    }
    manifest_views.append({"view_id": PROFILE["views"][2], "mode": "diagnostic",
                           "pair_id": "V3", "state_binding": state_binding,
                           "artifact_locator": {"kind": "image", "region": "pixel_rectangle",
                                                "pixel_rectangle": [0, PANEL_H, SHEET_W, PANEL_H]},
                           "camera": cam3_meta, "visibility": v3_visibility("diagnostic")})
    manifest_views.append({"view_id": PROFILE["views"][2], "mode": "clean",
                           "pair_id": "V3", "state_binding": state_binding,
                           "artifact_locator": {"kind": "image", "region": "pixel_rectangle",
                                                "pixel_rectangle": [0, 2 * PANEL_H, SHEET_W, PANEL_H]},
                           "camera": cam3_meta, "visibility": v3_visibility("clean")})

    # ------------------------------- write sheet + manifest ------------------
    png_path = EVIDENCE / "capture_sheet.png"
    plt.imsave(png_path, sheet, format="png")
    capture_sha = hashlib.sha256(png_path.read_bytes()).hexdigest()
    subject_sha = hashlib.sha256((EVIDENCE / "state_snapshot.json").read_bytes()).hexdigest()

    manifest = {
        "schema": "chimera.visual_capture_manifest.v1",
        "task_id": "A01", "card_id": "ONT-A01",
        "attempt_id": "fb552e4136ef4bfdaaa93686fb063e78",
        "run_id": RUN_ID,
        "subject_sha256": subject_sha,
        "capture_sha256": capture_sha,
        "profile_id": "anatomy",
        "tick_interval": [0, 3],
        "render": {
            "backend": "numpy-zbuffer-software-raster-cpu + matplotlib Agg compose",
            "native_engine_frames": False,
            "deterministic": True, "gpu_used": False,
            "occlusion_semantics": "mesh true z-buffer; diagnostic overlays (labels, arrows, "
                                   "box, course) intentionally unoccluded = xray semantics, "
                                   "declared occlusion_mode 'mixed'; clean rows depth_tested",
            "honesty": "NOT native application frames; anatomy evidence component capture",
        },
        "views": manifest_views,
    }

    # validate structurally with the canonical campaign validator (read-only)
    sys.path.insert(0, r"E:/PythonChimera/tools/monkey_campaign")
    from visual_capture import validate_manifest
    context = {"task_id": "A01", "subject_sha256": subject_sha, "run_id": RUN_ID,
               "capture_sha256": capture_sha, "tick_interval": [0, 3]}
    structural = validate_manifest(manifest, context, PROFILE)
    assert structural["structurally_valid"] is True

    (EVIDENCE / "capture_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    (EVIDENCE / "capture_context.json").write_text(
        json.dumps(context, indent=2, sort_keys=True), encoding="utf-8")
    provenance = {
        "schema": "chimera.ota01_visual_provenance.v1",
        "honest_label": "deterministic CPU offline render (numpy z-buffer + Agg text); "
                        "not native engine frames; subject is anatomy evidence records",
        "panels": {
            "V1": "target pack mesh (monkey_birth.bin, sha 550a5b3e...) whole body, "
                  "frame triad (+z anterior/+y up/-x right), boxed right forearm region, "
                  "elbow_R/wrist_R labels; clean pair = mesh only",
            "V2": "vendor ulna.stl (sha 71026415..., authored scale 1,1.2,1) in mm, six "
                  "labeled sites (flexors crimson, extensors blue), ECU tendon course, "
                  "volar +x / dorsal -x arrows; clean pair = bone only",
            "V3": "four-bookmark trajectory: anterior, posterior, left-lateral oblique, "
                  "superior; volar/dorsal/up/right arrows; clean strip = bone only",
        },
        "structural_validation": structural,
        "outcome_bound": "captures the AMBIGUITY_RECORDED state of numerical_receipt.json",
    }
    (EVIDENCE / "visual_provenance.json").write_text(
        json.dumps(provenance, indent=2, sort_keys=True), encoding="utf-8")
    return manifest, structural


def main() -> int:
    manifest, structural = build_everything()
    print("structurally_valid:", structural["structurally_valid"],
          "views:", structural["view_count"])
    print("wrote", EVIDENCE / "capture_sheet.png")
    print("wrote", EVIDENCE / "capture_manifest.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
