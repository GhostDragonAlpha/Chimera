# MAT2-M08 PREREGISTRATION — frozen before implementation and before any measurement

Frozen: 2026-09-29Z, before authoring resident_gpu_world.py, run_experiments.py,
test_resident_gpu_world.py, make_capture.py, make_report.py, before any GPU job
was run for this card (the only mailbox submission so far is a read-only
environment probe m08-probe-env-001: interpreter/library versions and CUDA
availability; no physics, no state), and before any capture code or frame
exists. Task: MAT2-M08 / planning id M08 — "Run the coupled material passes on
resident GPU state" (criteria sha256
491403f873b4e2a85c5f095998fc141c11b2de8464bca222e74ac13685fb1c79, attempt
28c16b488fff4ad48e08508ccbba2dcb, arrival
arrival-8232cdc99c9946e1ba250dfdbff0c254).

done_when (verbatim): "Reconcile the existing GPU/DSL/hierarchy path. GPU state
stays resident during steady-state stepping; CPU supplies bounded commands and
asynchronous diagnostics. Validate GPU/direct-reference agreement and
work/impulse budgets; profile actual step/frame/VRAM costs. Any Barnes-Hut pass
has its own eligible law, error criterion and near-field reference test."

Card task falsifier (verbatim, registry spec.falsifier + ontology task):
"A local bond/contact is replaced by an unchecked distant aggregate, or claimed
GPU dynamics require a full CPU state roundtrip each tick."

Verification-profile falsifier (verbatim): "Unbound media, clipped load path,
hidden constraint/support, area-independent triangle forces, overlay-driven
motion, or unaccounted energy prevents acceptance."

Port contract (verbatim): "Versioned resident buffers -> hierarchy/local passes
-> synchronized solver/render snapshot; bounded host commands."

## Base and reconciliation (read-only, done before this freeze)

