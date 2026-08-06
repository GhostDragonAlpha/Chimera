# theDig

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
> **RULE 0 IS ENFORCED AT S-1 VALIDATE** — every port tested alone, and `port_test()` REFUSES to
> register a test that names no falsifier. The model it feeds: `docs/THE_COMPILER.md` — ports →
> primitives → programs → parser → runtime → calibration.
>
> **[docs/THE_LAW.md](../../../../../../../../../../../../../../../../../docs/THE_LAW.md)** · the method: `docs/THE_WORKFLOW.md` §0
> · 26 rules: `Chimera/docs/EXPERIMENTAL_METHOD.md` · gate: `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

> **chapter 39** of the story  ·  **t = 5.75715e+15 s** since theZero  ·  lasts **0.0 s**
>
> *The serial is the place in TIME, not in the folder tree. A path says what contains
> what; this says what follows what. Both are published — `timeline_serial` in
> numbers.json and here — so the story and its numbers cannot disagree about when.*

**STATEMENT:** Digging a trench in granular soil requires overcoming shear strength determined by cohesion plus density·g·depth, and the spoil mound forms at exactly the repose angle with volume expanded by a bulking factor derived from porosity change.

**PREDICTION:** The trench resistance per unit area will equal `bearing_zero_depth_Pa + bearing_depth_coeff_Pa_per_m * trench_depth_m`, and the spoil mound's base width will be exactly `2 * heap_height_m / tan(repose_deg)` where `heap_height_m = sqrt(heap_volume_per_m / tan(repose_rad))`.

**FALSIFIER:** If the measured mound slope deviates from the repose angle by more than 1 degree, or if the trench resistance does not scale linearly with depth as predicted by the bearing capacity formula, the derivation is wrong.

**In plain words —** A body opens the ground: a narrow trench cut into an earthy surface, with a mound of freshly-dug grains heaped beside the opening, and a few loose grains scattered nearby. The matter is piled at the repose angle, and the resistance comes from the granular medium's bearing capacity and cohesion.

*It is not a smaller thing than its parent. It is the same ground, now disturbed.*

## The physics of digging: shear strength and spoil geometry

WHY DIGGING IS NOT JUST MOVING DIRT. A trench must overcome the soil's **shear strength**, which in a granular medium is cohesion plus density·g·depth — the same chain theGround publishes for bearing capacity. The trench depth is chosen by the player, and the width is a dial.

THE SPOIL MOUND: when dirt is dug out, it expands (bulking) due to the change in porosity from the in-situ state to the loose heap. The heap's slope is exactly the repose angle — the law, not a choice. Scattered grains follow ballistic trajectories in the parent's gravity.

WHERE EVERY NUMBER COMES FROM:
- `bulk_density`, `porosity`, `repose_deg`, `g` from theGround's numbers.json
- `bearing_capacity_Pa`, `bearing_cohesion_Pa` from Mitchell et al. 1972 (3rd Lunar Sci. Conf.) via Chimera/docs/matter/matter_library.json sand.cohesion_kpa — READ, never typed
- `mineral_materials: quartz/feldspar/oxide each with rgb_mean` for splat colors

WHAT IS NOT SOURCED, said out loud because a guess dressed as a citation is the one defect no checker can catch:
* The bulking factor is derived from porosity change: loose_porosity / in_situ_porosity. This is a standard geotechnical approximation.
* Scattered grains are modeled as ballistic projectiles with initial velocity derived from trench excavation energy.

Contained in theGround. Its movie shows intact ground at t=0, and a trench + repose-angle mound + scattered grains at t=1.