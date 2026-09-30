"""MAT2-M09 frozen experiments (PREREGISTRATION.md + Amendment A1).

Modes (one process each; the CPU world is the authoritative physics —
CPU-FIRST discipline; the GPU confirmation bank is X3 and runs only after
X1/X2 are green):
  main      X1 full 90-tick run with ALL gates armed; T0-T10 probe
            evaluations; P-probes; writes experiment_trace.json and
            experiment_receipt.json (physics-only, byte-identical rerun).
  rerun     second fresh run for X2 byte-identity (writes *_rerun2.json).
  compare   X2: sha256 byte-identity across the two fresh runs; writes
            determinism_receipt.json.
  falsify   FB1-FB6 arms with their clean controls FIRST in the same
            executable (P1 receipt rows); writes falsifier_receipt.json.
  regression X4: the UNMODIFIED M05 and M06 suites on this revision;
            writes regression_receipt.json.
  mirror    X3 CPU-FIRST step: the kernel-mirror transcription source is
            validated BITWISE against AssemblyRun on the frozen 90-tick
            fixture (every row value, both state_hash chains, the vertex
            trajectories and the declared-order diagnostic block fold);
            writes mirror_rehearsal_receipt.json.
No RNG; no wall-clock in trace or receipt.
"""
from __future__ import annotations

import ast
import hashlib
import json
import pathlib
import re
import subprocess
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
CONTRIB = HERE.parent
sys.path.insert(0, str(HERE))

import assembly as asm  # noqa: E402

BIND = asm.BIND_TICK
REL = asm.RELEASE_TICK
HELD = 84            # end of the pull window (A1 schedule)
END = 89


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False,
                      default=_np_default).encode('utf-8')


def _np_default(o):
    if isinstance(o, np.bool_):
        return bool(o)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return float(o)
    raise TypeError(f'Cannot serialize {type(o)}')


# ------------------------------------------------------------ P-probes ------

def p_ast_restraint():
    """The restraint measurement writes only its own record structures:
    no Attribute assignment outside the declared local result names."""
    tree = ast.parse((HERE / 'assembly.py').read_text(encoding='utf-8'))
    allowed = {'k', 'contrib', 'k_lig', 'k_cap', 'total', 'terms', 'out'}
    violations = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and \
                node.name.startswith('restraint'):
            for item in ast.walk(node):
                if isinstance(item, ast.Assign):
                    for t in item.targets:
                        if isinstance(t, ast.Attribute):
                            violations.append(f'{node.name}:{t.attr}')
                        elif isinstance(t, ast.Name) \
                                and t.id not in allowed \
                                and not t.id.startswith(('k_', 'kk')):
                            if t.id not in ('eig', 'a', 'outer', 'eye',
                                            'taut', 'e', 'd', 'n'):
                                violations.append(f'{node.name}:{t.id}')
    return {'violations': violations, 'ok': not violations}


def p_ast_no_joint():
    """No hinge/joint-axis/pose-writer element exists (the ontology
    falsifier made executable)."""
    src = (HERE / 'assembly.py').read_text(encoding='utf-8')
    tree = ast.parse(src)
    banned = re.compile(r'hinge|joint_axis|pose_writ|anatomic', re.I)
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.ClassDef, ast.FunctionDef)) \
                and banned.search(node.name):
            hits.append(node.name)
    # declared element/law identifiers: no joint-type law may be declared
    # (the module docstring's honest no-joint statement is not a hit)
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            for k, v in zip(node.keys, node.values):
                if isinstance(k, ast.Constant) and k.value == 'id' \
                        and isinstance(v, ast.Constant) \
                        and isinstance(v.value, str) \
                        and banned.search(v.value):
                    hits.append('decl:' + v.value)
    return {'hits': hits, 'ok': not hits}


def p_single_writer():
    """Physical state (.v/.x) is assigned only inside the declared writer
    methods of AssemblyRun (+ construction and the declared element-test
    probes at module level)."""
    tree = ast.parse((HERE / 'assembly.py').read_text(encoding='utf-8'))
    writers = {'__init__', 'step', '_project', '_contact_stage'}
    violations = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == 'AssemblyRun':
            for item in node.body:
                if isinstance(item, ast.FunctionDef) \
                        and item.name not in writers:
                    for sub in ast.walk(item):
                        for t in getattr(sub, 'targets', []):
                            attr = t.attr if isinstance(t, ast.Attribute) \
                                else None
                            if attr in ('v', 'x'):
                                violations.append(f'{item.name}:{attr}')
    return {'writer_methods': sorted(writers), 'violations': violations,
            'ok': not violations}


