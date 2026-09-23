# TRAINER-BUILD HEARTBEAT (2026-09-23)

Lane: TRAINER-BUILD (`Agent: trainer`), branch agent/typeb-gpu-finish-20260922.

- BUILT + COMMITTED: tools/train_first_skill.py (FirstSkillGoalEnv + PPO) at
  eab5de13; prereg (RECEIPT.md falsifiers + frozen modules) at 82ebea49.
- IN MEASUREMENT: the six preregistered falsifiers.
  - F-ACTION-MAP PASS (exact +1 -> 0.763624789; 0 -> half)
  - F-REWARD-FROZEN PASS (it first caught + fixed a real dropped-terminal-reward bug)
  - F-CLOCK FIRES on the ENGINE's tick-40 refusal (rc=5, command-independent,
    bit-identical trajectories incl. NO-command) = residual A (tick-66, drill
    lane), carried with numbers; deltas exactly 15 up to the refusal
  - F-OBS-FIELD21: channel 21 bit-exact vs the engine velocity state (G2.5 GREEN);
    the probe exposed 2 DLL reset defects (stale rb/rbi readback; a_battery
    ledger never re-initialized) -- wrapper compensates; see RECEIPT.md
  - F-BATCH-COUPLING: rerunning (GPU contention with the bars run)
  - F-SMOKE: queued after it
- RAM: smoke stays at 512 envs (declared shape); <=2 GB host, ~0.2 GB GPU.
- The two large python processes (16.5/13.7 GB) are NOT this lane's.
