# Cached source: Audio-to-video synchronization thresholds
Source URL: https://en.wikipedia.org/wiki/Audio-to-video_synchronization
Retrieved: 2026-07-12 by fable-5 (gauntlet/curriculum run, feature
audio_visual_sync/telemetry_accessors). Cached per the retrieval-leaves-
evidence rule (url_cache verifier).

## Extracted numbers

- **ITU-R BT.1359-1 detectability threshold:** 45 ms audio lead to 125 ms
  audio lag — the window inside which humans do not detect desync. This is the
  primary basis for Chimera's footstep sync budget of [-45 ms, +125 ms].
- **ATSC (television) recommendation:** audio leads by no more than 15 ms,
  lags by no more than 45 ms — a stricter broadcast operating window inside
  the detectability bounds.
- **Film lip-sync:** at most 22 ms in either direction (±22 ms symmetric).
- **EBU R37 end-to-end tolerance:** +40 ms / -60 ms (audio before/after
  video), with per-stage budgets of +5 ms / -15 ms.

## Perceptual asymmetry (the design-relevant fact)

Every standard tolerates LATE audio 2-3x more than EARLY audio — sound
arriving before its visible cause breaks causality in a way the brain refuses,
while modest lag reads as distance. Consequence for footsteps: the sync window
must be asymmetric, and any "centering" of it (symmetric ±85 ms, say) would
pass audio-leads that players physically cannot un-notice.
