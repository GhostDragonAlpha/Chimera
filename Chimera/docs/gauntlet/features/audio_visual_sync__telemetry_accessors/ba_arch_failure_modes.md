# Bachelor: failure modes — audio_visual_sync/telemetry_accessors

- **Component never attached** to BP_Astronaut_Character (the live suspicion on
  tb-0001): every accessor returns initializer defaults forever. Caught by:
  gate_playtest_no_failures via the liveness beat (count > 0 expect) — and by
  the H-22 read-back discipline before staging.
- **Initialization-order miss** — the component attaches but subscribes to
  contact events AFTER the first strides, or its counters reset on possess:
  undercounted steps, plausible-but-wrong latency. Caught by:
  gate_playtest_no_failures with the zero-state edge beat (read accessors
  before first stride, then after ten strides), per the H-31 family.
- **Silent default poisoning** — latency initialized to 999 ms (or count to 0)
  leaks into aggregates when no sample exists, so means lie. Caught by:
  gate_build_succeeded won't see it — it is a runtime lie — so the beat schema
  must assert NO-SAMPLE sentinels explicitly (H-32), and result_grader's
  criteria coverage fails the feature if that expect is missing.
