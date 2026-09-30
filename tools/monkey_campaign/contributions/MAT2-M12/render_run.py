"""MAT2-M12 renderer: software rasterization of solver snapshots at BOTH
declared resolutions (the render pass is OFFLINE over recorded states and
receives COPIES; the mechanical state can never be written back -- the
independence law, prereg section 1).

Frame plan (prereg section 8): SNAP_TICKS x {coarse, reference} x
{diagnostic, clean} = 24 frames, ONE video. Frame index =
si*4 + res_i*2 + mode_offset. View toggles never change the physical state
hash: every frame of a (resolution, tick) pair renders the SAME snapshot
and the binding assertions against the trace rows run BEFORE any pixel.
"""
from __future__ import annotations

import hashlib
import json
import math
import pathlib
import struct
import sys

import numpy as np
from PIL import Image, ImageDraw

import m12_lod as ml  # noqa: E402
import limb_world as lw  # noqa: E402

HERE = ml.HERE
TRACE_PATH = HERE / 'experiment_trace.json'

W_SHEET, H_SHEET = 960, 540
VP_W, VP_H = 476, 260
VIEW_IDS = ['whole experiment at fixed distance',
            'orthogonal side and front',
            'oblique close-up of the loaded interface']
LAYERS = ['stable membrane/triangle/port IDs',
          'pressure and area-scaled force vectors',
          'rest/current geometry and material directions',
          'contact/bond state',
          'energy/work and simulation tick']
NEAR_FAR = [0.005, 50.0]
RES_IDS = ('coarse', 'reference')
SUBJECTS = ['tissue_bladder', 'clamp_ring', 'humerus', 'ulna', 'radius',
            'foot', 'load_surrogate', 'source_m11_source']
LABELS = ['tissue_bladder', 'clamp_ring (visible support)',
          'chain T1 humerus', 'chain T2 ulna', 'chain T3 radius',
          'chain T4 foot(hand)', 'bond:load_surrogate',
          'source_m11_source']
CLAMP_RGB = (255, 70, 70)
LOAD_RGB = (60, 60, 225)
POLE_RGB = (255, 200, 60)
CONTACT_RGB = (0, 220, 120)
TIE_RGB = (0, 170, 255)
CHORD_RGB = (255, 140, 0)
PRESSURE_RGB = (220, 30, 30)
TICK_MAP = ('1 tick = 1/300 s simulated; frames are the declared snapshot '
            'ticks 0,450,460,700,1100,1350 x {coarse, reference} '
            '(frame = si*4 + res*2 + mode: diagnostic even-within-pair, '
            'clean odd); 1 video second per frame')
CLOSEUP_TARGET = (0.0, 0.0, 0.035)
_CLOSEUP_DIR = (0.10, -0.14, 0.045)
_CLOSEUP_DIR_NORM = 0.1791616856312864
CLOSEUP_DIST = 0.24
CLOSEUP_POSITION = tuple(
    CLOSEUP_TARGET[i] + CLOSEUP_DIST *
    (_CLOSEUP_DIR[i] / _CLOSEUP_DIR_NORM) for i in range(3))
BOOKMARKS = (
    ('whole', dict(position=(0.32, -0.44, 0.30), target=(0.0, 0.0, 0.19),
                   projection='perspective', fov_degrees=40)),
    ('side', dict(position=(0.0, 0.62, 0.19), target=(0.0, 0.0, 0.19),
                  projection='orthographic', span=0.46)),
    ('front', dict(position=(0.62, 0.0, 0.19), target=(0.0, 0.0, 0.19),
                   projection='orthographic', span=0.46)),
    ('closeup', dict(position=CLOSEUP_POSITION, target=CLOSEUP_TARGET,
                     projection='perspective', fov_degrees=30)))
ORIGINS = [(4, 4), (484, 4), (4, 268), (484, 268)]
NAMES = ['whole', 'side', 'front', 'close-up']
VP_RECTS = {'whole': (4, 4, 479, 263), 'side': (484, 4, 959, 263),
            'front': (4, 268, 479, 527), 'closeup': (484, 268, 959, 527)}
