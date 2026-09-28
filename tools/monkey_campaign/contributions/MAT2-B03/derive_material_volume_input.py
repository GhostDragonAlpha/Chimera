"""MAT2-B03 derivation: real validated material-volume input for the macaque
forelimb regions compiled by MAT2-M02.

Builds the complete C02 (mass inventory) + C03 (centre of mass and inertia)
input for the selected body exactly as frozen in PREREGISTRATION.md (committed
before this file existed):

- inputs are sha256-pinned (M01 validator, M02 documents, mesh blob, compile
  receipt, graph pins, archived matter library extract); a pin mismatch
  refuses `input_pin_mismatch:<path>`.
- volume ownership: exactly the five CLOSED regions count; the two open
  surfaces (scapula, hand) are shells and claim zero volume-owned mass
  (`shell_volume_claim_refused` otherwise) -- static meshes do not implicitly
  provide interiors.
- density: archived matter library `materials.bone` entry, mean 1800 kg/m3,
  researched provenance, source spread carried as an uncertainty band,
  conditions stated honestly (source states none); values outside the frozen
  physical envelope [500, 3000] kg/m3 refuse `density_unit_scale_violation`.
- C02: m = integral rho dV = rho * V (uniform authored density, exact);
  counted total over counted regions; .osim effective segment masses recorded
  as EXCLUDED claims, never counted.
- C03: aggregate COM + full symmetric inertia tensor (off-diagonals included)
  about the aggregate COM in the world:default_pose frame, computed by two
  algebraically independent formulations:
    method A: divergence-theorem signed monomial moment integrals per triangle
              (exact for polyhedra), parallel axis to COM;
    method B: per-triangle signed tetrahedral decomposition with exact
              reference-simplex covariance mapping, parallel axis to COM.
  Frozen checks: cross-method agreement (V1/W1), continuity with the admitted
  M02/graph-pin volumes (V2), analytic cube + tetra closed forms (V3),
  rotation covariance under two preregistered rotations (W2), parallel-axis
  recombination (W3), symmetry/positive-definiteness (W4), excluded-claim
  null contribution (W5).
- the emitted document is validated with the UNMODIFIED M01 validator; the
  validator's total mass equals the C02 counted total by construction.

Every emitted number is recorded in derivation_receipt.json. The `verify`
subcommand recomputes everything from the pinned inputs and refuses with the
named codes the frozen falsifiers bite: mass_inventory_mismatch:<region>,
density_source_missing, shell_volume_claim_refused:<region>,
density_unit_scale_violation:<region>, rotation_covariance_violation,
inertia_tensor_mismatch, mesh_blob_sha256_mismatch,
volume_continuity_violation.

CPU-only, deterministic (no randomness, no seeds; the two probe rotations are
preregistered fixed angles). Stdlib + numpy.
"""
from __future__ import annotations

import hashlib
import json
import math
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
CONTRIB = HERE.parent
sys.path.insert(0, str(CONTRIB / 'MAT2-M01'))

import material_state as ms  # noqa: E402  (unmodified M01 validator)

# ------------------------------------------------------------ frozen inputs
BASE_REVISION = '986f270ef24cda0008c52bd40d4b6d08565c0692'
INTAKE_REVISION = 'eafbc15161ae10ae95b62d07d3f4878aefa34d9d'
M01 = CONTRIB / 'MAT2-M01'
M02 = CONTRIB / 'MAT2-M02'
INPUT_PINS = {
    'validator': (M01 / 'material_state.py',
                  'b6b009713daa4b315c6b5cb43c7ad4e756123b50edcdd802eeebd55c6afd6c40'),
    'm02_arm_regions': (M02 / 'monkey_arm_regions.json',
                        '15ae0e5a3d540d52b9a0e5c9b8af2f8a6bf7f2c9770a5f2cd7c1e9e8758366f1'),
    'm02_indep_regions': (M02 / 'independent_shape_regions.json',
                          '0f0b7165883183446b15b7043fd5471f0b12d6d992ffabc27107f4de1238887e'),
    'mesh_blob': (M02 / 'monkey_arm_independent_meshes.json',
                  '51d8231e0d1eacd7f0d4b558699f011e35ff765f5d0e07ef5889ded27216a834'),
    'm02_compile_receipt': (M02 / 'compile_receipt.json',
                            '7192aed9a373e3ee639fafa44d4e86132eb3b37fb8187157ec906d399b8e430f'),
    'graph_pins': (M02 / 'data' / 'graph_pins.json',
                   '849f9988d1a6ccb451bb45d79f298dd954c4e5605acd19d7d882a5c70a285b97'),
    'matter_library': (HERE / 'data' / 'matter_library_1af0bbde.json',
                       'de10200fb87bf48c3cc80d5e223805f02e27df115b91186f42f28064a64054ed'),
}
MATTER_LIBRARY_ORIGIN = ('tools/monkey_campaign/contributions/MAT2-B02/work/'
                         'frozen/1af0bbde/Chimera/docs/matter/matter_library.json')
