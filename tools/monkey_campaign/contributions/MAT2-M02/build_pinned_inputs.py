"""Extract the pinned MAT2-M02 inputs at the recorded revision (read-only).

The assigned base lineage (c4650f0a = origin/astra/gait-capture) lacks
tools/science_funnel/ and tools/creature_graph/; the pinned macaque intake and
the admitted graph snapshot live at the recorded revision below. This builder
applies the M01 extraction pattern: `git show <rev>:<path>` out of this attempt
checkout (read-only; no tree is modified), byte-verification of every file
against the download receipt AND the admitted graph asset pins, then a distilled
committed `data/graph_pins.json` (macaque rows only) with the extraction
revision recorded. Refuses loudly on any drift.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]
INTAKE_REVISION = 'eafbc15161ae10ae95b62d07d3f4878aefa34d9d'
DATA_DIR = HERE / 'data'
MACAQUE_DIR = DATA_DIR / 'macaque_arm'
GRAPH_PATH_IN_TREE = 'tools/creature_graph/data/creature_graph.json'
INTAKE_PREFIX = 'tools/science_funnel/data/macaque_arm/'


def require(condition, code):
    if not condition:
        raise ValueError(code)


def git_show(revision, path):
    result = subprocess.run(
        ['git', 'show', '%s:%s' % (revision, path)],
        capture_output=True, check=True, cwd=str(ROOT))
    return result.stdout


def sha256_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    MACAQUE_DIR.mkdir(parents=True, exist_ok=True)
    # 1. download receipt pins the whole intake
    receipt_raw = git_show(INTAKE_REVISION, INTAKE_PREFIX
                           + 'download_receipt.json')
    receipt = json.loads(receipt_raw)
    require(receipt['revision'] == '4fb7dddeec06a0df9525c18f37234a824cb1b5b1'
            and receipt['license'] == 'MIT', 'source_identity')
    extracted = {}
    for entry in receipt['files']:
        raw = git_show(INTAKE_REVISION, INTAKE_PREFIX + entry['path'])
        require(sha256_bytes(raw) == entry['sha256']
                and len(raw) == entry['bytes'],
                'source_pin_drift:' + entry['path'])
        out = MACAQUE_DIR / entry['path']
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(raw)
        extracted[entry['path']] = entry['sha256']
    # MIT license travels with the data
    lic = git_show(INTAKE_REVISION, INTAKE_PREFIX + 'LICENSE')
    (MACAQUE_DIR / 'LICENSE').write_bytes(lic)
    extracted['LICENSE'] = sha256_bytes(lic)
    # 2. graph snapshot: distill the admitted macaque rows
    graph = json.loads(git_show(INTAKE_REVISION, GRAPH_PATH_IN_TREE))
    geom_pins = {}
    for body in ('sternum', 'clavicle', 'scapula', 'humerus', 'ulna',
                 'radius', 'hand'):
        oid = 'geom.macaque_arm.' + body
        obj = graph['objects'][oid]
        asset = obj['physical']['asset']
        require(sha256_bytes((MACAQUE_DIR / asset['path']).read_bytes())
                == asset['sha256'], 'graph_asset_pin_drift:' + oid)
        require(asset['source_units_to_m'] == [0.001, 0.001, 0.001],
                'graph_unit_pin_drift:' + oid)
        geom_pins[body] = {'graph_id': oid, 'asset': asset,
                           'metrics': obj['physical']['metrics'],
                           'anatomical_claim':
                               obj['physical'].get('anatomical_claim')}
    model_obj = graph['objects']['model.anatomy.macaque_arm']['physical']
    body_frames = {}
    for b in model_obj['model']['bodies']:
        ref = graph['objects'].get('ref.macaque_arm.body.' + b['name'])
        world_from_local = (ref or {}).get('spatial', {}).get(
            'world_from_local')
        if b['geometry']:
            require(world_from_local is not None,
                    'missing_world_from_local:' + b['name'])
        body_frames[b['name']] = world_from_local
    pins = {
        'kind': 'mat2_m02_pinned_graph_rows',
        'extraction_revision': INTAKE_REVISION,
        'graph_path_in_tree': GRAPH_PATH_IN_TREE,
        'graph_snapshot_note': 'distilled admitted rows; full snapshot is a '
                               '25 MB object at the extraction revision, '
                               're-derivable via git show',
        'source_receipt': {'revision': receipt['revision'],
                           'license': receipt['license'],
                           'files': extracted},
        'geom_pins': geom_pins,
        'model': model_obj['model'],
        'body_frames': body_frames,
        'scope_limitation': model_obj['model'].get('scope'),
    }
    out = DATA_DIR / 'graph_pins.json'
    out.write_text(json.dumps(pins, indent=1, ensure_ascii=False) + '\n',
                   encoding='utf-8')
    print('extracted %d intake files at %s' % (len(extracted), INTAKE_REVISION))
    print('geom pins verified for:', ', '.join(sorted(geom_pins)))
    print('wrote', out)


if __name__ == '__main__':
    sys.exit(main())
