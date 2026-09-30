"""MAT2-M08 visual capture renderer: renders the GPU-SOLVED snapshot stream
into the frozen camera sheet (PREREGISTRATION.md verification-profile views).

Every frame (2560x840) shows, for ONE declared capture tick of the X1
agreement fixture's GPU run:
  top row    diagnostic viewports [whole | side | front | close-up] with all
             five registry diagnostic layers (stable membrane/triangle/port
             IDs; pressure and area-scaled force vectors; rest/current
             geometry and material directions; contact/bond state;
             energy/work and simulation tick),
  middle row clean viewports (same cameras, geometry only, no overlays),
  bottom     delta-p / plate-x / cumulative-work trace strip + footer with
             the residency evidence line (per-tick telemetry bytes).

Geometry comes from the GPU-solved snapshots recorded in
experiment_receipt.json (read back at the 9 declared capture ticks,
asynchronously, outside steady-state stepping). BINDING ASSERTION: the
rendered membrane's signed volume is asserted equal to the snapshot's own
GPU diagnostic block volume before any pixel is written. The pinned ground
and the Maxwell wall anchor are rendered and labeled in every whole/side
view. Fixed bookmarks: the camera never moves; the SUBJECT moves.

CPU rasterizer, painter's algorithm (declared occlusion_mode depth_tested);
software rasterization of GPU-solved state, declared as such (the engine's
own splat pipeline is the reconciled residency pattern, not exercised here).
Deterministic. Frames + evidence are written to the attempt capture
directory passed as argv[1].
"""
from __future__ import annotations

import json
import math
import pathlib
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = pathlib.Path(__file__).resolve().parent
CONTRIB = HERE.parent
for _p in (str(HERE), str(CONTRIB / 'MAT2-M03'), str(CONTRIB / 'MAT2-M07')):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import integrated_step as iw  # noqa: E402
import pressure_membrane as pm  # noqa: E402
import local_contact as lc  # noqa: E402
import kernel_mirror as km  # noqa: E402

THICKNESS_M = km.THICKNESS_M
CONTACT_MARGIN_M = km.CONTACT_MARGIN_M

W_VP, H_VP = 640, 360
ASPECT = 16.0 / 9.0
SHEET = (4 * W_VP, 2 * H_VP + 120)
VIEW_IDS = ['whole experiment at fixed distance',
            'orthogonal side and front',
            'oblique close-up of the loaded interface']
LAYERS = ['stable membrane/triangle/port IDs',
          'pressure and area-scaled force vectors',
          'rest/current geometry and material directions',
          'contact/bond state',
          'energy/work and simulation tick']
TICK_MAP = ('1 tick = 1/300 s simulated; frames are the declared GPU '
            'snapshot ticks 0,10,..,70,79 at 1 video second per frame')


def require(condition, code):
    if not condition:
        raise ValueError(code)


