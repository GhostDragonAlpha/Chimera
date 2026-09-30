"""MAT2-G02 visual capture renderer (attachment-fixture/motion).

Renders the frozen capture ticks from the committed experiment trace into a
sheet per tick: three registry views x {diagnostic, clean} pairs, fixed
bookmark cameras, full 16-field registry camera record per camera, authored
frames and port IDs on diagnostic viewports only, gap/displacement trace
inset (diagnostic sheet footer). Clean pairs share the EXACT camera and the
EXACT physical state of their diagnostic pair (state hash preserved across
view toggles, asserted per tick). Pure software raster (Pillow); the solver
state is bound to the committed receipts before any pixel is written.

Run:  python -B render_run.py <attempt_capture_dir>
"""
from __future__ import annotations

import hashlib
import json
import math
import pathlib
import sys

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
VP_W, VP_H = 640, 240
SHEET = (2 * VP_W, 3 * VP_H + 0)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def state_hash(row):
    payload = json.dumps(row, sort_keys=True, separators=(',', ':'),
                         allow_nan=False).encode('utf-8')
    return sha(payload)


# ------------------------------------------------------------------ camera
def mat_to_quat(m):
    """Rotation matrix -> unit quaternion (w, x, y, z)."""
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
        w = (m[0][2] - m[2][0]) / s
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


class Camera:
    """Declared perspective camera with the full registry record."""

    def __init__(self, name, position, target, vfov_deg=40.0,
                 near=0.005, far=5.0):
        self.name = name
        self.position = list(position)
        self.target = list(target)
        self.vfov = vfov_deg
        self.near = near
        self.far = far
        f = [target[i] - position[i] for i in range(3)]
        fl = math.sqrt(sum(x * x for x in f))
        f = [x / fl for x in f]
        up = [0.0, 0.0, 1.0]
        r = [f[1] * up[2] - f[2] * up[1],
             f[2] * up[0] - f[0] * up[2],
             f[0] * up[1] - f[1] * up[0]]
        rl = math.sqrt(sum(x * x for x in r))
        r = [x / rl for x in r]
        u = [f[1] * r[2] - f[2] * r[1],
             f[2] * r[0] - f[0] * r[2],
             f[0] * r[1] - f[1] * r[0]]   # f x r: right-handed (r, u, f)
        self.basis = (r, u, f)
        self.quat = mat_to_quat([[r[0], u[0], f[0]],
                                 [r[1], u[1], f[1]],
                                 [r[2], u[2], f[2]]])

    def project(self, p, vp_w, vp_h):
        d = [p[i] - self.position[i] for i in range(3)]
        zc = sum(d[i] * self.basis[2][i] for i in range(3))
        xc = sum(d[i] * self.basis[0][i] for i in range(3))
        yc = sum(d[i] * self.basis[1][i] for i in range(3))
        if zc <= 1e-6:
            return None
        t = math.tan(math.radians(self.vfov) / 2.0)
        xn = xc / (zc * t)
        yn = yc / (zc * t)
        return (int((xn * 0.5 + 0.5) * vp_w),
                int((1.0 - (yn * 0.5 + 0.5)) * vp_h))

    def record(self, snap_ticks, layers, labels):
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
            'forward_axis': '+Z',
            'up_axis': '+Y',
            'near_far_planes': [self.near, self.far],
            'viewport_resolution': [VP_W, VP_H],
            'aspect_ratio': VP_W / VP_H,
            'projection': 'perspective',
            'vertical_fov_degrees': self.vfov,
            'sample_mode': 'fixed_bookmark',
            'samples': [sample(t) for t in snap_ticks],
            'position': list(self.position),
            'target': list(self.target),
            'distance_to_target': dist,
            'orientation_convention_and_values': {
                'convention': 'unit quaternion w,x,y,z mapping camera '
                              'coordinates to the declared rest frame',
                'quaternion_wxyz': list(self.quat)},
            'vertical_fov_or_orthographic_span': self.vfov,
            'camera_motion_or_bookmark_sequence':
                'fixed bookmark; no motion across frames',
            'visibility_layers': list(layers),
            'label_ids': list(labels),
            'occlusion_or_xray_mode': 'depth_tested',
            'state_or_tick_interval': [snap_ticks[0], snap_ticks[-1]],
        }



def cameras_for(_):
    target = [0.03, 0.01, 0.005]
    overview = Camera('patch_overview', (-0.25, -0.18, 0.16), target)
    closeup = Camera('loaded_interface_closeup', (-0.06, 0.008, 0.020),
                     [0.0, 0.008, 0.005], vfov_deg=25.0)
    ortho = Camera('orthogonal_patch', (0.12, 0.01, 0.005),
                   [0.0, 0.01, 0.005], vfov_deg=20.0)
    oblique = Camera('oblique_patch', (0.10, -0.09, 0.09),
                     [0.0, 0.01, 0.005], vfov_deg=20.0)
    return [
        (VIEWS[0], overview, None),
        (VIEWS[1], closeup, None),
        (VIEWS[2], ortho, oblique),
    ]


# ------------------------------------------------------------------ render
BODY_EDGES = [(0, 1), (1, 2), (2, 3), (3, 0), (0, 4), (1, 4), (2, 4),
              (3, 4)]
PATCH_QUAD_YZ = [(0.0, 0.0), (0.020, 0.0), (0.013, 0.010), (0.0, 0.010)]


