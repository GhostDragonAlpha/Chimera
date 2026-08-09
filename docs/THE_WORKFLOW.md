# THE WORKFLOW — the one sequence

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

> **Consolidated 2026-08-02 by reading every workflow document in the repository and putting each
> idea on one list first** — `docs/THE_PIECES.md`, 174 pieces with their provenance and status (§16 is the port ledger).
> Nothing here is new invention; it is the pieces that were already written down, in the order they
> actually run, with the joins that were missing.
>
> **What the gathering found.** This repo held **two workflows that were never joined.** The
> FORMULA (2026-07-24, `PROVE(X)` through S0–S7, sealed) and the CHAPTER (2026-07-28, membranes in
> `story/`). The second superseded the first in practice while the first stayed labelled canonical —
> which is the repo's own named drift pattern: *a new thing added beside the old thing instead of
> replacing it.* This document is the join.
>
> **And the join is where Rule 1's failure lived.** The formula's S4 read
> `MEASURE(TRAIN(PROGRAM(V)))`. There is no DERIVE in that line. A reward was programmed, weights
> were trained, the result was measured — every gate satisfied — while the target speed came from
> another planet. **The missing stage is now S4, and everything after it moved down one.**

---

## THE WHOLE THING ON ONE PAGE

```
  ┌─ THE DAY — and it is a LOOP OF TURNS, not a pipeline (§0) ──────────────┐
  │                                                                          │
  │   ORIENT ── read the state, never guess it                              │
  │      ▼                                                                   │
  │   NEXT ──── the operator names ONE camelCase term, or the six           │
  │      │      directions name it. You never pick it yourself.              │
  │      ▼                                                                   │
  │   THEORY ── STATE it: claim, prediction, FALSIFIER. No falsifier,       │
  │      │      no build. A description survives any result (§0).            │
  │      ▼                                                                   │
  │   ┌─ THE MEMBRANE — PROVE(X) ────────────────────────────────────┐      │
  │   │ S-1  VALIDATE ◄─ each PORT alone, against a KNOWN answer      │      │
  │   │                  statement · prediction · falsifier           │      │
  │   │                  registration REFUSES a test with no falsifier│      │
  │   │                  the COUNT is asserted, never assumed         │      │
  │   │  S0  FRAME      one claim · the/a · what would REFUTE this?   │      │
  │   │  S1  QUESTION   variables are BORN of questions               │      │
  │   │  S2  SATURATE   measured — Chao2 + a dry tail, curve rendered │      │
  │   │  S3  CLASSIFY   PHYSICS · FREE · LENS · HUMAN                 │      │
  │   │  S4  DERIVE  ◄── the equations close, from the PARENT only    │      │
  │   │  S5  TRAIN      only the genuinely free numbers               │      │
  │   │  S6  EMIT       the same numbers become matter, local units   │      │
  │   │  S7  DYAD       a NUMBER vs a blind eye's TERM                │      │
  │   │  S8  RECOMPOSE  the parent is proven BY its children          │      │
  │   └───────────────────────────────────────────────────────────────┘      │
  │      ▼                                                                   │
  │   CHECK ─── grow → witness → folding → gate → timeline → slider         │
  │      ▼      in that order, every time                                    │
  │   LOOK ──── a SECOND system reads the turn's output. This is where a     │
  │      │      correction can happen, and the only place it ever has.       │
  │      ▼                                                                   │
  │   COMMIT ── branch + SHA, the numbers and their comparisons in the msg   │
  │      │                                                                   │
  │      └───► NEXT TURN.  How many turns does your plan have? One is a      │
  │            monad, however long you run it.                               │
  └──────────────────────────────────┬───────────────────────────────────────┘
                                     ▼
                        THE NIGHT ── the day's failures become rules
```

Two terminals, and only two: **PHYSICS** (a fact true in an empty universe) and **THE HUMAN**
(taste). An LLM is never one — its answer is always another claim, so the walk recurses past it.

---

## 0 · THE THEORY METHODOLOGY — every membrane is a theory

> **The operator, 2026-08-02:** *"Every membrane is a theory. Every port is a theory. Every
> connection is a theory. The game itself is a theory."*

This is the frame S0–S8 was missing, and its absence is why the stages kept executing correctly
toward ends nobody had stated. **A membrane is not a thing you build and then check. It is a CLAIM
about how the world works, and building it is the experiment.**

**A theory that is not written down before the work is not a theory — it is a description written
afterwards, and a description cannot be wrong.** That is the whole difference:

    A DESCRIPTION SURVIVES ANY RESULT. A THEORY CAN LOSE.

### The three parts. A membrane may not be built without all three.

