"""MAT2-G02 visual capture renderer (attachment-fixture/motion).

Round-1 corrections (review sgt-pr281-r1): the previous revision defined
draw_viewport() with ZERO call sites - the published sheet had empty
viewports while the manifest claimed subjects in frame. This revision:

- CALLS draw_viewport() for all six tiles (3 registry views x
  diagnostic/clean): diagnostic rows carry the declared overlays and port
  labels, clean rows are geometry-only;
- gates every camera BEFORE drawing: an in-frame assert proves every
  subject of the camera's declared framing_scope projects inside the
  viewport (nothing hidden or clipped - the card falsifier prong);
- makes the declared camera record mathematically true: right-handed
  camera frame (+X right, +Y up, -Z forward), quaternion w,x,y,z =
  camera-to-frame rotation; an independent reprojection oracle
  (project_from_record, decode from the serialized record only) must
  reproduce the drawn anchor pixel within 1 px (perspective
  camera-consistency gate);
- grounds every visibility claim in measured pixels: per-tile,
  per-frame exact-color signature counts and per-subject evidence are
  written to evidence/pixel_presence.json; make_capture refuses to build
  the manifest if any required subject lacks pixel evidence (M09 lesson:
  observed_subject_ids are measured, never asserted).

Sheet layout: 2 x 3 viewports of the declared 640x240 plus a shared
diagnostic footer band (gap/displacement trace inset). Clean viewports
carry geometry and title only - no labels, no overlays, no trace inset
(the footer is outside every viewport rect).

Run:  python -B render_run.py <attempt_capture_dir>
"""
from __future__ import annotations

import hashlib
import json
import math
import pathlib
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

CARD_ID = 'G02'
CARD_FULL = 'MAT2-G02'
TICK_MAP = ('one tick = 1/300 s (declared fixture tick); frames are the '
            'declared snapshot ticks at 1 video second per frame; the '
            'rendered state is bound to experiment_trace.json rows')
VIEWS = ['patch overview', 'loaded interface close-up',
         'orthogonal and oblique patch views']
LAYERS = ['attachment patch geometry', 'authored frames and port IDs',
          'fixture load and displacement traces']
LABELS = ['iface:fixture-patch-p1', 'iface:fixture-patch-p2',
          'fixture_body_a', 'fixture_body_b', 'port:patch', 'port:seam']
LABEL_PATCH = ['iface:fixture-patch-p1', 'iface:fixture-patch-p2',
               'port:patch', 'port:seam']

# ----------------------------------------------------------- layout + colors
VP_W, VP_H = 640, 240
FOOTER_H = 56
SHEET = (2 * VP_W, 3 * VP_H + FOOTER_H)
BG = (246, 246, 248)
TILE_RECTS = {}  # 'pair-N:<mode>' -> [x0, y0, x1, y1] (sheet px)
for _row in range(3):
    for _col, _mode in ((0, 'diagnostic'), (1, 'clean')):
        TILE_RECTS[f'pair-{_row}:{_mode}'] = [
            _col * VP_W, _row * VP_H, (_col + 1) * VP_W, (_row + 1) * VP_H]
FOOTER_RECT = [0, 3 * VP_H, SHEET[0], SHEET[1]]
INSET_RECT = [8, 3 * VP_H + 4, SHEET[0] - 8, SHEET[1] - 4]
# oblique secondary inset inside the pair-2 diagnostic viewport (tile px)
PIP_RECT = [344, 6, 632, 82]

BODY_A = (60, 90, 200)
BODY_B = (200, 120, 60)
STAND = (120, 120, 128)
PATCH_T1 = (210, 60, 60)
PATCH_T2 = (120, 60, 160)
PATCH_CLEAN = (150, 150, 150)
PATCH_OUTLINE = (20, 20, 20)
SEAM_DIAG = (250, 220, 80)
PATCH_DIAGONAL = (255, 160, 40)  # distinct from the seam dot: the seam
# color must stay unambiguous for the centroid consistency check
SEAM_CLEAN = (90, 90, 90)
TRIAD = ((220, 40, 40), (40, 180, 40), (40, 40, 220))
TRACE_LINE = (30, 160, 90)
TITLE_COLOR = (90, 90, 100)
LABEL_COLOR = (10, 10, 30)

SIG_GEOMETRY_DIAG = {
    'body_a': [BODY_A], 'body_b': [BODY_B], 'stand': [STAND],
    'patch': [PATCH_T1, PATCH_T2, PATCH_OUTLINE], 'seam': [SEAM_DIAG]}
SIG_GEOMETRY_CLEAN = {
    'body_a': [BODY_A], 'body_b': [BODY_B], 'stand': [STAND],
    'patch': [PATCH_CLEAN, PATCH_OUTLINE], 'seam': [SEAM_CLEAN]}


def sha(b):
    return hashlib.sha256(b).hexdigest()


def state_hash(row):
    payload = json.dumps(row, sort_keys=True, separators=(',', ':'),
                         allow_nan=False).encode('utf-8')
    return sha(payload)