STILL_INDICES = (0, 2, 10, 20)   # coarse rest, ref rest, coarse release
# transient (tick 460), coarse settled (tick 1350) -- all diagnostic
GROUND_SPAN = 0.14


def require(condition, code):
    if not condition:
        raise ValueError(code)


class Camera:
    def __init__(self, name, position, target, projection, fov_degrees=None,
                 span=None):
        self.name = name
        self.position = np.array(position, dtype=np.float64)
        self.target = np.array(target, dtype=np.float64)
        self.projection = projection
        self.fov = fov_degrees
        self.span = span
        f = self.target - self.position
        self.dist = float(np.linalg.norm(f))
        self.forward = f / self.dist
        w = np.array([0.0, 0.0, 1.0])
        r = np.cross(self.forward, w)
        if np.linalg.norm(r) < 1e-9:
            r = np.array([0.0, 1.0, 0.0])
        r = r / np.linalg.norm(r)
        up = np.cross(r, self.forward)
        self.right, self.up = r, up

    def project(self, points, vp_w, vp_h):
        pts = np.atleast_2d(np.asarray(points, dtype=np.float64))
        rel = pts - self.position
        x = rel @ self.right
        y = rel @ self.up
        z = rel @ self.forward
        if self.projection == 'perspective':
            t = math.tan(math.radians(self.fov) / 2.0)
            aspect = vp_w / vp_h
            depth = z
            px = vp_w / 2.0 + (x / (z * t * aspect)) * (vp_w / 2.0)
            py = vp_h / 2.0 - (y / (z * t)) * (vp_h / 2.0)
        else:
            depth = z
            scale = vp_h / self.span
            px = vp_w / 2.0 + x * scale
            py = vp_h / 2.0 - y * scale
        return np.column_stack([px, py]), depth

    def quat(self):
        """wxyz quaternion of the camera-to-frame rotation (columns
        right, up, -forward; forward -Z / up +Y convention). Verbatim
        M11 form (the sealed renderer's proven conversion)."""
        m = np.column_stack([self.right, self.up, -self.forward])
        tr = m[0, 0] + m[1, 1] + m[2, 2]
        if tr > 0:
            sq = math.sqrt(tr + 1.0) * 2
            w = 0.25 * sq
            x = (m[2, 1] - m[1, 2]) / sq
            y = (m[0, 2] - m[2, 0]) / sq
            z = (m[1, 0] - m[0, 1]) / sq
        elif m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
            sq = math.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2]) * 2
            w = (m[2, 1] - m[1, 2]) / sq
            x = 0.25 * sq
            y = (m[0, 1] + m[1, 0]) / sq
            z = (m[0, 2] + m[2, 0]) / sq
        elif m[1, 1] > m[2, 2]:
            sq = math.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2]) * 2
            w = (m[0, 2] - m[2, 0]) / sq
            x = (m[0, 1] + m[1, 0]) / sq
            y = 0.25 * sq
            z = (m[1, 2] + m[2, 1]) / sq
        else:
            sq = math.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1]) * 2
            w = (m[1, 0] - m[0, 1]) / sq
            x = (m[0, 2] + m[2, 0]) / sq
            y = (m[1, 2] + m[2, 1]) / sq
            z = 0.25 * sq
        return [float(w), float(x), float(y), float(z)]

    def record(self, res, snap_ticks):
        samples = []
        for tick in snap_ticks:
            samples.append({
                'tick': int(tick),
                'resolution': res,
                'position': [float(c) for c in self.position],
                'target': [float(c) for c in self.target],
                'distance_to_target': self.dist,
                'orientation': self.quat(),
                'orientation_convention_and_values':
                    'quaternion_wxyz_camera_to_frame, forward -Z / up +Y; '
                    'fixed bookmark (pose constant across ticks)',
                'state_or_tick_interval': TICK_MAP,
            })
        rec = {
            'frame_id': 'mat2_m12_lod_' + res + '_' + self.name + '_sheet',
            'coordinate_unit': 'm',
            'handedness': 'right',
            'position': [float(c) for c in self.position],
            'orientation_convention': 'quaternion_wxyz_camera_to_frame',
            'orientation_convention_and_values':
                'quaternion_wxyz_camera_to_frame, forward -Z / up +Y, '
                'fixed bookmark',
            'forward_axis': '-Z',
            'up_axis': '+Y',
            'sample_mode': 'fixed_bookmark',
            'target': [float(c) for c in self.target],
            'distance_to_target': self.dist,
            'projection': self.projection,
            'near_far_planes': NEAR_FAR,
            'aspect_ratio': VP_W / VP_H,
            'viewport_resolution': [VP_W, VP_H],
            'camera_motion_or_bookmark_sequence':
                'fixed_bookmark: identical pose at every snapshot tick; '
                'the SUBJECT moves (solver-solved hanging rig), not the '
                'camera',
            'visibility_layers': list(LAYERS),
            'label_ids': list(LABELS),
            'occlusion_or_xray_mode': 'depth_tested',
            'state_or_tick_interval': TICK_MAP,
            'samples': samples,
        }
        if self.projection == 'perspective':
            rec['vertical_fov_or_orthographic_span'] = \
                'vertical_fov_degrees=%g' % self.fov
            rec['vertical_fov_degrees'] = self.fov
        else:
            rec['vertical_fov_or_orthographic_span'] = \
                'orthographic_span_m=%g' % self.span
            rec['orthographic_span'] = self.span
        return rec