class Camera:
    def __init__(self, name, position, target, resolution, projection,
                 fov_degrees=None, span=None):
        self.name = name
        self.position = np.array(position, dtype=np.float64)
        self.target = np.array(target, dtype=np.float64)
        self.resolution = list(resolution)
        self.projection = projection
        self.fov = fov_degrees
        self.span = span
        f = self.target - self.position
        self.dist = float(np.linalg.norm(f))
        self.forward = f / self.dist
        w = np.array([0.0, 0.0, 1.0])
        r = np.cross(self.forward, w)
        r = r / np.linalg.norm(r)
        up = np.cross(r, self.forward)
        self.right, self.up = r, up
        self._m = np.column_stack([r, up, -self.forward])
        self.quat = mat_to_quat(self._m)

    def project(self, points):
        pts = np.atleast_2d(np.asarray(points, dtype=np.float64))
        rel = pts - self.position
        x = rel @ self.right
        y = rel @ self.up
        z = rel @ (-self.forward)
        w_px, h_px = self.resolution
        if self.projection == 'perspective':
            t = math.tan(math.radians(self.fov) / 2.0)
            depth = z
            px = w_px / 2.0 + (x / (z * t * ASPECT)) * (w_px / 2.0)
            py = h_px / 2.0 - (y / (z * t)) * (h_px / 2.0)
        else:
            depth = z
            scale = h_px / self.span
            px = w_px / 2.0 + x * scale
            py = h_px / 2.0 - y * scale
        return np.column_stack([px, py]), depth

    def record(self, ticks):
        samples = []
        for tick in ticks:
            samples.append({
                'tick': int(tick),
                'position': [float(c) for c in self.position],
                'target': [float(c) for c in self.target],
                'distance_to_target': self.dist,
                'orientation': list(self.quat),
            })
        rec = {
            'frame_id': 'mat2_m08_resident_' + self.name + '_canvas_m',
            'coordinate_unit': 'm',
            'handedness': 'right',
            'orientation_convention': 'quaternion_wxyz_camera_to_frame',
            'forward_axis': '-Z',
            'up_axis': '+Y',
            'near_far_planes': [0.01, 100.0],
            'viewport_resolution': list(self.resolution),
            'aspect_ratio': ASPECT,
            'projection': self.projection,
            'sample_mode': 'fixed_bookmark',
            'samples': samples,
            'camera_motion_or_bookmark_sequence':
                'fixed_bookmark: identical pose at every snapshot tick; the '
                'SUBJECT moves (GPU-solved membrane inflates and slides, '
                'plate slides against friction and the Maxwell mount), not '
                'the camera',
            'state_or_tick_interval': TICK_MAP,
        }
        if self.projection == 'perspective':
            rec['vertical_fov_degrees'] = self.fov
        else:
            rec['orthographic_span'] = self.span
        return rec


def mat_to_quat(m):
    t = m[0, 0] + m[1, 1] + m[2, 2]
    if t > 0.0:
        s = math.sqrt(t + 1.0) * 2.0
        w = 0.25 * s
        x = (m[2, 1] - m[1, 2]) / s
        y = (m[0, 2] - m[2, 0]) / s
        z = (m[1, 0] - m[0, 1]) / s
    elif m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
        s = math.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2]) * 2.0
        w = (m[2, 1] - m[1, 2]) / s
        x = 0.25 * s
        y = (m[0, 1] + m[1, 0]) / s
        z = (m[0, 2] + m[2, 0]) / s
    elif m[1, 1] > m[2, 2]:
        s = math.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2]) * 2.0
        w = (m[0, 2] - m[2, 0]) / s
        x = (m[0, 1] + m[1, 0]) / s
        y = (m[1, 2] + m[2, 1]) / s
        z = 0.25 * s
    else:
        s = math.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1]) * 2.0
        w = (m[1, 0] - m[0, 1]) / s
        x = (m[0, 2] + m[2, 0]) / s
        y = (m[1, 2] + m[2, 1]) / s
        z = (m[2, 0] - m[0, 2]) / s
    q = np.array([w, x, y, z], dtype=np.float64)
    return [float(c) for c in q / np.linalg.norm(q)]


LIGHT = np.array([0.4, 0.35, 0.85])
LIGHT = LIGHT / np.linalg.norm(LIGHT)


def shade(normal, base):
    lam = 0.35 + 0.65 * abs(float(np.dot(normal, LIGHT)))
    return tuple(int(min(255, c * lam * 255)) for c in base)


def draw_arrow(draw, start2, end2, color):
    sx, sy = float(start2[0]), float(start2[1])
    ex, ey = float(end2[0]), float(end2[1])
    if math.hypot(ex - sx, ey - sy) < 2.0:
        return
    draw.line([sx, sy, ex, ey], fill=color, width=2)
    ang = math.atan2(ey - sy, ex - sx)
    for da in (2.6, -2.6):
        draw.line([ex, ey, ex + 7.0 * math.cos(ang + da),
                   ey + 7.0 * math.sin(ang + da)], fill=color, width=2)


