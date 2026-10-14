"""Force-annotate the Wiseman macaque assembly with the admitted Guimaraes numbers.

Rule-0 lane (receipt.json in this directory, preregistered before this builder ran).
Reads the admitted Guimaraes 2026 batch READ-ONLY from carrier commit 46ed85a3
(via `git show`, verified against the member sha256 pin; the carrier ref is never
merged, never modified), pairs the exact-matched muscles with the repo's own
specific-tension datum (LightEngine/kinematic/muscles.py:
SPECIFIC_TENSION_N_PER_CM2 = 30.0 -> F_max_N = 30.0 * PCSA_m2 * 1e4), and emits:

  macaque_assembly_force_annotated.json  the adapter's macaque_assembly.json with
                                         per-muscle force records, force_runtime_ready
                                         true on exactly the lawfully-paired muscles, and
                                         a force_pairing_status section naming the
                                         deferred slips, the Guimaraes-only muscles, and
                                         the rows the admitting lane's own laws
                                         quarantined.
  audit_table.json                       muscle -> Guimaraes row -> sha for every emitted
                                         number, plus the closure arithmetic, the store
                                         cross-check, and a completeness scan (F3).

MEASURED LAW OF THE BATCH (the admitting lane's preregistered rules, re-measured here
row by row and cross-checked against the admitted store at 46ed85a3): a sheet row is
ADMITTED only if it passes PCSA closure (PCSA = mass_kg/(1060*FL), 2%) and belly+tendon
mass additivity (2%) with no blank required field; length additivity is NOT enforced
(recorded condition). Six Macaca mulatta rows fail (AB, BFS, ObtInt, RF, SAR, TP) and
the store provably holds no records for them - 30 muscles, 265 records, count identity
exact. Their numbers are quarantined data: audited here with their failure modes, but
NO force is derived from them and force_runtime_ready stays false on the five of them
that are exact name matches. The mission's assumed count 28 is falsified to its lawful
count 23 by this measurement; nothing was tuned to avoid that.

Deterministic by construction: no timestamps, fixed key order, CPython float repr.
Re-running this script must produce byte-identical artifacts (falsifier F5).

Units follow the admitting lane's derivation (tools/science_funnel/adapters_muscle.py):
FL/PCSA really are m/m^2; the mass columns carry grams despite their headers; pennation
is degrees. Conversions go through the repo's own tools/science_funnel/units.convert.
"""
import hashlib
import io
import json
import math
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from tools.science_funnel.units import convert  # the admitting lane's converter

CARRIER_REF = 'refs/remotes/origin/agent/skeleton-movie-20260919'
CARRIER_COMMIT = '46ed85a3ba1e451cf5b02f068134bf6801dbd258'
XLSX_PATH = 'tools/science_funnel/data/guimaraes_arch/AJPA-190-e70329-s001.xlsx'
XLSX_PIN_SHA256 = '08ead4a901a53f97e136c709a7804b9d04b4b903107e873c01f3b9b5b9eb8678'
XLSX_PIN_BYTES = 321899
STORE_PATH = 'tools/creature_graph/data/creature_graph.json'
SHEET = 'Macaca mulatta'
RHO_KG_M3 = 1060.0
LAW_TOLERANCE = 0.02  # the admitting lane's cut; length additivity is NOT enforced
SPECIFIC_TENSION_N_PER_CM2 = 30.0  # LightEngine/kinematic/muscles.py line 79 (ANATOMY-DATUM)
N_PER_M2 = SPECIFIC_TENSION_N_PER_CM2 * 1.0e4  # 30 N/cm^2 in N/m^2

ADAPTER_DIR = ROOT / 'tools/science_funnel/validation/osim4_adapter_20260920'
ASSEMBLY_PATH = ADAPTER_DIR / 'macaque_assembly.json'
MATCH_TABLE_PATH = ADAPTER_DIR / 'guimaraes_match_table.json'
NAME_PAIRING_PATH = ADAPTER_DIR / 'guimaraes_name_pairing.json'
MUSCLES_PY = ROOT / 'LightEngine/kinematic/muscles.py'

HEADER_VARIANTS = {
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
REQUIRED = ('species', 'muscle', 'fl_m', 'pcsa_m2', 'musc_mass', 'belly_mass', 'tendon_mass')

_SSML = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
_OFFDOC = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
_PKGREL = 'http://schemas.openxmlformats.org/package/2006/relationships'


def refuse(code, detail):
    raise SystemExit(f'REFUSAL {code}: {detail}')


def git_show(path_or_ref):
    return subprocess.run(['git', 'show', path_or_ref], cwd=ROOT,
                          capture_output=True, check=True).stdout


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def pin(name, condition, detail):
    if not condition:
        refuse(name, detail)


# ------------------------------------------------------------------ xlsx reading

def _column_index(ref):
    letters = re.match(r'([A-Z]+)', ref).group(1)
    out = 0
    for ch in letters:
        out = out * 26 + (ord(ch) - 64)
    return out - 1


def _column_letters(index):
    out = ''
    index += 1
    while index:
        index, rem = divmod(index - 1, 26)
        out = chr(65 + rem) + out
    return out


def _workbook(raw):
    archive = zipfile.ZipFile(io.BytesIO(raw))
    workbook = ET.fromstring(archive.read('xl/workbook.xml'))
    rels = ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))
    rid_to_target = {rel.get('Id'): rel.get('Target')
                     for rel in rels.findall(f'{{{_PKGREL}}}Relationship')}
    out = []
    for sheet in workbook.iter(f'{{{_SSML}}}sheet'):
        target = rid_to_target[sheet.get(f'{{{_OFFDOC}}}id')]
        if not target.startswith('xl/'):
            target = 'xl/' + target.lstrip('/')
        out.append((sheet.get('name'), target))
    return archive, out


