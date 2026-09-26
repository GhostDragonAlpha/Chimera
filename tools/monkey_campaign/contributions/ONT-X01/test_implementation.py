"""test_implementation.py -- ONT-X01 extraction tests.

Laws: the quoted clauses reproduce from the frozen records; the objective
contains no invented elements (no missions/score thresholds/campaign
structure); exactly one decision request; identities pinned.
"""
import json
import pathlib
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import implementation as impl  # noqa: E402


class ObjectiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.obj = impl.extract()

    def test_loop_is_k08_verbatim(self):
        self.assertIn("resumes all-fours walking in one session",
                      self.obj["repeatable_objective"]
                      ["success_clause_k08_verbatim"])

    def test_no_invented_elements(self):
        import re
        text = json.dumps(self.obj).lower()
        banned = ("mission", "quest", "level-up", "campaign structure",
                  "score threshold", "achievement", "leaderboard")
        for word in banned:
            self.assertIsNone(
                re.search(r"\b%s\b" % re.escape(word), text),
                f"invented element {word!r} found")

    def test_exactly_one_decision_request(self):
        reqs = self.obj["operator_decision_requests"]
        self.assertEqual(len(reqs), 1)
        self.assertEqual(reqs[0]["id"], "objective-presentation-surface")
        self.assertEqual(len(reqs[0]["options"]), 3)

    def test_framing_recovered_not_invented(self):
        self.assertEqual(self.obj["framing"]["choice"], "complete game (not "
                                                        "movement demo)")
        self.assertIn("complete player flow",
                      self.obj["framing"]["recovered_from"])

    def test_identities_pinned(self):
        self.assertEqual(self.obj["records"]["scope_sha256"], impl.SCOPE_SHA)
        self.assertEqual(self.obj["records"]["contract_version"], "1.0.0")
        self.assertEqual(len(self.obj["records"]["contract_sha256"]), 64)

    def test_extraction_fails_loudly_on_tampered_contract(self):
        tampered = pathlib.Path(impl.CONTRACT)
        original = tampered.read_bytes()
        try:
            path = pathlib.Path(HERE / "tampered_contract.json")
            bad = json.loads(original.decode("utf-8"))
            bad["identities"]["scope_sha256"] = "0" * 64
            path.write_text(json.dumps(bad), encoding="utf-8")
            real = impl.CONTRACT
            impl.CONTRACT = path
            with self.assertRaises(impl.ExtractionFailure):
                impl.extract()
        finally:
            impl.CONTRACT = real
            (HERE / "tampered_contract.json").unlink(missing_ok=True)
            self.assertEqual(tampered.read_bytes(), original)


if __name__ == "__main__":
    unittest.main(verbosity=2)
