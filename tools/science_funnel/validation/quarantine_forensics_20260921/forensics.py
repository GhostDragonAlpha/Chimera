"""Quarantine forensics for the six law-failing Macaca mulatta rows (Rule-0 lane).

Preregistration: receipt.json in this directory (committed BEFORE this script
ran; falsifiers F1-F5 named there). READ-ONLY forensics: reads the carrier
commit 46ed85a3 via `git show` (xlsx member sha-pinned, store sha-pinned),
never merges, never checks out, never writes any store. Outputs land in this
directory only:

  raw_cells.json       byte-cited raw cell text of the six rows (sheet/row/cell/
                       raw text), the Information specimen + column dictionary
                       rows, and the paper-package scan windows (F3 byte-cites).
  forensics_table.json per-row: both sides of every law recomputed from the raw
                       bytes, the admitting store's own refusal detail (string-
                       compared byte-exactly against this lane's reproduction),
                       the unit-class test, the digit-neighbor test, the
                       cross-species admitted bands, the candidate single-cell
                       corrections with their law/band outcomes, the verdict
                       RECOVERABLE (with the fix spec) or GENUINELY BAD, and the
                       read-only store cross-check (30 subjects / 265 records /
                       count identity / zero records for the six).

Deterministic by construction: no timestamps, fixed key order, CPython float
repr. Two runs must produce byte-identical artifacts (falsifier F5).

The admitting lane's enforced laws (tools/science_funnel/adapters_muscle.py at
46ed85a3, sha 82ccdc67...): PCSA closure mass_g/1000/(1060*FL) == PCSA at 2%
(math.isclose, symmetric rel_tol), mass additivity |belly+tendon-whole|/whole
<= 2%, and every required field a finite positive number (blank refuses as
invalid_number). A row failing any of these is refused WHOLE and recorded as a
rejection {location, refusal{code, detail}} - those records are the evidence
base of this lane.
"""
import hashlib
import io
import json
import math
import re
import subprocess
import zipfile
import xml.etree.ElementTree as ET

ROOT = r'E:/ChimeraWork/forensic-agent'
CARRIER_REF = 'refs/remotes/origin/agent/skeleton-movie-20260919'
CARRIER = '46ed85a3ba1e451cf5b02f068134bf6801dbd258'
XLSX_PATH = 'tools/science_funnel/data/guimaraes_arch/AJPA-190-e70329-s001.xlsx'
XLSX_PIN = '08ead4a901a53f97e136c709a7804b9d04b4b903107e873c01f3b9b5b9eb8678'
XLSX_BYTES = 321899
STORE_PATH = 'tools/creature_graph/data/creature_graph.json'
STORE_PIN = 'f625169a2568e735462cd63605492d7fef212977966ddf73f08027c8e87ce80f'
FULLTEXT_PATH = 'tools/science_funnel/data/guimaraes_arch/PMC13425262_fulltext.xml'
DOCX_PATH = 'tools/science_funnel/data/guimaraes_arch/AJPA-190-e70329-s002.docx'
ADAPTER_PIN = '82ccdc6745f5b44ce29cb7dc4e8b1c7929c56c7683fcd4e05a0b66148b2ec452'
LAW_TOL = 0.02
RHO = 1060.0
SHEET = 'Macaca mulatta'
SIX = ('AB', 'BFS', 'ObtInt', 'RF', 'SAR', 'TP')
SHEET_ROWS = {'AB': 8, 'BFS': 23, 'ObtInt': 4, 'RF': 11, 'SAR': 21, 'TP': 9}
BFL_SHEET_ROW = 22  # the suspected copy-forward twin of the BFS row
SPECIFIC_TENSION_N_PER_CM2 = 30.0  # LightEngine/kinematic/muscles.py:79 ANATOMY-DATUM

_SSML = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
_OFFDOC = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
_PKGREL = 'http://schemas.openxmlformats.org/package/2006/relationships'
_VARIANTS = {
    'Species_common': 'species_common', 'Species': 'species',
    'Mus_abbrev': 'muscle', 'FL_m': 'fl_m', 'PCSA_m2': 'pcsa_m2',
    'musc_LENGTH_m': 'musc_len', 'musc_LENGTH': 'musc_len',
    'musc_MASS_kg': 'musc_mass', 'musc_MASS': 'musc_mass',
    'belly_LENGTH_m': 'belly_len', 'belly_LENGTH': 'belly_len',
    'belly_MASS_kg': 'belly_mass', 'belly_MASS': 'belly_mass',
    'tendon_LENGTH_m': 'tendon_len', 'tendon_LENGTH': 'tendon_len',
    'tendon_MASS_kg': 'tendon_mass', 'tendon_MASS': 'tendon_mass',
    'avg_penn_deg': 'penn_deg', 'avg_pen_deg': 'penn_deg', 'Limb': 'limb',
}


