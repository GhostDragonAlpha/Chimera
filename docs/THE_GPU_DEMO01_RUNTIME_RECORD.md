# GLM-GPU-DEMO-01 runtime record

## Preregistration

The governing statement, predictions, and falsifiers are in
`docs/THE_GPU_DEMO01_PREREGISTRATION.md`. This record keeps CPU, GPU,
runtime, visual/DYAD, and human verdicts separate.

## Build

- Checkout: `C:/Users/allen/AppData/Local/Temp/opencode/chimera_pub`
- Branch at inspection: `astra/gait-capture`
- Build directory: `C:/Users/allen/AppData/Local/Temp/opencode/chimera_build_gpu_demo_msvc`
- Protected `ChimeraEngine/engine/build/`: not used.
- Generator/toolchain: Visual Studio 17 2022, x64, MSVC 19.44.35228.0.
- Vulkan SDK: `C:/VulkanSDK/1.4.328.1`.
- Build command:
  `cmake -S C:/Users/allen/AppData/Local/Temp/opencode/chimera_pub/ChimeraEngine/engine -B C:/Users/allen/AppData/Local/Temp/opencode/chimera_build_gpu_demo_msvc -G "Visual Studio 17 2022" -A x64 -DVULKAN_SDK=C:/VulkanSDK/1.4.328.1`
  followed by
  `cmake --build C:/Users/allen/AppData/Local/Temp/opencode/chimera_build_gpu_demo_msvc --config Release --parallel 4`.
- Latest executable SHA-256:
  `30982A1C13055BC623D1AE82DFDB9B1EF9ADD3A6D948BBF424D138B49D7C3B82`.
- Latest engine-built shader SHA-256 (`Release/shaders/membrane_demo.spv`):
  `71B5F8D37ACFF921EA249C74ADE6D4074D79EA80D39BF03D66488F1C47C3898F`.
- The first runtime attempt exposed a concrete filename defect: CMake emitted
  `membrane_demo.spv`, while the controller requested
  `membrane_demo.comp.spv`. The source now requests the emitted filename.

## Runtime bring-up

The firewall prompt was allowed. Port 8091 was checked free before each
isolated launch. The only controlled processes were isolated executable PIDs
from the build directory; Alan's engine was not controlled.

Launch command:

`C:/Users/allen/AppData/Local/Temp/opencode/chimera_build_gpu_demo_msvc/Release/chimera_engine.exe 8091 --no-restore 1280 720`

The executable survived initialization, opened its HTTP listener, and
reported stable frame output around 55--56 FPS at 1280x720. The selected
Vulkan device was not printed by this engine path, so RTX identity is NOT
claimed by this record.

A B2 upload through `/membrane_demo_bin` succeeded. Initial status:

- energy `2.625` J;
- centre `[0, 0, 0.125]`;
- centre force approximately `[0, 2.98023224e-08, -0.428571433]`;
- `accepted_state_id=17560123212910228982`;
- material snapshot reported `gamma_admitted_f64=1`,
  `gamma_uploaded_f32=1`, unit `J/m^2`, and `wu_to_m=1.0`.

A single GPU step succeeded: iteration/accepted count became 1, centre z
`0.123999998`, energy `2.62457323` J, and the state ID changed. A frame
capture returned PNG bytes (3,687,468 bytes in one run).

## Runtime findings

The first runtime control sequence found and preserved two defects:

1. The demo shader filename mismatch caused init failure before the fix.
2. Gamma re-admission updated the GPU gamma buffer but did not immediately
   refresh the reported energy/force, and reset did not restore the initial
   material. These were corrected in the source by re-evaluating the accepted
   buffer after admission and restoring the initial gamma/snapshot on reset.

After that correction, a later control attempt caused an access violation in
`VCRUNTIME140.dll` while servicing the demo upload/control request. Windows
Application Error event 1000 recorded exception `0xc0000005` for the isolated
`chimera_engine.exe`; the process was not Alan's engine. The exact faulting
source line has not been established. Therefore the post-correction gamma,
reset, rejection, and fixed-state doubling controls are **NOT TESTED**.

