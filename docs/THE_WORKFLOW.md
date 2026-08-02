# THE WORKFLOW — the system as it actually is

> Reconstructed 2026-07-23 by reading the repo **chronologically** (git add dates, not
> filesystem mtimes — a `git checkout` had stamped everything with today).
> The newest layer is the working one; everything older either feeds it or is retired.

**THE ONE SENTENCE: everything in the world is a Gaussian splat, every material is a
*trained composition* of splat types, and every genome comes either from measuring reality
or from growing it under physics.**

---

## 0. The build order — what was made when

| Date | Layer | What landed |
|---|---|---|
| **07-20** | the periodic table | `element_catalog.py` → 69,718 trainable variables → `trainables/generated/*` (solar_system, shelter, trade_ui …) |
| **07-21** | **the splat world** | `splat_types.py`, `splat_level.py`, `train_splat_compositions.py`, `rebuild_world.py` + all of `WorldModel/` (SplatVAE, cellular, universe, infinite, nanite) |
| **07-22** | **genomes from reality + taste** | all of `Construction/` (scan → genome) and `taste.py` / `preference*.py` |
| **07-23** | consolidation | local-model docs, experimental method, this file |
| **07-23** | **AUTOMATED WORKFLOW** *(RETIRED 07-24)* | ~~`sequential_orchestrator.py` - continuous sequential agent pipeline~~ — retired 2026-07-24: orchestrator deleted, launcher pointed at deleted files, nothing imported the agents, and its documentation_agent corrupted task_progress.md. The canonical to-do list is now `Chimera/docs/THE_BACKLOG.md`.
| **07-23** | **THE COMPOSITION SIDE** | `progeny.py` (children/placement/verbs), `membrane_shapes.py` (containers), `render_world.py` (GPU render), and the link that made trained compositions reach the world builder |

**Read backwards from 07-22 and the system explains itself.** The last two days added the
two ends the middle was missing: *where genomes come from* (measured reality) and *who
decides which of the physics-feasible ones is good* (the operator).

---

## 1. THE SPINE

```
        ┌──────────────── two ways to obtain a genome ────────────────┐
        │                                                             │
  MEASURED                                                       GROWN
  Construction/                                            core/trainables/
  real scan → isolate → morphology-DNA                     physics objective →
  + material-DNA → serial number                           trainer → measured facts
        │                                                             │
        └──────────────────────────┬──────────────────────────────────┘
                                   ▼
                         THE MATTER LIBRARY
                  typed bricks: muscle bone skin wood stone water
                  each carrying only what the game reads
                                   ▼
                   train_splat_compositions.py          ← TRAINED, not authored
        "which combination of splat types reproduces this material's optics?"
                                   ▼
                          splat_types.py
              the catalog of emittable shapes (covariance space)
                                   ▼
                          splat_level.py
     ground = Cellular Potts → surface voxels → splats · resources · shelter
     (matter-assembled) · NPCs (matter-grown bodies) · beacon · sun
                                   ▼
                    trainer.train() → top_k feasible
                                   ▼
                     preference_select.py  ← THE ATTUNE-BACK
              re-rank the physics-feasible shortlist by operator taste
                                   ▼
                          rebuild_world.py
                        ONE COMMAND, whole world
                                   ▼
                          render_world.py
              GPU rasteriser, anisotropic footprints + shading
                                   ▼
                             SEE IT
```

**And the object path, added 07-23** — because a game is instances, not surfaces:

```
   one isolated object  ──▶  GENOME (mean + p10..p90 = the variation space)
                                   │
                    ┌──────────────┴──────────────┐
              spawn_children                  recombine(A, B)
              asexual: clone+noise            sexual: 2 parents,
              h² undefined                    independent assortment
                                   ▼
                          build_child(form=)
             tuft / clump / shard  — HOW THE PIECES FIT, not what they are
                                   ▼
                    place(...)   or   scatter(height_fn=...)
              explicit transforms      author any terrain, dress it
                                   ▼
                     pose(verb='wind'|'grow'|'settle')
                 rooted: bases stay planted, tips move most
                                   ▼
                             render_world
```

