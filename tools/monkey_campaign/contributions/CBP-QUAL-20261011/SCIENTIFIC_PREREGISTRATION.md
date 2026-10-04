# CBP-PREREG-001 — Completed scientific preregistration: synthetic coupled-backend qualification

Status: COMPLETE, UNPUBLISHED. Authored 2026-10-02/2026-10-04 by worker `wk-cbp-prereg`
under Lieutenant tasking in the coupled-backend qualification. This document
COMPLETES the sealed draft `PREREGISTRATION_DRAFT.md` (sha256
`7e05fbb11fbd1d3950a7c0bc78948da892210d096a91ed5b4dad87722cb92585`); it does not
replace or contradict it. Every draft prediction (1-6) and every draft
instrumentation prerequisite is preserved and extended below (traceability in
Appendix B).

Prereg-first law: this preregistration must be published through the one
serialized publication owner BEFORE the first gated physical measurement. A
local plan or package seal does not substitute for the published commit
(NO_WORKTREES.md, "Publication and scientific precommitment"). No gated run may
be submitted to the GPU queue until the Lieutenant pins the published revision.
No physics ticks and no GPU measurements informed anything below: the verified
construction check executed ZERO physics ticks (job
`c212c4f6d63b46dab5577ee04768a218`, `physics_ticks_executed: 0`,
`gpu_experiments_executed: 0`).

Every fixture parameter is SYNTHETIC and DECLARED. This is an explicitly
synthetic engineering fixture. No measured macaque anatomy is used or claimed
anywhere in this document.

---

## 1. The frozen fixture

One Newton XPBD model contains the torque-driven anchored limb (rigid body,
one revolute joint to the world), a tetrahedral deformable pad (18 particles),
and an infinite y=0 ground plane. Reciprocal elastic attachment binds the pad's
top layer to the arm. Source of record: `FixtureSpec` + `Candidate` in the
sealed `fixture.py` (sha256 `d796311539d4cf8c830e8aa17acb8997f9237693c2f6e01812ecf84ff2ae0633`).
Declaration string: `synthetic-limb-pad-floor-v1`. Units SI; frame Y-up;
world gravity acts along -Y with magnitude 9.80665 m/s^2.

### 1.1 Rigid limb (one body, label `synthetic_arm`)

| Frozen value | Declaration / assumption | Violation observable (V-law) |
|---|---|---|
| mass 0.8 kg | Synthetic authored mass. Assumption: uniform box-like inertia is adequate for a rigid-link engineering fixture. | Qualification text or evidence claiming this mass derives from measured macaque anatomy; or reconstructed model mass differing from 0.8 kg. |
| length 0.3 m (shoulder pivot at origin (0, 0.07, 0); COM at local (0.15, 0, 0)) | Synthetic authored geometry; arm extends along +X from the shoulder. | Rendered limb length or COM offset not matching these numbers; motion of the COM without a matching state change. |
| inertia Ixx = 0.00048, Iyy = Izz = 0.00624 kg m^2 (authored box-like; `lock_inertia=True`; no implicit collider-density mass addition) | Assumption: rigid-body response at these scales is insensitive to the exact inertia distribution for this qualification. | Solver evidence of density-derived mass injection, or measured inertia-dependent behavior (e.g., free-swing period) inconsistent with the authored inertia by more than the frozen ledger residual bound. |
| shoulder joint: revolute about Z, limits [-0.35, +0.35] rad, joint damping 0.0, target ke/kd 0.0 | Assumption: an undamped, uncontrolled revolute pair with hard limits isolates actuator and contact physics. | Motion outside the limits; a nonzero joint damping contribution appearing in the ledger; any joint-space pose write creating motion. |
| actuator limit 2.0 N m (`effort_limit`) | Synthetic cap, selected analytically BEFORE any run: horizontal gravity demand = 0.8*9.80665*0.15 + 0.072*9.80665*0.30 = 1.389 N m; the cap exceeds it with 0.611 N m margin. Not a biological measurement. | A command with |tau| > 2.0 N m being executed; evidence that the limit was chosen from measured tissue properties. |

### 1.2 Deformable pad (tetrahedral grid, 18 particles)

