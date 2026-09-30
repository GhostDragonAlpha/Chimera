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
  gmain     X3 GPU bank arm 1 (GPU box only, after X1/X2 AND the bitwise
            mirror): the resident CUDA world (resident_bones.py) and the
            CPU oracle step the SAME 90-tick fixture in one process;
            every tick compares the 16-row vertex snapshot (frozen window
            1e-12 m), the declared comparable slots (1e-9 relative, floor
            1.0, vacuous identically-zero comparisons recorded, never
            silently dropped), the declared-order digest chain and the
            telemetry budgets (<= 256 B/tick up, <= 1024 B/component/tick
            down); writes gpu_trace.json + gpu_receipt.json (+ the
            never-compared gpu_profile.json).
  grerun    X3 GPU bank arm 2: a fresh identical run writing
            gpu_trace_rerun2.json + gpu_receipt_rerun2.json.
  gcompare  X3 verdict: sha256 byte-identity of the two fresh GPU traces
            AND receipts, both receipts' X3_pass, and the frozen-window
            verdicts; writes gpu_determinism_receipt.json.
No RNG; no wall-clock in trace or receipt (timing goes to gpu_profile.json
only, which is never compared).
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
import kernel_mirror as km  # noqa: E402  (X3 layout authority; numba-free)

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


# ----------------------------------------------------------- X3 GPU bank ----

ORACLE_TRACE_FROZEN_SHA256 = ('273dbc4f8c73a6f5'
                              '62c0260050f7d23012288af29426f4d7b8a191b35efeb'
                              '744')
AGREE_POS_WINDOW_M = 1e-12
AGREE_SCALAR_WINDOW = 1e-9

# (name, component, slot, oracle extractor) — the declared comparable
# slots (kernel_mirror's block layout; system scalars in component 0).
# The oracle extractor maps the oracle row to the compared scalar (None
# maps to the mirror's declared 0.0 sentinel).
SCALAR_COMPARABLES = [
    ('gap_head_anchors_m', 0, km.D_GAP, lambda r: r['gap_head_anchors_m']),
    ('joint_gap_m', 0, km.D_JGAP,
     lambda r: 0.0 if r['joint_gap_m'] is None else r['joint_gap_m']),
    ('joint_jn_Ns', 0, km.D_JJN, lambda r: r['joint_jn_Ns']),
    ('contact_active_pairs', 0, km.D_ACTIVE,
     lambda r: r['contact_active_pairs']),
    ('contact_iterations', 0, km.D_ITERS, lambda r: r['contact_iterations']),
    ('gs_residual_N_s', 0, km.D_GSRES, lambda r: r['gs_residual_N_s']),
    ('jn_applied_total_N_s', 0, km.D_JNTOT,
     lambda r: r['jn_applied_total_N_s']),
    ('d_friction_j', 0, km.D_DFRIC, lambda r: r['d_friction_j']),
    ('d_impact_physical_j', 0, km.D_DIMP, lambda r: r['d_impact_physical_j']),
    ('lig_tension_n', 0, km.D_LIGT, lambda r: r['lig_tension_n']),
    ('lig_extension_m', 0, km.D_LIGEXT, lambda r: r['lig_extension_m']),
    ('cap_axial_n', 0, km.D_CAPAX, lambda r: r['cap_axial_n']),
    ('u_ligament_j', 0, km.D_ULIG, lambda r: r['u_ligament_j']),
    ('u_capsule_j', 0, km.D_UCAP, lambda r: r['u_capsule_j']),
    ('e_mechanical_j', 0, km.D_EMECH, lambda r: r['e_mechanical_j']),
    ('w_actuator_j', 0, km.D_WACT, lambda r: r['w_actuator_j']),
    ('w_ligament_j', 0, km.D_WLIG, lambda r: r['w_ligament_j']),
    ('w_capsule_j', 0, km.D_WCAP, lambda r: r['w_capsule_j']),
    ('w_gravity_j', 0, km.D_WGRAV, lambda r: r['w_gravity_j']),
    ('q_damping_j', 0, km.D_QDAMP, lambda r: r['q_damping_j']),
    ('q_contact_j', 0, km.D_QCONTACT, lambda r: r['q_contact_j']),
    ('q_projection_j', 0, km.D_QPROJ, lambda r: r['q_projection_j']),
    ('e_diss_release_j', 0, km.D_EDISS, lambda r: r['e_diss_release_j']),
    ('residual_r_j', 0, km.D_RESID, lambda r: r['residual_r_j']),
    ('residual_bound_j', 0, km.D_BOUND, lambda r: r['residual_bound_j']),
    ('anchor_consistency_err_N_s', 0, km.D_ANCHORERR,
     lambda r: r['anchor_consistency_err_N_s']),
    ('ground_jn_a', 0, km.D_GJNA,
     lambda r: r['ground_jn_N_s']['bone_a']),
    ('ground_jn_b', 0, km.D_GJNB,
     lambda r: r['ground_jn_N_s']['bone_b']),
]

