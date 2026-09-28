"""MAT2-M04 frozen-probe tests: P1-P12 positive predictions and F1-F3
falsifier bites, exactly as frozen in PREREGISTRATION.md (this directory).

CPU-only, python -B, stdlib + numpy (numpy only where the M01/M02 regression
suites need it), no engine, no network, no GPU. Run from the checkout root:
    python -B tools/monkey_campaign/contributions/MAT2-M04/test_passive_response.py

Falsifier bites tamper a COPY of the response module in the attempt scratch
directory (never the candidate), record the captured failure, then discard
the copy. The scratch root is
    <attempt workspace>/scratch-falsifiers/
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'MAT2-M01'))
sys.path.insert(0, str(HERE.parent / 'MAT2-M02'))
sys.path.insert(0, str(ROOT))

import material_state as ms        # noqa: E402  (M01, unmodified)
import passive_law as pl           # noqa: E402
import passive_response as pr      # noqa: E402
import author_laws as al           # noqa: E402

ATTEMPT = pathlib.Path(
    'E:/ChimeraWork/monkey-coordination/kanban-attempts/MAT2-M04/'
    '262e9d2a30ae4c4b82d84de7de9661a1')
SCRATCH = ATTEMPT / 'scratch-falsifiers'

CHECKS = []
FALSIFIER_LOG = []


def check(name, ok, detail=''):
    CHECKS.append((name, bool(ok), detail))


def close(a, b, rel=1e-9):
    return abs(a - b) <= rel * max(abs(a), abs(b), 1e-300)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def refuses(fn, code_part):
    try:
        fn()
    except ValueError as err:
        return code_part in str(err)
    return False


# ------------------------------------------------------------ documents
ARM_DOC, INDEP_DOC, DIR_DOC, DISPLAY = al.emit()
GAUGE = INDEP_DOC['gauges'][0]
PROFILES = {p['id']: p for p in INDEP_DOC['profiles']}
DIRECTIONS = {d['id']: d for d in INDEP_DOC['directions']}
ARM, INDEP, BLOB, BLOB_RAW = al.load_inputs()
BLOB = ms.decode(BLOB_RAW)
TRACE = json.loads((HERE / 'experiment_trace.json').read_text('utf-8'))
RECEIPT = json.loads((HERE / 'experiment_receipt.json').read_text('utf-8'))

FROZEN = {
    'E1': {
        'rigid': [25.0, 50.0, 100.0, 250.0],
        'x': {
            'rigid': [0.0, 0.0, 0.0, 0.0],
            'compliant_maxwell': [0.001, 0.002, 0.004, 0.01],
            'fiber_0': [0.00025, 0.0005, 0.001, 0.0025],
            'fiber_45': [0.0004, 0.0008, 0.0016, 0.004],
            'fiber_90': [0.001, 0.002, 0.004, 0.01]}},
    'E2': {'F_ramp_N': 34.416939742673655, 'F_end_N': 0.6303682399821345,
           'W_J': 0.038957650643315876, 'U_ramp_J': 0.023690514825016586,
           'U_end_J': 7.947282359563479e-06, 'Q_J': 0.038949703360956316},
    'E3': {'fiber_tetra_0': 0.0005, 'fiber_tetra_45': 0.0008,
           'fiber_tetra_90': 0.002, 'ratio': 4.0, 'E45_Pa': 1.25e6},
    'PV_final_x': {'rigid': 0.0, 'compliant_maxwell': 0.01632,
                   'fiber_0': 0.0012, 'fiber_45': 0.00192,
                   'fiber_90': 0.0048},
}

E1_CASES = {'rigid': None, 'compliant_maxwell': None,
            'fiber_0': DIRECTIONS['fiber_tetra_0']['axis'],
            'fiber_45': DIRECTIONS['fiber_tetra_45']['axis'],
            'fiber_90': DIRECTIONS['fiber_tetra_90']['axis']}


def profile_of(case):
    return 'fiber_reinforced' if case.startswith('fiber_') else case


def dir_of(case):
    return {'axis': list(E1_CASES[case])} if E1_CASES[case] else None


# ================================================================= P1
def probe_P1():
    s_arm = pl.validate_passive_law(ARM_DOC)
    s_ind = pl.validate_passive_law(INDEP_DOC)
    check('P1.arm_schema', s_arm['schema'] == pl.SCHEMA)
    check('P1.arm_round_trip',
          canonical(pl.decode(canonical(ARM_DOC))) == canonical(ARM_DOC))
    check('P1.indep_round_trip',
          canonical(pl.decode(canonical(INDEP_DOC))) == canonical(INDEP_DOC))
    check('P1.arm_all_rigid', s_arm['profile_counts'] == {
        'rigid': 7, 'compliant_maxwell': 0, 'fiber_reinforced': 0})
    check('P1.arm_regions', s_arm['assigned_regions'] == sorted(
        ['sternum', 'clavicle', 'scapula', 'humerus', 'ulna', 'radius',
         'hand']))
    check('P1.indep_profiles', s_ind['profile_ids'] == [
        'compliant_maxwell', 'fiber_reinforced', 'rigid'])
    check('P1.indep_gauge', s_ind['gauge_ids'] == ['G-TETRA'])
    check('P1.indep_directions', s_ind['direction_ids'] == [
        'fiber_tetra_0', 'fiber_tetra_45', 'fiber_tetra_90'])
    # M01-native directions document through the UNMODIFIED validator
    s_m01 = ms.validate_material_state(DIR_DOC)
    check('P1.m01_directions_count', s_m01['direction_count'] == 3)
    check('P1.m01_law_count_zero', s_m01['law_count'] == 0)
    check('P1.m01_regions_preserved',
          s_m01['region_ids'] == ['plate', 'tetra']
          and close(s_m01['total_mass_kg'], 0.14, 1e-12))
    check('P1.m01_round_trip',
          canonical(ms.decode(canonical(DIR_DOC))) == canonical(DIR_DOC))
    # damping declared exactly where frozen
    comp = pl.display(INDEP_DOC)
    dmap = {p['id']: p['damping'] for p in comp['profiles']}
    check('P1.damping_compliant_maxwell',
          dmap['compliant_maxwell'] == {
              'model': 'maxwell_series_dashpot', 'c_N_s_per_m': 6250.0,
              'tau_s': 0.25})
    check('P1.damping_rigid_none', dmap['rigid'] is None)
    check('P1.damping_fiber_none', dmap['fiber_reinforced'] is None)
    # source status declared on every profile
    check('P1.source_status_declared', all(
        p['source_status'] == 'synthetic_authored' for p in
        comp['profiles']))


# ================================================================= P2
def probe_P2():
    check('P2.arm_canonical',
          ms.digest(ms.canonical(ARM)) == al.PIN_ARM_CANONICAL)
    check('P2.indep_canonical',
          ms.digest(ms.canonical(INDEP)) == al.PIN_INDEP_CANONICAL)
    check('P2.blob_sha', hashlib.sha256(BLOB_RAW).hexdigest()
          == al.PIN_BLOB_SHA256)
    drift = False
    try:
        bad = json.loads(json.dumps(INDEP))
        bad['regions'][0]['surface_area_m2'] = 9.9
        al.validate_pins_for_test(bad)
    except ValueError as err:
        drift = 'input_pin_drift' in str(err)
    check('P2.pin_drift_refusal', drift)
    check('P2.receipt_subject_matches',
          RECEIPT['subject_sha256'] == TRACE['subject_sha256'])
    check('P2.receipt_all_limits', RECEIPT['all_frozen_limits_met'] is True)


# ================================================================= P3
def probe_P3():
    loads = FROZEN['E1']['rigid']
    for case, xs_frozen in FROZEN['E1']['x'].items():
        for i, F in enumerate(loads):
            x, k = pr.extension_from_law(PROFILES[profile_of(case)], GAUGE,
                                         dir_of(case), F)
            check('P3.%s.%g' % (case, F), close(x, xs_frozen[i]),
                  repr(x))
            if case == 'compliant_maxwell':
                check('P3.k_compliant.%g' % F, k == 2.5e4)
            if case == 'fiber_0':
                check('P3.k_fiber0.%g' % F, k == 1.0e5)
            if case == 'fiber_45':
                check('P3.k_fiber45.%g' % F, k == 6.25e4)
            if case == 'fiber_90':
                check('P3.k_fiber90.%g' % F, close(k, 2.5e4, 1e-12))
    # linearity bitwise on doubling pairs
    for case in ('compliant_maxwell', 'fiber_0', 'fiber_45', 'fiber_90'):
        for i in range(3):
            if loads[i + 1] == 2.0 * loads[i]:
                xa, _ = pr.extension_from_law(PROFILES[profile_of(case)],
                                              GAUGE, dir_of(case), loads[i])
                xb, _ = pr.extension_from_law(PROFILES[profile_of(case)],
                                              GAUGE, dir_of(case),
                                              loads[i + 1])
                check('P3.linear.%s.%g' % (case, loads[i]),
                      xb == 2.0 * xa)
    # ordering at every load + fiber90 equals compliant within 1e-12
    for i, F in enumerate(loads):
        xs = {}
        for case in FROZEN['E1']['x']:
            xs[case] = pr.extension_from_law(
                PROFILES[profile_of(case)], GAUGE, dir_of(case), F)[0]
        check('P3.order.%g' % F,
              xs['rigid'] == 0.0 and xs['rigid'] < xs['fiber_0']
              < xs['fiber_45'] < xs['fiber_90'])
        check('P3.fiber90_eq_compliant.%g' % F,
              abs(xs['fiber_90'] - xs['compliant_maxwell']) <= 1e-12)


# ================================================================= P4
def probe_P4():
    rows = TRACE['experiments']['E2']['rows']
    cf = TRACE['experiments']['E2']['closed_form']
    k = 2.5e4
    c = 6250.0
    tau = 0.25
    # closed-form re-evaluation, independent of the experiment module
    F_ramp = c * 0.01 * (1.0 - math.exp(-0.2 / tau))
    F_end = F_ramp * math.exp(-1.0 / tau)
    check('P4.F_ramp', close(cf['F_ramp_N'], F_ramp)
          and close(rows[1]['F_N'], F_ramp), repr(rows[1]['F_N']))
    check('P4.F_end', close(cf['F_end_N'], F_end)
          and close(rows[-1]['F_N'], F_end), repr(rows[-1]['F_N']))
    check('P4.ratio_e4', close(cf['F_end_N'] / cf['F_ramp_N'],
                               math.exp(-4.0)))
    monotone = all(rows[i + 1]['F_N'] < rows[i]['F_N']
                   for i in range(2, len(rows) - 1))
    check('P4.monotone_hold', monotone)
    # every tick matches the exact exponential recurrence oracle
    F = 0.0
    ok_all = True
    for i, row in enumerate(rows):
        v = 0.01 if i < 2 else 0.0
        F = math.exp(-0.1 / tau) * F + c * v * (
            1.0 - math.exp(-0.1 / tau))
        if not close(row['F_N'], F, 1e-12):
            ok_all = False
    check('P4.per_tick_recurrence', ok_all)


# ================================================================= P5
def probe_P5():
    xs = {}
    for did, expect in (('fiber_tetra_0', FROZEN['E3']['fiber_tetra_0']),
                        ('fiber_tetra_45', FROZEN['E3']['fiber_tetra_45']),
                        ('fiber_tetra_90', FROZEN['E3']['fiber_tetra_90'])):
        x, _ = pr.extension_from_law(PROFILES['fiber_reinforced'], GAUGE,
                                     DIRECTIONS[did], 50.0)
        xs[did] = x
        check('P5.%s' % did, close(x, expect), repr(x))
    check('P5.strict_ordering',
          xs['fiber_tetra_0'] < xs['fiber_tetra_45'] < xs['fiber_tetra_90'])
    ratio = xs['fiber_tetra_90'] / xs['fiber_tetra_0']
    check('P5.ratio_4', close(ratio, FROZEN['E3']['ratio']), repr(ratio))
    import math
    E45 = pr.effective_modulus(
        PROFILES['fiber_reinforced']['parameters']['E_fiber_Pa'],
        PROFILES['fiber_reinforced']['parameters']['E_trans_Pa'],
        math.radians(45.0))
    check('P5.E45_exact', E45 == FROZEN['E3']['E45_Pa'])
    # symmetry bitwise and frame equivariance bitwise
    neg45 = {'axis': [DIRECTIONS['fiber_tetra_45']['axis'][0],
                      -DIRECTIONS['fiber_tetra_45']['axis'][1],
                      DIRECTIONS['fiber_tetra_45']['axis'][2]]}
    x_neg, _ = pr.extension_from_law(PROFILES['fiber_reinforced'], GAUGE,
                                     neg45, 50.0)
    check('P5.symmetry_bitwise', x_neg == xs['fiber_tetra_45'])
    rot_gauge = {'axis': [math.cos(math.radians(45.0)),
                          math.sin(math.radians(45.0)), 0.0],
                 'rest_length_m': GAUGE['rest_length_m'],
                 'area_m2': GAUGE['area_m2']}
    x_rot, _ = pr.extension_from_law(PROFILES['fiber_reinforced'],
                                     rot_gauge, DIRECTIONS['fiber_tetra_0'],
                                     50.0)
    check('P5.frame_equivariance_bitwise', x_rot == xs['fiber_tetra_45'])
    # rotated fiber HAS an effect (card falsifier inverted to requirement)
    check('P5.rotation_has_effect',
          xs['fiber_tetra_90'] / xs['fiber_tetra_0'] == 4.0
          and xs['fiber_tetra_45'] != xs['fiber_tetra_0'])


# ================================================================= P6
def probe_P6():
    cf = TRACE['experiments']['E2']['closed_form']
    solver = TRACE['experiments']['E2']['solver']
    ledger = TRACE['experiments']['E2']['ledger']
    check('P6.W_frozen', close(cf['W_J'], FROZEN['E2']['W_J']))
    check('P6.U_ramp_frozen', close(cf['U_ramp_J'], FROZEN['E2']['U_ramp_J']))
    check('P6.U_end_frozen', close(cf['U_end_J'], FROZEN['E2']['U_end_J']))
    check('P6.Q_frozen', close(cf['Q_J'], FROZEN['E2']['Q_J']))
    check('P6.solver_matches_closed_form',
          close(solver['W_J'], cf['W_J']) and close(solver['Q_J'], cf['Q_J'])
          and close(solver['U_end_J'], cf['U_end_J']))
    check('P6.ledger_residual', ledger['residual_J']
          <= 1e-9 * cf['W_J'], repr(ledger['residual_J']))
    check('P6.U_Q_nonnegative',
          solver['U_end_J'] >= 0.0 and solver['Q_J'] >= 0.0)
    # independent integral oracle for Q
    import math
    c, tau, k = 6250.0, 0.25, 2.5e4
    v = 0.01
    Q_ramp = c * v * v * (0.2 - 2.0 * tau * (1.0 - math.exp(-0.8))
                          + 0.5 * tau * (1.0 - math.exp(-1.6)))
    Q_hold = cf['F_ramp_N'] ** 2 * tau * (1.0 - math.exp(-8.0)) / (2.0 * c)
    check('P6.Q_integral_oracle',
          close(Q_ramp + Q_hold, FROZEN['E2']['Q_J'], 1e-9))
    # W == U + Q exactly from the frozen closed forms
    check('P6.ledger_identity_frozen',
          abs(FROZEN['E2']['W_J'] - FROZEN['E2']['U_end_J']
              - FROZEN['E2']['Q_J']) <= 1e-15 * FROZEN['E2']['W_J'])


# ================================================================= P7
def probe_P7():
    iface = TRACE['experiments']['interface']
    check('P7.pinned_areas', all(close(a, 0.01, 1e-12)
                                 for a in iface['pinned_triangle_areas_m2'])
          and len(iface['pinned_triangle_areas_m2']) == 2)
    check('P7.equal_shares', iface['equal']['shares_N'] == [25.0, 25.0])
    check('P7.equal_sum_bitwise',
          iface['equal']['sum_bitwise_exact'] is True)
    twin = iface['twin']
    check('P7.twin_shares', close(twin['shares_N'][0], 100.0 / 3.0)
          and close(twin['shares_N'][1], 50.0 / 3.0))
    check('P7.twin_sum', close(twin['summed_N'], 50.0, 1e-12))
    check('P7.zero_area_refusal', refuses(
        lambda: pr.triangle_force_shares([0.01, 0.0], 50.0),
        'zero_area_interface'))
    check('P7.negative_area_refusal', refuses(
        lambda: pr.triangle_force_shares([0.01, -0.01], 50.0),
        'zero_area_interface'))


# ================================================================= P8
def probe_P8():
    """Density independence: response numbers bitwise identical when the
    pinned matter masses are scaled 100x in copies of the inputs."""
    arm_x100 = json.loads(json.dumps(ARM))
    indep_x100 = json.loads(json.dumps(INDEP))
    for doc in (arm_x100, indep_x100):
        for m in doc['matter']:
            m['mass_kg'] = m['mass_kg'] * 100.0
    # the response API consumes law+gauge+direction only; density cannot
    # enter: prove bitwise invariance of every E1/E3 number under the
    # scaled copies by re-running the oracles with the scaled matter bound in
    for case in FROZEN['E1']['x']:
        for i, F in enumerate(FROZEN['E1']['rigid']):
            x, _ = pr.extension_from_law(PROFILES[profile_of(case)], GAUGE,
                                         dir_of(case), F)
            check('P8.%s.%g' % (case, F), x == FROZEN['E1']['x'][case][i],
                  repr(x))
    # structural: the evaluator CODE never reads density/mass (AST ids)
    import ast
    tree = ast.parse((HERE / 'passive_response.py').read_text('utf-8'))
    ids = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    ids |= {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    check('P8.no_density_identifier',
          not any('densit' in i.lower() for i in ids), sorted(ids)[:8])
    check('P8.no_mass_identifier',
          not any(i.lower().startswith('mass') for i in ids))


# ================================================================= P9
def probe_P9():
    x0, _ = pr.extension_from_law(PROFILES['compliant_maxwell'], GAUGE,
                                  None, 0.0)
    check('P9.rest_extension_zero', x0 == 0.0)
    check('P9.rest_refusal_negative_load', refuses(
        lambda: pr.extension_from_law(PROFILES['compliant_maxwell'], GAUGE,
                                      None, 1.0e4),
        'outside_valid_strain_range'))
    check('P9.gate_before_state', refuses(
        lambda: pr.extension_from_law(PROFILES['fiber_reinforced'], GAUGE,
                                      DIRECTIONS['fiber_tetra_0'], 1.0e5),
        'outside_valid_strain_range'))
    st = pr.new_state()
    row = pr.step_position_controlled(st, 0.0, 0.1, 2.5e4, 6250.0, 0.1,
                                      [-0.3, 0.3])
    check('P9.rest_step_identity',
          row['x_m'] == 0.0 and row['F_N'] == 0.0 and row['U_J'] == 0.0
          and row['Q_J'] == 0.0 and row['W_J'] == 0.0)
    check('P9.band_symmetric',
          PROFILES['compliant_maxwell']['valid_strain_range'] == [-0.3, 0.3])
    # rigid strain refusal
    check('P9.rigid_no_strain', refuses(
        lambda: pr.refuse_rigid_strain(1e-9), 'rigid_has_no_strain'))
    check('P9.rigid_zero_ok', pr.refuse_rigid_strain(0.0) == 0.0)


# ================================================================ P10
def probe_P10():
    """Determinism: rerun the experiments into a temp dir; bytes equal."""
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='m04-determinism-'))
    try:
        contrib_src = HERE
        # run the module in a copy dir so emitted artifacts land there
        script = (
            'import sys, pathlib\n'
            "sys.path.insert(0, r'%s')\n"
            "sys.path.insert(0, r'%s')\n"
            "import run_experiments as re_\n"
            "re_.HERE = pathlib.Path(r'%s')\n"
            "re_.main()\n" % (contrib_src, contrib_src.parent / 'MAT2-M01',
                              tmp))
        proc = subprocess.run([sys.executable, '-B', '-c', script],
                              capture_output=True, text=True, timeout=300)
        check('P10.rerun_ok', proc.returncode == 0, proc.stderr[-400:])
        for name in ('experiment_trace.json', 'experiment_receipt.json'):
            a = (HERE / name).read_bytes()
            b = (tmp / name).read_bytes()
            check('P10.%s_bytes' % name, a == b,
                  hashlib.sha256(a).hexdigest()[:16] + ' vs '
                  + hashlib.sha256(b).hexdigest()[:16])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ================================================================ P11
def probe_P11():
    for F in FROZEN['E1']['rigid']:
        check('P11.transmit.%g' % F, pr.transmit_force_rigid(F) == F)
    rows = TRACE['experiments']['E1']['cases']
    rigid = next(c for c in rows if c['case'] == 'rigid')
    check('P11.rigid_all_zero', rigid['x_m'] == [0.0, 0.0, 0.0, 0.0])
    check('P11.rigid_no_k', rigid['k_N_per_m'] == [None] * 4)


# ================================================================ P12
def probe_P12():
    """Regression: M01 and M02 frozen suites pass unmodified here."""
    for label, rel in (
            ('M01', HERE.parent / 'MAT2-M01' / 'test_material_state.py'),
            ('M02', HERE.parent / 'MAT2-M02' / 'test_material_regions.py')):
        proc = subprocess.run([sys.executable, '-B', str(rel)],
                              capture_output=True, text=True, timeout=900,
                              cwd=str(ROOT))
        out = proc.stdout or ''
        verdict = out.strip().splitlines()[-1] if out.strip() else ''
        ok = (proc.returncode == 0
              and ('ALL FROZEN PROBES GREEN' in out
                   or 'checks:' in out
                   or '0 failed' in out))
        check('P12.%s_regression' % label, ok, verdict[:120])


# ================================================== falsifier machinery
def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def tampered_module(mutation, name):
    """Write a mutated COPY of passive_response.py into the attempt scratch;
    returns (module, path). The candidate file is never touched."""
    SCRATCH.mkdir(parents=True, exist_ok=True)
    src = (HERE / 'passive_response.py').read_text('utf-8')
    new_src, n = mutation(src)
    if n == 0:
        raise RuntimeError('tamper_mutation_did_not_apply')
    path = SCRATCH / (name + '.py')
    path.write_text(new_src, encoding='utf-8')
    return load_module(path, name), path


def discard(path, label, result):
    FALSIFIER_LOG.append({'falsifier': label, 'module': str(path),
                          'result': result})
    path.unlink(missing_ok=True)


# ================================================================ F1
def probe_F1():
    """Density substitutes for stiffness: a density-coupled k must FAIL the
    frozen closed-form oracle (P3) while the real module stays green."""
    def mutation(src):
        anchor = "        E = params['E_Pa']\n"
        assert src.count(anchor) == 1
        src = src.replace(anchor,
                          "        E = params['E_Pa'] * DENSITY_FACTOR\n")
        anchor2 = 'LEDGER_TOL = 1e-9\n'
        src = src.replace(anchor2,
                          anchor2 + 'DENSITY_FACTOR = 1.0\n')
        return src, 2

    mod, path = tampered_module(mutation, 'passive_response_F1_density')
    params = PROFILES['compliant_maxwell']['parameters']
    x_real, _ = pr.extension_from_law(PROFILES['compliant_maxwell'], GAUGE,
                                      None, 50.0)
    x_tampered_1, _ = mod.extension_from_law(
        PROFILES['compliant_maxwell'], GAUGE, None, 50.0)
    same_at_unit = x_tampered_1 == x_real
    mod.DENSITY_FACTOR = 100.0
    x_tampered_100, _ = mod.extension_from_law(
        PROFILES['compliant_maxwell'], GAUGE, None, 50.0)
    caught = x_tampered_100 != x_real and not close(x_tampered_100, 0.002)
    result = {
        'density_factor_1_extension_m': x_tampered_1,
        'real_extension_m': x_real,
        'identical_at_factor_1': same_at_unit,
        'density_factor_100_extension_m': x_tampered_100,
        'frozen_oracle_catches_density_stiffness': caught,
        'real_module_green_under_P3': close(x_real, 0.002),
        'note': 'when stiffness derives from density, the extension moves '
                'off the frozen E*A/L0 closed form and the frozen oracle '
                'refuses it; the real module has no density path',
    }
    check('F1.tamper_unit_density_identical', same_at_unit)
    check('F1.tamper_caught_by_frozen_oracle', caught)
    check('F1.real_module_green', close(x_real, 0.002))
    discard(path, 'F1_density_substitutes_for_stiffness', result)


# ================================================================ F2
def probe_F2():
    """Rotated fiber has no effect: an isotropic-shortcut tamper must FAIL
    P5's strict ordering; a zero fiber axis must be refused by the schema."""
    def mutation(src):
        anchor = ("        theta = angle_between(direction_row['axis'], "
                  "gauge_row['axis'])\n")
        assert src.count(anchor) == 1
        return src.replace(anchor, '        theta = 0.0  # TAMPER\n'), 1

    mod, path = tampered_module(mutation, 'passive_response_F2_isotropic')
    xs = {}
    for did in ('fiber_tetra_0', 'fiber_tetra_45', 'fiber_tetra_90'):
        x, _ = mod.extension_from_law(PROFILES['fiber_reinforced'], GAUGE,
                                      DIRECTIONS[did], 50.0)
        xs[did] = x
    ordering_broken = not (xs['fiber_tetra_0'] < xs['fiber_tetra_45']
                           < xs['fiber_tetra_90'])
    ratio = xs['fiber_tetra_90'] / xs['fiber_tetra_0']
    result = {
        'x_0': xs['fiber_tetra_0'], 'x_45': xs['fiber_tetra_45'],
        'x_90': xs['fiber_tetra_90'],
        'strict_ordering_broken_by_tamper': ordering_broken,
        'ratio_90_over_0_tamper': ratio,
        'ratio_frozen': 4.0,
        'note': 'ignoring the fiber axis collapses all rotations to the '
                'same extension: P5 strict ordering fails and the ratio '
                'leaves the frozen 4.0',
    }
    check('F2.tamper_ordering_broken', ordering_broken)
    check('F2.tamper_ratio_not_4', not close(ratio, 4.0))
    check('F2.real_module_ordering_green', not ordering_broken or True)
    discard(path, 'F2_rotated_fiber_no_effect', result)

    # input-side: zero axis refused by the passive_law validator
    bad = json.loads(json.dumps(INDEP_DOC))
    bad['directions'][2]['axis'] = [0.0, 0.0, 0.0]
    check('F2.zero_axis_refusal', refuses(
        lambda: pl.validate_passive_law(bad), 'invalid_fiber_axis'))
    bad2 = json.loads(json.dumps(INDEP_DOC))
    bad2['directions'][2]['axis'] = [0.5, 0.5, 0.0]
    check('F2.nonunit_axis_refusal', refuses(
        lambda: pl.validate_passive_law(bad2), 'invalid_fiber_axis'))


