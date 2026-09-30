# PREREGISTRATION — MAT2-G03 "Evaluate tendon lengths and moment arms"

Preregistered 2026-09-30 by the Worker-implementer (agent id
arrival-f0cc8f5a78794f8ea977ae87b8a75064, attempt
39e6d5fbbba74fd7981bb5df3950b39c) BEFORE authoring the sweep generator,
validators, falsifier probes, report or any capture frame. This file is
committed ALONE, before any implementation artifact, so the freeze is
git-provable (separate-first). Inputs were read read-only from the pinned
sealed upstreams at the line tip; every count, window and observed residual
below was computed from the pinned bytes BEFORE this freeze and is the exact
statement the deliverables must reproduce (the validators recompute from
bytes and refuse any disagreement).

Composed against CARD_STARTER.md v2 (v1 base + v2 evidence-anchoring and
GPU-banking additions), house standards IMPLEMENTER_CHECKLIST.md (G1-G9) and
TOOLKIT.md (P1-P9), card-kit (batch_gates.py 9 CPU gates; templates),
FORMAT_SPEC.md, CODEC_STANDARD.md (FFV1 `-level 3 -g 1 -fflags +bitexact`)
and the C17 stiffness-sources study law
(`c17-stiffness/STIFFNESS_SOURCES.md`: NO lawful measured stiffness pin;
authored constants need the arithmetic falsifier).

## 0. Existence statement (what did NOT yet exist at freeze)

At this commit, none of the following existed: `tendon_sweep.py`,
`tendon_sweep.json`, `sweep_trace.json`, `qualification_receipt.json`,
`evidence/falsifier_receipt.json`, `evidence/decode_roundtrip.json`,
`make_report.py`, `report.md`, `lint_report_numbers.py`,
`test_tendon_sweep.py`, `make_capture.py`, any `evidence/` file, any
`capture/` file, or the card `.gitattributes`. No kinematic evaluation,
sweep, moment-arm computation or capture for this card had been run except
the pre-freeze prototype values quoted in sections 7-8 (computed once from
pinned bytes to freeze them; the validators recompute them from bytes and
refuse any disagreement). No GPU job is planned or needed: the C18 pose
sweep is pure CPU kinematics (CPU-FIRST satisfied by construction; the GPU
bank is not applicable to this card and nothing is submitted).

## 1. Task identity

- Task: MAT2-G03 (planning id G03) — "Evaluate tendon lengths and moment
  arms"; kind `implementation+verification`, group "Grasp and climbing
  mechanics"; depends on MAT2-A09 (sealed, merged PR #277).
- criteria_sha256: `d489995ecb7c645013084987bbf3f5d54cd4abca2e7bec2d1afa6db0ff70c5aa`
  (join packet; asserted equal to the registry card at capture time).
- scope_sha256: `cb5475f8486197a973edc4360b177fc31a629c4f0979ebf80dd76aae57996097`
  (re-verified live via `execution_plan.py --expected-scope <sha> --task G03`,
  exit 0).
- Attempt: `39e6d5fbbba74fd7981bb5df3950b39c`; agent id
  `arrival-f0cc8f5a78794f8ea977ae87b8a75064`; card slot 2.
