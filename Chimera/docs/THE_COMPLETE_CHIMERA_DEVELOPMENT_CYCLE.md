# The Complete Chimera Development Cycle — THE CONTRACT

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
> **[docs/THE_LAW.md](../../docs/THE_LAW.md)** · the method: `docs/THE_WORKFLOW.md` §0
> · 25 rules: `Chimera/docs/EXPERIMENTAL_METHOD.md` · gate: `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

> **What this doc is for: INTENT. Not state, not procedure.**
>
> It was 469 lines and it lied, because it tried to be both. Rewritten 2026-07-16 on one
> rule, learned the hard way and measured:
>
> **A claim about INTENT does not rot. A claim about STATE rots by construction.**
>
> "The Dot: presence before action" was written months ago and is still true — it is a
> DECISION, and decisions do not go stale. "DNA Nodes: ~1280 · GPA 3.5 · build trend
> 20/20" was true for about a day; the real numbers when this was rewritten were **2,546
> nodes and GPA 1.8, flat**. Same doc, same MANDATORY heading, one half durable and one
> half false — and the false half is the one an agent would act on.
>
> So: **this doc holds intent and POINTS at everything else.** Anything a command prints
> is a pointer to that command, never a copy of its output. A copy is a snapshot, and a
> snapshot is a lie with a start date.
>
> **THE DEEPER REASON, which is the studio's own finding (2026-07-16):** *the reasoning
> trace is the code.* Measured across this repo — of 31 heuristics, the 18 that became
> mechanism (named in `core/`) are alive; the 13 that stayed prose degenerated into the
> same auto-generated sentence with the nouns swapped. Every part of THIS doc that became
> code is alive (the curriculum, the circadian, preflight). Every part that stayed prose
> rotted. **You cannot fix that by writing better prose.** You can only make it
> executable, make it a pointer, or delete it. This rewrite does the last two; the first
> already happened, and that is what hollowed the doc out.

---

## THE LIVE STATE IS NOT IN THIS FILE

There is no "Current Project State" section any more. There was one, dated
`2026-07-06`, and it was wrong within a day. The state is printed, on demand, by code
that reads the actual store:

```powershell
python -m core.preflight        # graph health, GPA, board, Will, pains, queues, CAPCOM
python -m core.capcom brief     # the operator channel — unread signals
python -m core.helm targets     # the ranked seed-vs-reality gap: what to build NEXT
python -m core.why --assertions # which finalized claims nobody ever asked WHY about
```

There is no "IMMEDIATE NEXT STEP" section either. There was one. It said *"Start at
Phase 0, Step 0.0... Begin education with School 1"* — a kickoff instruction from the
week the project began, still sitting under a MANDATORY heading ten days later, ready to
send an agent back to school. **The next step is whatever the helm says it is.**

---

## THE GROWTH PATTERN: THE SPIRAL

The game grows from a single point outward. Each loop is a layer of interaction, wider
than the last but always connected back to the centre.

```
Loop 0 (Player) → Loop 1 (Ground) → Loop 2 (Verbs) → Loop 3 (Sky) → ... → Loop 9 (Universe)
     │                │               │              │                  │
     └─── Verified ───┴───────────────┴──────────────┴──────────────────┘