COUNTED_REGIONS = ('clavicle', 'humerus', 'radius', 'sternum', 'ulna')
SHELL_REGIONS = ('scapula', 'hand')
DENSITY_MEAN_KG_M3 = 1800.0
DENSITY_BAND_KG_M3 = [1650.0, 1950.0]
DENSITY_ENVELOPE_KG_M3 = (500.0, 3000.0)
DENSITY_CONDITIONS = ('source library states no temperature/moisture/strain-rate '
                      'conditions for this entry; treated as apparent cortical '
                      'bone density at reference (near-ambient, wet tissue) '
                      'conditions; under-specification recorded, not fabricated')
TOL_REL = 1e-9
TOL_CONTINUITY = 1e-12
# preregistered probe rotations (deg, axis): W2 rotation covariance
PROBE_ROTATIONS = ((30.0, (0.0, 0.0, 1.0)), (25.0, (1.0, 0.0, 0.0)))
WORLD_FRAME_ID = 'world:default_pose'

OUTPUT_DOC = HERE / 'material_volume_input.json'
OUTPUT_RECEIPT = HERE / 'derivation_receipt.json'


def require(condition, code):
    if not condition:
        raise ValueError(code)


def sha256_file(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def rel_diff(a, b):
    scale = max(abs(a), abs(b))
    if scale == 0.0:
        return abs(a - b)
    return abs(a - b) / scale


def check_rel(a, b, tol, code):
    require(rel_diff(a, b) <= tol, code + ':rel=%r' % rel_diff(a, b))


def check_abs(value, tol, code):
    require(abs(value) <= tol, code + ':abs=%r' % abs(value))


def check_mat(a, b, tol, code):
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    denom = max(np.abs(a).max(), np.abs(b).max())
    require(denom > 0.0 and float(np.abs(a - b).max() / denom) <= tol,
            code + ':maxrel=%r' % float(np.abs(a - b).max() / denom))


# ----------------------------------------------------------------- geometry
def load_inputs():
    for name, (path, sha) in INPUT_PINS.items():
        require(path.exists(), 'input_missing:' + str(path))
        require(sha256_file(path) == sha, 'input_pin_mismatch:' + name)
    arm = json.loads(INPUT_PINS['m02_arm_regions'][0].read_text('utf-8'))
    blob = json.loads(
        INPUT_PINS['mesh_blob'][0].read_text('utf-8'))
    pins = json.loads(INPUT_PINS['graph_pins'][0].read_text('utf-8'))
    library = json.loads(
        INPUT_PINS['matter_library'][0].read_text('utf-8'))
    return arm, blob, pins, library


def bone_density_entry(library):
    entry = library['materials']['bone']['physical']['density_kg_m3']
    require(entry.get('provenance') == 'researched',
            'density_provenance_missing')
    mean = float(entry['mean'])
    spread = float(entry['spread'])
    require(DENSITY_ENVELOPE_KG_M3[0] <= mean <= DENSITY_ENVELOPE_KG_M3[1],
            'density_unit_scale_violation:mean=%r' % mean)
    return {'mean': mean, 'spread': spread,
            'note': entry.get('note', ''), 'provenance': entry['provenance']}


# ------------------------------------------------- method A: moment integrals
def tet_monomial_moments(a, b, c):
    """Signed monomial moment integrals of the tetra (origin, a, b, c).

    Exact for the tetrahedron: V = T/6; first/second moments from the
    reference-simplex monomial integrals (du1=1/24, du1^2=1/60, du1 du2=1/120).
    Returns (V, M100, M010, M001, M200, M020, M002, M110, M101, M011)."""
    T = float(np.dot(a, np.cross(b, c)))
    sx, sy, sz = a[0] + b[0] + c[0], a[1] + b[1] + c[1], a[2] + b[2] + c[2]
    def mom2(i, j):
        # integral of coordinate_i * coordinate_j over the signed tetra
        ai, bi, ci = a[i], b[i], c[i]
        aj, bj, cj = a[j], b[j], c[j]
        return T / 60.0 * (ai * aj + bi * bj + ci * cj) \
            + T / 120.0 * (ai * bj + bi * aj + ai * cj + ci * aj
                           + bi * cj + ci * bj)
    m200, m020, m002 = mom2(0, 0), mom2(1, 1), mom2(2, 2)
    m110, m101, m011 = mom2(0, 1), mom2(0, 2), mom2(1, 2)
    return (T / 6.0,
            T / 24.0 * sx, T / 24.0 * sy, T / 24.0 * sz,
            m200, m020, m002, m110, m101, m011)


def moments_method_a(verts, tris):
    """Divergence-theorem surface accumulation over the closed mesh."""
    v = np.asarray(verts, dtype=np.float64)
    t = np.asarray(tris, dtype=np.int64)
    total = np.zeros(10, dtype=np.float64)
    for t0, t1, t2 in t:
        m = tet_monomial_moments(v[t0], v[t1], v[t2])
        total += np.asarray(m)
    return total  # (V, Mx, My, Mz, Mxx, Myy, Mzz, Mxy, Mxz, Myz)


def inertia_from_moments(moments, rho):
    """COM + full inertia tensor about the COM from raw moments and density."""
    V, mx, my, mz, mxx, myy, mzz, mxy, mxz, myz = [rho * x for x in moments]
    m = V
    require(m > 0.0, 'nonpositive_mass')
    com = np.array([mx, my, mz]) / m
    # inertia about world origin: I_xx = rho(Myy+Mzz), I_xy = -rho Mxy ...
    I_o = np.array([
        [myy + mzz, -mxy, -mxz],
        [-mxy, mxx + mzz, -myz],
        [-mxz, -myz, mxx + myy]])
    shift = m * (float(np.dot(com, com)) * np.eye(3) - np.outer(com, com))
    return float(m), com, I_o - shift


# ----------------------- method B: tetra covariance mapping (independent)
_REF_COV = np.array([
    [1.0 / 160.0, -1.0 / 480.0, -1.0 / 480.0],
    [-1.0 / 480.0, 1.0 / 160.0, -1.0 / 480.0],
    [-1.0 / 480.0, -1.0 / 480.0, 1.0 / 160.0]])


def inertia_method_b(verts, tris, rho):
    """Per-triangle signed tetra (origin, a, b, c) exact covariance mapping.

    Uses the closed-form reference-simplex covariance (diag 1/160,
    off-diag -1/480) mapped by the tet edge basis, then parallel axis to the
    origin and accumulation. Algebraically independent of method A's monomial
    surface formulas."""
    v = np.asarray(verts, dtype=np.float64)
    t = np.asarray(tris, dtype=np.int64)
    V = 0.0
    first = np.zeros(3)
    second_o = np.zeros((3, 3))
    for t0, t1, t2 in t:
        A = np.column_stack([v[t0], v[t1], v[t2]])
        T = float(np.linalg.det(A))
        Vt = T / 6.0
        V += Vt
        cov_c = (rho * abs(T)) * (A @ _REF_COV @ A.T)  # about the tet centroid
        m_t = rho * Vt                                 # signed mass
        c_t = (v[t0] + v[t1] + v[t2]) / 4.0            # centroid of the tetra
        first += m_t * c_t
        I_c = np.trace(cov_c) * np.eye(3) - cov_c       # about centroid, |m|
        # signed accumulation: the WHOLE tet contribution carries sign(T)
        # (a negatively wound tet contributes the NEGATIVE of its positive-
        # mass inertia; mixing conventions here corrupts every off-origin
        # shape -- this exact defect was caught by the cross-method probe
        # and fixed before any candidate number was emitted).
        I_origin = I_c + abs(m_t) * (float(np.dot(c_t, c_t)) * np.eye(3)
                                     - np.outer(c_t, c_t))
        second_o += (1.0 if T >= 0.0 else -1.0) * I_origin
    require(V > 0.0, 'nonpositive_mass')
    m = float(rho * V)
    com = first / m
    shift = m * (float(np.dot(com, com)) * np.eye(3) - np.outer(com, com))
    return m, com, second_o - shift


def rodrigues(deg, axis):
    ax = np.asarray(axis, dtype=np.float64)
    ax = ax / np.linalg.norm(ax)
    th = math.radians(deg)
    K = np.array([[0.0, -ax[2], ax[1]], [ax[2], 0.0, -ax[0]],
                  [-ax[1], ax[0], 0.0]])
    return np.eye(3) + math.sin(th) * K + (1.0 - math.cos(th)) * (K @ K)


# ------------------------------------------------------------ analytic cells
def unit_cube_mesh(side):
    h = side / 2.0
    p = [(-h, -h, -h), (h, -h, -h), (h, h, -h), (-h, h, -h),
         (-h, -h, h), (h, -h, h), (h, h, h), (-h, h, h)]
    quads = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
             (2, 3, 7, 6), (1, 2, 6, 5), (3, 0, 4, 7)]
    tris = []
    for a, b, c, d in quads:
        tris += [[a, b, c], [a, c, d]]
    return np.asarray(p, dtype=np.float64), tris