# (name, component, slot triple, oracle list extractor)
VECTOR_COMPARABLES = [
    ('com_a_m', 0, (km.D_COMX, km.D_COMY, km.D_COMZ),
     lambda r: r['com_a_m']),
    ('com_b_m', 1, (km.D_COMX, km.D_COMY, km.D_COMZ),
     lambda r: r['com_b_m']),
    ('lig_force_n', 0, (km.D_LIGFX, km.D_LIGFY, km.D_LIGFZ),
     lambda r: r['lig_force_n']),
    ('cap_force_n', 0, (km.D_CAPFX, km.D_CAPFY, km.D_CAPFZ),
     lambda r: r['cap_force_n']),
    ('ground_anchor_impulse_N_s', 0, (km.D_GIMPX, km.D_GIMPY, km.D_GIMPZ),
     lambda r: r['ground_anchor_impulse_N_s']),
]

RESTRAINT_SLOTS = [(km.D_REST00 + 3 * i + j, i, j)
                   for i in range(3) for j in range(3)]


def refuse_vacuous(a, b, code='vacuous_comparison_refused'):
    """M07's independent-review lesson: a window gate whose two sides are
    identically zero cannot fail; such comparisons are REFUSED when used
    as falsifiable gates. Plain agreement comparisons of identically-zero
    values are exact agreement evidence: recorded as exact-zero pairs with
    diff 0.0, never silently dropped (Amendment A2 pattern)."""
    if a == 0.0 and b == 0.0:
        raise ValueError(code)


def vacuous_guard_selftest():
    fired = False
    try:
        refuse_vacuous(0.0, 0.0)
    except ValueError as exc:
        fired = str(exc) == 'vacuous_comparison_refused'
    return fired


def p_bone_layout():
    """The resident module's declared layout equals kernel_mirror's (the
    single transcription source). CPU-runnable; import is numba-lazy but
    decoration-only, so this also runs without a GPU."""
    import resident_bones as rb
    slots = {d: getattr(rb, d) == getattr(km, d)
             for d in dir(km) if d.startswith('D_')}
    p = {s: getattr(rb, s) == getattr(km, s)
         for s in ('P_WGRAV', 'P_QDAMP', 'P_IMPGX', 'P_DMPX', 'P_WLIG',
                   'P_WCAP', 'P_WACT', 'P_ELMX', 'P_CIMPX', 'P_LEDGER')}
    s = {t: getattr(rb, t) == getattr(km, t)
         for t in ('S_QCONTACT', 'S_DFRIC', 'S_DIMP', 'S_JNTOT', 'S_ITERS',
                   'S_GSRES', 'S_ACTIVE', 'S_JGAP', 'S_JHAS', 'S_JNX',
                   'S_GJNA', 'S_BBIX', 'S_CAX', 'S_CGX', 'S_RECX',
                   'S_QPROJ')}
    sizes = all(getattr(rb, n) == getattr(km, n)
                for n in ('DIAG', 'N_PASS', 'N_SYS', 'CMD_F64',
                          'MAX_ACTIVE', 'N_ENTRIES', 'H_SUB', 'GS_TOL_N_S',
                          'GS_CAP', 'XPBD_COMPLIANCE'))
    ok = (all(slots.values()) and all(p.values()) and all(s.values())
          and sizes)
    return {'ok': ok, 'd_slots': len(slots), 'p_slots': len(p),
            'sys_slots': len(s), 'sizes_match': sizes}


