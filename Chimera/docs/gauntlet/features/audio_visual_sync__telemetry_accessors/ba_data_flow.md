# Bachelor: data flow — audio_visual_sync/telemetry_accessors

In: tuning parameters (sync window bounds, debounce ms, sample window size)
belong in the DSL spec's technical block as the source of truth, surfaced as
EditAnywhere UPROPERTYs on USandSoundComponent so a designer can tune in-editor
while the spec remains canonical. Runtime in: footfall contact events
(locomotion), audio-start callbacks (the sound system).

Out: the accessor surface (counts, latency samples, orphan count) consumed by
the MCP bridge for beats and by telemetry_probe for soak evidence.

Save game: NOTHING. Every value here is derived-at-runtime measurement of the
current session — persisting a latency histogram into DeepSpaceTraderSaveGame
would fossilize one machine's frame timing as if it were world state. The save
surface for this feature is deliberately empty, and that emptiness is a design
decision worth this paragraph.