# ------------------------------------------------------------------ camera
def mat_to_quat(m):
    """Rotation matrix (rows-major, standard convention) -> unit quaternion
    (w, x, y, z)."""
    tr = m[0][0] + m[1][1] + m[2][2]
    if tr > 0:
        s = math.sqrt(tr + 1.0) * 2
        w = 0.25 * s
        x = (m[2][1] - m[1][2]) / s
        y = (m[0][2] - m[2][0]) / s
        z = (m[1][0] - m[0][1]) / s
    elif m[0][0] > m[1][1] and m[0][0] > m[2][2]:
        s = math.sqrt(1.0 + m[0][0] - m[1][1] - m[2][2]) * 2
        w = (m[2][1] - m[1][2]) / s
        x = 0.25 * s
        y = (m[0][1] + m[1][0]) / s
        z = (m[0][2] + m[2][0]) / s
    elif m[1][1] > m[2][2]:
        s = math.sqrt(1.0 + m[1][1] - m[0][0] - m[2][2]) * 2
        w = (m[2][0] - m[0][2]) / s
        x = (m[0][1] + m[1][0]) / s
        y = 0.25 * s
        z = (m[1][2] + m[2][1]) / s
    else:
        s = math.sqrt(1.0 + m[2][2] - m[0][0] - m[1][1]) * 2
        w = (m[1][0] - m[0][1]) / s
        x = (m[0][2] + m[2][0]) / s
        y = (m[1][2] + m[2][1]) / s
        z = 0.25 * s
    return [w, x, y, z]


def quat_to_mat(q):
    """Unit quaternion (w, x, y, z) -> rotation matrix (standard rows)."""
    w, x, y, z = q
    return [[1 - 2 * (y * y + z * z), 2 * (x * y - w * z),
             2 * (x * z + w * y)],
            [2 * (x * y + w * z), 1 - 2 * (x * x + z * z),
             2 * (y * z - w * x)],
            [2 * (x * z - w * y), 2 * (y * z + w * x),
             1 - 2 * (x * x + y * y)]]


def _norm(v):
    l = math.sqrt(sum(x * x for x in v))
    return [x / l for x in v]


def _cross(a, b):
    return [a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0]]


def _dot(a, b):
    return sum(a[i] * b[i] for i in range(3))


class Camera:
    """Declared perspective camera with the full registry record.

    Right-handed camera frame: +X right, +Y up, -Z forward. The recorded
    quaternion is the camera-to-frame rotation R whose columns are the
    camera axes in fixture coordinates; v_cam = R^T (p - position) and the
    depth is -v_cam_z. Projection: xn = x_cam/(depth*tan(vfov/2)),
    px = (xn*0.5+0.5)*w, py = (1 - (yn*0.5+0.5))*h.
    """

    def __init__(self, name, position, target, vfov_deg=40.0,
                 near=0.005, far=5.0):
        self.name = name
        self.position = list(position)
        self.target = list(target)
        self.vfov = vfov_deg
        self.near = near
        self.far = far
        f = _norm([target[i] - position[i] for i in range(3)])
        up = [0.0, 0.0, 1.0]
        r = _norm(_cross(f, up))
        u = _cross(r, f)
        self.basis = (r, u, f)
        # columns (r, u, -f): camera-to-frame, right-handed, det = +1
        m = [[r[0], u[0], -f[0]], [r[1], u[1], -f[1]], [r[2], u[2], -f[2]]]
        self.quat = mat_to_quat(m)

    def project(self, p, vp_w, vp_h):
        d = [p[i] - self.position[i] for i in range(3)]
        zc = _dot(d, self.basis[2])
        if zc <= 1e-6:
            return None
        xc = _dot(d, self.basis[0])
        yc = _dot(d, self.basis[1])
        t = math.tan(math.radians(self.vfov) / 2.0)
        xn = xc / (zc * t)
        yn = yc / (zc * t)
        return (int((xn * 0.5 + 0.5) * vp_w),
                int((1.0 - (yn * 0.5 + 0.5)) * vp_h))

    def record(self, snap_ticks, layers, labels, framing_scope,
               rendered_rect, render_mode):
        """Full registry camera record + the validator-required sample
        structure; fixed bookmark (all samples share pose)."""
        dist = math.sqrt(sum((self.position[i] - self.target[i]) ** 2
                             for i in range(3)))
        sample = lambda tick: {
            'tick': tick,
            'position': list(self.position),
            'target': list(self.target),
            'distance_to_target': dist,
            'orientation': list(self.quat),
        }
        return {
            'frame_id': 'g02_' + self.name,
            'coordinate_unit': 'm',
            'handedness': 'right',
            'orientation_convention': 'quaternion_wxyz_camera_to_frame',
            'forward_axis': '-Z',
            'up_axis': '+Y',
            'near_far_planes': [self.near, self.far],
            'viewport_resolution': [rendered_rect[2] - rendered_rect[0],
                                    rendered_rect[3] - rendered_rect[1]],
            'aspect_ratio': ((rendered_rect[2] - rendered_rect[0])
                             / (rendered_rect[3] - rendered_rect[1])),
            'projection': 'perspective',
            'vertical_fov_degrees': self.vfov,
            'sample_mode': 'fixed_bookmark',
            'samples': [sample(t) for t in snap_ticks],
            'position': list(self.position),
            'target': list(self.target),
            'distance_to_target': dist,
            'orientation_convention_and_values': {
                'convention':
                    'unit quaternion w,x,y,z of the camera-to-frame '
                    'rotation R; columns of R are the camera +X right, '
                    '+Y up, -Z backward axes in fixture coordinates '
                    '(right-handed, world up hint +Z); v_cam = R^T '
                    '(p - position); depth = -v_cam_z; xn = x_cam/'
                    '(depth*tan(vfov/2)); px = (xn*0.5+0.5)*w; '
                    'py = (1-(yn*0.5+0.5))*h',
                'quaternion_wxyz': list(self.quat)},
            'vertical_fov_or_orthographic_span': self.vfov,
            'camera_motion_or_bookmark_sequence':
                'fixed bookmark; no motion across frames',
            'visibility_layers': list(layers),
            'label_ids': list(labels),
            'occlusion_or_xray_mode': 'depth_tested',
            'state_or_tick_interval': [snap_ticks[0], snap_ticks[-1]],
            'framing_scope': framing_scope,
            'render_mode': render_mode,
            'rendered_rect_px': list(rendered_rect),
        }


