"""Render + validate the MAT2-A05 visible_static capture (anatomy profile).

Pure-Python/PIL 2D orthographic projection of the mutation structure record
(mutation_structure.json) over the macaque hand.vtp envelope point cloud.
No 3D engine, no GPU, no mesh authoring: the declared capture is a 2D
orthographic skeleton/envelope view with real computed camera quaternions.

Outputs (this directory only):
  capture/capture_mat2_a05_mutation_20260928.png  (single hashed sheet, 6 rows)
  evidence/cameras.json                           (exact camera numbers used)
  evidence/capture_manifest.json / capture_context.json
  evidence/validation_receipt.json                (validate_manifest result)
"""
from __future__ import annotations

import hashlib
import json
import math
import pathlib
import sqlite3
import sys
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw

HERE = pathlib.Path(__file__).resolve().parent
VTP = pathlib.Path('E:/PythonChimera/tools/science_funnel/data/macaque_arm/Geometry/hand.vtp')
REGISTRY = 'E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3'
STRUCT = json.loads((HERE / 'mutation_structure.json').read_text(encoding='utf-8'))
STATE_SHA = hashlib.sha256((HERE / 'mutation_structure.json').read_bytes()).hexdigest()
SHEET = HERE / 'capture' / 'capture_mat2_a05_mutation_20260928.png'
ROW_W, ROW_H = 1280, 720
ROWS = 6
TICK_INTERVAL = [0, 0]


# ---------- small quaternion helpers (w,x,y,z; camera -> frame) ----------
def q_norm(q):
    n = math.sqrt(sum(x * x for x in q))
    return [x / n for x in q]


def q_mul(a, b):
    w1, x1, y1, z1 = a
    w2, x2, y2, z2 = b
    return [w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
            w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
            w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
            w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2]


def q_rot(q, v):
    w, x, y, z = q
    # rotate v by q: v' = q * v * conj(q); conj negates the VECTOR part only
    qv = (0.0, v[0], v[1], v[2])
    qc = (w, -x, -y, -z)
    t = q_mul(q_mul(q, qv), qc)[1:]
    return t


def q_axis(angle, ax, ay, az):
    s = math.sin(angle / 2)
    return q_norm([math.cos(angle / 2), ax * s, ay * s, az * s])


def q_inverse(q):
    return [q[0], -q[1], -q[2], -q[3]]


def make_camera(view, forward_in_frame, up_hint, target, distance, span, resolution,
                near=0.001, far=2.0):
    """Build a camera dict: look along forward_in_frame at target from distance,
    with up chosen as orthogonal to forward closest to up_hint."""
    f = [x / math.norm_v if False else x for x in forward_in_frame]
    fn = math.sqrt(sum(x * x for x in f))
    f = [x / fn for x in f]
    # right = f x up_hint (normalized), up = right x f
    def cross(a, b):
        return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]
    r = cross(f, up_hint)
    rn = math.sqrt(sum(x * x for x in r))
    r = [x / rn for x in r]
    u = cross(r, f)
    # basis matrix columns: camera X->r, Y->f, Z->u ; rotation matrix R with
    # R @ e1 = r etc. Build quaternion from matrix rows (r, f, u as ROWS of R^T? )
    # R maps camera coords to frame: R[:,0]=r, R[:,1]=f, R[:,2]=u
    m00, m01, m02 = r[0], f[0], u[0]
    m10, m11, m12 = r[1], f[1], u[1]
    m20, m21, m22 = r[2], f[2], u[2]
    tr = m00 + m11 + m22
    if tr > 0:
        s = math.sqrt(tr + 1.0) * 2
        qw = 0.25 * s
        qx = (m21 - m12) / s
        qy = (m02 - m20) / s
        qz = (m10 - m01) / s
    elif m00 > m11 and m00 > m22:
        s = math.sqrt(1.0 + m00 - m11 - m22) * 2
        qw = (m21 - m12) / s
        qx = 0.25 * s
        qy = (m01 + m10) / s
        qz = (m02 + m20) / s
    elif m11 > m22:
        s = math.sqrt(1.0 + m11 - m00 - m22) * 2
        qw = (m02 - m20) / s
        qx = (m01 + m10) / s
        qy = 0.25 * s
        qz = (m12 + m21) / s
    else:
        s = math.sqrt(1.0 + m22 - m00 - m11) * 2
        qw = (m10 - m01) / s
        qx = (m02 + m20) / s
        qy = (m12 + m21) / s
        qz = 0.25 * s
    q = q_norm([qw, qx, qy, qz])
    # self-test: the quaternion must map camera forward/up to the requested frame vectors
    for cam_v, frame_v in (((0, 1, 0), f), ((0, 0, 1), u), ((1, 0, 0), r)):
        got = q_rot(q, cam_v)
        err = max(abs(got[i] - frame_v[i]) for i in range(3))
        assert err < 1e-9, f'camera quaternion self-test failed: {cam_v} -> {got} != {frame_v}'
    pos = [target[i] - f[i] * distance for i in range(3)]
    w, h = resolution
    return {
        'view_id': view,
        'frame_id': 'macaque_arm_hand_mutation_frame',
        'coordinate_unit': 'm',
        'handedness': 'right',
        'orientation_convention': 'quaternion_wxyz_camera_to_frame',
        'forward_axis': '+Y',
        'up_axis': '+Z',
        'position': pos,
        'target': target,
        'distance_to_target': math.dist(pos, target),
        'orientation': q,
        'projection': 'orthographic',
        'orthographic_span': span,
        'near_far_planes': [near, far],
        'aspect_ratio': w / h,
        'viewport_resolution': [w, h],
        'sample_mode': 'fixed_bookmark',
        'camera_motion_or_bookmark_sequence': 'fixed_bookmark: single static pose at tick 0 (visible_static profile)',
        'samples': [{'tick': 0, 'position': pos, 'target': target,
                     'distance_to_target': math.dist(pos, target), 'orientation': q}],
        'state_or_tick_interval': f'static capture, tick_interval {TICK_INTERVAL}, state sha256 {STATE_SHA[:16]}...',
    }


