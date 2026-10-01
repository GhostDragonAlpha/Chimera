"""Appearance-lane funnels (INTAKE-APPEARANCE, 2026-09-18).

Three adapters, one lane:
  goldenberg_rows      -- Goldenberg et al. color+NIR reflectance replication
                          data (Zenodo 15084543, CC BY 4.0): 441 taxon rows x
                          8 summary reflectance cells -> one observation entity
                          per row plus one measurement per measured cell.
  phylacine_species    -- PHYLACINE 1.2.1 trait table (CC0, GitHub release):
                          5,831 mammal rows -> one species entity per row with
                          mass, diet, habitat, island endemicity, IUCN status.
  splib07_chapter_spectra -- USGS Spectral Library v7 ASCII channel (CC0,
                          ScienceBase): Chapter-V Vegetation + Chapter-S Soils
                          and Mixtures spectra of the pinned splib07a zip ->
                          one series record per spectrum (wavelengths paired
                          from the zip's own Wavelengths files), plus one
                          deferred identity record for the 5.1 GB full bundle.

Lane adapters merge into the shared ADAPTERS dict via the adapters_* auto-load
(APPEARANCE_ADAPTERS below); the shared module is never edited by a lane.

RULE 0 for this lane (preregistered in tools/science_funnel/appearance_fetch.py
BEFORE any fetch ran; the per-class contracts in the authored store restate it
mechanically with envelopes derived from the pinned bytes):
  STATEMENT -- an appearance record is admittable only with pinned-byte
  provenance, source-declared (or declared-conversion) scaling, values inside
  envelopes derived from the pinned bytes, and explicit nodata; a spectrum
  without a wavelength pairing provable from the pinned bytes is never
  guessed.
  PREDICTION -- 441 Goldenberg rows (1,781 measured cells), 5,831 PHYLACINE
  species and 495 Chapter-V+S spectra pair under the recorded rule; 494
  spectra + 1 deferred identity admit and 1 AVIRIS spectrum quarantines (its
  detector-overlap grid decrease falls on MEASURED channels; in the other 38
  AVIRIS spectra the overlap channels are nodata and the admitted axes are
  monotonic); every count identity closes with zero silent drops.
  FALSIFIER -- one corrupted row/cell/channel quarantines exactly its own
  record(s), never its neighbours; a spectrum whose channel count matches no
  Wavelengths file refuses pairing; the -1.23e34 sentinel never becomes a
  value.
"""
import csv
import io
import re
import zipfile

from .adapters import rejection
from .common import Refusal, draft, number, require, text

# ---------------------------------------------------------------- Goldenberg

GOLDENBERG_HEADER = ['animal', 'N', 'ID', 'Subspecies', 'B2.TOT', 'B2.UV',
                     'B2.VIS', 'B2.NIR', 'B2.TOT.EGG', 'B2.UV.EGG',
                     'B2.VIS.EGG', 'B2.NIR.EGG', 'class',
                     'treetax_initial_class']
GOLDENBERG_CLASSES = ('Aranea', 'Aves', 'Crocodylia', 'Insecta', 'Mammalia',
                      'Squamata', 'Testudines')
GOLDENBERG_PERCENT_ENVELOPE = (-5.0, 120.0)
GOLDENBERG_FRACTION_ENVELOPE = (-0.05, 1.2)


def _goldenberg_cell(row, column):
    """One cell -> (percent_value_or_None, status); 'NA' is nodata."""
    stripped = (row.get(column) or '').strip()
    if stripped == 'NA' or stripped == '':
        return None, 'NA'
    value = number(stripped)
    require(GOLDENBERG_PERCENT_ENVELOPE[0] <= value <= GOLDENBERG_PERCENT_ENVELOPE[1],
            'reflectance_outside_envelope', f'{column}={stripped}')
    return value, 'measured'


def _goldenberg_name(animal):
    """Mechanical name hygiene: underscores preserved, no whitespace noise."""
    name = animal.strip()
    require(name and re.fullmatch(r'[A-Za-z0-9_.\-]+', name),
            'goldenberg_bad_name', animal)
    return name


