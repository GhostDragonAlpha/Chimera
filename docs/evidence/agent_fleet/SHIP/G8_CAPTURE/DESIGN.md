# G8 — TWO-PHASE ARM/COLLECT CAPTURE READBACK

Agent: H3 "capture-readback" (design + implementation, uncommitted) · finished and
desk-checked to compile-ready by H3f "capture-finisher" (2026-09-13) · root cause
named in commit f1ac0b5f, measured in [../R6_BENCH/tick_counter_audit.md](../R6_BENCH/tick_counter_audit.md).

## 0. THE ANSWER TO THE OPEN QUESTION

The BEFORE burst (`verify_g8_before_async_burst.json`) pulled `/frame?async=1` and
got 10/10 stalled pulls. **Measurement preceded implementation**: `git show
HEAD:ChimeraEngine/engine/main.cpp` has ZERO occurrences of "async" — on the
pre-G8 binary `?async=1` was an unknown query param, silently ignored, and the
pull ran the synchronous path. H3's diff is what creates the async contract.
(The verifier itself lives beside this file: `verify_g8_capture.py`.)

## 1. MECHANISM (H3's design, reconstructed from the diff)

The old servicing (`readback_captures`, called from `Engine::frame()` and
`frame_idle_ui()`) did `vkQueueWaitIdle(queue_)` + map + full-res BGRA→RGBA
swizzle ON THE RENDER THREAD — ~910 ms per grab, payload-independent — freezing
the tick loop that runs on the same thread after `frame()` returns. Between
grabs the loop is a metronome at ~297 t/s.

The replacement is an **arm/collect state machine over a staging ring**, keeping
render-thread exclusivity for all GPU work:

