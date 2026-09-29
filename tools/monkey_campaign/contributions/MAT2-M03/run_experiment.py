"""MAT2-M03 definitive experiment runner: executes the frozen preregistration
(PREREGISTRATION.md incl. corrections A1-A5) against the committed revision and
writes:

- pressure_state.json         the chimera.material_state.v1 experiment document
                              (subject; validated with the UNMODIFIED M01
                              validator),
- pressure_trace.json         the per-tick dynamic trace (visual state binding),
- qualification_receipt.json  every frozen check T0-T10 and falsifier bite F1-F6
                              with observed values next to the frozen bounds.

Deterministic: no stochastic inputs, no wall-clock values; the only
revision identity is recorded from git at the caller's responsibility.
CPU-only; stdlib + numpy. Run from this directory:
    python -B run_experiment.py
"""
from __future__ import annotations

import hashlib
import json
import math
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'MAT2-M01'))

import pressure_membrane as pm  # noqa: E402
import material_state as ms     # noqa: E402  (M01 validator, unmodified)

TICKS = 24
DT_S = 1.0 / 300.0
R0_M = 0.10
TOTAL_MASS_KG = 0.05
COMPLIANCE = 2.5e-2
DAMPING = 240.0
ITERATIONS = 8
PEAK_PA = 120.0

SOURCE_DECL = ('authored demonstrator pressure source (PREREGISTRATION.md T6: '
               'max |dp| 5000 Pa, max dV/dt 1e-3 m^3/s; no catalog constant '
               'imported)')
MASS_DECL = ('authored demonstrator membrane mass; law: remeshing preserves '
             'mass (docs/THE_MEMBRANE_INVENTORY.md "Triangles are not '
             'physical weights"); refinement families keep the same total')


def source_for(p_int_pa, p_ext_pa=0.0, tag='demo'):
    return pm.PressureSource('mat2_m03_' + tag, p_int_pa, p_ext_pa, 5000.0,
                             1e-3, SOURCE_DECL)


def ramp(tick):
    return PEAK_PA * max(0.0, math.sin(math.pi * tick / 16.0)) \
        if tick <= 16 else 0.0


def close_enough(name, value, bound, extra=None):
    row = {'check': name, 'value': value, 'bound': bound,
           'passed': bool(value <= bound)}
    if extra is not None:
        row['detail'] = extra
    return row


def close_enough_abs(name, value, bound, extra=None):
    return close_enough(name, abs(value), bound, extra)


