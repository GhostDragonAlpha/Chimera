"""SUPPORTED-LANDING battery entry (one process, deterministic).

Stages, in order, executed TWICE (the second pass is the determinism pair):
  1  pin gate (git-tree package files + host lane bytes + the embedded
     capture template manifest, all by sha256); CHIMERA_BASE_SHA asserted
     == the committed prereg commit (the prereg bytes refuse mismatch)
  2  load pinned interfaces (lc solver, gc grip fixture, g05 observation
     seam, the G07 sealed account observer -- imported, never forked)
  3  derive every threshold at run from pinned bytes; value-match presence
     against the pinned corpus (mismatch = refusal threshold_pin_mismatch)
  4  the no-floor reference run (sealed observer at hold 20 + release 59,
     rows bit-identical to gc.run_scenario) -> sealed-window anchors and
     the declared floor placement
  5  the LANDING run: the sealed observer through the declared floor-scene
     shim (the floor present from tick 0), 141 ticks; prefix bit-identity
     against the reference (observer_drift law)
  6  P1-P6 evaluated from the recorded rows/records; P7 fences recorded
  7  scene-composition checks + the undeclared-contact-site census
  8  verdicts P1-P7 as named variables with their derived constants
  9  captures through the embedded standing two-stage gate template (the
     card view-spec hash was pinned in card_prereg.json BEFORE capture)
 10  receipts (canonical bytes; every receipt embeds preregistration_sha256
     of the committed prereg bytes and refuses mismatch)

Then: named checks (unittest, in-process), the determinism pair (trace +
receipt + capture summary byte-identity), and the upstream regression
suites (UNMODIFIED M06/G04/G05) re-run on this exact revision.

Exit codes: 0 all frozen predictions SUPPORTED and all gates green;
3 a falsifier fired or a gate went RED (receipts still written; preserve,
never tune); 4 harness refusal (pin drift, threshold mismatch, undeclared
contact).
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import landing_physics as lp  # noqa: E402

OUT_DIR = os.environ.get('CHIMERA_OUTPUT_DIR') or 'outputs'

PREDICTIONS = {
    'P1_hold_prefix_reproduces_sealed_windows':
        'PASS (the 20 hold ticks at the declared operating point reproduce '
        'the K02-sealed window values within the sealed windows: press bar, '
        'all channels stick, zero creep class, the W20 ledger against the '
        'pinned G07 scene|n=3 values within 1e-9 J)',
    'P2_release_fall_identity_to_declared_floor':
        'PASS (W_press == 0.0 J EXACTLY every release tick; free-fall '
        'recursion within 1e-9 m/s; the first-40 release-tick prefix '
        'reproduces the K02-sealed release account within the declared '
        'windows; the fall continues past the G07 window end on the same '
        'identity; FIRST FLOOR CONTACT at release tick 60 inside the '
        'declared acceptance window {59, 60, 61})',
    'P3_floor_contact_nonpenetration_at_margin':
        'PASS (every recorded pad-floor contact has gap >= -SLOP_M; the '
        'steady minimum gap sits AT the margin (the M06 X1 class); no '
        'crossing without a contact record (the CCD no-tunnel '
        'declaration))',
    'P4_supporting_impulse_two_term_law':
        'PASS (impact term: on each pad\'s first floor-contact tick the '
        'summed floor jn equals the certified inelastic value re-derived '
        'from the recorded pre-impact state within 1e-9 N*s; steady term: '
        'every rest-window tick the per-channel floor jn equals '
        'share*g*DT = 0.1641212673 N*s within the 1e-9 bar; the recorded-'
        'vs-supporting distinction RESOLVED for the landing)',
    'P5_rest_stability_declared_window':
        'PASS (from the settle tick through the declared 60-tick rest '
        'window: post-solve |v| <= 1e-9 m/s every tick every channel; '
        'per-tick displacement <= 1e-9 m; NO upward velocity beyond 1e-9 '
        'm/s (the e = 0 no-bounce declaration); mode census recorded; '
        'TRANSLATIONAL rest only, the solver is translation-only)',
    'P6_energy_destination_through_impact':
        'CLOSE (the sealed observer\'s account runs EVERY tick INCLUDING '
        'the impact tick; on non-CCD ticks the impulse-work identities '
        'close within the sealed windows, enforced in-run; on the CCD '
        'impact tick the destination decomposition is computed from the '
        'recorded records and closes against them; over the whole release '
        'phase the account stops NOWHERE - the K02 stop-before-impact is '
        'EXTENDED through impact to rest)',
    'P7_fences_not_run':
        'FENCED (NO restitution declaration, NO recovery implementation, '
        'NO descent metering, NO transfer phase, NO n=4, NO grasp arm, NO '
        '0.41 arm, NO W-tier surrogate edit runs; stated so the fences are '
        'never smuggled)',
}

PRESENT_PHASES = ('hold', 'release')


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def presence_value(d, key):
    return d[key]


def battery_once(out_dir):
    """One full deterministic pass; returns (trace, receipt)."""
    trace = {'schema': lp.TRACE_SCHEMA,
             'preregistration_sha256': lp.PREREG_SHA256}

    # 1-2: pins and pinned modules
    pin_rows = lp.verify_pins()
    template_rows = lp.verify_template_manifest()
    lc = lp.load_pinned_module(lp.M06_MODULE_REL, lp.M06_MODULE_SHA256,
                               'landing_pinned_local_contact')
    gc = lp.load_pinned_module(lp.G04_MODULE_REL, lp.G04_MODULE_SHA256,
                               'landing_pinned_grip_contact')
    g05 = lp.load_pinned_module(lp.G05_MODULE_REL, lp.G05_MODULE_SHA256,
                                'landing_pinned_contact_obs')
    rfa = lp.load_pinned_host_module(lp.G07_OBSERVER_HOST,
                                     lp.G07_OBSERVER_SHA256,
                                     'landing_pinned_g07_account')
    geom = gc.load_trunk_geometry()

    # 3: derivation + presence
    d = lp.derive(lc, gc, rfa)
    defective_forms = lp.defective_literal_forms(d)
    tokens = {}
    for name, path in lp.PRESENCE_SOURCES.items():
        tokens[name] = lp.numeric_tokens(
            pathlib.Path(path).read_text(encoding='utf-8',
                                         errors='replace'))
    presence = {}
    missing = []
    for key, sources in lp.REQUIRED_PRESENCE:
        value = presence_value(d, key)
        hit = [src for src in sources if lp.value_present(value,
                                                          tokens[src])]
        presence[key] = {'sources_checked': sources, 'found_in': hit}
        if not hit:
            missing.append(key)
    if missing:
        raise lp.LandingRefusal('threshold_pin_mismatch:' + ','.join(missing))
    presence['values'] = {key: presence_value(d, key)
                          for key, _ in lp.REQUIRED_PRESENCE}

    # pinned authorities (JSON-exact extraction from hash-pinned bytes)
    g07_receipt = lp.load_pinned_json(lp.G07_RECEIPT_HOST,
                                      lp.HOST_PINS[lp.G07_RECEIPT_HOST])
    g07_ledger = lp.g07_scene_n3_ledger(g07_receipt)
    k02_receipt = lp.load_pinned_json(lp.K02_RECEIPT_REL,
                                      lp.HOST_PINS[lp.K02_RECEIPT_REL])
    k02_rel = lp.k02_release_authority(k02_receipt)
    k02_hold = lp.k02_hold_authority(k02_receipt)

    reading_kg = d['scene_kg']
    mu_s = d['mu_placeholder_s']
    mu_k = d['mu_placeholder_k']
    press = d['press_ns']

    # 4: the no-floor reference run (anchors + floor placement)
    ref = lp.run_reference(rfa, g05, gc, lc, geom, reading_kg, mu_s, mu_k,
                           press)
    verts0 = lp.initial_pad_verts(gc, geom, lp.READING[1])
    placement = lp.derive_floor_placement(gc, lc, ref['rows'], verts0)
    z_floor = placement['z_floor_m']
    trace['reference_no_floor'] = ref
    trace['floor_placement'] = placement

    # 5: the landing run (the floor present from tick 0)
    arm = lp.run_landing(rfa, g05, gc, lc, geom, reading_kg, mu_s, mu_k,
                         press, z_floor)
    trace['landing'] = arm
    verdicts = {}
    sealed_refusal = arm.get('sealed_law_refusal')
    if sealed_refusal is not None:
        for key, name in (
                ('P1_hold_prefix_reproduces_sealed_windows', 'P1'),
                ('P2_release_fall_identity_to_declared_floor', 'P2'),
                ('P3_floor_contact_nonpenetration_at_margin', 'P3'),
                ('P4_supporting_impulse_two_term_law', 'P4'),
                ('P5_rest_stability_declared_window', 'P5'),
                ('P6_energy_destination_through_impact', 'P6')):
            verdicts[key] = {
                'name': name, 'prediction': PREDICTIONS[key],
                'observed': 'the sealed observer refused in-run: %s; the '
                            'captured side channel holds %d ticks; '
                            'PRESERVED, never repaired'
                            % (sealed_refusal, len(arm['records_log'])),
                'verdict': 'UNMEASURED_SEALED_LAW_REFUSAL_PRESERVED',
                'falsifier_note': 'a sealed-law refusal is a records '
                                  'discrepancy preserved verbatim; it is '
                                  'never tuned and never silently '
                                  'normalized',
                'evidence': {'sealed_law_refusal': sealed_refusal,
                             'ticks_captured': len(arm['records_log'])},
            }
        receipt = _receipt(lp, d, trace, pin_rows, template_rows, presence,
                           g07_ledger, k02_rel, k02_hold, placement,
                           verdicts, None, sealed_refusal)
        receipt['overall_verdict'] = 'SEALED_LAW_REFUSAL_PRESERVED'
        receipt = _assert_retracted_absence(lp, receipt, defective_forms)
        return trace, receipt, None, None

    # 6: the predictions
    prefix_id = lp.prefix_bit_identity(rfa, arm, ref, 'landing_scene_n3')
    trace['prefix_bit_identity'] = prefix_id
    p1 = lp.check_p1_hold_prefix(arm, d, g07_ledger, k02_hold)
    p2 = lp.check_p2_release_fall(arm, ref, prefix_id, d, k02_rel, verts0)
    # the sealed release_account law on the pre-contact fall slice
    first_contact = prefix_id['first_floor_record_tick_abs']
    fall_end = (first_contact - 1) if first_contact is not None \
        else len(arm['rows'])
    try:
        rel_summary = rfa.release_account(
            arm['rows'][:fall_end],
            arm['acct_rows'][:fall_end], lp.READING[1],
            d['share_kg'], lc.DT, hold_ticks=lp.HOLD_TICKS)
        p2['g07_release_account_fall_slice'] = rel_summary
        p2['g07_release_account_fall_slice_state'] = 'CLEAN'
    except ValueError as exc:
        p2['g07_release_account_fall_slice'] = {'refusal': str(exc)}
        p2['g07_release_account_fall_slice_state'] = \
            'REFUSED_PRESERVED_FALSIFIER_CANDIDATE'
    p3 = lp.check_p3_nonpenetration(arm, d, verts0, z_floor)
    p4 = lp.check_p4_supporting_impulse(arm, d)
    p5 = lp.check_p5_rest_stability(arm, d)
    p6 = lp.check_p6_energy_destination(arm, d)
    scene = lp.scene_safety_checks(lc, geom, verts0, z_floor, arm)
    census = lp.site_census(arm)

    checks = {'P1': p1, 'P2': p2, 'P3': p3, 'P4': p4, 'P5': p5, 'P6': p6}
    verdicts['P1_hold_prefix_reproduces_sealed_windows'] = _verdict(
        'P1', 'hold_prefix_reproduces_sealed_windows',
        PREDICTIONS['P1_hold_prefix_reproduces_sealed_windows'], p1,
        'a window breach in the prefix is a records discrepancy '
        '(construction-class question) routed for review, never silently '
        'normalized')
    p2_ok = (not p2['falsified']
             and p2['g07_release_account_fall_slice_state'] == 'CLEAN')
    verdicts['P2_release_fall_identity_to_declared_floor'] = _verdict(
        'P2', 'release_fall_identity_to_declared_floor',
        PREDICTIONS['P2_release_fall_identity_to_declared_floor'],
        dict(p2, falsified=[] if p2_ok else p2['falsified'] +
             ['P2_sealed_release_account_law_refusal']),
        'a floor-contact record outside the declared window, a free-fall '
        'identity breach beyond the declared windows, or any recorded '
        'floor-contact impulse DURING the declared free-fall window is '
        'THE P2 FALSIFIER; a predicted-recording observed is a SUPPORTED '
        'PREDICTION (correction #3 wording law)')
    for key, name, pred, check, note in (
            ('P3_floor_contact_nonpenetration_at_margin', 'P3',
             PREDICTIONS['P3_floor_contact_nonpenetration_at_margin'], p3,
             'any contact record with gap < -SLOP_M, or any tick where a '
             'pad\'s position crosses the floor plane without a recorded '
             'floor contact, is THE P3 FALSIFIER'),
            ('P4_supporting_impulse_two_term_law', 'P4',
             PREDICTIONS['P4_supporting_impulse_two_term_law'], p4,
             'an impact tick whose summed jn violates the re-derived '
             'inelastic identity beyond 1e-9 N*s, or any rest tick whose '
             'support impulse leaves the weight-share bar while the pad '
             'remains at rest, contradicts the certified law as applied - '
             'records discrepancies, never tuned'),
            ('P5_rest_stability_declared_window', 'P5',
             PREDICTIONS['P5_rest_stability_declared_window'], p5,
             'any |v| breach, any upward-motion tick (a bounce would '
             'contradict RESTITUTION 0.0), or any displacement beyond the '
             'declared windows inside the rest window is THE P5 FALSIFIER; '
             'a longer settle is a completed measurement, never tuned'),
            ('P6_energy_destination_through_impact', 'P6',
             PREDICTIONS['P6_energy_destination_through_impact'], p6,
             'any identity window breach on any non-CCD tick, a '
             'missing/incomplete impulse replay (refusal '
             'impulse_replay_incomplete), or a destination decomposition '
             'that does not close against the recorded impulses is THE P6 '
             'FALSIFIER (arithmetic mismatch = records discrepancy routed, '
             'never normalized)')):
        verdicts[key] = _verdict(name, name, pred, check, note)
    verdicts['P7_fences_not_run'] = {
        'name': 'fences_not_run',
        'prediction': PREDICTIONS['P7_fences_not_run'],
        'observed': 'no restitution declaration, no recovery '
                    'implementation, no descent metering, no transfer '
                    'phase, no n=4, no grasp arm, no 0.41 arm, no W-tier '
                    'surrogate edit run exists in this package',
        'verdict': 'FENCED_NOT_RUN',
        'evidence': {'fence_law': 'prereg sections 1/5 P7/9; stated so '
                                  'the fences are never smuggled'},
    }
    falsified = [k for k, v in verdicts.items()
                 if str(v['verdict']).startswith('FALSIFIED')]
    overall = ('PREDICTION_FALSIFIED_PRESERVED: ' + ','.join(falsified)
               if falsified else 'CONFIRMING_MIXED_AS_PREDICTED')

    # 9: captures through the standing two-stage gate template
    states = _capture_states(lp, gc, arm, verts0, z_floor, first_contact)
    sys.path.insert(0, str(HERE / 'capture_card' / 'card'))
    import run_all as card_run_all
    capture_summary = card_run_all.run_cases(out_dir, states)
    capture_summary['preregistration_sha256'] = lp.PREREG_SHA256
    capture_summary_sha = lp.write_canonical(
        os.path.join(out_dir, 'capture_summary.json'), capture_summary)

    receipt = _receipt(lp, d, trace, pin_rows, template_rows, presence,
                       g07_ledger, k02_rel, k02_hold, placement, verdicts,
                       {'scene': scene, 'site_census': census}, None)
    receipt['findings'] = _findings(checks, d)
    receipt['overall_verdict'] = overall
    receipt['capture_summary_sha256'] = capture_summary_sha
    receipt['capture_verdict'] = capture_summary['exit_law_verdict']
    receipt = _assert_retracted_absence(lp, receipt, defective_forms)
    return trace, receipt, scene, census


def _findings(checks, d):
    """Recorded findings (honest deviations, never tuned, routed to the
    Lieutenant with the chain stop)."""
    findings = []
    p3 = checks['P3']
    if p3['margin_class_deviation']:
        findings.append({
            'class': 'steady_gap_margin_class_deviation',
            'finding': p3['margin_class_deviation']
            + ' Measured steady gaps: '
            + '; '.join('%s %.17g m' % (p['pad'], p['steady_min_gap_m'])
                        for p in p3['per_pad_steady_gaps'])
            + '.',
            'disposition': 'recorded finding; routed to the Lieutenant '
                           'with the chain stop; P3 verdict keys on its '
                           'named falsifier (gap < -SLOP or a crossing '
                           'without a record), which did not fire',
        })
    p4 = checks['P4']
    impact_rows = [r for pad in p4['per_pad_impulse_series']
                   for r in pad['floor_ticks'] if r.get('is_impact_tick')]
    if impact_rows:
        findings.append({
            'class': 'declared_impact_tick_structure',
            'finding':
                'the recorded per-channel impact structure inside the '
                'declared acceptance window {59, 60, 61}: '
                + '; '.join(
                    '%s impact at release tick %d (jn_total %.9g N*s, '
                    'inelastic identity delta %.3g N*s)'
                    % (r.get('pad', pad['pad']), r['tick'] - lp.HOLD_TICKS,
                       r['jn_total_Ns'], r.get('jn_identity_delta_Ns', 0.0))
                    for pad in p4['per_pad_impulse_series']
                    for r in pad['floor_ticks']
                    if r.get('is_impact_tick'))
                + '. The spread is the prereg\'s declared honest risk (a): '
                'the pads\' ~1e-13-class release-z spread and the '
                'event-driven CCD commit place the earliest pad at release '
                'tick 60 (the closed-form prediction) and the trailing '
                'pads one tick later, all inside the declared window.',
            'disposition': 'recorded structure; a predicted-recording '
                           'observed is a SUPPORTED PREDICTION (correction '
                           '#3 wording law)',
        })
    return findings


def _verdict(name, check_name, prediction, check, falsifier_note):
    ok = not check.get('falsified')
    return {
        'name': check_name,
        'prediction': prediction,
        'observed': ('all declared windows inside their bounds'
                     if ok else 'fired: ' + ','.join(check['falsified'])),
        'verdict': 'SUPPORTED' if ok else 'FALSIFIED',
        'falsifier_note': falsifier_note,
        'evidence': check,
    }


def _capture_states(lp, gc, arm, verts0, z_floor, first_contact):
    """Recorded-state capture cases: mid-fall (release tick 30), the
    FIRST-CONTACT frame (the trace's recorded tick), and the rest frame at
    the window end. Every rendered scene state is a fixture projection of
    RECORDED run state; nothing is invented at render time."""
    def state_at(tick_abs, family_note):
        row = arm['rows'][tick_abs - 1]
        disp = [row['pads'][k]['disp_down_m_cum']
                for k in range(lp.READING[1])]
        pad_verts = [[(v[0], v[1], v[2] - disp[k]) for v in verts0[k]]
                     for k in range(lp.READING[1])]
        events = []
        for i, records in enumerate(arm['records_log'][:tick_abs]):
            for k in range(lp.READING[1]):
                if lp.floor_records_for_pad(records, 'grip.pad_%d' % k):
                    events.append({'tick': i + 1, 'site': 'grip.pad_%d' % k})
        return {
            'kind': 'landing', 'family_note': family_note,
            'tick_abs': tick_abs,
            'pad_verts': pad_verts,
            'pad_modes': [row['pads'][k]['mode']
                          for k in range(lp.READING[1])],
            'attach': [c['centroid_m06']
                       for c in arm['header']['channels']],
            'normals': [c['normal_m06']
                        for c in arm['header']['channels']],
            'disp': disp,
            'fall_disp': disp,
            'floor_z_m': z_floor,
            'floor_half_m': lp.FLOOR_HALF_M,
            'ground_contacts': events,
        }

    midfall_tick = lp.HOLD_TICKS + 30
    contact_tick = first_contact if first_contact is not None \
        else len(arm['rows'])
    rest_tick = len(arm['rows'])
    states = {
        'landing_midfall': state_at(midfall_tick,
                                    'the release/fall frame mid-fall '
                                    '(release tick 30)'),
        'landing_first_contact': state_at(
            contact_tick, 'the FIRST-CONTACT frame (the trace\'s recorded '
                          'impact tick)'),
        'landing_rest_end': state_at(
            rest_tick, 'the rest frame at the declared window end'),
    }
    return states


def _receipt(lp, d, trace, pin_rows, template_rows, presence, g07_ledger,
             k02_rel, k02_hold, placement, verdicts, scene_block,
             sealed_refusal, extra=None):
    dt = d['dt_s']
    receipt = {
        'schema': lp.SCHEMA,
        'card': 'MAT2-SUPPORTED-LANDING',
        'card_label': 'FIXTURE-CLASS: the declared release fixture onto '
                      'the declared floor fixture; NEVER a grasp-chain '
                      'claim, never evidence about the anatomical hand '
                      '(B6 untouched) or the playable objective (prereg '
                      'section 0.3 objective law: a supported fixture '
                      'landing completes a diagnostic demonstration of '
                      'the certified contact line\'s ground response, '
                      'nothing more)',
        'preregistration_sha256': lp.PREREG_SHA256,
        'prereg_commit': lp.PREREG_COMMIT,
        'base_sha': lp.BASE_SHA,
        'impl_base_verification': lp.IMPL_BASE_NOTE,
        'prereg_bytes_in_package': {
            'path': lp.PREREG_REL,
            'sha256': lp.PREREG_SHA256,
            'refusal': 'the pin gate refuses any byte mismatch '
                       '(input_pin_drift); every emitted receipt embeds '
                       'preregistration_sha256 of exactly the committed '
                       'bytes',
        },
        'pins': pin_rows,
        'template_pins': template_rows,
        'derivation': d,
        'derivation_presence': presence,
        'floor_placement': placement,
        'scene_extension': (trace['landing']['scene_extension']
                            if 'landing' in trace else None),
        'observer_cross_checks': {
            'reference_no_floor':
                trace['reference_no_floor']['observer_cross_check'],
            'landing_prefix':
                trace.get('prefix_bit_identity', {}).get(
                    'law', 'unmeasured (sealed-law refusal preserved)'),
            'landing_prefix_ticks_compared':
                trace.get('prefix_bit_identity', {}).get(
                    'prefix_ticks_compared'),
        },
        'g07_reference': g07_ledger,
        'k02_release_authority': k02_rel,
        'k02_hold_authority': k02_hold,
        'sealed_law_refusal': sealed_refusal,
        'declared_structure': {
            'hold_ticks': lp.HOLD_TICKS,
            'fall_ticks_to_contact': lp.FALL_TICKS_TO_CONTACT,
            'contact_window_release_ticks': list(lp.CONTACT_WINDOW),
            'rest_ticks': lp.REST_TICKS,
            'total_ticks': lp.TOTAL_TICKS,
            'release_ticks_observed': lp.RELEASE_TICKS_OBSERVED,
            'floor_extent_m': [2 * lp.FLOOR_HALF_M, 2 * lp.FLOOR_HALF_M],
            'floor_body_id': lp.FLOOR_BODY_ID,
            'floor_matter_id': lp.FLOOR_MATTER,
            'one_arm_plus_byte_identical_rerun': True,
        },
        'declared_annotations': {
            'law': 'seconds computed FROM the frozen tick counts at '
                   'DT = 0.005 s (200 Hz); tick counts are the frozen '
                   'executable quantities (the K01 finding-1 class of '
                   'annotation mismatch is impossible by construction)',
            'hold_seconds': lp.HOLD_TICKS * dt,
            'fall_seconds': lp.FALL_TICKS_TO_CONTACT * dt,
            'rest_seconds': lp.REST_TICKS * dt,
            'cadence_hz': d['cadence_hz'],
            'max_scene_seconds': lp.TOTAL_TICKS * dt,
        },
        'declared_tolerance_windows': {
            'win_jn_press_Ns': lp.WIN_JN_PRESS,
            'win_energy_cross_J': lp.WIN_ENERGY_CROSS,
            'win_recursion_v_mps': lp.WIN_RECURSION_V,
            'win_disp_m': lp.WIN_DISP,
            'win_release_scale_Ns_per_kg': lp.WIN_RELEASE_SCALE,
            'win_impact_identity_Ns': lp.WIN_IMPACT_IDENTITY,
            'win_steady_support_Ns': lp.WIN_STEADY_SUPPORT,
            'win_rest_v_mps': lp.WIN_REST_V,
            'win_steady_gap_m': lp.WIN_STEADY_GAP,
            'win_destination_closure_J': lp.WIN_DEST_CLOSE,
            'observer_windows_imported': d['observer_windows'],
        },
        'mu_label': {
            'pad_and_floor_0_6_0_4':
                'NAMED PLACEHOLDERS (FRICTION_SOURCES verdict GAP; REPIN '
                'ORDER 2; acquisition gap NB-01/02 STANDS); the floor '
                'values are the SAME placeholders DECLARED for the '
                'fixture class - a screening choice, never a measurement, '
                'never tuned; no re-pin mid-run; the 0.41 scenario '
                'parameter is NOT used by this card at all (fenced)',
            'trunk_0_6_0_6': 'F03 declared placeholder layer (unchanged)',
        },
        'objective_law': 'DEMONSTRATED IMPOSSIBILITY CAN CLOSE AN '
                         'INVESTIGATION, BUT IT CANNOT COMPLETE THE '
                         'PLAYABLE-MONKEY GOAL: the supported landing '
                         'measured here is a FIXTURE-CLASS transition; it '
                         'NEVER completes the playable release-and-land '
                         'objective; a predicted failure completes a '
                         'diagnostic, never the objective',
        'honest_absent_inventory': {
            'A1': 'fixture class (declared pads onto a declared floor)',
            'A2': 'restitution/impact-model scope: the certified line\'s '
                  'impact response is the DECLARED INELASTIC law (e = 0); '
                  'no nonzero-restitution model exists, is assumed or is '
                  'requested',
            'A3': 'angular dynamics: the solver is TRANSLATION-ONLY; '
                  'translational rest only; toppling unmodeled',
            'A4': 'descent metering fenced (K04-class)',
            'A5': 'recovery absent (X03-class)',
            'A6': 'friction UNMEASURED (NB-01/02 stand)',
            'A7': 'mass-accounting open items OI-1..OI-5 stay open',
            'A8': 'training-spec items not frozen by this physical leg',
            'A9': 'rest persistence beyond the declared window unmeasured',
        },
        'scene_checks': scene_block,
        'verdicts': verdicts,
        'overall_verdict': None,
    }
    return receipt


def _assert_retracted_absence(lp, receipt, defective_forms):
    """The five RETRACTED defective static quotes NEVER enter any
    artifact: serialize, tokenize the emitted bytes, assert absence."""
    staged = canonical(receipt)
    staged_tokens = lp.numeric_tokens(staged.decode('utf-8'))
    present = [key for key, value in defective_forms.items()
               if lp.value_present(value, staged_tokens)]
    absence = {'checked': len(defective_forms), 'present': present,
               'status': ('ABSENT_OK' if not present
                          else 'RETRACTED_QUOTE_PRESENT_PRESERVED_FAILURE')}
    receipt['retracted_quote_absence'] = absence
    return receipt


def run_named_checks(receipt, trace, regression):
    import io
    import unittest
    import test_landing_checks as checks
    checks.STATE['receipt'] = receipt
    checks.STATE['trace'] = trace
    checks.STATE['regression'] = regression
    suite = unittest.defaultTestLoader.loadTestsFromModule(checks)
    runner = unittest.TextTestRunner(verbosity=0, stream=io.StringIO())
    result = runner.run(suite)
    rows = []
    for case, err in list(result.failures) + list(result.errors):
        rows.append({'test': str(case), 'status': 'FAIL',
                     'detail': (err or '').splitlines()[-1][:200]})
    return {
        'schema': 'chimera.landing_named_checks.v1',
        'preregistration_sha256': lp.PREREG_SHA256,
        'tests_run': result.testsRun, 'failures': rows,
        'green': result.wasSuccessful(),
    }


def run_regression():
    """The UNMODIFIED upstream suites re-run as direct scripts (the K02
    regression invocation). DECLARED SCOPE (recorded, never silent): the
    gate suites are the three direct upstream interfaces of this card -
    M06 (the solver), G04 (the grip fixture) and G05 (the observation
    seam). The M06 suite's P12 leg re-runs the M01/M02/M04 suites (and an
    engine asset) outside this package's declared read scope, so a
    full-repository M06 run is NOT claimed (NO_WORKTREES: reduced packages
    never claim full-repository gates). The M06 row is green for this card
    iff P1-P11 all PASS and the ONLY failure is the P12 out-of-scope file
    miss; any probe failure fails the gate."""
    suites = [
        ('M06', '../MAT2-M06', 'test_local_contact.py'),
        ('G04', '../MAT2-G04', 'test_g04_checks.py'),
        ('G05', '../MAT2-G05', 'test_g05_checks.py'),
    ]
    rows = []
    for name, rel, fname in suites:
        suite_dir = (lp.HERE / rel).resolve()
        proc = subprocess.run(
            [sys.executable, '-B', str(suite_dir / fname)],
            capture_output=True, text=True, cwd=str(suite_dir))
        rows.append({
            'suite': name, 'path': str(suite_dir / fname),
            'suite_unmodified': True, 'exit_code': proc.returncode,
            'tail': ((proc.stderr or '') + (proc.stdout or ''))[-1500:],
        })
    by_name = dict((r['suite'], r) for r in rows)
    m06 = by_name['M06']
    m06_tail = m06['tail']
    m06_probe_failure = any(
        ('FAIL P%d ' % i) in m06_tail and
        ('PASS P%d ' % i) not in m06_tail
        for i in range(1, 12))
    m06_scope_limited = ('FAIL P12' in m06_tail
                         and 'No such file or directory' in m06_tail
                         and not m06_probe_failure)
    m06['scope_note'] = (
        'M06 P12 re-runs the M01/M02/M04 suites (and an engine asset) '
        'outside this package read scope; P1-P11 green is the claimed '
        'solver evidence here; a full-repository M06 run is not claimed')
    m06['p1_p11_green_in_scope'] = bool(
        m06_scope_limited or m06['exit_code'] == 0)
    m06['p12_scope_limited'] = bool(m06_scope_limited)
    gate_green = (by_name['G04']['exit_code'] == 0
                  and by_name['G05']['exit_code'] == 0
                  and m06['p1_p11_green_in_scope'])
    return {
        'schema': 'chimera.landing_regression.v1',
        'preregistration_sha256': lp.PREREG_SHA256,
        'declared_scope': 'M06 in-scope probes P1-P11 (P12 chain outside '
                          'package scope) + G04 + G05 gate suites',
        'suites': rows,
        'green': bool(gate_green),
    }


def main():
    pathlib.Path(OUT_DIR).mkdir(parents=True, exist_ok=True)
    try:
        trace, receipt, _scene, _census = battery_once(OUT_DIR)
    except lp.LandingRefusal as refusal:
        payload = {
            'schema': lp.SCHEMA, 'card': 'MAT2-SUPPORTED-LANDING',
            'preregistration_sha256': lp.PREREG_SHA256,
            'refusal': str(refusal), 'state': 'REFUSED_HARNESS',
        }
        lp.write_canonical(
            os.path.join(OUT_DIR, 'landing_experiment_receipt.json'),
            payload)
        print('REFUSED: %s' % refusal)
        return 4

    receipt_sha = lp.write_canonical(
        os.path.join(OUT_DIR, 'landing_experiment_receipt.json'), receipt)
    trace_sha = lp.write_canonical(
        os.path.join(OUT_DIR, 'landing_trace.json'), trace)

    # determinism pair: full second pass into a sibling directory
    out2 = os.path.normpath(os.path.join(OUT_DIR, '..', 'outputs_rerun2'))
    try:
        trace2, receipt2, _s2, _c2 = battery_once(out2)
    except lp.LandingRefusal as refusal:
        print('REFUSED (rerun2): %s' % refusal)
        return 4
    receipt2_sha = lp.write_canonical(
        os.path.join(OUT_DIR, 'landing_experiment_receipt_rerun2.json'),
        receipt2)
    trace2_sha = lp.write_canonical(
        os.path.join(OUT_DIR, 'landing_trace_rerun2.json'), trace2)
    determinism = {
        'schema': 'chimera.landing_determinism.v1',
        'preregistration_sha256': lp.PREREG_SHA256,
        'trace_byte_identical': trace_sha == trace2_sha,
        'receipt_byte_identical': receipt_sha == receipt2_sha,
        'augmentation_keys': [],
        'trace_sha256': trace_sha,
        'receipt_sha256': receipt_sha,
        'trace_rerun2_sha256': trace2_sha,
        'receipt_rerun2_sha256': receipt2_sha,
    }
    lp.write_canonical(os.path.join(OUT_DIR, 'determinism_receipt.json'),
                       determinism)

    regression = run_regression()
    lp.write_canonical(os.path.join(OUT_DIR, 'regression_receipt.json'),
                       regression)
    checks_row = run_named_checks(receipt, trace, regression)
    lp.write_canonical(os.path.join(OUT_DIR, 'named_checks_receipt.json'),
                       checks_row)

    capture_verdict = receipt.get('capture_verdict')
    capture_ok = capture_verdict == 'PASS'
    absence_ok = (receipt.get('retracted_quote_absence', {}).get('status')
                  == 'ABSENT_OK')
    det_ok = (determinism['trace_byte_identical']
              and determinism['receipt_byte_identical'])
    falsified = str(receipt['overall_verdict']).startswith(
        'PREDICTION_FALSIFIED_PRESERVED')
    sealed_refused = receipt.get('sealed_law_refusal') is not None
    print('overall_verdict: %s' % receipt['overall_verdict'])
    print('capture: %s determinism: %s checks: %s regression: %s '
          'retracted_absence: %s'
          % (capture_verdict, 'IDENTICAL' if det_ok else 'DRIFT',
             checks_row['green'], regression['green'], absence_ok))
    for key, row in receipt['verdicts'].items():
        print('%s -> %s' % (key, row['verdict']))
    if falsified or sealed_refused:
        return 3
    return 0 if (det_ok and checks_row['green'] and regression['green']
                 and capture_ok and absence_ok) else 3


if __name__ == '__main__':
    sys.exit(main())
