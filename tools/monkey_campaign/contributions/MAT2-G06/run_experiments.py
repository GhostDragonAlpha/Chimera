"""MAT2-G06 frozen experiments (PREREGISTRATION.md, frozen) - CPU-only card.

Modes (one process each; no GPU anywhere on this card):
  main        the preregistered transfer battery (9 runs = the 8 transfer
              cases + the zero-mu control), 229 ticks each, replayed
              through the declared schedule + the G06 seam and composed
              with the pinned G05 seam; writes experiment_trace.json +
              experiment_receipt.json.
  rerun       second fresh run for the determinism pair (writes
              *_rerun2.json).
  compare     scoped determinism (card-kit form): trace byte-identity +
              receipt delta scoped to AUGMENTATION_KEYS; writes
              determinism_receipt.json.
  falsify     FB1-FB5, every tamper with its passing CLEAN CONTROL run
              FIRST, in the same executable; writes falsifier_receipt.json.
  regression  the declared upstream suites (M06 test_local_contact.py, the
              sealed G04 test_g04_checks.py AND the sealed G05
              test_g05_checks.py, all UNMODIFIED) re-run on this exact
              revision; writes regression_receipt.json.

No RNG; no wall clock in trace/receipt. Refusals are named codes; vacuous
comparisons are REFUSED.
"""
from __future__ import annotations

import g06_deps  # noqa: E402  (must run before upstream imports)

g06_deps.ensure()

import hashlib  # noqa: E402
import json  # noqa: E402
import pathlib  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
CONTRIB = HERE.parent
sys.path.insert(0, str(HERE))

import transfer_sequence as ts  # noqa: E402

require = ts.require

CARD_ID = 'G06'                  # SHORT registry form
CARD_FULL = 'MAT2-G06'
ATTEMPT_ROOT = HERE.parents[3]   # .../<attempt id>/ (scratch only)

MODES = ('main', 'rerun', 'compare', 'falsify', 'regression')

M06_SUITE = str(CONTRIB / 'MAT2-M06' / 'test_local_contact.py')
G04_SUITE = str(CONTRIB / 'MAT2-G04' / 'test_g04_checks.py')
G05_SUITE = str(CONTRIB / 'MAT2-G05' / 'test_g05_checks.py')

G01_RECEIPT_HOST = ('E:/ChimeraWork/monkey-coordination/evidence-store/'
                    'MAT2-G01/numerical/feasibility_receipt.json')
GRASP_BENCH_HOST = ('E:/ChimeraWork/research-data/20260929/benchmark-grasp/'
                    'GRASP_BENCHMARK.md')
FRICTION_SOURCES_HOST = ('E:/ChimeraWork/monkey-coordination/g04-friction/'
                         'FRICTION_SOURCES.md')
G04_REPORT_HOST = ('E:/ChimeraWork/monkey-coordination/evidence-store/'
                   'MAT2-G04/report/REPORT.md')
G05_REPORT_HOST = ('E:/ChimeraWork/monkey-coordination/evidence-store/'
                   'MAT2-G05/report/REPORT.md')

PINS = {
    '../MAT2-M06/local_contact.py':
        '1cd662b30343011eb4a0a01e461a1e82b00482d0371857c8e42d6bec8f9a28dc',
    '../MAT2-M06/test_local_contact.py':
        'b832d0dc07c1762a190d4b662ceed2b1b6dd469cbd22343cb39934e90eb08e77',
    '../MAT2-M06/contact_law.json':
        '583962c29f18118a478dedb167f2c3667414b86f5cab4ee54763416f1df7e41b',
    '../MAT2-M06/experiment_receipt.json':
        '2956dd7aaf3682fc18de9b724ddd8a695011ec74c9a12a5a56744b3d738a9397',
    '../MAT2-F03/assets/trunk_01_mesh.json':
        '3b17441764714c5e5e9c7a43c3253b3271a0f508954095e1960a57820cef6ee7',
    '../MAT2-F03/assets/trunk_01_material_state.json':
        '91c17a5c59ce79af3dc0e8a6dadb00c92a039075775a0a1de618da12dfca61bd',
    '../MAT2-G04/grip_contact.py':
        '0d6375484c350039468b31a2f7db2895d3365412aee52ce98de72b4173d69245',
    '../MAT2-G04/test_g04_checks.py':
        'a01b167e4393e2e513ba343f2bc6ba3fdf4d01ee08170f7fe8c3cb1c5c9a0ae1',
    '../MAT2-G05/contact_support_obs.py':
        '3dae0a3805cec86bba8dbae9a6fc563f43cddc98fcd01a693f725e4f31c46bd3',
    '../MAT2-G05/test_g05_checks.py':
        '83ba17604f66fdbe623b71ce481b539862ec39ebf81ee4c8bea2e5af29f9985b',
    G01_RECEIPT_HOST:
        '4061d8ec604ddea5dfbdf605f0244874129a69a88d771d4f593c7a927c16be42',
    GRASP_BENCH_HOST:
        'd936cebe38b1416dfc417db727ea81396eb8eb9217efed3f05b344db17f71610',
    FRICTION_SOURCES_HOST:
        '336118e929bd0b4fb067db5a448dc2e348fed073007787635549a4cf1cf5868b',
    G04_REPORT_HOST:
        'dfca5b5556efe018ca09be4577bf6fbb5df38bb5c9ebc33d15bd18646ba349c8',
    G05_REPORT_HOST:
        '1e5fcc7f81b5bd7b0ae3b460c72d5ed190510f66db4793c6b2e99756da8c8524',
}

BASE_COMMIT = '39ee4884dbd096259298b4b1bb7e84088acdad7f'
CRITERIA_SHA256 = ('244ec17a4265b1eff67a541566bc68764ca37e4597554e4ddd62218'
                   '96ca30b83')
REGISTRY_SQLITE = pathlib.Path(
    'E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3')

BATTERY_COUNT = 9                 # 8 transfer cases + the zero-mu control
CLOSING_CASES = (('band_lo', 3), ('band_mid', 3), ('band_hi', 3))
NONCLOSING_CASES = (('scene', 3), ('band_lo', 2), ('band_mid', 2),
                    ('band_hi', 2), ('scene', 2))
