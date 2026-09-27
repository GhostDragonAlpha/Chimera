"""ONT-A02 visual capture: deterministic CPU raster of the frozen anatomy views.

Honesty label (also carried in the manifest `render` block): geometry is
rasterized by a numpy z-buffer software rasterizer (true per-pixel depth test,
fixed light, no randomness) and composed/labeled with matplotlib Agg on CPU.
These are NOT native engine frames; nothing here claims an application run.
The claim subject is the A02 anatomy evidence (radioulnar definition, B4
result, before/after radius mapping), which the anatomy profile serves with
component evidence.

Views (PREREGISTRATION, frozen):
  V1 whole-creature overview          - target pack mesh (birth), frame axes,
                                        forearm region box, BEFORE/AFTER radius
                                        anchors (target world frame, m)
  V2 local attachment close-up        - elbow->wrist edge, BEFORE vs AFTER
                                        proximal anchors with the 5.1158 mm
                                        gap, all 16 radius site globals before
                                        (filled) and after (open), PT tendon
                                        course (the newly-defined chain) before
                                        and after (target frame, mm)
  V3 orthogonal side and oblique      - source ulna, 4-bookmark sampled
                                        trajectory: anterior, posterior,
                                        left-lateral oblique, superior; the
                                        23.0746 mm / 51.63 deg radius body
                                        origin offset vector (source rest
                                        frame, mm)
Each declared view gets a diagnostic + clean pair (identical camera/state per
pair). Diagnostic rows: occlusion 'mixed' (mesh depth-tested, overlay markers
and labels intentionally unoccluded = xray semantics). Clean rows:
'depth_tested' (true z-buffer, no overlays).

Falsifier guards (PREREGISTRATION FC): every camera is framed deterministically
from the PROJECTED BOUNDS of its declared subject point set plus a uniform
FRAME_MARGIN (fit_camera) and guarded by assert_in_bounds, so no declared
subject point can be clipped; the state snapshot sha256 is recorded before and
after rendering (view toggles must preserve the physical state hash).

Render machinery (camera basis, z-buffer, bounds fit) is carried over from the
review-accepted ONT-A01 renderer pattern (attempt d7edda352388470092b17a35e17391ba,
review 21f80a5b correction); the panels, subjects and overlays are A02-owned.

Writes: evidence/capture_sheet.png, evidence/capture_manifest.json,
evidence/capture_context.json, evidence/visual_provenance.json. Validates the
manifest structurally with the canonical campaign validator before returning.
CPU-only, deterministic; run with `python -B`.
"""
from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE / "evidence"
sys.path.insert(0, str(HERE))
import ota02_radioulnar as core  # noqa: E402

PANEL_W, PANEL_H = 480, 360
SHEET_COLS, SHEET_ROWS = 4, 3
SHEET_W, SHEET_H = PANEL_W * SHEET_COLS, PANEL_H * SHEET_ROWS
RUN_ID = "ONT-A02-ota02-deterministic-cpu-20260926"

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

LIGHT = np.array([0.35, 0.8, 0.5])
LIGHT = LIGHT / np.linalg.norm(LIGHT)
CLEAN_COLOR = np.array([0.72, 0.70, 0.66])
BONE_COLOR = np.array([0.80, 0.78, 0.74])
SKIN_COLOR = np.array([0.62, 0.58, 0.52])
BEFORE_COLOR = (20, 20, 20)      # near-black: BEFORE anchor / sites
AFTER_COLOR = (200, 30, 30)      # crimson: AFTER anchor / sites
PT_COLOR = (240, 140, 20)        # orange: PT tendon course (newly-defined chain)
OFFSET_COLOR = (160, 20, 160)    # purple: source radioulnar offset vector
VOLAR_COLOR = (200, 20, 20)
DORSAL_COLOR = (20, 20, 120)
FRAME_MARGIN = 0.08


# ------------------------------------------------------------ quaternion ----
def mat_to_quat_wxyz(R):
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


def fit_camera(points, anchor_target, direction, dist, aspect, margin=FRAME_MARGIN):
    """Deterministic framing from projected bounds (no hand-tuned spans)."""
    direction = core.unit(np.asarray(direction, float))
    anchor_target = np.asarray(anchor_target, float)
    pos0 = anchor_target + direction * dist
    Xc, Yc, Zc, fwd = camera_basis(pos0, anchor_target, [0, 1, 0])
    rel = np.asarray(points, float) - anchor_target
    xc, yc = rel @ Xc, rel @ Yc
    target = anchor_target + Xc * ((xc.max() + xc.min()) / 2.0) \
        + Yc * ((yc.max() + yc.min()) / 2.0)
    position = target + direction * dist
    span = max(float(yc.max() - yc.min()),
               float((xc.max() - xc.min()) / aspect)) * (1.0 + margin)
    return position, target, float(span)


def panel_inset(W, H, margin=FRAME_MARGIN):
    return W * margin / (2.0 * (1.0 + margin)), H * margin / (2.0 * (1.0 + margin))


def assert_in_bounds(points, cam, span, W, H, margin=FRAME_MARGIN):
    """Generation-time falsifier guard ('clipped/occluded subject fails')."""
    p = project(np.asarray(points, float), cam, span, W, H)
    inx, iny = panel_inset(W, H, margin)
    eps = 1e-6
    ok = (p[:, 0].min() >= inx - eps and p[:, 0].max() <= W - inx + eps
          and p[:, 1].min() >= iny - eps and p[:, 1].max() <= H - iny + eps)
    assert ok, (f"declared subject exceeds framed panel: px[{p[:, 0].min():.3f},"
                f"{p[:, 0].max():.3f}] py[{p[:, 1].min():.3f},{p[:, 1].max():.3f}]"
                f" on {W}x{H} (margin {margin})")


