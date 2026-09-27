# PREREGISTRATION — MAT2-U01 input/command-seam reconciliation (scoped verification)

Card `MAT2-U01` (planning U01, verification profile `controls`, kind **motion**),
attempt `c1488004ef62400389ba98a46837e5b7`, agent
`arrival-e922be0c34ef46ff84f504eb27e99178`, criteria
`bda3feb8fa32838f8799a83939af08a2d70c6069ec5af7b6c355b759f5aa019e`, scope
`cb5475f8486197a973edc4360b177fc31a629c4f0979ebf80dd76aae57996097`.
Written and frozen BEFORE the reconciliation verifier or either falsifier run
executed (this file and `verify_pinned_seam.py` were written before any run;
their hashes are recorded in the verification receipt). Any misprediction is
recorded FIRED in `evidence/verification_receipt.json`, never smoothed.

## Contribution class (frozen before execution)

RECONCILIATION + scoped verification, not a re-implementation. Steps 1 (reconcile
existing commits/diagnostics/receipts; reuse verified work) and 4 (verify the
exact done_when clause) of the card brief are satisfied by re-verifying the
ACCEPTED ONT-U01 qualification against the current criteria, over the REAL
pinned seam bytes. No new mapper/seam code is authored; nothing in the play
lineage is duplicated or modified.

## Clause identity (observed before this file was written)

The MAT2-U01 ontology packet and the ONT-U01 card contract carry the IDENTICAL
`definition_raw_sha256` `57ded6eb2f2cc6aa914d6f68c8efb55b215790fc7a9d0baa5dfd2c49fd1465c1`
(observed in this attempt's startup assignment packet and in
`reconcile/ont_u01_card_task.json`, extracted from integration tip
`origin/astra/gait-capture` = `b0108a364a560909c6c396bd916ec15369c27d7e`).
Unchanged clauses: done_when "Input emits bounded speed/heading commands at the
existing 20 Hz boundary, without state teleportation"; C12 "20 Hz implies a
50 ms command interval, not an end-to-end latency guarantee"; observation
"Do not require retraining for a UI remapping"; profile `controls`/motion with
falsifier "A stuck command, camera-induced body movement, unreadable required
target, concealed obstruction or unbound timing evidence fails." Only the scope
wrapper (`01ea5cdd…` -> `cb5475f8…`), card namespace (ONT- -> MAT2-) and
dependency cards (ONT-P01/P03 -> MAT2-P01/P03) differ.

## SUBJECT and lineage (identity pinned before execution)

