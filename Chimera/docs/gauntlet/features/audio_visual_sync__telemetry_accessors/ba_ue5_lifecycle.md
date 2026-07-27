# Bachelor: UE lifecycle — audio_visual_sync/telemetry_accessors

BeginPlay: the component registers its contact-event subscription and zeroes
counters with NO-SAMPLE sentinels (not fake numbers). Attachment must be
complete before the pawn's first footfall — H-31 names this exact disease:
telemetry falling back to hardcoded defaults means the component is not
attached or not populating at BeginPlay, and the fix is attachment/init order,
not the action handler.

Tick: NOTHING ticks. The feature is event-driven end to end — footfall events
and audio-start callbacks write samples; accessors read on demand from the MCP
bridge. A ticking version would burn budget measuring silence and invite
frame-rate coupling into the very instrument that measures frame-rate effects.

Possession/respawn: counters survive possession changes within a session
(the sleepwalker respawns pawns); a reset-on-possess would fake the zero-state
edge every beat. Explicit ClearFootstepSyncTelemetry exists for beats that WANT
a clean slate — reset is a verb, never a side effect.