| part | what it is | the test that it is real |
|---|---|---|
| **STATEMENT** | what this membrane claims is true, in one sentence, in plain words | someone could disagree with it |
| **PREDICTION** | a number or behaviour it implies **that you have not measured yet** | it could come out otherwise |
| **FALSIFIER** | what result would kill it — named **before** the run | you would accept that result as a loss |

**The falsifier is the part that gets skipped, and skipping it is how six months of work becomes
unfalsifiable.** If you cannot say in advance what would prove you wrong, you are not going to
notice when it happens — you will find a reason the result still fits, and every reason will be
individually reasonable.

### It is fractal, and that is what makes the game one object

    the game        is a theory   (hierarchy x physics x human = a 4D experience)
      a membrane    is a theory   (theCooling: atoms are permitted at 3760 K)
        a port      is a theory   (the hip carries its share without buckling)
          a number  is a theory   (leg_length = 0.9201 m, and two routes must agree)

Each level's PREDICTION is the level below's TEST. `theCooling` predicted 3760 K and the
literature said ~3700 — **the membrane was the experiment and the number was the result.** That is
not a metaphor for how this is built; it is the build.

### Where it changes the day

- **S0 FRAME gains a fourth question:** *what does this membrane CLAIM, and what would refute it?*
  A membrane with no falsifier does not proceed to S1.
- **A failed prediction is a RESULT, not a setback.** It names the missing row, and a named row is
  worth more than a passed test. R4 was named by a knee's ring period disagreeing with a fall time.
- **A confirmed prediction that could not have failed is worth NOTHING.** Check the falsifier was
  reachable before celebrating the pass.

### The worked example, written in this form on the day the method was named

> **THEORY — STANDING.** A human stands by continuously falling and catching itself, and the
> catching is done by the TRUNK. The legs are the strut (a static problem, solved: `GROUND→FOOT`
> closes at +0.7%); the trunk is the stabiliser.
>
> **PREDICTION.** A trunk port buys more survival than further leg training does. The legs sit at
> 32% / 24% / 13% and have returned diminishing, coin-toss gains for six commits.
>
> **FALSIFIERS, named before the run:** the sacroiliac seam turns out to be no joint (the trunk
> cannot reach the legs — dead on arrival) · the trunk muscles have near-zero moment arms at the
> standing pose (postural in name only) · **the legs alone reach 5 s under deeper search** (the
> strut was the answer and the theory is wrong).
>
> **THE EVIDENCE THAT PROMPTED IT, and it is a number nobody chose:** 290 muscles in the body,
> **80 in a trained port, 210 in none — 72%.** 162 of them cross the trunk across five lumbar
> levels in flexion/extension, lateral bending and axial rotation. **You do not put 162 actuators
> on a passive column.** Every result reported before this was 28% of the body's actuators, and it
> was never the human standing. It was the legs.

---

## 0b · THE DYAD IS THE DRIVER, NOT A GATE — the concept this document was missing

> **Added 2026-08-02, after the consolidation shipped without it.** The first version of this file
> put the dyad at **S7**: a checkpoint near the end of proving one membrane, where a number meets a
> blind eye's term and they must agree. That is *a* use of the dyad. It is not what the dyad **is**,
> and building the method around the smaller reading produced a monad with a checklist.
>
> `Chimera/core/dyad.py`, first line: **"THE DRIVER. Two minds that drive development, turn by
> turn."**

    drive()  ->  execute  ->  report()  ->  drive()  ->  ...     until the human stops it

**The loop is the method. The stages are what happens inside one turn.** S0–S8 is not a pipeline you
run once from end to end; it is the shape of a single turn, and the turns are where the work
actually lives — because a correction can only happen *between* turns, and a correction is the only
thing that ever changed anything here.

**THE TEST, and it is brutal: how many turns does your plan contain?** A six-hour batch job contains
**one**. It satisfies every stage of this document — targets derived, gravity read, gate passed,
envelope Froude-matched — and it cannot be corrected, because nothing looks at it until it is over.
Measured on 2026-08-02: a run reported `surv% = 92.8` while the body crouched at 13% of its target
speed. **The number designed to report success reported success.** Six hours of that is not six
hours of training; it is six hours of one unchallenged claim compounding, with a loss curve as its
alibi.

    A MONAD RUNNING LONGER IS STILL A MONAD. IT IS JUST A MONAD YOU HAVE INVESTED IN.

**Every real finding in this project came from a turn ending and someone looking:** `-9.81` on the
third line of a rollout, a knee 92.1% out of phase, an ankle demanding 15° of Earth push-off, a
witness holding its own stale copy of a leg. Not one came from a converging curve.

**So the cadence is the design decision, and it is made BEFORE the work, not after:**

- **Every turn ends in something a second system can read** — a picture, a number a different
  instrument produced, a measure with a derived pass/fail. A turn that ends in "it is still running"
  is not a turn.
