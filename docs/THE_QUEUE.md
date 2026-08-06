# THE QUEUE — how the whole game trains at once

*2026-08-06. Operator's directive: fill the GPU. After the seed and the canonical
prints prove, we author every concept the game needs as a print spec, and a
scheduler keeps the 4090's queue full until every concept has a verdict. This file
is the design; each concept still earns its own RULE 0 membrane before it enters
the queue (a falsifier named before its run — the queue executes membranes, it
does not replace them).*

## THE PIPELINE

1. **PROVE** (in flight): the seed settles (runs 1-4), the canonical prints hold or
   fail honestly (core_shell, disk, lattice). Nothing below matters if these lie.
2. **AUTHOR THE MANIFEST** — `LightEngine/categories.json`: every game concept as a
   spec: `{category, structure, geometry, seed, n, falsifier_id}`. This IS the
   light-era term tree: each entry is a membrane whose claim is "this printed form
   persists / behaves under the two forces + radiation". No concept enters without
   its falsifier pre-registered in `docs/THE_CATEGORIES.md`.
3. **SCHEDULE** — `LightEngine/queue_runner.py`: packs the manifest into batches
   sized to fill the card (target ~262k resident threads: W=64 worlds at N=4096,
   or fewer worlds at larger N — the packing is derived from measured occupancy,
   not guessed). One process, one CUDA context, one launch per tick per batch.
   As a batch finishes, the next packs and launches. Verdicts write to
   `LightEngine/output/ledger.json` (the queue's codebook).
4. **JUDGE** — every verdict lands with its metrics and frames. Falsified concepts
   get their successor named in THE_CATEGORIES.md, exactly as the seed chain did.

## THE CATEGORIES (draft skeleton — details earned by the proofs)

- **CELESTIAL**: core_shell (solar systems), disk (galaxies, accretion), orbiting
  pairs (moons), shell variants at derived radii/densities.
- **TERRAIN**: lattice (crystal/rock), slab (ground planes), packed bed (granular
  soil — random points at bond spacing under their own draw).
- **FLUID**: gas (hot structureless), liquid (cool structureless at bond density),
  droplet (a ball that should hold its edge against evaporation).
- **LIFE** (later): any clump that maintains its boundary while exchanging points
  with the medium — the hardest print, and the one the game is actually about.
- **UI/LIGHT** (the million): splat-shape-from-neighbor-covariance, morph between
  forms — render-layer membranes, judged by the reader, not the integrator.

## THE HARDWARE BUDGET (measured, this machine)

- W=64 x N=4096 = 262k threads ≈ 100% occupancy of the 4090; state ~20 MB.
- Direct O(N^2) per world: ~1 ms/tick for the whole batch (measured ensemble rate).
- A 10 t_ff window (~100k ticks) per batch ≈ 2-3 min. A 64-concept manifest is ONE
  batch. Ten categories of 64 concepts each ≈ 10 batches ≈ 30 min of GPU time.
  **The entire game's concept tree can train in an afternoon — once the concepts
  are written.** The bottleneck is authorship of honest falsifiers, not compute.

## WHAT KILLS THIS DESIGN (named before it runs)

- A concept queued without a pre-registered falsifier (the queue becomes a sweep).
- Packing beyond measured occupancy (the 3-process contention crash taught us:
  fill the card, don't fight it — one context, sized to the measured limit).
- Mixed-N batches that pad worlds into lies (uniform N per batch, always).
