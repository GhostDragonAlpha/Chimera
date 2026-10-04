# PREREG DRAFT — wk-press-derivation (PRESS-CHANNEL ACTUATOR DERIVATION: the forward + inverse computation on frozen sealed inputs)

Lane: `E:/ChimeraWork/monkey-coordination/press-derivation/`. Date: 2026-10-02.
Worker: wk-press-derivation. Status: **CHAIN STOP 1 — DRAFT FOR THE
LIEUTENANT'S PIN. NO RUNS EXECUTED. NO PACKAGE SEALED. NO CODE WRITTEN.**
This draft precedes any implementation. Every load-bearing input is named and
sha256-pinned below; every number quoted is copied from hash-verified sealed
bytes. Acceptance = sealed receipts, never prose.

## 0. Authority chain and scope fences

- THE DISPATCH (Lieutenant judgment per the session's parallel doctrine):
  `LIEUTENANT_RESUME_v2.json` entry "THE PRESS-ACTUATOR DERIVATION LANE
  DISPATCHED (agent_6cecdfe1)" — the engineering path: the forward + inverse
  computations from the FROZEN certified caps + the A05 chain + the J maps +
  the N1 pad geometry; the three honest outcomes declared BEFORE the work; the
  anti-tuning law; the TC-8 map. The Captain's formal answer may still
  redirect; the DECLARED-FIXTURE OPTION stays recorded as the parallel
  alternative (campaign law: a fixture NEVER completes the objective).
  The press channel is the grasp line's ONE REMAINING STRUCTURAL GAP as
  recorded at the N1 publication (PR #351 merged at 1848be4a).
- LANE CLASS (the actuator-map precedent, unchanged): deterministic closed-form
  derivation on hash-pinned sealed inputs, executed ONLY through the pinned
  file-package runner (`python -B
  E:/PythonChimera/tools/monkey_campaign/task_package.py seal|run`). This is
  preparation/derivation work, NOT a gated measurement; the preregistration
  law is satisfied by declaring this draft at chain stop 1 and pinning every
  input hash BEFORE any code exists. NO_WORKTREES honored in full: no
  worktree, no clone, no Git mutation; the draft lives in the lane directory
  only. If the Lieutenant classifies the Chain Stop 2 execution as a gated
  measurement, the prereg must first go through the serialized publication
  path and the package pins to the published prereg commit (a seal is never a
  substitute for a required commit).
- WRITE SCOPE: this lane directory plus the package contribution directory
  only. Other lanes are read-only. Other agents' ownership preserved.
- RUNNER DISCIPLINE (Chain Stop 2): assigned slots only; BUSY (exit 75) =
  retry with >= 10 s backoff, never a second directory; every declared output
  via `--keep`; only an actual receipt stating PASSED with
  `cleanup_verified: true` counts as a run, and even then it qualifies nothing
  physical by itself.

## 1. THE PHYSICS QUESTION (verbatim from the dispatch)

Can the CERTIFIED drive torques — hind hip 11.2125 / knee 6.6375 / ankle 7.4 /
MP 0.8875 N*m; fore shoulder 4.229 / elbow 3.76 N*m (the W03 scene bytes) —
lawfully produce the ~55-60 N grip press per pad set through the represented
anatomy?

SHORTHAND CORRECTION (recorded now, before any result): the sealed bytes
record the per-contact pincer CAPACITY as 38.254690383428-41.337217959487 N
at the four GP1 candidate postures and 31.546445053409755-38.027181977020 N
at the recorded q=0 configuration. The 54.68840727038889 N figure is the
REQUIRED press (P_req, std-g, n=3), not a capacity. The dispatch shorthand
"per-contact 38-54 N capacities" is recorded as dispatch context only; this
lane computes from the sealed numbers, never from the shorthand.

## 2. Pinned inputs (recomputed and verified by this lane at draft time)

| input | sha256 |
|---|---|
| W03 sealed scene (certified drive caps; outer file; schema chimera.earth_scene.v1; embedded scene_sha256 e61ad3864472453f2b2a77a71ca0579f1b78e905b2495f581a9f87f27502333c) `acceptance-chain/scenarios/common/gitrepo/tools/monkey_campaign/contributions/MAT2-W03/scene_out/scene.json` | `f6844eeae3dc87170a572ccdeedf326a6cac4f73d1448941808bd8b25a8db342` |
| A05 certified kinematics `evidence-store/MAT2-A05/workspace_evidence/48b037593f63_mutation_structure.json` | `48b037593f63ec473947d787077ab6fbcd3b364afd15765bff508e7d54f45649` |
| A05 hand mutation XML `evidence-store/MAT2-A05/workspace_evidence/9c91124600ab_macaque_hand_mutation.xml` | `9c91124600abc67a4a33d78ce79ab1a0604a48b5a9a2e6377d15de05717e5adf` |
| A09 grasp package `evidence-store/MAT2-A09/numerical/grasp_package.json` | `0a70adb1029d860ac9504683d77c2e94be2634724c63479f827fcbc8fcd97d24` |
| GP1 posture receipt `gp1-impl/final_run/gp1_experiment_receipt.json` | `e68e608936cacf9384f5701ba84df804e250683feb21b542f6c866f50f8808c5` |
| GP1 gate receipt `gp1-impl/final_run/gp1_gate_receipt.json` | `4d495a19db038353faa05cac289b475c88d4c5f3de7d51339cd4df65736b1647` |
| Actuator-map light prereg (precedent class) `actuator-map/PREREG_LIGHT_ACTUATOR_MAP.md` | `4e0472aff62ff7c8c6f148817e20505ba4bebca559c04aa22a801da260360c98` |
| Actuator-map lane EVIDENCE (revision 2 of record) `actuator-map/EVIDENCE.md` | `b56f181923fc85621ae112b536ea8b4bfc66926e993920b4e0abd24682eab189` |
| Actuator-map sealed receipt `actuator-map/final_run/actuator_map_receipt.json` | `013f3157c3455dc66c736fee465f8ac2341bc72ebbb8ca6bafdb7f545c2e9175` |
| Actuator-map jacobian map (SEALED J MAPS) `actuator-map/final_run/jacobian_map.json` | `96a4610ffb37e6729763cb13455b7d6b6b3d582a3ab35dc4975a3b67f64f31b3` |
| Actuator-map report `actuator-map/final_run/actuator_map_report.txt` | `036d3af275c4c4234b879fe80bde29048d91f75e3a399f8b266f35dc572fefe2` |
| Force-defs addendum (comparison semantics of record) `actuator-map/final_run_force_defs/force_defs_addendum.md` | `52fc5fed51cc1fe342806e9b934671cd4f61452d0c4b2bf353fd6c62fd8e669a` |
| Force-defs sealed receipt `actuator-map/final_run_force_defs/force_defs_receipt.json` | `f43a4444a267ef0c6abb06d821095578efb24f34a2b8c0b023280694b05e7fb6` |
| K01 skill spec (ACTION SPACE LAW) `k-spec/PREREGISTRATION_K01_SKILL_SPEC.md` | `fdc2e79aea9479fd4d6f9d761694ba1edbe6430b1bf1ee9df6fed64ca9ac0935` |
| K02 reset scenarios (MP cap row B9) `k-spec/PREREGISTRATION_K02_RESET_SCENARIOS.md` | `d23117a3810c3fccf9623194cfdadba4c33b2289a5cbf8d833e4d82960a18ab3` |
| Runtime contract (TC-8; certified caps table) `b07-prereqs/RUNTIME_CONTRACT.md` | `f33c188bcb561b1946b104340cf36cba366709526c095874684529a599df338c` |
| B05 port qualification ledger `b07-prereqs/PORT_QUALIFICATION.md` | `4818d4b03576f2821f75f49b2d54f8c01378763b1ad1441075dda267c9ff3f00` |
| N1 feed prereg (frozen pad law) `vpl1-native/PREREGISTRATION_N1_FEED.md` | `58fd70493fb05c964b025a2ff30da17af8fb6b231d455ce652a2f7dd1f6c3a5d` |
| N1 corrected run receipt `vpl1-native/final_run_n1_corrected/n1_receipt.json` | `7a97ceacfbb90c7cc7b4daad4cfaf41f334ad9dc6cdedacff68c45681a577b0f` |
| G04 friction sources (bench attribution) `g04-friction/FRICTION_SOURCES.md` | `336118e929bd0b4fb067db5a448dc2e348fed073007787635549a4cf1cf5868b` |
| Climb derivation (P_req sealed forms) `climb-derivation/DERIVATION.md` | `da34420558f6632b0544ca94bc3e25ece515027628c7bd8cc54b9fdd30b7ebd9` |
| Climb derivation output `climb-derivation/derivation_output.txt` | `534ac1f3dfe98bbfb14636704132ca192ca92f47e23cf1f065f9bd5032e2d73f` |
| Climb phase contracts `climb-spec/PHASE_CONTRACTS.md` | `7212f99d54bd8ee1d059d201ecfac3e4928a9069657b68553b3cec939b561963` |
| Dispatch record `LIEUTENANT_RESUME_v2.json` | `d616f422dd6e8502234226053adba17ffd5386ac034554a8102f5070b180600e` |
| Completion map `E:/PythonChimera/tools/monkey_campaign/MONKEY_COMPLETION_MAP.md` | `0e3984578b0cae38ab435daaa77cc10559cceeadbaf9885c3f31b979a362ecae` |

Cross-checks already performed at draft time: the K01 spec section 2.2 pins
(actuator-map receipt 013f3157.../jacobian 96a4610f.../EVIDENCE b56f1819.../
RUNTIME_CONTRACT f33c188b...) all match this lane's independent recomputation;
the N1 prereg blob 58fd7049... matches the resume's "byte-verified" pin;
CORRECTION-1 (bb9273033c8e4af0ec33deacc20e89d5924af589a8865e84ea97a08b70f70b05)
matches the N1 prereg's citation; MONKEY_COMPLETION_MAP.md is byte-identical to
the actuator-map input pin (no drift). At run time (Chain Stop 2) every pin is
re-verified; any drift = refusal `input_pin_mismatch`.

## 3. The certified frozen inputs (what they are; what they are NOT)

3.1 CERTIFIED DRIVE CAPS (W03 scene bytes, consumed FROZEN): hind
hip 11.2125 / knee 6.6375 / ankle 7.4 N*m; fore shoulder 4.229 / elbow 3.76
N*m; MP 0.8875 N*m (the name-matched `mp_flexion` cap; RUNTIME_CONTRACT
lines 111/221/322; K02 B9; GP1 B-G7). STRUCTURAL FACT recorded by the
actuator-map lane and re-verified here: these attach to W03 gait-scene
coordinates; NONE is a coordinate of the certified hand chain (A05, anchored
at `macaque_hand_anchor`; the wrist joints `mutation_wrist_flexion`/
`mutation_wrist_abduction` carry NO certified drive; the forelimb
shoulder/elbow chain above the wrist is ABSENT from the certified hand
model). They enter this derivation only as (i) the MP cap under the declared
comparison law, and (ii) the subject of the coupling question (section 4.3).
They are NEVER substituted as human-norm or off-chain torque values (C07).

3.2 THE CERTIFIED HAND CHAIN (A05, FROZEN): 20 bodies, 22 declared joints;
per tip the loaded chain is exactly 6 joints (2 wrist + 4 chain joints); the
digit metacarpals `secondmc`..`fifthmc` declare NO joints; the thumb chain
`firstmc` declares `cmc_abduction` + `cmc_flexion`; terminal exact-zero arms
(`ip_flexion`, `md{k}_flexion`) recorded per posture; 18 joints per tip are
off-chain `structural_zero`.

3.3 THE SEALED J MAPS (actuator-map revision 2 OF RECORD, consumed as sealed
bytes, never recomputed from scratch): `tau_j(q, f) = sum_i ((p_i - o_j) x
F_i) . u_j = (J(q)^T f)_j` (the GP1 CC5 law), per-posture columns
`J_col_j(t) = (p_t(q) - o_j(q)) x u_j(q)`; the four GP1 candidate postures q*
(PRIMARY thumb+digit3, F1 thumb+digit4, F2 thumb+digit5, F3 thumb+digit2 —
all CLOSED_SELF_COLLISION in the GP1 instrument, consumed as POSTURES ONLY)
plus the 22x9 coordinate-wise grid; the recorded A09 q=0 rows (tips matching
the A09 recorded endpoints to 1.3877787807814457e-17 m).

3.4 THE N1 PAD CONTACT GEOMETRY (frozen constants; the k formula is IN CODE
AS THE FORMULA and never retuned): unilateral Winkler law
`p = max(0, k*u/t)`, `F = p*A`, `k = 120.0 * 2.0e-3 / 5.160493e-5 =
4650.718448799368 Pa`; window constants pi_c = 1.0e-3 m, layer t = 2.0e-3 m,
u_max = 2.0e-3 m, refusal at d > 4.0e-3 m; `PAD_CONTACT` is the ONLY
force-carrying class; u <= 0 transmits ZERO force by the law itself. The N1
receipt records `pad_work = -1.2789773453750976e-03` J (the #351 honest
figure); its spring-work cross-check is a named open residual (FIRED_FAILED;
ZOH discretization + domain boundary) — cited as exactly that, never as a
pass. The pad law enters as the declared force-transmission interface at a
pad; the press force in this lane is the STATIC channel input, not a pad
compression solve (dynamics ABSENT, statics only).

3.5 THE PRESS REQUIREMENT (DECLARED arithmetic, never measured, FROZEN):
P_req(std-g, n=3) = 54.68840727038889 N per channel;
P_req(rec-g, n=3) = 54.70708910000001 N (climb-derivation sealed forms,
bit-exact recomputes at their runs); declared operating point 60.0 N per
channel (jn = 0.3 N*s/tick/channel, jn/DT = 60.0 N; F03 S1 -> G04 -> K01);
across-pad magnitude sum n x per-channel (n=3 -> 180 N; net vector force
constructions recorded separately). CORRECTED FRICTION ATTRIBUTION (frozen):
mu = 0.6 is an UNMATCHED PLACEHOLDER bench value (G04 FRICTION_SOURCES P3;
measured rhesus palm friction NOT located; NB-01/02 measured friction
ABSENT); every threshold consuming mu (P_req, mu_crit = 0.5468840727038888
scene n=3 std-g) is CONDITIONAL ON THE BENCH. This lane never re-derives,
adjusts, or defends mu; it consumes the declared requirement as declared.

3.6 THE RECORDED FRONTIER (the prior of record; re-derived at run, never
imported silently): with the declared cap law (3.7), the antipodal pincer
capacity per contact at the four GP1 candidate postures:
PRIMARY (thumb+digit3, chord 0.073999999885 m) F* = 41.162837671790484 N
binding `cmc_abduction`; F1 (thumb+digit4, chord 0.073999999236 m) F* =
38.254690383428375 N binding `cmc_abduction`; F2 (thumb+digit5, chord
0.073999999544 m) F* = 41.3372179594866 N binding `mcp5_flexion`; F3
(thumb+digit2, chord 0.073999999605 m) F* = 40.10156993237948 N binding
`cmc_flexion`. F*_mp (name-matched joint never binding): 70.944655072 /
88.541300434 / 92.240640869 / 91.675660892 N. At the recorded q=0
configuration: 32.08515614710456 (cmc_flexion), 34.31435637640251
(cmc_flexion), 38.027181977019985 (cmc_abduction), 31.546445053409755
(cmc_abduction) N across the four pairs. The declared 60 N per-channel press
exceeds the frontier at EVERY sealed posture under BOTH consistent readings
(per-contact ratios 1.4514764892694096-1.9019575707632639x; total ratios
2.1772147339041146-2.852936356144896x): x_press DEBT findings, RECORDED,
never decisive. tau@60 N at the binding joints: 1.2936425915187337 (PRIMARY),
1.391986171271366 (F1), -1.288185384226601 (F2), 1.327878187557041 (F3) N*m.

3.7 THE DECLARED CAP LAW (B-G7, unchanged): the single certified hand-chain
cap `0.8875 N*m` applied to EVERY loaded-chain joint is a DECLARED COMPARISON
LAW, not a per-joint cap set. NO certified per-joint torque cap exists for
any other hand joint: named gap. Per-joint caps for the wrist joints: NONE
(named gap). The lane records, per posture and configuration, BOTH the
declared-law frontier and the per-joint row that names which cap would be
needed — the shortfall arithmetic never hides behind the aggregate.

## 4. THE DERIVATION FRAME (two falsifiable computations + one declared
decomposition, fixed BEFORE any run)

4.1 FORWARD (capacity at each declared pad configuration). INPUTS: the frozen
cap set (3.7), the sealed J maps (3.3), the declared posture set P and
configuration set C (below). COMPUTATION: per posture q and configuration c,
per-unit-force coefficients `a_j(q, c) = sum over loaded pads i of J_col_j(t_i) .
n_i` (forces ON the hand, GP1 sign convention); the achievable per-pad press
`F*(q, c) = 0.8875 / max_j |a_j(q, c)|` with the binding joint named; the full
linear torque schedule `tau_j(F; q, c) = F * a_j(q, c)` for the declared
magnitude ladder [1, 5, 10, 20, 30, 40, 50, 54.68840727038889, 60.0] N.
DECLARED POSTURE SET P (closed; additions only by prereg amendment): the four
GP1 candidate postures + the recorded A09 q=0 configuration. DECLARED
CONFIGURATION SET C (closed; constructible from the sealed map bytes with NO
new inputs): (C1) the four antipodal pincer pairs at the candidate postures
(declared chord normals; the reduction configuration);
(C2) the four antipodal pincer pairs at the recorded q=0 configuration;
(C3) the single-tip declared axis-normal rows (+-x, +-y, +-z anchor frame) at
every sealed posture — the N1 pad normal at a tip is only defined by a
declared construction, and the ONLY declared constructions in the sealed
corpus are these; a fixture n=3 pad set has NO anatomical counterpart in the
sealed corpus (force-defs erratum 3), so n=3 enters on the REQUIREMENT side
only, never as an anatomical capacity configuration.
FALSIFIERS (hard in-run refusals, not prose): recomputing C1 from the sealed
jacobian bytes must reproduce 3.6's recorded F* values exactly (any deviation
= `frontier_reduction_failed`); the ladder must satisfy `tau_j(F) = F*a_j`
exactly for every j, F, q, c (linearity identity, `linearity_identity_failed`);
every number carries a posture-conditional CONDITIONAL-CALCULATION label
(`unlabeled_number_failed`).

