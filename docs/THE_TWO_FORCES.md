# THE TWO FORCES — density is the field, the splat is its packet, light is the third reader

*2026-08-05. The operator's theory, made falsifiable and then built:* "computational optimization
by using only the forces of nature, mainly electromagnetism and gravity — if we just calculated
those two forces, then all the other forces would make themselves apparent… if you put in the
concept of density then you can do it."

Status: **v1 BUILT AND MEASURED** (specular reflection; gates green 2026-08-05). Everything in
Part II is UNBUILT and says so.

---

## THE THEORY (RULE 0)

**STATEMENT.** Above the nucleus, every force in this world is gravity or electromagnetism,
mediated by density. The Gaussian splat is the computational packet of the density field — a
position, a mass, a size are a complete local density statement — and light is not a physics
system of its own: it is a third **reader** of the same field. Refraction comes from density
through Lorentz-Lorenz (`(n²−1)/(n²+2) = r·ρ`, pure electromagnetism: bound electron clouds
polarising, summed over number density); reflection amplitude from `n` through Fresnel;
transmission through opacity by Beer-Lambert — which the compositor already computes
(`trans *= (1−al)`, `ParticleEngine/gpu_pipeline.py`). Adding a phenomenon to this world should
cost one more reader of one field, never a new force system.

**PREDICTION** (made before the build; all landed — §Measured below). A specular pass whose every
number is read from published membrane data — density → F₀, published slope statistic → lobe
width, zero picked constants — will (a) match an independent float64 referee within pre-registered
tolerances on two membranes it was never fitted to, (b) leave every existing render bit-identical
(no light set → no term), and (c) add frame cost below the existing budget's noise floor.

**FALSIFIER.** Any of: referee disagreement beyond `EPS_KERNEL_MAX = 1e-3` (that is a wrong
formula, not a tuning opportunity — stop and re-derive); any of the 47 baseline terms moving by
one bit with no light set; a picked constant anywhere in the chain (RULE 1 violation, stops the
stage); the closure slider failing (move density → n, F₀, and the glint must all move; whatever
does not move is typed). **The literal "only two forces" claim is already refuted at the
nucleus** — the strong and weak interactions exist, bind nuclei, and drive beta decay, and are not
derivable from EM + gravity. They enter this world the way theStar already treats fusion: as
measured, cited inputs. The theory is scoped, and the scope is the next section.

## THE THREE SCOPE DECLARATIONS (decided by the operator, 2026-08-05)

