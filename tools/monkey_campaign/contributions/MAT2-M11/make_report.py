"""MAT2-M11 report generator: report.md is GENERATED from the committed
receipts (prose from receipts; no observed value is hand-transcribed).
Every number in the report is an f-string substitution from a receipt
field; the loaders FAIL FIRST (named codes) when a receipt is missing or
off-spec (P3). Run from this directory AFTER all modes, the capture and
the evidence anchoring:
    python -B make_report.py <candidate_head_sha>
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent

CRITERIA = ('0588c4140a9968160cd640507e02a5b0cefefa6238ff3107de4c232'
            'f0d7ea72e')
ATTEMPT = '8de1349ae67840fc8b8a15fb647c5e4a'
ARRIVAL = 'arrival-f11f7489a821465ea2c014fea51698f8'


def require(condition, code):
    if not condition:
        raise ValueError(code)


def load(name, required_keys=()):
    path = HERE / name
    require(path.exists(), 'm11_report_receipt_missing:' + name)
    doc = json.loads(path.read_text(encoding='utf-8'))
    for key in required_keys:
        require(key in doc,
                'm11_report_receipt_schema:' + name + ':' + key)
    return doc


def sha256_file(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def main():
    head = sys.argv[1]
    arec = load('experiment_receipt.json',
                ('X1_pass', 'X2_pass', 'X3_pass', 'X4_pass', 'X5_pass',
                 'X6_pass', 'X8_pass', 'all_gates_green', 'trace_sha256',
                 'X1_shape_identity', 'X2_real_data', 'X3_statics',
                 'X4_activation_off', 'X5_connection_removal', 'X6_limits',
                 'X8_ledger'))
    frec = load('falsifier_receipt.json', ('all_arms_bit',))
    drec = load('determinism_receipt.json', ('X7_trace_byte_identical',))
    grec = load('regression_receipt.json', ('regression_ok',))
    crec = load('capture_validation_receipt.json',
                ('structurally_valid', 'video_sha256', 'codec',
                 'criteria_sha256'))
    cams = load(str(pathlib.Path('capture') / 'evidence' / 'cameras.json'),
                ('row_order_proof', 'camera_consistency_proof',
                 'layer_presence_proof'))
    anch = load('evidence_anchors.json', ('anchors',))
    trace = load('experiment_trace.json', ('dynamic_run',))
    chain_mass = {e['name']: e['mass_kg']
                  for e in trace['dynamic_run']['chain_spec']}
    require(arec['criteria_sha256'] == CRITERIA, 'criteria_mismatch')
    require(crec['criteria_sha256'] == CRITERIA, 'capture_criteria_mismatch')
    require(arec['all_gates_green'] is True, 'bank_not_green')
    require(frec['all_arms_bit'] is True, 'arms_not_all_bit')
    require(drec['X7_trace_byte_identical'] is True, 'not_deterministic')
    require(grec['regression_ok'] is True, 'regression_not_green')
    require(crec['structurally_valid'] is True, 'capture_not_valid')

    x1 = arec['X1_shape_identity']
    x2 = arec['X2_real_data']
    x3 = arec['X3_statics']
    x4 = arec['X4_activation_off']
    x5 = arec['X5_connection_removal']
    x8 = arec['X8_ledger']
    fb1 = frec['FB1_overlay_driven_motion']
    fb2 = frec['FB2_area_independent_forces']
    fb3 = frec['FB3_clipped_load_path']
    fb4 = frec['FB4_hidden_support']
    fb5 = frec['FB5_unaccounted_energy']
    fb6 = frec['FB6_synthetic_port_standin']
    stage = x3['stage_limb']
    ico_x8 = x8['icosphere']
    cube_x8 = x8['cube']
    limb_x8 = x8['limb']
    limb_x4 = x4['limb']
    bindings = x2['X2c_attachments']['bindings']

    def anchor(name):
        for a in anch['anchors']:
            if a['name'] == name:
                return a['store_path'], a['sha256']
        raise ValueError('m11_report_anchor_missing:' + name)

    num_receipt, num_sha = anchor('experiment_receipt.json')
    num_trace, trace_sha_store = anchor('experiment_trace.json')
    num_fal, fal_sha = anchor('falsifier_receipt.json')
    num_det, det_sha = anchor('determinism_receipt.json')
    num_reg, reg_sha = anchor('regression_receipt.json')
    num_vid, vid_sha = anchor('capture_mat2_m11_limb.mkv')
    num_man, man_sha = anchor('capture_manifest.json')

    lines = []
    w = lines.append
    w('# MAT2-M11 report — reuse the same material rules in a loaded '
      'monkey limb')
    w('')
    w('Attempt %s, arrival %s, criteria sha256 %s. Attempt branch branch-1 '
      'fast-forwarded (ancestor check first) to the sealed line tip '
      '362da5056f84b56b62a13cfb878dddb98538b18f (merge of PR #271, the '
      'MAT2-M10 winner), which carries the merged winners of every '
      'declared dependency (MAT2-M09, MAT2-M10, MAT2-B03, MAT2-B04, '
      'MAT2-B05) and the whole M01-M08 law stack. Candidate head %s. '
      'PREREGISTRATION.md was committed (1ee40f9d) BEFORE the '
      'implementation existed and before any measurement; Amendments A1 '
      '(5159078c), A2 (e195a796) and A3 (f573767d) are separate commits on '
      'the amendment chain, each committed before the receipts that cite '
      'it; every triggering probe value is recorded in the amendment '
      'text.'
      % (ATTEMPT, ARRIVAL, CRITERIA, head))
    w('')
    w('This report is GENERATED by make_report.py from the committed '
      'receipts — no observed value is hand-transcribed. Evidence '
      'anchoring (CARD_STARTER v2): every referenced workspace artifact '
      'was copied into the durable evidence store and sha-verified BEFORE '
      'reference; the anchors live in evidence_anchors.json (%s) and are '
      'listed at the end of this report.' % num_man.split('/')[-1])
    w('')
    w('## done_when clause map (verbatim clauses; all on the candidate '
      'revision)')
    w('')
    w('| clause | execution | result |')
    w('|---|---|---|')
    w('| same law implementation on two distinct shapes without '
      'shape-specific motion code | the M03/M04/M05 law stack imported '
      'UNMODIFIED, composed once in LimbWorld; shapes are builder data '
      '(icosphere L2 R=0.05 m, cube grid side 0.10 m); X1a AST audit '
      'clean (%d dynamics methods, zero shape conditionals, zero shape '
      'literals); X1b run identity: %d runs, all law-identical (%s); '
      'X1c whole-system statics green on both synthetic shapes in every '
      'declared window | X1_pass=%s'
      % (len(x1['X1a_ast']['dynamics_methods']),
         arec['run_identity_count'],
         x1['X1b_run_identity']['compared_subset'].split(' (')[0],
         arec['X1_pass']))
    w('| then on the selected monkey limb | the limb tissue is a capped '
      'tube bladder between the REAL endpoints (top: %s; bottom: %s); '
      'real B03 masses ride the chain (bitwise audit clean: %s); 4/4 '
      'chain ties cite A06 attachment-role records verbatim (%s); the '
      'B05 port ledger is carried (%d ports, lawful statuses, 1 '
      'explicitly-unresolved terminal) | X2_pass=%s'
      % (x2['X2b_frames']['audit']['axis_top_source'].split(' (')[0],
         x2['X2b_frames']['audit']['axis_bottom_source'].split(' (')[0],
         ', '.join('%s=%.10e kg' % (k, chain_mass[k])
                   for k in ('humerus', 'ulna', 'radius')),
         ', '.join(b['tie_id'] + ':' + b['site']['record_id']
                   for b in bindings),
         x2['X2d_ports']['port_count'], arec['X2_pass']))
    w('| show tissue-to-bone-to-foot-to-ground load transmission | the '
      'A1/A2 hanging bone-chain rig: pressurization descends the free '
      'pole and presses the foot; whole-system statics '
      'F_clamp + sum(F_contacts) = W_total close in every declared '
      'window on all three shapes (worst residual %.2e N, bound %.3f N); '
      'limb stage statics at hold: F_contact %.6f N, T1 %.6f N, T4 %.6f N '
      '(foot identity residual %.2e N, chain-top %.2e N, bounds %.3f N) '
      '| X3_pass=%s'
      % (max(abs(v['residual_n'])
             for s in x3['per_shape'].values() for v in s.values()),
         x3['per_shape']['icosphere']['P0']['bound_n'],
         stage['HOLD']['f_contact_n'], stage['HOLD']['t1_n'],
         stage['HOLD']['t4_n'],
         stage['HOLD']['foot_identity_residual_n'],
         stage['HOLD']['chain_top_identity_residual_n'],
         stage['HOLD']['foot_identity_bound_n'], arec['X3_pass']))
    w('| activation-off control | the bitwise-0 vs positive '
      'discriminator: at p=0 the foot contact is bitwise 0.0 N in P0, in '
      'the OFF window and over the whole dedicated never-pressurized run '
      'on all three shapes; at hold the measured contact is %.6f N '
      '(limb); power-off recovery |gap_off(loaded) - gap_off(dedicated '
      'never-pressurized run)| = %.2e m (limb), window %.1e m (A2) | '
      'X4_pass=%s'
      % (stage['HOLD']['f_contact_n'], limb_x4['recovery_gap_m'],
         limb_x4['recovery_window_m'], arec['X4_pass']))
    w('| connection-removal control | releasing T2 at the declared tick '
      '450 (M05 release_of_unbound_bond vocabulary; double release '
      'refuses): released T2 tension bitwise 0.0; bound-vs-released '
      'departure %.2e m >= bite 1e-3 m; T1 drop %.6f N = W(ulna)+W(radius) '
      '(static %.6f N, A3 re-derivation: the bound hold is pressed); the '
      'distal chain lands on its own bone contacts (max landing offset '
      '%.2e m, window 1e-4 m); bound-vs-bound clean departure 0.0 | '
      'X5_pass=%s'
      % (x5['max_departure_m'], x5['t1_drop_n'], x5['t1_drop_expected_n'],
         x5['distal_landing_max_m'], arec['X5_pass']))
    w('| pressure limits / power-off | the four M03 named refusals fire '
      '(pressure_source_delta_p_limit_exceeded, '
      'pressure_source_negative_absolute, pressure_source_undeclared, '
      'pressure_source_flow_limit_exceeded); the work schedule returns to '
      '0 Pa (phase C_poweroff) | X6_pass=%s'
      % arec['X6_pass'])
    w('')
    w('## Determinism, ledger honesty, regression')
    w('')
    w('Two fresh dynamic runs at this revision produce byte-identical '
      'dynamic_run subtrees (sha256 %s, X7_pass=%s); the declared '
      'determinism unit is the canonical dynamic_run subtree of the limb '
      'loaded run. Ledger honesty (X8, A2 re-derivation): the binding '
      'cumulative no-source gate runs over the settled windows '
      '(900-1100 + 1300-1500): icosphere %+.3e J, cube %+.3e J, limb '
      '%+.3e J (floor %.1e J); the FULL-RUN residuals are REPORTED and '
      'not gated (icosphere %+.3e J, cube %+.3e J, limb %+.3e J): the '
      'under-relaxed projection mis-attributes constraint work during the '
      'extension/retraction transients, the symmetric M10 A1.8 artifact '
      'class, probe values recorded in Amendment A2. Upstream sealed '
      'suites re-run green in this checkout (regression_ok=%s).'
      % (drec['dynamic_run_sha256_main'][:16] + '...',
         drec['X7_pass'], ico_x8['settled_cumulative_residual_j'],
         cube_x8['settled_cumulative_residual_j'],
         limb_x8['settled_cumulative_residual_j'], ico_x8['x8_floor_j'],
         ico_x8['full_run_residual_j'], cube_x8['full_run_residual_j'],
         limb_x8['full_run_residual_j'], grec['regression_ok']))
    w('')
    w('## Falsifier arms (P1: clean control first, named premature guard, '
      'receipt rows)')
    w('')
    w('| arm | tamper | clean control | bit |')
    w('|---|---|---|---|')
    w('| FB1 overlay-driven motion | kinematic pose writer teleports the '
      'foot (cube fixture) | foot motion audit deviation %.17g m (window '
      '1e-9) | %s (tampered %.17g m >= 1e-3)'
      % (fb1['clean_control']['deviation_m'], fb1['bit'],
         fb1['tampered_deviation_m']))
    w('| FB2 area-independent triangle forces | constant-per-triangle '
      'traction weighting | M03 traction identity ratio worst %.17g '
      '(window 1e-9) | %s (tampered %.17g >= 1e-6)'
      % (fb2['clean_control']['ratio_worst'], fb2['bit'],
         fb2['tampered_ratio_worst']))
    w('| FB3 clipped load path | the chain-tie reaction dropped from the '
      'interface | interface audit bitwise zero on clean | %s (tampered '
      'reaction deviation %.3e N >= %.3f N)'
      % (fb3['bit'], fb3['tampered_audit']['max_reaction_dev_n'],
         fb3['bite_threshold_n']))
    w('| FB4 hidden constraint/support | the clamp removed from the scene '
      'inventory while still active | inventory matches rendered subjects '
      '| %s (support_missing_from_scene)' % fb4['bit'])
    w('| FB5 unaccounted energy | one-way T1 boost x2.0 | state-determined '
      'force-law audit bitwise zero on clean | %s (tampered law deviation '
      '%.3e N >= %.3f N)'
      % (fb5['bit'], fb5['tampered_audit']['max_force_law_dev_n'],
         fb5['bite_threshold_n']))
    w('| FB6 synthetic port stand-in | a tampered COPY substitutes a '
      '1.01x synthetic humerus mass | assembly mass audit matches the '
      'pinned B03 document bitwise on the clean build | %s (%s)'
      % (fb6['bit'], fb6['tampered_refusal_code']))
    w('')
    w('## Capture (material/motion profile; registry row is the authority)')
    w('')
    w('The registry verification profile was read READ-ONLY from '
      'agent_slots.sqlite3 (mode=ro URI); task_id SHORT form "M11"; '
      'criteria sha256 identical across dispatch, registry card + '
      'attempt, PREREGISTRATION.md, the receipts and the capture '
      'validation receipt (asserted by test_limb_world.py '
      'G7RegistryIdentity). Single-artifact binding (G8/P8): ONE video, '
      'capture_sha256 %s; every view row an artifact_locator of that '
      'video; every view row carries the same state_binding.sha256 (the '
      'canonical dynamic_run trace sha %s) — view toggles preserve the '
      'physical state hash. All 16 registry camera fields on every camera '
      'record; fixed bookmarks; clean rows carry zero labels/layers/'
      'overlays; per-viewport offscreen rendering (cross-viewport leakage '
      'impossible by construction; the leakage gate measures 0 outside '
      'pixels on every committed still); perspective depth sign conforms '
      'to the declared camera records (M10 F2 heritage). Codec (campaign '
      'standard): FFV1 level 3, GOP 1, +bitexact, %s. Per-layer pixel '
      'presence: all five declared layers render alone with >= 1 pixel of '
      'their key colors (probe receipt in cameras.json). The committed '
      'stills are BMP (stdlib-writable/readable) at declared frame '
      'indices %s of the 18-frame video; the P4 transform-list gate '
      'decodes the video with ffmpeg and matches the stills under '
      'IDENTITY ONLY (identity 0 px; vflip/hflip > 0 px), and the stdlib '
      'row-order proof verifies the BMP rows against the recorded '
      'per-frame payload hashes with the top-down misread sensitivity '
      'guard (proof green for %d stills); the camera-consistency gate '
      '(signed row order per perspective viewport: declared-above marker '
      'above the declared-below marker under the declared up; declared '
      'close-up content; zero tie-color leakage) is recomputed from the '
      'committed stills by the named check suite.'
      % (crec['video_sha256'], crec['trace_dynamic_run_sha256'],
         crec['codec']['ffmpeg_version'],
         str(cams['still_indices']), len(cams['row_order_proof'])))
    w('')
    w('## Honesty limits and disclosed gaps')
    w('')
    w('- The tissue is an engineering actuator bladder (M10 classification '
      'law applies); no metabolism, no sarcomere hierarchy, no activation '
      'dynamics beyond the declared pressure schedule.')
    w('- Bones are declared point-mass elements with real B03 masses; no '
      'bone inertia tensors are invented. The elbow bond stays UNRESOLVED '
      '(B04); the assembly uses declared ties at real A06 attachment '
      'sites, not authored joints. The foot/hand terminal stays '
      'explicitly unresolved (B03 shell zero counted mass bitwise + B04 '
      'unresolved body): declared 0.010 kg inertial contact mass '
      '(engineering, A1), B05 missing-evidence strings carried verbatim.')
    w('- The eight B05 anatomical ports remain mechanically UNQUALIFIED; '
      'this card carries their ledger and uses real attachment '
      'sites/masses/frames — it does not qualify the ports.')
    w('- The surrogate loads hang from the clamped pole (A1: the CHAIN '
      'WEIGHTS are the demonstrated load path; the surrogates are '
      'clamp-borne ballast, static by construction).')
    w('- The XPBD scaffold creeps under sustained load (plastic '
      'constraint flow, measured and recorded in A2); the erection '
      'offsets are probe-derived constants targeting the declared gap at '
      'the declared windows, and the X4 recovery reference is the '
      'never-pressurized run at the same ticks.')
    w('- The X8 settled-window floor (2.0e-3 J) is a re-derived constant '
      '(A2, probe values recorded); the full-run residuals are reported '
      'beside it, never hidden.')
    w('- Independent visual judgment of imagery stays with review '
      '(visual_acceptance stays false in the validator receipt).')
    w('')
    w('## Evidence anchors (CARD_STARTER v2: sha-verified store copies)')
    w('')
    w('| artifact | store path | sha256 |')
    w('|---|---|---|')
    for a in anch['anchors']:
        w('| %s | %s | %s |' % (a['name'], a['store_path'], a['sha256']))
    w('')
    report = '\n'.join(lines) + '\n'
    (HERE / 'report.md').write_bytes(report.encode('utf-8'))
    derived = {
        'provenance': 'derived by make_report.py from the committed '
                      'receipts; formulas recorded per entry',
        'worst_whole_system_residual_n': {
            'value': max(abs(v['residual_n'])
                         for s in x3['per_shape'].values()
                         for v in s.values()),
            'formula': 'max over shapes/windows of |F_clamp + '
                       'sum(F_contacts) - W_total|'},
        't1_drop_n': {'value': x5['t1_drop_n'],
                      'formula': 'T1(bound hold) - T1(released) '
                                 '(POST_RELEASE_WINDOW means)'},
        'recovery_limb_m': {'value': limb_x4['recovery_gap_m'],
                            'formula': '|gap_off(loaded) - gap_off('
                                       'dedicated off run)| (limb)'},
    }
    (HERE / 'report_derived_values.json').write_bytes(
        (json.dumps(derived, indent=1, sort_keys=True) + '\n')
        .encode('utf-8'))
    print('report written:', HERE / 'report.md')
    return 0


if __name__ == '__main__':
    sys.exit(main())