# ---------------------------------------------------------- z-buffer pass ----
def render_mesh(rgb, zbuf, V, F, cam, span, color, W, H):
    pos = np.array(cam["position"])
    Xc, Yc, Zc, fwd = camera_basis(cam["position"], cam["target"], [0, 1, 0])
    rel = V - pos
    xc, yc, dc = rel @ Xc, rel @ Yc, rel @ fwd
    aspect = W / H
    px = (xc / (span * aspect) + 0.5) * W
    py = (1.0 - (yc / span + 0.5)) * H
    tri_px, tri_py, tri_d = px[F], py[F], dc[F]
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
def draw_arrow_2d(fig, p0, p1, color, lw=1.6):
    fig.annotate("", xy=(p1[0], p1[1]), xytext=(p0[0], p0[1]),
                 xycoords="data", textcoords="data",
                 arrowprops=dict(arrowstyle="->", color=color, lw=lw))


def label_offset_inside(anchor_xy, dx, dy, W, H, pad=6.0, pad_top=22.0):
    x, y = anchor_xy[0] + dx, anchor_xy[1] + dy
    if not (pad <= x <= W - pad):
        dx = -dx
    if not (pad <= y <= H - pad_top):
        dy = -dy
    return dx, dy


def put_label(ax, xy, dx, dy, text, W, H, color="black", fontsize=6.0,
              ha="left"):
    ldx, ldy = label_offset_inside(xy, dx, dy, W, H)
    ax.text(xy[0] + ldx, xy[1] + ldy, text, fontsize=fontsize, color=color,
            zorder=8, ha=ha,
            bbox=dict(fc="white", ec="none", alpha=0.7, pad=0.6))


def compose_panel(fig, rgb, title, mode):
    fig.imshow(np.clip(rgb, 0, 255).astype(np.uint8), extent=[0, PANEL_W, 0, PANEL_H],
               interpolation="nearest", zorder=0)
    fig.set_xlim(0, PANEL_W)
    fig.set_ylim(0, PANEL_H)
    fig.axis("off")
    tag = "DIAGNOSTIC" if mode == "diagnostic" else "CLEAN"
    fig.text(4, PANEL_H - 4, f"{title} [{tag}]", fontsize=7, color="black",
             ha="left", va="top", zorder=10,
             bbox=dict(fc="white", ec="none", alpha=0.75, pad=1.2))


def grab(fig, sheet, x0, y0):
    fig.canvas.draw()
    buf = np.asarray(fig.canvas.buffer_rgba())[:, :, :3]
    sheet[y0:y0 + PANEL_H, x0:x0 + PANEL_W] = buf
    import matplotlib.pyplot as plt
    plt.close(fig)


def new_panel():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig = plt.figure(figsize=(PANEL_W / 100, PANEL_H / 100), dpi=100)
    return fig, fig.add_axes([0, 0, 1, 1])


def load_ulna_mesh():
    """Binary STL -> (V, F) with the authored chimanoid scale (1, 1.2, 1)."""
    b = core.INPUT_ULNA_STL.read_bytes()
    (n,) = struct.unpack("<I", b[80:84])
    assert len(b) == 84 + n * 50, (core.INPUT_ULNA_STL, n, len(b))
    rec = np.frombuffer(b, dtype=np.uint8, count=n * 50, offset=84).reshape(n, 50)
    floats = rec[:, :48].copy().view("<f4").reshape(n, 4, 3)
    tris = floats[:, 1:].astype(np.float64)
    verts, inv = np.unique(tris.reshape(-1, 3), axis=0, return_inverse=True)
    faces = inv.reshape(n, 3)
    scale = np.array([1.0, 1.2, 1.0])
    return verts * scale, faces.astype(np.int64)


# ------------------------------------------------------ subject builders ----
def build_subjects():
    """All A02-owned geometry for the three views, from the pinned inputs."""
    state = core.write_receipts()[0]
    joints = core.target_joints()
    elbow, wrist = joints["elbow_R"], joints["wrist_R"]
    m = state["before_after_radius_map"]
    P_new = np.array(m["right"]["P_new_m"])
    P_old = elbow  # BEFORE proximal anchor IS elbow_R (packet fitted origin)
    assert np.linalg.norm(P_old - np.array(m["right"]["P_old_m"])) <= 1e-12

    bodies, site_owner, joint_owner, tendon_paths, site_global = core.xml_world()
    declared = core.load_json("i7_receipts/00_candidate_declaration.json")
    kg = core.load_json("b4_receipts/01_known_good_records.json")
    packet = core.load_json("packet/actual_monkey_fit.json")
    seg = {s["source_body"]: s for s in packet["segments"]}["radius"]

    M = core._similarity_maps("r", bodies, site_global, declared, kg, seg)
    L_new, Pn = M["L_new"], M["P_new"]
    sites = [s for s in packet["sites"] if s["segment"] == "radius"]
    site_before = {s["name"]: np.array(s["fitted_pos_global"], float)
                   for s in sites}
    # AFTER globals: closed form pred = P_new + L_new x_loc (own construction)
    site_after = {s["name"]: Pn + L_new @ np.array(s["source_pos_local"], float)
                  for s in sites}

    # PT tendon course: the newly-defined chain's radius-owned sites (ordered)
    pt_order = [s for s in tendon_paths["PT_tendon"] if s in site_before]
    pt_before = [site_before[s] for s in pt_order]
    pt_after = [site_after[s] for s in pt_order]

    Vu, Fu = load_ulna_mesh()
    return {
        "state": state, "elbow": elbow, "wrist": wrist, "P_new": P_new,
        "P_old": P_old, "site_before": site_before, "site_after": site_after,
        "pt_order": pt_order, "pt_before": pt_before, "pt_after": pt_after,
        "Vu": Vu, "Fu": Fu,
        "gap_mm": m["right"]["gap_m"] * 1000.0,
        "offset_ulna_frame_m": state["radioulnar_definition"]
        ["offset_vector_ulna_frame_m"],
        "obliq_deg": state["radioulnar_definition"]["obliquity_deg"],
        "offset_mm": state["radioulnar_definition"]["offset_norm_mm"],
        "box_lo": np.minimum(elbow, wrist) - np.array([0.045, 0.03, 0.045]),
        "box_hi": np.maximum(elbow, wrist) + np.array([0.045, 0.03, 0.045]),
    }


