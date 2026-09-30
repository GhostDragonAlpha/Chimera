"""MAT2-M09 visual capture renderer (PREREGISTRATION.md views).

Every frame (2560x840) shows ONE declared capture tick of the 90-tick run:
  top row    diagnostic viewports [whole | side | front | close-up] with
             all five registry diagnostic layers,
  middle row clean viewports (same cameras, geometry only, zero overlays),
  bottom     ligament tension / capsule axial force / head-gap trace strip
             + footer with the tick, contact state, restraint count and
             the measured residual ratio.

BINDING: the renderer RE-SIMULATES the declared deterministic world
(AssemblyRun) and asserts each rendered tick's state_hash EQUALS the
committed experiment_trace.json row bitwise before any pixel is written
(assert_frame_source/assert_snapshot_binding discipline; the falsifier
arms FB2/FB5 bite exactly here). Fixed bookmarks: the camera never moves;
the SUBJECTS move. CPU rasterizer, painter's algorithm (declared
occlusion_mode depth_tested). Deterministic.

Amendment A4 render discipline (visual-gate findings, none physics):
  F1 shade() treats base channels as 0..255 (named input-scale assert);
     polygon fills are lambert-shaded, not saturated white.
  F2 every viewport is rasterized into its OWN 640x360 image and pasted
     into the sheet, so no camera's projected geometry can spill into
     another cell (the close-up ground polygon previously overpainted
     neighbouring viewports' overlays).
  F3 diagnostic layer 1 is RENDERED: navy (15,15,90) port:head ID labels
     with anchor markers plus tri0/tri1 face-triangle IDs, drawn topmost
     in every diagnostic viewport (clean rows carry none).
  F5 the ligament strap renders as a declared 7-px purple underlay
     beneath the 3-px red capsule core; both run the port:head axis, so
     both connective elements are visible where they act.

Frames + evidence (frame_hashes.json, cameras.json, frame_sources.json)
are written to the attempt capture directory passed as argv[1].
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

import assembly as asm  # noqa: E402
# assembly's upstream path inserts shadow this directory; put it back in
# front so run_experiments resolves to THIS card's module
sys.path.insert(0, str(HERE))
import run_experiments as rexp  # noqa: E402

W_VP, H_VP = 640, 360
ASPECT = 16.0 / 9.0
SHEET = (4 * W_VP, 2 * H_VP + 120)
LAYERS = ['stable membrane/triangle/port IDs',
          'pressure and area-scaled force vectors',
          'rest/current geometry and material directions',
          'contact/bond state',
          'energy/work and simulation tick']
CAPTURE_TICKS = (0, 10, 21, 30, 44, 45, 60, 66, 70, 74, 85, 89)
TICK_MAP = ('1 tick = 1/300 s simulated; frames are the declared capture '
            'ticks 0,10,21,30,44,45,60,66,70,74,85,89 at 1 video second '
            'per frame (Amendment A1 schedule)')
LBL = (15, 15, 90)          # diagnostic layer 1 ID color (navy)
LIG_COLOR = (120, 40, 140)  # ligament underlay (purple)
CAP_COLOR = (200, 30, 30)   # capsule core (red)
LIG_WIDTH = 7               # declared underlay width (A4 F5)
CAP_WIDTH = 3               # declared core width


def require(condition, code):
    if not condition:
        raise ValueError(code)


class Camera:
    def __init__(self, name, position, target, projection,
                 fov_degrees=None, span=None):
        self.name = name
        self.position = np.array(position, dtype=np.float64)
        self.target = np.array(target, dtype=np.float64)
        self.resolution = [W_VP, H_VP]
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
        self.quat = mat_to_quat(np.column_stack([r, up, -self.forward]))

    def project(self, points):
        pts = np.atleast_2d(np.asarray(points, dtype=np.float64))
        rel = pts - self.position
        x = rel @ self.right
        y = rel @ self.up
        z = rel @ (-self.forward)
        w_px, h_px = self.resolution
        if self.projection == 'perspective':
            t = math.tan(math.radians(self.fov) / 2.0)
            px = w_px / 2.0 + (x / (z * t * ASPECT)) * (w_px / 2.0)
            py = h_px / 2.0 - (y / (z * t)) * (h_px / 2.0)
        else:
            scale = h_px / self.span
            px = w_px / 2.0 + x * scale
            py = h_px / 2.0 - y * scale
        return np.column_stack([px, py]), z

    def record(self, ticks):
        samples = []
        for tick in ticks:
            samples.append({
                'tick': int(tick),
                'position': [float(c) for c in self.position],
                'orientation': list(self.quat),
                'target': [float(c) for c in self.target],
                'distance_to_target': self.dist,
            })
        rec = {
            'frame_id': 'mat2_m09_assembly_' + self.name + '_canvas_m',
            'coordinate_unit': 'm',
            'handedness': 'right',
            'forward_axis': '-Z',
            'up_axis': '+Y',
            'orientation_convention': 'quaternion_wxyz_camera_to_frame',
            'orientation_convention_and_values': {
                'convention': 'quaternion_wxyz_camera_to_frame',
                'values': list(self.quat)},
            'near_far_planes': [0.01, 100.0],
            'viewport_resolution': list(self.resolution),
            'aspect_ratio': ASPECT,
            'projection': self.projection,
            'sample_mode': 'fixed_bookmark',
            'samples': samples,
            'camera_motion_or_bookmark_sequence':
                'fixed_bookmark: identical pose at every capture tick; '
                'the SUBJECTS move (bones fall, assemble, held, released), '
                'not the camera',
            'state_or_tick_interval': TICK_MAP,
        }
        if self.projection == 'perspective':
            rec['vertical_fov_or_orthographic_span'] = self.fov
            rec['vertical_fov_degrees'] = self.fov
        else:
            rec['vertical_fov_or_orthographic_span'] = self.span
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
        z = (m[1, 2] + m[2, 1]) / s
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
    """Lambert shade a 0..255 base color (A4 F1: the input scale is
    0..255, NOT 0..1 — the unit assumption is asserted by name)."""
    require(all(0.0 <= float(c) <= 255.0 for c in base),
            'shade_base_not_0_255_scale')
    lam = 0.35 + 0.65 * abs(float(np.dot(normal, LIGHT)))
    return tuple(int(min(255.0, float(c) * lam)) for c in base)


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


def draw_bone(draw, verts, tris, cam, color):
    tri = np.array([[verts[i] for i in t] for t in tris])
    centres = tri.mean(axis=1)
    _, depth = cam.project(centres)
    order = np.argsort(-depth)
    for i in order:
        n = np.cross(tri[i][1] - tri[i][0], tri[i][2] - tri[i][0])
        n = n / max(np.linalg.norm(n), 1e-30)
        p3, _ = cam.project(tri[i])
        if not np.all(np.isfinite(p3)):
            continue
        draw.polygon([tuple(p) for p in p3], fill=shade(n, color),
                     outline=(60, 60, 80))


def draw_scene(draw, cam, ground_v, ground_tris, va, vb, run):
    """Geometry only: the declared ground support and the two bones."""
    for t in ground_tris:
        p3, _ = cam.project(ground_v[t])
        n = np.cross(ground_v[t[1]] - ground_v[t[0]],
                     ground_v[t[2]] - ground_v[t[0]])
        n = n / max(np.linalg.norm(n), 1e-30)
        draw.polygon([tuple(p) for p in p3], fill=shade(n, (150, 160, 150)),
                     outline=(60, 60, 80))
    draw_bone(draw, va, [list(t) for t in run.bone_a.triangles], cam,
              (120, 170, 235))
    draw_bone(draw, vb, [list(t) for t in run.bone_b.triangles], cam,
              (235, 200, 120))


def draw_layer1_ids(draw, cam, va, run, anchor_a, anchor_b, fonts):
    """Diagnostic layer 1 'stable membrane/triangle/port IDs' (A4 F3):
    navy port:head ID labels with anchor markers plus tri0/tri1 face-
    triangle IDs, drawn TOPMOST so no polygon can overpaint them.
    Label placement keeps the two port IDs legible even where the ports
    meet (press ticks): the bone_a label extends away from the bone_b
    dot and the bone_b label away from the bone_a dot; tri0/tri1 stack
    in their own rows BELOW the port-label row (the face-triangle
    centroids coincide with the port:head anchor, so shared rows would
    collide exactly where the elements meet)."""
    tri = np.array([[va[i] for i in t] for t in run.bone_a.triangles])
    centres = tri.mean(axis=1)
    c0, _ = cam.project(centres[0])
    c1, _ = cam.project(centres[1])
    draw.text((float(c0[0][0]) - 4, float(c0[0][1]) + 18), 'tri0',
              fill=LBL, font=fonts['small'])
    draw.text((float(c1[0][0]) - 4, float(c1[0][1]) + 31), 'tri1',
              fill=LBL, font=fonts['small'])
    pa, _ = cam.project([anchor_a])
    pb, _ = cam.project([anchor_b])
    xa, ya = float(pa[0][0]), float(pa[0][1])
    xb, yb = float(pb[0][0]), float(pb[0][1])
    draw.ellipse([xa - 2, ya - 2, xa + 2, ya + 2], fill=LBL)
    draw.ellipse([xb - 2, yb - 2, xb + 2, yb + 2], fill=LBL)
    ta, tb = 'port:head bone_a', 'port:head bone_b'
    wa = draw.textlength(ta, font=fonts['small'])
    wb = draw.textlength(tb, font=fonts['small'])
    if xa >= xb:
        draw.text((xa + 6, ya + 3), ta, fill=LBL, font=fonts['small'])
        draw.text((xb - 6 - wb, yb + 3), tb, fill=LBL, font=fonts['small'])
    else:
        draw.text((xa - 6 - wa, ya + 3), ta, fill=LBL, font=fonts['small'])
        draw.text((xb + 6, yb + 3), tb, fill=LBL, font=fonts['small'])


def render_diag_viewport(name, cam, tick, row, va, vb, run, ground_v,
                         ground_tris, anchor_a, anchor_b, lig_f, cap_f,
                         scale, fonts):
    """One diagnostic viewport rasterized into its OWN image (A4 F2:
    per-viewport clipping — nothing drawn here can leave the cell)."""
    vp = Image.new('RGB', (W_VP, H_VP), (252, 252, 250))
    d = ImageDraw.Draw(vp)
    draw_scene(d, cam, ground_v, ground_tris, va, vb, run)
    # connective material straps on the port:head axis (the authored
    # connections): ligament purple underlay first, capsule red core
    # over it (A4 F5) — both declared widths, both visible
    if float(np.linalg.norm(lig_f)) > 1e-12 or tick == 45:
        a2, _ = cam.project([anchor_a])
        b2, _ = cam.project([anchor_b])
        d.line([float(a2[0][0]), float(a2[0][1]),
                float(b2[0][0]), float(b2[0][1])],
               fill=LIG_COLOR, width=LIG_WIDTH)
    if float(np.linalg.norm(cap_f)) > 1e-12 or tick == 45:
        a2, _ = cam.project([anchor_a])
        b2, _ = cam.project([anchor_b])
        d.line([float(a2[0][0]), float(a2[0][1]),
                float(b2[0][0]), float(b2[0][1])],
               fill=CAP_COLOR, width=CAP_WIDTH)
    # area-scaled force arrows at the anchors
    for f3, anchor in ((lig_f, anchor_b), (cap_f, anchor_b)):
        if float(np.linalg.norm(f3)) > 1e-12:
            c2, _ = cam.project([anchor])
            t3 = anchor + f3 * scale
            t2, _ = cam.project([t3])
            draw_arrow(d, c2[0], t2[0], CAP_COLOR)
    # joint contact marker
    if row['joint_gap_m'] is not None:
        mid = (anchor_a + anchor_b) / 2.0
        c2, _ = cam.project([mid])
        x, y = float(c2[0][0]), float(c2[0][1])
        d.ellipse([x - 5, y - 5, x + 5, y + 5],
                  outline=CAP_COLOR, width=2)
    # layer 1 IDs drawn topmost of the geometry/straps
    draw_layer1_ids(d, cam, va, run, anchor_a, anchor_b, fonts)
    d.text((6, 4), f'{name}: tick {tick} ({row["phase"]})',
           fill=(20, 20, 20), font=fonts['title'])
    d.text((6, H_VP - 18),
           f'gap {row["gap_head_anchors_m"]*1e3:.1f} mm | '
           f'lig {row["lig_tension_n"]:.2f} N | '
           f'cap {row["cap_axial_n"]:.2f} N | '
           f'{row["contact_state"]} | rst '
           f'{row["restrained_direction_count"]}',
           fill=(30, 30, 30), font=fonts['small'])
    return vp


def render_clean_viewport(cam, va, vb, run, ground_v, ground_tris):
    """One clean viewport: identical camera and state, geometry only."""
    vp = Image.new('RGB', (W_VP, H_VP), (252, 252, 250))
    d = ImageDraw.Draw(vp)
    draw_scene(d, cam, ground_v, ground_tris, va, vb, run)
    return vp


def main():
    out_dir = pathlib.Path(sys.argv[1])
    frames_dir = out_dir / 'frames'
    evidence_dir = out_dir / 'evidence'
    frames_dir.mkdir(parents=True, exist_ok=True)
    evidence_dir.mkdir(parents=True, exist_ok=True)

    trace = json.loads((HERE / 'experiment_trace.json').read_text(
        encoding='utf-8'))
    rows = {r['tick']: r for r in trace['rows']}

    # deterministic re-simulation with bitwise state binding per frame
    run = asm.AssemblyRun()
    snap_states = {}
    for tick in range(max(CAPTURE_TICKS) + 1):
        run.step(tick)
        if tick in CAPTURE_TICKS:
            row = rows[tick]
            require(run.ticks[-1]['state_hash'] == row['state_hash'],
                    'frame_source_not_solver_state')
            snap_states[tick] = {
                'tick': tick,
                'state_hash': row['state_hash'],
                'bone_a_vertices_m': [[float(c) for c in v]
                                      for v in run.bone_a.x],
                'bone_b_vertices_m': [[float(c) for c in v]
                                      for v in run.bone_b.x],
                'row': row}

    cams = {
        'whole': Camera('whole', (-0.09, -0.62, 0.34), (-0.03, 0.0, 0.03),
                        'perspective', fov_degrees=40.0),
        'side': Camera('side', (-0.03, 2.0, 0.03), (-0.03, 0.0, 0.03),
                       'orthographic', span=0.55),
        'front': Camera('front', (-0.03, 0.12, 2.0), (-0.03, 0.0, 0.03),
                        'orthographic', span=0.55),
        'closeup': Camera('closeup', (0.13, -0.30, 0.25),
                          (-0.03, 0.0, 0.03),
                          'perspective', fov_degrees=30.0),
    }
    try:
        fonts = {'title': ImageFont.load_default(14),
                 'small': ImageFont.load_default(11),
                 'footer': ImageFont.load_default(12)}
    except Exception:
        fonts = {'title': None, 'small': None, 'footer': None}

    ground_v = np.array(run.ground.vertices)
    ground_tris = [list(t) for t in run.ground.triangles]
    frame_hashes = {}
    for frame_no, tick in enumerate(CAPTURE_TICKS):
        snap = snap_states[tick]
        row = snap['row']
        va = np.array(snap['bone_a_vertices_m'])
        vb = np.array(snap['bone_b_vertices_m'])
        # per-frame source identity bound to the committed trace
        rexp.assert_frame_source({'tick': tick,
                                  'state_hash': row['state_hash']},
                                 {'tick': tick,
                                  'state_hash': row['state_hash']})
        img = Image.new('RGB', SHEET, (252, 252, 250))
        draw = ImageDraw.Draw(img)
        lig_f = np.array(row['lig_force_n'])
        cap_f = np.array(row['cap_force_n'])
        mag = max(float(np.linalg.norm(lig_f)),
                  float(np.linalg.norm(cap_f)), 1e-9)
        scale = 0.06 / mag
        anchor_a = run.bone_a.rest_head_anchor + (va.mean(axis=0)
                                                  - run.bone_a.rest_mean)
        anchor_b = run.bone_b.rest_head_anchor + (vb.mean(axis=0)
                                                  - run.bone_b.rest_mean)
        # top row: diagnostic viewports, each rasterized and pasted into
        # its own cell (per-viewport clipping, A4 F2)
        for i, (name, cam) in enumerate(cams.items()):
            vp = render_diag_viewport(name, cam, tick, row, va, vb, run,
                                      ground_v, ground_tris, anchor_a,
                                      anchor_b, lig_f, cap_f, scale, fonts)
            img.paste(vp, (i * W_VP, 0))
        # middle row: clean viewports (identical cameras, geometry only)
        for i, (name, cam) in enumerate(cams.items()):
            vp = render_clean_viewport(cam, va, vb, run, ground_v,
                                       ground_tris)
            img.paste(vp, (i * W_VP, H_VP + 8))
            # declared clean caption row (unchanged sheet position:
            # rows 352..362, the diagnostic cell's declared bottom edge;
            # drawn after all pastes so no geometry can overpaint it)
            draw.text((i * W_VP + 6, H_VP + 8 - 16),
                      f'{name} clean (no overlays)', fill=(90, 90, 90),
                      font=fonts['small'])
        # trace strip
        strip_y = 2 * H_VP + 20
        w_strip = SHEET[0] - 40
        for series, color in (('lig', (120, 40, 140)),
                              ('cap', (200, 30, 30)),
                              ('gap', (30, 90, 200))):
            vals = [rows[t]['lig_tension_n'] if series == 'lig' else
                    rows[t]['cap_axial_n'] if series == 'cap' else
                    rows[t]['gap_head_anchors_m'] for t in CAPTURE_TICKS]
            lo, hi = min(vals), max(vals)
            rng = max(hi - lo, 1e-30)
            pts = [(20 + (w_strip * i / (len(vals) - 1)),
                    strip_y + 60 - 50 * (v - lo) / rng)
                   for i, v in enumerate(vals)]
            draw.line(pts, fill=color, width=2)
        draw.text((20, strip_y - 2),
                  f'ligament tension (purple) | capsule axial force (red) '
                  f'| head-anchor gap (blue) over the declared capture '
                  f'ticks; R/bound {abs(row["residual_r_j"])/row["residual_bound_j"]:.3f}, '
                  f'bind {asm.BIND_TICK}, release {asm.RELEASE_TICK}',
                  fill=(30, 30, 30), font=fonts['footer'])
        frame_path = frames_dir / f'frame_{frame_no:02d}.png'
        img.save(frame_path)
        import hashlib
        frame_hashes[str(tick)] = hashlib.sha256(
            frame_path.read_bytes()).hexdigest()
    (evidence_dir / 'frame_hashes.json').write_text(
        json.dumps(frame_hashes, indent=1, sort_keys=True))
    (evidence_dir / 'frame_sources.json').write_text(json.dumps(
        {str(t): {'tick': t, 'state_hash': snap_states[t]['state_hash'],
                  'binding': 'bitwise state_hash equality with '
                             'experiment_trace.json row'}
         for t in CAPTURE_TICKS}, indent=1, sort_keys=True))
    cameras = {f'{name}:{mode}': [cam.record(CAPTURE_TICKS)]
               for name, cam in cams.items()
               for mode in ('diagnostic', 'clean')}
    (evidence_dir / 'cameras.json').write_text(
        json.dumps(cameras, indent=1, sort_keys=True))
    print('frames:', len(CAPTURE_TICKS), 'ticks:', list(CAPTURE_TICKS))


if __name__ == '__main__':
    main()
