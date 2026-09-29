"""MAT2-M06 experiments: X0/S1 candidate-vs-exhaustive, X1 resting load,
X2 oblique contact, X3 finite sliding, X4 crossing trajectories, P7 area
scaling, refusal probes.

Runs the frozen PREREGISTRATION.md (Amendments A1-A3) experiments on the
exact candidate revision and emits:

- experiment_trace.json   : per-tick solver states (X1/X3/X4) with per-tick
                            canonical hashes (the capture binds to this file);
- experiment_receipt.json : frozen-limit verdicts, observed values, control
                            arms, refusal probes and content-derived hashes.
                            NO wall-clock, NO RNG outside the declared LCG.

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

import author_contact as ac  # noqa: E402
import local_contact as lc  # noqa: E402

G = lc.G
DT = lc.DT
V0_SLIDE = 0.5
VN_OBLIQUE = 0.25
VT_OBLIQUE = 0.4330127018922193
CLOSING_X4 = 2.0
X4_VARIANTS = ((0.0, 0.0), (0.005, 0.0), (0.0, -0.005), (0.004, 0.004),
               (-0.006, -0.002))
X1_TICKS = 600
X1_STEADY_FROM = 500
X3_MAX_TICKS = 200
X3_REST_TICKS = 50
X4_TICKS = 20


def require(ok, code):
    if not ok:
        raise ValueError(code)


def close(a, b, rel=1e-9, abl=0.0):
    return abs(a - b) <= max(rel * max(abs(a), abs(b)), abl)


def canonical(obj):
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(',', ':'),
                   ensure_ascii=True).encode('utf-8')).hexdigest()


def contact_set(records):
    return sorted((r['pair_key'], r['kind']) for r in records)


def contact_pairs(records):
    return sorted(r['pair_key'] for r in records)


# ---------- X0: candidate-vs-exhaustive on pinned compiled geometry ----------

def x0_independent_shapes():
    """Static snapshot of the pinned tetra+plate in their compiled poses."""
    blob = ac.load_blob()
    tetra = blob['regions']['tetra']
    plate = blob['regions']['plate']
    n_pairs = len(tetra['triangles']) * len(plate['triangles'])
    bodies = [
        lc.Body('tetra', 'tetra', 'mass_tetra', 0.12, 0.6, 0.4, lc.THICKNESS_M,
                tetra['world_vertices_m'], tetra['triangles']),
        lc.Body('plate', 'plate', 'mass_plate', 0.02, 0.7, 0.5, lc.THICKNESS_M,
                plate['world_vertices_m'], plate['triangles'], pinned=True),
    ]
    rec_p, led_p = lc.solve_tick(bodies, exhaustive=False, gravity=False)
    bodies2 = [
        lc.Body('tetra', 'tetra', 'mass_tetra', 0.12, 0.6, 0.4, lc.THICKNESS_M,
                tetra['world_vertices_m'], tetra['triangles']),
        lc.Body('plate', 'plate', 'mass_plate', 0.02, 0.7, 0.5, lc.THICKNESS_M,
                plate['world_vertices_m'], plate['triangles'], pinned=True),
    ]
    rec_e, led_e = lc.solve_tick(bodies2, exhaustive=True, gravity=False)
    require(contact_set(rec_p) == contact_set(rec_e), 'exhaustive_mismatch')
    ids = {r['surface_a'] for r in rec_p} | {r['surface_b'] for r in rec_p}
    return {
        'fixture': 'independent-shape tetra+plate, compiled default poses',
        'cross_body_pairs_exhaustive': n_pairs,
        'candidates_pruned_run': len(led_p['cand_set']),
        'candidates_exhaustive': len(led_e['cand_set']),
        'contacts': len(rec_p),
        'contact_set_identical': True,
        'surface_ids_used': sorted(ids),
        'recall': 1.0,
    }


def x0_tetra_drop():
    """The pinned tetra mesh (identity lists, declared rigid placement offset)
    dropped onto the support plate: contact rows over the pinned vocabulary
    {tetra, plate}; candidate-vs-exhaustive on the 8 cross pairs."""
    blob = ac.load_blob()
    tetra = blob['regions']['tetra']
    off = (-0.35, 0.065, 0.0687)  # declared fixture placement: tetra bottom
    # face 0.012 m above the plate midsurface -> initial gap 0.010 m
    verts = [tuple(v[i] + off[i] for i in range(3))
             for v in tetra['world_vertices_m']]
    z_bottom = min(v[2] for v in verts)
    require(abs(z_bottom - 0.012) <= 1e-12, 'tetra_placement_gap_wrong')

    def fresh():
        return [lc.Body('tetra', 'tetra', 'mass_tetra', 0.12, 0.6, 0.4,
                        lc.THICKNESS_M, verts, tetra['triangles']),
                ac.make_plate(pinned=True)]
    bodies = fresh()
    rec_p, led_p = [], None
    for _ in range(30):
        rec_p, led_p = lc.solve_tick(bodies)
        if rec_p:
            break
    require(rec_p, 'no_tetra_contact')
    bodies2 = fresh()
    rec_e, led_e = [], None
    for _ in range(30):
        rec_e, led_e = lc.solve_tick(bodies2, exhaustive=True)
        if rec_e:
            break
    require(rec_e, 'no_tetra_contact_exhaustive')
    require(contact_set(rec_p) == contact_set(rec_e), 'exhaustive_mismatch')
    ids = {r['surface_a'] for r in rec_p} | {r['surface_b'] for r in rec_p}
    require(ids == {'tetra', 'plate'}, 'surface_vocabulary_wrong')
    for r in rec_p:
        require(r['pair_key'] in led_p['cand_keys'], 'contact_not_in_candidates')
    return {
        'fixture': 'pinned tetra mesh (identity triangle lists, declared '
                   'placement offset %r) dropped onto the support plate' % (off,),
        'cross_body_pairs_exhaustive':
            len(tetra['triangles']) * 2,
        'candidates_pruned_run': len(led_p['cand_set']),
        'candidates_exhaustive': len(led_e['cand_set']),
        'contacts': len(rec_p),
        'contact_set_identical': True,
        'surface_ids_used': sorted(ids),
        'recall': 1.0,
    }


def x0_sternum_clavicle():
    """Complete exhaustive comparison on the declared small compiled pair."""
    blob = ac.load_blob()

    def fresh():
        out = []
        for rid in ('sternum', 'clavicle'):
            r = blob['regions'][rid]
            out.append(lc.Body(rid, rid, 'mass_' + rid, 0.01, 0.6, 0.4,
                               lc.THICKNESS_M, r['world_vertices_m'],
                               r['triangles']))
        return out
    bodies = fresh()
    rec_p, led_p = lc.solve_tick(bodies, exhaustive=False, gravity=False)
    bodies2 = fresh()
    rec_e, led_e = lc.solve_tick(bodies2, exhaustive=True, gravity=False)
    require(contact_set(rec_p) == contact_set(rec_e), 'exhaustive_mismatch')
    return {
        'fixture': 'sternum x clavicle (declared small compiled pair)',
        'triangles': sum(len(b.triangles) for b in bodies),
        'exhaustive_pairs': len(bodies[0].triangles) * len(bodies[1].triangles),
        'candidates_pruned_run': len(led_p['cand_set']),
        'candidates_exhaustive': len(led_e['cand_set']),
        'contacts': len(rec_p),
        'contact_set_identical': True,
        'recall': 1.0,
    }


def x0_full_arm_counts():
    """Full compiled arm: candidate search runs; counts + internal subset
    property recorded (complete exhaustive comparison out of small-fixture
    scope per Amendment A1)."""
    blob = ac.load_blob()
    arm_ids = ('clavicle', 'hand', 'humerus', 'radius', 'scapula', 'sternum',
               'ulna')
    bodies = ac.bodies_from_compiled(arm_ids)
    tris = sum(len(b.triangles) for b in bodies)
    rec, led = lc.solve_tick(bodies, exhaustive=False, gravity=False)
    cand = led['cand_keys']
    for r in rec:
        require(r['pair_key'] in cand, 'contact_not_in_candidates')
    return {
        'fixture': 'full compiled 7-region arm',
        'triangles': tris,
        'candidate_pair_count': len(cand),
        'contacts': len(rec),
        'contacts_subset_of_candidates': True,
    }


# ---------- S1: seeded randomized recall sweep ----------

def s1_random_sweep():
    scenes = []
    for k in range(32):
        bodies = ac.random_scene(k)
        misses = 0
        cand_counts = []
        contacts = 0
        for tick in range(3):
            # snapshot the PRE-tick state so the exhaustive reference solves
            # exactly the same state as the pruned run
            snap = [(b.velocity, [tuple(v) for v in b.vertices])
                    for b in bodies]
            rec_p, led_p = lc.solve_tick(bodies, exhaustive=False)
            cand = led_p['cand_keys']
            cand_counts.append(len(cand))
            contacts += len(rec_p)
            for r in rec_p:
                if r['pair_key'] not in cand:
                    misses += 1
                require(r['pair_key'] in cand, 'contact_not_in_candidates')
            bodies_e = ac.random_scene(k)
            for b_e, (vel, verts) in zip(bodies_e, snap):
                b_e.velocity = vel
                b_e.vertices = verts
            rec_e, _ = lc.solve_tick(bodies_e, exhaustive=True)
            require(contact_set(rec_p) == contact_set(rec_e),
                    'exhaustive_mismatch_scene_%d_tick_%d' % (k, tick))
        scenes.append({
            'scene': k, 'seed': ac.SEED_BASE + k,
            'candidate_counts': cand_counts, 'contacts': contacts,
            'missed': misses, 'recall': 1.0 if misses == 0 else 0.0,
        })
        require(misses == 0, 'candidate_missed_contact_scene_%d' % k)
    return {
        'scenes': scenes,
        'scene_count': len(scenes),
        'seed_base': ac.SEED_BASE,
        'total_missed': sum(s['missed'] for s in scenes),
        'recall_min': min(s['recall'] for s in scenes),
        'total_contacts': contacts,
    }


# ---------- X1: resting load ----------

def x1_resting():
    bodies = [ac.make_block(0.012), ac.make_plate(pinned=True)]
    trace = []
    steady_jn = []
    steady_forces = []
    steady_gap = []
    steady_anchor = []
    impact_tick = None
    settle_tick = None
    for tick in range(X1_TICKS):
        rec, led = lc.solve_tick(bodies)
        jn = sum(r['jn_Ns'] for r in rec
                 if {r['body_a'], r['body_b']} == {'block', 'plate'})
        block = bodies[0]
        gaps = [r['gap_m'] for r in rec]
        entry = {
            'tick': tick, 'block_z': block.vertices[0][2],
            'block_vz': block.velocity[2], 'jn_total_Ns': jn,
            'contacts': len(rec),
            'kinds': sorted({r['kind'] for r in rec}),
            'min_gap_m': min(gaps) if gaps else None,
            'ledger_residual_max': max(lc.vlen(led['residual'][b.id])
                                       for b in bodies),
            'reciprocity_residual': lc.vlen(led['reciprocity_residual']),
        }
        if jn > 0.0 and impact_tick is None:
            impact_tick = tick
        if impact_tick is not None and settle_tick is None and \
                close(jn, ac.MASS_BLOCK * G * DT, rel=1e-12):
            settle_tick = tick
        if tick >= X1_STEADY_FROM:
            steady_jn.append(jn)
            steady_gap.append(entry['min_gap_m'])
            steady_anchor.append(lc.vlen(bodies[1].anchor))
            forces = lc.area_split(bodies, rec).get('plate', {})
            steady_forces.append(forces)
        trace.append(entry)
    require(impact_tick is not None, 'no_resting_contact')
    weight = ac.MASS_BLOCK * G
    jn_ss = sum(steady_jn) / len(steady_jn)
    support = jn_ss / DT
    require(close(support, weight, rel=1e-9), 'weight_not_supported')
    f0 = steady_forces[0]
    require(set(f0) == {'0', '1'}, 'unexpected_support_triangles')
    require(abs(f0['0'] - f0['1']) <= 1e-12, 'area_split_not_equal')
    require(close(f0['0'], weight / 2.0, rel=1e-9), 'per_triangle_force_wrong')
    require(max(f['0'] for f in steady_forces) - min(f['0'] for f in steady_forces)
            <= 1e-12, 'support_unsteady')
    require(max(-g for g in steady_gap if g is not None) <= 1e-4,
            'steady_penetration_exceeded')
    anchor_mean = sum(steady_anchor) / len(steady_anchor)
    require(close(anchor_mean, weight * DT, rel=1e-12), 'anchor_not_weight')
    resid_max = max(t['ledger_residual_max'] for t in trace)
    require(resid_max <= 1e-12, 'ledger_imbalance')
    return {
        'impact_tick': impact_tick, 'settle_tick': settle_tick,
        'weight_N': weight, 'jn_steady_Ns': jn_ss,
        'support_force_N': support,
        'per_triangle_forces_N': {'0': f0['0'], '1': f0['1']},
        'steady_min_gap_m': min(steady_gap),
        'anchor_impulse_Ns_mean': anchor_mean,
        'anchor_is_weight_dt': close(anchor_mean, weight * DT, rel=1e-12),
        'ledger_residual_max': resid_max,
        'ticks': X1_TICKS, 'steady_from': X1_STEADY_FROM,
    }, trace


# ---------- X2: oblique contact ----------

def x2_oblique():
    bodies = [ac.make_block(0.012, vel=(VT_OBLIQUE, 0.0, -VN_OBLIQUE)),
              ac.make_plate(pinned=True)]
    impact = None
    trace = []
    for tick in range(40):
        rec, led = lc.solve_tick(bodies, gravity=False)
        block = bodies[0]
        rv = block.velocity
        entry = {'tick': tick, 'contacts': len(rec),
                 'vx': rv[0], 'vz': rv[2],
                 'jn': sum(r['jn_Ns'] for r in rec),
                 'jt': sum(r['jt_Ns'] for r in rec),
                 'kinds': sorted({r['kind'] for r in rec})}
        if rec and impact is None:
            impact = (tick, rec[0])
            entry['impact'] = True
        trace.append(entry)
        if impact and tick > impact[0] + 2:
            break
    require(impact is not None, 'no_oblique_contact')
    tick, rec0 = impact
    n = tuple(rec0['normal'])
    require(close(abs(n[2]), 1.0, rel=0, abl=1e-9) and abs(n[0]) <= 1e-9
            and abs(n[1]) <= 1e-9, 'oblique_normal_wrong')
    block = bodies[0]
    require(abs(block.velocity[2]) <= 1e-12, 'normal_velocity_not_arrested')
    require(close(block.velocity[0], VT_OBLIQUE - 0.1, rel=1e-9),
            'oblique_tangential_wrong')
    slip_required = ac.MASS_BLOCK * VT_OBLIQUE
    cone_cap = lc.pair_mu(bodies[0], bodies[1])[1] * rec0['jn_Ns']
    mu_s = lc.pair_mu(bodies[0], bodies[1])[0]
    require(slip_required > mu_s * rec0['jn_Ns'], 'slip_regime_wrong')
    require(rec0['jt_Ns'] <= cone_cap * (1.0 + 1e-12), 'friction_cone_violated')
    ratio = rec0['jt_Ns'] / rec0['jn_Ns']
    require(close(ratio, lc.pair_mu(bodies[0], bodies[1])[1], rel=1e-12),
            'slip_ratio_wrong')
    return {
        'impact_tick': tick, 'normal': list(n),
        'vn_after': block.velocity[2], 'vt_after': block.velocity[0],
        'jn_impact_Ns': rec0['jn_Ns'], 'jt_impact_Ns': rec0['jt_Ns'],
        'jt_over_jn': ratio, 'mu_k_pair': cone_cap / rec0['jn_Ns'],
        'slip_required_stop_Ns': slip_required,
        'mu_s_cap_Ns': mu_s * rec0['jn_Ns'],
        'slip_regime': slip_required > mu_s * rec0['jn_Ns'],
    }, trace


# ---------- X3: finite sliding ----------

def x3_sliding():
    bodies = [ac.make_block(0.002, x=-0.05, vel=(V0_SLIDE, 0.0, 0.0)),
              ac.make_plate(pinned=True)]
    block = bodies[0]
    x_start = block.vertices[0][0]
    trace = []
    stop_tick = None
    w_f_ke = 0.0
    w_force_path = 0.0
    ke_loss = 0.0
    v_prev = V0_SLIDE
    steady_jn = []
    for tick in range(X3_MAX_TICKS):
        rec, led = lc.solve_tick(bodies)
        vx = block.velocity[0]
        jn = sum(r['jn_Ns'] for r in rec
                 if {r['body_a'], r['body_b']} == {'block', 'plate'})
        jt = sum(r['jt_Ns'] for r in rec)
        mode = sorted({r['mode'] for r in rec if r['jt_Ns'] > 0.0})
        ds = vx * DT
        ke_loss += 0.5 * ac.MASS_BLOCK * (v_prev * v_prev - vx * vx)
        for r in rec:
            w_f_ke += r['w_f_ke_J']
            if r['jt_Ns'] > 0.0 and r['mode'] == 'slip':
                w_force_path += lc.pair_mu(bodies[0], bodies[1])[1] * \
                    r['jn_Ns'] * ds
        v_prev = vx
        gaps = [r['gap_m'] for r in rec]
        entry = {'tick': tick, 'block_x': block.vertices[0][0], 'vx': vx,
                 'jn_total_Ns': jn, 'jt_total_Ns': jt, 'modes': mode,
                 'ds_m': ds, 'contacts': len(rec),
                 'min_gap_m': min(gaps) if gaps else None,
                 'ledger_residual_max': max(lc.vlen(led['residual'][b.id])
                                            for b in bodies)}
        trace.append(entry)
        if stop_tick is None and abs(vx) <= 1e-12 and tick > 0 and \
                any(r['jn_Ns'] > 0.0 for r in rec):
            stop_tick = tick
        if stop_tick is not None:
            steady_jn.append(jn)
            if tick >= stop_tick + X3_REST_TICKS:
                break
    require(stop_tick is not None, 'block_never_stopped')
    d = block.vertices[0][0] - x_start
    d_oracle = V0_SLIDE * V0_SLIDE / (2.0 * 0.4 * G)
    require(abs(d - d_oracle) <= V0_SLIDE * DT, 'sliding_distance_wrong')
    require(close(w_f_ke, 0.5 * ac.MASS_BLOCK * V0_SLIDE ** 2, rel=0, abl=1e-9),
            'friction_work_ke_wrong')
    require(abs((ke_loss - w_f_ke) - w_force_path) <= 1e-3,
            'force_path_work_slack_exceeded')
    require(all(t['ds_m'] <= V0_SLIDE * DT + 1e-12 for t in trace),
            'sliding_not_finite')
    jn_ss = sum(steady_jn) / len(steady_jn)
    require(close(jn_ss, ac.MASS_BLOCK * G * DT, rel=1e-12),
            'resting_jn_not_steady')
    require(all(t['ledger_residual_max'] <= 1e-12 for t in trace),
            'ledger_imbalance')
    return {
        'stop_tick': stop_tick, 'distance_m': d, 'distance_oracle_m': d_oracle,
        'distance_error_m': abs(d - d_oracle),
        'w_f_ke_J': w_f_ke, 'ke_loss_J': ke_loss,
        'w_force_path_J': w_force_path,
        'work_slack_J': abs((ke_loss - w_f_ke) - w_force_path),
        'jn_steady_Ns': jn_ss, 'ds_max_m': max(t['ds_m'] for t in trace),
        'v0': V0_SLIDE, 'mu_k': 0.4,
    }, trace


# ---------- X4: crossing trajectories ----------

def x4_crossing():
    variants = []
    controls = []
    trace_first = None
    for vi, (ox, oy) in enumerate(X4_VARIANTS):
        a, b = ac.make_shells(0.04, offset=(ox, oy), closing=CLOSING_X4)
        impact = None
        ticks = []
        for tick in range(X4_TICKS):
            rec, led = lc.solve_tick(bodies=[a, b], gravity=False)
            entry = {
                'tick': tick, 'za': a.vertices[0][2], 'zb': b.vertices[0][2],
                'va': list(a.velocity), 'vb': list(b.velocity),
                'contacts': len(rec),
                'kinds': sorted({r['kind'] for r in rec}),
                'min_gap_m': min((r['gap_m'] for r in rec), default=None),
                'momentum_z': ac.MASS_SHELL * (a.velocity[2] + b.velocity[2]),
            }
            if rec and impact is None:
                impact = (tick, [r for r in rec if r['kind'] == 'ccd'])
                entry['impact'] = True
            ticks.append(entry)
            if impact and tick > impact[0] + 3:
                break
        require(impact is not None, 'crossing_missed_variant_%d' % vi)
        imp_tick, ccd_recs = impact
        jn_recs = [r for r in ccd_recs if r['jn_Ns'] > 0.0]
        require(len(jn_recs) == 1, 'unexpected_impulse_count_variant_%d' % vi)
        require(jn_recs[0]['gap_m'] > 0.0,
                'ccd_detected_after_overlap_variant_%d' % vi)
        require(abs(a.velocity[2]) <= 1e-12 and abs(b.velocity[2]) <= 1e-12,
                'post_impact_velocity_not_zero_variant_%d' % vi)
        post_gaps = [t['min_gap_m'] for t in ticks[imp_tick:]
                     if t['min_gap_m'] is not None]
        require(min(post_gaps) >= -1e-5, 'post_penetration_variant_%d' % vi)
        mom = max(abs(t['momentum_z']) for t in ticks)
        require(mom <= 1e-12, 'momentum_not_conserved_variant_%d' % vi)
        variants.append({
            'variant': vi, 'offset': [ox, oy], 'impact_tick': imp_tick,
            'toc': jn_recs[0]['toc'], 'gap_at_detection': jn_recs[0]['gap_m'],
            'jn_Ns': jn_recs[0]['jn_Ns'],
            'va_after': list(a.velocity), 'vb_after': list(b.velocity),
            'min_post_gap_m': min(post_gaps),
            'max_momentum_residual': mom,
        })
        if vi == 0 and trace_first is None:
            trace_first = ticks
        # declared negative control: CCD disabled on an identical fresh copy
        c, d = ac.make_shells(0.04, offset=(ox, oy), closing=CLOSING_X4)
        detected = None
        max_speed = 0.0
        for tick in range(X4_TICKS):
            rec, led = lc.solve_tick(bodies=[c, d], gravity=False,
                                     ccd_enabled=False)
            gaps = [r['gap_m'] for r in rec]
            if rec and detected is None:
                detected = (tick, min(gaps))
            max_speed = max(max_speed, lc.vlen(c.velocity), lc.vlen(d.velocity))
        controls.append({
            'variant': vi,
            'detected_tick': None if detected is None else detected[0],
            'gap_at_detection_m': None if detected is None else detected[1],
            'detected_after_mid_surface_overlap':
                detected is None or detected[1] < 0.0,
            'final_zc': c.vertices[0][2], 'final_zd': d.vertices[0][2],
            'final_zc_minus_zd': c.vertices[0][2] - d.vertices[0][2],
            'max_speed_after_control_contact': max_speed,
        })
    return {
        'closing_speed_each': CLOSING_X4,
        'per_tick_approach_m': 2 * CLOSING_X4 * DT,
        'thickness_each_m': lc.THICKNESS_M,
        'variants': variants, 'controls': controls,
        'all_detected_before_overlap': all(
            v['gap_at_detection'] > 0.0 for v in variants),
        'all_controls_late_or_missed': all(
            c['detected_after_mid_surface_overlap'] for c in controls),
    }, trace_first


# ---------- P7: area scaling ----------

def p7_area_scaling():
    bodies = [ac.make_block(0.002, x=-0.05), ac.make_plate(pinned=True)]
    for _ in range(200):
        rec, led = lc.solve_tick(bodies)
    forces = lc.area_split(bodies, rec).get('plate', {})
    require(set(forces) == {'0', '1'}, 'unexpected_p7_support')
    require(abs(forces['0'] - forces['1']) <= 1e-12, 'equal_areas_not_equal')
    twin = [ac.make_block(0.002, x=-0.05),
            ac.make_plate(pinned=True, twin=True)]
    for _ in range(200):
        rec_t, led_t = lc.solve_tick(twin)
    forces_t = lc.area_split(twin, rec_t).get('plate', {})
    require(set(forces_t) == {'0', '1'}, 'unexpected_p7_twin_support')
    ratio = forces_t['1'] / forces_t['0']
    require(close(ratio, 2.0, rel=1e-12), 'area_ratio_wrong')
    require(close(sum(forces_t.values()), ac.MASS_BLOCK * G, rel=1e-9),
            'twin_weight_not_supported')
    try:
        lc.Body('bad', 'bad', 'm', 0.1, 0.5, 0.4, lc.THICKNESS_M,
                [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (2.0, 0.0, 0.0)],
                [(0, 1, 2)])
        raised = None
    except ValueError as err:
        raised = str(err)
    require(raised == 'zero_area_interface', 'zero_area_not_refused')
    return {
        'equal_area_forces_N': {'0': forces['0'], '1': forces['1']},
        'equal_abs_diff': abs(forces['0'] - forces['1']),
        'twin_forces_N': {'0': forces_t['0'], '1': forces_t['1']},
        'twin_ratio': ratio,
        'twin_support_total_N': sum(forces_t.values()),
        'zero_area_refusal': raised,
    }


# ---------- refusal probes ----------

def refusal_probes():
    out = {}
    try:
        lc.validate_local_contact(
            {'schema': lc.SCHEMA, 'revision': 1,
             'declarations': dict(lc.DECL_KEYS),
             'surfaces': [{'id': 'plate', 'matter_id': 'm', 'thickness_m': 0.002,
                           'mu_s': 0.7, 'mu_k': 0.5}],
             'contacts': [{'surface_a': 'ghost', 'surface_b': 'plate',
                           'gap_m': 0.0}]},
            {'plate'})
        out['unknown_surface_id'] = None
    except ValueError as err:
        out['unknown_surface_id'] = str(err)
    require(out['unknown_surface_id'] == 'unknown_surface_id',
            'unknown_surface_not_refused')
    try:
        lc.Body('b', 'b', 'm', 1.0, 0.4, 0.5, lc.THICKNESS_M,
                [(0, 0, 0)] * 3, [(0, 1, 2)])
        out['bad_friction'] = None
    except ValueError as err:
        out['bad_friction'] = str(err)
    require(out['bad_friction'] == 'bad_friction', 'bad_friction_not_refused')
    try:
        lc.Body('b', 'b', 'm', 1.0, 0.6, 0.4, -0.001,
                [(0, 0, 0), (1, 0, 0), (0, 1, 0)], [(0, 1, 2)])
        out['bad_thickness'] = None
    except ValueError as err:
        out['bad_thickness'] = str(err)
    require(out['bad_thickness'] == 'bad_thickness',
            'bad_thickness_not_refused')
    return out


# ---------- main ----------

def main():
    ac.check_pins()
    doc, display = ac.emit()
    x0a = x0_independent_shapes()
    x0t = x0_tetra_drop()
    x0b = x0_sternum_clavicle()
    x0c = x0_full_arm_counts()
    s1 = s1_random_sweep()
    x1, trace_x1 = x1_resting()
    x2, trace_x2 = x2_oblique()
    x3, trace_x3 = x3_sliding()
    x4, trace_x4 = x4_crossing()
    p7 = p7_area_scaling()
    refusals = refusal_probes()

    trace = {
        'schema': 'chimera.local_contact.trace.v1',
        'task': 'M06',
        'tick_interval': [0, len(trace_x3) - 1],
        'scenarios': {
            'x1_resting': {'ticks': trace_x1, 'dt': DT},
            'x2_oblique': {'ticks': trace_x2, 'dt': DT},
            'x3_sliding': {'ticks': trace_x3, 'dt': DT,
                           'capture': True},
            'x4_crossing': {'ticks': trace_x4, 'dt': DT},
        },
    }
    (HERE / 'experiment_trace.json').write_text(
        json.dumps(trace, indent=1, ensure_ascii=False) + '\n',
        encoding='utf-8')

    receipt = {
        'schema': 'chimera.local_contact.receipt.v1',
        'task': 'M06',
        'criteria_sha256':
            'bb695fddee166aeb79edf99c62bf6537bb24d52b3d85866f1834f0526feb9efc',
        'preregistration': {
            'file': 'PREREGISTRATION.md',
            'sha256': hashlib.sha256(
                (HERE / 'PREREGISTRATION.md').read_bytes()).hexdigest(),
        },
        'input_pins': dict(ac.FROZEN_PINS),
        'modules_sha256': {
            name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
            for name in ('local_contact.py', 'author_contact.py',
                         'run_experiments.py')},
        'contact_law_sha256': hashlib.sha256(
            (HERE / 'contact_law.json').read_bytes()).hexdigest(),
        'trace_sha256': hashlib.sha256(
            (HERE / 'experiment_trace.json').read_bytes()).hexdigest(),
        'experiments': {
            'X0_independent_shapes': x0a,
            'X0_tetra_drop': x0t,
            'X0_sternum_clavicle': x0b,
            'X0_full_arm': x0c,
            'S1_random_sweep': s1,
            'X1_resting': x1,
            'X2_oblique': x2,
            'X3_sliding': x3,
            'X4_crossing': x4,
            'P7_area_scaling': p7,
            'refusal_probes': refusals,
        },
        'determinism': {
            'rng': 'none outside declared LCG (seed_base %d, 32 scenes)'
                   % ac.SEED_BASE,
            'wall_clock': 'absent',
        },
        'applicability': {
            'native_tests': 'campaign-owned executable named checks (M01/'
                            'M02/M04 precedent); offline CPU-only',
            'not_claimed': ['C++ engine integration', 'GPU residency',
                            'rotation dynamics', 'pressure law (M03 pending)',
                            'live renderer'],
        },
    }
    (HERE / 'experiment_receipt.json').write_text(
        json.dumps(receipt, indent=1, ensure_ascii=False) + '\n',
        encoding='utf-8')
    print('X0a contacts:', x0a['contacts'], '| recall', x0a['recall'],
          '| ids', x0a['surface_ids_used'])
    print('X0t contacts:', x0t['contacts'], '| ids', x0t['surface_ids_used'],
          '| recall', x0t['recall'])
    print('X0b exhaustive pairs:', x0b['exhaustive_pairs'],
          '| contacts', x0b['contacts'])
    print('X0c arm triangles:', x0c['triangles'], '| candidates',
          x0c['candidate_pair_count'], '| contacts', x0c['contacts'])
    print('S1 scenes:', s1['scene_count'], '| total missed:',
          s1['total_missed'])
    print('X1 support N:', x1['support_force_N'], '(weight',
          x1['weight_N'], ') anchor', x1['anchor_impulse_Ns_mean'])
    print('X2 vt_after:', x2['vt_after'], '| jt/jn:', x2['jt_over_jn'])
    print('X3 d:', x3['distance_m'], 'oracle', x3['distance_oracle_m'],
          '| W_f', x3['w_f_ke_J'], 'slack', x3['work_slack_J'])
    print('X4 detected before overlap:',
          x4['all_detected_before_overlap'], '| controls late/missed:',
          x4['all_controls_late_or_missed'])
    print('P7 twin ratio:', p7['twin_ratio'])
    print('receipt + trace written')


if __name__ == '__main__':
    main()