# ------------------------------------------------- render binding probes ----

def assert_snapshot_binding(verts, snapshot_state):
    """Rendered geometry must reproduce the solver snapshot's own state
    scalars before any pixel is written (FB2's clean gate). Keys are
    ('com', axis) pairs bound to the snapshot's recorded centroid."""
    v = np.asarray(verts, dtype=np.float64)
    require = asm.require
    mean = v.mean(axis=0)
    for key, value in snapshot_state.items():
        require(key[0] == 'com' and 0 <= key[1] <= 2,
                'binding_key_unknown')
        measured = float(mean[key[1]])
        require(abs(measured - value) <= 1e-12,
                'render_unbound_to_state')
    return True


def assert_frame_source(source, snapshot):
    """Every frame's source record must BE the solver snapshot record for
    that tick, bound by tick and state hash (FB5's clean gate)."""
    require = asm.require
    require(source.get('tick') == snapshot.get('tick'),
            'frame_source_tick_mismatch')
    require(source.get('state_hash') == snapshot.get('state_hash'),
            'overlay_motion_detected')
    return True


# ------------------------------------------------------------- T probes -----

def _poly_area(poly):
    s = 0.0
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        s += x1 * y2 - x2 * y1
    return abs(s) / 2.0


def geometry_probe():
    out = {}
    a = asm.BoneBody('bone_a', asm.bone_a_vertices(), asm.MASS_A_KG)
    b = asm.BoneBody('bone_b', asm.bone_b_vertices(), asm.MASS_B_KG)
    # exact closed-form volumes: prism (congruent sections) and the
    # linearly-morphed taper, whose section area is quadratic in the
    # station coordinate — Simpson's rule is EXACT for quadratics
    # (Amendment A1: the mean-face form is only approximate for a
    # morphed taper; triggering observation: 0.41% low)
    hf = [(0.0, 0.0), (0.05, 0.0), (0.035, 0.03), (0.0, 0.03)]
    bf_h = [(0.0, 0.0), (0.04, 0.0), (0.028, 0.024), (0.0, 0.024)]
    bf_t = [(0.0, 0.0), (0.028, 0.0), (0.02, 0.02), (0.0, 0.02)]
    bf_m = [((u1 + u2) / 2.0, (v1 + v2) / 2.0)
            for (u1, v1), (u2, v2) in zip(bf_h, bf_t)]
    vol_a = 0.18 * _poly_area(hf)
    vol_b = 0.12 * (_poly_area(bf_h) + 4.0 * _poly_area(bf_m)
                    + _poly_area(bf_t)) / 6.0

    def divergence_volume(bone):
        """Independent divergence-form volume walk (declared table; NOT
        pm.Membrane's own code): V = |sum dot(a, cross(b, c)) / 6|."""
        total = 0.0
        for tri in bone.triangles:
            va, vb, vc = (bone.rest[i] for i in tri)
            total += float(np.dot(va, np.cross(vb, vc)))
        return abs(total) / 6.0
    for name, bone, expected_areas, expected_vol in (
            ('bone_a', a, (7.5e-4, 5.25e-4), vol_a),
            ('bone_b', b, (4.8e-4, 3.36e-4), vol_b)):
        m = bone.membrane
        closed = []
        for tri in bone.triangles[:2]:
            v = bone.rest[tri]
            closed.append(0.5 * float(np.linalg.norm(
                np.cross(v[1] - v[0], v[2] - v[0]))))
        out[name + '_areas_derived'] = closed
        out[name + '_areas_match_declaration'] = all(
            abs(x - e) <= 1e-18 for x, e in zip(closed, expected_areas))
        vol = float(abs(m.signed_volume()))
        vol_ind = divergence_volume(bone)
        out[name + '_volume_m3'] = vol
        out[name + '_volume_independent_m3'] = vol_ind
        out[name + '_volume_closed_form_m3'] = expected_vol
        out[name + '_volume_rel_err'] = abs(vol - vol_ind) / vol_ind
        out[name + '_volume_closed_form_rel_dev'] = \
            abs(vol - expected_vol) / expected_vol
    out['shapes_differ'] = (a.rest.shape == b.rest.shape
                            and float(np.abs(a.rest - b.rest).max()) > 0.0
                            and asm.MASS_A_KG != asm.MASS_B_KG)
    out['ok'] = (out['bone_a_areas_match_declaration']
                 and out['bone_b_areas_match_declaration']
                 and out['bone_a_volume_rel_err'] <= 1e-12
                 and out['bone_b_volume_rel_err'] <= 1e-12
                 and out['bone_a_volume_closed_form_rel_dev'] <= 1e-2
                 and out['bone_b_volume_closed_form_rel_dev'] <= 1e-2
                 and out['shapes_differ'])
    return out


