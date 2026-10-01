# REPORT — MAT2-U07 measure controls during actual play

Generated from the sealed stage receipts; no hand-entered numbers.

## Identity

- Card MAT2-U07, attempt 5e2bc3cb1fec4305911a1048b600723d, agent wk-u07-arrival-1.
- Base a07ac859d4ef16bb34d4006a75c4de8dbee462b4; prereg sha256 a8781f6e9ae3b5aff31a497e52d697e8c60b0ab80b338e48707736576432d033.
- done_when (verbatim): End-to-end input response and camera behavior meet P06 limits under repeatable scenes
- Profile: controls/motion (registry read-only at run time; checked BEFORE any capture).
- Certified line: cpu-walk-scene-build-N (W10 gate identity re-executed; deploy ALLOW).

## Measured variables (named, preregistered)

- P1 first_response_ms_max = 27 over 5 input transitions (chains 403; limit 50.0 ms, C12 seam cadence, caller data; AMENDMENT-A1 law) -> QUALIFIED.
- P2 consumed_lag_ticks_max = 1 (ZOH boundary law) -> QUALIFIED.
- P3 presented_lag_ticks_max = 14 over 21 window chains (bound 300); presented = the DECLARED CPU-line frame record (A1).
- P4 poll_period_ms_max = 50 (P06 frozen ui-poll-cadence-ms = 100 ms) -> QUALIFIED against the ONLY frozen P06 cadence numeric.
- P7 first_revert_age_ticks = None (EXPIRY_TICKS=30; the stuck-command law reverts at age 31).
- P5/P6/P8/P9/P10/P12: all green in controls_receipt.json (repeatable scene bit-identical; wrong-key response flagged; focus blur drops named and recovery is a new chain; camera fields complete; obstruction numerics executed; mixed-clock refused).

## Honest negatives (the unqualified part of the done_when)

- P11 wall-clock end-to-end latency: status 'unqualified' (p06_limits_absent). No frozen wall-clock SLA exists — P06 network-latency-sla-ms is an open OPERATOR_DECISION_REQUESTED; nothing is inferred or defaulted.
- A1 native engine recorder seams: ABSENT; the presented stage is the declared CPU-line frame record; only the declared window (chains 21) carries presented events.
- A3 human feel: NOT measured (distinct acceptance field).
- A4/A5/A6/A7: camera HTTP transport, session controls, OS focus and W10's physical-separation claim: declared/cited, not exercised or re-claimed (controls_receipt.json absent_inventory).

## Checks and capture

- Named checks: GREEN (18 executed, 0 skipped).
- Capture: 32 frames, video sha 05ad0e2283581b84, decode probes pixel-exact True, validator True.
- Pixel gate (mechanical, AMENDMENT-A4): GREEN over 32 decoded frames of the committed video; 32 non-uniform; body palette present in 30 frames; declared diagnostic layers green in 6 of 6 diagnostic frames; planted-defect selftest GREEN (deliberately blank frame refused).
- Pins: 20 U07 rows + 65 W10 certified-line rows, byte-exact.

## Correction round r1 (review sgt-pr312-69772e91)

- Prior review citation (not a new measurement): 0 of 32 committed frames at head 69772e9143d582cdd0d2d56c990c0a5b0e697509 contained the body palette (PIXEL-FAIL; see kanban-reviews/MAT2-U07/sgt-pr312-69772e91/REVIEW_EVIDENCE.md (head 69772e9143d582cdd0d2d56c990c0a5b0e697509)).
- The view law is UNCHANGED frozen preregistration: the clean view is the declared follow view and every camera position/target is a body-anchored offset (PREREGISTRATION.md, the declared camera arms and the frozen probes/views sections). The candidate's view dicts omitted the pinned renderer's follow flag; this correction restores conformance and re-derives every committed frame.
- The mechanical pixel-content gate now decodes EVERY declared frame from the committed video and refuses uniform/empty renders or missing declared layers (AMENDMENT-A4; hash pinned in the receipts like the earlier amendments).

## Verdict

The frozen structural controls laws (P1/P2/P3/P4) and the camera behavior structure (P9) are QUALIFIED on the certified CPU line under repeatable scenes. The wall-clock end-to-end latency claim is UNQUALIFIED by law (A2) and the native presented frame is ABSENT (A1). This receipt alone does not close the card: lead-approved exact-head PR with full qualification evidence remains.