def goldenberg_rows(raw, manifest, path):
    """total_dataset.csv -> one observation entity per row + one measurement
    per measured reflectance cell. Percent -> fraction conversion is declared
    on every record; NA cells are statuses, never zeros."""
    rows = list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'), newline='')))
    require(rows, 'empty_capture')
    require(list(rows[0]) == GOLDENBERG_HEADER, 'csv_bad_header',
            str(list(rows[0])))
    out = []
    for index, row in enumerate(rows, 2):
        try:
            animal = _goldenberg_name(text(row['animal'], 'animal'))
            taxon_class = text(row['class'], 'class').strip()
            require(taxon_class in GOLDENBERG_CLASSES,
                    'goldenberg_class_outside_vocabulary', taxon_class)
            n_raw = text(row['N'], 'N').strip()
            n_samples = number(n_raw)
            require(n_samples == int(n_samples) and 1 <= n_samples <= 441,
                    'goldenberg_n_outside_envelope', n_raw)
            n_samples = int(n_samples)
            subspecies = row['Subspecies'].strip()
            sample_id = row['ID'].strip()
            treetax = row['treetax_initial_class'].strip()

            cells, statuses = {}, {}
            for column in GOLDENBERG_HEADER[4:12]:
                value, status = _goldenberg_cell(row, column)
                cells[column] = value
                statuses[column] = status
            measured = {column: value for column, value in cells.items()
                        if value is not None}
            external = f'goldenberg:row{index}:{animal}'
            unknowns = [f'nodata:{column}' for column, status in
                        statuses.items() if status != 'measured']
            if subspecies == 'NA':
                unknowns.append('nodata:Subspecies')
            if sample_id == 'NA':
                unknowns.append('nodata:ID')
            payload = {
                'binomial': animal,
                'taxon_class': taxon_class,
                'subspecies': subspecies if subspecies != 'NA' else None,
                'sample_id': sample_id if sample_id != 'NA' else None,
                'n_samples': n_samples,
                'treetax_initial_class': treetax,
                'reflectance_percent': measured,
                'cell_status': statuses,
            }
            entity = draft(external, 'entity', payload, unknowns=unknowns,
                           label=animal)
            entity['class_contract'] = {
                'class_id': 'batch.observation.goldenberg_taxon', 'version': 1}
            out.append(entity)
            for column, value in sorted(measured.items()):
                fraction = number(value / 100.0)
                require(GOLDENBERG_FRACTION_ENVELOPE[0] <= fraction
                        <= GOLDENBERG_FRACTION_ENVELOPE[1],
                        'reflectance_fraction_outside_envelope',
                        f'{column}={value}')
                kind = 'egg' if column.endswith('.EGG') else 'plumage_integument'
                payload = {
                    'quantity': 'reflectance',
                    'value_si': fraction,
                    'unit_si': '1',
                    'dimensions': [0, 0, 0, 0, 0, 0, 0],
                    'original': {'value': value, 'unit': 'percent reflectance'},
                    'conversion': {'law': 'fraction = percent / 100',
                                   'scale': 0.01},
                    'subject': animal + (':egg' if kind == 'egg' else ''),
                    'conditions': {'taxon_class': taxon_class,
                                   'cell': column,
                                   'cell_kind': kind,
                                   'source_row': index},
                    'raw_cell': row[column].strip(),
                }
                measurement = draft(external + ':' + column, 'measurement',
                                    payload, unknowns=['uncertainty'],
                                    label=animal + ' ' + column)
                measurement['class_contract'] = {
                    'class_id': 'batch.property.goldenberg_reflectance',
                    'version': 1}
                out.append(measurement)
        except Refusal as exc:
            out.append(rejection(f'goldenberg:row{index}', exc))
    return out


# ----------------------------------------------------------------- PHYLACINE

PHYLACINE_COLUMNS = ['Binomial.1.2', 'Order.1.2', 'Family.1.2', 'Genus.1.2',
                     'Species.1.2', 'Terrestrial', 'Marine', 'Freshwater',
                     'Aerial', 'Life.Habit.Method', 'Life.Habit.Source',
                     'Mass.g', 'Mass.Method', 'Mass.Source',
                     'Mass.Comparison', 'Mass.Comparison.Source',
                     'Island.Endemicity', 'IUCN.Status.1.2',
                     'Added.IUCN.Status.1.2', 'Diet.Plant',
                     'Diet.Vertebrate', 'Diet.Invertebrate', 'Diet.Method',
                     'Diet.Source']