| Frozen value | Declaration / assumption | Violation observable |
|---|---|---|
| grid 2 x 1 x 2 cells, node lattice 3 x 2 x 3 = 18 particles; extent X 0.06 m, Y 0.02 m, Z 0.06 m; nodes at x in {0.27, 0.30, 0.33}, y in {0.05, 0.07}, z in {-0.03, 0, 0.03} | Synthetic authored placement at the distal end of the arm; pad top layer at y = 0.07 coincides with the shoulder height at t0. | Particle count or any initial coordinate differing from the frozen lattice; a particle inside the arm volume (arm/pad self-contact is out of scope; the arm has no collision shape). |
| density 1000 kg/m^3; total pad mass 0.072 kg, enforced by tetrahedral-volume lumping that overrides the grid builder's per-cell mass assignment | Assumption: lumped tetrahedral volumes represent the authored uniform density. | Reconstructed particle-mass sum differing from 0.072 kg (construction check freezes tolerance 1e-7 kg); or the rigid arm's 0.8 kg being conflated with pad mass in any report. |
| particle radius 0.002 m | Authored contact radius. | Contact behavior reported as if the radius were fitted to data. |
| E = 25000 Pa, nu = 0.35 mapped to XPBD coefficients mu = E/(2(1+nu)) = 9259.2593 Pa, lambda = E*nu/((1+nu)(1-2nu)) = 21604.9383 Pa; k_damp = 0.0 | THE ELASTIC LAW IS AN XPBD SCALAR-CONSTRAINT PENALTY, NOT STVK AND NOT Neo-Hookean. Independent source audit (HANDOFF review block): the implemented density is the constraint potential c_mu = tr(F^T F) - 3, c_lambda = det(F) - 1 (+activation), energy = (1/(2*rest_inv_det)) * (mu*c_mu^2 + lambda*c_lambda^2). The E/nu-derived coefficients are authored parameter mappings, NOT a calibrated Young's modulus for this law. k_damp = 0 means no authored material damping; any dissipation observed is solver/contact numerics and belongs in the residual column. | Any report describing the pad material as STVK, Neo-Hookean, or "calibrated"; a tetrahedral energy term computed from a different potential than the one above; attributed damping that is not authored. |
| initial state: zero velocities, identity rotations, authored rest geometry; construction check freezes kinetic energy exactly 0, attachment energy < 1e-10 J, XPBD tet penalty < 1e-8 J | Assumption: the authored geometry is the (near) rest state of the attachment network. | Nonzero initial kinetic energy; attachment or penalty energy outside the frozen bounds at tick 0. |

### 1.3 Attachment (9 reciprocal elastic anchors)

| Frozen value | Declaration / assumption | Violation observable |
|---|---|---|
| stiffness 100 N m^-1 per anchor, 9 anchors = top particle layer (y = 0.07), anchors = t0 positions in the arm body frame; pad is never fixed to the world | Assumption: identical scalar springs capture a deformable distal pad binding. | An anchor set other than the 9 top-layer particles; a world-fixed pad node; a stiffness value other than 100 in the executed source. |
| force law: F_particle = -k (p - anchor_world), body receives the exact negation plus moment about COM (one bounded kernel thread, fixed-order gather, no atomics; attachment energy scalar sampled pre-integration) | Assumption: reciprocal pair forces with line-of-action moment equivalence (displacement x force = 0 along the spring). | Missing reaction; sign reversal; a separate opposing-force writer; the pre-integration energy scalar presented as post-step elastic energy. |

### 1.4 Contact, friction, solver, clock

