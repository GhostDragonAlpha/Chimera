# Elementary: three games — audio_visual_sync/telemetry_accessors

- **Death Stranding** — the gold standard for footfall truth: per-surface,
  per-load audio tied to a full locomotion model; did well: terrain and strain
  audible every step; did poorly for our lens: all tuned by human QA ears, no
  public telemetry story to imitate.
- **No Man's Sky** — per-biome footstep sets that sell alien ground cheaply;
  did well: material-to-sound mapping at planetary scale; did poorly: sync
  slop is noticeable at low frame rates because audio follows anim notifies
  without compensation — exactly the drift a measured window would catch.
- **Astroneer** — soft regolith crunch as core game-feel on low-gravity soil;
  did well: sound sells traction on slopes; did poorly: sprint transitions can
  double-fire or drop steps — a count-based telemetry accessor like ours would
  have flagged the double-fire in CI instead of in reviews.