def declared_subject_points(S, pair_id):
    """The declared subject point set each panel must contain (only pinned
    geometry + the drawn arrow tips). Used by fit_camera and the bounds
    regression."""
    if pair_id == "V1":
        mt_v = S["_mesh_V"]
        corners = np.array([S["box_lo"] + np.array(
            [bool((a >> s) & 1) for s in range(3)], float)
            * (S["box_hi"] - S["box_lo"]) for a in range(8)])
        return np.vstack([mt_v, S["elbow"][None, :], S["wrist"][None, :],
                          S["P_new"][None, :], corners])
    if pair_id == "V2":
        mm = 1000.0
        pts = [S["elbow"] * mm, S["wrist"] * mm, S["P_new"] * mm]
        pts += [v * mm for v in S["site_before"].values()]
        pts += [v * mm for v in S["site_after"].values()]
        # clearance tips anchored AT the subject (elbow), not at world origin
        tips = (S["elbow"] + np.array([[0.0, 0.008, 0.0],
                                       [0.0, -0.008, 0.0]])) * mm
        return np.vstack([np.array(pts), tips])
    if pair_id == "V3":
        Vmm = S["Vu"] * 1000.0
        tips = np.array([[60.0, 0.0, 0.0], [-60.0, 0.0, 0.0],
                         [0.0, 60.0, 0.0], [0.0, 0.0, 60.0]])
        return np.vstack([Vmm, tips])
    raise KeyError(pair_id)


