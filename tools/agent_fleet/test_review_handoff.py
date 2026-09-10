"""Ephemeral SQLite/HTTP tests for review-preserving slot handoff."""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request


HERE = Path(__file__).resolve().parent
CONTROL_ROOT = Path(os.environ["FLEET_CONTROL_ROOT"]) if "FLEET_CONTROL_ROOT" in os.environ else HERE
sys.path.insert(0, str(HERE)); sys.path.insert(1, str(CONTROL_ROOT))
from control import Refusal
from review_handoff import ReviewHandoffControl
from service import Server

BASE = "a" * 40
HEAD = "b" * 40
MERGED = "c" * 40


class ReviewHandoffTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
        self.c = ReviewHandoffControl(self.root / "state.sqlite", "supervisor-secret",
                                      "enroll-secret", self.root / "slots")
        self.tokens = {}
        for aid in ("lead", "worker", "replacement", "other"):
            self.tokens[aid] = self.c.call("enroll", "enroll-secret", agent=aid,
                                           label=aid)["result"]["session_token"]
            self.c.call("qualify", "supervisor-secret", agent=aid,
                        capabilities=["cpu", "gpu"], max_tasks=2,
                        can_lead=aid == "lead", rank=10 if aid == "lead" else 1,
                        evidence="ephemeral qualification")
        self.c.call("offer_lead", self.tokens["lead"], epoch=0,
                    checkpoint="ephemeral leader ready")
        self.c.call("elect", "supervisor-secret")

    def tearDown(self): self.temp.cleanup()

    def call(self, op, actor="lead", **p):
        return self.c.call(op, self.tokens.get(actor, actor), **p)["result"]

    def snap(self): return self.call("snapshot")

    def create(self, task, scopes=None):
        return self.call("create_task", task=task, epoch=self.snap()["epoch"], base=BASE,
                         scopes=scopes or [f"tools/work/{task}"],
                         packet="statement / prediction / falsifier", kind="worker")

    def claim(self, task, actor="worker"): return self.call("claim", actor, task=task)

    def review(self, task="reviewed", actor="worker"):
        self.create(task); claimed = self.claim(task, actor)
        self.call("checkpoint", actor, task=task, generation=claimed["generation"],
                  checkpoint="checkpoint retained")
        self.call("provision_slot", "supervisor-secret", task=task,
                  worktree_head=BASE, evidence="ephemeral provision receipt")
        self.call("submit_review", actor, task=task, generation=claimed["generation"],
                  branch=claimed["branch"], head=HEAD, evidence="exact review evidence")
        return claimed

    def release_args(self, task="reviewed"):
        t = self.snap()["tasks"][task]
        return dict(task=task, owner=t["owner"], generation=t["generation"],
                    slot=t["slot"], head=t["head"], pushed_head=t["head"],
                    pr_head=t["head"], pr_identity="PR draft #fixture",
                    remote_verification_evidence="supervisor broker verified remote and PR heads",
                    preservation_evidence="commit, PR, and review evidence retained",
                    writer_stopped_evidence="human confirmed owning writer stopped",
                    runtime_drained_evidence="owned runtime/process handles absent",
                    slot_reprovision_ready_evidence="slot worktree drained for reprovision")

    def handoff(self, task="reviewed"):
        return self.call("release_review_slot", "supervisor-secret", **self.release_args(task))

    def test_handoff_preserves_review_and_agent_but_frees_execution_capacity(self):
        reviewed = self.review()
        self.create("survivor"); survivor = self.claim("survivor")
        before = self.snap(); frozen = copy.deepcopy(before["tasks"]["reviewed"])
        self.handoff(); after = self.snap(); detached = after["tasks"]["reviewed"]
        for key in ("state", "owner", "generation", "head", "review", "checkpoint",
                    "branch", "integration"):
            self.assertEqual(detached[key], frozen[key], key)
        self.assertIsNone(detached["slot"])
        self.assertEqual(after["agents"], before["agents"])
        self.assertEqual(after["leader"], before["leader"])
        self.assertEqual(after["epoch"], before["epoch"])
        self.assertEqual(after["resources"], before["resources"])
        self.assertEqual(after["tasks"]["survivor"], before["tasks"]["survivor"])
        released_slot = after["slots"][reviewed["slot"]]
        self.assertIsNone(released_slot["task"])
        self.assertFalse(released_slot["engine"]["provisioned"])
        self.assertNotIn("worktree_head", released_slot["engine"])

        # max_tasks=2: survivor executes; detached review consumes no execution slot.
        self.create("new-work"); new_claim = self.claim("new-work")
        self.assertEqual(new_claim["slot"], reviewed["slot"])
        # Yet REVIEW remains a scope barrier.
        self.create("overlap", scopes=["tools/work/reviewed/subpath"])
        with self.assertRaisesRegex(Refusal, "write_scope_conflict"):
            self.claim("overlap", "other")

    def test_two_detached_reviews_do_not_exhaust_execution_capacity(self):
        self.review("review-one"); self.handoff("review-one")
        self.review("review-two"); self.handoff("review-two")
        self.create("executable")
        claimed = self.claim("executable")
        self.assertEqual(claimed["state"], "RUNNING")
        self.assertEqual(claimed["owner"], "worker")

    def test_slotless_review_integrates_and_post_ack_release_is_idempotent(self):
        t = self.review(); request = self.call(
            "integration_request", task="reviewed", head=HEAD, branch=t["branch"],
            expected_base=BASE, epoch=self.snap()["epoch"], review="independent review")
        before_request = copy.deepcopy(self.snap()["requests"][request["request"]])
        self.handoff()
        self.assertEqual(self.snap()["requests"][request["request"]], before_request)
        ack = self.call("ack_integration", "supervisor-secret", request=request["request"],
                        base_branch="astra/gait-capture", expected_base=BASE, commit=MERGED,
                        evidence="publisher verified remote head")
        self.assertIsNone(ack["slot"])
        self.assertEqual(ack["slot_status"], "RELEASED_AT_REVIEW_HANDOFF")
        result = self.call("release_slot", "supervisor-secret", task="reviewed",
                           evidence="already drained at PR handoff")
        self.assertTrue(result["already_released_for_review"])
        self.assertEqual(self.snap()["tasks"]["reviewed"]["state"], "INTEGRATED")

    def test_slotted_integration_ack_keeps_base_response(self):
        task = self.review()
        request = self.call(
            "integration_request", task="reviewed", head=HEAD, branch=task["branch"],
            expected_base=BASE, epoch=self.snap()["epoch"], review="independent review")
        ack = self.call("ack_integration", "supervisor-secret", request=request["request"],
                        base_branch="astra/gait-capture", expected_base=BASE, commit=MERGED,
                        evidence="publisher verified remote head")
        self.assertEqual(ack["slot"], "held until cleanup attestation")
        self.assertNotIn("slot_status", ack)

    def test_correction_requeues_ready_then_replacement_claims_once_and_provisions_exact_head(self):
        initial = self.review(); self.handoff()
        request = self.call(
            "integration_request", task="reviewed", head=HEAD, branch=initial["branch"],
            expected_base=BASE, epoch=self.snap()["epoch"], review="review pending")
        result = self.call("review_requeue", task="reviewed", epoch=self.snap()["epoch"],
                           head=HEAD, evidence="review requested correction")
        self.assertEqual(result["state"], "READY")
        ready = self.snap()["tasks"]["reviewed"]
        self.assertEqual(ready["generation"], initial["generation"])
        self.assertIsNone(ready["owner"]); self.assertIsNone(ready["slot"])
        self.assertIsNone(ready["head"]); self.assertEqual(ready["correction_base_head"], HEAD)
        self.assertEqual(ready["review_correction_history"][-1]["head"], HEAD)
        self.assertEqual(self.snap()["requests"][request["request"]]["state"],
                         "CANCELLED_REQUEUED")

        claimed = self.claim("reviewed", "replacement")
        self.assertEqual(claimed["generation"], initial["generation"] + 1)
        self.assertEqual(claimed["owner"], "replacement")
        self.call("checkpoint", "replacement", task="reviewed",
                  generation=claimed["generation"],
                  checkpoint="materialization preparation recorded")
        blocked = [
            ("submit_review", dict(task="reviewed", generation=claimed["generation"],
                                   branch=claimed["branch"], head=MERGED,
                                   evidence="must wait for provision")),
            ("resource_acquire", dict(task="reviewed", generation=claimed["generation"],
                                      resource="rtx4090")),
            ("resource_request", dict(task="reviewed", generation=claimed["generation"],
                                      wants=[{"name": "rtx4090"}], priority=1)),
        ]
        for operation, arguments in blocked:
            before = self.snap()
            with self.assertRaisesRegex(Refusal, "correction_provision_required"):
                self.call(operation, "replacement", **arguments)
            self.assertEqual(self.snap(), before)
        with self.assertRaisesRegex(Refusal, "stale_or_foreign_claim"):
            self.call("resource_request", "other", task="reviewed",
                      generation=claimed["generation"], wants=[{"name": "rtx4090"}],
                      priority=1)
        revision = self.snap()["revision"]
        with self.assertRaisesRegex(Refusal, "correction_worktree_head_mismatch"):
            self.call("provision_slot", "supervisor-secret", task="reviewed",
                      worktree_head=MERGED, evidence="wrong materialized head")
        self.assertEqual(self.snap()["revision"], revision)
        self.call("provision_slot", "supervisor-secret", task="reviewed",
                  worktree_head=HEAD, evidence="review head materialized and verified")
        corrected = self.snap()["tasks"]["reviewed"]
        self.assertNotIn("correction_base_head", corrected)
        self.assertEqual(corrected["correction_provisioned_head"], HEAD)
        request = self.call("resource_request", "replacement", task="reviewed",
                            generation=claimed["generation"],
                            wants=[{"name": "rtx4090"}], priority=1)
        self.assertTrue(request["granted"])
        self.call("resource_release", "replacement", task="reviewed",
                  generation=claimed["generation"], resource="rtx4090",
                  evidence="ephemeral GPU handle absent")
        self.call("submit_review", "replacement", task="reviewed",
                  generation=claimed["generation"], branch=claimed["branch"],
                  head=MERGED, evidence="corrected review after exact provision")

    def test_requeue_does_not_need_free_slot_but_following_claim_does(self):
        self.review(); self.handoff()
        # Occupy all four worker slots after the detached review freed one.
        for index, actor in enumerate(("worker", "replacement", "other", "other")):
            task = f"fill-{index}"; self.create(task); self.claim(task, actor)
        self.call("review_requeue", task="reviewed", epoch=self.snap()["epoch"],
                  head=HEAD, evidence="correction requested while fleet full")
        before = self.snap()
        with self.assertRaisesRegex(Refusal, "no_free_slot"):
            self.claim("reviewed", "replacement")
        self.assertEqual(self.snap(), before)

    def test_auth_identity_drain_and_resource_refusals_rollback(self):
        t = self.review(); valid = self.release_args()
        attempts = [
            ("worker", valid),
            ("supervisor-secret", {**valid, "owner": "other"}),
            ("supervisor-secret", {**valid, "generation": t["generation"] + 1}),
            ("supervisor-secret", {**valid, "slot": "5"}),
            ("supervisor-secret", {**valid, "pr_head": MERGED}),
            ("supervisor-secret", {**valid, "writer_stopped_evidence": ""}),
            ("supervisor-secret", {**valid, "runtime_drained_evidence": ""}),
        ]
        for actor, args in attempts:
            before = self.snap()
            with self.assertRaises(Refusal): self.call("release_review_slot", actor, **args)
            self.assertEqual(self.snap(), before)

        self.handoff()
        before = self.snap()
        with self.assertRaisesRegex(Refusal, "stale_slot"):
            self.call("release_review_slot", "supervisor-secret", **valid)
        self.assertEqual(self.snap(), before)

        # A REVIEW cannot normally acquire; inject a real hold through the normal
        # path before review in a fresh task and confirm submit itself refuses.
        self.create("held"); held = self.claim("held", "other")
        self.call("resource_acquire", "other", task="held", generation=held["generation"],
                  resource="rtx4090")
        with self.assertRaisesRegex(Refusal, "release_resources_before_review"):
            self.call("submit_review", "other", task="held", generation=held["generation"],
                      branch=held["branch"], head=HEAD, evidence="cannot freeze held resource")

    def test_handoff_refuses_a_preexisting_actual_hold(self):
        self.review()
        con = self.c.connect()
        try:
            con.execute("BEGIN IMMEDIATE")
            state = json.loads(con.execute("SELECT body FROM state WHERE id=1").fetchone()[0])
            state["resources"]["rtx4090"] = {
                "task": "reviewed", "owner": "worker", "generation": 1,
                "class": "gpu_functionality", "since_revision": state["revision"],
                "memory_mb": None,
            }
            con.execute("UPDATE state SET body=? WHERE id=1", (json.dumps(state),))
            con.execute("COMMIT")
        finally:
            con.close()
        before = self.snap()
        with self.assertRaisesRegex(Refusal, "resources_still_held"):
            self.handoff()
        self.assertEqual(self.snap(), before)

    def test_failed_owner_of_detached_review_uses_slotless_recovery(self):
        initial = self.review(); self.handoff()
        request = self.call(
            "integration_request", task="reviewed", head=HEAD, branch=initial["branch"],
            expected_base=BASE, epoch=self.snap()["epoch"], review="pending review")
        self.call("fail", "supervisor-secret", agent="worker", reason="PROCESS_EXIT",
                  evidence="trusted process exit after handoff")
        held = self.snap()["tasks"]["reviewed"]
        self.assertEqual(held["state"], "RECOVERY_HOLD"); self.assertIsNone(held["slot"])
        self.call("recover", "supervisor-secret", task="reviewed",
                  evidence="PR preserved and writer stopped")
        recovered = self.snap()["tasks"]["reviewed"]
        self.assertEqual(recovered["state"], "READY")
        self.assertIsNone(recovered["owner"]); self.assertIsNone(recovered["slot"])
        self.assertEqual(recovered["generation"], initial["generation"] + 2)
        self.assertIsNone(recovered["head"])
        self.assertEqual(recovered["correction_base_head"], HEAD)
        self.assertEqual(recovered["review_recovery_history"][-1]["head"], HEAD)
        self.assertEqual(self.snap()["requests"][request["request"]]["state"],
                         "CANCELLED_RECOVERED_REVIEW")
        claimed = self.claim("reviewed", "replacement")
        self.assertEqual(claimed["generation"], initial["generation"] + 3)
        self.call("provision_slot", "supervisor-secret", task="reviewed",
                  worktree_head=HEAD, evidence="submitted head restored for correction")

    def test_detached_review_resource_request_cannot_grant(self):
        initial = self.review(); self.handoff()
        request = self.call("resource_request", "worker", task="reviewed",
                            generation=initial["generation"],
                            wants=[{"name": "rtx4090"}], priority=9)
        self.assertTrue(request["served"])
        self.assertFalse(request["granted"])
        self.assertEqual(request["dropped_reason"], "stale_claim")
        self.assertFalse(self.snap()["resources"])

    def test_existing_slotted_review_requeue_behavior_is_preserved(self):
        initial = self.review()
        result = self.call("review_requeue", task="reviewed", epoch=self.snap()["epoch"],
                           evidence="stale base, same worktree retained")
        task = self.snap()["tasks"]["reviewed"]
        self.assertEqual(result["state"], "RUNNING")
        self.assertEqual(task["slot"], initial["slot"])
        self.assertEqual(task["owner"], "worker")
        self.assertEqual(task["generation"], initial["generation"] + 1)

    def test_restart_preserves_detached_review_and_reclaim_receipts(self):
        initial = self.review(); self.handoff()
        before = self.snap()["tasks"]["reviewed"]
        restarted = ReviewHandoffControl(self.root / "state.sqlite", "supervisor-secret",
                                         "enroll-secret", self.root / "slots")
        snapshot = restarted.call("snapshot", self.tokens["lead"])["result"]
        self.assertEqual(snapshot["tasks"]["reviewed"], before)
        restarted.call("review_requeue", self.tokens["lead"], task="reviewed",
                       epoch=snapshot["epoch"], head=HEAD,
                       evidence="correction requested after service restart")
        claimed = restarted.call("claim", self.tokens["replacement"],
                                 task="reviewed")["result"]
        self.assertEqual(claimed["generation"], initial["generation"] + 1)

        restarted_again = ReviewHandoffControl(
            self.root / "state.sqlite", "supervisor-secret", "enroll-secret",
            self.root / "slots")
        retained = restarted_again.call("snapshot", self.tokens["lead"])["result"]
        task = retained["tasks"]["reviewed"]
        self.assertEqual(task["correction_base_head"], HEAD)
        self.assertEqual(task["review_correction_history"][-1]["head"], HEAD)
        restarted_again.call("provision_slot", "supervisor-secret", task="reviewed",
                             worktree_head=HEAD,
                             evidence="restarted service verified materialized PR head")

    def test_http_service_routes_to_extension_and_refuses_worker(self):
        self.review(); server = Server(("127.0.0.1", 0), self.c)
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        def post(token):
            req = urllib.request.Request(
                f"http://127.0.0.1:{server.server_port}/v1/action",
                data=json.dumps({"operation": "release_review_slot",
                                 "arguments": self.release_args()}).encode(), method="POST",
                headers={"Authorization": "Bearer " + token,
                         "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status, json.load(response)
        try:
            with self.assertRaises(urllib.error.HTTPError) as caught:
                post(self.tokens["worker"])
            self.assertEqual(caught.exception.code, 409); caught.exception.close()
            status, body = post("supervisor-secret")
            self.assertEqual(status, 200); self.assertEqual(body["result"]["state"], "REVIEW")
        finally:
            server.shutdown(); server.server_close(); thread.join()


if __name__ == "__main__": unittest.main(verbosity=2)