def project_from_record(rec, p, vp_w, vp_h):
    """INDEPENDENT reprojection oracle: uses ONLY the serialized camera
    record (position + quaternion + fov), never the Camera object. Returns
    float pixel coordinates or None when the point is behind the camera."""
    q = rec['orientation_convention_and_values']['quaternion_wxyz']
    m = quat_to_mat(q)
    r = [m[0][0], m[1][0], m[2][0]]
    u = [m[0][1], m[1][1], m[2][1]]
    back = [m[0][2], m[1][2], m[2][2]]
    d = [p[i] - rec['position'][i] for i in range(3)]
    zc = _dot(d, back)
    if zc >= -1e-6:
        return None
    depth = -zc
    t = math.tan(math.radians(rec['vertical_fov_or_orthographic_span'])
                 / 2.0)
    xn = _dot(d, r) / (depth * t)
    yn = _dot(d, u) / (depth * t)
    return ((xn * 0.5 + 0.5) * vp_w, (1.0 - (yn * 0.5 + 0.5)) * vp_h)


# ------------------------------------------------------- fixture geometry
BODY_EDGES = [(0, 1), (1, 2), (2, 3), (3, 0), (0, 4), (1, 4), (2, 4),
              (3, 4)]
PATCH_QUAD_YZ = [(0.0, 0.0), (0.020, 0.0), (0.013, 0.010), (0.0, 0.010)]
SEAM_LOCAL = (0.0087, 0.0048)


def fixture_points(gap):
    """Every declared subject point of the fixture at this tick's gap."""
    verts_a = [(0.0, 0.0, 0.0), (0.0, 0.2, 0.0), (0.0, 0.15, 0.1),
               (0.0, 0.0, 0.1),
               (-0.16, 0.08809523809523807, 0.04761904761904761)]
    verts_b = [(gap + v[0], v[1], v[2]) for v in
               [(0.0, 0.0, 0.0), (0.0, 0.2, 0.0), (0.0, 0.15, 0.1),
                (0.0, 0.0, 0.1),
                (0.16, 0.08809523809523807, 0.04761904761904761)]]
    stand = [(-0.16, 0.0, -0.02), (0.0, 0.0, -0.02), (0.0, 0.0, 0.0),
             (-0.16, 0.0, 0.0)]
    quad = [(gap, y, z) for (y, z) in PATCH_QUAD_YZ]
    seam = (gap, SEAM_LOCAL[0], SEAM_LOCAL[1])
    return {'verts_a': verts_a, 'verts_b': verts_b, 'stand': stand,
            'quad': quad, 'seam': seam}


def label_anchor(label, gap, pts):
    if label == 'iface:fixture-patch-p1':
        return pts['quad'][0]
    if label == 'iface:fixture-patch-p2':
        return pts['quad'][1]
    if label == 'fixture_body_a':
        return pts['verts_a'][4]
    if label == 'fixture_body_b':
        return pts['verts_b'][4]
    if label == 'port:patch':
        ys = [q[1] for q in pts['quad']]
        zs = [q[2] for q in pts['quad']]
        return (pts['quad'][0][0], sum(ys) / 4.0, sum(zs) / 4.0)
    if label == 'port:seam':
        return pts['seam']
    raise SystemExit(f'unknown label id: {label}')


def cameras_for(_=None):
    return [
        (VIEWS[0],
         Camera('patch_overview', (-0.50, -0.39, 0.33),
                (0.046, 0.1, 0.04), vfov_deg=40.0), None),
        (VIEWS[1],
         Camera('loaded_interface_closeup', (0.048, -0.22, 0.09),
                (0.048, 0.0087, 0.0048), vfov_deg=26.0), None),
        (VIEWS[2],
         Camera('orthogonal_patch', (-0.24, 0.01, 0.005),
                (0.04, 0.01, 0.005), vfov_deg=14.0),
         Camera('oblique_patch', (0.45, -0.28, 0.22),
                (0.05, 0.1, 0.04), vfov_deg=52.0)),
    ]


