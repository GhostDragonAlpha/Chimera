# FAL.AI — the synthetic capture rig

> **What it is for, in one line:** this project sources APPEARANCE from measurement and cannot
> measure things that do not exist. fal.ai runs a video model that will texture our own geometry,
> which makes it a **scan rig for objects nobody can photograph** — this world's rock, a suit
> nobody has sewn, a creature nobody has caught.

---

## 1. Where it sits in the workflow

    a membrane's emit()  ->  clay_export  ->  FAL.AI (Seedance)  ->  a textured take
                                                                          |
                                     material genome  <-  harvest / splat_genome
                                                                          |
                                              back into the membrane's own numbers

`Construction/SPLAT_DNA_WORKFLOW.md` turns real 3DGS scans into material genomes. Its permanent
shortage is **scans of things that do not exist**. A video model conditioned on our clay closes
that gap without breaking the project's own rule, and the reason is worth being precise about:

**IT IS NOT ALLOWED TO INVENT THE SCENE.** We supply the geometry and the camera; it supplies
appearance only. Appearance is already the one thing this pipeline sources from measurement rather
than derivation, so nothing is being conceded. And it is CHECKABLE — reconstruct from the generated
views and compare against the membrane's own emit. That is the dyad: our geometry and its
reconstruction, two independent messengers.

---

## 2. What it can and cannot give us — MEASURED, not assumed

**CAN.** Colour, and it is a strong signal. R/G/B deltas against the clay control run
**−0.22 to −0.25** on a suit and **−0.45 to −0.51** on terrain. Also `surface_complexity` (fitting
cost at equal splats per subject pixel, 1.71× flat clay) and `splat_demand` (primitives the surface
asks for, 1.398×).

**CANNOT.** Geometry — the visual hull scored 0.45 IoU against the membrane's own emit, and the
generated body came back 25% less voluminous. **This does not matter**, and that is the point a
successor must not re-litigate: *a material genome contains no positions.* Every feature is a
distribution. We already have the geometry — the membranes derive it, that is the whole project.

**ALSO CANNOT: per-splat shape.** `log_size`, `aniso`, `opacity` fitted from a generated take match
**the clay we sent it** to within 6–7%, so they are the FITTER's signature, not the material's.
Adaptive densification was built and did not rescue them. Recorded REFUTED — do not re-attempt
without a real multi-view 3DGS scan.

---

## 3. Money, and the rules that exist because it was wasted

    tier   endpoint                                              480p      720p
    mini   bytedance/seedance-2.0/mini/reference-to-video       0.0721    0.1547   $/s
    fast   bytedance/seedance-2.0/fast/reference-to-video       0.2419    0.2419
    pro    bytedance/seedance-2.0/reference-to-video            0.3024    0.3024

    cost = rate x seconds x VIDEO_INPUT_MULTIPLIER (0.6)

- **NOTHING IS SPENT WITHOUT `--yes`.** The estimate prints first, every time.
- **DISCOVER FOR FREE BEFORE YOU SPEND.** `https://fal.ai/api/models?keywords=seedance` lists what
  exists; `https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=<id>` gives the exact input
  schema. Both are free. Seven paid calls were burned probing an endpoint with **invented field
  names** before anyone looked these up.
- **FAL IGNORES UNKNOWN FIELDS RATHER THAN REJECTING THEM.** A request with a misspelled or
  imaginary parameter returns 200 and a charge. Your schema guess is never validated for you.
- **A 422 IS NOT PROOF AN ENDPOINT IS LIVE.** One validated inputs and then returned a canned
  example for any prompt — `example_outputs/.../output.mp4`, seed 0, 0.6 s. Check the returned
  seed and duration against what you asked for before believing a take is yours.
- `FAL_KEY` in the environment. Never in a file, never in a commit.

---

## 4. Capture settings — every one measured against a control

- **480p BEATS 720p** for frame-to-frame consistency: 2.62% vs 4.30% drift against a clay control
  of 2.51%. More resolution bought less agreement. Do not assume up is better.
- **BLACK FLOOR, AMBIENT ONLY, NO SHADOWS.** The operator's call and it is load-bearing: our
  renderer programs its own lighting, so the sample must arrive lit flatly or the light is baked
  into the genome forever. A black floor also makes the subject mask exact.
- **KEEP THE CONTACT VISIBLE.** Where the object meets the floor is information — the prompt asks
  for a black matte floor that reflects no light, not for the floor's removal.
- **THE PROMPT NAMES `@Video1` AS THE GEOMETRY.** That is the only channel the 2.0 endpoints give
  us for structure. A "plain uncluttered backdrop" clause protects the segmentation everything
  downstream depends on.

---

## 5. The rule that governs all of it

**THE CLAY IS THE CONTROL, AND IT IS FREE.** We rendered it, so we know its answer by construction.
Run every measurement on the generated take AND on the clay we sent, through the same instrument.
Three conclusions were reversed by this in one day — a material genome that was the fitter's
signature, a detail gain that was render grain, and a cross-hatch blamed on new code that came from
the canvas. See rules 11–16 of `Chimera/docs/EXPERIMENTAL_METHOD.md`.

    A measurement without a control is not a weak measurement. It is not a measurement.

---

## 6. Files

| file | what it does |
|---|---|
| `tools/clay_export.py` | membrane → white-model blockout + `cameras.json` |
| `tools/seedance_probe.py` | the fal.ai runner. Costs printed, `--yes` to spend |
| `tools/harvest_material.py` | colour half of a genome, clustered on CHROMATICITY not RGB |
| `tools/splat_genome.py` | GPU splat fit; surface_complexity + splat_demand, with the clay control |
| `tools/visual_hull.py` | 3D geometry check from many silhouettes, with a control membrane |
| `tools/clay_check.py` | perturbation sweep against a measured appearance floor |
