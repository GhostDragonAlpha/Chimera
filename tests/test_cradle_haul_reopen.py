# SPDX-License-Identifier: AGPL-3.0-or-later
"""Offline reopen acceptance for the owned rescue-cradle/haul construction.

A fresh Blender process opens the saved owned project with no live solver,
verifies exact geometry-hash replay of the cached native samples against the
digests recorded by tests/test_cradle_haul_workflow.py, recomputes the seam
loads from the inspector against an independent raw MDD-cache decode, and
confirms the stored Layer Trial A/B pair survives the save/reopen round trip
with the same B-minus-A drop. Playback is cached mesh animation, not a new
physical solve; release/repair remain authoring-level seam edits."""
from pathlib import Path
import hashlib
import json
import math
import struct
import sys
import time
import traceback

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'python'))
import chimera_studio
from chimera_studio import operations as op, layer_editing as ed, layer_trials as lt
from chimera_studio import attachment_loads as loads

sys.path.insert(0, str(ROOT.parent / 'Libuipc/layered-source/integrations/blender/tests'))
from blender_integration import evaluated

BASE = ROOT / 'evidence/cradle-haul/run-01'
PROJECT = BASE / 'Rescue cradle haul.blend'
CHECKS = BASE / 'checks.json'
EVIDENCE = BASE / 'reopen-checks.json'
LAW = 'SoftVertexStitch-v1'

report = {'project': str(PROJECT), 'checks': [], 'pass': False}


def check(name, fn):
    try:
        details = fn()
        report['checks'].append({'name': name, 'pass': True, 'details': details})
        print('PASS', name, flush=True)
    except Exception as exc:
        report['checks'].append({'name': name, 'pass': False, 'error': str(exc),
                                 'traceback': traceback.format_exc()})
        print('FAIL', name, repr(exc), flush=True)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def raw_decode(arc_dir):
    """Independent decode of a bake directory: raw MDD/npz bytes only."""
    request = json.loads((arc_dir / 'request.json').read_text())
    result = json.loads((arc_dir / 'result.json').read_text())
    settings = request['settings']
    outputs = {v['index']: v for v in result['objects']}
    points = {}
    for i, body in enumerate(request['objects']):
        with np.load(arc_dir / f'input_{i:04d}.npz') as a:
            local = a['vertices'].copy()
            matrix = a['matrix'].copy()
        if i in outputs:
            data = (arc_dir / f'object_{i:04d}.mdd').read_bytes()
            frames, n = struct.unpack('>ii', data[:8])
            v = np.frombuffer(data, dtype='>f4', offset=8 + frames * 4).astype(float).reshape(frames, n, 3)
            if outputs[i].get('encoding') == 'AFFINE':
                v = np.asarray([local @ x[1:] + x[0] for x in v])
        else:
            v = local[None, :, :]
            frames = 1
        if frames == 1:
            v = np.repeat(v, result['frames'], axis=0)
        points[body['id']] = (v @ matrix[:3, :3].T + matrix[:3, 3]) * settings['unit_scale']
    return request, result, points


def seam_scalars(request, points):
    out = {}
    for seam in request['settings']['attachments']:
        pair = np.array(seam['pairs'], dtype=int)
        d = points[seam['b']][:, pair[:, 1]] - points[seam['a']][:, pair[:, 0]]
        length = np.sqrt(np.einsum('...i,...i->...', d, d))
        ext = length - np.array(seam['rest_lengths'])
        out[seam['id']] = seam['stiffness'] * ext
    return out


def open_offline():
    recorded = json.loads(CHECKS.read_text(encoding='utf-8'))
    state['recorded'] = recorded
    t0 = time.perf_counter()
    assert bpy.ops.wm.open_mainfile(filepath=str(PROJECT)) == {'FINISHED'}
    bpy.context.view_layer.update()
    state['open_seconds'] = time.perf_counter() - t0
    scene = bpy.context.scene
    state['scene'] = scene
    m = ed.module()
    assert not m.runtime.is_running(), 'Opening the project started native work'
    parts = {o['uipc_object_id']: o for o in scene.objects
             if hasattr(o, 'uipc_body') and o.uipc_body.role != 'NONE'}
    roles = sorted(o.uipc_body.role for o in parts.values())
    assert roles == ['CLOTH', 'FEM', 'FEM', 'RIGID', 'RIGID', 'STATIC'], roles
    atts = list(scene.uipc_settings.attachments)
    assert len(atts) == 2 and all(e.enabled for e in atts)
    for e in atts:
        assert json.loads(e.binding)['law'] == LAW, e.name
    with op.selected_targets(bpy.context, []):
        checked = m.bridge.check_cache(scene, verify_data=True)
    assert checked['frames'] == scene.frame_end + 1, (checked['frames'], scene.frame_end)
    state['module'] = m
    return {'open_seconds': round(state['open_seconds'], 2), 'roles': roles,
            'cached_frames': checked['frames'], 'solver_started': False,
            'recorded_pass': recorded['pass']}


