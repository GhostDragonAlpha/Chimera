# High: units — audio_visual_sync/telemetry_accessors

Quantities and units: time offsets in milliseconds (ms) stored as float;
footfall cadence in steps/s (walk ~1.6, sprint up to 4 steps/s); pawn velocity
in UE units/s (cm/s — 100 units = 1 m) used only to gate stride validity;
counts in whole units. Nothing here integrates over ticks — the feature
SAMPLES event pairs rather than accumulating a quantity, which is its
determinism shield.

Frame-rate dependence lives in one seam: visual contact time is quantized to
frame boundaries (16.7 ms at 60 fps, 33.3 ms at 30 fps) while audio start is
quantized to audio buffer boundaries (~10.7 ms at 512 samples / 48 kHz). The
measured delta therefore carries up to one frame of jitter by construction —
which is why the window is defined wide enough to hold the fps floor, and why
samples must record the frame time they were taken at.
