# High: the loop — audio_visual_sync/telemetry_accessors

Trigger: a footfall contact event from locomotion animation. Player action:
none beyond walking — this loop rides the movement verb. Resource delta: one
audio voice spent for the crunch; one telemetry sample appended (count += 1,
latency sample recorded). State change: the accessors' rolling window updates —
mean/max latency, per-surface counts. What re-arms the trigger: the NEXT stride
— locomotion re-arms it as long as velocity > 0, so the loop closes through the
player's body rather than through any system timer.

The meta-loop that feeds the studio: sleepwalker walks -> accessors accumulate
-> beat expects assert the window -> failures become graph evidence -> fixes
re-enter the build -> sleepwalker walks again. audio_visual_sync/
telemetry_accessors is the sensor in that larger closed loop.
