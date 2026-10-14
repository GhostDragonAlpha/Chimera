"""Pennation-correct the Guimaraes pairing's 23 force records.

Rule-0 lane (receipt.json in this directory, preregistered BEFORE this builder
existed). The sigma lane (agent/sigma-law-20260921 at beb6b106) measured that the
pinned sheet's PCSA_m2 column is the pennation-UNCORRECTED area m/(rho*FL)
(decisive bucket: 18 muscles with pennation > 11.48 deg where the conventions
differ > 2%: 17 match uncorrected, 0 match corrected), so the pairing's
F = sigma * PCSA overestimates pennate muscles by 1/cos(pennation) - up to
16.06% at VM's 30.5 deg. This builder applies the measured per-muscle correction

    F_corrected = sigma_ASSUMED * PCSA_m2 * 1e4 * cos(radians(pennation_deg))

to EXACTLY the 23 muscles whose before-record status is paired_exact_admitted,
re-reading PCSA and pennation fresh from the same sha-pinned xlsx bytes the
pairing read (the pairing lane's own reader is imported, not reimplemented).
sigma = 30.0 N/cm^2 == 0.30 MPa is EXPLICITLY ASSUMED on every record (the sigma
lane's verdict: RETAINED AS ASSUMED, NOT RETIRED BY MEASUREMENT).

Emits (all inside THIS directory; nothing else in the repo is touched):

  macaque_assembly_force_annotated_pennation_corrected.json
        the pairing's annotated assembly with the 23 force records amended;
        the UNCORRECTED value is retained on every record as
        max_isometric_force_N_uncorrected - nothing is hidden.
  amendment_table.json
        per-muscle before/after: pennation angle, factor, delta_N, delta_pct,
        the re-closed batch total vs the pairing's 2389.4823 N, top-3 named.
  audit_table.json
        every emitted data number traced muscle -> sheet row -> cell -> raw text
        -> member sha256; the correction factor traced to the measured
        avg_penn_deg; a completeness scan (falsifier F3).

The pairing's own artifacts are NEVER written: the output is a NEW annotation
file alongside the original; the integrator chooses. Deterministic by
construction (no timestamps, fixed key order, CPython float repr); re-running
must produce byte-identical outputs (falsifier F4).
"""
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]

# --- the pairing lane's lawful reader, imported so there is ONE reader ---------
PAIRING_DIR = ROOT / 'tools/science_funnel/validation/guimaraes_pairing_20260921'
sys.path.insert(0, str(PAIRING_DIR))
import build_force_annotation as pairing  # noqa: E402

BASE_COMMIT = '2098797b82011b6f334d57ad389a71c807150d79'
SIGMA_COMMIT = 'beb6b1062874d140a6a29a58282ea337fc226213'
SIGMA_RECEIPT_PATH = 'tools/science_funnel/validation/sigma_law_20260921/receipt.json'
SIGMA_AUDIT_CSV_PATH = 'tools/science_funnel/validation/sigma_law_20260921/audit_table.csv'

BEFORE_PATH = PAIRING_DIR / 'macaque_assembly_force_annotated.json'
BEFORE_AUDIT_PATH = PAIRING_DIR / 'audit_table.json'
BEFORE_SHA256 = 'd7791b4d1db7d0a49d4ff99c76d36a3d9fa02a77723ac694d9d7741acbd1a27f'
BEFORE_AUDIT_SHA256 = '843d1e70a5a881819360e05cef961eee89108ec86e6cb82ff2dbf475a0979d88'
MUSCLES_PY_SHA256 = 'e807d7f5533dcae06c338f6f053655ac0212073bac08f1d6e150e0808f51488a'

LANE = 'agent/pennation-correction-20260921'
SIGMA_STATUS = ('ASSUMED: 30.0 N/cm^2 == 0.30 MPa retained, NOT retired by measurement '
                '(sigma_law_20260921: the batch carries no Fmax, sigma_implied is not '
                'computable; 0.3 MPa stays the assumed point in the 23-32 N/cm^2 band)')
CORRECTION_LAW = ('F_corrected_N = sigma_ASSUMED_N_PER_CM2 * PCSA_m2 * 1e4 '
                  '* cos(radians(pennation_deg)); sheet PCSA measured pennation-'
                  'UNCORRECTED by sigma_law_20260921 (decisive bucket 17-0)')
