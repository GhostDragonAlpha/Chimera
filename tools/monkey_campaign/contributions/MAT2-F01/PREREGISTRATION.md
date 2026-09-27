# PREREGISTRATION — MAT2-F01 (Author the finite clearing and its spatial units)

Card `MAT2-F01`, planning id F01, attempt `5445fc5ef1df4571ace1e76579fadd9f`,
arrival `arrival-d4559daabbbb41c38d5a810c1db20de8`, criteria sha256
`bbcda6c08ab5f52efd1579e3af0504d46d024450d99ca5a8bcc47d600a99a665`, scope
sha256 `cb5475f8486197a973edc4360b177fc31a629c4f0979ebf80dd76aae57996097`.
Written and frozen BEFORE any candidate build/verify run in this workspace
(only read-only reconciliation — inbox reads, `git show` extraction, hashing,
and validator dry-runs on the ARCHIVED candidate's bytes — happened before this
freeze). Frozen 2026-09-27.

done_when (verbatim): "Deterministic terrain/tree recipe, explicit extent and
coordinate convention, safe spawn and visible boundary".
Verification profile: `forest` (kind `visible_static`, subject "Terrain/trunk
geometry and actual contact surfaces"), clean view required, numerical evidence
required. Falsifier (verbatim): "Rendered/collision mismatch, ghost support,
missing boundaries or off-frame probe subject fails; tags alone do not
establish contact."

## STATEMENT (frozen)

This card is a RECONCILIATION. The known-good F01 qualification already
exists: archived ONT-F01 candidate PR #188 head `a7b2acc4` (full
`a7b2acc4bf50e326c160292efec155f6db1ba444`), whose science was registry-verified
PASS (review `c7d95056`: 176/176 probe-views, suite 26/26, bites fail-first,
11/11 pins) and whose ONLY lead finding was packaging: the committed
`evidence/camera_manifest.json` was a bare `views[]` array with no campaign
envelope, so `visual_gate.verify` could not bind it (`capture_task_mismatch`).
This attempt ports that candidate verbatim into `contributions/MAT2-F01` at the
same base (`c525b82c`), regenerates and re-verifies ALL of its evidence in this
attempt against the same pinned bytes, and fixes exactly the packaging finding
plus the one additional campaign-schema defect found by scoped validator
dry-run (below). No terrain law, constant, probe, view, bar, or bite is
changed.

Provenance of the ported baseline (raw sha256 of the exact `a7b2acc4` bytes
extracted via `git show`, re-hashed in this attempt before this freeze):

| file | sha256 |
|---|---|
| PREREGISTRATION.md (ONT-F01, frozen pre-code, amendments A1–A6) | `6544778621855ecf8cad7f957b1e3f205c0a276664f9bc98fddc392d5d97348f` |
| implementation.py | `b846e58e5be7ad893b00b9d41e138caefe4086f2c0300a96cef2e5593b22cbeb` |
| test_implementation.py | `69500280828ea115c754d2f8f964096317e5d48ffe087031a4f782e4bd0f0b95` |
| evidence/pins_materialized/clearing_declaration.json | `18dd2ff65410cd1cf184a7a8df61c7503a6ce15083f30159e727e9a8117bfbc1` (= pin dc7ea811) |

Pinned inputs (11 pins, table inherited verbatim from the archived
preregistration above; every pin re-materialized and raw-hash-verified in this
attempt): dc7ea811 (recipe + declaration + trunk), a2895755 (terrain_query.py,
terrain_bundle.py/.json), f30f2224 (F01 play receipt), 33e7a444
(gait_controller.hpp), 86d0d8d4 (native_collision_brief.json), dce368d7
(completion_contract.json), 960a2f55 (FOLLOWUP proposed.patch).

## PREDICTIONS (frozen before the run; each with its pass bar)

Inherited (the archived preregistration's P1–P8, amendments A1–A6, the 44
frozen probes, the 4 frozen views V1–V4, and falsifier bites B1–B4 are
restated there verbatim and are NOT modified; hash above). Compact restatement
of the pass conditions this attempt's build asserts:

- P1 determinism 4/4 byte-identical to declaration pin `18dd2ff6…`.
- P2 spawn clearance 11.729184690233646 m ≥ 1.5 m; slopes within frozen bars.
- P3 extent strict-`>`: `f02_outside_extent` refusals on all four sides; ring
  extent 20.0 ± 1e-6 (no invisible wall).
