> **DEPRECATED** — This document describes the old approach.
> Read `AGENT_ONBOARDING.md`, `DECISION_METHOD.md`, and `EMERGENT_WORKFLOW.md` instead.
> The thought chain is at `docs/THOUGHT_CHAIN.md`.

# DYAD BRIEF

Two-agent conversation system active.
### RESULT 2026-07-19 10:19:10 UTC
**Outcome:** Ran fractal_zoom_sweep.py (tests/ version). No WinError 2 occurred — the test runs cleanly through all zoom levels. However, performance fails at close range (5m/1m): 540ms render time vs 16.6ms budget. At 50km, LOD reduces to 1 splat visible (over-aggressive merge). No resolve_assets() function exists in bake.py — the dyad's function reference was hallucinated. The actual code has no relative/temp path issues; Path(__file__).resolve() is already used throughout.
**Evidence:** tests/fractal_zoom_sweep.py ran end-to-end. Grown 614,813 splats. 7 zoom levels measured. LOD merge at 10m+ reduces splats. 5m/1m levels hit 540ms without LOD reduction due to full splat count.
---

### TURN 2026-07-19 10:29:55 UTC
**Dyad instruction:** Replace the world-distance-only LOD logic with a screen-space density cap in `splat_gpu.py`'s render pipeline and fix the far-range merge threshold in `splat_lod.py`. Specifically: (1) In `splat_gpu.py`, before issuing draw calls, enforce `max_visible = int(res_w * res_h * 1.5)` by sorting splats by depth/opacity and truncating the batch; this solves the 540ms close-range bottleneck where frustum 
**FAST reasoning:** 2.  **Identify Core Problem:**
   - The critical bottleneck is performance at close range: 540ms render time vs 16.6ms budget when splat count is high (~614k initially, though LOD reduces at distance)
**DEEP scrutiny:** 2.  **Deconstruct FAST's Approach:**
   - *Assumption 1:* The bottleneck is purely in `splat_gpu.py` render pipeline or `splat_lod.py` distance thresholds.
   - *Assumption 2:* Adaptive LOD + GPU inst
---