4.2 INVERSE (torque requirement at the declared requirement). INPUTS: F_req in
{54.68840727038889 (P_req std-g), 54.70708910000001 (P_req rec-g), 60.0
(declared operating point)} N per pad; the same P and C. COMPUTATION: per
posture, configuration and F_req, `tau_req_j = sum over loaded pads i of
F_req * (J_col_j(t_i) . n_i)`; the EXACT SHORTFALL ARITHMETIC per joint:
`gap_j = |tau_req_j| - 0.8875` (declared cap; sign recorded), the ratio
`F_req / F*(q, c)`, the binding joint named, and the count of debt joints
(`|tau_req_j| > 0.8875`) with each named. The anchor wrench — the net force
and torque the loaded hand chain transmits to `macaque_hand_anchor` at F_req
— is computed and RECORDED as an UNQUALIFIED INTERFACE row (no certified cap
exists at the anchor; see 4.3). FALSIFIERS: the inverse rows must reconcile
with 3.6's recorded debt arithmetic at C1/C2 (60 N rows; deviation =
`debt_reconciliation_failed`); the anchor wrench must equal the closed-chain
sum of the applied pad forces and their joint-frame moments (in-run identity,
`anchor_wrench_identity_failed`).

4.3 THE COUPLING DECOMPOSITION (declared now so no outcome can be reshaped
post hoc). The certified scene drives (3.1) share NO joint with the certified
hand chain: the W03 gait chain and the A05 hand chain are disjoint sealed
models joined by NO declared wrist/forelimb coupling in the corpus. The
physics question therefore decomposes exactly into two sub-questions:
(Q-HAND) can the hand-chain joints, under the declared cap law, carry the
pad-press torques at the declared postures/configurations — DECIDABLE by 4.1
+ 4.2 from the sealed bytes;
(Q-ANCHOR) can the certified forelimb drives (shoulder 4.229 / elbow 3.76)
and/or the eight B05 tendon ports produce the required anchor wrench —
STRUCTURALLY UNDECIDABLE ON CURRENT INPUTS: the forelimb chain is ABSENT
from the certified hand model, the wrist carries NO certified drive, the
tendon ports are 0/8 qualified with blocked_as_measured inputs, and no
declared coupling constant exists in the sealed corpus. Inventing a coupling,
a wrist cap, or a transmission ratio would be manufacturing an input —
prohibited. Q-ANCHOR is DECLARED UNDECIDABLE from the start; the lane's
outcome (section 5) is reported PER SUB-QUESTION, and the lane may not
present Q-HAND's answer as an answer to the undecomposed question.

