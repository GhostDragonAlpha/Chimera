# PREREGISTRATION — I-U07-TRACE-FOLLOWUP (connect the accepted trace format to the existing input/camera test seam)

Card `I-U07-TRACE-FOLLOWUP` (planning id **U07**, depends on I-U07-TRACE merged
as PR #138, head `4d2ececc`), attempt
`8703cf9f00bf4e11add0060bcc85da03`, arrival
`arrival-f742dfbb88244565a6d973717bc05f26`, branch `branch-2`, working base for
runtime pins: seam sources pinned at `9afbddcd` (the same revision the parent
card's report cites: `input_mapper.py` 7a36a45e…, `follow_camera.py`
d61347f0…, `command_record.py` 67711759…). Frozen BEFORE any implementation
edit (Rule 0: statement, prediction, falsifier F1–F6).

## STATEMENT (a theory someone could disagree with)

The accepted four-stage trace module (`I-U07-TRACE/input_trace.py`, sha256
`c8f4e444…`, byte-identical to the PR #138 merge) can be CONNECTED — without
rewriting it and without editing production — to the EXISTING input/camera test
seam so that: (a) the real U01 `InputMapper` (pinned bytes, injected sink,
injected integer-millisecond monotonic clock) emits ACTUAL `input` and
`command_emitted` events in the accepted event format, one chain per emitted
CommandRecord whose `input` stage is the causal antecedent key-state
transition; (b) the two native stages (`simulation_consumed` — the ZOH tick
boundary in `gait_controller.hpp` — and `presented` — the engine's frame offer)
are structurally ABSENT from this Python seam, so the adapter itself can never
produce a four-stage chain: analysis through the accepted module REFUSES the
trace by name (`missing_stage`) and no latency number of any kind is produced;
(c) the existing camera test seam (pinned `MockEngine` freshness harness,
`GET /frame` returning `{"armed_after": <ack count>}`) supplies an ORDERING
fact and NO presentation timestamp, so no native `presented` time exists to
record from it; and (d) a caller who explicitly attaches real native-stage
observations on the same clock gets the accepted module's exact matched-stage
arithmetic — format-compatible end to end.

## PREDICTION (measurable, not yet measured)

1. Driving the pinned `InputMapper` through the adapter produces, for every
   CommandRecord the mapper actually emits, exactly one chain (a fresh `seq`)
   carrying an `input` event (the latest observed key-state transition at or
   before the emission, copied, never invented) and a `command_emitted` event
   whose payload is the actual record (`v_forward`, `yaw_rate`, `issued_tick`,
   `source == "u01_input_mapper"`), with `t(input) <= t(command)` on ONE
   injected monotonic integer-ms clock, and `issued_tick ==
   (t_command_ms * 300) // 1000` for every chain (the mapper's own documented
   derivation with no injected tick source).
2. Feeding the adapter's Python-only event stream to the ACCEPTED module's
   `parse_trace` raises `TraceRefused` with reason `missing_stage` and
   `missing == ["presented", "simulation_consumed"]`; the adapter's `analyze()`
   surfaces that refusal with `latency_output: None` — no segment or
   end-to-end latency is produced from the 2-stage trace.
3. With FIXTURE-LABELED caller-attached `simulation_consumed`/`presented`
   observations (planted integers, explicitly declared fixtures — NOT native
   claims), the accepted module's `chain_latencies`/`summarize` return exactly
   the planted segment and end-to-end values (bit-equal), and with no limits
   the verdict is `unqualified`, reason `p06_limits_absent` — the accepted
   module's own P06 law, unchanged.
4. An event on the camera harness' host wall clock (`time.perf_counter`, a
   different clock identity) merged into the seam trace makes the accepted
   `parse_trace` refuse `mixed_clock`; and the pinned existing camera harness
   proves its freshness CONTRACT (`armed_after >= ack_count` after a camera
   write) while carrying NO timestamp field — the camera test seam cannot
   supply a native presentation timestamp.
5. Determinism and headlessness: two identical adapter runs produce
   byte-identical event streams; `adapter.py` performs no wall-clock reads, no
   network, no window; its only I/O beyond caller data is reading its own
   pinned `reference/` bytes and materializing them, unmodified, into an OS
   temp directory in the canonical repo layout for import (documented).
6. Regression: the pinned EXISTING seam suites pass byte-unmodified in the
   materialized layout — `input_mapper_tests.py` (U01 falsifiers, verdict
   GREEN) and `follow_camera_tests.py` (U02, all unittest cases) — plus the
   accepted module's own 26 tests — proving the connection disturbs neither
   the seam nor the accepted module.

## FALSIFIER (named before the run)

Any of these fails the build:

- **F1** the adapter imports anything but the sibling accepted
  `../I-U07-TRACE/input_trace.py` (no vendored copy, no rewritten stand-in),
  and the module file it loads must match the accepted sha256 pin
  `c8f4e4442a3ceedecd9c636857eda92642d26ec535d45f2c91a3ce9fd4550a57`;
- **F2** the `input`/`command_emitted` events originate from anything but the
  pinned real sources (`input_mapper.py` 7a36a45e…,
  `command_record.py` 67711759… — byte-identical `reference/` extractions,
  hash-asserted by tests), or any reimplementation of the mapper/record logic
  appears in the owned files;
- **F3** any `simulation_consumed`/`presented` event originates from the
  adapter itself rather than explicit caller attachment, or a native
  timestamp is invented from the camera mock's DECLARED deadlines
  (1/60 s apply, 1/30 s frame period) or from `armed_after`;
- **F4** any latency number is produced from the Python-only 2-stage trace
  (the `missing_stage` refusal fails to fire), or an end-to-end latency pass
  is claimed from fixtures;
- **F5** any P06 limit is hardcoded, defaulted, or inferred anywhere in the
  owned files; qualification derives only from the accepted module's
  caller-data law;
- **F6** any pinned existing seam test or accepted-module test breaks, or the
  adapter silently tolerates a non-monotonic / non-integer injected clock
  (must refuse by name).

## SCOPE

Owned files only (`adapter.py`, `test_adapter.py`, `report.md`, `receipt.json`,
`PREREGISTRATION.md`, plus `reference/` pinned extractions with
`EXTRACTION_LEDGER.json` and a `proposed.patch`). stdlib only, Python 3.11+.
No production edits, no network, no GUI, no engine starts, no GPU; CPU tests
bounded well under 120 s and 16 MiB. No live measurements are claimed; every
fixture is labeled a fixture; the native gates of U07 (P06 limits, repeatable
scenes, actual play) remain OPEN.