def shade(normal, base):
    light = np.array([0.4, -0.5, 0.75])
    light = light / np.linalg.norm(light)
    d = max(0.0, float(np.dot(normal, -light)))
    return tuple(int(c * (0.35 + 0.65 * d)) for c in base)


def draw_shell(draw, cam, verts, tris, vp_w, vp_h):
    tri = verts[tris]
    centroids = tri.mean(axis=1)
    px, depth = cam.project(centroids, vp_w, vp_h)
    e1 = tri[:, 1] - tri[:, 0]
    e2 = tri[:, 2] - tri[:, 0]
    normals = np.cross(e1, e2)
    nl = np.linalg.norm(normals, axis=1)
    nl[nl == 0] = 1.0
    normals = normals / nl[:, None]
    order = np.argsort(-depth)
    for i in order:
        p3, _ = cam.project(tri[i], vp_w, vp_h)
        pts = [(float(p[0]), float(p[1])) for p in p3]
        if not all(-vp_w <= p[0] <= 2 * vp_w and -vp_h <= p[1] <= 2 * vp_h
                   for p in pts):
            continue
        col = shade(normals[i], (198, 200, 214))
        draw.polygon(pts, fill=col, outline=(120, 122, 134))


def draw_chords(draw, cam, verts, chords, vp_w, vp_h):
    if chords.shape[0] == 0:
        return
    a = verts[chords[:, 0]]
    b = verts[chords[:, 1]]
    mid = 0.5 * (a + b)
    px, depth = cam.project(mid, vp_w, vp_h)
    order = np.argsort(-depth)
    for i in order:
        pa, _ = cam.project(a[i][None, :], vp_w, vp_h)
        pb, _ = cam.project(b[i][None, :], vp_w, vp_h)
        draw.line([(pa[0][0], pa[0][1]), (pb[0][0], pb[0][1])],
                  fill=CHORD_RGB, width=1)


def draw_arrow(draw, origin2, vec2, color, width=2):
    x0, y0 = float(origin2[0]), float(origin2[1])
    x1, y1 = x0 + float(vec2[0]), y0 + float(vec2[1])
    draw.line([(x0, y0), (x1, y1)], fill=color, width=width)
    ang = math.atan2(y1 - y0, x1 - y0)
    for da in (2.6, -2.6):
        draw.line([(x1, y1), (x1 + 6 * math.cos(ang + da),
                              y1 + 6 * math.sin(ang + da))],
                  fill=color, width=1)


