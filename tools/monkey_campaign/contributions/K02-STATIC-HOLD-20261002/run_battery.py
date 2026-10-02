"""K02 battery entry (one process, deterministic).

Stages, in order, executed TWICE (the second pass is the determinism pair):
  1  pin gate (git-tree package files + host lane bytes + the embedded
     capture template manifest, all by sha256); CHIMERA_BASE_SHA asserted
     == the committed prereg commit (the merged-tip basis)
  2  load pinned interfaces (lc solver, gc grip fixture, g05 observation
     seam, the G07 sealed account observer) and the pinned lane derivation
     scripts (constants only)
  3  derive every threshold at run from pinned bytes; value-match presence
     against the pinned corpus; read the pinned G07 scene|n=3 ledger and
     the K01 sealed 0.41-arm authority JSON-exact; keep the five retracted
     defective static quote forms OUT of every artifact while asserting
     their absence
  4  P1 hold windows W20/W100/W300 at placeholder mu (stick per tick,
     press bar, creep recorded, energy ledger, rate band; a contact break
     is a RECORDED falsifier, never tuned and never a harness refusal)
  5  P4 release-to-ground from the held state (20 hold + 40 release, the
     G07 structure; ground contacts recorded, never support)
  6  P5 the declared parameter mu=0.41 arm (20 ticks, K01 comparability;
     predicted NON-CLOSE via the slip recursion)
  7  P2 load path re-derivation + boundary agreement; P6 fence recorded
  8  verdicts P1-P6 as named variables with their derived constants
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

import k02_physics as kp  # noqa: E402

OUT_DIR = os.environ.get('CHIMERA_OUTPUT_DIR') or 'outputs'

PREDICTIONS = {
    'P1_hold_persists_all_declared_windows_placeholder':
        'PASS (stick class every channel every tick of W20/W100/W300 at '
        'placeholder mu; zero slip ticks predicted; creep recorded; a '
        'creep-driven contact break is the declared P1 falsifier - a '
        'recorded persistence boundary, never tuned)',
    'P2_load_path_within_declared_ceiling':
        'CLOSE (P_req <= 60 N declared press with the margin re-derived at '
        'run; thresholds inside the F-A band; boundary agreement)',
    'P3_hold_energy_ledger_closes':
        'CLOSE (identity within 1e-9 J in every window; W20 reproduces the '
        'pinned G07 ledger within 1e-9 J; W100/W300 press rate inside the '
        'declared 1% band of the measured W20 rate)',
    'P4_release_free_fall_identity':
        'PASS (W_press == 0.0 J exactly every release tick; free-fall '
        'identity; ground contacts recorded, never support; NO impact '
        'model exists or is claimed)',
    'P5_mu041_hold_nonclose_slip_recursion':
        'NON-CLOSE at the declared scenario parameter mu=0.41 (OBSERVING '
        'THE SLIP SUPPORTS the prediction; the slip recursion is the named '
        'failure discriminator; the falsifier is a sustained hold at 0.41)',
    'P6_transfer_and_n4_fenced_not_run':
        'FENCED (no transfer phase and no n=4 shape run; the B5 bound '
        'recorded as the reason; prereg section 4 P6)',
}

REQUIRED_PRESENCE = [
    ('p_req_scene_n3_std_N', ['prereg', 'g01_report']),
    ('p_req_scene_n3_rec_N', ['prereg']),
    ('hold_margin_std_N', ['prereg']),
    ('mu_crit_scene_n3_std', ['prereg', 'derivation_md']),
    ('mu_crit_scene_n3_rec', ['prereg', 'derivation_md']),
    ('press_n', ['prereg']),
    ('jn_press_ns', ['prereg']),
    ('friction_limit_rec_N', ['prereg']),
    ('friction_limit_std_N', ['prereg']),
    ('weight_N_std', ['runtime_contract']),
    ('weight_share_std_N', ['prereg']),
    ('transfer_req_scene_n3_ns', ['prereg', 'derivation_md']),
    ('transfer_req_scene_n2_ns', ['prereg', 'derivation_md']),
    ('transfer_req_band_lo_n3_ns', ['prereg', 'derivation_md']),
    ('cap_ns_placeholder', ['prereg', 'derivation_md']),
    ('cap_ns_at_scenario_mu', ['prereg', 'derivation_md']),
    ('g07_reference:w20_press_J', ['prereg', 'g07_receipt', 'g07_report']),
    ('g07_reference:w20_gravity_J',
     ['prereg', 'g07_receipt', 'g07_report']),
    ('g07_reference:w20_friction_J', ['prereg', 'g07_receipt']),
    ('g07_reference:release_gravity_J', ['prereg', 'g07_receipt']),
    ('g07_reference:release_ke_J', ['prereg', 'g07_receipt']),
    ('g07_reference:terminal_mps_derived', ['prereg', 'derivation_md']),
    ('k01_authority:slip_dv_per_tick_mps', ['prereg', 'k01_receipt']),
    ('k01_authority:slip_worst_v_residual_mps', ['k01_receipt']),
    ('k01_authority:slip_worst_disp_residual_m', ['k01_receipt']),
    ('k01_authority:slip_measured_disp_down_m', ['prereg', 'k01_receipt']),
    ('k01_authority:zero_mu_disp_hold_measured_m', ['prereg',
                                                    'k01_receipt']),
    ('mu041_derived:dv_per_tick_mps', ['prereg', 'k01_receipt']),
]

PRESENCE_SOURCES = {
    'prereg': kp.HERE / 'PREREGISTRATION.md',
    'derivation_md': pathlib.Path(
        kp.HOST_ROOT + 'climb-derivation/DERIVATION.md'),
    'derivation_output': pathlib.Path(
        kp.HOST_ROOT + 'climb-derivation/derivation_output.txt'),
    'g01_report': pathlib.Path(
        kp.HOST_ROOT + 'evidence-store/MAT2-G01/report/REPORT.md'),
    'g07_receipt': pathlib.Path(
        kp.HOST_ROOT +
        'evidence-store/MAT2-G07/numerical/experiment_receipt.json'),
    'g07_report': pathlib.Path(
        kp.HOST_ROOT + 'evidence-store/MAT2-G07/report/REPORT.md'),
    'runtime_contract': pathlib.Path(
        kp.HOST_ROOT + 'b07-prereqs/RUNTIME_CONTRACT.md'),
    'k01_receipt': pathlib.Path(kp.K01_RECEIPT_REL),
}

WIN_PRESENCE_REL = 1e-6   # declared relative window for tolerance-token
#                          scans (float-path-differing references only)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def write_canonical(path, value):
    data = canonical(value)
    pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'wb') as handle:
        handle.write(data)
    return hashlib.sha256(data).hexdigest()


def presence_value(d, key):
    if ':' in key:
        table, row = key.split(':', 1)
        return d[table][row]
    return d[key]


def token_scan(value, tokens, rel=WIN_PRESENCE_REL):
    """Pinned tokens within a declared relative window of ``value``
    (for float-path-differing references: the pinned bytes own the
    reference value; the scan never substitutes it)."""
    hits = []
    for tok in tokens:
        if tok == value:
            return [tok]
        scale = max(abs(value), 1e-300)
        if abs(tok - value) <= rel * scale:
            hits.append(tok)
    return hits


def battery_once(out_dir, pass_label):
    """One full deterministic pass; returns (trace, receipt).

    ``pass_label`` never enters the trace or receipt bytes (the rerun
    comparison is byte-identity); it exists only for the log."""
    del pass_label
    trace = {'schema': kp.TRACE_SCHEMA,
             'preregistration_sha256': kp.PREREG_SHA256}

    # 1-2: pins, template integrity, pinned modules
    pin_rows = kp.verify_pins()
    template_rows = kp.verify_template_manifest()
    lc = kp.load_pinned_module('../MAT2-M06/local_contact.py',
                               kp.GIT_PINS['../MAT2-M06/local_contact.py'],
                               'k02_pinned_local_contact')
    gc = kp.load_pinned_module(kp.G04_MODULE_REL, kp.G04_MODULE_SHA256,
                               'k02_pinned_grip_contact')
    g05 = kp.load_pinned_module(kp.G05_MODULE_REL, kp.G05_MODULE_SHA256,
                                'k02_pinned_contact_obs')
    rfa = kp.load_pinned_host_module(
        kp.HOST_ROOT + 'evidence-store/MAT2-G07/source/'
        'release_fall_account.py',
        kp.HOST_PINS[kp.HOST_ROOT +
                     'evidence-store/MAT2-G07/source/'
                     'release_fall_account.py'],
        'k02_pinned_g07_account')
    geom = gc.load_trunk_geometry()
    cd = kp.exec_pinned_script(
        kp.HOST_ROOT + 'climb-derivation/climb_derivation.py',
        kp.HOST_PINS[kp.HOST_ROOT +
                     'climb-derivation/climb_derivation.py'],
        'k02_pinned_climb_derivation')
    gg = kp.exec_pinned_script(
        kp.HOST_ROOT + 'climb-derivation/grasp-geometry/grasp_geometry.py',
        kp.HOST_PINS[kp.HOST_ROOT +
                     'climb-derivation/grasp-geometry/grasp_geometry.py'],
        'k02_pinned_grasp_geometry')

    # 3: derivation + presence + pinned cross-checks
    g07_receipt = kp.load_pinned_json(
        kp.HOST_ROOT +
        'evidence-store/MAT2-G07/numerical/experiment_receipt.json',
        kp.HOST_PINS[kp.HOST_ROOT +
                     'evidence-store/MAT2-G07/numerical/'
                     'experiment_receipt.json'])
    k01_receipt = kp.load_pinned_json(kp.K01_RECEIPT_REL,
                                      kp.HOST_PINS[kp.K01_RECEIPT_REL])
    massreg = kp.load_pinned_json(
        kp.HOST_ROOT +
        'evidence-store/MAT2-D-MASSREG/numerical/mass_register.json',
        kp.HOST_PINS[kp.HOST_ROOT +
                     'evidence-store/MAT2-D-MASSREG/numerical/'
                     'mass_register.json'])
    g07_ledger = kp.g07_scene_n3_ledger(g07_receipt)
    k01_auth = kp.k01_authority(k01_receipt)
    d = kp.derive(cd, gg, lc, gc, g07_ledger, k01_auth, massreg)
    tokens = {name: kp.numeric_tokens(
        pathlib.Path(path).read_text(encoding='utf-8', errors='replace'))
        for name, path in PRESENCE_SOURCES.items()}
    presence = {}
    missing = []
    for key, sources in REQUIRED_PRESENCE:
        value = presence_value(d, key)
        if isinstance(value, list):
            hit = [src for src in sources
                   if all(kp.value_present(v, tokens[src])
                          for v in value)]
        else:
            hit = [src for src in sources
                   if kp.value_present(value, tokens[src])]
        presence[key] = {'sources_checked': sources, 'found_in': hit}
        if not hit:
            missing.append(key)
    if missing:
        raise kp.K02Refusal('threshold_pin_mismatch:' + ','.join(missing))
    presence['values'] = {key: presence_value(d, key)
                          for key, _ in REQUIRED_PRESENCE}

    # tolerance-scan references (pinned bytes own the reference value)
    scan = {}
    fall_hits = token_scan(d['g07_reference']['fall_closed_form_m'],
                           tokens['prereg'] + tokens['derivation_md']
                           + tokens['g07_report'])
    kp.require(fall_hits, 'g07_fall_reference_token_absent',
               d['g07_reference']['fall_closed_form_m'])
    scan['g07_fall_reference_m'] = max(fall_hits)
    scan['g07_fall_reference_hits'] = len(fall_hits)
    rate_hits = token_scan(d['g07_reference']['w20_press_rate_J_per_tick'],
                           tokens['prereg'] + tokens['derivation_md'])
    scan['g07_rate_reference_hits'] = len(rate_hits)
    scan['g07_rate_reference_note'] = (
        'the pinned 1%-band anchor token (DERIVATION float path) differs '
        'from the sealed-receipt float path by <1e-15 relative; the P3 rate '
        'gate is the declared 1% band against the MEASURED W20 rate, never '
        'the pinned token itself')

    # 4: P1 hold windows at placeholder mu
    mu_s = d['mu_placeholder_s']
    mu_k = d['mu_placeholder_k']
    press = d['jn_press_ns']
    arms = {}
    windows = {}
    for name, ticks in kp.DECLARED_WINDOWS:
        arms[name] = kp.run_window(rfa, g05, gc, lc, geom, name, trace,
                                   ticks, 0, mu_s, mu_k, press)
        rows = arms[name]['rows']
        stick = kp.stick_records(rows, ticks)
        press_worst = kp.press_envelope(rows, press, ticks)
        impulse = kp.window_press_impulse(rows, press, ticks)
        ledger = kp.window_ledger(arms[name]['acct_rows'], 'hold')
        creep = kp.final_disp(rows, 3)
        creep_per_tick = [c / ticks for c in creep]
        windows[name] = {
            'ticks': ticks,
            'seconds_annotation': ticks * lc.DT,
            'stick_census': stick,
            'press_worst_abs_jn_minus_P_Ns': press_worst,
            'press_inside_bar': bool(press_worst <= kp.WIN_JN),
            'press_impulse': impulse,
            'ledger': ledger,
            'identity_inside_gate_J': bool(
                ledger['identity_gravity_minus_friction_J']
                <= kp.WIN_ENERGY_IDENTITY),
            'creep_final_m': creep,
            'creep_per_tick_m': creep_per_tick,
        }
    # P3(b): the W20 reference window reproduces the pinned G07 ledger
    ref = d['g07_reference']
    w20 = windows['W20']['ledger']['sums']
    g07_ref_deltas = {
        'press_J': abs(w20['work_press_J'] - ref['w20_press_J']),
        'gravity_J': abs(w20['work_gravity_J'] - ref['w20_gravity_J']),
        'friction_J': abs(w20['loss_solver_J'] - ref['w20_friction_J']),
    }
    g07_ref_ok = all(v <= kp.WIN_G07_REFERENCE for v in g07_ref_deltas.values())
    # P3(c): the declared 1% rate band vs the MEASURED W20 rate
    rate_w20 = (windows['W20']['ledger']['sums']['work_press_J']
                / windows['W20']['ticks'])
    rate_rows = {}
    rate_ok = True
    for name in ('W100', 'W300'):
        rate = (windows[name]['ledger']['sums']['work_press_J']
                / windows[name]['ticks'])
        deviation = abs(rate - rate_w20)
        inside = bool(deviation <= kp.WIN_RATE_BAND * rate_w20)
        rate_ok = rate_ok and inside
        rate_rows[name] = {'rate_J_per_tick': rate,
                           'abs_dev_vs_w20_J_per_tick': deviation,
                           'inside_declared_1pct_band': inside}
    # P1 verdict inputs (falsifier path recorded, never a refusal)
    p1_fired_windows = [name for name, w in windows.items()
                        if not (w['stick_census']['stick_all']
                                and w['press_inside_bar'])]
    for name in p1_fired_windows:
        rows = arms[name]['rows']
        slip_present = any(
            pad['mode'] == 'slip'
            for row in kp.phase_rows(rows, 'hold')
            for pad in row['pads'])
        windows[name]['slip_discriminator_applicable'] = slip_present
        windows[name]['falsifier_class'] = (
            'creep_driven_contact_break_persistence_boundary' if
            any(windows[name]['stick_census']['no_contact_ticks'])
            else 'slip_inside_declared_window')

    # 5: P4 release-to-ground from the held state (G07 structure)
    arms['release_to_ground'] = kp.run_window(
        rfa, g05, gc, lc, geom, 'release_to_ground', trace,
        kp.RELEASE_HOLD_TICKS, kp.RELEASE_FALL_TICKS, mu_s, mu_k, press)
    release = kp.release_leg_checks(arms['release_to_ground']['acct_rows'],
                                    arms['release_to_ground']['rows'],
                                    arms['release_to_ground']['share_kg'],
                                    lc)
    release['fall_reference_m'] = scan['g07_fall_reference_m']
    release['fall_delta_vs_reference_m'] = abs(
        release['fall_measured_m'] - scan['g07_fall_reference_m'])
    release['fall_inside_window'] = bool(
        release['fall_delta_vs_reference_m'] <= kp.WIN_G07_FALL)
    release['terminal_inside_window'] = bool(
        release['terminal_delta_mps'] <= kp.WIN_RECURSION_V)
    release['ke_identity_inside_gate_J'] = bool(
        release['ke_identity_delta_J'] <= kp.WIN_ENERGY_IDENTITY)
    release['freefall_inside_window'] = bool(
        release['freefall_worst_v_residual_mps'] <= kp.WIN_RECURSION_V)
    release['g07_reference_release'] = {
        'gravity_J': ref['release_gravity_J'],
        'ke_J': ref['release_ke_J'],
        'ke_delta_vs_reference_J': abs(
            release['ke_gain_J'] - ref['release_ke_J']),
        'gravity_delta_vs_reference_J': abs(
            release['gravity_work_J'] - ref['release_gravity_J']),
    }
    # the G07 sealed release-account law (its own measurement function;
    # a refusal inside it is a PRESERVED falsifier candidate for the P4
    # verdict path, never a silent repair)
    try:
        rel_summary = rfa.release_account(
            arms['release_to_ground']['rows'],
            arms['release_to_ground']['acct_rows'], kp.READING_N[1],
            arms['release_to_ground']['share_kg'], lc.DT,
            hold_ticks=kp.RELEASE_HOLD_TICKS)
        release['g07_release_account'] = rel_summary
        release['g07_release_account_state'] = 'CLEAN'
    except ValueError as exc:
        release['g07_release_account'] = {'refusal': str(exc)}
        release['g07_release_account_state'] = \
            'REFUSED_PRESERVED_FALSIFIER_CANDIDATE'

    # 6: P5 the declared parameter arm (K01 comparability window)
    arms['hold_mu041'] = kp.run_window(
        rfa, g05, gc, lc, geom, 'hold_mu041', trace,
        kp.MU041_TICKS, 0, kp.MU_SCENARIO, kp.MU_SCENARIO, press)
    mu041_modes = kp.final_modes(arms['hold_mu041']['rows'], 3)
    mu041_all_slip = all(m == 'slip' for m in mu041_modes)
    mu041_all_stick = all(m == 'stick' for m in mu041_modes)
    mu041 = {'final_modes': mu041_modes,
             'press_worst_abs_jn_minus_P_Ns': kp.press_envelope(
                 arms['hold_mu041']['rows'], press, kp.MU041_TICKS)}
    if mu041_all_slip:
        rec = kp.check_slip_recursion(arms['hold_mu041']['rows'],
                                      arms['hold_mu041']['share_kg'],
                                      kp.MU_SCENARIO, press, lc)
        mu041['slip_recursion'] = rec
        mu041['measured_disp_down_m'] = kp.final_disp(
            arms['hold_mu041']['rows'], 3)
        k01_disp = k01_auth['slip_measured_disp_down_m']
        mu041['k01_class_disp_delta_m'] = [
            abs(a - b) for a, b in zip(mu041['measured_disp_down_m'],
                                       k01_disp)]
        mu041['k01_class_match'] = bool(
            max(mu041['k01_class_disp_delta_m']) <= kp.WIN_K01_CLASS)
    mu041['stick_assertion_bites'] = kp.check_stick_assertion_bites(
        arms['hold_mu041']['rows'], kp.MU041_TICKS)

    # 7: P2 boundary agreement on the declared comparison arms
    share = arms['W20']['share_kg']

    def closed_stick(mu_s_):
        return bool(share * lc.G * lc.DT <= mu_s_ * press)

    boundary = {
        'hold_w20': {
            'solver': 'STICK' if windows['W20']['stick_census']['stick_all']
            else 'BROKEN',
            'closed_form_stick': closed_stick(mu_s),
            'b4_threshold_std': d['mu_crit_scene_n3_std'],
            'mu_above_threshold': bool(mu_s > d['mu_crit_scene_n3_std'])},
        'hold_mu041': {
            'solver': 'SLIP' if mu041_all_slip
            else ('STICK' if mu041_all_stick else 'MIXED'),
            'closed_form_stick': closed_stick(kp.MU_SCENARIO),
            'b4_threshold_std': d['mu_crit_scene_n3_std'],
            'mu_above_threshold': bool(
                kp.MU_SCENARIO > d['mu_crit_scene_n3_std'])},
    }
    boundary['agree_all'] = bool(
        boundary['hold_w20']['closed_form_stick']
        and boundary['hold_w20']['mu_above_threshold']
        and not boundary['hold_mu041']['closed_form_stick']
        and not boundary['hold_mu041']['mu_above_threshold']
        and boundary['hold_w20']['solver'] == 'STICK'
        and boundary['hold_mu041']['solver'] == 'SLIP')
    checks_p2 = {
        'boundary_agreement': boundary,
        'load_path': {
            'p_req_scene_n3_std_N': d['p_req_scene_n3_std_N'],
            'p_req_scene_n3_rec_N': d['p_req_scene_n3_rec_N'],
            'hold_margin_std_N': d['hold_margin_std_N'],
            'mu_crit_scene_n3_std': d['mu_crit_scene_n3_std'],
            'mu_crit_scene_n3_rec': d['mu_crit_scene_n3_rec'],
            'mu_crit_inside_fa_band': d['mu_crit_inside_fa_band'],
            'friction_limit_rec_N': d['friction_limit_rec_N'],
            'friction_limit_std_N': d['friction_limit_std_N'],
            'weight_share_std_N': d['weight_share_std_N'],
            'weight_share_rec_N': d['weight_share_rec_N'],
            'weight_N_std': d['weight_N_std'],
            'builder_order_sum_kg': d['builder_order_sum_kg'],
            'load_path_holds': d['load_path_holds'],
            'press_n': d['press_n'],
        },
    }

    # 8: verdicts P1-P6
    verdicts = {}
    p1_ok = not p1_fired_windows
    verdicts['P1_hold_persists_all_declared_windows_placeholder'] = {
        'name': 'hold_persists_all_declared_windows_placeholder',
        'prediction': PREDICTIONS[
            'P1_hold_persists_all_declared_windows_placeholder'],
        'observed': ('%d/%d declared windows stick-complete at placeholder '
                     'mu; creep recorded per window'
                     % (len(kp.DECLARED_WINDOWS) - len(p1_fired_windows),
                        len(kp.DECLARED_WINDOWS))
                     if p1_ok else
                     'non-stick ticks inside declared windows: %s'
                     % ','.join(p1_fired_windows)),
        'verdict': 'SUPPORTED' if p1_ok else 'FALSIFIED',
        'falsifier_note': (
            'a fired P1 falsifier is a RECORDED persistence boundary (the '
            'creep-driven contact break class on the longest windows); it '
            'is never tuned away and never a silent pass; the slip '
            'recursion is the named discriminator'),
        'evidence': windows,
    }
    p2_ok = bool(boundary['agree_all'] and d['load_path_holds']
                 and d['mu_crit_inside_fa_band'])
    verdicts['P2_load_path_within_declared_ceiling'] = {
        'name': 'load_path_within_declared_ceiling',
        'prediction': PREDICTIONS['P2_load_path_within_declared_ceiling'],
        'observed': ('P_req std %r N / rec %r N <= %r N declared press; '
                     'margin %r N; thresholds inside F-A'
                     % (d['p_req_scene_n3_std_N'],
                        d['p_req_scene_n3_rec_N'], d['press_n'],
                        d['hold_margin_std_N'])),
        'verdict': 'SUPPORTED' if p2_ok else 'FALSIFIED',
        'falsifier_note': ('a threshold value-mismatch against the pinned '
                           'bytes is a harness refusal '
                           '(threshold_pin_mismatch); a solver-vs-closed-'
                           'form boundary contradiction is THIS falsifier'),
        'evidence': checks_p2,
    }
    p3_ok = bool(windows['W20']['identity_inside_gate_J']
                 and windows['W100']['identity_inside_gate_J']
                 and windows['W300']['identity_inside_gate_J']
                 and g07_ref_ok and rate_ok
                 and windows['W20']['press_impulse']['inside_bar']
                 and windows['W100']['press_impulse']['inside_bar']
                 and windows['W300']['press_impulse']['inside_bar'])
    verdicts['P3_hold_energy_ledger_closes'] = {
        'name': 'hold_energy_ledger_closes',
        'prediction': PREDICTIONS['P3_hold_energy_ledger_closes'],
        'observed': ('identity deltas %r J across W20/W100/W300; G07 W20 '
                     'reference deltas %r; rate rows %r'
                     % ({k: windows[k][
                         'ledger']['identity_gravity_minus_friction_J']
                         for k in ('W20', 'W100', 'W300')},
                        g07_ref_deltas, rate_rows)),
        'verdict': 'SUPPORTED' if p3_ok else 'FALSIFIED',
        'falsifier_note': ('identity breach, G07 reference breach, or rate '
                           'drift beyond the declared 1% band is THE P3 '
                           'FALSIFIER - a recorded drift boundary '
                           '(refinement finding), never tuned away'),
        'evidence': {'windows': {k: {'ledger': windows[k]['ledger'],
                                     'identity_inside_gate_J':
                                     windows[k]['identity_inside_gate_J']}
                                 for k in windows},
                     'g07_reference_deltas': g07_ref_deltas,
                     'g07_reference_ok': g07_ref_ok,
                     'rate_reference_J_per_tick_measured_w20': rate_w20,
                     'rate_rows': rate_rows,
                     'rate_band_declared': kp.WIN_RATE_BAND,
                     'tolerance_scans': scan},
    }
    p4_ok = bool(release['g07_release_account_state'] == 'CLEAN'
                 and release['w_press_zero_exact_every_release_tick']
                 and release['impulses_inside_bar']
                 and release['freefall_inside_window']
                 and release['ke_identity_inside_gate_J']
                 and release['terminal_inside_window']
                 and release['fall_inside_window']
                 and not release['supporting_post_release_contacts'])
    verdicts['P4_release_free_fall_identity'] = {
        'name': 'release_free_fall_identity',
        'prediction': PREDICTIONS['P4_release_free_fall_identity'],
        'observed': ('W_press == 0.0 J exactly every release tick: %s; '
                     'ground-contact events recorded: %d; supporting: %d'
                     % (release['w_press_zero_exact_every_release_tick'],
                        release['ground_contact_count'],
                        len(release['supporting_post_release_contacts']))),
        'verdict': 'SUPPORTED' if p4_ok else 'FALSIFIED',
        'falsifier_note': ('a non-zero press channel during release, a '
                           'free-fall identity breach beyond the declared '
                           'windows, or a post-release contact event '
                           'providing support is THE P4 FALSIFIER (a '
                           'failed release, recorded as such)'),
        'evidence': release,
    }
    p5_supported = bool(mu041_all_slip
                        and mu041.get('stick_assertion_bites')
                        and 'slip_recursion' in mu041)
    verdicts['P5_mu041_hold_nonclose_slip_recursion'] = {
        'name': 'mu041_hold_nonclose_slip_recursion',
        'prediction': PREDICTIONS[
            'P5_mu041_hold_nonclose_slip_recursion'],
        'observed': ('all channels slip; slip recursion dv %r m/s per tick '
                     'closes inside the sealed windows (observing the slip '
                     'SUPPORTS the prediction)' % (
                         mu041.get('slip_recursion', {})
                         .get('dv_per_tick_mps'),)
                     if p5_supported else
                     'UNEXPECTED: modes %r (a sustained hold at the '
                     'declared parameter 0.41 is THE P5 FALSIFIER - a '
                     'records discrepancy, never a win)' % (mu041_modes,)),
        'verdict': 'SUPPORTED' if p5_supported else 'FALSIFIED',
        'falsifier_note': ('a sustained static hold at declared parameter '
                           'mu=0.41 with everything else frozen would '
                           'CONTRADICT the static law as applied - '
                           'preserve as a records discrepancy, never a '
                           'win (K01 P5 falsifier carried verbatim)'),
        'mu_label': 'DECLARED SCENARIO PARAMETER (human-analogue transfer, '
                    'Gerhardt et al. 2008 textile at 14.8+/-1.3 N; NOT '
                    'monkey-bark; UNMEASURED; no re-pin mid-run per the '
                    'placeholder-mu law)',
        'objective_law': 'the predicted 0.41 slip completes the SUSTAIN '
                         'diagnostic at the declared parameters; the '
                         'playable hold objective stays open (prereg '
                         'section 0.3)',
        'evidence': mu041,
    }
    verdicts['P6_transfer_and_n4_fenced_not_run'] = {
        'name': 'transfer_and_n4_fenced_not_run',
        'prediction': PREDICTIONS['P6_transfer_and_n4_fenced_not_run'],
        'observed': ('no transfer phase and no n=4 shape run; the B5 '
                     'scene-line bound %r N*s > capacity %r N*s at n=3 '
                     '(at 0.41 band_lo n=3 %r > %r)'
                     % (d['transfer_req_scene_n3_ns'],
                        d['cap_ns_placeholder'],
                        d['transfer_req_band_lo_n3_ns'],
                        d['cap_ns_at_scenario_mu'])),
        'verdict': 'FENCED_NOT_RUN_BOUND_RECORDED',
        'evidence': {
            'transfer_req_scene_n3_ns': d['transfer_req_scene_n3_ns'],
            'transfer_req_scene_n2_ns': d['transfer_req_scene_n2_ns'],
            'transfer_req_band_lo_n3_ns': d['transfer_req_band_lo_n3_ns'],
            'capacity_ns_placeholder': d['cap_ns_placeholder'],
            'capacity_ns_at_scenario_mu': d['cap_ns_at_scenario_mu'],
            'never_misread_as': 'this refusal fences TRANSFER only; it is '
                                'NOT a grasp, contact, hold or release '
                                'refusal; the n=4 shape stays unactivated '
                                'absent a Captain declaration',
        },
    }
    falsified = [k for k, v in verdicts.items()
                 if str(v['verdict']).startswith('FALSIFIED')]
    overall = ('PREDICTION_FALSIFIED_PRESERVED: ' + ','.join(falsified)
               if falsified else 'CONFIRMING_MIXED_AS_PREDICTED')

    # 9: captures through the standing two-stage gate template
    verts0 = kp.initial_pad_verts(gc, geom, kp.READING_N[1])
    z0 = g05.initial_centroid_z(gc, geom, kp.READING_N[1])
    base_terminal = k01_receipt['verdicts'][
        'P1_approach_terminates_at_declared_seam']['evidence'][
            'terminal_distance_m']
    states = {}
    for name, state_key in (('W20', 'hold_w20'), ('W100', 'hold_w100'),
                            ('W300', 'hold_w300'),
                            ('hold_mu041', 'hold_mu041')):
        rows = arms[name]['rows']
        disp = kp.final_disp(rows, 3)
        kp.check_centroid_consistency(arms[name]['centroids'], z0, disp, 3)
        states[state_key] = {
            'kind': 'contact',
            'pad_verts': kp.pad_verts_after(rows, verts0, disp),
            'pad_modes': kp.final_modes(rows, 3),
            'attach': [c['centroid_m06']
                       for c in arms[name]['header']['channels']],
            'normals': [c['normal_m06']
                        for c in arms[name]['header']['channels']],
            'disp': disp,
            'base_pos': [base_terminal, 0.0, 0.0],
            'base_pos_provenance':
                'K01 sealed approach terminal pose (declared fixture '
                'placement provenance, K01 receipt P1 terminal_distance_m)',
        }
    rel_rows = arms['release_to_ground']['rows']
    rel_disp = kp.final_disp(rel_rows, 3, phase='release')
    kp.check_centroid_consistency(arms['release_to_ground']['centroids'],
                                  z0, rel_disp, 3)
    states['release_to_ground'] = {
        'kind': 'release',
        'pad_verts': kp.pad_verts_after(rel_rows, verts0, rel_disp),
        'pad_modes': kp.final_modes(rel_rows, 3, phase='release'),
        'attach': [c['centroid_m06']
                   for c in arms['release_to_ground']['header']['channels']],
        'normals': [c['normal_m06']
                    for c in arms['release_to_ground']['header']
                    ['channels']],
        'disp': rel_disp,
        'fall_disp': release['fall_per_pad_m'],
        'creep_disp': windows['W20']['creep_final_m'],
        'ground_contacts': release['ground_contact_events'],
        'ground_z_m': 0.0,
        'base_pos': [base_terminal, 0.0, 0.0],
        'base_pos_provenance':
            'K01 sealed approach terminal pose (declared fixture '
            'placement provenance, K01 receipt P1 terminal_distance_m)',
    }

    sys.path.insert(0, str(HERE / 'capture_card' / 'card'))
    import run_all as card_run_all
    capture_summary = card_run_all.run_cases(out_dir, states)
    capture_summary['preregistration_sha256'] = kp.PREREG_SHA256
    capture_summary_sha = write_canonical(
        os.path.join(out_dir, 'capture_summary.json'), capture_summary)

    # the receipt. The retracted defective quote forms NEVER enter any
    # artifact: strip them from the emitted derivation, serialize, tokenize
    # the emitted bytes, assert absence, then pin the result.
    receipt = {
        'schema': kp.SCHEMA,
        'card': 'MAT2-K02-STATIC-HOLD',
        'preregistration_sha256': kp.PREREG_SHA256,
        'prereg_commit': kp.PREREG_COMMIT,
        'base_sha': kp.BASE_SHA,
        'merged_tip': kp.MERGED_TIP,
        'merged_tip_verification': kp.MERGED_TIP_NOTE,
        'pins': pin_rows,
        'template_pins': template_rows,
        'derivation': {k: v for k, v in d.items()
                       if k != '_defective_literal_forms'},
        'derivation_presence': presence,
        'tolerance_scans': scan,
        'declared_annotations': kp.annotations(d),
        'findings': [
            {
                'class': 'creep_expectation_vs_measured_record',
                'finding':
                    'the prereg P1 expectation quotes the pinned G7 '
                    'ledger creep 0.0024525000000000007 m per 20 ticks '
                    '(Baumgarte-bias scale) as the expected hold-creep '
                    'scale; the MEASURED scene|n=3 stick hold records '
                    'exact-zero cumulative creep in EVERY declared window '
                    '(W20/W100/W300, all three channels). The pinned G7 '
                    'quote belongs to the G07 ledger record corpus; the '
                    'scene|n=3 stick class at this operating point holds '
                    'with zero net displacement per tick (ke_delta class '
                    '1e-36 in the pinned G07 scene|n=3 hold account), so '
                    'the creep-driven contact-break risk does not fire '
                    'and the persistence boundary is not reached. '
                    'RECORDED, never normalized; nothing tuned.',
                'disposition': 'recorded finding; routed to the '
                               'Lieutenant with the chain stop',
            },
            {
                'class': 'declared_release_recording_conventions',
                'finding':
                    'the release-leg recording conventions are declared '
                    'in this package BEFORE the sealed run: the free-fall '
                    'recursion is evaluated on v_down = -vz (the G07 '
                    'release_account convention), the terminal speed is '
                    'compared by magnitude (vz is negative downward), '
                    'and a post-release contact EVENT is a pad-tick whose '
                    'recorded impulse exceeds the share-scaled bar '
                    '(sub-bar float noise is the G07 clean-release class '
                    'that release_account bars). Dev run '
                    '3b3b44ae9cbb4c70ad7ffec121c1fe13 (PRESERVED) first '
                    'ran the P4 leg with two harness recording defects '
                    '(gravity-sign recursion, unbarred event '
                    'classification) that mis-marked P4 FALSIFIED while '
                    'the G07 sealed release account itself ran CLEAN; '
                    'that falsified verdict is preserved in the dev '
                    'receipts, never silently discarded, and the P4 '
                    'verdict in THIS receipt is the corrected-recording '
                    'measurement of the same physics.',
                'disposition': 'declared in this package before the '
                               'sealed run; dev receipts preserved',
            },
        ],
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
            'hold_windows_ticks': dict(kp.DECLARED_WINDOWS),
            'mu041_ticks': kp.MU041_TICKS,
            'release_hold_ticks': kp.RELEASE_HOLD_TICKS,
            'release_fall_ticks': kp.RELEASE_FALL_TICKS,
            'release_structure': 'the G07 structure (20 hold + 40 release)',
            'cadence_hz': d['cadence_hz'],
            'tick_seconds': lc.DT,
            'seconds_annotations':
                'computed FROM the frozen tick counts (the K01 finding-1 '
                'annotation class is impossible here by construction)',
        },
        'declared_tolerance_windows': {
            'win_jn_Ns': kp.WIN_JN,
            'win_recursion_mps': kp.WIN_RECURSION_V,
            'win_disp_m': kp.WIN_DISP,
            'win_release_scale_Ns_per_kg': kp.WIN_RELEASE_SCALE,
            'win_energy_identity_J': kp.WIN_ENERGY_IDENTITY,
            'win_g07_reference_J': kp.WIN_G07_REFERENCE,
            'win_g07_fall_m': kp.WIN_G07_FALL,
            'win_rate_band': kp.WIN_RATE_BAND,
            'win_k01_class': kp.WIN_K01_CLASS,
        },
        'arm_checks': {
            'windows': {k: {kk: vv for kk, vv in w.items()
                            if kk != 'ledger'}
                        for k, w in windows.items()},
            'release': release,
            'mu041': mu041,
            'p2': checks_p2,
        },
        'observer_cross_checks': {
            name: trace[name]['observer_cross_check'] for name in arms},
        'site_census': kp.site_census(arms),
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
    import test_k02_checks as checks
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
        'schema': 'chimera.k02_named_checks.v1',
        'preregistration_sha256': kp.PREREG_SHA256,
        'tests_run': result.testsRun, 'failures': rows,
        'green': result.wasSuccessful(),
    }


def run_regression():
    """The UNMODIFIED upstream suites re-run as direct scripts (the K01
    regression invocation). DECLARED SCOPE (recorded, never silent): the
    gate suites are the two DIRECT upstream interfaces of this card - G04
    (grip fixture) and G05 (observation seam). The M06 solver suite runs
    too; its probes P1-P11 are the solver integrity evidence; its P12 leg
    re-runs the M01/M02/M04 suites (and an engine asset) outside this
    package's declared read scope, so a full-repository M06 run is NOT
    claimed (NO_WORKTREES: reduced packages never claim full-repository
    gates). The M06 row is green for this card iff P1-P11 all PASS and the
    ONLY failure is the P12 out-of-scope file miss; any probe failure
    fails the gate."""
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
        'schema': 'chimera.k02_regression.v1',
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
    except kp.K02Refusal as refusal:
        payload = {
            'schema': kp.SCHEMA, 'card': 'MAT2-K02-STATIC-HOLD',
            'preregistration_sha256': kp.PREREG_SHA256,
            'refusal': str(refusal), 'state': 'REFUSED_HARNESS',
        }
        write_canonical(os.path.join(OUT_DIR, 'k02_experiment_receipt.json'),
                        payload)
        print('REFUSED: %s' % refusal)
        return 4

    receipt_sha = write_canonical(
        os.path.join(OUT_DIR, 'k02_experiment_receipt.json'), receipt)
    trace_sha = write_canonical(os.path.join(OUT_DIR, 'k02_trace.json'),
                                trace)

    # determinism pair: full second pass into a disposable directory
    out2 = os.path.normpath(os.path.join(OUT_DIR, '..', 'outputs_rerun2'))
    try:
        trace2, receipt2 = battery_once(out2, '_rerun2')
    except kp.K02Refusal as refusal:
        print('REFUSED (rerun2): %s' % refusal)
        return 4
    receipt2_sha = write_canonical(
        os.path.join(OUT_DIR, 'k02_experiment_receipt_rerun2.json'),
        receipt2)
    trace2_sha = write_canonical(
        os.path.join(OUT_DIR, 'k02_trace_rerun2.json'), trace2)
    determinism = {
        'schema': 'chimera.k02_determinism.v1',
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
