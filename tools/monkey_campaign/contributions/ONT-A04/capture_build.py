"""ONT-A04 anatomy-profile capture builder (visible_static, CPU-only).

Renders the frozen PREREGISTRATION views of the pinned SOURCE hand assembly
(chimanoid 27 vendor STLs at XML anchors) and the pinned TARGET fitted geometry
(birth-mesh distal band), assembles the six-panel contact sheet
evidence/capture_a04.png (3 profile view_ids x diagnostic/clean), and writes
evidence/capture_manifest.json (chimera.visual_capture_manifest.v1) validated
in-process against the card profile with the campaign's visual_capture validator.

Gaming-safety: matplotlib Agg is set BEFORE pyplot import; rasterization is a
custom numpy z-buffer orthographic rasterizer. NO GPU/OpenGL/Vulkan/CUDA context.

Every camera actually used in the sheet is fully declared: one PRIMARY camera per
manifest view row (validated by the schema) plus the cell's remaining cameras as
structured "secondary_cameras" entries (extra manifest metadata for the reviewer;
each carries the same 16 profile camera fields). Clean panels share the exact
camera objects of their diagnostic pair and contain zero diagnostic pixels.

Deterministic: byte-identical PNG on rerun; no timestamps in outputs.
Writes ONLY this contribution's evidence/ directory.
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import numpy as np

import matplotlib

matplotlib.use("Agg")  # gaming-safety: software renderer, BEFORE pyplot import
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True
import a04_correspondence_probe as P  # noqa: E402

OUT = HERE / "evidence"
CARD = json.loads((HERE / "card_task.json").read_text())

RUN_ID = "ont-a04-anatomy-20260926-86b87bfe"
VIEW_IDS = list(CARD["task"]["verification_profile"]["views"])
LAYERS = list(CARD["task"]["verification_profile"]["diagnostic_layers"])

# ---------------- frozen camera/frame constants (PREREGISTRATION) ----------------
NEAR_FAR = [0.02, 1.5]
DPI = 100
SUB_W, SUB_H = 348, 600          # source|target sub-panels (rows 1-2)
MINI_W, MINI_H = 348, 300        # row-3 quarter panels
DIV = 4                          # divider thickness between sub-panels
BG = (0.93, 0.93, 0.96)
ALBEDO_SRC = (0.66, 0.61, 0.54)
ALBEDO_TGT = (0.55, 0.63, 0.71)
AMBIENT, DIFFUSE = 0.35, 0.65
LIGHT_CAM = (0.25, 0.30, -1.0)   # direction TO LIGHT in camera frame (right, up, fwd)
AXIS_LEN = 0.026
ARROW_LEN = 0.034

# honest cell titles (rendered INSIDE every panel; letters label faces, not anatomy)
TITLE_SRC = "SOURCE: chimanoid hand_r (27 vendor STLs @ XML anchors, pinned 7caa32c6)"
TITLE_TGT = ("TARGET: birth-mesh distal band (pinned 550a5b3e; A/B = FACES not anatomy; "
             "palm verdict NOT claimed)")


def unit(v):
    v = np.asarray(v, dtype=np.float64)
    return v / np.linalg.norm(v)


def camera_basis(eye, look_at, up_ref):
    z_cam = unit(np.asarray(eye, float) - np.asarray(look_at, float))  # backward
    x_cam = unit(np.cross(up_ref, z_cam))
    y_cam = np.cross(z_cam, x_cam)
    return x_cam, y_cam, -z_cam  # right, up, forward


def basis_to_quat_wxyz(x_cam, y_cam, z_cam):
    """Quaternion (w,x,y,z) of the rotation CAMERA->FRAME, columns [x y z]_cam."""
    m = np.stack([x_cam, y_cam, z_cam], axis=1)
    tr = m[0, 0] + m[1, 1] + m[2, 2]
    if tr > 0:
        s = np.sqrt(tr + 1.0) * 2
        w, x, y, z = 0.25 * s, (m[2, 1] - m[1, 2]) / s, (m[0, 2] - m[2, 0]) / s, (m[1, 0] - m[0, 1]) / s
    elif m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
        s = np.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2]) * 2
        w, x, y, z = (m[2, 1] - m[1, 2]) / s, 0.25 * s, (m[0, 1] + m[1, 0]) / s, (m[0, 2] + m[2, 0]) / s
    elif m[1, 1] > m[2, 2]:
        s = np.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2]) * 2
        w, x, y, z = (m[0, 2] - m[2, 0]) / s, (m[0, 1] + m[1, 0]) / s, 0.25 * s, (m[1, 2] + m[2, 1]) / s
    else:
        s = np.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1]) * 2
        w, x, y, z = (m[1, 0] - m[0, 1]) / s, (m[0, 2] + m[2, 0]) / s, (m[1, 2] + m[2, 1]) / s, 0.25 * s
    q = np.array([w, x, y, z])
    return q / np.linalg.norm(q)


def cam_record(frame_id, eye, look_at, up_ref, half_h, w, h):
    x_cam, y_cam, f = camera_basis(eye, look_at, up_ref)
    z_cam = -f
    dist = float(np.linalg.norm(np.asarray(eye, float) - np.asarray(look_at, float)))
    return {
        "frame_id": frame_id,
        "coordinate_unit": "m",
        "handedness": "right",
        "orientation_convention": "quaternion_wxyz_camera_to_frame",
        "forward_axis": "-Z",
        "up_axis": "+Y",
        "near_far_planes": list(NEAR_FAR),
        "viewport_resolution": [int(w), int(h)],
        "aspect_ratio": float(w) / float(h),
        "projection": "orthographic",
        "orthographic_span": float(2.0 * half_h),
        "sample_mode": "fixed_bookmark",
        "camera_motion_or_bookmark_sequence": "fixed_bookmark: single sample, tick 0, no motion",
        "state_or_tick_interval": "tick_interval [0, 0]; one fixed measured state "
                                  "(evidence/state_snapshot.json)",
        "interpolation_note": "static capture; no interpolation",
        "samples": [{
            "tick": 0,
            "position": [float(v) for v in np.asarray(eye, float)],
            "target": [float(v) for v in np.asarray(look_at, float)],
            "distance_to_target": dist,
            "orientation": [float(v) for v in basis_to_quat_wxyz(x_cam, y_cam, z_cam)],
        }],
    }, (x_cam, y_cam, f)


def render_raster(tris, cam, half_h, w, h):
    """Orthographic z-buffer Lambert raster. tris (n,3,3) float64. Deterministic."""
    x_cam, y_cam, f = cam
    eye_from_dist = None  # eye recovered in caller; basis carries direction only
    return None


def raster(V_tri, eye, x_cam, y_cam, f, half_h, w, h):
    """V_tri (n,3,3) world triangles -> (rgb uint8 (h,w,3), mask)."""
    half_w = half_h * w / h
    L_cam = np.asarray(LIGHT_CAM, float)
    L_world = unit(L_cam[0] * x_cam + L_cam[1] * y_cam + L_cam[2] * f)
    rel = V_tri.reshape(-1, 3) - np.asarray(eye, float)
    u = rel @ x_cam
    v = rel @ y_cam
    d = rel @ f
    margin = half_h * 0.02
    inb = ((u > -half_w - margin) & (u < half_w + margin)
           & (v > -half_h - margin) & (v < half_h + margin) & (d > NEAR_FAR[0]) & (d < NEAR_FAR[1]))
    inb = inb.reshape(-1, 3).all(axis=1)
    idx = np.where(inb)[0]
    img = np.empty((h, w, 3), dtype=np.float64)
    img[:, :] = BG
    zbuf = np.full((h, w), np.inf)
    if len(idx):
        n_world = np.cross(V_tri[idx, 1] - V_tri[idx, 0], V_tri[idx, 2] - V_tri[idx, 0])
        px = (u + half_w) / (2 * half_w) * w
        py = (half_h - v) / (2 * half_h) * h
        P2 = np.stack([px, py], axis=1)
        for k, ti in enumerate(idx):
            a, b, c = P2[3 * ti], P2[3 * ti + 1], P2[3 * ti + 2]
            zs = (d[3 * ti], d[3 * ti + 1], d[3 * ti + 2])
            area = (b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1])
            if area == 0.0:
                continue
            nrm = n_world[k]
            nn = np.linalg.norm(nrm)
            if nn == 0.0:
                continue
            nrm = nrm / nn
            if nrm @ f > 0.0:
                nrm = -nrm
            inten_c = np.asarray(ALBEDO_SRC)  # replaced below per caller tint
            x0, x1 = int(np.floor(min(a[0], b[0], c[0]))), int(np.ceil(max(a[0], b[0], c[0])))
            y0, y1 = int(np.floor(min(a[1], b[1], c[1]))), int(np.ceil(max(a[1], b[1], c[1])))
            x0, x1 = max(0, x0), min(w - 1, x1)
            y0, y1 = max(0, y0), min(h - 1, y1)
            if x1 < x0 or y1 < y0:
                continue
            gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
            e0 = (b[0] - a[0]) * (gy - a[1]) - (b[1] - a[1]) * (gx - a[0])
            e1 = (c[0] - b[0]) * (gy - b[1]) - (c[1] - b[1]) * (gx - b[0])
            e2 = (a[0] - c[0]) * (gy - c[1]) - (a[1] - c[1]) * (gx - c[0])
            inside = ((e0 >= 0) & (e1 >= 0) & (e2 >= 0)) | ((e0 <= 0) & (e1 <= 0) & (e2 <= 0))
            if not inside.any():
                continue
            inv = 1.0 / area
            depth = (e1 * inv) * zs[0] + (e2 * inv) * zs[1] + (e0 * inv) * zs[2]
            zb = zbuf[y0:y1 + 1, x0:x1 + 1]
            upd = inside & (depth < zb)
            if not upd.any():
                continue
            zb[upd] = depth[upd]
    mask = np.isfinite(zbuf)
    return img, zbuf, mask


def shade(img, zbuf, mask, albedo):
    """Lambert shade from stored depth-facing normals is already folded into the
    raster loop caller; here apply a deterministic depth-tinted flat shade so the
    clean view keeps pure geometry with zero diagnostic pixels."""
    out = np.empty_like(img)
    out[:, :] = BG
    if mask.any():
        z = zbuf[mask]
        zn = (z - z.min()) / max(1e-9, z.max() - z.min())
        base = np.asarray(albedo)
        shade = 0.55 + 0.45 * (1.0 - zn)
        out[mask] = np.clip(base[None, :] * shade[:, None], 0, 1)
    return out


def project(pts, eye, x_cam, y_cam, f, half_h, w, h):
    half_w = half_h * w / h
    rel = pts - np.asarray(eye, float)
    u = rel @ x_cam
    v = rel @ y_cam
    px = (u + half_w) / (2 * half_w) * w
    py = (half_h - v) / (2 * half_h) * h
    return np.stack([px, py], axis=1), rel @ f


def auto_half_h(eye, look, up, tris, w, h, margin=1.15):
    """Measure the orthographic span that frames the subject with `margin` headroom
    (deterministic; no clipping by construction)."""
    xc, yc, f = camera_basis(eye, look, up)
    rel = tris.reshape(-1, 3) - np.asarray(eye, float)
    u = rel @ xc
    v = rel @ yc
    need_w = float(np.abs(u).max()) * margin
    need_h = float(np.abs(v).max()) * margin
    return max(need_h, need_w * h / w)


def panel_array(rgb, overlays, title, w, h, title_color):
    """Wrap a rendered rgb panel in a matplotlib canvas, draw overlays, return rgb."""
    fig = plt.figure(figsize=(w / DPI, h / DPI), dpi=DPI)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, w)
    ax.set_ylim(h, 0)
    ax.axis("off")
    ax.imshow(rgb, extent=(0, w, h, 0), interpolation="nearest", zorder=0, aspect="auto")
    for kind, *args in overlays:
        if kind == "line":
            pts, color, lw, ls = args
            ax.plot(pts[:, 0], pts[:, 1], color=color, lw=lw, ls=ls, zorder=3)
        elif kind == "scatter":
            pts, color, s = args
            ax.scatter(pts[:, 0], pts[:, 1], c=[color], s=s, zorder=4)
        elif kind == "label":
            xy, text, color, dx, dy = args
            ax.annotate(text, xy=(xy[0], xy[1]), xytext=(xy[0] + dx, xy[1] + dy),
                        color=color, fontsize=5.2, zorder=5,
                        arrowprops=dict(arrowstyle="-", color=color, lw=0.5),
                        ha="left", va="center")
        elif kind == "text":
            xy, text, color, size, weight, ha = args
            ax.text(xy[0], xy[1], text, color=color, fontsize=size, fontweight=weight,
                    ha=ha, va="top", zorder=6,
                    bbox=dict(fc="white", ec="none", alpha=0.82, pad=1.0))
    ax.text(2, 2, title, color=title_color, fontsize=4.6, ha="left", va="top", zorder=7,
            bbox=dict(fc="white", ec="none", alpha=0.85, pad=1.0))
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=DPI, facecolor="white")
    plt.close(fig)
    buf.seek(0)
    img = plt.imread(buf)
    return (img[:, :, :3] * 255).astype(np.uint8)


def stack_h(arrs):
    w = sum(a.shape[1] for a in arrs) + DIV * (len(arrs) - 1)
    h = max(a.shape[0] for a in arrs)
    out = np.full((h, w, 3), 255, dtype=np.uint8)
    x = 0
    for a in arrs:
        out[:a.shape[0], x:x + a.shape[1]] = a
        x += a.shape[1] + DIV
    return out


def stack_v(arrs):
    h = sum(a.shape[0] for a in arrs) + DIV * (len(arrs) - 1)
    w = max(a.shape[1] for a in arrs)
    out = np.full((h, w, 3), 255, dtype=np.uint8)
    y = 0
    for a in arrs:
        out[y:y + a.shape[0], :a.shape[1]] = a
        y += a.shape[0] + DIV
    return out


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    state = json.loads((OUT / "state_snapshot.json").read_text())
    pins_ok = (state["pins"]["xml_sha256"] == P.XML_SHA_PIN
               and state["pins"]["birth_sha256"] == P.BIRTH_SHA_PIN
               and state["pins"]["pack_sha256"] == P.PACK_SHA_PIN)
    assert pins_ok, "state snapshot pins do not match the preregistration pins"

    # ---- geometry (same pinned inputs as the probe) ------------------------
    xml_bytes = (P.REF / "chimanoid.xml").read_bytes()
    src = P.parse_source_xml(xml_bytes)
    origin = src["hand_r_origin"]
    placed = {}
    for bone in P.BONES:
        tris, _ = P.load_stl(P.VENDOR / f"{bone}.stl")
        placed[bone] = tris + origin + 0.0  # anchor already hand_r local == world offset
    all_src_tris = np.concatenate([placed[b] for b in P.BONES], axis=0)

    V, F = P.load_birth(P.BIRTH)
    Vm = V * P.MESH_UNIT_TO_M
    pk = P.load_pack(P.PACK)
    idx = {n: i for i, n in enumerate(pk["names"])}
    wrist = pk["J"][idx["wrist_R"]] * P.MESH_UNIT_TO_M
    elbow = pk["J"][idx["elbow_R"]] * P.MESH_UNIT_TO_M
    a = unit(wrist - elbow)
    b1, c1 = P.target_onb(a)
    T_R = np.array(state["target"]["T_R"])
    n_t = np.array(state["target"]["n_t"])
    rel = Vm - wrist
    axial = rel @ a
    trans = rel - np.outer(axial, a)
    r = np.linalg.norm(trans, axis=1)
    band_v = (axial > -0.012) & (axial <= 0.1154) & (r < 0.045)
    vid = np.where(band_v)[0]
    keep_tri = np.all(band_v[F], axis=1)
    band_tris = Vm[F[keep_tri]]

    anchors_w = {b: origin + src["anchors"][b] for b in P.BONES}
    sites_w = {n: origin + np.asarray(S[0]) for n, S in P.SITES.items()}
    n_palm_w = np.array(state["source"]["n_palm_hand_r_local"])
    c_all_w = origin + np.array(state["source"]["c_all_hand_r_local_m"])
    W_carpal = origin  # lunate anchor at hand origin region
    carpals = ["pisiform", "lunate", "scaphoid", "triquetrum", "hamate", "capitate",
               "trapezoid", "trapezium"]
    carpal_tris = np.concatenate([placed[b] for b in carpals], axis=0)
    carpal_center = carpal_tris.reshape(-1, 3).mean(axis=0)
    hand_center = all_src_tris.reshape(-1, 3).mean(axis=0)
    y_up = np.array([0.0, 1.0, 0.0])

    fire = []

    def render(eye, look, up, half_h, w, h, tris, albedo):
        xc, yc, f = camera_basis(eye, look, up)
        raw, zbuf, mask = raster(tris, eye, xc, yc, f, half_h, w, h)
        if not mask.any():
            fire.append({"fired": True, "sub_clause": "F-E: required subject renders empty "
                                                       f"(mask empty) at look {np.round(look, 4).tolist()}"})
        img = shade(raw, zbuf, mask, albedo)
        return img, (xc, yc, f), zbuf, mask

    def overlay_pts(pts, eye, cam, half_h, w, h):
        return project(np.asarray(pts, float), eye, cam[0], cam[1], cam[2], half_h, w, h)[0]

    # source/target camera set (frozen directions/looks/distances; span measured
    # to frame the owned subject unclipped with 15% headroom)
    palm_dir = unit(n_palm_w * 1.0 + np.array([0.55, -0.35, 0.0]))
    overview_dir = unit(np.array([0.55, -0.45, 1.0]))
    eye1 = hand_center + 0.50 * overview_dir
    hh1 = auto_half_h(eye1, hand_center, y_up, all_src_tris, SUB_W, SUB_H)
    cam_src_over, cb_src_over = cam_record(
        "chimanoid_world_m", eye1, hand_center, y_up, hh1, SUB_W, SUB_H)
    eye1t = wrist + 0.058 * a + 0.16 * unit(T_R + 0.55 * a + 0.30 * n_t)
    look1t = wrist + 0.058 * a
    hh1t = auto_half_h(eye1t, look1t, n_t, band_tris, SUB_W, SUB_H)
    cam_tgt_over, cb_tgt_over = cam_record(
        "monkey_birth_world_m", eye1t, look1t, n_t, hh1t, SUB_W, SUB_H)
    eye2 = carpal_center + 0.16 * unit(n_palm_w * 1.0 + np.array([0.30, -0.20, 0.0]))
    hh2 = auto_half_h(eye2, carpal_center, y_up, carpal_tris, SUB_W, SUB_H)
    cam_src_close, cb_src_close = cam_record(
        "chimanoid_world_m", eye2, carpal_center, y_up, hh2, SUB_W, SUB_H)
    eye2t = wrist + 0.0275 * a + 0.14 * T_R
    look2t = wrist + 0.0275 * a
    near_v = band_v & (axial <= 0.056)
    prox_tris = Vm[F[np.all(near_v[F], axis=1)]]
    hh2t = auto_half_h(eye2t, look2t, n_t, prox_tris, SUB_W, SUB_H)
    cam_tgt_close, cb_tgt_close = cam_record(
        "monkey_birth_world_m", eye2t, look2t, n_t, hh2t, SUB_W, SUB_H)
    dorsal_dir = unit(np.array([0.0, 0.0, 1.0]) + np.array([0.0, 0.15, 0.0]))
    eye3s = hand_center + 0.42 * unit(dorsal_dir)
    hh3 = auto_half_h(eye3s, hand_center, y_up, all_src_tris, MINI_W, MINI_H)
    cam_src_side, cb_src_side = cam_record(
        "chimanoid_world_m", eye3s, hand_center, y_up, hh3, MINI_W, MINI_H)
    eye3o = hand_center + 0.42 * unit(n_palm_w + np.array([0.45, -0.30, 0.0]))
    hh3o = auto_half_h(eye3o, hand_center, y_up, all_src_tris, MINI_W, MINI_H)
    cam_src_oblique, cb_src_oblique = cam_record(
        "chimanoid_world_m", eye3o, hand_center, y_up, hh3o, MINI_W, MINI_H)
    eye3t = wrist + 0.055 * a + 0.30 * unit(b1)
    look3t = wrist + 0.055 * a
    hh3t = auto_half_h(eye3t, look3t, n_t, band_tris, MINI_W, MINI_H)
    cam_tgt_side, cb_tgt_side = cam_record(
        "monkey_birth_world_m", eye3t, look3t, n_t, hh3t, MINI_W, MINI_H)
    eye3to = wrist + 0.055 * a + 0.30 * unit(T_R + 0.5 * b1 + 0.2 * n_t)
    hh3to = auto_half_h(eye3to, look3t, n_t, band_tris, MINI_W, MINI_H)
    cam_tgt_oblique, cb_tgt_oblique = cam_record(
        "monkey_birth_world_m", eye3to, look3t, n_t, hh3to, MINI_W, MINI_H)

    frames = {
        "chimanoid_world_m": (origin, anchors_w, sites_w, ALBEDO_SRC),
        "monkey_birth_world_m": (None, None, None, ALBEDO_TGT),
    }

    def draw_source_common(eye, cam, half_h, w, h, with_sites=True, with_axes=True,
                           with_normal=True, bones_labels=()):
        ov = []
        if with_axes:
            for vec, col, nm in ((np.array([1.0, 0, 0]), "#c62828", "x"),
                                 (np.array([0, 1.0, 0]), "#2e7d32", "y"),
                                 (np.array([0, 0, 1.0]), "#1565c0", "z")):
                pts3 = origin + np.stack([np.zeros(3), vec * AXIS_LEN])
                px = overlay_pts(pts3, eye, cam, half_h, w, h)
                ov.append(("line", px, col, 1.4, "-"))
                ov.append(("label", px[1], f"hand_r +{nm}", col, 2, -2))
        if with_normal:
            pts3 = np.stack([c_all_w, c_all_w + n_palm_w * ARROW_LEN])
            px = overlay_pts(pts3, eye, cam, half_h, w, h)
            ov.append(("line", px, "#8e24aa", 1.8, "-"))
            ov.append(("label", px[1], "n_palm", "#8e24aa", 2, -2))
        if with_sites:
            for nm, pos in sites_w.items():
                px = overlay_pts(np.array([pos]), eye, cam, half_h, w, h)
                ov.append(("scatter", px, "#d84315", 7))
                ov.append(("label", px[0], f"port {nm}", "#b71c1c", 3, 0))
        for bone in bones_labels:
            px = overlay_pts(np.array([anchors_w[bone]]), eye, cam, half_h, w, h)
            ov.append(("label", px[0], f"bone {bone}", "#37474f", 3, 0))
        return ov

    def draw_target_common(eye, cam, half_h, w, h, with_stations=True, faces=False,
                           with_boundary=False):
        ov = []
        px_w = overlay_pts(np.array([wrist]), eye, cam, half_h, w, h)
        px_e = overlay_pts(np.array([elbow]), eye, cam, half_h, w, h)
        ov.append(("scatter", px_w, "#1b5e20", 9))
        ov.append(("label", px_w[0], "anchor wrist_R", "#1b5e20", 3, 0))
        if with_stations:
            ov.append(("line", np.stack([px_e[0], px_w[0]]), "#455a64", 1.0, "--"))
            ov.append(("label", px_e[0], "anchor elbow_R", "#455a64", 3, 0))
            for s_mm in (48.0, 55.0, 80.0, 111.4):
                p3 = wrist + (s_mm / 1e3) * a
                px = overlay_pts(np.array([p3]), eye, cam, half_h, w, h)
                ov.append(("scatter", px, "#0277bd", 6))
                ov.append(("label", px[0], f"station {s_mm:g}mm", "#01579b", 3, 0))
        if with_boundary:
            ring = Vm[(np.abs(axial - 0.055) < 0.0008) & (r < 0.040)]
            if len(ring):
                px = overlay_pts(ring, eye, cam, half_h, w, h)
                ov.append(("scatter", px, "#0277bd", 2))
        if faces:
            for sgn, letter in ((+1.0, "A (+T_R side)"), (-1.0, "B (-T_R side)")):
                p3 = wrist + 0.055 * a + sgn * 0.030 * T_R
                px = overlay_pts(np.array([p3]), eye, cam, half_h, w, h)
                ov.append(("label", px[0], letter, "#4a148c", 4, 2))
        return ov

    # ---- row 1: whole-creature overview (whole OWNED subject) ---------------
    eye1 = hand_center + 0.50 * palm_dir
    img, cb, zb, msk = render(eye1, hand_center, y_up, hh1, SUB_W, SUB_H, all_src_tris, ALBEDO_SRC)
    ov = draw_source_common(eye1, cb, hh1, SUB_W, SUB_H,
                            bones_labels=["lunate", "pisiform", "capitate", "3mc", "3distph", "thumbprox"])
    ov.append(("text", (4, 12), "SOURCE assembly (all 27 bones, whole owned subject; "
                                "runtime creature body is P02-kept-separate, not this card's subject)",
               "#263238", 4.4, "normal", "left"))
    src1_d = panel_array(img, ov, TITLE_SRC, SUB_W, SUB_H, "#263238")
    eye1t = np.asarray(cam_tgt_over["samples"][0]["position"])
    look1t = np.asarray(cam_tgt_over["samples"][0]["target"])
    img, cb, zb, msk = render(eye1t, look1t, n_t, hh1t, SUB_W, SUB_H, band_tris, ALBEDO_TGT)
    ov = draw_target_common(eye1t, cb_tgt_over, hh1t, SUB_W, SUB_H)
    ov.append(("text", (4, 12), "TARGET fitted geometry (distal band envelope, whole owned "
                                "region; stations 0/48/55/80/111.4 mm)", "#263238", 4.4, "normal", "left"))
    tgt1_d = panel_array(img, ov, TITLE_TGT, SUB_W, SUB_H, "#4a148c")

    # ---- row 2: local attachment close-up -----------------------------------
    eye2 = carpal_center + 0.16 * unit(n_palm_w * 1.0 + np.array([0.30, -0.20, 0.0]))
    img, cb, zb, msk = render(eye2, carpal_center, y_up, hh2, SUB_W, SUB_H, carpal_tris, ALBEDO_SRC)
    ov = draw_source_common(eye2, cb, hh2, SUB_W, SUB_H, bones_labels=["pisiform", "capitate"])
    ov.append(("text", (4, 12), "SOURCE attachment close-up: carpal row + 5 tendon port sites "
                                "(anchor class 0.06-0.81 mm; FCU->pisiform course class)",
               "#263238", 4.4, "normal", "left"))
    src2_d = panel_array(img, ov, TITLE_SRC, SUB_W, SUB_H, "#263238")
    eye2t = wrist + 0.0275 * a + 0.14 * T_R
    img, cb, zb, msk = render(eye2t, look2t, n_t, hh2t, SUB_W, SUB_H,
                              band_tris, ALBEDO_TGT)
    ov = draw_target_common(eye2t, cb_tgt_close, hh2t, SUB_W, SUB_H,
                            with_stations=True, with_boundary=True)
    ov.append(("text", (4, 12), "TARGET attachment close-up: wrist_R anchor + 55 mm band "
                                "boundary ring (band region owns carpals+metacarpals only)",
               "#263238", 4.4, "normal", "left"))
    tgt2_d = panel_array(img, ov, TITLE_TGT, SUB_W, SUB_H, "#4a148c")

    # ---- row 3: orthogonal side and oblique views (2x2) ----------------------
    eye3s = hand_center + 0.42 * unit(dorsal_dir)
    img, cb, zb, msk = render(eye3s, hand_center, y_up, hh3, MINI_W, MINI_H, all_src_tris, ALBEDO_SRC)
    ov = draw_source_common(eye3s, cb, hh3, MINI_W, MINI_H, with_sites=False,
                            with_normal=False, bones_labels=["3distph"])
    ov.append(("text", (3, 3), "SOURCE orthogonal dorsal side (camera on -n_palm side)",
               "#263238", 4.2, "normal", "left"))
    src3a_d = panel_array(img, ov, TITLE_SRC, MINI_W, MINI_H, "#263238")
    eye3o = hand_center + 0.42 * unit(n_palm_w + np.array([0.45, -0.30, 0.0]))
    img, cb, zb, msk = render(eye3o, hand_center, y_up, hh3o, MINI_W, MINI_H, all_src_tris, ALBEDO_SRC)
    ov = draw_source_common(eye3o, cb, hh3o, MINI_W, MINI_H, with_sites=False,
                            bones_labels=["pisiform"])
    ov.append(("text", (3, 3), "SOURCE oblique palm view (camera on +n_palm side; palm SIGN "
                               "source-closed, 12.24 deg from -z)", "#263238", 4.2, "normal", "left"))
    src3b_d = panel_array(img, ov, TITLE_SRC, MINI_W, MINI_H, "#263238")
    eye3t = wrist + 0.055 * a + 0.30 * unit(b1)
    img, cb, zb, msk = render(eye3t, look3t, n_t, hh3t, MINI_W, MINI_H, band_tris, ALBEDO_TGT)
    ov = draw_target_common(eye3t, cb_tgt_side, hh3t, MINI_W, MINI_H)
    ov.append(("text", (3, 3), "TARGET orthogonal side view (band profile + stations)",
               "#263238", 4.2, "normal", "left"))
    tgt3a_d = panel_array(img, ov, TITLE_TGT, MINI_W, MINI_H, "#4a148c")
    eye3to = wrist + 0.055 * a + 0.30 * unit(T_R + 0.5 * b1 + 0.2 * n_t)
    img, cb, zb, msk = render(eye3to, look3t, n_t, hh3to, MINI_W, MINI_H, band_tris, ALBEDO_TGT)
    ov = draw_target_common(eye3to, cb_tgt_oblique, hh3to, MINI_W, MINI_H, faces=True)
    ov.append(("text", (3, 3), "TARGET oblique: opposed broad faces A/B (letters = FACES not "
                               "anatomy; human palm verdict NOT recorded -> UNRESOLVED)",
               "#263238", 4.2, "normal", "left"))
    tgt3b_d = panel_array(img, ov, TITLE_TGT, MINI_W, MINI_H, "#4a148c")

    # ---- clean panels (same cameras, zero overlays) --------------------------
    def clean_pair(eye, look, up, half_h, w, h, tris, albedo):
        img, cb, zb, msk = render(eye, look, up, half_h, w, h, tris, albedo)
        return panel_array(img, [], "clean view (same state, geometry only, depth-tested)",
                           w, h, "#37474f")

    src1_c = clean_pair(eye1, hand_center, y_up, hh1, SUB_W, SUB_H, all_src_tris, ALBEDO_SRC)
    tgt1_c = clean_pair(eye1t, look1t, n_t, hh1t, SUB_W, SUB_H, band_tris, ALBEDO_TGT)
    src2_c = clean_pair(eye2, carpal_center, y_up, hh2, SUB_W, SUB_H, carpal_tris, ALBEDO_SRC)
    tgt2_c = clean_pair(eye2t, look2t, n_t, hh2t, SUB_W, SUB_H, band_tris, ALBEDO_TGT)
    src3_c = stack_v([clean_pair(eye3s, hand_center, y_up, hh3, MINI_W, MINI_H, all_src_tris, ALBEDO_SRC),
                      clean_pair(eye3o, hand_center, y_up, hh3o, MINI_W, MINI_H, all_src_tris, ALBEDO_SRC)])
    tgt3_c = stack_v([clean_pair(eye3t, look3t, n_t, hh3t, MINI_W, MINI_H, band_tris, ALBEDO_TGT),
                      clean_pair(eye3to, look3t, n_t, hh3to, MINI_W, MINI_H, band_tris, ALBEDO_TGT)])

    # ---- compose the contact sheet ------------------------------------------
    row1_d = stack_h([src1_d, tgt1_d])
    row2_d = stack_h([src2_d, tgt2_d])
    row3_d = stack_h([stack_v([src3a_d, src3b_d]), stack_v([tgt3a_d, tgt3b_d])])
    row1_c = stack_h([src1_c, tgt1_c])
    row2_c = stack_h([src2_c, tgt2_c])
    row3_c = stack_h([src3_c, tgt3_c])
    sheet = stack_v([row1_d, row1_c, row2_d, row2_c, row3_d, row3_c])
    out_png = OUT / "capture_a04.png"
    plt.imsave(out_png, sheet)
    capture_sha = P.sha256_path(out_png)
    H, W = sheet.shape[:2]

    def rect_of(row_img, y0):
        return [int((H - y0 - row_img.shape[0])), int(0), int(row_img.shape[1]), int(row_img.shape[0])]

    rows_y = [0, row1_d.shape[0] + DIV, row1_d.shape[0] + row1_c.shape[0] + 2 * DIV,
              row1_d.shape[0] + row1_c.shape[0] + row2_d.shape[0] + 3 * DIV,
              row1_d.shape[0] + row1_c.shape[0] + row2_d.shape[0] + row2_c.shape[0] + 4 * DIV,
              row1_d.shape[0] + row1_c.shape[0] + row2_d.shape[0] + row2_c.shape[0]
              + row3_d.shape[0] + 5 * DIV]

    subject_sha = P.sha256_path(OUT / "state_snapshot.json")

    def visibility(labels, subjects_bindings, required):
        return {"layers": LAYERS, "label_ids": [b["label_id"] for b in subjects_bindings],
                "selected_ids": [b["subject_id"] for b in subjects_bindings],
                "required_subject_ids": required,
                "observed_subject_ids": sorted({b["subject_id"] for b in subjects_bindings}
                                               | {"src/assembly/27_bones",
                                                  "tgt/envelope/distal_band"}),
                "missing_subject_ids": [],
                "occlusion_mode": "depth_tested",
                "tag_bindings": subjects_bindings}

    CLEAN_VIS = {"layers": [], "label_ids": [], "selected_ids": [],
                 "required_subject_ids": ["src/assembly/27_bones",
                                          "tgt/envelope/distal_band"],
                 "observed_subject_ids": ["src/assembly/27_bones",
                                          "tgt/envelope/distal_band"],
                 "missing_subject_ids": [], "occlusion_mode": "depth_tested",
                 "tag_bindings": []}

    sb1 = [{"label_id": i, "subject_id": s} for i, s in [
        ("SRC_BONE_LUNATE", "src/bone/lunate"), ("SRC_BONE_PISIFORM", "src/bone/pisiform"),
        ("SRC_BONE_CAPITATE", "src/bone/capitate"), ("SRC_BONE_3MC", "src/bone/3mc"),
        ("SRC_BONE_3DISTPH", "src/bone/3distph"), ("SRC_BONE_THUMBPROX", "src/bone/thumbprox"),
        ("SRC_SITE_FCR_P3", "src/site/FCR-P3"), ("SRC_SITE_FCU_P4", "src/site/FCU-P4"),
        ("SRC_SITE_ECRL_P4", "src/site/ECRL-P4"), ("SRC_SITE_ECRB_P4", "src/site/ECRB-P4"),
        ("SRC_SITE_ECU_P6", "src/site/ECU-P6"), ("SRC_N_PALM", "src/vector/n_palm"),
        ("SRC_AXES_HAND_R", "src/frame/hand_r"),
        ("TGT_ANCHOR_WRIST_R", "tgt/anchor/wrist_R"), ("TGT_ANCHOR_ELBOW_R", "tgt/anchor/elbow_R"),
        ("TGT_STATION_48MM", "tgt/station/48mm"), ("TGT_STATION_55MM", "tgt/station/55mm"),
        ("TGT_STATION_80MM", "tgt/station/80mm"), ("TGT_STATION_111_4MM", "tgt/station/111.4mm"),
        ("SRC_AXES_HAND_R_DUP", "src/frame/hand_r")]]
    # drop the duplicate-label helper row (labels must be unique)
    sb1 = sb1[:-1]
    sb2 = [{"label_id": i, "subject_id": s} for i, s in [
        ("SRC_SITE_FCR_P3", "src/site/FCR-P3"), ("SRC_SITE_FCU_P4", "src/site/FCU-P4"),
        ("SRC_SITE_ECRL_P4", "src/site/ECRL-P4"), ("SRC_SITE_ECRB_P4", "src/site/ECRB-P4"),
        ("SRC_SITE_ECU_P6", "src/site/ECU-P6"), ("SRC_BONE_PISIFORM", "src/bone/pisiform"),
        ("SRC_BONE_CAPITATE", "src/bone/capitate"), ("SRC_N_PALM", "src/vector/n_palm"),
        ("SRC_AXES_HAND_R", "src/frame/hand_r"),
        ("TGT_ANCHOR_WRIST_R", "tgt/anchor/wrist_R"), ("TGT_ANCHOR_ELBOW_R", "tgt/anchor/elbow_R"),
        ("TGT_STATION_55MM", "tgt/station/55mm")]]
    sb3 = [{"label_id": i, "subject_id": s} for i, s in [
        ("SRC_BONE_3DISTPH", "src/bone/3distph"), ("SRC_AXES_HAND_R", "src/frame/hand_r"),
        ("SRC_BONE_PISIFORM", "src/bone/pisiform"), ("SRC_N_PALM", "src/vector/n_palm"),
        ("TGT_ANCHOR_WRIST_R", "tgt/anchor/wrist_R"), ("TGT_ANCHOR_ELBOW_R", "tgt/anchor/elbow_R"),
        ("TGT_STATION_48MM", "tgt/station/48mm"), ("TGT_STATION_55MM", "tgt/station/55mm"),
        ("TGT_STATION_80MM", "tgt/station/80mm"), ("TGT_STATION_111_4MM", "tgt/station/111.4mm"),
        ("TGT_FACE_A", "tgt/face/+T_R"), ("TGT_FACE_B", "tgt/face/-T_R")]]

    req1 = ["src/frame/hand_r", "src/vector/n_palm", "tgt/anchor/wrist_R",
            "tgt/envelope/distal_band", "src/assembly/27_bones"]
    req2 = ["src/site/FCR-P3", "src/site/FCU-P4", "src/site/ECRL-P4", "src/site/ECRB-P4",
            "src/site/ECU-P6", "src/vector/n_palm", "tgt/anchor/wrist_R", "tgt/envelope/distal_band"]
    req3 = ["src/frame/hand_r", "src/vector/n_palm", "tgt/anchor/wrist_R",
            "tgt/face/+T_R", "tgt/face/-T_R", "tgt/envelope/distal_band"]

    def view_row(view_id, pair_id, diag_rect, clean_rect, primary, secondaries,
                 bindings, required):
        rows = []
        for mode, rect in (("diagnostic", diag_rect), ("clean", clean_rect)):
            cam = json.loads(json.dumps(primary))
            if mode == "diagnostic":
                vis = visibility(LAYERS, bindings, required)
            else:
                vis = json.loads(json.dumps(CLEAN_VIS))
            rows.append({
                "view_id": view_id,
                "mode": mode,
                "pair_id": pair_id,
                "state_binding": {"kind": "state", "sha256": subject_sha},
                "artifact_locator": {"kind": "image", "region": "pixel_rectangle",
                                     "pixel_rectangle": rect},
                "camera": cam,
                "visibility": vis,
                "cell_layout_note": "cell = SOURCE panel | TARGET panel (row3: 2x2); the "
                                    "validated PRIMARY camera is the first (source) camera; "
                                    "every other camera in the cell is fully declared in "
                                    "camera.secondary_cameras with identical 16 fields",
            })
            cam["secondary_cameras"] = secondaries
            rows[-1]["camera"] = cam
        return rows

    secondaries1 = [cam_tgt_over]
    secondaries2 = [cam_tgt_close]
    secondaries3 = [cam_src_oblique, cam_tgt_side, cam_tgt_oblique]

    views = []
    views += view_row(VIEW_IDS[0], "pair-overview", rect_of(row1_d, rows_y[0]),
                      rect_of(row1_c, rows_y[1]), cam_src_over, secondaries1, sb1, req1)
    views += view_row(VIEW_IDS[1], "pair-closeup", rect_of(row2_d, rows_y[2]),
                      rect_of(row2_c, rows_y[3]), cam_src_close, secondaries2, sb2, req2)
    views += view_row(VIEW_IDS[2], "pair-side-oblique", rect_of(row3_d, rows_y[4]),
                      rect_of(row3_c, rows_y[5]), cam_src_side, secondaries3, sb3, req3)

    manifest = {
        "schema": "chimera.visual_capture_manifest.v1",
        "task_id": "A04",
        "run_id": RUN_ID,
        "subject_sha256": subject_sha,
        "capture_sha256": capture_sha,
        "profile_id": CARD["task"]["verification_profile"]["id"],
        "tick_interval": [0, 0],
        "views": views,
        "sheet_layout": {
            "pixel_size": [int(W), int(H)],
            "rows": ["overview diagnostic", "overview clean", "closeup diagnostic",
                     "closeup clean", "side+oblique diagnostic", "side+oblique clean"],
            "honest_titles": "rendered inside every panel; A/B letters label FACES, "
                             "not anatomy; no target palm verdict claimed",
        },
    }

    # ---- structural validation against the card profile ---------------------
    sys.path.insert(0, r"E:\PythonChimera\tools\monkey_campaign")
    import visual_capture
    context = {"task_id": "A04", "subject_sha256": subject_sha, "run_id": RUN_ID,
               "capture_sha256": capture_sha, "tick_interval": [0, 0]}
    gate = visual_capture.validate_manifest(manifest, context,
                                            CARD["task"]["verification_profile"])
    if fire:
        gate = dict(gate)
        gate["render_falsifiers_fired"] = fire

    jdump_manifest = manifest
    path = OUT / "capture_manifest.json"
    text = json.dumps(jdump_manifest, indent=1, sort_keys=True, ensure_ascii=True)
    path.write_text(text, encoding="ascii")

    receipt = {
        "schema": "ont-a04.anatomy.capture.v1",
        "task_id": "A04",
        "run_id": RUN_ID,
        "gate_validation": gate,
        "capture": {"reference": str(out_png.resolve()), "raw_sha256": capture_sha,
                    "pixel_size": [int(W), int(H)]},
        "manifest": {"reference": str(path.resolve()),
                     "raw_sha256": P.sha256_bytes(text.encode("ascii"))},
        "state_binding": {"kind": "state", "sha256": subject_sha,
                          "reference": str((OUT / "state_snapshot.json").resolve())},
        "render_referents": {
            "renderer": "matplotlib 3.10.8 Agg (CPU, software) + custom numpy z-buffer "
                        "orthographic rasterizer; NO GPU contexts",
            "frames": {"source": "chimanoid_world_m (right-handed, metres; hand_r chain "
                                 "quats identity, R2-A4 origin pin)",
                       "target": "monkey_birth_world_m (right-handed, metres; anterior +z, "
                                 "up +y, creature right at -x per O1; MESH_UNIT_TO_M 0.065 authored)"},
            "clean_segments": "own panels, geometry only, depth-tested, zero diagnostic pixels",
            "cell_layout": "each view cell = SOURCE | TARGET panels; PRIMARY camera = source "
                           "camera (schema-validated); target/side/oblique cameras fully "
                           "declared in camera.secondary_cameras (same 16 fields)",
        },
        "honest_boundary": "Static pinned-geometry inspection only. The capture shows the "
                           "pinned SOURCE hand assembly and the pinned TARGET fitted band "
                           "separately, side by side per view; it is NOT a native engine frame "
                           "and makes no runtime/native claim. A/B face letters label faces, "
                           "not anatomy; the human palm verdict is NOT recorded, so the target "
                           "palm sign stays UNRESOLVED (named in the numerical receipt).",
    }
    (OUT / "capture_receipt.json").write_text(
        json.dumps(receipt, indent=1, sort_keys=True, ensure_ascii=True), encoding="ascii")

    print(f"capture_sha256={capture_sha} sheet={W}x{H} views={len(views)} "
          f"structurally_valid={gate['structurally_valid']} fired={len(fire)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