def draw_pressure_arrows(draw, cam, verts, tris, vp_w, vp_h, dp_pa):
    if dp_pa <= 0:
        return
    tri = verts[tris]
    e1 = tri[:, 1] - tri[:, 0]
    e2 = tri[:, 2] - tri[:, 0]
    normals = np.cross(e1, e2)
    nl = np.linalg.norm(normals, axis=1)
    nl[nl == 0] = 1.0
    normals = normals / nl[:, None]
    areas = 0.5 * nl
    forces = dp_pa * areas
    fmax = float(forces.max()) if len(forces) else 1.0
    step = max(1, len(tris) // 40)
    for i in range(0, len(tris), step):
        c = tri[i].mean(axis=0)
        px, _ = cam.project(c[None, :], vp_w, vp_h)
        if not (0 <= px[0][0] <= vp_w and 0 <= px[0][1] <= vp_h):
            continue
        n2 = np.array([normals[i] @ cam.right, -normals[i] @ cam.up])
        scale = 14.0 * float(forces[i] / fmax)
        draw_arrow(draw, px[0], n2 * scale, PRESSURE_RGB, width=1)


def _dot(draw, p, rgb, r=3):
    draw.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=rgb)


def _circle(draw, cam, center, radius, vp_w, vp_h, rgb, width=1):
    pts = []
    for k in range(24):
        ang = 2.0 * math.pi * k / 24.0
        pts.append(center + np.array(
            [radius * math.cos(ang), radius * math.sin(ang), 0.0]))
    px, _ = cam.project(np.array(pts), vp_w, vp_h)
    pts2 = [(float(p[0]), float(p[1])) for p in px]
    draw.line(pts2 + [pts2[0]], fill=rgb, width=width)


def _ground(draw, cam, vp_w, vp_h):
    a = np.array([-GROUND_SPAN, 0.0, 0.0])
    b = np.array([GROUND_SPAN, 0.0, 0.0])
    pa, _ = cam.project(a[None, :], vp_w, vp_h)
    pb, _ = cam.project(b[None, :], vp_w, vp_h)
    draw.line([(pa[0][0], pa[0][1]), (pb[0][0], pb[0][1])],
              fill=(90, 92, 104), width=2)


