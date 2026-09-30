"""MAT2-M08 capture manifest builder: assembles the video from the rendered
frames, builds the chimera.visual_capture_manifest.v1 manifest + context
(task_id SHORT form "M08") and validates them with the registry validator,
using the REGISTRY profile object read READ-ONLY from
E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3
kanban.cards[MAT2-M08].spec.ontology_qualification.task.verification_profile.

Every hash is derived from the files on disk (no hand-typed values).
Single-artifact binding: ONE video file; capture_sha256 = that file's
sha256; every view row is an artifact_locator of kind video on it.
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
CONTRIB = HERE.parent
sys.path.insert(0, str(HERE))
for _p in (str(CONTRIB / 'MAT2-M03'), str(CONTRIB / 'MAT2-M07')):
    if _p not in sys.path:
        sys.path.insert(0, _p)
sys.path.insert(0, 'E:/PythonChimera/tools/monkey_campaign')

import integrated_step as iw  # noqa: E402
from visual_capture import validate_manifest  # noqa: E402

FPS = 1
REGISTRY_DB = 'E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3'
SNAP_TICKS = [0, 10, 20, 30, 40, 50, 60, 70, 79]
TICK_MAP = ('1 tick = 1/300 s simulated; frames are the declared GPU '
            'snapshot ticks 0,10,..,70,79 at 1 video second per frame; '
            'the steady-state stepping itself never leaves the device '
            '(telemetry <= 1024 B/component/tick, commands <= 256 B/tick)')


def registry_profile():
    con = sqlite3.connect(f'file:{REGISTRY_DB}?mode=ro', uri=True)
    try:
        payload = con.execute(
            'SELECT payload FROM state WHERE id=1').fetchone()[0]
    finally:
        con.close()
    reg = json.loads(payload)
    card = reg['kanban']['cards']['MAT2-M08']
    profile = card['spec']['ontology_qualification']['task'][
        'verification_profile']
    return profile


SUBJECTS = ['membrane_A', 'plate_A', 'ground_A', 'wall_anchor_A']
LABELS = ['membrane_A', 'plate_A', 'ground_A (pinned support)',
          'wall_anchor_A', 'port:maxwell_mount',
          'membrane_A/m:t0', 'membrane_A/m:t1', 'membrane_A/m:t2',
          'membrane_A/m:t3']


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
        'capture_mat2_m08_resident_20260929.mkv'
    video_path.parent.mkdir(parents=True, exist_ok=True)
    frames = sorted(frames_dir.glob('frame_*.png'))
    assert len(frames) == len(SNAP_TICKS), \
        f'expected {len(SNAP_TICKS)} frames, found {len(frames)}'
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
    receipt_gpu = json.loads((HERE / 'experiment_receipt.json').read_text(
        encoding='utf-8'))
    subject_sha = iw.sha256_file(HERE / 'experiment_receipt.json')
    trace_sha = iw.sha256_file(HERE / 'experiment_trace.json')
    run_id = 'mat2-m08-resident-visual-20260929-' + video_sha[:8]

    cams = json.loads((evidence_dir / 'cameras.json').read_text('utf-8'))
    frame_hashes = json.loads(
        (evidence_dir / 'frame_hashes.json').read_text('utf-8'))
    cam_whole = cams['whole:diagnostic'][0]
    cam_side = cams['side:diagnostic'][0]
    cam_front = cams['front:diagnostic'][0]
    cam_iface = cams['closeup:diagnostic'][0]
    assert cam_whole == cams['whole:clean'][0]
    assert cam_side == cams['side:clean'][0]
    assert cam_front == cams['front:clean'][0]
    assert cam_iface == cams['closeup:clean'][0]

    binding = {'kind': 'trace', 'sha256': trace_sha,
               'note': 'sha256 of contributions/MAT2-M08/'
                       'experiment_trace.json: the per-tick GPU-vs-oracle '
                       'comparison trace of the resident-GPU run (declared '
                       'order digest, telemetry byte budgets per tick, '
                       'agreement windows); rendered positions are the '
                       'GPU-SOLVED snapshot vertex arrays recorded in '
                       'experiment_receipt.json (sha256 ' +
                       receipt_gpu.get('subject_sha', 'in-run') + '), '
                       'asserted to reproduce the snapshot own diagnostic '
                       'volume before any pixel is written'}

    def view(pair_id, view_id, mode, camera, secondary, visibility, note):
        row = {
            'artifact_locator': {'kind': 'video',
                                 'seconds': [0, len(SNAP_TICKS)]},
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
             'single viewport (sheet column 1); fixed camera; the '
             'GPU-solved membrane pressurizes, presses the loose plate, '
             'both slide, then the pressure relaxes and the Maxwell mount '
             'pulls the plate back; residency evidence in the footer'),
        view('pair-whole', PROFILE['views'][0], 'clean', cam_whole, None,
             vis_clean(),
             'clean row: identical camera and state to its diagnostic pair; '
             'no labels, layers or diagnostic styling by design; the '
             'declared gray caption inside the cell is the only text '
             '(Amendment A5: caption rendered inside its viewport)'),
        view('pair-planes', PROFILE['views'][1], 'diagnostic', cam_side,
             [cam_front], vis_diagnostic(),
             'two side-by-side viewports (sheet columns 2-3): side (primary '
             'camera) and front (secondary, fully declared with the same 16 '
             'camera fields); the pinned ground support and the wall anchor '
             'are rendered and labeled (nothing hidden)'),
        view('pair-planes', PROFILE['views'][1], 'clean', cam_side,
             [cam_front], vis_clean(),
             'clean row: identical cameras and state to its diagnostic '
             'pair; geometry only - the declared gray caption inside the '
             'cell is its only text (Amendment A5: caption rendered '
             'inside its viewport)'),
        view('pair-interface', PROFILE['views'][2], 'diagnostic', cam_iface,
             None, vis_diagnostic(['membrane_A', 'plate_A',
                                   'wall_anchor_A']),
             'single viewport (sheet column 4); oblique close-up of the '
             'loaded interface: membrane-plate contact state and '
             'area-scaled pressure traction arrows computed on the CURRENT '
             'GPU-solved geometry; layer-1 navy membrane-triangle and port '
             'ID labels rendered topmost'),
        view('pair-interface', PROFILE['views'][2], 'clean', cam_iface, None,
             vis_clean(),
             'clean row: identical camera and state to its diagnostic '
             'pair; geometry only - the declared gray caption inside the '
             'cell is its only text (Amendment A5: caption rendered '
             'inside its viewport)'),
    ]

    manifest = {
        'schema': 'chimera.visual_capture_manifest.v1',
        'task_id': 'M08',
        'profile_id': PROFILE['id'],
        'run_id': run_id,
        'tick_interval': [SNAP_TICKS[0], SNAP_TICKS[-1]],
        'subject_sha256': subject_sha,
        'capture_sha256': video_sha,
        'sheet_layout': {
            'pixel_size': [2560, 840],
            'honest_titles': 'rendered inside every viewport: diagnostic '
                             'viewports carry the view name and tick; clean '
                             'viewports carry the declared gray clean '
                             'caption inside the cell (Amendment A5); '
                             'diagnostic viewports carry the five declared '
                             'diagnostic layers, layer 1 (membrane/'
                             'triangle/port IDs) rendered as navy m:t and '
                             'port:maxwell_mount labels topmost of every '
                             'diagnostic viewport (Amendment A5: rendered, '
                             'not only declared); footer carries the GPU '
                             'contact pair-event count (substep sum), the '
                             'end-state display contact-triangle count, '
                             'the measured residual and the steady-state '
                             'telemetry cap',
            'rows': [
                'top    diagnostic viewports [whole | side | front | '
                'close-up] with all five declared diagnostic layers',
                'middle clean viewports (identical cameras; geometry only; '
                'the declared gray caption inside the cell is their only '
                'text; depth-tested)',
                'bottom per-lane delta-p / plate x / cumulative work traces '
                '(one lane per series) over the declared GPU snapshot '
                'ticks + footer',
            ],
            'tick_to_seconds_map': TICK_MAP + '; frame t = snapshot tick t',
            'frame_files': frame_hashes,
        },
        'views': views,
    }
    context = {
        'task_id': 'M08',
        'run_id': run_id,
        'subject_sha256': subject_sha,
        'capture_sha256': video_sha,
        'tick_interval': [SNAP_TICKS[0], SNAP_TICKS[-1]],
    }
    receipt = validate_manifest(manifest, context, PROFILE)
    receipt['video_path'] = str(video_path)
    receipt['video_sha256'] = video_sha
    receipt['subject_path'] = 'tools/monkey_campaign/contributions/' \
                              'MAT2-M08/experiment_receipt.json'
    receipt['subject_sha256'] = subject_sha
    receipt['trace_path'] = 'tools/monkey_campaign/contributions/' \
                            'MAT2-M08/experiment_trace.json'
    receipt['trace_sha256'] = trace_sha
    receipt['frame_count'] = len(frame_hashes)
    receipt['render_source'] = 'GPU-solved snapshot stream (9 declared ' \
                               'async capture ticks) of the resident GPU ' \
                               'world; software rasterization of solver ' \
                               'state, declared in the applicability ' \
                               'boundary'
    receipt['validator'] = 'tools/monkey_campaign/visual_capture.py ' \
                           'validate_manifest'
    receipt['profile_source'] = REGISTRY_DB + ' kanban.cards[MAT2-M08].spec' \
                              '.ontology_qualification.task' \
                              '.verification_profile (read read-only)'
    receipt['limits'] = 'Structural camera-metadata validation only; ' \
                        'independent image/physics review remains mandatory.'

    for target, payload in (
            (evidence_dir / 'capture_manifest.json', manifest),
            (evidence_dir / 'capture_context.json', context),
            (evidence_dir / 'validation_receipt.json', receipt)):
        # A5 F7: the card's committed copies of these artifacts live under
        # capture/ in this directory; the loose duplicates the committed
        # original also wrote at the contribution root are gone (attempt
        # scratch, byte-identical duplicates of the committed evidence)
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