def _shared_strings(archive):
    if 'xl/sharedStrings.xml' not in archive.namelist():
        return []
    root = ET.fromstring(archive.read('xl/sharedStrings.xml'))
    return [''.join(t.text or '' for t in si.iter(f'{{{_SSML}}}t'))
            for si in root.findall(f'{{{_SSML}}}si')]


def _sheet_rows(archive, target, shared):
    root = ET.fromstring(archive.read(target))
    out = []
    for row in root.iter(f'{{{_SSML}}}row'):
        cells = {}
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
                cells[_column_index(cell.get('r'))] = str(value)
        out.append(cells)
    return out


# ------------------------------------------------------------------ batch read

def admitted_store_subjects():
    """The macaque muscle subjects ACTUALLY admitted at 46ed85a3 (independent of the
    sheet: this is the store the admitting lane wrote)."""
    raw = git_show(f'{CARRIER_COMMIT}:{STORE_PATH}')
    text = raw.decode('utf-8')
    subjects = sorted({s.rsplit('/', 1)[-1].split(' ')[0]
                       for s in re.findall(r'Macaca_mulatta/muscle/[A-Za-z]+ \([RL]\)', text)})
    record_count = len(re.findall(r'Macaca_mulatta/muscle/', text))
    return subjects, record_count


def read_batch():
    """Sha-pinned read + admission-law classification of the Macaca mulatta sheet."""
    probe = subprocess.run(['git', 'merge-base', '--is-ancestor', CARRIER_COMMIT, CARRIER_REF],
                           cwd=ROOT, capture_output=True)
    pin('F1_carrier', probe.returncode == 0,
        f'{CARRIER_COMMIT} is not an ancestor of {CARRIER_REF}')
    raw = git_show(f'{CARRIER_COMMIT}:{XLSX_PATH}')
    pin('F1_pin', sha256(raw) == XLSX_PIN_SHA256 and len(raw) == XLSX_PIN_BYTES,
        f'xlsx bytes {sha256(raw)}/{len(raw)} vs pin {XLSX_PIN_SHA256}/{XLSX_PIN_BYTES}')
    receipt = json.loads(git_show(
        f'{CARRIER_COMMIT}:{XLSX_PATH.rsplit("/", 1)[0]}/download_receipt.json'))
    member = next(f for f in receipt['files'] if f['path'] == XLSX_PATH.rsplit('/', 1)[1])
    pin('F1_receipt', member['sha256'] == XLSX_PIN_SHA256 and member['bytes'] == XLSX_PIN_BYTES,
        'carrier download_receipt.json disagrees with the preregistered pin')

    archive, sheets = _workbook(raw)
    shared = _shared_strings(archive)
    target = dict(sheets)[SHEET]

    info_rows = _sheet_rows(archive, dict(sheets)['Information '], shared)
    specimen = None
    header = None
    for cells in info_rows:
        values = [v.strip() for v in cells.values()]
        if len(values) >= 6 and values[0].startswith('Specimen'):
            header = values
        if header and values and values[0].startswith('127') and 'Macaca' in ' '.join(values):
            specimen = dict(zip(header, values))
    pin('F2_specimen', specimen is not None, 'specimen 127 row not found in Information sheet')

    rows = _sheet_rows(archive, target, shared)
    header = {}
    for column, label in rows[0].items():
        canonical = HEADER_VARIANTS.get(label.strip())
        pin('F2_header', canonical is not None, f'unknown header {label!r}')
        header[canonical] = column
    for field in REQUIRED:
        pin('F2_header', field in header, f'required column {field} missing')

    out = {}
    for ordinal, cells in enumerate(rows[1:], 2):
        if not cells:
            continue
        pin('F2_species', cells.get(header['species'], '').strip() == 'Macaca_mulatta',
            f'sheet row {ordinal} is not Macaca_mulatta')
        muscle = cells.get(header['muscle'], '').strip()
        pin('F2_unique', muscle not in out, f'duplicate row for {muscle}')
        raws, values, problems = {}, {}, []
        for field in ('fl_m', 'pcsa_m2', 'musc_mass', 'belly_mass', 'tendon_mass'):
            col = header[field]
            text = cells.get(col, '').strip()
            raws[field] = text
            if text == '':
                values[field] = None
                problems.append(f'{field}_blank')
            else:
                values[field] = float(text)
        penn_col = header.get('penn_deg')
        penn_raw = cells.get(penn_col, '').strip() if penn_col is not None else ''
        raws['penn_deg'] = penn_raw or None
        values['penn_deg'] = float(penn_raw) if penn_raw else None
        # The admitting lane's ENFORCED laws (length additivity is a recorded condition,
        # never a quarantine). A violating row quarantines whole - prediction P3 said all
        # 36 macaque rows would pass; measured here, and cross-checked against the store.
        if values['fl_m'] is not None and values['pcsa_m2'] is not None \
                and values['musc_mass'] is not None:
            mass_kg = values['musc_mass'] / 1000.0
            pcsa_pred = mass_kg / (RHO_KG_M3 * values['fl_m'])
            if not math.isclose(pcsa_pred, values['pcsa_m2'], rel_tol=LAW_TOLERANCE):
                problems.append(
                    f'pcsa_closure_dev_{(pcsa_pred - values["pcsa_m2"]) / values["pcsa_m2"]:.3f}')
        if None not in (values['belly_mass'], values['tendon_mass'], values['musc_mass']):
            dev = abs(values['belly_mass'] + values['tendon_mass']
                      - values['musc_mass']) / values['musc_mass']
            if dev > LAW_TOLERANCE:
                problems.append(f'mass_additivity_dev_{dev:.3f}')
        out[muscle] = {
            'sheet_row': ordinal,
            'cells': {f: f'{_column_letters(header[f])}{ordinal}' for f in raws},
            'raws': raws,
            'values': values,
            'admitted': not problems,
            'problems': problems,
        }
    return out, {'bytes': len(raw), 'sha256': sha256(raw), 'receipt': receipt,
                 'sheet_names': [n for n, _ in sheets], 'specimen': specimen}


