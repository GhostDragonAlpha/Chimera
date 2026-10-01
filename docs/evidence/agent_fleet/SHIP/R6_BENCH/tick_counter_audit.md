# Tick counter audit — bursty ticks/s

G8 (tick audit), fleet round 2, 2026-09-13/14. Live engine
`http://127.0.0.1:8107`, PID 38960, binary
`.tmp/build_tick/Release/chimera_engine.exe` (built 2026-09-13 23:20 local,
started 2026-09-14 00:15:59 local — i.e. the F2 fast-capture build; the round-1
bench in [bench_report.md](bench_report.md) (commit 256b9a62) ran on the
previous instance). Round 1 measured the symptom (0-tick 250 ms windows,
651/s "catch-ups", mean 294-300 t/s) and suspected the capture fence without
proving it. Round 2 proves the mechanism and scopes the fix.

Tool: `tools/tick_audit.py` (raw samples in `.tmp/tick_audit/*.json`).
Method: poll `GET /tick_state` every 250 ms for 120 s; background load pulls
`/frame` on a schedule; per-interval rate = dticks/dt between consecutive poll
completions. Analyzer note: intervals whose poll was DELAYED (dt > 2x nominal)
are classified separately — see "the 651/s artifact" below; a burst computed
over a 1 ms dt is a division artifact, not engine behavior. TRUE mean is
(first.ticks - last.ticks) / wall time, immune to classification.

## The three measurements (120 s each, 2026-09-14)

| scenario | /frame load | clean-interval rate (mean / p1 / min, t/s) | TRUE mean (t/s) | frozen time | freeze per pull |
|---|---|---|---|---|---|
| A idle | none | 299.22 / 295.13 / 287.63 | **299.23** | **0.00 s (0.0%)** | — |
| B w512 | `/frame?w=512` every 5 s, 21 pulls | 298.56 / 279.95 / 244.93 | **252.67** | 18.39 s (15.3%) | ~876 ms |
| C full | `/frame` every 5 s, 20 pulls | 296.88 / 260.47 / 187.89 | **250.00** | 18.93 s (15.8%) | ~946 ms |

- Scenario A: 478/478 clean intervals, ZERO zero-tick windows, ZERO intervals
  above 303 t/s, zero counter resets. The loop is a metronome: 299-300 t/s
  against the 300 fps frame cap (`ChimeraEngine/engine/main.cpp:3769-3782`).
- Scenarios B/C: between captures the clean rate is still ~299.8 t/s
  (median); the entire mean loss is one long freeze per `/frame` pull.
  0 counter resets anywhere. Freeze/pull is payload-INDEPENDENT: a 559 KB
  PNG at w=512 and a 14 MB full PNG and a 9.7 KB JPEG (`fmt=jpg&q=85`)
  all freeze ~910-950 ms — so encode cost is NOT the stall.
- The stall exactly brackets each pull: ticks resume when the pull response
  completes (high-res probe, 30 ms polls: 74 ticks in a 1183 ms gap = ~936 ms
  frozen, one per pull, 21/21 aligned).

## Naming the mechanism (proven, engine-side)

**The capture servicing runs synchronously ON THE RENDER THREAD, inside
`Engine::frame()`, and costs ~0.91 s per request.** The tick
(`g_tick.step`, main.cpp:3760) runs after `frame()` returns on the same
thread, so every `/frame` (and `/glass`) request stops the tick loop for
~0.91 s.

Ground truth chain:

1. The engine's own frame-time ring (`/studio_chrome` -> `ring`, fed by
   `ui_.push_frame_time(ft_ms)`, main.cpp:3745, which brackets ONLY
   `engine.frame()`, main.cpp:3717-3722): baseline frames 0.30-0.35 ms; the
   capture frame reads **908.2 ms** (w512 jpg pull) and **912.0 ms** (full
   png pull) inside `frame()`. The stall is engine-side, inside frame(),
   not HTTP, not the client.
2. `/glass` — same freeze (~928 ms measured over ticks). Glass shares with
   capture the [submit -> `vkQueueWaitIdle(queue_)` -> map + full-res
   BGRA->RGBA swizzle] block and lacks the /frame-only pieces (the
   rt_image_ copy-record and the reel thumbnail). The freeze therefore sits
   in the SHARED block: `readback_captures()`
   (`ChimeraEngine/engine/engine.cpp:8624-8680`), called from `frame()`
   (engine.cpp:8609), both channels.
3. Payload/format independence (jpeg 9.7 KB == png 14.0 MB == 910 ms)
   rules out encode, downscale, and socket send. The remaining ~910 ms is
   the blocking wait + staged full-resolution readback executed on the
   render thread: `vkQueueWaitIdle(queue_)` +
   map/swizzle of a 14.7 MB staging buffer
   (engine.cpp:8625-8644 capture, 8650+ glass), armed by
   `request_capture()` and the handler spin
   (main.cpp:2249-2254 /frame, 2333-2338 /glass). The exact split between
   fence-wait and swizzle inside those ~910 ms is not resolvable live
   (needs one timer pair around engine.cpp:8626) — both sit in the same
   20-line function and both are removed by the same fix.
