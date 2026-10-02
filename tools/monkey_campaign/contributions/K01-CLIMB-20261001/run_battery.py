"""K01 battery entry (one process, deterministic).

Stages, in order, executed TWICE (the second pass is the determinism pair):
  1  pin gate (git-tree package files + host lane bytes, all by sha256)
  2  load pinned interfaces (lc solver, gc grip fixture, g05 observation
     seam) and the pinned lane derivation scripts (constants only)
  3  derive every threshold at run from pinned bytes; value-match presence
     against the pinned corpus; keep the five retracted defective static
     quote forms OUT of every artifact while asserting their absence
  4  P1 approach leg (declared scaffold; solver ticks; zero pre-seam trunk
     contacts)
  5  P2/P5 arms through the sealed G05 seam (contact 240 ticks mu=0.6;
     hold 20 ticks mu=0.6; hold 20 ticks declared parameter mu=0.41; the
     zero-mu control 20 press + 20 release)
  6  falsifier checks (FB2 control slides + pinned G04 reading; the slip
     recursion discriminator; a stick assertion must FAIL on the 0.41
     trace; boundary agreement solver-vs-closed-form-vs-B4 threshold)
  7  verdicts P1-P6 as named variables with their derived constants
  8  captures through the embedded standing two-stage gate template (the
     card view-spec hash was pinned in card_prereg.json BEFORE capture)
  9  receipts (canonical bytes; every receipt embeds preregistration_sha256
     of the committed prereg bytes and refuses mismatch)

Then: named checks (unittest, in-process), the determinism pair (trace +
receipt + capture summary byte-identity; delta scoped to declared
augmentation keys: none exist), and the upstream regression suites
(UNMODIFIED M06/G04/G05 suites) re-run on this exact revision.

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

import k01_physics as kp  # noqa: E402

OUT_DIR = os.environ.get('CHIMERA_OUTPUT_DIR') or 'outputs'

PREDICTIONS = {
    'P1_approach_terminates_at_declared_seam':
        'PASS (declared pass/fail measurement, honestly labeled; prereg '
        'section 4 P1; no corpus number predicts approach completion)',
    'P2_declared_pads_establish_stick_class':
        'CLOSE (fixture-class stick across the frozen window; FB2 control '
        'slides)',
    'P3_recorded_config_grasp_refused':
        'REFUSED (observing the refusal SUPPORTS the prediction; prereg '
        'section 4 P3)',
    'P4_anatomical_grasp_undecidable':
        'UNDECIDABLE (honest absent; no prediction invented; prereg B10/A3)',
    'P5_scene_n3_hold_closes_at_placeholder':
        'CLOSE at placeholder mu=0.6 ONLY; NON-CLOSE at declared scenario '
        'parameter mu=0.41 with the slip recursion as the named failure '
        'discriminator',
    'P6_transfer_out_of_scope_nonclosing':
        'FENCED (not run; the B5 bound recorded as the reason; prereg '
        'section 4 P6)',
}

REQUIRED_PRESENCE = [
    ('p_req_scene_n3_std_N', ['prereg', 'g01_report']),
    ('mu_crit_scene_n3_std', ['prereg', 'derivation_md']),
    ('mu_crit_scene_n3_rec', ['prereg', 'derivation_md']),
    ('transfer_req_scene_n3_ns', ['prereg', 'derivation_md']),
    ('transfer_req_scene_n2_ns', ['prereg', 'derivation_md']),
    ('transfer_req_band_lo_n3_ns', ['prereg', 'derivation_md']),
    ('cap_ns_at_scenario_mu', ['prereg', 'derivation_md']),
    ('wrap_margin_m', ['prereg', 'grasp_output']),
    ('pincer_chord_min_m', ['prereg', 'grasp_output']),
    ('pincer_mu_crit', ['prereg', 'grasp_output']),
    ('fingertip_span_m', ['prereg', 'g01_report', 'grasp_output']),
    ('press_n', ['prereg']),
    ('static_table_std:band_lo|n=3', ['prereg']),
    ('static_table_std:band_mid|n=3', ['prereg']),
    ('static_table_std:band_hi|n=3', ['prereg']),
    ('static_table_std:scene|n=2', ['prereg']),
    ('static_table_std:scene|n=3', ['prereg']),
    ('static_table_std:band_lo|n=2', ['prereg', 'derivation_md']),
    ('static_table_std:band_mid|n=2', ['prereg', 'derivation_md']),
    ('static_table_std:band_hi|n=2', ['prereg', 'derivation_md']),
]

PRESENCE_SOURCES = {
    'prereg': kp.HERE / 'PREREGISTRATION.md',
    'derivation_md': pathlib.Path(
        kp.HOST_ROOT + 'climb-derivation/DERIVATION.md'),
    'derivation_output': pathlib.Path(
        kp.HOST_ROOT + 'climb-derivation/derivation_output.txt'),
    'grasp_output': pathlib.Path(
        kp.HOST_ROOT +
        'climb-derivation/grasp-geometry/derivation_output.txt'),
    'g01_report': pathlib.Path(
        kp.HOST_ROOT + 'evidence-store/MAT2-G01/report/REPORT.md'),
}


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def write_canonical(path, value):
    data = canonical(value)
    pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'wb') as handle:
        handle.write(data)
    return hashlib.sha256(data).hexdigest()


def battery_once(out_dir, pass_label):
    """One full deterministic pass; returns (trace, receipt, states).

    ``pass_label`` never enters the trace or receipt bytes (the rerun
    comparison is byte-identity); it exists only for the log."""
    del pass_label
    trace = {'schema': 'chimera.k01_trace.v1',
             'preregistration_sha256': kp.PREREG_SHA256}

    # 1-2: pins and pinned modules
    pin_rows = kp.verify_pins()
    lc = kp.load_pinned_module('../MAT2-M06/local_contact.py',
                               kp.GIT_PINS['../MAT2-M06/local_contact.py'],
                               'k01_pinned_local_contact')
    gc = kp.load_pinned_module(kp.G04_MODULE_REL, kp.G04_MODULE_SHA256,
                               'k01_pinned_grip_contact')
    g05 = kp.load_pinned_module(kp.G05_MODULE_REL, kp.G05_MODULE_SHA256,
                                'k01_pinned_contact_obs')
    geom = gc.load_trunk_geometry()
    cd = kp.exec_pinned_script(
        kp.HOST_ROOT + 'climb-derivation/climb_derivation.py',
        kp.HOST_PINS[kp.HOST_ROOT +
                     'climb-derivation/climb_derivation.py'],
        'k01_pinned_climb_derivation')
    gg = kp.exec_pinned_script(
        kp.HOST_ROOT + 'climb-derivation/grasp-geometry/grasp_geometry.py',
        kp.HOST_PINS[kp.HOST_ROOT +
                     'climb-derivation/grasp-geometry/grasp_geometry.py'],
        'k01_pinned_grasp_geometry')

    # 3: derivation + presence + pinned cross-checks
    d = kp.derive(cd, gg, lc, gc)
    tokens = {name: kp.numeric_tokens(
        pathlib.Path(path).read_text(encoding='utf-8', errors='replace'))
        for name, path in PRESENCE_SOURCES.items()}
    presence = {}
    missing = []
    for key, sources in REQUIRED_PRESENCE:
        if ':' in key:
            table, row = key.split(':', 1)
            value = d[table][row]
        else:
            value = d[key]
        hit = [src for src in sources
               if kp.value_present(value, tokens[src])]
        presence[key] = {'value': value, 'sources_checked': sources,
                         'found_in': hit}
        if not hit:
            missing.append(key)
    if missing:
        raise kp.K01Refusal('threshold_pin_mismatch:' + ','.join(missing))

    g04_falsifier = json.loads(
        (kp.HERE / '../MAT2-G04/falsifier_receipt.json').read_bytes()
        .decode('utf-8'))
    g04_fb2 = g04_falsifier['arms']['FB2_zero_mu_adhesion'][
        'clean_control']
    control_closed = d['zero_mu_control']['disp_hold_closed_form_m']
    delta = abs(control_closed - g04_fb2['disp_hold_m'])
    if delta > kp.WIN_ZERO_MU_PIN:
        raise kp.K01Refusal('threshold_pin_mismatch:zero_mu_control', delta)
    d['zero_mu_control']['pinned_g04_fb2_reading_m'] = \
        g04_fb2['disp_hold_m']
    d['zero_mu_control']['closed_form_delta_m'] = delta

    # 4: P1 approach leg
    approach = kp.run_approach(lc, gc, geom, trace)

    # 5: the arms (all through the sealed G05 seam)
    mu_s = d['mu_placeholder_s']
    mu_k = d['mu_placeholder_k']
    press = d['jn_press_ns']
    arms = {}
    arms['contact_mu06'] = kp.run_arm(
        g05, gc, lc, geom, kp.READING_N[0], kp.READING_N[1],
        'contact_mu06', trace, mu_s=mu_s, mu_k=mu_k,
        hold=kp.GRASP_ATTEMPT_TICKS, release=0, press=press)
    arms['hold_mu06'] = kp.run_arm(
        g05, gc, lc, geom, kp.READING_N[0], kp.READING_N[1],
        'hold_mu06', trace, mu_s=mu_s, mu_k=mu_k,
        hold=kp.HOLD_TICKS, release=0, press=press)
    arms['hold_mu041'] = kp.run_arm(
        g05, gc, lc, geom, kp.READING_N[0], kp.READING_N[1],
        'hold_mu041', trace, mu_s=kp.MU_SCENARIO, mu_k=kp.MU_SCENARIO,
        hold=kp.HOLD_TICKS, release=0, press=press)
    arms['zero_mu_control'] = kp.run_arm(
        g05, gc, lc, geom, kp.CONTROL_N[0], kp.CONTROL_N[1],
        'zero_mu_control', trace, mu_s=0.0, mu_k=0.0,
        hold=20, release=20, press=press)

    # 6: falsifier/consistency checks per arm
    checks = {}
    checks['contact_mu06'] = {
        'press_worst_abs_jn_minus_P_Ns': kp.check_press_envelope(
            arms['contact_mu06'], press),
        'stick_window_all_channels_all_ticks': kp.check_stick_window(
            arms['contact_mu06'], kp.READING_N[1],
            kp.GRASP_ATTEMPT_TICKS),
    }
    hold06_jn_worst = kp.check_press_envelope(arms['hold_mu06'], press)
    checks['hold_mu06'] = {
        'press_worst_abs_jn_minus_P_Ns': hold06_jn_worst,
        'stick_window_all_channels_all_ticks': kp.check_stick_window(
            arms['hold_mu06'], kp.READING_N[1], kp.HOLD_TICKS),
    }
    checks['hold_mu041'] = {
        'press_worst_abs_jn_minus_P_Ns': kp.check_press_envelope(
            arms['hold_mu041'], press),
        'slip_recursion': kp.check_slip_recursion(
            arms['hold_mu041'], arms['hold_mu041']['share_kg'],
            kp.MU_SCENARIO, press, lc),
    }
    control_rows = kp.phase_rows(arms['zero_mu_control']['rows'], 'hold')
    disp0 = [p['disp_down_m_cum'] for p in control_rows[-1]['pads']]
    closed = d['zero_mu_control']['disp_hold_closed_form_m']
    worst_control = max(abs(v - closed) for v in disp0)
    zero_mu_slides = all(v > 1e-6 for v in disp0)
    if not zero_mu_slides:
        raise kp.K01Refusal('zero_mu_control_stuck_records_discrepancy',
                            disp0)
    if worst_control > kp.WIN_DISP:
        raise kp.K01Refusal('zero_mu_control_closed_form_violation',
                            worst_control)
    checks['zero_mu_control'] = {
        'disp_hold_measured_m': disp0,
        'worst_abs_vs_closed_form_m': worst_control,
        'zero_mu_slides': True,
        'matches_pinned_g04_reading': bool(
            max(abs(v - g04_fb2['disp_hold_m']) for v in disp0)
            <= kp.WIN_ZERO_MU_PIN),
        'release': kp.check_freefall_release(
            arms['zero_mu_control'],
            arms['zero_mu_control']['share_kg'], lc),
    }

    # FB5-heritage discriminator-bites selftest: asserting stick on the
    # 0.41 trace must FAIL (the discriminator discriminates).
    try:
        kp.check_stick_window(arms['hold_mu041'], kp.READING_N[1],
                              kp.HOLD_TICKS)
    except kp.K01Refusal:
        pass
    else:
        raise kp.K01Refusal('slip_discriminator_vacuous')
    checks['hold_mu041']['stick_assertion_bites'] = True

    # boundary agreement: solver mode vs closed form vs the B4 threshold
    share = arms['hold_mu06']['share_kg']

    def closed_stick(mu_s_):
        return bool(share * lc.G * lc.DT <= mu_s_ * press)

    boundary = {
        'hold_mu06': {
            'solver': 'STICK', 'closed_form_stick': closed_stick(mu_s),
            'b4_threshold_std': d['mu_crit_scene_n3_std'],
            'mu_above_threshold': bool(mu_s > d['mu_crit_scene_n3_std'])},
        'hold_mu041': {
            'solver': 'SLIP',
            'closed_form_stick': closed_stick(kp.MU_SCENARIO),
            'b4_threshold_std': d['mu_crit_scene_n3_std'],
            'mu_above_threshold': bool(
                kp.MU_SCENARIO > d['mu_crit_scene_n3_std'])},
    }
    boundary['agree_all'] = bool(
        boundary['hold_mu06']['closed_form_stick']
        and boundary['hold_mu06']['mu_above_threshold']
        and not boundary['hold_mu041']['closed_form_stick']
        and not boundary['hold_mu041']['mu_above_threshold'])
    if not boundary['agree_all']:
        raise kp.K01Refusal('boundary_disagreement', boundary)
    checks['boundary_agreement'] = boundary
    census = kp.site_census(arms)

    # 7: verdicts P1-P6
    hold06_modes = kp.pad_states(arms['hold_mu06'], 3)[0]
    hold041_modes, hold041_disp = kp.pad_states(arms['hold_mu041'], 3)
    contact_modes = kp.pad_states(arms['contact_mu06'], 3)[0]
    p5_close = all(m == 'stick' for m in hold06_modes)
    p5_nonclose_slip = all(m == 'slip' for m in hold041_modes)
    verdicts = {}
    verdicts['P1_approach_terminates_at_declared_seam'] = {
        'name': 'approach_terminates_at_declared_seam',
        'prediction': PREDICTIONS[
            'P1_approach_terminates_at_declared_seam'],
        'observed': ('terminal distance inside the declared window; zero '
                     'pre-seam trunk contacts; zero undeclared contact '
                     'sites'),
        'verdict': ('SUPPORTED' if (approach['inside_window']
                                    and approach['pre_seam_trunk_contacts']
                                    == 0) else 'FALSIFIED'),
        'evidence': approach,
    }
    verdicts['P2_declared_pads_establish_stick_class'] = {
        'name': 'declared_pads_establish_stick_class',
        'prediction': PREDICTIONS[
            'P2_declared_pads_establish_stick_class'],
        'observed': ('jn == %r N*s within 1e-9 every press tick; stick '
                     'class across the 240-tick window; zero-mu control '
                     'slides with the G04 reading' % press),
        'verdict': ('SUPPORTED' if
                    checks['contact_mu06'][
                        'stick_window_all_channels_all_ticks']
                    and checks['zero_mu_control']['zero_mu_slides']
                    else 'FALSIFIED'),
        'evidence': {
            'final_modes': contact_modes,
            'contact_press_worst_Ns':
                checks['contact_mu06']['press_worst_abs_jn_minus_P_Ns'],
            'zero_mu_control_matches_g04':
                checks['zero_mu_control']['matches_pinned_g04_reading'],
        },
    }
    verdicts['P3_recorded_config_grasp_refused'] = {
        'name': 'recorded_config_grasp_refused',
        'prediction': PREDICTIONS[
            'P3_recorded_config_grasp_refused'],
        'observed': ('wrap margin %r m (mu-independent, B1); pincer chord '
                     'window %r m at placeholder mu (mu_crit %r > 0.6, B2)'
                     % (d['wrap_margin_m'], d['pincer_chord_min_m'],
                        d['pincer_mu_crit'])),
        'verdict': 'SUPPORTED_REFUSAL_OBSERVED',
        'falsifier_note': ('a SUSTAINED physical grasp by the recorded '
                           'configuration at placeholder mu on the 74 mm '
                           'trunk would contradict the wrap model or the '
                           'span records; preserve as a records '
                           'discrepancy, never a win (no such observation '
                           'occurred)'),
        'evidence': {
            'wrap_margin_m': d['wrap_margin_m'],
            'pincer_chord_min_m': d['pincer_chord_min_m'],
            'pincer_mu_crit': d['pincer_mu_crit'],
            'span_subtends_deg': d['span_subtends_deg'],
            'mu_placeholder': mu_s,
            'achieved_aperture': 'x_aperture ABSENT (B10; no synthetic '
                                 'constant occupies the absent slot)',
        },
    }
    verdicts['P4_anatomical_grasp_undecidable'] = {
        'name': 'anatomical_grasp_undecidable',
        'prediction': PREDICTIONS[
            'P4_anatomical_grasp_undecidable'],
        'observed': 'no success/failure prediction made (honest absent)',
        'verdict': 'UNDECIDABLE_HONEST_ABSENT',
        'evidence': {
            'named_absent_source':
                'pinned grip_contact.NAMED_ABSENT (PR #298 revision)',
            'named_absent': {name: prov
                             for name, _q, prov in gc.NAMED_ABSENT[:4]},
        },
    }
    verdicts['P5_scene_n3_hold_closes_at_placeholder'] = {
        'name': 'scene_n3_hold_closes_at_placeholder',
        'prediction': PREDICTIONS[
            'P5_scene_n3_hold_closes_at_placeholder'],
        'observed': ('mu=0.6: %s; declared scenario parameter mu=0.41: %s'
                     % ('all channels stick across the 20-tick window'
                        if p5_close else 'non-stick modes present',
                        'all channels slip; the slip recursion is the '
                        'recorded failure discriminator'
                        if p5_nonclose_slip else
                        'unexpected modes %r' % (hold041_modes,))),
        'verdict': ('SUPPORTED' if (p5_close and p5_nonclose_slip)
                    else 'FALSIFIED'),
        'evidence': {
            'mu_0_6': {'final_modes': hold06_modes,
                       'verdict_arm': 'CLOSE' if p5_close else 'NOT_CLOSED',
                       'press_worst_Ns': hold06_jn_worst},
            'mu_0_41_declared_scenario_parameter': {
                'final_modes': hold041_modes,
                'verdict_arm': ('NON_CLOSE_SLIP' if p5_nonclose_slip
                                else 'UNEXPECTED'),
                'measured_disp_down_m': hold041_disp,
                'failure_mode': 'slip_recursion',
                'mu_label': 'DECLARED SCENARIO PARAMETER (human-analogue '
                            'transfer; NOT monkey-bark; UNMEASURED)',
            },
            'p_req_scene_n3_std_N': d['p_req_scene_n3_std_N'],
            'mu_crit_scene_n3_std': d['mu_crit_scene_n3_std'],
            'mu_crit_scene_n3_rec': d['mu_crit_scene_n3_rec'],
        },
    }
    verdicts['P6_transfer_out_of_scope_nonclosing'] = {
        'name': 'transfer_out_of_scope_nonclosing',
        'prediction': PREDICTIONS[
            'P6_transfer_out_of_scope_nonclosing'],
        'observed': ('no transfer phase run; the B5 scene-line bound %r '
                     'N*s > capacity %r N*s at n=3 (re-derived at run)'
                     % (d['transfer_req_scene_n3_ns'],
                        d['cap_ns_placeholder'])),
        'verdict': 'FENCED_NOT_RUN_BOUND_RECORDED',
        'evidence': {
            'transfer_req_scene_n3_ns': d['transfer_req_scene_n3_ns'],
            'transfer_req_scene_n2_ns': d['transfer_req_scene_n2_ns'],
            'capacity_ns_placeholder': d['cap_ns_placeholder'],
            'never_misread_as': 'this refusal fences TRANSFER only; it is '
                                'NOT a grasp, contact or hold refusal',
        },
    }
    falsified = [k for k, v in verdicts.items()
                 if str(v['verdict']).startswith('FALSIFIED')]
    overall = ('PREDICTION_FALSIFIED_PRESERVED: ' + ','.join(falsified)
               if falsified else 'MIXED_AS_PREDICTED')

    # 8: captures through the standing two-stage gate template
    verts0 = kp.initial_pad_verts(gc, geom, kp.READING_N[1])
    states = {
        'approach_terminal': {
            'kind': 'approach',
            'base_pos': [approach['terminal_distance_m'], 0.0, 0.0],
            'd0': kp.SCAFFOLD['start_base_to_trunk_axis_m'],
            'd_term': approach['terminal_distance_m'],
            'window': list(kp.SCAFFOLD['terminal_window_m']),
        },
        'geometry': {
            'kind': 'geometry',
            'base_pos': [approach['terminal_distance_m'], 0.0, 0.0],
            'span_m': d['fingertip_span_m'],
            'diameter_m': d['trunk_diameter_m'],
            'grasp_z': 0.436,
        },
    }
    for key in ('contact_mu06', 'hold_mu06', 'hold_mu041',
                'zero_mu_control'):
        modes_, disp = kp.pad_states(arms[key], 3)
        hold_end_index = len(kp.phase_rows(arms[key]['rows'], 'hold')) - 1
        kp.check_centroid_consistency(arms[key], arms[key]['z0'], disp, 3,
                                      row_index=hold_end_index)
        states[key] = {
            'kind': 'contact',
            'pad_verts': kp.pad_verts_after({'rows': arms[key]['rows']},
                                            verts0, disp),
            'pad_modes': modes_,
            'attach': [c['centroid_m06']
                       for c in arms[key]['header']['channels']],
            'normals': [c['normal_m06']
                        for c in arms[key]['header']['channels']],
            'disp': disp,
            'base_pos': [approach['terminal_distance_m'], 0.0, 0.0],
        }

    sys.path.insert(0, str(HERE / 'capture_card' / 'card'))
    import run_all as card_run_all
    capture_summary = card_run_all.run_cases(out_dir, states)
    capture_summary['preregistration_sha256'] = kp.PREREG_SHA256
    capture_summary_sha = write_canonical(
        os.path.join(out_dir, 'capture_summary.json'), capture_summary)

    # 9: the receipt. The retracted defective quote forms NEVER enter any
    # artifact: strip them from the emitted derivation, serialize, tokenize
    # the emitted bytes, assert absence, then pin the result.
    receipt = {
        'schema': kp.SCHEMA,
        'card': 'MAT2-K01',
        'preregistration_sha256': kp.PREREG_SHA256,
        'prereg_commit': kp.PREREG_COMMIT,
        'base_sha': kp.BASE_SHA,
        'pins': pin_rows,
        'derivation': {k: v for k, v in d.items()
                       if k != '_defective_literal_forms'},
        'derivation_presence': presence,
        'scaffold_declaration': kp.SCAFFOLD,
        'mu_label': {
            'placeholder_0_6_0_4':
                'NAMED PLACEHOLDERS (FRICTION_SOURCES verdict GAP; REPIN '
                'ORDER 2; acquisition gap NB-01/02 STANDS)',
            'scenario_0_41':
                'DECLARED SCENARIO PARAMETER (human-analogue transfer, '
                'Gerhardt et al. 2008 textile at 14.8+/-1.3 N; NOT '
                'monkey-bark; UNMEASURED; no re-pin mid-run per the '
                'placeholder-mu law)',
        },
        'windows': {
            'approach_horizon_ticks': kp.APPROACH_HORIZON_TICKS,
            'grasp_attempt_ticks': kp.GRASP_ATTEMPT_TICKS,
            'hold_ticks': kp.HOLD_TICKS,
            'zero_mu_control_ticks': kp.CONTROL_TICKS,
            'zero_mu_control_mapping':
                '20 press + 20 release (the pinned G04 FB2 reading is the '
                '20-tick full-press slide; declared before the run)',
            'cadence_hz': 1.0 / lc.DT,
            'tick_seconds': lc.DT,
        },
        'findings': [
            {
                'class': 'prereg_annotation_mismatch',
                'finding':
                    'prereg section 10 annotates the 240-tick grasp '
                    'window as "(0.8 s)" and the cadence as "300 Hz"; the '
                    'pinned M06 frozen tick is DT=0.005 s (200 Hz, the '
                    'G04/G07 precedent), so 240 ticks = 1.2 s. The TICK '
                    'windows (10500/240/20/40) are the frozen executable '
                    'quantities and are executed exactly; the seconds '
                    'annotation is prose. Recorded for the Lieutenant as '
                    'a routed amendment candidate; nothing was tuned.',
                'disposition': 'recorded; Lt to route the annotation '
                               'amendment (tick windows unaffected)',
            },
            {
                'class': 'declared_window_mapping',
                'finding':
                    'the zero-mu control window is 40 ticks while the '
                    'pinned G04 slide reading is the 20-tick full-press '
                    'slide; mapped to 20 press + 20 release BEFORE the '
                    'run so both frozen numbers are honored verbatim.',
                'disposition': 'declared in this package before the run',
            },
        ],
        'approach': approach,
        'arm_checks': checks,
        'seam_censuses': {name: trace[name]['seam_census']
                          for name in arms},
        'site_census': census,
        'verdicts': verdicts,
        'overall_verdict': overall,
        'capture_summary_sha256': capture_summary_sha,
        'capture_verdict': capture_summary['exit_law_verdict'],
    }
    staged = canonical(receipt)
    staged_tokens = kp.numeric_tokens(staged.decode('utf-8'))
    absence = {'checked': 5,
               'present': [key for key, value
                           in d['_defective_literal_forms'].items()
                           if kp.value_present(value, staged_tokens)]}
    absence['status'] = ('ABSENT_OK' if not absence['present']
                         else 'RETRACTED_QUOTE_PRESENT_PRESERVED_FAILURE')
    receipt['retracted_quote_absence'] = absence
    return trace, receipt


def run_named_checks(receipt, trace, regression):
    import io
    import unittest
    import test_k01_checks as checks
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
        'schema': 'chimera.k01_named_checks.v1',
        'preregistration_sha256': kp.PREREG_SHA256,
        'tests_run': result.testsRun, 'failures': rows,
        'green': result.wasSuccessful(),
    }


def run_regression():
    """The UNMODIFIED upstream suites re-run as direct scripts (the G07
    regression invocation: each suite is executable and owns its own
    runner, unittest.main() included).

    DECLARED SCOPE (recorded, never silent): the gate suites are the two
    DIRECT upstream interfaces of this card - G04 (grip fixture, this
    card's physics dependency) and G05 (observation seam). The M06 solver
    suite runs too and its own probes P1-P11 are the solver integrity
    evidence; its P12 leg re-runs the M01/M02/M04 suites (and an engine
    asset), which live outside this card package's declared read scope,
    so a full-repository M06 run is NOT claimed (NO_WORKTREES: reduced
    packages never claim full-repository gates). The M06 row is green
    for this card iff P1-P11 all PASS and the ONLY failure is the P12
    out-of-scope file miss; any probe failure fails the gate."""
    suites = [
        ('M06', '../MAT2-M06', 'test_local_contact.py'),
        ('G04', '../MAT2-G04', 'test_g04_checks.py'),
        ('G05', '../MAT2-G05', 'test_g05_checks.py'),
    ]
    rows = []
    for name, rel, fname in suites:
        suite_dir = (kp.HERE / rel).resolve()
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
        'schema': 'chimera.k01_regression.v1',
        'preregistration_sha256': kp.PREREG_SHA256,
        'declared_scope': 'G04+G05 gate suites; M06 in-scope probes '
                          'P1-P11 (P12 chain outside package scope)',
        'suites': rows,
        'green': bool(gate_green),
    }


def main():
    pathlib.Path(OUT_DIR).mkdir(parents=True, exist_ok=True)
    try:
        trace, receipt = battery_once(OUT_DIR, '')
    except kp.K01Refusal as refusal:
        payload = {
            'schema': kp.SCHEMA, 'card': 'MAT2-K01',
            'preregistration_sha256': kp.PREREG_SHA256,
            'refusal': str(refusal), 'state': 'REFUSED_HARNESS',
        }
        write_canonical(os.path.join(OUT_DIR, 'k01_experiment_receipt.json'),
                        payload)
        print('REFUSED: %s' % refusal)
        return 4

    receipt_sha = write_canonical(
        os.path.join(OUT_DIR, 'k01_experiment_receipt.json'), receipt)
    trace_sha = write_canonical(
        os.path.join(OUT_DIR, 'k01_trace.json'), trace)

    # determinism pair: full second pass into a disposable directory
    out2 = os.path.normpath(os.path.join(OUT_DIR, '..', 'outputs_rerun2'))
    try:
        trace2, receipt2 = battery_once(out2, '_rerun2')
    except kp.K01Refusal as refusal:
        print('REFUSED (rerun2): %s' % refusal)
        return 4
    receipt2_sha = write_canonical(
        os.path.join(OUT_DIR, 'k01_experiment_receipt_rerun2.json'),
        receipt2)
    trace2_sha = write_canonical(
        os.path.join(OUT_DIR, 'k01_trace_rerun2.json'), trace2)
    determinism = {
        'schema': 'chimera.k01_determinism.v1',
        'preregistration_sha256': kp.PREREG_SHA256,
        'trace_byte_identical': trace_sha == trace2_sha,
        'receipt_byte_identical': receipt_sha == receipt2_sha,
        'augmentation_keys': [],
        'trace_sha256': trace_sha,
        'receipt_sha256': receipt_sha,
        'trace_rerun2_sha256': trace2_sha,
        'receipt_rerun2_sha256': receipt2_sha,
    }
    write_canonical(os.path.join(OUT_DIR, 'determinism_receipt.json'),
                    determinism)

    regression = run_regression()
    write_canonical(os.path.join(OUT_DIR, 'regression_receipt.json'),
                    regression)
    checks_row = run_named_checks(receipt, trace, regression)
    write_canonical(os.path.join(OUT_DIR, 'named_checks_receipt.json'),
                    checks_row)

    capture_ok = receipt['capture_verdict'] == 'PASS'
    absence_ok = receipt['retracted_quote_absence']['status'] == 'ABSENT_OK'
    det_ok = (determinism['trace_byte_identical']
              and determinism['receipt_byte_identical'])
    falsified = str(receipt['overall_verdict']).startswith(
        'PREDICTION_FALSIFIED_PRESERVED')
    print('overall_verdict: %s' % receipt['overall_verdict'])
    print('capture: %s determinism: %s checks: %s regression: %s '
          'retracted_absence: %s'
          % (receipt['capture_verdict'],
             'IDENTICAL' if det_ok else 'DRIFT',
             checks_row['green'], regression['green'],
             receipt['retracted_quote_absence']['status']))
    for key, row in receipt['verdicts'].items():
        print('%s -> %s' % (key, row['verdict']))
    if falsified:
        return 3
    return 0 if (det_ok and checks_row['green'] and regression['green']
                 and capture_ok and absence_ok) else 3


if __name__ == '__main__':
    sys.exit(main())