def git_show(spec):
    return subprocess.run(['git', 'show', spec], cwd=ROOT,
                          capture_output=True, check=True).stdout


def refuse(name, detail):
    raise SystemExit(f'REFUSAL {name}: {detail}')


def pin(name, condition, detail=''):
    if not condition:
        refuse(name, detail)


def col_index(ref):
    letters = re.match(r'([A-Z]+)', ref).group(1)
    out = 0
    for ch in letters:
        out = out * 26 + (ord(ch) - 64)
    return out - 1


def col_letters(index):
    out = ''
    index += 1
    while index:
        index, rem = divmod(index - 1, 26)
        out = chr(65 + rem) + out
    return out


def sheet_rows(archive, target, shared):
    """Ordered rows as ({column index: raw text}, {column index: cell address})."""
    root = ET.fromstring(archive.read(target))
    out = []
    for row in root.iter(f'{{{_SSML}}}row'):
        cells, addrs = {}, {}
        for cell in row.findall(f'{{{_SSML}}}c'):
            kind = cell.get('t')
            if kind == 'inlineStr':
                value = ''.join(t.text or '' for t in cell.iter(f'{{{_SSML}}}t'))
            else:
                node = cell.find(f'{{{_SSML}}}v')
                if node is None:
                    continue
                value = shared[int(node.text)] if kind == 's' else node.text
            if value is not None and str(value).strip() != '':
                cells[col_index(cell.get('r'))] = str(value)
                addrs[col_index(cell.get('r'))] = cell.get('r')
        out.append((cells, addrs))
    return out


# ------------------------------------------------- admitting lane's own numbers

def adapter_laws(vals):
    """The admitting adapter's exact law evaluation (adapters_muscle.py:210-232
    semantics: math.isclose rel_tol=0.02 is SYMMETRIC in max(|a|,|b|))."""
    problems = []
    detail = None
    code = None
    for field in ('fl_m', 'pcsa_m2', 'musc_len', 'musc_mass', 'belly_len',
                  'belly_mass', 'tendon_len', 'tendon_mass'):
        if vals[field] is None:
            return 'invalid_number', '', [f'{field}_blank']
        if vals[field] <= 0:
            return 'nonpositive_value', f'{field}={vals[field]!r}', [f'{field}_nonpositive']
    pred = vals['musc_mass'] / 1000.0 / (RHO * vals['fl_m'])
    if not math.isclose(pred, vals['pcsa_m2'], rel_tol=LAW_TOL):
        return ('pcsa_closure_violation',
                f"pcsa={vals['pcsa_m2']} predicted={pred}",
                [f'pcsa_closure_dev_{(pred - vals["pcsa_m2"]) / vals["pcsa_m2"]:.3f}'])
    if abs(vals['belly_mass'] + vals['tendon_mass'] - vals['musc_mass']) / vals['musc_mass'] > LAW_TOL:
        return ('mass_additivity_violation',
                f"belly+tendon={vals['belly_mass'] + vals['tendon_mass']} "
                f"whole={vals['musc_mass']}",
                [f'mass_additivity_dev_{abs(vals["belly_mass"] + vals["tendon_mass"] - vals["musc_mass"]) / vals["musc_mass"]:.3f}'])
    return None, None, []


def digit_edit_kind(raw_text, corrected_float):
    """Classical keystroke-slip test: does a single substitution/adjacent
    transposition/deletion/insertion on the raw text's digit string produce the
    corrected value's digit string (both in %.6g display)?"""
    a = re.sub(r'[^0-9]', '', format(float(raw_text), '.6g'))
    b = re.sub(r'[^0-9]', '', format(corrected_float, '.6g'))
    if a == b:
        return 'identical'
    if len(a) == len(b):
        diffs = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
        if len(diffs) == 1:
            return 'single_substitution'
        if (len(diffs) == 2 and diffs[1] == diffs[0] + 1
                and a[diffs[0]] == b[diffs[1]] and a[diffs[1]] == b[diffs[0]]):
            return 'adjacent_transposition'
        return f'{len(diffs)}_substitutions'
    if len(a) == len(b) + 1:
        for i in range(len(a)):
            if a[:i] + a[i + 1:] == b:
                return 'single_deletion'
    if len(b) == len(a) + 1:
        for i in range(len(b)):
            if b[:i] + b[i + 1:] == a:
                return 'single_insertion'
    return None


