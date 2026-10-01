"""Gait/observation lane funnels (INTAKE-GAIT, 2026-09-17).

Lane adapters register themselves into the shared ADAPTERS dict in place at
import; the shared adapters module itself is never edited by a lane. The
import chain that activates them is batch.connectors' lane-module auto-load
(batch_qualify and the batch tests both go through it).

RULE 0 for this lane (the per-class contracts in the authored store restate
it mechanically):
  STATEMENT -- a wild-primate stride observation is admittable only as a
  species-tagged, substrate-tagged row whose every measured value sits inside
  a declared envelope; a deferred Dryad file is admittable only as a
  digest-pinned identity claim that says it is deferred and why.
  PREDICTION -- all 386 real stride rows admit carrying species + substrate
  tags and pass the class checks; the 2.1 GB video archive admits nothing.
  FALSIFIER -- one corrupted stride row (species, one angle, or substrate)
  quarantines exactly itself; the count identity fetched == admitted +
  quarantined closes with zero silent drops.
"""
import csv
import io

from .adapters import ADAPTERS, rejection
from .common import Refusal, draft, loads, number, require, text

JOINT_ANGLE_COLUMNS = [
    'hipTD', 'kneeTD', 'ankleTD', 'hlTD',
    'hipMID', 'kneeMID', 'ankleMID', 'hlMID',
    'hipLO', 'kneeLO', 'ankleLO', 'hlLO',
    'shoulderTD', 'elbowTD', 'wristTD', 'flTD',
    'shoulderMID', 'elbowMID', 'wristMID', 'flMID',
    'shoulderLO', 'elbowLO', 'wristLO', 'flLO',
]
MEAN_ANGLE_COLUMNS = ['meanElbowAng', 'meanKneeAng', 'meanFLAng', 'meanHLAng']
YIELD_COLUMNS = ['elbowYld', 'kneeYld']
EXCURSION_COLUMNS = ['shoulderExcur', 'hipExcur', 'flExcur', 'hlExcur']

ANGLE_GROUPS = [
    ('joint_angles_deg', JOINT_ANGLE_COLUMNS, 0.0, 360.0),
    ('mean_angles_deg', MEAN_ANGLE_COLUMNS, 0.0, 360.0),
    ('yields_deg', YIELD_COLUMNS, -180.0, 180.0),
    ('excursions_deg', EXCURSION_COLUMNS, 0.0, 360.0),
]

SEX_VOCABULARY = ('m', 'f', 'unknown')
AGE_VOCABULARY = ('adult', 'mom', 'juvenile', 'unknown')


def _measured(raw_value, low, high, field):
    """One cell: NA/empty -> (None, not counted); otherwise a finite number
    inside the declared envelope or the row refuses."""
    if raw_value in ('', 'NA'):
        return None
    value = number(raw_value)
    require(low <= value <= high, 'value_outside_envelope', field + '=' + raw_value)
    return value


def _required_text(row, column):
    value = row.get(column, '')
    require(value and value != 'NA', 'missing_column_value', column)
    return value


def janisch_strides(raw, manifest, path):
    """Janisch et al. 2024 new_mergedkinematicdata.csv -> one stride record per row.

    One record per stride row (387 fetched: 386 real strides + 1 all-NA row
    that must quarantine, not admit). Every record carries the species tag
    (vocabulary-checked), the substrate tags (diameter and orientation are
    required measured numbers; height/compliance/tree species are carried as
    None where the field study did not measure them), sex/age tags, body mass,
    and every measured joint angle / mean / yield / excursion under a declared
    envelope. Derived analysis columns (phylogenetic eigenvectors PE_1..PE_13,
    the orientation components horizVsang/incVsdec, subs_diam_std) are omitted:
    they are recomputable from the pinned consensus tree and the source R
    code, and re-derivation is a later membrane, not an admission.
    """
    constants = manifest.get('constants', {})
    vocabulary = constants.get('species_vocabulary')
    require(vocabulary, 'missing_text', 'constants.species_vocabulary')
    expected_rows = constants.get('expected_stride_rows')

    reader = csv.DictReader(io.StringIO(raw.decode('utf-8-sig'), newline=''))
    fields = reader.fieldnames
    require(fields and len(set(fields)) == len(fields), 'csv_bad_header')
    required = (['Species', 'Video', 'stridenumber', 'subs_diam', 'subs_ori',
                 'Mass', 'sex', 'age', 'subs_hght', 'subs_compl', 'tree_species']
                + JOINT_ANGLE_COLUMNS + MEAN_ANGLE_COLUMNS
                + YIELD_COLUMNS + EXCURSION_COLUMNS)
    missing = [column for column in required if column not in fields]
    require(not missing, 'csv_bad_header', 'missing columns: ' + ','.join(missing))
    rows = list(reader)
    if expected_rows:
        require(len(rows) == expected_rows, 'stride_row_count_changed',
                str(len(rows)) + ' rows != pinned ' + str(expected_rows))

    out = []
    for index, row in enumerate(rows, 2):
        try:
            species = _required_text(row, 'Species')
            require(species in vocabulary, 'species_outside_vocabulary', species)
            video = _required_text(row, 'Video')
            stride = number(row['stridenumber'])
            require(stride == int(stride) and 1 <= int(stride) <= 99,
                    'stride_number_out_of_range', row['stridenumber'])
            diameter = _measured(row['subs_diam'], 0.0, 2.0, 'subs_diam')
            orientation = _measured(row['subs_ori'], -90.0, 90.0, 'subs_ori')
            require(diameter is not None and orientation is not None,
                    'substrate_tags_missing', 'row ' + str(index))
            mass = _measured(row['Mass'], 0.1, 100.0, 'Mass')
            require(mass is not None, 'body_mass_missing', 'row ' + str(index))
            sex = _required_text(row, 'sex')
            require(sex in SEX_VOCABULARY, 'sex_outside_vocabulary', sex)
            age = _required_text(row, 'age')
            require(age in AGE_VOCABULARY, 'age_outside_vocabulary', age)

            substrate = {'diameter_m': diameter, 'orientation_deg': orientation,
                         'height_m': _measured(row['subs_hght'], 0.0, 100.0, 'subs_hght'),
                         'compliance': _measured(row['subs_compl'], 0.0, 1000.0, 'subs_compl'),
                         'tree_species': (None if row['tree_species'] in ('', 'NA')
                                          else row['tree_species'])}
            measured = 0
            payload = {'species': species, 'video': video, 'stride_number': int(stride),
                       'substrate': substrate, 'sex': sex, 'age': age,
                       'body_mass_kg': mass}
            for key, columns, low, high in ANGLE_GROUPS:
                values = {}
                for column in columns:
                    value = _measured(row[column], low, high, column)
                    if value is not None:
                        values[column] = value
                        measured += 1
                payload[key] = values
            require(measured >= 1, 'no_measured_values', 'row ' + str(index))
            payload['n_measured_values'] = measured
            record = draft('janisch:' + video + ':stride' + str(int(stride)), 'entity',
                           payload, label=species + ' ' + video + ' S' + str(int(stride))
                           + ' wild primate stride',
                           unknowns=['phylogenetic_eigenvectors_PE_1_13_omitted_'
                                     'derivable_from_pinned_consensus_tree',
                                     'derived_orientation_components_omitted',
                                     'substrate_height_compliance_absent_where_unmeasured',
                                     'angle_convention_defined_by_source_R_code_'
                                     'not_machine_pinned'])
            record['class_contract'] = {'class_id': 'batch.observation.janisch_stride',
                                        'version': 1}
            out.append(record)
        except Refusal as exc:
            out.append(rejection('csv_record:' + str(index), exc))
    require(any('refusal' not in row for row in out), 'empty_capture', 'all rows refused')
    return out


