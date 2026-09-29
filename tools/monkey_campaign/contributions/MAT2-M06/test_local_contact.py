"""MAT2-M06 named checks: P1-P13 probes and F1-F4 falsifier bites.

Runs the frozen PREREGISTRATION.md (Amendments A1-A3) probes on the exact
candidate revision, re-runs the UNMODIFIED M01/M02/M04 suites, and bites all
four card-falsifier arms on TAMPERED COPIES written to the attempt scratch
(scratch-falsifiers/, logged to FALSIFIER_LOG.json, copies discarded after).

CPU-only, stdlib-only, deterministic.
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'MAT2-M02'))

import author_contact as ac  # noqa: E402
import local_contact as lc  # noqa: E402
import run_experiments as rx  # noqa: E402

ATTEMPT = HERE.parents[4]
SCRATCH = ATTEMPT / 'scratch-falsifiers'
CONTRIB = HERE.parent

CHECKS = []


def check(name, arg=None):
    def wrap(fn):
        CHECKS.append((name, fn, arg))
        return fn
    return wrap


def close(a, b, rel=1e-9, abl=0.0):
    return abs(a - b) <= max(rel * max(abs(a), abs(b)), abl)


def fresh_run():
    """Full experiment run; returns (receipt dict, trace dict)."""
    rx.main()
    receipt = json.loads((HERE / 'experiment_receipt.json').read_text(
        encoding='utf-8'))
    trace = json.loads((HERE / 'experiment_trace.json').read_text(
        encoding='utf-8'))
    return receipt, trace


def tamper_module(name, old, new):
    """Copy local_contact.py into the attempt scratch, apply an exact source
    replacement, import the copy. Raises if the anchor text is missing."""
    src = (HERE / 'local_contact.py').read_text(encoding='utf-8')
    if src.count(old) != 1:
        raise AssertionError('tamper_anchor_missing:' + name)
    SCRATCH.mkdir(parents=True, exist_ok=True)
    path = SCRATCH / ('local_contact_tampered_' + name + '.py')
    path.write_text(src.replace(old, new), encoding='utf-8')
    spec = importlib.util.spec_from_file_location(
        'lc_tampered_' + name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod, path


# ---------- probes ----------

@check('P1 pins and declaration document')
def p1():
    ac.check_pins()
    doc, display = ac.emit()
    known = {s['id'] for s in doc['surfaces']}
    lc.validate_local_contact(doc, known)
    assert doc['declarations']['g'] == 9.81
    assert doc['declarations']['dt'] == 0.005
    assert doc['declarations']['thickness_m'] == 0.002
    assert doc['declarations']['slop_m'] == 1e-5
    assert doc['declarations']['margin_m'] == 1e-5
    assert doc['declarations']['beta'] == 0.2
    assert doc['declarations']['restitution'] == 0.0
    assert doc['declarations']['pair_friction_rule'] == 'elementwise_min'
    assert doc['declarations']['seeds'] == {
        'rng': 'lcg_64bit', 'seed_base': 20260928, 'scenes': 32,
        'scene_k_seed': 'seed_base + k'}
    assert doc['provenance']['input_pins'] == dict(ac.FROZEN_PINS)


@check('P2 X0 independent shapes + tetra drop: recall 1.0, pinned ids', arg='receipt')
def p2(receipt):
    x0a = receipt['experiments']['X0_independent_shapes']
    x0t = receipt['experiments']['X0_tetra_drop']
    assert x0a['recall'] == 1.0 and x0t['recall'] == 1.0
    assert x0a['contact_set_identical'] and x0t['contact_set_identical']
    assert x0a['cross_body_pairs_exhaustive'] == 8
    assert x0t['surface_ids_used'] == ['plate', 'tetra']
    assert x0t['contacts'] > 0


@check('P3 X0 sternum x clavicle complete exhaustive', arg='receipt')
def p3(receipt):
    x0b = receipt['experiments']['X0_sternum_clavicle']
    assert x0b['exhaustive_pairs'] == 2496
    assert x0b['recall'] == 1.0 and x0b['contact_set_identical']


@check('P4 X0 full compiled arm counts + subset property', arg='receipt')
def p4(receipt):
    x0c = receipt['experiments']['X0_full_arm']
    assert x0c['triangles'] == 5384
    assert x0c['contacts_subset_of_candidates']
    assert x0c['candidate_pair_count'] > 0


@check('P5 S1 seeded recall sweep: zero missed on all 32 scenes', arg='receipt')
def p5(receipt):
    s1 = receipt['experiments']['S1_random_sweep']
    assert s1['scene_count'] == 32
    assert s1['total_missed'] == 0
    assert s1['recall_min'] == 1.0
    assert s1['seed_base'] == 20260928
    assert [s['seed'] for s in s1['scenes']] == [20260928 + k for k in range(32)]


@check('P6 X1 resting load: weight supported, area split, anchor, ledger', arg='receipt')
def p6(receipt):
    x1 = receipt['experiments']['X1_resting']
    assert close(x1['support_force_N'], x1['weight_N'], rel=1e-9)
    assert close(x1['weight_N'], 1.1772, rel=0, abl=1e-12)
    f = x1['per_triangle_forces_N']
    assert abs(f['0'] - f['1']) <= 1e-12
    assert close(f['0'], 0.5886, rel=1e-9)
    assert close(x1['anchor_impulse_Ns_mean'], 1.1772 * 0.005, rel=1e-12)
    assert x1['anchor_is_weight_dt']
    assert x1['ledger_residual_max'] <= 1e-12
    assert -x1['steady_min_gap_m'] <= 1e-4
    assert x1['impact_tick'] is not None and x1['settle_tick'] is not None


@check('P7 area scaling: equal split, twin ratio 2, zero-area refusal', arg='receipt')
def p7(receipt):
    p7r = receipt['experiments']['P7_area_scaling']
    assert abs(p7r['equal_abs_diff']) <= 1e-12
    assert close(p7r['twin_ratio'], 2.0, rel=1e-12)
    assert close(p7r['twin_support_total_N'], 1.1772, rel=1e-9)
    assert p7r['zero_area_refusal'] == 'zero_area_interface'


@check('P8 X2 oblique: normal, arrested vn, slip vt, friction cone', arg='receipt')
def p8(receipt):
    x2 = receipt['experiments']['X2_oblique']
    assert abs(x2['normal'][2] - 1.0) <= 1e-9
    assert abs(x2['normal'][0]) <= 1e-9 and abs(x2['normal'][1]) <= 1e-9
    assert abs(x2['vn_after']) <= 1e-12
    assert close(x2['vt_after'], 0.4330127018922193 - 0.1, rel=1e-9)
    assert x2['slip_regime']
    assert close(x2['jt_over_jn'], 0.4, rel=1e-12)
    assert x2['slip_required_stop_Ns'] > x2['mu_s_cap_Ns']


@check('P9 X3 sliding: oracle distance, W_f, finite ds, stop and stay', arg='receipt')
def p9(receipt):
    x3 = receipt['experiments']['X3_sliding']
    assert abs(x3['distance_m'] - x3['distance_oracle_m']) <= 0.5 * rx.DT
    assert close(x3['distance_oracle_m'], 0.031855249745158, rel=1e-12)
    assert close(x3['w_f_ke_J'], 0.015, rel=0, abl=1e-9)
    assert x3['work_slack_J'] <= 1e-3
    assert close(x3['jn_steady_Ns'], 0.12 * 9.81 * 0.005, rel=1e-12)
    trace = json.loads((HERE / 'experiment_trace.json').read_text(
        encoding='utf-8'))
    ticks = trace['scenarios']['x3_sliding']['ticks']
    stop = x3['stop_tick']
    assert all(abs(t['vx']) <= 1e-12 for t in ticks[stop:])
    assert all(t['ds_m'] <= 0.5 * 0.005 + 1e-12 for t in ticks)


@check('P10 X4 crossing: CCD before overlap, controls late, ledger closes', arg='receipt')
def p10(receipt):
    x4 = receipt['experiments']['X4_crossing']
    assert len(x4['variants']) == 5
    assert x4['all_detected_before_overlap']
    assert x4['all_controls_late_or_missed']
    for v in x4['variants']:
        assert abs(v['va_after'][2]) <= 1e-12 and abs(v['vb_after'][2]) <= 1e-12
        assert v['min_post_gap_m'] >= -1e-5
        assert v['max_momentum_residual'] <= 1e-12
        assert v['jn_Ns'] > 0.0


@check('P11 refusal probes: named codes', arg='receipt')
def p11(receipt):
    ref = receipt['experiments']['refusal_probes']
    assert ref['unknown_surface_id'] == 'unknown_surface_id'
    assert ref['bad_friction'] == 'bad_friction'
    assert ref['bad_thickness'] == 'bad_thickness'
    try:
        lc.Body('b', 'b', 'm', 1.0, 0.6, 0.4, 0.002,
                [(0, 0, 0), (1, 0, 0), (2, 0, 0)], [(0, 1, 2)])
        raise AssertionError('zero_area_accepted')
    except ValueError as err:
        assert str(err) == 'zero_area_interface'


@check('P12 regressions: unmodified M01/M02/M04 suites green')
def p12():
    results = {}
    for name, rel, expect in (
            ('M01', 'MAT2-M01/test_material_state.py', None),
            ('M02', 'MAT2-M02/test_material_regions.py', None),
            ('M04', 'MAT2-M04/test_passive_response.py', None)):
        proc = subprocess.run([sys.executable, '-B', str(CONTRIB / rel)],
                              capture_output=True, text=True, timeout=1200)
        results[name] = proc
        assert proc.returncode == 0, name + ' regression failed: ' + \
            proc.stdout[-800:] + proc.stderr[-800:]
    return 'M01/M02/M04 suites re-ran green unmodified'


@check('P13 determinism: double run byte-identical')
def p13():
    rx.main()
    b1 = (HERE / 'experiment_receipt.json').read_bytes()
    t1 = (HERE / 'experiment_trace.json').read_bytes()
    rx.main()
    assert (HERE / 'experiment_receipt.json').read_bytes() == b1
    assert (HERE / 'experiment_trace.json').read_bytes() == t1


# ---------- falsifier arms (tampered copies, discarded after) ----------

def mini_recall(mod, scenes=(0, 1, 2, 3)):
    """Candidate recall of a (possibly tampered) module on seeded scenes,
    against the module's own exhaustive reference run on the same states."""
    missed = 0
    for k in scenes:
        bodies = ac.random_scene(k)
        for _ in range(3):
            snap = [(b.velocity, [tuple(v) for v in b.vertices])
                    for b in bodies]
            rec, led = mod.solve_tick(bodies, exhaustive=False)
            for r in rec:
                if r['pair_key'] not in led['cand_keys']:
                    missed += 1
            bodies_e = ac.random_scene(k)
            for be, (vel, verts) in zip(bodies_e, snap):
                be.velocity = vel
                be.vertices = verts
            rec_e, _ = mod.solve_tick(bodies_e, exhaustive=True)
            if rx.contact_set(rec) != rx.contact_set(rec_e):
                missed += 1
    return missed


