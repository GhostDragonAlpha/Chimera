"""ONT-A02 visual capture: deterministic CPU raster of the frozen radioulnar views.

Honesty label (also carried in the manifest `render` block, verbatim): geometry is
rasterized by a numpy z-buffer software rasterizer (true per-pixel depth test, fixed
light, no randomness) and composed/labeled with matplotlib Agg on CPU. These are NOT
native engine frames; nothing here claims an application run. The claim subject is
anatomy evidence records (radioulnar definition / before-after radius mapping), which
the anatomy profile serves with component evidence.

Views (PREREGISTRATION.md, frozen before this render ran):
  V1 whole-creature overview   - target pack mesh (monkey_birth.bin), frame triad,
                                 boxed right forearm region, elbow_R/wrist_R, the
                                 elbow->wrist axis, and BOTH radius proximal
                                 anchors (before = elbow_R; after = ulna.P_d).
  V2 local attachment close-up - SOURCE rest frame (mm): vendor ulna.stl at the ulna
                                 body origin and radius.stl at the authored
                                 ulna->radius offset, the kinematic-offset vector,
                                 its axial/lateral/posterior components, frame triad,
                                 and the recorded tendon-path waypoints on both bones.
  V3 orthogonal side and oblique - target forearm region (m), four bookmarks
                                 (anterior, posterior, lateral-oblique, superior):
                                 elbow->wrist axis, before anchor, after anchor, and
                                 the recorded span change.
Each declared view gets a diagnostic + clean pair (identical camera/state per pair).
Diagnostic rows: occlusion 'mixed' (mesh depth-tested, overlay markers/labels/paths
intentionally unoccluded = xray semantics). Clean rows: 'depth_tested', no layers.

Framing is never hand-picked: every camera is computed from the PROJECTED BOUNDS of
its declared subject point set + the single uniform FRAME_MARGIN, guarded by
assert_in_bounds at generation time (the anatomy profile's own "clipped/occluded
subject fails") and by the all-bookmark bounds regression in the test suite.

Rasterizer and camera/quaternion machinery are adapted from the reviewed ONT-A01
contribution (tools/monkey_campaign/contributions/ONT-A01, PR #176) — same
deterministic CPU z-buffer method, re-frozen for this card's subjects.

Writes: evidence/capture_sheet.png, evidence/capture_manifest.json,
evidence/capture_context.json, evidence/visual_provenance.json. Validates the
manifest structurally with the canonical campaign validator before writing.
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
TICKS = (0, 3)

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
RADIUS_COLOR = np.array([0.74, 0.80, 0.86])
SKIN_COLOR = np.array([0.62, 0.58, 0.52])
BEFORE_COLOR = (200, 30, 30)
AFTER_COLOR = (20, 120, 30)
AXIS_COLOR = (30, 30, 30)
FLEXOR_COLOR = (220, 30, 60)
EXTENSOR_COLOR = (30, 60, 220)
COURSE_COLOR = (240, 140, 20)
RADIUS_SITE_COLOR = (150, 40, 200)

# Source-frame anatomical basis constants recomputed by ota02_radioulnar (C1 §2);
# used only for the overlay arrows, values read from the module's measurement.
FRAME_MARGIN = 0.08

# source tendon-path waypoint records (packet site names), visible in V2
ULNA_PATH_SITES = ["ECU-P2", "ECU-P3", "ECU-P4"]
RADIUS_PATH_SITES = ["BIClong-P9", "BIClong-P11"]
ATTACH_SITES_ULNA = ["PT-P2", "BRA-P3", "BRA-P4"]


# ------------------------------------------------------------ building blocks --
def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_birth_pack():
    """Target pack (birth mesh + JNT3 joints); loader law per ONT-A01's pinned copy."""
    b = core.INPUT_BIRTH.read_bytes()
    N, M = struct.unpack("<ii", b[:8])
    V = np.frombuffer(b, np.float32, N * 3, 8).reshape(N, 3).astype(np.float64)
    F = np.frombuffer(b, np.uint32, M * 3, 8 + N * 12).reshape(M, 3)
    p = core.INPUT_PACK.read_bytes()
    assert p[:4] == b"JNT3", p[:4]
    nv, nj, nl = struct.unpack("<III", p[4:16])
    names = [n.decode("ascii") for n in p[16:16 + nl].split(b"\x00") if n][:nj]
    q = 16 + nl
    q += nv * 4  # assign
    q += nv * 4  # weights
    J = np.frombuffer(p, np.float32, nj * 3, q).reshape(nj, 3).astype(np.float64)
    q += nj * 12
    q += nj * 12  # AX
    q += nj * 8   # ROM
    parents = np.frombuffer(p, np.int32, nj, q)
    idx = {n: i for i, n in enumerate(names)}
    class Pack:
        pass
    pk = Pack()
    pk.V, pk.F, pk.names, pk.idx = V, F, names, idx
    pk.joint_pos = lambda name: J[idx[name]].copy()
    pk.parents = parents
    return pk


def load_binary_stl(path: Path):
    b = path.read_bytes()
    (n,) = struct.unpack("<I", b[80:84])
    assert len(b) == 84 + n * 50, (path, n, len(b))
    rec = np.frombuffer(b, dtype=np.uint8, count=n * 50, offset=84).reshape(n, 50)
    floats = rec[:, :48].copy().view("<f4").reshape(n, 4, 3)
    tris = floats[:, 1:].astype(np.float64)
    verts, inv = np.unique(tris.reshape(-1, 3), axis=0, return_inverse=True)
    return verts, inv.reshape(n, 3).astype(np.int64)


def bone_meshes_mm():
    """ulna.stl + radius.stl, XML-declared scale (1, 1.2, 1), metres -> mm."""
    scale = np.array([1.0, 1.2, 1.0])
    Vu, Fu = load_binary_stl(HERE / "reference" / "meshes" / "ulna.stl")
    Vr, Fr = load_binary_stl(HERE / "reference" / "meshes" / "radius.stl")
    return Vu * scale * 1000.0, Fu, Vr * scale * 1000.0, Fr


def source_offsets_mm():
    src = core.source_geometry()
    u2r = np.asarray(src["right"]["u2r"], float) * 1000.0
    decomp = core.anatomical_decomposition(np.asarray(src["right"]["u2r"], float),
                                           np.asarray(src["right"]["e2h"], float))
    return u2r, decomp


