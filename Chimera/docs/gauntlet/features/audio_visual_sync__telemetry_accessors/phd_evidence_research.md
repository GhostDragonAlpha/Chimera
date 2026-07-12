# PhD: the exam — audio_visual_sync/telemetry_accessors

Numeric acceptance criteria, each with its citation:

1. **Per-step sync offset within [-45 ms, +125 ms]** — the ITU-R BT.1359
   detectability window (audio lead 45 ms / lag 125 ms), consulted live and
   cached: https://en.wikipedia.org/wiki/Audio-to-video_synchronization ->
   research_corpus/audio_video_sync_thresholds.md. The window is asymmetric
   because perception forgives late audio 2-3x more than early.
2. **Liveness before latency: footstep_count >= 8 units after 8 s of walking**
   (walk cadence ~1.6 steps/s minus debounce) — grounded in the constitution's
   H-31/H-32 family as indexed in docs/MCP_PATHWAYS.md pathways and the
   evidence rules of docs/RESULT_GRADING_RUBRIC.md: no latency number is
   admissible while the count sits at its initializer.
3. **Measured at the 60 fps floor, foregrounded** — docs/RESULT_GRADING_RUBRIC.md's
   telemetry law; a backgrounded soak freezes simulation and certifies nothing.

The exam is the beat in ba_verify_beats.md asserting all three; the feature
passes when those numbers pass, and not one commit earlier.