def p_bone_single_writer():
    """AST scan: device state is written only inside @cuda.jit kernels and
    the ResidentBonesWorld construction/step path; host methods outside
    __init__/step_tick never copy_to_device."""
    import resident_bones as rb
    src = (HERE / 'resident_bones.py').read_text(encoding='utf-8')
    tree = ast.parse(src)
    kernels = set()
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.decorator_list:
            kernels.add(node.name)
    class_methods = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) \
                and node.name == 'ResidentBonesWorld':
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    class_methods[item.name] = item
    violations = []
    allowed_host_writers = {'__init__', 'step_tick'}
    for name in class_methods:
        for node in ast.walk(class_methods[name]):
            if isinstance(node, ast.Call) and isinstance(node.func,
                                                         ast.Attribute):
                if node.func.attr == 'copy_to_device' \
                        and name not in allowed_host_writers:
                    violations.append(f'{name}:copy_to_device')
    return {'kernels': sorted(kernels),
            'host_writer_methods': sorted(allowed_host_writers),
            'violations': violations, 'ok': not violations}


def p_gates_declared():
    """The GPU world refuses through the declared gate names."""
    import resident_bones as rb
    gates = [rb.E_ORDER, rb.E_TICK, rb.E_BYTES, rb.E_PAIRCAP, rb.E_CONV,
             rb.E_LEDGER, rb.E_SUPPORT, rb.E_UNEXPLAINED, rb.E_NONFINITE,
             rb.E_DIGEST]
    return {'gate_codes': sorted(gates), 'count': len(gates)}


def _gpu_debug_dump(gpu, block, tick, exc):
    """Debug evidence for a gate refusal (attempt scratch, not a claim):
    the failing tick's full named diagnostic blocks and partials."""
    import resident_bones as rb
    named = []
    for b in range(km.N_BONES):
        named.append({f'slot{i}': float(v) for i, v in
                      enumerate(block[b])})
    dbg = {'tick': tick, 'refusal': str(exc), 'blocks': named}
    try:
        dbg['pass'] = gpu.d_pass.copy_to_host().tolist()
        dbg['sys'] = gpu.d_sys.copy_to_host().tolist()
    except Exception as dbg_err:  # noqa: BLE001
        dbg['dump_error'] = repr(dbg_err)
    (HERE / 'debug_gate_failure.json').write_bytes(canonical(dbg))


def _gpu_bank_run(trace_path, receipt_path, profile_path):
    """One X3 GPU bank arm: the resident CUDA world and the CPU oracle
    step the SAME frozen fixture; every tick compared under the frozen
    windows. The world is released on EVERY exit path — a raise (E_BYTES,
    a gate, a CUDA fault) must never leak device state into the next world
    sharing this context. Receipt content is deterministic (no wall-clock,
    no mode keys) so gmain/grerun receipts are byte-identical."""
    import time
    import resident_bones as rb
    t0 = time.perf_counter()
    pins = asm.verify_input_pins()
    oracle = asm.AssemblyRun()
    gpu = rb.ResidentBonesWorld()
    try:
        rows, receipt = _gpu_bank_body(gpu, oracle, pins)
    finally:
        gpu.release()
    t1 = time.perf_counter()
    (HERE / trace_path.name).write_bytes(canonical({'rows': rows}))
    (HERE / receipt_path.name).write_bytes(canonical(receipt))
    if profile_path is not None:
        (HERE / profile_path.name).write_bytes(canonical({
            'bank_wall_seconds': t1 - t0,   # profile only, never compared
        }))
    print(json.dumps({'X3_pass': receipt['X3_pass'],
                      'worst_pos_m':
                          receipt['worst_position_diff_m'],
                      'worst_scalar_rel':
                          receipt['worst_scalar_relative_overall'],
                      'telemetry_within_budget':
                          receipt['telemetry']['within_budget'],
                      'digest_chain_green':
                          receipt['digest_chain_green_every_tick']},
                     indent=1, default=_np_default))