- Canonical startup assigned slot branch-1, prepared checkout head
  c525b82c7c3ce0128565424764293a3c85811ab3 (origin/branch-1). The sealed line
  tip 122bd3d3aab36073d96107a913eb60b879967a67 (= merge of PR #258, the
  MAT2-M07 winner 83d3dd44) is a fast-forward descendant of the prepared head
  (ancestor check performed first); the local attempt branch was fast-forwarded
  to it. M07's report pins its own base as prepared c525b82c advanced to the
  sealed line; this freeze is written against the post-merge tip 122bd3d3,
  which carries the MERGED winner of declared dependency MAT2-M07 (PR #258)
  and, transitively, MAT2-P04 and the M03/M04/M05/M06 winners M07 pinned.
- Dependency input pins verified in this checkout before this freeze (frozen
  inputs; a mismatch at run time refuses `input_pin_drift`):
  - MAT2-M07/integrated_step.py sha256
    36c556dcf2cf0b3c9b7fe3c79dd42baae6489ad2c0b3093a5ac1bd550d8c66e4
    (the sealed CPU reference/oracle: one state owner integrating
    pressure -> material -> contact; used UNMODIFIED),
  - MAT2-M07/run_experiments.py sha256
    444fd58fe932bf4cb4443f577d0088ae9bfe218bfdd6397ef5594db7fbec0830,
  - MAT2-M01/material_state.py, MAT2-M03/pressure_membrane.py,
    MAT2-M04/passive_response.py, MAT2-M06/local_contact.py: the four frozen
    hashes recorded in M07's INPUT_PINS (re-verified at run time through
    M07's own `verify_input_pins`, unmodified).
- Reconciled existing GPU/DSL/hierarchy sources (read-only inspection in this
  checkout, sealed tip; the same sources req.teddy_gpu_matter_kernel's
  source_inspection cites on master):
  - ChimeraEngine/engine/kernel_dsl.py — the kernel DSL: a kernel declaration
    names quantity/aggregate/kernel_fn/sign/coupling; `kernel gravity`
    declares quantity="mass", aggregate="weighted_sum" (monopole COM),
    kernel_fn="inverse_squared", sign="attractive", coupling="G". RECONCILED
    as the far-field law declaration this card's Barnes-Hut arm executes:
    the arm runs exactly this declared law (Newtonian point-mass gravity,
    U = -G m_i m_j / r, F = -grad U) as a resident CUDA kernel.
  - the spiace_phase6 gpuBarnesHut prototype (cited by
    req.teddy_gpu_matter_kernel source_inspection): builds/serializes a CPU
    tree, uploads particle arrays and maps readbacks each frame — the
    inspected prototype does NOT meet residency. RECONCILED as the defect
    this card replaces: the tree is built/refit ON DEVICE per tick from
    resident positions; no per-tick state upload/readback exists.
  - ParticleEngine/gpu_pipeline.py — the engine's own lossless-tiling splat
    pipeline (numba.cuda kernels, CuPy sort, device-resident buffers through
    simulation/splat/projection/composite). RECONCILED as the residency
    pattern this card follows: CUDA device arrays live across ticks; the
    host submits bounded commands; render snapshots are separately budgeted
    consumers. (Master tip a2effe9a additionally fixes the tile-eviction
    render defect; the coupled-material physics of this card does not depend
    on it — recorded, not repaired here: this card does not modify the
    engine.)
  - ChimeraEngine/core/field_physics_gpu.py — existing resident CUDA N-body
    pattern (O(N^2) direct, buffers held across steps, declared VRAM
    discipline). RECONCILED as the direct-path reference pattern for the
    near field.
- Reconciled gap this card fills: M07's sealed integrated step is CPU-only
  numpy; the engine's GPU paths (splats, N-body, BH prototype) carry no
  coupled pressure/material/contact material world. No module on the sealed
  line steps the coupled material passes with GPU-resident state. M08 adds
  exactly that resident executor of M07's declared laws — nothing inside any
  upstream file is modified.

## Frozen statement

M08 implements `ResidentGpuWorld`, a GPU-resident executor of M07's declared
integrated step. ALL physical state — membrane vertices and velocities, plate
vertices and velocity, ground, Maxwell force state F and its cumulative
ledgers, contact/anchor impulse accumulators — lives in CUDA device arrays
created ONCE at construction and stays there during steady-state stepping.
The host supplies BOUNDED COMMANDS per tick (tick index, scheduled delta_p,
dt, substep count, iteration caps — a small fixed struct) and consumes
BOUNDED ASYNCHRONOUS DIAGNOSTICS (a fixed 96-f64 diagnostic block per
component per tick plus a fixed world block; per-pair contact detail only at
declared capture ticks). Every tick executes M07's DECLARED order

    1. pressure  (M03 declared-source traction, area-scaled on CURRENT
                  geometry, equal-third lumping in declared order)
    2. material  (M04 Maxwell element, exact exponential update/integrals)
    3. contact   (M06 sweep candidates -> local closest features -> impulse
                  solve, Gauss-Seidel to the declared 1e-12 N*s gate)

at dt = 1/300 s with N_SUB = 4 substeps per tick, then the declared position
integration and tolerance-driven XPBD edge projection with its exchange kept
in the MEASURED residual — each pass a CUDA kernel (or single-thread
sequential kernel where M07's declared arithmetic is sequential: the GS
contact loop, the XPBD edge loop, the ordered lumping reduction), all reading
and writing the same resident buffers, with per-tick energy/momentum ledger
gates identical to M07's (refusals `unexplained_energy`,
`momentum_ledger_open`, `convergence_gate_not_met`, `declared_order_mismatch`).
The Barnes-Hut far-field pass (below) runs on the SAME resident state as an
additional declared external-load pass; the agreement fixture runs with it
DISABLED so the comparison against the sealed CPU oracle is exact.

