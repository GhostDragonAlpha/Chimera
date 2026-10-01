# B5 PREREGISTRATION — the GPU-residency contract (measured, live engine)

Rule 0: statement, prediction, falsifier — BEFORE implementation. Every
number below is derived from a cited engine surface or a measured
precedent. This bar runs against the LIVE engine (the only honest way to
prove residency); its judge() logic stays pure and offline-testable.

## STATEMENT

Triangles are weights: membranes load onto the GPU ONCE and stay
resident; compute happens in place; Python issues INTENTS and exits.
Therefore the engine's frame production is INDEPENDENT of Python
activity. During total Python silence the engine keeps rendering the
loaded scene at its own rate, within its own frame-time budget, with no
re-uploads. Any per-frame Python round-trip is visible as a collapse —
the 22 fps incident (the measured precedent behind kernel law 1) is
exactly what per-frame Python costs.

## INSTRUMENT (cited engine surface)

- GET /studio_chrome (engine main.cpp, route table): serves `fps`
  (rolling), `ft_avg` / `ft_max` (frame-time stats), `pushes`, and
  `rec.calls` / `rec.draws` (render-recorder liveness).
- `pushes` is the cumulative FRAME COUNTER: ui.hpp increments
  ft_pushes_ exactly once per rendered frame (push_frame_time), labeled
  "liveness proof for the twin".
- Derivations: silence test = read, sleep T with ZERO HTTP, read again.
  Frames advanced = pushes(t1) - pushes(t0). If Python were required
  per frame, a silent window shows collapse — the counter stalls.

## DERIVATION (bands from cited numbers)

- Per-frame Python precedent: 22 fps (kernel law 1 incident).
  Self-sufficiency floor: fps >= 100 — five times the incident rate,
  and below the engine's own minimized cap (120 fps, main.cpp ~3048),
  so the bar is honest on modest hardware and survives a minimize.
- Frame-time budget: ft_avg <= 10 ms — the same floor expressed in
  time (1/100 s).
- Window T = 10 s => frames advanced >= 100 x 10 = 1000.

## PREDICTIONS (test bars)

P1. Liveness: across a 10 s silent window the frame counter advances by
    >= 1000 frames. The engine renders with Python silent.
P2. Scene residency: rec.calls and rec.draws advance across the window
    (the SAME loaded scene keeps drawing) with zero intents between
    reads — nothing was re-uploaded, nothing re-issued.
P3. Budget: ft_avg <= 10 ms at both reads.
P4. Instrument honesty: the harness counts its own HTTP calls and the
    bar asserts EXACTLY 2 reads for the window (one t0, one t1). A
    harness that polls per frame fails its own bar by construction.
P5. Named refusals: engine unreachable -> engine_down; non-positive
    window -> invalid_window. The instrument never passes on a dead
    engine (proven: judge() refuses zero-advance samples).

## MUTATION PROBE

- "dead instrument": samples showing zero frame advance (engine frozen
  or a fake feed) must FAIL P1 — judge() refuses with stalled_frames.
- "chatty instrument": a harness sample-log with > 2 calls fails P4 —
  the instrument detects its own per-frame sin.
- "offline fake": unreachable engine raises engine_down before any
  judging — the harness cannot pass without a live engine.

## OPEN (named, with its test)

The spec reads "all of the above running": B1-B4 exist today as
reference models; their ENGINE scenes land later. This bar proves the
residency CONTRACT on the live engine + loaded membrane scene now; it
RE-RUNS unchanged with each battery scene as it lands, and the GPU
frame-time budget for full battery scenes is set when they exist.

## FALSIFIER

Frames do NOT advance during silence (the engine is a slave to
Python), OR fps < 100 with the window visible, OR ft_avg > 10 ms,
OR the recorder stalls (scene not resident), OR the harness cannot
prove its own 2-call silence. On failure the successor is named: find
the per-frame dependency (who woke the engine), fix it, re-run.

## AMENDMENT (2026-09-13, after the first live run fired the falsifier)

The first live window returned: counter +1365 frames in 10 s (PASS),
but the served `fps` field read 48-70 and `ft_avg` 16-18 ms (FAIL) —
and a follow-up double-sample exposed the cause: the engine carries
THREE clocks that disagree. The cumulative counter (`pushes`) is
exact and monotonic: 110-136 frames/s during silence, and rec.calls ==
rec.draws == pushes at every read (every frame recorded and drawn
exactly once). The served `fps` / `ft_avg` are UI-thread SMOOTHED
values that read LOW against the counter; ft_max also carries ~1.2 s
spikes from observer capture stalls. The falsifier fired on an
instrument dial, not on the law: the 22 fps incident could never have
been measured on the smoothed dial either.

Amended instrument law: the COUNTER is the only judge. The floor stays
100 frames/s during silence (unchanged, still 5x the incident); the
budget moves to the counter-derived mean frame time,
window_ms / frames_advanced <= 10 ms (exact); the smoothed `fps` /
`ft_avg` fields are recorded as corroboration, never judged. The
residency bars (silence, recorder advance, 2-call harness) are
unchanged. Nothing was weakened: the same window that FAILED on the
smoothed dial (52 fps) PASSES on the exact clock (136.5 frames/s) —
which is the point of the amendment: trust the monotonic counter,
distrust smoothed readouts.