def unit_factor_kind(numerator, denominator):
    """Clean-factor test (unit inconsistency class): ratio within 0.5% of
    10^k (k in -6..6), or 2/4/5/1000/1000000 multiples used by mm/cm/m and
    mg/g/kg slips."""
    ratio = numerator / denominator
    for factor in ([10.0 ** k for k in range(-6, 7)] + [2.0, 4.0, 5.0, 20.0, 50.0]):
        for candidate in (factor, 1.0 / factor):
            if abs(ratio - candidate) <= 0.005 * candidate:
                return f'clean_factor_{candidate:g}'
    return None


def main():
    # ------------------------------------------------ F1: pins and ancestry
    probe = subprocess.run(['git', 'merge-base', '--is-ancestor', CARRIER, CARRIER_REF],
                           cwd=ROOT, capture_output=True)
    pin('F1_carrier', probe.returncode == 0, f'{CARRIER} not an ancestor of {CARRIER_REF}')
    raw = git_show(f'{CARRIER}:{XLSX_PATH}')
    pin('F1_xlsx', hashlib.sha256(raw).hexdigest() == XLSX_PIN and len(raw) == XLSX_BYTES,
        'xlsx bytes drift from the preregistered pin')
    store_text = git_show(f'{CARRIER}:{STORE_PATH}').decode('utf-8')
    pin('F1_store', hashlib.sha256(store_text.encode('utf-8')).hexdigest() == STORE_PIN,
        'store bytes drift from the preregistered pin')
    adapter_raw = git_show(f'{CARRIER}:tools/science_funnel/adapters_muscle.py')
    pin('F1_adapter', hashlib.sha256(adapter_raw).hexdigest() == ADAPTER_PIN,
        'admitting adapter drifted from the preregistered pin')

    archive = zipfile.ZipFile(io.BytesIO(raw))
    workbook = ET.fromstring(archive.read('xl/workbook.xml'))
    rels = ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))
    rid_map = {rel.get('Id'): rel.get('Target')
               for rel in rels.findall(f'{{{_PKGREL}}}Relationship')}
    sheets = []
    for sh in workbook.iter(f'{{{_SSML}}}sheet'):
        target = rid_map[sh.get(f'{{{_OFFDOC}}}id')]
        if not target.startswith('xl/'):
            target = 'xl/' + target.lstrip('/')
        sheets.append((sh.get('name'), target))
    shared_root = ET.fromstring(archive.read('xl/sharedStrings.xml'))
    shared = [''.join(t.text or '' for t in si.iter(f'{{{_SSML}}}t'))
              for si in shared_root.findall(f'{{{_SSML}}}si')]

    parsed = {}
    for name, target in sheets:
        if name.strip().lower() == 'information':
            continue
        rows = sheet_rows(archive, target, shared)
        header = {}
        for column, label in rows[0][0].items():
            canonical = _VARIANTS.get(label.strip())
            pin('F1_header', canonical is not None, f'{name}: unknown header {label!r}')
            header[canonical] = column
        parsed[name] = (header, rows[1:])

    # ------------------------------------------------ store refusals (F1 identity)
    refusal_pattern = (r'"location": "(guimaraes:[^"]+)",\n      "refusal": \{\n'
                       r'       "code": "([^"]+)",\n       "detail": "([^"]*)"')
    store_refusals = {(m[0], m[1], m[2]) for m in re.findall(refusal_pattern, store_text)}
    pin('F1_refusal_count', len(store_refusals) == 49,
        f'store holds {len(store_refusals)} guimaraes refusals, preregistered 49')
    maca = {loc: (code, detail) for loc, code, detail in store_refusals
            if loc.startswith(f'guimaraes:{SHEET}:')}
    pin('F1_macaca_identity', set(maca) == {f'guimaraes:{SHEET}:row{r}' for r in SHEET_ROWS.values()},
        'macaque refusal locations != the six preregistered rows')

    # ------------------------------------------------ per-sheet law reconciliation
    admitted = {}   # (sheet, muscle, row) -> raws/vals for ADMITTED rows
    refused = {}
    for name, (header, rows) in parsed.items():
        for ordinal, (cells, addrs) in enumerate(rows, 2):
            if not cells:
                continue
            muscle = cells.get(header['muscle'], '').strip()
            if not muscle:
                continue
            vals, raws, cites = {}, {}, {}
            for field in ('fl_m', 'pcsa_m2', 'musc_len', 'musc_mass', 'belly_len',
                          'belly_mass', 'tendon_len', 'tendon_mass', 'penn_deg'):
                column = header.get(field)
                text = cells.get(column, '').strip() if column is not None else ''
                raws[field] = text
                vals[field] = float(text) if text else None
                if text:
                    cites[field] = f'{name}/{col_letters(column)}{ordinal}'
            code, detail, _ = adapter_laws(vals)
            entry = {'vals': vals, 'raws': raws, 'cites': cites, 'row': ordinal}
            if code is None:
                admitted[(name, muscle, ordinal)] = entry
            else:
                refused[(name, muscle, ordinal)] = dict(entry, code=code, detail=detail)
    reconciled = {f'guimaraes:{s}:row{r}' for (s, m, r) in refused}
    pin('F1_reconcile', reconciled == {loc for loc, _, _ in store_refusals},
        f'recomputed refusal set != store refusal set: '
        f'{sorted(reconciled ^ {loc for loc, _, _ in store_refusals})}')
    detail_mismatch = []
    for (sheet_name, muscle, ordinal), entry in refused.items():
        loc = f'guimaraes:{sheet_name}:row{ordinal}'
        store_code, store_detail = maca.get(loc, (None, None)) if sheet_name == SHEET else \
            next(((c, d) for l, c, d in store_refusals if l == loc), (None, None))
        if store_code != entry['code'] or store_detail != entry['detail']:
            detail_mismatch.append((loc, entry['code'], entry['detail'], store_code, store_detail))
    pin('F2_detail_strings', not detail_mismatch,
        f'refusal details do not reproduce byte-exactly: {detail_mismatch[:3]}')

    # ------------------------------------------------ store cross-check (read-only)
    subjects = sorted({s.rsplit('/', 1)[-1].split(' ')[0]
                       for s in re.findall(r'Macaca_mulatta/muscle/[A-Za-z]+ \([RL]\)', store_text)})
    record_count = len(re.findall(r'Macaca_mulatta/muscle/', store_text))
    six_in_store = [s for s in SIX if s in subjects]
    pin('F1_store_six', six_in_store == [], f'store holds records for quarantined {six_in_store}')
    sheet_admitted_names = sorted({m for (s, m, r) in admitted if s == SHEET})
    pin('F1_store_count', sheet_admitted_names == subjects,
        f'sheet admitted set != store subjects')
    with_penn = sum(1 for (s, m, r), e in admitted.items()
                    if s == SHEET and e['raws']['penn_deg'])
    without_penn = len(admitted) - with_penn if False else sum(
        1 for (s, m, r), e in admitted.items() if s == SHEET and not e['raws']['penn_deg'])
    pin('F1_count_identity', with_penn * 9 + without_penn * 8 == record_count,
        f'count identity broken: {with_penn}x9+{without_penn}x8 != store {record_count}')

    # ------------------------------------------------ bands from admitted rows of
    # the other five species (per muscle: mass partition fractions, FL, specific PCSA)
    other_sheets = [n for n, _ in sheets if n.strip().lower() != 'information' and n != SHEET]

    def band(muscle, quantity):
        values = []
        for name in other_sheets:
            header, rows = parsed[name]
            for ordinal, (cells, addrs) in enumerate(rows, 2):
                if not cells or cells.get(header['muscle'], '').strip() != muscle:
                    continue
                if (name, muscle, ordinal) in refused:
                    continue  # quarantined rows' fractions are untrustworthy by definition
                vals = {f: (float(cells.get(header[f], '').strip() or 'nan')
                            if cells.get(header[f], '').strip() else None)
                        for f in ('fl_m', 'pcsa_m2', 'musc_mass', 'belly_mass', 'tendon_mass')}
                if None in vals.values() or min(vals.values()) <= 0:
                    continue
                values.append({'sheet': name, 'row': ordinal,
                               'belly_frac': vals['belly_mass'] / vals['musc_mass'],
                               'tendon_frac': vals['tendon_mass'] / vals['musc_mass'],
                               'fl': vals['fl_m'],
                               'spec_pcsa': vals['pcsa_m2'] / vals['musc_mass']})
        if not values:
            return None
        return {q: {'min': min(v[q] for v in values), 'max': max(v[q] for v in values),
                    'n': len(values)} for q in ('belly_frac', 'tendon_frac', 'fl', 'spec_pcsa')}

    def in_band(value, band_doc, quantity):
        if band_doc is None:
            return {'in_band': None, 'note': 'no admitted comparison rows'}
        low, high = band_doc[quantity]['min'], band_doc[quantity]['max']
        if low <= value <= high:
            return {'in_band': True, 'band': [low, high]}
        margin = (low - value) / low if value < low else (value - high) / high
        return {'in_band': False, 'band': [low, high], 'out_margin_rel': margin}

    # ------------------------------------------------ paper package scan (BFS gap)
    def scan_text(label, text):
        hits = []
        for pat in ('BFS', 'biceps femoris', 'short head'):
            for m in re.finditer(pat, text):
                window = text[max(0, m.start() - 120):m.start() + 200]
                window = re.sub(r'\s+', ' ', window).strip()
                mass_hit = re.search(r'\d+(?:\.\d+)?\s*(?:g|kg)\b', window)
                hits.append({'pattern': pat, 'window': window[:260],
                             'numeric_mass_in_window': bool(mass_hit)})
        return {'source': label, 'mentions': len(hits), 'windows': hits,
                'numeric_mass_at_any_mention': any(h['numeric_mass_in_window'] for h in hits)}

    fulltext = re.sub(r'<[^>]+>', ' ', git_show(f'{CARRIER}:{FULLTEXT_PATH}').decode('utf-8', 'replace'))
    docx_zip = zipfile.ZipFile(io.BytesIO(git_show(f'{CARRIER}:{DOCX_PATH}')))
    docx_text = ''
    for member in docx_zip.namelist():
        if member.endswith('.xml') and ('document' in member or 'header' in member or 'footer' in member):
            docx_text += re.sub(r'<[^>]+>', ' ', docx_zip.read(member).decode('utf-8', 'replace'))
    package_scan = [scan_text(FULLTEXT_PATH, fulltext), scan_text(DOCX_PATH, docx_text)]

    # ------------------------------------------------ per-row forensics
    header, rows = parsed[SHEET]
    raw_cells_doc = {'schema': 'chimera.quarantine_forensics_raw_cells.v1',
                     'carrier': CARRIER, 'xlsx_path': XLSX_PATH, 'xlsx_sha256': XLSX_PIN,
                     'sheet': SHEET, 'rows': {}}
    rows_out = {}

    for muscle in SIX:
        ordinal = SHEET_ROWS[muscle]
        cells, addrs = rows[ordinal - 2]
        entry = admitted.get((SHEET, muscle, ordinal)) or refused[(SHEET, muscle, ordinal)]
        vals, raws, cites = entry['vals'], entry['raws'], entry['cites']
        raw_cells_doc['rows'][muscle] = {
            'sheet_row': ordinal,
            'cells': {f: {'cell': cites.get(f, f'<absent:{col_letters(header[f])}{ordinal}>'),
                          'raw_text': raws[f]}
                      for f in ('fl_m', 'pcsa_m2', 'musc_len', 'musc_mass', 'belly_len',
                                'belly_mass', 'tendon_len', 'tendon_mass', 'penn_deg')},
        }
        store_code, store_detail = maca[f'guimaraes:{SHEET}:row{ordinal}']
        recomputed_code, recomputed_detail, problems = adapter_laws(vals)
        pin('F2_recompute', (recomputed_code, recomputed_detail) == (store_code, store_detail),
            f'{muscle}: recomputed refusal != store refusal')
        read_back = {f: (float(raws[f]) if raws[f] else None)
                     for f in ('fl_m', 'pcsa_m2', 'musc_len', 'musc_mass', 'belly_len',
                               'belly_mass', 'tendon_len', 'tendon_mass', 'penn_deg')}
        read_vs_raw_ok = all((raws[f] == '' and read_back[f] is None)
                             or repr(read_back[f]) == repr(vals[f]) for f in raws)

        row_doc = {
            'muscle': muscle, 'sheet_row': ordinal,
            'admitting_refusal': {'code': store_code, 'detail': store_detail},
            'reproduced_detail': recomputed_detail,
            'problem_tags': problems,
            'read_path_integrity': {
                'parsed_equals_float_raw_text': read_vs_raw_ok,
                'verdict': 'no upstream extraction bug: the admitting lane read what the sheet bytes say'
                           if read_vs_raw_ok else 'EXTRACTION BUG: parsed value != float(raw_text)',
            },
        }

        if muscle == 'BFS':
            bfl = rows[BFL_SHEET_ROW - 2][0]
            twin_fields = {}
            for field in ('fl_m', 'pcsa_m2', 'penn_deg'):
                twin_fields[field] = {
                    'BFS_raw': raws[field], 'BFL_raw': bfl.get(header[field], '').strip(),
                    'byte_identical': raws[field] == bfl.get(header[field], '').strip()}
            row_doc['diagnosis'] = {
                'law': 'no blanks',
                'blank_required_fields': [f for f in ('musc_mass', 'belly_mass', 'tendon_mass')
                                          if not raws[f]],
                'also_blank': [f for f in ('musc_len', 'belly_len', 'tendon_len')
                               if not raws[f]],
                'BFL_twin_fields': twin_fields,
                'package_scan': package_scan,
            }
            row_doc['verdict'] = 'GENUINELY_BAD'
            row_doc['cause_class'] = 'source_gap'
            row_doc['cause_statement'] = (
                'The published sheet itself carries EMPTY mass and length cells for Macaca '
                'BFS (6.82-free row: no digits to misread); the only numbers present (FL, '
                'PCSA, pennation) are byte-identical copies of the BFL row, so they are not '
                'independent BFS measurements; the paper fulltext and S2 docx carry no '
                'numeric masses at any BFS mention. The admitting refusal (invalid_number) '
                'was faithful to the bytes. Quarantine right; nothing to recover from.')
            rows_out[muscle] = row_doc
            continue

        # ------------------------------------------ failing-law arithmetic, both sides
        if store_code == 'pcsa_closure_violation':
            pred = vals['musc_mass'] / 1000.0 / (RHO * vals['fl_m'])
            law_doc = {
                'law': 'PCSA closure: musc_mass_g/1000/(1060*FL_m) == PCSA_m2 within 2%',
                'left_side_predicted_pcsa_m2': pred,
                'right_side_sheet_pcsa_m2': vals['pcsa_m2'],
                'rel_deviation_vs_sheet': (pred - vals['pcsa_m2']) / vals['pcsa_m2'],
                'additivity_side': {'belly_plus_tendon_g': vals['belly_mass'] + vals['tendon_mass'],
                                    'whole_g': vals['musc_mass'],
                                    'rel_dev': abs(vals['belly_mass'] + vals['tendon_mass'] - vals['musc_mass']) / vals['musc_mass'],
                                    'status': 'PASS (corroborates musc_mass within 2%)'},
            }
            candidates = {
                'pcsa_m2': {'value': pred,
                            'equation': 'PCSA := musc_mass_g/1000/(1060*FL_m)',
                            'band_quantity': 'spec_pcsa',
                            'band_value': pred / vals['musc_mass']},
                'fl_m': {'value': vals['musc_mass'] / 1000.0 / (RHO * vals['pcsa_m2']),
                         'equation': 'FL := musc_mass_g/1000/(1060*PCSA_m2)',
                         'band_quantity': 'fl',
                         'band_value': vals['musc_mass'] / 1000.0 / (RHO * vals['pcsa_m2'])},
                'musc_mass': {'value': vals['pcsa_m2'] * RHO * vals['fl_m'] * 1000.0,
                              'equation': 'musc_mass := PCSA*1060*FL*1000',
                              'band_quantity': None, 'band_value': None},
            }
        else:
            parts = vals['belly_mass'] + vals['tendon_mass']
            law_doc = {
                'law': 'mass additivity: belly_mass + tendon_mass == musc_mass within 2%',
                'left_side_parts_g': parts,
                'right_side_whole_g': vals['musc_mass'],
                'rel_deviation_vs_whole': abs(parts - vals['musc_mass']) / vals['musc_mass'],
                'direction': 'parts_exceed_whole' if parts > vals['musc_mass'] else 'parts_fall_short_of_whole',
                'closure_side': {
                    'predicted_pcsa_m2': vals['musc_mass'] / 1000.0 / (RHO * vals['fl_m']),
                    'sheet_pcsa_m2': vals['pcsa_m2'],
                    'note': 'the sheet PCSA column recomputes from the whole mass and FL - '
                            'the whole is the value the published PCSA was derived from'},
            }
            candidates = {
                'belly_mass': {'value': vals['musc_mass'] - vals['tendon_mass'],
                               'equation': 'belly := musc_mass - tendon_mass',
                               'band_quantity': 'belly_frac',
                               'band_value': (vals['musc_mass'] - vals['tendon_mass']) / vals['musc_mass']},
                'tendon_mass': {'value': vals['musc_mass'] - vals['belly_mass'],
                                'equation': 'tendon := musc_mass - belly_mass',
                                'band_quantity': 'tendon_frac',
                                'band_value': (vals['musc_mass'] - vals['belly_mass']) / vals['musc_mass']},
                'musc_mass': {'value': parts,
                              'equation': 'musc_mass := belly_mass + tendon_mass',
                              'band_quantity': None, 'band_value': None},
            }
        row_doc['law_failure'] = law_doc
        row_doc['unit_class_test'] = {
            'ratio_two_sides': (law_doc.get('left_side_predicted_pcsa_m2', 0) or
                                law_doc.get('left_side_parts_g', 0)) /
                               (law_doc.get('right_side_sheet_pcsa_m2', 1) or
                                law_doc.get('right_side_whole_g', 1)),
        }
        ratio = row_doc['unit_class_test']['ratio_two_sides']
        row_doc['unit_class_test']['clean_factor'] = unit_factor_kind(ratio, 1.0)

        # ------------------------------------------ candidate corrections
        band_doc = band(muscle, None)
        cand_out = {}
        survivors = []
        for cell_name, cand in candidates.items():
            corrected = dict(vals)
            corrected[cell_name] = cand['value']
            code2, _, _ = adapter_laws(corrected)
            digit_kind = digit_edit_kind(raws[cell_name], cand['value']) if raws[cell_name] else None
            out = {'cell': cites.get(cell_name, f'{SHEET}/{col_letters(header[cell_name])}{ordinal}'),
                   'raw_text': raws[cell_name],
                   'corrected_value': cand['value'],
                   'corrected_value_display': format(cand['value'], '.6g'),
                   'equation': cand['equation'],
                   'laws_after_correction': 'ALL_GREEN' if code2 is None else f'FAILS:{code2}',
                   'digit_edit_signature': digit_kind,
                   'clean_unit_factor': unit_factor_kind(cand['value'], float(raws[cell_name]))
                   if raws[cell_name] else None}
            if code2 is None:
                if cand['band_quantity'] is not None:
                    verdict_band = in_band(cand['band_value'], band_doc, cand['band_quantity'])
                    out['band_test'] = {'quantity': cand['band_quantity'],
                                        'value': cand['band_value'], **verdict_band}
                    if verdict_band['in_band']:
                        survivors.append((cell_name, out))
                else:
                    out['band_test'] = {'quantity': None,
                                        'note': 'whole-mass candidate; adjudicated by the closure '
                                                'side of law_failure (recompute of the sheet PCSA column)'}
                    survivors.append((cell_name, out))
            cand_out[cell_name] = out
        row_doc['candidate_single_cell_corrections'] = cand_out
        row_doc['admitted_comparison_band_other_species'] = band_doc

        if len(survivors) == 1:
            cell_name, out = survivors[0]
            row_doc['verdict'] = 'RECOVERABLE'
            row_doc['cause_class'] = 'single_cell_entry_error_or_source_inconsistency'
            row_doc['fix_spec'] = {
                'note': 'FIX SPEC ONLY - NOT executed here, NO store change, the pinned '
                        'xlsx is NEVER edited; a future lane must re-run the admission '
                        'laws and the pairing with this override recorded as a derivation, '
                        'with the raw cell and this diagnosis carried as provenance.',
                'cell': out['cell'], 'raw_text': out['raw_text'],
                'derived_value': out['corrected_value'],
                'derived_value_display': out['corrected_value_display'],
                'equation': out['equation'],
                'band_test': out['band_test'],
                'digit_edit_signature': out['digit_edit_signature'],
                'force_consequence_N': SPECIFIC_TENSION_N_PER_CM2 * vals['pcsa_m2'] * 1.0e4,
                'force_law': 'F_max_N = 30.0 * PCSA_m2 * 1e4 (PCSA unchanged by this fix)',
            }
        else:
            row_doc['verdict'] = 'GENUINELY_BAD'
            row_doc['cause_class'] = ('undecidable_partition' if len(survivors) > 1
                                      else 'no_lawful_single_cell_completion')
        rows_out[muscle] = row_doc

    # SAR decimal-slip variant (documented, not the spec value)
    sar = rows_out['SAR']
    sar_variant_belly, sar_variant_tendon = 9.39, 0.09
    sar['documented_variant_not_adopted'] = {
        'story': 'tendon 0.9 entered for 0.09 (decimal-point slip, clean factor 10 on one '
                 'cell); leaves additivity at 0.85% (lawful, not exact)',
        'additivity_dev_if_adopted': abs(sar_variant_belly + sar_variant_tendon - 9.4) / 9.4,
        'why_not_spec': 'F4 requires the equation-derived value; 0.09 is not derivable '
                        'from the sheet alone',
    }

    # ------------------------------------------------ narrative causes (measured)
    rows_out['AB']['cause_statement'] = (
        'Closure off by +68.4% (predicted 1.50086e-4 m2 vs sheet 8.91e-05 m2). Class B '
        '(digit-entry) FALSIFIED: neither single-cell completion shows a keystroke '
        'signature and neither lands in the admitted cross-species band (corrected PCSA '
        '3.06e-5 g-1 is 2.2x above the admitted specific-PCSA max; corrected FL 0.0519 m '
        'is below the admitted FL band min). No clean unit factor anywhere. The sheet has '
        'two PCSA display classes (6-significant-digit computed values and 3-digit '
        'rounded); AB 8.91E-5 is 3-digit-rounded yet disagrees with its own row by 68% - '
        'the value was rounded from a computation inconsistent with BOTH current cells '
        '(edited later or from a different measurement round). AB rows are corrupted '
        'across species (Hylobates leg1 closure +76.9%, leg2 additivity +18.4% + a 12 mm '
        'FL outlier). Undecidable origin; quarantine right.')
    rows_out['RF']['cause_statement'] = (
        'Parts fall short of whole by 0.75 g (2.34%). Whole mass is corroborated (sheet '
        'PCSA 2.93644e-4 recomputes exactly from 32.06 g and FL 0.103). Both single-cell '
        'completions land far outside the admitted RF bands (corrected belly 89.86% vs '
        'band [97.46, 99.98]%; corrected tendon 12.48% vs [0.016, 2.10]%) and neither '
        'shows a keystroke signature; whole := 31.31 breaks closure by -2.36%. The same '
        'partition failure recurs in Pan troglodytes RF (+3.83%, also refused) - a '
        'systematically inconsistent measurement at source, not a typo. Quarantine right.')
    rows_out['TP']['cause_statement'] = (
        'Parts exceed whole by 0.86 g (6.04%). Whole mass corroborated (PCSA recomputes '
        'exactly; belly+tendon lengths also partition the whole length exactly at 0.00% '
        'deviation). BOTH single-cell completions stay inside the admitted TP bands '
        '(tendon := 0.14 g -> 0.98% in [0.17, 40.60]; belly := 13.25 g -> 93.0% in '
        '[59.40, 99.83]) and neither shows a keystroke signature - the data cannot name '
        'the wrong cell, and choosing one would be taste. Undecidable partition; '
        'quarantine right.')
    rows_out['ObtInt']['cause_statement'] = (
        'Parts fall short of whole by 2.02 g (22.47%). Whole corroborated (PCSA '
        'recomputes exactly). Tendon candidate excluded: corrected tendon 2.17 g would '
        'be 24.1% of whole vs admitted band [0.10, 6.23]% (4x out) while the sheet '
        'tendon 0.15 g sits mid-band; belly candidate lands in-band (98.33% vs [93.77, '
        '99.90]%) - the raw belly 6.82 g (75.86%) is the outlier cell. Unique lawful '
        'completion; RECOVERABLE.')
    rows_out['SAR']['cause_statement'] = (
        'Parts exceed whole by 0.89 g (9.47%). Whole corroborated (3-digit PCSA 4.07E-5 '
        'recomputes from 9.4 g to +0.062%). Belly candidate excluded: corrected belly '
        '8.5 g would be 90.43% of whole vs admitted band [91.59, 99.94]% (every admitted '
        'SAR is a strap muscle with belly >= 98% except Hylobates row56, whose 91.59% '
        'comes with a genuinely additive 8.41% tendon); corrected tendon := 0.01 g lands '
        'mid-band (0.106% in [0.057, 8.41]). Raw 0.9 shows no keystroke signature to '
        '0.01; the decimal-slip variant 0.09 (also lawful, 0.85% residual) is documented '
        'and NOT adopted (F4: equation only). Unique lawful completion; RECOVERABLE.')

    # ------------------------------------------------ artifacts
    forensics_doc = {
        'schema': 'chimera.quarantine_forensics_table.v1',
        'carrier': CARRIER, 'carrier_ref': CARRIER_REF,
        'inputs': {'xlsx_sha256': XLSX_PIN, 'store_sha256': STORE_PIN,
                   'adapter_sha256': ADAPTER_PIN},
        'f1_identity': {
            'store_refusals_total': len(store_refusals),
            'recomputed_refusal_set_equal': True,
            'macaque_refusal_rows': sorted(int(l.rsplit('row', 1)[1]) for l in maca),
            'refusal_detail_strings_reproduced_byte_exactly': True,
            'store_subjects': subjects, 'store_record_count': record_count,
            'count_identity': f'{with_penn}x9 + {without_penn}x8 = {record_count}',
            'quarantined_six_have_zero_store_records': True,
        },
        'verdict_table': {m: rows_out[m]['verdict'] for m in SIX},
        'rows': rows_out,
    }
    out_dir = __file__.rsplit('\\', 1)[0].replace('/', '\\')
    import os
    out_dir = os.path.dirname(os.path.abspath(__file__))
    for name, doc in (('raw_cells.json', raw_cells_doc),
                      ('forensics_table.json', forensics_doc)):
        with open(f'{out_dir}/{name}', 'w', encoding='utf-8', newline='\n') as handle:
            handle.write(json.dumps(doc, indent=1, sort_keys=True) + '\n')
    print(json.dumps({
        'verdicts': forensics_doc['verdict_table'],
        'store_records': record_count,
        'count_identity': forensics_doc['f1_identity']['count_identity'],
        'recoverable': [m for m in SIX if rows_out[m]['verdict'] == 'RECOVERABLE'],
        'genuinely_bad': [m for m in SIX if rows_out[m]['verdict'] == 'GENUINELY_BAD'],
        'package_scan_bfs_numeric_mass': [s['numeric_mass_at_any_mention'] for s in package_scan],
    }, indent=1))


if __name__ == '__main__':
    main()
