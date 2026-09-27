# U06 integration note — for U07 (actual-play measurement)

Module: `tools/monkey_campaign/product/state_feedback.py` (+ `state_feedback_tests.py`,
38/38 GREEN; prereg `PREREGISTRATION.md` §2; fuzz receipt
`receipts/no_capability_claim_fuzz_receipt_20260924.txt`). Depends on U05's seam
(`climb_intent.py`, now carrying R4's four binding amendments — 77/77 with the original
suite, see `receipts/`).

## The one-paragraph contract

`Observation` is pure data assembled from PUBLIC attributes of the four landed modules
(X02 `SessionFlow.state`, U03 `FocusPolicy.state`, U05 `ClimbIntentChannel.gates_active/
held/bindings`, U01 `InputMapper.held` + `InputMapper.is_expired`) — `observe()` does
exactly that read and nothing more; `render(obs) -> Feedback` is the pure display model:
ONE minimal prompt line + a structured record (per-field provenance, JSON-able via
`Feedback.record()`). `walk_record_live(records, now_ms)` derives the walking row from
U01's OWN expiry law — no new staleness rule exists anywhere in the module. Diagnostics
(engineering language: gate sets, named drops, flash age, cross-source wiring notes) are
OPTICAL: `render(obs)` returns `diagnostics=""`; pass `diagnostics=True` to fill.

## For U07's actual-play lane

1. **Readability of the prompt lines is a HUMAN acceptance field — it is yours to
   measure with the operator, not to derive from telemetry.** U07's measured fields
   (latency, response limits, P06) stay instrumented as U07 already plans; the words on
   screen are judged by the human terminal (the attunement bar: taste bottoms out in the
   human, never in a model's opinion of a string).
2. **Wording changes are DATA, never semantics.** If the operator cannot parse a line,
   the fix is a vocabulary-table edit (`PROMPTS` in state_feedback.py + the frozen table
   in `PREREGISTRATION.md` §2.2, re-run of the suite). What may NEVER change by a wording
   edit: the honesty boundary — a line must keep citing only what its source module
   provides. The forbidden-token list (prereg §2.4) is the guard: the fuzz re-run after
   any wording edit must stay at ZERO hits.
3. **The flash is the harness's choice.** Render with `flash_event=<the IntentEvent
   delivered on this ms>` to surface "Climb intent sent (no climb skill loaded)" at the
   moment of delivery; omit it on later calls to fall through to the held/ready rows.
   Intents do not expire at v1 (R3/no-expiry), so a persistently-surfaced flash stays
   TRUE — but the player-readable choice is the momentary flash; the diagnostics line
   reports the flash age if you hold one too long.
4. **Latency instrumentation hook:** the flash is lit directly from the delivered
   `IntentEvent`, whose `now_ms`/`issued_tick` share the walk timeline's clocks (C12's
   chain) — correlate flash onset with CommandRecords on the same stamps; do not
   re-time the channel.
5. **What the line will never say, so U07 never measures for it:** climbing, holding-on,
   falling, support contact, recovery — none exists at v1 (K-series/W09 future). If U07's
   protocol wants those states measured, that is a K-series deliverable, and the
   vocabulary gets new rows ONLY with a source module that provides the state.
6. **Remaps flow through automatically:** the `climb_ready` line interpolates the LIVE
   bindings table (a U04 remap changes the displayed key name with zero semantic effect,
   measured: V1.remap). No re-registration needed when U04's settings change bindings.