## 5. THE HONEST OUTCOMES (declared before the work; each advances lawfully)

(a) CAPS SUFFICIENT (Q-HAND): if F*(q, c) >= F_req at every declared posture
and configuration, the deliverable is the DERIVED PRESS ACTUATOR LAW
`tau_j(F; q, c) = F * a_j(q, c)` (a CONDITIONAL-CALCULATION: posture- and
configuration-conditional, statics only) PLUS THE NAMED QUALIFICATION PATH:
runtime qualification through the file-package runner under the action space
law (no pose-writing, no teleport, no force outside the capped channels; the
press decomposes into CAPPED SERVO INTENTS per the K05 composition law) and
x_press port admission through TC-8's measured inputs (section 7). The law
itself qualifies NOTHING (section 6 anti-claims).

(b) CAPS INSUFFICIENT (Q-HAND): the gap named with the exact shortfall
arithmetic of 4.2 — per posture, per configuration: gap_j per debt joint,
F_req/F* ratios (the recorded prior: 1.4514764892694096-1.9019575707632639x
per-contact at C1), binding joints named. THE STRONGEST NEGATIVE, stated
plainly: under the declared cap law the grasp line honestly closes at
actuator-capacity — the same class as the collision closure. This is a
lawful recorded negative; it is never silent, never a card failure, and
never decisive for lines outside the declared cap law.

