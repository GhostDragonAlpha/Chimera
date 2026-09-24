"""Conservative tetrahedral material-volume compiler (NumPy + stdlib only).

This is a reference compiler, not a fitter, attachment solver, or constitutive
model. It accepts a finite, conforming, watertight tetrahedral complex in
meters, resolves one region proposal per cell, integrates piecewise-constant
density, and emits shared, oriented material interfaces.

A cell with no proposal or competing region proposals remains explicitly
unresolved/conflicted. Such a partition has no total mass properties. No
material, owner, density, or stiffness default is inferred.

Input contract and numeric/topology scope are documented in
Chimera/docs/matter/material_volume_compiler.md.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence

import numpy as np

__all__ = [
    "BoundaryFace", "CellAssignment", "CompileError", "CompiledPartition",
    "CompilerReason", "MassProperties", "MassSourceClaim", "MassSourceKind",
    "MaterialInterface", "MaterialSpec", "RegionSpec", "UnresolvedAdjacency",
    "compile_document", "compile_partition", "validate_mass_source_claims",
]

EPS = float(np.finfo(np.float64).eps)
_DEGENERACY_REL = 64.0 * EPS
_SAT_REL = 128.0 * EPS
# Faces are oriented outward from a positively oriented tet [v0,v1,v2,v3].
_OUTWARD_LOCAL_FACES = ((1, 2, 3), (0, 3, 2), (0, 1, 3), (0, 2, 1))


class CompilerReason:
    """Stable machine-readable refusal and per-cell status strings."""
    BAD_SHAPE = "bad_shape"
    BAD_DTYPE = "bad_dtype"
    NONFINITE = "nonfinite_input"
    EMPTY_MESH = "empty_mesh"
    BAD_INDEX = "bad_index"
    REPEATED_VERTEX = "repeated_vertex"
    DUPLICATE_TETRAHEDRON = "duplicate_tetrahedron"
    UNUSED_VERTEX = "unused_vertex"
    DUPLICATE_VERTEX_POSITION = "duplicate_vertex_position"
    INVERTED_TETRAHEDRON = "inverted_tetrahedron"
    DEGENERATE_TETRAHEDRON = "degenerate_tetrahedron"
    NUMERIC_OVERFLOW = "numeric_overflow"
    NON_MANIFOLD_FACE = "non_manifold_face"
    INCONSISTENT_FACE_ORIENTATION = "inconsistent_face_orientation"
    OPEN_BOUNDARY = "open_boundary"
    NON_MANIFOLD_BOUNDARY = "non_manifold_boundary"
    INCONSISTENT_BOUNDARY_ORIENTATION = "inconsistent_boundary_orientation"
    NON_MANIFOLD_VERTEX_LINK = "non_manifold_vertex_link"
    OVERLAPPING_TETRAHEDRA = "overlapping_tetrahedra"
    BAD_IDENTIFIER = "bad_identifier"
    DUPLICATE_MATERIAL_ID = "duplicate_material_id"
    DUPLICATE_REGION_ID = "duplicate_region_id"
    DUPLICATE_MASS_OWNER_ID = "duplicate_mass_owner_id"
    MISSING_MATERIAL = "missing_material"
    INVALID_DENSITY = "invalid_density"
    MISSING_DENSITY = "missing_density"
    UNKNOWN_REGION = "unknown_region"
    BAD_ASSIGNMENT_COUNT = "bad_assignment_count"
    UNRESOLVED = "unresolved"
    CONFLICT = "conflict"
    INCOMPLETE = "incomplete_partition"
    BAD_SCHEMA = "bad_schema"
    MIXED_MASS_REPRESENTATIONS = "mixed_mass_representations"
    UNKNOWN_MASS_SOURCE = "unknown_mass_source"


class CompileError(ValueError):
    """Named refusal. ``reason`` is stable for tests and calling applications."""

    def __init__(self, reason: str, detail: str):
        super().__init__(f"{reason}: {detail}")
        self.reason = reason
        self.detail = detail


@dataclass(frozen=True)
class MaterialSpec:
    material_id: str
    density_kg_m3: float | None = None
    density_source: str | None = None
    conditions: str | None = None


@dataclass(frozen=True)
class RegionSpec:
    """A unique mass owner for one material region; stiffness is metadata only."""

    region_id: str
    mass_owner_id: str
    material_id: str
    stiffness_pa: float | None = None


@dataclass(frozen=True)
class MassProperties:
    volume_m3: float
    mass_kg: float
    center_of_mass_m: tuple[float, float, float]
    inertia_com_kg_m2: tuple[tuple[float, float, float], ...]
    cell_count: int


@dataclass(frozen=True)
class CellAssignment:
    cell_id: int
    status: str                         # resolved | unresolved | conflict | missing_density
    candidate_region_ids: tuple[str, ...]
    candidate_owner_ids: tuple[str, ...]
    region_id: str | None
    mass_owner_id: str | None
    material_id: str | None
    density_kg_m3: float | None
    density_source: str | None
    density_conditions: str | None


@dataclass(frozen=True)
class MaterialInterface:
    """One shared face; its normal points from region_a_id to region_b_id."""

    face_key: tuple[int, int, int]       # sorted node IDs, unique face identity
    vertices: tuple[int, int, int]       # oriented so cross points A -> B
    region_a_id: str
    region_b_id: str
    mass_owner_a_id: str
    mass_owner_b_id: str
    material_a_id: str
    material_b_id: str
    area_m2: float
    normal_a_to_b: tuple[float, float, float]


@dataclass(frozen=True)
class BoundaryFace:
    """A one-cell exterior face, oriented outward from that tetrahedron."""

    face_key: tuple[int, int, int]
    vertices: tuple[int, int, int]
    cell_id: int
    region_id: str | None


@dataclass(frozen=True)
class UnresolvedAdjacency:
    face_key: tuple[int, int, int]
    cell_ids: tuple[int, int]
    statuses: tuple[str, str]


@dataclass(frozen=True)
class CompiledPartition:
    complete: bool
    cells: tuple[CellAssignment, ...]  # exactly one entry per input tetrahedron
    geometric_volume_m3: float
    mass_properties: MassProperties | None  # None unless every cell is resolved
    resolved_only_subtotal: MassProperties | None  # explicitly not a body total
    resolved_region_subtotals: Mapping[str, MassProperties]
    geometry_signature: str
    interfaces: tuple[MaterialInterface, ...]
    boundary_faces: tuple[BoundaryFace, ...]
    unresolved_adjacencies: tuple[UnresolvedAdjacency, ...]
    connected_components: int

    @property
    def unresolved_cell_ids(self) -> tuple[int, ...]:
        return tuple(c.cell_id for c in self.cells if c.status == CompilerReason.UNRESOLVED)

    @property
    def missing_density_cell_ids(self) -> tuple[int, ...]:
        return tuple(c.cell_id for c in self.cells if c.status == CompilerReason.MISSING_DENSITY)

    @property
    def ownership_complete(self) -> bool:
        """Every cell has one known region/owner, even if density is absent."""
        return all(c.region_id is not None and c.mass_owner_id is not None
                   for c in self.cells)

    @property
    def conflicting_cell_ids(self) -> tuple[int, ...]:
        return tuple(c.cell_id for c in self.cells if c.status == CompilerReason.CONFLICT)

    def to_dict(self) -> dict:
        """JSON-ready result; missing total properties remain JSON null, never zero."""
        return {
            "complete": self.complete,
            "cell_count": len(self.cells),
            "accounting_row_count": len(self.cells),
            "resolved_mass_cell_count": sum(c.status == "resolved" for c in self.cells),
            "unresolved_cell_ids": list(self.unresolved_cell_ids),
            "missing_density_cell_ids": list(self.missing_density_cell_ids),
            "conflicting_cell_ids": list(self.conflicting_cell_ids),
            "ownership_complete": self.ownership_complete,
            "geometric_volume_m3": self.geometric_volume_m3,
            "geometry_signature": self.geometry_signature,
            "mass_properties": (asdict(self.mass_properties)
                                if self.mass_properties is not None else None),
            "resolved_only_subtotal_not_body_total": (
                asdict(self.resolved_only_subtotal)
                if self.resolved_only_subtotal is not None else None),
            "resolved_region_subtotals": {
                k: asdict(v) for k, v in sorted(self.resolved_region_subtotals.items())
            },
            "cells": [asdict(c) for c in self.cells],
            "interfaces": [asdict(i) for i in self.interfaces],
            "boundary_faces": [asdict(f) for f in self.boundary_faces],
            "unresolved_adjacencies": [asdict(f) for f in self.unresolved_adjacencies],
            "connected_components": self.connected_components,
            "mass_source_kind": MassSourceKind.MATERIAL_VOLUME,
        }


class MassSourceKind:
    """Accepted integration labels; mixed-dimensional/legacy mixtures are refused."""
    MATERIAL_VOLUME = "reconstructed_material_volume"
    THIN_SHEET = "thin_sheet"
    EFFECTIVE_SKELETAL_SEGMENT = "effective_skeletal_segment"
    ALL = frozenset((MATERIAL_VOLUME, THIN_SHEET, EFFECTIVE_SKELETAL_SEGMENT))


@dataclass(frozen=True)
class MassSourceClaim:
    source_kind: str
    mass_owner_id: str


def validate_mass_source_claims(claims: Iterable[MassSourceClaim]) -> None:
    """Reject duplicate owners and mixed representations for one body ledger.

    A thickness-bearing membrane belongs in the same tetrahedral partition as
    its tissue. A legacy thin-sheet mass or effective skeletal-segment mass may
    be used in a separate legacy-only ledger, but cannot be added to reconstructed
    volume mass by this v1 integration contract.
    """
    seen_owners: set[str] = set()
    kinds: set[str] = set()
    claim_count = 0
    for claim in claims:
        claim_count += 1
        if not isinstance(claim, MassSourceClaim):
            raise CompileError(CompilerReason.BAD_SCHEMA,
                               f"mass source claims must be MassSourceClaim records, got "
                               f"{type(claim).__name__}")
        if not isinstance(claim.source_kind, str) or claim.source_kind not in MassSourceKind.ALL:
            raise CompileError(CompilerReason.UNKNOWN_MASS_SOURCE,
                               f"unsupported mass source {claim.source_kind!r}")
        _identifier(claim.mass_owner_id, "mass_owner_id")
        if claim.mass_owner_id in seen_owners:
            raise CompileError(CompilerReason.DUPLICATE_MASS_OWNER_ID,
                               f"mass owner {claim.mass_owner_id!r} is claimed more than once")
        seen_owners.add(claim.mass_owner_id)
        kinds.add(claim.source_kind)
    if claim_count == 0:
        raise CompileError(CompilerReason.INCOMPLETE,
                           "body mass ledger must name at least one mass source")
    if len(kinds) > 1:
        if MassSourceKind.MATERIAL_VOLUME in kinds \
                and MassSourceKind.EFFECTIVE_SKELETAL_SEGMENT in kinds:
            detail = ("effective skeletal-segment masses cannot be added on top of "
                      "reconstructed tissue-volume masses")
        elif MassSourceKind.MATERIAL_VOLUME in kinds \
                and MassSourceKind.THIN_SHEET in kinds:
            detail = ("independent thin-sheet mass cannot be added to a volume partition; "
                      "mesh the membrane's exclusive thickness as tetrahedral cells")
        else:
            detail = ("one body mass ledger must use one representation kind; "
                      "no spatial disjointness proof is available in v1")
        raise CompileError(CompilerReason.MIXED_MASS_REPRESENTATIONS, detail)


def _identifier(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CompileError(CompilerReason.BAD_IDENTIFIER,
                           f"{label} must be a non-empty string")
    return value


def _positions(vertices) -> np.ndarray:
    raw = np.asarray(vertices)
    if raw.dtype.kind not in "fiu":
        raise CompileError(CompilerReason.BAD_DTYPE,
                           f"vertices must be numeric; got dtype {raw.dtype}")
    if raw.ndim != 2 or raw.shape[1] != 3:
        raise CompileError(CompilerReason.BAD_SHAPE,
                           f"vertices must have shape (n,3); got {raw.shape}")
    if raw.shape[0] < 4:
        raise CompileError(CompilerReason.EMPTY_MESH,
                           "a tetrahedral mesh needs at least four vertices")
    p = np.array(raw, dtype=np.float64, copy=True)
    if not np.all(np.isfinite(p)):
        raise CompileError(CompilerReason.NONFINITE,
                           "vertices contain NaN or infinity")
    if np.unique(p, axis=0).shape[0] != p.shape[0]:
        raise CompileError(CompilerReason.DUPLICATE_VERTEX_POSITION,
                           "distinct vertex IDs have exactly coincident coordinates; "
                           "weld them before compilation")
    return p


def _tetrahedra(tetrahedra, vertex_count: int) -> np.ndarray:
    raw = np.asarray(tetrahedra)
    if raw.dtype.kind not in "iu":
        raise CompileError(CompilerReason.BAD_DTYPE,
                           f"tetrahedra must be integral; got dtype {raw.dtype}")
    if raw.ndim != 2 or raw.shape[1] != 4:
        raise CompileError(CompilerReason.BAD_SHAPE,
                           f"tetrahedra must have shape (n,4); got {raw.shape}")
    if raw.shape[0] == 0:
        raise CompileError(CompilerReason.EMPTY_MESH, "tetrahedra is empty")
    if raw.dtype.kind == "u" and raw.size and int(raw.max()) > np.iinfo(np.int64).max:
        raise CompileError(CompilerReason.BAD_INDEX, "tetrahedron index exceeds int64")
    t = np.array(raw, dtype=np.int64, copy=True)
    if t.min() < 0 or t.max() >= vertex_count:
        raise CompileError(CompilerReason.BAD_INDEX,
                           f"indices must lie in [0,{vertex_count}); found "
                           f"[{int(t.min())},{int(t.max())}]")
    if np.any(np.diff(np.sort(t, axis=1), axis=1) == 0):
        raise CompileError(CompilerReason.REPEATED_VERTEX,
                           "a tetrahedron repeats a vertex ID")
    canonical = np.sort(t, axis=1)
    if np.unique(canonical, axis=0).shape[0] != t.shape[0]:
        raise CompileError(CompilerReason.DUPLICATE_TETRAHEDRON,
                           "the same four vertex IDs occur in more than one cell")
    used = np.unique(t)
    if used.size != vertex_count:
        unused = sorted(set(range(vertex_count)) - set(map(int, used)))
        raise CompileError(CompilerReason.UNUSED_VERTEX,
                           f"unreferenced vertex IDs: {unused[:8]}")
    return t


def _geometry(p: np.ndarray, t: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return positive volumes, stable centroids, and six-edge cell scales."""
    q = p[t]
    with np.errstate(over="ignore", invalid="ignore", under="ignore"):
        e = q[:, 1:, :] - q[:, :1, :]
        edge_lengths = []
        for i, j in ((0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)):
            edge_lengths.append(np.linalg.norm(q[:, i] - q[:, j], axis=1))
        scale = np.maximum.reduce(edge_lengths)
        if not np.all(np.isfinite(e)) or not np.all(np.isfinite(scale)):
            raise CompileError(CompilerReason.NUMERIC_OVERFLOW,
                               "edge arithmetic overflowed for finite coordinates")
        if np.any(scale <= 0.0):
            raise CompileError(CompilerReason.DEGENERATE_TETRAHEDRON,
                               "a tetrahedron has zero edge scale")
        en = e / scale[:, None, None]
        det_scaled = np.einsum("ij,ij->i", en[:, 0],
                               np.cross(en[:, 1], en[:, 2]))
    if not np.all(np.isfinite(det_scaled)):
        raise CompileError(CompilerReason.NUMERIC_OVERFLOW,
                           "scaled tetrahedron determinant is non-finite")
    inverted = det_scaled < -_DEGENERACY_REL
    if np.any(inverted):
        i = int(np.flatnonzero(inverted)[0])
        raise CompileError(CompilerReason.INVERTED_TETRAHEDRON,
                           f"cell {i} has negative signed determinant {det_scaled[i]:.17g}; "
                           "vertex order is not repaired")
    degenerate = np.abs(det_scaled) <= _DEGENERACY_REL
    if np.any(degenerate):
        i = int(np.flatnonzero(degenerate)[0])
        raise CompileError(CompilerReason.DEGENERATE_TETRAHEDRON,
                           f"cell {i} has |det|/max_edge^3={abs(det_scaled[i]):.3e} <= "
                           f"64*float64_epsilon={_DEGENERACY_REL:.3e}")
    with np.errstate(over="ignore", invalid="ignore", under="ignore"):
        volumes = (det_scaled / 6.0) * scale * scale * scale
        centroids = q[:, 0] + np.sum(e, axis=1) / 4.0
    if not np.all(np.isfinite(volumes)) or not np.all(volumes > 0.0) \
            or not np.all(np.isfinite(centroids)):
        raise CompileError(CompilerReason.NUMERIC_OVERFLOW,
                           "cell volume or centroid is non-finite/non-positive")
    return volumes, centroids, scale


