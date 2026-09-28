"""MAT2-M04 experiments: E1 load-extension, E2 relaxation, E3 rotated fiber.

Runs the three preregistered experiments of PREREGISTRATION.md on the exact
candidate revision and emits:

- experiment_trace.json   : per-tick solver states (E2 and protocol V) with
                            canonical per-state hashes (the capture binds to
                            this file);
- experiment_receipt.json : frozen-limit verdicts, oracle residuals and
                            content-derived hashes. NO wall-clock, NO RNG.

E1 is quasi-static (closed-form elastic oracle), E2 is position-controlled
(ramp + hold through the exact exponential Maxwell integrator), E3 is the
rotated-fiber directional gate. Protocol V (visual motion, force ramp) is
recorded here so the capture consumes solver output only.

CPU-only, stdlib-only, deterministic.
"""
from __future__ import annotations

import hashlib
import json
import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'MAT2-M01'))

import material_state as ms  # noqa: E402  (M01, unmodified; pin re-check)
import passive_law as pl  # noqa: E402
import passive_response as pr  # noqa: E402
import author_laws as al  # noqa: E402  (pins + emission, deterministic)

E1_LOADS_N = (25.0, 50.0, 100.0, 250.0)
E2_V = 0.01           # m/s ramp rate
E2_X_TARGET = 0.002   # m
E2_DT = 0.1           # s tick
E2_RAMP_TICKS = 2     # 0.2 s
E2_HOLD_TICKS = 10    # 1.0 s -> t_end 1.2 s
V_RATE = 100.0        # N/s protocol V force ramp
V_DT = 0.1
V_TICKS = 12


def require(ok, code):
    if not ok:
        raise ValueError(code)


def close(a, b, rel=1e-9):
    return abs(a - b) <= rel * max(abs(a), abs(b), 1e-300)


def law_parts():
    arm_doc, indep_doc, directions_doc, display = al.emit()
    gauge = indep_doc['gauges'][0]
    profiles = {p['id']: p for p in indep_doc['profiles']}
    directions = {d['id']: d for d in indep_doc['directions']}
    tetra_assignment = next(a for a in indep_doc['assignments']
                            if a['region_id'] == 'tetra')
    return (arm_doc, indep_doc, directions_doc, display, gauge, profiles,
            directions, tetra_assignment)


def direction_from_axis(axis):
    return {'axis': list(axis)}


# ------------------------------------------------------------------- E1
def run_E1(gauge, profiles, directions):
    loads = list(E1_LOADS_N)
    cases = {
        'rigid': None,
        'compliant_maxwell': None,
        'fiber_0': directions['fiber_tetra_0']['axis'],
        'fiber_45': directions['fiber_tetra_45']['axis'],
        'fiber_90': directions['fiber_tetra_90']['axis'],
    }
    frozen = {
        'rigid': [0.0, 0.0, 0.0, 0.0],
        'compliant_maxwell': [0.001, 0.002, 0.004, 0.01],
        'fiber_0': [0.00025, 0.0005, 0.001, 0.0025],
        'fiber_45': [0.0004, 0.0008, 0.0016, 0.004],
        'fiber_90': [0.001, 0.002, 0.004, 0.01],
    }
    rows, verdicts = [], []
    for name, axis in cases.items():
        profile = 'fiber_reinforced' if name.startswith('fiber_') else name
        dir_row = direction_from_axis(axis) if axis else None
        xs, ks = [], []
        for F in loads:
            x, k = pr.extension_from_law(profiles[profile], gauge, dir_row, F)
            xs.append(x)
            ks.append(k)
            require(close(x, frozen[name][loads.index(F)], 1e-9),
                    'E1_closed_form_mismatch:%s:%r' % (name, F))
        # linearity x(2F) == 2x(F) bitwise on consecutive doubling pairs
        for i in range(len(loads) - 1):
            if loads[i + 1] == 2.0 * loads[i]:
                require(xs[i + 1] == 2.0 * xs[i],
                        'E1_linearity_bitwise:%s' % name)
        rows.append({'case': name, 'profile': profile,
                     'loads_N': loads, 'x_m': xs, 'k_N_per_m': ks})
        verdicts.append('P3:%s green' % name)
    # rigid transmission + ordering across profiles at every load
    for F in loads:
        require(pr.transmit_force_rigid(F) == F, 'E1_rigid_transmission')
    for i, F in enumerate(loads):
        by_name = {r['case']: r['x_m'][i] for r in rows}
        require(by_name['rigid'] == 0.0, 'E1_rigid_zero')
        require(by_name['rigid'] < by_name['fiber_0']
                < by_name['fiber_45'] < by_name['fiber_90'],
                'E1_ordering:%r' % F)
        require(abs(by_name['fiber_90'] - by_name['compliant_maxwell'])
                <= 1e-12, 'E1_fiber90_equals_compliant:%r' % F)
    verdicts.append('P3:ordering+rigid green')
    return {'experiment': 'E1_load_extension', 'loads_N': loads,
            'cases': rows, 'verdicts': verdicts}


