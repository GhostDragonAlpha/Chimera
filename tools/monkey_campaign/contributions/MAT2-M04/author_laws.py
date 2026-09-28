"""MAT2-M04 law authoring: emit the passive-law documents from pinned inputs.

Loads the pinned MAT2-M02 documents (canonical sha256 frozen in
PREREGISTRATION.md), refuses `input_pin_drift` on any mismatch, and emits:

- arm_rigid_laws.json            (chimera.passive_law.v1): all seven arm
  regions -> rigid; no gauge (rigid takes none); no tissue invented.
- independent_shape_laws.json    (chimera.passive_law.v1): tetra -> the
  compliant_maxwell gauge G-TETRA and the fiber-reinforced variants
  (directions 0/45/90 deg about world Z); plate -> fiber_reinforced with
  the two-triangle area-scaled interface.
- independent_shape_directions.json: a material_state.v1 document copy of the
  independent shape with THREE M01 direction rows added (validating through
  the UNMODIFIED M01 validator; law rows deliberately untouched because M01's
  law vocabulary is closed at 'pressure_deformation').
- passive_law_display.json: structured numerical display the capture binds to.

The tetra gauge geometry is DERIVED from the pinned rest geometry (X-leg
0.100 m; face area 5.0e-3 m^2 computed from the mesh blob vertices and
cross-checked against the analytic 0.5*0.1*0.1). Deterministic, stdlib-only.
"""
from __future__ import annotations

import hashlib
import json
import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
M02 = HERE.parent / 'MAT2-M02'
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(M02.parent / 'MAT2-M01'))

import material_state as ms  # noqa: E402  (M01, unmodified)
import passive_law as pl  # noqa: E402

# Frozen input pins (PREREGISTRATION.md).
PIN_ARM_CANONICAL = '51767d1fd33c4002041a31764158dbd75ded27b4bec4c1ecb63453d87cfb316a'
PIN_INDEP_CANONICAL = '23995548570aaaac41fccfe9fb0e6cdbee1f7a3f25b151989ce4289be463ceed'
PIN_BLOB_SHA256 = '51d8231e0d1eacd7f0d4b558699f011e35ff765f5d0e07ef5889ded27216a834'

ARM_REGIONS = ('sternum', 'clavicle', 'scapula', 'humerus', 'ulna',
               'radius', 'hand')
E_PA = 5.0e5
E_FIBER_PA = 2.0e6
E_TRANS_PA = 5.0e5
C_N_S_PER_M = 6250.0
TAU_S = 0.25
STRAIN_BAND = [-0.30, 0.30]


def require(ok, code):
    if not ok:
        raise ValueError(code)


def load_inputs():
    arm_raw = (M02 / 'monkey_arm_regions.json').read_bytes()
    indep_raw = (M02 / 'independent_shape_regions.json').read_bytes()
    blob_raw = (M02 / 'monkey_arm_independent_meshes.json').read_bytes()
    arm = pl.decode(arm_raw)
    indep = pl.decode(indep_raw)
    blob = pl.decode(blob_raw)
    require(ms.digest(ms.canonical(arm)) == PIN_ARM_CANONICAL,
            'input_pin_drift:monkey_arm_regions')
    require(ms.digest(ms.canonical(indep)) == PIN_INDEP_CANONICAL,
            'input_pin_drift:independent_shape_regions')
    require(hashlib.sha256(blob_raw).hexdigest() == PIN_BLOB_SHA256,
            'input_pin_drift:mesh_blob')
    ms.validate_material_state(arm)
    ms.validate_material_state(indep)
    return arm, indep, blob, blob_raw


def tetra_gauge_from_blob(blob):
    """Derive the frozen gauge from the pinned tetra world vertices."""
    verts = blob['regions']['tetra']['world_vertices_m']
    require(len(verts) == 4, 'unexpected_tetra_vertex_count')
    v0 = verts[0]
    legs = [[verts[i][k] - v0[k] for k in range(3)] for i in (1, 2, 3)]
    # pinned legs: +X, +Y, +Z of length 0.1 (compiled placement of the
    # authored analytic right tetrahedron)
    for leg in legs:
        norm = math.sqrt(sum(c * c for c in leg))
        require(abs(norm - 0.1) < 1e-9, 'unexpected_tetra_leg:' + repr(norm))
    x_leg = legs[0]
    require(abs(x_leg[0] - 0.1) < 1e-9 and abs(x_leg[1]) < 1e-9
            and abs(x_leg[2]) < 1e-9, 'unexpected_tetra_x_leg')
    # face perpendicular to X at the x-min side: vertices v0, v2, v3
    a = [verts[2][k] - verts[0][k] for k in range(3)]
    b = [verts[3][k] - verts[0][k] for k in range(3)]
    cross = [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
             a[0] * b[1] - a[1] * b[0]]
    area = 0.5 * math.sqrt(sum(c * c for c in cross))
    require(abs(area - 0.005) < 1e-12, 'unexpected_gauge_area:' + repr(area))
    return {'rest_length_m': 0.1, 'area_m2': 5.0e-3, 'face_area_m2': area,
            'origin_m': v0}


