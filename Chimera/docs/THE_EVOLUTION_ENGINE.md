# The Evolution Engine — what this system can now build

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

> Written 2026-07-14, the day the pieces became a whole.
>
> Read `TRAINING_PROTOCOL.md` for the *method* and `TERRARIUM_DESIGN.md` for the *organism*.
> For what the phenotype is *made of* — the universal brick library that builds a whole world —
> see `THE_MATTER_MODEL.md` (a design, not yet built). This document is about the
> *possibilities* — what the assembled machine can now do, what it cannot, and where it goes
> next. Every capability below is grounded in a measured result, and every limit is stated as
> plainly as every possibility. Nothing here is a promise; it is an inventory.

---

## 0. The one sentence

**The studio has become a general engine for EVOLVING game content against machine-checkable
objectives — you write what GOOD means, in physics and not in taste, and the machine finds the
artifact that satisfies it, at 35,000 evaluations per second, honestly.**

Each piece was built for a narrow reason. The trainer got the LLM out of a tuning loop. The
terrarium grew a body from a genome. The membrane sealed a risky experiment. The GPU backend
took the physics off a thermally-limited CPU. But assembled, they are one thing: a pipeline
that turns **a specification of GOOD** into **a thing that is good**, with no human turning the
crank in the middle.

This is not artificial life running wild (see §6 — that problem is thirty years unsolved). It
is **development**: authorable, bounded, debuggable, and reproducible. Evolution is a tool the
studio uses, not a creature the studio releases.

---

## 1. The shape of it, in one picture

```
  A SPECIFICATION OF GOOD                         A THING THAT IS GOOD
  (the LLM's whole job)                           (nobody authored it)

   scenario ─┐                                          ┌─ a robust gait
             ▼                                          │
   docs/objectives/<f>.json   ──►  THE TRAINER  ──►     ├─ a creature's body
   (constraints: physics,          generic GA           │
    never taste)                   26k–37k evals/s      ├─ an economy that can't
             ▲                     NO LLM in the loop   │   be arbitraged to death
             │                          │               │
   [LLM reads the PINS] ◄───────────────┘               └─ any DATA feature
   the walls the winner rode = the next spec revision       in the game

        └────────────── iterate the OBJECTIVE, never the artifact ──────────────┘

  Two substrates underneath:
    CPU  (pybullet / plain MuJoCo / pure Python)  — flexible, legible, morphology, dev
    GPU  (mujoco-warp, thousands of worlds/kernel) — honest evaluation, control, scale
```

The genotype→phenotype pipeline is the heart, and the studio built it before it knew that is
what it was. **The DSL is a genome.** An L-system string is a genome. A neural network's weight
vector is a genome. In every case a compact recipe unfolds into a phenotype the objective can
measure, and selection does the rest.

---

## 2. What is PROVEN (measured, on this box)

These are not aspirations. Each has a committed artifact and a number behind it.

| capability | proof | where |
|---|---|---|
| **Evolve a body** from a genome | 447 B → 238 bones in 1.2 ms; mutation gives a *family*, not clones or noise | `core/terrarium.py`, Terrarium ladder stages 0–1 |
| **Evolve a nervous system** for a fixed body | a robust rhythmic gait: periodicity 0.11 → **0.78** | `core/trainables/brain_gpu.py`, `docs/objectives/brain_gpu.trained.json` |
| **Evolve a DATA feature** against physics-not-taste | economy trained over 400,000 price configs; the optimiser *refused* to fix a structural flaw with prices and exposed the missing `elasticity` field instead | `core/trainables/economy.py` |
| **Evaluate HONESTLY** — tell skill from luck | multi-restart worst-case scoring; a 1-micron start nudge that once swung a result 5.5 body lengths now moves it 0.5 | `robustness` measure, `TRAINING_PROTOCOL.md` §3.5 |
| **Run the population on the GPU** | **2,358 evals/sec at 16,384 worlds** (6.95 s, 1.5 of 24 GiB, card at 39 °C) vs pybullet's 70; P-cores idle | `core/mjcf.py` + `brain_gpu.py` |
| **Witness the result**, not just score it | Hildebrand footfall diagram + periodicity + a rendered gait strip; a foot is *discovered*, not declared | `core/gait.py`, `core/gait_mj.py` |
| **Contain a risky run** and prove containment | a training run wrote exactly one artifact and touched nothing live — the membrane measured it | `core/membrane.py` |

The through-line: **the LLM sits at the top (authoring constraints) and the bottom (reading the
exploit report). Never in the middle.** An LLM hand-tunes ~20 edits an hour; the trainer does
~30,000 evaluations a second. Six orders of magnitude. The division of labour is the whole idea.

---

## 3. What is ONE STEP AWAY (the tools exist; only the objective is unwritten)

This is where the word "possibilities" earns its place. None of the below needs new
infrastructure — each is an objective file and a training run.

