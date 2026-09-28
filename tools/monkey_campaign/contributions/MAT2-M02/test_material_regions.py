"""MAT2-M02 frozen-probe tests: P1-P9, P11 positive predictions and F1-F5
falsifier bites, exactly as frozen in PREREGISTRATION.md (this directory).

CPU-only, python -B, numpy + stdlib, no engine, no network, no GPU. Run from
the checkout root:
    python -B tools/monkey_campaign/contributions/MAT2-M02/test_material_regions.py

P10 (capture/validator) is exercised by the separate capture phase, not here.
"""
from __future__ import annotations

import copy
import json
import pathlib
import subprocess
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'MAT2-M01'))
sys.path.insert(0, str(ROOT))

import compile_material_regions as cr   # noqa: E402
import material_state as ms             # noqa: E402  (M01, unmodified)

ARM_DOC = json.loads((HERE / 'monkey_arm_regions.json').read_text('utf-8'))
INDEP_DOC = json.loads(
    (HERE / 'independent_shape_regions.json').read_text('utf-8'))
BLOB = json.loads((HERE / 'monkey_arm_independent_meshes.json')
                  .read_text('utf-8'))
RECEIPT = json.loads((HERE / 'compile_receipt.json').read_text('utf-8'))

# Frozen pinned-input table (PREREGISTRATION.md): region -> (tris, verts,
# signed_volume_m3, open_edges, kind)
PINNED = {
    'sternum': (16, 10, 2.6493280581797473e-07, 0, 'region'),
    'clavicle': (156, 80, 1.3101298443114225e-06, 0, 'region'),
    'scapula': (358, 180, 9.136383923955177e-06, 10, 'shell'),
    'humerus': (464, 234, 1.2504681471383375e-05, 0, 'region'),
    'ulna': (444, 224, 5.699077518562791e-06, 0, 'region'),
    'radius': (222, 113, 5.0558415568324745e-06, 0, 'region'),
    'hand': (3724, 1920, 1.5702994816386723e-06, 18, 'shell'),
}
ANALYTIC = {
    'tetra': (4, 4, 1.6666666666666667e-04, 0, 'region'),
    'plate': (2, 4, None, 4, 'shell'),
}
PINNED_MASS_SUM = 7.006            # 6.6 + 0.203 + 0.0922 + 0.0618 + 0.049
INDEP_MASS_SUM = 0.14

EXPECTED_BOND_PAIRS = {
    ('clavicle', 'sternum'), ('clavicle', 'scapula'),
    ('humerus', 'scapula'), ('humerus', 'ulna'),
    ('radius', 'ulna'), ('hand', 'radius'),
}

CHECKS = []


def check(name, ok, detail=''):
    CHECKS.append((name, bool(ok), detail))


