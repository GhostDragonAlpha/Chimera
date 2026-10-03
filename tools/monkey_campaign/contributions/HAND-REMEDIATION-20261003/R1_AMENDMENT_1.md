# R1 AMENDMENT-1 — the measured macaque pad-stiffness upgrade to VPL-1 (pre-run; DRAFT for the Lieutenant's pin)

- Lane: `E:/ChimeraWork/monkey-coordination/hand-remediation/` (owner
  `wk-hand-remediation`; NO_WORKTREES honored; NO runs, NO code shipped, NO
  sealed byte edited in this phase).
- Law of amendments: the pinned prereg bytes
  (`PREREGISTRATION_R1_PAD_LAYER.md`, commit
  `4def67e400953e8c4b833ce04345f75426a6180d`, blob sha
  `9213bf7d91ed9a6e6b2c5bbddc05d5ee36db63c600dfce42b559632f6f565da9`) are
  NEVER edited. This document is a NEW pinned amendment; it is lawful ONLY
  because it is authored and pinned PRE-RUN (the digit-scan has not returned;
  no R1 result exists anywhere). The readiness file `R1_IMPLEMENTATION_READINESS.md`
  (sha `f73d69a8de6cb83d15b412acc127ec925c8e81b1f9cc19689118a7ab8f87ea09`)
  stands; section 6 lists its implementation delta.
- Execution gate UNCHANGED: R1 stage 1 runs ONLY on the Lieutenant's explicit
  release AFTER the digit-scan result is on record.

## 0. STEP 0 — independent source verification (performed by this lane; PASS)