def right_tetra_mesh(a, b, c):
    p = [(0.0, 0.0, 0.0), (a, 0.0, 0.0), (0.0, b, 0.0), (0.0, 0.0, c)]
    tris = [[0, 2, 1], [0, 1, 3], [0, 3, 2], [1, 2, 3]]
    return np.asarray(p, dtype=np.float64), tris


# --------------------------------------------------------------- derivation
def region_material_volume(name, verts_w, tris, density, arm, pins):
    mom = moments_method_a(verts_w, tris)
    v_a = float(mom[0])
    m_b, com_b, I_b = inertia_method_b(verts_w, tris, density['mean'])
    m_a, com_a, I_a = inertia_from_moments(mom, density['mean'])
    check_rel(v_a, m_b / density['mean'], TOL_REL,
              'volume_cross_method_disagreement:' + name)
    # V2 continuity with the admitted recorded claims
    row = next(r for r in arm['regions'] if r['id'] == name)
    claim = row['rest_geometry']['volume_claim_m3']
    check_rel(v_a, claim, TOL_CONTINUITY,
              'volume_continuity_violation:' + name + ':doc')
    pin_v = pins['geom_pins'][name]['metrics']['signed_volume_m3']
    check_rel(v_a, pin_v, TOL_CONTINUITY,
              'volume_continuity_violation:' + name + ':pin')
    # W1 cross-method COM/inertia agreement
    check_abs(float(np.linalg.norm(com_a - com_b)), TOL_REL
              * max(float(np.linalg.norm(com_a)), 1e-12),
              'com_cross_method_disagreement:' + name)
    check_mat(I_a, I_b, TOL_REL, 'inertia_cross_method_disagreement:' + name)
    mass = density['mean'] * v_a
    # body-frame expression of the COM (transform only; no new physics)
    frame_name = name
    frames = pins['body_frames']
    F = np.asarray(frames[frame_name], dtype=np.float64)
    R, t = F[:3, :3], F[:3, 3]
    com_body = R.T @ (com_a - t)
    return {
        'region_id': name,
        'density_kg_m3': density['mean'],
        'volume_m3_method_a': v_a,
        'volume_m3_method_b': m_b / density['mean'],
        'mass_kg_method_a': m_a,
        'mass_kg_method_b': m_b,
        'com_m_world_default_pose': [float(x) for x in com_a],
        'com_m_body_frame': [float(x) for x in com_body],
        'inertia_about_own_com_kg_m2': [[float(x) for x in rowv]
                                        for rowv in I_a],
    }


