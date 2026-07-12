# Bachelor: online research — audio_visual_sync/telemetry_accessors

Consulted live: https://en.wikipedia.org/wiki/Audio-to-video_synchronization —
the consolidated sync-threshold reference (ITU-R BT.1359, ATSC, EBU R37, film
practice). Cached copy on disk: research_corpus/audio_video_sync_thresholds.md
(retrieval leaves evidence).

The ONE number that changes how this feature is built: **45 ms** — the ITU
detectability limit for audio LEADING video. It is less than three frames at
60 fps and under 1.5 frames at 30 fps, which means a single mistimed frame
plus audio-buffer quantization can cross it. Consequence: the accessors must
timestamp the audio START (not the request), the sync window must stay
asymmetric ([-45 ms, +125 ms]), and measurement must run at the fps floor —
a symmetric or averaged window would certify desyncs the standard says humans
detect.
