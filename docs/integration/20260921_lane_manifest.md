# Integration Lane Manifest — 2026-09-21

<!-- Author: agent/integration-manifest-20260921. Every sha, parent edge, and file list in
     this document was MEASURED on 2026-09-21 with git against the shared origin
     /e/ChimeraWork/movie-agent (master 32105f18, "Record native coupled-arm proof and
     continuation handoff", 2026-09-17) and against the per-lane worktree clones under
     /e/ChimeraWork/*-agent for branches that never left their clone. Nothing here is taken
     from the intake list on faith: where the intake list was wrong, the correction is
     recorded below and the measured DAG is authoritative. -->

Purpose: the integrator's map for the ~verified 2026-09-19/20 lanes awaiting master
integration — head shas, bases, touched files, the receipt evidence each lane was verified
with, the real (measured) conflict surface, a recommended merge order, and the lanes that
must NOT merge yet.

Verification method used for this manifest: `git rev-parse` / `git log` / `git
merge-base` / `git rev-list --parents` / `git diff --name-status <base> <head>` per lane;
parentage of every walk wave re-measured (`HEAD^`), not assumed; add/add candidates
compared by blob id; the cross-lineage conflict surface computed as the intersection of the
two lineages' post-fork (`f7ddbd07..head`) file sets.

---

## 0 · CORRECTIONS TO THE INTAKE LIST

1. **Two lanes are not on the shared origin.** `agent/wiseman-osim-20260920` lives only in
   the `osim-agent` clone; `agent/workflow-mcp-20260920` only in the `mcp-agent` clone.
   Both head shas verified where they live (`git ls-remote /e/ChimeraWork/movie-agent`
   does not list them).
2. **Walk waves 14–26 are clone-local.** Only wave12 and wave13 are on the shared origin.
   Waves 14–26 live in `w14-agent` … `w26-agent`. All 15 landed wave heads verified.
3. **The intake list's walk-chain sha ORDER was wrong in the middle.** Measured parentage:
   `b5886451` (w14) → **`c3db49cd` (w15)** → **`47d30cb4` (w16)** → **`c03ddf41` (w17)** →
   `74fc0195` (w19). The intake list had w15 and w17 swapped. All 15 shas themselves exist.
4. **The walk chain is NOT strictly linear — one falsified sibling.** Wave18
   (`agent/gait-wave18-partial-lean`, 17936d83) and wave19 (`agent/gait-wave19-leaned-entry`,
   74fc0195) are BOTH single-parent children of wave17 (c03ddf41). w20+ descend from **w19**;
   **w18 is an ancestor of no later wave** (falsified: "the entry-lean freedom is MEASURED
   EXHAUSTED"; w19 re-cut from w17 with the reconciled full-vault-lean composition 100 min
   later). The surviving fast-forward line is **12→13→14→15→16→17→19→20→21→22→23→24→25→26**.
5. **matter-skeleton-b is a CHILD of matter-skeleton-import** (A is B's first-parent chain
   base: 815a6504's parent is 2d585c7b), and **wiseman-osim is a CHILD of
   muscle-data-research** (aede5de9's parent is fc45106c), and **workflow-mcp is a CHILD of
   triangle-monkey-grid** (a672b16b's parent is 1b08b29d). Three dependency edges the
   intake list implied but did not state.
6. **wave27a moved during this survey.** `w27-agent` was at 6efb3ef0 (wave26, no work) at
   first read and at d981bc04 ("Wave 27: THE SINKING SHOULDER", 2026-09-20 21:27) at second
   read — the lane is actively landing. Treated as in flight, below.
7. Engine lane: `agent/engine-determinism-argc` is TWO commits (e435de97d691… preregistration
   + ee2dec8378d… measured receipt), base master 32105f18.

---

## 1 · STANDING INTEGRATION LAWS (apply to every merge below)

From the lead's integration memory, with the in-repo enforcement points that carry them:

- **Merge-by-replay contract.** A merge is not done when git exits 0 — it is done when the
  merged tree REPRODUCES the lane's receipt. Engine lanes: fresh cmake build, digit-exact
  reproduction of the receipt's headline numbers. Derivation lanes: script re-run in a
  fresh clone, clean `git diff` = byte-exact. Visual lanes: the pixel checker
  (`pixel_truth.py`, grain/coverage/clip-scan). Research lanes: sources re-checked. (This
  is THE_CHECKLIST.md §5, the lead's own verification contract — the merge replays it on
  the integrated tree, not on the lane tree.)
- **The `--ours` trap.** A conflict resolved with `--ours`/`-X ours` silently DROPS the
  other side's work records — receipts, derivations, verdicts. After every conflict
  resolution: verify the work records survive (receipt_waveN.json, PREREG/RESULT,
  validation dirs present at the merged head), and re-run the lane's verify on the merged
  tree. A resolution that deletes a receipt is a lost verdict, not a merge.
- **Conflict-marker greps.** After each merge and before any commit: grep the merged paths
  (text files) for the git marker pairs — seven open-angle brackets, seven close-angle
  brackets, and the seven-equals divider (`grep -rnE '^(<{7}|>{7}|={7})'`). A committed
  conflict marker is a false GREEN shipped to every downstream lane.
- **Byte-stability of data files.** `tools/science_funnel/data/**` must stay byte-stable
  (the `.gitattributes -text` rules exist for exactly this — sha-pinned upstream bytes,
  checksum replay). Blob-verify before and after merge: where several lanes add the same
  data file, the blobs are IDENTICAL (verified below, e.g. `bone_identification.json` =
  e1f60209 in all eight lanes that carry it); any post-merge blob drift is a defect, never
  a normalization.

---

## 2 · THE LANES

Legend: base = measured fork point (branch + sha). Files = `git diff --name-status
<base>..<head>`. Evidence = what the lead verified and how, quoted/condensed from the
lane's banked receipts and commit bodies.

### 2.1 agent/workflow-checklist-20260920 — docs, merge anytime
- **Head:** e9c8b394118e8b6cb4d43d3c932bfdfab8c3b113 (on origin)
- **Base:** master @ 32105f18 (merge-base measured)
- **Commits:** 1 (e9c8b394)
- **Files:** A `docs/THE_CHECKLIST.md` (only file)
- **Evidence:** operator-directive doc (2026-09-20), the one workflow every agent runs; §5
  states the per-lane-type verification contract itself. Content-only lane; nothing to run.
- **Conflicts/dependencies:** add/add on THE_CHECKLIST.md with the constitution lane (2.7) —
  measured: constitution's file is this file PLUS a 27-line appended section (strict
  superset). Merge FIRST; the constitution lane then resolves trivially.

### 2.2 agent/muscle-data-research-20260920 — research memo
- **Head:** fc45106cd700c8c0096c3a395b1f90ee0df7b3ae (on origin)
- **Base:** master @ 32105f18
- **Commits:** 1 (fc45106c)
- **Files:** A `docs/research/20260920_adult_and_muscle_data_options.md` (only file)
- **Evidence:** research-gate memo — measured MorphoSource sweep (1,671 Macaca records, 18
  full-body CTs, zero commercial-OK full-body), tier-1 adult candidates verified, the
  biological L1–L4 mixing-rules checkpoint spec, operator hand-download list. Sources
  re-checked per the research lane contract; wiseman lane (2.3) pre-registered against it.
- **Conflicts/dependencies:** none. **Must land before wiseman-osim** (its child).

### 2.3 agent/wiseman-osim-20260920 — data acquisition (clone-local: osim-agent)
- **Head:** aede5de9516949d4584e5cfffc8b71064afe7edc
- **Base:** agent/muscle-data-research-20260920 @ fc45106c (measured parent)
- **Commits:** 1 (aede5de9)
- **Files:** A `tools/science_funnel/data/wiseman2026/**` — 18 files, +49,430 lines:
  7 `.osim` models (Bonobo…Macaque…Siamang), 2 supplementary files (rsos260107_si_001.docx,
  _002.xlsx), `LICENSE_CC_BY_4.0.txt`, `acquisition_preregistration.json`,
  `download_receipt.json`, `inventory.json`, `sha256_manifest.json`, `_api/*.json`.
- **Evidence:** pre-registered acquisition (`acquisition_preregistration.json` written
  before any download; per-source predictions/falsifiers recorded against the fc45106c
  memo prior); CC BY 4.0 license recorded; sha256 manifest for checksum replay.
- **Conflicts/dependencies:** all-new directory — no file conflicts. Merge after 2.2.

### 2.4 agent/reality-fantasy-gate-20260920 — the adjudicator
- **Head:** 4d1c0ffa160c816a444c8d35159ba5781bc49ec8 (on origin)
- **Base:** master @ 32105f18
- **Commits:** 1 (4d1c0ffa)
- **Files:** 26 added — `tools/creature_graph/reality_gate.py` +
  `tools/creature_graph/tests/test_reality_gate.py` +
  `tools/creature_graph/validation/reality_gate_20260920/` (receipt.json,
  adjudications.json, 4 bundle JSONs, 2 runner scripts) + science_funnel data receipts
  (morphosource_ct bone_identification.json/download_receipt.json/mesh receipts +
  meshes manifests, ncbi_taxdmp extract, oku_bipedal PMC fulltext + receipt) +
  `validation/gait_controller_20260918/derived_numbers.json` +
  `validation/mount_reconciliation_20260919/` (3 files).
- **Evidence:** the two-category law measured — four preregistered adjudications all HIT
  (infant CT 000875604 → REALITY 0 violations; H2 mount → FANTASY +17.4..+173.0%; walker →
  REALITY with work-sum closure 0.0% / GRF impulse closure −0.004%; chimera → FANTASY
  humerus:femur +259.0%). Re-runs byte-identical; graph tests 19 OK both roots; new suite
  32 tests OK.
- **Conflicts/dependencies:** the shared data receipts (bone_identification.json etc.) are
  added by SEVEN other lanes too — blob-identical everywhere measured (e1f60209), so every
  add/add is trivial (keep one). **Land before the constitution lane** (2.7's pointers and
  THE_GAME.md Amendment 2 cite this lane's gate module and receipt). Watch item: the
  pre-existing (out-of-scope) `agent/mount-reconciliation` branch also carries
  mount_reconciliation_20260919 receipts — reconcile if it ever lands.

### 2.5 agent/matter-skeleton-import-20260920 — matter specimen A
- **Head:** 2d585c7b76a60dc299b2df798e8de22b4a59acfc (on origin)
- **Base:** master @ 32105f18
- **Commits:** 2 (1e56b90e import; 2d585c7b sha256 canonicalization repair — the verifier's
  fresh clone refused definition_drift and was RIGHT)
- **Files:** 62 — M `.gitattributes` (+`tools/science_funnel/data/morphosource_ct/**
  -text -whitespace`); A `matter_skeleton/tris/**` (25 resident triangle files),
  `matter_skeleton` definition, 25 `meshes_preview/**`, `meshes/manifest.json`,
  `bone_identification_v3.json`, 4 `validation/matter_skeleton_20260920/**`.
- **Evidence:** Rule-0 receipt banked BEFORE the tool (append-only proven by byte
  reconstruction); falsifiers all green: geometry 25/25 face+vertex equal (worst bbox dev
  6.3e-06 mm), adjacency 21/21 (rest-length dev 0.0 mm), mass book 52.3139 g in the 30–65 g
  window (mesh vs voxel −2.28%, worst compartment −3.27% itemized; Prange deviation NAMED,
  never tuned), kernel conformance (parse_body unmodified, 9/9 + 37 OK), stage_true infant
  scale 1.0; byte-exact regeneration in verify mode (fresh-clone law); data inherited
  blob-identical (30/30) from `origin/buffy/bone-id-transfer-20260919`.
- **Conflicts/dependencies:** `.gitattributes` M/M vs 2.6/2.11 lines (union resolution, see
  §4). Data adds blob-identical with other lanes. **Land before matter-skeleton-b** (child,
  and its receipts re-verify A: "verify b + verify a green").

### 2.6 agent/matter-skeleton-b-20260920 — matter specimen B
- **Head:** 53affb9c3cbcca29b8a6ce741611563118f57898 (on origin)
- **Base:** agent/matter-skeleton-import-20260920 @ 2d585c7b (measured parent chain:
  53affb9c → d921d031 → 815a6504 → 2d585c7b → 1e56b90e → 32105f18)
- **Commits:** 3 on top of A (815a6504 preregistration BEFORE the run; d921d031 import;
  53affb9c post-run measurements appended)
- **Files (vs A):** adds `meshes_875599/manifest.json`, `meshes_preview_875599/**` (25),
  `matter_skeleton_875599/**` (definition + 14 tris), 4 `validation/
  matter_skeleton_b_20260920/**` — tool parameterized ADDITIVELY (A's bare invocation
  proven byte-unchanged).
- **Evidence:** 6/6 falsifiers GREEN with numbers (14 compartments / 8 bonds / 12.0824 g =
  −0.061% of the identified-subset voxel book; geometry 1.39e-06 mm; adjacency 0.0 mm + 7
  excluded edges itemized; kernel 7.2e-07); prediction audit 4/4 HIT; **fresh-clone proof
  banked** (102-file worktree==blob pre-check; verify b + verify a green; tamper → REFUSED
  definition_drift exit 2; restored green); two mid-flight refusals banked as gate-fire
  evidence; corrections list empty. This is the canonical instance of the fresh-clone
  byte-exact contract.
- **Conflicts/dependencies:** none beyond A (superset child; B data checked out from
  `bone-id-v3-companion` with worktree==blob proved for all 27 files, LF-only — the CRLF
  lesson applied pre-check).

### 2.7 agent/constitution-bio-laws-20260920 — THE_GAME Amendment 2
- **Head:** c0e130c5624e987890ce894ee0bdfb278c62d790 (on origin)
- **Base:** master @ 32105f18
- **Commits:** 1 (c0e130c5)
- **Files:** A `docs/THE_CHECKLIST.md` (the 2.1 file + 27-line "THE CONSTITUTION POINTERS"
  appendix — strict superset, measured by blob diff: 27 insertions, 0 deletions);
  M `docs/THE_GAME.md` (append-only Amendment 2, +108/−0: THE BIOLOGICAL LAW, THE
  TWO-CATEGORY LAW, THE TRIANGLE DOCTRINE — statement/rationale/falsifier/enforcement each)
- **Evidence:** operator's banked words as canonical law text, receipts cited per entry:
  the gate's four adjudications (2.4's receipt), the triangle lane's splat divergence as
  the triangle-doctrine proof case. Both diffs additions only (append-only house law).
- **Conflicts/dependencies:** THE_CHECKLIST.md add/add with 2.1 — resolve by taking THIS
  lane's file (measured superset; verify the 2.1 blob is a prefix). Should land AFTER 2.1
  (its base doc) and AFTER 2.4 (its pointers cite reality_gate.py and its receipt).

### 2.8 agent/skeleton-movie-20260919 — the visual lineage root
- **Head:** ef02772dae269fac496071c69937982ce7ecf309 (on origin; NOTE: this branch is also
  the shared repo's current checkout — push-safe, pull/merge from it read-only)
- **Base:** master @ 32105f18 (measured merge-base; the lane carries 80 commits: the shared
  gait-wave-4..6 + morphosource-CT + bone-ID stack the walk chain also forks from, at
  f7ddbd07, plus this lane's own 2: 0f9e3dd0 CT visual layer, ef02772d skeleton movie)
- **Files (vs master):** 473 A + 36 M — the whole committed CT skeleton layer
  (118,617-splat buffer + 25 marching-cubes bone previews), `skeleton_movie.py`,
  `ct_skeleton_layer.py` (+13 tests), `validation/skeleton_movie_20260919/` (record.json +
  receipt.json + 13 more), docs/research, and the shared-stack engine files
  (gait_controller.hpp, gait_unit.cpp, coupled_*, CMakePresets.json …).
- **Evidence:** the standing visual contract fulfilled for the CT skeleton — 24-frame
  3-elevation orbit through the splat shell, dyad-judged with one identical blind prompt,
  verbatim reads recorded; F1 discrimination PARTIAL FAIL (align(true,P1)=0.9 ≥ 0.5 —
  scorer blind spot named, not tuned); **F2 determinism FAIL honestly banked (8/48
  replicate frames differ, max 3/255)** — the defect the engine lane (2.10) owns and fixes;
  F3 own-port PASS (8097 bind-tested; 8127 untouched). Rule-0 record.json banked before
  the first render. Also banked: the argc launch trap diagnosis (cost hours, under cdb).
- **Conflicts/dependencies:** root of the visual lineage — **2.9 and 2.11 (mcp) are its
  children and must follow it**. Post-fork (f7ddbd07..head) it does NOT touch a single file
  the walk chain touches (measured intersection: EMPTY). Sort.defect = 2.10's M1.

### 2.9 agent/triangle-monkey-grid-20260920 — the visual repair (Defects A–D)
- **Head:** 1b08b29d8d5607484afda59532912261c6a53267 (on origin)
- **Base:** agent/skeleton-movie-20260919 @ ef02772d (measured parent)
- **Commits:** 1 on top of the movie lane (1b08b29d)
- **Files (vs its base):** M `engine.cpp`/`engine.hpp` (mesh pipeline, bbox-centre camera
  target), M `main.cpp` (near-plane tracking, `small` macro rename), M
  `shaders/floor.vert`/`floor.frag` (per-fragment guide distance, depth-write OFF, UBO
  layout fix), M `free_root_dynamics.hpp`-adjacent surface, A
  `ct_skeleton_triangle.py` (compose: 355,831 verts / 712,522 tris through /mesh_bin), A
  `pixel_truth.py` (the deterministic pixel checker: grain, coverage, object/guide
  presence, clip scan), A `tests/test_ct_skeleton_triangle.py` (conformance gate: 5 tests,
  fails if the monkey ever posts /membrane_bin again), A
  `validation/triangle_monkey_20260920/{before,after}/**` (16+33 files) + receipt.json
  (preregistered A/B/C/D membranes + falsifiers), M `docs/THE_STUDIO_GRID_DEPTH.md`
  (append-only), M `.gitattributes` (+`tools/science_funnel/data/** -text`).
- **Evidence:** measured per-defect: A — per-bone silhouette coverage median 0.120 → 0.568
  (same hulls, same camera), five zero-coverage bones now 0.40–0.81; B — object_seen from
  the wrong side 0.0/0.0 → 0.749/0.519; C — frame 9 body px 605,367 → 2,488,355; D — CoG
  vs bbox-centre offset 27.26 mm = ±8.73% predicted swing, camera now pivots on the body.
  Regressions: ct_skeleton_layer 13 OK, conformance 5 OK, graph 19 OK + 14 OK both roots,
  body_surface 17/17, articulation_native 16/16, splat path still exercised.
- **Conflicts/dependencies:** **real M/M conflict on `ChimeraEngine/engine/main.cpp` with
  the engine lane (2.10)** — resolution = this lane's rendering changes + 2.10's argc guard
  re-applied, then BOTH lanes' receipts replayed. `.gitattributes` union with 2.5/2.12.
  **2.11 (workflow-mcp) is its child — this lane MUST land first** (the MCP tools wrap
  pixel_truth.py and ct_skeleton_triangle.py; thresholds are pre-encoded from this lane's
  banked numbers).

### 2.10 agent/engine-determinism-argc — engine robustness + the determinism fix
- **Head:** ee2dec8378d48c284c3f9eca400c820ff1f0981e (on origin)
- **Base:** master @ 32105f18
- **Commits:** 2 (e435de97d691… — stable splat sort total order, bounded argc parsing,
  banked-vocabulary scorer, receipt preregistered BEFORE the edits; ee2dec8378d… —
  measurements appended to the byte-verified pre-registered block)
- **Files:** M `ChimeraEngine/engine/main.cpp` (argc guard), M
  `ChimeraEngine/engine/shaders/sort.comp` ((key,index) tie-break); A
  `tools/science_funnel/ct_skeleton_layer.py` + morphosource_ct data + walker
  derived_numbers — explicitly pinned "identical git blobs" from lane 2.8 (verified for
  bone_identification.json: e1f60209), harness deps only.
- **Evidence:** M1 GREEN — 118,617-splat buffer, 4 separate uploads × 24-frame orbit:
  byte-identical PNGs (plain 0/24 differing, history-dirtying interleaved protocol 0/24,
  max per-pixel delta 0), median 10.2–10.8 s/orbit before AND after; the movie lane's
  pre-fix RED honestly recorded as not-reproducible from fresh states (history-dependent)
  — the fix removes the mechanism by construction. M2 GREEN — pre-fix crash reproduced
  (exit 0xC0000409, empty stderr), fixed engine serves all launch shapes, usage + exit 1
  on bad flags, legacy positional parity. M3 split, reported honestly — vocab_align
  (banked vocabulary, no model calls): P1 0.358 (distinguished), P2 0.608 → the banked
  falsifier FIRES for the scale probe; RED stands. Regressions: graph 19 OK ×2 roots,
  tests_p1 165/165 + 9/9, articulation native 16 + gpu 3 + body_surface 16 failed=0, teddy
  smoke through the fixed engine.
- **Conflicts/dependencies:** main.cpp M/M with 2.9 (see §4). Sort fix owns 2.8's F2 defect
  — land after the visual lineage and replay its receipt on the merged build.

### 2.11 agent/workflow-mcp-20260920 — the checklist as MCP commands (clone-local: mcp-agent)
- **Head:** a672b16ba2422a68fa43896a78571d9ee3eb2250
- **Base:** agent/triangle-monkey-grid-20260920 @ 1b08b29d (measured parent)
- **Commits:** 1 on top of the triangle lane (a672b16b)
- **Files (vs its base):** M `ChimeraEngine/mcp_server.py` (+7 additive tools, 0 removed
  lines), M `ChimeraEngine/MCP_ENGINE.md`; A `tools/science_funnel/workflow_commands.py`
  (the checklist as a machine-readable walk); A
  `tools/science_funnel/tests/test_workflow_commands.py`; A
  `validation/workflow_mcp_20260920/` (receipt.json, e2e_render_record.json,
  e2e_verify_visual.json, 3 e2e stills).
- **Evidence:** measured end-to-end on a fresh self-started engine (bind-tested free port;
  8127 refused by code): 25 bones / 355,831 verts / 712,522 tris through /mesh_bin;
  whole-hull coverage 0.397 (banked mesh 0.3957), per-bone median 0.5694 (banked 0.568),
  bones_at_zero 0; 12-frame orbit clip-scan clean; verify-visual 6 gates pass / 0 fail / 3
  honestly not-measured, exit 0. En-route defect found and fixed: the boot-restore /camera
  race (start_engine launches with --no-restore; post-fix probes match the projection model
  to ≤ 1 px). Suites: workflow_commands 13/13, ct_skeleton triangle+layer 18/18, graph 19
  ×2 roots, MCP registry lists the 7 commands with orient/next still answering.
- **Conflicts/dependencies:** wraps 2.9's instruments ("pixel_truth/workflow_commands on
  the mcp lineage") — **strictly after 2.8→2.9**; replay workflow_commands + e2e on the
  merged head (the render_creature numbers are pinned to the banked triangle values).

### 2.12 THE WALK CHAIN — waves 12…26, merge as ONE sequence
One linear fast-forward line (parentage measured per wave), plus one falsified sibling
(wave18) that merges NOT:

| # | branch | head (full sha verified) | parent (= previous head) | own files per wave |
|---|--------|--------------------------|--------------------------|--------------------|
| 12 | agent/gait-wave12-planted-struts | e7dce7e2013d7c62591b15a23b7a42c686c72884 | master@32105f18 + merge 84ff1747 of the sole-contact line; 9 own commits | gait_controller.hpp, gait_unit.cpp, coupled/multidynamics/free_root headers, tests, CMakePresets, receipts |
| 13 | agent/gait-wave13-stepping-struts | 554f40edbce92111d2ef972d2b6a262e3c3c2da8 | e7dce7e2 ✓ | gait_controller.hpp, gait_unit.cpp, receipt_wave13.json |
| 14 | agent/gait-wave14-entry-pose | b588645159b0292678b28e66fb9e61df8cdcb60b | 554f40ed ✓ | + gait_scene.py, derive_entry_pose.py/json, receipt |
| 15 | agent/gait-wave15-level-entry | c3db49cd59952e69e7c01aaaed8d48542c80b40d | b5886451 ✓ | same pattern, receipt_wave15 |
| 16 | agent/gait-wave16-load-strut-trade | 47d30cb4d03ed69ec46f332887367b5e6e204c6c | c3db49cd ✓ | same, receipt_wave16 |
| 17 | agent/gait-wave17-seat-law | c03ddf41406515233d5ffc9b1415519c5ef3b2b9 | 47d30cb4 ✓ | gait_unit.cpp (not the controller), receipt_wave17 |
| 18 | agent/gait-wave18-partial-lean | 17936d83f40f2925c394c71c9abc307897127c4a | c03ddf41 — **SIBLING, see below** | gait_controller.hpp, gait_unit.cpp, receipt_wave18 |
| 19 | agent/gait-wave19-leaned-entry | 74fc019521ccce4b2c9a4719ed4fd2bb1048eb02 | c03ddf41 ✓ (the surviving line) | gait_unit.cpp, derive_leaned_entry.py/json, receipt (gait_controller.hpp byte-untouched) |
| 20 | agent/gait-wave20-midentry-replant | 5c94fb4bb65d56d2ae212179a9be9ea729f79131 | 74fc0195 ✓ | controller + unit + receipt |
| 21 | agent/gait-wave21-hind-ride | 8a17c5003caaba4c2c34db9b74bc1b4ffc007209 | 5c94fb4b ✓ | controller + unit + receipt |
| 22 | agent/gait-wave22-touch-reset | 17b6bdde5ba6b59f576c053b428afb8747533d76 | 8a17c500 ✓ | controller + unit + receipt |
| 23 | agent/gait-wave23-joint-wall | 3cf3674cb16d70a91ad7b0b7d59657e840ad90b7 | 17b6bdde ✓ | controller + unit + receipt |
| 24 | agent/gait-wave24-glide-pocket | ecddf6eb34f72c5643f9bb7c069d3e9a7b05006e | 3cf3674c ✓ | controller + unit + receipt |
| 25 | agent/gait-wave25-gate-cadence | 40811bddfce8a5f5885fc58030a39d60dd2c00f4 | ecddf6eb ✓ | controller + unit + receipt |
| 26 | agent/gait-wave26-wall-wait | 6efb3ef0e287e5ee268463cc0e26bfd68caf22d9 | 40811bdd ✓ | controller + unit + receipt |

Waves 12–13 are on the shared origin; 14–26 clone-local (w14-agent … w26-agent; wave25's
clone dir is `w25b-agent`).

- **Base:** wave12 merges master@32105f18 (its own line) with the shared stack at f7ddbd07
  (merge-base with the movie lane measured = f7ddbd07). Every later wave's single parent is
  the previous wave's head — merging wave12 then fast-forwarding to wave26 is the whole
  integration.
- **Files (chain, post-fork):** 42 — `ChimeraEngine/engine/gait_controller.hpp` +
  `ChimeraEngine/engine/tests_coupled_arm/gait_unit.cpp` (EVERY wave except 17/19 touch the
  controller; every wave touches the unit — the shared-file pair, resolved by the ff order:
  last writer = wave26), `coupled_articulation.hpp`, `gait_scene.py`,
  `validation/gait_zero_20260919/receipt_waveN.json` + derive_*.py/derived_*.json (12 waves
  of receipts), + wave12's headers/CMakePresets/tests, + `.gitattributes`
  (+`tools/science_funnel/data/** -text`, same line as the triangle lane — trivial).
- **Evidence (the standing per-wave contract, receipts wave12…26):** falsifiers
  pre-registered in `receipt_waveN.json` BEFORE the run, pre-registered block never edited,
  measurements appended; every wave re-verifies on the byte-exact prior baseline (scene sha
  reproduced before any edit — 481f9f56 through w24, byte-stable twice); the proof-standard
  fence (waves 22–26: ticks [0,65] LINE-IDENTICAL, thousands of lines, 0 diffs, first
  divergence exactly the law's own tick); named-tick entry digits byte-identical (press at
  4, peak 41.325 N at 31, capture at 60); determinism bit-identical (plain==trace
  byte-equal, F-G7); free-fall −9.806650 exact; 19/37 graph tests both PYTHONPATH roots;
  elbow ceiling enforced. Cross-lane byte-exact proof of the clone re-run contract exists
  at w27b: the whole 105-tick trace stderr BYTE-IDENTICAL across lanes to the w26 lane's
  trace, 1,847,605 bytes, 0 diffs. Honest reds carried at every wave: the run ladder
  refusal 82→80→83→84→99→97→105 (w19→w26), each with the next membrane's law banked in the
  receipt. pass=false on the 426 bar is the chain's HONEST state — these lanes merge as a
  verified falsifier RECORD, not as a walking creature.
- **Conflicts/dependencies:** post-fork file intersection with the visual lineage measured
  EMPTY (0 of 81 × 42 files) — the walk chain and 2.8/2.9/2.11 interleave cleanly. Shared
  data adds (bone_identification.json etc.) blob-identical. `.gitattributes` line identical
  to 2.9's. **Internal order is absolute**: 12→13→14→15→16→17→**19**→20→21→22→23→24→25→26;
  the chain must NOT absorb wave18 (not an ancestor of wave26; its controller edits are the
  falsified variant — merging it would fork the line). Optionally cherry-pick wave18's
  three record files (derive_partial_lean.py, derived_partial_lean.json,
  receipt_wave18.json) as docs-only AFTER the line lands, controller/unit changes excluded.

---

## 3 · RECOMMENDED MERGE ORDER

Dependencies first; identical-blob add/adds anywhere; every step closed by replaying the
lane's verification on the merged tree (§1):

1. **agent/workflow-checklist-20260920** (2.1) — one doc file, zero conflicts; every later
   merge is judged by its §5 contract.
2. **agent/muscle-data-research-20260920** (2.2) — one doc file, zero conflicts.
3. **agent/wiseman-osim-20260920** (2.3) — child of 2; all-new data dir + receipts.
4. **agent/reality-fantasy-gate-20260920** (2.4) — the adjudicator; trivial identical-blob
   data adds; needed before 6 (its pointers cite the gate).
5. **agent/matter-skeleton-import-20260920** (2.5) — specimen A; `.gitattributes` conflict
   resolved here (union: keep 2.9/2.12's `data/** -text` AND A's
   `morphosource_ct/** -text -whitespace`).
6. **agent/constitution-bio-laws-20260920** (2.7) — after 1 (THE_CHECKLIST.md add/add:
   take this lane's file, the measured superset) and after 4 (its law entries cite the
   gate's receipt).
7. **agent/skeleton-movie-20260919** (2.8) — the visual lineage root (80 commits incl. the
   shared stack the walk chain forks from; identical commits ⇒ git merges the shared stack
   once, silently).
8. **agent/triangle-monkey-grid-20260920** (2.9) — ff onto 7; the visual repair.
9. **agent/engine-determinism-argc** (2.10) — resolve main.cpp M/M with 8 (triangle's
   rendering + argc guard), replay M1/M2/M3 on a fresh merged cmake build; owns 7's F2
   defect.
10. **agent/workflow-mcp-20260920** (2.11) — ff onto 8; the MCP tooling that WRAPS the
    visual repair (pixel_truth/workflow_commands); replay workflow_commands 13/13 + e2e on
    the merged head.
11. **agent/matter-skeleton-b-20260920** (2.6) — child of 5; replay the fresh-clone proof
    (verify a + verify b green, tamper → REFUSED) on the merged head.
12. **THE WALK CHAIN** (2.12) — merge wave12 (the one real merge: shared stack + receipts),
    then fast-forward 13→17→19→…→26. Post-fork conflict surface with everything above:
    measured EMPTY. Close by replaying the chain's standing battery + fence on the
    integrated master, and read the ladder honestly: refusal tick 105 at wave26.

Rationale for the tails: docs/data first (zero conflict risk, and later lanes' receipts
cite them); gate before constitution (pointer integrity); visual root before its wrapper
(the MCP tools pin the triangle numbers); engine determinism after the visual lineage
(main.cpp) but before the chain so the sort fix is in the tree the walk replay runs on;
matter B after its parent A; the walk chain LAST — it is the largest sequence, it conflicts
with nothing (measured), and its replay battery is the cheapest whole-tree regression check
the integrator has.

## 4 · THE REAL CONFLICT LIST (measured)

1. `docs/THE_CHECKLIST.md` — 2.1 vs 2.7, add/add; 2.7's blob = 2.1's + 27 appended lines
   (verified). Resolution: 2.7's file. Verify the prefix property, do NOT `--ours` either
   side blind.
2. `ChimeraEngine/engine/main.cpp` — 2.9 vs 2.10, M/M, real content conflict. Resolution:
   both (near-plane/pivot/macro from 2.9 + argc guard from 2.10), then BOTH receipts
   replayed (pixel checker + M1/M2 harness).
3. `.gitattributes` — 2.5 (`morphosource_ct/** -text -whitespace`) vs 2.9 and 2.12
   (`tools/science_funnel/data/** -text`). Resolution: union (the broad rule + A's
   stricter whitespace flag).
4. Shared data adds — `bone_identification.json` (+ download/mesh receipts, previews,
   manifests, `ct_skeleton_layer.py`) added by up to seven lanes (2.4, 2.5, 2.6, 2.8, 2.9,
   2.10, 2.12): blobs measured IDENTICAL (e1f60209 for the identification file; the engine
   lane's pins verified). Resolution: keep one; blob-verify after merge (§1 byte-stability
   law).
5. `gait_controller.hpp` / `gait_unit.cpp` — every walk wave (2.12). Resolved by the
   fast-forward order itself; never hand-merge these two files across waves.
6. Cross-lineage: visual (2.8–2.11) vs walk (2.12) post-fork intersection measured EMPTY —
   no conflict exists; do not invent one.

## 5 · DO NOT MERGE YET (in flight)

- **agent/gait-wave27-sinking-shoulder** (clone w27-agent) — head d981bc04e92fb0040d481d2c
  75c07a8c7448d49e as of this writing, cut from wave26, COMMIT LANDED DURING THIS SURVEY
  (the lane is actively moving). Receipt banked, hind-extension height-hold law, ladder
  105 → 122, pass=false on the 426 bar. Wait for the lead's verdict and a stable head.
- **agent/gait-wave27b-posture-sink** (clone w27b-agent) — head
  d907f8884b9427e9ed97e2e873b50f261e579fa7, cut from wave26. The honest NEGATIVE (posture
  hypothesis sealed: an 8.57° command change produced 0.000 mm of dynamics), engine files
  byte-untouched. Racing sibling of 27a — the lead picks the wave-27 line; do not merge
  either until then.
- **agent/gait-wave27c-decay-seats** (clone w27c-agent) — branch exists, ZERO commits
  (HEAD = wave26's 6efb3ef0). Nothing to merge.

## 6 · OUT OF SCOPE (observed on the shared origin, not part of this integration)

`agent/walk-campaign-doc` (e739db9c — campaign synthesis doc, "no new claims"; mergeable
anytime as docs at the lead's discretion), `agent/bone-id-v3-companion` (554dd62a — the
v3 bone-ID arbiter the matter lanes checkout data FROM), `agent/mount-reconciliation`
(8deef67f), `agent/posture-cap-provenance` (a8887424), `agent/quadruped-window`
(4b2bdb27), `agent/local` (1881334f), plus the `buffy/*`, `codex/*`, `lane/*`, `astra/*`
namespaces. If any of these lands later, re-run the §4 conflict check — notably
mount-reconciliation overlaps 2.4's receipt dir, and bone-id-v3-companion is a data source
the matter lanes pin against.

---

*Manifest by agent/integration-manifest-20260921 · every sha and edge above re-measured
2026-09-21 · trailer below per the house law.*

Agent: GLM 5.3
