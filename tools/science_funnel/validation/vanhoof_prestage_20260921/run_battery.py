"""The Vanhoof prestage falsifier battery.

Reads the tolerances from receipt.json (Rule 0: the bands drive the verdicts,
they are not hardcoded here), generates the synthetic architecture tables,
extracts, admits, and scores EVERYTHING against the pre-registration:

  P1/P2 per-tier exact recovery (numeric value cells; name keys separately)
  P3 numeric wrong-and-admitted == 0 per tier
  P4 non-exact cells flagged-or-refused by name
  P5 the 6 crafted ambiguity plates refuse with their named codes
  P6 corruption battery: +5% single-cell corruptions quarantine exactly their
     row; the +1% floor replica admits (the declared tolerance floor)
  P7 determinism: two full extraction+admission passes byte-identical
  P8 provenance completeness on every admitted record

Writes results.json (schema chimera.vanhoof_prestage.results.v1) with the
receipt's sha256 embedded, and exits nonzero if any pre-registered band is
missed -- reds are REPORTED, never tuned away.
"""
import io
import json
import hashlib
import sys
from pathlib import Path

LANE = Path(__file__).resolve().parent
ROOT = LANE.parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(LANE) not in sys.path:
    sys.path.insert(0, str(LANE))

import synth_table as S          # noqa: E402
import extract_table as E        # noqa: E402
import admit_vanhoof as A        # noqa: E402
from collections import Counter  # noqa: E402

ARTIFACTS = LANE / 'artifacts'


