"""MAT2-M07 named checks: prereg probes and F1-F5 falsifier bites.

Runs the frozen PREREGISTRATION.md (Amendments A1-A4) arms on the exact
candidate revision, re-runs the UNMODIFIED M03/M04/M05/M06 suites, verifies
determinism (two fresh subprocess runs -> byte-identical trace and receipt),
and bites all five card/profile falsifier arms on TAMPERED COPIES written to
the attempt scratch (scratch-falsifiers/, logged to FALSIFIER_LOG.json,
copies discarded after).

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


def _load_local(name):
    """Load THIS directory's module explicitly (upstream packages insert
    their own directories into sys.path and would otherwise shadow)."""
    spec = importlib.util.spec_from_file_location(
        'mat2_m07_' + name, str(HERE / (name + '.py')))
    module = importlib.util.module_from_spec(spec)
    sys.modules['mat2_m07_' + name] = module
    spec.loader.exec_module(module)
    return module


rx = _load_local('run_experiments')
iw = _load_local('integrated_step')

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
    return abs(a - b) <= max(abl, rel * max(abs(a), abs(b)))


TAMPER_LOG = []


def load_tampered(name, replacements, log=None):
    source = (HERE / 'integrated_step.py').read_text(encoding='utf-8')
    for old, new in replacements:
        require_(old in source, 'tamper_anchor_missing:' + old[:60])
        source = source.replace(old, new, 1)
    SCRATCH.mkdir(parents=True, exist_ok=True)
    path = SCRATCH / f'integrated_step_{name}.py'
    path.write_text(source, encoding='utf-8')
    TAMPER_LOG.append({'tamper': name, 'file': str(path),
                       'replacements': [old[:80] for old, _ in replacements]})
    spec = importlib.util.spec_from_file_location(
        f'integrated_step_tamper_{name}', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def require_(ok, code):
    if not ok:
        raise AssertionError(code)


def run_world(module, comps, dt=None, ticks=rx.TICKS):
    components = [module.Component(cid, off) for cid, off in comps]
    world = module.IntegratedWorld(components,
                                   dt_s=dt or module.DT_S)
    world.run(ticks)
    return world


# ---------------------------------------------------------------- probes ----

@check('P1_input_pins')
def p1(arg):
    pins = iw.verify_input_pins()
    require_(len(pins) == 5, 'pin_count')


@check('P2_declared_order_guard')
def p2(arg):
    world = rx.build_world([('A', 0.0)])
    row = world.step(0)
    require_(row['order_digest'] == iw.DECLARED_DIGEST, 'digest_recorded')
    require_(tuple(row['order']) == iw.DECLARED_ORDER, 'order_recorded')


@check('P3_single_owner_ast')
def p3(arg):
    result = rx.p_single_owner()
    require_(result['ok'], 'second_writer:' + str(result['violations']))


@check('P4_world_state_is_owned')
def p4(arg):
    world = rx.build_world([('A', 0.0), ('B', 3.0)])
    for comp in world.components:
        require_(not hasattr(comp.membrane, 'step'), 'membrane_has_step')
        require_(not hasattr(comp.plate, 'step'), 'plate_has_step')
        require_(not hasattr(comp, 'step'), 'component_has_step')
    require_(callable(world.step), 'world_step_missing')


@check('P5_receipt_claims_replay')
def p5(arg):
    receipt = json.loads((HERE / 'experiment_receipt.json')
                         .read_text(encoding='utf-8'))
    for cid in ('A', 'B'):
        x1 = receipt['X1_coupling'][cid]
        require_(x1['peak_plate_displacement_m'] >= 1e-5, 'x1_plate_moves')
        require_(x1['peak_membrane_com_z_change_m'] >= 1e-6, 'x1_mem_moves')
        require_(x1['all_residuals_within_bound'], 'x1_residuals')
        x2 = receipt['X2_independence'][cid]
        require_(x2['bitwise_identical'] and x2['max_abs_float_diff'] == 0.0,
                 'x2_bitwise')
        x3 = receipt['X3_refinement']['components'][cid]
        require_(x3['stability_all_timesteps'], 'x3_stability')
        require_(1.5 <= x3['order_volume_observable'] <= 3.0, 'x3_p_vol')
        require_(1.5 <= x3['order_plate_observable'] <= 3.2
                 or x3['plate_errors_vs_finest'][1] == 0.0, 'x3_p_plate')
    require_(receipt['P_probes']['P_declared_order_digest_every_tick'],
             'p_order_digest')
    require_(receipt['P_probes']['P_single_owner_ast']['ok'], 'p_ast')


@check('P6_state_document_m01')
def p6(arg):
    summary = json.loads((HERE / 'experiment_receipt.json')
                         .read_text(encoding='utf-8'))['P_probes'][
        'P_state_document_m01']
    require_(isinstance(summary, dict)
             and summary.get('object_id') == 'mat2_m07_integrated_world',
             'm01_validation:' + repr(summary)[:120])


@check('P7_determinism_two_fresh_runs_byte_identical')
def p7(arg):
    outs = []
    for run in (1, 2):
        proc = subprocess.run(
            [sys.executable, '-B', str(HERE / 'run_experiments.py')],
            capture_output=True, text=True, cwd=str(HERE), timeout=1200)
        require_(proc.returncode == 0,
                 'det_run_failed:' + proc.stderr[-400:])
        outs.append((
            (HERE / 'experiment_trace.json').read_bytes(),
            (HERE / 'experiment_receipt.json').read_bytes()))
    require_(outs[0] == outs[1], 'determinism_files_differ')
    arg['determinism'] = {
        'trace_sha256': iw.sha256_file(HERE / 'experiment_trace.json'),
        'receipt_sha256': iw.sha256_file(HERE / 'experiment_receipt.json'),
        'note': 'two fresh subprocess runs produced byte-identical files'}


@check('P8_regressions_M03_M04_M05_M06_green')
def p8(arg):
    suites = [('MAT2-M03', 'test_pressure_membrane.py'),
              ('MAT2-M04', 'test_passive_response.py'),
              ('MAT2-M05', 'test_interface_exchange.py'),
              ('MAT2-M06', 'test_local_contact.py')]
    results = {}
    for pkg, test in suites:
        path = CONTRIB / pkg / test
        proc = subprocess.run([sys.executable, '-B', str(path)],
                              capture_output=True, text=True,
                              cwd=str(CONTRIB / pkg), timeout=1800)
        results[pkg] = {'exit': proc.returncode}
        require_(proc.returncode == 0,
                 f'regression_{pkg}_failed:' + proc.stderr[-400:])
    arg['regressions'] = results


# ---------------------------------------------------------- falsifier arms --

@check('F1_hidden_coupling_cross_wire_caught_by_independence_oracle')
def f1(arg):
    tam = load_tampered('F1', [(
        "    def step(self, tick):\n",
        "    def step(self, tick):\n"
        "        if len(self.components) > 1 and tick >= 1:\n"
        "            # TAMPER: hidden cross-component load channel\n"
        "            self.components[1].v += 0.01 * (\n"
        "                self.components[0].plate.velocity\n"
        "                - self.components[1].plate.velocity)\n")])
    caught_by = None
    max_diff = 0.0
    try:
        joint = run_world(tam, [('A', 0.0), ('B', 3.0)], ticks=12)
    except ValueError as exc:
        caught_by = 'in_world_ledger:' + str(exc)
    else:
        solo = run_world(tam, [('B', 3.0)], ticks=12)
        for wt, st in zip(joint.ticks, solo.ticks):
            jr, sr = wt['components']['B'], st['components']['B']
            if jr['state_hash'] != sr['state_hash']:
                caught_by = 'independence_oracle_state_hash'
            for key, sv in sr.items():
                jv = jr.get(key)
                if isinstance(sv, float) and isinstance(jv, float):
                    max_diff = max(max_diff, abs(jv - sv))
        if max_diff > 0.0:
            caught_by = caught_by or 'independence_oracle_trajectory'
    require_(caught_by is not None,
             'F1_not_caught: neither ledger nor independence oracle fired')
    arg['F1'] = {'caught_by': caught_by, 'max_abs_diff_B': max_diff,
                 'note': 'cross-wired components are caught'}


@check('F3_mixed_tick_state_caught')
def f3(arg):
    tam = load_tampered('F3', [
        ("        # end-of-tick snapshot (M05 A1 rule: energies at THIS "
         "configuration)\n        ke = self._component_ke(comp)\n",
         "        # end-of-tick snapshot (M05 A1 rule: energies at THIS "
         "configuration)\n        ke = getattr(comp, '_stale_ke', "
         "self._component_ke(comp))\n"),
        ("            ke_pre_proj = self._component_ke(comp)\n",
         "            ke_pre_proj = self._component_ke(comp)\n"
         "            comp._stale_ke = ke_pre_proj\n"),
    ])
    fired = None
    try:
        world = run_world(tam, [('A', 0.0)], ticks=12)
    except ValueError as exc:
        fired = str(exc)
    else:
        bad = [r['tick'] for cid in world.components
               for r in world.ticks
               if not r['components'][cid.component_id][
                   'residual_within_bound']]
        if bad:
            fired = f'mixed-tick rows outside the residual bound: {bad[:3]}'
    require_(fired is not None, 'F3_not_caught_by_any_gate')
    arg['F3'] = {'refusal': fired}


@check('F2_ordering_swap_caught_by_declared_order_check')
def f2(arg):
    permuted = "('contact', 'material', 'pressure')"
    # F2a: permuted execution AND permuted declaration -> the guard fires
    tam = load_tampered('F2a', [
        ("DECLARED_ORDER = ('pressure', 'material', 'contact')",
         f"DECLARED_ORDER = {permuted}"),
        ("            ph1 = self._phase_pressure_and_gravity(comp, dp, h)\n"
         "            ph2 = self._phase_material(comp, h)\n"
         "            ph3 = self._phase_contact(comp, h)\n",
         "            ph3 = self._phase_contact(comp, h)\n"
         "            ph2 = self._phase_material(comp, h)\n"
         "            ph1 = self._phase_pressure_and_gravity(comp, dp, h)\n"),
    ])
    fired_code = None
    try:
        run_world(tam, [('A', 0.0)], ticks=1)
    except ValueError as exc:
        fired_code = str(exc)
    require_(fired_code == 'declared_order_mismatch',
             'F2a_guard_did_not_fire:' + repr(fired_code))
    # F2b: permuted execution with the declaration left lying -> the run
    # proceeds but the trajectory measurably differs from the declared order
    tam2 = load_tampered('F2b', [
        ("            ph1 = self._phase_pressure_and_gravity(comp, dp, h)\n"
         "            ph2 = self._phase_material(comp, h)\n"
         "            ph3 = self._phase_contact(comp, h)\n",
         "            ph3 = self._phase_contact(comp, h)\n"
         "            ph2 = self._phase_material(comp, h)\n"
         "            ph1 = self._phase_pressure_and_gravity(comp, dp, h)\n"),
    ])
    swapped = run_world(tam2, [('A', 0.0)], ticks=40)
    canonical = rx.run_world([('A', 0.0)], ticks=40)
    a = swapped.ticks[-1]['components']['A']['plate_x_m']
    b = canonical.ticks[-1]['components']['A']['plate_x_m']
    require_(abs(a - b) > 0.0, 'F2b_no_physical_order_effect')
    arg['F2'] = {'guard_fired': fired_code,
                 'plate_x_declared': b, 'plate_x_swapped': a,
                 'abs_diff': abs(a - b)}


@check('F4_separate_pass_overwrites_motion_caught')
def f4(arg):
    tam = load_tampered('F4', [
        ("        require(max_jn <= GS_TOL_N_S, 'convergence_gate_not_met')\n",
         "        require(max_jn <= GS_TOL_N_S, 'convergence_gate_not_met')\n"
         "        # TAMPER: the contact stage re-writes the plate state from\n"
         "        # its own propagation (a second, uncoordinated pass)\n"
         "        comp.plate.velocity = np.asarray(\n"
         "            lc.vscale(lc.vsub(comp.plate.velocity,\n"
         "                              comp.plate.velocity), 0.0)\n"
         "        ) if False else comp.plate.velocity * 0.5\n"),
    ])
    fired = None
    try:
        run_world(tam, [('A', 0.0)], ticks=6)
    except ValueError as exc:
        fired = str(exc)
    require_(fired is not None,
             'F4_not_caught:' + repr(fired))
    arg['F4'] = {'refusal': fired}


@check('F5_convergence_gate_disabled_fires')
def f5(arg):
    tam = load_tampered('F5', [
        ("        for iteration in range(GS_CAP):",
         "        for iteration in range(1):"),
    ])
    fired = None
    try:
        run_world(tam, [('A', 0.0)], ticks=4)
    except ValueError as exc:
        fired = str(exc)
    require_(fired == 'convergence_gate_not_met',
             'F5_gate_did_not_fire:' + repr(fired))
    arg['F5'] = {'refusal': fired}


def main():
    results = {}
    failures = []
    # P7 re-runs the experiments (determinism) and refreshes the receipt;
    # the receipt-reading checks P5/P6 must run after it.
    order = ['P1_input_pins', 'P2_declared_order_guard',
             'P3_single_owner_ast', 'P4_world_state_is_owned',
             'P7_determinism_two_fresh_runs_byte_identical',
             'P8_regressions_M03_M04_M05_M06_green',
             'P5_receipt_claims_replay', 'P6_state_document_m01',
             'F1_hidden_coupling_cross_wire_caught_by_independence_oracle',
             'F2_ordering_swap_caught_by_declared_order_check',
             'F3_mixed_tick_state_caught',
             'F4_separate_pass_overwrites_motion_caught',
             'F5_convergence_gate_disabled_fires']
    by_name = {name: (fn, arg_val) for name, fn, arg_val in CHECKS}
    missing = [n for n in by_name if n not in order]
    require_(not missing, 'unordered_checks:' + repr(missing))
    for name in order:
        fn, arg_val = by_name[name]
        arg = {} if arg_val is None else arg_val
        try:
            fn(arg)
            results[name] = {'ok': True, **arg}
            print('PASS', name)
        except Exception as exc:  # noqa: BLE001 - falsifier log needs all
            results[name] = {'ok': False, 'error': repr(exc)}
            failures.append(name)
            print('FAIL', name, repr(exc))
    receipt = {
        'task': 'MAT2-M07', 'planning_id': 'M07',
        'candidate_revision': 'integrated_step.py sha256 '
                              + iw.sha256_file(HERE / 'integrated_step.py'),
        'criteria_sha256': 'ff18b443b97f2b3947cc993ff64175a9e848fc6d806ed90b'
                           'd719fa2bd24e87b4',
        'attempt_id': 'cc584d2e1e7c46de80bacbaf7ba12f77',
        'checks': results,
        'failures': failures,
        'all_green': not failures,
    }
    log_path = SCRATCH / 'FALSIFIER_LOG.json'
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(json.dumps(
        {'tampered_copies': TAMPER_LOG, 'discarded_after': True,
         'log': 'tampered copies are attempt-scratch only, never committed'},
        indent=1) + '\n', encoding='utf-8')
    (HERE / 'test_receipt.json').write_text(
        json.dumps(receipt, indent=1, ensure_ascii=False, sort_keys=True)
        + '\n', encoding='utf-8')
    # discard the tampered copies (logged above)
    for item in TAMPER_LOG:
        path = pathlib.Path(item['file'])
        if path.exists():
            path.unlink()
    print('test receipt:', HERE / 'test_receipt.json')
    print('falsifier log:', log_path)
    print('failures:', failures)
    return 0 if not failures else 1


if __name__ == '__main__':
    sys.exit(main())
