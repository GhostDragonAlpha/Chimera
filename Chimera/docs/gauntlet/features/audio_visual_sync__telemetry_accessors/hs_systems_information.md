# High: information — audio_visual_sync/telemetry_accessors

What it HIDES from the player: everything. No latency meter, no step counter,
no debug overlay in the shipped experience — the player must live inside the
illusion the numbers protect, never see the scaffolding. Concealment serves
play because sync is preattentive: the moment a player is shown a sync metric
they start hearing problems that aren't there (measurement anxiety is real in
rhythm games' calibration screens — the lesson is calibrate silently).

What it REVEALS, and to whom: to the sleepwalker and the graph, everything —
counts, latency distribution, per-surface breakdown, orphan events. The
information asymmetry is the design: audio_visual_sync/telemetry_accessors is
a one-way mirror where the studio watches the conversation between boots and
ground without the player ever feeling observed.
