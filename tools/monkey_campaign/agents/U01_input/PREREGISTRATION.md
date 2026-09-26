# U01 PREREGISTRATION — gameplay input -> the 20 Hz command seam

Frozen BEFORE implementation, 2026-09-24, against base `33e7a444` (worktree HEAD
`8feea42a`). Discovery: `discovery_note.md` (revision B; revision A noted in its
§0). Every number below is cited to the seam or existing machinery; none is
tuned. The frozen walk contract (CommandRecord v1 + V1FamilyAdapter +
`GaitWalker::configure()`) is UNCHANGED by this work: this task only PRODUCES
records; a UI remap is a data-table edit, never a contract or training change.

## RULE 0 — the theory, stated before the build

**STATEMENT** (disagreeable): gameplay input can be mapped to the existing walk
command seam by a pure, stateless-of-the-engine module that emits versioned
`CommandRecord`s at the seam's own 20 Hz decision boundary — keyboard/mouse in,
bounded speed/heading records out — with release decay, no state writes, and
bindings that are data, so a UI remap changes emitted commands and nothing else.

**PREDICTION** (not yet measured, measured by the tests below):
Across 5000 randomized input schedules (keys + mouse deltas + jittered clocks),
the mapper emits (a) ZERO records outside `0.0 <= v_forward <= 0.763625` m/s or
`|yaw_rate| > 1.6` rad/s, (b) ZERO non-command calls into the sink, (c) with an
injected clock ticked at 1 ms, held-key records spaced EXACTLY 50 ms apart with
no burst after a stall (a 500 ms tick gap yields exactly ONE record at the next
tick), and (d) after key release, `v_forward` reaches EXACTLY 0.0 within 100 ms
(2 intervals) and emission then stops (the seam returns to INERT — no records).

**FALSIFIERS** (named now; any one firing kills the build as specified):
- F1 NO-TELEPORT: any input path that writes pose/state directly — observed as
  a sink call that is not `emit(CommandRecord)`, or any import of an engine /
  pose-writing module by the mapper (`gait_controller`, `pose_apply`,
  `/hinge_bin`, `/joints_bin`, `/stride_bin`, `/pose_apply` never appear).
