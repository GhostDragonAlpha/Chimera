# Elementary: one-liner twice — audio_visual_sync/telemetry_accessors

To a 10-year-old: it's the part of the game that checks your footsteps sound
exactly when your feet touch the ground, so the moon never feels like a video
that's out of sync.

To a senior designer: audio_visual_sync/telemetry_accessors is the runtime
instrumentation surface on SandSoundComponent exposing footstep-event counts
and audio-to-animation latency samples, so automated playtests can assert the
sync budget without a human ear in the loop.

The two sentences agree: the player hears the promise; the accessors are how
we measure that the promise was kept.
