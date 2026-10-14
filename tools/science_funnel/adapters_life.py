"""Life-science funnels: PanTHERIA traits, NCBI taxdmp Macaca subtree, Rhea
ChEBI-SMILES species. All imported content is data; nothing here executes a
model. Sentinel law for PanTHERIA: a -999 cell in ANY numeric rendering is
nodata with an explicit unknown, never a measurement."""
import csv
import io
import zipfile

from .adapters import rejection
from .common import Refusal, draft, number, require, text
from .units import DIMENSIONS, convert

PANTHERIA_MEMBER = 'PanTHERIA_1-0_WR05_Aug2008.txt'
PANTHERIA_TAGS = ('MSW05_Order', 'MSW05_Family', 'MSW05_Genus', 'MSW05_Species',
                  'MSW05_Binomial')
PANTHERIA_TRAITS = ('5-1_AdultBodyMass_g', '18-1_BasalMetRate_mLO2hr',
                    '5-2_BasalMetRateMass_g')
SENTINEL = -999.0


def norm_name(name):
    """Name-match normalization: underscore<->space, whitespace collapse, case."""
    return ' '.join(name.replace('_', ' ').split()).lower()


def pantheria_cell(value):
    """One trait cell -> (value_or_None, status). -999 in any rendering is
    nodata; empty is nodata; anything else must parse as a finite number."""
    stripped = value.strip()
    if stripped == '':
        return None, 'empty'
    try:
        parsed = float(stripped)
    except ValueError as exc:
        raise Refusal('bad_trait_cell', f'{stripped!r}') from exc
    if parsed == SENTINEL:
        return None, 'sentinel_-999'
    return number(parsed), 'measured'


def _subtree_names(blob):
    """Companion macaca_names.tsv -> {normalized name -> set(tax_ids)}; a name
    mapped to several taxa is AMBIGUOUS and the caller quarantines on hit."""
    names = {}
    for line in blob.decode('utf-8-sig').splitlines()[1:]:
        if not line.strip():
            continue
        parts = line.split('\t')
        require(len(parts) >= 4, 'macaca_names_row_short', line)
        names.setdefault(norm_name(parts[1]), set()).add(int(parts[0]))
    return names


