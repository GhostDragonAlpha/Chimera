"""MAT2-M10 visual capture renderer: renders the solver snapshot stream
(experiment_trace.json snapshots) into the frozen camera sheets
(PREREGISTRATION.md + Amendment A1 verification-profile views).

Per declared snapshot tick TWO sheets are produced:
  frame_2k   DIAGNOSTIC sheet (2x2 viewports: whole | side / front |
             close-up) carrying all five registry diagnostic layers,
  frame_2k+1 CLEAN sheet (identical cameras; geometry only; no labels, no
             overlays, no diagnostic styling).
Video = 18 frames (9 ticks x 2 sheets); committed BMP stills at declared
frame indices [0, 4, 5, 8] (recomputable). Cameras fixed bookmarks; the
SUBJECT moves per the sha-bound trace. BINDING ASSERTION: each rendered
snapshot's south-pole z and volume are asserted against the trace rows
before any pixel is written.

CPU rasterizer, painter's algorithm (declared occlusion depth_tested);
software rasterization of solver state. Deterministic.
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

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import actuator_world as aw  # noqa: E402

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
NEAR_FAR = [0.01, 100.0]
SUBJECTS = ['actuator_shell', 'clamp_north_cap', 'tie_south_pole', 'load',
            'source_m10_source']
LABELS = ['actuator_shell', 'actuator_shell/m:belt', 'port:pressure',
          'clamp_north_cap (visible support)', 'tie_south_pole',
          'bond:tie', 'load', 'source_m10_source']
# diagnostic marker colors (exact RGB; the camera-consistency probe and the
# committed-still gates key on them)
CLAMP_RGB = (255, 70, 70)    # north clamp ring (declared support, above)
LOAD_RGB = (60, 60, 225)     # load dot (declared below)
ANCHOR_RGB = (0, 220, 120)   # south-pole tie anchor dot (declared above load)
TIE_RGB = (0, 170, 255)      # tie line
TICK_MAP = ('1 tick = 1/300 s simulated; frames are the declared snapshot '
            'ticks 0,300,400,700,1000,1100,1200,1350,1499; even frames are '
            'the diagnostic sheets, odd frames the clean sheets '
            '(1 video second per snapshot)')
# fixed bookmarks (single source; A1.9 round: the close-up aim point moved
# from the south pole (0,0,-0.05) to the loaded-interface midpoint (0,0,
# -0.10) and pulled back along the SAME view direction (0.09,-0.13,0.03)
# from 0.161 m to 0.26 m so the DECLARED content (the south-pole tie anchor,
# the tie and the load) is inside the viewport once the perspective-depth
# sign is fixed; recorded in the regenerated cameras.json all-fields
# records. whole/side/front bookmarks unchanged.)
CLOSEUP_TARGET = (0.0, 0.0, -0.10)
_CLOSEUP_DIR_NORM = 0.1609347693943108  # |(0.09,-0.13,0.03)| original
CLOSEUP_DIST = 0.26
CLOSEUP_POSITION = tuple(
    CLOSEUP_TARGET[i] + CLOSEUP_DIST *
    ((0.09, -0.13, 0.03)[i] / _CLOSEUP_DIR_NORM) for i in range(3))
BOOKMARKS = (
    ('whole', dict(position=(0.30, -0.42, 0.26), target=(0.0, 0.0, -0.045),
                   projection='perspective', fov_degrees=40)),
    ('side', dict(position=(0.0, 0.62, -0.05), target=(0.0, 0.0, -0.05),
                  projection='orthographic', span=0.40)),
    ('front', dict(position=(0.62, 0.0, -0.05), target=(0.0, 0.0, -0.05),
                   projection='orthographic', span=0.40)),
    ('closeup', dict(position=CLOSEUP_POSITION, target=CLOSEUP_TARGET,
                     projection='perspective', fov_degrees=30)))
ORIGINS = [(4, 4), (484, 4), (4, 268), (484, 268)]
NAMES = ['whole', 'side', 'front', 'close-up']
# inclusive pixel rects of the four viewports on the sheet (leakage gate)
VP_RECTS = {'whole': (4, 4, 479, 263), 'side': (484, 4, 959, 263),
            'front': (4, 268, 479, 527), 'closeup': (484, 268, 959, 527)}

TRACE_PATH = HERE / 'experiment_trace.json'


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

    def project(self, points, vp_origin, vp_w, vp_h):
        pts = np.atleast_2d(np.asarray(points, dtype=np.float64))
        rel = pts - self.position
        x = rel @ self.right
        y = rel @ self.up
        # review r1 finding F2 fix: depth along +forward, so scene points
        # in front of the camera have POSITIVE depth (the previous
        # rel @ -forward made every depth negative and the perspective
        # divide mirrored both axes: 180-deg rotated viewports)
        z = rel @ self.forward
        ox, oy = vp_origin
        if self.projection == 'perspective':
            t = math.tan(math.radians(self.fov) / 2.0)
            aspect = vp_w / vp_h
            depth = z
            px = ox + vp_w / 2.0 + (x / (z * t * aspect)) * (vp_w / 2.0)
            py = oy + vp_h / 2.0 - (y / (z * t)) * (vp_h / 2.0)
        else:
            depth = z
            scale = vp_h / self.span
            px = ox + vp_w / 2.0 + x * scale
            py = oy + vp_h / 2.0 - y * scale
        return np.column_stack([px, py]), depth

    def quat(self):
        """wxyz quaternion of the camera-to-frame rotation (columns
        right, up, -forward; forward -Z / up +Y convention)."""
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

    def record(self, snap_ticks):
        samples = []
        for tick in snap_ticks:
            samples.append({
                'tick': int(tick),
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
            'frame_id': 'mat2_m10_jack_' + self.name + '_sheet',
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
                'the SUBJECT moves (solver-solved shell and load), not '
                'the camera',
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


def draw_shell(draw, cam, verts, tris, vp, base=(198, 200, 214)):
    tri = verts[tris]
    centroids = tri.mean(axis=1)
    px, depth = cam.project(centroids, vp[0], vp[1][0], vp[1][1])
    e1 = tri[:, 1] - tri[:, 0]
    e2 = tri[:, 2] - tri[:, 0]
    normals = np.cross(e1, e2)
    nl = np.linalg.norm(normals, axis=1)
    nl[nl == 0] = 1.0
    normals = normals / nl[:, None]
    order = np.argsort(-depth)
    inside = ((px[:, 0] > vp[0][0] - 80) & (px[:, 0] < vp[0][0] + vp[1][0] + 80)
              & (px[:, 1] > vp[0][1] - 80) & (px[:, 1] < vp[0][1] + vp[1][1] + 80))
    for i in order:
        if not inside[i]:
            continue
        p3, _ = cam.project(tri[i], vp[0], vp[1][0], vp[1][1])
        pts = [(float(p[0]), float(p[1])) for p in p3]
        col = shade(normals[i], base)
        draw.polygon(pts, fill=col, outline=(120, 122, 134))


def draw_chords(draw, cam, verts, chords, vp, color=(255, 140, 0)):
    a = verts[chords[:, 0]]
    b = verts[chords[:, 1]]
    mid = 0.5 * (a + b)
    px, depth = cam.project(mid, vp[0], vp[1][0], vp[1][1])
    order = np.argsort(-depth)
    for i in order:
        pa, _ = cam.project(a[i], vp[0], vp[1][0], vp[1][1])
        pb, _ = cam.project(b[i], vp[0], vp[1][0], vp[1][1])
        draw.line([(pa[0][0], pa[0][1]), (pb[0][0], pb[0][1])],
                  fill=color, width=1)


def draw_arrow(draw, origin2, vec2, color, width=2):
    x0, y0 = float(origin2[0]), float(origin2[1])
    x1, y1 = x0 + float(vec2[0]), y0 + float(vec2[1])
    draw.line([(x0, y0), (x1, y1)], fill=color, width=width)
    ang = math.atan2(y1 - y0, x1 - x0)
    for da in (2.6, -2.6):
        draw.line([(x1, y1), (x1 + 6 * math.cos(ang + da),
                              y1 + 6 * math.sin(ang + da))],
                  fill=color, width=1)


def draw_pressure_arrows(draw, cam, verts, tris, vp, dp_pa):
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
        px, depth = cam.project(c[None, :], vp[0], vp[1][0], vp[1][1])
        if not (vp[0][0] <= px[0][0] <= vp[0][0] + vp[1][0] and
                vp[0][1] <= px[0][1] <= vp[0][1] + vp[1][1]):
            continue
        n2 = np.array([normals[i] @ cam.right, -normals[i] @ cam.up])
        scale = 14.0 * float(forces[i] / fmax)
        draw_arrow(draw, px[0], n2 * scale, (220, 30, 30), width=1)


def bmp_bytes(arr):
    """Minimal 24-bit BMP writer (stdlib; top-down RGB array in)."""
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
    """Minimal 24-bit BMP reader (stdlib) -> top-down RGB array."""
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
    """Exact-RGB marker stats inside an inclusive viewport rect:
    pixel count and mean pixel row (image rows grow DOWNWARD)."""
    x0, y0, x1, y1 = rect
    sub = arr[y0:y1 + 1, x0:x1 + 1]
    mask = np.all(sub == np.array(rgb, dtype=np.uint8), axis=2)
    rows, cols = np.nonzero(mask)
    return {'rgb': [int(c) for c in rgb], 'px_count': int(rows.size),
            'mean_row': float(rows.mean()) if rows.size else None}


def camera_consistency_proof(stills):
    """Review r1 F2 required extension of the pixel probe: one SIGNED
    geometric check per perspective viewport on each committed diagnostic
    still — under the declared camera up (+Z-dominant), a declared-above
    object (north clamp ring in 'whole'; the south-pole tie anchor dot in
    'close-up') must land ABOVE (smaller pixel row) the declared-below
    object (the load dot). Also asserts declared-content presence in the
    close-up (anchor + tie + load pixels) and zero cross-viewport leakage
    of the tie color outside the four viewport rects."""
    proof = {'rule': 'declared-above marker mean pixel row < declared-below '
                     'marker mean pixel row (rows grow downward), per '
                     'perspective viewport, declared +Z-dominant camera up; '
                     'measured on the committed diagnostic stills',
             'viewports': {'whole': {'above': 'clamp_north_cap',
                                     'below': 'load'},
                           'closeup': {'above': 'tie_south_pole anchor dot',
                                       'below': 'load'}},
             'per_still': {}}
    tie_mask_all = None
    for fname, arr in sorted(stills.items()):
        per = {}
        for vp, above_rgb, below_rgb in (
                ('whole', CLAMP_RGB, LOAD_RGB),
                ('closeup', ANCHOR_RGB, LOAD_RGB)):
            above = _marker_stats(arr, VP_RECTS[vp], above_rgb)
            below = _marker_stats(arr, VP_RECTS[vp], below_rgb)
            require(above['px_count'] > 0,
                    'camera_consistency_content_missing:%s:%s' % (fname, vp))
            require(below['px_count'] > 0,
                    'camera_consistency_content_missing:%s:%s' % (fname, vp))
            delta = below['mean_row'] - above['mean_row']
            require(delta > 0.0,
                    'camera_consistency_row_order_failed:%s:%s' % (fname,
                                                                   vp))
            per[vp] = {'above': above, 'below': below,
                       'signed_row_delta_below_minus_above': float(delta),
                       'consistent': True}
        # declared close-up content: anchor, tie, load all present
        close = VP_RECTS['closeup']
        tie = _marker_stats(arr, close, TIE_RGB)
        require(tie['px_count'] > 0,
                'camera_consistency_content_missing:%s:closeup_tie' % fname)
        per['closeup']['tie_px_count'] = tie['px_count']
        # cross-viewport leakage: tie pixels only inside the four rects
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


def render_snapshot(model, snap, row_lookup, tick, diag):
    sheet = np.full((H_SHEET, W_SHEET, 3), 24, dtype=np.uint8)
    img = Image.fromarray(sheet, 'RGB')
    draw = ImageDraw.Draw(img)
    verts = np.array(snap['x'], dtype=np.float64)
    x_load = np.array(snap['x_load'], dtype=np.float64)
    dp = float(snap['delta_p_pa'])
    # binding assertions BEFORE any pixel is written (snapshot tick T is
    # the state after T completed ticks = trace row T-1; snapshot 0 is the
    # rest state, bound to the model's own closed-mesh identity)
    if tick == 0:
        bind_volume = float(model.report['signed_volume_m3'])
        bind_pole = float(model.rest[model.south, 2])
    else:
        row = row_lookup[tick - 1]
        bind_volume = float(row['volume_m3'])
        bind_pole = float(row['z_tip_m'])
    require(abs(float(snap['volume_m3']) - bind_volume) <= 1e-9,
            'bind_volume_mismatch:%d' % tick)
    pole_z = float(verts[model.south, 2])
    require(abs(pole_z - bind_pole) <= 1e-9,
            'bind_pole_mismatch:%d' % tick)

    cams = [Camera(cname, **kw) for cname, kw in BOOKMARKS]
    # Each viewport renders on its OWN image which is then pasted onto the
    # sheet: no viewport can draw outside its rectangle (the review r1 F2
    # cross-viewport tie-line leakage class is impossible by construction).
    for ci, cam in enumerate(cams):
        ox, oy = ORIGINS[ci]
        vp_img = Image.new('RGB', (VP_W, VP_H), (24, 24, 24))
        vdraw = ImageDraw.Draw(vp_img)
        vp = ((0, 0), (VP_W, VP_H))
        vdraw.rectangle([0, 0, VP_W - 1, VP_H - 1], outline=(90, 92, 104))
        draw_shell(vdraw, cam, verts, model.tris, vp)
        if diag:
            draw_chords(vdraw, cam, verts, model.chords, vp)
            draw_pressure_arrows(vdraw, cam, verts, model.tris, vp, dp)
            # clamp ring (visible support) + tie anchor dot + tie + load
            cl = verts[model.clamp_idx]
            px, _ = cam.project(cl, vp[0], vp[1][0], vp[1][1])
            for p in px:
                if 0 <= p[0] <= VP_W and 0 <= p[1] <= VP_H:
                    vdraw.ellipse([p[0] - 3, p[1] - 3, p[0] + 3, p[1] + 3],
                                  fill=CLAMP_RGB)
            sp = verts[model.south]
            pt, _ = cam.project(np.vstack([sp, x_load]), vp[0], vp[1][0],
                                vp[1][1])
            vdraw.ellipse([pt[0][0] - 3, pt[0][1] - 3, pt[0][0] + 3,
                           pt[0][1] + 3], fill=ANCHOR_RGB)
            vdraw.line([(pt[0][0], pt[0][1]), (pt[1][0], pt[1][1])],
                       fill=TIE_RGB, width=2)
            vdraw.ellipse([pt[1][0] - 5, pt[1][1] - 5, pt[1][0] + 5,
                           pt[1][1] + 5], fill=LOAD_RGB)
            # labels (stable IDs)
            for name, world_pt, col in (
                    ('clamp_north_cap (visible support)',
                     verts[model.clamp_idx].mean(axis=0), (255, 90, 90)),
                    ('actuator_shell / bond:tie', sp, (0, 190, 255)),
                    ('load', x_load, (140, 140, 255)),
                    ('port:pressure / source_m10_source',
                     verts[model.north], (255, 200, 90))):
                p, _ = cam.project(np.array([world_pt]), vp[0], vp[1][0],
                                   vp[1][1])
                if 0 <= p[0][0] <= VP_W and 0 <= p[0][1] <= VP_H:
                    vdraw.text((p[0][0] + 4, p[0][1] - 6), name, fill=col)
            vdraw.text((4, 2),
                       '%s | diagnostic | tick %d | dp %.0f Pa'
                       % (NAMES[ci], tick, dp), fill=(230, 230, 230))
        else:
            vdraw.text((4, 2),
                       '%s | clean | tick %d' % (NAMES[ci], tick),
                       fill=(160, 160, 160))
        img.paste(vp_img, (ox, oy))
    mode = 'diagnostic' if diag else 'clean'
    footer = ('MAT2-M10 jack: clamped spherical pressure vessel, authored '
              '%s chord net | layers: %s | footer: dp=%.0f Pa, '
              'z_load=%.5f m, W_press_cum=%.3e J'
              % (model.layout, '; '.join(LAYERS[:3]) + '; ' +
                 '; '.join(LAYERS[3:]), dp, float(snap['x_load'][2]),
                 float(snap['w_press_cum_j'])))
    draw.text((4, 532), footer[:160], fill=(190, 190, 190))
    return mode, np.array(img, dtype=np.uint8)


def main():
    capture_dir = pathlib.Path(sys.argv[1])
    frames_dir = capture_dir / 'frames'
    payloads_dir = capture_dir / 'payloads'
    evidence_dir = capture_dir / 'evidence'
    for d in (frames_dir, payloads_dir, evidence_dir):
        d.mkdir(parents=True, exist_ok=True)
    trace = json.loads(TRACE_PATH.read_text(encoding='utf-8'))
    dyn = trace['dynamic_run']
    snap_ticks = sorted(int(k) for k in dyn['snapshots'])
    row_lookup = {r['tick']: r for r in dyn['rows']}
    model = aw.ActuatorModel('braid')
    cameras = [Camera(cname, **kw) for cname, kw in BOOKMARKS]
    cam_records = {c.name: c.record(snap_ticks) for c in cameras}
    frame_hashes = {}
    still_hashes = {}
    for si, tick in enumerate(snap_ticks):
        snap = dyn['snapshots'][str(tick)]
        for mode_offset, diag in ((0, True), (1, False)):
            frame = si * 2 + mode_offset
            mode, arr = render_snapshot(model, snap, row_lookup, tick, diag)
            payload = arr.tobytes()
            sha = hashlib.sha256(payload).hexdigest()
            frame_hashes['frame_%02d' % frame] = {
                'frame_index': frame, 'snapshot_tick': tick, 'mode': mode,
                'raw_payload_sha256': sha,
                'width': W_SHEET, 'height': H_SHEET}
            (payloads_dir / ('frame_%02d.raw' % frame)).write_bytes(payload)
            if frame in (0, 8, 10, 16):
                bmp = bmp_bytes(arr)
                (frames_dir / ('frame_%02d.bmp' % frame)).write_bytes(bmp)
                still_hashes['frame_%02d' % frame] = {
                    'path': 'capture/frames/frame_%02d.bmp' % frame,
                    'sha256': hashlib.sha256(bmp).hexdigest(),
                    'snapshot_tick': tick, 'mode': mode}
    # stdlib row-order proof: decode a committed still, rebuild the rgb24
    # payload rows, and compare against the recorded payload hash
    proof = {}
    for fname, meta in still_hashes.items():
        data = (frames_dir / (fname + '.bmp')).read_bytes()
        arr = read_bmp_rgb(data)
        payload = arr.tobytes()
        ok = hashlib.sha256(payload).hexdigest() == \
            frame_hashes[fname]['raw_payload_sha256']
        # sensitivity guard: a reader that (wrongly) takes the storage rows
        # top-down must NOT reproduce the payload (the F04 bug class; the
        # guard dies if the bug class returns)
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
    # review r1 F2: the camera-consistency pixel probe runs on the
    # COMMITTED stills (read back from disk, not the in-memory arrays)
    cc_stills = {}
    for fname in still_hashes:
        cc_stills[fname] = read_bmp_rgb(
            (frames_dir / (fname + '.bmp')).read_bytes())
    cc_proof = camera_consistency_proof(cc_stills)
    (evidence_dir / 'cameras.json').write_text(
        json.dumps({'cameras': cam_records, 'view_ids': VIEW_IDS,
                    'subjects': SUBJECTS, 'labels': LABELS,
                    'tick_map': TICK_MAP, 'sheet': [W_SHEET, H_SHEET],
                    'still_indices': [0, 8, 10, 16],
                    'still_frame_indices_declared': aw.STILL_INDICES,
                    'row_order_proof': proof,
                    'camera_consistency_proof': cc_proof,
                    'viewport_rects': {k: list(v) for k, v in
                                       VP_RECTS.items()},
                    'frame_raw_sha256': frame_hashes,
                    'still_hashes': still_hashes},
                   indent=1, sort_keys=True) + '\n', encoding='utf-8',
        newline='\n')
    print('rendered %d frames (%d snapshots x2), stills %d'
          % (len(frame_hashes), len(snap_ticks), len(still_hashes)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
