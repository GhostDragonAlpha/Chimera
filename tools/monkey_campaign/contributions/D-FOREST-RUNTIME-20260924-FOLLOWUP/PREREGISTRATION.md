# PREREGISTRATION — D-FOREST-RUNTIME-20260924-FOLLOWUP (correction attempt)

Card: `D-FOREST-RUNTIME-20260924-FOLLOWUP` (planning IDs F02/F03/F04; depends on
D-FOREST-RUNTIME-20260924 = merged PR #120 head `86d0d8d461ea50420c053681f7e297343e3fbb97`).
Correction attempt `0f29ec07434840939d0b53c4bc5a30b4`, arrival
`arrival-5fa3f57a83574a62b674a3f9d8fdd873`, criteria sha256
`be7394fa3f7f02f43e67a271926342fb994c1a2042d58791c8cac75fe505a7c3`.
Written BEFORE any probe in this workspace (Rule 0). This is a PLACEMENT +
COMPILE-EVIDENCE correction of the verified finding
(msg-90831766cb2645538f322ab949ea1c49, arrival-876e63bf9dbb44a8b10c5b546f783e9b);
the prior attempt `95df22c9a08e492d97df79ce838d6f63` stays untouched (read-only
source of its artifacts).

## SUBJECT (verified finding + predecessor facts)

- OPERATIONAL LEAD VERIFICATION (pre-publication): the prior proposed.patch is
  ill-formed C++ — the helper member-function definitions `terrain_model_y` and
  `contact_normal` are inserted INSIDE `gap_of`'s function body; g++ 15.2
  rejects the patched `gait_controller.hpp` ("a function-definition is not
  allowed here", exit 1). No shipped check compiled the modified header.
- Verified GOOD (must be preserved): surface-law content of
  `terrain_surface.hpp`; oracle agreement (worst height 0.0 m EXACT over 2081
  points, worst normal component 3.469e-18, bars 1e-9/1e-12); 10/10 unittest.
- Pinned facts (re-verified by reading the play repo read-only, this attempt):
  `ChimeraEngine/engine/gait_controller.hpp` @ `33e7a444fe7b4c35aa99afe7ef898046877025b4`
  = blob `5863348f2deef1f01e3cf761d0c4151a10035a6d`; `class GaitWalker` at :35;
  `ContactPoint` nested at :56; member anchor line at :94; `double gap_of(const
  Evaluation& e,size_t k)const{` at :635; the engine compiles with include dir
  = the engine dir itself (CMakeLists `target_include_directories(chimera_engine
  PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}")`); the quoted-include chain of the
  gait header is `coupled_articulation.hpp` -> `earth_environment.hpp` ->
  `force_models.hpp` -> `../native/viewer3rd/json.hpp` (no Vulkan in this
  chain), so a bare `-fsyntax-only -I <engine>` TU is the minimal faithful
  compile of the modified header.
- The prior include seam placed `#include "terrain_surface.hpp"` INSIDE
  `namespace chimera::multibody` (lead anomaly: legal-but-brittle nesting);
  this correction normalizes it to file scope.

## STATEMENT (a theory that can lose)

Moving the two helper definitions to proper CLASS scope in `gait_controller.hpp`
(inserted immediately before `double gap_of(`), moving the
`terrain_surface.hpp` include to file scope, and leaving the gap/contact/tangent
ternary edits byte-identical in their inactive arms produces a patch that
applies to the pinned blob AND compiles as a C++ translation unit
(`g++ -std=c++17 -fsyntax-only`, exit 0), while the compiled surface service
reproduces the prior oracle-parity evidence exactly. A `-fsyntax-only` check of
the MODIFIED header, added to the shipped checks with a negative control,
prevents this class of defect from regressing.

## PREDICTION (not yet measured in this workspace)

1. The regenerated patch applies cleanly to the pinned blob (`git apply
   --check`) and touches exactly the same two files; the new-file
   `terrain_surface.hpp` bytes are IDENTICAL to the prior attempt's
   (sha256 prefix 9413a821) — the surface law is untouched.
2. The modified `gait_controller.hpp`: (a) contains no function definition
   inside any function body (helpers sit at class scope before `double
   gap_of(`); (b) compiles standalone: `g++ -std=c++17 -fsyntax-only -I
   <engine-dir> gait_controller.hpp` exits 0; (c) the four original plane
   expressions + `plane_model_y_=plane_world_y_-shift_[1];` remain verbatim.
3. Compile-vs-oracle parity reproduces the frozen numbers: worst height error
   0.0 m (exact) over 2081 points, worst gradient 0.0, nodes exact, worst
   normal component ≤1e-15 (prior: 3.469e-18); plane degeneracy exact
   (constant grid: h=0, grad=(0,0), n=(0,1,0)); gap-law constant-grid delta
   0.0 measured FROM COMPILED h values (replacing the prior tautological
   self-comparison); tangent identity axes 0/2 exact; axis-1 refusal named.
4. Extent law: closed boundary serves (i=1 at ±20 edges + corner), ±20+1e-7
   flags outside, height query just outside refuses `gait_outside_extent`.
5. The new compile check BITES: compiling a deliberately ill-formed stub
   (function definition nested in a function body) exits nonzero (negative
   control recorded in checks.json).
6. Physics-symbol guard green (no changed line touches mu_/kTouch/
   kReleaseBand/friction_solve/substeps/dt); no trunk machinery (Stage 1).
7. The unittest suite passes 13/13 (10 prior semantics + compile-check tests,
   order-independent on a fresh directory).

## FALSIFIER (named before the run)

- FC1: the regenerated patch fails to apply, changes scope beyond the two
  declared files, or alters `terrain_surface.hpp` by one byte;
- FC2: the modified header fails `g++ -std=c++17 -fsyntax-only` (exit != 0), or
  the negative control compiles clean (check does not bite);
- FC3: any oracle-parity number regresses vs the frozen bars (height >1e-9,
  normal >1e-12, nodes not exact, degeneracy/extent not exact);
- FC4: a verbatim plane expression lost, a physics symbol touched, trunk
  machinery added, or an overclaim of engine acceptance (compile check
  verifies TU well-formedness of the modified header only; no engine run, no
  walk, no W10 readiness — all runtime/visual gates stay PENDING).

## BOUNDS

CPU-only; g++ invocations bounded (one `-fsyntax-only` TU + one driver TU
compile + one tiny negative-control TU, each ≤120 s); Python checks; read-only
against E:/ChimeraWork/monkey-play-20260924 (git archive of the pinned subtree
into a temp scratch dir); prior attempt workspace read-only; ZERO writes in
E:/PythonChimera; no GPU, no engine launch, no training, ≤16 MiB new output.