(c) UNDECIDABLE (Q-HAND only; Q-ANCHOR is already declared (c) by
decomposition): a named input gap blocks the computation — e.g. an absent
posture/pad-geometry identity, a missing joint property, or a required
declared construction that does not exist in the sealed corpus. The lane
reports (c) with the EXACT missing input named; it does not approximate,
substitute, or tune to force (a) or (b).

Mixed outcome is the expected shape: Q-HAND resolves to (a) or (b) or (c)
from the sealed bytes; Q-ANCHOR stands (c); the lane reports both rows and
the Lieutenant owns the synthesis.

## 6. THE ANTI-TUNING AND NOT-CLAIMS LAWS

- FROZEN, NEVER ADJUSTED: the certified caps (W03 bytes f6844eea...;
  RUNTIME_CONTRACT 0.8875); the anatomy (A05 48b03759.../9c911246...); the J
  maps (sealed revision-2 bytes 96a4610f.../013f3157...); the N1 pad
  constants (k formula, pi_c, t, u_max, 4.0e-3); the requirement constants
  (54.68840727038889 / 54.70708910000001 / 60.0 N; jn = 0.3 N*s/tick/channel);
  the friction bench mu = 0.6 (placeholder, conditional-on-bench, never
  adjusted and never used to rescue an outcome). A post-result change request
  is a FINDING routed to the Lieutenant, never an edit.
