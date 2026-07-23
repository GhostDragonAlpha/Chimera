# Chimera — AGENTS.md

> **This file POINTS. It does not duplicate.** Rewritten 2026-07-16, from 408 lines.
>
> It used to carry its own copy of The Contract, the Feature Ledger, the project
> structure, and the pipeline — all of which `CLAUDE.md` also carried. Three copies of a
> rule is not three times the safety; it is three things to update and two that will not
> be. Both previous attempts to fix that were patches, and the second one's commit
> message is the diagnosis: *"the amendment landed on some lines and not others — agents
> obeyed the stale ones."*
>
> Measured the day this was rewritten: **ten gates had shipped and this file mentioned
> ZERO of them.** Not from neglect — from architecture. A doc that duplicates a fact
> will drift from it, always, and no amount of diligence fixes that. A doc that POINTS
> at a fact cannot drift, because it does not hold one.
>
> So this file now holds **only what nothing else holds**, and points at the rest.

---

## READ THESE, IN THIS ORDER

**New agent? Paste `AGENT_ONBOARDING.md` into your session.** It gets you into the rhythm in under 2 minutes.

| # | Doc | What it OWNS |
|---|---|---|
| 1 | **`CLAUDE.md`** | **THE CONSTITUTION.** The Contract, the gates, Key Paths, conventions, troubleshooting, the full operational infrastructure (task board, sleepwalker, trainer, automation). If a rule is anywhere, it is here. **Read this first every session.** |
| 2 | **`SUCCESSOR_RUNBOOK.md`** | **RECIPES, not principles.** Copy-paste exactly. Read this instead of improvising if you are a less capable model or unsure. |
| 3 | **`WORKFLOW.md`** | **THE FOUNDRY — the dialectical design engine.** The 7-gate internal council, question categories, DESIGN→BUILD cycle, MCP construction. This is HOW you design a feature from scratch when the helm says "build toward the seed." It operates WITHIN the infrastructure described by CLAUDE.md. |
| 5 | **`docs/FARMING_SEASONS.md`** | **THE FARM.** Spring (design) → Summer (build) → Fall (verify) → Winter (reflect). Discrete, repeatable batch processes. Any agent can run any batch. |

**The live state is in none of them.** It is printed by code that reads the actual store:

```powershell
cd E:\PythonChimera\Chimera
python -m core.preflight          # graph health, GPA, board, Will, pains — opens with CAPCOM
python -m core.capcom brief       # the operator channel: unread signals. Reply: capcom tell "..."
python -m core.helm targets       # the ranked seed-vs-reality gap: what to build NEXT
```

---

## THE SESSION, IN FOUR LINES

```powershell
python -m core.circadian tick --run                     # runs the night IFF due; else a no-op
python -m core.preflight                                # DAWN
python -m core.task_board claim --agent <your-id>       # THE single entry. Prints your work packet.
# ... do the ONE thing it gave you, inside the footprint it declared ...
python -m core.task_board done --agent <id> --id tb-N --result "<verbatim evidence>"
python -m core.postflight --phase "..." --result "<UBT verbatim>" --researched "..."
# Update task_progress.md with session block + NEXT list before committing
```

`task_board done` and `postflight` both REFUSE things. **That is the system working, not
breaking.** What each refusal wants is in `CLAUDE.md`; what to DO about it is in
`SUCCESSOR_RUNBOOK.md`.

**The handoff log is `task_progress.md`** — always read it after preflight and write your
session block + NEXT list before committing. The NEXT list invariant: exact commands or a
named feature node + skip-condition per item. An item without a recipe is a wish.

---

## WHAT ONLY THIS FILE HOLDS

### Research Agent (`chimera-research` mode)

Any mode can invoke on-demand web research without going through the Orchestrator. The
Research Agent's ONLY job is to research, search, gather documentation, and return
structured findings. It never writes code.

```python
new_task(mode="chimera-research", message="Research: <your question here>")
```
```
Agent(subagent_type: "mode-research", prompt: "Research: <your query here>")
```

It queries the DNA graph first (`g.query("pathway", ...)`, `g.query("feature", ...)`) and
stops if the answer already exists. Mode definition: `.roo/modes/research-agent.md`.

**Research is not optional and postflight enforces it** (`core/research_gate.py`): cite
`--researched "<sources>"` or record a reasoned `--research-waiver`. It covers
TECHNICAL/INFRASTRUCTURE decisions, not just game assets. **A "Build toward the seed"
task cannot waive it at all** — that task's premise is that the thing does NOT exist, so
nothing in this repo can supply the answer, which is exactly why the task exists.

### Subagent delegation

The Orchestrator compiles a context package (DSL block + graph context + reference
images + campus sources + required endpoints) and delegates. A subagent has full
authority to try 5+ parameter combinations before reporting blocked, and records every
attempt as a `pathway_attempt`. Unknown MCP action → try combos → record all → spawn
research → move on. When solved: record the pathway so the next agent inherits it.

**`blocked` is a verdict that must be EARNED**, and bare `blocked` is forbidden — give a
cause and evidence (`task_board block --reason "..."`), or run `core/solver.py`. But note
the boundary this file used to get wrong: it said *"never ask for human help"* full stop.
**The human is one of the two legal terminals.** Taste bottoms out in them and nowhere
else — it is EARNED (`core/trainables/attunement.py: HUMAN_TEST_BAR`), never requested to
dodge work. Refusing to ask about a MEASURABLE thing is right; refusing to ask about
FUN is just guessing.

---

## THE THING TO ACTUALLY UNDERSTAND

**No reference, no verdict.** The system never decides what is good on its own. A human —
or an objective a human authored — supplies the reference; the machine attunes to it and
reports how close it got.

**A claim is not true because it is written down.** Every gate exists because prose said
one thing and the machine did another. `verified` meant nothing until the Witness Gate
demanded an evidence node; the node meant nothing until the **Why Gate** demanded its
chain reach **PHYSICS** or **THE HUMAN** — the only terminals, because they are the only
answers that need no observer. **An LLM is never a terminal**: its answer is another
claim, so the walk recurses past it (`python -m core.why --feature X --loop`).

**A file existing is not proof — you wrote the file.** A compile is not proof (H-14). A
verb needs behavior, not metadata (H-21).