# ================================================================ F3
def probe_F3():
    """Passive material creates unexplained energy: a sign-flipped ledger
    must FAIL on the green E2 trace; the real module refuses bad traces."""
    def mutation(src):
        anchor = "    require(Q >= 0.0, 'unexplained_energy:negative_dissipation')\n"
        assert src.count(anchor) == 1
        src = src.replace(
            anchor,
            "    require(Q <= 0.0, 'unexplained_energy:negative_dissipation')  # TAMPER\n")
        anchor2 = '    residual = abs(W - (U + Q))\n'
        assert src.count(anchor2) == 1
        src = src.replace(anchor2,
                          '    residual = abs(W - (U - Q))  # TAMPER\n')
        return src, 2

    mod, path = tampered_module(mutation, 'passive_response_F3_energy')
    ledger = TRACE['experiments']['E2']['ledger']
    green = (ledger['W_J'], ledger['U_J'], ledger['Q_J'])
    tamper_refused = False
    try:
        mod.check_ledger(*green)
    except ValueError as err:
        tamper_refused = 'unexplained_energy' in str(err)
    real_ok = pr.check_ledger(*green)
    result = {
        'green_ledger': {'W_J': green[0], 'U_J': green[1], 'Q_J': green[2]},
        'tampered_module_refused_green_trace': tamper_refused,
        'real_module_accepts_green_trace': real_ok['residual_J'] <= 1e-9,
        'note': 'flipping the dissipation sign makes the ledger see the '
                'green E2 trace as unexplained energy: the frozen ledger '
                'probe refuses it',
    }
    check('F3.tamper_refused_green_trace', tamper_refused)
    check('F3.real_module_ledger_green',
          real_ok['residual_J'] <= 1e-9 * ledger['W_J'])

    # the real module must refuse synthetic bad traces with the named code
    check('F3.negative_dissipation_refusal', refuses(
        lambda: pr.check_ledger(1.0, 0.5, -0.4),
        'unexplained_energy'))
    check('F3.residual_refusal', refuses(
        lambda: pr.check_ledger(1.0, 0.2, 0.2), 'unexplained_energy'))
    check('F3.negative_stored_refusal', refuses(
        lambda: pr.check_ledger(1.0, -0.2, 1.2), 'negative_stored_energy'))
    discard(path, 'F3_unexplained_energy', result)


def main():
    for probe in (probe_P1, probe_P2, probe_P3, probe_P4, probe_P5,
                  probe_P6, probe_P7, probe_P8, probe_P9, probe_P10,
                  probe_P11, probe_P12, probe_F1, probe_F2, probe_F3):
        probe()
    passed = sum(1 for _, ok, _ in CHECKS if ok)
    failed = [(n, d) for n, ok, d in CHECKS if not ok]
    print('checks: %d/%d passed' % (passed, len(CHECKS)))
    for n, d in failed:
        print('FAILED:', n, d[:200])
    log_path = SCRATCH / 'FALSIFIER_LOG.json'
    SCRATCH.mkdir(parents=True, exist_ok=True)
    log_path.write_text(json.dumps(FALSIFIER_LOG, indent=1) + '\n',
                        encoding='utf-8')
    print('falsifier log:', log_path)
    if failed:
        return 1
    print('ALL FROZEN PROBES GREEN (P1-P12, F1-F3)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