Numerics law (declared): float64 throughout; NO float atomics; no RNG; no
wall-clock in results; per-element arithmetic mirrors M07's numpy expression
order element-for-element; reductions recorded in diagnostics use the exact
numpy pairwise/block reduction order (8-accumulator blocked sum for n >= 8,
sequential below) in a declared single-thread reduction kernel; sequential
loops (XPBD edges, GS contact, ordered lumping) run in the declared index
order. Determinism law: two fresh GPU runs at the same revision are
BYTE-IDENTICAL in trace and receipt (X2). Trajectory agreement (X1) is
declared below as a measured window, not assumed bitwise.

## Frozen declarations (constants; declared BEFORE measurement)

- Agreement fixture = M07's frozen X1 scenario UNCHANGED: two components
  (offsets 0 and +3.0 m), icosphere L1 membranes R = 0.06 m mass 0.02 kg,
  plates 0.12 x 0.12 shells mass 0.02 kg, pinned grounds, Maxwell mounts
  k = 20 N/m c = 8 N*s/m, pressure schedule 60 Pa ticks 1..40 then 0,
  80 ticks at dt0 = 1/300 s, N_SUB = 4. Same initial state document feeds
  BOTH the M07 oracle world and the resident GPU world.
- Telemetry budget (steady-state, per tick): host -> device <= 256 bytes
  (command block); device -> host <= 1024 bytes per component (fixed
  96-f64 diagnostic block: energies, work terms, impulse totals, iteration
  counts, residual, state digest scalars) + 1024 bytes world block. Full
  geometry snapshots are NOT part of steady state: exactly 9 declared
  snapshot reads for the capture at ticks {0, 10, ..., 80}, taken
  asynchronously after the tick closes (separately budgeted consumers, the
  req.teddy_gpu_matter_kernel residency rule). The per-tick byte counts are
  RECORDED and gated (falsifier F1).
- Determinism: byte-identity of fresh reruns (X2); no atomics on floats; no
  clock, no RNG anywhere.
- GPU working set capacity (req.teddy residency `capacity` clause): declared
  per run from device queries — total VRAM, free VRAM at construction, peak
  allocated (numba/cupy allocator counters + nvidia-smi), transient buffer
  sizes (load/reduction scratch) recorded; scene bounds = the declared
  fixture; overflow is structurally impossible at these sizes and any
  allocation failure is a refusal, never a silent drop.
- Timing: CUDA events (device-side) bracket each pass; host wall-clock only
  around submissions and present (recorded as CPU submission/present times).
  Reported: per-pass and per-tick device times p50/p95/p99/max over the
  profile window; host upload/readback bytes per tick; VRAM before/peak/
  after. Timing never feeds physics (no adaptive stepping).
