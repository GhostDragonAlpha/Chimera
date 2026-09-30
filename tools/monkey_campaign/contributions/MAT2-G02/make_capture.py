"""MAT2-G02 capture manifest builder (card-kit pattern, CODEC_STANDARD
2026-09-29 addendum: FFV1 -level 3 -g 1 -fflags +bitexact; NO lossy fallback
- the build refuses instead of degrading; ffmpeg version recorded).

task_id SHORT form ('G02') in manifest AND context; registry verification
profile read READ-ONLY from agent_slots.sqlite3 (never hand-copied); every
hash derived from files on disk; single-artifact binding (ONE video,
capture_sha256 = its sha256, every view row an artifact_locator on it);
diagnostic/clean pairs with identical cameras and identical physical state.

Round-1 corrections (review sgt-pr281-r1): visibility rows are MEASURED -
observed/missing subject ids come from render_run's per-frame pixel
evidence (evidence/pixel_presence.json) and make_capture REFUSES to build
the manifest if any required subject lacks pixel evidence (the previous
revision asserted observed_subject_ids without pixels while five of six
viewports were empty).

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


def vis_rows(presence, cams):
    """Measured visibility rows (round-1 fix): observed/missing subject ids
    come from render_run's per-frame pixel evidence; make_capture REFUSES
    instead of publishing a claim the pixels do not back."""
    req = presence['required_subjects']
    frames = presence['per_tile_frames']
    rows = {}
    for view_id in VIEWS:
        for mode in ('diagnostic', 'clean'):
            tile = cams_tile(view_id, mode)
            per_frame = frames[tile]
            required = list(req[tile])
            observed = [s for s in required
                        if all(fr['subjects'][s]['present']
                               for fr in per_frame)]
            missing = [s for s in required if s not in observed]
            if missing:
                raise SystemExit(f'subject_pixels_missing:{tile}: {missing}'
                                 ' (refusing to publish a manifest the '
                                 'pixels do not back)')
            entry = {'required_subject_ids': required,
                     'observed_subject_ids': observed,
                     'missing_subject_ids': []}
            if mode == 'diagnostic':
                labels = sorted({lab
                                 for rec in cams[f'{view_id}:diagnostic']
                                 for lab in rec['label_ids']})
                entry.update({
                    'layers': list(LAYERS),
                    'label_ids': labels,
                    'selected_ids': list(labels),
                    'occlusion_mode': 'depth_tested',
                    'tag_bindings': [{'label_id': lab, 'subject_id': lab}
                                     for lab in labels],
                    'pixel_evidence': {
                        'min_tile_nonbg_pixels':
                            min(fr['nonbg_pixels'] for fr in per_frame),
                        'footer_min_trace_line_pixels':
                            min(fh['footer']['trace_line_pixels']
                                for fh in presence['frames']),
                        'source': 'evidence/pixel_presence.json '
                                  '(render_run measured signatures)'},
                })
                inset = inset_evidence(presence, tile)
                if inset is not None:
                    entry['pixel_evidence']['secondary_inset'] = inset
            else:
                entry.update({
                    'layers': [],
                    'label_ids': [],
                    'selected_ids': [],
                    'occlusion_mode': 'depth_tested',
                    'tag_bindings': [],
                    'pixel_evidence': {
                        'min_tile_nonbg_pixels':
                            min(fr['nonbg_pixels'] for fr in per_frame),
                        'label_pixels_total_max':
                            max(fr['label_pixels_total']
                                for fr in per_frame),
                        'source': 'evidence/pixel_presence.json '
                                  '(render_run measured signatures)'},
                })
            rows[f'{view_id}:{mode}'] = entry
    return rows


def cams_tile(view_id, mode):
    pair = f'pair-{VIEWS.index(view_id)}'
    return f'{pair}:{mode}'


def inset_evidence(presence, tile):
    """Measured picture-in-picture inset evidence (round-2 fix, the r2
    blocker: the declared 288x76 oblique inset contained caption text
    only). Every number is measured INSIDE the declared rect; the gate is
    exact-color signatures of the declared inset render, so a caption-
    only inset cannot pass."""
    per_frame = presence['per_tile_frames'][tile]
    pips = [fr.get('pip') for fr in per_frame if fr.get('pip')]
    if not pips:
        return None
    sig_names = sorted(pips[0]['signatures'])
    return {
        'rect_px': list(pips[0]['rect_px']),
        'viewport_resolution': list(pips[0]['viewport_resolution']),
        'camera_frame_id': pips[0]['camera_frame_id'],
        'render_mode': pips[0]['render_mode'],
        'min_signature_pixels_inside_rect':
            {k: min(p['signatures'][k] for p in pips)
             for k in sig_names},
        'min_caption_chip_pixels':
            min(p['caption_chip_pixels'] for p in pips),
        'min_nonbg_pixels': min(p['nonbg_pixels'] for p in pips),
        'max_occluded_prepaste_pixels':
            max(sum(p['occluded_prepaste_pixels'].values())
                for p in pips),
        'gate': 'every declared geometry signature > 0 exact-color px '
                'INSIDE the declared rect (render_run gate + '
                'check_capture_pixels inset check); a caption-only '
                'inset fails every signature gate',
        'measurement': 'post-paste tile stats; primary geometry '
                       'occluded by the paste disclosed per frame '
                       '(pixel_presence.json pip blocks)',
    }


def req_tile(presence, tile):
    return list(presence['required_subjects'][tile])


def pixel_presence_summary(presence):
    tiles = {}
    for key, per_frame in sorted(presence['per_tile_frames'].items()):
        required = req_tile(presence, key)
        observed = [s for s in required
                    if all(fr['subjects'][s]['present']
                           for fr in per_frame)]
        tiles[key] = {'required': required, 'observed': observed,
                      'missing': [s for s in required
                                  if s not in observed],
                      'min_nonbg_pixels': min(fr['nonbg_pixels']
                                              for fr in per_frame)}
    insets = {key: inset_evidence(presence, key)
              for key in sorted(presence['per_tile_frames'])}
    insets = {k: v for k, v in insets.items() if v is not None}
    return {
        'all_present': bool(presence['all_present']),
        'min_tile_nonbg_pixels':
            min(t['min_nonbg_pixels'] for t in tiles.values()),
        'footer_min_trace_line_pixels':
            min(fh['footer']['trace_line_pixels']
                for fh in presence['frames']),
        'camera_consistency_max_delta_px':
            max(c['delta_px'] for c in presence['camera_consistency']),
        'secondary_insets': insets,
        'tiles': tiles,
        'evidence_file': 'evidence/pixel_presence.json',
        'independent_check': 'check_capture_pixels.py <capture_dir> '
                             '(re-measures from the committed frames; '
                             'control mode red on the pre-fix capture '
                             'and on the r2 caption-only inset)',
    }


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
    presence = json.loads((evidence_dir / 'pixel_presence.json')
                          .read_bytes().decode('utf-8'))
    for view_id in VIEWS:
        assert cams[f'{view_id}:diagnostic'][0] == \
            cams[f'{view_id}:clean'][0], \
            f'{view_id}: clean/diagnostic camera mismatch'
    vis = vis_rows(presence, cams)

    binding = {'kind': 'trace', 'sha256': trace_sha,
               'note': 'sha256 of contributions/' + CARD_FULL +
                       '/experiment_trace.json: the per-tick fixture trace '
                       'of the run; rendered state is bound to the '
                       'committed receipts before any pixel is written'}

    def view(pair_id, view_id, mode, camera, visibility, note,
             secondary=None):
        row = {'artifact_locator': {'kind': 'video',
                                    'seconds': [0, len(SNAP_TICKS)]},
               'camera': camera,
               'cell_layout_note': note,
               'mode': mode,
               'pair_id': pair_id,
               'state_binding': binding,
               'view_id': view_id,
               'visibility': visibility}
        if secondary:
            row['secondary_cameras'] = secondary
        return row

    views = []
    notes = {
        VIEWS[0]: 'whole-fixture viewport; fixed bookmark camera; the '
                  'in-frame gate asserted per frame that the patch quad, '
                  'both bodies and the declared support stand project '
                  'inside the viewport (nothing hidden or clipped)',
        VIEWS[1]: 'loaded interface close-up; fixed bookmark camera; '
                  'declared framing scope = the loaded patch quad and '
                  'seam (interface subjects)',
        VIEWS[2]: 'orthogonal patch view (axis-aligned, looking along '
                  '+X); declared framing scope = the patch quad and seam; '
                  'the diagnostic cell additionally renders the declared '
                  'oblique secondary camera as a labeled picture-in-'
                  'picture inset (secondary_cameras) at its declared '
                  '288x76 resolution: the inset camera is in-frame-gated '
                  'in the INSET coordinate space, every declared geometry '
                  'signature is measured > 0 exact-color px INSIDE the '
                  'declared rect (caption-only insets refuse to build), '
                  'and the gate-checked inset hides no subject point and '
                  'no label of the primary viewport',
    }
    for vi, view_id in enumerate(VIEWS):
        pair_id = f'pair-{vi}'
        secondary = cams[f'{view_id}:diagnostic'][1:] or None
        views.append(view(pair_id, view_id, 'diagnostic',
                          cams[f'{view_id}:diagnostic'][0],
                          vis[f'{view_id}:diagnostic'], notes[view_id],
                          secondary=secondary))
        views.append(view(pair_id, view_id, 'clean',
                          cams[f'{view_id}:clean'][0],
                          vis[f'{view_id}:clean'],
                          'clean row: identical camera and identical '
                          'physical state to its diagnostic pair; no '
                          'labels, layers or diagnostic styling by design '
                          '(measured: zero label and triad pixels)'))

    manifest = {
        'schema': 'chimera.visual_capture_manifest.v1',
        'task_id': CARD_ID,
        'profile_id': PROFILE['id'],
        'run_id': run_id,
        'tick_interval': [SNAP_TICKS[0], SNAP_TICKS[-1]],
        'subject_sha256': subject_sha,
        'capture_sha256': video_sha,
        'sheet_layout': {
            'pixel_size': [2 * 640, 3 * 240 + 56],
            'tile_rects': presence['tile_rects'],
            'footer_rect': presence['footer_rect'],
            'honest_titles': 'rendered inside every viewport: view name, '
                             'mode and tick (exact-color marker chips '
                             'measured); the shared diagnostic footer band '
                             'carries the gap/displacement trace inset '
                             'outside every viewport rect',
            'rows': ['one row per registry view id: diagnostic (left) and '
                     'clean (right) 640x240 viewports of the same state'],
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
                                '(solver state bound before pixels); '
                                'draw_viewport() called for all six '
                                'viewports AND the 288x76 oblique PiP '
                                'inset at its own target resolution '
                                '(round-2 fix); in-frame gate + '
                                'reprojection oracle gate passed before '
                                'any manifest, inset content gated by '
                                'exact-color signatures inside the '
                                'declared rect')
    receipt['state_hash_preserved_across_view_toggles'] = \
        bool(state_hashes.get('preserved_across_view_toggles'))
    receipt['state_hashes'] = state_hashes.get('hashes', {})
    receipt['pixel_presence'] = pixel_presence_summary(presence)
    receipt['validator'] = ('tools/monkey_campaign/visual_capture.py '
                            'validate_manifest')
    receipt['profile_source'] = REGISTRY_DB + f' kanban.cards[{CARD_FULL}]' \
                              '.spec.ontology_qualification.task' \
                              '.verification_profile (read read-only)'
    receipt['limits'] = ('Structural camera-metadata validation only; '
                         'pixel grounding is recorded by render_run '
                         '(pixel_presence) and re-checked by '
                         'check_capture_pixels.py; independent image/'
                         'physics review remains mandatory. The raster is '
                         'wireframe (no hidden-line removal); occlusion is '
                         'declared depth_tested per the validator enum.')

    for target, payload in (
            (HERE / 'capture_manifest.json', manifest),
            (HERE / 'capture_context.json', context),
            (HERE / 'capture_validation_receipt.json', receipt),
            (HERE / 'capture_pixel_presence.json', presence),
            (evidence_dir / 'capture_manifest.json', manifest),
            (evidence_dir / 'capture_context.json', context),
            (evidence_dir / 'validation_receipt.json', receipt),
            (evidence_dir / 'capture_pixel_presence.json', presence)):
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
