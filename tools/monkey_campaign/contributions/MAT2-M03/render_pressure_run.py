"""MAT2-M03 visual capture renderer: renders the committed pressure run into
the frozen camera sheet (PREREGISTRATION.md, corrections A1-A5).

Every frame (2560x840) shows, for ONE tick:
  top row    diagnostic viewports [whole | side | front | close-up] with the
             packet's five diagnostic layers (IDs, area-scaled force vectors,
             rest/current geometry, contact/bond declaration, energy/work and
             tick),
  middle row clean viewports (same cameras, no labels, no overlays),
  bottom     pressure/volume/work traces and the honest footer.

CPU rasterizer, painter's algorithm (declared occlusion_mode depth_tested);
display of solver state, not a GPU render. Deterministic. Frames + evidence
are written to the attempt capture directory passed as argv[1].
Run from this directory:
    python -B render_pressure_run.py <attempt_capture_dir>
"""
from __future__ import annotations

import json
import math
import pathlib
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'MAT2-M01'))

import pressure_membrane as pm  # noqa: E402

TICKS = 24
W_VP, H_VP = 640, 360
VP_RES = [W_VP, H_VP]
ASPECT = 16.0 / 9.0
SHEET = (4 * W_VP, 2 * H_VP + 120)

VIEWS = ['whole experiment at fixed distance', 'orthogonal side and front',
         'oblique close-up of the loaded interface']
LAYERS = ['stable membrane/triangle/port IDs',
          'pressure and area-scaled force vectors',
          'rest/current geometry and material directions',
          'contact/bond state',
          'energy/work and simulation tick']

VIEW_IDS = ['whole experiment at fixed distance',
            'orthogonal side and front',
            'oblique close-up of the loaded interface']

R0 = 0.10
TICKS_SLOWMO = '1 tick = 1/300 s simulated, replayed at 1 video second per tick (slow motion x300)'


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
            'frame_id': 'mat2_m03_' + self.name + '_canvas_m',
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
                'fixed_bookmark: identical pose at both sample ticks; the '
                'SUBJECT moves (membrane inflates/deflates; tetra traction '
                'arrows grow), not the camera',
            'state_or_tick_interval': TICKS_SLOWMO
                + '; tick_interval [0, 23]',
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
        y = 0.25 * s
        z = (m[1, 2] + m[2, 1]) / s
    else:
        s = math.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1]) * 2.0
        w = (m[1, 0] - m[0, 1]) / s
        x = (m[0, 2] + m[2, 0]) / s
        y = (m[1, 2] + m[2, 1]) / s
        z = 0.25 * s
    q = np.array([w, x, y, z], dtype=np.float64)
    return [float(c) for c in q / np.linalg.norm(q)]


# ------------------------------------------------------------- painter ------
LIGHT = np.array([0.4, 0.35, 0.85])
LIGHT = LIGHT / np.linalg.norm(LIGHT)


def shade(normal, base):
    lam = 0.35 + 0.65 * abs(float(np.dot(normal, LIGHT)))
    return tuple(int(min(255, c * lam * 255)) for c in base)


def draw_membrane(draw, membrane, cam, color, arrows=None, arrow_scale=1.0,
                  arrow_color=(220, 40, 40), edge=(60, 60, 80),
                  label_prefix=None, fonts=None, rest_mesh=None,
                  offset=(0, 0)):
    tri = membrane.vertices[membrane.triangles]
    centres = tri.mean(axis=1)
    pts, depth = cam.project(centres)
    order = np.argsort(-depth)          # far first
    for i in order:
        p3 = cam.project(tri[i])[0]
        if not np.all(np.isfinite(p3)):
            continue
        n = membrane.normals[i]
        col = shade(n, color)
        draw.polygon([tuple(p + np.array(offset)) for p in p3],
                     fill=col, outline=edge)
    if arrows is not None:
        forces = arrows
        for i in range(forces.shape[0]):
            mag = float(np.linalg.norm(forces[i]))
            if mag <= 1e-12:
                continue
            tip3 = centres[i] + membrane.normals[i] * (mag * arrow_scale)
            c2, = cam.project(centres[i])[0]
            t2, = cam.project(tip3)[0]
            if not (np.all(np.isfinite(c2)) and np.all(np.isfinite(t2))):
                continue
            draw_arrow(draw, c2 + offset, t2 + offset, arrow_color)
            if label_prefix and fonts:
                mid = (c2 + t2) / 2.0 + np.array(offset)
                draw.text((mid[0] + 3, mid[1] - 6),
                          f'{label_prefix}t{i} A={membrane.areas[i]:.4f}',
                          fill=(20, 20, 20), font=fonts['small'])


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