- **ARM** (render thread, mid-command-buffer-recording): `arm_capture_readback()`
  / `arm_glass_readback()` pick a free slot from a 2-deep staging ring per
  channel (`capture_rb_[RB_SLOTS]`, `glass_rb_[RB_SLOTS]`; `RB_SLOTS = 2`),
  (re)size its host-visible coherent buffer to the CURRENT extent
  (`rb_ensure_slot` — a resize between arm and collect cannot change an
  in-flight slot's geometry; the slot records its own w/h), record
  `vkCmdCopyImageToBuffer` (capture) or have the caller record `record_glass_copy`
  (glass) into the frame's cmdbuf, stamp `{frame_slot, w, h, seq, in_flight}`,
  and return. NO WAIT — the frame's normal `vkQueueSubmit` carries the copy.
  `seq = ++capture_armed_gen_` is the arm-order watermark. A full ring just
  re-stores the request flag (`capture_requested_` / `glass_requested_`) and the
  arm is retried next frame.
- **COLLECT** (render thread, end of frame, at the exact site the old blocking
  readback occupied): `collect_readbacks()` polls every in-flight slot with
  **zero-timeout** `vkGetFenceStatus` on the frame fence the slot rides
  (`fences_[frame_slot]`, `MAX_FRAMES_IN_FLIGHT = 2`); only ALREADY-signalled
  slots get mapped + swizzled, oldest seq first, into `capture_rgba_` /
  `glass_rgba_` under their mutexes. A not-yet-finished slot stays pending for a
  later frame: worst case one frame (~3.3 ms at the 300 fps cap) of added
  latency instead of ~910 ms of freeze. No fences are created — the design
  reuses the per-frame-in-flight fences, which is sound because of the
  pre-existing "reset happens at the submit site, immediately before
  vkQueueSubmit" law (engine.cpp, the NOTE above the strain overlay).
- **THE FENCE-GENERATION LAW** (the one real bug H3f found and fixed — see §5):
  between a frame's frame-start `vkWaitForFences` and its `vkResetFences`, the
  fence still carries the PREVIOUS submit's signal. A collect in that window
  must ignore slots armed in the CURRENT frame (their copy was never submitted;
  the "passing" fence check would publish the staging buffer's PREVIOUS bytes
  and falsely advance the watermark). Both loops therefore snapshot
  `capture_armed_gen_` at entry (`g8_armed_before`) and the pre-reset backstop
  filters `seq <= g8_armed_before`.
- **THE BACKSTOP**: `collect_for_frame_slot(img_idx, 100, g8_armed_before)`
  runs before every `vkResetFences`. If an OLD slot (armed a previous frame)
  still rides the fence about to be reset, it capped-waits (100 ms) so the reset
  can never destroy the only proof the copy finished — reachable only when the
  device is ≥ MAX_FRAMES_IN_FLIGHT frames backlogged. In practice it is a scan
  of 4 slot flags (~ns): the frame-start fence wait already guarantees the
  fence signalled, so the normal end-of-frame collect drained everything.
  With the §5 guard, this wait cannot block on current-frame arms.
- **TICK-LOOP SANCTITY** (verified by reading, not building): the only waits on
  the render/tick path are (a) the PRE-EXISTING frame-pacing
  `vkWaitForFences(..., UINT64_MAX)` at frame start, which exists with or
  without captures, and (b) the backstop's capped 100 ms, which as above cannot
  actually block on a current-frame arm and exists to preserve proof for
  old-generation slots. No `vkQueueWaitIdle`/`vkDeviceWaitIdle` remains on any
  per-frame path (resize/shutdown device-idles are rare and pre-existing). The
  zero-timeout collect polls completed state only.
- Reel law carried over: `reel_note_grab()` fires per capture COLLECT (was: per
  sync grab in `frame()` only). Idle-path grabs now land in the reel too, which
  is D3's law ("every grab lands") made literal; capped at `StudioUI::REEL_MAX`.

## 2. THE /frame CONTRACT (exact)

One route, two modes (`/stream` is the same handler):

- **`GET /frame`** (and `?sync=1` spelled out) — **STRICTLY FRESH**, byte-identical
  semantics to pre-G8: this request's own capture is armed and collected before
  the answer. Implementation: read `want = capture_arm_watermark() + 1`, arm via
  `request_capture()`, spin on `capture_collected_since(want)` (3 s deadline,
  `Sleep(5)`) **on the HTTP worker** — the single-worker server serializes
  pulls, and only the HTTP thread ever arms captures, so `want` can only be
  reached by this request's own arm's collect. The watermark is load-bearing: a
  bare `capture_ready()` could be satisfied by a stale slot an earlier `?async=1`
  pull left in flight. Timeouts answer `{"ok":false,"error":"capture timeout"}`.
  The scrub loop (`/capture_render`) uses the identical watermark pattern per
  frame.
- **`GET /frame?async=1`** — **TWO-PHASE**: arms (CAS, only if nothing already
  requested; a full ring defers the arm one frame) and returns IMMEDIATELY with
  **PRIOR FRAME BYTES** — the last COLLECTED capture encoded as usual
  (`image/png`, or `image/jpeg` with `fmt=jpg`/`q=`; `w=` downscales before
  encode). H3 documented the alternative (empty 202-style body / Retry-After)
  and rejected it so every response stays an IMAGE for naive `.read()` callers.
  Only when NO capture has ever completed does it answer the legacy
  `{"ok":false,"error":"no frame"}` JSON. Freshness sits one arm-collect cycle
  (~2 frames) behind the default; `sync=1` wins if both params are present.
  `?async=1` composes with `w=`/`fmt=`/`q=` (substring parse, same hand-rolled
  law as the F2 params — `query_has`/`query_uint`, main.cpp:435-446).

F2's bench timers (`CHIMERA_FRAME_BENCH`) shifted one beat (t0 now starts after
the capture fetch, which moved into the contract branches); the encode-phase
numbers remain valid. Encode path otherwise UNTOUCHED.

## 3. PER-CALLER COMPATIBILITY VERDICTS

Default route keeps blocking strict-fresh semantics, so **every existing caller
works unchanged**; none uses `?async=1` except the verifier. Survey (all read,
none edited — tools/ has other owners):

