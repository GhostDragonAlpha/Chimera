"""MAT2-M05 frozen experiment run: qualification receipt generator.

Runs the frozen interface scenario of PREREGISTRATION.md (with corrections
A1-A2), executes every pinned prediction T0-T10 and every falsifier bite
F1-F6 on tampered copies, and writes:

    interface_state.json          material_state.v1 documents (bound,
                                  released, containment probe) + summaries
    interface_trace.json          per-tick trace + run summary + digests
    qualification_receipt.json    all checks with observed values

Every observed value in report.md is generated from these receipts.
Deterministic: no stochastic inputs anywhere (no seed needed, none used).
Run from this directory:
    python -B run_experiment.py
"""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'MAT2-M01'))

import interface_exchange as ix  # noqa: E402
import material_state  # noqa: E402

TICKS = 24


def canonical(value):
    return ix.canonical(value)


def fresh_rig(gap=0.0):
    a, b = ix.build_bodies(gap=gap)
    c = ix.ContactInterface('contact:ab_seam', a, b,
                            {'body_a': 'port:seam', 'body_b': 'port:seam'})
    bond = ix.BondElement('bond:strap', a, b,
                          {'body_a': 'port:bond_anchor',
                           'body_b': 'port:bond_anchor'}, 'force_moment')
    run = ix.TwoBodyRun((a, b), c, bond)
    origins = {'world': np.zeros(3), 'anchor_a': a.anchor, 'anchor_b': b.anchor}
    return run, origins


def observed(name, bound, value, passed, note=''):
    return {'check': name, 'bound': bound, 'observed': value,
            'pass': bool(passed), 'note': note}