def _cyclic_equal(a: Sequence[int], b: Sequence[int]) -> bool:
    aa, bb = tuple(a), tuple(b)
    return any(aa == bb[k:] + bb[:k] for k in range(3))


def _face_records(t: np.ndarray) -> dict[tuple[int, int, int], list[tuple[int, tuple[int, int, int]]]]:
    records: dict[tuple[int, int, int], list[tuple[int, tuple[int, int, int]]]] = {}
    for cell_id, tet in enumerate(t):
        for local in _OUTWARD_LOCAL_FACES:
            oriented = tuple(int(tet[k]) for k in local)
            key = tuple(sorted(oriented))
            records.setdefault(key, []).append((cell_id, oriented))
    return records


def _face_orientation_and_boundary(records):
    boundary: list[tuple[tuple[int, int, int], int, tuple[int, int, int]]] = []
    for key, sides in records.items():
        if len(sides) > 2:
            raise CompileError(CompilerReason.NON_MANIFOLD_FACE,
                               f"face {key} is incident to {len(sides)} tetrahedra")
        if len(sides) == 1:
            cell_id, oriented = sides[0]
            boundary.append((key, cell_id, oriented))
            continue
        (cell_a, face_a), (cell_b, face_b) = sides
        if _cyclic_equal(face_a, face_b):
            raise CompileError(CompilerReason.INCONSISTENT_FACE_ORIENTATION,
                               f"cells {cell_a} and {cell_b} orient shared face {key} "
                               "in the same direction")
        if not _cyclic_equal(face_a, (face_b[0], face_b[2], face_b[1])):
            raise CompileError(CompilerReason.INCONSISTENT_FACE_ORIENTATION,
                               f"cells {cell_a} and {cell_b} have inconsistent face {key}")
    if not boundary:
        raise CompileError(CompilerReason.OPEN_BOUNDARY,
                           "finite tetrahedral input has no exterior boundary faces")
    return boundary


