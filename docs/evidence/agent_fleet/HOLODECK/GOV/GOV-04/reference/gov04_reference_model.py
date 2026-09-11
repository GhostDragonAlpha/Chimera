"""GOV-04 reference model: agent packet generation + admission (INTENDED base contract).

Stdlib-only, self-contained. Mirrors the DEPLOYED source text at base
62b8e35757c71e31d621c26b32a7c52558905b02 — tools/agent_fleet/control.py —
with the INTENDED per-instance fencing (owner_instance bound at claim and
enforced at mutation), not the interceptor deviation (recorded separately as
the R6 measured finding; fix in flight as PR #80).

Line references in comments cite control.py at base.
"""
from __future__ import annotations

import re
from pathlib import PurePosixPath

ID_RE = re.compile(r"[a-z0-9][a-z0-9-]{0,63}")          # control.py:506
PROTECTED = "chimeraengine/engine/build"                 # control.py:47
ACTIVE = ("RUNNING", "BLOCKED", "REVIEW", "RECOVERY_HOLD")
ACTIVE_MUTABLE = ("RUNNING", "BLOCKED", "REVIEW")        # control.py:120
SLOT_GUARD = 64                                          # control.py SLOT_GUARD


class Refusal(Exception):
    """Deployed refusal semantics: require(condition, reason)."""


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise Refusal(reason)


def path_scope(value) -> str:                            # control.py:41-49
    require(isinstance(value, str), "invalid_scope")
    value = value.replace("\\", "/")
    p = PurePosixPath(value)
    require(not p.is_absolute() and ":" not in value
            and not any(x in (".", "..", "") for x in value.split("/")),
            "invalid_scope")
    require(".git" not in [x.casefold() for x in p.parts], "git_metadata_scope")
    v = value.casefold()
    require(not (v == PROTECTED or v.startswith(PROTECTED + "/")
                 or PROTECTED.startswith(v + "/")), "protected_build_scope")
    return value


def overlaps(a: str, b: str) -> bool:                    # control.py:51-53
    a = a.casefold()
    b = b.casefold()
    return a == b or a.startswith(b + "/") or b.startswith(a + "/")


def _sha40(value) -> str:                                # control.py:37-38
    require(isinstance(value, str)
            and re.fullmatch(r"[0-9a-f]{40}", value) is not None, "invalid_commit")
    return value


