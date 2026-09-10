"""geometry.py -- validated immutable rest geometry for the elastic triangle.

Rest snapshots are built ONCE, frozen (immutable), and carry everything the law needs per face:
rest tangent basis, rest edge-coordinate matrix D and its inverse B, rest areas, and the
deterministic CSR vertex->corner adjacency shared with the surface reference's gather convention.

Conventions (DERIVATION.md section 2):
  rest faces (v0,v1,v2) as indexed; rest normal n = normalize((x1-x0)x(x2-x0));
  the pullback frame is the SHEET frame: one common (frame_t1, frame_t2) for all faces,
  derived from the area-weighted mean rest normal (flat reference sheet) -- so uniform
  fields pull back to identical coefficient tensors on every face (exact patch test);
  D = [coord(x1-x0), coord(x2-x0)] in the sheet frame; B = inv(D).

Refusals mirror the surface reference's naming: a degenerate rest triangle is refused, never
silently patched. Nothing here clamps.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

EPS64 = float(np.finfo(np.float64).eps)
DEGENERACY_FLOOR_FACTOR = 64.0  # shared geometric near-singularity gate (surface reference)
FLAT_SHEET_TOL = 1e-9          # max per-face reference-normal deviation from the sheet frame


class InvalidGeometry(ValueError):
    """Named refusal for invalid input geometry. reason is machine-readable."""

    def __init__(self, reason: str, message: str):
        super().__init__(message)
        self.reason = reason
        self.message = message


class Reason:
    """Stable machine-readable refusal reasons (falsifiers assert on these)."""
    BAD_DTYPE = "bad_dtype"
    BAD_SHAPE = "bad_shape"
    EMPTY_POSITIONS = "empty_positions"
    EMPTY_FACES = "empty_faces"
    NONFINITE_POSITIONS = "nonfinite_positions"
    MALFORMED_INDICES = "malformed_indices"
    REPEATED_VERTEX_FACE = "repeated_vertex_face"
    COLLAPSED_TRIANGLE = "collapsed_triangle"
    NEAR_DEGENERATE = "near_degenerate_triangle"
    NONFINITE_RESULT = "nonfinite_result"
    REST_POSITIONS_NONFINITE = "rest_positions_nonfinite"
    NONFLAT_REST_SHEET = "nonflat_rest_sheet"


def as_positions(positions, *, rest: bool = False):
    """Validate + normalize positions to float64 (nV,3). Refuses NaN/inf and bad shapes."""
    pos = np.asarray(positions)
    if pos.dtype.kind not in "fiu":
        raise InvalidGeometry(Reason.BAD_DTYPE, f"positions dtype {pos.dtype} is not numeric")
    if pos.dtype != np.float64:
        pos = pos.astype(np.float64)
    if pos.ndim != 2 or pos.shape[1] != 3:
        raise InvalidGeometry(Reason.BAD_SHAPE, f"positions must be (n,3); got {pos.shape}")
    if not np.all(np.isfinite(pos)):
        raise InvalidGeometry(
            Reason.NONFINITE_POSITIONS if not rest else Reason.REST_POSITIONS_NONFINITE,
            "positions contain NaN or infinity")
    if pos.shape[0] == 0:
        raise InvalidGeometry(Reason.EMPTY_POSITIONS, "positions is empty")
    return pos


def as_faces(faces, n_vertices: int):
    """Validate + normalize faces to int64 (nF,3). No face dropped, none repeated."""
    tri = np.asarray(faces)
    if tri.dtype.kind not in "iu":
        raise InvalidGeometry(Reason.BAD_DTYPE, f"faces dtype {tri.dtype} is not integral")
    if tri.dtype != np.int64:
        tri = tri.astype(np.int64)
    if tri.ndim != 2 or tri.shape[1] != 3:
        raise InvalidGeometry(Reason.BAD_SHAPE, f"faces must be (n,3); got {tri.shape}")
    if tri.shape[0] == 0:
        raise InvalidGeometry(Reason.EMPTY_FACES, "faces is empty")
    if tri.min() < 0 or tri.max() >= n_vertices:
        raise InvalidGeometry(
            Reason.MALFORMED_INDICES,
            f"face index out of [0,{n_vertices}) (min {tri.min()}, max {tri.max()})")
    dup = ((tri[:, 0] == tri[:, 1]) | (tri[:, 1] == tri[:, 2]) | (tri[:, 0] == tri[:, 2]))
    if np.any(dup):
        i = int(np.argmax(dup))
        raise InvalidGeometry(Reason.REPEATED_VERTEX_FACE,
                              f"face {i} repeats a vertex ({tri[i].tolist()})")
    return tri


def build_vertex_corner_adjacency(faces, vertex_count: int):
    """Fixed-order vertex->corner CSR: vertex asc, face asc, slot asc.

    Identical ordering to the surface reference's gather (vertex ascending, face ascending,
    corner slot ascending) so both laws can share one GPU gather stage. Corner c refers to the
    flat index 3*f + k in a face-major (3*nF, ...) corner array.
    """
    tri = np.asarray(faces)
    if tri.dtype.kind not in "iu" or tri.ndim != 2 or tri.shape[1] != 3 or tri.shape[0] == 0:
        raise InvalidGeometry(Reason.BAD_SHAPE, f"faces must be (n,3) int; got {tri.shape}")
    if tri.min() < 0 or tri.max() >= vertex_count:
        raise InvalidGeometry(Reason.MALFORMED_INDICES, "face index out of range")
    flat = tri.reshape(-1)                      # face-major: 3f + k
    order = np.argsort(flat, kind="stable")
    corner_indices = order.astype(np.int64)
    counts = np.bincount(flat[order], minlength=vertex_count)
    if int(counts.sum()) != 3 * tri.shape[0]:
        raise InvalidGeometry(Reason.MALFORMED_INDICES, "corner count mismatch")
    offsets = np.zeros(vertex_count + 1, dtype=np.int64)
    np.cumsum(counts, out=offsets[1:])
    return offsets, corner_indices


@dataclass(frozen=True)
class RestGeometry:
    """Immutable validated rest snapshot. Built once by build_rest_geometry()."""
    positions: np.ndarray          # (nV,3) float64 rest positions
    faces: np.ndarray              # (nF,3) int64 as indexed (never reordered)
    n_vertices: int
    n_faces: int
    edge1: np.ndarray              # (nF,3) x1 - x0
    edge2: np.ndarray              # (nF,3) x2 - x0
    t1: np.ndarray                 # (nF,3) sheet frame first tangent (same for all faces)
    t2: np.ndarray                 # (nF,3) sheet frame second tangent
    n: np.ndarray                  # (nF,3) rest unit normal (per-face, from cross, orientation parity)
    frame_t1: np.ndarray           # (3,) sheet-level reference tangent 1 (global pullback basis)
    frame_t2: np.ndarray           # (3,) sheet-level reference tangent 2
    frame_n: np.ndarray            # (3,) sheet-level reference normal
    D: np.ndarray                  # (nF,2,2) rest edge coords in the sheet frame
    B: np.ndarray                  # (nF,2,2) inv(D)
    areas0: np.ndarray             # (nF,) rest reference area
    max_edge0: np.ndarray          # (nF,) largest rest edge length
    csr_offsets: np.ndarray        # (nV+1,) int64
    csr_corners: np.ndarray        # (3*nF,) int64
    build_info: dict = field(default_factory=dict)

    @property
    def total_area0(self) -> float:
        return float(np.sum(self.areas0))


def _frame(p: np.ndarray, tri):
    e1 = p[tri[:, 1]] - p[tri[:, 0]]
    e2 = p[tri[:, 2]] - p[tri[:, 0]]
    n = np.cross(e1, e2)
    cross_mag = np.linalg.norm(n, axis=1)
    e1len = np.linalg.norm(e1, axis=1)
    e2len = np.linalg.norm(e2, axis=1)
    e3len = np.linalg.norm(p[tri[:, 2]] - p[tri[:, 1]], axis=1)
    max_edge = np.maximum(e1len, np.maximum(e2len, e3len))
    if not (np.all(np.isfinite(cross_mag)) and np.all(np.isfinite(max_edge))):
        raise InvalidGeometry(Reason.NONFINITE_RESULT,
                              "edge/cross magnitudes overflow float64 -- refusing")
    areas2 = 0.5 * cross_mag
    floor = DEGENERACY_FLOOR_FACTOR * EPS64 * max_edge * max_edge
    if np.any(cross_mag <= floor):
        i = int(np.argmax(cross_mag <= floor))
        if cross_mag[i] <= 0.0:
            raise InvalidGeometry(Reason.COLLAPSED_TRIANGLE,
                                  f"face {i} is collapsed (zero-area)")
        raise InvalidGeometry(
            Reason.NEAR_DEGENERATE,
            f"face {i} near-degenerate: |cross| = {cross_mag[i]:.3e} <= floor {floor[i]:.3e}")
    n = n / cross_mag[:, None]
    t1 = e1 / e1len[:, None]
    t2 = np.cross(n, t1)
    return e1, e2, t1, t2, n, areas2, max_edge


def build_rest_geometry(positions, faces, build_info=None) -> RestGeometry:
    """Build the frozen rest snapshot, refusing any nondegenerate-invalid rest triangle.

    The reference pullback frame is the SHEET frame: one common tangent basis for the whole
    mesh, derived from the area-weighted mean rest normal (flat reference sheet). Every face
    shares the same (frame_t1, frame_t2), so a uniform deformation field pulls back to the
    same coefficient tensor on every face and the constant-strain patch test is exact
    (F16/F11 affine patch test in PREREGISTRATION.md). Rest faces whose normals deviate from
    the sheet frame are REFUSED (nonflat_rest_sheet). This is the ONLY place the sheet basis,
    D and B are formed. Called once; the outputs are immutable (frozen dataclass carrying
    fresh arrays). build_info is user metadata (units, provenance) copied verbatim.
    """
    pos = as_positions(positions, rest=True)
    tri = as_faces(faces, pos.shape[0])
    e1, e2, _, _, n, areas0, max_edge0 = _frame(pos, tri)
    areas0 = np.asarray(areas0, dtype=np.float64)

    # Sheet-level reference frame: the plane axis of the face normals, sign-robust against
    # mixed winding (a mesh may be all-CW, all-CCW, or mixed; the energy is winding-agnostic).
    normals = n.astype(np.float64, copy=False)
    _, _, vh = np.linalg.svd(normals.reshape(normals.shape[0], 3), full_matrices=False)
    cand = vh[0]
    if not np.all(np.isfinite(cand)) or np.linalg.norm(cand) == 0.0:
        raise InvalidGeometry(Reason.NONFINITE_RESULT,
                              "cannot form a sheet reference frame from rest normals")
    if np.sum(areas0 * (normals @ cand)) < 0.0:
        cand = -cand
    dev = 1.0 - np.abs(normals @ cand)
    if np.any(dev > FLAT_SHEET_TOL):
        i = int(np.argmax(dev))
        raise InvalidGeometry(
            Reason.NONFLAT_REST_SHEET,
            f"rest sheet not flat: face {i} reference-normal deviation "
            f"{dev[i]:.3e} > {FLAT_SHEET_TOL}")
    frame_n = cand
    # frame_t1 is rest-DERIVED (the first face's first edge, projected onto the tangent
    # plane) so the whole sheet frame CO-ROTATES with the rest mesh: rigidly re-placing the
    # entire configuration (rest and current together) leaves the strain coefficients
    # identical (F7), not merely the energy. Degenerate projections fall back to the next edge.
    t1c = e1[0] - (e1[0] @ frame_n) * frame_n
    if np.linalg.norm(t1c) < 1e-12:
        t1c = e2[0] - (e2[0] @ frame_n) * frame_n
        if np.linalg.norm(t1c) < 1e-12:
            raise InvalidGeometry(Reason.NONFINITE_RESULT,
                                  "cannot form a sheet-frame tangent from rest edges")
    frame_t1 = t1c / np.linalg.norm(t1c)
    frame_t2 = np.cross(frame_n, frame_t1)

    # D = [coord(e1 in sheet frame), coord(e2 in sheet frame)]; shares of the pullback basis.
    D = np.empty((tri.shape[0], 2, 2))
    D[:, 0, 0] = e1 @ frame_t1
    D[:, 1, 0] = e1 @ frame_t2
    D[:, 0, 1] = e2 @ frame_t1
    D[:, 1, 1] = e2 @ frame_t2
    det = D[:, 0, 0] * D[:, 1, 1] - D[:, 0, 1] * D[:, 1, 0]
    det_floor = DEGENERACY_FLOOR_FACTOR * EPS64 * np.maximum(
        np.abs(D[:, 0, 0] * D[:, 1, 1]) + np.abs(D[:, 0, 1] * D[:, 1, 0]),
        np.finfo(np.float64).tiny)
    if np.any(np.abs(det) <= det_floor):
        raise InvalidGeometry(Reason.NEAR_DEGENERATE,
                              "rest frame degenerate (linearly dependent edges)")
    B = np.empty_like(D)
    B[:, 0, 0] = D[:, 1, 1] / det
    B[:, 1, 1] = D[:, 0, 0] / det
    B[:, 0, 1] = -D[:, 0, 1] / det
    B[:, 1, 0] = -D[:, 1, 0] / det

    offsets, corners = build_vertex_corner_adjacency(tri, pos.shape[0])
    info = dict(build_info) if build_info else {}
    t1_all = np.tile(frame_t1, (tri.shape[0], 1))
    t2_all = np.tile(frame_t2, (tri.shape[0], 1))
    return RestGeometry(
        positions=np.array(pos, copy=True),
        faces=np.array(tri, copy=True),
        n_vertices=int(pos.shape[0]), n_faces=int(tri.shape[0]),
        edge1=e1.astype(np.float64, copy=False), edge2=e2.astype(np.float64, copy=False),
        t1=t1_all, t2=t2_all, n=n.astype(np.float64, copy=False),
        frame_t1=frame_t1.astype(np.float64, copy=False),
        frame_t2=frame_t2.astype(np.float64, copy=False),
        frame_n=frame_n.astype(np.float64, copy=False),
        D=D, B=B, areas0=areas0, max_edge0=max_edge0,
        csr_offsets=offsets, csr_corners=corners, build_info=info)


def unit_make_grid(width=1.0, height=1.0, nx=1, ny=1, z0=0.0, diagonal="f"):
    """Planar grid sheet: nX x nY quads -> 2*nX*nY CCW triangles in z=z0.

    Triangles are CCW viewed from +z (n = +z). Even slots split one way, odd the other, so
    shared edges always agree. diagonal determines the split: 'f' -> (i,j),(i+1,j+1),(i,j+1) on
    the forward-bias half, 'b' -> the opposite bias (still conforming, vertices differ).
    """
    nx = int(nx); ny = int(ny)
    xs = np.linspace(0.0, width, nx + 1)
    ys = np.linspace(0.0, height, ny + 1)
    # "xy" ordering matches the face index formula v00 = j*(nx+1)+i below: rows of constant y.
    gx, gy = np.meshgrid(xs, ys, indexing="xy")
    pos = np.stack([gx.ravel(), gy.ravel(), np.full((nx + 1) * (ny + 1), float(z0))], axis=1)
    faces = []
    for j in range(ny):
        for i in range(nx):
            v00 = j * (nx + 1) + i
            v10 = v00 + 1
            v01 = (j + 1) * (nx + 1) + i
            v11 = v01 + 1
            if (i + j) % 2 == 0:
                faces.append((v00, v10, v11)); faces.append((v00, v11, v01))
            else:
                faces.append((v00, v10, v01)); faces.append((v10, v11, v01))
    return pos, np.array(faces, dtype=np.int64)


def apply_affine(pos, S, t=None, axis=(0.0, 0.0, 1.0), angle=0.0):
    """y = R * S * x + t applied to rows. S is (3,3) or scalar-matrix; axis/angle optional rotation."""
    S = np.asarray(S, dtype=np.float64)
    if S.ndim == 0:
        S = S * np.eye(3)
    R = np.eye(3)
    if angle != 0.0:
        a = np.asarray(axis, dtype=np.float64)
        a = a / np.linalg.norm(a)
        c = np.cos(angle); s = np.sin(angle)
        K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]], dtype=np.float64)
        R = np.eye(3) + s * K + (1 - c) * (K @ K)
    y = pos @ S.T
    y = y @ R.T
    if t is not None:
        y = y + np.asarray(t, dtype=np.float64)
    return y