def _check_closed_boundary(boundary) -> set[int]:
    edge_directions: dict[tuple[int, int], list[tuple[int, int]]] = {}
    boundary_vertices: set[int] = set()
    for _key, _cell, face in boundary:
        boundary_vertices.update(face)
        for a, b in ((face[0], face[1]), (face[1], face[2]), (face[2], face[0])):
            edge_directions.setdefault((min(a, b), max(a, b)), []).append((a, b))
    for edge, directions in edge_directions.items():
        if len(directions) < 2:
            raise CompileError(CompilerReason.OPEN_BOUNDARY,
                               f"exterior edge {edge} is incident to {len(directions)} "
                               "boundary faces, expected 2")
        if len(directions) > 2:
            raise CompileError(CompilerReason.NON_MANIFOLD_BOUNDARY,
                               f"exterior edge {edge} is incident to {len(directions)} "
                               "boundary faces")
        if directions[0] != directions[1][::-1]:
            raise CompileError(CompilerReason.INCONSISTENT_BOUNDARY_ORIENTATION,
                               f"boundary edge {edge} is not traversed in opposite directions")
    return boundary_vertices


def _check_vertex_links(t: np.ndarray, boundary_vertices: set[int]) -> None:
    """Require each vertex link to be one sphere (interior) or disk (boundary)."""
    incident: dict[int, list[tuple[int, int, int]]] = {}
    for tet in t:
        row = tuple(map(int, tet))
        for v in row:
            incident.setdefault(v, []).append(tuple(x for x in row if x != v))
    for v, triangles in incident.items():
        edge_to_faces: dict[tuple[int, int], list[int]] = {}
        link_vertices: set[int] = set()
        for ti, tri in enumerate(triangles):
            link_vertices.update(tri)
            for a, b in ((tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0])):
                edge_to_faces.setdefault((min(a, b), max(a, b)), []).append(ti)
        bad = [edge for edge, fs in edge_to_faces.items() if len(fs) > 2 or len(fs) < 1]
        if bad:
            raise CompileError(CompilerReason.NON_MANIFOLD_VERTEX_LINK,
                               f"vertex {v} has non-manifold link edge {bad[0]}")
        adjacency = [set() for _ in triangles]
        for fs in edge_to_faces.values():
            if len(fs) == 2:
                adjacency[fs[0]].add(fs[1])
                adjacency[fs[1]].add(fs[0])
        seen = set()
        components = 0
        for start in range(len(triangles)):
            if start in seen:
                continue
            components += 1
            stack = [start]
            seen.add(start)
            while stack:
                cur = stack.pop()
                for nxt in adjacency[cur] - seen:
                    seen.add(nxt)
                    stack.append(nxt)
        if components != 1:
            raise CompileError(CompilerReason.NON_MANIFOLD_VERTEX_LINK,
                               f"vertex {v} link has {components} disconnected components")
        boundary_edges = [edge for edge, fs in edge_to_faces.items() if len(fs) == 1]
        chi = len(link_vertices) - len(edge_to_faces) + len(triangles)
        if v in boundary_vertices:
            if not boundary_edges or chi != 1:
                raise CompileError(CompilerReason.NON_MANIFOLD_VERTEX_LINK,
                                   f"boundary vertex {v} link is not a disk "
                                   f"(boundary edges={len(boundary_edges)}, Euler={chi})")
            degree: dict[int, int] = {}
            boundary_graph: dict[int, set[int]] = {}
            for a, b in boundary_edges:
                degree[a] = degree.get(a, 0) + 1
                degree[b] = degree.get(b, 0) + 1
                boundary_graph.setdefault(a, set()).add(b)
                boundary_graph.setdefault(b, set()).add(a)
            if any(n != 2 for n in degree.values()):
                raise CompileError(CompilerReason.NON_MANIFOLD_VERTEX_LINK,
                                   f"boundary vertex {v} link boundary is not one cycle")
            reached = {next(iter(boundary_graph))}
            stack = list(reached)
            while stack:
                cur = stack.pop()
                for nxt in boundary_graph[cur] - reached:
                    reached.add(nxt)
                    stack.append(nxt)
            if len(reached) != len(boundary_graph):
                raise CompileError(CompilerReason.NON_MANIFOLD_VERTEX_LINK,
                                   f"boundary vertex {v} link boundary has multiple cycles")
        elif boundary_edges or chi != 2:
            raise CompileError(CompilerReason.NON_MANIFOLD_VERTEX_LINK,
                               f"interior vertex {v} link is not a sphere "
                               f"(boundary edges={len(boundary_edges)}, Euler={chi})")