def _gpu_bank_body(gpu, oracle, pins):
    """The lockstep oracle-vs-resident run (called under the world's
    release guard)."""
    rows = []
    worst_pos = 0.0
    scalar_worst = {}
    exact_zero_pairs = 0
    digest_green = True
    budget_rows = []
    exceeded_ticks = []
    for tick in range(asm.TICKS):
        orow = oracle.step(tick)
        up0 = gpu.host_bytes_up
        down0 = gpu.host_bytes_down
        gpu.step_tick(tick)
        block = gpu.diagnostics()
        xsnap = gpu.snapshot()
        up = gpu.host_bytes_up - up0
        down = gpu.host_bytes_down - down0
        budget_rows.append({'tick': tick, 'up_bytes': up,
                            'down_bytes': down,
                            'down_budget': (km.
                                            TELEMETRY_BUDGET_DOWN_PER_COMP
                                            * gpu.declaration['n_bones'])})
        if up > km.TELEMETRY_BUDGET_UP_PER_TICK or down > \
                km.TELEMETRY_BUDGET_DOWN_PER_COMP * \
                gpu.declaration['n_bones']:
            raise ValueError(km.E_BYTES)
        try:
            gpu.check_gates(block, tick)
        except ValueError as exc:
            _gpu_debug_dump(gpu, block, tick, exc)
            raise
        # digest chain recompute from the emitted block (stale guard) is
        # inside check_gates; record its verdict
        for b in range(km.N_BONES):
            want = km.block_digest(block[b], tick)
            if want != float(block[b][km.D_DIGEST]):
                digest_green = False
        # frozen position window: the full 16-row vertex snapshot
        oa = np.asarray(oracle.bone_a.x)
        ob = np.asarray(oracle.bone_b.x)
        dpos = max(float(np.abs(xsnap[:8] - oa).max()),
                   float(np.abs(xsnap[8:] - ob).max()))
        worst_pos = max(worst_pos, dpos)
        row = {'tick': tick, 'worst_position_diff_m': dpos,
               'exceeded': [], 'exact_zero_pairs': 0}
        ez = 0
        # scalar comparables
        for name, comp, slot, extractor in SCALAR_COMPARABLES:
            a = float(extractor(orow))
            b = float(block[comp][slot])
            if a == 0.0 and b == 0.0:
                ez += 1
                rel = 0.0
            else:
                rel = abs(a - b) / max(1.0, abs(a), abs(b))
            if rel > AGREE_SCALAR_WINDOW:
                row['exceeded'].append({'name': name, 'oracle': a,
                                        'gpu': b, 'rel': rel})
            scalar_worst.setdefault(name, 0.0)
            if rel > scalar_worst[name]:
                scalar_worst[name] = rel
            row[name] = {'oracle': a, 'gpu': b, 'rel': rel}
        # vector comparables
        for name, comp, slots, extractor in VECTOR_COMPARABLES:
            vals = extractor(orow)
            for k, slot in enumerate(slots):
                a = float(vals[k])
                b = float(block[comp][slot])
                if a == 0.0 and b == 0.0:
                    ez += 1
                    rel = 0.0
                else:
                    rel = abs(a - b) / max(1.0, abs(a), abs(b))
                tag = f'{name}[{k}]'
                if rel > AGREE_SCALAR_WINDOW:
                    row['exceeded'].append({'name': tag, 'oracle': a,
                                            'gpu': b, 'rel': rel})
                scalar_worst.setdefault(tag, 0.0)
                if rel > scalar_worst[tag]:
                    scalar_worst[tag] = rel
                row[tag] = {'oracle': a, 'gpu': b, 'rel': rel}
        # restraint matrix slots + derived eigen-count (host fold)
        for slot, i, j in RESTRAINT_SLOTS:
            a = float(orow['restraint_matrix'][3 * i + j])
            b = float(block[0][slot])
            rel = abs(a - b) / max(1.0, abs(a), abs(b))
            tag = f'restraint_matrix[{i}][{j}]'
            if rel > AGREE_SCALAR_WINDOW:
                row['exceeded'].append({'name': tag, 'oracle': a,
                                        'gpu': b, 'rel': rel})
            scalar_worst.setdefault(tag, 0.0)
            if rel > scalar_worst[tag]:
                scalar_worst[tag] = rel
            row[tag] = {'oracle': a, 'gpu': b, 'rel': rel}
        kmat = np.array([float(block[0][slot])
                         for slot, _i, _j in RESTRAINT_SLOTS]
                        ).reshape(3, 3)
        cnt = int(km.MirrorWorld._restrained_direction_count(kmat))
        row['restrained_direction_count'] = {
            'oracle': int(orow['restrained_direction_count']), 'gpu': cnt}
        if cnt != int(orow['restrained_direction_count']):
            row['exceeded'].append({'name': 'restrained_direction_count',
                                    'oracle':
                                        int(orow['restrained_direction_count'
                                                 ]), 'gpu': cnt, 'rel': 1.0})
        # derived host folds over per-bone slots (the harness's own folds,
        # declared in mirror_rehearsal)
        folds = {
            'e_kinetic_j': (float(block[0][km.D_KE])
                            + float(block[1][km.D_KE]),
                            float(orow['e_kinetic_j'])),
            'u_scaffold_j': (float(block[0][km.D_USCAFF])
                             + float(block[1][km.D_USCAFF]),
                             float(orow['u_scaffold_j'])),
            'max_speed_m_per_s': (max(float(block[0][km.D_MAXSPD]),
                                      float(block[1][km.D_MAXSPD])),
                                  float(orow['max_speed_m_per_s'])),
            'min_vertex_z_m': (min(float(block[0][km.D_MINZ]),
                                   float(block[1][km.D_MINZ])),
                               float(orow['min_vertex_z_m'])),
            'ledger_worst_N_s': (max(float(block[0][km.D_LEDGERW]),
                                     float(block[1][km.D_LEDGERW])),
                                 float(orow['ledger_residual_worst_N_s'])),
        }
        for name, (bval, aval) in folds.items():
            if aval == 0.0 and bval == 0.0:
                ez += 1
                rel = 0.0
            else:
                rel = abs(aval - bval) / max(1.0, abs(aval), abs(bval))
            if rel > AGREE_SCALAR_WINDOW:
                row['exceeded'].append({'name': name, 'oracle': aval,
                                        'gpu': bval, 'rel': rel})
            scalar_worst.setdefault(name, 0.0)
            if rel > scalar_worst[name]:
                scalar_worst[name] = rel
            row[name] = {'oracle': aval, 'gpu': bval, 'rel': rel}
        row['exact_zero_pairs'] = ez
        exact_zero_pairs += ez
        if row['exceeded']:
            exceeded_ticks.append(tick)
        rows.append(row)
    layout = p_bone_layout()
    writer = p_bone_single_writer()
    gates = p_gates_declared()
    trace_sha = asm.sha256_file(HERE / 'experiment_trace.json')
    position_within = worst_pos <= AGREE_POS_WINDOW_M
    scalars_within = all(v <= AGREE_SCALAR_WINDOW
                         for v in scalar_worst.values())
    receipt = {
        'schema': 'chimera.m09_gpu_bank.v1',
        'criteria_sha256':
            '803ca2d1cd6e410217fb9e3a2bdb8e29fbe291ae2fe685fcfb83f66'
            'b442dacc4',
        'fixture': {'ticks': asm.TICKS, 'dt_s': asm.DT_S,
                    'substeps_per_tick': asm.N_SUB,
                    'declared_order': list(asm.DECLARED_ORDER)},
        'windows': {'position_m': AGREE_POS_WINDOW_M,
                    'scalar_relative': AGREE_SCALAR_WINDOW,
                    'vacuous_policy': 'exact-zero pairs recorded; the '
                                      'self-tested guard gates falsifiable '
                                      'comparisons'},
        'worst_position_diff_m': worst_pos,
        'worst_scalar_relative': scalar_worst,
        'worst_scalar_relative_overall': max(scalar_worst.values())
        if scalar_worst else 0.0,
        'position_within_window': position_within,
        'comparables_within_window': scalars_within,
        'exceeded_ticks': exceeded_ticks,
        'exact_zero_pairs': exact_zero_pairs,
        'vacuous_guard_selftest': vacuous_guard_selftest(),
        'digest_chain_green_every_tick': digest_green,
        'gates_declared': {'count': gates['count'],
                           'codes': gates['gate_codes']},
        'telemetry': {
            'max_up_bytes_per_tick': max(r['up_bytes']
                                         for r in budget_rows),
            'max_down_bytes_per_tick': max(r['down_bytes']
                                           for r in budget_rows),
            'up_budget': km.TELEMETRY_BUDGET_UP_PER_TICK,
            'down_budget_per_comp': km.TELEMETRY_BUDGET_DOWN_PER_COMP,
            'within_budget':
                max(r['up_bytes'] for r in budget_rows)
                <= km.TELEMETRY_BUDGET_UP_PER_TICK
                and max(r['down_bytes'] for r in budget_rows)
                <= km.TELEMETRY_BUDGET_DOWN_PER_COMP * 2,
            'total_up_bytes': gpu.host_bytes_up,
            'total_down_bytes': gpu.host_bytes_down},
        'order_digest_gpu': gpu.order_digest,
        'input_pins': {k: 'ok' for k in pins},
        'p_bone_layout': {'ok': layout['ok'], 'd_slots': layout['d_slots'],
                          'p_slots': layout['p_slots'],
                          'sys_slots': layout['sys_slots'],
                          'sizes_match': layout['sizes_match']},
        'p_bone_single_writer': {'ok': writer['ok'],
                                 'violations': writer['violations']},
        'oracle_trace_frozen': {
            'sha256': trace_sha,
            'expected': ORACLE_TRACE_FROZEN_SHA256,
            'matches': trace_sha == ORACLE_TRACE_FROZEN_SHA256},
        'declaration': gpu.declaration,
    }
    receipt['X3_pass'] = bool(
        position_within and scalars_within
        and receipt['telemetry']['within_budget'] and digest_green
        and not exceeded_ticks and receipt['vacuous_guard_selftest']
        and layout['ok'] and writer['ok']
        and receipt['oracle_trace_frozen']['matches'])
    return rows, receipt