The earlier pre-correction controls are retained only as diagnostic evidence:
positive-gamma single-step passed; the earlier gamma-zero control showed
stationary geometry; however the earlier fixed-state gamma-doubling result was
invalid because admission status did not refresh, so it is not a PASS.

## Verdicts

- CPU reference: PASS (existing `tools/membrane_window_demo.py` rerun;
  gamma 1 reaches 126 accepted steps and `stagnated`; gamma 0 is stationary
  with no accepted steps).
- Standalone Vulkan probe: existing published PASS remains unchanged; this
  record does not rerun or replace it.
- Engine build/shader compilation: PASS.
- Engine startup/listener: PASS for isolated instance on the allowed firewall
  path.
- Engine GPU material demo initialization: PASS once, before the later
  post-correction crash.
- Engine GPU single-step: PASS once, before the later post-correction crash.
- Gamma-zero, fixed-state doubling, reset after gamma change, rejection
  integrity after the correction: NOT TESTED.
- Full matched CPU/GPU relaxation trajectory: NOT TESTED.
- Compute-to-render state-id/capture hash certification: NOT TESTED.
- Visual capture comparison/DYAD: NOT TESTED.
- Human acceptance: NOT CLAIMED.
- GPU-driven engine milestone: NOT COMPLETE.

The remaining blocker is a concrete isolated Windows access violation during
post-correction control/upload handling. Do not infer RTX hardware identity,
full numerical parity, or window/DYAD acceptance from the successful startup,
initialization, or single-step observations.

---

# GLM-GPU-DEMO-02 — crash resolved, full runtime gate PASS (2026-09-09)

## Crash diagnosis (marker ladder, all evidence preserved)

Nine WER records (2026-09-08 22:39 through 23:59) showed the IDENTICAL fault:
`0xc0000005` at VCRUNTIME140.dll offset `0x1ddea` (inside `memcpy`), across
rebuilds — deterministic, hence logic/toolchain-state, not random. A
stderr marker ladder through `membrane_demo_init` bound the crash to the
statement after "[md] initial position copy ready": the valid-sized
`md_idx_host_.assign(...)` — whose inputs were independently valid. A
valid-size memcpy crashing there means corrupted CRT vector internals.

