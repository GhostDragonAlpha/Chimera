"""MAT2-F02 test suite: bites fail-first, then the pinned pass, then the build.

Run from THIS directory (stdlib only):
    python -B -m unittest test_implementation -v

The heavy test (test_50) runs the full build (bites -> checks -> frames ->
trace), the campaign capture manifest against the REGISTRY profile object,
and the mechanical report; it is the card's gate. The earlier tests are
focused probes with pinned bars.
"""
from __future__ import annotations

import json
import pathlib
import sys
import unittest

import terrain_contact as tc
import f01_implementation as f01
import run_terrain_contact as run

HERE = pathlib.Path(__file__).resolve().parent
EVIDENCE = HERE / "evidence"

SOURCES = tc.load_sources()
(BUNDLE, RAW, ASSET_RECEIPT, SURFACE, DECLARATION, TRUNK, LAW) = SOURCES


class Test01PinsAndTiedAsset(unittest.TestCase):
    def test_pins_raw_hashes(self):
        pins = tc.load_pins()
        self.assertEqual(len(pins), 9)
        self.assertTrue(all(p["raw_match"] for p in pins.values()))

    def test_asset_validator_passes(self):
        self.assertTrue(ASSET_RECEIPT["validated"])
        self.assertLessEqual(ASSET_RECEIPT["worst_mesh_analytic_deviation_m"],
                             tc.tb.DISCRETIZATION_BOUND_M)
        self.assertEqual(ASSET_RECEIPT["hygiene_broken"], 0)
        self.assertEqual(ASSET_RECEIPT["hygiene_deviant"], 0)

    def test_contact_body_is_the_render_arrays(self):
        body = tc.ground_contact_body(BUNDLE)
        checks = tc.tied_asset_checks(BUNDLE, RAW, body)
        self.assertTrue(checks["ok"], checks)
        self.assertTrue(checks["arrays_exact_equal"])
        self.assertEqual(checks["worst_component_diff"], 0.0)
        self.assertEqual(len(body.triangles), 3200)

    def test_frame_map_is_an_involution(self):
        p = (1.25, -3.5, 7.0)
        self.assertEqual(tc.to_clearing(tc.to_contact(p)), p)


class Test02FalsifierBites(unittest.TestCase):
    """Every falsifier must BITE. Recorded before any pinned-pass assertion."""

    def test_all_five_bites_bite(self):
        bites = [
            tc.bite_ghost_support_decoupled_asset(BUNDLE, SURFACE),
            tc.bite_parallel_solver_unaccepted(SURFACE),
            tc.bite_material_identity_detached(BUNDLE),
            tc.bite_ghost_support_past_boundary(BUNDLE),
            tc.bite_off_frame_probe_subject(f01),
        ]
        for b in bites:
            self.assertTrue(b["bites"], b)


class Test03SettleAgreement(unittest.TestCase):
    def test_s1_rests_on_query_surface_through_shared_path(self):
        body = tc.ground_contact_body(BUNDLE)
        o = tc.settle(body, SURFACE, "S1", tc.SITES["S1"])
        p3 = tc.resting_checks({"S1": o}, BUNDLE)
        p4 = tc.point_normal_checks({"S1": o}, BUNDLE)
        self.assertTrue(p3["ok"], p3)
        self.assertTrue(p4["ok"], p4)
        self.assertLessEqual(o["worst_ledger_residual"], 1e-12)
        for rec in o["records_last_tick"]:
            self.assertEqual(rec["matter_a"], tc.GROUND_MATTER_ID)
            self.assertEqual(rec["matter_b"], tc.PROBE_MATTER_ID)
            self.assertEqual(rec["surface_a"], tc.GROUND_SURFACE_ID)

    def test_shared_path_document_validates(self):
        body = tc.ground_contact_body(BUNDLE)
        o = tc.settle(body, SURFACE, "S1", tc.SITES["S1"])
        p2 = tc.shared_path_checks({"S1": o}, LAW)
        self.assertTrue(p2["ok"], p2)
        self.assertTrue(p2["declarations_match_law"])

    def test_exhaustive_reference_identical(self):
        p2b = tc.exhaustive_reference_check(BUNDLE, SURFACE)
        self.assertTrue(p2b["ok"], p2b)

    def test_determinism_same_site_twice(self):
        a = tc.settle(tc.ground_contact_body(BUNDLE), SURFACE, "S1", tc.SITES["S1"])
        b = tc.settle(tc.ground_contact_body(BUNDLE), SURFACE, "S1", tc.SITES["S1"])
        strip = lambda o: tc.canonical(
            {k: v for k, v in o.items() if k != "probe"})
        self.assertEqual(strip(a), strip(b))


class Test50FullBuildAndCapture(unittest.TestCase):
    """The card gate: the whole build, the capture manifest against the
    REGISTRY profile, and the mechanical report."""

    def test_build_capture_and_report(self):
        import make_capture_manifest
        import make_report

        results = run.build()
        self.assertTrue(results["all_bites_bite"])
        self.assertTrue(results["all_ok"], {k: results[k].get("ok")
                                            for k in results
                                            if isinstance(results[k], dict)})
        make_capture_manifest.main()
        receipt = json.loads((EVIDENCE / "validation_receipt.json")
                             .read_text(encoding="utf-8"))
        self.assertTrue(receipt["structurally_valid"], receipt)
        self.assertEqual(receipt["validated_profile_id"], "forest")
        self.assertEqual(receipt["validated_profile_kind"], "visible_static")
        make_report.main()
        report = (HERE / "report.md").read_text(encoding="utf-8")
        self.assertIn("Verdict: PASS", report)


if __name__ == "__main__":
    unittest.main(verbosity=2)
