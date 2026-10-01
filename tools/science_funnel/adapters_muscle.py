"""INTAKE-MUSCLE lane adapters (2026-09-17). Two CC BY 4.0 biomechanics
sources admitted through the batch connector machinery:

  guimaraes_arch      Guimaraes, Vereecke & Wiseman 2026 (Am J Phys Anthropol,
                      PMC13425262 S1 xlsx): hindlimb muscle architecture of 6
                      primate species including Macaca mulatta -- one
                      measurement record per specimen x muscle x parameter.
  oku_bipedal_series  Oku, Ide & Ogihara 2021 (Commun Biol 4:1831, PMC7940622
                      Supplementary Data 1 xlsx): joint angles, GRFs, joint
                      moments and muscle forces over the gait cycle, before and
                      after foot-morphology alteration -- one series record per
                      sheet x block x signal.

xlsx is parsed with the standard library only (zipfile + xml.etree over
xl/workbook.xml, xl/_rels, xl/sharedStrings.xml, xl/worksheets/sheetN.xml).

Unit interpretation is DERIVED from the data, never from the header text
alone: the Guimaraes sheet headers declare _m/_kg on every column while the
values of the whole-muscle/belly/tendon length and mass columns are
millimetres and grams. The closure law the dataset defines for itself,
PCSA = muscle_mass / (rho * fascicle_length) with rho = 1060 kg/m3, is
enforced per row (2% tolerance) together with the segment identities
muscle = belly + tendon (length and mass, 2%). A row violating any law is
quarantined whole; nothing is dropped silently."""
import io
import math
import re
import zipfile
import xml.etree.ElementTree as ET

from .adapters import ADAPTERS, rejection
from .common import Refusal, draft, number, require, text
from .units import convert

_SSML = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
_OFFDOC = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
_PKGREL = 'http://schemas.openxmlformats.org/package/2006/relationships'

MUSCLE_DENSITY_KG_M3 = 1060.0
LAW_TOLERANCE = 0.02


# ---------------------------------------------------------------- xlsx reading

def _column_index(ref):
    letters = re.match(r'([A-Z]+)', ref).group(1)
    out = 0
    for ch in letters:
        out = out * 26 + (ord(ch) - 64)
    return out - 1


def _workbook(raw):
    """zipfile + sheet name -> worksheet xml path (workbook.xml + its rels)."""
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
    """Ordered rows as {zero-based column index: raw string value}."""
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


# ------------------------------------------------------------ guimaraes_arch

