# Middle: forgiveness — audio_visual_sync/telemetry_accessors

What applies: a measurement DEBOUNCE window rather than player-facing buffer —
two footfall events within 120 ms at walk cadence are physically impossible for
this rig, so the accessors should coalesce them as one step (that is the
anti-double-fire forgiveness Astroneer needed). Landing-from-jump gets one free
heavy-step classification within a 100 ms window of ground contact rather than
counting as a stride.

What it must NOT have: any forgiveness on the sync window itself. No coyote
time for late audio — the [-45, +125] ms budget is the measurement's whole
meaning, and widening it to make builds pass is the exact corruption
audio_visual_sync/telemetry_accessors exists to prevent.
