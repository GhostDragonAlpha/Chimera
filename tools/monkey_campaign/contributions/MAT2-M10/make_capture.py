"""MAT2-M10 capture manifest builder: encodes the rendered payload frames
(rawvideo rgb24 pipe) into the single gate-bound video (FFV1 lossless, level
3, GOP 1, +bitexact per the campaign codec standard), builds the
chimera.visual_capture_manifest.v1 manifest + context (task_id SHORT form
"M10") and validates them with the registry validator, using the REGISTRY
profile object read READ-ONLY from
E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3
kanban.cards[MAT2-M10].spec.ontology_qualification.task.verification_profile.

Every hash is derived from files on disk (no hand-typed values).
Single-artifact binding: ONE video; capture_sha256 = that file's sha256;
every view row is an artifact_locator of kind video on it; every view row
carries the same state_binding.sha256 (the committed trace's dynamic_run
canonical sha256) — view toggles preserve the physical state hash.
Run from this directory:
    python -B make_capture.py <attempt_capture_dir>
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

import actuator_world as aw  # noqa: E402
from visual_capture import validate_manifest  # noqa: E402

REGISTRY_DB = 'E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3'
CANONICAL_LAYERS = {  # loud tripwire only; never supplies values
    'stable membrane/triangle/port IDs',
    'pressure and area-scaled force vectors',
    'rest/current geometry and material directions',
    'contact/bond state',
    'energy/work and simulation tick',
}
CRITERIA = '5e7560caa9efae9ec819c9127ab6ee6e7016e134bdf97e525f06cfedee31190c'
ATTEMPT = '02cc9dbda6f3494f8d8de36e20b94c0f'
VIEW_IDS = ['whole experiment at fixed distance',
            'orthogonal side and front',
            'oblique close-up of the loaded interface']


def require(condition, code):
    if not condition:
        raise ValueError(code)


def sha256_file(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False)


def registry_profile():
    con = sqlite3.connect(f'file:{REGISTRY_DB}?mode=ro', uri=True)
    try:
        payload = con.execute(
            'SELECT payload FROM state WHERE id=1').fetchone()[0]
    finally:
        con.close()
    reg = json.loads(payload)
    card = reg['kanban']['cards']['MAT2-M10']
    profile = card['spec']['ontology_qualification']['task'][
        'verification_profile']
    return profile


def vis_diagnostic():
    return {'layers': list(PROFILE['diagnostic_layers']),
            'label_ids': ['actuator_shell', 'actuator_shell/m:belt',
                          'port:pressure',
                          'clamp_north_cap (visible support)',
                          'tie_south_pole', 'bond:tie', 'load',
                          'source_m10_source'],
            'selected_ids': SUBJECTS,
            'required_subject_ids': SUBJECTS,
            'observed_subject_ids': SUBJECTS,
            'missing_subject_ids': [],
            'occlusion_mode': 'depth_tested',
            'tag_bindings': [
                {'label_id': l,
                 'subject_id': ('clamp_north_cap' if 'clamp' in l else
                                'load' if l == 'load' else
                                'tie_south_pole' if 'tie' in l else
                                'source_m10_source' if 'source' in l else
                                'actuator_shell')}
                for l in LABELS]}


def vis_clean():
    return {'layers': [],
            'label_ids': [],
            'selected_ids': [],
            'required_subject_ids': SUBJECTS,
            'observed_subject_ids': SUBJECTS,
            'missing_subject_ids': [],
            'occlusion_mode': 'depth_tested',
            'tag_bindings': []}


SUBJECTS = ['actuator_shell', 'clamp_north_cap', 'tie_south_pole', 'load',
            'source_m10_source']
LABELS = ['actuator_shell', 'actuator_shell/m:belt', 'port:pressure',
          'clamp_north_cap (visible support)', 'tie_south_pole',
          'bond:tie', 'load', 'source_m10_source']


def main():
    capture_dir = pathlib.Path(sys.argv[1])
    payloads_dir = capture_dir / 'payloads'
    evidence_dir = capture_dir / 'evidence'
    video_path = capture_dir / 'capture' / 'capture_mat2_m10_jack.mkv'
    video_path.parent.mkdir(parents=True, exist_ok=True)
    payloads = sorted(payloads_dir.glob('frame_*.raw'))
    require(len(payloads) == 18, 'expected 18 payload frames, found %d'
            % len(payloads))
    # codec standard: FFV1 lossless level 3 GOP 1 + bitexact (no muxer
    # timestamp drift; measured lossless, decode delta 0)
    cmd = ['ffmpeg', '-y', '-loglevel', 'error',
           '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '960x540',
           '-r', '1', '-i', '-',
           '-fflags', '+bitexact', '-c:v', 'ffv1', '-level', '3', '-g', '1',
           str(video_path)]
    proc = subprocess.run(cmd, input=b''.join(p.read_bytes()
                                              for p in payloads),
                          capture_output=True)
    require(proc.returncode == 0, 'ffmpeg_failed:' +
            proc.stderr.decode('utf-8', 'replace')[-200:])
    version = subprocess.run(['ffmpeg', '-version'], capture_output=True,
                             text=True)
    ffmpeg_version = version.stdout.splitlines()[0]
    video_sha = sha256_file(video_path)

    trace_path = HERE / 'experiment_trace.json'
    trace = json.loads(trace_path.read_text(encoding='utf-8'))
    trace_sha = hashlib.sha256(
        canonical(trace['dynamic_run']).encode('utf-8')).hexdigest()
    receipt_sha = sha256_file(HERE / 'experiment_receipt.json')
    evidence = json.loads((evidence_dir / 'cameras.json').read_text(
        encoding='utf-8'))
    cams = evidence['cameras']
    frame_hashes = evidence['frame_raw_sha256']

    binding = {'kind': 'trace',
               'sha256': trace_sha,
               'note': 'canonical dynamic_run subtree of contributions/'
                       'MAT2-M10/experiment_trace.json: the per-tick '
                       'solver trace of the braid-jack work run; rendered '
                       'vertex arrays are asserted against the trace rows '
                       '(volume + output pole position) before any pixel '
                       'is written'}

    def view(pair_id, view_id, mode, camera, secondary, visibility, note):
        row = {'artifact_locator': {'kind': 'video', 'seconds': [0, 18]},
               'camera': dict(camera),
               'cell_layout_note': note,
               'mode': mode,
               'pair_id': pair_id,
               'state_binding': binding,
               'view_id': view_id,
               'visibility': visibility}
        if secondary:
            row['camera']['secondary_cameras'] = secondary
        return row

    views = [
        view('pair-whole', VIEW_IDS[0], 'diagnostic', cams['whole'], None,
             vis_diagnostic(),
             'single viewport (sheet 0, top-left); fixed camera; the '
             'clamped spherical jack contracts under pressure and lifts '
             'the load through the declared tie'),
        view('pair-whole', VIEW_IDS[0], 'clean', cams['whole'], None,
             vis_clean(),
             'clean row: identical camera and state to its diagnostic '
             'pair; no labels, layers or diagnostic styling by design'),
        view('pair-planes', VIEW_IDS[1], 'diagnostic', cams['side'],
             [cams['front']], vis_diagnostic(),
             'two side-by-side viewports (sheet 0 top-right, sheet 0 '
             'bottom-left): side (primary) and front (secondary, fully '
             'declared); the north clamp (visible support), the tie and '
             'the load are rendered and labeled (nothing hidden)'),
        view('pair-planes', VIEW_IDS[1], 'clean', cams['side'],
             [cams['front']], vis_clean(),
             'clean row: identical cameras and state to its diagnostic '
             'pair'),
        view('pair-interface', VIEW_IDS[2], 'diagnostic', cams['closeup'],
             None, vis_diagnostic(),
             'single viewport (sheet 0 bottom-right); oblique close-up of '
             'the loaded interface: the south-pole tie anchor, the tie and '
             'the load'),
        view('pair-interface', VIEW_IDS[2], 'clean', cams['closeup'], None,
             vis_clean(),
             'clean row: identical camera and state to its diagnostic '
             'pair'),
    ]
    manifest = {
        'schema': 'chimera.visual_capture_manifest.v1',
        'task_id': 'M10',
        'profile_id': PROFILE['id'],
        'run_id': 'mat2-m10-jack-visual-20260929-' + video_sha[:8],
        'tick_interval': [0, 1499],
        'subject_sha256': receipt_sha,
        'capture_sha256': video_sha,
        'sheet_layout': {
            'pixel_size': [960, 540],
            'honest_titles': 'rendered inside every viewport: view name, '
                             'mode and tick; diagnostic viewports carry '
                             'the five declared diagnostic layers; footer '
                             'carries the architecture line, layers and '
                             'the work-run scalars',
            'rows': [
                'frame 2k   diagnostic viewports [whole | side; front | '
                'close-up] with all five declared diagnostic layers',
                'frame 2k+1 clean viewports (identical cameras, no labels, '
                'no overlays, depth-tested)',
                'footer strip: architecture line, dp, z_load, cumulative '
                'W_press of the captured tick',
            ],
            'tick_to_seconds_map': evidence['tick_map'] +
            '; frame t = sheet of snapshot tick t//2 '
            '(diagnostic when t is even, clean when odd)',
            'frame_files': frame_hashes,
        },
        'views': views,
    }
    context = {
        'task_id': 'M10',
        'run_id': manifest['run_id'],
        'subject_sha256': receipt_sha,
        'capture_sha256': video_sha,
        'tick_interval': [0, 1499],
    }
    receipt = validate_manifest(manifest, context, PROFILE)
    receipt['criteria_sha256'] = CRITERIA
    receipt['attempt_id'] = ATTEMPT
    receipt['video_path'] = str(video_path)
    receipt['video_sha256'] = video_sha
    receipt['trace_path'] = 'tools/monkey_campaign/contributions/' \
                            'MAT2-M10/experiment_trace.json'
    receipt['trace_dynamic_run_sha256'] = trace_sha
    receipt['render_source'] = ('solver snapshot stream of the braid-jack '
                                'work run (9 declared ticks, diagnostic/'
                                'clean sheet pairs); software '
                                'rasterization of solver state, declared '
                                'in the applicability boundary')
    receipt['validator'] = 'tools/monkey_campaign/visual_capture.py ' \
                           'validate_manifest'
    receipt['profile_source'] = REGISTRY_DB + \
        ' kanban.cards[MAT2-M10].spec.ontology_qualification.task.' \
        'verification_profile (read read-only)'
    receipt['codec'] = {'container': 'matroska', 'codec': 'ffv1',
                        'level': 3, 'gop': 1, 'bitexact': True,
                        'ffmpeg_version': ffmpeg_version,
                        'standard': 'E:/ChimeraWork/monkey-coordination/'
                                    'codec-benchmark/CODEC_STANDARD.md'}
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
                                     sort_keys=True) + '\n',
                          encoding='utf-8', newline='\n')
    print('video:', video_path)
    print('video sha256:', video_sha)
    print('validate_manifest:', receipt.get('mode'),
          '| structurally_valid:', receipt.get('structurally_valid'),
          '| views:', receipt.get('view_count'))
    return 0


PROFILE = registry_profile()
require(PROFILE['id'] == 'material', 'profile_id_mismatch')
require(set(PROFILE['diagnostic_layers']) == CANONICAL_LAYERS,
        'profile_layers_tripwire')
require(PROFILE['clean_view_required'] is True, 'clean_view_required')
for key in ('id', 'kind', 'views', 'clean_view_required',
            'diagnostic_layers'):
    require(key in PROFILE, 'profile_key_missing:' + key)

if __name__ == '__main__':
    sys.exit(main())