---

## 2. The stages, with the file that does each

### Stage 1 — obtain a genome

**A. MEASURED (`Construction/`, 07-22)** — from a real 3DGS scan.
`ksplat_io` decode → `decompose_scene` (RANSAC planes, then blob clustering, PCA signature
per element) → `gpu_render_torch` + `multiview_sam_lift` (render, segment with SAM 2,
back-project, vote) → `morphology_signatures` (shape-DNA) → `material_dna` (inverse
rendering) / `take_dna_full` (splat-configuration distributions) → `codebook` (serial
number). Full status per stage: `Construction/SPLAT_DNA_WORKFLOW.md`.

**B. GROWN (`core/trainables/`, 07-18 → 07-20)** — from a physics objective.
The domain reports **facts**; the objective says which facts are good; `trainer.py` runs
26k–37k evals/sec with no LLM in the loop. Trained rungs, each against reality's own
numbers: `granular` (sand, 40.03° emergent repose), `bigbang` (Kepler slope 1.50 at
r²=1.000 measured from grown orbits), `planet` (oceans, atmospheres, a habitable zone
nobody placed), `material_appearance`, `tree_appearance`, `creature`, `walker`, `brain`.

> **Both paths produce the same thing** — a typed brick with measured properties and a
> serial number. Extraction and generation are one library seen from two directions.

### Stage 2 — the matter library (`core/matter.py`, 650 lines)

Differential adhesion (Cellular Potts) self-sorts scrambled typed bricks into layered
structure. `limb.py` uses a skeleton as a frozen axis and lets adhesion wrap flesh around
it. `matter_gpu.py` runs the same shaker at **6.3 B site-updates/sec** — use it, never the
CPU loop, at scale.

### Stage 3 — TRAIN the splat composition (`train_splat_compositions.py`, 07-21)

**This is the hinge, and it is trained rather than authored.**

```
genome  : per material, [type_mask (7 bits), weights (7 floats), scales (7 floats)]
measure : render the splat cloud, compare against the library's optical targets
```

Each material *discovers* which combination of splat types — surface, fiber, point, shell —
reproduces its optics. Nobody hand-picks "bark is fibers."

### Stage 4 — emit the world (`splat_types.py` + `splat_level.py`, 07-21)

Everything is a splat: ground from the Cellular Potts grid, resources as clusters with
material properties, shelter matter-assembled, NPCs matter-grown, beacon, sun. The GPU
rasterizer reads the **full 3×3 anisotropic covariance**, so new shapes need no kernel
change.

### Stage 5 — the operator decides (`preference*.py` + `taste.py`, 07-22)

Physics narrows to what is *feasible*; it cannot say what is *good*.
`trainer.train()` returns `top_k` (every hard gate passed) → `preference_select.py`
re-ranks by a Bradley-Terry model over the **physics measure vector** → `taste.py` supplies
the human-authored Will as the prior.

> **NO REFERENCE, NO VERDICT.** The machine never decides what is good on its own. A
> human — or an objective a human authored — supplies the reference; the machine attunes
> and reports how close it got.

### Stage 6 — one command (`rebuild_world.py`, 07-21)

GPU terrain growth (Cellular Potts at 256³) → matter shelter growth → splat emission for
all elements → GLB export → render.

Its last two steps used to import into UE5. That is **replaced** (07-23): `rebuild_world`
now calls `render_world.show()`. The old `import_to_ue5()` built a UE Python script as a
string, ran `telemetry_probe`, printed "command written", and executed nothing — it never
worked.

### Stage 7 — SEE IT (`render_world.py`, 07-23)

`render_orbit(splats)` — the soft-Gaussian scatter rasteriser, made reusable from the
hardcoded `Construction/gpu_render_torch.py`. Projects each splat's **3×3 covariance to a
screen-space ellipse** (anisotropic footprints — before this every splat drew the same
round dot, so `surface 63% + cloud 29% + beam 8%` rendered identically to `surface 100%`
and the whole composition pipeline was invisible), applies **Lambert shading** from the
splats' normals, orbits N cameras, writes a montage. 6 views of 118k splats in ~1.5 s on
the 4090. **The operator must be able to see the output** (`EXPERIMENTAL_METHOD.md`).