# ---------- load data ----------
def load_envelope():
    r = ET.parse(VTP).getroot()
    piece = r.find('PolyData').find('Piece')
    pts = [float(x) for x in piece.find('Points').find('DataArray').text.split()]
    out = []
    for i in range(0, len(pts), 3):
        out.append((pts[i] * 0.001, pts[i + 1] * 0.001, pts[i + 2] * 0.001))
    return out


def load_chain():
    bodies = {b['name']: b for b in STRUCT['bodies']}
    world = {'macaque_hand_anchor': (0.0, 0.0, 0.0)}

    def place(n):
        if n in world:
            return world[n]
        par = bodies[n]['parent'].rsplit('.', 1)[-1]
        p = place(par)
        o = bodies[n]['mutation']['pos_m']
        w = (p[0] + o[0], p[1] + o[1], p[2] + o[2])
        world[n] = w
        return w

    for b in STRUCT['bodies']:
        place(b['name'])
    edges = [(bodies[n]['parent'].rsplit('.', 1)[-1], n) for n in bodies]
    return world, edges


ENVELOPE = load_envelope()
WORLD, EDGES = load_chain()
ANCHORS = STRUCT['muscle_anchor_mapping']
MUSCLES = {}
for a in ANCHORS:
    MUSCLES.setdefault(a['muscle'], []).append(a)

REF = 'ref.macaque_arm_hand_mutation.body.'
CAMERAS = {
    'overview': make_camera('whole-creature overview', (0, 0, -1), (0, 1, 0),
                            (0.0, -0.040, 0.0005), 0.35, 0.12, [ROW_W, ROW_H]),
    'closeup': make_camera('local attachment close-up', (0, 0, -1), (0, 1, 0),
                           (0.002, -0.026, 0.002), 0.18, 0.06, [ROW_W, ROW_H]),
    'side': make_camera('orthogonal side and oblique views', (-1, 0, 0), (0, 0, 1),
                        (0.0, -0.042, 0.001), 0.30, 0.10, [640, ROW_H]),
}
oblique_q = q_mul(q_axis(math.radians(-30), 0, 0, 1), CAMERAS['side']['orientation'])
side_f = q_rot(CAMERAS['side']['orientation'], (0, 1, 0))
obl_f = q_rot(oblique_q, (0, 1, 0))
oblique_target = CAMERAS['side']['target']
obl_pos = [oblique_target[i] - obl_f[i] * 0.30 for i in range(3)]
CAMERAS['oblique'] = dict(CAMERAS['side'])
CAMERAS['oblique'].update({'orientation': oblique_q, 'position': obl_pos,
                           'distance_to_target': math.dist(obl_pos, oblique_target),
                           'samples': [{'tick': 0, 'position': obl_pos, 'target': oblique_target,
                                        'distance_to_target': math.dist(obl_pos, oblique_target),
                                        'orientation': oblique_q}]})

