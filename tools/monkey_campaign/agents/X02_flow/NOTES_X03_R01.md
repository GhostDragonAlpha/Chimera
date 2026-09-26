# X02 HANDOFF NOTES — for X03 (fall/recovery) and R01 (save/restore on restart)

M-X02, 2026-09-24, HEAD `8550b634`. Module: `tools/monkey_campaign/product/session_flow.py`
(tests: `session_flow_tests.py`, 74 checks, ALL PASS x3 byte-identical, seed 20260924).
Discovery with every citation: `agents/X02_flow/DISCOVERY.md`. Frozen table + rules:
`agents/X02_flow/PREREGISTRATION.md`.

## FOR X03 — the fall/recovery experience (deps W09 + X02)

1. THE EXTENSION POINT IS THE TABLE, NOT NEW MECHANISM. `TRANSITIONS` and
   `DEFAULT_FLOW_BINDINGS` are plain dicts (session_flow.py:89-108). The map's X03
   note ("the player can continue after failure by the approved recovery action or
   visible restart"; "Do not require a new get-up skill unless explicitly selected")
   means the likely row is either the EXISTING `(paused, restart)` (visible restart —
   already live) or ONE new row `(playing, <recovery-action>)` + one binding, if the
   operator approves an in-play recovery key. Law: the new row arrives through its own
   prereg with the same falsifiers (explicit user action only; named no-op in every
   other state; F1's reachability checks extend mechanically).
2. WHAT X03 MAY ASSUME FROM THE FLOW: after `pause` or `restart` the mapper is
   HELD-EMPTY (the quiesce used U01's declared `release_all`) and no gameplay event
   reaches the mapper outside `playing` — a recovery action can never race an
   in-flight walk command, because while the flow is not `playing` there are none.
3. THE FLOW ADDS NO PHYSICS. A fall is the engine's own root/limb law; recovery that
   re-seats the body is X03's own declared engine contact (the restart row is the only
   world touch this module has — keep it that way or prereg a new declared referent).
4. WIring note for X04 (shared): the page's browser `keydown` handler feeds
   `flow.key(name, down, now_ms)`; the flow consumes `Return/Escape/R/Q` and forwards
   everything else only in `playing`. The page's existing DEV KEYS `c/x/r/s`
   (index.html:1070-1073) and buttons (index.html:138-142) are operator surfaces —
   retire/absorb them behind the flow (`R` already matches the flow's restart key).
   During a boot the page is already answered `{"restarting": true}`
   (slice_server.py:444-452) — map that protocol state to the flow's non-playing
   visuals, never to a console error.

## FOR R01 — save/restore on restart (and R02's save lifecycle)

1. THE HOOK POINT IS THE RESTART TRANSITION. Today a restart DISCARDS the session
   record: `World.boot()` resets `events`/`mock_carry`/`fall_test`
   (slice_server.py:126-131) and `World.save()` (slice_server.py:378-387) writes
   `progress/session_<ts>.json` only when explicitly called. R01's save-before-restart
   wraps the wired callable: `def restart_with_save(): world.save(); world.boot()` —
   passed to `SessionFlow` as `restart_scene`. The flow treats it as ONE declared call
   (F3 semantics are per-CALL, not per-sub-step).
2. ENGINE-STATE RESTORE IS A DIFFERENT DOOR. The bit-identical save/restore of the
   four restart-state classes lives in the out-of-tree instrument
   (`tools/science_funnel/validation/snapshot_apis_20260920/receipt.json`,
   schema `chimera.snapshot_apis.v1`) whose own recorded forward gaps are, quoted:
   "no ship-tree HTTP snapshot route, no first-class engine build id, no
   actor-in-the-engine-loop coupling". Until that ship-tree route exists, a
   "continue where you fell" flow has no honest engine path — X02's restart is
   deliberately CLEAN-SCENE (the completion map's law: "reset is an explicit user
   action"), and R01's engine-state work lands behind the named gap.
3. REFUSALS SURFACE AS NAMED STATES. The compatibility-certificate machinery
   (`upgrade_gate_20260920` 4/4 caught; `cert_dryrun_20260920` tamper suite 3/3) is
   what must judge a save from build N on build N+1. The flow's pattern for a refused
   world call: NO transition, the failure NAMED in the trace (`restart_failed` /
   `exit_failed`), the previous state retained — reuse it; never let a save refusal
   silently skip the boot (the boot is the player's requested act; the save is not).
4. R05 borrows the teardown contract: exit's declared ordering is
   terminate -> wait(10 s) -> kill (slice_server.py:174-181); `TeardownDouble`
   (session_flow.py) is the headless shape of the owned-children proof, and F4
   measures it exactly once per session from every state.

## INTEGRATION NOTE (whoever wires the live flow)

`World.boot()` spawns its own thread and settles in the background
(slice_server.py:134, :543-547), so the raw bound method returns BEFORE the scene is
back. If the flow must not return to `playing` until the scene exists, wrap:
`lambda: (world.boot(), sb.wait_engine(world.url), wait_settled(...))` or poll
`/api/health world_booted` — the flow's contract is that `restart_scene()` returning
means the declared path COMPLETED; a wrapper that lies about completion breaks F3's
meaning, not the module.