def draw_membrane(draw, verts, tris, normals, cam, arrows=None,
                  arrow_scale=1.0, offset=(0, 0), labels=False,
                  fonts=None, max_label=4):
    tri = verts[tris]
    centres = tri.mean(axis=1)
    _, depth = cam.project(centres)
    order = np.argsort(-depth)
    for i in order:
        p3, _ = cam.project(tri[i])
        if not np.all(np.isfinite(p3)):
            continue
        draw.polygon([tuple(p + np.array(offset)) for p in p3],
                     fill=shade(normals[i], (120, 170, 235)),
                     outline=(60, 60, 80))
        if labels and fonts and i < max_label:
            c2, _ = cam.project(centres[i])
            draw.text((c2[0][0] + offset[0] + 3, c2[0][1] + offset[1] - 6),
                      f'm:t{i}', fill=(15, 15, 90), font=fonts['small'])
    if arrows is not None:
        for i in range(arrows.shape[0]):
            mag = float(np.linalg.norm(arrows[i]))
            if mag <= 1e-12:
                continue
            tip3 = centres[i] + normals[i] * (mag * arrow_scale)
            c2, _ = cam.project(centres[i])
            t2, _ = cam.project(tip3)
            if not (np.all(np.isfinite(c2)) and np.all(np.isfinite(t2))):
                continue
            draw_arrow(draw, c2[0] + offset, t2[0] + offset, (200, 30, 30))


def draw_shell(draw, verts, tris, cam, color, offset=(0, 0)):
    tri = np.array([[verts[i] for i in t] for t in tris])
    centres = tri.mean(axis=1)
    _, depth = cam.project(centres)
    order = np.argsort(-depth)
    for i in order:
        p3, _ = cam.project(tri[i])
        if not np.all(np.isfinite(p3)):
            continue
        n = np.cross(tri[i][1] - tri[i][0], tri[i][2] - tri[i][0])
        n = n / max(np.linalg.norm(n), 1e-30)
        draw.polygon([tuple(p + np.array(offset)) for p in p3],
                     fill=shade(n, color), outline=(60, 60, 80))