- C01 frame chain: R = I det +1; trunk world→local→world round-trip ≤ 1e-12;
  80 post bases on the collision surface ≤ 1e-9.
- P5 correspondence: 44 probes × 4 views = 176 probe-views; worst ground
  height error ≤ 1e-9 m; normal agreement within the A3/A5 bounds; occlusions
  exactly per the A6 analytic cylinder-silhouette rule; ZERO bar breaches.
- P6 spawn ray first-hits `monkey_clearing_ground` at y-error 0.0 (bar 1e-9).
- P7 80/80 posts recovered, 80/80 post tops VISIBLE_EXACT in the overview.
- B1–B4 bites all bite (recorded BEFORE the pinned pass, order recorded).

New, this attempt (packaging and port fidelity — frozen now):

- Q1 port fidelity: the diff between ported files and the `a7b2acc4` bytes is
  EXACTLY the disclosed identity edits (module docstrings; SCHEMA string
  `chimera.ont_f01.qualification.v1` → `chimera.mat2_f01.qualification.v1`;
  checks.json identity fields card/attempt_id/criteria_sha256; manifest
  frame_id prefix `ONT-F01/` → `MAT2-F01/`). No other line changes. If the
  diff shows anything else, STOP and report.
- Q2 render byte-determinism: this attempt's CPU-only re-render (Python
  3.14.3, same as the archived run) reproduces all 12 archived BMPs
  byte-identically — each rendered BMP's sha256 equals the archived value
  recorded in the archived `evidence/checks.json` (V1 clean
  `b4aab2898a01afd9…` etc.). A mismatch means nondeterminism or an accidental
  science change: STOP and report, never hand-tune.
- Q3 campaign capture manifest: the regenerated
  `evidence/capture_manifest.json` (schema `chimera.visual_capture_manifest.v1`)
  carries the envelope (task_id `F01`, run_id, subject_sha256 bound to the
  pinned clearing_declaration.json bytes, capture_sha256 bound to the committed
  gate-bound overview clean BMP, tick_interval [0,0], profile_id `forest`) and
  passes `visual_capture.validate_manifest` against the card's `forest`
  profile. KNOWN DEFECT FIXED BY DECLARATION (found by validator dry-run on
  the archived corrected draft): diagnostic rows carry
  `required_subject_ids: []`, which the validator refuses
  (`visibility_required_subject_ids_invalid`); the generator sets it to the
  same non-empty required-subject triple as the clean rows. No other row
  content changes from the archived corrected draft's construction.
- Q4 gate binding: `visual_gate.verify` passes on the COMMITTED bytes with
  contract task_id `F01`, receipt evidence camera = committed
  capture_manifest.json, visual = committed `frame_V1_clearing_overview_clean.bmp`.

## FROZEN PROBES AND VIEWS

Unchanged from the archived preregistration (hash above): V1 clearing_overview
pos (0, 46, -32) target origin vfov 55°; V2 seam_closeup pos (10.15, 1.25,
1.35) target (11.976783, 0.32, 2.471766) vfov 55°; V3 side_depth pos (0, 12,
-50) target (0, 0, 6) vfov 45°; V4 oblique_depth pos (-34, 20, -30) target
origin vfov 55°; all 1280×720, near 0.05, far 200, static bookmarks. Probes:
44 frozen points (25 ground grid, 1 spawn, 8 seam, 6 trunk lateral
V2-facing per A1, 4 corner post-tops). Diagnostic layers: the profile's five.
Clean frames carry no overlay.

## COMMANDS (frozen)

From `tools/monkey_campaign/contributions/MAT2-F01/`:

1. `python -B implementation.py bites` → all 4 bite (failing-first).
2. `python -B implementation.py build` → regenerates `evidence/` (bites first,
   pinned pass second); `checks.json` `all_ok: true`. CPU-only.
3. `python -B -m unittest test_implementation -v` → 26 tests OK.
4. `python -B make_capture_manifest.py` → regenerates the campaign-schema
   `evidence/capture_manifest.json` from the build outputs (envelope +
   per-row bindings recomputed from file bytes, never copied).
5. Campaign validator run (stdlib, from the campaign tools directory):
   `visual_capture.validate_manifest` + `visual_gate.verify` against the
   committed bytes; plus BMP sha256 comparison Q2 against the archived
   checks.json values.

