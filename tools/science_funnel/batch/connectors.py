"""Connector declarations. Artifact pins are resolved at load time from each
data directory's download receipt -- never hardcoded here, never guessed."""
import json
import os

from ..common import require, sha

DATA_ROOT = os.path.join(os.path.dirname(__file__), '..', 'data')


def _pins(data_dir):
    """Map filename -> {sha256, bytes, url} from a data dir's download receipt."""
    receipt_path = os.path.join(DATA_ROOT, data_dir, 'download_receipt.json')
    require(os.path.isfile(receipt_path), 'connector_receipt_missing', data_dir)
    with open(receipt_path, encoding='utf-8') as stream:
        receipt = json.load(stream)
    pins = {}
    for entry in receipt['files']:
        pins[entry['path']] = entry
    return receipt, pins


def _artifacts(data_dir, names, pins):
    out = []
    for name, role in names:
        entry = pins.get(name)
        require(entry is not None, 'connector_pin_missing', data_dir + '/' + name)
        out.append({'id': name, 'path': 'artifacts/' + entry['sha256'],
                    'sha256': entry['sha256'], 'url': entry.get('url', ''), 'role': role})
    return out


_smith_receipt, _smith_pins = _pins('smithsonian')
_cop_receipt, _cop_pins = _pins('copernicus_glo30')
_bp3d_receipt, _bp3d_pins = _pins('bodyparts3d')
_egm_receipt, _egm_pins = _pins('nga_egm08')

CONNECTORS = {
    'smithsonian_voyager': {
        'connector_id': 'smithsonian_voyager',
        'mode': 'admit',
        'data_dir': 'smithsonian',
        'adapter': 'smithsonian_voyager',
        'source': {
            'id': 'smithsonian.usnm15259',
            'release': 'object pages and derivative files snapshot-pinned 2026-09-17',
            'url': 'https://3d.si.edu/object/3d/macaca-sinica-cranium:fb42ecf6-2756-4b6f-bbb0-eb91f31964e5',
            'license': 'CC0 1.0 per object page ("You can copy, modify, and distribute this work '
                       'without contacting the Smithsonian"); document.json embeds a conflicting '
                       'all-rights-reserved string -- recorded on every record, never resolved silently',
            'known_gaps': ['head elements only (cranium + mandible, Macaca sinica USNM 15259)',
                           'photogrammetry surface, not CT', 'no postcranial geometry'],
        },
        'artifacts': _artifacts('smithsonian', [
            ('USNM15259_cranium_document.json', 'data'),
            ('USNM15259_mandible_document.json', 'data'),
            ('USNM15259_cranium_-300_dec-150k-4096-high.glb', 'attachment'),
            ('USNM15259_mandible_-300-150k-4096-high.glb', 'attachment'),
        ], _smith_pins),
        'classes': {'geometry': 'batch.geometry.smithsonian_voyager'},
    },
    'copernicus_glo30': {
        'connector_id': 'copernicus_glo30',
        'mode': 'admit',
        'data_dir': 'copernicus_glo30',
        'adapter': 'copernicus_meta',
        'source': {
            'id': 'copernicus.dem_glo30.n18w066',
            'release': 'GLO-30 Public 2021 release via AWS Open Data (bucket copernicus-dem-30m), '
                       'tile N18 W066 HEAD-verified 2026-09-17',
            'url': 'https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_N18_00_W066_00_DEM/',
            'license': 'Copernicus free licence with attribution (DLR/Airbus/Copernicus notices); '
                       'bucket EULA pinned as artifact',
            'known_gaps': ['DSM (surface), not bare earth', 'ABS vertical accuracy < 4 m LE90',
                           'EOXML verticalDatumCode carries the horizontal code (ESA quirk)'],
        },
        'artifacts': _artifacts('copernicus_glo30', [
            ('Copernicus_DSM_10_N18_00_W066_00.xml', 'data'),
            ('Copernicus_DSM_COG_10_N18_00_W066_00_DEM.tif', 'attachment'),
            ('Copernicus_DSM_COG_10_N18_00_W066_00_WBM.tif', 'attachment'),
            ('Copernicus_eula_F.pdf', 'attachment'),
        ], _cop_pins),
        'classes': {'measurement': 'batch.property.copernicus_tile'},
    },
    'bodyparts3d': {
        'connector_id': 'bodyparts3d',
        'mode': 'admit',
        'data_dir': 'bodyparts3d',
        'adapter': 'bp3d_lists',
        'source': {
            'id': 'bodyparts3d.lists',
            'release': 'archive layout observed 2026-09-15/17 (FMA-based tables, no release '
                       'versioning on the archive)',
            'url': 'https://dbarchive.biosciencedbc.jp/data/bodyparts3d/LATEST/',
            'license': 'CC Attribution 4.0 International; attribution: BodyParts3D, '
                       '(c) The Database Center for Life Science',
            'known_gaps': ['mesh zips not imported (lists only)',
                           'FMA version not pinned by the archive',
                           'isa/partof inclusion pairs pinned as attachments, not reified'],
        },
        'artifacts': _artifacts('bodyparts3d', [
            ('partof_parts_list_e.txt', 'data'),
            ('isa_parts_list_e.txt', 'attachment'),
            ('partof_element_parts.txt', 'attachment'),
            ('isa_element_parts.txt', 'attachment'),
            ('partof_inclusion_relation_list.txt', 'attachment'),
            ('isa_inclusion_relation_list.txt', 'attachment'),
            ('license.html', 'attachment'),
            ('README_e.html', 'attachment'),
        ], _bp3d_pins),
        'constants': {'isa_parts_sha256': _bp3d_pins['isa_parts_list_e.txt']['sha256']},
        'classes': {'entity': 'batch.entity.external'},
    },
    'nga_egm08': {
        'connector_id': 'nga_egm08',
        'mode': 'admit',
        'data_dir': 'nga_egm08',
        'adapter': 'egm08_grid_meta',
        'source': {
            'id': 'nga.egm08_25',
            'release': 'Earth Gravitational Model 2008, 2.5-minute grid, PROJ CDN '
                       'redistribution pinned 2026-09-17',
            'url': 'https://cdn.proj.org/us_nga_egm08_25.tif',
            'license': 'Public domain (NGA model; PROJ-data names free use)',
            'known_gaps': ['2.5-minute grid: geoid slope between nodes is interpolated, '
                           'not measured', 'no uncertainty field in the grid'],
        },
        'artifacts': _artifacts('nga_egm08', [
            ('us_nga_egm08_25.tif', 'data'),
        ], _egm_pins),
        'constants': {'grid_bytes': _egm_pins['us_nga_egm08_25.tif']['bytes']},
        'classes': {'measurement': 'batch.property.measurement'},
    },
}

