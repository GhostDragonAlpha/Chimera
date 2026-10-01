"""Admission adapter: extracted table cells -> architecture records.

The Guimaraes batch_muscle pattern (tools/science_funnel/adapters_muscle.py on
origin/agent/skeleton-movie-20260919) applied to tables-in-images:

  * one measurement record per (muscle, specimen, field), SI via
    tools/science_funnel/units.convert (g->kg, cm3->m3, mm->m, mm2->m2),
  * the dataset's own closure laws per row at 2%: density
    (mass = volume * 1060 kg/m3), PCSA (PCSA = m/(rho*FL)), MTU additivity
    (MTU = FL + tendon_ext + tendon_int); a violating (row, specimen) pair
    quarantines WHOLE and VISIBLY (one rejection per field, named code),
  * positivity / no-blanks, unknown muscle names refuse (the closed
    vocabulary stands in for the homology table; the real day pins the
    Vanhoof S1 name list the same way),
  * only EXTRACTED-CONFIDENT cells admit; EXTRACTED-LOW-CONFIDENCE and every
    REFUSED cell emit a rejection row carrying the read + confidence so the
    operator can hand-review -- never a guessed number,
  * provenance on every record: tiff sha256, sheet, row/col, cell bbox,
    per-cell conf_min/conf_mean, route tag,
  * count identity: fetched == admitted + rejected, zero silent drops.
"""
import sys
from pathlib import Path

_LANE = Path(__file__).resolve()
_ROOT = _LANE.parents[4]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from tools.science_funnel.common import Refusal, draft, number, require, text  # noqa: E402
from tools.science_funnel.units import convert  # noqa: E402

import synth_table  # noqa: E402

RHO_KG_M3 = 1060.0
LAW_TOLERANCE = 0.02
ROUTE = 'template-grid-ncc-v1'

# field -> (source unit, quantity, decimals)
FIELD_SPECS = {
    'mass_g': ('g', 'mass', 2),
    'volume_cm3': ('cm3', 'volume', 2),
    'fl_mm': ('mm', 'length', 1),
    'mtu_mm': ('mm', 'length', 1),
    'tendon_ext_mm': ('mm', 'length', 1),
    'tendon_int_mm': ('mm', 'length', 1),
    'pcsa_mm2': ('mm2', 'area', 2),
}
FIELD_LABEL = {
    'mass_g': 'muscle mass', 'volume_cm3': 'muscle volume',
    'fl_mm': 'fascicle length', 'mtu_mm': 'mtu length',
    'tendon_ext_mm': 'external tendon length',
    'tendon_int_mm': 'internal tendon length',
    'pcsa_mm2': 'physiological cross-sectional area',
}


def build_column_map(headers=None):
    """Column semantics for the battery layout (the real Vanhoof S1/S2 headers
    are declared the same way on the day -- RUNBOOK.md step 3)."""
    headers = headers or synth_table.headers()
    cmap = {'name_col': 0, 'specimen_columns': {}, 'summary_columns': {},
            'n_headers': len(headers)}
    for col, label in enumerate(headers):
        if col == 0:
            continue
        if label == 'mass mean±sd':
            cmap['summary_columns'][col] = 'mean_sd_mass_g'
            continue
        spec = label.split(' ')[0]
        for field, hdr_label, _, _ in synth_table.FIELDS:
            if label.endswith(hdr_label):
                cmap['specimen_columns'][col] = (spec, field)
                break
    require(len(cmap['specimen_columns'])
            == len(synth_table.SPECIMENS) * len(synth_table.FIELDS),
            'manifest_incomplete', str(len(cmap['specimen_columns'])))
    return cmap


def _reject(location, code, detail, provenance=None, weight=1):
    row = {'location': location,
           'refusal': {'code': code, 'detail': str(detail)},
           'weight': weight}
    if provenance:
        row['provenance'] = provenance
    return row


