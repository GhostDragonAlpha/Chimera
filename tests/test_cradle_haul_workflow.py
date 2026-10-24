# SPDX-License-Identifier: AGPL-3.0-or-later
"""R2 acceptance: the owned rescue-cradle/haul construction through the documented
workshop loop. Open offline, inspect asymmetric SoftVertexStitch seam loads against
an independent raw MDD-cache decode and a finite difference of the published
stitch energy, RELEASE the loaded seam (authoring-level disable), re-bake, store
trial A, REPAIR by partial rebind over the rail top, re-bake, store trial B,
compare A/B at one exact sample time, attempt the optional physical checkpoint,
save, and keep every user project byte-identical.
Force estimates come from rounded saved positions and the native SoftVertexStitch
energy, not recorded solver forces. Release/repair are authoring-level seam
disable/rebind operations, NOT force-triggered slip (I09 deferred)."""
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
EVIDENCE = BASE / 'checks.json'
LAW = 'SoftVertexStitch-v1'
GUARD = ('GPU busy', 'already running', 'Wait for the current')

report = {
    'scope': 'Owned rescue-cradle haul construction (plan 13.0 R2, catalog I05-I09): '
             'inspect asymmetric seam loads with independent raw-cache decode and '
             'finite-difference of the published SoftVertexStitch energy; authoring-level '
             'release and partial over-the-rail repair; Layer Trial Comparison A/B at one '
             'exact sample time; optional physical checkpoint; save for offline reopen. '
             'Finite-gap stitches only: no fracture, delamination or force-triggered slip.',
    'project': str(PROJECT), 'checks': [], 'guard_refusals': [], 'optional': [],
}


def check(name, fn):
    try:
        details = fn()
        report['checks'].append({'name': name, 'pass': True, 'details': details})
        print('PASS', name, flush=True)
    except Exception as exc:
        report['checks'].append({'name': name, 'pass': False, 'error': str(exc),
                                 'traceback': traceback.format_exc()})
        print('FAIL', name, repr(exc), flush=True)


def optional(name, fn):
    try:
        details = fn()
        report['optional'].append({'name': name, 'pass': True, 'details': details})
        print('PASS (optional)', name, flush=True)
    except Exception as exc:
        report['optional'].append({'name': name, 'pass': False, 'error': str(exc),
                                   'traceback': traceback.format_exc()})
        print('FAIL (optional)', name, repr(exc), flush=True)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_hashes(directory):
    return {str(p.relative_to(directory)).replace('\\', '/'): sha(p)
            for p in sorted(directory.rglob('*')) if p.is_file()}


def guarded(fn, label):
    for attempt in (1, 2):
        try:
            return fn()
        except (RuntimeError, ValueError) as exc:
            if not any(t in str(exc) for t in GUARD) or attempt == 2:
                raise
            report['guard_refusals'].append({'label': label, 'attempt': attempt, 'text': str(exc)})
            time.sleep(2.)


def apply_op(action, params, purpose):
    def once():
        r = op.apply(op.propose(action, [], params, purpose)['id'])
        assert r['status'] == 'succeeded', (action, r)
        return r
    return guarded(once, action)


def submit_bake(purpose, timeout=900):
    def once():
        p = op.propose('bake_layers', [], {'timeout_seconds': timeout}, purpose)
        r = op.apply(p['id'])
        end = time.monotonic() + timeout + 60
        while r['status'] in ('queued', 'running') and time.monotonic() < end:
            time.sleep(.05)
            r = op.status(p['id'])
        if r['status'] != 'succeeded':
            raise RuntimeError('bake failed: %s; native: %s' % (r.get('error'),
                               (r.get('native_result') or {}).get('error')))
        return r
    # GPU contention from desktop apps can slow a bake far past its deadline while
    # the physics is unchanged; keep the failure in the receipt, then retry once.
    def retried():
        try:
            return once()
        except RuntimeError as exc:
            if 'deadline' not in str(exc).lower():
                raise
            report['guard_refusals'].append({'label': 'bake deadline retry', 'text': str(exc)})
            time.sleep(10.)
            return once()
    return guarded(retried, 'bake_layers')