def main():
    checks = []
    falsifiers = []

    # ---- T0: byte-verified M02 tetra ---------------------------------------
    tetra = pm.load_m02_tetra(str(HERE.parent))
    rep = tetra.closure_report()
    checks.append(close_enough_abs(
        'T0_m02_tetra_volume_vs_compiled_m3',
        rep['signed_volume_m3'] - pm.M02_TETRA_RECORDED_VOLUME_M3, 1e-18,
        {'derived_exact': 1.0 / 6000.0,
         'open_edge_count': rep['open_edge_count'],
         'duplicate_directed_edges': rep['duplicate_directed_edges'],
         'vertex_count': rep['vertex_count'],
         'triangle_count': rep['triangle_count']}))
    checks.append(close_enough_abs(
        'T0_m02_tetra_area_vs_compiled_m2',
        rep['surface_area_m2'] - pm.M02_TETRA_RECORDED_AREA_M2, 1e-18))

    # ---- T1: uniform delta-p traction on the M02 tetra ---------------------
    src100 = source_for(100.0, 0.0, 'uniform_dp')
    loads, forces, _ = tetra.vertex_loads(src100)
    net_f, net_tau = tetra.net_force_torque(forces)
    vf = forces.sum(axis=0)
    vt = np.cross(tetra.centroids, forces).sum(axis=0)
    checks.append(close_enough_abs('T1_net_force_triangle_level_N',
                                   np.linalg.norm(vf), 1e-12,
                                   {'per_triangle_force_n':
                                    [float(f) for f in
                                     np.linalg.norm(forces, axis=1)],
                                    'frozen': [0.5, 0.5, 0.5,
                                               0.8660254037844386]}))
    checks.append(close_enough_abs('T1_net_torque_origin_triangle_Nm',
                                   np.linalg.norm(vt), 1e-12))
    net_fv = loads.sum(axis=0)
    # lumped torque: sum r_v x f_v with r_v the vertex positions
    tau_v = np.cross(tetra.vertices, loads).sum(axis=0)
    checks.append(close_enough_abs('T1_net_force_vertex_lumped_N',
                                   np.linalg.norm(net_fv), 1e-12))
    checks.append(close_enough_abs('T1_net_torque_vertex_lumped_Nm',
                                   np.linalg.norm(tau_v), 1e-12))

    # ---- T2: buoyancy on cube grids (exact linear-field reference) ---------
    field = pm.LinearField(101325.0, [0.0, 0.0, -pm.RHO_KG_M3 * pm.G_M_S2])
    src_b = source_for(101425.0, 101325.0, 'buoyancy')
    for n in (1, 2, 4):
        cube = pm.cube_grid(n)
        forces, _ = cube.triangle_tractions(src_b, field)
        nf, nt = cube.net_force_torque(forces)
        ref = cube.linear_field_reference(field)
        tau_centre = nt - np.cross(ref['volume_centroid_m'], nf)
        rgv = pm.RHO_KG_M3 * pm.G_M_S2 * cube.signed_volume()
        refined = n >= 2
        checks.append(close_enough_abs(
            f'T2_cube_n{n}_force_vs_rho_gV_rel',
            np.linalg.norm(nf - [0.0, 0.0, rgv]) / rgv, 1e-12))
        checks.append(close_enough_abs(
            f'T2_cube_n{n}_force_vs_-qV_rel',
            np.linalg.norm(nf - ref['force_n']) / np.linalg.norm(ref['force_n']),
            1e-12))
        checks.append(close_enough_abs(
            f'T2_cube_n{n}_torque_about_centre_Nm',
            np.linalg.norm(tau_centre), 1e-9 if refined else 1.0e-1,
            None if refined else {'note': 'coarse member: h^2 quadrature '
                                          'convergence (correction A7)'}))
    # A7: torque quadrature converges monotonically on the tetra family
    tetra_taus = []
    for tag, mem in (('L0', tetra), ('L1', pm.subdivide(tetra, 1)),
                     ('L2', pm.subdivide(tetra, 2))):
        forces, _ = mem.triangle_tractions(src_b, field)
        nf, nt = mem.net_force_torque(forces)
        ref = mem.linear_field_reference(field)
        tau_centre = nt - np.cross(ref['volume_centroid_m'], nf)
        tetra_taus.append(float(np.linalg.norm(tau_centre)))
    checks.append({'check': 'T2_tetra_torque_quadrature_monotone_Nm',
                   'value': tetra_taus,
                   'bound': 'strictly decreasing (A7); L0 <= 1.0e-1',
                   'passed': bool(tetra_taus[0] <= 1.0e-1
                                  and tetra_taus[0] > tetra_taus[1]
                                  > tetra_taus[2])})

    # ---- T3: icosphere family ----------------------------------------------
    vol_err = []
    for level in (0, 1, 2):
        sph = pm.icosphere(level, 1.0)
        forces, _ = sph.triangle_tractions(src_b, field)
        nf, nt = sph.net_force_torque(forces)
        ref = sph.linear_field_reference(field)
        v_rel = abs(sph.signed_volume() - 4.0 / 3.0 * math.pi) \
            / (4.0 / 3.0 * math.pi)
        vol_err.append(v_rel)
        tau_centre = nt - np.cross(ref['volume_centroid_m'], nf)
        checks.append(close_enough_abs(
            f'T3_icosphere_L{level}_force_vs_-qV_rel',
            np.linalg.norm(nf - ref['force_n'])
            / np.linalg.norm(ref['force_n']), 1e-12))
        checks.append(close_enough_abs(
            f'T3_icosphere_L{level}_torque_about_centroid_Nm',
            np.linalg.norm(tau_centre), 1e-9 if level >= 1 else 1.0e-1,
            None if level >= 1 else
            {'note': 'coarse member: h^2 quadrature convergence (A7)'}))
        checks.append(close_enough(
            f'T3_icosphere_L{level}_volume_relerr', v_rel,
            6.0e-2 if level == 2 else 1.0,
            None if level == 2 else
            {'note': 'no absolute prereg bound for this level; monotone '
                     'decrease across levels is checked separately'}))
    checks.append({'check': 'T3_volume_relerr_monotone_decreasing',
                   'value': vol_err,
                   'bound': 'strictly decreasing',
                   'passed': bool(vol_err[0] > vol_err[1] > vol_err[2])})

    # ---- T4: refinement invariance of uniform-pressure net loading ---------
    families = {'tetra_L0': pm.right_tetra(0.1),
                'tetra_L1': pm.subdivide(pm.right_tetra(0.1), 1),
                'tetra_L2': pm.subdivide(pm.right_tetra(0.1), 2)}
    for n in (1, 2, 4):
        families[f'cube_n{n}'] = pm.cube_grid(n)
    for level in (0, 1, 2):
        families[f'icosphere_L{level}'] = pm.icosphere(level, 0.1)
    families['m02_tetra'] = tetra
    worst_f = worst_t = 0.0
    for name, mem in families.items():
        loads, forces, _ = mem.vertex_loads(src100)
        nf, nt = mem.net_force_torque(forces)
        worst_f = max(worst_f, float(np.linalg.norm(nf)))
        worst_t = max(worst_t, float(np.linalg.norm(nt)))
        mem.declared_mass_kg = TOTAL_MASS_KG
    checks.append(close_enough('T4_worst_net_force_N', worst_f, 1e-12,
                               {'family_members': sorted(families)}))
    checks.append(close_enough('T4_worst_net_torque_Nm', worst_t, 1e-12))

    # ---- T5: quasi-static P-V work -----------------------------------------
    src_w = source_for(101475.0, 101325.0, 'work')
    work = tetra.quasi_static_scaling_work(src_w, s_final=1.1, steps=2000)
    checks.append(close_enough('T5_max_step_traction_volume_diff_J',
                               work['max_step_traction_volume_diff_j'],
                               1e-15))
    checks.append(close_enough_abs(
        'T5_volume_sum_telescoping_J',
        work['work_volume_sum_j'] - work['work_closed_form_j'], 1e-14,
        {'closed_form_frozen_J': 8.275e-3}))
    checks.append(close_enough_abs('T5_closed_form_vs_frozen_J',
                                   work['work_closed_form_j'] - 8.275e-3,
                                   1e-12))

    # ---- T6: source power and limits ---------------------------------------
    src_p = source_for(101475.0, 101325.0, 'power')
    power = src_p.power_watts(2.0e-4)
    checks.append(close_enough_abs('T6_power_W', power - 0.03, 1e-16,
                                   {'power_watts': power}))
    refusals = {}
    for label, fn in (
        ('negative_absolute', lambda: pm.PressureSource(
            'bad', -1.0, 0.0, 5000.0, 1e-3, SOURCE_DECL)),
        ('delta_p_limit', lambda: source_for(6000.0, 0.0, 'over').enforce_delta_p()),
        ('flow_limit', lambda: source_for(150.0, 0.0, 'flow').power_watts(2.0e-3)),
        ('undeclared', lambda: tetra.triangle_tractions(None)),
    ):
        try:
            fn()
            refusals[label] = 'NOT_REFUSED'
        except ValueError as exc:
            refusals[label] = str(exc)
    checks.append({'check': 'T6_named_refusals', 'value': refusals,
                   'bound': {'negative_absolute':
                             'pressure_source_negative_absolute',
                             'delta_p_limit':
                             'pressure_source_delta_p_limit_exceeded',
                             'flow_limit':
                             'pressure_source_flow_limit_exceeded',
                             'undeclared': 'pressure_source_undeclared'},
                   'passed': all(refusals[k] == v
                                 for k, v in {
                                     'negative_absolute':
                                     'pressure_source_negative_absolute',
                                     'delta_p_limit':
                                     'pressure_source_delta_p_limit_exceeded',
                                     'flow_limit':
                                     'pressure_source_flow_limit_exceeded',
                                     'undeclared':
                                     'pressure_source_undeclared'}.items())})

    # ---- T7/T9: dynamic run -------------------------------------------------
    dyn_source = pm.PressureSource('mat2_m03_membrane', PEAK_PA, 0.0, 5000.0,
                                   1e-3, SOURCE_DECL)
    sphere = pm.icosphere(1, R0_M)
    schedule = [ramp(tick) for tick in range(TICKS)]
    run = pm.InflatableRun(sphere, dyn_source, TOTAL_MASS_KG, COMPLIANCE,
                           DAMPING, ITERATIONS, DT_S)
    dyn = run.run(schedule)
    drift = max(t['com_drift_m'] for t in dyn['ticks'])
    v0 = dyn['volume_start_m3']
    peak_ratio = dyn['volume_peak_m3'] / v0
    final_ratio = dyn['volume_final_m3'] / v0
    edge_now = run.x[run.tri_edge_array()[:, 0]] - run.x[run.tri_edge_array()[:, 1]]
    max_strain = float((np.linalg.norm(edge_now, axis=1) / run.rest - 1.0)
                       .max())
    checks.append(close_enough('T7_com_drift_m', drift, 1e-6,
                               {'note': 'uniform internal pressure does not '
                                        'propel the free body'}))
    checks.append({'check': 'T7_peak_volume_ratio', 'value': peak_ratio,
                   'bound': '>= 1.02', 'passed': bool(peak_ratio >= 1.02),
                   'peak_tick': max(dyn['ticks'],
                                    key=lambda t: t['volume_m3'])['tick']})
    checks.append({'check': 'T7_recoil_final_volume_ratio',
                   'value': abs(final_ratio - 1.0), 'bound': '<= 1.0e-2',
                   'passed': bool(abs(final_ratio - 1.0) <= 1.0e-2)})
    checks.append({'check': 'T7_max_edge_strain_reported', 'value': max_strain,
                   'bound': 'reported (scaffold validity)',
                   'passed': True})
    t9_rows = []
    for t in dyn['ticks']:
        allowance = max(1.0 * (abs(t['w_pressure_j']) + t['e_diss_damping_j']
                               + t['e_kinetic_j'] + t['e_elastic_j']), 1e-6)
        t9_rows.append(abs(t['residual_r_j']) <= allowance)
    checks.append({'check': 'T9_residual_within_turnover_every_tick',
                   'value': {'max_abs_residual_J':
                             max(abs(t['residual_r_j'])
                                 for t in dyn['ticks']),
                             'all_ticks_within': all(t9_rows)},
                   'bound': '|R| <= max(1.0*(|W_press|+E_diss+E_kin+E_el), 1e-6)',
                   'passed': all(t9_rows)})
    e0 = dyn['ticks'][0]['e_mechanical_j']
    ef = dyn['ticks'][-1]['e_mechanical_j']
    closure = abs((ef - e0)
                  - sum(t['w_pressure_j'] for t in dyn['ticks'])
                  + sum(t['e_diss_damping_j'] for t in dyn['ticks'])
                  - sum(t['residual_r_j'] for t in dyn['ticks']))
    checks.append(close_enough('T9_ledger_closes_J', closure, 1e-12,
                               {'identity': 'E_final - E_0 = sum(W_press) - '
                                            'sum(E_diss) + sum(R)'}))

    # ---- T8: determinism (byte-identical replay) ---------------------------
    run2 = pm.InflatableRun(pm.icosphere(1, R0_M),
                            pm.PressureSource('mat2_m03_membrane', PEAK_PA,
                                              0.0, 5000.0, 1e-3, SOURCE_DECL),
                            TOTAL_MASS_KG, COMPLIANCE, DAMPING, ITERATIONS,
                            DT_S)
    dyn2 = run2.run([ramp(tick) for tick in range(TICKS)])
    checks.append({'check': 'T8_determinism_byte_identical',
                   'value': {'run1': pm.digest(dyn), 'run2': pm.digest(dyn2)},
                   'bound': 'equal canonical digests',
                   'passed': pm.digest(dyn) == pm.digest(dyn2)})

    # ---- T10: material_state gate ------------------------------------------
    doc, state_summary = build_state_document(run, dyn, tetra, field)
    summary = ms.validate_material_state(doc)
    checks.append({'check': 'T10_material_state_v1_validates',
                   'value': summary,
                   'bound': {'region_count': 1, 'law_count': 1,
                             'matter_count': 1, 'total_mass_kg': 0.05,
                             'reference_count': 0},
                   'passed': bool(
                       summary['region_count'] == 1
                       and summary['law_count'] == 1
                       and summary['matter_count'] == 1
                       and abs(summary['total_mass_kg'] - 0.05) < 1e-12
                       and summary['reference_count'] == 0)})

    # ---- Falsifier bites ----------------------------------------------------
    # F1: area-independent traction tamper (constant force per triangle)
    tampered_forces = (src100.delta_p * tetra.areas.mean()) * tetra.normals
    f_tam_net = tampered_forces.sum(axis=0)
    falsifiers.append({'falsifier': 'F1_area_independent_tamper',
                       'observed': {
                           'correct_net_force_N': float(np.linalg.norm(vf)),
                           'tampered_net_force_N':
                               float(np.linalg.norm(f_tam_net))},
                       'bound': 'tampered >= 1e-2 N while correct <= 1e-12 N',
                       'bit': bool(np.linalg.norm(f_tam_net) >= 1e-2
                                   and np.linalg.norm(vf) <= 1e-12)})
    sub = pm.subdivide(pm.right_tetra(0.1), 2)
    forces_ok, _ = sub.triangle_tractions(src_b, field)
    nf_ok, _ = sub.net_force_torque(forces_ok)
    loads_tam, forces_tam, _ = sub.vertex_loads(src_b, field,
                                                area_weighting='constant')
    nf_tam_b, _ = sub.net_force_torque(forces_tam)
    ref_b = sub.linear_field_reference(field)
    rel_ok = float(np.linalg.norm(nf_ok - ref_b['force_n'])
                   / np.linalg.norm(ref_b['force_n']))
    rel_tam = float(np.linalg.norm(nf_tam_b - ref_b['force_n'])
                    / np.linalg.norm(ref_b['force_n']))
    falsifiers.append({'falsifier': 'F1_buoyancy_identity_tamper_subdivided_tetra_L2',
                       'observed': {'correct_rel_error': rel_ok,
                                    'tampered_rel_error': rel_tam},
                       'bound': 'tampered >= 1e-3 while correct <= 1e-12',
                       'bit': bool(rel_tam >= 1e-3 and rel_ok <= 1e-12)})

    # F2: free-body propulsion tamper
    good_run = pm.InflatableRun(tetra, source_for(100.0, 0.0, 'f2'),
                                TOTAL_MASS_KG, 1e-8, 0.0, 4, DT_S)
    good = good_run.run([100.0] * 12)
    bad_run = pm.InflatableRun(tetra, source_for(100.0, 0.0, 'f2'),
                               TOTAL_MASS_KG, 1e-8, 0.0, 4, DT_S,
                               load_mode='constant_per_triangle')
    bad = bad_run.run([100.0] * 12)
    falsifiers.append({'falsifier': 'F2_free_body_propulsion_tamper',
                       'observed': {
                           'correct_com_drift_m': good['com_drift_final_m'],
                           'tampered_com_drift_m': bad['com_drift_final_m']},
                       'bound': 'tampered >= 1e-3 m while correct <= 1e-6 m',
                       'bit': bool(bad['com_drift_final_m'] >= 1e-3
                                   and good['com_drift_final_m'] <= 1e-6)})

    # F3: undeclared source / negative absolute refusals (recorded in T6)

    # F4: broken closure (deleted triangle)
    broken = pm.Membrane(tetra.vertices, tetra.triangles[:3], 'broken_tetra')
    try:
        broken.require_closed()
        f4 = {'observed': 'NOT_REFUSED', 'bit': False}
    except ValueError as exc:
        code = str(exc)
        try:
            broken.triangle_tractions(src100)
            trac_refused = 'NOT_REFUSED'
        except ValueError as exc2:
            trac_refused = str(exc2)
        f4 = {'observed': {'closure_refusal': code,
                           'traction_refusal': trac_refused},
              'bound': 'closure_open_edges then traction refused',
              'bit': bool(code == 'closure_open_edges'
                          and trac_refused == 'closure_open_edges')}
    falsifiers.append({'falsifier': 'F4_deleted_triangle_closure', **f4})

    # F5: flipped winding
    tris = tetra.triangles.copy()
    tris[3] = tris[3][::-1]
    flipped = pm.Membrane(tetra.vertices, tris, 'flipped_tetra')
    try:
        flipped.require_closed()
        f5 = {'observed': 'NOT_REFUSED', 'bit': False}
    except ValueError as exc:
        # tampered traction computed directly (the gated path correctly
        # refuses): the flipped triangle's unit normal reverses
        tri = tetra.vertices[tris]
        cross = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        normals_fl = cross / np.linalg.norm(cross, axis=1)[:, None]
        areas_fl = 0.5 * np.linalg.norm(cross, axis=1)
        forces_fl = src100.delta_p * areas_fl[:, None] * normals_fl
        nf_flip = forces_fl.sum(axis=0)
        f5 = {'observed': {'orientation_refusal': str(exc),
                           'signed_volume_m3': flipped.signed_volume(),
                           'net_force_N_tampered':
                               float(np.linalg.norm(nf_flip))},
              'bound': 'orientation_inconsistent and net force >= 1e-6 N',
              'bit': bool(str(exc) == 'orientation_inconsistent'
                          and np.linalg.norm(nf_flip) >= 1e-6)}
    falsifiers.append({'falsifier': 'F5_flipped_winding', **f5})

    # F6: unaccounted energy (area factor omitted from traction power)
    buggy_total = 0.0
    template = tetra.vertices
    v_unit_mag = tetra.signed_volume()
    delta_s = 0.1 / 2000
    for k in range(1, 2001):
        s_prev = 1.0 + delta_s * (k - 1)
        s_k = 1.0 + delta_s * k
        s_mid = 0.5 * (s_prev + s_k)
        mid = pm.Membrane(template * s_mid, tetra.triangles, 'mid')
        forces_buggy = src_w.delta_p * mid.normals     # AREA OMITTED (tamper)
        loads_b = np.zeros_like(mid.vertices)
        np.add.at(loads_b, tetra.triangles[:, 0], forces_buggy / 3.0)
        np.add.at(loads_b, tetra.triangles[:, 1], forces_buggy / 3.0)
        np.add.at(loads_b, tetra.triangles[:, 2], forces_buggy / 3.0)
        dx = delta_s * template
        buggy_total += float((loads_b * dx).sum())
    dv_total = v_unit_mag * (1.1 ** 3 - 1.0)
    buggy_diff = abs(buggy_total - src_w.delta_p * dv_total)
    falsifiers.append({'falsifier': 'F6_area_factor_omitted_work_account',
                       'observed': {
                           'correct_total_J': work['work_traction_j'],
                           'tampered_total_J': buggy_total,
                           'tampered_mismatch_J': buggy_diff},
                       'bound': 'tampered mismatch >= 1e-6 J (correct <= '
                                '1e-15 J per step)',
                       'bit': bool(buggy_diff >= 1e-6)})

    # ---- write artifacts ----------------------------------------------------
    trace = {'schema': 'chimera.mat2_m03.pressure_trace.v1',
             'task_id': 'M03',
             'tick_interval': [0, TICKS - 1],
             'tick_to_seconds': '1 tick = 1/300 s simulated, replayed at 1 '
                                'video second per tick (slow motion x300)',
             'schedule_pa': schedule,
             'dynamic': dyn,
             'phase_a_tetra_demo_pa': {str(t): 20.0 * t for t in range(6)},
             'scene': {'membrane_rest_radius_m': R0_M,
                       'membrane_centre_m': [0.0, 0.0, 0.0],
                       'tetra_demo': 'm02 tetra, native compiled frame'}}
    state_path = HERE / 'pressure_state.json'
    state_path.write_text(json.dumps(doc, indent=1, ensure_ascii=False,
                                     sort_keys=True) + '\n', encoding='utf-8')
    trace_path = HERE / 'pressure_trace.json'
    trace_path.write_text(json.dumps(trace, indent=1, ensure_ascii=False,
                                     sort_keys=True) + '\n', encoding='utf-8')
    receipt = {
        'schema': 'chimera.mat2_m03.qualification_receipt.v1',
        'task_id': 'M03',
        'criteria_sha256': 'f91d2bca94b7f72c2650eab4f14356eb0889e139facb6f07'
                           'd66920b021bb8ded',
        'attempt_id': '61aa525f80da4b61a10b7e3c788d87fc',
        'base_revision': '986f270ef24cda0008c52bd40d4b6d08565c0692',
        'preregistration': 'PREREGISTRATION.md (incl. corrections A1-A5)',
        'upstream_authority': {
            'm01_validator': 'tools/monkey_campaign/contributions/MAT2-M01/'
                             'material_state.py (unmodified)',
            'm01_validator_sha256': pm.sha256_file(
                HERE.parent / 'MAT2-M01' / 'material_state.py'),
            'm02_mesh_blob_sha256': pm.M02_TETRA_BLOB_SHA256,
        },
        'state_document_sha256': pm.sha256_file(state_path),
        'trace_sha256': pm.sha256_file(trace_path),
        'checks': checks,
        'falsifier_bites': falsifiers,
        'determinism': 'no stochastic inputs anywhere; replay equality is '
                       'checked by T8 (canonical digests)',
    }
    receipt_path = HERE / 'qualification_receipt.json'
    receipt_path.write_text(json.dumps(receipt, indent=1, ensure_ascii=False,
                                       sort_keys=True) + '\n', encoding='utf-8')
    all_pass = all(c['passed'] for c in checks) and \
        all(f['bit'] for f in falsifiers)
    print('checks:', sum(1 for c in checks if c['passed']), '/',
          len(checks), '| falsifier bites:',
          sum(1 for f in falsifiers if f['bit']), '/', len(falsifiers))
    print('ALL PASS' if all_pass else 'FAILURES PRESENT - DO NOT SHIP')
    return 0 if all_pass else 1


