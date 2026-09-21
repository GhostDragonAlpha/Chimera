"""Positive contracts for the reality/fantasy adjudicator.

Run: python -B tools/creature_graph/tests/test_reality_gate.py
Standard library only; the gate's expectation tables are derived from the
repo's pinned measured files, so these tests also re-derive them.
"""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import reality_gate as rg

VALIDATION_DIR = Path(__file__).resolve().parents[1] / "validation" / "reality_gate_20260920"


def bundle(**over):
    b = {
        "schema": rg.BUNDLE_SCHEMA,
        "name": "fixture",
        "species": [{"name": "Macaca mulatta", "provenance": "fixture"}],
        "components": [
            {"id": "c1", "kind": "anatomy", "segment_label": "femur",
             "stage": {"label": "infant", "provenance": "fixture", "confirmed": True},
             "species": "Macaca mulatta"},
            {"id": "c2", "kind": "anatomy", "segment_label": "tibia",
             "stage": {"label": "infant", "provenance": "fixture", "confirmed": True},
             "species": "Macaca mulatta"},
        ],
        "allometry": {
            "stage": "infant",
            "ratios": {"femur:tibia": {"value": 1.05, "from": ["fixture"], "source": "fixture"}},
        },
    }
    b.update(over)
    return b


class StageConsistency(unittest.TestCase):
    def test_unlabeled_component_is_a_named_violation(self):
        b = bundle()
        b["components"][0]["stage"] = None
        verdict = rg.adjudicate(b)
        codes = {v["code"] for v in verdict["violations"]}
        self.assertIn("stage-unlabeled", codes)
        viol = next(v for v in verdict["violations"] if v["code"] == "stage-unlabeled")
        self.assertEqual(viol["components"], ["c1"])
        self.assertEqual(verdict["category"], "fantasy")

    def test_mixed_stages_name_the_components_per_stage(self):
        b = bundle()
        b["components"][1]["stage"]["label"] = "adult"
        b["components"][1]["stage"]["confirmed"] = True
        verdict = rg.adjudicate(b)
        viol = next(v for v in verdict["violations"] if v["code"] == "stage-mixed")
        self.assertEqual(viol["components_by_stage"]["infant"], ["c1"])
        self.assertEqual(viol["components_by_stage"]["adult"], ["c2"])
        self.assertEqual(viol["measured"]["stage_component_counts"], {"adult": 1, "infant": 1})

    def test_adult_label_requires_confirmation(self):
        b = bundle()
        for c in b["components"]:
            c["stage"] = {"label": "adult", "provenance": "fixture", "confirmed": False}
        verdict = rg.adjudicate(b)
        codes = {v["code"] for v in verdict["violations"]}
        self.assertIn("adult-unconfirmed", codes)
        self.assertEqual(verdict["category"], "fantasy")

    def test_confirmed_adult_passes_stage_check(self):
        b = bundle()
        for c in b["components"]:
            c["stage"] = {"label": "adult", "provenance": "fixture", "confirmed": True}
        check, violations = rg.check_stage_consistency(b)
        self.assertEqual(check["verdict"], "pass")
        self.assertEqual(violations, [])


