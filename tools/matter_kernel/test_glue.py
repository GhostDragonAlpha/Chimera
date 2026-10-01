"""B2 battery: the preregistered bars (1ef3fff1).
Run: python -m unittest tools.matter_kernel.test_glue"""
from __future__ import annotations

import unittest

from tools.matter_kernel.constants import lookup
from tools.matter_kernel.glue import GlueRefused, pull_bond

STEEL = "mat.steel_mild"
CURE = 3.5e7      # per-bond cure strength, Pa (spec worked example)
A_STEEL = 0.01    # 10 cm x 10 cm plate cross-section, m^2
A_GLUE = 0.01     # matching overlap, m^2
CAP_GLUE = CURE * A_GLUE        # 3.5e5 N, derived in the prereg
CAP_STEEL = lookup(STEEL)["yield"] * A_STEEL  # 2.5e6 N


def pull(force_n, cure=CURE, a_glue=A_GLUE):
    return pull_bond(STEEL, STEEL, a_glue, A_STEEL, A_STEEL, cure, force_n)


class GlueBars(unittest.TestCase):
    def bar2_glue_line_break(self):
        """P2: past cure capacity the joint breaks AT the glue line,
        at exactly cure x area; the steel never reaches its yield."""
        out = pull(4.0e5)
        self.assertFalse(out["holds"])
        self.assertEqual(out["site"], "glue_line")
        self.assertAlmostEqual(out["failure_force_n"], CAP_GLUE, places=3)
        self.assertLess(out["failure_force_n"], CAP_STEEL / 2,
                        "glue-line failure must sit far below steel capacity")
        return out

    def test_p1_holds_below_cure(self):
        """P1: 3.0e5 N holds with safety factor 7/6."""
        out = pull(3.0e5)
        self.assertTrue(out["holds"])
        self.assertIsNone(out["site"])
        self.assertAlmostEqual(out["safety_factor"], 7.0 / 6.0, places=9)

    def test_p2_breaks_at_glue_line(self):
        self.bar2_glue_line_break()

    def test_p2b_cannot_hold_past_double_cure(self):
        """P2 (spec falsifier bar): pulling 2x cure capacity still
        records glue-line failure at the same single capacity value."""
        out = pull(2 * CAP_GLUE)
        self.assertFalse(out["holds"])
        self.assertEqual(out["site"], "glue_line")
        self.assertAlmostEqual(out["failure_force_n"], CAP_GLUE, places=3)

    def test_p3_linear_in_glue_area(self):
        """P3: halve the overlap -> failure force exactly halves."""
        out = pull(4.0e5, a_glue=A_GLUE / 2)
        self.assertEqual(out["site"], "glue_line")
        self.assertAlmostEqual(out["failure_force_n"], CAP_GLUE / 2, places=3)
        self.assertAlmostEqual(out["failure_force_n"], 1.75e5, places=3)

    def test_p4_strong_glue_fails_in_steel(self):
        """P4 control: cure above steel yield -> the STEEL is the weak
        line. The model reads capacities; it never blames the glue."""
        out = pull(3.0e6, cure=3.0e8)
        self.assertFalse(out["holds"])
        self.assertEqual(out["site"], STEEL)
        self.assertAlmostEqual(out["failure_force_n"], CAP_STEEL, places=3)

    def test_p5_named_refusals(self):
        """P5: omitted/invalid force, bad area, bad cure — all refused
        by name, never defaulted."""
        with self.assertRaisesRegex(GlueRefused, "force_required"):
            pull(None)
        with self.assertRaisesRegex(GlueRefused, "invalid_force"):
            pull(0.0)
        with self.assertRaisesRegex(GlueRefused, "invalid_force"):
            pull(-10.0)
        with self.assertRaisesRegex(GlueRefused, "invalid_area"):
            pull_bond(STEEL, STEEL, 0.0, A_STEEL, A_STEEL, CURE, 1.0e5)
        with self.assertRaisesRegex(GlueRefused, "invalid_area"):
            pull_bond(STEEL, STEEL, A_GLUE, -1.0, A_STEEL, CURE, 1.0e5)
        with self.assertRaisesRegex(GlueRefused, "invalid_cure"):
            pull_bond(STEEL, STEEL, A_GLUE, A_STEEL, A_STEEL, None, 1.0e5)

    def test_p6_exact_boundary(self):
        """P6: exactly at capacity fails; one epsilon below holds."""
        out = pull(CAP_GLUE)
        self.assertFalse(out["holds"])
        out = pull(CAP_GLUE - 1e-6)
        self.assertTrue(out["holds"])

    def test_mutation_probe_cure_pinning(self):
        """Wiring check: if the glue-line capacity wrongly used the
        MEMBER's yield instead of cure_strength, the failure force
        would read 2.5e6 N — the bar detects the 7.14x divergence by
        pinning the exact capacity value."""
        out = self.bar2_glue_line_break()
        wrong = lookup(STEEL)["yield"] * A_GLUE
        self.assertGreater(wrong / out["failure_force_n"], 7.0,
                           "member-yield mutation must diverge from cure pin")


if __name__ == "__main__":
    unittest.main()
