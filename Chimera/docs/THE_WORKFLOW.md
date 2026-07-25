# THE WORKFLOW — how Chimera gets built, end to end

> The canonical entry point (the one `CLAUDE.md` sends you to). It is the **map**; the deep docs
> are the terrain. Consolidated 2026-07-24 from the session that solidified the method — the point
> at which the *way of working* was declared complete ("the final piece"). If you read one doc
> before touching this project, read this one.
>
> **SEALED 2026-07-24** — the operator called ENOUGH. This is settled doctrine: do not re-open or
> re-litigate the method; *use* it to build the game. The next session begins the way it should —
> the operator names one `camelCase` term, and the agent guides from the setting down.
>
> **The true root (found right after the seal, 2026-07-24) —** above the setting sits the **seed:
> the STORY, the timeline** ([`THE_STORY.md`](THE_STORY.md)). A build begins by securing it, and its
> **true measure is the human *seeing it unfold in play*, not reading it.** See §2b. (That this was
> found *after* ENOUGH is the method being honest: you cannot see the lens you never ground until you
> ground it — writing the actual story revealed the seed sits above the solar system.)
>
> **ENFORCED (2026-07-25) by the Chimera Engine.** This workflow is no longer only a document. It is
> an MCP server (`ChimeraEngine/`, docs `ChimeraEngine/MCP_ENGINE.md`) whose tools are the ONLY
> sanctioned way to move a term to "proven": `prove` runs these gates and refuses until they pass. A
> doc can be ignored; an engine that owns "proven" cannot. Onboarding: `ChimeraEngine/ONBOARDING.md`.
>
> **The whole method in one sentence:** the human names **one term at a time** and the agent
> **guides them down a hierarchy of membranes**, proving each term against **PHYSICS or THE HUMAN**
> until the game stands — assembled from proven bricks, none of them hand-waved.

---

## The one page

```
you name ONE camelCase term         (setting-first, and I guide you to the right one)
   │
   ▼
I run PROVE(term) through THE FORMULA        (S0–S7, docs/THE_FORMULA.md)
   │      · S1 questions it until the discovery curve SATURATES (measured, not asserted)
   │      · every variable is DISCOVERED by a question, never declared
   │      · each branch bottoms out at PHYSICS (a measurement) or THE HUMAN (you)
   ▼
it lands as a proven BRICK          (a collision-free serial in the codebook)
   │
   ▼
we STITCH                           the brick becomes vocabulary for the next term
   │
   └──────────────► repeat, climbing the hierarchy, until the game stands
```

**There are exactly two roles, and only two:**

| | THE HUMAN (you) | THE AGENT (me) |
|---|---|---|
| names | **one term at a time** | — |
| owns | **DECIDE** (taste) and **ENOUGH** (is it deep enough) | the **hierarchy** and the **formula** |
| is | one of the two **terminals** (where meaning ends) | never a terminal — I write constraints and read walls; I decide neither truth nor taste |
| does | points at the peak | walks you down to bedrock and back up |

Everything below expands one box of that loop. Each section ends with the deep doc that owns it.

---

## 1 · The verb is PROVE (and the only other verb is DECIDE)

"Build" is the old-programming verb — press the button, trust the output; it lets an agent *make
a thing and declare it done*, which is the one failure this whole studio exists to kill. The verb
is **PROVE**, because **"prove" forces the definition to be reduced**: you cannot prove what you
cannot first state precisely, so "prove X" forces *"what exactly is X, and how would we check it?"*
before a single line of work.

**DECIDE** is for taste. You do not prove taste, you decide it — you are THE HUMAN terminal.

→ **`docs/THE_METHOD.md`** (the verb, the question-tree, the terminals, the lenses, Stage 0).

---

## 2 · The operating protocol

### 2a · One `camelCase` term at a time

The human names **one** term per PROVE. This is forced, not stylistic:

- It is the formula's first gate, **S0** (`atomic(X)`, else split).
- The **saturation** measurement (§4) is only well-defined for a *single* term — two terms blur
  which variable belongs to which, and the completeness curve stops meaning anything.