**Root cause: a stale translation unit.** The build directory sits under the
user Temp dir (CMake warning MSB8029: "Intermediate/Output directory cannot
reside under the Temporary directory as it could lead to issues with
incremental build"); earlier `engine.hpp` member-layout changes had left a
stale object compiled against the old header. A `--clean-first` rebuild of
the SAME source eliminated the crash entirely. No source change fixes this
crash; the fix is the clean build, recorded here.

Falsifier check: the crash reproduced exactly (single `/membrane_demo_bin`
request, exit 0xC0000005) before the clean rebuild and never after — across
four subsequent builds including two more `--clean-first` passes.

## Second, independent defect: JSON value-shadowing (source fix)

With the crash gone the gate exposed: after any `/membrane_demo` gamma
request, energy and force read EXACTLY 0 (validity stayed 1; the kernel ran
and wrote the energy buffer). Root cause in `main.cpp::find_colon_after`:
it returned the FIRST textual occurrence of the key, which in
`{"op":"gamma","gamma":2.0}` is the VALUE of `op`; no colon follows, so
`get_double("gamma", 0.0)` silently returned its DEFAULT 0.0, which
`md_admit_gamma(0.0)` legally admitted as a zero material — every observed
symptom, including the never-recovering status refresh (each subsequent
admission parsed 0.0 again).

Fix: scan ALL occurrences of the key; accept the first followed by ':';
skip value occurrences and longer names sharing the prefix (closing-quote
guard). No tolerance, fixture, shader or physics change.

## New runtime gate (option-b per Astra; Astra review answered)

Astra's review items were resolved: no prior symbolized record of this
crash; the source-publication discrepancy was real — commit `35f97e34` had
never been pushed (the crash session died before `git push`); pushed as a
fast-forward, remote head now `35f97e346abb7cb3f703d5af0e1d7edfe5313680`.
The runtime numerical gate is option (b): a separate engine-runtime gate
reusing the frozen fixtures/references — `tools/membrane_demo_client.py`
(separated requests; launch discipline: refuses occupied ports, terminates
only the PID it launched; archives engine stdout/stderr per run).

Preregistered: STATEMENT — the demo executes the declared law through its
actual runtime path. PREDICTION — comparisons and state-transition controls
meet their preregistered bounds. FALSIFIER — any bound breach,
accepted-state corruption, incomplete readback, or unverifiable state
association.

## Results (two consecutive clean-build gates, 20 PASS + 1 INFO each)

- init: E=2.625 vs frozen ref 2.6249999533666486 (f32 readback); centre
  [0,0,0.125]; material snapshot gamma f64=1/f32=1, J/m^2, wu_to_m=1.0.
- Fixed-state gamma doubling: E2=5.25=2×E0 EXACT; centre force
  -0.857142866 = 2×F0 EXACT.
- gamma back to 1: E=2.625 restored.
- step1: it=1, E=2.62457323 (CPU law first step 2.6245730615, f32-consistent).
- Full run: terminal `stagnated` at iteration 126, E=2.59807611 vs CPU
  2.5980761647224426 — SAME terminal state as the CPU law, not just an
  iteration-count match.
- reset: E=2.625, it=0, z=0.125 restored.
- rejection integrity: `invalid_trial_REFUSED`, accepted_state_id unchanged.
- gamma=0: `stationary`, it=0, no accepted step.
- Captures `final_relaxed.png` / `raised_gamma0.png` with status sidecars
  and accepted_state_id linkage (render-side certification remains
  conditional per GLM-WINDOW-02; not upgraded here).
- CPU regression rerun (shared-code rule): gamma=1 `stagnated`, 126
  accepted, 2.6245730615178493 → 2.5980761647224426; gamma=0 `stationary`.
- The leftover single-request CRASH in evidence 20260909T135116 was the
  client probing a port after its own gate had terminated the engine; the
  engine was not running; no engine defect.

## Verdicts after GLM-GPU-DEMO-02
- Engine runtime numerical gate (frozen B2, actual 11-binding/32-byte ABI,
  GPU readback): PASS.
- CPU: PASS. Engine build/shader: PASS. Startup/listener: PASS.
- Full matched CPU/GPU relaxation: PASS at terminal state and endpoints;
  per-iteration trajectory dump remains NOT TESTED.
- Gamma-zero, fixed-state doubling, reset, rejection integrity: PASS.
- Visual/DYAD review of the GPU-driven demo: NOT TESTED (next task).
- Human acceptance: NOT CLAIMED. GPU-driven engine milestone: implementation
  and numerical runtime gate complete; DYAD/human verdicts pending.

---

# GLM-GPU-DEMO-03 — DYAD review of the GPU-driven demo (2026-09-09)

Protocol: `docs/THE_DYAD_PROTOCOL.md`; runner `tools/run_dyad_gpu_demo_review.py`;
run reviewed `20260909T140408.398190Z` (the third consecutive 20-PASS gate, with
the capture camera now POSTed, not assumed). Eye verification first: LM Studio
resident VLM accepted the capability probe; served model recorded per call.
One image per `senses.watch_one` call, `PYTHONIOENCODING=utf-8`, no timeouts,
physical briefing verbatim, six numbered non-leading questions, image sha256
+ raw responses + finish reasons recorded to
`docs/evidence/membrane_gpu_demo_runtime/20260909T140408.398190Z/dyad_gpu_demo_review.json`
and `Saved/dyad/dyad_log.jsonl`. (Note: at first run the eye was dark — no
model loaded after the PC-crash reboot; the runner reports BLOCKED with the
operator action and Chimera never loads a model itself. Alan loaded
qwen3.8-27b-nvfp4-mtp; the review then ran.)

## What the dyad observed (raw responses preserved in the evidence JSON)

Both frames: a single light hexagonal membrane on a dark void, with a darker
hexagonal region read as a cast shadow on an implied (unrendered) floor.
- rim: clearly visible in both states; centre vertex: NOT visible — inferred
  only from the shading highlight.
- Raised (gamma=0) frame: the 0.125 m centre offset is **NOT RESOLVABLE**;
  the silhouette reads as a flat hexagon; the central specular sheen is
  consistent with either a raised cone or a flat plate lit from above.
- Relaxed (gamma=1, 126 iterations) frame: reads flat, qualitatively
  consistent with the recorded state, but only weakly — the image cannot
  confirm the numerical facts, which the dyad correctly leaves to the
  numerical record.
- Named worst problem (both): the membrane's defining geometry (six-triangle
  fan spokes, centre vertex) is invisible; a smooth highlight on a flat plate
  can masquerade as a residual bump.
