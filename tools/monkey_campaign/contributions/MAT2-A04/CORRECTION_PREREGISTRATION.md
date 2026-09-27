# CORRECTION PREREGISTRATION — MAT2-A04 palm-sign binding + geometry-coverage determination

Written and frozen BEFORE any correction verification run of this attempt. Card
`MAT2-A04` (planning `A04`, profile `anatomy`, kind `visible_static`), attempt
`c8bb40c32ddb4b01a1c99d7a66582e37`, agent `arrival-749dfd83baf04ac3835e45ef54657633`,
criteria `b6a4bb30f1bfe207c76969f2eebfd736d33360546d1d0522bae8e29860a1bf3d`, scope
`cb5475f8486197a973edc4360b177fc31a629c4f0979ebf80dd76aae57996097`. Correction return
narrowly per the Lieutenant ruling on this card (msg-0ea0fba3): preserve all verified
reconciliation bytes; bind the authorized palm-face decision to the correspondence
record; define and verify the required geometry-coverage result or request a precise
amendment. Work branch `work-a04-palm-bind`, base = merged tip `4dba6cb1`
(`origin/astra/gait-capture`; the prior candidate base `8ec90f13` is an ancestor).
The 12 prior candidate files (published head `72ecc827`; attempt commits `d18b12bc` +
`4e80fe27`) are carried BYTE-PRESERVED in the preceding commit — verified equal to the
`72ecc827` blobs before this freeze.

## Reconcile-phase inputs (read, hash-verified on disk BEFORE this freeze; nothing run)

- OPERATOR decision record
  `E:/ChimeraWork/monkey-coordination/review-workspaces/labeling_gate_ER/gate_artifact/OPERATOR_DECISION.json`
  sha256 `4999a60cb9045f2e27f32b92e7b4f115cda8e34ed78dbdbf95af619255c6ad46`;
  question verbatim "Which lettered face is the PALM (ventral) - A or B? (A = broad
  face on the +T_R side; B = -T_R side)"; answer verbatim "B"; answered_by "Captain
  (operator), verbatim message: B"; answered_at "2026-09-27T18:20Z"; anatomical
  effect: palm/ventral = the -T_R face.
- Instruments, hashes re-verified on disk by this attempt: `DECISION_PANEL.png`
  `33b88a30ee2b4b6c90751c65f36fb6557ddf04a837400415769cde5cf49861b0`;
  `DECISION_CARD.md` `c4a36f289087e8cf3ff401ec425e74d3d9d42616c3fad724ae4e70e54370646c`;
  `VERIFICATION.txt` `95ac1609b588fe583e4baa37ad39bdef608e5c8fe8622df1aa8f70defd45b808`
  (34/34 PASS; self-pins the same panel/card hashes).
- DISCLOSED instrument-record defect (observed, not silently corrected, not authored
  by this attempt): inside `OPERATOR_DECISION.json` the `instrument.sha256` field
  contains `95ac1609…` — the VERIFICATION.txt hash — while sitting directly under the
  `decision_panel_png` path key whose on-disk hash is `33b88a30…`. The binding below
  uses the ON-DISK VERIFIED hashes for every instrument and records this mislabel
  verbatim. The operator record file itself is outside this attempt's write authority.

## What this correction builds (the only work it builds)

On top of the byte-preserved candidate: (i) a decision-binding record
`verification/P7_operator_decision_binding.json` binding the operator verdict to the
correspondence record with full source identity (all hashes above + the question,
answer, answerer, timestamp); (ii) palm clause moved UNRESOLVED ->
**RESOLVED-BY-OPERATOR** in `reconciliation.json` and `qualification_receipt.json`
(with `gaps_standing` G1 closed the same way; G2-G5 texts untouched); (iii) the
geometry-coverage determination `verification/P10_geometry_coverage.md` defining the
required result FROM THE MERGED EVIDENCE'S OWN CLAIMS and verifying it at preserved
bytes; (iv) base-move re-verification receipts `verification/P8_base_move.txt` and
`verification/P9_validators.json`. The prior `PREREGISTRATION.md`, the frozen
P1-P6 receipts, `card_task.json`, `revalidate_manifest.py` and the frozen capture
evidence are NOT modified. No new measurement code, no constants authored, no edits
to the merged ONT-A04 tree, no capture rebuild (capture evidence stays frozen).

## FROZEN PREDICTIONS (any miss is recorded FIRED, never retried into passing)