def _tet_edges(q: np.ndarray) -> tuple[np.ndarray, ...]:
    return tuple(q[j] - q[i] for i, j in
                 ((0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)))


def _tetrahedra_overlap(a: np.ndarray, b: np.ndarray, scale: float) -> bool:
    """SAT for two non-degenerate convex tetrahedra; strict interior overlap only."""
    tol_world = _SAT_REL * scale
    if np.any(np.max(a, axis=0) < np.min(b, axis=0) - tol_world) \
            or np.any(np.max(b, axis=0) < np.min(a, axis=0) - tol_world):
        return False
    origin = a[0]
    # Local, nondimensional coordinates make the SAT tolerance scale-free.
    ar, br = (a - origin) / scale, (b - origin) / scale
    if not np.all(np.isfinite(ar)) or not np.all(np.isfinite(br)):
        raise CompileError(CompilerReason.NUMERIC_OVERFLOW,
                           "normalized tetrahedron coordinates are non-finite")
    edges_a, edges_b = _tet_edges(ar), _tet_edges(br)
    dirs_a, dirs_b = [], []
    for edge in edges_a:
        length = float(np.linalg.norm(edge))
        if not math.isfinite(length) or length <= 0.0:
            raise CompileError(CompilerReason.NUMERIC_OVERFLOW,
                               "invalid normalized SAT edge")
        dirs_a.append(edge / length)
    for edge in edges_b:
        length = float(np.linalg.norm(edge))
        if not math.isfinite(length) or length <= 0.0:
            raise CompileError(CompilerReason.NUMERIC_OVERFLOW,
                               "invalid normalized SAT edge")
        dirs_b.append(edge / length)
    axes: list[np.ndarray] = []
    for points in (ar, br):
        for i, j, k in ((0, 1, 2), (0, 1, 3), (0, 2, 3), (1, 2, 3)):
            axes.append(np.cross(points[j] - points[i], points[k] - points[i]))
    # Cross products of edge directions complete the polyhedron SAT axes.
    for ea in dirs_a:
        for eb in dirs_b:
            axes.append(np.cross(ea, eb))
    for axis in axes:
        n = float(np.linalg.norm(axis))
        if not math.isfinite(n):
            raise CompileError(CompilerReason.NUMERIC_OVERFLOW,
                               "tetrahedron SAT axis overflowed")
        if n <= _SAT_REL:
            continue
        unit = axis / n
        pa, pb = ar @ unit, br @ unit
        overlap = min(float(pa.max()), float(pb.max())) \
            - max(float(pa.min()), float(pb.min()))
        if overlap <= _SAT_REL:
            return False
    return True


