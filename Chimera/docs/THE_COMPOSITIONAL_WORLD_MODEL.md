# The Compositional World Model — everything specific, trained separately

> **The human's thesis, 2026-07-17, verbatim intent:** *"Not a world model like they are
> making with a trained everything — I'm making a world model with everything specific
> being trained separately."*
>
> This document names the destination. It is INTENT, per the Contract's rule — claims
> about intent do not rot; claims about state are pointers to the commands that print
> them. Read `TRAINING_PROTOCOL.md` for the method, `THE_EVOLUTION_ENGINE.md` for the
> machine, `THE_MATTER_MODEL.md` for the substrate, `CHIMERA_VISION.py` for the seed
> this all serves.

---

## 0. The one sentence

**A world model assembled from many small models — each trained separately against its
own machine-checkable objective, each verified piece-by-piece through the studio's own
gates, composed inside a real engine that keeps receipts — instead of one giant model
trained end-to-end that dreams everything at once and can prove nothing.**

---

## 1. The two positions

There are two ways to build a "world model videogame."

**The monolith** (the frontier-lab position; every shipped demo of it shares the shape):
train one enormous model on everything at once — video, actions, worlds — and let it
dream the game frame by frame. As of this document's writing the known public examples
(Genie-class interactive world generation, the playable neural-Minecraft demos, the
game-video generators) all share three structural holes, and they are not polish gaps:

1. **No persistence.** Walk away from a thing and the dream forgets it existed.
2. **No physics guarantees.** Nothing is measurable; objects merge; gravity negotiates.
3. **No game underneath.** No economy, no progression, no consequence — a steerable
   dream, not a game.