- **Prefer more turns to longer turns.** If a plan cannot be cut into turns, that is the finding:
  the thing being built has no observable intermediate, which means it also has no observable
  failure.
- **The two minds must stay de-coupled** — that is what every seam in this engine is for (blind
  reading, a separate process, `via='mcp'`, "an LLM is never a terminal"). Two coupled systems
  agreeing is **bimanual interference**, not proof.
- **The human is one of the two minds.** Attention, correction and insight are not overhead around
  the method; they *are* the method's second half. `core/council.py` (FAST proposes, DEEP
  pressure-tests) is the same shape when the operator is away — it is not a substitute for them.

---

## 0c · WHO DOES WHAT

| | **THE HUMAN** | **THE AGENT** |
|---|---|---|
| writes | `story.md` — what a membrane IS | `physics.py` — the law reaching it from its parent |
| produces | the **NODES**: which membranes exist, how deep we go | the **EDGES**: the numbers and the matter |
| owns | **DECIDE** (taste) and **ENOUGH** (is it deep enough) | the hierarchy, the formula, and **every technical decision** |
| is | one of the two terminals | never a terminal |

**You are the head of the dragon.** You do not ask which wrench to pick up. There are exactly four
legal stops: the term is proven · a real blocker (name the cause) · a taste decision · the eye is
dark and no blind reader is possible. **"Which term?"** is never legal — `next` answered it.
**"Which approach?"** is never legal — that is your half.

---

## 1 · ORIENT — read the state, never guess it

```bash
python story/grow.py --read --depth 2     # the universe in three sentences
python story/timeline.py                  # the story in the order it happens
python tools/methodology_gate.py          # all 42 membranes, 8 columns
```

Piece #109 of the inventory, and it governs this whole document: **a claim about INTENT does not
rot; a claim about STATE rots by construction.** So nothing here copies a command's output — it
points at the command. A copy is a snapshot, and a snapshot is a lie with a start date.

---

## 2 · NEXT — which membrane, and you do not choose it

**Setting-first, from the seed down.** Jumping to a mid-tree scene is this project's founding
failure and it has been repeated since. `lushEden` was proved three membranes deep with no bubble
around it; a walker was built six membranes deep with nothing proven beneath it.

When the operator has not named one, the question *"what next?"* has a designed answer rather than
a "whatever is broken" answer — **the six directions from the anchor**:

| direction | the question it asks |
|---|---|
| **DOWN** | what are they standing on? |
| **FORWARD** | what draws them onward? |
| **UP** | sky, ceiling, the scale of the place |
| **LEFT / RIGHT / BACK** | what holds the world together around them? |

**Work one direction at a time. Build nothing that no direction asked for.** Detail is budgeted by
*perceived* distance — arm's reach, personal, social, horizon — not by travel: **distance travelled
is not a consideration**, and in a space game most of the space is void, and void is correct. When
all six are filled, **MIGRATE**: move the anchor, six fresh directions open. The universe expands
because the current one is *saturated*, not because someone decided to add more.

It is scale-invariant, which is the payoff — the same six questions at regolith, cockpit, orbit and
interstellar. And they are not a metaphor: **the six directions are the PORTS of a cell**, typed by
what flows through them, so an unfilled port is somewhere the world is not finished and
`work_queue()` is the world's to-do list **enumerated rather than authored**.

---

## 3 · THE MEMBRANE — `PROVE(X)`

The verb is **PROVE**, never "build". "Build" is the old-programming verb — press the button, trust
the output — and it lets an agent make a thing and declare it done, which is the one failure this
studio exists to kill. **"Prove" forces the definition to be reduced:** you cannot prove what you
cannot first state precisely.

### S-1 · VALIDATE — every port alone, against a known answer

**Added 2026-08-02, and it is numbered −1 because it comes before framing: you cannot frame a claim
about a composition whose parts have never been tested.** A PORT is one instruction — a mass falls,
a muscle makes force, a spindle reports length, a ligament resists. S-1 tests each one *by itself*
against an answer known independently of the simulator.

    a port that has not been tested ALONE cannot be ruled out when a composition built on it fails.

Three things are enforced as code, not as advice (`tools/port_registry.py`):

| enforcement | why it exists |
|---|---|
| **no falsifier, no registration** | Rule 0 at the level where it is cheapest to apply. `port_test()` raises on a missing STATEMENT or FALSIFIER — a claim without a named refutation is a description, and a description cannot be wrong. |
| **the COUNT is asserted** | `expect(12)` refuses to run a partial set. Not a smaller suite — an *untested instruction that a composition will later be blamed for*. |
| **duplicate names refused** | two instructions cannot share a name, and a silent overwrite hides one of them. |