- The dyad also flagged the runner's claimed "1-px wireframe" as not visible.

## Measurement/source reconciliation (the two-lens law)

The dyad's wireframe observation was checked against source and found
CORRECT: the GPU demo path sets no render mode, `mesh_mode_` is only set via
`/mesh_bin`, and the wire pass requires `mesh_mode_ >= 1` — so the demo
renders FILL ONLY. The runner's earlier "slotmode 2" fact was imported from
the CPU-demo `/mesh_bin` law and was WRONG for this path; the runner and the
recorded facts are corrected. The dyad's rim/centre/height findings reproduce
the GLM-DYAD-01/02 findings for the CPU-reference demo: height resolvability
requires the edge-contrast presentation (or a profile view), which the GPU
demo path does not yet enable.

## Verdicts

- DYAD (GPU-driven demo): EXECUTED. Rim visible; centre vertex not visible;
  height NOT RESOLVABLE in both states with the current fill-only
  presentation. No rendering defect beyond the already-recorded presentation
  limitation; no contradiction of the numerical record.
- Numerical (unchanged): GPU runtime gate 20 PASS; CPU law unchanged.
- Corrections made: runner render-mode fact (wireframe claim removed);
  capture camera now POSTed and recorded as applied (GLM-GPU-DEMO-03 prep).
- Visual/height resolvability: remains INCONCLUSIVE until the demo path gets
  the edge-contrast presentation (GLM-DEMO-CONTRAST-01's opt-in pipeline
  exists in the engine; the demo path does not enable it) or profile views.
- Human acceptance: NOT CLAIMED. GPU-driven claim: unchanged — compute drives
  the accepted state; presentation findings are render-path facts.

---

# GLM-GPU-DEMO-EDGE-01 — edge contrast closes the visual loop (2026-09-09)

Preregistered: STATEMENT — edge contrast exposes the accepted geometry
without changing it. PREDICTION — centre and spokes become visible; a
suitable fixed view makes the raised/relaxed distinction assessable.
FALSIFIER — geometry/state changes, contrast remains absent, or height
remains unresolved (INCONCLUSIVE).

## Implementation (smallest opt-in)

Source inspection first: `tri_edge_pipeline_` (GLM-DEMO-CONTRAST-01) is
created only when `CHIMERA_TRI_EDGE_CONTRAST` latches, and the wire pass
runs only when `mesh_mode_ >= 1`; the demo path sets neither. Added
`md_edge_contrast_`, latched at init from `CHIMERA_MD_EDGE`, extending the
wire-pass condition ONLY while the demo owns the triangle draw
(`mesh_mode_ >= 1 || (md_draw && md_edge_contrast_)`) and joining the
contrast-instrument creation gate. `mesh_mode_` is never written by the
demo, so ordinary presentation is untouched by construction (demo exit
restores prior presentation — the flag IS the demo scope).

## Attempts (both preserved — the falsifier fired twice before the PASS)

1. `20260909T142006.842279Z` — wire pass opened, but the CONTRAST pipeline
   did not exist (its own latch unset) so the pass fell back to the
   fill-colored ordinary wire. PNGs byte-differed from fill-only, yet the
   dyad saw no edges: contrast absent = falsifier FIRED. Correction: the
   instrument is created when either opt-in latches.