def raw_points(arc):
    """Independent decode: raw MDD/npz bytes, not layer_trials' sampler."""
    points = {}
    settings = arc['request']['settings']
    outputs = {v['index']: v for v in arc['result']['objects']}
    for i, body in enumerate(arc['request']['objects']):
        with np.load(arc['directory'] / f'input_{i:04d}.npz') as a:
            local = a['vertices'].copy()
            matrix = a['matrix'].copy()
        if i in outputs:
            data = (arc['directory'] / f'object_{i:04d}.mdd').read_bytes()
            frames, n = struct.unpack('>ii', data[:8])
            v = np.frombuffer(data, dtype='>f4', offset=8 + frames * 4).astype(float).reshape(frames, n, 3)
            if outputs[i].get('encoding') == 'AFFINE':
                v = np.asarray([local @ x[1:] + x[0] for x in v])
        else:
            v = local[None, :, :]
            frames = 1
        if frames == 1:
            v = np.repeat(v, arc['result']['frames'], axis=0)
        points[body['id']] = (v @ matrix[:3, :3].T + matrix[:3, 3]) * settings['unit_scale']
    return points


def seam_decode(arc, points):
    """Independent all-frame stitch forces from raw decoded positions, plus a central
    finite difference of the published SoftVertexStitch energy
    E = sum 0.5*k*(|b-a|-rest)^2 (https://github.com/spiriMirror/libuipc .../soft_vertex_stitch.md)."""
    out = {}
    for seam in arc['request']['settings']['attachments']:
        pair = np.array(seam['pairs'])
        d = points[seam['b']][:, pair[:, 1]] - points[seam['a']][:, pair[:, 0]]
        length = np.sqrt(np.einsum('...i,...i->...', d, d))
        ext = length - np.array(seam['rest_lengths'])
        scalar = seam['stiffness'] * ext
        f = scalar[..., None] * d / length[..., None]

        def energy(pts_a, pts_b):
            dd = pts_b - pts_a
            ln = np.sqrt(np.einsum('...i,...i->...', dd, dd))
            return (0.5 * seam['stiffness'] * (ln - np.array(seam['rest_lengths'])) ** 2).sum()

        peak_frame, peak_stitch = np.unravel_index(np.argmax(abs(scalar)), scalar.shape)
        a_pk = points[seam['a']][peak_frame, pair[:, 0]]
        b_pk = points[seam['b']][peak_frame, pair[:, 1]]
        h = 1e-4
        fd = np.zeros_like(f[peak_frame])
        for stitch in range(pair.shape[0]):
            for axis in range(3):
                plus = a_pk.copy()
                minus = a_pk.copy()
                plus[stitch, axis] += h
                minus[stitch, axis] -= h
                fd[stitch, axis] = (energy(plus, b_pk) - energy(minus, b_pk)) / (2 * h)
        out[seam['id']] = {
            'ext': ext, 'scalar': scalar, 'f': f,
            'energy': .5 * seam['stiffness'] * ext ** 2,
            'net': np.linalg.norm(f.sum(axis=1), axis=1), 'sum': np.abs(scalar).sum(axis=1),
            'fd_peak_frame': int(peak_frame), 'fd_peak_stitch': int(peak_stitch),
            'fd_force_on_a': -fd[peak_stitch],
            'analytic_force_on_a': f[peak_frame, peak_stitch],
        }
    return out