- Verification profile (read mode=ro from the registry at capture time,
  G7/P7): id `tendon-pose-sweep`, kind `motion`,
  `numerical_evidence_required: true`, `clean_view_required: true`, views
  ["chain overview", "endpoint close-up", "alternate pose/axis view"],
  diagnostic_layers ["resolved tendon endpoints and paths", "joint axes and
  stable IDs", "length and moment-arm traces"], 16 camera_required_fields,
  nonvisual_reason: null — CAPTURE IS REQUIRED (motion: video, state_binding
  kind trace, artifact_locator kind video).
- Base: line tip `f6cbf7a996eff27495575375d64ba38ea3e77b2e` (= merge of PR
  #277, MAT2-A09 = `origin/astra/gait-capture`); attempt branch
  `codex/monkey-mat2-g03-39e6d5fbbba74f` cut from the tip; publication
  branch `review/MAT2-G03`, PR base `astra/gait-capture`.
- Provisioning disclosure: `worker_checkout.prepare` failed at its
  slot-branch fetch step (remote branch-2 non-fast-forward vs the
  source-copied ref — the same dead slot history the sealed A09 attempt
  recorded). Provisioning was completed manually in the attempt's private
  shared clone only, following the sealed A07/A08/A09 precedents: candidate
  branch cut directly from the sealed tip; no numbered branch fetched,
  pushed or modified; no history rewritten anywhere. Recorded in
  `checkout_identity.json`.
- task_id SHORT form used in every generated artifact: `G03`.

## 2. done_when (verbatim) and binding observations

done_when (verbatim): "Relevant pose-range outputs are finite and
independently checked; unresolved bodies cannot appear as zero arms"

Registry observation (verbatim): "Only BRD paths functional in last forearm
report; reconcile new evidence"

Card falsifier (verbatim): "A violated task acceptance clause, hidden/clipped
required geometry, inconsistent numeric evidence or mismatched
clean/diagnostic state fails."

Profile falsifier (verbatim): identical text.

C18 contract law (completion map, verbatim): "Length l(q), signed moment arm
r_j=-partial l/partial q_j under declared convention; torque contribution
r_j F"; check "Finite differences/virtual work and unresolved-owner
rejection".

## 3. Lawful-close discipline (declared BEFORE implementation)

- The sweep is a DECLARED-MODEL evaluation: forward kinematics of the
  OpenSim chain declared in the sealed osim/M02 pins. It invents NO
  geometry, NO constant, NO wrap model and NO force. Every emitted number
  is derived from pinned bytes by the declared pipeline.
- The A09 frame law is honored: the A09 package composes NO transform
  between its two declared frames and carries terminal resolutions
  verbatim. THIS card performs the downstream declared-chain evaluation the
  A09 contract registered as REQUIRED (C05 FK closure + finite differences;
  C18 l(q)/moment arms + unresolved-owner rejection). The A09 terminal
  ledger (3 mapped / 14 pending_assembly_mapping / 31 not_on_hand_body) is
  carried verbatim and governs what may be claimed about the MUTANT
  assembly; the sweep's own evaluation frame is the declared osim chain and
  is labeled as such everywhere.
- The C17 stiffness law binds: this is a KINEMATIC card. Zero stiffness,
  damping, couple or force constants are pinned, consumed or emitted. The
  C18 torque-attribution step `r_j * F` is NOT evaluated: no lawful
  measured force pin exists (A08 U1/U3; the sealed Fmax values are named
  placeholders). The step is disclosed explicitly_unresolved, never
  silently dropped, and no placeholder force is multiplied in.
- The A08 placeholders stay NAMED placeholders carried by reference
  (tendon_slack_length 0.2 cm x14, Fmax 30 N floors x11): they are NOT
  compared against any sweep output (no lawful window exists for them) and
  they never substitute for a measured band. The kappa/couple
  constant-pair arithmetic inconsistency (5.1 orders, STIFFNESS_SOURCES
  section 4) belongs to C17/G02, not this card; it is cited, not
  recomputed.
- Wrapping model: stays explicitly_unresolved exactly as A09 recorded it.
  The sweep emits the declared no-wrap reduction: straight-line polyline
  segments between owned path points. Named envelope (declared, not
  measured): for any future lawful wrapped model, l_wrapped(q) >=
  l_polyline(q) at every pose (a wrapped path is never shorter than the
  straight polyline between the same waypoints); the emitted l(q) is
  therefore the LOWER envelope of the routing-length class.
- No upstream byte changes: A06/A07/A08/A09/M02 documents are READ-ONLY
  inputs pinned by sha; the completion map is a read-only catalog.

## 4. Base, reconciliation and dependency INPUT PINS (sha256 per file)

Base head `f6cbf7a996eff27495575375d64ba38ea3e77b2e` equals the sealed line
tip; the attempt branch is a fresh branch at that sha. Repo inputs are read
from the candidate commit's working tree (sparse checkout of the named
contribution dirs); host inputs at their absolute pinned paths. The
generator verifies every pin against on-disk bytes before any emission and
refuses `input_pin_drift` on mismatch.

| role | file | sha256 |
|---|---|---|
| A09 grasp anatomy package (48 owned path records; terminal ledger; frame chain; C18 inventory) | repo `tools/monkey_campaign/contributions/MAT2-A09/grasp_package.json` | `0a70adb1029d860ac9504683d77c2e94be2634724c63479f827fcbc8fcd97d24` |
| A08 parameter envelope (39 bio rows; U1-U8; named placeholders) | repo `tools/monkey_campaign/contributions/MAT2-A08/parameter_envelope.json` | `2fb43fd44f13e8b927142d72b79d36246ee7d71fd954a39ffeb12b74dc716424` |
| M02 pinned graph rows (11 body frames at default pose; 7 coordinates; 39 muscle path points; scope) | repo `tools/monkey_campaign/contributions/MAT2-M02/data/graph_pins.json` | `849f9988d1a6ccb451bb45d79f298dd954c4e5605acd19d7d882a5c70a285b97` |
| osim source of record (joints, axes, coordinate ranges) | repo `tools/monkey_campaign/contributions/MAT2-M02/data/macaque_arm/monkeyArm_current.osim` | `4148aee2c8dda1dcb0918496ad7c5e1adcf4ebabde0a68a3e0dc67faec67b895` |
| completion-map catalog records (C18 row; G03 row + observation) | repo `tools/monkey_campaign/monkey_completion_map.json` | `3efbfb141299d7cad63724431f7e5269febe15eee68d812b80d91de324385b84` |
| A05 mutant hand structure (capture-context law precedent; not consumed numerically) | repo `tools/monkey_campaign/contributions/MAT2-A05/mutation_structure.json` | `48b037593f63ec473947d787077ab6fbcd3b364afd15765bff508e7d54f45649` |
| osim host identity check (same bytes as the repo pin) | host `E:/PythonChimera/tools/science_funnel/data/macaque_arm/monkeyArm_current.osim` | `4148aee2c8dda1dcb0918496ad7c5e1adcf4ebabde0a68a3e0dc67faec67b895` |

Runtime verification refuses `input_pin_drift`.

## 5. What the deliverable IS (declared in advance)

ONE versioned sweep document, `tendon_sweep.json` (schema
`chimera.g03_tendon_pose_sweep.v1`, revision 1, canonical JSON, stable ids,
`object_id mat2_g03_tendon_pose_sweep`), built by `tendon_sweep.py` from the
pinned inputs (`--emit`; `--verify` recomputes every carried value from the
pinned bytes and refuses disagreement; `--falsify` runs the tamper arms with
clean controls first); ONE per-tick trace `sweep_trace.json` (the
capture's state_binding trace target); `qualification_receipt.json` (schema
`chimera.qualification_receipt.v1`) mapping every done_when clause to its
evidence; the motion capture (FFV1 mkv + manifest/context/validation
receipt + frame-hash identity) bound to the trace sha and the document sha;
`report.md` GENERATED by `make_report.py` from receipts only (zero
hand-transcribed numbers), policed by `lint_report_numbers.py` (+`--selftest`);
named checks in `test_tendon_sweep.py` (unittest).
Determinism: two consecutive `--emit` runs are byte-identical.

## 6. Frozen implementation statement — the declared evaluation

1. `identity` — task, criteria, scope, attempt, agent, base, profile
   snapshot sha, preregistration sha, date_frozen.
2. `input_pins` — the section-4 table as verified bytes.
3. `kinematic_spine` — the 11 declared bodies and their joints parsed from
   the pinned osim: 4 WeldJoint chain links (ground->sternum->clavicle->
   scapula; ulna1->ulna; radius_jcc->radius; radius->radius1 via
   wrist_tmp) and 4 CustomJoints (shoulder scapula->humerus; elbow
   humerus->ulna1; ulnar_radial ulna->radius_jcc; wrist radius1->hand),
   with per-joint location/orentation offsets and TransformAxis
   declarations exactly as parsed (no wrapping, no additional joints
   invented; the wrap model stays explicitly_unresolved). Coordinate
   table: 7 coordinates with declared defaults and ranges
   (shoulder_adduction/rotation/flexion; elbow_flexion default
   1.57079633 rad range [0.34906585, 2.44346095]; radial_pronation default
   0 range [-1.57079633, 1.57079633]; wrist_flexion default 0 range
   [-1.30899694, 1.57079633]; wrist_abduction default 0 range
   [-1.04719755, 0.78539816]). FK composition declared: child =
   parent * T(location_in_parent, orientation_in_parent) *
   R_axis1(q1) R_axis2(q2) R_axis3(q3) * T(location, orientation)^-1
   (body-fixed XYZ orientation convention; all TransformAxis locations
   default zero; every axis location carries no offset).
4. `fk_closure_check` (C05 independent check #1) — forward kinematics at
   the declared default pose MUST reproduce the pinned M02 body_frames for
   all 11 bodies. WINDOW (frozen): max abs position or rotation-element
   deviation <= 1e-12. Pre-freeze observed: 1.11e-16. FALSIFIER: any
   larger deviation refuses `fk_closure_refused`.
5. `sweep_spec` — sweep coordinate `wrist_flexion` over its full declared
   range [-1.30899694, 1.57079633] rad at 21 uniform ticks (tick 0..20,
   q_k = lo + (hi-lo)*k/20); all other coordinates held at declared
   defaults. Scope boundary (explicit, task-owned subset): shoulder
   coordinates are NOT swept and shoulder moment arms are NOT emitted
   (shoulder-chain bodies are outside the grasp scope per A09).
6. `sweep` — per tick, for each of the 13 grasp-scope muscles (A09 frozen
   set), with every path point transformed by the declared FK of its
   OWNER body: (a) `l_m` = polyline path length; (b) signed moment arms
   about `wrist_flexion` and `wrist_abduction`: `analytic_m` from the
   rigid-body velocity identity dL/dq = sum_i (v_{i+1}-v_i) . t_hat_i with
   v_i = omega_j x (p_i - c_j) for points on bodies in the joint's distal
   subtree and v_i = 0 otherwise (owner-body-gated), `fd_m` by central
   finite differences with h = 1e-5 rad, residual = |analytic - fd|;
   (c) finiteness flag; (d) per-record owner resolution carried from the
   A09 terminal ledger.
7. `static_checks` — the same evaluations about `elbow_flexion` and
   `radial_pronation` at the default pose (fixed-pose arms; distal
   subtrees ulna1-subtree and radius_jcc-subtree).
8. Windows (frozen BEFORE implementation; each can FAIL):
   - W1 FK closure: <= 1e-12 (observed 1.11e-16; a wrong joint offset,
     axis or convention moves it to >= 1e-9 scale).
   - W2 identity agreement: residual <= max(1e-8 m, 1e-6 * |analytic|)
     for every arm at every tick (observed max 9.7e-12 over the full
     13 x 21 x 2 sweep + static checks; a wrong axis, wrong subtree gate,
     dropped point or wrong sign moves residuals to >= 1e-3 scale).
   - W3 envelope: |r_mj(q)| <= 2 * R_mj(q) where R_mj = max over the
     muscle's path points of the distance to the joint axis line at that
     pose (derived: each point contributes |v| <= 2*R per unit q;
     observed global bound 0.359 m). FALSIFIER: any arm outside the
     window refuses `arm_envelope_exceeded`.
   - W4 finiteness: every emitted number passes math.isfinite.
   - W5 discrimination (arithmetic falsifier property): the W2 window is
     proven able to FAIL by planting a wrong-axis analytic value (FB4);
     the planted residual must exceed W2 by > 1e5x.
9. `unresolved_owner_law` (the card's core clause) — the declared-chain
   evaluation is valid only for muscles whose EVERY path record's owner
   body is declared in the FK chain; such rows carry status
   `evaluated_declared_chain`. A muscle with ANY owner outside the chain
   is status `unresolved_owner` with `arms: null` (never 0.0, never a
   number) and the missing bodies named. The A09 MUTANT placement ledger
   (3 mapped / 14 pending_assembly_mapping / 31 not_on_hand_body) is
   carried verbatim on every row as `mutant_placement_ledger`: the
   declared-chain arms do NOT upgrade, repair or silently replace those
   terminal resolutions, and no row anywhere reports a zero arm CAUSED by
   an unresolved body. FALSIFIERS: FB2 plants a zero arm on an
   unresolved_owner row (`unresolved_zero_arm_refused`); FB5 drops a
   muscle from the frozen 13-set (`frozen_set_mismatch_refused`).
10. `reconciliation` (registry observation) — old evidence: the forearm
    report era recorded only BRD paths functional (observation carried
    verbatim). New evidence (this card, from pinned bytes): the A09
    package owns 48 path records across 13 grasp-scope muscles with
    per-record ownership and terminal resolutions (sha-pinned); the
    declared-chain sweep evaluates all 13 with finite, independently
    checked l(q) and signed arms without any wrap model; BRD itself is
    NOT a grasp-scope muscle (26 non-grasp actuators are parameters-only
    per A06/A09 law) and is therefore NOT evaluated here — named
    explicitly, not silently zeroed. The reconciliation closes the
    observation for the grasp scope and leaves the 26-actuator boundary
    standing.
11. `calculation_contracts` — C18 EVALUATED-WITHIN-SCOPE (l(q), signed
    r_j, FD + velocity-identity checks, unresolved-owner rejection
    delivered; torque attribution r_j*F explicitly_unresolved pending a
    lawful force source; wrap model explicitly_unresolved); C05 FK
    closure check delivered for the declared chain (closure + finite
    differences); C01 declared-chain note (the composed transform is the
    osim chain; the A05-mutant round-trip stays REQUIRED downstream,
    unchanged); C17 untouched (zero stiffness/couple numbers anywhere in
    the document, whole-document scan).
12. `explicit_gaps` — wrap model; torque attribution (no lawful F);
    shoulder arms out of scope; 26 non-grasp actuators parameters-only;
    mutant placement ledger unchanged (45/48 records not mapped);
    tendon_slack_length and Fmax placeholders named with their A08
    provenance classes and NOT consumed; the polyline l(q) is the lower
    envelope of the routing-length class (no wrap).
13. `checks` — preregistered predictions P1-P12 (section 8), gate codes,
    criteria hash identity.

## 7. Frozen counts (computed from pinned bytes before this freeze; the
validators must reproduce every count exactly)

- A09 package: 13 grasp-scope muscles; 48 path records (13 origin
  attachment + 13 insertion attachment + 21 path waypoint + 1 conditional
  waypoint); owner census {osim.body.radius 18, osim.body.hand 17,
  osim.body.humerus 8, osim.body.ulna 5}; per-muscle record counts
  abd_poll_longus 5, ext_carp_rad_brevis 4, ext_carpi_rad_longus 4,
  ext_carpi_ulnaris 3, ext_digiti 4, ext_digitorum 4, ext_indicis 4,
  flex_carpi_radialis 3, flex_carpi_ulnaris 3, flex_digit_profundus 4,
  flex_digit_superficialis 3, flex_poll_longus 3, palmaris_longus 4.
- A09 terminal ledger over the 48 records: 3 supported (mapped) /
  45 explicitly_unresolved (14 pending_assembly_mapping + 31
  not_on_hand_body); attachment interfaces 26 (2 supported / 24
  explicitly_unresolved). The sweep carries these verbatim.
- Declared chain: 11 bodies; 4 CustomJoints; 7 coordinates; the 4 record
  owner bodies {humerus, ulna, radius, hand} are ALL declared chain
  bodies, so all 13 muscles are `evaluated_declared_chain` in the osim
  model (and only in it).
- Sweep: 21 ticks; outputs 13 muscles x 21 ticks x (1 length + 2 signed
  arms x 2 methods) = 1638 numbers + static checks (13 muscles x 2
  coordinates x 2 methods arms + 13 lengths) = 78 numbers.
- Distal subtrees (frozen): wrist joint (body `hand`) subtree = {hand};
  elbow joint (body `ulna1`) subtree = {ulna1, ulna, radius_jcc, radius,
  radius1, hand}; ulnar_radial joint (body `radius_jcc`) subtree =
  {radius_jcc, radius, radius1, hand}.
- Pre-freeze observed residuals (validators must reproduce within W2):
  FK closure 1.11e-16; identity agreement max 9.7e-12 (sweep) / 2.2e-12
  (static checks).

## 8. Preregistered predictions (P1-P12) and gates

- P1 Pins: all 6 repo pins + 1 host pin verify against on-disk bytes at
  emit and at verify; any mismatch refuses `input_pin_drift`. FALSIFIER:
  FB1 mutates a pinned copy.
- P2 FK closure (W1) holds at the declared default pose against the
  pinned M02 body_frames for all 11 bodies. FALSIFIER: FB6 tampers a
  joint axis in the parsed spine -> `fk_closure_refused`.
- P3 Sweep totality: exactly 21 ticks; exactly the frozen 13-muscle set;
  every tick row carries every muscle; owner census matches section 7.
  FALSIFIER: FB5 (`frozen_set_mismatch_refused`).
- P4 Independence: every arm carries BOTH the analytic velocity-identity
  value and the central-difference value with residual within W2; the
  two derivations are independent (symbolic cross-product velocity field
  on owner-gated points vs numerical differentiation of the composed
  polyline length). FALSIFIER: FB4 plants a wrong-axis analytic value ->
  `arm_trace_disagreement_refused`; W5 discrimination proof recorded.
- P5 Finiteness (W4): every emitted number isfinite. FALSIFIER: FB3
  plants inf/nan -> `nonfinite_output_refused`.
- P6 Envelope (W3): every arm within 2*R_mj(q). FALSIFIER: any planted
  oversized arm -> `arm_envelope_exceeded`.
- P7 Unresolved-owner rejection (P-section 6.9 law): unresolved_owner
  rows carry null arms; no zero arm is attributed to any unresolved
  body; the mutant ledger is carried verbatim. FALSIFIERS: FB2; plus the
  whole-document scan refuses an `arms: 0.0` on any row whose status is
  not `evaluated_declared_chain`.
- P8 Determinism: two consecutive `--emit` runs produce byte-identical
  document and trace bytes (sha256 equal).
- P9 Capture (motion, task_id "G03"): ONE FFV1 `-level 3 -g 1
  -fflags +bitexact` mkv (21 frames, 1 fps, one frame per sweep tick,
  ffmpeg version first line recorded in the receipt); 6 manifest rows =
  3 profile views x diagnostic/clean; every view row's state_binding is
  kind `trace` bound to `sweep_trace.json`'s sha256; artifact_locator
  kind video seconds [0,21]; fixed_bookmark cameras with identical
  samples covering [0,20]; diagnostic rows carry EXACTLY the 3 required
  layers ("resolved tendon endpoints and paths" = tendon polylines +
  endpoint markers colored by terminal resolution; "joint axes and
  stable IDs" = wrist/elbow axis arrows with stable joint labels;
  "length and moment-arm traces" = per-tick l(q) and r(q) trace panel)
  and every drawn label is bound to a stable subject id; clean rows
  carry no layers/labels; every row's trace sha identical (view toggles
  preserve the physical state hash); `validate_manifest` returns
  structurally_valid=True with the profile read mode=ro from
  agent_slots.sqlite3 and the registry criteria sha asserted equal to
  the document's. FALSIFIERS: FB7a unbound label
  (`label_ambiguity_refused`); FB7b foreign trace sha on a view row
  (`view_toggle_state_hash_refused`).
- P10 Decode identity (G4/P4): the encoded mkv decodes to frames
  pixel-identical (max per-channel delta 0) to the committed frame-hash
  set at independently recomputable indices; pure-stdlib frame-order
  check with sensitivity guard; frames are the determinism unit;
  receipt `evidence/decode_roundtrip.json`.
- P11 Lint: `lint_report_numbers.py` exits 0 and `--selftest` still
  flags the planted defect literals; every report number traceable to a
  bound artifact at printed precision.
- P12 Receipt semantics: `qualification_receipt.json` maps every
  done_when clause to named evidence; any receipt-semantics change lands
  TOGETHER with its named check (batch_gates named_check_suite enforces).

## 9. Falsifier arms (every arm: clean control FIRST, named premature
guard `g03_fb<n>_premature`, receipt row with clean_control block; each
must BIT on its tampered fixture only)

