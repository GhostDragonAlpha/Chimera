# I-U07-TRACE — report (trace ingestion + matched-stage latency analysis)

Card `I-U07-TRACE` (planning id **U07** — "Measure controls during actual play";
this card is the explicitly authorized PREPARATORY module), attempt
`9b94126614af41238eefc4c64682acbd`, arrival `arrival-ec97e63be318447499de475cc02077cd`,
branch `branch-5`, base revision `9afbddcd90164b5544a16fd0bc72278d985eb6e3`
(source repo `E:/ChimeraWork/monkey-play-20260924`, read via `git show` only —
zero checkouts, zero working-tree changes there). Prior attempts
(0444b44c/98468c4b/d3f1d76c + this resume) left no recoverable artifacts; this
attempt implements from the pinned brief. PREREGISTRATION.md frozen BEFORE any
implementation edit (Rule 0: statement, prediction, falsifier F1–F5).

## 1. What was built

- **`input_trace.py`** (stdlib-only, Python 3.11+, headless/deterministic by
  construction — no wall clock, no window, no network; verified by test):
  - The explicit four-stage event record: `seq` (chain id), `stage`
    (`input` → `command_emitted` → `simulation_consumed` → `presented`), `t`
    (finite) + `unit` (`ms`/`s`, per event, converted canonically; original
    value preserved — units are data), `clock` identity, `run` identity,
    `build` identity, opaque `payload`.
  - Strict parsing (`parse_trace`) refusing the WHOLE trace by named reason:
    `empty_trace, record_not_object, missing_field, bad_type,
    non_finite_time, unknown_stage, bad_unit, duplicate_seq_stage,
    mixed_clock, mixed_run, mixed_build, missing_stage, reversed_stage_order`
    (equal stage timestamps are legal at finite clock resolution; strictly
    earlier is reversal).
  - Matched-stage latencies (`chain_latencies`): a latency is EXACTLY the
    difference of two matched-stage timestamps of one complete chain;
    `chain_latencies` independently re-refuses partial chains even if handed
    pre-parsed events (belt-and-braces for falsifier F1).
  - `summarize`: per-segment + end-to-end stats (nearest-rank percentiles,
    method declared in output), and a qualification verdict that derives ONLY
    from explicit caller-supplied limits; **absent limits ⇒ `unqualified`
    with reason `p06_limits_absent`** (P06 "Choose release acceptance limits"
    is an unresolved decision card — no limit is inferred, defaulted, or
    hardcoded). Unknown/bad limit keys refuse rather than guess.
  - CLI (`--input FILE` JSONL/JSON, optional `--limits FILE`, optional
    `--output`): exit 0 + full JSON summary, or exit 2 + a refusal object
    that contains **no latency numbers at all**.

- **`test_input_trace.py`**: 20 tests / 4 suites — AnalyticExactness (planted
  intervals return exactly; hand-computed p50/p95/p99; ms/s conversion exact;
  interleaved arrival order), Refusals (every named break + no-latency-on-
  refusal), Qualification (unqualified-without-limits; pass/fail strictly
  against caller data; unknown/bad limits refuse), CLI (round-trips; refusal
  emits no numbers), HeadlessLaw (banned tokens absent; deterministic
  byte-identical output). **Result: 20/20 OK in 0.51 s** (bound: 120 s).

- **`reference/`**: pinned extractions with `EXTRACTION_LEDGER.json`
  (path + base revision + sha256 per file): `input_mapper.py`
  (7a36a45e…, 18,349 B), `follow_camera.py` (d61347f0…, 33,410 B),
  `typeb_export/command_record.py` (67711759…, 12,095 B). Read-only after
  extraction.

## 2. The APIs this was derived from (pinned 9afbddcd, cited not invented)

- `tools/monkey_campaign/product/input_mapper.py` — THE seam: emits versioned
  `CommandRecord`s (`v_forward` m/s ≥ 0, `yaw_rate` rad/s carried without
  authority, `issued_tick`, `source`) into an injected sink at 20 Hz
  (`INTERVAL_MS = 50`, HOLD_TICKS = 15 over 300 Hz physics); the clock is
  INJECTED integer milliseconds; `SOURCE_ID = "u01_input_mapper"`. Its two
  collapsed-by-naive-mappers states (no record = inert; `v_forward=0.0` =
  live zero-advance) both matter for stage attribution.
- `tools/science_funnel/typeb_export/command_record.py` — CommandRecord v1
  freeze + projection law; `issued_tick` is the physics tick of the
  zero-order-hold boundary (the natural `simulation_consumed` correlation).
- `tools/monkey_campaign/product/follow_camera.py` — reads via the frozen
  HTTP contract (`GET /frame` freshness harness; TICK_PERIOD 0.05 s); the
  `presented` stage belongs at the frame offer, not at camera math.

## 3. Insertion-point patch PROPOSAL (text only — no production edits made)

Four seams, each an injected recorder call — no seam changes behavior; the
tracer is a caller-supplied sink (the module itself never clocks):

1. **`input`** — in `input_mapper.py`'s key-state change handling: when a
   binding transitions, call `tracer.record(seq=n, stage="input", t=clock_ms(),
   clock=..., run=..., build=...)` with the injected clock the mapper already
   receives (its API already takes integer ms — no new clock source).
2. **`command_emitted`** — wrap the injected sink: a `TraceSink` object whose
   `emit(record)` forwards to the real sink and records
   `stage="command_emitted"`, `payload={"v_forward": record.v_forward,
   "issued_tick": record.issued_tick, "source": record.source}`. This is ~10
   lines at the seam, uses the SAME injected clock, and adds zero authority.