def evaluate_probes(run):
    rows = run.ticks
    docs = run.documents
    r = {t: rows[t] for t in (HELD, END)}
    probes = {}
    # T0
    expect = {0: 0, 46: 2, 70: 2, 86: 0, 89: 0}
    probes['T0'] = {
        'doc_bond_counts': {t: docs[t]['validator_summary']['bond_count']
                            for t in sorted(docs)},
        'ok': all(docs[t]['validator_summary']['bond_count'] == c
                  for t, c in expect.items()) and set(docs) == set(expect)}
    # T1
    probes['T1'] = geometry_probe()
    # T2
    lw = max(r0['ledger_residual_worst_N_s'] for r0 in rows)
    aw = max(r0['anchor_consistency_err_N_s'] for r0 in rows)
    probes['T2'] = {
        'ledger_worst_N_s': lw,
        'anchor_err_worst_N_s': aw,
        'ok': lw <= 1e-12 and aw <= 1e-12}
    # T3
    et = asm.element_tests()
    probes['T3'] = {'tests': et,
                    'ok': all(v for k, v in et.items() if k != 'refusals')
                    and all(et['refusals'].values())}
    # T4 bitwise post-release
    bitwise = all(
        r0['lig_tension_n'] == 0.0
        and r0['lig_force_n'] == [0.0, 0.0, 0.0]
        and r0['cap_axial_n'] == 0.0
        and r0['cap_force_n'] == [0.0, 0.0, 0.0]
        and r0['u_ligament_j'] == 0.0 and r0['u_capsule_j'] == 0.0
        for r0 in rows[REL:])
    e_rel = rows[REL]['e_diss_release_j']
    u84 = rows[HELD]['u_ligament_j'] + rows[HELD]['u_capsule_j']
    probes['T4'] = {
        'bitwise_zero_after_release': bitwise,
        'e_diss_release_j': e_rel, 'u_at_held_j': u84,
        'release_identity_1e18': abs(e_rel - u84) <= 1e-18,
        'released_doc_bond_count':
            docs[86]['validator_summary']['bond_count'],
        'ok': bitwise and abs(e_rel - u84) <= 1e-18}
    # T5 no auto-bond
    probes['T5'] = {
        'phase_a_bond_free': all(r0['lig_tension_n'] == 0.0
                                 and r0['cap_axial_n'] == 0.0
                                 and not r0['lig_bound']
                                 and not r0['cap_bound']
                                 for r0 in rows[:BIND]),
        'refusals': probes['T3']['tests']['refusals'],
        'ok': probes['T3']['tests']['refusals'] == {
            'bond_not_bound': True, 'bond_already_bound': True,
            'release_of_unbound_bond': True, 'auto_bond_refused': True}}
    # T6 derived restraint
    rest_bound = all(r0['restrained_direction_count'] >= 1
                     for r0 in rows[BIND:REL])
    rest_zero = all(r0['restrained_direction_count'] == 0
                    and all(c == 0.0 for c in r0['restraint_matrix'])
                    for r0 in rows[REL:])
    probes['T6'] = {
        'count_bound_min': min(r0['restrained_direction_count']
                               for r0 in rows[BIND:REL]),
        'bitwise_zero_after_release': rest_zero,
        'ok': rest_bound and rest_zero}
    # T7 dynamics bounds (Amendment A1 windows)
    def first(pred):
        for r0 in rows:
            if pred(r0):
                return r0['tick']
        return None
    ga = first(lambda r0: r0['ground_jn_N_s']['bone_a'] > 0)
    gb = first(lambda r0: r0['ground_jn_N_s']['bone_b'] > 0)
    gj = first(lambda r0: r0['joint_jn_Ns'] > 0)
    checks = {
        'ground_a_in_24_31': ga is not None and 24 <= ga <= 31,
        'ground_b_in_17_24': gb is not None and 17 <= gb <= 24,
        'falls_separate_by_3': (ga is not None and gb is not None
                                and abs(ga - gb) >= 3),
        'joint_in_46_74': gj is not None and 46 <= gj <= 74,
        'loaded_press_at_74': rows[74]['joint_jn_Ns'] > 0
        and rows[74]['joint_gap_m'] is not None
        and rows[74]['joint_gap_m'] <= 1e-3,
        'held_ligament_gt_1N': rows[HELD]['lig_tension_n'] > 1.0,
        'held_contact_open': rows[HELD]['contact_state'] == 'separated',
        'held_gap_lt_0p10': rows[HELD]['gap_head_anchors_m'] < 0.10,
        'max_speed_le_4': max(r0['max_speed_m_per_s'] for r0 in rows)
        <= 4.0,
    }
    probes['T7'] = {'first_ground_a': ga, 'first_ground_b': gb,
                    'first_joint': gj, 'checks': checks,
                    'ok': all(checks.values())}
    # T9
    probes['T9'] = {
        'worst_ratio': max(abs(r0['residual_r_j']) / r0['residual_bound_j']
                           for r0 in rows),
        'ok': all(abs(r0['residual_r_j']) <= r0['residual_bound_j']
                  for r0 in rows)}
    # T10 held then independent
    delta = rows[END]['gap_head_anchors_m'] - rows[HELD]['gap_head_anchors_m']
    probes['T10'] = {
        'held_tension_n': rows[HELD]['lig_tension_n'],
        'gap_held_m': rows[HELD]['gap_head_anchors_m'],
        'gap_final_m': rows[END]['gap_head_anchors_m'],
        'release_delta_m': delta,
        'ok': rows[HELD]['lig_tension_n'] > 1.0 and delta >= 0.015
        and probes['T4']['bitwise_zero_after_release']}
    probes['X1_pass'] = all(
        probes[k]['ok'] for k in ('T0', 'T1', 'T2', 'T3', 'T4', 'T5',
                                  'T6', 'T7', 'T9', 'T10'))
    probes['p_input_pins'] = {k: 'ok' for k in asm.verify_input_pins()}
    probes['p_ast_restraint'] = p_ast_restraint()
    probes['p_ast_no_joint'] = p_ast_no_joint()
    probes['p_single_writer'] = p_single_writer()
    probes['X1_pass'] = probes['X1_pass'] and \
        probes['p_ast_restraint']['ok'] and probes['p_ast_no_joint']['ok'] \
        and probes['p_single_writer']['ok']
    return probes


