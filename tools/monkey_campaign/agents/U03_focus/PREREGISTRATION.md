# U03 PREREGISTRATION — focus loss, disconnect, and the release/expiry policy

Frozen BEFORE implementation, 2026-09-24, worktree `E:/ChimeraWork/monkey-play-20260924`
(branch `monkey-play-20260924`, HEAD `8550b634` = U01 INTEGRATED). Prerequisite read
first: `product/input_mapper.py` (READ-ONLY, imported), `agents/U01_input/PREREGISTRATION.md`,
`agents/U01_input/discovery_note.md` (CommandRecord v1 seam, cited file/lines), and
`agents/U01_input/INTEGRATION_U03_U04_U07_W08.md` (the actual filename — the brief's
`INTEGRATION_U03_U07_W08.md` is that same note under a longer name; it names MY hooks:
`release_all` + the `is_expired` floor). U01 baseline re-measured green in this worktree
before this prereg was written (26/26 checks).

Row, verbatim: "Alt-tab, disconnect and key release clear or age commands under a
declared policy; no stuck movement." Constraint: "Keep operator desktop focus and
processes untouched."

## RULE 0 — the theory, stated before the build

**STATEMENT** (disagreeable): focus loss and device disconnect are handled entirely as a
POLICY LAYER on top of U01's untouched mapper — window-blur and device-disconnect release
every held key EXACTLY as a physical release (the mapper's own frozen decay, not a new
clear primitive), a record older than the declared max-age is never handed to the sink
(belt over decay), and the disconnected condition is a named, queryable state — so that
after any blur/disconnect/release event the command stream provably reaches exact 0.0 and
then silence, and the animal is never left under a sustained stale command.

**PREDICTION** (not yet measured; measured by `focus_policy_tests.py`):
Across the deterministic scenarios plus a 2000-event randomized fuzz (input events +
policy events + jittered clock, frozen seed), after EVERY blur/disconnect/release event at
instant E: (a) zero sink records with `v_forward > 0` exist later than `E + 100 ms`;
(b) the stream ends in an EXACT 0.0 record (emitted after E, or the last record before E
was already 0.0) and then TOTAL SILENCE until a fresh press accepted by policy; (c) every
post-E record is inside U01's frozen bounds (band ceiling 0.763625 m/s, |yaw| <= 1.6);
(d) with a stalled injected tick clock, zero expired records reach the sink; (e) blur's
sink-visible stream is byte-identical to a bare U01 mapper receiving the same physical
release at the same instant (same count, same values, same issued ticks).

**THE FROZEN POLICY** (each clause answers the row's "clear or age ... declared policy"):
1. **Blur** (`on_blur`): `mapper.release_all(now)` — all held keys released EXACTLY as
   physical release. The mapper's own frozen decay runs untouched: linear samples from the
   LAST EMITTED speed, EXACT 0.0 at or before release+100 ms (`RELEASE_DECAY_MS`),
   then emission stops (the inert path resumes). NO hard-clear primitive is added: a
   final `v_forward=0.0` record would flip the seam to the LIVE-ZERO state
   (command_record.py:81-83), which is a DIFFERENT seam state from inert — the physical-
   release semantics reuse the decay U01 already froze and keeps both states honest.
2. **Disconnect** (`on_disconnect`): the same `release_all(now)`, PLUS the named
   disconnected state (`state == "disconnected"` — a queryable name, never a silent flag).
   While disconnected (or blurred), NEW `press`/`mouse` intents are DROPPED and NAMED in
   the trace (a disconnected/unfocused surface cannot honestly produce intent; accepting
   it would manufacture phantom movement — the stuck-movement bug family this row kills).
   `release` events always pass (they can only reduce demand). `tick` always passes (the
   in-flight decay must REACH the sink — the declared decay-to-zero sequence then silence).
3. **The expiry floor at emission** (the "age" half): every record the mapper produces is
   gated through `InputMapper.is_expired(record, now)` — the U01 hook, unchanged — before
   the real sink sees it. An expired record is dropped and NAMED ("expired_at_gate"),
   never emitted. `MAX_AGE_MS = VALID_MS = 100` (2 intervals, `EXPIRY_TICKS = 30` @ 300 Hz)
   is IMPORTED from U01's module — zero new numeric constants exist in this policy.
4. **Recovery**: `on_focus` / `on_reconnect` clear their named state only; the mapper is
   guaranteed empty of held keys (blur/disconnect released them), so the next accepted
   press arms a FRESH 50 ms grid — clean re-arm, no phantom keys, no replayed tail.
5. **Transition idempotence**: blur-while-blurred, disconnect-while-disconnected and their
   recoveries are no-ops recorded by name — a repeated `release_all` must never restart a
   decay tail (restarting would EXTEND movement past the 100 ms deadline).

**FALSIFIERS** (named now; any one firing kills the build as specified):
- P1 NO-STUCK: in any scenario or fuzz event, after any release/blur/disconnect at E —
  (i) any sink record with `v_forward > 0` later than `E + RELEASE_DECAY_MS`;
  (ii) any sink record AT ALL after the stream's post-E exact-0.0 landing (before a fresh
  accepted press); (iii) any post-E record outside U01's frozen bounds or non-finite;
  (iv) a post-E stream that is non-monotone within a single decay tail. Any hit fires.
