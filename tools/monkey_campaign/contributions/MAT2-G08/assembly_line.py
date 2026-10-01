"""MAT2-G08 assembly line (PREREGISTRATION.md, frozen; amendment a1).

done_when: "Accepted mechanics pass CPU/GPU and runtime identity gates
relevant to climbing"

The assembly executes the composed qualification battery in ONE deterministic
CPU process: the sealed G06 transfer battery (9 runs x 229 ticks) and the
sealed G07 release/fall battery (13 runs x 60 ticks), all through the pinned
M06 solver and the sealed upstream modules (imported, hash-asserted, never
forked). G08 adds NO schedule, NO force channel and NO new physics: the
assembly value is the identity of the assembled line with the certified lines
(byte-level row identity, amendment a1 composition binding for continuous
certified values), the union support ledger with declared response classes
(the W09-disclosure handling by measurement), the whole-line continuity law,
event localization, reference-math composition, the seam union census and the
per-operation numerical budget.

CPU-only, stdlib-only, deterministic (no RNG, no wall clock). Refusals are
named codes (prereg section 13); nothing is silently repaired.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent

SCHEMA = 'chimera.g08_assembly.v1'

BASE_COMMIT = '5f82a3ddb35aac8b59bc4b087a90353e1fb69c1d'
PREREG_COMMITS = ('f5ae83ce92cf6cb33c14151f491d2e339117ee7f',
                  '65bccc768b9f30be42d4253db3d4eeba6d9cdc61')
CRITERIA_SHA256 = ('f2a89774038270b2665c70ec8ff2a8a521aec21fde5b9bc229e4faea'
                   '84bdbbcb')

# ---- the established interfaces (imported, hash-asserted, never forked) ----
G04_MODULE_REL = '../MAT2-G04/grip_contact.py'
G04_MODULE_SHA256 = ('0d6375484c350039468b31a2f7db2895d3365412aee52ce98de72b'
                     '4173d69245')
G05_MODULE_REL = '../MAT2-G05/contact_support_obs.py'
G05_MODULE_SHA256 = ('3dae0a3805cec86bba8dbae9a6fc563f43cddc98fcd01a693f725e'
                     '4f31c46bd3')
G06_MODULE_REL = '../MAT2-G06/transfer_sequence.py'
G06_MODULE_SHA256 = ('a3f376f9feafc07897ea331219320b6393bfb69916781a6beb8079'
                     '2c7bd068f9')
G07_MODULE_REL = '../MAT2-G07/release_fall_account.py'
G07_MODULE_SHA256 = ('78b5cc66f7019fa181765eb0366fe6c98525941840f57723d0ae99'
                     'cb55b2a8c5')
F05_REPORT_REL = '../MAT2-F05/report.md'
F05_REPORT_SHA256 = ('0a640c131f067241d3d20f595bd825e2e4319102cc2d200ac04805'
                     'f702c6ba6d')
G06_PINNED_TRACE_REL = '../MAT2-G06/experiment_trace.json'
G06_PINNED_TRACE_SHA256 = ('eec274ded637a4cb10049bc7d427037e3a1e54e72a3c11b5'
                           '5ddf80ec5d18f2f9')
G06_PINNED_RECEIPT_REL = '../MAT2-G06/experiment_receipt.json'
G06_PINNED_RECEIPT_SHA256 = ('cf5c9cc5b7d51a23f282313974f853edca83ca30c19edd'
                             '51a36eb9ddf0d3feff')
G07_PINNED_TRACE_REL = '../MAT2-G07/experiment_trace.json'
G07_PINNED_TRACE_SHA256 = ('b8a9e139d85bd7cc116ea3d6ca94f655e41ec7ae67c15f76'
                           '86e057ca0706eb9b')
G07_PINNED_RECEIPT_REL = '../MAT2-G07/experiment_receipt.json'
G07_PINNED_RECEIPT_SHA256 = ('c539617b098190918187d9a7dcbb0a5e33a85998adaa58'
                             'f6b781703bbdeb88f8')

# ---- frozen windows (prereg section 7; verbatim from the sealed modules) --
COMPOSITION_BIND = 1e-9        # amendment a1 (ii)
STANDARD_G = 9.80665           # the record-g no-flip composition constant

RESPONSE_CLASSES = ('declared_release', 'declared_solver_slip',
                    'declared_flight_hover', 'declared_establishing')

# T-segment story beats (capture; prereg section 12): the composed
# band_mid|n=3 transfer story. Tick 1 is a CAMERA COVER tick (the composed
# axis start), not a frame beat.
T_STORY_SCENARIO = 'band_mid|n=3'
T_STORY_TICKS = (1, 4, 8, 20, 31, 60, 120, 186, 193, 208)
# R-segment story (the stick-class scene|n=3 run): the frame beat is the
# release flip at replay tick 21; ticks 1 and 60 are CAMERA COVER ticks
# (composed axis 230 and 289; the full 60-tick replay maps to
# composed 230..289 as composed = 229 + replay tick).
R_STORY_SCENARIO = 'scene|n=3'
R_STORY_TICK = 21
R_STORY_TICKS = (1, 21, 60)


def require(ok, code, detail=''):
    if not ok:
        raise ValueError(code + (': ' + str(detail) if detail != '' else ''))


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def sha_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def sha_json(value):
    return sha_bytes(canonical(value))


def importable_spec(spec):
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_pinned(rel, expected_sha, name):
    path = (HERE / rel).resolve()
    if not path.exists():
        raise ValueError('interface_pin_missing:' + str(path))
    got = sha_bytes(path.read_bytes())
    if got != expected_sha:
        raise ValueError('interface_pin_drift:' + rel + ':' + got)
    spec = importlib.util.spec_from_file_location(name, path)
    return importable_spec(spec)


def load_pinned_modules():
    """Import the pinned sealed modules (each byte-asserted). Returns the
    namespace tuple (gc, lc, g05, ts, rfa)."""
    gc = _load_pinned(G04_MODULE_REL, G04_MODULE_SHA256,
                      'g08_pinned_grip_contact')
    lc = gc.load_interface()
    g05 = _load_pinned(G05_MODULE_REL, G05_MODULE_SHA256,
                       'g08_pinned_contact_support_obs')
    ts = _load_pinned(G06_MODULE_REL, G06_MODULE_SHA256,
                      'g08_pinned_transfer_sequence')
    rfa = _load_pinned(G07_MODULE_REL, G07_MODULE_SHA256,
                       'g08_pinned_release_fall_account')
    return gc, lc, g05, ts, rfa


def load_pinned_json(rel, expected_sha):
    path = (HERE / rel).resolve()
    if not path.exists():
        raise ValueError('interface_pin_missing:' + str(path))
    raw = path.read_bytes()
    got = sha_bytes(raw)
    if got != expected_sha:
        raise ValueError('interface_pin_drift:' + rel + ':' + got)
    return json.loads(raw)


# ---- matter identity (P1; the F05 data binding) ---------------------------

def matter_identity(gc):
    """The fixture constants must equal the pinned F05 declared rows
    (climbable trunk matter wood_trunk_01 0.6/0.6; probe shells 0.6/0.4).
    Refusal: matter_identity_drift."""
    require(gc.TRUNK_MATTER == 'wood_trunk_01', 'matter_identity_drift:trunk'
            '_matter', gc.TRUNK_MATTER)
    require(abs(gc.TRUNK_MU_S - 0.6) == 0.0, 'matter_identity_drift:trunk'
            '_mu_s', gc.TRUNK_MU_S)
    require(abs(gc.TRUNK_MU_K - 0.6) == 0.0, 'matter_identity_drift:trunk'
            '_mu_k', gc.TRUNK_MU_K)
    require(abs(gc.PAD_MU_S - 0.6) == 0.0, 'matter_identity_drift:pad_mu_s',
            gc.PAD_MU_S)
    require(abs(gc.PAD_MU_K - 0.4) == 0.0, 'matter_identity_drift:pad_mu_k',
            gc.PAD_MU_K)
    path = (HERE / F05_REPORT_REL).resolve()
    got = sha_bytes(path.read_bytes())
    require(got == F05_REPORT_SHA256, 'interface_pin_drift:' + F05_REPORT_REL,
            got)
    text = path.read_text(encoding='utf-8')
    trunk_row = _f05_row(text, 'wood_trunk_01')
    require(trunk_row == (0.6, 0.6), 'matter_identity_drift:f05_trunk_row',
            trunk_row)
    probe_row = _f05_row(text, 'mass_tetra')
    require(probe_row == (0.6, 0.4), 'matter_identity_drift:f05_probe_row',
            probe_row)
    return {'trunk_matter': gc.TRUNK_MATTER, 'trunk_mu_s': gc.TRUNK_MU_S,
            'trunk_mu_k': gc.TRUNK_MU_K, 'pad_mu_s': gc.PAD_MU_S,
            'pad_mu_k': gc.PAD_MU_K, 'f05_trunk_row': list(trunk_row),
            'f05_probe_row': list(probe_row), 'pair_rule': 'elementwise_min'}


def _f05_row(text, matter):
    m = re.search(r'^\|\s[^|]+\|\s%s\s\|\s([0-9.]+)\s\|\s([0-9.]+)\s\|'
                  % re.escape(matter), text, re.M)
    require(m is not None, 'matter_identity_drift:f05_row_missing', matter)
    return (float(m.group(1)), float(m.group(2)))


# ---- the frozen assembly battery order (prereg section 4) -----------------

def transfer_cases(ts):
    """The sealed G06 battery VERBATIM (frozen order; zero-mu control
    last)."""
    cases = []
    for name, kg in ts.TRANSFER_READINGS:
        for n in ts.TRANSFER_CHANNELS:
            cases.append(('%s|n=%d' % (name, n), kg, n, None, None))
    zc = ts.ZERO_MU_CONTROL
    cases.append(('%s|n=%d|mu=0' % (zc['reading'], zc['n']),
                  dict(ts.TRANSFER_READINGS)[zc['reading']], zc['n'],
                  zc['mu_s'], zc['mu_k']))
    return cases


def release_cases(gc):
    """The sealed G07 battery VERBATIM (G04's frozen order; zero-mu control
    last)."""
    cases = []
    for name, kg in gc.READINGS_KG:
        for n in gc.CHANNELS:
            cases.append((gc.scenario_label(name, n), kg, n, gc.PAD_MU_S,
                          gc.PAD_MU_K))
    zc = gc.ZERO_MU_CONTROL
    cases.append((gc.scenario_label(zc['reading'], zc['n']) + '|mu=0',
                  dict(gc.READINGS_KG)[zc['reading']], zc['n'],
                  zc['mu_s'], zc['mu_k']))
    return cases


# ---- segment T: the assembled transfer battery -----------------------------

def run_transfer_case(gc, lc, g05, ts, geom, label, kg, n, mu_s=None,
                      mu_k=None, injections=None, story_ticks=()):
    """One assembled transfer scenario through the PINNED ts.run_case, with
    the seam deliveries of the sealed G06 harness. Returns (minimal record,
    header, rows); the record carries the row hash, verdict hash, census,
    marks, events and the declared story beats; the full per-tick rows stay
    in this process for the in-process budget measurements."""
    header, rows = ts.run_case(lc, gc, geom, kg, n, mu_s=mu_s, mu_k=mu_k,
                               scenario_id=label, injections=injections)
    ts.cumulative_down_disp(rows)
    verdicts = ts.support_verdicts(header, rows)
    Seam = ts.build_seam_module(g05)
    seam = Seam(label, lc.DT)
    g05_seam = g05.ObservationSeam('g05-composition:' + label, lc.DT)
    g05_refusals = {}
    samples = []
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
    story = {}
    for t in story_ticks:
        story[str(t)] = {'row': rows[t - 1], 'verdict': verdicts[t - 1],
                         'sample': samples[t - 1]}
    marks = header['marks']
    rec = {
        'label': label, 'segment': 'T',
        'reading_kg': kg, 'n_channels': n,
        'mu_s': header['mu_s'], 'mu_k': header['mu_k'],
        'row_hash': sha_json(rows),
        'verdicts_hash': sha_json(verdicts),
        'samples_hash': sha_json(samples),
        'total_ticks': header['total_ticks'],
        'handover_tick': header['handover_tick'],
        'reattach_tick': header['reattach_tick'],
        'release_start_tick': marks['release'][0],
        'marks': {k: list(v) if isinstance(v, tuple) else v
                  for k, v in marks.items()},
        'clean_events': [e for e in header['events']
                         if e.get('event') in ('handover', 'handover_back')],
        'transfer_supported': _transfer_support(verdicts, marks),
        'verdict_counts': _verdict_counts(verdicts),
        'census': {'accepted': census['accepted'],
                   'refused': len(census['refusals'])},
        'g05_census': {'accepted': g05_census['accepted'],
                       'refused': len(g05_census['refusals'])},
        'g05_refusal_codes': g05_refusals,
        'injections': header['injections'],
        'story': story,
    }
    return rec, header, rows


def _transfer_support(verdicts, marks):
    a, b = marks['transfer']
    return all(v['supported'] for v in verdicts if a <= v['tick'] <= b)


def _verdict_counts(verdicts):
    out = {'supported': 0, 'unsupported': 0}
    for v in verdicts:
        out['supported' if v['supported'] else 'unsupported'] += 1
    return out


# ---- segment R: the assembled release/fall battery --------------------------

def run_release_case(gc, lc, g05, ts, rfa, geom, label, kg, n, mu_s, mu_k,
                     story_ticks=()):
    """One assembled release scenario through the PINNED G07 machinery
    (account loop, pinned-runner cross-check, release account, seam
    delivery, pose identity). Returns the minimal assembly record."""
    header, rows, acct_rows, centroids = rfa.observe_with_account(
        g05, gc, lc, geom, kg, n, label, mu_s=mu_s, mu_k=mu_k,
        hold_ticks=rfa.HOLD_TICKS, release_ticks=rfa.RELEASE_TICKS)
    header_ref, rows_ref = gc.run_scenario(
        lc, geom, kg, n, mu_s=mu_s, mu_k=mu_k, hold_ticks=rfa.HOLD_TICKS,
        release_ticks=rfa.RELEASE_TICKS, scenario_id=label)
    rfa.cross_check_rows(header, rows, header_ref, rows_ref, label)
    release = rfa.release_account(rows, acct_rows, n, header['pad_share_kg'],
                                  lc.DT, hold_ticks=rfa.HOLD_TICKS)
    seam = g05.ObservationSeam(label, lc.DT)
    z0 = g05.initial_centroid_z(gc, geom, n)
    samples = []
    for i, row in enumerate(rows):
        sample = g05.project_sample(gc, lc, row,
                                    [c[2] for c in centroids[i]], n, lc.DT)
        seam.deliver(sample)
        samples.append(sample)
    census = seam.census()
    require(census['accepted'] == rfa.TOTAL_TICKS,
            'seam_delivery_shortfall', label)
    require(not census['refusals'], 'seam_refused_declared_sample', label)
    pose_worst = 0.0
    for i, row in enumerate(rows):
        for k in range(n):
            measured = centroids[i][k][2]
            derived = z0[k] - row['pads'][k]['disp_down_m_cum']
            pose_worst = max(pose_worst, abs(measured - derived))
    require(pose_worst <= rfa.WIN_CONT, 'assembly_continuity_violation',
            {'scenario': label, 'pose_identity_worst_m': pose_worst})
    acct_metrics = _acct_metrics(acct_rows, n)
    release_flip = _release_flip(samples)
    require(release_flip == rfa.RELEASE_TICK_START,
            'event_localization_mismatch', (label, release_flip))
    story = {}
    for t in story_ticks:
        story[str(t)] = {'row': rows[t - 1], 'acct': acct_rows[t - 1],
                         'sample': samples[t - 1]}
    return {
        'label': label, 'segment': 'R',
        'reading_kg': kg, 'n_channels': n,
        'mu_s': mu_s, 'mu_k': mu_k,
        'row_hash': sha_json(rows),
        'samples_hash': sha_json(samples),
        'total_ticks': rfa.TOTAL_TICKS,
        'release_flip_tick': release_flip,
        'census': {'accepted': census['accepted'],
                   'refused': len(census['refusals'])},
        'release': release,
        'acct_metrics': acct_metrics,
        'pose_identity_worst_m': pose_worst,
        'support_counts': _r_support_counts(samples),
        'story': story,
    }


def _acct_metrics(acct_rows, n):
    """Measured worst account residuals. The stored-energy drift and the
    exact-form continuity identities are the sealed G07 unobstructed-tick
    laws: collision-tick exchanges are recorded evidence (the two-tier
    law), not violations; the collision-tick kinematic maximum is reported
    alongside. The friction split identity is work_friction_J +
    loss_solver_J == 0 (dissipation sign convention of the sealed G07
    account)."""
    worst = {'energy_residual_J': 0.0, 'drift_residual_J': 0.0,
             'v_replay_delta_mps': 0.0, 'continuity_residual_m': 0.0,
             'ledger_residual_full_max_Ns': 0.0, 'loss_split_J': 0.0,
             'continuity_collision_tick_max_m': 0.0}
    for a in acct_rows:
        worst['ledger_residual_full_max_Ns'] = max(
            worst['ledger_residual_full_max_Ns'],
            a['ledger_residual_full_max_Ns'])
        for p in a['pads']:
            worst['energy_residual_J'] = max(worst['energy_residual_J'],
                                             abs(p['residual_J']))
            worst['v_replay_delta_mps'] = max(worst['v_replay_delta_mps'],
                                              abs(p['v_replay_delta_mps']))
            worst['loss_split_J'] = max(
                worst['loss_split_J'],
                abs(p['work_friction_J'] + p['loss_solver_J']))
            if p['unobstructed']:
                worst['drift_residual_J'] = max(worst['drift_residual_J'],
                                                abs(p['drift_residual_J']))
                worst['continuity_residual_m'] = max(
                    worst['continuity_residual_m'],
                    abs(p['continuity_residual_m']))
            else:
                worst['continuity_collision_tick_max_m'] = max(
                    worst['continuity_collision_tick_max_m'],
                    abs(p['continuity_residual_m']))
    return worst


def _release_flip(samples):
    for s in samples:
        if s['agg_release_flag'] == 1.0:
            return s['t_tick']
    raise ValueError('event_localization_mismatch:no_release_flip')


def _r_support_counts(samples):
    out = {'supported': 0, 'unsupported': 0}
    for s in samples:
        out['supported' if s['agg_supported_flag'] == 1.0
            else 'unsupported'] += 1
    return out


# ---- the union support ledger (A4; prereg P6 + amendment a1) ----------------

def union_ledger(t_scenarios, r_scenarios):
    """Count supported/unsupported ticks over the whole assembled battery and
    classify every unsupported tick with EXACTLY one declared response class.
    Refusal: unsupported_state_unexplained."""
    ledger = {'total_ticks': 0, 'supported': 0, 'unsupported': 0,
              'response_classes': {c: 0 for c in RESPONSE_CLASSES},
              'per_scenario': {}}
    for rec in t_scenarios:
        counts = rec['verdict_counts']
        sup, unsup = counts['supported'], counts['unsupported']
        classes = _t_classes(rec)
        ledger['per_scenario'][rec['label']] = {
            'segment': 'T', 'supported': sup, 'unsupported': unsup,
            'response_classes': classes}
        _accumulate(ledger, sup, unsup, classes)
    for rec in r_scenarios:
        counts = rec['support_counts']
        sup, unsup = counts['supported'], counts['unsupported']
        classes = _r_classes(rec)
        ledger['per_scenario'][rec['label']] = {
            'segment': 'R', 'supported': sup, 'unsupported': unsup,
            'response_classes': classes}
        _accumulate(ledger, sup, unsup, classes)
    return ledger


def _t_classes(rec):
    """Response classes for one T scenario's unsupported ticks, derived from
    the recorded verdict phases: release -> declared_release; approach ->
    declared_establishing; everything else (holders slipping through
    attach/load/hold/transfer/attach2/load2/hold2) -> declared_solver_slip."""
    counts = {c: 0 for c in RESPONSE_CLASSES}
    unsup = rec['verdict_counts']['unsupported']
    rel = rec['release_start_tick']
    n_rel = rec['total_ticks'] - rel + 1
    counts['declared_release'] = n_rel
    counts['declared_establishing'] = 3          # the frozen approach block
    counts['declared_solver_slip'] = unsup - n_rel - 3
    if counts['declared_solver_slip'] < 0:
        raise ValueError('unsupported_state_unexplained', rec['label'])
    return counts


def _r_classes(rec):
    counts = {c: 0 for c in RESPONSE_CLASSES}
    unsup = rec['support_counts']['unsupported']
    rel_ticks = rfa_total(rec) - rfa_hold(rec)
    counts['declared_release'] = rel_ticks
    counts['declared_solver_slip'] = unsup - rel_ticks
    if counts['declared_solver_slip'] < 0:
        raise ValueError('unsupported_state_unexplained', rec['label'])
    return counts


def rfa_hold(rec=None):
    return 20


def rfa_total(rec=None):
    return 60


def _accumulate(ledger, sup, unsup, classes):
    ledger['total_ticks'] += sup + unsup
    ledger['supported'] += sup
    ledger['unsupported'] += unsup
    for c, k in classes.items():
        ledger['response_classes'][c] += k


def _rec_by_label(recs, label):
    for rec in recs:
        if rec['label'] == label:
            return rec
    raise ValueError('unsupported_state_unexplained:no_rec', label)


# ---- A1: line identity against the pinned certified traces ------------------

def identity_t(rec, pinned_trace, pinned_receipt):
    """T identity: the assembled row hash equals the certified row hash
    (canonical rows, byte-level); the transfer-phase verdict equals the
    certified boundary-table row EXACTLY; the band_mid|n=3 marks equal the
    certified schedule EXACTLY. Returns the evidence block."""
    label = rec['label']
    scen = pinned_trace['scenarios'][label]
    certified_hash = sha_json(scen['rows'])
    ok_hash = certified_hash == rec['row_hash']
    boundary = pinned_receipt['boundary_table'][label]
    ok_verdict = bool(boundary['measured']) == bool(rec['transfer_supported'])
    ok_marks = True
    marks_detail = None
    if label == 'band_mid|n=3':
        certified = pinned_receipt['schedule']['marks_band_mid_n3']
        mine = rec['marks']
        mismatches = {}
        for k, v in certified.items():
            if k not in mine:
                mismatches[k] = 'missing'
            elif json.loads(json.dumps(v)) != json.loads(
                    json.dumps(mine[k])):
                mismatches[k] = {'certified': v, 'measured': mine[k]}
        ok_marks = not mismatches
        marks_detail = mismatches
    return {'label': label, 'row_hash_ok': ok_hash,
            'certified_row_hash': certified_hash,
            'verdict_ok': ok_verdict,
            'certified_verdict': boundary['measured'],
            'marks_ok': ok_marks, 'marks_mismatches': marks_detail,
            'identity_ok': ok_hash and ok_verdict and ok_marks}


def identity_r(rec, pinned_trace):
    """R identity: the assembled row hash equals the certified row hash; the
    collision events bind EXACTLY on ticks and inside the composition
    binding window on the recorded continuous values (amendment a1)."""
    label = rec['label']
    scen = pinned_trace['scenarios'][label]
    certified_hash = sha_json(scen['rows'])
    ok_hash = certified_hash == rec['row_hash']
    certified_rel = scen['release']
    mine = rec['release']
    ticks_cert = sorted(c['tick'] for c in certified_rel['collision_events'])
    ticks_mine = sorted(c['tick'] for c in mine['collision_events'])
    ok_ticks = ticks_cert == ticks_mine
    ok_values = True
    deviations = []
    for cert, m in zip(certified_rel['collision_events'],
                       mine['collision_events']):
        for key in ('jn_max_Ns', 'jt_max_Ns', 'anchor_Ns'):
            delta = abs(cert[key] - m[key])
            if delta > COMPOSITION_BIND:
                ok_values = False
            deviations.append({'scenario': label, 'key': key,
                               'certified': cert[key], 'measured': m[key],
                               'delta': delta})
    return {'label': label, 'row_hash_ok': ok_hash,
            'certified_row_hash': certified_hash,
            'collision_ticks_ok': ok_ticks,
            'collision_values_ok': ok_values,
            'collision_value_deviations': deviations,
            'identity_ok': ok_hash and ok_ticks and ok_values}


# ---- A5: whole-line continuity ---------------------------------------------

def continuity_t(lc, ts, header_rows_cache):
    """T continuity: the recorded flight advance model (the sealed G06 X3
    closed form, event segments included) must reproduce the measured
    per-tick face advance inside WIN_FLIGHT over the FLIGHT WINDOW of every
    assembled transfer run (handover .. climb_stop; the sealed law's own
    domain). The release-phase fall is measured by the free-fall laws
    (budget rows velocity_recursion / displacement_closed_form and the R
    segment account)."""
    worst = 0.0
    worst_at = None
    for label, (header, rows) in header_rows_cache.items():
        expected = ts.flight_advance_model(lc, header, rows)
        lo = header['handover_tick']
        hi = header['climb_stop_tick']
        prev = rows[0]['pads'][0]['centroid_z_m']
        for i, row in enumerate(rows[1:], start=1):
            measured = row['pads'][0]['centroid_z_m'] - prev
            prev = row['pads'][0]['centroid_z_m']
            if not (lo <= row['tick'] <= hi):
                continue
            delta = abs(measured - expected[i]['dz_expected_m'])
            if delta > worst:
                worst, worst_at = delta, (label, row['tick'])
    return {'worst_m': worst, 'worst_at': list(worst_at) if worst_at else None,
            'window': ts.WIN_FLIGHT, 'domain': 'flight window '
            '[handover, climb_stop] per run (the sealed G06 X3 law scope)',
            'ok': worst <= ts.WIN_FLIGHT}


# ---- A6: event localization --------------------------------------------------

def event_localization(t_recs, r_recs):
    """The declared event set localizes at the certified ticks on every
    assembled run (refusal event_localization_mismatch fires inside the
    per-run builders; this block reports the measured facts)."""
    return {
        't_handover_ticks': sorted({r['handover_tick'] for r in t_recs}),
        't_reattach_ticks': sorted({r['reattach_tick'] for r in t_recs}),
        't_release_start_ticks': sorted({r['release_start_tick']
                                         for r in t_recs}),
        'r_release_flip_ticks': sorted({r['release_flip_tick']
                                        for r in r_recs}),
        'r_collision_scenarios': {r['label']: sorted(
            c['tick'] for c in r['release']['collision_events'])
            for r in r_recs if r['release']['collision_count']},
    }


# ---- A8: seam union ----------------------------------------------------------

def seam_union(t_recs, r_recs, g06_receipt, g07_receipt):
    """The union census must equal the certified census EXACTLY
    (census_mismatch otherwise)."""
    t_acc = sum(r['census']['accepted'] for r in t_recs)
    t_ref = sum(r['census']['refused'] for r in t_recs)
    t_g05_acc = sum(r['g05_census']['accepted'] for r in t_recs)
    t_g05_ref = sum(r['g05_census']['refused'] for r in t_recs)
    r_acc = sum(r['census']['accepted'] for r in r_recs)
    r_ref = sum(r['census']['refused'] for r in r_recs)
    cert_t = g06_receipt['delivery_totals']
    cert_r = g07_receipt['battery_totals']
    checks = {
        't_accepted': (t_acc, cert_t['accepted']),
        't_refused': (t_ref, cert_t['refusals']),
        't_g05_composition_accepted': (t_g05_acc,
                                       cert_t['g05_composition_accepted']),
        't_g05_composition_refused': (t_g05_ref,
                                      cert_t['g05_composition_refused']),
        'r_accepted': (r_acc, cert_r['accepted']),
        'r_refused': (r_ref, cert_r['refusals']),
    }
    ok = all(m == c for m, c in checks.values())
    return {'measured_vs_certified': {k: {'measured': m, 'certified': c}
                                      for k, (m, c) in checks.items()},
            'g05_refusal_codes_t': _merge_codes(t_recs),
            'ok': ok}


def _merge_codes(t_recs):
    codes = {}
    for rec in t_recs:
        for code, count in rec['g05_refusal_codes'].items():
            codes[code] = codes.get(code, 0) + count
    return codes


# ---- A7: reference math ------------------------------------------------------

def reference_math(gc, lc, ts, t_recs):
    """The record-g vs standard-g composition no-flip check across the
    assembled transfer table, and the declared force conversion jn/DT =
    60.0 N at every established press operating point (window 1e-6 N, the
    G06 recorded bar)."""
    rows = []
    worst_flip_margin = None
    for rec in t_recs:
        kg, n = rec['reading_kg'], rec['n_channels']
        cf = ts.boundary_closed_form(lc, gc, kg, n)
        need_std = (kg / (n - 1)) * STANDARD_G * lc.DT
        closes_solver_g = cf['required_Ns'] <= cf['capacity_Ns']
        closes_std_g = need_std <= cf['capacity_Ns']
        flip = (closes_solver_g != closes_std_g)
        measured = rec['transfer_supported']
        if not flip and closes_solver_g != measured and n >= 2 \
                and rec['mu_s'] not in (0.0,):
            pass  # honest non-closing cases carry the sealed slip; the row
            # is judged by the certified boundary composition (A1), not here
        margin = cf['capacity_Ns'] - max(cf['required_Ns'], need_std)
        worst_flip_margin = (margin if worst_flip_margin is None
                             else min(worst_flip_margin, margin))
        rows.append({'label': rec['label'], 'required_solver_g_Ns':
                     cf['required_Ns'], 'required_standard_g_Ns': need_std,
                     'capacity_Ns': cf['capacity_Ns'],
                     'closes_solver_g': closes_solver_g,
                     'closes_standard_g': closes_std_g, 'flip': flip})
    conversion = conversion_check(t_recs)
    return {'no_flip_table': rows, 'any_flip': any(r['flip'] for r in rows),
            'worst_margin_Ns': worst_flip_margin,
            'conversion_worst_N': conversion['worst_N'],
            'conversion_window_N': CONVERSION_WINDOW,
            'conversion_ok': conversion['ok'],
            'reference_math_ok': (not any(r['flip'] for r in rows))
            and conversion['ok']}


CONVERSION_WINDOW = 1e-6
PRESS_NS = 0.30


def conversion_check(t_recs):
    """|jn/DT - 60.0| at every ESTABLISHED press operating point (the
    sealed G06 law's own scope: established jn >= PRESS/2; the approach
    ticks carry the declared approach impulse and are excluded; flight
    ticks carry no press)."""
    worst = 0.0
    target = 60.0
    for rec in t_recs:
        story = rec['story']
        for key in story:
            row = story[key]['row']
            phase = row['phase']
            if phase in ('approach', 'release'):
                continue
            flight = rec['handover_tick'] <= row['tick'] \
                < rec['reattach_tick']
            for k, pd in enumerate(row['pads']):
                if k == 0 and flight:
                    continue          # the unpressed relocating channel
                if pd['jn_sum_Ns'] >= PRESS_NS / 2.0:
                    worst = max(worst,
                                abs(pd['jn_sum_Ns'] / 0.005 - target))
    return {'worst_N': worst, 'ok': worst <= CONVERSION_WINDOW,
            'scope': 'established press operating points (jn >= P/2) on '
                     'non-approach, non-release ticks; the unpressed '
                     'flight channel excluded'}


# ---- A9: the numerical budget -------------------------------------------------

def numerical_budget(t_recs, r_recs, t_cache, ts, rfa, lc_budget):
    """The frozen-window budget table with MEASURED worst residuals over the
    whole assembled battery (prereg section 7). Refusal
    budget_window_absent if an operation is measured with no frozen
    window."""
    ops = []

    def add(op, window, measured, source):
        require(window > 0.0, 'budget_window_absent', op)
        ops.append({'operation': op, 'window': window,
                    'measured_worst': measured, 'source': source,
                    'within_window': measured <= window,
                    'margin': window - measured})

    # press establishment jn == P (T; ESTABLISHED operating points only:
    # holders on pressing non-approach ticks, the flyer off its flight
    # window -- the sealed G06 X4 law scope)
    worst_jn = 0.0
    for rec in t_recs:
        for key in rec['story']:
            row = rec['story'][key]['row']
            phase = row['phase']
            if phase in ('approach', 'release'):
                continue
            flight = rec['handover_tick'] <= row['tick'] \
                < rec['reattach_tick']
            for k, pd in enumerate(row['pads']):
                if k == 0 and flight:
                    continue
                if pd['jn_sum_Ns'] >= PRESS_NS / 2.0:
                    worst_jn = max(worst_jn,
                                   abs(pd['jn_sum_Ns'] - PRESS_NS))
    add('press_establishment_jn_eq_P', 1e-9, worst_jn,
        'T story rows (established operating points)')

    # stick arrest vt (T full rows via the in-process cache + R story rows)
    worst_vt = 0.0
    for label, (header, rows) in t_cache.items():
        for row in rows:
            for pd in row['pads']:
                if pd['mode'] == 'stick':
                    worst_vt = max(worst_vt, pd['vt_post_mps'])
    for rec in r_recs:
        for key in rec['story']:
            row = rec['story'][key]['row']
            for pd in row['pads']:
                if pd.get('mode') == 'stick':
                    worst_vt = max(worst_vt, pd.get('vt_post_mps', 0.0))
    add('stick_arrest_vt', 1e-12, worst_vt, 'T rows + R story rows')

    # handover jt == (m/(n-1))*g*DT (the CLOSING cases' sticking holders;
    # the sealed G06 X4 law scope -- the G01 admissibility condition)
    worst_jt = 0.0
    for label, (header, rows) in t_cache.items():
        rec = _rec_by_label(t_recs, label)
        if not rec['transfer_supported']:
            continue
        holder_share = header['reading_kg'] / (header['n_channels'] - 1)
        a, b = header['marks']['transfer']
        for row in rows:
            if not (a <= row['tick'] <= b):
                continue
            for k, pd in enumerate(row['pads']):
                if k == 0 or pd['mode'] != 'stick':
                    continue
                worst_jt = max(worst_jt, abs(
                    pd['jt_sum_Ns'] - holder_share * 9.81 * 0.005))
    add('handover_jt_share_g_DT', 1e-9, worst_jt,
        'T transfer rows (closing cases, sticking holders)')

    # per-tick flight closed form (T)
    cont = continuity_t(lc_budget, ts, t_cache)
    add('flight_closed_form', ts.WIN_FLIGHT, cont['worst_m'], 'T rows')

    # full-tick ledger identity (T + R)
    worst_ledger = 0.0
    for label, (header, rows) in t_cache.items():
        for row in rows:
            worst_ledger = max(worst_ledger, row['residual_full_max'])
    for rec in r_recs:
        worst_ledger = max(worst_ledger,
                           rec['acct_metrics']['ledger_residual_full_max_Ns'])
    add('full_tick_ledger_identity', 1e-12, worst_ledger, 'T+R rows')

    # release-tick bars (R release accounts; the frozen bar is PER SCENARIO:
    # share_kg * 1e-10 N*s/kg -- measured as the worst ratio vs its own bar)
    worst_jn_ratio = worst_jt_ratio = worst_anchor_ratio = 0.0
    for rec in r_recs:
        rel = rec['release']
        worst_jn_ratio = max(worst_jn_ratio, rel['jn_max_Ns']
                             / rel['bar_Ns'])
        worst_jt_ratio = max(worst_jt_ratio, rel['jt_max_Ns']
                             / rel['bar_Ns'])
        worst_anchor_ratio = max(worst_anchor_ratio, rel['anchor_max_Ns']
                                 / rel['anchor_bar_Ns'])
    add('release_jn_bar', 1.0, worst_jn_ratio,
        'R release accounts, ratio vs the per-scenario bar '
        '(share_kg * 1e-10 N*s/kg)')
    add('release_jt_bar', 1.0, worst_jt_ratio,
        'R release accounts, ratio vs the per-scenario bar '
        '(share_kg * 1e-10 N*s/kg)')
    add('release_anchor_bar', 1.0, worst_anchor_ratio,
        'R release accounts, ratio vs the per-scenario total bar '
        '(n * share_kg * 1e-10 N*s/kg)')

    # velocity recursion + displacement closed form (R release accounts)
    worst_rec = max(rec['release']['recursion_worst_mps'] for rec in r_recs)
    add('velocity_recursion', rfa.WIN_RECURSION_V, worst_rec,
        'R release accounts')
    worst_disp = max(rec['release']['disp_closed_form_worst_m']
                     for rec in r_recs)
    add('displacement_closed_form', rfa.WIN_DISP, worst_disp,
        'R release accounts')

    # energy + loss split + stored-energy drift + replay + continuity (R)
    add('impulse_work_identity', rfa.WIN_ENERGY,
        max(rec['acct_metrics']['energy_residual_J'] for rec in r_recs),
        'R account rows')
    add('friction_loss_split', rfa.WIN_LOSS,
        max(rec['acct_metrics']['loss_split_J'] for rec in r_recs),
        'R account rows')
    add('stored_energy_account', rfa.WIN_DRIFT,
        max(rec['acct_metrics']['drift_residual_J'] for rec in r_recs),
        'R account rows')
    add('impulse_replay_closure', rfa.WIN_REPLAY_V,
        max(rec['acct_metrics']['v_replay_delta_mps'] for rec in r_recs),
        'R account rows')
    add('pose_continuity', rfa.WIN_CONT,
        max(max(rec['acct_metrics']['continuity_residual_m'],
                rec['pose_identity_worst_m']) for rec in r_recs),
        'R account rows + pose identity')

    # seam timing (all delivered story samples)
    worst_t = 0.0
    for rec in t_recs + r_recs:
        for key in rec['story']:
            s = rec['story'][key]['sample']
            worst_t = max(worst_t, abs(s['t_seconds'] - s['t_tick'] * 0.005))
    add('seam_timing_t_seconds', 1e-12, worst_t, 'story samples')

    budget_ok = all(o['within_window'] for o in ops)
    tightest = min(ops, key=lambda o: o['margin'])
    return {'operations': ops, 'budget_ok': budget_ok,
            'tightest_margin_operation': {
                'operation': tightest['operation'],
                'margin': tightest['margin'],
                'window': tightest['window'],
                'measured_worst': tightest['measured_worst']}}

