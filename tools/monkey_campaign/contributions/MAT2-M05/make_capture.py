"""MAT2-M05 capture manifest builder: assembles the video from the rendered
frames, builds the chimera.visual_capture_manifest.v1 manifest + context
(task_id SHORT form "M05") and validates them with the registry validator.

The verification PROFILE is read READ-ONLY from the coordination registry
(agent_slots.sqlite3, kanban.cards.MAT2-M05 ... verification_profile) — never
hand-copied. Every hash is derived from the files on disk.
Run from this directory:
    python -B make_capture.py <attempt_capture_dir> <ffmpeg_path> \
        <registry_sqlite_path>
"""
from __future__ import annotations

import json
import pathlib
import sqlite3
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'MAT2-M01'))
sys.path.insert(0, 'E:/PythonChimera/tools/monkey_campaign')

import interface_exchange as ix  # noqa: E402
from visual_capture import validate_manifest  # noqa: E402

TICK_INTERVAL = [0, 23]
FPS = 1
DURATION_S = 24

SUBJECTS = ['body_a', 'body_b']
LABELS = ['body_a', 'body_b', 'body_a/port:seam', 'body_b/port:seam',
          'body_a/port:bond_anchor', 'body_b/port:bond_anchor',
          'bond:strap', 'support:body_a']


def registry_profile(sqlite_path):
    """Read the material/motion verification profile READ-ONLY from the
    coordination registry (never hand-copied)."""
    con = sqlite3.connect('file:' + pathlib.Path(sqlite_path).absolute()
                          .as_posix() + '?mode=ro', uri=True)
    try:
        payload = json.loads(con.execute(
            'SELECT payload FROM state WHERE id=1').fetchone()[0])
    finally:
        con.close()
    card = payload['kanban']['cards']['MAT2-M05']
    prof = card['spec']['ontology_qualification']['task']['verification_profile']
    assert prof['id'] == 'material' and prof['kind'] == 'motion'
    return prof, card.get('criteria_sha256')


def vis_diagnostic():
    return {'layers': list(PROFILE['diagnostic_layers']),
            'label_ids': list(LABELS),
            'selected_ids': list(SUBJECTS),
            'required_subject_ids': list(SUBJECTS),
            'observed_subject_ids': list(SUBJECTS),
            'missing_subject_ids': [],
            'occlusion_mode': 'depth_tested',
            'tag_bindings': [
                {'label_id': 'body_a', 'subject_id': 'body_a'},
                {'label_id': 'body_b', 'subject_id': 'body_b'},
                {'label_id': 'body_a/port:seam', 'subject_id': 'body_a'},
                {'label_id': 'body_b/port:seam', 'subject_id': 'body_b'},
                {'label_id': 'body_a/port:bond_anchor',
                 'subject_id': 'body_a'},
                {'label_id': 'body_b/port:bond_anchor',
                 'subject_id': 'body_b'},
                {'label_id': 'bond:strap', 'subject_id': 'body_b'},
                {'label_id': 'support:body_a', 'subject_id': 'body_a'}]}


def vis_clean():
    return {'layers': [],
            'label_ids': [],
            'selected_ids': [],
            'required_subject_ids': list(SUBJECTS),
            'observed_subject_ids': list(SUBJECTS),
            'missing_subject_ids': [],
            'occlusion_mode': 'depth_tested',
            'tag_bindings': []}