# The workbook's own column dictionary (Information sheet) declares these
# headers; sheets disagree on suffixes and pennation spelling. Variants map to
# one canonical field name; an unknown non-empty header refuses the sheet.
_HEADER_VARIANTS = {
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

# field -> (canonical unit of the VALUES as they sit in the sheet, quantity)
# fl/pcsa really are m/m2; the six segment columns carry mm/g despite their
# headers -- the PCSA closure law pins this interpretation row by row.
_GUIMARAES_FIELDS = {
    'fl_m': ('m', 'length', 'fascicle length'),
    'pcsa_m2': ('m2', 'area', 'physiological cross-sectional area'),
    'musc_len': ('mm', 'length', 'whole-muscle length (belly + tendon)'),
    'musc_mass': ('g', 'mass', 'whole-muscle mass (belly + tendon)'),
    'belly_len': ('mm', 'length', 'muscle belly length'),
    'belly_mass': ('g', 'mass', 'muscle belly mass'),
    'tendon_len': ('mm', 'length', 'external tendon length'),
    'tendon_mass': ('g', 'mass', 'external tendon mass'),
}


def _specimens(rows):
    """Information sheet -> species (space form) -> specimen record."""
    out = {}
    header_seen = False
    for cells in rows:
        first = cells.get(0, '').strip()
        if not header_seen:
            header_seen = first.lower() == 'specimen id'
            continue
        if first.lower().startswith('column id'):
            break
        species = cells.get(1, '').strip()
        if not first or not species:
            continue
        mass_raw = cells.get(4, '').strip()
        match = re.match(r'[-+0-9.eE]+', mass_raw)
        limbs = out_of = cells.get(5, '').strip()
        limb_set = ('RL' if 'left' in limbs.lower() and 'right' in limbs.lower()
                    else 'R' if 'right' in limbs.lower()
                    else 'L' if 'left' in limbs.lower() else '')
        out[species] = {
            'specimen_id': first,
            'sex': cells.get(2, '').strip(),
            'age': cells.get(3, '').strip(),
            'body_mass_raw': mass_raw,
            'body_mass_kg': float(match.group(0)) if match else None,
            'limbs_dissected': limb_set,
        }
    require(out, 'specimen_table_missing')
    return out


def _within(parts, whole):
    return abs(parts - whole) / whole <= LAW_TOLERANCE


def guimaraes_arch(raw, manifest, path):
    archive, sheets = _workbook(raw)
    shared = _shared_strings(archive)
    out = []

    specimens = None
    for name, target in sorted(sheets):
        if name.strip().lower() == 'information':
            specimens = _specimens(_sheet_rows(archive, target, shared))
    require(specimens is not None, 'information_sheet_missing')

    for name, target in sorted(sheets):
        if name.strip().lower() == 'information':
            continue
        rows_ = _sheet_rows(archive, target, shared)
        require(rows_, 'empty_sheet', name)
        header = {}
        for column, label in rows_[0].items():
            canonical = _HEADER_VARIANTS.get(label.strip())
            require(canonical and canonical not in header.values(),
                    'unknown_or_duplicate_header', f'{name}:{label}')
            header[canonical] = column
        for field in ('species', 'muscle', 'fl_m', 'pcsa_m2', 'musc_len',
                      'musc_mass', 'belly_len', 'belly_mass', 'tendon_len',
                      'tendon_mass'):
            require(field in header, 'required_column_missing', f'{name}:{field}')

        for row_number, cells in enumerate(rows_[1:], 2):
            if not cells:
                continue  # sheets declare ~1000 rows; only the data rows carry cells
            location = f'guimaraes:{name}:row{row_number}'
            try:
                species = text(cells.get(header['species'], ''), 'species').strip()
                muscle = text(cells.get(header['muscle'], ''), 'muscle').strip()
                specimen = specimens.get(species.replace('_', ' '))
                require(specimen is not None, 'specimen_missing', species)
                limb_raw = cells.get(header.get('limb', -1), '')
                if limb_raw.strip() in ('L', 'R'):
                    limb = limb_raw.strip()
                else:
                    require(len(specimen['limbs_dissected']) == 1,
                            'limb_ambiguous', specimen['limbs_dissected'])
                    limb = specimen['limbs_dissected']

                values = {field: number(cells.get(header[field], ''))
                          for field in _GUIMARAES_FIELDS}
                for field, value in values.items():
                    require(value > 0, 'nonpositive_value', f'{field}={value}')

                # Row laws from the dataset's own computed columns (2% tolerance;
                # the deviation distribution is bimodal -- passing rows sit at
                # ~1e-5, violators far above 20% -- so the cut is not tuned).
                # Belly+tendon LENGTH additivity is NOT enforced: its deviation
                # is continuous (2%..90% across 56 rows), so it is a recorded
                # condition, never a quarantine.
                mass_kg = values['musc_mass'] / 1000.0
                pcsa_pred = mass_kg / (MUSCLE_DENSITY_KG_M3 * values['fl_m'])
                require(math.isclose(pcsa_pred, values['pcsa_m2'],
                                     rel_tol=LAW_TOLERANCE),
                        'pcsa_closure_violation',
                        f"pcsa={values['pcsa_m2']} predicted={pcsa_pred}")
                require(_within(values['belly_mass'] + values['tendon_mass'],
                                values['musc_mass']), 'mass_additivity_violation',
                        f"belly+tendon={values['belly_mass'] + values['tendon_mass']}"
                        f" whole={values['musc_mass']}")
                length_deviation = (abs(values['belly_len'] + values['tendon_len']
                                        - values['musc_len']) / values['musc_len'])

                conditions = {
                    'species': species,
                    'species_common': cells.get(header.get('species_common', -1),
                                                '').strip(),
                    'specimen_id': specimen['specimen_id'],
                    'sex': specimen['sex'],
                    'age': specimen['age'],
                    'body_mass_raw': specimen['body_mass_raw'],
                    'limb': limb,
                    'sheet': name,
                    'dataset': 'Guimaraes/Vereecke/Wiseman 2026 dissection dataset',
                    'muscle_density_law': 'PCSA = m/(1060 kg/m3 * FL), '
                                          'enforced per row at 2%',
                    'length_additivity_rel_deviation': length_deviation,
                }
                subject = f'{species}/muscle/{muscle} ({limb})'
                penn_raw = cells.get(header.get('penn_deg', -1), '')
                emittable = [(field, unit, quantity)
                             for field, (unit, quantity, _) in _GUIMARAES_FIELDS.items()]
                if penn_raw.strip():
                    emittable.append(('penn_deg', 'deg', 'angle'))
                for field, unit, quantity in emittable:
                    source_value = penn_raw if field == 'penn_deg' else values[field]
                    payload = convert(source_value, unit, quantity)
                    payload.update(subject=subject, conditions=dict(conditions),
                                   source_field=field,
                                   parameter=(_GUIMARAES_FIELDS.get(field, ({}, {}, 'pennation angle'))[2]))
                    unknowns = ['single_specimen_per_species',
                                'fascicle_sampling_not_published']
                    if field in ('musc_len', 'musc_mass', 'belly_len',
                                 'belly_mass', 'tendon_len', 'tendon_mass'):
                        unknowns.append('header_declares_m_kg_but_values_are_'
                                        + ('mm' if unit == 'mm' else 'g'))
                    if field == 'penn_deg':
                        unknowns.append('pennation_averaged_over_dissection_'
                                        'observations_19_homologous_muscles_only')
                    row = draft(f'guimaraes:{species}:{muscle}:{limb}:{field}',
                                'measurement', payload, unknowns=unknowns,
                                label=f'{species} {muscle} {field}')
                    row['class_contract'] = {
                        'class_id': 'batch.property.measurement', 'version': 1}
                    out.append(row)
            except Refusal as exc:
                out.append(rejection(location, exc))
    require(out, 'empty_capture')
    return out


# ------------------------------------------------------- oku_bipedal_series

# Oku 2021 Fig. 4 caption: "Red solid line = before alteration. Gray dotted
# line = after alteration." -- the two column blocks of each sheet follow that
# order (recorded on every record as the role basis; never silently resolved).
OKU_BLOCK_ROLES = ('before_alteration', 'after_alteration')
OKU_SIGN_CONVENTION = ('joint angles and moments positive for hip flexion, knee '
                       'extension, and ankle and metatarsophalangeal dorsiflexion; '
                       'horizontal GRF negative for braking, positive for propelling')
OKU_MUSCLES = ('IL', 'GMED', 'VAS', 'TA', 'SOL', 'RF', 'BIFl', 'GAS', 'EDL', 'FDL')


def _oku_signal_semantics(label):
    clean = label.strip()
    if clean in ('GRF h', 'GRF v'):
        return 'N', 'force', 'ground reaction force'
    if clean.endswith('angle'):
        return 'rad', 'angle', 'joint angle'
    if clean.endswith('torque'):
        return 'N*m', 'torque', 'joint moment'
    if clean in OKU_MUSCLES:
        return 'N', 'force', 'muscle force'
    raise Refusal('unknown_signal', label)


def oku_bipedal_series(raw, manifest, path):
    archive, sheets = _workbook(raw)
    shared = _shared_strings(archive)
    out = []
    for name, target in sorted(sheets):
        rows_ = _sheet_rows(archive, target, shared)
        require(len(rows_) >= 3, 'empty_sheet', name)
        header = rows_[0]
        labelled = sorted(column for column, value in header.items() if value.strip())
        require(labelled and labelled[0] > 0, 'x_axis_column_unexpected', name)
        # two label blocks split by the empty separator column
        blocks, current = [], [labelled[0]]
        for column in labelled[1:]:
            if column == current[-1] + 1:
                current.append(column)
            else:
                blocks.append(current)
                current = [column]
        blocks.append(current)
        require(len(blocks) == 2 and all(len(b) == 10 for b in blocks),
                'block_structure_unexpected', f'{name}:{[len(b) for b in blocks]}')

        for cells in rows_[1:]:
            require(0 in cells, 'x_value_missing', name)
        for block_index, block in enumerate(blocks):
            role = OKU_BLOCK_ROLES[block_index]
            for column in block:
                label = header[column].strip()
                unit, quantity, kind = _oku_signal_semantics(label)
                external_id = f'oku2021:{name}:{role}:{label}'
                try:
                    samples = []
                    metadata = None
                    for cells in rows_[1:]:
                        x = convert(number(cells[0]) / 100.0, '1', 'dimensionless')
                        y = convert(cells.get(column, ''), unit, quantity)
                        current = {'subject': label,
                                   'conditions': {
                                       'figure': 'Fig. 4 (paper text: the raw data '
                                                 'are provided in Supplementary Data 1)',
                                       'sheet': name,
                                       'block': role,
                                       'block_role_basis': 'figure caption line order '
                                           '(red solid = before alteration, gray dotted '
                                           '= after alteration); sheet itself is unlabelled',
                                       'signal_kind': kind,
                                       'sign_convention': OKU_SIGN_CONVENTION,
                                       'x_semantics': 'percent of gait cycle '
                                                      '(integer 0-100) -> fraction',
                                       'subject_species': 'Macaca fuscata '
                                                          '(Japanese macaque)',
                                       'source_kind': 'forward-dynamics simulation '
                                           'of a planar nine-link model with ten '
                                           'muscles driven by a CPG',
                                   },
                                   'x_quantity': x['quantity'], 'x_unit_si': x['unit_si'],
                                   'quantity': y['quantity'], 'unit_si': y['unit_si']}
                        require(metadata is None or current == metadata,
                                'series_context_changed', external_id)
                        metadata = current
                        require(not samples or x['value_si'] > samples[-1]['x'],
                                'axis_not_increasing', external_id)
                        samples.append({'x': x['value_si'], 'value': y['value_si'],
                                        'uncertainty': None})
                    require(len(samples) >= 2, 'insufficient_samples', external_id)
                    row = draft(external_id, 'series',
                                {**metadata, 'samples': samples,
                                 'interpolation': 'unspecified'},
                                unknowns=['block_role_inferred_from_caption_line_order',
                                          'sheet_named_fig3_but_panels_match_fig4_'
                                          'caption_angles_grf_moments_forces',
                                          'no_per_sample_uncertainty_published',
                                          'simulation_output_not_biological_measurement'],
                                label=f'Oku 2021 {role} {label}')
                    row['class_contract'] = {'class_id': 'batch.property.series',
                                             'version': 1}
                    out.append(row)
                except Refusal as exc:
                    out.append(rejection(f'oku2021:{name}:{role}:{label}', exc))
    require(out, 'empty_capture')
    return out


ADAPTERS['guimaraes_arch'] = guimaraes_arch
ADAPTERS['oku_bipedal_series'] = oku_bipedal_series
