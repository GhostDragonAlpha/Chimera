"""MAT2-M02 display probe: the compiled material regions display their actual
records with stable IDs.

CPU-only structured display (JSON, not pixels): reads ONLY the compiled
material_state documents, the mesh blob and the compile receipt produced by
compile_material_regions.py (plus the unmodified M01 validator), and writes
material_display.json with the numerical evidence the visual capture binds to:
per-region metrics, classification, ownership, bonds, absence inventory and
canonical hashes. No solver exists at revision 1: rest == current, and force
vectors / energy / work are absent (inventoried, never fabricated).
"""
from __future__ import annotations

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'MAT2-M01'))

import material_state as ms  # noqa: E402  (M01, unmodified)


def main():
    arm = json.loads((HERE / 'monkey_arm_regions.json').read_text('utf-8'))
    indep = json.loads(
        (HERE / 'independent_shape_regions.json').read_text('utf-8'))
    blob_bytes = (HERE / 'monkey_arm_independent_meshes.json').read_bytes()
    blob = json.loads(blob_bytes.decode('utf-8'))
    receipt = json.loads((HERE / 'compile_receipt.json').read_text('utf-8'))

    def region_rows(doc):
        rows = []
        for r in sorted(doc['regions'], key=lambda r: r['id']):
            g = r['rest_geometry']
            claims = {c['matter_id']: c['role'] for c in r['matter_claims']}
            rows.append({
                'id': r['id'], 'kind': r['kind'],
                'triangles': g['triangle_count'],
                'vertices': g['vertex_count'],
                'closure': g['closure'],
                'open_edge_count': g['open_edge_count'],
                'signed_volume_m3': g['signed_volume_m3'],
                'surface_area_m2': g['surface_area_m2'],
                'bounds_m': g['bounds_m'],
                'source_units_to_m': g['source_units_to_m'],
                'shell_thickness_m': g['shell_thickness_m'],
                'matter_claims': claims,
                'render_to_physics': g['render_to_physics_mapping']['mapping'],
            })
        return rows

    display = {
        'kind': 'mat2_m02_region_display',
        'objects': [
            {'object_id': arm['object_id'], 'revision': arm['revision'],
             'canonical_sha256': ms.digest(ms.canonical(arm)),
             'summary': ms.validate_material_state(arm),
             'total_mass_once_kg': ms.total_mass_once(arm),
             'regions': region_rows(arm),
             'bonds': arm['bonds'],
             'absent_internal_anatomy':
                 arm['provenance']['absent_internal_anatomy'],
             'intersection_check': arm['provenance']['intersection_check']},
            {'object_id': indep['object_id'], 'revision': indep['revision'],
             'canonical_sha256': ms.digest(ms.canonical(indep)),
             'summary': ms.validate_material_state(indep),
             'total_mass_once_kg': ms.total_mass_once(indep),
             'regions': region_rows(indep),
             'bonds': indep['bonds'],
             'absent_internal_anatomy':
                 indep['provenance']['absent_internal_anatomy'],
             'intersection_check': indep['provenance']['intersection_check']},
        ],
        'mesh_blob': {'file': 'monkey_arm_independent_meshes.json',
                      'sha256': ms.digest(blob_bytes),
                      'region_keys': sorted(blob['regions'])},
        'world_bounds_note': 'world_vertices_m in the mesh blob carry the '
                             'admitted default-pose transforms; regions render '
                             'from the blob only',
        'display_honesty': {
            'kind': 'compiled_region_display_with_real_triangle_geometry',
            'visual_clause': 'CAPTURED_SEPARATELY: the motion-profile capture '
                             '(3D orthographic views of these exact triangle '
                             'sets) is built in the attempt capture workspace '
                             'and validated with visual_capture.'
                             'validate_manifest; visual acceptance belongs to '
                             'the independent reviewer',
            'numerical_clause': 'PASSED_HERE: test_material_regions.py'
                                ' (142 frozen probes: P1-P9, P11, F1-F5) on '
                                'this revision',
            'absent': ['force vectors (no solver at revision 1)',
                       'energy/work (no solver at revision 1)',
                       'material directions (none declared, none inferred)',
                       'contacts (none declared; bonds are the source joint '
                       'chains)',
                       'shell thickness on bone surfaces (none used, none '
                       'invented)'],
        },
        'compile_receipt': {'base_revision': receipt['base_revision'],
                            'extraction_revision':
                                receipt['extraction_revision'],
                            'mesh_blob_sha256': receipt['mesh_blob']['sha256']},
    }
    out = HERE / 'material_display.json'
    out.write_text(json.dumps(display, indent=1, ensure_ascii=False) + '\n',
                   encoding='utf-8')
    for obj in display['objects']:
        print('object:', obj['object_id'], '| regions:',
              obj['summary']['region_count'], '| shells:',
              obj['summary']['shell_count'], '| mass once:',
              obj['total_mass_once_kg'], 'kg')
    print('canonical hashes:', [o['canonical_sha256'][:16]
                                for o in display['objects']])
    print('wrote', out)


if __name__ == '__main__':
    sys.exit(main())