class AllometricCoherence(unittest.TestCase):
    def test_within_band_ratio_passes(self):
        check, violations = rg.check_allometric_coherence(bundle())
        self.assertEqual(check["verdict"], "pass")
        self.assertEqual(violations, [])
        expected_mean = rg.infant_table()["ratios"]["femur:tibia"]["mean"]
        self.assertAlmostEqual(check["measured"]["segments"]["femur:tibia"]["deviation_frac"],
                               1.05 / expected_mean - 1.0, places=6)

    def test_out_of_band_ratio_violates_with_measured_deviation(self):
        b = bundle()
        b["allometry"]["ratios"]["femur:tibia"]["value"] = 2.0
        check, violations = rg.check_allometric_coherence(b)
        self.assertEqual(len(violations), 1)
        v = violations[0]
        self.assertEqual(v["law"], rg.LAW_ALLOMETRY)
        self.assertGreater(abs(v["measured"]["deviation_frac"]), rg.TOLERANCE_FRAC)
        self.assertIn("segment", v)

    def test_unmeasurable_expectation_is_refused_not_guessed(self):
        b = bundle()
        b["allometry"]["ratios"]["wing:body"] = {"value": 0.5, "from": ["fixture"], "source": "fixture"}
        check, violations = rg.check_allometric_coherence(b)
        self.assertEqual(violations[0]["code"], "allometry-unmeasurable-expectation")
        self.assertEqual(violations[0]["measured"]["declared_value"], 0.5)

    def test_per_bone_scale_incoherence_matches_the_h2_pre_measurement(self):
        b = bundle()
        b["allometry"]["per_bone_scale_factors"] = {"h2_bone_2": 3.814326112931453}
        b["allometry"]["reference_uniform_scale"] = 3.2314822711250724
        check, violations = rg.check_allometric_coherence(b)
        self.assertEqual(len(violations), 1)
        self.assertAlmostEqual(violations[0]["measured"]["deviation_frac"], 0.18034, places=4)

    def test_adult_table_derives_table1_ratios(self):
        t = rg.adult_table()
        self.assertAlmostEqual(t["ratios"]["thigh:shank"]["mean"], 0.163 / 0.182, places=9)
        self.assertAlmostEqual(t["ratios"]["shank:thigh"]["mean"], 0.182 / 0.163, places=9)
        self.assertEqual(t["mass_kg"], 10.038)

    def test_infant_table_is_leave_one_out(self):
        t = rg.infant_table(exclusions=("000875604",))
        self.assertEqual(t["exclusions"], ["000875604"])
        self.assertEqual(t["per_specimen"].keys(), {"000875599"})
        # specimen B's femur:tibia chain (ranks 3/7): 43.00 / 41.20
        self.assertAlmostEqual(t["ratios"]["femur:tibia"]["mean"], 43.00 / 41.20, places=6)

    def test_infant_and_adult_tables_measurably_disagree(self):
        """The stage shift is real: infant femur:tibia vs adult thigh:shank."""
        inf = rg.infant_table()["ratios"]["femur:tibia"]["mean"]
        adu = rg.adult_table()["ratios"]["thigh:shank"]["mean"]
        self.assertGreater(abs(inf - adu) / adu, rg.TOLERANCE_FRAC)


class TaxonomicCoherence(unittest.TestCase):
    def test_single_species_passes(self):
        check, violations = rg.check_taxonomic_coherence(bundle())
        self.assertEqual(check["verdict"], "pass")
        self.assertEqual(violations, [])

    def test_cross_species_names_the_distance(self):
        b = bundle(species=[{"name": "Macaca mulatta", "provenance": "fixture"},
                            {"name": "Macaca fuscata", "provenance": "fixture"}])
        check, violations = rg.check_taxonomic_coherence(b)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0]["code"], "cross-species-substitution")
        self.assertEqual(violations[0]["measured"]["taxonomic_distance_edges"], 2)
        self.assertEqual(violations[0]["measured"]["pair"], ["Macaca fuscata", "Macaca mulatta"])

    def test_unresolvable_species_never_passes_silently(self):
        b = bundle(species=[{"name": "Homo sapiens", "provenance": "outside the pinned Macaca extract"}])
        check, violations = rg.check_taxonomic_coherence(b)
        self.assertEqual(violations[0]["code"], "species-unresolvable")

    def test_no_species_label_is_a_violation(self):
        b = bundle(species=[])
        for c in b["components"]:
            c.pop("species")
        check, violations = rg.check_taxonomic_coherence(b)
        self.assertEqual(violations[0]["code"], "species-unlabeled")


class PhysicsBars(unittest.TestCase):
    def bar(self, **over):
        bar = {"law": "conservation", "verdict": "pass",
               "measured": {"closure_deviation_frac": 0.0}, "falsifier": "fixture", "source": "fixture"}
        bar.update(over)
        return bar

    def test_vocabulary_is_the_aliveness_bars(self):
        self.assertEqual(rg.PHYSICS_BAR_LAWS, ("conservation", "pressure", "pose", "touch"))

    def test_passing_bar_is_adjudicated_and_reported(self):
        check, violations = rg.check_physics_bars({"physics_bars": [self.bar()]})
        self.assertEqual(check["verdict"], "pass")
        self.assertEqual(violations, [])
        self.assertEqual(check["measured"]["bars_adjudicated"][0]["law"], "conservation")

    def test_failing_bar_violates_with_its_numbers(self):
        check, violations = rg.check_physics_bars(
            {"physics_bars": [self.bar(verdict="fail", measured={"dP_Pa": 9000.0})]})
        self.assertEqual(violations[0]["code"], "physics-bar-failed")
        self.assertEqual(violations[0]["measured"], {"dP_Pa": 9000.0})

    def test_inventing_new_physics_is_forbidden(self):
        check, violations = rg.check_physics_bars(
            {"physics_bars": [self.bar(law="quantum_flavor")]} )
        self.assertEqual(violations[0]["code"], "physics-bar-unknown-law")

    def test_numberless_bar_is_refused(self):
        check, violations = rg.check_physics_bars(
            {"physics_bars": [self.bar(measured={})]})
        self.assertEqual(violations[0]["code"], "physics-bar-unmeasured")

    def test_absent_bars_are_reported_not_gated(self):
        verdict = rg.adjudicate(bundle())
        self.assertEqual(verdict["reported_not_gated"], ["physics_bars"])