- The human is the serial terminal: you decide one meaning at a time.

**Why `camelCase`:** you are *not* limited to single English words. camelCase **compresses many
words into one atomic token** — `lushEden`, `growTree`, `densityClock` — so you get the richness of
a phrase *and* the atomicity the formula needs. Two payoffs: (1) **collision-free** — a coined term
carries no prior meaning to fight (the reason this repo needs `python -m core.terms`); it means
*exactly* the proven genome bound to it. (2) It is a **serial** — a named handle in the codebook,
"compression is intelligence" made into a word. A proven term becomes **vocabulary**: the next term
can reference it (`treeOfKnowledge in lushEden`). The game is the **composition of proven bricks**,
and "does A compose with B?" is itself a one-term PROVE (that is S7, recompose).

### 2b · The agent guides the hierarchy — SETTING FIRST

You do not have to hold the whole tree. **I hold it and lead you through it, one term at a time,**
in the order a story is told: **the setting first.**

But there is one membrane *above* the setting — **the seed: the STORY, the timeline** (the true root,
[`THE_STORY.md`](THE_STORY.md)). Before the setting there is the frame that says what the whole thing
is *for*, so a build begins by **securing the story** — the human's vision, written as an arc. And a
story has **two measures**: the written text is the cheap up-front proxy (the human reads it and can
redirect it before a line is built), but the **true** measure is the human **seeing it unfold as the
game is played** — meaning is experienced, not described (the movie you didn't want to see and loved
anyway). Provisionally secured on the page; **truly secured only when witnessed in play** — a visual
WITNESS, not a read.

- **The setting is the outermost membrane.** A space game you fly around a solar system → the root
  is `theSolarSystem`, established *before* anything inside it, because a station means nothing
  until there is a system to put it in. (Getting this wrong looks like proving `lushEden` — a garden
  scene three membranes deep — with no bubble around it. Start at the biggest bubble.)
- **Each membrane is a bubble with a BOUNDED decision set** — "within this bubble, these many
  decisions." That boundedness is the membrane primitive doing its job: a boundary supplies a local
  frame and a finite set of choices.
- **You name what you want inside** — *"I want a space station"* — and that **opens the next inner
  bubble** and its own questions. Recurse inward.
- **The leaves are concrete assets to DOWNLOAD and TRAIN** — toward *your goals*.
- **Your goals get the 40-question treatment too.** They are not assumed; they are *elicited* by the
  same question-tree, and they **become the training objective** everything inner is trained toward.

```
theSolarSystem                     ← the SETTING, established first (the establishing shot)
   ├─ theStar · thePlanets · theSpace        (the bounded decisions inside the bubble)
   ├─ theStation   ("I want a space station")  → opens its own bubble of questions
   │     └─ … → download + train station assets → toward YOUR goal
   └─ theGoal      (what you're here to DO)     → your 40-question treatment = the objective
```

The agent's job in one line: **expose the hierarchy by questioning, and lead the human down it
setting-first, surfacing their DECIDE at each node.**

→ this section and 2a are the protocol; the mechanism that enforces them is **`docs/THE_FORMULA.md`**.

---

## 3 · The equation — THE FORMULA (S0–S7)

`PROVE(X)` is an ordered sequence of gates. Each `⊢` ("must hold") is a mandatory checkpoint; fail
one and you are thrown back, almost always to S1 (ask more).

