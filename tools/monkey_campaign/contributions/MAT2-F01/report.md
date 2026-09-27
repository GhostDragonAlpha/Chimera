# MAT2-F01 — source-bound qualification receipt: the finite clearing and its spatial units

**Verdict: RECONCILED AND RE-VERIFIED. F01's four done_when clauses are
qualified by the registry-verified ONT-F01 candidate (PR #188 head `a7b2acc4`,
PASS review `c7d95056`), which this attempt ported to `contributions/MAT2-F01`
with identity-string-only changes (Q1 diff audited), re-executed in full
against the same pinned bytes (bites 4/4 fail-first, build `all_ok: true`,
suite 26/26, pins 11/11 raw-equal, P5 correspondence 141 VISIBLE_EXACT / 8
OCCLUDED / 27 OFF_FRAME over 176 probe-views with ZERO bar breaches), and
re-rendered byte-identically: all 12 committed BMPs hash EQUAL to the archived
candidate's committed blobs (Q2, 12/12) — this attempt's visual evidence IS
the reviewed pixels. The archived candidate's sole lead finding (capture
manifest was a bare `views[]` array, unbindable: `capture_task_mismatch`) is
fixed: `evidence/capture_manifest.json` now ships in campaign schema
`chimera.visual_capture_manifest.v1` with the full identity envelope and PASSES
`visual_capture.validate_manifest` and `visual_gate.verify` on the committed
bytes (Q3, Q4). CPU-only (Python 3.14.3); no engine run; no runtime or
training claim.**

- card: `MAT2-F01`; attempt `5445fc5ef1df4571ace1e76579fadd9f`; arrival
  `arrival-d4559daabbbb41c38d5a810c1db20de8`; criteria sha256
  `bbcda6c08ab5f52efd1579e3af0504d46d024450d99ca5a8bcc47d600a99a665`; scope
  sha256 `cb5475f8486197a973edc4360b177fc31a629c4f0979ebf80dd76aae57996097`;
  planning id F01; base revision `c525b82c7c3ce0128565424764293a3c85811ab3`
  (branch-1, same base as the archived candidate); calculation contract C01
  independently checked (below).
- PREREGISTRATION.md (this directory) frozen BEFORE any build/verify run in
  this workspace; it inherits the archived ONT-F01 preregistration
  (raw sha256 `6544778621855ecf8cad7f957b1e3f205c0a276664f9bc98fddc392d5d97348f`,
  amendments A1–A6) verbatim and adds packaging predictions Q1–Q4. One
  disclosed appendix realizes the inheritance clause after the first suite
  run (no prediction changed; motivated by the ported suite's structural
  check of PREREGISTRATION.md).

## Reconcile-first: the archived work reused (why nothing was re-implemented)

Read before any write: task inbox (empty), legacy `R5-forest-review` and
`R5-forest-review-FOLLOWUP` (HISTORICAL_SCOPE_READ_ONLY), and the archived
`ONT-F01` card (CHANGES_REQUESTED) whose lead review is the governing finding:

> "The committed evidence/camera_manifest.json is a bare views[] array with NO
> campaign envelope … visual_gate.verify cannot bind it (capture_task_mismatch
> …). CORRECTION: regenerate camera_manifest.json in the campaign capture
> schema … keep the verified per-view camera records, add the envelope with
> task_id F01, a run_id, subject_sha256 bound to the state snapshot,
> capture_sha256 bound to the committed capture sheet BMP, and the tick
> interval … No science, probe, suite, or BMP changes."

The archived candidate's science had already been registry-verified PASS
(review `c7d95056`: 176/176 probe-views, suite 26/26, bites fail-first,
11/11 pins). Per the card's reconcile-first discipline this attempt reuses
that work instead of reimplementing it. Provenance of the ported baseline
(exact `a7b2acc4` bytes extracted via `git show` from the archived attempt
checkout, re-hashed here before the preregistration freeze):

| file | sha256 |
|---|---|
| ONT-F01 implementation.py | `b846e58e5be7ad893b00b9d41e138caefe4086f2c0300a96cef2e5593b22cbeb` |
| ONT-F01 test_implementation.py | `69500280828ea115c754d2f8f964096317e5d48ffe087031a4f782e4bd0f0b95` |
| ONT-F01 PREREGISTRATION.md | `6544778621855ecf8cad7f957b1e3f205c0a276664f9bc98fddc392d5d97348f` |
| pins_materialized/clearing_declaration.json | `18dd2ff65410cd1cf184a7a8df61c7503a6ce15083f30159e727e9a8117bfbc1` (= pin dc7ea811) |