| caller | pulls | verdict |
|---|---|---|
| `ChimeraEngine/cpp_bridge.py::fetch_frame` (all movie renderers, dyad judges) | plain `/frame` | OK unchanged — bytes postdate the request, as before. `_settle_capture`/`wait_for_frame_change` refetch-until-different, self-heals any skew |
| `tools/tick_audit.py` (the audit harness) | `/frame?w=512`, `/frame` every 5 s | OK unchanged (sync) |
| `tools/game_shell/bench.py:276` thumbnail channel | `/frame?w=1024` every 2 s | OK unchanged (sync). Optional opt-in: append `&async=1` — the thumbnail channel tolerates one-behind bytes |
| `tools/trailer/make_trailer.py:157` | `/frame?w=1920` ~1/s | OK unchanged — and KEEP sync: it interpolates camera BETWEEN captures, so each frame must postdate its `/camera` POST |
| `tools/gallery/run_gallery.py:269` | `/frame?w=900` | OK unchanged (sync; fit-then-capture wants fresh) |
| `tools/dyad_timed_capture.py`, `window_battery.py`, `kernel_axis_probe.py`, `seal2_run.py`, `mitosis_run.py`, `feet_only_scene.py`, `feet_splat_membrane.py`, `jnt2_tear_probe.py`, `membrane_demo_client.py`, `membrane_window_demo.py`, `product_features{,_walk}/*`, `product_viewer/server.py`, `r8_media/capture_beauty.py`, `store_art/make_art.py` | plain `/frame` (+params) | OK unchanged (sync; proof PNGs and portraits are freshness-critical) |
| `verify_g8_capture.py` (this directory) | `?async=1` burst (default) / `/frame` (`--pull`) | the intended async consumer; both paths live |
| `method.py` `/frame?term=` | gallery server, NOT the engine | out of scope |

## 4. BEFORE NUMBERS (live 8107, pre-G8 binary; files in this directory)

- quiet: **17,839** / 17,865 ticks/min, max zero-tick stall **4.4** / 3.7 ms
- `/frame?async=1` burst: **9,389** ticks/min, max stall **1,010.5 ms**,
  10/10 pulls at **1,134-1,195 ms** each
- `/frame` burst: **9,654** ticks/min, max stall **1,028.0 ms**, 10/10 pulls at
  **1,106-1,157 ms** each
- stall bar: burst ticks within 2x of quiet AND max stall ≤ 200 ms — the rate
  bar passed, the stall bar FAILED both runs (this is the BEFORE evidence).

## 5. WHAT H3f CHANGED (the one substantive repair)

H3's three files were otherwise complete (every header symbol implemented, both
loops wired, route + scrub route consistent, brace/paren balance identical to
HEAD, no `small` typedef collision, no JSON-boolean parsing). The bug found by
tracing fence generations:

**Backstop false-collect.** `collect_for_frame_slot()` matched ANY in-flight
slot riding `fences_[img_idx]` — including the slot armed THIS frame (the arm
stamps `frame_slot = img_idx` and runs before the backstop). In the pre-reset
window the fence still carries the PREVIOUS submit's signal (the frame-start
wait guarantees it), so the zero-timeout check passed, `collect_readbacks()`
mapped and published a copy that was never submitted — the staging buffer's
previous contents (≈2 frames stale, or undefined on first use) — marked the
slot collected, advanced `capture_collected_gen_`, fired `capture_ready_`, and
logged a stale reel grab. EVERY capture frame hit it: strict pulls would serve
stale bytes and the async ladder would serve garbage. Same pattern in
`frame_idle_ui()`.

**Fix** (engine.hpp + engine.cpp): both loops snapshot
`const uint64_t g8_armed_before = capture_armed_gen_.load();` at entry (before
any arm is possible); `collect_readbacks(uint64_t armed_before = UINT64_MAX)`
gains the guard `slot.seq <= armed_before` in both channel scans; the backstop
takes and passes the snapshot. End-of-frame collects keep the default — after
reset+submit the fence signal they observe is the copy's own generation.
`frame()` and `frame_idle_ui()` call sites updated; the G8 block comment and
header comments record the law. Re-desk-checked: all 6 call sites consistent,
balance deltas zero vs HEAD.