**THE COUNT IS ASSERTED BECAUSE IT ALREADY FAILED SILENTLY.** `port_tests_more.py` imported the
registry from `port_tests.py`, which was running as `__main__` — so it got a *second copy of the
module with its own empty dict*. Ports 5–12 registered into a dictionary nobody read, and the
harness printed **`4/4 ports validated`**: a clean, confident success with two-thirds of the
instruction set missing. Nothing in the output said so. **The harness built to catch silent
successes silently succeeded.** The registry now lives in a module that is imported by everything
and run by nothing, and the count is an assertion.

**A PORT'S PREDICTION MUST MATCH THE THING BEING RUN.** Port 1 predicted free fall from
`½gt²` and measured **0.2% off** — which is exactly `g·dt²·n(n+1)/2`, the semi-implicit Euler
term. The port was correct and the *falsifier* was mis-specified. The fix is to predict the
**discrete** sum the integrator actually computes and print the continuous value beside it —
**never to widen the tolerance until the truth fits.**

**THE LAYER ABOVE.** A PRIMITIVE composes validated ports and must clear two further guards: it
must **name** the ports it composes (and every one must already be registered), and it must
**ABLATE** — the test runs twice, once composed and once with one port's contribution removed, and
passes only if the second one *fails*. Without an ablation a primitive is a port wearing a longer
name. Where the ablation is "open the loop", the open-loop control gets the closed loop's **own
mean drive**, or the comparison changes two things at once. Full specification:
**[`docs/THE_COMPILER.md`](THE_COMPILER.md)**.

### S0 · FRAME

`⊢ atomic(X)` — one claim, else SPLIT. Then three questions that are cheap now and expensive later:

- **Is this a LAW or an INSTANCE?** `theX` says what any X must satisfy; `aX` is the one that formed
  here. If you are an instance you **do not know your own name yet** — it is derived (S4).
- **Is a level missing?** `story/HIERARCHIES.md` holds the real paths. A cloud does not become a
  system on its own. **Say so and stop; do not skip it and do not invent one.**
- **Who is this for?** The demographic decides which human terminal you aim at. It is a DECIDE.

### S1 · QUESTION — variables are BORN, never declared

Ask *"what must be true for X?"* recursively. Each question forks three ways: **you know it** →
answer · **it is physical** → run the measurement → answer · **you cannot answer honestly** → that
question **is a research request wearing a question mark**, and research is *generative* — its
answer hands you questions you could not have asked before.

> **The failure this stage exists to kill, in the operator's words:** *"you failed the workflow
> because you determined yourself these variables."* Asked to prove *"Eden is lush"*, the agent
> shattered it into `{land_fraction, warmth, wetness}` — three climate drivers invented in one head
> — trained them and declared it done. Those are not the constituents of a lush Eden. Where are the
> trees as populations, the understory, the canopy, fauna, birdsong, streams, loam, dappled light?
> **Three knobs cannot make it. They can only make the weather over it.**

`⊢ born_of_question(V)` — else **REJECT the variable.** Inventing one in your head is already a
failure, not a shortcut to be audited later.

**WHAT TO ASK — 22 categories in four groups.** This stage stayed orphaned for months partly
because nobody wrote down *which* questions, and they had been written down: recovered from
`WORKFLOW.md` (THE FOUNDRY), where they were buried under a retired UE pipeline.

| group | asks | the categories |
|---|---|---|
| **NODE** (13) | *what IS this?* | physics · world · foundation · performance · economy · narrative · UX · save_load · audio · accessibility · testing · shipping · platform |
| **EDGE** (5) | *how does it RELATE?* | depends_on · proves · derived_from · conflicts · requires |
| **MIRROR** (4) | *why does it EXIST?* | vision · tradeoff · evidence · **terminal** |
| **META** (5) | *where does it FIT?* | depth · breadth · parent · priority · dependency |

Two of those groups do work nothing else in this method does. **MIRROR's `terminal`** forces you to
name, per variable, whether it bottoms out at PHYSICS or THE HUMAN — which is S3 asked early enough
to be cheap. **META's `depth`** is what says *"this needs a deeper zoom"* — and a membrane whose
META answers demand more zoom is a membrane that should have children, which is the tree deciding
its own shape rather than an author deciding it.

**The council's shape:** `Frame → 10Q → Answer → 10Q → Answer → Saturate → Spec`. Two rounds before
you are allowed to think you are done, because the second round's questions are the ones the first
round's answers made askable.

> **THE RHYTHM, and it is the whole operating posture:** ask a concrete question about the current
> state → answer it **with evidence**, not with recall → ask the next question based on what you
> learned → repeat. **Never stop at "task done." A task is just one answer.** The session ends when
> the human stops you, not when you have checked a box.

