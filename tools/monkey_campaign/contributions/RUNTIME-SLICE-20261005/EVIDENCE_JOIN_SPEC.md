# EVIDENCE JOIN SPEC — RUNTIME-SLICE-V1 (the chain that exists nowhere yet)

Status: DRAFT (CHAIN STOP 1), authored by wk-runtime-slice, 2026-10-02.
Binds to task brief
`E:/Chimera/parallel-budget-probe/orchestration_cycle2/PLAYER_CONTROLLED_RUNTIME_SLICE_TASK.md`
required path: "attach the same tick ID/state hash to `/tick_state` and the
evidence recorder". This spec defines the chain; implementation is gated on
the prereg unlock (see PREREG_DRAFT.md section 3/7).

## The one chain (six links, one record)

```
player_command_id
  -> physics tick / state hash          (committed snapshot identity)
  -> immutable tick snapshot            (copied state, no post-hoc reads)
  -> same-tick render submission        (update_mesh from the snapshot)
  -> completed GPU readback             (watermark-gated capture_frame)
  -> frame hash                         (rgba hash + capture seq in ONE record)
```

Every record carries ALL link identities. A record missing any link is an
incomplete chain and fails closed (`evidence_join_incomplete`).

## Link definitions

### L1 player_command_id
- Assigned at HTTP intake (`main.cpp` route handler) BEFORE dispatch to the
  tick: monotonic `cmd_seq` (uint64) + the raw command body hash + receipt
  wall-time. New sequenced queue (std::deque under a small mutex); handlers
  push, never write tick state directly (removes today's unguarded
  `force_l_/force_r_` float writes from HTTP threads — membrane_tick.cpp:342-347
  have no lock against the render-thread `step()`).
- Late/duplicate policy is a frozen prereg constant: a duplicate cmd_seq is
  refused (named), never re-executed (FB-J).

### L2 physics tick / state hash
- Consumed EXACTLY once per tick at the top of `step()`: pop at most the
  queue's next command (one-per-tick law; a tick with no command records
  `cmd_seq: null`).
- The committed tick snapshot is built AFTER the solver update completes for
  tick T: `tick_id = ticks_` (existing counter, membrane_tick.hpp:283), plus
  `state_hash = SHA-256(canonical snapshot bytes)` (below).
- The dt used is recorded (the frozen fixed-step value once declared; today's
  measured `tick_dt` is recorded as-is until the policy lands).
- Volatile fields (`ts_us`, `ts_ms` — membrane_tick.cpp:4652-4660) are
  EXCLUDED from the hashed canonical form and carried as named metadata
  (FB-D trigger protection).

### L3 immutable tick snapshot (the canonical hashed bytes)
One serialized record per committed tick, copied under the tick lock, versioned
(`chimera.tick_snapshot.v1`), containing:
- tick_id, cmd identity (seq + body hash), dt;
- root state (root_y_, root_vy_ — today's ONLY integrated DOF), and, when the
  gated mechanisms land: full generalized q/v, per-body COM states, masses,
  inertia tensors with expressed frame, mass-owner IDs (the LV-1 emission
  table reference);
- applied force/torque inputs per actuator channel (actuator id, sign, value,
  the pinned sign-map version);
- contact identities: receiver pair, application point, gap/touch state;
- signed impulses: world-space J and the (n, t1, t2) basis vectors with the
  pinned construction rule + degeneracy fallback (WALK_TELEMETRY_V2_CORRECTIONS
  "Preserve the meaning of current friction output");
- solver event records: disposition ∈ {committed, discarded, diagnostic_only};
  only committed records enter totals (the corrections doc, fold 1).
- The snapshot is written ONCE; `step()` never rereads mutable solver state
  after building it (FB-H). Render + telemetry + recorder all consume the
  snapshot, never live state.

### L4 same-tick render submission
- `engine.update_mesh(snapshot.verts, N)` is called with the SNAPSHOT's vertex
  bytes in the same frame block as `step()` (the existing seam
  main.cpp:4473-4474), and the submission is logged with
  (tick_id, state_hash, verts_hash). A verts_hash mismatch between snapshot
  and submission = mixed-state refusal (FB-H).

### L5 completed GPU readback
- The existing watermark contract (engine.hpp:74-79): read
  `capture_arm_watermark()`, `request_capture()`, wait
  `capture_collected_since(watermark)` with a declared deadline, then
  `capture_frame(rgba, w, h, &seq, &phases_us)`; require `seq >= watermark+1`
  (the thermal-path pattern, main.cpp:783-793). A timeout is a named failure
  (`gpu_readback_timeout`), never a skipped link.

### L6 frame hash (the join record)
One `chimera.evidence_join.v1` row per tick, appended to the evidence
recorder AND mirrored into `/tick_state`'s JSON (bounded ring + a
`/tick_join?tick=N` GET):
```
{ join_id, tick_id, cmd_seq, cmd_body_sha256, dt,
  snapshot_sha256, snapshot_bytes_ref,
  render_submission: { verts_sha256, mesh_seq },
  gpu_readback: { capture_seq, width, height, phases_us },
  frame_sha256 (rgba bytes), prev_join_hash (chain hash) }
```
`prev_join_hash` chains rows so a dropped or reordered tick is detectable.

## Alignment laws (inherited from WALK_TELEMETRY_V2_CORRECTIONS.md "Separate
whole-demo evidence binding" — every row named there maps to a link here)

- Every telemetry state, contact, force and energy record aligns to tick_id
  and dt; video frames bind through frame_sha256 with a declared
  video-timestamp -> tick mapping.
- The player-input stream carries receipt time, assigned tick, sequence, and
  the late/duplicate policy outcome.
- Replay identity: the same frozen initial state + command stream must
  reproduce snapshot_sha256 AND frame_sha256 exactly, excluding only the
  named volatile metadata fields (FB-D). Excluded fields are enumerated in
  the freeze, never discovered after a mismatch.
- Fail-closed: a missing source vector, application point, impulse basis, or
  mass row makes the dependent evaluator NOT ASSESSABLE and the join
  incomplete for that tick — recorded, never zero-filled.

## What exists today vs what this spec adds

| Piece | Status at pinned source | Action |
|---|---|---|
| tick seam step->update_mesh | EXISTS (main.cpp:4473-4474) | reuse |
| tick counter + state_json | EXISTS (ticks_; /tick_state) | reuse |
| GPU watermark readback | EXISTS (engine.hpp:47-79; thermal path) | reuse |
| sequenced command queue | ABSENT (bare float writes, no lock) | NEW (gated patch) |
| canonical snapshot + hash | ABSENT (state_json is unversioned, ts-polluted) | NEW |
| join record + recorder | ABSENT | NEW |
| signed impulses / contacts / energy rows | ABSENT (RT-3/4/5) | owned by the physics prerequisites, not this spec |

The join is implementable ONLY down to the depth the physics provides: today
it can bind command -> tick -> snapshot -> render -> readback -> frame hash
for the EXISTING stand/fall DOF, which is diagnostic plumbing and proves NO
locomotion claim. The chain becomes milestone-capable only when RT-1..RT-5
land. This ordering is the point: the evidence instrument must never be the
thing that invents the physics it records.