def rotated_axis(deg):
    """Fiber axis: world +X rotated about world Z by deg degrees."""
    r = math.radians(deg)
    return [math.cos(r), math.sin(r), 0.0]


def validate_pins_for_test(document):
    """Refuse any document whose canonical hash is not one of the frozen
    input pins (test helper for the drift refusal probe)."""
    seen = ms.digest(ms.canonical(document))
    require(seen in (PIN_ARM_CANONICAL, PIN_INDEP_CANONICAL),
            'input_pin_drift:%s' % seen[:16])
    return seen


def profiles_rows():
    return [
        {'id': 'rigid',
         'constitutive_equation': 'x = 0 for any load in range; transmits '
                                  'F_out = F_in exactly; U = Q = 0',
         'parameters': {},
         'source_status': 'synthetic_authored',
         'damping': None,
         'valid_strain_range': [0.0, 0.0],
         'rest_state': 'no strain state exists; rest geometry is the only '
                       'geometry'},
        {'id': 'compliant_maxwell',
         'constitutive_equation': 'elastic x_el = F/k, k = E*A/L0; series '
                                  'dashpot: dF/dt = k*v - F/tau, tau = c/k; '
                                  'hold decay F(t) = F_ramp*exp(-t/tau); '
                                  'creep x(t) = F/k + F*t/c',
         'parameters': {'E_Pa': E_PA, 'A_m2': 5.0e-3, 'L0_m': 0.1,
                        'k_N_per_m': E_PA * 5.0e-3 / 0.1,
                        'c_N_s_per_m': C_N_S_PER_M, 'tau_s': TAU_S},
         'source_status': 'synthetic_authored',
         'damping': {'model': 'maxwell_series_dashpot',
                     'c_N_s_per_m': C_N_S_PER_M, 'tau_s': TAU_S},
         'valid_strain_range': list(STRAIN_BAND),
         'rest_state': 'zero applied load: extension 0, force 0, stored 0, '
                       'dissipated 0; current geometry == rest geometry'},
        {'id': 'fiber_reinforced',
         'constitutive_equation': 'E(theta) = E_trans + (E_fiber - '
                                  'E_trans)*cos^2(theta); elastic '
                                  'x = F*L0/(A*E(theta)); k = E(theta)*A/L0',
         'parameters': {'E_fiber_Pa': E_FIBER_PA, 'E_trans_Pa': E_TRANS_PA,
                        'A_m2': 5.0e-3, 'L0_m': 0.1},
         'source_status': 'synthetic_authored',
         'damping': None,
         'valid_strain_range': list(STRAIN_BAND),
         'rest_state': 'zero applied load: extension 0, force 0, stored 0, '
                       'dissipated 0; current geometry == rest geometry'},
    ]


def base_document(object_id, sources):
    return {'schema': pl.SCHEMA, 'revision': 1, 'object_id': object_id,
            'source_documents': sources, 'gauges': [], 'profiles': [],
            'directions': [], 'assignments': []}


def source_rows():
    return [
        {'id': 'monkey_arm_regions',
         'path': 'tools/monkey_campaign/contributions/MAT2-M02/'
                 'monkey_arm_regions.json',
         'object_id': 'monkey-arm-regions', 'canonical_sha256':
             PIN_ARM_CANONICAL},
        {'id': 'independent_shape_regions',
         'path': 'tools/monkey_campaign/contributions/MAT2-M02/'
                 'independent_shape_regions.json',
         'object_id': 'independent-shape-regions', 'canonical_sha256':
             PIN_INDEP_CANONICAL},
        {'id': 'mesh_blob',
         'path': 'tools/monkey_campaign/contributions/MAT2-M02/'
                 'monkey_arm_independent_meshes.json',
         'object_id': 'mat2-m02-mesh-blob', 'canonical_sha256':
             PIN_BLOB_SHA256},
    ]