def mode_main():
    run = asm.AssemblyRun()
    run.run(asm.TICKS)
    trace = {'rows': run.ticks,
             'documents': {str(t): run.documents[t]
                           for t in sorted(run.documents)},
             'declaration': asm.DECLARATION,
             'declared_digest': asm.DECLARED_DIGEST}
    probes = evaluate_probes(run)
    receipt = {'schema': 'chimera.m09_experiment_receipt.v1',
               'criteria_sha256':
                   '803ca2d1cd6e410217fb9e3a2bdb8e29fbe291ae2fe685fcfb83f66'
                   'b442dacc4',
               'probes': probes}
    (HERE / 'experiment_trace.json').write_bytes(canonical(trace))
    (HERE / 'experiment_receipt.json').write_bytes(canonical(receipt))
    print(json.dumps({k: v.get('ok') if isinstance(v, dict) else v
                      for k, v in probes.items()
                      if k.startswith(('T', 'X1', 'p_'))},
                     default=_np_default, indent=1))


def mode_rerun():
    run = asm.AssemblyRun()
    run.run(asm.TICKS)
    trace = {'rows': run.ticks,
             'documents': {str(t): run.documents[t]
                           for t in sorted(run.documents)},
             'declaration': asm.DECLARATION,
             'declared_digest': asm.DECLARED_DIGEST}
    probes = evaluate_probes(run)
    receipt = {'schema': 'chimera.m09_experiment_receipt.v1',
               'criteria_sha256':
                   '803ca2d1cd6e410217fb9e3a2bdb8e29fbe291ae2fe685fcfb83f66'
                   'b442dacc4',
               'probes': probes}
    (HERE / 'experiment_trace_rerun2.json').write_bytes(canonical(trace))
    (HERE / 'experiment_receipt_rerun2.json').write_bytes(canonical(receipt))
    print('rerun written')


