# R1 STAGE-3 PREREGISTRATION (DRAFT) — contact forces: the per-tick pad-force identity, the mu=0 non-closing control, and the per-tick signed instrumentation class

Status: DRAFT authored by `wk-hand-remediation` for the Lieutenant's pin
(separate-first; the committed bytes are the freeze). PRE-RUN of the
stage-3 class: no stage-3 result exists. The run executes on the
Lieutenant's explicit release AFTER this pin; the package seals against
the pin commit. NO_WORKTREES honored; all CPU through the canonical
runner. Authored UNDER THE CORRECTED RULES: the absorbed band is an
explicit predicted class; every falsifier's teeth are stated against the
FULL outcome space; every cited quantity names its instrument-quantity
code path; execution narratives cite only this lane's own records.

## 0. Position and inputs (each names its artifact and code path)

- Ladder position: stage 3 of the Captain's declared order (collision
  geometry DONE -> actuator capacity DONE -> CONTACT FORCES -> supported
  grasp -> runtime evidence).
- The frozen survivor set (354 = 348 PAD_CONTACT + 6 PAD_ABSORBED):
  raised-cap receipt `4df5f480...` (the stage-2 input; reused, never
  re-derived).
- VPL-1-FORCE (amendment-1, frozen): p = k*(u/t); F = p*A;
  k = K_eff*t/A_thumb = 4650.718448799368 Pa;
  K_eff = 120.0 N/m (Kumar/Liu/Schloerb/Srinivasan 2015, verified);
  A_thumb = 5.160493e-05 m^2.
- The tick law: DT = jn/60 = 0.3/60 = 5.0e-3 s (the sealed scene tick,
  DERIVATION A3/A6 conventions); per-tick contact impulse
  J_tick = F * DT (signed along the declared inward radial).
- The mu=0 law form: static closure P_req = W/(n*mu) (A6) — at mu = 0 the
  closure diverges: the NON-CLOSING class is a law-form consequence; at
  the declared placeholder mu_s = 0.6 the same law closes (the positive
  control). Friction stays PLACEHOLDER-labeled (A5); the 36 N figure
  remains a simulated capacity conditional on model + mu = 0.6.
- Quantity code paths (the depth-basis law): u per tick from the FROZEN
  schedule (section 2, a frozen table — never from a result); F from
  `vpl1_pad.pad_force_column(u, A)`; impulse from the tick law above;
  d quantities keep their names (`d_receipt` first-proven vs
  `d_covered_max` full-scan — never conflated); the survivor/contact
  geometry from the raised-cap receipt's survivor records (o, u, witness
  via `pad_scan_verts`).

## 1. THE RUN CLASS (what executes)

