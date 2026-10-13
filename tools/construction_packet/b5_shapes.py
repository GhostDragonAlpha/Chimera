"""B5 shape battery — concavity, holes and branch junctions through the
ORIGINAL compiler, plus the refusal controls that prove nothing is filled
silently.  This is the §13 B5 "broaden shape" half of the gate for the SEALED
construction plan (docs/GAME_PLAN_ACTION_RPG.md); the "reuse function" half is
tools/construction_packet/test_b5_bridge.py against the resident runtime.

Nothing here extends tools/material_volume.py: its checks (closed boundary,
manifold faces/links, positive orientation, no overlap, explicit ownership)
are genus-agnostic, so the extension is authoring qualified meshes and
proving them — acceptance of a genus-1 ring by the unchanged compiler is
itself the evidence that cutting/meshing was never sphere-only.

Shapes (acceptance-gallery mapping)
-----------------------------------
ring_frame        gallery #4 "a ring's hole remains a hole": a rectangular
                  tube closed into a loop (genus 1) meshed as 8 conforming
                  grid boxes; compiled volume equals the analytic ring volume,
                  the boundary surface has Euler characteristic 0, and a point
                  in the hole stays outside the solid.
concave_l         gallery #4 concave half: an L solid as two regions; the
                  union is non-convex (bounding-box volume exceeds compiled
                  volume; a notch probe is outside by ray parity), the shared
                  wall is counted once.
triple_junction   gallery #5: three regions whose walls meet along one edge;
                  exactly three region pairs share faces, the junction edge
                  lies in all three walls, no wall is duplicated, and the
                  region volumes sum exactly to the envelope volume (no gap,
                  no overlap).
chamber_oblique   gallery #3: a lopsided chamber (uneven footprint, oblique
                  plan) partitioned by an oblique planar interface into two
                  regions; each region closes on its own, the separator is
                  one wall with the intended normal orientation, and mass /
                  volume / COM inventories are preserved under the split.

Refusal controls (gallery #4 "reject unsupported geometry instead of filling
it silently"): a pinched ring (edge self-contact, four boundary faces at the
pinch edge) is refused as non-manifold, never welded or filled; an open shell
of the ring's wall is refused as degenerate; an inverted ring cell is refused.

Run:  python tools/construction_packet/b5_shapes.py   (prints the inventory)
"""
from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import material_volume as mv  # noqa: E402
from material_volume import CompileError, CompilerReason, MaterialSpec, RegionSpec  # noqa: E402

PROV = "B5 fixture - nominal value, assumed, not measured"
COND = "dry, 293 K assumed"

MAT_GRANITE = MaterialSpec("mat_b5_granite", 2700.0, PROV, COND)
MAT_STEEL = MaterialSpec("mat_b5_steel", 7850.0, PROV, COND)
MAT_TIMBER = MaterialSpec("mat_b5_timber", 600.0, PROV, COND)
MAT_CORK = MaterialSpec("mat_b5_cork", 240.0, PROV, COND)
MAT_ALLOY = MaterialSpec("mat_b5_alloy", 6100.0, PROV, COND)


# --------------------------------------------------------------------------
# Mesh authoring helpers.  Boxes are split by the Freudenthal/Kuhn triangula-
# tion from the minimum corner: two grid-adjacent boxes then triangulate their
# shared rectangle along the SAME diagonal, so the union is conforming without
# any welding.  Orientation is fixed at authoring time by signed volume; the
# compiler still refuses anything inverted, so acceptance remains the proof.
# --------------------------------------------------------------------------
def _pos_tet(p: np.ndarray, a: int, b: int, c: int, d: int) -> list[int]:
    q = p[np.array([a, b, c, d])]
    if np.linalg.det(q[1:] - q[0]) < 0.0:
        return [a, b, d, c]
    return [a, b, c, d]


def kuhn_hex_tets(vids: list[int]) -> list[list[int]]:
    """6 tetrahedra for the combinatorial cube vids[0..7] (vids[1]/[2]/[4] are
    the edge neighbours of vids[0], vids[7] the opposite corner), each
    positively oriented in the caller's positions (passed via _pos_tet)."""
    out = []
    for perm in itertools.permutations((1, 2, 4)):
        a, b, c = perm
        out.append([vids[0], vids[a], vids[a + b], vids[7]])
    return out