## 6. LEAD'S BUILD WINDOW (build → relaunch → verify → expected bars)

The live engine (127.0.0.1:8107, PID 38960, binary
`.tmp/build_tick/Release/chimera_engine.exe`) is NOT to be touched outside the
window. The lead owns stop/start; builds serialize through the lead.

```bash
cd /e/ChimeraWork/slot-01
# 1. BUILD (desk-checked only — never compiled)
cmake --build .tmp/build_tick --config Release --parallel 4
# 2. RELAUNCH (lead only): stop the live instance, start the new exe with the
#    SAME command line and working directory as the current instance
#    (chimera_engine.exe [port] [genome] [width] [height], port 8107).
# 3. VERIFY — both bars must PASS (exit 0):
python docs/evidence/agent_fleet/SHIP/G8_CAPTURE/verify_g8_capture.py --tag after_async
python docs/evidence/agent_fleet/SHIP/G8_CAPTURE/verify_g8_capture.py --pull /frame --tag after_default
```

EXPECTED BARS: `burst_within_2x_quiet` PASS (burst ticks/min should now sit
NEAR quiet ~17-18k — the render thread no longer freezes; pulls complete in
~2 frames + encode on the HTTP worker) and `max_stall_ms_le_200` PASS (worst
render-thread readback cost is now the map + swizzle + reel thumbnail, tens of
ms, amortized one slot per frame; the backstop cannot block on current-frame
arms per §1/§5). Sanity checks in the same window: one plain `/frame` returns a
fresh full-res PNG; one `/frame?async=1` returns an image immediately; a
`/capture_render` short scrub produces frames without "capture timeout".

## 7. ROUND 2 — THE AFTER BAR FAILED: THE REAL ROOT CAUSE (2026-09-14, H3f)

The lead's build window ran (fresh exe, engine.obj mtime 09:11 > the G8 commit;
PID 43248 started 09:12:44) and the AFTER bar FAILED identically to BEFORE:
async ≈ sync ≈ ~950 ms per pull regardless of size/format, tick deficit ≈ pull
duration, quiet clean (17.9k ticks/min, ~4 ms gaps).

### The measurements that pinned it (light GET probes against the live 8107)

1. **The freeze is inside `Engine::frame()`**: the `/studio_chrome` frame-time
   ring (brackets ONLY `engine.frame()`) showed exactly one ~940-965 ms frame
   per pull, all others 0.5 ms — the tick loop stalls once per pull.
2. **The HTTP worker is blocked the SAME window**: a 30 ms-cadence
   `/studio_chrome` poller got zero responses during each pull's window
   (TTFB = total = ~950 ms on a raw socket). The async handler blocks on
   `capture_mutex_`, which the render thread holds across the collect's
   map+swizzle scope.
3. **The collect (map+swizzle) is the cost, not the arm**: the SYNC pull's
   spin exits at `capture_collected_gen_.store` — which sits AFTER the
   swizzle, BEFORE `reel_note_grab` — and sync TTFB is ~950 ms, pinning the
   stall inside the swizzle scope, not the reel path.
4. `/glass` (same collect machinery, its own mutex) totalled 1125-1174 ms =
   glass swizzle+spin (~950) + the full-res PNG encode (~80 ms: png_encoder.hpp
   is STORED-deflate — pure copy + CRC32, never the 1.1 s F2-era folklore).
   BOTH channels' collects are slow.

### Root cause