### S2 · SATURATE — DRY is measured, never asserted

Stopping because you *feel* done is how you get completeness 0.53 and a chapter of one-offs. Two
signals, **both** required:

- **Chao2 completeness** — estimates unseen variables from the one-off discoveries. Many singletons
  ⇒ many unseen ⇒ not done.
- **A dry tail** — the last *K* questions each added **zero** new variables. Sustained, not a lucky
  gap.

`completeness ≥ C_min AND dry_tail ≥ K ⇒ SATURATED`, and **the curve is rendered every run**, so DRY
is a witnessed measurement. A hand-declared set scores completeness 0.50, dry tail 0, and is refused.

    core/saturation.py       # the gate. The operator still calls ENOUGH — but on the curve.

### S3 · CLASSIFY — every variable goes to exactly one of four places

| | what it is | where it lives | who settles it |
|---|---|---|---|
| **PHYSICS** | derivable from the parent | `derive()` | S4 |
| **FREE** | genuinely open — the law fixes the form, not this number | a `FREE` dict | S5 |
| **LENS** | a declared exaggeration | a `LENS` dict | nobody — it is a lie you can turn off |
| **HUMAN** | taste | the operator's DECIDE | the operator |

**The one test that places anything: try to write its `measure()` first.** Can't? You are missing
the substrate — **PROGRAM that first.** *You cannot train inside a physics that does not exist yet.*

**Never merge FREE and LENS.** A FREE dial changes what the world IS and re-derives the subtree; a
LENS dial changes only the picture. One is a fact you may choose; the other is a lie you may see
through.

### S4 · DERIVE — the stage that was missing

> **This is RULE 1, and it is a stage rather than a warning because a warning did not hold.** On
> 2026-08-02 a walker that would not walk was met with a four-variant parameter sweep. It looked
> like this project's own method — one variable each, run in parallel, controls, a fair comparison.
> **Every variant was asking the body for a speed it physically cannot walk at.**
>
>     this world     g = 7.076 m/s2 (0.722 Earth),  leg 0.9201 m
>     theHuman derives its own comfortable speed:    0.9924 m/s
>     the trainer targeted:                          1.285  m/s   <- MEASURED ON EARTH
>
> Froude settles it in one line — `Fr = v²/(gL)`, and equal Fr means a dynamically similar gait.
> 1.285 m/s is Fr 0.183 on Earth and **Fr 0.254 here**, 39% higher and heading for the walk→run
> transition. So the velocity term demanded a running-ward gait while the tracking term demanded
> Earth *walking* envelopes. **The crouch was the only stable point in a contradictory reward.**

**The rules of this stage:**

1. **Read ONLY your parent's `numbers.json`.** That is the entire set of things you may inherit.
   Not a sibling's, not a grandparent's, not a child's.
2. **If what you need is not there, it belongs to your parent and your parent should derive it** —
   being what both children can see is what a parent is FOR. **Never type it.** The failure mode is
   a literal under a comment claiming inheritance (`"T_star_surface": 5772.0`), and the disguised
   form is `parent.get("k", 86400.0)`, which reads as defensive programming and serves a typed value
   the instant the parent stops carrying `k`. **`.get` cannot fail.**
3. **Show the equations CLOSE.** Trace every variable to a parent number, a measured constant, or a
   law. A chain with a gap in it is not a derivation with a caveat; it is not a derivation.
4. **A derived instance now knows its name.** `T = 5772 K → Harvard G → "Yellow" → aYellowStar`, and
   `measure()` checks the folder name still matches the class the physics produces. **The name is a
   claim, so it is tested like one.**
5. **The test that it is real and not a story: it predicts a fact it was never fitted to.** η + mₑ +
   13.6 eV → **3760 K** against a literature ~3700. `σ/(ρg)` contains no geology and says a
   low-gravity world carries a taller mountain — shown Earth, it returned Mars.

```bash
python tools/training_gate.py --target-speed X --stride-s Y   # refuses another planet's numbers
python story/audit.py --typed                                 # numbers that did not come from the parent
```

**THE TELL, before you run variants: ask what QUESTION each one answers. If the answer is "which
number is best", stop.** That is a search where a derivation belongs.

