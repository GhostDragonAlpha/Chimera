# U01 integration notes — for U03, U04, U07, W08

Module: `tools/monkey_campaign/product/input_mapper.py` (+ `input_mapper_tests.py`).
Prereg: `PREREGISTRATION.md` (frozen). Discovery: `discovery_note.md` (revision B,
base `33e7a444`). Receipt: `receipts/input_mapper_tests_20260924.txt` (GREEN).

## The contract in one paragraph

`InputMapper(sink)` consumes `press(name, now_ms)` / `release(name, now_ms)` /
`mouse(dx_counts)` / `tick(now_ms)` and hands **`CommandRecord` v1** instances
(`tools/science_funnel/typeb_export/command_record.py`) to `sink.emit(...)` —
at most ONE per 50 ms boundary (20 Hz over 300 Hz physics, `HOLD_TICKS=15`),
`v_forward` in `[0.0, 0.763625]` m/s (the seam's measured in-band band),
`|yaw_rate| <= 1.6` rad/s (input-side steer bound, carried-only at v1),
`source="u01_input_mapper"`. Idle emits NOTHING (the machinery's inert path);
`S` held emits LIVE ZEROS (zero-advance target). All clocks are injected; the
mapper never reads a wall clock and never touches state.

## U03 — focus loss and input release (depends on U01)

- Your hook exists: `mapper.release_all(now_ms)` releases every held key and
  starts the standard decay tail. For Alt-tab/disconnect you likely want a HARD
  clear instead of a decay: call `release_all(now_ms)` and then tick once with
  an explicit zero demand — OR extend the mapper with a `clear(now_ms)` that
  drops the tail and emits one final `v_forward=0.0` record. That is a NEW
  declared policy on top of this floor (your row: "clear or age commands under
  a declared policy"); add it in your module or propose a small amendment —
  do not silently change the decay.
- The consumer-side expiry floor is live: `InputMapper.is_expired(record,
  now_ms)` — a record older than `VALID_MS = 100` (EXPIRY_TICKS = 30 @ 300 Hz)
  is expired and the consumer must revert to the seam's inert path. Your
  focus-lost handler can reuse it as the "age" half of your policy.
- The private-channel precedent for detecting focus loss WITHOUT touching the
  operator's desktop: the viewer's browser channel
  (`ChimeraEngine/live_viewer.py`, "30 Hz of INTENT", deltas consumed never
  resent) — page visibility / channel silence is your disconnect signal, the
  same way U01's no-refresh expiry is.

## U04 — supported input settings (depends on U01)

- Bindings are DATA: `InputMapper(sink, bindings={...})` or edit
  `input_mapper.DEFAULT_BINDINGS`. A remap changes emitted values ONLY —
  measured by `input_mapper_tests.py` F5 (record type/version, bounds, clock
  and the adapter projection are untouched). No retraining, no contract change
  — this is the completion map's U01 constraint, already honored.
- Sensitivity: `InputMapper(sink, sensitivity=rad_per_count)` — baseline
  `SENS_RAD_PER_COUNT = 0.002` (declared input-side preference, `walker.py`
  `look()` precedent: "how far a hand should push a view is a preference, not
  a physics"). Inversion = a negative sensitivity for the yaw axis, or swap the
  `turn_left`/`turn_right` entries in the bindings table — both are data edits.
- Persist schema suggestion (for your row + R02): the bindings dict + the
  sensitivity float are the whole settings surface; a `chimera.monkey_input.v1`
  JSON (F01's `chimera.<thing>.v<N>` naming) carries exactly those. Bounds
  (`V_MAX_IN_BAND_M_S`, `INTERVAL_MS`, `EXPIRY_TICKS`) are the SEAM's numbers —
  they must NOT become settings; refuse that in your loader (the parser's
  "refuse what it cannot name" rule).
- Controller/gamepad: the wire format already carries analog (the record is
  float; `mouse()` is just an axis accumulator). A stick maps to
  `press/release`-free direct demand — that needs a small extension (an
  `analog(fwd, yaw, now_ms)` entry point); the map marks controller support an
  explicit product decision, so nothing is prebuilt.

## U07 — measure controls during actual play (depends on W10, U03, U04)

- The timestamp chain C12 asks for is assembled from three clocks, all pinned:
  (1) input event `now_ms` (the harness' injected clock — wall-clock in the
  live harness), (2) `record.issued_tick` (300 Hz physics tick; default
  `now_ms*300//1000`, or inject `tick_source=` in the live harness for exact
  pinning), (3) the machinery echo `gait["command"]` in the gait status JSON
  (`gait_controller.hpp:2772-2775`: `issued_tick`, `plant_law_consumptions`,
  `first_plant_law_tick`) — the typea receipt already measured onset at 7
  ticks (23.3 ms) <= the 15-tick hold (`command_record.py:85-86`).
- The 50 ms interval is a COMMAND CADENCE, not a latency claim (C12's warning;
  the seam's own F-INFERENCE-BUDGET treats 50 ms as a per-decision budget).
  Report your measured end-to-end field separately from the interval, as the
  map demands ("human feel and measured latency are distinct acceptance
  fields").
- The mapper is headless and engine-free: in the live harness, feed it from
  the private browser channel (`/walk`-style HTTP -> `press/release/mouse`)
  exactly as `live_viewer.py` does — never from desktop injection.

## W08 — verify commanded start, stop, speed, heading (depends on W07)

- The command stream to freeze is a list of `(issued_tick, v_forward,
  yaw_rate)` — exactly `CommandRecord.canonical_fields()`; replay it through a
  real `InputMapper` (deterministic injected clock, seed 20260924 in the tests)
  or straight into `GaitWalker::configure()` via the V1FamilyAdapter
  (`commanded_target_velocity_x = float64(v_forward)`, the adapter pre-clamps
  nothing). C11's commanded-vs-achieved then reads the echo's
  `target_velocity_x_m_s` / `plant_law_consumptions`.
- Start = first record after idle (the inert path ends); stop = the decay
  tail's exact-0.0 record (or S's live zeros); heading has NO machinery
  authority at v1 (`routed_yaw_rate: False`) — "commanded heading" can only be
  verified once the reserved `commanded_heading` lane lands; until then your
  heading column is the CARRIED yaw_rate, labeled as unrouted.
- The R4 constraint is binding on any frozen sequence you author: never pin a
  constant seed from entry — held commands must track (the mapper's held-key
  re-issue at every boundary is compliant by construction).

## Disjointness (the coordinator's file-ownership law)

- U01 files: `tools/monkey_campaign/product/input_mapper*.py` +
  `agents/U01_input/*`. U02 files: `product/follow_camera*.py` +
  `agents/U02_camera/*`. No shared harness was needed: the camera consumes
  state/frames; the mapper produces commands. The single future rendezvous is
  the live play harness (U07/W10): both modules are constructed with injected
  sinks/providers there — neither imports the other.
- No existing file was modified (see `git status` in the U01 receipt report);
  the only tracked-tree reads were discovery citations.
