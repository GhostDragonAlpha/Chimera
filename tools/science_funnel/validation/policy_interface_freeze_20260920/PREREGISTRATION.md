# RULE 0 PREREGISTRATION — POLICY INTERFACE FREEZE (2026-09-20)

Lane: `lane/policy-interface-freeze-20260920` (Agent: ifreeze) @ bd4bf630.
This file is frozen BEFORE the aliasing audit's build, BEFORE the interface table is
generated, BEFORE any command-record or certificate code is written. The order is the
law: (1) this prereg, (2) the audit, (3) the freeze artifacts, (4) the measurements,
(5) the receipt. Nothing below is edited after a measurement lands; the receipt appends.

## THE DECISION BEING SERVED (Astra round 5, settled)

Hierarchical control: derived reflexes fixed below; command-conditioned policies WITHIN
behavior families at 20 Hz over 300 Hz physics (15-tick holds); certified
option-transitions between families; a planner on top. The policy interface — the
observation content and the command encoding — is the irreversible choice: once skill #1
trains against it, changing it retires every trained weight. So it is frozen first, on
evidence, by this lane.

## THE THEORY (statement)

THE 80-FIELD OBSERVATION + THE VERSIONED COMMAND RECORD ARE A SUFFICIENT AND SOUND
DECISION INTERFACE for the family-policy layer. Sufficient: every quantity a certified
transition needs to guard entry/termination is either in the 80 fields or in the
certificate's registered timeout/fallback (which do not need to observe). Sound: no two
states the policy must treat differently present it bit-identical 80-field observations
while the interface's own command record is identical — except where the audit REPORTS
the alias (a necessary alias of the record set, named by field and evidence).

A description survives any result; a theory can lose. The falsifiers below are named
before the run.

## FALSIFIERS

### F1 — STATE-ALIASING (the audit)

**Statement.** Two live walk states that differ in reflex mode, or in deformation
velocity beyond the machinery's own scale, or in contact regime, never present the
policy bit-identical 80-field observations (as projected by
`observation_schema.project_trace` v2 from the per-tick record the CPU walk trace
determines).

**Prediction (unmeasured before the run).** On the live CPU walk, the aliased-pair
count over the recorded horizon is ZERO once the observation carries the walk's own
phase clock and per-foot contact/force census — the phase alone staggers ticks enough
that float32 sin/cos plus contact census separates regimes.

