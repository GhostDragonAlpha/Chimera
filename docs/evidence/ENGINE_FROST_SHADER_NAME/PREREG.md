# PREREG — engine-frost-shader-name-01 (gen 1)

- Agent: subagent-worker-03. Slot 8, worktree E:\ChimeraWork\slot-08, branch
  astra/tasks/engine-frost-shader-name-01, base
  51864412d2ffcc46acd89a3dc136e7e3c7a3350f (HEAD==base verified, clean, index
  6165 files, before any work). Realizes the PR #79 recorded adjacent defect,
  reviewer-verified: `load_frost` reads bare `shaders/render_tri_frost.spv`
  (engine.cpp:4891-4892 at this base) while the derived shader build emits
  `render_tri_frost.frag.spv`.
- Scope discipline: the task record scopes `ChimeraEngine/CMakeLists.txt`,
  which does not exist at base — the shader build rules live in
  `ChimeraEngine/engine/CMakeLists.txt`, outside this task's scopes. No build
  rule change is needed anyway: the derived build already emits the
  stage-suffixed name. The fix is LOADER-SIDE ONLY (engine.cpp), inside scope.
- SOURCE+CPU lane: the live service is never contacted; no GPU admission is
  requested. Runtime frost load is NOT_TESTED-with-reason (recorded in
  RESULT.md).
- This commit contains the PREREG ONLY. No fix, no checks, no results.

## MEMBRANE (packet verbatim, thresholds concrete below)

- STATEMENT: the frost render shader name contract is INCOHERENT at base —
  the loader reads a bare name that no clean derived build artifact carries,
  so frost cannot load without hand-staging.
- PREDICTION: after the loader reads the name the sibling pattern and the
  derived build already produce, a clean private build loads frost from
  derived artifacts alone.
- FALSIFIER: any hand-staging needed post-fix, or a sibling shader's name
  contract broken by the fix.
- THRESHOLD POLICY: every check below is a counted N/N row; any miss is
  REPORTED as a fired falsifier, never patched around. The protected shared
  build dir `ChimeraEngine/engine/build/` is never touched (all builds in the
  slot-private `.tmp/engine_build`).

## THE NAME CONTRACT AT BASE (measured before the fix; the sibling table)

Every shader read in engine.cpp at base, classified:

| Family pattern | Reads (engine.cpp lines at base) |
|---|---|
| vert/frag — `<stem>.<stage>.spv` (9) | render.vert.spv 1242, render.frag.spv 1243, render_tri.vert.spv 1261, render_tri.frag.spv 1262, render_tri_edge.frag.spv 1281, render_tri_shadow.frag.spv 1288, render_tri_shadow.vert.spv 1291, floor.vert.spv 1296, floor.frag.spv 1299 |
| compute — bare `<stem>.spv` (6 read sites; 8 logical shaders) | compute.spv 1244, sort.spv 1245, skin.spv 1246, membrane_demo.spv 4151, hinge.spv via 2088 (`set_hinge`), and the compute-pipeline helper 3692 (`w_make_pipeline`) whose call sites pass bare names: gait.spv, volp.spv, water_depth/color/occ/vis.spv, frost_decode.spv, joints.spv |
| **violator (1)** | **render_tri_frost.spv 4891 — a FRAG source read under the COMPUTE naming rule** |

CMakeLists (engine/CMakeLists.txt:56-62, outside scope, unchanged): comp/glsl
sources emit `<stem>.spv`; vert/frag sources emit `<name>.spv` KEEPING the
stage extension. `render_tri_frost.frag` therefore derives to
`render_tri_frost.frag.spv`.

CHOSEN FIX (by contract ownership): the build owns the derived naming (the
2026-09-03 stale-spv incident made the manifest DERIVED and declared it
matching read_file names); the one mismatching read is the loader. Fix =
read `shaders/render_tri_frost.frag.spv` (the established vert/frag pattern
of its own graphics family; no third pattern invented). Two-line change:
the read string and its missing-file message.

## PREREGISTERED CHECKS (stated before the fix)

- **C1 source trace (16/16 classified)**: enumerate every shader read site in
  engine.cpp at base (the 16 sites tabled above); classify each into
  vert/frag-suffixed vs compute-bare; assert exactly 1 violator pre-fix and
  0 violators post-fix; assert the post-fix diff touches ONLY the frost read
  line + its message line.
- **C2 manifest coherence (17/17 post-fix; defect reproduced pre-fix)**:
  derive the CMake output manifest from `shaders/` sources with the same
  rules (comp/glsl → `<stem>.spv`; vert/frag → `<name>.spv`); assert PRE-fix
  that the loader-expected bare name is ABSENT from the manifest (the
  incoherence, reproduced); assert POST-fix that EVERY engine shader read
  name resolves into the manifest (17 read names incl. the 8 compute-helper
  logical shaders).
- **C3 clean-build compile without hand staging (4/4)**: configure+build the
  slot-private `.tmp/engine_build`; assert (a) the build's own pipeline
  (glslc via CMake) produced `Release/shaders/render_tri_frost.frag.spv`,
  (b) NO `render_tri_frost.spv` (bare) exists anywhere under the build's
  shader output, (c) the fixed loader name == the derived file name,
  (d) sha256 of the derived file recorded (no staged/stale file involved —
  build dir was configured fresh in this slot).
- **C4 sibling contract preserved (16/16)**: post-fix, all 16 pre-existing
  read names are byte-identical to base and each still resolves in the C2
  manifest.

Verdict rule: C1 16/16 + 1→0 violators, C2 17/17 with the pre-fix absence
demonstrated, C3 4/4, C4 16/16 — ALL must hold; any miss = the falsifier
fired and is reported (never patched).

## METHOD

1. checks/check_names.py (stdlib-only, committed with the fix): runs C1+C2
   pre- and post-fix against the base and worktree texts and the derived
   manifest; writes `checks/c1_source_trace.txt`, `checks/c2_manifest.txt`.
2. Fix (engine.cpp two lines). Fresh configure+build in `.tmp/engine_build`.
   checks script C3+C4 → `checks/c3_clean_build.txt`, `checks/c4_siblings.txt`.
3. RESULT.md: verdict, reproduction commands, source identity (git sha +
   sha256s), runtime NOT_TESTED-with-reason, limitations.
4. Commit chain (trailer `Agent: subagent-worker-03`), push no-force, PR into
   astra/gait-capture, submit_review with exact HEAD.