```
S0 FRAME       ⊢ atomic(X)                              else SPLIT
S1 QUESTION    {V} ← QUESTION*(X)   variables are BORN here — ask till DRY
S2 DECLARE     ⊢ ∀V: born_of_question(V)                else REJECT V   (declared, not discovered)
               ⊢ SATURATED({V})    (measured — §4)      else goto S1    (curve not over the hump)
S3 CLASSIFY    ⊢ measure_writable(V)→PHYSICS | taste→HUMAN | neither→goto S1
S4 PROVE·each  ∀phys V: MEASURE(TRAIN(PROGRAM(V)))       ⊢ researched∧trained∧witnessed∧looked
S5 CHAIN       ⊢ why_chain(V) ↦ {PHYSICS, HUMAN}   ∧   coin: claim ⟺ evidence
S6 DECIDE      ∀human V: operator rules                  the only place MEANING closes
S7 RECOMPOSE   ⊢ recompose({V}) ⊨ X                     else goto S1

∴ X ⟺ (∀phys V: measured) ∧ (∀human V: decided) ∧ DRY
floor: PHYSICS (a fact) or THE HUMAN (taste) — an LLM is never one.
```

The three gates that were only prose until 2026-07-24 — **S2a** (provenance), **S2b** (saturation),
**S7** (recompose) — are exactly the three that catch *"the agent declared its own variables."*

→ **`docs/THE_FORMULA.md`** (the full equation, the gate table, the two worked failures, and the
black-hole structure).

---

## 4 · DRY is a MEASURED saturation — proven every time

