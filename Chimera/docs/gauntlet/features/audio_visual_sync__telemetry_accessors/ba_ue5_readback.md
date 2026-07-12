# Bachelor: the read-back — audio_visual_sync/telemetry_accessors

The exact MCP read-back that proves this feature alive in PIE, per H-22 (read
back live-PIE pawn components BEFORE staging an interaction verb):

1. `control_actor` action=get_components on the possessed pawn — EXPECT
   SandSoundComponent present in the component list (attachment proof).
2. Drive ten real strides (registered move actions), then the telemetry query
   through the bridge — EXPECT GetFootstepCount >= 8 units (debounce may eat
   one or two) and GetLastSyncLatencyMs inside [-45, +125] ms, NOT 999.
3. `inspect` action=runtime_report — EXPECT the component's category present,
   confirming the accessors are wired into the report path the beats consume.

Read-back 1 without 2 is metadata; 2 without 1 is a number with no provenance.
Together they are the H-22 standard: component attached, bound, and answering
from real input — the exact chain whose absence got this feature rejected.