# ----------------------------------------------------------------- gates
def assert_in_frame(cam, points_by_name, margin=4):
    """In-frame gate: every subject point of the camera's declared framing
    scope must project inside the viewport with margin and sit inside the
    clip planes - 'nothing hidden or clipped' becomes a checked
    precondition, not prose."""
    bad = []
    for name, p in points_by_name.items():
        pr = cam.project(p, VP_W, VP_H)
        d = [p[i] - cam.position[i] for i in range(3)]
        depth = _dot(d, cam.basis[2])
        if (pr is None or not (margin <= pr[0] <= VP_W - 1 - margin)
                or not (margin <= pr[1] <= VP_H - 1 - margin)
                or not (cam.near < depth < cam.far)):
            bad.append((name, p, pr, round(depth, 4)))
    if bad:
        raise SystemExit(f'geometry_out_of_frame:{cam.name}: {bad[:4]}')


def scope_points(cam_scope, pts, gap):
    if cam_scope == 'whole_fixture':
        flat = {}
        for group in ('verts_a', 'verts_b', 'stand', 'quad'):
            for i, p in enumerate(pts[group]):
                flat[f'{group}[{i}]'] = p
        flat['seam'] = pts['seam']
        return flat
    if cam_scope == 'patch_interface':
        flat = {f'quad[{i}]': p for i, p in enumerate(pts['quad'])}
        flat['seam'] = pts['seam']
        return flat
    raise SystemExit(f'unknown framing scope: {cam_scope}')


# ----------------------------------------------------------------- render
def draw_viewport(draw, cam, row, diagnostic):
    """The geometry renderer: support stand, both bodies (wireframe + apex
    marker), the patch quad (diagnostic: the two declared triangles in
    distinct colors + seam diagonal; clean: neutral gray) and the seam
    dot; diagnostic adds the axis triad at the seam. Every call site is
    in this file's tile loop (round-1 fix: it previously had NONE)."""
    gap = row['gap_m']
    pts = fixture_points(gap)
    for a, b in ((pts['stand'][0], pts['stand'][1]),
                 (pts['stand'][1], pts['stand'][2]),
                 (pts['stand'][2], pts['stand'][3]),
                 (pts['stand'][3], pts['stand'][0])):
        pa, pb = cam.project(a, VP_W, VP_H), cam.project(b, VP_W, VP_H)
        if pa and pb:
            draw.line([pa, pb], fill=STAND, width=2)
    for verts, color in ((pts['verts_a'], BODY_A),
                         (pts['verts_b'], BODY_B)):
        for a, b in BODY_EDGES:
            pa, pb = (cam.project(verts[a], VP_W, VP_H),
                      cam.project(verts[b], VP_W, VP_H))
            if pa and pb:
                draw.line([pa, pb], fill=color, width=2)
        pa = cam.project(verts[4], VP_W, VP_H)
        if pa:
            draw.ellipse([pa[0] - 2, pa[1] - 2, pa[0] + 2, pa[1] + 2],
                         fill=color)
    quad = pts['quad']
    pts2 = [cam.project(p, VP_W, VP_H) for p in quad]
    if all(pts2):
        if diagnostic:
            draw.polygon([pts2[0], pts2[1], pts2[2]], fill=PATCH_T1)
            draw.polygon([pts2[0], pts2[2], pts2[3]], fill=PATCH_T2)
            draw.line([pts2[0], pts2[2]], fill=PATCH_DIAGONAL, width=1)
        else:
            draw.polygon(pts2, fill=PATCH_CLEAN)
        draw.line(pts2 + [pts2[0]], fill=PATCH_OUTLINE, width=1)
    c = cam.project(pts['seam'], VP_W, VP_H)
    if c:
        draw.ellipse([c[0] - 3, c[1] - 3, c[0] + 3, c[1] + 3],
                     fill=SEAM_DIAG if diagnostic else SEAM_CLEAN)
    if diagnostic:
        o = cam.project(pts['seam'], VP_W, VP_H)
        for vec, col in (((0.02, 0, 0), TRIAD[0]), ((0, 0.02, 0), TRIAD[1]),
                         ((0, 0, 0.02), TRIAD[2])):
            e = cam.project((pts['seam'][0] + vec[0],
                             pts['seam'][1] + vec[1],
                             pts['seam'][2] + vec[2]), VP_W, VP_H)
            if o and e:
                draw.line([o, e], fill=col, width=2)


def draw_title(draw, view_id, mode, tick):
    # exact-color marker chip (FreeType text antialiases; the chip is the
    # measurable exact-color evidence of the title band)
    draw.rectangle([4, 4, 7, 26], fill=TITLE_COLOR)
    draw.text((10, 4), view_id, fill=TITLE_COLOR)
    draw.text((10, 16), f'{mode} | tick {tick}', fill=TITLE_COLOR)


