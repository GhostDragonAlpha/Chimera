"""Review-preserving physical-slot handoff layered over the existing Control."""
from __future__ import annotations

from control import Control, integer, overlaps, require, sha, text
from layout import slot_layout


class ReviewHandoffControl(Control):
    def _dispatch(self, state, actor, operation, arguments):
        if operation in ("resource_request", "resource_acquire", "submit_review"):
            task = state["tasks"].get(arguments.get("task"))
            if task is not None and task.get("correction_base_head") is not None:
                # Preserve the base identity check before naming the narrower
                # provisioning refusal; foreign/stale sessions learn no more.
                self._task(state, actor, arguments.get("task"),
                           arguments.get("generation"))
                require(False, "correction_provision_required")
        if operation == "claim":
            return self._claim_with_detached_review_capacity(state, actor, arguments)
        if operation == "release_review_slot":
            return self._release_review_slot(state, actor, arguments)
        if operation == "review_requeue":
            task = state["tasks"].get(arguments.get("task"))
            if task is not None and task.get("state") == "REVIEW" and task.get("slot") is None:
                return self._requeue_slotless_review(state, actor, task, arguments)
        if operation == "recover":
            task = state["tasks"].get(arguments.get("task"))
            if task is not None and task.get("state") == "RECOVERY_HOLD" and task.get("slot") is None:
                return self._recover_slotless(state, actor, task, arguments)
        if operation == "release_slot":
            task = state["tasks"].get(arguments.get("task"))
            if task is not None and task.get("state") == "INTEGRATED" and task.get("slot") is None:
                return self._release_already_handed_off(state, actor, task, arguments)
        if operation == "ack_integration":
            result = super()._dispatch(state, actor, operation, arguments)
            request = state.get("requests", {}).get(arguments.get("request"))
            task = state["tasks"].get(request.get("task")) if request else None
            if (task is not None and task.get("slot") is None
                    and bool(task.get("review_slot_handoffs"))):
                return {**result, "slot": None,
                        "slot_status": "RELEASED_AT_REVIEW_HANDOFF"}
            return result
        if operation == "provision_slot":
            task = state["tasks"].get(arguments.get("task"))
            if task is not None and task.get("correction_base_head") is not None:
                require(arguments.get("worktree_head") == task["correction_base_head"],
                        "correction_worktree_head_mismatch")
                result = super()._dispatch(state, actor, operation, arguments)
                task["correction_provisioned_head"] = task.pop("correction_base_head")
                task["correction_provisioned_revision"] = state["revision"] + 1
                return result
        return super()._dispatch(state, actor, operation, arguments)

    def _claim_with_detached_review_capacity(self, state, actor, p):
        """Base claim, changing only detached REVIEW capacity accounting."""
        require(actor in state["agents"] and state["agents"][actor]["qualified"],
                "qualified_agent_required")
        agent = state["agents"][actor]
        task = state["tasks"].get(p.get("task"))
        require(task is not None and task["state"] == "READY", "task_not_ready")
        require(task["kind"] != "integration" or actor == state["leader"],
                "integration_slot_lead_only")
        if any(overlaps(scope, "docs/THE_MASTER_LIST.md") for scope in task["scopes"]):
            require(actor == state["leader"], "master_list_lead_only")
        require(set(task["capabilities"]) <= set(agent["capabilities"]), "capability_missing")
        active = [other for other in state["tasks"].values()
                  if other["owner"] == actor
                  and other["state"] in ("RUNNING", "BLOCKED", "REVIEW", "RECOVERY_HOLD")
                  and not (other["state"] == "REVIEW" and other.get("slot") is None
                           and bool(other.get("review_slot_handoffs")))]
        require(len(active) < agent["max_tasks"], "agent_capacity_reached")
        require(all(state["tasks"][dep]["state"] == "INTEGRATED"
                    for dep in task["dependencies"]), "dependencies_not_integrated")
        for other in state["tasks"].values():
            if other["state"] in ("RUNNING", "BLOCKED", "REVIEW", "RECOVERY_HOLD"):
                require(not any(overlaps(left, right) for left in task["scopes"]
                                for right in other["scopes"]), "write_scope_conflict")
        available = [(number, slot) for number, slot in state["slots"].items()
                     if slot["task"] is None and slot["kind"] == task["kind"]]
        require(available, "no_free_slot")
        number, slot = available[0]
        slot["task"] = task["id"]
        task.update(owner=actor, slot=number, state="RUNNING",
                    generation=task["generation"] + 1)
        return {**task, "worktree": slot["path"], "engine": slot["engine"],
                "provisioning": "REQUIRED: claim metadata does not create or modify a worktree"}

    def _release_review_slot(self, state, actor, p):
        require(actor == "SUPERVISOR", "supervisor_only")
        task_id = text(p.get("task"), "task")
        owner = text(p.get("owner"), "owner")
        generation = integer(p.get("generation"), 0, 2**63 - 1, "generation")
        slot_id = text(p.get("slot"), "slot")
        head = sha(p.get("head"))
        pushed_head = sha(p.get("pushed_head"))
        pr_head = sha(p.get("pr_head"))
        pr_identity = text(p.get("pr_identity"), "pr_identity")
        remote_verification = text(p.get("remote_verification_evidence"),
                                   "remote_verification_evidence")
        preservation = text(p.get("preservation_evidence"), "preservation_evidence")
        writer_stopped = text(p.get("writer_stopped_evidence"), "writer_stopped_evidence")
        runtime_drained = text(p.get("runtime_drained_evidence"), "runtime_drained_evidence")
        slot_ready = text(p.get("slot_reprovision_ready_evidence"),
                          "slot_reprovision_ready_evidence")
        require(head == pushed_head == pr_head, "review_head_identity_mismatch")

        task = state["tasks"].get(task_id)
        require(task is not None and task.get("state") == "REVIEW", "task_not_in_review")
        require(task.get("owner") == owner, "stale_or_foreign_owner")
        require(task.get("generation") == generation, "stale_generation")
        require(task.get("slot") == slot_id, "stale_slot")
        require(task.get("head") == head, "review_head_changed")
        slot = state["slots"].get(slot_id)
        require(slot is not None and slot.get("task") == task_id, "slot_binding_mismatch")
        require(not any(resource.get("task") == task_id
                        for resource in state["resources"].values()),
                "resources_still_held")

        receipt = {
            "owner": owner, "generation": generation, "slot": slot_id,
            "head": head, "branch": task["branch"], "review": task.get("review"),
            "checkpoint": task.get("checkpoint"), "pr_identity": pr_identity,
            "pushed_head": pushed_head, "pr_head": pr_head,
            "remote_verification_evidence": remote_verification,
            "preservation_evidence": preservation,
            "writer_stopped_evidence": writer_stopped,
            "runtime_drained_evidence": runtime_drained,
            "slot_reprovision_ready_evidence": slot_ready,
            "released_revision": state["revision"] + 1,
        }
        task.setdefault("review_slot_handoffs", []).append(receipt)
        slot["task"] = None
        slot["engine"] = slot_layout(state["root"], int(slot_id))["engine"]
        task["slot"] = None
        return {"state": "REVIEW", "head": head, "generation": generation,
                "slot_released": slot_id, "filesystem_deleted": False,
                "acceptance": "NOT_CLAIMED"}

    def _requeue_slotless_review(self, state, actor, task, p):
        self._lead(state, actor, p.get("epoch"))
        old_head = sha(p.get("head"))
        require(task.get("head") == old_head, "review_head_changed")
        handoffs = task.get("review_slot_handoffs", [])
        require(handoffs and handoffs[-1].get("head") == old_head,
                "missing_review_slot_handoff")
        owner = task.get("owner")
        evidence = text(p.get("evidence"), "requeue_reconciliation_evidence")

        previous = {
            "head": old_head, "review": task.get("review"),
            "checkpoint": task.get("checkpoint"), "owner": owner,
            "generation": task["generation"], "handoff": handoffs[-1],
            "requeue_evidence": evidence, "requeued_revision": state["revision"] + 1,
        }
        task.setdefault("review_correction_history", []).append(previous)
        for request in state.get("requests", {}).values():
            if (request.get("task") == task["id"] and
                    request.get("state") == "PENDING_EXTERNAL_BROKER"):
                request["state"] = "CANCELLED_REQUEUED"
                request["cancelled_revision"] = state["revision"] + 1
        task.update(state="READY", owner=None, slot=None, head=None,
                    checkpoint=evidence, correction_base_head=old_head)
        return {"state": "READY", "generation": task["generation"],
                "previous_owner": owner, "review_artifact_preserved": True,
                "claim_required": True,
                "provisioning": "after claim, materialize exact correction_base_head then provision_slot"}

    def _recover_slotless(self, state, actor, task, p):
        require(actor == "SUPERVISOR", "preservation_observer_required")
        require(not any(resource.get("task") == task["id"]
                        for resource in state["resources"].values()),
                "resources_still_held")
        for request in state.get("resource_queues", []):
            if request.get("task") == task["id"] and not request.get("served"):
                request["served"] = True
                request["dropped_reason"] = "recovered_generation"
        evidence = text(p.get("evidence"), "preserved_and_writer_stopped_evidence")
        reviewed_head = task.get("head")
        require(reviewed_head is not None and bool(task.get("review_slot_handoffs")),
                "missing_review_slot_handoff")
        task.setdefault("review_recovery_history", []).append({
            "head": reviewed_head, "review": task.get("review"),
            "checkpoint": task.get("checkpoint"), "failed_owner": task.get("owner"),
            "failed_generation": task.get("generation"), "recovery_evidence": evidence,
            "recovered_revision": state["revision"] + 1,
        })
        for request in state.get("requests", {}).values():
            if (request.get("task") == task["id"] and
                    request.get("state") == "PENDING_EXTERNAL_BROKER"):
                request["state"] = "CANCELLED_RECOVERED_REVIEW"
                request["cancelled_revision"] = state["revision"] + 1
        task.update(state="READY", owner=None, slot=None, head=None,
                    generation=task["generation"] + 1, checkpoint=evidence,
                    correction_base_head=reviewed_head)
        self._promote_queues(state)
        return {"state": "READY",
                "old_workspace": "review artifact remains preserved; no slot was bound"}

    def _release_already_handed_off(self, state, actor, task, p):
        require(actor == "SUPERVISOR", "supervisor_only")
        text(p.get("evidence"), "preserved_clean_workspace_and_stopped_processes")
        require(bool(task.get("review_slot_handoffs")), "missing_review_slot_handoff")
        require(not any(resource.get("task") == task["id"]
                        for resource in state["resources"].values()),
                "resource_still_held")
        return {"released": False, "already_released_for_review": True,
                "filesystem_deleted": False}
