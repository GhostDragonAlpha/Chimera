"""HAND_TARGET_VIEWS — R1 target-view render script (M-handtgt).  AMENDED v2.

Fulfills audits/HAND_EVIDENCE_REQUEST/HAND_EVIDENCE_REQUEST.md §R1: opposed
ORTHOGRAPHIC renders of the hash-pinned birth mesh's right-hand distal band with
declared camera extrinsics, for HUMAN palm/dorsum labeling; left hand rendered as
a mirrored CONSISTENCY CHECK. All camera/light/annotation parameters are FROZEN
CONSTANTS in this file (prereg: PREREG.md + PREREG_AMENDMENT_1.md, frozen before
the official renders).

GAMING-SAFETY (verbatim law): "During gaming, use existing images or a verified
CPU-only rendering path. Otherwise queue the render through the GPU broker."
THIS SCRIPT IS THE VERIFIED CPU-ONLY PATH: matplotlib with Agg set BEFORE pyplot
import (O1/O2 precedent) + a custom numpy z-buffer triangle rasterizer.
NO GPU/OpenGL/Vulkan/WebGL/CUDA context is created anywhere.

Orthographic projection is COMPUTED FROM THE MESH TRIANGLES (declared): camera
basis from the declared extrinsics, screen coordinates by dot products,
per-pixel z-buffer, Lambert shading with a declared camera-frame light, 2x
supersampling box-downsampled.

CAMERA DELIVERABLES (PREREG_AMENDMENT_1):
  PRIMARY pair (letters A/B, the human question): opposed along the MEASURED
    broad-face normal +/-T_R (T_R = fixed +x-rejection rule, asserted to O2's
    recorded value). Measured geometry (geometry_probe receipt): band sections
    are ~46-50 mm along n_t and ~6-16 mm along T_R, far-end PCA major axis
    47.1 mm lies ALONG n_t (dot -0.9989) -> the R1.4 ±n_t default views the lens
    edge-on (band span 567.0 px < the R1.5-3 600 px bar). The ±T cameras
    photograph each broad face face-on (R1.3-A's stated design intent).
  RECORD pair (no letters): the literal R1.4 ±n_t cameras, kept as the frozen
    execution record; its 567.0 px band span is recorded against the bar (FAILS
    it; recorded, not tuned away).
  LEFT-hand mirror check: letters assigned by the declared MIRROR RELATION
    (+T_L = -M.T_R, O2's anti-mirror), so the same letter should be named on
    both sides; a rendered-pixel mirror difference is recorded (mesh x-mirror is
    88-91 % exact, so the check is visual).

Identity pins (R1.4) are asserted before rendering; the pinned mesh is read
verbatim (NO repair/resampling). Reproducibility: two unmodified runs must
produce byte-identical outputs. Falsifiers: (a) not reproducible; (b) crop
missing the distal band (asserted); (c) any GPU usage (none).
"""
from __future__ import annotations

import json
import sys

sys.dont_write_bytecode = True
from pathlib import Path

import numpy as np

import matplotlib

matplotlib.use("Agg")  # gaming-safety: software renderer, BEFORE pyplot import
import matplotlib.patheffects as pe  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

HERE = Path(__file__).resolve().parent.parent  # audits/HAND_TARGET_VIEWS
BASE = Path(r"E:\PythonChimera\forearm_package\baseline_snapshot")
FIGDIR = HERE / "figures"
sys.path.insert(0, str(HERE / "work"))
from mesh_target_htv import MESH_UNIT_TO_M, MonkeyTarget, sha256_of  # noqa: E402

# ---------------- FROZEN CONSTANTS (PREREG §1–§6 + AMENDMENT 1) ----------------
EXPECT_BIRTH_SHA = "550a5b3ec927ea13614ad250963b23e2948e76a238ac110da9889f339aabfa3c"
EXPECT_PACK_SHA = "74b3ab044b7adaed4a0f9349a81f5d3c87441084b2ec8981f4e0afaba50c1662"
EXPECT_LOADER_SHA = "268f139a9e90e561f4a5f8ab02553f0d87f51633f635139e6cec6f5c9cfa19a0"

# R1.4 / O2 §3 RECORDED values (assertion targets; tol = recording precision)
REC_6DP = 6e-6
REC_4DP = 1e-4
RECORDED = {
    "wrist_R": (-0.144995, 0.261482, -0.005956),
    "elbow_R": (-0.1155, 0.3191, -0.0061),
    "a_R": (-0.455844, -0.890058, 0.001857),
    "T_R": (0.890060, -0.455843, 0.000951),
    "n_t": (0.000000, 0.002086, 1.000000),
    "look_at_R": (-0.182830, 0.187607, -0.005802),
    "wrist_L": (0.144995, 0.261482, -0.005956),
    "elbow_L": (0.1155, 0.3191, -0.0061),
    "T_L": (0.890060, 0.455843, -0.000951),
    "n_tL": (-0.000001, 0.002086, 1.000000),
    "look_at_L": (0.182830, 0.187607, -0.005802),  # exact x-mirror of look_at_R
}