def force_n(pcsa_m2):
    return N_PER_M2 * pcsa_m2


def guimaraes_numbers(row):
    v = row['values']
    return {
        'fl_m': v['fl_m'],
        'pcsa_m2': v['pcsa_m2'],
        'musc_mass_kg': convert(v['musc_mass'], 'g', 'mass')['value_si'],
        'belly_mass_kg': convert(v['belly_mass'], 'g', 'mass')['value_si'],
        'tendon_mass_kg': convert(v['tendon_mass'], 'g', 'mass')['value_si'],
        'penn_deg': v['penn_deg'],
        'pennation_angle_at_optimal_rad': (None if v['penn_deg'] is None
                                           else convert(v['penn_deg'], 'deg', 'angle')['value_si']),
        'max_isometric_force_N': force_n(v['pcsa_m2']),
        'optimal_fiber_length_m': v['fl_m'],
    }


def provenance(row, batch_meta):
    spec = batch_meta['specimen']
    return {
        'ref': CARRIER_REF,
        'commit': CARRIER_COMMIT,
        'path': XLSX_PATH,
        'member_sha256': XLSX_PIN_SHA256,
        'member_bytes': batch_meta['bytes'],
        'sheet': SHEET,
        'sheet_row': row['sheet_row'],
        'cells': row['cells'],
        'specimen': {'id': spec['Specimen ID'], 'species': spec['Species'],
                     'sex': spec['Sex'], 'age': spec['Age at death (yrs)'],
                     'body_mass_kg_raw': spec['Body Mass (kg)'],
                     'limb_dissected': spec['Limb dissected']},
        'law': {
            'max_isometric_force': 'F_max_N = SPECIFIC_TENSION_N_PER_CM2 (30.0, '
                                   'LightEngine/kinematic/muscles.py:79 ANATOMY-DATUM) '
                                   '* PCSA_m2 * 1e4',
            'pcsa_closure': 'PCSA = musc_mass_kg / (1060 kg/m^3 * FL_m), enforced at 2% '
                            '(the admitting lane\'s quarantine law; re-measured here)',
            'optimal_fiber_length': 'sheet FL_m (resting fascicle length) mapped to Millard '
                                    'optimal_fiber_length; declared convention',
        },
    }


# ------------------------------------------------------------------ audit

def audit(muscle, guim, field, kind, value, row, raw_field, extra=None):
    entry = {
        'muscle': muscle,
        'guimaraes': guim,
        'field': field,
        'kind': kind,
        'value': value,
        'sheet_row': row['sheet_row'],
        'raw_cell': row['cells'].get(raw_field),
        'raw_text': row['raws'].get(raw_field),
        'member_sha256': XLSX_PIN_SHA256,
        'source_ref': CARRIER_REF,
        'source_commit': CARRIER_COMMIT,
        'source_path': XLSX_PATH,
    }
    if extra:
        entry.update(extra)
    return entry


