
## 2026-09-04 — THE TAG LAYOUT LAWS (three rounds, each convicted by the eye)

The face-stick rework (features draw LOCAL vectors, not neck spokes) passed on
round 1, but the close-up shots earned three real layout laws:

1. **LABEL-RECT CROWDING** (run 225408): crowding judged by PIN distance
   (SPREAD=2.5*lh) let two pins ~140 px apart in x pass while their ~100 px
   inline labels superimposed into unreadable glyphs (ear_L/lid_L mid-show).
   Law: a tag is crowded if its inline label RECT intersects another tag's
   rect, or pins are close. Verified: ear_L/lid_L readable (run 230949).
2. **RESIDUAL DE-OVERLAP**: clusters form by pin gaps, so displaced tags in
   different clusters can still collide. A global sweep over ALL tags (inline
   tags are immovable — an isolated tag belongs exactly on its anchor) pushes
   overlapping label rects apart vertically, 3 iterations.
3. **PANEL SUPPRESSION** (run 230949): labels whose ANCHOR projects into a UI
   panel (strip/docks/bottom/reel/status bar) overprint that panel —
   *wrist_L/*elbow_R garbled the timeline, REEL captions ate stray strings.
   Law: those tags are suppressed. Clamping was rejected: a tag pointing at a
   lie is worse than no tag. Verified clean (run 231751).

Also: brow sticks shortened to OUTWARD ticks (+x = creature's left, so
outward = +x for brow_L) — the old +-0.50 vectors bridged mid-face as one
cross-face line (run 224349).

## THE ONE-SHOT LAW (operator directive) — tools/dyad_shot.py

No batch scans. One deliberate shot -> one eye read -> program from the
answer -> repeat. Camera angle is MANDATORY (--theta or --v); the operator's
view is bookmarked pre-shot and restored post-shot. Every shot/verdict lands
in Saved/dyad/dyad_shots/<ts>_<name>/report.json and the shared dyad log.
Measured read cost: ~11k tokens (briefing+live state ~1.8k + 2 images
~4.6k each) — compliant with the 30k context decree with headroom.
Read latency: ~190-280 s GPU-resident; **26 s** with the operator's CPU/RAM
offload split active (the CPU-picture-ops theory, confirmed).
