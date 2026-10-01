"""MAT2-G04 capture builder (grasp/motion profile).

Assembles the ONE deterministic FFV1 capture from the rendered frames
(render_run.py), validates the camera metadata structurally with the
in-repo campaign validator, and refuses on any gap:

- codec law (CODEC_STANDARD): FFV1 `-level 3 -g 1 -fflags +bitexact` mkv;
  lossy codecs are never evidence (there is no fallback -- the build
  refuses instead);
- the registry grasp profile is read READ-ONLY from agent_slots.sqlite3
  at capture time (house gate G7; never hand-copied); task_id SHORT
  form (G04) in manifest AND context;
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

import contact_support_obs as cso  # noqa: E402
from monkey_campaign import visual_capture as vc  # noqa: E402
from monkey_campaign import visual_gate as vg  # noqa: E402

gc = cso.load_g04_module()   # the pinned sealed G04 fixture (hash-asserted)

CARD_ID = 'G05'                       # SHORT form (G7)
CARD_FULL = 'MAT2-G05'
TASK_FULL = 'MAT2-G05'
RUN_ID = 'mat2-g05-observe-20260930-e20294c6'
CRITERIA_SHA256 = ('e1e41e878ac6ed0ecae012363f738747dc161ff499223c0dd13acc6'
                   '00cf21388')
REGISTRY_SQLITE = pathlib.Path(
    'E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3')
VIDEO_NAME = 'capture_mat2_g05_obs_20260930.mkv'
FFMPEG_CMD = ['ffmpeg', '-y', '-f', 'image2', '-framerate', '1',
              '-i', 'frame_%02d.png', '-c:v', 'ffv1', '-level', '3',
              '-g', '1', '-fflags', '+bitexact', '-pix_fmt', 'rgb24',
              VIDEO_NAME]


def sha256_file(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def registry_profile():
    """Read-ONLY single-query profile extraction at capture time (G7)."""
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
        'note': 'profile object read READ-ONLY; never hand-copied',
        'criteria_sha256': CRITERIA_SHA256,
    }
    return profile, provenance


def main():
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

    # 2. camera records -> manifest rows (full 17-field record per row)
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
        'tick_interval': [1, 30],
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
        'tick_interval': [1, 30],
        'task_full': TASK_FULL,
        'criteria_sha256': CRITERIA_SHA256,
        'attempt_id': 'e20294c681f64128bad610a7e98ba1d8',
        'agent_id': 'wk-g05-observe',
        'tick_map': cameras['tick_map'],
        'view_realization': cameras['view_realization'],
        'absent_components': cameras['absent_components'],
        'rendered_scenario': ('scene|n=3 (the closing multi-channel case) '
                              'REPLAYED through the declared observation '
                              'interface: supported through the 20 hold '
                              'ticks, release at tick 21 (support removed); '
                              'the diagnostic layer draws the delivered '
                              'telemetry (tick/phase/dt, support count); '
                              'the slip states are carried numerically in '
                              'the receipts, not in this capture'),
        'registry_profile_provenance': None,   # filled below
    }
    profile, provenance = registry_profile()
    context['registry_profile_provenance'] = provenance

    # 3. structural validation (in-repo campaign validator + gate)
    receipt = vc.validate_manifest(manifest, context, profile)
    (cap / 'capture_manifest.json').write_bytes(gc.canonical(manifest))
    (cap / 'capture_context.json').write_bytes(gc.canonical(context))
    (cap / 'capture_validation_receipt.json').write_bytes(gc.canonical(
        {'schema': 'chimera.g05_capture_validation.v1',
         'validate_manifest': receipt,
         'visual_gate_verify': None}))
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
    (cap / 'capture_validation_receipt.json').write_bytes(gc.canonical(
        {'schema': 'chimera.g05_capture_validation.v1',
         'validate_manifest': receipt,
         'visual_gate_verify': gate}))
    print(json.dumps({'capture_sha256': capture_sha,
                      'structurally_valid': receipt['structurally_valid'],
                      'visual_acceptance': receipt['visual_acceptance'],
                      'visual_gate_verify': gate['structurally_valid']},
                     indent=1))


if __name__ == '__main__':
    main()