`rb_ensure_slot` allocated staging with `find_mem_type(VISIBLE|COHERENT)`,
which returns the FIRST matching type. **The box is an RTX 4090 with Resizable
BAR ON** (`nvidia-smi`: BAR1 Total = 32768 MiB), so NVIDIA's type list is
`[0] DEVICE_LOCAL (VRAM), [1] DEVICE_LOCAL|HOST_VISIBLE|HOST_COHERENT (BAR1 —
UNCACHED), [2] HOST_VISIBLE|HOST_COHERENT (cached sysmem)` — and type 1 (BAR)
matches first. Every staging byte the swizzle reads is a PCIe transaction:
8.3 MB of 4-byte-strided reads ≈ **~940 ms ON THE RENDER THREAD**, holding
`capture_mutex_`. Payload/format-independent ✓ (full-res swizzle regardless of
`?w=`), async ≈ sync ✓, quiet clean ✓ (no grabs, no reads).

**The pre-G8 "~910 ms vkQueueWaitIdle" (R6 audit) was THE SAME READ all
along** — the audit's own footnote: "the exact split between fence-wait and
swizzle inside those ~910 ms is not resolvable live". F2's "the ~1.1 s floor
lived in the ENCODE" was also misattributed (the encode is ~80 ms; the floor
was capture servicing + encode on one worker).

### The fix (engine.hpp + engine.cpp only)

**THE READBACK MEMORY LAW**: capture/glass staging must be CPU-cached sysmem —
never a DEVICE_LOCAL BAR allocation. `rb_ensure_slot` now picks the memory type
by property passes: (0) host-visible & non-local & coherent → (1) non-local &
cached → (2) any non-local → (3) coherent (the old law, kept as fallback) →
(4) the old `find_mem_type` last resort. On this 4090 pass 0 lands on type 2
(cached sysmem, coherent): the swizzle drops from ~940 ms to single-digit ms.
When the picked type lacks HOST_COHERENT (some AMD/Intel stacks), the slot is
flagged (`ReadbackSlot.noncoherent`) and the collect issues
`vkInvalidateMappedMemoryRanges` (VK_WHOLE_SIZE: the whole allocation is mapped
from 0, which also keeps the nonCoherentAtomSize-multiple VUID moot) before the
CPU read. `dispatch_compute`'s staging (engine.cpp:716 `host_mt`) shares the
same first-match hazard but is not pull-correlated — flagged for its owner,
not touched.

### Expected AFTER-round-2 numbers

- `/frame?async=1`: TTFB/total ~30-80 ms (arm + fast collect + encode) — the
  prior-frame contract finally measurable as "immediate".
- `/frame` (sync): ~50-150 ms (2-frame fresh collect + encode).
- burst ticks/min ≈ quiet (worst collect frame ~10-30 ms on the ring),
  max_stall ≤ ~50 ms — both bars PASS with margin.
- `/glass`: ~100-200 ms (fast swizzle + full-res PNG encode).

Same verify commands as §6. If a bar still fails, the ring + TTFB probes above
localize any residual in minutes.

## 8. ROUND 3 — THE BAR1 LAW WAS ALSO NOT THE STALL: THE COLLECT LEFT THE RENDER THREAD (2026-09-14, H3f)

AFTER2 (round-2 binary, cached-sysmem staging verified in-tree): async pulls
1068-1087 ms, worst tick gap 932 ms — identical signature. Memory bandwidth was
the second misattribution.

### Round-3 probes (live 8107, independent observer PROCESS + ring + TTFB)

- **Tick truth**: the membrane tick counter is stepped on the render loop
  (main.cpp, `g_tick.step` after `engine.frame()`) — an independent-process
  /tick_state observer showed the loop genuinely frozen ~900 ms per pull
  (+10 ticks across a 941 ms bracket), then full rate again. The verifier's
  deficit metric is engine-side real (not an observer artifact).
- **The freeze is one `frame()` call**: the ring (brackets ONLY
  `engine.frame()`) carried a single ~914-965 ms entry per pull; every other
  frame 0.5 ms.
- **The worker is blocked the whole window**: raw-socket TTFB = total =
  ~930-950 ms (observer rows starved exactly across the pull). The async
  handler's only engine-side block is `capture_mutex_`, held by the render
  thread across the collect's map+swizzle scope ⇒ the collect itself costs
  ~900 ms EVEN WITH cached-sysmem staging. `reel_note_grab` runs after the
  watermark store the sync spin waits on — exonerated. `reel_push`'s
  `vkQueueWaitIdle` likewise downstream of the sync spin — exonerated.
