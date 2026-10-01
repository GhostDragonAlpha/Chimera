"""MAT2-G06 capture builder (grasp/motion profile).

Assembles the ONE deterministic FFV1 capture from the rendered frames
(render_run.py), validates the camera metadata structurally with the
in-repo campaign validator, and refuses on any gap:

- codec law (CODEC_STANDARD): FFV1 `-level 3 -g 1 -fflags +bitexact` mkv;
  lossy codecs are never evidence (there is no fallback -- the build
  refuses instead);
- the registry grasp profile is read READ-ONLY from agent_slots.sqlite3
  at capture time (house gate G7; never hand-copied); task_id SHORT
  form (G06) in manifest AND context;
- one gate-bound capture identity: video -> disk sha256 == manifest ==
  context == determinism record; every view row carries the full
  registry camera record; clean/diagnostic pairs share the exact camera
  and the exact physical state binding (motion class: the state binding
  is the committed trace);
- visual_acceptance stays false BY DESIGN: structural validation only;
  independent visual review remains the Sergeant gate.

Run: python -B make_capture.py
"""
from __future__ import annotations

import g06_deps  # noqa: E402

g06_deps.ensure()

import hashlib  # noqa: E402
import json  # noqa: E402
import pathlib  # noqa: E402
import sqlite3  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
CONTRIB = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(CONTRIB.parents[1]))   # .../tools (package root)
sys.path.insert(0, str(CONTRIB.parent))       # visual_gate's flat import

import transfer_sequence as ts  # noqa: E402
from monkey_campaign import visual_capture as vc  # noqa: E402
from monkey_campaign import visual_gate as vg  # noqa: E402

gc = ts.load_g04_module()   # the pinned sealed G04 fixture (hash-asserted)

CARD_ID = 'G06'                       # SHORT form (G7)
CARD_FULL = 'MAT2-G06'
TASK_FULL = 'MAT2-G06'
RUN_ID = 'mat2-g06-transfer-20261001-06f81b4d'
CRITERIA_SHA256 = ('244ec17a4265b1eff67a541566bc68764ca37e4597554e4ddd62218'
                   '96ca30b83')
REGISTRY_SQLITE = pathlib.Path(
    'E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3')
VIDEO_NAME = 'capture_mat2_g06_transfer_20261001.mkv'
FFMPEG_CMD = ['ffmpeg', '-y', '-f', 'image2', '-framerate', '1',
              '-i', 'frame_%02d.png', '-c:v', 'ffv1', '-level', '3',
              '-g', '1', '-fflags', '+bitexact', '-pix_fmt', 'rgb24',
              VIDEO_NAME]
TICK_INTERVAL = [1, 229]


def sha256_file(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def registry_profile():
    """Read-ONLY single-query profile extraction at capture time (G7)."""
    con = sqlite3.connect('file:%s?mode=ro' % REGISTRY_SQLITE.as_posix(),
                          uri=True)
    try:
        cur = con.cursor()
        cur.execute('SELECT payload FROM state WHERE id=1')
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
                    '.verification_profile' % CARD_ID,
        'note': 'profile object read READ-ONLY; never hand-copied',
        'criteria_sha256': CRITERIA_SHA256,
    }
    return profile, provenance


def main():
    import render_run as rr
    cap = HERE / 'evidence' / 'capture'
    frames = sorted(cap.glob('frame_*.png'))
    if len(frames) != 10:
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
    rows_out = []
    observed = ['trunk_01.lateral', 'grip.pad_0', 'grip.pad_1', 'grip.pad_2']
    for view in cameras['views']:
        rec = cameras['records'][view]
        for mode in ('diagnostic', 'clean'):
            labels = ['grip.pad_0', 'grip.pad_1', 'grip.pad_2']
            if view == cameras['views'][1]:
                labels = ['grip.pad_0', 'contact.s1.centroid']
            observed_view = observed if view != cameras['views'][1] \
                else ['trunk_01.lateral', 'grip.pad_0',
                      'contact.s1.centroid']
            row = {
                'view_id': view,
                'mode': mode,
                'pair_id': 'pair:%s' % view,
                'state_binding': {'kind': 'trace', 'sha256': trace_sha,
                                  'note': SCENARIO_NOTE + ' at the declared '
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
                    'required_subject_ids': observed_view,
                    'observed_subject_ids': observed_view,
                    'missing_subject_ids': [],
                    'occlusion_mode': 'depth_tested' if mode == 'clean'
                    else 'xray',
                    'tag_bindings': [] if mode == 'clean' else
                    [{'label_id': lbl, 'subject_id': lbl}
                     for lbl in labels],
                },
                'pixel_presence_min': {
                    k: min(fr['exact_color_counts']['%s:%s' % (view, mode)]
                           .get(k, 0) for fr in presence['frames'])
                    for k in ('trunk', 'pad_edge', 'pad_fill',
                              'normal_arrow', 'force_arrow')
                },
            }
            rows_out.append(row)
    manifest = {
        'schema': vc.SCHEMA,
        'task_id': CARD_ID,
        'run_id': RUN_ID,
        'profile_id': 'grasp',
        'subject_sha256': trace_sha,
        'capture_sha256': capture_sha,
        'tick_interval': TICK_INTERVAL,
        'views': rows_out,
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
        'tick_interval': TICK_INTERVAL,
        'task_full': TASK_FULL,
        'criteria_sha256': CRITERIA_SHA256,
        'attempt_id': '06f81b4dee134738a8c03a1c8c5d3797',
        'agent_id': 'wk-g06b-arrival-1',
        'tick_map': cameras['tick_map'],
        'view_realization': cameras['view_realization'],
        'absent_components': cameras['absent_components'],
        'rendered_scenario': SCENARIO_NOTE,
        'registry_profile_provenance': None,   # filled below
    }
    profile, provenance = registry_profile()
    context['registry_profile_provenance'] = provenance

    # 3. structural validation (in-repo campaign validator + gate)
    receipt = vc.validate_manifest(manifest, context, profile)
    (cap / 'capture_manifest.json').write_bytes(ts.canonical(manifest))
    (cap / 'capture_context.json').write_bytes(ts.canonical(context))
    (cap / 'capture_validation_receipt.json').write_bytes(ts.canonical(
        {'schema': 'chimera.g06_capture_validation.v1',
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
    (cap / 'capture_validation_receipt.json').write_bytes(ts.canonical(
        {'schema': 'chimera.g06_capture_validation.v1',
         'validate_manifest': receipt,
         'visual_gate_verify': gate}))
    print(json.dumps({'capture_sha256': capture_sha,
                      'structurally_valid': receipt['structurally_valid'],
                      'visual_acceptance': receipt['visual_acceptance'],
                      'visual_gate_verify': gate['structurally_valid']},
                     indent=1))


SCENARIO_NOTE = ('band_mid|n=3 (a closing transfer) REPLAYED through the '
                 'declared 229-tick schedule: attach at the source band, '
                 'load (climb-to-friction handover), hold, the handover at '
                 'tick 31 (holders carry m/(n-1)), the accel/cruise/brake/'
                 'hover climb to the target band, re-attach at tick 193, '
                 'hold2, release at tick 220; every envelope tick records '
                 'admissible support (the done_when transfer); the '
                 'diagnostic layer draws the delivered telemetry (tick/'
                 'phase/dt, all-stick and holding-stick counts, support '
                 'flag)')


if __name__ == '__main__':
    main()
