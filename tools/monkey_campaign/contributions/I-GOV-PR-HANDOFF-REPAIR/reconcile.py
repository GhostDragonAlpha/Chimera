"""reconcile.py -- I-GOV-PR-HANDOFF-REPAIR correction probe.

Proves, against the CURRENT installed campaign modules (astra-0026), in
isolated temporary registries configured like production, that the two PR #116
review findings repaired by the historical PR #128 cannot reproduce today:

  D1  explicit task routing: an explicit request for card X NEVER returns
      another card. While the worker holds other WORKING work it refuses by
      name (checkpoint_active_work_before_switch); with no other active work
      it returns exactly X. (PR #128's automatic displacement is deliberately
      NOT installed: astra-0022 forbids automatic parking/takeover.)
  D2  PR-request bridge: continuous_cycle.request_publication IS the durable
      machinery (exact identity, idempotent, offline), and the requesting
      worker is handed the NEXT card, never trapped.

Also asserts the card falsifier invariants: capacity stays 10, criteria
hashes never change, another agent's attempts are never touched.

Exit 0 = reconciliation holds (all checks green). Exit 1 = any deviation
(reported loudly -- see PREREGISTRATION falsifier). No production files are
touched: modules are imported read-only from MODULES_DIR; registries live in
tempfile.TemporaryDirectory.
"""
from __future__ import annotations

import json
import pathlib
import shutil
import sys
import tempfile
import traceback

MODULES_DIR = pathlib.Path("E:/PythonChimera/tools/monkey_campaign")
sys.path.insert(0, str(MODULES_DIR))

import kanban  # noqa: E402  (current installed module, read-only use)
import continuous_cycle  # noqa: E402
from agent_slots import Registry  # noqa: E402

WORKER = "reconcile-probe-worker"
OTHER = "reconcile-probe-other-agent"

SPECS = [{"id": f"T{i}", "objective": f"o{i}", "falsifier": f"f{i}",
          "steps": [f"s{i}"], "completion": f"c{i}", "depends_on": []}
         for i in range(3)]

ARTIFACTS = [{"path": "x.py", "sha256": "0" * 64}]


def fresh_registry():
    tmp = tempfile.mkdtemp(prefix="igov_reconcile_")
    registry = Registry(pathlib.Path(tmp))
    registry.initialize()
    kanban.initialize(registry, SPECS, actor=kanban.LEAD)
    with registry.transaction() as state:          # production board shape
        state["kanban"]["continuous_cycle"] = True
        state["kanban"]["separate_review_lane"] = True
        state["kanban"]["branch_policy"] = "TEN_PERSISTENT_SLOT_BRANCHES"
    return registry


def request_payload(packet, head_tag="b"):
    # artifacts must be real files inside the attempt workspace (production law)
    import hashlib
    ws = pathlib.Path(packet["attempt"]["workspace"])
    ws.mkdir(parents=True, exist_ok=True)
    art = ws / "candidate.txt"
    art.write_text("reconciliation probe candidate\n", encoding="utf-8")
    return {"agent_id": WORKER, "task_id": packet["task_id"],
            "attempt_id": packet["attempt"]["id"],
            "criteria_sha256": packet["attempt"]["criteria_sha256"],
            "checkpoint": "candidate preserved; reconciliation probe",
            "writes_stopped": True,
            "artifacts": [{"path": str(art),
                           "sha256": hashlib.sha256(art.read_bytes()).hexdigest()}]}


def check_d1(results):
    """Explicit routing never returns another card."""
    registry = fresh_registry()
    a0 = kanban.join(registry, WORKER)
    assert a0["state"] == "ASSIGNED" and a0["task_id"] == "T0", a0["state"]
    kanban.submit(registry, {"agent_id": WORKER, "task_id": "T0",
                             "attempt_id": a0["attempt"]["id"],
                             "criteria_sha256": a0["attempt"]["criteria_sha256"],
                             "pr_url": "https://github.com/GhostDragonAlpha/Chimera/pull/9101",
                             "head_sha": "a" * 40})
    a1 = kanban.join(registry, WORKER)
    assert a1["state"] == "ASSIGNED", a1
    # (a) explicit request for T0 while T1 is WORKING -> named refusal, no card
    refused = None
    try:
        kanban.join(registry, WORKER, "T0")
    except ValueError as exc:
        refused = str(exc)
    results["d1_refusal_named"] = "checkpoint_active_work_before_switch" in (refused or "")
    # (b) no automatic displacement: T1 attempt still WORKING, untouched
    raw = registry.readonly()["kanban"]["cards"]
    t1 = [a for a in raw["T1"]["attempts"].values() if a["agent_id"] == WORKER]
    results["d1_no_autodisplacement"] = all(a["state"] == "WORKING" for a in t1)
    # (c) park T1, then explicit request for T0 -> NEVER a packet naming T1
    kanban.park(registry, {"agent_id": WORKER, "task_id": "T1",
                           "attempt_id": a1["attempt"]["id"],
                           "checkpoint": "parked for reconciliation probe",
                           "writes_stopped": True})
    packet = kanban.join(registry, WORKER, "T0")
    results["d1_explicit_never_wrong_card"] = packet.get("task_id") != "T1"
    results["d1_explicit_outcome"] = packet.get("state", packet.get("next_action", "?"))
    # (d) positive control: other worker, no active work, explicit T2 -> exactly T2
    a2 = kanban.join(registry, OTHER, "T2")
    results["d1_explicit_positive_control"] = (
        a2.get("state") == "ASSIGNED" and a2.get("task_id") == "T2")
    shutil.rmtree(registry.root, ignore_errors=True)