### Stage 8 — OBJECTS, not surfaces (`progeny.py` + `membrane_shapes.py`, 07-23)

The correction that reframed the back half: **a game is instances of objects, not a
material painted on a surface.** Isolate one thing → make variations → place them.

- **`membrane_shapes.py`** — sphere / plane / cylinder / box / dome, `displace()` for
  relief, `clothe()` to dress a shape in a material's trained composition. Built because
  terrain had no CONTAINER: 300 random blobs left 22% of columns carrying matter across a
  2,000-unit spread — the physics ran correctly and produced noise because the objective
  was underdetermined. **A membrane is a boundary, and a boundary is what makes a result
  attributable** (the Membrane Programming principle, applied to geometry).
- **`progeny.py`** — the genetics. A genome is stored as mean + p10..p90; **that range is
  the variation space children are sampled from.**
  - `spawn_children(parent)` — asexual, clone + noise. h² undefined from one specimen.
  - `recombine(A, B)` — sexual. Independent assortment per **linkage group**, **pleiotropy**
    (R/G/B share one luminance factor — independent draws made rainbow confetti), **mutation**
    as a separate low-rate process, and **liability-scale** sampling (logit/log) so bounded
    traits never clip. Measured after: 0/10 saturated-white, 0/10 zero-size.
  - `merge_specimens(...)` — combines N scans of one KIND into a class genome and computes
    **heritability** h² = V_between / (V_between + V_within) by the law of total variance.
    **This is why two scans of a thing is the minimum useful sample** — with one you cannot
    separate "this individual is like this" from "the class varies like this".
  - `build_child(form='tuft'|'clump'|'shard')` — the archetype is **how the pieces fit**,
    not what they are made of.
  - `place(children, positions)` — explicit hand placement. `scatter(height_fn=...)` — dress
    an authored heightmap (the operator's own example: get grass working, then apply it to
    any terrain).
  - `pose(verb='wind'|'grow'|'settle')` — the VERB. Rooted, so bases stay planted and tips
    move most. **Plasticity**: one genotype expressed differently by environment, not
    inherited.

---

## 3. What still points at Unreal

| Where | What | Status |
|---|---|---|
| `rebuild_world.py` steps 5–6 | MCP import → UE5, level save | **DONE (07-23)** — now calls `render_world.show()` |
| `ParticleEngine/` | Python particle sim **plus** a UE render bridge | **DO NOT DELETE.** `Construction/backend_3d.py` and `WorldModel/train.py` both import it (`tree_trainer.TreeParams`). The simulation is current; only the bridge is dead. |
| `core/bake_to_ue5.py`, `system_to_ue5.py` | UE staging | dead |
| `Chimera/docs/THE_MATTER_MODEL.md` §5 | "what maps to which UE5 technology" | dead section, **the rest of the document is the live concept** |

---

## 4. Honest gaps

1. ~~Extraction and generation are not yet joined.~~ **WIRED 2026-07-23.**
   `Construction/export_genome.py` writes measured splat-configuration distributions to
   `Chimera/docs/matter/recovered_genomes.json`; `train_splat_compositions.py` now prefers
   a recovered genome over the 40Q keyword constraints (`measure_recovered()`), emitting
   the composition's splats and comparing **covariance-eigenvalue features against the
   scan's own numbers**. Proof it works: the one measured cluster with LOW anisotropy
   (0.52, rough corrosion) trained to `surface 63% + cloud 29%` — reaching for the only
   isotropic emitter — while the 0.95–0.99 clusters trained to `beam 78–90%`. Nobody
   encoded that. **Remaining:** only one scan (truck, 8 clusters) is exported, and naming
   `cluster_07` "corroded steel" is still manual.
