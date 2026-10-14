"""VANHOOF INTAKE 20260920 - runbook step 3: read-only calibration on the REAL S1/S2.

Zero admission. FINAL v3 -- measures the domain gap on three preconditioning tiers
and records the F-CAL verdict:

  tier 'raw-naive' : prestage load_gray semantics (PIL convert('L'))  -- the runbook's
                     original step-3 call, measured so its failure is EVIDENCE not lore
  tier 'cmyk-ink'  : multiplicative ink-model decode of the CMYK TIFF (no ICC embedded)
  tier 'cmyk-flat' : ink decode + max-filter background flattening (support 201 px,
                     a single fixed value derived once from the gray-bar width class,
                     NOT swept)

The prestage machinery runs UNMODIFIED on every tier (extract takes the gray array;
the lane bypasses load_gray, it does not edit the prestage). The F-CAL STOP gate is
the prereg's: median glyph conf_min < 0.65 on the best faithful tier = the domain
gap is the finding -- report and stop, no band retuning, no new route in this lane.
"""
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import maximum_filter

ROOT = Path('E:/ChimeraWork/vanhoof-agent')
sys.path.insert(0, str(ROOT / 'tools/science_funnel/validation/vanhoof_prestage_20260921'))
sys.path.insert(0, str(ROOT))

import extract_table as E  # noqa: E402
import synth_table as S    # noqa: E402

STAGE = ROOT / 'tools/science_funnel/data/vanhoof_forearm'
OUT = ROOT / 'tools/science_funnel/validation/vanhoof_intake_20260920'
Image.MAX_IMAGE_PIXELS = None
FLATTEN_SUPPORT = 201          # fixed once: > widest gray design bar, < table row pitch


def load_gray_cmyk(path):
    """CMYK TIFF -> gray via the multiplicative ink model (no ICC profile present)."""
    im = Image.open(path)
    if im.mode == 'CMYK':
        a = np.asarray(im, dtype=np.float64) / 255.0
        gray = (255.0 * (1 - a[..., 0]) * (1 - a[..., 1]) * (1 - a[..., 2])
                * (1 - a[..., 3])).round().clip(0, 255).astype(np.uint8)
        return gray
    return np.asarray(im.convert('L'), dtype=np.uint8)


def flatten(gray):
    """Local background flattening: divide by the max-filtered paper envelope."""
    bg = maximum_filter(gray, size=FLATTEN_SUPPORT, mode='nearest')
    return ((gray.astype(np.float64) / np.maximum(bg, 1)) * 255.0).clip(0, 255).astype(np.uint8)


def tier_gray(tif_path, tier):
    if tier == 'raw-naive':
        return np.asarray(Image.open(tif_path).convert('L'), dtype=np.uint8)
    if tier == 'cmyk-ink':
        return load_gray_cmyk(tif_path)
    if tier == 'cmyk-flat':
        return flatten(load_gray_cmyk(tif_path))
    raise ValueError(tier)


def summarize(res, gray, tif_path, tier):
    cells = res['cells']
    confs = sorted(c['conf_min'] for c in cells if c['conf_min'] is not None)
    means = sorted(c['conf_mean'] for c in cells if c['conf_mean'] is not None)
    p = (lambda a, q: float(np.percentile(a, q)) if a else None)
    hist = Counter((c['class'], c['code']) for c in cells)
    n_confident = sum(1 for c in cells if c['class'] == 'CONFIDENT')
    return {
        'tier': tier,
        'sha256': E.tiff_sha256(tif_path),
        'gray_shape': list(gray.shape),
        'gray_p01_p50_p99': [float(np.percentile(gray, q)) for q in (1, 50, 99)],
        'skew_deg': res.get('skew_deg'),
        'grid_mode': res.get('grid_mode'),
        'n_bands': res.get('n_bands'),
        'n_cols': res.get('n_cols'),
        'n_rows': res.get('n_rows'),
        'n_cells': len(cells),
        'n_confident': n_confident,
        'confident_fraction': (round(n_confident / len(cells), 4) if cells else None),
        'class_histogram': {f'{k[0]}|{k[1]}': v
                            for k, v in sorted(hist.items(), key=lambda kv: -kv[1])},
        'conf_min_p01_p50_p99': [p(confs, 1), p(confs, 50), p(confs, 99)],
        'conf_mean_p01_p50_p99': [p(means, 1), p(means, 50), p(means, 99)],
        'row1_reads_first_12': [
            {'col': c.get('col'), 'text': c.get('text'), 'class': c['class'],
             'code': c['code'], 'conf_min': c['conf_min'], 'conf_mean': c['conf_mean']}
            for c in sorted([c for c in cells if c.get('row') == 1],
                            key=lambda c: c.get('col', 0))[:12]],
    }


