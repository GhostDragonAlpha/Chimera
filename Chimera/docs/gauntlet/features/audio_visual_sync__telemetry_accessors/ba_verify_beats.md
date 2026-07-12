# Bachelor: the beat skeleton — audio_visual_sync/telemetry_accessors

Actions: only Sleepwalker-REGISTERED verbs (H-17 — beats declaring unregistered
actions fail at dispatch): reset_position, move (W hold, duration-based), the
registered sprint modifier by its registered LShift name, and the telemetry
query action the bridge exposes.

Beat skeleton:
1. reset_position (H-25 — W-drift accumulates across sequential beats and
   BugItGo is refused during PIE; every position-expect beat starts clean).
2. Read accessors — expect NO-SAMPLE sentinels (zero-state edge, count 0).
3. move forward 8 s at walk — expect footstep_count >= 8 units (schema-bound
   expect on a real accessor, H-30: unknown expects fail beats at runtime).
4. Expect last-sync-latency within -45..+125 ms and NOT the 999 default.
5. Sprint 4 s with the registered modifier — expect count delta >= 12 and the
   window still held at doubled cadence.
Every expect names an accessor the bridge actually serves — the expect
vocabulary is validated at dispatch, not discovered mid-run.
