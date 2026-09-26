# I-U07-TRACE-FOLLOWUP — report (accepted trace format connected to the existing input/camera test seam)

Card `I-U07-TRACE-FOLLOWUP` (planning id **U07**; depends on **I-U07-TRACE**,
merged as PR #138, head `4d2ececc`), attempt
`8703cf9f00bf4e11add0060bcc85da03`, arrival
`arrival-f742dfbb88244565a6d973717bc05f26`, branch `branch-2`
(`c525b82c7c3ce0128565424764293a3c85811ab3`), isolated attempt checkout only —
zero writes to the shared onboarding checkout or any other attempt.
`PREREGISTRATION.md` frozen BEFORE any implementation edit (statement,
predictions 1–6, falsifier F1–F6).

## 1. What was built

- **`adapter.py`** — the seam connection. It owns NO trace law of its own:
  - imports the ACCEPTED module from the sibling merged contribution
    (`../I-U07-TRACE/input_trace.py`) via `load_accepted_trace_module()` —
    never a vendored copy (a local `input_trace.py` is absent, asserted by
    test); the loaded bytes are pinned to the PR #138 merge
    (`c8f4e4442a3ceedecd9c636857eda92642d26ec535d45f2c91a3ce9fd4550a57`).
  - imports the REAL U01 mapper from `reference/` pins (see below),
    materialized byte-identically into an OS temp directory in the canonical
    repo layout so the unmodified files' own `from tools.science_funnel…`
    import resolves. Every pin hash is asserted at materialization;
    a mismatch refuses by name (`pinned_source_hash_mismatch`).
  - `TraceSink` wraps ANY existing sink: forwards `emit(record)` untouched
    (the mapper's no-teleport law is unchanged) and stamps the actual
    CommandRecord as the `command_emitted` stage at the EXACT boundary time
    the mapper was driven at.
  - `SeamTracer` drives the real `InputMapper` on ONE injected
    integer-millisecond monotonic clock (the mapper's own contract), one
    clock read per seam event. Chain law: every emitted CommandRecord opens
    one fresh `seq`; its `input` stage is the latest observed key-state
    transition (copied, `transition_index` records lawful sharing by
    re-issued commands). Refusals: `command_without_input_antecedent`,
    `non_integer_clock`, `clock_regression`, `bad_identity`, `bad_clock`,
    `not_a_native_stage`, `unknown_seq`, `pinned_source_missing`,
    `pinned_source_hash_mismatch`, `accepted_module_missing`.
  - `analyze()` hands the trace to the accepted `parse_trace`/`summarize` and
    surfaces the verdict WHATEVER it is: the Python-seam trace refuses
    (`missing_stage`) and is reported with `latency_output: null`. Limits are
    caller data only; they pass through unmodified (absent → the accepted
    module's own `unqualified`/`p06_limits_absent`).
  - `attach_native_stage(seq, stage, t)` exists ONLY for explicit caller
    attachment of native observations; the adapter itself never calls it.
- **`test_adapter.py`** — 30 tests / 6 suites (F1–F6 below). **Result:
  30/30 OK, run three times (0.90 s, 0.97 s, 0.98 s; bound 120 s),
  `python -B -m unittest test_adapter` and `python -B test_adapter.py`,
  exit 0, byte-identical verdicts.**
- **`reference/`** — pinned byte-identical extractions + `EXTRACTION_LEDGER.json`.
  Revision `9afbddcd` — the SAME revision the accepted I-U07-TRACE report cites
  for its own pinned extractions; all five hashes match that report's ledger
  citations exactly (`input_mapper.py` 7a36a45e… 18,349 B; `follow_camera.py`
  d61347f0… 33,410 B; `command_record.py` 67711759… 12,095 B; plus the two
  EXISTING seam test modules `input_mapper_tests.py` 95f44e90… 15,154 B and
  `follow_camera_tests.py` 4d7516… 27,743 B, pinned so they run unmodified as
  regression).

## 2. The seam as found (all citations from the pinned sources)

- `tools/monkey_campaign/product/input_mapper.py` — THE input seam: versioned
  CommandRecords (`v_forward` m/s ≥ 0, `yaw_rate` rad/s carried,
  `issued_tick`, `source="u01_input_mapper"`) into an injected sink at 20 Hz
  (`INTERVAL_MS = 50`, HOLD_TICKS 15 over 300 Hz physics); the clock is
  INJECTED integer milliseconds; idle emits NOTHING, held `S` emits LIVE
  ZEROS — both traced here (`test_f2_both_seam_states…`).
- `tools/monkey_campaign/product/input_mapper_tests.py` — the existing input
  test seam: injected ms clock + `MockSink`, falsifiers F1–F6.
- `tools/monkey_campaign/product/follow_camera.py` + `follow_camera_tests.py`
  — the existing camera test seam: `GET /frame` freshness harness; the mock
  answers `{"armed_after": <ack count>}` so tests can prove the frame
  postdates the last camera ack. **That answer is an ordering fact and carries
  NO timestamp field** (asserted: `set(doc.keys()) == {"armed_after"}`); its
  apply/frame deadlines (1/60 s, 1/30 s) are the mock's DECLARED constants —
  using them as a `presented` time would be fabrication, and none is.

## 3. The connection (explicit missing native stages)

Trace shape emitted by driving the real mapper (fixture scenario, real
records, one clock `injected_ms`, caller-set `run`/`build`):

    seq  stage            t      payload (abridged)
    0    input            1000   {press W, action forward, transition_index 0}
    0    command_emitted  1050   {v_forward 0.763625, yaw_rate 0.0, issued_tick 315, source u01_input_mapper}
    1    input            1100   {press A, transition_index 1}
    1    command_emitted  1150   {v_forward 0.763625, yaw_rate 1.6, …}
    …    (decay sample, deadline zero, live zero — 7 chains in the scenario)

- **`simulation_consumed`** — native only: the ZOH tick boundary in
  `gait_controller.hpp` (engine-side; the parent card's insertion-point
  proposal §3). NO Python source exists; the adapter never emits it.
- **`presented`** — native only: the engine's frame offer. The existing camera
  harness yields `armed_after` (ordering), never a timestamp; the adapter
  never emits it.
- Consequence, enforced by the ACCEPTED module itself: the seam's 2-stage
  trace is REFUSED `missing_stage` (missing `["presented",
  "simulation_consumed"]`) with `latency_output: null` — no segment or
  end-to-end latency exists on this seam, and none is manufactured.

## 4. Verification (exact commands, this attempt workspace)

```
cd <attempt>/checkout/tools/monkey_campaign/contributions/I-U07-TRACE-FOLLOWUP
python -B -m unittest test_adapter -v     # 30/30 OK (0.900 s) — run 1
python -B -m unittest test_adapter        # 30/30 OK (0.972 s) — run 2, identical
python -B test_adapter.py                 # 30/30 OK (0.978 s), exit 0
```
Evidence transcript: `test_run_evidence.txt`
(sha256 `32aa12ff6b280563d4ebbb3dd282ab7c97257ad6f13cd27a642e7b3d626f569b`).
Highlights (each pinned by a named test):

1. Payloads of all chains equal the mapper's ACTUAL emissions
   (`inner_sink.records`), `source == "u01_input_mapper"`, and
   `issued_tick == (t_command_ms * 300) // 1000` for every chain.
2. Causal matching: `t(input) ≤ t(command)` per chain, integer ms, one
   clock/run/build; two identical runs are byte-identical.
3. The accepted module refuses the 2-stage trace `missing_stage`; the
   refusal text carries no latency field names or numbers.
4. FIXTURE-labeled attached native stages (planted +5 ms/+37 ms, payloads
   marked "NOT native evidence") flow through the accepted module to
   bit-equal segment values; verdict with no limits is `unqualified`
   (`p06_limits_absent`), with `{}` it is `p06_limits_empty`, with caller
   limits it is `pass`/`fail` against exactly those numbers; unknown limit
   keys refuse (`unknown_limit_key`, surfaced with `latency_output: null`).
5. A REAL `perf_counter` reading from the camera harness' clock domain,
   merged into the seam trace, refuses `mixed_clock` — the naive "one trace
   from both harnesses" is exactly what the law forbids.
6. Camera seam facts: freshness contract holds (`armed_after ≥ ack_count`
   after a write) AND the frame answer has no timestamp-like field; the
   mock's deadlines are the declared constants and stay constants.
7. Regression (byte-unmodified pinned suites, subprocess-isolated):
   `input_mapper_tests.py` → `VERDICT: GREEN`, exit 0;
   `follow_camera_tests.py` → unittest OK, exit 0; the accepted module's own
   `test_input_trace` + `test_correction` → OK (26 tests), exit 0.
8. Headless law: `adapter.py`'s full import set is exactly
   {__future__, importlib, shutil, sys, tempfile, pathlib, typing, hashlib}
   (AST-checked); no wall clock, network, or window anywhere in it.

## 5. Falsifier self-check (F1–F6)

- **F1 stand-in instead of accepted module:** impossible by construction —
  the sibling path is the only import target; a vendored copy is asserted
  absent; bytes are pinned to PR #138 (`test_f1_*`).
- **F2 rewritten seam:** all events derive from the pinned byte-exact real
  sources (`test_f2_pinned_sources_are_byte_exact`, hash-pinned payloads).
- **F3 native qualification from a fixture / invented native stage:** the
  adapter structurally cannot emit native stages (`not_a_native_stage`);
  fixtures are labeled in-payload; the camera harness is pinned to an
  ordering-only contract (`test_f3_*`, `test_f4_camera_clock…`).
- **F4 fabricated latency pass:** the 2-stage trace refuses with
  `latency_output: null` (`test_f4_two_stage_trace_is_refused_missing_stage`,
  `test_f4_refusal_output_carries_no_latency_numbers`).
- **F5 fabricated P06:** no limit literal exists in the owned files; verdicts
  come only from the accepted module's caller-data law (`test_f5_*`).
- **F6 regression/silent misuse:** all three existing suites stay green;
  non-integer/regressed clocks refuse by name (`test_f6_*`).

## 6. Remaining gates (this card closes none of them)

1. P06 (unresolved decision card): release acceptance limits — still open.
2. Native recorder seams in the engine (`simulation_consumed` at the ZOH
   boundary; `presented` at the frame offer) — still proposal-only (parent
   card §3); until they exist, end-to-end latency is UNMEASURABLE, not just
   unmeasured.
3. One-clock threading through all four seams in a live run + repeatable
   scenes + actual play (U07's native gates).

## 7. Artifacts (sha256, bytes)

| file | sha256 |
|---|---|
| `adapter.py` | `8522cbefb176fbd512f7191dfc79e8ff6dd45d9ed51fe4d34b23c307829df723` |
| `test_adapter.py` | `668ba733e92225503d1a051ba650192d7dad0ecb7f75486fc8e1ed54e928fb17` |
| `PREREGISTRATION.md` | `4187261ea8c7aca8b46b959bb6cd6cef710e1ecb208feee9e8ed6a9a678f1b0c` |
| `report.md` | (this file; sha256 travels in the submission artifacts — a file cannot contain its own hash) |
| `reference/EXTRACTION_LEDGER.json` | `af152032c4c57e445569ecab0d05706a93106dfdd98fafe911a1c407aac4e46a` |
| `reference/…/input_mapper.py` | `7a36a45ead6637d9ba5659ea43b54a6b424803c8e57d02720ac970b42cfe6b44` |
| `reference/…/follow_camera.py` | `d61347f085644e66a5f29ab1e689e2bbd2cd5ff04099856ade70e5da90a791a7` |
| `reference/…/input_mapper_tests.py` | `95f44e90998f9728802ff5f7cb8628f18f2026bef1fb2c4de681e5253381216e` |
| `reference/…/follow_camera_tests.py` | `4d75164ff6a16bf0d817332b7c5229513750782727ad1a23911025dc93d31b27` |
| `reference/…/command_record.py` | `6771175933ad20ac6d20c360df96f6a9729a56deb31c58a13be5e76e1cc4355e` |
| `test_run_evidence.txt` | `32aa12ff6b280563d4ebbb3dd282ab7c97257ad6f13cd27a642e7b3d626f569b` |
| `proposed.patch` | `e8817276e4fff9a57ba905f963c3eb5597b12828fed21cab298ee0a0bb40dbd5` |
| `receipt.json` | `5624b53a3125b756862db053e28707bdcf35539f4fb85bacb3a080dfe628a7fb` |

No live measurement, no native qualification, and no P06 limit is claimed
anywhere above; every fixture is labeled a fixture.