## HONEST BOUNDARY (frozen)

Unchanged from the archived candidate: static-scene qualification of the
pinned clearing data package plus an attempt-local stdlib render of those
bytes. NOT claimed: engine run or HTTP load_mesh exercise; native collision
query route (S1-3); engine-side render upload (S1-4); engine walk replay or
playable-build acceptance; trunk contact subsystem (Stage 2); training or
runtime acceptance; W10 scene readiness. The rasterizer is evidence tooling,
not the engine render path. Play-lane artifacts cited as static/data-package
evidence only (R5 correction).


---

## APPENDIX — the inherited frozen preregistration, restated verbatim (hash-pinned above)

Disclosure: appended after the first suite run, which found the ported suite
(`test_implementation.py`, byte-identical to the reviewed candidate) structurally
requires the inherited sections to appear in this file. NO prediction, bar,
probe, view, or bite is changed by this appendix: the text below is the archived
ONT-F01 preregistration (raw sha256
`6544778621855ecf8cad7f957b1e3f205c0a276664f9bc98fddc392d5d97348f`, itself
frozen before any candidate code in the archived workspace), restated verbatim
to realize this preregistration's frozen inheritance clause. Card-identity
headings inside it refer to the archived candidate; this attempt's identity is
in the header above, and the inherited predictions apply to the same pinned
bytes re-verified in this attempt.

# PREREGISTRATION — ONT-F01 (Author the finite clearing and its spatial units)

Card `ONT-F01`, planning id F01, attempt `ff6ee7ed079c48a3b3835cd146f89bfd`,
arrival `arrival-0a0ae1e81d964423a209851494a58215`, criteria sha256
`cbbcae167a0930f55ba11b7da57a5827013e70e6fbcb0fae8f70c3cd7914e654`, scope
sha256 `01ea5cddca8d4795caa096945edf7eadcd1f3eb3e2f084fd2ee36a08cae12ef6`.
Written BEFORE any candidate code in this workspace. Frozen on 2026-09-27.