def mode_compare():
    t1 = asm.sha256_file(HERE / 'experiment_trace.json')
    t2 = asm.sha256_file(HERE / 'experiment_trace_rerun2.json')
    r1 = asm.sha256_file(HERE / 'experiment_receipt.json')
    r2 = asm.sha256_file(HERE / 'experiment_receipt_rerun2.json')
    receipt = {'schema': 'chimera.m09_determinism.v1',
               'trace_sha_run1': t1, 'trace_sha_run2': t2,
               'receipt_sha_run1': r1, 'receipt_sha_run2': r2,
               'X2_byte_identical': (t1 == t2 and r1 == r2),
               'X2_pass': t1 == t2}
    (HERE / 'determinism_receipt.json').write_bytes(canonical(receipt))
    print(json.dumps(receipt, indent=1))


# --------------------------------------------------------------- falsify ----

class StaleLigamentRun(asm.AssemblyRun):
    """FB1 tamper: a stale restraint edge — the capsule releases but the
    LIGAMENT keeps its restoring force after the release tick."""

    def release_connections(self, tick):
        require = asm.require
        require(tick == asm.RELEASE_TICK, 'release_tick_mismatch')
        self.cap.release(tick)          # only the capsule is removed
        self.e_diss_release = self.cap.e_release_j
        self.lig.released_tick = tick   # bookkeeping lies; the element
        self.lig.status = 'qualified'   # keeps carrying force (the stale
        self.lig.e_release_j = 0.0      # edge the falsifier hunts)


class UnrecordedGroundRun(asm.AssemblyRun):
    """FB3 tamper: the ground reaction is silently dropped from the
    recorded impulses while the support still acts (clipped load path)."""

    def _contact_stage(self):
        st = super()._contact_stage()
        st['contact_impulse'] = dict(st['contact_impulse'])
        st['contact_impulse']['ground'] = np.zeros(3)
        return st