def measure(arc, horizon):
    report_ui = loads.inspect(state['scene'], horizon, 1.0)
    assert report_ui['law_reference'].endswith('soft_vertex_stitch.md')
    points = raw_points(arc)
    decoded = seam_decode(arc, points)
    start = arc['request']['settings']['frame_start']
    rows = {}
    worst_decode = 0.
    for row in report_ui['seams']:
        p = row['peak']
        d = decoded[row['id']]
        assert math.isfinite(p['absolute_force_N']) and p['absolute_force_N'] > 0
        frame, stitch = np.unravel_index(np.argmax(abs(d['scalar'])), d['scalar'].shape)
        assert p['frame'] == frame + start and p['stitch'] == stitch, (row['name'], p['frame'], frame)
        worst_decode = max(worst_decode,
                           abs(p['signed_force_N'] - d['scalar'][frame, stitch]),
                           abs(p['extension_m'] - d['ext'][frame, stitch]) * 1e3,
                           float(np.max(np.abs(np.array(p['force_on_a_N']) - d['f'][frame, stitch]))))
        assert worst_decode < 1e-9, ('Inspector disagrees with the independent raw decode', worst_decode)
        fd_error = float(np.max(np.abs(d['fd_force_on_a'] - d['analytic_force_on_a'])))
        scale = max(0.01, .02 * float(np.abs(d['analytic_force_on_a']).max()))
        assert fd_error <= scale, ('Finite-difference of the published stitch energy disagrees', fd_error, scale)
        assert abs(row['maximum_energy_J'] - d['energy'].sum(axis=1).max()) < 1e-12
        assert abs(row['maximum_net_force_N'] - d['net'].max()) < 1e-10
        rows[row['name']] = {
            'peak_N': p['absolute_force_N'], 'peak_frame': p['frame'],
            'tension': p['signed_force_N'] >= 0,
            'fd_energy_force_error_N': fd_error,
            'net_N': row['maximum_net_force_N'],
        }
    rest_residual = float(max(np.abs(d['scalar'][0]).max() for d in decoded.values()))
    assert rest_residual < 1e-4, ('Authored rest gap is not force-free', rest_residual)
    load_z = None
    for body in arc['request']['objects']:
        if body['name'].startswith('05'):
            load_z = points[body['id']][:, :, 2].mean(axis=1)
    drop = float(load_z[0] - load_z[-1])
    return {'seams': rows, 'rest_residual_frame0_N': rest_residual,
            'independent_decode_max_diff': worst_decode,
            'load_drop_m': drop, 'samples': report_ui['sample_count'],
            'final_load_z_m': float(load_z[-1])}


if not hasattr(bpy.types.Scene, 'chimera_blocks'):
    chimera_studio.register()
bpy.context.preferences.use_preferences_save = False
state = {}

GUARD_BLENDS = {p: sha(p) for p in (ROOT.parent / 'Projects').rglob('*.blend')}
MEMBRANE = ROOT.parent / 'Projects/Membrane Workshop/Chimera Membrane Workshop.blend'
state['membrane_sha'] = sha(MEMBRANE) if MEMBRANE.is_file() else None


def open_project():
    state['blend_before'] = sha(PROJECT)
    t0 = time.perf_counter()
    assert bpy.ops.wm.open_mainfile(filepath=str(PROJECT)) == {'FINISHED'}
    bpy.context.view_layer.update()
    state['open_seconds'] = time.perf_counter() - t0
    scene = bpy.context.scene
    m = ed.module()
    assert not m.runtime.is_running(), 'Opening the project started native work'
    parts = {o['uipc_object_id']: o for o in scene.objects
             if hasattr(o, 'uipc_body') and o.uipc_body.role != 'NONE'}
    roles = sorted(o.uipc_body.role for o in parts.values())
    assert roles == ['CLOTH', 'FEM', 'FEM', 'RIGID', 'RIGID', 'STATIC'], roles
    atts = list(scene.uipc_settings.attachments)
    assert len(atts) == 2 and all(e.enabled for e in atts)
    cloth = next(o for o in parts.values() if o.uipc_body.role == 'CLOTH')
    spacings = []
    for e in atts:
        binding = json.loads(e.binding)
        assert binding['law'] == LAW
        pair = np.array(binding['pairs'], dtype=int)
        ys = np.sort(np.array([cloth.data.vertices[cloth_vi].co.y for rail_vi, cloth_vi in pair]))
        spacings.append({'name': e.name, 'pairs': len(binding['pairs']),
                         'stitch_y_positions_m': [round(float(y), 4) for y in ys],
                         'stitch_spacings_m': [round(float(d), 4) for d in np.diff(ys)],
                         'rest_gap_lengths_m': sorted(float(x) for x in binding['rest_lengths']),
                         'stiffness_N_per_m': e.stiffness})
    assert spacings[0]['pairs'] == 4 and spacings[1]['pairs'] == 2, spacings
    assert max(spacings[0]['stitch_spacings_m']) < min(spacings[1]['stitch_spacings_m']), spacings
    state['scene'] = scene
    with op.selected_targets(bpy.context, []):
        checked = m.bridge.check_cache(scene, verify_data=True)
    assert checked['frames'] == 61
    s = scene.uipc_settings
    bake_dir = Path(bpy.path.abspath(s.last_bake)).resolve()
    assert BASE / 'cache' in bake_dir.parents
    return {'open_seconds': round(state['open_seconds'], 2), 'roles': roles,
            'seams': spacings, 'cached_frames': checked['frames'],
            'spacing_asymmetry': {'left_4_stitches_max_gap_m': max(spacings[0]['stitch_spacings_m']),
                                  'right_2_stitches_min_gap_m': min(spacings[1]['stitch_spacings_m'])}}