def draw_ghost_sphere(draw, cam, radius, color=(120, 120, 130),
                      offset=(0, 0)):
    for phase in np.linspace(0.0, math.pi, 13):
        circle = np.column_stack([
            radius * np.cos(np.linspace(0, 2 * math.pi, 49)),
            radius * np.sin(np.linspace(0, 2 * math.pi, 49)),
            np.zeros(49)])
        rot = circle @ np.column_stack([
            np.array([1.0, 0.0, 0.0]),
            np.array([0.0, math.cos(phase), math.sin(phase)]),
            np.array([0.0, -math.sin(phase), math.cos(phase)])])
        pts, depth = cam.project(rot)
        draw.line([tuple(p + np.array(offset)) for p in pts], fill=color,
                  width=1)


# ----------------------------------------------------------------- main -----
def main():
    out_dir = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 \
        else HERE / 'capture_out'
    frames_dir = out_dir / 'frames'
    evidence_dir = out_dir / 'evidence'
    frames_dir.mkdir(parents=True, exist_ok=True)
    evidence_dir.mkdir(parents=True, exist_ok=True)

    trace = json.loads((HERE / 'pressure_trace.json').read_text(
        encoding='utf-8'))
    dyn = trace['dynamic']['ticks']
    tetra = pm.load_m02_tetra(str(HERE.parent))
    sphere_rest = pm.icosphere(1, R0)

    slant = tetra.vertices[tetra.triangles[3]]
    slant_centroid = slant.mean(axis=0)
    cams = {
        'whole': Camera('whole', (2.2, 1.6, 1.2), (0.18, -0.07, 0.0), VP_RES,
                        'perspective', fov_degrees=40.0),
        'side': Camera('side', (3.0, 0.0, 0.0), (0.18, -0.07, 0.0), VP_RES,
                       'orthographic', span=1.4),
        'front': Camera('front', (0.0, -3.0, 0.0), (0.18, -0.07, 0.0), VP_RES,
                        'orthographic', span=1.4),
        'closeup': Camera('closeup',
                          tuple(slant_centroid + np.array([0.66, -0.42,
                                                           0.45])),
                          tuple(slant_centroid), VP_RES, 'perspective',
                          fov_degrees=30.0),
    }

    try:
        from PIL import ImageFont
        fonts = {'title': ImageFont.load_default(14),
                 'small': ImageFont.load_default(11),
                 'footer': ImageFont.load_default(12)}
    except Exception:
        fonts = {'title': None, 'small': None, 'footer': None}

    frame_hashes = {}
    for tick in range(TICKS):
        row = dyn[tick]
        dp = row['delta_p_pa']
        src_now = pm.PressureSource('render', max(dp, 0.0) if dp >= 0 else 0.0,
                                    0.0, 5000.0, 1e-3, 'render-time source '
                                    'declared from the committed trace row')
        img = Image.new('RGB', SHEET, (252, 252, 250))
        draw = ImageDraw.Draw(img)
        state_hash = pm.digest(row)

        # current membrane (recomputed from the committed trace geometry? the
        # trace stores scalars; geometry is recomputed by replaying the run)
        positions = row.get('positions_m')
        if positions is None:
            membrane_now = replay_positions()[tick]
        else:
            membrane_now = pm.Membrane(np.array(positions),
                                       sphere_rest.triangles, 'membrane')
        loads_now, forces_now, _ = membrane_now.vertex_loads(src_now)

        panels = [
            ('whole', 0), ('side', 1), ('front', 2), ('closeup', 3)]
        for col, (cam_name, _) in enumerate(panels):
            for row_idx, mode in ((0, 'diagnostic'), (1, 'clean')):
                x0 = col * W_VP
                y0 = row_idx * H_VP
                cam = cams[cam_name]
                view_label = {'whole': VIEW_IDS[0], 'side': VIEW_IDS[1],
                              'front': VIEW_IDS[1],
                              'closeup': VIEW_IDS[2]}[cam_name]
                if mode == 'clean':
                    if cam_name == 'closeup':
                        draw_membrane(draw, tetra, cam, (235, 205, 160),
                                      offset=(x0, y0))
                    else:
                        draw_ghost_sphere(draw, cam, R0, offset=(x0, y0))
                        draw_membrane(draw, membrane_now, cam, (70, 120, 210),
                                      offset=(x0, y0))
                        draw_membrane(draw, tetra, cam, (235, 205, 160),
                                      offset=(x0, y0))
                    title = f'{view_label} | clean | tick {tick}'
                    draw.rectangle([x0, y0, x0 + W_VP - 1, y0 + H_VP - 1],
                                   outline=(160, 160, 160))
                else:
                    if cam_name == 'closeup':
                        forces_t, _ = tetra.triangle_tractions(src_now)
                        draw_membrane(draw, tetra, cam, (245, 210, 150),
                                      arrows=forces_t, arrow_scale=0.08,
                                      label_prefix='m02_tetra/',
                                      fonts=fonts, offset=(x0, y0))
                    else:
                        draw_ghost_sphere(draw, cam, R0, offset=(x0, y0))
                        every = 8
                        sub_forces = np.zeros_like(forces_now)
                        sub_forces[::every] = forces_now[::every]
                        draw_membrane(draw, membrane_now, cam,
                                      (70, 120, 210), arrows=sub_forces,
                                      arrow_scale=0.29,
                                      arrow_color=(200, 30, 30),
                                      offset=(x0, y0))
                        draw_membrane(draw, tetra, cam, (245, 210, 150),
                                      offset=(x0, y0))
                    title = f'{view_label} | diagnostic | tick {tick} | ' \
                            f'dp={dp:.1f} Pa'
                    draw.rectangle([x0, y0, x0 + W_VP - 1, y0 + H_VP - 1],
                                   outline=(90, 90, 90))
                draw.text((x0 + 6, y0 + 4), title, fill=(20, 20, 20),
                          font=fonts['title'])
                if mode == 'diagnostic':
                    layers_txt = ('layers: IDs | area-scaled force vectors | '
                                  'rest(gray)/current geometry | contacts: '
                                  'none | bonds: none | tick')
                    draw.text((x0 + 6, y0 + H_VP - 46), layers_txt,
                              fill=(60, 60, 160), font=fonts['small'])
                    draw.text((x0 + 6, y0 + H_VP - 32),
                              f'membrane V={row["volume_m3"]:.3e} m^3 '
                              f'W_press={row["w_pressure_j"]:+.2e} J '
                              f'COM drift={row["com_drift_m"]:.1e} m',
                              fill=(60, 60, 160), font=fonts['small'])
                    draw.text((x0 + 6, y0 + H_VP - 18),
                              f'port pressure_inlet | state {state_hash[:12]}',
                              fill=(60, 60, 160), font=fonts['small'])

        # traces strip
        y_base = 2 * H_VP + 8
        draw_traces(draw, dyn, tick, y_base, fonts)
        footer = (f'frame {tick:02d} | tick {tick} (={tick}/300 s simulated, '
                  f'replayed x300) | sheets: top diagnostic, middle clean | '
                  f'ortho span 1.4 m (side/front) | state {state_hash[:16]}')
        draw.text((8, SHEET[1] - 16), footer, fill=(30, 30, 30),
                  font=fonts['footer'])
        frame_path = frames_dir / f'frame_{tick:02d}.png'
        img.save(frame_path)
        frame_hashes[frame_path.name] = pm.sha256_file(frame_path)

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


