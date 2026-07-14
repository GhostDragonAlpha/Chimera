# The Terrarium — a growing organism, sealed in glass

> **STATUS: DESIGN ONLY. No code exists. Nothing runs. This document is inert.**
>
> A terrarium is alive, growing, and watchable — and it **cannot get out**.
> That is the whole design, in one word.

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

- Headless, no render, on the CPU: 24 workers on the i9-13900K's 24 cores.
- Bounded per night: `P <= 64`, `G <= 200` → ~10⁴ evaluations ≈ **minutes**, not hours.
- Output: **genomes in `terrarium.db`. Nothing else.** No heuristics. No graph writes. No
  board tasks.
- The GPU is idle at Night anyway — the LLM owns it, the game does not.

The classic ALife failure mode — creatures discovering and exploiting your physics bugs — is
here a **feature**: it is a free fuzzer for Chaos. But the finding crosses the membrane as a
*file a human reads*, never as an automatic graph write (Rule 1).

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

| # | what | time | touches | worst case | KILL IF |
|---|---|---|---|---|---|
| **0** | `grow(genome, seed) -> .obj`. One pure Python file. Writes an OBJ to a scratch dir. | **½ day** | **nothing** | a wasted afternoon | it never makes a shape you'd look at twice |
| **1** | Mutate the genome. Grow 100. Render a contact sheet of 100 thumbnails. | **1 day** | **nothing** | a wasted day | **mutations give noise or clones — not a *family*** |
| 2 | Morphology → UE5 static mesh via Geometry Script. | 2–3 days | one level | a weird mesh | it's ugly, unshippable |
| 3 | Skeleton → Chaos articulated body. It falls over. Fine. | ~1 week | one level | it flops around | bodies are unusable |
| 4 | Offline evolution. Night. Headless. Bounded. | ~1 week | a new .db | wasted CPU-nights | evolution converges to mush |
| 5 | Make it a game. | — | — | — | — |

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