### A bestiary, grown overnight
The GPU evaluates thousands of controllers in one kernel; the CPU evolves bodies. Point them at
each other and you get a **menagerie**: N different genomes, each grown into a body, each given
its own trained gait, generated while you sleep. Nobody animates them. Nobody rigs them. The
gait is not keyframed — it is *evolved*, and it is robust because it was scored from many starts.
A world that is populated by creatures no human designed is the Terrarium's original promise,
and locomotion was the missing rung. It is no longer missing.

### Crawl → walk → run
The first honest winner is a robust *crawl* (it stayed low: torso height 0.037). This is not a
wall; it is an under-weighted objective term. The pins name the fix precisely — raise the weight
on "get off the floor," correct the energy scale that was guessed 90× wrong. One ~60-minute GPU
run stands between the crawl and an upright stride. Gaits are a **curriculum**, and we are on the
first rung of it by choice, not by limit.

### Gaits that generalize — terrain and task curricula
The same brain, scored across flat ground *and* slopes *and* gaps *and* rubble, cannot overfit
to one surface. Because restarts and terrains are the same axis as population on the GPU (they
are all just more worlds), a curriculum of environments costs no new machinery — only more
worlds in the batch, and there are 22 of 24 gigabytes still free.

### Co-evolution
Body and brain can be evolved together by alternation: evolve the body on the CPU against the
best-so-far brain, then evolve the brain on the GPU against the new body, and repeat. Predator
and prey can be co-evolved against each other. This is Karl Sims' 1994 result, which this studio
now has every part to reproduce — and to exceed, because Sims had neither a 4090 nor an LLM
writing his fitness functions.

### The whole game, as data
The creature was the hard case — contact-rich, chaotic, control-in-the-loop. Everything else in
a game is *easier*. Spawn tables, loot distributions, mission rewards, faction economics, damage
curves, enemy compositions, difficulty ramps, procedural layouts — all of it is DATA, and all of
it can be **evolved against an objective instead of hand-tuned by argument.** Write what a good
economy *does* (money velocity in a band, no single dominant route, price shocks that decay);
the trainer finds the numbers. The exploit it finds on the way is free QA: it is the degenerate
strategy your players would have found in a week, surfaced in an afternoon.

---

## 4. What it means for how the game gets MADE

The deepest possibility is not any single feature. It is a **shift in how content comes to
exist.**

- **From authoring to constraint-writing.** The expensive, slow, taste-laden act of *making* a
  creature / economy / level becomes the faster, checkable act of *specifying what would make one
  good*. The LLM is good at the second and bad at the first; the trainer is the reverse. Together
  they cover the whole task.
- **From "does it look right?" to "is it measurably good?"** A gait is not judged by an animator's
  eye but by periodicity, robustness, and distance — numbers that cannot be fooled and do not get
  tired. The witness (`gait_mj.py`) still renders the thing so a human *can* look, but the human is
  the second opinion, not the gate.
- **The exploit is the product.** A degenerate winner is the optimiser auditing your design at 35
  kHz and finding the hole you would have defended in review. Every exploit this system has found —
  the lollipop, the satisficer, the outriggers, the lottery ticket — was a real flaw in a real
  specification, surfaced faster than any playtest could. Design review, run at machine speed.
- **Content that scales past a team's hands.** A studio can hand-build a dozen creatures. This can
  evolve a thousand overnight, each one honest, each one different, none of them animated. That is
  a different order of content production, and it is the reason any of this matters for a *game*.

---

## 5. The two substrates — and why you need both

This is the single most important engineering fact, and getting it wrong wastes days.

**CPU — flexible, legible, and where morphology lives.**
pybullet and plain MuJoCo on the CPU are for development and for bodies. Errors are synchronous
and land in Python where you can read them. You can change everything between runs. Crucially,
**morphology is not GPU-batchable** — `mujoco-warp` batches N copies of *one* model, so a
population of *different bodies* has no single model to batch. Bodies are evolved on the CPU, one
at a time or across a process pool.

**GPU — honest evaluation, control, and scale.**
`mujoco-warp` runs the whole population × every restart in one kernel. This is not a speed
optimization bolted onto the CPU path; it is what makes **honest evaluation affordable**, and honest
evaluation is a correctness requirement, not a luxury (§ below). A neural controller evolved with
16 randomized restarts per genome is unaffordable on the CPU (≈32 h/run, 8 P-cores at thermal
limit) and nearly free on the GPU (≈1 h, card at 39 °C).

**The rule that makes the GPU path work:** nothing reads back from the GPU inside the rollout
loop. The brain is three Warp kernels; every measurement accumulates into device arrays; there is
exactly one transfer, after the last step. The *previous* GPU attempt did 1,575 CPU↔GPU syncs per
batch and ran **300× slower than the CPU**. The syncs, not the GPU, were the enemy.

**Why not pybullet on the GPU?** Because it cannot. Bullet has promised OpenCL physics on its own
forums since 2006, and the 2022 Quickstart Guide still writes it in the future tense. The
ecosystem's GPU path (TDS) is a separate, unmaintained C++ library that is *slower* than
mujoco-warp on this hardware. Verified, not assumed.