class _VertexBook:
    """Exact-coordinate vertex dedup: shared grid points become shared IDs,
    and the compiler's duplicate-position refusal never sees a repeat."""

    def __init__(self) -> None:
        self.positions: list[tuple[float, float, float]] = []
        self._index: dict[tuple[float, float, float], int] = {}

    def add(self, p: tuple[float, float, float]) -> int:
        key = tuple(float(x) for x in p)
        if key in self._index:
            return self._index[key]
        self._index[key] = len(self.positions)
        self.positions.append(key)
        return self._index[key]

    def box(self, x0: float, x1: float, y0: float, y1: float,
            z0: float, z1: float) -> list[list[int]]:
        """Kuhn-split axis-aligned box; returns its 6 tets over shared IDs."""
        v = [self.add(c) for c in (
            (x0, y0, z0), (x1, y0, z0), (x0, y1, z0), (x1, y1, z0),
            (x0, y0, z1), (x1, y0, z1), (x0, y1, z1), (x1, y1, z1))]
        return kuhn_hex_tets(v)


def _orient(p: np.ndarray, tets: list[list[int]]) -> list[list[int]]:
    return [_pos_tet(p, *t) for t in tets]


# --------------------------------------------------------------------------
# Surface analysis: genus of the compiled boundary and point-in-solid parity.
# The compiled boundary faces ARE the collision triangles a runtime would
# consume, so the parity test is the collision agreement witness: what the
# compiler calls exterior is exactly what a contact query calls outside.
# --------------------------------------------------------------------------
def boundary_genus(boundary_faces) -> tuple[int, int]:
    """(Euler characteristic, genus) of the closed boundary surface."""
    verts: set[int] = set()
    edges: set[tuple[int, int]] = set()
    faces = 0
    for f in boundary_faces:
        a, b, c = f.vertices
        verts.update((a, b, c))
        edges.update(((min(a, b), max(a, b)), (min(b, c), max(b, c)),
                      (min(c, a), max(c, a))))
        faces += 1
    chi = len(verts) - len(edges) + faces
    return chi, (2 - chi) // 2


def inside_solid(vertices, boundary_faces, point: tuple[float, float, float]) -> bool:
    """Ray-crossing parity along +x against the boundary triangles."""
    p = np.asarray(vertices, dtype=np.float64)
    o = np.asarray(point, dtype=np.float64)
    count = 0
    for f in boundary_faces:
        v0, v1, v2 = p[list(f.vertices)]
        e1, e2 = v1 - v0, v2 - v0
        h = np.cross((1.0, 0.0, 0.0), e2)
        det = float(np.dot(e1, h))
        if abs(det) < 1e-15:
            continue
        s = o - v0
        u = float(np.dot(s, h)) / det
        if not (0.0 <= u <= 1.0):
            continue
        q = np.cross(s, e1)
        v = float(np.dot((1.0, 0.0, 0.0), q)) / det
        if v < 0.0 or u + v > 1.0:
            continue
        t = float(np.dot(e2, q)) / det
        if t > 0.0:
            count += 1
    return count % 2 == 1


# --------------------------------------------------------------------------
# Ring frame (genus 1): 3x3 grid of boxes minus the centre cell.
# --------------------------------------------------------------------------
RING_GX = (-0.30, -0.20, 0.20, 0.30)
RING_GY = (-0.30, -0.20, 0.20, 0.30)
RING_GZ = (0.0, 0.10)
RING_VOLUME_M3 = 0.020  # 4 bars: 2 x 0.6*0.1*0.1 + 2 x 0.4*0.1*0.1


