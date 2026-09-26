# D-FOREST-RUNTIME-20260924-FOLLOWUP — correction: insertion site + compile evidence

**Verdict: the reviewed patch's ill-formed C++ (helper member-function
definitions inside `gap_of`'s body) is corrected — helpers now sit at proper
class scope immediately before `double gap_of(`; the surface include moved to
file scope; the MODIFIED `gait_controller.hpp` is now compiled as evidence
(`g++ -std=c++17 -fsyntax-only`, exit 0) with a negative control proving the
check bites (exit 1, "not allowed here"). The compile evidence surfaced ONE
further masked defect — the surface header's private default constructor made
the `TerrainSurface terrain_;` member un-constructible — fixed minimally by
moving that constructor to public access (no law change, oracle parity
reproduced bit-exactly). Surface-law oracle agreement reproduced EXACTLY as
reviewed: worst height 0.0 m over 2081 points, worst normal 3.469e-18. No
engine run, no trunk contact; W10 readiness and all runtime/visual gates
remain PENDING.**

- card: `D-FOREST-RUNTIME-20260924-FOLLOWUP` (planning ids F02/F03/F04; parent
  D-FOREST-RUNTIME-20260924 = merged PR #120 head `86d0d8d461ea50420c053681f7e297343e3fbb97`)
- correction attempt: `0f29ec07434840939d0b53c4bc5a30b4`, arrival
  `arrival-5fa3f57a83574a62b674a3f9d8fdd873`; criteria
  `be7394fa3f7f02f43e67a271926342fb994c1a2042d58791c8cac75fe505a7c3`
- corrects the verified finding on attempt `95df22c9a08e492d97df79ce838d6f63`
  (lead-verify-20260926; inbox msg-90831766cb2645538f322ab949ea1c49) — that
  attempt and its artifacts are untouched.
- PREREGISTRATION.md for this correction was frozen BEFORE any probe; one of
  its predictions honestly LOST (see "Prediction that lost" below).

## What changed vs the reviewed candidate (and why)

1. **Helpers to class scope (THE reviewed fix).** `terrain_model_y` and
   `contact_normal` were inserted inside `gap_of`'s function body
   (ill-formed). They are now two member-function definitions at class scope,
   inserted immediately BEFORE `double gap_of(` (patch hunk `@@ -632,6
   +637,8`). Token content unchanged; only the insertion site moved.
2. **Include seam to file scope.** `#include "terrain_surface.hpp"` was placed
   inside `namespace chimera::multibody` (legal but brittle nesting — lead
   anomaly); it now sits at file scope after the std includes, before the
   namespace opens (hunk `@@ -6,6 +6,7`).
3. **NEW compile evidence (the reviewed gap):** `header_compile_check`
   materializes the pinned engine subtree (`git archive` of commit
   `33e7a444`, LF-forced via `-c core.autocrlf=false -c core.eol=lf` — the
   repo's `.gitattributes` `* text=auto` otherwise smudges CRLF), applies
   `proposed.patch`, and runs
   `g++ -std=c++17 -fsyntax-only -I <engine-dir> <engine-dir>/gait_controller.hpp`
   — the same include-path law the engine's CMake uses
   (`target_include_directories = the engine dir`). Required: exit 0.
   `compile_check_bites` feeds the compiler the reviewed defect shape (a
   member-function definition nested in a member-function body) and requires
   exit != 0 with the named error.
4. **Masked defect found by the new evidence, fixed minimally:** with helpers
   at class scope the header STILL failed to compile —
   `TerrainSurface::TerrainSurface()` is private in the reviewed
   `terrain_surface.hpp`, and `GaitWalker`'s new member `TerrainSurface
   terrain_;` could never be constructed (g++ 15.2: "TerrainSurface() is
   private within this context"). The ill-formed helper placement had masked
   this because no check ever compiled the modified header. Fix: the default
   constructor moves to public access in `terrain_surface.hpp`. This is the
   ONLY byte change to the reviewed surface header (verified by diff: the
   constructor line + an explanatory comment; every law token — grid,
   diagonal, interpolation, gradient, normal, extent, spacing refusal —
   byte-identical). Safety: an empty surface (nx_=0, half_=0) refuses every
   height query by name (`terrain_query_below_grid`) and is only queried once
   `from_arrays` succeeded (`terrain_active_`).
5. **Prior minor anomalies also addressed:** the tautological Python-side
   "gap law |delta|=0" self-comparison now measures the constant-grid gap
   delta FROM compiled h values (`gap_law_constant_grid_delta` = 0.0, bitwise
   vs the plane arm); the unittest suite is order-independent on a fresh
   directory (every class materializes the artifacts it needs; fresh-run
   verified: OK, 1 honest skip for not-yet-existing evidence).

Unchanged, per the verified finding ("preserve them"): the gap/contact/tangent
ternary edits with the ORIGINAL plane expressions verbatim in the inactive
arms, the recipe-gated `terrain_grid` activation, the tangent degenerate-axis
named refusal, the member seam, the loader seam, and the physics-symbol guard.

## Independent checks (exact commands, CPU-only)

```
python -B implementation.py all                  # exit 0, all_ok true
python -B -m unittest test_implementation -v     # Ran 15 tests, OK (4.0 s)
```

- patch applies to the pinned blob `5863348f2deef1f01e3cf761d0c4151a10035a6d`
  @ `33e7a444` (git apply --check, re-hashed this attempt); scope exactly the
  two declared files; new-file `terrain_surface.hpp` blob `d24b4eb`;
  `proposed.patch` sha256
  `e4dee59272e531d297e974a079c8dcfe401123713d7c421b52266f53bfebfce9`.
- **Compile evidence:** `g++ -std=c++17 -fsyntax-only -I <tree>/ChimeraEngine/engine
  <tree>/ChimeraEngine/engine/gait_controller.hpp` (tree = pinned subtree @
  33e7a444 + proposed.patch, in a temp scratch dir) → **exit 0** (g++ 15.2.0,
  MinGW-Builds x86_64-posix-seh; sole output a benign `-Wpragma-once-outside-header`
  warning). Recorded in full (command, compiler, stderr tail) in
  `evidence/checks.json` under `header_compile_check`.
- **Negative control:** same invocation shape on
  `build/ill_formed_negative_control.cpp` (the reviewed defect shape) → exit 1,
  "a function-definition is not allowed here" present; recorded under
  `compile_check_bites`.
- **Oracle parity (reproduced bit-exactly vs the reviewed numbers):** the
  shipped surface header compiled (one TU) and compared against the frozen F02
  oracle over 2081 points (1681 grid nodes + 400 deterministic interior):
  worst height error **0.0 m**, worst gradient **0.0**, nodes exactly equal,
  worst normal component **3.469446951953614e-18** (bars 1e-9 / 1e-12). The
  oracle itself is now COMMIT-PINNED: `terrain_query.py` + siblings
  materialized read-only from play-repo commit
  `a2895755d009f8afc78078f57dc5c3c3819ef74a` (the worktree no longer carries
  the files); sha256s recorded in `evidence/checks.json` →
  `oracle_provenance` (`terrain_query.py`
  `b1e244b8843671afc29af530c4725bf812ffd5f8967130f0202792aeb7a8cce1`).
- plane degeneracy (constant grid): h=0, gradient=(0,0), normal=(0,1,0)
  EXACTLY at 5 sampled points; gap-law constant-grid delta 0.0 (measured from
  compiled h); tangent identity exact for axes 0/2; axis-1 refused by name.
- extent law: closed boundary serves (±20 edges + corner), ±20+1e-7 flags
  outside, height query just outside refuses `gait_outside_extent`.
- physics-symbol guard green (no changed line touches mu_/kTouch/
  kReleaseBand/friction_solve/substeps/dt); no trunk machinery (token scan) —
  Stage 1 law preserved.

## Prediction that lost (preregistration FC1, honestly recorded)

The frozen preregistration predicted the new-file `terrain_surface.hpp` bytes
would be IDENTICAL to the reviewed candidate. They are not: the compile
evidence this correction adds proved the reviewed header could not be used as
a `GaitWalker` member at all (private default constructor). The prediction
lost for a real, named reason; the minimal public-ctor fix above was applied
and the law re-proven against the oracle bit-exactly (0.0 m / 3.469e-18 — the
same numbers the lead independently reproduced), which is precisely the
preservation the card demands. No other prediction was falsified.

## Honest boundary (preserved gates)

The compile check proves TU well-formedness of the modified header under the
engine's include path — NOT engine integration. NOT done here, all still
PENDING: full engine TU-set build, the recipe actually carrying `terrain_grid`
(grid data feeding is an integration step), the collision query route (parent
S1-3), render binding + zero normal-hygiene lines (S1-4), any engine walk
replay (A1 byte-identity of the frozen plane walk), W10 scene readiness, all
runtime and visual gates. Trunk contact remains Stage 2.

Environment: Windows x64, CPython 3.14 + g++ (MinGW 15.2.0). Read-only against
E:/ChimeraWork/monkey-play-20260924; scratch trees in temp dirs and `build/`;
prior attempt workspace untouched; zero writes in E:/PythonChimera.
