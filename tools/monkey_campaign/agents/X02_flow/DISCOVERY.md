# X02 DISCOVERY NOTE — lifecycle / reset machinery on the game lineage

M-X02, 2026-09-24, worktree `E:/ChimeraWork/monkey-play-20260924`
(branch `monkey-play-20260924`, HEAD `8550b634` = U01 INTEGRATED).
Every claim below is cited to file + lines read in THIS worktree at this revision.
No engine C++ was edited; nothing outside my dir + the two declared `session_flow*.py`
files was written.

## 1. The game lineage runtime is the playable slice, not the membrane deck

The playable build's front door is `tools/playable_slice/slice_server.py` — "THE
PLAYABLE SLICE's front door" (module docstring, lines 1-17): one stdlib server that
serves the slice page, starts and OWNS its own engine process on a bind-tested free
port (`NEVER_PORT = 8127` refused BY CODE, line 38; `sb.free_port`, scene_boot.py:408),
boots the standing start through the REAL aliveness ingestion, and fronts gameplay.
Engine process ownership: `World.boot()` Popen's
`chimera_engine.exe <port> --no-restore --hidden` (slice_server.py:98-103).

The membrane deck viewer (`ChimeraEngine/live_viewer.py` — `/pause?on=1` at :986-991,
`/step` at :1013-1022, `/scene?term=` at :979-981) is a DIFFERENT lineage (the
holodeck membrane decks). Its pause routes do NOT exist on the game-lineage server
and are not reused; they are cited only as prior art for "pause is a Python-side
policy, never a physics edit".

## 2. THE DECLARED RESTART PATH (what the brief demands be cited)

`World.boot()` — slice_server.py:94-135 — is the existing, declared, byte-clean
restart: **a full scene reload through the existing load path**, exactly the brief's
fallback clause. Its steps, in order:

1. `self.shutdown_engine()` (:96) — the owned engine dies first (see section 3).
2. `self.port = sb.free_port()` (:97) — fresh port, 8127 refused by code.
3. Fresh engine process `Popen(..., "--no-restore", "--hidden")` (:98-103).
4. `sb.wait_engine(self.url)` (:105; scene_boot.py:446-456 — poll until the engine
   answers).
5. `rec = sb.boot_standing_start(self.url)` (:108; scene_boot.py:457-483) — the
   SCENE LOAD: POST `/mesh_import` with the committed real-body payload
   (scene_boot.py:470), scene sha recorded, then POST `/tick_gravity {"on":true}`
   (:475-477) — the standing start settles as REAL physics the player watches
   (`_finish_settle`, :137-172, records `start_state_sha256`).
6. Per-boot state resets: `mock_carry`, `fall_test`, `events` all reset (:126-131);
   `boot_count += 1` (:128) — "the restart verifier's honest signal" (:371-375).

It is already exposed to a player surface TODAY: POST `/api/restart`
(slice_server.py:543-547) and the page's RESTART button / `R` key
(index.html:141 and :1072). During a boot the page is ANSWERED, not failed:
`/api/verts` and `/api/press` return `{"restarting": true}` as a first-class
protocol state (slice_server.py:444-452, :537-539) — "the stranger's console stays
empty through a restart".

=> X02's restart = an injected callable whose declared referent is `World.boot`.
NEVER a state teleport: the engine has no set-pose route used by this lineage's
runtime, and `/tick_gravity {"on":false}` re-seat (the drop test's authored-rest
trick, slice_server.py:313-339) EDITS physics and is not a reset — named and refused.

## 3. THE DECLARED TEARDOWN PATH (exit)