AXIAL_STATION_M = 0.083      # look_at = wrist + 0.083*a   (R1.4 default)
EYE_DIST_M = 0.30            # eye = look_at +/- 0.30*(normal)  (R1.4 default)
HALF_WIDTH_M = 0.040         # ortho half-width              (R1.4 default)
IMG_PX = 2048                # output pixels per side        (R1.4 default)
SS = 2                       # supersample factor (render SS*IMG_PX, box-downsample)
MARGIN_M = 0.005             # triangle pre-filter box expansion (rendering cost only)
DEPTH_WIN = (0.24, 0.36)     # BAND DEPTH SLAB about the eye along f (m) - AMENDMENT-1
                             # §A2.7: the render is of the band region ("rasterize the
                             # band's silhouette"); measured band depth [260,333] mm in
                             # every view; body occluders <= ~150 mm and far body >= ~520
                             # mm excluded. Declared in every sidecar.
LIGHT_CAM = (0.25, 0.30, -1.0)  # direction TO LIGHT in camera frame (right,up,fwd)
AMBIENT, DIFFUSE = 0.25, 0.75
ALBEDO, BG = 0.62, 0.94
TICKS_MM = [0, 48, 55, 80, 111]   # R1.3-B stations
BAND_MM = (55.0, 111.4)           # the distal band (B1/C2 receipts)
FACE_MM = (80.0, 111.4)           # far-end face population (B1's 47.1 mm extent)
REGION_CAP_M = 0.042              # B1 r-cap: crop CHECK only, never a mesh edit
VISIBILITY_MIN_PX = 600           # R1.5-3 visibility bar (PRIMARY pair only)
MESH_UNIT_TO_M_ASSERT = 0.065
INVOCATION = "PYTHONDONTWRITEBYTECODE=1 python scripts/render_hand_views.py"
RENDERER = (
    "matplotlib 3.10.8 Agg (CPU, software) + custom numpy z-buffer orthographic "
    "rasterizer, supersample 2x; NO GPU contexts"
)
CHANNEL = "M-handtgt / HAND_TARGET_VIEWS"
MIRROR = np.array([-1.0, 1.0, 1.0])  # L/R mirror operator M (world x flip)

PFX = FIGDIR / "hand_target_R_view1_plusT"
OUT = {
    "R_primary": [
        (FIGDIR / "hand_target_R_view1_plusT.png", FIGDIR / "hand_target_R_view1_plusT.json"),
        (FIGDIR / "hand_target_R_view2_minusT.png", FIGDIR / "hand_target_R_view2_minusT.json"),
    ],
    "R_record": [
        (FIGDIR / "hand_target_R_view1_literal_nt_record.png",
         FIGDIR / "hand_target_R_view1_literal_nt_record.json"),
        (FIGDIR / "hand_target_R_view2_literal_nt_record.png",
         FIGDIR / "hand_target_R_view2_literal_nt_record.json"),
    ],
    "L_check": (FIGDIR / "hand_target_L_mirror_check.png",
                FIGDIR / "hand_target_L_mirror_check.json"),
}

PPM = IMG_PX / (2.0 * HALF_WIDTH_M)  # 25600 px per metre -> 25.6 px/mm


def unit(v):
    v = np.asarray(v, dtype=np.float64)
    return v / np.linalg.norm(v)


def assert_close(name, got, want, tol):
    got = np.asarray(got, dtype=np.float64)
    want = np.asarray(want, dtype=np.float64)
    d = float(np.abs(got - want).max())
    ok = d <= tol
    print(f"  assert {name:10s} got={np.round(got, 6).tolist()} want={np.round(want, 6).tolist()} "
          f"maxdiff={d:.2e} tol={tol:.0e} -> {'OK' if ok else 'FAIL'}")
    if not ok:
        raise AssertionError(f"identity/derivation assertion failed: {name} (maxdiff {d:.3e} > {tol:.0e})")
    return got


def camera_basis(eye, look_at, up):
    z_cam = unit(np.asarray(eye) - np.asarray(look_at))  # backward
    x_cam = unit(np.cross(up, z_cam))
    y_cam = np.cross(z_cam, x_cam)
    return x_cam, y_cam, -z_cam


def fixed_T(a):
    """C3's fixed rule: +T = rejection of global +x on the plane orthogonal to a."""
    x = np.array([1.0, 0.0, 0.0])
    e1 = x - a * (a @ x)
    if np.linalg.norm(e1) < 1e-9:
        x = np.array([0.0, 0.0, 1.0])
        e1 = x - a * (a @ x)
    return unit(e1)


