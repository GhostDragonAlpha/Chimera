"""MAT2-M03 capture manifest builder: assembles the video from the rendered
frames, builds the chimera.visual_capture_manifest.v1 manifest + context
(task_id SHORT form "M03") and validates them with the registry validator.

Every hash is derived from the files on disk (no hand-typed values).
Run from this directory:
    python -B make_capture.py <attempt_capture_dir> <ffmpeg_path>
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, 'E:/PythonChimera/tools/monkey_campaign')

import pressure_membrane as pm  # noqa: E402
from visual_capture import validate_manifest  # noqa: E402

TICK_INTERVAL = [0, 23]
FPS = 1

PROFILE = {
    'id': 'material',
    'kind': 'motion',
    'subject': 'Actual material state, membrane surfaces and physical '
               'interfaces',
    'views': ['whole experiment at fixed distance',
              'orthogonal side and front',
              'oblique close-up of the loaded interface'],
    'clean_view_required': True,
    'diagnostic_layers': ['stable membrane/triangle/port IDs',
                          'pressure and area-scaled force vectors',
                          'rest/current geometry and material directions',
                          'contact/bond state',
                          'energy/work and simulation tick'],
}

SUBJECTS = ['membrane', 'm02_tetra']
LABELS = ['membrane', 'm02_tetra', 'port:pressure_inlet',
          'm02_tetra/t0', 'm02_tetra/t1', 'm02_tetra/t2', 'm02_tetra/t3']


def vis_diagnostic():
    return {'layers': list(PROFILE['diagnostic_layers']),
            'label_ids': list(LABELS),
            'selected_ids': list(SUBJECTS),
            'required_subject_ids': list(SUBJECTS),
            'observed_subject_ids': list(SUBJECTS),
            'missing_subject_ids': [],
            'occlusion_mode': 'depth_tested',
            'tag_bindings': [{'label_id': 'membrane', 'subject_id': 'membrane'},
                             {'label_id': 'm02_tetra', 'subject_id':
                              'm02_tetra'},
                             {'label_id': 'port:pressure_inlet',
                              'subject_id': 'membrane'},
                             {'label_id': 'm02_tetra/t0',
                              'subject_id': 'm02_tetra'},
                             {'label_id': 'm02_tetra/t1',
                              'subject_id': 'm02_tetra'},
                             {'label_id': 'm02_tetra/t2',
                              'subject_id': 'm02_tetra'},
                             {'label_id': 'm02_tetra/t3',
                              'subject_id': 'm02_tetra'}]}


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
        'capture_mat2_m03_pressure_20260928.mkv'
    video_path.parent.mkdir(parents=True, exist_ok=True)
    frames = sorted(frames_dir.glob('frame_*.png'))
    assert len(frames) == 24, f'expected 24 frames, found {len(frames)}'
    cmd = [ffmpeg, '-y', '-loglevel', 'error', '-framerate', str(FPS),
           '-i', str(frames_dir / 'frame_%02d.png'),
           '-c:v', 'libx264', '-preset', 'veryslow', '-crf', '18',
           '-pix_fmt', 'yuv420p', str(video_path)]
    subprocess.run(cmd, check=True)
    video_sha = pm.sha256_file(video_path)
    subject_sha = pm.sha256_file(HERE / 'pressure_state.json')
    trace_sha = pm.sha256_file(HERE / 'pressure_trace.json')
    run_id = 'mat2-m03-pressure-visual-20260928-' + video_sha[:8]

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
               'note': 'sha256 of contributions/MAT2-M03/pressure_trace.json: '
                       'the per-tick solver trace (delta_p, volume, area, '
                       'energy ledger with measured constraint-projection '
                       'residual, COM drift, per-tick state hash rendered in '
                       'every frame footer); render positions are a replay '
                       'asserted equal to the committed trace volumes'}

    def view(pair_id, view_id, mode, camera, secondary, visibility, note):
        row = {
            'artifact_locator': {'kind': 'video', 'seconds': [0, 24]},
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
        view('pair-whole', VIEW := PROFILE['views'][0], 'diagnostic',
             cam_whole, None, vis_diagnostic(),
             'single viewport (sheet column 1); fixed camera; the membrane '
             'inflates/deflates under the declared source beside the M02 tetra '
             'traction demonstrator'),
        view('pair-whole', VIEW, 'clean', cam_whole, None, vis_clean(),
             'clean row: identical camera and state to its diagnostic pair; '
             'no labels, layers or diagnostic styling by design'),
        view('pair-planes', PROFILE['views'][1], 'diagnostic', cam_side,
             [cam_front], vis_diagnostic(),
             'two side-by-side viewports (sheet columns 2-3): side (primary '
             'camera) and front (secondary, fully declared with the same 16 '
             'camera fields)'),
        view('pair-planes', PROFILE['views'][1], 'clean', cam_side,
             [cam_front], vis_clean(),
             'clean row: identical cameras and state to its diagnostic pair'),
        view('pair-interface', PROFILE['views'][2], 'diagnostic', cam_iface,
             None, vis_diagnostic(),
             'single viewport (sheet column 4); oblique close-up of the M02 '
             'tetra loaded interface; per-triangle arrows grow with '
             'delta-p and scale with triangle area (slant face A=0.0087 '
             'longer than leg faces A=0.0050 at every tick)'),
        view('pair-interface', PROFILE['views'][2], 'clean', cam_iface, None,
             vis_clean(),
             'clean row: identical camera and state to its diagnostic pair'),
    ]

    manifest = {
        'schema': 'chimera.visual_capture_manifest.v1',
        'task_id': 'M03',
        'profile_id': 'material',
        'run_id': run_id,
        'tick_interval': TICK_INTERVAL,
        'subject_sha256': subject_sha,
        'capture_sha256': video_sha,
        'sheet_layout': {
            'pixel_size': [2560, 840],
            'honest_titles': 'rendered inside every viewport: view_id, mode, '
                             'tick and delta-p; every diagnostic viewport '
                             'carries the layer row, the state line (volume, '
                             'pressure work, COM drift) and the port/state '
                             'hash; footer carries frame_id, the tick-to-'
                             'seconds mapping and the state hash',
            'rows': [
                'top    diagnostic viewports [whole | side | front | '
                'close-up] with all five declared diagnostic layers',
                'middle clean viewports (identical cameras, no labels, no '
                'overlays, depth-tested)',
                'bottom pressure / volume / cumulative work traces + footer',
            ],
            'tick_to_seconds_map': '1 tick = 1/300 s simulated, replayed at '
                                   '1 video second per tick (slow motion '
                                   'x300); frame t = tick t',
            'frame_files': frame_hashes,
        },
        'views': views,
    }
    context = {
        'task_id': 'M03',
        'run_id': run_id,
        'subject_sha256': subject_sha,
        'capture_sha256': video_sha,
        'tick_interval': TICK_INTERVAL,
    }
    receipt = validate_manifest(manifest, context, PROFILE)
    receipt['video_path'] = str(video_path)
    receipt['video_sha256'] = video_sha
    receipt['subject_path'] = 'tools/monkey_campaign/contributions/MAT2-M03/' \
                              'pressure_state.json'
    receipt['subject_sha256'] = subject_sha
    receipt['trace_path'] = 'tools/monkey_campaign/contributions/MAT2-M03/' \
                            'pressure_trace.json'
    receipt['trace_sha256'] = trace_sha
    receipt['frame_count'] = len(frame_hashes)
    receipt['validator'] = 'tools/monkey_campaign/visual_capture.py ' \
                           'validate_manifest'
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


if __name__ == '__main__':
    sys.exit(main())