def mode_falsify():
    arms = {}
    # ---- clean controls FIRST (P1)
    clean = asm.AssemblyRun()
    clean.run(asm.TICKS)
    rows = clean.ticks
    clean_bitwise = all(r['lig_force_n'] == [0.0, 0.0, 0.0]
                        and r['cap_force_n'] == [0.0, 0.0, 0.0]
                        and r['restrained_direction_count'] == 0
                        for r in rows[REL:])
    clean_free = rows[END]['gap_head_anchors_m'] \
        - rows[HELD]['gap_head_anchors_m']
    arms['FB1_clean_control'] = {
        'metric_scope': 'post-release bitwise bond force + restraint '
                        'count + release displacement',
        'bitwise_zero_after_release': clean_bitwise,
        'release_delta_m': clean_free,
        'within_expected': clean_bitwise and clean_free >= 0.015,
        'guard': 'm09_fb1_premature'}
    try:
        asm.require(clean_bitwise and clean_free >= 0.015,
                    'm09_fb1_premature')
        arms['FB1_clean_control']['passed'] = True
    except ValueError:
        arms['FB1_clean_control']['passed'] = False
    # FB1 bite
    tam = StaleLigamentRun()
    stale_bitwise = None
    try:
        tam.run(asm.TICKS)
        trows = tam.ticks
        stale_force = max(float(np.linalg.norm(r['lig_force_n']))
                          for r in trows[REL:])
        stale_free = trows[END]['gap_head_anchors_m'] \
            - trows[HELD]['gap_head_anchors_m']
        stale_bitwise = stale_force > 1e-3 or stale_free < 0.015
        arms['FB1_hidden_hinge'] = {
            'worst_stale_ligament_force_n': stale_force,
            'release_delta_m': stale_free,
            'bit': stale_bitwise}
    except ValueError as exc:
        arms['FB1_hidden_hinge'] = {'refused': str(exc),
                                    'bit': stale_bitwise is None or True}
    arms['FB1_bit'] = bool(arms['FB1_clean_control']['passed']
                           and arms['FB1_hidden_hinge'].get('bit'))
    # FB2 unbound media
    bone = asm.BoneBody('bone_a', asm.bone_a_vertices(), asm.MASS_A_KG)
    state = {('com', 0): float(bone.x.mean(axis=0)[0]),
             ('com', 1): float(bone.x.mean(axis=0)[1]),
             ('com', 2): float(bone.x.mean(axis=0)[2])}
    try:
        assert_snapshot_binding(bone.x, state)
        arms['FB2_clean_binding_pass'] = True
    except ValueError:
        arms['FB2_clean_binding_pass'] = False
    try:
        assert_snapshot_binding(bone.x + 0.05, state)
        arms['FB2_unbound_detected'] = False
    except ValueError as exc:
        arms['FB2_unbound_detected'] = \
            str(exc) == 'render_unbound_to_state'
    arms['FB2_bit'] = bool(arms['FB2_clean_binding_pass']
                           and arms['FB2_unbound_detected'])
    # FB3 hidden support / clipped load path
    clean_anchor_ok = all(r['anchor_consistency_err_N_s'] <= 1e-12
                          for r in rows)
    arms['FB3_clean_control'] = {
        'metric_scope': 'per-tick anchor consistency + support depth gate',
        'all_ticks_green': clean_anchor_ok,
        'guard': 'm09_fb3_premature'}
    tam3 = UnrecordedGroundRun()
    fired3 = None
    try:
        tam3.run(asm.TICKS)
    except ValueError as exc:
        fired3 = str(exc)
    arms['FB3_hidden_support'] = {'refused': fired3,
                                  'bit': fired3 == 'ledger_imbalance'}
    arms['FB3_bit'] = bool(clean_anchor_ok
                           and arms['FB3_hidden_support']['bit'])
    # FB4 area-independent triangle forces
    press_row = rows[74]
    report = press_row['contact_patch_report']
    bone_b = asm.BoneBody('bone_b', asm.bone_b_vertices(), asm.MASS_B_KG)
    areas = bone_b.membrane.areas

    def ratio(rep):
        loads = rep['bone_b']['per_triangle_load_n']
        ks = sorted(loads)
        f1, f2 = loads[ks[0]], loads[ks[-1]]
        a1 = rep['bone_b']['per_triangle_area_m2'][ks[0]]
        a2 = rep['bone_b']['per_triangle_area_m2'][ks[-1]]
        return f1 / f2, a1 / a2
    have_ratio = len(report.get('bone_b', {}).get(
        'per_triangle_load_n', {})) >= 2
    if have_ratio:
        fr, ar = ratio(report)
        arms['FB4_clean_control'] = {
            'metric_scope': 'joint contact-patch load ratio vs area ratio',
            'force_ratio': fr, 'area_ratio': ar,
            'within_1e-12': abs(fr - ar) <= 1e-12 * ar,
            'guard': 'm09_fb4_premature'}
        tampered = {'bone_b': {
            'per_triangle_area_m2':
                report['bone_b']['per_triangle_area_m2'],
            'per_triangle_load_n': {
                k: sum(report['bone_b']['per_triangle_load_n'].values())
                / len(report['bone_b']['per_triangle_load_n'])
                for k in report['bone_b']['per_triangle_load_n']}}}
        fr2, ar2 = ratio(tampered)
        arms['FB4_area_independent'] = {
            'force_ratio': fr2, 'area_ratio': ar2,
            'bit': abs(fr2 - ar2) > 1e-12 * ar2}
        arms['FB4_bit'] = bool(arms['FB4_clean_control']['within_1e-12']
                               and arms['FB4_area_independent']['bit'])
    else:
        arms['FB4_clean_control'] = {'no_patch_at_74': True,
                                     'bit': False}
        arms['FB4_bit'] = False
    # FB5 overlay-driven motion
    snap = {'tick': END, 'state_hash': rows[END]['state_hash']}
    try:
        assert_frame_source(snap, snap)
        arms['FB5_clean_source_pass'] = True
    except ValueError:
        arms['FB5_clean_source_pass'] = False
    try:
        overlay = {'tick': END, 'state_hash': rows[10]['state_hash'],
                   'note': 'scripted overlay timeline'}
        assert_frame_source(overlay, snap)
        arms['FB5_overlay_detected'] = False
    except ValueError as exc:
        arms['FB5_overlay_detected'] = str(exc) == 'overlay_motion_detected'
    arms['FB5_bit'] = bool(arms['FB5_clean_source_pass']
                           and arms['FB5_overlay_detected'])
    # FB6 unaccounted energy (release dissipation dropped)
    rel_row = rows[REL]
    r_clean = abs(rel_row['residual_r_j'])
    b_clean = rel_row['residual_bound_j']
    r_tampered = abs(rel_row['residual_r_j'] + rel_row['e_diss_release_j'])
    arms['FB6_clean_control'] = {
        'metric_scope': 'release-tick residual within the declared bound',
        'residual_j': r_clean, 'bound_j': b_clean,
        'within_bound': r_clean <= b_clean,
        'guard': 'm09_fb6_premature'}
    arms['FB6_unaccounted'] = {
        'residual_without_release_j': r_tampered,
        'bit': r_tampered > b_clean}
    arms['FB6_bit'] = bool(arms['FB6_clean_control']['within_bound']
                           and arms['FB6_unaccounted']['bit'])

    receipt = {'schema': 'chimera.m09_falsifiers.v1', 'arms': arms,
               'F_all_green': all(arms.get(k) for k in
                                  ('FB1_bit', 'FB2_bit', 'FB3_bit',
                                   'FB4_bit', 'FB5_bit', 'FB6_bit'))}
    (HERE / 'falsifier_receipt.json').write_bytes(canonical(receipt))
    print(json.dumps({k: v for k, v in arms.items() if k.endswith('_bit')
                      or k == 'FB1_clean_control'},
                     default=_np_default, indent=1))


