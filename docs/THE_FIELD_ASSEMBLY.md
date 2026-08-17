# THE FIELD ASSEMBLY — one field, one law, N readers; membranes as packets that snap together

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
> **[docs/THE_LAW.md](../docs/THE_LAW.md)** · the method: `docs/THE_WORKFLOW.md` §0
> · 26 rules: `Chimera/docs/EXPERIMENTAL_METHOD.md` · gate: `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

*2026-08-10. Captured from the operator before any build, because the idea is too large to hold in
a working session: this document is the law the assembly lane will be judged against. If a later
session must rebuild this from nothing, it rebuilds from THIS file. It POINTS at the machinery that
already exists — it does not duplicate it.*

**The operator's theory, in his words.** *"A collection of sectioned-off Gaussian space… Gaussian
space interacting with Gaussian space through gravity only. To make a complex movable object we
simply create actual physical membranes that interact. We sign everything a gravity force and
direction. Everything gets applied the same rule only in a different direction and magnitude —
meaning mass and velocity and all that. We have normal gravity that pulls things to the plane, but
then all the other gravity that holds matter together. I know that's not how the real world works,
but we have to think about it computationally like that. And that's where the translation becomes:
we take what we're proving in these tests and translate it into that master algorithm for that
membrane. We may have a series of events that trigger things to happen with input — triggering
chains of events that changed these forces. We have to train the color of everything and the shape
of everything, one membrane at a time, and then we fit them all together. It's like if Legos
worked every other direction, not just pushing down."*

---

## THE THEORY (RULE 0)

**STATEMENT.** One density field, one force law, N readers. "Sectioned Gaussian space" is the
field partitioned into packets; the only interaction between packets is the field itself. Every
phenomenon — attraction to the world, the binding that holds matter together, contact, light — is
the SAME computation applied with a different direction, magnitude and coupling. An object is a
**membrane**: a held-together packet collection, trained alone and assembled with other membranes
along any interface direction (Lego in every orientation, not just gravity-down).

**PREDICTION.** (a) The binding force that holds a membrane together is derivable from the density
field already in the repo — attraction (gravity reads aggregate density) and exclusion (contact
reads local density) are two readers of one field, and together they make a stable, shape-holding
membrane with NO new force law. (b) A record groove can modulate a membrane's force couplings —
not just its colors and positions — so an input event becomes a chain of coupling changes with a
measured, physical consequence. (c) Two independently-trained membranes, assembled along an
arbitrary interface, hold together at the seam with the same density-derived cohesion their parts
already prove, at any orientation — no gravity-down stacking required.

**FALSIFIER.** Any of: (a) a membrane whose shape-holding requires a force that is not a reader of
the density field; (b) a groove-modulated coupling change whose physical consequence cannot be
measured to a pre-registered tolerance; (c) a seam between assembled membranes that leaks, floats,
or shears at any tested orientation under the density-derived cohesion. One firing stops the lane
and re-derives.

---

## THE VOCABULARY — operator terms → repo terms

| operator's word | repo term | where it lives today |
|---|---|---|
| Gaussian space, sectioned | the density field partitioned into **packets** (the Gaussian splat is the packet: a position, a mass, a size = one local density statement) | `ParticleEngine/gpu_pipeline.py`; `docs/THE_TWO_FORCES.md` |
| sections interact through gravity only | the folded Barnes-Hut walk — the tree cells ARE the sections; the only cross-section interaction is the one inverse-square rule | the walk; `docs/THE_TWO_FORCES.md` scope declaration 2 |
| same rule, different direction/magnitude | one walk + per-grain couplings (MASS, CHARGE/PROP, TYPE columns) | buffer layout, `docs/RENDER_PIPELINE_DATA_FLOW.md` |
| the gravity that holds matter together | **saturated-density contact** — matter held by a DERIVED rest-volume potential (stiffness linear in cited bulk modulus; seam closes at 1.2 nm; sound speed 1463.5 vs published 1474.78 m/s) | `docs/THE_TWO_FORCES.md` Stage 8 v2, Stage 9–15 |
| membrane | a folder in `story/` — a membrane is a folder with `derive()` and `emit()` | `README.md`, `docs/THE_WORKFLOW.md` |
| master algorithm for a membrane | the record: `derive() -> numbers.json`, `emit(nums, t) -> buffer` | `story/theZero/theLight/` |
| events triggering chains that change forces | the groove + needle: story-time t, the deck's solo dial | `story/theZero/theLight/physics.py` `emit()` / `_DECK` |
| train color + shape, one at a time | per-membrane `derive()`/`emit()`, recovered genomes, heritability per material, composition fitting | `Construction/`, `docs/THE_PIPELINE.md` §4 |
| fit them all together, Lego in every direction | the UNBUILT membrane assembly grammar (see B2) | — |

---

## WHAT IS ALREADY BUILT AND GATED (pointer-only — read these before building anything)

- **The field, the packet, the readers.** `docs/THE_TWO_FORCES.md` — density is the field, the
  Gaussian splat is its packet, light and contact are readers. 20+ stages built and judged.
- **The two readers that make a membrane hold together are BOTH DONE.** Attraction: the folded
  walk (aggregate density). Exclusion: saturated-density contact, Stage 8 v2 — the seam closes at
  1.2 nm with stiffness linear in cited bulk modulus; Stages 9–15 add sound, damping, friction,
  Hertz/Mindlin, rolling, hysteresis. **This is the operator's "the other gravity that holds
  matter together," already measured.**
- **Orientation-free contact already works.** Normals are carried per-grain; contact is
  orientation-free (Hertz normal, Mindlin tangential, Coulomb ceiling at a grown repose angle). The
  "Lego in every direction" primitive exists; only the assembly grammar is missing.
- **The record player exists.** `theLight` is a pressed record: grooves, needle, story-time. The
  deck already modulates states while the needle runs (`_DECK["solo"]`). The groove that modulates
  FORCE COUPLINGS is a small, named extension (B1).
- **Training one membrane at a time exists.** `derive()`/`emit()` per membrane; measured genomes
  and heritability; composition fitting. `docs/THE_PIPELINE.md` §4.
- **The cost wallet.** `docs/RENDER_COST_MODEL.md`, `docs/MEASURED_RENDER_BUDGETS.md`,
  `ChimeraEngine/perf_guard.py`. The currency is tile expansions, not grains; the pixel tax and
  the memory law are named walls nothing beats.

---

## THE UNBUILT LANE — falsifiers named before each build

> Build order follows dependencies: B1 (cheap) → B2 (the flagship) → B3 → B4 (the challenge).
> Each build is gated by RULE 0/1: no sweep for a number, derive it, and name the falsifier first.

### B1 — THE GROOVE THAT MODULATES THE LAW (`emit()` extension)
The record currently interpolates positions and colors along story-time t. Extend it so a groove
can modulate a membrane's **force couplings** (mass, charge, the couplings that set contact
stiffness and cohesion) — an input event becomes a chain of coupling changes.
**FALSIFIER.** A groove-driven coupling change whose physical consequence cannot be measured to a
pre-registered tolerance (e.g. stiffness change → measured sound-speed change must match the
derived `c = √(3B/2ρ₀)` relation the lane already proved).

### B2 — THE MEMBRANE ASSEMBLY GRAMMAR (Lego in every direction) — THE FLAGSHIP
Two independently-trained membranes, assembled along an arbitrary interface, must hold together at
the seam with density-derived cohesion — at any orientation, not just gravity-down.
**FALSIFIER.** The seam leaks (packets separate), floats (overlaps past the derived rest volume),
or shears (slides under a load below the derived Coulomb ceiling) at any tested interface
orientation under the density-derived cohesion alone. Named before the build: the seam test runs at
{0°, 30°, 60°, 90°} to the world gravity axis.

### B3 — THE MASTER ALGORITHM PER MEMBRANE (event chains)
A membrane's whole behaviour is one record: derive → train (color, shape, couplings) → events as
grooves → assembly. The "master algorithm" is the record itself, generalized.
**FALSIFIER.** A membrane whose behaviour cannot be expressed as a record of coupling modulations
+ assembly interfaces (i.e. needs a bespoke force not readable from the density field).

### B4 — THE CHALLENGE (the "way faster than today's tech" claim, made falsifiable)
The performance claim is scoped, not universal: this field/packet renderer beats an
Unreal-class (triangle/deferred) pipeline on **scene complexity** (independent dynamic entities,
features added at ~zero marginal cost) and loses to it on **hard thin surfaces** (hair, text,
sharp edges) — and NEITHER beats the pixel tax or the memory law.
**FALSIFIER.** A named head-to-head where this pipeline cannot hold ≥ N splats at the target fps
while adding a feature at <1% frame cost, against a published Nanite-class reference, or where it
renders a hard-surface scene within the same margin as the reference. N and the scene are written
down before the run, in `ChimeraEngine/the_matrix_stress.py` (the wallet already exists).

---

## THE SCOPE DECLARATIONS (what can and cannot lose — decide once, here)

1. **This is a computational theory, not a claim about the real world.** The operator said it
   himself: *"I know that's not how the real world works but we have to think about it
   computationally like that."* Physical unification is not claimed.
2. **The nucleus is outside the scope.** Strong and weak interactions exist and enter as measured,
   cited constants (as theStar's fusion always has) — `docs/THE_TWO_FORCES.md` §Scope 3.
3. **Attraction and exclusion are two readers of one field, not two forces.** Gravity reads
   aggregate density; contact reads local density. Any build that needs a third law is a refutation
   of the STATEMENT, not a feature.
4. **The pixel tax and the memory law are walls.** Every frame pays the fixed rasterization floor
   (~7–14 ms) and every scene pays VRAM. The theory's win is marginal cost of phenomena and scene
   complexity, never these walls.
5. **Hard thin surfaces are a named loss.** Splats smear; triangles are exact. The assembly lane
   targets matter-as-density, and does not claim the blade.

---

## THE GATE

```bash
python ChimeraEngine/test_optics.py            # the field/reader lane is still green
python ChimeraEngine/test_render_pipeline.py   # 47/47 baseline terms, bit-level
python ChimeraEngine/the_matrix_stress.py      # the wallet: the cost model still holds
python tools/training_gate.py                  # the rules gate
```

Each B-build adds its own falsifier test to this list before the build starts, and the build is
not done until its falsifier is either pinned (refuted, on the record) or closed (passed).

---

## THE HONEST END

This lane is not "everything is gravity." It is: **one density field, one force law, N readers,
membranes as packets that snap together.** What is already proven here — a membrane that holds
together from density-derived cohesion alone, contact at any orientation, a record that modulates
a membrane while the needle runs, per-membrane training — is most of the theory already standing.
The unbuilt part is the grammar that fits trained membranes together and the groove that modulates
their laws. That is the next build, and it answers to THIS file.