`stage3_contact_forces`: a CONSTRUCTED, ANALYTIC, ticked contact sequence
per audited survivor — NO physical-solver integration is claimed or
attempted (the solver-side per-tick identity is the runtime stage's). The
declared tick schedule (frozen table in the package, identical for every
audited survivor): N_TICKS = 40; u(t) linear from 0 to the survivor's
recorded pad_u over ticks 1-20, held at pad_u over ticks 21-40; the
absorbed-class survivors (pad_u = 0) hold u = 0 across all 40 ticks (the
explicit zero-force class). Per tick, the pipeline emits SIGNED records:
F_vector (along the declared inward radial at the contact vertex),
J_tick = F*DT (signed), cumulative impulse, and the identity residual
r_tick = F_tick*DT - J_tick_recorded (which is identically zero by
construction — see the prediction form below).

## 2. THE OUTCOME SPACE (declared before the run; counts close)

Per audited survivor, the tick sequence yields EXACTLY ONE of:
- `IDENTITY_CLOSED` — all 40 per-tick residuals <= the declared tolerance
  (1e-12 relative) AND the cumulative identity holds AND the sign record
  shows no reversal (the force stays on the declared inward radial).
- `IDENTITY_MISMATCH` — any residual above tolerance, any cumulative
  mismatch, or any sign reversal (a reversal is a REAL event class: the
  instrumentation must be able to show it, never absorb it).
- `ZERO_FORCE_CLASS` — the absorbed-band survivors (pad_u = 0): all 40
  ticks carry F = 0 and J = 0 (a REAL class, predicted as such, never
  merged into IDENTITY_CLOSED).
PLUS the mu=0 control outcome (per the constructed control, section 3):
- `NON_CLOSING_AT_MU0` (expected — the supported prediction);
- `CLOSED_AT_MU0` (would FALSIFY the law-form implementation).
COVERAGE ARITHMETIC: the survivor classes sum to 354 exactly; the control
outcome is exactly one of the two named classes; any unnamed state is a
refusal (`stage3_outcome_space_broken`).

## 3. THE FROZEN PREDICTIONS (teeth against the full outcome space)

- S3-P1 IDENTITY: all 348 PAD_CONTACT survivors classify
  `IDENTITY_CLOSED`. TEETH: any `IDENTITY_MISMATCH` (a per-tick residual
  above tolerance, a cumulative mismatch, or a signed reversal) — a
  RESULT routed, never absorbed; the tick index and the signed residual
  are recorded per violation.
- S3-P2 THE ABSORBED BAND: exactly 6 survivors classify
  `ZERO_FORCE_CLASS` (6 q_c + 0 q_zero — the raised-cap basis), with all
  40 ticks F = 0 and J = 0. TEETH: any nonzero tick force or impulse on a
  u = 0 survivor; the 348/6 split not reproducing the receipt; an
  absorbed survivor scored in any other class.
- S3-P3 THE MU=0 NON-CLOSING CONTROL: the constructed mu = 0 case yields
  `NON_CLOSING_AT_MU0`. TEETH: `CLOSED_AT_MU0` falsifies the law-form
  implementation (instrument invalid, everything carries not).
- S3-P4 THE POSITIVE CONTROL (the bite-both-ways law): the same law form
  at the declared placeholder mu_s = 0.6 CLOSES for the declared W class
  (W = the measured scene weight share line, placeholder-labeled). TEETH:
  a non-closure at mu = 0.6 (the positive control failing = the law form
  implemented wrong).
- S3-P5 THE SIGN INSTRUMENTATION (the walk/pair lesson): the per-tick
  records are SIGNED (the force component along the declared inward
  radial carries its sign; the impulse carries its sign); the run
  includes one constructed REVERSAL case (a declared outward-pointing
  schedule) that MUST record a negative signed force and classify
  `IDENTITY_MISMATCH` on the sign check — proving the instrumentation can
  show a reversal, never absorb it. TEETH: the reversal case recording a
  nonnegative force or closing clean.

## 4. THE CONTROLS (constructed truths, frozen in the package table)

- C11 IDENTITY (the per-tick law): a survivor's declared schedule vs the
  identity residual — truths are the frozen schedule + the closed-form
  tick law (analytic, independent of the classification).
- C12 MU0 NON-CLOSING / C13 MU0.6 CLOSING (the law-form pair): truths are
  the A6 law forms at mu = 0 and mu = 0.6 (analytic).
- C14 REVERSAL (the sign class): the outward schedule (analytic).
- The stage-1 battery C1-C9 is NOT re-run (not exercised by this class);
  its certification rides on the stage-1/raised-cap records.

## 5. WHAT STAGE 3 DOES NOT CLAIM

Friction is PLACEHOLDER (A5); no monkey-bark value exists; no physical-
solver integration is claimed (the per-tick identity here is the declared
law form on constructed schedules; the solver-side identity is the
runtime stage's); the 36 N figure stays conditional on model + mu = 0.6;
the absorbed band carries no force and supports nothing; TC-8 = 0/8
stands; the same-hands finding stands. No stage-3 output may be phrased
as a hold or grasp result: the hold law is stage 4's, on its own gates.

## 6. EXECUTION AND CONVENTIONS

Gate: the Lieutenant pins THIS file (separate-first), then releases; the
package seals against the pin commit; run class `stage3_contact_forces`
with a receipt-level delta note; the survivor-set input pins the
raised-cap receipt bytes `4df5f480...`. SEAL-STORE LAW: the seal bytes
(manifest + patch) are captured into `seal-store/` at seal creation.
Slot discipline: slot 2 first, fallback slot 3; this lane's refusals left
no runner rows (the corrected record); other lanes' rows are never cited
as this lane's attempts. Anti-tuning: the schedule, tolerance, tick count,
and every constant above are frozen pre-run; post-run change requests are
FINDINGS, never edits. No merge/review authority claimed; Sergeant review
requested through the Lieutenant; author self-review certifies nothing.