def _pantheria_row(row, col, index, calorific, subtree):
    """Parse every cell BEFORE drafting anything: a bad row quarantines whole."""
    tags = {tag: text(row[col[tag]], tag) for tag in PANTHERIA_TAGS}
    binomial = tags['MSW05_Binomial']
    require(norm_name(binomial) == norm_name(tags['MSW05_Genus'] + ' '
                                             + tags['MSW05_Species']),
            'binomial_disagrees_with_tags',
            binomial + ' vs ' + tags['MSW05_Genus'] + ' ' + tags['MSW05_Species'])
    mass_v, mass_st = pantheria_cell(row[col['5-1_AdultBodyMass_g']])
    bmr_v, bmr_st = pantheria_cell(row[col['18-1_BasalMetRate_mLO2hr']])
    bmass_v, bmass_st = pantheria_cell(row[col['5-2_BasalMetRateMass_g']])
    taxonomy = None
    if tags['MSW05_Genus'] == 'Macaca':
        hits = subtree.get(norm_name(binomial), set())
        require(len(hits) == 1,
                'macaca_name_unresolved' if not hits else 'macaca_name_ambiguous',
                binomial + ' -> ' + repr(sorted(hits)))
        taxonomy = {'provider': 'ncbi_taxdmp.macaca_subtree',
                    'tax_id': next(iter(hits)), 'resolved_name': binomial}
    unknowns = [f'nodata:{field}:{status}'
                for field, status in (('adult_body_mass_g', mass_st),
                                      ('basal_met_rate_mLO2hr', bmr_st),
                                      ('bmr_measurement_mass_g', bmass_st))
                if status != 'measured']
    species = draft('pantheria:' + binomial, 'entity',
                    {'species_tags': tags,
                     'trait_status': {'adult_body_mass_g': mass_st,
                                      'basal_met_rate_mLO2hr': bmr_st,
                                      'bmr_measurement_mass_g': bmass_st},
                     'taxonomy': taxonomy, 'source_row': index},
                    unknowns=unknowns, label=binomial)
    species['class_contract'] = {'class_id': 'batch.entity.pantheria_species', 'version': 1}
    records = [species]
    # Measurement conditions stay lean (species + genus + row + resolution);
    # the full MSW05 tag set lives on the species entity, once per row.
    conditions = {'species': binomial, 'genus': tags['MSW05_Genus'],
                  'source_row': index}
    if taxonomy is not None:
        conditions['ncbi_tax_id'] = taxonomy['tax_id']
    if mass_v is not None:
        payload = convert(mass_v, 'g', 'mass')
        payload.update(subject=binomial, conditions=dict(conditions),
                       raw_cell=row[col['5-1_AdultBodyMass_g']].strip())
        record = draft('pantheria:' + binomial + ':adult_body_mass_g', 'measurement',
                       payload, unknowns=['uncertainty'])
        record['class_contract'] = {'class_id': 'batch.property.pantheria_trait', 'version': 1}
        records.append(record)
    if bmr_v is not None:
        watts = number(bmr_v * calorific / 3600.0)
        require(watts > 0, 'bmr_nonpositive', binomial)
        bmr_conditions = dict(conditions)
        bmr_conditions['bmr_measurement_mass_g'] = bmass_v
        bmr_conditions['bmr_measurement_mass_status'] = bmass_st
        payload = {'quantity': 'power', 'value_si': watts, 'unit_si': 'W',
                   'dimensions': list(DIMENSIONS['power']),
                   'original': {'value': bmr_v, 'unit': 'mL O2 / hour'},
                   'conversion': {'law': 'W = mLO2hr * J_per_mL_O2 / 3600',
                                  'o2_calorific_J_per_mL': calorific,
                                  'assumption': 'approximate respiratory calorific '
                                                'equivalent (typical mixed-diet RQ); '
                                                'DECLARED assumption, not a PanTHERIA '
                                                'measurement'}}
        payload.update(subject=binomial, conditions=bmr_conditions,
                       raw_cell=row[col['18-1_BasalMetRate_mLO2hr']].strip())
        record = draft('pantheria:' + binomial + ':basal_metabolic_rate', 'measurement',
                       payload, unknowns=['uncertainty', 'o2_calorific_assumed_'
                                          + str(calorific) + '_J_per_mL'])
        record['class_contract'] = {'class_id': 'batch.property.pantheria_trait', 'version': 1}
        records.append(record)
    return records


def pantheria_traits(raw, manifest, path):
    """PanTHERIA 1-0 WR05 archive -> one species entity per row plus one
    measurement per measured trait cell. BMR converts mLO2/hr -> W with the
    calorific equivalent declared by the connector (manifest constant). Macaca
    rows keep species tags and resolve their binomial against the pinned NCBI
    taxdmp Macaca subtree companion; unresolved or ambiguous names quarantine
    the row -- no fuzzy match, ever."""
    calorific = number(manifest.get('constants', {}).get('o2_calorific_J_per_mL'))
    names_pin = manifest.get('constants', {}).get('macaca_names_sha256')
    require(names_pin, 'missing_text', 'constants.macaca_names_sha256')
    subtree = _subtree_names(path.parent.joinpath(names_pin).read_bytes())
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        require(PANTHERIA_MEMBER in archive.namelist(), 'pantheria_layout_changed')
        table = archive.read(PANTHERIA_MEMBER).decode('utf-8-sig')
    rows = list(csv.reader(io.StringIO(table, newline=''), delimiter='\t'))
    require(rows and rows[0][:5] == list(PANTHERIA_TAGS), 'pantheria_header_changed')
    col = {name: index for index, name in enumerate(rows[0])}
    for field in PANTHERIA_TRAITS:
        require(field in col, 'pantheria_column_missing', field)
    out = []
    for index, row in enumerate(rows[1:], 2):
        if not row:
            continue
        try:
            require(len(row) == len(rows[0]), 'row_width_changed', str(index))
            out.extend(_pantheria_row(row, col, index, calorific, subtree))
        except Refusal as exc:
            out.append(rejection(f'row:{index}', exc))
    return out


