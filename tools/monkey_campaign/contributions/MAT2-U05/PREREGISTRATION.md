# MAT2-U05 PREREGISTRATION (attempt 867dc0b142e84c138c99a486e4d4caa6) — the climb/let-go intent seam: records leg reused, MOTION leg delivered

Frozen 2026-09-27 BEFORE any motion-leg assembly or verification run, in isolated
attempt workspace `E:/ChimeraWork/monkey-coordination/kanban-attempts/MAT2-U05/867dc0b142e84c138c99a486e4d4caa6`
(slot branch `branch-4`, candidate base = `2e2b8f5e02fa92d951f4065480ef4ddf2fa6fa1c`,
the head of `astra/gait-capture` at attempt start; U01's input-seam reconciliation
`ebdfda61` is an ancestor of this base). Arrival:
`arrival-3ba367764f6543598c2669131d8b9982`. Card criteria sha256:
`0bc5d131c64d029e0b12f86ad4188b3fbe411ce5e2bc74510c5f7164e72c9a4a`.

## DONE_WHEN (verbatim, frozen by the card)

"One explicit climb/let-go intent reaches the skill selector with versioned
semantics; frozen walk contract remains unchanged." Constraint: "Requires a
reviewed interface decision, not an invented API."

Verification profile: `controls`, **kind = motion** — visual + camera + runtime
qualification evidence is REQUIRED (this is exactly the leg the lead's
CHANGES_REQUIRED on ONT-U05 PR #179 demanded; the records leg was verified and
PRESERVED there and is REUSED here, never re-authored).

## RECONCILIATION (phase 1 deliverable, frozen here before the build)

Clause-to-evidence map:

- The reviewed interface decision EXISTS and is NOT re-decided by this attempt:
  `INTENT_SEAM_SPEC.md` (sha256 of the shipped bytes
  `772d809df620bb93cce97fd41f081ba244b44edfef8d9ee4797f16cc8eac143b`), frozen
  before implementation 2026-09-24, R4 verdict APPROVED-WITH-AMENDMENTS, the four
  binding AMR-1..4 landed inside v1.
- The implementation EXISTS and is owned by this exact task:
  `product/climb_intent.py` @ lineage `272e7bda` (LF sha256
  `586cb1c541afdc391ac14ce989cf2d2561a9ee79e25e874f7fbfc2312fd3c5a2`), shipped
  here BYTE-EXACT as `seam_records/implementation.py` together with its two
  original suites (73 + 4 checks), the four sibling product modules
  (`input_mapper.py` `7a36a45e…`, `focus_policy.py` `e0b23968…`,
  `session_flow.py` `30e06c04…`), the frozen walk seam
  (`tools/science_funnel/typeb_export/command_record.py` `67711759…`), the
  lineage receipts and the ONT-U05 attempt's own re-verification harness — the
  ENTIRE reviewed 30-file records leg of ONT-U05 PR #179 @
  `cdb0d81c95fb0fe93577e7b5d1f73d1549b3ec29` (two COMPLETE PASS worker reviews;
  lead finding was ONLY the missing motion evidence), relocated under
  `seam_records/` with `receipts/identity_manifest.json` re-verifiable by its
  own contribution-relative paths. Provenance chain: MAT2-U05/seam_records ==
  cdb0d81c blobs == lineage 272e7bda blobs (for the 17 pinned artifacts).
- "One explicit climb/let-go intent reaches the skill selector": the selector
  does not exist yet (K-series); the spec's section 7 DECLARS the consumer
  surface the selector will implement (`emit(IntentEvent)` only). The motion leg
  delivers a REAL through-the-seam run into a STRICT selector-sink double that
  implements exactly that declared surface and its consumer-side law
  (refuse `intent_version != 1` loudly). This is the map's own completion
  semantics for this row — no climbing-behavior or selector-state-machine claim.
- "Frozen walk contract remains unchanged": measured live — the walk seam's
  bytes (`67711759…`) are hashed before and after the ENTIRE probe run, and the
  walk side's REAL behavior is exercised in the same run (named `Space` refusal
  unchanged; CommandRecords at the 20 Hz boundary before/during/after intent
  delivery; exclusive sinks).
