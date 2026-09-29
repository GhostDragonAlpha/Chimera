"""MAT2-M05 visual capture renderer: renders the committed interface run into
the frozen camera sheet (PREREGISTRATION.md visual profile, corrections A1-A2).

Every frame (2560x840) shows, for ONE tick:
  top row    diagnostic viewports [whole | side | front | close-up] with the
             five declared diagnostic layers (stable IDs, area-scaled force
             vectors, rest/current geometry and material directions,
             contact/bond state, energy/work and simulation tick),
  middle row clean viewports (same cameras; body_a/body_b and the fixed
             support stand only — no subject labels, no overlays, and the
             bond strap, line and label, is diagnostic-row content),
  bottom     gap/force/energy traces and the honest footer.

CPU rasterizer, painter's algorithm (declared occlusion_mode depth_tested);
it displays solver state, it is not a GPU render. Deterministic. Camera and
painter helpers follow the M03 pattern unmodified in method. Frames + evidence
are written to the attempt capture directory passed as argv[1].
Run from this directory:
    python -B render_interface_run.py <attempt_capture_dir>
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
sys.path.insert(0, str(HERE.parent / 'MAT2-M03'))

import interface_exchange as ix  # noqa: E402

TICKS = 24
W_VP, H_VP = 640, 360
VP_RES = [W_VP, H_VP]
ASPECT = 16.0 / 9.0
SHEET = (4 * W_VP, 2 * H_VP + 120)
TICKS_SLOWMO = ('1 tick = 1/300 s simulated, replayed at 1 video second per '
                'tick (slow motion x300)')
YC, ZC = ix.face_centroid_yz()
TARGET = np.array([0.0, YC, ZC])          # shared-face centroid at gap 0

VIEWS = ['whole experiment at fixed distance', 'orthogonal side and front',
         'oblique close-up of the loaded interface']
LAYERS = ['stable membrane/triangle/port IDs',
          'pressure and area-scaled force vectors',
          'rest/current geometry and material directions',
          'contact/bond state',
          'energy/work and simulation tick']


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
            'frame_id': 'mat2_m05_' + self.name + '_canvas_m',
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
                'SUBJECT moves (bodies squeeze/pull apart along the declared '
                'interface normal; bond strap stretches and releases), not '
                'the camera',
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


def draw_arrow(draw, start2, end2, color, width=2):
    sx, sy = float(start2[0]), float(start2[1])
    ex, ey = float(end2[0]), float(end2[1])
    if math.hypot(ex - sx, ey - sy) < 2.0:
        return
    draw.line([sx, sy, ex, ey], fill=color, width=width)
    ang = math.atan2(ey - sy, ex - sx)
    for da in (2.6, -2.6):
        draw.line([ex, ey, ex + 7.0 * math.cos(ang + da),
                   ey + 7.0 * math.sin(ang + da)], fill=color, width=width)


def draw_body(draw, body, cam, color, offset=(0, 0), force_tri=None,
              arrow_scale=1.0, arrow_color=(200, 30, 30), fonts=None,
              body_label=None, port_labels=False):
    """Painted body + wireframe of the REST geometry + interface arrows."""
    tri = body.x[body.triangles]
    centres = tri.mean(axis=1)
    mem = body.membrane
    pts, depth = cam.project(centres)
    order = np.argsort(-depth)
    for i in order:
        p3 = cam.project(tri[i])[0]
        if not np.all(np.isfinite(p3)):
            continue
        col = shade(mem.normals[i], color)
        draw.polygon([tuple(p + np.array(offset)) for p in p3],
                     fill=col, outline=(60, 60, 80))
    # rest geometry wireframe (current vs rest)
    rest_edges = {}
    for tri_i in body.triangles.tolist():
        for u, w in ((tri_i[0], tri_i[1]), (tri_i[1], tri_i[2]),
                     (tri_i[2], tri_i[0])):
            rest_edges[(min(u, w), max(u, w))] = True
    for (u, w) in sorted(rest_edges):
        pa, _ = cam.project(body.rest[[u, w]])
        pb, _ = cam.project(body.x[[u, w]])
        if not (np.all(np.isfinite(pa)) and np.all(np.isfinite(pb))):
            continue
        draw.line([tuple(pa[0] + np.array(offset)),
                   tuple(pb[0] + np.array(offset))],
                  fill=(120, 120, 140), width=1)
    if body_label and fonts:
        c2, _ = cam.project(body.x.mean(axis=0)[None, :])
        if np.all(np.isfinite(c2[0])):
            draw.text((c2[0][0] + offset[0] - 20, c2[0][1] + offset[1]),
                      body_label, fill=(15, 15, 15), font=fonts['small'])
    if port_labels and fonts:
        for pname, p3 in (('port:seam', body.anchor),
                          ('port:bond_anchor', body.anchor)):
            p2, _ = cam.project(p3[None, :])
            if np.all(np.isfinite(p2[0])):
                draw.text((p2[0][0] + offset[0] + 4,
                           p2[0][1] + offset[1] - 12), pname,
                          fill=(90, 30, 120), font=fonts['small'])
    if force_tri is not None:
        for i in range(force_tri.shape[0]):
            mag = float(np.linalg.norm(force_tri[i]))
            if mag <= 1e-9:
                continue
            c3 = tri[i].mean(axis=0)
            n = mem.normals[i] if i < 2 else np.sign(
                force_tri[i][0]) * ix.XHAT
            tip3 = c3 + n * (mag * arrow_scale)
            c2, = cam.project(c3)[0]
            t2, = cam.project(tip3)[0]
            if not (np.all(np.isfinite(c2)) and np.all(np.isfinite(t2))):
                continue
            draw_arrow(draw, c2 + offset, t2 + offset, arrow_color)
            if fonts:
                draw.text((t2[0] + offset[0] + 2, t2[1] + offset[1] - 6),
                          f'A={body.iface_areas[i]:.4f}',
                          fill=(150, 30, 30), font=fonts['small'])


def draw_support_stand(draw, body_a, cam, offset=(0, 0)):
    """The DECLARED support under body A (never a hidden constraint)."""
    base = body_a.x[0]
    pts = np.array([base + [0.0, -0.02, -0.02], base + [0.0, 0.22, -0.02],
                    base + [0.0, 0.22, 0.12], base + [0.0, -0.02, 0.12],
                    base + [-0.14, -0.02, -0.02],
                    base + [-0.14, 0.22, -0.02],
                    base + [-0.14, 0.22, 0.12],
                    base + [-0.14, -0.02, 0.12]])
    edges = [(0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7), (7, 4),
             (0, 4), (1, 5), (2, 6), (3, 7)]
    for u, w in edges:
        p, _ = cam.project(pts[[u, w]])
        if np.all(np.isfinite(p)):
            draw.line([tuple(p[0] + np.array(offset)),
                       tuple(p[1] + np.array(offset))],
                      fill=(90, 90, 90), width=2)


def draw_strap(draw, anchor_a, anchor_b, active, cam, offset=(0, 0),
               tension=0.0, label=True):
    """Strap line + text label. The 'bond:strap' text is a SUBJECT label:
    rows that declare no labels (the clean rows, manifest label_ids [])
    must never draw it, so the label is row-mode aware via `label`."""
    if not active:
        return
    p, _ = cam.project(np.array([anchor_a, anchor_b]))
    if np.all(np.isfinite(p)):
        draw.line([tuple(p[0] + np.array(offset)),
                   tuple(p[1] + np.array(offset))],
                  fill=(230, 120, 20), width=max(2, int(2 + 6 * tension)))
        if label:
            mid = (p[0] + p[1]) / 2.0 + np.array(offset)
            draw.text((mid[0] - 14, mid[1] - 14), 'bond:strap',
                      fill=(170, 90, 10))


def draw_traces(draw, ticks, tick_now, y_base, fonts):
    w = SHEET[0]
    gap_series = [t['gap_m'] for t in ticks]
    fcon = [t['contact_force_n'][0] for t in ticks]
    fbon = [t['bond_tension_n'] for t in ticks]
    en = [t['e_mechanical_j'] for t in ticks]
    panels = [('gap m', gap_series), ('F_contact x N', fcon),
              ('bond tension N', fbon), ('E_mech J', en)]
    pw = (w - 40) // 4
    for k, (title, series) in enumerate(panels):
        x0 = 20 + k * pw
        lo, hi = min(series), max(series)
        rng = (hi - lo) or 1.0
        draw.rectangle([x0, y_base, x0 + pw - 12, y_base + 76],
                       outline=(150, 150, 150))
        draw.text((x0 + 2, y_base + 2), title, fill=(20, 20, 20),
                  font=fonts['small'])
        pts = [(x0 + 4 + (pw - 20) * i / (len(series) - 1),
                y_base + 72 - 64 * (v - lo) / rng)
               for i, v in enumerate(series)]
        draw.line(pts, fill=(180, 40, 40), width=2)
        if tick_now < len(pts):
            draw.ellipse([pts[tick_now][0] - 3, pts[tick_now][1] - 3,
                          pts[tick_now][0] + 3, pts[tick_now][1] + 3],
                         fill=(20, 20, 200))
        draw.text((x0 + 2, y_base + 62),
                  f'{series[tick_now]:+.4f}', fill=(20, 20, 200),
                  font=fonts['small'])


# ---------------------------------------------------------------- replay ----
_POS_CACHE = None


def replay_rig():
    """Replay the frozen run deterministically; assert per-tick equality
    with the committed trace (solver-bound geometry, never regenerated)."""
    global _POS_CACHE
    if _POS_CACHE is not None:
        return _POS_CACHE
    trace = json.loads((HERE / 'interface_trace.json').read_text(
        encoding='utf-8'))
    run, origins = _fresh_rig()
    frames = []
    for tick in range(TICKS):
        row = run.step(tick, origins)
        assert abs(row['gap_m'] - trace['ticks'][tick]['gap_m']) < 1e-15, \
            'render replay diverged from the committed trace (gap)'
        assert abs(row['contact_pressure_pa']
                   - trace['ticks'][tick]['contact_pressure_pa']) < 1e-9, \
            'render replay diverged from the committed trace (pressure)'
        assert abs(row['bond_tension_n']
                   - trace['ticks'][tick]['bond_tension_n']) < 1e-12, \
            'render replay diverged from the committed trace (tension)'
        frames.append((run.body_a.x.copy(), run.body_b.x.copy(),
                       run.contact.shared_partition(),
                       run.contact.tractions()[0:2], row))
    _POS_CACHE = frames
    return _POS_CACHE


def _fresh_rig():
    a, b = ix.build_bodies()
    c = ix.ContactInterface('contact:ab_seam', a, b,
                            {'body_a': 'port:seam', 'body_b': 'port:seam'})
    bond = ix.BondElement('bond:strap', a, b,
                          {'body_a': 'port:bond_anchor',
                           'body_b': 'port:bond_anchor'}, 'force_moment')
    run = ix.TwoBodyRun((a, b), c, bond)
    origins = {'world': np.zeros(3), 'anchor_a': a.anchor, 'anchor_b': b.anchor}
    return run, origins


# ----------------------------------------------------------------- main -----
def main():
    out_dir = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 \
        else HERE / 'capture_out'
    frames_dir = out_dir / 'frames'
    evidence_dir = out_dir / 'evidence'
    frames_dir.mkdir(parents=True, exist_ok=True)
    evidence_dir.mkdir(parents=True, exist_ok=True)

    trace = json.loads((HERE / 'interface_trace.json').read_text(
        encoding='utf-8'))
    ticks = trace['ticks']
    frames = replay_rig()

    cams = {
        'whole': Camera('whole', (1.0, -0.9, 0.7), tuple(TARGET), VP_RES,
                        'perspective', fov_degrees=40.0),
        'side': Camera('side', (0.02, 2.0, 0.30), tuple(TARGET), VP_RES,
                       'orthographic', span=0.7),
        'front': Camera('front', (2.0, YC, ZC + 0.05), tuple(TARGET), VP_RES,
                        'orthographic', span=0.7),
        'closeup': Camera('closeup', tuple(TARGET + np.array([0.55, -0.35,
                                                              0.30])),
                          tuple(TARGET), VP_RES, 'perspective',
                          fov_degrees=30.0),
    }

    try:
        from PIL import ImageFont
        fonts = {'title': ImageFont.load_default(13),
                 'small': ImageFont.load_default(10),
                 'footer': ImageFont.load_default(12)}
    except Exception:
        fonts = {'title': None, 'small': None, 'footer': None}

    frame_hashes = {}
    for tick in range(TICKS):
        row = ticks[tick]
        xa, xb, partition, (f_a_tri, f_b_tri), _ = frames[tick]
        # rebuild display bodies at the replayed positions
        a_disp = ix.Body('body_a', 0.0, 0.16, None, True)
        b_disp = ix.Body('body_b', 0.0, -0.16, [ix.MASS_B_KG / 5.0] * 5,
                         False)
        a_disp.x = xa.copy()
        b_disp.x = xb.copy()
        state_hash = ix.digest(row)
        img = Image.new('RGB', SHEET, (252, 252, 250))
        draw = ImageDraw.Draw(img)
        phases = []
        if 1 <= tick <= 5:
            phases.append('PHASE squeeze (contact loads, bond slack)')
        if 6 <= tick <= 10:
            phases.append('PHASE pull (bond holds: tension rises)')
        if tick == 11:
            phases.append('PHASE RELEASE (bond removed)')
        if 12 <= tick <= 13:
            phases.append('PHASE post-release pull')
        if tick >= 14:
            phases.append('PHASE approach (contact re-loads, NO bond: '
                          'proximity never bonds)')
        phase_txt = ' | '.join(phases)
        panels = [('whole', 0), ('side', 1), ('front', 2), ('closeup', 3)]
        for col, (cam_name, _) in enumerate(panels):
            for row_idx, mode in ((0, 'diagnostic'), (1, 'clean')):
                x0 = col * W_VP
                y0 = row_idx * H_VP
                cam = cams[cam_name]
                view_label = {'whole': VIEWS[0], 'side': VIEWS[1],
                              'front': VIEWS[1], 'closeup': VIEWS[2]}[cam_name]
                if mode == 'clean':
                    # DECLARED clean-row content: body_a and body_b only,
                    # plus the fixed support stand. The bond strap — the
                    # orange line AND its 'bond:strap' text label — is
                    # diagnostic-row content (the manifest's clean rows
                    # declare label_ids [] and observed_subject_ids
                    # [body_a, body_b], so the strap is not declared clean
                    # scene content). Drawing it here leaked bond state into
                    # the clean row: the strap appears only while bound, so
                    # the release tick was readable from clean frames.
                    draw_support_stand(draw, a_disp, cam, offset=(x0, y0))
                    draw_body(draw, a_disp, cam, (225, 195, 150),
                              offset=(x0, y0))
                    draw_body(draw, b_disp, cam, (95, 140, 205),
                              offset=(x0, y0))
                    title = f'{view_label} | clean | tick {tick}'
                    draw.rectangle([x0, y0, x0 + W_VP - 1, y0 + H_VP - 1],
                                   outline=(160, 160, 160))
                else:
                    draw_support_stand(draw, a_disp, cam, offset=(x0, y0))
                    draw_body(draw, a_disp, cam, (245, 210, 150),
                              offset=(x0, y0), body_label='body_a (supported)',
                              fonts=fonts)
                    draw_body(draw, b_disp, cam, (80, 130, 210),
                              offset=(x0, y0), body_label='body_b (free)',
                              fonts=fonts, port_labels=(cam_name == 'closeup'))
                    draw_strap(draw, a_disp.anchor, b_disp.anchor,
                               row['bond_active'], cam, offset=(x0, y0),
                               tension=row['bond_tension_n'])
                    # contact traction arrows on BOTH bodies (area-scaled,
                    # equal and opposite); bond tension arrow along the strap
                    if row['contact_pressure_pa'] > 0.0:
                        scale = 0.55 / max(row['contact_force_n'][0], 1.0)
                        draw_body(draw, b_disp, cam, (80, 130, 210),
                                  offset=(x0, y0), force_tri=f_b_tri,
                                  arrow_scale=scale, arrow_color=(200, 30, 30),
                                  fonts=fonts if cam_name == 'closeup' else None)
                        draw_body(draw, a_disp, cam, (245, 210, 150),
                                  offset=(x0, y0), force_tri=f_a_tri,
                                  arrow_scale=scale, arrow_color=(200, 30, 30))
                    if row['bond_active'] and row['bond_tension_n'] > 1e-9:
                        mid = 0.5 * (a_disp.anchor + b_disp.anchor)
                        scale = 0.25 / max(row['bond_tension_n'], 0.05)
                        tip = mid + np.array([-row['bond_tension_n']
                                              * scale, 0.0, 0.0])
                        p1, _ = cam.project(mid[None, :])
                        p2, _ = cam.project(tip[None, :])
                        if np.all(np.isfinite(p1)) and np.all(np.isfinite(p2)):
                            off = np.array([x0, y0])
                            draw_arrow(draw, p1[0] + off, p2[0] + off,
                                       (230, 120, 20), width=3)
                            if fonts:
                                draw.text((p2[0][0] + x0,
                                           p2[0][1] + y0 - 14),
                                          f'T={row["bond_tension_n"]:.2f} N',
                                          fill=(170, 90, 10),
                                          font=fonts['small'])
                    title = (f'{view_label} | diagnostic | tick {tick} | '
                             f'gap={row["gap_m"]*1000:+.2f} mm '
                             f'p={row["contact_pressure_pa"]:.1f} Pa '
                             f'T={row["bond_tension_n"]:.2f} N')
                    draw.rectangle([x0, y0, x0 + W_VP - 1, y0 + H_VP - 1],
                                   outline=(90, 90, 90))
                draw.text((x0 + 6, y0 + 4), title, fill=(20, 20, 20),
                          font=fonts['title'])
                if mode == 'diagnostic':
                    draw.text((x0 + 6, y0 + H_VP - 60),
                              'layers: IDs | area-scaled force vectors | '
                              'rest(wire)/current geometry | '
                              f'contact {row["contact_state"]} | '
                              f'bond {"bound" if row["bond_active"] else "RELEASED"}'
                              ' | energy+tick',
                              fill=(60, 60, 160), font=fonts['small'])
                    draw.text((x0 + 6, y0 + H_VP - 46),
                              f'W_act={row["w_actuator_j"]:+.2e} '
                              f'W_contact={row["w_contact_j"]:+.2e} '
                              f'W_bond={row["w_bond_j"]:+.2e} J',
                              fill=(60, 60, 160), font=fonts['small'])
                    draw.text((x0 + 6, y0 + H_VP - 32),
                              f'Q={row["q_total_j"]:+.2e} '
                              f'(release {row["e_diss_release_j"]:+.2e}) '
                              f'R={row["residual_r_j"]:+.1e} J',
                              fill=(60, 60, 160), font=fonts['small'])
                    draw.text((x0 + 6, y0 + H_VP - 18),
                              f'ports port:seam port:bond_anchor | '
                              f'{phase_txt[:52]} | {state_hash[:10]}',
                              fill=(60, 60, 160), font=fonts['small'])

        y_base = 2 * H_VP + 8
        draw_traces(draw, ticks, tick, y_base, fonts)
        footer = (f'frame {tick:02d} | tick {tick} (={tick}/300 s simulated, '
                  f'replayed x300) | sheet: top diagnostic, middle clean, '
                  f'bottom traces | state {state_hash[:16]}')
        draw.text((8, SHEET[1] - 16), footer, fill=(30, 30, 30),
                  font=fonts['footer'])
        frame_path = frames_dir / f'frame_{tick:02d}.png'
        img.save(frame_path)
        frame_hashes[frame_path.name] = ix.sha256_file(frame_path)

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
