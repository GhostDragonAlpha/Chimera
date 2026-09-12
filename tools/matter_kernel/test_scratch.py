"""B1 battery: the six preregistered bars (111a82f6).
Run: python -m unittest tools.matter_kernel.test_scratch"""
from __future__ import annotations

import unittest

from tools.matter_kernel.constants import lookup
from tools.matter_kernel.scratch import ScratchRefused, scratch, HV_TO_PA

R = 0.001  # 1 mm round tip (preregostered geometry)


class ScratchBars(unittest.TestCase):
    def bar1_depth_value(self):
        """P1: oak, 10 N -> ~0.0406 mm (derived from cited constants)."""
        out = scratch("mat.steel_hardened", "mat.oak", 10.0, R)
        expect = 10.0 / (2 * 3.141592653589793 * R
                         * lookup("mat.oak")["hardness_vickers"] * HV_TO_PA)
        self.assertAlmostEqual(out["groove_depth_m"], expect, places=12)
        self.assertAlmostEqual(out["groove_depth_m"] * 1000, 0.0406, places=2)
        return out

    def test_p1_depth_value(self):
        self.bar1_depth_value()

    def test_p2_linearity(self):
        """P2: 20 N is exactly 2x the 10 N groove."""
        d10 = scratch("mat.steel_hardened", "mat.oak", 10.0, R)["groove_depth_m"]
        d20 = scratch("mat.steel_hardened", "mat.oak", 20.0, R)["groove_depth_m"]
        self.assertAlmostEqual(d20, 2 * d10, places=12)

    def test_p3_monotonic(self):
        """P3: depth strictly increases across the 1..100 N sweep."""
        depths = [scratch("mat.steel_hardened", "mat.oak", f, R)["groove_depth_m"]
                  for f in range(1, 101)]
        self.assertTrue(all(b > a for a, b in zip(depths, depths[1:])),
                        "depth must strictly increase with force")

    def test_p4_tip_intact(self):
        """P4: steel-on-oak leaves the tip undamaged at every force."""
        for f in (1.0, 10.0, 50.0, 100.0):
            out = scratch("mat.steel_hardened", "mat.oak", f, R)
            self.assertEqual(out["tip_damage_m"], 0.0)
            self.assertEqual(out["yields"], "mat.oak")

    def test_p5_refusals(self):
        """P5: rubber tip refuses; equal-hardness pair refuses, both named."""
        with self.assertRaisesRegex(ScratchRefused, "no_cut_ordering"):
            scratch("mat.rubber", "mat.oak", 10.0, R)
        with self.assertRaisesRegex(ScratchRefused, "no_cut_ordering"):
            scratch("mat.steel_hardened", "mat.steel_hardened", 10.0, R)

    def test_p6_force_required(self):
        """P6: omitted/invalid force is a refusal, never a default."""
        with self.assertRaisesRegex(ScratchRefused, "force_required"):
            scratch("mat.steel_hardened", "mat.oak", None, R)
        with self.assertRaisesRegex(ScratchRefused, "invalid_force"):
            scratch("mat.steel_hardened", "mat.oak", 0.0, R)
        with self.assertRaisesRegex(ScratchRefused, "invalid_force"):
            scratch("mat.steel_hardened", "mat.oak", -5.0, R)

    def test_mutation_probe_pressure_pinning(self):
        """Wiring check: if pinned pressure used the TIP's hardness (the
        wrong member), the depth value must diverge — proving the formula
        reads the plate, not the tip."""
        out = self.bar1_depth_value()
        wrong = out["force_n"] / (2 * 3.141592653589793 * R
                                  * lookup("mat.steel_hardened")["hardness_vickers"]
                                  * HV_TO_PA)
        self.assertGreater(out["groove_depth_m"], wrong * 100,
                           "plate-pinned depth must dwarf tip-pinned depth")


if __name__ == "__main__":
    unittest.main()
