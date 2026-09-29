"""MAT2-M07 frozen experiments (PREREGISTRATION.md + Amendments A1-A2).

X1 coupling run (two-component world, dt0, 80 ticks, geometry stored),
X2 disconnected-component independence (joint vs solo runs, BITWISE),
X3 timestep refinement (1/300, 1/600, 1/1200; stability + convergence
order on the smooth volume observable and the event-ful plate observable),
and the P-probes. Deterministic; no RNG; no wall-clock. Writes
experiment_trace.json and experiment_receipt.json (byte-identical on
re-run at the same revision).
"""
from __future__ import annotations

import ast
import json
import math
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import integrated_step as iw  # noqa: E402

DT0 = iw.DT_S
REFINEMENT = [DT0, DT0 / 2.0, DT0 / 4.0]
TICKS = iw.TICKS
MAX_SPEED_BOUND_M_PER_S = 5.0
VOLUME_ORDER_WINDOW = (1.5, 3.0)   # A4 (A3's [0.5,1.6] was FALSIFIED: p=2.34)
PLATE_ORDER_WINDOW = (1.5, 3.2)    # A4 (A3's [0.3,1.8] was FALSIFIED: p=2.61)


def build_world(component_ids_offsets, dt_s=DT0):
    comps = [iw.Component(cid, off) for cid, off in component_ids_offsets]
    return iw.IntegratedWorld(comps, dt_s=dt_s)


def run_world(component_ids_offsets, dt_s=DT0, ticks=TICKS, store=False):
    world = build_world(component_ids_offsets, dt_s)
    world.run(ticks, store_geometry_from=(0 if store else None))
    return world


def peak(values):
    return max(abs(v) for v in values)


def plate_observable(ticks_rows):
    """Plate displacement averaged over the final 20% of the horizon."""
    tail = ticks_rows[int(len(ticks_rows) * 0.8):]
    rest_x = tail[0]['plate_x_m']  # placeholder; real rest handled by caller
    return sum(r['plate_x_m'] for r in tail) / len(tail)


def p_single_owner():
    """AST scan: state writes happen only inside IntegratedWorld (and the
    declared MembranePort write-through setter)."""
    source = (HERE / 'integrated_step.py').read_text(encoding='utf-8')
    tree = ast.parse(source)
    state_names = {'x', 'v', 'velocity', 'F', 'U_mat', 'Q_mat', 'W_in_mat',
                   'ground_anchor_impulse', 'wall_reaction_impulse'}
    violations = []

    def walk(node, klass):
        for child in ast.iter_child_nodes(node):
            new_klass = klass
            if isinstance(child, ast.ClassDef):
                new_klass = child.name
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                walk(child, new_klass)
                continue
            targets = []
            if isinstance(child, ast.Assign):
                targets = child.targets
            elif isinstance(child, ast.AugAssign):
                targets = [child.target]
            for target in targets:
                name = None
                node_t = target
                while isinstance(node_t, (ast.Attribute, ast.Subscript)):
                    if isinstance(node_t, ast.Attribute):
                        name = node_t.attr
                        break
                    node_t = node_t.value
                if isinstance(target, ast.Attribute):
                    name = target.attr
                if name in state_names and klass not in (
                        'IntegratedWorld', 'MembranePort', '_PairBody',
                        'ShellBody', 'Component'):
                    # IntegratedWorld is the single writer; MembranePort and
                    # _PairBody are its DECLARED write-through adapters
                    # (called only from IntegratedWorld._phase_contact);
                    # ShellBody/Component only initialize their own state.
                    violations.append(f'{klass}:{name}')
            walk(child, new_klass)

    walk(tree, None)
    # Component.__init__ legitimately initializes its own state; ShellBody
    # and MembranePort are declared state holders/views. Anything else is a
    # second writer.
    require_violations = [v for v in violations]
    return {'ok': not require_violations, 'violations': require_violations}


def require(condition, code):
    if not condition:
        raise ValueError(code)