def target_submesh(R=0.06):
    """Triangles of the birth mesh with all vertices within R of the elbow->wrist
    segment (deterministic region selection; R is a single declared radius)."""
    pk = load_birth_pack()
    V, F = pk.V * 0.065, pk.F  # authored prototype scale (mesh_target_o1 law)
    elbow = pk.joint_pos("elbow_R") * 0.065
    wrist = pk.joint_pos("wrist_R") * 0.065
    d = wrist - elbow
    t = np.clip(((V - elbow) @ d) / (d @ d), 0.0, 1.0)
    closest = elbow + t[:, None] * d
    dist = np.linalg.norm(V - closest, axis=1)
    keep_v = dist <= R
    tri_keep = keep_v[F].all(axis=1)
    return V, F[tri_keep]


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
    forward = core_unit(np.asarray(target, float) - np.asarray(position, float))
    Zc = -forward
    up = np.asarray(up_hint, float)
    Yc = core_unit(up - (up @ Zc) * Zc)
    Xc = np.cross(Yc, Zc)
    return Xc, Yc, Zc, forward


def core_unit(v):
    return v / np.linalg.norm(v)


def cam_sample(position, target, up_hint):
    Xc, Yc, Zc, _ = camera_basis(position, target, up_hint)
    q = mat_to_quat_wxyz(np.column_stack([Xc, Yc, Zc]))
    pos = [float(v) for v in position]
    tgt = [float(v) for v in target]
    return {"position": pos, "target": tgt,
            "distance_to_target": float(np.linalg.norm(np.subtract(pos, tgt))),
            "orientation": [float(v) for v in q]}


def fit_camera(points, anchor_target, direction, dist, aspect, margin=FRAME_MARGIN):
    direction = core_unit(np.asarray(direction, float))
    anchor_target = np.asarray(anchor_target, float)
    pos0 = anchor_target + direction * dist
    Xc, Yc, Zc, _ = camera_basis(pos0, anchor_target, [0, 1, 0])
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


def project(points, cam, span, W, H):
    Xc, Yc, Zc, fwd = camera_basis(cam["position"], cam["target"], [0, 1, 0])
    rel = np.asarray(points, float) - np.asarray(cam["position"])
    xc, yc = rel @ Xc, rel @ Yc
    aspect = W / H
    px = (xc / (span * aspect) + 0.5) * W
    py = (1.0 - (yc / span + 0.5)) * H
    depth = rel @ fwd
    return np.column_stack([px, py, depth])


def assert_in_bounds(points, cam, span, W, H, margin=FRAME_MARGIN):
    p = project(np.asarray(points, float), cam, span, W, H)
    inx, iny = panel_inset(W, H, margin)
    eps = 1e-6
    ok = (p[:, 0].min() >= inx - eps and p[:, 0].max() <= W - inx + eps
          and p[:, 1].min() >= iny - eps and p[:, 1].max() <= H - iny + eps)
    assert ok, (f"declared subject exceeds framed panel: px[{p[:, 0].min():.3f},"
                f"{p[:, 0].max():.3f}] py[{p[:, 1].min():.3f},{p[:, 1].max():.3f}]"
                f" on {W}x{H} (margin {margin})")


# ---------------------------------------------------------------- geometry -----
def declared_subject_points(pair_id):
    """The declared subject point set each panel must contain (same pinned geometry
    the views draw). V1: whole creature mesh + joints + box corners + both anchors.
    V2: both source bone meshes + offset/component arrow tips + origins + triad tips
    + tendon-path waypoints (common source rest frame, mm). V3: the target forearm
    sub-mesh + elbow/wrist + both anchors (target frame, m)."""
    if pair_id == "V1":
        pk = load_birth_pack()
        V = pk.V * 0.065
        elbow = pk.joint_pos("elbow_R") * 0.065
        wrist = pk.joint_pos("wrist_R") * 0.065
        P_new = np.asarray(core.declaration()["records"]["ulna"]["landmarks"]["dist"]["target"], float)
        box_lo = np.minimum(elbow, wrist) - np.array([0.045, 0.03, 0.045])
        box_hi = np.maximum(elbow, wrist) + np.array([0.045, 0.03, 0.045])
        corners = np.array([box_lo + np.array([bool((a >> s) & 1) for s in range(3)], float)
                            * (box_hi - box_lo) for a in range(8)])
        return np.vstack([V, elbow[None, :], wrist[None, :], P_new[None, :], corners])
    if pair_id == "V2":
        # declared CLOSE-UP subject: the proximal attachment region of both bones
        # (vertices within 100 mm of the respective body origin) + the offset and
        # component arrows + the two origins + triad tips + recorded tendon-path
        # points. The distal bone shafts are the declared backdrop of the close-up
        # (same semantics as ONT-A01's reviewed V2).
        Vu, Fu, Vr, Fr = bone_meshes_mm()
        u2r, decomp = source_offsets_mm()
        near_u = Vu[np.linalg.norm(Vu, axis=1) <= 100.0]
        Vrs = Vr + u2r
        near_r = Vrs[np.linalg.norm(Vrs - u2r, axis=1) <= 100.0]
        a, l, p = decomp["a"], decomp["l"], decomp["p"]
        tips = np.array([
            u2r,
            a * decomp["axial_mm"], l * decomp["lateral_mm"], p * decomp["posterior_mm"],
            np.array([60.0, 0, 0]), np.array([0, 60.0, 0]), np.array([0, 0, 60.0]),
        ])
        path = tendon_path_points_mm()
        return np.vstack([near_u, near_r, tips, path, np.zeros((1, 3))])
    if pair_id == "V3":
        V, F = target_submesh()
        pk = load_birth_pack()
        elbow = pk.joint_pos("elbow_R") * 0.065
        wrist = pk.joint_pos("wrist_R") * 0.065
        P_new = np.asarray(core.declaration()["records"]["ulna"]["landmarks"]["dist"]["target"], float)
        used = np.unique(F)
        return np.vstack([V[used], elbow[None, :], wrist[None, :], P_new[None, :]])
    raise KeyError(pair_id)


def tendon_path_points_mm():
    """Recorded tendon-path waypoints (source locals, common ulna rest frame, mm)."""
    pk = core.packet_records()
    u2r_mm, _ = source_offsets_mm()
    pts = []
    for name in ULNA_PATH_SITES + ATTACH_SITES_ULNA:
        pts.append(np.asarray(pk["sites"]["ulna"][name]["x_local"], float) * 1000.0)
    for name in RADIUS_PATH_SITES:
        pts.append(np.asarray(pk["sites"]["radius"][name]["x_local"], float) * 1000.0 + u2r_mm)
    return np.array(pts)


