# THE TRIANGLE CARRIER — triangles are matter elements; the CA over them

*2026-08-23. Rule 0 shell: named before build, per the law.*
**Provenance flag:** operator data recorded verbatim below is his words (2026-08-23 session);
where a clause is synthesis from repo data it is flagged. "k with memory" is MY framing of
his timeline law — not yet his words; it stays flagged until he signs it.

## WHY TRIANGLES (the geometry, one free mode)

A triangle is the smallest element that is rigid in its own plane and still has **one**
free mode left: area. That one mode is the CA variable — strain scalar `aᵢ/A₀` plus
stiffness `k`. Three vertices, one number per element: the same one-buffer doctrine as
the splat era's 14 variables (`web/renderer/splat.wgsl`, top of file — pos3+opa / col3+
_p0 / scale3+_p1 / quat4 = 16 f32, derived never stored), with triangles as elements.
His words: *"you need a triangle in order to create this spring"*; the CA is
*"a calculus equation brought to a footstep"* — finite-difference elasticity on a
triangle lattice.

## THE SHARED-EDGE LAW

Solidity is a **shared-edge law**: springs live on edges, not vertices, and there is no
long-range part. The edge spring IS RESISTANCE at element scale (`THE_LIGHT_SEED`: M=0
the bond, M<0 the wall). Neighbors do not tear — they spring; elasticity is the bond law.

## THE SPRING GATES (before any build)

- **A₀ from import** — bit-exact chain already proven: TEST B2 readback |duv| = 0.0 exactly
  (`docs/THE_UV_METHOD.md`); `THE_TRANSLATION` Run 3 mass err 0.000%, iner ≤1.921% vs tol 2%.
- **k derived, never picked** — precedent in-repo: M3 hip bond
  `k_rot = W·0.0166 / 0.0175 = 23.5 N.m/rad` from single-support moment + deflection bound
  (`tools/kernel_walk.py` L17–20); the joint must LOOK rigid on the scale the stability
  margins were derived at. Door-material tag (THE_TRANSLATION law 4) is the other source.
- **Band clamp, derived like THETA_CLAMP 0.24 rad** — the strain update is a linearization
  valid only inside its band: `|sin t − t|/t ≤ 1% → t ≤ 0.244` (`LightEngine/kinematic/
  dynamics.py` L172–174); beyond the band it was measured wrong **in kind, not degree**
  (unclamped corrections scrambled small-link orientations into pi-flips). The triangle
  analog: k derived at A₀ stays ≤1% accurate while `|aᵢ/A₀ − 1|` is inside a named band;
  beyond it the clamp fires and the membrane says so — a static hold that trips the clamp
  is a falsifier, not a feature.
