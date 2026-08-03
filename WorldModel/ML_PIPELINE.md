# WorldModel — the generative ML pipeline

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
> **RULE 0 IS ENFORCED AT S-1 VALIDATE** — every port tested alone, and `port_test()` REFUSES to
> register a test that names no falsifier. The model it feeds: `docs/THE_COMPILER.md` — ports →
> primitives → programs → parser → runtime → calibration.
>
> **[docs/THE_LAW.md](../docs/THE_LAW.md)** · the method: `docs/THE_WORKFLOW.md` §0
> · 26 rules: `Chimera/docs/EXPERIMENTAL_METHOD.md` · gate: `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

> **This is the GENERATE half.** `Construction/` extracts genomes from real scans;
> `WorldModel/` learns a latent space over splat clouds and generates new ones.
> Documented 2026-07-23 after an audit found seven working scripts and nine trained
> checkpoints with no doc entry at all.

**Honest status:** the code and the trained checkpoints are on disk. Sizes and
architectures below are read from the files. **Nothing here was re-run or re-verified
during this documentation pass** — treat performance claims as unrecorded, not as proven.

---

## 1. The model — `model.py`

```
SplatVAE
  Encoder: PointNet-style per-point MLP → max pool → 256-d latent (mu, logvar)
  Decoder: latent → N × D splat parameters
  point_dim = 10   latent_dim = 256   num_splats = 4096 (default)
```

A VAE over **splat clouds**, not images. Each point carries 10 channels (position,
scale, rotation, colour, opacity — see `splat_cloud_to_tensor`), so the latent encodes a
whole object's splat configuration rather than a picture of one.

**Known limit, stated in the source:** for N > 100K splats it needs patch-based encoding,
which is *not yet implemented*. Current captures well exceed that, so the VAE operates on
sampled/normalised clouds, not full scans.

---

## 2. Training — three data paths, one model

| Script | Role | Notes |
|---|---|---|
| `train.py` | **The reference run.** Generates procedural oak clusters via `ParticleEngine.tree_trainer.TreeParams`, trains SplatVAE, samples new trees. | 300 epochs, batch 16 |
| `parallel_train.py` | Same data generation across **all CPU cores** (`ProcessPoolExecutor`) | for bulk dataset builds |
| `warp_train.py` | Data generation on the **GPU via NVIDIA Warp** — "zero CPU bottlenecks" | `generate_tree_kernel` → `generate_trees_gpu` → `train_on_gpu` |

The three differ only in how training data is produced. `warp_train.py` is the one to
reach for at scale — consistent with the project-wide rule that the GPU is mandatory.

### Trained checkpoints on disk (`WorldModel/training_data/`)

| File | Size | Apparently |
|---|---:|---|
| `physics_vae.pt` | 179 MB | physics-conditioned latent space |
| `warp_vae.pt` | 179 MB | trained via the Warp GPU path |
| `game_vae.pt` | 113 MB | game-asset latent space |
| `expanse_vae.pt` | 73 MB | large-scene latent space |
| `real_tree_normalized.npz` | 111 MB | normalised real-capture training set |
| `tree_vae_sampled.npz` | 0.6 MB | generated samples |
| `molds/membrane_classifier.pt` | 62 KB | **membrane labelling** (see §5) |
| `molds/membrane_classifier_v2.pt` | 63 KB | v2 |
| `molds/pattern_classifier.pt` | 93 KB | pattern labelling |

**No training logs or metrics accompany these.** Which checkpoint corresponds to which
run, and what any of them scored, is not recorded anywhere — that is a real gap.

---

## 3. Rendering at scale — `nanite.py`

Nanite-inspired hierarchical splats, borrowing the UE5 idea without the engine:

1. Objects decompose into **clusters** of fixed size (~1024 splats)
2. Clusters form a **LOD hierarchy** (coarse → fine) via `build_cluster_tree` / `_subdivide`
3. At render time, **cluster selection by screen-space error**
4. Only visible clusters at the right LOD are rendered

Classes: `Cluster`, `ClusterTree`. This is what makes a VAE-generated world renderable
rather than merely representable.

---

## 4. World generation — `infinite.py`, `cellular.py`, `universe.py`

```
world coordinate → hash → latent vector → VAE → clusters → render
```

| Script | Role |
|---|---|
| `infinite.py` | `WorldRegion` / `InfiniteWorld`. Each region (~100 m³) hashes its coordinates to a latent and generates its own cluster tree; only regions near the camera exist. **Deterministic: same coordinate, same world, forever.** |
| `cellular.py` | **Cellular Construction Rules** — `CellRule`, `CellNode`, `TreeCells`, `grow_cellular_tree`. Explicitly *not positions for splats* but **rules that produce splats**: "A tree is not a collection of splats. It is a set of rules that produce splats at the right positions with the right properties." |
| `universe.py` | `PhysicalLaw`, `PhysicsUniverse` — one rule to bind them all. Gravity → trees grow up, water flows down, dust settles. Light → leaves orient skyward, atmosphere scatters blue. Wind → canopy asymmetry, sand drift. Stress → branches taper, rocks fracture. |

---

## 5. Relationship to MEMBRANE PROGRAMMING (`CLAUDE.md`)

These are **not separate projects.** The membrane architecture in `CLAUDE.md` is the
design; this directory is its implementation:

| Membrane concept | Implemented by |
|---|---|
| "We don't write code — we define training patterns and energy principles" | `cellular.py` (rules, not positions), `train.py` |
| Physics as the generative substrate (gravity / light / wind / stress) | `universe.py` — `PhysicalLaw`, `PhysicsUniverse` |
| Membrane labels verified by physics, not visual interpretation | `molds/membrane_classifier*.pt`, `molds/pattern_classifier.pt` |
| Level 1–4 hierarchy (Sky → Ground → Growth → Observer) | `universe.py` laws + `infinite.py` regions + growth in `cellular.py` |
| Same seed, same world | `infinite.py` coordinate hashing |

**If you are working on membrane programming, these are the files.**

---

## 6. Other files here

| File | Role | Documented in |
|---|---|---|
| `splat_io.py` | `.ply` splat I/O. **Colour is SH-DC, not sigmoid:** `rgb = 0.5 + 0.28209479177387814 · f_dc` | `Construction/SPLAT_DNA_WORKFLOW.md` §9 |
| `clay.py` | Procedural ship hulls — `SHIP_PARAMS`, 24 parameters | `CLAUDE.md` |
| `physics_tree.py` | Physics-driven tree growth | `Construction/DESIGN.md` |

---

## 7. Known gaps

- **No training logs or metrics.** Nine checkpoints, no record of what produced them or
  how they scored. Any future run should write a sidecar with config, dataset, epochs and
  final loss.
- **Patch-based encoding unimplemented** — caps the VAE at ~100K splats while real
  captures run to millions.
- **The extract and generate halves are not yet connected.** `Construction/` recovers
  material genomes from reality; `WorldModel/` generates from a learned latent. Feeding
  recovered genomes into the generator is the obvious next step and has not been built.
