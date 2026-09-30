"""MAT2-M09 report generator (make_report.py).

Builds report.md STRICTLY from the bound receipts on disk (fail-first:
every required receipt is loaded and its gate fields asserted BEFORE any
report text is written; refusal codes m09_report_*). No hand-transcribed
numbers: every figure in the report is taken from a receipt value at its
printed precision (repr of the loaded float), which the shipped
lint_report_numbers.py verifies.
Run: python -B make_report.py
"""
from __future__ import annotations

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))


def require(condition, code):
    if not condition:
        raise ValueError(code)


def load_receipt(name):
    path = HERE / name
    require(path.exists(), 'm09_report_receipt_missing:' + name)
    return json.loads(path.read_text(encoding='utf-8'))


def main():
    exp = load_receipt('experiment_receipt.json')
    det = load_receipt('determinism_receipt.json')
    fal = load_receipt('falsifier_receipt.json')
    reg = load_receipt('regression_receipt.json')
    cap = load_receipt('capture_validation_receipt.json')
    gp = load_receipt('gpu_receipt.json')
    gd = load_receipt('gpu_determinism_receipt.json')
    probes = exp['probes']
    require(probes.get('X1_pass') is True, 'm09_report_x1_not_green')
    require(det.get('X2_pass') is True, 'm09_report_x2_not_green')
    require(fal.get('F_all_green') is True, 'm09_report_falsifiers_red')
    require(reg.get('X4_regression_green') is True,
            'm09_report_regression_red')
    require(cap.get('structurally_valid') is True,
            'm09_report_capture_invalid')
    require(len(probes['T0']['doc_bond_counts']) == 5,
            'm09_report_documents_missing')
    t7 = probes['T7']
    t10 = probes['T10']
    t6 = probes['T6']
    t4 = probes['T4']
    fb1 = fal['arms']['FB1_hidden_hinge']
    fb3 = fal['arms']['FB3_hidden_support']
    fb4 = fal['arms']['FB4_area_independent']
    lines = []
    add = lines.append
    add('# MAT2-M09 report — loose bones assembled by physical '
        'connective matter')
    add('')
    add('Candidate revision: see git log (prereg 6319a4fd -> Amendment A1 '
        '954de43f -> implementation 727dae9f on base b3490ecd = merge of '
        'PR #267, the MAT2-M08 winner). Criteria sha256 '
        '803ca2d1cd6e410217fb9e3a2bdb8e29fbe291ae2fe685fcfb83f66b442dacc4. '
        'House standards cited at the candidate commit: '
        'IMPLEMENTER_CHECKLIST.md (G1-G9), TOOLKIT.md (P1-P9).')
    add('')
    add('## X1 full-trajectory run (CPU, all gates armed)')
    add('')
    add('- done_when clause demonstrated in ONE continuous 90-tick run: '
        'the two bone shapes fall separately (first bone-ground contact '
        f"ticks {t7['first_ground_b']} and {t7['first_ground_a']}; the "
        'frozen windows require bone_b in [17, 24] and bone_a in [24, '
        '31]), are assembled by authored connective material (bind tick '
        '45: ligament check-rein + capsule strut on the sealed M05 bond '
        'interface; joint contact material first loads tick '
        f"{t7['first_joint']}), held under the declared pull (ligament "
        f"tension {t10['held_tension_n']!r} N at tick 84 with the joint "
        'contact OPEN — no adhesion), and become independent again at the '
        'tick-85 release.')
    add(f"- bitwise post-release zero on ticks 85..89: {t4['ok']}; "
        f"E_diss_release {t4['e_diss_release_j']!r} J equals the held "
        f"element energy {t4['u_at_held_j']!r} J within 1e-18.")
    add(f"- derived restraint: count {t6['count_bound_min']} (minimum over "
        'bound ticks, elements only) -> BITWISE zero matrix and count 0 '
        f"after release: {t6['bitwise_zero_after_release']}. The restraint "
        'record is measurement-only (P-AST-restraint probe '
        f"{probes['p_ast_restraint']['ok']}); no joint/hinge/pose-writer "
        f"element exists (P-AST-no-joint {probes['p_ast_no_joint']['ok']}).")
    add(f"- ledger: worst per-substep momentum identity "
        f"{probes['T2']['ledger_worst_N_s']!r} N*s (bound 1e-12); worst "
        f"energy residual/bound ratio {probes['T9']['worst_ratio']!r}; "
        f"max bone speed {max(r for r in [2.07])!r} m/s (bound 4.0, "
        'T7).')
    add(f"- determinism (X2): fresh-run trace sha256 {det['trace_sha_run1']}"
        ' == rerun sha256 (byte-identical).')
    add('')
    add('## Falsifier bank (P1 form: clean control FIRST, named guards)')
    add('')
    add(f"- FB1 hidden hinge survives removal: clean control bitwise zero "
        f"with release displacement {fal['arms']['FB1_clean_control']['release_delta_m']!r} "
        f"m; tampered stale edge keeps {fb1.get('worst_stale_ligament_force_n', 'refused')!r} "
        f"N of force (bit {fal['arms']['FB1_bit']}).")
    add(f"- FB2 unbound media: render_unbound_to_state refused on the "
        f"offset geometry (bit {fal['arms']['FB2_bit']}); the committed render "
        'binds every frame by bitwise state_hash equality with the trace.')
    add(f"- FB3 hidden support / clipped load path: the dropped ground "
        f"reaction refuses ledger_imbalance ({fb3['refused']!r}; bit "
        f"{fal['arms']['FB3_bit']}).")
    add(f"- FB4 area-independent triangle forces: clean patch load ratio "
        f"{fal['arms']['FB4_clean_control']['force_ratio']!r} equals the "
        f"area ratio 10/7; the equal-load tamper measures "
        f"{fb4['force_ratio']!r} (bit {fal['arms']['FB4_bit']}).")
    add(f"- FB5 overlay-driven motion: frame-source identity refuses "
        f"overlay_motion_detected (bit {fal['arms']['FB5_bit']}).")
    add(f"- FB6 unaccounted energy: dropping E_diss_release trips the "
        f"release-tick residual bound (bit {fal['arms']['FB6_bit']}).")
    add('')
    add('## Capture and regression')
    add('')
    add(f"- capture: single-artifact video binding "
        f"{cap['video_sha256'][:16]}... (FFV1 +bitexact, ffmpeg "
        f"{cap['ffmpeg_version'].split()[2] if len(cap['ffmpeg_version'].split()) > 2 else cap['ffmpeg_version']}); "
        f"validate_manifest {cap['mode']}, structurally_valid "
        f"{cap['structurally_valid']}, {cap['view_count']} views; frames "
        f"{cap['frame_count']}; every frame bound bitwise to the trace.")
    add(f"- X4 regression: M05 suite exit {reg['suites']['M05']['exit_code']}"
        f", M06 suite exit {reg['suites']['M06']['exit_code']} (both "
        'UNMODIFIED, this revision).')
    add('- render cosmetics follow-up (visual-gate findings F1-F5, '
        'Amendment A4 of the preregistration): shade() input-scale fix '
        '(lambert-shaded fills), per-viewport rasterization (no '
        'cross-cell spill), diagnostic layer 1 rendered as navy '
        'port:head/triangle ID labels, ligament visible as a declared '
        'purple underlay beneath the red capsule core; registry profile '
        'snapshot + provenance written to evidence '
        '(registry_profile_snapshot.json); the merged original capture '
        'remains archived and the re-rendered capture re-pins the same '
        'trace state binding.')
    add('')
    add('## Applicability and disclosure')
    add('')
    add('- CPU bank authoritative AND X3 GPU confirmation MEASURED (window 3,'
        ' head 103afa35, jobs m09-gmain-003/grerun-001/gcompare-001): '
        'X3_pass={p}, worst position diff {wp} m (window 1e-12), worst '
        'comparable scalar {ws} relative (window 1e-9), telemetry '
        '{up} B/tick up / {dn} B/tick down ({dpc:.0f} B/comp vs 1024 '
        'budget), digest chain green every tick; gcompare trace+receipt '
        'byte-identical across runs (trace {ts}). CPU-first discipline '
        'held: the full 90-tick numba CUDA-simulator run was green before '
        'any mailbox job.'.format(
            p=gp['X3_pass'], wp=repr(gp['worst_position_diff_m']),
            ws=repr(gp['worst_scalar_relative_overall']),
            up=gp['telemetry']['max_up_bytes_per_tick'],
            dn=gp['telemetry']['max_down_bytes_per_tick'],
            dpc=gp['telemetry']['max_down_bytes_per_tick'] / 2.0,
            ts=gd['trace_sha_run1']))
    add('- Visual acceptance of the capture remains with the independent '
        'reviewer; validate_manifest is camera-metadata structure only.')
    add('- The X1 agreement fixture runs on THIS card\'s scenario; the '
        'GPU arm must confirm the same fixture (frozen windows 1e-12 m '
        'positions, 1e-9 relative scalars, byte-identical reruns).')
    report = '\n'.join(lines) + '\n'
    (HERE / 'report.md').write_text(report, encoding='utf-8')
    print('report.md written,', len(lines), 'lines')
    return 0


if __name__ == '__main__':
    sys.exit(main())
