# R_AFTER — provenance + run index (agent R-after "window-verifier", 2026-09-14)

## The binary under test (the lead's rebuild: sealed-cell degenerate guard + two-phase capture readback)

- Path: `E:\ChimeraWork\slot-01\.tmp\build_tick\Release\chimera_engine.exe`
- sha256: `a62c6b467f1a860cad96faae9da47fd5e56553076aaa04b10454de73d137238e`
- size: 1,594,368 bytes; mtime 2026-09-14 09:11
- Repo state at run time: branch `astra/tasks/matter-kernel-format-01`

This sha256 is the provenance for EVERY verdict in this directory (the gait
falsifier, the aliveness gallery, the R6 bench).

## Isolation rules in force (all three runs)

- The LIVE world on 8107 (PID 43248 at start) was READ-ONLY: GET-only light
  polling. No POST, no /frame pulls against it.
- Each protocol ran on a SCRATCH engine on a private port (8139 / 8140 /
  8141) in an isolated cwd, one at a time, each killed BEFORE the next booted.
- Every kill was BY PID (PID taken from `netstat -ano` on the private port or
  from the harness's own PID tracking). No name-filtered taskkill anywhere
  (H14's incident is on record).
- Headless only (`--hidden`); no desktop input (operator shares this machine).

## Runs

1. GAIT FALSIFIER — port 8139, session snapshot replayed, harness
   `tools/gait_verify.py`. Evidence: `gait_verify_result.json`,
   `run1_gait/`.
2. ALIVENESS GALLERY — port 8140, driver
   `docs/evidence/agent_fleet/SHIP/H15_GALLERY/h15_gallery.py`. Evidence:
   `run2_gallery/`.
3. R6 BENCH — port 8141, harness `tools/game_shell/bench.py --scratch`.
   Evidence: `bench_after_build.md`, `run3_bench/`.

Verdicts + the known-defect-vs-new-defect classification: `VERDICTS.md`.
