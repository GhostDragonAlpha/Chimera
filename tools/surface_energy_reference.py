"""surface_energy_reference.py -- THE CONSTANT-GAMMA SURFACE-ENERGY REFERENCE. (G01)

The law of record is docs/THE_SURFACE_ENERGY_TRANSLATION.md (ASTRA, 2026-09-06):

    For nondegenerate triangles with constant, nonnegative interfacial energy
    density gamma, the current-area energy U = sum_t gamma_t A_t has
    conservative vertex forces obtained from its exact geometric derivative.

        grad_a A = cross(b - c, n) / 2        (cyclic in a, b, c)
        n = cross(b - a, c - a) / |cross(b - a, c - a)|   from CURRENT geometry

    face-corner force f = -gamma * grad A; vertex forces sum incident corners.

DISTINCTION FROM EXISTING CODE (the preregistration demands this be explicit):
`tools/ca_triangle.py::area_grads` implements a DIFFERENT law -- the SIGNED area
against a FROZEN import normal n0 (a rest-area/strain experiment). This module
implements the CURRENT-normal UNSIGNED-area law: the normal is recomputed from
current geometry on every evaluation. A frozen import normal is a different
projected-area law; the negative controls in surface_energy_checks.py prove the
instrument distinguishes them. Neither file redefines the other.

numpy + stdlib only. Units: positions in meters (any consistent unit works --
energies scale as unit^2 x gamma, forces as unit x gamma); gamma in energy/area
(J/m^2 for meters). Dimensionless fixtures use gamma = 1.

Public API:
    evaluate_surface(positions, faces, gamma)  -> Evaluation
    build_vertex_corner_adjacency(faces, vertex_count) -> (offsets, corner_idx)
    triangle_metric(rest_positions, positions, faces) -> MetricResult

Invalid input raises InvalidSurface with a named reason. Nothing is silently
dropped, no force silently zeroed, no face repaired.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

__all__ = [
    "InvalidSurface", "RejectionReason", "Evaluation", "MetricResult",
    "evaluate_surface", "build_vertex_corner_adjacency", "triangle_metric",
]

# Double-precision epsilon and the preregistered numerical allowances (ASTRA,
# THE_SURFACE_ENERGY_TRANSLATION.md): FD h = e^(1/3); derivative error limit
# 256*e^(2/3); algebraic invariance limit 512*e; degeneracy floor 64*e*maxedge^2.
EPS = float(np.finfo(np.float64).eps)
FD_H = EPS ** (1.0 / 3.0)
DERIV_LIMIT = 256.0 * EPS ** (2.0 / 3.0)
INVARIANCE_LIMIT = 512.0 * EPS
DEGENERACY_FLOOR = 64.0 * EPS


class InvalidSurface(ValueError):
    """A named refusal. The reason is machine-readable; the message is human text.

    The reference never silently drops a face, never creates a zero force to
    hide invalid geometry, never repairs a pose. A refusal is the honest output
    for input outside the numerical domain.
    """

    def __init__(self, reason: "RejectionReason", message: str):
        super().__init__(message)
        self.reason = reason
        self.message = message


class RejectionReason:
    """Stable machine-readable reason strings (the falsifiers assert on these)."""
    MALFORMED_INDICES = "malformed_indices"
    NONFINITE_POSITIONS = "nonfinite_positions"
    NONFINITE_GAMMA = "nonfinite_gamma"
    NEGATIVE_GAMMA = "negative_gamma"
    EMPTY_FACES = "empty_faces"
    EMPTY_POSITIONS = "empty_positions"
    BAD_SHAPE = "bad_shape"
    REPEATED_VERTEX = "repeated_vertex_face"
    COLLAPSED_TRIANGLE = "collapsed_triangle"
    NEAR_DEGENERATE = "near_degenerate_triangle"
    BAD_DTYPE = "bad_dtype"


def _as_positions(positions) -> np.ndarray:
    """Validate + normalize the positions array. Float64 in, (nV,3) out."""
    pos = np.asarray(positions)
    if pos.dtype.kind not in "fiu":
        raise InvalidSurface(RejectionReason.BAD_DTYPE,
                             f"positions dtype {pos.dtype} is not numeric")
    if pos.dtype != np.float64:
        pos = pos.astype(np.float64)
    if pos.ndim != 2 or pos.shape[1] != 3:
        raise InvalidSurface(RejectionReason.BAD_SHAPE,
                             f"positions must be (n,3); got {pos.shape}")
    if not np.all(np.isfinite(pos)):
        raise InvalidSurface(RejectionReason.NONFINITE_POSITIONS,
                             "positions contain NaN or infinity")
    if pos.shape[0] == 0:
        raise InvalidSurface(RejectionReason.EMPTY_POSITIONS,
                             "positions is empty (no vertices)")
    return pos


def _as_faces(faces, n_vertices: int) -> np.ndarray:
    """Validate + normalize the faces array. Int in, (nF,3) out. No face dropped."""
    faces_arr = np.asarray(faces)
    if faces_arr.dtype.kind not in "iu":
        raise InvalidSurface(RejectionReason.BAD_DTYPE,
                             f"faces dtype {faces_arr.dtype} is not integral")
    if faces_arr.dtype != np.int64:
        faces_arr = faces_arr.astype(np.int64)
    if faces_arr.ndim != 2 or faces_arr.shape[1] != 3:
        raise InvalidSurface(RejectionReason.BAD_SHAPE,
                             f"faces must be (n,3); got {faces_arr.shape}")
    if faces_arr.shape[0] == 0:
        raise InvalidSurface(RejectionReason.EMPTY_FACES,
                             "faces is empty (no triangles)")
    if faces_arr.min() < 0 or faces_arr.max() >= n_vertices:
        raise InvalidSurface(RejectionReason.MALFORMED_INDICES,
                             f"face index out of [0,{n_vertices}) "
                             f"(min {faces_arr.min()}, max {faces_arr.max()})")
    dup = (faces_arr[:, 0] == faces_arr[:, 1]) | \
          (faces_arr[:, 1] == faces_arr[:, 2]) | \
          (faces_arr[:, 0] == faces_arr[:, 2])
    if np.any(dup):
        i = int(np.argmax(dup))
        raise InvalidSurface(RejectionReason.REPEATED_VERTEX,
                             f"face {i} repeats a vertex "
                             f"({faces_arr[i].tolist()})")
    return faces_arr


def _as_gamma(gamma, n_faces: int) -> np.ndarray:
    """Validate + broadcast gamma. Nonnegative scalar or per-face vector."""
    gam = np.asarray(gamma, dtype=np.float64)
    if not np.all(np.isfinite(gam)):
        raise InvalidSurface(RejectionReason.NONFINITE_GAMMA,
                             "gamma contains NaN or infinity")
    if np.any(gam < 0.0):
        raise InvalidSurface(RejectionReason.NEGATIVE_GAMMA,
                             f"gamma must be nonnegative; got {gam}")
    if gam.ndim == 0:
        return np.full(n_faces, float(gam))
    if gam.ndim == 1 and gam.shape[0] == n_faces:
        return gam
    raise InvalidSurface(RejectionReason.BAD_SHAPE,
                         f"gamma must be scalar or per-face ({n_faces},); "
                         f"got shape {gam.shape}")


@dataclass
class Evaluation:
    """One evaluate_surface() result. All arrays are fresh; nothing aliases input."""
    energy: float                    # U = sum gamma_t A_t   [gamma * unit^2]
    areas: np.ndarray                # (nF,) current unsigned areas [unit^2]
    face_corner_forces: np.ndarray   # (nF,3,3) -gamma*gradA per face corner [gamma*unit]
    vertex_forces: np.ndarray        # (nV,3) corner sums gathered per vertex [gamma*unit]
    normals: np.ndarray              # (nF,3) unit normals from CURRENT geometry
    gamma: np.ndarray                # (nF,) the validated per-face gamma
    n_vertices: int
    n_faces: int


def evaluate_surface(positions, faces, gamma) -> Evaluation:
    """U = sum_t gamma_t A_t and its exact vertex gradient, current geometry.

    parameters
    ----------
    positions : (nV,3) float (m). NaN/inf refused.
    faces     : (nF,3) int. Out-of-range, repeated-vertex faces refused.
    gamma     : nonnegative scalar or (nF,) (J/m^2). Negative/nonfinite refused.

    returns
    -------
    Evaluation with energy, per-face areas, per-face-corner forces
    (-gamma * grad A, grad_a A = cross(b-c, n)/2 cyclic), and vertex forces
    gathered from corners. Degenerate faces (|cross| == 0 exactly) and
    near-degenerate faces (|cross| <= 64*e*max_edge^2) are REFUSED, not patched.
    """
    pos = _as_positions(positions)
    tri = _as_faces(faces, pos.shape[0])
    gam = _as_gamma(gamma, tri.shape[0])

    a = pos[tri[:, 0]]
    b = pos[tri[:, 1]]
    c = pos[tri[:, 2]]
    cross = np.cross(b - a, c - a)                      # (nF,3)
    cross_mag = np.linalg.norm(cross, axis=1)
    edge_sq = np.maximum(np.maximum(
        np.sum((b - a) ** 2, axis=1), np.sum((c - b) ** 2, axis=1)),
        np.sum((a - c) ** 2, axis=1))
    floor = DEGENERACY_FLOOR * np.maximum(edge_sq, np.finfo(np.float64).tiny)

    if np.any(cross_mag <= floor):
        i = int(np.argmax(cross_mag <= floor))
        raise InvalidSurface(
            RejectionReason.NEAR_DEGENERATE if cross_mag[i] > 0.0
            else RejectionReason.COLLAPSED_TRIANGLE,
            f"face {i} has |cross(b-a, c-a)| = {cross_mag[i]:.3e} <= "
            f"degeneracy floor {floor[i]:.3e} (64*e*max_edge^2)")

    areas = 0.5 * cross_mag
    normals = cross / cross_mag[:, None]

    # EXACT geometric derivative of the UNSIGNED current area, current normal:
    #   grad_a A = cross(b - c, n)/2   (cyclic: b<-c-a, c<-a-b)
    # Sign convention cross-check for a flat CCW triangle in z=0, n=+z:
    #   grad_a A = cross(b-c, z)/2. With a=(0,0), b=(1,0), c=(0,1):
    #   b-c=(1,-1), cross((1,-1,0),(0,0,1)) = (-1,-1,0) -> dA/da_x = -1/2,
    #   dA/da_y = -1/2. Moving `a` by (+h,+h) changes A by  (-h-h)/2 ... direct
    #   check: A(a=(s,s)) = |cross(b-a, c-a)|/2 with b=(1,0), c=(0,1):
    #   b-a = (1-s, -s), c-a = (-s, 1-s); cross_z = (1-s)^2 - s^2 = 1-2s.
    #   A = (1-2s)/2, dA/ds = -1 = (-1/2) + (-1/2). MATCHES. The force is the
    #   NEGATIVE gradient (conservative, shrinks area).
    grad_a = np.cross(b - c, normals) * 0.5
    grad_b = np.cross(c - a, normals) * 0.5
    grad_c = np.cross(a - b, normals) * 0.5
    face_corner_forces = -(gam[:, None, None] *
                           np.stack([grad_a, grad_b, grad_c], axis=1))

    # Deterministic gather: vertex forces from face corners via CSR adjacency.
    # reduceat sums corner_indices[offsets[v]:offsets[v+1]] per vertex; the CSR
    # construction guarantees offsets[-1] == 3*nF, and vertex 0 always owns at
    # least one corner for a valid mesh, so offsets[0] == 0 starts segment 0.
    offsets, corner_idx = build_vertex_corner_adjacency(tri, pos.shape[0])
    flat = face_corner_forces.reshape(-1, 3)            # (3*nF, 3) face-major
    vertex_forces = np.zeros_like(pos)
    if offsets[-1] == flat.shape[0] and np.all(np.diff(offsets) > 0):
        # GATHER BUG, found by F8 (2026-09-06): reduceat was applied to the
        # FACE-MAJOR rows with VERTEX-MAJOR offsets -- every vertex bucket
        # summed the wrong rows (O(1) wrong forces; the single-triangle smoke
        # test could not see it because face-major == vertex-major there).
        # corner_idx reorders rows into the CSR's vertex-major corner order,
        # which is what the offsets segment. The FD check (F1) caught the
        # same bug independently: finite differences measure the ENERGY,
        # which never touches the gather.
        np.add.reduceat(flat[corner_idx], offsets[:-1], axis=0, out=vertex_forces)
    else:
        # Empty-vertex case (a declared vertex no face references): reduceat
        # cannot express empty segments, so fall back to explicit binning.
        # STILL deterministic: same CSR order, same segment boundaries.
        corner_of = np.repeat(np.arange(pos.shape[0]), np.diff(offsets))
        np.add.at(vertex_forces, corner_of, flat[corner_idx])

    energy = float(np.sum(gam * areas))
    return Evaluation(energy=energy, areas=areas,
                      face_corner_forces=face_corner_forces,
                      vertex_forces=vertex_forces, normals=normals,
                      gamma=gam, n_vertices=pos.shape[0], n_faces=tri.shape[0])


def build_vertex_corner_adjacency(faces, vertex_count: int):
    """Fixed-order vertex->corner CSR for deterministic GPU gather.

    parameters
    ----------
    faces        : (nF,3) int, validated (in range, no repeated vertex).
    vertex_count : int, the declared nV (faces may not reference every vertex).

    returns
    -------
    (offsets, corner_indices):
        offsets        : (nV+1,) int64. Vertex v's corners are
                         corner_indices[offsets[v]:offsets[v+1]].
        corner_indices : (3*nF,) int64. Corner c refers to flat corner index
                         into a (3*nF, ...) corner array laid out face-major
                         (face f, corner k -> flat 3*f + k).
    Order is deterministic: vertex ascending, then face ascending, then corner
    slot (0,1,2) ascending -- the fixed order a GPU gather pass relies on.

    validates
    ---------
    Every face corner appears exactly once across all vertex lists (count check
    == 3*nF), no index out of range. Raises InvalidSurface otherwise.
    """
    tri = np.asarray(faces)
    if tri.dtype.kind not in "iu":
        raise InvalidSurface(RejectionReason.BAD_DTYPE,
                             f"faces dtype {tri.dtype} is not integral")
    if tri.ndim != 2 or tri.shape[1] != 3:
        raise InvalidSurface(RejectionReason.BAD_SHAPE,
                             f"faces must be (n,3); got {tri.shape}")
    if tri.shape[0] == 0:
        raise InvalidSurface(RejectionReason.EMPTY_FACES, "faces is empty")
    if tri.min() < 0 or tri.max() >= vertex_count:
        raise InvalidSurface(RejectionReason.MALFORMED_INDICES,
                             f"face index out of [0,{vertex_count})")

    nF = tri.shape[0]
    flat_corners = tri.reshape(-1)                      # face-major: 3f+k
    order = np.argsort(flat_corners, kind="stable")     # vertex asc, face asc, slot asc
    corner_indices = order.astype(np.int64)
    sorted_vertices = flat_corners[order]

    counts = np.bincount(sorted_vertices, minlength=vertex_count)
    if int(counts.sum()) != 3 * nF:
        raise InvalidSurface(RejectionReason.MALFORMED_INDICES,
                             "corner count mismatch: some corner is lost or "
                             "duplicated -- this is impossible for valid input")
    offsets = np.zeros(vertex_count + 1, dtype=np.int64)
    np.cumsum(counts, out=offsets[1:])
    return offsets, corner_indices


@dataclass
class MetricResult:
    """Per-face rest-to-current in-plane metric, in a declared tangent basis.

    F = [t1 t2] @ G @ inv([t1t t2t]) composed with the normal rotation is
    encoded by reporting C = F^T F restricted to the tangent plane:
        C[i] is (2,2):  C = J^T J where J maps rest-tangent coords to current
        surface coords, expressed in the REST tangent basis.
    tangent_basis : (nF,2,3) unit rest-basis vectors (t1, t2) per face.
    area_ratio    : (nF,) current area / rest area.
    """
    C: np.ndarray                # (nF,2,2)
    tangent_basis: np.ndarray    # (nF,2,3) rest tangent frame per face
    rest_areas: np.ndarray       # (nF,)
    current_areas: np.ndarray    # (nF,)
    area_ratio: np.ndarray       # (nF,) current/rest


def triangle_metric(rest_positions, positions, faces) -> MetricResult:
    """Rest-frame in-plane metric F^T F per face. GEOMETRY ONLY.

    Declared convention: for each face, the REST tangent basis is
        t1 = normalize(b - a)                     (first edge)
        n  = normalize(cross(b - a, c - a))       (rest normal)
        t2 = cross(n, t1)                         (in-plane, orthonormal)
    The linear map J (2x2) satisfies: for rest-tangent coords u (2,), the
    current image of the rest tangent vector t1*u1 + t2*u2, projected onto the
    CURRENT tangent plane coordinates (same construction on current geometry:
    current t1', t2'), is J @ u. C = J^T J is the pullback metric: it captures
    stretch and shear IN THE TANGENT PLANE and is blind to bending (two faces
    sharing an edge can have equal C and different dihedral angles). Area is
    NOT an invariant of C alone for the purpose the preregistration names:
    diag(2, 1/2) preserves area (det = 1) while C != I -- see
    surface_energy_checks::f6_equal_area_distortion.

    This returns geometric information. It is NOT a constitutive solid law and
    invents no modulus (the preregistration forbids that).
    """
    rest = _as_positions(rest_positions)
    cur = _as_positions(positions)
    if rest.shape != cur.shape:
        raise InvalidSurface(RejectionReason.BAD_SHAPE,
                             f"rest {rest.shape} and current {cur.shape} "
                             f"must have identical shape")
    tri = _as_faces(faces, rest.shape[0])

    def _frame(p):
        e1 = p[tri[:, 1]] - p[tri[:, 0]]
        e2 = p[tri[:, 2]] - p[tri[:, 0]]
        n = np.cross(e1, e2)
        area2 = np.linalg.norm(n, axis=1)
        e1len = np.linalg.norm(e1, axis=1)
        e2len = np.linalg.norm(e2, axis=1)
        e3len = np.linalg.norm(e2 - e1, axis=1)          # third edge
        max_edge = np.maximum(e1len, np.maximum(e2len, e3len))
        # GEOMETRY BEFORE NORMALIZATION (G01-R2, P-8p): degenerate faces are
        # refused BY NAME before any division -- the old code divided by
        # area2 and e1len first and let NaN flow into C. The floor is the
        # reference's own law (DEGENERACY_FLOOR * max_edge^2, the same one
        # F4's fixture was derived from), so no new constant is invented.
        collapsed = ~(area2 > 0.0)     # NaN-safe: zero AND NaN cross products
        if np.any(collapsed):
            i = int(np.argmax(collapsed))
            raise InvalidSurface(RejectionReason.COLLAPSED_TRIANGLE,
                                 f"face {i} is collapsed (zero-area: collinear "
                                 f"or zero-length edges); refusing before "
                                 f"normalization -- no NaN metric is returned")
        floor = DEGENERACY_FLOOR * max_edge * max_edge
        degenerate = ~(area2 > floor)
        if np.any(degenerate):
            i = int(np.argmax(degenerate))
            raise InvalidSurface(RejectionReason.NEAR_DEGENERATE,
                                 f"face {i} is near-degenerate: |cross| = "
                                 f"{area2[i]:.3e} <= floor {floor[i]:.3e} "
                                 f"(64*e*max_edge^2); refusing before division")
        n = n / area2[:, None]
        t1 = e1 / e1len[:, None]
        t2 = np.cross(n, t1)
        return t1, t2, 0.5 * area2

    t1r, t2r, rest_areas = _frame(rest)
    t1c, t2c, cur_areas = _frame(cur)

    # Solve for J per face: the current image of rest edge vectors, projected
    # into the CURRENT tangent basis, gives J @ (rest coords of those edges).
    # Rest edge coords in the rest basis: E_rest = I (columns are t1,t2 coords
    # of e1,e2 projected into rest frame). Build both 2x2 systems and solve.
    # Current edge projections: e1_cur, e2_cur expressed in CURRENT basis.
    E_rest = np.stack([
        np.stack([np.sum((rest[tri[:, 1]] - rest[tri[:, 0]]) * t1r, axis=1),
                  np.sum((rest[tri[:, 1]] - rest[tri[:, 0]]) * t2r, axis=1)], axis=1),
        np.stack([np.sum((rest[tri[:, 2]] - rest[tri[:, 0]]) * t1r, axis=1),
                  np.sum((rest[tri[:, 2]] - rest[tri[:, 0]]) * t2r, axis=1)], axis=1),
    ], axis=2)                                        # (nF,2,2): columns = edges
    E_cur = np.stack([
        np.stack([np.sum((cur[tri[:, 1]] - cur[tri[:, 0]]) * t1c, axis=1),
                  np.sum((cur[tri[:, 1]] - cur[tri[:, 0]]) * t2c, axis=1)], axis=1),
        np.stack([np.sum((cur[tri[:, 2]] - cur[tri[:, 0]]) * t1c, axis=1),
                  np.sum((cur[tri[:, 2]] - cur[tri[:, 0]]) * t2c, axis=1)], axis=1),
    ], axis=2)                                        # (nF,2,2)
    # J = E_cur @ inv(E_rest). E_rest is the identity by construction for the
    # FIRST edge (t1 = e1/|e1| => coords (|e1|, 0)); the second edge has coords
    # (proj, proj). Solve the 2x2 systems explicitly (no batched inv needed):
    #   J @ E_rest = E_cur  =>  J = E_cur @ inv(E_rest)
    a11 = E_rest[:, 0, 0]; a12 = E_rest[:, 0, 1]
    a21 = E_rest[:, 1, 0]; a22 = E_rest[:, 1, 1]
    det = a11 * a22 - a12 * a21
    det_floor = DEGENERACY_FLOOR * np.maximum(
        np.abs(a11 * a22) + np.abs(a12 * a21), np.finfo(np.float64).tiny)
    if np.any(~(np.abs(det) >= det_floor)):   # NaN-safe (P-8o): a NaN det is a refusal
        raise InvalidSurface(RejectionReason.NEAR_DEGENERATE,
                             "rest frame is degenerate (linearly dependent "
                             "edges) for at least one face")
    b11 = E_cur[:, 0, 0]; b12 = E_cur[:, 0, 1]
    b21 = E_cur[:, 1, 0]; b22 = E_cur[:, 1, 1]
    # inv(E_rest) = 1/det * [[a22, -a12], [-a21, a11]]
    J = np.empty((tri.shape[0], 2, 2))
    J[:, 0, 0] = (b11 * a22 - b12 * a21) / det
    J[:, 0, 1] = (b12 * a11 - b11 * a12) / det
    J[:, 1, 0] = (b21 * a22 - b22 * a21) / det
    J[:, 1, 1] = (b22 * a11 - b21 * a12) / det
    C = np.einsum("fji,fjk->fik", J, J)               # J^T J

    return MetricResult(C=C, tangent_basis=np.stack([t1r, t2r], axis=1),
                        rest_areas=rest_areas, current_areas=cur_areas,
                        area_ratio=cur_areas / rest_areas)