| Frozen value | Declaration / assumption | Violation observable |
|---|---|---|
| ground: infinite static plane y = 0 (`add_ground_plane`); render side draws only a finite visual patch (extent 0.6 m) | Assumption: the plane is dynamically infinite; the visual patch is presentation only. | Physics behavior that treats the floor as finite (objects falling off the visual patch edge in free fall when the plane should stop them). |
| friction coefficient 0.6 wired to BOTH `default_shape_cfg.mu` and `soft_contact_mu` | Synthetic Coulomb-style coefficient authored before runs. | A shape-material or soft-contact mu differing from 0.6 in the executed model; friction effects claimed as measured material data. |
| dt = 1/1200 s fixed substep; 12 XPBD iterations; one simulation clock independent of render rate | Assumption: 12 iterations at 1/1200 s reach the frozen convergence behavior of prediction P10. | A run executing a different dt or iteration count without a prospective amendment; render-rate coupling into the physics clock. |
| solver `SolverXPBD(model, iterations=12, rigid_contact_con_weighting=False, enable_restitution=False, angular_damping=0.0)` | Frozen configuration. Known, documented solver properties: XPBD reports APPROXIMATE reaction forces and contact momentum loss with default con_weighting; `con_weighting=False` is set here but this does not convert the solver into an exact ledger machine (see G5). | Restitution or damping appearing that was disabled; a claim of exact reaction/momentum closure merely because the solver runs. |
| dependency pins: Newton 1.3.0, warp-lang 1.15.0 (`RuntimeError` otherwise); `wp.config.deterministic = DeterministicMode.RUN_TO_RUN` set before Newton kernel import in the sealed candidate | Exact inspected versions; RUN_TO_RUN is the candidate's default arm (D1). Warp 1.15.0 documents record/sort/reduce transformation of supported atomics; unsupported-pattern bounds must be recorded before graph capture. | A run on unpinned versions; a silent deterministic-mode change; unsupported atomic patterns used without recorded bounds. |
| hash scope of "committed state": body_q, body_qd, particle_q, particle_qd only. Excludes solver history, contacts, control and force buffers | Declared law scope (HANDOFF `hash_scope`). Byte-identity predictions (P9, P11) apply to exactly this scope plus captured frame digests. | An identity claim extended to solver history without a new frozen scope; a history divergence being reported as impossible because the four arrays matched. |

No macaque qualification claim exists in the fixture, this preregistration, or
any permitted report of it. The word "falsifier" in the draft is realized here
as the "violation observable" column: a named, checkable observation that would
contradict the declaration or prediction.

---

## 2. Frozen test battery, drive schedule, and controls

All runs use the sealed candidate API only: `advance_candidate(torque_nm)`
(|tau| <= 2.0 N m, finite, else refusal), private `fork()` reconstruction,
`TickOwner.prepare/commit` publication, `snapshot()` digests,
`candidate_energy` same-stage diagnostics, `render_snapshot` adapter,
`make_replay_bundle` packaging. Schedule frozen now, before any gated run.

### 2.1 Battery B1 (primary arms)

One battery = 3600 ticks = 3.000000 s of simulated time at dt = 1/1200 s:

- Phase A — passive settle: ticks 0-1199, tau = 0 N m. Establishes the
  passive-contact baseline (P1) and the fork point for controls.
- Phase B — press: ticks 1200-2399, tau = -2.0 N m. Sign basis: joint axis +Z,
  arm along +X, gravity -Y gives gravity torque z-component -1.389 N m at
  horizontal; holding horizontal demands +1.389 N m (fixture comment), so a
  downward press against the floor is NEGATIVE torque. Press drives the pad
  into the floor through the attachment network via solver state only; no pose
  writes.
- Phase C — release: ticks 2400-3599, tau = 0 N m (drive released; the
  simulation continues; passive dynamics must continue from the moving state).

If the commanded sign produces lift rather than press (pad penetration and
floor reaction decreasing under Phase B), that observation is recorded as a
schedule-sign misprediction; the battery is NOT silently re-run with the flipped
sign. A corrected schedule requires a prospective amendment and a fresh pinned
attempt.

Convergence arms (P10): B1 re-executed at dt/2 = 1/2400 s and dt/4 = 1/4800 s
with identical physical duration and input schedule (tick counts 7200 and
14400; per-phase doubled and quadrupled). Same backend, same hardware, same
frozen inputs.

Checkpoint cadence (all arms): full `snapshot()` state digest + `candidate_energy`
diagnostic every 120 ticks (30 checkpoints per battery, 10 Hz simulated),
plus at each phase boundary and at every control fork/commit boundary.

### 2.2 Controls (each starts as a private fork of the committed end-of-phase-A state)

- C1 power-cut preservation: 600 ticks tau = 0 continuing from settle,
  executed through a fork + TickOwner prepare/commit roundtrip; committed
  state, tick, and (declared-scope) continuation must be indistinguishable
  from a non-forked continuation (P7).
