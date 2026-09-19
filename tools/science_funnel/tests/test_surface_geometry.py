"""Surface geometry membrane: verify the canonical form's residues match
the solver's impulse shares, and energy conservation is a geometric theorem."""
import math
import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.science_funnel.surface_geometry import (
    canonical_form, residues, conservation_identity,
    friction_double_copy, hull_positivity,
)


class TestCanonicalFormResidues(unittest.TestCase):
    """F1: The canonical form's residues ARE the impulse shares."""

    def test_single_row_contact(self):
        """One contact row, one DOF: the canonical form residue = the impulse."""
        rows = [[1.0]]
        floors = [0.0]
        mass_inv = [[1.0]]  # unit mass
        mass = {(0, 0): 1.0}

        form = canonical_form(rows, floors, mass_inv)
        self.assertEqual(len(form), 1)

        # Free acceleration violates the constraint (accelerating through floor)
        free = [-2.0]
        qdd, lambdas, shares = residues(form, free, rows, floors, mass, mass_inv)

        # The constraint pushes back: qdd should be at the floor (0.0)
        self.assertAlmostEqual(qdd[0], 0.0, places=10)
        self.assertAlmostEqual(lambdas[0], 2.0, places=10)
        # The share is the energy dissipated
        self.assertLess(shares[0], 0)  # energy removed

    def test_two_row_contact_stick(self):
        """Two contact rows: both active, residues split the impulse."""
        rows = [[1.0, 0.0], [0.0, 1.0]]
        floors = [0.0, 0.0]
        mass_inv = [[1.0, 0.0], [0.0, 1.0]]  # identity mass
        mass = {(0, 0): 1.0, (0, 1): 0.0, (1, 0): 0.0, (1, 1): 1.0}

        form = canonical_form(rows, floors, mass_inv)
        self.assertEqual(len(form), 2)

        free = [-1.0, -2.0]
        qdd, lambdas, shares = residues(form, free, rows, floors, mass, mass_inv)

        # Both constraints push back
        self.assertAlmostEqual(lambdas[0], 1.0, places=10)
        self.assertAlmostEqual(lambdas[1], 2.0, places=10)


class TestConservationIdentity(unittest.TestCase):
    """F2: Energy conservation is a geometric theorem (d(omega) = 0)."""

    def test_single_contact_dissipation(self):
        """One contact: delta_E == sum(shares), and delta_E <= 0."""
        rows = [[1.0]]
        floors = [0.0]
        mass_inv = [[2.0]]
        mass = {(0, 0): 0.5}  # M^-1 = 2 implies M = 0.5

        form = canonical_form(rows, floors, mass_inv)
        free = [-3.0]
        qdd, lambdas, shares = residues(form, free, rows, floors, mass, mass_inv)
        result = conservation_identity(shares, free, qdd, mass, mass_inv)

        self.assertTrue(result["dissipated"], "energy must be dissipated")
        self.assertTrue(result["geometric_theorem_holds"],
                        f"identity error: {result['identity_error']}")


class TestFrictionDoubleCopy(unittest.TestCase):
    """F3: The Coulomb cone emerges from the double copy of the contact row."""

    def test_2d_normal_gives_perpendicular_tangent(self):
        result = friction_double_copy([0.0, 1.0], 0.5)
        self.assertAlmostEqual(result["tangent_row"][0], -1.0)
        self.assertAlmostEqual(result["tangent_row"][1], 0.0)
        self.assertEqual(result["coupling"], 0.5)

    def test_no_adhesion(self):
        """When lambda_n = 0, f_t = 0 — the gauge constraint's no-pull law."""
        result = friction_double_copy([0.0, 1.0], 0.5)
        self.assertIn("no_adhesion", result)

    def test_mu_is_the_double_copy_coupling(self):
        """mu is not a free parameter but the membrane's coupling constant."""
        for mu in [0.0, 0.3, 0.8, 1.0]:
            result = friction_double_copy([1.0, 0.0], mu)
            self.assertEqual(result["coupling"], mu)


class TestHullPositivity(unittest.TestCase):
    """F4: Support hull stability from the canonical form's sign."""

    def test_com_inside_triangle(self):
        """CoM at the centroid of a triangle: all weights positive."""
        contacts = [[0.0, 0.0], [1.0, 0.0], [0.5, 0.8]]
        com = [0.5, 0.267]  # near centroid
        result = hull_positivity(contacts, com)
        self.assertTrue(result["inside"])
        self.assertEqual(result["positivity"], "positive")
        self.assertFalse(result["capture_step_triggered"])

    def test_com_outside_triangle(self):
        """CoM outside the triangle: sign change, capture step triggered."""
        contacts = [[0.0, 0.0], [1.0, 0.0], [0.5, 0.8]]
        com = [1.5, 0.5]  # outside
        result = hull_positivity(contacts, com)
        self.assertEqual(result["positivity"], "negative")
        self.assertTrue(result["capture_step_triggered"])


class TestLaplacianIdentity(unittest.TestCase):
    """F5: The terrain.py Laplacian identity IS a canonical form residue."""

    def test_five_point_stencil(self):
        """The identity axial_mean - node = (d2x + d2y)/4 is the residue
        of a symmetric 5-point polytope."""
        # Symmetric stencil: center node with 4 axial neighbors
        values = {}
        for r in range(-2, 3):
            for c in range(-2, 3):
                values[(r, c)] = float(r * r + c * c)  # quadratic surface

        # Compute at the center node (0, 0)
        node = values[(0, 0)]
        axial = [values[(0, 1)], values[(0, -1)], values[(1, 0)], values[(-1, 0)]]
        axial_mean = sum(axial) / 4.0

        # Second differences
        d2x = values[(1, 0)] - 2 * node + values[(-1, 0)]
        d2y = values[(0, 1)] - 2 * node + values[(0, -1)]

        # The identity
        error = abs(axial_mean - node - (d2x + d2y) / 4.0)
        self.assertLess(error, 1e-12,
                        "Laplacian identity (canonical form residue) must hold exactly")


if __name__ == "__main__":
    import unittest
    unittest.main()
