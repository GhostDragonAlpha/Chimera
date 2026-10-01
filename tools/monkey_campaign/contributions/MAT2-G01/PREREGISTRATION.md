# PREREGISTRATION - MAT2-G01 (derive support and grip feasibility)

Frozen 2026-09-30, BEFORE implementation and before any derivation run.
Composed against CARD_STARTER v3 (the 12-gate batch harness, the
evidence-anchoring law, the publication pattern), the house-standards
IMPLEMENTER_CHECKLIST G1-G9 / TOOLKIT P1-P9, FORMAT_SPEC v0 (content
addressing), and the card-kit generator pattern. This file exists before the
implementation files named in section 11; at freeze time none of them existed.

## 1. Task identity

- task_id: MAT2-G01 (registry SHORT form for any manifest/context: G01).
- planning_ids: G01. Group: Grasp and climbing mechanics; kind: derivation;
  profile: records/offline. Calculations C19 (grip contact wrench capacity),
  C20 (vertical transfer and climbing load). Catalog refs CTRL-03, CTRL-04,
  BIO-02, CON-03, CON-04, DYN-02 (holodeck catalog rows; recorded in the
  receipt).
- attempt id: 682fec627d7a413cb0fff77388436868
- agent: wk-g01-feasibility (slot 2, branch-2)
- criteria_sha256: c79a569f7259084e948d60058ccd850ccb671af30e61062c59295d152b9f0374
  (identical across dispatch, registry attempt, this prereg, and the checks
  identity; carried into the publication request args).
- ontology scope_sha256: cb5475f8486197a973edc4360b177fc31a629c4f0979ebf80dd76aae57996097;
  definition_raw_sha256: 57ded6eb2f2cc6aa914d6f68c8efb55b215790fc7a9d0baa5dfd2c49fd1465c1.