- P and C are closed IN THIS DRAFT. Adding postures/configurations after any
  result is seen = a prereg amendment (routed to the Lieutenant), never a
  silent extension.
- A SUCCESSFUL DERIVATION IS A DERIVED ACTUATOR LAW — the conditional-
  calculation class. It is NEVER an actuator qualification: qualification
  requires runtime evidence (sealed runner receipts + independent Sergeant
  review). Named follow-on if (a): the runtime press-channel qualification
  card, gated on TC-8's measured admission.
- NOT-CLAIMS (exhaustive): no candidate-certified claim (the four GP1
  postures are CLOSED_SELF_COLLISION candidates consumed as postures only;
  the corrected instrument lane owns reachability); no collision or
  reachability computation in this lane; no muscle/tendon claim (C18 moment
  arms ABSENT — this is the joint-torque map, not a tendon model); no
  measured-muscle claim (A08-U1..U5 absent); no friction measurement claim;
  no grasp-completion claim; no x_press qualification claim (TC-8 stays 0/8);
  no dynamics or stability claim (statics only); no whole-creature or
  aliveness claim; NO PICTURE INSPECTION (this is a text-only model — any
  visual question goes to the Flash Sergeant via the Lieutenant); the five
  retracted static quotes (GP1 section-6 list) MUST NOT appear in any output
  byte.