EXPECTED_PAIRED = 23
DATA_FIELDS = frozenset((
    'fl_m', 'pcsa_m2', 'musc_mass_kg', 'belly_mass_kg', 'tendon_mass_kg',
    'penn_deg', 'pennation_angle_at_optimal_rad', 'optimal_fiber_length_m',
    'pennation_correction_factor', 'overestimate_if_uncorrected_pct',
    'max_isometric_force_N', 'max_isometric_force_N_uncorrected',
    'pennation_delta_N', 'pennation_delta_pct',
))


def refuse(code, detail):
    raise SystemExit(f'REFUSAL {code}: {detail}')


def pin(name, condition, detail):
    if not condition:
        refuse(name, detail)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def rel_dev(measured, predicted):
    return abs(measured - predicted) / max(abs(predicted), 1e-300)


# ------------------------------------------------------------------ preregistration

def load_preregistration():
    path = HERE / 'receipt.json'
    pin('rule0', path.exists(), 'the Rule-0 receipt must exist before the builder runs')
    receipt = json.loads(path.read_text(encoding='utf-8'))
    pre = receipt.get('pre_registration', {})
    for key in ('P1_before_reproduction', 'P2_corrected_sum_23_N', 'P3_total_shift_N',
                'P4_top3_by_absolute_delta_N', 'P5_top3_by_pct_correction',
                'P6_uncorrected_by_absence'):
        pin('rule0', key in pre, f'receipt pre_registration missing {key}')
    pin('rule0', receipt.get('written_before_build') is True,
        'receipt is not marked written_before_build')
    return pre


# ------------------------------------------------------------------ audit

def audit_row(muscle, guim, field, kind, value, row, raw_field, extra=None):
    entry = {
        'muscle': muscle,
        'guimaraes': guim,
        'field': field,
        'kind': kind,
        'value': value,
        'sheet_row': row['sheet_row'],
        'raw_cell': row['cells'].get(raw_field),
        'raw_text': row['raws'].get(raw_field),
        'member_sha256': pairing.XLSX_PIN_SHA256,
        'source_ref': pairing.CARRIER_REF,
        'source_commit': pairing.CARRIER_COMMIT,
        'source_path': pairing.XLSX_PATH,
    }
    if extra:
        entry.update(extra)
    return entry


def correction_rows(muscle, guim, row, factor, f_before, f_after, penn):
    """Audit rows for the correction chain of one muscle."""
    sigma_extra = {'sigma_status': SIGMA_STATUS}
    rows = [
        audit_row(muscle, guim, 'max_isometric_force_N_uncorrected',
                  'derived_before_amendment_retained', f_before, row, 'pcsa_m2',
                  {'law': 'F = 30.0 N/cm^2 * PCSA_m2 * 1e4 (the pairing\'s uncorrected '
                          'law); value RETAINED as a named field, nothing hidden',
                   **sigma_extra}),
        audit_row(muscle, guim, 'pennation_correction_factor', 'derived_correction',
                  factor, row, 'penn_deg',
                  {'law': ('cos(radians(avg_penn_deg)) with avg_penn_deg = '
                           f'{penn!r} deg from this sheet row') if penn is not None else
                          ('1.0 - no measured pennation in this sheet row; treat-as-0 '
                           'DECLARED (the pairing\'s convention), NOT a measured '
                           'parallel fiber'),
                   **sigma_extra}),
        audit_row(muscle, guim, 'max_isometric_force_N', 'derived_pennation_corrected',
                  f_after, row, 'pcsa_m2',
                  {'law': CORRECTION_LAW + f' with pennation_deg = {penn!r}',
                   'factor': factor, 'status': 'amended_by_' + LANE, **sigma_extra}),
        audit_row(muscle, guim, 'pennation_delta_N', 'derived_amendment',
                  f_after - f_before, row, 'pcsa_m2',
                  {'law': 'F_corrected - F_uncorrected', **sigma_extra}),
        audit_row(muscle, guim, 'pennation_delta_pct', 'derived_amendment',
                  (factor - 1.0) * 100.0, row, 'penn_deg',
                  {'law': '(factor - 1) * 100; negative = force reduced',
                   **sigma_extra}),
    ]
    if penn is not None:
        rows.append(audit_row(muscle, guim, 'overestimate_if_uncorrected_pct',
                              'derived_correction', (1.0 / factor - 1.0) * 100.0,
                              row, 'penn_deg',
                              {'law': '(1/cos(pennation) - 1) * 100; the sigma lane\'s '
                                      'overestimate framing', **sigma_extra}))
    return rows


