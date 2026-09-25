#!/usr/bin/env python3
"""Repair tests for I-GOV-PR-HANDOFF-REPAIR against the PATCHED kanban.py.

Every scenario runs in its own isolated temporary registry. CPU-only, no
network, no credentials, no production registry. Bounded well under 120 s.
"""
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "reference"))  # agent_slots + integrity deps

_spec = importlib.util.spec_from_file_location(
    "kanban_patched", HERE / "patched" / "kanban.py")
kanban = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(kanban)

from agent_slots import Registry  # noqa: E402

SPECS = [
    {"id": f"T{i}", "objective": f"o{i}", "falsifier": f"f{i}", "steps": [f"s{i}"],
     "completion": f"c{i}", "depends_on": []} for i in range(3)
]
W = "worker-test"
OTHER = "worker-two"
PR = "https://github.com/GhostDragonAlpha/Chimera/pull/9"


class Isolated(unittest.TestCase):
    def make_registry(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        registry = Registry(Path(tmp.name))
        registry.initialize()
        kanban.initialize(registry, SPECS, actor=kanban.LEAD)
        return registry

    @staticmethod
    def request_args(alloc, head="b" * 40, criteria=None):
        return {"agent_id": alloc["attempt"]["agent_id"] if "attempt" in alloc else W,
                "task_id": alloc["task_id"], "attempt_id": alloc["attempt"]["id"],
                "criteria_sha256": criteria or alloc["attempt"]["criteria_sha256"],
                "head_sha": head, "branch": "branch-1", "checkpoint": "candidate at "
                + head[:8] + " with artifacts", "writes_stopped": True,
                "artifacts": [{"path": "x.py", "sha256": "0" * 64}]}

    @staticmethod
    def submit_args(alloc, url=PR, head="a" * 40):
        return {"agent_id": W, "task_id": alloc["task_id"],
                "attempt_id": alloc["attempt"]["id"],
                "criteria_sha256": alloc["attempt"]["criteria_sha256"],
                "pr_url": url, "head_sha": head}

    @staticmethod
    def card(registry, task_id):
        return registry.readonly()["kanban"]["cards"][task_id]


class ExplicitRouting(Isolated):
    def test_review_regression_explicit_return(self):
        """PR#116 finding 1: submit T0 -> T1 -> revisit T0 -> explicit T1 returns T1."""
        registry = self.make_registry()
        t0 = kanban.join(registry, W)
        self.assertEqual(t0["task_id"], "T0")
        kanban.submit(registry, self.submit_args(t0))
        t1 = kanban.join(registry, W)
        self.assertEqual(t1["task_id"], "T1")
        revisit = kanban.join(registry, W, "T0")
        self.assertEqual((revisit["state"], revisit["task_id"]),
                         ("RESUME_ATTEMPT", "T0"))
        working = [(tid, a["state"]) for tid in ("T0", "T1", "T2")
                   for a in self.card(registry, tid)["attempts"].values()
                   if a["agent_id"] == W and a["state"] == "WORKING"]
        self.assertEqual(working, [("T0", "WORKING")],
                         "explicit revisit must displace the other WORKING attempt")
        t1_again = kanban.join(registry, W, "T1")
        self.assertEqual((t1_again["state"], t1_again["task_id"]),
                         ("RESUME_ATTEMPT", "T1"),
                         "explicit request for T1 must return T1, not T0")
        self.assertEqual(t1_again["attempt"]["id"], t1["attempt"]["id"])
        resumed = self.card(registry, "T1")["attempts"][t1["attempt"]["id"]]
        self.assertEqual(resumed["state"], "WORKING")
        displaced = self.card(registry, "T0")["attempts"][t0["attempt"]["id"]]
        self.assertEqual(displaced["state"], "PAUSED")
        self.assertIn("auto_displaced_by_explicit_task_selection",
                      displaced["checkpoint"])

    def test_displacement_never_touches_other_workers(self):
        registry = self.make_registry()
        w1 = kanban.join(registry, W)
        w2 = kanban.join(registry, OTHER)
        self.assertEqual((w1["task_id"], w2["task_id"]), ("T0", "T1"))
        kanban.join(registry, W, "T2")  # W1 explicitly moves; T0 displaced
        self.assertEqual(
            self.card(registry, "T1")["attempts"][w2["attempt"]["id"]]["state"],
            "WORKING", "another worker's attempt must never be displaced")
        self.assertEqual(
            self.card(registry, "T0")["attempts"][w1["attempt"]["id"]]["state"],
            "PAUSED")

    def test_generic_resume_still_works(self):
        registry = self.make_registry()
        first = kanban.join(registry, W)
        again = kanban.join(registry, W)
        self.assertEqual((again["state"], again["task_id"], again["attempt"]["id"]),
                         ("RESUME_ATTEMPT", first["task_id"], first["attempt"]["id"]))

    def test_explicit_new_card_switch_displaces_own_working(self):
        """Explicit selection of a card with no own attempt must assign THAT card,
        checkpoint-parking the worker's own WORKING attempt (never another's)."""
        registry = self.make_registry()
        t0 = kanban.join(registry, W)
        other = kanban.join(registry, OTHER)
        self.assertEqual((t0["task_id"], other["task_id"]), ("T0", "T1"))
        switch = kanban.join(registry, W, "T2")
        self.assertEqual((switch["state"], switch["task_id"]), ("ASSIGNED", "T2"))
        self.assertNotEqual(switch["attempt"]["id"], t0["attempt"]["id"])
        self.assertEqual(
            self.card(registry, "T0")["attempts"][t0["attempt"]["id"]]["state"],
            "PAUSED")
        self.assertIn("auto_displaced_by_explicit_task_selection",
                      self.card(registry, "T0")["attempts"][t0["attempt"]["id"]]["checkpoint"])
        self.assertEqual(
            self.card(registry, "T1")["attempts"][other["attempt"]["id"]]["state"],
            "WORKING")


class PublicationRequest(Isolated):
    def test_request_moves_worker_to_next_card_without_credentials(self):
        """PR#116 finding 2: a request must transition the worker, not trap them."""
        registry = self.make_registry()
        t0 = kanban.join(registry, W)
        result = kanban.request_publication(registry, self.request_args(t0))
        self.assertEqual(result["state"], "PUBLICATION_REQUESTED")
        attempt = self.card(registry, "T0")["attempts"][t0["attempt"]["id"]]
        self.assertEqual(attempt["state"], "PUBLICATION_REQUESTED")
        nxt = kanban.join(registry, W)  # generic poll; no credentials involved
        self.assertNotEqual(nxt.get("task_id"), "T0",
                            "requesting worker must not be trapped on T0")
        self.assertEqual(nxt["state"], "ASSIGNED")

    def test_request_is_never_submission_or_merge(self):
        registry = self.make_registry()
        t0 = kanban.join(registry, W)
        kanban.post(registry, {"task_id": "T0", "author": kanban.LEAD,
                               "body": "lead correction still open"})
        kanban.request_publication(registry, self.request_args(t0))
        card = self.card(registry, "T0")
        self.assertNotIn(card["state"], ("REVIEW", "DONE"))
        self.assertEqual(card["prs"], {})
        self.assertNotIn(card["winner"], (True,))
        self.assertTrue(all(m["status"] == "OPEN" for m in card["messages"]),
                        "request must not resolve inbox messages")
        self.assertEqual(card["state"], "OPEN")

    def test_request_identity_refusals(self):
        registry = self.make_registry()
        t0 = kanban.join(registry, W)
        stale = self.request_args(t0, criteria="f" * 64)
        with self.assertRaises(ValueError) as ctx:
            kanban.request_publication(registry, stale)
        self.assertEqual(str(ctx.exception), "criteria_changed")
        short_head = self.request_args(t0, head="abc")
        with self.assertRaises(ValueError) as ctx:
            kanban.request_publication(registry, short_head)
        self.assertEqual(str(ctx.exception), "full_request_head_required")
        wrong_owner = self.request_args(t0)
        wrong_owner["agent_id"] = OTHER
        with self.assertRaises(ValueError) as ctx:
            kanban.request_publication(registry, wrong_owner)
        self.assertEqual(str(ctx.exception), "wrong_attempt_owner")
        no_checkpoint = self.request_args(t0)
        no_checkpoint["writes_stopped"] = False
        with self.assertRaises(ValueError) as ctx:
            kanban.request_publication(registry, no_checkpoint)
        self.assertEqual(str(ctx.exception),
                         "request_checkpoint_and_stopped_writes_required")

    def test_request_idempotent_and_retry_preserves_records(self):
        registry = self.make_registry()
        t0 = kanban.join(registry, W)
        args = self.request_args(t0)
        first = kanban.request_publication(registry, args)
        second = kanban.request_publication(registry, dict(args))
        self.assertEqual(first["request_id"], second["request_id"])
        self.assertEqual(second["state"], "REQUEST_ALREADY_RECORDED")
        requests = self.card(registry, "T0")["publication_requests"]
        self.assertEqual(len(requests), 1, "identical retries create no duplicates")
        # A new head supersedes the old request but preserves it.
        new_args = self.request_args(t0, head="c" * 40)
        third = kanban.request_publication(registry, new_args)
        self.assertNotEqual(third["request_id"], first["request_id"])
        requests = self.card(registry, "T0")["publication_requests"]
        self.assertEqual(len(requests), 2)
        self.assertEqual(requests[first["request_id"]]["status"], "SUPERSEDED")
        self.assertEqual(requests[first["request_id"]]["superseded_by"],
                         third["request_id"])

    def test_worker_can_explicitly_revisit_requested_card(self):
        registry = self.make_registry()
        t0 = kanban.join(registry, W)
        result = kanban.request_publication(registry, self.request_args(t0))
        back = kanban.join(registry, W, "T0")
        self.assertEqual((back["state"], back["task_id"]), ("RESUME_ATTEMPT", "T0"))
        attempt = self.card(registry, "T0")["attempts"][t0["attempt"]["id"]]
        self.assertEqual(attempt["state"], "WORKING")
        self.assertEqual(
            self.card(registry, "T0")["publication_requests"][
                result["request_id"]]["status"], "OPEN",
            "corrections path must preserve the outstanding request record")


class LeadFulfilment(Isolated):
    def test_fulfil_records_pr_and_is_idempotent(self):
        registry = self.make_registry()
        t0 = kanban.join(registry, W)
        req = kanban.request_publication(registry, self.request_args(t0))
        fulfil = kanban.fulfil_publication(registry, {
            "actor": kanban.LEAD, "agent_id": W, "task_id": "T0",
            "attempt_id": t0["attempt"]["id"], "request_id": req["request_id"],
            "pr_url": PR, "head_sha": "b" * 40})
        self.assertEqual(fulfil["state"], "FULFILLED")
        card = self.card(registry, "T0")
        self.assertEqual(card["state"], "REVIEW")
        self.assertIn(PR, card["prs"])
        self.assertEqual(card["prs"][PR]["fulfilled_request"], req["request_id"])
        self.assertEqual(
            card["attempts"][t0["attempt"]["id"]]["state"], "PR_SUBMITTED")
        self.assertEqual(
            card["publication_requests"][req["request_id"]]["status"], "FULFILLED")
        again = kanban.fulfil_publication(registry, {
            "actor": kanban.LEAD, "agent_id": W, "task_id": "T0",
            "attempt_id": t0["attempt"]["id"], "request_id": req["request_id"],
            "pr_url": PR, "head_sha": "b" * 40})
        self.assertEqual(again["state"], "ALREADY_FULFILLED")
        self.assertEqual(len(self.card(registry, "T0")["prs"]), 1)

    def test_fulfil_refusals(self):
        registry = self.make_registry()
        t0 = kanban.join(registry, W)
        req = kanban.request_publication(registry, self.request_args(t0))
        base = {"actor": kanban.LEAD, "agent_id": W, "task_id": "T0",
                "attempt_id": t0["attempt"]["id"],
                "request_id": req["request_id"], "pr_url": PR}
        with self.assertRaises(ValueError) as ctx:
            kanban.fulfil_publication(registry, {**base, "head_sha": "d" * 40})
        self.assertEqual(str(ctx.exception), "request_head_changed")
        with self.assertRaises(ValueError) as ctx:
            kanban.fulfil_publication(registry,
                                      {**base, "head_sha": "b" * 40,
                                       "actor": "not-the-lead"})
        self.assertEqual(str(ctx.exception), "lead_action_required")
        with self.assertRaises(ValueError) as ctx:
            kanban.fulfil_publication(registry,
                                      {**base, "head_sha": "b" * 40,
                                       "request_id": "pub-nonexistent"})
        self.assertEqual(str(ctx.exception), "unknown_publication_request")

    def test_worker_submission_still_works(self):
        registry = self.make_registry()
        t0 = kanban.join(registry, W)
        result = kanban.submit(registry, self.submit_args(t0))
        self.assertEqual(result["state"], "PR_RECORDED")
        repeat = kanban.submit(registry, self.submit_args(t0))
        self.assertEqual(repeat["state"], "PR_ALREADY_RECORDED")
        card = self.card(registry, "T0")
        self.assertEqual(card["state"], "REVIEW")
        self.assertEqual(
            card["attempts"][t0["attempt"]["id"]]["state"], "PR_SUBMITTED")


class BoardInvariants(Isolated):
    def test_capacity_and_criteria_unchanged(self):
        registry = self.make_registry()
        before = kanban.read(registry)
        t0 = kanban.join(registry, W)
        req = kanban.request_publication(registry, self.request_args(t0))
        kanban.fulfil_publication(registry, {
            "actor": kanban.LEAD, "agent_id": W, "task_id": "T0",
            "attempt_id": t0["attempt"]["id"], "request_id": req["request_id"],
            "pr_url": PR, "head_sha": "b" * 40})
        after = kanban.read(registry)
        self.assertEqual(after["capacity"], before["capacity"])
        self.assertEqual(after["capacity"], 10)
        for card in after["cards"]:
            self.assertEqual(card["id"] in {c["id"] for c in before["cards"]}, True)
        criteria_before = {c["id"]: self.card(registry, c["id"])["criteria_sha256"]
                           for c in before["cards"]}
        for card in after["cards"]:
            self.assertEqual(self.card(registry, card["id"])["criteria_sha256"],
                             criteria_before[card["id"]],
                             "criteria hashes must never change")

    def test_review_and_merge_path_still_enforced(self):
        """A fulfilled request follows the normal path: merge still requires an
        ACCEPTED lead review of the exact head — no masquerade shortcut."""
        registry = self.make_registry()
        t0 = kanban.join(registry, W)
        req = kanban.request_publication(registry, self.request_args(t0))
        kanban.fulfil_publication(registry, {
            "actor": kanban.LEAD, "agent_id": W, "task_id": "T0",
            "attempt_id": t0["attempt"]["id"], "request_id": req["request_id"],
            "pr_url": PR, "head_sha": "b" * 40})
        card = self.card(registry, "T0")
        self.assertEqual(card["state"], "REVIEW")  # not DONE: request is not a merge
        with self.assertRaises(ValueError) as ctx:
            kanban.accept_merge(registry, {
                "actor": kanban.LEAD, "task_id": "T0", "pr_url": PR,
                "head_sha": "b" * 40},
                {"merged": True, "html_url": PR, "base": {"ref": kanban.BASE},
                 "head": {"sha": "b" * 40}, "merge_commit_sha": "e" * 40})
        self.assertEqual(str(ctx.exception), "merged_head_not_approved")


if __name__ == "__main__":
    unittest.main(verbosity=2)
