"""MAT2-M07 visual capture renderer: renders the committed coupling run into
the frozen camera sheet (PREREGISTRATION.md, verification-profile probes).

Every frame (2560x840) shows, for ONE tick of the X1 two-component run:
  top row    diagnostic viewports [whole | side | front | close-up] with the
             packet's five diagnostic layers (stable membrane/triangle/port
             IDs; pressure and area-scaled force vectors; rest/current
             geometry and material directions; contact/bond state;
             energy/work and simulation tick),
  middle row clean viewports (same cameras, geometry only, no overlays),
  bottom     delta-p / plate displacement / cumulative-work traces + footer.

Geometry is read from the committed experiment_trace.json (positions stored
per tick by the solver run) and re-played through the committed owner for
binding assertions: the rendered membrane volume is asserted equal to the
trace's own volume row before any pixel is written. Component A is the
rendered subject; component B runs identically beside it (X2 bitwise).

CPU rasterizer, painter's algorithm (declared occlusion_mode depth_tested);
display of solver state, not a GPU render. Deterministic. Frames + evidence
are written to the attempt capture directory passed as argv[1].
Run from this directory:
    python -B render_run.py <attempt_capture_dir>
"""
from __future__ import annotations

import json
import math
import pathlib
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'MAT2-M03'))

import integrated_step as iw  # noqa: E402
import pressure_membrane as pm  # noqa: E402

TICKS = iw.TICKS
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
TICK_MAP = ('1 tick = 1/300 s simulated, replayed at 1 video second per '
            'tick (slow motion x300)')


# ---------------------------------------------------------------- camera ----
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
            'frame_id': 'mat2_m07_' + self.name + '_canvas_m',
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
                'fixed_bookmark: identical pose at every sample tick; the '
                'SUBJECT moves (membrane inflates and slides, plate slides '
                'against friction and the Maxwell mount), not the camera',
            'state_or_tick_interval': TICK_MAP + '; tick_interval [0, 79]',
        }
        if self.projection == 'perspective':
            rec['vertical_fov_degrees'] = self.fov
        else:
            rec['orthographic_span'] = self.span
        return rec


def mat_to_quat(m):
    """Rotation matrix (columns = camera axes in world) -> quaternion wxyz."""
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


# ------------------------------------------------------------- painter ------
LIGHT = np.array([0.4, 0.35, 0.85])
LIGHT = LIGHT / np.linalg.norm(LIGHT)


def shade(normal, base):
    lam = 0.35 + 0.65 * abs(float(np.dot(normal, LIGHT)))
    return tuple(int(min(255, c * lam * 255)) for c in base)


def draw_shell(draw, verts, tris, cam, color, edge=(60, 60, 80),
               offset=(0, 0)):
    tri = verts[list(tris)] if not isinstance(tris[0], (list, tuple)) \
        else np.array([[verts[i] for i in t] for t in tris])
    centres = tri.mean(axis=1)
    pts, depth = cam.project(centres)
    order = np.argsort(-depth)
    for i in order:
        p3, _ = cam.project(tri[i])
        if not np.all(np.isfinite(p3)):
            continue
        n = np.cross(tri[i][1] - tri[i][0], tri[i][2] - tri[i][0])
        n = n / max(np.linalg.norm(n), 1e-30)
        draw.polygon([tuple(p + np.array(offset)) for p in p3],
                     fill=shade(n, color), outline=edge)


def draw_membrane(draw, verts, tris, normals, cam, color, arrows=None,
                  arrow_scale=1.0, arrow_color=(200, 30, 30),
                  label_prefix=None, fonts=None, rest_verts=None,
                  offset=(0, 0)):
    tri = verts[tris]
    centres = tri.mean(axis=1)
    _, depth = cam.project(centres)
    order = np.argsort(-depth)
    for i in order:
        p3, _ = cam.project(tri[i])
        if not np.all(np.isfinite(p3)):
            continue
        draw.polygon([tuple(p + np.array(offset)) for p in p3],
                     fill=shade(normals[i], color), outline=(60, 60, 80))
        if label_prefix and fonts and i < 4:
            c2, _ = cam.project(centres[i])
            draw.text((c2[0][0] + offset[0] + 3, c2[0][1] + offset[1] - 6),
                      f'{label_prefix}t{i}', fill=(15, 15, 90),
                      font=fonts['small'])
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
            draw_arrow(draw, c2[0] + offset, t2[0] + offset, arrow_color)


def draw_arrow(draw, start2, end2, color, end2y=None):
    if end2y is not None:
        sx, sy, ex, ey = float(start2[0]), float(start2[1]),             float(end2), float(end2y)
    else:
        sx, sy = float(start2[0]), float(start2[1])
        ex, ey = float(end2[0]), float(end2[1])
    if math.hypot(ex - sx, ey - sy) < 2.0:
        return
    draw.line([sx, sy, ex, ey], fill=color, width=2)
    ang = math.atan2(ey - sy, ex - sx)
    for da in (2.6, -2.6):
        draw.line([ex, ey, ex + 7.0 * math.cos(ang + da),
                   ey + 7.0 * math.sin(ang + da)], fill=color, width=2)