**RESEARCH CORRELATION (2026-08-08, the floor saga's lesson — `docs/JOINT_ATLAS.md` METHOD
LESSON).** Derivation starts with a literature scan, not a blank page. Contact mechanics (ODE's
CFM/ERP, MuJoCo's solref/solimp — implicit rows, bias, damping from effective mass) was in print
the whole time the floor saga spent 16 runs arriving at it by failure. The rule: the first run
TRANSLATES the published solution into our form; runs are spent only on the unknowns no paper
carries — this kernel, this skeleton, this servo. A published model is a measured-constant-class
input (a legal terminal); a copied library is not (a black box, no chain). Scan first: MuJoCo /
ODE / PhysX docs, Baraff–Witkin SIGGRAPH notes, the OpenSim corpus, the capture-point literature.

### S5 · TRAIN — and only the genuinely free numbers

Everything S4 could not reach is what S5 is for, and nothing else. **Program the rules, train the
numbers.** The LLM writes the constraints and never turns the crank — ~20 edits/hour against
~30,000 evals/sec, six orders of magnitude.

- **Write the domain** (`core/trainables/<f>.py` — `seed`/`mutate`/`measure`, reporting **FACTS**,
  never opinions), then **the objective** (`docs/objectives/<f>.json` — what GOOD means, in physics
  not taste, with at least one `maximize` term or you get a satisficer).
- **Diagnose the TIER before you fix.** A `measure()` reported 47% of land as ice+tundra; the
  tempting fix was to train the thresholds down. Wrong — the bands were in the right places and a
  `lat^1.15` curve was freezing the mid-latitudes. A **LAW** bug. Fixing the law took the mismatch
  0.655 → 0.512; *then* training the residual took it to 0.180. **Do not train away a broken law.**
- **The exploit is the product.** A degenerate winner is the optimiser auditing your spec at 35 kHz
  and finding the hole you would have defended in review. **Iterate the objective, never the
  artifact.**
- **One rollout is a coin toss.** Score N randomized restarts and keep the **WORST**.
- **You cannot train CODE** — ~6 min/eval against 1.5 ms.

### S6 · EMIT — the same numbers become matter

`emit()` lives in the **same file** as `derive()` and reads the **same numbers**, so appearance
cannot drift from physics: there is nothing to cross-check because they are one thing.

- **NO AESTHETIC PASSES.** A colour is a measurement. `theCooling` ends salmon because 3760 K *is*
  salmon.
- **`emit()` is READ-ONLY.** It may not mint an object. A "star marker" drawn beside a planet is
  **a moon**, and no moon was derived. **A light source is told by its light** — the terminator, the
  lit limb, the shadow already said where the star was.
- **Local units.** A horizon is 2.3e-35 m and a planet is 6.4e6 m; in metres one of them is
  float-precision dust. Emit at radius ~1 in your own frame, **grain size included**.
- **A chapter is a MOVIE, not a picture.** Sample five values of `t`, and check the ends
  specifically — one frame cannot show motion, and a scene that silently failed to switch is
  pixel-identical to one that worked.

### S7 · DYAD — a NUMBER against a blind eye's TERM

**A membrane is real only where its inside and its outside agree, and the two must be measured by
DIFFERENT SYSTEMS.**

- **PHYSICS (you) → a NUMBER.** Deterministic, from the law.
- **AN EYE → a TERM.** Something LOOKS at the render, **blind to the number**, and says what it sees.
- **CROSS-REFERENCE → an alignment 0→1.** Above threshold the dyad holds; below it, **the render is
  wrong — fix the physics, never the tolerance.**

Two *different kinds* of output are what make the sides independent. **Identical outputs are the
tell of a false dyad, not proof.**

> **A MONAD IS NEVER PROOF**, and it is the most common failure here because it feels like
> diligence: you render something and look at it yourself · you measure pixels off your own picture
> and call it convergence · you script the `Engine` from a driver instead of calling the tool.

Three tiers of eye, and the operator chooses: **LM Studio's vision model** (truly independent
weights) · **a blind spawned instance** (structurally blind — declare the correlated priors) ·
**Alan** (the terminal, ends any dispute). **Tier 0 — the agent that built the thing judging it — is
never acceptable.**

```bash
python ChimeraEngine/gallery.py 8765
curl -s "http://127.0.0.1:8765/frame?term=aBlueWorld" -o frame.jpg   # then LOOK at it
```

`/live?blind=1` is the same picture with the *"physics expects…"* caption withheld — **shown the
answer, an eye confirms instead of observes.**

**Why a dyad at all? Because that is how a MIND verifies itself.** You answer your own questions
constantly, which looks impossible under *"you cannot measure a system with itself"* — until you
notice your head was never one system. A monad cannot check itself; a dyad can. The method is
cognition externalized, where the agreement cannot be faked.

### S8 · RECOMPOSE — the parent is proven BY its children

`⊢ recompose({V}) ⊨ X`, else back to S1. A parent is **made of** its children: `layout(nums)`
returns `{child: (centre, scale)}` in your frame, each child is grown, emitted in **its own** local
units, and placed. The parent supplies only **where** and **how big**; the child always supplies its
own appearance.

Four rules, each learned by breaking it:

- **Convert units at the seam** — or better, move the number to the parent that owns it. Two
  authorities for one number is how they drift apart.