def audit_row_numbers(muscle, guim, row, recorded_only=None, kind_prefix=''):
    """Audit rows for the measured/converted/derived numbers of one admitted row."""
    numbers = guimaraes_numbers(row)
    tag = recorded_only or {}
    rows_ = [
        audit(muscle, guim, 'fl_m', kind_prefix + 'measured', numbers['fl_m'], row, 'fl_m', tag),
        audit(muscle, guim, 'pcsa_m2', kind_prefix + 'measured', numbers['pcsa_m2'], row, 'pcsa_m2', tag),
        audit(muscle, guim, 'musc_mass_kg', kind_prefix + 'converted', numbers['musc_mass_kg'],
              row, 'musc_mass', {'conversion': 'g -> kg (/1000, units.convert)', **tag}),
        audit(muscle, guim, 'belly_mass_kg', kind_prefix + 'converted', numbers['belly_mass_kg'],
              row, 'belly_mass', {'conversion': 'g -> kg (/1000, units.convert)', **tag}),
        audit(muscle, guim, 'tendon_mass_kg', kind_prefix + 'converted', numbers['tendon_mass_kg'],
              row, 'tendon_mass', {'conversion': 'g -> kg (/1000, units.convert)', **tag}),
    ]
    if numbers['penn_deg'] is not None:
        rows_.append(audit(muscle, guim, 'penn_deg', kind_prefix + 'measured',
                           numbers['penn_deg'], row, 'penn_deg', tag))
        rows_.append(audit(muscle, guim, 'pennation_angle_at_optimal_rad',
                           kind_prefix + 'converted', numbers['pennation_angle_at_optimal_rad'],
                           row, 'penn_deg', {'conversion': 'deg -> rad (units.convert)', **tag}))
    rows_.append(audit(muscle, guim, 'max_isometric_force_N', kind_prefix + 'derived',
                       numbers['max_isometric_force_N'], row, 'pcsa_m2',
                       {'law': 'F = 30.0 N/cm^2 * PCSA_m2 * 1e4', **tag}))
    rows_.append(audit(muscle, guim, 'optimal_fiber_length_m', kind_prefix + 'mapped',
                       numbers['optimal_fiber_length_m'], row, 'fl_m',
                       {'law': 'resting fascicle length -> Millard optimal_fiber_length', **tag}))
    return rows_, numbers


def audit_quarantined(muscle, guim, row):
    """Quarantined rows: raw sheet values audited with their failure mode; NO derived
    force of any kind (the batch's own laws refused these numbers at admission)."""
    rows_ = [audit(muscle, guim, 'row_status', 'quarantined_at_admission', False, row,
                   'pcsa_m2', {'problems': row['problems'],
                               'store_cross_check': 'no Macaca_mulatta/muscle record at '
                                                    + CARRIER_COMMIT})]
    for field in ('fl_m', 'pcsa_m2', 'musc_mass', 'belly_mass', 'tendon_mass', 'penn_deg'):
        if row['raws'].get(field):
            rows_.append(audit(muscle, guim, f'raw_{field}', 'quarantined_raw_text',
                               float(row['raws'][field]), row, field,
                               {'problems': row['problems'],
                                'not_admitted': True, 'no_force_derived': True}))
    return rows_


# ------------------------------------------------------------------ main