`World.shutdown_engine()` — slice_server.py:174-181: `terminate()` → `wait(timeout=10)`
→ on timeout `kill()` → clear the handle. This is the owned-children contract: called
in `main()`'s `finally` (:604-605) and at the top of every boot (:96). X02's exit =
an injected callable whose declared referent is this method (terminate → wait → kill,
in that order). R05 ("Repeated scene/restart/save cycles ... all owned children/
resources close", MONKEY_COMPLETION_MAP.md) verifies against the same ordering.

## 4. The engine's route surface (enumerated, no C++ read-modify)

Routes in `ChimeraEngine/engine/main.cpp` (string-enumerated at this revision):
`/mesh_import`, `/tick_state`, `/tick_touch`, `/tick_touch_clear`, `/tick_gravity`,
`/tick_seal*`, `/tick_stance`, `/verts`, `/topology`, `/frame`, `/scene`, `/pose_apply`,
`/pose_store`, `/camera(s)`, `/gait*`, `/keys`(deck family), `/ui_click`, `/capture`,
... — **there is NO engine pause route and NO reset-in-place route on this lineage.**
The game-lineage server adds `/api/restart`, `/api/save`, `/api/send`, `/api/stop`,
`/api/carry_reset`, `/api/press`, `/api/drop_test` (slice_server.py:524-551).
Consequence (the brief already ruled this): pause is a Python-side policy —
"paused = input mapper quiesced" — and restart is the full re-boot of section 2.

## 5. Demo flow drivers that exist today (what X02 replaces/absorbs)

`tools/playable_slice/index.html`: buttons SEND / STOP / FALL TEST / RESTART / SAVE
(:138-142) wired to `/api/send|stop|drop_test|restart|save` (:555-585) plus DEV KEYS
`c/x/r/s` → send/stop/restart/save (:1070-1073). These are operator surfaces with no
states — no attract, no pause, no exit anywhere on the lineage. X02 is the FIRST flow
state machine; X04 owns absorbing/retiring the page's dev keys behind it (notes file).

## 6. The input surface X02 gates (U01, integrated at 8550b634)

`tools/monkey_campaign/product/input_mapper.py` — the mapper's declared public surface:
`press(name, now_ms)` (:191), `release(name, now_ms)` (:205), `mouse(dx_counts)` (:220),
`tick(now_ms)` (:235, the 50 ms boundary — emits 0 or 1 CommandRecord into the injected
sink), `release_all(now_ms)` (:225-228 — DECLARED as "U03's focus-loss/disconnect
hook"), `held` (:230), `is_expired(record, now_ms)` (:341-347 — the consumer-side
expiry floor: a record older than VALID_MS = 100 ms = 30 physics ticks expires and the
seam reverts to its inert path). Emission happens ONLY inside `tick()` — a mapper that
receives no ticks emits nothing. The two seam states (inert vs live-zero,
gait_controller.hpp:121-123 via input_mapper.py:10-21) are preserved by U01 and X02
adds no seam-affecting primitive.

## 7. U03's declared interface (IN FLIGHT — interplay cited, not imported)

`agents/U03_focus/PREREGISTRATION.md` (frozen 2026-09-24; `focus_policy.py` NOT yet
landed — only brief + prereg exist in `agents/U03_focus/`). Its frozen policy,
which X02's resume re-arm cites per its DECLARED interface:
- blur/disconnect = `mapper.release_all(now)` EXACTLY as physical release (clause 1-2);
- dropped intents are NAMED in the trace, never silent (clause 2);
- recovery (`on_focus`/`on_reconnect`) "clear their named state only; the mapper is
  guaranteed empty of held keys ... so the next accepted press arms a FRESH 50 ms
  grid — clean re-arm, no phantom keys, no replayed tail" (clause 4);
- idempotence: "a repeated `release_all` must never restart a decay tail" (clause 5).
X02 uses the SAME primitives (`release_all` at the pause/restart instant) so that when
U03 lands, the flow's mapper slot accepts the FocusPolicy wrapper unchanged (it
presents the mapper surface plus the policy events; the flow never touches mapper
privates).

## 8. Save/restore continuation contracts (R01's building site, cited)

(a) SESSION-record save on the lineage: `World.save()` (slice_server.py:378-387) —
writes `{"schema": "chimera.playable_slice.session.v1", scene, events}` to
`progress/session_<ts>.json`. This is a RECORD of play (scene spec + event log), not
engine state; a restart today DISCARDS it (boot resets `events`, :126-131).
(b) ENGINE-STATE save/restore: `tools/science_funnel/validation/snapshot_apis_20260920/receipt.json`
(schema `chimera.snapshot_apis.v1`) — the four production restart-state classes
(contact warm start, reflex state, controller history, world state) serialized via an
out-of-tree `GAIT_SNAPSHOT_API` instrument; mid-walk capture restored into a FRESH
process bit-identically (tick-wise state hashes + all 21,888 action bytes). Its own
recorded forward gaps, quoted: "no ship-tree HTTP snapshot route, no first-class
engine build id, no actor-in-the-engine-loop coupling". The compatibility-certificate
gate on top: `upgrade_gate_20260920` (4/4 injected incompatibilities caught) and
`cert_dryrun_20260920` (first production certificate; tamper suite 3/3 rejected).
R01's save-on-restart work stands on (a) for the session record and (b) for engine
state — the flow's restart transition is the natural pre-save hook (notes file).

## 9. What does NOT exist (honest absences that shaped the prereg)

- No flow state machine anywhere on the lineage (grep: no attract/pause states in
  `tools/playable_slice/` or `tools/monkey_campaign/product/`).
- No engine pause; no engine reset-in-place; no session `resume` of a saved engine
  state on a ship-tree route (snapshot instrument is lane-side).
- No existing session_flow*.py files (name check before declaring them: absent).