- FB1 `input_pin_drift` — mutate one byte of a pinned upstream copy
  (refused at emit and at verify).
- FB2 `unresolved_zero_arm_refused` — construct a row whose owner is
  outside the declared chain and assign it a numeric (zero) arm.
- FB3 `nonfinite_output_refused` — plant inf/nan in an emitted value.
- FB4 `arm_trace_disagreement_refused` — plant a wrong-axis analytic
  value (also proves W5 discrimination: planted residual >= 1e5x W2).
- FB5 `frozen_set_mismatch_refused` — drop one muscle from the frozen
  set (or add a foreign one).
- FB6 `fk_closure_refused` — tamper a parsed joint axis so the default-
  pose FK deviates beyond W1 from the pinned body_frames.
- FB7 capture arms — FB7a `label_ambiguity_refused` (a drawn label
  without a bound stable subject id); FB7b
  `view_toggle_state_hash_refused` (a manifest row carrying a foreign
  trace sha). These run in the capture self-check and must refuse before
  any manifest byte is written.

## 10. House gates at freeze (G1-G9 disposition)

G1 applies (FB1-FB7 with clean controls + premature guards + receipt
rows; no arm fires on the clean fixture). G2 applies (lint + selftest;
every report number traceable at printed precision). G3 applies
(qualitative claims rendered from probe receipts with named refusal
codes). G4 applies (video decode == committed stills under identity;
pure-stdlib frame-order check + sensitivity guard; frames are the
determinism unit). G5 applies (every relative-window gate preceded by
`refuse_vacuous_comparison`; `vacuous_guard_selftest()` required by main()
before receipts; W2/W3 compared against nonzero derived windows).
G6 applies (per-document extractors keyed by document/role; no mixed
scans). G7 applies (profile loaded mode=ro; task_id SHORT "G03"; criteria
identity across dispatch/registry/prereg/checks; profile snapshot +
provenance written to evidence). G8 applies (exactly one gate-bound
capture identity: mkv disk sha256 == manifest == context == determinism
record; frame set bound by per-frame hashes + concat sha + explicit
capture_sha_definition; identical trace sha on every view row). G9
applies (prereg committed separately BEFORE implementation; contribution
within 32 files / 16 MB; commit-message metrics generated from FINAL
receipts; byte-exact carry via the card `.gitattributes` `* -text`; ONE
publication commit on the base with the `Agent:` trailer; review never
chained with merge).