- workspace: E:/ChimeraWork/monkey-coordination/kanban-attempts/MAT2-G01/682fec627d7a413cb0fff77388436868
- checkout: sparse at tools/monkey_campaign/contributions/MAT2-G01/, branch-2,
  base ced164735e5c2ff0a9662b04e7ffa28fd081f160 (= origin/astra/gait-capture;
  the MAT2-W04 merge PR #295; carries sealed A09, F03, W04, D-MASSREG).
- CPU-ONLY card: no GPU queue submission, no training, no runtime. Records
  and offline arithmetic over pinned bytes.

## 2. done_when (verbatim from the card)

"Required force/moment support lies within reachable contacts and actuator
bounds for the declared trunk"

Card observation (verbatim, binds the claim class): "Static support is
necessary, not proof of climbing".

Card falsifier (verbatim): "Missing identities or a claimed pass unsupported
by records fails; a screenshot is not a substitute."

Card law (dispatch): feasibility can FAIL honestly; if required support lies
OUTSIDE reachable bounds for the declared trunk, the honest negative result IS
the card outcome - record it, do not tune it away.

## 3. Reconciliation of the dispatch language against the sealed records

The dispatch described upstream "F03" as "the forearm package: the source
shoulder/elbow coupled native forces + the fictional-Chimanoid falsifier
history" and named "the W03 trunk declaration". The sealed records say
otherwise, and the dispatch itself orders the wave brief checked first:

- Wave-6 brief (verbatim): "Builds on wave-4 A09, sealed F03 (one rigid
  climbable trunk) and wave-5 W04." The evidence-store MAT2-F03 record is the
  one-rigid-climbable-trunk package (PR #248, Sergeant PASS). This card
  composes against THAT F03.
- W03 is the walk-lane parity-replay verification card; the trunk declaration
  lineage is F01/F03 (trunk_declaration.json pinned at dc7ea811; F03's sealed
  trunk_01 mesh 3b174417...). "The declared trunk" for THIS card is F03's
  sealed trunk_01.
- The "Chimanoid" string belongs to ONT-A02 (FreeMusco's fictional model
  disclosure), a different lane; it is not a G01 input.
- Recorded as an observed dispatch-vs-store discrepancy; the sealed records
  govern. No upstream record was modified.

## 4. The declared trunk and the buffer-absent story

trunk_01 as sealed by F03: mesh 3b17441764714c5e5e9c7a43c3253b3271a0f508954095e1960a57820cef6ee
(pin P3), 130 vertices / 128 triangles, shell region with exact seam
duplicates (welded closed for volume), declared density 760 kg/m3 (band
650-850, researched class), mass 3.7850835688601157 kg, band
[3.2372425259987834, 4.233317149383025], passive law rigid-and-rooted
(RED-1 rigid-by-declaration; no bonds), contact law M06 with
mu_s = 0.6 UNEVIDENCED-PLACEHOLDER (acquisition_prerequisite G04). Geometry
(radius 0.037 m, height 1.158 m) is DERIVED by this card from the pinned mesh
bounds and cross-checked against P2's analytic solid volume
0.004980373116921205 m3 - never asserted from prose.

Buffer-absent (the trunk files story): the trunk exists as a DECLARED OVERLAY
in record space - a sealed mesh/material/law bundle plus scoped contact
experiments (S1/S2/S3 on instantiated parts). NO runtime scene co-instantiates
the trunk with any creature body: the adopted assembly has no runtime scene
module at all (W04 honest limitation, verbatim: "a runtime scene module
executing the adopted assembly (none exists)"), and the sealed walk scene
carries no trunk. Co-instantiation of the full three-part forest scene is
REFUSED by the unmodified M06 solver (F03 A3: nonfinite_state). The
feasibility derived here is therefore a RECORD-SPACE derivation over sealed
lineages; no engine frame, screenshot, or runtime world is claimed or needed
(records/offline profile).

## 5. Input pins (sha256 per file; the generator refuses input_pin_drift)

In-repo pins, all at base ced164735e5c2ff0a9662b04e7ffa28fd081f160 (extracted
with git cat-file at run time and hash-verified against THIS table):

| role | path at base | sha256 |
|---|---|---|
| A09 grasp anatomy package | tools/monkey_campaign/contributions/MAT2-A09/grasp_package.json | 0a70adb1029d860ac9504683d77c2e94be2634724c63479f827fcbc8fcd97d24 |
| F03 numerical record (S1/S3 experiments, trunk mass/volume) | tools/monkey_campaign/contributions/MAT2-F03/evidence/checks.json | 0f5463c618e55a3453e109010ff7a8b33d316f69bfdf207caea6d338cbeeeb71 |
| F03 sealed trunk mesh | tools/monkey_campaign/contributions/MAT2-F03/assets/trunk_01_mesh.json | 3b17441764714c5e5e9c7a43c3253b3271a0f508954095e1960a57820cef6ee7 |
| W04 freeze manifest (actuation caps, mass rulings, refusal identities) | tools/monkey_campaign/contributions/MAT2-W04/w04_freeze_manifest.json | be632ffc85865515285f3d622a09882a3180a43101027914f1ed3408496f5d29 |
| D-MASSREG mass register (scene vs biological-reference systems) | tools/monkey_campaign/contributions/MAT2-D-MASSREG/mass_register.json | 61fb79b1bf2df8c5e1a5b1bff2ab1c4f41700de25bc7f1a114cbc78fe693cc7a |

Coordination-space sealed pins:

| role | path | sha256 |
|---|---|---|
| GRASP_BENCHMARK.md (g anchor 9.80665, capacity conversion 35.98770642201834 N, BW placement) | E:/ChimeraWork/research-data/20260929/benchmark-grasp/GRASP_BENCHMARK.md | d936cebe38b1416dfc417db727ea81396eb8eb9217efed3f05b344db17f71610 |
| B07 PORT_QUALIFICATION.md (0/8 ports, 24/24 waypoint refusals, refusal codes verbatim) | E:/ChimeraWork/monkey-coordination/evidence-store/MAT2-B07/numerical/PORT_QUALIFICATION.md | 4818d4b03576f2821f75f49b2d54f8c01378763b1ad1441075dda267c9ff3f00 |
| REPIN_STUDY.md (pin inventory, GAP ledger, mass adjudication) | E:/ChimeraWork/monkey-coordination/re-pin/REPIN_STUDY.md | 99cde4758566784b5b98ad45db19f50beba2c81d8b1761428af19e32290c318b |
| W03 report (10.037998 kg seating scan corroboration; weight 98.43913308670002 N) | E:/ChimeraWork/monkey-coordination/evidence-store/MAT2-W03/source/REPORT.md | 6692f07fc5314210c854884d1c17d7a8e561b1c9fa131c02131e3611198d64fa |
| C17 stiffness sources study (no measured C17 input exists) | E:/ChimeraWork/monkey-coordination/c17-stiffness/STIFFNESS_SOURCES.md | 309b1788fa35aefe4f0cd822300ba926b30648ec8a021460dfb7f06ffe30ff0e |

The generator re-verifies every pin at run time and refuses on drift or
absence.

## 6. Declared quantities read from the pins (the derivation consumes ONLY these)

- Grip channel (F03 S1 record, P5_m06_contact_binding): jn_Ns 0.3, mu_used
  0.6, mode stick, surface trunk_01.lateral, facet centroid (m06 frame)
  [0.036763000000000545, -0.002405999999999982, 0.38599999999999995], facet
  normal [0.9951835289511874, -0.09802930023345664, 0.0], grip_capacity_kg
  3.6697247706422016, ledger residual 7.354763734505376e-51. Demonstrated
  normal press operating point N0 = jn/dt = 0.30/0.005 = 60 N (dt = 0.005 s is
  the M06 contact-law pin; carried as the operating point, NEVER as an
  actuator capability). Channel capacity at g = 9.80665:
  c0 = 3.6697247706422016 kg * 9.80665 = 35.98770642201834 N (the anchor's
  own conversion; record-g 9.81 gives 36.0 N - both recorded).
- Trunk mass and weight: 3.7850835688601157 kg (P3_mass_provenance mass_kg).
- Creature weight W, TWO lawful readings, kept DISTINCT (D-MASSREG law: the
  two systems stay distinct; no reconciliation):
  - scene system: m_scene = 10.037998 kg (register scene carve total;
    corroborated by the W03 seating scan) -> W_scene = m_scene * 9.80665.
  - biological-reference system: the receipted Turnquist band rows 5.4 /
    6.15 / 6.9 kg (register reference.turnquist) -> W_band_lo/mid/hi.
- Grasp endpoints (A09 package, interface_graph.grasp_endpoints): 6 endpoints,
  all resolution=supported, all in the mutant hand frame
  (macaque_arm_hand_mutation_frame, anchored at the wrist joint location
  0 0 0); positions carried verbatim; NO transform composed (frame_chain law).
- A07 envelope facts (carried inside the A09 package counts):
  envelope_measured_outside 8 (4 outside insertions + 4 outside waypoints),
  attachments_mutant_supported 2 / unresolved 24, pending_assembly_mapping 14,
  grasp_endpoint_resolutions 6 supported.
- Actuator-side records: A08-U1 explicitly unresolved ("measured maximum
  isometric force (or measured PCSA plus measured specific tension) for the
  selected animal; the sealed carrier Fmax values are 22 derived-provisional /
  6 provenance-unknown / 11 hand-set defaults"); force_runtime_ready false for
  all 39; W04 actuation_interface caps "fore shoulder 4.229 / fore elbow
  3.76 N.m are the CERTIFIED 10.038 kg scene's drives only" with status
  RE_DECLARE_PENDING (TC-3 never-transfer law); B07 0/8 ports qualified,
  24/24 waypoints refused waypoint_not_a_port.
- g = 9.80665 (GRASP_BENCHMARK pin; F03's own S1 used record-g 9.81 - both
  carried, each labeled).

## 7. THE FROZEN DERIVATION FORM (freeze-before-implementation)

### 7.1 C19 static support model

Static hold at n contact channels on trunk_01.lateral: sum f + W = 0 with
per-channel tangential capacity c = mu * N (Coulomb limit, M06 law) and
per-channel required tangential load W/n (equal share declared HERE as the
model of the balance; the per-port load share is UNPINNED in every sealed
record - carried as named variable x_share, so n-channel rows are the
equal-share CASE ANALYSIS, not a partition claim).

Channel capacity is evaluated ONLY at the demonstrated operating point
N0 = 60 N: c0 = mu * N0 (record-g 36.0 N; standard-g 35.98770642201834 N).
Sensitivity law (declared, from the linear Coulomb form): capacity is linear
in mu and in N; the falsified understated-mu case (B7: mu 0.15 -> 0.9174311926605504 kg)
is carried as the sensitivity row.

Decision rule (frozen BEFORE the run), per body reading B and channel count
n in {1,2,3}:
- FRICTION-FEASIBLE(B, n) iff n * c0 >= W(B).
- PRESS-FEASIBLE(B, n) iff the required press per channel N_req = W(B)/(n*mu)
  <= N0 (the demonstrated operating point). PRESS-FEASIBLE is an OPERATING-
  POINT statement, never an actuator qualification.
- ACTUATOR-QUALIFIED: NO case can be actuator-qualified while x_press (the
  measured grip-force actuator bound) is ABSENT (A08-U1; ports 0/8; BIO-02
  energy-budgeted actuator models PROPOSED). The within-actuator-bounds clause
  of done_when is therefore evaluated CONDITIONALLY and the condition is
  named.

### 7.2 Moment model (C19 second clause)

sum r x f + external moments = 0. Every sealed demonstrated grip case is
zero-external-moment (S1 static stick on a rooted vertical trunk; S3 rest).
The creature-hold moment about the grip axis requires the CoM offset r_com
from the grip axis - ABSENT (no grasp-posture CoM record; B06 CHK-8 zero
transported segment masses; the walk-scene CoM is posture-specific and is
NOT consumed). Carried as named variable x_com; the receipt tabulates the
moment template M_req = W * |x_com| at the two declared disclosure probes
|x_com| in {0, span_rec/2} where span_rec is the recorded fingertip span
(arithmetic disclosures, never feasibility claims).

Trunk-side support: the declared trunk admits any reaction BY DECLARATION
ONLY (rigid-and-rooted, RED-1, M04 profile rigid, source_status
synthetic_authored). No measured trunk/root strength bound exists in any
pinned source (the 1290 lbf table cell is unadjudicated column semantics and
is NOT consumed). Carried as named variable x_trunk_strength. The receipt
tabulates the root-moment template at the pinned facet height 0.386 m:
M_root = W * 0.386 (arithmetic disclosure at the S1 facet, per body reading).

### 7.3 Reach model (the "reachable contacts" clause)

Reaching a trunk contact requires the hand-to-trunk placement T_hand_trunk -
ABSENT BY LAW (A09 frame_chain law verbatim: "every packaged position carries
its source frame declaration; NO transform is composed between frames and NO
new fit is recorded"; A07: forearm correspondences explicitly unresolved, the
A05 mutation record's scope is the hand; C01 round-trip verification is
registered as still REQUIRED downstream). Carried as named variable x_reach;
NO synthetic transform is composed, no world placement is invented.

What IS derivable in-record (arithmetic inside the hand frame only):
- span_rec: the maximum pairwise distance among the five supported fingertip
  endpoints (exact arithmetic on the pinned positions).
- The wrap-geometry comparison: a rigid set of contact points enclosing a
  disc of diameter D must have diameter >= D; compare span_rec against the
  declared trunk diameter 2r = 0.074 m. Recorded-configuration-only result;
  achievable aperture is a configuration variable (joint limits ABSENT, C05
  inputs open) carried as named variable x_aperture.
- The A07 outside-counts (8 outside sites; 24/26 attachments unresolved;
  pending_assembly_mapping 14) carried as the arm-side reach-chain state:
  explicitly unresolved, never defaulted.

### 7.4 C20 vertical transfer (climbing load)

Potential-energy requirement (static-to-quasistatic line only):
Delta_E(h) = W(B) * h at the declared heights h in {0.386 (S1 facet height),
1.158 (full trunk height)}. Dynamic transfer inputs - support sequence, body
inertia of the adopted assembly, transfer trajectory, losses - are ABSENT
(name them: x_sequence, x_inertia, x_trajectory, x_losses). The card
observation binds the claim class: static support is necessary, not proof of
climbing; NO ascent feasibility is claimed. GAP-9 (duty factor / contact
channels missing from the sealed walk trace) is carried as the reason the
dynamic line cannot even be screened.

### 7.5 The named-variable law

Every absent interface quantity is carried as a NAMED VARIABLE with its
absence provenance and, where derivable, declared bounds. The five primary
variables: x_reach (T_hand_trunk, absent by A09/A07/C01 law), x_press
(measured grip-force actuator bound; A08-U1), x_com (grasp-posture CoM
offset), x_trunk_strength (measured trunk/root strength), x_share (per-port
load share) plus the C20 set. NO synthetic constant may occupy an absent
slot (the lambda_min law: declared never qualifies, synthetic never
transfers). A derivation row that fills an absent slot with a number fails
the named-variable gate.

### 7.6 The frozen verdict vocabulary

Per-clause verdicts are exactly one of: WITHIN (records support the clause),
OUTSIDE (records refute the clause), CONDITIONAL (the clause reduces to named
variables that are absent; listed), UNDECIDABLE-IN-RECORDS (no lawful
arithmetic exists). The overall verdict composes the clause verdicts. An
honest OUTSIDE or CONDITIONAL overall is a VALID card outcome; tuning any
input to flip a verdict is forbidden.

## 8. Falsifier arms (bite suite; tampered copies in attempt scratch, never committed)

Each arm: clean control FIRST in the same executable, named premature guard,
then the tampered copy must bite.

- G1FB1 verdict_tamper: flip one computed verdict row (single-channel
  OUTSIDE -> WITHIN) in a scratch receipt copy -> the verdict-consistency
  check FAILS (recomputation disagrees with the row).
- G1FB2 synthetic_constant_in_absent_slot: replace one named-variable absence
  marker with a synthetic numeric constant in a scratch copy -> the
  named-variable gate FAILS.
- G1FB3 source_drift: perturb a pinned input value in a scratch copy of a
  pin (grip capacity 36 -> 30 N) -> the bit-reproduction check FAILS.
- G1FB4 claim_without_record: inject an unbacked pass claim (a within-bounds
  verdict row with no receipt citation) -> the claim-tracing check FAILS
  (the card falsifier: a claimed pass unsupported by records fails).

Preflight: clean fixtures pass all four detectors before any tampered run
(guards g01_fb1_premature .. g01_fb4_premature).

## 9. Determinism and receipts

- feasibility_receipt.json (schema chimera.g01.feasibility.v1): canonical
  JSON (sorted keys, no spaces, ensure_ascii=False, allow_nan=False, UTF-8,
  LF), no wall-clock in receipts. Every input re-verified at run time;
  refusals: input_pin_missing, input_pin_drift.
- X2 determinism: two fresh runs produce byte-identical receipts (the
  receipt is the determinism unit); rerun receipts compared with declared
  augmentation keys only.
- Named-check suite test_g01_checks.py: one check per done_when clause +
  the four falsifier arms + pin/lint probes. ZERO skips planned; the claim
  will state "N executed, 0 skipped" (no KNOWN_SKIPS).
- Report GENERATED by make_report.py from the receipts (zero hand-written
  numbers); lint_report_numbers.py (+ --selftest) enforces printed-precision
  traceability (G2).
- Catalog rows CTRL-03/CTRL-04/BIO-02/CON-03/CON-04/DYN-02 and calcs C19/C20
  are recorded in the receipt as the card's contract frame (titles,
  statements, falsifiers) exactly as read from docs/roadmap/holodeck_tasks.json
  and the completion map at the base revision.

## 10. Nonvisual rationale (predeclared)

records/offline card over pinned bytes: no rendered scene, no camera, no
clean view; the verification profile requires records/numerical oracle only
("a screenshot is not a substitute"). Visual evidence classes do not apply.
Numerical and independent review remain required.

## 11. Files this prereg names (none existed at freeze time)

- run_feasibility.py (modes: main / rerun / falsify)
- feasibility_receipt.json
- test_g01_checks.py
- make_report.py, lint_report_numbers.py, REPORT.md (generated)
- .gitattributes (path-local `* -text`)

## 12. Refusal codes declared now

input_pin_missing, input_pin_drift, verdict_tamper_detected,
synthetic_constant_in_absent_slot, claim_without_record,
vacuous_comparison_refused, unavailable_body_reading.

## 13. Known limits declared now

- The verdict is a record-space derivation; it creates no runtime scene, no
  port qualification, and no actuator admission.
- The equal-share case analysis is a model of the balance (x_share absent),
  not a measured load partition.
- mu_s = 0.6 is the declared placeholder (G04 debt); every capacity number
  inherits it and the receipt carries the linear sensitivity law.
- The scene-vs-band body readings stay distinct ledgers (D-MASSREG law);
  split verdicts are recorded per reading, never averaged.
- GAP-1 (osim muscle placeholders), GAP-5 (palm friction), GAP-6 (C17 inputs
  lawfully absent), GAP-9 (missing duty-factor channel) are inherited
  constraints, not repaired here.