The ACCEPTED ONT-U01 qualification (PR #147 head `9ad277d7…`, ACCEPTED and
merged via #169 `048b63f4` into `astra/gait-capture`), whose
`qualification_receipt.json` pins the lineage. The pinned bytes were extracted
byte-exact from `origin/astra/gait-capture` at `b0108a36…` into
`reconcile/pinned_seam/` BEFORE this file froze, and must hash:

- `tools/monkey_campaign/product/input_mapper.py`
  `7a36a45ead6637d9ba5659ea43b54a6b424803c8e57d02720ac970b42cfe6b44` (the
  qualified subject, `subject_sha256` of the accepted capture);
- `tools/science_funnel/typeb_export/command_record.py`
  `6771175933ad20ac6d20c360df96f6a9729a56deb31c58a13be5e76e1cc4355e` (the
  existing CommandRecord v1 seam);
- `tools/monkey_campaign/product/follow_camera.py`
  `d61347f085644e66a5f29ab1e689e2bbd2cd5ff04099856ade70e5da90a791a7`;
- `tools/monkey_campaign/product/input_mapper_tests.py`
  `95f44e90998f9728802ff5f7cb8628f18f2026bef1fb2c4de681e5253381216e` (frozen
  falsifier module F1–F6);
- `tools/monkey_campaign/agents/U01_input/PREREGISTRATION.md` `0aadc3cd…`,
  `discovery_note.md` `38efdf39…`, `receipts/input_mapper_tests_20260924.txt`
  `00c73e34…` (preserved records leg).

## FROZEN VERIFICATION PROBE (the ONLY runs that produce evidence)

CPU-only, stdlib, `python -B`, no GPU, no engine process, no network, no wall
clock in any asserted path. `verify_pinned_seam.py` executes, in order:

1. FAILING-FIRST mutant run: a throwaway copy of the pinned tree
   (`reconcile/mutant_seam/`) whose ONLY change is `INTERVAL_MS = 50` -> `40`
   in `input_mapper.py` (a bounded-command-cadence violation), run under the
   UNMUTATED pinned falsifier module. FROZEN PREDICTION P3: the suite FAILS
   (exit code 1, at least one `FAIL` line naming the clock falsifier). If the
   mutant suite passes cleanly, the falsifier suite is vacuous and this
   reconciliation is DEAD (F-C below).
2. Pinned run: the same pinned falsifier module over the byte-identical pinned
   bytes, with the runner asserting all seven lineage hashes at import time.
   FROZEN PREDICTION P2: exit code 0, VERDICT GREEN, 0 FAIL lines (the
   preserved records receipt `00c73e34…` reported 26/26).
3. Lineage assertion: the seven pinned hashes recomputed from disk.
   FROZEN PREDICTION P1: 7/7 match the accepted receipt's pinned lineage table
   (above), proving the accepted subject bytes are UNCHANGED at the current
   integration tip.

Frozen prediction P4 (board state, observed at this attempt's startup BEFORE
implementation): dependencies MAT2-P01 and MAT2-P03 are DONE with lead-verified
merges (#192 merged 2026-09-27T08:47:35Z, #194 merged 2026-09-27T09:36:08Z).

## FALSIFIERS of this card's reconciliation (any one kills it)

- F-A: any pinned hash mismatch at the current tip — the seam drifted, the
  accepted work no longer satisfies the unchanged clauses, and a new
  implementation would be required.
- F-B: any FAIL line in the pinned falsifier run — the accepted subject no
  longer holds its own frozen contract.
- F-C: the mutant run passes cleanly — the falsifier suite is vacuous and the
  PASS it produces is worthless.
- F-D: any clause divergence (`done_when` / C12 / profile / observation) between
  the MAT2-U01 packet and the ONT-U01 card contract — reconciliation is
  unlawful and the clause is NOT unchanged.

## EVIDENCE CLASS (recorded honestly, frozen before execution)

COMPONENT-LEVEL evidence over the REAL pinned seam bytes, exactly the class the
accepted ONT-U01 review scoped as satisfying this interface-subject clause
("the done_when subject is the input-to-command seam itself and the card
profile explicitly does not require downstream skills to accept an upstream
interface"). NOT an integrated-application claim. The input->body-EXECUTION leg
remains INCOMPLETE exactly as measured and recorded in ONT-U01's
`real_run_correction` (the pinned engine refuses gait enablement and has no
route consuming V1 speed/heading records — measured, not assumed). The
profile's visual/camera legs were exercised by the ACCEPTED ONT-U01
qualification at these exact subject bytes (capture `a51fcbc8…`, labeled
SYNTHETIC/deterministic CPU visualization; real-run leg `846f0b32…`); this
reconciliation manufactures NO new visual capture because the subject bytes are
unchanged — re-running the visual pipeline over identical bytes would produce
no new information and is deliberately not claimed as new evidence.

## DONE_WHEN mapping claimed (bounded by the falsifiers above)

"Input emits bounded speed/heading commands at the existing 20 Hz boundary,
without state teleportation" — satisfied by the accepted, integrated, pinned
lineage, re-verified at the current criteria per the frozen probes. If F-A,
F-B, F-C or F-D fires, this claim is withdrawn and the card returns to
implementation.