def dryad_files_meta(raw, manifest, path):
    """Dryad API v2 version file list -> per-file identity records, deferred.

    The records admit WHAT the files are (path, byte size, Dryad-declared
    sha-256 digest, API file id) verified against the pinned dataset-record
    attachment, plus the deferral cause with its first-hand probe evidence.
    The file BYTES are not claimed: the API download endpoint answers 401
    "must have current bearer token", the website stream URLs sit behind an
    Anubis bot challenge, no Dryad account is registrable from this agent and
    browser download is unavailable to it. When a token-enabled lane later
    downloads the files, these records are the byte-identity pins to match.
    """
    constants = manifest.get('constants', {})
    dataset_pin = constants.get('dataset_sha256')
    require(dataset_pin, 'missing_text', 'constants.dataset_sha256')
    deferral = constants.get('deferral')
    require(isinstance(deferral, dict) and deferral.get('cause'),
            'missing_text', 'constants.deferral.cause')

    dataset = loads(path.parent.joinpath(dataset_pin).read_bytes())
    doi = text(dataset.get('identifier'), 'dataset.identifier')
    title = text(dataset.get('title'), 'dataset.title')
    license_url = text(dataset.get('license'), 'dataset.license')
    version_href = ((dataset.get('_links') or {}).get('stash:version') or {}).get('href', '')
    version_id = version_href.rsplit('/', 1)[-1]
    require(version_id.isdigit(), 'dryad_version_id_missing', version_href)

    listing = loads(raw)
    entries = ((listing.get('_embedded') or {}).get('stash:files') or [])
    require(entries, 'empty_capture', 'no files in version listing')
    suffix = doi.rsplit('.', 1)[-1]
    exclude = set(constants.get('exclude_paths', []))
    out = []
    for entry in entries:
        file_path = text(entry.get('path'), 'file.path')
        size = number(entry.get('size'))
        digest = text(entry.get('digest'), 'file.digest')
        require(entry.get('digestType') == 'sha-256', 'digest_type_unsupported',
                str(entry.get('digestType')))
        file_id = (((entry.get('_links') or {}).get('self') or {}).get('href', '')
                   .rsplit('/', 1)[-1])
        require(file_id.isdigit(), 'dryad_file_id_missing', file_path)
        status = 'excluded_by_policy' if file_path in exclude else 'deferred'
        payload = {'dataset_doi': doi, 'dataset_title': title, 'license': license_url,
                   'dryad_version_id': version_id, 'file_path': file_path,
                   'file_id': file_id, 'size_bytes': size,
                   'sha256_digest': digest, 'digest_type': 'sha-256',
                   'mime_type': entry.get('mimeType', ''), 'status': status,
                   'download_url': 'https://datadryad.org/api/v2/files/'
                                   + file_id + '/download',
                   **deferral}
        record = draft('dryad:' + suffix + ':' + file_path, 'entity', payload,
                       label=title + ' / ' + file_path,
                       unknowns=['file_bytes_not_downloaded_deferred',
                                 'dryad_digest_is_api_claim_unverified_by_download'])
        record['class_contract'] = {'class_id': 'batch.deferred.dryad_file', 'version': 1}
        out.append(record)
    require(any(row['payload']['status'] == 'deferred' for row in out),
            'no_deferred_files', 'every file excluded?')
    return out


GAIT_ADAPTERS = {'janisch_strides': janisch_strides,
                 'dryad_files_meta': dryad_files_meta}
ADAPTERS.update(GAIT_ADAPTERS)