- C2 floor removal: ground plane removed; 600 ticks tau = 0; free fall
  (P6). The plane removal is a model-construction change declared here and
  only here; it is a control, never mixed into B1 arms.
- C3 invalid-input refusals: torque NaN, torque +2.0+eps, torque -2.0-eps,
  non-True validator returns, wrong-owner/stale/reused pending candidates,
  nonfinite diagnostic snapshots. Each refusal must leave committed state
  digest and tick byte-identical (P8).
- C4 declared negative variants, each a separately sealed frozen variant
  package: C4a friction 0.0 (all other fields identical); C4b detached pad
  (attachment id array empty; no anchors); C4c invalid material
  (poisson_ratio = 0.5) which must be REFUSED by `FixtureSpec.validate()`
  at construction, not simulated.

### 2.3 Repeats and mode comparison

- Byte-identity repeats (P9): battery B1 executed at least 3 times as
  identical jobs on the same backend and hardware in the candidate's
  RUN_TO_RUN mode; all checkpoint digests and captured frame hashes compared.
- Deterministic-mode comparison (P11): arm D1 = sealed candidate (RUN_TO_RUN);
  arm D2 = pre-declared variant identical in every byte except Warp
  deterministic mode left at default (native atomics). Identical frozen
  inputs; >= 3 repeats each; both outcomes reported. D2's variant source must
  be sealed and pinned BEFORE the first D2 run.

### 2.4 What may never change mid-campaign

No dependency, scenario, tolerance, schedule or mode change after any
observation, without a prospective amendment published through the same
one-writer path and a fresh pinned attempt. Refused and failed jobs are
recorded alongside passes.

---

## 3. Frozen predictions and their contradicting observations

Tolerances are analytic predictions frozen BEFORE any gated run (zero physics
ticks informed them). They may fail; a failure is a finding, never a tuning
input. The independent tolerance review precondition in section 4.7 applies
before any pass/fail run.

### P1 — Passive-contact penetration bounds

Prediction: after the 1.0 s passive settle, over the final 0.2 s window
(ticks 1080-1199 checkpoints): (i) no pad particle lies below y = -1.0e-3 m
(half the authored particle radius); (ii) at no checkpoint of phase A does any
particle lie below y = -2.0e-3 m (one particle radius). Basis: static pad
weight 0.706 N (0.072 kg) and total fixture weight 8.551 N (0.872 kg) against
XPBD contact projection at 12 iterations and 1/1200 s; the bound is the
authored particle radius, not a solver guarantee.
Contradicting observation: sustained penetration beyond (i) at >= 3 consecutive
checkpoints, or any particle below (ii) at any phase-A checkpoint. A pass does
not claim XPBD forbids penetration in general.

### P2 — Torque-driven state change (draft prediction 1, completed)

Prediction: the frozen press command changes the maximal rigid-body state only
through solver integration, with the pad deforming through the elastic
attachment network; the same-stage diagnostics and snapshot digests move
together. Contradicting observation: any root/pose injection path, rendered
vertex motion without a corresponding committed state change, zero applied
drive during phase B, or a snapshot digest that does not change across a tick
in which forces were applied.

### P3 — Press-phase work and energy ledger with an unexplained-residual column

Prediction: at every phase-B checkpoint the ledger reports
`actuator_work_estimate_j` (trapezoidal tau*omega*dt estimate — an estimate,
never presented as an exact discrete work proof), the same-stage energy change
(kinetic + gravitational + attachment + XPBD tet penalty),
`unexplained_residual_j` = dE_accounted - W_estimate, and
`ledger_closed = false`. Frozen bound: |unexplained_residual_j| <= 5% of
|actuator_work_estimate_j| sustained over the final 0.2 s of phase B.
Contradicting observation: residual beyond the bound at >= 3 consecutive
checkpoints — reported as a finding with the documented Newton approximation
cited (section 5, G5), not tuned away; or ANY presentation of the residual as
heat, as measured dissipation, or as closure. The residual column is never
renamed. Modeled dissipation, if ever attributed, must be an authored,
declared term (currently k_damp = 0 and angular_damping = 0: the authored
dissipation is ZERO, so every observed loss is numerical until a declared term
is added by amendment).

### P4 — Reciprocal attachment reactions (draft prediction 2, completed)

