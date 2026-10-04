# PREREGISTRATION (DRAFT) — VPL1-NATIVE: the VPL-1 compliant pad contact model inside the native engine (the W03 walk line's contact path)

Status: DRAFT authored by `wk-vpl1-native` for the Lieutenant's pin
(separate-first; the committed bytes are the freeze; every emitted receipt of
this card must embed `preregistration_sha256` of exactly those bytes and
refuse any mismatch). NO implementation file, engine patch, harness,
sealed package, runner job, capture frame or measurement of this card exists
at draft time. Write scope of the draft: the NEW lane dir
`E:/ChimeraWork/monkey-coordination/vpl1-native/` (NO_WORKTREES law honored:
no worktree, no clone, no per-task checkout; all CPU verification through
`python -B E:/PythonChimera/tools/monkey_campaign/task_package.py seal|run`,
slots 2/3, BUSY = retry with >= 10 s backoff, never a failed test).

This is the GRASP LINE'S FORMAL NEXT RUNG named by the stage-5 record: the
VPL-1 NATIVE COMPLIANT LAYER — "its own prereg + review + qualification
chain". This file is that prereg. It builds ONLY on published records; every
consumed record is named with its pin in section 1 and re-verified hashes
are recorded in this lane's EVIDENCE.md.

## 0. Standing laws consumed

- The objective-line law: a completed specification is not a trained skill;
  demonstrated impossibility cannot close the playable-monkey goal; no
  measured value is ever tuned to force success.
- The wording law: a predicted refusal that is observed is a SUPPORTED
  PREDICTION; each falsifier NAMES the observation that would CONTRADICT
  its prediction; a refusal is never misread as a grasp, contact, hold,
  ascent or descent result.
- The anti-tuning law EXTENDED TO SYNTHETIC PARAMETERS, standing since the
  pinned prereg: every parameter below was declared a priori, hash-pinned in
  the chain, and is NEVER adjusted after any result is seen. A post-result
  proposal to change any value is a FINDING routed to the Lieutenant, never
  an edit. THE PAD STIFFNESS k IS FROZEN FROM THE CHAIN (the exact formula
  value from AMENDMENT-1); it is never retuned here, in any arm, at any
  stage, for any outcome.
- The instrument anti-tuning law: tau = 1.0e-4 m, pi_c = 1.0e-3 m,
  r_joint = 5.0e-3 m remain frozen; no tolerance is enlarged; no pair is
  removed; no collision check is weakened. The pad admission window is a
  MODEL of a declared compliant layer, NOT a loosened tolerance: the
  bone-vs-solid checks are unchanged and remain hard failures.
- The anti-masking invariant (carried unchanged): the bone stays RIGID and
  FULLY collision-checked; the pad is the OFFSET-SURFACE LAYER ONLY. Any
  code path that lets a pad-covered vertex's contact silence a bone-level
  classification is `instrument_invalid_pad_masks_bone` and invalidates the
  run.
- The concealment law: each falsifier is an executable check inside its
  stage's sealed run and each MUST fire on its constructed trigger in the
  same run; a falsifier path that never executes or cannot bite is
  concealed falsification and fails its own stage.
- The stage-5 durable lesson, ELEVATED TO THE FIRST DESIGN REQUIREMENT OF
  THIS RUNG: A DECODABILITY GATE IS NOT A BINDING GATE (section 3).
- The hash law: hash lines are script-emitted from the target bytes or they
  do not exist; every hash-citing field names its artifact (path + role +
  its own sha256); per-posture/per-arm blocks are keyed, never update()d;
  every emit-placeholder replacement is asserted to have fired; superseded
  markers are voided explicitly; emitters end `assert stated == computed`.
- The W03I additive-engine law (the template for all engine work here):
  every patch is ANCHORED (count==1), ADDITIVE-ONLY, and PURE-RECORDING;
  added lines read existing values into new recording fields; no assignment
  to any pre-existing state; no existing expression reordered or
  re-evaluated under a changed gate; the gate is a single pure env read;
  unset env => every added line is skipped and all streams are
  byte-identical.

