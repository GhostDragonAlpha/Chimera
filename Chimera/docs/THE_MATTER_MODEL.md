# The Matter Model — a world built from living bricks

<!-- CHIMERA-LAW -->
> **RULE 1 — DERIVE IT BEFORE YOU TRAIN IT.** A parameter sweep is an admission the derivation was
> not done. Before any run, any sweep, any "let's try N variants": trace the variables and show the
> equations close. If you are choosing a number, you broke the chain and substituted taste for a
> law. Ask what QUESTION each variant answers — if the answer is "which number is best", STOP.
> **[docs/THE_LAW.md](../../docs/THE_LAW.md)** · full method: `Chimera/docs/EXPERIMENTAL_METHOD.md`
> · enforced by `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

> **STATUS: grown anatomy RENDERS IN UE5 and MOVES BY ITS BRAIN (rungs 0–2 + headless spine);
> the in-editor animation onward is design.** Born from a design conversation on 2026-07-14.
> `core/matter.py` shows differential adhesion self-assembling a bone/muscle/skin limb (2D
> `--mode cross2d`, 3D `--mode limb3d` with a typed tendon), each against a failing control. That
> 3D run found, honestly, that adhesion alone cannot hold an axis, so **`core/limb.py` fuses the
> evolution engine's L-system skeleton with the adhesion** — a frozen bone axis wrapped in
> self-organized flesh. Then **`core/bake.py` + `core/bake_to_ue5.py` bake it to a Nanite mesh in
> the LIVE editor** (grown flesh, rendered and shadowed). A system audit then closed the biggest
> gap: **`core/rig.py` makes the skeleton the shared spine** — the REAL evolved body is fleshed,
> skinned to its bones, and posed by the TRAINED BRAIN's own gait (headless), so the creature
> that learned to walk is the creature you see move (§10, rung 3). Remaining: the UE5
> skeletal-mesh + animation export, coalesce/fracture, a world. The measured/witnessed results
> are rungs 0–2 plus the headless spine; that line between built and planned is kept sharp.
>
> This is the substrate *beneath* `THE_EVOLUTION_ENGINE.md`. The evolution engine grows a
> phenotype from a genome; this is the phenotype's *material* — what everything is made OF.

---

## 0. The one sentence

**A universal library of typed "bricks" — muscle, bone, skin, wood, stone, water — each carrying
only the properties the game actually reads, assembled bottom-up into everything in the world,
and baked into what Unreal Engine 5 already renders fast.**

The human's metaphor, verbatim: *"we're building a LEGO set that equals everything in the world,
and then we give those LEGOs to the AI and the AI starts playing with LEGOs and it puts together
a human with muscles… we basically have to pick the things that are important for the video game
and then pull variables."*

That last clause is the whole discipline. You do not model the nervous system if the game does
not read it. You model muscle because movement, mass, strength, and wounds are read. **The brick
carries the variables the game pulls, and nothing else.**

---

## 1. The pipeline, in one picture

```
  GENERATE (offline — the assembler)      BAKE (ship native UE5)        RUNTIME (adaptive detail)
  ──────────────────────────────────      ──────────────────────        ─────────────────────────
  genome (DSL / L-system)                  dense Nanite mesh ── LOOK      COALESCE: quiet,
    │  written in the                        + coarse rig    ── MOVE        homogeneous clusters
    ▼  UNIVERSAL ALPHABET                     + Chaos Flesh   ── DEFORM      → ONE static item
  bricks: muscle · bone · skin ·              + Mass agents  ── BEHAVE           │
  wood · stone · water · …                          │                      FRACTURE: cut / active
    │  fit together by                              │                        regions → live cells
    ▼  differential adhesion                        ▼                        (local, on demand)
  an assembled body / tree / rock          what SHIPS is native UE5              │
                                                                           behavior wakes only there
