"""MAT2-M02 compiler: imported triangles -> explicit chimera.material_state.v1 regions.

Compiles the pinned monkey mesh (the seven admitted geom.macaque_arm.* VTP bone
assets, extracted at the recorded revision by build_pinned_inputs.py) and a
simple independent analytic shape (right tetrahedron + authored open plate)
into explicit M01 material regions, per the frozen preregistration
(PREREGISTRATION.md, this directory, including Amendment A1):

- unit check: source blob sha pins verified, declared source_units_to_m applied,
  metre-envelope magnitude gate (mm scale dropped -> refused).
- orientation: closed meshes need consistent directed edges + positive signed
  volume (outward); violations refused with named codes.
- closure: zero open edges -> volume region; open edges -> shell that is never
  treated as sealed (volume claim refused).
- shell thickness: declared only where authored with provenance (the plate);
  bone surfaces carry thickness null (none is used; none is invented).
- intersections: measured triangle-triangle between every region pair in the
  common world frame (default pose, admitted world_from_local transforms) and
  reported per pair; nothing hidden.
- region ownership: one matter id per source body mass, owned exactly once.
- subdivision vs semantics: triangle sets live in hashed mesh blobs; the
  material_state documents reference them by sha256 and never embed
  coordinates; visual mesh and physical mesh are the same identity-mapped
  triangle lists.

The VTP parser and mesh metrics are a credited, minimally-adapted copy of the
qualified tools/science_funnel/macaque_anatomy.py code at revision
eafbc15161ae10ae95b62d07d3f4878aefa34d9d (Amendment A1): the assigned base
lineage does not contain that module. Parser output is verified against the
admitted graph-pinned metrics (P2), which are the qualified numbers.
Validates every emitted document with the unmodified M01 validator
tools/monkey_campaign/contributions/MAT2-M01/material_state.py.
CPU-only (numpy + stdlib).
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys
import xml.etree.ElementTree as ET
from collections import Counter

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]                      # checkout root
M01_DIR = HERE.parent / 'MAT2-M01'
DATA_DIR = HERE / 'data'
MACAQUE_DIR = DATA_DIR / 'macaque_arm'
sys.path.insert(0, str(M01_DIR))

import material_state as ms                 # noqa: E402  (M01, unmodified)

BASE_REVISION = 'c4650f0a8a321353d5409ce6244aa5e6a2fe61b2'
INTAKE_REVISION = 'eafbc15161ae10ae95b62d07d3f4878aefa34d9d'
PORT = {'id': 'surface', 'protocol': 'material_contact',
        'unit': 'unitless_interface_id'}
# metre envelope per compiled region axis extent. mm-scaled sources must have
# strictly non-degenerate extents (bones are 3-D); the lower bound is what a
# wrongly applied x1e3 "m->mm" style scale would violate. Upper bound is what a
# dropped mm pin (x1e3 too large) violates.
ENVELOPE_UPPER_M = 0.6
ENVELOPE_LOWER_SCALED_M = 2e-4
GEOM_BODIES = ('sternum', 'clavicle', 'scapula', 'humerus', 'ulna',
               'radius', 'hand')


def require(condition, code):
    if not condition:
        raise ValueError(code)


def sha256_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def sha256_file(path):
    return sha256_bytes(pathlib.Path(path).read_bytes())


def bbox_of(verts):
    v = np.asarray(verts, dtype=np.float64)
    return [v.min(axis=0).tolist(), v.max(axis=0).tolist()]


# ------------------------------------------------- vendored qualified parser
# Adapted from tools/science_funnel/macaque_anatomy.py at revision
# eafbc15161ae10ae95b62d07d3f4878aefa34d9d (MIT project code). Kept behavior-
# identical for VTP polydata (weld + ear-clip triangulation + metrics); output
# is verified against the admitted graph-pinned metrics in the tests (P2).
def read_vtp(raw):
    root = ET.fromstring(raw)
    pieces = root.findall('./PolyData/Piece')
    require(len(pieces) == 1, 'unsupported_vtp_pieces')
    piece = pieces[0]
    require(all(int(piece.get(k, '0')) == 0
                for k in ('NumberOfVerts', 'NumberOfLines', 'NumberOfStrips')),
            'unsupported_vtp_primitives')

    def arr(node, ints=False):
        require(node is not None and node.get('format') == 'ascii',
                'unsupported_vtp_array')
        a = np.asarray([float(x) for x in node.text.split()], dtype=np.float64)
        require(np.isfinite(a).all(), 'invalid_numeric_field')
        if ints:
            require(np.equal(a, np.floor(a)).all(), 'nonintegral_index')
            a = a.astype(np.int64)
        return a

    source_xyz = arr(piece.find('./Points/DataArray')).reshape(-1, 3)
    require(len(source_xyz) == int(piece.get('NumberOfPoints')),
            'vtp_vertex_count')
    xyz, inverse = np.unique(source_xyz, axis=0, return_inverse=True)
    conn = arr(piece.find('./Polys/DataArray[@Name="connectivity"]'), True)
    ends = arr(piece.find('./Polys/DataArray[@Name="offsets"]'), True)
    require(len(ends) == int(piece.get('NumberOfPolys')) and len(ends) > 0
            and ends[-1] == len(conn)
            and np.diff(np.r_[0, ends]).min() >= 3, 'vtp_polygon_count')
    require(conn.min() >= 0 and conn.max() < len(source_xyz),
            'vtp_index_range')

    def triangulate_polygon(ids):
        # ear clipping projected onto the max-signed-area plane (source
        # polygons may be concave); identical to the qualified implementation
        poly = list(ids)
        normal = np.sum(np.cross(xyz[poly], np.roll(xyz[poly], -1, axis=0)),
                        axis=0)
        if np.linalg.norm(normal) == 0:
            return []
        uv = np.delete(xyz, int(np.argmax(np.abs(normal))), axis=1)

        def cross2(a, b, c):
            u = uv[b] - uv[a]
            v = uv[c] - uv[a]
            return u[0] * v[1] - u[1] * v[0]

        sign = 1 if sum(uv[a, 0] * uv[b, 1] - uv[b, 0] * uv[a, 1]
                        for a, b in zip(poly, np.roll(poly, -1))) > 0 else -1
        eps = np.finfo(float).eps * max(
            1., float(np.ptp(uv[poly], axis=0).max()) ** 2) * 32
        out = []
        while len(poly) > 3:
            found = False
            for i, b in enumerate(poly):
                a = poly[i - 1]
                c = poly[(i + 1) % len(poly)]
                turn = sign * cross2(a, b, c)
                if abs(turn) <= eps:
                    poly.pop(i)
                    found = True
                    break
                if turn < 0:
                    continue
                if any(sign * cross2(a, b, p) >= -eps
                       and sign * cross2(b, c, p) >= -eps
                       and sign * cross2(c, a, p) >= -eps
                       for p in poly if p not in (a, b, c)):
                    continue
                out.append((a, b, c))
                poly.pop(i)
                found = True
                break
            require(found, 'self_intersecting_or_untriangulable_polygon')
        if len(poly) == 3 and abs(cross2(*poly)) > eps:
            out.append(tuple(poly))
        return out

    tris = []
    start = 0
    for end in ends:
        mapped = inverse[conn[start:end]]
        start = end
        poly = []
        for v in mapped:
            if not poly or v != poly[-1]:
                poly.append(int(v))
        if len(poly) > 1 and poly[0] == poly[-1]:
            poly.pop()
        if len(set(poly)) < 3:
            continue
        require(len(set(poly)) == len(poly), 'self_touching_polygon')
        tris.extend(triangulate_polygon(poly))
    require(tris, 'empty_mesh_after_triangulation')
    return xyz, np.asarray(tris, dtype=np.uint32)


def mesh_metrics(xyz, tris):
    edges = Counter(tuple(sorted((int(a), int(b))))
                    for t in tris for a, b in zip(t, np.roll(t, -1)))
    a, b, c = xyz[tris[:, 0]], xyz[tris[:, 1]], xyz[tris[:, 2]]
    return {'vertices': len(xyz), 'triangles': len(tris),
            'bounds_m': [xyz.min(axis=0).tolist(), xyz.max(axis=0).tolist()],
            'surface_area_m2': float(
                np.linalg.norm(np.cross(b - a, c - a), axis=1).sum() / 2),
            'signed_volume_m3': float(
                np.einsum('ij,ij->i', a, np.cross(b, c)).sum() / 6),
            'edges_not_shared_twice': sum(v != 2 for v in edges.values())}


# --------------------------------------------------------------- mesh checks
def orientation_report(verts, tris):
    """Closure + winding consistency + signed volume, from the triangle list."""
    tris = np.asarray(tris, dtype=np.int64)
    a, b, c = verts[tris[:, 0]], verts[tris[:, 1]], verts[tris[:, 2]]
    signed_volume = float(np.einsum('ij,ij->i', a, np.cross(b, c)).sum() / 6.0)
    directed = {}
    undirected = {}
    for t in tris:
        for u, v in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            directed[(int(u), int(v))] = directed.get((int(u), int(v)), 0) + 1
            key = (int(u), int(v)) if u < v else (int(v), int(u))
            undirected[key] = undirected.get(key, 0) + 1
    open_edges = sum(1 for n in undirected.values() if n != 2)
    inconsistent = any(directed.get((v, u), 0) != 1 for (u, v) in directed)
    return {'open_edges': open_edges,
            'consistent_directed_edges': not inconsistent,
            'signed_volume_m3': signed_volume,
            'closed': open_edges == 0}


def classify(name, report):
    """Frozen decision rule: closed+consistent+positive -> region (volume);
    open -> shell (never sealed); inconsistent/negative closed -> REFUSED."""
    if report['closed']:
        require(report['consistent_directed_edges'],
                'mesh_orientation_inconsistent:' + name)
        require(report['signed_volume_m3'] > 0.0,
                'mesh_orientation_negative:' + name)
        return 'region', 'closed_outward_consistent'
    return 'shell', 'open_surface'


def require_volume_region(name, report):
    """The volume-region path: refuses open surfaces as never sealed (F1)."""
    require(report['closed'], 'open_surface_not_sealed:' + name +
            ':open_edges=' + str(report['open_edges']))
    require(report['consistent_directed_edges'],
            'mesh_orientation_inconsistent:' + name)
    require(report['signed_volume_m3'] > 0.0,
            'mesh_orientation_negative:' + name)
    return 'region', 'closed_outward_consistent'


def unit_gate(name, bounds, scale):
    """Compiled metre bounds must sit inside the magnitude envelope; a dropped
    mm pin (scale 1.0 on mm source data) is 1e3 too large and refuses here."""
    bounds = [np.asarray(bounds[0]), np.asarray(bounds[1])]
    ext = bounds[1] - bounds[0]
    lower = ENVELOPE_LOWER_SCALED_M if any(s < 1.0 for s in scale) else 0.0
    inside = bool(np.all(ext >= lower) and np.all(ext <= ENVELOPE_UPPER_M))
    require(inside, 'unit_scale_violation:' + name +
            ':extents_m=' + json.dumps(ext.tolist()))
    return {'envelope_m': [lower, ENVELOPE_UPPER_M], 'extents_m': ext.tolist(),
            'applied_source_units_to_m': list(scale), 'inside': inside}


def check_assignment(triangle_ids, triangle_count, region_id):
    """A material assignment may reference only triangle ids that exist in the
    imported subdivision (F3): nothing outside the mesh may carry material."""
    ids = list(triangle_ids)
    require(all(type(i) is int and 0 <= i < triangle_count for i in ids),
            'assignment_outside_subdivision:' + region_id)
    return True


def validate_region_geometry_source(geometry, region_id):
    """A region row must reference hashed imported geometry (mesh blob + pins)
    or a declared analytic definition; nothing else may become a region (F3)."""
    has_blob = ('mesh_blob_sha256' in geometry
                and 'source_sha256' in geometry
                and geometry.get('render_to_physics_mapping'))
    analytic = geometry.get('definition_kind') == 'authored_analytic'
    require(has_blob or analytic,
            'region_without_geometry_source:' + region_id)
    return True


# ------------------------------------------------- triangle-triangle overlap
def _tri_aabbs(verts, tris):
    t = np.asarray(tris, dtype=np.int64)
    p = verts[t]                                   # (n,3,3)
    return p.min(axis=1), p.max(axis=1)


def tri_tri_intersect(p1, q1, r1, p2, q2, r2):
    """Moller's triangle-triangle overlap test (3D), scalar port of the
    public-domain reference implementation."""
    def sub(a, b):
        return (a[0] - b[0], a[1] - b[1], a[2] - b[2])

    def cross(a, b):
        return (a[1] * b[2] - a[2] * b[1],
                a[2] * b[0] - a[0] * b[2],
                a[0] * b[1] - a[1] * b[0])

    def dot(a, b):
        return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]

    def compute_intervals(tri, dist):
        pts = []
        for i in range(3):
            a, b = tri[i], tri[(i + 1) % 3]
            da, db = dist[i], dist[(i + 1) % 3]
            if da * db < 0.0:
                t = da / (da - db)
                pts.append((a[0] + t * (b[0] - a[0]),
                            a[1] + t * (b[1] - a[1]),
                            a[2] + t * (b[2] - a[2])))
            elif da == 0.0:
                pts.append(a)
        uniq = []
        for pt in pts:
            if not any(all(abs(pt[k] - u[k]) < 1e-15 for k in range(3))
                       for u in uniq):
                uniq.append(pt)
        if len(uniq) != 2:
            return None
        return uniq[0], uniq[1]

    n1 = cross(sub(q1, p1), sub(r1, p1))
    n2 = cross(sub(q2, p2), sub(r2, p2))
    d2 = tuple(dot(sub(v, p1), n1) for v in (p2, q2, r2))
    if (d2[0] > 0 and d2[1] > 0 and d2[2] > 0) or \
       (d2[0] < 0 and d2[1] < 0 and d2[2] < 0):
        return False
    d1 = tuple(dot(sub(v, p2), n2) for v in (p1, q1, r1))
    if (d1[0] > 0 and d1[1] > 0 and d1[2] > 0) or \
       (d1[0] < 0 and d1[1] < 0 and d1[2] < 0):
        return False
    seg1 = compute_intervals((p2, q2, r2), d2)
    if seg1 is None:
        return False
    seg2 = compute_intervals((p1, q1, r1), d1)
    if seg2 is None:
        return False
    direction = cross(n1, n2)
    proj1 = sorted((dot(sub(s, p1), direction) for s in seg1))
    proj2 = sorted((dot(sub(s, p1), direction) for s in seg2))
    return proj1[0] <= proj2[1] and proj2[0] <= proj1[1]


def pair_intersections(verts_a, tris_a, verts_b, tris_b):
    """Count intersecting triangle pairs between two world-frame meshes."""
    verts_a = np.asarray(verts_a, dtype=np.float64)
    verts_b = np.asarray(verts_b, dtype=np.float64)
    tris_a = np.asarray(tris_a, dtype=np.int64)
    tris_b = np.asarray(tris_b, dtype=np.int64)
    lo_a, hi_a = _tri_aabbs(verts_a, tris_a)
    lo_b, hi_b = _tri_aabbs(verts_b, tris_b)
    count = 0
    for i in range(len(tris_a)):
        if np.any(lo_b > hi_a[i]) or np.any(hi_b < lo_a[i]):
            continue
        ta = verts_a[tris_a[i]]
        for j in range(len(tris_b)):
            if np.any(lo_b[j] > hi_a[i]) or np.any(hi_b[j] < lo_a[i]):
                continue
            tb = verts_b[tris_b[j]]
            if tri_tri_intersect(ta[0], ta[1], ta[2], tb[0], tb[1], tb[2]):
                count += 1
    return count


def intersection_matrix(world):
    """Every unordered region pair; AABB gate first, Moeller inside overlaps."""
    keys = sorted(world)
    report = []
    for i, ka in enumerate(keys):
        for kb in keys[i + 1:]:
            va, ta = world[ka]['world_vertices_m'], world[ka]['triangles']
            vb, tb = world[kb]['world_vertices_m'], world[kb]['triangles']
            ba, bb = bbox_of(va), bbox_of(vb)
            aabb_overlap = not (np.any(np.asarray(ba[1]) < np.asarray(bb[0]))
                                or np.any(np.asarray(bb[1]) < np.asarray(ba[0])))
            n = pair_intersections(va, ta, vb, tb) if aabb_overlap else 0
            report.append({'pair': [ka, kb], 'aabb_overlap': bool(aabb_overlap),
                           'triangle_pairs_intersecting': int(n),
                           'intersecting': bool(n > 0)})
    return report


def aabb_gap(bounds_a, bounds_b):
    """Separation measure between two AABBs: positive iff disjoint, equal to
    the largest per-axis separation."""
    a0, a1 = np.asarray(bounds_a[0]), np.asarray(bounds_a[1])
    b0, b1 = np.asarray(bounds_b[0]), np.asarray(bounds_b[1])
    return float(max((b0 - a1).max(), (a0 - b1).max()))


# ------------------------------------------------------------ joints/bonds
def source_bonds(model):
    """Explicit bonds between geometry-bearing bodies along source joint chains.
    Kinematic declaration only: reaction forces are NOT qualified. Chain
    provenance is returned separately (the M01 schema keeps bond rows minimal)."""
    bodies = {b['name']: b for b in model['bodies']}
    bonds = []
    skipped = []
    chains = {}
    for bname in sorted(bodies):
        body = bodies[bname]
        if not body['geometry']:
            continue
        cursor, chain = bname, []
        while True:
            joint = bodies[cursor]['joint']
            if joint is None:
                skipped.append({'body': bname, 'chain': list(chain),
                                'reason': 'reached ground (no material region)'})
                break
            chain.append(joint['name'])
            parent = joint['parent']
            if bodies[parent]['geometry']:
                bond_id = 'bond_%s_%s_joint' % (parent, bname)
                bonds.append({
                    'id': bond_id,
                    'status': 'source_declared',
                    'endpoints': [{'region_id': parent, 'port': 'surface'},
                                  {'region_id': bname, 'port': 'surface'}],
                    'transfers': 'force_moment',
                })
                chains[bond_id] = ('source joint chain '
                                   + ' -> '.join(reversed(chain))
                                   + ' (monkeyArm_current.osim); declared '
                                   'kinematic connection, NOT a qualified '
                                   'reaction force')
                break
            cursor = parent
    return bonds, skipped, chains


# --------------------------------------------------------------- mesh blobs
def region_mesh_record(key, verts_m, world_vertices_m, tris, source_path,
                       source_sha, scale, frame):
    rep = orientation_report(verts_m, tris)
    return {'key': key, 'frame': frame, 'source_path': source_path,
            'source_sha256': source_sha, 'source_units_to_m': list(scale),
            'vertices_m': [list(map(float, v)) for v in np.asarray(verts_m)],
            'world_vertices_m': [list(map(float, v))
                                 for v in np.asarray(world_vertices_m)],
            'triangles': [list(map(int, t)) for t in np.asarray(tris)],
            'visual_mesh': 'identity (same triangle list as physical mesh)',
            'physical_mesh': 'identity (same triangle list as visual mesh)',
            'orientation_report': rep}


def build_region_rows(keys, blob, doc_blobs_sha, metrics_map, thickness_map):
    rows = []
    for key in sorted(keys):
        rec = blob['regions'][key]
        met = metrics_map[key]
        kind, closure = classify(key, rec['orientation_report'])
        thickness, thickness_prov = thickness_map.get(
            key,
            (None, 'no source shell thickness exists for this surface; '
                   'none used, none invented'))
        geometry = {
            'unit': 'm',
            'frame': rec['frame'],
            'source_path': rec['source_path'],
            'source_sha256': rec['source_sha256'],
            'source_units_to_m': rec['source_units_to_m'],
            'mesh_blob': doc_blobs_sha['file'],
            'mesh_blob_sha256': doc_blobs_sha['sha256'],
            'mesh_blob_region_key': key,
            'vertex_count': met['vertices'],
            'triangle_count': met['triangles'],
            'bounds_m': met['bounds_m'],
            'surface_area_m2': met['surface_area_m2'],
            'edges_not_shared_twice': met['edges_not_shared_twice'],
            'closure': closure,
            'open_edge_count': rec['orientation_report']['open_edges'],
            'orientation': ('outward_consistent'
                            if closure == 'closed_outward_consistent'
                            else 'open_surface_unoriented'),
            'signed_volume_m3': (rec['orientation_report']['signed_volume_m3']
                                 if closure == 'closed_outward_consistent'
                                 else None),
            'volume_claim_m3': (rec['orientation_report']['signed_volume_m3']
                                if kind == 'region' else None),
            'shell_thickness_m': thickness,
            'shell_thickness_provenance': thickness_prov,
            'render_to_physics_mapping': {
                'visual_mesh': 'mesh_blob triangle list (identity)',
                'physical_mesh': 'mesh_blob triangle list (identity)',
                'mapping': 'identity',
                'visual_triangle_count': met['triangles'],
                'physical_triangle_count': met['triangles'],
            },
        }
        validate_region_geometry_source(geometry, key)
        check_assignment(range(met['triangles']), met['triangles'], key)
        rows.append({
            'id': key,
            'kind': kind,
            'parent': None,
            'rest_geometry': geometry,
            'current_geometry': {'equal_to': 'rest_geometry',
                                 'reason': 'revision 1; no solver exists'},
            'matter_claims': [{'matter_id': 'mass_' + key, 'role': 'owner'}],
            'ports': [dict(PORT)],
            'sources': [rec['source_path']],
        })
    return rows


# ----------------------------------------------------------- independent shape
def authored_shapes(arm_world_bbox):
    """The simple independent shape: analytic right tetrahedron (volume region)
    plus an authored open plate (shell with explicit thickness). Authored in
    metres; placed disjoint from the measured arm AABB by construction."""
    amin = np.asarray(arm_world_bbox[0])
    amax = np.asarray(arm_world_bbox[1])
    tetra_local = np.array([[0.0, 0.0, 0.0], [0.1, 0.0, 0.0],
                            [0.0, 0.1, 0.0], [0.0, 0.0, 0.1]])
    tetra_tris = [[0, 2, 1], [0, 1, 3], [0, 3, 2], [1, 2, 3]]
    tetra_offset = np.array([float(amax[0]) + 0.10,
                             float(amin[1]), float(amin[2])])
    plate_local = np.array([[0.0, 0.0, 0.0], [0.2, 0.0, 0.0],
                            [0.2, 0.1, 0.0], [0.0, 0.1, 0.0]])
    plate_tris = [[0, 1, 2], [0, 2, 3]]
    plate_offset = np.array([float((amin[0] + amax[0]) / 2) - 0.1,
                             float((amin[1] + amax[1]) / 2) - 0.05,
                             float(amax[2]) + 0.08])
    return {
        'tetra': {'verts': tetra_local + tetra_offset, 'tris': tetra_tris,
                  'offset': tetra_offset.tolist()},
        'plate': {'verts': plate_local + plate_offset, 'tris': plate_tris,
                  'offset': plate_offset.tolist()},
    }


# ------------------------------------------------------------------- masses
def mass_rows(model):
    rows = []
    for b in sorted(model['bodies'], key=lambda b: b['name']):
        if not b['geometry']:
            continue
        rows.append({'id': 'mass_' + b['name'], 'mass_kg': b['mass_kg'],
                     'provenance': 'monkeyArm_current.osim Body mass for body "'
                                   + b['name'] + '" (admitted model row, '
                                   'extracted at revision ' + INTAKE_REVISION
                                   + '); mass_scope: ' + b['mass_scope']})
    return rows


def independent_mass_rows():
    return [
        {'id': 'mass_tetra', 'mass_kg': 0.120,
         'provenance': 'authored fixture mass at chosen fidelity (no measured '
                       'source); explicit, single-owner'},
        {'id': 'mass_plate', 'mass_kg': 0.020,
         'provenance': 'authored fixture mass at chosen fidelity (no measured '
                       'source); explicit, single-owner'},
    ]


ABSENT_ANATOMY = [
    'no skin or fat surface geometry exists in the pinned source; none compiled',
    'no muscle volume geometry: the 39 source muscles are 1D path points only',
    'no organs or internal tissue surfaces; the compiled regions are bone '
    'surface segments only',
    'no layer thicknesses: bone surfaces declare shell_thickness_m null; '
    'declaring one would fabricate tissue',
    'no material directions and no pressure/deformation laws are declared; '
    'none is inferred from geometry (deferred to downstream cards)',
]


def provenance_block(pins, extra):
    prov = {
        'base_revision': BASE_REVISION,
        'source_receipt_revision': pins['source_receipt']['revision'],
        'extraction_revision': INTAKE_REVISION,
        'source_license': pins['source_receipt']['license'],
        'data_root': 'tools/monkey_campaign/contributions/MAT2-M02/data/'
                     'macaque_arm (byte-verified extraction of '
                     'tools/science_funnel/data/macaque_arm at the recorded '
                     'revision)',
        'unit_convention': 'source VTP geometry is millimetre-scaled; admitted '
                           'graph pins source_units_to_m [0.001, 0.001, 0.001]'
                           ' (data/graph_pins.json); compiled geometry is '
                           'metres',
        'tools': {
            'compiler': 'tools/monkey_campaign/contributions/MAT2-M02/'
                        'compile_material_regions.py',
            'compiler_sha256': sha256_file(HERE / 'compile_material_regions.py'),
            'input_builder': 'tools/monkey_campaign/contributions/MAT2-M02/'
                             'build_pinned_inputs.py',
            'schema_authority': 'tools/monkey_campaign/contributions/MAT2-M01/'
                                'material_state.py (unmodified M01 validator)',
            'schema_authority_sha256': sha256_file(M01_DIR / 'material_state.py'),
            'vtp_parser': 'vendored credited adaptation of qualified '
                          'tools/science_funnel/macaque_anatomy.py read_vtp + '
                          'mesh_metrics at revision ' + INTAKE_REVISION
                          + ' (Amendment A1); output verified against the '
                          'admitted graph-pinned metrics',
        },
        'decisions': [
            'region ids reuse the source body names (stable pinned identities)',
            'kinds follow the frozen closure rule: closed outward-consistent '
            'meshes are regions; open meshes (scapula, hand) are shells and '
            'carry no volume claim',
            'bonds are the source-declared OpenSim joint chains between '
            'geometry-bearing bodies; containment does not exist here (all '
            'regions are roots) and no contact is implied by proximity',
            'no directions or laws are compiled: none can be inferred from '
            'surface geometry without inventing material structure',
            'measured region intersections are reported in intersection_check; '
            'region ownership keeps every matter id owned exactly once '
            'regardless of overlap',
            'self-intersection within one source mesh is NOT claimed either '
            'way (source qualification limit carried from the graph)',
        ],
        'absent_internal_anatomy': list(ABSENT_ANATOMY),
    }
    prov.update(extra)
    return prov


def main():
    receipt_log = {'base_revision': BASE_REVISION,
                   'extraction_revision': INTAKE_REVISION}
    pins = json.loads((DATA_DIR / 'graph_pins.json').read_text('utf-8'))
    require(pins['extraction_revision'] == INTAKE_REVISION,
            'graph_pins_revision_drift')
    model = pins['model']
    geom_pins = pins['geom_pins']
    # 1. parse pinned meshes with the vendored qualified parser; verify pins
    blob = {'kind': 'mat2_m02_mesh_blob', 'schema': 'chimera.mesh_blob.v1',
            'frame_note': 'vertices_m: body-frame metres (rest); '
                          'world_vertices_m: default-pose world metres '
                          '(render + intersection frame, admitted '
                          'world_from_local transforms)',
            'regions': {}}
    metrics_map = {}
    world = {}
    for name in GEOM_BODIES:
        pin = geom_pins[name]
        geom = pin['asset']
        raw = (MACAQUE_DIR / geom['path']).read_bytes()
        require(sha256_bytes(raw) == geom['sha256'],
                'geometry_pin_drift:' + geom['path'])
        xyz, tris = read_vtp(raw)
        xyz = xyz * np.asarray(geom['source_units_to_m'])
        met = mesh_metrics(xyz, tris)
        # parser output must reproduce the admitted qualified metrics (P2)
        gmet = pin['metrics']
        require(met['triangles'] == gmet['triangles']
                and met['vertices'] == gmet['vertices']
                and met['edges_not_shared_twice']
                == gmet['edges_not_shared_twice'],
                'graph_metric_drift:counts:' + name)
        require(abs(met['signed_volume_m3'] - gmet['signed_volume_m3'])
                <= 1e-9 * abs(gmet['signed_volume_m3']),
                'graph_metric_drift:volume:' + name)
        require(abs(met['surface_area_m2'] - gmet['surface_area_m2'])
                <= 1e-9 * gmet['surface_area_m2'],
                'graph_metric_drift:area:' + name)
        metrics_map[name] = met
        body_row = next(b for b in model['bodies'] if b['name'] == name)
        T = np.asarray(pins['body_frames'][name], dtype=np.float64)
        world_xyz = xyz @ T[:3, :3].T + T[:3, 3]
        blob['regions'][name] = region_mesh_record(
            name, xyz, world_xyz, tris, 'macaque_arm/' + geom['path'],
            geom['sha256'], geom['source_units_to_m'], 'body:' + name)
        world[name] = blob['regions'][name]
        unit_gate(name, met['bounds_m'], geom['source_units_to_m'])
        receipt_log.setdefault('graph_pin_verification', []).append(
            {'region': name, 'graph_id': pin['graph_id'],
             'sha256': geom['sha256'], 'metrics_match': True})
    # 2. independent shape, placed disjoint from the measured arm AABB
    arm_bbox = bbox_of(np.vstack([np.asarray(world[k]['world_vertices_m'])
                                  for k in GEOM_BODIES]))
    shapes = authored_shapes(arm_bbox)
    for key in ('tetra', 'plate'):
        verts = shapes[key]['verts']
        tris = shapes[key]['tris']
        met = mesh_metrics(verts, np.asarray(tris, dtype=np.uint32))
        metrics_map[key] = met
        unit_gate(key, met['bounds_m'], [1.0, 1.0, 1.0])
        analytic_sha = sha256_bytes(np.ascontiguousarray(verts).tobytes()
                                    + np.ascontiguousarray(
                                        np.asarray(tris, dtype=np.int64))
                                    .tobytes())
        blob['regions'][key] = region_mesh_record(
            key, verts, verts, tris,
            'authored analytic shape (independent of macaque data)',
            'authored:' + analytic_sha, [1.0, 1.0, 1.0], 'world')
        world[key] = blob['regions'][key]
    blob_path = HERE / 'monkey_arm_independent_meshes.json'
    blob_path.write_text(json.dumps(blob, indent=1, ensure_ascii=False) + '\n',
                         encoding='utf-8')
    blob_sha = sha256_file(blob_path)
    doc_blobs_sha = {'file': blob_path.name, 'sha256': blob_sha}
    # 3. placement margins (frozen minimums)
    gaps_to_arm = []
    for key in ('tetra', 'plate'):
        gap = aabb_gap(metrics_map[key]['bounds_m'], arm_bbox)
        gaps_to_arm.append({'region': key, 'gap_m': gap})
        require(gap >= 0.05, 'placement_margin_violation:' + key)
    gap_tetra_plate = aabb_gap(metrics_map['tetra']['bounds_m'],
                               metrics_map['plate']['bounds_m'])
    require(gap_tetra_plate >= 0.02, 'placement_margin_violation:tetra_plate')
    # 4. intersections, every pair inside each object + across objects
    arm_matrix = intersection_matrix({k: world[k] for k in GEOM_BODIES})
    indep_matrix = intersection_matrix({k: world[k] for k in ('tetra', 'plate')})
    cross_matrix = intersection_matrix(
        {**{k: world[k] for k in GEOM_BODIES}, 'tetra': world['tetra'],
         'plate': world['plate']})
    cross_external = [r for r in cross_matrix
                      if r['pair'][0] in ('tetra', 'plate')
                      or r['pair'][1] in ('tetra', 'plate')]
    require(all(not r['intersecting'] for r in indep_matrix + cross_external),
            'independent_shape_overlaps_compiled_regions')
    # 5. documents
    arm_bonds, skipped_chains, bond_chains = source_bonds(model)
    thickness_map = {'plate': (0.002,
                               'authored at chosen fidelity (independent shape '
                               'demonstrator); explicit declaration with '
                               'provenance')}
    arm_doc = {
        'schema': 'chimera.material_state.v1',
        'revision': 1,
        'object_id': 'monkey-arm-regions',
        'provenance': provenance_block(pins, {
            'mesh_blob': doc_blobs_sha,
            'graph_pin_extraction': 'data/graph_pins.json (sha256 '
                                    + sha256_file(DATA_DIR / 'graph_pins.json')
                                    + ')',
            'intersection_check': {
                'frame': 'world at default pose (admitted world_from_local)',
                'pairs': arm_matrix,
                'intersecting_pair_count':
                    sum(1 for r in arm_matrix if r['intersecting']),
                'note': 'measured overlaps between body-surface segments; '
                        'segment masses stay single-owned regardless'},
            'joint_chains_without_region': skipped_chains,
            'source_bond_chains': bond_chains,
        }),
        'regions': build_region_rows(GEOM_BODIES, blob, doc_blobs_sha,
                                     metrics_map, thickness_map),
        'matter': mass_rows(model),
        'directions': [],
        'laws': [],
        'contacts': [],
        'bonds': arm_bonds,
    }
    indep_doc = {
        'schema': 'chimera.material_state.v1',
        'revision': 1,
        'object_id': 'independent-shape-regions',
        'provenance': provenance_block(pins, {
            'independent_shape': {
                'definition': 'authored analytic right tetrahedron (0.1 m '
                              'orthogonal edges) + authored open square plate '
                              '(0.2 m x 0.1 m, authored thickness 0.002 m)',
                'independence': 'derived from no macaque or repository '
                                'geometry; exact analytic values are the '
                                'preregistered predictions',
                'placement_offsets_m': {'tetra': shapes['tetra']['offset'],
                                        'plate': shapes['plate']['offset']},
                'measured_gaps_m': {'to_arm': gaps_to_arm,
                                    'tetra_plate': gap_tetra_plate},
            },
            'mesh_blob': doc_blobs_sha,
            'intersection_check': {
                'frame': 'world',
                'pairs': indep_matrix + cross_external,
                'intersecting_pair_count': 0,
                'note': 'independent shape disjoint from every compiled '
                        'region (frozen placement margins)'},
        }),
        'regions': build_region_rows(('tetra', 'plate'), blob, doc_blobs_sha,
                                     metrics_map, thickness_map),
        'matter': independent_mass_rows(),
        'directions': [],
        'laws': [],
        'contacts': [],
        'bonds': [],
    }
    for name, doc in (('monkey_arm_regions.json', arm_doc),
                      ('independent_shape_regions.json', indep_doc)):
        (HERE / name).write_text(
            json.dumps(doc, indent=1, ensure_ascii=False) + '\n',
            encoding='utf-8')
        ms.validate_material_state(doc)   # refuse invalid output, always
    # 6. receipt
    receipt_log['objects'] = []
    for doc in (arm_doc, indep_doc):
        summary = ms.validate_material_state(doc)
        once = ms.total_mass_once(doc)
        receipt_log['objects'].append(
            {'object_id': summary['object_id'],
             'canonical_sha256': ms.digest(ms.canonical(doc)),
             'region_count': summary['region_count'],
             'shell_count': summary['shell_count'],
             'matter_count': summary['matter_count'],
             'bond_count': summary['bond_count'],
             'total_mass_kg': summary['total_mass_kg'],
             'total_mass_once_kg': once,
             'region_ids': summary['region_ids']})
    receipt_log['mass_oracle'] = {
        'arm_total_once_kg': receipt_log['objects'][0]['total_mass_once_kg'],
        'independent_total_once_kg': receipt_log['objects'][1]
        ['total_mass_once_kg']}
    receipt_log['placement_gaps_m'] = {'to_arm': gaps_to_arm,
                                       'tetra_plate': gap_tetra_plate}
    receipt_log['mesh_blob'] = doc_blobs_sha
    (HERE / 'compile_receipt.json').write_text(
        json.dumps(receipt_log, indent=1, ensure_ascii=False) + '\n',
        encoding='utf-8')
    for obj in receipt_log['objects']:
        print('object:', obj['object_id'], '| regions:', obj['region_count'],
              '| shells:', obj['shell_count'], '| bonds:', obj['bond_count'],
              '| mass once:', obj['total_mass_once_kg'], 'kg')
    print('intersecting arm pairs:',
          sum(1 for r in arm_matrix if r['intersecting']), 'of', len(arm_matrix))
    print('mesh blob:', blob_path.name, blob_sha[:16])
    print('wrote monkey_arm_regions.json independent_shape_regions.json'
          ' compile_receipt.json')


if __name__ == '__main__':
    main()
