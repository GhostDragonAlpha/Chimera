"""test_implementation.py -- MAT2-X01 extraction tests (frozen probes P1-P4, F1-F6).

Laws: every quoted clause reproduces from its pinned record; identities are
full 64-hex and pinned; the objective contains no invented elements; archived
envelope numbers are not promoted; exactly one decision request; tampered
records refuse loudly.
"""
import json
import pathlib
import re
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import implementation as impl  # noqa: E402


class ObjectiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.obj = impl.extract()

    # ---- P1/P3/P4 identity pins (load_pinned already refused on drift)
    def test_contract_identity_pinned(self):
        self.assertEqual(impl.sha256_file(impl.CONTRACT), impl.CONTRACT_SHA256)
        contract = json.loads(impl.CONTRACT.read_text(encoding="utf-8"))
        self.assertEqual(contract["schema"], "chimera.completion_contract.v1")
        self.assertEqual(contract["task_id"], "MAT2-P01")
        self.assertEqual(contract["identities"]["active_scope_sha256"], impl.SCOPE_SHA)
        self.assertEqual(contract["identities"]["criteria_sha256"], impl.P01_CRITERIA_SHA)
        self.assertEqual(contract["identities"]["archived_scope_sha256"], impl.ARCHIVED_SCOPE_SHA)
        self.assertEqual(contract["identities"]["instruction_revision"], "astra-0031")

    def test_authority_files_full_hash_pinned(self):
        for path, expected in (
            (impl.MATERIAL_PLAN, impl.MATERIAL_PLAN_SHA256),
            (impl.APPROVED_SCOPE, impl.APPROVED_SCOPE_SHA256),
            (impl.MONKEY_RUN, impl.MONKEY_RUN_SHA256),
            (impl.COMPLETION_MAP, impl.COMPLETION_MAP_SHA256),
            (impl.HOLODECK_CATALOG, impl.HOLODECK_CATALOG_SHA256),
        ):
            self.assertEqual(impl.sha256_file(path), expected, str(path))

    # ---- P2 clause carry
    def test_clauses_carry_in_catalog_p01_done_when(self):
        catalog = json.loads(impl.COMPLETION_MAP.read_text(encoding="utf-8"))
        tasks = {t["id"]: t for t in catalog["tasks"]}
        contract = json.loads(impl.CONTRACT.read_text(encoding="utf-8"))
        p01 = impl.norm(tasks["P01"]["done_when"])
        self.assertIn(impl.norm(contract["core_clause"]["text"]), p01)
        self.assertIn(
            impl.norm(contract["material_first_addition"]["text"]), p01)

    def test_card_done_when_live_in_catalog(self):
        catalog = json.loads(impl.COMPLETION_MAP.read_text(encoding="utf-8"))
        tasks = {t["id"]: t for t in catalog["tasks"]}
        self.assertEqual(impl.norm(tasks["X01"]["done_when"]),
                         impl.norm(impl.CARD_DONE_WHEN))

    # ---- F5 quote reproduction oracle
    def test_every_evidence_quote_reproduces(self):
        sources = {}
        for field, ev in self.obj["evidence_map"].items():
            path, sha = ev["path"], ev["sha256"]
            self.assertEqual(impl.sha256_file(pathlib.Path(path)), sha,
                             f"{field}: source drifted")
            if path not in sources:
                sources[path] = pathlib.Path(path).read_text(encoding="utf-8")
            self.assertIn(impl.norm(ev["quote"]), impl.norm(sources[path]),
                          f"{field}: quote does not reproduce")

    # ---- F2 invention scan
    def test_no_invented_elements(self):
        text = json.dumps(self.obj).lower()
        banned = ("mission", "quest", "level-up", "campaign structure",
                  "score threshold", "achievement", "leaderboard")
        for word in banned:
            self.assertIsNone(re.search(r"\b%s\b" % re.escape(word), text),
                              f"invented element {word!r} found")

    # ---- F3 archived envelope non-promotion
    def test_archived_envelope_not_promoted(self):
        content = json.dumps(self.obj["selected_definition"]).lower()
        for token in ("20.0 m", "11.976783", "2.471766"):
            self.assertNotIn(token, content,
                             f"archived envelope token {token!r} promoted")
        inv = {u["id"]: u for u in self.obj["unresolved_inventory"]}
        for needed in ("mat2-f01-spatial-envelope",
                       "mat2-p06-acceptance-limits",
                       "mat2-x02-session-flow"):
            self.assertIn(needed, inv)
        self.assertFalse(
            inv["mat2-f01-spatial-envelope"]["archived_envelope_numbers_promoted"])
        self.assertEqual(inv["mat2-f01-spatial-envelope"]["owner_card"], "MAT2-F01")
        self.assertEqual(inv["mat2-p06-acceptance-limits"]["owner_card"], "MAT2-P06")
        self.assertEqual(inv["mat2-x02-session-flow"]["owner_card"], "MAT2-X02")

    # ---- F4 single decision request, carried with provenance
    def test_exactly_one_decision_request(self):
        reqs = self.obj["operator_decision_requests"]
        self.assertEqual(len(reqs), 1)
        self.assertEqual(reqs[0]["id"], "objective-presentation-surface")
        self.assertEqual(len(reqs[0]["options"]), 3)
        self.assertIn("PR #136", reqs[0]["provenance"])

    # ---- F6 identity completeness
    def test_records_identities_full_hash(self):
        for key, val in self.obj["records"].items():
            if key.endswith("_sha256"):
                self.assertRegex(val, r"^[0-9a-f]{64}$", key)
        for field, ev in self.obj["evidence_map"].items():
            self.assertRegex(ev["sha256"], r"^[0-9a-f]{64}$", field)

    # ---- definition content laws
    def test_framing_recovered_not_invented(self):
        self.assertEqual(self.obj["selected_definition"]["framing"]["choice"],
                         "complete game (not movement demo)")
        self.assertIn("complete player flow",
                      self.obj["selected_definition"]["framing"]["recovered_from"])

    def test_loop_clause_is_current_k08_verbatim(self):
        clause = (self.obj["selected_definition"]
                        ["repeatable_objective"]
                        ["success_loop_clause_current_verbatim"])
        self.assertIn("resumes all-fours walking in one session", clause)
        self.assertIn("releases", clause)

    def test_milestone_order_is_material_first_verbatim(self):
        clause = (self.obj["selected_definition"]
                        ["repeatable_objective"]
                        ["milestone_order_material_first_verbatim"])
        contract = json.loads(impl.CONTRACT.read_text(encoding="utf-8"))
        self.assertEqual(clause, contract["material_first_addition"]["text"])

    def test_legacy_promotion_claim_is_none(self):
        xw = self.obj["legacy_crosswalk"]
        self.assertEqual(xw["promotion_claim"], "NONE -- archived DONE is not new acceptance")
        self.assertTrue(xw["not_carried"])
        self.assertEqual(xw["provenance"]["pr_head_sha"],
                         "0c9a615cceccf7f7269b9545f555bd2be8daa138")

    # ---- F1 tamper refusal (loud, no artifact)
    def test_extraction_fails_loudly_on_tampered_contract(self):
        original = impl.CONTRACT.read_bytes()
        try:
            path = HERE / "tampered_contract.json"
            bad = json.loads(original.decode("utf-8"))
            bad["identities"]["active_scope_sha256"] = "0" * 64
            path.write_text(json.dumps(bad), encoding="utf-8")
            real = impl.CONTRACT
            impl.CONTRACT = path
            with self.assertRaises(impl.ExtractionFailure):
                impl.extract()
        finally:
            impl.CONTRACT = real
            (HERE / "tampered_contract.json").unlink(missing_ok=True)
            self.assertEqual(impl.CONTRACT.read_bytes(), original)

    def test_extraction_fails_loudly_on_drifted_source(self):
        original = impl.MONKEY_RUN_SHA256
        try:
            impl.MONKEY_RUN_SHA256 = "f" * 64
            with self.assertRaises(impl.ExtractionFailure):
                impl.extract()
        finally:
            impl.MONKEY_RUN_SHA256 = original


if __name__ == "__main__":
    unittest.main(verbosity=2)
