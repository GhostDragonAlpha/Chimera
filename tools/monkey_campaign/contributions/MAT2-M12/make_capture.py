"""MAT2-M12 capture manifest builder: encodes the rendered payload frames
(rawvideo rgb24 pipe) into the single gate-bound video (FFV1 lossless,
level 3, GOP 1, +bitexact per the campaign codec standard), builds the
chimera.visual_capture_manifest.v1 manifest + context (task_id SHORT form
"M12") and validates them with the registry validator, using the REGISTRY
profile object read READ-ONLY from
E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3
kanban.cards[MAT2-M12].spec.ontology_qualification.task.verification_profile.

Every hash is derived from files on disk (no hand-typed values).
Single-artifact binding (G8/P8): ONE video; capture_sha256 = that file's
sha256; every view row is an artifact_locator of kind video on it; every
view row carries the same state_binding.sha256 (the whole-file trace
binding, which contains BOTH resolutions' runs); the per-resolution
canonical subtree shas are recorded in the evidence bundle and the
validation receipt (state-hash uniformity: view toggles never change the
physical state hash).
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

from visual_capture import validate_manifest  # noqa: E402

REGISTRY_DB = 'E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3'
CANONICAL_LAYERS = {  # loud tripwire only; never supplies values
    'stable membrane/triangle/port IDs',
    'pressure and area-scaled force vectors',
    'rest/current geometry and material directions',
    'contact/bond state',
    'energy/work and simulation tick',
}
CRITERIA = ('1e98a4f4465d4a50f21ce5c1d42b5ab51e9a7f96482f8f711d2c66ca4c5'
            '3b5b7')
ATTEMPT = '22954da7b9704483960b563273e77b4a'
VIEW_IDS = ['whole experiment at fixed distance',
            'orthogonal side and front',
            'oblique close-up of the loaded interface']
FRAME_COUNT = 24


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
    card = reg['kanban']['cards']['MAT2-M12']
    profile = card['spec']['ontology_qualification']['task'][
        'verification_profile']
    return profile


def vis_diagnostic(labels, subjects):
    return {'layers': list(PROFILE['diagnostic_layers']),
            'label_ids': list(labels),
            'selected_ids': list(subjects),
            'required_subject_ids': list(subjects),
            'observed_subject_ids': list(subjects),
            'missing_subject_ids': [],
            'occlusion_mode': 'mixed',
            'tag_bindings': [
                {'label_id': l,
                 'subject_id': ('clamp_ring' if 'clamp' in l else
                                'load_surrogate' if 'load' in l else
                                'foot' if 'T4' in l else
                                'humerus' if 'T1' in l else
                                'ulna' if 'T2' in l else
                                'radius' if 'T3' in l else
                                'source_m11_source' if 'source' in l else
                                'tissue_bladder')}
                for l in labels]}


def vis_clean():
    return {'layers': [],
            'label_ids': [],
            'selected_ids': [],
            'required_subject_ids': SUBJECTS,
            'observed_subject_ids': SUBJECTS,
            'missing_subject_ids': [],
            'occlusion_mode': 'depth_tested',
            'tag_bindings': []}


SUBJECTS = ['tissue_bladder', 'clamp_ring', 'humerus', 'ulna', 'radius',
            'foot', 'load_surrogate', 'source_m11_source']
LABELS = ['tissue_bladder', 'clamp_ring (visible support)',
          'chain T1 humerus', 'chain T2 ulna', 'chain T3 radius',
          'chain T4 foot(hand)', 'bond:load_surrogate',
          'source_m11_source']
CLOSEUP_SUBJECTS = ['tissue_bladder', 'humerus', 'ulna', 'radius', 'foot']
CLOSEUP_LABELS = ['tissue_bladder', 'chain T1 humerus', 'chain T2 ulna',
                  'chain T3 radius', 'chain T4 foot(hand)']


def main():
    capture_dir = pathlib.Path(sys.argv[1])
    payloads_dir = capture_dir / 'payloads'
    evidence_dir = capture_dir / 'evidence'
    video_path = HERE / 'capture' / 'capture_mat2_m12_lod.mkv'
    video_path.parent.mkdir(parents=True, exist_ok=True)
    payloads = sorted(payloads_dir.glob('frame_*.raw'))
    require(len(payloads) == FRAME_COUNT,
            'expected %d payload frames, found %d'
            % (FRAME_COUNT, len(payloads)))
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
    trace_file_sha = sha256_file(trace_path)
    res_subtree_shas = {
        res: hashlib.sha256(canonical(
            trace['runs'][res]).encode('utf-8')).hexdigest()
        for res in ('coarse', 'reference')}
    receipt_sha = sha256_file(HERE / 'experiment_receipt.json')
    evidence = json.loads((evidence_dir / 'capture_evidence.json').read_text(
        encoding='utf-8'))
    cams = evidence['cameras']
    frame_hashes = evidence['frame_raw_sha256']

    binding = {'kind': 'trace',
               'sha256': trace_file_sha,
               'note': 'whole-file binding of contributions/MAT2-M12/'
                       'experiment_trace.json (the per-tick solver traces '
                       'of BOTH resolutions loaded runs); rendered '
                       'vertex/chain arrays are asserted against the trace '
                       'rows before any pixel is written; the per-resolution '
                       'canonical subtree shas are recorded in '
                       'resolution_bindings and in '
                       'capture_validation_receipt.json'}

    def view(pair_id, view_id, mode, camera, secondary, visibility, note):
        row = {'artifact_locator': {'kind': 'video', 'seconds': [0, 24]},
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
        view('pair-whole', VIEW_IDS[0], 'diagnostic', cams['coarse']['whole'],
             [cams['reference']['whole']], vis_diagnostic(LABELS, SUBJECTS),
             'two viewports on the diagnostic frames of this pair: coarse '
             '(primary, sheet even frames) and reference (secondary, fully '
             'declared); fixed cameras; the vessel hangs from the declared '
             'clamp, pressurization descends the free pole and presses the '
             'foot on the ground through the tension chain'),
        view('pair-whole', VIEW_IDS[0], 'clean', cams['coarse']['whole'],
             [cams['reference']['whole']], vis_clean(),
             'clean row: identical cameras and state to its diagnostic '
             'pair; no labels, layers or diagnostic styling by design'),
        view('pair-planes', VIEW_IDS[1], 'diagnostic',
             cams['coarse']['side'], [cams['coarse']['front'],
                                      cams['reference']['side'],
                                      cams['reference']['front']],
             vis_diagnostic(LABELS, SUBJECTS),
             'four side/front viewports across the pair frames (coarse '
             'side primary; coarse front, reference side and reference '
             'front secondary, fully declared): the clamp (visible '
             'support), the chain and the surrogate load are rendered and '
             'labeled (nothing hidden)'),
        view('pair-planes', VIEW_IDS[1], 'clean', cams['coarse']['side'],
             [cams['coarse']['front'], cams['reference']['side'],
              cams['reference']['front']], vis_clean(),
             'clean row: identical cameras and state to its diagnostic '
             'pair'),
        view('pair-interface', VIEW_IDS[2], 'diagnostic',
             cams['coarse']['closeup'], [cams['reference']['closeup']],
             vis_diagnostic(CLOSEUP_LABELS, CLOSEUP_SUBJECTS),
             'oblique close-up of the loaded interface at both '
             'resolutions: the free pole, the chain ties, the foot '
             'contact element and the ground (pixel-gated by the '
             'camera-consistency probe)'),
        view('pair-interface', VIEW_IDS[2], 'clean',
             cams['coarse']['closeup'], [cams['reference']['closeup']],
             vis_clean(),
             'clean row: identical cameras and state to its diagnostic '
             'pair'),
    ]
    manifest = {
        'schema': 'chimera.visual_capture_manifest.v1',
        'task_id': 'M12',
        'profile_id': PROFILE['id'],
        'run_id': 'mat2-m12-lod-visual-20260930-' + video_sha[:8],
        'tick_interval': [0, 1350],
        'subject_sha256': receipt_sha,
        'capture_sha256': video_sha,
        'resolution_bindings': res_subtree_shas,
        'sheet_layout': {
            'pixel_size': [960, 540],
            'honest_titles': 'rendered inside every viewport: view name, '
                             'mode, resolution and tick; diagnostic '
                             'viewports carry the five declared diagnostic '
                             'layers; footer carries the LOD comparison '
                             'line, layers and the run scalars',
            'rows': [
                'frame si*4 + res*2 + 0 diagnostic viewports [whole | '
                'side; front | close-up] with all five declared '
                'diagnostic layers',
                'frame si*4 + res*2 + 1 clean viewports (identical '
                'cameras, no labels, no overlays, depth-tested)',
                'footer strip: LOD comparison line and the layer list',
            ],
            'tick_to_seconds_map': evidence['tick_map'] +
            '; frame t = snapshot tick (t//4) of resolution '
            'coarse|reference (t//2 % 2); diagnostic when t is even, '
            'clean when odd',
            'frame_files': {str(v['frame_index']): v['raw_payload_sha256']
                            for v in frame_hashes.values()},
        },
        'views': views,
    }
    context = {
        'task_id': 'M12',
        'run_id': manifest['run_id'],
        'subject_sha256': receipt_sha,
        'capture_sha256': video_sha,
        'tick_interval': [0, 1350],
    }
    receipt = validate_manifest(manifest, context, PROFILE)
    require(receipt['structurally_valid'] is True,
            'manifest_structurally_invalid')
    receipt['frame_count'] = len(payloads)
    receipt['subject_path'] = 'experiment_receipt.json'
    receipt['trace_sha256'] = trace_file_sha
    receipt['schema'] = 'chimera.capture_validation_receipt.v1'
    receipt['criteria_sha256'] = CRITERIA
    receipt['attempt_id'] = ATTEMPT
    receipt['video_path'] = str(video_path)
    receipt['video_sha256'] = video_sha
    receipt['trace_path'] = 'tools/monkey_campaign/contributions/' \
                            'MAT2-M12/experiment_trace.json'
    receipt['resolution_bindings'] = res_subtree_shas
    receipt['render_source'] = ('solver snapshot stream of BOTH '
                                'resolutions loaded runs (6 declared '
                                'ticks, diagnostic/clean sheet pairs); '
                                'software rasterization of solver state, '
                                'declared in the applicability boundary')
    receipt['validator'] = 'tools/monkey_campaign/visual_capture.py ' \
                           'validate_manifest'
    receipt['profile_source'] = REGISTRY_DB + \
        ' kanban.cards[MAT2-M12].spec.ontology_qualification.task.' \
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