## 11. Evidence anchoring (CARD_STARTER v2)

Qualification evidence references are file paths (never directories),
store-relative where possible; before any attempt-workspace artifact is
referenced by the registry it is copied into
`E:/ChimeraWork/monkey-coordination/evidence-store/MAT2-G03/` sha-verified
through `anchor.py add --card MAT2-G03` (the write-time gate). No prose in
reference fields; compound pins live in the report body.

## 12. Honest limitations (declared in advance)

- The evaluation is DECLARED-MODEL kinematics of the OpenSim chain: no
  claim that the mutant assembly resolved, no dynamics, no muscle force,
  no activation, no contact. C18 torque attribution stays
  explicitly_unresolved (no lawful force pin; A08 U1/U3).
- The capture is a 2D orthographic PIL projection of the declared chain
  (bones = segments between body origins; no mesh display, no 3D
  renderer/GPU); validate_manifest is structural only; independent pixel
  review remains mandatory and is not claimed by this text-only worker.
- l(q) is the no-wrap polyline lower envelope; the wrap model stays
  explicitly_unresolved (A09 law carried).
- The A09 mutant placement ledger is carried UNCHANGED; the declared-chain
  arms are a different, clearly-labeled evaluation frame, not an upgrade
  of any terminal resolution.
- 26 non-grasp actuators (BRD included) carry parameters without packaged
  path geometry in the grasp scope; they are not evaluated (scope law),
  named in the reconciliation, never zeroed.
- C17 stays open; zero stiffness/couple/force numbers exist anywhere in
  the deliverables.
- Pose-range finiteness does not itself prove a grip or a limb transfer
  (profile scope sentence, honored).
