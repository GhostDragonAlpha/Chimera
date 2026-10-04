# CBP-PREREG-001-AMENDMENT-003 — E4 reclassified report-only; the spring-reaction basis recorded

Status: COMPLETE, UNPUBLISHED. Authored 2026-10-11 by the Lieutenant
(one-writer path). This is the scoped repair demanded by the fresh
endorsement verdict `CHANGES_REQUIRED` on AMENDMENT-002 (rev `1bf02538`,
PR #354 at `11ffcdfc`), whose single required item was repair 1g. ZERO runs
were executed before or by this amendment. `SCIENTIFIC_PREREGISTRATION.md`
(`0f62cbfa...`), AMENDMENT-001 (`2be48e44...`), AMENDMENT-002 (`1bf02538...`),
and the sealed fixture (`d7963115`, package `9102816d`) stand byte-unchanged.
This document supersedes ONLY AMENDMENT-002 §1 (the E4 restatement) and adds
one standing law. Everything else stands as reviewed.

Trigger of record: the endorsement review resolved the spring-force
subtlety AGAINST the amendment's basis sentence. The sealed attachment
kernel applies the 9 anchor reactions to the ARM as first-class forces
(`reactions[index] = -force`; `body_f[0] += total_force` — the endorsed P4
pair-sum identity's other half). The reviewer's closed-form derivation
about the pivot (the pivot reaction has zero moment about the pivot, so the
theta-ODE closes without it):

  `a_down = (m·r²/I)·g·cos²θ − (r·cosθ/I)·τ_spr + r·sinθ·θ̇²`,
  with I = 0.02424 kg·m², m·r²/I = 0.7426, r = 0.15 m, k_eff = 900 N/m.

The gravity term alone gives 7.282 m/s² < g. The premise "arm-COM downward
acceleration <= g" holds ONLY while the fall-assisting spring pull at the
arm stays under F\*(0) = 1.360 N (2.064 N at theta = ±0.35 rad) — total
effective stretch under ~1.51 mm. The sealed phase-A settled state is NOT
in that regime (arm at the lower limit, pad floored, per-anchor stretches
42.6/52.9/63.2 mm, total pull 47.6 N, stored spring PE 1.29 J ~ 1255x the
threshold energy), and the generic post-C2 mirrored configuration (pad
lagging below the anchors after the inelastic stop) produces multi-newton
pulls: 1 cm lag = 9.0 N = 2.2x g; 3 cm = 5.2x g arm-COM downward
acceleration. In a fresh post-event segment (d(0) = 0) the first checkpoint
can realize ~34 mm drop against a 12.26 mm free-fall-style bound — E4
would fire on LEGITIMATE sealed dynamics. That is the exact
guaranteed-false-negative class the repair process prohibits, introduced
through the omitted spring term, violating AMENDMENT-002's own L4. Review
evidence: `E:/ChimeraWork/monkey-coordination/sgt-cbp-amend2-endorsement-scratch/recompute_e4_premise.py`.

Fix choice: the reviewer's option (c) — RECLASSIFY E4 as REPORT-ONLY with
ledger adjudication. AMENDMENT-002's fix-choice had declined full deletion
because "a correct kinematic sanity bound has qualification value"; the
review has now PROVEN no correct non-vacuous kinematic upper bound is
derivable at useful tightness (a spring-envelope-based bound — the only
provable one — is vacuous by roughly two orders of magnitude), which
answers that rationale with evidence. The kinematic DATA is kept and
recorded; the kinematic GATE is not asserted anywhere; anomalous descent is
adjudicated by the instruments that can actually decide it.

---

## 1. E4 reclassified (supersedes AMENDMENT-002 §1 in its entirety)

- E4 (post-C2 kinematics — REPORT-ONLY, NON-GATING): per segment (segments
  delimited by the C2 window start, every recorded joint-limit event, and
  the C2 window end), the arm-COM and pad-COM cumulative vertical
  displacement trajectories from each segment-start state are RECORDED as
  measured data in the C2 report, with segment-start velocities. NO frozen
  kinematic upper bound is asserted on any of them, by this amendment or
  any prior text. A drop faster than the free-fall-style form is NOT a
  failure: it is the expected consequence of spring potential energy
  funding the descent, and its correctness instrument is E1 (the segment
  energy identity — the attachment term pays for it) plus E2 (event rows).
- The premise-regime boundary is RECORDED as a derivation, not a gate: the
  acceleration premise `a_down <= g` for the arm holds only while the
  fall-assisting spring pull is below F\*(theta) (F\*(0) = 1.360 N,
  F\*(±0.35 rad) = 2.064 N, from the closed form above); the sealed settled
  state (total pull ~47.6 N) and the generic post-event mirrored
  configuration sit far outside that regime, which is precisely why no
  kinematic bound is asserted.
- The named contradicting observations for kinematics remain exactly as
  already frozen: "upward COM motion inside the limits without a spring
  term to pay for it" (adjudicated via E1), and any report citing
  unconstrained/free-fall reference numbers as C2 predictions.
- No other E-clause changes: E1 (set-membership applicability), E2 (event
  rows), E3 (pivot invariance 1.0e-4 m), E5 (scoped monotonicity with the
  NOT-EVALUABLE branch), and E6 (labeled references) stand as reviewed.
  Recorded non-blocking observations from the review (not reopened, kept
  for the record): AMENDMENT-001 E6's reference pair is internally
  inconsistent (KE 0.3037 J vs 0.2573 J implied by its own 0.0328 m drop);
  the base prereg's P1 "final 0.2 s (1080-1199)" label is superseded by
  AMENDMENT-001 §4; the single-engagement picture is a bare-pendulum
  reference — the sealed passive settle generically yields multi-engagement
  spring-yank dynamics, and the empirical event count is what E2 records.

## 2. Standing law addition

- L7. An acceleration-premise derivation must account for EVERY force the
  sealed constraint graph applies to the gated body. Pivot-only basis
  sentences are the L1 class again; attachment reactions on a body are
  first-class forces via the P4 exact pair-sum identity, and they enter the
  moment balance about the pivot even when the pivot reaction itself does
  not.

## 3. Endorsement scope

G4 remains LOCKED for C2 until this amendment is pinned and published
through the one serialized publication owner and a fresh endorsement
verdict is recorded. The fresh review's scope is this document's §1-§2
only: the reclassification semantics (report-only, non-gating, no frozen
kinematic bound anywhere), the recorded premise-regime derivation, and L7.
All previously endorsed clauses stand. No gated run of any kind has been
submitted.