# ------------------------------------------------------------------- E2
def run_E2(gauge, profiles):
    k = profiles['compliant_maxwell']['parameters']['k_N_per_m']
    c = profiles['compliant_maxwell']['parameters']['c_N_s_per_m']
    tau = profiles['compliant_maxwell']['parameters']['tau_s']
    band = profiles['compliant_maxwell']['valid_strain_range']
    state = pr.new_state()
    for _ in range(E2_RAMP_TICKS):
        pr.step_position_controlled(state, E2_V, E2_DT, k, c, 0.1, band)
    for _ in range(E2_HOLD_TICKS):
        pr.step_position_controlled(state, 0.0, E2_DT, k, c, 0.1, band)
    rows = state['rows']
    t_ramp = E2_RAMP_TICKS * E2_DT
    t_end = (E2_RAMP_TICKS + E2_HOLD_TICKS) * E2_DT

    F_ramp_cf = c * E2_V * (1.0 - math.exp(-t_ramp / tau))
    F_end_cf = F_ramp_cf * math.exp(-(t_end - t_ramp) / tau)
    W_cf = c * E2_V ** 2 * (t_ramp - tau * (1.0 - math.exp(-t_ramp / tau)))
    U_ramp_cf = F_ramp_cf ** 2 / (2.0 * k)
    U_end_cf = F_end_cf ** 2 / (2.0 * k)
    Q_cf = W_cf - U_end_cf
    Q_ramp_cf = c * E2_V ** 2 * (t_ramp - 2.0 * tau * (1.0 - math.exp(
        -t_ramp / tau)) + 0.5 * tau * (1.0 - math.exp(-2.0 * t_ramp / tau)))
    Q_hold_cf = F_ramp_cf ** 2 * tau * (1.0 - math.exp(
        -2.0 * (t_end - t_ramp) / tau)) / (2.0 * c)

    ramp_end = rows[E2_RAMP_TICKS - 1]
    last = rows[-1]
    require(close(ramp_end['F_N'], F_ramp_cf), 'E2_ramp_force_mismatch')
    require(close(last['F_N'], F_end_cf), 'E2_hold_force_mismatch')
    require(close(last['W_J'], W_cf), 'E2_work_mismatch')
    require(close(ramp_end['U_J'], U_ramp_cf), 'E2_U_ramp_mismatch')
    require(close(last['U_J'], U_end_cf), 'E2_U_end_mismatch')
    require(close(last['Q_J'], Q_cf, 1e-9), 'E2_Q_mismatch')
    require(close(Q_ramp_cf + Q_hold_cf, Q_cf, 1e-9),
            'E2_Q_integral_mismatch')
    # monotone strict decay through the hold
    for i in range(E2_RAMP_TICKS, len(rows) - 1):
        require(rows[i + 1]['F_N'] < rows[i]['F_N'], 'E2_not_monotone')
    # x target reached (position-controlled; nominal 0.002 m)
    require(close(last['x_m'], E2_X_TARGET, 1e-12), 'E2_x_target')
    ledger = pr.check_ledger(last['W_J'], last['U_J'], last['Q_J'])
    return {'experiment': 'E2_relaxation', 'tick_interval': [1, len(rows)],
            'dt_s': E2_DT, 'k_N_per_m': k, 'c_N_s_per_m': c, 'tau_s': tau,
            'closed_form': {'F_ramp_N': F_ramp_cf, 'F_end_N': F_end_cf,
                            'W_J': W_cf, 'U_ramp_J': U_ramp_cf,
                            'U_end_J': U_end_cf, 'Q_J': Q_cf,
                            'Q_ramp_J': Q_ramp_cf, 'Q_hold_J': Q_hold_cf},
            'solver': {'F_ramp_N': ramp_end['F_N'], 'F_end_N': last['F_N'],
                       'W_J': last['W_J'], 'U_ramp_J': ramp_end['U_J'],
                       'U_end_J': last['U_J'], 'Q_J': last['Q_J'],
                       'x_end_m': last['x_m']},
            'ledger': ledger,
            'rows': rows,
            'verdicts': ['P4 green', 'P6 green']}