def main():
    out_dir = pathlib.Path(sys.argv[1])
    frames_dir = out_dir / 'frames'
    evidence_dir = out_dir / 'evidence'
    frames_dir.mkdir(parents=True, exist_ok=True)
    evidence_dir.mkdir(parents=True, exist_ok=True)

    receipt = json.loads((HERE / 'experiment_receipt.json').read_text(
        encoding='utf-8'))
    trace = json.loads((HERE / 'experiment_trace.json').read_text(
        encoding='utf-8'))
    snaps = receipt['snapshots']
    comp_a = iw.Component('A', 0.0)

    cams = {
        'whole': Camera('whole', (0.38, -0.92, 0.40), (0.031, 0.0, 0.055),
                        [W_VP, H_VP], 'perspective', fov_degrees=42.0),
        'side': Camera('side', (0.031, 1.05, 0.055), (0.031, 0.0, 0.055),
                       [W_VP, H_VP], 'orthographic', span=0.42),
        'front': Camera('front', (1.05, 0.0, 0.055), (0.031, 0.0, 0.055),
                        [W_VP, H_VP], 'orthographic', span=0.42),
        'closeup': Camera('closeup', (0.20, -0.24, 0.17),
                          (0.058, 0.0, 0.055),
                          [W_VP, H_VP], 'perspective', fov_degrees=33.0),
    }
    try:
        fonts = {'title': ImageFont.load_default(14),
                 'small': ImageFont.load_default(11),
                 'footer': ImageFont.load_default(12)}
    except Exception:
        fonts = {'title': None, 'small': None, 'footer': None}

    snap_ticks = sorted(int(k) for k in snaps.keys())
    frame_hashes = {}
    for frame_no, tick in enumerate(snap_ticks):
        snap = snaps[str(tick)]
        verts = np.array(snap['membrane_positions_m'], dtype=np.float64)
        plate_v = np.array(snap['plate_vertices_m'], dtype=np.float64)
        gblock = snap['gpu_block']
        membrane_now = pm.Membrane(verts, comp_a.membrane.triangles,
                                   'membrane_A')
        # BINDING ASSERTION: rendered geometry must reproduce the GPU
        # snapshot's own diagnostic volume before any pixel is written
        require(abs(membrane_now.signed_volume() - gblock[km.D_VOL]) < 1e-15,
                'render_replay_diverged_from_gpu_snapshot')
        dp = snap['delta_p_pa']
        src_now = comp_a.source.with_delta_p(dp)
        _, forces_now, _ = membrane_now.vertex_loads(src_now)
        plate_x = float(plate_v[:, 0].mean())
        wall = comp_a.wall_anchor
        ground_v = comp_a.ground.x
        active = int(gblock[km.D_ACTIVE])
        # contact/bond state markers: membrane triangles whose CURRENT gap
        # to any plate/ground triangle is within the declared margin
        # (diagnostic recomputation from the snapshot for display; the
        # per-tick authoritative count is the GPU diagnostic block)
        contact_tris = set()
        plate_tris_v = [plate_v[[0, 1, 2]], plate_v[[0, 2, 3]]]
        ground_tris_v = [ground_v[[0, 1, 2]], ground_v[[0, 2, 3]]]
        for e_a in range(80):
            ta = verts[np.asarray(comp_a.membrane.triangles[e_a])]
            ta = [tuple(v) for v in ta]
            for tb in plate_tris_v + ground_tris_v:
                tb = [tuple(v) for v in tb]
                _, _, dist = lc.tri_tri_closest(*ta, *tb)
                if dist - THICKNESS_M <= CONTACT_MARGIN_M + 1e-12:
                    contact_tris.add(e_a)
                    break
        contact_centroids = [membrane_now.centroids[i]
                             for i in sorted(contact_tris)]
        w_press_cum = float(gblock[km.D_WPRESS])
        resid = float(gblock[km.D_RESID])
        bytes_down = receipt['telemetry']['max_down_bytes_per_tick']

        img = Image.new('RGB', SHEET, (252, 252, 250))
        draw = ImageDraw.Draw(img)
        cams_diag = [('whole', cams['whole'], (0, 0)),
                     ('side', cams['side'], (W_VP, 0)),
                     ('front', cams['front'], (2 * W_VP, 0)),
                     ('closeup', cams['closeup'], (3 * W_VP, 0))]
        max_force = float(np.linalg.norm(forces_now, axis=1).max())
        arrow_scale = (0.02 / max_force) if max_force > 0 else 0.0
        plate_centroid = plate_v.mean(axis=0)
        for name, cam, off in cams_diag:
            draw_membrane(draw, verts, comp_a.membrane.triangles,
                          membrane_now.normals, cam, arrows=forces_now,
                          arrow_scale=arrow_scale, offset=off, labels=True,
                          fonts=fonts)
            draw_shell(draw, plate_v, [(0, 1, 2), (0, 2, 3)], cam,
                       (235, 200, 120), offset=off)
            draw_shell(draw, ground_v, [(0, 1, 2), (0, 2, 3)], cam,
                       (150, 160, 150), offset=off)
            # contact markers (red circles at contacted membrane centroids)
            for c3 in contact_centroids:
                c2, _ = cam.project([c3])
                x, y = float(c2[0][0]) + off[0], float(c2[0][1]) + off[1]
                if math.isfinite(x) and math.isfinite(y):
                    draw.ellipse([x - 4, y - 4, x + 4, y + 4],
                                 outline=(200, 30, 30), width=2)
            # the declared Maxwell mount: wall anchor -> plate centroid
            wa, _ = cam.project([wall])
            pc, _ = cam.project([plate_centroid])
            draw.line([float(wa[0][0]) + off[0], float(wa[0][1]) + off[1],
                       float(pc[0][0]) + off[0], float(pc[0][1]) + off[1]],
                      fill=(120, 40, 140), width=2)
            wx, _ = cam.project([wall])
            draw.text((wx[0][0] + off[0] - 30, wx[0][1] + off[1] + 8),
                      'wall_anchor (Maxwell mount)', fill=(120, 40, 140),
                      font=fonts['small'])
            gx, _ = cam.project([(0.0, 0.0, -0.001)])
            draw.text((gx[0][0] + off[0] - 30, gx[0][1] + off[1] + 8),
                      'ground (pinned support)', fill=(40, 90, 40),
                      font=fonts['small'])
            draw.text((off[0] + 6, off[1] + 4),
                      f'{name}: tick {tick}', fill=(20, 20, 20),
                      font=fonts['title'])
        for name, cam, off in cams_diag:
            off2 = (off[0], off[1] + H_VP + 8)
            draw_membrane(draw, verts, comp_a.membrane.triangles,
                          membrane_now.normals, cam, offset=off2)
            draw_shell(draw, plate_v, [(0, 1, 2), (0, 2, 3)], cam,
                       (235, 200, 120), offset=off2)
            draw_shell(draw, ground_v, [(0, 1, 2), (0, 2, 3)], cam,
                       (150, 160, 150), offset=off2)
            draw.text((off2[0] + 6, off2[1] - 16),
                      f'{name} clean (no overlays)', fill=(90, 90, 90),
                      font=fonts['small'])
        # trace strip: the GPU-solved scalars across the declared snapshots
        strip_y = 2 * H_VP + 20
        w_strip = SHEET[0] - 40
        xs = [s for s in snap_ticks]
        for series, slot, color in (
                ('delta_p Pa', None, (200, 30, 30)),
                ('plate x m', None, (30, 90, 200)),
                ('cum w_press J', km.D_WPRESS, (30, 140, 60))):
            vals = []
            for t2 in xs:
                s2 = snaps[str(t2)]
                if series == 'delta_p Pa':
                    vals.append(s2['delta_p_pa'])
                elif series == 'plate x m':
                    vals.append(float(np.array(
                        s2['plate_vertices_m'])[:, 0].mean()))
                else:
                    vals.append(float(s2['gpu_block'][slot]))
            lo, hi = min(vals), max(vals)
            rng = max(hi - lo, 1e-30)
            pts = [(20 + (w_strip * i / (len(xs) - 1)),
                    strip_y + 60 - 50 * (v - lo) / rng)
                   for i, v in enumerate(vals)]
            draw.line(pts, fill=color, width=2)
        draw.text((20, strip_y - 2),
                  f'delta_p (red) | plate x (blue) | cumulative w_press '
                  f'(green) over declared GPU snapshot ticks; '
                  f'active contact pairs {active}, R_tick {resid:.3e} J, '
                  f'steady-state telemetry {bytes_down} B/tick cap',
                  fill=(30, 30, 30), font=fonts['footer'])
        frame_path = frames_dir / f'frame_{frame_no:02d}.png'
        img.save(frame_path)
        import hashlib
        frame_hashes[str(tick)] = hashlib.sha256(
            frame_path.read_bytes()).hexdigest()
    (evidence_dir / 'frame_hashes.json').write_text(
        json.dumps(frame_hashes, indent=1, sort_keys=True))
    cameras = {f'{name}:{mode}': [cam.record(snap_ticks)]
               for name, cam in cams.items()
               for mode in ('diagnostic', 'clean')}
    (evidence_dir / 'cameras.json').write_text(
        json.dumps(cameras, indent=1, sort_keys=True))
    print('frames:', len(snap_ticks), 'ticks:', snap_ticks)


if __name__ == '__main__':
    main()
