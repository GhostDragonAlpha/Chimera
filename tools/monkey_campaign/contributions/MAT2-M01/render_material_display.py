"""MAT2-M01 display probe: the known teddy object displays its actual regions and
graph relations with stable IDs.

CPU-only structured display (JSON, not pixels): this base revision has no runnable
material solver, so the 'material' motion profile's visual/camera clause is recorded
as pending-runtime, not passed. Numerical display evidence and counts are real.
"""
from __future__ import annotations

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import material_state as ms  # noqa: E402


def main():
    doc = json.loads((HERE / 'teddy_fixture.json').read_text(encoding='utf-8'))
    display = ms.display(doc)
    display['display_honesty'] = {
        'kind': 'structured_records_display',
        'visual_clause': 'PENDING_RUNTIME: no native material solver exists at base '
                         'revision c525b82c; motion-profile camera evidence is deferred '
                         'to runtime-facing cards (M03/M04, MAT-PRESSURE). Not passed here.',
        'numerical_clause': 'PASSED_HERE: validation, ownership, relation distinctness '
                            'and identity stability are checked by test_material_state.py '
                            '(35 named checks) against the committed fixture.',
    }
    out = HERE / 'material_display.json'
    out.write_text(json.dumps(display, indent=1, ensure_ascii=False) + '\n',
                   encoding='utf-8')
    print('object:', display['object_id'], 'revision:', display['revision'])
    print('regions:', display['counts']['region_count'],
          '| shells:', display['counts']['shell_count'])
    print('matter owned once:', display['counts']['matter_count'],
          '| references:', display['counts']['reference_count'])
    print('containment edges:', len(display['relations']['containment']),
          '| contacts:', len(display['relations']['contacts']),
          '| bonds:', len(display['relations']['bonds']))
    print('total mass (counted once):', display['mass_summary']['total_mass_kg'], 'kg')
    print('canonical_sha256:', display['canonical_sha256'])
    print('wrote', out)


if __name__ == '__main__':
    sys.exit(main())