# Existing science_funnel admissions re-proven by recorded-producer replay.
REPROVE_SOURCES = ['iaea.livechart', 'nist.codata2022', 'jpl.de440',
                   'cantera.gri30.thermo', 'nist.al6061t6']

# Default class mapping for records admitted before class contracts existed.
DEFAULT_CLASSES = {
    'measurement': 'batch.property.measurement',
    'series': 'batch.property.measurement',
    'entity': 'batch.entity.external',
    'geometry': 'batch.entity.external',
    'model': 'batch.entity.external',
    'relation': 'batch.entity.external',
    'unit_definition': 'batch.entity.external',
}

# Lane connectors auto-load: sibling modules connectors_*.py may define
# EXTRA_CONNECTORS = {...} (this lane's convention) or CONNECTORS_LANE = {...}
# (the intake lanes' spelling); both merge by id with hard collision refusal.
import importlib as _importlib
import os as _os
for _name in sorted(n for n in _os.listdir(_os.path.dirname(__file__))
                    if n.startswith('connectors_') and n.endswith('.py')):
    _mod = _importlib.import_module('.' + _name[:-3], __package__)
    _extra = (getattr(_mod, 'EXTRA_CONNECTORS', None) or getattr(_mod, 'CONNECTORS_LANE', None)
              or getattr(_mod, 'CONNECTORS', None))
    for _cid, _conn in (_extra or {}).items():
        require(_cid not in CONNECTORS, 'lane_connector_collision', _cid)
        CONNECTORS[_cid] = _conn


def class_for(connector_id, record_type):
    if connector_id in CONNECTORS:
        return CONNECTORS[connector_id]['classes'].get(record_type)
    return DEFAULT_CLASSES.get(record_type)