Prediction: for each of the 9 attachments, the recorded particle force and the
recorded body reaction sum to EXACTLY zero in the recorded float buffers
(literal negation), and the recorded body spatial force equals the fixed-order
gather of (-sum F_i, sum (anchor_i - com) x (-F_i)). An independent float64
recomputation from float32 readback must agree within the declared
re-association budget: relative 1e-5 on the moment (basis: 9-term float32
accumulation vs float64 re-summation) and exact zero on pair sums.
Contradicting observation: any nonzero pair sum; a missing reaction; a sign
reversal; a recomputation outside the budget; a reaction exceeding the frozen
numerical budget implied by |tau| <= 2 N m, spring displacements, and weight.

### P5 — Support only during contact (draft prediction 3, contact part)

Prediction: the floor's normal reaction supports the pad only while contact
exists; recorded penetration (P1) and floor reaction co-vary, and the passive
settle ends in a supported configuration with near-zero residual dynamics.
Contradicting observation: a nonzero floor reaction with no contact; hidden
world pins supporting the pad; frozen (time-invariant) inertia reported during
settle.

### P6 — Floor-removal fall and gravity/KE identity (draft prediction 3, control part)

Prediction: with the ground removed (C2), the whole fixture falls: every body
and particle y decreases monotonically over the window, and over any
unpowered sub-window the mechanical identity d(KE + E_grav + E_attach +
E_xpbd)/dt = 0 holds within the ledger residual bound (P3's 5% form, applied
to the window's energy change). Analytic from-rest control: after 0.1 s,
COM drop 4.9033e-2 m, speed 0.980665 m/s, KE 0.4193 J (m = 0.872 kg); with
measured v0, drop = v0*T + 0.5*g*T^2. Contradicting observation: residual
removed-floor support; anything hovering; a KE gain that exceeds PE loss
beyond the residual bound with no declared term; static passive configuration
misreported as a power-cut failure (a static configuration need not fall after
power cut — the tested quantity is preservation of passive dynamics, P7).

### P7 — Power-cut preservation (draft prediction 3 + draft instrumentation, completed)

Prediction: after power cut (tau = 0 commit via fork + TickOwner), passive
dynamics continue from the committed state; the committed snapshot digest and
tick are unchanged by the REFUSAL path, and the C1 forked continuation is
state-identical (declared scope) to a non-forked continuation at every
checkpoint. Fork purity includes the declared state arrays; solver history is
deliberately fresh per fork — this is a declared execution-policy difference
(HANDOFF `fork_policy`), not an equivalence claim.
Contradicting observation: frozen inertia after power cut; a fork whose
committed source changed; digest or tick drift caused by the
fork/prepare/commit machinery itself.

### P8 — Invalid-input refusals before state change (draft prediction 5 + software checks, completed)

Prediction: every C3 input is refused with committed state digest and tick
byte-identical to before the attempt (fixture command bounds; TickOwner
validator/ownership/generation semantics; snapshot finiteness; adapter and
replay validation). Contradicting observation: any committed digest or tick
change following a refused call; an invalid command executing; a refusal
surfacing only after private mutation became visible in committed state.

### P9 — Byte-identity repeats (draft prediction 4, completed)

Prediction: >= 3 identical B1 jobs, same backend, same hardware, RUN_TO_RUN
mode: all checkpoint `state_sha256` sequences and all captured frame digests
byte-identical across repeats. Identity scope = the four declared state arrays
plus frame digests (section 1.4); this law says nothing about solver history,
contacts, control or force buffers. A pass does not establish cross-GPU
determinism or atomic guarantees beyond the tested patterns.
Contradicting observation: ANY digest mismatch at ANY checkpoint. A failed
byte identity is a reported ADOPTION BLOCKER, never rounded, averaged,
re-seeded, or retried into a pass.

### P10 — Timestep refinement reporting (draft prediction 6, completed)

Prediction: B1 at dt, dt/2, dt/4 with identical physical duration and input
schedule yields reported convergence tables for: max penetration (P1 metric),
attachment pair residual (P4), ledger residual (P3), XPBD penalty energy, and
the frozen probes (body rotation angle theta(t) and pad bottom-layer mean y at
all checkpoints). Errors are predicted to decrease away from changed impact
events. NO universal convergence order, stability, or monotonicity is promised
across impacts or contact events; contact event sensitivity is reported per
PLAN. Contradicting observation: sustained growing error with refinement away
from impact events, or an unexplained failure to converge — reported as a
finding.

### P11 — Native-atomics vs RUN_TO_RUN on identical frozen inputs

Prediction: both arms produce complete, reportable sequences. Arm D1
(RUN_TO_RUN) satisfies P9. Arm D2 (native atomics, Warp default mode) either
satisfies the same identity or does not; BOTH outcomes are acceptable
measurements and both are reported. Unsupported-pattern bounds are recorded
from the installed Warp 1.15.0 source before graph capture, per PLAN.
Contradicting observation (as blocker): claiming atomic-mode equivalence
without the comparison; running the arms on different inputs; silently
switching a run's mode. D1 failing while D2 passes (or vice versa) is a
finding that decides which mode adoption may rely on (G7), never a rounding
candidate.

### P12 — Snapshot/frame join for any capture (draft prediction 5, completed)

Prediction: every render/capture frame joins to exactly one committed
candidate tick with matching topology identity and state digest; the adapter
refuses mismatched/stale identifiers, unvalidated vertex/index arrays, and
altered geometry with a stale digest; replay bundle digests are canonical
(key-order independent) and prove bundled bytes only — not GPU readback,
solver correctness, or physics certification. Scope limit: the runtime
snapshot consumer and actual capture path do not exist yet (HANDOFF
`remaining`); P12 binds any capture produced after that consumer exists and is
not claimable from the current adapter alone. Contradicting observation: a
mismatched or stale identifier in a consumed frame; visual motion without
matching physical state; a capture presented as a game demonstration.

### P13 — Software-law persistence under measurement

Prediction: the module contract checks (TickOwner transaction boundaries,
work-account refusals and permanent `ledger_closed = false`, replay bundle
refusals) pass unchanged in every measurement job that imports them; the
assembly binds only contract-declared symbols with recorded module sha256s.
Contradicting observation: a measurement job running modified copies of these
modules; any `ledger_closed: true`; a binding to a symbol outside the frozen
contract.

---

## 4. Measurement protocol

### 4.1 GPU queue (mailbox; one GPU agent; no direct GPU)

All GPU work is submitted through the existing mailbox queue at
`E:/ChimeraWork/gpu-queue/` per its PROTOCOL.md (Captain-ordered 2026-09-28):
JSON job files to `incoming/<priority>-cbp-prereg-<short-id>.json` with id,
requester, exact non-interactive command, workdir, expected_outputs,
timeout_seconds, notes; jobs < 10 min GPU time, bigger work split; the single
GPU agent claims, checks the card, runs, hashes outputs, and writes
`done/<id>.result.json` or `failed/<id>.result.json`; the requester polls
done/ and failed/, never reads running/, never touches the GPU. Worker status
inspected before submission; read-only discovery does not reserve the GPU or
authorize a competing worker. CPU-side scalar/software checks (sealed suites,
construction checks) go through the canonical `task_package.py` CPU runner
(slots 0-3) when needed; authoring and sealing need no runner.

### 4.2 Compilation vs runtime, separated

Every arm's first job is a warmup job: it performs exact pinned imports, GPU
initialization, small allocation, kernel compilation (including the
attachment adapter), and a bounded tick-rate probe. Warmup outputs (compile
log, cache directory bounds, probe rate) are recorded and DISCARDED from all
latency statistics. Measured repetitions start only after warmup. Kernel-cache
paths, job timeout, memory, frame counts and retained outputs are bounded in
each job manifest before submission.

### 4.3 Latency law

Reported per-tick latency is the measured solver-step duration distribution
(p50/p95/p99/max) over steady windows only: the first 120 ticks after process
start or after any compile/allocation event are excluded and the exclusion
count recorded. Harness-elapsed time (job wall time including interpreter
startup, imports, model construction, fork rebuilds, I/O) is reported
separately, clearly labeled, and NEVER as tick latency. The `fork()` full
model rebuild per tick is a correctness-prototype cost and is reported as
its own line item, never absorbed into solver latency.

### 4.4 Memory and transfer, per stage

Device memory recorded after model finalize, after solver construction, after
warmup, and at steady state (method and sampling recorded). Host-device
transfer measured separately for: diagnostics readback, snapshot/state
readback, reaction/energy scalars, and frame capture. Renderer timing is
measured separately from physics tick latency. The CPU diagnostics readback is
correctness instrumentation; its overhead is measured, not hidden.

### 4.5 Job decomposition rule (frozen)

The battery is submitted as K queue jobs, where K is chosen from the warmup
probe tick rate such that every job stays under 8 minutes GPU time; K, the
phase-to-job mapping, and the checkpoint set are recorded in the job manifest
BEFORE the first measured run. No mid-run re-decomposition. Allocation
failure or OOM is a reported failure, not a trigger for shrinking the fixture
outside this preregistration. Retained outputs stay within the runner/queue
declared-output bounds (compact digests, checkpoint CSVs, receipts; one short
capture later, per PLAN step 8).

### 4.6 Evidence anchoring

Campaign-required evidence goes through the existing `anchor.py` into the
sealed evidence store before it is referenced. Every report carries job ids,
receipt paths, exit statuses, artifact sha256s and cleanup_verified; refused
and failed jobs are recorded alongside passes. Only an actual receipt saying
PASSED with cleanup_verified true may be called a passing run — and that
still does not qualify physics by itself.

### 4.7 Independent tolerance review precondition

The frozen numeric bounds in sections 1-3 (penetration bounds, ledger
residual percentage, re-association budget, construction tolerances) are
analytic precommitments. Before the first gated pass/fail run, the
Lieutenant's independent review (Sergeant Flash review through the
Lieutenant) either endorses these frozen numbers or an amended preregistration
is published first. Any subsequent numeric change is a prospective amendment
with a fresh pinned attempt — never an in-place edit after observations.