- **Energy gate** — spring PE + KE drift < 1% through his existing falsifier (THE_
  TRANSLATION's conservation contract applies to the CA field exactly as it did to packets).

## k WITH MEMORY (flagged synthesis)

Loaded triangles hold their loading in stiffness: a type is a modifier shaped by a
timeline (`THE_LIGHT_SEED`, verbatim). The timeline lives INSIDE the membrane — no second
state buffer. This is the genuine contribution beyond textbook FEM, and it stays flagged
until he signs it in his words.

## THE UE DOOR (adaptation device)

Loads + displays only; **computes no truth.** Contract: bijection ledger
(triangles_in == elements_created), vertex checksum vs an independent parse, mass/inertia
inside `THE_TRANSLATION` tolerances. Dumb pipe by design: the known local distortion is in
OUR export C++ — `/100` + Y/Z axis swap baked into `SetSplatNodeTransform` (`Chimera/
Plugins/MLSLabsRenderer/Source/MLSLabsRenderer/Private/GaussianSplatingRendererLibrary.
cpp` L530–540), with no test against a known pose — that is ours to fix/test, not the box's
fault; UE's internal rendering is exactly what we never ask for truth from.

## STATEMENT / PREDICTION / FALSIFIER

- **STATEMENT:** finite-difference elasticity on the triangle lattice reproduces the shared-
  edge bond law of `THE_LIGHT_SEED` to tolerance, with k derived (never picked) and A₀
  from import — triangles are matter elements, not a render mesh after translation.
- **PREDICTION:** first run = cad_bear at its proven import density: strain field under
  gravity matches the bond-law force read from M within named tolerance; static hold trips
  no clamp; energy gate <1%. (cad_bear because THE_TRANSLATION already proved its mass/
  inertia to the letter — the carrier is tested where the door's numbers stand.)
- **FALSIFIER:** any of — energy drift > 1%; band clamp fires on a static hold (k/A₀ wrong);
  a code path that edits mesh after translation to fix physics (`THE_TRANSLATION`'s own
  falsifier, still in force); ANY drift not produced by the sampler ⇒ **the box is a
  participant** — rebuild the membrane rather than trust the door.

## DECISION: KEEP UE (delegated judgment, flagged until he signs)

Keep UE as dumb pipe; do not build a second engine. The custom engine already exists in-repo
for everything that is truth (GPU field sim + kernel DSL + native wgpu viewer);
"make our own completely" restates what the repo owns and buys nothing new — display-side
months with zero bearing on the launch metric. UE 5.8 confirmed at source (`Chimera/
Chimera.uproject`, PCG plugin enabled). Snap points where this decision dies: (1) the
1M-element DISPLAY must hold inside OUR frame budget in our window (wgpu path already proven
for splats — triangle rasterization there becomes build work); (2) any drift not produced by
our sampler (box = participant, membrane rebuilt rather than door trusted); (3) standalone
shipping without engine dependency becomes a stated goal. Advanced-UE combination sides:
DISPLAY (Nanite shows imported meshes at any density — truth stays our elements; Lumen +
post feed the `U.light` seam already in `web/renderer/splat.wgsl`), AUTHORING (PCG generates
triangle fields that cross the door as authoring; World Partition streams import/display
regions only), OPERATOR-side (the genuine combinations: Sequencer-style tooling composing
LEVER tracks — f32 ∈ [0..1] per intent, behavior authored on inputs never state; net code
replicating levers + seed not state — `theDeterminism` ladder is ours, drift caught by this
doc's checksum falsifier; ML policies writing levers = operator device with an AI at the
wheel). PARTICIPANT LIST (falsifier fires): Chaos GPU sim / cloth / fracture truth, any
engine stepping of our state (`ChaosVehiclesPlugin` enabled in .uproject — same fence: it may
drive a displayed vehicle's wheels, never compute where matter goes). Gate for every feature:
no path from any of these into the element buffer; the lever/force law (M modifier) is the
only entry, per `THE_LEVERS.md`. Not integration-tested this session (no shell); each
gates through its own Rule-0 before build.

## KNOWN-POSE TEST SPECIFIED (algebra from source; no execution)

Full chain read end-to-end — both ends are OURS: `FGaussianSplattingSceneProxy` (`Gaussian
SplattingSceneProxy.cpp` L99–103) reads the component's Location/Rotation/Scale (UE cm) →
library call applies `/100` + axis swap (L536–538: `Translation.x = InTranslation.Y / 100.0;
y = −InTranslation.Z / 100.0; z = InTranslation.X / 100.0`; Scale remap `.x=.y, .y=.z,
.z=.x`) → native DLL. Load + update call sites: `GaussianSplattingComponent.cpp` L106–134.
Pre-derived expected table (component pose → GSR vector sent to the DLL):

| component (L cm / R deg pitch-yaw-roll / S) | GSR translation (m) | GSR rotation (rad) | GSR scale |
|---|---|---|---|
| (0,0,0) / (0,0,0) / (1,1,1) | (0, 0, 0) | (0, 0, 0) | (1, 1, 1) |
| (100,0,0) | (0, 0, +1.0) | — | — |
| (0,100,0) | (+1.0, 0, 0) | — | — |
| (0,0,100) | (0, −1.0, 0) | — | — |
| pitch = 90° | — | (π/2, 0, 0) | — |

Run spec: place a node at each pose in UE, capture the window, compare observed splat
position against this table. FALSIFIER SHARPENED: any failure lands in our proxy/library C++
(both ends of the pipe are ours per source read above) — an Ours bug to fix here; "the box is
a participant" fires only on drift NOT produced by the documented transform above. No free
numbers: every row is algebra from L536–538 + SceneProxy L99–103.

## SOURCE RE-CHECK + CONCRETE UE 5.x FEATURE MAP (continuation, no-shell)

Re-verified at source this session (not memory): the `/100` + Y/Z axis swap is in OUR export C++ — `GaussianSplatingRendererLibrary.cpp` **L529–536** (`x=InTranslation.Y/100; y=-InTranslation.Z/100; z=InTranslation.X/100`; Scale `.x=.y,.y=.z,.z=.x`), and the caller is read end-to-end — `FGaussianSplattingSceneProxy::UpdateSplatTransform()` reads component `Location/Rotation/Scale` (UE cm) → same library call → DLL. Both ends ours, so a known-pose failure = an Ours C++ bug until proven otherwise; "the box is a participant" fires only on drift NOT produced by this documented transform. Line refs corrected here: transform block L529–536 (not L536–538); `H_C` ~L88 of `tools/kernel_policy.py` (not the prior L74).
Concrete UE 5.x map, each gated "no path into the element buffer":
- **Nanite** — DISPLAY: virtualized geometry / per-pixel cluster streaming; shows imported triangles at any density without us authoring LODs. Truth stays our elements.
- **Lumen GI/Reflections** — DISPLAY: real-time light feeding the existing `U.light` seam in `web/renderer/splat.wgsl`; it lights, never owns.
- **PCG Framework** — AUTHORING: generates POINTS from spatial data (volumes/surfaces/meshes), GPU for perf; 5.7 Editor Mode + experimental Procedural Vegetation plugin. The concrete "static meshes in → triangles translated" mechanism, but per THE_TRANSLATION it authors IN only — ANY post-translation mesh edit is a violation, so our sampler is the sole field writer.
- **World Partition** — AUTHORING/streaming: streaming grid + one-file-per-actor + Data/HLOD layers streams DISPLAY/AUTHORING regions by camera position; never element state.
- **Netcode replication + ML agents** — OPERATOR: replicate levers+seed not sim state (`theDeterminism` ladder); ML policies write LEVERS ∈ [0..1] (operator device with an AI at the wheel); drift caught by this doc's checksum falsifier.
Uniqueness recheck 2026: nearest neighbors unchanged — Avalanche (GPU-resident), Houdini per-point attrs (offline), Flex/GEM (millions of points on GPU); concrete current academic neighbor = **Newton** (newton-physics, NVIDIA Warp + MuJoCo-Warp; Disney/DeepMind/NVIDIA) — GPU-resident and per-element but a differentiable robotics sim, NOT the welded one-buffer physics+picture+control with CPU levers. No shipping engine has the weld; UE5 Chaos "GPU simulation" is still the part most likely to be mistaken for this (offloads stepping, does not hand over the clock).

## T2 FIRST CA RUN — PRE-REGISTERED (continuation-4, before build)
Lattice from `models/cad_bear/cad_bear.glb` via `cad_sample.load_glb_triangles` (the bit-exact import chain): 59,712 tris / ~30.8k verts, 19 watertight per-part shells; shared-edge adjacency WITHIN a part only (parts share no vertices — cross-shell coupling is the fold walk's job, not the CA's; stated as structure, not apology). A₀ per triangle at parse: |e1×e2|/2.
Space and scale, all from `LightEngine/constants.py` (no SI this run): vertices scaled to walk space by S = R_BOND / e_med where e_med = median shared-edge length of the parsed lattice (named ratio — flagged synthesis); vertex mass m = 1 each (the seed's dimensionless convention); k_area = K_BOND/R_BOND² — the bond spring stiffness constants.py already derives in its GAMMA_W block, i.e. derived-never-picked and zero new free numbers.
Update rule: one area mode per triangle — F(v) = −k·(A/A₀−1)·∇A, ∇A finite-difference-checked against the analytic signed-area gradient at build time ("a calculus equation brought to a footstep"); symplectic Euler, dt = DT from the seed.
RUN A (bond-law match, static): per shared edge, CA stiffness slope vs the M=0 bond algebra exactly as in `LightEngine/modifier.py` (`fb = kb(r−rb)/(rb·r)`, linearized at r=R_BOND: slope K_BOND/R_BOND²). Gate: relative error ≤ 1% (flagged synthesis tolerance — same number as the energy gate).
RUN B (liveness + energy, live): from rest at import pose under the fold walk read by `compute_forces_mod` (GPU, octree rebuilt per tick — a live frame's tree moves with its points; honesty line), 1000 ticks. Gates: spring PE + KE drift < 1%; finiteness (no NaN); max |A/A₀−1| PRINTED as the honesty line that feeds the band-clamp sub-gate (the number is still derived after this run, not named here).
FALSIFIER inherits the membrane shell: energy drift > 1% / clamp on a hold / NaN / any code path that edits mesh after translation. Cad_bear because THE_TRANSLATION Run 3 stands to the letter (mass err 0.000%, iner ≤ 1.921%).

## PARALLEL OCTREE — SFC-keyed tree build (operator directive, Rule-0 shell)
The operator's algorithm, verbatim: "map your points to integer coordinates, then compute their 3D Hilbert or Z-order keys; 1) sort those keys with a parallel radix sort; 2) run a prefix sum to create leaf cells; 3) link the leaves upward into internal nodes using GPU kernels."
Contract: output = `bh_draw`'s exact tree-dict format ({sorted_pos, sorted_idx, cell_min, cell_max, cell_com, cell_mass, cell_child, cell_is_leaf, cell_leaf_start, cell_leaf_count}) so `compute_forces_mod` consumes it UNCHANGED — the folded walk is referee infrastructure (T4 measured on it; `agent_logs/envelope_million.json` stays comparable). A build that changes the walk to fit its own tree violates the door contract.
- STATEMENT: an SFC-keyed parallel octree build produces a valid nested octree in that format, at any point count the GPU holds.
- PREDICTION: on two reference scenes — cad_bear's 30,768 walk-space positions and T4's exact 1M uniform scene (same seed/scene as `envelope_million.json`) — per-point forces from the new tree vs `build_octree` at theta=DEFAULT_THETA(0.3), leaf_size 16 agree ≤ 1% relative (flagged synthesis tolerance); structural invariants: every child box ⊂ parent box, bottom-up com/mass recompute matches stored values to float32 epsilon, no leaf over 16.
- FALSIFIER: any of — non-finite or walk exception; nesting violation; com-mass mismatch beyond float32 epsilon; force rel diff > 1% on EITHER scene. Until it passes, NO build may claim per-tick tree rebuild at scale — the known CPU-visible cost in RUN B is exactly this single-threaded octree (source-verified: `LightEngine/bh_draw.py` kernels carry no prange; the walk itself is one-thread-per-point GPU and does not show in CPU usage). Do NOT touch `bh_draw.py` itself — new builder lives beside it, old one stays referee.

### MEASURED RESULT (continuation-10) — FALSIFIER FIRES; root cause named, not papered over
Built the corrected SFC builder (`LightEngine/bh_sfc.build_octree_sfc`) per the verbatim algorithm and ran `tools/gate_octree_sfc.py`. Two bugs found+fixed on the way (both real): (1) the occupancy-bump loop never terminated on coincident data — cad_bear has **3,431 exact float32 duplicates** whose max run plateaus at 43; a grid can never split identical points, so "bump B until ≤16" overflows past B>1024. Fix: refine until occupancy **plateaus** (residual = true coincidence), mirroring `build_octree`'s own `n_nonempty==1` oversized-leaf guard — no free number. (2) com/mass/min/max were written into GLOBAL `cell_*` slots using LOCAL parent ids (only correct at the root where offset=0) → root mass 281≠500, nesting broken; fixed with a local→global map.
After both fixes the tree is STRUCTURALLY VALID on both scenes (partition=n exact, root mass exact, zero nesting violations, com/mass to f32 eps). The gate still FIRES on force:
- cad_bear: **9.04%** rel vs `build_octree` (gate ≤1%).
- T4-1M uniform: **2.97%** rel vs `build_octree` (gate ≤1%); invariants all pass here.
Root cause, measured against an O(n²) ground-truth sum (`dbg`, n=2048/4096): the REFEEER is ~0.1% from truth at θ=0.3; my SFC tree is **~24× less accurate** (θ=0.3: ref 0.144% vs sfc 3.45%; both →0 as θ→0, so mine is a VALID convergent Barnes-Hut tree, just with a ~24× higher truncation constant). Cause: uniform-depth fixed-grid nodes make different (s,d) theta decisions than the adaptive referee — inherent to the operator's verbatim algorithm, not a fixable defect without making it adaptive. Build cost also WORSE, not better: T4-1M sfc 18.2 s vs ref 2.1 s (uniform grid builds deep structure in sparse regions the adaptive tree skips → 2.06M cells vs 293k); cad_bear sfc 0.79 s vs ref 0.34 s.
**Verdict:** T13-as-specified does NOT hold — the SFC build is neither a ≤1% drop-in for `build_octree` nor faster than the single-core BFS it was meant to replace. The "one core" pain is NOT solved by this construction. Per membrane: NO per-tick-rebuild-at-scale claim until it passes; it does not pass. Operator fork (his call, I do not pick): (a) keep `build_octree` as referee and make ITS build parallel/GPU instead of swapping trees; (b) run the SFC tree at a lower θ for accuracy (changes THE law's knob — not a free param); (c) accept the CPU-build cost. Gate + builder stay on disk as the honest record; `agent_logs/gate_octree_sfc.json` holds the numbers.
