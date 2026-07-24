# THE LINE — what "train everything" actually means

> The operator's doctrine is **"train everything, one piece at a time."** This document is the
> precise definition, written because if the operator can get confused about where training
> stops and programming starts, so will every agent. It is not a softening of the vision — it
> is the vision's architecture. Read it before deciding whether to *author* a feature or *train*
> it. Companion to `docs/OBJECTIVE_DESIGN.md` (how to write the objective once you know a thing
> is trainable) and `docs/TRAINING_PROTOCOL.md` (the mechanics).

---

## The line has THREE tiers, not two

**PROGRAM the rules · TRAIN the numbers · the HUMAN sets the taste.**

| Tier | What it is | Examples in this repo | Who does it |
|---|---|---|---|
| **PROGRAM** | What is TRUE or STRUCTURAL: laws, algorithms, representations, invariants. You don't *search* for a truth — you state it. | `probe()` (what's at a depth), the spherical-harmonic onion, flood-fill for caves, the water table, `F=ma` in a thrust verb, the Whittaker climate structure | authored, once per mechanism |
| **TRAIN** | The free NUMBERS the rules leave open, **when "better" is machine-checkable in physics, not taste**: abundances, yields, thresholds, prices. | `planet_layers.DEPOSITS` (abundance/price/mineral_frac), biome `THRESHOLDS`, the hypsometry constants | a search — `core/trainer.py` — never a human turning the crank |
| **HUMAN** | What is better **only in the operator's eye**: art direction, mood, which options exist at all. | biome `PALETTE`, which resources/biomes exist, "lush vs harsh" | the operator — the preference loop / `taste.json` |

These are the same three the why-loop already names: **PHYSICS** (a fact true in an empty
universe), the searched middle, and **THE HUMAN** (taste, the reference). An LLM is never a
terminal — it writes the constraints and reads the walls; it does not decide truth or taste.

---

## The one test that places anything: **try to write its `measure()` first**

- **Can't** write a `measure()` that reports facts about it? → you are missing the substrate.
  **PROGRAM** that first. *You cannot train inside a physics that does not exist yet* — which is
  why building a world is mostly programming at the start.
- The `measure()` needs a 6-minute build, or a human, to run? → **not trainable.** Author it
  once, or elicit it. (A C++ system at ~6 min/eval is CODE; taste needs a human, not a search.)
- The `measure()` is a cheap pure function **and** "good" is physics-not-taste? → **TRAIN it.**
  Write the objective (`docs/objectives/<f>.json`), let the search find the numbers.

---

## "Cause and effect for everything" ≠ "program everything"

The fear: if a rule is "when I press a button, a state changes," then everything needs a
hand-written rule. It does not. **You program each *kind* of cause→effect ONCE, and it
generates the effect for infinite instances.**

- One `thrust` verb (`membranes.Verb` — two states + a dial) → every ship, every throttle
  setting, forever. No per-ship code.
- One `probe()` → what's under *every* point of *every* planet.
- One water-table rule → which of *every* cave floods.

The number of RULES is small and finite (a human authors them one at a time). The number of
INSTANCES they generate is infinite. That leverage is the whole game.

---

## The hardware floor is real, thin, and mostly not yours

Registering a keystroke, reading a controller, drawing pixels — that is **programmed**, and you
cannot train it; you can only *simulate* input to train against. But that floor is smaller than
it feels, in three pieces:

| Piece | Tier | Who owns it |
|---|---|---|
| read the W key from hardware | PROGRAM (I/O) | the **engine/library** — written once, reused by every game |
| W → the `thrust` dial | data / config | a **binding table**, player-rebindable |
| `thrust` = two states + a dial | PROGRAM (a rule) | **you**, once |

And most rules have **no input at all** — gravity, the water table, `probe()` all run with
nothing pressed. Input-response is just the small subset of rules whose *cause* is the player.

**Training vs hardware:** you train in a SIM on *simulated* input (offline, fast); you play on
hardware with *programmed* I/O and *real* input. That is why the trainer and the runtime are
different worlds.

---

## Diagnose the TIER before you fix — the classic mistake

When a `measure()` flags a problem, **which tier owns the fix is a diagnosis, and getting it
wrong is how you train luck.** Worked live in `core/biomes.py`:

- `measure()` reported 47% of land was ice+tundra. The tempting fix: TRAIN the temperature
  thresholds down until the fractions match Earth.
- **Wrong.** Looking at the map, the biome *bands were in the right places* but a `lat^1.15`
  temperature curve froze the mid-latitudes — a **LAW bug (PROGRAM)**. Training a threshold to
  hide a broken law is training luck to paper over physics.
- Fixed the law (`→ cos(lat)`): mismatch **0.655 → 0.512**. *Then* trained the residual
  thresholds: **0.542 → 0.180**. Two tiers, two fixes, one `measure()`.

**Do not train away a broken law. Fix the law, then train the residual.**

---

## The complete floor — the actual limit of "train everything"

Exactly three things must be programmed, and all three are finite:

1. **The engine I/O** (read input, draw, play sound) — written/adopted *once*, reused everywhere.
2. **Each rule / verb** (what a cause does) — authored one at a time; a small finite list; each
   generates infinite instances.
3. **A `measure()` for each thing you want to train** — so its numbers *become* trainable.

Everything above that floor — every instance, every value, every layout, the whole world — is
trained, generated, or taste. **"Train everything" means everything above a finite floor of
I/O + rules + measures.** You always write those three. You never hand-write the content they
produce.

---

## The world, sorted onto the line (as of 2026-07-24)

- **PROGRAM (authored, correct):** the SH onion (`planet_membrane`), `probe()` + formation
  physics (`planet_layers`), mining mechanics (`mining`), cave flood-fill (`cave`), the
  cave-system BFS (`cave_system`), cave water/darkness (`cave_features`), the climate laws +
  Whittaker structure (`biomes`), the verb primitive (`membranes.Verb`).
- **TRAIN (the numbers — the queue):** deposit abundance/price/mineral_frac
  (`resource_economy` — the first one actually trained; see `docs/objectives/resource_economy.json`),
  biome thresholds (`biomes.train_thresholds`), the hypsometry constants (or a real DEM),
  vadose depth, void thresholds, mining yields, the market (`economy_engine`).
- **HUMAN (taste):** which biomes/resources exist, the palettes, the mood, the feel — the
  preference loop.

The reassurance: **programming is not where the vision fails — it is where it stands.** You
program the machinery that makes a thing *measurable*, and that is exactly what *unlocks*
training it.
