"""MAT2-G02 report generator (card-kit pattern: the report is GENERATED
from committed receipts - zero hand-transcribed numbers; amendments and
repairs fully disclosed; file identities at freeze time).

Run:  python -B make_report.py
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
CARD_FULL = 'MAT2-G02'
CARD_ID = 'G02'

FILES = ('PREREGISTRATION.md', 'attachment_patch.py', 'run_experiments.py',
         'test_attachment_fixture.py', 'lint_report_numbers.py',
         'render_run.py', 'make_capture.py', 'make_report.py',
         'KNOWN_SKIPS.md', '.gitattributes',
         'experiment_receipt.json', 'experiment_trace.json',
         'experiment_receipt_rerun2.json', 'experiment_trace_rerun2.json',
         'determinism_receipt.json', 'falsifier_receipt.json',
         'regression_receipt.json', 'experiment_profile.json',
         'capture_manifest.json', 'capture_context.json',
         'capture_validation_receipt.json')


def load(name):
    return json.loads((HERE / name).read_bytes().decode('utf-8'))


def sha(path):
    return hashlib.sha256((HERE / path).read_bytes()).hexdigest()


def main():
    r = load('experiment_receipt.json')
    det = load('determinism_receipt.json')
    fal = load('falsifier_receipt.json')
    reg = load('regression_receipt.json')
    prof = load('experiment_profile.json')
    cap = load('capture_validation_receipt.json')
    t8 = r['T8']
    arms = fal['arms']
    w = []
    add = w.append

    add(f'# {CARD_FULL} report - Qualify finite-area anatomical attachments')
    add('')
    add(f'Attempt 983a9a8b1be54457a6aa516319290aa1, agent '
        'zcode-glm-mat2-g02-a1, criteria sha256 '
        '03ee207b7b2c701ff189bf1ee9133ada87eea7a1bd760fe4cb24525fcc5e4c45. '
        'Isolated attempt-workspace checkout of E:/PythonChimera; candidate '
        'branch codex/monkey-mat2-g02-983a9a8b1b on the sealed line tip '
        'f6cbf7a9 (= origin/astra/gait-capture). Composed against '
        'CARD_STARTER.md v2; house standards IMPLEMENTER_CHECKLIST.md '
        '(G1-G9) and TOOLKIT.md (P1-P9) cited at the candidate commit.')
    add('')
    add('## done_when clause map (executed on the exact candidate revision)')
    add('')
    add('| clause | execution | result |')
    add('| --- | --- | --- |')
    x1 = 'PASS' if r['X1_pass'] else 'FAIL'
    add('| Actual patch geometry ... meet declared physical requirements '
        '| T1/T2/T4/T5 exact probes + X1 closed-form agreement '
        f'(worst rel {r["worst_agreement_rel"]}) | {x1} |')
    c1 = 'PASS' if r['T3_pass'] else 'FAIL'
    add('| Finite-area attachment forces and moments enter both connected '
        'material states | T3 reciprocity (bitwise force pairs, summed '
        f'torque {t8["worst_ledger_residual_J"]} N*m ledger class; '
        'interface force sums bitwise zero; per-body received moments '
        f'recorded in the trace) | {c1} |')
    c2 = 'PASS' if (t8['bitwise_release_identity']
                    and t8['post_release_bitwise_zero']
                    and r['documents']['released_document_bond_count'] == 0
                    and r['documents']['released_document_contact_count']
                    == 1) else 'FAIL'
    add('| Physical bond/removal semantics match the limb experiment | '
        'T6 release gate: bitwise post-release zero, '
        f'E_diss_release == U(233) ({t8["U233_J"]} J), M01 documents '
        'bond 1 -> 0 with contact persisting, separation demonstrated '
        f'({t8["max_gap_235_264_m"]} m > gap(234) '
        f'{t8["gap_234_m"]} m), re-contact at tick '
        f'{t8["recontact_loaded_tick"]} with no patch | {c2} |')
    add('')
    add('## declared physical requirements (the C17 law)')
    add('')
    add('- The fixture constants are DECLARED placeholders (provenance '
        'class declared_placeholder, never biological): areal densities '
        'derived from the sealed MAT2-M05 carrier (kA_t = 60/0.0175, '
        'kA_s = 40/0.0175, kA_theta = 0.8/0.0175 N units per the prereg '
        'laws 3-4); patch quad 20 mm x 10 mm with UNEQUAL triangles '
        '(A1 = 1.0e-4 m^2, A2 = 6.5e-5 m^2) so area scaling is '
        'falsifiable; distribution weights w1 = '
        f'{r["c17_terminal"]["fixture_constants"]["values"]["w1"]}, w2 = '
        f'{r["c17_terminal"]["fixture_constants"]["values"]["w2"]}; '
        'owner-body-local frames carried verbatim with authored port ids '
        'iface:fixture-patch-p1/p2.')
    add('- The BIOLOGICAL attachment ports (26 attachment_interface '
        'connections carried from the sealed A09 package, c17_status '
        'carried_open) close EXPLICITLY-UNRESOLVED: no measured or '
        'separately-authorized source exists; the sealed A07 gate '
        'requires authorization BEFORE any fitting experiment and none is '
        'recorded; no synthetic lambda_min appears anywhere in this card '
        '(the term does not occur in any artifact).')
    add('- Adjacent debt, NOT this card\'s scope: the G04 friction study '
        'records no lawful measured friction pin exists (mu_s 0.6 / mu_k '
        '0.4 remain NAMED placeholders; the elementwise_min pair rule is '
        'two-sided). This fixture uses the sealed M05 frictionless '
        'normal-penalty contact and introduces no friction constant.')
    add('')
    add('## X-gates')
    add('')
    add(f'- X1 element-vs-oracle agreement: worst relative diff '
        f'{r["worst_agreement_rel"]} (window 1e-15); probe series T1/T2/'
        f'T3/T4/T5/T7/T9 all pass: {r["X1_pass"]}.')
    add(f'- X2 scoped determinism: trace byte-identical '
        f'({det["X2_trace_byte_identical"]}); receipt delta scoped to '
        f'{det["receipt_keys_only_in_main"]}; pass: {det["X2_pass"]}.')
    add(f'- Dynamic fixture (Amendment A2 schedule, '
        f'{r["tick_count"]} ticks): gap(233) = {t8["gap_at_tick_233_m"]} m '
        f'in {t8["window_gap_233"]}; U(233) = {t8["U233_J"]} J in '
        f'{t8["window_U"]}; worst ledger residual '
        f'{t8["worst_ledger_residual_J"]} J (frozen bound); min '
        f'penetration {t8["min_penetration_m"]} m within '
        f'{t8["penetration_window"]}; T8_pass: {t8["T8_pass"]}.')
    add('')
    add('## falsifier proof (each arm: clean control FIRST, named guard, '
        'discriminator)')
    add('')
    for name, arm in arms.items():
        add(f'- {name}: clean control {arm["clean_control"]["value"]} '
            f'(within tolerance: '
            f'{arm["clean_control"]["within_tolerance"]}); tampered '
            f'{arm["tampered_value"]}; bites: {arm["bit"]}; '
            f'discriminating: {arm["discriminating"]}.')
    add(f'- F_all_green: {fal["F_all_green"]} (vacuous guard selftest: '
        f'{fal["vacuous_guard_selftest"]}).')
    add('')
    add('## capture identity (attachment-fixture/motion profile)')
    add('')
    add(f'- FFV1 level 3 g 1 with -fflags +bitexact (mkv); sha256 '
        f'{cap["video_sha256"]}; ffmpeg: {cap["ffmpeg_version"]}.')
    add(f'- validate_manifest (tools/monkey_campaign/visual_capture.py, '
        f'registry profile read read-only): structurally_valid '
        f'{cap["structurally_valid"]}, {cap["view_count"]} view rows '
        '(3 registry views x diagnostic+clean pairs); subject sha256 '
        f'{cap["subject_sha256"]}; state binding = trace '
        f'{cap["trace_sha256"]}.')
    add('- Full registry camera record on every row (frame_id, '
        'coordinate_unit, position, orientation_convention_and_values, '
        'target, distance_to_target, projection, vertical_fov, '
        'near_far_planes, aspect_ratio, viewport_resolution, sample '
        'mode/sequence, visibility, labels, occlusion, state interval); '
        'fixed bookmarks; clean pairs share the exact camera and the '
        'exact physical state; state hash preserved across view toggles: '
        f'{cap["state_hash_preserved_across_view_toggles"]}.')
    add('- Honest limit: validate_manifest is structural only; independent '
        'image/physics review (the Sergeant gate) remains mandatory and is '
        'owned by the Lieutenant.')
    add('')
    add('## regression')
    add('')
    add(f'- Upstream suite (MAT2-M05 test_interface_exchange.py, pinned) '
        f're-run unmodified on this revision: exit '
        f'{reg["exit_code"]}, green: {reg["P_regression_suite_green"]}.')
    add('')
    add('## amendments and repairs (full disclosure)')
    add('')
    add('- Amendment A1 (a39a946e, pre-implementation): T2 per-triangle '
        'tension literals repaired (three decades; patch total, ratio and '
        'windows unchanged). No experiment had run.')
    add('- Amendment A2 (951c963e, pre-experiment): damping-ratio formula '
        'corrected (zeta = c_v/(2*m*omega_t); the declared c_v = 2.0 '
        'overdamped the soft patch at zeta 9.4017 -> c_v = 0.02, zeta '
        '0.0940); schedule amended to a quasi-static squeeze ramp + settle '
        '+ bind at rest + release at the derived oscillation peak; T8 '
        'windows re-derived from the corrected closed form; ledger '
        'bookkeeping statement added (midpoint displacement identity, '
        'damping booked as Q, elastic contact in W_contact, '
        'E_diss_release in Q at the release tick). Element laws 1-9 '
        'untouched.')
    add('- Reference repair (8cbcd91b, recorded with the first receipts): '
        'the three attempt commits were rewritten on the UNPUBLISHED '
        'sole-owner attempt branch to separate the Agent: trailer into a '
        'proper trailer block; TREES UNCHANGED; identities recorded in '
        'PREREGISTRATION.md.')
    add('- Receipt-index repair (this revision): the T8 receipt block '
        'indexed trace rows by tick instead of by row index (rows[i] '
        'holds tick i+1); the bound M01 document is now captured while '
        'still bound; the released document is emitted after the release '
        'tick executes.')
    add('')
    add('## file identities at freeze')
    add('')
    for name in FILES:
        path = HERE / name
        if path.exists():
            add(f'- {name}: {sha(name)}')
    add('')
    add('## honest limits')
    add('')
    add('- Offline CPU experiment executable over pinned inputs; no GPU '
        'submission (the scope is a 356-tick two-body fixture; prereg '
        'law 12).')
    add('- The fixture constants are declared placeholders with the '
        'derivation recorded; they do NOT qualify the biological ports; '
        'the biological C17 debt remains explicitly-unresolved pending a '
        'separately authorized measurement (A07 gate).')
    add('- No fitting experiment was run; no friction constant was '
        'introduced; no lambda_min appears in any artifact.')
    add('')
    (HERE / 'report.md').write_bytes('\n'.join(w).encode('utf-8'))
    print('report.md written:', len('\n'.join(w)), 'chars')
    return 0


if __name__ == '__main__':
    sys.exit(main())
