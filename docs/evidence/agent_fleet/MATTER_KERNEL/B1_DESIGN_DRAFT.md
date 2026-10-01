# B1 — THE SCRATCH TEST (design draft, for operator review)

The first proof that the membrane method simulates matter. A geologist's
scratch, computed: a hard tip dragged across a softer surface — the softer
one gives, along the contact line, every time, from the constants.

## The scene

- A flat membrane plate of WOOD (sourced oak constants) lying on the ground
  plane.
- A rigid STEEL tip (hardened-steel constants), pressed onto the plate with
  a set force and dragged across in a straight line at constant speed.
- One camera, fixed. The whole interaction visible in one take.

## The law under test (KERNEL_SPEC law 4)

When two membranes press, the pairwise interaction table decides who yields
and how. For B1: HV(steel_hardened) = 640 >> HV(oak) = 4 (both cited in
constants.py). The wood yields at the contact line; the steel is unmoved.

## Three stages, honest (the repo's established method)

1. **Reference model (Python, stdlib)** — the INTENDED physics derived on
   paper first: groove geometry as a function of tip geometry, applied
   force, and the two materials' hardness and modulus. Predictions with
   numbers: groove depth grows monotonically with force; doubles when
   force doubles (linear regime); groove width set by tip contact area;
   zero deformation in the tip. Negative controls: swapping to a rubber
   tip must REFUSE to cut wood (softer than the plate); steel-on-steel
   must refuse to cut either (comparable hardness).
2. **Battery against the model** — the model's predictions vs computed
   runs, all four bars (depth monotonic, linear-in-force, tip intact,
   ordering respected). Falsifier: any bar fails, or the model contradicts
   the sourced hardness ordering.
3. **Visual proof (engine, later appliance)** — only after the model
   passes: the scratch rendered live, the wood visibly grooved, steel tip
   clean, judged blind by the dyad ("a hard thing was dragged across a
   softer thing and left a line"). The engine appliance that computes this
   on GPU-resident triangles is a NAMED exception, spec'd separately per
   the kitchen rule — this draft does not build it.

## What B1 does NOT claim

- No engine changes in this stage. No GPU residency claim (that is B5).
- The reference model is a derivation tool, not the game runtime — Python
  computes it offline; the game will not.

## Acceptance

Model battery all-green + the design's negative controls refuse correctly.
Then the operator sees the rendered scratch before B2 begins.
