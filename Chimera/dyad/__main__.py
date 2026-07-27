"""Hybrid Dyad package entry point.

Quick start (three terminals):

  # terminal 0 — optional: seed a task (or pass --task to agent A)
  python -m dyad seed "Design a minimal REST ping endpoint in Python"

  # terminal 1
  python -m dyad.agent A "You are Agent A, a pragmatic engineer. Propose concrete code/design."

  # terminal 2
  python -m dyad.agent B "You are Agent B, a rigorous critic. Challenge assumptions, find bugs, improve."

Both windows watch dyad/ledger.json, read each other's output, and write
whenever they want. The orchestrator task (seeded above) keeps them aligned.
"""

from __future__ import annotations

import argparse

from dyad.ledger import append, entries, reset


def seed(task: str) -> None:
    append("ORCH", "task", task)
    print(f"orchestrator task seeded: {task}")


def show() -> None:
    for e in entries():
        print(f"{e['n']:>3} [{e['who']}/{e['kind']}] {e['text'][:120]}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Hybrid Dyad control")
    sub = ap.add_subparsers(dest="cmd")
    s = sub.add_parser("seed", help="write an orchestrator task")
    s.add_argument("task")
    sub.add_parser("show", help="print the ledger")
    sub.add_parser("reset", help="wipe the ledger")
    args = ap.parse_args()

    if args.cmd == "seed":
        seed(args.task)
    elif args.cmd == "show":
        show()
    elif args.cmd == "reset":
        reset()
        print("ledger reset")
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