def draw_labels(draw, cam, pts, labels):
    """Port-ID labels at their subjects' projected anchors; placement is
    collision-avoiding and gate-checked (bbox in frame, no overlap). Each
    label carries a 3 px exact-color marker chip at its bbox left edge
    (FreeType text antialiases; the chip is the measurable evidence)."""
    placed = []
    out = {}
    for label in labels:
        anchor = label_anchor(label, 0.0, pts)
        pr = cam.project(anchor, VP_W, VP_H)
        if pr is None:
            raise SystemExit(f'label_anchor_out_of_frame:{cam.name}:'
                             f'{label}')
        text = label
        tw = draw.textlength(text)
        th = 11
        cands = [(pr[0] + 6, pr[1] - 6 - th), (pr[0] + 6, pr[1] + 6),
                 (pr[0] - 6 - tw, pr[1] - 6 - th),
                 (pr[0] - 6 - tw, pr[1] + 6),
                 (pr[0] + 6, pr[1] - 20 - th), (pr[0] + 6, pr[1] + 20),
                 (pr[0] - 6 - tw, pr[1] - 20 - th),
                 (pr[0] - 6 - tw, pr[1] + 20)]
        chosen = None
        for (tx, ty) in cands:
            bb = [int(tx), int(ty), int(tx) + int(tw) + 6,
                  int(ty) + th + 1]
            if not (2 <= bb[0] and bb[2] <= VP_W - 2
                    and 2 <= bb[1] and bb[3] <= VP_H - 2):
                continue
            if any(not (bb[2] < o[0] or bb[0] > o[2]
                        or bb[3] < o[1] or bb[1] > o[3]) for o in placed):
                continue
            chosen = bb
            break
        if chosen is None:
            raise SystemExit(f'label_placement_failed:{cam.name}:{label}')
        placed.append(chosen)
        draw.rectangle([chosen[0], chosen[1], chosen[0] + 2, chosen[3]],
                       fill=LABEL_COLOR)
        draw.text((chosen[0] + 5, chosen[1]), text, fill=LABEL_COLOR)
        out[label] = {'bbox_px': chosen, 'anchor_px': [pr[0], pr[1]]}
    return out


def draw_trace_inset(draw, snap_rows, tick):
    x0, y0, x1, y1 = INSET_RECT
    gaps = [(r['tick'], r['gap_m']) for r in snap_rows]
    gmax = max(g for _, g in gaps)
    gmin = min(g for _, g in gaps)
    span = (gmax - gmin) or 1.0
    draw.rectangle([x0, y0, x1, y1], outline=(160, 160, 160))
    prev = None
    for tk, g in gaps:
        px = x0 + int((x1 - x0) * tk / max(1, gaps[-1][0]))
        py = y1 - int((y1 - y0 - 2) * (g - gmin) / span) - 1
        if prev:
            draw.line([prev, (px, py)], fill=TRACE_LINE)
        prev = (px, py)
    here = dict(gaps).get(tick, 0.0)
    draw.text((x0 + 4, y0 + 2),
              f'gap trace m; tick {tick} gap {here:.6f}', fill=(20, 20, 20))
    mx = x0 + int((x1 - x0) * tick / max(1, gaps[-1][0]))
    draw.line([(mx, y0 + 14), (mx, y1 - 1)], fill=(160, 160, 160))


# ----------------------------------------------------------- measurement
def _mask(arr, colors):
    m = np.zeros(arr.shape[:2], dtype=bool)
    for c in colors:
        m |= np.all(arr == np.array(c, dtype=np.uint8), axis=-1)
    return m


def _count_near(mask, xy, radius):
    x, y = int(round(xy[0])), int(round(xy[1]))
    x0, x1 = max(0, x - radius), min(mask.shape[1], x + radius + 1)
    y0, y1 = max(0, y - radius), min(mask.shape[0], y + radius + 1)
    return int(mask[y0:y1, x0:x1].sum())


def measure_tile(arr, sigs, label_bboxes, triad_expected, label_expected):
    stats = {
        'nonbg_pixels': int(np.any(arr != np.array(BG, dtype=np.uint8),
                                   axis=-1).sum()),
        'unique_colors': int(len(np.unique(arr.reshape(-1, 3), axis=0))),
        'signatures': {k: int(_mask(arr, v).sum())
                       for k, v in sigs.items()},
        'title_pixels': int(_mask(arr, [TITLE_COLOR]).sum()),
    }
    if triad_expected:
        stats['triad_pixels'] = int(_mask(arr, list(TRIAD)).sum())
    else:
        stats['triad_pixels'] = 0
    label_px = {}
    lm = _mask(arr, [LABEL_COLOR])
    for label, info in (label_bboxes or {}).items():
        x0, y0, x1, y1 = info['bbox_px']
        label_px[label] = int(lm[y0:y1 + 1, x0:x1 + 1].sum())
    stats['label_bbox_pixels'] = label_px
    stats['label_pixels_total'] = int(lm.sum())
    stats['label_expected'] = bool(label_expected)
    return stats


