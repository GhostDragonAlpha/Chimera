"""MAT2-G02 pixel-presence check (round-1 corrections, the M09 lesson).

Independent re-measurement of the committed capture frames against the
committed manifest claims:

- every declared viewport tile must contain real content (non-background
  pixels) in every frame - the pre-fix capture had five of six tiles at
  ZERO non-background pixels while claiming all subjects observed;
- every observed/required subject id must be grounded in measured exact-
  color pixel evidence (point subjects: signature pixels within a radius
  of the ORACLE-predicted anchor, where the oracle reprojects from the
  manifest camera record alone - quaternion decode, no renderer code);
- diagnostic rows must carry their declared labels, overlays and title;
  clean rows must be geometry-only (zero label/triad/styling pixels);
- perspective camera consistency: the measured seam-dot centroid must sit
  within 3 px of the record-predicted seam pixel;
- the shared diagnostic footer must carry the trace inset.

CONTROL LAW: run against the PRE-FIX capture - it must RED (the old
manifest claims observed_subject_ids for tiles with zero content).

Usage:
    python -B check_capture_pixels.py <capture_dir>            # green path
    python -B check_capture_pixels.py <capture_dir> <manifest> # control
Exit codes: 0 all checks green, 1 any check red.
"""
from __future__ import annotations

import hashlib
import json
import math
import pathlib
import sys

import numpy as np
from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent

BG = (246, 246, 248)
BODY_A = (60, 90, 200)
BODY_B = (200, 120, 60)
PATCH_T1 = (210, 60, 60)
PATCH_T2 = (120, 60, 160)
PATCH_CLEAN = (150, 150, 150)
PATCH_OUTLINE = (20, 20, 20)
SEAM_DIAG = (250, 220, 80)
SEAM_CLEAN = (90, 90, 90)
TRIAD = [(220, 40, 40), (40, 180, 40), (40, 40, 220)]
TRACE_LINE = (30, 160, 90)
TITLE_COLOR = (90, 90, 100)
LABEL_COLOR = (10, 10, 30)
MIN_TILE_NONBG = 500
MIN_TRIAD_PX = 20
MIN_TITLE_PX = 20
MIN_LABEL_PX_PER_LABEL = 30
POINT_RADIUS = 8
SEAM_RADIUS = 6
MAX_SEAM_CENTROID_PX = 3.0

VIEWS = ['patch overview', 'loaded interface close-up',
         'orthogonal and oblique patch views']
LABELS = ['iface:fixture-patch-p1', 'iface:fixture-patch-p2',
          'fixture_body_a', 'fixture_body_b', 'port:patch', 'port:seam']
QUAD_YZ = [(0.0, 0.0), (0.020, 0.0), (0.013, 0.010), (0.0, 0.010)]


def mask(arr, colors):
    m = np.zeros(arr.shape[:2], dtype=bool)
    for c in colors:
        m |= np.all(arr == np.array(c, dtype=np.uint8), axis=-1)
    return m


def count_near(m, xy, radius):
    x, y = int(round(xy[0])), int(round(xy[1]))
    return int(m[max(0, y - radius):y + radius + 1,
                 max(0, x - radius):x + radius + 1].sum())


def centroid(m):
    ys, xs = np.nonzero(m)
    if len(xs) == 0:
        return None
    return (float(xs.mean()), float(ys.mean()))


def quat_to_mat(q):
    w, x, y, z = q
    return [[1 - 2 * (y * y + z * z), 2 * (x * y - w * z),
             2 * (x * z + w * y)],
            [2 * (x * y + w * z), 1 - 2 * (x * x + z * z),
             2 * (y * z - w * x)],
            [2 * (x * z - w * y), 2 * (y * z + w * x),
             1 - 2 * (x * x + y * y)]]


def dot(a, b):
    return sum(a[i] * b[i] for i in range(3))


def project_from_record(rec, p, w, h):
    """Oracle: reproject from the manifest camera record ONLY."""
    q = rec['orientation_convention_and_values']['quaternion_wxyz']
    m = quat_to_mat(q)
    r = [m[0][0], m[1][0], m[2][0]]
    u = [m[0][1], m[1][1], m[2][1]]
    back = [m[0][2], m[1][2], m[2][2]]
    d = [p[i] - rec['position'][i] for i in range(3)]
    zc = dot(d, back)
    if zc >= -1e-6:
        return None
    depth = -zc
    t = math.tan(math.radians(
        rec['vertical_fov_or_orthographic_span']) / 2.0)
    xn = dot(d, r) / (depth * t)
    yn = dot(d, u) / (depth * t)
    return ((xn * 0.5 + 0.5) * w, (1.0 - (yn * 0.5 + 0.5)) * h)


