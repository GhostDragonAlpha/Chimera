# R1 AMENDMENT-2 — the raised-cap adjudication of ALL pad-satisfied rows (pre-run; DRAFT for the Lieutenant's pin)

- Lane: `E:/ChimeraWork/monkey-coordination/hand-remediation/` (owner
  `wk-hand-remediation`; NO_WORKTREES honored). DRAFT authored for the
  Lieutenant's pin (separate-first; the committed bytes are the freeze).
- Status: PRE-RUN for the raised-cap class. The stage-1 receipt
  (`d29113a1...`, PR #333, astra `28e372ff`) exists and is the DECLARED BASIS
  of this amendment's numbers; the raised-cap run itself has NOT executed —
  no raised-cap result exists anywhere, and nothing below is adjusted to one.
- Law of amendments: the pinned prereg (4def67e4 / `9213bf7d...`) and
  AMENDMENT-1 (0c06e093 / `018f0bc1...`) are never edited; this document
  adds ONE declared change (the post-pad adjudication cap) plus the review's
  three receipt-convention fixes, and is lawful ONLY pre-run of the
  raised-cap class. Post-run change requests remain FINDINGS, never edits.
- Execution gate: the raised-cap run executes on the Lieutenant's explicit
  release AFTER this amendment is pinned; the implementation package seals
  against the pin commit.

## 1. THE DECLARATION (the one change)

The post-pad exact-adjudication cap is RAISED from the inherited
`CAP_S1_PER_POSTURE = 96` (a cheap-screen inheritance from the frozen v2.0
formulation, never a physics bound) to **ALL pad-satisfied rows of the
posture** — implemented as the frozen constant `CAP_POST_PAD = 1500`
(>= 1,184, the total pad-satisfied rows of both evaluated postures: 826 q_c
+ 358 q_zero), under the UNCHANGED inherited cumulative S1 wall-clock budget
(2.5 h) and every other frozen law. The inheritance note is recorded, not
hidden: the 96 cap existed to bound the v2.0 cheap screen's cost, and stage 1
inherited it; the raised-cap class removes it for the pad-adjudicated rows
ONLY. Nothing else changes: the S0 mirror, the sealed-row identity gates,
the pad layer, the battery C1-C10, the tolerances, the force columns, P1-P4
(all verified, preserved), the force label, and the timing budget stand.

## 2. THE COMPUTE COST (from the stage-1 throughput; declared before the run)

Stage-1 measured S1 clock: 12.2 s for 192 exact cells = 63.5 ms/cell. The
raised cap adjudicates 826 + 358 = 1,184 cells -> ~75 s of S1 (from ~12 s),
total run wall from 139 s to an estimated ~3-4 min. Budget 2 GiB unchanged;
timeout 4 h unchanged; one job, slot 2 (fallback 3), BUSY = retry. The
estimate is an admission convenience, never an acceptance criterion.

## 3. THE FROZEN PREDICTIONS (count floors only; NO WHICH-rows prediction — that would be tuning)

- P5 (q_c_PRIMARY): the FULL-SET post-pad survivor count is **>= 84** — the
  capped sample's count, stated as the floor because the sample cannot
  exceed the full set's rate without the cap rows being systematically
  harder, which nothing in the frozen law predicts. The exact full-set
  number is RECORDED (it is the deliverable, not a gate).
- P6 (q_zero_CONTROL): the full-set post-pad survivor count is **>= 14**,
  the same discipline applied to the second posture (the Lieutenant's
  declaration named q_c; P6 is recorded symmetrically so no posture's number
  arrives unpredicted).
- CONTRADICTING OBSERVATIONS (the wording law): P5 falsified iff the q_c
  full-set count < 84; P6 falsified iff the q_zero full-set count < 14. A
  falsified floor is a RESULT (the capped sample was unrepresentative) —
  recorded in the receipt and routed to the Lieutenant; it refuses nothing
  and retunes nothing. No prediction is made about WHICH rows survive; the
  per-row records identify them, and the capacity stage consumes the ACTUAL
  final set.

## 4. THE RECEIPT-CONVENTION FIXES (the review's durable lessons, applied in this revision)

1. HASH-CITING FIELDS NAME THEIR ARTIFACT EXPLICITLY: the stage-1 receipt's
   `digit_scan_gate` field carried the V2.0 receipt sha under a digit-scan
   label. The revision names every cited artifact: path + role + its own
   sha256 (the digit-scan gate cites
   `digit-scan/final_run_job1/grasp_screen_digit_receipt_job1.json`, sha
   `a4f9b62678b16efb287fe0e1792bd59e04b3dcf81ecd54e4e58800c8663000b7`,
   verdict ZERO_SURVIVORS_DIGIT_SIDE, job `3a1ff276...`).
2. PER-POSTURE BLOCKS ARE KEYED, NOT update()d: stage 1's
   `predictions.update(preds)` let q_zero overwrite q_c's P1/P2 entries in
   the flattened view. The revision keys every per-posture block by posture
   (`predictions[q_c_PRIMARY][P1]`, ...); no cross-posture overwrite exists.
3. RECEIPT-LEVEL DELTA NOTE: the raised-cap receipt carries a
   `delta_note` naming its run class
   (`stage1_pad_raised_cap`, amendment-2) and stating the delta vs the
   published stage-1 class: ONLY the post-pad S1 cap coverage changes (and
   the three convention fixes); the S0 mirror, pad layer, battery and
   identity-gate code paths are unchanged, and the stage-1 receipt remains
   the published record of the capped class.

## 5. THE ANTI-TUNING STATEMENT

This amendment is authored BEFORE the raised-cap run exists; its only
numerical inputs are the ALREADY-PUBLISHED stage-1 receipt (the sample) and
its own throughput measurement. The floor predictions are the sample counts
themselves — the weakest claims the sample supports — and no which-rows
prediction is made. Any post-run change request is a FINDING routed to the
Lieutenant, never an edit.

## 6. WHAT DOES NOT CHANGE

The pinned prereg and AMENDMENT-1 byte-for-byte; t, u_max, the window, the
patch rule, k and the force columns; the trunk, joint limits, placement
families, tolerances; the bone-level classes and the exclusions ledger;
TC-8 = 0/8; the C17 non-identity; the honest scope (the pad = a
contact-geometry layer, never a support element; cause 2 converted ZERO rows
at stage 1 and this amendment does not touch cause 2); the named-unscanned
list; the qualification ladder and its gate order. Stage 2 (actuator
capacity) consumes the FINAL survivor set of the raised-cap receipt — prep
only until then.

## 7. GOVERNANCE

Authored by wk-hand-remediation; DRAFT for the Lieutenant's pin
(separate-first, pre-run). The implementation revision pins THIS document's
committed sha and refuses on drift; the package seals against the pin
commit; all execution stays through the canonical runner; hashes land in
EVIDENCE.md. No merge/review authority claimed; Sergeant review requested
through the Lieutenant; author self-review certifies nothing.
