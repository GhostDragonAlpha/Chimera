"""K02 named checks (house-standard named-check suite; run in-process by
run_battery after the battery). Every check asserts a prereg-bound property
against the recorded receipt/trace; no check can pass vacuously."""
from __future__ import annotations

import json
import pathlib
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import k02_physics as kp  # noqa: E402

STATE = {}


def require(ok, code):
    if not ok:
        raise AssertionError(code)


class K02NamedChecks(unittest.TestCase):

    def test_prereg_bytes_pinned(self):
        got = kp.sha256_file(kp.HERE / 'PREREGISTRATION.md')
        require(got == kp.PREREG_SHA256,
                'preregistration bytes drift: ' + got)

    def test_receipt_embeds_prereg_sha(self):
        require(STATE['receipt']['preregistration_sha256']
                == kp.PREREG_SHA256, 'receipt prereg sha missing')

    def test_base_and_merged_tip_recorded(self):
        receipt = STATE['receipt']
        require(receipt['base_sha'] == kp.PREREG_COMMIT, 'base sha drift')
        require(receipt['merged_tip'] == kp.MERGED_TIP,
                'merged tip pin drift')
        require('d100e87c' in receipt['merged_tip_verification'],
                'merged-tip verification note missing')

    def test_template_manifest_pins_embedded_modules(self):
        manifest = json.loads(
            (kp.HERE / 'capture_card/TEMPLATE_MANIFEST.json')
            .read_bytes().decode('utf-8'))
        for rel, expect in manifest['files'].items():
            got = kp.sha256_file(kp.HERE / 'capture_card' / rel)
            require(got == expect, 'template pin drift: ' + rel)

    def test_view_spec_hash_pinned_before_capture(self):
        sys.path.insert(0, str(kp.HERE / 'capture_card'))
        from capture_gate import view_spec
        spec = json.loads((kp.HERE / 'capture_card/card/view_spec.json')
                          .read_bytes().decode('utf-8'))
        prereg = json.loads((kp.HERE / 'capture_card/card/card_prereg.json')
                            .read_bytes().decode('utf-8'))
        require(prereg['view_spec']['prereg_sha256']
                == view_spec.spec_prereg_sha256(spec),
                'view-spec prereg pin mismatch')
        require(prereg['experiment_preregistration'][
            'preregistration_sha256'] == kp.PREREG_SHA256,
            'card prereg does not bind the committed experiment prereg')

    def test_declared_windows_frozen(self):
        w = STATE['receipt']['windows']
        require(w['hold_windows_ticks'] == {'W20': 20, 'W100': 100,
                                            'W300': 300},
                'hold window drift')
        require(w['mu041_ticks'] == 20, '0.41 window drift')
        require(w['release_hold_ticks'] == 20
                and w['release_fall_ticks'] == 40,
                'release structure drift (the G07 structure is 20+40)')
        require(w['tick_seconds'] == 0.005, 'tick drift (pinned M06 DT)')
        require(w['cadence_hz'] == 200.0, 'cadence drift')
        ann = STATE['receipt']['declared_annotations']
        require(ann['w20_seconds'] == 20 * 0.005
                and ann['w100_seconds'] == 100 * 0.005
                and ann['w300_seconds'] == 300 * 0.005
                and ann['release_fall_seconds'] == 40 * 0.005,
                'seconds annotations must be computed FROM tick counts')

    def test_static_thresholds_and_margin_derived(self):
        d = STATE['receipt']['derivation']
        require(d['mu_crit_scene_n3_std'] == 0.5468840727038888,
                'std threshold drift')
        require(d['mu_crit_scene_n3_rec'] == 0.5470708910000001,
                'rec threshold drift')
        require(d['p_req_scene_n3_std_N'] == 54.68840727038889,
                'P_req std drift')
        require(d['p_req_scene_n3_rec_N'] == 54.70708910000001,
                'P_req rec drift')
        require(d['hold_margin_std_N'] == 5.311592729611107,
                'margin drift')
        require(d['friction_limit_rec_N'] == 36.0,
                'per-channel friction limit (rec) drift')
        require(d['friction_limit_std_N'] == 35.98770642201834,
                'per-channel friction limit (std) drift')
        require(d['weight_share_std_N'] == 32.81304436223334,
                'weight share drift')
        require(d['weight_N_std'] == 98.43913308670002, 'weight drift')
        require(d['weight_share_std_N'] < d['friction_limit_std_N'],
                'the weight share must sit below the friction limit')

    def test_mu_crit_inside_declared_fa_band(self):
        d = STATE['receipt']['derivation']
        require(d['mu_crit_inside_fa_band'] is True,
                'closure thresholds must sit inside the declared F-A band')
        require(d['fa_band'] == [0.3, 1.0], 'F-A band drift')

    def test_transfer_bound_scene_lines_fenced(self):
        d = STATE['receipt']['derivation']
        require(d['transfer_req_scene_n3_ns'] == 0.24618190095000003,
                'scene n=3 transfer bound drift')
        require(d['transfer_req_scene_n3_ns'] > d['cap_ns_placeholder'],
                'B5 bound must not close at n=3')
        require(d['transfer_req_scene_n2_ns'] == 0.49236380190000006,
                'scene n=2 transfer bound drift')
        require(d['transfer_req_band_lo_n3_ns'] == 0.13243500000000002,
                'band_lo n=3 transfer bound drift')
        require(d['transfer_req_band_lo_n3_ns']
                > d['cap_ns_at_scenario_mu'], 'no transfer closes at 0.41')

    def test_scenario_mu_label_and_value(self):
        require(kp.MU_SCENARIO == 0.41, 'declared parameter drift')
        receipt = STATE['receipt']
        require('NOT '
                'monkey-bark' in receipt['mu_label']['scenario_0_41'],
                'the 0.41 label must carry the NOT-monkey-bark law')
        require('UNMEASURED' in receipt['mu_label']['scenario_0_41'],
                'the 0.41 label must carry UNMEASURED')

    def test_hold_windows_stick_with_press_and_census(self):
        checks = STATE['receipt']['arm_checks']['windows']
        for name in ('W20', 'W100', 'W300'):
            w = checks[name]
            require(w['stick_census']['stick_all'] is True,
                    '%s: a non-stick tick inside a declared window at '
                    'placeholder mu (the P1 falsifier class)' % name)
            require(w['press_inside_bar'] is True,
                    '%s: press envelope breach' % name)
            require(w['stick_census']['ticks_checked'] ==
                    {'W20': 20, 'W100': 100, 'W300': 300}[name],
                    '%s: window length drift' % name)

    def test_hold_ledger_identity_and_g07_reference(self):
        receipt = STATE['receipt']
        p3 = receipt['verdicts'][
            'P3_hold_energy_ledger_closes']['evidence']
        for name in ('W20', 'W100', 'W300'):
            require(p3['windows'][name]['identity_inside_gate_J'] is True,
                    '%s: gravity work != friction losses beyond 1e-9 J'
                    % name)
        require(p3['g07_reference_ok'] is True,
                'the W20 window must reproduce the pinned G07 ledger '
                'within 1e-9 J')

    def test_rate_band_and_impulse_ledger(self):
        p3 = STATE['receipt']['verdicts'][
            'P3_hold_energy_ledger_closes']['evidence']
        require(p3['rate_rows']['W100']['inside_declared_1pct_band']
                is True, 'W100 press-rate drift beyond the declared 1% band')
        require(p3['rate_rows']['W300']['inside_declared_1pct_band']
                is True, 'W300 press-rate drift beyond the declared 1% band')
        windows = STATE['receipt']['arm_checks']['windows']
        for name in ('W20', 'W100', 'W300'):
            require(windows[name]['press_impulse']['inside_bar'] is True,
                    '%s: window press impulse outside the scaled bar' % name)

    def test_creep_recorded_per_window(self):
        windows = STATE['receipt']['arm_checks']['windows']
        for name in ('W20', 'W100', 'W300'):
            creep = windows[name]['creep_final_m']
            require(len(creep) == 3 and all(c >= 0.0 for c in creep),
                    '%s: creep must be recorded per channel' % name)
        g07 = STATE['receipt']['derivation']['g07_reference']
        require(g07['w20_press_J'] == 0.8069338128977511,
                'G07 W20 press reference drift')
        require(g07['w20_gravity_J'] == 0.24150444483195008,
                'G07 W20 gravity reference drift')
        require(g07['w20_friction_J'] == 0.24150444482831965,
                'G07 W20 friction reference drift')

    def test_findings_recorded(self):
        findings = STATE['receipt']['findings']
        classes = {f['class'] for f in findings}
        require('creep_expectation_vs_measured_record' in classes,
                'the creep expectation-vs-measured finding must be '
                'recorded')
        require('declared_release_recording_conventions' in classes,
                'the declared release recording conventions finding must '
                'be recorded')

    def test_release_leg_law(self):
        release = STATE['receipt']['arm_checks']['release']
        require(release['g07_release_account_state'] == 'CLEAN',
                'the G07 sealed release account refused: %r'
                % release['g07_release_account'])
        require(release['w_press_zero_exact_every_release_tick'] is True,
                'W_press must be 0.0 J exactly every release tick')
        require(release['impulses_inside_bar'] is True,
                'release impulses outside the share-scaled noise bar')
        require(release['freefall_inside_window'] is True,
                'free-fall recursion breach beyond 1e-9 m/s')
        require(release['ke_identity_inside_gate_J'] is True,
                'release gravity work != KE gain beyond 1e-9 J')
        require(release['terminal_inside_window'] is True,
                'terminal speed != 40*g_rec*DT beyond 1e-9 m/s')
        require(release['fall_inside_window'] is True,
                'fall displacement vs the G07 same-class reading beyond '
                '1e-9 m')
        require(release['terminal_mps_derived'] == 1.9620000000000002,
                'terminal derivation drift')
        require(release['g07_reference_release']['ke_J']
                == 19.320355586289068, 'G07 release KE reference drift')
        require(release['g07_reference_release']['gravity_J']
                == 19.320355586443497,
                'G07 release gravity reference drift')
        require('ABSENT' in release['impact_model'],
                'the no-impact-model honest absence must be stated')

    def test_ground_contacts_recorded_never_support(self):
        release = STATE['receipt']['arm_checks']['release']
        require('ground_contact_events' in release,
                'ground-contact records missing (recorded, never support)')
        require(release['supporting_post_release_contacts'] == [],
                'a post-release contact provided support (the P4 falsifier)')

    def test_slip_recursion_discriminator_live(self):
        checks = STATE['receipt']['arm_checks']['mu041']
        rec = checks['slip_recursion']
        require(rec['dv_per_tick_mps'] == 0.012289681856880237,
                'declared-parameter slip dv drift (K01-sealed class)')
        require(rec['worst_v_residual_mps'] <= kp.WIN_RECURSION_V,
                'slip recursion residual outside sealed window')
        require(rec['worst_disp_residual_m'] <= kp.WIN_DISP,
                'slip displacement residual outside sealed window')
        require(checks['stick_assertion_bites'] is True,
                'the stick assertion must FAIL on the 0.41 trace')
        require(max(checks['k01_class_disp_delta_m']) <= kp.WIN_K01_CLASS,
                'window displacement outside the K01-sealed class')

    def test_boundary_agreement(self):
        require(STATE['receipt']['arm_checks']['p2'][
            'boundary_agreement']['agree_all'] is True,
            'boundary disagreement')

    def test_verdicts_match_frozen_predictions(self):
        verdicts = STATE['receipt']['verdicts']
        expect = {
            'P1_hold_persists_all_declared_windows_placeholder': 'SUPPORTED',
            'P2_load_path_within_declared_ceiling': 'SUPPORTED',
            'P3_hold_energy_ledger_closes': 'SUPPORTED',
            'P4_release_free_fall_identity': 'SUPPORTED',
            'P5_mu041_hold_nonclose_slip_recursion': 'SUPPORTED',
            'P6_transfer_and_n4_fenced_not_run':
                'FENCED_NOT_RUN_BOUND_RECORDED',
        }
        for key, want in expect.items():
            require(verdicts[key]['verdict'] == want,
                    '%s: %s != %s' % (key, verdicts[key]['verdict'], want))

    def test_objective_law_recorded_on_the_diagnostic(self):
        v5 = STATE['receipt']['verdicts'][
            'P5_mu041_hold_nonclose_slip_recursion']
        require('diagnostic' in v5['objective_law'],
                'the objective-line law must ride with the 0.41 diagnostic')
        require('stays open' in v5['objective_law'],
                'the playable hold objective must be recorded OPEN')

    def test_no_transfer_phase_or_n4_ran(self):
        trace = STATE['trace']
        for name in trace:
            if name in ('schema', 'preregistration_sha256'):
                continue
            require('transfer' not in name and 'n4' not in name
                    and 'ascent' not in name,
                    'a fenced phase ran: ' + name)

    def test_observer_cross_checks_recorded(self):
        for name, row in STATE['receipt']['observer_cross_checks'].items():
            require('bit-identical' in row,
                    '%s: the pinned-runner cross-check must be recorded'
                    % name)

    def test_site_census_clean(self):
        census = STATE['receipt']['site_census']
        require(census['undeclared'] == [],
                'undeclared contact sites recorded')
        require(census['records'] > 0, 'empty site census')

    def test_retracted_quotes_absent(self):
        absence = STATE['receipt']['retracted_quote_absence']
        require(absence['status'] == 'ABSENT_OK'
                and absence['present'] == [],
                'retracted defective quotes present in the receipt')

    def test_capture_gate_ran_green(self):
        receipt = STATE['receipt']
        require(receipt['capture_verdict'] == 'PASS',
                'capture gate not green')
        require(len(receipt['capture_summary_sha256']) == 64,
                'capture summary hash missing')

    def test_regression_gate_in_declared_scope(self):
        reg = STATE.get('regression') or {}
        require(reg.get('green') is True, 'regression gate not green')
        require('G04+G05' in reg.get('declared_scope', ''),
                'regression declared scope missing')
        m06 = [s for s in reg.get('suites', []) if s['suite'] == 'M06']
        require(m06 and (m06[0].get('p1_p11_green_in_scope') is True),
                'M06 in-scope probes not green')


if __name__ == '__main__':
    unittest.main()