def replay_digests():
    scene = state['scene']
    digests = state['recorded']['geometry_digests']
    worst = {}
    for name, per_frame in digests.items():
        obj = scene.objects[name]
        for frame, expected in per_frame.items():
            got = hashlib.sha256(evaluated(obj, scene, int(frame)).astype('<f4').tobytes()).hexdigest()
            worst[frame] = max(worst.get(frame, 0), 0 if got == expected else 1)
    assert not any(worst.values()), ('Replayed geometry digests differ', worst)
    return {'digest_objects': sorted(digests), 'frames': sorted(worst),
            'playback_error_m': 0.0, 'method': 'sha256 of evaluated mesh cache samples'}


def recompute_loads():
    scene = state['scene']
    s = scene.uipc_settings
    arc_dir = Path(bpy.path.abspath(s.last_bake)).resolve()
    assert BASE in arc_dir.parents, arc_dir
    report_ui = loads.inspect(scene, .6, 1.0)
    assert report_ui['law_reference'].endswith('soft_vertex_stitch.md')
    request, result, points = raw_decode(arc_dir)
    scalars = seam_scalars(request, points)
    rows = {}
    worst = 0.
    for row in report_ui['seams']:
        p = row['peak']
        scalar = scalars[row['id']]
        frame, stitch = np.unravel_index(np.argmax(abs(scalar)), scalar.shape)
        assert p['frame'] == frame + request['settings']['frame_start'] and p['stitch'] == stitch
        worst = max(worst, abs(p['signed_force_N'] - scalar[frame, stitch]),
                    abs(p['absolute_force_N'] - abs(scalar[frame, stitch])))
        rows[row['name']] = {'peak_N': p['absolute_force_N'], 'peak_frame': p['frame']}
    assert worst < 1e-9, ('Inspector disagrees with the independent raw decode', worst)
    rest_residual = float(max(abs(v[0]).max() for v in scalars.values()))
    assert rest_residual < 1e-4, rest_residual
    recorded_peaks = state['recorded']['summary']['repaired_seam_peaks_N']
    assert set(rows) == set(recorded_peaks), (set(rows), set(recorded_peaks))
    drift = {name: abs(rows[name]['peak_N'] - recorded_peaks[name]) for name in rows}
    assert max(drift.values()) < .02 * max(recorded_peaks.values()), drift
    return {'saved_bake': arc_dir.name, 'seams': rows,
            'inspector_vs_decode_max_diff': worst,
            'rest_residual_frame0_N': rest_residual,
            'peak_drift_vs_repair_bake_N': drift}


def compare_trials():
    scene = state['scene']
    slots = lt._pair['slots']
    assert set(slots) == {'A', 'B'}, set(slots)
    for slot, entry in slots.items():
        assert Path(entry['directory']).is_dir(), (slot, entry['directory'])
    load = next(o for o in scene.objects if o.name.startswith('05'))
    load_id = load['uipc_object_id']
    result, _ = lt.compare(scene, .6, load_id)
    recorded = state['recorded']['summary']['B_minus_A_drop_m']
    assert abs(result['B_minus_A_drop_m'] - recorded) < 1e-9, (result['B_minus_A_drop_m'], recorded)
    return {'slots': {k: {'label': v['label'], 'content_id': v['content_id'][:16]}
                      for k, v in slots.items()},
            'seconds': result['seconds'], 'focus': result['focus_name'],
            'A_drop_m': result['trials']['A']['downward_drop_m'],
            'B_drop_m': result['trials']['B']['downward_drop_m'],
            'B_minus_A_drop_m': result['B_minus_A_drop_m'],
            'matches_workflow_record': True,
            'changed_inputs': result['changed_inputs']}


state = {}
if not hasattr(bpy.types.Scene, 'chimera_blocks'):
    chimera_studio.register()
bpy.context.preferences.use_preferences_save = False

check('Saved owned project reopens offline with no solver start', open_offline)
check('Exact geometry replay: evaluated cache samples match the workflow digests bit-for-bit', replay_digests)
check('Seam loads recompute offline: inspector matches independent raw decode and the repair-bake peaks', recompute_loads)
check('Layer Trial A/B pair survives save/reopen and compares with the same B-minus-A drop', compare_trials)

report['pass'] = all(c['pass'] for c in report['checks'])
report['summary'] = {
    'reopened_project': str(PROJECT),
    'labels': {'playback': 'Cached native mesh animation replay; not a new physical solve',
               'release_repair': 'AUTHORING-LEVEL seam disable/rebind; NOT force-triggered slip (I09 deferred)'},
}
EVIDENCE.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
chimera_studio.unregister()
if not report['pass']:
    raise RuntimeError('Cradle haul reopen acceptance failed; see evidence/cradle-haul/run-01/reopen-checks.json')
print('PASS all cradle haul reopen steps; evidence/cradle-haul/run-01/reopen-checks.json', flush=True)