---

## 5. Qualification gates — what decides backend adoption

Hard gates (all must pass on the pinned revision for an adoption proposal to
exist at all):

- G1 structure: executed model matches section 1 exactly (1 body; 18
  particles; 9 attachments; pad mass 0.072 kg within 1e-7 kg; arm 0.8 kg
  separate; authored mu/lambda mappings; friction 0.6 on both paths; dt
  1/1200 s; 12 iterations; limits +/-0.35 rad and 2.0 N m; pinned Newton
  1.3.0 / Warp 1.15.0).
- G2 refusals: P8 holds for every listed input.
- G3 reciprocity: P4 exact identities hold.
- G4 controls: P5, P6, P7 hold (support co-varies with contact; floor removal
  satisfies the ballistic identity; power cut preserves committed state and
  passive dynamics).
- G5 ledger honesty: P3's residual column exists at every checkpoint with
  `ledger_closed: false`; no residual is ever relabeled heat or dissipation.
  An excess residual is reported as a finding citing Newton's documented
  approximate reaction forces and contact momentum loss (con_weighting
  context). CLAIMING EXACT LEDGER CLOSURE MERELY BECAUSE THE SIMULATION RUNS
  IS ITSELF A GATE FAILURE. Newton XPBD is not represented as an exact
  ledger machine anywhere in any report.