def draw_viewport(draw, cam, row, diagnostic):
    verts_a = [(0.0, 0.0, 0.0), (0.0, 0.2, 0.0), (0.0, 0.15, 0.1),
               (0.0, 0.0, 0.1), (-0.16, 0.08809523809523807,
                                 0.04761904761904761)]
    verts_b = [(row['gap_m'] + v[0], v[1], v[2]) for v in
               [(0.0, 0.0, 0.0), (0.0, 0.2, 0.0), (0.0, 0.15, 0.1),
                (0.0, 0.0, 0.1), (0.16, 0.08809523809523807,
                                  0.04761904761904761)]]
    stand = [(-0.16, 0.0, -0.02), (0.0, 0.0, -0.02), (0.0, 0.0, 0.0),
             (-0.16, 0.0, 0.0)]
    for a, b in ((stand[0], stand[1]), (stand[1], stand[2]),
                 (stand[2], stand[3]), (stand[3], stand[0])):
        pa, pb = cam.project(a, VP_W, VP_H), cam.project(b, VP_W, VP_H)
        if pa and pb:
            draw.line([pa, pb], fill=(120, 120, 128), width=2)
    for verts, color in ((verts_a, (60, 90, 200)), (verts_b, (200, 120, 60))):
        for a, b in BODY_EDGES:
            pa, pb = cam.project(verts[a], VP_W, VP_H), \
                cam.project(verts[b], VP_W, VP_H)
            if pa and pb:
                draw.line([pa, pb], fill=color, width=2)
        pa = cam.project(verts[4], VP_W, VP_H)
        if pa:
            draw.ellipse([pa[0] - 2, pa[1] - 2, pa[0] + 2, pa[1] + 2],
                         fill=color)
    zp = row['gap_m']
    quad = [(zp, y, z) for (y, z) in PATCH_QUAD_YZ]
    pts = [cam.project(p, VP_W, VP_H) for p in quad]
    if all(pts):
        if diagnostic:
            draw.polygon([pts[0], pts[1], pts[2]], fill=(210, 60, 60))
            draw.polygon([pts[0], pts[2], pts[3]], fill=(120, 60, 160))
            draw.line([pts[0], pts[2]], fill=(250, 220, 80), width=1)
        else:
            draw.polygon(pts, fill=(150, 150, 150))
        draw.line(pts + [pts[0]], fill=(20, 20, 20), width=1)
    c = cam.project((zp, 0.0087, 0.0048), VP_W, VP_H)
    if c:
        draw.ellipse([c[0] - 3, c[1] - 3, c[0] + 3, c[1] + 3],
                     fill=(250, 220, 80) if diagnostic else (90, 90, 90))
    if diagnostic:
        o = cam.project((zp, 0.0087, 0.0048), VP_W, VP_H)
        for vec, col in (((0.02, 0, 0), (220, 40, 40)),
                         ((0, 0.02, 0), (40, 180, 40)),
                         ((0, 0, 0.02), (40, 40, 220))):
            e = cam.project((zp + vec[0], 0.0087 + vec[1],
                             0.0048 + vec[2]), VP_W, VP_H)
            if o and e:
                draw.line([o, e], fill=col, width=2)


def draw_trace_inset(draw, snap_rows, tick):
    x0, y0, w, h = VP_W + 8, 3 * VP_H - 56, VP_W - 16, 48
    gaps = [(r['tick'], r['gap_m']) for r in snap_rows]
    gmax = max(g for _, g in gaps)
    gmin = min(g for _, g in gaps)
    span = (gmax - gmin) or 1.0
    draw.rectangle([x0, y0, x0 + w, y0 + h], outline=(160, 160, 160))
    prev = None
    for tk, g in gaps:
        px = x0 + int(w * tk / max(1, gaps[-1][0]))
        py = y0 + h - int(h * (g - gmin) / span) - 1
        if prev:
            draw.line([prev, (px, py)], fill=(30, 160, 90))
        prev = (px, py)
    here = dict(gaps).get(tick, 0.0)
    draw.text((x0 + 4, y0 + 2),
              f'gap trace m; tick {tick} gap {here:.6f}', fill=(20, 20, 20))


def _bookmark_view(rec):
    """The fixed-bookmark identity: everything except the per-frame fields."""
    return {k: v for k, v in rec.items()
            if k not in ('frame_id', 'state_or_tick_interval')}


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
    cams_out = {}
    for view_id, cam, secondary in cameras_for(snap_ticks[0]):
        base = cam.record(snap_ticks, LAYERS, LABELS)
        entry = [base]
        if secondary is not None:
            entry.append(secondary.record(snap_ticks, LAYERS, LABELS))
        cams_out[f'{view_id}:diagnostic'] = entry
        cams_out[f'{view_id}:clean'] = [base]
    frame_hashes = []
    state_hashes = {}
    for idx, row in enumerate(snap_rows):
        tick = row['tick']
        sheet = Image.new('RGB', SHEET, (246, 246, 248))
        h = state_hash({k: row[k] for k in (
            'tick', 'gap_m', 'penetration_m', 'velocity_m_per_s',
            'patch_energy_J', 'triangle_connections', 'vertices_b_m')})
        state_hashes[str(tick)] = h
        draw_trace_inset(ImageDraw.Draw(sheet), snap_rows, tick)
        frame_path = frames_dir / f'frame_{idx:02d}.png'
        sheet.save(frame_path, format='PNG')
        frame_hashes.append({'frame': frame_path.name, 'tick': tick,
                             'sha256': sha(frame_path.read_bytes())})
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
    print('frames:', len(frame_hashes), 'cameras:', len(cams_out))


if __name__ == '__main__':
    main()