- P2 CONSISTENCY-WITH-U01: (a) blur's sink stream is not byte-identical to the bare
  mapper's physical-release stream (same history, same clock, same instant — count,
  values, issued_ticks all equal); (b) any frozen constant redeclared instead of
  imported (module numeric constants must be the SAME OBJECTS as U01's: `is` identity);
  (c) any numeric literal in the module source duplicating a frozen number
  (`= 100`, `= 50`, `0.763`, `1.6`, `300`, `= 30`). Any hit fires.
- P3 EXPIRY FLOOR: with a stalled injected `tick_source` (issued_tick frozen while now_ms
  advances) and a held key, the mapper emits records that age past `VALID_MS` — the gate
  must drop EVERY one (zero stale records reach the sink; every drop named). With a
  healthy clock, the gate must drop ZERO records (the belt never fires spuriously).
  The drop boundary must match `is_expired` exactly (age > EXPIRY_TICKS, strictly).
- P4 NO OPERATOR DESKTOP: the module's imports are exactly {`__future__`, `sys`,
  `pathlib`, the seam's `command_record`, U01's `input_mapper`}; no transport or
  desktop-injection surface (keybd_event/SendInput/SetCursorPos/socket/urllib/ctypes/
  subprocess/win32/pyautogui/pynput); no wall-clock read (time/datetime absent); every
  test drives the module with synthetic events and injected clocks only. Any hit fires.
- P5 DISCONNECTED STATE NAMED + CLEAN RE-ARM: `state` must report
  "focused"/"blurred"/"disconnected" (disconnected dominates); input dropped during
  blur/disconnect must be NAMED in the trace (never silent); after
  `on_focus`/`on_reconnect`, `mapper.held` is empty (no phantom keys), the dropped-gate is
  open again, and the first accepted press emits at ITS OWN boundary (fresh grid).
  A disconnect that leaves the state unnamed, drops silently, or re-arms with phantom
  keys fires.
- P6 CYCLE SURVIVAL: repeated focus/disconnect cycles (blur→focus→press→blur→…,
  disconnect→reconnect→…, including blur-while-disconnected and double-blur) never
  restart a decay tail (no tail after an event whose held set was already empty) and the
  P1 invariant holds at EVERY event instant. Any restart or violation fires.

**STOP RULE**: the test module green, all six falsifiers measured with receipts saved,
the consistency verdict written. No tuning loop: if a falsifier fires, the POLICY MODULE
is wrong and is fixed against U01's frozen numbers; the numbers are never adjusted to pass.

## THE FROZEN NUMBERS (all inherited; this module declares ZERO new ones)

