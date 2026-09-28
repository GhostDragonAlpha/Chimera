# MAT2-U03 PREREGISTRATION — frozen before implementation

Frozen: 2026-09-28Z, before authoring focus_policy.py or any test run.
Task: MAT2-U03 / planning id U03 — "Handle focus loss and input release"
(criteria sha256 03b278cbe376141d5e3659b6d9b211530e0f7fc9990376e33087da4a9c3e724c,
scope sha256 cb5475f8486197a973edc4360b177fc31a629c4f0979ebf80dd76aae57996097,
attempt 53bf60ba7dee454bac95cec63ba717cf, base revision
c525b82c7c3ce0128565424764293a3c85811ab3, isolated branch-2 checkout,
sparse path tools/monkey_campaign/contributions/MAT2-U03).

## Dependency reconciliation (step 1 — done before this file froze)

- MAT2-U01 is DONE (PR #197 merged 2026-09-27 as ebdfda61bf3df9b1f6985f771044fd946dd5e9db
  into astra/gait-capture; head a445461bcf53754438fd3d17a17a96cf1dbf0816). Its
  qualified subject is the U01 input seam. The U01 PREREGISTRATION (verbatim,
  read at ebdfda61) declares the subject hashes; I re-derived all three raw
  sha256 values from the committed pinned_seam bytes at the merge commit and
  they MATCH exactly:
  - tools/monkey_campaign/product/input_mapper.py
    7a36a45ead6637d9ba5659ea43b54a6b424803c8e57d02720ac970b42cfe6b44
  - tools/science_funnel/typeb_export/command_record.py
    6771175933ad20ac6d20c360df96f6a9729a56deb31c58a13be5e76e1cc4355e
  - tools/monkey_campaign/product/follow_camera.py
    d61347f085644e66a5f29ab1e689e2bbd2cd5ff04099856ade70e5da90a791a7
  (referenced only; not needed by the policy logic).
- The canonical top-level product/ paths do not exist at this attempt's base
  c525b82c (the U01 merge lives on the astra/gait-capture lineage). Following
  U01's own pinned_seam precedent, the EXACT subject bytes are vendored into
  this contribution at `pinned_seam/` (byte-identical copies, hashes above) so
  the policy and its tests run self-contained from the sparse attempt checkout.
  A probe re-verifies the vendored bytes against the pinned hashes through
  `git show`/`git cat-file` at test time, and additionally hashes the ACTUAL
  loaded module file, so a wrong resolution fails loudly.
- Prior attempt f633058890344cb4ada3561352506015 (parked PAUSED by the lead):
  its workspace contains only a bare sparse .git at the same base — no commits,
  no working tree, no artifacts (verified read-only before writing). There is
  no prior U03 work to continue; this attempt starts the card fresh.
- The U01 interface is the floor this card builds on, by the upstream's own
  declaration inside input_mapper.py: `release_all(now_ms)` ("U03's
  focus-loss/disconnect hook") and `is_expired(record, now_ms)` (the
  consumer-side aging floor, VALID_MS = 100 ms = 2 intervals, EXPIRY_TICKS = 30
  physics ticks @ 300 Hz). This card redeclares NEITHER: it imports and wraps.

## Frozen statement

One declared policy (`u03_focus_release_policy.v1`) wraps the U01 input seam
and handles the three release triggers of the done_when:
- KEY RELEASE (age): unchanged U01 floor — the demand decays from the last
  emitted speed and lands on EXACTLY 0.0 at or before release+100 ms, then
  emission stops (the inert path resumes).
- FOCUS LOSS (alt-tab; clear+age): all held keys are cleared via the upstream
  `release_all`; any live demand AGES to exactly 0.0 through the same decay
  tail (the tail is never gated — landing on zero is mandatory); then, while
  focus is absent, NEW demands are held back (gated): presses and mouse counts
  are refused BY NAME in the trace, never silently.
- DISCONNECT (clear+age): identical declared action to focus loss, under the
  same policy id; refocus/reconnect lifts the gate and resumes with a FRESH
  grid and NO replay of anything from the gated window.
- NO STUCK MOVEMENT (consumer side): a consumer that holds the last emitted
  record and applies the upstream aging floor (`is_expired`) is INERT —
  commands nothing — whenever no fresh record exists within the 100 ms aging
  window; combined with the producer tail, the effective demand is 0.0-or-inert
  at or before event+100 ms and stays there while the gate holds.

