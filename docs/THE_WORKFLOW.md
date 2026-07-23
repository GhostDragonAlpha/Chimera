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
| **07-23** | **AUTOMATED WORKFLOW** | `sequential_orchestrator.py` - continuous sequential agent pipeline (research → validation → recombination → integration → documentation)
| **07-23** | **AUTOMATED WORKFLOW** | `sequential_orchestrator.py` - continuous sequential agent pipeline (research → validation → recombination → integration → documentation)
| **07-23** | **THE COMPOSITION SIDE** | `progeny.py` (children/placement/verbs), `membrane_shapes.py` (containers), `render_world.py` (GPU render), and the link that made trained compositions reach the world builder |
| **07-23** | consolidation | local-model docs, experimental method, this file |
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
3. **The splat-type catalog has a ceiling.** `beam` caps at aniso 0.95 but real material
   measured 0.994 — you cannot emit what the vocabulary cannot express. Needs a more
   extreme emitter + finer scale control. Measurable target.
4. **Colour and opacity are recovered but unused in composition matching** — only
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
- **Measure the thing, not a proxy** (`docs/EXPERIMENTAL_METHOD.md`).
