"""MAT2-G07 visual capture renderer (grasp/motion profile).

The rendered subject is the OBSERVED release/fall replay bound to
experiment_trace.json: the pinned trunk (wireframe outline -- an
engineering view that conceals nothing), the declared grip pads drawn at
their MEASURED TRACE CENTROIDS (the falling poses), the diagnostic layers
of the registry grasp profile read at capture time, AND the DECLARED
observation telemetry of the sealed G05 interface (tick/phase/dt stamp,
per-channel support states, support count, cumulative fall displacement)
drawn from the delivered samples of the scene|n=3 replay.

Gates implemented here (the G02/G05 sealed-pattern lessons):
- draw_viewport() is CALLED for every tile (3 registry views x
  diagnostic/clean); nothing is a stub;
- every camera is gated BEFORE drawing on the DRAWN poses: each declared
  framing-scope subject must project inside the viewport at every
  snapshot tick (the anti-concealment prong; the close-up scope declares
  only the subjects it frames -- here the full fall corridor);
- the serialized camera record is mathematically true: right-handed
  camera frame (+X right, +Y up, -Z forward), quaternion wxyz =
  camera-to-frame; an independent reprojection oracle
  (project_from_record: decodes the serialized record ONLY) reproduces
  the drawn anchors within 1 px at the fixture pose AND at a falling
  snapshot pose;
- every visibility claim is MEASURED per frame as exact-color pixel
  counts (evidence/pixel_presence.json); make_capture refuses the
  manifest if a required subject lacks pixels;
- clean rows are geometry-only; diagnostic rows carry the declared
  layers, labels and support-state text. No inset, no footer: nothing
  overlaps a viewport rect.
- 'tendon paths' (a profile diagnostic layer) is inventoried ABSENT:
  this fixture has no tendons; the layer is declared with zero drawn
  geometry and the absence is disclosed in the context and the report.

TIMING CONFORMANCE (motion class; checked BEFORE the capture build -- the
W06 lesson): the tick axis is REAL -- tick_interval [1, 60] over the
trace ticks, one tick = 0.005 s (the pinned M06 DT), declared in
tick_map and in every camera record's state_or_tick_interval.

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

import release_fall_account as rfa  # noqa: E402

cso = rfa.load_g05_module()   # the sealed G05 seam (hash-asserted)
gc = cso.load_g04_module()    # the pinned sealed G04 fixture (hash-asserted)

CARD_ID = 'G07'
CARD_FULL = 'MAT2-G07'
TICK_MAP = ('one tick = 0.005 s (M06 DT); tick_interval [1, 60] over the '
            'trace ticks (20 hold + 40 release); frames are the declared '
            'snapshot ticks at 1 video second per frame; the rendered '
            'state is bound to experiment_trace.json rows')
VIEWS = ['whole-body/trunk relationship', 'wrist/digit attachment close-up',
         'orthogonal view of each loaded interface']
# task-owned realization of the profile views (context disclosure):
VIEW_REALIZATION = {
    'whole-body/trunk relationship':
        'side overview of the pinned trunk (wireframe; conceals nothing) '
        'with all declared grip-pad channels drawn at their MEASURED '
        'TRACE CENTROIDS (the falling poses), support states and the '
        'delivered observation telemetry (tick/phase/dt, support count, '
        'cumulative fall displacement); the creature body is ABSENT in '
        'records (x_reach), so the view shows the fixture, not anatomy',
    'wrist/digit attachment close-up':
        'the sealed F03 S1 channel contact close-up framed over the full '
        'fall corridor: attachment patch, contact normal and force arrows '
        'at the CURRENT measured pose per snapshot tick; wrist/digit '
        'ANATOMY is ABSENT in records (no creature body, no tendons) and '
        'is not faked; the loaded interface is the fixture pad',
    'orthogonal view of each loaded interface':
        'top-down view along the trunk axis: all three loaded interfaces '
        'at 120 degree spacing, nothing occluded (anti-concealment view); '
        'the fall runs along the view axis so the pads hold their azimuth',
}
DIAG_LAYERS = ['attachment patches and endpoint IDs', 'tendon paths',
               'joint/frame axes', 'contact normals and forces',
               'support state']
PAD_LABELS = ['grip.pad_0', 'grip.pad_1', 'grip.pad_2']
SNAPSHOT_TICKS = (1, 8, 16, 20, 24, 32, 44, 56)   # hold 1..20; release 21..60

VP_W, VP_H = 640, 240
SHEET = (2 * VP_W, 3 * VP_H)
TILE_RECTS = {}
for _row, _view in enumerate(VIEWS):
    for _col, _mode in ((0, 'diagnostic'), (1, 'clean')):
        TILE_RECTS[f'{_view}:{_mode}'] = [
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
STATE_COLORS = {'stick': (20, 140, 60), 'slip': (200, 40, 40)}
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
    """Right-handed camera-to-frame rotation basis; forward is -Z, up +Y."""
    zc = gc.vnorm(gc.vsub(position, target))
    xc = gc.vnorm(gc.vcross(up, zc))
    yc = gc.vcross(zc, xc)
    return xc, yc, zc


def quat_from_basis(xc, yc, zc):
    """Quaternion (w, x, y, z) of the camera-to-frame rotation whose matrix
    columns are xc, yc, zc (proper, det=+1)."""
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
        s = math.sqrt(1.0 + m22 - m00 - m11)
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
        require_front = cam[2] < -1e-9     # in front of the near plane
        if not require_front:
            return None
        return (w / 2.0 + f * (cam[0] / (-cam[2])),
                h / 2.0 - f * (cam[1] / (-cam[2])))

    return project, (xc, yc, zc)


def project_from_record(sample, fov_deg, w, h, p):
    """The independent reprojection oracle: decodes ONLY the serialized
    camera record fields (position, quaternion, convention, axes, fov,
    resolution) and returns the pixel for world point p."""
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

def load_battery_states():
    trace = json.loads((HERE / 'experiment_trace.json').read_text(
        encoding='utf-8'))
    return trace


def trunk_wireframe(geom):
    segs = set()
    tris = geom['triangles']
    lat = geom['lateral_indices']
    for ti in lat:
        t = tris[ti]
        for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            segs.add((min(a, b), max(a, b)))
    return sorted(segs)


def pad_layouts(geom, n_channels):
    """The pad tetra layouts: the solver moves bodies by rigid
    translation, so each snapshot's drawn verts are the fixture verts
    translated by (measured centroid - fixture centroid). The per-tick
    poses are filled in by main() from the measured acct centroids."""
    out = []
    for k, (ti, cen, n) in enumerate(gc.channel_facets(geom, n_channels)):
        ey, ez = gc.orthobasis(n)
        verts0 = gc.place_tetra(gc.vadd(cen, gc.vscale(n, gc.PAD_OFFSET_M)),
                                n, ey, ez)
        c0 = gc.vscale(gc.vadd(gc.vadd(verts0[0], verts0[1]),
                               gc.vadd(verts0[2], verts0[3])), 0.25)
        edges = set()
        for t in gc.TETRA_TRIS:
            for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
                edges.add((min(a, b), max(a, b)))
        out.append({'idx': k, 'verts0': verts0, 'cen0': c0, 'n': n,
                    'edges': sorted(edges), 'per_tick': {}})
    return out


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
            if px is None or not (rect[0] <= rect[0] + px[0] < rect[2]
                                  and rect[1] <= rect[1] + px[1] < rect[3]):
                raise ValueError('subject_out_of_frame:%s:%s'
                                 % (scope_name, name))


def pad_label(idx):
    return PAD_LABELS[idx] if idx < len(PAD_LABELS) else 'grip.pad_%d' % idx


def _shift(px, x0, y0):
    return (px[0] + x0, px[1] + y0) if px else None


TICK_TEXT = 'dt=0.005s'


def draw_viewport(tile, rect, view, mode, tick, scene, cam):
    """One tile of the sheet. Diagnostic rows carry the declared layers,
    labels, support states and release telemetry; clean rows are
    geometry-only. The pads are drawn at their MEASURED TRACE poses."""
    draw = ImageDraw.Draw(tile)
    x0, y0, x1, y1 = rect
    project, _basis = make_projector(cam['position'], cam['target'],
                                     cam['fov'], x1 - x0, y1 - y0,
                                     cam.get('up', (0.0, 0.0, 1.0)))
    drawn = []
    for pad in scene['pads']:
        pt = pad['per_tick'][tick]
        drawn.append({'idx': pad['idx'], 'verts': pt['verts'],
                      'cen': pt['cen'], 'n': pad['n'],
                      'edges': pad['edges']})
    subjects = cam['framing_scope'](scene, drawn, tick)
    in_frame_gate(project, subjects, [x0, y0, x1, y1], view + ':' + mode)
    # trunk wireframe (the outline conceals nothing)
    edge_color = TRUNK_EDGE if mode == 'diagnostic' else TRUNK_CLEAN
    for a_i, b_i in scene['trunk_segs']:
        pa, pb = project(scene['vs6'][a_i]), project(scene['vs6'][b_i])
        if pa and pb:
            draw.line([x0 + pa[0], y0 + pa[1], x0 + pb[0], y0 + pb[1]],
                      fill=edge_color, width=1)
    # pads at the measured falling poses
    row = scene['rows'][tick - 1]
    for pad in drawn:
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
    # diagnostic layers (drawn at the CURRENT measured pose)
    for pad, prow in zip(drawn, row['pads']):
        c0 = pad['cen']
        # contact normals and forces (lengths carry the recorded impulses)
        arrow(draw, lambda p: _shift(project(p), x0, y0), c0, pad['n'],
              60.0 * max(prow['jn_sum_Ns'], 0.0) / gc.PRESS_JN_NS + 8.0,
              NORMAL_ARROW)
        grav = (0.0, 0.0, -1.0)
        arrow(draw, lambda p: _shift(project(p), x0, y0), c0, grav,
              60.0 * max(prow['jt_sum_Ns'], 0.0) / gc.PRESS_JN_NS + 8.0,
              FORCE_ARROW)
        # joint/frame axes
        draw_triad(draw, lambda p: _shift(project(p), x0, y0),
                   gc.vadd(c0, gc.vscale(pad['n'], 0.02)), 0.02)
        # attachment patch endpoint id + support state
        lbl = pad_label(pad['idx'])
        state = ('RELEASE' if row['phase'] == 'release'
                 else prow['mode'].upper())
        color = (STATE_RELEASE if state == 'RELEASE'
                 else STATE_COLORS.get(prow['mode'], LABEL_COLOR))
        sp = project(gc.vadd(c0, gc.vscale(pad['n'], 0.055)))
        if sp:
            draw.text((x0 + sp[0], y0 + sp[1]), '%s %s' % (lbl, state),
                      fill=color)
    draw.text((x0 + 8, y0 + 4), '%s [diagnostic] tick %d %s'
              % (view, tick, TICK_TEXT), fill=TITLE_COLOR)
    draw.text((x0 + 8, y0 + 22),
              'layers: ' + ', '.join(DIAG_LAYERS), fill=TITLE_COLOR)
    draw.text((x0 + 8, y0 + 36),
              'tendon paths: ABSENT in this fixture (inventoried)',
              fill=TITLE_COLOR)
    sample = scene['samples'][tick - 1]
    ok = (sample['t_tick'] == tick
          and sample['t_dt_s'] == gc.load_interface().DT
          and abs(sample['t_seconds'] - tick * 0.005) <= 1e-12
          and sample['t_phase'] == row['phase'])
    if not ok:
        raise ValueError('telemetry_sample_unbound:tick %d' % tick)
    fall = scene['trace_scen']['rows'][tick - 1]['pads'][0][
        'disp_down_m_cum']
    draw.text((x0 + 8, y0 + 50),
              'obs t=%.3fs %s dt=%.3fs supported=%d/%d'
              % (sample['t_seconds'], sample['t_phase'], sample['t_dt_s'],
                 int(sample['agg_support_count']),
                 scene['header']['n_channels']),
              fill=TITLE_COLOR)
    draw.text((x0 + 8, y0 + 64),
              'release: press off, fall disp pad0 %.6f m' % fall,
              fill=STATE_RELEASE if row['phase'] == 'release'
              else TITLE_COLOR)


# ------------------------------------------------------------- cameras

def build_cameras(scene):
    cams = {}
    cen0 = scene['pads'][0]['cen0']
    n0 = scene['pads'][0]['n']
    # V0 overview: the whole pinned trunk wireframe (conceals nothing) and
    # every pad channel across the full fall corridor, framed from +x
    cams[VIEWS[0]] = {'position': (1.45, 0.0, 0.62),
                      'target': (0.0, 0.0, 0.52), 'fov': 50.0,
                      'near': 0.01, 'far': 10.0,
                      'framing_scope': lambda s, drawn, tick: [
                          ('trunk_01.lateral',
                           [s['vs6'][i] for i in s['corner_verts']]),
                      ] + [('grip.pad_%d' % p['idx'], list(p['verts']))
                           for p in drawn]}
    # V1 close-up: the sealed S1 channel interface framed over the FULL
    # FALL CORRIDOR (fixture pose z=0.386 down to the tick-56 measured
    # pose), so the drawn subject is in frame at every snapshot tick. The
    # creature wrist/digit anatomy is ABSENT in records and is not faked.
    cams[VIEWS[1]] = {'position': gc.vadd(cen0, gc.vscale(n0, 0.55)),
                      'target': (cen0[0], cen0[1], 0.30), 'fov': 46.0,
                      'near': 0.005, 'far': 2.0,
                      'framing_scope': lambda s, drawn, tick: [
                          ('grip.pad_0', list(drawn[0]['verts'])),
                          ('contact.s1.centroid', [drawn[0]['cen']]),
                          ('contact.s1.arrow_extent',
                           [gc.vadd(drawn[0]['cen'],
                                    gc.vscale(drawn[0]['n'], 0.07)),
                            gc.vadd(drawn[0]['cen'], (0, 0, 0.07)),
                            gc.vadd(drawn[0]['cen'], (0, 0, -0.07))]),
                      ]}
    # V2 top-down along the trunk axis: every loaded interface at 120
    # degree spacing, nothing occluded (anti-concealment view)
    cams[VIEWS[2]] = {'position': (0.0, 0.0, 1.45),
                      'target': (0.0, 0.0, 0.52), 'fov': 46.0,
                      'near': 0.01, 'far': 5.0, 'up': (0.0, 1.0, 0.0),
                      'framing_scope': lambda s, drawn, tick: [
                          ('trunk_01.lateral',
                           [s['vs6'][i] for i in s['corner_verts']]),
                      ] + [('grip.pad_%d' % p['idx'], list(p['verts']))
                           for p in drawn]}
    for view, cam in cams.items():
        d = gc.vlen(gc.vsub(cam['position'], cam['target']))
        xc, yc, zc = look_at(cam['position'], cam['target'],
                             cam.get('up', (0.0, 0.0, 1.0)))
        cam['distance'] = d
        cam['quaternion'] = quat_from_basis(xc, yc, zc)
    return cams


def camera_record(view, cam):
    samples = [{'tick': 1, 'position': list(cam['position']),
                'target': list(cam['target']),
                'distance_to_target': cam['distance'],
                'orientation': list(cam['quaternion'])},
               {'tick': 60, 'position': list(cam['position']),
                'target': list(cam['target']),
                'distance_to_target': cam['distance'],
                'orientation': list(cam['quaternion'])}]
    return {
        'frame_id': 'mat2-g07-%s' % view,
        'coordinate_unit': 'm',
        'handedness': 'right',
        'orientation_convention': 'quaternion_wxyz_camera_to_frame',
        'forward_axis': '-Z', 'up_axis': '+Y',
        'near_far_planes': [cam['near'], cam['far']],
        'viewport_resolution': [VP_W, VP_H],
        'aspect_ratio': VP_W / VP_H,
        'projection': 'perspective',
        'vertical_fov_degrees': cam['fov'],
        'sample_mode': 'fixed_bookmark',
        'samples': samples,
        'camera_motion_or_bookmark_sequence':
            'fixed bookmark: identical pose at every declared snapshot '
            'tick (the FALL is carried by the measured pad poses, not by '
            'camera motion)',
        'state_or_tick_interval':
            'tick_interval [1, 60]; frames at declared snapshot ticks %s; '
            '%s' % (list(SNAPSHOT_TICKS), TICK_MAP),
    }


def main():
    out = HERE / 'evidence' / 'capture'
    out.mkdir(parents=True, exist_ok=True)
    lc = gc.load_interface()
    geom = gc.load_trunk_geometry()
    trace = load_battery_states()
    scen = trace['scenarios']['scene|n=3']   # the capture scenario
    rows = scen['rows']
    samples = scen['samples']                # the DELIVERED observation
    acct = scen['acct_rows']
    assert len(samples) == len(rows), 'observation_rows_mismatch'
    centroids = acct   # measured per-tick account rows (centroid_z per pad)
    pads = pad_layouts(geom, scen['header']['n_channels'])
    # rebuild the measured centroids in 3D: the pads translate rigidly, so
    # the x/y stay at the fixture values and z is the measured centroid z
    for k, pad in enumerate(pads):
        for tick in SNAPSHOT_TICKS:
            cm_z = acct[tick - 1]['pads'][k]['centroid_z_m']
            d_z = cm_z - pad['cen0'][2]
            cm = gc.vadd(pad['cen0'], (0.0, 0.0, d_z))
            d = gc.vsub(cm, pad['cen0'])
            pad['per_tick'][tick] = {
                'verts': [gc.vadd(v, d) for v in pad['verts0']],
                'cen': cm}
    corner_idx = sorted({i for ti in geom['lateral_indices']
                         for i in geom['triangles'][ti]})
    scene = {
        'vs6': geom['vertices_m06'],
        'trunk_segs': trunk_wireframe(geom),
        'pads': pads,
        'rows': rows,
        'samples': samples,
        'header': scen['header'],
        'corner_verts': corner_idx,
        'trace_scen': scen,
    }
    cams = build_cameras(scene)
    records = {view: camera_record(view, cams[view]) for view in VIEWS}
    # reprojection oracle self-check: the drawn anchors (fixture pose and
    # a falling snapshot pose) must reproject within 1 px per view
    oracle = []
    for view in VIEWS:
        cam = cams[view]
        pts = [('fixture', pads[0]['cen0']),
               ('tick56', pads[0]['per_tick'][56]['cen'])]
        for name, p in pts:
            if view == VIEWS[1] and name == 'fixture':
                pass   # the close-up oracle uses both poses too
            got = project_from_record(
                {'position': list(cam['position']),
                 'orientation': list(cam['quaternion'])},
                cam['fov'], VP_W, VP_H, p)
            project, _ = make_projector(cam['position'], cam['target'],
                                        cam['fov'], VP_W, VP_H,
                                        cam.get('up', (0.0, 0.0, 1.0)))
            want = project(p)
            if got is None or want is None:
                raise ValueError('oracle_anchor_missing:' + view)
            dpx = math.hypot(got[0] - want[0], got[1] - want[1])
            oracle.append({'view': view, 'anchor': name, 'delta_px': dpx})
            if dpx > 1.0:
                raise ValueError('oracle_reprojection_mismatch:' + view)
    frames = []
    presence = {'schema': 'chimera.g07_pixel_presence.v1', 'frames': []}
    for fi, tick in enumerate(SNAPSHOT_TICKS):
        sheet = Image.new('RGB', SHEET, BG)
        frame_state = json.dumps(
            {'tick': tick,
             'rows': [{k: v for k, v in r.items() if k != 'disp_tick_m'}
                      for r in rows[tick - 1:tick]]},
            sort_keys=True).encode('utf-8')
        state_sha = hashlib.sha256(frame_state).hexdigest()
        counts = {}
        for view in VIEWS:
            for mode in ('diagnostic', 'clean'):
                rect = TILE_RECTS['%s:%s' % (view, mode)]
                tile = sheet.crop(rect)
                draw_viewport(tile, [0, 0, rect[2] - rect[0],
                                     rect[3] - rect[1]],
                              view, mode, tick, scene, cams[view])
                exact = {}
                targets = presence_targets(mode)
                color_counts = {}
                for cnt, col in tile.getcolors(maxcolors=1 << 20):
                    color_counts[col] = cnt
                for name, color in targets.items():
                    exact[name] = color_counts.get(color, 0)
                counts['%s:%s' % (view, mode)] = exact
                sheet.paste(tile, (rect[0], rect[1]))
        fname = 'frame_%02d.png' % fi
        sheet.save(out / fname, 'PNG', optimize=False)
        sha = hashlib.sha256((out / fname).read_bytes()).hexdigest()
        frames.append({'frame': fname, 'tick': tick, 'sha256': sha,
                       'state_hash': state_sha})
        presence['frames'].append({'frame': fname, 'tick': tick,
                                   'state_hash': state_sha,
                                   'exact_color_counts': counts})
    # presence gate: every required subject has pixels in EVERY frame
    failures = []
    for fr in presence['frames']:
        for key, counts in fr['exact_color_counts'].items():
            mode = key.split(':')[-1]
            required = (['trunk', 'pad_edge'] if mode == 'clean' else
                        ['trunk', 'pad_edge', 'pad_fill', 'normal_arrow',
                         'force_arrow'])
            for name in required:
                if counts.get(name, 0) <= 0:
                    failures.append('%s:%s missing %s'
                                    % (fr['frame'], key, name))
    if failures:
        presence['failures'] = failures
        (out / 'pixel_presence.json').write_bytes(rfa.canonical(presence))
        raise ValueError('required_subject_pixels_missing:' +
                         '; '.join(failures[:5]))
    (out / 'pixel_presence.json').write_bytes(rfa.canonical(presence))
    (out / 'cameras.json').write_bytes(rfa.canonical({
        'views': VIEWS, 'view_realization': VIEW_REALIZATION,
        'records': records, 'snapshot_ticks': list(SNAPSHOT_TICKS),
        'oracle': oracle, 'diagnostic_layers': DIAG_LAYERS,
        'tick_map': TICK_MAP,
        'absent_components': ['creature body', 'wrist/digit anatomy',
                              'tendon paths', 'joint axes of the creature '
                              '(only declared fixture frame axes drawn)'],
    }))
    print(json.dumps({'frames': len(frames),
                      'oracle_max_delta_px': max(o['delta_px']
                                                 for o in oracle),
                      'presence_failures': 0}, indent=1))


if __name__ == '__main__':
    main()