def ring_geometry(pinch: bool = False) -> tuple[list, list[list[int]]]:
    """pinch=False: the conforming genus-1 frame.  pinch=True: the bottom
    edge box is slid one tube thickness to y in [-0.2, -0.1] (exact literals,
    so the contact vertices dedupe), pinching the ring to edge contact with
    the corner boxes — a non-manifold boundary the compiler must refuse
    rather than accept or fill."""
    book = _VertexBook()
    tets: list[list[int]] = []
    for ix in range(3):
        for iy in range(3):
            if (ix, iy) == (1, 1):
                continue  # the hole: no cell, and nothing fills it
            y0, y1 = RING_GY[iy], RING_GY[iy + 1]
            if pinch and (ix, iy) == (1, 0):
                y0, y1 = -0.2, -0.1
            tets += book.box(RING_GX[ix], RING_GX[ix + 1], y0, y1, *RING_GZ)
    p = np.asarray(book.positions, dtype=np.float64)
    return list(book.positions), _orient(p, tets)


RING_REGION = RegionSpec("region_ring_frame", "part_ring_frame",
                         MAT_GRANITE.material_id, 5.0e10)


def compile_ring(pinch: bool = False) -> mv.CompiledPartition:
    vertices, tets = ring_geometry(pinch)
    return mv.compile_partition(vertices, tets, [MAT_GRANITE], [RING_REGION],
                                [[RING_REGION.region_id]] * len(tets))


# --------------------------------------------------------------------------
# Concave L: two regions, non-convex union.
# --------------------------------------------------------------------------
# The tall leg is authored as two stacked boxes so its shared rectangle with
# the flat leg (x = 0.2, z in [0, 0.2]) is conforming; both boxes stay in
# region A, so the A|B separator remains exactly one wall.
L_LEG_A = ((0.0, 0.2, 0.0, 0.2, 0.0, 0.2), (0.0, 0.2, 0.0, 0.2, 0.2, 0.4))
L_LEG_B = (0.2, 0.6, 0.0, 0.2, 0.0, 0.2)     # flat leg
L_VOLUME_M3 = 0.032

L_REGION_A = RegionSpec("region_l_tall", "part_l_tall",
                        MAT_GRANITE.material_id, 5.0e10)
L_REGION_B = RegionSpec("region_l_flat", "part_l_flat",
                        MAT_TIMBER.material_id, 1.0e10)


def l_geometry() -> tuple[list, list[list[int]], list[list[str]]]:
    book = _VertexBook()
    tets_a = book.box(*L_LEG_A[0]) + book.box(*L_LEG_A[1])
    tets_b = book.box(*L_LEG_B)
    p = np.asarray(book.positions, dtype=np.float64)
    proposals = ([[L_REGION_A.region_id]] * len(tets_a)
                 + [[L_REGION_B.region_id]] * len(tets_b))
    return list(book.positions), _orient(p, tets_a + tets_b), proposals


def compile_l() -> mv.CompiledPartition:
    vertices, tets, proposals = l_geometry()
    return mv.compile_partition(vertices, tets, [MAT_GRANITE, MAT_TIMBER],
                                [L_REGION_A, L_REGION_B], proposals)


# --------------------------------------------------------------------------
# Triple junction: three regions, walls meeting along the edge
# x = 0.3, z = 0.2 (parallel to y).  Region A owns both left boxes (its own
# internal face is same-region and therefore NOT a wall).
# --------------------------------------------------------------------------
TJ_BOXES = [
    ("region_tj_a", (0.0, 0.3, 0.0, 0.2, 0.0, 0.2), MAT_GRANITE),
    ("region_tj_a", (0.0, 0.3, 0.0, 0.2, 0.2, 0.4), MAT_GRANITE),
    ("region_tj_b", (0.3, 0.6, 0.0, 0.2, 0.2, 0.4), MAT_STEEL),
    ("region_tj_c", (0.3, 0.6, 0.0, 0.2, 0.0, 0.2), MAT_TIMBER),
]
TJ_VOLUME_M3 = 0.6 * 0.2 * 0.4
TJ_JUNCTION_EDGE = ((0.3, 0.0, 0.2), (0.3, 0.2, 0.2))


