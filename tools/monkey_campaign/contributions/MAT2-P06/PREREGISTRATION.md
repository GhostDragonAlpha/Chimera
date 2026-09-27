# MAT2-P06 — PREREGISTRATION (frozen before implementation)

Card: MAT2-P06 "Choose release acceptance limits" (planning id P06, kind=decision).
Attempt: `6ecad9d537c346c4a31e9ce7b48a1fc7`, agent `arrival-e43f2a7138c44240b07bc79f0e15176a`.
Criteria: `adfd6c0c8aa993c1ed0c5379a5fe790b8949ea4786ccc7865863b23c8b4d9ce8`.
Profile: `records` (offline; numerical evidence required; no camera fields).
This file is written BEFORE `implementation.py`, the reference recovery and the
generated artifact. It freezes the statement, prediction, falsifier and the exact
applicable probes.

## done_when (exact, two clauses + material-first split duty)

1. "Supported hardware, controls, terrain/trunk envelope, session duration,
   latency, frame-time and stability limits are frozen before acceptance trials."
2. Material-first addition: "Freeze numerical/convergence/energy/contact/performance
   limits and camera-visible player outcomes before experiments."
3. "Report first walking-through-woods acceptance separately from later full
   climbing completion."

Card law (recorded observation): "No numeric product-wide limits supplied; do not
fabricate them." Decide-phase law: find the recorded ruling for this exact
decision; if absent, provide the smallest evidence-backed alternatives; do not
choose policy, geometry, thresholds or physical parameters by default.

## Statement

A record-bound release-limits contract for MAT2-P06 can be assembled WITHOUT
inventing any number, by (a) crosswalking the lead-accepted ONT-P06 release-limits
proposal (archived board, PR #156 head `2148f8d3c722cd41ec05297775538fd949a226e0`,
criteria `7bea081e57fa35a83fcedfc7dfc8243c63d027448b0d9b104eab179dd96f1333`,
independent PASS review `43b415fe0db04e72b9f5e047754839c4`, lead verdict ACCEPTED)
onto the byte-identical first done_when clause after re-verifying its 15 derived
values and 4 operator decision requests from recovered pinned bytes, and (b)
freezing the material-first clauses from existing pinned records: the coupled-arm
native validation receipt (numerical/convergence/energy limits and their
applicability boundary), the material-first catalog (camera-visible player
outcomes, checkpoint acceptance texts, demonstration order), the pinned engine
headers and walker validation source (contact-model and friction status), each
carrying `{path, commit, blob_sha256, method, locator}` provenance. Every limit
for which NO record supplies a number is recorded as `OPERATOR_DECISION_REQUESTED`
with options and a recommendation, never silently chosen.

## Prediction (named before execution)

1. All 10 legacy play-repository pins (`commit:path`, content sha256) still
   resolve read-only in `E:/ChimeraWork/monkey-play-20260924` and re-derive the
   15 carried values bit-identically to the accepted proposal
   (sha256 `80d567eaecc432552e5605eda625d6942fe533903386faccf789a0f92744140e`);
   its 4 operator decision requests carry over unchanged.
2. The coupled-arm native validation receipt at source-repository commit
   `32105f18d7340ba14d4764cc1e0d3abb4496f80f` contains, as written record text,
   a numeric energy/store residual bound (1e-5 J), a fourth-order free-trajectory
   refinement requirement and an explicit applicability boundary (qualified only
   for that source model, gains/caps and timestep; no unconditional stability
   claim), plus measured metrics (worst ten-second residual,
   free-refinement ratio) demonstrating the bound was met.
3. The material-first catalog at source-repository commit
   `59f81d4dcb1cf45192bde124c1e35510fb439f1b` (content identical to the live
   on-disk catalog, sha256 `8fa2e1409a2da1e3cbe70a84f59f7620a61d3eed12519171190e9c61543cb272`)
   supplies, as frozen text: the walking and material verification profiles
   (scenario, falsifier, clean-view requirement, camera-required fields), the
   MAT-WOODS/V07/S05 checkpoint acceptance texts, and the 17-entry
   `first_visible_sequence` in which walking (W10/F06) precedes climbing
   completion (K08) and feature acceptance (S05).
4. The pinned walker validation source at commit
   `8707551c072a847e1d4d85b50202f3e89d048198` line 60 records
   `CONTACT_FRICTION = 0.6` as a bare literal with no source citation on the
   line, and the pinned `gait_controller.hpp` records a single-plane contact
   scalar (`plane_model_y_`) — i.e. the records support a contact/friction
   STATUS freeze (placeholder unevidenced; native contact single-plane), not a
   numeric contact tolerance; any numeric contact/friction/performance ceiling
   absent from records therefore lands in `OPERATOR_DECISION_REQUESTED`.

