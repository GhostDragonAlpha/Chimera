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
                             RENDER
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

**Its last two steps are the only Unreal left in the whole chain** (MCP import, level
save) and they are now dead. The replacement is already in the repo:
`Construction/gpu_render_torch.py` (pure-torch CUDA rasteriser, 9 views in 120 ms) and
`web/view.html`. **This is the one real seam left to close.**

---

## 3. What still points at Unreal

| Where | What | Status |
|---|---|---|
| `rebuild_world.py` steps 5–6 | MCP import → UE5, level save | **dead — swap for `gpu_render_torch` / `web/view.html`** |
| `ParticleEngine/` | Python particle sim **plus** a UE render bridge | **DO NOT DELETE.** `Construction/backend_3d.py` and `WorldModel/train.py` both import it (`tree_trainer.TreeParams`). The simulation is current; only the bridge is dead. |
| `core/bake_to_ue5.py`, `system_to_ue5.py` | UE staging | dead |
| `Chimera/docs/THE_MATTER_MODEL.md` §5 | "what maps to which UE5 technology" | dead section, **the rest of the document is the live concept** |

---

## 4. Honest gaps

1. **Extraction and generation are not yet joined.** `Construction/` recovers real material
   genomes; `train_splat_compositions.py` trains compositions against *library* optical
   targets. Feeding **recovered** genomes in as those targets is the obvious next move and
   has not been done. That single wire turns "a scan of rust" into "rust anywhere in the game."
2. **No training logs.** Nine VAE checkpoints (713 MB) with no record of what produced them.
3. **Relighting is unsolved.** Structural DNA (size/shape/angle) is lighting-clean; colour
   DNA carries baked capture light.
4. **Patch encoding unimplemented** — caps SplatVAE at ~100K splats; real captures are millions.

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
