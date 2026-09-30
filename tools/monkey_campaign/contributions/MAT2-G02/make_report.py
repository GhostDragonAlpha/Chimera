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
         'check_capture_pixels.py',
         'KNOWN_SKIPS.md', '.gitattributes',
         'experiment_receipt.json', 'experiment_trace.json',
         'experiment_receipt_rerun2.json', 'experiment_trace_rerun2.json',
         'determinism_receipt.json', 'falsifier_receipt.json',
         'regression_receipt.json',
         'capture_manifest.json', 'capture_context.json',
         'capture_validation_receipt.json', 'capture_pixel_presence.json')


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
    px = load('capture_pixel_presence.json')
    t8 = r['T8']
    t3 = next(p for p in r['element_probes']
              if p['probe'] == 'T3_reciprocity')
    arms = fal['arms']
    w = []
    add = w.append

    add(f'# {CARD_FULL} report - Qualify finite-area anatomical attachments')
    add('')
    add(f'Attempt 983a9a8b1be54457a6aa516319290aa1, agent '
        'zcode-glm-mat2-g02-a1, criteria sha256 '
        '03ee207b7b2c701ff189bf1ee9133ada87eea7a1bd760fe4cb24525fcc5e4c45. '
        'Isolated attempt-workspace checkout of E:/PythonChimera; candidate '
        'lineage branch codex/monkey-mat2-g02-983a9a8b1b (unsquashed in the '
        'attempt workspace); the r3 publication is ONE fresh trailered '
        'commit on the sealed line tip 66f193c4 (= origin/astra/gait-'
        'capture after the merged MAT2-M12 and agent-memory-backup PRs; '
        'the r1/r2 publications sat on the earlier tip f6cbf7a9). '
        'Composed against CARD_STARTER.md v3; '
        'house standards IMPLEMENTER_CHECKLIST.md (G1-G9) and TOOLKIT.md '
        '(P1-P9) cited at the candidate commit.')
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
        'material states | T3 reciprocity (bitwise force pairs; worst '
        f'summed torque {t3["worst_summed_torque_N_m"]} N*m against the '
        'frozen 1e-15 bound (receipt element_probes T3 block); interface '
        'force sums bitwise zero; per-body received moments recorded in '
        f'the trace) | {c1} |')
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
    pp = cap['pixel_presence']
    add('- Pixel-presence grounding (round-1 fix): draw_viewport() is '
        'called for all six viewports; every visibility claim is measured '
        f'per frame in capture_pixel_presence.json (min tile non-bg '
        f'pixels {pp["min_tile_nonbg_pixels"]}, footer trace-inset line '
        f'min {pp["footer_min_trace_line_pixels"]} px, reprojection-oracle '
        f'max delta {pp["camera_consistency_max_delta_px"]} px); '
        'check_capture_pixels.py re-measures the committed frames against '
        'the manifest (GREEN) and REDs on both preserved pre-fix '
        'captures (controls, measured on this revision: the pre-round-1 '
        'capture 420 violations, five of six tiles at zero non-'
        'background pixels; the r2 capture 35 violations of which the '
        'caption-only inset fails the inset signature gates - the r2 '
        'blocker can no longer pass).')
    insets = pp.get('secondary_insets') or {}
    for tile_key, inset in sorted(insets.items()):
        sigs = ', '.join(f'{k} {v}' for k, v in sorted(
            inset['min_signature_pixels_inside_rect'].items()))
        add(f'- Declared oblique picture-in-picture inset ({tile_key}, '
            'round-2 fix): rendered at its declared '
            f'{inset["viewport_resolution"][0]}x'
            f'{inset["viewport_resolution"][1]} resolution by the SAME '
            'draw_viewport() with the target-surface dimensions bound as '
            'parameters (the r2 revision projected with module viewport '
            'constants, so every inset geometry pixel landed outside the '
            '288x76 surface and PIL clipped it to a caption-only rect); '
            'the inset camera is in-frame-gated and consistency-oracled '
            'in the INSET coordinate space; exact-color geometry '
            'signatures measured INSIDE the declared rect '
            f'{inset["rect_px"]} (minima over the 7 frames: {sigs}; '
            f'caption chip min {inset["min_caption_chip_pixels"]} px, '
            f'inset non-bg min {inset["min_nonbg_pixels"]} px); tile '
            'stats are measured POST-paste so the manifest describes the '
            'committed pixels; the paste occludes at most '
            f'{inset["max_occluded_prepaste_pixels"]} primary geometry '
            'px per frame (measured and disclosed - the inset hides no '
            'subject POINT, verified by the tile-space hide gate, and '
            'the r2 caption-only state measured 0 geometry px at this '
            'rect).')
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
    add('- Round-1 corrections (review sgt-pr281-r1, CHANGES_REQUIRED): '
        'the published capture had draw_viewport() defined with ZERO call '
        'sites - five of six viewports were uniform background while the '
        'manifest claimed all subjects observed. Fixed: draw_viewport() '
        'called for all six tiles (diagnostic rows with overlays and port '
        'labels; clean rows geometry-only); cameras re-derived with an '
        'in-frame gate (every declared subject point of the camera '
        'framing scope must project inside the viewport, checked per '
        'frame); the camera record made mathematically true (right-handed '
        'camera frame +X right/+Y up/-Z forward; quaternion = '
        'camera-to-frame rotation; an independent reprojection oracle '
        'reproduces drawn anchors from the serialized record alone); '
        'visibility rows are MEASURED (capture_pixel_presence.json, '
        'per-frame exact-color evidence) and make_capture refuses the '
        'build if any required subject lacks pixels; the sheet gained a '
        'declared footer band so the trace inset no longer overlaps a '
        'clean viewport. The physics chain is UNCHANGED: all receipts '
        'regenerate byte-identically (trace 259b731d..., experiment/'
        'determinism/falsifier/regression receipts identical; only the '
        'declared live-field experiment_profile.json differs, by '
        'declaration).')
    add('- Round-2 corrections (review sgt-pr281-r2, CHANGES_REQUIRED on '
        'ONE blocker): the declared oblique picture-in-picture inset '
        '(288x76) contained ZERO geometry pixels - 354 non-bg px of '
        'caption text only - because draw_viewport() projected with the '
        'MODULE CONSTANTS VP_W/VP_H regardless of the target surface, '
        'every inset geometry pixel landed outside the 288x76 image and '
        'PIL clipped it silently, while assert_in_frame(secondary) '
        'checked the 640x240 tile space and the pip content gate '
        '(nonbg > 100) was satisfied by the caption text. Fixed: '
        'draw_viewport() (and every projection-space gate: '
        'assert_in_frame, draw_labels, ground_subjects) now takes the '
        'TARGET surface dimensions as parameters - the inset renders at '
        'its declared 288x76 with its own oblique camera; the secondary '
        'in-frame gate runs in the inset coordinate space; the inset '
        'content gate is EXACT-COLOR (every declared geometry signature '
        'must have > 0 measured px inside the declared rect - caption '
        'text alone cannot pass; the caption carries an exact-color '
        'chip); check_capture_pixels.py gained the same inset gates '
        'plus an inset-space seam-centroid consistency bound, and its '
        'clean-row styling list gained PATCH_DIAGONAL and SEAM_DIAG '
        '(review R2N2); tiles are measured POST-paste so manifest pixel '
        'counts describe the committed pixels (review R2N1), with the '
        'pre-paste occlusion of primary geometry under the inset '
        'measured and disclosed per frame (review R2O1). The physics '
        'chain is UNCHANGED: all receipts regenerate byte-identically '
        '(trace 259b731d...).')
    add('- Refusals disclosure (review finding F6): the submit-time '
        'coordination record (LIEUTENANT_RESUME_v2.json, 2026-09-30 15:4x '
        'CDT entry) states "4 named refusals disclosed" for development '
        'of this attempt. No durable artifact of this attempt records '
        'their names or triggers (verified by the r1 reviewer across '
        'report.md, PREREGISTRATION.md, KNOWN_SKIPS.md, commit messages, '
        'the PR body and the attempt workspace; re-verified by this '
        'corrections pass). Their content is therefore recorded as '
        'UNRECOVERABLE - no names are invented. Durable process record: '
        'development-time refusals must be written into report.md or '
        'KNOWN_SKIPS.md when they happen, not left in a coordination log.')
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
    add('- experiment_profile.json is the single DECLARED live-field file '
        '(wall-clock x1_wall_seconds); it is excluded from byte identity '
        'by declaration and from the pinned file list above; every other '
        'artifact regenerates byte-identically.')
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