def _check_overlaps(p: np.ndarray, t: np.ndarray, scales: np.ndarray) -> None:
    """Quadratic broad-phase + tetrahedron SAT; appropriate for reference meshes."""
    q = p[t]
    lows, highs = q.min(axis=1), q.max(axis=1)
    order = np.argsort(lows[:, 0], kind="stable")
    for oi, i in enumerate(order):
        for j in order[oi + 1:]:
            if lows[j, 0] > highs[i, 0] + _SAT_REL * max(scales[i], scales[j]):
                break
            if np.any(highs[i] < lows[j] - _SAT_REL * max(scales[i], scales[j])) \
                    or np.any(highs[j] < lows[i] - _SAT_REL * max(scales[i], scales[j])):
                continue
            scale = max(float(scales[i]), float(scales[j]))
            if _tetrahedra_overlap(q[i], q[j], scale):
                raise CompileError(CompilerReason.OVERLAPPING_TETRAHEDRA,
                                   f"cells {int(i)} and {int(j)} have intersecting interiors "
                                   f"(SAT tolerance={_SAT_REL:.3e} x max edge)")


def _catalogues(materials: Iterable[MaterialSpec],
                regions: Iterable[RegionSpec], allow_missing_density: bool = False):
    material_map: dict[str, MaterialSpec] = {}
    for material in materials:
        if not isinstance(material, MaterialSpec):
            raise CompileError(CompilerReason.BAD_SCHEMA,
                               f"materials must contain MaterialSpec records, got "
                               f"{type(material).__name__}")
        mid = _identifier(material.material_id, "material_id")
        if mid in material_map:
            raise CompileError(CompilerReason.DUPLICATE_MATERIAL_ID,
                               f"material ID {mid!r} is declared more than once")
        if material.density_kg_m3 is None:
            if not allow_missing_density:
                raise CompileError(CompilerReason.MISSING_DENSITY,
                                   f"material {mid!r} has no density; missing-density "
                                   "acceptance is validation-only opt-in")
            if material.density_source is not None and not isinstance(material.density_source, str):
                raise CompileError(CompilerReason.INVALID_DENSITY,
                                   f"material {mid!r} density_source must be text or null")
            if material.conditions is not None and not isinstance(material.conditions, str):
                raise CompileError(CompilerReason.INVALID_DENSITY,
                                   f"material {mid!r} conditions must be text or null")
            material_map[mid] = material
            continue
        if not isinstance(material.density_source, str) or not material.density_source.strip() \
                or not isinstance(material.conditions, str) or not material.conditions.strip():
            raise CompileError(CompilerReason.INVALID_DENSITY,
                               f"material {mid!r} needs non-empty density_source and conditions")
        raw_density = np.asarray(material.density_kg_m3)
        if raw_density.ndim != 0 or raw_density.dtype.kind not in "iuf":
            raise CompileError(CompilerReason.INVALID_DENSITY,
                               f"material {mid!r} density must be a numeric scalar")
        try:
            rho = float(raw_density)
        except (TypeError, ValueError, OverflowError):
            raise CompileError(CompilerReason.INVALID_DENSITY,
                               f"material {mid!r} density is not a real number")
        if not math.isfinite(rho) or rho <= 0.0:
            raise CompileError(CompilerReason.INVALID_DENSITY,
                               f"material {mid!r} density must be finite and positive")
        material_map[mid] = MaterialSpec(mid, rho, material.density_source,
                                         material.conditions)
    region_map: dict[str, RegionSpec] = {}
    owners: set[str] = set()
    for region in regions:
        if not isinstance(region, RegionSpec):
            raise CompileError(CompilerReason.BAD_SCHEMA,
                               f"regions must contain RegionSpec records, got "
                               f"{type(region).__name__}")
        rid = _identifier(region.region_id, "region_id")
        owner = _identifier(region.mass_owner_id, "mass_owner_id")
        material_id = _identifier(region.material_id, "material_id")
        if rid in region_map:
            raise CompileError(CompilerReason.DUPLICATE_REGION_ID,
                               f"region ID {rid!r} is declared more than once")
        if owner in owners:
            raise CompileError(CompilerReason.DUPLICATE_MASS_OWNER_ID,
                               f"mass owner {owner!r} is assigned to multiple regions")
        if material_id not in material_map:
            raise CompileError(CompilerReason.MISSING_MATERIAL,
                               f"region {rid!r} references absent material {material_id!r}")
        owners.add(owner)
        region_map[rid] = region
    return material_map, region_map