# ------------------------------------------------------------------- E3
def run_E3(gauge, profiles, directions):
    F = 50.0
    frozen = {'fiber_tetra_0': 0.0005, 'fiber_tetra_45': 0.0008,
              'fiber_tetra_90': 0.002}
    rows, xs = [], {}
    E45_cf = pr.effective_modulus(profiles['fiber_reinforced']['parameters']
                                  ['E_fiber_Pa'],
                                  profiles['fiber_reinforced']['parameters']
                                  ['E_trans_Pa'], math.radians(45.0))
    require(E45_cf == 1.25e6, 'E3_E45_closed_form')
    for did, x_expect in frozen.items():
        x, k = pr.extension_from_law(profiles['fiber_reinforced'], gauge,
                                     directions[did], F)
        require(close(x, x_expect), 'E3_closed_form_mismatch:' + did)
        xs[did] = x
        rows.append({'direction_id': did,
                     'axis': directions[did]['axis'], 'F_N': F,
                     'x_m': x, 'k_N_per_m': k})
    require(xs['fiber_tetra_0'] < xs['fiber_tetra_45'] < xs['fiber_tetra_90'],
            'E3_ordering')
    ratio = xs['fiber_tetra_90'] / xs['fiber_tetra_0']
    require(close(ratio, 4.0), 'E3_ratio_mismatch')
    # symmetry x(+theta) == x(-theta) bitwise
    neg45 = {'axis': [directions['fiber_tetra_45']['axis'][0],
                      -directions['fiber_tetra_45']['axis'][1],
                      directions['fiber_tetra_45']['axis'][2]]}
    x_neg, _ = pr.extension_from_law(profiles['fiber_reinforced'], gauge,
                                     neg45, F)
    require(x_neg == xs['fiber_tetra_45'], 'E3_symmetry_bitwise')
    # rotating the LOAD by theta with fixed fiber == rotating the fiber
    rotated_gauge = {'axis': [math.cos(math.radians(45.0)),
                              math.sin(math.radians(45.0)), 0.0],
                     'rest_length_m': gauge['rest_length_m'],
                     'area_m2': gauge['area_m2']}
    x_rot, _ = pr.extension_from_law(profiles['fiber_reinforced'],
                                     rotated_gauge,
                                     directions['fiber_tetra_0'], F)
    require(x_rot == xs['fiber_tetra_45'], 'E3_frame_equivariance_bitwise')
    return {'experiment': 'E3_rotated_fiber', 'load_N': F,
            'E45_Pa': E45_cf, 'ratio_90_over_0': ratio, 'cases': rows,
            'verdicts': ['P5 green']}


# ------------------------------------------------- interface area oracle
def run_interface(blob):
    areas = []
    tris = blob['regions']['plate']['triangles']
    verts = blob['regions']['plate']['world_vertices_m']
    for tri in tris:
        p = [verts[i] for i in tri]
        a = [p[1][k] - p[0][k] for k in range(3)]
        b = [p[2][k] - p[0][k] for k in range(3)]
        cross = [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
                 a[0] * b[1] - a[1] * b[0]]
        areas.append(0.5 * math.sqrt(sum(cc * cc for cc in cross)))
        require(abs(areas[-1] - 0.01) < 1e-12,
                'plate_triangle_area_mismatch:%r' % areas[-1])
    equal = pr.triangle_force_shares(areas, 50.0)
    require(equal['shares_N'] == [25.0, 25.0], 'P7_equal_shares')
    require(equal['sum_bitwise_exact'] is True, 'P7_sum_bitwise')
    twin = pr.triangle_force_shares([0.02, 0.01], 50.0)
    require(close(twin['shares_N'][0], 100.0 / 3.0)
            and close(twin['shares_N'][1], 50.0 / 3.0), 'P7_twin_shares')
    require(close(twin['summed_N'], 50.0, 1e-12), 'P7_twin_sum')
    refused = False
    try:
        pr.triangle_force_shares([0.01, 0.0], 50.0)
    except ValueError as err:
        refused = 'zero_area_interface' in str(err)
    require(refused, 'P7_zero_area_refusal_missing')
    return {'experiment': 'interface_area_scaling', 'load_N': 50.0,
            'pinned_triangle_areas_m2': areas, 'equal': equal,
            'twin': twin,
            'verdicts': ['P7 green']}