def render_snapshot(model, snap, diag, res, only_layer=None):
    """Render one sheet at the given resolution's model/topology."""
    sheet = np.full((H_SHEET, W_SHEET, 3), 24, dtype=np.uint8)
    img = Image.fromarray(sheet, 'RGB')
    draw = ImageDraw.Draw(img)
    verts = np.array(snap['x'], dtype=np.float64)
    chain = [np.array(p, dtype=np.float64) for p in snap['chain']]
    x_load = np.array(snap['load'], dtype=np.float64)
    dp = float(snap['delta_p_pa'])
    layer_set = set(range(5)) if only_layer is None else {only_layer}
    cams = [Camera(cname, **kw) for cname, kw in BOOKMARKS]
    for ci, cam in enumerate(cams):
        ox, oy = ORIGINS[ci]
        vp_img = Image.new('RGB', (VP_W, VP_H), (24, 24, 24))
        vdraw = ImageDraw.Draw(vp_img)
        vdraw.rectangle([0, 0, VP_W - 1, VP_H - 1], outline=(90, 92, 104))
        draw_shell(vdraw, cam, verts, model.tris, VP_W, VP_H)
        if diag:
            if 0 in layer_set or only_layer == 0:
                p_north, _ = cam.project(verts[model.top_idx][None, :],
                                         VP_W, VP_H)
                _dot(vdraw, p_north[0], (255, 200, 90), 2)
                for name, world_pt, col in (
                        ('tissue_bladder',
                         verts[model.tris].mean(axis=(0, 1)),
                         (200, 200, 210)),
                        ('clamp_ring (visible support)',
                         verts[model.clamp_idx].mean(axis=0),
                         (255, 90, 90)),
                        ('chain T1 humerus', chain[0], (120, 190, 255)),
                        ('chain T2 ulna', chain[1], (120, 190, 255)),
                        ('chain T3 radius', chain[2], (120, 190, 255)),
                        ('chain T4 foot(hand)', chain[3], (90, 230, 160)),
                        ('source_m11_source',
                         verts[model.top_idx], (255, 200, 90))):
                    p, _ = cam.project(np.array([world_pt]), VP_W, VP_H)
                    if 0 <= p[0][0] <= VP_W and 0 <= p[0][1] <= VP_H:
                        vdraw.text((p[0][0] + 4, p[0][1] - 6), name,
                                   fill=col)
            if 1 in layer_set or only_layer == 1:
                draw_pressure_arrows(vdraw, cam, verts, model.tris, VP_W,
                                     VP_H, dp)
            if 2 in layer_set or only_layer == 2:
                draw_chords(vdraw, cam, verts, model.chords, VP_W, VP_H)
            if 3 in layer_set or only_layer == 3:
                _ground(vdraw, cam, VP_W, VP_H)
                anchor = verts[model.bottom_idx]
                pts = [anchor] + chain
                for k in range(len(pts) - 1):
                    pa, _ = cam.project(pts[k][None, :], VP_W, VP_H)
                    pb, _ = cam.project(pts[k + 1][None, :], VP_W, VP_H)
                    vdraw.line([(pa[0][0], pa[0][1]),
                                (pb[0][0], pb[0][1])], fill=TIE_RGB, width=2)
                pl, _ = cam.project(verts[model.top_idx][None, :], VP_W,
                                    VP_H)
                pld, _ = cam.project(x_load[None, :], VP_W, VP_H)
                vdraw.line([(pl[0][0], pl[0][1]), (pld[0][0], pld[0][1])],
                           fill=TIE_RGB, width=1)
                for p_world, rgb, r in ((verts[model.top_idx], CLAMP_RGB,
                                         3),
                                        (x_load, LOAD_RGB, 5),
                                        (anchor, POLE_RGB, 3),
                                        (chain[3], CONTACT_RGB, 4)):
                    p, _ = cam.project(np.array([p_world]), VP_W, VP_H)
                    _dot(vdraw, p[0], rgb, r)
                for k in range(len(chain)):
                    _circle(vdraw, cam, chain[k], model.chain_radius[k],
                            VP_W, VP_H, (0, 150, 90), 1)
            if 4 in layer_set or only_layer == 4:
                vdraw.rectangle([VP_W - 10, VP_H - 10, VP_W - 6, VP_H - 6],
                                fill=(140, 235, 140))
                vdraw.text((4, VP_H - 14),
                           'tick %d | dp %.0f Pa | W_press_cum %.3e J | '
                           'foot_gap %.3e m'
                           % (snap['tick'], dp,
                              float(snap['w_press_cum_j']),
                              float(snap['foot_gap_m'])),
                           fill=(140, 235, 140))
            vdraw.text((4, 2),
                       '%s | diagnostic | %s | tick %d | dp %.0f Pa'
                       % (NAMES[ci], res, snap['tick'], dp),
                       fill=(230, 230, 230))
        else:
            vdraw.text((4, 2),
                       '%s | clean | %s | tick %d' % (NAMES[ci], res,
                                                      snap['tick']),
                       fill=(160, 160, 160))
        img.paste(vp_img, (ox, oy))
    mode = 'diagnostic' if diag else 'clean'
    if diag:
        footer = ('MAT2-M12 LOD comparison: coarse (6x6, 38v/72t/33 '
                  'chords) vs reference (12x12, 146v/288t/150 chords); '
                  'sheet = %s tick %d | layers: %s'
                  % (res, snap['tick'],
                     '; '.join(LAYERS[:3]) + '; ' + '; '.join(LAYERS[3:])))
        draw.text((4, 532), footer[:165], fill=(190, 190, 190))
    return mode, np.array(img, dtype=np.uint8)


def bmp_bytes(arr):
    h, w, _ = arr.shape
    row_size = (w * 3 + 3) & ~3
    pixel_data_size = row_size * h
    header_size = 54
    data_size = header_size + pixel_data_size
    out = bytearray()
    out += struct.pack('<2sIHHI', b'BM', data_size, 0, 0, header_size)
    out += struct.pack('<IiiHHIIiiII', 40, w, h, 1, 24, 0,
                       pixel_data_size, 0, 0, 0, 0)
    pad = b'\x00' * (row_size - w * 3)
    flipped = arr[::-1]
    for y in range(h):
        row = flipped[y]
        out += row.tobytes()
        out += pad
    return bytes(out)