# ------------------------------------------------------------------ build ----
def build_everything():
    EVIDENCE.mkdir(exist_ok=True)
    import matplotlib
    matplotlib.use("Agg")

    state_path = EVIDENCE / "state_snapshot.json"
    subject_sha_before = core.sha256_file(state_path)

    S = build_subjects()
    sys.path.insert(0, str(core.REFERENCE))
    from mesh_target_o1 import MonkeyTarget
    mtk = MonkeyTarget(birth_path=str(core.INPUT_BIRTH), pack_path=str(core.INPUT_PACK))
    S["_mesh_V"], S["_mesh_F"] = mtk.V, mtk.F

    sheet = np.full((SHEET_H, SHEET_W, 3), 255, dtype=np.uint8)
    manifest_views = []
    state_binding = {"kind": "state",
                     "sha256": core.sha256_file(state_path)}

    # ---------------- V1: whole-creature overview (target world frame, m) ----
    V, F = S["_mesh_V"], S["_mesh_F"]
    center = (V.min(0) + V.max(0)) / 2.0
    diag = float(np.linalg.norm(V.max(0) - V.min(0)))
    subj1 = declared_subject_points(S, "V1")
    pos1, tgt1, span1 = fit_camera(subj1, center, core.unit([0.30, 0.35, 1.0]),
                                   diag * 1.15, PANEL_W / PANEL_H)
    cam1 = cam_sample(pos1, tgt1, [0, 1, 0])
    assert_in_bounds(subj1, cam1, span1, PANEL_W, PANEL_H)

    corner_pts = np.array([S["box_lo"] + np.array(
        [bool((a >> s) & 1) for s in range(3)], float) * (S["box_hi"] - S["box_lo"])
        for a in range(8)])
    box_edges = [(a, b) for a in range(8) for b in range(8)
                 if sum(1 for s in range(3)
                        if ((a >> s) & 1) != ((b >> s) & 1)) == 1]

    def render_v1():
        rgb = np.full((PANEL_H, PANEL_W, 3), 255, dtype=np.float64)
        zbuf = np.full((PANEL_H, PANEL_W), np.inf)
        render_mesh(rgb, zbuf, V, F, cam1, span1, SKIN_COLOR, PANEL_W, PANEL_H)
        return rgb, zbuf

    rgb1d, _ = render_v1()
    fig, ax = new_panel()
    ax.imshow(np.clip(rgb1d, 0, 255).astype(np.uint8),
              extent=[0, PANEL_W, 0, PANEL_H], interpolation="nearest", zorder=0)
    corners = project(corner_pts, cam1, span1, PANEL_W, PANEL_H)
    for a, b in box_edges:
        ax.plot([corners[a, 0], corners[b, 0]],
                [PANEL_H - corners[a, 1], PANEL_H - corners[b, 1]],
                color=(0.1, 0.4, 0.9), lw=1.2, zorder=6)
    # screen-anchored world-axis triad (projected directions, unoccluded)
    origin1 = np.array([V[:, 0].min(), V[:, 1].min(), V[:, 2].max()]) \
        + np.array([0.02, 0.02, -0.02])
    o2 = project(np.array([origin1]), cam1, span1, PANEL_W, PANEL_H)[0]
    ax0, ay0 = 52, PANEL_H - 52
    for d, lab in (([0, 0, 1], "+z anterior"), ([0, 1, 0], "+y up"),
                   ([-1, 0, 0], "-x right")):
        tip3 = np.array([origin1]) + np.array(d, float) * span1 * 0.14
        t2 = project(tip3, cam1, span1, PANEL_W, PANEL_H)[0]
        v = np.array([t2[0] - o2[0], -(t2[1] - o2[1])])
        n = np.linalg.norm(v)
        if n < 1e-9:
            continue
        v = v / n * 24
        tip = (ax0 + v[0], ay0 + v[1])
        draw_arrow_2d(ax, (ax0, ay0), tip, (0.08, 0.08, 0.08))
        ax.text(tip[0] + 3, tip[1] + 3, lab, color=(0.08, 0.08, 0.08),
                fontsize=6.5, ha="left", va="bottom")
    # BEFORE/AFTER anchors (drawn even though they nearly coincide at this
    # scale; V2 carries the 5.1158 mm detail)
    pb = project(np.array([S["P_old"]]), cam1, span1, PANEL_W, PANEL_H)[0]
    pa = project(np.array([S["P_new"]]), cam1, span1, PANEL_W, PANEL_H)[0]
    ax.plot([pb[0]], [PANEL_H - pb[1]], "s", ms=5, color="black", zorder=7)
    ax.plot([pa[0]], [PANEL_H - pa[1]], "o", ms=5, color="red", zorder=7)
    put_label(ax, (pb[0], PANEL_H - pb[1]), 8, 14,
              "radius P_before=elbow_R", PANEL_W, PANEL_H, fontsize=5.6)
    put_label(ax, (pa[0], PANEL_H - pa[1]), 8, -8,
              "radius P_after=ulna.P_d", PANEL_W, PANEL_H, color="red",
              fontsize=5.6)
    for name, p3 in (("elbow_R", S["elbow"]), ("wrist_R", S["wrist"])):
        p = project(np.array([p3]), cam1, span1, PANEL_W, PANEL_H)[0]
        ax.plot([p[0]], [PANEL_H - p[1]], "+", ms=4, color="black", zorder=7)
        put_label(ax, (p[0], PANEL_H - p[1]), 6, 12, name, PANEL_W, PANEL_H,
                  fontsize=5.6)
    put_label(ax, (corners[0, 0], PANEL_H - corners[0, 1]), 6, 6,
              "U-STR forearm region", PANEL_W, PANEL_H, color=(0.1, 0.4, 0.9),
              fontsize=5.6)
    compose_panel(ax, rgb1d, "V1 whole-creature overview (target frame, m)",
                  "diagnostic")
    grab(fig, sheet, 0, 0)

    fig, ax = new_panel()
    rgb1c, _ = render_v1()
    compose_panel(ax, rgb1c, "V1 whole-creature overview", "clean")
    grab(fig, sheet, PANEL_W, 0)

    near1, far1 = 0.01, round(float(diag * 3.0), 3)
    cam1_meta = {
        "frame_id": "target_world_frame(+z anterior,+y up,-x right; O1 sec.1)",
        "coordinate_unit": "m", "handedness": "right",
        "orientation_convention": "quaternion_wxyz_camera_to_frame",
        "orientation_convention_and_values":
            f"quaternion_wxyz_camera_to_frame {cam1['orientation']}",
        "forward_axis": "-Z", "up_axis": "+Y",
        "position": cam1["position"], "target": cam1["target"],
        "distance_to_target": cam1["distance_to_target"],
        "projection": "orthographic",
        "orthographic_span": float(span1),
        "vertical_fov_or_orthographic_span": float(span1),
        "near_far_planes": [near1, far1],
        "aspect_ratio": PANEL_W / PANEL_H,
        "viewport_resolution": [PANEL_W, PANEL_H],
        "sample_mode": "fixed_bookmark",
        "camera_motion_or_bookmark_sequence": "fixed_bookmark (ticks 0,3)",
        "samples": [dict(cam1, tick=t) for t in (0, 3)],
    }

    def v1_visibility(mode):
        if mode == "clean":
            return {"layers": [], "label_ids": [], "selected_ids": [],
                    "required_subject_ids": ["target_monkey_mesh"],
                    "observed_subject_ids": ["target_monkey_mesh"],
                    "missing_subject_ids": [], "occlusion_mode": "depth_tested",
                    "tag_bindings": []}
        subjects = ["target_monkey_mesh", "target_joint_elbow_R",
                    "target_joint_wrist_R", "target_forearm_region_box",
                    "radius_anchor_P_before", "radius_anchor_P_after"]
        labels = ["L-mesh", "L-elbow_R", "L-wrist_R", "L-region-box",
                  "L-P-before", "L-P-after"]
        return {"layers": ["outer envelope", "selected bones/joints", "frame axes",
                           "stable 3D labels"],
                "label_ids": labels, "selected_ids": subjects,
                "required_subject_ids": ["target_monkey_mesh",
                                         "radius_anchor_P_before",
                                         "radius_anchor_P_after"],
                "observed_subject_ids": subjects, "missing_subject_ids": [],
                "occlusion_mode": "mixed",
                "tag_bindings": [{"label_id": l, "subject_id": s}
                                 for l, s in zip(labels, subjects)]}

    for mode, x0 in (("diagnostic", 0), ("clean", PANEL_W)):
        vis = v1_visibility(mode)
        manifest_views.append({
            "view_id": PROFILE["views"][0], "mode": mode, "pair_id": "V1",
            "state_binding": state_binding,
            "artifact_locator": {"kind": "image", "region": "pixel_rectangle",
                                 "pixel_rectangle": [x0, 0, PANEL_W, PANEL_H]},
            "camera": dict(cam1_meta, state_or_tick_interval=[0, 3]),
            "visibility": vis})

    # ---------------- V2: local attachment close-up (target frame, mm) -------
    subj2 = declared_subject_points(S, "V2") / 1000.0  # back to metres for framing
    target0 = (S["elbow"] + S["wrist"]) / 2.0
    pos2, target2, span2 = fit_camera(subj2, target0, core.unit([0.15, 0.25, 1.0]),
                                      0.30, PANEL_W / PANEL_H)
    cam2 = cam_sample(pos2, target2, [0, 1, 0])
    assert_in_bounds(subj2, cam2, span2, PANEL_W, PANEL_H)
    near2, far2 = 0.001, 1.0

    site_names = sorted(S["site_before"])
    site_pts_b = np.array([S["site_before"][n] for n in site_names])
    site_pts_a = np.array([S["site_after"][n] for n in site_names])
    pt_b = np.array(S["pt_before"]) if S["pt_before"] else np.zeros((0, 3))
    pt_a = np.array(S["pt_after"]) if S["pt_after"] else np.zeros((0, 3))

    def draw_v2(ax, annotated):
        """Geometry always; text/annotations only in the diagnostic row."""
        ax.imshow(np.full((PANEL_H, PANEL_W, 3), 255, dtype=np.uint8),
                  extent=[0, PANEL_W, 0, PANEL_H], interpolation="nearest",
                  zorder=0)
        e2d = project(np.array([S["elbow"]]), cam2, span2, PANEL_W, PANEL_H)[0]
        w2d = project(np.array([S["wrist"]]), cam2, span2, PANEL_W, PANEL_H)[0]
        ax.plot([e2d[0], w2d[0]], [PANEL_H - e2d[1], PANEL_H - w2d[1]],
                color="gray", lw=1.4, ls=":", zorder=4)
        # 16 radius sites: before filled / after open
        pb_all = project(site_pts_b, cam2, span2, PANEL_W, PANEL_H)
        pa_all = project(site_pts_a, cam2, span2, PANEL_W, PANEL_H)
        ax.plot(pb_all[:, 0], PANEL_H - pb_all[:, 1], "o", ms=2.6,
                color="black", zorder=6)
        ax.plot(pa_all[:, 0], PANEL_H - pa_all[:, 1], "o", ms=3.4,
                markerfacecolor="none", markeredgecolor="red",
                markeredgewidth=0.8, zorder=6)
        # PT tendon course (newly-defined chain), before solid / after dashed
        if len(pt_b):
            cpb = project(pt_b, cam2, span2, PANEL_W, PANEL_H)
            ax.plot(cpb[:, 0], PANEL_H - cpb[:, 1],
                    color=tuple(c / 255 for c in PT_COLOR), lw=1.6, zorder=6)
            if len(pt_a):
                cpa = project(pt_a, cam2, span2, PANEL_W, PANEL_H)
                ax.plot(cpa[:, 0], PANEL_H - cpa[:, 1],
                        color=tuple(c / 255 for c in PT_COLOR), lw=1.2,
                        ls="--", zorder=6)
        # anchors + gap arrow
        pb2 = project(np.array([S["P_old"]]), cam2, span2, PANEL_W, PANEL_H)[0]
        pa2 = project(np.array([S["P_new"]]), cam2, span2, PANEL_W, PANEL_H)[0]
        ax.plot([pb2[0]], [PANEL_H - pb2[1]], "s", ms=6, color="black", zorder=7)
        ax.plot([pa2[0]], [PANEL_H - pa2[1]], "o", ms=6, color="red", zorder=7)
        draw_arrow_2d(ax, (pb2[0], PANEL_H - pb2[1]),
                      (pa2[0], PANEL_H - pa2[1]),
                      tuple(c / 255 for c in AFTER_COLOR))
        if annotated:
            put_label(ax, (w2d[0], PANEL_H - w2d[1]), 6, 10,
                      "wrist_R (P_d, unchanged)", PANEL_W, PANEL_H, fontsize=5.6)
            put_label(ax, (pb2[0], PANEL_H - pb2[1]), 8, -14,
                      "P_before=elbow_R", PANEL_W, PANEL_H, fontsize=5.8)
            put_label(ax, (pa2[0], PANEL_H - pa2[1]), -8, 30,
                      "P_after=ulna.P_d\n(gap "
                      f"{S['gap_mm']:.4f} mm >> JOINT_EPS 1e-9)",
                      PANEL_W, PANEL_H, color="red", fontsize=5.8, ha="right")
            put_label(ax, (pb_all[0, 0], PANEL_H - pb_all[0, 1]), 6, -18,
                      "16 radius sites: before (filled) / after (open)",
                      PANEL_W, PANEL_H, fontsize=5.4)
            if len(pt_b):
                cpt = project(np.array([pt_b[0]]), cam2, span2, PANEL_W,
                              PANEL_H)[0]
                put_label(ax, (cpt[0], PANEL_H - cpt[1]), -20, -30,
                          "PT course: solid=before, dashed=after\n"
                          "(chain completed by ulna resolution)",
                          PANEL_W, PANEL_H,
                          color=tuple(c / 255 for c in PT_COLOR), fontsize=5.2,
                          ha="right")

    fig, ax = new_panel()
    draw_v2(ax, annotated=True)
    compose_panel(ax, np.full((PANEL_H, PANEL_W, 3), 255, dtype=np.float64),
                  "V2 radius before/after mapping (target frame, mm)",
                  "diagnostic")
    grab(fig, sheet, 2 * PANEL_W, 0)

    fig, ax = new_panel()
    draw_v2(ax, annotated=False)
    compose_panel(ax, np.full((PANEL_H, PANEL_W, 3), 255, dtype=np.float64),
                  "V2 radius before/after mapping", "clean")
    grab(fig, sheet, 3 * PANEL_W, 0)

    cam2_meta = {
        "frame_id": "target_world_frame(+z anterior,+y up,-x right; O1 sec.1; "
                    "panel annotations in mm)",
        "coordinate_unit": "m", "handedness": "right",
        "orientation_convention": "quaternion_wxyz_camera_to_frame",
        "orientation_convention_and_values":
            f"quaternion_wxyz_camera_to_frame {cam2['orientation']}",
        "forward_axis": "-Z", "up_axis": "+Y",
        "position": cam2["position"], "target": cam2["target"],
        "distance_to_target": cam2["distance_to_target"],
        "projection": "orthographic",
        "orthographic_span": float(span2),
        "vertical_fov_or_orthographic_span": float(span2),
        "near_far_planes": [near2, far2],
        "aspect_ratio": PANEL_W / PANEL_H,
        "viewport_resolution": [PANEL_W, PANEL_H],
        "sample_mode": "fixed_bookmark",
        "camera_motion_or_bookmark_sequence": "fixed_bookmark (ticks 0,3)",
        "samples": [dict(cam2, tick=t) for t in (0, 3)],
    }

    def v2_visibility(mode):
        if mode == "clean":
            return {"layers": [], "label_ids": [], "selected_ids": [],
                    "required_subject_ids": ["radius_edge_elbow_wrist",
                                             "radius_anchor_P_before",
                                             "radius_anchor_P_after"],
                    "observed_subject_ids": ["radius_edge_elbow_wrist",
                                             "radius_anchor_P_before",
                                             "radius_anchor_P_after",
                                             "radius_sites_16_before",
                                             "radius_sites_16_after"],
                    "missing_subject_ids": [], "occlusion_mode": "depth_tested",
                    "tag_bindings": []}
        subjects = ["radius_edge_elbow_wrist", "radius_anchor_P_before",
                    "radius_anchor_P_after", "radius_sites_16_before",
                    "radius_sites_16_after", "pt_tendon_course"]
        labels = ["L-edge", "L-P-before", "L-P-after", "L-sites",
                  "L-sites-after", "L-pt-course"]
        return {"layers": ["selected bones/joints", "muscle/tendon paths",
                           "attachment sites", "stable 3D labels"],
                "label_ids": labels, "selected_ids": subjects,
                "required_subject_ids": ["radius_anchor_P_before",
                                         "radius_anchor_P_after",
                                         "radius_sites_16_before"],
                "observed_subject_ids": subjects, "missing_subject_ids": [],
                "occlusion_mode": "mixed",
                "tag_bindings": [{"label_id": l, "subject_id": s}
                                 for l, s in zip(labels, subjects)]}

    for mode, x0 in (("diagnostic", 2 * PANEL_W), ("clean", 3 * PANEL_W)):
        vis = v2_visibility(mode)
        manifest_views.append({
            "view_id": PROFILE["views"][1], "mode": mode, "pair_id": "V2",
            "state_binding": state_binding,
            "artifact_locator": {"kind": "image", "region": "pixel_rectangle",
                                 "pixel_rectangle": [x0, 0, PANEL_W, PANEL_H]},
            "camera": dict(cam2_meta, state_or_tick_interval=[0, 3]),
            "visibility": vis})

    # ------------- V3: orthogonal side and oblique views (source frame) ------
    Vmm, Fmm = S["Vu"] * 1000.0, S["Fu"]
    off_mm = np.array(S["offset_ulna_frame_m"]) * 1000.0  # radius origin in ulna frame
    target0_3 = Vmm.mean(0)
    dirs = [
        (core.unit([1.0, 0.0, 0.0]), "anterior (+x view)"),
        (core.unit([-1.0, 0.0, 0.0]), "posterior (-x view)"),
        (core.unit([-0.55, 0.25, -1.0]), "left-lateral oblique (-z,+x up-tilt)"),
        (core.unit([0.35, 1.0, 0.0]), "superior (+y view)"),
    ]
    dist3 = 320.0
    subj3 = declared_subject_points(S, "V3")
    fits3 = [fit_camera(subj3, target0_3, d, dist3, PANEL_W / PANEL_H)
             for d, _ in dirs]
    span3 = max(s for _, _, s in fits3)
    cams3 = [cam_sample(p, t, [0, 1, 0]) for p, t, _ in fits3]
    for cam3 in cams3:
        assert_in_bounds(subj3, cam3, span3, PANEL_W, PANEL_H)
    near3, far3 = 1.0, 2000.0

    for row, mode in ((1, "diagnostic"), (2, "clean")):
        for k, (cam3, (_, name)) in enumerate(zip(cams3, dirs)):
            rgb = np.full((PANEL_H, PANEL_W, 3), 255, dtype=np.float64)
            zbuf = np.full((PANEL_H, PANEL_W), np.inf)
            render_mesh(rgb, zbuf, Vmm, Fmm, cam3, span3, BONE_COLOR,
                        PANEL_W, PANEL_H)
            fig, ax = new_panel()
            if mode == "diagnostic":
                ax.imshow(np.clip(rgb, 0, 255).astype(np.uint8),
                          extent=[0, PANEL_W, 0, PANEL_H],
                          interpolation="nearest", zorder=0)
                origin3 = np.array([0.0, 0.0, 0.0])
                o3 = project(np.array([origin3]), cam3, span3, PANEL_W, PANEL_H)[0]
                r3 = project(np.array([off_mm]), cam3, span3, PANEL_W, PANEL_H)[0]
                draw_arrow_2d(ax, (o3[0], PANEL_H - o3[1]),
                              (r3[0], PANEL_H - r3[1]),
                              tuple(c / 255 for c in OFFSET_COLOR))
                ax.plot([r3[0]], [PANEL_H - r3[1]], "o", ms=4,
                        color=tuple(c / 255 for c in OFFSET_COLOR), zorder=7)
                put_label(ax, (r3[0], PANEL_H - r3[1]), 6, 8,
                          "radius body origin "
                          f"({S['offset_mm']:.4f} mm, {S['obliq_deg']:.2f} deg)",
                          PANEL_W, PANEL_H,
                          color=tuple(c / 255 for c in OFFSET_COLOR),
                          fontsize=5.6)
                for d3, lab, col in ((np.array([60.0, 0, 0]), "volar +x", VOLAR_COLOR),
                                     (np.array([-60.0, 0, 0]), "dorsal -x", DORSAL_COLOR),
                                     (np.array([0, 60.0, 0]), "+y proximal", (0, 0, 0)),
                                     (np.array([0, 0, 60.0]), "+z right", (0, 120, 0))):
                    tip = project(np.array([d3]), cam3, span3, PANEL_W, PANEL_H)[0]
                    draw_arrow_2d(ax, (o3[0], PANEL_H - o3[1]),
                                  (tip[0], PANEL_H - tip[1]),
                                  tuple(c / 255 for c in col))
                    put_label(ax, (tip[0], PANEL_H - tip[1]), 2, 2, lab,
                              PANEL_W, PANEL_H, color=tuple(c / 255 for c in col),
                              fontsize=5.2)
                compose_panel(ax, rgb, f"V3 {name}", "diagnostic")
            else:
                compose_panel(ax, rgb, "V3 trajectory frame", "clean")
            grab(fig, sheet, k * PANEL_W, row * PANEL_H)

    def v3_visibility(mode):
        if mode == "clean":
            return {"layers": [], "label_ids": [], "selected_ids": [],
                    "required_subject_ids": ["source_ulna_mesh"],
                    "observed_subject_ids": ["source_ulna_mesh"],
                    "missing_subject_ids": [], "occlusion_mode": "depth_tested",
                    "tag_bindings": []}
        subjects = ["source_ulna_mesh", "radius_body_origin_offset",
                    "source_volar_axis_x", "source_dorsal_axis_x",
                    "source_frame_axis_proximal_y", "source_frame_axis_right_z"]
        labels = ["L-ulna", "L-radius-origin", "L-volar", "L-dorsal",
                  "L-proximal", "L-right"]
        return {"layers": ["selected bones/joints", "frame axes",
                           "stable 3D labels"],
                "label_ids": labels, "selected_ids": subjects,
                "required_subject_ids": ["source_ulna_mesh",
                                         "radius_body_origin_offset"],
                "observed_subject_ids": subjects, "missing_subject_ids": [],
                "occlusion_mode": "mixed",
                "tag_bindings": [{"label_id": l, "subject_id": s}
                                 for l, s in zip(labels, subjects)]}

    cam3_meta = {
        "frame_id": "source_rest_frame(+x volar,+y proximal,+z right; "
                    "chimanoid.xml rest, axis-aligned asserted)",
        "coordinate_unit": "mm", "handedness": "right",
        "orientation_convention": "quaternion_wxyz_camera_to_frame",
        "orientation_convention_and_values": "quaternion_wxyz_camera_to_frame "
                                             "(per-sample in samples)",
        "forward_axis": "-Z", "up_axis": "+Y",
        "projection": "orthographic",
        "orthographic_span": float(span3),
        "vertical_fov_or_orthographic_span": float(span3),
        "near_far_planes": [near3, far3],
        "aspect_ratio": PANEL_W / PANEL_H,
        "viewport_resolution": [PANEL_W, PANEL_H],
        "sample_mode": "sampled_trajectory",
        "interpolation": "linear_position_target_slerp_orientation",
        "camera_motion_or_bookmark_sequence": "sampled_trajectory "
                                              "(anterior, posterior, "
                                              "left-lateral oblique, superior)",
        "samples": [dict(c, tick=t) for t, c in enumerate(cams3)],
    }
    for mode, y0 in (("diagnostic", PANEL_H), ("clean", 2 * PANEL_H)):
        vis = v3_visibility(mode)
        manifest_views.append({
            "view_id": PROFILE["views"][2], "mode": mode, "pair_id": "V3",
            "state_binding": state_binding,
            "artifact_locator": {"kind": "image", "region": "pixel_rectangle",
                                 "pixel_rectangle": [0, y0, SHEET_W, PANEL_H]},
            "camera": dict(cam3_meta,
                           position=cam3_meta["samples"][0]["position"],
                           target=cam3_meta["samples"][0]["target"],
                           distance_to_target=cam3_meta["samples"][0]
                           ["distance_to_target"],
                           state_or_tick_interval=[0, 3]),
            "visibility": vis})

    # ------------------------------- write sheet + manifest ------------------
    png_path = EVIDENCE / "capture_sheet.png"
    import matplotlib.pyplot as plt
    plt.imsave(png_path, sheet, format="png")
    capture_sha = core.sha256_file(png_path)
    subject_sha = core.sha256_file(state_path)
    assert subject_sha == subject_sha_before, "state snapshot mutated by render"
    assert subject_sha == state_binding["sha256"]

    manifest = {
        "schema": "chimera.visual_capture_manifest.v1",
        "task_id": "A02", "card_id": "ONT-A02",
        "attempt_id": "b4a2b12b8c854e55bc400c64a502c85c",
        "run_id": RUN_ID,
        "subject_sha256": subject_sha,
        "capture_sha256": capture_sha,
        "profile_id": "anatomy",
        "tick_interval": [0, 3],
        "render": {
            "backend": "numpy-zbuffer-software-raster-cpu + matplotlib Agg compose",
            "native_engine_frames": False,
            "deterministic": True, "gpu_used": False,
            "state_hash_before_render": subject_sha_before,
            "state_hash_after_render": subject_sha,
            "state_hash_preserved_under_view_toggles": True,
            "occlusion_semantics": "mesh true z-buffer; diagnostic overlays "
                                   "(labels, arrows, sites, courses) intentionally "
                                   "unoccluded = xray semantics, declared "
                                   "occlusion_mode 'mixed'; clean rows depth_tested",
            "honesty": "NOT native application frames; anatomy evidence "
                       "component capture for A02",
        },
        "views": manifest_views,
    }

    sys.path.insert(0, r"E:/PythonChimera/tools/monkey_campaign")
    from visual_capture import validate_manifest
    context = {"task_id": "A02", "subject_sha256": subject_sha, "run_id": RUN_ID,
               "capture_sha256": capture_sha, "tick_interval": [0, 3]}
    structural = validate_manifest(manifest, context, PROFILE)
    assert structural["structurally_valid"] is True, structural

    (EVIDENCE / "capture_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    (EVIDENCE / "capture_context.json").write_text(
        json.dumps(context, indent=2, sort_keys=True), encoding="utf-8")
    provenance = {
        "schema": "chimera.ota02_visual_provenance.v1",
        "honest_label": "deterministic CPU offline render (numpy z-buffer + Agg "
                        "text); not native engine frames; subject is the A02 "
                        "anatomy evidence (radioulnar definition, B4 result, "
                        "before/after radius mapping)",
        "framing": "cameras framed from the PROJECTED BOUNDS of each view's "
                   "declared subject point set (declared_subject_points) + "
                   "uniform 8% frame margin (fit_camera); generation-time guard "
                   "assert_in_bounds; bounds regression in "
                   "test_ota02_radioulnar.py",
        "state_hash": {
            "before_render": subject_sha_before,
            "after_render": subject_sha,
            "preserved": True,
            "note": "view toggles (diagnostic/clean, bookmark changes) never "
                    "touch the physical state snapshot",
        },
        "panels": {
            "V1": "target pack mesh (monkey_birth.bin, sha 550a5b3e...) whole "
                  "body, frame triad via region box, boxed right forearm region, "
                  "elbow_R/wrist_R labels, BEFORE/AFTER radius anchors; clean "
                  "pair = mesh only",
            "V2": "elbow->wrist edge with BEFORE (elbow_R) vs AFTER (ulna.P_d) "
                  "anchors, the 5.1158 mm forced-closure gap arrow, all 16 "
                  "radius site globals before (filled) / after (open), PT "
                  "tendon course before (solid) / after (dashed); clean pair = "
                  "geometry only",
            "V3": "vendor ulna.stl (sha in state inputs, authored scale 1,1.2,1) "
                  "in mm, four-bookmark trajectory, the 23.0746 mm / 51.63 deg "
                  "radius body-origin offset vector, volar/dorsal/proximal/"
                  "right axes; clean strip = bone only",
        },
        "structural_validation": structural,
        "outcome_bound": "captures the numerical_receipt.json outcome state",
    }
    (EVIDENCE / "visual_provenance.json").write_text(
        json.dumps(provenance, indent=2, sort_keys=True), encoding="utf-8")
    return manifest, structural


def main() -> int:
    manifest, structural = build_everything()
    print("structurally_valid:", structural["structurally_valid"],
          "views:", structural["view_count"])
    print("state hash preserved:",
          manifest["render"]["state_hash_preserved_under_view_toggles"])
    print("wrote", EVIDENCE / "capture_sheet.png")
    print("wrote", EVIDENCE / "capture_manifest.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