- Note on observer discipline: during a pull the single-worker HTTP server
  starves ALL observers; their in-flight rows carry start-of-request
  timestamps with post-stall content. Post-hoc ring reads (the spike persists
  ~400 ms in the 120-frame ring) and bracket tick deltas are the reliable
  views; the probes above used both.

### What round 3 ships

1. **THE COLLECT LEFT THE RENDER THREAD (the fix that cannot miss the bar)**:
   `collect_readbacks` now only fence-checks and ENQUEUES finished slots
   (µs, render thread); a dedicated **reader thread** (`rb_reader_loop`,
   spawned at end of init, joined first in shutdown) owns every slow op —
   `vkMapMemory` → optional `vkInvalidateMappedMemoryRanges` → BGRA→RGBA
   swizzle into a reused scratch → `vkUnmapMemory` → publish under the channel
   mutex (pointer **swap**, so the async handler's `capture_frame` never waits
   behind a slow read) → watermark/ready stores → `in_flight=false` (now
   atomic). The reel moved with it: the reader sets `reel_pending_`; the
   render thread consumes it next frame and runs `reel_note_grab` from the
   already-published bytes (snapshot under `capture_mutex_` — the old
   unlocked read became cross-thread). The render thread's entire readback
   cost is now fence checks + enqueue + a pointer exchange: the tick bar is
   met BY CONSTRUCTION, whatever the mystery call is.
2. **PHASE TIMERS**: `/studio_chrome` gained `ph_fence_us`, `ph_coll_us`,
   `ph_pres_us` (last frame's fence-wait / collect / present, µs) — the split
   the R6 audit said was unresolvable. If any stall survives window #3, these
   three numbers name the phase immediately.
3. **`rb_mem_type` / `rb_mem_flags` on `/studio_chrome`**: the memory type the
   selection law actually picked — settles "is it still BAR?" in one GET
   (round 2's open question).
4. **RIDER `pick_cam` Z-flip (engine.cpp, `/tick_touch` cam-form)**: the web
   kernel's eye was reconstructed with `target.z - r*c*cos(phi)` (the engine's
   render-side law) while the page renders `target.z + r*ch*cos(theta)` — the
   pick ray started mirrored through the target (click front → dent far
   side, operator-measured). Fixed to `+ r*c*cos(phi)`, matching the page
   (source of truth). The engine-camera `{px,py}` form uses `pick()` —
   untouched; the `{"hit"}` form bypasses picking — untouched.
5. **RIDER `host_mt` (engine.cpp:716, UI stage memory): NOT applied.** The
   round-2→round-3 evidence exonerates memory selection for the stall (the
   collect stayed ~900 ms after staging moved to sysmem), and the UI's stage
   buffer is write-only in its hot path (BAR writes are write-combined fast).
   Revisit only if the new `ph_*`/`rb_mem_*` instruments ever indict it.

### Build window #3 — expected numbers

Same commands as §6 (`--tag after3_async` / `--pull /frame --tag after3_default`).
- `/studio_chrome` quiet: `ph_fence_us` ≤ ~3500 (the pacing wait), `ph_coll_us`
  ≤ ~100 (enqueue only), `ph_pres_us` ≤ ~1000; `rb_mem_type` = the sysmem
  index, `rb_mem_flags` has HOST_VISIBLE (+COHERENT or CACHED), **no
  DEVICE_LOCAL**.
- Burst: ticks/min ≈ quiet (the render loop's per-pull cost is now fence
  checks + enqueue + an occasional ~20 ms reel ledger), max tick gap ≤ ~50 ms
  — **both bars PASS by construction of the render-thread path**.
- Pull durations: async ~30-80 ms (truly immediate); sync ~1.0 s the first
  time the reader's read is slow (its wait is client-side, contract preserved)
  or ~100 ms if the round-2 memory law did fix the read and the residual stall
  was elsewhere — `ph_coll_us` decides which world we are in.