- Dependency MAT2-U01: DONE (winner PR #197, merge `ebdfda61bf3df9b1f6985f771044fd946dd5e9db`,
  an ancestor of this candidate base). Its contribution is in the tree.

DECISION (recorded ruling, not invented here): the interface semantics are the
shipped spec + R4 amendments; no new vocabulary, key default, gate, stamp or
delivery semantic is chosen by this attempt. The motion leg adds NO product
code: the only authored sources are the probe, the capture builder, the card
contract, the receipts and this prereg — all under `contributions/MAT2-U05/`.

## RULE 0 — the theory, stated before the build

**STATEMENT** (disagreeable): the pinned seam modules, assembled UNMODIFIED into
a repo-shaped sandbox from `seam_records/` bytes, drive a REAL integrated
session — SessionFlow gating the FocusPolicy-wrapped InputMapper (walk side)
and the ClimbIntentChannel (intent side) on ONE injected clock and ONE shared
press/release surface — such that (a) every scripted climb/let-go press yields
EXACTLY ONE versioned IntentEvent delivered synchronously into the declared
selector sink, (b) every gated press is dropped-and-named with no phantom edge
across blur/disconnect/pause and across a full session restart (reload), (c)
the walk side keeps its frozen behavior and its sink receives ONLY
CommandRecords while the intent sink receives ONLY IntentEvents, and (d) no
pinned byte changes across the whole run. The visualization of this recorded
trace is diagnostic rendering of REAL module outputs, not a fixture standing in
for a missing seam.

**PREDICTIONS** (measured by `seam_motion_probe.py`, then
`capture_build_seam.py`; all CPU-only, headless, injected integer ms):

- P1 IDENTITY: all 17 `seam_records/receipts/identity_manifest.json` pins
  re-hash to their expected values from the shipped bytes (F1 of the records
  leg, re-measured here), and the five core modules below match their pins.
- P2 SUITES GREEN (records leg, unchanged): the UNMODIFIED original suites
  re-run in the hash-verified sandbox print `RESULT: GREEN`, exit 0 —
  `climb_intent_tests.py` (73 checks) and `climb_intent_amr_tests.py` (4 checks);
  walk-contract byte-identity across that run (the records leg's I6).
- P3 THROUGH-THE-SEAM RUN (the frozen timeline below):
  - exactly 5 IntentEvents delivered, in press order:
    climb_request@2000ms/tick600, let_go@3000ms/tick900,
    climb_request@5500ms/tick1650, climb_request@9500ms/tick2850,
    let_go@10200ms/tick3060; every event: `intent_version==1`,
    `source=="u05_climb_intent"`, canonical field set exactly
    `{intent, issued_tick, now_ms, intent_version, source}`, and
    `issued_tick == now_ms*300//1000` (the injected tick_source; the walk seam's
    own stamp convention — C12's one-timeline chain).
  - exactly 3 gated presses dropped-and-named, zero events, no arm:
    `dropped_blurred`@4500, `dropped_disconnected`@7000 (gates
    {blurred, disconnected} — strongest names it), `dropped_paused`@8500; the
    next press after each recovery delivers fresh (no phantom).
  - exactly 2 repeat-press no-ops (2050, 2100) with zero events.
  - releases and policy events fabricate NO intent (no let_go except the
    scripted C presses).
  - the walk side records the exact named refusal
    "jump: no walk-seam channel exists at v1 (commanded_heading itself is
    reserved for a later lane)" for each scripted Space press, and emits
    exactly 101 CommandRecords (derivation frozen below), all into the walk
    sink; `v_forward` per the frozen law; the walk side and the intent side
    NEVER cross-deliver (strict doubles; any other surface call is recorded as
    an undeclared attempt and fails).
  - session reload (pause→R→World.boot→playing, exactly one boot call):
    channel `held` empty, state `ready`, and the first post-reload press
    (9500ms) delivers exactly once — no stuck intent through reload; the walk
    side's held set is empty at the quiesce and its decision clock is suspended
    while paused (zero records in [8000,9000)).
- P4 TEETH (failing-first, sandbox copies only, pinned bytes restored after):
  - M1 EDGE LAW BROKEN (the records leg's M1: a repeat press emits a second
    event) → probe check C4-exactly-once fires, exit 1.
  - M2 VERSION DRIFT ON THE WIRE (`_stamp` issues `intent_version=2`) → the
    strict selector sink's consumer law REFUSES the event; probe check
    C2-versioned-delivery fires, exit 1.
  - M3 GATE LAW BROKEN (the records leg's M3: a gated press falls through and
    delivers) → probe check C5-gates-drop-named fires, exit 1.
  Restoring the pinned bytes returns the probe to GREEN.
- P5 SCOPE: the candidate commit touches ONLY
  `tools/monkey_campaign/contributions/MAT2-U05/**` on top of base `2e2b8f5e`;
  no product path, no sibling module, no campaign tooling is modified.
- P6 CAPTURE GATE: the rendered capture validates against THIS card's frozen
  contract (`card_task.json`, task_id "U05", profile controls/motion) with the
  campaign's own validator (`visual_capture.validate_manifest` via
  `visual_gate.verify`): `structurally_valid: true`, 3 declared views ×
  diagnostic+clean pairs, all camera required fields present, state binding =
  the trace sha256.