# ------------------------------------------------------------ protocol V
def run_protocol_V(gauge, profiles, directions):
    """Solver-driven motion for the capture: force ramp 100 N/s, 12 ticks."""
    k_comp = profiles['compliant_maxwell']['parameters']['k_N_per_m']
    c_comp = profiles['compliant_maxwell']['parameters']['c_N_s_per_m']
    band = profiles['compliant_maxwell']['valid_strain_range']
    columns = {}
    state = pr.new_state()
    for _ in range(V_TICKS):
        pr.step_force_ramp(state, V_RATE, V_DT, k_comp, c_comp, 0.1, band)
    columns['compliant_maxwell'] = state['rows']
    for name, did in (('fiber_0', 'fiber_tetra_0'),
                      ('fiber_45', 'fiber_tetra_45'),
                      ('fiber_90', 'fiber_tetra_90')):
        k_theta = None
        x = 0.0
        rows = []
        for i in range(1, V_TICKS + 1):
            F = V_RATE * i * V_DT
            dir_row = direction_from_axis(directions[did]['axis'])
            x, k_theta = pr.extension_from_law(
                profiles['fiber_reinforced'], gauge, dir_row, F)
            rows.append({'tick': i, 't': i * V_DT, 'x_m': x, 'F_N': F,
                         'k_N_per_m': k_theta})
        columns[name] = rows
    columns['rigid'] = [{'tick': i, 't': i * V_DT, 'x_m': 0.0,
                         'F_N': V_RATE * i * V_DT}
                        for i in range(1, V_TICKS + 1)]
    frozen_last = {'rigid': 0.0, 'compliant_maxwell': 0.01632,
                   'fiber_0': 0.0012, 'fiber_45': 0.00192,
                   'fiber_90': 0.0048}
    for name, x_expect in frozen_last.items():
        require(close(columns[name][-1]['x_m'], x_expect),
                'PV_closed_form_mismatch:' + name)
    eps_final = columns['compliant_maxwell'][-1]['x_m'] / 0.1
    require(-0.30 <= eps_final <= 0.30, 'PV_strain_band')
    return {'experiment': 'protocol_V_force_ramp', 'rate_N_per_s': V_RATE,
            'dt_s': V_DT, 'tick_interval': [1, V_TICKS],
            'final_strain': eps_final, 'columns': columns,
            'verdicts': ['PV frozen limits green']}


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def main():
    (arm_doc, indep_doc, directions_doc, display, gauge, profiles,
     directions, tetra_assignment) = law_parts()
    arm, indep, blob, blob_raw = al.load_inputs()

    e1 = run_E1(gauge, profiles, directions)
    e2 = run_E2(gauge, profiles)
    e3 = run_E3(gauge, profiles, directions)
    iface = run_interface(blob)
    pv = run_protocol_V(gauge, profiles, directions)

    # rest-state + strain-gate probes (P9), executed here on the exact inputs
    x0, _ = pr.extension_from_law(profiles['compliant_maxwell'], gauge,
                                  None, 0.0)
    require(x0 == 0.0, 'P9_rest_extension')
    refused = False
    try:
        pr.extension_from_law(profiles['compliant_maxwell'], gauge, None,
                              1.0e4)
    except ValueError as err:
        refused = 'outside_valid_strain_range' in str(err)
    require(refused, 'P9_strain_gate_refusal_missing')
    p9 = {'zero_load_extension_m': x0,
          'over_band_load_N': 1.0e4,
          'over_band_refusal': 'outside_valid_strain_range'}

    trace = {
        'schema': 'chimera.passive_response_trace.v1',
        'task_id': 'M04',
        'attempt': '262e9d2a30ae4c4b82d84de7de9661a1',
        'base_revision': '986f270ef24cda0008c52bd40d4b6d08565c0692',
        'preregistration': 'PREREGISTRATION.md (frozen before measurement)',
        'experiments': {'E1': e1, 'E2': e2, 'E3': e3, 'interface': iface},
        'protocol_V': pv,
        'rest_state_and_strain_gate': p9,
        'state_hashes': {
            'E2_trace_sha256': ms.digest(canonical(e2['rows'])),
            'protocol_V_trace_sha256': ms.digest(canonical(pv['columns'])),
        },
        'subject_binding': {
            'formula': 'sha256(canonical({arm_laws, indep_laws, '
                       'directions_doc, pinned M02 docs}))',
            'arm_laws_sha256': pl.digest(pl.canonical(arm_doc)),
            'indep_laws_sha256': pl.digest(pl.canonical(indep_doc)),
            'directions_doc_sha256': ms.digest(ms.canonical(directions_doc)),
            'm02_arm_canonical': al.PIN_ARM_CANONICAL,
            'm02_indep_canonical': al.PIN_INDEP_CANONICAL,
            'm02_blob_sha256': al.PIN_BLOB_SHA256,
        },
    }
    subject_components = [trace['subject_binding']['arm_laws_sha256'],
                          trace['subject_binding']['indep_laws_sha256'],
                          trace['subject_binding']['directions_doc_sha256'],
                          al.PIN_ARM_CANONICAL, al.PIN_INDEP_CANONICAL,
                          al.PIN_BLOB_SHA256,
                          trace['state_hashes']['E2_trace_sha256'],
                          trace['state_hashes']['protocol_V_trace_sha256']]
    subject_sha = ms.digest(canonical(subject_components))
    trace['subject_sha256'] = subject_sha

    receipt = {
        'schema': 'chimera.passive_response_receipt.v1',
        'task_id': 'M04',
        'attempt': '262e9d2a30ae4c4b82d84de7de9661a1',
        'criteria_sha256':
            'e9faa5bcb3926b2cdcd68f110c2c9480bb7b7d18e40a2623beb5ff5ce978a665',
        'base_revision': '986f270ef24cda0008c52bd40d4b6d08565c0692',
        'subject_sha256': subject_sha,
        'trace_sha256': ms.digest(canonical(trace)),
        'experiments': {
            'E1': {'verdicts': e1['verdicts'],
                   'cases': [{k: v for k, v in c.items()}
                             for c in e1['cases']]},
            'E2': {'verdicts': e2['verdicts'], 'closed_form': e2['closed_form'],
                   'solver': e2['solver'], 'ledger': e2['ledger']},
            'E3': {'verdicts': e3['verdicts'], 'ratio_90_over_0':
                   e3['ratio_90_over_0'], 'E45_Pa': e3['E45_Pa'],
                   'cases': e3['cases']},
            'interface': {'verdicts': iface['verdicts'],
                          'equal': iface['equal'], 'twin': iface['twin']},
            'protocol_V': {'verdicts': pv['verdicts'],
                           'final_strain': pv['final_strain'],
                           'final_x_m': {name: rows[-1]['x_m'] for name, rows
                                         in pv['columns'].items()}},
            'P9': p9,
        },
        'all_frozen_limits_met': True,
    }

    (HERE / 'experiment_trace.json').write_text(
        json.dumps(trace, indent=1, ensure_ascii=False) + '\n',
        encoding='utf-8')
    (HERE / 'experiment_receipt.json').write_text(
        json.dumps(receipt, indent=1, ensure_ascii=False) + '\n',
        encoding='utf-8')
    print('E1', e1['verdicts'])
    print('E2', e2['verdicts'], 'F_end %.12f N' % e2['solver']['F_end_N'],
          'ledger residual %.3e J' % e2['ledger']['residual_J'])
    print('E3', e3['verdicts'], 'ratio %.12f' % e3['ratio_90_over_0'])
    print('interface', iface['verdicts'])
    print('protocol V', pv['verdicts'], 'final strain', pv['final_strain'])
    print('subject_sha256', subject_sha)
    print('trace_sha256', receipt['trace_sha256'])


if __name__ == '__main__':
    main()