def derive():
    arm, blob, pins, library = load_inputs()
    density = bone_density_entry(library)

    counted, shells = {}, {}
    for name in COUNTED_REGIONS:
        rec = blob['regions'][name]
        verts = rec['world_vertices_m']
        tris = rec['triangles']
        counted[name] = region_material_volume(name, verts, tris, density,
                                               arm, pins)
    for name in SHELL_REGIONS:
        row = next(r for r in arm['regions'] if r['id'] == name)
        require(row['kind'] == 'shell', 'shell_expected:' + name)
        osim_claim = next(m['mass_kg'] for m in arm['matter']
                          if m['id'] == 'mass_' + name)
        shells[name] = {
            'region_id': name,
            'open_edge_count': row['rest_geometry']['open_edge_count'],
            'volume_owned_mass_kg': 0.0,
            'excluded_osim_segment_claim_kg': osim_claim,
        }

    counted_total = sum(counted[k]['mass_kg_method_a'] for k in COUNTED_REGIONS)

    # ---- aggregate C03 over the counted set (world:default_pose)
    M = counted_total
    com = sum(np.asarray(counted[k]['com_m_world_default_pose'])
              * counted[k]['mass_kg_method_a'] for k in COUNTED_REGIONS) / M
    I_com = np.zeros((3, 3))
    for k in COUNTED_REGIONS:
        I_i = np.asarray(counted[k]['inertia_about_own_com_kg_m2'])
        d = np.asarray(counted[k]['com_m_world_default_pose']) - com
        I_com += I_i + counted[k]['mass_kg_method_a'] * (
            float(np.dot(d, d)) * np.eye(3) - np.outer(d, d))

    # ---- frozen verification battery
    verification = {'probes': []}

    def probe(pid, ok, detail):
        require(ok, 'verification_probe_failed:' + pid + ':' + detail)
        verification['probes'].append({'id': pid, 'ok': True, 'detail': detail})

    # W2 rotation covariance (fixed preregistered rotations)
    blob_regions = blob['regions']
    rot_reports = []
    for deg, axis in PROBE_ROTATIONS:
        R = rodrigues(deg, axis)
        first = np.zeros(3)
        per_region = []
        for k in COUNTED_REGIONS:
            v = np.asarray(blob_regions[k]['world_vertices_m'],
                           dtype=np.float64) @ R.T
            m_k, com_k, I_k = inertia_method_b(
                v.tolist(), blob_regions[k]['triangles'], density['mean'])
            first += m_k * com_k
            per_region.append((m_k, com_k, I_k))
        com_rot = first / M
        agg_rot = np.zeros((3, 3))
        for m_k, com_k, I_k in per_region:
            d = com_k - com_rot
            agg_rot += I_k + m_k * (float(np.dot(d, d)) * np.eye(3)
                                    - np.outer(d, d))
        check_mat(agg_rot, R @ I_com @ R.T, TOL_REL,
                  'rotation_covariance_violation')
        check_abs(float(np.linalg.norm(com_rot - R @ com)), TOL_REL
                  * max(float(np.linalg.norm(com)), 1e-12),
                  'rotation_covariance_violation:com')
        rot_reports.append({'rotation_deg': deg, 'axis': list(axis),
                            'covariance_ok': True})

    # W3 recombination is exact by construction of I_com; assert it independently
    # (recompute aggregate from fresh per-region world integrals, shifting each
    # region's about-own-COM tensor to the fresh aggregate COM)
    com_direct = np.zeros(3)
    fresh = []
    for k in COUNTED_REGIONS:
        rec = blob_regions[k]
        m_k, com_k, I_k = inertia_from_moments(
            moments_method_a(rec['world_vertices_m'], rec['triangles']),
            density['mean'])
        com_direct += m_k * com_k
        fresh.append((m_k, com_k, I_k))
    com_direct /= M
    I_direct = np.zeros((3, 3))
    for m_k, com_k, I_k in fresh:
        d = com_k - com_direct
        I_direct += I_k + m_k * (float(np.dot(d, d)) * np.eye(3)
                                 - np.outer(d, d))
    check_mat(I_direct, I_com, TOL_REL, 'parallel_axis_recombination_violation')
    check_abs(float(np.linalg.norm(com_direct - com)), 1e-15,
              'com_recombination_violation')

    # W4 symmetry + positive-definiteness
    sym = float(np.abs(I_com - I_com.T).max())
    require(sym == 0.0, 'inertia_not_symmetric')
    eig = sorted(float(x) for x in np.linalg.eigvalsh(I_com))
    require(eig[0] > 0.0, 'inertia_not_positive_definite')

    # W5 excluded claims contribute nothing
    I_with_shells = np.zeros((3, 3))
    for k in COUNTED_REGIONS:
        I_i = np.asarray(counted[k]['inertia_about_own_com_kg_m2'])
        d = np.asarray(counted[k]['com_m_world_default_pose']) - com
        I_with_shells += I_i + counted[k]['mass_kg_method_a'] * (
            float(np.dot(d, d)) * np.eye(3) - np.outer(d, d))
    require(float(np.abs(I_with_shells - I_com).max()) == 0.0,
            'excluded_claim_contributed_mass')
    probe('W5', True, 'excluded claims contribute exactly zero')

    # V3 analytic cells through the same pipeline
    rho = density['mean']
    s = 1.0
    cv, ct = unit_cube_mesh(s)
    mom = moments_method_a(cv.tolist(), ct)
    v_cube = float(mom[0])
    m_c, com_c, I_c = inertia_from_moments(mom, rho)
    check_rel(v_cube, s ** 3, TOL_REL, 'analytic_cube_volume')
    check_rel(m_c, rho * s ** 3, TOL_REL, 'analytic_cube_mass')
    check_abs(float(np.abs(np.asarray(com_c)).max()), 1e-15,
              'analytic_cube_com')
    I_diag = m_c * s * s / 6.0 * np.eye(3)
    check_mat(I_c, I_diag, TOL_REL, 'analytic_cube_inertia')
    a = b = c = 0.1
    tv, tt = right_tetra_mesh(a, b, c)
    mom_t = moments_method_a(tv.tolist(), tt)
    v_tet = float(mom_t[0])
    m_t, com_t, I_t = inertia_from_moments(mom_t, rho)
    check_rel(v_tet, a * b * c / 6.0, TOL_REL, 'analytic_tetra_volume')
    check_rel(m_t, rho * a * b * c / 6.0, TOL_REL, 'analytic_tetra_mass')
    check_abs(float(np.linalg.norm(np.asarray(com_t)
                                   - np.asarray([a / 4, b / 4, c / 4]))),
              1e-15, 'analytic_tetra_com')
    # right-tet inertia closed form about its COM via the reference-simplex
    # covariance mapped by the edge basis A = diag(a, b, c)
    rho_t = rho
    A = np.diag([a, b, c])
    cov_c = (rho_t * a * b * c) * (A @ _REF_COV @ A.T)
    I_closed = np.trace(cov_c) * np.eye(3) - cov_c
    check_mat(I_t, I_closed, TOL_REL, 'analytic_tetra_inertia')
    probe('V3', True, 'analytic cube and right tetra closed forms reproduced')

    probe('V1', True, 'cross-method volumes agree within %g' % TOL_REL)
    probe('V2', True, 'volumes continuous with M02 claims and graph pins')
    probe('W1', True, 'cross-method COM/inertia agree within %g' % TOL_REL)
    probe('W2', True, 'rotation covariance for %s' % repr(PROBE_ROTATIONS))
    probe('W3', True, 'parallel-axis recombination exact within %g' % TOL_REL)
    probe('W4', True, 'tensor symmetric, eigenvalues %r' % eig)

    # ---- emitted document (chimera.material_state.v1)
    regions_out = []
    matter_out = []
    lib_sha = INPUT_PINS['matter_library'][1]
    for row in arm['regions']:
        name = row['id']
        new_row = json.loads(json.dumps(row))
        if name in counted:
            cvd = counted[name]
            new_row['rest_geometry']['material_volume'] = {
                'counted': True,
                'density_kg_m3': cvd['density_kg_m3'],
                'density_band_kg_m3': list(DENSITY_BAND_KG_M3),
                'density_source': {
                    'library_file': 'data/matter_library_1af0bbde.json',
                    'library_sha256': lib_sha,
                    'library_origin': MATTER_LIBRARY_ORIGIN,
                    'entry': 'materials.bone.physical.density_kg_m3',
                    'provenance_class': density['provenance'],
                    'citation_note': density['note'],
                    'honesty': 'library provenance class recorded; not claimed '
                               'to be proof of authentic measurement (MAT-03)',
                },
                'density_conditions': DENSITY_CONDITIONS,
                'volume_m3_method_a': cvd['volume_m3_method_a'],
                'volume_m3_method_b': cvd['volume_m3_method_b'],
                'volume_provenance': 'exact divergence-theorem integral over '
                                     'the pinned closed triangle set '
                                     '(mesh_blob sha '
                                     + INPUT_PINS['mesh_blob'][1] + '); two '
                                     'independent formulations agree',
                'volume_claim_m3': cvd['volume_m3_method_a'],
                'mass_kg': cvd['mass_kg_method_a'],
                'mass_method': 'm = integral rho dV = rho*V '
                               '(uniform authored density; exact reduction)',
                'com_m_world_default_pose': cvd['com_m_world_default_pose'],
                'com_m_body_frame': cvd['com_m_body_frame'],
                'inertia_about_own_com_kg_m2':
                    cvd['inertia_about_own_com_kg_m2'],
            }
            new_row['matter_claims'] = [
                {'matter_id': 'bone_' + name, 'role': 'owner'}]
            matter_out.append({
                'id': 'bone_' + name, 'mass_kg': cvd['mass_kg_method_a'],
                'provenance': 'volume-owned: m = integral rho dV = '
                              + repr(cvd['density_kg_m3']) + ' kg/m3 * '
                              + repr(cvd['volume_m3_method_a']) + ' m3; '
                              'density from archived matter library '
                              'materials.bone (researched, sha ' + lib_sha
                              + '); counted region'})
        else:
            sh = shells[name]
            new_row['rest_geometry']['material_volume'] = {
                'counted': False,
                'volume_claim_m3': None,
                'volume_owned_mass_kg': 0.0,
                'refusal': 'shell_volume_claim_refused: static mesh does not '
                           'implicitly provide interiors',
                'excluded_osim_segment_claim_kg':
                    sh['excluded_osim_segment_claim_kg'],
                'open_edge_count': sh['open_edge_count'],
            }
            new_row['matter_claims'] = [
                {'matter_id': 'shell_' + name, 'role': 'owner'}]
            matter_out.append({
                'id': 'shell_' + name, 'mass_kg': 0.0,
                'provenance': 'open surface (no interior authored); carries '
                              'ZERO volume-owned mass; the .osim effective '
                              'segment claim ('
                              + repr(sh['excluded_osim_segment_claim_kg'])
                              + ' kg) is recorded as an excluded claim and '
                              'is NOT counted'})
        regions_out.append(new_row)

    excluded = []
    for m in arm['matter']:
        excluded.append({
            'claim_id': m['id'], 'mass_kg': m['mass_kg'],
            'kind': 'osim_effective_body_segment_mass',
            'reason': 'effective body segment mass from the admitted .osim '
                      'row; not owned by this bone-geometry input; not '
                      'counted',
            'source': 'MAT2-M02 monkey_arm_regions.json (sha '
                      + INPUT_PINS['m02_arm_regions'][1] + ')'})
    document = {
        'schema': 'chimera.material_state.v1',
        'revision': 1,
        'object_id': 'monkey-arm-material-volume-input',
        'regions': regions_out,
        'matter': matter_out,
        'directions': [],
        'laws': [],
        'contacts': [],
        'bonds': json.loads(json.dumps(arm['bonds'])),
        'provenance': {
            'base_revision': BASE_REVISION,
            'derived_from': {
                'm02_document': 'tools/monkey_campaign/contributions/MAT2-M02/'
                                'monkey_arm_regions.json',
                'm02_document_sha256': INPUT_PINS['m02_arm_regions'][1],
                'mesh_blob_sha256': INPUT_PINS['mesh_blob'][1],
                'graph_pins_sha256': INPUT_PINS['graph_pins'][1],
                'validator': 'tools/monkey_campaign/contributions/MAT2-M01/'
                             'material_state.py (unmodified)',
                'validator_sha256': INPUT_PINS['validator'][1],
            },
            'preregistration': {
                'file': 'tools/monkey_campaign/contributions/MAT2-B03/'
                        'PREREGISTRATION.md',
                'frozen_commit': '421a9873',
                'note': 'frozen before implementation and before any '
                        'measurement',
            },
            'density_source': {
                'library_file': 'data/matter_library_1af0bbde.json',
                'library_sha256': lib_sha,
                'library_origin': MATTER_LIBRARY_ORIGIN,
                'entry': 'materials.bone.physical.density_kg_m3',
                'mean_kg_m3': density['mean'],
                'uncertainty_band_kg_m3': list(DENSITY_BAND_KG_M3),
                'provenance_class': density['provenance'],
                'conditions': DENSITY_CONDITIONS,
                'fidelity': 'uniform apparent density per counted region; no '
                            'heterogeneous field, muscle volume, skin or fat '
                            'is authored (none supported by pinned geometry)',
            },
            'counted_set': {
                'regions': sorted(COUNTED_REGIONS),
                'rule': 'closed_outward_consistent regions only',
                'counted_total_kg': counted_total,
            },
            'excluded_claims': excluded,
            'surface_mass_note': 'no surface mass is represented: no source '
                                 'shell thickness exists for bone surfaces '
                                 '(M02); shells count zero volume mass',
            'centre_of_mass_m_world_default_pose': [float(x) for x in com],
            'inertia_about_com_kg_m2': [[float(x) for x in r]
                                        for r in I_com],
            'inertia_frame': WORLD_FRAME_ID,
            'verification': verification,
            'absent_or_unresolved': [
                'muscle volumes: the 39 source muscles are 1D path points '
                'only; no volume authored',
                'skin/fat geometry: absent from the pinned source',
                'organs/interior tissue: absent',
                'heterogeneous density field: not authored (uniform '
                'per-region apparent density only)',
                'temperature/moisture/strain-rate conditions for the density '
                'source: not stated by the source; recorded as a limitation',
                'runtime solver: none exists at revision 1',
            ],
        },
    }
    summary = ms.validate_material_state(document)
    require(abs(summary['total_mass_kg'] - counted_total) <= 0.0,
            'm01_total_differs_from_counted_total')

    # frozen prediction check (preregistered from admitted pin arithmetic)
    predictions = []
    for name in COUNTED_REGIONS:
        pin_v = pins['geom_pins'][name]['metrics']['signed_volume_m3']
        predicted = DENSITY_MEAN_KG_M3 * pin_v
        actual = counted[name]['mass_kg_method_a']
        ok = rel_diff(predicted, actual) <= 1e-12
        predictions.append({'region': name, 'predicted_kg': predicted,
                            'actual_kg': actual, 'match': bool(ok)})
        require(ok, 'frozen_prediction_missed:' + name)
    require(rel_diff(DENSITY_MEAN_KG_M3
                     * sum(pins['geom_pins'][k]['metrics']['signed_volume_m3']
                           for k in COUNTED_REGIONS), counted_total) <= 1e-12,
            'frozen_prediction_missed:counted_total')

    receipt = {
        'kind': 'mat2_b03_derivation_receipt',
        'base_revision': BASE_REVISION,
        'input_pins': {k: v[1] for k, v in INPUT_PINS.items()},
        'density': {'mean_kg_m3': density['mean'],
                    'band_kg_m3': list(DENSITY_BAND_KG_M3),
                    'provenance_class': density['provenance'],
                    'conditions': DENSITY_CONDITIONS},
        'counted_total_kg': counted_total,
        'regions': [counted[k] for k in COUNTED_REGIONS],
        'shells': [shells[k] for k in SHELL_REGIONS],
        'aggregate': {
            'frame': WORLD_FRAME_ID,
            'mass_kg': M,
            'com_m': [float(x) for x in com],
            'inertia_about_com_kg_m2': [[float(x) for x in r] for r in I_com],
            'eigenvalues_kg_m2': eig,
        },
        'predictions': predictions,
        'verification': verification,
        'emitted_document': {
            'file': 'material_volume_input.json',
            'canonical_sha256': ms.digest(ms.canonical(document)),
            'm01_summary': summary,
        },
        'determinism': 'no randomness; fixed preregistered rotations '
                       + repr(PROBE_ROTATIONS) + '; stdlib+numpy only',
    }

    OUTPUT_DOC.write_text(json.dumps(document, indent=1) + '\n',
                          encoding='utf-8')
    OUTPUT_RECEIPT.write_text(json.dumps(receipt, indent=1) + '\n',
                              encoding='utf-8')
    return document, receipt