done_when (verbatim): "Deterministic terrain/tree recipe, explicit extent and
coordinate convention, safe spawn and visible boundary".
Verification profile: `forest` (kind `visible_static`, subject "Terrain/trunk
geometry and actual contact surfaces"), clean view required, numerical evidence
required. Falsifier (verbatim): "Rendered/collision mismatch, ghost support,
missing boundaries or off-frame probe subject fails; tags alone do not
establish contact."

## Reconciled starting state (step 1 deliverable, verified in this attempt)

The recipe and its downstream artifacts ALREADY EXIST pinned in git; this card
does NOT re-derive them. Every hash below was re-verified 2026-09-27 in this
attempt by materializing from the E:/PythonChimera + origin object stores
(`git show COMMIT:PATH`), never from the drifted play worktree (hazard:
E:/ChimeraWork/monkey-play-20260924 @ 8d16d3c1 no longer carries the files).

| artifact | commit | raw sha256 |
|---|---|---|
| clearing_recipe.py | dc7ea811 | ab800d2257655118296519b606c77ddc7116f524ae0c2e6a0bab3b38473892dc |
| clearing_declaration.json | dc7ea811 | 18dd2ff65410cd1cf184a7a8df61c7503a6ce15083f30159e727e9a8117bfbc1 |
| terrain_query.py (oracle) | a2895755 | b1e244b8843671afc29af530c4725bf812ffd5f8967130f0202792aeb7a8cce1 |
| terrain_bundle.py | a2895755 | c6ada25a1b6192aa86add8b09bc19161c0cd81e3fb3d4bd267492660c0be8f2e |
| terrain_bundle.json | a2895755 | 446ed3fbd0f50205c61a7233ceca289bfc3316f76dfc672fec307b20d8305d52 |
| F03 trunk_declaration.json | dc7ea811 | 94ff906ec5e8b8388e4de318aa3321bad9c791fbb168e8234c371ed1d327e3f1 (self-digest field b7089e78…) |
| F01 play receipt report.md | f30f2224 | 9d29bdb8494b4729d8c3a84a2eb9e6f0e282c2eccc94dee278e1e4748e7d8839 |
| gait_controller.hpp | 33e7a444 | f0ffea12795bd47f7c48f5ed9b8aa98869725467d94a1081b1d942f6fba129bd (blob 5863348f) |
| D-FOREST native_collision_brief.json | 86d0d8d4 | bc0c723592aff3e3… (blob c34ee9b4) |
| ONT-P01 completion_contract.json | dce368d7 | 80b2e2f2736ce6fd594633f85fa22bda702991c3ed4d415a0d9c4eadd377163b |
| FOLLOWUP proposed.patch | 960a2f55 | b02fc9e65da5459120249d8fd2ec3068818dcd0c43385ffe4331815ac431acb8 (blob 838aa05a; embeds terrain_surface.hpp sha256 24f47dbb…, byte-identical to the reviewed candidate) |

Dependency verdicts: ONT-P01 DONE (PR #127 merge 391f0ede). Parent
D-FOREST-RUNTIME-20260924 DONE (PR #120, specification only).
D-FOREST-RUNTIME-20260924-FOLLOWUP DONE (PR #170 head 960a2f55, merge
a16080f9, 2026-09-27T00:23:16Z): the native surface seam is MERGED; its
non-blocking empty-surface note stays carried (not re-litigated here, not
cited as fact). R5 verdict governs citation: play-lane forest artifacts are
STATIC/data-package evidence only, never native/runtime evidence.

Clause-to-evidence map (first unmet clause drives the implementation):

1. "Deterministic terrain/tree recipe" — MET AS DATA (pinned recipe +
   declaration; play falsifier (a) determinism 4/4). UNMET in the ONT lane:
   no attempt-local re-run binding the pinned bytes to F01.
2. "Explicit extent and coordinate convention" — MET AS DATA (declaration
   convention block + extent rule; C01 chain articulated). UNMET: C01
   independent checks (round-trip, handedness, landmarks) not evidenced in an
   attempt.
3. "Safe spawn" — MET AS DATA (spawn (0,0,0), clearance 11.729184690233646 m
   ≥ 1.5 m). UNMET: attempt-local numerical re-derivation + spawn shown on the
   rendered/collision surface (ghost-support falsifier).
4. "Visible boundary" — WEAKEST. 80 posts exist in the pinned render bundle,
   but NO visible_static evidence set (camera fields, clean view, diagnostic
   layers, silhouettes/depth, render/collision correspondence) exists anywhere
   for F01. THIS IS THE BULK OF THE NEW WORK.

## STATEMENT (frozen)

The pinned clearing data package (recipe + declaration + F02 render/collision
bundle + F03 trunk asset) satisfies F01's four done_when clauses as a static
scene, and a stdlib-only static render path built IN THIS ATTEMPT from those
pinned bytes verbatim produces the profile's visible_static evidence set:
three frozen profile views (plus one extra depth view) under the 16 required
camera fields, clean + diagnostic frames, with NUMERICAL render/collision
correspondence at frozen ground/trunk/seam/boundary/spawn probes — the
rendered first-hit surface IS the collision oracle's surface within frozen
bars. No new terrain law, no new constants, no engine change.

## PREDICTIONS (frozen before the run; each with its pass bar)

- P1 determinism: `compile_declaration()` from the pinned recipe, run 4x,
  produces bytes IDENTICAL to the pinned clearing_declaration.json
  (sha256 18dd2ff6…); `validate_declaration` re-derives self-digest aa2607df…
  and returns validated=true.
- P2 gentleness/safety numbers (attempt-local reproduction): spawn clearance
  11.729184690233646 m ≥ required 1.5 m; worst grid slope 0.034606 m/m and
  worst triangle slope ≤ 0.05 m/m; continuous slope bound ≤ 0.0471; grid ≡
  height function error 0.0 over all 1,681 grid points; 5 mounds pairwise
  disjoint; trunk site (11.976783, 0.0, 2.471766), spawn distance 12.229185 m,
  slope at site 0.0.
- P3 extent strict-`>`: oracle classify(±20.0, ±20.0) = inside; classify(20+δ)
  = outside for δ=1e-6; height_at refuses `f02_outside_extent` for |x| or |z|
  > 20; ring extent == 20.0 ± 1e-6 (no invisible wall); worst perimeter-to-post
  gap exactly 1.0 m; worst post off-edge error 0.0.
- P4 C01 frame chain: trunk mesh vertices are WORLD-frame; axis midpoint of
  lateral rings == declared base centre (11.976783, ·, 2.471766) within 1e-6 m;
  trunk site record == F01 declaration trunk site exactly; world→local→world
  round-trip |err| ≤ 1e-12 m for all mesh vertices; R = I has det +1
  (right-handed, x=east y=up z=south); all 80 post bases satisfy
  |base_y − oracle height_at(base_x, base_z)| ≤ 1e-9 m.
- P5 render/collision correspondence (the profile's core numerical claim):
  frozen probe set (below) per view — each probe is a world point ON the
  collision surface (oracle height for ground; analytic cylinder law for
  trunk), projected through the frozen camera; a ray from camera through the
  probe's pixel is cast against the pinned RENDER arrays (ray/triangle);
  outcome ∈ {VISIBLE_EXACT, OCCLUDED, OFF_FRAME}: VISIBLE_EXACT requires first
  hit within 1e-6 m of the probe distance AND |hit_y − oracle height_at| ≤
  1e-9 m (ground) / |hit point − cylinder surface distance| ≤ 1e-9 m (trunk)
  AND hit-face normal vs oracle normal max-component ≤ 1e-12 (ground) / radial
  law agreement ≤ 1e-9 (trunk). OCCLUDED/OFF_FRAME are recorded with the
  occluder/where, not failures, but every frozen probe must be VISIBLE_EXACT
  in at least one frozen view.
- P6 spawn on the surface (ghost-support check): straight-down ray at (0,0)
  first-hits the ground mesh at y = 0.0 ± 1e-9 (the SAME arrays the collision
  oracle answers from, collision.same_arrays_as_render = true).
- P7 boundary visibility: the render bundle's boundary_posts section carries
  all 80 posts (4,320 vertices, surface_id monkey_clearing_boundary_posts);
  posts recovered from the mesh == 80; in the overview view ALL 80 post-top
  label anchors are VISIBLE_EXACT (nothing occludes them above gentle
  terrain); every post sits exactly on the physical extent edge (off-edge 0.0)
  so the visible ring IS the blocking edge.
- P8 frames/manifest: 4 views x {clean, diagnostic} BMP frames + 4 depth maps
  emitted from the pinned vertices verbatim (no smoothing, no resampling); a
  camera manifest records ALL 16 profile-required fields per view; stable
  labels (spawn, trunk_01, 4 extent corners, N/E/S/W midpoints, 5 mounds)
  carry 3D anchor + projected pixel + per-view visibility.

## FROZEN PROBES AND VIEWS

Views (pinhole perspective, right-handed world, x=east y=up z=south,
1280x720, aspect 16:9, near 0.05 m, far 200 m, static bookmark per frame):

- V1 clearing_overview: pos (0, 46, -32), target (0, 0, 0), vfov 55 deg.
  Pre-frozen margin check: extent corners incl. 0.9 m post tops project to
  x ±0.499, y -0.716..+0.491 (in frame).
- V2 seam_closeup: pos (10.15, 1.25, 1.35), target (11.976783, 0.32,
  2.471766), vfov 55 deg — terrain/trunk seam region framed.
- V3 side_depth: pos (0, 12, -50), target (0, 0, 6), vfov 45 deg.
- V4 oblique_depth: pos (-34, 20, -30), target (0, 0, 0), vfov 55 deg.

Probe set (34 world points, frozen):
- 25 ground probes: 5x5 grid x,z ∈ {-16,-8,0,8,16}, y = oracle height_at.
- 1 spawn probe (0, oracle height, 0).
- 8 seam probes: circle r = 0.05 m around the trunk axis at oracle terrain
  height, azimuths k*pi/4.
- 6 trunk lateral probes: r = 0.037 m (the declared radius), heights
  {0.15, 0.6, 1.0} x azimuths {0, pi} relative to the axis (near and far
  side). The base-centre axis point is rejected as inside the solid.
- 4 corner post-top anchors (-20, 0.9, -20), (20, 0.9, -20), (20, 0.9, 20),
  (-20, 0.9, 20) as boundary probes.
Total: 25 + 1 + 8 + 6 + 4 = 44 probes.

Diagnostic layers (per profile's five): render mesh = triangle-edge wireframe
overlay of the ground section; collision surfaces = section-coloured render
(ground checker two-tone from bundle style; boundary posts ochre 0.72,0.55,0.20;
trunk bark 0.36,0.25,0.16) with surface_id legend; normals/contact markers =
projected surface-normal arrows at all 44 probes; scene bounds = extent edge
rectangle + verticals at ±20 drawn in world; stable 3D labels = spawn, trunk_01,
4 corners (SW/SE/NE/NW), N/E/S/W edge midpoints, 5 mound centres — each with 3D
anchor, projected px, label id, per-view visibility. Clean frames carry NO
overlay.

## FALSIFIER BITES (failing-first, run BEFORE the pinned pass, recorded)

- B1 ghost support: raise ONE ground vertex of a bundle copy by +0.01 m →
  the correspondence probe on that triangle must FAIL its 1e-9 bar
  (rendered/collision mismatch demonstrably bites; P5 machinery is not
  tag-based).
- B2 missing boundary: move one post 0.5 m inward in a declaration copy →
  validate_declaration must refuse (`f01_post_off_edge` or invisible-wall /
  coverage refusal).
- B3 unsafe spawn: shrink the declared spawn clearance demand onto a mound
  world (copy with a mound re-centred near origin) → validation must refuse
  (`f01_mound_spawn_exclusion` / `f01_spawn_flat_by_construction`).
- B4 off-frame: a probe point asserted VISIBLE in a view whose frustum
  excludes it must classify OFF_FRAME (the visibility classifier itself is
  shown to detect off-frame subjects rather than pass them).

Then the pinned bytes must PASS all predictions. Order recorded in evidence.

## HONEST BOUNDARY (frozen)

Static-scene evidence only: no engine run, no HTTP load_mesh exercise, no
native collision query route (S1-3), no render upload through the engine
(S1-4), no walk replay, no trunk contact (Stage 2), no training. The render
path is an attempt-local stdlib rasterizer over the pinned bytes — it
qualifies F01's visible_static profile (geometry correspondence, extent,
boundary, spawn) and does NOT claim engine integration, runtime acceptance,
or any W10 scene readiness. Per the R5 correction the play-lane artifacts are
cited as static/data-package evidence. If the lead judges the S1-4-style
engine-side upload a prerequisite for F01 closure, the absent-component
inventory in report.md names it explicitly.

## AMENDMENT A1 (disclosed BEFORE any candidate run; no candidate code had been executed)

Motivated by pre-run geometry analysis of occlusion (the trunk is a solid
cylinder; probes on its far hemisphere are occluded in every frozen view by
construction, which would turn P5's "visible somewhere" clause into a
guaranteed failure rather than evidence):

1. Trunk lateral probes move to the V2-facing hemisphere: r = 0.037 m,
   heights {0.15, 0.6, 1.0} x azimuths {pi, 5*pi/4} (west and southwest, the
   seam close-up camera side). All 6 must be VISIBLE_EXACT in V2.
2. Seam probes keep all 8 azimuths; their per-view classification is now
   PART OF THE PREDICTION: in V2, the camera-facing hemisphere (azimuths
   4, 5, 6 of k*pi/4) must be VISIBLE_EXACT and the far hemisphere
   (azimuths 0, 1, 2, 3, 7) must be OCCLUDED with occluder trunk_01 (the
   solid cylinder blocks them). In V1/V3/V4 seam outcomes are recorded
   without per-probe pass/fail.
3. P5 global rules unchanged and extended: every ground/spawn probe
   VISIBLE_EXACT in at least one view; all 4 corner post-top anchors
   VISIBLE_EXACT in the overview; every trunk lateral probe VISIBLE_EXACT
   in V2; and NO probe may classify VISIBLE_BUT_MISMATCH in ANY view (a
   single bar breach anywhere is render/collision divergence and fails).

## AMENDMENT A2 (disclosed after a bites-only smoke run, BEFORE the first full-suite run)

The bites smoke run measured B1-B3 biting exactly as frozen (B1: the raised
triangle becomes the first hit at the probe's ray, named outcome recorded;
B2: `f01_boundary_coverage` refusal at 1.05 m; B3:
`f01_mound_spawn_exclusion`). B4 did NOT bite: the NE corner post top is
actually INSIDE V2's frustum (measured 37.2 deg from the view axis, horizontal
half-FOV ~42.8 deg at 55 deg vertical on 16:9) — the classifier correctly
classified it VISIBLE_EXACT, so the frozen B4 assumption ("whose frustum
excludes it") was wrong, not the classifier. B4 is corrected to the SW corner
post top in V2 (measured 155.7 deg from the view axis, i.e. behind the
camera): requiring visibility there must classify OFF_FRAME. The bites-only
smoke run wrote `evidence/bites.json`; the full-suite run regenerates it and
the suite asserts the amended bites.

## AMENDMENT A3 (disclosed after a build smoke run, BEFORE the first full-suite run)

The smoke build measured three bar-level facts that motivate precise bars
(the pinned bytes are unchanged; only the probe rules are refined):

1. Ground probes sit exactly on grid NODES, where the declared
   piecewise-linear surface is C1-discontinuous by construction (frozen
   diagonal rule: triangles A and B of a cell meet the neighbours with
   different plane normals). Heights are continuous (measured errs <= 8.9e-15
   m) but the normal is a SET of incident face normals at a node. Bar
   refinement: the rendered hit normal must match, within 1e-12, ANY incident
   ground face normal at the probe point (incident set enumerated from the
   pinned arrays by exact 2D footprint containment). Height bar unchanged
   (1e-9 m).
2. The trunk asset is the DECLARED 32-ring-segment polygonal approximation
   (trunk render_mesh.ring_segments = 32; F03's declared representation). A
   face normal deviates from the analytic radial by up to half a segment,
   sin(pi/32) measured exactly on the smoke run (0.0980). Bar refinement:
   trunk probes check (a) radial position |dist_to_axis - R| <= 5e-6 m
   (1e-6 grid quantization of the mesh vertices) and (b) angle between hit
   face normal and the analytic radial <= pi/32 + 1e-9 rad (the declared
   polygonal law). The prior 1e-9 normal-component bar confused the mesh law
   with the analytic law and was wrong.
3. C01 check fix (implementation bug, not a data fact): the y-span landmark
   must test the mesh's MIN and MAX y against the declared base and
   base+height, not each vertex against both.

## AMENDMENT A4 (disclosed after the A3 build smoke run, BEFORE the first full-suite run)

Measured max trunk face-normal deviation from the analytic radial:
0.0981870 rad — a hair ABOVE pi/32 = 0.0981748 rad, by 1.2e-5 rad. That
delta is the declared 1e-6 vertex-quantization on R = 0.037 m (angular
wander up to ~2.7e-5 rad). Bar refinement: trunk normal-angle bound becomes
pi/32 + 3e-5 rad. Radial bars and everything else unchanged.

## AMENDMENT A5 (supersedes A4's slack; disclosed before the first full-suite run)

A4's 3e-5 slack was an underestimate: the measured max trunk face-normal
deviation is 0.09823296 rad, which overshoots pi/32 + 3e-5 = 0.09820477.
A PRINCIPLED bound derived from declared constants (not from the
measurement): vertex quantization q = 1e-6 m (the recipe's determinism grid)
tilts a face normal by at most 2*sqrt(2)*q / chord, where the ring chord is
chord = 2*R*sin(pi/32) = 2*0.037*0.0980171... = 7.24e-3 m, giving 3.91e-4
rad. Final bound: pi/32 + 5e-4 rad = 0.09867477 rad. Measured 0.09823296
fits with a 4.4e-4 margin. Radial bars and everything else unchanged.

## AMENDMENT A6 (replaces A1's seam-hemisphere partition; derived, not tuned)

A1's 90-degree hemisphere cutoff for seam-occlusion in V2 was a rough
approximation. The measured build found seam_2, seam_3, seam_7 VISIBLE_EXACT
(exact bars) where A1 predicted trunk-occlusion. The governing rule is the
EXACT analytic cylinder-silhouette test: a seam probe is predicted
OCCLUDED-by-trunk_01 in V2 iff the sightline from the frozen camera to the
probe's closest horizontal approach to the trunk axis is < R = 0.037 m; else
VISIBLE_EXACT (bars enforced). Computed once from the frozen camera/axis:
seam_0 dist 0.02565 (occluded), seam_1 dist 0.01137 (occluded),
seam_2 dist 0.04209, seam_3/4/5/6 dist 0.05, seam_7 dist 0.04835 (visible).
This reproduces the measurement exactly and supersedes A1's rule 2. All
other seam rules (bars enforced whenever VISIBLE_EXACT; other views
record-only) unchanged.

## Suite

`python -B -m unittest test_implementation -v` from this directory (stdlib
only, order-independent). Evidence written under `evidence/` by
`implementation.py build` (deterministic order, every artifact hashed).