## THE FROZEN TIMELINE (nothing else is injected; per-ms order: key/policy events first, then the 50 ms decision tick)

Injected clock (ms); tick stamp = `now_ms*PHYSICS_HZ//1000`, PHYSICS_HZ=300
imported from the walk seam. Decision ticks every 50 ms from 0 to 15000
(T_END=15000; 301 boundaries).

| ms | event |
------|-------
| 0 | Return down (flow attract→playing) |
| 500 | W down |
| 2000 | Space down → DELIVER climb_request #1 (tick 600) |
| 2050 | Space down (repeat no-op) |
| 2100 | Space down (repeat no-op) |
| 2500 | Space up |
| 3000 | C down → DELIVER let_go #2 (tick 900) |
| 3500 | C up |
| 4000 | blur (walk side releases W via its law; intent gate blurred) |
| 4500 | Space down → DROP dropped_blurred |
| 5000 | focus |
| 5500 | Space down → DELIVER climb_request #3 (tick 1650) |
| 6000 | Space up |
| 6500 | disconnect |
| 6800 | blur (gates = {disconnected, blurred}) |
| 7000 | C down → DROP dropped_disconnected (dominance naming) |
| 7100 | C up (releases always pass) |
| 7500 | reconnect + focus → ready |
| 7800 | W down |
| 8000 | Escape down (flow playing→paused: quiesce release_all; harness mirrors on_pause once) |
| 8200 | Escape up (flow named drop while paused) |
| 8500 | Space down → DROP dropped_paused (NOT armed) |
| 8700 | Space up (passes) |
| 9000 | R down (paused→restart: release_all + World.boot → playing; harness mirrors on_resume) |
| 9500 | Space down → DELIVER climb_request #4 (tick 2850) — fresh after reload |
| 10000 | Space up |
| 10200 | C down → DELIVER let_go #5 (tick 3060) |
| 10500 | C up |
| 11000 | W down |
| 12000 | W up (decay tail) |
| …15000 | decision ticks only (quiet tail) |

CommandRecord count derivation (frozen): phase 1 boundaries 500..4000 inclusive
(71) + decay 4050, 4100 (2); phase 2 boundaries 7800, 7850, 7900, 7950 (4);
post-resume tail 9000 (deadline 0.0), 9050 inert→no record — wait, 9000 emits
the tail's exact 0.0 (1) and 9050 is inert (0); phase 3 boundaries 11000..11950
(20) + decay 12050, 12100 (2). TOTAL = 101. (If the real modules disagree with
this derivation, the deviation is recorded under `prediction_deviations` and
P3 counts assert the MEASURED module truth, never a re-tuned expectation.)

Frozen scene constants (visualization referents, harness-owned): body starts at
origin, heading east (+x, yaw π/2), integrated from the REAL walk sink's
CommandRecords at 50 ms steps; trunk cylinder at (x=3.0, z=-0.6), r=0.5,
top=8.0 (the climb REQUEST's declared visual referent — the selector that would
act on the intent is K-series and absent, so the body's walk is unchanged by
any intent; that IS the demonstration).

