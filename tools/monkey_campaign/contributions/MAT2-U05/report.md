# MAT2-U05 qualification report — climb/let-go intent seam: records leg reused, MOTION leg delivered

Attempt `867dc0b142e84c138c99a486e4d4caa6`, arrival
`arrival-3ba367764f6543598c2669131d8b9982`. Card MAT2-U05 (planning U05,
profile `controls`, kind **motion**), criteria sha256
`0bc5d131c64d029e0b12f86ad4188b3fbe411ce5e2bc74510c5f7164e72c9a4a`.
Candidate base `2e2b8f5e02fa92d951f4065480ef4ddf2fa6fa1c` (head of
`astra/gait-capture` at attempt start; U01's merge `ebdfda61` is an ancestor).
PREREGISTRATION frozen BEFORE the build: body sha256
`05f8d9d0cdb0a30e0899a7d834ee7e32db3f9aa058c0736ca568bd0bcd868aac`; APPENDIX A
(prediction-deviation record, dated, body unchanged; full-file sha256
`41b22f89d881220cf78215e21377154a27b694843357cecf1da9d5ec580f7529`).

## DONE_WHEN (verbatim)

"One explicit climb/let-go intent reaches the skill selector with versioned
semantics; frozen walk contract remains unchanged."

## RECONCILIATION (what was reused, never re-authored)

- **Records leg (byte-exact reuse)**: the ENTIRE reviewed 30-file ONT-U05
  records leg of PR #179 @ `cdb0d81c95fb0fe93577e7b5d1f73d1549b3ec29` (two
  COMPLETE PASS worker reviews; the lead's only finding was the missing motion
  leg) is shipped under `seam_records/` with `git archive`-extracted blob
  bytes. Verified on disk before any build: 17/17 `identity_manifest.json`
  pins re-hash to their expected sha256 values (== lineage `272e7bda` for the
  pinned artifacts), and direct `git cat-file blob cdb0d81c:<path>` compares
  are byte-exact for `implementation.py` (== `product/climb_intent.py`
  `586cb1c5…`) and the walk seam `command_record.py` (`67711759…`).
  `seam_records/test_implementation.py` stays byte-exact: its F1–F4 re-run
  anywhere; its F5 names the ONT-U05 attempt checkout and is THAT attempt's
  historical measurement (this card's scope law is F-E below).
- **Interface decision (not re-decided)**: `INTENT_SEAM_SPEC.md`
  (`772d809d…`) + the four binding R4 amendments are THE reviewed interface
  decision; no vocabulary, key default, gate, stamp or delivery semantic is
  chosen by this attempt.
- **Dependency MAT2-U01**: DONE (PR #197, merge `ebdfda61`), in the base tree.

## WHAT THIS ATTEMPT AUTHORED (the motion leg; all under `contributions/MAT2-U05/`)

- `card_task.json` — THIS card's contract for the campaign's visual gate
  (task_id "U05", profile controls/motion, the three declared views).
- `seam_motion_probe.py` — the through-the-seam run: ONE deterministic
  injected-clock session drives the REAL pinned modules assembled UNMODIFIED
  into a repo-shaped sandbox — `SessionFlow` (X02) gating
  `FocusPolicy`->`InputMapper` (U03/U01 walk side) and `ClimbIntentChannel`
  (the seam) on ONE shared press/release surface — into STRICT exclusive
  sinks: the walk sink accepts ONLY CommandRecords; the selector sink
  implements the spec's DECLARED consumer surface (`emit(IntentEvent)` only)
  and its consumer law (refuse `intent_version != 1` loudly).
- `capture_build_seam.py` — renders the recorded trace into ONE deterministic
  video (3 views x 301 ticks x diagnostic+clean, 640x360, 20 fps, ffmpeg
  bitexact) and writes + VALIDATES the `chimera.visual_capture_manifest.v1`
  manifest with the campaign's own validator against `card_task.json`.
- `PREREGISTRATION.md`, `report.md` (this file), `qualification_receipt.json`,
  `evidence/` (trace, receipts, capture).

## HOW VERIFIED (exact commands, CPU-only, python -B, headless, injected clocks)

```
python -B tools/monkey_campaign/contributions/MAT2-U05/seam_motion_probe.py
python -B tools/monkey_campaign/contributions/MAT2-U05/capture_build_seam.py
```

Probe result: **RESULT: GREEN (11/11 checks)**, exit 0. Measured counts
(`evidence/numerical_receipt.json`, run_id `mat2-u05-seam-20260927-867dc0b1`):

- 5 IntentEvents delivered to the declared selector sink, exactly at the
  frozen predictions: climb_request@2000ms/tick600, let_go@3000ms/tick900,
  climb_request@5500ms/tick1650, climb_request@9500ms/tick2850 (first press
  after the session reload), let_go@10200ms/tick3060; every event
  `intent_version==1`, `source=="u05_climb_intent"`, canonical field set
  exactly `{intent, issued_tick, now_ms, intent_version, source}`,
  `issued_tick == now_ms*300//1000` (C12 one-timeline chain with the walk
  records' own stamp convention).
- 3 gated presses dropped-and-named, zero events, edge NOT armed:
  `dropped_blurred`@4500, `dropped_disconnected`@7000 (gates
  {blurred, disconnected}: the strongest names it), `dropped_paused`@8500;
  post-recovery presses deliver fresh (no phantom).
- 2 repeat-press named no-ops (2050, 2100), zero events; releases and policy
  events fabricated NO intent (let_go only at the two scripted C presses).
- Walk side UNCHANGED: 99 CommandRecords (module truth — see Deviations),
  all `source=="u01_input_mapper"`, all stamped on the same convention; 5
  exact named `Space` refusals ("jump: no walk-seam channel exists at v1 …")
  at 2000/2050/2100/5500/9500 (the other two Space downs are dropped
  upstream by the walk side's OWN blur/pause laws); zero sink violations;
  zero cross-deliveries (C1).
- Session reload: exactly ONE `World.boot` call; walk held empty at the
  quiesce; channel held empty + `ready` after; first post-reload press
  delivers exactly once (C7 — no stuck intent through reload).
- Falsifier outcomes: **F-A did not fire** (8/8 probe pins + 17/17 manifest
  pins), **F-B did not fire** (unmodified original suites re-run GREEN in a
  hash-verified sandbox: `climb_intent_tests.py` 73 checks,
  `climb_intent_amr_tests.py` 4 checks — the records leg's 77/77),
  **F-C did not fire** (sha256 of all five core modules identical before vs
  after the ENTIRE run incl. teeth — the frozen walk contract
  `67711759…` byte-unchanged, re-measured live), **F-D did not fire**
  (teeth below), **F-E did not fire** (`git status --porcelain -uall` on the
  attempt checkout: 41 paths, ALL under
  `tools/monkey_campaign/contributions/MAT2-U05/`, 0 outside),
  **F-F did not fire** (C1/C5/C7/C2 outcomes), **F-G did not fire** (gate
  receipt below).

Teeth (failing-first, sandbox copies only, pinned bytes never mutated):

- `m1_edge_law` (repeat press emits a second event) → 7 deliveries with
  extras at 2050 AND 2100 → C4 family fired.
- `m2_wire_version` (validator widened to accept 2 AND `_stamp` issues
  `intent_version=2`) → all 5 events REFUSED by the selector sink's consumer
  law, accepted 0 → C2 family fired. (Recorded intermediate: the stamp-only
  defect alone cannot reach the sink — the module's own validator REFUSES to
  CONSTRUCT a v2 event (IntentEventError at the press), a stronger guarantee
  than predicted; the two-anchor mutation is the minimal defect set that
  produces the predicted through-the-seam drift.)
- `m3_gate_law` (gated press falls through and delivers) → leaked deliveries
  at 4500/7000/8500 → C5 family fired.

Capture + camera manifest (`evidence/capture_receipt.json`,
`evidence/capture_manifest.json`):

- `evidence/capture.mp4` — 1806 frames (3 views x 301 ticks x
  diagnostic+clean interleaved), 640x360@20fps, sha256
  `e952a5f55453e569f12d6390ba65cddbfdcbb6a73c7d9dad91ea610fba2fc8ed`.
- `evidence/capture_manifest.json` — `chimera.visual_capture_manifest.v1`,
  task_id "U05" (the CONTRACT's task id), run_id
  `mat2-u05-seam-20260927-867dc0b1`, subject_sha256 = the seam module
  `586cb1c5…`, profile_id `controls`, tick_interval [0, 300], six view rows
  (3 declared views x diagnostic/clean pairs, per-pair identical camera
  blocks + state binding), every camera required field present, state
  binding = trace sha256.
- Gate: `visual_gate.verify` (campaign's own validator) against
  `card_task.json` → `structurally_valid: true` (`visual_acceptance: false`
  — the validator's own honest limit: independent visual review remains
  required and is the lead's).
- Visual spot-check performed by this worker at the seven frozen moments
  (deliveries 2000/5500/10200, drops 4500/7000, clean pairs): the L1 banner
  renders the REAL channel state and the REAL event/drop with its version
  and tick; the required target (monkey body) is readable in every view;
  clean rows contain no diagnostics. Frame extracts retained in the attempt
  workspace (`framecheck/`, not part of the candidate).

## DEVIATIONS (recorded, none silent)

1. **Walk-record count 101 → 99 (PREREGISTRATION APPENDIX A).** The frozen
   derivation misread the walk seam's release-decay law; the module's actual
   law (first boundary after release = linear sample, second = exactly 0.0
   and the tail ENDS) measures 99 = 72+4+1+22. Per the frozen stop rule the
   probe asserts the MEASURED module truth and the derivation correction is
   recorded in the dated appendix; no pinned byte was adjusted.
2. **M2 tooth shape.** Predicted as a stamp-only wire drift; a stamp-only
   defect is refused AT CONSTRUCTION by the event validator (the press
   raises IntentEventError — the drift cannot reach the wire). The shipped
   tooth is the minimal two-anchor defect (validator widened + stamp drifted)
   that produces the predicted through-the-seam drift; the stamp-only
   observation is recorded here as a measured intermediate.

## BUILD TRAIL (honesty; all defects were in THIS attempt's authored probe, never in the pinned bytes)

First runs failed as follows, each fixed before the final green run: (a) the
intent channel was not routed (the shared-surface half of the seam was
missing from the harness); (b) the trace-harvest snapshots were taken after
the channel press instead of before; (c) the teeth driver rebuilt the sandbox
from pinned bytes, wiping the mutation before import; (d) the m2 anchor-pair
replacement used the wrong value key. The walk-contract byte-identity and the
identity pins held at every stage (F-C/F-A were green from the first run).

## APPLICABILITY BOUNDARY (honest limits; nothing downstream is claimed)

Headless CPU visualization of the recorded trace of the REAL modules — NOT
native engine frames (no V03/V07/V08 claim); the selector state machine is
K-series and does not exist ("reaches the skill selector" is delivered at the
spec's DECLARED sink interface — the map's own completion semantics for this
row); no climbing behavior is claimed; the 50 ms boundary is the walk seam's
command cadence, not a latency claim (the runtime receipt records actual
durations, nothing derived); `visual_acceptance` stays with the lead's
independent review per the validator's own limits.

## SUBMISSION

Candidate commit on the attempt checkout branch (local `work-mat2-u05`, cut
from base `2e2b8f5e`), submitted for LEAD_SERIALIZED publication to
`review/MAT2-U05` (base `astra/gait-capture`) via the canonical
`worker_start.py --request-pr` handoff with hash-bound artifacts. Writes stop
at submission.