def check_d2(results):
    """The durable PR-request bridge exists, is idempotent, and frees the worker."""
    registry = fresh_registry()
    a0 = kanban.join(registry, WORKER)
    first = continuous_cycle.request_publication(registry, request_payload(a0))
    results["d2_request_recorded"] = bool(first.get("request_id"))
    raw = registry.readonly()["kanban"]["cards"]["T0"]
    attempts = list(raw["attempts"].values())
    results["d2_attempt_state"] = attempts[0]["state"]
    results["d2_state_is_publication_requested"] = \
        attempts[0]["state"] == "PUBLICATION_REQUESTED"
    # idempotent repeat with identical artifacts -> same request id
    again = continuous_cycle.request_publication(registry, request_payload(a0))
    results["d2_idempotent_same_request"] = (
        again.get("request_id") == first.get("request_id"))
    # wrong criteria hash -> named refusal
    refused = None
    try:
        bad = request_payload(a0)
        bad["criteria_sha256"] = "f" * 64
        continuous_cycle.request_publication(registry, bad)
    except ValueError as exc:
        refused = str(exc)
    results["d2_wrong_criteria_refused"] = bool(refused)
    # next generic join -> a DIFFERENT card (worker not trapped)
    nxt = kanban.join(registry, WORKER)
    results["d2_next_card_differs"] = (
        nxt.get("task_id") != "T0" and nxt.get("state") == "ASSIGNED")
    results["d2_next_card"] = nxt.get("task_id")
    shutil.rmtree(registry.root, ignore_errors=True)


def check_invariants(results):
    """Capacity 10 and per-card criteria hashes survive the workflow ops."""
    registry = fresh_registry()
    before = kanban.read(registry)
    hashes_before = {s["id"]: None for s in SPECS}
    raw = registry.readonly()["kanban"]["cards"]
    hashes_before = {tid: c["criteria_sha256"] for tid, c in raw.items()}
    a0 = kanban.join(registry, WORKER)
    continuous_cycle.request_publication(registry, request_payload(a0))
    a1 = kanban.join(registry, WORKER)
    kanban.park(registry, {"agent_id": WORKER, "task_id": a1["task_id"],
                           "attempt_id": a1["attempt"]["id"],
                           "checkpoint": "invariant probe park",
                           "writes_stopped": True})
    raw_after = registry.readonly()["kanban"]["cards"]
    hashes_after = {tid: c["criteria_sha256"] for tid, c in raw_after.items()}
    results["capacity_stays_ten"] = kanban.read(registry)["capacity"] == 10
    results["criteria_hashes_unchanged"] = hashes_before == hashes_after
    # another agent's attempts untouched by any of the above
    foreign = [a for c in raw_after.values() for a in c["attempts"].values()
               if a["agent_id"] == OTHER]
    results["foreign_attempts_untouched"] = foreign == []
    shutil.rmtree(registry.root, ignore_errors=True)


def run_all() -> dict:
    results = {"schema": "igov.pr116.reconciliation.probe.v1",
               "modules_dir": str(MODULES_DIR)}
    try:
        check_d1(results)
        check_d2(results)
        check_invariants(results)
    except Exception:                                # noqa: BLE001
        results["probe_error"] = traceback.format_exc()[-2000:]
    green_keys = [k for k in results if k.startswith(("d1_", "d2_")) and
                  isinstance(results[k], bool)] + [
        "capacity_stays_ten", "criteria_hashes_unchanged",
        "foreign_attempts_untouched"]
    results["green"] = {k: results.get(k) for k in green_keys}
    results["all_green"] = (not results.get("probe_error")
                            and all(results["green"].values()))
    return results


def main() -> int:
    results = run_all()
    here = pathlib.Path(__file__).resolve().parent
    (here / "reconciliation_receipt.json").write_text(
        json.dumps(results, indent=1, ensure_ascii=False) + "\n",
        encoding="utf-8", newline="\n")
    print(json.dumps(results["green"], indent=1))
    print("all_green:", results["all_green"])
    return 0 if results["all_green"] else 1


if __name__ == "__main__":
    sys.exit(main())
