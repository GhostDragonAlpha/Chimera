"""Reproducible AP02 batch: two independent ports on one surface plus
finite-area port coupling, with resumable receipts. CPU-only research harness;
no GPU batch, render binding or gameplay admission is claimed."""
from __future__ import annotations
import argparse
import json
import sys
import time
from pathlib import Path
import numpy as np
from .core import (Refusal, require, digest, file_hash, source_hashes, recipe as recipe1)
from .core2 import (recipe2, detailed2, measure_quadratic, quadratic_from_measurements,
                    Response2, equilibrium2, QUAD_DOMAIN)
from .verify2 import (LIMITS2, verify_samples2, verify_quadratic2, stiffness_detailed,
                      stiffness_heron, verify_equilibrium2)
from .faa_port import (patch_spec, admit, measure_transfer, equilibrium_loaded_port,
                       faa_source_hash, faa)
from .runner import write, read

SCHEMA2 = 'chimera.artificial_protein.run2.v1'
JOINT_LIMITS = {"balance_rel": 1e-12, "gradient_rel": 1e-6, "equilibrium_residual": 1e-9,
                "transfer_fraction": 0.25}
XST_STATES = [(0.12, -0.18, 1.), (-0.25, 0.05, 1.), (0.30, 0.30, 1.), (0.20, -0.10, 2.)]
TRANSFER_CASES = [("force_z", [0., 0., 0.01], [0., 0., 0.]), ("force_x", [0., 0.005, 0.], [0., 0., 0.]),
                  ("moment_x", [0., 0., 0.], [0.02, 0., 0.]), ("mixed", [0., 0., 0.008], [0., 0., 0.03])]
LOADED_CASES = [([0., 0., -50.], [0., 2., 0.]), ([0., 0., -120.], [1.5, -1.0, 0.])]

def cases2(recipes):
    cases = []
    for r in recipes:
        g = np.linspace(-.3, .3, 13)
        for i, hp in enumerate(g):
            for j, hq in enumerate(g):
                cases.append({'id': f"{r['id']}_train_{i}_{j}", 'recipe': r, 'hp': float(hp), 'hq': float(hq), 'scale': 1., 'gamma': 1., 'split': 'train'})
        rng = np.random.default_rng(9100 + r['seed'])
        for scale in [.5, 2.]:
            for j in range(6):
                hp, hq = rng.uniform(-.34, .34, 2)
                cases.append({'id': f"{r['id']}_held_{scale}_{j}", 'recipe': r, 'hp': float(hp*scale), 'hq': float(hq*scale), 'scale': scale, 'gamma': 1., 'split': 'heldout'})
        cases.append({'id': f"{r['id']}_zero", 'recipe': r, 'hp': .12, 'hq': -.21, 'scale': 1., 'gamma': 0., 'split': 'control'})
    return cases

def _rel(value, *terms):
    return value/max(max(abs(t) for t in terms), 1e-30)