def build_geometry():
    """All camera decisions in one deterministic place (reused by the bounds test)."""
    geo = {}
    pk = load_birth_pack()
    V = pk.V * 0.065
    F = pk.F
    center = (V.min(0) + V.max(0)) / 2.0
    diag = float(np.linalg.norm(V.max(0) - V.min(0)))
    subj1 = declared_subject_points("V1")
    pos1, tgt1, span1 = fit_camera(subj1, center, core_unit([0.30, 0.35, 1.0]),
                                   diag * 1.15, PANEL_W / PANEL_H)
    cam1 = cam_sample(pos1, tgt1, [0, 1, 0])
    assert_in_bounds(subj1, cam1, span1, PANEL_W, PANEL_H)
    geo["V1"] = {"points": subj1, "cam": cam1, "span": span1}

    Vu, Fu, Vr, Fr = bone_meshes_mm()
    u2r, decomp = source_offsets_mm()
    subj2 = declared_subject_points("V2")
    c2 = u2r * 0.5
    # volar-dominant close-up: puts the offset's axial (-y) and lateral (+z)
    # components in the image plane so the 23.0746 mm offset reads at true scale
    pos2, tgt2, span2 = fit_camera(subj2, c2, core_unit([1.0, 0.18, 0.05]),
                                   260.0, PANEL_W / PANEL_H)
    cam2 = cam_sample(pos2, tgt2, [0, 1, 0])
    assert_in_bounds(subj2, cam2, span2, PANEL_W, PANEL_H)
    geo["V2"] = {"points": subj2, "cam": cam2, "span": span2}

    Vsub, Fsub = target_submesh()
    used = np.unique(Fsub)
    subj3 = declared_subject_points("V3")
    elbow = pk.joint_pos("elbow_R") * 0.065
    wrist = pk.joint_pos("wrist_R") * 0.065
    mid = (elbow + wrist) / 2.0
    span_len = float(np.linalg.norm(wrist - elbow))
    dirs = [
        (core_unit([1.0, 0.0, 0.0]), "anterior (+x view)"),
        (core_unit([-1.0, 0.0, 0.0]), "posterior (-x view)"),
        (core_unit([-0.55, 0.25, -1.0]), "lateral oblique (-z,+x up-tilt)"),
        (core_unit([0.35, 1.0, 0.0]), "superior (+y view)"),
    ]
    dist3 = span_len * 6.0
    fits3 = [fit_camera(subj3, mid, d, dist3, PANEL_W / PANEL_H) for d, _ in dirs]
    span3 = max(s for _, _, s in fits3)
    cams3 = [cam_sample(p, t, [0, 1, 0]) for p, t, _ in fits3]
    for cam3 in cams3:
        assert_in_bounds(subj3, cam3, span3, PANEL_W, PANEL_H)
    geo["V3"] = {"points": subj3, "cam_list": cams3, "span": span3,
                 "names": [n for _, n in dirs], "mesh_used": used, "F": Fsub, "V": Vsub}
    return geo


# -------------------------------------------------------------- rasterizer -----
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
        sub_rgb[m] = base[k][None, :]


def draw_arrow_2d(ax, p0, p1, color, lw=1.6):
    ax.annotate("", xy=(p1[0], p1[1]), xytext=(p0[0], p0[1]),
                xycoords="data", textcoords="data",
                arrowprops=dict(arrowstyle="->", color=color, lw=lw))


def label_offset_inside(anchor_xy, dx, dy, W, H, pad=6.0, pad_top=22.0):
    """Deterministically keep a screen-space label anchor inside its panel: flip the
    offset if it exits, then clamp so the anchor cannot sit off-panel (no hand-tuned
    per-label values; 'stable 3D labels' is a declared diagnostic layer)."""
    x, y = anchor_xy[0] + dx, anchor_xy[1] + dy
    if not (pad <= x <= W - pad):
        dx = -dx
    if not (pad <= y <= H - pad_top):
        dy = -dy
    x, y = anchor_xy[0] + dx, anchor_xy[1] + dy
    dx += max(pad, min(W - pad, x)) - x
    dy += max(pad_top, min(H - pad, y)) - y
    return dx, dy


def compose_panel(ax, rgb, title, mode):
    ax.imshow(np.clip(rgb, 0, 255).astype(np.uint8), extent=[0, PANEL_W, 0, PANEL_H],
              interpolation="nearest", zorder=0)
    ax.set_xlim(0, PANEL_W)
    ax.set_ylim(0, PANEL_H)
    ax.axis("off")
    tag = "DIAGNOSTIC" if mode == "diagnostic" else "CLEAN"
    ax.text(4, PANEL_H - 4, f"{title} [{tag}]", fontsize=7, color="black",
            ha="left", va="top", zorder=10,
            bbox=dict(fc="white", ec="none", alpha=0.75, pad=1.2))


def panel_rgb(cam, span, mesh_color, V, F):
    rgb = np.full((PANEL_H, PANEL_W, 3), 255, dtype=np.float64)
    zbuf = np.full((PANEL_H, PANEL_W), np.inf)
    render_mesh(rgb, zbuf, V, F, cam, span, mesh_color, PANEL_W, PANEL_H)
    return np.clip(rgb, 0, 255).astype(np.uint8)


def panel_rgb_two(cam, span, pieces):
    """One shared z-buffer pass over several (V, F, color) meshes (true mutual depth)."""
    rgb = np.full((PANEL_H, PANEL_W, 3), 255, dtype=np.float64)
    zbuf = np.full((PANEL_H, PANEL_W), np.inf)
    for V, F, color in pieces:
        render_mesh(rgb, zbuf, V, F, cam, span, color, PANEL_W, PANEL_H)
    return np.clip(rgb, 0, 255).astype(np.uint8)


def put_in_sheet(sheet, buf, col, row):
    y0, x0 = row * PANEL_H, col * PANEL_W
    sheet[y0:y0 + PANEL_H, x0:x0 + PANEL_W] = buf


