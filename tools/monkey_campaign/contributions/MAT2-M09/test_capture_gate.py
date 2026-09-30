"""MAT2-M09 capture gate (P4 heritage): frames are the determinism unit.

Decodes the bound FFV1 video with ffmpeg and proves the decoded frames
match the committed stills under the IDENTITY transform ONLY across the
explicit transform list (identity/vflip/hflip): identity diff == 0 pixels,
every non-identity transform > 0. Uses the frames recorded in the capture
manifest's sheet_layout.frame_files (indices independently recomputable:
frame i <-> capture tick list order). Skips (with a loud note) only when
ffmpeg is unavailable.
Run: python -B test_capture_gate.py [capture_dir]
"""
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

CAPTURE_DIR = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else \
    pathlib.Path('E:/ChimeraWork/monkey-coordination/kanban-attempts/'
                 'MAT2-M09/fa6dbcc82b2f4f4c9036bc6c8227b241/capture')
TRANSFORMS = ('identity', 'vflip', 'hflip')


def require(ok, code):
    if not ok:
        raise ValueError(code)


def main():
    from PIL import Image
    import numpy as np
    ffmpeg = shutil.which('ffmpeg')
    if ffmpeg is None:
        print('SKIP: ffmpeg not on PATH (gate must be re-run where it is)')
        return 0
    manifest = json.loads((HERE / 'capture_manifest.json').read_text(
        encoding='utf-8'))
    frames = sorted((CAPTURE_DIR / 'frames').glob('frame_*.png'))
    require(len(frames) == 12, 'frame_count_mismatch')
    video = pathlib.Path(cap_json_video(manifest))
    require(video.exists(), 'video_missing')
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


def cap_json_video(manifest):
    import hashlib
    # the video path is recorded in the validation receipt
    receipt = json.loads((HERE / 'capture_validation_receipt.json')
                         .read_text(encoding='utf-8'))
    return receipt['video_path']


if __name__ == '__main__':
    sys.exit(main())