check('Owned cradle opens offline with two unequal rails, sling, pad, load, ground and valid cache', open_project)


def inspect_attached():
    scene = state['scene']
    module, arc = lt.current(scene)
    assert len(arc['request']['settings']['attachments']) == 2
    q = arc['quality']['solver']
    assert q['nonconverged_steps'] == 0 and q['steps'] == 120, q
    measured = measure(arc, .6)
    names = list(measured['seams'])
    left, right = measured['seams'][names[0]], measured['seams'][names[1]]
    assert abs(left['peak_N'] - right['peak_N']) > .1 * max(left['peak_N'], right['peak_N']), \
        ('Left and right seam peaks do not differ materially', left['peak_N'], right['peak_N'])
    state['attached_arc'] = arc
    state['attached'] = measured
    state['load_id'] = next(b['id'] for b in arc['request']['objects'] if b['name'].startswith('05'))
    return {**measured, 'asymmetry_delta_N': abs(left['peak_N'] - right['peak_N'])}


check('Attached bake: seam peaks differ (asymmetry) and match the independent decode + energy finite difference', inspect_attached)


def release_and_bake():
    r = apply_op('set_layer_attachment', {'attachment': 0, 'values': {'enabled': False}},
                 'RELEASE: disable the loaded left seam (authoring-level seam disable, not slip)')
    state['release_applied'] = r
    t0 = time.perf_counter()
    submit_bake('Re-bake with the left seam released so the counterfactual drop comes from fresh native samples')
    wall = time.perf_counter() - t0
    scene = state['scene']
    module, arc = lt.current(scene)
    assert len(arc['request']['settings']['attachments']) == 1, 'Released seam still bound'
    q = arc['quality']['solver']
    assert q['nonconverged_steps'] == 0 and q['steps'] == 120, q
    measured = measure(arc, .6)
    drop = measured['load_drop_m']
    attached_drop = state['attached']['load_drop_m']
    assert drop - attached_drop > .3, ('Released load did not drop materially farther', drop, attached_drop)
    state['released_arc'] = arc
    state['released'] = measured
    return {'wall_seconds': round(wall, 2), 'native_seconds': round(arc['result']['performance']['total_seconds'], 2),
            'seams': list(measured['seams']), 'released_drop_m': drop,
            'attached_drop_m': attached_drop, 'drop_delta_m': drop - attached_drop}


check('RELEASE through the shared operation: re-bake shows the load dropping materially farther', release_and_bake)


def capture_a():
    assert bpy.ops.chimera.capture_layer_trial(slot='A', label='Released left seam',
                                               purpose='Counterfactual: haul load with the loaded left seam disabled') == {'FINISHED'}
    assert set(lt._pair['slots']) >= {'A'}
    return {'slot': 'A', 'label': lt._pair['slots']['A']['label'],
            'content_id': lt._pair['slots']['A']['content_id']}


check('Store released bake as Layer Trial A through the panel operator', capture_a)


