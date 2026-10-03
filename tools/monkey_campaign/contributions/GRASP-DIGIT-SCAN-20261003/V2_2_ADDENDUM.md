# V2.2 ADDENDUM — concrete frozen parameters (authored BEFORE the v2.2 run)

Status: sub-ladder freeze under the COMMITTED prereg
(`655047b466f5d959e065252670bd275153a4d775`, bytes `e5bfa3cd...`, section 5
ladder law: "the declared next candidate is v2.2 (POSTURE VARIATION: cmc/mp
flexion scan within the certified ranges at the v2.1 placement solve ...),
again cheap-screened BEFORE any sweep"). The committed prereg authorizes
v2.2's execution and names its joints; THIS document freezes the concrete
grid before the run, same discipline as the v2.0 formulation. The v2.2 code
pins THIS file's sha and refuses on drift.

Trigger (observed, sealed): v2.1 job `f0da9bb122bb411f9acef57b650f674c`
PASSED — q_c PRIMARY 0 S0-survivors over the full 11,520-axis grid;
P1 FALSIFIED (0 survivors); P2 FALSIFIED (tip-deep share of reachable =
7,458/9,364 = 79.6% >= 50%, worse than v2.0's 66.3%); other postures not
run (the declared cap law). Ladder branch: v2.2.

## Frozen v2.2 parameters

- SCAN JOINTS (the prereg's named scope, nothing added): cmc_flexion x
  mp_flexion. All other joints at the sealed q_c(PRIMARY) values (wrist 0).
  The SEALED q_c point itself is NOT a grid point (it is v2.1's own
  evaluated and rejected posture; the scan explores the rest of the range).
- GRID VALUES: per joint, 5 values at certified-range fractions
  f in {0.05, 0.275, 0.5, 0.725, 0.95} of [lo, hi], computed FROM the parsed
  certified ranges AT RUN (no hardcoded ranges; a value outside the
  certified range is a refusal). 5 x 5 = 25 postures. Certified ranges
  (A05, verified 2026-10-03): cmc_flexion [-0.78, 0.7]; mp_flexion
  [-0.785398, 0.698132].
- AXIS GRID, stage 1 (coarse scan): theta = every 8th of 720 (90 values) x
  the v2.1 phi grid (8 values) x 2 mirrors = 1,440 axes per posture;
  25 x 1,440 = 36,000 candidates. Construction, two-contact solve (41-point
  bracketing pre-scan + 40 bisections, tau bracket +/-0.05 m), screens,
  caps, pad gate: IDENTICAL to sealed v2.1 (prereg section 5 law).
- STAGE 2 (refinement, hits only): any stage-1 posture with >= 1 S0-survivor
  is re-run at FULL resolution (720 theta x 8 phi x 2 mirror = 11,520 axes).
  At most the hitting postures; if none hit, stage 2 does not run.
- CAPS (unchanged): CAP_S1_PER_POSTURE = 96; cumulative S1 wall-clock budget
  2.5 h per job; s* bracket [0, 0.15] m; pad-orientation cos > 0 active at
  S1-survivor recording.
- DECLARED SCOPE LIMIT (honest): thumb-side joints only. The v2.1 rejection
  class "opposing digit crosses the solid" (distph2/distph3/distph4 proven
  events) is NOT addressed by cmc_flexion/mp_flexion; if a stage-2 survivor
  exists it must clear that class at S1 like any other; if the scan rejects
  everywhere, the class is named in the EXHAUSTED report as an unscanned
  DOF direction (a finding for the Captain, never a silent omission).

## Frozen predictions (falsifiers)

- V2.2-P1: at least one of the 25 scanned postures yields >= 1 S0-survivor
  at the coarse grid. FALSIFIED if all 25 reject (then stage 2 does not run
  and the ladder reaches EXHAUSTED).
- V2.2-P2: the best scanned posture's tip-deep share among reachable axes is
  < 50%. FALSIFIED if every reachable-majority posture sits >= 50%.
- PROGRAM LAW (committed prereg): if v2.2 also rejects with zero survivors,
  the candidate-family line is reported EXHAUSTED — the geometry option's
  answer at this anatomy/trunk: feasibility evidence of absence at the
  represented geometry under the declared families, NOT impossibility.

## Execution identity

- Code: `grasp_screen_v22.py` (imports the sealed v2.1 and v2.0 modules and
  the merged instrument, all unmodified). Package base: the prereg commit
  `655047b...`. Runner path identical; declared CPU envelope for the v2.2
  program <= 4 CPU-hour (stage-1 ~1.1 h measured-rate estimate + stage-2
  headroom); timeout 4 h per job; BUSY -> retry per NO_WORKTREES.
