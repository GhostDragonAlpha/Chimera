# R1 STAGE-4 PREREGISTRATION (DRAFT) — the supported-grasp rung at DECLARED-MODEL SCOPE: the G01 transfer law re-armed per the mass reading

Status: DRAFT authored by `wk-hand-remediation` for the Lieutenant's pin
(separate-first; the committed bytes are the freeze). PRE-RUN of the
stage-4 class: no stage-4 result exists. The run executes on the
Lieutenant's explicit release AFTER this pin; the package seals against
the pin commit; the seal bytes are captured into `seal-store/` at seal
creation. NO_WORKTREES honored; all CPU through the canonical runner.

## 0. THE SCOPE THIS PREREG FREEZES, AND WHY (the Lieutenant's question, answered first)

Stage 4 freezes the **DECLARED-MODEL SCOPE**: the G01 hold/transfer law
forms evaluated as CONDITIONAL-CALCULATIONS at DECLARED inputs — the
per-reading mass lines, the declared 60 N/channel fixture press ceiling,
the mu placeholders, the declared contact counts n, and the sealed tick —
with every threshold labeled CONDITIONAL-CALCULATION. WHY: the support of
a real hold routes through the declared press channel, and that channel
has NO actuator derivation (x_press ABSENT, TC-8 ports 0/8, honest
refusal stands; DERIVATION gap 6). A physical hold run would therefore
require an input this corpus does not contain, and anything past
declared-model scope would overclaim exactly the class the erratum
polices. The same-hands debt (the 0.049 kg anatomical hand vs the
10.038 kg scene line; the solver's mass-ratio problem) STANDS and is
named in the honest-absent list (section 5). Stage 4 answers, at
declared-model scope and no further: WHICH (mass reading, contact count)
CELLS the frozen law forms close or fail on.

## 1. INPUTS (each names its artifact/code path)

| quantity | value | code path / source |
|---|---|---|
| the mass readings (4) | 5.4 / 6.15 / 6.9 kg (register band) + 10.037998 kg (the certified scene line) | the DERIVATION A1 readings; gap 9 UNRESOLVED (per-reading law, never merged) |
| the weights W | 52.95591 / 60.3108975 / 67.665885 / 98.4391330867 N | the K-spec's own quoted std-g lines (frozen verbatim) |
| g | std-g via the frozen weights | the K-spec convention |
| the press ceiling | 60.0 N/channel | A3: the DECLARED fixture operating point, never an actuator qualification |
| mu_s | 0.6 | A5: NAMED placeholder |
| the transfer capacity | mu_s * jn = 0.6 * 0.3 = 0.18 N*s per channel | A3/A6 (jn = 0.3 N*s per tick) |
| DT | 5.0e-3 s | A3 (jn/DT = 60 N) |
| the contact counts | n = 1..5 | A2: the declared contact count, never an established anatomy count |
| the law forms | static hold P_req = W/(n*mu_s) <= 60; transfer (m*(g)*DT)/(n-1) <= 0.18 | A6 + the DERIVATION section 8.2 instance list |
| the mu=0 bite | the mu = 0 -> NON_CLOSING law-form consequence | retained from stage 3 (the S3-P3 pair), re-armed at the G01 forms |

## 2. THE OUTCOME SPACE (declared before the run; counts close over the full 4x5 grid)

Per (reading, n) cell, EXACTLY ONE of:
- `HOLD_CLOSES` / `HOLD_EXCEEDED` (the static law form);
- `TRANSFER_CLOSES` / `TRANSFER_EXCEEDED` (the transfer law form);
- `TRANSFER_UNDEFINED_AT_N1` (the (m/(n-1)) form at n = 1 — an EXPLICIT
  named class, the institutionalized absorbed-band lesson: the undefined
  cell is predicted, never silently dropped).
The 20 cells partition: 20 static outcomes + 20 transfer outcomes
(16 defined + 4 undefined). Any unnamed state, any count mismatch, or any
cell scored in two classes = `stage4_outcome_space_broken` (refusal).

## 3. THE FROZEN PREDICTIONS (the full partition, frozen; teeth = any cell differing)

- S4-P1 THE STATIC PARTITION (frozen): EXACTLY these 5 cells
  `HOLD_EXCEEDED`: (10.037998, n=1) P_req 164.065 N; (10.037998, n=2)
  82.033 N; (5.4, n=1) 88.260 N; (6.15, n=1) 100.518 N; (6.9, n=1)
  112.776 N. The other 15 cells `HOLD_CLOSES` (the band readings from
  n = 2 up; the scene line from n = 3 up, P_req 54.688 N at n = 3 — the
  same law-form number stage 3's positive control produced: cross-stage
  consistency recorded).
  TEETH: any cell's class or P_req differing from the frozen table; any
  count mismatch; any cell scored in both classes.
- S4-P2 THE TRANSFER PARTITION (frozen): EXACTLY these 5 cells
  `TRANSFER_EXCEEDED`: (every reading, n=2): 0.2648 / 0.3016 / 0.3383 /
  0.4922 N*s; and (10.037998, n=3): 0.2461 N*s. EXACTLY these 4 cells
  `TRANSFER_UNDEFINED_AT_N1`: (every reading, n=1). The other 11 cells
  `TRANSFER_CLOSES` (the band readings from n = 3 up; the scene line from
  n = 4 up). TEETH: any cell differing; the 5+4+11 counts not summing to
  20; the n = 1 class silently dropped (the absorbed-band lesson).
- S4-P3 THE MU=0 BITE (retained): the mu = 0 -> `NON_CLOSING` law-form
  consequence evaluated in-run on the G01 forms. TEETH: a closure at
  mu = 0 -> instrument invalid.
- S4-P4 NON-VACUITY (the comparison bites): the 5 static `HOLD_EXCEEDED`
  cells ARE the bite (proven in-run, not asserted); additionally the
  recorded debt-row cell (the scene line at 60 N declared press, tau
  1.392 N*m at cmc_abduction vs the 0.8875 cap) is RECORDED beside its
  law-form cell so the two readings of "exceeded" cannot be conflated.

## 4. THE QUANTITY CODE-PATH TABLE (the depth-basis law)

Every emitted number names its producer: P_req from the static law form
evaluated at the frozen W and mu; the transfer quantity from the frozen
transfer form at the frozen DT and jn*mu_s; W from the K-spec quoted
lines (verbatim); the ceiling/mu/jn/DT from A3/A5/A6; the law forms from
A6 + the DERIVATION instance list. No quantity is cited from a run
output; stage 4 consumes NO survivor-set geometry (the capacity stage
owns the placements; stage 4 owns the (reading, n) law grid).

## 5. THE HONEST-ABSENT LIST (binding; the not-claims at their most important)

- THE SAME-HANDS DEBT STANDS: the 0.049 kg anatomical hand vs the
  10.038 kg scene line; the support routes through the declared press
  channel; x_press is ABSENT (TC-8 ports 0/8); the 60 N/channel press is
  a DECLARED fixture, never an actuator qualification. NOTHING in this
  stage demonstrates that the anatomy can supply the press.
- THIS STAGE DEMONSTRATES NO PHYSICAL HOLD. "Supported" here means: the
  frozen law forms CLOSE or FAIL at declared inputs, per reading, with
  every threshold a CONDITIONAL-CALCULATION. The playable-monkey goal
  stays open until the positive behavior is demonstrated (the objective
  line law).
- Friction PLACEHOLDER (A5); the mass lineage UNRESOLVED (gap 9 —
  per-reading, never merged); no monkey-bark value exists; no solver
  integration is claimed; TC-8 = 0/8; C01 frame round-trip remains
  REQUIRED; the absorbed-band/undefined-cell lesson is applied (the n = 1
  transfer class is named, never dropped).

## 6. EXECUTION AND CONVENTIONS

Gate: the Lieutenant pins THIS file (separate-first), then releases; the
package seals against the pin commit; the seal bytes are captured into
`seal-store/` at seal creation; run class `stage4_supported_grasp` with a
receipt-level delta note (new stage, new (reading, n) grid, no survivor-
set geometry). Slot discipline: slot 2 first, fallback slot 3; this
lane's refusals leave no runner rows (the corrected record) and other
lanes' rows are never cited as this lane's attempts. Anti-tuning: the
grid, the law forms, and every constant above are frozen pre-run; the
frozen partitions are PREDICTIONS — a falsified cell is a RESULT recorded
and routed, never a re-tune. Receipt conventions: script-emitted hash
lines only; per-posture/per-reading blocks keyed; delta note present.
No merge/review authority claimed; Sergeant review requested through the
Lieutenant; author self-review certifies nothing.
