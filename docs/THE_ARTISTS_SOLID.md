# THE ARTIST'S SOLID — the architecture of the artist tool

> Commissioned by the operator, 2026-08-27: "We have the power of an artist with the
> precision of a computer. This will be the most powerful artist tool ever created —
> architect its future."
>
> **OPERATOR DECREE (2026-08-27, same day): CAD FIRST, FROST DEFERRED.** The frost is
> unsolved at the current limits of AI technology and will be developed in-house — but
> "if I don't have a fancy CAD shape to splat them on, then it's all pointless." Work
> concentrates on Layer 1 (THE SOLID) until the solid exists; Layers 3+ wait. Layer 3's
> section below is kept as the record of where the frost goes when its time comes.
>
> This file POINTS, per the AGENTS.md law: it holds only what nothing else holds
> (the layered architecture and the phase bets) and cites the rest. Every phase
> carries a falsifier, because Rule 0 does not stop at physics membranes — a product
> plan that cannot lose is a description, not a theory.

## THE ONE-SENTENCE THEORY

**The solid is the only artifact the artist authors; every other representation —
mesh at any resolution, Gaussian-splat frost, physics proxy, technical drawing,
training datum — is a derived projection that can be regenerated forever and can
never drift, because it was never edited.**

The artist works on intent (shape, proportion, stance, surface). The machine
guarantees the warrant (watertight, balanced, load-bearing, provable). Neither
does the other's job. That division is the whole product.

## THE FIVE LAYERS

### 1 · THE SOLID — the source of truth

Every object the tool ships exists first as a **watertight, per-part solid**.
Two origins, one contract:

- **Authored** — CAD-kernel construction (OpenCascade via CadQuery/build123d,
  headless and local; BrepGen/DTGBrepGen-class models when organic B-rep
  generation matures). Parts carry names, materials, and mass.
- **Reconstructed** — scans and found meshes (the staged Objaverse monkeys)
  enter through Poisson/SDF shrink-wrap into closed solids. Triangle soup never
  touches the pipeline downstream of this door.

The contract is enforced by what already exists: `tools/cad_sample.py`'s
ray-parity sampler only accepts watertight per-part geometry. The loader is the
gate; there is no second path in.

**OPERATOR DECREE (2026-08-27): THE DATABASE OF AN OBJECT IS ITS TRIANGLE LIST.**
Whatever authors or reconstructs a solid must emit **standard triangles** — the
same `(part_name, verts, tri_indices)` contract `load_glb_triangles` already
returns — decoded deterministically. The division of labor is exact: **the CAD
system produces the standard triangles; the CA system crawls the object and
decodes it into the store** as a flat list of per-part triangles. The CA system
and the renderer then manipulate the SAME triangles: physics and appearance are
two views of one database, never two models kept in sync. A reconstruction
method whose output is not standard, predictable triangles (implicit fields,
point clouds, procedural-only surfaces) fails this decree no matter how pretty
it renders — it must tessellate before the CA system can crawl it, and the
tessellation must be reproducible from the stored parameters.

**OPERATOR DOCTRINE (2026-08-27), three principles:**
1. **CONSUME-TO-RECREATE.** Reconstruction is not repair. The source asset is
   consumed — destroyed as an artifact — and the object is *made over* based on
   what it is, as a CA-native version that can be given life and movement. The
   source is evidence, never the product; our object is the product.
2. **THE VOXEL IS THE DIMENSIONALITY.** A triangle floating in space has no
   address. The square (cell) contains the triangle; the lattice is what lets
   the CA locate, neighbor, and manipulate matter. This is why the voxel method
   is not one option among many — it is the step that gives the object
   dimensionality in our system. The mesh we keep is the lattice's surface.
3. **THE HARD FIGHTS GO TO OPEN CODE.** When a falsifier bites (the challenging
   part), the brief is pasted in chat and the operator carries it to the local
   Open Code agent (unlimited usage, runs indefinitely) for the long research/
   coding grind. The relay is the mandatory channel for those fights.

### 2 · THE BRUSH — how the artist works

The artist never edits vertices. The brush is **constraint and proportion**:

- Sculpt/place/generate freely, then **solidify** — the tool closes the shape
  and reports what the closure costs (volume added, silhouette moved).