**The composition** (this studio's position): the world is made of many specific
pieces — a weather, an economy, a creature's body, a creature's brain, a memorial
curve, a director's ecology — and **each piece is trained separately**, against its own
objective, by an optimiser that runs six orders of magnitude faster than a person can
tune, then composed by the engine. The engine — not a context window — holds the state.

Now read the seed's Design Laws against the monolith's three holes:

| Seed law (`CHIMERA_VISION.py`) | The monolith's hole it answers |
|---|---|
| Law 4: *"Nothing observed is lost. Footprints, pits, shelters, debts of kindness persist across generations."* | No persistence |
| Law 1: *"The world answers the body — every verb has physical, audible, visible consequence."* | No physics guarantees |
| Law 2: *"The bad ending is a costless life... taught only through consequence."* | No game underneath |

The seed was written before this thesis had a name, and it is already the exact negation
of the monolith's failure modes. **The winnable first is not "first neural game" — that
ship has sailed. It is the first persistent, physically-grounded, consequence-bearing
world-model game.** Persistence and grounding are THE open problems in that literature;
this architecture gets them free, because the engine is real.

---

## 2. Why composition wins here — and what it costs

- **It fits the hardware.** Each piece is small: the trainer does 26k–37k evals/sec on
  this box for data domains; a brain population runs 16,384 worlds in one GPU kernel at
  1.5 of 24 GiB. The monolith needs a frontier lab's cluster. You cannot out-compute
  them; **they cannot out-decompose you**, because their whole bet is against
  decomposition.
- **Every piece is verifiable.** A trained piece has pinned walls, a rep battery, a
  witness, a why-chain that terminates at PHYSICS. You cannot unit-test a dream; you can
  audit a trained economy — this studio has (400,000 configs; the optimiser refused to
  fix a structural flaw with prices and exposed the missing `elasticity` field instead).
- **Persistence is free.** State lives in the engine and `core/world_store.py` (proven
  at 1M nodes, sub-ms). Law 4 is trivial here and unsolved in the monolith world.
- **Swappability.** Retrain the weather without touching the creatures. The monolith
  entangles everything it learns; the composition isolates every failure.
- **The exploit is the product.** Each separate objective gets audited by its own
  optimiser at 35 kHz (the lollipop, the satisficer, the outriggers, the lottery
  ticket — each a real spec hole surfaced faster than any playtest). A monolith's
  failures are undiagnosable; a composition's failures arrive labeled with the piece
  that owns them.

**The honest costs, stated as plainly:**

- **The interfaces are authored, not learned.** The DSL is the interface contract
  between pieces. A monolith gets cross-system coherence implicitly (when it gets it at
  all); we must *earn* it, piece by piece, at the seams.
- **The seams are where the bugs live.** When N separately-trained systems compose,
  nothing yet measures whether the trained weather starves the trained economy. §5 is
  the answer, and it is the one genuinely new machinery this thesis demands.
- **No free generalization.** A new system is a new domain + objective — work, every
  time. That is also why it stays auditable.

---

## 3. The identity: this studio already IS a compositional world-model trainer

This is the load-bearing observation, and the full-system read makes it unmistakable.
The workflow was never merely process — **it is a per-piece training harness**, and it
says so in its own founding documents:

> `docs/GAUNTLET.md`, the curriculum's commission, verbatim: *"it'll also be like
> training an AI — if an AI was one feature, think of it like that."* And below it:
> *"The AI-training reading is literal: a feature enrolls like a model entering
> training; grade bands are curriculum-learning stages; every passed checkpoint is a
> saved, evaluated state in its transcript; the PhD dissertation... is the final eval
> before deployment."*

Map the machinery onto a training loop and every organ lands:

| Training-loop concept | The studio organ that already is it |
|---|---|
| genome / parameters | the DSL (`tests/dsl_grammar/*.chimera`) — "THE DSL IS THE GENOME" |
| genotype→phenotype | `core/game_code_generator.py` → UBT → the running game |
| per-piece learner | `core/trainer.py` + `core/trainables/<f>.py` + `docs/objectives/<f>.json` |
| loss / objective | the objective JSON — physics, never taste, ≥1 `maximize` term |
| honest eval (anti-overfit) | worst-of-N restarts; `robustness`; `core/gait.py` the witness |
| training curriculum | `core/curriculum.py` K→PhD, 7 bands, 69 checkpoints |
| accumulated verification | `core/rep_engine.py` — resolution through repetition, tiers 0–4 |
| eval-in-deployment | `core/sleepwalker.py` beats in PIE; telemetry; the result grade |
| the training gate | `core/training_gate.py` — un-enrolled work cannot even close |
| regularizer / envelope | `core/malcolm.py` — 15 walls, admission control, edge-of-chaos |
| which piece trains next | `core/helm.py` — the seed-vs-reality gap, ranked |
| experience replay / consolidation | circadian night: `dream_loop`, distiller, gardener, history book |
| checkpointed weights | the DNA graph — every mutation, build, verification, recorded typed |

Nothing in that table is a metaphor being stretched. "Train the piece you worked" is
enforced at task closure. Features literally cannot finish without accumulating reps.
**The compositional world model is not a pivot. It is the name of the building.**

And the composition is *governed*, not hoped for: Malcolm's walls already constrain the
composition itself — `interacting_systems_per_slice [3,7]`, `coupling_degree_k ≤ 4`
(Kauffman's criticality band: below it the network freezes, above it dissolves; the
regulatory-network cap in `TERRARIUM_DESIGN.md` §3 lands on the same constant for the
same reason), `active_dots [2,24]`. The envelope is a composition gauge in embryo.

---

## 4. The seed is the spec — its §10 is a shelf of untrained models

`CHIMERA_VISION.py` §10 (world systems) is written as C++ shells around **data tables**.
Every table is a genome; every shell is the authored code that expresses it. That is
exactly the trainer's hard boundary (train DATA, author CODE) drawn through the middle
of every system — the C++ is written once by the generator; the data trains forever.

The trainable surface, walked system by system:

| Seed system (§10) | Its data (the genome) | What GOOD means (the objective's shape) |
|---|---|---|
| `UWeatherSubsystem` | `WIND`: gust period, storm period/duration, speeds | **The Law-4 tension made a band:** storms erase sand footprints (the memento mori) — erasure must come often enough to ache, rarely enough that prints matter. Gust energy that reads as weather, not noise; no dead calm, no permanent storm. |
| `UStarMemorialSubsystem` + `UCostlessLifeEndingDiagnostic` | `STAR`: `brightness_k`, `bright_lights_yard`; the `1−exp(−w/k)` curve | Law 2 made perceptual physics: a costless life must be *visibly* dim; distinct sacrifice weights must yield distinguishable stars; the night-light sum stays inside the lighting budget. Monotone, discriminable, bounded. |
| `USacrificeLogComponent` | `SACRIFICE_WEIGHTS` table | Weights such that endings distribute meaningfully across honest playstyles — no single act dominates the mirror; QUIET vs BRIGHT is reachable from play, not luck. |
| `UDirectorSubsystem` | stranger cadence, `SCENARIOS` mix, `can_pay` fraction, pirate trigger | An **ecology**: encounter pressure inside `active_dots [2,24]`; the design rules stay invariant under training (first stranger of a generation cannot pay; pirates only bother the visibly rich during storms) — those are HARD gates, not tunables. |
| `AGroundActor` | `SURFACE_TABLE`: traction / makes_print / dust / synth per surface | Traversal variety measurable by the sleepwalker: every surface changes movement or sound observably (Law 1); no surface is a no-op skin. |
| `UGenerationSubsystem` | inheritance rules (credit halving, heirloom carry) | Generational difficulty neither compounds to ruin nor resets to zero; the heir starts poorer but not hopeless — a band on effective progression across N simulated lives. |
| `FStationMarket` / `UFactionSubsystem` | prices, standings ladders | Already begun (`core/trainables/economy.py`); the remaining pins name the next structural loci: station specialisation, demand cycles, stock limits. |
| creatures (the terrarium line) | L-system genomes; brain weights | Done and proven — the template every row above follows (`brain_gpu.trained.json`: periodicity 0.78, robustness 0.76). |

Run `python -m core.helm targets` for the live gap; the wellspring already mints board
tasks from it. What this thesis adds is the **discipline**: when a §10 system comes up
for building, its C++ shell is authored once, and its numbers are NEVER hand-argued —
they get a domain, an objective, a membrane run, and pins.

**The economy precedent generalizes:** when a domain's pins prove the DSL lacks a locus
(as `elasticity` was proven missing by 400,000 evals), the fix flows top-down — add the
field to the DSL, teach the generator to emit it, retrain. The trainer is how the DSL
discovers what fields it needs.

---

## 5. The seams — the one genuinely new machinery

Separately-trained pieces compose; the composition itself must be measured, or we are
hoping. The instrument already exists in parts — what is new is pointing it at PAIRS.

**A seam objective is a measurable claim about two trained systems interacting.** The
seed states several outright:

- **weather × footprints** (Law 4 vs the memento mori): after a storm passes, sand
  prints are gone and METAL prints remain — `FStormEvent.prints_erased > 0` when prints
  existed; between storms, prints persist across sessions.
- **director × economy**: pirates spawn iff `credits > 200 ∧ storm_active` — a
  conditional the sleepwalker can drive both ways (rich in storm, poor in storm, rich in
  calm) and read back.
- **weather × suit**: `GE_DustClog_Storm` applied iff storm ∧ ¬indoors — four states,
  four read-backs.
- **memorial × night**: bright ancestors measurably lift the Yard's night luminance
  (`NightLightLevel` → the Lumen memorial term), within frame budget.
- **habitat × attributes**: module effects present iff inside — proximity drives GAS,
  read back per module.

Mechanically, seams are **additive to existing organs, not a new engine**:

1. **Seam rep atoms** — `rep_engine` atoms whose probe spans two features (the probe
   registry already takes arbitrary specs; a seam battery `docs/rep_batteries/seam_*.json`
   is just atoms whose evidence names both). Red seam atoms mint board tasks through the
   existing ripener/wellspring path.
2. **Seam beats** — beat scripts that drive one system to observe another
   (`docs/beats/seam_*.beats.json`), linted like all beats (a seam beat must be able to
   FAIL for the seam it tags — the tautology rule applies doubly here).
3. **Seam objectives for co-training** — when two domains' data interact (director
   cadence × economy wealth), train them **jointly against seam constraints** in one
   membrane run: the composition trained as a composition, still without touching code.

The envelope governs how many seams may be live at once (`coupling_degree_k ≤ 4` is
exactly this number); a seam that cannot be stated as physics or a read-back is not a
seam — it is taste, and taste is the human's (§7).

---

## 6. Where learned models enter — still compositional, never the renderer

Three rungs of *learned* world models fit inside the composition without ever becoming
a monolith. Each is a separate model with a separate objective, verified separately:

1. **Agents that imagine (model-based control).** A latent-dynamics model learned from
   `mujoco-warp` rollouts, per creature class; the brain plans by rolling futures
   forward in imagination. This is a true world model in the technical sense, small
   enough for this GPU, and it extends `core/trainables/brain_gpu.py` — same membrane,
   same honest evaluation (worst-of-N applies to imagined futures too, or the
   imagination becomes the new lottery ticket).
2. **The Director as a learned policy.** §10's `UDirectorSubsystem` upgraded from tuned
   cadences to a small sequence model over `world_store` telemetry streams — predicting
   the player's next stretch and steering encounter pressure — trained against the SAME
   ecology objective as its tuned predecessor, so the learned director is judged by the
   measures the tuned one was. The design invariants (first stranger cannot pay; pirates
   need storms and wealth) remain HARD gates the policy cannot trade away.
3. **Imagination as a mechanic.** The Erisaid's mirror and the memorial's visions are
   the honest home for generative models INSIDE the game — a small action-conditioned
   model fine-tuned on sleepwalker footage (the studio's automated playtests are
   action-labeled gameplay video: a world-model training set that accumulates as a side
   effect of verification). Bounded, low-res, diegetic — the dream rendered as a dream,
   inside a world that is real.

**The sleepwalker data asset deserves its own sentence:** frontier labs scrape
unlabeled video and infer actions; this studio's witness infrastructure generates
unlimited footage of its own game where every frame's causing action is *known* and the
telemetry ground truth rides alongside. That is the rarest ingredient of the monolith
approach, produced here as exhaust.

---

## 7. What this thesis does NOT claim

- **No neural renderer.** The engine renders; models feed it. Rung 6.3 is a mechanic,
  not a display path.
- **No end-to-end training.** The moment everything trains against everything, the
  audit trail dies and this becomes a worse monolith.
- **No trained fun.** `TRAINING_PROTOCOL.md` §7 stands: you can train the substrate
  (a creature that stands, an economy that doesn't inflate, a storm cadence in a band);
  you cannot train *unsettling*, *clever*, or *lost-then-relieved*. NO REFERENCE, NO
  VERDICT — the human supplies what good means; every objective in §4 is a human
  sentence made measurable, and the ones that can't be are the human's to keep.
- **No open-ended evolution shipped live.** Thirty years of ALife stagnation; evolution
  stays a supervised bake in a membrane (`THE_EVOLUTION_ENGINE.md` §6).
- **No claim of beating monoliths at their own game.** A Genie-class model will always
  dream wider; it will not remember a footprint, prove a storm, or carry a debt of
  kindness across a generation. Different game. Ours.

---

## 8. The ladder — every rung independently abandonable

| # | rung | what proves it | KILL IF |
|---|---|---|---|
| 1 | **Three seed domains** — weather cadence, memorial curve, director ecology: `core/trainables/{weather,memorial,director}.py` + objectives, trained in membranes, pins read | three `*.trained.json` winners whose pins name real spec holes | an objective cannot be stated as physics/read-backs without smuggling taste |
| 2 | **Trained data flows top-down** — DSL grows the loci the pins demand; generator emits trained tables into the §10 shells (the elasticity precedent, repeated) | a UBT-green build whose weather/memorial numbers came from a `.trained.json`, not an argument | the DSL⇄generator round-trip costs more than the training saved |
| 3 | **Seam batteries + seam beats** — the five seams of §5 as rep atoms and lintable beats; red seams mint tasks | seam atoms green for the right reason; a deliberately broken seam goes red | seams prove unmeasurable headless (then they wait for PIE lanes, not deletion) |
| 4 | **An agent that imagines** — latent dynamics on brain_gpu rollouts; plan-by-imagination beats the reactive brain on the SAME honest eval | worst-of-N distance/periodicity ≥ the reactive baseline, same membrane discipline | imagination trains but transfers nothing (dreams don't survive contact) |
| 5 | **The learned Director** — sequence model over world_store, judged by the tuned director's own objective, invariants as hard gates | ecology measures in-band across N sleepwalker sessions; invariants never violated | the policy can't beat the tuned tables it replaced |
| 6 | **The composition at scale** — §10's full data surface trained, seams green, the whole experience witnessed holistically | the collapse: automated observation over the composed world | the seams multiply faster than they green (then narrow `coupling_degree_k`, which is what it is for) |

Rungs 1–3 need zero new engine machinery. Rung 4 is the first new model class; 5 the
second; 6 is not a build step but the state the conveyor converges to.

---

## 9. Files

| path | role |
|---|---|
| `CHIMERA_VISION.py` | the seed — the spec the composition realizes; §10 is the shelf |
| `core/trainer.py` + `core/trainables/` + `docs/objectives/` | the per-piece learners |
| `core/rep_engine.py` + `docs/rep_batteries/` | per-piece memory; seam batteries land here |
| `core/curriculum.py` | the per-piece training program (the literal reading) |
| `core/sleepwalker.py` + `docs/beats/` | the witness — and the action-labeled data engine |
| `core/malcolm.py` + `docs/envelope.json` | the composition governor (`coupling_degree_k`) |
| `core/helm.py` | which piece trains next |
| `core/membrane.py` | where every training run lives |
| `docs/TRAINING_PROTOCOL.md` | the method every rung obeys |
| `docs/THE_EVOLUTION_ENGINE.md` | the machine, proven on creatures |
| `docs/THE_MATTER_MODEL.md` | the substrate: even matter is compositional |

> The monolith bets that one model can learn a world. This studio bets that a world is
> too important to be one model — that a footprint should persist because ground is
> real, a storm should cost because weather is real, and a star should be exactly as
> bright as what a life gave up, because the curve that says so was trained against
> that sentence and can prove it. Everything specific. Trained separately. Composed
> where physics keeps the receipts.

---
---

# PART II — THE SUBSTRATE ENGINE

> **The human's second commission, 2026-07-18, assembled from their own words:**
> *"Make matter atoms... and just piece them together. I want to use the same physics
> that the universe uses."* · *"I know it's computationally impossible — but not if we
> give it the proper context through pre-programmed algorithms."* · *"If we can train
> the SHAPES and we can train the MOVEMENTS, what else do we need?"* · *"The magic
> sauce is Gaussian splatting... little shapes that are translucent and angled."* ·
> *"We'd have to program Gaussian in a way that allows dynamic lighting — Substrate in
> Unreal Engine is the technology that would make it possible."* And the closing
> sentence, which is the whole part in one line:
>
> **"It'll be both a physics and a rendering engine that combines physics to make
> rendering possible."**

---

## 10. The problem Part II solves — the AI cannot invent decompositions

Part I's §4 asks the LLM to write a bespoke domain per seed system. That works for the
systems the seed already names — but inventing trainable framings for arbitrary content
is creative decomposition, and it is the LLM's weakest act. The human's fix: **go below
the systems.** On a universal matter substrate, decomposition stops being invented and
becomes mechanical:

- **A world model is exactly two things: state and dynamics.** The human named them —
  **SHAPES** (what matter is arranged as) and **MOVEMENTS** (how arrangements change).
  Train shapes; train movements; compose. There is no third kind of thing.
- **Objectives collapse into a template library.** Shape objectives: *stands, holds
  under load, encloses volume, spans a gap.* Movement objectives: *travels, lifts,
  cycles, throws* — always worst-of-N, always robustness (`TRAINING_PROTOCOL.md` §3.5).
  The AI stops inventing framings and starts filling templates — the thing it is
  actually good at.
- Both trainables are ALREADY PROVEN on this box: shapes (`core/terrarium.py`, 35k
  evals/sec) and movements (`core/trainables/brain_gpu.py`, honest eval), composed
  (`core/rig.py` — the trained brain posing the grown flesh). Part II generalizes the
  proven pair from creatures to *everything*.

Part I's system-level domains (weather, memorial, director) remain valid — they are
cheap data trainables. The **long road** is substrate-level.

---

## 11. The atom — one primitive, two field sets

The Matter Model's brick (`THE_MATTER_MODEL.md` §2) and the rendering primitive unify
into a single particle:

```
ATOM {
  physical   — the brick:  identity, density, stiffness, adhesion[], tear, granularity
  optical    — the slab:   albedo, roughness, F0, subsurface MFP, translucency, anisotropy
  footprint  — the splat:  position + oriented anisotropic covariance
                           (the covariance hands you a surface normal and a spread for free)
}
```

At the research frontier the splat and the simulation particle are already the same
object — continuum physics run directly on Gaussians is an existing line of work (as of
model knowledge; **verify the current state at build time**, the research gate will
demand it). The two ideas are not being combined; they are the same primitive wearing
two field sets.

---

## 12. Two engines, one substrate

Every engine today keeps **two copies of the world**: a low-resolution invisible one
for physics (collision proxies, capsules) and a high-resolution dead one for rendering
(meshes that feel nothing), glued by animation. A whole class of bugs lives in the gap
between the copies. The substrate engine keeps ONE copy: **the render state IS the
physical state.** Nothing is drawn that is not physically there; nothing exists that
cannot be seen.

And the human's sentence runs in BOTH directions, which is why it is an engine and not
an aesthetic:

- **Physics makes rendering affordable.** Coalescence is a physical event (quiet
  uniform matter congeals into a rigid aggregate) and it IS the LOD system. The dune is
  drawable because it is asleep.
- **Rendering makes physics affordable.** Visibility and activity tell the substrate
  where to spend live simulation (the BEHAVE budget). The wound simulates because
  someone is looking at it, cutting into it.

### The rendering division of labor

| layer | carried by | does |
|---|---|---|
| **Geometry** | the Gaussian footprint — oriented anisotropic spread from the covariance | where matter is; how its surface is oriented |
| **Material** | an Unreal **Substrate** slab, parameterized per-particle from the atom's optical fields | what the matter is, optically — the brick's `optical` maps ~1:1 onto slab parameters |
| **Light** | Lumen + the 27-hour sun + the memorial night-light — the engine's own pipeline | dynamic illumination, shadows, GI |

**Splats carry MATTER, not LIGHT.** Captured 3DGS bakes real-world lighting into its
radiance — which is exactly why it cannot be relit, and why relighting is a research
problem *for capture pipelines*. This studio EMITS splats from grown matter whose true
material parameters it already knows — nothing was ever entangled, so nothing needs
disentangling. The hard research problem becomes an engineering problem: render the
particles into the deferred pipeline (oriented particles writing GBuffer attributes,
dithered/stochastic opacity for the soft edges) and let Unreal light the matter.

**The honest trade:** captured splats look real largely because real global
illumination is baked in. Relighting dynamically means realism is EARNED from materials
+ Lumen — which is where this studio's advantage (ground-truth materials per atom)
actually lives. Earned, not free.

**The convergence that matters to THIS studio:** in a physics-rendered world, a
screenshot is a physics measurement. The visual gate and the witness gate converge by
construction — "looks right" and "is right" stop being separate claims, which is the
gap H-14 exists to police.

---

## 13. The scale ladder — pre-programmed laws per scale

*"The same physics the universe uses"* does not mean simulating atoms — the universe
itself is computed with effective theories per scale (nobody derives sand from quarks).
The pre-programmed algorithms the human names ARE these per-scale laws:

- **grain scale** — contact physics where the shovel digs, live particles at the wound;
- **bulk scale** — statics where the dune sleeps: one rigid aggregate, one draw;
- **the switch** — coalesce/fracture (`THE_MATTER_MODEL.md` §6, rung 4 — the one real
  unbuilt machine): quiet uniform regions merge (with hysteresis; merging forgets
  per-cell state, so merge only what individuality you will surrender); a cut fractures
  locally, instantly.

**On abandoning standard landscaping:** less radical than it sounds. The seed's
`AGroundActor` already bypasses UE Landscape — procedural height plus LIVE dig deltas
(`GA_Dig` writes into the ground's own truth). Terrain-as-matter is that same ground
made of atoms: coalesced at rest, fracturing under the shovel, splat-rendered. The
experiment that decides it is rung C below.

---

## 14. What else is needed — the short honest list

The human asked: *"if we can train the shapes and we can train the movements, what else
do we need?"* The studio's own measured findings answer — the list is short:

1. **Joints.** Rung 1.5 proved it physically: adhesion alone cannot hold an axis
   (Rayleigh-Plateau pinching). Shapes need typed connections — tendons, hinges,
   sockets. The part that failed when omitted gets named.
2. **The scale ladder** (§13) — coalesce/fracture is the one real build.
3. **The read-surface.** Law 1 — the world answers the body — means the substrate must
   expose the variables verbs touch: traction, temperature, tear. A physics world
   nothing reads is a screensaver. "Pull only what the game reads" is the whole rule.
4. **Objective templates** — small, reusable, physics-not-taste (§10).
5. **Storage, measured early.** Splats and Nanite make detail free to *draw*, not to
   *store*. This bounds the ambition; measure it, never assume it.
6. **Substrate maturity in UE 5.8** — per-particle slab parameter binding, deferred
   compositing, performance: verify LIVE at build time (model knowledge ends before
   5.8; the research gate on rung D′ enforces this).

Fun stays the human's. That never changes, at any scale.

---

## 15. The experiment ladder — every rung killable

| rung | experiment | inputs that already exist | KILL IF |
|---|---|---|---|
| **A** | **Brick→splat emission**, headless: emit one Gaussian per surface tissue-voxel of the baked limb (optical fields from tissue type), render N views under a MOVING light with a small splat rasterizer, in a membrane | `core/bake.py` voxel tissues; `core/rig.py` | it cannot beat the marching-cubes render of the same limb, or relighting artifacts dominate |
| **B** | **Movement**: skin the splats with rig.py's own LBS weights, replay the trained gait, check temporal coherence | `core/rig.py --mode walk` frames | splats shear/swim/pop under animation |
| **C** | **Terrain-as-matter (the shovel test)**, headless first: a bounded ground patch of atoms, coalesced at rest, a scripted dig fractures it locally, grain physics on the freed particles, splats follow | the seed's `DIG`/`GA_Dig` design; MuJoCo grain sim | fracture seams cannot be stitched, or the grain budget breaks the frame — then landscaping is NOT abandoned and the finding is recorded |
| **D′** | **In-engine**: the limb as per-particle Substrate-shaded splats in the LIVE editor under a moving directional light (the 27h-sun stand-in), MCP viewport screenshot, side-by-side vs its own mesh | rung A's emitter; the MCP bridge | no viable UE 5.8 path (plugin/Niagara/GBuffer) reaches acceptable compositing + perf, or it cannot match the mesh under dynamic light |

A and B are pure Python on artifacts that exist today. C decides the landscaping
question honestly in both directions. D′ is where Unreal's own Substrate earns its
place in the stack — and where the live research happens.

---

> Part I said: everything specific, trained separately, composed where physics keeps
> the receipts. Part II says what everything is MADE of, and who does the seeing:
> one atom carrying its matter and its appearance; shapes and movements as the only
> two things ever trained; physics that congeals into rendering where the world is
> quiet and wakes into simulation where a body touches it. A physics engine and a
> rendering engine that are the same engine — because matter simulated correctly is
> already most of the way to being seen correctly.