- G6 determinism: P9 holds in the adopted mode. Any byte-identity failure is
  a reported adoption blocker, never rounded away.

Recorded comparisons (mandatory, unrounded; they inform but do not by
themselves authorize adoption):

- G7 mode comparison: P11's D1/D2 results decide whether adoption may rely on
  native atomics, requires RUN_TO_RUN mode, or must record a blocker.
- G8 performance/memory vs the preserved baseline: per-tick latency
  distributions, device memory per stage, transfer per stage and renderer
  timing measured for the candidate AND for the preserved existing baseline
  under the same warmup/measured protocol on the same host, after warmup.
  Comparisons are reported with full distributions; the adoption
  recommendation must cite them; the fork-rebuild and diagnostics-readback
  costs are line items. Harness-elapsed never appears as tick latency.

Decision rule: the author of this preregistration claims NO adoption
authority. Gates G1-G6 hard-pass plus honest G7/G8 reports form the evidence
package; the serialized publication owner and the independent review
(Sergeant Flash review through the Lieutenant) decide adoption. Independent
review precedes any enablement, engine-completion, or production claim
(PLAN step 8). A model that merely runs is not qualified; a reviewer role
carries no merge authority.

---

## 6. Not-claims

1. This is an explicitly SYNTHETIC engineering fixture. No parameter derives
   from measured macaque anatomy; nothing here qualifies macaque anatomy,
   tissue, muscle, or biological movement.
