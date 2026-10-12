"""B1 gate battery for the construction packet.

Checks required by the §13 B1 evidence column: geometry refusals, positive
volumes, mass/COM/inertia against independent analytic references, correct
interface orientation, no overlapping ownership, and stable material/region/
boundary IDs.  Tolerances are FIXED: a failure means the packet or the
compiler is wrong, never that the tolerance widens.  The Monte-Carlo inertia
reference is seeded and independent of the compiler's tetrahedral integration.

Run:  python tools/construction_packet/test_construction_packet.py  (or pytest)
"""
from __future__ import annotations

import unittest

import numpy as np

import packet
from material_volume import CompileError, CompilerReason


def rel_err(a: float, b: float) -> float:
    return abs(a - b) / max(abs(b), 1e-300)


def wedge_analytic(L: float, W: float, H: float, rho: float):
    """Closed-form mass properties of the right triangular prism
    {x>=0, y>=0, x/L+y/W<=1, 0<=z<=H} about its center of mass."""
    m = rho * L * W * H / 2.0
    com = np.array([L / 3.0, W / 3.0, H / 2.0])
    inertia = m * np.array([
        [W * W / 18.0 + H * H / 12.0, L * W / 36.0, 0.0],
        [L * W / 36.0, L * L / 18.0 + H * H / 12.0, 0.0],
        [0.0, 0.0, (L * L + W * W) / 18.0],
    ])
    return m, com, inertia


def tapered_analytic(L: float, W: float, h0: float, h1: float, alpha: float,
                     rho_core: float, rho_skin: float):
    """Closed-form volume/mass/COM of the trapezoidal prism split at
    z = alpha*h(x) into core (below) and skin (above)."""
    vol = W * L * (h0 + h1) / 2.0
    xbar = L * (h0 + 2.0 * h1) / (3.0 * (h0 + h1))
    zbar = (h0 * h0 + h0 * h1 + h1 * h1) / (3.0 * (h0 + h1))
    m_core = rho_core * alpha * vol
    m_skin = rho_skin * (1.0 - alpha) * vol
    com_core = np.array([xbar, W / 2.0, alpha * zbar])
    com_skin = np.array([xbar, W / 2.0, (1.0 + alpha) * zbar])
    mass = m_core + m_skin
    com = (m_core * com_core + m_skin * com_skin) / mass
    return {"volume": vol, "mass": mass, "com": com,
            "core": (alpha * vol, m_core, com_core),
            "skin": ((1.0 - alpha) * vol, m_skin, com_skin)}


def monte_carlo_inertia(L, W, h0, h1, alpha, rho_core, rho_skin,
                        n=1_000_000, seed=20261012):
    """Seeded uniform-sample reference inertia about the COM; independent of
    the compiler's exact tetrahedral integration."""
    rng = np.random.default_rng(seed)
    x = rng.uniform(0.0, L, n)
    y = rng.uniform(0.0, W, n)
    z = rng.uniform(0.0, max(h0, h1), n)
    h = h0 + (h1 - h0) * x / L
    inside = z <= h
    x, y, z = x[inside], y[inside], z[inside]
    rho = np.where(z <= alpha * h[inside], rho_core, rho_skin)
    box_vol = L * W * max(h0, h1)
    w = rho * box_vol / n
    mass = float(np.sum(w))
    com = np.sum(w[:, None] * np.column_stack([x, y, z]), axis=0) / mass
    d = np.column_stack([x, y, z]) - com
    ix = np.sum(w * np.sum(d * d, axis=1))
    i = np.zeros((3, 3))
    for a in range(3):
        for b in range(3):
            i[a, b] = -np.sum(w * d[:, a] * d[:, b]) if a != b else 0.0
    for a in range(3):
        i[a, a] = ix - np.sum(w * d[:, a] * d[:, a])
    return mass, com, i


