"""MAT2-M07 capture manifest builder: assembles the video from the rendered
frames, builds the chimera.visual_capture_manifest.v1 manifest + context
(task_id SHORT form "M07") and validates them with the registry validator,
using the REGISTRY profile object read READ-ONLY from
E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3
kanban.cards[MAT2-M07].spec.ontology_qualification.task.verification_profile.

Every hash is derived from the files on disk (no hand-typed values).
Single-artifact binding: ONE video file; capture_sha256 = that file's sha256;
every view row is an artifact_locator of kind video on it.
Run from this directory:
    python -B make_capture.py <attempt_capture_dir> <ffmpeg_path>
"""
from __future__ import annotations

import json
import pathlib
import sqlite3
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, 'E:/PythonChimera/tools/monkey_campaign')

import integrated_step as iw  # noqa: E402
from visual_capture import validate_manifest  # noqa: E402

TICK_INTERVAL = [0, iw.TICKS - 1]
FPS = 1
REGISTRY_DB = 'E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3'
TICK_MAP = ('1 tick = 1/300 s simulated, replayed at 1 video second per '
            'tick (slow motion x300)')


def registry_profile():
    """Read the verification profile object read-only from the registry."""
    con = sqlite3.connect(f'file:{REGISTRY_DB}?mode=ro', uri=True)
    try:
        payload = con.execute(
            'SELECT payload FROM state WHERE id=1').fetchone()[0]
    finally:
        con.close()
    reg = json.loads(payload)
    card = reg['kanban']['cards']['MAT2-M07']
    profile = card['spec']['ontology_qualification']['task'][
        'verification_profile']
    return profile


SUBJECTS = ['membrane_A', 'plate_A', 'ground_A', 'wall_anchor_A']
LABELS = ['membrane_A', 'plate_A', 'ground_A (pinned support)',
          'wall_anchor_A', 'port:maxwell_mount',
          'membrane_A/t0', 'membrane_A/t1', 'membrane_A/t2', 'membrane_A/t3']