# ------------------------------------------------------------------ main

def main():
    pre = load_preregistration()

    # ---- F1 pins -------------------------------------------------------------
    lines = (ROOT / 'LightEngine/kinematic/muscles.py').read_text(encoding='utf-8').splitlines()
    datum = [(i + 1, l.strip()) for i, l in enumerate(lines)
             if l.startswith('SPECIFIC_TENSION_N_PER_CM2')]
    pin('F1_datum', sha256((ROOT / 'LightEngine/kinematic/muscles.py').read_bytes())
        == MUSCLES_PY_SHA256 and datum == [(79, 'SPECIFIC_TENSION_N_PER_CM2 = 30.0')],
        f'muscles.py drifted: sha/line {datum}')
    pin('F1_before', sha256(BEFORE_PATH.read_bytes()) == BEFORE_SHA256,
        'the pairing\'s annotated assembly drifted from its committed sha')
    pin('F1_before_audit', sha256(BEFORE_AUDIT_PATH.read_bytes()) == BEFORE_AUDIT_SHA256,
        'the pairing\'s audit table drifted from its committed sha')
    sigma_receipt_bytes = pairing.git_show(f'{SIGMA_COMMIT}:{SIGMA_RECEIPT_PATH}')
    sigma_csv_bytes = pairing.git_show(f'{SIGMA_COMMIT}:{SIGMA_AUDIT_CSV_PATH}')
    pin('F1_sigma', json.loads(sigma_receipt_bytes)['schema'] == 'chimera.rule0.receipt.v1'
        and len(sigma_csv_bytes) > 0, 'sigma lane artifacts unreachable at ' + SIGMA_COMMIT)

    # ---- fresh byte-read of the same pinned sheet ----------------------------
    batch, batch_meta = pairing.read_batch()
    pin('F1_xlsx', batch_meta['sha256'] == pairing.XLSX_PIN_SHA256
        and batch_meta['bytes'] == pairing.XLSX_PIN_BYTES, 'xlsx pin drift')

    before = json.loads(BEFORE_PATH.read_text(encoding='utf-8'))
    arith = before['force_pairing_status']['arithmetic']

    # ---- P1: the before-state must reproduce from the bytes, bit-exactly ------
    p1_drift = []
    corrected, f_before_by_guim, f_after_by_guim = {}, {}, {}
    audit_rows = []
    n_measured_penn = 0
    for m in before['muscles']:
        fp = m['force_pairing']
        if fp.get('status') != 'paired_exact_admitted':
            continue
        guim = fp['guimaraes_name']
        row = batch.get(guim)
        pin('F2_row', row is not None and row['admitted'],
            f'{guim}: paired muscle has no admitted sheet row at the pinned bytes')
        numbers_before = fp['numbers']
        fresh = pairing.guimaraes_numbers(row)
        if numbers_before != fresh:
            diff = sorted(k for k in set(numbers_before) | set(fresh)
                          if numbers_before.get(k) != fresh.get(k))
            p1_drift.append({'wiseman': m['name'], 'guimaraes': guim, 'fields': diff})
        f_before = fresh['max_isometric_force_N']
        pcsa = fresh['pcsa_m2']
        penn = fresh['penn_deg']
        pin('F2_force_law', f_before == pairing.force_n(pcsa),
            f'{guim}: before force != 30.0*PCSA*1e4 exactly')
        factor = 1.0 if penn is None else math.cos(math.radians(penn))
        f_after = f_before * factor
        pin('F6_mult', f_after == f_before * factor,
            f'{guim}: corrected force is not the exact IEEE product')
        if penn is not None:
            n_measured_penn += 1
        corrected[m['name']] = {
            'guimaraes': guim, 'row': row, 'fresh': fresh, 'factor': factor,
            'f_before': f_before, 'f_after': f_after, 'penn': penn,
        }
        f_before_by_guim[guim] = f_before
        f_after_by_guim[guim] = f_after

    pin('F2_count', len(corrected) == EXPECTED_PAIRED,
        f'{len(corrected)} paired_exact_admitted records, expected {EXPECTED_PAIRED}')
    pin('P1_before_reproduction', not p1_drift,
        f'before-artifact does not reproduce from bytes: {p1_drift}')
    p1_verdict = 'PASS' if not p1_drift else 'FALSIFIED'

    # ---- P6 counts ------------------------------------------------------------
    absent_penn = sorted(c['guimaraes'] for c in corrected.values() if c['penn'] is None)
    p6_expected = pre['P6_uncorrected_by_absence']
    p6_verdict = ('PASS' if n_measured_penn == 19 and absent_penn == ['AM', 'GRA', 'PB', 'PL']
                  else 'FALSIFIED')

    # ---- apply the amendment to the annotation copy ---------------------------
    for m in before['muscles']:
        fp = m['force_pairing']
        if fp.get('status') != 'paired_exact_admitted':
            continue
        c = corrected[m['name']]
        fresh, factor = c['fresh'], c['factor']
        f_before, f_after, penn = c['f_before'], c['f_after'], c['penn']
        numbers = dict(fresh)
        numbers['max_isometric_force_N_uncorrected'] = f_before
        numbers['max_isometric_force_N'] = f_after
        numbers['pennation_correction_factor'] = factor
        numbers['overestimate_if_uncorrected_pct'] = (
            None if penn is None else (1.0 / factor - 1.0) * 100.0)
        numbers['pennation_correction'] = {
            'sigma_status': SIGMA_STATUS,
            'law': CORRECTION_LAW,
            'pennation_deg': penn,
            'factor': factor,
            'source': ('measured sheet avg_penn_deg, same pinned row as the pairing read'
                       if penn is not None else
                       'absent_at_source_treat_as_0_declared: this row carries no measured '
                       'pennation; factor exactly 1.0; UNCORRECTED BY ABSENCE, never a '
                       'measured parallel fiber'),
        }
        fp['numbers'] = numbers
        fp['note'] = fp['note'] + ' AMENDED by ' + LANE + (': max_isometric_force_N now '
                      'carries the measured pennation correction (sheet PCSA is '
                      'pennation-uncorrected per sigma_law_20260921); the uncorrected '
                      'value is retained as max_isometric_force_N_uncorrected; sigma '
                      'stays explicitly ASSUMED.')
        m['reason'] = m['reason'] + (' PENNATION AMENDMENT (' + LANE + '): F = '
                      'sigma_ASSUMED (30.0 N/cm^2 = 0.30 MPa, retained-not-retired per '
                      'sigma_law_20260921) * PCSA_m2 * 1e4 * cos(pennation); the '
                      'uncorrected value is retained on the record.')

    # ---- audit rows for all 23 -------------------------------------------------
    for wname in sorted(corrected):
        c = corrected[wname]
        guim, row, fresh = c['guimaraes'], c['row'], c['fresh']
        base = [
            audit_row(wname, guim, 'fl_m', 'measured', fresh['fl_m'], row, 'fl_m'),
            audit_row(wname, guim, 'pcsa_m2', 'measured', fresh['pcsa_m2'], row, 'pcsa_m2'),
            audit_row(wname, guim, 'musc_mass_kg', 'converted', fresh['musc_mass_kg'],
                      row, 'musc_mass', {'conversion': 'g -> kg (/1000, units.convert)'}),
            audit_row(wname, guim, 'belly_mass_kg', 'converted', fresh['belly_mass_kg'],
                      row, 'belly_mass', {'conversion': 'g -> kg (/1000, units.convert)'}),
            audit_row(wname, guim, 'tendon_mass_kg', 'converted', fresh['tendon_mass_kg'],
                      row, 'tendon_mass', {'conversion': 'g -> kg (/1000, units.convert)'}),
            audit_row(wname, guim, 'optimal_fiber_length_m', 'mapped',
                      fresh['optimal_fiber_length_m'], row, 'fl_m',
                      {'law': 'resting fascicle length -> Millard optimal_fiber_length'}),
        ]
        if fresh['penn_deg'] is not None:
            base.append(audit_row(wname, guim, 'penn_deg', 'measured', fresh['penn_deg'],
                                  row, 'penn_deg'))
            base.append(audit_row(wname, guim, 'pennation_angle_at_optimal_rad', 'converted',
                                  fresh['pennation_angle_at_optimal_rad'], row, 'penn_deg',
                                  {'conversion': 'deg -> rad (units.convert)'}))
        audit_rows.extend(base)
        audit_rows.extend(correction_rows(wname, guim, row, c['factor'], c['f_before'],
                                          c['f_after'], c['penn']))

    # ---- closure arithmetic (F6) ----------------------------------------------
    sum23_before = math.fsum(f_before_by_guim.values())
    pin('F6_before_sum', sum23_before == arith['sum_23_paired'],
        f'sum of before forces {sum23_before!r} != pairing\'s {arith["sum_23_paired"]!r}')
    sum23_after = math.fsum(f_after_by_guim.values())
    carried = {
        'F_EDL_whole': arith['F_EDL_whole'],
        'F_FDL_whole': arith['F_FDL_whole'],
        'sum_5_absent_admitted': arith['sum_5_absent_admitted'],
    }
    batch_total_after = math.fsum([sum23_after, carried['F_EDL_whole'],
                                   carried['F_FDL_whole'], carried['sum_5_absent_admitted']])
    batch_total_before = arith['sum_30_admitted_batch_total']
    shift = sum23_after - sum23_before

    before['force_pairing_status']['arithmetic']['pennation_amendment'] = {
        'lane': LANE,
        'law': CORRECTION_LAW,
        'sigma_status': SIGMA_STATUS,
        'scope': 'exactly the 23 paired_exact_admitted records; the deferred EDL/FDL '
                 'whole-muscle numbers and the 5 admitted absent-muscle numbers are '
                 'carried UNCORRECTED into this closure (out of scope, named)',
        'sum_23_paired_corrected_N': sum23_after,
        'batch_total_corrected_N': batch_total_after,
        'batch_total_before_N': batch_total_before,
        'shift_N': shift,
        'shift_pct_of_sum23': shift / sum23_before * 100.0,
        'carried_unchanged_terms_N': carried,
        'identity': 'sum_23_paired_corrected + F_EDL_whole + F_FDL_whole + '
                    'sum_5_absent_admitted == batch_total_corrected (the three non-paired '
                    'terms are the pairing\'s values, unchanged)',
    }

    # ---- amendment table -------------------------------------------------------
    per_muscle = []
    for wname in sorted(corrected):
        c = corrected[wname]
        guim, row, fresh = c['guimaraes'], c['row'], c['fresh']
        factor, f_before, f_after, penn = c['factor'], c['f_before'], c['f_after'], c['penn']
        per_muscle.append({
            'wiseman_muscle': wname,
            'guimaraes_name': guim,
            'sheet_row': row['sheet_row'],
            'penn_cell': row['cells'].get('penn_deg'),
            'penn_deg': penn,
            'pcsa_m2': fresh['pcsa_m2'],
            'pennation_correction_factor': factor,
            'correction_status': ('corrected_measured_pennation' if penn is not None else
                                  'uncorrected_by_absence_treat_as_0_declared'),
            'max_isometric_force_N_uncorrected': f_before,
            'max_isometric_force_N': f_after,
            'pennation_delta_N': f_after - f_before,
            'pennation_delta_pct': (factor - 1.0) * 100.0,
            'overestimate_if_uncorrected_pct': (
                None if penn is None else (1.0 / factor - 1.0) * 100.0),
            'member_sha256': pairing.XLSX_PIN_SHA256,
        })
    measured_rows = [r for r in per_muscle if r['penn_deg'] is not None]
    top3_abs = sorted(per_muscle, key=lambda r: -abs(r['pennation_delta_N']))[:3]
    top3_pct = sorted(measured_rows, key=lambda r: -abs(r['pennation_delta_pct']))[:3]

    # ---- P2/P3/P4/P5 measured vs frozen pre-registration -----------------------
    p2_pred = pre['P2_corrected_sum_23_N']['value']
    p2_verdict = 'PASS' if rel_dev(sum23_after, p2_pred) <= 1e-12 else 'FALSIFIED'
    p3_pred = pre['P3_total_shift_N']
    p3_checks = {
        'shift_N': (shift, p3_pred['shift']),
        'batch_total_after_N': (batch_total_after, p3_pred['batch_total_after_N']),
        'batch_total_before_N': (batch_total_before, p3_pred['batch_total_before_N']),
    }
    p3_devs = {k: rel_dev(v, p) for k, (v, p) in p3_checks.items()}
    p3_verdict = 'PASS' if max(p3_devs.values()) <= 1e-12 else 'FALSIFIED'

    def names3(pred_key):
        return [e['muscle'] for e in pre[pred_key]]

    p4_measured = [{'muscle': r['guimaraes_name'], 'delta_N': r['pennation_delta_N']}
                   for r in top3_abs]
    p4_verdict = ('PASS' if names3('P4_top3_by_absolute_delta_N')
                  == [r['guimaraes_name'] for r in top3_abs] else 'FALSIFIED')
    p5_measured = [{'muscle': r['guimaraes_name'], 'penn_deg': r['penn_deg'],
                    'force_drop_pct': r['pennation_delta_pct']} for r in top3_pct]
    p5_verdict = ('PASS' if names3('P5_top3_by_pct_correction')
                  == [r['guimaraes_name'] for r in top3_pct] else 'FALSIFIED')
    p1_expected_names = ['AL', 'AM', 'BFL', 'EHL', 'FHL', 'GMax', 'GMed', 'GMin', 'GRA',
                         'ILI', 'LG', 'MG', 'PB', 'PECT', 'PIRI', 'PL', 'SM', 'SOL', 'ST',
                         'TA', 'VI', 'VL', 'VM']
    p1_set_ok = sorted(f_before_by_guim) == p1_expected_names
    p1_verdict = 'PASS' if (p1_verdict == 'PASS' and p1_set_ok) else 'FALSIFIED'

    # ---- completeness scan (F3): every emitted data number has an audit row ----
    emitted = set()
    for m in before['muscles']:
        fp = m['force_pairing']
        if fp.get('status') != 'paired_exact_admitted':
            continue
        numbers = fp['numbers']
        for f in DATA_FIELDS:
            v = numbers.get(f)
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                emitted.add((f, v))
            elif f == 'overestimate_if_uncorrected_pct' and v is None:
                pass  # absence is declared, not a number
    amendment_numbers = set()
    for r in per_muscle:
        for f in DATA_FIELDS:
            v = r.get(f)
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                amendment_numbers.add((f, v))
    audited = {(r['field'], r['value']) for r in audit_rows}
    unprovenanced = sorted(f'{f}={v!r}' for f, v in (emitted | amendment_numbers) - audited)
    pin('F3', not unprovenanced, f'emitted data numbers without audit rows: {unprovenanced[:5]}')
    orphan_audits = sorted(f'{f}={v!r}' for f, v in audited - emitted - amendment_numbers)
    pin('F3', not orphan_audits, f'audit rows without emitted numbers: {orphan_audits[:5]}')
    completeness = {
        'data_fields_scanned': sorted(DATA_FIELDS),
        'emitted_data_numbers': len(emitted | amendment_numbers),
        'audit_rows': len(audit_rows),
        'unprovenanced': 0,
        'orphan_audit_rows': 0,
        'scope_note': 'aggregate sums (arithmetic sections) are bookkeeping over audited '
                      'per-muscle numbers and are excluded from the scan, exactly as in '
                      'the pairing lane\'s own completeness scan',
        'verdict': 'PASS',
    }

    # ---- write the amended annotation ------------------------------------------
    before['force_annotation']['pennation_amendment'] = {
        'lane': LANE,
        'builder': 'tools/science_funnel/validation/pennation_correction_20260921/'
                   'build_pennation_correction.py',
        'base_commit': BASE_COMMIT,
        'before_artifact': {
            'path': 'tools/science_funnel/validation/guimaraes_pairing_20260921/'
                    'macaque_assembly_force_annotated.json',
            'sha256': BEFORE_SHA256,
        },
        'correction_source': {
            'finding': 'sigma_law_20260921: the sheet PCSA_m2 column is the '
                       'pennation-UNCORRECTED area m/(rho*FL) (decisive bucket, 18 rows '
                       'with pennation > 11.48 deg: 17 match uncorrected, 0 corrected)',
            'ref': SIGMA_COMMIT,
            'sigma_status': SIGMA_STATUS,
        },
        'law': CORRECTION_LAW,
        'scope': 'the 23 paired_exact_admitted records; EDL/FDL and the 5 admitted '
                 'absent-muscle numbers are carried UNCORRECTED (named, not hidden)',
        'output_kind': 'NEW annotation file alongside the pairing\'s; the original '
                       'artifacts are unchanged; the integrator chooses',
    }
    before['force_pairing_status']['declared_gaps'] = before[
        'force_pairing_status']['declared_gaps'] + [
        'PENNATION AMENDMENT (' + LANE + '): the sheet\'s PCSA is pennation-uncorrected '
        '(sigma_law_20260921, decisive bucket 17-0), so this annotation\'s 23 paired '
        'forces carry the measured cos(pennation) correction; max_isometric_force_N '
        'values are the corrected ones and max_isometric_force_N_uncorrected retains '
        'the pairing\'s values; AM, GRA, PB, PL have no measured pennation and are '
        'UNCORRECTED BY ABSENCE (factor 1.0, treat-as-0 declared); the corrected 23-pair '
        f'sum is {sum23_after!r} N (shift {shift!r} N) and the re-closed batch total is '
        f'{batch_total_after!r} N vs the pairing\'s {batch_total_before!r} N; EDL, FDL '
        'and the 5 admitted absent-muscle numbers are carried UNCORRECTED (out of scope, '
        'named)',
        'PENNATION AMENDMENT inter-lane observation, not adjudicated here: '
        'sigma_law_20260921\'s audit_table.csv names PB a pcsa-closure contradiction '
        '(dev 2.013e-02 vs the 2% cut) while the admitting store at ' +
        pairing.CARRIER_COMMIT + ' and the pairing lane admitted PB (30 admitted rows); '
        'this lane keeps the pairing\'s before-state as-is (PB paired) and applies no '
        'quarantine of its own; PB has no measured pennation and carries factor 1.0 '
        'either way',
    ]
    before['unknowns'] = before['unknowns'] + [
        'PENNATION AMENDMENT (' + LANE + '): resolved - the 23 paired max_isometric_force '
        'values now carry the measured pennation correction demanded by '
        'sigma_law_20260921 (sheet PCSA is pennation-uncorrected); sigma remains the '
        'ASSUMED 30.0 N/cm^2 = 0.30 MPa datum (retained, not retired); uncorrected '
        'values are retained on every record; the pairing\'s original artifacts are '
        'unchanged alongside this file and the integrator chooses which to admit',
    ]

    # ---- assemble audit doc ------------------------------------------------------
    audit_doc = {
        'schema': 'chimera.pennation_correction_audit.v1',
        'lane': LANE,
        'base_commit': BASE_COMMIT,
        'inputs': {
            'before_annotation': {
                'path': 'tools/science_funnel/validation/guimaraes_pairing_20260921/'
                        'macaque_assembly_force_annotated.json',
                'sha256': BEFORE_SHA256},
            'before_audit_table': {
                'path': 'tools/science_funnel/validation/guimaraes_pairing_20260921/'
                        'audit_table.json',
                'sha256': BEFORE_AUDIT_SHA256},
            'sigma_lane_commit': SIGMA_COMMIT,
            'sigma_receipt_sha256': sha256(sigma_receipt_bytes),
            'sigma_audit_csv_sha256': sha256(sigma_csv_bytes),
            'xlsx': {'path': pairing.XLSX_PATH, 'sha256': batch_meta['sha256'],
                     'bytes': batch_meta['bytes']},
            'muscles_py': {'path': 'LightEngine/kinematic/muscles.py',
                           'sha256': MUSCLES_PY_SHA256, 'datum_line': 79},
        },
        'laws': {
            'corrected_force': CORRECTION_LAW,
            'sigma': SIGMA_STATUS,
            'pennation_source': 'sheet avg_penn_deg of the same Macaca mulatta row the '
                                'pairing read; deg -> rad via math.radians',
            'no_pennation_rows': 'factor exactly 1.0, treat-as-0 DECLARED, listed '
                                 'uncorrected_by_absence',
            'scope': '23 paired_exact_admitted records only; EDL/FDL/absent carried '
                     'uncorrected and named',
            'reader': 'tools/science_funnel/validation/guimaraes_pairing_20260921/'
                      'build_force_annotation.py imported (ONE reader, no drift)',
        },
        'predictions_measured': {
            'P1_before_reproduction': {'verdict': p1_verdict,
                                       'drifts': p1_drift,
                                       'paired_set_matches': p1_set_ok},
            'P2_corrected_sum_23_N': {'predicted': p2_pred, 'measured': sum23_after,
                                      'rel_dev': rel_dev(sum23_after, p2_pred),
                                      'verdict': p2_verdict},
            'P3_total_shift_N': {'predicted': p3_pred,
                                 'measured': {'shift_N': shift,
                                              'batch_total_after_N': batch_total_after,
                                              'batch_total_before_N': batch_total_before},
                                 'rel_dev': p3_devs, 'verdict': p3_verdict},
            'P4_top3_by_absolute_delta_N': {'predicted': names3('P4_top3_by_absolute_delta_N'),
                                            'measured': p4_measured,
                                            'verdict': p4_verdict},
            'P5_top3_by_pct_correction': {'predicted': names3('P5_top3_by_pct_correction'),
                                          'measured': p5_measured,
                                          'verdict': p5_verdict},
            'P6_uncorrected_by_absence': {'predicted': p6_expected,
                                          'measured': {'measured_pennation_count':
                                                       n_measured_penn,
                                                       'absent': absent_penn},
                                          'verdict': p6_verdict},
        },
        'completeness_scan': completeness,
        'closure': before['force_pairing_status']['arithmetic']['pennation_amendment'],
        'rows': audit_rows,
    }

    amendment_doc = {
        'schema': 'chimera.pennation_amendment.v1',
        'lane': LANE,
        'base_commit': BASE_COMMIT,
        'law': CORRECTION_LAW,
        'sigma_status': SIGMA_STATUS,
        'before': {
            'artifact': 'tools/science_funnel/validation/guimaraes_pairing_20260921/'
                        'macaque_assembly_force_annotated.json',
            'artifact_sha256': BEFORE_SHA256,
            'sum_23_paired_N': sum23_before,
            'batch_total_N': batch_total_before,
        },
        'after': {
            'artifact': 'tools/science_funnel/validation/pennation_correction_20260921/'
                        'macaque_assembly_force_annotated_pennation_corrected.json',
            'sum_23_paired_corrected_N': sum23_after,
            'batch_total_corrected_N': batch_total_after,
            'shift_N': shift,
            'shift_pct_of_sum23': shift / sum23_before * 100.0,
        },
        'carried_unchanged_terms_N': carried,
        'carried_unchanged_note': 'the deferred EDL/FDL whole-muscle numbers and the 5 '
                                  'admitted Guimaraes-only numbers enter the closure '
                                  'UNCORRECTED: correcting them is out of this lane\'s '
                                  'scope (named here, not hidden)',
        'integrator_note': 'the corrected annotation is a NEW file alongside the '
                           'pairing\'s originals; the originals are byte-unchanged; the '
                           'integrator chooses which to admit',
        'top3_by_absolute_delta': [
            {'muscle': r['guimaraes_name'], 'wiseman_muscle': r['wiseman_muscle'],
             'penn_deg': r['penn_deg'], 'factor': r['pennation_correction_factor'],
             'delta_N': r['pennation_delta_N']} for r in top3_abs],
        'top3_by_pct': [
            {'muscle': r['guimaraes_name'], 'wiseman_muscle': r['wiseman_muscle'],
             'penn_deg': r['penn_deg'], 'force_drop_pct': r['pennation_delta_pct'],
             'overestimate_if_uncorrected_pct': r['overestimate_if_uncorrected_pct']}
            for r in top3_pct],
        'inter_lane_observation': 'sigma_law_20260921\'s audit_table.csv names PB a '
                                  'pcsa-closure contradiction (dev 2.013e-02 vs the 2% '
                                  'cut) while the admitting store and the pairing '
                                  'admitted PB; not adjudicated here - the pairing\'s '
                                  'before-state stands and PB carries factor 1.0 (no '
                                  'measured pennation) either way',
        'per_muscle': per_muscle,
        'completeness_scan': completeness,
    }

    for name, doc in (('macaque_assembly_force_annotated_pennation_corrected.json', before),
                      ('amendment_table.json', amendment_doc),
                      ('audit_table.json', audit_doc)):
        (HERE / name).write_text(json.dumps(doc, indent=1, sort_keys=True) + '\n',
                                 encoding='utf-8')

    print(json.dumps({
        'paired_amended': len(corrected),
        'measured_pennation': n_measured_penn,
        'uncorrected_by_absence': absent_penn,
        'sum23_before_N': sum23_before,
        'sum23_corrected_N': sum23_after,
        'shift_N': shift,
        'batch_total_before_N': batch_total_before,
        'batch_total_corrected_N': batch_total_after,
        'carried_unchanged_N': carried,
        'top3_abs': [r['guimaraes_name'] for r in top3_abs],
        'top3_pct': [r['guimaraes_name'] for r in top3_pct],
        'predictions': {k: v['verdict'] for k, v in audit_doc['predictions_measured'].items()},
        'audit_rows': len(audit_rows),
        'artifact_sha256': {
            name: sha256((HERE / name).read_bytes())
            for name in ('macaque_assembly_force_annotated_pennation_corrected.json',
                         'amendment_table.json', 'audit_table.json')},
    }, indent=1))


if __name__ == '__main__':
    main()