class TestWedgeTemplates(unittest.TestCase):
    def _check_wedge(self, spec):
        part = packet.compile_wedge(spec)
        L, W, H = spec["L"], spec["W"], spec["H"]
        rho = spec["material"].density_kg_m3
        self.assertTrue(part.complete)
        self.assertTrue(part.ownership_complete)
        self.assertEqual(part.conflicting_cell_ids, ())
        self.assertEqual(part.unresolved_cell_ids, ())
        self.assertEqual(part.connected_components, 1)
        self.assertGreater(part.geometric_volume_m3, 0.0)
        mp = part.mass_properties
        self.assertIsNotNone(mp)
        m, com, inertia = wedge_analytic(L, W, H, rho)
        self.assertLess(rel_err(mp.volume_m3, L * W * H / 2.0), 1e-12)
        self.assertLess(rel_err(mp.mass_kg, m), 1e-12)
        for k in range(3):
            self.assertLess(abs(mp.center_of_mass_m[k] - com[k]), 1e-12)
        got = np.array(mp.inertia_com_kg_m2)
        self.assertTrue(np.allclose(got, got.T, rtol=0, atol=1e-15))
        scale = np.max(np.abs(inertia))
        self.assertLess(np.max(np.abs(got - inertia)), 1e-9 * scale)
        eig = np.linalg.eigvalsh(got)
        self.assertTrue(np.all(eig > 0.0))
        return part

    def test_wedge_a_matches_closed_form(self):
        self._check_wedge(packet.WEDGE_A)

    def test_wedge_b_matches_closed_form(self):
        self._check_wedge(packet.WEDGE_B)

    def test_templates_are_unequal_and_asymmetric(self):
        a, b = packet.compile_wedge(packet.WEDGE_A), packet.compile_wedge(packet.WEDGE_B)
        self.assertNotAlmostEqual(a.geometric_volume_m3, b.geometric_volume_m3, delta=1e-9)
        self.assertNotAlmostEqual(a.mass_properties.mass_kg, b.mass_properties.mass_kg, delta=1e-9)
        self.assertNotEqual(a.geometry_signature, b.geometry_signature)
        # asymmetric cross-section: legs unequal in each template
        for spec in (packet.WEDGE_A, packet.WEDGE_B):
            self.assertNotEqual(spec["L"], spec["W"])

    def test_region_subtotals_sum_without_double_count(self):
        for part in (packet.compile_wedge(packet.WEDGE_A),
                     packet.compile_wedge(packet.WEDGE_B),
                     packet.compile_tapered_layer()):
            subs = part.resolved_region_subtotals
            self.assertAlmostEqual(sum(s.mass_kg for s in subs.values()),
                                   part.mass_properties.mass_kg, delta=1e-12)
            self.assertAlmostEqual(sum(s.volume_m3 for s in subs.values()),
                                   part.geometric_volume_m3, delta=1e-15)
            self.assertEqual(sum(s.cell_count for s in subs.values()), len(part.cells))
            owners = [c.mass_owner_id for c in part.cells]
            self.assertTrue(all(o is not None for o in owners))
            # one owner per cell, and each owner's cells are exactly one region
            for cell in part.cells:
                self.assertEqual(cell.status, "resolved")
                self.assertIsNotNone(cell.region_id)

    def test_boundary_and_signature_ids_stable(self):
        for compile_ in (lambda: packet.compile_wedge(packet.WEDGE_A),
                         lambda: packet.compile_wedge(packet.WEDGE_B),
                         packet.compile_tapered_layer):
            first, second = compile_(), compile_()
            self.assertEqual(first.geometry_signature, second.geometry_signature)
            keys = lambda p: sorted(f.face_key for f in p.boundary_faces)
            self.assertEqual(keys(first), keys(second))
            ifaces = lambda p: sorted(i.face_key for i in p.interfaces)
            self.assertEqual(ifaces(first), ifaces(second))
            self.assertEqual(first.to_dict(), second.to_dict())

    def test_boundary_face_counts(self):
        for spec in (packet.WEDGE_A, packet.WEDGE_B):
            self.assertEqual(len(packet.compile_wedge(spec).boundary_faces), 8)
        # 12 tets * 4 face instances - 2*(6 core-internal + 6 skin-internal
        # + 2 interface) = 48 - 28 = 20 exterior faces
        self.assertEqual(len(packet.compile_tapered_layer().boundary_faces), 20)


