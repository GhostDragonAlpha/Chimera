# Middle: input mapping — audio_visual_sync/telemetry_accessors

Bindings that feed this feature: W/A/S/D and the left gamepad axis drive
locomotion (the stride generator); Left Shift modifies to sprint, doubling
cadence. The verb's energy match: walking is continuous and low-attention, so
it lives on held keys, not taps — the sound answers the body's rhythm rather
than a button press, which is why the sync window matters more here than in
any tap-verb.

Modifier-key trap, on the record: the sleepwalker's walk_fast_on_sand beat
already blocked once because the harness expected LShift/RShift naming for the
Shift modifier — any beat driving this feature's sprint case must use the
registered modifier names, or the telemetry will honestly report a sprint that
never happened.