def physics(recipes):
    """All AP02 measurements and independent checks; run2 stores it, check2 recomputes it."""
    out = {}
    quads = []
    for r in recipes:
        K, e0 = measure_quadratic(r)
        quad = quadratic_from_measurements(r, K, e0, measured_errors={'reaction': 0., 'energy': 0.})
        errors = verify_quadratic2(r, quad)
        quad = quadratic_from_measurements(r, K, e0, measured_errors={'reaction': errors['max_reaction_error'], 'energy': errors['max_energy_error']})
        quads.append(quad)
        require(errors['passes'], 'quadratic_out_of_budget:'+r['id'])
    out['quadratics'] = quads
    xs = []
    for r in recipes:
        for hp, hq, scale in XST_STATES:
            d = stiffness_detailed(r, hp, hq, scale); h = stiffness_heron(r, hp, hq, scale)
            err = float(np.max(np.abs(d-h)))   # gamma = 1 for all cross-stiffness states
            sym = float(np.max(np.abs(d-d.T)))
            frac = abs(d[0,1])/min(d[0,0], d[1,1])
            require(err <= LIMITS2['cross_stiffness'], 'cross_stiffness_mismatch:'+r['id'])
            require(sym <= LIMITS2['hessian_symmetry'], 'hessian_asymmetric:'+r['id'])
            require(frac >= LIMITS2['coupling_fraction'], 'ports_decoupled:'+r['id'])
            xs.append({'recipe_id': r['id'], 'state': [hp, hq], 'scale': scale,
                       'detailed': d.tolist(), 'heron': h.tolist(),
                       'max_error_normalized': err, 'symmetry_error': sym, 'coupling_fraction': frac})
    out['cross_stiffness'] = xs
    eq = []
    a = recipes[0]; b = recipes[1]
    anchors = [(-.08, -.06), (.07, .11)]
    for loads, box in [((-0.3, 0.45), (-.25, .25)), ((0.5, -0.2), (-.25, .25))]:
        pieces = [(lambda h, r=r: detailed2(r, float(h[0]), float(h[1])), an) for r, an in zip([a, b], anchors)]
        measured = equilibrium2(pieces, loads, np.array(box*2, dtype=float).reshape(2,2))
        check = verify_equilibrium2([(a, anchors[0]), (b, anchors[1])], loads, np.array(box*2, dtype=float).reshape(2,2), measured)
        eq.append({'kind': 'detailed', 'recipes': [a['id'], b['id']], 'anchors': [list(an) for an in anchors], 'loads_n': list(loads), 'result': measured, 'verification': check})
    red_anchors = [(-.008, -.006), (.006, .004)]   # keep |q - anchor| inside the 0.02 quadratic domain
    for loads in [(0.02, -0.03), (-0.012, 0.009)]:
        box = np.array([[-.012, .012], [-.012, .012]])
        det = equilibrium2([(lambda h, r=r: detailed2(r, float(h[0]), float(h[1])), an) for r, an in zip([a, b], red_anchors)], loads, box)
        red = equilibrium2([(Response2(q), an) for q, an in zip(out['quadratics'][:2], red_anchors)], loads, box)
        diff = float(np.max(np.abs(np.array(det['q'])-np.array(red['q']))))
        require(diff <= LIMITS2['equilibrium_m'], 'reduced_equilibrium_mismatch')
        eq.append({'kind': 'reduced_vs_detailed', 'loads_n': list(loads), 'anchors': [list(an) for an in red_anchors],
                   'detailed_q': det['q'], 'reduced_q': red['q'], 'q_difference_m': diff})
    out['equilibria'] = eq
    spec, area = patch_spec()
    out['patch_admission'] = admit(spec, area)
    falsifiers = {}
    try:
        collinear, _ = patch_spec(collinear=True); collinear.assert_constrains_all_six(); falsifiers['collinear_refused'] = False
    except ValueError: falsifiers['collinear_refused'] = True
    try:
        spec.assert_min_couple_stiffness(1e-3, kappa_areal=1e8, patch_area=area*1.7); falsifiers['provenance_refused'] = False
    except ValueError: falsifiers['provenance_refused'] = True
    require(falsifiers['collinear_refused'] and falsifiers['provenance_refused'], 'admission_falsifier_failed')
    out['admission_falsifiers'] = falsifiers
    fan = recipe1(0)
    transfers = []
    for name, c_a, phi in TRANSFER_CASES:
        m = measure_transfer(spec, fan, c_a, phi)
        f_scale = max(max(abs(v) for v in m['F_a_N']), max(abs(v) for v in m['F_b_N']), 1e-30)
        # torque terms can vanish physically (pure axial load): normalize against
        # the moment-arm scale too, not only the (zero) torque magnitudes
        t_scale = max(max(abs(v) for v in m['tau_a_Nm']), max(abs(v) for v in m['tau_b_Nm']),
                      float(np.linalg.norm(c_a))*f_scale, 1e-30)
        require(m['wrench_balance_force_n']/f_scale <= JOINT_LIMITS['balance_rel'], 'wrench_force_balance:'+name)
        require(m['wrench_balance_torque_nm']/t_scale <= JOINT_LIMITS['balance_rel'], 'wrench_torque_balance:'+name)
        require(m['gradient_fd_max_error_relative'] <= JOINT_LIMITS['gradient_rel'], 'joint_gradient_mismatch:'+name)
        transfers.append({'case': name, 'c_a_m': c_a, 'phi_rad': phi, **m})
    eigen = spec.couple_stiffness_eigen()   # already ascending eigenvalues
    for t, (name, c_a, phi) in zip(transfers, TRANSFER_CASES):
        delta = max(abs(v) for v in c_a); angle = max(abs(v) for v in phi)
        if delta: require(max(abs(v) for v in t['F_b_N']) >= JOINT_LIMITS['transfer_fraction']*spec.Kbar[0,0]*delta, 'force_not_transferred:'+name)
        if angle: require(max(abs(v) for v in t['tau_b_Nm']) >= JOINT_LIMITS['transfer_fraction']*eigen[0]*angle, 'moment_not_transferred:'+name)
    out['transfers'] = transfers
    loaded = []
    for load, torque in LOADED_CASES:
        m = equilibrium_loaded_port(spec, fan, load, torque)
        f_scale = max(max(abs(v) for v in load), abs(m['fan_reaction_n']), max(abs(v) for v in m['F_b_N']), 1e-30)
        t_scale = max(max(abs(v) for v in torque), max(abs(v) for v in m['tau_b_Nm']), 1e-30)
        require(m['residual_force_n'] <= JOINT_LIMITS['equilibrium_residual'] and m['residual_torque_nm'] <= JOINT_LIMITS['equilibrium_residual'], 'joint_equilibrium_residual')
        require(m['carrier_balance_force_n']/f_scale <= JOINT_LIMITS['balance_rel'], 'carrier_force_balance')
        require(m['carrier_balance_torque_nm']/t_scale <= JOINT_LIMITS['balance_rel'], 'carrier_torque_balance')
        loaded.append({'load_n': load, 'torque_nm': torque, **m})
    out['loaded_ports'] = loaded
    return out

