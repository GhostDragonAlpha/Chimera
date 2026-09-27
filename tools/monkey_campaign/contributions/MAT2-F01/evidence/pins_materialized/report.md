# F01 Report — the finite clearing and its spatial units

Author: M-F01. Date: 2026-09-24. Checkout `E:/ChimeraWork/monkey-play-20260924`,
branch `monkey-play-20260924`, base master `32105f18` (HEAD at start `8c60bea3`).
Item F01, verbatim: "Deterministic terrain/tree recipe, explicit extent and coordinate
convention, safe spawn and visible boundary. One clearing is sufficient; no planet or
infinite-world requirement."

## What was done

1. **Discovery** (`discovery_note.md`): mapped the live scene-declaration pattern
   (compiled canonical-JSON bundles, self-pinned sha256, strict `require`/`Refusal`
   intake — `tools/science_funnel/common.py`, `earth_scene.py`, native loaders
   `graph_earth.hpp`) and pinned the engine's world convention with citations.
2. **Prereg frozen before implementation** (`PREREGISTRATION.md`): schema, seed,
   determinism rule, extent, spawn derivation, boundary design, three falsifiers.
   Two dated amendments record derivation fixes made BEFORE any run (mound range
   contradicting the slope law; mound superposition breaking it) — falsifiers
   unchanged throughout.
3. **Implementation** (pure Python, stdlib-only):
   - `tools/monkey_campaign/data/monkey_clearing/clearing_recipe.py` — the frozen
     constants, splitmix64 PRNG, `height_at`, deterministic
     `compile_declaration`, canonical `write_declaration`, strict `loads`/`load_declaration`,
     and `validate_declaration` (re-derives every claim from stored numbers).
   - `tools/monkey_campaign/data/monkey_clearing/clearing_declaration.json` — the
     compiled `chimera.monkey_clearing.v1` declaration (13,112 canonical bytes).
4. **Tests** (`tests/test_clearing.py`): 30 cases — determinism (in-process x2, fresh
   subprocess, cross-seed), schema/digest/grid tamper refusals, spawn-safety proofs
   and refusals, boundary coverage/visibility/invisible-wall refusals, loader
   strictness. **All 30 green**, standalone and via `python -m unittest` from the
   repo root.
5. **Receipts** (`receipts/`): `test_run.txt`, `validate_receipt.json`,
   `determinism_receipt.txt`.

## Measured numbers

| Quantity | Value | Frozen bound |
|---|---|---|
| Declaration bytes | 13,112, canonical, sorted keys | byte-identical per seed |
| `declaration_sha256` (body without pin) | `aa2607df97e0d6ec6a132b1e1ed0686da2ae920de7d659a8bb5ced013a358474` | — |
| sha256 of the committed file (with pin) | `18dd2ff65410cd1cf184a7a8df61c7503a6ce15083f30159e727e9a8117bfbc1` | — |
| Byte identity (committed vs 2 in-process vs 1 subprocess) | True, 4/4 × 13,112 bytes | falsifier (a) |
| Extent | square, half-width 20.0 m (40 m × 40 m) | frozen |
| Terrain | y = 0 base + 5 disjoint cosine mounds (R 4.0–6.0 m, A 0.05–0.12 m) | frozen |
| Worst grid slope (central differences, 1 m grid) | 0.034606 m/m | ≤ 0.05 |
| Continuous slope bound (max A_i·π/(2R_i), disjoint mounds) | ≤ 0.0471 | ≤ 0.05 |
| Grid ≡ height function error (1,681 points) | 0.0 | ≤ 1e-9 |
| Spawn | (0.0, 0.0, 0.0), flat base ground by construction | h(spawn) = 0 |
| Spawn clearance (dist − trunk bound) | 11.729184690233646 m | ≥ 1.5 m (R_clear = 0.5 + 4×0.25) |
| Trunk site | (11.976783, 0.0, 2.471766), local slope 0.0, bound 0.5 m, marker `geometry_qualified_in: F03` | annulus 8–14 m, inset ≥ 3 m |
| Boundary posts | 80 on the perimeter lines, spacing 2.0 m, height 0.9 m, ochre (0.72, 0.55, 0.20) | 80 = 160 m / 2.0 m |
| Worst gap from any perimeter point to a post base | 1.0 m (exactly the frozen max) | ≤ 1.0 m |
| Worst post off-edge error | 0.0 m | ≤ 1e-6 m |

## Falsifier verdicts

- **(a) same seed → different declarations: NOT OBSERVED.** Four compiles (two
  in-process, one fresh subprocess, plus the committed file) are byte-identical;
  `receipts/determinism_receipt.txt`. Splitmix64 + integer-grid rounding makes this
  version- and platform-stable by construction.
- **(b) spawn intersecting a declared obstacle: NOT OBSERVED; refusals proven.**
  Spawn is the extent centre, flat base ground by construction (mound footprints
  excluded within R_clear); clearance 11.729 m ≥ 1.5 m required. Corrupted variants
  (spawn inside trunk footprint, off-centre, lifted, mound over spawn, site outside
  annulus) are each refused with named codes.