def read_bmp_rgb(data):
    pixel_off = struct.unpack('<I', data[10:14])[0]
    w = struct.unpack('<i', data[18:22])[0]
    h = struct.unpack('<i', data[22:26])[0]
    bpp = struct.unpack('<H', data[28:30])[0]
    require(bpp == 24 and h > 0, 'bmp_format_unsupported')
    row_size = (w * 3 + 3) & ~3
    arr = np.zeros((h, w, 3), dtype=np.uint8)
    for y in range(h):
        start = pixel_off + (h - 1 - y) * row_size
        arr[y] = np.frombuffer(data[start:start + w * 3],
                               dtype=np.uint8).reshape(w, 3)
    return arr


def _marker_stats(arr, rect, rgb):
    x0, y0, x1, y1 = rect
    sub = arr[y0:y1 + 1, x0:x1 + 1]
    mask = np.all(sub == np.array(rgb, dtype=np.uint8), axis=2)
    rows, cols = np.nonzero(mask)
    return {'rgb': [int(c) for c in rgb], 'px_count': int(rows.size),
            'mean_row': float(rows.mean()) if rows.size else None}


def layer_presence_proof(stills):
    layer_colors = {
        0: [(255, 200, 90)],
        1: [(220, 30, 30)],
        2: [(255, 140, 0)],
        3: [(0, 170, 255), (0, 150, 90)],
        4: [(140, 235, 140)],
    }
    proof = {'rule': 'each declared layer rendered alone places >= 1 pixel '
                     'of a layer key color (both resolutions probed)',
             'per_layer': {}}
    for idx in range(5):
        per_res = {}
        for res in RES_IDS:
            arr = stills['layer_%d_%s' % (idx, res)]
            counts = {}
            total = 0
            for rgb in layer_colors[idx]:
                mask = np.all(arr == np.array(rgb, dtype=np.uint8), axis=2)
                counts[str(rgb)] = int(np.count_nonzero(mask))
                total += counts[str(rgb)]
            require(total >= 1, 'layer_pixel_presence_failed:%s:%d'
                    % (res, idx))
            per_res[res] = {'key_colors': counts, 'pixels_present': total,
                            'present': True}
        proof['per_layer'][LAYERS[idx]] = {
            'layer_index': idx, 'per_resolution': per_res}
    return proof


def camera_consistency_proof(stills):
    proof = {'rule': 'declared-above marker mean pixel row < declared-below '
                     'marker mean pixel row (rows grow downward), per '
                     'perspective viewport, declared +Z-dominant camera up; '
                     'measured on the committed diagnostic stills',
             'viewports': {'whole': {'above': 'clamp_ring',
                                     'below': 'load_surrogate'},
                           'closeup': {'above': 'free pole (T1 anchor)',
                                       'below': 'foot contact'}},
             'per_still': {}}
    for fname, arr in sorted(stills.items()):
        if not fname.startswith('frame_'):
            continue
        per = {}
        for vp, above_rgb, below_rgb in (
                ('whole', CLAMP_RGB, LOAD_RGB),
                ('closeup', POLE_RGB, CONTACT_RGB)):
            above = _marker_stats(arr, VP_RECTS[vp], above_rgb)
            below = _marker_stats(arr, VP_RECTS[vp], below_rgb)
            require(above['px_count'] > 0,
                    'camera_consistency_content_missing:%s:%s'
                    % (fname, vp))
            require(below['px_count'] > 0,
                    'camera_consistency_content_missing:%s:%s'
                    % (fname, vp))
            delta = below['mean_row'] - above['mean_row']
            require(delta > 0.0,
                    'camera_consistency_row_order_failed:%s:%s'
                    % (fname, vp))
            per[vp] = {'above': above, 'below': below,
                       'signed_row_delta_below_minus_above': float(delta),
                       'consistent': True}
        close = VP_RECTS['closeup']
        tie = _marker_stats(arr, close, TIE_RGB)
        require(tie['px_count'] > 0,
                'camera_consistency_content_missing:%s:closeup_tie' % fname)
        per['closeup']['tie_px_count'] = tie['px_count']
        mask = np.all(arr == np.array(TIE_RGB, dtype=np.uint8), axis=2)
        allowed = np.zeros_like(mask)
        for rect in VP_RECTS.values():
            x0, y0, x1, y1 = rect
            allowed[y0:y1 + 1, x0:x1 + 1] = True
        outside = int(np.count_nonzero(mask & ~allowed))
        require(outside == 0, 'viewport_leakage:%s:%d' % (fname, outside))
        per['leakage'] = {'tie_rgb': [int(c) for c in TIE_RGB],
                          'pixels_outside_viewports': outside}
        proof['per_still'][fname] = per
    return proof


