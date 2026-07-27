"""Two independent CLI coding agents that talk to each other via LM Studio.

Run ONE of these in each of two terminal windows:

    python -m dyad.agent A "You are Agent A: a careful senior engineer..." [--task "build X"]
    python -m dyad.agent B "You are Agent B: a rigorous critic/architect..." [--task "build X"]

Each window:
  1. reads the shared ledger (dyad/ledger.json)
  2. sees the other agent's output + the orchestrator's task
  3. thinks via LM Studio (unsloth/qwen3.6-35b-a3b)
  4. appends its own turn (reply / critique / note)
  5. loops, so either agent can speak whenever it wants (hybrid dyad:
     orchestrator task + ping-pong + debate/critique)

This is the ONLY networking layer; the rest is plain file I/O.
"""

from __future__ import annotations

import argparse
import sys
import time

from dyad.ledger import append, entries, last_n, orchestrator_task, reset, since
from dyad.lm_client import Agent, Message

POLL_S = 4.0
MAX_TURNS = 40
MODEL = "unsloth/qwen3.6-35b-a3b"


def _render_history(who: str, seen: list[dict]) -> list[Message]:
    """Turn the ledger into a chat history this agent can reason over."""
    msgs: list[Message] = []
    for e in seen:
        # Each entry becomes a user-role message describing who said what.
        # The agent replies as itself; we don't fake the other agent's role.
        speaker = {"A": "Agent A", "B": "Agent B", "ORCH": "Orchestrator"}.get(
            e["who"], e["who"]
        )
        label = f"[{speaker} / {e['kind']}]"
        msgs.append(Message(role="user", content=f"{label}\n{e['text']}"))
    return msgs


def _system_for(who: str, base_prompt: str, task: str | None) -> str:
    task_line = (
        f"\n\nORCHESTRATOR TASK (work toward this):\n{task}"
        if task
        else ""
    )
    return (
        f"{base_prompt}\n\nYou are {who}. There is another agent and an "
        f"orchestrator in a shared conversation log you can see. Read what they "
        f"wrote, then contribute: advance the work, reply to the other agent, "
        f"or critique their last message. Keep it concise and concrete. When "
        f"the task is genuinely done, say 'DONE:' and summarize the result.{task_line}"
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="Hybrid Dyad CLI agent window")
    ap.add_argument("who", choices=["A", "B"], help="this window's identity")
    ap.add_argument("system", help="base system prompt for this agent")
    ap.add_argument("--task", help="orchestrator task (written once to ledger)")
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--turns", type=int, default=MAX_TURNS)
    ap.add_argument("--reset", action="store_true", help="wipe the ledger first")
    args = ap.parse_args()

    if args.reset:
        reset()
        print(f"[{args.who}] ledger reset.", flush=True)

    # The first window to run with --task seeds the orchestrator task.
    if args.task and not orchestrator_task():
        append("ORCH", "task", args.task)
        print(f"[{args.who}] orchestrator task seeded.", flush=True)

    agent = Agent(args.who, args.system, model=args.model)
    task = orchestrator_task()
    task_text = task["text"] if task else None

    seen_index = 0
    print(f"[{args.who}] online. model={args.model}. polling every {POLL_S}s.",
          flush=True)

    for turn in range(args.turns):
        new = since(seen_index)
        if not new:
            time.sleep(POLL_S)
            continue
        seen_index = new[-1]["n"]

        # Skip our own entries when deciding what to respond to, but always
        # include them in history so context is complete.
        others = [e for e in new if e["who"] != args.who]
        if not others:
            time.sleep(POLL_S)
            continue

        history = _render_history(args.who, entries())
        system = _system_for(args.who, args.system, task_text)

        print(f"\n[{args.who}] thinking... (turn {turn + 1})", flush=True)
        reply = agent.reply(history)

        kind = "critique" if "critique" in reply.lower() or "DONE" in reply else "reply"
        append(args.who, kind, reply)
        print(f"[{args.who}] >> {reply[:200]}{'...' if len(reply) > 200 else ''}",
              flush=True)

        if reply.strip().upper().startswith("DONE:"):
            print(f"[{args.who}] declared DONE. Exiting.", flush=True)
            break

    print(f"[{args.who}] reached turn limit / exiting.", flush=True)


if __name__ == "__main__":
    main()