def render_raster(V, F, eye, look_at, up):
    """Orthographic z-buffer raster of the pinned mesh (CPU, numpy only).

    Returns (img_u8, zmin, mask, n_tri, (dmin, dmax)). Deterministic.
    """
    eye = np.asarray(eye, dtype=np.float64)
    x_cam, y_cam, f = camera_basis(eye, look_at, up)
    L_cam = np.asarray(LIGHT_CAM, dtype=np.float64)
    L_world = unit(L_cam[0] * x_cam + L_cam[1] * y_cam + L_cam[2] * f)

    rel = V - eye
    u = rel @ x_cam
    v = rel @ y_cam
    d = rel @ f
    W = IMG_PX * SS
    scale = W / (2.0 * HALF_WIDTH_M)
    U = (u + HALF_WIDTH_M) * scale
    Vp = (HALF_WIDTH_M - v) * scale

    inb = (
        (u > -HALF_WIDTH_M - MARGIN_M) & (u < HALF_WIDTH_M + MARGIN_M)
        & (v > -HALF_WIDTH_M - MARGIN_M) & (v < HALF_WIDTH_M + MARGIN_M)
        & (d > DEPTH_WIN[0]) & (d < DEPTH_WIN[1])
    )
    tri_ids = np.where(inb[F].any(axis=1))[0]
    n_world = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])

    zbuf = np.full((W, W), np.inf, dtype=np.float64)
    img = np.full((W, W), BG, dtype=np.float64)

    for ti in tri_ids:
        i0, i1, i2 = F[ti]
        zs = np.array([d[i0], d[i1], d[i2]])
        if zs.max() < DEPTH_WIN[0] or zs.min() > DEPTH_WIN[1]:
            continue
        xs = np.array([U[i0], U[i1], U[i2]])
        ys = np.array([Vp[i0], Vp[i1], Vp[i2]])
        area = (xs[1] - xs[0]) * (ys[2] - ys[0]) - (xs[2] - xs[0]) * (ys[1] - ys[0])
        if area == 0.0:
            continue
        nrm = n_world[ti]
        nn = np.linalg.norm(nrm)
        if nn == 0.0:
            continue
        nrm = nrm / nn
        if nrm @ f > 0.0:  # two-sided: normal of the camera-facing side
            nrm = -nrm
        inten = ALBEDO * (AMBIENT + DIFFUSE * max(0.0, float(nrm @ L_world)))
        x0 = max(0, int(np.floor(xs.min())))
        x1 = min(W - 1, int(np.ceil(xs.max())))
        y0 = max(0, int(np.floor(ys.min())))
        y1 = min(W - 1, int(np.ceil(ys.max())))
        if x1 < x0 or y1 < y0:
            continue
        gx, gy = np.meshgrid(
            np.arange(x0, x1 + 1, dtype=np.float64) + 0.5,
            np.arange(y0, y1 + 1, dtype=np.float64) + 0.5,
        )
        e0 = (xs[1] - xs[0]) * (gy - ys[0]) - (ys[1] - ys[0]) * (gx - xs[0])
        e1 = (xs[2] - xs[1]) * (gy - ys[1]) - (ys[2] - ys[1]) * (gx - xs[1])
        e2 = (xs[0] - xs[2]) * (gy - ys[2]) - (ys[0] - ys[2]) * (gx - xs[2])
        inside = ((e0 >= 0) & (e1 >= 0) & (e2 >= 0)) | ((e0 <= 0) & (e1 <= 0) & (e2 <= 0))
        if not inside.any():
            continue
        areai = 1.0 / area
        depth = (e1 * areai) * zs[0] + (e2 * areai) * zs[1] + (e0 * areai) * zs[2]
        zb = zbuf[y0:y1 + 1, x0:x1 + 1]
        upd = inside & (depth < zb)
        if not upd.any():
            continue
        zb[upd] = depth[upd]
        img[y0:y1 + 1, x0:x1 + 1][upd] = inten

    img_f = img.reshape(IMG_PX, SS, IMG_PX, SS).mean(axis=(1, 3))
    zmin = zbuf.reshape(IMG_PX, SS, IMG_PX, SS).min(axis=(1, 3))
    mask = zmin < np.inf
    img_u8 = np.clip(np.rint(img_f * 255.0), 0, 255).astype(np.uint8)

    vis = zmin[mask]
    if vis.size:
        dmin, dmax = float(vis.min()), float(vis.max())
    else:
        dmin = dmax = float("nan")
    return img_u8, zmin, mask, int(len(tri_ids)), (dmin, dmax)


def px_of(uv):
    """screen (u,v) metres -> pixel (x, y) on the final grid."""
    u, v = uv
    return (u + HALF_WIDTH_M) * PPM, (HALF_WIDTH_M - v) * PPM


def silhouette_max_run(mask, row_lo, row_hi):
    best = 0
    for r in range(max(0, row_lo), min(mask.shape[0], row_hi)):
        idx = np.flatnonzero(mask[r])
        if idx.size == 0:
            continue
        if idx.size == 1:
            best = max(best, 1)
            continue
        splits = np.where(np.diff(idx) > 1)[0]
        starts = np.concatenate(([0], splits + 1))
        ends = np.concatenate((splits, [idx.size - 1]))
        best = max(best, int((idx[ends] - idx[starts] + 1).max()))
    return best


def spans_about(eye, x_cam, y_cam, P):
    rel = P - np.asarray(eye, dtype=np.float64)
    return (rel @ x_cam), (rel @ y_cam)


def crop_check(V, wrist, a, look_at, eye, x_cam, y_cam, label):
    """AMENDMENT-1 §4: project about the EYE (debug-run bug fixed). Asserts the
    distal band lies inside the frozen frame (falsifier b)."""
    rel = V - wrist
    t = rel @ a
    perp = rel - np.outer(t, a)
    r = np.linalg.norm(perp, axis=1)
    band = (t >= BAND_MM[0] / 1000.0) & (t <= BAND_MM[1] / 1000.0) & (r <= REGION_CAP_M)
    face = (t >= FACE_MM[0] / 1000.0) & (t <= BAND_MM[1] / 1000.0) & (r <= REGION_CAP_M)
    assert band.sum() > 300 and face.sum() > 100, "band/face selection unexpectedly small"
    ub, vb = spans_about(eye, x_cam, y_cam, V[band])
    uf, vf = spans_about(eye, x_cam, y_cam, V[face])
    worst = max(abs(ub.min()), abs(ub.max()), abs(vb.min()), abs(vb.max()))
    print(f"  [{label}] band n={int(band.sum())}: u [{ub.min()*1000:+.2f},{ub.max()*1000:+.2f}] mm, "
          f"v [{vb.min()*1000:+.2f},{vb.max()*1000:+.2f}] mm (frame +/-40) -> worst {worst*1000:.2f} mm")
    assert worst <= HALF_WIDTH_M, f"FALSIFIER (b): distal-band vertex outside the frozen frame ({label})"
    for edge in (BAND_MM[0] / 1000.0 - AXIAL_STATION_M, BAND_MM[1] / 1000.0 - AXIAL_STATION_M):
        assert abs(edge) <= HALF_WIDTH_M - 0.003, f"FALSIFIER (b): band edge not >=3mm inside frame ({label})"
    band_span_px = (ub.max() - ub.min()) * PPM
    face_span_px = (uf.max() - uf.min()) * PPM
    print(f"  [{label}] whole-band u-span {band_span_px:.1f} px; far-end face u-span "
          f"{face_span_px:.1f} px (bar >= {VISIBILITY_MIN_PX})")
    return dict(
        band_n=int(band.sum()), face_n=int(face.sum()),
        band_u_span_mm=[float(ub.min() * 1000), float(ub.max() * 1000)],
        band_v_span_mm=[float(vb.min() * 1000), float(vb.max() * 1000)],
        band_u_span_px=float(band_span_px),
        face_u_span_px=float(face_span_px),
        face_v_span_mm=[float(vf.min() * 1000), float(vf.max() * 1000)],
    )


