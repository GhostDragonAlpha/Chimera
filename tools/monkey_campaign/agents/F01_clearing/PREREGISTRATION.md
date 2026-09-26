# F01 Preregistration — frozen BEFORE implementation

Recorded 2026-09-24, before the recipe, declaration, loader, or tests were written.
Companion discovery note: `discovery_note.md` (same dir). Item F01, verbatim:
"Deterministic terrain/tree recipe, explicit extent and coordinate convention, safe
spawn and visible boundary. One clearing is sufficient; no planet or infinite-world
requirement."

## Statement (someone could disagree with it)

A single finite clearing for the monkey game can be authored as pure data — one
deterministic recipe compiling to one byte-identical declaration — that already
satisfies the engine's world convention (right-handed, Y-up, metres), places a safe
spawn and one trunk site by construction, and makes the physical boundary and the
rendered boundary the same edge, so no invisible wall can appear later.

## Prediction (not yet measured)

Compiling the frozen recipe twice — in-process and in a separate process — produces
byte-identical canonical JSON and identical sha256; the validator proves spawn
clearance from stored numbers alone; and every boundary-consistency check passes on
the authored declaration while refusing corrupted variants (deleted posts, posts moved
inward, posts shrunk below visibility, spawn moved into the trunk footprint).

## Frozen values (no tuning after this point)

- **Schema**: `chimera.monkey_clearing.v1` (house convention, `discovery_note.md` §1.4).
- **Seed**: `4598321` (= 0x463031, the ASCII bytes of "F01"). Frozen; not a tuned choice.
- **Determinism rule**: a self-contained splitmix64 integer PRNG (stable across Python
  versions and platforms, unlike `random`); every derived float is rounded to the
  1e-6 m grid before the canonical write; the declaration pins its own
  `declaration_sha256` over the canonical bytes. Same seed → byte-identical file,
  anywhere.
- **Extent**: square, half-width `20.0 m` (40 m × 40 m), centred at the origin;
  physical boundary at |x| = 20 or |z| = 20.
- **Coordinate convention**: right-handed, +Y up, metres, origin at scene centre,
  base ground plane y=0 — citations in `discovery_note.md` §2
  (`coupled_dynamics.hpp:52`, `earth_environment.hpp:41,44,68,118`,
  `tests_environment/native.cpp:13`, `units.py`).
- **Terrain recipe**: base plane y=0 plus exactly 5 cosine-profile mounds
  (radius 4.0–6.0 m, amplitude 0.05–0.12 m, centres from the seed). "Gentle" is made
  checkable: max |slope| of the heightfield must be ≤ 0.05 (verified by central
  differences on the stored grid). Grid: 41×41 samples at 1.0 m spacing materialised
  in the declaration; `height_at(x,z)` provided for sub-grid queries; validator
  requires grid ≡ function on every grid point.