Pinned inputs: the same 11 pins as the archived candidate (dc7ea811 recipe +
declaration + trunk declaration; a2895755 terrain_query.py / terrain_bundle.py
/ terrain_bundle.json; f30f2224 F01 play receipt; 33e7a444 gait_controller.hpp;
86d0d8d4 native_collision_brief.json; dce368d7 completion_contract.json;
960a2f55 FOLLOWUP proposed.patch). Every pin was re-materialized from git
objects in THIS attempt's checkout and raw-hash-verified (11/11 `raw_match:
true`; byte-identical to the archived candidate's pins — only the local
`file`/`via_repo` path fields differ, as they must).

## What this attempt changed (Q1 port fidelity, audited)

1. Port of `implementation.py` and `test_implementation.py` from `a7b2acc4`
   with ONLY disclosed identity edits: module docstrings + port-provenance
   note; SCHEMA `chimera.ont_f01.qualification.v1` →
   `chimera.mat2_f01.qualification.v1`; `checks.json` identity fields
   (card `MAT2-F01`, attempt `5445fc5ef1df4571ace1e76579fadd9f`, criteria
   `bbcda6c0…`); manifest frame_id prefix `ONT-F01/` → `MAT2-F01/`. The
   complete unified diff is 25 + 6 changed lines, all inside these strings;
   no probe, bar, view, bite, render law or refusal code changed.
2. NEW `make_capture_manifest.py` (packaging only): regenerates
   `evidence/capture_manifest.json` in campaign schema
   `chimera.visual_capture_manifest.v1` from the build outputs, recomputing
   every binding hash from the committed bytes (never copied):
   - envelope: `task_id: "F01"`, `run_id:
     "mat2-f01-forest-20260927-5445fc5e"`, `profile_id: "forest"`,
     `tick_interval: [0, 0]`;
   - `subject_sha256` = sha256 of
     `evidence/pins_materialized/clearing_declaration.json`
     (`18dd2ff6…bfbc1`, asserted equal to the dc7ea811 pin);
   - `capture_sha256` = sha256 of the gate-bound committed capture
     `evidence/frame_V1_clearing_overview_clean.bmp` (`b4aab289…e44`);
   - 6 rows = 3 profile view pairs (clearing overview / terrain-trunk seam
     close-up / side and oblique depth checks), each embedding the build's
     verified 16-field camera record verbatim
     (`camera_record_16field_convention`), with per-row
     `artifact_locator.raw_sha256` recomputed from that row's committed BMP;
   - unit quaternion per view derived from the recorded look-at basis
     (columns [right, up, −fwd]; worst basis error 1.11e-16, worst
     round-trip error 4.44e-16).
3. Re-generated evidence in this attempt: `bites.json`, `checks.json`, 12
   BMPs, `capture_manifest.json`.

## Observed results (exact commands, CPU-only, from this directory)

- `python -B implementation.py bites` → 4/4 bite, fail-first, recorded
  BEFORE the pinned pass (order recorded in checks.json): B1 ghost support
  (+1 cm vertex) detected as OCCLUDED-by-mismatched-surface at the probe ray
  (loads_clean true, oracle height recorded); B2 `f01_boundary_coverage`
  refusal at 1.05 m; B3 `f01_mound_spawn_exclusion` refusal; B4 OFF_FRAME in
  V2 (155.7° off-axis, per amendment A2).
- `python -B implementation.py build` → `all_ok: true`, `bites_all_bite:
  true` (~1 s wall, Python 3.14.3, CPU only). Details:
  - P1 determinism: 4/4 recompiles byte-identical to declaration pin
    `18dd2ff6…`.
  - P2: spawn clearance 11.729184690233646 m ≥ 1.5 m; slopes within frozen
    bounds; grid ≡ height function over 1,681 points; 5 disjoint mounds; 80
    posts; worst on-edge error 0.0.
  - P3: strict-`>` extent, `f02_outside_extent` refusals on all four sides,
    ring extent 20.0 m (no invisible wall).
  - C01: R = I det +1 right-handed; trunk world→local→world round-trip worst
    0.0 m (bar 1e-12); all 80 post bases on the collision surface worst
    8.67e-19 m (bar 1e-9); lateral radius law worst 3.67e-7 m (bar 1e-6);
    trunk site equals the F01 declaration site.
  - P5: 44 frozen probes × 4 frozen views = 176 probe-views → 141
    VISIBLE_EXACT, 8 OCCLUDED (exactly the A6 analytic cylinder-silhouette
    prediction), 27 OFF_FRAME, ZERO mismatches; worst ground height error
    8.951173136040325e-15 m (bar 1e-9); worst ground normal error 0.0
    (bar 1e-12); worst trunk radial error 6.83e-8 m (bar 5e-6); trunk
    face-normal angle within the A5 bound π/32 + 5e-4 rad.
  - P6: spawn ray first-hits `monkey_clearing_ground` at y-error 0.0;
    `collision.same_arrays_as_render = true` (no ghost support).
  - P7: 80/80 posts recovered from the mesh section, 80/80 post tops
    VISIBLE_EXACT in the overview, 0 offset fallbacks.
- `python -B -m unittest test_implementation -v` → **Ran 26 tests … OK**.
- `python -B make_capture_manifest.py` → 6 rows, envelope hashes recomputed
  (values above).
- Q2 byte-determinism: all 12 rendered BMPs sha256-EQUAL to the archived
  candidate's committed blobs at `a7b2acc4` (V1 clean `b4aab2898a01afd9…`,
  V1 diagnostic `2d6005624f0d0229…`, V2 clean `1570caddef964bd9…`, V2 diag
  `415934e9506a97e7…`, V3 clean `5e8eea291b264a26…`, V3 diag
  `ba9432f2102e701c…`, V4 clean `eb5c5d7eaa6e9824…`, V4 diag
  `ee7d7c96a0ac2f61…`, depths `130c5a26f0a2f782… / e9ed8da15b0d85ba… /
  b5dbcbd15ac7586c… / 4eb25c122eced056…`) — 12/12 MATCH.
- Q3/Q4 campaign validators (run from the campaign tools directory against
  the committed bytes):
  - `visual_capture.validate_manifest(manifest, context, forest-profile)` →
    `structurally_valid: true`, view_count 6, capture_kind image.
  - `visual_gate.verify(receipt, contract task_id "F01")` → passes (no
    `capture_task_mismatch`, no `capture_file_binding_mismatch`): the exact
    check that refused the archived candidate now binds subject
    `18dd2ff6…` and capture `b4aab289…` to the committed bytes.

## Clause-to-evidence map (done_when → evidence)

1. **Deterministic terrain/tree recipe** — pinned recipe + declaration
   re-materialized and raw-hash-verified in this attempt (11/11 pins); P1
   4/4 byte-identical recompiles; tree asset is F03's declared mesh at F01's
   site (C01 site-equality check).
2. **Explicit extent and coordinate convention** — declaration convention
   block (right-handed, x=east y=up z=south, metres, origin at scene
   centre); P3 strict-`>` extent with all-four-sides refusals and ring
   extent 20.0 m; C01 frame-chain checks (det +1, cross-product identity,
   round-trips, landmarks).
3. **Safe spawn** — P2 clearance 11.729184690233646 m ≥ 1.5 m; P6 spawn ray
   first-hits the rendered/collision ground at y-error 0.0 (ghost-support
   falsifier B1 demonstrably bites).
4. **Visible boundary** — P7 80/80 posts recovered and 80/80 post tops
   VISIBLE_EXACT in the frozen overview (0 fallbacks); P3 worst on-edge
   error 0.0 (the visible ring IS the blocking edge); visible_static
   evidence set = 12 committed BMPs + the campaign capture manifest (Q3/Q4),
   byte-identical to the registry-reviewed renders (Q2).

## Falsifier

Bites B1–B4 recorded failing-first before the pinned pass (results above);
the pass then runs on the pinned bytes. Tags alone establish nothing: B1
proves the correspondence machinery detects a +1 cm rendered/collision
divergence, B2/B3 prove the declaration validators refuse coverage/spawn
violations, B4 proves the visibility classifier reports OFF_FRAME rather
than passing an off-frame subject.

## Deviations and disclosures (exact reasons)

1. **Preregistration appendix** (after first suite run): the ported suite
   asserts frozen-section markers inside PREREGISTRATION.md; the appendix
   restates the inherited archived preregistration verbatim (hash-pinned).
   No prediction, bar, probe, view or bite changed; the inheritance was
   already frozen in the header.
2. **Two additional campaign-schema defects found by scoped validator
   dry-run on the archived corrected draft** (the workspace copy of the
   never-committed envelope fix found in the archived attempt tree): (a)
   diagnostic rows carried `required_subject_ids: []` →
   `visibility_required_subject_ids_invalid`; fixed by setting the same
   non-empty subject triple as the clean rows (declared in PREREGISTRATION
   Q3). (b) the draft attempted 4 view pairs under the profile's 3 view
   names → `capture_view_duplicate` (V3 and V4 shared view_id "side and
   oblique depth checks"); fixed by declaring 3 pairs (V3 = side bookmark
   declares the "side and oblique depth checks" pair). V4 (oblique) remains
   fully rendered, committed, sha256-listed under `capture_layout.files`,
   with its probes classified in checks.json P5 — a manifest row count
   change only, forced by the validator's (view_id, mode) uniqueness; all
   4 frozen views keep their full frozen probe coverage.
3. **`evidence/camera_manifest.json`** remains the build's bare 16-field
   record dump (unchanged build behaviour, byte-for-byte the reviewed
   candidate's writer); the campaign-binding manifest is
   `evidence/capture_manifest.json`. Reviewers should bind the gate to the
   latter (receipt shown to the lead uses `capture_manifest.json`).

## Honest boundary (unchanged from the reviewed candidate)

Static-scene qualification of the pinned clearing data package plus an
attempt-local stdlib render of those bytes. NOT claimed: engine run or HTTP
load_mesh exercise; native collision query route (#120 S1-3); engine-side
render upload (#120 S1-4); engine walk replay or playable-build acceptance;
trunk contact subsystem (Stage 2); training or runtime acceptance; W10
scene readiness. Downstream owners unchanged (F02 render/collision
tolerance; F03 trunk qualification; F04 contact dynamics; D-FOREST cards
own S1-3/S1-4). Required ports: `surface_query(x_m, z_m) → {h_m, gx, gz,
inside}` and the S1-4 render upload of `terrain_bundle.json`. The
rasterizer is evidence tooling, not the engine render path. Play-lane
artifacts are cited as static/data-package evidence only (R5 correction).