---

## 6. The limits — stated as plainly as the possibilities

Thoroughness means the boundaries, not just the frontier.

- **You can train DATA. You cannot train CODE.** Morphology is ~1.5 ms per evaluation; a C++
  gameplay system is ~6 minutes (LLM + UBT + PIE). Seven orders of magnitude. So push the game
  *out* of code and *into* data wherever you can — but a system that genuinely needs a build to
  evaluate is authored by hand, one at a time, and no amount of GPU changes that.
- **One rollout is a coin toss, not a measurement.** In a chaotic system — and contact-rich
  locomotion *is* chaotic — a single evaluation from a single start selects luck, not skill. This
  is not optional to fix. It is the difference between a result and an artifact, and it is the
  entire reason the GPU is needed. (See `TRAINING_PROTOCOL.md` §3.5; the old "13.52 body length"
  walker scored *worse than untrained* once measured honestly.)
- **Audit the constants you inherit.** The creature carried 35 N·m/kg of torque — ten times a
  human hip — because the number was inherited and never questioned, and it flung the body 3.4 km
  into the air. A number you inherited is not a number you chose. Sanity-check every constant
  against a real-world referent.
- **The objective is the hard part, not the compute.** Four exploits in a row (lollipop,
  satisficer, outriggers, lottery ticket) were all failures of the *specification*, not the
  optimiser. More compute on a wrong objective just finds the exploit faster. The LLM's whole
  value is here.
- **Open-ended evolution is NOT solved.** Thirty years of ALife has not beaten stagnation. This
  system does *development* — reliable, bounded, authorable — and lets evolution be a slow,
  supervised bake. Do not ship open-ended evolution as a live game feature and expect it to keep
  producing novelty. It won't.
- **The safety envelope is load-bearing, not decoration.** Every risky run goes in a membrane
  that proves it touched nothing live. Growth is *total* (the L-system cannot fail to terminate —
  runaway growth is unrepresentable, not merely guarded). Malcolm's envelope admits or refuses
  every organism before birth. The whole thing is deterministic and default-off. These are the
  reasons this is safe to build, and they are not to be removed for convenience.

---

## 7. The path from here

The ladder, re-read in the light of this session:

1. **Body** — grow a genome into a skeleton and mesh. ✅ done.
2. **Family** — mutate; get a family, not clones or noise. ✅ done.
3. **The trainer** — the LLM writes constraints, the machine turns the crank. ✅ done.
4. **Honest evaluation** — worst-of-N restarts on the GPU; skill, not luck. ✅ done this session.
5. **Locomotion** — a robust, repeating gait. ✅ done this session (a crawl; the objective revision
   to an upright walk is written and waiting).
6. **Upright walk → run** — raise the torso-height weight, fix the energy scale. One GPU run away.
7. **A bestiary** — many bodies, each with an evolved gait, grown overnight. Tools all exist.
8. **Co-evolution and curricula** — body+brain together; gaits across terrains. Tools all exist.
9. **The whole game as data** — every tunable evolved against an objective, not argued into place.
10. **A game** — a world populated by creatures nobody designed, moving with gaits nobody animated.

The distance from here to rung 10 is not a distance of missing technology. It is a distance of
objectives yet to be written — which is exactly where a language model belongs, and exactly where
the human's taste for what makes a *good* game becomes the specification the machine optimizes
toward.

> We built a genotype→phenotype pipeline before we knew that is what it was, put an optimiser
> under it that runs six orders of magnitude faster than a person can tune, learned the hard way
> that a measurement taken once is a measurement not taken at all, and moved it onto a processor
> that does the honest version for free. What remains is to decide what GOOD means — and to let
> the machine go and find it.

---

## 8. Files that make up the engine

| file | role |
|---|---|
| `core/trainer.py` | the generic GA + objective compiler; auto-selects CPU pool or GPU batch |
| `core/trainables/<f>.py` | a **domain** — `seed`/`mutate`/`measure`, reporting FACTS only |
| `docs/objectives/<f>.json` | an **objective** — LLM-authored, physics not taste, ≥1 `maximize` term |
| `core/terrarium.py` | the genome→body grower (bounded L-system; total, deterministic, sealed) |
| `core/mjcf.py` | bone tree → MJCF; the three load-bearing physics settings live here |
| `core/trainables/brain_gpu.py` | population × restarts in one `mujoco-warp` kernel; the anti-lottery |
| `core/gait.py`, `core/gait_mj.py` | the witness — footfall diagram, periodicity, robustness, render |
| `core/membrane.py` | seal any run in a copy and prove it touched nothing live |
| `core/malcolm.py` + `docs/envelope.json` | the envelope — admit or refuse every organism before birth |
| `docs/TRAINING_PROTOCOL.md` | the method, in full, including the honest-evaluation discipline |
| `docs/TERRARIUM_DESIGN.md` | the organism, its six safety rules, and the ladder |