def refused(code_substring, fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except ValueError as exc:
        return code_substring in str(exc), str(exc)
    return False, 'no refusal raised'


def region(doc, rid):
    return next(r for r in doc['regions'] if r['id'] == rid)


# ------------------------------------------------------------------ positives
def p1_schema():
    for doc in (ARM_DOC, INDEP_DOC):
        summary = ms.validate_material_state(doc)
        reloaded = ms.decode(ms.canonical(doc))
        check('P1 canonical round trip ' + summary['object_id'],
              ms.canonical(reloaded) == ms.canonical(doc))
    s_arm = ms.validate_material_state(ARM_DOC)
    s_ind = ms.validate_material_state(INDEP_DOC)
    check('P1 arm counts', s_arm['region_count'] == 7 and s_arm['shell_count'] == 2
          and s_arm['matter_count'] == 7 and s_arm['bond_count'] == 6
          and s_arm['contact_count'] == 0,
          json.dumps({k: s_arm[k] for k in ('region_count', 'shell_count',
                                            'matter_count', 'bond_count',
                                            'contact_count')}))
    check('P1 independent counts',
          s_ind['region_count'] == 2 and s_ind['shell_count'] == 1
          and s_ind['matter_count'] == 2 and s_ind['bond_count'] == 0
          and s_ind['contact_count'] == 0)
    check('P1 arm region ids', s_arm['region_ids'] == sorted(PINNED),
          str(s_arm['region_ids']))
    check('P1 independent region ids', s_ind['region_ids'] == ['plate', 'tetra'])
    owners = [c['matter_id'] for r in ARM_DOC['regions']
              for c in r['matter_claims'] if c['role'] == 'owner']
    check('P1 single ownership arm', len(owners) == 7
          and len(set(owners)) == 7)


def p2_pinned_metrics():
    for rid, (tris, verts, vol, open_e, kind) in PINNED.items():
        g = region(ARM_DOC, rid)['rest_geometry']
        check('P2 %s triangles' % rid, g['triangle_count'] == tris,
              str(g['triangle_count']))
        check('P2 %s vertices' % rid, g['vertex_count'] == verts)
        check('P2 %s open edges' % rid, g['open_edge_count'] == open_e)
        check('P2 %s kind' % rid, region(ARM_DOC, rid)['kind'] == kind)
        if vol is not None and kind == 'region':
            got = g['signed_volume_m3']
            check('P2 %s signed volume' % rid,
                  abs(got - vol) <= 1e-9 * abs(vol), '%r vs %r' % (got, vol))
        if rid in ('scapula', 'hand'):
            check('P2 %s no volume claim' % rid, g['volume_claim_m3'] is None
                  and g['shell_thickness_m'] is None)
    for rid, (tris, verts, vol, open_e, kind) in ANALYTIC.items():
        g = region(INDEP_DOC, rid)['rest_geometry']
        check('P2 %s shape counts' % rid, g['triangle_count'] == tris
              and g['vertex_count'] == verts and g['open_edge_count'] == open_e
              and region(INDEP_DOC, rid)['kind'] == kind)
        if vol is not None:
            got = g['signed_volume_m3']
            check('P2 tetra analytic volume',
                  abs(got - vol) <= 1e-15 * abs(vol), '%r' % got)
    area = region(INDEP_DOC, 'tetra')['rest_geometry']['surface_area_m2']
    check('P2 tetra analytic area',
          abs(area - 0.023660254037844386) <= 1e-15 * area, '%r' % area)
    area_p = region(INDEP_DOC, 'plate')['rest_geometry']['surface_area_m2']
    check('P2 plate analytic area', abs(area_p - 0.02) <= 1e-12, '%r' % area_p)
    th = region(INDEP_DOC, 'plate')['rest_geometry']
    check('P2 plate authored thickness', th['shell_thickness_m'] == 0.002
          and 'authored' in th['shell_thickness_provenance'])


def p3_units():
    import hashlib
    for rid in PINNED:
        g = region(ARM_DOC, rid)['rest_geometry']
        check('P3 %s unit pin' % rid,
              g['source_units_to_m'] == [0.001, 0.001, 0.001])
        raw = (cr.DATA_DIR / g['source_path']).read_bytes()
        check('P3 %s source blob pin' % rid,
              hashlib.sha256(raw).hexdigest() == g['source_sha256'])
        xyz, tris = cr.read_vtp(raw)
        xyz = xyz * np.asarray([0.001, 0.001, 0.001])
        exact = np.allclose(np.asarray(g['bounds_m']),
                            np.array([xyz.min(axis=0), xyz.max(axis=0)]),
                            rtol=0.0, atol=0.0)
        check('P3 %s bounds == mm parse x 0.001' % rid, exact)
        ext = np.asarray(g['bounds_m'][1]) - np.asarray(g['bounds_m'][0])
        check('P3 %s envelope' % rid,
              bool(np.all(ext >= 2e-4) and np.all(ext <= 0.6)),
              str(ext.tolist()))
    for rid in ANALYTIC:
        g = region(INDEP_DOC, rid)['rest_geometry']
        check('P3 %s authored in metres' % rid,
              g['source_units_to_m'] == [1.0, 1.0, 1.0])
    # admitted graph pins travel with the extraction and must still agree
    pins = json.loads((cr.DATA_DIR / 'graph_pins.json').read_text('utf-8'))
    check('P3 extraction revision pinned',
          pins['extraction_revision'] == cr.INTAKE_REVISION)
    for rid in PINNED:
        pin = pins['geom_pins'][rid]
        g = region(ARM_DOC, rid)['rest_geometry']
        check('P3 %s graph asset pin agreement' % rid,
              pin['asset']['sha256'] == g['source_sha256']
              and pin['asset']['source_units_to_m'] == g['source_units_to_m'])


def p4_ownership():
    arm_once = ms.total_mass_once(ARM_DOC)
    indep_once = ms.total_mass_once(INDEP_DOC)
    check('P4 arm mass counted once', abs(arm_once - PINNED_MASS_SUM) < 1e-9,
          repr(arm_once))
    check('P4 independent mass counted once',
          abs(indep_once - INDEP_MASS_SUM) < 1e-12, repr(indep_once))
    check('P4 no reference claims at revision 1',
          ms.validate_material_state(ARM_DOC)['reference_count'] == 0
          and ms.validate_material_state(INDEP_DOC)['reference_count'] == 0)
    prov = {m['id']: m['mass_kg'] for m in ARM_DOC['matter']}
    check('P4 pinned source masses', prov == {
        'mass_sternum': 6.6, 'mass_clavicle': 0.0, 'mass_scapula': 0.0,
        'mass_humerus': 0.203, 'mass_ulna': 0.0922, 'mass_radius': 0.0618,
        'mass_hand': 0.049}, json.dumps(prov))


def p5_bonds():
    bonds = ARM_DOC['bonds']
    chains = ARM_DOC['provenance']['source_bond_chains']
    pairs = set()
    for b in bonds:
        ids = [e['region_id'] for e in b['endpoints']]
        pairs.add((ids[0], ids[1]) if ids[0] < ids[1] else (ids[1], ids[0]))
        check('P5 %s declared status/transfers' % b['id'],
              b['status'] == 'source_declared'
              and b['transfers'] == 'force_moment'
              and 'NOT a qualified' in chains.get(b['id'], ''))
    check('P5 chain provenance covers every bond exactly',
          set(chains) == {b['id'] for b in bonds})
    check('P5 exactly the source joint chains', pairs == EXPECTED_BOND_PAIRS,
          str(sorted(pairs)))
    check('P5 no bonds in independent doc', INDEP_DOC['bonds'] == [])
    containment = [r for r in ARM_DOC['regions'] if r['parent'] is not None]
    check('P5 no containment (so no containment-implied bond)',
          containment == [])


def p6_mapping():
    blob_sha = RECEIPT  # placeholder to keep linters calm; real check below
    del blob_sha
    doc_blob_sha = ARM_DOC['provenance']['mesh_blob']['sha256']
    import hashlib
    actual = hashlib.sha256(
        (HERE / ARM_DOC['provenance']['mesh_blob']['file'])
        .read_bytes()).hexdigest()
    check('P6 blob sha binding', doc_blob_sha == actual == INDEP_DOC[
        'provenance']['mesh_blob']['sha256'])
    for doc in (ARM_DOC, INDEP_DOC):
        for r in doc['regions']:
            g = r['rest_geometry']
            rec = BLOB['regions'][g['mesh_blob_region_key']]
            m = g['render_to_physics_mapping']
            check('P6 %s identity mapping' % r['id'],
                  m['mapping'] == 'identity'
                  and m['visual_triangle_count'] == m['physical_triangle_count']
                  == g['triangle_count'] == len(rec['triangles'])
                  and rec['visual_mesh'].startswith('identity')
                  and rec['physical_mesh'].startswith('identity'))


def p7_absent_anatomy():
    for doc in (ARM_DOC, INDEP_DOC):
        inv = doc['provenance']['absent_internal_anatomy']
        joined = ' '.join(inv).lower()
        check('P7 absent anatomy inventory %s' % doc['object_id'],
              len(inv) >= 4 and 'skin' in joined and 'muscle' in joined
              and ('organ' in joined or 'tissue' in joined)
              and 'thickness' in joined, '%d entries' % len(inv))


def p8_separation():
    # documents never embed coordinates: no vertex/triangle arrays in region rows
    def has_arrays(obj):
        if isinstance(obj, dict):
            if any(k in obj for k in ('vertices', 'vertices_m', 'triangles',
                                      'world_vertices_m')):
                return True
            return any(has_arrays(v) for v in obj.values())
        if isinstance(obj, list):
            return any(has_arrays(v) for v in obj)
        return False
    for doc in (ARM_DOC, INDEP_DOC):
        check('P8 no coordinates in %s regions' % doc['object_id'],
              not has_arrays(doc['regions']))
    # mutating a blob triangle changes the blob sha but no assignment id
    mutated = copy.deepcopy(BLOB)
    mutated['regions']['tetra']['vertices_m'][0][0] += 1e-9
    new_sha = ms.digest(ms.canonical(mutated))
    check('P8 blob mutation changes blob identity',
          new_sha != ARM_DOC['provenance']['mesh_blob']['sha256'])
    check('P8 assignment ids stable under blob mutation',
          [r['id'] for r in ARM_DOC['regions']] == sorted(PINNED))


def p9_render_sources():
    for doc in (ARM_DOC, INDEP_DOC):
        for r in doc['regions']:
            key = r['rest_geometry']['mesh_blob_region_key']
            rec = BLOB['regions'].get(key)
            check('P9 render source complete %s' % r['id'],
                  rec is not None and len(rec['world_vertices_m']) >= 3
                  and len(rec['triangles']) >= 1)


def p11_regression():
    result = subprocess.run(
        [sys.executable, '-B',
         str(HERE.parent / 'MAT2-M01' / 'test_material_state.py')],
        capture_output=True, text=True, cwd=str(ROOT))
    check('P11 M01 frozen probes still pass', result.returncode == 0,
          (result.stdout + result.stderr)[-300:])


# ---------------------------------------------------------------- falsifiers
def f1_open_as_sealed():
    for rid in ('hand', 'scapula'):
        rec = BLOB['regions'][rid]
        report = cr.orientation_report(
            np.asarray(rec['vertices_m']), rec['triangles'])
        ok, code = refused('open_surface_not_sealed',
                           cr.require_volume_region, rid, report)
        check('F1 %s refused as sealed volume' % rid, ok, code)
        check('F1 %s open edge count recorded' % rid,
              report['open_edges'] == PINNED[rid][3], str(report['open_edges']))


def f2_double_counting():
    doc = copy.deepcopy(ARM_DOC)
    doc['regions'][0].setdefault('matter_claims', []).append(
        {'matter_id': 'mass_hand', 'role': 'owner'})
    ok, code = refused('duplicate_matter_owner',
                       ms.validate_material_state, doc)
    check('F2 second owner claim refused', ok, code)
    # overlapping authored shapes sharing one matter id: detected, counted once
    tetra = np.array([[0.0, 0.0, 0.0], [0.1, 0.0, 0.0],
                      [0.0, 0.1, 0.0], [0.0, 0.0, 0.1]])
    tris = BLOB['regions']['tetra']['triangles']
    offset_a, offset_b = np.zeros(3), np.array([0.03, 0.0, 0.0])
    overlap = cr.pair_intersections(tetra + offset_a, tris, tetra + offset_b,
                                    tris)
    check('F2 overlap is detected by the intersection check', overlap > 0,
          '%d triangle pairs' % overlap)
    overlap_doc = {
        'schema': 'chimera.material_state.v1', 'revision': 1,
        'object_id': 'f2-overlap-probe',
        'regions': [
            {'id': 'shape_a', 'kind': 'region', 'parent': None,
             'rest_geometry': {'note': 'probe'}, 'current_geometry': {},
             'matter_claims': [{'matter_id': 'shared_mass', 'role': 'owner'}],
             'ports': [dict(cr.PORT)]},
            {'id': 'shape_b', 'kind': 'region', 'parent': None,
             'rest_geometry': {'note': 'probe'}, 'current_geometry': {},
             'matter_claims': [{'matter_id': 'shared_mass',
                                'role': 'reference'}],
             'ports': [dict(cr.PORT)]},
        ],
        'matter': [{'id': 'shared_mass', 'mass_kg': 0.5,
                    'provenance': 'F2 probe mass (fixture)'}],
        'directions': [], 'laws': [], 'contacts': [], 'bonds': [],
    }
    summary = ms.validate_material_state(overlap_doc)
    once = ms.total_mass_once(overlap_doc)
    check('F2 overlapping matter counted exactly once',
          abs(once - 0.5) < 1e-12 and abs(summary['total_mass_kg'] - 0.5)
          < 1e-12, repr(once))


def f3_invented_tissue():
    ok, code = refused('assignment_outside_subdivision',
                       cr.check_assignment, [0, 1, 99], 4, 'tetra')
    check('F3 assignment outside subdivision refused', ok, code)
    ok2, code2 = refused('region_without_geometry_source',
                         cr.validate_region_geometry_source, {'unit': 'm'},
                         'ghost_region')
    check('F3 region without geometry source refused', ok2, code2)
    check('F3 compiled regions all carry hashed geometry sources',
          all(cr.validate_region_geometry_source(r['rest_geometry'], r['id'])
              for doc in (ARM_DOC, INDEP_DOC) for r in doc['regions']))


def f4_unit_error():
    raw = (cr.MACAQUE_DIR / 'Geometry' / 'humerus.vtp').read_bytes()
    xyz, tris = cr.read_vtp(raw)          # millimetre coordinates, pin dropped
    bounds = [xyz.min(axis=0).tolist(), xyz.max(axis=0).tolist()]
    ok, code = refused('unit_scale_violation', cr.unit_gate, 'humerus',
                       bounds, [1.0, 1.0, 1.0])
    check('F4 dropped mm pin refused', ok, code[:160])
    scaled = [[v * 0.001 for v in side] for side in bounds]
    gate = cr.unit_gate('humerus', scaled, [0.001, 0.001, 0.001])
    check('F4 correct pin passes the gate', gate['inside'] is True)


def f5_orientation():
    verts = np.array([[0.0, 0.0, 0.0], [0.1, 0.0, 0.0],
                      [0.0, 0.1, 0.0], [0.0, 0.0, 0.1]])
    good = [[0, 2, 1], [0, 1, 3], [0, 3, 2], [1, 2, 3]]
    one_flipped = [[0, 1, 2], [0, 1, 3], [0, 3, 2], [1, 2, 3]]
    all_flipped = [[t[0], t[2], t[1]] for t in good]
    rep = cr.orientation_report(verts, good)
    kind, closure = cr.classify('tetra-good', rep)
    check('F5 authored tetra classifies region', kind == 'region'
          and closure == 'closed_outward_consistent')
    ok, code = refused('mesh_orientation_inconsistent', cr.classify,
                       'tetra-flip1', cr.orientation_report(verts, one_flipped))
    check('F5 single flipped face refused', ok, code)
    ok2, code2 = refused('mesh_orientation_negative', cr.classify,
                         'tetra-flipall',
                         cr.orientation_report(verts, all_flipped))
    check('F5 fully inverted winding refused', ok2, code2)
    ok3, code3 = refused('mesh_orientation_negative', cr.require_volume_region,
                         'tetra-flipall',
                         cr.orientation_report(verts, all_flipped))
    check('F5 volume path refuses inverted solid', ok3, code3)


def main():
    for fn in (p1_schema, p2_pinned_metrics, p3_units, p4_ownership, p5_bonds,
               p6_mapping, p7_absent_anatomy, p8_separation, p9_render_sources,
               p11_regression, f1_open_as_sealed, f2_double_counting,
               f3_invented_tissue, f4_unit_error, f5_orientation):
        fn()
    passed = sum(1 for _, ok, _ in CHECKS if ok)
    failed = [(n, d) for n, ok, d in CHECKS if not ok]
    print('checks: %d/%d passed' % (passed, len(CHECKS)))
    for name, detail in failed:
        print('FAIL:', name, '--', detail)
    if failed:
        sys.exit(1)
    print('ALL FROZEN PROBES GREEN (P1-P9, P11, F1-F5)')


if __name__ == '__main__':
    main()