# ------------------------------------------------------------- verification
def verify(doc_path=OUTPUT_DOC, receipt_path=OUTPUT_RECEIPT,
           blob_path=None):
    """Recompute everything from pinned inputs; refuse with named codes.

    blob_path: optional override path for the mesh blob (used by the tamper
    falsifiers); an override whose bytes do not match the pinned sha256
    refuses `mesh_blob_sha256_mismatch`."""
    arm, blob, pins, library = load_inputs()
    density = bone_density_entry(library)
    if blob_path is not None:
        require(sha256_file(blob_path)
                == INPUT_PINS['mesh_blob'][1],
                'mesh_blob_sha256_mismatch')
        blob = json.loads(pathlib.Path(blob_path).read_text('utf-8'))
    doc = json.loads(pathlib.Path(doc_path).read_text('utf-8'))
    receipt = json.loads(pathlib.Path(receipt_path).read_text('utf-8'))
    summary = ms.validate_material_state(doc)

    rows = {r['id']: r for r in doc['regions']}
    recomputed_total = 0.0
    for name in COUNTED_REGIONS:
        rec = blob['regions'][name]
        verts = rec['world_vertices_m']
        tris = rec['triangles']
        mom = moments_method_a(verts, tris)
        v_a = float(mom[0])
        mass = density['mean'] * v_a
        recomputed_total += mass
        row = rows[name]
        mv = row['rest_geometry']['material_volume']
        require(mv.get('density_source'), 'density_source_missing:' + name)
        require(abs(mv['mass_kg'] - mass) <= 1e-15 + 1e-12 * abs(mass),
                'mass_inventory_mismatch:' + name)
        check_rel(mv['volume_claim_m3'], v_a, TOL_CONTINUITY,
                  'volume_continuity_violation:' + name)
        _, com_v, I_v = inertia_from_moments(mom, density['mean'])
        check_mat(np.asarray(mv['inertia_about_own_com_kg_m2']), I_v, TOL_REL,
                  'inertia_tensor_mismatch:' + name)
        check_rel(float(np.linalg.norm(
            np.asarray(mv['com_m_world_default_pose']) - com_v)), 0.0,
            TOL_REL, 'com_mismatch:' + name)
    for name in SHELL_REGIONS:
        mv = rows[name]['rest_geometry']['material_volume']
        require(mv['volume_owned_mass_kg'] == 0.0,
                'shell_volume_claim_refused:' + name)
        require(mv['volume_claim_m3'] is None,
                'shell_volume_claim_refused:' + name)
    # counted total consistency with matter rows and receipt
    matter_mass = sum(m['mass_kg'] for m in doc['matter'])
    require(abs(matter_mass - recomputed_total) <= 1e-15,
            'counted_total_mismatch')
    require(abs(receipt['counted_total_kg'] - recomputed_total) <= 1e-15,
            'counted_total_mismatch:receipt')
    # density envelope on the emitted values (F4 bites here)
    for name in COUNTED_REGIONS:
        d = rows[name]['rest_geometry']['material_volume']['density_kg_m3']
        require(DENSITY_ENVELOPE_KG_M3[0] <= d <= DENSITY_ENVELOPE_KG_M3[1],
                'density_unit_scale_violation:' + name)
    # rotation covariance of the EMITTED tensor (F5 bites here)
    M = recomputed_total
    com = sum(np.asarray(rows[k]['rest_geometry']['material_volume']
                         ['com_m_world_default_pose'])
              * rows[k]['rest_geometry']['material_volume']['mass_kg']
              for k in COUNTED_REGIONS) / M
    I_doc = np.asarray(doc['provenance']['inertia_about_com_kg_m2'])
    I_com = np.zeros((3, 3))
    for k in COUNTED_REGIONS:
        mv = rows[k]['rest_geometry']['material_volume']
        I_i = np.asarray(mv['inertia_about_own_com_kg_m2'])
        d = np.asarray(mv['com_m_world_default_pose']) - com
        I_com += I_i + mv['mass_kg'] * (float(np.dot(d, d)) * np.eye(3)
                                        - np.outer(d, d))
    # rotation covariance of the EMITTED tensor runs FIRST so that a
    # frame-substitution tamper reports the frozen rotation_covariance_violation
    # code (F5) rather than the generic tensor mismatch
    for deg, axis in PROBE_ROTATIONS:
        R = rodrigues(deg, axis)
        first = np.zeros(3)
        per_region = []
        for k in COUNTED_REGIONS:
            rec = blob['regions'][k]
            v = np.asarray(rec['world_vertices_m'], dtype=np.float64) @ R.T
            m_k, com_k, I_k = inertia_method_b(v.tolist(), rec['triangles'],
                                               density['mean'])
            first += m_k * com_k
            per_region.append((m_k, com_k, I_k))
        com_rot = first / M
        agg_rot = np.zeros((3, 3))
        for m_k, com_k, I_k in per_region:
            d = com_k - com_rot
            agg_rot += I_k + m_k * (float(np.dot(d, d)) * np.eye(3)
                                    - np.outer(d, d))
        check_mat(agg_rot, R @ I_doc @ R.T, TOL_REL,
                  'rotation_covariance_violation')
    check_mat(I_doc, I_com, TOL_REL, 'inertia_tensor_mismatch:aggregate')
    return {'summary': summary, 'counted_total_kg': recomputed_total,
            'm01_total_kg': summary['total_mass_kg'],
            'com_m': [float(x) for x in com],
            'inertia_about_com_kg_m2': [[float(x) for x in r] for r in I_com]}


def main():
    action = sys.argv[1] if len(sys.argv) > 1 else 'derive'
    if action == 'derive':
        doc, receipt = derive()
        v = verify()
        print('derived material_volume_input.json  canonical_sha256=%s'
              % receipt['emitted_document']['canonical_sha256'])
        print('counted_total_kg=%.15g  m01_total_kg=%.15g'
              % (v['counted_total_kg'], v['m01_total_kg']))
        print('regions=%d shells=%d matter=%d bonds=%d'
              % (v['summary']['region_count'], v['summary']['shell_count'],
                 v['summary']['matter_count'], v['summary']['bond_count']))
        print('verification probes: %d green'
              % len(receipt['verification']['probes']))
        return 0
    if action == 'verify':
        v = verify()
        print('verify: counted_total_kg=%.15g m01_total_kg=%.15g'
              % (v['counted_total_kg'], v['m01_total_kg']))
        return 0
    raise SystemExit('unknown action: %s' % action)


if __name__ == '__main__':
    sys.exit(main())
