# ASTRA stance closure — handoff

Base: `42c6f5db33541da8e50e2713752e42f6fc06dcbd`.
Branch: `astra/gait-capture`. Offline only. No protected build-file edits.

## 1. Falsifier table

| Item | Result |
|---|---|
| S1 imported FK reproduces every new rigid seed | PASS: max 4.866020254e-15 wu |
| S1 admissible new seeds at every sampled target | PASS: at least 2 |
| S1 geometric extension margin | Derived continuous floor 0.141938983 rad; sampled minimum 0.173619618 rad |
| S2 observed right-axis parity | +1, all paired leg intervals remain unchanged |
| S2 deliberately negated axis + swapped interval | PASS: full mesh discrepancy 0.0 wu |
| S2 no-ROM-swap ablation | Rejects a spatial endpoint by 16 degrees, as predicted |
| S3 old flat-seed ablation | FAIL: max/RMS 0.122037880750 / 0.024728394083 wu |
| S3 recommended inverse | PASS: max/RMS 9.873789293e-11 / 2.182060552e-11 wu; bound 0.028078200 |
| S3 full/subset mirror | PASS: exact |
| S4 synchronized left/right solves | PASS: position difference 1.868642267e-8 wu, angle difference 7.349214348e-9 rad |
| Full joint-path continuity | NOT CLOSED: worst sampled joint jump 2.381311797 rad |
| Pose periodicity | NOT CLOSED: return discrepancy 0.297065513 wu |
| Physical gait gate | CLOSED; sampled position closure does not certify contact or walking |

Both raw logs contain side/phase cohorts, worst samples and angles, clock,
capture and energy diagnostics. No gate tolerance was relaxed.

## 2. Files written

* `tools/gait_capture.py`: free-frame inverse, conditional ROM sign law,
  stable bounded refinement, side/gauge controls and decomposition output.
* `docs/THE_CAPTURE_LAW.md`: appended S1–S4 membranes, derivation, measurements,
  corrections to conflicting coordinator hypotheses, and the honesty ledger.
* `docs/THE_CAPTURE_INTEGRATION.md`: appended exact inverse, clamp and referee
  propagation contract; full gait remains disabled.
* `agent_logs/astra/stance_closure_baseline.txt`: preserved flat-seed ablation.
* `agent_logs/astra/stance_closure.txt`: recommended-law run.
* This handoff.

## 3. Falsified / corrected

The seed's old annulus imposes full-frame angle zero, independently of knee
ROM. At exact midstance it has positive 0.007502013 wu radial margin, not an
extension singularity. Across stance it accepts only offsets in
[-0.268014393,0.172516620] wu. Unavailable flat seeds do not prove unavailable
three-hinge poses. Allowing derived full-frame orientation closes the sampled
position defect with root drop zero and no skeleton changes.

The committed axes are hip/knee +X and ankle -X on BOTH sides. Paired ROMs are
identical and already spatially consistent. A genuine negated-axis convention
requires sign-swapped intervals, but that is a tested hypothetical control,
not grounds for changing this pack. The message's negated-axis diagnosis and
the audit's -147.89 knee extension do not match the canonical blob.

The worst baseline phase is 0.290909091 of the right stance interval and its
ankle is at -159.21 degrees. The histories differ because the sides begin
half a stride apart; their warm-start dictionaries are separate. Same-phase
controls agree. No ROM widening or weight repair is warranted by this defect.

The initial new-seed trial choosing the smallest residual produced 9.288e-14
max error and zero pose-return error. That apparent return was not accepted
as proof of a continuous path. The final algorithm prefers the closest
previous pose among numerically solved candidates and reports the remaining
jumps and nonperiodic return honestly.

An equal-phase test exposed `LinAlgError: Singular matrix` in the inherited
normal-equation refinement near a solved redundant pose. The final probe
stops at its declared 1e-10 numerical tolerance, solves an augmented least
squares system and uses inward boundary differences. The mirror is unchanged.

The old net full-frame angle statistic is |h+k+b|, not sum |q_i| and not a
weight-contamination metric. No geometric or contact finding is inferred
from that scalar alone.

## 4. Open items

Continuous periodic inverse-branch tracking, oriented/contacting LBS sole,
contact/impact/actuator budgets, lateral stability and coupled physical swing
clock. A sampled position pass is not permission to animate or certify a walk.
No live physics or visual score is claimed for this offline task.

## 5. Boundaries and commands

No master push, no force push, no engine calls, no binary/blob modifications.
`tools/gait_mirror.py` remains unchanged. Existing unrelated untracked files
were preserved. The inherited PR #5 was already merged; this task makes one
new PR on the same held branch.

From repository root (numpy + stdlib only):

```bash
OPENBLAS_NUM_THREADS=1 python tools/gait_capture.py --seed-law flat
OPENBLAS_NUM_THREADS=1 python tools/gait_capture.py --require-ready
```

Baseline exits 0 for successful report generation and prints foot FAIL.
Recommended run exits 2 as intended for the still-closed full readiness gate,
while printing foot PASS and all S1–S4 controls. The environment variable only
avoids BLAS thread overhead. Numerical constants in the inverse are computed
from the pack and target; there was no angle/height/ROM parameter sweep.
