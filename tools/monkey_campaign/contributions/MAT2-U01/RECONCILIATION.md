# RECONCILIATION — MAT2-U01: the existing input/command seam, re-verified at the current criteria

Attempt `c1488004ef62400389ba98a46837e5b7`, agent
`arrival-e922be0c34ef46ff84f504eb27e99178`, criteria
`bda3feb8fa32838f8799a83939af08a2d70c6069ec5af7b6c355b759f5aa019e`.
Contribution class: **reconciliation + scoped verification** (card brief step 1
"Reconcile existing commits, diagnostics and receipts first; reuse verified
work. Do not repeat completed implementation."). No new mapper or seam code is
authored; the play lineage is not duplicated or modified.

## 1. The accepted prior work

- ONT-U01 (planning U01, same definition) was implemented, lead-ACCEPTED and
  merged: PR #147 head `9ad277d73268476a51809becc36c021e020d8d35`, merged to
  `astra/gait-capture` via PR #169 merge `048b63f4`. Its
  `qualification_receipt.json` (on the tip at
  `tools/monkey_campaign/contributions/ONT-U01/qualification_receipt.json`)
  records `done_when_verified: true`, `profile_verified: true`, 9/9 frozen
  controls checks, and an independent non-author review (reviewer `016ddbe3`,
  PASS, bit-exact capture rebuild).
- A later lead CHANGES_REQUIRED (`msg-6764166d`) produced the real-run
  correction leg (`PREREGISTRATION_REAL_RUN.md` `da5dba00…`, correction
  attempt `29bb1ccc…`), recorded in the same receipt: emission leg REAL and
  bounded (138 records, emit-only, in-band, 50 ms cadence, decay to exactly
  0.0 then silence); body observed ONLY through the engine's own state/frame
  path — bit-identical horizontal centroid across the whole command stream, no
  teleportation observed; receiver capability measured (engine refuses gait
  enablement; no route consumes V1 speed/heading records) so the
  input→body-EXECUTION leg stays honestly INCOMPLETE with the integrated
  playable-runtime checkpoint in the integration lane.

## 2. Clause identity between scopes (observed, then used)

| item | ONT-U01 (scope `01ea5cdd…`) | MAT2-U01 (scope `cb5475f8…`) | equal? |
|---|---|---|---|
| `definition_raw_sha256` | `57ded6eb2f2cc6aa914d6f68c8efb55b215790fc7a9d0baa5dfd2c49fd1465c1` | same | YES |
| done_when | "Input emits bounded speed/heading commands at the existing 20 Hz boundary, without state teleportation" | same | YES |
| C12 | "20 Hz implies a 50 ms command interval, not an end-to-end latency guarantee" | same | YES |
| observation | "Do not require retraining for a UI remapping" | same | YES |
| profile | controls / motion, falsifier "A stuck command, camera-induced body movement, unreadable required target, concealed obstruction or unbound timing evidence fails." | same | YES |
| dependencies | ONT-P01, ONT-P03 (DONE) | MAT2-P01 (DONE, #192 merged 2026-09-27T08:47:35Z), MAT2-P03 (DONE, #194 merged 2026-09-27T09:36:08Z) | satisfied in current board |

## 3. Pinned bytes — unchanged at the current integration tip

Extracted byte-exact from `origin/astra/gait-capture` at `b0108a364a560909c6c396bd916ec15369c27d7e`
into `reconcile/pinned_seam/`; all seven hashes match the accepted receipt's
`pinned_lineage` table (fresh run `evidence/verification_receipt.json`,
probe 3: **7/7 match**):

| path | sha256 | role |
|---|---|---|
| `tools/monkey_campaign/product/input_mapper.py` | `7a36a45ead6637d9ba5659ea43b54a6b424803c8e57d02720ac970b42cfe6b44` | the qualified subject (the M-U01 mapper) |
| `tools/science_funnel/typeb_export/command_record.py` | `6771175933ad20ac6d20c360df96f6a9729a56deb31c58a13be5e76e1cc4355e` | the EXISTING CommandRecord v1 seam (the "67711759 lineage") |
| `tools/monkey_campaign/product/follow_camera.py` | `d61347f085644e66a5f29ab1e689e2bbd2cd5ff04099856ade70e5da90a791a7` | declared camera referent |
| `tools/monkey_campaign/product/input_mapper_tests.py` | `95f44e90998f9728802ff5f7cb8628f18f2026bef1fb2c4de681e5253381216e` | frozen falsifier module F1–F6 |
| `tools/monkey_campaign/agents/U01_input/PREREGISTRATION.md` | `0aadc3cd5fec7e7bd0a7aba0bcfa2a5d05edf8fcb6805eda2ecae92d4d3d1b5f` | preserved frozen U01 prereg |
| `tools/monkey_campaign/agents/U01_input/discovery_note.md` | `38efdf393bd03b7b1260896e917231f2968963a501a180f4fc01491a02b30849` | preserved seam discovery record |
| `tools/monkey_campaign/agents/U01_input/receipts/input_mapper_tests_20260924.txt` | `00c73e346298f3880c61f4f30c77f490565c6f630e61f9bf414839ae6f6fa84c` | preserved GREEN falsifier receipt |

The `input_mapper.py` at the tip does NOT exist as a production-path file;
the seam lives in the merged contributions tree (integration cards own
production paths). The reconciliation claims nothing about production-path
installation.

## 4. Fresh scoped verification (CPU-only, `python -B`, stdlib only)

Frozen BEFORE running (`PREREGISTRATION.md` `f2c80ee05841c7dab97f1fe093a85b40dad5dbf500211179cdbf42347af46c8d`,
verifier `verify_pinned_seam.py` `8ca6017a016ae0f590214de1820b6407c9af075df46344d47b79ae52ee044df6`):

1. FAILING-FIRST mutant (`reconcile/mutant_seam/`, only change
   `INTERVAL_MS = 50` → `40`): suite **FAIL, exit 1, 3 falsifier checks fired**
   (`F3a` held-key records not exactly 50 ms apart, `F3c` ticks inside the
   interval now emit, `F5c` bounds/clock after remap) — the falsifier suite is
   load-bearing, not vacuous.
2. Pinned run over the byte-identical subject: **exit 0, 30 PASS / 0 FAIL,
   VERDICT GREEN** (`evidence/pinned_falsifier_run_full.txt`
   `61b806f14c405993bf6c10f447b7b9e10e12576c8508ea307fd2700b59f86855`),
   identical to the preserved receipt `00c73e34…` (30 PASS / 0 FAIL).
3. Lineage assertion: **7/7** pinned hashes match.

All three frozen predictions (P1, P2, P3) HELD; falsifiers F-A, F-B, F-C did
not fire; F-D (clause divergence) did not fire (section 2 table, observed
before freezing). No prediction deviations. Failures observed: none in the
pinned run; the 3 mutant FAILs are the deliberate failing-first fixture.

## 5. Clause-to-evidence map (done_when, decomposed)

| clause | evidence (accepted lineage, merged #169) | fresh scoped re-verification (this attempt) |
|---|---|---|
| "Input emits … commands" | mapper emits `CommandRecord` v1 via `sink.emit` ONLY (F1a/b: 9 calls, 9 records, 0 non-emit sink calls; accepted 5000-schedule fuzz: 117,142 records, 0 violations, 0 non-emit sink calls) | F1 re-passed over pinned bytes (30/30 includes F1a–F1d) |
| "bounded speed" | `v_forward ∈ [0, 0.763625]` — the seam's own measured in-band ceiling (`command_record.py:66`), mapper never demands out-of-band (F2 fuzz, 0 violations) | F2 re-passed over pinned bytes |
| "bounded … heading" | `|yaw_rate| ≤ 1.6` declared input-side steer bound; yaw CARRIED with NO machinery route at v1 (`RANGES`, F6f, adapter `routed_yaw_rate=False`) | F6f/F5d re-passed over pinned bytes |
| "at the existing 20 Hz boundary" | the EXISTING seam's own clock (`HOLD_TICKS=15`, `POLICY_HZ=20`, `PHYSICS_HZ=300` in pinned `command_record.py`); mapper `INTERVAL_MS=50` EXACT under the injected clock (F3a–e); accepted real-run cadence with the one 67 ms late boundary FIRED and recorded (no burst) | F3 re-passed; mutant run proves the 50 ms bound is actually enforced |
| "without state teleportation" | F1 no-teleport invariant (emit-only, imports exactly the declared set, no pose/state route); accepted real-run leg: engine-observed body bit-identical through the whole command stream | F1c/F1d re-passed over pinned bytes; execution-leg boundary carried honestly below |
| C12: "50 ms command interval, not an end-to-end latency guarantee" | `INTERVAL_MS=50` exact; consumer-side expiry `VALID_MS=100` (F6h: valid 95 ms, expired 105 ms); accepted probe recorded cadence, never latency claims | F3/F6h re-passed |
| observation: remap without retraining | bindings are DATA (`DEFAULT_BINDINGS`); remap changes emitted VALUES only (F5a–d); refusals by name, never silent (F6e) | F5/F6e re-passed |

Profile legs (controls/motion): the visual/camera probes (clean view, the 16
camera fields, three views) were exercised by the ACCEPTED ONT-U01
qualification at these exact subject bytes (capture `a51fcbc8…`, labeled
SYNTHETIC — deterministic CPU visualization of the headless trace, NOT native
engine frames; real-run capture `846f0b32…` with `structurally_valid true`,
`visual_acceptance false by law`). This reconciliation manufactures NO new
visual capture: the subject bytes are unchanged (7/7 hashes), so a new capture
would add no information and is not claimed as new evidence.

## 6. Evidence class and honest boundary

COMPONENT-LEVEL evidence over the REAL pinned seam bytes — the class the
accepted ONT-U01 review explicitly scoped as satisfying this interface-subject
clause ("the done_when subject is the input-to-command seam itself and the
card profile explicitly does not require downstream skills to accept an
upstream interface"). NOT an integrated-application claim. The
input→body-EXECUTION leg remains INCOMPLETE exactly as measured in the
accepted correction (the pinned engine refuses gait enablement and has no
route consuming V1 speed/heading records); the native playable-runtime
checkpoint stays with the integration lane. Nothing here claims walking,
climbing, game completion, or human acceptance.

## 7. What would have changed the answer

If the pinned hashes had drifted (F-A), the pinned suite had failed (F-B), the
mutant had passed (F-C), or any clause had differed between scopes (F-D), this
reconciliation would be withdrawn and the card would need fresh implementation.
None fired. Counts: lineage 7/7; pinned falsifiers 30 PASS / 0 FAIL; mutant
failing-first 3 FAIL / exit 1; frozen predictions 3/3 HELD; dependencies 2/2
DONE on the current board.
