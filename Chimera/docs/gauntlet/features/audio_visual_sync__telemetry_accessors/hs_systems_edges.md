# High: edges — audio_visual_sync/telemetry_accessors

- Zero-state (first use): read the accessors before the first stride ever
  lands. Intended: count=0, latency reads as NO SAMPLE (null/NaN sentinel), not
  a fake number — the current 999 ms initializer is precisely the corruption of
  this edge, making emptiness look like slowness.
- Spam case (input mash): rapid W-tap jitter producing sub-stride shuffles.
  Intended: the 120 ms debounce coalesces micro-contacts; count rises no faster
  than physical cadence allows (max ~4 steps/s sprinting); no sample storm.
- Boundary value (stationary sound): a crunch fires with velocity == 0 (audio
  triggered by a stray notify). Intended: the sample is recorded AND flagged
  orphaned — orphan count is its own accessor, because a step without a stride
  is a worse lie than a late step.