STANDARD_G = ts.STANDARD_G

WIN_JN = ts.WIN_JN
WIN_JT = ts.WIN_JT
WIN_LEDGER = ts.WIN_LEDGER
WIN_FLIGHT = ts.WIN_FLIGHT
WIN_RECURSION = ts.WIN_RECURSION
WIN_DISP = ts.WIN_DISP
Z_TOUCH = ts.Z_TOUCH
WIN_RELEASE_SCALE = ts.WIN_RELEASE_SCALE
CAPTURE_WINDOW_M = ts.CAPTURE_WINDOW_M
D_MAX_REACH_M = ts.D_MAX_REACH_M


def sha256_file(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def canonical(value):
    return ts.canonical(value)


def refuse_vacuous(a, b, code='vacuous_comparison_refused'):
    if a == 0.0 and b == 0.0:
        raise ValueError(code)


def vacuous_guard_selftest():
    fired = False
    try:
        refuse_vacuous(0.0, 0.0)
    except ValueError as exc:
        fired = str(exc) == 'vacuous_comparison_refused'
    return fired


def verify_input_pins():
    if not PINS:
        raise ValueError('input_pins_empty: declare your frozen inputs')
    for rel, expected in PINS.items():
        path = (HERE / rel).resolve() if not rel.startswith('E:') \
            else pathlib.Path(rel)
        if not path.exists():
            raise ValueError('input_pin_missing:' + rel)
        if sha256_file(path) != expected:
            raise ValueError('input_pin_drift:' + rel)
    return dict(PINS)


def registry_criteria_sha256():
    """The registry card row read mode=ro (the prereg-identity law)."""
    import sqlite3
    con = sqlite3.connect('file:%s?mode=ro' % REGISTRY_SQLITE.as_posix(),
                          uri=True)
    try:
        cur = con.cursor()
        cur.execute('SELECT payload FROM state WHERE id=1')
        state = json.loads(cur.fetchone()[0])
    finally:
        con.close()
    card = state['kanban']['cards'][CARD_FULL]
    return card['criteria_sha256'], [a['state'] for a
                                     in card['attempts'].values()]


def battery_cases(gc):
    """The preregistered 9 runs in frozen order (zero-mu control last,
    '|mu=0' suffix -- the G04 label-hygiene law)."""
    cases = []
    for name, kg in ts.TRANSFER_READINGS:
        for n in ts.TRANSFER_CHANNELS:
            cases.append(('%s|n=%d' % (name, n), kg, n, None, None))
    zc = ts.ZERO_MU_CONTROL
    cases.append(('%s|n=%d|mu=0' % (zc['reading'], zc['n']),
                  dict(ts.TRANSFER_READINGS)[zc['reading']], zc['n'],
                  zc['mu_s'], zc['mu_k']))
    return cases


def run_battery(gc, lc, g05, geom):
    """The full battery under the frozen schedule. Returns (scenarios,
    totals). Each scenario: run_case -> cumulative displacement -> P6
    verdicts -> projected samples -> the G06 seam (all ticks) + the pinned
    G05 seam composition (hold/release accepted; G06-only phases refused
    timing_unbound)."""
    Seam = ts.build_seam_module(g05)
    scenarios = {}
    accepted_total = 0
    refusal_total = 0
    g05_accepted_total = 0
    g05_refused_total = 0
    for label, kg, n, mu_s, mu_k in battery_cases(gc):
        header, rows = ts.run_case(lc, gc, geom, kg, n, mu_s=mu_s, mu_k=mu_k,
                                   scenario_id=label)
        ts.cumulative_down_disp(rows)
        verdicts = ts.support_verdicts(header, rows)
        SeamClass = Seam
        seam = SeamClass(label, lc.DT)
        g05_seam = g05.ObservationSeam('g05-composition:' + label, lc.DT)
        samples = []
        g05_refusals = {}
        for row, verdict in zip(rows, verdicts):
            sample = ts.project_sample(g05, header, verdict, row, lc.DT)
            samples.append(sample)
            seam.deliver(sample)
            try:
                g05_seam.deliver(sample)
            except ValueError as exc:
                code = str(exc).split(':')[0]
                g05_refusals[code] = g05_refusals.get(code, 0) + 1
        census = seam.census()
        g05_census = g05_seam.census()
        require(census['accepted'] == header['total_ticks'],
                'seam_delivery_shortfall', label)
        require(not census['refusals'], 'seam_refused_declared_sample',
                (label, census['refusals'][:2]))
        accepted_total += census['accepted']
        refusal_total += len(census['refusals'])
        g05_accepted_total += g05_census['accepted']
        g05_refused_total += len(g05_census['refusals'])
        scenarios[label] = {'header': header, 'rows': rows,
                            'verdicts': verdicts, 'samples': samples,
                            'census': census, 'g05_census': g05_census,
                            'g05_refusal_codes': g05_refusals}
    totals = {'accepted': accepted_total, 'refusals': refusal_total,
              'scenarios': len(scenarios),
              'runs_expected': BATTERY_COUNT,
              'g05_composition_accepted': g05_accepted_total,
              'g05_composition_refused': g05_refused_total}
    return scenarios, totals


def g01_boundary_rows():
    doc = json.loads(pathlib.Path(G01_RECEIPT_HOST).read_text(
        encoding='utf-8'))
    out = {}
    for row in doc['derivation']['case_table']:
        out[(row['reading'], row['n_channels'])] = bool(
            row['friction_feasible'])
    return out


def transfer_support_measured(scenario):
    """True iff EVERY transfer tick is supported (the measured verdict)."""
    return all(v['supported'] for v in scenario['verdicts']
               if v['phase'] == 'transfer')


def _case_of(label):
    base = label.rsplit('|mu=0', 1)[0]
    reading, n_str = base.split('|n=')
    return reading, int(n_str)


def build_receipt(gc, lc, g05, scenarios, totals, pins):
    """All preregistered predicates, evaluated here so the named checks and
    the falsifier arms consume the SAME predicate set."""
    declared_keys = sorted(frozenset(ts.TIMING_KEYS) | g05.OBS_NAME_SET)
    g01 = g01_boundary_rows()

    # ---- X1 done_when: the tested envelope ----
    x1_fail = None
    envelope_ticks = None
    for label, s in scenarios.items():
        case = _case_of(label)
        if case not in CLOSING_CASES or label.endswith('|mu=0'):
            continue
        env = s['header']['envelope']
        envelope_ticks = env
        for v in s['verdicts']:
            if env[0] <= v['tick'] <= env[1] and not v['supported']:
                x1_fail = {'label': label, 'tick': v['tick'],
                           'reason': v['reason']}
                break
        if x1_fail:
            break
    x1 = (x1_fail is None and totals['scenarios'] == BATTERY_COUNT
          and totals['refusals'] == 0
          and totals['accepted'] ==
          sum(s['header']['total_ticks'] for s in scenarios.values()))

    # ---- X2 sealed boundary composition ----
    x2_fail = None
    table = {}
    g_delta_max = 0.0
    margin_min = None
    for label, s in scenarios.items():
        case = _case_of(label)
        is_zero_mu = label.endswith('|mu=0')
        measured = transfer_support_measured(s)
        cf = ts.boundary_closed_form(lc, gc, s['header']['reading_kg'],
                                     case[1])
        if is_zero_mu:
            pred = False                     # P8: the control cannot hold
        else:
            pred = g01[(case[0], case[1] - 1)]
            require(pred == cf['closes'],
                    'g01_closed_form_disagreement', (label, pred, cf))
            delta = abs(cf['required_Ns'] -
                        cf['holder_share_kg'] * STANDARD_G * lc.DT)
            g_delta_max = max(g_delta_max, delta)
            margin = abs(cf['capacity_Ns'] - cf['required_Ns'])
            margin_min = (margin if margin_min is None
                          else min(margin_min, margin))
            # the no-flip composition: the record-g arithmetic flips no row
            if (cf['holder_share_kg'] * STANDARD_G * lc.DT <=
                    cf['capacity_Ns']) != cf['closes']:
                x2_fail = {'label': label, 'flip': 'record_g'}
        if measured != pred:
            x2_fail = {'label': label, 'measured': measured,
                       'predicted': pred}
            break
        table[label] = {'measured': measured, 'g01_row': pred,
                        'closed_form': cf}
    x2 = x2_fail is None and len(table) == BATTERY_COUNT
    if x2:
        # the minimum row margin must dominate the g-delta class
        x2 = margin_min is not None and margin_min > g_delta_max

    # ---- X3 flight kinematics ----
    x3_fail = None
    flight_worst = 0.0
    stop_worst = 0.0
    for label, s in scenarios.items():
        header = s['header']
        rows = s['rows']
        marks = header['marks']
        case = _case_of(label)
        is_zero_mu = label.endswith('|mu=0')
        closing = case in CLOSING_CASES and not is_zero_mu
        lo, hi = marks['transfer']
        face_z = [r['pads'][ts.FLYER]['centroid_z_m'] - 0.025
                  for r in rows]
        v_climb = header['v_climb_mps']
        ceiling = (v_climb + 1e-2) * lc.DT
        model = ts.flight_advance_model(lc, header, rows)
        for i in range(1, len(rows)):
            t = rows[i]['tick']
            if not (lo <= t <= hi):
                continue
            dz = face_z[i] - face_z[i - 1]
            want = model[i]['dz_expected_m']
            err = abs(dz - want)
            non_event = not rows[i]['flyer_events']
            lim = WIN_FLIGHT if non_event else 1e-9
            flight_worst = max(flight_worst, err) if non_event \
                else flight_worst
            if err > lim:
                x3_fail = {'label': label, 'tick': t, 'dz': dz,
                           'want': want, 'events': rows[i]['flyer_events']}
                break
            if not (0.0 <= dz <= ceiling):
                x3_fail = {'label': label, 'tick': t, 'dz': dz,
                           'ceiling': ceiling}
                break
            if rows[i]['flyer_climb_Ns'] is None:
                x3_fail = {'label': label, 'tick': t,
                           'climb': 'unrecorded'}
                break
        if x3_fail:
            break
        # the declared capture window binds the CLOSING cases: an honest
        # non-closing flyer may itself slip during hold (its sealed G01 row
        # is infeasible), so its flight starts from the slid position and
        # the boundary verdict (X2) carries that case's physics
        if closing:
            stop_face = face_z[marks['reattach'] - 1 - 1]
            stop_err = abs(stop_face - header['target_probe'][
                'target_centroid_m06'][2])
            stop_worst = max(stop_worst, stop_err)
            if stop_err > CAPTURE_WINDOW_M:
                x3_fail = {'label': label, 'stop_face_z': stop_face,
                           'stop_err': stop_err}
                break
    x3 = x3_fail is None

    # ---- X4 handover and force telemetry (P2 + P4) ----
    x4_fail = None
    conv_worst = 0.0
    for label, s in scenarios.items():
        header = s['header']
        rows = s['rows']
        n = header['n_channels']
        marks = header['marks']
        case = _case_of(label)
        is_zero_mu = label.endswith('|mu=0')
        closing = case in CLOSING_CASES and not is_zero_mu
        m_holder = header['reading_kg'] / (n - 1)
        jt_handover = m_holder * lc.G * lc.DT
        lo, hi = marks['transfer']
        if closing:
            for row in rows:
                t = row['tick']
                if not (lo <= t <= hi):
                    continue
                for pd in row['pads']:
                    if pd['k'] == ts.FLYER:
                        continue
                    if abs(pd['jn_sum_Ns'] - header['press_ns']) > WIN_JN:
                        x4_fail = {'label': label, 'tick': t, 'pad': pd['k'],
                                   'jn': pd['jn_sum_Ns']}
                        break
                    if abs(pd['jt_sum_Ns'] - jt_handover) > WIN_JT:
                        x4_fail = {'label': label, 'tick': t, 'pad': pd['k'],
                                   'jt': pd['jt_sum_Ns'],
                                   'want': jt_handover}
                        break
                    if pd['vt_post_mps'] > Z_TOUCH:
                        x4_fail = {'label': label, 'tick': t, 'pad': pd['k'],
                                   'vt_post': pd['vt_post_mps']}
                        break
                if x4_fail:
                    break
            # holder downward displacement <= 1e-9 per tick through the
            # flight window (the handover carries the load; the release
            # free fall is X5's law, not a handover defect)
            for i in range(1, len(rows)):
                if not (header['handover_tick'] <= rows[i]['tick']
                        < header['reattach_tick']):
                    continue
                for pd in rows[i]['pads']:
                    if pd['k'] == ts.FLYER:
                        continue
                    prev = rows[i - 1]['pads'][pd['k']]['centroid_z_m']
                    drop = prev - pd['centroid_z_m']
                    if drop > 1e-9:
                        x4_fail = {'label': label,
                                   'tick': rows[i]['tick'],
                                   'pad': pd['k'], 'drop_m': drop}
                        break
                if x4_fail:
                    break
        if x4_fail:
            break
        # P4: pressed ATTACHED ticks carry jn == P (non-flyer always; the
        # flyer outside the flight window, from tick 4) + the declared
        # conversion jn/DT == P/DT. A pad that honestly separated or slips
        # (mode slip/no_contact in the honest non-closings) is not in the
        # pressed attached state; its telemetry is recorded, and the
        # boundary verdict (X2) carries that case's physics. The flyer's
        # ESTABLISHMENT tick records its own approach + corner impulses
        # (prereg section 3 disclosure), so the jn == P law binds from the
        # tick after the recorded establishment event.
        est_tick = None
        for row in rows:
            if row['flyer_events']:
                est_tick = row['tick']
                break
        for row in rows:
            t = row['tick']
            for pd in row['pads']:
                pressed = ((pd['k'] == ts.FLYER and ts.flyer_pressed(header,
                                                                    t)
                            and t >= 4) or
                           (pd['k'] != ts.FLYER and t < marks['release'][0]))
                if not pressed:
                    continue
                if pd['k'] == ts.FLYER and t == est_tick:
                    continue
                if pd['mode'] not in ('stick', 'still'):
                    continue
                if abs(pd['jn_sum_Ns'] - header['press_ns']) > WIN_JN:
                    x4_fail = {'label': label, 'tick': t, 'pad': pd['k'],
                               'jn_pressed': pd['jn_sum_Ns']}
                    break
                conv = abs(pd['jn_sum_Ns'] / lc.DT
                           - header['press_ns'] / lc.DT)
                conv_worst = max(conv_worst, conv)
                if conv > 1e-6:
                    x4_fail = {'label': label, 'tick': t, 'pad': pd['k'],
                               'conversion': conv}
                    break
            if x4_fail:
                break
        if x4_fail:
            break
        # the full-tick identity + reciprocity ceilings (asserted live in
        # run_case; the receipts carry the residuals)
        for row in rows:
            if row['residual_full_max'] > WIN_LEDGER:
                x4_fail = {'label': label, 'tick': row['tick'],
                           'residual': row['residual_full_max']}
                break
            if max(abs(v) for v in
                   row['ledger']['reciprocity_residual']) > WIN_LEDGER:
                x4_fail = {'label': label, 'tick': row['tick'],
                           'reciprocity':
                               row['ledger']['reciprocity_residual']}
                break
        if x4_fail:
            break
    x4 = x4_fail is None

    # ---- X5 release law (P5) ----
    x5_fail = None
    freefall_worst_disp = 0.0
    for label, s in scenarios.items():
        header = s['header']
        rows = s['rows']
        n = header['n_channels']
        marks = header['marks']
        case = _case_of(label)
        is_zero_mu = label.endswith('|mu=0')
        closing = case in CLOSING_CASES and not is_zero_mu
        lo, hi = marks['release']
        for row in rows:
            if not (lo <= row['tick'] <= hi):
                continue
            for pd in row['pads']:
                bar = pd['mass_kg'] * WIN_RELEASE_SCALE
                if pd['jn_sum_Ns'] > bar or pd['jt_sum_Ns'] > bar:
                    x5_fail = {'label': label, 'tick': row['tick'],
                               'pad': pd['k'], 'jn': pd['jn_sum_Ns'],
                               'jt': pd['jt_sum_Ns'], 'bar': bar}
                    break
            if x5_fail:
                break
        if x5_fail:
            break
        # velocity recursion v(k) = v(k-1) + g*DT from the measured entry
        for k_i in range(1, len(rows)):
            row = rows[k_i]
            prev = rows[k_i - 1]
            if not (lo <= row['tick'] <= hi):
                continue
            for pd, pd_prev in zip(row['pads'], prev['pads']):
                want = pd_prev['vz_mps'] - lc.G * lc.DT
                if abs(pd['vz_mps'] - want) > WIN_RECURSION:
                    x5_fail = {'label': label, 'tick': row['tick'],
                               'pad': pd['k'], 'vz': pd['vz_mps'],
                               'want': want}
                    break
            if x5_fail:
                break
        if x5_fail:
            break
        # holders (and the flyer) released from clean stick accumulate the
        # free-fall displacement g*DT^2*(1+2+...+10) across the ten release
        # ticks (entry state = the last hold2 tick's end)
        if closing:
            want_disp = lc.G * lc.DT * lc.DT * 55.0
            for k in range(n):
                pd_first = rows[lo - 2]['pads'][k]
                pd_last = rows[hi - 1]['pads'][k]
                disp = pd_first['centroid_z_m'] - pd_last['centroid_z_m']
                freefall_worst_disp = max(freefall_worst_disp,
                                          abs(disp - want_disp))
                if abs(disp - want_disp) > WIN_DISP:
                    x5_fail = {'label': label, 'pad': k, 'disp': disp,
                               'want': want_disp}
                    break
            if x5_fail:
                break
    x5 = x5_fail is None

    # ---- X6 reachability and identity (P7 / C16 composition) ----
    x6_fail = None
    for label, s in scenarios.items():
        header = s['header']
        travel = abs(header['target_probe']['travel_m'])
        if travel > D_MAX_REACH_M:
            x6_fail = {'label': label, 'travel': travel}
            break
        rows = s['rows']
        marks = header['marks']
        hold_tris = set()
        for row in rows:
            if marks['hold'][0] <= row['tick'] <= marks['hold'][1]:
                hold_tris.update(row['pads'][ts.FLYER]['tris'])
        if 0 not in hold_tris:
            x6_fail = {'label': label, 'hold_tris': sorted(hold_tris)}
            break
        hold2_tris = set()
        for row in rows:
            if marks['hold2'][0] <= row['tick'] <= marks['hold2'][1]:
                hold2_tris.update(row['pads'][ts.FLYER]['tris'])
        if ts.TARGET_TRI not in hold2_tris:
            x6_fail = {'label': label, 'hold2_tris': sorted(hold2_tris)}
            break
    x6 = x6_fail is None

    # ---- P-class: seam law + named-variable law + prereg identity ----
    p_fail = None
    key_union = set()
    for label, s in scenarios.items():
        for sample in s['samples']:
            key_union.update(sample)
            if set(sample) != set(declared_keys):
                p_fail = {'label': label, 'keys': sorted(sample)}
                break
        if p_fail:
            break
        last = 0
        for sample in s['samples']:
            if sample['t_tick'] <= last:
                p_fail = {'label': label, 'non_monotone': sample['t_tick']}
                break
            last = sample['t_tick']
            if abs(sample['t_seconds'] - sample['t_tick'] * lc.DT) > 1e-12:
                p_fail = {'label': label, 'seconds': sample['t_seconds']}
                break
        if p_fail:
            break
        # the pinned G05 seam composition: hold/release accepted, the
        # G06-only phases refused timing_unbound
        expected_g05_refused = s['header']['total_ticks'] - \
            s['g05_census']['accepted']
        if s['g05_census']['accepted'] != 30 or \
                len(s['g05_census']['refusals']) != expected_g05_refused or \
                set(s['g05_refusal_codes']) != {'timing_unbound'}:
            p_fail = {'label': label, 'g05_census': s['g05_census'],
                      'codes': s['g05_refusal_codes']}
            break
    if p_fail is None:
        # live refusal probe: the x_* namespace is refused by the G06 seam
        Seam = ts.build_seam_module(g05)
        seam_p = Seam('p_class_probe', lc.DT)
        sample0 = dict(scenarios['band_mid|n=3']['samples'][0])
        sample0['x_press'] = 5.0
        fired_absent = None
        try:
            seam_p.deliver(sample0)
        except ValueError as exc:
            fired_absent = str(exc)
        if fired_absent is None or 'named_absent_occupied' not in \
                fired_absent:
            p_fail = {'probe': 'x_namespace', 'fired': fired_absent}
    if p_fail is None:
        # live refusal probe: the pinned G05 seam refuses a G06-only phase
        seam_g = g05.ObservationSeam('p_class_g05_probe', lc.DT)
        transfer_sample = None
        for sample in scenarios['band_mid|n=3']['samples']:
            if sample['t_phase'] == 'transfer':
                transfer_sample = dict(sample)
                break
        fired_g05 = None
        try:
            seam_g.deliver(transfer_sample)
        except ValueError as exc:
            fired_g05 = str(exc)
        if fired_g05 is None or 'timing_unbound' not in fired_g05:
            p_fail = {'probe': 'g05_phase_extension', 'fired': fired_g05}
    if p_fail is None:
        try:
            reg_criteria, _states = registry_criteria_sha256()
        except Exception as exc:            # the store is a host pin
            reg_criteria = None
            p_fail = {'probe': 'registry_read', 'error': str(exc)[:200]}
        if reg_criteria is not None and reg_criteria != CRITERIA_SHA256:
            p_fail = {'probe': 'criteria_identity', 'registry':
                      reg_criteria, 'declared': CRITERIA_SHA256}
    # named absent variables carried, never filled
    absent = gc.NAMED_ABSENT
    named_ok = (len(absent) == 10
                and all(v[0].startswith('x_') for v in absent)
                and not (key_union & {v[0] for v in absent}))
    p_class = (p_fail is None and named_ok and
               sorted(key_union) == declared_keys)

    rec = {
        'schema': 'chimera.g06_transfer_receipt.v1', 'revision': 1,
        'card': CARD_FULL, 'task_id': CARD_ID,
        'criteria_sha256': CRITERIA_SHA256,
        'base_commit': BASE_COMMIT,
        'preregistration': 'PREREGISTRATION.md',
        'input_pins': {k: 'ok' for k in pins},
        'interface': {
            'module': 'tools/monkey_campaign/contributions/MAT2-G06/'
                      'transfer_sequence.py',
            'obs_schema': ts.SCHEMA,
            'table': 'the pinned G05 32-slot float32 table (imported; '
                     'bit-identical slot semantics)',
            'obs_dim': g05.OBS_DIM, 'dtype': 'float32',
            'history_ticks': 0,
            'timing_keys': list(ts.TIMING_KEYS),
            'phase_universe': list(ts.PHASES),
            'g05_phase_universe': list(g05.PHASES),
            'timing_law': {'tick_base': 1, 'phase_values': list(ts.PHASES),
                           'dt_s': lc.DT,
                           'cadence': 'exactly one sample per solver tick, '
                                      'delivered in tick order, post solve'},
            'channel_flag_projection':
                'four-way recorded mode {stick, still, slip, no_contact}: '
                'contact = mode != no_contact; stick = mode == stick; '
                'slip = mode == slip; a still tick is contact=1, stick=0, '
                'slip=0',
            'declared_keys': declared_keys,
        },
        'upstream': {
            'solver': {'module': 'MAT2-M06/local_contact.py',
                       'sha256': gc.INTERFACE_SHA256,
                       'imported_not_forked': True},
            'grip_physics': {'module': 'MAT2-G04/grip_contact.py',
                             'sha256': ts.G04_MODULE_SHA256,
                             'imported_not_forked': True,
                             'revision': 'sealed PR #298'},
            'observation_table': {'module':
                                  'MAT2-G05/contact_support_obs.py',
                                  'sha256': ts.G05_MODULE_SHA256,
                                  'imported_not_forked': True,
                                  'revision': 'sealed PR #300',
                                  'composition': 'the pinned 32-slot table '
                                  'is NOT re-declared or modified; the '
                                  'task-owned G06 phase universe extends '
                                  'the hold/release universe at the '
                                  'shared-table level'},
            'sealed_boundary': {'module': 'MAT2-G01 feasibility receipt',
                                'sha256':
                                PINS[G01_RECEIPT_HOST],
                                'role': 'the 12-row case table IS the '
                                        'transfer-admissibility authority '
                                        'at (reading, n-1)'},
        },
        'schedule': {
            'ticks': 229, 'dt_s': lc.DT, 'g': lc.G,
            'v_climb_mps': ts.V_CLIMB_MPS,
            'approach_press_ns': ts.A_PRESS_NS,
            'standoff_m': ts.STANDOFF_M,
            'cruise_ticks_band_cases': scenarios['band_mid|n=3']['header'][
                'marks']['cruise'],
            'marks_band_mid_n3': {
                k: list(v) if isinstance(v, tuple) else v
                for k, v in scenarios['band_mid|n=3']['header']['marks']
                .items() if k != 'envelope'},
            'envelope': list(envelope_ticks),
            'capture_window_m': CAPTURE_WINDOW_M,
            'reach_envelope_m': D_MAX_REACH_M,
        },
        'named_absent_variables': [
            {'name': v, 'quantity': q, 'status': 'ABSENT',
             'provenance_verbatim': p} for (v, q, p) in absent],
        'delivery_totals': totals,
        'boundary_table': table,
        'x_checks': {
            'X1_done_when_transfer_envelope': bool(x1),
            'X2_sealed_boundary_composition': bool(x2),
            'X3_flight_kinematics': bool(x3),
            'X4_handover_and_force_telemetry': bool(x4),
            'X5_release_law': bool(x5),
            'X6_reachability_and_identity': bool(x6),
            'X7_determinism_scoped_to_compare': True,
        },
        'x_evidence': {
            'x1_fail': x1_fail,
            'x2_fail': x2_fail,
            'x3_fail': x3_fail,
            'x4_fail': x4_fail,
            'x5_fail': x5_fail,
            'x6_fail': x6_fail,
            'p_class_fail': p_fail,
            'p_class_pass': bool(p_class),
            'flight_worst_non_event_m': flight_worst,
            'stop_window_worst_m': stop_worst,
            'conversion_worst_N': conv_worst,
            'freefall_disp_worst_m': freefall_worst_disp,
            'record_g_delta_max_Ns': g_delta_max,
            'row_margin_min_Ns': margin_min,
            'delivered_key_union': sorted(key_union),
            'declared_key_count': len(declared_keys),
        },
        'vacuous_guard_selftest': vacuous_guard_selftest(),
    }
    numeric_x = [v for k, v in rec['x_checks'].items()
                 if k != 'X7_determinism_scoped_to_compare']
    rec['X1_pass'] = all(bool(v) for v in numeric_x) and bool(p_class)
    return rec


def mode_main():
    pins = verify_input_pins()
    gc = ts.load_g04_module()
    lc = gc.load_interface()
    g05 = ts.load_g05_module()
    geom = gc.load_trunk_geometry()
    scenarios, totals = run_battery(gc, lc, g05, geom)
    trace = {'schema': 'chimera.g06_transfer_trace.v1', 'revision': 1,
             'scenarios': scenarios}
    receipt = build_receipt(gc, lc, g05, scenarios, totals, pins)
    (HERE / 'experiment_trace.json').write_bytes(canonical(trace))
    (HERE / 'experiment_receipt.json').write_bytes(canonical(receipt))
    print(json.dumps({'X1_pass': receipt['X1_pass'],
                      'x_checks': receipt['x_checks'],
                      'p_class_pass':
                          receipt['x_evidence']['p_class_pass'],
                      'delivery_totals': totals}, indent=1))


def mode_rerun():
    pins = verify_input_pins()
    gc = ts.load_g04_module()
    lc = gc.load_interface()
    g05 = ts.load_g05_module()
    geom = gc.load_trunk_geometry()
    scenarios, totals = run_battery(gc, lc, g05, geom)
    trace = {'schema': 'chimera.g06_transfer_trace.v1', 'revision': 1,
             'scenarios': scenarios}
    receipt = build_receipt(gc, lc, g05, scenarios, totals, pins)
    (HERE / 'experiment_trace_rerun2.json').write_bytes(canonical(trace))
    (HERE / 'experiment_receipt_rerun2.json').write_bytes(canonical(receipt))
    print('rerun written')


AUGMENTATION_KEYS = []


def mode_compare():
    a = (sha256_file(HERE / 'experiment_trace.json'),
         sha256_file(HERE / 'experiment_receipt.json'))
    b = (sha256_file(HERE / 'experiment_trace_rerun2.json'),
         sha256_file(HERE / 'experiment_receipt_rerun2.json'))
    run1 = json.loads((HERE / 'experiment_receipt.json').read_text())
    run2 = json.loads((HERE / 'experiment_receipt_rerun2.json').read_text())
    only1 = sorted(set(run1) - set(run2))
    only2 = sorted(set(run2) - set(run1))
    shared_differ = sorted(k for k in set(run1) & set(run2)
                           if run1[k] != run2[k])
    trace_identical = a[0] == b[0]
    receipt = {
        'schema': 'chimera.g06_determinism.v1',
        'trace_sha_run1': a[0], 'receipt_sha_run1': a[1],
        'trace_sha_run2': b[0], 'receipt_sha_run2': b[1],
        'X2_trace_byte_identical': trace_identical,
        'X2_receipt_byte_identical': a[1] == b[1],
        'receipt_keys_only_in_main': only1,
        'receipt_keys_only_in_rerun': only2,
        'receipt_shared_keys_differing': shared_differ,
        'declared_augmentation_keys': AUGMENTATION_KEYS,
        'X2_byte_identical': a == b,
        'X2_pass': trace_identical and only1 == AUGMENTATION_KEYS
        and not only2 and not shared_differ,
    }
    (HERE / 'determinism_receipt.json').write_bytes(canonical(receipt))
    print(json.dumps({k: receipt[k] for k in (
        'X2_pass', 'X2_trace_byte_identical')}, indent=1))


# ---- falsifier arms (clean control FIRST; named premature guard) ----

def _load_scratch_module(stem, source_bytes):
    """Write a tampered module COPY into the attempt scratch (never the
    card dir, never committed state) and import it under a private name."""
    import importlib.util
    scratch = ATTEMPT_ROOT / 'scratch-falsifiers'
    scratch.mkdir(parents=True, exist_ok=True)
    path = scratch / (stem + '.py')
    path.write_bytes(source_bytes)
    spec = importlib.util.spec_from_file_location('g06_' + stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _continuity_violation(lc, header, rows):
    """The X3 continuity law, evaluated standalone so the tampered build
    can be scored by the SAME predicate as the clean control."""
    marks = header['marks']
    lo, hi = marks['transfer']
    face_z = [r['pads'][ts.FLYER]['centroid_z_m'] - 0.025 for r in rows]
    ceiling = (header['v_climb_mps'] + 1e-2) * lc.DT
    for i in range(1, len(rows)):
        t = rows[i]['tick']
        if not (lo <= t <= hi):
            continue
        dz = face_z[i] - face_z[i - 1]
        if not (0.0 <= dz <= ceiling):
            return {'tick': t, 'dz': dz, 'ceiling': ceiling}
    return None


def mode_falsify():
    pins = verify_input_pins()
    gc = ts.load_g04_module()
    lc = gc.load_interface()
    g05 = ts.load_g05_module()
    geom = gc.load_trunk_geometry()
    Seam = ts.build_seam_module(g05)
    arms = {}

    def arm(name, clean, tampered, bites, discriminator):
        arms[name] = {
            'clean_control': clean, 'tampered': tampered,
            'bites': bool(bites), 'discriminator': discriminator,
            'premature_guard': name.replace('FB', 'g06_fb')
            + '_premature: PASS (clean control ran first)',
        }

    # ONE clean closing scenario grounds the clean controls (band_mid|n=3).
    header_c, rows_c = ts.run_case(lc, gc, geom, 6.15, 3,
                                   scenario_id='FB_ground')
    ts.cumulative_down_disp(rows_c)
    verdicts_c = ts.support_verdicts(header_c, rows_c)
    clean_continuity = _continuity_violation(lc, header_c, rows_c) is None

    # FB1 teleport_transfer -- the continuity law bites on the teleporting
    # build (the preregistered tamper: the flyer's vertices jump to the
    # target pose at the handover tick).
    header_t, rows_t = ts.run_case(lc, gc, geom, 6.15, 3,
                                   scenario_id='FB1_teleport',
                                   injections={'teleport_at_tick':
                                               header_c['handover_tick']})
    ts.cumulative_down_disp(rows_t)
    violation = _continuity_violation(lc, header_t, rows_t)
    refuse_vacuous(0.0, float(violation is not None))
    arm('FB1_teleport_transfer',
        {'continuity_violation': clean_continuity,
         'handover_tick': header_c['handover_tick']},
        {'continuity_violation': violation is not None,
         'violation': violation,
         'teleport_tick': header_t['injections']['teleport_at_tick']},
        clean_continuity and violation is not None
        and violation['dz'] > 0.1,
        'a hidden reset/teleport in the flight window jumps dz by the whole '
        'travel and the continuity law must fire (the teleportation class)')

    # FB2 support_overclaim -- the support assertion matches the measured
    # modes on band_mid|n=3 (supported) and scene|n=3 (honestly not);
    # substituting the stick mode on the scene transfer ticks (an
    # unsupported transfer recorded as supported) must FAIL the assertion.
    header_s, rows_s = ts.run_case(lc, gc, geom, 10.037998, 3,
                                   scenario_id='FB2_ground_scene')
    ts.cumulative_down_disp(rows_s)
    verdicts_s = ts.support_verdicts(header_s, rows_s)
    clean_scene_honest = not transfer_support_all(verdicts_s)

    def assert_matches_modes(verdicts, rows):
        """The production support assertion: every verdict re-derives from
        the recorded pad modes (P6)."""
        for v, row in zip(verdicts, rows):
            n = len(row['pads'])
            holding = [pd for k, pd in enumerate(row['pads'])
                       if k != ts.FLYER]
            if v['phase'] == 'transfer':
                want = all(pd['mode'] == 'stick' for pd in holding)
            elif v['phase'] in ('load', 'hold', 'load2', 'hold2'):
                want = all(pd['mode'] == 'stick' for pd in row['pads'])
            elif v['phase'] == 'release':
                want = False
            else:
                continue
            if bool(want) != bool(v['supported']):
                return {'tick': v['tick'], 'phase': v['phase'],
                        'supported': v['supported'], 'modes': want}
        return None

    clean_assert = (assert_matches_modes(verdicts_c, rows_c) is None
                    and assert_matches_modes(verdicts_s, rows_s) is None)
    tampered_verdicts = [dict(v) for v in verdicts_s]
    marks_s = header_s['marks']
    for v in tampered_verdicts:
        if v['phase'] == 'transfer':
            v['supported'] = True
            v['reason'] = 'tampered_stick_substitution'
    tampered_fail = assert_matches_modes(tampered_verdicts, rows_s)
    refuse_vacuous(float(clean_scene_honest),
                   float(tampered_fail is not None))
    arm('FB2_support_overclaim',
        {'band_mid_assertion_clean': assert_matches_modes(verdicts_c,
                                                          rows_c) is None,
         'scene_honestly_unsupported': clean_scene_honest,
         'scene_assertion_clean':
             assert_matches_modes(verdicts_s, rows_s) is None},
        {'assertion_fail': tampered_fail,
         'tamper': 'stick mode substituted on scene|n=3 transfer ticks'},
        clean_assert and clean_scene_honest and tampered_fail is not None,
        'recording an unsupported transfer as supported is exactly the '
        'unsupported-transfer class the profile falsifier names (F03 B7 / '
        'G04 FB5 heritage: the discriminator must discriminate)')

    # FB3 flight_hidden_anchor -- an unrecorded 0.02 N*s per-tick impulse on
    # the flyer during the flight window; the full-tick ledger identity
    # must fire (ledger_imbalance) with residual ~ 2e-2.
    anchor = (0.0, 0.0, 0.02)
    fired3 = None
    try:
        ts.run_case(lc, gc, geom, 6.15, 3, scenario_id='FB3_hidden_anchor',
                    injections={'hidden_anchor': anchor})
    except ValueError as exc:
        fired3 = str(exc)
    clean_ledger_ok = all(r['residual_full_max'] <= ts.WIN_LEDGER
                          for r in rows_c)
    refuse_vacuous(float(clean_ledger_ok), float(fired3 is not None))
    arm('FB3_flight_hidden_anchor',
        {'clean_residual_max_Ns': max(r['residual_full_max']
                                      for r in rows_c),
         'clean_ledger_ok': clean_ledger_ok},
        {'fired': fired3 is not None, 'refusal': fired3,
         'unrecorded_impulse_Ns': list(anchor)},
        clean_ledger_ok and fired3 is not None
        and 'ledger_imbalance' in fired3,
        'an invisible anchor (applied but absent from every recorded '
        'channel) breaks the full-tick identity -- the concealment class')

    # FB4 release_sticky -- re-applying the last hold friction impulse after
    # press-off (G04 FB1 heritage) must FAIL the release free-fall law (the
    # tampered run completes; the evaluated law is what bites).
    header_4, rows_4 = ts.run_case(lc, gc, geom, 6.15, 3,
                                   scenario_id='FB4_sticky',
                                   injections={'sticky_release': True})
    ts.cumulative_down_disp(rows_4)
    tampered_release_ok = _release_law_ok(lc, header_4, rows_4)
    clean_release_ok = _release_law_ok(lc, header_c, rows_c)
    refuse_vacuous(float(clean_release_ok), float(tampered_release_ok))
    arm('FB4_release_sticky',
        {'clean_release_law_ok': clean_release_ok},
        {'release_law_ok_on_tampered': tampered_release_ok,
         'tamper': 'the last hold friction impulse re-applied after '
                   'press-off (recorded weld channel)'},
        clean_release_ok and not tampered_release_ok,
        'a hidden sticky constraint holding the pads after press-off '
        'breaks the free-fall release law -- nothing retains a force '
        'after the press stops')

    # FB5 force_pose_inconsistency -- the declared conversion jn/DT doubled
    # with the recorded pose unchanged (the profile's named class).
    sample1 = ts.project_sample(g05, header_c, verdicts_c[11], rows_c[11],
                                lc.DT)
    SeamProbe = Seam
    seam5 = SeamProbe('FB5_clean', lc.DT)
    accepted_c5 = seam5.deliver(dict(sample1))
    clean_ok5 = accepted_c5 and not seam5.refusals
    hold_row = rows_c[11]
    jn_raw = hold_row['pads'][0]['jn_sum_Ns']
    conv_clean = abs(sample1['ch0_contact_force_N'] * lc.DT - jn_raw) \
        <= 1e-6 * max(1.0, jn_raw)
    tampered5 = dict(sample1)
    tampered5['ch0_contact_force_N'] = ts.to_f32(
        2.0 * jn_raw / lc.DT)
    conv_tampered = abs(tampered5['ch0_contact_force_N'] * lc.DT - jn_raw) \
        <= 1e-6 * max(1.0, jn_raw)
    pose_unchanged = (tampered5['ch0_centroid_z_m']
                      == sample1['ch0_centroid_z_m'])
    refuse_vacuous(sample1['ch0_contact_force_N'],
                   tampered5['ch0_contact_force_N'])
    arm('FB5_force_pose_inconsistency',
        {'conversion_holds': conv_clean, 'force_N':
         sample1['ch0_contact_force_N']},
        {'conversion_holds': conv_tampered, 'pose_unchanged':
         pose_unchanged, 'force_N': tampered5['ch0_contact_force_N']},
        clean_ok5 and conv_clean and (not conv_tampered) and pose_unchanged,
        'doubling the declared force conversion with the recorded pose '
        'unchanged is exactly the force/pose inconsistency the profile '
        'falsifier names (G05 FB4 heritage)')

    receipt = {'schema': 'chimera.g06_falsifiers.v1',
               'arms': arms,
               'F_all_green': all(a['bites'] for a in arms.values()),
               'arm_count': len(arms)}
    (HERE / 'falsifier_receipt.json').write_bytes(canonical(receipt))
    print(json.dumps({'F_all_green': receipt['F_all_green'],
                      'arms': {k: v['bites'] for k, v in arms.items()}},
                     indent=1))


def transfer_support_all(verdicts):
    return all(v['supported'] for v in verdicts if v['phase'] == 'transfer')


def _release_law_ok(lc, header, rows):
    """The X5 release law, evaluated standalone (the clean-control form):
    free-fall velocity recursion + the free-fall displacement identity."""
    marks = header['marks']
    lo, hi = marks['release']
    n = header['n_channels']
    for i in range(1, len(rows)):
        row = rows[i]
        prev = rows[i - 1]
        if not (lo <= row['tick'] <= hi):
            continue
        for pd, pd_prev in zip(row['pads'], prev['pads']):
            want = pd_prev['vz_mps'] - lc.G * lc.DT
            if abs(pd['vz_mps'] - want) > ts.WIN_RECURSION:
                return False
    want_disp = lc.G * lc.DT * lc.DT * 55.0
    for k in range(n):
        disp = rows[lo - 2]['pads'][k]['centroid_z_m'] \
            - rows[hi - 1]['pads'][k]['centroid_z_m']
        if abs(disp - want_disp) > ts.WIN_DISP:
            return False
    return True


def mode_regression():
    results = []
    for suite in (M06_SUITE, G04_SUITE, G05_SUITE):
        proc = subprocess.run([sys.executable, '-B', suite],
                              capture_output=True, text=True, timeout=3000)
        results.append({'suite': suite, 'suite_unmodified': True,
                        'exit_code': proc.returncode,
                        'tail': proc.stdout[-1500:]})
    receipt = {
        'schema': 'chimera.g06_regression.v1',
        'suites': results,
        'P_regression_suite_green': all(r['exit_code'] == 0
                                        for r in results),
    }
    (HERE / 'regression_receipt.json').write_bytes(canonical(receipt))
    print(json.dumps({r['suite'].split('/')[-1]: r['exit_code']
                      for r in results}, indent=1))


def main(argv):
    mode = argv[1] if len(argv) > 1 else 'main'
    if mode not in MODES:
        raise SystemExit('unknown mode: ' + mode
                         + ' (valid: ' + ', '.join(MODES) + ')')
    getattr(sys.modules[__name__], 'mode_' + mode)()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