## 7. THE TC-8 MAP (which ports this derivation would qualify; which stay
absent)

- THE EIGHT PORTS (B05 sealed requirements chimera.mechanical_port_requirements.v1,
  object mat2-b05-mechanical-port-requirements, sha256 ef69ee74...47f3d, per
  PORT_QUALIFICATION.md): BIClong-P11, BICshort-P8, BRD-P3, PT-P5 (tendon
  endpoint sites on body `radius`; tendons BIClong_tendon, BICshort_tendon,
  BRD_tendon, PT_tendon) and BIClong_l-P11, BICshort_l-P8, BRD_l-P3, PT_l-P5
  (body `radius_l`, left side). Status: ports_mechanically_qualified 0/8;
  per-port inputs blocked_as_measured (kappa_areal etc.); zero lawful
  stiffness pins (C17) and zero lawful friction pins (G04).
- THIS DERIVATION QUALIFIES ZERO OF THE 8. It is a static conditional-
  calculation on sealed artifacts; authored requirements, declared laws and
  demonstrated computations NEVER qualify a port. ALL EIGHT STAY ABSENT
  (blocked_as_measured). x_press stays ABSENT (TC-8 0/8): the 60 N
  per-channel press remains a DECLARED fixture operating point, never a
  channel, never a qualification.