def resolve_key(name_cell, vocabulary):
    """Closed-vocabulary key resolution.  A read is matched against the
    vocabulary with spaces collapsed (fragmentation/loss of word spaces is
    a rendering artifact, not a different muscle) and with the recorded
    ambiguous-glyph alternates substituted (the l/I class of confusions is
    pixel-undecidable; only the vocabulary can decide).  Returns the
    vocabulary spelling of the key, or None."""
    text = (name_cell.get('text') or '').strip()
    if not text:
        return None

    def compact(s):
        return ''.join(s.split())

    if compact(text) in {compact(v) for v in vocabulary}:
        for v in vocabulary:
            if compact(v) == compact(text):
                return v
        return None
    alts = name_cell.get('alts') or []
    if not alts or len(alts) > 3:
        return None
    chars = list(text)
    positions = [p for p, _ in alts]
    options = [c for _, c in alts]
    found = None
    import itertools
    for combo in itertools.product(*options):
        trial = chars[:]
        for pos, ch in zip(positions, combo):
            if pos < len(trial):
                trial[pos] = ch
        variant = ''.join(trial)
        if compact(variant) in {compact(v) for v in vocabulary}:
            matches = [v for v in vocabulary
                       if compact(v) == compact(variant)]
            if len(matches) == 1:
                if found is not None and found != matches[0]:
                    return None
                found = matches[0]
    return found


def _close(parts, whole, what):
    require(whole > 0, 'nonpositive_value', f'{what}={whole}')
    return abs(parts - whole) / whole <= LAW_TOLERANCE


