"""ci_determinism.py -- assert the physics verdicts are STABLE across runs.

MEMBRANE (Rule 0, stated before the build):
  STATEMENT : the engine is deterministic; the same primitive/action, asked the same
              question from the same initial condition, returns the same VERDICT every run.
  PREDICTION: across N repeated runs, every item's verdict (pass / refused / fail) is
              identical run-to-run.
  FALSIFIER : any item whose verdict FLIPS between runs -> the harness exits non-zero.
              (A stable FAIL or stable REFUSED is NOT a flip; pre-existing gaps are allowed
               to be stably wrong. Only non-determinism is a defect.)

Run:  python tools/ci_determinism.py [N]
  N = number of repetitions (default 3).
Prints a JSON stability report and exits 0 if every item is stable, 1 otherwise.
"""
from __future__ import annotations

import json
import sys

import tools.action_tests as at
import tools.primitive_tests as pt


def _verdict(meta):
    """Call one registered item and reduce its result to a stable label."""
    try:
        r = meta["fn"](None)
    except Exception as exc:  # noqa: BLE001 - a crash is itself a verdict to track
        return f"error:{type(exc).__name__}"
    if r.get("pass_"):
        return "pass"
    if r.get("refused"):
        return "refused"
    return "fail"


def _collect(kind, registry, n):
    runs = []
    for _ in range(n):
        runs.append({name: _verdict(meta) for name, meta in registry.items()})
    # transpose to per-item verdict lists
    items = {}
    for name in registry:
        items[name] = [run[name] for run in runs]
    return items


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 3

    actions = _collect("action", at.ACTIONS, n)
    primitives = _collect("primitive", pt.PRIMITIVES, n)

    report = {"runs": n, "actions": {}, "primitives": {}}
    unstable = []
    for kind, items in (("actions", actions), ("primitives", primitives)):
        for name, verdicts in items.items():
            stable = len(set(verdicts)) == 1
            report[kind][name] = {"verdicts": verdicts, "stable": stable}
            if not stable:
                unstable.append(f"{kind}:{name}")

    report["stable"] = not unstable
    report["unstable_items"] = unstable

    print(json.dumps(report, indent=2))
    if unstable:
        print(f"\nNON-DETERMINISTIC: {len(unstable)} item(s) flipped verdict across runs: {unstable}")
        return 1
    total = len(actions) + len(primitives)
    print(f"\nDETERMINISTIC: {total} items stable across {n} runs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