## FALSIFIERS (named now; any one firing kills THIS attempt's claim)

- **F-A IDENTITY DIVERGES**: any of the 17 `seam_records` pins re-hashes
  differently, or any of the five core modules diverges from its pin. Any hit fires.
- **F-B SUITE NOT GREEN**: either unmodified original suite fails in the
  hash-verified sandbox. Any hit fires.
- **F-C PINNED STATE TOUCHED**: sha256 of ANY of the five core modules
  (`climb_intent`/`input_mapper`/`focus_policy`/`session_flow`/
  `command_record`) differs before vs after the ENTIRE probe run (main run +
  teeth runs, each in its own sandbox copy; the shipped `seam_records/` bytes
  are never executable targets of mutation). Any hit fires.
- **F-D TOOTHLESS PROBE**: any teeth mutation (M1/M2/M3) that leaves the probe
  GREEN, or a fired mutation outside its predicted check family without an
  explained overlap. Any hit fires.
- **F-E SCOPE CREEP**: any file outside `contributions/MAT2-U05/` changed in
  the attempt checkout relative to base `2e2b8f5e`. Any hit fires.
- **F-F DELIVERY VIOLATION**: any cross-delivery (walk sink sees an
  IntentEvent, intent sink sees a CommandRecord), any undeclared surface call
  on either strict double, any delivered event off the v1 wire format, any
  delivery count/order deviation from P3, any phantom edge after recovery or
  reload, any fabricated retract. Any hit fires.
- **F-G CAPTURE GATE REJECTS**: `visual_gate.verify` returns
  `structurally_valid: false` for the built manifest, or any required
  view/pair/field is missing. Any hit fires.