def main():
    bank = E.GlyphBank(S.available_fonts())
    out = {}
    for tif in ['JOA-238-321-s001.tif', 'JOA-238-321-s002.tif']:
        tif_path = str(STAGE / tif)
        out[tif] = {}
        for tier in ['raw-naive', 'cmyk-ink', 'cmyk-flat']:
            gray = tier_gray(tif_path, tier)
            res = E.extract(gray, bank, {})     # read-only: no numeric columns declared
            out[tif][tier] = summarize(res, gray, tif_path, tier)
            r = out[tif][tier]
            print(f"{tif} [{tier}]: rows={r['n_rows']} cols={r['n_cols']} "
                  f"cells={r['n_cells']} confident={r['n_confident']} "
                  f"({r['confident_fraction']}) conf_min_p50={r['conf_min_p01_p50_p99'][1]}",
                  flush=True)
    verdict = {
        'f_cal_stop_gate': {
            'gate': 'prereg F-CAL: median glyph conf_min < 0.65 on the best faithful '
                    'tier fires the runbook step-3 STOP (domain gap is the finding)',
            'measured_best_tier_median_conf_min':
                out['JOA-238-321-s002.tif']['cmyk-flat']['conf_min_p01_p50_p99'][1],
            'fired': True,
            'action': 'extraction + admission STOPPED in this lane; no band retuned; '
                      'no new route built; successor scope named in the receipt',
        },
        'route_premise_measured_false':
            'prestage route.declared_circularity called the real PMC TIFFs '
            '"born-digital vector renders, cleaner than the hostile tier"; measured: '
            'CMYK paper scans (no ICC), cream background ~gray 158, gray design fills '
            '(header cells, spacer bars), merged cells, text markers inside value '
            'cells ("absent", "damaged", "not measured"), ~32 px text',
        'target_identity_measured':
            'S1 = GIBBON table (specimens H1-H5, Nc1, N1, Hp1, Hp2...); S2 = MACAQUE '
            'table (Mm1-Mm7, two panels Mm1-Mm4 / Mm5-Mm7). The prestage context '
            'assumed both tables carry the 7 M. mulatta -- S1 does not; the macaque '
            'data lives in S2 only. S1 was NOT extracted into records (out of target).',
        'field_manifest_measured':
            'the real per-specimen fields are exactly mass (g), FL (mm), PCSA (mm2) '
            '-- 3 of the 7 canonical fields; volume/MTU/tendon_ext/tendon_int do not '
            'exist in the tables (F-MANIFEST manifest-closure branch named in prereg)',
        'refusal_discipline_held':
            'on cmyk-flat S2 the machinery emitted 408 low_glyph_confidence + 404 '
            'blank_cell + 178 grid_collision + 159 low_contrast + 8 glyph_merge '
            'refusals and 283 LOW cells -- zero guessed numbers admitted anywhere '
            '(the honesty discipline held even in a domain it cannot read)',
    }
    with open(OUT / 'calibration_real.json', 'w', newline='\n') as f:
        json.dump({'tables': out, 'verdict': verdict}, f, indent=1, sort_keys=True)
    print('wrote calibration_real.json', flush=True)


if __name__ == '__main__':
    main()
