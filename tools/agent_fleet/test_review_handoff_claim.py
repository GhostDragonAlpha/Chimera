"""fleet-review-handoff-claim-delegation-01: the claim path THROUGH the
review-handoff layer must preserve the base-claim behaviors.

ReviewHandoffControl._dispatch intercepts claim unconditionally and routes
to _claim_with_detached_review_capacity, whose ONE legitimate deviation
from base Control.claim is detached-REVIEW capacity accounting (a slotless
REVIEW task carrying review_slot_handoffs does not consume its owner's
agent capacity). The wrapper must still deliver everything base claim
delivers:

  F1  the fleet-slot-expansion-03 auto-spawn plane (no free slot of the
      kind -> spawn one under the integration/guard fuses; a free but
      provisioned slot is NEVER masked by spawn) - found DEAD in
      production, live refusal no_free_slot (feedback c4212657 rev 767,
      and this task's own claim at rev 781);
  F2  owner_instance binding from the resolved instance header, so the
      instance fence (instance_not_bound) actually holds;
  F3  the enforced-mode instance_binding_required guard.

The preservation tests (capacity accounting, other interception paths)
are expected to PASS on the UNFIXED base; the F1/F2/F3 tests are expected
to FAIL there - that contrast is the fail-pre-fix proof retained in
docs/evidence/agent_fleet/REVIEW_HANDOFF_CLAIM_DELEGATION/.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from control import Refusal
from review_handoff import ReviewHandoffControl

BASE = "a" * 40
HEAD = "b" * 40
MERGED = "c" * 40


class ReviewHandoffClaimTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.c = ReviewHandoffControl(self.root / "state.sqlite", "supervisor-secret",
                                      "enroll-secret", self.root / "slots")
        self.tokens = {}
        for aid, cap in (("lead", 3), ("worker", 2), ("replacement", 3),
                         ("filler", 5)):
            self.tokens[aid] = self.c.call("enroll", "enroll-secret", agent=aid,
                                           label=aid)["result"]["session_token"]
            self.c.call("qualify", "supervisor-secret", agent=aid,
                        capabilities=["cpu"], max_tasks=cap,
                        can_lead=aid == "lead", rank=10 if aid == "lead" else 1,
                        evidence="ephemeral qualification")
        # an instance-bearing agent for the F2/F3 lanes
        self.instance = {"id": "wk-inst-1",
                         "secret": "INSTSECRET-wk-0123456789abcdef"}
        self.tokens["wk"] = self.c.call(
            "enroll", "enroll-secret", agent="wk", label="wk",
            instance=dict(self.instance))["result"]["session_token"]
        self.c.call("qualify", "supervisor-secret", agent="wk",
                    capabilities=["cpu"], max_tasks=3, can_lead=False,
                    evidence="ephemeral qualification")
        self.c.call("offer_lead", self.tokens["lead"], epoch=0,
                    checkpoint="ephemeral leader ready")
        self.c.call("elect", "supervisor-secret")

    def tearDown(self):
        self.temp.cleanup()

    # --- harness ----------------------------------------------------------
    def call(self, op, actor="lead", _instance=None, **p):
        token = self.tokens.get(actor, actor)
        return self.c.call(op, token, _instance=_instance, **p)["result"]

    def refused(self, op, actor, error, _instance=None, **p):
        with self.assertRaisesRegex(Refusal, error):
            self.call(op, actor, _instance=_instance, **p)

    def snap(self):
        return self.call("snapshot")

    def create(self, task, scopes=None, kind="worker"):
        return self.call("create_task", task=task, epoch=self.snap()["epoch"],
                         base=BASE, scopes=scopes or ["tools/work/" + task],
                         packet="statement / prediction / falsifier", kind=kind)

    def fill_worker_slots(self, count=4, owner="filler"):
        """Claim `count` worker tasks so no unprovisioned worker slot remains."""
        for i in range(count):
            tid = "fill%d" % i
            self.create(tid)
            self.call("claim", owner, task=tid)

    def review_and_handoff(self, task="reviewed"):
        """A full review cycle ending in a slotless detached REVIEW task."""
        self.create(task)
        claimed = self.call("claim", "worker", task=task)
        self.call("checkpoint", "worker", task=task,
                  generation=claimed["generation"], checkpoint="checkpoint kept")
        self.call("provision_slot", "supervisor-secret", task=task,
                  worktree_head=BASE, evidence="ephemeral provision receipt")
        self.call("submit_review", "worker", task=task,
                  generation=claimed["generation"], branch=claimed["branch"],
                  head=HEAD, evidence="exact review evidence")
        t = self.snap()["tasks"][task]
        self.call("release_review_slot", "supervisor-secret",
                  task=task, owner=t["owner"], generation=t["generation"],
                  slot=t["slot"], head=t["head"], pushed_head=t["head"],
                  pr_head=t["head"], pr_identity="PR draft #fixture",
                  remote_verification_evidence="broker verified remote and PR heads",
                  preservation_evidence="commit, PR, and review evidence retained",
                  writer_stopped_evidence="human confirmed owning writer stopped",
                  runtime_drained_evidence="owned runtime/process handles absent",
                  slot_reprovision_ready_evidence="slot worktree drained")
        return claimed

    # --- F1: the auto-spawn plane survives the wrapper ---------------------
    def test_claim_auto_spawns_when_no_free_worker_slot(self):
        self.fill_worker_slots(4)                     # slots 2-5 all bound
        self.create("overflow")
        claimed = self.call("claim", "worker", task="overflow")
        self.assertEqual(claimed["state"], "RUNNING")
        self.assertEqual(claimed["slot"], "6")        # next id by high-water
        self.assertEqual(self.snap()["slots"]["6"]["task"], "overflow")

    def test_auto_spawn_respects_integration_named_guard(self):
        self.create("lead-work", kind="integration")
        self.call("claim", "lead", task="lead-work")   # takes the unique slot 1
        self.create("lead-work-2", kind="integration")
        # no free INTEGRATION slot exists: refuse by name, never auto-spawn
        self.refused("claim", "lead", "integration_slot_busy",
                     task="lead-work-2")

    def test_auto_spawn_respects_slot_guard_fuse(self):
        self.c.SLOT_GUARD = len(self.snap()["slots"])  # fuse at current count
        self.fill_worker_slots(4)
        self.create("overflow")
        self.refused("claim", "worker", "slot_guard_reached", task="overflow")

    def test_free_but_provisioned_slot_still_refuses_not_spawned(self):
        self.fill_worker_slots(3)                      # slots 2-4 bound
        self.create("stale")                           # claims slot 5
        claimed = self.call("claim", "worker", task="stale")
        self.call("provision_slot", "supervisor-secret", task="stale",
                  worktree_head=BASE, evidence="provision receipt")
        # free the binding WITHOUT clearing the provision: the stale state
        # (free slot of the kind, actively provisioned) via direct fixture
        # surgery - the same technique test_slot_expansion uses.
        con = self.c.connect()
        con.execute("BEGIN IMMEDIATE")
        s = json.loads(con.execute("SELECT body FROM state WHERE id=1").fetchone()[0])
        s["slots"][claimed["slot"]]["task"] = None
        con.execute("UPDATE state SET body=? WHERE id=1", (json.dumps(s),))
        con.execute("COMMIT")
        con.close()
        self.create("next-task")
        # a free slot of the kind EXISTS -> spawn must NOT mask the stale state
        self.refused("claim", "worker", "stale_provision_requires_recovery",
                     task="next-task")

    # --- F2: owner_instance binding survives the wrapper -------------------
    def test_claim_binds_owner_instance_and_fence_holds(self):
        self.create("fenced")
        claimed = self.call("claim", "wk", _instance=dict(self.instance),
                            task="fenced")
        self.assertEqual(self.snap()["tasks"]["fenced"]["owner_instance"],
                         self.instance["id"])
        # header-less twin of the SAME bearer must be refused by the fence
        self.refused("checkpoint", "wk", "instance_not_bound", task="fenced",
                     generation=claimed["generation"], checkpoint="twin writes")
        # the correctly-headed instance is admitted
        out = self.call("checkpoint", "wk", _instance=dict(self.instance),
                        task="fenced", generation=claimed["generation"],
                        checkpoint="bound instance writes")
        self.assertTrue(out["saved"])
        self.refused("submit_review", "wk", "instance_not_bound", task="fenced",
                     generation=claimed["generation"], branch=claimed["branch"],
                     head=HEAD, evidence="twin review refused")

    def test_compat_mode_headerless_claim_stays_legacy_unfenced(self):
        self.create("legacy")
        claimed = self.call("claim", "worker", task="legacy")   # no header
        self.assertIsNone(self.snap()["tasks"]["legacy"]["owner_instance"])
        out = self.call("checkpoint", "worker", task="legacy",
                        generation=claimed["generation"],
                        checkpoint="legacy unfenced writer")
        self.assertTrue(out["saved"])

    # --- F3: enforced-mode guard survives the wrapper ----------------------
    def test_enforced_mode_refuses_instanceless_claim(self):
        self.call("instance_fencing_set", "supervisor-secret", mode="enforced")
        self.create("must-bind")
        # base behavior: enforced fencing refuses an instance-less claim
        self.refused("claim", "worker", "instance_binding_required",
                     task="must-bind")
        # with the header the claim is admitted - and bound (F2)
        claimed = self.call("claim", "wk", _instance=dict(self.instance),
                            task="must-bind")
        self.assertEqual(claimed["state"], "RUNNING")
        self.assertEqual(self.snap()["tasks"]["must-bind"]["owner_instance"],
                         self.instance["id"])

    # --- P4: the ONE legitimate deviation is preserved ---------------------
    def test_detached_review_task_does_not_consume_agent_capacity(self):
        self.review_and_handoff("reviewed")            # worker owns a slotless
        # REVIEW task WITH a handoff receipt; worker is at max_tasks=2 once
        # the survivor lands, so the NEXT claim only succeeds because the
        # detached REVIEW is excluded from the capacity count.
        self.create("survivor")
        self.call("claim", "worker", task="survivor")
        self.create("new-work")
        claimed = self.call("claim", "worker", task="new-work")
        self.assertEqual(claimed["state"], "RUNNING")
        self.assertEqual(claimed["owner"], "worker")
        # ...and the margin is real: one more RUNNING task hits the cap.
        self.create("new-work-2")
        self.refused("claim", "worker", "agent_capacity_reached",
                     task="new-work-2")

    def test_running_task_still_counts_toward_agent_capacity(self):
        self.create("cap-a")
        self.call("claim", "worker", task="cap-a")     # max_tasks=2
        self.create("cap-b")
        self.call("claim", "worker", task="cap-b")
        self.create("cap-c")
        self.refused("claim", "worker", "agent_capacity_reached",
                     task="cap-c")

    # --- P5: the wrapper's OTHER interception paths stay intact ------------
    def test_slotless_requeue_requires_exact_head_then_requeues(self):
        self.review_and_handoff("reviewed")
        # live-observed 2026-09-11: a requeue without the reviewed head
        # refuses invalid_commit
        self.refused("review_requeue", "lead", "invalid_commit",
                     task="reviewed", epoch=self.snap()["epoch"],
                     evidence="head omitted")
        result = self.call("review_requeue", task="reviewed",
                           epoch=self.snap()["epoch"], head=HEAD,
                           evidence="review requested correction")
        self.assertEqual(result["state"], "READY")
        ready = self.snap()["tasks"]["reviewed"]
        self.assertIsNone(ready["slot"])
        self.assertEqual(ready["correction_base_head"], HEAD)

    def test_correction_interception_still_gates_post_requeue(self):
        self.review_and_handoff("reviewed")
        self.call("review_requeue", task="reviewed", epoch=self.snap()["epoch"],
                  head=HEAD, evidence="correction requested")
        claimed = self.call("claim", "replacement", task="reviewed")
        self.call("checkpoint", "replacement", task="reviewed",
                  generation=claimed["generation"], checkpoint="prep recorded")
        self.refused("submit_review", "replacement", "correction_provision_required",
                     task="reviewed", generation=claimed["generation"],
                     branch=claimed["branch"], head=MERGED,
                     evidence="must wait for provision")

    def test_recover_stays_supervisor_only_and_release_routes_slotless(self):
        self.review_and_handoff("reviewed")
        self.refused("recover", "lead", "preservation_observer_required",
                     task="reviewed", evidence="non-supervisor refused")
        request = self.call("integration_request", task="reviewed", head=HEAD,
                            branch=self.snap()["tasks"]["reviewed"]["branch"],
                            expected_base=BASE, epoch=self.snap()["epoch"],
                            review="independent review")
        ack = self.call("ack_integration", "supervisor-secret",
                        request=request["request"],
                        base_branch="astra/gait-capture", expected_base=BASE,
                        commit=MERGED, evidence="publisher verified remote head")
        self.assertIsNone(ack["slot"])
        self.assertEqual(ack["slot_status"], "RELEASED_AT_REVIEW_HANDOFF")
        released = self.call("release_slot", "supervisor-secret",
                             task="reviewed", evidence="already drained at handoff")
        self.assertTrue(released["already_released_for_review"])


if __name__ == "__main__":
    unittest.main()
