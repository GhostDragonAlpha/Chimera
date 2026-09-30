"""MAT2-M09 capture gate (P4 heritage): frames are the determinism unit.

Decodes the bound FFV1 video with ffmpeg and proves the decoded frames
match the PINNED stills under the IDENTITY transform ONLY across the
explicit transform list (identity/vflip/hflip): identity diff == 0 pixels,
every non-identity transform > 0. Uses the frames pinned by the capture
manifest's sheet_layout.frame_files (indices independently recomputable:
frame i <-> capture tick list order). Skips (with a loud note) only when
ffmpeg is unavailable.

Resolution rule (the committed pins own the truth; no attempt paths):
  1. The committed capture_manifest.json pins the 12 stills by sha256
     (sheet_layout.frame_files, keyed by capture tick) and the video by
     capture_sha256; the committed capture_validation_receipt.json pins
     video_sha256 and locates the video file. The two pin sets must
     agree (capture_pin_conflict otherwise).
  2. The video locator is resolved without hardcoded attempt paths:
     absolute locators pass through; relative locators resolve against
     the coordination workspace found by walking up from this file to
     the nearest ancestor carrying an evidence-store/MANIFEST.json
     (schema chimera.evidence_store.v1). The file is accepted only if
     its sha256 equals the pinned video sha (capture_video_unresolvable
     / capture_video_sha_mismatch otherwise).
  3. The stills are accepted only from a directory whose frame_*.png
     set hashes 12/12 against the manifest pins in tick order.
     Candidates, in order: the optional argv[1] capture_dir (escape
     hatch; its frames/ subdirectory holds the stills, per the
     historical parameterized contract), then the frames/ sibling of
     the resolved video's generation directory. A resolvable candidate
     that fails the pin check is the named refusal
     capture_stills_generation_mismatch (exit 1) -- the gate never
     compares a decode against unverified live content; no resolvable
     candidate at all is capture_stills_dir_unresolvable.
Run: python -B test_capture_gate.py [capture_dir]
"""
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

TRANSFORMS = ('identity', 'vflip', 'hflip')
FRAME_COUNT = 12


def require(ok, code):
    if not ok:
        raise ValueError(code)


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b''):
            digest.update(chunk)
    return digest.hexdigest()


def evidence_store_root():
    """Nearest ancestor directory carrying the evidence-store vault."""
    for ancestor in (HERE, *HERE.parents):
        store = ancestor / 'evidence-store'
        manifest = store / 'MANIFEST.json'
        if not manifest.is_file():
            continue
        try:
            head = json.loads(manifest.read_text(encoding='utf-8'))
        except ValueError:
            continue
        if head.get('schema') == 'chimera.evidence_store.v1':
            return store
    return None


def resolve_video(receipt):
    """Resolve the receipt's video locator to an existing file."""
    locator = pathlib.Path(str(receipt['video_path']))
    candidates = []
    if locator.is_absolute():
        candidates.append(locator)
    else:
        store = evidence_store_root()
        if store is not None:
            candidates.append(store.parent / locator)
            candidates.append(store / locator)
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    require(False, 'capture_video_unresolvable')


def stills_pin_match(stills_dir, pins):
    """True iff stills_dir holds FRAME_COUNT frame_*.png files whose
    sha256 values equal the manifest pins in tick order."""
    frames = sorted(stills_dir.glob('frame_*.png'))
    if len(frames) != FRAME_COUNT:
        return False
    tick_order = sorted(pins, key=int)
    return all(sha256_file(path) == pins[tick]
               for path, tick in zip(frames, tick_order))


def resolve_stills(pins, video, override):
    """Resolve the stills directory from the committed pins only.
    The optional override is a capture_dir whose frames/ subdirectory
    holds the stills (the historical parameterized contract)."""
    if override is not None:
        stills = override / 'frames'
        require(stills.is_dir(), 'capture_stills_dir_unresolvable')
        require(stills_pin_match(stills, pins),
                'capture_stills_generation_mismatch')
        return stills
    default = video.parent.parent / 'frames'
    require(default.is_dir(), 'capture_stills_dir_unresolvable')
    require(stills_pin_match(default, pins),
            'capture_stills_generation_mismatch')
    return default


def main():
    from PIL import Image
    import numpy as np
    ffmpeg = shutil.which('ffmpeg')
    if ffmpeg is None:
        print('SKIP: ffmpeg not on PATH (gate must be re-run where it is)')
        return 0
    override = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else None
    manifest = json.loads((HERE / 'capture_manifest.json').read_text(
        encoding='utf-8'))
    receipt = json.loads((HERE / 'capture_validation_receipt.json')
                         .read_text(encoding='utf-8'))
    pins = manifest['sheet_layout']['frame_files']
    require(len(pins) == FRAME_COUNT, 'capture_pin_count_mismatch')
    require(receipt['video_sha256'] == manifest['capture_sha256'],
            'capture_pin_conflict')
    video = resolve_video(receipt)
    require(sha256_file(video) == receipt['video_sha256'],
            'capture_video_sha_mismatch')
    stills_dir = resolve_stills(pins, video, override)
    frames = sorted(stills_dir.glob('frame_*.png'))
    require(len(frames) == FRAME_COUNT, 'frame_count_mismatch')
    print('capture source: video ' + video.as_posix())
    print('capture source: stills ' + stills_dir.as_posix())
    worst_identity = 0
    min_nonidentity = None
    with tempfile.TemporaryDirectory() as td:
        td = pathlib.Path(td)
        subprocess.run([ffmpeg, '-y', '-loglevel', 'error',
                        '-i', str(video), str(td / 'dec_%02d.png')],
                       check=True)
        dec = sorted(td.glob('dec_*.png'))
        require(len(dec) == 12, 'decode_count_mismatch')
        for src, dec_p in zip(frames, dec):
            a = np.asarray(Image.open(src).convert('RGB'), dtype=np.int16)
            b = np.asarray(Image.open(dec_p).convert('RGB'), dtype=np.int16)
            require(a.shape == b.shape, 'decode_shape_mismatch')
            diffs = {}
            diffs['identity'] = int((np.abs(a - b).max(axis=-1) > 0).sum())
            diffs['vflip'] = int((np.abs(a - b[::-1]).max(axis=-1)
                                  > 0).sum())
            diffs['hflip'] = int((np.abs(a - b[:, ::-1]).max(axis=-1)
                                  > 0).sum())
            require(diffs['identity'] == 0,
                    f'decode_identity_diff_{diffs["identity"]}_px')
            nonid = min(diffs[t] for t in TRANSFORMS if t != 'identity')
            require(nonid > 0, 'nonidentity_transform_not_discriminating')
            worst_identity = max(worst_identity, diffs['identity'])
            min_nonidentity = nonid if min_nonidentity is None \
                else min(min_nonidentity, nonid)
    print('capture gate green: identity diff 0 px on all 12 decoded '
          f'frames; minimum non-identity diff {min_nonidentity} px '
          '(identity-only match proven)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
