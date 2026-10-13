"""B5 shape battery: torus, concave partition, triple junction, oblique
chamber cut — all through the UNCHANGED material_volume compiler — plus the
refusal controls proving unsupported geometry is rejected, never filled.

Section 13 B5 evidence column, compiler half: "torus/concave/triple-junction
cases pass".  Acceptance gallery #3 (oblique partition of a lopsided chamber:
regions close, separator counted once, inventory preserved), #4 (concave/holed
section: a ring's hole remains a hole, collision agrees, unsupported geometry
refused) and #5 (three-way junction: no duplicated wall, no gap, no ambiguous
ownership) are asserted here as measured properties, not narrated.

Pure Python: no engine required.

Run:  python tools/construction_packet/test_b5_shapes.py
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
for p in (str(HERE), str(HERE.parent)):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np

import b5_shapes as b5
import material_volume as mv


def _rel(a: float, b: float) -> float:
    return abs(a - b) / max(abs(b), 1e-300)


def _subtotals_add_up(test: unittest.TestCase, part: mv.CompiledPartition) -> None:
    """Material inventory is preserved under the partition: region subtotals
    re-sum to the exact total (volume, mass, and mass-weighted COM)."""
    total = part.mass_properties
    subs = list(part.resolved_region_subtotals.values())
    test.assertLess(_rel(sum(s.volume_m3 for s in subs), total.volume_m3), 1e-12)
    test.assertLess(_rel(sum(s.mass_kg for s in subs), total.mass_kg), 1e-12)
    com = np.array(total.center_of_mass_m)
    mix = sum(s.mass_kg * np.array(s.center_of_mass_m) for s in subs) / total.mass_kg
    for i in range(3):
        test.assertLess(_rel(mix[i], com[i]), 1e-9)


class B5Shapes(unittest.TestCase):
    # ── gallery #4: a ring's hole remains a hole ───────────────────────────
    def test_ring_frame_genus_one(self):
        part = b5.compile_ring()
        self.assertTrue(part.complete)
        self.assertTrue(part.ownership_complete)
        self.assertEqual(part.connected_components, 1)
        self.assertLess(_rel(part.geometric_volume_m3, b5.RING_VOLUME_M3), 1e-12)
        self.assertLess(_rel(part.mass_properties.mass_kg,
                             b5.RING_VOLUME_M3 * 2700.0), 1e-12)
        chi, genus = b5.boundary_genus(part.boundary_faces)
        self.assertEqual(chi, 0, "ring boundary Euler characteristic")
        self.assertEqual(genus, 1, "a ring's hole must survive compilation")
        # the hole is not filled: compiled volume is well under the envelope
        self.assertLess(part.geometric_volume_m3, 0.6 * 0.6 * 0.1)
        # collision agreement: the compiled boundary faces ARE the collision
        # triangles, and a point query on them keeps the hole outside.
        # (Probes avoid the Kuhn wall diagonals, where parity is degenerate.)
        verts, _ = b5.ring_geometry()
        self.assertFalse(b5.inside_solid(verts, part.boundary_faces, (0.0, 0.0, 0.03)),
                         "hole centre must be outside the solid")
        self.assertTrue(b5.inside_solid(verts, part.boundary_faces, (0.0, -0.25, 0.03)))
        self.assertTrue(b5.inside_solid(verts, part.boundary_faces, (-0.25, 0.07, 0.03)))
        self.assertFalse(b5.inside_solid(verts, part.boundary_faces, (0.0, 0.0, 0.30)))

    def test_ring_refusals_never_fill_silently(self):
        self.assertEqual(b5.refusal_pinched_ring().reason,
                         mv.CompilerReason.NON_MANIFOLD_BOUNDARY)
        self.assertEqual(b5.refusal_open_ring_shell().reason,
                         mv.CompilerReason.DEGENERATE_TETRAHEDRON)
        self.assertEqual(b5.refusal_inverted_ring().reason,
                         mv.CompilerReason.INVERTED_TETRAHEDRON)

    # ── gallery #4 concave half + inventory under a partition ──────────────
    def test_concave_l_partition(self):
        part = b5.compile_l()
        self.assertTrue(part.complete)
        self.assertEqual(part.connected_components, 1)
        _subtotals_add_up(self, part)
        chi, genus = b5.boundary_genus(part.boundary_faces)
        self.assertEqual((chi, genus), (2, 0))
        # the separator is counted once: one region pair, one rectangle of
        # shared faces (two conforming triangles), area 0.2 * 0.2
        pairs = {(i.region_a_id, i.region_b_id) for i in part.interfaces}
        self.assertEqual(pairs, {("region_l_flat", "region_l_tall")})
        self.assertEqual(len(part.interfaces), 2)
        self.assertLess(_rel(sum(i.area_m2 for i in part.interfaces), 0.04), 1e-12)
        # concavity: the union is strictly inside its bounding box, and the
        # notch point is outside by collision parity while both legs are in
        self.assertLess(part.geometric_volume_m3, 0.6 * 0.2 * 0.4)
        verts, tets, _ = b5.l_geometry()
        self.assertFalse(b5.inside_solid(verts, part.boundary_faces, (0.4, 0.11, 0.3)),
                         "notch point must stay outside the L")
        for probe in ((0.1, 0.13, 0.31), (0.4, 0.13, 0.07), (0.1, 0.13, 0.07)):
            self.assertTrue(b5.inside_solid(verts, part.boundary_faces, probe),
                            f"leg point {probe} must be inside")

    # ── gallery #5: three-way junction ─────────────────────────────────────
    def test_triple_junction(self):
        part = b5.compile_tj()
        self.assertTrue(part.complete)
        self.assertTrue(part.ownership_complete)
        self.assertEqual(part.conflicting_cell_ids, ())
        self.assertEqual(part.connected_components, 1)
        _subtotals_add_up(self, part)
        # no gap and no duplicated wall: region volumes sum to the envelope
        self.assertLess(_rel(part.geometric_volume_m3, b5.TJ_VOLUME_M3), 1e-12)
        pairs = {(i.region_a_id, i.region_b_id) for i in part.interfaces}
        self.assertEqual(pairs, {("region_tj_a", "region_tj_b"),
                                 ("region_tj_a", "region_tj_c"),
                                 ("region_tj_b", "region_tj_c")})
        # three walls, each one rectangle (two triangles), meeting along the
        # junction edge: EVERY interface triangle carries a junction vertex
        verts, _, _, _, _ = b5.tj_geometry()
        jv = set()
        for jp in b5.TJ_JUNCTION_EDGE:
            ids = [i for i, v in enumerate(verts)
                   if all(abs(float(v[k]) - jp[k]) < 1e-12 for k in range(3))]
            self.assertEqual(len(ids), 1, f"junction point {jp} must be one vertex")
            jv.add(ids[0])
        self.assertEqual(len(jv), 2)
        for iface in part.interfaces:
            self.assertTrue(set(iface.vertices) & jv,
                            f"wall {iface.region_a_id}|{iface.region_b_id} "
                            "must meet the junction edge")
        self.assertLess(_rel(sum(i.area_m2 for i in part.interfaces), 0.14), 1e-12)
        # ownership is unambiguous: one probe per region inside, outside out
        self.assertTrue(b5.inside_solid(verts, part.boundary_faces, (0.15, 0.13, 0.07)))
        self.assertTrue(b5.inside_solid(verts, part.boundary_faces, (0.45, 0.13, 0.31)))
        self.assertTrue(b5.inside_solid(verts, part.boundary_faces, (0.45, 0.13, 0.07)))
        self.assertFalse(b5.inside_solid(verts, part.boundary_faces, (0.7, 0.13, 0.07)))

    # ── gallery #3: oblique partition of a lopsided chamber ────────────────
    def test_chamber_oblique_partition(self):
        part = b5.compile_chamber()
        self.assertTrue(part.complete)
        self.assertEqual(part.connected_components, 1)
        _subtotals_add_up(self, part)
        # the separator is counted once and is a single oblique wall
        pairs = {(i.region_a_id, i.region_b_id) for i in part.interfaces}
        self.assertEqual(pairs, {("region_chamber_lower", "region_chamber_upper")})
        self.assertEqual(len(part.interfaces), 2)  # one quad, two conforming tris
        self.assertLess(_rel(sum(i.area_m2 for i in part.interfaces),
                             b5.chamber_interface_area_m2()), 1e-12)
        # intended orientation: the wall normal points lower -> upper and is
        # the analytic plane normal — oblique, not axis-aligned
        n = b5.chamber_plane_normal()
        for iface in part.interfaces:
            self.assertEqual((iface.region_a_id, iface.region_b_id),
                             ("region_chamber_lower", "region_chamber_upper"))
            dot = float(np.dot(np.array(iface.normal_a_to_b), n))
            self.assertGreater(dot, 0.9999)
            self.assertLess(abs(iface.normal_a_to_b[2]), 0.999,
                            "separator must be oblique, not horizontal")
        # each region closes on its own with the intended orientation
        lower = b5.compile_chamber_region(b5.CH_REGION_LOWER, b5.MAT_CORK, "lower")
        upper = b5.compile_chamber_region(b5.CH_REGION_UPPER, b5.MAT_ALLOY, "upper")
        for solo in (lower, upper):
            self.assertTrue(solo.complete)
            self.assertGreater(solo.mass_properties.volume_m3, 0.0)
            chi, genus = b5.boundary_genus(solo.boundary_faces)
            self.assertEqual((chi, genus), (2, 0))
        self.assertLess(_rel(lower.mass_properties.volume_m3
                             + upper.mass_properties.volume_m3,
                             part.geometric_volume_m3), 1e-12)

    # ── inventory contract ─────────────────────────────────────────────────
    def test_inventory_json(self):
        import json
        inv = b5.b5_inventory()
        json.dumps(inv)  # must serialize
        self.assertEqual(inv["shapes"]["ring_frame"]["boundary_genus"], 1)
        self.assertEqual(inv["shapes"]["concave_l"]["boundary_genus"], 0)
        self.assertEqual(inv["shapes"]["triple_junction"]["interface_count"], 6)
        self.assertEqual(inv["shapes"]["chamber_oblique"]["interface_count"], 2)
        self.assertEqual(inv["refusal_controls"],
                         {"pinched_ring": "non_manifold_boundary",
                          "open_ring_shell": "degenerate_tetrahedron",
                          "inverted_ring": "inverted_tetrahedron"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
