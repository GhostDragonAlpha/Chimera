# THE MASTER LIST — everything this is for, one page

*Rewritten 2026-08-27 by operator decree ("change the master list to fit my
vision"). The 32-continuation history is compressed, not erased: every claim
below names its run record or commit. When docs fight, run records beat prose;
`python tools/orient.py` prints live state.*

## 1 · THE ONE CLAIM (what this is for)

**A holographic engine: the triangle is BOTH the structure of reality AND the
mirror.** One database row per triangle — it occludes, collides, carries mass,
runs in the CA — and it answers light *from the perspective of the viewer*,
the only perspective that matters. Cellular automata give the matter life and
movement; a trained per-triangle light field gives it frost. The product is
**the game** — art so perfect in the reality of its light that people ask
*"how did he make something so beautiful with just triangles alone?"*

**The economics (operator doctrine):** the engine is open-sourced for
humanity — AI unlocks all doors, so there is no durable money in *how* a
thing is done; the machine will be absorbed into the membrane of ML within a
year or two. The only value is the art that comes out of it, and that value
is the artist's taste, amplified. Taste is the one input no absorption can
copy, which is why the human is a terminal of this system, not a user of it.

## 2 · THE ARCHITECTURE (operator decrees — settled, do not reopen)

- **Triangles ARE the CA substrate.** The cubes are invisible Cartesian
  address scaffolding; **each cube is its own Gaussian space**. The cubes
  give every triangle an address; the triangles are what we want.
- **A triangle IS a Gaussian.** Covariance identity verified numerically
  (max err 0.0016 vs Monte Carlo). 10 of the 14 splat parameters are DERIVED
  from the geometry (address, frame, extent); 4 are free — the material
  state, the only numbers a model ever learns per triangle.
- **Consume-to-recreate.** Eat a mesh, decompose it into the triangle
  database, regrow it CA-friendly with a bone axis. **Openings stay open**
  (sockets, mouth) — closing a true opening is the defect.
- **The bone axis.** Voxels are only scaffolding to grow the stick figure;
  triangles are addressed relative to bones. Determinism = ROM extremities +
  CA-filled interior, harnessed by the bone rig.
- **Hinge arrays.** A joint is not an object; it is a region where the
  substrate's law changes. Flexion axes DERIVED from bone geometry; muscles
  are CA contraction signals; gait is a standing wave, not a keyframed clip.
- **Water.** The cube columns hold height + flow; a CA exchange rule moves
  it; mass conservation is the falsifier. Creatures interact for free —
  occupied columns exclude water; the wading monkey is the same rows meeting.
- **The frost is distilled ray tracing — 2D splats only (operator decree:
  "we're only going to be working on the 2D version").** Not volumetric 3DGS:
  each splat is a 2D Gaussian living ON its triangle's plane — a surfel whose
  angle IS the triangle's angle, which is exactly what makes reflection
  simulation derivable (the mirror's tilt is known, never fitted). Train the
  light answer offline (path tracer or photographs), run it at lookup cost.
  "Ray tracing without ray tracing cores." Held-out LIGHT directions are the
  door, not held-out views — novel views alone make a texture, not a NeRF.
- **The dyad.** Silicon builds; a separate vision eye (LM Studio's resident
  model via `core/lm_gateway`) judges blind orbit movies; disagreements get
  measured; taste bottoms out in the operator and nowhere else.
- **Rule 0.** Statement / prediction / falsifier BEFORE the build. Derived,
  never chosen. Honest about the unmeasured. Docs append-only (this page's
  rewrite is by decree).

## 3 · THE LINES (every thread, state, next gate)

| # | Line | State | Next action | Home |
|---|------|-------|-------------|------|
| L1 | **The corpus** — 5 license-verified monkeys as watertight per-part contract GLBs | DONE (gate 5/5, `d7a8655e`, `d142f207`) | consumed by L3 | `docs/THE_ARTISTS_SOLID.md` |
| L2 | **The substrate view** — one-mask skin+bone, engine 1px wireframe + overlay slot | DONE — dyad **NO COMPLAINTS 0.95** (`34938671`) | reference pipeline for every later visual | `docs/THE_ARTISTS_SOLID.md` |
| L3 | **THE REGISTRY** (Phase 4a) — triangle centers = Cartesian addresses; cube edge DERIVED from max edge-adjacent center distance; dual graph; cube index must reproduce the neighborhood 100% | membrane pre-written, goal paused one step from run | RUN IT — falsifier: any neighbor not found through the 26-cube ring | `docs/THE_ARTISTS_SOLID.md` |
| L4 | **THE BIRTH RULE** (Phase 4b) — triangle-native wound repair, no voxel rasterization; 8955's 41 boundary loops close, sockets measured OPEN | membrane pre-written | after L3 — falsifier: any true opening closed | same |
| L5 | **THE FROST** (BET-F2) — distilled relighting on the substrate | specced (`8b36e2b6`) | needs L3+L4; then train on a corpus part, held-out LIGHT falsifier | same |
| L6 | **HINGE ARRAYS** (BET-J1) — CA-state joints, derived flexion axes | specced (`8b36e2b6`) | needs the repaired bone-addressed mesh; monkey knee 0→140°, zero self-intersection | same |
| L7 | **WATER** (BET-W1) — river on the cube scaffolding | specced (`8b36e2b6`) | needs L3's cubes; downhill flow + level + mass bound | same |
| L8 | **THE FIRST CHIMERA** — teddy-bear / monkey 50-50 split down the midline | pipeline proven at dyad 0.65 with a procedural stand-in (P9, `41893558`); real creature awaits the substrate | the creature the whole stack points at | `docs/THE_MASTER_LIST.md` §heritage |
| L9 | **THE GAME** | the artifact of value | arrives when L1–L8 produce a world | — |

## 4 · LANDED FOUNDATIONS (verified — do not redo)

- **T2 triangle carrier LANDED:** the triangle is a SOLID element — area
  rigidity `k = 0.75·K_BOND/A0` (derived, zero free numbers) + R7c bending.
  RUN A rel err 2.5e-9; 1000 ticks finite; energy drift 0.5% ≤ 1% net of
  radiation; max strain 2.19% honesty line; curvature-exterior
  domain-restricted, BOTH meshes pass (`models/cad_bear/ca_run.json`).
- **Octree lane:** B1 njit build byte-identical to the referee, 44.5→3.5 ms;
  persistent pool landed (`3ee05fb`); the live CA walk uses it (~12×). The
  visible pinned core the operator kept killing runs for is GONE.
- **Bone rig PASS 12/12 (P7):** ROM + CA interior slaved to a rig; mesh
  follows LBS exactly — J1's direct ancestor. **Tissue systems PASS (P6):**
  skin/muscle/bone as separate triangle systems with interface continuity.
  **In-between harness 27/27 (P8).**
- **Physics body lane CLOSED (Phase 0, 2026-08-27):** ports 19/19+2 REFUSED,
  primitives 7/7, actions 9/10 + RHYTHM_DRIVE's earned FALSIFIED (the test
  left failing, mechanism proven, no tolerance widened); S4 determinism
  52,472 stepped states bit-identical; theDeterminism PROVEN via MCP.
  Doctrine that carries forward into J1: allometry (no human-table number on
  another body), hard stops own the boundary, ligaments arrest the approach.
- **The dyad machinery:** LM Studio resident vision judge (adopt-never-pin),
  settle-capture fix (movies are real movies), `senses.watch` orbit protocol.

## 5 · HONEST NEGATIVES (recorded, never papered)

- **T13 SFC octree FALSIFIED** — structurally valid, 24× less accurate than
  the adaptive referee and slower; not a drop-in (`gate_octree_sfc.json`).
- **B2-A prange octree FALSIFIED 0.93×** — threads engaged, still no win;
  the 24-core build question stays OPEN.
- **RHYTHM_DRIVE (action) FALSIFIED as stated** — the drive CAN move the
  frequency in this regime; successor theory (cadence + the ligament wall)
  parked for the physics lane.
- **Substrate-view bugs that were mine, not geometry's:** two-centroid
  overlay misalignment; contaminated dyad reference frame. Both recorded in
  `THE_ARTISTS_SOLID.md` with the lesson: when instrument and eye disagree,
  suspect the display transform first.

## 6 · RETIRED / PARKED

- **UE pipeline EXCISED** (doctrine: nothing closed-source; ~1000 files,
  history retains all).
- **P-A stand lane PARKED** — blocked structurally (story ledgers hollow in
  this checkout); not dead, not gating anything above.
- **"Seconds held at forward = 0.5" RETIRED as THE metric** — that was the
  walk-first era. Every membrane now carries its own falsifier as the gate;
  the project's north star is the operator's sentence in §1.

## 7 · THE ATTACK ORDER

1. **L3+L4 — Phase 4** (registry + birth rule): falsifiers pre-written,
   everything else stands on this.
2. **L6 — hinge arrays** (the monkey bends its knee; life begins).
3. **L5 — the frost** (the mirror answers light; beauty begins).
4. **L7 — water** (the world gets a river).
5. **L8 — the chimera** (the first creature, dyad-judged).
6. **L9 — the game.**

**Division of labor (operator decree 2026-08-27):** Kimi holds project
context and writes elaborate prompts IN CHAT (never in docs) for transfer to
Open Code, where local agents run long construction loops. **HARD BOUNDARY
(same day): Kimi edits ONLY this file** — every other file in the repo
(engine, docs, tools, .tmp) is the construction agents' domain; if Kimi wants
a change anywhere else, it goes into a prompt, never an edit. This file is
the guide for BOTH sides: the prompter writes from it, the builder reads it
first and runs `python tools/orient.py` second. The operator ratifies,
steers, and is the human terminal of every dyad.

## 8 · THE RULES OF THIS PAGE

- This list is a MAP, not evidence: when it disagrees with orient or a run
  record, the newer fired falsifier wins and the row rots — amend, don't argue.
- Every thread has a home doc; no second source of truth lives anywhere else.
- Written so any agent, after any compression, can read ONLY this file and
  know what this is for, what is proven, what is unmeasured, and who owns
  the next gate.

## 9 · HERITAGE LEDGER (the 32 continuations, compressed)

Key run records behind §4/§5, newest last: T2 CA pre-registration →
degenerate-nan gate → T2 landed → run-record audit ("pass" prose corrected)
→ Option B derived rest-area → curvature exterior landed both meshes → T13
SFC falsified → octree option-(a): byte-identity, B1 njit 15×, pool, CA-walk
swap → doctrine: Wolfram frame, Earth gravity canonical, UE excised, island
retired → appearance messenger + dyad movie fix → SWING/UPRIGHT/RHYTHM_DRIVE
closed → 10-task swarm (P1–P10) integrated → Phase 0 closed → corpus 5/5 →
THE ARTIST'S SOLID (CAD-first decree) → substrate view dyad-closed 0.95 →
build queue BET-F2/J1/W1 specced. Full text: git history of this file.