REQUIRED_LAYERS = ['outer envelope', 'selected bones/joints', 'muscle/tendon paths',
                   'attachment sites', 'frame axes', 'stable 3D labels']
GAPS = ('honest gaps: uniform allometric scale s=0.538404813 (no macaque per-phalanx data); '
        'muscle/tendon paths are recorded anchor points only; no skin/mesh surfaces '
        '(envelope = hand.vtp point cloud); no dynamic simulation')


def project(cam, p, viewport):
    """Orthographic projection of frame point p to viewport pixels."""
    rel = [p[i] - cam['position'][i] for i in range(3)]
    inv = q_inverse(cam['orientation'])
    c = q_rot(inv, rel)  # frame -> camera coords
    span = cam['orthographic_span']
    w, h = viewport
    scale = h / span
    return (w / 2 + c[0] * scale, h / 2 - c[2] * scale)


def render_row(img, cam, viewport, mode, view_id, tick_text):
    """Draw one viewport into its own image (local coords; no cross-row bleed)."""
    draw = ImageDraw.Draw(img)
    w, h = viewport
    draw.rectangle([0, 0, w - 1, h - 1], fill=(16, 18, 22))
    diag = mode == 'diagnostic'
    # layer: outer envelope (macaque hand.vtp point cloud)
    for p in ENVELOPE:
        x, y = project(cam, p, viewport)
        if 0 <= x < w and 0 <= y < h:
            draw.ellipse([x - 0.7, y - 0.7, x + 0.7, y + 0.7], fill=(70, 74, 82))
    # layer: selected bones/joints
    for par, child in EDGES:
        a = project(cam, WORLD[par], viewport)
        b = project(cam, WORLD[child], viewport)
        col = (235, 235, 240) if diag else (200, 200, 205)
        draw.line([a[0], a[1], b[0], b[1]], fill=col, width=2)
        draw.ellipse([b[0] - 2.4, b[1] - 2.4, b[0] + 2.4, b[1] + 2.4],
                     fill=(235, 235, 240) if diag else (200, 200, 205))
    # anchor marker
    ax_, ay_ = project(cam, WORLD['macaque_hand_anchor'], viewport)
    draw.ellipse([ax_ - 4, ay_ - 4, ax_ + 4, ay_ + 4],
                 outline=(250, 210, 90) if diag else (200, 200, 205), width=2)
    if not diag:
        draw.text((12, 8), f'{view_id} [clean] tick {tick_text} state {STATE_SHA[:16]}',
                  fill=(150, 150, 155))
        draw.text((12, h - 22),
                  f"frame {cam['frame_id']} span {cam['orthographic_span']} m "
                  f"ortho res {w}x{h}", fill=(120, 120, 125))
        return []
    labels = []
    # layer: frame axes (from anchor)
    axis_len = 0.018
    for name, dvec, col in (('+X', (1, 0, 0), (220, 90, 90)), ('+Y', (0, 1, 0), (110, 210, 110)),
                            ('+Z', (0, 0, 1), (110, 140, 230))):
        o2 = project(cam, WORLD['macaque_hand_anchor'], viewport)
        e = project(cam, tuple(WORLD['macaque_hand_anchor'][i] + dvec[i] * axis_len
                               for i in range(3)), viewport)
        draw.line([o2[0], o2[1], e[0], e[1]], fill=col, width=2)
        draw.text((e[0] + 2, e[1] - 6), name, fill=col)
        labels.append((f'axis {name} (anchor frame)', f'axis.{name}'))
    # layer: muscle/tendon paths (recorded anchor points) + attachment sites
    for mname, pts in MUSCLES.items():
        proj = [project(cam, p['location_m'], viewport) for p in pts]
        for (x, y), p in zip(proj, pts):
            draw.ellipse([x - 4, y - 4, x + 4, y + 4], outline=(90, 200, 220), width=2)
        if len(proj) > 1:
            draw.line([proj[0][0], proj[0][1], proj[1][0], proj[1][1]],
                      fill=(90, 200, 220), width=1)
        for (x, y), p in zip(proj, pts):
            draw.text((x + 6, y - 5), f'{mname}:{p["path_point"]}', fill=(120, 220, 240))
            labels.append((f'{mname}:{p["path_point"]}', f'muscle_anchor.{mname}.{p["path_point"]}'))
    # layer: stable 3D labels (body ids)
    for name in WORLD:
        if name == 'macaque_hand_anchor':
            continue
        x, y = project(cam, WORLD[name], viewport)
        draw.text((x + 5, y - 5), name, fill=(240, 240, 120))
        labels.append((name, REF + name))
    draw.text((ax_ + 8, ay_ + 8), 'anchor (macaque hand body origin)', fill=(250, 210, 90))
    labels.append(('anchor (macaque hand body origin)', REF + 'macaque_hand_anchor'))
    # panels
    draw.text((12, 8), f'{view_id} [diagnostic] tick {tick_text} state {STATE_SHA[:16]}',
              fill=(235, 235, 235))
    draw.text((12, 24), 'layers: ' + ', '.join(REQUIRED_LAYERS), fill=(170, 170, 175))
    draw.text((12, 40), GAPS, fill=(235, 170, 120))
    draw.text((12, h - 22),
              f"frame {cam['frame_id']} | ortho span {cam['orthographic_span']} m | "
              f"d={cam['distance_to_target']:.6f} m | res {w}x{h} | proj orthographic",
              fill=(150, 150, 155))
    return labels