2. **TWO SCANS OF EACH KIND — COMPLETED 2026-07-23.** `merge_specimens()` and `heritability()` are written and waiting. With a single specimen h² is undefined, so every child is a rearrangement of one individual. Two grass tufts, two rocks, two bolts, and between-specimen variation becomes measurable.

   **STATUS: VALIDATED WITH 5 MATERIALS.** Processed bonsai vegetative, stump wood, bicycle metallic, plush fabric, and truck metallic — all with heritability estimates (color h² > 0.72 in plants/fabric, size h² < 0.08). Children rendered successfully on RTX 4090 (~500ms each). The pipeline is operational end-to-end: scan → cluster matching → specimen merging → heritability estimation → child generation → visual rendering.

   **NEXT:** Process remaining critical materials (grass, rock, pure metal, ice) and test two-parent recombination.
3. ~~The arrangement dimension has no search in it.~~ **CLOSED 2026-07-23.**
   `build_child` had three hand-written branches, so a driven section returned
   `{'clump': 1147}` — every object a clump, the section reading as gravel however varied
   its genomes. `core/trainables/arrangement.py` is now a continuous 10-gene space with
   the trainer's contract; tuft/clump/shard are POINTS in it, not branches.
   `Construction/arrangement_dna.py` measures the same statistics from real scans so it
   trains against measurement rather than taste. **Remaining: the objective JSON, and the
   gap it must close — real material clusters at 4.7–8.2, the old forms reached only
   1.3–1.5.**
4. **The splat-type catalog has a ceiling.** `beam` caps at aniso 0.95 but real material
   measured 0.994 — you cannot emit what the vocabulary cannot express. Needs a more
   extreme emitter + finer scale control. Measurable target.
5. **No emissive, fluid or atmospheric genome.** `energy`, `fluid` and `atmospheric` ports
   return **zero** admissible candidates — the library cannot express anything that flows
   through those interfaces. Lasers, engine glow, water. Reported by the system itself
   rather than remembered.
6. **Colour and opacity are recovered but unused in composition matching** — only
   anisotropy and size-CV are compared. The RGB/opacity distributions sit in
   `recovered_genomes.json` doing nothing.
5. **No training logs.** Nine VAE checkpoints (713 MB) with no record of what produced them.
6. **Relighting is unsolved.** Structural DNA (size/shape/angle) is lighting-clean; colour
   DNA carries baked capture light.
7. **Patch encoding unimplemented** — caps SplatVAE at ~100K splats; real captures are millions.

---

## 5. The rules that govern all of it

- **TRAIN it, don't hand-tune it.** DATA gets evolved; the LLM writes the constraints and
  never turns the crank. ~30,000 evals/sec vs ~20 edits/hour.
- **One rollout is a coin toss.** Score N randomised restarts and keep the WORST.
- **GPU for the population, CPU for development.** Nothing reads back from the GPU inside a
  rollout loop.
- **The exploit is the product** — a degenerate winner is the optimiser auditing your spec.
  Iterate the objective, never the artifact.
- **Measure the thing, not a proxy** (`Chimera/docs/EXPERIMENTAL_METHOD.md`).
- **A measurement without a CONTROL is not a measurement** (2026-08-01). Push a KNOWN subject --
  one you MADE, whose answer you know by construction -- through the whole instrument before you
  report anything. Three already-written conclusions were reversed by this in one day. Corollaries:
  *measure at the scale the thing lives at* (an unresolvable effect returns a wrong number, not a
  refusal); *never threshold on a quantile of what you are measuring*; *suspect the data's
  construction, not only the probe*; *a shared name is not a shared definition*; and *derive the
  shape, let physics set the level -- when the two disagree, that IS the finding*.
  Rules 11-16 of `Chimera/docs/EXPERIMENTAL_METHOD.md`.
