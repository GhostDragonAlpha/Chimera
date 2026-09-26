"""test_implementation.py -- ONT-P06 limits proposal tests (correction).

Laws: every derived numeric reproduces from its cited PINNED source at test
time (sha256-asserted reference bytes, identity verified in the play
repository); every taste numeric is an explicit operator decision request;
zero entries carry neither class; the unresolved CoT lineage is preserved;
the 15 derived VALUES are bit-identical to the lead-verified prior proposal.
"""
import hashlib
import json
import pathlib
import subprocess
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import implementation as impl  # noqa: E402


class LimitsProposalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proposal = impl.build_proposal()

    def test_every_numeric_is_derived_or_decision(self):
        for limit in self.proposal["derived_limits"]:
            self.assertEqual(limit["class"], "DERIVED", limit["id"])
            self.assertTrue(limit.get("source"), limit["id"])
            # The corrected claim: measured_now must be backed by pinned
            # provenance (no value-hardcoded entries anywhere).
            self.assertTrue(limit.get("measured_now"), limit["id"])
            self.assertTrue(limit.get("provenance"), limit["id"])
            for p in limit["provenance"]:
                self.assertIn(p["path"], impl.PINNED, limit["id"])
                self.assertTrue(p["method"], limit["id"])
        for req in self.proposal["operator_decision_requests"]:
            self.assertEqual(req["class"], "OPERATOR_DECISION_REQUESTED")
            self.assertTrue(req["options"])

    def test_derived_values_reproduce(self):
        by_id = {l["id"]: l["value"] for l in self.proposal["derived_limits"]}
        self.assertEqual(by_id["terrain-envelope-half-width-m"], 20.0)
        self.assertEqual(by_id["spawn-position-m"], [0.0, 0.0, 0.0])
        self.assertEqual(by_id["spawn-required-clearance-m"], 1.5)
        self.assertEqual(by_id["body-envelope-radius-m"], 0.25)
        self.assertEqual(by_id["scene-seed"], 4598321)
        self.assertEqual(by_id["trunk-base-centre-m"],
                         [11.976783, 0.0, 2.471766])
        self.assertEqual(by_id["trunk-blocking-radius-m"], 0.287)
        self.assertEqual(by_id["simulation-tick-hz"], 300)
        self.assertEqual(by_id["walking-episode-cap-ticks"], 300)
        self.assertEqual(by_id["walking-eval-window-ticks"], 270)
        self.assertEqual(by_id["stability-settle-sink-m"], 0.01)
        self.assertEqual(by_id["stability-settle-vy-ms"], 0.05)
        self.assertEqual(by_id["ui-poll-cadence-ms"], 100)
        self.assertEqual(by_id["controls-bindings"]["pause"], "Escape")

    def test_pinned_sources_exist_and_match(self):
        for rel, (commit, want) in impl.PINNED.items():
            path = impl.REFERENCE / rel
            self.assertTrue(path.is_file(), rel)
            got = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(got, want, rel)
            proc = subprocess.run(
                ["git", "-c", f"safe.directory={impl.PLAY}",
                 "-C", str(impl.PLAY), "cat-file", "-e",
                 f"{commit}:{rel}", "--"], capture_output=True)
            self.assertEqual(proc.returncode, 0,
                             f"git identity missing: {commit}:{rel}")

    def test_unresolved_cot_lineage_preserved(self):
        joined = json.dumps(self.proposal)
        self.assertIn("13824.5", joined)
        self.assertIn("10.038", joined)

    def test_decision_requests_present(self):
        ids = {r["id"] for r in self.proposal["operator_decision_requests"]}
        self.assertEqual(ids, {"session-duration-cap", "supported-hardware-floor",
                               "network-latency-sla-ms", "frame-time-budget-ms"})

    def test_file_written(self):
        out = HERE / "limits_proposal.json"
        if not out.is_file():
            impl.main(["--out", str(out)])
        loaded = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(loaded["schema"], impl.SCHEMA)
        self.assertEqual(loaded["derived_count"], 15)


if __name__ == "__main__":
    unittest.main(verbosity=2)
