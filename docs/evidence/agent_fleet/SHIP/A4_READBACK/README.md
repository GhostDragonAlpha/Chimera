# A4_READBACK — the Q3 readback discrimination harness (Astra spec)

Fleet agent A4 "readback-probe", 2026-09-14. Builds and runs
`tools/readback_probe/` (standalone headless Vulkan, NOT the engine).

## Spec provenance

The harness follows **Astra's Q3 harness spec exactly** (as relayed by the lead):

> Headless standalone (no swapchain, no window). One preallocated source image,
> one PERSISTENTLY MAPPED, host-cached staging buffer. Reuse everything across
> iterations. Start with BUFFER→BUFFER copies; then substitute the real
> IMAGE→BUFFER copy. Valid copy→host-visibility dependency (barrier/fence),
> wait on THAT submission's fence, invalidate the mapped range if noncoherent.
> ONE CONTINUOUS MONOTONIC WALL-CLOCK TIMELINE per iteration: request →
> submission entry/return → fence-wait entry/return → invalidate entry/return →
> first CPU read → completed memcpy into ordinary RAM → completed swizzle in
> ordinary RAM → consumer receipt. Plus GPU timestamps around the copy
> (retrieved after completion). Separately time initial allocation/map and
> teardown. Include queue-lock acquisition / worker wakeup intervals if
> applicable.

Variation matrix rows 1–5 (cold vs warm; 4 B vs 8.3 MB; no-CPU-access; read /
memcpy / swizzle split; idle vs queued backlog) are all present as cells below,
plus the decisive signatures Astra named: paging, scheduling, queue
serialization, CPU-side blocking, device-wide stall.

## What was built

- `tools/readback_probe/readback_probe.cpp` — one file, Vulkan 1.1, no window,
  no surface extension, no swapchain. Single queue family (RTX 4090, driver
  566.36-era, tsPeriod 1 ns, ReBAR yes). Mirrors the engine's Vulkan setup
  (same SDK `C:/VulkanSDK/1.4.328.1`, direct `vulkan-1.lib` link, MSVC
  `Visual Studio 18 2026`, per `ChimeraEngine/engine/CMakeLists.txt`).
- Per iteration it records ONE continuous QPC timeline
  (ns since process start): `request, submit_entry, submit_return,
  fwait_entry, fwait_return, invalidate_entry, invalidate_return, first_read,
  memcpy_done, swizzle_done, consumer, gpu_ts_retrieved` (+ backlog/witness
  markers), plus two GPU timestamps bracketing the copy (query pool, read
  after fence). Allocation/map and teardown are timed separately.
- Regimes: `{img8M, img4B, buf8M, buf4B} × {full, noread} × {idle, backlog}`
  (16 cells), plus `witness` (independent 64 KB job on a second queue,
  fence-polled during the readback wait), `idlesleep` (3 s GPU idle between
  pulls), `nofence` (engine-shape: copy submitted, fence wait OMITTED, straight
  to the mapped read — where does the wait land when the dependency is
  missing?), and `pressure` (19 GB of device-local buffers committed and
  re-filled every iteration, then the standard readback).
- N=40 warm per cell (+cold iter0), 20 witness, 10 idlesleep. Two processes:
  matrix (`--nopressure`) and pressure (`--pressure 20`), each with its own
  clean process-cold first pull.

Run it:

```bash
cmake -S tools/readback_probe -B tools/readback_probe/.tmp/build \
      -G "Visual Studio 18 2026" -A x64 -DVULKAN_SDK="C:/VulkanSDK/1.4.328.1"
cmake --build tools/readback_probe/.tmp/build --config Release
cd tools/readback_probe && mkdir -p .tmp/results/matrix .tmp/results/pressure
./.tmp/build/Release/readback_probe.exe --nopressure --out .tmp/results/matrix
./.tmp/build/Release/readback_probe.exe --pressure 20 --out .tmp/results/pressure
```

## Files

- `RESULTS.md` — the tables + the finding (relay to Astra).
- `summary_matrix.md`, `summary_pressure.md` — exe-generated per-regime
  segment tables (median/max).
- `raw_timeline_matrix.csv`, `raw_timeline_pressure.csv` — every iteration,
  full continuous timeline (raw numbers).

## Known harness caveats (read before quoting numbers)

1. **`consumer` segment is a hash over the swizzled buffer** (~6.1 ms for
   8.3 MB — O(n) byte FNV). It inflates the old "e2e" line; the decisive
   readback number is **e2e_read = request→swizzle_done**, which the summary
   reports separately.
2. **`invalidate` is a no-op on this driver**: the 4090 driver exposes NO
   non-coherent cached host type (types: 2 = HTV|COHERENT, 3 = HTV|COHERENT|
   CACHED, 4 = ReBAR HTV|COHERENT|DEVLOCAL), so per the spec ("invalidate the
   mapped range if noncoherent") the invalidate step degenerates to µs. The
   mapped-access question is instead answered by first_read/memcpy/swizzle.
3. Witness `fwait` uses a 0.5 ms poll loop (that regime only) — its
   fence_wait/granularity is poll-limited by design; `first_read` ~113 µs in
   that cell is poll granularity, not a stall.
4. Single-threaded, no worker/queue-lock (render-thread-inline analog);
   Astra's "queue-lock acquisition / worker wakeup intervals" are N/A here and
   remain an engine-side instrument.

## Next matrix rows (what the standalone does NOT have — the follow-up)

1. **Swapchain + present interleaved** with the readback (flip queue, present
   fence retirement, DWM, occlusion states). The known engine datum — "a
   reader thread's map+read stalled the render thread's submit/present" —
   points here first.
2. **Readback submitted after render+present on the SAME queue** (frame-scale
   backlog): our row-5 mechanics predict the pull then inherits the whole
   frame's queued latency, size-independent.
3. **Port this exact timeline schema into the engine's pull path** (same
   markers + GPU timestamps). Wherever the ~900 ms lands in THAT timeline
   names the mechanism directly; the segments here map 1:1.
4. **Per-frame alloc/free churn in the pull path** (heavier WDDM
   commit/demote cycles than our pinned 19 GB) — check the engine's pull for
   per-frame `vkAllocate*`/`vkFree*`.
