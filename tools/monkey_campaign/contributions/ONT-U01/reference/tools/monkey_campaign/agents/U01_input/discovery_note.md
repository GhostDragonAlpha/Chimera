# U01 Discovery Note — the 20 Hz speed/heading command seam and the existing input machinery

Author: M-U01 (gameplay input mapper). Date: 2026-09-24. Checkout:
`E:/ChimeraWork/monkey-play-20260924`, branch `monkey-play-20260924`.
Read-only discovery plus this dir; no existing file modified. All paths relative
to the checkout root unless absolute.

## 0. DISCOVERY REVISION — the base jumped mid-task (required by the coordinator)

| | revision A (stale) | revision B (current, authoritative) |
|---|---|---|
| base | old local master `32105f18` (467 commits behind) | `33e7a444` (real game tip; branch rebased, then F01 + P02P03 integrated on top — worktree HEAD `8feea42a`, all receipts cite `33e7a444` paths) |
| verdict on the seam | NO walk machinery existed in-tree; the completion map's "existing 20 Hz speed/heading seam" could not be found; nearest candidates were the human-demo drive contract and the 50 Hz stand-port cadence | THE SEAM EXISTS: the typea command channel (`GaitWalker::configure()` key `commanded_target_velocity_x`) + the frozen CommandRecord v1 (`tools/science_funnel/typeb_export/command_record.py`), decision clock 20 Hz over 300 Hz physics |
| consequence | prereg would have had to invent a seam | prereg targets the real seam; nothing had been implemented at revision A, so nothing is re-targeted — the mapper is written against revision B only |

Everything below is revision B, re-verified in the current worktree
(`git log --oneline -1` per cited tracked file where noted).

## 1. THE SEAM (what U01 emits into)

### 1.1 The decision clock: 20 Hz over 300 Hz physics (the "20 Hz boundary")

- `tools/science_funnel/typeb_export/command_record.py:68-70` — `HOLD_TICKS = 15  # the 20 Hz decision clock over 300 Hz physics`; `POLICY_HZ = 20`; `PHYSICS_HZ = 300`. 300 Hz / 15 ticks = 20 Hz = one decision per **50 ms** — exactly C12's "20 Hz implies a 50 ms command interval".
- `tools/science_funnel/typeb_export/infer_numpy.py:29-44` — `PolicyClock`: `assert policy_hz * hold_ticks == physics_hz`; `is_decision_tick = tick % hold_ticks == 0` (decision every 15th tick; ZOH between).
- `tools/science_funnel/typeb_export/interface_freeze.py:108-109` — `policy_gate` = "1.0 iff this tick is a decision tick (physics_tick % hold_ticks == 0), else 0.0 — the 20 Hz gate over the 300 Hz physics".
- `tools/science_funnel/typeb_export/run_f_inference_budget.py:8` — "F-INFERENCE-BUDGET fires if p50/p95/p99 exceeds 50 ms (the 20 Hz budget)" — the seam's own measured precedent that 50 ms is a per-decision budget, NOT an end-to-end latency guarantee (C12's exact warning).
- The engine side agrees: `ChimeraEngine/engine/gait_controller.hpp:108-111` — "a constant command re-issued at the learned layer's 20 Hz decision clock over the 300 Hz physics is byte-equivalent to one issue" (zero-order hold; re-issue at 20 Hz is legal and idempotent).

### 1.2 The machinery-side channel: `GaitWalker::configure()` / `commanded_target_velocity_x`

All in `ChimeraEngine/engine/gait_controller.hpp` (read-only; no C++ edits, per the architecture law):

- `:102-123` — THE COMMAND CHANNEL (typea-command-adapter 20260921): `{commanded_target_velocity_x}` — "the commanded target velocity, **m/s**, fed by the scene/test harness through `configure()` between ticks. ZERO-ORDER HOLD: a new command applies at the next tick boundary and holds until replaced… THE AUTHORITY LAW: the command REPLACES the v argument of the walk's own derived plant law `x_off = v*t_stance/2` at its two plant-target sites — the command multiplies the DERIVED relation; it is not a gain on its output… INERT WHEN UNUSED: `cmd_vx_live_` false reads exactly the legacy expression `(std::max)(0., s_.v[3])`."
- `:2252-2255` — the configure() intake: `require(it.value().is_number() && !it.value().is_boolean(), "gait_command_number"); require(a >= 0., "gait_command_domain");` then `cmd_vx_live_=true; cmd_vx_=a; cmd_vx_tick_=ticks_;` — **live (NOT restart-gated)**, domain **non-negative**, first-class.
- `:1116-1117` — the fire: `return cmd_vx_live_ ? cmd_vx_ : (std::max)(0., s_.v[3]);` — the plant law's v argument.
- `:2772-2775` — the read-back echo (status JSON): `gait["command"] = {live, target_velocity_x_m_s, issued_tick, plant_law_consumptions, first_plant_law_tick}` — the census W08/F-G42 reads; a U07 latency chain can use `issued_tick` → `first_plant_law_tick` (7 ticks measured, see 1.3).
- **There is NO HTTP route for this channel** (`grep configure|gait_control` over `engine/main.cpp`, `engine/http_server.cpp`: no match). The gait walker is driven as a native scene bundle (`tools/science_funnel/gait_scene.py` compiles the `gait_controller` bundle kind, `RECORD='model.dynamics.gait_walker'`), not through the render engine's HTTP surface. The "engine consumed via HTTP only" law applies to the C++ *renderer*; the gait machinery's declared input is `configure()` between ticks, fed by the Python-side harness — exactly where this task's module sits.

