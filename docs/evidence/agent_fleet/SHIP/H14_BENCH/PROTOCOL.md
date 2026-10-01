# H14 BENCH PROTOCOL — the post-build-window R6 re-run

One command, any machine, scratch-only by default, live stack never touched.
Written 2026-09-14 by H14 before the build window (gait machine + async capture
readback + sealed-cell guard) landed. The before-picture it must beat or match
is `BASELINE.md` in this directory.

## THE R6 BAR (unchanged)

- PRIMARY: every scenario's **1% low of 5-second tick-rate buckets >= 60 ticks/s**
  (60 fps on a mid-range machine), measured on `GET /tick_state`, 60 s per
  scenario, engine restarted never mid-run (counter resets fail the scenario).
- The four scenarios: IDLE, GAME_PAGE_LOAD (the real page's ask: /verts?delta=1
  at 3 Hz + /api/state at ~1.4 Hz, /frame never), FRAME_THUMBNAIL
  (/frame?w=1024 every 2 s — the reel/dyad channel, kept measured because its
  engine-side stall is real), TOUCH_STORM (press+clear every 1 s).
- ADDITIONAL (this window): the after-run must **beat or match** the pre-build
  baseline (`BASELINE.md`): 1% low within 5% of, or above,
  298.99 / 298.44 / 134.14 / 298.42 t/s. A scenario can clear the 60 bar and
  still be a regression — report it as one.

## STEP 1 — build the new binary (any machine)

    # the build window's own procedure lands the exe at:
    #   .tmp/build_tick/Release/chimera_engine.exe
    # plus its shaders/ directory. Record the exe sha256 (the bench prints it
    # in the report header when run with --scratch).

If `.tmp/build_tick/Release/session_snapshot/` exists (this machine), the
scratch bench replays the real sealed world — the same before/after world.
If it does NOT exist (fresh clone), the bench still runs but boots an EMPTY
world (0 verts) and says so in the report header; such a run is not
comparable to the baseline — say so in the verdict, do not fudge it.

## STEP 2 — THE ONE COMMAND (the R6 verdict)

    python tools/game_shell/bench.py --scratch --report docs/evidence/agent_fleet/SHIP/H14_BENCH/bench_after_build.md

That is the whole harness: boots the exe on private port 8141 in an isolated
cwd (`--engine-exe` / `--scratch-port` to override), settles past the measured
boot counter re-base, runs all four scenarios 60 s each, kills the engine BY
PID, writes the report (header carries exe sha256 + scene provenance), exit
code 0 = 4/4 PASS. Stdlib only; ~6 minutes.

## STEP 3 — browser-side fps (optional, recommended)

Scratch pair (engine from step 1's exe, shell proxied to it):

    # shell (pick any free ports; 8141/8241 shown):
    python -c "import sys; sys.path.insert(0, r'<REPO>/tools/game_shell'); import server; server.Handler.engine_url = 'http://127.0.0.1:8141'; server.main()" 8241 &
    node tools/game_shell/fps_probe.js --mode headless --windows 3 \
        --game http://127.0.0.1:8241 --engine http://127.0.0.1:8141
    # then kill the engine+shell BY PID (never by image name)

Expect ~240 fps headless (Chrome's headless rAF cap — compare headless to
headless) and engine ticks ~299 t/s under browser load. JSON lands at
`.tmp/fps_probe.json`; copy to this directory as `fps_probe_after_build.json`.

## STEP 4 — record + commit

- Verdict section appended to `bench_after_build.md`: 4/4 bar, beat-or-match
  table vs `BASELINE.md`, FRAME_THUMBNAIL delta vs 134.14 (the G8 readback
  should move this number UP; IDLE/TOUCH_STORM regressions implicate the gait
  machine).
- Commit the report + json here with the built exe hash in the message.

## HONEST-HOST NOTE (stated, not hidden)

Every number in this protocol's history (R6 pass, the pre-build baseline) was
measured on Desktop-BI03LBO: **RTX 4090, Windows 11** — a top-tier GPU. The
strict reading of R6 — "60 fps on ORDINARY machines" — remains **UNTESTED**
until a 1060-class (or equivalent mid-range) machine runs this same protocol,
one command, and posts its table here. The protocol is deliberately
machine-agnostic for exactly that run: stdlib Python for the verdict, one
Node script (Playwright + installed Chrome) for the browser side, scratch
engine on a private port, no live-stack dependency.

## LIVE-STACK RULES (apply on any machine, always)

- The live world (8107) is shared: measurement-only. `/health`, `/tick_state`,
  `/verts` are fine; never POST presses/poses to it; /frame pulls are capped
  (each stalls the tick ~1 s until the async-readback fix lands).
- `bench.py` enforces this: touch_storm / frame_thumbnail against the default
  live base are REFUSED without `--allow-live-mutating`.
- The engine is killed BY PID ONLY. Both engines share one image name; a
  name-filtered taskkill takes the live world down with the scratch one
  (measured the hard way, 2026-09-14 — see DRIFT.md).
- Co-tenants: back off exponentially on 429s from any shared endpoint.