The completeness gate (S2b/S7) is **never** an assertion ("I asked enough"). It is the measured
signature of a discovery curve going **over the hump and flattening** — the point where new
questions return only what you already have. The science is species-accumulation ("have I found all
the species?"). Two signals, **both** required:

1. **Chao2 completeness** — estimates unseen variables from one-off discoveries. Many singletons ⇒
   many unseen ⇒ **not done**. When new questions only re-surface known variables ⇒ done.
2. **A dry tail** — the last *K* questions each added **zero** new variables. A sustained flat tail,
   not a lucky gap.

`completeness ≥ C_min AND dry_tail ≥ K ⇒ SATURATED`. The gate **renders the accumulation curve every
run**, so DRY is a witnessed measurement. A hand-declared set (3 knobs, one question, no tail) scores
completeness 0.50, dry tail 0 — **refused**. The operator still calls the final ENOUGH, but *on the
measured curve*, never on a claim.

→ **`core/saturation.py`** (the principle as code) · `tests/test_saturation.py` (it must discriminate)
· wired into the pre-commit hook so it cannot rot into a rubber stamp.

---

## 5 · What to PROGRAM vs TRAIN vs DECIDE — THE LINE

The line has **three** tiers, and the test that places anything is *"try to write its `measure()`
first."*

- **PROGRAM** the rules — laws, algorithms, representations, invariants. You state a truth; you do
  not search for it. *You cannot train inside a physics that does not exist yet.*
- **TRAIN** the numbers — abundances, yields, thresholds, prices — **when "better" is machine-checkable
  in physics, not taste.** A search (`core/trainer.py`), never a human turning the crank.
- **DECIDE** (the HUMAN) — mood, art direction, which options exist at all.

→ **`docs/THE_LINE.md`** (the tiers, the one test, the world sorted onto the line) ·
**`docs/OBJECTIVE_DESIGN.md`** (the 7 rules for a trainer objective the optimiser won't exploit,
enforced by `core/objective_lint.py`) · **`docs/TRAINING_PROTOCOL.md`** (the mechanics).

---

## 6 · The shape is a black hole (why it is trustworthy)

Not a metaphor — the same constraint forces both. The **descent** is the density clock accelerating
inward (deeper membrane = denser = faster clock). The **two terminals are the two singularities** —
the points past which no further *why* escapes. The **gates are a one-way horizon** — inputs fall in
and are consumed into the compressed genome; nothing unproven climbs back out. The **compression is
the no-hair theorem** (Eden → its finite proven variable set). And it is the **unitary** black hole:
by holography the information is written on the **boundary** — the graph of *because*-edges, the
why-chain ("the why is the edge"). Opaque floor, **transparent descent**: a black hole you can audit.

→ **`docs/THE_FORMULA.md` §"The shape of the formula is a black hole".**

---

## 7 · The gates that enforce it (a doc can be ignored; a lint cannot)

The method is not trusted because it is written down — it is trusted because it is **run**:

| Gate | Refuses | Code |
|---|---|---|
| research | a research-less session with no cited sources/waiver | `core/research_gate.py` |
| witness | `verified`/`observed` with no observation node | `core/witness_gate.py` |
| visual | a visual claim the model never looked at | `core/visual_gate.py` |
| training | closing a game task with the subject un-trained | `core/training_gate.py` |
| why | a claim whose *because*-chain never reaches a terminal | `core/why_gate.py` |
| coin | a claim and its evidence that don't agree both ways | `core/coin_verifier.py` |
| objective | a trainer objective the optimiser can exploit | `core/objective_lint.py` |
| **saturation** | **DRY asserted instead of measured** | **`core/saturation.py`** |

`preflight → gates → postflight`. No render-and-declare (H-14: a compile is not proof; a render is
not a witness).

---

## 8 · The reading order (the doc map)

| Read | For | When |
|---|---|---|
| **`THE_WORKFLOW.md`** (this) | the whole method as one map | first |
| `THE_METHOD.md` | the engine: question-tree, terminals, lenses, Stage 0 demographic | to understand *why* PROVE |
| `THE_FORMULA.md` | the equation: S0–S7 gates, saturation, the black-hole shape | before proving anything |
| `THE_LINE.md` | program vs train vs decide; what is trainable | before authoring or training a feature |
| `OBJECTIVE_DESIGN.md` | writing a trainer objective that isn't exploitable (7 rules) | before writing `docs/objectives/*.json` |
| `TRAINING_PROTOCOL.md` | the training mechanics (domain / objective / trainer) | when you run `core/trainer.py` |
| `CLAUDE.md` | the project manual: paths, hardware traps, conventions | for anything operational |

---

## 9 · The build as it stands (the hierarchy)

Re-rooted at the setting. `✓` grown/measured · `~` built, not yet proven through the full formula ·
`○` open at the human terminal.

```
theStory  (the SEED / timeline)  ◐  written + ratified on the page; TRUE measure = seen unfolding in play
└─ theSolarSystem              ✓  bigbang grew one, Kepler emergent (slope 1.50, r² 1.000)
   ├─ theStar                  ✓  formed (96% collapse)
   ├─ thePlanets               ✓  3–4 worlds, orbits + climates; the habitable zone emerged
   │  └─ aPlanet (e.g. Eden)   ✓  the SH onion + biomes + underground (caves/mining/geology)
   │     └─ aScene (lushEden)  ~  physics measured, but its variables were declared, not questioned
   ├─ theSpace  (the medium)   ~  orbital mechanics + the density clock for travel & scale
   ├─ theLoop  (the engine)    ✓  world+player+input→verbs→state, witnessed running (6/6)
   │  └─ theVerbs              ~  dig · thrust · balance · grow, on one density clock
   ├─ theStation               ○  opens its own bubble when named
   └─ theGoal                  ○  YOUR 40-question treatment → the training objective
```

Almost all the **substrate** is `✓`. We do not re-prove solid numbers. The next work is wherever
proof is weakest and value highest — and the recursion finds it: name a summit you care about, and
S1's descent walks us to the unproven constituents on the way down.

---

## 10 · The honest bounds (they belong to the method, not against it)

- **Completeness of the world is unprovable.** Saturation measures completeness *within the questions
  you asked*; a lens you never ground leaves a region unsampled that no estimator on your samples can
  price. That last call — *are the right lenses on the table?* — is the operator's **ENOUGH**.
- **Meaning is observer-completed** — it lives in the viewer, so a meaning claim is checked against a
  *model of the viewer*, never a fact of the matter.
- **An LLM is never a terminal** — its answer is always another claim; the walk recurses past it.
- **Fiction is not the forbidden lie** — art is honest, labeled fiction; keeping the two terminals
  separate is what lets facts stay true *and* stories stay free.

That is the workflow. It maps its own territory, digs only where it must, measures its own
completeness, stops at two floors, and leaves the human exactly two levers: **decide the taste**, and
**call when it is deep enough.**