def main():
    lines = MUSCLES_PY.read_text(encoding='utf-8').splitlines()
    tension_lines = [i + 1 for i, l in enumerate(lines)
                     if l.startswith('SPECIFIC_TENSION_N_PER_CM2')]
    pin('law', len(tension_lines) == 1 and
        lines[tension_lines[0] - 1].strip() == 'SPECIFIC_TENSION_N_PER_CM2 = 30.0',
        f'SPECIFIC_TENSION line drifted: {tension_lines}')

    batch, batch_meta = read_batch()
    store_subjects, store_record_count = admitted_store_subjects()
    assembly = json.loads(ASSEMBLY_PATH.read_text(encoding='utf-8'))
    match_table = json.loads(MATCH_TABLE_PATH.read_text(encoding='utf-8'))['table']
    name_pairing = json.loads(NAME_PAIRING_PATH.read_text(encoding='utf-8'))

    pin('inputs', sha256(ASSEMBLY_PATH.read_bytes())
        == 'fcc119b953cf93d957760770e3d24884f79f9db14396e7f12b7ec4ec7857f792',
        'adapter assembly drifted from the preregistered pin')
    pin('F2_names', sorted(batch) == sorted(name_pairing['guimaraes_names_36']),
        'sheet muscle set != guimaraes_names_36')
    pin('F2_names', len(batch) == 36, f'sheet holds {len(batch)} rows, predicted 36')

    admitted_names = sorted(n for n, r in batch.items() if r['admitted'])
    quarantined_names = sorted(n for n, r in batch.items() if not r['admitted'])
    # The store cross-check: what the admitting lane actually wrote must equal what the
    # re-measured laws admit, muscle by muscle (independent second measurement).
    pin('F2_admitted', admitted_names == store_subjects,
        f'admitted-set mismatch: sheet-only={sorted(set(admitted_names) - set(store_subjects))} '
        f'store-only={sorted(set(store_subjects) - set(admitted_names))}')
    admitted_record_count = sum(9 if batch[n]['values']['penn_deg'] is not None else 8
                                for n in admitted_names)
    pin('F2_admitted', admitted_record_count == store_record_count,
        f'record-count identity broken: {admitted_record_count} vs store {store_record_count}')

    annotated = json.loads(ASSEMBLY_PATH.read_text(encoding='utf-8'))  # deep copy
    audit_rows = []
    exact_names, deferred_pairs, quarantined_exact = [], [], []
    forces = {}
    paired_forces = {}

    for m in annotated['muscles']:
        pairing = m['force_pairing']
        status = pairing['status']
        if status == 'name_exact':
            guim = pairing['guimaraes_name']
            row = batch[guim]
            if row['admitted']:
                numbers = guimaraes_numbers(row)
                forces[guim] = numbers['max_isometric_force_N']
                paired_forces[m['name']] = numbers['max_isometric_force_N']
                exact_names.append(m['name'])
                new_rows, _ = audit_row_numbers(m['name'], guim, row)
                audit_rows.extend(new_rows)
                penn_note = ('pennation measured at source'
                             if numbers['penn_deg'] is not None else
                             'pennation absent at source; carried null with treat-as-0 '
                             '(parallel fiber) declared - the Millard placeholder 0 is not '
                             'silently reused')
                m['force_pairing'] = {
                    'guimaraes_name': guim,
                    'adapter_status': status,
                    'status': 'paired_exact_admitted',
                    'note': 'paths Wiseman 2026; force, PCSA, masses and pennation from the '
                            'admitted Guimaraes 2026 batch read at carrier '
                            f'{CARRIER_COMMIT} through {CARRIER_REF}; ' + penn_note,
                    'numbers': numbers,
                    'provenance': provenance(row, batch_meta),
                }
                m['force_placeholder'] = None
                m['force_all_source_placeholder'] = False
                m['force_runtime_ready'] = True
                m['reason'] = ('Paths are Wiseman 2026; max_isometric_force derives from the '
                               'admitted Guimaraes 2026 PCSA via the repo specific-tension '
                               'datum (30.0 N/cm^2, LightEngine/kinematic/muscles.py:79); '
                               'PCSA, masses, FL and pennation are measured batch values '
                               '(provenance in force_pairing). tendon_slack_length has NO '
                               'lawful measured value and is deliberately ABSENT (not the '
                               '1 m placeholder); wrapping remains unresolved geometry data. '
                               'The batch is NOT merged: numbers travel from carrier '
                               f'{CARRIER_COMMIT} by sha-pinned read.')
            else:
                quarantined_exact.append(
                    {'wiseman': m['name'], 'guimaraes': guim,
                     'sheet_row': row['sheet_row'], 'problems': row['problems'],
                     'store_cross_check': 'no admitted record at ' + CARRIER_COMMIT})
                audit_rows.extend(audit_quarantined(m['name'], guim, row))
                m['force_pairing'] = {
                    'guimaraes_name': guim,
                    'adapter_status': status,
                    'status': 'exact_name_row_quarantined_at_admission',
                    'note': 'name matches, but the Guimaraes row for this muscle FAILED the '
                            f'admitting lane\'s own laws ({", ".join(row["problems"])}) and '
                            f'was quarantined: the store at {CARRIER_COMMIT} holds no record '
                            'for it. No force exists to pair; force_runtime_ready stays '
                            'false. Measured raw values are audited (quarantined) only.',
                    'numbers': None,
                    'provenance': provenance(row, batch_meta),
                }
        elif status == 'split_homolog_deferred':
            guim = pairing['guimaraes_name']
            row = batch[guim]
            pin('F2_deferred_source', row['admitted'],
                f'{guim} whole-muscle row is not admitted')
            deferred_pairs.append({'wiseman': m['name'], 'guimaraes': guim})
            forces[guim] = force_n(row['values']['pcsa_m2'])
        else:
            refuse('unknown_pairing_status', f'{m["name"]}: {status}')
    for name in batch:
        if batch[name]['admitted']:
            forces[name] = force_n(batch[name]['values']['pcsa_m2'])

    counts = match_table['counts']
    pin('F2_pairing', len(deferred_pairs) == counts['split_homolog_deferred'] == 8,
        f'deferred count {len(deferred_pairs)} != 8')
    absent = match_table['guimaraes_without_wiseman_record']
    pin('F2_pairing', len(absent) == counts['guimaraes_without_wiseman_record'] == 6,
        f'absent count {len(absent)} != 6')

    absent_admitted, absent_quarantined = [], []
    for name in absent:
        row = batch[name]
        if row['admitted']:
            new_rows, numbers = audit_row_numbers(None, name, row,
                                                  recorded_only={'recorded_only':
                                                                 'not in the Wiseman model'})
            audit_rows.extend(new_rows)
            absent_admitted.append({'guimaraes_name': name, 'numbers': numbers,
                                    'provenance': provenance(row, batch_meta)})
        else:
            audit_rows.extend(audit_quarantined(None, name, row))
            absent_quarantined.append({'guimaraes_name': name,
                                       'sheet_row': row['sheet_row'],
                                       'problems': row['problems'],
                                       'store_cross_check': 'no admitted record at '
                                                            + CARRIER_COMMIT})

    # Whole-muscle EDL/FDL numbers travel in the status section (recorded only - never
    # attached to a slip).
    deferred_whole = {}
    for name in ('EDL', 'FDL'):
        new_rows, numbers = audit_row_numbers(None, name, batch[name],
                                              recorded_only={'recorded_only':
                                                             'deferred whole-muscle number; '
                                                             'never attached to a slip'})
        audit_rows.extend(new_rows)
        deferred_whole[name] = {'numbers': numbers,
                                'provenance': provenance(batch[name], batch_meta)}

    # ------------------------------------------------ closure arithmetic (F6)
    force_paired = math.fsum(paired_forces.values())
    force_edl = forces['EDL']
    force_fdl = forces['FDL']
    absent_admitted_names = [r['guimaraes_name'] for r in absent_admitted]
    force_absent = math.fsum(forces[name] for name in absent_admitted_names)
    force_admitted_total = math.fsum(forces[n] for n in admitted_names)
    reconstructed = force_paired + force_edl + force_fdl + force_absent
    residual = abs(reconstructed - force_admitted_total)
    pin('F6', residual / force_admitted_total <= 1e-9,
        f'closure residual {residual} exceeds 1e-9 relative')
    pcsa = {n: batch[n]['values']['pcsa_m2'] for n in batch}
    pcsa_paired = math.fsum(pcsa[p['guimaraes']] for p in match_table['exact']
                            if batch[p['guimaraes']]['admitted'])
    pcsa_absent = math.fsum(pcsa[n] for n in absent_admitted_names)
    pcsa_admitted = math.fsum(pcsa[n] for n in admitted_names)
    pin('F6', abs(N_PER_M2 * pcsa_admitted - force_admitted_total)
        <= 1e-9 * force_admitted_total, 'sigma*sum(PCSA) != fsum(forces)')

    # --------------------------------- predictions: measured, reported, never gates
    predictions = {
        'P3_all_36_rows_pass_batch_laws': {
            'predicted': 'every Macaca mulatta row passes the admitting lane\'s enforced '
                         'laws (PCSA closure 2%, mass additivity 2%, no blanks)',
            'measured': {'passing': len(admitted_names), 'failing': len(quarantined_names),
                         'failing_rows': [{'muscle': n, 'sheet_row': batch[n]['sheet_row'],
                                           'problems': batch[n]['problems']}
                                          for n in quarantined_names],
                         'store_cross_check': 'the admitted store at ' + CARRIER_COMMIT +
                                              f' holds exactly {len(store_subjects)} macaque '
                                              f'muscles / {store_record_count} records; the '
                                              '6 failing rows have zero records'},
            'verdict': 'FALSIFIED' if quarantined_names else 'PASS',
            'consequence': 'the mission count 28 flips to its lawful count '
                           f'{len(exact_names)}: 5 of the 28 exact matches '
                           '({AB, BFS, RF, SAR, TP}) and ObtInt of the absent 6 are '
                           'quarantined data with no admitted numbers',
        },
        'P4_batch_total_N': {
            'predicted': 'between 2000 and 12000 N (written for the 36-row batch before the '
                         'quarantine measurement; the lawful realization is the admitted '
                         '30-row total)',
            'measured': force_admitted_total,
            'verdict': 'PASS' if 2000.0 <= force_admitted_total <= 12000.0 else 'FALSIFIED',
        },
        'P4_top3_plantarflexors': None,
        'P5_absent_pcsa_share': {
            'predicted': '< 15% of batch PCSA (deep hip rotators + plantaris + popliteus)',
            'measured': {'absent_admitted_5_share_of_admitted_total': pcsa_absent / pcsa_admitted},
            'verdict': 'PASS' if pcsa_absent / pcsa_admitted < 0.15 else 'FALSIFIED',
        },
    }
    top3 = sorted(admitted_names, key=lambda n: -forces[n])[:3]
    predictions['P4_top3_plantarflexors'] = {
        'predicted': 'SOL, LG, MG are the three largest forces',
        'measured': [{'muscle': n, 'force_N': forces[n]} for n in top3],
        'verdict': 'PASS' if set(top3) == {'SOL', 'LG', 'MG'} else 'FALSIFIED',
    }

    annotated['unknowns_source_output'] = annotated['unknowns']
    annotated['unknowns'] = [
        'RESOLVED for '
        f'{len(exact_names)}/36 muscles by this annotation: max_isometric_force now derives '
        'from the admitted Guimaraes 2026 batch (carrier ' + CARRIER_COMMIT + ', read '
        'sha-pinned, NOT merged) via the repo specific-tension datum 30.0 N/cm^2; 5 more '
        'exact-name matches (AB, BFS, RF, SAR, TP) have QUARANTINED rows - the admitting '
        'lane\'s own laws refused those rows and no admitted number exists, so they stay '
        'false; the 8 EDL/FDL digit-slip records stay deferred (per-slip division is an '
        'unstated law); tendon_slack_length has no lawful measured value and is absent; '
        'knee-extension and MTP-flexion straight-line paths carry the muscle_paths_20260918 '
        'falsifier (ratio 0.00) - force claims through them stay barred until via-pulley '
        'paths exist; wrapping remains unresolved geometry data',
        'display meshes (.obj) are pinned in the gitignored Zenodo deposit '
        '(Primate_models.zip sha256 6cb8e29ad6d7664beb0d3bd13fd3feee915d457d9fe65c2d93d39c44600886c)',
    ]
    annotated['force_annotation'] = {
        'lane': 'agent/guimaraes-pairing-20260921 (receipt: this directory, receipt.json)',
        'builder': 'tools/science_funnel/validation/guimaraes_pairing_20260921/'
                   'build_force_annotation.py',
        'input_artifact': {
            'path': 'tools/science_funnel/validation/osim4_adapter_20260920/'
                    'macaque_assembly.json',
            'sha256': sha256(ASSEMBLY_PATH.read_bytes()),
        },
        'law': {
            'datum': 'SPECIFIC_TENSION_N_PER_CM2 = 30.0 (ANATOMY-DATUM)',
            'home': 'LightEngine/kinematic/muscles.py:79',
            'muscles_py_sha256': sha256(MUSCLES_PY.read_bytes()),
            'derivation': 'F_max_N = 30.0 * PCSA_m2 * 1e4; sigma is a repo datum, PCSA is a '
                          'measured batch value; nothing is tuned',
        },
        'batch_source': {
            'ref': CARRIER_REF,
            'commit': CARRIER_COMMIT,
            'access': 'read-only git show; carrier never merged',
            'path': XLSX_PATH,
            'member_sha256': batch_meta['sha256'],
            'member_bytes': batch_meta['bytes'],
            'pin_authority': 'download_receipt.json at ' + CARRIER_COMMIT,
            'sheets': batch_meta['sheet_names'],
        },
        'admission_cross_check': {
            'store_path_at_carrier': STORE_PATH,
            'admitted_macaque_muscles': len(store_subjects),
            'admitted_macaque_records': store_record_count,
            'count_identity': 'admitted muscles x fields (9 with pennation / 8 without) == '
                              'store record count, exact',
            'lawful_consequence': 'force_runtime_ready flips for the admitted exact matches '
                                  f'({len(exact_names)}), not the mission-assumed 28',
        },
    }
    annotated['force_pairing_status'] = {
        'counts': {
            'exact_paired_runtime_ready': len(exact_names),
            'exact_name_but_row_quarantined': len(quarantined_exact),
            'split_homolog_deferred': len(deferred_pairs),
            'guimaraes_without_wiseman_record': len(absent),
            'guimaraes_absent_admitted': len(absent_admitted),
            'guimaraes_absent_quarantined': len(absent_quarantined),
            'unmatched': 0,
            'wiseman_muscles': len(annotated['muscles']),
            'guimaraes_batch_rows': len(batch),
            'guimaraes_admitted_rows': len(admitted_names),
        },
        'law': annotated['force_annotation']['law'],
        'exact_muscles': exact_names,
        'exact_but_quarantined': quarantined_exact,
        'split_homolog_deferred': deferred_pairs,
        'deferred_reason': 'Wiseman splits EDL and FDL into digit tendon slips II-V; the '
                           'Guimaraes batch measures EDL and FDL whole. Per-slip force '
                           'division is an unstated law (inventing one is taste), so the 8 '
                           'slip records stay force_runtime_ready=false; the whole-muscle '
                           'EDL/FDL numbers are recorded below and MUST NOT be copied onto '
                           'any single slip.',
        'deferred_whole_muscle_numbers': deferred_whole,
        'guimaraes_without_wiseman_record': absent_admitted,
        'guimaraes_absent_quarantined': absent_quarantined,
        'arithmetic': {
            'unit': 'N',
            'partition': 'admitted 30 rows = 23 exact-paired + EDL + FDL + 5 admitted '
                         'Guimaraes-only; the 6 quarantined rows (AB, BFS, ObtInt, RF, '
                         'SAR, TP) carry no lawful numbers and appear in no sum',
            'sum_23_paired': force_paired,
            'F_EDL_whole': force_edl,
            'F_FDL_whole': force_fdl,
            'sum_5_absent_admitted': force_absent,
            'sum_30_admitted_batch_total': force_admitted_total,
            'identity': 'sum_23_paired + F_EDL_whole + F_FDL_whole + sum_5_absent_admitted '
                        '== sum_30_admitted_batch_total',
            'reconstructed': reconstructed,
            'abs_residual_N': residual,
            'rel_residual': residual / force_admitted_total,
            'pcsa_form': {'pcsa_23_paired_m2': pcsa_paired, 'pcsa_EDL_m2': pcsa['EDL'],
                          'pcsa_FDL_m2': pcsa['FDL'], 'pcsa_5_absent_admitted_m2': pcsa_absent,
                          'pcsa_30_admitted_m2': pcsa_admitted,
                          'absent5_share_of_admitted_pcsa': pcsa_absent / pcsa_admitted},
        },
        'declared_gaps': [
            'QUARANTINE LAYER: 6 of the 36 sheet rows (AB, BFS, ObtInt, RF, SAR, TP) failed '
            'the admitting lane\'s enforced laws and have NO admitted numbers at '
            f'{CARRIER_COMMIT}; 5 of them are exact name matches, so the mission-assumed '
            f'count 28 is falsified to its lawful count {len(exact_names)}',
            'tendon_slack_length: no lawful measured value; absent from all force records '
            '(the batch\'s external tendon length is a dissected length whose additivity the '
            'batch itself does not enforce)',
            'pennation absent at source for some rows: carried null with treat-as-0 declared '
            '(see per-muscle notes)',
            'knee extension and MTP flexion: barred from force claims through the '
            'straight-line path proxy (muscle_paths_20260918 falsifier, ratio 0.00) until '
            'via-pulley paths are derived',
            'the 8 digit slips: deferred (see deferred_reason)',
        ],
    }

    # ------------------------------------------------ completeness scan (F3/F4)
    def walk_numbers(node):
        found = set()
        if isinstance(node, dict):
            for key, value in node.items():
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    found.add((key, value))
                else:
                    found |= walk_numbers(value)
        elif isinstance(node, list):
            for item in node:
                found |= walk_numbers(item)
        return found

    emitted = walk_numbers(annotated['force_pairing_status']) | \
        {f for m in annotated['muscles'] for f in walk_numbers(m['force_pairing'])}
    audited = {(r['field'], r['value']) for r in audit_rows}
    data_fields = ('fl_m', 'pcsa_m2', 'musc_mass_kg', 'belly_mass_kg', 'tendon_mass_kg',
                   'penn_deg', 'pennation_angle_at_optimal_rad', 'max_isometric_force_N',
                   'optimal_fiber_length_m')
    unprovenanced = {(f, v) for f, v in emitted - audited if f in data_fields}
    force_numbers = {(f, v) for f, v in emitted if f == 'max_isometric_force_N'}
    force_audited = {(r['field'], r['value']) for r in audit_rows
                     if r['field'] == 'max_isometric_force_N'}
    pin('F3', not unprovenanced, f'numbers without audit rows: {sorted(unprovenanced)[:5]}')
    pin('F4', force_numbers <= force_audited,
        f'force numbers without provenance: {sorted(force_numbers - force_audited)[:5]}')
    completeness = {
        'emitted_data_numbers': len(emitted),
        'audit_rows': len(audit_rows),
        'unaudited': 0,
        'force_numbers_emitted': len(force_numbers),
        'force_numbers_without_provenance': 0,
        'quarantined_values_audited_without_force': True,
        'verdict': 'PASS',
    }

    audit_doc = {
        'schema': 'chimera.guimaraes_pairing_audit.v1',
        'lane': 'agent/guimaraes-pairing-20260921',
        'source': annotated['force_annotation']['batch_source'],
        'inputs': {
            'head': subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT,
                                   capture_output=True, check=True).stdout.decode().strip(),
            'assembly': {'path': str(ASSEMBLY_PATH.relative_to(ROOT)),
                         'sha256': sha256(ASSEMBLY_PATH.read_bytes())},
            'match_table': {'path': str(MATCH_TABLE_PATH.relative_to(ROOT)),
                            'sha256': sha256(MATCH_TABLE_PATH.read_bytes())},
            'name_pairing': {'path': str(NAME_PAIRING_PATH.relative_to(ROOT)),
                             'sha256': sha256(NAME_PAIRING_PATH.read_bytes())},
            'wiseman_osim_py': {'path': 'tools/science_funnel/wiseman_osim.py',
                                'sha256': sha256((ROOT / 'tools/science_funnel/wiseman_osim.py')
                                                 .read_bytes())},
            'muscles_py': {'path': 'LightEngine/kinematic/muscles.py',
                           'sha256': sha256(MUSCLES_PY.read_bytes())},
        },
        'laws': {
            'specific_tension': {'value_N_per_cm2': SPECIFIC_TENSION_N_PER_CM2,
                                 'home': 'LightEngine/kinematic/muscles.py:79',
                                 'kind': 'ANATOMY-DATUM (repo-authored, nothing tuned)'},
            'pcsa_closure': {'law': 'PCSA = mass_kg / (1060 * FL)', 'tolerance': 0.02,
                             'enforced': True},
            'mass_additivity': {'law': 'belly + tendon == whole', 'tolerance': 0.02,
                                'enforced': True},
            'length_additivity': {'law': 'belly + tendon == whole',
                                  'enforced': False,
                                  'note': 'the admitting lane records it as a per-row '
                                          'condition, never a quarantine'},
            'conversions': {'g_to_kg': '/1000 via tools/science_funnel/units.convert',
                            'deg_to_rad': 'units.convert'},
        },
        'admission_cross_check': {
            'store_subjects': store_subjects,
            'store_record_count': store_record_count,
            'sheet_admitted_set_equal': True,
            'quarantined_rows': [{'muscle': n, 'sheet_row': batch[n]['sheet_row'],
                                  'problems': batch[n]['problems']} for n in quarantined_names],
        },
        'specimen': batch_meta['specimen'],
        'predictions_measured': predictions,
        'completeness_scan': completeness,
        'closure': annotated['force_pairing_status']['arithmetic'],
        'rows': audit_rows,
    }

    out_dir = Path(__file__).resolve().parent
    for name, doc in (('macaque_assembly_force_annotated.json', annotated),
                      ('audit_table.json', audit_doc)):
        (out_dir / name).write_text(json.dumps(doc, indent=1, sort_keys=True) + '\n',
                                    encoding='utf-8')

    print(json.dumps({
        'paired_runtime_ready': len(exact_names),
        'exact_but_quarantined': [q['wiseman'] for q in quarantined_exact],
        'deferred': len(deferred_pairs),
        'absent_admitted': len(absent_admitted),
        'absent_quarantined': [r['guimaraes_name'] for r in absent_quarantined],
        'force_paired_23_N': force_paired,
        'F_EDL_N': force_edl, 'F_FDL_N': force_fdl,
        'sum_absent5_N': force_absent,
        'admitted_batch_total_30_N': force_admitted_total,
        'rel_residual': residual / force_admitted_total,
        'absent5_pcsa_share': pcsa_absent / pcsa_admitted,
        'top3_forces': top3,
        'predictions': {k: v['verdict'] for k, v in predictions.items()},
        'audit_rows': len(audit_rows),
        'store_records': store_record_count,
        'runtime_ready_count': sum(1 for m in annotated['muscles'] if m['force_runtime_ready']),
    }, indent=1))


if __name__ == '__main__':
    main()