def _resolve_cells(cell_proposals: Sequence[Iterable[str]], n_cells: int,
                   regions: Mapping[str, RegionSpec],
                   materials: Mapping[str, MaterialSpec]) -> tuple[CellAssignment, ...]:
    if isinstance(cell_proposals, (str, bytes, Mapping)):
        raise CompileError(CompilerReason.BAD_SCHEMA,
                           "cell_proposals must be a sequence of per-cell arrays")
    try:
        row_count = len(cell_proposals)
    except TypeError:
        raise CompileError(CompilerReason.BAD_SCHEMA,
                           "cell_proposals must be a sized sequence of per-cell arrays")
    if row_count != n_cells:
        raise CompileError(CompilerReason.BAD_ASSIGNMENT_COUNT,
                           f"got {row_count} assignment rows for {n_cells} cells")
    rows: list[CellAssignment] = []
    for cell_id, proposals in enumerate(cell_proposals):
        try:
            if proposals is None or isinstance(proposals, (str, bytes, Mapping)):
                raise CompileError(CompilerReason.BAD_SCHEMA,
                                   f"cell {cell_id} proposals must be an array; "
                                   "use [] to mark the assignment explicitly unresolved")
            ids = tuple(sorted({_identifier(x, f"cell {cell_id} region proposal")
                                for x in proposals}))
        except CompileError:
            raise
        except TypeError:
            raise CompileError(CompilerReason.BAD_SCHEMA,
                               f"cell {cell_id} proposals must be an iterable of region IDs")
        unknown = [rid for rid in ids if rid not in regions]
        if unknown:
            raise CompileError(CompilerReason.UNKNOWN_REGION,
                               f"cell {cell_id} proposes unknown region ID(s): {unknown}")
        owners = tuple(sorted(regions[rid].mass_owner_id for rid in ids))
        if not ids:
            rows.append(CellAssignment(cell_id, CompilerReason.UNRESOLVED, (), (),
                                       None, None, None, None, None, None))
        elif len(ids) > 1:
            rows.append(CellAssignment(cell_id, CompilerReason.CONFLICT, ids, owners,
                                       None, None, None, None, None, None))
        else:
            region = regions[ids[0]]
            material = materials[region.material_id]
            if material.density_kg_m3 is None:
                rows.append(CellAssignment(cell_id, CompilerReason.MISSING_DENSITY,
                                           ids, owners, region.region_id,
                                           region.mass_owner_id, region.material_id,
                                           None, material.density_source,
                                           material.conditions))
            else:
                rows.append(CellAssignment(cell_id, "resolved", ids, owners,
                                           region.region_id, region.mass_owner_id,
                                           region.material_id, material.density_kg_m3,
                                           material.density_source, material.conditions))
    return tuple(rows)


def _mass_properties(p: np.ndarray, t: np.ndarray, volumes: np.ndarray,
                     cell_ids: Sequence[int], densities: np.ndarray) -> MassProperties:
    ids = np.asarray(cell_ids, dtype=np.int64)
    if ids.size == 0:
        raise CompileError(CompilerReason.INCOMPLETE,
                           "mass properties are undefined for an empty resolved-cell set")
    q = p[t[ids]]
    cell_volumes = volumes[ids]
    cell_masses = cell_volumes * densities[ids]
    if not np.all(np.isfinite(cell_masses)) or not np.all(cell_masses > 0):
        raise CompileError(CompilerReason.NUMERIC_OVERFLOW,
                           "cell mass overflowed or became non-positive")
    total_mass = float(np.sum(cell_masses, dtype=np.float64))
    total_volume = float(np.sum(cell_volumes, dtype=np.float64))
    if not (math.isfinite(total_mass) and total_mass > 0
            and math.isfinite(total_volume) and total_volume > 0):
        raise CompileError(CompilerReason.NUMERIC_OVERFLOW,
                           "mass or volume sum is non-finite/non-positive")
    cell_centres = q[:, 0] + np.sum(q[:, 1:] - q[:, :1], axis=1) / 4.0
    origin = p[0]
    com = origin + np.sum(cell_masses[:, None] * (cell_centres - origin), axis=0) / total_mass
    local = q - cell_centres[:, None, :]
    q_intrinsic = (cell_masses[:, None, None] / 20.0) * np.einsum(
        "tvi,tvj->tij", local, local)
    offset = cell_centres - com
    eye = np.eye(3)
    inertia_cells = (np.trace(q_intrinsic, axis1=1, axis2=2)[:, None, None] * eye
                     - q_intrinsic
                     + cell_masses[:, None, None] * (
                         np.einsum("ti,ti->t", offset, offset)[:, None, None] * eye
                         - np.einsum("ti,tj->tij", offset, offset)))
    inertia = np.sum(inertia_cells, axis=0, dtype=np.float64)
    inertia = 0.5 * (inertia + inertia.T)
    if not (np.all(np.isfinite(com)) and np.all(np.isfinite(inertia))):
        raise CompileError(CompilerReason.NUMERIC_OVERFLOW,
                           "center of mass or inertia overflowed")
    return MassProperties(total_volume, total_mass, tuple(map(float, com)),
                          tuple(tuple(map(float, row)) for row in inertia), int(ids.size))


