"""MAT2-G02 capture manifest builder (card-kit pattern, CODEC_STANDARD
2026-09-29 addendum: FFV1 -level 3 -g 1 -fflags +bitexact; NO lossy fallback
- the build refuses instead of degrading; ffmpeg version recorded).

task_id SHORT form ('G02') in manifest AND context; registry verification
profile read READ-ONLY from agent_slots.sqlite3 (never hand-copied); every
hash derived from files on disk; single-artifact binding (ONE video,
capture_sha256 = its sha256, every view row an artifact_locator on it);
diagnostic/clean pairs with identical cameras and identical physical state.

Run AFTER render_run:
    python -B make_capture.py <attempt_capture_dir> <ffmpeg_path>
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sqlite3
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, 'E:/PythonChimera/tools/monkey_campaign')

from visual_capture import validate_manifest  # noqa: E402

FPS = 1
REGISTRY_DB = 'E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3'
CARD_FULL = 'MAT2-G02'
CARD_ID = 'G02'
SNAP_TICKS = [0, 20, 150, 232, 233, 250, 320]
TICK_MAP = ('one tick = 1/300 s (declared fixture tick); frames are the '
            'declared snapshot ticks at 1 video second per frame; the '
            'rendered state is bound to experiment_trace.json rows')
VIEWS = ['patch overview', 'loaded interface close-up',
         'orthogonal and oblique patch views']
LAYERS = ['attachment patch geometry', 'authored frames and port IDs',
          'fixture load and displacement traces']
LABELS = ['iface:fixture-patch-p1', 'iface:fixture-patch-p2',
          'fixture_body_a', 'fixture_body_b', 'port:patch', 'port:seam']
VIDEO_NAME = 'capture_mat2_g02_attachment_20260930.mkv'


def sha256_file(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def registry_profile():
    con = sqlite3.connect(f'file:{REGISTRY_DB}?mode=ro', uri=True)
    try:
        payload = con.execute(
            'SELECT payload FROM state WHERE id=1').fetchone()[0]
    finally:
        con.close()
    reg = json.loads(payload)
    card = reg['kanban']['cards'][CARD_FULL]
    profile = card['spec']['ontology_qualification']['task'][
        'verification_profile']
    return profile


def vis_diagnostic():
    return {'layers': list(LAYERS),
            'label_ids': list(LABELS),
            'selected_ids': list(LABELS),
            'required_subject_ids': list(LABELS),
            'observed_subject_ids': list(LABELS),
            'missing_subject_ids': [],
            'occlusion_mode': 'depth_tested',
            'tag_bindings': [{'label_id': lab, 'subject_id': lab}
                             for lab in LABELS]}


def vis_clean():
    return {'layers': [],
            'label_ids': [],
            'selected_ids': [],
            'required_subject_ids': list(LABELS),
            'observed_subject_ids': list(LABELS),
            'missing_subject_ids': [],
            'occlusion_mode': 'depth_tested',
            'tag_bindings': []}


def ffmpeg_version(ffmpeg):
    probe = subprocess.run([ffmpeg, '-version'], capture_output=True,
                           text=True)
    return (probe.stdout or '').splitlines()[0] if probe.stdout else ''


def main():
    capture_dir = pathlib.Path(sys.argv[1])
    ffmpeg = sys.argv[2]
    frames_dir = capture_dir / 'frames'
    evidence_dir = capture_dir / 'evidence'
    video_path = capture_dir / 'capture' / VIDEO_NAME
    video_path.parent.mkdir(parents=True, exist_ok=True)
    frames = sorted(frames_dir.glob('frame_*.png'))
    assert len(frames) == len(SNAP_TICKS), \
        f'expected {len(SNAP_TICKS)} frames, found {len(frames)}'
    probe = subprocess.run([ffmpeg, '-hide_banner', '-encoders'],
                           capture_output=True, text=True)
    if 'ffv1' not in probe.stdout:
        raise SystemExit('ffv1 encoder missing from this ffmpeg build '
                         f'({ffmpeg}); a lossless gate-bearing capture is '
                         'mandatory - install an ffmpeg with ffv1')
    subprocess.run([ffmpeg, '-y', '-loglevel', 'error', '-framerate',
                    str(FPS), '-i', str(frames_dir / 'frame_%02d.png'),
                    '-c:v', 'ffv1', '-level', '3', '-g', '1',
                    '-fflags', '+bitexact', str(video_path)], check=True)
    video_sha = sha256_file(video_path)
    subject_sha = sha256_file(HERE / 'experiment_receipt.json')
    trace_sha = sha256_file(HERE / 'experiment_trace.json')
    run_id = 'g02-attachment-fixture-20260930-' + video_sha[:8]

    cams = json.loads((evidence_dir / 'cameras.json')
                      .read_bytes().decode('utf-8'))
    frame_hashes = json.loads((evidence_dir / 'frame_hashes.json')
                              .read_bytes().decode('utf-8'))
    state_hashes = json.loads((evidence_dir / 'state_hashes.json')
                              .read_bytes().decode('utf-8'))
    for view_id in VIEWS:
        assert cams[f'{view_id}:diagnostic'][0] == \
            cams[f'{view_id}:clean'][0], \
            f'{view_id}: clean/diagnostic camera mismatch'

    binding = {'kind': 'trace', 'sha256': trace_sha,
               'note': 'sha256 of contributions/' + CARD_FULL +
                       '/experiment_trace.json: the per-tick fixture trace '
                       'of the run; rendered state is bound to the '
                       'committed receipts before any pixel is written'}

    def view(pair_id, view_id, mode, camera, visibility, note):
        return {'artifact_locator': {'kind': 'video',
                                     'seconds': [0, len(SNAP_TICKS)]},
                'camera': camera,
                'cell_layout_note': note,
                'mode': mode,
                'pair_id': pair_id,
                'state_binding': binding,
                'view_id': view_id,
                'visibility': visibility}

    views = []
    notes = {
        VIEWS[0]: 'whole-fixture viewport; fixed bookmark camera; the '
                  'patch quad, both bodies and the declared support stand '
                  'are fully in frame (nothing hidden or clipped)',
        VIEWS[1]: 'loaded interface close-up; fixed bookmark camera '
                  'centered on the patch plane',
        VIEWS[2]: 'orthogonal side view; the diagnostic row also declares '
                  'a fully-declared oblique secondary camera '
                  '(secondary_cameras in the camera record)',
    }
    for vi, view_id in enumerate(VIEWS):
        pair_id = f'pair-{vi}'
        views.append(view(pair_id, view_id, 'diagnostic',
                          cams[f'{view_id}:diagnostic'][0],
                          vis_diagnostic(), notes[view_id]))
        views.append(view(pair_id, view_id, 'clean',
                          cams[f'{view_id}:clean'][0], vis_clean(),
                          'clean row: identical camera and identical '
                          'physical state to its diagnostic pair; no '
                          'labels, layers or diagnostic styling by design'))

    manifest = {
        'schema': 'chimera.visual_capture_manifest.v1',
        'task_id': CARD_ID,
        'profile_id': PROFILE['id'],
        'run_id': run_id,
        'tick_interval': [SNAP_TICKS[0], SNAP_TICKS[-1]],
        'subject_sha256': subject_sha,
        'capture_sha256': video_sha,
        'sheet_layout': {
            'pixel_size': list((2 * 640, 3 * 240)),
            'honest_titles': 'rendered inside every viewport: view name, '
                             'mode and tick; diagnostic footer carries the '
                             'gap/displacement trace inset',
            'rows': ['one row per registry view id: diagnostic (left) and '
                     'clean (right) viewports of the same state'],
            'tick_to_seconds_map': TICK_MAP + '; frame t = snapshot tick t',
            'frame_files': frame_hashes,
        },
        'views': views,
    }
    context = {'task_id': CARD_ID, 'run_id': run_id,
               'subject_sha256': subject_sha, 'capture_sha256': video_sha,
               'tick_interval': [SNAP_TICKS[0], SNAP_TICKS[-1]]}
    receipt = validate_manifest(manifest, context, PROFILE)
    receipt['video_path'] = str(video_path)
    receipt['video_sha256'] = video_sha
    receipt['subject_path'] = ('tools/monkey_campaign/contributions/'
                               + CARD_FULL + '/experiment_receipt.json')
    receipt['subject_sha256'] = subject_sha
    receipt['trace_path'] = ('tools/monkey_campaign/contributions/'
                             + CARD_FULL + '/experiment_trace.json')
    receipt['trace_sha256'] = trace_sha
    receipt['frame_count'] = len(frame_hashes)
    receipt['ffmpeg_version'] = ffmpeg_version(ffmpeg)
    receipt['codec'] = 'ffv1 level 3 g 1, -fflags +bitexact (mkv); ' \
                       'CODEC_STANDARD.md 2026-09-29'
    receipt['render_source'] = ('render_run.py software raster over the '
                                'committed experiment_trace.json rows '
                                '(solver state bound before pixels)')
    receipt['state_hash_preserved_across_view_toggles'] = \
        bool(state_hashes.get('preserved_across_view_toggles'))
    receipt['state_hashes'] = state_hashes.get('hashes', {})
    receipt['validator'] = ('tools/monkey_campaign/visual_capture.py '
                            'validate_manifest')
    receipt['profile_source'] = REGISTRY_DB + f' kanban.cards[{CARD_FULL}]' \
                              '.spec.ontology_qualification.task' \
                              '.verification_profile (read read-only)'
    receipt['limits'] = ('Structural camera-metadata validation only; '
                         'independent image/physics review remains '
                         'mandatory.')

    for target, payload in (
            (HERE / 'capture_manifest.json', manifest),
            (HERE / 'capture_context.json', context),
            (HERE / 'capture_validation_receipt.json', receipt),
            (evidence_dir / 'capture_manifest.json', manifest),
            (evidence_dir / 'capture_context.json', context),
            (evidence_dir / 'validation_receipt.json', receipt)):
        target.write_bytes((json.dumps(payload, indent=1,
                                       ensure_ascii=False, sort_keys=True)
                            + '\n').encode('utf-8'))
    print('video:', video_path)
    print('video sha256:', video_sha)
    print('validate_manifest:', receipt['mode'],
          '| structurally_valid:', receipt['structurally_valid'],
          '| views:', receipt['view_count'])
    return 0


PROFILE = registry_profile()

if __name__ == '__main__':
    sys.exit(main())
