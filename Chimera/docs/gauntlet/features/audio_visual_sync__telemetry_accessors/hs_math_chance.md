# High: chance — audio_visual_sync/telemetry_accessors

Randomness deliberately lives in only one place upstream: cosmetic pitch/volume
variance on the crunch (±4%), which never touches timing. The measurement
itself is deterministic by design — same walk, same frame timing, same deltas.

Expected value of a typical interaction: delta ~= +10 to +15 ms at 60 fps
(audio buffer quantization dominates). Worst case a player hits through no
fault of their own: a loading hiccup or GC spike displaces one visual frame,
producing a single sample near ±35 ms — still inside the window, and the
rolling mean absorbs it. Determinism is right here because this feature IS the
measuring instrument: an instrument with dice in it cannot indict anything —
every flake it reported would be deniable.