def _interface_tables(p: np.ndarray, face_records, boundary_records,
                       cells: tuple[CellAssignment, ...], centroids: np.ndarray):
    interfaces: list[MaterialInterface] = []
    unresolved: list[UnresolvedAdjacency] = []
    boundaries: list[BoundaryFace] = []
    seen: set[tuple[int, int, int]] = set()
    for key, cell_id, oriented in boundary_records:
        assignment = cells[cell_id]
        boundaries.append(BoundaryFace(key, oriented, cell_id, assignment.region_id))
    for key, sides in face_records.items():
        if len(sides) != 2:
            continue
        (cell_x, face_x), (cell_y, face_y) = sides
        ax, ay = cells[cell_x], cells[cell_y]
        if ax.region_id is None or ay.region_id is None:
            unresolved.append(UnresolvedAdjacency(
                key, tuple(sorted((cell_x, cell_y))), (ax.status, ay.status)))
            continue
        if ax.region_id == ay.region_id:
            continue
        if key in seen:
            raise CompileError(CompilerReason.INCONSISTENT_FACE_ORIENTATION,
                               f"shared interface {key} was extracted more than once")
        seen.add(key)
        if ax.region_id < ay.region_id:
            ca, fa, cb, cell_a, cell_b = ax, face_x, ay, cell_x, cell_y
        else:
            ca, fa, cb, cell_a, cell_b = ay, face_y, ax, cell_y, cell_x
        tri = p[np.asarray(fa, dtype=np.int64)]
        cross = np.cross(tri[1] - tri[0], tri[2] - tri[0])
        area2 = float(np.linalg.norm(cross))
        if not math.isfinite(area2) or area2 <= 0.0:
            raise CompileError(CompilerReason.DEGENERATE_TETRAHEDRON,
                               f"interface face {key} has invalid area")
        normal = cross / area2
        toward_b = centroids[cell_b] - centroids[cell_a]
        if float(np.dot(normal, toward_b)) <= 0.0:
            raise CompileError(CompilerReason.INCONSISTENT_FACE_ORIENTATION,
                               f"face {key} normal does not point from region "
                               f"{ca.region_id!r} to {cb.region_id!r}")
        interfaces.append(MaterialInterface(
            key, fa, ca.region_id, cb.region_id, ca.mass_owner_id,
            cb.mass_owner_id, ca.material_id, cb.material_id,
            0.5 * area2, tuple(map(float, normal))))
    interfaces.sort(key=lambda face: face.face_key)
    boundaries.sort(key=lambda face: face.face_key)
    unresolved.sort(key=lambda face: face.face_key)
    return tuple(interfaces), tuple(boundaries), tuple(unresolved)