- F2 OUT-OF-BOUNDS: any emitted record with `v_forward` outside [0.0,
  0.763625] m/s, `|yaw_rate|` outside [0, 1.6] rad/s, non-finite values, or a
  negative `v_forward` (the seam's own domain, `gait_command_domain`).
- F3 CLOCK JITTER / BURST: emitted records not spaced 50 ms apart under the
  dense injected clock; more than ONE record emitted per 50 ms interval; or a
  stall followed by a burst replay instead of a single current-state record.
- F4 RELEASE NOT EXPIRING: after release, any record with `v_forward > 0`
  later than 100 ms after the release instant, or emission continuing after
  the decay tail (the inert path must resume).
- F5 REMAP TOUCHES THE CONTRACT: a bindings remap that changes anything except
  the emitted records' values (record type, bounds, clock, adapter projection).

**STOP RULE**: the test module green, all five falsifiers measured, receipts
saved. No tuning loop: if a falsifier fires, the MAPPER is wrong and is fixed
against the frozen numbers above; the numbers are never adjusted to pass.

## THE FROZEN MAPPING TABLE (bindings are DATA — `tools/parser.py:39-69` precedent)

Physical input -> emitted command at the next 50 ms boundary. `V_MAX =
0.763625` m/s (`command_record.py:66`); `OMEGA = 1.6` rad/s
(`controller.py:45`, input-side steer constant; the v1 adapter routes yaw_rate
NOWHERE — carried only, `command_record.py:180-181`).

| Physical input | Command emitted while held |
|---|---|
| `W`, `Up` | `v_forward = V_MAX`, `yaw_rate` per steer input |
| `S`, `Down` | `v_forward = 0.0` (zero-advance walk target — legal, `command_record.py:81-83`; NOT a stop bar; the seam has no reverse authority: domain >= 0, `gait_controller.hpp:2253`) |
| `A`, `Left` | `yaw_rate = +OMEGA` |
| `D`, `Right` | `yaw_rate = -OMEGA` |
| mouse X delta | accumulates; at each boundary emits `yaw_rate = clamp(counts * SENS_RAD_PER_COUNT / INTERVAL_S, -OMEGA, +OMEGA)`, then clears the accumulation (deltas consumed, never resent — `live_viewer.py:1978-1980` law). Baseline `SENS_RAD_PER_COUNT = 0.002` (declared input-side preference; U04 owns it) |
| `Shift` | REGISTERED REFUSAL by name ("sprint: no seam authority at v1 — in-band ceiling is the measured band") — a refusal entry in the trace, never a silent clamp (`parser.py:96-102` precedent) |
| `Space` | REGISTERED REFUSAL by name ("jump: no walk-seam channel") |
| anything else | unbound; ignored (the parser's own rule, `parser.py:130-132`) |

Sign convention: `yaw_rate > 0` is declared as turning LEFT (counter-clockwise
seen from above, right-handed +Y-up world — F01 discovery note §2). It is
carried only at v1; a future heading lane owns the machinery-side sign.

## THE FROZEN EMISSION RULE (the 20 Hz boundary)

- `INTERVAL_MS = 50` (20 Hz over 300 Hz; `command_record.py:68-70`,
  `infer_numpy.py:29-44`, `gait_controller.hpp:108-111`). Declared tolerance:
  ZERO drift under the tests' injected clock (the only clock the headless tests
  use); a real-clock harness may tick at any rate — early ticks emit nothing.
- At most ONE record per interval, and only when the command VALUE changed or a
  held input needs refreshing: a held key re-issues its record every interval
  (the R4 discipline: a held command must track, `command_record.py:84-87`);
  idle emits NOTHING (the seam's inert path must stay reachable —
  `gait_controller.hpp:121-123`).
- No burst: if ticks are delayed (a stall), the next eligible tick emits the
  CURRENT state once; the past is never replayed. Consumers are protected by
  the expiry policy below, not by replay.
- Every emitted record: `issued_tick` = the mapper's tick source at emission
  (injectable; the headless tests inject an integer tick counter,
  300 Hz), `source = "u01_input_mapper"`.

## THE FROZEN RELEASE / EXPIRE POLICY

- Held key = sustained command (re-issued every interval, per above).
- Key release: the speed demand decays LINEARLY to 0.0 over `RELEASE_DECAY_MS
  = 100` (2 intervals) — at most one record per interval along the tail — and
  then emission STOPS (inert resumes; F4). `v_forward` is monotone
  non-increasing along the tail and lands on exactly 0.0 at or before the 100
  ms boundary.
- Steering release: `yaw_rate` emits 0.0 at the first boundary after release
  (steering is an effort; no heading memory), alongside the decaying speed
  tail if one is running.
- Expiry (consumer-side contract, declared for U03): a record is valid for
  `VALID_MS = 100` (2 intervals) after its boundary; a consumer that receives
  no fresh record treats the walk demand as EXPIRED and reverts to the seam's
  inert path (no record). U03's focus-loss extends this with an immediate
  clear; the basic release decay here is the floor.
- Focus loss / disconnect: OUT OF SCOPE here (U03's row); the mapper exposes
  the hook (`release_all`) U03 builds on.

## THE FROZEN NO-TELEPORT INVARIANT

The mapper's ONLY output is `CommandRecord` instances handed to an injected
sink (`emit(record)`). It imports nothing from the engine, performs no HTTP,
holds no pose, reads no state, and cannot move the animal: position is the
machinery's output (CONTROLLER_MAP.md: "positions are OUTPUTS, never inputs").
The mock sink records every call; the tests assert every recorded call is a
command emission (F1).

## OWNERSHIP (declared before implementation; nothing existing modified)

- `tools/monkey_campaign/product/input_mapper.py` — the module (stdlib +
  `tools.science_funnel.typeb_export.command_record` import only).
- `tools/monkey_campaign/product/input_mapper_tests.py` — the falsifier tests
  (house style: sibling `*_tests.py`, `parser_tests.py` precedent; runnable as
  a script, prints per-falsifier receipts, exit 1 on any failure).
- `tools/monkey_campaign/agents/U01_input/` — brief, discovery note, this
  prereg, INTEGRATION_U03_U04_U07_W08.md, receipts/.

Parallel-worker disjointness: U02 owns `follow_camera*.py` in the same
`product/` dir; file sets are disjoint; no shared harness needed (noted in the
integration file).

## WHAT WOULD MAKE THIS THEORY LOSE (honest limits, stated now)

- The seam's heading authority does not exist yet: `yaw_rate` is carried, not
  routed. If the later heading lane derives a different sign or bound, THIS
  module's mapping table is amended by a NEW prereg, not silently.
- The 0.763625 m/s ceiling is the measured in-band band of the scene seed; if
  a later authorized receipt widens the band, the ceiling follows THAT receipt
  (one cited constant, re-frozen) — never a tuning sweep.
- The tests are headless with injected clocks: they measure the mapper's
  emission discipline and bounds, NOT end-to-end latency. C12's actual-play
  latency field belongs to U07 (declared in the integration file).
