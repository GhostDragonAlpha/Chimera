# High: cost and pay — audio_visual_sync/telemetry_accessors

Cost to the player: effectively zero attention (that is the point) and a real
but tiny runtime budget — target under 0.05 ms per footstep event for the
sampling path, no allocation per sample (ring buffer), so the instrument never
degrades the thing it measures. Cost to the studio: one component's
initialization discipline and the beat-time to read it.

What it PAYS: every desync caught before a human hears it. The exchange rate,
concretely: one nightly sleepwalk (minutes of machine time) buys continuous
proof of the [-45, +125] ms promise across every surface — protection the ear-
based alternative pays for in reviewer trust after shipping. An unmeasured
promise costs nothing until it costs everything; audio_visual_sync/
telemetry_accessors converts that debt into a number the graph can hold.
