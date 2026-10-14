"""Curve-integral contact solver tests.

The falsifier: the curve-integral solution (boundary residues of the
canonical form) must match the classical KKT solution to machine precision.
Any difference proves the geometric derivation wrong.

The building-block tests verify the on-shell decomposition: single contacts
are "triangles" and friction pairs are "bubbles" with the double-copy cap.
"""
import math
import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tools.science_funnel.curve_integral import curve_integral_solve, verify_against_kkt


class TestCurveIntegralEquivalence(unittest.TestCase):
    """F1: The curve integral gives the SAME answer as KKT — the residue theorem."""

    def test_single_contact_no_violation(self):
        """Free acceleration already satisfies the constraint: no correction."""
        rows = [[1.0]]
        floors = [0.0]
        free = [1.0]  # moving away from the floor
        minv = [[1.0]]
        result = curve_integral_solve(rows, floors, free, minv)
        self.assertEqual(result["constrained_accel"], [1.0])
        self.assertEqual(result["lambdas"], [0.0])
        self.assertEqual(result["method"], "curve_integral (no active boundary)")

    def test_single_contact_violation(self):
        """Free acceleration violates: the boundary residue corrects it."""
        rows = [[1.0]]
        floors = [0.0]
        free = [-2.0]
        minv = [[1.0]]
        result = curve_integral_solve(rows, floors, free, minv)
        self.assertAlmostEqual(result["constrained_accel"][0], 0.0, places=12)
        self.assertAlmostEqual(result["lambdas"][0], 2.0, places=12)

    def test_single_contact_vs_kkt(self):
        """Falsifier: curve integral == KKT for 1 row."""
        rows = [[1.0]]
        floors = [-0.5]
        free = [-3.0]
        minv = [[2.0]]
        v = verify_against_kkt(rows, floors, free, minv)
        self.assertTrue(v["equivalent"], f"max diff: {v['max_difference']}")

    def test_two_independent_contacts_vs_kkt(self):
        """Falsifier: curve integral == KKT for 2 independent rows."""
        rows = [[1.0, 0.0], [0.0, 1.0]]
        floors = [0.0, 0.0]
        free = [-1.5, -2.5]
        minv = [[1.0, 0.0], [0.0, 1.0]]
        v = verify_against_kkt(rows, floors, free, minv)
        self.assertTrue(v["equivalent"], f"max diff: {v['max_difference']}")

    def test_coupled_mass_vs_kkt(self):
        """Falsifier: curve integral == KKT with cross-coupled mass matrix."""
        rows = [[1.0, 0.0], [0.5, 1.0]]
        floors = [0.0, -0.1]
        free = [-2.0, -1.0]
        minv = [[2.0, 0.5], [0.5, 1.5]]
        v = verify_against_kkt(rows, floors, free, minv)
        self.assertTrue(v["equivalent"], f"max diff: {v['max_difference']}")

    def test_one_active_one_inactive(self):
        """Only one constraint violated: the other stays free."""
        rows = [[1.0, 0.0], [0.0, 1.0]]
        floors = [0.0, 0.0]
        free = [-1.0, 2.0]  # row 0 violated, row 1 satisfied
        minv = [[1.0, 0.0], [0.0, 1.0]]
        result = curve_integral_solve(rows, floors, free, minv)
        self.assertAlmostEqual(result["constrained_accel"][0], 0.0, places=12)
        self.assertAlmostEqual(result["constrained_accel"][1], 2.0, places=12)
        self.assertEqual(result["active_rows"], [0])


class TestBuildingBlocks(unittest.TestCase):
    """F2: The on-shell decomposition produces triangles and bubbles."""

    def test_single_row_is_triangle(self):
        """One contact row = the on-shell triangle building block."""
        rows = [[1.0]]
        floors = [0.0]
        free = [-1.0]
        minv = [[1.0]]
        result = curve_integral_solve(rows, floors, free, minv)
        self.assertEqual(len(result["building_blocks"]), 1)
        self.assertEqual(result["building_blocks"][0]["type"], "triangle")

    def test_friction_pair_is_bubble(self):
        """Normal + tangential rows with mu > 0 = the bubble building block."""
        rows = [[1.0, 0.0], [0.0, 1.0]]
        floors = [0.0, 0.0]
        free = [-2.0, -3.0]
        minv = [[1.0, 0.0], [0.0, 1.0]]
        result = curve_integral_solve(rows, floors, free, minv, mu=0.5)
        bubbles = [b for b in result["building_blocks"] if b["type"] == "bubble"]
        self.assertTrue(len(bubbles) >= 1, "should have at least one bubble")

    def test_fricionless_has_no_bubbles(self):
        """mu = 0: all building blocks are triangles (no double-copy pairs)."""
        rows = [[1.0, 0.0], [0.0, 1.0]]
        floors = [0.0, 0.0]
        free = [-2.0, -3.0]
        minv = [[1.0, 0.0], [0.0, 1.0]]
        result = curve_integral_solve(rows, floors, free, minv, mu=0.0)
        types = {b["type"] for b in result["building_blocks"]}
        self.assertNotIn("bubble", types)

    def test_bubble_cap(self):
        """The tangential residue is capped at mu * the normal residue."""
        rows = [[1.0, 0.0], [0.0, 1.0]]
        floors = [0.0, 0.0]
        free = [-1.0, -10.0]  # strong tangential demand
        minv = [[1.0, 0.0], [0.0, 1.0]]
        result = curve_integral_solve(rows, floors, free, minv, mu=0.3)
        # lambda[0] should be 1.0 (the normal constraint)
        self.assertAlmostEqual(result["lambdas"][0], 1.0, places=10)
        # lambda[1] should be capped at 0.3 * 1.0 = 0.3
        self.assertLessEqual(result["lambdas"][1], 0.3 + 1e-10)


class TestResidueTheorem(unittest.TestCase):
    """F3: The residue theorem: sum of boundary residues = the KKT solution."""

    def test_many_random_configurations(self):
        """The theorem holds for many random contact configurations."""
        import random
        rng = random.Random(42)
        for trial in range(20):
            n = 2
            N = rng.randint(1, 3)
            rows = [[rng.uniform(-1, 1) for _ in range(n)] for _ in range(N)]
            floors = [rng.uniform(-1, 0) for _ in range(N)]
            free = [rng.uniform(-3, 3) for _ in range(n)]
            # SPD inverse mass
            a, b = rng.uniform(0.5, 2.0), rng.uniform(-0.3, 0.3)
            minv = [[a, b], [b, a]]
            v = verify_against_kkt(rows, floors, free, minv, tolerance=1e-10)
            self.assertTrue(v["equivalent"],
                f"trial {trial}: max diff {v['max_difference']}")


if __name__ == "__main__":
    unittest.main()
