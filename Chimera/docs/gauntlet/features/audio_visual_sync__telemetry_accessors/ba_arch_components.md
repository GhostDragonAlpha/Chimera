# Bachelor: component decomposition — audio_visual_sync/telemetry_accessors

Classes and ownership: **USandSoundComponent** (loop-built manual, under
ProceduralGenerated/Sound/) owns footstep audio triggering AND the telemetry
surface this feature adds — counters, latency ring buffer, accessors
(GetFootstepCount, GetLastSyncLatencyMs, GetOrphanCount). It attaches to
**BP_Astronaut_Character** (the pawn), subscribing to locomotion contact
events; the character owns lifecycle, the component owns measurement. The MCP
bridge handler (Plugins/McpAutomationBridge, plugin-owned manual class code)
reads the accessors for beats — it must READ, never compute, so the number the
beat sees is the number the component measured.

Contract declarations: SandSoundComponent and its telemetry are loop-built
MANUAL files — no generator template exists, hand-edits are legal and safe.
The character blueprint attachment is config, not template. Nothing in this
feature touches generator-owned files, so no template change rides along; if
the accessors ever migrate into a generated Sound template, the generator gains
a generate_sound_telemetry method FIRST (per the migrate-under-generator rule).