## Frozen predictions (named probes; all with an injected integer-ms clock)

P0 (upstream regression): the vendored U01 falsifier module F1-F6 runs GREEN
unchanged against the vendored mapper (VERDICT: GREEN, exit 0).
P1 (policy identity + interface pin): the policy exposes POLICY_ID and the
declared action names; wrapping an object missing the U01 interface
(press/release/release_all/tick/is_expired/held) is refused
(`upstream_interface_missing:<member>`); the ACTUAL loaded mapper source file
hashes to 7a36a45e... (subject pin) and command_record to 67711759... (seam pin).
P2 (focus loss mid-walk, clear+age): W held at the band ceiling; focus_lost(t)
clears the held set; the next boundaries emit EXACTLY two tail records —
v0*(1-elapsed/100) then EXACTLY 0.0 — and emission then stops permanently
while gated; every gated press is refused by name; refocus resumes with a
fresh grid (exactly one record for the first post-refocus press interval; no
replay of the gated window).
P3 (disconnect on the live-zero path): S held (a live zero-advance target);
disconnect(t) clears it; the next boundary emits NOTHING (no tail from a zero
demand) and the machinery's inert path resumes; the trace names the event.
P4 (key release ages — U01 floor preserved through the wrapper): release(W)
decays monotone and lands on EXACTLY 0.0 at or before release+100 ms, then
stops (upstream semantics, wrapper-transparent).
P5 (consumer aging floor independent of producer ticks): with the last record
nonzero and NO tick after the event (the hidden-window case), the consumer's
effective demand is commanded at age == 30 ticks (100 ms) and INERT from
age 31 ticks (strict `>` in the upstream `is_expired`), so movement cannot
outlive 100 ms without a fresh record.
P6 (gate refusals are named, never silent): every press/mouse while gated
lands in the trace with a named code and the mapper's held set stays empty;
a disconnect/refocus pair with nothing held is a named no-op, not an error.

## Frozen falsifiers (each must fail loudly with a named code)

F1 (stuck command — the card's own hazard, bitten live): after focus loss, a
FORCED press while gated is REFUSED (`press_refused_while_gated:<name>`) and
no record after the deadline boundary carries a nonzero v_forward. Hazard
baseline H1 (recorded, not hidden): the RAW mapper with no policy keeps
issuing nonzero records every 50 ms indefinitely while a key is held — this
is exactly what the policy prevents, demonstrated on the same vendored bytes.
F2 (unbound timing): the timing claims are exact, not approximate — the decay
at elapsed == RELEASE_DECAY_MS is EXACTLY 0.0 (never negative), the aging
boundary is strict at 30 vs 31 ticks, and every probe's event carries its
injected now_ms in the trace.
F3 (silent policy): any code path that drops input without a named trace
entry, or gates without exposing the gate in the trace, fails the probe
(F6/P6 checks assert named entries for every refusal and gate transition).

## Frozen probes (exact commands; CPU-only, stdlib-only, no engine, no network,
no OS focus manipulation — the card's observation "Keep operator desktop focus
and processes untouched" is honored: focus/disconnect are INJECTED events on an
injected clock, never real desktop state)

- `python -B tools/monkey_campaign/contributions/MAT2-U03/test_focus_policy.py`
  (P0-P6, F1-F3, H1; named checks counted and printed).
- `python -B tools/monkey_campaign/contributions/MAT2-U03/pinned_seam/tools/monkey_campaign/product/input_mapper_tests.py`
  (U01 F1-F6 regression, run in place from the vendored bytes).
- `python -B tools/monkey_campaign/contributions/MAT2-U03/emit_focus_trace.py`
  (writes `policy_traces.json`: the frozen qualification scenario's per-tick
  table — the profile's "input/state/tick display" diagnostic layer as
  numerical evidence, with policy state and consumer effective demand).

## Honest boundary (frozen)

The `controls` profile is kind=motion with camera-required fields and views.
NO runtime or visual claim is made: this attempt checkout is sparse (the
contribution path only), the base carries no integrated game loop that consumes
the seam, and real alt-tab would touch operator desktop focus, which the card's
observation forbids. The visual/camera clause and the real-runtime exercise of
the policy are recorded PENDING_RUNTIME for the runtime-facing lane (the venue
that produced U01's real capture), inventoried explicitly here rather than
claimed. No GPU, training, network, engine process, or desktop automation is
started; writes are confined to this attempt checkout.
