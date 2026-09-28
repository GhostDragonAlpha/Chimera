"""Build the MAT2-M01 teddy fixture from the pinned base revision.

Extracts the actual membrane regions of the existing teddy prototype from
`ChimeraEngine/native/teddy_membranes.json` at the recorded base revision via
`git show <base>:<path>` (read-only; never modifies the tree) and writes
`teddy_fixture.json` with full provenance. The fixture is committed so tests are
self-contained; P4 re-verifies the blob hash through git when available.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys

BASE = 'c525b82c7c3ce0128565424764293a3c85811ab3'
MEMBRANES_PATH = 'ChimeraEngine/native/teddy_membranes.json'
MATERIALS_PATH = 'ChimeraEngine/native/teddy_materials.json'
HERE = pathlib.Path(__file__).resolve().parent


def git_show(base, path):
    result = subprocess.run(['git', 'show', '%s:%s' % (base, path)],
                            capture_output=True, text=True, check=True,
                            encoding='utf-8')
    return result.stdout


def main():
    raw_membranes = git_show(BASE, MEMBRANES_PATH)
    raw_materials = git_show(BASE, MATERIALS_PATH)
    membranes = json.loads(raw_membranes)
    materials = json.loads(raw_materials)
    names = sorted(membranes['membranes'])
    material_names = sorted(materials)

    fixture = {
        'schema': 'chimera.material_state.v1',
        'revision': 1,
        'object_id': 'teddy-prototype',
        'provenance': {
            'base_revision': BASE,
            'source_blobs': {
                MEMBRANES_PATH: hashlib.sha256(raw_membranes.encode('utf-8')).hexdigest(),
                MATERIALS_PATH: hashlib.sha256(raw_materials.encode('utf-8')).hexdigest(),
            },
            'extraction': 'git show <base>:<path>, read-only; regions reuse the pinned teddy prototype membrane ids',
            'excluded': ['mass values, laws, contacts and bonds are authored at chosen fidelity with explicit provenance strings; no anatomy constant or activation law is inferred'],
        },
        'regions': [],
        'matter': [
            {'id': 'fur_matter', 'mass_kg': 1.25, 'provenance': 'authored fixture mass at chosen fidelity (no measured source); explicit, single-owner'},
            {'id': 'core_matter', 'mass_kg': 0.75, 'provenance': 'authored fixture mass at chosen fidelity (no measured source); explicit, single-owner'},
        ],
        'directions': [
            {'id': 'fur_grain', 'region_id': 'belly', 'axis': [0.0, 0.0, 1.0],
             'history': [{'revision': 1, 'state': 'authored fixture direction (declared, not inferred)'}],
             'frame': 'rest'},
        ],
        'laws': [
            {'id': 'fur_pressure_law', 'kind': 'pressure_deformation',
             'regions': ['belly', 'chest'],
             'parameters': {'model': 'declared_fixture_placeholder', 'stiffness_note': 'values deferred to runtime-facing cards (M03/M04); no number invented here'},
             'provenance': 'declared fixture placeholder law; parameter numbers intentionally absent until a sourced law exists'},
        ],
        'contacts': [],
        'bonds': [],
    }

    roots, nested = [], []
    for name in names:
        row = {
            'id': name,
            'kind': 'shell',
            'parent': None,
            'rest_geometry': {'source': 'teddy_membranes.json membrane region (rest = authored prototype geometry)'},
            'current_geometry': {'source': 'equal to rest at revision 1 (no solver in this qualification)'},
            'matter_claims': [{'matter_id': 'fur_matter', 'role': 'owner' if name == 'belly' else 'reference'},
                              {'matter_id': 'core_matter', 'role': 'owner' if name == 'chest' else 'reference'}],
            'ports': [{'id': 'surface', 'protocol': 'material_contact', 'unit': 'unitless_interface_id'}],
            'sources': [MEMBRANES_PATH],
        }
        fixture['regions'].append(row)
    # Two explicit containment nests (parent = another region), keeping the rest
    # as roots: demonstrates containment without implying any bond.
    nested = [n for n in names if n in ('ankle_left', 'ankle_right')]
    for name in names:
        row = next(r for r in fixture['regions'] if r['id'] == name)
        if name == 'ankle_left':
            row['parent'] = 'belly'
            nested.append(name)
    _ = roots, nested

    # Two explicit contacts and one explicit bond between distinct regions,
    # through their declared ports; nothing here is implied by containment.
    fixture['contacts'] = [
        {'id': 'contact_belly_chest', 'state': 'touching',
         'endpoints': [{'region_id': 'belly', 'port': 'surface'},
                       {'region_id': 'chest', 'port': 'surface'}],
         'interface': 'adjacent prototype shells'},
        {'id': 'contact_core_ground', 'state': 'separated',
         'endpoints': [{'region_id': 'chest', 'port': 'surface'}],
         'interface': 'single-sided declared contact (state separated)'},
    ]
    fixture['bonds'] = [
        {'id': 'bond_belly_chest_surface', 'status': 'planned',
         'endpoints': [{'region_id': 'belly', 'port': 'surface'},
                       {'region_id': 'chest', 'port': 'surface'}],
         'transfers': 'force_moment'},
    ]

    out = HERE / 'teddy_fixture.json'
    out.write_text(json.dumps(fixture, indent=1, ensure_ascii=False) + '\n',
                   encoding='utf-8')
    print('wrote', out)
    print('membrane ids reused:', len(names), names[:8], '...')
    print('material catalog names:', material_names)


if __name__ == '__main__':
    sys.exit(main())