- **LOD every placed child by its size** (`matter.grains_for`). Eleven worlds at a flat 900 grains
  each put 4,801 splats into a tile that allows 4,096, and the cap evicted *the parent's* grains —
  a hard-edged black rectangle on the 32-px grid.
- **A SCALE step composes; an ASPECT step must not.** `theRockyPlanet → aRockyPlanet → aBlueWorld →
  theTerrain` is one body four ways, all at extent = R. Composing those draws the same sphere four
  times, interpenetrating.
- **Never duplicate a child**, and **place it even when it is sub-pixel** — that is what makes the
  tree ONE OBJECT rather than a stack of separate pictures.

---

## 4 · CHECK — in this order, every time

**The order is not a preference.** A witness that reads published numbers cannot see a generator
that failed to publish; it walks the last good file on disk and reports green. `grow.py` was dying
while `chain_witness` reported *"42 working, 0 broken."*

```bash
python story/grow.py                  # 1. the GENERATOR must exit clean. Never pipe it to /dev/null
python tools/chain_witness.py         # 2. every membrane derives, emits, moves, closes
python story/folding.py audit         # 3. units: what a law may connect to
python tools/methodology_gate.py      # 4. form / derives / emits / free / units / one-name / typed / predicts
python story/timeline.py --write      # 5. containment vs chronology — AND RE-STAMP
python tools/slider.py                # 6. move a free number — whatever does not move is TYPED
```

**Step 5 must come after step 1, and it is not a preference either.** `grow.py` and
`timeline.py --write` are **two writers to one file**: `grow` rebuilds every `numbers.json` from
`derive()`, which does not know about `timeline_serial`, so **every `grow.py` run silently strips
the timeline stamps off all 42 membranes.** Nothing complains — the numbers are still correct, the
witness still passes, the gate still scores 42/42, and the story's chapter order has quietly lost
its consumer. Measured while consolidating these documents, on the very run that produced them.

**When a membrane fails a column, suspect the COLUMN once before suspecting the membrane.** The
gate written to catch forty-two membranes made **four of its own bugs in a day**, every one of them
a check applied outside the shape it was written for. There is no exemption for tools.

**And a systematic pattern is ONE decision, not N edits.** Forty-five flagged pairs across the tree
were a single choice. Count the pattern before fixing instances.

---

## 5 · WHEN IT IS WRONG — backtrace, do not debug forward

**Forward debugging finds where an error became VISIBLE. Backtracing finds where it ENTERED.** In a
hierarchy where every child consumes its parent's numbers, those are rarely the same membrane.

A foot went through the floor. Six hypotheses were tested against the foot — segment lengths, pelvis
height, ankle sign, half-cycle offset, knee amplitude, knee phase — and every one was eliminated
clean. **The foot was faithfully executing an instruction handed to it from four membranes up:**
`aBlueWorld` mass → `g = 7.076` → Froude → comfortable speed falls 15% → the model reads the *slow*
condition from a dataset recorded on Earth.

    WHEN EVERY INPUT VERIFIES AND THE OUTPUT IS STILL WRONG, STOP INTERROGATING THE MEMBRANE.
    WALK UP. Ask what it was handed, and whether that was true where it now stands.

**And find the zero.** `HIERARCHY × PHYSICS × HUMAN` is a product, not a sum — so when something is
wrong you do not argue quality, you find which factor is at zero. A terrain with 39 traced variables
rendered from noise is *physics = 0*. A walker six membranes deep with nothing proven beneath it is
*hierarchy = 0*.

The full diagnostic set — 24 rules, each with the failure that earned it and the number that proved
it — is **`Chimera/docs/EXPERIMENTAL_METHOD.md`**. Read it before debugging **or reporting**
anything.

---

## 6 · THE NIGHT — the day's failures become rules

Every one of those 24 rules was written **by hand, after a failure, by whichever context happened to
notice.** That is the weakest link in this whole method, and the repo already measured why:

> Of 31 heuristics, the **18 that became mechanism are alive**; the **13 that stayed prose
> degenerated into the same auto-generated sentence with the nouns swapped.**
> **You cannot fix that by writing better prose. You can only make it executable, make it a
> pointer, or delete it.**

So the day ends by converting what it learned into something that runs:

1. **Capture surprises live** — a correction, a dead end, an expectation violated. They are the raw
   material and they are gone by morning otherwise.
2. **Distil at most two** into candidate rules. More than two per night is not learning, it is
   note-taking.
3. **Make each one executable, a pointer, or delete it.** A rule nothing checks is prose. Rule 1
   became `tools/training_gate.py` the same night it was earned, which is why it is a rule and not
   a paragraph.

---

## 7 · THE ARCHITECTURE — one primitive, one motion, one address

