# Research — anchored to tb-0002 (audio_visual_sync/report_telemetry)

The open board task tb-0002 needs telemetry that reports footstep audio-visual
sync honestly. Research writes this exam:

**Acceptance criteria (numeric):**
- Audio-visual sync tolerance: audio may LEAD the visual footfall by at most
  45 ms and LAG it by at most 125 ms (the ITU broadcast detectability window —
  the human ear forgives late audio far more than early audio). Beat expects
  should assert measured latency inside that asymmetric window, not a naive
  symmetric one.
- Measurement floor: 60 fps foregrounded during capture — the telemetry law in
  docs/RESULT_GRADING_RUBRIC.md holds that backgrounded capture freezes fps and
  Niagara/anim simulation, so any sync number measured backgrounded is a lie.
- Liveness sentinel: footstep event count must be > 0 units before any latency
  number is trusted; count=0 with latency=999 ms is the hardcoded-default lie
  documented in the constitution's H-31/H-32 family.

**Sources consulted on disk:**
- docs/RESULT_GRADING_RUBRIC.md — evidence layers and the foregrounded-telemetry rule.
- docs/MCP_PATHWAYS.md — proven read-back pathways and TRAPS for runtime queries.
- research_corpus/RESEARCH_CAMPUSES.md — campus index for the audio school.

The exam, then: a beat that walks on sand, asserts count > 0 units, then asserts
-45 ms <= (audio_time - visual_time) <= 125 ms at 60 fps foregrounded.
