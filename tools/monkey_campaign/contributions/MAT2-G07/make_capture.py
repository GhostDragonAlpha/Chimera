"""MAT2-G07 capture builder (grasp/motion profile).

Assembles the ONE deterministic FFV1 capture from the rendered frames
(render_run.py), validates the camera metadata structurally with the
in-repo campaign validator, and refuses on any gap:

- codec law (CODEC_STANDARD): FFV1 `-level 3 -g 1 -fflags +bitexact` mkv;
  lossy codecs are never evidence (there is no fallback -- the build
  refuses instead);
- the registry grasp profile is read READ-ONLY from agent_slots.sqlite3
  at capture time (house gate G7; never hand-copied); the profile KIND is
  asserted `motion` BEFORE the capture is built (the W06 lesson) and
  task_id is the SHORT form (G07) in manifest AND context;
- one gate-bound capture identity: video -> disk sha256 == manifest ==
  context == determinism record; every view row carries the full
  registry camera record; clean/diagnostic pairs share the exact camera
  and the exact physical state binding;
- visual_acceptance stays false BY DESIGN: structural validation only;
  independent visual review remains the Sergeant gate.

Run: python -B make_capture.py
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sqlite3
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
CONTRIB = HERE.parent
sys.path.insert(0, str(CONTRIB.parents[1]))   # .../tools (package root)
sys.path.insert(0, str(CONTRIB.parent))       # visual_gate's flat import

import release_fall_account as rfa  # noqa: E402
from monkey_campaign import visual_capture as vc  # noqa: E402
from monkey_campaign import visual_gate as vg  # noqa: E402

cso = rfa.load_g05_module()   # the sealed G05 seam (hash-asserted)
gc = cso.load_g04_module()    # the pinned sealed G04 fixture (hash-asserted)

CARD_ID = 'G07'                       # SHORT form (G7)
CARD_FULL = 'MAT2-G07'
TASK_FULL = 'MAT2-G07'
RUN_ID = 'mat2-g07-release-20260930-6a00d379'
CRITERIA_SHA256 = ('a6691ba418440dd040761e84c04c024f7a7535ffa41889167cab7e8'
                   'd63750cfe')
ATTEMPT_ID = '6a00d37939ef4f258ae8fb730f3c96fb'
AGENT_ID = 'wk-g07-falls'
REGISTRY_SQLITE = pathlib.Path(
    'E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3')
VIDEO_NAME = 'capture_mat2_g07_release_20260930.mkv'
FFMPEG_CMD = ['ffmpeg', '-y', '-f', 'image2', '-framerate', '1',
              '-i', 'frame_%02d.png', '-c:v', 'ffv1', '-level', '3',
              '-g', '1', '-fflags', '+bitexact', '-pix_fmt', 'rgb24',
              VIDEO_NAME]


def sha256_file(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def registry_profile():
    """Read-ONLY single-query profile extraction at capture time (G7);
    the profile kind is asserted motion BEFORE the capture is built."""
    con = sqlite3.connect('file:%s?mode=ro' % REGISTRY_SQLITE.as_posix(),
                          uri=True)
    try:
        cur = con.cursor()
        cur.execute('SELECT payload FROM state')
        state = json.loads(cur.fetchone()[0])
    finally:
        con.close()
    task = state['kanban']['cards'][TASK_FULL]['spec'][
        'ontology_qualification']['task']
    profile = task['verification_profile']
    assert profile['id'] == 'grasp' and profile['kind'] == 'motion', \
        'registry_profile_drift'
    provenance = {
        'db_path': str(REGISTRY_SQLITE),
        'extractor': 'sqlite3 mode=ro single query at capture time',
        'row_path': 'kanban.cards[MAT2-%s].spec.ontology_qualification.task'
                    '.verification_profile' % TASK_FULL,
        'note': 'profile object read READ-ONLY; never hand-copied; the '
                'profile kind (motion) is asserted BEFORE the capture is '
                'built (the W06 lesson)',
        'criteria_sha256': CRITERIA_SHA256,
    }
    return profile, provenance


def main():
    profile, provenance = registry_profile()   # BEFORE the build (W06)
    cap = HERE / 'evidence' / 'capture'
    frames = sorted(cap.glob('frame_*.png'))
    if len(frames) != 8:
        raise ValueError('capture_frames_missing:%d' % len(frames))
    presence = json.loads((cap / 'pixel_presence.json').read_text(
        encoding='utf-8'))
    if presence.get('failures'):
        raise ValueError('pixel_presence_failures_present')
    cameras = json.loads((cap / 'cameras.json').read_text(
        encoding='utf-8'))
    trace_sha = sha256_file(HERE / 'experiment_trace.json')

    # 1. encode: ONE artifact, FFV1 level 3 g 1 bitexact (refuse, never
    #    fall back to a lossy codec)
    proc = subprocess.run(FFMPEG_CMD, cwd=cap, capture_output=True,
                          text=True, timeout=600)
    if proc.returncode != 0:
        raise ValueError('ffmpeg_encode_failed:' + proc.stderr[-400:])
    video = cap / VIDEO_NAME
    capture_sha = sha256_file(video)
    ver = subprocess.run(['ffmpeg', '-version'], capture_output=True,
                         text=True, timeout=60)
    ffmpeg_version = ver.stdout.splitlines()[0]

    # 2. camera records -> manifest rows (full record per row)
    snap = cameras['snapshot_ticks']
    rows = []
    for view in cameras['views']:
        rec = cameras['records'][view]
        for mode in ('diagnostic', 'clean'):
            counts_key = '%s:%s' % (view, mode)
            observed = ['trunk_01.lateral', 'grip.pad_0', 'grip.pad_1',
                        'grip.pad_2']
            labels = ['grip.pad_0', 'grip.pad_1', 'grip.pad_2']
            if view == cameras['views'][1]:
                observed = ['trunk_01.lateral', 'grip.pad_0',
                            'contact.s1.centroid']
                labels = ['grip.pad_0', 'contact.s1.centroid']
            row = {
                'view_id': view,
                'mode': mode,
                'pair_id': 'pair:%s' % view,
                'state_binding': {'kind': 'trace', 'sha256': trace_sha,
                                  'note': 'scene|n=3 rows at the declared '
                                          'snapshot ticks; identical '
                                          'state_hash across the pair'},
                'artifact_locator': {'kind': 'video',
                                     'seconds': [0.0, float(len(frames))]},
                'camera': rec,
                'visibility': {
                    'layers': ([] if mode == 'clean'
                               else cameras['diagnostic_layers']),
                    'label_ids': [] if mode == 'clean' else labels,
                    'selected_ids': [],
                    'required_subject_ids': observed,
                    'observed_subject_ids': observed,
                    'missing_subject_ids': [],
                    'occlusion_mode': 'depth_tested' if mode == 'clean'
                    else 'xray',
                    'tag_bindings': [] if mode == 'clean' else
                    [{'label_id': lbl, 'subject_id': lbl}
                     for lbl in labels],
                },
                'pixel_presence_min': {
                    k: min(fr['exact_color_counts'][counts_key].get(k, 0)
                           for fr in presence['frames'])
                    for k in ('trunk', 'pad_edge', 'pad_fill',
                              'normal_arrow', 'force_arrow')
                },
            }
            rows.append(row)
    manifest = {
        'schema': vc.SCHEMA if hasattr(vc, 'SCHEMA') else
        'chimera.visual_capture.v2',
        'task_id': CARD_ID,
        'run_id': RUN_ID,
        'profile_id': 'grasp',
        'subject_sha256': trace_sha,
        'capture_sha256': capture_sha,
        'tick_interval': [1, 60],
        'views': rows,
        'capture_sha_definition':
            'sha256 of the single on-disk FFV1 mkv (bytes); frames are the '
            'determinism unit and are re-extractable at identity indices',
        'codec': {'codec': 'ffv1', 'level': 3, 'gop': 1,
                  'flags': '+bitexact', 'container': 'mkv',
                  'pix_fmt': 'rgb24', 'lossy_fallback': 'refused'},
        'ffmpeg_version': ffmpeg_version,
        'frame_manifest': [{'frame': fr['frame'], 'tick': fr['tick'],
                            'sha256': sha256_file(cap / fr['frame']),
                            'state_hash': fr['state_hash']}
                           for fr in presence['frames']],
    }
    context = {
        'task_id': CARD_ID,
        'run_id': RUN_ID,
        'subject_sha256': trace_sha,
        'capture_sha256': capture_sha,
        'tick_interval': [1, 60],
        'task_full': TASK_FULL,
        'criteria_sha256': CRITERIA_SHA256,
        'attempt_id': ATTEMPT_ID,
        'agent_id': AGENT_ID,
        'tick_map': cameras['tick_map'],
        'view_realization': cameras['view_realization'],
        'absent_components': cameras['absent_components'],
        'rendered_scenario': ('scene|n=3 (the closing multi-channel case; '
                              'zero collision events) REPLAYED through the '
                              'declared observation interface: supported '
                              'through the 20 hold ticks, release at tick '
                              '21 (press off; forces at the noise bars), '
                              'the measured free fall drawn at the trace '
                              'centroids through tick 56; the diagnostic '
                              'layer draws the delivered telemetry '
                              '(tick/phase/dt, support count, cumulative '
                              'fall displacement); the slip states and the '
                              'two recorded collision events (other '
                              'scenarios) are carried numerically in the '
                              'receipts, not in this capture'),
        'registry_profile_provenance': provenance,
    }

    # 3. structural validation (in-repo campaign validator + gate)
    receipt = vc.validate_manifest(manifest, context, profile)
    (cap / 'capture_manifest.json').write_bytes(rfa.canonical(manifest))
    (cap / 'capture_context.json').write_bytes(rfa.canonical(context))
    gate_receipt = {
        'evidence': {
            'camera': {'reference': str(cap / 'capture_manifest.json'),
                       'raw_sha256': sha256_file(
                           cap / 'capture_manifest.json')},
            'visual': {'reference': str(video), 'raw_sha256': capture_sha},
        },
        'capture_context': context}
    gate = vg.verify(gate_receipt, {'task_id': CARD_ID,
                                    'task': {'verification_profile':
                                             profile}})
    (cap / 'capture_validation_receipt.json').write_bytes(rfa.canonical(
        {'schema': 'chimera.g07_capture_validation.v1',
         'validate_manifest': receipt,
         'visual_gate_verify': gate}))
    print(json.dumps({'capture_sha256': capture_sha,
                      'structurally_valid': receipt['structurally_valid'],
                      'visual_acceptance': receipt['visual_acceptance'],
                      'visual_gate_verify': gate['structurally_valid']},
                     indent=1))


if __name__ == '__main__':
    main()