```

Three moves, and each maps to tech that already ships: **generate** in bricks (our evolution
engine, given a universal alphabet) → **bake** to UE5-native assets → let runtime detail
**coalesce and fracture** so you pay for structure only where it matters.

---

## 2. The brick

A brick is a small **typed struct**. Not a simulated cell with chemistry — a parts-bin entry
that carries exactly the fields the game reads:

```
Brick {
  identity        muscle | bone | skin | fat | chitin | bark | stone | water | …
  physical        density, stiffness, strength, tear_threshold, deforms?    (what force does to it)
  optical         base_color, subsurface, translucency, roughness           (how it MEETS LIGHT → shadows)
  interface       adheres_to[…], connects_via (tendon, membrane, matrix)    (what it snaps to)
  behavior?       contract | flow | grow | none                             (only if the game reads it)
  granularity     cell | chunk | region                                     (how finely it must resolve)
}
```

Two fields are load-bearing and easy to miss:

- **`optical`** is why "shadows and everything" fall out for free. A brick declares how it meets
  light; the bake turns that into a standard UE5 material, and the renderer shadows it like any
  other surface. Skin gets subsurface scattering, a leaf gets translucency, bone is opaque —
  and none of it is special-cased.
- **`granularity`** is the human's *"pull the variables that matter"* applied to **spatial
  resolution**, not just which fields exist. Flesh resolves to `cell` because it deforms, tears,
  and bleeds; stone resolves to `region` because its insides never surface in play. The same wall
  is fine-grained for a muscle and coarse for a rock — and §6 makes that choice *emergent*, not
  authored.

**The library is the work.** The machine that assembles bricks mostly exists (§8). Defining the
brick types well — the right fields, honest interfaces, sane defaults — is the real, slow effort,
and it is why this starts with three bricks, not three hundred (§10).

---

## 3. How bricks fit together "the same way the real world does"

This is the human's core requirement, and it is not hand-waving — it has a real mechanism.

- **Differential adhesion.** Real tissue self-organizes because cells sort by how strongly they
  stick to one another, the way oil and water separate. Give each brick an adhesion profile and
  skin ends up *outside* and bone *inside* **without anyone placing them.** It is a few lines on
  the GPU (a cellular-Potts / differential-adhesion rule), and it is the mechanism that makes a
  pile of bricks *snap into correct anatomy* instead of needing hand-assembly.
- **Typed interfaces.** Where two tissues meet, they meet through a standardized connector —
  muscle to bone through tendon, organ to organ through membrane, everything through the
  extracellular matrix. In engineering terms these are **typed sockets**: a brick exposes the
  connectors it accepts, and assembly only joins compatible ones. That typing is what makes the
  world *composable* rather than bespoke — the same capillary meets the same cell wall everywhere.
- **The genome is the assembly program.** The L-system / DSL we already run *is* the recipe that
  says which bricks, in what arrangement. Today its alphabet is one symbol: bone. The Matter Model
  is that same alphabet made **universal**. **THE DSL IS THE GENOME; the bricks are the letters.**

---

## 4. Generate, then bake — and the THREE budgets

The move that makes a cellular world affordable in UE5: **the bricks are the GENERATOR, not the
runtime.** The AI assembles a creature/tree/rock out of bricks *offline* — exactly the way the
terrarium grows a body — then **bakes** it to native UE5. What ships is not a cell simulation; it
is a mesh, a material, a rig.

And "the cells are alive" is really **three different budgets**, which must never be conflated
(conflating them is where cellular-world projects die):

| budget | question | UE5 tech | how much runs |
|---|---|---|---|
| **LOOK** | how do the cells appear? | **Nanite** (virtualized geometry) | full cellular density, *everywhere* — cheap to draw |
| **MOVE** | how does the flesh deform? | **Chaos Flesh** / a skeletal cage | a coarse rig of ~hundreds of points; the dense skin follows it |
| **BEHAVE** | do cells divide, heal, tear, signal? | **Mass** / **Niagara** agents | only *locally*, on demand — where the player wounds or zooms |

Nanite is the piece that lets the *look* stay cell-dense at runtime instead of being flattened
away — it renders effectively unlimited triangles by streaming and auto-LOD. But **Nanite renders
geometry; it does not simulate it.** It solves "show me a billion triangles," not "make a billion
cells behave." So keep the LOOK dense (Nanite), the MOTION coarse (a rig the dense skin rides —
the standard film/AAA pattern of a heavy render mesh on a light sim cage), and pay for true cell
BEHAVIOR only where someone is looking.

**The real constraint is storage, not render.** Nanite makes detail free to *draw*, not free to
*store* — the geometry still has to exist and stream from disk. "Every cell in the world" is a
disk/streaming budget, which is the other reason granularity-follows-relevance (§2, §6) matters.

---

## 5. What maps to which UE5 technology (the "acceptable for UE5" proof)

Every part of this has a real, shipping home. Nothing here is invented engine tech.

| Matter-Model concept | UE5 system | role |
|---|---|---|
| brick appearance, cell-dense look | **Nanite** | render unlimited geometry cheaply |
| a merged static aggregate (§6) | **HLOD** / merged static mesh | the cheapest thing UE5 can draw |
| flesh that deforms, squishes | **Chaos Flesh** | coarse soft-body simulation cage |
| cutting, cracking, wounding (§6) | **Chaos Geometry Collections** | fracture a static item back into pieces |
| many live cells at an active site | **Mass Entity** / **Niagara** | thousands of local agents, on demand |
| growing a mesh from an assembly | **Geometry Script** | runtime procedural mesh (already our plan) |
| assembling organs into a body, creatures into a biome | **PCG** | rule-based compositional placement |
| streaming the world by region | **World Partition** | only nearby detail is resident |
| brick optical properties → shadows | **standard materials** | subsurface, translucency, opacity — all native |

---

## 6. Adaptive granularity — COALESCE and FRACTURE

The human's key contribution, and the thing that makes the universal ambition tractable: **cells
generate individually, but where many identical, quiet ones are packed together, they collapse
into ONE static item.**

This is, from first principles, a **sparse octree** — a homogeneous region becomes a single node
— and it runs **both directions**:

- **COALESCE.** A cluster of identical, quiet bricks (the interior of a bone, the bulk of a
  muscle, the core of a rock) merges into one static Nanite item. Cheap, and it produces exactly
  UE5's favorite asset.
- **FRACTURE.** When the player cuts the muscle or cracks the rock, that static item breaks *back*
  into bricks locally — right at the wound — so the cut reveals structure. This is Chaos Geometry
  Collections doing what it already does.

Two things make this more than an optimization:

- **Granularity becomes EMERGENT, not authored.** Nobody labels "rock = coarse." The rock is one
  static item *because* it is a big uniform cluster that coalesced; the muscle stays cellular
  *because* it is striated and working. The `granularity` field of §2 is decided by how clustered
  and how uniform a region is, and by whether anything is happening there.
- **It mirrors where biology puts its own complexity.** The interior bulk of a uniform tissue is
  metabolically quiet and structurally redundant; the action is all at surfaces and interfaces
  (skin, membranes, wound edges, growth plates). Collapsing the quiet interior to a static
  aggregate does not fight biology — it copies it.

**The honest hard parts of the merge/split rule:**

- **The trigger needs hysteresis.** You cannot merge-and-split every frame at a boundary or it
  thrashes. The craft is "coalesce when a region has been quiet a while; fracture *instantly* on
  impact."
- **Merging forgets per-cell state.** Once a cluster is one static item, individual brick state is
  gone (or compressed to a summary). Only merge bricks whose individuality you are willing to
  lose — fine for identical bulk, dangerous for anything carrying unique state.
- **The seam** between a merged region and its live-cell neighbors must be stitched so it does not
  crack visually. Standard voxel-LOD problem; solvable; real work.

---

## 7. Why this is the same idea as the Evolution Engine

Nothing here is a new machine. It is the parts bin for the machine we built.

- The **evolution engine** grows a phenotype from a genome and selects it against an objective.
  The Matter Model is what the phenotype is *made of*.
- The **terrarium** is already the assembler that plays with bricks — it just has one brick type
  today (bone). Give it the universal alphabet and it assembles muscle-on-bone-under-skin.
- **Generate-then-bake** is genotype→phenotype, the exact pattern we already run: bricks are the
  genotype, baked UE5 assets are the phenotype.
- **"Pull the variables that matter"** is the domain/objective discipline from
  `TRAINING_PROTOCOL.md`: report only the facts the game reads, encode physics not taste.
- Risky generation runs in a **membrane**, the same as any training job.

---

## 8. The honest limits

- **This is a generation substrate, not a live cellular simulation.** The world is *built* from
  cells and baked; it is not trillions of cells simulated as you play. If someone pictures literal
  live cells everywhere, that is a different (and infeasible) project.
- **The library is the slow part.** The pipeline is mostly built; defining brick types,
  interfaces, and adhesion profiles well is the real work, and it cannot be rushed.
- **Storage bounds the ambition**, not render cost — cell-dense geometry across a whole world is a
  disk budget. Author dense where it pays; stay coarse where it does not.
- **The GAME is a separate design.** The human chose *immersive substrate*: this makes the world
  real; it is not the core loop. What the player does, wins, and loses is unwritten — and the good
  news is the substrate is reusable no matter what that game becomes.
- **Emergence must be governed.** Differential adhesion left fully open produces mush; too much
  hand-authoring stops it "fitting together like reality." The line between them is the design,
  and it is found by building, not by arguing.

---

## 9. The first brick — the thinnest slice that proves the whole chain

Do not build the library. Build the **pipeline**, with the smallest set that exercises every
stage, and only then grow the library.

**Three bricks — muscle, bone, skin — assembled into a limb that:**

1. **moves** — the muscle brick contracts and articulates the bone brick (LOOK + MOVE budgets);
2. **wounds** — the skin brick tears and the muscle beneath is revealed (FRACTURE + local BEHAVE);
3. **bakes** — the assembly becomes a dense Nanite mesh on a coarse Chaos Flesh rig that UE5
   renders, shadows, and deforms.

If that end-to-end chain works — generate → adhere → bake → move → wound → coalesce/fracture —
then the LEGO set only ever *grows*, and every new brick is additive. Living tissue is first
because the payoff is highest (movement, wounds, growth, evolution) and because our assembler
already lives there.

---

## 10. The ladder — every rung independently abandonable

| # | rung | status | KILL IF |
|---|---|---|---|
| 0 | **The brick struct.** One typed primitive; three instances (muscle/bone/skin). | ✅ **DONE** (`core/matter.py`). Modelled only the field the proof reads — the adhesion profile; the rest of the struct lands as the pipeline needs it. | you cannot name the game-relevant fields without inventing chemistry |
| 1 | **Adhesion assembles a limb.** Differential adhesion → muscle-on-bone-under-skin, unattended. | ✅ **DONE 2026-07-14** (`python -m core.matter`). From a *scrambled* pepper of bricks, a Cellular Potts / differential-adhesion model sorted bone to the core (radius 10.5, 0% medium exposure), skin to the shell (27.2, 39%), muscle between — radial spread +12–15 across 4 seeds. The **uniform-adhesion control did NOT sort** (spread ≈ 0), so the sort is the adhesion, not the machine. **Scope: this is a 2D cross-section proving radial LAYERING — the load-bearing half of "fits together like reality." Elongated limb shape, muscle→bone attachment via tendon (typed interfaces), and the 3D lattice are still ahead (rung 1.5).** | it needs hand-placement to look right — then it is not "fitting together like reality" |
| 1.5 | **Shape, attachment, 3D.** Elongate into a limb; add a typed tendon connector; lift the lattice to 3D. | ✅ **DONE 2026-07-14** (`python -m core.matter --mode limb3d`). The same rule on a 3D lattice grew concentric TUBES (bone core r=5.1, muscle 8.5, skin shell 11.4) in a limb 65 long × 8.6 across; the uniform control did not sort. The **typed tendon** (strong to muscle+bone, hostile to skin/medium) held its junction — 81% bonded to bone+muscle, **0.00 exposure** to skin/air — where the control let it drift (0.46 / 0.32). Layering AND a rule-placed interface, unattended. **FINDING (from the render, not the metrics): a thin, highly-cohesive bone core is Rayleigh-Plateau unstable and PINCHES into segments along the length. Adhesion cannot hold an axis.** That is real physics, and it names the next rung. | typed interfaces need hand-authoring per pair — they did not |
| 1.75 | **The skeleton is the scaffold.** Lay the bone along the L-system axis (the evolution engine's genome), then let adhesion wrap muscle/skin around it. | ✅ **DONE 2026-07-14** (`python -m core.limb`, the integration module fusing `core.terrarium` + `core.matter`). A bent 3-segment skeleton (terrarium `Bone` objects) was voxelized into a **frozen** bone axis, then differential adhesion wrapped it: bone stayed **ONE continuous connected blob** following the bend (where rung 1.5's free bone pinched into 2+), muscle formed the inner sheath (**100% of the bone's tissue-neighbours are muscle**), skin the outer shell — radial order bone 18.3 < muscle 21.2 < skin 25.6, unattended. **The two halves of the whole system are one pipeline now: skeleton = AXIS, adhesion = RADIAL TISSUE.** | the axis and the tissue could not co-generate without hand-tuning — they did |
| 2 | **Bake to UE5 (Nanite).** Voxel anatomy → per-tissue meshes → import + enable Nanite in the live editor. It renders and shadows. | ✅ **DONE 2026-07-14** (`core/bake.py` + `core/bake_to_ue5.py`). Marching cubes on each tissue's smoothed occupancy → three watertight, materialed, nested meshes (skin/muscle/bone, 66k tris) → a UE5-importable GLB. Then, driving the LIVE editor over the MCP bridge: import (glTF splits per-tissue), `nanite_rebuild_mesh` on each, spawn, screenshot. **It rendered and shadowed — grown flesh (muscle under translucent skin) as native Nanite geometry, witnessed in-editor.** The Chaos Flesh *deformation* rig is rung 3, not this. | the baked asset is uglier or slower than a hand-made one — it is neither |
| 3 | **It moves — THE SPINE.** The skeleton IS the rig: skin the flesh to the terrarium bones; the trained BRAIN poses it. | ◐ **HEADLESS DONE 2026-07-14** (`python -m core.rig --mode walk`). From the system audit: the real evolved 17-bone body, fleshed by adhesion, auto-skinned (k=4 inverse-distance), and posed frame-by-frame by the trained brain's actual gait joint angles (FK + linear blend skinning). The flesh deforms coherently with the gait — it mapped without hand-tuning because `mjcf.py` and `rig.skeleton_frames` build the joint axes identically. **This closed the audit's two biggest gaps: the fleshed body is now the REAL evolved one (GAP #2), and the BRAIN drives the flesh (GAP #1) — the two halves are one spine.** Remaining: export as a UE5 skeletal mesh + animation clip (the in-editor half). | the brain's pose can't map onto the mesh skeleton without hand-tuning — it did |
| 4 | **Coalesce / fracture.** Quiet bulk → one static item; a cut → live cells locally. | ⬜ | the merge/split thrashes or the seam cracks and cannot be stitched |
| 5 | **Grow the library.** Fat, chitin, bark, stone, water — additively. | ⬜ | each new brick needs bespoke engine work instead of just a struct |
| 6 | **A world.** The same substrate builds environment, not just creatures. | ⬜ | storage, not render, makes world-scale cell detail impossible |
| 7 | **A game.** Decide what the player DOES in this world (separate design). | ⬜ | — |

---

## 11. Open questions (the next conversations)

- **The game.** Substrate is decided; the loop is not. What does the player do?
- **The storage budget.** How much unique cell-dense geometry can we actually stream? This bounds
  rung 6 and should be measured early, not assumed.
- **Authoring vs. emergence.** How much of a body is grown by adhesion vs. specified by the
  genome? The first limb (§9) is where we find out.
- **Where behavior lives.** Which bricks get a `behavior` (muscle contracts, water flows) and
  which are inert? "Pull only what the game reads" is the rule; the list is the work.

---

## 12. The expansion — from a limb to a player, and a world

The reason to build the pipeline is not the limb. It is what the limb makes cheap.

> **THE LEVERAGE: once the machine works, a new thing in the world is a new RECIPE, not new
> engine code.** The assembler never changes. You add content the way you add a save file.

That is the multiplier that turns "a limb" into "everything," and it is worth being concrete
about, because it is the whole payoff. Everything below is forward-looking — rung 3 and beyond —
but every step lands on a rung that already exists or is one integration away.

### The worked example: our first player character

In the human's own words: *"get the biology of a human, program that into our system, and bam,
we've got our first player character."* Here is exactly what that means in this machine — and it
is not hand-waving, because each step is a rung.

A human is a **recipe** with three parts:

1. **A skeleton** — the human skeletal frame as an L-system / genome. This is rung 1.75's axis,
   the scaffold adhesion cannot provide itself (rung 1.5 proved that: a thin bone rod segments
   without one).
2. **A tissue map** — which bricks go where: the major muscle groups over the bones, fat
   distribution, the skin shell, and the handful of organs the *game actually reads*. This is
   "pull the variables that matter" applied to a person — you encode the deltoid because it moves
   the arm and shows through the skin; you do not encode the islets of Langerhans, because no
   game system reads them.
3. **Parameters** — height, build, age: the knobs that turn one recipe into many people.

And the reference data for this **already exists** — anatomical atlases, the Visible Human
Project, standard muscle and bone datasets. You are not inventing a human; you are *encoding the
game-relevant subset of a known one.*

Feed that recipe to the machine: the skeleton lays the axis, differential adhesion wraps the
muscle/fat/skin around it (rungs 1–1.75), the coalesce/fracture rule keeps it cheap (rung 4), and
the bake turns it into a normal UE5 character (rung 2) — a dense Nanite mesh on a Chaos Flesh rig
on a skeletal frame — driven by the same evolved controller that already walks the creatures.

The payoff is not "a character mesh." A hand-modelled mesh gives you a *shape*. **A grown anatomy
gives you a shape that can be WOUNDED** (the skin fractures and the muscle shows — the same rule
as everything else the machine grows), **VARIED** (one recipe, one parameter, a different build —
anatomically coherent, not a stretched mesh), and **MOVED** by muscle that is actually there.
That is the difference the whole substrate buys, and none of it is a per-character feature — it
falls out of how the thing was grown.

### Clothing, armour, equipment — not a special system

*"We'll have to make sure they have clothes on."* Good — and clothing is the cleanest proof that
the substrate generalises. A garment is just **more bricks**: fabric bricks with a "drapes over
the skin shell" typed interface (§3); armour as rigid bricks; both worn as a layer on top of the
skin. They tear and dent through the *same* coalesce/fracture rule as flesh. There is no "clothing
system" to write — there is a fabric brick and an interface, and the machine already knows what to
do with those.

### One recipe, a population

Because the recipe is parametric — like the genome it is — one human recipe is a whole population.
Turn the "build" knob and the fat bricks redistribute *correctly*; turn "age" and the tissue
properties shift. This is procedural character generation, but grounded in anatomy, so the
variation is coherent rather than a mesh stretched at the seams.

### The library grows; the engine does not

Human, then wolf, then oak, then granite. Each is a recipe; the assembler that grows them never
changes. This is the LEGO set that equals everything, filled one recipe at a time — and every
recipe you add is content the whole rest of the machine (wounds, variation, evolution, the bake)
*immediately* knows how to handle.

### The compounding opportunities

Each is unlocked by the substrate, and each is grounded in a piece that already exists:

- **Physiology the game reads.** Stamina from muscle mass, injury from tissue damage, growth and
  aging by re-running the recipe over time. The numbers are already in the bricks.
- **Inheritance.** Mix two recipes and the offspring's anatomy is the blend — which is exactly the
  genome crossover the [evolution engine](THE_EVOLUTION_ENGINE.md) already does. Breeding becomes
  real, not cosmetic.
- **Evolve the anatomy, not just the skeleton.** The Matter Model × the Evolution Engine: the
  trainer can select *fleshed* variants — a stronger build, a leaner one — against an objective,
  not merely morphology.
- **Universal wounds, surgery, disease.** Because everything is layered bricks, a cut reveals
  structure the same way in a human, a creature, or a tree; a disease can spread through a tissue;
  a wound can heal by re-growth. One mechanism, every object in the world.
- **Modding as data.** A recipe is data, not code — designers, or players, can add creatures,
  plants, and gear to the world without touching the engine.

### The honest gates (opportunities, with their costs)

- **Each recipe is real work.** Encoding a human's game-relevant anatomy is a project, not a
  weekend. The *pipeline* is reusable; the *recipe* is earned.
- **The bake must exist first (rung 2).** None of this ships until grown anatomy becomes native
  UE5 assets, cheaply.
- **Grown is not automatically beautiful.** Art direction still matters; the machine gives you a
  correct anatomy, not a directed one.
- **"Pull what matters" is a discipline, applied per recipe.** The urge to model the whole human
  is the lollipop trap in a new costume — encode what the game reads, and nothing more.

> A limb was never the goal. The goal is the day a designer writes a recipe, feeds it to the
> machine, and a new living thing walks into the world already able to be wounded, varied, bred,
> and evolved — because the machine that grew the limb already knows how to do all of that to
> anything it grows.