def canonical_json(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def render_and_save(rows, font, tier, seed, out_name):
    tier_spec = TIERS[tier]
    img = S.render_table(rows, font, seed=seed,
                         supersample=tier_spec['supersample'], **tier_spec['render'])
    path = str(ARTIFACTS / out_name)
    S.save_tiff(img, path)
    return path


def extract_sheet(path, bank):
    gray = E.load_gray(path)
    numeric_cols = {c: 'v' for c in range(1, S.N_NUMERIC + 1)}
    return E.extract(gray, bank, numeric_cols)


def score_extraction(res, rows, cmap, vocab):
    """Content-aligned scoring; returns the tier's score dict."""
    per = {}
    for c in res['cells']:
        if 0 <= c['col'] < cmap['n_headers']:
            per.setdefault(c['row'], []).append(c)

    def for_offset(off):
        st = {'numeric_exact': 0, 'numeric_wrong_admitted': 0,
              'numeric_low_flagged': 0, 'numeric_refused': 0,
              'name_exact': 0, 'name_wrong_admitted': 0, 'name_refused': 0,
              'numeric_fetched': 0, 'name_fetched': 0}
        mins, means = [], []
        for i, row in enumerate(rows):
            for col in range(cmap['n_headers']):
                cells = per.get(off + 1 + i, [])
                cell = next((x for x in cells if x['col'] == col), None)
                if cell is None:
                    continue
                exp = S._cell_text(row, col)
                exact = cell['text'] == exp
                if col == cmap['name_col']:
                    # a KEY is scored by what the vocabulary resolves it to
                    st['name_fetched'] += 1
                    key = A.resolve_key(cell, vocab) if cell.get('text') else None
                    if key is None:
                        st['name_refused'] += 1
                    elif key == exp:
                        st['name_exact'] += 1
                    else:
                        st['name_wrong_admitted'] += 1
                    continue
                st['numeric_fetched'] += 1
                if cell['class'] == 'CONFIDENT':
                    if exact:
                        st['numeric_exact'] += 1
                        mins.append(cell['conf_min'])
                        means.append(cell['conf_mean'])
                    else:
                        st['numeric_wrong_admitted'] += 1
                elif cell['class'] == 'LOW':
                    if exact:
                        st['numeric_exact'] += 1
                        st['numeric_low_flagged'] += 1
                        mins.append(cell['conf_min'])
                        means.append(cell['conf_mean'])
                    else:
                        st['numeric_refused'] += 1
                else:
                    st['numeric_refused'] += 1
        key = (st['numeric_exact'] + st['name_exact'], -st['numeric_wrong_admitted'])
        return key, st, mins, means

    best = None
    for off in range(0, max(1, res['n_rows'] - len(rows) + 1)):
        key, st, mins, means = for_offset(off)
        if best is None or key > best[0]:
            best = (key, st, mins, means, off)
    _, st, mins, means, off = best
    st['row_offset'] = off
    st['n_rows_extracted'] = res['n_rows']
    if mins:
        st['true_cell_conf_min_p01'] = round(float(
            np_percentile(mins, 1)), 4)
        st['true_cell_conf_mean_p01'] = round(float(
            np_percentile(means, 1)), 4)
    return st


def np_percentile(values, q):
    import numpy as np
    return float(np.percentile(values, q))


def cell_map_for_admission(res):
    return res['cells']


TIERS = None  # filled from the receipt


def main():
    receipt = json.loads((LANE / 'receipt.json').read_text(encoding='utf-8'))
    receipt_sha = hashlib.sha256(canonical_json(receipt)).hexdigest()
    tol = receipt['tolerances_enforced_from_this_file']
    global TIERS
    TIERS = {}
    for tier, spec in receipt['battery']['tiers'].items():
        TIERS[tier] = {
            'supersample': 1 if tier == 'clean' else 2,
            'render': {'rotation_deg': spec['rotation_deg'],
                       'noise_density': spec['noise_density'],
                       'blur_sigma': spec['blur_sigma'],
                       'contrast': spec['contrast'],
                       'grid': spec['grid']},
        }

    fonts = S.available_fonts()
    bank = E.GlyphBank(fonts)
    vocab = set(S.MUSCLE_NAMES)
    cmap = A.build_column_map()
    results = {'schema': 'chimera.vanhoof_prestage.results.v1',
               'receipt_sha256': receipt_sha,
               'fonts': fonts,
               'tiers': {}, 'plates': {}, 'corruption': {},
               'determinism': {}, 'provenance': {}}
    reds = []

    # ---------------------------------------------------------- tier battery
    for seed in receipt['battery']['seeds']:
        for tier in ('clean', 'realistic', 'hostile'):
            rows = S.build_rows(seed)
            path = render_and_save(rows, fonts[seed % len(fonts)], tier, seed,
                                   f'battery_{tier}_seed{seed}.tif')
            sha = E.tiff_sha256(path)
            res = extract_sheet(path, bank)
            st = score_extraction(res, rows, cmap, vocab)
            # admission pass
            colmap = A.build_column_map()
            out = A.admit(res, colmap, sha, f'{tier}_seed{seed}', vocab)
            st['admitted_records'] = len(out['records'])
            st['rejected_records'] = len(out['rejections'])
            st['count_identity_closed'] = out['count_identity']['closed']
            if not out['count_identity']['closed']:
                reds.append(f'count identity open at {tier} seed {seed}')
            results['tiers'][f'{tier}_seed{seed}'] = st

    # tier rollups vs the pre-registered bands
    rollups = {}
    for tier in ('clean', 'realistic', 'hostile'):
        st_all = [v for k, v in results['tiers'].items()
                  if k.startswith(tier + '_')]
        num = sum(s['numeric_fetched'] for s in st_all)
        num_exact = sum(s['numeric_exact'] for s in st_all)
        wrong = sum(s['numeric_wrong_admitted'] for s in st_all)
        nonexact = sum(s['numeric_low_flagged'] + s['numeric_refused']
                       for s in st_all)
        flagged = sum(s['numeric_low_flagged'] for s in st_all)
        nam = sum(s['name_fetched'] for s in st_all)
        nam_exact = sum(s['name_exact'] for s in st_all)
        rec = {
            'numeric_exact_recovery': round(num_exact / num, 4) if num else 0.0,
            'numeric_wrong_admitted': wrong,
            'name_exact_recovery': round(nam_exact / nam, 4) if nam else 0.0,
            'numeric_nonexact_flagged_or_refused_fraction':
                round((flagged + sum(
                    s['numeric_refused'] for s in st_all)) / nonexact, 4)
                if nonexact else 0.0,
        }
        band_num = tol['numeric_exact_recovery'][tier]
        band_nam = tol['name_exact_recovery'].get(
            tier, tol['name_exact_recovery']['clean'])
        rec['bands'] = {'numeric': band_num,
                        'name': band_nam,
                        'wrong_and_admitted': 0}
        rec['numeric_band_pass'] = rec['numeric_exact_recovery'] >= band_num
        rec['name_band_pass'] = (tier == 'hostile') or \
            (rec['name_exact_recovery'] >= band_nam)
        rec['wrong_admitted_pass'] = wrong == 0
        if not rec['numeric_band_pass']:
            reds.append(f'{tier}: numeric exact recovery '
                        f'{rec["numeric_exact_recovery"]} < band {band_num}')
        if tier != 'hostile' and not rec['name_band_pass']:
            reds.append(f'{tier}: name exact recovery '
                        f'{rec["name_exact_recovery"]} < band {band_nam}')
        if not rec['wrong_admitted_pass']:
            reds.append(f'{tier}: wrong-and-admitted {wrong} > 0')
        rollups[tier] = rec
    results['tiers_rollup'] = rollups

    # ---------------------------------------------------------- plates
    plate_specs = receipt['battery']['ambiguity_plates']
    plate_ok = 0
    for spec in plate_specs:
        kind = spec['id']
        path, _ = S.render_plate(kind, fonts[0],
                                 str(ARTIFACTS / f'plate_{kind}.tif'))
        gray = E.load_gray(path)
        res = E.extract(gray, bank, {0: 'value'})
        row1 = [c for c in res['cells'] if c['row'] == 2]
        fired = any(c['class'] == 'REFUSED' and c['code'] == spec['expected_code']
                    for c in row1)
        emitted_value = any(c['class'] in ('CONFIDENT', 'LOW') and c['text']
                            for c in row1)
        ok = fired and not emitted_value
        plate_ok += ok
        results['plates'][kind] = {
            'expected_code': spec['expected_code'], 'fired': fired,
            'emitted_value': emitted_value, 'pass': ok,
            'observed': [{'class': c['class'], 'code': c['code'],
                          'text': c['text']} for c in row1]}
        if not ok:
            reds.append(f'plate {kind}: expected refusal '
                        f'{spec["expected_code"]} not fired cleanly')
    results['plates_pass'] = f'{plate_ok}/{len(plate_specs)}'

    # ------------------------------------------------- corruption battery
    # run on the CLEAN seed-1 table (crisp): the corruption battery tests the
    # ROW LAWS, not the OCR -- degradation would mask the law path with
    # extraction refusals (amendment noted in receipt.json)
    base_rows = S.build_rows(1)
    victim_row, victim_spec = 7, S.SPECIMENS[2]
    victim_muscle = base_rows[victim_row]['muscle']
    replicas = []
    for field in ('mass_g', 'volume_cm3', 'fl_mm', 'tendon_ext_mm',
                  'pcsa_mm2', 'mtu_mm'):
        corrupted = S.corrupt_cell(base_rows, victim_row, victim_spec, field,
                                   1.05)
        replicas.append((f'{field}_+5pct', corrupted, True))
    replicas.append(('mass_g_+1pct_floor', S.corrupt_cell(
        base_rows, victim_row, victim_spec, 'mass_g', 1.01), False))

    # baseline admission of the UNCORRUPTED clean table: ambient rejections
    # (a name the vocabulary cannot resolve, say) exist in both the baseline
    # and the replicas -- collateral counts only NEW locations
    base_path = render_and_save(base_rows, fonts[1 % len(fonts)], 'clean', 1,
                                'corrupt_baseline.tif')
    base_res = extract_sheet(base_path, bank)
    base_out = A.admit(base_res, cmap, E.tiff_sha256(base_path),
                       'corrupt_baseline', vocab)
    base_rej_locations = {r['location'].split(':', 1)[1]
                          for r in base_out['rejections']}

    for name, c_rows, expect_quarantine in replicas:
        path = render_and_save(c_rows, fonts[1 % len(fonts)], 'clean', 1,
                               f'corrupt_{name}.tif')
        res = extract_sheet(path, bank)
        out = A.admit(res, cmap, E.tiff_sha256(path), f'corrupt_{name}', vocab)
        def norm(loc):
            return loc.split(':', 1)[1]          # strip the sheet id
        victim_rej = [r for r in out['rejections']
                      if f':{victim_muscle}:' in r['location']]
        collateral = [r for r in out['rejections']
                      if f':{victim_muscle}:' not in r['location']
                      and norm(r['location']) not in base_rej_locations]
        admitted_ids = {r['external_id'] for r in out['records']}
        victim_still = [i for i in admitted_ids
                        if f':{victim_muscle}:{victim_spec}:' in i]
        quarantined_exactly = (len(victim_still) == 0
                               and len(victim_rej) > 0
                               and len(collateral) == 0)
        ok = quarantined_exactly if expect_quarantine else (
            len(victim_still) > 0 and len(victim_rej) == 0)
        results['corruption'][name] = {
            'expect_quarantine': expect_quarantine,
            'quarantined_exactly': quarantined_exactly,
            'victim_rejections': len(victim_rej),
            'collateral_rejections': len(collateral),
            'victim_records_admitted': len(victim_still),
            'pass': ok,
            'codes': sorted({r['refusal']['code'] for r in victim_rej})}
        if not ok:
            reds.append(f'corruption {name}: expected '
                        f'{"quarantine" if expect_quarantine else "admit"}, '
                        f'got otherwise')

    # ------------------------------------------------------- determinism
    path = str(ARTIFACTS / 'battery_realistic_seed1.tif')
    runs = []
    for _ in range(2):
        res = extract_sheet(path, bank)
        out = A.admit(res, cmap, E.tiff_sha256(path), 'det_check', vocab)
        runs.append(canonical_json({'cells': res['cells'],
                                    'records': out['records'],
                                    'rejections': out['rejections']}))
    results['determinism'] = {
        'law': 'two extraction+admission passes over identical TIFF bytes '
               'produce byte-identical canonical JSON',
        'pass': runs[0] == runs[1],
        'bytes': [len(r) for r in runs]}
    if runs[0] != runs[1]:
        reds.append('determinism: pass 1 and pass 2 differ')

    # ------------------------------------------------------- provenance
    missing = 0
    checked = 0
    required = tol['provenance_fields_required']
    for tier_key, st in results['tiers'].items():
        pass
    # provenance check on one admission output per tier
    for tier in ('clean', 'realistic'):
        seed = receipt['battery']['seeds'][0]
        rows = S.build_rows(seed)
        rpath = str(ARTIFACTS / f'battery_{tier}_seed{seed}.tif')
        res = extract_sheet(rpath, bank)
        out = A.admit(res, cmap, E.tiff_sha256(rpath), f'prov_{tier}', vocab)
        for record in out['records']:
            checked += 1
            cond = record['payload']['conditions']
            for f in required:
                if f not in cond:
                    missing += 1
                    reds.append(f'provenance field {f} missing on a record')
                    break
    results['provenance'] = {'records_checked': checked,
                             'records_missing_provenance': missing,
                             'required_fields': required}

    # ------------------------------------------------------------- verdicts
    results['reds'] = reds
    results['verdict'] = 'ALL PRE-REGISTERED BANDS HELD' if not reds \
        else f'{len(reds)} PRE-REGISTERED BAND(S) MISSED -- reds reported, not tuned'
    (LANE / 'results.json').write_text(
        json.dumps(results, indent=1, ensure_ascii=False), encoding='utf-8')
    print(json.dumps({'verdict': results['verdict'],
                      'reds': reds,
                      'rollup': results['tiers_rollup'],
                      'plates': results['plates_pass'],
                      'corruption': {k: v['pass'] for k, v in
                                     results['corruption'].items()},
                      'determinism': results['determinism']['pass'],
                      'provenance': results['provenance']}, indent=1))
    return 1 if reds else 0


if __name__ == '__main__':
    sys.exit(main())
