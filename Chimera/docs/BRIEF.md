# DYAD BRIEF

<!-- CHIMERA-LAW -->
> **RULE 0 — EVERY MEMBRANE IS A THEORY. STATE IT BEFORE YOU BUILD IT.** Three parts, all three
> required: a **STATEMENT** someone could disagree with · a **PREDICTION** you have not measured
> yet · a **FALSIFIER** named *before* the run. **A description survives any result; a theory can
> lose.** No falsifier, no build.
>
> **RULE 1 — DERIVE IT BEFORE YOU TRAIN IT.** A parameter sweep is an admission the derivation was
> not done. Before any run, any sweep, any "let's try N variants": trace the variables and show the
> equations close. If you are choosing a number, you broke the chain and substituted taste for a
> law. Ask what QUESTION each variant answers — if the answer is "which number is best", STOP.
>
> **[docs/THE_LAW.md](../../docs/THE_LAW.md)** · the method: `docs/THE_WORKFLOW.md` §0
> · 25 rules: `Chimera/docs/EXPERIMENTAL_METHOD.md` · gate: `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

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

