# The Matter Model — a world built from living bricks

> **STATUS: mostly DESIGN; rungs 0–1 BUILT.** Born from a design conversation on 2026-07-14.
> The generation half is proven — `core/matter.py` shows differential adhesion self-assembling
> a bone/muscle/skin limb cross-section from a scrambled start, with a failing control (§10).
> Everything from the UE5 bake onward (rung 2+) is still design. Numbers marked "UE5 fact" or
> "reuse" are claims, not measurements; the only measured results here are in rungs 0–1. That
> line between built and planned is kept sharp on purpose, so no successor mistakes one for the
> other.
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
| 1.5 | **Shape, attachment, 3D.** Elongate the cross-section into a limb; add typed tendon/membrane connectors; lift the lattice to 3D. | ⬜ | typed interfaces need hand-authoring per pair instead of a rule |
| 2 | **Bake to UE5.** Dense Nanite mesh + coarse Chaos Flesh rig. It renders and shadows. | ⬜ | the baked asset is uglier or slower than a hand-made one |
| 3 | **It moves.** The muscle contracts the bone; the dense skin follows the rig. | ⬜ | motion needs per-cell simulation to look right (budget blows up) |
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