def tj_geometry() -> tuple[list, list[list[int]], list[list[str]],
                           list[MaterialSpec], list[RegionSpec]]:
    book = _VertexBook()
    tets: list[list[int]] = []
    proposals: list[list[str]] = []
    mats: dict[str, MaterialSpec] = {}
    regions: dict[str, RegionSpec] = {}
    for rid, box, mat in TJ_BOXES:
        mats[mat.material_id] = mat
        regions.setdefault(
            rid, RegionSpec(rid, "part_" + rid[len("region_"):],
                            mat.material_id, 5.0e10))
        bt = book.box(*box)
        tets += bt
        proposals += [[rid]] * len(bt)
    p = np.asarray(book.positions, dtype=np.float64)
    return (list(book.positions), _orient(p, tets), proposals,
            list(mats.values()), list(regions.values()))


def compile_tj() -> mv.CompiledPartition:
    vertices, tets, proposals, mats, regions = tj_geometry()
    return mv.compile_partition(vertices, tets, mats, regions, proposals)


# --------------------------------------------------------------------------
# Lopsided chamber, obliquely partitioned.  Uneven footprint quad, two
# parallel oblique planes z = c + sx*x + sy*y (lower solid) and +0.18 higher
# (upper solid); the shared interface is the oblique quad, triangulated along
# the same diagonal from both sides.
# --------------------------------------------------------------------------
CH_FOOTPRINT = ((0.00, 0.00), (0.62, 0.02), (0.55, 0.47), (0.04, 0.43))
CH_SX, CH_SY, CH_C0, CH_DZ = 0.15, 0.10, 0.12, 0.18

CH_REGION_LOWER = RegionSpec("region_chamber_lower", "owner_chamber_lower",
                             MAT_CORK.material_id, 3.0e7)
CH_REGION_UPPER = RegionSpec("region_chamber_upper", "owner_chamber_upper",
                             MAT_ALLOY.material_id, 7.0e10)


def _ch_plane(x: float, y: float, c: float) -> float:
    return c + CH_SX * x + CH_SY * y


def chamber_geometry() -> tuple[list, list[list[int]], list[list[str]]]:
    book = _VertexBook()
    b = [book.add((x, y, 0.0)) for x, y in CH_FOOTPRINT]
    i = [book.add((x, y, _ch_plane(x, y, CH_C0))) for x, y in CH_FOOTPRINT]
    t = [book.add((x, y, _ch_plane(x, y, CH_C0 + CH_DZ))) for x, y in CH_FOOTPRINT]
    # Kuhn bit order on each quad face: v0,v1,v2,v3 = (00,10,01,11), i.e. the
    # cyclic footprint (0,1,2,3) enters as (0,1,3,2) so v3 is face-diagonal.
    quad = (0, 1, 3, 2)
    lower = kuhn_hex_tets([b[k] for k in quad] + [i[k] for k in quad])
    upper = kuhn_hex_tets([i[k] for k in quad] + [t[k] for k in quad])
    p = np.asarray(book.positions, dtype=np.float64)
    proposals = ([[CH_REGION_LOWER.region_id]] * 6
                 + [[CH_REGION_UPPER.region_id]] * 6)
    return list(book.positions), _orient(p, lower + upper), proposals


def compile_chamber() -> mv.CompiledPartition:
    vertices, tets, proposals = chamber_geometry()
    return mv.compile_partition(vertices, tets, [MAT_CORK, MAT_ALLOY],
                                [CH_REGION_LOWER, CH_REGION_UPPER], proposals)


def compile_chamber_region(region: RegionSpec, material: MaterialSpec,
                           which: str) -> mv.CompiledPartition:
    """One chamber region alone: it must close on its own (the intended
    orientation proof for each side of the separator)."""
    vertices, tets, _ = chamber_geometry()
    sel = tets[:6] if which == "lower" else tets[6:]
    keep = sorted({v for tet in sel for v in tet})
    remap = {old: new for new, old in enumerate(keep)}
    sub_verts = [vertices[i] for i in keep]
    sub_tets = [[remap[v] for v in tet] for tet in sel]
    return mv.compile_partition(sub_verts, sub_tets, [material], [region],
                                [[region.region_id]] * len(sub_tets))


