"""B4 battery: the preregistered bars (06be7c05).
Run: python -m unittest tools.matter_kernel.test_drape"""
from __future__ import annotations

import math
import unittest

from tools.matter_kernel.drape import DrapeRefused, drape_rail

R = 0.05        # 5 cm rail radius (preregistered geometry)
SIGMA = 0.2     # kg/m^2, woven cotton sheeting typical (prereg, cited)
G = 9.80665     # standard gravity, SI defined value
CIRC = math.pi * R


def drape(width):
    return drape_rail(width, R, SIGMA, G)


class DrapeBars(unittest.TestCase):
    def test_p1_no_drape_below_threshold(self):
        """P1: 0.9 x pi x R slides off — named refusal, no drape."""
        with self.assertRaisesRegex(DrapeRefused, "cannot_drape"):
            drape(0.9 * CIRC)

    def test_p2_exact_threshold(self):
        """P2: exactly pi x R drapes with zero excess and zero
        lift-off tension."""
        out = drape(CIRC)
        self.assertTrue(out["drapes"])
        self.assertAlmostEqual(out["contact_arc_m"], CIRC, places=12)
        self.assertEqual(out["excess_m"], 0.0)
        self.assertEqual(out["liftoff_tension_each_n_per_m"], 0.0)
        self.assertEqual(out["min_tension_n_per_m"], 0.0)

    def bar3_full_drape(self):
        """P3: pi x R + 0.02 drapes: exact contact arc, exact excess,
        lift-off at pi/2, all tensions >= 0."""
        out = drape(CIRC + 0.02)
        self.assertTrue(out["drapes"])
        self.assertAlmostEqual(out["contact_arc_m"], CIRC, places=12)
        self.assertEqual(out["liftoff_angle_rad"], math.pi / 2)
        self.assertAlmostEqual(out["excess_m"], 0.02, places=15)
        self.assertGreaterEqual(out["min_tension_n_per_m"], 0.0)
        return out

    def test_p3_full_drape(self):
        self.bar3_full_drape()

    def test_p4_conservation_exact(self):
        """P4: contact + excess = W_c at exact float equality — no
        stretch, no loss."""
        out = self.bar3_full_drape()
        self.assertEqual(out["contact_arc_m"] + out["excess_m"],
                         CIRC + 0.02)

    def test_p5_load_path_sums_to_weight(self):
        """P5: arc weight + lift pulls = sigma g W_c exactly; each
        component matches its derived value."""
        out = self.bar3_full_drape()
        lp = out["load_path"]
        w_total = SIGMA * G * (CIRC + 0.02)
        self.assertAlmostEqual(lp["total_n_per_m"], w_total, places=12)
        self.assertAlmostEqual(lp["cloth_weight_n_per_m"], w_total, places=12)
        self.assertAlmostEqual(lp["arc_weight_n_per_m"], SIGMA * G * CIRC,
                               places=12)
        self.assertAlmostEqual(lp["liftoff_pulls_n_per_m"], SIGMA * G * 0.02,
                               places=12)

    def test_p6_tension_linear_in_excess(self):
        """P6: doubling the excess exactly doubles T_e."""
        t1 = drape(CIRC + 0.01)["liftoff_tension_each_n_per_m"]
        t2 = drape(CIRC + 0.02)["liftoff_tension_each_n_per_m"]
        self.assertAlmostEqual(t2, 2 * t1, places=12)
        self.assertAlmostEqual(t1, SIGMA * G * 0.01 / 2, places=12)

    def test_p7_named_refusals(self):
        """P7: missing gravity and invalid inputs — refused by name,
        never defaulted."""
        with self.assertRaisesRegex(DrapeRefused, "gravity_required"):
            drape_rail(CIRC + 0.02, R, SIGMA, None)
        with self.assertRaisesRegex(DrapeRefused, "invalid_width"):
            drape_rail(0.0, R, SIGMA, G)
        with self.assertRaisesRegex(DrapeRefused, "invalid_radius"):
            drape_rail(CIRC, 0.0, SIGMA, G)
        with self.assertRaisesRegex(DrapeRefused, "invalid_density"):
            drape_rail(CIRC, R, -1.0, G)

    def test_mutation_probe_slide_and_stretch(self):
        """Wiring check: a 'slide mutant' (drapes below threshold by
        holding with negative tension) hits P1's refusal; a 'stretch
        mutant' (consumes excess by stretching the arc) breaks P4's
        exact equality. Both mutations are pinned here."""
        with self.assertRaisesRegex(DrapeRefused, "cannot_drape"):
            drape(CIRC - 1e-9)
        out = self.bar3_full_drape()
        self.assertGreaterEqual(out["min_tension_n_per_m"], 0.0)
        self.assertEqual(out["contact_arc_m"] + out["excess_m"],
                         CIRC + 0.02)


if __name__ == "__main__":
    unittest.main()
