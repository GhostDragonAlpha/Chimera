> **DEPRECATED** — This document describes the old approach.
> Read `AGENT_ONBOARDING.md`, `DECISION_METHOD.md`, and `EMERGENT_WORKFLOW.md` instead.
> The thought chain is at `docs/THOUGHT_CHAIN.md`.

# The Terrarium — a growing organism, sealed in glass

> **STATUS (2026-07-14): STAGES 0 AND 1 ARE BUILT, TESTED, AND PASSED.**
> `core/terrarium.py` · `core/evolve.py` · `core/trainables/creature.py` · 16/16 tests.
> Built entirely inside a membrane; the studio saw nothing until the tests were green.
>
> A terrarium is alive, growing, and watchable — and it **cannot get out**.
> That is the whole design, in one word.

---

## WHAT ACTUALLY HAPPENED (read this before the design)

**Stage 0 — PASSED.** 447 bytes of genome → **238 bones in 1.2 ms** → 3,808 triangles in
1.8 ms → an `.obj` you can open. The totality proof is not a claim, it is a **bomb**: a genome
built to explode (`A → F[+A]F[-A]A`, strictly expanding, no terminal, asking for 999
iterations — 4⁹⁹⁹ symbols in an unbounded L-system) **terminates anyway**. Not because a guard
caught it; because there is no path where it doesn't.

**Stage 1 — PASSED.** 24 individuals from one genome: **not clones, not noise, a FAMILY** —
shared body plan, real variation in density, branch angle, crown shape, and one genuine
**deformity** where a mutation reached *structure*, not merely parameters. **The indirect
encoding works.**

**But it grew TREES.** The fix was not a tweak — it was a category error:

> ### A TREE IS A RECURSION. A CREATURE IS A CASCADE.
>
> `A → F[+B]F[-B]A` — **A calls A.** Self-similarity **is** the definition of a plant: every
> branch is a smaller tree. It cannot make anything else.
>
> An animal is a **finite staged program** — `C → S → G → K → P` — where each symbol fires
> **once** and hands off to a **different** one. That is what Hox genes do: **positional
> identity**. Segment 3 *knows* it is segment 3, which is why a fly's thorax grows wings and
> its abdomen does not, from one genome.
>
> Consequence: a cascade **terminates on its own**, so `MAX_DEPTH` stops being the mechanism
> that bounds growth and becomes a mere backstop.

Added: `( )` = **bilateral mirror** — `(X) → [X][X-flipped]`, a pure string rewrite *before*
interpretation, so the turtle never has to know animals have two sides. Yaw and roll flip;
pitch does not (down is down on both flanks). Bilateral symmetry in one operator.

**Then the human said: *"this needs to be trained like an ai model not with llm thinking (too
slow)."* They were right.** `grow()` is 1.2 ms; on 24 cores that is **35,634 evals/sec,
measured**. An LLM hand-editing a grammar manages ~20/hour. Six orders of magnitude.

**My hand-designed quadruped scored 0.00000. It TOPPLES.** The creature I built by *reasoning*
cannot stand up, and the optimiser proved it in three seconds.

### THE CREATURE IS NOT DONE, AND I KNOW EXACTLY WHY

Three degenerate optima, in order — each statically excellent and biologically absurd:

1. **THE LOLLIPOP** — a boulder on a pole over a tripod. Mass goes as *r²* and parsimony was
   charged **per bone**, so one enormous bone was free.
2. **THE BLOB ON STILTS** — minimally compliant. The objective was made only of *bounds*, so
   the optimiser stopped dead at "barely legal" (see the SATISFICER trap in
   `docs/TRAINING_PROTOCOL.md` §3).
3. **THE MAST WITH OUTRIGGERS** — legs sprawled *flat on the ground*, giving a huge support
   polygon and almost no mass, while a heavy rod held the centre of gravity high.

> **Three exploits in a row is not a message about your parameters. It is a message about your
> FRAME.** Static stability can **always** be gamed by outriggers, because a creature is not
> defined by how it **stands** — it is defined by what it **does**.