def main():
    global PROFILE
    capture_dir = pathlib.Path(sys.argv[1])
    ffmpeg = sys.argv[2]
    registry = sys.argv[3]
    PROFILE, registry_criteria = registry_profile(registry)
    frames_dir = capture_dir / 'frames'
    evidence_dir = capture_dir / 'evidence'
    video_path = capture_dir / 'capture' / \
        'capture_mat2_m05_interface_20260928.mkv'
    video_path.parent.mkdir(parents=True, exist_ok=True)
    frames = sorted(frames_dir.glob('frame_*.png'))
    assert len(frames) == 24, f'expected 24 frames, found {len(frames)}'
    cmd = [ffmpeg, '-y', '-loglevel', 'error', '-framerate', str(FPS),
           '-i', str(frames_dir / 'frame_%02d.png'),
           '-c:v', 'libx264', '-preset', 'veryslow', '-crf', '18',
           '-pix_fmt', 'yuv420p', str(video_path)]
    subprocess.run(cmd, check=True)
    video_sha = ix.sha256_file(video_path)
    subject_sha = ix.sha256_file(HERE / 'interface_state.json')
    trace_sha = ix.sha256_file(HERE / 'interface_trace.json')
    run_id = 'mat2-m05-interface-visual-20260928-' + video_sha[:8]

    cams = json.loads((evidence_dir / 'cameras.json').read_text('utf-8'))
    frame_hashes = json.loads(
        (evidence_dir / 'frame_hashes.json').read_text('utf-8'))
    cam_whole = cams['whole:diagnostic'][0]
    cam_side, cam_front = cams['planes:diagnostic']
    cam_iface = cams['closeup:diagnostic'][0]
    assert cam_whole == cams['whole:clean'][0]
    assert [cam_side, cam_front] == cams['planes:clean']
    assert cam_iface == cams['closeup:clean'][0]

    binding = {'kind': 'trace', 'sha256': trace_sha,
               'note': 'sha256 of contributions/MAT2-M05/interface_trace.json: '
                       'the per-tick solver trace (gap, contact state/pressure, '
                       'bond tension/status, work and dissipation ledger, '
                       'measured residual, per-tick state hash); render '
                       'positions are a replay asserted equal to the '
                       'committed trace at 1e-15 (gap/pressure/tension)'}

    def view(pair_id, view_id, mode, camera, secondary, visibility, note):
        row = {
            'artifact_locator': {'kind': 'video',
                                 'seconds': [0, DURATION_S]},
            'camera': camera,
            'cell_layout_note': note,
            'mode': mode,
            'pair_id': pair_id,
            'state_binding': binding,
            'view_id': view_id,
            'visibility': visibility,
        }
        if secondary:
            row['camera']['secondary_cameras'] = secondary
        return row

    views = [
        view('pair-whole', PROFILE['views'][0], 'diagnostic', cam_whole, None,
             vis_diagnostic(),
             'single viewport (sheet column 1); fixed camera; two supported/'
             'free pentahedra squeeze, hold by the visible bond strap, '
             'release and separate, then re-load contact with no bond'),
        view('pair-whole', PROFILE['views'][0], 'clean', cam_whole, None,
             vis_clean(),
             'clean row: identical camera and state to its diagnostic pair; '
             'no labels, layers or diagnostic styling by design'),
        view('pair-planes', PROFILE['views'][1], 'diagnostic', cam_side,
             [cam_front], vis_diagnostic(),
             'two side-by-side viewports (sheet columns 2-3): side (primary '
             'camera, left-side view: world +x projects screen-left) and '
             'front (secondary on the interface axis, seam face-on with '
             'body_b apex toward the camera), both fully declared'),
        view('pair-planes', PROFILE['views'][1], 'clean', cam_side,
             [cam_front], vis_clean(),
             'clean row: identical cameras and state to its diagnostic pair'),
        view('pair-interface', PROFILE['views'][2], 'diagnostic', cam_iface,
             None, vis_diagnostic(),
             'single viewport (sheet column 4); oblique close-up of the '
             'loaded interface: per-triangle contact arrows scale with '
             'triangle area (A=0.0100 vs A=0.0075 m^2, ratio 4/3), equal and '
             'opposite on the two bodies; the bond strap and its tension '
             'arrow vanish bitwise at the release tick'),
        view('pair-interface', PROFILE['views'][2], 'clean', cam_iface, None,
             vis_clean(),
             'clean row: identical camera and state to its diagnostic pair'),
    ]

    manifest = {
        'schema': 'chimera.visual_capture_manifest.v1',
        'task_id': 'M05',
        'profile_id': 'material',
        'run_id': run_id,
        'tick_interval': TICK_INTERVAL,
        'subject_sha256': subject_sha,
        'capture_sha256': video_sha,
        'sheet_layout': {
            'pixel_size': [2560, 840],
            'honest_titles': 'rendered inside every viewport: view_id, mode, '
                             'tick, gap, contact pressure and bond tension; '
                             'every diagnostic viewport carries the layer '
                             'row, the work/dissipation/residual lines and '
                             'the port/state line; footer carries frame_id, '
                             'the tick-to-seconds mapping and the state hash',
            'rows': [
                'top    diagnostic viewports [whole | side | front | '
                'close-up] with all five declared diagnostic layers',
                'middle clean viewports (identical cameras, no labels, no '
                'overlays, depth-tested)',
                'bottom gap / contact-force / bond-tension / energy traces + '
                'footer',
            ],
            'tick_to_seconds_map': '1 tick = 1/300 s simulated, replayed at '
                                   '1 video second per tick (slow motion '
                                   'x300); frame t = tick t',
            'frame_files': frame_hashes,
        },
        'views': views,
    }
    context = {
        'task_id': 'M05',
        'run_id': run_id,
        'subject_sha256': subject_sha,
        'capture_sha256': video_sha,
        'tick_interval': TICK_INTERVAL,
    }
    receipt = validate_manifest(manifest, context, PROFILE)
    receipt['video_path'] = str(video_path)
    receipt['video_sha256'] = video_sha
    receipt['subject_path'] = 'tools/monkey_campaign/contributions/MAT2-M05/' \
                              'interface_state.json'
    receipt['subject_sha256'] = subject_sha
    receipt['trace_path'] = 'tools/monkey_campaign/contributions/MAT2-M05/' \
                            'interface_trace.json'
    receipt['trace_sha256'] = trace_sha
    receipt['frame_count'] = len(frame_hashes)
    receipt['profile_source'] = {
        'registry': str(registry),
        'read_mode': 'sqlite3 mode=ro (read-only)',
        'card_path': 'kanban.cards.MAT2-M05.spec.ontology_qualification.task'
                     '.verification_profile',
        'profile_id': PROFILE['id'], 'kind': PROFILE['kind'],
        'registry_criteria_sha256': registry_criteria}
    receipt['validator'] = 'tools/monkey_campaign/visual_capture.py ' \
                           'validate_manifest'
    receipt['limits'] = 'Structural camera-metadata validation only; ' \
                        'independent image/physics review remains mandatory.'

    for target, payload in (
            (HERE / 'capture_manifest.json', manifest),
            (HERE / 'capture_context.json', context),
            (HERE / 'capture_validation_receipt.json', receipt),
            (evidence_dir / 'capture_manifest.json', manifest),
            (evidence_dir / 'capture_context.json', context),
            (evidence_dir / 'validation_receipt.json', receipt)):
        target.write_text(json.dumps(payload, indent=1, ensure_ascii=False,
                                     sort_keys=True) + '\n', encoding='utf-8')
    print('video:', video_path)
    print('video sha256:', video_sha)
    print('validate_manifest:', receipt['mode'],
          '| structurally_valid:', receipt['structurally_valid'],
          '| views:', receipt['view_count'],
          '| profile:', receipt['profile_id'],
          '| profile_source: registry read-only')
    return 0


if __name__ == '__main__':
    sys.exit(main())
