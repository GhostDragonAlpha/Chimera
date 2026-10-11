# Round 10 — Engine rebuild + tendon endpoint verification (engine-side)

Date: 2026-10-10. Scope: rebuild `.tmp/body-engine` with the tendon drive and
verify endpoints on a scratch port. No `tools/game_shell/` source, no
`tools/creature_graph/`, no `acceptance.py`/`build_graph.build()`, no
`Saved/meshes/monkey_joints.bin` writes. Only this evidence file was written
under `tools/game_shell/`.

## Build (PASS)
Commands (from `tools/science_funnel/run_creature.ps1`):
- `cmake -S ChimeraEngine/engine -B .tmp/body-engine`
- `cmake --build .tmp/body-engine --config Release --parallel 2`
Result: `chimera_engine.exe` linked (only benign LNK4315 /DEBUG:FASTLINK warning).
- Binary: `E:\PythonChimera\.tmp\body-engine\Release\chimera_engine.exe`
- LastWriteTime: 2026-10-10 19:11:46 ; SHA256 `C89531A80866E2C8A820A1D993AA5CC7CB7FB388AB318704C62C8DDE61B24F86`

## Stop / start log
- Listeners found: 8110 = PID 65724 `body-engine\...\chimera_engine.exe`;
  8210 = PID 72228 `python -B tools/game_shell/server.py 8210 --engine ...:8110`.
  Both confirmed our shared stack -> stopped ONLY those two (STOPPED 65724, STOPPED 72228).
- Scratch launch: requested port 8117 was already held by a FOREIGN engine
  (PID 71636, `.tmp\tendon-engine\...` — not our stack, left untouched). My
  engine failed to bind 8117 (stderr "Failed to start HTTP server on port 8117");
  killed only that own failed PID (70920). Re-launched on free scratch port 8118.
- Scratch engine: PID 76144, args `8118 --hidden 1600 900 --no-restore`
  (same scene args as run_creature.ps1). Ready confirmed via `/tick_state`.
- Scene admitted via `python -B -m tools.science_funnel.creature_scene
  --engine http://127.0.0.1:8118 --output .tmp/scratch-8118/assembly`
  -> body_model JNT3_hierarchical, cells 2, graph_hash b0e30d6c...0ca40d.
- Teardown: killed ONLY PID 76144. Post-check: 8110 free (shared stack left
  STOPPED as required), 8118 free, foreign 71636 still running (untouched).

## Probes (scratch engine 8118, freshly built binary)
Baseline /state: tendon_armed=false, q=0, battery_J=1000, severed=false.

1. GET /state tendon fields — PASS. Contains tendon_armed plus tendon_F_n,
   tendon_battery_J, tendon_battery0_J, tendon_work_J, tendon_heat_J,
   tendon_elastic_J, tendon_elastic0_J, tendon_q_deg, tendon_severed.
2. POST /tick_effort {joint_index:15,u:1} — PASS. ok=true, armed=true.
   max q = 135.64 deg (probe1) / 143.11 deg (probe2) -> q>90 (crossed 90 at ~0.2 s).
   min battery_J = 960.667 -> battery<1000.
3. POST /tick_sever {joint_index:15} — PASS. ok=true, severed=true.
   Tendon tension observed live: peak F_n = 222.22 N during active pull,
   F_n = 0 at held plateau; after sever F_n = 0 and q collapses to capsule
   rest: q 129.07 -> 5.22 -> 0.35 deg (force zero + joint falls).
4. POST /tick_effort {joint_index:15,u:-1} then /tick_pose knee_L 40 — PASS.
   disarm ok=true, tendon_armed=false. While armed, /tick_pose knee_L 40 is
   REFUSED (drive owns pin 15); after disarm it returns ok=true (succeeds).
   Note: /tick_state exposes only the frozen ledger tendon_q_deg, not the
   kinematic joint_deg_, so pose success is the POST result (refused->ok).

## Result
Build PASS. Endpoint checks 1-4 PASS on the freshly built binary.
Shared stack left stopped; scratch engine stopped; foreign engine untouched.
