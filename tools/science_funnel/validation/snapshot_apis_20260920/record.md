# snapshot-apis-20260920 -- the four production restart-state gaps

Rule-0 preregistration of record: `receipt.json` (frozen rule_0 sha
`b49707933222e2f787f8105449450304c6f256146fb7258ca9459c4054003d56`; convention in the receipt). This file is the narrative; the
receipt is the law. Committed BEFORE the instrument existed.

## The theory (Rule 0)

The four REGISTERED RESTART-STATE GAPS that validator-BLOCK every
production-class certificate -- `gap_engine_contact_warm_start`,
`gap_engine_reflex_state`, `gap_engine_controller_history`,
`gap_engine_world_state` -- are names for state that already exists, per tick,
inside `ChimeraEngine/engine/gait_controller.hpp`'s `GaitWalker`. If that is
true, an out-of-tree instrument (the wave/ifreeze GAIT_EVENT_TRACE precedent:
copy the headers into the lane dir, add a dormant flag, build under `.tmp/`,
zero shipped bytes) can dump all four classes at a mid-walk tick, a fresh
process can restore them, and the restored future must be BIT-IDENTICAL to
uninterrupted execution. Then the validator's gap registry can accept the four
gaps as RESOLVED (reader + proof) for instrumented builds.

**Prediction (pre-named):** contact warm-start + controller history + reflex
state are resident in the controller's per-tick state and dump cleanly via the
instrument pattern; world state reduces to the walker's dynamical state `s_`
plus the scene pin already carried by the build recipe.

**Falsifiers (pre-named, full text in the receipt):**
- **F1 RESTORE-DRIFT** -- any restored future divergence (state hashes or
  action bytes) fires; the diverging class is localized by the declared
  forced-drop probe and reported, never papered over.
- **F2 SHIP-INVARIANCE** -- unexercised scene bytes = `f6844eea...`, trace =
  the wave-47 sha `c6f9b6c0...`; the instrument copy flag-off equals the
  pristine base build byte-for-byte. Any ship-byte movement fires. Committed
  reporting growth (the base is past the wave-47 anchor) is a NAMED diagnosis,
  never a silent pass.
- **F3 GAP-CLOSURE** -- each gap closes (reader + proof) or becomes a
  precisely-named engine-service record; neither = fired.
- **F4 determinism** -- 3 fresh-process reference runs byte-identical.
- **F5 scope** -- only the lane dir + `tools/policy_compat`; no edits to
  `gait_controller.hpp`; no new C++ in the shipped tree.

## The mid-walk tick (Rule 1: derived, not chosen)

T = 150: the shipped walk refuses at ~300-304 (wave-45/47: 302), so the future
half carries >= 150 comparable ticks; 150 is after the entry transient and the
first full hind exchange era (fire 98, TD 107) and INSIDE the ride/hold era
[107,152) -- a mid-hold tick on the shipped calendar. Frozen before any run.

## Method

1. Fence builds (pristine, out-of-tree): `gait_unit` + `gait_unit_trace` at
   this base -> the base's own anchor bytes; cross-check the wave-47 pins.
2. Instrument: the lane-dir header copy + dormant `GAIT_SNAPSHOT_API` +
   proof harness; flag-off rebuild must equal the pristine bytes (LEG A).
3. Proof: dump at T=150, restore in a fresh process, compare tick hashes +
   action bytes to the uninterrupted reference (F1), 3x (F4).
4. `tools/policy_compat`: the engine gap registry consumes the readers; the
   validator accepts a production certificate's inventory only when all four
   gaps carry RESOLVED **with verifiable proof** (and still blocks unresolved
   or unproven gaps).
5. Receipt: per-falsifier measured verdicts, appended below.

## Measured (append-only)

VERDICT: **ALL FIVE FALSIFIERS HELD**.

- **F2 SHIP-INVARIANCE, every leg EXACT:** scene `f6844ee...`, ship stdout
  `8c537cdb...`, ship trace `c6f9b6c0...`, plain stderr `b505bb65...` -- all
  reproduced byte-exactly at this base. LEG A: the instrument header copy with
  the flag off, built with the shipped harness source, equals the pristine
  build byte-for-byte. The EXERCISED build (recording + snapshot active)
  printed the ship stdout and the full wave-47 trace byte-exactly on all
  three reference runs.
- **F1 RESTORE-DRIFT, not fired:** the fresh-process restore at the end of
  tick 150 carried the future to the refusal BIT-IDENTICALLY: state hashes
  identical on all 152 compared ticks, action bytes identical
  (21888 B), refusal 302/gait_positional_correction_budget
  identical; blind phase matched the snapshot file; round-trip serialization
  byte-equal.
- **F3 GAP-CLOSURE:** all four gaps CLOSED. Snapshot = 3129 B
  (3089 B body) with a 184-field manifest
  (world_state 7, contact_warm_start
  10, reflex_state 93,
  controller_history 74). Every forced-drop
  probe (class reverted to the fresh-reset serialization) MOVED the
  continuation -- no reader is vacuous. `rng_stream` recorded: the engine
  walk carries no random stream; nothing invented.
- **F4 determinism, not fired:** three fresh-process reference runs
  byte-identical (states/actions/snapshot/stdout/stderr).
- **F5 scope, not fired:** zero `ChimeraEngine/` edits (gait_controller.hpp
  untouched); the diff vs base touches only the lane dir + tools/policy_compat.

The validator now un-blocks production-class certificates only through
proven readers: `tools/policy_compat/snapshot_api.py` (registry, live-verified:
all four gaps RESOLVED with proofs) +
`certificate._validate_inventory`'s proof enforcement. Per-falsifier numbers:
`receipt.json` `measured`; raw verdicts: `runs/proof_compare.json`,
`runs/fence.json`.