**STOP RULE**: `seam_motion_probe.py` exits 0 with F-A..F-F measured GREEN,
`capture_build_seam.py` exits 0 with the gate receipt GREEN; receipts saved
under `evidence/`; then writes stop and the candidate is submitted for lead
publication to `review/MAT2-U05`. No tuning loop exists: if a falsifier fires,
the CLAIM is wrong and is reported as a failure — the pinned semantics are
never adjusted here to pass (that would be a lineage version bump, not this
card's authority).

## THE CAPTURE (frozen views and honest boundary)

One deterministic video (640x360, 20 fps, ffmpeg libx264 bitexact), six
back-to-back segments: three declared profile views × (diagnostic + clean per
tick over the 301-row trace):

1. "normal follow-camera distance" — harness-owned deterministic follow pose
   behind the integrated body (eye = body − 3.2 m along heading + 1.6 m up,
   target = body + 2.0 m ahead at ground level).
2. "obstructed and close-target views" — closer framing (eye = body − 1.8 m
   along heading + 1.1 m up, target = the trunk referent center at body height
   when the body is inside the declared close window x>=2.2, else 2.0 m ahead),
   showing the trunk referent and the intent stream at delivery/drop moments.
3. "repeatable inspection side view" — fixed bookmark: eye (1.5, 9.0, 9.0),
   target (1.8, 0.0, -0.2).

Diagnostic rows draw the three declared layers with labels: L1
input/state/tick display (decision tick, t_ms, walk held, intent held, channel
gate state, intents delivered/dropped THIS tick, CommandRecords THIS tick),
L2 camera target and frustum diagnostics (target, distance, 45° frustum rays),
L3 selected creature labels (monkey-01 anchor/heading/v) + the intent-stream
label (last delivered event or named drop). Clean rows draw the scene only
(depth-ordered; no diagnostics — the gate rejects a clean view containing any).

**HONEST BOUNDARY (declared, part of the freeze):** the pixels are a
deterministic CPU visualization of the recorded headless trace of the REAL
pinned seam modules; the body stream integrates the REAL walk records and the
intent banners/labels render REAL IntentEvents and named drops from the REAL
channel trace. These are NOT native engine frames and carry no V03/V07/V08
native-rendering claim; the camera poses are the harness-owned inspection law
declared above, not the FollowCamera product module. The native integrated
checkpoints stay with the integration lane.

## OWNERSHIP (declared before assembly)

- `contributions/MAT2-U05/PREREGISTRATION.md` — this file (frozen first).
- `contributions/MAT2-U05/card_task.json` — THIS card's contract for the
  visual gate (task_id "U05", profile controls/motion, the three views).
- `contributions/MAT2-U05/seam_motion_probe.py` — the motion leg probe
  (authored source; assembles the sandbox from `seam_records/`, runs the frozen
  timeline + teeth, writes `evidence/trace.jsonl`, `evidence/numerical_receipt.json`,
  `evidence/runtime_receipt.json`, `evidence/teeth_receipts/*.txt`,
  `qualification_receipt.json`).
- `contributions/MAT2-U05/capture_build_seam.py` — the capture builder
  (trace → `evidence/capture.mp4` + `evidence/capture_manifest.json` +
  `evidence/capture_receipt.json`, validated by the campaign's own gate).
- `contributions/MAT2-U05/seam_records/**` — the preserved ONT-U05 records leg
  (30 files, BYTE-EXACT from PR #179 @cdb0d81c == lineage 272e7bda for all
  pinned artifacts). READ-ONLY. Its `test_implementation.py` remains byte-exact:
  its F1–F4 re-run anywhere, but its F5 scope check names the ONT-U05 attempt
  checkout and is THAT attempt's historical measurement; THIS card's scope law
  is F-E here.
- `contributions/MAT2-U05/report.md` — the source-bound qualification receipt.
- `contributions/MAT2-U05/evidence/` — run outputs (trace, receipts, capture).

Nothing outside `contributions/MAT2-U05/` is written.

## APPLICABILITY BOUNDARY (declared now; no invented acceptance)

- Headless, CPU-only, injected integer-millisecond clocks. The run measures the
  SEAM's delivery discipline over the REAL modules (edges, gates, naming,
  versioning, exclusive sinks, reload cleanliness, walk-contract isolation) —
  the controls profile's task-owned subset. It does NOT measure live key feel,
  a selector state machine (K-series), climbing behavior, or any rendered
  engine state. Recorded honestly; the runtime lane's native actual-play
  evidence remains with the integration checkpoints, never passed by a fixture.
- The C12 contract: the 50 ms interval is the WALK seam's command cadence, not
  a latency guarantee; the probe records actual press→deliver call durations as
  runtime actuals with no derived latency claim. The intent channel adds no
  queue (synchronous delivery inside the press call — enforced structurally by
  the strict sink recording inside `emit`).
- LF/CRLF: sandbox and candidate artifacts use the git BLOB (LF) bytes; the
  byte-identity claims state that they hash those bytes.
- RUN_ID (frozen): `mat2-u05-seam-20260927-867dc0b1`.

---

## APPENDIX A (2026-09-27, BEFORE the first green run: a prediction DEVIATION record — the frozen body above is unchanged)

The frozen CommandRecord-count derivation in THE FROZEN TIMELINE said 101. On
the first instrumented run the REAL module measured 99. Root cause: the
derivation misread the walk seam's release-decay law. The module's actual law
(input_mapper.py `_apply_tail`, pinned bytes `7a36a45e…`): the FIRST boundary
after a release carries the linear sample `v0*(1-elapsed/100)` and the SECOND
carries EXACTLY 0.0 and ENDS the tail — there is no third tail record. The
frozen body's phase splits ("71+2" and "20+2" with three tail records each)
assumed three.

MEASURED module truth (frozen here as the corrected derivation, per the
stop rule: counts assert measured module truth, never a re-tuned expectation):

- phase 1: held boundaries 500..3950 (70, v0) + tail 4000 (v0, elapsed 0),
  4050 (0.0, ends) = 72
- phase 2: held boundaries 7800..7950 (4, v0); tail deferred across the pause
- post-resume: 9000 (0.0, deadline elapsed>=100, ends) = 1
- phase 3: held boundaries 11000..11950 (20, v0) + tail 12000 (v0), 12050
  (0.0, ends) = 22
- TOTAL = 99

The frozen body's per-event delivery/drop/repeat predictions are unchanged
and were re-derived independently of this arithmetic. The probe asserts
99 (`PREDICTED_WALK_RECORDS`) and carries this appendix's reference in the
C3 measured output. No pinned byte is adjusted; the module was right, the
paper derivation was wrong.