def vis_diagnostic(subjects=None):
    subjects = list(SUBJECTS) if subjects is None else list(subjects)
    labels = [l for l in LABELS
              if any(l.startswith(s) or s in l for s in subjects)]
    return {'layers': list(PROFILE['diagnostic_layers']),
            'label_ids': labels,
            'selected_ids': subjects,
            'required_subject_ids': subjects,
            'observed_subject_ids': subjects,
            'missing_subject_ids': [],
            'occlusion_mode': 'depth_tested',
            'tag_bindings': [
                {'label_id': label,
                 'subject_id': ('wall_anchor_A' if 'wall' in label
                                or 'maxwell' in label else
                                'ground_A' if 'ground' in label else
                                'plate_A' if 'plate' in label else
                                'membrane_A')}
                for label in labels]}


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
    capture_dir = pathlib.Path(sys.argv[1])
    ffmpeg = sys.argv[2]
    frames_dir = capture_dir / 'frames'
    evidence_dir = capture_dir / 'evidence'
    video_path = capture_dir / 'capture' / \
        'capture_mat2_m07_integrated_20260929.mkv'
    video_path.parent.mkdir(parents=True, exist_ok=True)
    frames = sorted(frames_dir.glob('frame_*.png'))
    assert len(frames) == iw.TICKS, \
        f'expected {iw.TICKS} frames, found {len(frames)}'
    cmd = [ffmpeg, '-y', '-loglevel', 'error', '-framerate', str(FPS),
           '-i', str(frames_dir / 'frame_%02d.png'),
           '-c:v', 'ffv1', '-level', '3', '-g', '1',
           str(video_path)]
    probe = subprocess.run([ffmpeg, '-hide_banner', '-encoders'],
                           capture_output=True, text=True)
    if 'ffv1' not in probe.stdout:
        cmd = [ffmpeg, '-y', '-loglevel', 'error', '-framerate', str(FPS),
               '-i', str(frames_dir / 'frame_%02d.png'),
               '-c:v', 'libx264', '-preset', 'veryslow', '-crf', '18',
               '-pix_fmt', 'yuv420p', str(video_path)]
    subprocess.run(cmd, check=True)
    video_sha = iw.sha256_file(video_path)
    subject_sha = iw.sha256_file(HERE / 'integrated_state.json')
    trace_sha = iw.sha256_file(HERE / 'experiment_trace.json')
    run_id = 'mat2-m07-integrated-visual-20260929-' + video_sha[:8]

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
               'note': 'sha256 of contributions/MAT2-M07/'
                       'experiment_trace.json: the per-tick solver trace '
                       '(declared order digest, delta-p, plate/Maxwell '
                       'state, contact records with converged-pass '
                       'impulses, per-tick energy ledger with measured '
                       'residual and recorded projection exchange, '
                       'boundary reactions, per-tick state hash rendered '
                       'in every frame footer); rendered positions are the '
                       'trace-stored vertex positions, asserted to '
                       'reproduce the trace volume before any pixel is '
                       'written'}

    def view(pair_id, view_id, mode, camera, secondary, visibility, note):
        row = {
            'artifact_locator': {'kind': 'video',
                                 'seconds': [0, iw.TICKS]},
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
        view('pair-whole', PROFILE['views'][0], 'diagnostic',
             cam_whole, None, vis_diagnostic(),
             'single viewport (sheet column 1); fixed camera; the membrane '
             'pressurizes, presses the loose plate, both slide, then the '
             'pressure relaxes and the Maxwell mount pulls the plate back'),
        view('pair-whole', PROFILE['views'][0], 'clean', cam_whole, None,
             vis_clean(),
             'clean row: identical camera and state to its diagnostic pair; '
             'no labels, layers or diagnostic styling by design'),
        view('pair-planes', PROFILE['views'][1], 'diagnostic', cam_side,
             [cam_front], vis_diagnostic(),
             'two side-by-side viewports (sheet columns 2-3): side (primary '
             'camera) and front (secondary, fully declared with the same 16 '
             'camera fields); the pinned ground support and the wall anchor '
             'are rendered and labeled (nothing hidden)'),
        view('pair-planes', PROFILE['views'][1], 'clean', cam_side,
             [cam_front], vis_clean(),
             'clean row: identical cameras and state to its diagnostic pair'),
        view('pair-interface', PROFILE['views'][2], 'diagnostic', cam_iface,
             None, vis_diagnostic(['membrane_A', 'plate_A',
                                   'wall_anchor_A']),
             'single viewport (sheet column 4); oblique close-up of the '
             'loaded interface: membrane-plate contact patch markers and '
             'area-scaled pressure traction arrows; the Maxwell mount force '
             'arrow grows with the recorded element force'),
        view('pair-interface', PROFILE['views'][2], 'clean', cam_iface, None,
             vis_clean(),
             'clean row: identical camera and state to its diagnostic pair'),
    ]

    manifest = {
        'schema': 'chimera.visual_capture_manifest.v1',
        'task_id': 'M07',
        'profile_id': PROFILE['id'],
        'run_id': run_id,
        'tick_interval': TICK_INTERVAL,
        'subject_sha256': subject_sha,
        'capture_sha256': video_sha,
        'sheet_layout': {
            'pixel_size': [2560, 840],
            'honest_titles': 'rendered inside every viewport: view_id, mode, '
                             'tick and delta-p; every diagnostic viewport '
                             'carries the layer row, the state line (plate '
                             'x, Maxwell F, active contacts, cumulative Q) '
                             'and the port/state hash; footer carries '
                             'frame_id, the tick-to-seconds mapping and the '
                             'state hash',
            'rows': [
                'top    diagnostic viewports [whole | side | front | '
                'close-up] with all five declared diagnostic layers',
                'middle clean viewports (identical cameras, no labels, no '
                'overlays, depth-tested)',
                'bottom delta-p / plate displacement / cumulative work '
                'traces + footer',
            ],
            'tick_to_seconds_map': TICK_MAP + '; frame t = tick t',
            'frame_files': frame_hashes,
        },
        'views': views,
    }
    context = {
        'task_id': 'M07',
        'run_id': run_id,
        'subject_sha256': subject_sha,
        'capture_sha256': video_sha,
        'tick_interval': TICK_INTERVAL,
    }
    receipt = validate_manifest(manifest, context, PROFILE)
    receipt['video_path'] = str(video_path)
    receipt['video_sha256'] = video_sha
    receipt['subject_path'] = 'tools/monkey_campaign/contributions/MAT2-M07/' \
                              'integrated_state.json'
    receipt['subject_sha256'] = subject_sha
    receipt['trace_path'] = 'tools/monkey_campaign/contributions/MAT2-M07/' \
                            'experiment_trace.json'
    receipt['trace_sha256'] = trace_sha
    receipt['frame_count'] = len(frame_hashes)
    receipt['validator'] = 'tools/monkey_campaign/visual_capture.py ' \
                           'validate_manifest'
    receipt['profile_source'] = REGISTRY_DB + ' kanban.cards[MAT2-M07].spec' \
                              '.ontology_qualification.task' \
                              '.verification_profile (read read-only)'
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
          '| views:', receipt['view_count'])
    return 0


PROFILE = registry_profile()

if __name__ == '__main__':
    sys.exit(main())