def ground_subjects(arr, sigs, cam_rec, pts, gap, labels, diagnostic):
    """Per-subject pixel evidence: point subjects need signature pixels
    within a radius of the oracle-predicted anchor; area subjects need
    their color signature anywhere in the tile; diagnostic labels need
    text pixels."""
    patch_colors = sigs['patch']
    seam_colors = sigs['seam']
    pmask = _mask(arr, patch_colors)
    smask = _mask(arr, seam_colors)
    subjects = {}
    for label in LABELS:
        anchor_w = label_anchor(label, gap, pts)
        pred = project_from_record(cam_rec, anchor_w, VP_W, VP_H)
        if label == 'fixture_body_a':
            ev = {'geometry_pixels': stats_body(arr, BODY_A),
                  'method': 'area_signature'}
        elif label == 'fixture_body_b':
            ev = {'geometry_pixels': stats_body(arr, BODY_B),
                  'method': 'area_signature'}
        elif label == 'port:patch':
            n = (_count_near(pmask, pred, 8) if pred else 0)
            ev = {'geometry_pixels': n,
                  'predicted_px': pred and [round(pred[0], 1),
                                            round(pred[1], 1)],
                  'method': 'point_radius_patch'}
        elif label == 'port:seam':
            n = (_count_near(smask, pred, 6) if pred else 0)
            ev = {'geometry_pixels': n,
                  'predicted_px': pred and [round(pred[0], 1),
                                            round(pred[1], 1)],
                  'method': 'point_radius_seam'}
        else:  # interface points p1/p2 live on the patch quad
            n = (_count_near(pmask, pred, 8) if pred else 0)
            ev = {'geometry_pixels': n,
                  'predicted_px': pred and [round(pred[0], 1),
                                            round(pred[1], 1)],
                  'method': 'point_radius_patch'}
        present_geom = ev['geometry_pixels'] > 0
        present = present_geom
        if diagnostic and label in labels:
            present = present_geom  # label text checked via bbox pixels
        ev['present'] = bool(present)
        subjects[label] = ev
    return subjects


def stats_body(arr, color):
    return int(_mask(arr, [color]).sum())