PHYLACINE_MASS_ENVELOPE_G = (0.0, 2e8)


def _phylacine_flag(row, column):
    raw = text(row[column], column).strip()
    require(raw in ('0', '1'), 'phylacine_flag_invalid', f'{column}={raw}')
    return int(raw)


def phylacine_species(raw, manifest, path):
    """Derived trait table -> one species entity per row. Mass converts g -> kg
    with the exact SI scale; a row with a missing or out-of-envelope mass
    quarantines whole (parse everything before drafting anything)."""
    rows = list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'), newline='')))
    require(rows, 'empty_capture')
    require(list(rows[0]) == PHYLACINE_COLUMNS, 'csv_bad_header',
            str(list(rows[0])))
    out = []
    for index, row in enumerate(rows, 2):
        try:
            binomial = text(row['Binomial.1.2'], 'Binomial.1.2').strip()
            require(re.fullmatch(r'[A-Za-z0-9_\-]+', binomial),
                    'phylacine_bad_binomial', binomial)
            genus = text(row['Genus.1.2'], 'Genus.1.2').strip()
            species = text(row['Species.1.2'], 'Species.1.2').strip()
            require(binomial == genus + '_' + species,
                    'binomial_disagrees_with_tags',
                    binomial + ' vs ' + genus + '_' + species)
            mass_raw = text(row['Mass.g'], 'Mass.g').strip()
            mass_g = number(mass_raw)
            require(PHYLACINE_MASS_ENVELOPE_G[0] < mass_g
                    <= PHYLACINE_MASS_ENVELOPE_G[1],
                    'phylacine_mass_outside_envelope', mass_raw)
            mass_kg = number(mass_g / 1000.0)
            diet = {name: number(row['Diet.' + name])
                    for name in ('Plant', 'Vertebrate', 'Invertebrate')}
            for name, value in diet.items():
                require(0.0 <= value <= 100.0, 'phylacine_diet_outside_envelope',
                        f'{name}={value}')
            habitat = {name: _phylacine_flag(row, name)
                       for name in ('Terrestrial', 'Marine', 'Freshwater',
                                    'Aerial')}
            payload = {
                'binomial': binomial,
                'tags': {'order': row['Order.1.2'].strip(),
                         'family': row['Family.1.2'].strip(),
                         'genus': genus, 'species': species},
                'mass_g': mass_g,
                'mass_kg': mass_kg,
                'mass_method': row['Mass.Method'].strip(),
                'habitat_flags': habitat,
                'diet_percent': diet,
                'diet_method': row['Diet.Method'].strip(),
                'island_endemicity': row['Island.Endemicity'].strip(),
                'iucn_status': text(row['IUCN.Status.1.2'],
                                    'IUCN.Status.1.2').strip(),
                'added_iucn_status': row['Added.IUCN.Status.1.2'].strip(),
                'source_row': index,
            }
            record = draft('phylacine:' + binomial, 'entity', payload,
                           unknowns=['mass_source_citation_not_projected',
                                     'life_habit_source_citation_not_projected',
                                     'diet_source_citation_not_projected',
                                     'phylogeny_members_not_projected'],
                           label=binomial)
            record['class_contract'] = {
                'class_id': 'batch.entity.phylacine_species', 'version': 1}
            out.append(record)
        except Refusal as exc:
            out.append(rejection(f'phylacine:row{index}', exc))
    return out


# ------------------------------------------------------------- USGS SPLib v7

SPLIB_SENTINEL = -1.23e34
SPLIB_FAMILY_BY_SIGNATURE = (('ASDNG', 'ASD'), ('ASDHR', 'ASD'),
                             ('ASDFR', 'ASD'), ('ASD', 'ASD'),
                             ('AVIRIS', 'AVIRIS'), ('BECK', 'BECK'),
                             ('NIC4', 'NIC4'))
SPLIB_REFLECTANCE_ENVELOPE = (0.0, 2.5)


def _splib_family(signature):
    for prefix, family in SPLIB_FAMILY_BY_SIGNATURE:
        if signature.startswith(prefix):
            return family
    raise Refusal('splib_signature_unknown', signature)