@check('F1 hierarchy pruning misses contact -> caught', arg='log')
def f1(log):
    mod, path = tamper_module(
        'f1_prune',
        '            if _overlaps(loi, hii, loj, hij):\n'
        '                pairs.add((i, j) if i < j else (j, i))',
        '            if _overlaps(loi, hii, loj, hij) and (i + j) % 5:\n'
        '                pairs.add((i, j) if i < j else (j, i))')
    missed = mini_recall(mod)
    assert missed > 0, 'F1 tamper was NOT caught (pruning drop undetected)'
    # the untampered module stays green on the same scenes
    assert mini_recall(lc) == 0
    log['F1'] = {'tamper': 'sweep_prune drops every 5th candidate pair',
                 'missed_contacts': missed, 'verdict': 'CAUGHT',
                 'tampered_module': path.name}


@check('F2 render-only triangles support weight -> caught', arg='log')
def f2(log):
    # arm (a): the pinned identity declaration is checked against the blob
    blob = ac.load_blob()
    indep = ac.load_indep()
    plate_blob = blob['regions']['plate']
    plate_doc = next(r for r in indep['regions'] if r['id'] == 'plate')
    assert plate_blob['visual_mesh'].startswith('identity')
    assert plate_blob['physical_mesh'].startswith('identity')
    assert len(plate_blob['triangles']) == plate_doc['rest_geometry'][
        'triangle_count']
    # arm (b): a visual-only support (one plate triangle dropped) cannot
    # carry the block placed over the dropped triangle's exclusive region
    v, t = ac.plate_vertices(0.0)
    one_tri = ac.make_plate(pinned=True)
    one_tri.triangles = [t[0]]  # tri1 (the upper-diagonal half) dropped
    block = ac.make_block(0.002, x=0.0, y=0.055)  # entirely within tri1's
    # exclusive region (y above the 0.5x diagonal, clear of tri0)
    bodies = [block, one_tri]
    for _ in range(30):
        rec, led = lc.solve_tick(bodies)
    assert block.vertices[0][2] < -0.05, 'F2 arm b: block did not fall through'
    assert not any(r['jn_Ns'] > 0.0 for r in rec), \
        'F2 arm b: phantom support appeared'
    # the full physical support carries the weight (P6 green)
    log['F2'] = {'tamper': 'support reduced to one plate triangle under a '
                           'block placed over the dropped region',
                 'observed': 'block falls through, zero support impulses',
                 'verdict': 'CAUGHT',
                 'identity_guard': 'pinned visual/physical identity verified'}