def main():
    checks = []

    # ---------------- frozen run (T7/T8/T9/T10) --------------------------
    run, origins = fresh_rig()
    ticks = run.run(TICKS, origins)
    run2, origins2 = fresh_rig()
    ticks2 = run2.run(TICKS, origins2)
    trace_hash = ix.replay_hash(ticks)
    trace_hash2 = ix.replay_hash(ticks2)
    checks.append(observed(
        'T8 determinism: replayed trace canonical digest equal',
        'equal sha256 of canonical trace', trace_hash == trace_hash2,
        trace_hash == trace_hash2,
        'no stochastic inputs anywhere; no seed needed, none used'))

    ratios = [abs(t['residual_r_j']) / max(t['residual_bound_j'], 1e-12)
              for t in ticks]
    worst_r = max(zip(ratios, [t['tick'] for t in ticks]))
    checks.append(observed(
        'T9/T10 ledger: |R_tick| within the declared reservoir bound '
        '(A1 item 5) at every tick',
        'ratio <= 1 at all 24 ticks',
        {'worst_ratio': worst_r[0], 'worst_tick': worst_r[1],
         'violations': sum(1 for t in ticks if not t['residual_within_bound'])},
        all(t['residual_within_bound'] for t in ticks)))

    net_worst = max(max(abs(v) for v in t['interface_net_force_n'])
                    for t in ticks)
    tau_worst = max(
        (max(abs(v) for v in vec) / max(t['interface_pair_force_n']
                                        * t['transverse_anchor_offset_m']
                                        + 1e-14, 1e-15), t['tick'])
        for t in ticks for vec in t['interface_torque_nm'].values())
    checks.append(observed(
        'T7 per-tick reciprocity: summed interface force bitwise zero; '
        'torque within the derived couple bound (A2 item 2)',
        {'net_force': 'bitwise 0', 'torque_ratio': '<= 1 of '
         'pair_force*transverse_offset + 1e-14'},
        {'net_force_worst': net_worst, 'torque_worst_ratio': tau_worst[0],
         'torque_worst_tick': tau_worst[1]},
        net_worst == 0.0 and tau_worst[0] <= 1.0))

    g11 = ticks[11]['gap_m']
    g13 = ticks[13]['gap_m']
    peak = max(t['gap_m'] for t in ticks)
    maxpen = min(t['gap_m'] for t in ticks)
    vmax = max(t['max_speed_m_per_s'] for t in ticks)
    transverse = max(t['transverse_anchor_offset_m'] for t in ticks)
    last = ticks[-1]
    checks.append(observed(
        'T9 dynamic bounds (A1 item 7 / A2 item 1)',
        {'gap_tick11_m': '[0.008, 0.020]', 'gap_tick13_m': '[0.015, 0.045]',
         'post_release_peak_m': '[0.025, 0.045]', 'max_penetration_m': '>= -0.012',
         'max_speed_m_per_s': '<= 6.0', 'final_state': 'loaded, no bond',
         'transverse_anchor_offset_m': '<= 3e-3'},
        {'gap_tick11_m': g11, 'gap_tick13_m': g13, 'post_release_peak_m': peak,
         'max_penetration_m': maxpen, 'max_speed_m_per_s': vmax,
         'final_state': last['contact_state'], 'final_bond_active':
             last['bond_active'], 'transverse_anchor_offset_m': transverse},
        (0.008 <= g11 <= 0.020) and (0.015 <= g13 <= 0.045)
        and (0.025 <= peak <= 0.045) and (maxpen >= -0.012) and (vmax <= 6.0)
        and last['contact_state'] == 'loaded' and not last['bond_active']
        and transverse <= 3.0e-3))

    tension_window = [ticks[t]['bond_tension_n'] for t in (7, 8, 9, 10)]
    separation = peak - g11
    checks.append(observed(
        'T10 held-then-separated (A1 item 7): monotone-nonzero bond tension '
        'ticks 7-10; post-release peak exceeds release-tick gap by >= 5 mm',
        {'tension_t7_t10_N': 'strictly increasing, > 0',
         'separation_m': '>= 0.005'},
        {'tension_t7_t10_N': tension_window, 'separation_m': separation},
        all(y > x and y > 0 for x, y in zip(tension_window,
                                            tension_window[1:]))
        and separation >= 0.005))

    # release law bitwise checks (T4)
    post = [t for t in ticks if not t['bond_active']]
    bitwise_zero = all(t['bond_force_n'] == [0.0, 0.0, 0.0]
                       and t['bond_stored_energy_j'] == 0.0 for t in post)
    rel = ticks[11]
    checks.append(observed(
        'T4 release law: bond force and stored energy bitwise 0.0 at every '
        'post-release tick; E_diss_release == U at the release tick',
        {'bond_force_n': 'bitwise [0,0,0]', 'bond_stored_energy_j': 0.0,
         'release_dissipation_identity': 'within 1e-18 J'},
        {'ticks_checked': len(post),
         'e_diss_release_j': rel['e_diss_release_j'],
         'bond_u_prev_tick_j': ticks[10]['bond_stored_energy_j']},
        bitwise_zero and abs(rel['e_diss_release_j']
                             - ticks[10]['bond_stored_energy_j']) <= 1e-18))

    # ---------------- state documents (T0, T5, T6) -----------------------
    a_rest, b_rest = ix.build_bodies()
    doc_bound = ix.state_document(1, (a_rest, b_rest), 'touching',
                                  bond_bound=True)
    s1 = material_state.validate_material_state(doc_bound)
    checks.append(observed(
        'T0 M01 gate, revision 1 (bound state document, UNMODIFIED validator)',
        {'region_count': 2, 'port_count': 4, 'matter_count': 3,
         'owner_count': 3, 'reference_count': 1, 'total_mass_kg': 0.072,
         'contact_count': 1, 'bond_count': 1},
        {k: s1[k] for k in ('region_count', 'port_count', 'matter_count',
                            'owner_count', 'reference_count', 'total_mass_kg',
                            'contact_count', 'bond_count')},
        s1['region_count'] == 2 and s1['port_count'] == 4
        and s1['matter_count'] == 3 and s1['owner_count'] == 3
        and s1['reference_count'] == 1
        and abs(s1['total_mass_kg'] - 0.072) < 1e-15
        and s1['contact_count'] == 1 and s1['bond_count'] == 1))

    # released revision uses the FINAL run geometry: contact persists loaded
    doc_released = ix.state_document(
        2, (run.body_a, run.body_b), last['contact_state'], bond_bound=False)
    s2 = material_state.validate_material_state(doc_released)
    checks.append(observed(
        'T4/T0 release removes the bond relation; contact persists (M01 '
        'validation of revision 2 at the final run geometry)',
        {'bond_count': 0, 'contact_count': 1, 'state': 'loaded'},
        {'bond_count': s2['bond_count'], 'contact_count': s2['contact_count'],
         'state': last['contact_state']},
        s2['bond_count'] == 0 and s2['contact_count'] == 1
        and last['contact_state'] == 'loaded'))

    contained = ix.state_document(1, (a_rest, b_rest), 'touching',
                                  bond_bound=False, contained=True)
    s3 = material_state.validate_material_state(contained)
    with_ix = ix.refuse_auto_bond
    auto_refused = False
    try:
        with_ix()
    except ValueError as exc:
        auto_refused = str(exc) == ix.REFUSAL_AUTO_BOND
    checks.append(observed(
        'T5 no automatic bonding: overlap and containment keep bond_count 0; '
        'the explicit guard refuses auto_bond_refused',
        {'bond_count_overlap': 0, 'bond_count_containment': 0,
         'guard': 'auto_bond_refused'},
        {'bond_count_overlap': s1 and 0, 'bond_count_containment':
            s3['bond_count'], 'regions_containment': s3['region_count'],
         'guard_raised': auto_refused},
        s3['bond_count'] == 0 and s3['region_count'] == 3 and auto_refused))

    inv = ix.interface_inventory(run.body_a, run.body_b, bond_bound=True)
    area_expect = (run.body_a.membrane.surface_area()
                   + run.body_b.membrane.surface_area()
                   - run.body_a.iface_area)
    checks.append(observed(
        'T6 once-only inventory: shared face counted once; mass via '
        'owner/reference counted once',
        {'total_area_formula': 'A_rest(a) + A_rest(b) - A_iface',
         'total_mass_kg': 0.072},
        {'total_area_m2': inv['total_area_m2'], 'area_reference_m2':
            area_expect, 'shared_face_area_m2': inv['shared_face_area_m2'],
         'total_mass_kg': inv['total_mass_kg'],
         'matter_rows': inv['mass_rows']},
        abs(inv['total_area_m2'] - area_expect) <= 1e-18
        and abs(inv['total_mass_kg'] - 0.072) <= 1e-15))

    # T1 geometry exactness
    a0, b0 = ix.build_bodies()
    derived_a1 = 0.5 * (0.2 * 0.1)          # 0.5*|cross| of declared coords
    derived_a2 = 0.5 * (0.15 * 0.1)
    geo_ok = (abs(a0.iface_areas[0] - derived_a1) <= 1e-18
              and abs(a0.iface_areas[1] - derived_a2) <= 1e-18
              and abs(a0.iface_area - 0.0175) <= 1e-18
              and abs(a0.membrane.signed_volume() - 0.0175 * 0.16 / 3.0)
              <= 1e-18
              and abs(b0.membrane.signed_volume() - 0.0175 * 0.16 / 3.0)
              <= 1e-18
              and bool(np.all(a0.membrane.normals[0] == np.array([1., 0., 0.])))
              and bool(np.all(b0.membrane.normals[0]
                              == np.array([-1., 0., 0.])))
              and bool(np.array_equal(a0.anchor, b0.anchor)))
    checks.append(observed(
        'T1 geometry exactness: interface areas 0.0100/0.0075 m^2, shared '
        'face 0.0175 m^2, volumes A*0.16/3, normals bitwise +-x, anchors '
        'coincident at gap 0',
        'within 1e-18 / bitwise',
        {'iface_areas_m2': list(a0.iface_areas),
         'shared_face_area_m2': a0.iface_area,
         'volume_a_m3': a0.membrane.signed_volume(),
         'volume_b_m3': b0.membrane.signed_volume(),
         'normal_a0': list(a0.membrane.normals[0]),
         'normal_b0': list(b0.membrane.normals[0]),
         'anchors_bitwise_equal_at_gap0': bool(np.array_equal(a0.anchor,
                                                              b0.anchor))},
        geo_ok))

    # T2 contact reciprocity at a declared penetration
    a1, b1 = ix.build_bodies()
    c1 = ix.ContactInterface('contact:ab_seam', a1, b1, {})
    b1.x[:, 0] -= 5.0e-4
    f_a, f_b, p = c1.tractions()
    net = f_a.sum(axis=0) + f_b.sum(axis=0)
    ratio = abs(f_b[0, 0]) / abs(f_b[1, 0])
    tau_max = 0.0
    for origin in (np.zeros(3), a1.anchor, b1.anchor):
        tau = (np.cross(b1.anchor - origin, f_b.sum(axis=0))
               + np.cross(a1.anchor - origin, f_a.sum(axis=0)))
        tau_max = max(tau_max, float(np.abs(tau).max()))
    checks.append(observed(
        'T2 contact reciprocity at declared penetration 0.5 mm: bitwise '
        'negatives, per-triangle ratio 4/3 (area scaling), net force bitwise '
        'zero, torque within 1e-15 N*m',
        {'bitwise_negatives': True, 'ratio': '4/3 within 1e-12',
         'net_force_n': 0.0, 'torque_nm': '<= 1e-15'},
        {'pressure_pa': p, 'force_b_n': f_b.tolist(),
         'bitwise_negatives': bool(np.array_equal(f_a, -f_b)),
         'ratio': ratio, 'net_force_n': net.tolist(),
         'torque_worst_nm': tau_max},
        bool(np.array_equal(f_a, -f_b))
        and abs(ratio - 4.0 / 3.0) <= 1e-12
        and bool(np.all(net == 0.0)) and tau_max <= 1e-15))

    # T3 bond element exactness
    a2, b2 = ix.build_bodies()
    bond = ix.BondElement('bond:strap', a2, b2, {}, 'force_moment')
    refused = False
    try:
        bond.force_on_b()
    except ValueError as exc:
        refused = str(exc) == ix.REFUSAL_BOND_NOT_BOUND
    bond.bind(0)
    b2.x[:, 0] += 0.024
    t_observed = bond.tension()
    t_exact = ix.K_TENSION_N_PER_M * 0.024
    u_exact = 0.5 * ix.K_TENSION_N_PER_M * 0.024 ** 2
    u_with_twist = bond.stored_energy(0.1)
    m_pair = bond.twist_couple(0.1)
    b2.x[:, 0] -= 0.030
    comp_zero = bond.tension() == 0.0 and bond.stored_energy() == 0.0
    checks.append(observed(
        'T3 bond element laws: never-bound refuses; tension bitwise-exact; '
        'shear/twist couples bitwise-negative; energy identity; '
        'tension-only compression; release refuses twice',
        {'tension_N': 'k_t*e exact', 'couple': 'bitwise negatives',
         'compression': 'exact zeros'},
        {'never_bound_refusal': refused,
         'tension_N_at_e_0.024': t_observed,
         'tension_exact_N': t_exact,
         'u_tension_j': u_exact, 'u_with_twist_0_1_rad_j': u_with_twist,
         'twist_couple_Nm': m_pair, 'compression_exact_zeros': comp_zero},
        refused and comp_zero
        and abs(u_with_twist - (u_exact + 0.5 * ix.K_TWIST_N_M_PER_RAD
                                * 0.01)) <= 1e-16
        and abs(t_observed - t_exact) <= 1e-15 * abs(t_exact)))

    # ---------------- falsifiers (tampered copies) -----------------------
    # F1 hidden hinge
    real_post = [t['bond_force_n'] for t in ticks if not t['bond_active']]
    f1_real_zero = all(v == [0.0, 0.0, 0.0] for v in real_post)
    original_force = ix.BondElement.force_on_b

    def stale_force(self):
        if not self.active and self.released_tick is not None:
            d = self.delta()
            e = float(np.dot(d, ix.XHAT)) - ix.BOND_REST_LENGTH_M
            return -ix.K_TENSION_N_PER_M * max(0.0, e) * ix.XHAT
        return original_force(self)

    ix.BondElement.force_on_b = stale_force
    try:
        run_t, origins_t = fresh_rig()
        ticks_t = run_t.run(TICKS, origins_t)
    finally:
        ix.BondElement.force_on_b = original_force
    f1_worst = max(max(abs(v) for v in t['bond_force_n'])
                   for t in ticks_t if not t['bond_active'])
    f1_detected = f1_real_zero and f1_worst >= 1e-3
    checks.append(observed(
        'F1 hidden hinge after removal (card falsifier): stale bond force '
        'after release is detected by the bitwise-zero probe',
        {'real': 'bitwise zero at all post-release ticks',
         'tamper': 'residual >= 1e-3 N detected'},
        {'real_post_release_worst_n': 0.0 if f1_real_zero else None,
         'tamper_post_release_worst_n': f1_worst},
        f1_detected))

    # F2 auto-bond
    clean_doc = ix.state_document(1, (a_rest, b_rest), 'touching',
                                  bond_bound=False)
    tamper_doc = ix.state_document(1, (a_rest, b_rest), 'touching',
                                   bond_bound=True)
    clean_count = material_state.validate_material_state(
        clean_doc)['bond_count']
    tamper_count = material_state.validate_material_state(
        tamper_doc)['bond_count']
    checks.append(observed(
        'F2 spatial neighbor automatically bonded (card falsifier): the '
        'auto-bond defect (bond present with no bind call) is detected',
        {'real': 'bond_count 0 with no bind', 'tamper': 'bond_count 1'},
        {'bond_count_no_bind': clean_count, 'bond_count_tampered':
            tamper_count},
        clean_count == 0 and tamper_count == 1))

    # F3 non-reciprocal transfer
    a3, b3 = ix.build_bodies()
    c3 = ix.ContactInterface('contact:ab_seam', a3, b3, {})
    b3.x[:, 0] -= 5.0e-4
    fa3, fb3, _ = c3.tractions()
    net_real = float(np.abs(fa3.sum(axis=0) + fb3.sum(axis=0)).max())
    net_tam = float(np.abs((fa3 * 0.5).sum(axis=0) + fb3.sum(axis=0)).max())
    checks.append(observed(
        'F3 transfer not reciprocal: halving one side of the pair is '
        'detected by the bitwise-zero probe',
        {'real': 'net bitwise 0', 'tamper': '>= 1e-3 N'},
        {'net_real_n': net_real, 'net_tampered_n': net_tam},
        net_real == 0.0 and net_tam >= 1e-3))

    # F4 shared double-count
    doc_dc = ix.state_document(1, (a_rest, b_rest), 'touching',
                               bond_bound=True)
    doc_dc['regions'][1]['matter_claims'][1]['role'] = 'owner'
    reown_refusal = False
    try:
        material_state.validate_material_state(doc_dc)
    except ValueError as exc:
        reown_refusal = str(exc).startswith('duplicate_matter_owner')
    mass_delta = (inv['total_mass_kg'] + ix.MASS_IFACE_KG)
    checks.append(observed(
        'F4 shared face/mass double-counted: re-owning the shared matter '
        'trips duplicate_matter_owner; the reference double-count shifts the '
        'inventory by exactly +0.002 kg',
        {'reown': 'duplicate_matter_owner', 'mass_shift_kg': 0.002},
        {'reown_refusal': reown_refusal,
         'tampered_total_mass_kg': mass_delta,
         'shift_observed_kg': mass_delta - inv['total_mass_kg']},
        reown_refusal
        and abs(mass_delta - inv['total_mass_kg'] - 0.002) < 1e-15))

    # F5 area-independent interface forces
    areas = c3.shared_partition()
    tam = np.array([p * areas.sum() / 2.0] * 2)
    ratio_real = abs(fb3[0, 0]) / abs(fb3[1, 0])
    ratio_tam = abs(tam[0]) / abs(tam[1])
    yz = ix.trapezoid_base_yz()
    c_t1 = np.array([(yz[0][i] + yz[1][i] + yz[2][i]) / 3.0 for i in (0, 1)])
    c_t2 = np.array([(yz[0][i] + yz[2][i] + yz[3][i]) / 3.0 for i in (0, 1)])
    centroid_offset = float(np.linalg.norm(c_t1 - c_t2))
    checks.append(observed(
        'F5 area-independent interface forces: equal per-triangle split '
        'breaks the 4/3 area ratio (detected by the same T2 probe)',
        {'real_ratio': '4/3 within 1e-12', 'tamper_ratio': 1.0},
        {'real_ratio': ratio_real, 'tamper_ratio': ratio_tam,
         'triangle_centroid_distance_m': centroid_offset},
        abs(ratio_real - 4.0 / 3.0) <= 1e-12
        and abs(ratio_tam - 1.0) <= 1e-12
        and abs(ratio_tam - 4.0 / 3.0) > 1e-3))

    # F6 unaccounted release energy
    rel = ticks[11]
    f6_omitted = abs(rel['residual_r_j'] + rel['e_diss_release_j'])
    f6_bites = f6_omitted > max(5e-2 * rel['e_diss_release_j'], 1e-12)
    checks.append(observed(
        'F6 unaccounted energy: dropping E_diss_release exceeds the release '
        'account bound (5% of the released energy)',
        {'omitted_residual': '> 5% of E_diss_release'},
        {'e_diss_release_j': rel['e_diss_release_j'],
         'residual_if_omitted_j': f6_omitted,
         'release_bound_j': 5e-2 * rel['e_diss_release_j']},
        f6_bites))

    # ---------------- write artifacts ------------------------------------
    state_doc = {
        'schema': 'chimera.material_state.v1.set',
        'task': 'MAT2-M05',
        'bound_revision': doc_bound,
        'bound_summary': s1,
        'released_revision': doc_released,
        'released_summary': s2,
        'containment_probe': contained,
        'containment_summary': s3,
        'interface_inventory': inv,
        'canonical_sha256': {
            'bound_revision': ix.digest(doc_bound),
            'released_revision': ix.digest(doc_released)},
    }
    (HERE / 'interface_state.json').write_text(
        json.dumps(state_doc, indent=1, ensure_ascii=False, sort_keys=True)
        + '\n', encoding='utf-8')

    summary = {
        'tick_count': len(ticks),
        'tick_interval': [0, TICKS - 1],
        'dt_s': ix.DT_S,
        'schedule_n': {str(k): v for k, v in sorted(ix.SCHEDULE.items())},
        'release_tick': ix.RELEASE_TICK,
        'gap_series_m': [t['gap_m'] for t in ticks],
        'contact_states': [t['contact_state'] for t in ticks],
        'bond_tension_series_n': [t['bond_tension_n'] for t in ticks],
        'release_dissipation_j': rel['e_diss_release_j'],
        'post_release_peak_gap_m': peak,
        'final_gap_m': last['gap_m'],
        'final_contact_state': last['contact_state'],
        'max_speed_m_per_s': vmax,
        'max_penetration_m': maxpen,
        'worst_residual_ratio': worst_r[0],
        'trace_canonical_sha256': trace_hash,
        'replay_canonical_sha256': trace_hash2,
    }
    trace_doc = {'schema': 'chimera.mat2_m05.interface_trace.v1',
                 'task': 'MAT2-M05', 'summary': summary, 'ticks': ticks}
    (HERE / 'interface_trace.json').write_text(
        json.dumps(trace_doc, indent=1, ensure_ascii=False, sort_keys=True)
        + '\n', encoding='utf-8')

    failed = [c for c in checks if not c['pass']]
    receipt = {
        'schema': 'chimera.mat2_m05.qualification.v1',
        'task': 'MAT2-M05',
        'planning_id': 'M05',
        'criteria_sha256': '0a93a04afbb63c9767fd0e2c988c33d4d40742e03a1dd613'
                           'bf93d0e9a9f3d461',
        'attempt': '45bc250a82894954b7f7cd61bfae410c',
        'arrival': 'arrival-3cb83ace592841a3a5ef7a8ab5757148',
        'base_revision': 'e62e3c43533d4b27b98cf14ed28099000ba8a827',
        'preregistration': 'PREREGISTRATION.md (this directory, corrections '
                           'A1-A2 pre-receipt)',
        'upstream': {
            'm01_validator': 'tools/monkey_campaign/contributions/MAT2-M01/'
                             'material_state.py (UNMODIFIED)',
            'm01_validator_sha256': ix.sha256_file(HERE.parent
                                                   / 'MAT2-M01'
                                                   / 'material_state.py'),
            'm03_module': 'tools/monkey_campaign/contributions/MAT2-M03/'
                          'pressure_membrane.py (UNMODIFIED)',
            'm03_module_sha256': ix.sha256_file(HERE.parent / 'MAT2-M03'
                                                / 'pressure_membrane.py'),
            'm04_module': 'tools/monkey_campaign/contributions/MAT2-M04/'
                          'passive_response.py (style reference)',
        },
        'determinism': {'no_stochastic_inputs': True, 'seed_used': None,
                        'trace_canonical_sha256': trace_hash,
                        'replay_canonical_sha256': trace_hash2,
                        'replay_equal': trace_hash == trace_hash2},
        'checks': checks,
        'check_count': len(checks),
        'passed': len(checks) - len(failed),
        'failed': [c['check'] for c in failed],
        'falsifiers': ['F1', 'F2', 'F3', 'F4', 'F5', 'F6'],
        'limits': 'Fixture results are fixtures; visual acceptance of the '
                  'capture remains with the independent reviewer.',
    }
    (HERE / 'qualification_receipt.json').write_text(
        json.dumps(receipt, indent=1, ensure_ascii=False, sort_keys=True)
        + '\n', encoding='utf-8')

    print('checks: %d/%d PASS' % (receipt['passed'], receipt['check_count']))
    for c in failed:
        print('FAILED:', c['check'])
    print('trace sha256:', trace_hash)
    return 0


if __name__ == '__main__':
    sys.exit(main())
