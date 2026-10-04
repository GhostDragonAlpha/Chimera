# PHASE_CONTRACTS.md — THE ZERO-RECORD CLIMB PHASES: ASCEND, HOLD-AT-HEIGHT, DESCEND, RESUME-GROUND

Lane: `E:/ChimeraWork/monkey-coordination/climb-spec/` (records lane; phase 1 =
SPECIFICATION + PREREG SKELETON ONLY; NO runs, NO worktrees, NO clones, NO Git
mutation, NO runner job). Worker: wk-climb-spec. Date: 2026-10-04.
NO_WORKTREES.md obeyed: sha256
`7d3fe1029f727b95ff2c832b06a89b3bac40f59e14993440255636218645f433`
(re-hashed by this lane; every hash in this lane's EVIDENCE.md was recomputed
from the bytes, never copied).

Reading checkout: `E:/PythonChimera` branch `WK-ENGINE-PATHS-20260929-PR`,
HEAD `7222729eca6e9f97f25061c8b1dc3d229bb703d8` (dirty state preserved;
repository used READ-ONLY).

## 0. WHAT THIS DOCUMENT IS AND IS NOT

- It IS the phase-contract specification for the four demonstration phases
  between the grasp and the landing that have ZERO RECORDS today: climb
  (ascend), hold-at-height, descend, resume-ground
  (`completion-matrix/MATRIX.md` sections 1.5, 1.6/1.7, 1.10, sha256
  `fd6c7caeca360ef4cb0d7ef44a1845b7e02c189dffa969718f9a87ae18eca68a`, read
  2026-10-04). Authoring a contract is a SPECIFICATION event, never a physics,
  training, integration or qualification event (K01 falsifier F6, K02
  falsifier F6; the objective-line law: "A COMPLETED SPECIFICATION IS NOT A
  TRAINED SKILL").
- It IS a consumer of the published chain, pinned by hash in this lane's
  EVIDENCE.md: the K-tier specs frozen CONDITIONAL on grasp (K01 skill spec,
  PIN `4d697d7c` on `origin/review/K01-SKILL-SPEC-20261003`, bytes sha256
  `fdc2e79aea9479fd4d6f9d761694ba1edbe6430b1bf1ee9df6fed64ca9ac0935`, all
  eight registry elements; K02 reset scenarios, PIN `1c943ea3` on
  `origin/review/K02-RESET-SCENARIOS-20261003`, bytes sha256
  `d23117a3810c3fccf9623194cfdadba4c33b2289a5cbf8d833e4d82960a18ab3`, pins
  K01's bytes); the grasp line (#344 merged `28a110f2`: "354/354 GENUINE —
  THE PAD IS THE INTERFACE"); the VPL-1 native N0 (#348 merged `ffc09b27`,
  recording-only tier published, the N1 force-feeding tier the named next
  rung); the climb derivation (`climb-derivation/DERIVATION.md` sha256
  `da34420558f6632b0544ca94bc3e25ece515027628c7bd8cc54b9fdd30b7ebd9`);
  the hold/release/landing fixture-class certifications (K02 impl + landing
  PR `10b05f9f`/`2ee6918`); the walk line (W-tier complete, W10 PR #311).
- It IS NOT: a training authorization (master law K01 0.4: NO TRAINING RUN
  until a qualified grasp configuration exists — the seven named
  prerequisites); a dispatch (this lane holds NO dispatch authority beyond
  phase 1); a completion claim (all four phases remain ABSENT as behavior —
  zero runs, zero captures, zero board events for resume-ground).
- Every number below is either copied from the hash-pinned chain with its
  source named, or a declared CONDITIONAL-CALCULATION of the sealed law forms
  under assumptions A1-A7 (`DERIVATION.md` section 8.1). The friction
  placeholders are consumed under the M1-corrected attribution (this lane's
  `DERIVATION_UPDATE.md`): the sealed trunk pin is mu_s/mu_k = 0.6/0.6
  UNEVIDENCED-PLACEHOLDER (scene `contact_friction` 0.6 single-scalar; the
  M06 probe-shell block 0.6/0.4 synthetic-authored, combined by the
  elementwise_min pair rule), and the 0.41 value is the Gerhardt-2008 HUMAN
  volar-forearm-on-TEXTILE analogue scoped to BAND ARITHMETIC ONLY — never a
  scene parameter, never a run configuration value. "Monkey-bark friction
  (macaque volar skin on bark at the 20-60 N operating load) is UNMEASURED";
  the friction bench is the CAPTAIN's docket item.

## 0.1 The two named physics dependencies (binding on all four contracts)

Every one of the four phases has PHYSICS that does not exist on the creature
line until BOTH of these land. They are named here with their exact states;
no phase contract may be read as if either existed.

- **DEP-N — the N1 causal tier (the pad must push).** State: PREREG DRAFT
  AUTHORED, NOT RUN — `vpl1-native/PREREGISTRATION_N1_FEED.md` sha256
  `58fd70493fb05c964b025a2ff30da17af8fb6b231d455ce652a2f7dd1f6c3a5d` (the
  Lieutenant-authorized N1 force-feeding tier, the named next rung from the
  #348 publication; the two preconditions enforced at pin time: the F1
  sub-window amendment OPTION (a) adopted — the u <= 0 sub-window excluded
  from PAD_CONTACT, class PAD_ENGAGED_UNCOMPRESSED, zero force by the amended
  unilateral law p = max(0, k*u/t) — and the harmonized one-classifier sign
  handling; the G08 parity re-bind on its three-tier basis with the REQUIRED
  feed-on divergence). The tier below it is REAL and published: VPL-1 native
  N0 (#348) is RECORDING-ONLY with ZERO solver coupling — "the pad is NOT a
  support element (F_max = K_eff*t = 0.24 N)". Consequence: until an N1 run
  is published with the causal classes FEED_APPLIED/FEED_ZERO sealed, any
  climb-phase episode on the native creature line has pads that record but do
  not push — the climb phases cannot physically exist there. N1's declared
  Tier-3 bounds (the N1 draft's own account: max total pad force 0.40961 N =
  0.68% of band BW; dx/dy divergence <= 0.01 m; refusal tick within
  +-15 of the padless 302) are that tier's OWN envelope, not this lane's.
- **DEP-P — the press channel (the grip normal force has no actuator
  derivation).** State: ABSENT — x_press is one of the ten named-absent
  variables (refused at the seam, `named_absent_occupied`); TC-8 measured
  port inputs are 0/8 with the honest refusal standing. The 60.0 N per
  channel operating point (jn = 0.3 N*s per tick per channel; jn/DT = 60.0 N)
  is a DECLARED fixture operating point (F03 S1), never an actuator
  qualification; no derivation exists from the capped scene servo drives
  (hind hip 11.2125 / knee 6.6375 / ankle 7.4 / MP 0.8875; fore shoulder
  4.229 / elbow 3.76 N*m) to a 60 N grip normal — it needs the limb lever
  arms in the grasp posture (x_reach/x_inertia ABSENT, gaps 4-5) and either
  a measured isometric force or PCSA x specific tension (the C17 line).
  K05's composition law governs its future: the trained climb channel must
  DECOMPOSE INTO CAPPED SERVO INTENTS; the G06 climb channel (a declared
  kinematic schedule) is NOT an available actuator. Consequence: every
  friction-supported tick in all four phase contracts is, today, a
  fixture-declared press — the same-hands debt stands (the 0.049 kg
  anatomical hand cannot statically carry the 10.037998 kg line through this
  solver; m_eff = 0.048761970806378674 kg, impulse ratio ~1/205,
  `DERIVATION.md` section 2).

Named additional dependencies, per phase, below. The four phases are ordered
as the goal orders them; the phase numbering C1-C4 is this lane's.

---

## C1 — CLIMB (ASCEND)

**Record state: ABSENT as behavior.** The only sealed ascent physics is the
G06 climb-bridge (merged PR #305 @ 5f82a3dd): 3 transfers CLOSED at FIXTURE
class with per-tick admissible support (jt 0.132-0.169 vs capacity 0.18 N*s,
stick arrest <= 1e-12, zero drift; `evidence-store/MAT2-G06/report/REPORT.md`
sha256 `2e4343191591322d...`). G06 used DECLARED pads at the declared
operating point on the trunk's own contact sites; it is transfer physics, not
climbing behavior. No run, no training run, no capture of ascending exists
for any creature line.

### C1.1 Entry conditions (from the grasp chain)

- E1 QUALIFIED GRASP: a qualified grasp configuration exists per the K01
  master conditionality section 0.4 (all seven named prerequisites, each with
  its own sealed receipt). Until the grasp chain's stage-5 runtime rung is
  met, this entry is CLOSED — the pad interface is proven (#344, 354/354
  GENUINE) and the VPL-1 pad class is natively proven at N0 (recording-only);
  the grasp closure itself is the open rung (wrap margin -0.01733690019744087 m
  for the recorded configuration at the declared 74 mm trunk;
  UNDECIDABLE for the anatomical achievable aperture).
- E2 LAWFUL INITIAL STATE: the episode's initial state is a K02 catalog
  state (RS-01..RS-22 class) or its successor under the same validity law —
  a declared fixture (or, when the grasp chain allows, anatomical) grasp at
  trunk_01 (0.074 m x 1.158 m, lateral sites), source facet (triangle 0)
  under the pads, press at the declared operating point, validity V1-V5
  verified AT THE BOUNDARY (ledger identity, facet geometry, declared
  contact set, seam-delivered setup, no solver-refused state).
- E3 STAGE-B SUPPORT AT THE POST-ATTACH (reading, n): the static support row
  WITHIN at the declared reading and channel count (band n>=2 / scene n=3
  static; the corrected closure thresholds: band n=3
  0.2941995 / 0.33506054166666666 / 0.37592158333333336 standard-g; band n=2
  0.44129925000000003 / 0.5025908125 / 0.563882375; scene n=3
  0.5468840727038888 standard-g / 0.5470708910000001 record-g; scene n=2
  0.8203261090558333 — all CONDITIONAL-CALCULATION, per-reading, per-A1-A7).
- E4 INTENT: the climb intent declared through the U05 versioned seam
  (one explicit intent reaches the skill selector; the frozen walk contract
  unchanged).
- E5 ENVELOPE DECLARED: the training envelope E1-E7 of the K01 spec frozen
  BEFORE the run (corridor = band n=3 at the placeholder mu; scene-line and
  all n=1/n=2 transfer rows FROZEN failure regions; n=4 carried as
  FEASIBILITY CANDIDATE with its five unmet demonstrations — (a)
  fourth-contact reachability, (b) simultaneous sustainability, (c)
  load-sharing, (d) contact independence, (e) dynamic transfer — and its
  declaration a SEPARATE DECISION, NOT MADE by this lane).

### C1.2 Exit conditions

- X1 CORRIDOR CLOSE: every declared envelope tick of every executed transfer
  records admissible support (the 219-tick contiguous span class from attach
  through hold2 end), and the completed rise matches the declared template
  accounting (3 transfers x 0.38599999999999995 m = 1.158 m = trunk height;
  687 ticks; mean template rate 0.33711790393013097 m/s; the stage-D
  accel/cruise/brake/hover schedule) with the energy account closed. Exit
  state: the re-attach/hold2 state at the target facet — the C2 entry state.
- X2 SLIP-STOP (the honest terminal): the first slip-mode tick at a HOLDING
  channel during load/hold/transfer terminates the episode (the sealed slip
  recursion is the stop law). Slip observed at a lawful failure region is the
  SUPPORTED PREDICTION outcome, recorded, never reset away, never a pass.
- X3 ENVELOPE BREACH / UNDECLARED RELEASE / INTEGRITY REFUSAL / HORIZON END:
  the K01 terminations T2-T5 verbatim; a termination is not a success;
  failures are retained.

### C1.3 State variables (declared, measurable, timed)

The G05 seam (`chimera.g05_obs.v1`, OBS_DIM 32, 36 declared keys, one sample
per solver tick post-solve, no interpolation, no hidden lookahead) composed
with the certified walking interface (`policy_observation_interface v2`,
dim 80, privileged_forbidden, history 0) under the declared aliasing law —
exactly the K01 observation space, NOT re-declared here. Per-channel group x
declared channels: contact flag, stick flag, slip flag, jn, jt, contact
force (DECLARED conversion jn/dt), cumulative downward displacement, measured
centroid z. Aggregates: support count, supported flag, release flag, trunk
anchor z (the VISIBLE recorded anchor), full-tick residual max, reciprocity
max, availability slots. Phase universe: approach, attach, load, hold,
transfer, attach2, load2, hold2, release. Body-level: z, v_z, stored
potential energy (per full trunk, standard-g: band_lo 61.322943779999996 J /
band_mid 69.840019305 J / band_hi 78.35709483 J / scene 113.99251611439858 J
— CONDITIONAL-CALCULATION, = the sealed G01 C20 rows), the press-work
account. The ten x_* variables stay ABSENT with verbatim provenance; no
synthetic constant occupies an absent slot.

### C1.4 Physics law (the sealed ascent law, at fixture class until DEP-P lands)

- Per-tick support: static P_req = W/(n*mu_s), WITHIN iff <= 60.0 N per
  channel (the sealed G01 rows are the standard-g authority).
- Transfer admissibility = the G01 row at (reading, n-1); closed form
  (m/(n-1))*g*DT <= mu_s*jn = 0.18 N*s per holding channel; the m/(n-1)
  handover law (band_mid n=3 handover holder_mass_kg 3.075, trace tick 31).
  The three band n=3 closing requirements 0.13243500000000002 /
  0.15082875 / 0.16922250000000003 N*s vs capacity 0.18 N*s (thinnest margin
  0.010777499999999968 N*s at band_hi); the FROZEN FAILURE REGIONS: scene n=3
  0.24618190095000003; scene n=2 0.49236380190000006; band n=2
  0.26487000000000005 / 0.3016575 / 0.33844500000000005 N*s; all n=1.
- The G06 229-tick schedule (approach 1, attach 4, load 8, hold 11, handover
  31, transfer 31, re-attach 193, attach2 193, load2 197, hold2 200-219,
  release 220), climb-template envelope span [4,219], fixture reach envelope
  0.5 m, v_climb 0.5 m/s.
- mu placeholder law: mu_s = 0.6 effective (the M1-corrected attribution:
  the trunk pin 0.6/0.6 UNEVIDENCED-PLACEHOLDER, elementwise_min pair rule
  with the M06 0.6/0.4 block) is a NAMED placeholder; no re-pin mid-run; the
  0.41 human-textile analogue is band-arithmetic sensitivity context only.

### C1.5 Interface to the certified phases (the anti-assist boundary)

- The C1 entry state is produced by the previous phase's own solver
  evolution (approach -> grasp -> attach) or by a K02 catalog reset OUTSIDE
  the composed episode. In a composed session there is NO reset at the
  ascend boundary: the attach state arrives by continuous physics. A reset
  executed between phases INSIDE a composed session is a hidden in-episode
  assist (K02 law D3/F4 applied verbatim across phase boundaries).
- Every C1 boundary delivery passes the seam gates (undeclared_field,
  timing_unbound, timing_drift, named_absent_occupied, privileged_source,
  nonfinite_value, dim_mismatch); any refusal is an integrity termination
  (T4), never a repair.
- Evidence keys at the boundary follow the G05/G06 seam pattern (per-phase
  evidence keys; the K08 composition consumes them).

### C1.6 The honest dependency statement

C1's PHYSICS depends on DEP-N (the N1 causal tier; state: prereg draft
authored `58fd7049...`, NOT RUN — without it the pads record but do not
push, so no native ascend tick carries real pad force) and DEP-P (the press
channel; state: ABSENT, x_press, TC-8 0/8 — without it the 0.18 N*s
per-channel transfer capacity is a DECLARED fixture number, never an
actuator-qualified one). Additionally: the friction acquisition (gap 1,
NB-01/02 — the bench is the CAPTAIN's docket item; at the 0.41 analogue NO
transfer case closes at any tested n, so the corridor's existence is
hostage to one unmeasured number); the mass-lineage decision (gap 9 — under
the sealed law the certified 10.037998 kg scene line has NO closing transfer
at any tested n; its only unrefuted shape is the n=4 FEASIBILITY CANDIDATE);
the P04 training reservations for any training-bearing run (K03).
The certification class available WITHOUT those dependencies is exactly
G06's: CERTIFIED FIXTURE-BASED transfer physics. It is not climbing behavior
and this contract does not claim it is.

---

## C2 — HOLD-AT-HEIGHT

**Record state: SPLIT.** Static hold is CERTIFIED FIXTURE-BASED (K02 static
hold, merged PR #316 @ 7c1f395a, sealed job e4a9da8c PASSED, verdict
CONFIRMING_MIXED_AS_PREDICTED, P1-P5 SUPPORTED: the certified scene|n=3
fixture line sticks every channel every tick across W20/W100/W300 at the
placeholder mu, zero slip ticks, press worst deviation 1.01e-12 N*s, measured
creep [0,0,0] m). Hold AT HEIGHT — the same law re-armed at height with the
stored potential energy at stake — has ZERO records. The K02 view-spec id is
self-declared "K02-STATIC-HOLD-20261002-hold-site-fixture"; per the
objective-line law in its own receipt, that completes the SUSTAIN diagnostic
at the declared parameters and NEVER completes the playable hold objective.

### C2.1 Entry conditions

- E1: the C1 exit state X1 — the hold2 law re-armed at the target facet
  (triangle 1 class), arrived at by executed transfers (or, for a scoped
  first run, the K02 catalog's hold-class states RS-10..RS-22 armed at a
  declared height offset — a DECLARED scenario state, never a teleport to
  height; a height-offset initial state must be constructed as a new
  declared fixture state under the K02 validity law V1-V5 and its own
  prereg, or reached by physics; a teleport is an assist).
- E2: the stage-B static row WITHIN at the holding (reading, n).
- E3: the hold intent declared (the climb family's hold; the U05 seam).

### C2.2 Exit conditions

- X1 TO DESCEND: the descend intent declared; the brake template armed
  (C3 entry).
- X2 TO RELEASE: the release intent declared; the K02 P4 release structure
  executes (the G07 20-hold + 40-release class); the landing phase consumes
  the released body.
- X3 FAILURE ARMS: slip at any holding channel (T1); an UNDECLARED release
  terminates as a failure (T2); integrity refusals terminate (T4); horizon
  end without the hold metrics met is a failure (T5).
- The stored PE is the stake, not a state to manage away: on any failure the
  release account pays it back (the G07 identity below). There is no
  mechanism in this contract that discharges stored PE except declared
  descent or declared release.

### C2.3 State variables

The C1.3 set, plus: the hold window counters (the hold2 200-219 class), the
press-work account (the measured scene|n=3 press cost 0.040346690644887555
J/tick — the G07 recorded operating-point value, a CONDITIONAL-CALCULATION
bound, never a budget grant), the
gravity==friction hold accounting (the G07 exact class: gravity work
0.24150444483195008 J == friction losses 0.24150444482831965 J, delta
3.63e-12 J at ~zero KE), and the cumulative creep channel (stick class
records EXACT ZERO cumulative creep per K02 P1; the G07 scene hold's implied
creep 0.0024525000000000007 m per 20 ticks is the recorded alternative class
— BOTH are recorded findings, never normalized, never erased).

### C2.4 Physics law

The hold law is stage B's static row per tick: the friction limit
mu_s*N per channel IS the only support channel in the sealed solver (the
zero-mu control cannot hold: G04 FB2 / G06 mu=0 non-closing; the sealed
sibling class slides 0.05150250000055512 m under full press). The hold is
NOT free but bounded and small at the operating point. Stick-class hold law
(band_hi|n=2): press 0.5217391304347825 J / friction 0.1660072724981848 J;
slip class (band_hi|n=1) never holds.

### C2.5 Interface to the certified phases

- Upstream: the C1 boundary law (C1.5) applies verbatim — hold-at-height
  arrives by executed transfers or by a DECLARED catalog state, never by a
  mid-episode teleport to height.
- Downstream: the release exit is the K02 P4 / G07 certified structure at
  fixture class (W_press == 0.0 J EXACTLY every release tick; free-fall
  recursion worst 5.81e-12 m/s; gravity work 19.320355586443497 J == KE gain
  19.320355586289068 J within 1.54e-10 J; terminal speed delta 1.27e-11;
  120 post-release contact records RECORDED-NOT-SUPPORTING, max 6.48e-11
  N*s); the landing card (#324 @ 2ee6918) is the certified consumer at
  fixture class. The descent exit is C3's entry. No re-press, no contact
  restoration, no creep erase at either boundary (K02 D3 across phases).

### C2.6 The honest dependency statement

C2's PHYSICS depends on DEP-N and DEP-P exactly as C1.6 (a hold is a
press-sustained friction balance; without the press channel the hold is
fixture-declared; without N1 the native pads do not push). THE HAND PROBLEM
is C2's own named UNDECIDABLE (`DERIVATION.md` section 2): hold-at-height
for the REAL creature is UNDECIDABLE until the adopted assembly's hand/arm
mass model is runtime-qualified (TC-3 drive-table re-declaration from the
assembly's OWN sealed sources + TC-8 measured ports) or the solver treatment
of the mass ratio changes — the 0.049 kg hand cannot statically support the
10.037998 kg line through this solver. Additionally the friction bench
(the Captain's item: hold closure at scene n=3 sits at the corrected
mid-band threshold 0.5468840727038888 standard-g / 0.5470708910000001
record-g, UNMEASURED for the pair) and the mass-lineage decision (gap 9).

---

## C3 — CONTROLLED DESCEND

**Record state: ABSENT.** No descent run exists in any class. The sealed
ascent/hold/release laws and the G06 brake segment define the descent LAW
(`DERIVATION.md` section 3); K04's split law ("evaluate climb, hold and
descend separately"; "an ascent success cannot stand in for controlled
descent") is explicitly NOT closed by the landing card
(`landing-impl/EVIDENCE.md` section 5, sha256 `67278cbffab956ea1c6e9180d5d6
f87e759f8f53dc542a8e514caa0b1896b186`). K02 fenced the transfer phase
(P6 FENCED_NOT_RUN).

### C3.1 Entry conditions

- E1: the C2 exit X1 — at a declared facet, at the hold2 class state, the
  descend intent declared through the U05 seam.
- E2: THE DIRECTION LAW: controlled descent closes EXACTLY where the hold
  law closes and fails exactly where it fails — the entry (reading, n) must
  satisfy the same stage-B static row as the hold; there is NO separate
  descent law in the sealed evidence, and this contract declines to invent
  one.
- E3: the brake template declared BEFORE the run: the G06 brake segment is
  the sealed metering template (10 ticks x 0.05 m/s = full v_climb shed,
  ending v=0, then hover); metered descent at v_d = 0.5 m/s gives per-tick
  climb channel = m_share*(g*DT - 0.0025) = 0.09542750000000001 N*s at the
  band_mid share — still gravity-cancel dominated; the channel goes negative
  (net braking below weight) only when the schedule sheds > g*DT = 0.04905
  m/s per tick.

### C3.2 Exit conditions

- X1 METERED ARRIVAL: the hold2/attach state at the LOWER facet (the stage-B
  law re-armed at the lower facet), the descent rate profile inside the
  brake template for the declared window, the energy account closed (the PE
  paid back into the declared account, never vanished).
- X2 RELEASE (the certified failure arm, not a descent credit): the free-fall
  identity class — an observed free-fall release is the failure arm of
  descent, never a descent credit (K01 R3 law). The landing phase consumes
  the released body under the landing card's own contract.
- X3: T1/T2/T4/T5 as in C1.2 (slip-stop, undeclared release, integrity,
  horizon).

### C3.3 State variables

The C1.3 set with v_z SIGNED (descent direction explicit), the remaining
height to the target facet, the brake-template schedule position, the PE
payback account, and the release discriminator armed (the G07 identities
above are the expected values if the release arm fires).

### C3.4 Physics law

Reverse load path: the per-tick support law is direction-blind in impulse
balance — descending, gravity drives and the SAME friction law holds the
weight while the climb channel meters the rate. Release is separated from
descent by exact identities (gravity work == KE gain == 19.320355586443497 /
19.320355586289068 J at the sealed 40-tick scene fall; terminal speed
1.9620000000000002 m/s; the two CCD facet contacts are recorded, never
support; no impact model was claimed at K02 — the impact/landing account is
the landing card's, certified at fixture class).

### C3.5 Interface to the certified phases

- Upstream: the C2 boundary law (C2.5).
- Downstream: the arrival exit re-arms the certified static/hold law (K02
  class); the release exit hands to the certified landing line (#324,
  fixture class: first floor contact [61,60,61] inside the declared window
  {59,60,61}; nonpenetrating worst gap +3.15e-12 m; impact jn
  9.847/10.011/10.007 N*s identity-bounded; at rest settle 82, rest window
  60/60, worst |v| 5.93e-18 m/s, restitution 0.0; energy accounted to rest,
  destination closures <= 5.33e-15 J). The landing is a declared 0.6 x 0.6 m
  ground-plane fixture with NAMED placeholder mu — the full-body landing
  from a real release height is a NAMED GAP the landing card itself
  declares; this contract does not inherit past it. No reset, no snap, no
  creep erase at the arrival or release boundaries.

### C3.6 The honest dependency statement

C3's PHYSICS depends on DEP-N and DEP-P exactly as C1.6/C2.6 (the metering
channel is the same press-sustained friction law). Additionally: the K04
split evaluation (per-phase metrics, failures visible) is a hard exit
obligation — an ascent success cannot stand in for controlled descent; the
phase-extractor precedent is G07's keyed per-phase extractor; the friction
bench (the Captain's item) and the mass-lineage decision (gap 9) as in C2.

---

## C4 — RESUME-GROUND

**Record state: ABSENT — the largest unowned phase in the goal text**
(`MATRIX.md` section 1.10: zero records, zero board events, no lane). The
merged demonstration line ends at SUPPORTED LANDING. Everything in this
contract is specification, authored by this lane, owned by nobody until the
Lieutenant dispatches it.

### C4.1 Entry conditions

- E1: the landing terminal state — at rest on the ground (the landing
  card's terminal class: at rest, restitution 0.0), arrived at by declared
  release + landing physics; OR a declared non-climb ground state under the
  walk line's own initial-state law (for scoped first runs that compose
  resume AFTER a declared landing fixture state).
- E2: the walk intent re-declared through the U05 seam; the K06 arbitration
  precondition holds: a transition is lawful iff the post-transition support
  row is WITHIN — for resume-ground that is the WALK line's support law
  (the four front pads, min contact count 4, at the declared walk interval),
  evaluated at the transition tick.
- E3: NO STALE GRIP: the release removed the press EXACTLY (W_press == 0.0 J
  every release tick; the G07 identity); any residual trunk contact at the
  resume boundary is declared contact, not a hidden anchor (C22: no
  snap/teleport, unaccounted impulse, stale grip or lost command at
  transitions).

### C4.2 Exit conditions

- X1 SUSTAINED WALK: the certified walk line's own gates hold for the
  declared window (the sealed R1 stride law 0.2 driving com_v; the stop
  floor semantics available; the velocity envelope V = 2.977443609022557
  m/s and the cross-build non-regression margin 0.03103119967715015 m/s as
  the declared walking-line envelopes carried until a climbing re-derivation
  supersedes them by a recorded decision — K01 E6).
- X2 FAILURE: the walk line's own failure modes plus the K07 boundary
  classes; the failure path routes through X03 ("the player can continue
  after failure by the approved recovery action or visible restart; do not
  require a new get-up skill unless explicitly selected" — registry row X03,
  prereqs W09/X02, limit C13).

### C4.3 State variables

The certified walking interface (`policy_observation_interface v2`, dim 80,
OBS_SCHEMA_VERSION 2, float32, privileged_forbidden, history 0; FIELDS[:64]
the frozen v1 width) — NOT re-declared here; plus the climb-side channels
at their declared absent/zero fill (channels k >= n_channels UNAVAILABLE
with declared fill 0.0; obs_mask_mean / obs_frac_avail report availability),
the ground contact set (the four front pads; foot forces as the walk line
actually produces them), and the intent echo slots. The body is the walk
line's body — WHICH IS THE NAMED PROBLEM: the certified walk line is the
declared gait-walker hind-pad surrogate with prescribed (fixed 0.25) front
pad forces, and hands/feet do NOT transmit the walking forces anywhere in
it (MATRIX 1.12, sealed-byte verified; the walk-physicalization lane owns
the F7 remediation, phase-1 design + prereg DRAFT state,
`walk-physicalization/EVIDENCE.md` sha256
`b4ec73efbf4d84107679b0eab489de91bc81302cbfa03476c327653156b87230`).

### C4.4 Physics law

The certified walk line's law (the W10 trace class: applied_cmd drives
com_v; the FB2 clean control = stride-law deviation + velocity recursion),
composed with the landing terminal state's ground support (the floor's
declared anchor reaction carries the support — the landing card's certified
account). The resume transition itself has NO law in records: this contract
declares the composition law only (E1-E3, X1), and the first run's prereg
must freeze the transition window, the arbitration tick, and the per-phase
evidence keys before any execution.

### C4.5 Interface to the certified phases

- Upstream: the landing card's terminal (fixture class) or the walk line's
  own declared ground state. The landing -> resume boundary is the SAME
  anti-assist boundary as every other phase boundary: no reset, no teleport,
  no pose-set; the state-chain head must be bit-continuous across the
  boundary; the boundary delivery passes the seam gates.
- Downstream: the certified walk line (W-tier complete; W10 merged PR #311
  @ a07ac859, review PASS) and, for the full loop, the K08 composition
  ("player approaches, attaches, ascends, holds, descends, releases, resumes
  walking in one session") whose success predicate is the envelope law on
  every climb tick and whose honest negative stands today: the loop CANNOT
  close for the scene line under current evidence (gap 9).

### C4.6 The honest dependency statement

C4's PHYSICS depends on DEP-N and DEP-P TRANSITIVELY through the chain it
consumes: the landing it resumes from is fed by a release that removes the
press channel exactly — if the press channel is fixture-declared (DEP-P
ABSENT), the release/landing/resume chain is fixture-class end to end; if
any native hand/trunk contact persists into the resume window, its forces
exist only under DEP-N (N1 run published; state: prereg draft authored,
NOT RUN). DIRECT dependencies: the walk physicalization (the F7
hands/feet-force-transmission remediation — without it the resumed walk is
the prescribed-force surrogate, and the goal's "hands and feet transmit the
forces" is NOT met by this phase), the landing->walk body identity (the
landing body is the 3-pad fixture body; the walk line is the 10.037998 kg
gait-walker surrogate; the mass-lineage decision gap 9 owns whether these
are one body), the F06 terrain law for any non-flat resume (the certified
walk is FLAT-ONLY; the gentle-grade route class <= 2.6% is the certified
uneven envelope; obstacle mount is a MEASURED NEGATIVE), and X03 for the
failure path. Resume-ground has NO owner until the Lieutenant dispatches
one; this lane claims authorship only.

---

## C5. THE COMPOSED-LOOP BOUNDARY LAW (applies to ALL FOUR contracts)

This section is the K02 anti-assist law applied BETWEEN phases — the
interface law every first climb-phase run must carry:

1. NO BOUNDARY RESET: in a composed session, phase transitions are solver
   state evolution only. The reset machinery (any state write, re-press,
   contact restoration, pose-set, creep erase, force restore, teleport,
   hidden anchor) is lawful ONLY at the declared terminal/reset boundary
   OUTSIDE the composed episode (K02 D3/D4; F4 assist-smuggling extends to
   every inter-phase boundary).
2. BIT-CONTINUOUS STATE-CHAIN: each phase's entry state is the previous
   phase's exit state — the state-chain head identity (the K02 D1
   determinism class: two fresh processes, identical boundary state; any
   nonzero delta at a phase boundary is a determinism falsifier hit, not
   noise).
3. THE SEAM GOVERNMENT EVERYTHING: every boundary delivery (setup telemetry,
   phase transition keys, intent deliveries) passes the declared seam gates;
   the x_* namespace refused (`named_absent_occupied`); the privileged
   registry empty (K01 1.4).
4. INTENTS ONLY AT THE COMMAND BOUNDARY: the only climb-specific commands
   are the U05 climb/let-go intents (versioned semantics) at the existing
   command boundary; K06 arbitration owns every transition precondition
   (lawful iff the post-transition support row is WITHIN; the honest slip is
   the refusal mode — never a snap); "no automatic snap-to-tree" verbatim.
5. ACCOUNTS NEVER RESET MID-SESSION: reward, energy, ledger identities and
   success metrics are continuous across phase boundaries within a session;
   reset operations never enter any account (K02 D4).
6. FAILURES PRESERVED AT BOUNDARIES: a slip-stop, an undeclared release, an
   integrity refusal or a horizon end at any phase is recorded with its
   phase, seed and tick; no boundary may reclassify a termination as a
   transition (C13: no concealed reset; failures visible per K04).

## C6. NOT-CLAIMS (maximum form; binding on every reading of this file)

- NO climb, hold-at-height, descend or resume-ground behavior exists,
  is trained, is integrated, or is qualified. All four are ZERO-RECORD
  phases; this document authors contracts for them and nothing else.
- NO corridor arithmetic in this file demonstrates a capability: every
  threshold is a CONDITIONAL-CALCULATION under A1-A7 of DECLARED inputs
  (per-reading mass, declared contact count, declared 60 N press ceiling,
  declared pad fixtures, PLACEHOLDER friction, stated law forms, declared
  screening band [0.3, 1.0]).
- NO claim that n=4 closes, opens the corridor, or is the lawful ascent
  shape: FEASIBILITY CANDIDATE, five unmet demonstrations, declaration a
  separate decision (K01 F7).
- NO claim that the fixture-class certifications (G06 transfers, K02
  hold/release, the landing) compose into a playable climb; each carries its
  own objective-line disclaimer in its own receipt, preserved verbatim
  upstream.
- NO claim about DEP-N or DEP-P landing: the N1 draft is authored, NOT RUN;
  the press channel is ABSENT (TC-8 0/8). Both are named dependencies, not
  achievements.
- NO training authorization: master law 0.4 (NO TRAINING RUN until a
  qualified grasp configuration exists; the seven prerequisites); the
  training gate = the grasp chain + P04 alone (board record).
- NO mass-lineage resolution: the reserved decision stays open; corridor
  arithmetic is NOT a lineage-selection input; every threshold is
  per-reading.
- NO friction resolution: monkey-bark UNMEASURED; the 0.6/0.6 trunk pin is
  an UNEVIDENCED-PLACEHOLDER; the 0.41 is the human-textile analogue for
  band arithmetic ONLY; the friction bench is the CAPTAIN's item.
- NO resume-ground ownership: this lane authored the contract; no card, no
  lane, no run exists for it.
- THE SPEC-EQUALS-SKILL LAW: authoring, approving, or committing these
  documents trains nothing, qualifies no physics, and completes no playable
  behavior; "DEMONSTRATED IMPOSSIBILITY CAN CLOSE AN INVESTIGATION, BUT IT
  CANNOT COMPLETE THE PLAYABLE-MONKEY GOAL".