2. No game completion is claimed or claimable from this campaign. The runtime
   snapshot consumer, committed runtime capture and state/frame join do not
   exist yet; the current adapter and replay bundle are not a captured game
   demonstration.
3. No backend adoption, production enablement, solver equivalence, real-time
   performance, cross-GPU determinism, or universal parallelism claim is made
   by this preregistration or by any single passing gate. `fork()` fresh
   solver history is a declared execution policy, not a persistent-history
   equivalence.
4. The construction check's pass is software/API validation with ZERO physics
   ticks; it is not physics evidence.
5. The E/nu mappings are authored parameter mappings, not a calibrated
   material; the XPBD energy is a constraint potential, not STVK/Neo-Hookean.
6. No positive behavior or impossibility conclusion may be issued from the
   unpublished draft or from this document; both bind only future measurement.

---

## 7. Amendment law and publication path

- This preregistration publishes through the ONE serialized publication owner
  (existing one-writer Git path, commit BEFORE any gated experiment, existing
  commit trailers/review/push/acceptance rules in force; unsquashed lineage
  preserved). A package seal is not a substitute for the commit. Suggested
  repository destination: `tools/monkey_campaign/coupled_backend_prototype/SCIENTIFIC_PREREGISTRATION.md`
  beside the preserved draft. Subsequent measurement packages pin to the
  published prereg commit.
- Any change to a frozen value, tolerance, schedule, mode, hash scope or gate
  after any observation requires a prospective amendment published the same
  way, plus a fresh pinned attempt. Scenario re-runs after peeking are
  prohibited.
- Refused, failed and BUSY (exit 75, retry with >= 10 s backoff) jobs are
  recorded alongside passes; missing or skipped checks are stated explicitly,
  never silently omitted.

---

## Appendix A — Input identity chain (sha256)

Recorded in `E:/ChimeraWork/monkey-coordination/cbp-prereg/EVIDENCE.md`.
Key anchors: sealed manifest
`62a89fa864f41f688fa4b089afbb801b458e8af28ad376c311e554f6a4c01a6d`;
base/source `65a23111877f587d0568942a354b7f9310786b0c`; draft
`7e05fbb11fbd1d3950a7c0bc78948da892210d096a91ed5b4dad87722cb92585`;
fixture.py `d796311539d4cf8c830e8aa17acb8997f9237693c2f6e01812ecf84ff2ae0633`;
module_contracts.json `6208228f4a5ea28cea113f3f77adee0467fd7b8fffbb8d953aa1c28959d6e15b`;
verified construction job `c212c4f6d63b46dab5577ee04768a218` (0 ticks);
parallel-module canonical job `4bac9824b487472db45bc5d8a2903d69`.

## Appendix B — Draft traceability

| Draft item | Completed location |
|---|---|
| Draft prediction 1 (drive via solver, falsifier: pose injection/zero drive) | P2 |
| Draft prediction 2 (reciprocal attachment, budget) | P4 |
| Draft prediction 3 (support only in contact; floor removal; power cut) | P5, P6, P7 |
| Draft prediction 4 (RUN_TO_RUN byte identity x3) | P9 |
| Draft prediction 5 (snapshot join) | P12 |
| Draft prediction 6 (dt refinement, no unconditional order) | P10 |
| Draft instrumentation: same-stage energies, actuator work, support reaction, residual not heat | P3, P5, section 4.4 |
| Draft instrumentation: private solver history / weaker candidate-only scope | section 1.4 hash scope, P7, G6 |
| Draft instrumentation: runtime consumer + capture | P12, section 6 |
| Draft instrumentation: bounded queue jobs, atomic-mode same inputs | sections 4.1, 4.2, 4.5, P11 |
| Draft instrumentation: warmup, latency distributions, compile-not-tick | sections 4.2, 4.3 |
| Draft closure: no conclusions from draft; amendments prospective | sections 2.4, 6, 7 |