@check('F3 two-sided loads violated -> caught', arg='log')
def f3(log):
    mod, path = tamper_module(
        'f3_onesided',
        '    body_a.velocity = vadd(body_a.velocity, vscale(jn_vec, inv_ma))\n'
        '    body_b.velocity = vsub(body_b.velocity, vscale(jn_vec, inv_mb))',
        '    pass  # TAMPERED: body_a impulse half dropped\n'
        '    body_b.velocity = vsub(body_b.velocity, vscale(jn_vec, inv_mb))')
    bodies = [ac.make_block(0.002, x=-0.05), ac.make_plate(pinned=True)]
    fired = None
    try:
        for _ in range(5):
            mod.solve_tick(bodies)
    except ValueError as err:
        fired = str(err)
    assert fired == 'ledger_imbalance', \
        'F3 tamper was NOT caught (fired: %r)' % (fired,)
    log['F3'] = {'tamper': 'solve_contact drops the reciprocal impulse half',
                 'fired': fired, 'verdict': 'CAUGHT',
                 'tampered_module': path.name}


@check('F4 friction removed -> caught', arg='log')
def f4(log):
    mod, path = tamper_module(
        'f4_mu0',
        'def pair_mu(body_a, body_b):\n'
        '    """Declared rule: elementwise min of the two surface '
        'declarations."""\n'
        '    return min(body_a.mu_s, body_b.mu_s), min(body_a.mu_k, '
        'body_b.mu_k)',
        'def pair_mu(body_a, body_b):\n'
        '    return (0.0, 0.0)  # TAMPERED: friction removed')
    bodies = [ac.make_block(0.002, x=-0.05, vel=(0.5, 0.0, 0.0)),
              ac.make_plate(pinned=True)]
    block = bodies[0]
    x0 = block.vertices[0][0]
    stopped = False
    for _ in range(200):
        mod.solve_tick(bodies)
        if abs(block.velocity[0]) <= 1e-12:
            stopped = True
            break
    assert not stopped, 'F4 tamper was NOT caught (block stopped without mu)'
    d = block.vertices[0][0] - x0
    assert d > 0.5 * 0.005, 'F4: expected runaway sliding'
    log['F4'] = {'tamper': 'pair friction forced to (0, 0)',
                 'observed': 'block never stops; displacement %.6f m in 200 '
                             'ticks' % d,
                 'verdict': 'CAUGHT', 'tampered_module': path.name}


def main():
    log = {}
    receipt, trace = fresh_run()
    passed = 0
    for entry in CHECKS:
        name, fn, arg = entry
        try:
            if arg == 'receipt':
                extra = fn(receipt)
            elif arg == 'log':
                extra = fn(log)
            else:
                extra = fn()
            print('PASS', name, ('| ' + str(extra)) if extra else '')
            passed += 1
        except Exception as err:
            print('FAIL', name, '->', repr(err))
            (SCRATCH / 'FALSIFIER_LOG.json').write_text(
                json.dumps(log, indent=1) + '\n', encoding='utf-8')
            raise
    # falsifier copies are discarded after the log is written
    for path in SCRATCH.glob('local_contact_tampered_*.py'):
        path.unlink()
    (SCRATCH / 'FALSIFIER_LOG.json').write_text(
        json.dumps(log, indent=1) + '\n', encoding='utf-8')
    print('checks: %d/%d passed' % (passed, len(CHECKS)))
    print('falsifier log:', SCRATCH / 'FALSIFIER_LOG.json')
    print('ALL FROZEN PROBES GREEN (P1-P13, F1-F4)')


if __name__ == '__main__':
    main()