class Registry:
    def __init__(self, leader: str, epoch: int = 5):
        self.leader = leader
        self.epoch = epoch
        self.agents: dict = {}
        self.tasks: dict = {}
        self.slots: dict = {"1": {"task": None, "kind": "integration",
                                  "engine": {"provisioned": False}}}
        self.catalogue: dict = {"import": None, "imports": [], "payload": {}}
        self.revision = 0

    # ── agents ────────────────────────────────────────────────────────────
    def add_agent(self, agent_id: str, capabilities, max_tasks: int,
                  qualified: bool = True) -> None:
        self.agents[agent_id] = {"capabilities": set(capabilities),
                                 "max_tasks": max_tasks,
                                 "qualified": qualified,
                                 "instances": {}}

    def _lead(self, actor, epoch) -> None:               # control.py:113-114
        require(actor == self.leader and epoch == self.epoch,
                "stale_or_nonleader")

    # ── create_task (packet admission) — control.py:503-524 ──────────────
    def create_task(self, actor, epoch, task, base, scopes, dependencies=(),
                    capabilities=None, kind="worker", packet="", resources=()):
        self._lead(actor, epoch)
        require(isinstance(task, str) and task, "invalid_task")
        require(ID_RE.fullmatch(task) is not None and task not in self.tasks,
                "invalid_or_duplicate_task")             # control.py:506
        require(isinstance(scopes, list) and bool(scopes), "scopes_required")
        scopes = [path_scope(x) for x in scopes]
        deps = list(dependencies)
        require(isinstance(deps, list)
                and all(x in self.tasks for x in deps),
                "dependencies_must_exist")               # control.py:508
        capabilities = [] if capabilities is None else capabilities
        require(isinstance(capabilities, list)
                and all(isinstance(x, str) for x in capabilities),
                "invalid_capabilities")
        require(kind in ("integration", "worker"), "invalid_task_kind")
        record = {
            "id": task, "state": "READY", "owner": None, "slot": None,
            "owner_instance": None, "generation": 0, "kind": kind,
            "base": _sha40(base), "branch": "astra/tasks/" + task,
            "pr_base": "astra/gait-capture",
            "scopes": scopes, "dependencies": deps,
            "capabilities": list(capabilities), "resources": list(resources),
            "packet": packet if isinstance(packet, str) else "",
            "checkpoint": None, "head": None, "review": None,
            "integration": None,
        }
        require(isinstance(record["packet"], str) and record["packet"] != "",
                "invalid_packet")                        # control.py:521 text()
        self.tasks[task] = record
        self.revision += 1
        return dict(record)

    # ── claim — control.py:520-558, INTENDED instance binding ────────────
    def claim(self, actor, task, instance=None):
        require(actor in self.agents and self.agents[actor]["qualified"],
                "qualified_agent_required")
        a = self.agents[actor]
        t = self.tasks.get(task)
        require(t is not None and t["state"] == "READY", "task_not_ready")
        require(t["kind"] != "integration" or actor == self.leader,
                "integration_slot_lead_only")
        if any(overlaps(x, "docs/THE_MASTER_LIST.md") for x in t["scopes"]):
            require(actor == self.leader, "master_list_lead_only")
        require(set(t["capabilities"]) <= set(a["capabilities"]),
                "capability_missing")
        active = [v for v in self.tasks.values()
                  if v["owner"] == actor and v["state"] in ACTIVE]
        require(len(active) < a["max_tasks"], "agent_capacity_reached")
        require(all(self.tasks[d]["state"] == "INTEGRATED"
                    for d in t["dependencies"]),
                "dependencies_not_integrated")           # control.py:526
        for other in self.tasks.values():
            if other["state"] in ACTIVE:
                require(not any(overlaps(x, y)
                                for x in t["scopes"] for y in other["scopes"]),
                        "write_scope_conflict")          # control.py:531-532
        available = [(n, v) for n, v in self.slots.items()
                     if v["task"] is None and v["kind"] == t["kind"]
                     and not v["engine"].get("provisioned")]
        if not available:
            # fleet-slot-expansion-03 auto-spawn, control.py:537-546
            if not any(v["task"] is None and v["kind"] == t["kind"]
                       for v in self.slots.values()):
                require(t["kind"] != "integration", "integration_slot_busy")
                require(len(self.slots) < SLOT_GUARD, "slot_guard_reached")
                n = str(max(int(k) for k in self.slots) + 1)
                self.slots[n] = {"task": None, "kind": t["kind"],
                                 "engine": {"provisioned": False}}
                available = [(n, self.slots[n])]
            else:
                require(False, "stale_provision_requires_recovery")
        n, slot = available[0]
        slot["task"] = t["id"]
        t.update(owner=actor, slot=n, state="RUNNING",
                 generation=t["generation"] + 1,
                 owner_instance=instance)                # control.py:553-554
        self.revision += 1
        return dict(t)

    # ── mutate via _task CAS — control.py:116-124 (INTENDED fencing) ─────
    def _task(self, actor, tid, generation, instance=None):
        t = self.tasks.get(tid)
        require(t is not None, "unknown_task")
        require(t["owner"] == actor and t["generation"] == generation,
                "stale_or_foreign_claim")
        require(t["state"] in ACTIVE_MUTABLE, "task_not_owned_active")
        if t.get("owner_instance") is not None:          # control.py:121-123
            require(instance == t["owner_instance"], "instance_not_bound")
        return t

    def checkpoint(self, actor, tid, generation, payload, instance=None,
                   state="RUNNING"):
        t = self._task(actor, tid, generation, instance)
        require(state in ("RUNNING", "BLOCKED"), "invalid_checkpoint_state")
        t["checkpoint"] = payload
        t["state"] = state
        self.revision += 1
        return {"saved": True}

    def submit_review(self, actor, tid, generation, head, evidence,
                      instance=None):
        t = self._task(actor, tid, generation, instance)
        require(t["state"] == "RUNNING", "task_not_running")
        t["state"] = "REVIEW"
        t["head"] = _sha40(head)
        t["review"] = evidence
        self.revision += 1
        return {"state": "REVIEW", "acceptance": "NOT_CLAIMED"}

    def integrate(self, tid):
        """Supervisor-side integration terminal (state machine closure only)."""
        t = self.tasks[tid]
        require(t["state"] == "REVIEW", "task_not_in_review")
        t["state"] = "INTEGRATED"
        self.revision += 1

    # ── catalogue plane — control.py:774-826 ──────────────────────────────
    def catalogue_import(self, actor, epoch, digest_value, payload,
                         imported_revision):
        self._lead(actor, epoch)
        require(isinstance(digest_value, str) and len(digest_value) == 64,
                "invalid_catalogue_digest")
        current = self.catalogue.get("import")
        if current is not None:
            require(digest_value == current["digest"], "stale_catalogue_import")
        require(isinstance(payload, dict), "invalid_catalogue_payload")
        for c in payload.get("cards", []):
            require(isinstance(c, dict) and isinstance(c.get("id"), str)
                    and isinstance(c.get("status"), str),
                    "invalid_catalogue_payload")
        require(all(d["digest"] != digest_value
                    for d in self.catalogue["imports"]),
                "duplicate_catalogue_import")
        self.catalogue["import"] = {"digest": digest_value,
                                    "imported_revision": imported_revision,
                                    "epoch": epoch}
        self.catalogue["imports"].append({"digest": digest_value,
                                          "imported_revision": imported_revision,
                                          "epoch": epoch})
        self.catalogue["payload"] = payload
        self.revision += 1
        return {"imported": True}

    def catalogue_next(self, digest_value):               # control.py:804-826
        require(isinstance(digest_value, str), "missing_catalogue_digest")
        require(self.catalogue.get("import") is not None
                and digest_value == self.catalogue["import"]["digest"],
                "unknown_catalogue_digest")
        payload = self.catalogue.get("payload") or {}
        live = {tid.casefold() for tid, t in self.tasks.items()
                if t["state"] not in ("INTEGRATED", "ABANDONED")}
        done = {tid.casefold() for tid, t in self.tasks.items()
                if t["state"] == "INTEGRATED"}
        candidates = []
        for c in payload.get("cards", []):
            if not isinstance(c, dict) or not isinstance(c.get("id"), str):
                continue
            cid = c["id"].casefold()
            if cid in live or cid in done:
                continue
            if c.get("status") != "PROPOSED":
                continue
            deps = c.get("depends_on") if isinstance(c.get("depends_on"),
                                                     list) else []
            if all(str(d).casefold() in done for d in deps):
                candidates.append(c["id"])
        candidates.sort()
        return {"digest": digest_value, "candidates": candidates,
                "live_tasks": sorted(live)}

    def catalogue_read(self, digest_value, plane, ident):
        require(plane in ("card", "master_row"), "unknown_catalogue_plane")
        require(self.catalogue.get("import") is not None
                and digest_value == self.catalogue["import"]["digest"],
                "unknown_catalogue_digest")
        key = "cards" if plane == "card" else "master_rows"
        for rec in (self.catalogue.get("payload") or {}).get(key, []):
            if isinstance(rec, dict) and rec.get("id") == ident:
                return {"plane": plane, "record": rec, "digest": digest_value}
        raise Refusal("unknown_catalogue_id")

    # ── CARD DELIVERABLE 1: packet generation ─────────────────────────────
    def generate_packet(self, tid) -> dict:
        """Self-contained assignment from a task record (CARD STATEMENT) with
        the four measured-required elements (CARD PREDICTION): dependencies,
        actual evidence, write scope, finish criteria."""
        t = self.tasks.get(tid)
        require(t is not None, "unknown_task")
        return {
            "id": t["id"],
            "base": t["base"],
            "branch": t["branch"],
            "kind": t["kind"],
            "capabilities": list(t["capabilities"]),
            # (1) CARD PREDICTION: dependencies
            "dependencies": list(t["dependencies"]),
            # (2) CARD PREDICTION: actual evidence — the record's real state
            "evidence": {
                "state": t["state"],
                "generation": t["generation"],
                "checkpoint": t["checkpoint"],
                "head": t["head"],
                "review": t["review"],
                "integration": t["integration"],
                "slot": t["slot"],
                "resources": list(t["resources"]),
            },
            # (3) CARD PREDICTION: write scope
            "write_scope": list(t["scopes"]),
            # (4) CARD PREDICTION: finish criteria
            "finish_criteria": {
                "assignment": t["packet"],
                "terminal_states": ["REVIEW", "INTEGRATED"],
                "review_requires": ["branch == astra/tasks/" + t["id"],
                                    "resources released",
                                    "evidence text present"],
            },
        }

    # ── CARD MATHEMATICS: scheduling ──────────────────────────────────────
    def ready_set(self, integrated: set) -> list:
        """Tasks whose dependencies are all satisfied by `integrated`."""
        return sorted(tid for tid in self.tasks
                      if all(d in integrated for d in self.tasks[tid]["dependencies"]))

    def schedule(self, worker_slots: int):
        """Topological scheduling under a resource constraint (worker slots).

        Rounds: each round schedules at most `worker_slots` READY worker tasks
        (dependencies already integrated); the round's batch finishes and
        integrates at round end, freeing the slots. Integration-kind tasks use
        the single immortal integration slot (<=1 per round).
        Returns (order, rounds, critical_path, max_batch).
        """
        integrated: set = set()
        scheduled: set = set()
        order: list = []
        rounds: list = []
        max_batch = 0
        while scheduled < set(self.tasks):
            ready = [tid for tid in self.ready_set(integrated)
                     if tid not in scheduled]
            require(bool(ready), "dependency_cycle")  # topo law: a DAG always yields
            workers = [t for t in ready if self.tasks[t]["kind"] == "worker"]
            others = [t for t in ready if self.tasks[t]["kind"] != "worker"]
            batch = workers[:worker_slots] + others[:1]
            require(bool(batch), "resource_deadlock")
            rounds.append(list(batch))
            order.extend(batch)
            scheduled.update(batch)
            integrated.update(batch)
            max_batch = max(max_batch, len(batch))
        # critical path: longest dependency chain (node count), derived
        depth = {tid: 1 for tid in self.tasks}
        for tid in order:  # topo order guarantees dependencies first
            for d in self.tasks[tid]["dependencies"]:
                depth[tid] = max(depth[tid], depth[d] + 1)
        deepest = max(depth.values())
        path = []
        node = next(tid for tid in order if depth[tid] == deepest)
        while True:
            path.append(node)
            preds = list(self.tasks[node]["dependencies"])
            if not preds:
                break
            node = max(preds, key=lambda d: depth[d])
        path.reverse()
        return order, rounds, path, max_batch