- Barnes-Hut far-field pass (the ONLY Barnes-Hut pass in this card):
  - Eligible law (the DSL's declared gravity kernel): Newtonian point-mass
    gravity between the declared mass elements, U = -G_N m_i m_j / r,
    a_i = G_N sum_j m_j (x_j - x_i)/|x_j - x_i|^3, G_N = 6.674e-11
    (SI, declared units m/s^2 accelerations on kg point masses; the declared
    mass elements are the lumped membrane vertices and the plate vertices at
    their declared masses/3, exactly the masses the coupled world already
    carries). Applicability declared: a far-field self-gravity coupling of
    the matter set; on the agreement fixture it is DISABLED (the sealed
    oracle has no self-gravity); on the BH fixture it is enabled and its
    work/impulse contribution is RECORDED as an external-load term (expected
    ~1e-13 N — negligible against the 1e-3 N pressure/contact scale, a
    measured record, not a tuned claim).
  - Hierarchy: Morton-code sorted binary BVH over the declared mass elements,
    built and refit ON DEVICE from resident positions each tick (deterministic
    bitonic sort on (code, index); per-node monopole aggregate = mass and
    center of mass = the DSL's declared weighted_sum aggregate). No CPU tree
    build, no per-tick host involvement beyond the command block.
  - Error criterion: opening angle theta = 0.5 (s/d <= theta aggregates the
    node's monopole; nearer nodes descend to leaves or direct pairs).
    Declared acceptance: max relative acceleration error against the exact
    direct-sum reference <= 5e-3 over all bodies and all measured ticks
    (`bh_error_window_exceeded` refusal otherwise). theta is NOT tuned after
    measurement; a violation is a frozen-criterion failure.
  - Near-field reference test: the direct O(N^2) pairwise sum (CPU numpy,
    vectorized, exact pairwise law) runs alongside every measured tick; the
    near-field set (leaf-adjacent pairs) is additionally compared pair-exact
    (<= 1e-12 relative) proving the near path is direct, not aggregated.
    The comparison reference itself is covered by a declared independent
    identity: acceleration on body i from a two-body system has the closed
    form a = G m / r^2, tested to 1e-12 relative.

## Frozen experiments and predictions (limits fixed before any run)

- X1 GPU/direct-reference agreement (the deliverable): the M07 oracle world
  (UNMODIFIED integrated_step.py, CPU) and the ResidentGpuWorld step the SAME
  agreement fixture from the SAME initial state at dt0 for 80 ticks.
  Frozen acceptance, recorded per tick:
  (a) trajectory agreement: max absolute membrane position difference <=
  1e-12 m; plate x difference <= 1e-12 m; Maxwell F difference <= 1e-12 N
  (measured; the declared numerics law targets exactness, the window exists
  so the claim is falsifiable, and the measured value is reported either way);
  (b) work/impulse budget agreement per tick, both sides recorded, each
  compared under the declared window: |a - b| <= 1e-9 * max(1, |a|, |b|) for
  w_press, w_grav, w_mat_on_plate, q_mat, w_contact_ke, projection_exchange,
  jn_applied_total, impulse_trapezoid_work, ground/wall anchor impulses
  (vacuous comparisons — both sides identically zero — are REFUSED
  `vacuous_comparison_refused` with the guard self-tested, M07's
  independent-review lesson);
  (c) both sides close their OWN ledgers inside M07's declared per-tick
  residual bound (the GPU side gates identically: `unexplained_energy`,
  `momentum_ledger_open` refusals otherwise);
  (d) declared-order digest present and asserted every tick on the GPU side.
  A violation of (a) or (b) fires `reference_agreement_exceeded` — the
  measured window is a gate, and its measured margins are reported.
- X2 GPU determinism byte-identity: two fresh subprocess runs of
  run_experiments.py produce BYTE-IDENTICAL experiment_trace.json and
  experiment_receipt.json (sha256 recorded). This is the engine's
  byte-identity determinism law applied to the resident physics path
  (independent of the render path).
- X3 residency/profile run (the card's measured costs): a scaled steady-state
  world of 16 components (independent, 3 m apart — the M07 component rig
  verbatim), cyclic pressure schedule (60 Pa on 1..40 of an 80-tick cycle,
  M07's A5 pattern), 240 ticks at dt0. Measured and RECORDED (no estimates):
  per-tick device step time (p50/p95/p99/max), per-pass kernel times
  (pressure/material/contact/integration/projection/ledger), host upload and
  readback BYTES per tick (gated against the telemetry budget above), VRAM
  free/used at construction, peak allocated, and after release, frame cost =
  device step + snapshot present (the capture's per-frame rasterizer time is
  reported separately and labeled as software rasterization of the GPU-solved
  snapshot), CPU submission time per tick. The steady-state residency claim
  is exactly: upload/readback bytes per tick are the bounded command/diagnostic
  blocks, INDEPENDENT of the 16-component state size, with zero full-state
  roundtrips (F1 gate green).
- X4 Barnes-Hut arm: the resident world at the 16-component scale with the
  far-field pass ENABLED for 120 ticks; per measured tick (every 10th) the
  BH accelerations are compared against the direct-sum reference: frozen
  window max relative error <= 5e-3 (theta = 0.5); near-field pair-exact
  window <= 1e-12 relative; the two-body closed-form identity test green;
  hierarchy built/refit on device (host bytes for the pass = command block
  only, recorded). Refusal `bh_error_window_exceeded` otherwise.
- P-probes: P-input-pins (all pinned files re-hash to the frozen values at
  run time); P1 declared-order digest every GPU tick (M07's literal guard);
  P2 single-writer structure (AST scan of resident_gpu_world.py: device
  state is written only inside the declared pass kernels invoked from
  `ResidentGpuWorld.step_tick`; host objects hold commands and diagnostics
  only); P3 byte-identity = X2; P4 regression: the UNMODIFIED M07 test suite
  re-runs green in this checkout on the exact candidate revision (which
  transitively re-runs the M03/M04/M05/M06 suites through M07's own P8).

## Frozen falsifier arms (each bitten on a TAMPERED COPY, discarded after; each arm runs its CLEAN CONTROL in the same executable)

- F1 "claimed GPU dynamics require a full CPU state roundtrip each tick"
  (card falsifier): a tampered residency path that uploads and downloads the
  FULL state (all vertices, velocities, ledgers) every tick MUST trip the
  recorded per-tick byte gate (`state_roundtrip_budget_exceeded`: measured
  host bytes > the declared telemetry budget); the clean resident path stays
  within budget at the SAME tick range (its recorded bytes are the frozen
  command/diagnostic blocks). Both arms run in the same executable; the
  clean control passing is part of the proof.
- F2 "a local bond/contact is replaced by an unchecked distant aggregate"
  (card falsifier): two tampered far-field copies: (F2a) the theta gate
  removed (every node aggregates as a monopole regardless of s/d — the
  unchecked aggregate) MUST exceed the declared 5e-3 error window against
  the direct reference (`bh_error_window_exceeded`); (F2b) the near-field
  path replaced by the aggregate for leaf-adjacent pairs MUST fail the
  pair-exact 1e-12 near-field test. Clean controls: the theta-gated BH arm
  (X4) passes both windows in the same executable.
- F3 "stale/lying diagnostics" (bounded-async-diagnostics gate): a tampered
  diagnostics path that returns the PREVIOUS tick's diagnostic block while
  the state advances (the exact "async telemetry lies about residency"
  failure) MUST be caught by the declared tick-digest chain (each diagnostic
  block carries a state-digest scalar chained to the tick; mismatch fires
  `stale_diagnostics_detected`). Clean control green.
- Profile-falsifier arms: unbound media (every capture view binds the sha256
  of the committed GPU-solved trace; rendered vertex arrays are asserted
  against the trace before any pixel is written); clipped load path and
  hidden constraint/support (fixed-bookmark cameras with all 16 registry
  camera fields; the pinned ground and the Maxwell wall anchor are rendered
  and labeled in whole/side/front views; measured camera margins reported);
  area-independent triangle forces (the GPU pressure pass recomputes
  per-triangle areas/normals from CURRENT resident geometry every substep —
  the recorded per-tick traction ratio |F_i|/A_i equals the scheduled
  delta_p, min/max recorded, M03's declared law; the 'constant' tamper is
  refused by construction); overlay-driven motion (fixed bookmarks; geometry
  moves only per the sha-bound trace); unaccounted energy (the GPU side runs
  M07's per-tick residual gate every tick; F3 guards the diagnostic chain).

## Frozen verification-profile probes and views (material, motion)

- Views (registry profile object read READ-ONLY from
  agent_slots.sqlite3 kanban.cards[MAT2-M08].spec.ontology_qualification.task
  .verification_profile): "whole experiment at fixed distance",
  "orthogonal side and front", "oblique close-up of the loaded interface";
  each rendered as a diagnostic/clean pair (clean_view_required true).
- Diagnostic layers: ALL FIVE registry layers carried in every diagnostic
  row: stable membrane/triangle/port IDs; pressure and area-scaled force
  vectors; rest/current geometry and material directions; contact/bond
  state; energy/work and simulation tick.
- Capture: task_id SHORT form "M08"; the captured state is the GPU-solved
  snapshot stream (read back at the 9 declared capture ticks, asynchronously,
  outside steady-state stepping) plus the committed per-tick GPU trace;
  solver-state binding asserted against the trace before assembly;
  single-artifact binding: ONE video file, capture_sha256 = that file's
  sha256, every view row an artifact_locator of kind video on it; cameras
  carry all 16 registry camera_required_fields; validate_manifest runs with
  the registry profile object read read-only from the registry;
  visual_acceptance stays false in the validator receipt (independent visual
  review is mandatory and outstanding, M07 precedent).
- Frozen capture scenario: the X1 agreement fixture's GPU-solved run
  (membrane inflates, presses the plate, plate slides against friction and
  stretches the Maxwell mount, then relaxes and settles) — the SAME physical
  experiment the oracle comparison validates, over its full 80-tick range
  with the 9 declared snapshots.

## Applicability boundary (honest, frozen)

An offline GPU experiment executable over pinned upstream laws and the M07
fixture; not the native C++ engine runtime, not a live renderer, no training.
The render is a software rasterization of the GPU-SOLVED state (M07's
rasterizer heritage reading resident snapshots; the engine's own splat
pipeline is cited as the reconciled residency pattern but is not modified or
exercised here — its render-path defects on this line are recorded, not
repaired, by this card). The membrane is M03's lumped XPBD scaffold, the
plate M06's rigid translating shell, the mount M04's 1-D Maxwell element; no
new physical law is invented — the one far-field law executed (Newtonian
point-mass self-gravity) is the DSL's own declared gravity kernel, run to
qualify the hierarchy path under its own error criterion, and it is disabled
on the agreement fixture. GPU work runs EXCLUSIVELY through the mailbox
(E:/ChimeraWork/gpu-queue per PROTOCOL.md); no direct GPU access from this
agent. "Frame" in this card means one physics tick plus its snapshot present;
the declared percentiles are over that measured quantity, labeled as such.

## Amendment A1 (frozen after the freeze commit d1aca4fb, BEFORE implementation completed and BEFORE any experiment or measurement)

Refinements derived during honest design (no experiment has run; the only
GPU submission remains the read-only environment probe):

1. Barnes-Hut declared mass elements: the lumped membrane vertices at their
   lumped masses and the plate CORNERS at plate_mass/4 (the rigid plate's
   mass split over its four vertices). The freeze's "masses/3" phrase is
   corrected to this declaration.
2. Barnes-Hut hierarchy form: a Morton-sorted binary hierarchy of STATIC
   SHAPE (deterministic bitonic sort on (code, index); children 2i+1/2i+2)
   whose per-node aggregates (AABB, mass, center of mass — the DSL's
   declared weighted_sum) are REFIT on device each substep from resident
   positions. "Build/refit" of the freeze is satisfied by the per-tick
   device refit; the shape never touches the host.
3. Near-field reference test, precise frozen form: rerunning the SAME
   traversal with theta = 0 forces every pair down the leaf-direct path;
   that run must reproduce the on-device exact direct sum pair-exact
   (<= 1e-12 relative, every body, every measurement tick) — proving the
   near path is direct, not aggregated. The falsifier arm F2b is the
   aggregate-everything run (theta = 1e9) measured under the SAME 1e-12
   window, which MUST fail; F2a is that run measured under the production
   5e-3 window, which MUST also fail. Clean controls: production theta
   within 5e-3 and theta = 0 within 1e-12 in the same executable.
4. Far-field pass position: executed ONCE PER SUBSTEP, after the contact
   pass and before position integration, as an additional declared external
   load; its per-tick work (trapezoid) and impulses are recorded and enter
   the whole-system ledger exactly like gravity (w_external and the
   momentum-ledger right-hand side). On the agreement fixture the pass is
   absent (zero), matching the sealed oracle.
5. Diagnostic block: the declared 96-f64 per-component block layout is the
   slot table at the head of kernel_mirror.py (single transcription source
   shared by mirror and CUDA); the chained tick digest is computed over the
   block content plus the tick, recomputed host-side, and its mismatch is
   the F3 refusal `stale_diagnostics_detected`.
6. X1 comparison method: per-tick, per-component scalar comparisons under
   the declared relative window (floor 1.0; vacuous identically-zero
   comparisons refused) plus full membrane/plate vertex-array comparison at
   the declared capture ticks; the oracle's per-tick row fields and the
   GPU diagnostic block slots carry the same named quantities.
7. Mirrored rehearsal: the kernel logic exists as kernel_mirror.py (pure
   numpy, identical statement order), locally validated BITWISE against the
   sealed oracle on the frozen fixture (trajectories exactly equal, ledger
   scalars <= 8.7e-19 over the full 80-tick two-component run, commit
   01012cb4) BEFORE the CUDA port. The CUDA module is its mechanical
   transcription; X1 measures the port on the GPU. The mirror's far-field
   rehearsal path uses the exact direct sum in place of the theta-gated
   traversal (the CUDA Barnes-Hut is validated on the GPU against the same
   direct reference by its own frozen windows).

## Amendment A2 (frozen after A1; the X1 measurement is being rerun after a diagnostic code fix; no acceptance window changed)

The vacuous-comparison guard (M07's independent-review lesson, armed and
self-tested) gates the FALSIFIABLE window claims: the per-tick residual
bound, the momentum ledger, the Barnes-Hut error windows and the falsifier
arms. A plain X1 agreement comparison of two IDENTICALLY-ZERO values
(e.g. w_press at tick 0, where the declared schedule is zero on both
sides) is itself the agreement evidence: it is recorded as an exact-zero
pair with difference exactly 0.0 inside the declared window — counted per
tick in the trace — and is not "refused", because unlike a window gate
there is no falsifiable claim being vacuously satisfied. The refusal
`vacuous_comparison_refused` remains armed and self-tested for the window
gates. Also recorded here: the two GPU failures during the rerun of the
frozen experiments (component-B NaN from a component-tiled adjacency
out-of-bounds read, fixed and localized by the armed gate-failure dump)
are preserved as failed checks in the mailbox failed/ records; the frozen
acceptance windows themselves never changed.

## Amendment A3 (frozen after A2; diagnostic-gate correction, no acceptance window changed)

The host pair-slot gate compared the M07 per-tick SUM of active pairs
(agg over the declared substeps) against the PER-SUBSTEP kernel slot
capacity (64). Measured at tick 43: 20 active pairs per substep (sum 80,
well inside per-substep capacity; GS residual 2.2e-14 N*s; reciprocity
exact; residual 7.7e-10 J inside the 3.1e-6 J bound; components A and B
identical) — the gate was wrong, not the physics. Corrected: the host
gate bounds the tick sum by MAX_ACTIVE * N_SUB; true per-substep slot
overflow still raises through the kernel's own cap path (P_GSRES = 1e300
-> convergence_gate_not_met). The armed gate-failure dump produced this
measurement.

## AMENDMENT A5 (render cosmetics; post-merge visual-gate follow-up,
## 2026-09-29Z, branch m08-render-cosmetics — recorded BEFORE the
## re-render, observations quoted from the independent gate)

Triggering record: the deferred visual_acceptance item was closed by the
independent visual gate (reviewer sgt-m08-visual; REVIEW_EVIDENCE.md +
VERDICT.json under kanban-reviews/MAT2-M08/visual-gate/; verdict PASS
with findings F1-F7, measured on the MERGED capture
20c9dc49540496de5ff2d827151a30ab8ca8263db07bc3c963cb1ebaca1914c3 decoded
from the mkv itself). No finding touches physics, state binding,
integrity or honesty; all seven are render/prose/housekeeping workmanship
on the renderer, its generators and their declared prose. The merged
original capture stays archived untouched as the merged original; every
correction below is render-side, generator-side or housekeeping and is
re-measured on the new capture. The state binding is UNCHANGED: every
view still binds sha256 of the committed experiment_trace.json
(826a5e8f...), the frozen cameras are unchanged (cameras.json stays
byte-identical), and the in-code volume binding assertion still gates
every frame.

1. F1 per-lane trace strip (renderer fix): gate observation — the red
   delta_p series had ZERO visible pixels in all 9 frames; it was drawn
   but 100.00% exactly overdrawn by the green cumulative-work series
   (4502/4502 predicted red px covered) because all three series shared
   one band. Re-issued: the strip draws ONE SERIES PER LANE (three
   separate 18-px bands with per-lane colored series tags), so no series
   can overpaint another.
2. F2 diagnostic layer 1 RENDERED in every diagnostic viewport (was
   falsified for the close-up): gate measurement — L1 (m:t0..3 navy
   labels) was exactly 0 px in the close-up at every tick (drawn first,
   then erased by the close-up cell's own plate/ground polygons).
   Re-issued by RENDERING the layer (preferred over prose amendment):
   navy (15,15,90) m:t0..3 membrane-triangle ID labels at their
   centroids plus the navy 'port:maxwell_mount' port ID (anchor dot +
   label) at the Maxwell mount anchor, drawn TOPMOST of every diagnostic
   viewport; clean rows carry none. Projection probe: all four m:t
   centroids project inside the close-up viewport at every tick, so the
   layer is renderable there.
3. F3 footer/marker agreement (footer binding fix): gate observation —
   L4 contact circles were 0 px at ticks 10/20/40 while the same frames'
   footers declared GPU active pairs 8/26/14. The GPU count D_ACTIVE is
   a pair-EVENT sum over the tick's substeps (an event integral, not an
   end-state); the circles are the end-state display recomputation, and
   the snapshot carries no GPU pair identities to draw. Re-issued: the
   footer names both quantities precisely — 'GPU contact pair-events N
   (summed over the tick's 4 substeps; end-state display contact
   triangles M)' — so the circles and the footer agree on what each
   number is; no value is hand-typed (both from the snapshot block /
   display set).
4. F4 clean captions inside their viewports (renderer fix): gate
   observation — clean captions were drawn at y=352-365, inside the
   diagnostic row, 3-16 px ABOVE their clean viewports. Re-issued: each
   caption is drawn INSIDE its clean viewport image (top-left), the
   clean cell's only text, declared in honest_titles and the clean view
   notes.
5. F5 shade() unit scale (renderer fix): the previous form multiplied
   0..255 base channels by an extra 255 (int(min(255, c*lam*255))),
   saturating every polygon fill to pure white (gate observation: the
   render was effectively wireframe). Re-issued: shade() treats the base
   scale as 0..255 with the named assert shade_base_not_0_255_scale;
   fills are lambert-shaded.
6. F6 per-viewport clipping (renderer fix; root cause of F2's close-up
   loss and the wall-anchor line loss): gate observation — no viewport
   clipping; later viewports' geometry overpainted earlier overlays
   (wall-anchor line 679 drawn vs 1/1/4/0 visible px). Re-issued: every
   diagnostic/clean viewport is rasterized into its OWN 640x360 image
   and pasted into the sheet, so no projected geometry can leave its
   cell. Frozen cameras unchanged.
7. F7 housekeeping: the three untracked loose JSONs the committed
   original also wrote at the contribution root (byte-identical
   duplicates of the committed evidence) are removed; make_capture.py
   now writes the manifest/context/receipt only into the attempt
   evidence directory, and make_report.py reads the committed
   capture/validation_receipt.json.
8. Re-capture identity: same 9 capture ticks, same frozen cameras
   (camera records unchanged), state binding unchanged — every frame is
   still bound to the committed trace (sha256 826a5e8f...) via the
   snapshot volume assertion. The cosmetics fixes intentionally change
   frame pixels, so the NEW capture carries a NEW video sha256 and NEW
   frame hashes, re-pinned in the manifest/context/receipt; the
   decoded-frame == committed-still gate re-runs on the new artifact,
   with the adapted visual-gate measurement scripts first validated
   against the OLD capture as control.