def _splib_wavelength_files(archive):
    """The zip's own Wavelengths files -> {family: (member, channels)}."""
    out = {}
    for name in archive.namelist():
        if 'Wavelengths' not in name or not name.endswith('.txt'):
            continue
        base = name.rsplit('/', 1)[-1]
        parts = base.split('_')
        require(len(parts) >= 4 and parts[1] == 'Wavelengths',
                'splib_wavelength_layout_changed', base)
        family = parts[2].split('-')[0]
        channels = []
        for line in archive.read(name).decode('utf-8-sig').splitlines()[1:]:
            try:
                channels.append(float(line))
            except ValueError:
                continue
        require(channels, 'splib_wavelength_file_empty', base)
        if family in out:
            require(out[family][1] == channels,
                    'splib_wavelength_family_conflict', base)
        out[family] = (name, channels)
    return out


def _splib_header(line):
    """' splib07a Record=NNNN: Sample Name... SIGNATURE AREF...' parsed."""
    match = re.match(r'\s*splib07([ab])\s+Record=(\d+):\s*(.*)$', line)
    require(match is not None, 'splib_bad_header', line[:80])
    tokens = match.group(3).split()
    require(len(tokens) >= 3, 'splib_header_tokens', line[:80])
    signature = tokens[-2]
    record_no = int(match.group(2))
    return record_no, signature, ' '.join(tokens[:-2])


def _splib_values(blob):
    """Value lines (bytes or text) -> floats; a non-numeric line refuses."""
    if isinstance(blob, bytes):
        blob = blob.decode('utf-8-sig')
    values = []
    for line in blob.splitlines()[1:]:
        stripped = line.strip()
        if not stripped:
            continue
        values.append(number(stripped))
    return values


def _splib_wavelength_runs(wavelengths, indices):
    """Nodata channel indices -> closed [start_wl, end_wl] runs in micrometers
    (deterministic; never interpolated away silently)."""
    runs = []
    for index in sorted(indices):
        if runs and index == runs[-1][2] + 1:
            runs[-1][2] = index
        else:
            runs.append([index, index, index])
    return [[wavelengths[run[1]], wavelengths[run[2]]] for run in runs]


