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
TICK_MAP = ('1 tick = 1/300 s simulated; frames are the declared snapshot '
            'ticks 0,300,400,700,1000,1100,1200,1350,1499; even frames are '
            'the diagnostic sheets, odd frames the clean sheets '
            '(1 video second per snapshot)')

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
        z = rel @ (-self.forward)
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

    def record(self, snap_ticks):
        samples = []
        for tick in snap_ticks:
            samples.append({
                'tick': int(tick),
                'position': [float(c) for c in self.position],
                'target': [float(c) for c in self.target],
                'distance_to_target': self.dist,
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
            'orientation_convention_and_values':
                'quaternion_wxyz_camera_to_frame, forward -Z / up +Y, '
                'fixed bookmark',
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


def render_snapshot(model, snap, row_lookup, tick, diag):
    sheet = np.full((H_SHEET, W_SHEET, 3), 24, dtype=np.uint8)
    img = Image.fromarray(sheet, 'RGB')
    draw = ImageDraw.Draw(img)
    verts = np.array(snap['x'], dtype=np.float64)
    x_load = np.array(snap['x_load'], dtype=np.float64)
    dp = float(snap['delta_p_pa'])
    # binding assertions BEFORE any pixel is written (snapshot tick T is
    # the state after T completed ticks = trace row T-1)
    row = row_lookup[tick - 1]
    require(abs(float(row['volume_m3']) - float(snap['volume_m3'])) <= 1e-9,
            'bind_volume_mismatch:%d' % tick)
    pole_z = float(verts[model.south, 2])
    require(abs(pole_z - float(row['z_tip_m'])) <= 1e-9,
            'bind_pole_mismatch:%d' % tick)

    cams = [
        ('whole', Camera('whole', (0.30, -0.42, 0.26), (0.0, 0.0, -0.045),
                         'perspective', fov_degrees=40)),
        ('side', Camera('side', (0.0, 0.62, -0.05), (0.0, 0.0, -0.05),
                        'orthographic', span=0.40)),
        ('front', Camera('front', (0.62, 0.0, -0.05), (0.0, 0.0, -0.05),
                         'orthographic', span=0.40)),
        ('closeup', Camera('closeup', (0.09, -0.13, -0.02), (0.0, 0.0, -0.05),
                           'perspective', fov_degrees=30)),
    ]
    origins = [(4, 4), (484, 4), (4, 268), (484, 268)]
    names = ['whole', 'side', 'front', 'close-up']
    for ci, (cname, cam) in enumerate(cams):
        ox, oy = origins[ci]
        vp = ((ox, oy), (VP_W, VP_H))
        draw.rectangle([ox, oy, ox + VP_W, oy + VP_H],
                       outline=(90, 92, 104))
        draw_shell(draw, cam, verts, model.tris, vp)
        if diag:
            draw_chords(draw, cam, verts, model.chords, vp)
            draw_pressure_arrows(draw, cam, verts, model.tris, vp, dp)
            # clamp ring (visible support) + tie + load
            cl = verts[model.clamp_idx]
            px, _ = cam.project(cl, vp[0], vp[1][0], vp[1][1])
            for p in px:
                if ox <= p[0] <= ox + VP_W and oy <= p[1] <= oy + VP_H:
                    draw.ellipse([p[0] - 3, p[1] - 3, p[0] + 3, p[1] + 3],
                                 fill=(255, 70, 70))
            sp = verts[model.south]
            pt, _ = cam.project(np.vstack([sp, x_load]), vp[0], vp[1][0],
                                vp[1][1])
            draw.line([(pt[0][0], pt[0][1]), (pt[1][0], pt[1][1])],
                      fill=(0, 170, 255), width=2)
            draw.ellipse([pt[1][0] - 5, pt[1][1] - 5, pt[1][0] + 5,
                          pt[1][1] + 5], fill=(60, 60, 225))
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
                if ox <= p[0][0] <= ox + VP_W and oy <= p[0][1] <= oy + VP_H:
                    draw.text((p[0][0] + 4, p[0][1] - 6), name, fill=col)
            draw.text((ox + 4, oy + 2),
                      '%s | diagnostic | tick %d | dp %.0f Pa'
                      % (names[ci], tick, dp), fill=(230, 230, 230))
        else:
            draw.text((ox + 4, oy + 2),
                      '%s | clean | tick %d' % (names[ci], tick),
                      fill=(160, 160, 160))
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
    cameras = [Camera('whole', (0.30, -0.42, 0.26), (0.0, 0.0, -0.045),
                      'perspective', fov_degrees=40),
               Camera('side', (0.0, 0.62, -0.05), (0.0, 0.0, -0.05),
                      'orthographic', span=0.40),
               Camera('front', (0.62, 0.0, -0.05), (0.0, 0.0, -0.05),
                      'orthographic', span=0.40),
               Camera('closeup', (0.09, -0.13, -0.02), (0.0, 0.0, -0.05),
                      'perspective', fov_degrees=30)]
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
    (evidence_dir / 'cameras.json').write_text(
        json.dumps({'cameras': cam_records, 'view_ids': VIEW_IDS,
                    'subjects': SUBJECTS, 'labels': LABELS,
                    'tick_map': TICK_MAP, 'sheet': [W_SHEET, H_SHEET],
                    'still_indices': [0, 8, 10, 16],
                    'still_frame_indices_declared': aw.STILL_INDICES,
                    'row_order_proof': proof,
                    'frame_raw_sha256': frame_hashes,
                    'still_hashes': still_hashes},
                   indent=1, sort_keys=True) + '\n', encoding='utf-8',
        newline='\n')
    print('rendered %d frames (%d snapshots x2), stills %d'
          % (len(frame_hashes), len(snap_ticks), len(still_hashes)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
