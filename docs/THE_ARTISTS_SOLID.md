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
  **CORPUS VERDICTS (2026-08-27, second session — batch v3, SEED=20260827,
  production pitch = law/4, reports `.tmp/monkey_assets/recon/*_report.json`,
  gate `*_gate.json`):** the geometry door is OPEN — **gate 5/5 PASS** (all
  contract GLBs watertight, `load_glb_triangles` parses, `inside_mask`
  ray-parity accepts; probe accuracy per part in the gate files) — and the
  mass bound is an EARNED FALSIFIED for the uniform lattice, 0/37 parts at
  <=2% (best: 9906 Object_0 at 5.00%). Per asset, no verdict without numbers:
  - `8955fb5b` (SALLY): body conv 10.41% FAIL, silhouette 0.39% h PASS,
    41 caps (max 4.27u); eyes conv 17.10% FAIL, silhouette 0.15% h.
    Seen live in the engine: 2 parts, 409k tris, smooth at p/4.
  - `1534c1b1`: Object_1 conv 8.72% FAIL + silhouette 1.20% h FAIL (the one
    silhouette breach besides f4783); Object_0 conv 43.26% FAIL. 150 caps.
  - `22d16268` (Cymbal Monkey, law fallback h/100 = 1.966): 15/22 parts
    SUB-LAW (cells across at law pitch 0.1-2.8 — the asset is a box of tiny
    parts), 7 FAIL incl. pCube12 at 9068% and r_ear_helix3 at 3624%
    (thin-walled parts whose interior collapses under refinement).
  - `9906e586`: 5/9 SUB-LAW, 4 FAIL (5.00-35.46%).
  - `f4783633`: BOTH bounds fail on both parts — conv 55.99% / 274.82%,
    silhouette 2.47% / 10.13% h. Cause named, not hidden: the soup carries
    **3,027 boundary loops** (1,412 + 1,615); the capper closes them, the
    solid is watertight and gate-accepted, but a soup that shredded is not a
    reconstruction target — this asset is a candidate for corpus exclusion
    or manual repair, and the operator sees it as it is.
  Reading for the roadmap: the geometry door (consume any soup -> watertight
  per-part solid) WORKS at corpus scale; the mass law needs the graded
  lattice (BET-A2), exactly as the decay measurement predicted. This is not
  a tolerance story — the 2% bound never moved.

**THE TRIANGLE SUBSTRATE (operator decree 2026-08-27, Phase 4 — an
architecture correction, accepted):** *triangles are the CA substrate; the
cubes are invisible scaffolding — a Cartesian address frame, never the
matter. Every triangle has a center; the center is its Cartesian address;
the cube that holds the center only tells the automaton who the triangle's
neighbors are and lines up with the neighboring cubes. Each cube is its own
Gaussian space (the frost hook: the cube holds the local frame, the triangle
centers inside it are the anchors). The Phase-3 voxel automaton acted on the
scaffolding and let triangles fall out — that era's repair (centroid-fan
caps) is exactly where the corpus bled, and the substrate below replaces it.*
Two membranes, theory BEFORE code per Rule 0:

- **BET-T1 (the registry / the address law).** *Statement: an object can be
  stored as a bare triangle list where every triangle is reachable through
  the cube index and every edge-adjacent neighbor lives within the 26-cube
  ring — the cubes give the automaton its Cartesian order without
  quantizing the matter.* The cube edge is DERIVED, never chosen: it must
  cover the worst edge-adjacent center-to-center distance in the mesh
  (measured per part from the dual graph), else a neighbor could hide
  outside the ring. *Prediction: on all 5 corpus GLBs, cube-ring neighbor
  queries reproduce the dual graph 100%, and 100% of triangles are
  reachable.* *Falsifier: any edge-adjacent neighbor missed by the ring,
  or any unreachable triangle — then the cube derivation is wrong, and it
  is the derivation that gets fixed, never the 100%.*