def run2(out, resume=False):
    if not resume: out.mkdir(parents=True, exist_ok=False)
    require(out.is_dir(), 'output_missing')
    recipes = [recipe2(i) for i in range(3)]; cases = cases2(recipes)
    identity = {'schema': SCHEMA2, 'source_hashes': source_hashes(), 'faa_source_hash': faa_source_hash(),
                'case_manifest_hash': digest(cases)}
    identity_path = out/'identity.json'
    if resume:
        require(read(identity_path) == identity, 'stale_resume_inputs')
        if (out/'receipt.json').exists():
            return check2(out)
    else: write(identity_path, identity)
    write(out/'case-manifest.json', cases)
    start = time.perf_counter()
    try:
        values = [{k: v for k, v in detailed2(c['recipe'], c['hp'], c['hq'], c['scale'], c['gamma']).items() if k in ('energy', 'reaction')} for c in cases]
        reference = verify_samples2(cases, values)
        write(out/'measurements.json', values)
        result = physics(recipes)
        for r, q in zip(recipes, result['quadratics']): write(out/(r['id']+'-quadratic.json'), q)
        write(out/'cross-stiffness.json', result['cross_stiffness'])
        write(out/'equilibria.json', result['equilibria'])
        write(out/'finite-area-coupling.json', {k: result[k] for k in ('patch_admission','admission_falsifiers','transfers','loaded_ports')})
        functions = [{'recipe_id': r['id'], 'artifact_sha256': q['sha256'],
                      'function': 'opposes two independent rail displacements through one shared surface; reactions are cross-coupled',
                      'domain_half_normalized': QUAD_DOMAIN,
                      'measured_errors': q['measured_errors'],
                      'not_supported': ['inertia','damage','general folding','mass inventory','out-of-domain quadratic use','dynamics'],
                      'new_question': 'Does the measured cross-port moment remain accurate when the far carrier fixture is replaced by a second compliant piece?'}
                     for r, q in zip(recipes, result['quadratics'])]
        write(out/'function-cards.json', functions)
        receipt = {**identity, 'status': 'PASS', 'authority': 'local numerical verification only; independent release review required',
                   'scope': 'AP02 two independent rail ports, measured cross stiffness, quadratic reduced response, finite-area port coupling with cross-port force and moment',
                   'reference': reference, 'physics': {k: result[k] for k in ('cross_stiffness','equilibria')},
                   'coupling': {k: result[k] for k in ('patch_admission','admission_falsifiers','transfers','loaded_ports')},
                   'limits': {**LIMITS2, **JOINT_LIMITS}, 'elapsed_s': time.perf_counter()-start,
                   'unimplemented': ['2-D response table','Noether learned model','general multiport kernel','gameplay admission','controller attestation','dynamic physics','render binding']}
        files = ['identity.json','case-manifest.json','measurements.json','cross-stiffness.json','equilibria.json','finite-area-coupling.json','function-cards.json'] + [r['id']+'-quadratic.json' for r in recipes]
        receipt['artifacts'] = {f: file_hash(out/f) for f in files}
        write(out/'receipt.json', receipt)
        return receipt
    except BaseException as e:
        write(out/'failure.json', {'status': 'INTERRUPTED' if isinstance(e, KeyboardInterrupt) else 'FAIL', 'reason': str(e), 'source_hashes': identity['source_hashes'], 'elapsed_s': time.perf_counter()-start})
        raise