**THE NEXT OBJECTIVE MUST BE LOCOMOTION** — distance travelled under Chaos physics. It cannot
be faked, because outriggers do not walk. That is what Karl Sims used in 1994 and what should
have been used here.

### UPDATE 2026-07-14 — locomotion was built, and it revealed a FOURTH exploit deeper than the three above

Locomotion happened. And it taught a lesson the three static exploits could not: **the frame
was not the only thing broken — so was the MEASUREMENT.**

The first locomotion winner travelled 13.52 body lengths and was not a gait at all. It had
**periodicity 0.25** (no repeating cycle), a **one-micron** nudge to its start cost it 5.5 body
lengths, and under honest physics it scored **2.41 — worse than an untrained brain.** That is
Lyapunov divergence: no attractor, no limit cycle, no gait. Every genome had been scored by ONE
rollout from ONE start, which in a chaotic system is a **coin toss**, so the GA spent 80,000
evaluations selecting lucky dice. (The root cause ran deeper still: an inherited torque of 35
N·m/kg — ten times a human hip — flung the body 3.4 km up, and pybullet's solver *contained* the
violence instead of NaN-ing, so it lived permanently airborne with no contact to form a cycle.)

**THE FOURTH EXPLOIT — THE LOTTERY TICKET — is a hole in the EVALUATION, and no objective could
have closed it.** The fix: score every genome from many randomized restarts and keep the
**worst** (`robustness` = worst/mean); add `periodicity` as a first-class objective term, because
a gait is a limit cycle and nothing had ever rewarded rhythm. Honest evaluation costs 16× the
compute, which the CPU cannot afford and a GPU does not notice — so this is where the creature
moved onto `mujoco-warp` (§5, §6 below, both now superseded by the GPU path).

**RESULT:** the first *honest* winner is a robust rhythmic **crawl** — periodicity 0.78,
robustness 0.76, distance 3.24, all repeatable from any start. It did not stand up (torso 0.037);
that is an under-weighted objective term, not a wall, and the revision is written. See
`docs/THE_EVOLUTION_ENGINE.md` for what this unlocks and `docs/TRAINING_PROTOCOL.md` §3.5 for the
honest-evaluation discipline in full. **Stage 3 is done; Stage 5–6 are now the real next steps.**

---

## 0. Why this is scary, and which fears are real

Three fears. They are not equal.

| Fear | Real? | Answer |
|---|---|---|
| It grows without bound and eats the machine | **No — engineerable to zero** | Runaway is made *unrepresentable*, not *guarded against*. See §2. |
| It destabilises the studio that currently works | **YES — the serious one** | The studio auto-commits, auto-pushes, auto-promotes heuristics, and `pi` reads the handoff log and acts on it. On 2026-07-14 a *fabricated* solver blocker was auto-pushed and picked up by `pi` within ~10 minutes. **A self-replicating system must never be inside that loop.** See §4 and §6. |
| It eats months and isn't fun | **YES — but it's a product risk, not a safety risk** | Cannot be engineered away. Can be made cheap to discover: Stages 0–1 cost ~1.5 days and answer it. See §8. |

### The Jurassic Park lesson, stated precisely

The park's containment failed because it was **procedural** — rules the system was *asked to follow*. The lysine contingency and the all-female population were bolt-ons layered over a system that was perfectly capable of violating them.

This design uses **structural** containment — states the system **cannot express**. A bounded total grammar cannot loop forever in the same way a `for i in range(12)` cannot run thirteen times. It is not a rule being obeyed. It is a shape that has no room for the failure.