# ------------------------------------------------------------------ main
def main():
    capture_dir = pathlib.Path(sys.argv[1])
    frames_dir = capture_dir / 'frames'
    evidence_dir = capture_dir / 'evidence'
    frames_dir.mkdir(parents=True, exist_ok=True)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    trace = json.loads((HERE / 'experiment_trace.json')
                       .read_bytes().decode('utf-8'))
    rows = trace['rows']
    snap_rows = [r for r in rows if r.get('snap')]
    assert [r['tick'] for r in snap_rows] == [0, 20, 150, 232, 233, 250,
                                              320], 'capture ticks drifted'
    snap_ticks = [r['tick'] for r in snap_rows]

    cams = cameras_for()
    labels_by_view = {
        VIEWS[0]: list(LABELS),
        VIEWS[1]: list(LABEL_PATCH),
        VIEWS[2]: list(LABEL_PATCH),
    }
    scope_by_cam = {'patch_overview': 'whole_fixture',
                    'loaded_interface_closeup': 'patch_interface',
                    'orthogonal_patch': 'patch_interface',
                    'oblique_patch': 'whole_fixture'}
    rects_by_cam = {'patch_overview': [0, 0, VP_W, VP_H],
                    'loaded_interface_closeup': [0, 0, VP_W, VP_H],
                    'orthogonal_patch': [0, 0, VP_W, VP_H],
                    'oblique_patch': list(PIP_RECT)}

    cams_out = {}
    rec_by_tile = {}
    required_by_tile = {}
    for vi, (view_id, cam, secondary) in enumerate(cams):
        labels = labels_by_view[view_id]
        base = cam.record(snap_ticks, LAYERS, labels,
                          scope_by_cam[cam.name], rects_by_cam[cam.name],
                          'primary_viewport')
        entry = [base]
        if secondary is not None:
            entry.append(secondary.record(
                snap_ticks, ['attachment patch geometry'], [],
                scope_by_cam[secondary.name],
                rects_by_cam[secondary.name],
                'picture_in_picture_inset'))
        cams_out[f'{view_id}:diagnostic'] = entry
        cams_out[f'{view_id}:clean'] = [base]
        rec_by_tile[f'pair-{vi}:diagnostic'] = base
        rec_by_tile[f'pair-{vi}:clean'] = base
        req = list(LABELS) if vi == 0 else \
            list(LABEL_PATCH) + (['fixture_body_a', 'fixture_body_b']
                                 if secondary is not None else [])
        required_by_tile[f'pair-{vi}:diagnostic'] = req
        required_by_tile[f'pair-{vi}:clean'] = \
            list(LABELS) if vi == 0 else list(LABEL_PATCH)

    frame_hashes = []
    state_hashes = {}
    presence_frames = {k: [] for k in TILE_RECTS}
    consistency = []
    for idx, row in enumerate(snap_rows):
        tick = row['tick']
        h = state_hash({k: row[k] for k in (
            'tick', 'gap_m', 'penetration_m', 'velocity_m_per_s',
            'patch_energy_J', 'triangle_connections', 'vertices_b_m')})
        state_hashes[str(tick)] = h
        sheet = Image.new('RGB', SHEET, BG)
        gap = row['gap_m']
        pts = fixture_points(gap)
        for vi, (view_id, cam, secondary) in enumerate(cams):
            for mode in ('diagnostic', 'clean'):
                diagnostic = mode == 'diagnostic'
                tile_key = f'pair-{vi}:{mode}'
                # ---- in-frame gate BEFORE any pixel is written
                assert_in_frame(cam, scope_points(
                    scope_by_cam[cam.name], pts, gap))
                if diagnostic and secondary is not None:
                    assert_in_frame(secondary, scope_points(
                        scope_by_cam[secondary.name], pts, gap))
                # ---- render the viewport (draw_viewport CALL SITE)
                tile = Image.new('RGB', (VP_W, VP_H), BG)
                tdraw = ImageDraw.Draw(tile)
                draw_viewport(tdraw, cam, row, diagnostic)
                draw_title(tdraw, view_id, mode, tick)
                label_bboxes = {}
                if diagnostic:
                    label_bboxes = draw_labels(tdraw, cam, pts,
                                               labels_by_view[view_id])
                # ---- camera-consistency gate (reprojection oracle)
                rec = json.loads(json.dumps(rec_by_tile[tile_key]))
                pred = project_from_record(rec, pts['seam'], VP_W, VP_H)
                drawn = cam.project(pts['seam'], VP_W, VP_H)
                delta = max(abs(pred[0] - drawn[0]),
                            abs(pred[1] - drawn[1]))
                if delta > 1.0:  # int() truncation bound per axis
                    raise SystemExit(
                        f'camera_consistency_failed:{tile_key}: '
                        f'predicted {pred} drawn {drawn} delta {delta}')
                consistency.append({'tile': tile_key, 'tick': tick,
                                    'predicted_px': [round(pred[0], 2),
                                                     round(pred[1], 2)],
                                    'drawn_px': list(drawn),
                                    'delta_px': round(delta, 3)})
                arr = np.asarray(tile, dtype=np.uint8)
                sigs = SIG_GEOMETRY_DIAG if diagnostic else \
                    SIG_GEOMETRY_CLEAN
                stats = measure_tile(arr, sigs, label_bboxes,
                                     diagnostic, diagnostic)
                stats['label_bboxes'] = label_bboxes
                # ---- subject grounding from the rendered pixels
                subs = ground_subjects(arr, sigs, rec, pts, gap,
                                       labels_by_view[view_id],
                                       diagnostic)
                missing = [s for s in required_by_tile[tile_key]
                           if not subs[s]['present']]
                if diagnostic:
                    for lab, n in stats['label_bbox_pixels'].items():
                        if n <= 0:
                            missing.append(f'label_text:{lab}')
                    if stats['triad_pixels'] <= 0:
                        missing.append('overlay:axis_triad')
                else:
                    if stats['label_pixels_total'] != 0:
                        missing.append('clean_row_has_label_pixels')
                    if stats['triad_pixels'] != 0:
                        missing.append('clean_row_has_triad_pixels')
                stats['subjects'] = subs
                stats['missing'] = missing
                stats['required'] = required_by_tile[tile_key]
                presence_frames[tile_key].append(
                    {'tick': tick, **{k: v for k, v in stats.items()
                                      if k != 'label_bboxes'},
                     **{'label_bboxes': label_bboxes}})
                if missing:
                    raise SystemExit(f'subject_pixels_missing:'
                                     f'{tile_key}: tick {tick}: {missing}')
                # ---- diagnostic-only oblique inset (pair 2)
                if diagnostic and secondary is not None:
                    for name, p in scope_points(scope_by_cam[cam.name],
                                                pts, gap).items():
                        pr = cam.project(p, VP_W, VP_H)
                        if pr and (PIP_RECT[0] <= pr[0] <= PIP_RECT[2]
                                   and PIP_RECT[1] <= pr[1]
                                   <= PIP_RECT[3]):
                            raise SystemExit(
                                f'pip_hides_geometry:{tile_key}:{name}: '
                                f'{pr} vs {PIP_RECT}')
                    for lab, info in label_bboxes.items():
                        bb = info['bbox_px']
                        if not (bb[2] < PIP_RECT[0] or bb[0] > PIP_RECT[2]
                                or bb[3] < PIP_RECT[1]
                                or bb[1] > PIP_RECT[3]):
                            raise SystemExit(
                                f'pip_hides_label:{tile_key}:{lab}: '
                                f'{bb} vs {PIP_RECT}')
                    pip = Image.new('RGB', (PIP_RECT[2] - PIP_RECT[0],
                                            PIP_RECT[3] - PIP_RECT[1]), BG)
                    pdraw = ImageDraw.Draw(pip)
                    draw_viewport(pdraw, secondary, row, False)
                    pdraw.text((4, 4), 'oblique secondary',
                               fill=TITLE_COLOR)
                    tile.paste(pip, (PIP_RECT[0], PIP_RECT[1]))
                    parr = np.asarray(tile, dtype=np.uint8)[
                        PIP_RECT[1]:PIP_RECT[3], PIP_RECT[0]:PIP_RECT[2]]
                    pstats = measure_tile(parr, SIG_GEOMETRY_CLEAN, None,
                                          False, False)
                    if pstats['nonbg_pixels'] <= 100:
                        raise SystemExit(
                            f'subject_pixels_missing:{tile_key}:pip: '
                            f'tick {tick}')
                    badpx = int(_mask(parr, [LABEL_COLOR, TRIAD[0],
                                             TRIAD[1], TRIAD[2]]
                                      + [PATCH_T1, PATCH_T2]).sum())
                    if badpx != 0:
                        raise SystemExit(
                            f'pip_contains_diagnostic_styling:'
                            f'{tile_key}: tick {tick}: {badpx}')
                    presence_frames[tile_key][-1]['pip_nonbg_pixels'] = \
                        pstats['nonbg_pixels']
                sheet.paste(tile, (TILE_RECTS[tile_key][0],
                                   TILE_RECTS[tile_key][1]))
        draw_trace_inset(ImageDraw.Draw(sheet), snap_rows, tick)
        farr = np.asarray(sheet.crop(FOOTER_RECT), dtype=np.uint8)
        footer = {'tick': tick,
                  'trace_line_pixels': int(_mask(farr, [TRACE_LINE]).sum()),
                  'nonbg_pixels': int(np.any(
                      farr != np.array(BG, dtype=np.uint8),
                      axis=-1).sum())}
        if footer['trace_line_pixels'] <= 20:
            raise SystemExit(f'subject_pixels_missing:footer: '
                             f'tick {tick}: trace inset empty')
        frame_path = frames_dir / f'frame_{idx:02d}.png'
        sheet.save(frame_path, format='PNG')
        frame_hashes.append({'frame': frame_path.name, 'tick': tick,
                             'sha256': sha(frame_path.read_bytes()),
                             'footer': footer})
        print(f'frame {idx} tick {tick}: tiles '
              + ' '.join(f"{k}={presence_frames[k][-1]['nonbg_pixels']}"
                         for k in sorted(presence_frames))
              + f' footer={footer["nonbg_pixels"]}')

    presence = {
        'law': 'per-tile, per-frame measured pixel evidence; subject '
               'presence grounded in exact-color signatures and '
               'oracle-predicted point hits inside the declared viewport '
               'rects (observed_subject_ids are MEASURED, never asserted)',
        'signature_colors': {
            'body_a': [list(BODY_A)], 'body_b': [list(BODY_B)],
            'stand': [list(STAND)],
            'patch_diagnostic': [list(PATCH_T1), list(PATCH_T2),
                                 list(PATCH_OUTLINE)],
            'patch_diagonal': [list(PATCH_DIAGONAL)],
            'patch_clean': [list(PATCH_CLEAN), list(PATCH_OUTLINE)],
            'seam_diagnostic': [list(SEAM_DIAG)],
            'seam_clean': [list(SEAM_CLEAN)],
            'title': [list(TITLE_COLOR)], 'label': [list(LABEL_COLOR)],
            'trace_line': [list(TRACE_LINE)],
            'triad': [list(c) for c in TRIAD]},
        'tile_rects': {k: list(v) for k, v in TILE_RECTS.items()},
        'footer_rect': list(FOOTER_RECT),
        'pip_rect_tile_px': list(PIP_RECT),
        'required_subjects': required_by_tile,
        'frames': frame_hashes,
        'per_tile_frames': presence_frames,
        'camera_consistency': consistency,
        'all_present': True,
    }
    (evidence_dir / 'cameras.json').write_bytes(
        json.dumps({k: list(v) for k, v in cams_out.items()},
                   indent=1, sort_keys=True).encode('utf-8'))
    (evidence_dir / 'frame_hashes.json').write_bytes(
        json.dumps(frame_hashes, indent=1, sort_keys=True).encode('utf-8'))
    (evidence_dir / 'state_hashes.json').write_bytes(
        json.dumps({'law': 'composite physical state hash per snapshot '
                    'tick; identical for diagnostic and clean rows of the '
                    'same tick (view toggles preserve the physical state '
                    'hash)',
                    'hashes': state_hashes,
                    'preserved_across_view_toggles': True},
                   indent=1, sort_keys=True).encode('utf-8'))
    (evidence_dir / 'pixel_presence.json').write_bytes(
        json.dumps(presence, indent=1, sort_keys=True).encode('utf-8'))
    print('frames:', len(frame_hashes), 'cameras:', len(cams_out),
          'tiles:', len(TILE_RECTS))
    print('pixel presence: all required subjects grounded in every frame')
    print('camera consistency: max delta px =',
          max(c['delta_px'] for c in consistency))


if __name__ == '__main__':
    main()