def annotate_view(ax, img_u8, zmin, meta):
    """Machine-drawn annotations (PREREG §5 + AMENDMENT-1): title strip with the
    camera declaration, scale bar, axis triad, axial ruler with frame-edge wrist
    annotation, face letter (primary only), guidance strip, depth-relief inset."""
    W = IMG_PX
    eye, look_at = meta["eye"], meta["look_at"]
    x_cam, y_cam, f = camera_basis(eye, look_at, meta["up"])
    ax.set_axis_off()
    ax.imshow(img_u8, extent=(0, W, W, 0), cmap="gray", vmin=0, vmax=255,
              interpolation="none", zorder=0)
    ax.set_xlim(0, W)
    ax.set_ylim(W, 0)
    txt = dict(fontfamily="DejaVu Sans", zorder=9)

    # title strip: camera declaration (R1.3-B)
    ax.add_patch(Rectangle((0, 0), W, 250, fc="white", ec="k", lw=1.0, alpha=0.90, zorder=8))
    lines = [
        (meta["title"], 16 if meta["mode"] == "primary" else 15, "bold"),
        (f"eye = ({eye[0]:+.6f}, {eye[1]:+.6f}, {eye[2]:+.6f}) m", 12, "normal"),
        (f"look_at = ({look_at[0]:+.6f}, {look_at[1]:+.6f}, {look_at[2]:+.6f}) m    "
         f"mesh_unit_to_m = 0.065 (authored)", 12, "normal"),
        (f"view dir = ({f[0]:+.6f}, {f[1]:+.6f}, {f[2]:+.6f})    up = "
         f"({meta['up'][0]:+.6f}, {meta['up'][1]:+.6f}, {meta['up'][2]:+.6f})", 12, "normal"),
        (f"right = ({x_cam[0]:+.6f}, {x_cam[1]:+.6f}, {x_cam[2]:+.6f})    projection = "
         f"ORTHOGRAPHIC half-width 0.040 m, 2048x2048 px (SS 2)", 11, "normal"),
        ("light (camera frame) = unit(0.25, 0.30, -1.0), I = 0.25+0.75*max(0, n.L)    "
         "depth slab 0.24-0.36 m about the band (declared, AMENDMENT-1 §A2.7)", 10, "normal"),
        (f"mesh sha256 {EXPECT_BIRTH_SHA[:16]}...  loader sha256 {EXPECT_LOADER_SHA[:16]}...  "
         f"scripts/render_hand_views.py  {CHANNEL}", 10, "normal"),
    ]
    y = 30
    for s, fs, wgt in lines:
        ax.text(24, y, s, fontsize=fs, fontweight=wgt, ha="left", va="top", **txt)
        y += {17: 44, 16: 42, 15: 40, 12: 34, 11: 32, 10: 30}[fs]

    # scale bar: 10.00 mm = 256 px exactly (above the guidance strip)
    sb_x0, sb_x1, sb_y = 60, 60 + 10.0 / 1000.0 * PPM, 1810
    ax.plot([sb_x0, sb_x1], [sb_y, sb_y], "k-", lw=3, zorder=10)
    for x in (sb_x0, sb_x1):
        ax.plot([x, x], [sb_y - 10, sb_y + 10], "k-", lw=2, zorder=10)
    ax.text(sb_x0, sb_y + 16, "10 mm (orthographic)", fontsize=11, ha="left", va="top", **txt)

    # axis triad: world +x/+y/+z projected
    ox, oy = 1810, 640
    ax.add_patch(Rectangle((ox - 160, oy - 175), 330, 350, fc="white", ec="k",
                           lw=0.8, alpha=0.75, zorder=8))
    for vec, name in (((1, 0, 0), "+x"), ((0, 1, 0), "+y"), ((0, 0, 1), "+z")):
        e = np.asarray(vec, dtype=np.float64)
        du, dv = float(e @ x_cam), float(e @ y_cam)
        d_f = float(e @ f)
        dx, dy = du * 150.0, -dv * 150.0
        if np.hypot(dx, dy) < 20.0:
            sym, words = ("\u2299", "toward camera") if d_f < 0 else ("\u2297", "away from camera")
            ax.text(ox, oy, sym, fontsize=22, ha="center", va="center", **txt)
            ax.text(ox, oy + 30, f"world {name}: {words}", fontsize=10, ha="center", va="top", **txt)
        else:
            ax.annotate("", xy=(ox + dx, oy + dy), xytext=(ox, oy),
                        arrowprops=dict(arrowstyle="-|>", color="k", lw=2.0), zorder=9)
            ax.text(ox + dx * 1.10, oy + dy * 1.10, f"world {name}", fontsize=11,
                    ha="center", va="center", **txt)
    ax.text(ox - 150, oy - 165, "world axis triad (birth frame: +z anterior, +y up, -x right)",
            fontsize=9, ha="left", va="top", **txt)

    # axial ruler along the projected axis line (u = 0 by construction)
    cx = px_of((0.0, 0.0))[0]
    t_top, t_bot = BAND_MM[1] / 1000.0, BAND_MM[0] / 1000.0
    y_top = px_of((0.0, t_top - AXIAL_STATION_M))[1]
    y_bot = px_of((0.0, t_bot - AXIAL_STATION_M))[1]
    ax.plot([cx, cx], [y_top, y_bot], color="k", lw=1.2, ls="--", zorder=9)
    for tmm in TICKS_MM:
        v = tmm / 1000.0 - AXIAL_STATION_M
        if abs(v) <= HALF_WIDTH_M - 0.003:
            ty = px_of((0.0, v))[1]
            band_edge = tmm in (55, 111)
            ax.plot([cx - (16 if band_edge else 10), cx + (16 if band_edge else 10)],
                    [ty, ty], "k-", lw=2.5 if band_edge else 1.4, zorder=9)
            if tmm < 55:  # in-frame stations below the band: label above the tick
                ax.text(cx, ty - 8, f"{tmm} mm", fontsize=10.5, ha="center", va="bottom",
                        bbox=dict(fc="white", ec="none", alpha=0.65, pad=1.0), **txt)
            else:
                ax.text(cx + 22, ty, f"{tmm} mm" + ("  (band edge)" if band_edge else ""),
                        fontsize=10.5, fontweight="bold" if band_edge else "normal",
                        ha="left", va="center",
                        bbox=dict(fc="white", ec="none", alpha=0.65, pad=1.0), **txt)
    ax.text(40, 1024, "distal band 55-111.4 mm along a\n(elbow->wrist axis; B1/C2 receipts)",
            fontsize=11, rotation=90, ha="left", va="center",
            bbox=dict(fc="white", ec="none", alpha=0.7, pad=2.0), **txt)
    ax.annotate("", xy=(cx, 1944), xytext=(cx, 1840),
                arrowprops=dict(arrowstyle="-|>", color="k", lw=1.6), zorder=10)
    ax.text(cx + 12, 1842, "0 mm = wrist_R - 83 mm below frame (arrow)",
            fontsize=9.5, ha="left", va="center",
            bbox=dict(fc="white", ec="none", alpha=0.8, pad=1.5), **txt)

    # face letter (PRIMARY pair only; labels FACES, never anatomy)
    if meta.get("letter"):
        lx, ly = 1454, 1024
        ax.text(lx, ly, meta["letter"], fontsize=120, ha="center", va="center",
                color="k", path_effects=[pe.withStroke(linewidth=7, foreground="white")], zorder=10)
        ax.plot([lx - 60, 1035], [ly + 55, 1024], "k-", lw=1.0, zorder=9)
        ax.text(lx, ly + 130, meta["letter_caption"], fontsize=13, ha="center", va="top",
                bbox=dict(fc="white", ec="k", lw=0.8, alpha=0.85, pad=3.0), **txt)

    # depth-relief inset (bottom-right; CONTENT = a 420x420 px crop centred on the
    # band pad: station 68 mm, 20 mm screen-left of the ruler; normalized over its
    # own visible depth range; off-surface = mid-gray 128)
    r0, r1, c0, c1 = 1400, 1820, 1560, 1980
    ccx, ccy = px_of((-0.020, 0.068 - AXIAL_STATION_M))
    cc0, cr0 = int(ccx) - 210, int(ccy) - 210
    crop = zmin[cr0:cr0 + 420, cc0:cc0 + 420]
    chit = crop < np.inf
    cvis = crop[chit]
    if cvis.size:
        lo, hi = float(cvis.min()), float(cvis.max())
        rel_d = np.where(chit, (crop - lo) / max(hi - lo, 1e-12), 0.0)
        inset = np.where(chit, np.clip(np.rint((1.0 - rel_d) * 255.0), 0, 255), 128.0)
        inset = inset.astype(np.uint8)
    else:
        inset = np.full((420, 420), 128, dtype=np.uint8)
    ax.imshow(inset, extent=(c0, c1, r1, r0), cmap="gray", vmin=0, vmax=255,
              interpolation="none", zorder=6)
    ax.add_patch(Rectangle((c0, r0), c1 - c0, r1 - r0, fill=False, ec="k", lw=1.5, zorder=7))
    ax.text(2040, r0 - 10, "depth relief at the band pad (station 68 mm) - lighter = closer",
            fontsize=10.5, ha="right", va="bottom",
            bbox=dict(fc="white", ec="none", alpha=0.8, pad=1.5), **txt)

    # guidance strip (bottom 98 px)
    ax.add_patch(Rectangle((0, 1950), W, W - 1950, fc="white", ec="k", lw=1.0, alpha=0.90, zorder=8))
    if meta["mode"] == "primary":
        ax.text(60, 1958,
                "QUESTION (human terminal): which lettered face is the PALM (ventral) - A or B?",
                fontsize=13.5, fontweight="bold", ha="left", va="top", **txt)
        ax.text(60, 1996,
                "Guidance (O2 diagnostics): one face is flatter/slightly cupped; the other carries the "
                "outward lens bulge - which is the palm/volar?",
                fontsize=11, ha="left", va="top", **txt)
    else:
        ax.text(60, 1958,
                "RECORD ONLY - literal R1.4 camera (+/-n_t), executed as frozen.",
                fontsize=13.5, fontweight="bold", ha="left", va="top", **txt)
        ax.text(60, 1996,
                "Measured: the 47.1 mm broad-face extent lies ALONG n_t -> near edge-on (band span "
                "567 px < 600 px bar). See PREREG_AMENDMENT_1.",
                fontsize=11, ha="left", va="top", **txt)


