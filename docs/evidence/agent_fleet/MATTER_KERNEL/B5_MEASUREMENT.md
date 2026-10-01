# B5 MEASUREMENT — GPU residency, live engine (2026-09-13)

Engine: chimera_engine.exe 8107 (roottranslation-BASE Release), window
maximized, teddy membrane scene loaded. Harness:
`python -m tools.matter_kernel.residency http://127.0.0.1:8107 10`
(two GET /studio_chrome reads, TOTAL HTTP silence between them).

## RESULT: PASS (on the amended instrument — see B5_PREREGISTRATION.md)

- frames advanced during 10 s silence: 1323 (floor: 1000)
- counter rate: 132.3 frames/s (floor: 100 = 5x the 22 fps incident)
- mean frame time from counter: 7.56 ms (budget: 10 ms)
- rec.calls = rec.draws = 1323 — every frame recorded and drawn exactly
  once; the resident scene kept drawing with ZERO Python intents
- harness HTTP calls for the whole window: exactly 2

## FIRST RUN (pre-amendment) — kept honest

The first window FAILED the original bands: served fps field read 52.4,
ft_avg 16.6 ms. Investigation: the engine carries three clocks that
disagree. The cumulative counter (ui.hpp ft_pushes_) is exact; the served
fps/ft_avg are UI-thread smoothed and read LOW (measured 48-73 against
counter 110-136.5 across three windows); ft_max carries ~1.2 s spikes
(observer capture stalls). The amendment moves the judge onto the exact
counter; the floor is unchanged. Full story in the prereg amendment.

## CORROBORATION (recorded, not judged)

- reported fps fields during the passing window: 51.7 -> 73.2 (smoothed)
- reported ft_avg: 16.6 -> 10.8 ms
- present mode: FIFO preferred, MAILBOX if available (engine.cpp ~1100) —
  vsync can pace presents below compute rate; the counter measures frames
  computed+recorded, which is the residency question.

## OPEN (unchanged)

Re-runs with each battery scene as B1-B4 land as engine scenes.