# ------------------------------------------------------------------ build ------
def build_everything():
    state, receipt = core.write_receipts()
    EVIDENCE.mkdir(exist_ok=True)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    geo = build_geometry()
    sheet = np.full((SHEET_H, SHEET_W, 3), 255, dtype=np.uint8)
    manifest_views = []
    state_sha = hashlib.sha256((EVIDENCE / "state_snapshot.json").read_bytes()).hexdigest()
    state_binding = {"kind": "state", "sha256": state_sha}

    pk = load_birth_pack()
    Vt, Ft = pk.V * 0.065, pk.F
    center = (Vt.min(0) + Vt.max(0)) / 2.0
    elbow = pk.joint_pos("elbow_R") * 0.065
    wrist = pk.joint_pos("wrist_R") * 0.065
    P_new = np.asarray(core.declaration()["records"]["ulna"]["landmarks"]["dist"]["target"], float)
    u2r, decomp = source_offsets_mm()
    Vu, Fu, Vr, Fr = bone_meshes_mm()

    # ------------------------------------------------ V1 whole-creature overview
    g = geo["V1"]
    cam1, span1 = g["cam"], g["span"]
    rgb = panel_rgb(cam1, span1, SKIN_COLOR, Vt, Ft)

    box_lo = np.minimum(elbow, wrist) - np.array([0.045, 0.03, 0.045])
    box_hi = np.maximum(elbow, wrist) + np.array([0.045, 0.03, 0.045])
    corners3 = np.array([box_lo + np.array([bool((a >> s) & 1) for s in range(3)], float)
                         * (box_hi - box_lo) for a in range(8)])
    box_edges = [(a, b) for a in range(8) for b in range(8)
                 if sum(1 for s in range(3) if ((a >> s) & 1) != ((b >> s) & 1)) == 1]
    fig = plt.figure(figsize=(PANEL_W / 100, PANEL_H / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.imshow(rgb, extent=[0, PANEL_W, 0, PANEL_H], interpolation="nearest", zorder=0)
    corners = project(corners3, cam1, span1, PANEL_W, PANEL_H)
    for a, b in box_edges:
        ax.plot([corners[a, 0], corners[b, 0]], [PANEL_H - corners[a, 1], PANEL_H - corners[b, 1]],
                color=(0.1, 0.4, 0.9), lw=1.2, zorder=6)
    # elbow->wrist axis
    axp = project(np.array([elbow, wrist]), cam1, span1, PANEL_W, PANEL_H)
    ax.plot([axp[0, 0], axp[1, 0]], [PANEL_H - axp[0, 1], PANEL_H - axp[1, 1]],
            color=tuple(c / 255 for c in AXIS_COLOR), lw=1.4, ls=":", zorder=6)
    for pt, col in ((elbow, BEFORE_COLOR), (P_new, AFTER_COLOR), (wrist, AXIS_COLOR)):
        p = project(np.array([pt]), cam1, span1, PANEL_W, PANEL_H)[0]
        ax.plot([p[0]], [PANEL_H - p[1]], "o", ms=4.2, color=tuple(c / 255 for c in col),
                zorder=7, markeredgecolor="black", markeredgewidth=0.4)
    # label anchors spread to the open right side of the panel with short leader lines
    lead = [(elbow, "elbow_R", BEFORE_COLOR, (36, 74)),
            (elbow, "radius P before = elbow_R (packet anchor)", BEFORE_COLOR, (36, 58)),
            (P_new, "radius P after = ulna.P_d (+5.1158 mm)", AFTER_COLOR, (36, 42)),
            (wrist, "wrist_R (radius distal anchor, unchanged)", AXIS_COLOR, (36, -30))]
    for pt, lab, col, off in lead:
        p = project(np.array([pt]), cam1, span1, PANEL_W, PANEL_H)[0]
        dx, dy = label_offset_inside((p[0], PANEL_H - p[1]), *off, PANEL_W, PANEL_H)
        ax.plot([p[0], p[0] + dx * 0.8], [PANEL_H - p[1], PANEL_H - p[1] + dy * 0.8],
                lw=0.5, color="gray", zorder=7)
        ax.text(p[0] + dx, PANEL_H - p[1] + dy, lab, fontsize=5.8, color="black", zorder=8,
                bbox=dict(fc="white", ec="none", alpha=0.7, pad=0.6))
    ctr = project(np.array([center]), cam1, span1, PANEL_W, PANEL_H)[0]
    ax.text(ctr[0] + 6, PANEL_H - ctr[1], f"target creature mesh ({len(Vt)} verts / {len(Ft)} tris)",
            fontsize=5.8, color="black", zorder=8, bbox=dict(fc="white", ec="none", alpha=0.7, pad=0.5))
    bc = project(np.array([box_hi]), cam1, span1, PANEL_W, PANEL_H)[0]
    dxb, dyb = label_offset_inside((bc[0], PANEL_H - bc[1]), 10, 26, PANEL_W, PANEL_H)
    ax.text(bc[0] + dxb, PANEL_H - bc[1] + dyb, "right forearm region (boxed)", fontsize=5.6,
            color="black", zorder=8, bbox=dict(fc="white", ec="none", alpha=0.7, pad=0.5))
    midw = project(np.array([(elbow + wrist) / 2.0]), cam1, span1, PANEL_W, PANEL_H)[0]
    dxm, dym = label_offset_inside((midw[0], PANEL_H - midw[1]), 36, -52, PANEL_W, PANEL_H)
    ax.text(midw[0] + dxm, PANEL_H - midw[1] + dym, "elbow→wrist axis (305.7922 mm source span)",
            fontsize=5.6, color="black", zorder=8, bbox=dict(fc="white", ec="none", alpha=0.7, pad=0.5))
    o1 = np.array([Vt[:, 0].min(), Vt[:, 1].min(), Vt[:, 2].max()]) + np.array([0.02, 0.02, -0.02])
    for d, lab, col in (([0, 0, 1], "+z anterior", (0, 0, 0)), ([0, 1, 0], "+y up", (0, 0, 0)),
                        ([-1, 0, 0], "-x right", (0, 0, 0))):
        tip3 = o1 + np.array(d, float) * span1 * 0.14
        t2 = project(np.array([tip3]), cam1, span1, PANEL_W, PANEL_H)[0]
        v = np.array([t2[0] - o1[0], -(t2[1] - o1[1])])
        v = v / max(np.linalg.norm(v), 1e-9) * 24
        ax0, ay0 = 74.0, PANEL_H - 74.0
        draw_arrow_2d(ax, (ax0, ay0), (ax0 + v[0], ay0 + v[1]), tuple(c / 255 for c in col))
        tdx, tdy = label_offset_inside((ax0 + v[0], ay0 + v[1]), 4, 3, PANEL_W, PANEL_H)
        ax.text(ax0 + v[0] + tdx, ay0 + v[1] + tdy, lab, fontsize=7, color="black", zorder=8)
    compose_panel(ax, rgb, "V1 whole-creature overview (target frame, m)", "diagnostic")
    fig.canvas.draw()
    put_in_sheet(sheet, np.asarray(fig.canvas.buffer_rgba())[:, :, :3], 0, 0)
    plt.close(fig)

    fig = plt.figure(figsize=(PANEL_W / 100, PANEL_H / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    compose_panel(ax, rgb, "V1 whole-creature overview", "clean")
    fig.canvas.draw()
    put_in_sheet(sheet, np.asarray(fig.canvas.buffer_rgba())[:, :, :3], 1, 0)
    plt.close(fig)

    def v1_vis(mode):
        if mode == "clean":
            return {"layers": [], "label_ids": [], "selected_ids": [],
                    "required_subject_ids": ["target_monkey_mesh"],
                    "observed_subject_ids": ["target_monkey_mesh"],
                    "missing_subject_ids": [], "occlusion_mode": "depth_tested",
                    "tag_bindings": []}
        labels = ["L-mesh", "L-elbow_R", "L-P-before", "L-P-after", "L-wrist_R", "L-region-box",
                  "L-elbow-wrist-axis", "L-ax-z", "L-ax-y", "L-ax-x"]
        subs = ["target_monkey_mesh", "target_joint_elbow_R", "target_anchor_radius_before",
                "target_anchor_radius_after", "target_joint_wrist_R", "target_forearm_region_box",
                "target_elbow_wrist_axis", "target_frame_axis_anterior_z",
                "target_frame_axis_up_y", "target_frame_axis_right_x"]
        bindings = [{"label_id": lab, "subject_id": sub} for lab, sub in zip(labels, subs)]
        return {"layers": ["outer envelope", "selected bones/joints", "attachment sites",
                           "frame axes", "stable 3D labels"],
                "label_ids": labels, "selected_ids": ["target_monkey_mesh", "target_forearm_region_box"],
                "required_subject_ids": ["target_monkey_mesh", "target_forearm_region_box",
                                         "target_anchor_radius_after"],
                "observed_subject_ids": subs, "missing_subject_ids": [],
                "occlusion_mode": "mixed", "tag_bindings": bindings}

    cam1_meta = {
        "frame_id": "target_world_frame(+z anterior,+y up,-x right; O1 §1)",
        "coordinate_unit": "m", "handedness": "right",
        "orientation_convention": "quaternion_wxyz_camera_to_frame",
        "forward_axis": "-Z", "up_axis": "+Y",
        "near_far_planes": [0.01, round(float(np.linalg.norm(Vt.max(0) - Vt.min(0)) * 3.0), 3)],
        "viewport_resolution": [PANEL_W, PANEL_H],
        "aspect_ratio": PANEL_W / PANEL_H,
        "projection": "orthographic", "orthographic_span": float(span1),
        "sample_mode": "fixed_bookmark",
        "samples": [dict(cam1, tick=t) for t in TICKS],
    }
    manifest_views.append({"view_id": PROFILE["views"][0], "mode": "diagnostic", "pair_id": "V1",
                           "state_binding": state_binding,
                           "artifact_locator": {"kind": "image", "region": "pixel_rectangle",
                                                "pixel_rectangle": [0, 0, PANEL_W, PANEL_H]},
                           "camera": cam1_meta, "visibility": v1_vis("diagnostic")})
    manifest_views.append({"view_id": PROFILE["views"][0], "mode": "clean", "pair_id": "V1",
                           "state_binding": state_binding,
                           "artifact_locator": {"kind": "image", "region": "pixel_rectangle",
                                                "pixel_rectangle": [PANEL_W, 0, PANEL_W, PANEL_H]},
                           "camera": cam1_meta, "visibility": v1_vis("clean")})

    # ------------------------------------------------ V2 local attachment close-up
    g = geo["V2"]
    cam2, span2 = g["cam"], g["span"]
    Vr_shift = Vr + u2r
    rgb2 = panel_rgb_two(cam2, span2, [(Vu, Fu, BONE_COLOR), (Vr_shift, Fr, RADIUS_COLOR)])

    fig = plt.figure(figsize=(PANEL_W / 100, PANEL_H / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.imshow(rgb2, extent=[0, PANEL_W, 0, PANEL_H], interpolation="nearest", zorder=0)
    # tendon path waypoints (recorded; unoccluded overlay)
    pkrec = core.packet_records()
    ecu = np.array([np.asarray(pkrec["sites"]["ulna"][s]["x_local"], float) * 1000.0
                    for s in ULNA_PATH_SITES])
    bic = np.array([np.asarray(pkrec["sites"]["radius"][s]["x_local"], float) * 1000.0 + u2r
                    for s in RADIUS_PATH_SITES])
    for pts, col in ((ecu, COURSE_COLOR), (bic, RADIUS_SITE_COLOR)):
        pr = project(pts, cam2, span2, PANEL_W, PANEL_H)
        ax.plot(pr[:, 0], PANEL_H - pr[:, 1], color=tuple(c / 255 for c in col), lw=1.4, ls="--", zorder=6)
        ax.plot(pr[:, 0], PANEL_H - pr[:, 1], "o", ms=3.0, color=tuple(c / 255 for c in col), zorder=7)
    cpt = project(np.array([ecu[-1]]), cam2, span2, PANEL_W, PANEL_H)[0]
    ax.text(cpt[0] + 4, PANEL_H - cpt[1] - 10, "recorded tendon-path waypoints ECU-P2..P4",
            fontsize=5.6, color=tuple(c / 255 for c in COURSE_COLOR), zorder=8,
            bbox=dict(fc="white", ec="none", alpha=0.7, pad=0.6))
    bpt = project(np.array([bic[-1]]), cam2, span2, PANEL_W, PANEL_H)[0]
    ax.text(bpt[0] + 4, PANEL_H - bpt[1] + 8, "BIClong-P9/P11 (radius)",
            fontsize=5.6, color=tuple(c / 255 for c in RADIUS_SITE_COLOR), zorder=8,
            bbox=dict(fc="white", ec="none", alpha=0.7, pad=0.6))
    for s in ATTACH_SITES_ULNA:
        x = np.asarray(pkrec["sites"]["ulna"][s]["x_local"], float) * 1000.0
        p = project(np.array([x]), cam2, span2, PANEL_W, PANEL_H)[0]
        ax.plot([p[0]], [PANEL_H - p[1]], "s", ms=3.2, color=tuple(c / 255 for c in FLEXOR_COLOR),
                zorder=7, markeredgecolor="black", markeredgewidth=0.3)
        dx, dy = label_offset_inside((p[0], PANEL_H - p[1]), 6, 10, PANEL_W, PANEL_H)
        ax.text(p[0] + dx, PANEL_H - p[1] + dy, s, fontsize=5.4, color="black", zorder=8,
                bbox=dict(fc="white", ec="none", alpha=0.65, pad=0.5))
    # origins + offset + components
    o2 = project(np.array([[0.0, 0.0, 0.0]]), cam2, span2, PANEL_W, PANEL_H)[0]
    r2 = project(np.array([u2r]), cam2, span2, PANEL_W, PANEL_H)[0]
    ax.plot([o2[0]], [PANEL_H - o2[1]], "o", ms=4.5, color="black", zorder=7)
    ax.plot([r2[0]], [PANEL_H - r2[1]], "o", ms=4.5, color=tuple(c / 255 for c in RADIUS_SITE_COLOR), zorder=7)
    draw_arrow_2d(ax, (o2[0], PANEL_H - o2[1]), (r2[0], PANEL_H - r2[1]), (0, 0, 0), lw=1.3)
    dxo, dyo = label_offset_inside((o2[0], PANEL_H - o2[1]), -118, -26, PANEL_W, PANEL_H)
    ax.text(o2[0] + dxo, PANEL_H - o2[1] + dyo, "ulna origin (elbow_flexion)", fontsize=5.8,
            color="black", zorder=8, bbox=dict(fc="white", ec="none", alpha=0.7, pad=0.5))
    dxr, dyr = label_offset_inside((r2[0], PANEL_H - r2[1]), 18, -34, PANEL_W, PANEL_H)
    ax.text(r2[0] + dxr, PANEL_H - r2[1] + dyr,
            "radius body origin (kinematic offset 23.0746 mm)", fontsize=5.8,
            color="black", zorder=8, bbox=dict(fc="white", ec="none", alpha=0.7, pad=0.5))
    comp = [("axial +14.324 mm", decomp["a"] * decomp["axial_mm"], (200, 60, 20)),
            ("lateral +18.088 mm", decomp["l"] * decomp["lateral_mm"], (30, 120, 200)),
            ("posterior +0.301 mm", decomp["p"] * decomp["posterior_mm"], (120, 120, 120))]
    for lab, vec, col in comp:
        t = project(np.array([vec]), cam2, span2, PANEL_W, PANEL_H)[0]
        draw_arrow_2d(ax, (o2[0], PANEL_H - o2[1]), (t[0], PANEL_H - t[1]), tuple(c / 255 for c in col))
        dx, dy = label_offset_inside((t[0], PANEL_H - t[1]), 4, 6, PANEL_W, PANEL_H)
        ax.text(t[0] + dx, PANEL_H - t[1] + dy, lab, fontsize=5.6, color=tuple(c / 255 for c in col),
                zorder=8, bbox=dict(fc="white", ec="none", alpha=0.65, pad=0.5))
    ax.text(6, 30, "offset 51.63° to the 305.7922 mm elbow→hand axis (rest pose)",
            fontsize=5.4, color="black", zorder=8, bbox=dict(fc="white", ec="none", alpha=0.7, pad=0.5))
    pu = project(np.array([Vu.mean(0)]), cam2, span2, PANEL_W, PANEL_H)[0]
    dxu, dyu = label_offset_inside((pu[0], PANEL_H - pu[1]), -70, -26, PANEL_W, PANEL_H)
    ax.text(pu[0] + dxu, PANEL_H - pu[1] + dyu, "ulna.stl (authored scale 1,1.2,1)", fontsize=5.6,
            color="black", zorder=8, bbox=dict(fc="white", ec="none", alpha=0.7, pad=0.5))
    prv = project(np.array([(Vr + u2r).mean(0)]), cam2, span2, PANEL_W, PANEL_H)[0]
    dxp, dyp = label_offset_inside((prv[0], PANEL_H - prv[1]), 10, 16, PANEL_W, PANEL_H)
    ax.text(prv[0] + dxp, PANEL_H - prv[1] + dyp, "radius.stl at the authored offset", fontsize=5.6,
            color="black", zorder=8, bbox=dict(fc="white", ec="none", alpha=0.7, pad=0.5))
    moff = project(np.array([u2r * 0.5]), cam2, span2, PANEL_W, PANEL_H)[0]
    dmo, dmo2 = label_offset_inside((moff[0], PANEL_H - moff[1]), 60, 46, PANEL_W, PANEL_H)
    ax.plot([moff[0], moff[0] + dmo * 0.7], [PANEL_H - moff[1], PANEL_H - moff[1] + dmo2 * 0.7],
            lw=0.5, color="gray", zorder=7)
    ax.text(moff[0] + dmo, PANEL_H - moff[1] + dmo2, "ulna→radius kinematic offset 23.0746 mm",
            fontsize=5.6, color="black", zorder=8, bbox=dict(fc="white", ec="none", alpha=0.7, pad=0.5))
    for d, lab in ((np.array([60.0, 0, 0]), "volar +x"), (np.array([0, 60.0, 0]), "+y up"),
                   (np.array([0, 0, 60.0]), "+z right")):
        t = project(np.array([d]), cam2, span2, PANEL_W, PANEL_H)[0]
        draw_arrow_2d(ax, (o2[0], PANEL_H - o2[1]), (t[0], PANEL_H - t[1]), (0.08, 0.08, 0.08))
        ax.text(t[0] + 3, PANEL_H - t[1] + 3, lab, fontsize=5.6, color="black", zorder=8)
    compose_panel(ax, rgb2, "V2 radioulnar close-up (source rest frame, mm)", "diagnostic")
    fig.canvas.draw()
    put_in_sheet(sheet, np.asarray(fig.canvas.buffer_rgba())[:, :, :3], 2, 0)
    plt.close(fig)

    fig = plt.figure(figsize=(PANEL_W / 100, PANEL_H / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    compose_panel(ax, rgb2, "V2 radioulnar close-up", "clean")
    fig.canvas.draw()
    put_in_sheet(sheet, np.asarray(fig.canvas.buffer_rgba())[:, :, :3], 3, 0)
    plt.close(fig)

    def v2_vis(mode):
        if mode == "clean":
            return {"layers": [], "label_ids": [], "selected_ids": [],
                    "required_subject_ids": ["source_ulna_mesh"],
                    "observed_subject_ids": ["source_ulna_mesh", "source_radius_mesh"],
                    "missing_subject_ids": [], "occlusion_mode": "depth_tested",
                    "tag_bindings": []}
        subs = ["source_ulna_mesh", "source_radius_mesh", "radioulnar_offset_vector",
                "offset_component_axial", "offset_component_lateral",
                "offset_component_posterior", "ecu_tendon_path", "bic_tendon_path",
                "ulna_origin_elbow", "radius_body_origin", "source_frame_axis_volar_x",
                "source_frame_axis_up_y", "source_frame_axis_right_z"]
        labels = ["L-ulna", "L-radius", "L-offset", "L-axial", "L-lateral", "L-posterior",
                  "L-ecu-path", "L-bic-path", "L-ulna-origin", "L-radius-origin",
                  "L-volar", "L-up", "L-right"]
        bindings = [{"label_id": lab, "subject_id": sub} for lab, sub in zip(labels, subs)]
        return {"layers": ["selected bones/joints", "muscle/tendon paths", "attachment sites",
                           "frame axes", "stable 3D labels"],
                "label_ids": labels, "selected_ids": ["source_ulna_mesh", "source_radius_mesh"],
                "required_subject_ids": ["source_ulna_mesh", "source_radius_mesh",
                                         "radioulnar_offset_vector"],
                "observed_subject_ids": subs, "missing_subject_ids": [],
                "occlusion_mode": "mixed", "tag_bindings": bindings}

    cam2_meta = {
        "frame_id": "source_rest_frame(+x volar,+y up,+z right; chimanoid.xml rest, axis-aligned asserted)",
        "coordinate_unit": "mm", "handedness": "right",
        "orientation_convention": "quaternion_wxyz_camera_to_frame",
        "forward_axis": "-Z", "up_axis": "+Y",
        "near_far_planes": [1.0, 1000.0],
        "viewport_resolution": [PANEL_W, PANEL_H],
        "aspect_ratio": PANEL_W / PANEL_H,
        "projection": "orthographic", "orthographic_span": float(span2),
        "sample_mode": "fixed_bookmark",
        "samples": [dict(cam2, tick=t) for t in TICKS],
    }
    manifest_views.append({"view_id": PROFILE["views"][1], "mode": "diagnostic", "pair_id": "V2",
                           "state_binding": state_binding,
                           "artifact_locator": {"kind": "image", "region": "pixel_rectangle",
                                                "pixel_rectangle": [2 * PANEL_W, 0, PANEL_W, PANEL_H]},
                           "camera": cam2_meta, "visibility": v2_vis("diagnostic")})
    manifest_views.append({"view_id": PROFILE["views"][1], "mode": "clean", "pair_id": "V2",
                           "state_binding": state_binding,
                           "artifact_locator": {"kind": "image", "region": "pixel_rectangle",
                                                "pixel_rectangle": [3 * PANEL_W, 0, PANEL_W, PANEL_H]},
                           "camera": cam2_meta, "visibility": v2_vis("clean")})

    # ------------------------------------------- V3 orthogonal side and obliques
    g = geo["V3"]
    span3, cams3 = g["span"], g["cam_list"]
    Vsub, Fsub = g["V"], g["F"]
    mid = (elbow + wrist) / 2.0
    for row, mode in ((1, "diagnostic"), (2, "clean")):
        for k, cam3 in enumerate(cams3):
            rgb3 = panel_rgb(cam3, span3, SKIN_COLOR, Vsub, Fsub)
            fig = plt.figure(figsize=(PANEL_W / 100, PANEL_H / 100), dpi=100)
            ax = fig.add_axes([0, 0, 1, 1])
            ax.imshow(rgb3, extent=[0, PANEL_W, 0, PANEL_H], interpolation="nearest", zorder=0)
            if mode == "diagnostic":
                axp = project(np.array([elbow, wrist]), cam3, span3, PANEL_W, PANEL_H)
                ax.plot([axp[0, 0], axp[1, 0]], [PANEL_H - axp[0, 1], PANEL_H - axp[1, 1]],
                        color=tuple(c / 255 for c in AXIS_COLOR), lw=1.3, ls=":", zorder=6)
                for pt, lab, col, off in (
                        (elbow, "P before (elbow_R)", BEFORE_COLOR, (-104, 12)),
                        (P_new, "P after (+5.1158 mm)", AFTER_COLOR, (8, -20)),
                        (wrist, "wrist_R (unchanged)", AXIS_COLOR, (-88, -12))):
                    p = project(np.array([pt]), cam3, span3, PANEL_W, PANEL_H)[0]
                    ax.plot([p[0]], [PANEL_H - p[1]], "o", ms=4.0, color=tuple(c / 255 for c in col),
                            zorder=7, markeredgecolor="black", markeredgewidth=0.4)
                    dx, dy = label_offset_inside((p[0], PANEL_H - p[1]), *off, PANEL_W, PANEL_H)
                    ax.text(p[0] + dx, PANEL_H - p[1] + dy, lab, fontsize=5.6, color="black",
                            zorder=8, bbox=dict(fc="white", ec="none", alpha=0.7, pad=0.5))
                ax.text(6, PANEL_H - 24, f"span before 64.7449 mm → after 59.6291 mm "
                                         f"(scale −7.9015 %)", fontsize=5.6, color="black", zorder=8,
                        bbox=dict(fc="white", ec="none", alpha=0.7, pad=0.5))
                rm = project(np.array([mid]), cam3, span3, PANEL_W, PANEL_H)[0]
                dxr, dyr = label_offset_inside((rm[0], PANEL_H - rm[1]), 8, 12, PANEL_W, PANEL_H)
                ax.text(rm[0] + dxr, PANEL_H - rm[1] + dyr, "elbow→wrist axis; target forearm region mesh",
                        fontsize=5.6, color="black", zorder=8,
                        bbox=dict(fc="white", ec="none", alpha=0.7, pad=0.5))
                compose_panel(ax, rgb3, f"V3 {g['names'][k]}", "diagnostic")
            else:
                compose_panel(ax, rgb3, "V3 trajectory frame", "clean")
            fig.canvas.draw()
            put_in_sheet(sheet, np.asarray(fig.canvas.buffer_rgba())[:, :, :3], k, row)
            plt.close(fig)

    def v3_vis(mode):
        if mode == "clean":
            return {"layers": [], "label_ids": [], "selected_ids": [],
                    "required_subject_ids": ["target_forearm_region_mesh"],
                    "observed_subject_ids": ["target_forearm_region_mesh"],
                    "missing_subject_ids": [], "occlusion_mode": "depth_tested",
                    "tag_bindings": []}
        subs = ["target_forearm_region_mesh", "target_elbow_wrist_axis",
                "target_anchor_radius_before", "target_anchor_radius_after"]
        labels = ["L-region-mesh", "L-elbow-wrist-axis", "L-P-before", "L-P-after"]
        bindings = [{"label_id": lab, "subject_id": sub} for lab, sub in zip(labels, subs)]
        return {"layers": ["selected bones/joints", "attachment sites", "frame axes",
                           "stable 3D labels"],
                "label_ids": labels, "selected_ids": ["target_forearm_region_mesh"],
                "required_subject_ids": ["target_forearm_region_mesh",
                                         "target_anchor_radius_after"],
                "observed_subject_ids": subs, "missing_subject_ids": [],
                "occlusion_mode": "mixed", "tag_bindings": bindings}

    cam3_meta = {
        "frame_id": "target_world_frame(+z anterior,+y up,-x right; O1 §1)",
        "coordinate_unit": "m", "handedness": "right",
        "orientation_convention": "quaternion_wxyz_camera_to_frame",
        "forward_axis": "-Z", "up_axis": "+Y",
        "near_far_planes": [0.005, 2.0],
        "viewport_resolution": [PANEL_W, PANEL_H],
        "aspect_ratio": PANEL_W / PANEL_H,
        "projection": "orthographic", "orthographic_span": float(span3),
        "sample_mode": "sampled_trajectory",
        "interpolation": "linear_position_target_slerp_orientation",
        "samples": [dict(c, tick=t) for t, c in enumerate(cams3)],
    }
    manifest_views.append({"view_id": PROFILE["views"][2], "mode": "diagnostic", "pair_id": "V3",
                           "state_binding": state_binding,
                           "artifact_locator": {"kind": "image", "region": "pixel_rectangle",
                                                "pixel_rectangle": [0, PANEL_H, SHEET_W, PANEL_H]},
                           "camera": cam3_meta, "visibility": v3_vis("diagnostic")})
    manifest_views.append({"view_id": PROFILE["views"][2], "mode": "clean", "pair_id": "V3",
                           "state_binding": state_binding,
                           "artifact_locator": {"kind": "image", "region": "pixel_rectangle",
                                                "pixel_rectangle": [0, 2 * PANEL_H, SHEET_W, PANEL_H]},
                           "camera": cam3_meta, "visibility": v3_vis("clean")})

    # ------------------------------------------------------- write + validate --
    png_path = EVIDENCE / "capture_sheet.png"
    plt.imsave(png_path, sheet, format="png")
    capture_sha = sha256_file(png_path)
    subject_sha = sha256_file(EVIDENCE / "state_snapshot.json")

    manifest = {
        "schema": "chimera.visual_capture_manifest.v1",
        "task_id": "A02", "card_id": "ONT-A02",
        "attempt_id": "a6c4ddd216a648348d0810f05dd464d4",
        "run_id": RUN_ID, "subject_sha256": subject_sha, "capture_sha256": capture_sha,
        "profile_id": "anatomy", "tick_interval": list(TICKS),
        "render": {
            "backend": "numpy-zbuffer-software-raster-cpu + matplotlib Agg compose",
            "native_engine_frames": False, "deterministic": True, "gpu_used": False,
            "occlusion_semantics": "mesh true z-buffer; diagnostic overlays (markers, labels, "
                                   "arrows, paths, box) intentionally unoccluded = xray semantics, "
                                   "declared occlusion_mode 'mixed'; clean rows depth_tested",
            "honesty": "NOT native application frames; anatomy evidence component capture",
        },
        "views": manifest_views,
    }
    context = {"task_id": "A02", "subject_sha256": subject_sha, "run_id": RUN_ID,
               "capture_sha256": capture_sha, "tick_interval": list(TICKS)}
    sys.path.insert(0, r"E:/PythonChimera/tools/monkey_campaign")
    from visual_capture import validate_manifest
    structural = validate_manifest(manifest, context, PROFILE)
    assert structural["structurally_valid"] is True
    (EVIDENCE / "capture_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    (EVIDENCE / "capture_context.json").write_text(
        json.dumps(context, indent=2, sort_keys=True), encoding="utf-8")
    provenance = {
        "schema": "chimera.ont_a02_visual_provenance.v1",
        "honest_label": "deterministic CPU offline render (numpy z-buffer + Agg text); not native "
                        "engine frames; subject is anatomy evidence records (radioulnar definition, "
                        "before/after radius mapping)",
        "framing": "cameras framed from the PROJECTED BOUNDS of each view's declared subject point "
                   "set (declared_subject_points) + uniform 8% frame margin (fit_camera); "
                   "generation-time guard assert_in_bounds; all-bookmark bounds regression in "
                   "test_ota02_radioulnar.py",
        "panels": {
            "V1": "target pack mesh (monkey_birth.bin, sha 550a5b3e...) whole body in the target "
                  "world frame; frame triad; boxed right forearm region; elbow_R/wrist_R; dotted "
                  "elbow→wrist axis; before anchor (elbow_R) and after anchor (ulna.P_d, +5.1158 mm); "
                  "clean pair = mesh only",
            "V2": "source rest frame (mm): ulna.stl at the ulna body origin and radius.stl at the "
                  "authored 23.0746 mm kinematic offset (scale 1,1.2,1 per the XML); offset vector + "
                  "axial/lateral/posterior component arrows (14.324 / 18.088 / 0.301 mm; 51.63°); "
                  "recorded tendon-path waypoints ECU-P2..P4 (ulna) and BIClong-P9/P11 (radius); "
                  "attachment sites PT-P2/BRA-P3/BRA-P4; clean pair = bones only",
            "V3": "target forearm region sub-mesh (all vertices within 60 mm of the elbow→wrist "
                  "segment), four bookmarks (anterior, posterior, lateral oblique, superior): "
                  "elbow→wrist axis, before/after anchors, span change 64.7449 → 59.6291 mm "
                  "(−7.9015 %); clean strip = region mesh only",
        },
        "structural_validation": structural,
        "outcome_bound": "captures the PRESENTED_AND_VERIFIED state of numerical_receipt.json",
    }
    (EVIDENCE / "visual_provenance.json").write_text(
        json.dumps(provenance, indent=2, sort_keys=True), encoding="utf-8")
    return manifest, structural


def main() -> int:
    manifest, structural = build_everything()
    print("structurally_valid:", structural["structurally_valid"], "views:", structural["view_count"])
    print("wrote", EVIDENCE / "capture_sheet.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