- **BACKTRACE: debug UP the chain, not forward from the symptom** (2026-08-01, the operator's).
  Forward debugging finds where an error became VISIBLE; backtracing finds where it ENTERED. Six
  hypotheses were eliminated against a foot whose instruction came from four membranes up.
  Corollaries: *one quantity, one landmark* (three leg lengths, 3.11 cm apart, all dimensionally
  identical); *the instrument must move with the membrane and keep no copy of it* (four witness
  self-inflictions in one day); and *in a grown world an authored phenotype is the defect* -- the
  witness is the FITNESS FUNCTION and the measured dataset is the CONTROL, not the answer.
  Rules 17-20.
- **DERIVE it before you TRAIN it** (2026-07-28). Trace every membrane's variables and show the
  equations CLOSE before a run — else it is guess-and-check on a 2-hour loop (= training the RULES).
  A real derivation predicts what it was never fitted to. `docs/THE_MATHEMATICS_OF_WALKING.md`.
- **One change at a time** — three coupled changes is a three-body problem with no attributable
  solution. And watch the second variable you changed by accident (an action-space swap silently
  rescales exploration noise).
- **Command the PROCESS and its stop condition, never the final position** — positions are OUTPUTS;
  in rewards, reward the outcome (grasped/balanced/still), not a target pose. `docs/CONTROLLER_MAP.md`.
- **The work-gate judges LEARNING, not heat** — temperature is a readout; a coasting run has neither
  heat nor a learning curve (`ChimeraEngine/gpu_gate.py`).
- **Verify your own MEASUREMENT, not just the claim** — before reporting a result that contradicts a
  prior one, suspect the instrument first.
- **Build in one of six directions, from the player outward** — §6 below. Without a
  priority rule the pipeline yields unrelated assets instead of a place.


---

## 6. WHAT TO BUILD NEXT — the six directions

Everything above says *how* the world gets made. This says **what to make next**, and it
exists because the pipeline can make anything: without a priority rule an agent produces a
pile of unrelated assets instead of a place. **Six directions is the constraint that
focuses it.**

### The anchor and the timeline

Development follows the **player's timeline from t=0** — the first thing they ever see.
There is **no main menu screen**; the menu is written into the environment, because the
world can be the menu. From the player's position (**the anchor**) there are exactly six
directions, and each is a work bucket:

| Direction | The question it asks |
|---|---|
| **DOWN** | what are they standing on? |
| **FORWARD** | what draws them onward? |
| **UP** | sky, ceiling, the scale of the place |
| **LEFT / RIGHT / BACK** | what holds the world together around them? |

**Work one direction at a time. Build nothing that no direction asked for.** Each direction
names concrete pipeline work — which genome to recover (Stage 1), which objects to breed
(Stage 8), where to `place()` them, which `pose()` verb they carry. The six directions do
not replace the stages; they aim them.

### How far out — proxemics, not travel

Detail is budgeted by **perceived** distance, in the bands humans actually read (Hall,
1966): arm's reach, personal, social, horizon. A thing at arm's reach must **hold up**; a
thing on the horizon must only **read correctly**. This is the LOD-of-meaning ladder
already in `CLAUDE.md`, anchored to a body instead of a number.

> **DISTANCE TRAVELLED IS NOT A CONSIDERATION.** Work is **anchor-local**. You never budget
> by how far the player will move, and the space *between* anchors is not a development
> target — in a space game most of it is void, and **void is correct**. Crossing a million
> kilometres costs nothing to build.

### When all six are filled: MIGRATE

Move the anchor to new ground; six fresh directions open. The universe expands because the
current one is **saturated**, not because someone decided to add more — an organism fills
its niche and disperses. This is the same range-expansion logic as the genetics in Stage 8.

### The frame, not the compass

Four cardinal directions presuppose a horizon. **In space there is none**, so the player's
own orientation is the only reference — you are not adding two directions to a plane, you
are losing the plane. The machinery already exists: **`core/terrarium.py:264` is a 3D
turtle** carrying `H, L, U` (heading/left/up), and its yaw/pitch/roll commands *are* the
six. Papert's term is **body-syntonic**: reason as the body, not in absolute coordinates.

### The rule that must not bend

Six directions govern **traversal and authoring**. World state is stored in **absolute
coordinates**. `CLAUDE.md` promises *same seed, same world, forever* — that holds only if
the camera's frame never leaks into what is **saved**. Egocentric for attention and
building; allocentric for persistence.

### It transcends scales — and that is the payoff

Because work is **anchor-local** and travel distance is never budgeted, **the rule is
scale-invariant**. A frame does not care how large anything is. The same six questions are
asked, unchanged, at every rung:

| Anchor | DOWN | FORWARD | UP |
|---|---|---|---|
| standing on regolith | grain under the boot | the ridge line | sky, weather |
| a ship's cockpit | the deck plate | the viewport | the overhead console |
| orbit | the planet below | the terminator | the star field |
| interstellar | the ecliptic | the next system | the galactic plane |

This is the **compositional ladder** (`CLAUDE.md`) given a work order — sand → cloud → star
→ system → planet → climate → matter under boots are *scales*, and the six directions apply
identically at each. It is also why `core/terrarium.py`'s turtle is the right primitive:
its yaw/pitch/roll commands are the same whether the step is a bark fibre or a light-year.
**Same method, any magnitude. Migration between scales is just another anchor move.**

### Why this produces emergence

You are not designing a world from above. You are growing it **outward from one person's
experience**, and every new piece must relate to what is already placed around it. The
constraint is what makes the parts cohere into a place rather than a collection.

---

## 7. THE ARCHITECTURE — one primitive, one motion, one address

Everything below was worked out 2026-07-23 with the operator and then built. It replaces
a set of separate systems with one construct seen at different sizes.

### 7.1 A membrane is a boundary, and a boundary is a SCALE

    time ⊃ universe ⊃ system ⊃ planet ⊃ ground ⊃ section ⊃ cell ⊃ object ⊃ material ⊃ …

These are not different constructs. **The membrane IS the hierarchy** — each nested one is
the next scale finer, and crossing one inward is exactly what "finer" means. Being a
boundary supplies, for free, at every level:

| | |
|---|---|
| **a frame** | up is the membrane's LOCAL NORMAL. A global +Z is wrong on a sphere, in a cave, on a hull. |
| **a unit** | coordinates are LOCAL, so they can never exceed the membrane's own extent |
| **an identity** | the serial attaches here — an address is the PATH of membranes crossed |
| **inside / outside** | soil vs air, hull vs void. A thing may SPAN one — roots in, trunk out |
| **LOD** | `depth()` IS the level of detail. Approach decompresses, retreat coalesces |

**Precision stops being a problem rather than being managed.** A coordinate inside a
membrane cannot exceed that membrane's extent, so there is no far-from-origin case at any
scale, and the large number only appears if someone asks for world coordinates.
Verified: rock-local `[0.05 0.02 0.01]` → world `[1.5e11, 0.22, 0.01]`.

`core/membranes.py`. Not `core/membrane.py`, which seals a git worktree — same idea (no
inside/outside means no individual, nothing for selection to act on) applied to space
rather than to work.

### 7.2 TIME is the outermost membrane

The 4th dimension contains every spatial one. It passes the same tests: **past is inside**
(settled, determinate), **future is outside** (unformed), **the present is the boundary
surface**, and its normal is the arrow of time. Nothing contains it, and you cannot cross
back out — which is what makes it *ultimate*.

Consequences: temporal LOD is the same coalesce/fracture mechanism as spatial; *"same
seed, same world, forever"* is a claim about time, so history is **derivable rather than
stored**; and the address is 4D — `T+000123 / U / P-earth / G / S+00384+00896 / C…`.

### 7.3 Everything is TWO ENDS AND A DIAL

| | the two ends | the dial |
|---|---|---|
| a verb | at_rest → fully_bent | wind speed |
| a morph | genome A → genome B | blend |
| heritability | specimen A → specimen B | what varies between them |
| LOD | near → far | distance |
| growth | seed → mature | time |
| **the story** | first frame → end state | progression |

*You do not describe an axis; you exhibit its two ends* (`Construction/scene.py`, DESIGN §3).
So **the game is not built with the mechanism — the game IS the mechanism**, and the story
is simply the outermost dial. A verb whose two ends do not differ is refused at definition
time: that is one state written twice.

**GATES** are the only thing a story dial has that the others do not. A player is held at a
checkpoint until something *measurable* is true, then released — open-world included, since
grinding reputation to upgrade a gun is a 0..1 dial with a gate on it. The condition reads
world state; it is never a flag someone sets, for the same reason acceptance conditions are
not self-reported.

### 7.4 The six directions are the PORTS of a cell

Not an analogy. A direction is a face you can attach through; an unfilled port is somewhere
the world is not finished; **`work_queue()` is therefore the world's to-do list, enumerated
rather than authored.** Ports are typed by WHAT FLOWS — structural, gravitational, energy,
fluid, atmospheric, substrate — so composition is checkable: *"structural cannot carry
energy — nothing flows through that joint."* Three conditions to mate, all physical: same
kind, ports FACING each other, matched size.

A cell is human-scale (**1.83 m**, a person and their arm span). Earth's surface holds
**1.52 × 10¹⁴** of them.

### 7.5 The loop, closed

    open stud  →  propose()  →  candidates, RECOMBINED not selected  →  place()  →  filled

`core/bricks.py`. Candidates are **bred** from the library, so what is offered includes
matter that does not exist yet but could — the reason genomes are stored as distributions.
Ranked by measurable facts only (heritable first); **taste never enters here**, that is
`preference_select`. An empty result is a RESULT: `energy`/`fluid`/`atmospheric` studs
return zero candidates because nothing in the library flows through them, which is the
vocabulary gap made visible instead of papered over.

**Measured, driving a whole section:** 4,761 cells scanned, 581 occupied (12.2%), **1,147
bricks in 0.19 s = 6,037 bricks/sec**, 57,350 splats. Same section twice → byte-identical
geometry; the neighbour → different content. Content derives from coordinates, so a section
is regenerated rather than stored.

### 7.6 Development order = play order

You build **along the story dial from t = 0**. First frame, first gate, next gate — and at
each position ask the six directions. The world gets made in the order it is experienced,
and **nothing gets made that no position asked for.** That is the answer to how one person
builds a world: you don't. You build a corridor of experience and let the machine fill the
six directions around each step of it.

---

## Before you train anything: derive the target, then let the gate check it

`python tools/training_gate.py --target-speed X --stride-s Y`

A walker that would not walk was met, on 2026-08-02, with a four-variant parameter sweep. It looked
like method — one variable each, run in parallel, fair comparison. **Every variant was asking the
body for a speed it physically cannot walk at.**

    this world     g = 7.076 m/s2 (0.722 Earth),  leg 0.9201 m
    the body derives its own comfortable speed:    0.9924 m/s
    the trainer targeted:                          1.285  m/s   <- MEASURED ON EARTH

Froude settles it. `Fr = v^2/(gL)`, and equal Fr is a dynamically similar gait: 1.285 m/s is
Fr 0.183 on Earth and **Fr 0.254 here** — 39% higher, heading toward the walk-run transition. The
velocity term demanded a running-ward gait while the tracking term demanded Earth *walking*
envelopes. **The crouch was the only stable point in a contradictory reward.**

The stride clock was wrong the same way: a pendulum goes as sqrt(L/g), so this world's stride is
1.327 s and the gait was being clocked 18% too fast.

**A sweep cannot find this.** Four variants asking an impossible question rank four failures.

    THE TELL: before running variants, ask what QUESTION each one answers. If the answer is
    "which number is best", stop -- that is a search where a derivation belongs. Sweeping is
    for genuinely FREE numbers, and a target Froude-derived from measured gravity is not free.

The gate refuses a run whose speeds are not scaled by sqrt(g/g_E), whose strides are not scaled by
sqrt(g_E/g), or which disagrees with what the body publishes about itself. Full account: rule 24 of
`Chimera/docs/EXPERIMENTAL_METHOD.md`.