def chamber_interface_area_m2() -> float:
    """Analytic area of the oblique interface quad (same diagonal as the
    mesh: I0-I2)."""
    pts = [np.array((x, y, _ch_plane(x, y, CH_C0))) for x, y in CH_FOOTPRINT]
    a = 0.5 * np.linalg.norm(np.cross(pts[1] - pts[0], pts[2] - pts[0]))
    b = 0.5 * np.linalg.norm(np.cross(pts[2] - pts[0], pts[3] - pts[0]))
    return float(a + b)


def chamber_plane_normal() -> np.ndarray:
    n = np.array([-CH_SX, -CH_SY, 1.0])
    return n / np.linalg.norm(n)


# --------------------------------------------------------------------------
# Refusal controls.  Each returns the CompileError the compiler raised.
# --------------------------------------------------------------------------
def refusal_pinched_ring() -> CompileError:
    """The bottom edge box slid one full tube thickness: the ring now touches
    itself along two edges, and each pinch edge is incident to four boundary
    faces.  A non-manifold solid is refused outright — the compiler neither
    welds the pinch apart nor fills the intruded hole."""
    try:
        compile_ring(pinch=True)
    except CompileError as ex:
        return ex
    raise AssertionError("pinched ring was accepted")


def refusal_open_ring_shell() -> CompileError:
    """The ring's outer wall alone, as a flat tetrahedron: an open surface
    cannot stand in for the solid ring and is refused as degenerate."""
    vertices = [[-0.3, -0.3, 0.0], [0.3, -0.3, 0.0],
                [-0.3, -0.3, 0.1], [0.3, -0.3, 0.1]]
    try:
        mv.compile_partition(vertices, [[0, 1, 2, 3]], [MAT_GRANITE],
                             [RING_REGION], [[RING_REGION.region_id]])
    except CompileError as ex:
        return ex
    raise AssertionError("open ring shell was accepted")


def refusal_inverted_ring() -> CompileError:
    vertices, tets = ring_geometry()
    tets[0] = [tets[0][0], tets[0][1], tets[0][3], tets[0][2]]
    try:
        mv.compile_partition(vertices, tets, [MAT_GRANITE], [RING_REGION],
                             [[RING_REGION.region_id]] * len(tets))
    except CompileError as ex:
        return ex
    raise AssertionError("inverted ring cell was accepted")


# --------------------------------------------------------------------------
# Inventory (prints with python b5_shapes.py; the test battery asserts on it).
# --------------------------------------------------------------------------
def _part_summary(part: mv.CompiledPartition) -> dict[str, Any]:
    chi, genus = boundary_genus(part.boundary_faces)
    return {
        "cell_count": len(part.cells),
        "complete": part.complete,
        "ownership_complete": part.ownership_complete,
        "connected_components": part.connected_components,
        "geometric_volume_m3": part.geometric_volume_m3,
        "mass_kg": part.mass_properties.mass_kg if part.mass_properties else None,
        "boundary_euler_chi": chi,
        "boundary_genus": genus,
        "interface_count": len(part.interfaces),
        "interface_region_pairs": sorted({(i.region_a_id, i.region_b_id)
                                          for i in part.interfaces}),
        "interface_area_total_m2": sum(i.area_m2 for i in part.interfaces),
    }


def b5_inventory() -> dict:
    ring = compile_ring()
    lpart = compile_l()
    tj = compile_tj()
    ch = compile_chamber()
    return {
        "battery": "construction_packet_B5_shapes",
        "compiler": "tools/material_volume.py schema chimera.material_volume.v1 (unchanged)",
        "shapes": {
            "ring_frame": _part_summary(ring),
            "concave_l": _part_summary(lpart),
            "triple_junction": _part_summary(tj),
            "chamber_oblique": _part_summary(ch),
        },
        "chamber": {
            "interface_area_analytic_m2": chamber_interface_area_m2(),
            "plane_normal": list(chamber_plane_normal()),
        },
        "refusal_controls": {
            "pinched_ring": refusal_pinched_ring().reason,
            "open_ring_shell": refusal_open_ring_shell().reason,
            "inverted_ring": refusal_inverted_ring().reason,
        },
    }


def main(argv=None) -> int:
    print(json.dumps(b5_inventory(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