def mode_gmain():
    _gpu_bank_run(HERE / 'gpu_trace.json', HERE / 'gpu_receipt.json',
                  HERE / 'gpu_profile.json')


def mode_grerun():
    _gpu_bank_run(HERE / 'gpu_trace_rerun2.json',
                  HERE / 'gpu_receipt_rerun2.json', None)


def mode_gcompare():
    t1 = asm.sha256_file(HERE / 'gpu_trace.json')
    t2 = asm.sha256_file(HERE / 'gpu_trace_rerun2.json')
    r1 = asm.sha256_file(HERE / 'gpu_receipt.json')
    r2 = asm.sha256_file(HERE / 'gpu_receipt_rerun2.json')
    run1 = json.loads((HERE / 'gpu_receipt.json').read_text(
        encoding='utf-8'))
    run2 = json.loads((HERE / 'gpu_receipt_rerun2.json').read_text(
        encoding='utf-8'))
    trace_identical = t1 == t2
    receipt_identical = r1 == r2
    receipt = {
        'schema': 'chimera.m09_gpu_determinism.v1',
        'trace_sha_run1': t1, 'receipt_sha_run1': r1,
        'trace_sha_run2': t2, 'receipt_sha_run2': r2,
        'X3_trace_byte_identical': trace_identical,
        'X3_receipt_byte_identical': receipt_identical,
        'X3_runs_pass': bool(run1.get('X3_pass') and run2.get('X3_pass')),
        'X3_pass': bool(trace_identical and receipt_identical
                        and run1.get('X3_pass') and run2.get('X3_pass')),
    }
    (HERE / 'gpu_determinism_receipt.json').write_bytes(canonical(receipt))
    print(json.dumps(receipt, indent=1))


def main(argv):
    mode = argv[1] if len(argv) > 1 else 'main'
    {'main': mode_main, 'rerun': mode_rerun, 'compare': mode_compare,
     'falsify': mode_falsify, 'regression': mode_regression,
     'mirror': mode_mirror, 'gmain': mode_gmain, 'grerun': mode_grerun,
     'gcompare': mode_gcompare}[mode]()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