_POS_CACHE = None


def replay_positions():
    """Replay the committed run deterministically to recover per-tick vertex
    positions (the trace stores scalars; geometry must be bound to solver
    state, not regenerated)."""
    global _POS_CACHE
    if _POS_CACHE is not None:
        return _POS_CACHE
    import run_experiment as rx
    dyn_source = pm.PressureSource('mat2_m03_membrane', rx.PEAK_PA, 0.0,
                                   5000.0, 1e-3, rx.SOURCE_DECL)
    run = pm.InflatableRun(pm.icosphere(1, rx.R0_M), dyn_source,
                           rx.TOTAL_MASS_KG, rx.COMPLIANCE, rx.DAMPING,
                           rx.ITERATIONS, rx.DT_S)
    membranes = []
    for tick in range(rx.TICKS):
        row = run.step(rx.ramp(tick), tick)
        membranes.append(run.current_membrane())
        assert abs(row['volume_m3'] - _trace_volume(tick)) < 1e-15, \
            'render replay diverged from committed trace'
    _POS_CACHE = membranes
    return _POS_CACHE


def _trace_volume(tick):
    trace = json.loads((HERE / 'pressure_trace.json').read_text(
        encoding='utf-8'))
    return trace['dynamic']['ticks'][tick]['volume_m3']


def draw_traces(draw, dyn, tick, y_base, fonts):
    panel_w = (SHEET[0] - 16) // 3
    series = {
        'pressure dP (Pa)': [t['delta_p_pa'] for t in dyn],
        'volume (m^3)': [t['volume_m3'] for t in dyn],
        'cumulative pressure work (J)': None,
    }
    cum = 0.0
    cum_work = []
    for t in dyn:
        cum += t['w_pressure_j']
        cum_work.append(cum)
    series['cumulative pressure work (J)'] = cum_work
    for idx, (label, data) in enumerate(series.items()):
        x0 = 8 + idx * panel_w
        y0 = y_base
        w, h = panel_w - 16, 84
        draw.rectangle([x0, y0, x0 + w, y0 + h], outline=(120, 120, 120))
        lo, hi = min(data), max(data)
        if hi - lo < 1e-12:
            hi = lo + 1e-12
        pts = [(x0 + (i / max(1, len(data) - 1)) * w,
                y0 + h - (v - lo) / (hi - lo) * (h - 8) - 4)
               for i, v in enumerate(data[:tick + 1])]
        if len(pts) > 1:
            draw.line(pts, fill=(180, 30, 30), width=2)
        draw.text((x0 + 4, y0 + 2),
                  f'{label} [{lo:.3e} .. {hi:.3e}] tick {tick}',
                  fill=(20, 20, 20), font=fonts['small'])


if __name__ == '__main__':
    sys.exit(main())