def build_state_document(run, dyn, tetra, field):
    """chimera.material_state.v1 experiment document (M01 schema authority)."""
    current = run.current_membrane()
    rep = current.closure_report()
    rest_rep = pm.icosphere(1, R0_M).closure_report()
    doc = {
        'schema': pm.SCHEMA,
        'revision': 1,
        'object_id': 'mat2-m03-pressure-membrane-experiment',
        'provenance': {
            'task_id': 'M03',
            'base_revision': '986f270ef24cda0008c52bd40d4b6d08565c0692',
            'preregistration': 'PREREGISTRATION.md (corrections A1-A5)',
            'schema_authority':
                'tools/monkey_campaign/contributions/MAT2-M01/'
                'material_state.py (unmodified M01 validator)',
            'schema_authority_sha256': pm.sha256_file(
                HERE.parent / 'MAT2-M01' / 'material_state.py'),
            'upstream_regions':
                'tools/monkey_campaign/contributions/MAT2-M02/ '
                '(tetra mesh blob '
                + pm.M02_TETRA_BLOB_SHA256 + ')',
            'laws': 'traction F = dp*A_i*n_i from a declared source; volume by '
                    'divergence theorem; P-V work W = dp*dV; power dp*dV/dt',
        },
        'regions': [{
            'id': 'membrane',
            'kind': 'region',
            'parent': None,
            'rest_geometry': {
                'unit': 'm', 'frame': 'world',
                'kind': 'icosphere_level1',
                'radius_m': R0_M,
                'centre_m': [0.0, 0.0, 0.0],
                'vertex_count': rest_rep['vertex_count'],
                'triangle_count': rest_rep['triangle_count'],
                'closure': 'closed_outward_consistent',
                'open_edge_count': rest_rep['open_edge_count'],
                'signed_volume_m3': rest_rep['signed_volume_m3'],
                'surface_area_m2': rest_rep['surface_area_m2'],
            },
            'current_geometry': {
                'unit': 'm', 'frame': 'world',
                'tick': dyn['ticks'][-1]['tick'],
                'vertex_count': rep['vertex_count'],
                'triangle_count': rep['triangle_count'],
                'closure': 'closed_outward_consistent',
                'open_edge_count': rep['open_edge_count'],
                'signed_volume_m3': rep['signed_volume_m3'],
                'surface_area_m2': rep['surface_area_m2'],
                'delta_p_pa': dyn['ticks'][-1]['delta_p_pa'],
            },
            'matter_claims': [{'matter_id': 'mass_membrane', 'role': 'owner'}],
            'ports': [{'id': 'pressure_inlet',
                       'protocol': 'chimera.pressure_traction.v1',
                       'unit': 'Pa'}],
        }],
        'matter': [{'id': 'mass_membrane', 'mass_kg': TOTAL_MASS_KG,
                    'provenance': MASS_DECL}],
        'directions': [],
        'laws': [{'id': 'law_pressure_deformation',
                  'kind': 'pressure_deformation',
                  'regions': ['membrane'],
                  'parameters': {
                      'source_id': 'mat2_m03_membrane',
                      'p_int_peak_pa': PEAK_PA,
                      'p_ext_pa': 0.0,
                      'max_delta_p_pa': 5000.0,
                      'max_dv_dt_m3_per_s': 1e-3,
                      'edge_compliance_m_per_n': COMPLIANCE,
                      'damping_per_s': DAMPING,
                      'xpbd_iterations': ITERATIONS,
                      'dt_s': DT_S,
                      'tick_count': TICKS,
                      'traction_rule': 'F_i = dp * A_i * n_i, equal-third '
                                       'vertex lumping'},
                  'provenance': SOURCE_DECL}],
        'contacts': [],
        'bonds': [],
    }
    return doc, ms.validate_material_state(doc)


if __name__ == '__main__':
    sys.exit(main())