**A membrane is a boundary, and a boundary is a SCALE.**

    time ⊃ universe ⊃ system ⊃ planet ⊃ ground ⊃ section ⊃ cell ⊃ object ⊃ material ⊃ …

These are not different constructs — the membrane IS the hierarchy, and crossing one inward is
exactly what "finer" means. Being a boundary supplies, free, at every level: **a frame** (up is the
local normal — a global +Z is wrong on a sphere), **a unit** (a coordinate cannot exceed its own
membrane's extent, so precision stops being a problem rather than being managed), **an identity**
(the serial attaches here; an address is the path of membranes crossed), **inside/outside**, and
**LOD** (`depth()` IS the level of detail).

**TIME is the outermost membrane.** Past is inside (settled), future is outside (unformed), the
present is the boundary surface, and nothing contains it. So *"same seed, same world, forever"* is a
claim about time, and history is **derivable rather than stored**.

**Everything is TWO ENDS AND A DIAL** — a verb, a morph, heritability, LOD, growth, and **the story,
which is simply the outermost dial.** What a story dial has that the others do not is **GATES**: a
player is held until something *measurable* is true, then released. The condition reads world state;
it is never a flag someone sets, for the same reason acceptance conditions are not self-reported.

**And a hierarchy says what CONTAINS what; a timeline says what FOLLOWS what.** Those agree down a
spine and part company the instant the tree branches — `theStar` and `thePlanets` are siblings and
are not simultaneous. Derive the epoch from published durations (`t_end = t_end(parent) +
duration_s`), never declare it, and **stamp the story with the same number** — otherwise there are
two orderings and the human-readable one loses silently.

---

## 8 · THE MAP — what to read, and when

| read | for | when |
|---|---|---|
| **`docs/THE_LAW.md`** | Rule 1, alone, in one page | first, always |
| **this file** | the whole method as one sequence | before touching anything |
| `story/README.md` | how the game is built — chapters, the two authors | before writing a chapter |
| `story/ONBOARDING.md` | the procedure, the viewer, and the 45-row failure catalogue | before your first membrane |
| `story/LANGUAGE.md` | the grammar — four verbs, articles, units, the visibility model | when writing `physics.py` |
| `Chimera/docs/EXPERIMENTAL_METHOD.md` | 24 rules for not fooling yourself | before debugging **or reporting** |
| `Chimera/docs/THE_GROWTH.md` | what the game IS — the five rulings, the corpus, D0–D4 | to know the standard |
| `docs/THE_FOLDING.md` | units, folds, bonds, regimes | before calling a chapter done |
| `docs/FAL_AI.md` | the synthetic capture rig, its costs and its traps | before spending money |
| `docs/THE_PIPELINE.md` | where a genome comes from and what it becomes — scan → genome → matter → world → render | when working the splat pipeline |
| `docs/THE_COMPILER.md` | **the operating model** — ports → primitives → programs → parser → runtime → calibration, and passive tissue as a universal port | before building anything at any layer |
| `docs/THE_PIECES.md` | **the full inventory — 174 pieces, with what is orphaned**; §16 is the port ledger | when you think something is missing |
| `CLAUDE.md` | paths, hardware traps, conventions | for anything operational |

**A doc marked DESIGN is not a description of something that exists.** Check the banner.

---

## 9 · THE HONEST BOUNDS — they belong to the method, not against it

- **Completeness of the world is unprovable.** Saturation measures completeness *within the
  questions you asked*; a lens you never ground leaves a region unsampled that no estimator on your
  samples can price. That last call is the operator's **ENOUGH**.
- **Nine pieces are orphaned** — written down, load-bearing, and done by nothing. S1/S2 (questions
  and saturation), S8's gate, the why-chain and the coin for membranes, the night phase, the six
  directions, the demographic, live surprise capture, and `work_queue()`. They are listed with their
  sources in `docs/THE_PIECES.md` §14, and they are the honest backlog of this method.
- **The genome pipeline is a separate document** because it is a separate concern:
  `docs/THE_PIPELINE.md` (the spine, stage by stage, with its own honest gaps — the splat-type
  catalog's anisotropy ceiling, no emissive/fluid/atmospheric genome, unused colour and opacity in
  composition matching, unsolved relighting), plus `Construction/SPLAT_DNA_WORKFLOW.md` (scan →
  genome in detail) and `WorldModel/ML_PIPELINE.md` (the generative half).
- **An LLM is never a terminal**, so no amount of this document makes a claim true. Only the
  measurement and the human do.

---

That is the workflow. It maps its own territory, digs only where it must, **derives before it
trains**, measures its own completeness, stops at two floors, and leaves the human exactly two
levers: **decide the taste**, and **call when it is deep enough.**
