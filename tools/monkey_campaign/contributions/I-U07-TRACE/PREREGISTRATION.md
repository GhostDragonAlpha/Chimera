# PREREGISTRATION — I-U07-TRACE (input trace ingestion + latency analysis)

Card `I-U07-TRACE` (planning id **U07**, prep for P06-limited play measurement),
attempt `9b94126614af41238eefc4c64682acbd`, arrival
`arrival-ec97e63be318447499de475cc02077cd`, branch `branch-5`, base revision
`9afbddcd90164b5544a16fd0bc72278d985eb6e3` (source repo `E:/ChimeraWork/monkey-play-20260924`,
read via `git show` only). Frozen BEFORE any implementation edits.

## STATEMENT (a theory someone could disagree with)

The four stages of the input pipeline — `input` (player intent observed),
`command_emitted` (a CommandRecord handed to the seam sink), `simulation_consumed`
(the physics tick that zero-order-holds it), `presented` (a frame containing that
tick offered to the player) — can be measured as one strictly-ordered chain per
input sequence number, on ONE clock identity and ONE run/build identity, with
units carried explicitly; every latency is then exactly the difference of two
matched-stage timestamps, and nothing else. Any trace that cannot satisfy
matching (missing stage, duplicate seq, reversed order, mixed clock/run/build,
non-finite time) carries NO latency information and must be refused whole, not
patched statistically.

## PREDICTION (measurable, not yet measured)

1. On a hand-built analytic trace of N complete 4-stage chains with known exact
   intervals, this module's computed segment and end-to-end latencies equal the
   planted values exactly (bit-equal float differences of the planted numbers),
   and its p50/p95/p99/order statistics equal hand-computed values.
2. Deliberately broken traces (missing stage, mixed clock, mixed build, duplicate
   seq, NaN/inf time, reversed stage order, empty input) each produce a NAMED
   refusal and produce NO latency output.
3. With no P06 limits supplied (P06 is an unresolved decision card), the
   qualification verdict is `unqualified` regardless of how good the numbers
   look; with caller-supplied limits the verdict is computed against exactly
   those numbers and nothing else.

## FALSIFIER (named before the run)

The card's own falsifier, operationalized — any of these fails the build:

- **F1** any code path that produces a latency number for a chain with an
  unmatched/missing stage (invented latency), including silent interpolation,
  imputation or "best-effort" pairing;
- **F2** any code path that compares timestamps across different `clock`
  identities or across different `run`/`build` identities without refusing;
- **F3** any fixture/analytic trace in tests or report labeled as actual-play
  acceptance evidence (these are fixtures only; U07's native gates stay open);
- **F4** module reads a wall clock, opens a window, or performs I/O beyond the
  caller-supplied trace input and CLI output (it must be headless/deterministic);
- **F5** acceptance limits appearing from anywhere other than explicit caller
  data (hardcoded thresholds = fabricated P06).

## SCOPE

Owned files only (`input_trace.py`, `test_input_trace.py`, `report.md`,
`receipt.json`, `PREREGISTRATION.md`, plus `reference/` extracted pinned sources
with recorded hashes). stdlib only, Python 3.11+. No production edits, no
network, no GUI, no engine starts, no GPU; tests bounded well under 120 s and
16 MiB. An insertion-point patch PROPOSAL (text) is a deliverable; no live
measurements are claimed.

---

# CORRECTION ADDENDUM — attempt 1b797ab5558149919bfe4b85066d484c (2026-09-25)

Responds to the lead's CHANGES REQUIRED on PR #121 (base module adopted
byte-identical, sha256 `4da6f5de…`; prior 20/20 suite green pre-fix).
Written BEFORE the fix; failing-first tests were run against the BASE first.

## The two corrections

1. **Overflow after unit conversion + latency arithmetic**: parse_trace
   accepted t=1e308 `s` (finite), multiplied by 1000 → inf, and chain
   arithmetic then produced NaN latencies. Fixed: (a) named refusal
   `time_overflow` when `t * UNITS_TO_MS[unit]` is not finite; (b) named
   refusal `latency_overflow` when any chain segment difference is not
   finite. NaN can never reach a summary.
2. **Empty limits**: `summarize(events, limits={})` produced qualification
   `pass` with ZERO checks (vacuous). Fixed: `{}` is `unqualified`
   (`reason: p06_limits_empty`), exactly like absent limits — never PASS.

Plus a CLI regression: refusals print the named refusal with
`latency_output: null` — no latency values (law already present; now
pinned by a test).

## Failing-first predictions (against BASE before the fix)

- C1 lead reproducer (t=1e308 s): BASE emits a summary containing NaN/inf
  (defect) → FIXED refuses `time_overflow`.
- C2 same trace in ms (t=1e308 ms single stage pair inf spread): BASE NaN
  latency (defect) → FIXED refuses `latency_overflow` if conversion passed.
- C3 empty limits {}: BASE `pass` with zero checks (defect) → FIXED
  `unqualified` reason `p06_limits_empty`.
- C4 CLI on the reproducer: exit 2, `latency_output` null, reason named.
- All 20 prior tests still pass after the fix.

## Falsifier

Any new test passing on BASE (defect not real — report loudly); any prior
test broken; any NaN/inf reaching a summary; empty limits ever yielding
`pass`; a refusal printing a latency value.

---

# SECOND CORRECTION ADDENDUM — attempt 2321d1811a92415db7863826702e2d5c (2026-09-25, later)

Scope correction per the independent candidate review (msg-a3856ac4): this
addendum addresses the STATISTICS-ACCUMULATION overflow — a boundary DISTINCT
from the unit-conversion overflow already fixed in the first correction.

## The remaining boundary (independently reproduced by the lead's quality probe)

Two COMPLETE chains with stage times [0,0,0,1e308] ms have finite per-chain
latencies, but the statistics SUM over chains overflows: `math.fsum` raised an
uncontrolled `OverflowError` mid-summary. (Unit conversion was never involved
— these are already-millisecond finite values; the first correction's
`time_overflow` correctly does not fire.)

## Prediction (failing-first, then fixed)

- The two-chain reproducer against the first-correction code raises raw
  `OverflowError` (defect, recorded in the quality probe).
- The returned candidate refuses it by name: `statistics_overflow`, CLI exit
  2, `latency_output: null`; details carry `operation: "sum"` (the actual
  operation), per the reviewer's labeling correction — the old nested reason
  string `fsum_overflow` named an operation no longer used and is gone.

## Documentation corrections applied (reviewer-directed, chronological)

1. Source comment rewritten: sum() is NOT claimed more stable than fsum();
   the real difference is silent-to-inf (detectable) vs raising
   OverflowError; the approach is DETECT-AND-REFUSE.
2. Refusal details: `{"operation": "sum", ...}` — accurate label.
3. This addendum separates statistics-accumulation overflow from the
   already-fixed unit-conversion overflow (the first addendum's objective
   text conflated them; history preserved, not rewritten).

## Falsifier

The two-chain trace being accepted (any statistic emitted); the refusal
raising an uncontrolled exception; any of the 25 first-correction tests or 20
original tests failing; a details label naming an unused operation.