## 1. The chain consumed (pins in force; verified hashes in EVIDENCE.md)

| record | pin |
|---|---|
| The VPL-1 declared-synthetic pad prereg | commit `4def67e400953e8c4b833ce04345f75426a6180d`; committed bytes sha256 `9213bf7d91ed9a6e6b2c5bbddc05d5ee36db63c600dfce42b559632f6f565da9` (byte-verified by this lane from the shared object store) |
| AMENDMENT-1 (the measured Kumar 2015 stiffness upgrade) | commit `0c06e093566dcf6bfdf59665ea55a5ca68106444`; committed blob content sha256 `018f0bc120c0fa44cdcc1f611ab883764eb91e2d668975573f792218b93f94ac` (byte-verified) |
| AMENDMENT-2 (the raised-cap adjudication + receipt conventions) | commit `ccb60023568fb7c4d2cbd8d8e4855c0f5c18d372`; committed blob content sha256 `e96e09a1a925b12d68763139958eaae5897e27c027ecd3670336f5df5bc597cf` (byte-verified) |
| The decisive adjudication (PR #344, THE PAD IS THE INTERFACE) | merged at `28a110f2` (astra tip); receipt `collision_adjudication_receipt.json` sha256 `4e46523872eddaa6ffc293b3137dc2dfe79bd1eba6ed66841a2eb9b9d418777c` (cited from the published record; 354/354 GENUINE_PENETRATION, 0 CLEAR, 0 UNRESOLVED) |
| Stage-5 runtime evidence (PR #345, the sealed G04 solver ran) | merged at `0d0fcb81` (astra tip); receipt `stage5_runtime_receipt.json` sha256 `f37b2e9ea3bd2c766800e5a1d2fbaecea02eda85748c329cb22740a52dac41f3` (lane copy re-verified); runner receipt `17863a7a...` (job `5cb2081e`, PASSED, exit 0, slot 2, cleanup_verified true); 4 state-binding PNG frames `3d28831c...` / `e865c713...` / `73359e52...` / `80cf69d2...` (lane copies re-verified) |
| The coupling repair (PR #343, combine window failure-atomic) | merged at `65a23111` (master tip): `combine_core.hpp` ONLY, the failure-atomic `run_window` semantics, the additive test lane; the engine source line this rung builds on carries this repair |
| The W03I recording patch pattern | `INSTRUMENT_SIGNED_PATCH.py` sha256 `e4a8d3b51a94c0057b33b8ce4ef5f06df127a4e219b8f326f367c5402788980e` (lane copy re-verified); battery receipt of record `0a9c325776ecd1557553e409ee962a39519cba97ec29b6b9a8983d3e6c1d2c02` (re-verified; job `f2dfde7d`, slot 3); P1 ANCHOR FLOOR: ALL EXACT, BOTH ARMS |
| The sealed W03 anchor set | `dump_run_record.json` `6278f4b02089d62500b5ce48748209a476ccbdb773bc40f1a413bb9e2954bb85`; `dump_stdout.txt` `8c537cdb7cb8c43cf9423cb50056787bcc31ee487d70d3c2a1e73ed5d60b06cc`; `states_run1.jsonl` `b47b709c43a021d24bfee13bb2fe4592167cf205ee0abf9971de462319389c93`; `states_run2.jsonl` `b47b709c43a021d24bfee13bb2fe4592167cf205ee0abf9971de462319389c93`; stderr `c6f9b6c00a1d549a4bc709724d2f62f8f28b37823696de4689e1950651c37481`; the walk identity dx `0.9131056683968011`, dy `-0.7178374101385098`; 302 ticks + the refusal note (all four anchor files re-verified from the astra tip `0d0fcb81`) |
| The pinned walk-line engine input | header blob `5863348f2deef1f01e3cf761d0c4151a10035a6d`, content sha256 `f0ffea12795bd47f7c48f5ed9b8aa98869725467d94a1081b1d942f6fba129bd` (the W03I chain's engine header input; re-verified from the shared object store) |
| The sealed capture-gate template | `03a95c39...` (cited from the pinned stage-5 prereg; VISUAL-GATE-1, 7/7 planted defects, sergeant visual PASS) |
| The canonical coexistence text (582 chars) + the complete ladder label | attached verbatim in the stage-5 record erratum (PHASE 17 F1/F2); every receipt of this card carries both verbatim |

## 2. THE TARGET (what gains the pad, and what does not)

- THE ENGINE: the NATIVE engine's contact path — the W03 walk line's
  headless solver class (the `GaitWalker` machinery: the `ContactPoint`
  contact set, the kTouch/kSlip gap quantum, `project_rows` mass-metric
  active-set projection with joint stops, the `advance()` tick engine with
  substep impact/friction catch, the positional-correction band, the energy
  ledger). The implementation input is the PINNED engine header blob
  `5863348f` (content `f0ffea12...`), hash-asserted at build time; the
  package's base commit is recorded in its manifest and must carry the
  engine line WITH the #343 combine-window repair in its ancestry, or the
  exact blob pins are declared instead; any drift at build = refusal.
- NOT THE TARGET: the product runtime is EXCLUDED — readiness 0/5
  (PR #334: no body, no actuation); the product `MembraneTick` path stays
  excluded per the readiness negative. Nothing in this card touches the
  product runtime, the product scene, or any product gate.
- THE PAD: the VPL-1 compliant pad is added as a DECLARED contact model at
  the FIVE DISTAL TIPS — covered bodies `distal_thumb`, `distph2`,
  `distph3`, `distph4`, `distph5` — with EXACTLY the chain's frozen
  constants (section 4) and EXACTLY the chain's evaluation law: the pad
  consumes the UNCHANGED rigid solution (post-hoc reclassification at the
  rigid solution; the offset solve s*, the placement families and every
  bone-level class stay byte-identical to the sealed screens).
- THE HONEST TOPOLOGY, DECLARED: the sealed W03 walk scene is a 6-body
  quadruped (NB=6) whose contact points are the paw points — the five
  distal digit bodies are NOT bodies of the walk scene. The compliant class
  is therefore delivered in TWO ARMS WITH DIFFERENT SCENES, never conflated:
  - ARM-A (THE ANCHOR FLOOR, section 5): the sealed W03 walk scene, byte
    unchanged, in mode0 (gate unset) AND gated-on. The scene registers NO
    pad descriptors, so the compliant class executes ZERO pad rows; the
    floor PROVES that inertness byte-exactly.
  - ARM-B (THE PAD-ACTIVE QUALIFICATION SCENE): a declared headless
    grasp-scene harness (the sealed G04-pattern fixture press/hold/release
    schedule) in which the five distal tips exist as contact-capable
    geometry of the native body class, each carrying its frozen pad
    descriptor. ARM-B's OWN anchor set is freshly sealed at its
    qualification run and is never cited as a W03 anchor. The harness's
    scene topology is specified in the implementation package under THIS
    prereg's frozen laws; the five descriptors carry the frozen constants
    verbatim.
- THE TIER LAW (this rung's deliverable, stated before any code exists):
  - TIER N0 (THIS RUNG): the pad classes, u, the admission window, the
    measured-anchored split, and the pad force column F = p*A are COMPUTED
    INSIDE the native tick path and EMITTED into the state stream
    (recording-class channels); the rigid dynamics are UNCHANGED — the pad
    feeds nothing back into the bone solve in N0. This is the chain's own
    evaluation law executed natively, and it is the layer whose capture,
    anchors and classes this prereg qualifies.
  - TIER N1 (pad force feeding the generalized force vector): a SEPARATE
    declaration, gated on N0's sealed receipt; it CHANGES contact dynamics
    and therefore requires its own parity re-bind per the G08 law and its
    own pin. N1 is NAMED-NOT-BUILT by this prereg.

## 3. THE BINDING-GATE CAPTURE DESIGN (the FIRST requirement; the stage-5 review's law)

THE LAW BEING EXECUTED: the stage-5 capture gate verified DECODABILITY (the
strip decodes to a hash) while the DECODE-TO-HASH MATCH was performed by the
REVIEWER outside the gate. A decodability gate is not a binding gate — it
does not prove the frame was created FROM the state. THIS RUNG'S CAPTURE
GATE VALIDATES CONTENT, IN-RUN, AS THE GATE ITSELF:

- THE PER-TICK STATE HASH `H_tick`: sha256 over the declared canonical
  per-tick state serialization — the exact field list (tick index, phase,
  q, v, the rigid contact rows, the pad rows of every covered tip, the
  ledger terms) is frozen in the implementation package and byte-stable
  across arms and modes; the serializer is engine-side code whose output
  the driver re-derives independently from the state dump rows.
- THE STRIP: every retained capture frame carries a dedicated pixel strip
  (fixed layout, fixed colorspace, one bit per declared pixel-channel
  position) that encodes `H_tick` via the declared deterministic
  bit-to-pixel mapping. The encoding is LOSSLESS BY CONSTRUCTION: decoded
  pixel values equal the encoded bits exactly (PNG, lossless, declared).
- THE GATE (in-run, inside the sealed run): at every audited tick the gate
  (i) recomputes `H_tick` from the live state independently of the encoder,
  (ii) extracts the strip bytes from the RETAINED frame's decoded pixels,
  (iii) requires BYTE-EQUALITY. PASS exists only on byte-equality. THE
  DECODE COMPARISON IS THE GATE. No reviewer step carries any part of it;
  a PASS without the gate having run is structurally impossible in the
  sealed flow (the capture-gate template's own exit-code law).
- THE PROOF CLASS: byte-equality of the frame-embedded strip against the
  independently recomputed state hash is the frame-derived-from-state
  proof. A frame whose strip does not byte-match its claimed tick's
  recomputed hash is NOT BOUND to that state, whatever else it decodes to.
- THE TEETH (constructed triggers, both fired IN-RUN): T1 — the driver
  encodes a frame from a PERTURBED state (one declared field changed) and
  the gate must FAIL it against the true tick's hash;
  T2 — the driver mutates the strip bytes of a correctly encoded frame
  post-encode and the gate must FAIL it. A gate that never executes T1/T2,
  or executes them and passes either, is concealed falsification: the
  capture stage fails itself (`binding_gate_trigger_missed`).
- THE BINDING RECORD: every retained frame carries {tick, `H_tick`,
  strip-bytes sha256, gate verdict, trigger census}. Missing or
  contradicting state-revealing content fails the stage (the stage-5 law
  inherited: the runtime evidence is not capture-bound -> the run records
  the failure and routes it).

## 4. The frozen constants (carried from the chain VERBATIM; never retuned)

| id | parameter | frozen value (source) |
|---|---|---|
| G-1 | covered bodies | distal_thumb, distph2, distph3, distph4, distph5 (pinned prereg G-1) |
| G-2 | layer thickness t | 2.0e-3 m (pinned prereg G-2; UNCHANGED by AMENDMENT-1) |
| G-3 | max admitted indentation u_max | 2.0e-3 m (= t; pinned prereg G-3) |
| G-4 | admission window | rigid-proven tip fold depth d in (pi_c, t + u_max] = (1.0e-3, 4.0e-3] m (pinned prereg G-4) |
| G-5 | patch rule | pad-covered vertex set of body B = {v : n_v . a_B > 0}; n_v = area-weighted vertex normal with incident triangles sorted lexicographically before summation; a_B = normalize(u_flex x e_extent), sign per body from the A05 joint-axis table, sign-verified by control C6 before any candidate runs (pinned prereg G-5) |
| G-6 | evaluation law | post-hoc reclassification at the UNCHANGED rigid solution; the placement family, offset solve s*, and every bone-level class stay byte-identical (pinned prereg G-6) |
| F-1 | contact law | Winkler linear foundation, p = k * (u / t), valid to u_max (strain <= 1.0 by admission) (pinned prereg F-1) |
| F-2 | areal stiffness k | `k = K_eff * t / A_thumb` = **4650.718448799368 Pa**, declared as the EXACT FORMULA over the three pinned constants K_eff = 120.0 N/m (Kumar 2015 PMC4403516, mean A0 quasi-static stiffness, verified in AMENDMENT-1 section 0), t = 2.0e-3 m, A_thumb = 5.160493e-5 m^2 (AMENDMENT-1 section 1). ONE constant for all five pads (per-body k_body DECLINED, recorded in AMENDMENT-1). NO rounding; the formula value is computed, never re-typed |
| F-3 | force column | F = p * A per pad contact, A = the recorded patch area estimate; labeled DECLARED-MODEL-FORCE; consumed as load only; never an actuator, solver input, or action channel (pinned prereg F-3; in N0 it is a recording channel only) |
| X-1 | coexistence constants | tau = 1.0e-4 m, pi_c = 1.0e-3 m, r_joint = 5.0e-3 m — frozen, unchanged, and the admission window remains a MODEL, never a loosened tolerance |
| X-2 | measured/extrapolated split | MEASURED-ANCHORED band u in (0, 0.8e-3] m (the paper's 200-800 um protocol); DECLARED-EXTRAPOLATED band u in (0.8e-3, 2.0e-3] m; every pad row carries the `measured_anchored` column and every receipt splits its counts on it, never merged (AMENDMENT-1 section 2) |
| X-3 | per-pad force ceiling (declared reading) | at the window edge F = K_eff * t = 0.24 N per thumb pad; digits 0.153-0.178 N — the pad is a contact-GEOMETRY layer, NOT a support element (AMENDMENT-1 section 1.3) |
| X-4 | viscoelastic constants | t1 = 2.279+-0.233 s, t2 = 0.149+-0.022 s, two-term Prony, multilayer FE — NAMED-NOT-MODELED; VPL-1 stays QUASI-STATIC ELASTIC; the declared force columns are the SOFT/relaxed-bound reading (AMENDMENT-1 section 3) |
| X-5 | class battery | C1-C10 (C6 pad-indent, C7 over-compression refusal, C8 anti-masking, C9 pad-free, C10 measured-stiffness identity at 200/400/600/800 um -> F = K_eff * u = 0.024/0.048/0.072/0.096 N) run natively in ARM-B; the light gate is C1-C10; any miss -> `INSTRUMENT_INVALID_IN_SITU` (pinned prereg section 2 + AMENDMENT-1 section 4) |

## 5. THE ANCHOR FLOOR (the W03I pattern: mode0 default-off + the gated-on arm)

- THE PATTERN (from `e4a8d3b5...`, P1 ALL EXACT BOTH ARMS): the engine
  patch is additive, anchored (count==1) and pure-recording; the compliant
  class is registered per-scene and gated by ONE pure env read
  (`GAITPHYS_VPL1`; unset => default-off => every added line skipped). The
  gate name is NEW and distinct; no other lane's gate semantics are reused
  or redefined. Telemetry goes to FILES only; no new stdout/stderr byte
  exists in any mode.
- THE FLOOR: in the sealed W03 walk scene, BOTH ARMS reproduce the sealed
  W03 anchor set BIT-EXACTLY — the four anchor files (`6278f4b0...`,
  `8c537cdb...`, `b47b709c...` x2) AND stderr (`c6f9b6c0...`) AND the walk
  identity (dx `0.9131056683968011`, dy `-0.7178374101385098`; 302 ticks +
  the refusal note):
  - mode0 (all VPL envs unset): byte-identical to the sealed records.
  - gated-on: byte-identical to the sealed records — the declared basis is
    that the walk scene registers NO pad descriptors (the five distal tips
    are not walk-scene bodies), so the compliant class executes ZERO pad
    rows; the floor PROVES the gated code is byte-inert where it must be
    inert. This is STRONGER than the W03I floor: W03I gated only recording
    lines; here the gated-on arm gates NEW CONTACT-CLASS CODE, so the
    byte-exact floor proves the gate adds nothing to an unregistered
    scene, in either arm.
- TEETH: ANY anchor byte drift in EITHER arm = the layer is not inert where
  declared inert = `anchor_floor_drift`, the run is invalid, nothing
  carries (recorded, routed, never waived).
- ARM-B's anchors: freshly sealed at ARM-B's qualification run; named the
  ARM-B anchor set; NEVER cited as W03 anchors and never merged with them.

## 6. THE HONEST SCOPE (the not-claims at maximum)

- THE COMPLIANT LAYER'S SCOPE: the compliant layer at the native solver =
  THE HEADLESS W03 BODY CLASS (ARM-A's engine + ARM-B's declared headless
  grasp harness). The product runtime stays EXCLUDED (readiness 0/5,
  PR #334; `MembraneTick` excluded per the readiness negative). No claim
  about any product build, any rendered creature, or any playable behavior
  is made or derivable from this card.
- NO GRASP-COMPLETION CLAIM unless the evidence reaches it: TC-8 = 0/8 and
  x_press ABSENT stand UNCHANGED; the same-hands debt stands (0.049 kg hand
  vs the 10.038 kg line); the 60 N/channel press is a DECLARED fixture,
  never an actuator qualification; friction PLACEHOLDER (mu_s = 0.6 /
  mu_k = 0.4); the mass lineage UNRESOLVED (gap 9, per-reading); the C17
  non-identity stands (the pad is NOT an attachment port and implies no
  lambda_min); K01 master conditionality stands (training gated on the
  whole grasp chain). A pad contact row is a DECLARED-MODEL contact
  classification; it is never a grasp, hold, or support result.
- WALKING CERTIFICATION IS NOT INHERITED (the G08 law): ARM-B changes no
  walk-scene dynamics (proven by the floor), but any future dynamics-touch
  (N1) re-binds its own parity and identity gates; nothing here qualifies
  locomotion.
- THE COMPLETE LADDER LABEL (carried verbatim in every receipt; the stage-5
  erratum F2 form): pad-geometry + capacity + law-form + collision-
  adjudication (strict-fail named) stages complete; RUNTIME EVIDENCE at the
  declared rigid-contact scope = the stage-5 receipt; the exact-candidate
  collision adjudication at the PAD-INTERFACE scope remains the named-unmet
  collision rung; the VPL-1 native compliant layer remains the NAMED-UNMET
  RUNG (its own prereg + review + qualification chain) — THIS CARD IS THAT
  CHAIN; the goal stays open.
- THE COEXISTENCE NOTE (carried verbatim in every receipt; the stage-5
  erratum F1 canonical 582-char text): the strict represented-BONE
  adjudication reads the bone against the UNOFFSET trunk surface; the VPL-1
  offset-surface reading COEXISTS as a DIFFERENT quantity, never conflated;
  no claim that pad contact was physically resolved is made or derivable
  (in N0 this is exact by construction: the pad resolves nothing — it
  classifies).

## 7. THE CLOSED OUTCOME SPACE (counts must close; no unnamed state)

Per audited tick, per covered tip, EXACTLY ONE of:
- `PAD_CONTACT(u)` — d in (pi_c, 4.0e-3] m AND the deepest vertex lies in
  the declared pad patch; u = d - t in (0, 2.0e-3] m recorded with its
  `measured_anchored` flag and the patch witness.
- `PAD_REFUSED_DEPTH` — d > 4.0e-3 m (stays refused; the deep classes
  never convert).
- `PAD_REFUSED_PATCH` — d in the window but the deepest vertex lies
  outside the declared patch.
- `NO_PAD_ROW` — no window event for this tip this tick.
Per phase/schedule: {COMPLETED, REFUSED} — exactly one. Capture:
{GATE_PASS, GATE_FAIL} — exactly one. Anchors: {ANCHOR_EXACT,
ANCHOR_DRIFT} — exactly one per arm. Binding triggers: {FIRED_BOTH,
TRIGGER_MISSED} — exactly one. COVERAGE ARITHMETIC: the four pad classes
partition all covered-tip ticks; any unnamed state or double-scored row =
`vpl1_native_outcome_space_broken` (refusal).

## 8. THE QUANTITY CODE-PATH TABLE (every emitted number names its producer)

| quantity | producer code path | tier/label |
|---|---|---|
| pad class + u + `measured_anchored` + patch witness | the native compliant class inside the engine tick path, from the UNCHANGED rigid solution | N0, DECLARED-MODEL |
| pad force column F = p*A | the native compliant class, recording channel | N0 recording; DECLARED-MODEL-FORCE; never a solver input |
| bone-level classes, trunk clearance, self-collision, the exclusions ledger | the UNCHANGED rigid machinery / the sealed instrument law forms — cited from the sealed receipts, byte-identical with the pad gate ON or OFF | rigid, unchanged |
| per-tick state hash `H_tick` | the declared canonical engine-side serializer | N0, byte-stable |
| capture binding | the in-run gate (strip extract + byte-equality vs the recomputed `H_tick`) | capture stage |
| W03 anchors + walk identity | the sealed W03 dump path, unchanged | ARM-A floor |
| ARM-B anchors | ARM-B's own sealed dump at its qualification run | ARM-B |
| parity / identity gates | re-bound per the G08 law at any dynamics-affecting tier (N1 only; N0 inherits the W03 floor instead) | N1 (named-not-built) |
| actuator capacity, law-form grids | NOT PRODUCED HERE — the capacity/law-form stages' receipts are cited, never re-run | cited |

NO quantity is cited from an analytic stage as if natively produced, and no
natively produced number is cited as a sealed-chain result.

## 9. THE FROZEN PREDICTIONS (each names its contradicting observation)

- N-P1 ANCHOR FLOOR: both arms (mode0, gated-on) reproduce the sealed W03
  anchor set bit-exactly (section 5). CONTRADICTION: any byte drift in
  either arm — `anchor_floor_drift`, the run invalid, nothing carries.
- N-P2 BINDING GATE: every retained frame's strip byte-matches the
  recomputed per-tick state hash IN-RUN, and both tamper triggers (T1
  perturbed-state encode, T2 post-encode strip mutation) are constructed
  and FAIL the gate in the same run. CONTRADICTION: any strip/hash mismatch
  on an untampered frame; any tampered frame PASSING; either trigger
  missing or firing the wrong way — `binding_gate_failure` or
  `binding_gate_trigger_missed` (the stage fails itself).
- N-P3 WINDOW CONVERSION, NATIVE: in ARM-B, every admitted contact row of a
  covered tip with d in (1.0e-3, 4.0e-3] m whose deepest vertex lies in the
  declared patch reclassifies to `PAD_CONTACT` with u = d - t in
  (0, 2.0e-3] m; every d > 4.0e-3 m row stays `PAD_REFUSED_DEPTH`; the
  native C10 analog reproduces F = K_eff * u EXACTLY at the four measured
  depths (0.024 / 0.048 / 0.072 / 0.096 N; equivalently F(u)/u = 120.0 N/m),
  validating the CONVERSION MAPPING in-band in the NATIVE code path (it
  does NOT validate the paper's FE model class — X-4). CONTRADICTION: any
  `PAD_CONTACT` with u > u_max; any conversion of a d > 4.0e-3 m row; any
  conversion lacking a patch witness; any C10 miss — instrument or
  patch-rule defect, the run invalid.
- N-P4 ANTI-MASKING: the C8-class trigger (pad engaged AND a
  non-covered-body bone vertex inside the solid) classifies
  `GENUINE_PENETRATION` in the native path; the bone-level classes are
  byte-identical with the pad gate ON and OFF. CONTRADICTION: any other
  class = `instrument_invalid_pad_masks_bone`; any bone-level class change
  under the gate toggle = masking; the run invalid, nothing carries.
- N-P5 DETERMINISM: ARM-A's streams are byte-identical across independent
  re-runs (the W03I P8 law extended to the new gate), and ARM-B's streams
  are byte-identical across its independent re-runs. CONTRADICTION: any
  stream divergence in either arm.
- N-P6 THE MEASURED/EXTRAPOLATED SPLIT: ARM-B's conversion counts split on
  the `measured_anchored` column, and the declared expectation is that BOTH
  bands are populated at the declared operating point (the in-band basis:
  646 measured-anchored / 308 extrapolated of the 954 q_c rows at the
  sealed screens). CONTRADICTION: a band silently EMPTY (every conversion
  in one band) — recorded as a routed FINDING on the operating point, never
  repaired by moving any constant.

A falsified prediction is a RESULT — recorded in the receipt and routed to
the Lieutenant; it refuses nothing retroactively and retunes nothing.

## 10. THE QUALIFICATION ORDER (no stage starts before its predecessor's sealed receipt exists)

1. PIN: the Lieutenant commits THIS file alone (separate-first; the
   committed bytes are the freeze) — required BEFORE any gated experiment
   (the publication law: prereg commits precede packages; a seal is not a
   substitute).
2. THE ENGINE PATCH PACKAGE: the additive anchored gated patch on the
   pinned engine bytes (blob `5863348f` / content `f0ffea12...`
   hash-asserted at build; the base commit recorded; #343 in ancestry or
   the exact blob pins declared); build logs retained from the FIRST
   failure onward (the W03I lesson); the seal bytes captured into this
   lane's `seal-store/` at creation.
3. THE ANCHOR FLOOR RUN (ARM-A): mode0 + gated-on against the sealed W03
   anchor set; N-P1 decided in-run.
4. THE BINDING-GATE BATTERY: T1/T2 constructed and fired; N-P2 decided
   in-run; the binding record emitted for every retained frame.
5. THE PAD-ACTIVE QUALIFICATION RUN (ARM-B): the declared grasp harness,
   the C1-C10 battery, N-P3/N-P4/N-P6 decided in-run; the ARM-B anchor set
   sealed; determinism re-runs (N-P5).
6. THE RECEIPT + REVIEW: script-emitted hashes; keyed per-arm blocks;
   delta note (`run class vpl1_native_tier_n0`; the delta vs the chain:
   NEW native compliant class + binding gate, NO frozen constant moved);
   the canonical coexistence text + the complete ladder label verbatim;
   Sergeant review through the Lieutenant; author self-review certifies
   nothing.

## 11. GOVERNANCE

Authored by `wk-vpl1-native`; DRAFT for the Lieutenant's pin
(separate-first). The implementation package pins THIS document's committed
sha and refuses on drift; the package seals against the pin commit; all CPU
execution through the canonical runner (slots 2/3; BUSY = retry >= 10 s;
`--keep`-declared outputs only; required missing outputs fail the job);
every load-bearing artifact's sha256 lands in this lane's EVIDENCE.md;
required evidence is anchored through the existing anchor.py before any
registry reference. NO merge/review authority is claimed; NO Git mutation in
any shared checkout is made by this lane; Sergeant review is requested
through the Lieutenant. Anti-tuning: every constant above is frozen from the
chain pre-run; k is NEVER retuned; any post-result change request is a
FINDING routed to the Lieutenant, never an edit.
