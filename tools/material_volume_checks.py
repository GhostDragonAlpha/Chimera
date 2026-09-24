"""Independent falsifier suite for material_volume.py (NumPy + stdlib only).

STATEMENT: the v1 compiler exactly partitions its declared conforming tet
complex, computes piecewise-uniform-density rigid-body properties, and refuses
ambiguous ownership and invalid/non-manifold/overlapping geometry.
PREDICTION: analytic simplex and bipyramid integrals match; refinement and
uniform scaling preserve the stated mass-property laws.
FALSIFIERS: wrong analytic mass/COM/inertia; unresolved cells given a total;
shared faces emitted more than once or with the wrong normal; material-region
closed-surface vectors/volumes fail to close; scaling/refinement/stiffness
controls change mass properties; overlap, inversion, degeneracy, open boundary,
non-manifold face/link, duplicate ownership, or a mixed mass ledger is accepted.

Run: python tools/material_volume_checks.py
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import material_volume as mv


TET = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
SIMPLEX = np.array([[0, 1, 2, 3]], dtype=np.int64)


def material(mid="tissue", density=12.0):
    return mv.MaterialSpec(mid, density, "analytic fixture", "uniform fixture density")


def region(rid="whole", owner="owner-whole", mid="tissue", stiffness=123.0):
    return mv.RegionSpec(rid, owner, mid, stiffness)


def compile_one(vertices=TET, tets=SIMPLEX, proposals=None, regions=None, materials=None):
    if proposals is None:
        proposals = [["whole"] for _ in range(len(tets))]
    if regions is None:
        regions = [region()]
    if materials is None:
        materials = [material()]
    return mv.compile_partition(vertices, tets, materials, regions, proposals)


def bipyramid():
    """Two positively oriented tets sharing the triangle z=0."""
    vertices = np.array([[0., 0., 0.], [1., 0., 0.], [0., 1., 0.],
                         [0., 0., 1.], [0., 0., -1.]])
    tets = np.array([[0, 1, 2, 3], [0, 2, 1, 4]], dtype=np.int64)
    return vertices, tets


def oracle_simplex_moments(vertices, tets, densities):
    """Analytic barycentric second-moment integral, independent of compiler.

    For uniform density on a 3-simplex, E[lambda_i lambda_j] is 2/20 on
    diagonal and 1/20 off diagonal. This computes raw moments about the world
    origin, then shifts to COM; it does not use the implementation's centered
    vertex covariance or per-cell parallel-axis assembly.
    """
    p = np.asarray(vertices, dtype=np.float64)
    first = np.zeros(3)
    raw_second = np.zeros((3, 3))
    mass_total = 0.0
    volume_total = 0.0
    for tet, rho in zip(np.asarray(tets), np.asarray(densities)):
        x = p[tet]
        volume = float(np.linalg.det((x[1:] - x[0]).T) / 6.0)
        assert volume > 0
        mass = volume * float(rho)
        s = x.sum(axis=0)
        raw = (x.T @ x + np.outer(s, s)) * (mass / 20.0)
        first += mass * s / 4.0
        raw_second += raw
        mass_total += mass
        volume_total += volume
    com = first / mass_total
    central = raw_second - mass_total * np.outer(com, com)
    inertia = np.trace(central) * np.eye(3) - central
    return volume_total, mass_total, com, inertia


def face_area_vector(vertices, oriented_face):
    tri = np.asarray(vertices)[np.asarray(oriented_face)]
    return 0.5 * np.cross(tri[1] - tri[0], tri[2] - tri[0])


def signed_triangle_volume(vertices, oriented_face):
    tri = np.asarray(vertices)[np.asarray(oriented_face)]
    return float(np.dot(tri[0], np.cross(tri[1], tri[2])) / 6.0)


def assert_raises_reason(test, reason, fn):
    try:
        fn()
    except mv.CompileError as exc:
        test.assertEqual(exc.reason, reason, str(exc))
    else:
        test.fail(f"expected named refusal {reason!r}")


def _split_simplex_four_ways():
    p = np.vstack([TET, TET.mean(axis=0)])
    # Local face winding is outward for the positively oriented parent tet.
    parent_outward_faces = ((1, 2, 3), (0, 3, 2), (0, 1, 3), (0, 2, 1))
    t = np.array([[4, *face] for face in parent_outward_faces], dtype=np.int64)
    return p, t


import unittest


class MaterialVolumeChecks(unittest.TestCase):
    def test_unit_simplex_matches_independent_analytic_mass_com_and_inertia(self):
        out = compile_one()
        expected = oracle_simplex_moments(TET, SIMPLEX, [12.0])
        props = out.mass_properties
        self.assertIsNotNone(props)
        self.assertAlmostEqual(props.volume_m3, 1.0 / 6.0, places=15)
        self.assertAlmostEqual(props.mass_kg, 2.0, places=15)
        np.testing.assert_allclose(props.center_of_mass_m, [0.25] * 3,
                                   rtol=0.0, atol=2e-16)
        # Closed-form unit right-tet tensor for rho=12: diagonal .15,
        # positive off-diagonal .025 kg*m^2.
        expected_tensor = np.full((3, 3), 0.025)
        np.fill_diagonal(expected_tensor, 0.15)
        np.testing.assert_allclose(props.inertia_com_kg_m2, expected_tensor,
                                   rtol=0.0, atol=3e-16)
        self.assertAlmostEqual(props.volume_m3, expected[0], places=15)
        self.assertAlmostEqual(props.mass_kg, expected[1], places=15)
        np.testing.assert_allclose(props.center_of_mass_m, expected[2], rtol=0.0, atol=2e-16)
        np.testing.assert_allclose(props.inertia_com_kg_m2, expected[3], rtol=0.0, atol=3e-16)

    def test_two_material_bipyramid_has_one_oriented_shared_interface(self):
        p, t = bipyramid()
        mats = [material("upper", 2.0), material("lower", 4.0)]
        regs = [region("A-upper", "owner-upper", "upper"),
                region("B-lower", "owner-lower", "lower")]
        out = mv.compile_partition(p, t, mats, regs, [["A-upper"], ["B-lower"]])
        self.assertTrue(out.complete)
        self.assertAlmostEqual(out.geometric_volume_m3, 1.0 / 3.0, places=15)
        self.assertEqual(len(out.interfaces), 1)
        face = out.interfaces[0]
        self.assertEqual(face.face_key, (0, 1, 2))
        self.assertEqual((face.region_a_id, face.region_b_id), ("A-upper", "B-lower"))
        self.assertEqual((face.mass_owner_a_id, face.mass_owner_b_id),
                         ("owner-upper", "owner-lower"))
        self.assertAlmostEqual(face.area_m2, 0.5, places=15)
        np.testing.assert_allclose(face.normal_a_to_b, [0, 0, -1], rtol=0.0, atol=1e-15)
        self.assertEqual(len({f.face_key for f in out.interfaces}), len(out.interfaces))
        expected = oracle_simplex_moments(p, t, [2.0, 4.0])
        got = out.mass_properties
        self.assertAlmostEqual(got.mass_kg, expected[1], places=15)
        np.testing.assert_allclose(got.center_of_mass_m, expected[2], rtol=0.0, atol=3e-16)
        np.testing.assert_allclose(got.inertia_com_kg_m2, expected[3], rtol=0.0, atol=5e-16)
        self.assertAlmostEqual(got.center_of_mass_m[2], -1.0 / 12.0, places=15)

    def test_shared_interface_cancels_and_each_material_surface_closes(self):
        # Translate away from the origin so the shared triangle contributes a
        # nonzero signed tetrahedral volume term; each side must contribute
        # equal and opposite interface terms exactly once.
        p, t = bipyramid()
        p += np.array([1.3, -2.1, 3.7])
        regs = [region("A-upper", "owner-upper", "upper"),
                region("B-lower", "owner-lower", "lower")]
        out = mv.compile_partition(p, t,
            [material("upper", 2), material("lower", 4)], regs,
            [["A-upper"], ["B-lower"]])
        by_region_area = {r: np.zeros(3) for r in ("A-upper", "B-lower")}
        by_region_volume = {r: 0.0 for r in by_region_area}
        for boundary in out.boundary_faces:
            row = out.cells[boundary.cell_id]
            by_region_area[row.region_id] += face_area_vector(p, boundary.vertices)
            by_region_volume[row.region_id] += signed_triangle_volume(p, boundary.vertices)
        interface = out.interfaces[0]
        a_vector = interface.area_m2 * np.asarray(interface.normal_a_to_b)
        by_region_area[interface.region_a_id] += a_vector
        by_region_area[interface.region_b_id] -= a_vector
        oriented_a = signed_triangle_volume(p, interface.vertices)
        by_region_volume[interface.region_a_id] += oriented_a
        by_region_volume[interface.region_b_id] -= oriented_a
        for rid in by_region_area:
            np.testing.assert_allclose(by_region_area[rid], np.zeros(3),
                                       rtol=0.0, atol=3e-15)
            self.assertAlmostEqual(by_region_volume[rid], 1.0 / 6.0, places=14)
        self.assertAlmostEqual(sum(by_region_volume.values()), out.geometric_volume_m3,
                               places=14)

    def test_all_unresolved_is_json_safe_and_unknown_region_is_refused(self):
        p, t = bipyramid()
        regs = [region("A-upper", "owner-upper", "upper"),
                region("B-lower", "owner-lower", "lower")]
        mats = [material("upper", 2), material("lower", 4)]
        result = mv.compile_partition(p, t, mats, regs, [[], []])
        self.assertFalse(result.complete)
        self.assertIsNone(result.mass_properties)
        self.assertIsNone(result.resolved_only_subtotal)
        self.assertEqual(result.unresolved_cell_ids, (0, 1))
        json.dumps(result.to_dict(), allow_nan=False)
        assert_raises_reason(self, mv.CompilerReason.UNKNOWN_REGION,
            lambda: mv.compile_partition(p, t, mats, regs,
                                         [["not-a-region"], ["B-lower"]]))

    def test_unresolved_and_conflicting_cells_never_get_default_material(self):
        p, t = bipyramid()
        regs = [region("A-upper", "owner-upper", "upper"),
                region("B-lower", "owner-lower", "lower")]
        mats = [material("upper", 2), material("lower", 4)]
        unresolved = mv.compile_partition(p, t, mats, regs,
                                          [["A-upper"], []])
        self.assertFalse(unresolved.complete)
        self.assertEqual(unresolved.unresolved_cell_ids, (1,))
        self.assertIsNone(unresolved.mass_properties)
        self.assertIsNotNone(unresolved.resolved_only_subtotal)
        self.assertEqual(unresolved.resolved_only_subtotal.cell_count, 1)
        self.assertIsNone(unresolved.cells[1].density_kg_m3)
        self.assertEqual(len(unresolved.unresolved_adjacencies), 1)
        self.assertEqual(unresolved.unresolved_adjacencies[0].statuses,
                         ("resolved", "unresolved"))
        conflict = mv.compile_partition(p, t, mats, regs,
                                        [["A-upper", "B-lower"], ["B-lower"]])
        self.assertFalse(conflict.complete)
        self.assertEqual(conflict.conflicting_cell_ids, (0,))
        self.assertIsNone(conflict.mass_properties)
        self.assertEqual(conflict.cells[0].candidate_region_ids,
                         ("A-upper", "B-lower"))
        self.assertEqual(conflict.cells[0].candidate_owner_ids,
                         ("owner-lower", "owner-upper"))
        self.assertIsNone(conflict.cells[0].region_id)
        self.assertIsNone(conflict.cells[0].density_kg_m3)

    def test_stiffness_is_optional_metadata_and_not_a_mass_input(self):
        # None and extreme values are accepted as inert metadata; even NaN
        # cannot contaminate results because stiffness is deliberately unused.
        finite = compile_one(regions=[region(stiffness=None)])
        changed = compile_one(regions=[region(stiffness=float("nan"))])
        self.assertEqual(finite.mass_properties, changed.mass_properties)

    def test_duplicate_mass_owner_is_refused_at_region_boundary(self):
        assert_raises_reason(self, mv.CompilerReason.DUPLICATE_MASS_OWNER_ID,
            lambda: compile_one(regions=[region("one", "same"), region("two", "same")],
                                proposals=[["one"]]))

    def test_stiffness_is_not_read_by_mass_properties(self):
        first = compile_one(regions=[region(stiffness=1.0)])
        second = compile_one(regions=[region(stiffness=9.9e15)])
        self.assertEqual(first.mass_properties, second.mass_properties)

    def test_subdivision_preserves_integrated_mass_properties(self):
        p_refined, t_refined = _split_simplex_four_ways()
        coarse = compile_one()
        refined = compile_one(p_refined, t_refined,
                              [["whole"] for _ in range(4)])
        self.assertEqual(refined.mass_properties.cell_count, 4)
        self.assertAlmostEqual(refined.geometric_volume_m3, coarse.geometric_volume_m3,
                               places=15)
        self.assertAlmostEqual(refined.mass_properties.mass_kg,
                               coarse.mass_properties.mass_kg, places=15)
        np.testing.assert_allclose(refined.mass_properties.center_of_mass_m,
                                   coarse.mass_properties.center_of_mass_m,
                                   rtol=0.0, atol=3e-16)
        np.testing.assert_allclose(refined.mass_properties.inertia_com_kg_m2,
                                   coarse.mass_properties.inertia_com_kg_m2,
                                   rtol=0.0, atol=4e-16)

    def test_uniform_scaling_laws_mass_cubed_inertia_fifth(self):
        scale = 3.75
        base = compile_one().mass_properties
        scaled = compile_one(TET * scale).mass_properties
        self.assertAlmostEqual(scaled.mass_kg / base.mass_kg, scale ** 3,
                               delta=2e-13 * scale ** 3)
        np.testing.assert_allclose(np.asarray(scaled.inertia_com_kg_m2)
                                   / np.asarray(base.inertia_com_kg_m2),
                                   np.full((3, 3), scale ** 5),
                                   rtol=2e-13, atol=2e-12)

    def test_translation_does_not_change_com_relative_tensor_or_mass(self):
        shift = np.array([123.0, -41.0, 9.0])
        base, translated = compile_one(), compile_one(TET + shift)
        self.assertAlmostEqual(base.mass_properties.mass_kg,
                               translated.mass_properties.mass_kg, places=14)
        np.testing.assert_allclose(np.asarray(translated.mass_properties.center_of_mass_m)
                                   - shift, base.mass_properties.center_of_mass_m,
                                   rtol=0.0, atol=2e-14)
        np.testing.assert_allclose(translated.mass_properties.inertia_com_kg_m2,
                                   base.mass_properties.inertia_com_kg_m2,
                                   rtol=0.0, atol=2e-14)

    def test_degenerate_inverted_open_and_nonmanifold_inputs_are_refused(self):
        duplicate_tets = np.vstack([SIMPLEX, SIMPLEX])
        assert_raises_reason(self, mv.CompilerReason.DUPLICATE_TETRAHEDRON,
            lambda: compile_one(tets=duplicate_tets,
                                proposals=[["whole"], ["whole"]]))
        assert_raises_reason(self, mv.CompilerReason.INVERTED_TETRAHEDRON,
                             lambda: compile_one(tets=np.array([[0, 2, 1, 3]])))
        flat = TET.copy()
        flat[3] = [0.25, 0.25, 0.0]
        assert_raises_reason(self, mv.CompilerReason.DEGENERATE_TETRAHEDRON,
                             lambda: compile_one(vertices=flat))
        # Three distinct cells incident to one face are the direct
        # non-manifold-face case (no duplicate-tet shortcut).
        p3 = np.array([[0., 0., 0.], [1., 0., 0.], [0., 1., 0.],
                       [0., 0., 1.], [0., 0., -1.], [0.3, 0.3, 2.]])
        t3 = np.array([[0, 1, 2, 3], [0, 2, 1, 4], [0, 1, 2, 5]])
        assert_raises_reason(self, mv.CompilerReason.NON_MANIFOLD_FACE,
            lambda: compile_one(p3, t3, [["whole"]] * 3))
        # Positive cells on the same side of a shared face have identical
        # outward face winding: this is a topology/orientation refusal before
        # the overlap detector's geometric refusal.
        same_side = np.array([[0., 0., 0.], [1., 0., 0.], [0., 1., 0.],
                              [0., 0., 1.], [0., 0., 2.]])
        same_side_tets = np.array([[0, 1, 2, 3], [0, 1, 2, 4]])
        assert_raises_reason(self, mv.CompilerReason.INCONSISTENT_FACE_ORIENTATION,
            lambda: compile_one(same_side, same_side_tets, [["whole"], ["whole"]]))
        # Two tetrahedra meeting at only an edge make four unpaired boundary
        # triangles around that edge. The geometric sets touch but do not
        # overlap; the invalid simplicial topology must still be refused.
        edge_p = np.array([[0., 0., 0.], [1., 0., 0.], [0., 1., 0.],
                           [0., 0., 1.], [0., 0., -1.], [0., -1., 0.]])
        edge_t = np.array([[0, 1, 2, 3], [0, 1, 5, 4]])
        assert_raises_reason(self, mv.CompilerReason.NON_MANIFOLD_BOUNDARY,
            lambda: compile_one(edge_p, edge_t, [["whole"], ["whole"]]))
        # A face T-junction (one large triangular face opposite three small
        # triangles) is not conforming and must not compile as a closed body.
        tj = np.array([[0., 0., 0.], [1., 0., 0.], [0., 1., 0.],
                       [0., 0., 1.], [0., 0., -1.], [1/3, 1/3, 0.]])
        tj_t = np.array([[0, 1, 2, 3], [0, 5, 1, 4],
                         [1, 5, 2, 4], [2, 5, 0, 4]])
        assert_raises_reason(self, mv.CompilerReason.NON_MANIFOLD_BOUNDARY,
            lambda: compile_one(tj, tj_t, [["whole"]] * 4))
        # Pinched vertex: two valid tet components share one node ID but no
        # edge/face; boundary edges alone look closed, while the vertex link
        # has two disconnected components and is not a 2-manifold.
        pinch = np.vstack([TET, [[4., 0., 0.], [3., 1., 0.], [3., 0., 1.]]])
        pinch_t = np.array([[0, 1, 2, 3], [0, 4, 5, 6]])
        assert_raises_reason(self, mv.CompilerReason.NON_MANIFOLD_VERTEX_LINK,
            lambda: compile_one(pinch, pinch_t, [["whole"], ["whole"]]))

    def test_overlapping_disconnected_cells_are_refused_and_disjoint_are_counted(self):
        second_far = TET + np.array([3.0, 0.0, 0.0])
        p_far = np.vstack([TET, second_far])
        two_tets = np.array([[0, 1, 2, 3], [4, 5, 6, 7]])
        disjoint = compile_one(p_far, two_tets, [["whole"], ["whole"]])
        self.assertEqual(disjoint.connected_components, 2)
        second_overlap = TET + np.array([0.05, 0.05, 0.05])
        p_overlap = np.vstack([TET, second_overlap])
        assert_raises_reason(self, mv.CompilerReason.OVERLAPPING_TETRAHEDRA,
            lambda: compile_one(p_overlap, two_tets, [["whole"], ["whole"]]))

    def test_material_density_changes_properties_and_density_is_validated(self):
        light = compile_one(materials=[material(density=2.0)]).mass_properties
        dense = compile_one(materials=[material(density=6.0)]).mass_properties
        self.assertAlmostEqual(dense.mass_kg / light.mass_kg, 3.0, places=14)
        np.testing.assert_allclose(np.asarray(dense.inertia_com_kg_m2)
                                   / np.asarray(light.inertia_com_kg_m2),
                                   np.full((3, 3), 3.0), rtol=1e-14, atol=1e-14)
        assert_raises_reason(self, mv.CompilerReason.INVALID_DENSITY,
            lambda: compile_one(materials=[material(density=float("nan"))]))
        assert_raises_reason(self, mv.CompilerReason.INVALID_DENSITY,
            lambda: compile_one(materials=[material(density=0.0)]))

    def test_thin_sheet_and_effective_skeletal_mass_cannot_be_added_to_volume(self):
        claims = [mv.MassSourceClaim(mv.MassSourceKind.MATERIAL_VOLUME, "volume-1"),
                  mv.MassSourceClaim(mv.MassSourceKind.EFFECTIVE_SKELETAL_SEGMENT, "segment-1")]
        assert_raises_reason(self, mv.CompilerReason.MIXED_MASS_REPRESENTATIONS,
                             lambda: mv.validate_mass_source_claims(claims))
        claims = [mv.MassSourceClaim(mv.MassSourceKind.MATERIAL_VOLUME, "volume-1"),
                  mv.MassSourceClaim(mv.MassSourceKind.THIN_SHEET, "sheet-1")]
        assert_raises_reason(self, mv.CompilerReason.MIXED_MASS_REPRESENTATIONS,
                             lambda: mv.validate_mass_source_claims(claims))
        assert_raises_reason(self, mv.CompilerReason.INCOMPLETE,
                             lambda: mv.validate_mass_source_claims([]))
        assert_raises_reason(self, mv.CompilerReason.DUPLICATE_MASS_OWNER_ID,
            lambda: mv.validate_mass_source_claims([
                mv.MassSourceClaim(mv.MassSourceKind.MATERIAL_VOLUME, "same"),
                mv.MassSourceClaim(mv.MassSourceKind.MATERIAL_VOLUME, "same")]))

    def test_json_schema_requires_volume_source_and_refuses_ignored_fields(self):
        doc = {
            "schema_version": "chimera.material_volume.v1",
            "coordinate_unit": "m", "density_unit": "kg/m^3",
            "mass_source_kind": mv.MassSourceKind.MATERIAL_VOLUME,
            "vertices_m": TET.tolist(), "tetrahedra": SIMPLEX.tolist(),
            "materials": [dict(material("tissue").__dict__)],
            "regions": [dict(region().__dict__)],
            "cell_proposals": [["whole"]],
        }
        out = mv.compile_document(doc)
        self.assertTrue(out["complete"])
        self.assertEqual(out["mass_source_kind"], mv.MassSourceKind.MATERIAL_VOLUME)
        bad = dict(doc)
        bad["effective_segment_mass_kg"] = 2.0
        assert_raises_reason(self, mv.CompilerReason.BAD_SCHEMA,
                             lambda: mv.compile_document(bad))
        bad = dict(doc)
        bad["mass_source_kind"] = mv.MassSourceKind.EFFECTIVE_SKELETAL_SEGMENT
        assert_raises_reason(self, mv.CompilerReason.MIXED_MASS_REPRESENTATIONS,
                             lambda: mv.compile_document(bad))

    def test_independent_simplex_oracle_covers_heterogeneous_density_fixture(self):
        p, t = bipyramid()
        p += np.array([-0.8, 2.5, 0.33])
        out = mv.compile_partition(p, t,
            [material("upper", 2), material("lower", 4)],
            [region("A-upper", "owner-upper", "upper"),
             region("B-lower", "owner-lower", "lower")],
            [["A-upper"], ["B-lower"]])
        expected = oracle_simplex_moments(p, t, [2.0, 4.0])
        self.assertAlmostEqual(out.mass_properties.volume_m3, expected[0], places=14)
        self.assertAlmostEqual(out.mass_properties.mass_kg, expected[1], places=14)
        np.testing.assert_allclose(out.mass_properties.center_of_mass_m, expected[2],
                                   rtol=0.0, atol=2e-15)
        np.testing.assert_allclose(out.mass_properties.inertia_com_kg_m2, expected[3],
                                   rtol=0.0, atol=3e-15)


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(MaterialVolumeChecks)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