### 1.3 The Python-side command interface: CommandRecord v1 + V1FamilyAdapter (the type U01 emits)

`tools/science_funnel/typeb_export/command_record.py` (frozen at `e028d6fb` "COMMAND RECORD v1 frozen: the planner's downward currency…"):

- The record (`:88-140`): `CommandRecord(v_forward, yaw_rate=0.0, issued_tick=0, source="planner", record_version=1)`.
  - `v_forward`: m/s, **>= 0 enforced in `__post_init__`** ("the plant law's own max(0,.) domain"); must be finite.
  - `yaw_rate`: rad/s, finite, **CARRIED, NO AUTHORITY** — "commanded_heading is reserved for a later lane per the typea receipt; present so the wire format never changes when the authority is derived".
  - `issued_tick`: the physics tick at which the planner issued (the ZOH applies it at the next `step()` and holds >= HOLD_TICKS).
  - `source`: the issuing planner's id (the R4 discipline lives here).
- The projection law (`:146-190`): `V1FamilyAdapter.project()` routes **EXACTLY ONE field** to the machinery: `{"commanded_target_velocity_x": float(rec.v_forward), "routed_yaw_rate": False}` — float64 pass-through, "the machinery owns every clamp; the adapter pre-clamps nothing". Actor conditioning is EMPTY at v1.
- The measured numbers (`:66-87`, none tuned):
  - **Supported (in-band) range: [0.0, 0.763625] m/s** — `V_MAX_IN_BAND_M_S = 0.763625`, "the scene seed's band, measured veto-free horizons 137-222 ticks (R1-R4)".
  - Out-of-band is LEGAL up to the declared envelope (`V_ENVELOPE_DEMO_M_S = 1.30`): the MACHINERY absorbs the excess through its own reach annulus (R5: 1.30 m/s demanded, clamped to xoff 0.258747 m by the existing fore clamp). **The adapter never pre-clamps** — and the INPUT therefore should never demand out-of-band in the first place (that is U01's bound, frozen below).
  - Rate limits: **DECLARED UNLIMITED at v1** (`rate_limit_v_per_s = None`, `rate_limit_yaw_per_s = None`); step changes measured-legal (R1-R3 onset latency 7 ticks <= the 15-tick hold).
  - Zero-speed semantics: `v_forward = 0.0` is "the plant law's own `x_off = 0` — a legal command that targets the walk's own zero advance. It is NOT a stop bar" (declared; noted for the mapping below).
  - The R4 lesson (planner-owned semantic): "never feed a constant seed pinned from entry — a held command must TRACK the measured relation". For U01 this means: a held key RE-ISSUES the demand every interval (which is exactly what a gameplay key means), and the seam's inert path stays available when no key is held.
- The seam has **two states that a naive mapper would collapse**: no record at all (machinery INERT, legacy `max(0, measured v)` — `gait_controller.hpp:121-123,1117`) vs a record with `v_forward=0` (a live zero-advance target). The distinction is load-bearing for release handling (frozen below) and is cited here as the reason "emit nothing" and "emit zero" are different mapper outputs.

### 1.4 Heading: what exists and what does not

- The record CARRIES `yaw_rate` (rad/s, finite) but the v1 adapter routes it NOWHERE (`routed_yaw_rate: False`, `:180-181`); `commanded_heading` is reserved for a later lane (`:33-35`).
- No yaw/turn/heading channel exists anywhere in `gait_controller.hpp` (grep `yaw|turn|heading`: only trunk-vault/table comments; the walker is a planar Oku assembly — `gait_scene.py:52-56` "planar assembly", base 6-axis but the gait machinery drives hip/knee/ankle/MP in one plane).
- The declared in-repo input-side steering constant is `ChimeraEngine/controller.py:45` — `TURN_RATE = 1.6  # rad/s -- a brisk but controllable steer`. The mapper adopts it as its own emission bound for the carried yaw_rate, explicitly labelled an INPUT-side bound (no machinery authority claimed).

## 2. THE EXISTING INPUT MACHINERY (what U01 builds on; keyboard/mouse baseline)

| Piece | What it is | Citation |
|---|---|---|
| The parser grammar | physical input -> verb via BINDING TABLES (DATA, never code) -> `ButtonState(held, value)` -> Formula -> control vector; unimplemented verbs are REGISTERED REFUSALS, never silent | `tools/parser.py:39-69` (BIND_KEYBOARD/BIND_GAMEPAD), `:96-102` (Refusal), `:114-170` (Parser) |
| Binding-remap precedent | "bindings are DATA… the formula layer never sees a physical name" — a remap is a table edit, no retraining, no formula change (parser_tests falsifier 2) | `tools/parser_tests.py:8-10`; `tools/parser.py:128-134` (`set_physical`) |
| The keys->drive state machine | `Controller.update(dt, keys, on_ground) -> Drive(state, fwd, strafe, turn_rate, sprint, crouch, jump, angle)`; keys are booleans; digital keys drive at magnitude 1.0; `BACKWARD_FACTOR = 0.8`; `TURN_RATE = 1.6` rad/s | `ChimeraEngine/controller.py:44-45, 48-125` |
| The private browser input channel | "The browser sends mouse drag / wheel back as tiny /input requests; the render thread consumes them"; walk input via `/walk` -> `walk_input(fwd, strafe, sprint, jump, crouch, mx, my, use)`; deltas accumulate into `_walk_in`, consumed once per render tick, "jump never dropped between frames" | `ChimeraEngine/live_viewer.py:14, 755-772, 893-897`; browser side "30 Hz of INTENT. Deltas are consumed, never resent — a dropped packet must not double a turn" `:1978-1980` |
| Engine-local keyboard | the C++ window's own WASD/QE/space/ctrl/R poll is CAMERA-ONLY and explicitly GATED while the console is open ("a typed command can never leak into the scene") | `ChimeraEngine/engine/engine.cpp:104-127, 152-166` |
| Viewer HTTP camera input | browser orbit/keys throttled to one POST per 60 ms, camera routes only (radius/theta/phi) | `tools/product_viewer/server.py:588-639`; route contract re-verified in `agents/U02_camera/discovery_note.md` §2 |

Headless constraint honored: everything above is HTTP-to-a-private-local-server or in-window engine input. There is NO operator-desktop injection anywhere in the lineage and this task adds none: the mapper is a pure module whose tests run headless with an injected clock and a mock sink; the eventual play harness (U07/W10) feeds it from the same private-channel pattern (browser/gamepad JS -> HTTP -> module), never from desktop hooks.

## 3. BOUNDS THE MAPPER INHERITS (all cited, none invented)

| Quantity | Value | Source (units) |
|---|---|---|
| v_forward domain | [0.0, inf) — non-negative | `command_record.py:106-108` (`__post_init__`), `gait_controller.hpp:2253` (`require(a>=0., "gait_command_domain")`) |
| v_forward supported band (U01's emission ceiling) | 0.0 .. 0.763625 m/s | `command_record.py:66` `V_MAX_IN_BAND_M_S` (measured R1-R4 veto-free) |
| v_forward out-of-band envelope (NOT used for input) | 1.30 m/s machinery-absorbed | `command_record.py:67` `V_ENVELOPE_DEMO_M_S` (R5) |
| Reverse speed | NONE — the seam has no reverse authority (domain >= 0); backward is a later lane | `command_record.py:106-108`; `gait_controller.hpp:2253` |
| Zero speed | legal; targets zero advance; NOT a stop bar | `command_record.py:81-83` |
| yaw_rate (carried) | finite; input-side emission bound 1.6 rad/s (declared from the existing steer constant; NO machinery authority at v1) | `command_record.py:96-99,180-181`; `controller.py:45` |
| Rate limits | unlimited at v1 (schema fields exist for a v2 derivation) | `command_record.py:84-87` |
| Decision interval | 50 ms (20 Hz over 300 Hz; 15-tick ZOH) | `command_record.py:68-70`; `infer_numpy.py:29-44`; `gait_controller.hpp:108-111` |
| Onset latency precedent | 7 ticks (23.3 ms) measured, <= the 15-tick hold | `command_record.py:85-86` (R1-R3) |

## 4. What this task does NOT touch

- No C++ edits (`gait_controller.hpp` read-only; no HTTP route is added to the engine).
- No edits to `tools/parser.py`, `ChimeraEngine/controller.py`, `ChimeraEngine/live_viewer.py`, or any existing driver — the mapper is a NEW module that PRODUCES `CommandRecord`s; wiring it to a live harness is U07/W07/W08's integration.
- No training, no policy, no dynamics: the frozen walk contract is unchanged (a UI remap edits a bindings dict, nothing else).
- Disjoint from U02 (follow camera): U02 owns `tools/monkey_campaign/product/follow_camera*.py`; this task owns `tools/monkey_campaign/product/input_mapper*.py`. No shared harness is required: the camera consumes state/frames, the mapper produces commands; the only future rendezvous is the play harness (noted in the integration file).

## 5. Follow-up needs recorded (not doable in this task)

1. Reverse/backward walking: requires a seam authority that does not exist (domain >= 0). U05/W-lane decision, not U01's to invent.
2. `commanded_heading` authority: reserved by the typea receipt for a later lane; the mapper carries yaw_rate and its input-side bound, and routes nothing.
3. Live-harness wiring (browser/gamepad -> mapper -> adapter -> native `configure()`): U07 measures end-to-end there; W08 consumes the record stream for commanded-vs-achieved (C11).