class TheGate(unittest.TestCase):
    def test_reality_first_zero_violations_is_reality(self):
        verdict = rg.adjudicate(bundle())
        self.assertEqual(verdict["category"], "reality")
        self.assertEqual(verdict["violations"], [])

    def test_any_violation_is_fantasy_by_default(self):
        b = bundle()
        b["components"][0]["stage"] = None
        verdict = rg.adjudicate(b)
        self.assertEqual(verdict["category"], "fantasy")

    def test_fantasy_requires_manifest_acknowledgement(self):
        b = bundle()
        b["components"][0]["stage"] = None
        b["fantasy_manifest_acknowledged"] = True
        verdict = rg.adjudicate(b)
        codes = {v["code"] for v in verdict["violations"]}
        self.assertNotIn("fantasy-unacknowledged", codes)
        self.assertEqual(verdict["construction"]["fantasy_manifest_acknowledged"], True)
        b2 = bundle()
        b2["components"][0]["stage"] = None
        verdict2 = rg.adjudicate(b2)
        self.assertIn("fantasy-unacknowledged", {v["code"] for v in verdict2["violations"]})

    def test_verdict_is_deterministic(self):
        b = bundle()
        self.assertEqual(rg.adjudicate(b), rg.adjudicate(b))

    def test_foreign_bundle_schema_refuses(self):
        with self.assertRaises(rg.BundleError):
            rg.adjudicate({"schema": "something.else.v9", "name": "x"})

    def test_every_check_names_a_law_and_carries_a_measurement(self):
        verdict = rg.adjudicate(bundle())
        self.assertEqual([c["law"] for c in verdict["checks"]], list(rg.LAWS))
        for check in verdict["checks"]:
            self.assertIsInstance(check["measured"], dict)


class TheFourAdjudications(unittest.TestCase):
    """The banked receipts: the gate's runs, re-adjudicated live."""

    def test_receipt_pre_registration_hits(self):
        receipt = json.loads((VALIDATION_DIR / "receipt.json").read_text(encoding="utf-8"))
        hits = receipt["measurements"]["pre_registration_hits"]
        for key, hit in sorted(hits.items()):
            self.assertTrue(hit["hit"], "pre-registration MISS for %s" % key)

    def test_receipt_falsifier_checks_hold(self):
        receipt = json.loads((VALIDATION_DIR / "receipt.json").read_text(encoding="utf-8"))
        checks = receipt["measurements"]["falsifier_checks"]
        self.assertTrue(checks["all_four_landed_as_pre_registered"])
        self.assertTrue(checks["every_violation_carries_a_measured_number"])
        self.assertTrue(checks["every_law_check_carries_a_measurement"])

    def test_bundles_readjudicate_to_the_banked_categories(self):
        banked = {"a_infant_ct": "reality", "b_h2_mount": "fantasy",
                  "c_walker": "reality", "d_chimera": "fantasy"}
        for key, expected in sorted(banked.items()):
            b = json.loads((VALIDATION_DIR / ("%s_bundle.json" % key)).read_text(encoding="utf-8"))
            self.assertEqual(rg.adjudicate(b)["category"], expected, key)

    def test_h2_mount_violations_are_itemized_per_bone(self):
        b = json.loads((VALIDATION_DIR / "b_h2_mount_bundle.json").read_text(encoding="utf-8"))
        verdict = rg.adjudicate(b)
        bones = {v["component"] for v in verdict["violations"]
                 if v["code"] == "allometric-scale-incoherence"}
        self.assertEqual(bones, {"h2_bone_2", "h2_bone_3", "h2_bone_6", "h2_bone_7",
                                 "h2_bone_18", "h2_bone_24", "h2_bone_25"})
        for v in verdict["violations"]:
            if v["code"] == "allometric-scale-incoherence":
                self.assertGreater(abs(v["measured"]["deviation_frac"]), rg.TOLERANCE_FRAC)

    def test_chimera_within_forelimb_ratios_stay_unflagged(self):
        b = json.loads((VALIDATION_DIR / "d_chimera_bundle.json").read_text(encoding="utf-8"))
        verdict = rg.adjudicate(b)
        segments = {v["segment"] for v in verdict["violations"] if v["code"] == "allometric-deviation"}
        self.assertEqual(segments, {"humerus:femur", "forearm:tibia"})
        check = next(c for c in verdict["checks"] if c["law"] == rg.LAW_ALLOMETRY)
        self.assertTrue(check["measured"]["segments"]["humerus:forearm"]["within_band"])


if __name__ == "__main__":
    unittest.main()