- WHAT THE MAP RECORDS: the derivation names WHICH inputs a lawful anatomical
  press production would consume and their current lawful status: (i) the
  hand-chain joint caps beyond the name-matched MP cap — NONE EXIST (named
  gap; TC-8-adjacent); (ii) the wrist drive — ABSENT from the certified hand
  chain (named gap); (iii) the anchor-wrench producer — the forelimb tendon
  set, exactly the eight B05 ports above the wrist anchor, 0/8; (iv) the
  measured friction under the threshold arithmetic — ABSENT (bench-
  conditional). Outcome routing: under (a), the qualification path MUST pass
  through the eight ports' measured admission (MAT-03-class lead acts, c17
  lane completion, B05 qualification, or the honest refusal) — the derivation
  cannot and does not shortcut it; under (b), the eight ports stay absent and
  the closure stands without them; under (c), the named input gap becomes a
  TC-8 debt row.

## 8. Execution plan (Chain Stop 2) and evidence obligations

- Chain Stop 1 is THIS DRAFT — no runs, no package, no code. The Lieutenant
  pins the draft; the sealed package (Chain Stop 2) cites this draft's hash
  in its own prereg block.
- The run implements EVERY falsifier of sections 4.1/4.2 as a hard in-run
  refusal (the actuator-map revision-1 lesson: a declared falsifier that is
  not executed at run is a structural defect, not a formality).
- Declared outputs (all via `--keep`, hashed into the runner receipt and this
  lane's EVIDENCE.md): `outputs/press_derivation_receipt.json` (input gate;
  per-posture/configuration coefficient tables; forward F* table; the linear
  actuator-law schedule; inverse tau_req + shortfall rows; anchor-wrench rows;
  determinism block; honest-absent inventory), `outputs/press_derivation_report.txt`
  (human-readable frontier + shortfall + TC-8 map tables),
  `outputs/press_law.json` (the derived actuator law, CONDITIONAL-CALCULATION
  labeled).
- Lane EVIDENCE.md records sha256 of: this draft, the package script, every
  seal manifest hash + base SHA, every runner receipt, every output, and the
  section 2 input pins re-verified at run.
- Chain stop: after the run and its EVIDENCE.md, this lane makes no further
  claims; the sealed receipt is the deliverable; independent review stays
  with the Flash Sergeant via the Lieutenant.