- **(c) boundary invisible while blocking: NOT OBSERVED; refusals proven.** The
  physical rule (extent square) and the rendered ring are the SAME edge (worst
  off-edge error 0.0; invisible-wall guard `f01_invisible_wall` refuses any
  physical bound inside the ring). Coverage: every perimeter point within 1.0 m of
  a post base; posts protrude 0.9 m ≥ 0.6 m minimum. Removing posts, moving the
  ring inward, shrinking posts, or shrinking the physical bound are each refused.

## Handoff notes

### To F02 (terrain rendering + collision) — what you must consume

- File: `tools/monkey_campaign/data/monkey_clearing/clearing_declaration.json`
  (schema `chimera.monkey_clearing.v1`); loader/validator:
  `tools/monkey_campaign/data/monkey_clearing/clearing_recipe.py`
  (`load_declaration`, `height_at`, `validate_declaration`). Import from repo root;
  stdlib-only.
- Coordinates: right-handed, +Y up, metres, origin at centre, base ground y=0 —
  the engine's convention (citations in `discovery_note.md` §2 and inside the
  declaration's `coordinate_convention.citations`).
- Render/collision geometry source of truth: `terrain.recipe.mounds` +
  `height_at` (exact, 1e-6 grid) and `terrain.grid.heights_m` (41×41 @ 1 m, row = z,
  col = x, x/z from `x0_m`/`z0_m` by `dx_m`/`dz_m`). They agree to 0.0 — keep them
  agreeing in whatever mesh/collision you build (C14: render/query consistency).
- Boundary rendering: `boundary.rendered.posts_m` (80 × [x, base_y, z]),
  `post_height_m` 0.9, `colour_rgb` [0.72, 0.55, 0.20]. Posts must render AT these
  positions; the physical stop is `extent.boundary_rule` (engine `out_of_patch`
  semantics, `earth_environment.hpp:118`). Do not add any collider inside the ring
  — that is the invisible-wall falsifier (F07's law).
- Boundary physical semantics for motion: outside = |x| > 20 or |z| > 20; the
  declaration carries this as `boundary.physical` for your collision surface.
- Follow-up need recorded per brief: exercising the actual engine HTTP contract
  (mesh upload via `engine.load_mesh`, 9-float vertex layout pos+normal+color) is
  F02's task; nothing was launched here (CPU-only, no servers).

### To F03 (rigid climbable trunk) — what you must consume

- The trunk SITE is data, not geometry: `trunk_sites[0]` = site centre
  (11.976783, 0.0, 2.471766) m, footprint radius BOUND 0.5 m (maximum envelope your
  collision representation must respect — your actual geometry must fit inside),
  upright axis +Y, marker `geometry_qualified_in: "F03"`.
- Ground truth at the site: terrain height 0.0 m, local slope 0.0 m/m (recorded in
  the declaration; re-derivable via `height_at`).
- Keep the site id `trunk_01`; surface IDs, material provenance and geometry are
  yours to qualify (C15). The spawn-safety proof depends on the footprint bound:
  if your geometry needs a LARGER footprint than 0.5 m, that is a prereg change
  (R_clear derives from it), not a free edit.

### To F05/F07 (later consumers)

- The gentle-terrain envelope is declared and checkable: |∇h| ≤ 0.05 everywhere
  (continuous bound + grid verification); F05 still owes the walking-specific
  slope/friction envelope from evidence.
- F07 places further obstacles INSIDE this extent; the spawn disk (R_clear = 1.5 m
  around the origin) and its construction law are the pattern to follow.

## Integrity paste (git status --porcelain -uall at completion)

```
?? tools/monkey_campaign/agents/F01_clearing/PREREGISTRATION.md
?? tools/monkey_campaign/agents/F01_clearing/brief.md
?? tools/monkey_campaign/agents/F01_clearing/discovery_note.md
?? tools/monkey_campaign/agents/F01_clearing/receipts/determinism_receipt.txt
?? tools/monkey_campaign/agents/F01_clearing/receipts/test_run.txt
?? tools/monkey_campaign/agents/F01_clearing/receipts/validate_receipt.json
?? tools/monkey_campaign/agents/F01_clearing/tests/test_clearing.py
?? tools/monkey_campaign/data/monkey_clearing/clearing_declaration.json
?? tools/monkey_campaign/data/monkey_clearing/clearing_recipe.py
```

All F01-owned paths. The status also shows sibling agents' untracked files
(`agents/P02P03/brief.md`, `agents/U01_input/`, `agents/U02_camera/`) — created by
them, untouched by M-F01. Scratch compiles went to gitignored `.tmp/`. No existing
file was modified; no engine C++ edits; no GPU; no servers launched.

Not committed (coordinator commits agent files, per campaign pattern).