**Fires if.** There exists a pair of ticks (t1 != t2) in the recorded live walk with
bit-identical float32 80-field observations (all 80 values bitwise equal) whose labels
differ in ANY of:
  (a) REFLEX MODE: the fore stepping clock mode (0 stance / 1 swing, per leg, the
      [dvf] `mode=` read), or the capture-event counter moved between the ticks, or
      one tick is inside the settle window [0, 59] (the machinery's own settle freeze,
      the F-Gfore `ticks0-59` convention) and the other is not;
  (b) CONTACT REGIME: the per-foot touch pattern (8 pad gaps vs the release law's own
      band edge kTouch = 1e-5 m) differs between the ticks;
  (c) DEFORMATION VELOCITY: any hind or fore pad's per-tick gap delta differs by more
      than kSinkRateMax = 2.349e-3 m/tick (the wave-27 mined worst sink rate — the
      machinery's own derived scale, zero new numbers), or the per-tick body advance
      differs by more than 0.05 m/s (the command-adapter receipt's own frozen graded
      spread bar, F_COMMAND_AUTHORITY_2 clause (c) — this campaign's pre-registered
      velocity scale).

**Pre-committed action on FIRE.** REPORT the pair class and a witness pair (tick
indices + the differing label quantity + the field(s) that would have separated them),
honestly, in the receipt. NEVER speculatively expand the field set — the 80-field
table is not amended by this lane. The freeze stands at 80 fields; the finding is
carried to the planner lane as the measured reason certified transitions must guard
mode boundaries. The verdict is whatever the search returns.

**Declared scope (honesty).** The audit runs on the channels the CPU walk trace
actually determines: gait phase (the controller's own [dv] phases), the 8-pad
contact/force census ([dvp]/[dvfp]), the aggregate + per-foot + intervention +
clock + health + phase-dynamics groups, and the 16 pad-split channels ONLY where the
trace determines them. The channels the trace does not determine (body velocity group,
command echo groups, limiter saturation, the class flags) are DECLARED UNAVAILABLE
(mean-filled by the projector — the mask convention). Aliases found among them are
therefore NECESSARY aliases of the record set: the receipt says so explicitly rather
than claiming the deployed sensor path is blind. The audit's instrument is a
scratch `GAIT_EVENT_TRACE` build; its unexercised stdout must be the ship stdout
byte-for-byte (sha 71065ac5..., the wave-38/command-adapter fence) or the audit is
VOID (the instrument perturbed the walk it claims to observe).

### F2 — FREEZE-DRIFT (the unittest)

**Statement.** The frozen tables — the 80-field interface table (JSON + code), the v1
legacy block (64 fields), the command-record v1 projection law, the option-certificate
v1 schema, and the deployment-inference freeze block — are pinned by version constants
and by digest; any change to their content without a declared version bump fails a
unittest.

**Prediction (unmeasured before the run).** The pinning test suite passes at commit
time and every later mutation of a pinned table without its version bump is caught.

**Fires if.** (a) any pinned digest (table JSON sha, canonical projection bytes,
existing-manifest hash) differs from the pinned value at test time, or (b) a mutation
of any frozen structure (field order, field name, projection arithmetic, record field
set, certificate required keys, inference-freeze required keys) leaves any pinned test
green, or (c) `policy_manifest.load_manifest` rejects or re-hashes the EXISTING frozen
manifest `typeb_p3_20260921/policy_manifest.json` differently after this lane's
backward-compatible extension (its manifest_hash must be byte-identical to the
pre-lane value, read-only).

**Pre-committed action on FIRE.** Fix the pin or declare the version bump; a failing
falsifier is never tuned away.

## THE FREEZE ARTIFACTS (what this lane ships)

1. `observation_interface_v2.json` + `INTERFACE.md` — the 80-field table: per field
   index/name/group/source/unit/frame/availability/missing-value semantics/meaning, and
   the normalization actually applied (mean, std, clip 8.0, from the v2 manifest
   section the obs-split lane measured). Generated from `observation_schema.py` +
   the pinned `obs_section_v2.json`; pinned by sha in the freeze test.
2. The aliasing audit receipt (F1 verdict + witness evidence + the run harness .ps1).
3. `command_record.py` — CommandRecord v1: `v_forward` (m/s, non-negative — the plant
   law's own max(0,·) domain), `yaw_rate` (rad/s, RESERVED: carried in the record, ZERO
   measured authority — the typea receipt reserved commanded_heading for a later lane;
   this lane does not invent it), supported ranges (in-band [0, 0.763625] veto-free
   measured R1-R4; out-of-band legal, absorbed by the machinery's own reach annulus,
   measured R5), rate limits (DECLARED UNLIMITED at v1 with the measured evidence:
   step commands R1-R3 onset 7 ticks <= hold 15, veto-free horizons 137-222 — no
   rate-limit number is invented; the schema carries the fields so v2 can fill them),
   zero-speed semantics (v_forward = 0 is the plant law's own x_off = 0 — a legal
   command, NOT a stop bar; stopping bars are a different lane's job), and the
   projection law: `record -> family adapter -> fixed actor input`, where the v1
   adapter routes ONLY `commanded_target_velocity_x = v_forward` (the typea channel)
   and the old actor's command-conditioning input at v1 is EMPTY — the old actor sees
   exactly its old projection. TEST: a v2 record through the v1 adapter is
   bit-identical to the v1 record's projection (the v1 adapter reads only the v1
   field set; future fields cannot leak).
4. `option_certificate.py` — the certified option-transition schema v1: entry guard
   (predicates over the FROZEN 80-field vocabulary), command payload (record version +
   adapter version the option consumes), termination conditions, registered timeout
   (ticks), named fallback (must be a REGISTERED option). Validator + three DECLARED
   example certificates (walk_v1, recovery_v1, rear_up_v1). HONESTY: these are schema
   examples, not certified behaviors — rear-up does not exist yet; the certificates
   make zero behavior claims (the dummy-weights convention).
5. The deployment-inference freeze: `policy_manifest.py` gains a versioned OPTIONAL
   inference-freeze block (deterministic action selection, compute precision,
   exported-graph pinning, normalization-constant digest). Backward-compatible: the
   block is validated only when present; the existing frozen manifest loads with its
   pre-lane hash unchanged.
6. Tests: freeze-drift (F2) + projection bit-identity + certificate validation +
   manifest backward compatibility; a 3-run byte-identity replay of the frozen P3
   action stream; the lane receipt; commits at each milestone; push of this branch.

## NOT THIS LANE (named, so nobody waits on it)

Stopping bars for v_forward = 0 (the zero-speed stand/stopping criterion), the yaw-rate
authority derivation, any reflex change, any first_skill prestage content, any gait_*
validation or gait_controller.hpp byte, any engine behavior. The command-adapter
receipt's R4 lesson is carried as a SEMANTIC note on the record (no constant
pinned-from-entry feed-forward); enforcing it is the planner's job.