- **PC-1 decision binding:** the decision record and instruments hash-match the
  on-disk values above; the recorded question equals the prior candidate's recorded
  `decision_request.question_verbatim`; the answer is a lawful answer under the card
  ("B is the palm"); the binding records the mislabel disclosure.
- **PC-2 base-move pin integrity:** the 7 in-tree ONT-A04 accepted-head pins
  (probe `8e36aa2f…`, PNG `878eb3de…`, manifest `4447058a…`, capture receipt
  `74731438…`, numerical `e3864b16…`, state `33d3219c…`, ONT qualification receipt
  `726efaf8…`) byte-match at the NEW base `4dba6cb1` (the merged line moved; the
  ontology definition blob is unchanged on the line — verified in the reconcile
  phase).
- **PC-3 numerical probe rerun at the new base (scratch copy, CPU-only `python -B`):**
  `a04_correspondence_probe.py` exits 0, `all_green=True`, deviations exactly the 2
  merged-recorded ones (C4 s2 site-metric convention within the 3.5 mm anchor class;
  C5 far-end 18.0393 vs printed 18.1 mm), regenerating `numerical_receipt.json` /
  `state_snapshot.json` byte-identical to `e3864b16…` / `33d3219c…`.
- **PC-4 test suite at the new base:** `python -B -m unittest test_ont_a04` → 19/19 OK.
- **PC-5 both validators TRUE on the committed envelope:** with `card_task.json`
  (CONTRACT `task_id "A04"`, scope `cb5475f8…`, profile anatomy/visible_static) and
  the FROZEN merged capture bytes (no rebuild): canonical
  `visual_capture.validate_manifest` → `structurally_valid=True`; canonical
  `visual_gate.verify` on materialized merged manifest + capture sheet bytes →
  `structurally_valid=True`.
- **PC-6 geometry coverage determination:** the required result is defined from the
  merged evidence's own claims — (a) C1: 27/27 vendor STL sha256 identity of the
  source assembly (`27 right + 27 left geoms`, scales [1,1,1]); (b) C6: 27 source
  bone IDs + 5 port IDs + per-port owner map + 2 target anchors (wrist_R, elbow_R);
  (c) capture receipt `capture_truth.placed_source_vertex_count = 342111` with
  `bounds_check.all_inside = true` (subjects `src/assembly/27_bones`,
  `tgt/envelope/distal_band`); (d) C4: all anchor sites inside the governing 3.5 mm
  anchor class. Determination: the 14-phalanges gap does NOT leave the clause
  unsatisfiable — the identical clause text was lead-ACCEPTED (`done_when_verified:
  true`) with the SAME explicit gap carried in the merged ONT-A04 record, and the
  operator decision's own scope note keeps digit structure outside this card's
  closure (owned by A05). Therefore NO amendment request is filed and NO clause text
  is weakened: the gap stays recorded verbatim in `gaps_standing` (G3) with owner A05.
  Falsifier PC-6-FIRES if the re-verified bytes contradict any claim in (a)-(d), in
  which case a precise amendment decision request naming the missing scope is filed
  instead of the determination.
- **PC-7 preservation:** the 12 carried files remain byte-identical to `72ecc827`
  except exactly the files this correction is authorized to change
  (`reconciliation.json`, `qualification_receipt.json`, `report.md`, and the new
  `verification/P7…`-`P10…` artifacts); `PREREGISTRATION.md`, `card_task.json`,
  the P1-P6 receipts and `revalidate_manifest.py` stay byte-identical.

## FALSIFIERS (frozen)

- **GC-A (decision forgery/drift):** any on-disk hash mismatch vs the recorded
  decision/instrument identities, or any answer string other than the recorded
  verbatim values → STOP and report; nothing is bound.
- **GC-B (honesty inheritance, from card falsifier F-D):** binding anything beyond
  what the operator record states, inferring a sign not stated, or weakening any
  standing gap text → FORBIDDEN; the correction only closes G1 the way the operator
  record states it.
- **GC-C (evidence drift at the new base):** any PC-2 pin mismatch, PC-3 new
  deviation or non-identical regeneration, PC-4 suite failure, PC-5 validator FALSE
  → STOP and report.
- **GC-D (preservation):** any byte change outside the authorized files → STOP.

## SCOPE DISCIPLINE

CPU-only (`python -B`; stdlib + numpy + matplotlib Agg only). Reads outside the
attempt workspace are read-only; ALL writes stay inside this attempt workspace and
its checkout. The merged ONT-A04 tree is referenced read-only, never modified. No
runtime/native claim; capture evidence frozen (no rebuild); static/offline only.