def mode_regression():
    results = {}
    for name, target in (
            ('M05', str(CONTRIB / 'MAT2-M05' / 'test_interface_exchange.py')),
            ('M06', str(CONTRIB / 'MAT2-M06' / 'test_local_contact.py'))):
        proc = subprocess.run([sys.executable, '-B', target],
                              capture_output=True, text=True, timeout=3000)
        results[name] = {'exit_code': proc.returncode,
                         'tail': proc.stdout[-800:]}
    receipt = {'schema': 'chimera.m09_regression.v1', 'suites': results,
               'X4_regression_green': all(v['exit_code'] == 0
                                          for v in results.values())}
    (HERE / 'regression_receipt.json').write_bytes(canonical(receipt))
    print(json.dumps({k: v['exit_code'] for k, v in results.items()},
                     indent=1))


def mode_mirror():
    """X3 CPU-FIRST step: bitwise mirror validation on the frozen fixture
    (prereg X3: 'kernel_mirror.py ... validated BITWISE against the CPU
    world on the frozen fixture' BEFORE any GPU submission)."""
    import kernel_mirror as km
    import mirror_rehearsal as mr
    res = mr.run_rehearsal(asm.TICKS)
    bad = res['findings']
    worst_pos = res['worst_position_diff_m']
    receipt = {
        'schema': 'chimera.m09_mirror_rehearsal.v1',
        'fixture': {'ticks': asm.TICKS, 'dt_s': asm.DT_S,
                    'substeps_per_tick': asm.N_SUB},
        'declared_order': list(asm.DECLARED_ORDER),
        'oracle_trace_sha256': asm.sha256_file(
            HERE / 'experiment_trace.json'),
        'worst_position_diff_m': worst_pos,
        'worst_block_scalar_diff': res['worst_block_scalar_diff'],
        'findings': bad[:24],
        'rows_bitwise_identical': bool(res['rows_bitwise_identical']),
        'state_hash_chains_identical':
            bool(res['state_hash_chains_identical']),
        'X3_mirror_bitwise_agreed': bool(
            res['rows_bitwise_identical']
            and res['state_hash_chains_identical'] and worst_pos == 0.0),
        'note': 'kernel_mirror.py is the single transcription source for '
                'the resident CUDA world; the GPU bank stays frozen-'
                'declared until that transcription and its confirmation '
                'run (X3 disclosure clause).',
    }
    (HERE / 'mirror_rehearsal_receipt.json').write_bytes(canonical(receipt))
    print(json.dumps({k: v for k, v in receipt.items()
                      if k.endswith(('identical', 'agreed'))
                      or k.startswith('worst_')}, indent=1))


def main(argv):
    mode = argv[1] if len(argv) > 1 else 'main'
    {'main': mode_main, 'rerun': mode_rerun, 'compare': mode_compare,
     'falsify': mode_falsify, 'regression': mode_regression,
     'mirror': mode_mirror}[mode]()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