def repair_and_bake():
    r = apply_op('set_layer_attachment',
                 {'attachment': 0, 'values': {'enabled': True, 'group_a': 'Left seam A top outer',
                                              'group_b': 'Left edge B outer', 'max_gap': 0.15}},
                 'REPAIR: partial rebind of the strap over the rail top (authoring-level field repair)')
    state['repair_applied'] = r
    r = apply_op('rebind_layer_attachment', {'attachment': 0}, 'Rebind the repaired seam through the authoring owner')
    scene = state['scene']
    entry = scene.uipc_settings.attachments[0]
    binding = json.loads(entry.binding)
    assert len(binding['pairs']) == 2, binding['pairs']
    rest = [float(x) for x in binding['rest_lengths']]
    assert all(.08 <= x <= .11 for x in rest), ('Repaired rest gaps are not over the rail top', rest)
    t0 = time.perf_counter()
    submit_bake('Re-bake with the partially repaired seam so the repair comparison uses fresh native samples')
    wall = time.perf_counter() - t0
    module, arc = lt.current(scene)
    seams = arc['request']['settings']['attachments']
    assert len(seams) == 2, seams
    q = arc['quality']['solver']
    assert q['nonconverged_steps'] == 0 and q['steps'] == 120, q
    measured = measure(arc, .6)
    drop = measured['load_drop_m']
    attached_drop = state['attached']['load_drop_m']
    released_drop = state['released']['load_drop_m']
    assert abs(drop - attached_drop) > .05, ('Repaired drop is not materially different from attached', drop, attached_drop)
    assert released_drop - drop > .3, ('Repair did not recover the load materially versus release', drop, released_drop)
    state['repaired_arc'] = arc
    state['repaired'] = measured
    return {'wall_seconds': round(wall, 2), 'native_seconds': round(arc['result']['performance']['total_seconds'], 2),
            'repaired_rest_gaps_m': [round(x, 4) for x in rest],
            'seams': list(measured['seams']), 'repaired_drop_m': drop,
            'attached_drop_m': attached_drop, 'released_drop_m': released_drop}


check('REPAIR by partial over-the-rail rebind: re-bake holds the load with a materially different drop', repair_and_bake)


def capture_b_and_compare():
    assert bpy.ops.chimera.capture_layer_trial(slot='B', label='Repaired: partial over-rail rebind',
                                               purpose='Repair comparison: the load path restored through fewer, higher stitches') == {'FINISHED'}
    scene = state['scene']
    scene.chimera_layer_trials.seconds = .6
    scene.chimera_layer_trials.focus_object = next(o for o in scene.objects
                                                   if o.get('uipc_object_id') == state['load_id'])
    assert bpy.ops.chimera.compare_layer_trials(seconds=.6) == {'FINISHED'}
    result = lt._pair['result']
    drop_a = result['trials']['A']['downward_drop_m']
    drop_b = result['trials']['B']['downward_drop_m']
    assert abs(drop_b - drop_a) > .3, ('A/B drops are not materially different at the common sample', drop_a, drop_b)
    assert any('settings' in c or 'attachments' in c for c in result['changed_inputs']), result['changed_inputs']
    state['comparison'] = result
    return {'seconds': result['seconds'], 'A_drop_m': drop_a, 'B_drop_m': drop_b,
            'B_minus_A_drop_m': result['B_minus_A_drop_m'],
            'changed_inputs': result['changed_inputs'],
            'attached_reference_drop_m': state['attached']['load_drop_m']}


check('Layer Trial Comparison at one exact sample time: repaired vs released drops differ materially', capture_b_and_compare)


def physical_checkpoint():
    scene = state['scene']

    def run(action, params, purpose):
        p = op.propose(action, [], params, purpose)
        r = op.apply(p['id'])
        end = time.monotonic() + 400
        while r['status'] in ('queued', 'running') and time.monotonic() < end:
            time.sleep(.02)
            r = op.status(p['id'])
        assert r['status'] == 'succeeded', r
        return r

    guarded(lambda: run('bake_layers_checkpoint', {'timeout_seconds': 900},
                        'Optional: record a native physical checkpoint of the repaired cradle'),
            'bake_layers_checkpoint')
    from chimera_studio import layer_checkpoint as lcp
    assert scene.get(lcp.KEY), 'No checkpoint reference recorded'
    record = json.loads(scene[lcp.KEY])
    guarded(lambda: run('continue_layers', {'end_frame': 65, 'timeout_seconds': 900},
                        'Optional: continue the saved native physics five frames'),
            'continue_layers')
    assert scene.frame_end == 65, scene.frame_end
    return {'checkpoint_sha256': record['sha256'][:16],
            'native_step': record['step'],
            'continued_to_frame': scene.frame_end}