4. Why nobody saw it before: F2's instrumentation starts its clock AFTER
   the capture_ready spin (f2_t0 at main.cpp:2273), so F2 measured copy/
   downscale/encode on the HTTP thread and legitimately reported the
   encode floor it fixed — the fence/readback stall was upstream of every
   F2 timer and is still there.

### The 651/s "catch-up bursts" are an instrument artifact

The HTTP server is single-worker (proven: a `/tick_state` poll takes 1 ms
normally and hangs ~1 s, 21/21 times, while a capture is in flight — it
queues behind the capture). A delayed poll followed by an immediate catch-up
poll divides a normal dticks by a ~1 ms dt: round 1's 651.30 t/s and this
round's 1269.8 t/s max are that division, not engine behavior. The 300 fps
frame cap makes a real >300 t/s window impossible; clean intervals never
exceed 303.75 t/s in any scenario. Round 1's IDLE zeros (p1 44.18) are the
same mechanism seen from the other side: ONE stray capture (any agent or
tool pulling /frame or /glass once) contributes a ~900 ms stall — 3-4
zero-tick windows at 250 ms sampling — which is exactly the 1-2% of
intervals round 1 saw at idle. No traffic, no stalls: 0 in 120 s this round.

## The fix (scoped): retire the synchronous readback from the frame path

Keep the render-thread law for GPU work, but make the readback a two-phase
arm/collect across frames instead of a wait inside frame():

1. **Arm (render thread, in frame(), replaces the wait):** keep recording
   `vkCmdCopyImageToBuffer` into the frame's cmdbuf (engine.cpp:8474-8489)
   and the glass copy (record_glass_copy, engine.cpp:8553-8563). Submit as
   today. Then record {staging buffer, fence} as "readback in flight" and
   return. Needs a per-in-flight fence (signal a new capture_fence_ in the
   submit) and a ring of 2 staging buffers (capture AND glass in flight
   concurrently; a new request only arrives after the previous completed,
   so 2 suffice) — `ensure_capture_staging`/`ensure_glass_staging`
   (engine.cpp:6202/6231) become ring allocations.
2. **Collect (render thread, top of the NEXT frame, ~ns):** replace
   `readback_captures()`'s `vkQueueWaitIdle` with
   `vkGetFenceStatus`/`vkWaitForFences(0)` on the in-flight fence; only
   when signalled do the map + swizzle + `capture_ready_.store(true)`.
   Worst case adds one frame (~3.3 ms) of latency instead of ~910 ms of
   freeze. The ~15 ms swizzle may stay on the render thread initially
   (bounded, visible) or move to the HTTP worker (map is host-visible; hand
   the mapped pointer over under capture_mutex_) to make capture frames
   fully invisible.
3. **Protocol:** `request_capture()`/`capture_ready()` (engine.hpp:47-48)
   are unchanged; handlers keep their 3 s spin (main.cpp:2249-2254,
   2333-2338) — response latency becomes ~2 frames + encode.

Files/lines: `ChimeraEngine/engine/engine.cpp` (readback_captures split
8624-8680, copy blocks 8474-8489 and 8553-8563, staging ring 6202-6254) and
`ChimeraEngine/engine/engine.hpp` (in-flight members + fence, ~758-760,
~754). ~120-180 lines, 2 files, no route changes, no third file.
Prediction before the run: scenario C's TRUE mean returns to >= 295 t/s
(frozen fraction 15.8% -> <1%), with /frame response latency unchanged
within +10 ms. Falsifier: if a capture frame still shows >50 ms in the
`/studio_chrome` ft ring after the fix, the wait was not (only) in
readback_captures — instrument `vkQueueWaitIdle` vs swizzle next.

## Follow-ups (other lanes' files)

- bench.py (A2): compute rates only over consecutive successful polls and
  bucket delayed polls (dt >> interval) as stall evidence, never as rate
  samples; the 651 t/s catch-up figure is an artifact and should not
  survive into the next verdict.
- F2 (build window): move f2_t0 BEFORE the capture_ready spin (one line,
  main.cpp:2273) so the fence cost is visible in the bench log.
- The idle-stall class round 1 saw is real but rarer than measured: any
  single /frame or /glass pull by ANY agent during a bench window poisons
  p1. Bench scenarios should assert no other HTTP clients, or sample the
  engine's capture_state (`/capture_state`, main.cpp:3065) alongside.

## Addendum — external restart after the measurements (2026-09-14 00:47:59 local)

After all three 120 s windows and every probe completed, the engine was
restarted by something outside this lane (new PID 3176, same binary, no
watchdog event — not this agent; this lane never stops the engine). All
measurements above were taken against the previous instance (PID 38960) with
ZERO counter resets inside any measured window; the restart therefore does
not touch the data. Reproduction check on the new instance, scenario A re-run
(120 s): mean 299.19 t/s, p1 295.58, 478/478 clean intervals, 0 zero windows,
0 resets — the idle profile is identical. The restart itself (cause: another
lane's build window or a crash) is outside this lane's file scope and is
handed to whoever owns the 00:47 window.