3. **`simulation_consumed`** — at the ZOH boundary in
   `gait_controller.hpp`/engine tick where `commanded_target_velocity_x` is
   applied (the 15-tick hold edge): record `stage="simulation_consumed"`,
   `payload={"tick": issued_tick}`. Engine-side; proposed for the native leg,
   out of scope for this Python card.
4. **`presented`** — in the follow_camera/frame freshness path (`GET /frame`
   harness): record `stage="presented"` with the frame id, on the SAME clock
   identity as 1–3 (one clock per trace is enforced by `parse_trace`; mixed
   clocks refuse, so the integrator must thread one clock through all four
   seams — that constraint is deliberate).

Chains correlate by `seq` = the input-transition counter; the `payload`s
above make audit possible without the tracer interpreting them.

## 4. Falsifier self-check (PREREGISTRATION F1–F5)

- **F1 invented latency:** impossible by construction — arithmetic runs only
  on complete matched chains; `chain_latencies` re-refuses partials; refused
  CLI output contains no latency fields (tested).
- **F2 silent clock/build mixing:** refused by name (`mixed_clock/run/build`)
  — tested.
- **F3 fixtures labeled as play acceptance:** this report labels every trace
  a FIXTURE; no live measurement exists here; U07's native gates (P06 limits,
  repeatable scenes, actual play) remain OPEN.
- **F4 wall clock / window / hidden IO:** source scanned by test for banned
  tokens; deterministic byte-identical output asserted.
- **F5 limits from anywhere but caller data:** only the `--limits` file or
  explicit `limits=` argument; absent ⇒ unqualified; unknown keys refuse —
  tested.

## 5. Remaining gates (this card closes none of them)

1. P06 decision: freeze the release acceptance limits (owner: operator/lead —
   a decision card, not derivable here).
2. Native integration of the four recorder seams (engine-side
   `simulation_consumed` is C++ work under the frozen-service law).
3. Actual-play capture on repeatable scenes → trace files → this module
   computes; qualification only then, against the P06 numbers.
4. U07's visual/native profile (`controls`, checkpoint V03) stays with its
   card — this preparatory module satisfies no parent gate by itself.

## 6. Next implementation step

Wire the `TraceSink` wrapper (seam 2) into the pinned `input_mapper.py` call
site inside a scoped follow-up card once this module is reviewed/merged; the
engine-side seam 3 goes to the native runtime lane. No further work is
unblocked by this card alone.

---

# CORRECTION — attempt 1b797ab5558149919bfe4b85066d484c (2026-09-25)

Responds to the lead's CHANGES REQUIRED on PR #121. Base adopted
byte-identical (input_trace.py sha256 `4da6f5de…`); prior 20/20 suite green
pre-fix; failing-first proof recorded (4/5 new tests FAILED on base —
`failing_first_base.txt`).

## Fixes

1. **`time_overflow`**: parse_trace now refuses when `t * UNITS_TO_MS[unit]`
   is not finite (the lead's `t=1e308 s` reproducer → named refusal at
   parse; no summary is reachable).
2. **`latency_overflow`**: chain_latencies refuses when any segment
   difference is non-finite — NaN can never reach a statistic.
3. **Empty limits**: `summarize(events, limits={})` → `unqualified` with
   reason `p06_limits_empty` (absent stays `p06_limits_absent`); the vacuous
   zero-check `pass` is structurally impossible.
4. CLI regression pinned: refusals exit 2 with the named reason and
   `latency_output: null` — no latency values (tested end-to-end on the
   reproducer trace).

## Verification

`python -B -m unittest test_input_trace test_correction` → **25/25 OK
(20 prior + 5 correction), run twice, deterministic**. No prior test broken;
no NaN/inf can reach a summary; empty limits never pass; synthetic traces
only (no device claim, no production edits).

---

# SECOND CORRECTION — attempt 2321d1811a92415db7863826702e2d5c (2026-09-25, later)

Returns the independently reviewed candidate (source `0a84cd77…`, tests
`b77fe596…` — review msg-a3856ac4: 26 tests pass, two-chain overflow CLI
exits 2 `statistics_overflow`, `latency_output` null) WITH the reviewer's
documentation corrections applied, from this attempt's isolated workspace:

1. **Statistics-accumulation overflow fixed** (distinct from the first
   correction's unit-conversion overflow): two finite chains
   [0,0,0,1e308] ms — finite per-chain latencies whose statistics sum
   overflows — now refuse by name `statistics_overflow`; the regression
   `test_fsum_overflow_two_chains` is in the suite.
2. **Source comment corrected**: sum() is not claimed more stable than
   math.fsum(); the implemented approach detects a non-finite sum and refuses
   it (sum() overflows silently to inf = detectable; fsum raises an
   uncontrolled OverflowError mid-statistic).
3. **Refusal details accurately labeled**: `operation: "sum"` (the stale
   `reason: "fsum_overflow"` named an unused operation and is removed).
4. **Preregistration scope separated** (appended, chronological): statistics
   accumulation ≠ unit conversion; the first addendum's text conflated them.
5. Prior correction tests preserved (test_correction.py byte-identical to the
   first correction); PR #130 (671-commit dirty head) NOT used — this handoff
   contains only the trace deliverables + prior correction tests.

Measured in this workspace: 26/26 tests, CLI reproducer exit 2 with
`statistics_overflow` + `latency_output: null`, both lead reproducer probes
(conversion refusal + statistics refusal) print their named refusals.