2. `20260909T143120.546189Z` + `20260909T143341.345560Z` — spokes visible
   at the oblique demo camera (phi 0.7), but height still not resolvable;
   documented profile phi 0.06 put the rim plane at eye level (a few
   pixels of bump) — still unresolved. (A client-side NameError aborted one
   run at the capture step; fixed; engine was fine.)
3. `20260909T143821.177952Z` — PASS. Camera radius 3.0, phi 0.35, uniform
   for BOTH states (a camera change is presentation, not geometry).

## Final dyad reads (raw responses in the run's dyad_gpu_demo_review.json)

- RAISED: centre = the spoke-convergence point, displaced toward the
  upper/far side of the projected rim (not the centroid); front facets
  broad, rear facets slivers — "a fan that bulges rather than lying flat…
  a 3D apex, not a point on a flat plane"; offset "resolvable in
  principle, but only qualitatively — I would not trust a pixel-measured
  magnitude."
- RELAXED: convergence coincides with the projected centroid (y~345 vs
  midline ~345), "consistent with centre height ~0"; and the dyad affirms
  discriminability: "a gross offset such as the 0.125 m raised case WOULD
  be visible here."

The raised/relaxed distinction is ASSESSABLE in this fixed view: apex
above centroid + bulging fan vs centroid-converged planar fan. The dyad's
no-pixel-magnitude caveat is recorded as its stated uncertainty; the
numerical magnitudes remain owned by the numerical gates.

## State identity across every presentation change

accepted_state_id is BIT-IDENTICAL across fill-only, wire-fallback, edge,
profile, and close-camera runs: raised `17560123212910228982`, relaxed
`16501489447187382864`. The full numerical gate re-ran green (20 PASS +
1 INFO) in EVERY presentation configuration. Presentation provably never
moved geometry. (One relaxed capture at r=3 shows a magenta top-edge bar
artifact — recorded as an observation, not blocking.)

## Verdicts

- Edge contrast: PASS (centre and spokes visible; raised/relaxed
  distinction assessable at phi 0.35, radius 3.0).
- Numerical: PASS (unchanged, rerun per configuration).
- Human acceptance: NOT CLAIMED — the phi-0.35 pair is the one to review.
- The visual loop opened by GLM-DYAD-01 is CLOSED for this demo.


---

# GLM-SLOT01-E2E — slot-01 end-to-end through the fleet control plane (2026-09-09)

- Task `slot01-membrane-143008` on the fleet registry (integration-kind, slot-01); base f9a4623e4ee8; evidence dir 20260909T193041.370670Z.
- Built clean from the slot worktree head f9a4623e4ee8; exe sha256 26fff49b9ee1; spv sha256 71b5f8d37acf; shader source blob 4f7a356e34cd (provenance verified against the tested revision).
- Runtime numerical gate (edge-contrast presentation, phi 0.35 radius 3.0): init=PASS, init.energy_vs_fixture=PASS, init.centre_z=PASS, doubling.energy=PASS, doubling.force=PASS, gamma_back_to_1=PASS, gamma_back.energy=PASS, step1=PASS, step1.descends=PASS, run=PASS, run.terminal=INFO, capture.final_relaxed.status=PASS, capture.final_relaxed=PASS, reset=PASS, reset.restore=PASS, reject=PASS, reject.refused=PASS, gamma0_step=PASS, gamma0.stationary=PASS, capture.raised_gamma0.status=PASS, capture.raised_gamma0=PASS.
- Interruption drill: worker client terminated post-checkpoint; registry failover to standby01; zombie write refused; GPU reservation retained until verified drain (port 8101 free); worktree reconciled at f9a4623e4ee8; reassigned at generation 4.
- DYAD: executed per THE_DYAD_PROTOCOL (served model qwen3.8-27b-nvfp4-mtp; one image per call; raw responses in dyad_gpu_demo_review.json).
- Capture association remains CONDITIONAL per GLM-WINDOW-02 (accepted_state_id linkage is the strongest implemented linkage; competing-writer exclusion is not proven).
- Human acceptance: NOT CLAIMED. GPU-driven claim unchanged (compute drives the accepted state; presentation findings are render-path facts).
