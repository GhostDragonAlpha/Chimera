# Middle: juice — audio_visual_sync/telemetry_accessors

One cheap addition: pitch variance — ±4% random pitch per crunch, velocity-
scaled volume, so no two strides are clones. It costs nothing and kills the
machine-gun sameness that makes synced footsteps feel LESS real the more
perfect they get.

Where juice becomes noise for this feature: anything that widens timing.
Layering a delayed dust-settle whoosh, reverb tails, or randomized start
offsets smears the very onset the sync window measures — juice for footsteps
must live in pitch and volume, never in TIME. If a juice pass moves the
measured latency histogram of audio_visual_sync/telemetry_accessors, the juice
is lying about physics and must be cut.