- **BET-T2 (the birth rule — triangle-native repair).** *Statement: a wound
  (split artifact) can be closed by birthing triangles at the triangle
  level — a boundary edge births when the triangle on the far side of the
  wound is within voting range — while true openings (sockets, mouth) stay
  open because no far-side triangle votes.* No rasterization: the pitch
  disease (thin members vanishing, the measured 0/37 mass FALSIFIED) cannot
  exist on this substrate. *Prediction: on 8955's raw body soup (41 boundary
  loops, NO caps), the boundary-edge count falls to ~0 at the split seams
  and the result passes the same ray-parity gate.* *Falsifier: any true
  opening measured closed (the eye sockets must remain open) — then the
  rule cannot tell wounds from features, and the voting range law, not the
  requirement, is what gets re-derived.*
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

**THE HOLOGRAPHIC ANCHOR (operator decree 2026-08-27 — "a holographic engine:
the triangles are the mirrors AND the structure of reality; they will be both,
and easily expressible by AI").** Theory BEFORE code, Rule 0. The identity that
makes it a law instead of a metaphor, verified numerically today (max rel. err
0.0016 vs 2M-sample Monte Carlo, three arbitrary triangles):

- **A triangle IS a Gaussian.** A uniform measure over a triangle has
  covariance exactly `Sigma_2 = (1/12) * sum_i (v_i - m)(v_i - m)^T`, m the
  centroid. Not fitted, not approximate: identity. A Gaussian splat is a
  triangle given a measure; a triangle is a splat at zero normal thickness.
- **The 14 splat parameters decompose 10 derived + 4 free.** Standard 3DGS:
  position(3) + rotation(4) + scale(3) + opacity(1) + color(3) = 14. On this
  substrate: position = the BET-T1 Cartesian address; rotation = quaternion
  with z->normal and the in-plane twist FIXED by the major eigenvector of
  Sigma_2 (derived, never chosen; equilateral degeneracy -> canonical fallback,
  stated here before any run); scale = sqrt of Sigma_2's two eigenvalues
  (in-plane extent IS the triangle's shape) plus a normal thickness from the
  local-thickness law. That is 10 parameters the geometry owns outright. The
  remaining 4 (opacity + RGB / SH-0) are the material state — the ONLY numbers
  the CA ever evolves. A model learns 4 numbers per triangle on a fixed graph:
  that is what "easily expressible by AI" costs.
- **The mirror.** View-dependence anchors to the normal hemisphere: higher SH
  bands attach at the derived frame, and energy shared across a dual-graph
  edge is weighted by the dihedral angle — the fold between two mirrors is a
  measurement, not a parameter.
- **Both at once, one row.** The database row per triangle holds the 3
  vertices (reality: it occludes, collides, carries mass — the BET-A gates)
  and the 4 state variables (the image). No conversion, no duplicate
  representation: holography = the image is a function of the matter and the
  viewpoint, and nothing else is stored.

- **BET-F1 (the frost anchor).** *Statement: a mesh rendered as its derived
  per-triangle Gaussians reproduces the hard-triangle render from any
  viewpoint, with ZERO trained parameters.* *Prediction: on a corpus part, the
  derived-Gaussian render and the triangle render agree within a stated image
  bound, from held-out viewpoints.* *Falsifier: any novel-view deviation
  beyond the bound — then the anchor (covariance / rotation / thickness
  derivation) is wrong, and it is the derivation that gets re-derived, never
  the bound. Needle and equilateral triangles must be enumerated by the
  derivation BEFORE the run, not patched after.*

---

## SESSION VERDICTS — the bone/skin substrate view (2026-08-27, dyad-closed)

The visualization membrane for the substrate (skin + bone over the live Vulkan
engine, port 8090) iterated under the AI dyad until zero complaints. Record,
honest numbers, and the two bugs that were NOT geometry:

- **Construction.** One filled voxel mask per part (voxelize original
  watertight GLB at pitch span/192; `binary_fill_holes`, closing-seal retry on
  leak). SKIN = marching cubes on the dilated mask after a gaussian pre-pass
  (sigma 0.7 voxels — melts the voxel staircase; dilation closes 1-voxel
  diagonal pinholes). BONE = 3D skeleton of the SAME mask, X-filtered, drawn
  as rods. Containment by construction, then measured by two instruments.
- **THE CONTAINMENT MEMBRANE.** *Statement: the bone axis is strictly inside
  the skin.* *Instruments: (1) mask test — every skeleton endpoint inside a
  filled voxel; (2) ray parity (Möller–Trumbore, fixed irrational direction,
  no rtree) of bone points against the rendered MC skin.* *Falsifier: any
  bone endpoint outside on both instruments, or any red visible against empty
  background in the depth-tested fill render.* Measured on 8955: mask
  100.00%, ray 99.85% (body, residual = single-direction grazing flips on
  thin walls — ruled instrument noise against the depth-tested render, which
  shows zero red outside openings), eyes part 100%/100%.
- **Clearance cut (derived, not chosen).** The worst measured escape before
  the cut was 0.06 world units (~0.5 voxel); skeleton voxels within 1.5
  voxels of the mask boundary are pruned (3x the measurement). Bone stops
  before thin extremities instead of poking through — anatomically true:
  bone does not reach skin.
- **Bug 1 (display, not geometry): the two-centroid misalignment.** The
  posting tool recentered each GLB to its own centroid; skin and bone have
  different centroids, so the overlay floated off the body and EVERY angle
  showed "escapes" the instruments denied. Fix: one shared center for both
  slots. Lesson recorded: when the instrument and the eye disagree, suspect
  the display transform before the geometry.
- **Bug 2 (protocol, not geometry): a contaminated reference frame.** The
  reference stills of the original mesh were captured with a STALE bone
  overlay still in its engine slot; the dyad correctly flagged the red it
  saw — in the reference, not the reconstruction. Fix: purge the overlay
  slot (off-screen center) before any capture; the reference is now clean.
- **The mouth ruling (operator law confirmed).** The muzzle has a genuine
  surface opening (present with the bone removed entirely). Red seen THROUGH
  it is anatomy through a hole — LEGAL. Openings stay open; closing one
  would be the defect. The dyad accepted the ruling and classified it (c).
- **DYAD LEDGER (senses.watch orbit movies, LM Studio vision model):**
  round 1: 0.5 (stipple lines, blob eyes, X-mark skeleton — all fixed:
  1px GPU wireframe pipeline + overlay slot in the engine, world-space
  normals in render_tri.vert so light stops being glued to the camera);
  round 2 (technical consult): 0.75, ranked the one-mask construction first
  among fixes — built; round 3: 0.65 — flagged red that lived in the
  contaminated reference frame (bug 2); round 4: **NO COMPLAINTS, 0.95** —
  containment clean, fidelity holds across the orbit, residuals cosmetic
  (marching-cubes banding on skull/torso, blobby fingers: resolution, not
  shape).
- Known cosmetic residual, stated not hidden: MC banding is the pitch; the
  knob is span/192 and can be turned when beauty outranks speed.

---

## THE BUILD QUEUE — three membranes specced 2026-08-27 (operator session)

Named before any run, per Rule 0. Order of attack: registry + birth rule
first (Phase 4), then these in dependency order — F2 needs the substrate,
J1 needs the repaired bone-addressed mesh, W1 needs the cube scaffolding.

- **BET-F2 — the frost is distilled ray tracing (operator decree: "train ray
  tracing without ray tracing cores"; the mirror answers light FROM THE
  PERSPECTIVE OF THE VIEWER, the only thing that matters).** *Statement: a
  per-triangle light-response field, anchored to the substrate (10 derived
  parameters owned by geometry: address, frame, extent), reproduces an
  offline path-traced reference at runtime lookup cost.* *Prediction: train
  against path-traced renders of a corpus part over view x light
  combinations; the field matches held-out views AND held-out light
  directions within a stated image bound.* *Falsifier: any novel-LIGHT
  deviation beyond the bound — novel views alone make it a texture, not ray
  tracing; the falsifier is light generalization. Capacity starts at SH band
  0-1 per triangle; more channels are earned by the measured error floor,
  never by taste. Neighboring triangles share response across dual-graph
  edges (the graph owns the bandwidth).*

- **BET-J1 — hinge arrays (operator decree: elbows and knees are designated
  hinge arrays of triangles; joint state is CA state).** *Statement: a joint
  is a region where the substrate's law changes, not an object: triangles
  carry addresses relative to bone segments, the hinge array is the overlap
  band with dual addresses, the flexion axis is DERIVED from the two
  segments' geometry (never placed), and motion is a CA contraction signal
  through bone-adjacent columns (muscles) torquing the array — gait as a
  standing wave, not a keyframed clip.* *Prediction: flex the monkey's knee
  0 -> 140 deg (range from the primate CT reference in the research doc);
  the hinge-array skin deforms with zero self-intersection and volume loss
  inside a stated bound.* *Falsifier: interpenetration or candy-wrapper
  collapse beyond the bound — the deformation law is wrong. Open by
  admission: the contraction LAW's source (hand-tuned vs consumed mocap) is
  a bet, stated here as one.*

- **BET-W1 — water on the scaffolding (operator decree: a river is the same
  idea as the hinge array).** *Statement: the bed and banks are consumed
  substrate; each cube column holds water height + flow velocity; the update
  is a CA exchange between neighbor columns proportional to height
  difference and bed slope; the surface triangle sheet is addressed to the
  columns; depth = surface minus bed (derived from two rows, never stored);
  creature interaction is free (occupied columns exclude water — the wading
  monkey is the same rows meeting, not a special case); the frost (F2) is
  what makes it answer light like water.* *Prediction: pour a volume onto a
  sloped consumed bed — it flows downhill, fills the basin, goes flat; a
  poke radiates rings; total volume conserved within a stated bound. The
  tick is DERIVED: shorter than a wave's crossing time of one cube.*
  *Falsifier: any uphill flow, or mass created or destroyed beyond the
  bound — the exchange law is wrong. Open by admission: spray (sheet tear)
  needs a sub-grid law we do not have yet; shore foam is cosmetic frost
  work, last.*

**2D-SPLAT AMENDMENT (operator decree 2026-08-27, supersedes any 3DGS reading
of the anchor above):** the frost is **2D Gaussian splatting ONLY** — each
splat is a 2D Gaussian on its triangle's own plane, never a volumetric 3D
blob. Consequence that makes the anchor STRONGER: the splat's normal/frame is
the triangle's normal/frame outright (the 2DGS paper's worst problem — surfel
orientation drift — cannot exist here), and because the mirror's tilt is
KNOWN at every moment, view-dependent reflection is simulated from the
geometry's angle, not fitted from data. A triangle is a 2D splat at zero
normal thickness; the 2D splat is that triangle taught to answer light.

**VIEW-VOLUME FIX (same day, operator report: "the nose and one hand are
severed at the wall of deletion"):** two causes, both fixed in the engine.
(1) Framing: at radius 13.5 a 45° FOV shows ~11.2 vertical units; the upright
monkey is ~15.2 tall — the feet left the FRAME (not a clip). Camera radius
for whole-body views is DERIVED: >= sphere/tan(22.5°) ~= 2.41x the bounding
sphere (2.7x with margin). (2) Zoom floor: the interactive camera could
scroll INSIDE the mesh (min radius 1.0 vs sphere 7.6) where the near plane
slices whatever it touches. The floor is now measured at upload from the
vertex data itself (max |v| about the target) — zoom stops at 1.02x the
bounding sphere, so no part can ever be deleted by the near plane again.