Fetched and read: PMC4403516 (https://pmc.ncbi.nlm.nih.gov/articles/PMC4403516/),
Kumar, Liu, Schloerb & Srinivasan, "Viscoelastic Characterization of the
Primate Finger Pad In Vivo by Microstep Indentation and Three-Dimensional
Finite Element Models for Tactile Sensation Studies," ASME J. Biomech. Eng.
137(6):061002, 2015, DOI 10.1115/1.4029985. Verified against the collaborator
citation, with the paper's own sentences:

| claim | verdict | paper text (quoted) |
|---|---|---|
| ONE male rhesus macaque, 9.5 kg | VERIFIED | "The animal used for the experiments was a pair-housed, intact male rhesus macaque, weighing 9.5 kg" (also ~7.5 yr old). Nomenclature note, recorded honestly: the fetched text says "rhesus macaque" and does not spell the binomial; Macaca mulatta is the standard binomial for the rhesus macaque — and is the SAME species as the hybrid hand's constraint lineage (the Limblab `monkeyArm_current.osim`). Subject is n=1: every derived use below carries that label. |
| five finger pads; 86 usable force curves | VERIFIED | "curve fitting was done for all 86 independent force curves (obtained by our experiments across four different indentation depths and across five fingers)" (thumb, index, middle, ring, little; 19 trials x 4 fingers + 10 index = 86). |
| effective quasi-static stiffness 0.120 mN/um = 120 N/m | VERIFIED, with exact meaning | "A0 was found to vary linearly with depth with mean stiffness of 0.120 mN/um." Meaning: the MEAN of the per-curve linear quasi-static (A0) stiffness fit across all five pads and four depths — a per-pad-equivalent linear spring rate. 0.120e-3 N / 1e-6 m = 120.0 N/m exactly. Per-pad/per-finger breakdowns were not transcribed at this stop (available for a follow-up transcription pass under the cheng_tables discipline if the Lieutenant wants them). |
| relaxation constants 2.279 s, 0.149 s | VERIFIED | "The mean decay constant t1 was found to be 2.279±0.233 s and t2 = 0.149±0.022 s." |
| indentation envelope 200-800 um | VERIFIED | "Static indentations were performed at depths of 200 um, 400 um, 600 um, and 800 um"; "our given indentation ranges (200-800 um)". |
| model class: layered viscoelastic FE | VERIFIED | 3-D multilayer linearly viscoelastic FE models (ADINA) on realistic primate fingertip geometry; homogeneous-viscoelastic and multilayer (elastic epidermis + viscoelastic core) versions; two-term Prony relaxation. |

The measured citation ENTERS the evidence chain with this verification
record. Had any number failed, the amendment would have died and the finding
been recorded instead.

## 1. THE UPGRADE — k: synthetic prior -> measured-derived, with the conversion explicit

### 1.1 Declared contact-patch area A (from the mesh geometry; lane-dev arithmetic, deterministic)

The frozen patch rule (normal half-space test `n_v . a_B > 0`) splits a
roughly tubular distal bone into two half-area patches; the DECLARED estimate
is the half-space area A = A_total / 2 per covered body. A_total computed
from the vendor STLs at scale s = 0.5384048132470733 (triangle-area sums;
vendor files unmodified; per-triangle exact arithmetic):

| body | A_total (scaled) | declared A_pad = A_total/2 |
|---|---|---|
| distal_thumb | 1.032099e-4 m^2 | **5.160493e-5 m^2** |
| distph2 | 6.581194e-5 m^2 | 3.290597e-5 m^2 |
| distph3 | 7.691615e-5 m^2 | 3.845808e-5 m^2 |
| distph4 | 7.099076e-5 m^2 | 3.549538e-5 m^2 |
| distph5 | 7.045877e-5 m^2 | 3.522939e-5 m^2 |

Class-representative for the single frozen k: the THUMB pad
(`distal_thumb`, A = 5.160493e-5 m^2) — the dominant fold body (3,298 of the
receipt-verified tip-fold events) and one of the paper's measured pads.
The stage-1 run RECORDS each body's actual mask patch area as a validation
column (declared expectation: within 2x of the estimate above; outside ->
FINDING, never a re-tune).

### 1.2 The conversion (explicit arithmetic)

Winkler form: `p = k * (u / t)`; over patch area A the pad's spring rate is
`F/u = k * A / t`. Setting this equal to the measured `K_eff = 120.0 N/m`:

    k = K_eff * t / A = 120.0 * 2.0e-3 / 5.160493e-5 = 4650.718448799368 Pa

FROZEN VALUE: `k = 4650.718448799368 Pa`, declared as the exact formula
`K_eff * t / A_thumb` over the three pinned constants (K_eff = 120.0 N/m,
t = 2.0e-3 m, A_thumb = 5.160493e-5 m^2), so no rounding ambiguity exists.

### 1.3 The plainly-stated comparison and its direction

- The synthetic prior (1.5e5 Pa, declared human-pulp ORDER) was **~32.25x
  STIFFER** than the measured-derived value — 1.5 orders of magnitude, not
  one. The change is DOWNWARD, pre-run.
- Stage 1 (collision geometry) is UNCHANGED: the admission window
  (pi_c, 4.0e-3] m, t, u_max, the patch rule and every bone-level class are
  untouched; k enters no geometric predicate.
- Stages 2-3 (capacity/forces): the force columns DROP by the same ~32x.
  Hard consequence, stated plainly: at the window edge the pad transmits
  `F = K_eff * t = 0.24 N` per pad (digits: `k * A_body / ... ` per-body
  maxima 0.153-0.178 N) — **2.5 orders below the declared 60 N/channel
  fixture press and ~150x below the ~36-40 N frontier capacities**. The
  measured-stiffness pad is therefore NOT a support element at the declared
  operating point: it is a contact-geometry layer, and support must route
  through the bones and the press channel — which remains ABSENT (TC-8 0/8,
  x_press ABSENT, unchanged by this amendment). This makes R1 HARDER to ride
  to any grasp-capacity claim: the force stage now EXPOSES the press-channel
  gap instead of hiding it behind a stiff synthetic — which strengthens the
  anti-tuning argument (a post-run softening would have done the opposite).
- Mapping idealization, named: the Winkler-over-declared-A mapping is a
  MODEL MAPPING of the paper's measured spring rate, not the paper's layered
  FE class. A real confined, layered, curved pad is stiffer than a free
  Winkler column of equal A and t, so the derived k is the SOFTER reading;
  the capacity stage's force columns are consequently lower bounds under the
  declared mapping, and they remain DECLARED-MODEL-FORCE (CONDITIONAL-
  CALCULATION), never a capacity claim.
- Class-wide application, declared: F-2 stays ONE constant applied to all
  five pads; the digits' implied spring rates are `k * A_body / t` =
  76.5 / 89.3 / 82.5 / 82.0 N/m (distph2/3/4/5) — 0.64-0.76x of the measured
  120 N/m mean. Per-body `k_body = K_eff * t / A_body` was DECLINED to keep
  F-2 a single frozen constant; the alternative is recorded here, not hidden.
- Context, no action: the paper's 9.5 kg animal sits between the declared
  mass band (5.4/6.15/6.9 kg) and the certified 10.037998 kg scene line; the
  mass-lineage reserved decision stays open and untouched.

## 2. ENVELOPE SCOPING — measured-anchored vs declared-extrapolated

- MEASURED-ANCHORED band: pad indentation u in (0, 0.8e-3] m (the paper's
  200-800 um static protocol, four depths, 86 curves).
- DECLARED-EXTRAPOLATED band: u in (0.8e-3, 2.0e-3] m — linear-Winkler
  extrapolation to at most 2.5x the maximum measured depth. The paper
  validates IN BAND only; beyond-band linearity is a DECLARED IDEALIZATION,
  named here and in every receipt (per-row column: `measured_anchored`
  true/false).
- Fold-row coverage at q_c (receipt-verified): of the 954 TIP_DEEP rows,
  **646 rows** convert to u <= 0.8 mm (measured-anchored) and **308 rows**
  land in the extrapolated band (u up to 1.673e-3 m). Every stage-1 receipt
  splits its conversion counts on this column; P1's per-row evidence is
  thereby labeled measured-anchored vs extrapolated, never merged.
- t = 2.0e-3 m is UNCHANGED: the paper characterizes indentation behavior,
  not our layer's thickness; no paper number overrides the anatomy-proportion
  declaration, and none is invented to do so.

## 3. VISCOELASTIC CONSTANTS — NAMED-NOT-MODELED

- Recorded values (paper-quoted): t1 = 2.279±0.233 s, t2 = 0.149±0.022 s,
  two-term Prony, multilayer (elastic epidermis + viscoelastic core), ADINA.
- VPL-1 remains QUASI-STATIC ELASTIC. The timescale argument, explicit: the
  scene tick is DT = jn/60 = 0.3/60 = 5.0e-3 s; t2 = 29.8 ticks, t1 = 455.8
  ticks. Fast per-tick loading responds near the INSTANTANEOUS (stiffer)
  modulus; multi-second holds relax toward the SOFTER quasi-static value the
  A0 fit represents. The declared force columns are therefore the
  soft/relaxed-bound reading; the instantaneous bound is higher by the Prony
  modulus split — WHICH THE PAPER REPORTS BUT THIS LANE HAS NOT TRANSCRIBED
  (named absence; extractable by a follow-up transcription pass).
- Modeling proposal, DECLINED at this amendment: adding the two-term Prony
  multiplier is cheap arithmetically but changes the model class (time-history
  force columns interacting with the per-tick G04 accounting) — it gets its
  own declaration at stage 3 if the Lieutenant wants the instantaneous-bound
  reading. Until then: NAMED-NOT-MODELED, with the bracket above stated in
  every receipt.

## 4. THE ADDED CONTROL — C10 (extends the battery; stage 1 runs it)

- C10 MEASURED-STIFFNESS IDENTITY (in-band): at the paper's four measured
  depths the constructed pad force column must reproduce
  `F = K_eff * u` exactly — 0.024 / 0.048 / 0.072 / 0.096 N at
  200 / 400 / 600 / 800 um (equivalently `F(u)/u = 120.0 N/m` at all four).
  Construction: the C6 pad-geometry case evaluated at the four depths via
  `pad_force_column` (now active for the battery only). This validates the
  CONVERSION MAPPING in-band; it does NOT validate the paper's FE model
  itself (that model class is NAMED-NOT-MODELED, section 3). The control
  table extension appends C10 to `control_input_table_vpl1.json` with its
  frozen constructed truths; the light gate becomes C1-C10; any C10 miss ->
  `INSTRUMENT_INVALID_IN_SITU`.

## 5. THE ANTI-TUNING STATEMENT

- This amendment is PRE-RUN: the digit-scan has NOT returned; no R1 stage has
  run; no R1 result of any kind exists anywhere in the campaign. Nothing is
  adjusted to obtain a result, because no result is in sight to adjust to.
- MEASURED > SYNTHETIC is the goal's own quantity law: the upgrade replaces a
  declared-synthetic placeholder (F-2, human-pulp order) with a
  species-matched, in-vivo, independently verified measurement — in the
  DOWNWARD direction, which reduces the pad's force columns and cannot make
  any pass easier to manufacture.
- The upgrade path was DECLARED IN THE PINNED PREREG ITSELF (F-2: "the macaque
  pad stiffness is UNMEASURED (acquisition-gap class)"; the design's "upgrade
  path: measured pad/phalanx acquisition"). The acquisition arrived; the swap
  is the declared path executing, not a new permission.
- FALSIFIER (unchanged and restated): ANY post-run change request to a frozen
  value — measured or synthetic — is a FINDING routed to the Lieutenant,
  never an edit. This amendment is lawful ONLY pre-run; after the first R1
  stage-1 receipt exists, this document's numbers are as frozen as the
  prereg's.

## 6. WHAT DOES NOT CHANGE (and the readiness delta)

- UNCHANGED: t = 2.0e-3 m; u_max = 2.0e-3 m; the admission window
  (pi_c, 4.0e-3] m; the patch rule and sign table; the post-hoc evaluation
  law; every bone-level class and the exclusions ledger; the trunk, joint
  limits, placement families; TC-8 = 0/8; the C17 non-identity; the honest
  scope (cause 1 ONLY); the named-unscanned list; the execution gate.
- Readiness delta (vs `R1_IMPLEMENTATION_READINESS.md`
  `f73d69a8...`, which otherwise stands): (i) `PAD_CONSTANTS` pins the three
  conversion constants and the formula value of k in place of the 1.5e5
  literal; (ii) `pad_force_column` activates for the C10 battery case at
  stage 1 (recording only); (iii) `light_gate_vpl1` extends to C10; (iv) the
  receipt gains the `measured_anchored` per-row column and the conversion
  split counts; (v) the input gate adds THIS amendment's pinned sha.

## 7. Governance

Authored by wk-hand-remediation; DRAFT for the Lieutenant's pin via the one
publication owner (committed ALONE, pre-run); the implementation package
seals against the prereg commit WITH this amendment pinned alongside. All
CPU execution stays through the canonical runner; hashes land in the lane
EVIDENCE.md. No merge/review authority claimed; Sergeant review requested
through the Lieutenant; author self-review certifies nothing.
