# Chimera — AGENTS.md

<!-- CHIMERA-LAW -->
> **RULE 0 — EVERY MEMBRANE IS A THEORY. STATE IT BEFORE YOU BUILD IT.** Three parts, all three
> required: a **STATEMENT** someone could disagree with · a **PREDICTION** you have not measured
> yet · a **FALSIFIER** named *before* the run. **A description survives any result; a theory can
> lose.** No falsifier, no build.
>
> **RULE 1 — DERIVE IT BEFORE YOU TRAIN IT.** A parameter sweep is an admission the derivation was
> not done. Before any run, any sweep, any "let's try N variants": trace the variables and show the
> equations close. If you are choosing a number, you broke the chain and substituted taste for a
> law. Ask what QUESTION each variant answers — if the answer is "which number is best", STOP.
>
> **RULE 0 IS ENFORCED AT S-1 VALIDATE** — every port tested alone, and `port_test()` REFUSES to
> register a test that names no falsifier. The model it feeds: `docs/THE_COMPILER.md` — ports →
> primitives → programs → parser → runtime → calibration.
>
> **[docs/THE_LAW.md](docs/THE_LAW.md)** · the method: `docs/THE_WORKFLOW.md` §0
> · 26 rules: `Chimera/docs/EXPERIMENTAL_METHOD.md` · gate: `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

> **This file POINTS. It does not duplicate.** Rewritten 2026-07-16, from 408 lines.
> Amended 2026-08-03 (operator delegation): the retired task-board session shape removed —
> one contradiction, found the way this file predicted, fixed by pointing.
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

**New agent? Paste `ChimeraEngine/ONBOARDING.md` into your session.** It is the single
onboarding: you are the PHYSICS (you own rendering + the workflow), the HUMAN side is the
operator + LM Studio's vision, and a proof is a dyadAnalysis (a number and a term, aligned).
You build THROUGH the engine.

Then the reading list `CLAUDE.md` owns — `docs/THE_LAW.md` → `docs/THE_WORKFLOW.md` →
`docs/THE_COMPILER.md` → `docs/THE_PIECES.md` → `story/README.md` — then `CLAUDE.md` itself
for Key Paths, hardware traps, and conventions. **The rule index is `docs/THE_LAW.md`'s
last section** — every rule, one line, with its enforcer and its canonical home.

> **Retired (2026-07-23): the Unreal Engine pipeline and its task-board session shape.**
> `SUCCESSOR_RUNBOOK.md`, `docs/FARMING_SEASONS.md`, `task_progress.md`, and the
> `core.preflight` / `core.task_board` / `core.postflight` / `core.circadian` loop that used
> to be prescribed here were removed from this file 2026-08-03. The modules still exist
> under `Chimera/core/`, and the GATES (research, witness, why, training) remain live
> machinery cited by `Chimera/docs/THE_FORMULA.md` — but the session is no longer entered
> through them. `WORKFLOW.md` (the foundry) no longer exists; `docs/THE_WORKFLOW.md` is the
> method.

## THE SESSION

The day is `docs/THE_WORKFLOW.md`'s loop: **ORIENT → NEXT → PROVE(X) → CHECK → COMMIT**.
The live state is printed by code that reads the actual store:

```bash
python story/grow.py --read --depth 2    # the tree as it stands
python story/timeline.py                 # containment vs chronology
python tools/methodology_gate.py         # every membrane against the workflow
```

Through the engine (MCP — `ChimeraEngine/MCP_ENGINE.md`): `orient` first, every time;
`next` hands you the term — you do not pick it.

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

**Research is not optional** — it is an S4 enforcer (`Chimera/docs/THE_FORMULA.md`;
`Chimera/core/research_gate.py`). It covers TECHNICAL/INFRASTRUCTURE decisions, not just
game assets. **A "Build toward the seed" task cannot waive it at all** — that task's
premise is that the thing does NOT exist, so nothing in this repo can supply the answer,
which is exactly why the task exists.

### Subagent delegation

A subagent has full authority to try 5+ parameter combinations before reporting blocked,
and records every attempt so the next agent inherits the pathway instead of re-paying for
it. **`blocked` is a verdict that must be EARNED** — bare `blocked` is forbidden; give a
cause and evidence, or run `core/solver.py`. But note the boundary this file used to get
wrong: it said *"never ask for human help"* full stop. **The human is one of the two legal
terminals.** Taste bottoms out in them and nowhere else — it is EARNED
(`core/trainables/attunement.py: HUMAN_TEST_BAR`), never requested to dodge work. Refusing
to ask about a MEASURABLE thing is right; refusing to ask about FUN is just guessing.

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