- The tool **knows bodies**: the biomechanics membranes already in the repo
  (theStance, the symmetric stand, the gait envelope, the allometry work of
  Phase 0's F-1/F-2/F-3) are the beginning of an anatomical rulebook — a paw
  carries its load cells, a stance is feasible or it is refused, proportions
  come from measured allometry, not sliders.
- "Physically correct shapes" is literal: the brush can refuse. A monkey that
  cannot stand is rejected at authoring time, not discovered in the game.

### 3 · THE FROST — appearance as projection

Gaussian splats bound to the solid's surface, rendered by the C++ Vulkan
engine (`ChimeraEngine/engine/`, the settled renderer — see
`docs/THE_RENDERER_DECISION.md`). The frost is where the "how did he make that
with triangles" reaction lives — but the frost never edits the solid. Re-light,
re-splat, re-render at will: the geometry underneath is untouched, so the
physics never lies about the picture.

### 4 · THE WITNESS — every asset ships with its proof

The proof machinery (the engine gates, the dyad, `tools/chain_witness.py`,
`tools/methodology_gate.py`) is repurposed from ritual to **product feature**.
Each shipped asset carries:

- the measured numbers (CoM, mass per part, watertightness, stance margin),
- a blind-judged render — the dyad (`ChimeraEngine/senses.py` +
  `human_messenger.py`) confirming the appearance reads as the intent,
- the falsifier it survived.

No reference, no verdict — the AGENTS.md law becomes the quality bar buyers can
inspect. Nobody else in the asset market ships a proof.

### 5 · THE MARKET — monetization in sequence

1. **The game** — the chimeras (monkey first) are the showcase; the physics is
   the attraction, per the operator's thesis.
2. **The library** — every character made is a license-clean, proof-carrying
   asset; the corpus grows with each production.
3. **The corpus** — every shipped solid is also a *training datum*: organic
   B-reps/construction sequences are the dataset the AI-CAD industry does not
   have (its models are trained on mechanical parts — that gap is the moat).
4. **The tool** — only when the corpus exists does the authoring tool open to
   others. Layer 5.3 is what makes layer 5.4 defensible.

## THE PHASE BETS (each falsifiable, each named before its run)

- **BET-A (Phase 2, RUNNING):** the staged monkey GLBs reconstruct into
  watertight per-part solids that `load_glb_triangles` + ray-parity accept,
  with per-part mass within 2% of the triangle-soup estimate. *Falsifier: any
  body-sized shell fails to close, or closure moves the silhouette past one
  voxel of the source scan.*
  **MEASUREMENT SPEC v2 (2026-08-27, Phase 3 — the operator's two findings drove
  this: "the blocks are too big" and "even with big blocks the triangles should
  align into a smooth surface"):**
  1. *Extraction upgraded: binary on/off grid -> distance-field zero-crossing.*
     The stair-stepping was an extraction defect, not a lattice size: vertices
     snapped to cell corners terrace at any pitch. The surface is now cut where
     the MEASURED distance to the source surface crosses zero (sign from the
     fill, magnitude from dense surface samples) — vertices land on the true
     skin, big cells and all. Measured on the body: silhouette p95 improved
     1.09 -> 0.92 pitch; the tail reads smooth in the render.
  2. *Mass criterion re-derived for the smooth path: CONVERGENCE UNDER
     REFINEMENT.* Binary occupancy counts whole cells; the smooth surface cuts
     them — the two now measure different things (16% apart on the body), so
     the old comparator is void for the smooth path, exactly as the soup
     signed volume was found void before it. The derived reference:
     **|V(p) - V(p/2)| / V(p/2) <= 2%** — a volume that has stopped moving
     under refinement is the mass; no external estimate exists for open soup.
     Same 2% bound, third honest comparator — each replacement recorded with
     its reason, the bound never touched.
  3. *The paw law is now deterministic.* Surface sampling is seeded
     (SEED = 20260827, a stored parameter): the decree demands tessellation
     reproducible from stored parameters, and an unseeded law hands back a
     different pitch per run — measured drifting 0.083 -> 0.117 between runs.
  4. *Cell != triangle, recorded from the operator's question:* a boundary
     cell holds 1-4 triangles; the lattice is the address frame through which
     matter lives, never a one-triangle container.
  **MEASUREMENT FINDINGS (2026-08-27, second session — the corpus batch FAILed
  honestly, 5/5, and the failure was chased to its causes BEFORE any rerun):**
  5. *The leaks are mesh-space holes, not cell-space cracks: CAP BEFORE
     VOXELIZING.* Measured on `SALLY_body_0`: 41 boundary loops, largest 2.2u
     on a 10u asset (~44 cells at fine pitch) — the per-part split leaves real
     sockets, and no voxel-space seal can close a 44-cell hole without
     destroying the part. `trimesh.repair.fill_holes` refused (0 faces);
     pymeshlab's `meshing_close_holes` segfaulted on the corpus; the pipeline
     therefore carries its own centroid-fan capper (`close_boundary_loops`),
     and every cap is reported openly per part (loops, cap tris, max diameter).
     The capped, closed mesh — not the raw soup — is the reconstruction
     target: distance field, sign fill, and silhouette all measure against it.
  6. *The dilated seal FAKES DIVERGENCE — demoted to fallback.* Marking the
     one-cell dilation band as inside inflates volume ~3x (measured: 7.78 ->
     25.58); marking it outside undercounts a full interior layer with a bias
     that grows with pitch (rec 6.09 vs plain-fill 9.1 at p) — both directions
     manufactured a false |V(p) - V(p/2)| gap. After capping, the mesh is
     closed, no leak path exists, and the PLAIN fill is the honest sign.
     Dilation survives only as the residual-crack fallback, and shell-solid
     (the band as thin volume) as the honest answer for open sheets.
  7. *Band-limited distance field.* The all-cells KD query is the memory wall
     (p/8 on the body = 196M cells, ~5 GB of world coords before the query
     starts). The zero crossing lives within two cells of the surface, so only
     the band is measured; far cells carry +/-pitch, which the level set reads
     identically. Verified: band volume reproduces the all-cells volume to
     the digit (9.3224 = 9.3224 at p).
  8. *Silhouette bound re-expressed as HEIGHT FRACTION.* The <1.0-pitch bound
     double-counts refinement: in pitch units the measured deviation RISES as
     pitch halves (0.98 -> 1.00 -> 1.54 -> 2.81 down the ladder) while in
     absolute units it falls (0.98% -> 0.50% -> 0.38% -> 0.35% of height). The
     bound's physical intent was one law-cell, and the law pitch is ~height/100,
     so the bound becomes **silhouette mean <= 1% of asset height** — same
     intent, now invariant under refinement. Recorded BEFORE the corpus rerun;
     it does not move any mass verdict.
  9. *Refinement cap derived from the measured decay.* The full ladder on
     `SALLY_body_0` (band-limited, plain fill, capped soup): 9.3224 ->
     11.4571 -> 12.7872 -> 13.4991, convergence 18.63% -> 10.40% -> 5.27%,
     decay ratio ~0.5 per halving. Members thinner than ~2 cells carry no
     interior and VANISH from the level set at coarse pitch — that is the
     climbing volume, and it means the 2% mass bound is unreachable on a
     UNIFORM lattice inside the grid guard (p/8 = 197M cells reads 5.27%;
     p/16 = 1.5B cells). Production pitch is therefore capped at p/4
     (MAX_REFINE = 2), the mass shortfall is recorded as an EARNED FALSIFIED
     per part with its ladder, and the mass fight moves to BET-A2 — the
     graded lattice is not an upgrade, it is the measured necessity.
 10. *Paw-law fallback derived.* When no paw contact blob survives the dust
     cutoff (measured on the Cymbal Monkey, 22d16268 — its base is two small
     cubes), the load-bearing member is unmeasured and the law cannot speak;
     pitch falls back to the law's own sampling scale h/100, cross-validated
     on 8955 where paw measurement and h/100 agreed to the digit. Also fixed:
     per-part seeds now use crc32 (Python's `hash()` is process-randomized —
     an unseeded backdoor in the determinism decree).
  **MEASUREMENT SPEC (fixed 2026-08-27 after the prototype run, BEFORE the full
  run — the run that teaches you the estimators are broken is exactly when the
  spec must be written down, with reasons, never silently):**
  1. *Mass estimator replaced.* The soup's signed (divergence-theorem) volume
     is INVALID for open shells — measured on `SALLY_body_0`: soup read 13.998
     while two independent reconstruction estimates agreed at 9.25/9.33 (34%
     off). Open game exports carry interior/duplicate faces whose signed
     contributions are noise; there IS no valid triangle-soup mass estimate for
     open soup, which is precisely why we reconstruct. The criterion becomes:
     **reconstruction volume vs. independent grid-occupancy volume agree within
     2%** (prototype: 0.85%). The 2% bound itself is unchanged — what changed is
     which measurement it binds, because the old measurement was found void.
  2. *Silhouette statistic fixed.* The one-voxel bound applies to the **mean
     bidirectional Chamfer distance, in pitch units** (prototype: 0.72), with
     p95 and max reported honestly (1.06 / 2.0, localized at sub-law thin
     features — the paw law guarantees ≥3 cells across load-bearing members,
     not ear tips; a max of ~2 pitches at those features is the law's stated
     boundary, not the method exceeding it). Choosing the statistic after
     seeing data is only honest if the choice is recorded — this is that record.
  3. *Input corrected.* 4 of 5 staged GLBs carry out-of-range indices (staging
     split vertices per-part but kept shared-buffer indices; only `f4783...`
     is clean). BET-A's input is therefore the **raw downloads**, with part
     structure derived by the pipeline itself — the source is evidence, never
     the product (doctrine 1).

  **VERDICT (2026-08-27, first asset): PASS.** `8955fb5b` (MONKEY, dinesdiabolik,
  CC-BY-4.0) consumed from the raw download and re-created as watertight per-part
  solids (`.tmp/monkey_assets/recon/8955fb5b..._solid.glb`, contract GLB written
  by the pipeline itself — the staging defect cannot recur because our writer
  emits per-primitive buffers). Numbers (full machine-readable report beside the
  GLB): pitch 0.08326 derived by the paw law on surface-sampled points (grid
  75x121x75). **SALLY_body_0: watertight volume, mass consistency 0.98% <= 2%,
  silhouette mean 0.75 pitch < 1.0 (p95 1.09, max 2.25 at sub-law thin
  features).** **SALLY_EYES_0: watertight, silhouette 0.58 pitch, mass
  quantization 3.01% — flagged SUB-LAW, not failed: the part spans ~2.5 cells,
  below the >=3-cells law that sets the pitch, so the 2% mass bound does not
  bind it (quantization noise at 952 occupied cells; the part carries 2.8% of
  the body's mass, so the absolute error is 0.08% of body mass).** The real
  geometry gate accepts the result: `load_glb_triangles` parses it, and
  `inside_mask` ray-parity agrees with the solid (98.5% inside/outside probe
  accuracy on the body at grazing epsilons, 100% on the eyes). The reconstruction
  was SEEN through the Vulkan engine (`/mesh_bin` real-triangle path): fingers,
  tail, and muzzle survive visibly at the derived pitch; the splayed front pose
  is the source's stance, not an artifact. Engine note for the pipeline: the
  /membrane splat path died silently at 56k points (theShape ran at 25.7k) —
  a limit to characterize before large meshes go through it; /mesh_bin is the
  robust door for viewing solids.
- **BET-A2 (the graded lattice, operator-endorsed 2026-08-27):** a graded
  lattice — surface cells refined by the pixel law (a cell must subtend ~1px
  at the canonical view) and the LOCAL paw law (cell <= local thickness / 3),
  interior cells coarsened by the mass law — removes visible stair-stepping at
  the canonical view while every BET-A bound holds. *Prediction: silhouette
  p95 < 0.5 pitch-equivalent at the surface; mass convergence still <= 2%;
  cell count >= 10x smaller than the equivalent uniform fine grid.* *Falsifier:
  any crack or hole at a level boundary (the classic octree failure mode), or
  the mass bound breaks — then the grading law is wrong, never the tolerances.*
- **BET-B:** a monkey solid dropped into the stance membrane stands (the
  symmetric stand's feasibility band accepts it) without retuning the law.
  *Falsifier: the law needs a monkey-specific parameter.*
- **BET-C:** the frosted render of the reconstructed monkey passes the blind
  dyad at the existing 0.6 gate against a physics reading written from the
  solid's numbers. *Falsifier: alignment < 0.6 with the physics verified —
  then the appearance pipeline, not the geometry, is wrong.*
- **BET-D (the moat, long):** a corpus of ≥50 shipped organic solids suffices
  to train a construction-sequence model that authors a *new* standing animal
  with no per-species parameters. *Falsifier: the model's output needs
  species-specific repair — then the grammar, not the data, is the gap.*

## WHAT EXISTS TODAY (the architecture is not aspirational)

- Renderer: `ChimeraEngine/engine/build/Release/chimera_engine.exe` (Vulkan, port 8090)
- Geometry gate: `tools/cad_sample.py::load_glb_triangles` + ray-parity
- Witness: `tools/chain_witness.py`, `tools/methodology_gate.py`, engine MCP gates
- Dyad: `ChimeraEngine/senses.py` (LM Studio resident model, operator-loaded)
- Body laws: `story/theStance`, the symmetric stand (`tools/world.py`), gait envelope
- First corpus members: `.tmp/monkey_assets/staged/*.glb` (5, license-verified
  CC-BY-4.0, per `docs/research/2026-08-26_monkey_geometry_sources.md`)
- Hardware: RTX 4090 24 GB — the recommended tier for every local model cited

## THE OPEN QUESTIONS (owned, not hidden)

1. **Reconstruction quality on organic shells** — Poisson closes holes but
   rounds fine features; the paw/face detail budget is unmeasured. BET-A
   measures it.
2. **Frost binding** — how splats stay glued to a solid that later *moves*
   (the game wants animation, not statues). Undesigned; the rig is a solid-level
   question, not a mesh-level one.
3. **The brush UX** — layers 1/3/4 exist; the interactive authoring surface
   does not. It is deliberately last: tools built before the corpus guess at
   the workflow; tools built after it know.