def _canonical_geometry_signature(p: np.ndarray, t: np.ndarray) -> str:
    """Order/renumber-invariant signature of the exact finite input geometry.

    Coordinates are serialized as exact float64 hexadecimal tokens. Cells are
    keyed by sorted vertex-coordinate tokens; this identifies exact same
    coordinates/connectivity after a cell shuffle or vertex-ID bijection, but
    intentionally changes under rigid transform, scaling, or subdivision.
    """
    vertex_tokens = [tuple(float(x).hex() for x in row) for row in p]
    cell_tokens = sorted(tuple(sorted(vertex_tokens[int(i)] for i in row)) for row in t)
    payload = json.dumps(cell_tokens, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def _count_components(face_records, n_cells: int) -> int:
    graph = [set() for _ in range(n_cells)]
    for sides in face_records.values():
        if len(sides) == 2:
            a, b = sides[0][0], sides[1][0]
            graph[a].add(b)
            graph[b].add(a)
    seen: set[int] = set()
    count = 0
    for start in range(n_cells):
        if start in seen:
            continue
        count += 1
        seen.add(start)
        stack = [start]
        while stack:
            for nxt in graph[stack.pop()] - seen:
                seen.add(nxt)
                stack.append(nxt)
    return count


def compile_partition(vertices_m, tetrahedra, materials: Iterable[MaterialSpec],
                      regions: Iterable[RegionSpec],
                      cell_proposals: Sequence[Iterable[str]], *,
                      allow_missing_density: bool = False) -> CompiledPartition:
    """Compile a conforming, closed, positively oriented tetrahedral partition.

    Parameters
    ----------
    vertices_m:
        Finite numeric ``(nV,3)`` positions in meters. Exact duplicate
        coordinates and unused vertices are refused; no welding is attempted.
    tetrahedra:
        Integral ``(nT,4)`` vertex IDs. Every row must be positively oriented
        in the right-handed input frame, unique, and nondegenerate. The mesh is
        required to be conforming, watertight, and a combinatorial 3-manifold.
    materials:
        Unique ``MaterialSpec`` records. Density is finite and positive in kg/m^3
        unless ``allow_missing_density=True``; that opt-in is diagnostic-only and
        leaves affected cells explicitly missing_density with no mass properties.
        No unit conversion/default occurs.
    regions:
        Unique region IDs and unique mass-owner IDs. Each region references one
        known material. ``stiffness_pa`` is carried only as metadata and is
        never read by mass or inertia calculations.
    cell_proposals:
        Exactly one row per tetrahedron, each containing zero or more region
        IDs. Empty => unresolved; one distinct ID => resolved; multiple distinct
        IDs => explicit conflict. Duplicate identical IDs collapse to consensus.
        Unknown IDs are a named input refusal, never a default material.

    The exact-total mass properties are ``None`` until every cell has a unique
    owner/material and known density. ``resolved_only_subtotal`` is explicitly
    partial and is not a body total.
    """
    p = _positions(vertices_m)
    t = _tetrahedra(tetrahedra, p.shape[0])
    material_map, region_map = _catalogues(materials, regions, allow_missing_density)
    volumes, centroids, scales = _geometry(p, t)
    face_records = _face_records(t)
    boundary_records = _face_orientation_and_boundary(face_records)
    boundary_vertices = _check_closed_boundary(boundary_records)
    _check_vertex_links(t, boundary_vertices)
    _check_overlaps(p, t, scales)
    cell_rows = _resolve_cells(cell_proposals, t.shape[0], region_map, material_map)
    # Unresolved/conflicted cells carry an explicit NaN sentinel internally;
    # no numeric density default is assigned. Only resolved indices are ever
    # passed to an integration routine, and their public density field is None
    # unless a unique material/owner assignment was made.
    densities = np.full(t.shape[0], np.nan, dtype=np.float64)
    resolved_ids: list[int] = []
    by_region: dict[str, list[int]] = {}
    for row in cell_rows:
        if row.status == "resolved":
            assert row.region_id is not None and row.density_kg_m3 is not None
            densities[row.cell_id] = row.density_kg_m3
            resolved_ids.append(row.cell_id)
            by_region.setdefault(row.region_id, []).append(row.cell_id)
    complete = all(c.status == "resolved" for c in cell_rows)
    subtotal = (_mass_properties(p, t, volumes, resolved_ids, densities)
                if resolved_ids else None)
    total = subtotal if complete else None
    region_subtotals = {
        rid: _mass_properties(p, t, volumes, ids, densities)
        for rid, ids in sorted(by_region.items())
    }
    interfaces, boundary_faces, unresolved_adj = _interface_tables(
        p, face_records, boundary_records, cell_rows, centroids)
    geom_volume = float(np.sum(volumes, dtype=np.float64))
    if not math.isfinite(geom_volume) or geom_volume <= 0:
        raise CompileError(CompilerReason.NUMERIC_OVERFLOW,
                           "geometric volume sum is non-finite/non-positive")
    geometry_signature = _canonical_geometry_signature(p, t)
    return CompiledPartition(
        complete, cell_rows, geom_volume, total, subtotal, region_subtotals,
        geometry_signature, interfaces, boundary_faces, unresolved_adj,
        _count_components(face_records, t.shape[0]))


def compile_document(document: Mapping, *, allow_missing_density: bool = False) -> dict:
    """Compile the versioned JSON contract; missing density is opt-in diagnostic-only."""
    if not isinstance(document, Mapping):
        raise CompileError(CompilerReason.BAD_SCHEMA, "top-level JSON value must be an object")
    required = {"schema_version", "coordinate_unit", "density_unit", "mass_source_kind",
                "vertices_m", "tetrahedra", "materials", "regions", "cell_proposals"}
    missing = sorted(required - set(document))
    extra = sorted(set(document) - required)
    if extra:
        raise CompileError(CompilerReason.BAD_SCHEMA,
                           f"unknown fields are refused (prevents ignored mass inputs): {extra}")
    if missing:
        raise CompileError(CompilerReason.BAD_SCHEMA, f"missing required fields: {missing}")
    if document["mass_source_kind"] != MassSourceKind.MATERIAL_VOLUME:
        raise CompileError(CompilerReason.MIXED_MASS_REPRESENTATIONS,
                           "v1 requires mass_source_kind='reconstructed_material_volume'; "
                           "effective skeletal-segment or thin-sheet mass is not importable")
    if document["schema_version"] != "chimera.material_volume.v1":
        raise CompileError(CompilerReason.BAD_SCHEMA,
                           "schema_version must be 'chimera.material_volume.v1'")
    if document["coordinate_unit"] != "m" or document["density_unit"] != "kg/m^3":
        raise CompileError(CompilerReason.BAD_SCHEMA,
                           "v1 accepts coordinate_unit='m' and density_unit='kg/m^3' only")
    try:
        if not isinstance(document["materials"], list) or not isinstance(document["regions"], list):
            raise TypeError("materials and regions must be JSON arrays")
        materials = [MaterialSpec(**item) for item in document["materials"]]
        regions = [RegionSpec(**item) for item in document["regions"]]
    except (TypeError, ValueError) as ex:
        raise CompileError(CompilerReason.BAD_SCHEMA,
                           f"malformed material/region record: {ex}")

    result = compile_partition(document["vertices_m"], document["tetrahedra"],
                               materials, regions, document["cell_proposals"],
                               allow_missing_density=allow_missing_density)
    return result.to_dict()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_json", help="v1 input document; result JSON is written to stdout")
    args = parser.parse_args(argv)
    try:
        with Path(args.input_json).open("r", encoding="utf-8") as f:
            document = json.load(f)
        result = compile_document(document)
    except (OSError, json.JSONDecodeError, CompileError) as ex:
        reason = getattr(ex, "reason", "input_error")
        print(json.dumps({"error": reason, "detail": str(ex)}), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0 if result["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