def save_figure(path, panels):
    n = len(panels)
    fig = plt.figure(figsize=(10.24, 10.24 * n), dpi=200)
    for k, (img_u8, zmin, meta) in enumerate(panels):
        ax = fig.add_axes([0, 1.0 - (k + 1) / n, 1.0, 1.0 / n])
        annotate_view(ax, img_u8, zmin, meta)
    fig.savefig(path, dpi=200, facecolor="white")
    plt.close(fig)
    print("wrote", path)


def make_sidecar(path, image_size_px, views, measurements, check=False):
    rec = {
        "artifact": path.name,
        "request": "HAND_EVIDENCE_REQUEST §R1.3 (A images, B annotations, C sidecar)",
        "consistency_check_only": check,
        "views": views,
        "image_size_px": list(image_size_px),
        "mesh_sha256": EXPECT_BIRTH_SHA,
        "joints_sha256": EXPECT_PACK_SHA,
        "loader_sha256": EXPECT_LOADER_SHA,
        "loader_copy": "work/mesh_target_htv.py (byte-identical to baseline_snapshot/code/mesh_target.py)",
        "mesh_unit_to_m": MESH_UNIT_TO_M_ASSERT,
        "renderer": RENDERER,
        "channel": CHANNEL,
        "invocation": INVOCATION,
        "mesh_repair": "none - the rendered surface derives from the pinned file verbatim",
        "face_letters": {
            "A": "the broad face on the +T_R side (primary pair)",
            "B": "the broad face on the -T_R side (primary pair)",
            "note": "check-figure letters are assigned by the declared MIRROR RELATION "
                    "(PREREG_AMENDMENT_1 §A2.5); record-pair views carry no letters",
        },
        "ticks_mm": TICKS_MM,
        "band_mm": list(BAND_MM),
        "prereg": ["PREREG.md", "PREREG_AMENDMENT_1.md"],
        "measurements": measurements,
        "reproducibility": {
            "protocol": "two unmodified runs; every output file must hash byte-identical",
            "declared_nondeterminism": "none",
        },
    }
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(rec, fh, indent=1, sort_keys=True, ensure_ascii=False)
    print("wrote", path)