def admit(extraction, column_map, tiff_sha256, sheet_id, vocabulary,
          source_note='synthetic battery table (Vanhoof-class)'):
    """extraction: extract_table.extract(...) output.  Returns dict with
    records, rejections and the count identity."""
    cells_by_pos = {}
    for cell in extraction['cells']:
        cells_by_pos[(cell['row'], cell['col'])] = cell

    # the fetched datum is a VALUE cell (present ones only); the name cell
    # is the row key -- its refusal quarantines exactly the row's present
    # value cells
    manifest_value_cols = (list(column_map['specimen_columns'])
                           + list(column_map['summary_columns']))
    data_rows = sorted({r for (r, _) in cells_by_pos if r >= 1})
    fetched = 0
    records = []
    rejections = []
    ledger = set()          # (row, col) of every value cell with an outcome

    for row in data_rows:
        # the row key: the muscle name cell.  Keys go through the CLOSED
        # vocabulary (an error-correcting gate, not a guessed value): a read
        # of any confidence class that EXACTLY matches a vocabulary entry is
        # a usable key; anything else refuses and the whole row quarantines.
        name_cell = cells_by_pos.get((row, column_map['name_col']))
        present = [c for c in manifest_value_cols if (row, c) in cells_by_pos]
        fetched += len(present)
        row_weight = len(present)
        if name_cell is None:
            rejections.append(_reject(f'{sheet_id}:row{row}:name',
                                      'blank_cell', 'row key missing',
                                      weight=row_weight))
            ledger.update((row, c) for c in present)
            continue
        prov_name = {'tiff_sha256': tiff_sha256, 'sheet': sheet_id,
                     'row': row, 'col': column_map['name_col'],
                     'cell_bbox': name_cell['bbox'],
                     'conf_min': name_cell['conf_min'],
                     'conf_mean': name_cell['conf_mean'], 'route': ROUTE}
        muscle = resolve_key(name_cell, vocabulary)
        if muscle is None:
            rejections.append(_reject(
                f'{sheet_id}:row{row}:name',
                'unknown_muscle',
                f'key "{name_cell.get("text", "")}" (class '
                f'{name_cell["class"]}) not in the vocabulary/homology table',
                prov_name, weight=row_weight))
            ledger.update((row, c) for c in present)
            continue

        # per-specimen field cells: extraction refusals first
        spec_cells = {}
        for col, (spec, field) in column_map['specimen_columns'].items():
            cell = cells_by_pos.get((row, col))
            spec_cells.setdefault(spec, {})[field] = cell
            ledger.add((row, col))
            if cell is None:
                rejections.append(_reject(f'{sheet_id}:row{row}:{col}',
                                          'blank_cell', 'missing cell'))
            elif cell['class'] != 'CONFIDENT':
                rejections.append(_reject(
                    f'{sheet_id}:row{row}:{col}:{field}',
                    cell['code'] or 'low_confidence_extract',
                    f'read "{cell["text"]}" class {cell["class"]} '
                    f'conf_min {cell["conf_min"]:.3f} conf_mean {cell["conf_mean"]:.3f}',
                    {'tiff_sha256': tiff_sha256, 'sheet': sheet_id,
                     'row': row, 'col': col, 'cell_bbox': cell['bbox'],
                     'conf_min': cell['conf_min'],
                     'conf_mean': cell['conf_mean'], 'route': ROUTE}))
        # summary (mean±sd) column: recorded, not law-closed (declared)
        for col, field in column_map['summary_columns'].items():
            cell = cells_by_pos.get((row, col))
            ledger.add((row, col))
            if cell is None or cell['class'] != 'CONFIDENT' \
                    or muscle not in vocabulary:
                rejections.append(_reject(
                    f'{sheet_id}:row{row}:{col}:{field}',
                    (cell['code'] if cell else 'blank_cell')
                    or 'low_confidence_extract',
                    'summary cell not extraction-confident', weight=1))
                continue
            body, _, sd = cell['text'].partition('±')
            if not body or not sd:
                rejections.append(_reject(f'{sheet_id}:row{row}:{col}:{field}',
                                          'summary_malformed', cell['text']))
                continue
            payload = convert(float(body), 'g', 'mass')
            payload['uncertainty_si'] = number(float(sd)) / 1000.0
            payload.update(
                subject=f'Macaca mulatta/{muscle} (summary)',
                conditions={
                    'dataset': source_note, 'sheet': sheet_id,
                    'tiff_sha256': tiff_sha256, 'row': row,
                    'col': col, 'cell_bbox': cell['bbox'],
                    'extraction_class': 'EXTRACTED-CONFIDENT',
                    'conf_min': cell['conf_min'],
                    'conf_mean': cell['conf_mean'],
                    'route': ROUTE,
                    'statistic': 'mean ± sd across the seven specimens',
                },
                source_field=field, parameter='muscle mass (summary)')
            record = draft(f'vanhoof_prestage:{sheet_id}:{muscle}:summary:{field}',
                           'measurement', payload,
                           unknowns=['summary_statistic_not_per_specimen'],
                           label=f'{muscle} summary {field}')
            record['class_contract'] = {
                'class_id': 'batch.property.measurement', 'version': 1}
            records.append(record)


        # the row laws run per specimen -- but ONLY on specimens whose every
        # cell is CONFIDENT.  A specimen with an extraction-refused cell has
        # an untestable row identity: its CONFIDENT siblings refuse as
        # row_law_untestable (a value whose row closure cannot be verified
        # is never admitted), and the refused cells are already rejected
        # above -- nothing is counted twice.
        for spec, fields in spec_cells.items():
            if any(cell is None or cell['class'] != 'CONFIDENT'
                   for cell in fields.values()):
                for field, cell in fields.items():
                    if cell is not None and cell['class'] == 'CONFIDENT':
                        prov = {'tiff_sha256': tiff_sha256, 'sheet': sheet_id,
                                'row': row, 'col': cell['col'],
                                'cell_bbox': cell['bbox'],
                                'conf_min': cell['conf_min'],
                                'conf_mean': cell['conf_mean'],
                                'route': ROUTE}
                        rejections.append(_reject(
                            f'{sheet_id}:row{row}:{muscle}:{spec}:{field}',
                            'row_law_untestable',
                            'a sibling cell of this specimen refused '
                            'extraction; the row closure laws cannot be '
                            'verified', prov))
                continue
            parsed = {}
            law_rejections = []
            try:
                for field, cell in fields.items():
                    unit, quantity, _ = FIELD_SPECS[field]
                    value = number(cell['text'])
                    require(value > 0, 'nonpositive_value', f'{field}={value}')
                    parsed[field] = (value, cell)
                mass_g, _ = parsed['mass_g']
                vol_cm3, _ = parsed['volume_cm3']
                fl_mm, _ = parsed['fl_mm']
                pcsa_mm2, _ = parsed['pcsa_mm2']
                mtu_mm, _ = parsed['mtu_mm']
                te_mm, _ = parsed['tendon_ext_mm']
                ti_mm, _ = parsed['tendon_int_mm']
                mass_kg = mass_g / 1000.0
                fl_m = fl_mm / 1000.0
                vol_m3 = vol_cm3 * 1e-6
                pcsa_m2 = pcsa_mm2 * 1e-6
                mtu_m = mtu_mm / 1000.0
                require(_close(vol_m3 * RHO_KG_M3, mass_kg, 'mass_kg'),
                        'density_closure_violation',
                        f'volume*rho={vol_m3 * RHO_KG_M3:.6g} kg '
                        f'mass={mass_kg:.6g} kg')
                require(_close(mass_kg / (RHO_KG_M3 * fl_m), pcsa_m2, 'pcsa_m2'),
                        'pcsa_closure_violation',
                        f'm/(rho*FL)={mass_kg / (RHO_KG_M3 * fl_m):.6g} m2 '
                        f'pcsa={pcsa_m2:.6g} m2')
                require(_close(fl_mm + te_mm + ti_mm, mtu_mm, 'mtu_mm'),
                        'mtu_additivity_violation',
                        f'FL+ten={fl_mm + te_mm + ti_mm:.4g} mm '
                        f'mtu={mtu_mm:.4g} mm')
            except Refusal as exc:
                for field, cell in fields.items():
                    prov = None
                    if cell is not None:
                        prov = {'tiff_sha256': tiff_sha256, 'sheet': sheet_id,
                                'row': row, 'col': cell['col'],
                                'cell_bbox': cell['bbox'],
                                'conf_min': cell['conf_min'],
                                'conf_mean': cell['conf_mean'],
                                'route': ROUTE}
                    law_rejections.append(_reject(
                        f'{sheet_id}:row{row}:{muscle}:{spec}:{field}',
                        exc.code, exc.detail, prov))
            # the 7 rejection rows TOGETHER cover the specimen's 7 cells:
            # weight 1 each (the whole-row visibility is the named codes)
            rejections.extend(law_rejections)
            if law_rejections:
                continue

            # laws pass: emit the specimen's records
            for field, (value, cell) in parsed.items():
                unit, quantity, _ = FIELD_SPECS[field]
                payload = convert(value, unit, quantity)
                payload.update(
                    subject=f'Macaca mulatta/{muscle} ({spec})',
                    conditions={
                        'dataset': source_note,
                        'sheet': sheet_id,
                        'tiff_sha256': tiff_sha256,
                        'row': row,
                        'col': cell['col'],
                        'cell_bbox': cell['bbox'],
                        'extraction_class': 'EXTRACTED-CONFIDENT',
                        'conf_min': cell['conf_min'],
                        'conf_mean': cell['conf_mean'],
                        'route': ROUTE,
                        'specimen': spec,
                        'row_closure_laws': {
                            'density': 'mass = volume * 1060 kg/m3 @ 2%',
                            'pcsa': 'PCSA = m/(1060 kg/m3 * FL) @ 2%',
                            'mtu': 'MTU = FL + tendon_ext + tendon_int @ 2%'},
                    },
                    source_field=field,
                    parameter=FIELD_LABEL[field])
                record = draft(f'vanhoof_prestage:{sheet_id}:{muscle}:{spec}:{field}',
                               'measurement', payload,
                               unknowns=[
                                   'synthetic_battery_table_not_real_vanhoof_data',
                                   'extraction_provenance_is_the_tiff_cell_not_a_doi',
                               ],
                               label=f'{muscle} {spec} {field}')
                record['class_contract'] = {
                    'class_id': 'batch.property.measurement', 'version': 1}
                records.append(record)

    # leftover sweep: any extraction cell outside the manifest's columns
    # (extra intervals from noise/rotation) is counted, never dropped; any
    # MANIFEST cell the paths above failed to give an outcome is reported
    uncovered_manifest = []
    for (r, c), cell in cells_by_pos.items():
        if r < 1:
            continue
        if c in manifest_value_cols or c == column_map['name_col']:
            if (r, c) not in ledger and c in manifest_value_cols:
                uncovered_manifest.append((r, c))
                fetched += 1
                rejections.append(_reject(
                    f'{sheet_id}:row{r}:{c}', 'unaccounted_cell',
                    'no admission path produced an outcome for this cell',
                    weight=1))
        else:
            fetched += 1
            rejections.append(_reject(
                f'{sheet_id}:row{r}:{c}', 'interval_out_of_manifest',
                f'cell at col {c} outside the declared columns (structural)',
                weight=1))
    admitted = len(records)
    rejected_weight = sum(r.get('weight', 1) for r in rejections)
    return {'records': records, 'rejections': rejections,
            'count_identity': {
                'law': 'fetched == admitted + rejected(weighted), '
                       'zero silent drops',
                'fetched': fetched, 'admitted': admitted,
                'rejected_records': len(rejections),
                'rejected_weight': rejected_weight,
                'unaccounted_manifest_cells': uncovered_manifest,
                'closed': fetched == admitted + rejected_weight
                and not uncovered_manifest}}


ADAPTERS = {'vanhoof_prestage_tables': admit}
