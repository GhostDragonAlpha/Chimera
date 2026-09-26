# PREREGISTRATION — I-R05-RESOURCE-LEDGER-FOLLOWUP (planning id R05)

Attempt: a4592d4b796542a7ad657d8e2ad7d3ec · branch-3 · base `c525b82c7c3ce0128565424764293a3c85811ab3`
criteria_sha256 `03d70278eca25c1b2f7450abaca7178f475aba038a76ff9e1ed3e5e35669f815`
Written BEFORE any adapter/test code (Rule 0: statement / prediction / falsifier).
Depends on the ACCEPTED I-R05-RESOURCE-LEDGER module: PR #139 head
`47c00f05169fa49ea770c274cfe7f280e6710e82` (merge `becdcb2716ee441cfb2832287a349c8f4b6c7090`),
`resource_ledger.py` sha256
`05cf62184931d6443188cd9b72aa9e88821cc8a9063a351a7e4d658d6690da6c`.

## RULE 0 — STATEMENT

The accepted resource ledger can be connected to the EXISTING session teardown
hooks and the EXISTING session teardown tests with a thin, production-untouched
ADAPTER: (a) `LedgeredSessionFlow`, a subclass of the pinned
`session_flow.SessionFlow` (9afbddcd, sha256 `30e06c04…`), that owns a session
generation integer (mirroring `World.boot_count`, slice_server.py:128) and
closes exactly that generation through the ACCEPTED ledger around the frozen
restart/exit transitions (parent hook-up proposal A, session_flow.py:327-350);
and (b) `LedgeredForestScene`, a subclass of the pinned
`forest_loader.ForestScene` (9afbddcd, sha256 `53d7fdde…`), that mirrors every
name the scene registers into `self._resources` (:358-362, plus
`attach_engine_shutdown` :367-374) as a
`(generation, owner="session", "forest:<name>")` ledger record and mirrors each
successful teardown release, leaving the record live on the `f08_teardown_leak`
path (parent hook-up proposal B, forest_loader.py:380-405). No production file
is edited (`production_edit_allowed: false`); the reference extraction
(`reference/`, byte-pinned in `reference/EXTRACTION_LEDGER.json`) is read-only
input. The adapter imports the ACCEPTED ledger SOURCE and verifies its sha256
at import time.

## PREDICTION (not yet measured)

1. The adapter loads the accepted ledger bytes and the imported module's file
   hashes to `05cf6218…` byte-identically (the same bytes as PR #139 head);
   the EXISTING teardown suite `session_flow_tests.py` (74 checks, F1–F5)
   runs green against the extracted pinned hooks WITHOUT modification, proving
   the reference bytes behave exactly as upstream.
2. Restart/exit through `LedgeredSessionFlow` closes exactly the generations
   the frozen transitions end: a restart closes the old generation only after
   `restart_scene()` succeeds and bumps the generation (boot_count mirror); an
   exit releases the session-owned live records by name BEFORE the one real
   teardown fires and closes the generation AFTER it returns (exactly once;
   a second Q remains the frozen named drop and re-closes nothing).
3. A DELIBERATE UNRELEASED resource is named `ledger_live_at_close` at the
   exit close; that cycle's summary FAILS and cannot be laundered by any
   caller ceiling.
4. A WRONG-GENERATION release claim made through the adapter surface (a stale
   generation integer against a live current-generation record) records
   `ledger_wrong_generation`, leaves the current record live and releasable by
   its true generation, and fails the affected cycle summary.
5. `LedgeredForestScene` keeps two independent counts of one truth in
   agreement on a clean teardown (`live_after == []` and zero ledger-live
   records of the generation), and on a raising release the scene refuses
   `f08_teardown_leak` while the ledger names the exact leaked id at the
   generation close.
6. The unittest suite runs green CPU-only, stdlib-only, in well under the
   120 s per-invocation bound (predicted < 5 s); the adapter source contains
   no process discovery/termination, no wall-clock read, no network, no GPU.

## FALSIFIER (named before the run — ANY ONE fails the build)

- F1 (the card falsifier): the adapter uses a REWRITTEN stand-in instead of
  the accepted module — i.e. the imported ledger source hashes to anything
  other than `05cf6218…`, or the adapter re-declares ledger logic instead of
  importing it. Guarded by construction: the import refuses by name
  (`adapter_accepted_source_drift`) unless the exact sha256 matches.
- F2: a deliberate unreleased resource passes its cycle (a leak launders
  through any ceiling).
- F3: a wrong-generation release claim mutates or closes the current record.
- F4: any production source is edited (session_flow.py / forest_loader.py /
  input_mapper.py / command_record.py / slice_server.py); the adapter must
  wrap the hooks, never rewrite them.
- F5: native-process or VRAM soak qualification is claimed from a fixture.
  NOT claimed: the engine process itself, the native shutdown ordering
  (terminate → wait → kill) and any VRAM/soak behavior remain native runtime
  gates, exercised here only as recorded doubles of the declared referents.

If F2/F3 occur the hook wiring is wrong; if F1/F4 occur the attempt violates
its card; if F5 occurs the report lies. None may be tuned away — the result
gets recorded and the card reports honestly.

## BOUNDS

stdlib only · Python 3.11+ · headless · CPU-only · deterministic (injected
`now_ms`, no wall clock) · no process enumeration / termination / engine
launches / memory probing / network / GPU · tests < 120 s per invocation ·
total new output < 16 MiB · code only inside the attempt workspace.