def main() -> int:
    print("== HAND_TARGET_VIEWS render (M-handtgt) — CPU-only (Agg) — AMENDED v2 ==")
    print("renderer:", RENDERER)
    loader_sha = sha256_of(str(HERE / "work" / "mesh_target_htv.py"))
    assert loader_sha.lower() == EXPECT_LOADER_SHA, "loader copy is not the pinned baseline module"
    print(f"loader copy sha256 OK ({EXPECT_LOADER_SHA[:16]}...)")
    mt = MonkeyTarget(birth_path=str(BASE / "inputs" / "monkey_birth.bin"),
                      pack_path=str(BASE / "inputs" / "monkey_joints.bin"))
    assert mt.birth_sha.lower() == EXPECT_BIRTH_SHA, f"mesh sha {mt.birth_sha} != pin"
    assert mt.pack_sha.lower() == EXPECT_PACK_SHA, f"pack sha {mt.pack_sha} != pin"
    assert MESH_UNIT_TO_M == MESH_UNIT_TO_M_ASSERT, "unit convention changed"
    print(f"mesh sha256 OK ({EXPECT_BIRTH_SHA[:16]}...; {mt.input_bytes['birth']} B)  "
          f"pack sha256 OK ({EXPECT_PACK_SHA[:16]}...; {mt.input_bytes['pack']} B)")
    print(f"mesh verts {len(mt.V)} tris {len(mt.F)}")

    print("right hand derivations vs R1.4 recorded values:")
    wrist = assert_close("wrist_R", mt.joint_pos("wrist_R"), RECORDED["wrist_R"], REC_6DP)
    elbow = assert_close("elbow_R", mt.joint_pos("elbow_R"), RECORDED["elbow_R"], REC_4DP)
    a = assert_close("a_R", unit(wrist - elbow), RECORDED["a_R"], REC_6DP)
    T = assert_close("T_R", fixed_T(a), RECORDED["T_R"], REC_6DP)
    n_t = assert_close("n_t", unit(np.cross(a, T)), RECORDED["n_t"], REC_6DP)
    look_at = assert_close("look_at", wrist + AXIAL_STATION_M * a, RECORDED["look_at_R"], REC_6DP)

    meas_common = {"side": "R",
                   "assertions": "all R1.4 derivations OK (see run log)",
                   "look_at_full_precision": [float(x) for x in look_at]}

    # ---------------- PRIMARY pair (+/-T_R, face-on broad faces) ----------------
    print("PRIMARY pair (+/-T_R cameras; AMENDMENT-1):")
    xP, yP, _ = camera_basis(look_at + EYE_DIST_M * T, look_at, a)
    meas_primary = dict(meas_common)
    meas_primary["crop_check_view1"] = crop_check(mt.V, wrist, a, look_at,
                                                  look_at + EYE_DIST_M * T, xP, yP, "primary v1")
    meas_primary["crop_check_view2"] = crop_check(mt.V, wrist, a, look_at,
                                                  look_at - EYE_DIST_M * T, *camera_basis(
                                                      look_at - EYE_DIST_M * T, look_at, a)[:2],
                                                  "primary v2")

    primary_imgs = {}
    views = {}
    for k, (sgn, letter) in enumerate(((+1.0, "A"), (-1.0, "B"))):
        eye = look_at + sgn * EYE_DIST_M * T
        x_cam, y_cam, f = camera_basis(eye, look_at, a)
        img_u8, zmin, mask, ntri, (dmin, dmax) = render_raster(mt.V, mt.F, eye, look_at, a)
        row_lo = int(px_of((0.0, BAND_MM[1] / 1000.0 - AXIAL_STATION_M))[1])
        row_hi = int(px_of((0.0, BAND_MM[0] / 1000.0 - AXIAL_STATION_M))[1]) + 1
        run_px = silhouette_max_run(mask, row_lo, row_hi)
        side_name = ("+T_R-side view" if sgn > 0 else "-T_R-side view")
        cap = (f"face {letter} - the broad face toward this camera ({side_name})")
        print(f"  primary view {k+1} ({side_name}): eye={np.round(eye, 6).tolist()} tris {ntri} "
              f"silhouette max run in band rows {run_px} px  depth [{dmin*1000:.1f},{dmax*1000:.1f}] mm")
        assert run_px >= VISIBILITY_MIN_PX, f"FALSIFIER: face span {run_px} px < {VISIBILITY_MIN_PX}"
        meta = dict(title=f"VIEW {k+1} - {side_name} (right hand, birth pose) - "
                          f"FACE {letter} toward camera",
                    eye=eye, look_at=look_at, up=a, side_name=side_name, letter=letter,
                    letter_caption=cap, mode="primary")
        primary_imgs[k] = img_u8
        views[f"view{k+1}"] = {
            "pair": "PRIMARY (AMENDMENT-1; measured broad-face normal +/-T_R)",
            "side_name": side_name, "face_letter": letter,
            "eye_m": [float(x) for x in eye], "look_at_m": [float(x) for x in look_at],
            "up": [float(x) for x in a], "view_direction": [float(x) for x in f],
            "right": [float(x) for x in x_cam],
            "projection": "orthographic", "ortho_half_width_m": HALF_WIDTH_M,
            "depth_slab_m_along_f": [0.24, 0.36],  # AMENDMENT-1 §A2.7 band depth slab
            "light_camera_frame_to_light": list(LIGHT_CAM),
            "shading": "I = 0.25 + 0.75*max(0, n_vis.L); albedo 0.62; bg 0.94",
            "n_triangles_rasterized": ntri,
            "silhouette_max_run_band_rows_px": run_px,
            "face_span_bar_ge_600px": bool(run_px >= VISIBILITY_MIN_PX),
        }
        meas_primary[f"view{k+1}"] = {
            "silhouette_max_run_band_rows_px": run_px,
            "visible_depth_range_mm": [dmin * 1000, dmax * 1000],
            "face_span_bar_ge_600px": bool(run_px >= VISIBILITY_MIN_PX),
        }
        png, js = OUT["R_primary"][k]
        save_figure(png, [(img_u8, zmin, meta)])
        make_sidecar(js, [IMG_PX, IMG_PX], {f"view{k+1}": views[f"view{k+1}"]}, meas_primary)

    # ---------------- RECORD pair (literal R1.4 +/-n_t cameras) ----------------
    print("RECORD pair (literal R1.4 +/-n_t cameras; no letters):")
    meas_record = dict(meas_common,
                       literal_camera_note="band u-span 567.0 px < 600 px bar (AMENDMENT-1 §A1)")
    for k, sgn in enumerate((+1.0, -1.0)):
        eye = look_at + sgn * EYE_DIST_M * n_t
        x_cam, y_cam, f = camera_basis(eye, look_at, a)
        cc = crop_check(mt.V, wrist, a, look_at, eye, x_cam, y_cam,
                        f"record v{k+1}")
        meas_record[f"crop_check_view{k+1}"] = cc
        img_u8, zmin, mask, ntri, (dmin, dmax) = render_raster(mt.V, mt.F, eye, look_at, a)
        row_lo = int(px_of((0.0, BAND_MM[1] / 1000.0 - AXIAL_STATION_M))[1])
        row_hi = int(px_of((0.0, BAND_MM[0] / 1000.0 - AXIAL_STATION_M))[1]) + 1
        run_px = silhouette_max_run(mask, row_lo, row_hi)
        side_name = ("+n_t-side view" if sgn > 0 else "-n_t-side view")
        print(f"  record view {k+1} ({side_name}): tris {ntri} band-row silhouette run {run_px} px")
        meta = dict(title=f"RECORD - literal R1.4 VIEW {k+1}: {side_name} (right hand) - "
                          f"no face letter",
                    eye=eye, look_at=look_at, up=a, side_name=side_name, letter=None,
                    letter_caption="", mode="record")
        vrec = {
            "pair": "RECORD (literal R1.4 default camera +/-n_t; no question letters)",
            "side_name": side_name,
            "eye_m": [float(x) for x in eye], "look_at_m": [float(x) for x in look_at],
            "up": [float(x) for x in a], "view_direction": [float(x) for x in f],
            "right": [float(x) for x in x_cam],
            "projection": "orthographic", "ortho_half_width_m": HALF_WIDTH_M,
            "depth_slab_m_along_f": [0.24, 0.36],  # AMENDMENT-1 §A2.7 band depth slab
            "light_camera_frame_to_light": list(LIGHT_CAM),
            "shading": "I = 0.25 + 0.75*max(0, n_vis.L); albedo 0.62; bg 0.94",
            "n_triangles_rasterized": ntri,
            "silhouette_max_run_band_rows_px": run_px,
            "note": "the 47.1 mm broad-face extent lies ALONG this view direction "
                    "(measured); kept as the frozen-prereg execution record",
        }
        png, js = OUT["R_record"][k]
        save_figure(png, [(img_u8, zmin, meta)])
        make_sidecar(js, [IMG_PX, IMG_PX], {f"record_view{k+1}": vrec}, meas_record)

    # ---------------- LEFT-hand mirror consistency check ----------------
    print("left hand (mirror consistency check) derivations:")
    wristL = assert_close("wrist_L", mt.joint_pos("wrist_L"), RECORDED["wrist_L"], REC_6DP)
    elbowL = assert_close("elbow_L", mt.joint_pos("elbow_L"), RECORDED["elbow_L"], REC_4DP)
    aL = assert_close("a_L", unit(wristL - elbowL),
                      (-RECORDED["a_R"][0],) + RECORDED["a_R"][1:], REC_6DP)
    TL = assert_close("T_L", fixed_T(aL), RECORDED["T_L"], REC_6DP)
    n_tL = assert_close("n_tL", unit(np.cross(aL, TL)), RECORDED["n_tL"], REC_6DP)
    lookL = assert_close("look_at_L", wristL + AXIAL_STATION_M * aL, RECORDED["look_at_L"], REC_6DP)

    # mirror-relation letters: R face A has outward normal +T_R; M(+T_R) = -T_L,
    # so A_L is the -T_L-side face and B_L the +T_L-side face (AMENDMENT-1 §A2.5).
    panels, viewsL = [], {}
    check_imgs = {}
    for k, (sgn, letter) in enumerate(((-1.0, "A"), (+1.0, "B"))):
        eye = lookL + sgn * EYE_DIST_M * TL
        x_cam, y_cam, f = camera_basis(eye, lookL, aL)
        img_u8, zmin, mask, ntri, (dmin, dmax) = render_raster(mt.V, mt.F, eye, lookL, aL)
        run_px = silhouette_max_run(mask, row_lo, row_hi)
        side_name = ("-T_L-side view (mirrors R's +T_R side)" if sgn < 0
                     else "+T_L-side view (mirrors R's -T_R side)")
        side_short = ("-T_L side (mirror of R's +T_R)" if sgn < 0
                      else "+T_L side (mirror of R's -T_R)")
        meta = dict(title=f"CHECK - LEFT hand mirror - VIEW {k+1}: {side_short} - "
                          f"FACE {letter}",
                    eye=eye, look_at=lookL, up=aL, side_name=side_name, letter=letter,
                    letter_caption=f"face {letter} - mirror counterpart of R's face {letter}",
                    mode="primary")
        panels.append((img_u8, zmin, meta))
        check_imgs[k] = img_u8
        viewsL[f"check_view{k+1}"] = {
            "pair": "CHECK (left hand, letters by MIRROR RELATION; consistency check only)",
            "side_name": side_name, "face_letter": letter,
            "eye_m": [float(x) for x in eye], "look_at_m": [float(x) for x in lookL],
            "up": [float(x) for x in aL], "view_direction": [float(x) for x in f],
            "right": [float(x) for x in x_cam],
            "projection": "orthographic", "ortho_half_width_m": HALF_WIDTH_M,
            "depth_slab_m_along_f": [0.24, 0.36],  # AMENDMENT-1 §A2.7 band depth slab
            "light_camera_frame_to_light": list(LIGHT_CAM),
            "shading": "I = 0.25 + 0.75*max(0, n_vis.L); albedo 0.62; bg 0.94",
            "n_triangles_rasterized": ntri,
            "silhouette_max_run_band_rows_px": run_px,
        }
        print(f"  check view {k+1} ({side_name}): tris {ntri} band-row run {run_px} px")
    save_figure(OUT["L_check"][0], panels)

    # informational pixel-mirror receipt: L check panel 1 vs x-flipped R primary view 1
    diff = np.abs(check_imgs[0].astype(np.int16) - primary_imgs[0][:, ::-1].astype(np.int16))
    meas_check = dict(meas_common,
                      side="L (mirror consistency check only)",
                      pixel_mirror_receipt={
                          "compared": "L check panel 1 raster vs x-flipped R primary view 1 raster",
                          "mean_abs_diff_u8": float(diff.mean()),
                          "max_abs_diff_u8": int(diff.max()),
                          "pct_pixels_diff_gt_8": float((diff > 8).mean() * 100.0),
                          "note": "mesh x-mirror exactness measured at 90.87% verts / 88.11% tris "
                                  "(geometry_probe receipt) - the check is visual, not exact",
                      })
    make_sidecar(OUT["L_check"][1], [IMG_PX, IMG_PX * len(panels)], viewsL, meas_check, check=True)

    print("ALL RENDER + ASSERTION CHECKS PASSED (crop, visibility, identity pins).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