```

**The Dot (Loop 0):** The player. One character. One suit. One set of materials.
Presence before action. The seed from which everything grows.

**Loop 1:** The Ground — the dot touches something. Sand. Rock. Metal. Footprints.
Particles. Sound.

**Loop 2:** Basic Verbs — look, step, bend, pick up, drop, shovel. The simplest
interactions.

Loops 3–9 widen from there. **The seed is `CHIMERA_VISION.py`, and the helm
(`core/helm.py`) measures the gap between it and the live project** — that measurement,
not this list, is what decides the heading.

---

## THE PILLARS — CHOOSE THE RIGHT RESOLUTION

For every task, balance these disciplines:

- **Mathematics** — Compiles zero errors. Deterministic. Provable.
- **Physics** — Feels real at 60fps. The engine is the measurement device.
- **Biology** — Same bug never twice. The DNA learns and immunizes.
- **Psychology** — The human is heard. Connection without exploitation.
- **Sociology** — The rain is free. Accessible but safe.
- **Philosophy** — The soul in the code. Meaning without harm.

**And the one that outranks them: NO REFERENCE, NO VERDICT.** The system never decides
what is good on its own. A human — or an objective a human authored — supplies the
reference; the machine attunes to it and reports how close it got. Only **physics**
yields verifiable data with no observer. You can measure whether there is something to
master. **You cannot measure whether mastering it feels good** — that question is the
human's, and it is EARNED (`core/trainables/attunement.py: HUMAN_TEST_BAR`), never
requested.

---

## THE VOICE

When you report, speak with attention. Do not judge. Do not celebrate falsely. Do not
summarize away the truth. Push back when something is wrong. Celebrate quietly when
something is right.

---

## EVERYTHING ELSE IS CODE NOW — GO THERE, NOT HERE

Each of these was once a long prose section in this file. Each was replaced by something
that RUNS, and the prose kept describing the old shape until it was simply false. The
code is the spec; this table is a pointer, and a pointer cannot drift.

| This doc used to say | It is really | Where it lives |
|---|---|---|
| **THE 13 SCHOOLS** (110 lines of curriculum) | The Curriculum a FEATURE graduates through, K→PhD. The 13 schools exist **nowhere in code** — this section described a system that had already been replaced. | `core/curriculum.py`, `docs/curriculum/curriculum.json`, `docs/GAUNTLET.md` |
| **SIX PHASES OF THE DEVELOPMENT CYCLE** | The circadian rhythm: **Dawn** (wake/preflight) · **Day** (build) · **Dusk** (the Will/postflight) · **Night** (dream_loop). Four, not six. | `core/circadian.py`, `docs/GENERATION_PROTOCOL.md` |
| **FEATURE LEDGER (60+ features)**, hand-listed | The DNA graph — SQLite + FTS, `record_*` helpers only, never a hand-written dict. | `core/graphify_interface.py`, `core/dna_sqlite_backend.py` |
| **PRE-FLIGHT: 6 × `g.query(...)`** | `python -m core.preflight` does all of it in one command (the `g.query` API is still live and still works — it is superseded, not dead). | `core/preflight.py` |
| **POST-FLIGHT: report and record** | `python -m core.postflight` — and it now REFUSES: Research → Generator Guard → Witness → **Why** → Visual → Training → Coin → Council. | `core/postflight.py` |
| **THE CONTRACT's rules** (duplicated here, in `AGENTS.md`, and in `CLAUDE.md`) | **`CLAUDE.md` owns them.** Three copies is why all three drifted; the copies are gone. | `CLAUDE.md`, `ChimeraEngine/ONBOARDING.md` |
| **MCP Pathway Query Rule** | Proven pathways + TRAPS, maintained as data. | `docs/MCP_PATHWAYS.md` |
| **THE RALPH WIGGUM LOOP** | Real, and it runs. | `core/ralph_loop_harness.py` |
| **EMOTION-TO-PARAMETER MAPPING** | Physicalized — emotion is measured through the body, not asserted in a table. | `core/attunement.py`, `core/trainables/attunement.py` |

---

## THE ONE RULE THIS DOC EXISTS TO STATE

**A claim is not true because it is written down.** Every gate in this studio exists
because prose said a thing and the machine did another:

- `verified` meant nothing until the **Witness Gate** demanded an evidence node.
- An evidence node meant nothing until the **Why Gate** demanded that its chain reach
  **PHYSICS** or **THE HUMAN** — the only two terminals, because they are the only
  answers that need no observer. **An LLM is never a terminal**: its answer is another
  claim, so the walk recurses past it.
- A citation meant nothing until `derived_from` had to **RESOLVE**: 14 Observations said
  `accepted` while citing simtest ids that were **typed by hand and never existed**,
  because every consumer tested truthiness, not resolution. **A field can lie; an edge
  cannot** — a graph knows its own ids.

That is the cycle, and it is the only part of this document that is load-bearing:
**write the intent here, put the check in the code, and let the code be the one that
says no.**
