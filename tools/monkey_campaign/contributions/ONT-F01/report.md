# ONT-F01 — source-bound qualification receipt: the finite clearing and its spatial units

**Verdict: F01's four done_when clauses are qualified against the PINNED
clearing data package, with the `forest` visible_static profile's visual
evidence set produced in this attempt from those pinned bytes verbatim.
Deterministic recipe/declaration re-proven 4/4 byte-identical
(18dd2ff6…); extent strict-`>` shown live on the render/collision oracle
(refusals named `f02_outside_extent` on all four sides, ring extent 20.0 m,
off-edge error 0.0, no invisible wall); safe spawn re-derived
(11.729184690233646 m ≥ 1.5 m) and shown standing ON the rendered surface
(first-hit ground y-error 0.0 at the spawn ray); visible boundary proven with
all 80 posts recovered from the render mesh and all 80 post tops
VISIBLE_EXACT in the frozen overview (zero offset fallbacks); render/collision
correspondence closed numerically at 44 frozen probes over 4 frozen views —
141 probe-views VISIBLE_EXACT (worst height error 8.95e-15 m against a 1e-9
bar; worst incident-normal error 0.0 against 1e-12), 8 correctly
trunk-occluded exactly as the analytic cylinder-silhouette rule predicts, 27
off-frame, ZERO bar breaches anywhere. The falsifier bites demonstrably fail
first (B1 ghost-support +1 cm vertex, B2 post moved 0.5 m →
`f01_boundary_coverage` 1.05 m, B3 mound near spawn →
`f01_mound_spawn_exclusion`, B4 off-frame post top → OFF_FRAME). 26/26
unittest suite; stdlib-only; no engine run, no runtime or training claim.**