def check2(out):
    receipt = read(out/'receipt.json')
    require(receipt.get('schema') == SCHEMA2 and receipt.get('source_hashes') == source_hashes() and receipt.get('faa_source_hash') == faa_source_hash(), 'stale_sources')
    recipes = [recipe2(i) for i in range(3)]; cases = cases2(recipes)
    require(read(out/'case-manifest.json') == cases, 'case_manifest_changed')
    expected_files = {'identity.json','case-manifest.json','measurements.json','cross-stiffness.json','equilibria.json','finite-area-coupling.json','function-cards.json'} | {f'ap02_{i}-quadratic.json' for i in range(3)}
    require(set(receipt.get('artifacts', {})) == expected_files, 'missing_receipt_artifacts')
    for name, h in receipt['artifacts'].items():
        require((out/name).is_file() and file_hash(out/name) == h, 'artifact_changed:'+name)
    verify_samples2(cases, read(out/'measurements.json'))
    result = physics(recipes)
    for r in recipes: require(read(out/(r['id']+'-quadratic.json')) == next(q for q in result['quadratics'] if q['recipe_hash'] == digest(r)), 'quadratic_changed:'+r['id'])
    require(read(out/'cross-stiffness.json') == result['cross_stiffness'], 'cross_stiffness_changed')
    require(read(out/'equilibria.json') == result['equilibria'], 'equilibria_changed')
    require(read(out/'finite-area-coupling.json') == {k: result[k] for k in ('patch_admission','admission_falsifiers','transfers','loaded_ports')}, 'coupling_changed')
    require(receipt['status'] == 'PASS', 'receipt_not_pass')
    return {'status': 'PASS', 'scope': 'freshness and independently recomputed two-port and finite-area physics; no release attestation'}

def main():
    p = argparse.ArgumentParser(); p.add_argument('action', choices=['run','check']); p.add_argument('--out', type=Path, required=True); p.add_argument('--resume', action='store_true'); a = p.parse_args()
    try:
        result = run2(a.out.resolve(), a.resume) if a.action == 'run' else check2(a.out.resolve())
        print(json.dumps({k: result[k] for k in ['status','scope']}, indent=2)); return 0
    except (Refusal, OSError, ValueError, KeyError) as e:
        print(json.dumps({'status': 'FAIL', 'reason': str(e)})); return 1

if __name__ == '__main__': sys.exit(main())
