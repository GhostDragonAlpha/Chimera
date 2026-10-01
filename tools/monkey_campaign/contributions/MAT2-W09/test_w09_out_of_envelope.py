#!/usr/bin/env python3
"""MAT2-W09 named-check suite (prereg section 8).

Every FB arm carries a clean control AND a bite: the detector must stay
green on the clean run and must FIRE on the tampered input (a falsifier
that cannot fail is refused by the house standard). The heavy fixture (the
whole declared pipeline of run_out_of_envelope.py: pins -> validator ->
ALLOW -> frozen loader -> A0 -> A1 -> A2 -> FB arms) executes ONCE and is
cached; everything else is arithmetic on the emitted receipts.
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import verify_inputs as vi       # noqa: E402
import out_of_envelope as oe     # noqa: E402
import run_out_of_envelope as rle  # noqa: E402

_FIXTURE = {}


def fixture():
    """Run the declared pipeline once; return the parsed receipts."""
    if _FIXTURE:
        return _FIXTURE
    rle.main()
    out = vi.outputs_dir()
    _FIXTURE.update(
        main=json.loads((out / "out_of_envelope_receipt.json")
                        .read_bytes().decode("utf-8")),
        falsifier=json.loads((out / "falsifier_receipt.json")
                             .read_bytes().decode("utf-8")),
        pins=json.loads((out / "input_pins.json").read_bytes().decode("utf-8")))
    return _FIXTURE


def pred(fx, key):
    return fx["main"]["predictions"][key]


class Test01InputPinsAndRegistry(unittest.TestCase):
    def test_pins_green_and_criteria_join(self):
        fx = fixture()
        self.assertEqual(fx["pins"]["pins_ok"], fx["pins"]["pins_total"])
        self.assertEqual(fx["pins"]["pins_total"], 28)
        self.assertEqual(fx["pins"]["criteria_sha256"], vi.CRITERIA_SHA256)
        self.assertEqual(fx["pins"]["registry"]["criteria_sha256"],
                         vi.CRITERIA_SHA256)
        self.assertEqual(fx["pins"]["registry"]["attempt_agent"],
                         vi.AGENT_ID)
        self.assertNotEqual(fx["pins"]["preregistration_sha256"],
                            "ce4caefef319df42901b5a97500a3c3e742a93e76fbb06"
                            "c4f7fcdd10e7ba25aa",
                            "the amended prereg must supersede the "
                            "pre-amendment bytes (amendment a1)")


class Test02GateLoadIdentity(unittest.TestCase):
    def test_validator_allow_and_no_trained_load(self):
        fx = fixture()
        ident = fx["main"]["identity"]
        self.assertEqual(ident["validator"], "VALID")
        self.assertEqual(ident["deploy_decision"], "ALLOW")
        self.assertEqual(ident["trained_bundles_loaded"], 0)
        self.assertEqual(ident["w07_anchor_crosscheck"]["verdict"], "AGREE")


class Test03P1AnchorsExact(unittest.TestCase):
    def test_certified_line_reproduces_bit_for_bit(self):
        fx = fixture()
        anchors = fx["main"]["arms"]["A0_baseline"]["anchors"]
        self.assertEqual(set(anchors), {"final_state_sha256",
                                        "initial_snapshot_sha256",
                                        "trajectory_sha256"})
        for key, row in anchors.items():
            self.assertEqual(row["verdict"], "EXACT", key)


class Test04P2LineObservation(unittest.TestCase):
    def test_a0_observation_only_and_visits_recorded(self):
        fx = fixture()
        p = pred(fx, "P2_line_observation")
        self.assertTrue(p["pass"])
        self.assertEqual(p["ledger_events"], 0)
        self.assertTrue(fx["main"]["arms"]["A0_baseline"]["clean"])
        self.assertIn("unsupported_ticks_on_the_certified_line", p)
        self.assertGreaterEqual(p["unsupported_ticks_on_the_certified_line"],
                                0)


class Test05P3NaturalFallProduced(unittest.TestCase):
    def test_trip_cascade_produces_the_declared_fall(self):
        fx = fixture()
        p = pred(fx, "P3_natural_fall_produced")
        self.assertTrue(p["pass"])
        self.assertIn(p["first_interval"][0], (29, 30, 31))
        self.assertGreaterEqual(p["first_interval_length"], 90)
        self.assertIn(p["fall_declared_tick"], (118, 119, 120))
        self.assertTrue(all(c > 0 for c in p["trips_at_fall"]))


class Test06P4R1Coverage(unittest.TestCase):
    def test_every_pre_fall_unsupported_interval_responded(self):
        fx = fixture()
        p = pred(fx, "P4_r1_coverage")
        self.assertTrue(p["pass"])
        self.assertEqual(p["audit"]["uncovered_intervals"], [])
        arms = fx["main"]["arms"]["A1_unsupported_probe"]
        self.assertGreater(arms["r1_events"], 0)


class Test07P5InertiaLaw(unittest.TestCase):
    def test_velocity_recursion_and_never_frozen(self):
        fx = fixture()
        p = pred(fx, "P5_inertia_law")
        self.assertTrue(p["pass"])
        self.assertTrue(p["velocity_never_frozen"])
        self.assertLess(p["max_residual_m_s"],
                        oe.SEAM_VELOCITY_WINDOW)


class Test08P6SupportForceRemoved(unittest.TestCase):
    def test_no_force_without_contact_and_warm_crosscheck(self):
        fx = fixture()
        p = pred(fx, "P6_support_force_removed")
        self.assertTrue(p["pass"])
        self.assertEqual(p["crosscheck"]["violations"], [])


class Test09P7FallInjection(unittest.TestCase):
    def test_r2_fires_at_declared_horizon_latched_and_labeled(self):
        fx = fixture()
        p = pred(fx, "P7_fall_injection")
        self.assertTrue(p["pass"])
        self.assertEqual(p["fall_declared_tick"],
                         rle.A2_T0 + 89)
        self.assertEqual(p["label"], "monitor_input_injection")
        self.assertTrue(p["r2_latched_to_terminal"])
        self.assertEqual(p["injected_ticks"], rle.A2_TICKS)
        self.assertIn("injected_window_unsupported_overlap", p)
        self.assertLessEqual(p["injected_window_unsupported_overlap"],
                             rle.A2_TICKS)


class Test10P8CleanArmsGreen(unittest.TestCase):
    def test_all_clean_arms_zero_violations(self):
        fx = fixture()
        p = pred(fx, "P8_no_concealed_reset_clean")
        self.assertTrue(p["pass"])
        for arm in ("a0", "a1", "a2"):
            for detector, count in p[arm].items():
                self.assertEqual(count, 0, arm + ":" + detector)


class Test11FB1ConcealedReset(unittest.TestCase):
    def test_clean_green_bite_fires_precondition(self):
        fx = fixture()
        p = pred(fx, "P9_falsifiers_bite")["fb1"]
        self.assertTrue(p["clean_green"])
        self.assertTrue(p["precondition_same_streak"])
        self.assertTrue(p["fired"]["micro_draw_chain"])
        self.assertTrue(p["fired"]["velocity_recursion"])
        self.assertTrue(p["fired"]["phase_recursion"])


class Test12FB2ConcealedForce(unittest.TestCase):
    def test_clean_green_bite_fires_far_above_window(self):
        fx = fixture()
        p = pred(fx, "P9_falsifiers_bite")["fb2"]
        self.assertTrue(p["clean_green"])
        self.assertTrue(p["fired"])
        self.assertGreater(p["residual_m_s"], rle.FB2_IMPULSE_DV / 2.0)
        self.assertGreater(p["residual_m_s"],
                           100 * oe.SEAM_VELOCITY_WINDOW)


class Test13FB3AnimationSubstitution(unittest.TestCase):
    def test_clean_byte_equal_tampered_fires(self):
        fx = fixture()
        p = pred(fx, "P9_falsifiers_bite")["fb3"]
        self.assertTrue(p["clean_green"])
        self.assertTrue(p["fired"])
        self.assertGreater(p["mismatch_count"], 0)
        arms = fx["main"]["falsifiers"]["FB3_animation_substitution"]
        self.assertEqual(arms["clean"]["byte_equality"]["mismatch_ticks"], [])


class Test14FB4StaleSupport(unittest.TestCase):
    def test_clean_covered_tampered_uncovered(self):
        fx = fixture()
        p = pred(fx, "P9_falsifiers_bite")["fb4"]
        self.assertTrue(p["clean_green"])
        self.assertTrue(p["fired"])
        self.assertGreater(len(p["uncovered"]), 0)


class Test15P10StructuralRecords(unittest.TestCase):
    def test_structural_verdicts_amended_cascade(self):
        fx = fixture()
        p = pred(fx, "P10_structural_records")
        self.assertTrue(p["pass"])
        s = p["structural"]
        self.assertTrue(s["sustained_fall_reachable_and_produced"]["verdict"])
        self.assertTrue(s["trip_reflex_reachable_and_produced"]["verdict"])
        self.assertGreaterEqual(s["sustained_fall_reachable_and_produced"]
                                ["first_interval_length"], 90)
        self.assertTrue(all(c > 0 for c in
                            s["sustained_fall_reachable_and_produced"]
                            ["trips_at_fall"]))


class Test16StructuralAndEnvelopeLaws(unittest.TestCase):
    def test_supervisor_module_has_no_pose_write_channel(self):
        source = (HERE / "out_of_envelope.py").read_bytes().decode("utf-8")
        self.assertEqual(oe.structural_no_pose_write(source), [])

    def test_a1_velocity_envelope_and_energy_window(self):
        fx = fixture()
        arms = fx["main"]["arms"]["A1_unsupported_probe"]
        self.assertTrue(arms["velocity_envelope_ok"])
        self.assertLess(arms["max_abs_v_m_s"],
                        arms["velocity_envelope_m_s"])
        battery = arms["detectors"]
        self.assertEqual(battery["energy_account"]["violations"], [])
        self.assertEqual(battery["warm_force_crosscheck"]["violations"], [])


if __name__ == "__main__":
    unittest.main()