- **Trunk site (data only; geometry qualified in F03)**: exactly one site, centre from
  the seed inside the annulus 8–14 m from the spawn, ≥ 3.0 m inside the extent,
  footprint radius **bound** `0.5 m` (maximum envelope for collision authoring;
  actual trunk geometry is F03's), upright axis +Y, explicit marker
  `"geometry_qualified_in": "F03"`.
- **Spawn-safety derivation (by construction, not search)**:
  - Spawn is FIXED first at the extent centre `(0, h(0,0), 0)`; the recipe forbids any
    mound footprint within `R_clear` of the spawn, so `h(0,0) = 0.0` exactly and the
    spawn stands on flat base ground by construction.
  - Declared body-footprint envelope `r_body = 0.25 m` (generous macaque envelope).
  - Required clearance `R_clear = r_trunk_bound + 4*r_body = 0.5 + 1.0 = 1.5 m`
    (trunk bound plus four body radii of passing room — derived from the two declared
    bounds, no free parameter).
  - The trunk placement constraint (≥ 8 m from spawn) strictly implies the 1.5 m
    requirement; the validator re-proves `distance(spawn, trunk) - r_trunk_bound >= R_clear`
    from stored numbers and refuses otherwise.
- **Boundary visibility design (physical + rendered, no invisible walls — F07's law)**:
  the physical rule is the extent square itself (the engine's existing
  `out_of_patch` semantics, `earth_environment.hpp:118`); the rendered markers are
  boundary posts lying exactly ON the perimeter lines, 80 posts (21 per edge, corners
  shared), spacing 2.0 m, height 0.9 m above local terrain, colour data included
  (ochre 0.72/0.55/0.20). The validator enforces the anti-falsifier-(c) invariants:
  (i) every perimeter point is within 1.0 m of a post base (coverage),
  (ii) every post protrudes ≥ 0.6 m above its local terrain (visibility),
  (iii) post bases coincide with the physical edge within 1e-6 m (the blocking edge
  and the visible edge are the same edge).

## Falsifiers (frozen before the run; a hit refutes the design)

- **(a) Same seed produces different declarations**: compiling twice (in-process and
  via a fresh subprocess) yields different bytes or different `declaration_sha256`.
- **(b) Spawn intersects a declared obstacle**: `distance(spawn, trunk centre) −
  r_trunk_bound < R_clear`, or any mound footprint covers the spawn disk, or
  `h(0,0) ≠ 0`.
- **(c) Boundary invisible while blocking motion**: any perimeter point farther than
  1.0 m from every post base; or any post protruding < 0.6 m above local terrain; or
  any post base off the physical edge by > 1e-6 m; or (the invisible-wall form) any
  declared physical bound inside the visible post ring.

## Stop rule

Determinism tests + spawn-safety proof + boundary-consistency verdicts are green with
receipts, and `git status` shows changes only in the owned dir + the two declared data
paths. CPU-only; no GPU, no engine C++ edits, no launched servers — exercising the
engine HTTP contract is recorded as a follow-up need (F02), per brief.

## Amendment 1 (2026-09-24, before implementation — derivation caught a contradiction)

The originally frozen mound range (radius 3.0–6.0 m, amplitude 0.05–0.15 m) violates
this prereg's own slope law. Derivation: a cosine mound h(d) = A·(1+cos(πd/R))/2 has
|h'(d)| ≤ A·π/(2R) (max of |−A·π/(2R)·sin(πd/R)|), so worst case A=0.15, R=3.0 gives
0.15·π/6 ≈ 0.0785 > 0.05 — the "gentle" bound would be false by construction.
Corrected by derivation, not tuning: radius 4.0–6.0 m, amplitude 0.05–0.12 m gives
worst case 0.12·π/8 ≈ 0.0471 ≤ 0.05 for EVERY allowed combination. Falsifiers,
seed, extent, spawn derivation, and boundary design are unchanged.

## Amendment 2 (2026-09-24, during implementation, before any run — derivation caught the superposition error)

The amendment-1 argument bounded ONE mound's slope, but overlapping mounds
superpose: 5 mounds at the amendment-1 maxima give Σ A_i·π/(2R_i) ≈ 5·0.0471 ≈
0.236 ≫ 0.05. Corrected by construction, not tuning: mound footprints are
DISJOINT (centre distance ≥ R_i + R_j, enforced at placement and re-checked by the
validator), so at most one mound contributes at any point and
|∇h| ≤ max_i A_i·π/(2R_i) ≤ 0.12·π/8 ≈ 0.0471 ≤ 0.05 everywhere. Seed, extent,
spawn derivation, boundary design, and all falsifiers are unchanged.

## Scope boundary

F01 places the trunk SITE as data and bounds its footprint; trunk geometry, surface
IDs and material provenance are F03's. Terrain rendering and collision surfaces are
F02's — the declaration carries the height grid and recipe so F02 consumes exact
numbers without re-deriving. Obstacle placement beyond the trunk site is F07's.
