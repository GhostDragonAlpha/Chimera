"""B3 battery: the preregistered bars (c3fb2152).
Run: python -m unittest tools.matter_kernel.test_tensile"""
from __future__ import annotations

import unittest

from tools.matter_kernel.constants import lookup
from tools.matter_kernel.tensile import ChainRefused, pull_chain

A = 0.01  # every link 0.01 m^2, as derived in the prereg
CURE = 3.5e7


def link(name, material, kind="member", area=A):
    out = {"name": name, "kind": kind, "material": material, "area_m2": area}
    if kind == "bond":
        out["cure_strength_pa"] = CURE
    return out


FOUR = [link("plate_steel", "mat.steel_mild"),
        link("glue", "mat.wood_glue", kind="bond"),
        link("plate_alu", "mat.aluminum"),
        link("plate_oak", "mat.oak")]
THREE = [l for l in FOUR if l["name"] != "glue"]

CAP = {"plate_steel": lookup("mat.steel_mild")["yield"] * A,
       "glue": CURE * A,
       "plate_alu": lookup("mat.aluminum")["yield"] * A,
       "plate_oak": lookup("mat.oak")["yield"] * A}


class TensileBars(unittest.TestCase):
    def test_p1_holds_below_weakest(self):
        """P1: 3.0e5 N holds with safety factor 7/6."""
        out = pull_chain(FOUR, 3.0e5)
        self.assertTrue(out["holds"])
        self.assertIsNone(out["site"])
        self.assertAlmostEqual(out["safety_factor"], 7.0 / 6.0, places=9)

    def bar2_weakest_glue_fails(self):
        """P2: past the minimum, the GLUE fails at exactly its
        capacity; the second-weakest oak and both metals survive."""
        out = pull_chain(FOUR, 4.0e5)
        self.assertFalse(out["holds"])
        self.assertEqual(out["site"], "glue")
        self.assertAlmostEqual(out["failure_force_n"], CAP["glue"], places=3)
        self.assertLess(out["failure_force_n"], CAP["plate_oak"],
                        "failure must land below the second-weakest link")
        return out

    def test_p2_weakest_glue_fails(self):
        self.bar2_weakest_glue_fails()

    def test_p3_failure_follows_the_minimum(self):
        """P3: without the glue the minimum moves to the oak — pull
        5.0e5 N fails at the OAK at 4.5e5 N, aluminum and steel
        survive. A positional rule would still name the second link."""
        out = pull_chain(THREE, 5.0e5)
        self.assertFalse(out["holds"])
        self.assertEqual(out["site"], "plate_oak")
        self.assertAlmostEqual(out["failure_force_n"], CAP["plate_oak"],
                               places=3)
        self.assertLess(out["failure_force_n"], CAP["plate_alu"])
        self.assertLess(out["failure_force_n"], CAP["plate_steel"])

    def test_p4_survivors_stay_below_their_strength(self):
        """P4: at failure every surviving link carries the failure
        force at a stress strictly below its own strength."""
        out = self.bar2_weakest_glue_fails()
        f = out["failure_force_n"]
        for name in ("plate_steel", "plate_alu", "plate_oak"):
            rec = out["links"][name]
            self.assertGreater(rec["capacity_n"], f)
            self.assertLess(f / rec["area_m2"], rec["strength_pa"])

    def test_p5_linear_in_weakest_area(self):
        """P5: halve the glue overlap -> F_fail exactly halves."""
        half = [FOUR[0], dict(FOUR[1], area_m2=A / 2)] + FOUR[2:]
        out = pull_chain(half, 4.0e5)
        self.assertEqual(out["site"], "glue")
        self.assertAlmostEqual(out["failure_force_n"], CAP["glue"] / 2,
                               places=3)
        self.assertAlmostEqual(out["failure_force_n"], 1.75e5, places=3)

    def test_p6_named_refusals(self):
        """P6: omitted/invalid force, empty chain, bad area, bond
        without cure — all refused by name, never defaulted."""
        with self.assertRaisesRegex(ChainRefused, "force_required"):
            pull_chain(FOUR, None)
        with self.assertRaisesRegex(ChainRefused, "invalid_force"):
            pull_chain(FOUR, 0.0)
        with self.assertRaisesRegex(ChainRefused, "invalid_force"):
            pull_chain(FOUR, -1.0)
        with self.assertRaisesRegex(ChainRefused, "empty_chain"):
            pull_chain([], 1.0e5)
        with self.assertRaisesRegex(ChainRefused, "invalid_area"):
            pull_chain([link("zero", "mat.oak", area=0.0)], 1.0e5)
        with self.assertRaisesRegex(ChainRefused, "invalid_cure"):
            pull_chain([{"name": "b", "kind": "bond",
                         "material": "mat.wood_glue", "area_m2": A}],
                       1.0e5)

    def test_p7_exact_boundary(self):
        """P7: exactly at F_fail fails; one epsilon below holds."""
        self.assertFalse(pull_chain(FOUR, CAP["glue"])["holds"])
        self.assertTrue(pull_chain(FOUR, CAP["glue"] - 1e-6)["holds"])

    def test_mutation_probe_min_not_max_not_position(self):
        """Wiring check: 'max instead of min' would fail the steel
        (2.5e6 N) while the glue survives; 'first link' would name the
        steel too. P2 pins site and force at the true minimum."""
        out = self.bar2_weakest_glue_fails()
        self.assertNotEqual(out["site"], "plate_steel")
        self.assertGreater(CAP["plate_steel"] / out["failure_force_n"], 7.0,
                           "max-mutation must diverge from the true minimum")


if __name__ == "__main__":
    unittest.main()
