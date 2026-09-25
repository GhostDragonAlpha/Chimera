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