(The studio's regulator is already named `malcolm`. That is not an accident, and the joke should be earned.)

---

## 1. Architecture in one picture

```
        THE MEMBRANE  (one-way, human-gated)
   ┌──────────────────────────────────────────────────────────┐
   │                                                          │
   │   THE TERRARIUM            docs/world/terrarium.db       │
   │                            (its own store — NOT dna.db)  │
   │                                                          │
   │   genome ──grow()──▶ morphology ──▶ body ──▶ behaviour   │
   │   bounded            deterministic   Chaos    (later)    │
   │   total              pure fn                             │
   │                                                          │
   └──────────────────────────────────────────────────────────┘
                    │
                    │  reports (files a HUMAN reads)
                    ▼
              ┌───────────┐
              │  A HUMAN  │  ← the only channel. Machine → human → studio.
              └───────────┘
                    │
                    ▼
   THE STUDIO GENOME   docs/world/dna.db, PENDING_HEURISTICS.md, task_board, …
   The Terrarium may NEVER write here. Not by convention — by construction.
```

**Two genomes. One membrane. No write-back.**

---

## 2. The six rules

### Rule 1 — THE MEMBRANE. The Terrarium never writes to the studio.

Not "shouldn't". *Cannot.* `core/terrarium/` must not import `graphify_record`, `record_*`,
`task_board`, `capcom`, or any `world_store` write path. A unit test asserts the import
graph, so the moment someone adds the import, CI fails.

Why this rule exists: without it, the organism's fitness search is optimising against the
studio's own development. That is the actual grey-goo scenario in *this* architecture — not
replication, but **substrate contamination**.

### Rule 2 — TOTALITY. Runaway growth is not a bug. It is unrepresentable.

The genome is a **bounded parametric L-system**. Development is a `for` loop with a hard
symbol cap. There is no `while`. There is no recursion. There is no genome — valid,
malformed, or adversarial — that can make `grow()` fail to terminate.

```python
def grow(genome: Genome, seed: int) -> Morphology:
    """TOTAL: provably terminates for every input. No while. No recursion."""
    s = genome.axiom
    for _ in range(MAX_DEPTH):              # <= 12. A for loop. It cannot run 13 times.
        s = rewrite(s, genome.rules)
        if len(s) > MAX_SYMBOLS:            # <= 50_000. Hard truncation.
            s = s[:MAX_SYMBOLS]
            break
    return interpret(s, seed)               # turtle -> skeleton
```

This is the load-bearing safety property. Everything else is hygiene.

### Rule 3 — DETERMINISM. `grow(genome, seed)` is a pure function.

No wall clock. No global RNG. No I/O. Same inputs → byte-identical output. Therefore every
creature is reproducible, every bug is reproducible, and "what just happened?" is always
answerable by re-running it. Hash the morphology; diff two runs.

(The studio already bans `Date.now()` / `Math.random()` in workflow scripts for exactly
this reason. Same principle, same payoff.)

### Rule 4 — THE ENVELOPE. Malcolm admits or refuses every organism, before birth.

New axes in `docs/envelope.json` — the *existing* container does the work, no new safety
system:

| axis | family | band | why |
|---|---|---|---|
| `organism_symbols` | systemic | [1, 50000] | phenotype complexity ceiling |
| `organism_derivation_depth` | systemic | [1, 12] | the `for` bound, made visible |
| `organism_bodies` | experience | [1, 64] | rigid bodies per creature (Chaos cost) |
| `terrarium_population` | experience | [1, 64] | how many may live at once |
| `growth_ms_per_frame` | hardware | [null, 4.0] | 24% of a 16.6 ms frame |
| `terrarium_vram_mb` | hardware | [null, 2048] | 2 GB ceiling |

`malcolm admit` runs **before** an organism exists. Breach → it is not born.

### Rule 5 — THE OFF SWITCH. Default OFF, deletion restores the prior state exactly.

`CHIMERA_TERRARIUM=0` by default; the module is inert unless explicitly enabled. It adds
**zero** gates, **zero** pipeline stages, **zero** DNA-graph schema changes. `rm -rf
core/terrarium docs/world/terrarium.db` returns the studio byte-identical.

### Rule 6 — NO AUTONOMY. The Terrarium is hand-cranked.

It does **not** run inside `dream_loop`, `gardener`, `rehearsal`, `ralph_loop`, `preflight`,
or `postflight`. It runs when a human types the command. Full stop.

This is the rule that exists because of what happened on 2026-07-14, and it is not
negotiable until the thing has earned trust over months.

---

## 3. The genome (~256–1024 bytes)

```
header      : version, axiom_id, seed_hint
rules       : N productions — (lhs, rhs_module_string, probability)
params      : segment_len, branch_angle, scale_decay, thickness, symmetry_k
regulatory  : a small threshold network, K <= 4, that switches rules on/off
              by developmental age + local context
```

**The regulatory network is where differentiation comes from** — the same genome producing
legs *and* a spine. Keep `K <= 4`.

That is not a taste call. `K` is Kauffman's coupling parameter: below it the network freezes
into order, above it dissolves into chaos, and life sits in the narrow critical band between.
**The studio's envelope already caps `coupling_degree_k` at 4.** You already have the right
constant, for the right reason, written down before this document existed.

### The one design decision that decides everything

**INDIRECT ENCODING.** The genome must be a *recipe*, never a *blueprint*.

A human genome is ~750 MB and specifies ~37 trillion cells. That is not storage — it is a
compressed generative rule set that unfolds in an environment. If gene 17 means "the vertex
position of the left elbow", the system will not scale, will not evolve, and will never
surprise you. If gene 17 means "branch, rotate, recurse with decay", complexity comes free.

Karl Sims' 1994 *Evolving Virtual Creatures* — the closest prior art to what we are
building — encoded creatures as a **directed graph with recursive node references**. Indirect,
compact, generative. That is the target.

---

## 4. Development pipeline

1. **Rewrite** — bounded L-system derivation (§2). Cost: ~2 ms of CPU, once, at birth.
2. **Interpret** — 3D turtle → skeleton: `[(parent_idx, transform, radius, kind)]`.
3. **Pattern** *(optional, later)* — reaction–diffusion over the skin for pigment / organ
   sites. 256³, 10 steps ≈ **2.7 ms/frame**, bandwidth-bound. Skip entirely for Stage 0.
4. **Emit** — skeleton + mesh.

### In UE5

| need | subsystem |
|---|---|
| mesh from skeleton at runtime | **Geometry Script** |
| scatter / grow many | **PCG** |
| articulated body, joints | **Chaos** |
| many simple organisms | **Mass Entity** |
| triangle budget | **Nanite** (a 10⁵–10⁶-tri creature is nothing) |

---

## 5. Fitness and evolution — offline only, in the Night

**Evolution is a bake. Development is a runtime.** Two budgets, never one.

- Output: **genomes in `terrarium.db`. Nothing else.** No heuristics. No graph writes. No
  board tasks. The finding crosses the membrane as a *file a human reads*, never as an automatic
  graph write (Rule 1).
- **Morphology** (bodies) is evolved on the **CPU** — `mujoco-warp` batches N copies of *one*
  model, so a population of *different bodies* has no single model to batch. Bounded per bake:
  `P <= 64`, `G <= 200` → ~10⁴ evaluations ≈ **minutes**.
- **Control** (brains, for a fixed body) is evolved on the **GPU** — and this is not a speed
  choice, it is a correctness one. Honest evaluation (worst-of-16 randomized restarts, §51's
  fourth exploit) is unaffordable on the CPU and nearly free on `mujoco-warp`: **2,358 evals/sec
  at 16,384 worlds, on 1.5 of 24 GiB.** `core/trainables/brain_gpu.py`.
- **The GPU is NOT idle at Night — it is the evaluation engine.** This changes the co-tenancy
  story in §6: the LLM and the trainer now genuinely contend for the card, so a control bake and
  an LLM night cannot run at the same instant. Time-share them (`lm_gateway evict` frees VRAM),
  or run the control bake when the LLM is quiet.

The classic ALife failure mode — creatures discovering and exploiting your physics bugs — is
here a **feature**: it is a free fuzzer for Chaos, and it has already paid out four times (the
lollipop, satisficer, outriggers, and lottery ticket were all real specification holes surfaced
at 35 kHz).

---

## 6. Compute budget (measured 2026-07-14 on the actual box)

`RTX 4090 · 24.0 GB VRAM · i9-13900K 24C/32T · 127.8 GB RAM`

| component | per frame | VRAM | verdict |
|---|---|---|---|
| genome | ~0 | ~1 KB | free |
| L-system growth, 10⁵ modules | ~2 ms CPU **once, at birth** | — | free |
| reaction–diffusion 3D 256³ ×10 | 2.7 ms (bandwidth-bound) | 134 MB | fits |
| Chaos, 24 articulated creatures | ~5 ms | small | fits |
| Nanite render | in normal render cost | 1–4 GB | fits |
| **organism runtime total** | **~8–10 ms of 16.6** | **~2–5 GB** | **comfortable** |

**The organism is cheap.** The scarce resource is VRAM, and the LLM currently holds 20.8 GB
of 24 — leaving 2.76 GB. The organism is not the problem; the co-tenancy is. Time-share the
GPU by circadian phase (Day = game, Night = LLM); `lm_gateway evict --all` already exists.

The roofline ridge point is 82.6 TFLOP/s ÷ 1008 GB/s = **~82 FLOP/byte**. Reaction–diffusion
runs at ~1.25 FLOP/byte — **66× below the ridge**. Every kernel here is bandwidth-bound, so
the only 4090 spec that matters is its **1008 GB/s**, not its 82 TFLOPS.

---

## 7. What we will explicitly NOT do

- ❌ Change the DNA graph schema.
- ❌ Put self-replication anywhere near the studio's own pipeline.
- ❌ Let the Terrarium write anything the studio reads automatically.
- ❌ Run it inside any autonomous loop (`dream_loop`, `gardener`, `rehearsal`, `ralph`).
- ❌ Enable it by default.
- ❌ Ship **open-ended evolution** as a game feature. Thirty years of ALife has not solved
  stagnation. Build **development** (reliable, authorable, debuggable); let evolution be a
  slow background bake, if at all.

---

## 8. The ladder — every rung is independently abandonable

The idea only *feels* risky because it sounds like one leap. It is not. Every stage below
stands alone, is worth having on its own, and has an explicit **kill criterion**.

| # | what | status | KILL IF |
|---|---|---|---|
| **0** | `grow(genome, seed) -> .obj`. One pure Python file. | ✅ **DONE.** 447 B → 238 bones (1.2 ms) → 3,808 tris. 16/16 tests. | it never makes a shape you'd look at twice |
| **1** | Mutate. Grow 24. Look at the contact sheet. | ✅ **PASSED.** A *family* — not clones, not noise, plus a real structural deformity. | mutations give noise or clones, not a *family* |
| **1.5** | **The trainer** — get the LLM out of the inner loop. | ✅ **DONE.** `core/evolve.py` + the generic `core/trainer.py`. 35,634 evals/sec. | — |
| **2** | Morphology → UE5 mesh via Geometry Script. | ⬜ not started | it's ugly, unshippable |
| **3** | **LOCOMOTION.** Chaos physics. Fitness = **distance travelled**, HONESTLY (worst-of-16 restarts). | ✅ **DONE 2026-07-14.** A robust rhythmic crawl: periodicity 0.78, robustness 0.76. It also proved static geometry cannot specify "creature" (3 exploits) *and* that one rollout cannot measure one (the 4th). | it can't learn to move at all |
| **3.5** | **Honest evaluation on the GPU.** `mujoco-warp`, whole population × restarts in one kernel. | ✅ **DONE 2026-07-14.** 2,358 evals/sec at 16,384 worlds. The anti-lottery. `core/trainables/brain_gpu.py`. | it can't tell skill from luck |
| **4** | Crawl → upright walk → run; then a bestiary. | ⬜ **THE REAL NEXT STEP.** Raise the torso-height weight, fix the energy ref (both named by the winner's pins). One GPU run to upright. | evolution converges to mush |
| 5 | Make it a game — a world of creatures nobody designed. | ⬜ (see `docs/THE_EVOLUTION_ENGINE.md`) | — |

### Stage 1 is the whole thesis

**If mutating a genome produces a *family* of related-but-different creatures — that is the
indirect encoding working, and everything downstream follows.**

**If it produces noise, or 100 identical things — the idea is dead, and you found out in a
day.**

Stages 0 and 1 touch no engine, no graph, no gate, no pipeline. They are a pure function and
a contact sheet. **The risk is one and a half days.**

---

## 9. First command, when you're ready

```powershell
python -m core.terrarium grow --genome docs/terrarium/seed0.json --out scratch/organism.obj
```

Pure function in. OBJ file out. Nothing else touched.
