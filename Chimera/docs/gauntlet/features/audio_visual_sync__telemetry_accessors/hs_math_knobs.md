# High: the three knobs — audio_visual_sync/telemetry_accessors

- **Sync window bounds** — lead limit / lag limit, default -45 ms / +125 ms.
  Sane range: lead -20 to -60 ms, lag +80 to +160 ms. Outside it: tighter than
  -20 ms fails every build on scheduler jitter alone; looser than +160 ms
  passes desync a reviewer would name in a headline.
- **Debounce window** — default 120 ms coalescing for double-fires. Sane range:
  80 to 200 ms. Below 80 ms sprint double-fires count as real steps; above
  200 ms genuine sprint strides (up to 4 steps/s = 250 ms apart) get eaten.
- **Sample window size** — rolling window the accessors aggregate, default 64
  samples. Sane range: 16 to 256 units. Under 16 one hitch dominates the mean;
  over 256 a regression hides inside old good data for whole minutes of play.