optional('Physical checkpoint and five-frame native continuation of the repaired cradle', physical_checkpoint)


def save_and_digest():
    scene = state['scene']
    samples = (1, 31, 61)
    hashes = {o.name: {str(f): hashlib.sha256(evaluated(o, scene, f).astype('<f4').tobytes()).hexdigest()
                       for f in samples} for o in scene.objects
              if hasattr(o, 'uipc_body') and o.uipc_body.role not in ('NONE', 'STATIC')}

    def relativize(obj):
        for mod in obj.modifiers:
            if mod.type == 'MESH_CACHE' and mod.filepath:
                path = Path(bpy.path.abspath(mod.filepath)).resolve()
                if BASE in path.parents:
                    mod.filepath = '//' + path.relative_to(BASE).as_posix()

    for obj in scene.objects:
        relativize(obj)
    for pobj in bpy.data.objects:
        if pobj.get('uipc_affine_cache') == 1:
            relativize(pobj)
    s = scene.uipc_settings
    directory = Path(bpy.path.abspath(s.last_bake)).resolve()
    assert BASE in directory.parents, directory
    s.last_bake = '//' + directory.relative_to(BASE).as_posix()
    s.cache_directory = '//cache'
    assert bpy.ops.wm.save_mainfile() == {'FINISHED'}
    state['digests'] = hashes
    state['cache_after'] = tree_hashes(BASE / 'cache')
    untouched = {p: sha(p) for p in (ROOT.parent / 'Projects').rglob('*.blend')} == GUARD_BLENDS
    assert untouched, 'A user project changed!'
    membrane_ok = state['membrane_sha'] is None or sha(MEMBRANE) == state['membrane_sha']
    assert membrane_ok, 'Membrane Workshop project changed!'
    return {'saved': True, 'digest_samples': sum(len(v) for v in hashes.values()),
            'user_projects_byte_identical': True, 'membrane_project_unchanged': True,
            'cache_files': len(state['cache_after'])}


check('Save the owned cradle with its caches; user projects stay byte-identical', save_and_digest)

report['summary'] = {
    'attached_drop_m': state['attached']['load_drop_m'],
    'released_drop_m': state['released']['load_drop_m'],
    'repaired_drop_m': state['repaired']['load_drop_m'],
    'comparison_time_s': .6,
    'attached_seam_peaks_N': {k: v['peak_N'] for k, v in state['attached']['seams'].items()},
    'released_seam_peaks_N': {k: v['peak_N'] for k, v in state['released']['seams'].items()},
    'repaired_seam_peaks_N': {k: v['peak_N'] for k, v in state['repaired']['seams'].items()},
    'rest_residual_frame0_N': state['attached']['rest_residual_frame0_N'],
    'B_minus_A_drop_m': state['comparison']['B_minus_A_drop_m'],
    'labels': {
        'release_repair': 'AUTHORING-LEVEL seam disable / partial rebind; NOT force-triggered slip (I09 deferred)',
        'rope': 'I06 cloth sling surrogate (specified-only)',
        'pad': 'I07 illustrative FEM silicone, measured material missing',
        'ground': 'I08 authored static surrogate',
    },
}
report['pass'] = all(c['pass'] for c in report['checks'])
report['geometry_digests'] = state['digests']
EVIDENCE.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
chimera_studio.unregister()
if not report['pass']:
    raise RuntimeError('Cradle haul workflow acceptance failed; see evidence/cradle-haul/run-01/checks.json')
print('PASS all cradle haul workflow steps; evidence/cradle-haul/run-01/checks.json', flush=True)