def tile_rects(manifest):
    layout = manifest['sheet_layout']
    rects = {}
    if 'tile_rects' in layout:
        return {k: list(v) for k, v in layout['tile_rects'].items()}
    w, h = layout['pixel_size']
    tw, th = w // 2, h // 3
    for row in range(3):
        for col, mode in ((0, 'diagnostic'), (1, 'clean')):
            rects[f'pair-{row}:{mode}'] = [col * tw, row * th,
                                           (col + 1) * tw, (row + 1) * th]
    return rects


def main(argv):
    capture_dir = pathlib.Path(argv[0])
    manifest_path = pathlib.Path(argv[1]) if len(argv) > 1 \
        else HERE / 'capture_manifest.json'
    manifest = json.loads(manifest_path.read_bytes().decode('utf-8'))
    trace = json.loads(
        (HERE / 'experiment_trace.json').read_bytes().decode('utf-8'))
    gaps = {r['tick']: r['gap_m'] for r in trace['rows'] if r.get('snap')}
    frames = sorted((capture_dir / 'frames').glob('frame_*.png'))
    ticks = [f for f in manifest['sheet_layout']['frame_files']]
    if len(frames) != len(ticks):
        print(f'RED: frame count {len(frames)} != manifest '
              f'{len(ticks)}')
        return 1
    rects = tile_rects(manifest)
    rows = {(v['pair_id'], v['mode']): v for v in manifest['views']}
    red = []

    def check(cond, msg):
        if not cond:
            red.append(msg)
        return cond

    table = []
    for fi, frame_path in enumerate(frames):
        entry = ticks[fi]
        check(entry['frame'] == frame_path.name,
              f"frame order: {frame_path.name} vs {entry['frame']}")
        check(entry['sha256'] == hashlib.sha256(
            frame_path.read_bytes()).hexdigest(),
            f"frame sha mismatch: {frame_path.name}")
        tick = entry['tick']
        gap = gaps[tick]
        arr = np.asarray(Image.open(frame_path).convert('RGB'),
                         dtype=np.uint8)
        quad = [(gap, y, z) for (y, z) in QUAD_YZ]
        seam = (gap, 0.0087, 0.0048)
        for vi, view_id in enumerate(VIEWS):
            for mode in ('diagnostic', 'clean'):
                tile_key = f'pair-{vi}:{mode}'
                x0, y0, x1, y1 = rects[tile_key]
                t = arr[y0:y1, x0:x1]
                nonbg = int(np.any(
                    t != np.array(BG, dtype=np.uint8), axis=-1).sum())
                row = rows[(f'pair-{vi}', mode)]
                cam = row['camera']
                sig_patch = ([PATCH_T1, PATCH_T2, PATCH_OUTLINE]
                             if mode == 'diagnostic'
                             else [PATCH_CLEAN, PATCH_OUTLINE])
                sig_seam = [SEAM_DIAG] if mode == 'diagnostic' \
                    else [SEAM_CLEAN]
                pm, sm = mask(t, sig_patch), mask(t, sig_seam)
                check(nonbg >= MIN_TILE_NONBG,
                      f'{tile_key} tick {tick}: nonbg {nonbg} < '
                      f'{MIN_TILE_NONBG} (empty viewport)')
                # camera-consistency: record-predicted vs measured seam
                pred = project_from_record(cam, seam, x1 - x0, y1 - y0)
                cen = centroid(sm)
                if pred and cen:
                    d = math.hypot(pred[0] - cen[0], pred[1] - cen[1])
                    check(d <= MAX_SEAM_CENTROID_PX,
                          f'{tile_key} tick {tick}: seam centroid '
                          f'{tuple(round(v, 1) for v in cen)} vs predicted '
                          f'{tuple(round(v, 1) for v in pred)} '
                          f'delta {d:.1f}px')
                # subject grounding
                anchors = {
                    'iface:fixture-patch-p1': quad[0],
                    'iface:fixture-patch-p2': quad[1],
                    'port:patch': (gap, sum(q[1] for q in quad) / 4.0,
                                   sum(q[2] for q in quad) / 4.0),
                    'port:seam': seam,
                }
                measured = []
                for lab in row['visibility']['observed_subject_ids']:
                    if lab == 'fixture_body_a':
                        ok = int(mask(t, [BODY_A]).sum()) > 0
                    elif lab == 'fixture_body_b':
                        ok = int(mask(t, [BODY_B]).sum()) > 0
                    else:
                        p = anchors[lab]
                        pr = project_from_record(cam, p, x1 - x0,
                                                 y1 - y0)
                        m = pm if lab != 'port:seam' else sm
                        rad = SEAM_RADIUS if lab == 'port:seam' \
                            else POINT_RADIUS
                        n = count_near(m, pr, rad) if pr else 0
                        ok = n > 0
                    if ok:
                        measured.append(lab)
                    else:
                        red.append(f'{tile_key} tick {tick}: subject '
                                   f'{lab} claimed observed but has no '
                                   f'pixel evidence')
                check(sorted(measured)
                      == sorted(row['visibility']['observed_subject_ids']),
                      f'{tile_key} tick {tick}: measured observed '
                      f'{sorted(measured)} != manifest '
                      f"{sorted(row['visibility']['observed_subject_ids'])}")
                check(row['visibility']['missing_subject_ids'] == [],
                      f'{tile_key}: missing_subject_ids not empty')
                req = row['visibility']['required_subject_ids']
                obs = row['visibility']['observed_subject_ids']
                check(set(req) <= set(obs),
                      f'{tile_key}: required not subset of observed')
                # per-layer law
                tp = int(mask(t, [TITLE_COLOR]).sum())
                check(tp >= MIN_TITLE_PX,
                      f'{tile_key} tick {tick}: title pixels {tp} < '
                      f'{MIN_TITLE_PX}')
                if mode == 'diagnostic':
                    lp = int(mask(t, [LABEL_COLOR]).sum())
                    nlab = len(row['visibility']['label_ids'])
                    check(lp >= MIN_LABEL_PX_PER_LABEL * max(1, nlab),
                          f'{tile_key} tick {tick}: label pixels {lp} < '
                          f'{MIN_LABEL_PX_PER_LABEL * max(1, nlab)} '
                          f'for {nlab} labels')
                    tri = int(mask(t, TRIAD).sum())
                    check(tri >= MIN_TRIAD_PX,
                          f'{tile_key} tick {tick}: triad pixels {tri} < '
                          f'{MIN_TRIAD_PX}')
                else:
                    for colors, name in (
                            ([LABEL_COLOR], 'label'),
                            (TRIAD, 'triad'),
                            ([PATCH_T1, PATCH_T2], 'diagnostic patch'),
                            ([TRACE_LINE], 'trace inset')):
                        n = int(mask(t, colors).sum())
                        check(n == 0,
                              f'{tile_key} tick {tick}: clean row has '
                              f'{n} {name} pixels (diagnostic styling in '
                              f'a clean viewport)')
                table.append((tick, tile_key, nonbg, tp, len(measured)))
        footer = None
        layout = manifest['sheet_layout']
        if 'footer_rect' in layout:
            fx0, fy0, fx1, fy1 = layout['footer_rect']
            f = arr[fy0:fy1, fx0:fx1]
            tr = int(mask(f, [TRACE_LINE]).sum())
            check(tr >= 20,
                  f'footer tick {tick}: trace pixels {tr} < 20')
            footer = tr
        print(f'frame {fi} tick {tick}: '
              + ' '.join(f'{k.split(":")[0]}{k.split(":")[1][0]}='
                         f'{int(np.any(arr[r[1]:r[3], r[0]:r[2]]
                                      != np.array(BG, dtype=np.uint8),
                                      axis=-1).sum())}'
                         for k, r in sorted(rects.items()))
              + (f' footer_trace={footer}' if footer is not None else ''))
    print()
    print('tiles checked per frame:', len(rects),
          '| frames:', len(frames),
          '| subject-point oracle radius:', POINT_RADIUS)
    if red:
        print(f'RED: {len(red)} pixel-presence violations')
        for m in red[:20]:
            print('  -', m)
        return 1
    print('GREEN: every manifest visibility claim is grounded in measured '
          'pixels of the committed frames')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