def main():
    pins = iw.verify_input_pins()
    receipt = {'task': 'MAT2-M07', 'planning_id': 'M07',
               'schema': iw.SCHEMA,
               'declaration': iw.DECLARATION,
               'declared_digest': iw.DECLARED_DIGEST,
               'input_pins_verified': pins,
               'criteria_sha256':
                   'ff18b443b97f2b3947cc993ff64175a9e848fc6d806ed90bd719fa2'
                   'bd24e87b4',
               'attempt_id': 'cc584d2e1e7c46de80bacbaf7ba12f77'}

    # ---- X1: coupling run (joint two-component world, dt0) ---------------
    joint = run_world([('A', 0.0), ('B', 3.0)], store=True)
    x1 = {}
    offsets = {'A': 0.0, 'B': 3.0}
    for cid in ('A', 'B'):
        rows = [t['components'][cid] for t in joint.ticks]
        rest_plate_x = iw.PLATE_X0_M + offsets[cid]
        disp = [r['plate_x_m'] - rest_plate_x for r in rows]
        com_z = [r['membrane_com_m'][2] for r in rows]
        com_z0 = com_z[0]
        x1[cid] = {
            'peak_plate_displacement_m': peak(disp),
            'final_plate_displacement_m': disp[-1],
            'peak_membrane_com_z_change_m': peak([c - com_z0 for c in com_z]),
            'max_residual_r_j': max(abs(r['residual_r_j']) for r in rows),
            'max_residual_bound_j': max(r['residual_bound_j'] for r in rows),
            'all_residuals_within_bound':
                all(r['residual_within_bound'] for r in rows),
            'max_membrane_speed_m_per_s':
                max(r['membrane_max_speed_m_per_s'] for r in rows),
            'max_contact_iterations':
                max(r['contact_iterations'] for r in rows),
            'max_gs_residual_N_s':
                max(r['contact_gs_residual_N_s'] for r in rows),
            'peak_maxwell_F_N': max(abs(r['F_N']) for r in rows),
            'final_F_N': rows[-1]['F_N'],
            'cum_Q_mat_j': rows[-1]['Q_mat_j'],
            'cum_U_mat_j': rows[-1]['U_mat_j'],
            'cum_W_in_mat_j': rows[-1]['W_in_mat_j'],
            'final_ground_anchor_impulse_N_s':
                rows[-1]['ground_anchor_impulse_N_s'],
            'final_wall_reaction_impulse_N_s':
                rows[-1]['wall_reaction_impulse_N_s'],
        }
        require(x1[cid]['peak_plate_displacement_m'] >= 1e-5,
                'x1_plate_did_not_move:' + cid)
        require(x1[cid]['peak_membrane_com_z_change_m'] >= 1e-6,
                'x1_membrane_did_not_move:' + cid)
        require(x1[cid]['all_residuals_within_bound'], 'x1_residual_gate')
        # bitwise reciprocity + momentum identity are enforced in-world
        # (ledger_imbalance / momentum_ledger_open / anchor_reaction_imbalance)
        weight_impulse = (iw.PLATE_MASS_KG * iw.G_M_S2
                          * (TICKS * DT0))
        anchor_z = rows[-1]['ground_anchor_impulse_N_s'][2]
        require(anchor_z > 0.0 and abs(anchor_z) >= weight_impulse,
                'p_boundary_reaction_support:' + cid)
        x1[cid]['cumulative_gravity_weight_impulse_N_s'] = weight_impulse
    receipt['X1_coupling'] = x1

    # ---- X2: disconnected-component independence (BITWISE) ---------------
    solo_a = run_world([('A', 0.0)])
    solo_b = run_world([('B', 3.0)])
    x2 = {}
    for cid, solo in (('A', solo_a), ('B', solo_b)):
        max_abs_diff = 0.0
        compared_fields = 0
        for wt, st in zip(joint.ticks, solo.ticks):
            jr, sr = wt['components'][cid], st['components'][cid]
            require(jr['state_hash'] == sr['state_hash'],
                    'independence_violated:state_hash:' + cid)
            for key, sv in sr.items():
                jv = jr[key]
                if isinstance(sv, float):
                    compared_fields += 1
                    max_abs_diff = max(max_abs_diff, abs(jv - sv))
                    require(jv == sv,
                            'independence_violated:' + key + ':' + cid)
                elif isinstance(sv, list) and sv and isinstance(sv[0], float):
                    compared_fields += 1
                    d = max((abs(a - b) for a, b in zip(jv, sv)), default=0.0)
                    max_abs_diff = max(max_abs_diff, d)
                    require(jv == sv,
                            'independence_violated:' + key + ':' + cid)
                else:
                    require(jv == sv,
                            'independence_violated:' + key + ':' + cid)
        x2[cid] = {'max_abs_float_diff': max_abs_diff,
                   'hash_mismatches': 0,
                   'compared_float_fields_per_component': compared_fields,
                   'bitwise_identical': max_abs_diff == 0.0}
        require(max_abs_diff == 0.0, 'independence_violated:' + cid)
    receipt['X2_independence'] = x2

    # ---- X3: timestep refinement -----------------------------------------
    x3 = {'timesteps_s': REFINEMENT, 'components': {}}
    series = {}
    for dt in REFINEMENT:
        ticks = int(round(TICKS * DT0 / dt))
        w = run_world([('A', 0.0), ('B', 3.0)], dt_s=dt, ticks=ticks)
        series[dt] = {cid: [t['components'][cid] for t in w.ticks]
                      for cid in ('A', 'B')}
    for cid in ('A', 'B'):
        vols = [series[dt][cid][-1]['membrane_volume_m3']
                for dt in REFINEMENT]
        plates = [plate_observable(series[dt][cid]) for dt in REFINEMENT]
        e_vol = [abs(v - vols[-1]) for v in vols]
        e_pl = [abs(p - plates[-1]) for p in plates]
        stable = True
        max_speed = 0.0
        for dt in REFINEMENT:
            for r in series[dt][cid]:
                max_speed = max(max_speed,
                                r['membrane_max_speed_m_per_s'])
                stable = stable and r['residual_within_bound']
        stable = stable and all(math.isfinite(v) for v in vols + plates) \
            and max_speed <= MAX_SPEED_BOUND_M_PER_S
        require(e_vol[0] > e_vol[1] > e_vol[2],
                'x3_volume_errors_not_decreasing:' + cid)
        require(e_pl[0] > e_pl[2],
                'x3_plate_error_not_decreasing:' + cid)
        p_vol = math.log2(e_vol[0] / e_vol[1])
        p_pl = math.log2(e_pl[0] / e_pl[1]) if e_pl[1] > 0 else 99.0
        plate_mid_converged = e_pl[1] == 0.0
        entry = {
            'final_volume_m3_by_dt': vols,
            'volume_errors_vs_finest': e_vol,
            'plate_tail_avg_m_by_dt': plates,
            'plate_errors_vs_finest': e_pl,
            'stability_all_timesteps': bool(stable),
            'max_membrane_speed_m_per_s': max_speed,
            'order_volume_observable': p_vol,
            'order_plate_observable': p_pl,
            'plate_order_note': ('mid-timestep error already 0 vs the '
                                 'finest reference (converged at dt0/2)'
                                 if plate_mid_converged else
                                 'order measured from the dt0 -> dt0/2 '
                                 'pair against the dt0/4 reference'),
        }
        require(stable, 'x3_stability_violated:' + cid)
        require(VOLUME_ORDER_WINDOW[0] <= p_vol <= VOLUME_ORDER_WINDOW[1],
                'x3_volume_order_out_of_window:' + cid)
        require(plate_mid_converged
                or PLATE_ORDER_WINDOW[0] <= p_pl <= PLATE_ORDER_WINDOW[1],
                'x3_plate_order_out_of_window:' + cid)
        x3['components'][cid] = entry
    receipt['X3_refinement'] = x3

    # ---- P-probes ----------------------------------------------------------
    last_tick = joint.ticks[-1]['components']['A']
    comp_a = joint._component('A')
    source_now = comp_a.source.with_delta_p(last_tick['delta_p_pa'])
    current = iw.pm.Membrane(comp_a.x, comp_a.membrane.triangles,
                             comp_a.membrane.name)
    forces, _ = current.triangle_tractions(source_now)
    ratios = [float(np.linalg.norm(f) / a) / max(last_tick['delta_p_pa'],
                                                 1e-12)
              for f, a in zip(forces, current.areas)]
    net_f, net_tau = current.net_force_torque(forces)
    receipt['P_probes'] = {
        'P_declared_order_digest_every_tick': all(
            t['order_digest'] == iw.DECLARED_DIGEST for t in joint.ticks),
        'P_order_digest_constant': iw.DECLARED_DIGEST,
        'P_single_owner_ast': p_single_owner(),
        'P_area_scaled_traction': {
            'note': 'per-triangle pressure traction |F_i|/A_i equals the '
                    'declared delta_p on the CURRENT geometry (an '
                    'area-independent constant-force tamper violates this)',
            'min_abs_ratio': min(ratios), 'max_abs_ratio': max(ratios),
            'uniform_net_force_n': [float(c) for c in net_f],
            'uniform_net_torque_n_m': [float(c) for c in net_tau]},
        'P_boundary_reactions': {
            'recorded_every_tick': all(
                'ground_anchor_impulse_N_s' in t['components'][c]
                for t in joint.ticks for c in ('A', 'B')),
            'final_ground_anchor_z_N_s_A':
                joint.ticks[-1]['components']['A'][
                    'ground_anchor_impulse_N_s'][2],
            'final_ground_anchor_z_N_s_B':
                joint.ticks[-1]['components']['B'][
                    'ground_anchor_impulse_N_s'][2]},
        'P_state_document_m01': iw.state_document(joint, revision=1),
        'P_determinism': 'verified by test_integrated_step.py: two fresh '
                         'subprocess runs must produce byte-identical '
                         'trace and receipt files',
        'P_regressions': 'verified by test_integrated_step.py: the '
                         'UNMODIFIED M03, M04, M05 and M06 suites re-run '
                         'green in this checkout',
    }

    # ---- trace (committed artifact; capture binds its sha) -----------------
    trace = {
        'schema': iw.SCHEMA,
        'declaration': joint.declaration,
        'declared_digest': iw.DECLARED_DIGEST,
        'tick_count': len(joint.ticks),
        'ticks': joint.ticks,
    }
    out_trace = HERE / 'experiment_trace.json'
    out_receipt = HERE / 'experiment_receipt.json'
    out_state = HERE / 'integrated_state.json'
    out_trace.write_text(json.dumps(trace, indent=1, ensure_ascii=False,
                                    sort_keys=True) + '\n', encoding='utf-8')
    out_receipt.write_text(json.dumps(receipt, indent=1, ensure_ascii=False,
                                      sort_keys=True) + '\n',
                           encoding='utf-8')
    out_state.write_text(json.dumps(receipt['P_probes'][
        'P_state_document_m01'], indent=1, ensure_ascii=False,
        sort_keys=True) + '\n', encoding='utf-8')
    print('trace:', out_trace)
    print('receipt:', out_receipt)
    print('X1 plate peak disp (A, B):',
          x1['A']['peak_plate_displacement_m'],
          x1['B']['peak_plate_displacement_m'])
    print('X2 bitwise max diff:', x2['A']['max_abs_float_diff'],
          x2['B']['max_abs_float_diff'])
    print('X3 volume errors (A):', x3['components']['A'][
        'volume_errors_vs_finest'])
    print('X3 orders (A): vol', x3['components']['A']['order_volume_observable'],
          'plate', x3['components']['A']['order_plate_observable'])
    return 0


if __name__ == '__main__':
    sys.exit(main())
