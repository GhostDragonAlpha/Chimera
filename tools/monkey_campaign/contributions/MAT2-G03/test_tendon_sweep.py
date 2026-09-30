"""MAT2-G03 named checks — the executable done_when suite.

done_when (verbatim): "Relevant pose-range outputs are finite and
independently checked; unresolved bodies cannot appear as zero arms"

Receipt-semantics law: any change to qualification_receipt.json semantics
lands TOGETHER with the named check that asserts it (batch_gates
named_check_suite enforces co-change).
"""
from __future__ import annotations

import json
import math
import pathlib
import unittest

import tendon_sweep as ts

HERE = pathlib.Path(__file__).resolve().parent
DOC = json.loads((HERE / "tendon_sweep.json").read_text(encoding="utf-8"))
TRACE = json.loads((HERE / "sweep_trace.json").read_text(encoding="utf-8"))


def arm_rows():
    for t in DOC["sweep"]:
        for m, e in t["muscles"].items():
            for c, ce in e["coords"].items():
                yield t, m, c, ce


def static_rows():
    for crow in DOC["static_checks"]:
        for m, ce in crow["muscles"].items():
            yield crow, m, ce


class TestFiniteAndChecked(unittest.TestCase):
    def test_every_sweep_output_finite(self):
        for t, m, c, ce in arm_rows():
            if ce["status"] != "evaluated_declared_chain":
                continue
            for key in ("l_m", "r_analytic_m", "r_fd_m", "residual_m",
                        "envelope_limit_m"):
                self.assertIsInstance(ce[key], float, (t["tick"], m, c, key))
                self.assertTrue(math.isfinite(ce[key]),
                                ("nonfinite", t["tick"], m, c, key))

    def test_every_static_output_finite(self):
        for crow, m, ce in static_rows():
            if ce["status"] != "evaluated_declared_chain":
                continue
            for key in ("l_m", "r_analytic_m", "r_fd_m", "residual_m"):
                self.assertTrue(math.isfinite(ce[key]), (crow["coordinate"],
                                                         m, key))

    def test_independent_check_agreement_within_window(self):
        w_abs = DOC["sweep_spec"]["windows"]["W2_identity_abs_m"]
        w_rel = DOC["sweep_spec"]["windows"]["W2_identity_rel"]
        n = 0
        for t, m, c, ce in arm_rows():
            if ce["status"] != "evaluated_declared_chain":
                continue
            window = max(w_abs, w_rel * abs(ce["r_analytic_m"]))
            self.assertLessEqual(ce["residual_m"], window,
                                 (t["tick"], m, c))
            self.assertTrue(ce["within_window"])
            n += 1
        self.assertEqual(n, 546)

    def test_fk_closure_within_window(self):
        chk = DOC["fk_closure_check"]
        self.assertTrue(chk["within_window"])
        self.assertLessEqual(chk["observed_max_deviation"],
                             chk["window"])

    def test_envelope_window_holds(self):
        for t, m, c, ce in arm_rows():
            if ce["status"] != "evaluated_declared_chain":
                continue
            self.assertTrue(ce["within_envelope"], (t["tick"], m, c))
            self.assertLessEqual(abs(ce["r_analytic_m"]),
                                 ce["envelope_limit_m"])
            self.assertLessEqual(abs(ce["r_fd_m"]),
                                 ce["envelope_limit_m"])

    def test_sweep_totality_frozen_set(self):
        self.assertEqual(DOC["sweep_spec"]["ticks"], 21)
        self.assertEqual(sorted(DOC["sweep"][0]["muscles"]),
                         sorted(ts.GRASP_MUSCLES))
        self.assertEqual([t["tick"] for t in DOC["sweep"]],
                         list(range(21)))
        fc = DOC["frozen_counts"]
        self.assertEqual(fc["grasp_muscles"], 13)
        self.assertEqual(fc["path_records"], 48)
        self.assertEqual(fc["owners_census"],
                         {"osim.body.radius": 18, "osim.body.hand": 17,
                          "osim.body.humerus": 8, "osim.body.ulna": 5})
        self.assertEqual(fc["per_muscle_records"], ts.RECORD_COUNTS)
        self.assertEqual(fc["a09_terminal_census"],
                         {"mapped": 3, "pending_assembly_mapping": 14,
                          "not_on_hand_body": 31})

    def test_unresolved_bodies_cannot_appear_as_zero_arms(self):
        """The card's core clause: a non-evaluated row carries arms null
        (never 0.0, never any number); evaluated rows carry real numbers."""
        seen_unresolved = 0
        for t, m, c, ce in arm_rows():
            if ce["status"] != "evaluated_declared_chain":
                self.assertIsNone(ce.get("arms"))
                self.assertIsNone(ce.get("l_m"))
                seen_unresolved += 1
            else:
                self.assertNotIn("arms", ce)
        for _crow, m, ce in static_rows():
            if ce["status"] != "evaluated_declared_chain":
                self.assertIsNone(ce.get("arms"))
        self.assertEqual(seen_unresolved, 0)  # all owners declared here
        # the LAW is still exercised by FB2 (falsifier receipt must show it)
        fb = json.loads((HERE / "evidence" / "falsifier_receipt.json")
                        .read_text(encoding="utf-8"))
        arm2 = next(a for a in fb["arms"] if a["arm"] == "FB2")
        self.assertTrue(arm2["bit"])
        self.assertEqual(arm2["observed_refusal"],
                         "unresolved_zero_arm_refused")

    def test_trace_matches_document(self):
        self.assertEqual(TRACE["schema"], ts.TRACE_SCHEMA)
        self.assertEqual(TRACE["tick_interval"], [0, 20])
        self.assertEqual(len(TRACE["ticks"]), 21)
        for tr, t in zip(TRACE["ticks"], DOC["sweep"]):
            self.assertEqual(tr["tick"], t["tick"])
            self.assertAlmostEqual(tr["q_rad"], t["q_rad"], places=15)
            for m in ts.GRASP_MUSCLES:
                for c in ts.ARM_COORDS:
                    doc_e = t["muscles"][m]["coords"][c]
                    tr_e = tr["muscles"][m][c]
                    if doc_e["status"] != "evaluated_declared_chain":
                        self.assertIsNone(tr_e)
                    else:
                        self.assertAlmostEqual(
                            tr_e["r_analytic_m"], doc_e["r_analytic_m"],
                            places=15)

    def test_signed_convention_physical_sanity(self):
        """r_j = -dl/dq_j under the declared convention: wrist extensors
        carry negative flexion arms and flexors positive at mid-range
        (declared-sign check, rendered from the document numbers)."""
        mid = DOC["sweep"][10]
        an = mid["muscles"]["muscle.ext_carpi_ulnaris"]["coords"][
            "wrist_flexion"]["r_analytic_m"]
        fl = mid["muscles"]["muscle.flex_carpi_radialis"]["coords"][
            "wrist_flexion"]["r_analytic_m"]
        self.assertLess(an, 0.0)
        self.assertGreater(fl, 0.0)

    def test_no_unlawful_constant_anywhere(self):
        raw = (HERE / "tendon_sweep.json").read_text(encoding="utf-8")
        for bad in ("kappa", "n_m_per_rad", "torque_nm",
                    "stiffness_value", "fmax_consumed"):
            self.assertNotIn(bad, raw)

    def test_falsifier_receipt_all_green(self):
        fb = json.loads((HERE / "evidence" / "falsifier_receipt.json")
                        .read_text(encoding="utf-8"))
        self.assertTrue(fb["F_all_green"])
        self.assertEqual(len(fb["arms"]), 6)
        for arm in fb["arms"]:
            self.assertTrue(arm["bit"], arm["arm"])
            self.assertTrue(arm["clean_control"]["within_tolerance"],
                            arm["arm"])
            self.assertEqual(arm["premature_result"], "CLEAN_PASSED")

    def test_criteria_identity(self):
        self.assertEqual(DOC["identity"]["criteria_sha256"],
                         ts.CRITERIA_SHA256)
        self.assertEqual(DOC["identity"]["scope_sha256"], ts.SCOPE_SHA256)
        self.assertEqual(DOC["checks"]["criteria_sha256"],
                         ts.CRITERIA_SHA256)


if __name__ == "__main__":
    unittest.main()