class TestTaperedLayer(unittest.TestCase):
    def setUp(self):
        self.part = packet.compile_tapered_layer()
        t = packet.TAPERED_LAYER
        self.t = t
        self.ref = tapered_analytic(t["L"], t["W"], t["h0"], t["h1"], t["alpha"],
                                    t["core_material"].density_kg_m3,
                                    t["skin_material"].density_kg_m3)

    def test_volume_mass_com_match_closed_form(self):
        mp = self.part.mass_properties
        self.assertIsNotNone(mp)
        self.assertLess(rel_err(self.part.geometric_volume_m3, self.ref["volume"]), 1e-12)
        self.assertLess(rel_err(mp.mass_kg, self.ref["mass"]), 1e-12)
        for k in range(3):
            self.assertLess(abs(mp.center_of_mass_m[k] - self.ref["com"][k]), 1e-12)

    def test_region_subtotals_match_closed_form(self):
        subs = self.part.resolved_region_subtotals
        core_id = self.t["core_region"].region_id
        skin_id = self.t["skin_region"].region_id
        for rid, key in ((core_id, "core"), (skin_id, "skin")):
            vol, mass, com = self.ref[key]
            s = subs[rid]
            self.assertLess(rel_err(s.volume_m3, vol), 1e-12)
            self.assertLess(rel_err(s.mass_kg, mass), 1e-12)
            for k in range(3):
                self.assertLess(abs(s.center_of_mass_m[k] - com[k]), 1e-12)

    def test_inertia_matches_monte_carlo(self):
        t = self.t
        got = np.array(self.part.mass_properties.inertia_com_kg_m2)
        _, _, ref = monte_carlo_inertia(
            t["L"], t["W"], t["h0"], t["h1"], t["alpha"],
            t["core_material"].density_kg_m3, t["skin_material"].density_kg_m3)
        # Monte-Carlo noise floor scales with the tensor magnitude, not with
        # each component: I_xy and I_yz are exactly zero and the sampler can
        # only confirm they sit under the noise floor of the dominant terms.
        scale = np.max(np.abs(ref))
        for a in range(3):
            for b in range(3):
                tol = 0.02 if a == b else 0.03
                self.assertLess(abs(got[a, b] - ref[a, b]), tol * scale,
                                msg=f"inertia[{a},{b}] got {got[a,b]} ref {ref[a,b]}")
        # exact zeros: the extrusion is uniform along y
        self.assertLess(abs(got[0, 1]), 1e-12)
        self.assertLess(abs(got[1, 2]), 1e-12)

    def test_inertia_is_additive_about_origin(self):
        """core + skin shifted to the common origin must equal the total:
        catches double-counted or dropped cells."""
        def to_origin(mp):
            com = np.array(mp.center_of_mass_m)
            return (np.array(mp.inertia_com_kg_m2)
                    + mp.mass_kg * (com @ com * np.eye(3) - np.outer(com, com)))
        subs = self.part.resolved_region_subtotals
        total = to_origin(self.part.mass_properties)
        parts = sum(to_origin(s) for s in subs.values())
        self.assertLess(np.max(np.abs(total - parts)), 1e-9 * np.max(np.abs(total)))

    def test_interface_orientation_and_area(self):
        t = self.t
        core_id = t["core_region"].region_id
        skin_id = t["skin_region"].region_id
        ifaces = self.part.interfaces
        self.assertEqual(len(ifaces), 2)
        com = {rid: np.array(s.center_of_mass_m)
               for rid, s in self.part.resolved_region_subtotals.items()}
        for i in ifaces:
            self.assertEqual({i.region_a_id, i.region_b_id}, {core_id, skin_id})
            n = np.array(i.normal_a_to_b)
            self.assertLess(abs(np.linalg.norm(n) - 1.0), 1e-12)
            # normal points from region_a's material toward region_b's
            self.assertGreater(float(np.dot(n, com[i.region_b_id] - com[i.region_a_id])), 0.0)
            self.assertGreater(i.area_m2, 0.0)
        slope = t["alpha"] * (t["h1"] - t["h0"])
        quad_area = t["W"] * np.hypot(t["L"], slope)
        self.assertLess(abs(sum(i.area_m2 for i in ifaces) - quad_area), 1e-12 * quad_area)

    def test_unresolved_adjacency_empty(self):
        self.assertEqual(self.part.unresolved_adjacencies, ())