GAUGE_PROVENANCE = (
    'gauge_declared: uniaxial X-leg gauge of the pinned compiled tetra; '
    'L0 = 0.100 m (X-leg rest length) and A = 5.0e-3 m^2 (exact area of the '
    'tetrahedron face perpendicular to X, recomputed from the pinned mesh '
    'blob vertices and cross-checked); support = pinned x-min face (visible '
    'in every capture); load applied at the x-max vertex, compressive. '
    'Authored experiment rig (synthetic), not a source-measured cross-section.')


def emit():
    arm, indep, blob, blob_raw = load_inputs()
    gauge = tetra_gauge_from_blob(blob)
    sources = source_rows()

    # ---------------- arm rigid laws (no tissue invented)
    arm_doc = base_document('mat2-m04-arm-rigid-laws', sources)
    arm_doc['profiles'] = [profiles_rows()[0]]
    arm_doc['assignments'] = [
        {'region_id': rid, 'profile_id': 'rigid', 'gauge_id': None,
         'direction_id': None,
         'provenance': 'bone surface segment (M02 compiled region); treated '
                       'as rigid for the monkey per preregistration; the '
                       'compiled arm has no soft-tissue volumes (M02 absence '
                       'inventory preserved)'}
        for rid in ARM_REGIONS]
    arm_doc['provenance'] = {
        'card': 'MAT2-M04', 'planning_id': 'M04',
        'attempt': '262e9d2a30ae4c4b82d84de7de9661a1',
        'note': 'all seven compiled arm regions rigid; no compliant or fiber '
                'profile assigned to any arm region because no soft tissue '
                'exists in the compiled inputs; density is never an input to '
                'stiffness',
        'schema_gap_note': "M01 material_state.v1 'laws' rows are closed at "
                           'kind pressure_deformation; passive laws are '
                           'declared in this chimera.passive_law.v1 document '
                           'until the schema vocabulary is extended by serial '
                           'integration'}

    # ---------------- independent shape laws (tetra + plate)
    indep_doc = base_document('mat2-m04-independent-shape-laws', sources)
    indep_doc['gauges'] = [
        {'id': 'G-TETRA', 'region_id': 'tetra', 'kind': 'uniaxial',
         'axis': [1.0, 0.0, 0.0], 'rest_length_m': gauge['rest_length_m'],
         'area_m2': gauge['area_m2'],
         'support': {'face': 'x_min_face', 'pinned': True},
         'load_application': 'x_max_vertex',
         'provenance': GAUGE_PROVENANCE},
    ]
    indep_doc['profiles'] = profiles_rows()
    indep_doc['directions'] = [
        {'id': 'fiber_tetra_0', 'region_id': 'tetra',
         'axis': rotated_axis(0.0), 'frame': 'rest', 'role': 'fiber_axis'},
        {'id': 'fiber_tetra_45', 'region_id': 'tetra',
         'axis': rotated_axis(45.0), 'frame': 'rest', 'role': 'fiber_axis'},
        {'id': 'fiber_tetra_90', 'region_id': 'tetra',
         'axis': rotated_axis(90.0), 'frame': 'rest', 'role': 'fiber_axis'},
    ]
    indep_doc['assignments'] = [
        {'region_id': 'tetra', 'profile_id': 'compliant_maxwell',
         'gauge_id': 'G-TETRA', 'direction_id': None,
         'provenance': 'isotropic compliant matrix profile on the pinned '
                       'tetra gauge (synthetic modulus E=5e5 Pa; no source '
                       'modulus admitted for monkey tissue)'},
    ]
    # The plate's area-scaled interface probe (P7) consumes the pinned blob
    # triangle areas directly through passive_response.triangle_force_shares;
    # the plate carries no gauge assignment in this document (no uniaxial
    # plate experiment is declared or claimed).
    indep_doc['provenance'] = {
        'card': 'MAT2-M04', 'planning_id': 'M04',
        'attempt': '262e9d2a30ae4c4b82d84de7de9661a1',
        'gauge_derivation': {'rest_length_m': gauge['rest_length_m'],
                             'area_m2': gauge['area_m2'],
                             'recomputed_face_area_m2': gauge['face_area_m2'],
                             'tetra_origin_m': gauge['origin_m']},
        'rotated_fiber_note': 'the tetra carries three declared fiber '
                              'directions (0/45/90 deg about world Z) used '
                              'by the E3 rotated-fiber experiment; each '
                              'direction row is assigned in experiments, '
                              'not simultaneously',
        'plate_note': 'the plate keeps its pinned M02 geometry and authored '
                      'thickness; only its pinned two-triangle areas feed '
                      'the area-scaled interface oracle (P7) — no plate '
                      'gauge, no plate deformation claim',
        'density_note': 'matter masses/densities are M02 pinned data; they '
                        'are never inputs to stiffness, force, extension or '
                        'energy'}

    # ---------------- M01-native directions document (validator unmodified)
    directions_doc = json.loads(json.dumps(indep))  # deep copy of pinned doc
    directions_doc['directions'] = [
        {'id': 'fiber_tetra_0', 'region_id': 'tetra',
         'axis': rotated_axis(0.0), 'history': [
             {'revision': 0, 'state': 'declared_by_MAT2-M04'}]},
        {'id': 'fiber_tetra_45', 'region_id': 'tetra',
         'axis': rotated_axis(45.0), 'history': [
             {'revision': 0, 'state': 'declared_by_MAT2-M04'}]},
        {'id': 'fiber_tetra_90', 'region_id': 'tetra',
         'axis': rotated_axis(90.0), 'history': [
             {'revision': 0, 'state': 'declared_by_MAT2-M04'}]},
    ]
    directions_doc['provenance'] = dict(directions_doc['provenance'])
    directions_doc['provenance']['mat2_m04_directions'] = (
        'direction rows declared by MAT2-M04 (attempt '
        '262e9d2a30ae4c4b82d84de7de9661a1) through the unmodified M01 '
        'direction schema; no law rows added because M01 law kinds are '
        'closed at pressure_deformation (M03); geometry, matter, bonds and '
        'all revision-1 records are byte-preserved from the pinned M02 '
        'document')
    ms.validate_material_state(directions_doc)

    # validate through the M04 validator
    pl.validate_passive_law(arm_doc)
    pl.validate_passive_law(indep_doc)

    display = {
        'kind': 'mat2_m04_passive_law_display',
        'documents': [
            {'file': 'arm_rigid_laws.json',
             'canonical_sha256': pl.digest(pl.canonical(arm_doc)),
             'summary': pl.summary(arm_doc)},
            {'file': 'independent_shape_laws.json',
             'canonical_sha256': pl.digest(pl.canonical(indep_doc)),
             'summary': pl.summary(indep_doc)},
            {'file': 'independent_shape_directions.json',
             'canonical_sha256': ms.digest(ms.canonical(directions_doc)),
             'summary': ms.validate_material_state(directions_doc)},
        ],
        'input_pins': {'arm_canonical': PIN_ARM_CANONICAL,
                       'independent_canonical': PIN_INDEP_CANONICAL,
                       'mesh_blob': PIN_BLOB_SHA256},
        'gauge': {'id': 'G-TETRA', 'rest_length_m': gauge['rest_length_m'],
                  'area_m2': gauge['area_m2'],
                  'recomputed_face_area_m2': gauge['face_area_m2']},
        'honesty': {
            'profiles_implemented': ['rigid', 'compliant_maxwell',
                                     'fiber_reinforced'],
            'profiles_absent': ['active muscle control', 'pressure law '
                                '(M03, parallel)', 'fracture', 'thermal',
                                'plasticity', 'viscoelastic beyond the '
                                'single Maxwell element'],
            'density_in_stiffness': False,
            'm01_law_vocabulary_gap': "passive kinds are not in M01 "
                                      "LAW_KINDS (closed at "
                                      "pressure_deformation); declared "
                                      "here instead"},
    }

    def write(name, doc):
        path = HERE / name
        path.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + '\n',
                        encoding='utf-8')
        return path

    write('arm_rigid_laws.json', arm_doc)
    write('independent_shape_laws.json', indep_doc)
    write('independent_shape_directions.json', directions_doc)
    write('passive_law_display.json', display)
    print('arm assignments:', pl.summary(arm_doc)['assignment_count'],
          'all rigid')
    print('independent assignments:',
          pl.summary(indep_doc)['assignment_count'],
          pl.summary(indep_doc)['profile_counts'])
    print('directions doc law_count (must be 0):',
          ms.validate_material_state(directions_doc)['law_count'],
          'direction_count:',
          ms.validate_material_state(directions_doc)['direction_count'])
    print('canonical hashes:', [d['canonical_sha256'][:16]
                                for d in display['documents']])
    return arm_doc, indep_doc, directions_doc, display


if __name__ == '__main__':
    emit()
