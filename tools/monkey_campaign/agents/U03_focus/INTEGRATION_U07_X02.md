# U03 integration notes — for U07 (real-play measurement) and X02 (pause interplay)

Module: `tools/monkey_campaign/product/focus_policy.py` (+ `focus_policy_tests.py`).
Prereg: `agents/U03_focus/PREREGISTRATION.md` (frozen, with REVISION A appended —
read it: two build defects and one checker alignment were caught by the falsifiers
and are recorded there; no frozen number moved). Receipt:
`agents/U03_focus/receipts/focus_policy_tests_20260924.txt` (GREEN, 41 checks).
U01 baseline re-measured green in this worktree before the final run:
`receipts/u01_baseline_recheck_20260924.txt`.

## The contract in one paragraph

`FocusPolicy(sink, mapper_factory=...)` OWNS the wiring: it inserts its expiry
gate as the mapper's sink, so records flow mapper -> gate -> your real sink and
nowhere else (a gate BESIDE the mapper double-delivers — that exact defect was
caught by P2.a; do not reintroduce it in the harness). The input surface is the
mapper's own shape (`press/release/mouse/tick`, injected integer ms), plus four
policy events: `on_blur/on_focus/on_disconnect/on_reconnect`. Blur and
disconnect both call the mapper's `release_all` (physical-release semantics:
the mapper's frozen decay runs, exact 0.0 lands at or before +100 ms, then
silence — NEVER a hard-clear live-zero record, which would flip the seam to the
zero-advance state, command_record.py:81-83). Disconnect additionally raises a
named state (`fp.state` in {"focused","blurred","disconnected"}; disconnect
dominates). While blurred or disconnected, new press/mouse intent is DROPPED
AND NAMED; releases pass; ticks pass (the decay must reach the sink). Every
record is gated through U01's `is_expired` at delivery — expired records are
dropped, named, never emitted. Recovery re-arms with an empty held set.

## U07 — measure controls during actual play (depends on W10, U03, U04)

- Wiring the live harness: feed the policy, not the bare mapper. Page visibility
  (`visibilitychange` in the browser channel, the private-channel precedent from
  U01's note — ChimeraEngine/live_viewer.py, "30 Hz of INTENT") maps to
  `on_blur`/`on_focus`; channel silence maps to `on_disconnect` (declare the
  silence threshold there and name it in the trace — this module deliberately
  does NOT own a silence timer; nothing in it reads a wall clock).
- Where to send records: the policy's sink is the harness' real seam sink. Feed
  events at frame rate and `tick(now_ms)` once per frame with the harness clock;
  the mapper's 50 ms grid stays exact under any tick rate (U01 F3).
- The stall-arrival case you WILL see live: after a long stall (tab throttling,
  GC), the exact-0.0 tail record arrives at the first boundary AFTER the decay
  deadline — value exactly 0.0, never a positive sample past the deadline
  (measured in the fuzz; prereg REVISION A §3). When computing your
  stop-latency field, measure the DEMAND deadline (E + 100 ms) separately from
  the zero record's ARRIVAL, and report both — C12's commanded-vs-arrived
  distinction, same as the interval-vs-latency rule.
- Delivery-time expiry: the gate checks age at tick-processing time. If your
  harness queues records for later consumption (a producer/consumer split),
  RE-CHECK `InputMapper.is_expired(record, now)` at consumption — declared
  limit, prereg "what would make this theory lose".
- Blur arrives from the OS even when the browser keeps sending: while blurred,
  presses are dropped BY NAME (`dropped_blurred` in `last_trace`) — if your
  measurement shows "input dead after refocus", check the trace first: the
  likely cause is that `on_focus` never fired, not stuck input.
- What U03 guarantees your latency table: after ANY blur/disconnect/release at
  E — no v_forward > 0 delivered later than E + 100 ms (RELEASE_DECAY_MS, the
  mapper's frozen constant, identity-imported); the stream lands exact 0.0 and
  then silence until a fresh accepted press; all records inside U01's bounds;
  blur byte-identical to the mapper's own release_all (P2.a, 5 vs 5 records,
  0 field mismatches).

## X02 — pause interplay (depends on the pause lane)

- Pause is NOT blur, and should not fake one: `on_blur` releases held keys and
  DECAYS over 100 ms — the right semantics for "the window lost focus", wrong
  for a game menu that wants the animal FROZEN mid-stride. If the pause lane
  wants an instant stop, that is a NEW declared policy (the integration note of
  U01 sketched a `clear(now_ms)` amendment: drop the tail, emit one final
  live-zero record) — it must flip the seam to the zero-advance state
  (command_record.py:81-83) knowingly, under its own prereg. Do not route
  pause through this module silently.
- What pause CAN reuse today: while a pause menu is up, drive the policy with
  `on_blur` (or `on_disconnect` if the input device is also suspended) — you
  get release + decay + silence + intent-dropping for free, and `on_focus` on
  resume gives a clean re-arm with no phantom keys (P5.j/k measured). The
  dropped-intent counters (`dropped_blurred` / `dropped_disconnected` in
  `last_trace`) are your audit that no menu-time keystrokes leaked into
  gameplay.
- The expiry floor composes with any pause: a record older than VALID_MS is
  never emitted by this gate regardless of pause state, and the consumer-side
  contract (revert to inert on expiry) is unchanged from U01.
- One trap measured here: repeated release_all never restarts a decay tail
  (P1.f/P1.l, P6 cycles) — so calling `on_blur` again on an already-paused
  session is safe, but if the pause lane ADDS its own release path on the bare
  mapper, re-check P1.f semantics: a release that RESET the tail's start
  instant would extend movement past the 100 ms deadline. That falsifier
  (P6 "restart" checks) is reusable against any pause implementation.

## Disjointness

U03 files: `tools/monkey_campaign/product/focus_policy*.py` +
`agents/U03_focus/*`. U01's `input_mapper.py` was imported READ-ONLY (both
named hooks existed: `release_all`, `is_expired` — no amendment needed, none
made). No existing file modified; `git status` in the receipt report.