class TestRefusalControls(unittest.TestCase):
    def _expect(self, fn, reason):
        ex = fn()
        self.assertIsInstance(ex, CompileError)
        self.assertEqual(ex.reason, reason)

    def test_open_surface_sheet_refused(self):
        self._expect(packet.refusal_open_surface_sheet, CompilerReason.DEGENERATE_TETRAHEDRON)

    def test_thin_sheet_document_refused(self):
        self._expect(packet.refusal_thin_sheet_document, CompilerReason.MIXED_MASS_REPRESENTATIONS)

    def test_inverted_cell_refused(self):
        self._expect(packet.refusal_inverted_cell, CompilerReason.INVERTED_TETRAHEDRON)

    def test_overlapping_cells_refused(self):
        self._expect(packet.refusal_overlapping_cells, CompilerReason.OVERLAPPING_TETRAHEDRA)

    def test_duplicate_mass_owner_refused(self):
        self._expect(packet.refusal_duplicate_mass_owner, CompilerReason.DUPLICATE_MASS_OWNER_ID)

    def test_dual_claim_is_explicit_conflict_not_merge(self):
        part = packet.dual_claim_conflict()
        self.assertFalse(part.complete)
        self.assertEqual(part.conflicting_cell_ids, (0,))
        cell = part.cells[0]
        self.assertEqual(cell.status, CompilerReason.CONFLICT)
        self.assertIsNone(cell.region_id)
        self.assertIsNone(cell.mass_owner_id)
        # the conflicted cell contributes to no region subtotal
        self.assertEqual(sum(s.cell_count for s in part.resolved_region_subtotals.values()), 2)

    def test_unknown_region_refused(self):
        vertices, tets = packet.wedge_geometry(0.1, 0.1, 0.1)
        with self.assertRaises(CompileError) as cm:
            from material_volume import compile_partition
            compile_partition(vertices, tets, [packet.WEDGE_A["material"]],
                              [packet.WEDGE_A["region"]], [["no_such_region"]] * 3)
        self.assertEqual(cm.exception.reason, CompilerReason.UNKNOWN_REGION)


class TestDocumentContract(unittest.TestCase):
    def test_document_compiles_and_matches_direct(self):
        direct = packet.compile_wedge(packet.WEDGE_A)
        via_doc = packet.mv.compile_document(packet.wedge_document(packet.WEDGE_A))
        self.assertEqual(via_doc["geometry_signature"], direct.geometry_signature)
        self.assertTrue(via_doc["complete"])
        self.assertIsNotNone(via_doc["mass_properties"])

    def test_unknown_field_refused(self):
        doc = packet.wedge_document(packet.WEDGE_A)
        doc["surprise"] = 1
        with self.assertRaises(CompileError) as cm:
            packet.mv.compile_document(doc)
        self.assertEqual(cm.exception.reason, CompilerReason.BAD_SCHEMA)

    def test_missing_field_refused(self):
        doc = packet.wedge_document(packet.WEDGE_A)
        del doc["materials"]
        with self.assertRaises(CompileError) as cm:
            packet.mv.compile_document(doc)
        self.assertEqual(cm.exception.reason, CompilerReason.BAD_SCHEMA)


class TestResourceInventory(unittest.TestCase):
    def test_inventory_shape_and_completeness(self):
        inv = packet.resource_inventory()
        self.assertEqual(set(inv["templates"]),
                         {"template_wedge_a", "template_wedge_b", "template_tapered_layer"})
        for tmpl in inv["templates"].values():
            self.assertTrue(tmpl["complete"])
            self.assertTrue(tmpl["ownership_complete"])
            self.assertGreater(tmpl["mass_properties"]["mass_kg"], 0.0)
            self.assertGreater(tmpl["geometric_volume_m3"], 0.0)
        self.assertEqual(inv["refusal_controls"]["open_surface_sheet"],
                         CompilerReason.DEGENERATE_TETRAHEDRON)
        self.assertEqual(inv["refusal_controls"]["thin_sheet_document"],
                         CompilerReason.MIXED_MASS_REPRESENTATIONS)
        self.assertEqual(inv["templates"]["template_tapered_layer"]["interface_count"], 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