1. **Light v1 = specular reflection only.** Transmission was already proven code (the
   compositor's Beer-Lambert walk); diffuse already exists (`story/matter.py:lit()`). Refraction,
   caustics, interreflection, dispersion: Part II, unbuilt, falsifiers pre-written.
2. **Gravity reads aggregate density; light and contact read local density.** Gravity's reader is
   the membrane tree (analytic wells; the parent carries `g` and the child consumes it —
   aSaltOcean and aBlueWorld publish the same 7.076122… and the closure test checks it). It was
   NOT re-plumbed onto the grain buffer: physically defensible (gravity's source is aggregate
   mass) and stated here so "one field, three readers" cannot drift into a lie. The granularities
   are different; the field is the same quantity.
3. **Two forces above the nucleus.** Nuclear physics enters as measured constants, exactly as
   theStar's fusion chain (Bethe) always has.

## WHAT WAS BUILT (v1)

| piece | where | what it is |
|---|---|---|
| density declared once | `story/matter.py` — `MASS` col, `grain_mass`/`grain_density`, `SPECIFIC_REFRACTION_CM3_G`, `refractive_index`, `fresnel_f0`, `paint_specular`, `SPEC_F0`/`SPEC_SLOPE` cols | the ρ → n → F₀ chain, one source; specific refractions are cited measured constants (water CRC 3.712 cm³/mol / 18.015 g/mol; silicate = quartz's measured n at its measured ρ restated through the law) |
| the specular term | `ParticleEngine/gpu_pipeline.py` — `_smith_g1`, the block in `_p2s`, `set_light()` | per-GRAIN Cook-Torrance: one grain = one facet = one light slot. Beckmann D (a Gaussian slope distribution — exactly what Cox-Munk measured on a real sea), Schlick F on the membrane's derived F₀, EXACT Smith-Beckmann G via `erfc` (no fitted rational anywhere). Runs ONLY under an explicitly set light; zero in either column disables the grain (absence refuses, never defaults) |
| the referee | `ChimeraEngine/core/optics.py` | the same declared model, independent float64 implementation, with the pre-registered tolerances (`EPS_*`) written before the first comparison ran. The renderer was Lambertian-only and could not judge specular — the referee had to be BUILT |
| the falsifier gate | `ChimeraEngine/test_optics.py` (31 checks) | closure, one-source (ast), kernel-vs-referee on both membranes, clay controls, slider, PNG artifacts |
| the cost record | `ChimeraEngine/benchmark_optics.py`, `perf_guard.MS_PER_LIT_GRAIN_MAX` | interleaved A/B with the decision rule pre-stated in the docstring |

**Why per-grain and not per-pixel:** colour is per-grain in this renderer (`_p2s` bakes it, the
compositor blends it), so the glint resolves at grain granularity, the compositor is untouched,
its measured cost model (`docs/RENDER_COST_MODEL.md`) keeps holding, and the pass is idempotent
because `_p2s` re-derives splat colour from the buffer every frame. The grain's normal carries the
RESOLVED geometry; the published slope statistic carries the UNRESOLVED sub-grain geometry. No
double count, and no aesthetic pass anywhere: the lobe width is the sea's own measured slope.

## MEASURED (2026-08-05, all against pre-registered gates)

- **Density alone lands on numbers it was never fitted to.** Pure water: n = 1.3336 (literature
  1.333). Seawater at aSaltOcean's published 1026.95 kg/m³: n = 1.3436 against the membrane's own
  independently-sourced 1.34 (0.27%); F₀ = 0.02149 against its published `sunglint_intensity`
  0.02111 (1.8%, gate 5%). Regolith at theGround's published 1537 kg/m³: F₀ = 0.0165 < solid
  quartz 0.0462 — **porosity lowers reflectance by the law itself** (refractivity is additive in
  mass; air adds nothing), no porosity rule written.
- **Kernel vs referee:** max |diff| 4.78e-07 (water), 1.82e-08 (ground) against gate 1e-3 —
  float32 GPU and float64 CPU agree to ~7 significant figures on two membranes' real numbers.
- **The clay controls are silent.** Zeroed specular columns under a light, and populated columns
  under no light: grain colours AND frames bit-identical. The full 47-term baseline suite passes
  untouched (47/47), because no existing caller sets a light.
- **The glint is physical.** Water (σ = 0.1233, the membrane's Cox-Munk number): 272 grains lit,
  peak 0.125 — a tight bright patch where the half-vector says it must sit. Ground (σ = 0.3534
  from aTerrain's mean_slope_deg): 836 grains, peak 0.012 — wider and dimmer. Rougher glints
  wider and dimmer with no one deciding it. Frames: `agent_logs/optics_{water,ground}_{on,off}.png`.
- **The cost is a measured null.** Interleaved A/B, worst case (every grain lit), N up to 262,144:
  Δ = −0.0020 ± 0.0118 ms — statistically zero. Recorded as the 2σ upper bound
  `MS_PER_LIT_GRAIN_MAX = 9.0e-08 ms/grain`: even at the bound, a 200 ms frame admits ≥ 2.2
  billion lit grains, so `MAX_EXPANSIONS_PER_FRAME` fires first in every reachable scene, and
  **no light-slot check was added** — a wall nothing can reach without already being over the
  expansion wall is decorative, perf_guard's own named failure. The pre-stated rule in
  `benchmark_optics.py` promotes the bound to a fitted slope + inversion if a future change (a
  per-PIXEL specular, say) makes the term measurable.
- **The slider closes.** ρ ± 10% moves n and F₀ strictly monotonically in both materials, and the
  ocean consumes the parent's g exactly. Move the density and every consequence moves.

## THE GATE

```bash
python ChimeraEngine/test_optics.py        # 31 checks: closure, one-source, referee, controls, slider
python ChimeraEngine/test_render_pipeline.py   # 47/47 baseline terms, bit-level
python ChimeraEngine/test_perf_guard.py    # 11 checks
python ChimeraEngine/benchmark_optics.py   # the cost A/B (prints the decision rule's verdict)
```

## WHAT THIS BUYS, STATED HONESTLY

"High frame rate AND exquisite detail" is not dissolved by this theory — detail is still paid for
in tile expansions, and the budget machinery in `docs/RENDER_COST_MODEL.md` is still the wallet.
What the theory changes is the **marginal cost of a phenomenon**: specular reflection arrived as
one more reader of numbers the membranes already published — no new force system, no new per-pixel
pass, a measured-zero frame cost — and refraction, caustics and contact are scoped to arrive the
same way. That is the operator's claim made precise: calculate the two forces (here: the EM
response of matter, as density); the other behaviours make themselves apparent as READERS, not as
new machinery.

---

# PART II — NAMED UNBUILT, falsifiers written before any build

Dependency order: Stage 4 → {5, 7}; Stage 6 needs the slot budget machinery only if its cost is
measurable (see the benchmark's rule); Stage 8 is independent of the light chain. **None of this
is specified-as-proof: nothing below exists.**

### Stage 4 — Refraction: screen-space lensing
STATEMENT: light bends at density gradients; the bend is computable in screen space from
`(n−1)·∇ρ` alone. PREDICTION: a lensing pass reading only `n(ρ)` matches a brute-force ray-march
through the same grain density field within a pre-registered ε on a water membrane, and its cost
fits the frame-cost model. FALSIFIER: the ε miss (expected first at multi-interface paths — that
boundary is the scope); cost fit R² < 0.9 kills it independently. The ray-march referee must be
built first; the clay control is a uniform-density membrane on which the pass must be the identity.

### Stage 5 — Caustics (consumes Stage 4)
STATEMENT: a caustic is the convergence of the same lensing field — flux concentrates as
`1/|det J|` of the bend field, never a new phenomenon. PREDICTION: the bright-band position on a
curved water surface matches the ray-marched reference within ε_position. FALSIFIER: energy
non-conservation (a caustic is redistribution, never creation), or the band position miss. Cannot
begin before Stage 4 passes — it has no field of its own to read.

### Stage 6 — Splat-to-splat interreflection
STATEMENT: one-bounce indirect light is a gather where each surface's outgoing lobe becomes
another's incident light; Gaussians close under that convolution, so the bounce stays analytic.
PREDICTION: a budget-capped one-bounce gather matches a brute-force two-pass reference within ε on
a two-plane membrane, at cost LINEAR in slots (the naive version is O(expansions²); the prediction
is precisely that the budgeted cut removes the quadratic term). FALSIFIER: the quadratic showing
through, or the ε miss. Conservation: with albedo → 0 the bounce vanishes bit-for-bit.

### Stage 7 — Dispersion (consumes Stage 4)
STATEMENT: `n` depends on wavelength (Cauchy/Sellmeier); dispersion is the lensing pass per colour
channel with `n_R, n_G, n_B` from the material's sourced dispersion coefficients — never picked.
PREDICTION: RGB separation at a prism-like density edge matches the per-channel ray-march within
ε, at 3× the lensing cost — a derived multiplier. FALSIFIER: separation wrong beyond ε, or
measured cost ≠ 3× within the documented noise floor (extra hidden work).

### Stage 8 — EM overlap-pressure: contact from Gaussian overlap (independent)
STATEMENT: short-range contact/pressure is the overlap integral of neighbouring density packets —
Gaussian × Gaussian is Gaussian, so pressure is closed-form and there is no contact solver to
write. PREDICTION: overlap-derived ground reaction on a standing body reproduces the proven
contact seam (terrain_witness's 0.000 mm gap; MuJoCo's contact list as truth) within a stated
tolerance, from density alone. FALSIFIER: disagreement with the proven seam — or a picked
stiffness constant anywhere, which is a RULE 1 violation and stops the stage on the spot. This is
the emergence claim's sharpest test: it is where "the other forces make themselves apparent" is
proven or refuted.