- card: `ONT-F01`; attempt `ff6ee7ed079c48a3b3835cd146f89bfd`; arrival
  `arrival-0a0ae1e81d964423a209851494a58215`; criteria sha256
  `cbbcae167a0930f55ba11b7da57a5827013e70e6fbcb0fae8f70c3cd7914e654`;
  scope sha256 `01ea5cddca8d4795caa096945edf7eadcd1f3eb3e2f084fd2ee36a08cae12ef6`;
  planning id F01; calculation contract C01 ("Frames, units and source
  correspondence") independently checked below.
- PREREGISTRATION.md frozen BEFORE candidate code, with disclosed amendments
  A1–A6 (each dated by its section, each motivated by a named smoke-run
  measurement, none after the first full-suite run; A6 replaces a rough
  occlusion heuristic with the EXACT analytic cylinder-silhouette rule, which
  reproduces the measurement precisely).

## Reconcile-first: what already existed and was reused (hashes re-verified in this attempt)

Materialized exclusively from git objects (`git show COMMIT:PATH` — never the
drifted play worktree at `8d16d3c1`, which no longer carries the files), then
re-hashed. All 11 pins verified raw-equal; the R5 three-convention hashes
(raw / lf / crlf) are recorded in `evidence/checks.json`
(`pins_hash_conventions`) and never substituted for raw equality.

| pin | commit | raw sha256 |
|---|---|---|
| clearing_recipe.py | dc7ea811 | ab800d2257655118296519b606c77ddc7116f524ae0c2e6a0bab3b38473892dc |
| clearing_declaration.json | dc7ea811 | 18dd2ff65410cd1cf184a7a8df61c7503a6ce15083f30159e727e9a8117bfbc1 |
| terrain_query.py (F02 oracle) | a2895755 | b1e244b8843671afc29af530c4725bf812ffd5f8967130f0202792aeb7a8cce1 |
| terrain_bundle.py | a2895755 | c6ada25a1b6192aa86add8b09bc19161c0cd81e3fb3d4bd267492660c0be8f2e |
| terrain_bundle.json (13,920 v / 4,640 tris) | a2895755 | 446ed3fbd0f50205c61a7233ceca289bfc3316f76dfc672fec307b20d8305d52 |
| trunk_declaration.json (F03 asset) | dc7ea811 | 94ff906ec5e8b8388e4de318aa3321bad9c791fbb168e8234c371ed1d327e3f1 |
| F01 play receipt report.md | f30f2224 | 9d29bdb8494b4729d8c3a84a2eb9e6f0e282c2eccc94dee278e1e4748e7d8839 |
| gait_controller.hpp (blob 5863348f) | 33e7a444 | f0ffea12795bd47f7c48f5ed9b8aa98869725467d94a1081b1d942f6fba129bd |
| native_collision_brief.json (#120, blob c34ee9b4) | 86d0d8d4 | bc0c723592aff3e3116952b8e647a0c80ada8b011d1d659af8b61b90fccc709d |
| completion_contract.json (ONT-P01) | dce368d7 | 80b2e2f2736ce6fd594633f85fa22bda702991c3ed4d415a0d9c4eadd377163b |
| FOLLOWUP proposed.patch (corrected) | 960a2f55 | b02fc9e65da5459120249d8fd2ec3068818dcd0c43385ffe4331815ac431acb8 |

Dependency verdicts at submission time (registry read 2026-09-27, revision
1099): ONT-P01 **DONE** (PR #127 merge 391f0ede, 2026-09-25T19:35:57Z);
D-FOREST-RUNTIME-20260924 **DONE** (PR #120, specification deliverable only);
D-FOREST-RUNTIME-20260924-FOLLOWUP **DONE** — PR #155 ACCEPTED at be058d58,
then the lead's gap/row CHANGES_REQUIRED corrected by **PR #170, head
960a2f55, merge a16080f9, merged 2026-09-27T00:23:16Z**; both objects were
fetched into this attempt's checkout and verified (merge parents
8567f629 + 960a2f55; the in-tree patch's embedded `terrain_surface.hpp`
is sha256 `24f47dbb…87e2`, byte-identical to the reviewed candidate). The
FOLLOWUP's non-blocking empty-surface note stays carried; nothing here
re-shapes the merged surface law or cites the overstated comment as fact.
Per the R5 correction, all play-lane artifacts are cited as
static/data-package evidence only.

Clause-to-evidence map (done_when → evidence):

1. **Deterministic terrain/tree recipe** — pinned recipe + declaration
   (table above); P1 below re-proves byte-determinism in this attempt; the
   tree asset is F03's declared mesh at F01's site (C01 landmarks below).
2. **Explicit extent and coordinate convention** — declaration convention
   block (right-handed, x=east y=up z=south, metres, origin at scene centre)
   + P3 live extent checks + C01 frame-chain checks.
3. **Safe spawn** — P2 re-derived clearance + P6 spawn-on-surface ray.
4. **Visible boundary** — P7 post recovery/visibility + P5 boundary probes +
   the frames/camera manifest (P8). This was the weakest clause at
   reconciliation (no visible_static evidence existed anywhere for F01) and
   is the bulk of this attempt's new work.

## What this attempt built (nothing re-derived)

`implementation.py` + `test_implementation.py` (stdlib-only) provide:

1. Pin materialization + three-convention hashing (git objects only; refuses
   with `f01_pin_unavailable` + fetch hint when an object is absent).
2. Predictions P1–P8 executed against the pinned bytes.
3. A software rasterizer + raycaster over the pinned render arrays VERBATIM
   (z-buffer, perspective pinhole; presentation shading only — probes never
   read pixels).
4. Frozen falsifier bites (failing-first; `evidence/bites.json` is written
   BEFORE `evidence/checks.json` on every build and the order is recorded in
   it).
5. Camera manifests carrying all 16 profile-required fields for 8 view
   variants (4 views × clean/diagnostic).

## Observed results (exact commands and counts)

Commands (from this directory):

- `python -B implementation.py bites` → all 4 bite.
- `python -B implementation.py build` → `evidence/checks.json`, `all_ok: true`
  (~6 s wall, Python 3.14.3, CPU only).
- `python -B -m unittest test_implementation -v` → **Ran 26 tests … OK**
  (order-independent: passes with `evidence/` deleted first, rebuilt
  26/26 in 6.7 s; passes from a different cwd via `unittest discover`).

- **P1 determinism**: 4/4 recompiles byte-identical to the pinned
  declaration; validation receipt re-derives self-digest `aa2607df…`.
- **P2 gentleness/safety**: spawn clearance 11.729184690233646 m ≥ 1.5 m;
  worst grid slope 0.034606 m/m; worst triangle slope 0.042522289331596436
  at (17, 7); continuous slope bound 0.03795552514626025 ≤ 0.0471; grid ≡
  height-function error 0.0 over all 1,681 points; 5 disjoint mounds; 80
  posts; worst perimeter-to-post gap exactly 1.0 m; worst post off-edge
  error 0.0; trunk site (11.976783, 0.0, 2.471766).
- **P3 extent strict-`>`**: classify(±20, ±20) and (±20 on an edge) =
  inside; (20+1e-6, 0) and (0, −20−1e-6) = outside; height_at refuses
  `f02_outside_extent` on all four sides; ring extent 20.0 ± 1e-6 (the
  visible ring IS the blocking edge — no invisible wall).
- **C01 frame chain**: R = I, det +1; cross(x̂, ŷ) = ẑ; trunk mesh
  world→local→world round-trip worst error 0.0 (bar 1e-12); lateral radius
  law and y-span match the declared base/height within 1e-6; trunk asset
  site equals F01's declaration site exactly; all 80 post bases stand on the
  collision surface within 1e-9.
- **P5 render/collision correspondence** (44 frozen probes × 4 frozen
  views = 176 probe-views): 141 VISIBLE_EXACT, 8 OCCLUDED (exactly the
  silhouette rule's prediction), 27 OFF_FRAME, **0 mismatches**. Worst
  height error 8.951173136040325e-15 m (bar 1e-9); worst incident-normal
  error 0.0 (bar 1e-12); worst trunk radial error 6.83e-8 m (bar 5e-6);
  worst trunk face-normal angle 0.09823296 rad ≤ declared bound
  π/32 + 5e-4 (A5 derivation: 2·√2·q/chord, chord = 2·R·sin(π/32)).
- **P6 spawn on the surface**: straight-down ray at (0,0) first-hits
  `monkey_clearing_ground` at y-error 0.0 vs the oracle height;
  collision.same_arrays_as_render = true — no ghost support.
- **P7 boundary visibility**: 80/80 posts recovered from the mesh's
  `monkey_clearing_boundary_posts` section (4,320 vertices), 80/80 post tops
  VISIBLE_EXACT in the overview, 0 offset fallbacks needed.
- **P8 frames/manifest**: 12 BMPs (4 views × clean + diagnostic, plus 4
  depth maps; each 1,280×720, 2,764,854 bytes; sha256s recorded in
  `evidence/checks.json` and re-hashed below); camera manifest with exactly
  the 16 required fields for all 8 view variants; 15 stable 3D labels
  (spawn, trunk_01, 4 corners, 4 edge midpoints, 5 mounds) with projected
  pixels and per-view in-frame flags.

Frame sha256 (first 16 hex, full values in checks.json):
V1 clean b4aab2898a01afd9, V1 diagnostic 2d6005624f0d0229, V2 clean
1570caddef964bd9, V2 diagnostic 415934e9506a97e7, V3 clean 5e8eea291b264a26,
V3 diagnostic ba9432f2102e701c, V4 clean eb5c5d7eaa6e9824, V4 diagnostic
ee7d7c96a0ac2f61, depth maps 130c5a26f0a2f782 / e9ed8da15b0d85ba /
4eb25c122eced056 / b5dbcbd15ac7586c.

## Falsifier bites (failing-first, recorded before the pinned pass)

- **B1 ghost support**: +0.01 m on one ground vertex of a bundle copy (with
  that triangle's stored normals recomputed so the COPY loads clean — the
  hygiene gate is not the thing under test) → the probe ray at the tampered
  triangle's centroid no longer first-hits the collision-surface point
  (outcome OCCLUDED-by-nearer-mismatched-surface; B1's loads_clean: true and
  the pinned oracle height are recorded). The P5 machinery demonstrably
  detects rendered/collision divergence; it is not tag-based.
- **B2 missing boundary**: one post moved 0.5 m inward →
  `f01_boundary_coverage` refusal at 1.05 m.
- **B3 unsafe spawn**: mound re-centred at (2, 2) →
  `f01_mound_spawn_exclusion` refusal.
- **B4 off-frame**: the SW corner post top required visible in the seam
  close-up (155.7° off-axis, behind the camera) → OFF_FRAME.

## Amendments A1–A6 (all disclosed before the first full-suite run)

A1 trunk/seam probe geometry after occlusion analysis; A2 corrected B4 (the
NE corner is 37.2° off-axis — inside V2's frustum; the classifier was right,
the frozen assumption wasn't) after a bites-only smoke run; A3 node-normal
sets (the piecewise-linear surface is C1-discontinuous at grid nodes by the
frozen diagonal rule; heights continuous, normals are a SET) + declared
32-segment trunk polygonal law + a C01 span-check implementation bug fix;
A4/A5 trunk angular bar derived from the declared vertex quantization
(A5 supersedes A4: bound = π/32 + 5e-4 rad from 2·√2·q/chord); A6 exact
cylinder-silhouette occlusion rule replacing A1's hemisphere heuristic
(computed silhouette distances 0.02565/0.01137 occluded; 0.04209/0.05/0.04835
visible — reproduces the measurement exactly).

## Honest boundary (absent components inventoried explicitly)

This is STATIC-scene qualification of the pinned data package plus an
attempt-local render of those bytes. NOT claimed: engine run or HTTP
load_mesh exercise; native collision query route (#120 S1-3); engine-side
render upload (#120 S1-4); engine walk replay or playable-build acceptance;
trunk contact subsystem (Stage 2); training or runtime acceptance; W10 scene
readiness. Downstream owners: the #120/#155 seam cards own S1-3/S1-4; F02
owns render/query tolerance work; F03 owns trunk geometry qualification; F04
owns contact dynamics. Component-complete framing per DELIVERY.md: the
existing downstream integration task IDs are D-FOREST-RUNTIME cards (S1-1…
S1-6) and ONT-F02/F03/F04; required ports: `surface_query(x_m,z_m) →
{h_m,gx,gz,inside}` (S1-1 io_contract) and the S1-4 render upload of
`terrain_bundle.json`; unresolved blockers: those stages. The rasterizer
here is evidence tooling, not the engine render path.

## Suite

`python -B -m unittest test_implementation -v` — 26 tests, OK, order- and
cwd-independent. `python -B implementation.py build` regenerates all
evidence deterministically (bites first, pinned pass second).