def splib07_chapter_spectra(raw, manifest, path):
    """Pinned splib07a zip bytes -> one series record per Chapter-V/Chapter-S
    spectrum + one deferred identity record for the full bundle.

    The wavelength pairing law: a spectrum's instrument signature (its own
    header tokens) names a family; the family's Wavelengths file -- read from
    the SAME pinned zip -- must have exactly the spectrum's channel count.
    No pairing provable from the pinned bytes, no admission (quarantine,
    never a guess). The -1.23e34 nodata channels are excluded and counted as
    wavelength runs, never interpolated; paired errorbars files (exact name
    match, matching channel count) ride as per-channel uncertainties."""
    constants = manifest.get('constants', {})
    chapters = constants.get('chapters')
    require(isinstance(chapters, list) and chapters, 'missing_text',
            'constants.chapters')
    deferred = constants.get('deferred')
    require(isinstance(deferred, dict), 'missing_text', 'constants.deferred')

    prefix = 'ASCIIdata_splib07a/'
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names = archive.namelist()
        waves = _splib_wavelength_files(archive)
        errorbars = {n.rsplit('/', 1)[-1][len('errorbars_for_'):]:
                     n for n in names
                     if n.startswith(prefix + 'errorbars/errorbars_for_')
                     and n.endswith('.txt')}
        out = []
        quarantined = 0
        for chapter in chapters:
            members = [n for n in names
                       if n.startswith(prefix + chapter + '/')
                       and n.endswith('.txt')]
            require(members, 'splib_chapter_missing', chapter)
            for member in sorted(members):
                base = member.rsplit('/', 1)[-1]
                location = f'splib07a:{chapter}:{base}'
                try:
                    lines = archive.read(member).decode('utf-8-sig').splitlines()
                    record_no, signature, sample_name = _splib_header(lines[0])
                    family = _splib_family(signature)
                    y = _splib_values('\n'.join(lines))
                    pair = waves.get(family)
                    require(pair is not None and len(pair[1]) == len(y),
                            'spectrum_grid_unpaired',
                            f'{base}: {signature} x {len(y)} channels')
                    wavelengths = pair[1]

                    uncertainties = None
                    err_member = errorbars.get(base)
                    if err_member is not None:
                        err_values = _splib_values(archive.read(err_member))
                        require(len(err_values) == len(y),
                                'splib_errorbars_channels', base)
                        uncertainties = err_values

                    samples, nodata = [], []
                    for order, (wavelength, value) in enumerate(zip(wavelengths, y)):
                        if value == SPLIB_SENTINEL:
                            nodata.append(order)
                            continue
                        require(SPLIB_REFLECTANCE_ENVELOPE[0] <= value
                                <= SPLIB_REFLECTANCE_ENVELOPE[1],
                                'spectrum_value_outside_envelope',
                                f'{base}: {value} at {wavelength} um')
                        uncertainty = None
                        if uncertainties is not None \
                                and uncertainties[order] != SPLIB_SENTINEL:
                            uncertainty = uncertainties[order]
                        samples.append({'x': number(wavelength * 1e-6),
                                        'value': value,
                                        'uncertainty': uncertainty})
                    require(len(samples) >= 2, 'spectrum_degenerate', base)
                    increasing = all(samples[i]['x'] < samples[i + 1]['x']
                                     for i in range(len(samples) - 1))
                    require(increasing, 'spectrum_axis_not_increasing', base)
                    payload = {
                        'sample_name': sample_name,
                        'record_no': record_no,
                        'chapter': chapter,
                        'instrument_signature': signature,
                        'instrument_family': family,
                        'wavelength_file': pair[0].rsplit('/', 1)[-1],
                        'channel_count': len(y),
                        'nodata_channel_count': len(nodata),
                        'nodata_wavelength_runs_um':
                            _splib_wavelength_runs(wavelengths, nodata),
                        'errorbars_paired': err_member is not None,
                        'quantity': 'relative_reflectance',
                        'unit_si': '1',
                        'x_quantity': 'length',
                        'x_unit_si': 'm',
                        'x_conversion': {'law': 'm = micrometer * 1e-6',
                                         'scale': 1e-06},
                        'samples': samples,
                    }
                    unknowns = ['sample_metadata_html_not_pinned']
                    if err_member is None:
                        unknowns.append('errorbars_absent_for_this_spectrum')
                    if family == 'AVIRIS':
                        unknowns.append('aviris_1996_grid_has_3_detector_'
                                        'overlap_decreases_monotonic_spectra_only')
                    record = draft('splib07:' + str(record_no), 'series',
                                   payload, unknowns=unknowns,
                                   label=sample_name)
                    record['class_contract'] = {
                        'class_id': 'batch.series.splib07_spectrum',
                        'version': 1}
                    out.append(record)
                except Refusal as exc:
                    quarantined += 1
                    out.append(rejection(location, exc))

    deferred_record = draft('splib07:deferred:usgs_splib07.zip', 'entity', {
        'status': 'deferred',
        'artifact': deferred.get('path', 'usgs_splib07.zip'),
        'size_bytes': number(deferred['bytes']),
        'url': deferred['url'],
        'license': 'CC0 1.0',
        'cause': deferred['cause'],
    }, unknowns=['bytes_not_downloaded', 'specpr_plots_photos_not_admitted'],
        label='USGS SPLib v7 full bundle (deferred)')
    deferred_record['class_contract'] = {
        'class_id': 'batch.deferred.usgs_splib07_full', 'version': 1}
    out.append(deferred_record)
    require(out, 'empty_capture')
    return out


APPEARANCE_ADAPTERS = {'goldenberg_rows': goldenberg_rows,
                       'phylacine_species': phylacine_species,
                       'splib07_chapter_spectra': splib07_chapter_spectra}

# Registration must survive the circular-import order (connectors_appearance
# is alphabetically first in the connectors auto-load, so this module can be
# imported while adapters.py itself is only partially executed and its *_ADAPTERS
# merge loop has not run yet). Mutating the shared dict directly -- the
# adapters_muscle pattern -- registers under every import order.
from .adapters import ADAPTERS as _ADAPTERS
for _name, _fn in APPEARANCE_ADAPTERS.items():
    _ADAPTERS[_name] = _fn
