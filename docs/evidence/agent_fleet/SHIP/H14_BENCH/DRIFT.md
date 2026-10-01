# H14 bench-protocol — DRIFT LIST (audit of bench.py + fps_probe.js vs the 2026-09-14 page)

Audited against HEAD `569083bb` (branch `astra/tasks/matter-kernel-format-01`).
The bench was written for the R6 run (commit `92287a2b` binary); since then the
page landed W4 sound wiring, E4 lesson rail + overlays, the new judge types
(`pressure_isolation`, `cells_woken`), and the C3 kernel delta stream.

## What did NOT drift (checked, no change needed)

- `#play-btn` id, the `screen-start` -> `screen-play` flow, `JOINT_INDEX.knee_L = 15`
  (index.html line 410), `POST /api/pose {joint_index, deg}` (proxied to engine
  `/tick_pose`, which still accepts both `joint` and `joint_index` forms).
- Page poll cadence: `setInterval(pollVerts, 333)` + `setInterval(pollState, 700)`
  (index.html lines 1804-1805). `E4checkProgression` (400 ms) is page-local —
  no fetch, no new engine channel. The W4 sound rail (`snd()`) is page-local
  and guarded; it adds no engine traffic.
- `TOUCH_STORM` body `{"px","py","force_n"}` — still a valid engine
  `/tick_touch` form (engine main.cpp line 1208: the three touch forms).
- The 5 s-bucket PRIMARY judgement and the raw footnote series: unchanged,
  like-for-like with the R6 run.

## DRIFT 1 — GAME_PAGE_LOAD modeled the pre-C3 page (FIXED)

The bench's verts load thread pulled the FULL `/verts` frame at 3 Hz. The real
page has asked `/api/verts?delta=1` (C3 kernel stream) since C3 landed; the
shell rides the query through to the engine. The old model imposed ~119.6 MB/min
of full-frame exports the page no longer triggers — it hid the page's true
footprint and could not verify C3's byte drop.

FIX: `_verts_thread` now polls `/verts?delta=1`, counts bytes, and classifies
each answer's framing from the magic/flag bytes (kernel keyframe / kernel runs /
legacy) — reported in the scenario's load line. NOTE recorded in code: the delta
chain is defined for ONE client; while the thread runs it must be the only
`?delta=1` poller against that engine.

## DRIFT 2 — bench could press / frame-flood the shared LIVE stack (FIXED)

R6 ran everything against live 8107. Fleet rules now forbid mutating POSTs
against live and limit /frame pulls (each stalls the tick loop ~1 s — a known
defect being fixed). TOUCH_STORM against live = 30 presses per run;
FRAME_THUMBNAIL = ~30 stall-pulls per run.

FIX: bench REFUSES `touch_storm` / `frame_thumbnail` against the default live
base (8107) unless `--allow-live-mutating` is passed (exit 2, honest refusal).
The full bench's honest home is `--scratch`.

## DRIFT 3 — no throwaway-engine mode; the R6 re-run was not one command (FIXED)

FIX: `--scratch` boots the engine exe (`--engine-exe`, default
`.tmp/build_tick/Release/chimera_engine.exe`) on a private port
(`--scratch-port`, default 8141) in an isolated cwd with `shaders/` +
`session_snapshot/` copied (the gallery/vertbind measured pattern; boot restore
replays the real sealed world), records the exe sha256 + scene provenance in
the report header, and kills the engine BY PID in a `finally` (never by image
name — the live engine shares it).

## DRIFT 4 — scratch boot re-bases the tick counter; read as a false restart (FIXED)

MEASURED: a fresh `--scratch` boot re-bases its tick counter during the async
snapshot restore — observed `599 -> 53` at t+4.0 s and `586 -> 47` at t+6.1 s
after boot, with the FPS log continuous (no engine restart). The harness's
counter-backwards rule (correct for live) read this as "engine restart
mid-run" and failed IDLE on an otherwise-299 t/s run (first baseline attempt,
3/4 with 2 false resets).

FIX: `launch_scratch_engine` now settles after boot until the counter has been
monotonic AND advancing for 20 s (restart-on-new-rebase), so scenario 1 judges
the settled world, not the boot transient.

## DRIFT 5 — fps_probe.js had no way to leave the live stack (FIXED)

The probe MUTATES the world (scripted knee pose) and its URLs were hardcoded
to live 8206/8107 — under fleet rules it could never legally run again.

FIX: `--game` / `--engine` flags (defaults unchanged for operator-authorized
runs). Also: dismisses the E4 first-run intro overlay (Enter) after PLAY for
player fidelity; Playwright require falls back from local node_modules to the
ship root so it runs from any checkout.

## Verification of the fixes (all against scratch, live untouched)

- `bench.py --scenarios touch_storm` (default base) -> REFUSED, exit 2. 
- `bench.py --scratch` full run -> 4/4 PASS, exit 0
  (`bench_baseline_pre_build.md`, the before-picture).
- `fps_probe.js --game ...:8241 --engine ...:8141 --mode headless --windows 1`
  -> ok, rAF loop started, PLAY entered, 240 fps (headless rAF cap), engine
  299.0 t/s under browser load (`fps_probe_scratch_validation.json`).

## Named, NOT fixed (not H14's files)

- Live-incident note (honesty): while auditing which engines were running,
  H14 killed a process group by IMAGE NAME (`taskkill /FI IMAGENAME eq
  chimera_engine.exe`) and took down the LIVE engine with the scratch one.
  Restored ~40 s later from its own boot snapshot; world verified
  bit-for-bit against the pre-incident sample (n_cells 5, V_lower 0.287914,
  V_upper 12.5091, V_whole 13.8246, seal_cuts 203, seal_caps 199,
  conserve_pct -0.000117273, capacity_sum 1.34699e9 — all match). Lesson now
  encoded in bench.py: kill BY PID ONLY.
- Resync amplification (C3 follow-up): measured ~4 keyframe resyncs/min for
  an IDLE player through the python shell proxy, and 83/207 keyframe pulls
  for a player in sustained whole-mesh pose motion. Any transport hiccup or
  non-beating delta costs a full 664 KB keyframe. See POLL_COST.md.