def ncbi_taxdmp_macaca(raw, manifest, path):
    """Derived Macaca subtree (nodes primary, names companion) -> one
    reference_entity per taxon with rank and every name-class record."""
    names_pin = manifest.get('constants', {}).get('macaca_names_sha256')
    require(names_pin, 'missing_text', 'constants.macaca_names_sha256')
    names = {}
    for line in path.parent.joinpath(names_pin).read_bytes() \
            .decode('utf-8-sig').splitlines()[1:]:
        if not line.strip():
            continue
        parts = line.split('\t')
        require(len(parts) >= 4, 'macaca_names_row_short', line)
        names.setdefault(int(parts[0]), []).append(
            {'name': parts[1], 'unique_name': parts[2], 'name_class': parts[3]})
    lines = raw.decode('utf-8-sig').splitlines()
    require(lines and lines[0] == 'tax_id\tparent_tax_id\trank',
            'macaca_nodes_header_changed')
    taxa = {}
    for line in lines[1:]:
        if not line.strip():
            continue
        parts = line.split('\t')
        require(len(parts) == 3, 'macaca_nodes_row_shape', line)
        taxa[int(parts[0])] = (int(parts[1]), text(parts[2], 'rank'))
    require(set(names) == set(taxa), 'names_nodes_mismatch',
            f'names={len(names)} nodes={len(taxa)}')
    roots = [tax for tax, (parent, _rank) in taxa.items() if parent not in taxa]
    require(len(roots) == 1, 'subtree_roots_not_unique', repr(roots))
    root = roots[0]
    out = []
    for tax in sorted(taxa):
        parent, rank = taxa[tax]
        taxon_names = names[tax]
        scientific = [entry['name'] for entry in taxon_names
                      if entry['name_class'] == 'scientific name']
        require(len(scientific) == 1, 'scientific_name_not_unique', repr(scientific))
        row = draft('ncbitaxon:' + str(tax), 'entity',
                    {'tax_id': tax, 'parent_tax_id': parent, 'rank': rank,
                     'scientific_name': scientific[0], 'names': taxon_names,
                     'subtree_root': tax == root},
                    label=scientific[0],
                    unknowns=['division_and_gc_code_not_projected',
                              'lineage_outside_macaca_not_projected'])
        row['class_contract'] = {'class_id': 'batch.entity.ncbi_taxon', 'version': 1}
        out.append(row)
    return out


def rhea_chebi_smiles(raw, manifest, path):
    """Rhea rhea-chebi-smiles.tsv (headerless CHEBI id -> SMILES map) -> one
    entity per row; duplicate CHEBI identities are withheld by the pipeline's
    duplicate-identity law, never merged or greedily picked."""
    out = []
    for index, line in enumerate(raw.decode('utf-8-sig').splitlines(), 1):
        if not line.strip():
            continue
        parts = line.split('\t')
        try:
            require(len(parts) == 2, 'rhea_row_shape', repr(parts))
            chebi = text(parts[0], 'chebi_id')
            require(chebi.startswith('CHEBI:') and chebi[6:].isdigit(),
                    'chebi_id_syntax', chebi)
            smiles = text(parts[1], 'smiles')
            row = draft('rhea-chebi:' + chebi, 'entity',
                        {'chebi_id': chebi, 'smiles': smiles, 'id_scheme': 'chebi'},
                        unknowns=['structure_not_validated',
                                  'reaction_membership_not_in_file'],
                        label=chebi)
            row['class_contract'] = {'class_id': 'batch.entity.rhea_chebi_species',
                                     'version': 1}
            out.append(row)
        except Refusal as exc:
            out.append(rejection(f'row:{index}', exc))
    return out


LIFE_ADAPTERS = {'pantheria_traits': pantheria_traits,
                 'ncbi_taxdmp_macaca': ncbi_taxdmp_macaca,
                 'rhea_chebi_smiles': rhea_chebi_smiles}