## Falsifier (any one fails the contribution)

- A numeric appears in the emitted contract that is neither re-measured at run
  time from sha256-asserted recovered bytes nor an `OPERATOR_DECISION_REQUESTED`
  option/recommendation (zero un-sourced numerics).
- The re-derived carried values differ from the accepted ONT-P06 proposal
  (crosswalk zero-diff must be empty), or a pin drifts / a pinned identity is
  missing and the code does not refuse loudly.
- A claim that walking-through-woods and full-climbing acceptances are merged
  into one report, or a report structure not derivable from the pinned catalog
  checkpoint graph.
- An operator decision silently decided (a taste/policy limit emitted as final).
- Dependency misstatement: MAT2-P01 recorded as anything other than DONE at
  merge `97993cbefaf00380803d8e67652ac51d50c37d06` (PR #192), or ONT-P06
  lineage recorded as anything other than archived/DONE (PR #156 ACCEPTED).
- Tests fail on CPU-only deterministic rerun, or pass only with network/GPU.

## Frozen probes (records profile — exact sources, locators, checks)

- Recovery (read-only, both repositories): `git -c safe.directory=<repo> -C <repo>
  show <commit>:<path>`, bytes written once into `reference/<path>`, sha256
  asserted at import; `git cat-file -e <commit>:<path>` identity re-check; no
  live-worktree file is read by the derivation; repositories are never written.
- Carried limits (15) — play repo pins identical to the accepted ONT-P06
  correction: clearing_declaration.json@c9aee37c (extent/spawn/clearance/
  envelope/seed), trunk_declaration.json@b4de4de8 (site/radius),
  session_flow.py@42f7cdc4 (DEFAULT_FLOW_BINDINGS),
  input_mapper.py@8550b634 + command_record.py@e028d6fb (input surface,
  recovered but unused numerically, kept for surface identity),
  slice_server.py@0b3b22a5:44/48/449 (settle vy/sink recorded bar + arithmetic
  cross-check, poll cadence), acceptance.py@8294053b:19-20 (episode cap/eval
  window), receipt_wave47.json@33e7a444 (worst moving ledger, all occurrences
  must agree), gait_controller.hpp@8cec4a6b:1961 + earth_environment.hpp@ee52a99f:91
  (tick 300 Hz + substeps 4, cross-checked).
- Material-first limits (new): coupled_native receipt limits[] text parse
  (residual bound; refinement order text; applicability boundary strings) and
  metrics parse (worst_ten_second_energy_residual_J,
  free_trajectory_refinement_ratio); catalog profile/checkpoint/sequence parses
  (walking scenario+falsifier, material falsifier, MAT-WOODS/V07/S05 acceptance,
  clean-view flags, camera-required fields, first_visible_sequence);
  gait_controller.hpp single-plane contact locator; walker CONTACT_FRICTION
  literal + no-citation-on-line check.
- Crosswalk checks: programmatic zero-diff of 15 values + 4 decision requests
  against the accepted proposal copy (sha256 asserted);
  negative checks: tampered reference byte -> PIN DRIFT refusal; missing
  reference file -> pinned_source_missing refusal; nulled commit ->
  git_identity_missing refusal; disagreeing tick pins -> tick_pins_disagree
  refusal.
- Operator decision requests: mailbox `suggestion_box.py list` re-checked before
  submission — no operator answer exists to the 4 carried requests (checked
  2026-09-27); they carry forward unchanged; new requests are added only for
  material-first numerics absent from all records.

## Applicability boundary (recorded, not hidden)

- The coupled-arm receipt limits are qualified (by their own text) only for that
  source model, admitted gains/caps and timestep; they are frozen here as the
  FIRST record-backed numerical/convergence/energy bars for material-coupled
  trials, not as universal physics. M07/M08 must declare their own timestep and
  convergence statement against these bars or request better ones.
- The W03 walking anchor (30.970714 J) is baseline evidence until rerun against
  the selected material representation (catalog W03 material-first note).
- Absolute cost-of-transport limits stay blocked on the D-W04 denominator
  registration (mailbox Q-34439597b1774332972da4d8b4ec6b2a NEEDS_EVIDENCE;
  supersession question Q-136fedaa492e4375a5b6f7589345e881 OPEN).
- This is a decision/records artifact: it freezes limits and decision requests;
  it runs no physics, claims no gameplay or human acceptance.
