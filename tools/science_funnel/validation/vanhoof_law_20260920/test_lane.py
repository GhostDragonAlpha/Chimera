"""VLAW lane tests: the admission pattern's mechanical falsifiers, lane-local.

Covers (prereg work_plan step 6): value pins (F3), registered-constant consistency,
law-run agreement, count identity, no-guess (every admitted value is a landed pin),
provenance completeness, unit sanity, mutation probe (content-derived identity),
and the cross-specimen summary's closure. Determinism proper (3-run byte-identity)
is enforced by the lane's run protocol on the artifacts as committed; here the
embedded record_set_digest is re-derived from the committed files (replay check).

Run: python -B tools/science_funnel/validation/vanhoof_law_20260920/test_lane.py
"""
import glob
import hashlib
import json
import os
import sys
import unittest
from decimal import Decimal

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.abspath(os.path.join(BASE, "..", "..", "..", "..")))

import laws_registered as L  # noqa: E402
from tools.science_funnel.common import canonical, sha  # noqa: E402

TLANE = os.path.join(BASE, "..", "vanhoof_transcription_20260920")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load(name, lane=BASE):
    with open(os.path.join(lane, name), "rb") as f:
        return json.loads(f.read().decode("utf-8"))


class VanhoofLawLane(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prereg = load("receipt.json")
        cls.constants = load("constants.json")
        cls.laws = load("laws_registered.json")
        cls.admission = load("admission.json")
        cls.records = load("records_vanhoof_s2.json")["records"]
        cls.summary = load("cross_specimen_summary.json")
        cls.rec = load("reconciliation.json", lane=TLANE)
        cls.tent = sorted((c["muscle"], c["specimen"], c["field"], c["value"])
                          for c in cls.rec["cells"] if c["verdict"] == "TENTATIVE")

    def test_01_value_pins_hold(self):
        self.assertEqual(sha256_file(os.path.join(TLANE, "reconciliation.json")),
                         self.prereg["target"]["frozen_inputs"]["reconciliation.json"])
        blob = json.dumps(self.tent, separators=(",", ":"), sort_keys=True).encode("utf-8")
        self.assertEqual(hashlib.sha256(blob).hexdigest(),
                         self.prereg["target"]["value_pin"]["sha256"])
        self.assertEqual(len(self.tent), 654)

    def test_02_registered_constant_is_the_stated_one(self):
        self.assertEqual(self.constants["route"], "stated_cited")
        self.assertEqual(self.constants["constant"]["rho_g_cm3"], 1.1)
        self.assertEqual(self.constants["unchanged_inherited_constants"]["law_tolerance_rel"], 0.02)
        self.assertEqual(self.constants["unchanged_inherited_constants"]["floor_law_pass"], 0.90)
        self.assertTrue(self.constants["evidence"]["quotes_verbatim"])

    def test_03_law_run_agrees_with_recomputation(self):
        _, rho = L.load_constants()
        rec, _ = L.load_reconciliation_with_pins()
        rows = L.compute_rows(rec, rho)
        self.assertEqual(rows, self.laws["law_rows"])
        self.assertEqual(self.laws["n_checkable_rows"], 218)
        self.assertEqual(self.laws["n_pass"], 146)
        self.assertEqual(self.laws["law_pass_rate"], 0.6697)
        self.assertEqual(self.laws["admission_gate"], "F1_FIRED_TIERS_EXECUTE_PER_PREREG")

    def test_04_admission_count_identity_closes(self):
        ci = self.admission["count_identity"]
        self.assertTrue(ci["closed"])
        self.assertEqual(ci["fetched"], 774)
        self.assertEqual(ci["admitted"], 438)
        self.assertEqual(ci["rejected_weight"], 336)
        ts = self.admission["tier_summary"]
        self.assertEqual((ts["law_pass_rows"], ts["law_fail_rows"]), (146, 72))
        self.assertEqual(ts["refused_row_closure_violation_cells"], 216)
        self.assertEqual(ts["marker_refused_cells"], 105)
        self.assertEqual(ts["merged_covered_positions"], 15)
        closed_taxonomy = {"row_closure_violation", "marker_absent", "marker_absent_cfr",
                           "marker_crossref_APB", "marker_crossref_FDP", "merged_cell_covered"}
        for r in self.admission["rejections"]:
            self.assertIn(r["refusal"]["code"], closed_taxonomy)

    def test_05_no_guess_every_admitted_value_is_a_landed_pin(self):
        pins = {(m, s, f): v for (m, s, f, v) in self.tent}
        self.assertEqual(len(self.records), 438)
        seen = set()
        for r in self.records:
            key = (r["payload"]["conditions"]["muscle"], r["payload"]["conditions"]["specimen"],
                   r["payload"]["conditions"]["field"])
            self.assertNotIn(key, seen)
            seen.add(key)
            self.assertEqual(r["payload"]["conditions"]["printed_value"], pins[key])
            self.assertGreater(float(r["payload"]["value_si"]), 0.0)
        self.assertEqual(len(seen), 438)
        self.assertTrue(seen.issubset(set(pins.keys())))
        # exactly the law-PASS rows' cells
        pass_keys = {(r["muscle"], r["specimen"]) for r in self.laws["law_rows"] if r["law"] == "PASS"}
        for r in self.records:
            self.assertIn((r["payload"]["conditions"]["muscle"],
                           r["payload"]["conditions"]["specimen"]), pass_keys)
            self.assertEqual(r["payload"]["conditions"]["row_closure_law"]["verdict"], "PASS")
            self.assertIn(r["class_contract"]["class_id"], ("batch.property.measurement",))

    def test_06_provenance_completeness_and_units(self):
        units = {"mass_g": "kg", "fl_mm": "m", "pcsa_mm2": "m2"}
        for r in self.records:
            c = r["payload"]["conditions"]
            for field in ("sheet", "tiff_sha256", "panel", "tiles", "muscle", "specimen",
                          "field", "printed_value", "pass_values", "legibility", "row_closure_law"):
                self.assertTrue(c.get(field), "missing provenance %s" % field)
            self.assertEqual(c["tiff_sha256"],
                             "cb9e91be3d2345182b6d2b956245b76905243d4bbf37fff79c3d96a802e5debe")
            self.assertEqual(c["row_closure_law"]["rho_g_cm3"], 1.1)
            self.assertEqual(c["row_closure_law"]["constant_route"].split(":")[0], "stated_cited")
            for t in c["tiles"]:
                self.assertTrue(t["crop_sha256"] and t["pass"] in ("passA", "passB"))
            self.assertEqual(r["payload"]["unit_si"], units[c["field"]])
            self.assertEqual(r["payload"]["quantity"], {"mass_g": "mass", "fl_mm": "length",
                                                        "pcsa_mm2": "area"}[c["field"]])

    def test_07_replay_record_set_digest(self):
        body = {"records": self.admission["records"], "rejections": self.admission["rejections"]}
        self.assertEqual(sha(canonical(body)), self.admission["record_set_digest"])
        self.assertEqual(len(self.records), len({r["external_id"] for r in self.records}))
        for r in self.records:
            self.assertTrue(r["external_id"].startswith("vanhoof:s002:"))

    def test_08_mutation_probe_breaks_identity(self):
        body = {"records": self.admission["records"], "rejections": self.admission["rejections"]}
        mutated = json.loads(json.dumps(body))
        mutated["records"][0]["payload"]["value_si"] *= 1.000001
        self.assertNotEqual(sha(canonical(body)), sha(canonical(mutated)))

    def test_09_cross_specimen_summary_closes(self):
        self.assertEqual(self.summary["n_cells_summarized"], 654)
        n_fields = sum(d["fields"][f]["n"] for d in self.summary["muscles"].values()
                       for f in ("mass_g", "fl_mm", "pcsa_mm2"))
        self.assertEqual(n_fields, 654)
        law_cells = sum(d["law_rows"] for d in self.summary["muscles"].values())
        self.assertEqual(law_cells, 218)
        for m, d in self.summary["muscles"].items():
            for f, fd in d["fields"].items():
                self.assertGreater(fd["n"], 0)
                self.assertLessEqual(fd["min"], fd["max"])
                if fd["min"] is not None:
                    self.assertGreater(fd["min"], 0.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