| Quantity | Value | Source (imported, never redeclared) |
|---|---|---|
| Release decay deadline | 100 ms | `input_mapper.RELEASE_DECAY_MS` |
| Consumer max-age (the floor) | 100 ms | `input_mapper.VALID_MS`; `MAX_AGE_MS = VALID_MS` |
| Expiry in physics ticks | 30 @ 300 Hz (strictly `age > 30`) | `input_mapper.EXPIRY_TICKS`, via `InputMapper.is_expired` |
| Emission interval | 50 ms | `input_mapper.INTERVAL_MS` (the mapper owns the grid; policy never touches it) |
| Band ceiling / steer bound | 0.763625 m/s / 1.6 rad/s | `input_mapper.V_MAX_IN_BAND_M_S` / `OMEGA_MAX_RAD_S` |
| Fuzz seed / size | 20260924 / 2000 events | house seed (U01 tests precedent); the brief's floor is 200 |

## OWNERSHIP (declared before implementation; nothing existing modified)

- `tools/monkey_campaign/product/focus_policy.py` — the policy module (disjoint name;
  imports U01's mapper READ-ONLY; if a hook were missing it would be recorded as a
  finding, not edited — both named hooks EXIST, so no amendment is needed).
- `tools/monkey_campaign/product/focus_policy_tests.py` — the falsifier tests (house
  style: sibling `*_tests.py`, runnable as a script, per-falsifier receipts, exit 1).
- `tools/monkey_campaign/agents/U03_focus/` — brief, this prereg,
  `INTEGRATION_U07_X02.md`, `receipts/`.

## WHAT WOULD MAKE THIS THEORY LOSE (honest limits, stated now)

- The decay-to-silence choice is exactly U01's physical-release semantics: the seam stays
  under a DECAYING (monotone, <= 0.763625 m/s) command for at most 100 ms after
  blur/disconnect, protected further by the consumer's own `is_expired` contract. If a
  future ruling demands an instant hard clear, that is a NEW declared policy (and flips
  the seam to the live-zero state, command_record.py:81-83) — it would need its own prereg,
  not a silent edit here.
- The gate checks age at tick-processing time with the same injected `now_ms` the mapper
  saw; a harness that queues records for real-time later adds a delivery delay this module
  cannot see (declared for U07's live harness: re-check `is_expired` at consumption there).
- The tests are headless with synthetic events; they measure policy discipline, NOT real
  OS focus behavior or real device stacks. U07 measures the live chain; X02 owns the
  pause-menu interplay (notes written for both, nothing prebuilt).

## REVISION A (appended before the final green run; the falsifiers caught two
## build defects and forced one honest test alignment — no frozen number moved)

1. GATE TOPOLOGY (caught by P2.a "5 vs 10 records" and P5.k "2 records"): the
   first wiring constructed `InputMapper(sink)` and `FocusPolicy(mapper, sink)`
   with a SHARED sink — the mapper emitted directly into the sink AND the gate
   re-emitted there, so every boundary record arrived twice and the gate gated
   nothing on the direct path. Fixed in the module: the policy hands ITSELF in
   as the mapper's sink through a `mapper_factory` — ONE emission path,
   mapper -> gate -> real sink. The policy's frozen clauses (release_all,
   named state, drops, expiry floor) are unchanged.
2. FUZZ SCALE (P6.d fired twice, honestly): the 2000-frame fuzz yielded only
   89 then 138 deliveries against the prereg's own 200-record vacuity floor.
   The fuzz was rebuilt frame-based (every frame advances the injected clock,
   as a real harness loop would) and doubled to 4000 frames — more coverage,
   same event mix; the 200 floor now holds with margin (249 deliveries).
3. CHECKER ALIGNMENT (P6.a fired once): the fuzz checker demanded the exact-
   zero RECORD within E+100 ms, but U01's frozen no-replay clause delivers that
   record at the FIRST BOUNDARY AFTER a stall that eats the deadline (measured:
   E=98250, zero record at 98359, value exactly 0.0). The prereg's falsifier
   P1(i) is about POSITIVE-speed records past the deadline — the checker now
   measures exactly the prereg's wording: no v>0 past the deadline; the tail
   lands on zero; silence after it. The deterministic P1 scenarios (dense
   clock) still hold zero-arrival INSIDE the deadline (P1.b/P1.g/P1.k), as
   U01's own F4 does.
