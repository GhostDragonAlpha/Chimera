# THE PIECES — everything the workflow is made of, gathered in one place

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
> **[docs/THE_LAW.md](../docs/THE_LAW.md)** · the method: `docs/THE_WORKFLOW.md` §0
> · 26 rules: `Chimera/docs/EXPERIMENTAL_METHOD.md` · gate: `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

> **Why this file exists.** Consolidating documentation is rewriting the workflow, silently, by
> deletion — so before anything was archived, every idea was read out of every document and put on
> one list. This is that list. It is the evidence that the consolidation lost nothing.
>
> **How to read the STATUS column.** `LIVE` = in the working method today. `ORPHANED` = written
> down, load-bearing, and *nothing in the current story/ workflow does it* — these are the real
> findings. `RETIRED` = superseded, kept because the idea outlived the code. `MISSING` = named in
> one document and never built anywhere.
>
> Sources read in full: `Chimera/docs/THE_WORKFLOW.md` · `THE_METHOD.md` · `THE_FORMULA.md` ·
> `THE_LINE.md` · `WORKFLOW_RULES.md` · `THE_COMPLETE_CHIMERA_DEVELOPMENT_CYCLE.md` ·
> `GENERATION_PROTOCOL.md` · `EXPERIMENTAL_METHOD.md` · `THE_GROWTH.md` · `docs/THE_WORKFLOW.md` ·
> `docs/THE_ORDER.md` · `story/README.md` · `story/ONBOARDING.md` · `story/LANGUAGE.md` ·
> `ChimeraEngine/ONBOARDING.md` · plus the retired `sequential_orchestrator.py`, `run_sequential.py`
> and `agents/*.py` recovered from git history.

---

## THE HEADLINE FINDING — there are TWO workflows in this repo and they were never joined

| | **WORKFLOW A** — the FORMULA | **WORKFLOW B** — the CHAPTER |
|---|---|---|
| written | 2026-07-24/25, **"SEALED — do not re-litigate"** | 2026-07-28 onward |
| unit of work | one `camelCase` **term** | one **membrane** (a folder) |
| procedure | `PROVE(X)` = S0–S7 gates | derive → emit → grow → witness |
| completeness | **measured saturation** (Chao2 + dry tail) | *nothing* |
| enforced by | `ChimeraEngine` MCP `prove` + 8 gates | `grow.py`, `chain_witness`, `folding audit`, `methodology_gate`, `timeline`, `training_gate` |
| the tree it works on | `theStory → theSolarSystem → theStation → theGoal` | `story/theZero/…` — **42 real folders** |

**They describe the same method at two different times, and B superseded A in practice while A is
still labelled canonical.** `Chimera/docs/THE_WORKFLOW.md` §9 draws a hierarchy that does not exist
on disk. The engine's `prove` owns the word "proven"; not one of the 42 membranes has passed
through it.

**And the join is where Rule 1's failure lived.** Workflow A's S4 reads:

    S4  PROVE·each   ∀ physics V:  MEASURE( TRAIN( PROGRAM(V) ) )

`PROGRAM → TRAIN → MEASURE`. **There is no DERIVE.** A reward function was programmed, its weights
were trained, the result was measured — every step of S4 satisfied — while the target speed came
from another planet. The formula could not catch it because the formula does not ask where a number
came from once it has been classified `PHYSICS`.

---

## 1 · ROLES AND TERMINALS

| # | the piece | status | source |
|---|---|---|---|
| 1 | **Two authors.** The human writes `story.md` (the NODES); the physics writes `physics.py` (the EDGES). Neither alone is the game. | LIVE | story/README |
| 2 | **Two roles.** The human names one term and owns DECIDE + ENOUGH; the agent owns the hierarchy and the formula. | LIVE | THE_WORKFLOW |
| 3 | **Exactly two terminals: PHYSICS** (a fact true in an empty universe) **and THE HUMAN** (taste). They are the floor of the recursion — without them it is turtles all the way down. | LIVE | THE_METHOD |
| 4 | **An LLM is NEVER a terminal.** Its answer is always another claim, so the walk recurses past it. | LIVE | THE_METHOD |
| 5 | **You are the head of the dragon.** Own every technical decision, execute without asking which wrench. *"Which term?"* and *"which approach?"* are never legal stops. | LIVE | ChimeraEngine/ONBOARDING |
| 6 | **The four legal stops:** proven · a real blocker (name the cause) · a taste decision · the eye is dark and no tier-2 reader is possible. | LIVE | story/ONBOARDING |
| 7 | **NO REFERENCE, NO VERDICT.** The system never decides what is good on its own. | LIVE | CYCLE / THE_WORKFLOW |
| 8 | **Meaning is observer-completed** — checked against a model of the viewer, never a fact of the matter. | LIVE | THE_METHOD |
| 9 | **Fiction is not the forbidden lie.** Keeping the two terminals separate is what lets facts stay true *and* stories stay free. | LIVE | THE_METHOD |
| 10 | **Stage 0 — the demographic.** *Who is this for?* decides WHICH human terminal you aim at. | **ORPHANED** | THE_METHOD |

---

## 2 · THE VERB AND THE UNIT

| # | the piece | status |
|---|---|---|
| 11 | **The verb is PROVE, never "build".** "Prove" forces the definition to be reduced — you cannot prove what you cannot first state precisely. | LIVE |
| 12 | **The only other verb is DECIDE**, for taste. | LIVE |
| 13 | **One `camelCase` term at a time.** camelCase compresses a phrase into an atomic token, collision-free, and it is a SERIAL. A proven term becomes vocabulary for the next. | LIVE |
| 14 | **Setting-first.** Start at the biggest bubble. Jumping to a mid-tree scene is the founding failure. | LIVE |
| 15 | **You do not pick the membrane** — the operator names it, or `next` does. | LIVE |

---

## 3 · THE FORMULA — S0…S7 (Workflow A)

| # | stage | the checkpoint | status |
|---|---|---|---|
| 16 | **S0 FRAME** | X is exactly one claim; the demographic is named | half — atomicity yes, demographic no |
| 17 | **S1 QUESTION** | variables are BORN as the subject of a question; ask until DRY | **ORPHANED** |
| 18 | **S2a PROVENANCE** | `born_of_question(V)` else REJECT — *"you declared it, you did not discover it"* | **ORPHANED** |
| 19 | **S2b SATURATION** | **measured** — Chao2 completeness + a dry tail of K questions, and the curve is RENDERED every run | **ORPHANED** (`core/saturation.py` exists, nothing in `story/` calls it) |
| 20 | **S3 CLASSIFY** | `measure_writable(V)` → PHYSICS · taste → HUMAN · neither → back to S1 | LIVE as `FREE`/derived/`LENS` |
| 21 | **S3b DERIVE** | *(does not exist — this is the hole Rule 1 fell through)* | **MISSING** |
| 22 | **S4 PROVE·each** | researched ∧ trained-not-tuned ∧ witnessed ∧ **looked** | LIVE |
| 23 | **S5 CHAIN** | the why-chain reaches a terminal; the coin's two faces agree | **ORPHANED** for membranes |
| 24 | **S6 DECIDE** | the operator rules — the only place MEANING closes | LIVE |
| 25 | **S7 RECOMPOSE** | the proven parts **reconstitute X** | **ORPHANED** — `layout()` composes, nothing gates it |
| 26 | **The black-hole shape**: descent = the density clock accelerating inward · two singularities · a one-way horizon · no-hair compression · **holographic** — the information is on the boundary, which is the graph of *because*-edges | LIVE (as understanding) |

---

## 4 · THE DYAD — how anything becomes true

| # | the piece | status |
|---|---|---|
| 27 | **PHYSICS → a NUMBER. AN EYE → a TERM, blind. Cross-reference → alignment 0→1.** Two *different kinds* of output are what make the sides independent. | LIVE |
| 28 | **A MONAD IS NEVER PROOF.** Judging your own render, measuring pixels off your own picture, scripting the Engine from a driver — all monads, and all *feel like diligence*. | LIVE |
| 29 | **Identical outputs are the TELL of a false dyad**, not proof. | LIVE |
| 30 | **Bimanual interference** — two "independent" systems that are secretly coupled move together because they are one. Every de-coupling seam exists to prevent it. | LIVE |
| 31 | **The brain is a dyad** — two hemispheres reaching consensus. That is why a dyad is the minimum unit of proof: cognition externalized. | LIVE |
| 32 | **Three eye tiers:** LM Studio vision (standard) · a blind spawned instance (declare the correlated priors) · Alan (the terminal). **Tier 0 — the agent that built it — is never acceptable.** | LIVE |
| 33 | **The eye disagrees ⇒ the PHYSICS is wrong. Start over.** Never widen the tolerance. | LIVE |
| 34 | **The appearance is a MOVIE from the real engine**, beginning→end — not a still, not a diagram. | LIVE |
| 35 | `/live?blind=1` — identical picture, the *"physics expects…"* caption withheld. **Shown the answer, an eye confirms instead of observes.** | LIVE |

---

## 5 · THE LINE — program / train / decide

| # | the piece | status |
|---|---|---|
| 36 | **PROGRAM the rules · TRAIN the numbers · the HUMAN sets the taste.** | LIVE |
| 37 | **The one test that places anything: try to write its `measure()` first.** | LIVE |
| 38 | **You cannot train inside a physics that does not exist yet.** | LIVE |
| 39 | **Program each KIND of cause→effect once; it generates infinite instances.** The rules are few and finite; the instances are unbounded. | LIVE |
| 40 | **Diagnose the TIER before you fix.** A `lat^1.15` law bug looked like a threshold to train. **Do not train away a broken law — fix the law, then train the residual** (0.655 → 0.512 → 0.180). | LIVE |
| 41 | **The complete floor is three things:** engine I/O · each rule/verb · a `measure()` per trainable. Everything above it is trained, generated, or taste. | LIVE |
| 42 | **You cannot train CODE** — ~6 min/eval vs 1.5 ms. Push the game out of code and into data. | LIVE |
| 43 | **The exploit is the product.** A degenerate winner is the optimiser auditing your spec at 35 kHz. **Iterate the objective, never the artifact.** | LIVE |
| 44 | **One rollout is a coin toss** — score N randomized restarts and keep the WORST. | LIVE |
| 45 | **GPU for the population, CPU for development.** Nothing reads back from the GPU inside the rollout loop. | LIVE |
| 46 | **RULE 1 — DERIVE IT BEFORE YOU TRAIN IT.** A sweep is an admission the derivation was not done. THE TELL: if a variant answers *"which number is best"*, stop. | LIVE — `tools/training_gate.py` |

---

## 6 · THE CHAPTER — the grammar of the tree (Workflow B)

| # | the piece | status |
|---|---|---|
| 47 | **A chapter is a folder**: `story.md` · `physics.py` · `numbers.json` · `trained.json` · children. | LIVE |
| 48 | **Path = serial = compressed story.** A `/` reads as "and inside it"; the path IS the sentence. | LIVE |
| 49 | **`theX` = the LAW · `theXs` = the SET · `aX` = the INSTANCE.** | LIVE |
| 50 | **An instance is named by its KIND, and the kind is DERIVED.** `measure()` checks the folder name still matches the class its own physics produces. **The name is a claim, so it is tested like one.** | LIVE |
| 51 | **The plain-words line IS the chapter at that zoom** — not a summary of it. Harvested into every ancestor's `contents.md`, so it is CONSUMED and cannot rot silently. | LIVE |
| 52 | **Exactly four verbs**: `derive` · `emit` · `layout` · `measure`. A fifth operation belongs to a different level. | LIVE |
| 53 | **Gerunds are processes** — `-ing` marks a happening. Objects have extent; processes have duration. | LIVE |
| 54 | **The suffix is the unit, and that is the type system.** `snow_line_au`, `T_orbit_myr`. | LIVE |
| 55 | **A membrane reads ONLY its parent.** private = a `derive()` local · protected = `numbers.json` · **public does not exist**. | LIVE |
| 56 | **A sibling's number comes through the parent, or not at all.** The failure mode is a LITERAL under a comment claiming inheritance (`"T_star_surface": 5772.0`). Hoist it to the parent. | LIVE |
| 57 | **The disguised form is `parent.get("k", 86400.0)`** — it reads as defensive programming and serves a typed value the instant the parent stops carrying `k`. `.get` cannot fail. | LIVE |
| 58 | **`emit()` is read-only.** It may not mint an object. A "star marker" beside a planet is **a moon**, and no moon was derived. | LIVE |
| 59 | **Local units at every membrane** — precision stops being a problem rather than being managed. | LIVE |
| 60 | **`FREE` vs `LENS`.** A FREE dial changes what the world IS and re-derives the subtree; a LENS dial changes only the picture. **Never merge the two panels** — one is a fact you may choose, the other a lie you may see through. | LIVE |
| 61 | **From zero, only ADDITION is legal.** | LIVE |
| 62 | **Containment is not sequence.** A star and its planets happen in order and live at the same level. | LIVE |
| 63 | **Don't invent levels** — `story/HIERARCHIES.md` holds the real paths. | LIVE |
| 64 | **A SCALE step composes; an ASPECT step must not.** `theRockyPlanet → aRockyPlanet → aBlueWorld → theTerrain` is one body four ways, all at extent = R. | LIVE |
| 65 | **Place it even when it is sub-pixel** — that is what makes the tree ONE OBJECT instead of a stack of pictures. | LIVE |
| 66 | **`grow.py` is the enzyme** — the same three moves at every folder. Adding world means adding a chapter, never more machinery. | LIVE |
| 67 | **When a child needs its parent's reasoning, publish a TABLE** (`theHuman` publishes 48 gait samples), never restate the law. | LIVE |

---

## 7 · THE TESTS A CHAPTER MUST PASS — six now, and they were added one at a time

| # | test | the check | added |
|---|---|---|---|
| 68 | **PROVEN** | the math closes **and predicts a fact it was never fitted to** (η + mₑ + 13.6 eV → 3760 K, lit. ~3700) | 07-28 |
| 69 | **VISUAL** | `emit()` in the *same file* as `derive()`, reading the *same numbers*. **No aesthetic passes** — a colour is a measurement. **Sample the video**, not one frame | 07-28 |
| 70 | **LEARNED** | the law fixes the FORM; free numbers are trained against the membrane's own target, never tuned | 07-28 |
| 71 | **BINDABLE** | every number declares its unit — FOLD (dimensional shape) · BOND (exact unit *with offset*) · REGIME (the range it holds over). `python story/folding.py audit` | 07-31 |
| 72 | **CONTROLLED** | push a KNOWN subject through the whole instrument first. `emit()` hands you one free | 08-01 |
| 73 | **DERIVED** | the target existed before the run. `python tools/training_gate.py` | 08-02 |

---

## 8 · THE GATES — a doc can be ignored, a lint cannot

| # | gate | refuses | status |
|---|---|---|---|
| 74 | research | a research-less session with no cited sources | LIVE (`core/research_gate.py`) |
| 75 | witness | `verified` with no observation node | LIVE |
| 76 | visual → the human dyad | a render no independent mind judged | LIVE |
| 77 | training | closing a game task with the subject un-trained | LIVE |
| 78 | why | a claim whose *because*-chain never reaches a terminal | LIVE (`core/why_gate.py`) — **not wired to `story/`** |
| 79 | coin | a claim and its evidence that do not agree BOTH ways | LIVE — **not wired to `story/`** |
| 80 | objective | a trainer objective the optimiser can exploit | LIVE (`core/objective_lint.py`) |
| 81 | **saturation** | **DRY asserted instead of measured** | **ORPHANED** — exists, unused by `story/` |
| 82 | folding | a Kelvin bonded to a Celsius; a fraction above one | LIVE |
| 83 | methodology | a membrane failing form/derives/emits/free/units/one-name/typed/predicts | LIVE |
| 84 | timeline | two orderings that disagree | LIVE |
| 85 | training (Froude) | a target that belongs to another planet | LIVE |
| 86 | **MANDATORY GATES, NO FALLBACK LADDERS, NO SILENT CONTINUATION.** A gate failure exits non-zero and halts. Exit contract: 0 complete · 1 gate violation · 2 unexpected. | LIVE |

---

## 9 · THE DAY — the circadian loop

| # | the piece | status |
|---|---|---|
| 87 | **Dawn** (preflight — read live state) · **Day** (build) · **Dusk** (the Will — what this generation sacrificed to learn, and where it predicts the approach fails) · **Night** (`dream_loop` distills failures + surprises into **at most 2** candidate heuristics) | **RETIRED** — and the Night is the piece worth reviving (see §12) |
| 88 | **Capture surprises LIVE**, as they happen — `graphify_record surprise`. These are dream fodder no failure node captures. | RETIRED |
| 89 | **The Gardener is AUTOMATED; the human vetoes AFTER.** A veto is law, never argued, and stays a tombstone. | RETIRED |
| 90 | **Memory shedding, never deletion.** Archive; never delete. | LIVE (as a principle) |
| 91 | **NO DEAD ENDS** — a blocker fails the ITEM, never the SHIFT. Bare "blocked" is forbidden: evidence or a reasoned waiver. | LIVE |
| 92 | **ANTI-IDLE** — a tick with no state delta outputs one line and ends, never a full re-report. | LIVE |
| 93 | **Fork before researching** — 3 briefs (conservative / alternative / wild), winner proceeds, losers' autopsies are recorded tuition. | RETIRED |

---

## 10 · WHAT TO BUILD NEXT

| # | the piece | status |
|---|---|---|
| 94 | **The six directions from the anchor** — DOWN (what are they standing on?) · FORWARD (what draws them onward?) · UP (the scale of the place) · LEFT/RIGHT/BACK (what holds it together?). **Work one at a time. Build nothing that no direction asked for.** | ORPHANED |
| 95 | **The six directions are the PORTS of a cell**, typed by WHAT FLOWS, so `work_queue()` is the world's to-do list **enumerated rather than authored**. | ORPHANED |
| 96 | **Proxemics, not travel.** Detail is budgeted by *perceived* distance (arm's reach / personal / social / horizon). **Distance travelled is not a consideration** — void is correct. | ORPHANED |
| 97 | **When all six are filled: MIGRATE.** The universe expands because the current one is *saturated*. | ORPHANED |
| 98 | **Development order = play order.** Build along the story dial from t=0. | LIVE (as the timeline) |
| 99 | **Everything is TWO ENDS AND A DIAL** — and the story is simply the outermost dial, with **GATES** on it (a measurable condition, never a flag someone sets). | LIVE |
| 100 | **It is scale-invariant.** The same six questions at regolith, cockpit, orbit, interstellar. | ORPHANED |

---

## 11 · THE FIVE RULINGS + THE CREED

| # | the piece | status |
|---|---|---|
| 101 | **Everything is a sample that you train.** No surface may have less fidelity than a measured scan of its class provides. | LIVE |
| 102 | **Research connects the physics to the training data.** Effort is spent on a subject ONCE, then reused infinitely. | LIVE |
| 103 | **The physics is the code.** No library call terminates a law. Proven by deriving it yourself or from official scientific sources. | LIVE |
| 104 | **The natural world is a combination of ALL of the known.** A membrane ignoring a governing row is incomplete by construction. | LIVE |
| 105 | **The standard of definition is measured capture.** D0 proven function · D1 ~1 mm · D2 ~0.3 mm · D3 histology · D4 out of scope. | LIVE |
| 106 | **Children are legal two ways: RE-SEED or MIX**, both inside the measured envelope. Extrapolation is an invention that must prove itself. | LIVE |
| 107 | **`measure → sample → prove`, never `generate → trust`.** | LIVE |
| 108 | **HIERARCHY × PHYSICS × HUMAN — a product, not a sum.** It is also the debugger: **you do not argue quality, you find the zero.** | LIVE |

---

## 12 · DOCUMENT DISCIPLINE — the pieces that govern this file itself

| # | the piece | status |
|---|---|---|
| 109 | **A claim about INTENT does not rot. A claim about STATE rots by construction.** | LIVE |
| 110 | **THE REASONING TRACE IS THE CODE.** Measured across this repo: of 31 heuristics, the **18 that became mechanism are alive**; the **13 that stayed prose degenerated into the same auto-generated sentence with the nouns swapped**. | LIVE |
| 111 | **You cannot fix that by writing better prose.** You can only **make it executable, make it a pointer, or delete it.** | LIVE — *this is the consolidation law* |
| 112 | **Point at the command, never copy its output.** A copy is a snapshot, and a snapshot is a lie with a start date. | LIVE |
| 113 | **A rule nothing checks is prose.** | LIVE |
| 114 | **Every rename travels with its consumers in ONE commit.** Grep `parent["<key>"]` first. | LIVE |
| 115 | **THE DRIFT PATTERN: a new thing was added BESIDE the old thing instead of replacing it.** Renamed scripts left launchers pointing at ghosts; fixed agents saved as `_fixed` beside broken ones. *"The remedy is not more documentation — it is deleting the losers once a winner exists."* | LIVE — **and it is exactly what happened to the two workflows** |
| 116 | **A systematic pattern is ONE decision, not N edits.** Count the pattern before fixing instances. | LIVE |

---

## 13 · THE RETIRED SEQUENTIAL WORKFLOW — what it was, and why it died

Recovered from git (`run_sequential.py`, `sequential_orchestrator.py`, `agents/*.py`). Its shape:

```
research → visual validation → recombination → integration → documentation
   ^                                                              │
   └────────────────── continuously looping ─────────────────────┘
```

Five stations, one at a time, in order, forever, each with a timeout, each logged, and **one
station failing did not kill the chain.** That is a closed loop that runs without a human, which is
something the current workflow does not have.

**It was destroyed by its own agents, and both mechanisms are worth keeping on this list:**

1. **A station reported success on absence.** `integration_agent.py`, verbatim:

   ```python
   except ImportError as e:
       print(f"Membrane shapes not available yet: {e}")
       print("This is expected - membrane integration will be tested later")
       return True  # Not a failure, just not ready
   ```

   A test that returns `True` when the thing under test does not exist. Every cycle reported green.

2. **`documentation_agent.py` wrote prose STATE.** It PREPENDED a hand-authored block to
   `task_progress.md` every loop — *"Agents executing in order… Next automated tasks…"* — claims
   about what was happening, unverified, accumulating forever. That is piece #109 being violated by
   a program.

**The correct reading is not "automation is dangerous".** It is that the loop was built *before*
the gates existed. Green-on-absence is exactly what the **witness gate** refuses; prose state is
exactly what piece #112 forbids. The loop's shape is sound and its stations are now available in
verified form.

---

## 14 · THE ORPHANS, RANKED — what this gathering actually found

Nine things are written down, load-bearing, and **not done by anything in the current workflow.**

| rank | the orphan | why it matters | where it lives |
|---|---|---|---|
| 1 | **S1 QUESTION + S2 SATURATION** | A membrane's variable set is currently whatever the author thought of. The formula calls that *"declared, not discovered"* and makes it a **thrown error**. `core/saturation.py` measures it and nothing in `story/` calls it. **Its missing half was FOUND — see §15.** | THE_FORMULA §S2 |
| 2 | **S3b DERIVE** | The stage that does not exist, that Rule 1 exists because of. Between CLASSIFY and PROVE there must be *"where did this number come from, and is it true where it now stands?"* | this document |
| 3 | **S7 RECOMPOSE** | `layout()` composes children into a parent and **nothing checks that the parent is thereby proven.** A parent can be green while its children are hollow. | THE_FORMULA §S7 |
| 4 | **S5 CHAIN / the coin** | `why_gate` and `coin_verifier` are built and are not wired to a single membrane. | THE_WORKFLOW §7 |
| 5 | **The NIGHT phase** | All 24 experimental rules were written **by hand, after a failure, by whichever context happened to notice.** The circadian loop had automation for exactly this and it is switched off. | GENERATION_PROTOCOL |
| 6 | **The six directions** | The only thing in this repo that answers *"what next"* by design rather than by whatever is broken. | docs/THE_WORKFLOW §6 |
| 7 | **Stage 0 — the demographic** | Never asked for any membrane. | THE_METHOD |
| 8 | **Capture surprises LIVE** | Every correction in this session is a surprise nobody recorded. | GENERATION_PROTOCOL |
| 9 | **`work_queue()`** | The world's to-do list, enumerated from unfilled ports rather than authored. Built (`core/bricks.py`), unused by `story/`. | docs/THE_WORKFLOW §7.4 |

---

---

## 15 · THE FOUNDRY — the orphaned S1, already written, hidden under a retired pipeline

`WORKFLOW.md` at the repo root is titled *"GAUSSIAN FOUNDRY — AGENT WORKFLOW"* and reads, on the
surface, like a dead UE5 document: MCP session headers, port 3000, `UnrealEditor.exe`. Underneath
that is **the concrete implementation of the stage this method has been missing** — not the
principle that variables must be discovered, but the actual list of what to ask.

| # | the piece | status |
|---|---|---|
| 117 | **22 question categories in four groups.** **NODE** (13 — what IS this) · **EDGE** (5 — how does it RELATE: depends_on, proves, derived_from, conflicts, requires) · **MIRROR** (4 — why does it EXIST: vision, tradeoff, evidence, **terminal**) · **META** (5 — where does it FIT: depth, breadth, parent, priority, dependency). | **EXTRACTED → S1** |
| 118 | **MIRROR's `terminal` asks, per variable, whether it bottoms out at PHYSICS or THE HUMAN** — S3 asked early enough to be cheap. | **EXTRACTED** |
| 119 | **META's `depth` is what says "this needs a deeper zoom."** A membrane whose META answers demand more zoom is a membrane that should have children — **the tree deciding its own shape** rather than an author deciding it. | **EXTRACTED** |
| 120 | **The council's seven gates:** `Frame → 10Q → Answer → 10Q → Answer → Saturate → Spec`. Two rounds, because the second round's questions are the ones the first round's answers made askable. | **EXTRACTED** |
| 121 | **THE RHYTHM.** ask → answer *with evidence* → ask again from what you learned → repeat. **"Never stop at 'task done.' A task is just one answer."** The session ends when the human stops you, not when a box is checked. | **EXTRACTED** |
| 122 | **Tool hierarchy, fastest first:** your own context before any API call. | LIVE (as practice) |
| 123 | **"The graph lives on disk, not in your head. Never assume state — read it."** | LIVE (as ORIENT) |
| 124 | **"Build from answers, not from scratch. The graph IS the design. Implement literally."** | LIVE |

**The lesson is #115 in reverse.** The drift pattern says a new thing gets added beside the old one;
this is the other half of the same cost — **a live idea gets buried inside a dead document and
becomes invisible.** The Foundry's question set was not superseded by anything. It was never
carried across when the UE pipeline was retired, and S1 has been orphaned ever since.

---

## 16 · THE PORT LEDGER — the instruction set, and what is actually validated

**Added 2026-08-02.** The compiler framing (`docs/THE_COMPILER.md`) is the operating model, and it
makes the ledger's job concrete: **a layer is only as true as the layer below it has been measured
to be.** This section is that measurement. Everything here has a falsifier that was named before
the run.

### Layer 1 — PORTS · **12 / 12 validated**

| # | port | measured |
|---|---|---|
| 125 | RIGID_BODY | 0.00000% against the DISCRETE integrator (the continuous form is 1.769 mm out) |
| 126 | CONTACT | 29.6404 N predicted, 29.6404 measured |
| 127 | HILL_MUSCLE | ratio 1.984 vs 2.000; `t63` 15.0 ms vs `tau_act` 15.0 ms |
| 128 | SPINDLE | length-vs-integral drift 0.0000% |
| 129 | JOINT_LIMIT | 0.860° overshoot under 400 N·m — **was 3.566° before passive tissue** |
| 130 | PASSIVE_FORCE | 1.84 / 1.92 / 225.89 N·m at 10/50/90% of range — **was identically 0.00000** |
| 131 | TENDON_ELASTICITY | 0.221 N at zero activation over 100.6 mm |
| 132 | FORCE_VELOCITY | `f_v` = 0.8324 shortening |
| 133 | GTO | monotone: 2.2 / 147 / 293 / 438 / 584 N |
| 134 | OTOLITH | `g·sin` and `g·cos` both 0.0000% off |
| 135 | PLANTAR_PRESSURE | 71.65 N loaded, 0.000000 lifted |
| 136 | PHASE_OSCILLATOR | 2.6e-12 rad coupled vs π uncoupled |

**PORTS 5 AND 6 WERE ONE FINDING, NOT TWO FAILURES: the body had no ligaments.** With no passive
tissue the hard constraint carried the entire end-range load. Passive tissue was derived and
installed the same day (`tools/world.py::derive_ligaments` — 10 ligaments derived, **2 refused by
name** because the gap fell inside the gait envelope's own sample grain), and both ports closed.

> **This entry supersedes the snapshot "ten validated, two failing."** The two failures were the
> instruction that was missing, and it is no longer missing.

### Layer 2 — PRIMITIVES · **7 / 7 validated**, all 12 ports covered

| # | primitive | status |
|---|---|---|
| 137 | END_STOP · joint_limit + passive_force + tendon_elasticity | **PASS** — 0.860° vs 3.574° ablated |
| 138 | DAMPING · hill_muscle + force_velocity | **PASS** — −28.54 J absorbed; 1.1% left at 1/100 speed |
| 139 | LOAD_RELIEF · hill_muscle + gto | **PASS** — 2440 N vs 4896 N, 50.2% relieved |
| 140 | RHYTHM_DRIVE · phase_oscillator + hill_muscle | **PASS** — correlation −0.689, swing 81.5° vs 6.2° |
| 141 | STIFFNESS · hill_muscle + spindle | **PASS** — ankle bench: 2.07° closed vs 16.44° open (8.0×) |
| 142 | WEIGHT_TRANSFER · rigid_body + contact + plantar_pressure | **PASS** — totals 537–613 N of 581 (12.4%), share moves 79 pts |
| 143 | UPRIGHT · hill_muscle + otolith | **PASS** — RMS lean 10.37° true vs 14.05° with the signal inverted |

**141–143 were three INSTRUMENT faults, not mechanism faults, and each is recorded in
`tools/primitive_tests.py` at the test it fixed:** STIFFNESS had conflated muscle STRENGTH with
feedback DIRECTION (and the knee cannot host this question — its strong muscles and its gravity
load point the same way; the bench moved to the ankle). WEIGHT_TRANSFER stood its statue on a
mid-gait keyframe, overwrote the root orientation to lean it, and let it keep momentum; it now
stands on the symmetric default pose, seats at 4 mm penetration, composes the lean, and relaxes
with no momentum. UPRIGHT's matched-mean ablation was structurally blind for a proportional loop
at equilibrium (a constant IS the mean of the feedback) and its drive direction was inverted; the
ablation is now the signal destroyed — the same loop reading the gravity vector inverted.

### Layer 3 — ACTION PRIMITIVES · **9 / 11 validated, 1 REFUSED** (`tools/action_tests.py`)

| # | action | status |
|---|---|---|
| 155 | SWING — `T = 2π√(I/(m g d))` | **PASS** 1.7093 s vs 1.7929 predicted (4.7%) |
| 156 | THROW — `R = v² sin(2θ)/g` | **PASS** 5.0089 m vs 5.0102 (0.03%) |
| 157 | LAND — `J = m√(2gh)` | **PASS** 147.08 vs 138.03 N·s (6.6%) |
| 158 | TURN — `ΔL_z = 0` under internal drive | **PASS** 0.0415 vs 41.82 for the external control |
| 159 | STANCE — `Σplantar = (1−s)W` | **PASS** fitted slope −583.7 N vs −W = −580.5 |
| 160 | PUSH — `F_slip = μN` | FAIL, honest — slid at 137.9 N against a 348.3 N bound: the cone never set this bound (ankle-height control 480.1 N, above μN; toe/heel capsules tilt contact normals) |
| 161 | LIFT — `0 < efficiency ≤ 1` | **PASS**, and flagged WEAK in its own output |
| 162 | BALANCE — `ω₀ = √(g/H)` | **PASS** 2.7500 vs 2.7423 rad/s (0.3%) — solver pivot (`connect` equality on `calcn_r`), exact cosh fit over honest samples |
| 163 | PULL — isotropic friction | FAIL, honest — 137.9/88.1 N (36.2% apart, bar 25%): **foot geometry, not harness** (ankle-height control 480.1/157.7 N = 67.1%; sustained slides, μ = 1.000 on every geom) |
| 164 | STEP — one foot takes what the other drops | **PASS** L 0.0/R 347.1 N vs 348.3 predicted (2.0%) — contact-force ground truth, not the touch zones |
| 165 | CROUCH — `τ = W_above × lever`, two routes | **PASS** 37.22 vs 40.76 N·m (8.7%) — a crouch is a POSE, not a knee angle: closed-form squat (hip/knee/ankle = 22.5/45/22.5°), braced AT the pose |
| 166 | GRIP | **REFUSED** — 47 joints, not one shoulder, elbow, wrist, thumb or finger |
| 167 | **PREDICTION is now a required registration field.** `port_test`/`primitive_test` enforced only STATEMENT and FALSIFIER, so the number could be written after the run. `action_test` demands all three at import. | LIVE |
| 168 | **THE BRACE.** Teleporting `qpos` reports 8344 N against a predicted 290; an explicit PD loop NaNs at 6 ms; `jnt_stiffness`+`dof_damping` is integrated implicitly and works. K derived, deviation reported. | LIVE |
| 169 | **Four vacuous passes caught** — PULL comparing two ramp ceilings, STEP unloading a foot that carried nothing, STANCE blaming the keyframe's defect on its brace, SWING timing a teleported pendulum. | LIVE (as the lesson) |

### Layers 4–6

| # | layer | status |
|---|---|---|
| 145 | PARSER — intent → program, ~12 buttons over one input-agnostic formula layer | **DELIBERATELY LAST** — the only layer that cannot be wrong in an interesting way |
| 146 | RUNTIME — `dx/dt = f(x,u,p,w)`; `w` from `tools/world.py` and nowhere else | LIVE |
| 147 | CALIBRATION — `p` splits DERIVED / INGESTED / TRAINED, never chosen | LIVE (`tools/training_gate.py`) |

### The universal passive-tissue framework — **SPECIFIED, ZERO PORTS VALIDATED**

| # | the piece | status |
|---|---|---|
| 148 | **Passive tissue is universal** — ligament : human :: cellulose : grass :: crystal lattice : rock :: rebar : wall. The same equations, tests and ledger for every object with structure. | **SPECIFIED** |
| 149 | Passive ports for plant · rock · tree · building · vehicle · fabric · terrain (`docs/THE_COMPILER.md`) | **SPECIFIED — no falsifier has been run on any of them** |
| 150 | **The tolerances in that table are CHOSEN.** "within 5%" / "within 10%" are round numbers with no source. A tolerance must come from the measurement's own grain — the way the knee-extension ligament was refused because a 1.84° gap fell inside a 4.16° sample step. **A falsifier chosen to be comfortable is a falsifier chosen to be survivable.** | **OPEN** |
| 151 | **`k`, `c`, `E`, `μ`, `σ_max` are FREE NUMBERS and Rule 1 applies to every one.** Writing `F = kx + cv` programs the FORM — legitimate, and exactly "program the rules". It says nothing about `k`. | **OPEN** |

**The worked precedent for all of 148–151 is the human ligament**, and it cost four wrong
arithmetics that each returned a plausible number (antagonists counted as helping, 6× too stiff ·
the sign of `moment` read alone when muscle force is negative · peak *isometric* force where the
muscle makes 719 N of a nominal 2212 · evaluated at the limit where the hamstrings are spent).
**Expect the same four when a tree trunk or a wall is derived.**

### 17 · READ FROM OUTSIDE — what a foreign project was worth, and what it was not

**NVIDIA ARDY, SIGGRAPH 2026 (code Apache-2.0, weights NVIDIA Open Model Agreement), read
2026-08-03.** Evaluated for extractable physics. **There is none** — the paper states the model is
*"purely kinematic… lacks awareness of physical dynamics"*, and its loss carries no energy,
momentum or dynamics prior. **NOT ADOPTED as a motion source**: 630 h of Earth mocap with no
gravity input is the authored-phenotype defect already named at piece 92, and an Earth walk
replayed on this body is **Fr 0.2536 against the 0.1513 `theHuman` derives for itself.**

| # | the piece | status | home |
|---|---|---|---|
| 170 | **THE GATED-SUM TRAP.** A penalty gated by a quantity the optimiser controls is minimised by turning the GATE off, not the error. `SUM c*err / SUM c` — the denominator is the rule. Not caught by rule 3 (satisficer) or by the normalisation rule; neither sees a term that can be made *not to apply*. | **RECORDED, NOT ADOPTED** — no current objective uses a gated sum; `objective_lint.py` does not check it | `Chimera/docs/OBJECTIVE_DESIGN.md` |
| 171 | **HORIZONTAL IS RELATIVE; VERTICAL IS NOT.** Decode the root as `(psi_dot, p_x_dot, p_z_dot, p_y)` — heading rate and planar velocities relative, **height absolute**. Measured to reduce foot skating. Height is referenced to gravity and the ground is at a fixed place; heading and planar position are frame-arbitrary. | **VERIFIED** as their result; the *why* is **INFERRED** and **UNTESTED HERE** | `docs/THE_COMPILER.md` |
| 172 | **Their `L_consist = \|\|J - FK(theta)\|\|` is dyadAnalysis** — two independent routes to one number, forced to agree. Independent confirmation that the dyad is the right instrument. | CONFIRMATION | `docs/THE_COMPILER.md` |
| 173 | **Their hybrid representation is the synergy result** — keep EXPLICIT whatever must be addressable (you cannot inpaint a latent), compress the rest. States with its reason what we measured as 290 muscles → 8 dims for 91%. | CONFIRMATION | `docs/THE_COMPILER.md` |
| 174 | **`MotionCorrection/` UNREAD** — a C++ foot-skating post-process, Apache-2.0, algorithm not named in its README. The one place in that repo a real solver might live. | **OPEN** | — |

**THE GENERAL LESSON, and it is the reason this section exists:** a kinematic motion model has no
physics to give a physics project, and the check that settles it takes one line — *does it take
gravity as an input?* What a foreign project IS worth is its **objective-design scars** and its
**representational choices**, because those are measured consequences someone else already paid
for. Read for the losses and the frames, not for the model.

### The outstanding data, named

| # | what is missing | blocks |
|---|---|---|
| 152 | measured human passive moment–angle curves | the ligament level is currently an **upper bound** (sized to hold maximum voluntary contraction; real curves are softer and exponential, because reflex withdrawal shares the job) |
| 153 | muscle via-points as bone-length fractions (ISB) | moment arms away from the measured poses |
| 154 | sensor noise floors | what a reflex loop can actually resolve |

---

**Next:** these pieces, organized into one sequence — `docs/THE_WORKFLOW.md`.
