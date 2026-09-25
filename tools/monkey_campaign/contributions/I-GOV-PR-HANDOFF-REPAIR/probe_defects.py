#!/usr/bin/env python3
"""Reproduce the two PR #116 review findings against the PINNED kanban.py.

Runs entirely in an isolated temporary registry. Exit code: number of defects
reproduced (0 means the premise failed -> F7 in the preregistration).
"""
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
VARIANT = sys.argv[1] if len(sys.argv) > 1 else "reference"
sys.path.insert(0, str(HERE / "reference"))

if VARIANT == "patched":
    import importlib.util
    _spec = importlib.util.spec_from_file_location(
        "kanban", HERE / "patched" / "kanban.py")
    kanban = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(kanban)
else:
    import kanban  # noqa: E402  (pinned PR #116 bytes)
from agent_slots import Registry  # noqa: E402

SPECS = [
    {"id": "T0", "objective": "o0", "falsifier": "f0", "steps": ["s0"],
     "completion": "c0", "depends_on": []},
    {"id": "T1", "objective": "o1", "falsifier": "f1", "steps": ["s1"],
     "completion": "c1", "depends_on": []},
    {"id": "T2", "objective": "o2", "falsifier": "f2", "steps": ["s2"],
     "completion": "c2", "depends_on": []},
]
WORKER = "worker-probe"


def main():
    reproduced = 0
    with tempfile.TemporaryDirectory() as tmp:
        registry = Registry(Path(tmp))
        registry.initialize()
        kanban.initialize(registry, SPECS, actor=kanban.LEAD)

        # --- Defect 1: explicit routing with two WORKING attempts ---
        a0 = kanban.join(registry, WORKER)                       # T0 WORKING
        assert a0["task_id"] == "T0", a0["task_id"]
        kanban.submit(registry, {"agent_id": WORKER, "task_id": "T0",
                                 "attempt_id": a0["attempt"]["id"],
                                 "criteria_sha256": a0["attempt"]["criteria_sha256"],
                                 "pr_url": "https://github.com/GhostDragonAlpha/Chimera/pull/9001",
                                 "head_sha": "a" * 40})
        a1 = kanban.join(registry, WORKER)                       # T1 WORKING
        assert a1["task_id"] == "T1", a1["task_id"]
        revisit = kanban.join(registry, WORKER, "T0")            # explicit revisit T0
        # Count the worker's WORKING attempts directly from the raw board.
        raw = registry.readonly()["kanban"]["cards"]
        working = [(tid, att["id"], att["state"])
                   for tid, card in raw.items() for att in card["attempts"].values()
                   if att["agent_id"] == WORKER and att["state"] == "WORKING"]
        back = kanban.join(registry, WORKER, "T1")               # explicit request T1
        print("D1: revisit state:", revisit["state"], revisit["task_id"])
        print("D1: WORKING attempts after revisit:", working)
        print("D1: explicit request for T1 returned:", back["state"], back["task_id"])
        d1 = (back.get("task_id") != "T1") or (len(working) > 1)
        if d1:
            reproduced += 1
            print("D1 REPRODUCED: wrong card and/or two WORKING attempts")
        else:
            print("D1 NOT reproduced (F7)")

        # --- Defect 2: PR-request bridge has no worker transition ---
        # Fresh registry: worker joins T0, then signals a PR request, then polls.
        with tempfile.TemporaryDirectory() as tmp2:
            registry2 = Registry(Path(tmp2))
            registry2.initialize()
            kanban.initialize(registry2, SPECS, actor=kanban.LEAD)
            first = kanban.join(registry2, WORKER)
            assert first["task_id"] == "T0"
            if VARIANT == "patched":
                result = kanban.request_publication(registry2, {
                    "agent_id": WORKER, "task_id": "T0",
                    "attempt_id": first["attempt"]["id"],
                    "criteria_sha256": first["attempt"]["criteria_sha256"],
                    "head_sha": "b" * 40, "branch": "branch-1",
                    "checkpoint": "candidate preserved", "writes_stopped": True,
                    "artifacts": [{"path": "x", "sha256": "0" * 64}]})
                print("D2: request_publication state:", result["state"])
            else:
                kanban.post(registry2, {"task_id": "T0", "author": WORKER,
                                        "body": "PR REQUEST branch=X head=" + "b" * 40})
            nxt = kanban.join(registry2, WORKER)                  # generic poll
            print("D2: after the PR-request signal, generic poll returned:",
                  nxt["state"], nxt.get("task_id"))
            raw2 = registry2.readonly()["kanban"]["cards"]
            t0 = raw2["T0"]
            attempt0 = next(iter(t0["attempts"].values()))
            if VARIANT == "patched":
                ok = (attempt0["state"] == "PUBLICATION_REQUESTED"
                      and nxt.get("task_id") != "T0" and nxt.get("state") == "ASSIGNED")
                if ok:
                    print("D2 RESOLVED: durable request state; worker moved to next card")
                else:
                    reproduced += 1
                    print("D2 STILL PRESENT on patched variant")
            else:
                has_request_state = any(att["state"] == "PUBLICATION_REQUESTED"
                                        for att in t0["attempts"].values())
                if (nxt.get("task_id") == "T0" and nxt.get("state") == "RESUME_ATTEMPT"
                        and not has_request_state):
                    reproduced += 1
                    print("D2 REPRODUCED: request leaves attempt WORKING; "
                          "poll returns same card; no request state exists")
                else:
                    print("D2 NOT reproduced (F7)")
    print("defects reproduced:", reproduced)
    return reproduced


if __name__ == "__main__":
    sys.exit(main())
