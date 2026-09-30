"""MAT2-M09 capture manifest builder (single-artifact video binding).

Assembles the declared FFV1 video (codec standard: -fflags +bitexact, the
campaign codec addendum; lossless, muxer-timestamp-pinned), builds the
chimera.visual_capture_manifest.v1 manifest + context (task_id SHORT form
"M09") and validates them with the registry validator using THE profile
object read READ-ONLY from
E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3
kanban.cards[MAT2-M09].spec.ontology_qualification.task
.verification_profile (never hand-copied). Every hash derives from disk
bytes. Records the ffmpeg version line in the receipt.
Run: python -B make_capture.py <attempt_capture_dir> <ffmpeg_path>
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
# visual_capture.py is shared campaign infrastructure outside the sparse
# contribution prefix (the sealed M08 make_capture imports it the same way)
sys.path.insert(0, 'E:/PythonChimera/tools/monkey_campaign')
sys.path.insert(0, str(HERE))

import assembly as asm  # noqa: E402
from visual_capture import validate_manifest  # noqa: E402

FPS = 1
REGISTRY_DB = 'E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3'
TICK_MAP = ('1 tick = 1/300 s simulated; frames are the declared capture '
            'ticks 0,10,21,30,44,45,60,66,70,74,85,89 at 1 video second '
            'per frame (Amendment A1 schedule)')
SUBJECTS = ['bone_a', 'bone_b', 'ground']
LABELS = ['bone_a (rod, 0.030 kg)', 'bone_b (tapered wedge, 0.018 kg)',
          'ground (pinned support)', 'port:head bone_a', 'port:head bone_b',
          'ligament:strap_l1', 'capsule:sleeve_c1',
          'contact:joint_faces marker']


def registry_profile():
    con = sqlite3.connect(f'file:{REGISTRY_DB}?mode=ro', uri=True)
    try:
        payload = con.execute(
            'SELECT payload FROM state WHERE id=1').fetchone()[0]
    finally:
        con.close()
    reg = json.loads(payload)
    card = reg['kanban']['cards']['MAT2-M09']
    profile = card['spec']['ontology_qualification']['task'][
        'verification_profile']
    # A4 (visual-gate F4): carry the exact payload identity the profile
    # object was parsed from, so the snapshot is verifiable provenance
    return profile, hashlib.sha256(payload.encode('utf-8')).hexdigest()


PROFILE, REGISTRY_PAYLOAD_SHA256 = registry_profile()


def profile_snapshot():
    """A4 (F4): the frozen 'registry profile snapshot + provenance
    written to evidence' line, made real — the full profile object plus
    its read-only provenance, deterministic (no wall-clock fields).
    Round-2 law: the DURABLE identity is the canonical profile-object
    sha (the live single-row registry store rewrites on coordinator
    writes, so whole-store payload shas are capture-time-only)."""
    canon = json.dumps(PROFILE, sort_keys=True,
                       separators=(',', ':'), ensure_ascii=False)
    return {
        'schema': 'chimera.m09_registry_profile_snapshot.v1',
        'profile': PROFILE,
        'provenance': {
            'source_db': REGISTRY_DB,
            'selector': 'kanban.cards[MAT2-M09].spec.ontology_qualification'
                        '.task.verification_profile',
            'access_mode': 'sqlite read-only (file:...?mode=ro URI)',
            'profile_object_sha256':
                hashlib.sha256(canon.encode('utf-8')).hexdigest(),
            'profile_object_canonicalization':
                'sha256 of json.dumps(profile, sort_keys=True, '
                'separators=(",",":"), ensure_ascii=False)',
            'payload_sha256': REGISTRY_PAYLOAD_SHA256,
            'payload_note': ('whole-store payload_sha256 is CAPTURE-TIME-ONLY '
                             'and NOT re-verifiable: the live registry '
                             'single-row store rewrites on coordinator writes '
                             '(observed 30 min post-commit). The durable '
                             'identity is profile_object_sha256 above - '
                             're-verify by re-reading the registry read-only, '
                             'extracting the same profile object, '
                             'canonicalizing identically, and comparing shas.'),
            'used_by': ('validate_manifest(manifest, context, PROFILE) '
                        'in this module; PROFILE is never hand-copied'),
        },
    }


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
                {'label_id': l,
                 'subject_id': ('ground' if 'ground' in l else
                                'bone_a' if 'bone_a' in l or
                                'strap_l1' in l else 'bone_b')}
                for l in labels]}


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
        'capture_mat2_m09_assembly_20260929.mkv'
    video_path.parent.mkdir(parents=True, exist_ok=True)
    frames = sorted(frames_dir.glob('frame_*.png'))
    n_frames = 12
    assert len(frames) == n_frames, \
        f'expected {n_frames} frames, found {len(frames)}'
    cmd = [ffmpeg, '-y', '-loglevel', 'error', '-fflags', '+bitexact',
           '-framerate', str(FPS), '-i', str(frames_dir / 'frame_%02d.png'),
           '-c:v', 'ffv1', '-level', '3', '-g', '1', str(video_path)]
    subprocess.run(cmd, check=True)
    ver = subprocess.run([ffmpeg, '-hide_banner', '-version'],
                         capture_output=True, text=True)
    ffmpeg_version = ver.stdout.splitlines()[0] if ver.stdout else 'unknown'
    video_sha = asm.sha256_file(video_path)
    subject_sha = asm.sha256_file(HERE / 'experiment_receipt.json')
    trace_sha = asm.sha256_file(HERE / 'experiment_trace.json')
    run_id = 'mat2-m09-assembly-visual-20260929-' + video_sha[:8]

    cams = json.loads((evidence_dir / 'cameras.json').read_text('utf-8'))
    frame_hashes = json.loads(
        (evidence_dir / 'frame_hashes.json').read_text('utf-8'))
    sources = json.loads(
        (evidence_dir / 'frame_sources.json').read_text('utf-8'))
    cam_whole = cams['whole:diagnostic'][0]
    cam_side = cams['side:diagnostic'][0]
    cam_front = cams['front:diagnostic'][0]
    cam_iface = cams['closeup:diagnostic'][0]
    assert cam_whole == cams['whole:clean'][0]
    assert cam_side == cams['side:clean'][0]
    assert cam_front == cams['front:clean'][0]
    assert cam_iface == cams['closeup:clean'][0]

    binding = {'kind': 'trace', 'sha256': trace_sha,
               'note': 'sha256 of contributions/MAT2-M09/'
                       'experiment_trace.json; every frame was rendered '
                       'from a deterministic re-simulation whose per-tick '
                       'state_hash equals the committed trace row bitwise '
                       '(frame_sources.json); the connective material is '
                       'the authored ligament/capsule straps and the M06 '
                       'joint contact marker'}

    def view(pair_id, view_id, mode, camera, secondary, visibility, note):
        row = {'artifact_locator': {'kind': 'video',
                                    'seconds': [0, n_frames]},
               'camera': camera,
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
        view('pair-whole', PROFILE['views'][0], 'diagnostic', cam_whole,
             None, vis_diagnostic(),
             'single viewport (sheet column 1); fixed camera; the bones '
             'fall separately, are assembled by the authored ligament/'
             'capsule straps, pressed through the joint contact, held by '
             'the ligament under pull, then released and independent'),
        view('pair-whole', PROFILE['views'][0], 'clean', cam_whole, None,
             vis_clean(),
             'clean row: identical camera and state to its diagnostic '
             'pair; no labels, layers or diagnostic styling by design'),
        view('pair-planes', PROFILE['views'][1], 'diagnostic', cam_side,
             [cam_front], vis_diagnostic(),
             'two side-by-side viewports (sheet columns 2-3): side '
             '(primary) and front (secondary, fully declared with the '
             'same 17 camera fields); the pinned ground support is '
             'rendered and labeled (nothing hidden)'),
        view('pair-planes', PROFILE['views'][1], 'clean', cam_side,
             [cam_front], vis_clean(),
             'clean row: identical cameras and state to its diagnostic '
             'pair'),
        view('pair-interface', PROFILE['views'][2], 'diagnostic',
             cam_iface, None,
             vis_diagnostic(['bone_a', 'bone_b']),
             'single viewport (sheet column 4); oblique close-up of the '
             'loaded joint interface: contact marker, ligament (purple) '
             'and capsule (red) straps — the ligament renders as a '
             'declared 7-px purple underlay beneath the 3-px red capsule '
             'core, both on the port:head axis (Amendment A4) — '
             'area-scaled element force arrows'),
        view('pair-interface', PROFILE['views'][2], 'clean', cam_iface,
             None, vis_clean(),
             'clean row: identical camera and state to its diagnostic '
             'pair'),
    ]
    manifest = {
        'schema': 'chimera.visual_capture_manifest.v1',
        'task_id': 'M09',
        'profile_id': PROFILE['id'],
        'run_id': run_id,
        'tick_interval': [0, 89],
        'subject_sha256': subject_sha,
        'capture_sha256': video_sha,
        'sheet_layout': {
            'pixel_size': [2560, 840],
            'honest_titles': 'rendered inside every viewport: view name, '
                             'mode and tick; diagnostic viewports carry '
                             'the five declared diagnostic layers, layer 1 '
                             'rendered as navy port:head/triangle ID '
                             'labels (Amendment A4: rendered, not only '
                             'declared); footer carries the R/bound ratio '
                             'and the bind/release ticks',
            'rows': [
                'top    diagnostic viewports [whole | side | front | '
                'close-up] with all five declared diagnostic layers',
                'middle clean viewports (identical cameras, no labels, '
                'no overlays, depth-tested)',
                'bottom ligament/capsule/gap trace strip + footer',
            ],
            'tick_to_seconds_map': TICK_MAP + '; frame t = capture tick t',
            'frame_files': frame_hashes,
        },
        'views': views,
    }
    context = {'task_id': 'M09',
               'run_id': run_id,
               'subject_sha256': subject_sha,
               'capture_sha256': video_sha,
               'tick_interval': [0, 89]}
    receipt = validate_manifest(manifest, context, PROFILE)
    receipt['video_path'] = str(video_path)
    receipt['video_sha256'] = video_sha
    receipt['subject_path'] = 'tools/monkey_campaign/contributions/' \
                              'MAT2-M09/experiment_receipt.json'
    receipt['subject_sha256'] = subject_sha
    receipt['trace_path'] = 'tools/monkey_campaign/contributions/' \
                            'MAT2-M09/experiment_trace.json'
    receipt['trace_sha256'] = trace_sha
    receipt['frame_count'] = len(frame_hashes)
    receipt['frame_sources'] = sources
    receipt['ffmpeg_version'] = ffmpeg_version
    receipt['codec'] = ('FFV1 level 3 gop 1 in matroska with '
                        '-fflags +bitexact (campaign codec standard: '
                        're-encodes byte-reproducible; decode verified '
                        'lossless by the standard measurement)')
    receipt['render_source'] = ('deterministic re-simulation of '
                                'AssemblyRun with bitwise state_hash '
                                'equality against experiment_trace.json '
                                'at every capture tick; software '
                                'rasterization of solver state')
    receipt['validator'] = ('tools/monkey_campaign/visual_capture.py '
                            'validate_manifest')
    receipt['profile_source'] = REGISTRY_DB + ' kanban.cards[MAT2-M09]' \
        '.spec.ontology_qualification.task.verification_profile ' \
        '(read read-only)'
    receipt['profile_snapshot'] = ('registry_profile_snapshot.json '
                                   '(card dir + evidence dir; full '
                                   'profile object + provenance, '
                                   'Amendment A4)')
    receipt['registry_payload_sha256'] = REGISTRY_PAYLOAD_SHA256
    receipt['limits'] = ('Structural camera-metadata validation only; '
                         'independent image/physics review remains '
                         'mandatory.')
    for target, payload in (
            (HERE / 'capture_manifest.json', manifest),
            (HERE / 'capture_context.json', context),
            (HERE / 'capture_validation_receipt.json', receipt),
            (HERE / 'registry_profile_snapshot.json', profile_snapshot()),
            (evidence_dir / 'capture_manifest.json', manifest),
            (evidence_dir / 'capture_context.json', context),
            (evidence_dir / 'validation_receipt.json', receipt),
            (evidence_dir / 'registry_profile_snapshot.json',
             profile_snapshot())):
        target.write_text(json.dumps(payload, indent=1, ensure_ascii=False,
                                     sort_keys=True) + '\n',
                          encoding='utf-8')
    print('video:', video_path)
    print('video sha256:', video_sha)
    print('ffmpeg:', ffmpeg_version)
    print('validate_manifest:', receipt['mode'],
          '| structurally_valid:', receipt['structurally_valid'],
          '| views:', receipt['view_count'])
    return 0


if __name__ == '__main__':
    sys.exit(main())
