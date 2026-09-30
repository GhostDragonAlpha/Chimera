"""{{CARD_FULL}} capture manifest builder - card-kit template.

Copy-adapted from the merged MAT2-M08 make_capture.py, upgraded with the
CODEC_STANDARD.md addendum (lane CODEC-BENCHMARK, 2026-09-29):
  - FFV1 `-level 3 -g 1` PLUS `-fflags +bitexact` (plain FFV1 embeds an
    8-byte wall-clock DateUTC field: two identical encodes differed in 44
    bytes; bitexact re-encodes are byte-identical, measured);
  - NO lossy fallback: lossy codecs are never evidence (x264 crf18 shifts
    >= 1 LSB on ~86% of pixels); if ffv1 is missing from the ffmpeg build,
    REFUSE - do not silently write a lossy capture;
  - the ffmpeg version string is recorded in the validation receipt
    (residual build dependency: outputs differ across ffmpeg builds).

Unchanged from M08 (keep all of it):
  - task_id SHORT form ("{{CARD_ID}}", not "MAT2-{{CARD_ID}}") in manifest
    AND context;
  - the registry verification profile is read READ-ONLY from
    agent_slots.sqlite3 (`file:...?mode=ro`), never hand-copied;
  - every hash derived from files on disk (no hand-typed values);
  - single-artifact binding: ONE video file, capture_sha256 = its sha256,
    every view row an artifact_locator of kind video on it;
  - diagnostic/clean view pairs with identical cameras and state.

FILL LIST: {{CARD_FULL}} {{CARD_ID}} {{DATE}} {{VIDEO_NAME}}
{{SUBJECTS}} {{LABELS}} {{VIEWS}} {{TICK_MAP}} and the PROFILE key path.
Run from this directory AFTER the experiment modes and render_run:
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

# FILL {{ORACLE_IMPORT}}: only for sha256_file reuse (M08 reused the
# oracle module's helper); a local def sha256_file is equally fine.
# import integrated_step as iw  # noqa: E402
from visual_capture import validate_manifest  # noqa: E402

FPS = 1
REGISTRY_DB = 'E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3'
CARD_FULL = '{{CARD_FULL}}'
CARD_ID = '{{CARD_ID}}'                 # SHORT form for task_id
if CARD_ID.startswith('{{'):
    raise SystemExit('make_capture_template.py is UNFILLED: replace the '
                     '{{...}} placeholders before running (see FILL LIST).')
SNAP_TICKS = [0, 10, 20, 30, 40, 50, 60, 70, 79]   # FILL: declared ticks
TICK_MAP = ('FILL {{TICK_MAP}}: units per tick; frames are the declared '
            'snapshot ticks at 1 video second per frame; the steady-state '
            'stepping itself never leaves the device (telemetry budgets)')


def sha256_file(path):
    return hashlib_sha256(pathlib.Path(path).read_bytes()).hexdigest()


def hashlib_sha256(data):
    import hashlib
    return hashlib.sha256(data).hexdigest()


def registry_profile():
    """The verification profile object, read READ-ONLY from the registry.
    NEVER hand-copy profile fields: validate_manifest must see the exact
    registry object (G7)."""
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


SUBJECTS = []   # FILL {{SUBJECTS}}: required subject ids
LABELS = []     # FILL {{LABELS}}: declared label ids


def vis_diagnostic(subjects=None):
    """Every declared diagnostic layer carried; nothing hidden. FILL the
    tag_bindings mapping for your subject families."""
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
                {'label_id': label, 'subject_id': label}
                for label in labels]}


def vis_clean():
    """Clean pair row: identical camera and state, no labels/layers by
    design (clean_view_required)."""
    return {'layers': [],
            'label_ids': [],
            'selected_ids': [],
            'required_subject_ids': list(SUBJECTS),
            'observed_subject_ids': list(SUBJECTS),
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
    video_path = capture_dir / 'capture' / '{{VIDEO_NAME}}'
    video_path.parent.mkdir(parents=True, exist_ok=True)
    frames = sorted(frames_dir.glob('frame_*.png'))
    assert len(frames) == len(SNAP_TICKS), \
        f'expected {len(SNAP_TICKS)} frames, found {len(frames)}'
    probe = subprocess.run([ffmpeg, '-hide_banner', '-encoders'],
                           capture_output=True, text=True)
    if 'ffv1' not in probe.stdout:
        # CODEC_STANDARD: lossy codecs are never evidence. Refuse instead
        # of falling back (M08's x264 fallback is closed by this addendum).
        raise SystemExit('ffv1 encoder missing from this ffmpeg build '
                         f'({ffmpeg}); a lossless gate-bearing capture is '
                         'mandatory - install an ffmpeg with ffv1')
    cmd = [ffmpeg, '-y', '-loglevel', 'error', '-framerate', str(FPS),
           '-i', str(frames_dir / 'frame_%02d.png'),
           '-c:v', 'ffv1', '-level', '3', '-g', '1',
           '-fflags', '+bitexact',
           str(video_path)]
    subprocess.run(cmd, check=True)
    video_sha = sha256_file(video_path)
    receipt_gpu = json.loads((HERE / 'experiment_receipt.json').read_text(
        encoding='utf-8'))
    subject_sha = sha256_file(HERE / 'experiment_receipt.json')
    trace_sha = sha256_file(HERE / 'experiment_trace.json')
    run_id = '{{CARD_ID_LOWER}}-resident-visual-{{DATE}}-' + video_sha[:8]

    cams = json.loads((evidence_dir / 'cameras.json').read_text('utf-8'))
    frame_hashes = json.loads(
        (evidence_dir / 'frame_hashes.json').read_text('utf-8'))
    # clean pairs must be the SAME cameras as their diagnostic pairs
    for name in ('whole', 'side', 'front', 'closeup'):   # FILL: your views
        assert cams[f'{name}:diagnostic'][0] == cams[f'{name}:clean'][0], \
            f'{name}: clean/diagnostic camera mismatch'

    binding = {'kind': 'trace', 'sha256': trace_sha,
               'note': 'sha256 of contributions/' + CARD_FULL +
                       '/experiment_trace.json: the per-tick comparison '
                       'trace of the run; rendered state is bound to the '
                       'committed receipts before any pixel is written'}

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

    # FILL {{VIEWS}}: one diagnostic+clean pair per registry view id.
    views = [
        view('pair-whole', PROFILE['views'][0], 'diagnostic',
             cams['whole:diagnostic'][0], None, vis_diagnostic(),
             'FILL: single viewport; fixed camera; what the reviewer sees'),
        view('pair-whole', PROFILE['views'][0], 'clean',
             cams['whole:diagnostic'][0], None, vis_clean(),
             'clean row: identical camera and state to its diagnostic '
             'pair; no labels, layers or diagnostic styling by design'),
    ]

    manifest = {
        'schema': 'chimera.visual_capture_manifest.v1',
        'task_id': CARD_ID,             # SHORT form
        'profile_id': PROFILE['id'],
        'run_id': run_id,
        'tick_interval': [SNAP_TICKS[0], SNAP_TICKS[-1]],
        'subject_sha256': subject_sha,
        'capture_sha256': video_sha,
        'sheet_layout': {
            'pixel_size': [2560, 840],  # FILL: your sheet size
            'honest_titles': 'rendered inside every viewport: view name, '
                             'mode and tick; footer carries residency '
                             'evidence',
            'rows': ['FILL: describe your sheet rows honestly'],
            'tick_to_seconds_map': TICK_MAP + '; frame t = snapshot tick t',
            'frame_files': frame_hashes,
        },
        'views': views,
    }
    context = {
        'task_id': CARD_ID,             # SHORT form here too
        'run_id': run_id,
        'subject_sha256': subject_sha,
        'capture_sha256': video_sha,
        'tick_interval': [SNAP_TICKS[0], SNAP_TICKS[-1]],
    }
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
    receipt['render_source'] = 'FILL: what produced the pixels (solver ' \
                               'state, declared rasterizer)'
    receipt['validator'] = 'tools/monkey_campaign/visual_capture.py ' \
                           'validate_manifest'
    receipt['profile_source'] = REGISTRY_DB + f' kanban.cards[{CARD_FULL}]' \
                              '.spec.ontology_qualification.task' \
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
        # CRLF law: byte-level write (write_text translates \n to
        # os.linesep on Windows; M08's capture JSONs committed as CRLF
        # that way - stable under * -text, but byte-level is the law)
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
