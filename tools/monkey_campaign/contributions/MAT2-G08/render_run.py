"""MAT2-G08 visual capture renderer (grasp/motion profile).

The rendered subject is the OBSERVED assembled replay bound to
experiment_trace.json (the composed qualification story): the pinned trunk
(wireframe outline -- an engineering view that conceals nothing), the
declared grip pads drawn at their MEASURED per-tick poses, the diagnostic
layers of the registry grasp profile, AND the DECLARED observation telemetry
(tick/phase/dt stamp, per-channel support states, all-stick and
holding-stick counts) drawn from the delivered samples.

The COMPOSED AXIS (declared, monotone, real): T-segment = the sealed G06
band_mid|n=3 229-tick replay at ticks 1..229; R-segment = the sealed G07
scene|n=3 60-tick replay mapped to composed ticks 230..259 (composed tick =
229 + replay tick). Every frame is bound to a REAL replay tick of a REAL
certified run through the declared tick_map; no relabeling, no interpolation
of physics. Frames (the preregistered story beats): the nine T beats (4, 8,
20, 31, 60, 120, 186, 193, 208) plus the R release-flip beat (replay tick
21 -> composed 250).

R-frame pose binding: the sealed G07 pose identity (measured centroid z ==
z0 - disp_down_cum) is a vertical displacement law; the R-frame pads are
drawn at their initial placement translated by the MEASURED centroid-z
delta (no lateral invention).

Motion-class capture gates (the W06 lesson):
- the tick axis is REAL: every frame is a declared story beat of a declared
  replay; state_or_tick_interval declares the composed axis and tick_map
  declares the tick->video-second mapping (1 video second per frame);
- every camera is gated BEFORE drawing (the anti-concealment prong);
- the serialized camera record is mathematically true (right-handed
  camera frame, quaternion wxyz = camera-to-frame); the reprojection
  oracle decodes ONLY the serialized record and reproduces the drawn
  anchors within 1 px;
- every visibility claim is MEASURED per frame as exact-color pixel
  counts (evidence/pixel_presence.json); make_capture refuses the
  manifest if a required subject lacks pixels;
- clean rows are geometry-only; diagnostic rows carry the declared layers,
  labels and support-state text; no inset, no footer;
- 'tendon paths' (a profile diagnostic layer) is inventoried ABSENT:
  this fixture has no tendons; the absence is disclosed here, in the
  context and in the report.

Run: python -B render_run.py
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

import g08_deps  # noqa: E402

g08_deps.ensure()

import assembly_line as al  # noqa: E402

gc = al.load_pinned_modules()[0]   # the pinned sealed G04 fixture
canonical = al.canonical

CARD_ID = 'G08'
CARD_FULL = 'MAT2-G08'
T_SCENARIO = al.T_STORY_SCENARIO          # band_mid|n=3
R_SCENARIO = al.R_STORY_SCENARIO          # scene|n=3
T_BEATS = (4, 8, 20, 31, 60, 120, 186, 193, 208)
R_BEAT = 21
AXIS = [1, 229 + 60]                      # composed: T 1..229, R 230..259
R_OFFSET = 229
SNAPSHOT_TICKS = list(T_BEATS) + [R_OFFSET + R_BEAT]
TICK_MAP = ('one tick = 0.005 s (M06 DT); COMPOSED AXIS: ticks 1..229 are '
            'the T-segment band_mid|n=3 replay ticks, ticks 230..289 are '
            'the R-segment scene|n=3 replay ticks 1..60 (composed = 229 + '
            'replay tick); frames are the declared story beats at 1 video '
            'second per frame; the rendered states are bound to '
            'experiment_trace.json story rows of the two declared '
            'scenarios')
VIEWS = ['whole-body/trunk relationship', 'wrist/digit attachment close-up',
         'orthogonal view of each loaded interface']
VIEW_REALIZATION = {
    'whole-body/trunk relationship':
        'side overview of the pinned trunk (wireframe; conceals nothing) '
        'with all declared grip-pad channels at their measured positions, '
        'support states and the delivered observation telemetry (tick/'
        'phase/dt, all-stick count, holding-stick count); the relocating '
        'channel climbs the column between the source band (z 0.386) and '
        'the target band (z 0.772), then the release story shows the '
        'falling pads; the creature body is ABSENT in records (x_reach), '
        'so the view shows the fixture, not anatomy',
    'wrist/digit attachment close-up':
        'the relocating channel (the sealed S1 facet) attachment patch '
        'wherever the limb is on its declared schedule: the source facet '
        'through the hold, the column during the climb flight, the target '
        'band after re-attach; on the R beat the falling pad 0 at its '
        'measured pose; contact normal and press/climb arrows; wrist/digit '
        'ANATOMY is ABSENT in records (no creature body, no tendons) and '
        'is not faked; the loaded interface is the fixture pad',
    'orthogonal view of each loaded interface':
        'top-down view along the trunk axis: all three loaded interfaces '
        'at 120 degree spacing at their measured positions, nothing '
        'occluded (anti-concealment view)',
}
DIAG_LAYERS = ['attachment patches and endpoint IDs', 'tendon paths',
               'joint/frame axes', 'contact normals and forces',
               'support state']
PAD_LABELS = ['grip.pad_0', 'grip.pad_1', 'grip.pad_2']

VP_W, VP_H = 640, 240
SHEET = (2 * VP_W, 3 * VP_H)
TILE_RECTS = {}
for _row, _view in enumerate(VIEWS):
    for _col, _mode in ((0, 'diagnostic'), (1, 'clean')):
        TILE_RECTS['%s:%s' % (_view, _mode)] = [
            _col * VP_W, _row * VP_H, (_col + 1) * VP_W, (_row + 1) * VP_H]

BG = (246, 246, 248)
TRUNK_EDGE = (96, 96, 104)
TRUNK_CLEAN = (150, 150, 158)
PAD_EDGE = (200, 60, 60)
PAD_FILL = (252, 210, 210)
NORMAL_ARROW = (30, 140, 220)
FORCE_ARROW = (230, 140, 20)
TRIAD = ((220, 40, 40), (40, 170, 40), (40, 40, 220))
TITLE_COLOR = (90, 90, 100)
LABEL_COLOR = (10, 10, 30)
STATE_COLORS = {'stick': (20, 140, 60), 'slip': (200, 40, 40),
                'still': (40, 90, 200)}
STATE_RELEASE = (120, 60, 160)


def presence_targets(mode):
    """The exact-color presence vocabulary (name -> RGB), shared with
    check_capture_pixels.py so the re-measure cannot drift."""
    targets = {
        'trunk': TRUNK_EDGE if mode == 'diagnostic' else TRUNK_CLEAN,
        'pad_edge': PAD_EDGE, 'pad_fill': PAD_FILL,
        'normal_arrow': NORMAL_ARROW, 'force_arrow': FORCE_ARROW,
    }
    if mode == 'diagnostic':
        targets['state_stick'] = STATE_COLORS['stick']
        targets['state_slip'] = STATE_COLORS['slip']
        targets['state_release'] = STATE_RELEASE
    return targets


# ---------------------------------------------------------------- geometry

def look_at(position, target, up=(0.0, 0.0, 1.0)):
    zc = gc.vnorm(gc.vsub(position, target))
    xc = gc.vnorm(gc.vcross(up, zc))
    yc = gc.vcross(zc, xc)
    return xc, yc, zc


def quat_from_basis(xc, yc, zc):
    m00, m01, m02 = xc
    m10, m11, m12 = yc
    m20, m21, m22 = zc
    tr = m00 + m11 + m22
    if tr > 0.0:
        s = math.sqrt(tr + 1.0) * 2.0
        w = 0.25 * s
        x = (m21 - m12) / s
        y = (m02 - m20) / s
        z = (m10 - m01) / s
    elif m00 > m11 and m00 > m22:
        s = math.sqrt(1.0 + m00 - m11 - m22) * 2.0
        w = (m21 - m12) / s
        x = 0.25 * s
        y = (m01 + m10) / s
        z = (m02 + m20) / s
    elif m11 > m22:
        s = math.sqrt(1.0 + m11 - m00 - m22) * 2.0
        w = (m02 - m20) / s
        x = (m01 + m10) / s
        y = 0.25 * s
        z = (m12 + m21) / s
    else:
        s = math.sqrt(1.0 + m22 - m00 - m11) * 2.0
        w = (m10 - m01) / s
        x = (m02 + m20) / s
        y = (m12 + m21) / s
        z = 0.25 * s
    n = math.sqrt(w * w + x * x + y * y + z * z)
    return (w / n, x / n, y / n, z / n)


def basis_from_quat(q):
    w, x, y, z = q
    return (
        (1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)),
        (2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)),
        (2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)),
    )


def make_projector(position, target, fov_deg, w, h, up=(0.0, 0.0, 1.0)):
    xc, yc, zc = look_at(position, target, up)
    f = (h / 2.0) / math.tan(math.radians(fov_deg) / 2.0)

    def project(p):
        d = gc.vsub(p, position)
        cam = (gc.vdot(d, xc), gc.vdot(d, yc), gc.vdot(d, zc))
        if cam[2] >= -1e-9:
            return None
        return (w / 2.0 + f * (cam[0] / (-cam[2])),
                h / 2.0 - f * (cam[1] / (-cam[2])))

    return project, (xc, yc, zc)


def project_from_record(sample, fov_deg, w, h, p):
    """The independent reprojection oracle: decodes ONLY the serialized
    camera record fields and returns the pixel for world point p."""
    q = sample['orientation']
    pos = sample['position']
    xc, yc, zc = basis_from_quat(q)
    d = gc.vsub(p, pos)
    cam = (gc.vdot(d, xc), gc.vdot(d, yc), gc.vdot(d, zc))
    if cam[2] >= -1e-9:
        return None
    f = (h / 2.0) / math.tan(math.radians(fov_deg) / 2.0)
    return (w / 2.0 + f * (cam[0] / (-cam[2])),
            h / 2.0 - f * (cam[1] / (-cam[2])))


# ------------------------------------------------------------------ scenes

def load_trace():
    return json.loads((HERE / 'experiment_trace.json').read_text(
        encoding='utf-8'))


def trunk_wireframe(geom):
    segs = set()
    tris = geom['triangles']
    for ti in geom['lateral_indices']:
        t = tris[ti]
        for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            segs.add((min(a, b), max(a, b)))
    return sorted(segs)


def initial_pads(geom, n_channels):
    out = []
    for k, (ti, cen, n) in enumerate(gc.channel_facets(geom, n_channels)):
        ey, ez = gc.orthobasis(n)
        verts = gc.place_tetra(gc.vadd(cen, gc.vscale(n, gc.PAD_OFFSET_M)),
                               n, ey, ez)
        edges = set()
        for t in gc.TETRA_TRIS:
            for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
                edges.add((min(a, b), max(a, b)))
        out.append({'idx': k, 'verts0': verts, 'cen0': centroid(verts),
                    'edges': sorted(edges), 'facet_cen': cen, 'n': n})
    return out


def centroid(vlist):
    s = [0.0, 0.0, 0.0]
    for v in vlist:
        s[0] += v[0]
        s[1] += v[1]
        s[2] += v[2]
    n = len(vlist)
    return (s[0] / n, s[1] / n, s[2] / n)


def pad_pose(pad, segment, row):
    """The pad's MEASURED pose at a story beat: rigid translation from the
    initial placement. T rows carry the measured centroid_m06 (the G06
    form); R rows carry the measured cumulative downward displacement
    (disp_down_m_cum) and the sealed G07 pose identity is
    z == z0 - disp_down_m_cum -- a vertical displacement law; the
    translation is the measured z delta, no lateral invention."""
    prow = row['pads'][pad['idx']]
    if segment == 'T':
        c = tuple(prow['centroid_m06'])
    else:
        c0 = pad['cen0']
        c = (c0[0], c0[1], c0[2] - prow['disp_down_m_cum'])
    d = gc.vsub(c, pad['cen0'])
    return {'idx': pad['idx'], 'verts': [gc.vadd(v, d)
                                         for v in pad['verts0']],
            'cen': c, 'edges': pad['edges'], 'n': pad['n']}


def arrow(draw, project, p0, direction, length, color, width=2):
    a = project(p0)
    b = project(gc.vadd(p0, gc.vscale(direction, length)))
    if a is None or b is None:
        return False
    draw.line([a[0], a[1], b[0], b[1]], fill=color, width=width)
    return True


def draw_triad(draw, project, p, scale):
    for axis, color in zip(((1, 0, 0), (0, 1, 0), (0, 0, 1)), TRIAD):
        a = project(p)
        b = project(gc.vadd(p, gc.vscale(axis, scale)))
        if a is not None and b is not None:
            draw.line([a[0], a[1], b[0], b[1]], fill=color, width=1)


def in_frame_gate(project, subjects, rect, scope_name):
    for name, pts in subjects:
        for p in pts:
            px = project(p)
            if px is None or not (rect[0] <= px[0] < rect[2]
                                  and rect[1] <= px[1] < rect[3]):
                raise ValueError('subject_out_of_frame:%s:%s'
                                 % (scope_name, name))


def _shift(px, x0, y0):
    return (px[0] + x0, px[1] + y0) if px else None


def pad_label(idx):
    return PAD_LABELS[idx] if idx < len(PAD_LABELS) else 'grip.pad_%d' % idx


def draw_viewport(tile, rect, view, mode, frame, scene, cam_pose):
    """One tile of the sheet. Diagnostic rows carry the declared layers,
    labels and support-state text; clean rows are geometry-only."""
    draw = ImageDraw.Draw(tile)
    x0, y0, x1, y1 = rect
    project, _basis = make_projector(cam_pose['position'], cam_pose['target'],
                                     cam_pose['fov'], x1 - x0, y1 - y0,
                                     cam_pose.get('up', (0.0, 0.0, 1.0)))
    subjects = cam_pose['framing_scope'](frame)
    in_frame_gate(project, subjects, [x0, y0, x1, y1], view + ':' + mode)
    edge_color = TRUNK_EDGE if mode == 'diagnostic' else TRUNK_CLEAN
    for a_i, b_i in scene['trunk_segs']:
        pa, pb = project(scene['vs6'][a_i]), project(scene['vs6'][b_i])
        if pa and pb:
            draw.line([x0 + pa[0], y0 + pa[1], x0 + pb[0], y0 + pb[1]],
                      fill=edge_color, width=1)
    pads_now = [pad_pose(p, frame['segment'], frame['row'])
                for p in scene['pads0']]
    for pad in pads_now:
        pts = [project(v) for v in pad['verts']]
        if any(p is None for p in pts):
            raise ValueError('pad_out_of_frame:' + pad_label(pad['idx']))
        pix = [(x0 + p[0], y0 + p[1]) for p in pts]
        if mode == 'diagnostic':
            draw.polygon(pix, fill=PAD_FILL)
        for a_i, b_i in pad['edges']:
            draw.line([pix[a_i][0], pix[a_i][1], pix[b_i][0], pix[b_i][1]],
                      fill=PAD_EDGE, width=1)
    if mode != 'diagnostic':
        draw.text((x0 + 8, y0 + 4), '%s [clean]' % view, fill=TITLE_COLOR)
        return
    row = frame['row']
    sample = frame['sample']
    verdict = frame.get('verdict')
    for pad, prow in zip(pads_now, row['pads']):
        c0 = pad['cen']
        arrow(draw, lambda p: _shift(project(p), x0, y0), c0, pad['n'],
              60.0 * max(prow['jn_sum_Ns'], 0.0) / gc.PRESS_JN_NS + 8.0,
              NORMAL_ARROW)
        grav = (0.0, 0.0, -1.0)
        arrow(draw, lambda p: _shift(project(p), x0, y0), c0, grav,
              60.0 * max(abs(prow['jt_sum_Ns']), 0.0) / gc.PRESS_JN_NS
              + 8.0, FORCE_ARROW)
        draw_triad(draw, lambda p: _shift(project(p), x0, y0),
                   gc.vadd(c0, gc.vscale(pad['n'], 0.02)), 0.02)
        lbl = pad_label(pad['idx'])
        state = ('RELEASE' if row['phase'] == 'release'
                 else prow['mode'].upper())
        color = (STATE_RELEASE if state == 'RELEASE'
                 else STATE_COLORS.get(prow['mode'], LABEL_COLOR))
        sp = project(gc.vadd(c0, gc.vscale(pad['n'], 0.055)))
        if sp:
            draw.text((x0 + sp[0], y0 + sp[1]), '%s %s' % (lbl, state),
                      fill=color)
    if not (sample['t_tick'] == row['tick'] and sample['t_dt_s'] == 0.005
            and abs(sample['t_seconds'] - row['tick'] * 0.005) <= 1e-12
            and sample['t_phase'] == row['phase']):
        raise ValueError('telemetry_sample_unbound:%s tick %d'
                         % (frame['segment'], row['tick']))
    holding_stick = (verdict['holding_stick_count'] if verdict else
                     sum(1 for k, pd in enumerate(row['pads'])
                         if k != 0 and pd['mode'] == 'stick'))
    supported = (verdict['supported'] if verdict else
                 sample['agg_supported_flag'] == 1.0)
    draw.text((x0 + 8, y0 + 4),
              '%s [diagnostic] tick %d %s' % (view, row['tick'], TICK_TEXT),
              fill=TITLE_COLOR)
    draw.text((x0 + 8, y0 + 22),
              'layers: ' + ', '.join(DIAG_LAYERS), fill=TITLE_COLOR)
    draw.text((x0 + 8, y0 + 36),
              'tendon paths: ABSENT in this fixture (inventoried)',
              fill=TITLE_COLOR)
    draw.text((x0 + 8, y0 + 50),
              'obs t=%.3fs %s dt=%.3fs all_stick=%d/%d holding_stick=%d/%d '
              'supported=%d'
              % (sample['t_seconds'], sample['t_phase'], sample['t_dt_s'],
                 int(sample['agg_support_count']),
                 scene['n_channels'],
                 holding_stick,
                 scene['n_channels'] - 1,
                 int(supported)),
              fill=TITLE_COLOR)


TICK_TEXT = 'dt=0.005s'

# ------------------------------------------------------------- cameras

BASE_CAMS = None


def frame_at(composed_tick, story_t, story_r):
    """The frame (segment + story entry) for a composed-axis tick."""
    if composed_tick <= R_OFFSET:
        return story_t[str(composed_tick)], 'T'
    return story_r[str(composed_tick - R_OFFSET)], 'R'


def anchor_of(entry, segment, pads0):
    pose = pad_pose(pads0[0], segment, entry['row'])
    return pose['cen']


def build_cameras(scene, story_t, story_r):
    """The declared bookmark-trajectory cameras. V0/V2 are fixed; V1 tracks
    the moving anchor (the relocating channel's measured patch through the
    T story, the falling pad on the R beat). Every camera carries samples
    covering the composed axis (validator law) with its real pose at each
    declared cover tick."""
    pads0 = scene['pads0']
    cams = {}
    cams[VIEWS[0]] = {
        'kind': 'fixed',
        'position': (1.45, 0.0, 0.58), 'target': (0.0, 0.0, 0.58),
        'fov': 50.0, 'near': 0.01, 'far': 10.0,
        'up': (0.0, 0.0, 1.0),
        'framing_scope': lambda f: [
            ('trunk_01.lateral',
             [scene['vs6'][i] for i in scene['corner_verts']]),
        ] + [('grip.pad_%d' % p['idx'], list(p['verts']))
             for p in scene['pads_now'](f)],
    }
    cams[VIEWS[1]] = {
        'kind': 'track_anchor',
        'offset': gc.vscale(pads0[0]['n'], 0.40), 'fov': 45.0,
        'near': 0.005, 'far': 2.0,
        'up': (0.0, 0.0, 1.0),
        'framing_scope': lambda f: [
            ('grip.pad_0', list(scene['pads_now'](f)[0]['verts'])),
            ('grip.pad_0.centroid', [scene['pads_now'](f)[0]['cen']]),
        ],
    }
    cams[VIEWS[2]] = {
        'kind': 'fixed',
        'position': (0.0, 0.0, 1.45), 'target': (0.0, 0.0, 0.55),
        'fov': 46.0, 'near': 0.01, 'far': 5.0, 'up': (0.0, 1.0, 0.0),
        'framing_scope': lambda f: [
            ('trunk_01.lateral',
             [scene['vs6'][i] for i in scene['corner_verts']]),
        ] + [('grip.pad_%d' % p['idx'], list(p['verts']))
             for p in scene['pads_now'](f)],
    }
    cover = sorted({AXIS[0], AXIS[1]}
                   | {R_OFFSET + 1, R_OFFSET + R_BEAT}
                   | set(T_BEATS))
    for view, cam in cams.items():
        samples = []
        for c in cover:
            if c <= R_OFFSET:
                entry, segment = story_t[str(c)], 'T'
            else:
                entry, segment = story_r[str(c - R_OFFSET)], 'R'
            if cam['kind'] == 'fixed':
                pos, tgt = tuple(cam['position']), tuple(cam['target'])
            else:
                cen = anchor_of(entry, segment, pads0)
                pos = gc.vadd(cen, cam['offset'])
                tgt = cen
            d = gc.vlen(gc.vsub(pos, tgt))
            xc, yc, zc = look_at(pos, tgt, cam['up'])
            samples.append({'tick': c, 'position': list(pos),
                            'target': list(tgt), 'distance_to_target': d,
                            'orientation': list(quat_from_basis(xc, yc,
                                                                zc))})
        cam['samples'] = samples
    return cams


def camera_record(view, cam):
    moving = cam['kind'] != 'fixed'
    return {
        'frame_id': 'mat2-g08-%s' % view,
        'coordinate_unit': 'm',
        'handedness': 'right',
        'orientation_convention': 'quaternion_wxyz_camera_to_frame',
        'forward_axis': '-Z', 'up_axis': '+Y',
        'near_far_planes': [cam['near'], cam['far']],
        'viewport_resolution': [VP_W, VP_H],
        'aspect_ratio': VP_W / VP_H,
        'projection': 'perspective',
        'vertical_fov_degrees': cam['fov'],
        'sample_mode': 'sampled_trajectory' if moving else 'fixed_bookmark',
        'interpolation': ('linear_position_target_slerp_orientation'
                          if moving else None),
        'samples': cam['samples'],
        'camera_motion_or_bookmark_sequence':
            ('the close-up camera tracks the declared anchor at its '
             'MEASURED pose at every declared cover tick of the composed '
             'axis (the relocating channel climbs from the source band to '
             'the target band; on the R-segment beat it follows the '
             'falling pad)' if moving else
             'fixed bookmark: identical pose at every declared cover tick'),
        'state_or_tick_interval':
            'composed tick_interval %s; T-segment replay ticks 1..229 '
            '(band_mid|n=3); R-segment replay ticks mapped to composed '
            '230..259 (scene|n=3, composed = 229 + replay tick); frames '
            'at the declared story beats %s; %s'
            % (AXIS, SNAPSHOT_TICKS, TICK_MAP),
    }


def main():
    out = HERE / 'evidence' / 'capture'
    out.mkdir(parents=True, exist_ok=True)
    geom = gc.load_trunk_geometry()
    trace = load_trace()
    story_t = trace['scenarios']['T:' + T_SCENARIO]['story']
    story_r = trace['scenarios']['R:' + R_SCENARIO]['story']
    rec_t = trace['scenarios']['T:' + T_SCENARIO]
    n_channels = rec_t['n_channels']
    pads0 = initial_pads(geom, n_channels)

    def pads_now(frame):
        return [pad_pose(p, frame['segment'], frame['row'])
                for p in pads0]

    corner_idx = sorted({i for ti in geom['lateral_indices']
                         for i in geom['triangles'][ti]})
    scene = {
        'vs6': geom['vertices_m06'],
        'trunk_segs': trunk_wireframe(geom),
        'pads0': pads0, 'pads_now': pads_now,
        'n_channels': n_channels, 'corner_verts': corner_idx,
    }
    cams = build_cameras(scene, story_t, story_r)
    records = {view: camera_record(view, cams[view]) for view in VIEWS}
    # reprojection oracle self-check: the drawn anchor (the tracked/fixed
    # target) reprojects within 1 px from the serialized record per sample
    oracle = []
    for view in VIEWS:
        cam = cams[view]
        for s in cam['samples']:
            if cam['kind'] == 'fixed':
                anchor = cam['target']
            else:
                anchor = s['target']
            got = project_from_record(
                {'position': s['position'], 'orientation': s['orientation']},
                cam['fov'], VP_W, VP_H, anchor)
            project, _ = make_projector(s['position'], s['target'],
                                        cam['fov'], VP_W, VP_H, cam['up'])
            want = project(anchor)
            if got is None or want is None:
                raise ValueError('oracle_anchor_missing:' + view)
            dpx = math.hypot(got[0] - want[0], got[1] - want[1])
            oracle.append({'view': view, 'tick': s['tick'],
                           'delta_px': dpx})
            if dpx > 1.0:
                raise ValueError('oracle_reprojection_mismatch:' + view)
    frames = []
    presence = {'schema': 'chimera.g08_pixel_presence.v1', 'frames': []}
    for fi, composed_tick in enumerate(SNAPSHOT_TICKS):
        entry, segment = frame_at(composed_tick, story_t, story_r)
        frame = {'segment': segment, 'row': entry['row'],
                 'sample': entry['sample'], 'verdict': entry.get('verdict')}
        sheet = Image.new('RGB', SHEET, BG)
        row = frame['row']
        frame_state = json.dumps(
            {'segment': segment, 'tick': row['tick'],
             'row': row},
            sort_keys=True).encode('utf-8')
        state_sha = hashlib.sha256(frame_state).hexdigest()
        counts = {}
        for view in VIEWS:
            cam = cams[view]
            s = next(x for x in cam['samples'] if x['tick']
                     == composed_tick)
            cam_pose = {'position': s['position'], 'target': s['target'],
                        'fov': cam['fov'], 'up': cam['up'],
                        'framing_scope': cam['framing_scope']}
            for mode in ('diagnostic', 'clean'):
                key = '%s:%s' % (view, mode)
                rect = TILE_RECTS[key]
                tile = sheet.crop(rect)
                draw_viewport(tile, [0, 0, rect[2] - rect[0],
                                     rect[3] - rect[1]],
                              view, mode, frame, scene, cam_pose)
                targets = presence_targets(mode)
                color_counts = {}
                for cnt, col in tile.getcolors(maxcolors=1 << 20):
                    color_counts[col] = cnt
                exact = {name: color_counts.get(color, 0)
                         for name, color in targets.items()}
                counts[key] = exact
                sheet.paste(tile, (rect[0], rect[1]))
        fname = 'frame_%02d.png' % fi
        sheet.save(out / fname, 'PNG', optimize=False)
        sha = hashlib.sha256((out / fname).read_bytes()).hexdigest()
        frames.append({'frame': fname, 'tick': composed_tick,
                       'segment': segment, 'replay_tick': row['tick'],
                       'sha256': sha, 'state_hash': state_sha})
        presence['frames'].append({'frame': fname, 'tick': composed_tick,
                                   'segment': segment,
                                   'replay_tick': row['tick'],
                                   'state_hash': state_sha,
                                   'exact_color_counts': counts})
    failures = []
    for fr in presence['frames']:
        for key, cnt_table in fr['exact_color_counts'].items():
            mode = key.split(':')[-1]
            required = (['trunk', 'pad_edge'] if mode == 'clean' else
                        ['trunk', 'pad_edge', 'pad_fill', 'normal_arrow',
                         'force_arrow'])
            for name in required:
                if cnt_table.get(name, 0) <= 0:
                    failures.append('%s:%s missing %s'
                                    % (fr['frame'], key, name))
    if failures:
        presence['failures'] = failures
        (out / 'pixel_presence.json').write_bytes(canonical(presence))
        raise ValueError('required_subject_pixels_missing:' +
                         '; '.join(failures[:5]))
    (out / 'pixel_presence.json').write_bytes(canonical(presence))
    (out / 'cameras.json').write_bytes(canonical({
        'views': VIEWS, 'view_realization': VIEW_REALIZATION,
        'records': records, 'snapshot_ticks': SNAPSHOT_TICKS,
        'composed_axis': AXIS, 'r_segment_offset': R_OFFSET,
        'oracle': oracle, 'diagnostic_layers': DIAG_LAYERS,
        'tick_map': TICK_MAP, 't_scenario': T_SCENARIO,
        'r_scenario': R_SCENARIO,
        'absent_components': ['creature body', 'wrist/digit anatomy',
                              'tendon paths', 'joint axes of the creature '
                              '(only declared fixture frame axes drawn)'],
    }))
    print(json.dumps({'frames': len(frames),
                      'oracle_max_delta_px': max(o['delta_px']
                                                 for o in oracle),
                      'presence_failures': 0,
                      'snapshot_ticks': SNAPSHOT_TICKS,
                      'composed_axis': AXIS}, indent=1))


if __name__ == '__main__':
    main()
