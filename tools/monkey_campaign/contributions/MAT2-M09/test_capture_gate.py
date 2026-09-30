"""MAT2-M09 capture gate (P4 heritage): frames are the determinism unit.

Decodes the bound FFV1 video with ffmpeg and proves the decoded frames
match the committed stills under the IDENTITY transform ONLY across the
explicit transform list (identity/vflip/hflip): identity diff == 0 pixels,
every non-identity transform > 0. Uses the frames recorded in the capture
manifest's sheet_layout.frame_files (indices independently recomputable:
frame i <-> capture tick list order). Skips (with a loud note) only when
ffmpeg is unavailable.

Pin-first (regression V2 red fix, the F03 live-pointer class): the live
stills are NOT trusted content. Before any decode comparison every live
still is sha256-verified against the committed capture_manifest.json
sheet_layout.frame_files pins (tick order) and the bound video against
capture_validation_receipt.json video_sha256 == capture_manifest.json
capture_sha256; drift raises the named refusals
capture_stills_generation_mismatch_* / video_pin_mismatch instead of an
unnamed pixel-diff error. The default capture dir is the sha-registered
evidence-store home of the pinned generation (the pre-fix default pointed
at the superseded fa6dbcc attempt-space stills left behind by the #270
capture re-pin).
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

CAPTURE_DIR = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else \
    pathlib.Path('E:/ChimeraWork/monkey-coordination/'
                 'evidence-store/MAT2-M09/visual')
TRANSFORMS = ('identity', 'vflip', 'hflip')


def require(ok, code):
    if not ok:
        raise ValueError(code)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def main():
    from PIL import Image
    import numpy as np
    ffmpeg = shutil.which('ffmpeg')
    if ffmpeg is None:
        print('SKIP: ffmpeg not on PATH (gate must be re-run where it is)')
        return 0
    manifest = json.loads((HERE / 'capture_manifest.json').read_text(
        encoding='utf-8'))
    receipt = json.loads((HERE / 'capture_validation_receipt.json')
                         .read_text(encoding='utf-8'))
    frames = sorted((CAPTURE_DIR / 'frames').glob('frame_*.png'))
    require(len(frames) == 12, 'frame_count_mismatch')
    video = pathlib.Path(receipt['video_path'])
    require(video.exists(), 'video_missing')
    require(sha256_file(video) == receipt['video_sha256'] ==
            manifest['capture_sha256'], 'video_pin_mismatch')
    pins = manifest['sheet_layout']['frame_files']
    for tick, src in zip(sorted(pins, key=int), frames):
        live = sha256_file(src)
        require(live == pins[tick],
                f'capture_stills_generation_mismatch_tick_{tick}_'
                f'live_{live[:16]}_pinned_{pins[tick][:16]}')
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
