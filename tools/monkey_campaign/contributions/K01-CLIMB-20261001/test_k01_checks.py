"""K01 named checks (house-standard named-check suite; run in-process by
run_battery after the battery). Every check asserts a prereg-bound property
against the recorded receipt/trace; no check can pass vacuously."""
from __future__ import annotations

import json
import math
import pathlib
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import k01_physics as kp  # noqa: E402

STATE = {}


def require(ok, code):
    if not ok:
        raise AssertionError(code)


class K01NamedChecks(unittest.TestCase):

    def test_prereg_bytes_pinned(self):
        got = kp.sha256_file(kp.HERE / 'PREREGISTRATION.md')
        require(got == kp.PREREG_SHA256,
                'preregistration bytes drift: ' + got)

    def test_receipt_embeds_prereg_sha(self):
        require(STATE['receipt']['preregistration_sha256']
                == kp.PREREG_SHA256, 'receipt prereg sha missing')

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
        require(w['approach_horizon_ticks'] == 10500, 'horizon drift')
        require(w['grasp_attempt_ticks'] == 240, 'grasp window drift')
        require(w['hold_ticks'] == 20, 'hold window drift')
        require(w['zero_mu_control_ticks'] == 40, 'control window drift')
        require(w['tick_seconds'] == 0.005,
                'tick drift (pinned M06 DT)')
        # prereg section 10 annotates "300 Hz"; the pinned DT gives 200 Hz.
        # The annotation mismatch is a RECORDED FINDING (receipt findings
        # block); the tick windows are the frozen executable quantities.
        require(any(f['class'] == 'prereg_annotation_mismatch'
                    for f in STATE['receipt']['findings']),
                'the cadence annotation finding must be recorded')

    def test_static_threshold_scene_n3_derived(self):
        d = STATE['receipt']['derivation']
        require(d['mu_crit_scene_n3_std'] == 0.5468840727038888,
                'std threshold drift')
        require(d['mu_crit_scene_n3_rec'] == 0.5470708910000001,
                'rec threshold drift')
        require(d['p_req_scene_n3_std_N'] == 54.68840727038889,
                'P_req drift')

    def test_transfer_bound_scene_lines(self):
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

    def test_wrap_margin_mu_independent(self):
        d = STATE['receipt']['derivation']
        require(d['wrap_margin_m'] == -0.01733690019744087,
                'wrap margin drift')
        require(d['fingertip_span_m'] == 0.056663099802559125,
                'span drift')
        require(d['trunk_diameter_m'] == 0.074, 'diameter drift')
        require(d['pincer_mu_crit'] == 0.8399663223427114,
                'pincer mu_crit drift')
        require(d['pincer_mu_crit'] > d['mu_placeholder_s'],
                'pincer mu_crit must sit above the placeholder')
        require(d['pincer_chord_min_m'] == 0.06345447650272827,
                'pincer chord window drift')

    def test_scenario_mu_label_and_value(self):
        require(kp.MU_SCENARIO == 0.41, 'declared parameter drift')
        receipt = STATE['receipt']
        require('NOT monkey-bark' in receipt['mu_label']['scenario_0_41'],
                'the 0.41 label must carry the NOT-monkey-bark law')
        require('UNMEASURED' in receipt['mu_label']['scenario_0_41'],
                'the 0.41 label must carry UNMEASURED')

    def test_zero_mu_control_matches_pinned_g04(self):
        checks = STATE['receipt']['arm_checks']['zero_mu_control']
        require(checks['zero_mu_slides'] is True,
                'the zero-mu control must slide (FB2)')
        require(checks['matches_pinned_g04_reading'] is True,
                'control slide must match the pinned G04 FB2 reading')
        d = STATE['receipt']['derivation']['zero_mu_control']
        require(abs(d['disp_hold_closed_form_m']
                    - d['pinned_g04_fb2_reading_m']) <= kp.WIN_ZERO_MU_PIN,
                'closed form vs pinned reading window')

    def test_slip_recursion_discriminator_live(self):
        checks = STATE['receipt']['arm_checks']['hold_mu041']
        rec = checks['slip_recursion']
        require(rec['dv_per_tick_mps'] > 0.0,
                'the 0.41 slip must have nonzero downward acceleration')
        require(rec['worst_v_residual_mps'] <= kp.WIN_RECURSION_V,
                'slip recursion residual outside sealed window')
        require(checks['stick_assertion_bites'] is True,
                'the stick assertion must FAIL on the 0.41 trace')

    def test_boundary_agreement(self):
        require(STATE['receipt']['arm_checks']['boundary_agreement'][
            'agree_all'] is True, 'boundary disagreement')

    def test_verdicts_match_frozen_predictions(self):
        verdicts = STATE['receipt']['verdicts']
        expect = {
            'P1_approach_terminates_at_declared_seam': 'SUPPORTED',
            'P2_declared_pads_establish_stick_class': 'SUPPORTED',
            'P3_recorded_config_grasp_refused':
                'SUPPORTED_REFUSAL_OBSERVED',
            'P4_anatomical_grasp_undecidable': 'UNDECIDABLE_HONEST_ABSENT',
            'P5_scene_n3_hold_closes_at_placeholder': 'SUPPORTED',
            'P6_transfer_out_of_scope_nonclosing':
                'FENCED_NOT_RUN_BOUND_RECORDED',
        }
        for key, want in expect.items():
            require(verdicts[key]['verdict'] == want,
                    '%s: %s != %s' % (key, verdicts[key]['verdict'], want))

    def test_no_transfer_phase_ran(self):
        trace = STATE['trace']
        for name in trace:
            if name in ('schema', 'pass', 'preregistration_sha256',
                        'approach'):
                continue
            require('transfer' not in name,
                    'a transfer phase ran: ' + name)

    def test_seam_censuses_accepted(self):
        for name, census in STATE['receipt']['seam_censuses'].items():
            require(census['refusals'] == [],
                    'seam refused deliveries: %s' % name)
            require(census['accepted'] > 0, 'empty seam census')

    def test_approach_window_declared_scaffold(self):
        s = STATE['receipt']['scaffold_declaration']
        lo, hi = s['terminal_window_m']
        require(0.0 < lo < hi < 0.5, 'window must sit inside the G06 '
                'declared fixture reach envelope 0.5 m')
        require(s['start_base_to_trunk_axis_m'] >= 2.0,
                'start must respect the F05 >= 2.0 placement law')
        require('SCAFFOLD' in s['label'], 'scaffold must be labeled')
        approach = STATE['receipt']['approach']
        require(lo <= approach['terminal_distance_m'] <= hi,
                'terminal distance outside window')
        require(approach['terminal_tick'] <= 10500, 'horizon exceeded')

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