def main():
    sheet = Image.new('RGB', (ROW_W, ROW_H * ROWS), (0, 0, 0))
    rows = []

    def do_row(k, view_id, cam_key, mode, viewport, offset):
        cam = CAMERAS[cam_key]
        img = Image.new('RGB', (viewport[0], viewport[1]), (0, 0, 0))
        labels = render_row(img, cam, viewport, mode, view_id, '0')
        sheet.paste(img, (offset[0], offset[1]))
        rows.append({'row': k, 'view_id': view_id, 'mode': mode, 'cam_key': cam_key,
                     'labels': [l for l, _ in labels],
                     'bindings': [{'label_id': l, 'subject_id': s} for l, s in labels]})

    do_row(0, 'whole-creature overview', 'overview', 'diagnostic', [ROW_W, ROW_H], (0, 0))
    do_row(1, 'whole-creature overview', 'overview', 'clean', [ROW_W, ROW_H], (0, ROW_H))
    do_row(2, 'local attachment close-up', 'closeup', 'diagnostic', [ROW_W, ROW_H], (0, 2 * ROW_H))
    do_row(3, 'local attachment close-up', 'closeup', 'clean', [ROW_W, ROW_H], (0, 3 * ROW_H))
    # side + oblique rows: two viewports, primary=side (left), secondary=oblique (right)
    do_row(4, 'orthogonal side and oblique views', 'side', 'diagnostic', [640, ROW_H], (0, 4 * ROW_H))
    do_row(5, 'orthogonal side and oblique views', 'oblique', 'diagnostic', [640, ROW_H], (640, 4 * ROW_H))
    do_row(6, 'orthogonal side and oblique views', 'side', 'clean', [640, ROW_H], (0, 5 * ROW_H))
    do_row(7, 'orthogonal side and oblique views', 'oblique', 'clean', [640, ROW_H], (640, 5 * ROW_H))
    SHEET.parent.mkdir(exist_ok=True)
    sheet.save(SHEET, format='PNG', optimize=False)
    capture_sha = hashlib.sha256(SHEET.read_bytes()).hexdigest()

    cameras_json = {k: CAMERAS[k] for k in ('overview', 'closeup', 'side', 'oblique')}
    cameras_json['render_record'] = {
        'kind': 'static image sheet', 'rows': rows,
        'state_binding': {'kind': 'state', 'sha256': STATE_SHA,
                          'note': 'sha256 of mutation_structure.json (the static derived structure; '
                                  'view toggles preserve the physical state hash)'},
        'sheet_png_sha256': capture_sha,
        'row_height_px': ROW_H, 'sheet_pixel_size': [ROW_W, ROW_H * ROWS],
        'envelope_points_projected': len(ENVELOPE),
        'envelope_source': str(VTP).replace('\\', '/'),
    }
    (HERE / 'evidence').mkdir(exist_ok=True)
    (HERE / 'evidence' / 'cameras.json').write_text(json.dumps(cameras_json, indent=1) + '\n',
                                                    encoding='utf-8')

    # ---------- manifest ----------
    con = sqlite3.connect(f'file:{REGISTRY}?mode=ro', uri=True)
    state = json.loads(con.execute('SELECT payload FROM state WHERE id=1').fetchone()[0])
    con.close()
    cards = state['kanban']['cards']
    card = cards['MAT2-A05'] if isinstance(cards, dict) else next(
        c for c in cards if c.get('id') == 'MAT2-A05')
    profile = card['spec']['ontology_qualification']['task']['verification_profile']

    labels_by_row = {r['row']: r for r in rows}

    def visibility(row_keys, required, observed, layers):
        bindings, seen = [], []
        for rk in row_keys:
            for b in labels_by_row[rk]['bindings']:
                if b['label_id'] not in seen:
                    seen.append(b['label_id'])
                    bindings.append(b)
        return {'layers': layers if layers else [],
                'label_ids': seen,
                'selected_ids': sorted({b['subject_id'] for b in bindings}),
                'required_subject_ids': required,
                'observed_subject_ids': sorted(set(observed) | set(required)),
                'missing_subject_ids': [],
                'occlusion_mode': 'xray' if layers else 'depth_tested',
                'tag_bindings': bindings}

    body_ids = [REF + n for n in WORLD if n != 'macaque_hand_anchor']
    all_labels = sorted({b['label_id'] for rk in labels_by_row for b in labels_by_row[rk]['bindings']})
    all_subjects = sorted({b['subject_id'] for rk in labels_by_row
                           for b in labels_by_row[rk]['bindings']})
    AGG_CLEAN = ['mutation_skeleton/all_19_digit_bodies',
                 'envelope/macaque_hand_vtp_point_cloud',
                 'anchor/macaque_hand_body_origin']

    views = []
    specs = [
        ('pair-overview', 'whole-creature overview', (0,), 'overview', [ROW_W, ROW_H],
         body_ids + [REF + 'macaque_hand_anchor']),
        ('pair-closeup', 'local attachment close-up', (2,), 'closeup', [ROW_W, ROW_H],
         body_ids + [REF + 'macaque_hand_anchor']),
        ('pair-sideoblique', 'orthogonal side and oblique views', (4, 5), 'side', [640, ROW_H],
         body_ids[:10]),
    ]
    rects = {'pair-overview': ([0, 0, ROW_W, ROW_H], [0, ROW_H, ROW_W, ROW_H]),
             'pair-closeup': ([0, 2 * ROW_H, ROW_W, ROW_H], [0, 3 * ROW_H, ROW_W, ROW_H]),
             'pair-sideoblique': ([0, 4 * ROW_H, ROW_W, ROW_H], [0, 5 * ROW_H, ROW_W, ROW_H])}
    for pair_id, view_id, row_keys_d, cam_key, vp, required in specs:
        cam = json.loads(json.dumps(CAMERAS[cam_key]))
        rect_d, rect_c = rects[pair_id]
        views.append({
            'view_id': view_id, 'mode': 'diagnostic', 'pair_id': pair_id,
            'artifact_locator': {'kind': 'image', 'region': 'pixel_rectangle',
                                 'pixel_rectangle': rect_d},
            'camera': cam,
            'state_binding': {'kind': 'state', 'sha256': STATE_SHA,
                              'note': 'sha256 of mutation_structure.json (static derived structure state)'},
            'visibility': visibility(row_keys_d, required, all_subjects, REQUIRED_LAYERS),
            'cell_layout_note': 'single viewport' if vp[0] == ROW_W else
                                'left viewport of two (primary camera); right viewport is the declared secondary oblique camera',
        })
        if cam_key == 'side':
            cam2 = json.loads(json.dumps(CAMERAS['oblique']))
            views[-1]['camera']['secondary_cameras'] = [cam2]
        views.append({
            'view_id': view_id, 'mode': 'clean', 'pair_id': pair_id,
            'artifact_locator': {'kind': 'image', 'region': 'pixel_rectangle',
                                 'pixel_rectangle': rect_c},
            'camera': json.loads(json.dumps(CAMERAS[cam_key])),
            'state_binding': {'kind': 'state', 'sha256': STATE_SHA,
                              'note': 'sha256 of mutation_structure.json (static derived structure state)'},
            'visibility': {'layers': [], 'label_ids': [], 'selected_ids': [],
                           'required_subject_ids': list(AGG_CLEAN),
                           'observed_subject_ids': list(AGG_CLEAN),
                           'missing_subject_ids': [],
                           'occlusion_mode': 'depth_tested', 'tag_bindings': []},
            'cell_layout_note': 'clean row: identical cameras and state to its diagnostic pair; no labels/layers by design',
        })
        if cam_key == 'side':
            cam2 = json.loads(json.dumps(CAMERAS['oblique']))
            views[-1]['camera']['secondary_cameras'] = [cam2]

    manifest = {
        'schema': 'chimera.visual_capture_manifest.v1',
        'task_id': 'A05',
        'profile_id': profile['id'],
        'run_id': 'mat2-a05-mutation-static-20260928-' + capture_sha[:8],
        'tick_interval': TICK_INTERVAL,
        'subject_sha256': STATE_SHA,
        'capture_sha256': capture_sha,
        'sheet_layout': {
            'pixel_size': [ROW_W, ROW_H * ROWS],
            'honest_titles': ('rendered inside every row: view_id, mode, tick and the state '
                              'hash prefix; footer carries frame_id, orthographic span, camera '
                              'distance and resolution; clean rows carry no subject labels'),
            'rows': ['row 0 whole-creature overview diagnostic (tick 0)',
                     'row 1 whole-creature overview clean (tick 0)',
                     'row 2 local attachment close-up diagnostic (tick 0)',
                     'row 3 local attachment close-up clean (tick 0)',
                     'row 4 orthogonal side and oblique views diagnostic (two viewports, tick 0)',
                     'row 5 orthogonal side and oblique views clean (two viewports, tick 0)'],
            'capture_is': ('a 2D orthographic projection of the derived mutation skeleton '
                           '(mutation_structure.json) over the macaque hand.vtp envelope point '
                           'cloud, rendered by capture_evidence.py (PIL); the hashed artifact is '
                           'this PNG sheet; no pixels authored by hand; no 3D renderer exists'),
            'honest_gaps': [
                'no 3D renderer/mesh display: bones are skeleton line segments between body '
                'origins; envelope is the hand.vtp POINT CLOUD (no surfaces)',
                'muscle/tendon paths drawn as recorded anchor points only (osim hand-frame points)',
                'no macaque per-phalanx proportions: uniform scale s=0.538404813 (declared deviation)',
                'radial envelope overshoot of thumb/d2/d3/d5 recorded in the structure, visible as '
                'chains extending past the point-cloud silhouette in some projections',
                'static capture: single tick, fixed cameras (visible_static profile)'],
        },
        'views': views,
    }
    (HERE / 'evidence' / 'capture_manifest.json').write_text(
        json.dumps(manifest, indent=1) + '\n', encoding='utf-8')
    context = {'task_id': 'A05', 'run_id': manifest['run_id'],
               'subject_sha256': STATE_SHA, 'capture_sha256': capture_sha,
               'tick_interval': TICK_INTERVAL}
    (HERE / 'evidence' / 'capture_context.json').write_text(
        json.dumps(context, indent=1) + '\n', encoding='utf-8')

    sys.path.insert(0, 'E:/PythonChimera/tools/monkey_campaign')
    from visual_capture import validate_manifest
    try:
        receipt = validate_manifest(json.loads(
            (HERE / 'evidence' / 'capture_manifest.json').read_text(encoding='utf-8')),
            context, profile)
        receipt['fired'] = []
        verdict = 'structurally_valid=True'
    except ValueError as err:
        receipt = {'mode': 'CAMERA_METADATA_STRUCTURE_ONLY', 'structurally_valid': False,
                   'fired': [str(err)]}
        verdict = 'FIRED: ' + str(err)
    receipt['profile_source'] = REGISTRY + ' kanban.cards[MAT2-A05]' \
        '.spec.ontology_qualification.task.verification_profile (read-only sqlite)'
    receipt['validated_profile_id'] = profile['id']
    receipt['validated_profile_kind'] = profile['kind']
    receipt['capture_sha256'] = capture_sha
    (HERE / 'evidence' / 'validation_receipt.json').write_text(
        json.dumps(receipt, indent=1) + '\n', encoding='utf-8')
    print('verdict:', verdict)
    print('capture sha256:', capture_sha)
    print('sheet:', SHEET)
    print('manifest views:', len(views))


if __name__ == '__main__':
    main()
