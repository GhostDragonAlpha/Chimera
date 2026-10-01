"""MAT2-G07 capture re-verification (house gate G4 + pixel grounding).

Re-extracts EVERY declared frame from the committed mkv at identity
indices, compares the decoded RGB matrix EXACTLY (identity only; any
non-identity transform is a failure) to the committed still, and
re-measures the exact-color presence table from the DECODED frames
against the manifest's recorded values. Pure stdlib + PIL + ffmpeg; a
RED here fails the card.

Run: python -B check_capture_pixels.py
"""
from __future__ import annotations

import io
import json
import pathlib
import subprocess
import sys

from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import release_fall_account as rfa  # noqa: E402
import render_run as rr  # noqa: E402  (tile layout constants; main guarded)

cso = rfa.load_g05_module()   # the sealed G05 seam (hash-asserted)
gc = cso.load_g04_module()    # the pinned sealed G04 fixture (hash-asserted)


def main():
    cap = HERE / 'evidence' / 'capture'
    manifest = json.loads((cap / 'capture_manifest.json').read_text(
        encoding='utf-8'))
    presence = json.loads((cap / 'pixel_presence.json').read_text(
        encoding='utf-8'))
    video = cap / [p.name for p in cap.glob('*.mkv')][0]
    results = []
    for idx, fr in enumerate(manifest['frame_manifest']):
        still = Image.open(cap / fr['frame']).convert('RGB')
        proc = subprocess.run(
            ['ffmpeg', '-v', 'error', '-i', str(video), '-vf',
             'select=eq(n\\,%d)' % idx, '-frames:v', '1', '-f',
             'image2pipe', '-vcodec', 'png', '-'], capture_output=True,
            timeout=300)
        if proc.returncode != 0 or not proc.stdout:
            raise ValueError('frame_extract_failed:' + fr['frame'])
        decoded = Image.open(io.BytesIO(proc.stdout)).convert('RGB')
        if decoded.size != still.size:
            raise ValueError('frame_size_mismatch:' + fr['frame'])
        identical = decoded.tobytes() == still.tobytes()
        if not identical:
            raise ValueError('decoded_frame_differs:' + fr['frame'])
        # re-measure presence from the DECODED frame (post-decode pixels),
        # cropped to the SAME tile rect the still was measured over
        for view_mode in presence['frames'][idx]['exact_color_counts']:
            view, mode = view_mode.rsplit(':', 1)
            rect = rr.TILE_RECTS[view_mode]
            tile = decoded.crop(rect)
            colors = {}
            for cnt, col in tile.getcolors(maxcolors=1 << 20):
                colors[col] = cnt
            table = presence['frames'][idx]['exact_color_counts'][view_mode]
            targets = rr.presence_targets(mode)
            for k, recorded in table.items():
                got = colors.get(targets[k], 0)
                if got != recorded:
                    raise ValueError(
                        'presence_remeasure_mismatch:%s:%s:%d!=%d'
                        % (fr['frame'], k, got, recorded))
        results.append({'frame': fr['frame'], 'index': idx,
                        'decoded_identity': True,
                        'state_hash': fr['state_hash']})
    out = {'schema': 'chimera.g07_capture_recheck.v1',
           'video': video.name,
           'capture_sha256': manifest['capture_sha256'],
           'frames': results,
           'all_frames_decoded_identity': True,
           'presence_remeasured_from_decoded': True}
    (cap / 'capture_recheck_receipt.json').write_bytes(rfa.canonical(out))
    print(json.dumps({'frames_checked': len(results),
                      'all_frames_decoded_identity': True,
                      'presence_remeasured_from_decoded': True}, indent=1))


if __name__ == '__main__':
    main()