def build_models():
    real = lw.load_real_data()
    models = {}
    for res in RES_IDS:
        world, _ = ml.build_world(res, lw.off_schedule, 1, 'off', real=real)
        models[res] = world
    return models


def main():
    capture_dir = pathlib.Path(sys.argv[1])
    frames_dir = capture_dir / 'frames'
    payloads_dir = capture_dir / 'payloads'
    evidence_dir = capture_dir / 'evidence'
    for d in (frames_dir, payloads_dir, evidence_dir):
        d.mkdir(parents=True, exist_ok=True)
    trace = json.loads(TRACE_PATH.read_text(encoding='utf-8'))
    models = build_models()
    cameras = {res: [Camera(cname, **kw) for cname, kw in BOOKMARKS]
               for res in RES_IDS}
    frame_hashes = {}
    still_hashes = {}
    res_bindings = {}
    for res in RES_IDS:
        dyn = trace['runs'][res]
        snap_ticks = sorted(int(k)
                            for k in dyn['loaded_snapshots'])
        row_lookup = {r['tick']: r for r in dyn['loaded_rows']}
        model = models[res]
        for si, tick in enumerate(snap_ticks):
            snap = dyn['loaded_snapshots'][str(tick)]
            if tick == 0:
                require(abs(float(snap['volume_m3']) -
                            float(model.volume_rest)) <= 1e-12,
                        'bind_rest_volume_mismatch:%s' % res)
            else:
                row = row_lookup[tick - 1]
                require(abs(float(snap['foot_gap_m']) -
                            float(row['foot_gap_m'])) <= 1e-12,
                        'bind_foot_gap_mismatch:%s:%d' % (res, tick))
                require(abs(float(snap['chain'][-1][2]) -
                            float(row['chain_z_m'][-1])) <= 1e-12,
                        'bind_chain_tail_mismatch:%s:%d' % (res, tick))
                require(abs(float(snap['volume_m3']) -
                            float(row['volume_m3'])) <= 1e-12,
                        'bind_volume_mismatch:%s:%d' % (res, tick))
            for mode_offset, diag in ((0, True), (1, False)):
                frame = si * 4 + RES_IDS.index(res) * 2 + mode_offset
                mode, arr = render_snapshot(model, snap, diag, res)
                payload = arr.tobytes()
                sha = hashlib.sha256(payload).hexdigest()
                frame_hashes['frame_%02d' % frame] = {
                    'frame_index': frame, 'resolution': res,
                    'snapshot_tick': tick, 'mode': mode,
                    'raw_payload_sha256': sha,
                    'width': W_SHEET, 'height': H_SHEET}
                (payloads_dir / ('frame_%02d.raw' % frame)).write_bytes(
                    payload)
                if frame in STILL_INDICES:
                    bmp = bmp_bytes(arr)
                    (frames_dir /
                     ('frame_%02d.bmp' % frame)).write_bytes(bmp)
                    still_hashes['frame_%02d' % frame] = {
                        'path': 'capture/frames/frame_%02d.bmp' % frame,
                        'sha256': hashlib.sha256(bmp).hexdigest(),
                        'resolution': res, 'snapshot_tick': tick,
                        'mode': mode}
    # per-layer pixel presence at BOTH resolutions (first diagnostic tick)
    presence_stills = {}
    layer_meta = {}
    for res in RES_IDS:
        dyn = trace['runs'][res]
        snap_ticks = sorted(int(k) for k in dyn['loaded_snapshots'])
        snap0 = dyn['loaded_snapshots'][str(snap_ticks[0])]
        if snap_ticks[0] == 0 and len(snap_ticks) > 1:
            snap0 = dyn['loaded_snapshots'][str(snap_ticks[1])]
        for idx in range(5):
            mode, arr = render_snapshot(models[res], snap0, True, res,
                                        only_layer=idx)
            fname = 'layer_%d_%s' % (idx, res)
            presence_stills[fname] = arr
            bmp = bmp_bytes(arr)
            (frames_dir / (fname + '.bmp')).write_bytes(bmp)
            layer_meta[fname] = {'resolution': res,
                                 'snapshot_tick': int(snap0['tick']),
                                 'sha256': hashlib.sha256(bmp).hexdigest(),
                                 'mode': mode}
    proof = {}
    for fname, meta in still_hashes.items():
        data = (frames_dir / (fname + '.bmp')).read_bytes()
        arr = read_bmp_rgb(data)
        payload = arr.tobytes()
        ok = hashlib.sha256(payload).hexdigest() == \
            frame_hashes[fname]['raw_payload_sha256']
        h, w, _ = arr.shape
        row_size = (w * 3 + 3) & ~3
        pixel_off = struct.unpack('<I', data[10:14])[0]
        mis = np.zeros((h, w, 3), dtype=np.uint8)
        for y in range(h):
            start = pixel_off + y * row_size
            mis[y] = np.frombuffer(data[start:start + w * 3],
                                   dtype=np.uint8).reshape(w, 3)
        top_down = mis.tobytes() != payload
        proof[fname] = {'bmp_rows_match_payload': bool(ok),
                        'topdown_misread_does_not_match': bool(top_down)}
        require(ok, 'row_order_proof_failed:' + fname)
        require(top_down, 'row_order_sensitivity_failed:' + fname)
    cc_stills = {}
    for fname in still_hashes:
        cc_stills[fname] = read_bmp_rgb(
            (frames_dir / (fname + '.bmp')).read_bytes())
    cc_proof = camera_consistency_proof(cc_stills)
    lp_proof = layer_presence_proof(presence_stills)
    cam_records = {res: {c.name: c.record(res, sorted(
        int(k) for k in trace['runs'][res]['loaded_snapshots']))
        for c in cameras[res]} for res in RES_IDS}
    (evidence_dir / 'cameras.json').write_text(
        json.dumps({res: {VIEW_IDS[0]: [cam_records[res]['whole']],
                          VIEW_IDS[1]: [cam_records[res]['side'],
                                        cam_records[res]['front']],
                          VIEW_IDS[2]: [cam_records[res]['closeup']]}
                     for res in RES_IDS}, indent=1, sort_keys=True) + '\n',
        encoding='utf-8', newline='\n')
    (evidence_dir / 'capture_evidence.json').write_text(
        json.dumps({'cameras': cam_records, 'view_ids': VIEW_IDS,
                    'resolutions': list(RES_IDS), 'subjects': SUBJECTS,
                    'labels': LABELS, 'tick_map': TICK_MAP,
                    'sheet': [W_SHEET, H_SHEET],
                    'still_indices': list(STILL_INDICES),
                    'row_order_proof': proof,
                    'camera_consistency_proof': cc_proof,
                    'layer_presence_proof': lp_proof,
                    'layer_probe_meta': layer_meta,
                    'viewport_rects': {k: list(v) for k, v in
                                       VP_RECTS.items()},
                    'frame_raw_sha256': frame_hashes,
                    'still_hashes': still_hashes},
                   indent=1, sort_keys=True) + '\n',
        encoding='utf-8', newline='\n')
    print('rendered %d frames (%d snapshots x %d resolutions x2), '
          'stills %d, layer probes %d'
          % (len(frame_hashes), 6, len(RES_IDS), len(still_hashes),
             len(layer_meta)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