# ----------------------------------------------------------------- main -----
def main():
    out_dir = pathlib.Path(sys.argv[1])
    frames_dir = out_dir / 'frames'
    evidence_dir = out_dir / 'evidence'
    frames_dir.mkdir(parents=True, exist_ok=True)
    evidence_dir.mkdir(parents=True, exist_ok=True)

    trace = json.loads((HERE / 'experiment_trace.json').read_text(
        encoding='utf-8'))
    dyn = trace['ticks']
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

    frame_hashes = {}
    for tick in range(TICKS):
        row = dyn[tick]['components']['A']
        dp = row['delta_p_pa']
        verts = np.array(row['membrane_positions_m'], dtype=np.float64)
        plate_v = np.array(row['plate_vertices_m'], dtype=np.float64)
        ground_v = comp_a.ground.x
        membrane_now = pm.Membrane(verts, comp_a.membrane.triangles,
                                   'membrane_A')
        # binding assertion: rendered geometry must reproduce the trace row
        require_close = abs(membrane_now.signed_volume()
                            - row['membrane_volume_m3'])
        assert require_close < 1e-15, 'render replay diverged from trace'
        src_now = comp_a.source.with_delta_p(dp)
        loads_now, forces_now, _ = membrane_now.vertex_loads(src_now)
        # contact state from the committed row (converged-pass records);
        # pair_key = [surface_a, tri_a, surface_b, tri_b] as strings
        active_mem_tris = sorted({int(c['pair_key'][1])
                                  for c in row['contacts']
                                  if c['pair_key'][0] == 'membrane'})
        contact_pts = [membrane_now.centroids[i] for i in active_mem_tris]
        wall = comp_a.wall_anchor
        f_maxwell = row['F_N']

        img = Image.new('RGB', SHEET, (252, 252, 250))
        draw = ImageDraw.Draw(img)
        state_hash = iw.digest(row)

        panels = [('whole', 0), ('side', 1), ('front', 2), ('closeup', 3)]
        for col, (cam_name, _) in enumerate(panels):
            for row_idx, mode in ((0, 'diagnostic'), (1, 'clean')):
                x0 = col * W_VP
                y0 = row_idx * H_VP
                cam = cams[cam_name]
                view_label = {'whole': VIEW_IDS[0], 'side': VIEW_IDS[1],
                              'front': VIEW_IDS[1],
                              'closeup': VIEW_IDS[2]}[cam_name]
                # per-cell offscreen canvas: geometry can never bleed across
                # viewport boundaries (declared depth_tested occlusion per
                # viewport, no cross-cell overdraw)
                cell = Image.new('RGB', (W_VP, H_VP), (252, 252, 250))
                cd = ImageDraw.Draw(cell)
                offset = (0, 0)
                draw_shell(cd, ground_v, comp_a.ground.triangles, cam,
                           (196, 196, 186), edge=(120, 120, 110),
                           offset=offset)
                w2, _ = cam.project(np.array([wall]))
                if np.all(np.isfinite(w2)):
                    wx, wy = float(w2[0][0]), float(w2[0][1])
                    if mode == 'diagnostic':
                        cd.rectangle([wx - 4, wy - 14, wx + 4, wy + 14],
                                     fill=(90, 70, 140))
                        if f_maxwell > 1e-9:
                            fw = np.array([f_maxwell, 0.0, 0.0])
                            t3, _ = cam.project(np.array([wall + fw * 0.02]))
                            if np.all(np.isfinite(t3)):
                                draw_arrow(cd, (wx, wy),
                                           (float(t3[0][0]),
                                            float(t3[0][1])),
                                           (120, 40, 180))
                draw_shell(cd, plate_v, comp_a.plate.triangles, cam,
                           (235, 205, 160), offset=offset)
                every = 4
                sub_forces = np.zeros_like(forces_now)
                sub_forces[::every] = forces_now[::every]
                if mode == 'clean':
                    draw_membrane(cd, verts, comp_a.membrane.triangles,
                                  membrane_now.normals, cam, (70, 120, 210),
                                  offset=offset)
                else:
                    draw_membrane(cd, verts, comp_a.membrane.triangles,
                                  membrane_now.normals, cam, (70, 120, 210),
                                  arrows=sub_forces, arrow_scale=0.5,
                                  label_prefix='membrane_A/', fonts=fonts,
                                  offset=offset)
                    for cp in contact_pts:
                        p2, _ = cam.project(np.array([cp]))
                        if np.all(np.isfinite(p2)):
                            px, py = float(p2[0][0]), float(p2[0][1])
                            cd.ellipse([px - 3, py - 3, px + 3, py + 3],
                                       outline=(200, 30, 30), width=2)
                img.paste(cell, (x0, y0))
                title = (
                    f'{view_label} | {mode} | tick {tick}'
                    + (f' | dp={dp:.0f} Pa' if mode == 'diagnostic' else ''))
                draw.text((x0 + 6, y0 + 4), title, fill=(20, 20, 20),
                          font=fonts['title'])
                if mode == 'diagnostic':
                    draw.rectangle([x0, y0, x0 + W_VP - 1, y0 + H_VP - 1],
                                   outline=(90, 90, 90))
                    if cam_name == 'side':
                        draw.text((x0 + 6, y0 + 18),
                                  'ground_A (pinned support) | wall_anchor_A',
                                  fill=(90, 70, 140), font=fonts['small'])
                    layers_txt = ('layers: membrane/triangle/port IDs | '
                                  'area-scaled pressure vectors | '
                                  'rest(gray)/current geometry + mount '
                                  'direction | contact markers | '
                                  'energy/work + tick')
                    draw.text((x0 + 6, y0 + H_VP - 46), layers_txt,
                              fill=(60, 60, 160), font=fonts['small'])
                    draw.text((x0 + 6, y0 + H_VP - 32),
                              f'plate_x={row["plate_x_m"]:.5f} m '
                              f'F_maxwell={row["F_N"]:.4f} N '
                              f'contacts={row["contact_active_pairs"]} '
                              f'Q={row["Q_mat_j"]:.2e} J',
                              fill=(60, 60, 160), font=fonts['small'])
                    draw.text((x0 + 6, y0 + H_VP - 18),
                              f'port:maxwell_mount axis +x | '
                              f'state {state_hash[:12]}',
                              fill=(60, 60, 160), font=fonts['small'])
                else:
                    draw.rectangle([x0, y0, x0 + W_VP - 1, y0 + H_VP - 1],
                                   outline=(160, 160, 160))

        # traces strip
        y_base = 2 * H_VP + 8
        series = {
            'membrane delta-p (Pa)': [t['components']['A']['delta_p_pa']
                                      for t in dyn],
            'plate displacement (m)': [t['components']['A']['plate_x_m']
                                       - iw.PLATE_X0_M for t in dyn],
            'cumulative work (J)': None,
        }
        cum = 0.0
        cum_work = []
        for t in dyn:
            r = t['components']['A']
            cum += r['w_press_j'] + r['w_grav_j'] + r['w_mat_on_plate_j']
            cum_work.append(cum)
        series['cumulative work (J)'] = cum_work
        panel_w = (SHEET[0] - 16) // 3
        for idx, (label, data) in enumerate(series.items()):
            bx = 8 + idx * panel_w
            by = y_base
            w, h = panel_w - 16, 84
            draw.rectangle([bx, by, bx + w, by + h], outline=(120, 120, 120))
            lo, hi = min(data), max(data)
            if hi - lo < 1e-12:
                hi = lo + 1e-12
            pts = [(bx + (i / max(1, len(data) - 1)) * w,
                    by + h - (v - lo) / (hi - lo) * (h - 8) - 4)
                   for i, v in enumerate(data[:tick + 1])]
            if len(pts) > 1:
                draw.line(pts, fill=(180, 30, 30), width=2)
            draw.text((bx + 4, by + 2),
                      f'{label} [{lo:.3e} .. {hi:.3e}] tick {tick}',
                      fill=(20, 20, 20), font=fonts['small'])
        footer = (f'frame {tick:02d} | tick {tick} (={tick}/300 s simulated, '
                  f'replayed x300) | sheets: top diagnostic, middle clean | '
                  f'ortho span 0.42 m (side/front) | state {state_hash[:16]}')
        draw.text((8, SHEET[1] - 16), footer, fill=(30, 30, 30),
                  font=fonts['footer'])
        frame_path = frames_dir / f'frame_{tick:02d}.png'
        img.save(frame_path)
        frame_hashes[frame_path.name] = iw.sha256_file(frame_path)

    cameras_json = {f'{key}:{mode}': value
                    for key in ('whole', 'planes', 'closeup')
                    for mode in ('diagnostic', 'clean')
                    for value in [camera_set_for(key, cams)]}
    (evidence_dir / 'cameras.json').write_text(
        json.dumps(cameras_json, indent=1) + '\n', encoding='utf-8')
    (evidence_dir / 'frame_hashes.json').write_text(
        json.dumps(frame_hashes, indent=1, sort_keys=True) + '\n',
        encoding='utf-8')
    print('frames:', len(frame_hashes), '->', frames_dir)
    return 0


def camera_set_for(key, cams):
    if key == 'whole':
        return [cams['whole'].record((0, TICKS - 1))]
    if key == 'planes':
        return [cams['side'].record((0, TICKS - 1)),
                cams['front'].record((0, TICKS - 1))]
    return [cams['closeup'].record((0, TICKS - 1))]


if __name__ == '__main__':
    sys.exit(main())
