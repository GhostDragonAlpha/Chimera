# THE TWO FORCES — density is the field, the splat is its packet, light is the third reader

*2026-08-05. The operator's theory, made falsifiable and then built:* "computational optimization
by using only the forces of nature, mainly electromagnetism and gravity — if we just calculated
those two forces, then all the other forces would make themselves apparent… if you put in the
concept of density then you can do it."

Status: **ALL PARTS BUILT AND JUDGED, INCLUDING THE SUCCESSOR** (2026-08-05, one day, three
passes). Part I (specular) and Part II Stages 4/5/6/7 passed their pre-registered falsifiers.
Stage 8's first model **fired its own falsifier** (cross-term overlap: 3.2 mm settlement vs the
witnessed 0.000 mm seam) — and the named successor, saturated-density contact, was then built and
**closed the seam at 1.2 nm** with stiffness linear in the cited bulk modulus. A theory that can
lose, losing exactly once on the record and being repaired by its own diagnosis, is the method
working end to end.

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

# PART II — ALL BUILT AND JUDGED 2026-08-05 (one stage refuted, and that is a result)

Every stage below was built referee-first against the falsifier written here before the build.
Four passed. One — Stage 8 — **fired its own falsifier**, and the refutation is pinned to numbers
in a test that will go red if anyone changes the model without updating the record. Two
INSTRUMENT defects were also caught and corrected by the runs themselves (a dispersion gate
thresholded on the grid cell instead of float noise; a bounce cap whose guarantee compared bound
to bound) — both are documented in the tests that refuted them.

### Stage 4 — Refraction — **BUILT, PASSED**
STATEMENT: light bends at density gradients; a refractive grain is an interface — Snell at its
density-derived `n`, straight to the membrane-published floor plane, floor colour attenuated by
the membrane's own absorption, weighted by the transmitted Fresnel fraction `(1 − F(cos_v))`.
MEASURED: kernel vs float64 referee max |diff| **3.8e-08** (gate 1e-3) with 1586 of 2304 surface
grains transmitting; the clay control (η = 1 ⇒ uniform density ⇒ no interface) is the straight-line
identity to **8.9e-16**; no `set_refraction()` ⇒ bit-identical frames; cost is another measured
null (**Δ = −0.005 ± 0.019 ms at 262k worst-case grains** ⇒ ≤ 1.4e-07 ms/grain, not the binding
constraint). The refracted direction `η·d + (ηc₁−c₂)·n̂` is exactly unit length, so the plane
parameter IS the Beer–Lambert path — no normalisation anywhere. SCOPE (unchanged): one interface,
a plane floor; multi-interface paths and curved floors are named unbuilt territory.
Frames: `agent_logs/optics_refraction_{off,on}.png` — the checker seen through water shifts
blue-green because the membrane's published absorption kills red 22× faster than blue.

### Stage 5 — Caustics — **BUILT, PASSED** (consumes Stage 4)
STATEMENT: a caustic is the convergence of the same lensing field. Deposition of refracted light
rays onto the floor grid — nothing in the code knows what a band is. MEASURED: energy conserved
**exactly** (24,000 deposited = 24,000 summed; redistribution, never creation); the deposited
band pair sits at **0.0725/0.1775** against the analytic det-J zeros at **0.0705/0.1795** —
error 0.002, gate 0.010 (2 cells). The focusing depth was DERIVED (g = 2 exactly), not chosen.

### Stage 6 — Interreflection — **BUILT, PASSED — and the first cap construction was REFUTED**
STATEMENT: one diffuse bounce is a gather with a derived budget. THE REFUTATION THE RUN EARNED:
the original cap compared the tail BOUND to the prefix BOUND (cosines ≤ 1), and grazing receivers
dropped 1.46% of their ACTUAL energy against a 1.1% gate. Replaced by the a-posteriori rule —
stop when `tail_bound ≤ frac · actual_kept` — which bounds the true error by `frac` **provably**.
MEASURED: max rel error **4.4e-03** (gate 1.1e-2); albedo → 0 vanishes **bit-for-bit**; 1/r²
falloff alive (near 0.229 vs far 0.059); cost LINEAR in N at fixed sources, **R² = 0.9999**
(gate 0.9). HONEST LIMIT, said out loud by the instrument: a near-uniform bright wall is the
cap's hardest scene — it keeps 99% of pairs there, and reports it rather than lying. SCOPE:
diffuse receive only; specular-to-specular chains remain unbuilt.

### Stage 7 — Dispersion — **BUILT, PASSED** (consumes Stage 4)
STATEMENT: dispersion is the same lensing pass with three measured indices
(`story/matter.py:WATER_N_BY_CHANNEL`, Fraunhofer C/D/F lines, restated through Lorentz-Lorenz so
the density slider still moves all three). MEASURED: η_R > η_G > η_B as the literature orders
them; kernel vs per-channel referee max |diff| **3.3e-08**; R and B rays land **0.0059** scene
units apart — the exact magnitude water's Δn ≈ 0.006 commands at this geometry. THE INSTRUMENT
REFUTATION: the first gate demanded separation exceed one floor CELL and failed on correct
physics — a threshold from the container, not the phenomenon; replaced by the float-noise gate
(10× EPS_HIT), with the cell ratio reported as the fringe-visibility statement.
Frame: `agent_logs/optics_dispersion_on.png`.

### Stage 8 — Overlap-pressure contact — **MACHINERY BUILT · MODEL v1 REFUTED, ON PURPOSE**
STATEMENT: contact is the overlap integral of density packets; the energy scale comes from the
material's cited bulk modulus (`story/matter.py:BULK_MODULUS_PA`) — **no picked stiffness
anywhere**, which is exactly why the model could lose. THE MACHINERY PASSED: closed-form overlap
= brute-force 3D integral to **4e-15** (Gaussians close, proven not assumed); the force is
−dU/dd to **5e-11** (conservative); repulsive and monotone. THE PHYSICS FIRED THE FALSIFIER:
under theHuman's published 668.7 N spread over a footprint of grain pairs, the settlement is
**3.2 mm per pair** against the witnessed 0.000 mm seam; one grain carrying the whole body rests
at **7.2σ** separation (the render's own cutoff is 3.7σ); and 10× the bulk modulus moves the
equilibrium by only 6.3% — inside the model's own first-order bound ln(10)/(2·ln(F_peak/W)) =
7.3% — because **the stiffness lives in the Gaussian tail's shape, not in B**. VERDICT: the
cross-term overlap model is exponentially soft; a real density edge is sharper than its rendering
Gaussian. The named successor (NOT built): a saturated-density / volume-exclusion energy, which
becomes valid exactly where this one leaves (d ≲ 2.4σ, where summed density reaches ρ₀).
`ChimeraEngine/test_overlap.py` pins the refutation: if the model changes and the seam closes,
the refutation checks go red and force this record to be updated. Both directions honest.

### Stage 8 v2 — Saturated-density contact — **BUILT, PASSED: THE SEAM CLOSES** (2026-08-05)
THE SUCCESSOR, built where the refutation said stiffness must live. Matter saturates at its rest
density: a packet of mass m occupies the sphere of its own mass at ρ₀ — **R = (3m/4πρ₀)^⅓ =
1.5550σ for a Gaussian packet, derived, no free parameter**. The Gaussian is the packet's
APPEARANCE; its matter is the rest volume (the v1 diagnosis, taken literally). Contact is the
lens where two rest volumes intersect, double-occupied at strain 1: `U = (B/2)·V_lens(d)`,
`F = (πB/8)(4R²−d²)` for equal packets — stiffness `k = πBR/2`, **linear in B**.
MEASURED, all against pre-registered gates: closed-form lens = 1D-quadrature referee to
**1e-11–1e-9** (equal AND unequal spheres); force conservative to **2.5e-10**; onset exact and
continuous (F(2R) = 0 identically). **THE SEAM:** settlement under theHuman's published 668.7 N
is **1.2 nm per pair** (v1: 3.2 mm — six orders of magnitude); even the whole body on ONE pair
penetrates **0.37 µm**. The witnessed 0.000 mm seam, reproduced from density + cited B alone.
**THE PATHOLOGY INVERTED:** 10× B → exactly h/10 (v1 moved 6.3% for the same 10×). DECLARED
SCOPE: DEM-style linear overlap contact (uniform unit strain in the lens); Hertzian half-space
redistribution (F ∝ h^1.5) is a named unbuilt refinement. v1's tails carry no contact force —
superseded, not summed. Both records stand in one test file; the supersession check
(`v1 3.2 mm > 1 mm > v2 1.2 nm`) goes red if either model drifts from its verdict.

### Stage 9 — The seam: contact carries a body, and carries sound — **BUILT, PASSED**
The integration Stage 8 v2 earned. If contact really is the overlap of density packets, the same
stiffness must do a contact law's two other jobs — and both are checked against numbers published
by other membranes for other reasons.

**TWO DERIVED IDENTITIES, no chosen constant.** At first touch the lens force's slope is
`k = πBR/2 = B·(πR²)/(2R)` — **exactly the rod stiffness E·A/L of the sphere's own great circle
across the centre spacing**; nobody arranged that, it falls out of the lens volume. And a line of
touching spheres fills exactly **2/3** of its bounding cylinder, so the chain has a rod's
stiffness with two thirds of a rod's mass and must run `√(3/2) = 1.2247×` faster:
`c_chain = √(3B/2ρ₀)`, carrying **no R** — the wave speed of a packet chain is independent of
packet size, which is what makes it a statement about the material rather than the grid.

**THE FLAGSHIP PREDICTION — a number never fitted to.** `aSaltOcean` publishes
`sound_speed_water_ms = 1474.78`, derived from an oceanographic temperature/salinity formula that
knows nothing about contact mechanics. Given only the **cited** bulk modulus (CRC, 2 sig figs) and
the membrane's own published density, the simulated packet chain runs at **1792.5 m/s**, and with
the derived packing factor √(2/3) that is **1463.5 m/s against the published 1474.78 — 0.76%**.
The mode measurement matches the derived dispersion to **0.007%** and is **scale-invariant to five
significant figures** (10× smaller packets, same speed).

**THE INSTRUMENT REFUTATION, and it was mine.** The first wave measurement timed the front's
*first arrival* against a fraction of the piston speed, and reported 15% high. The sweep convicted
it: 1795.0 / 1824.7 / 1878.8 / 1928.8 / 1975.6 / **2069.3** m/s at triggers 3e-1 → 1e-6 — a
monotone dependence on the threshold, because a discrete lattice puts an exponentially small
**precursor** ahead of the energy-carrying front. *The threshold being an external number (the
piston's own speed) did not save it* — external or not, it defined a quantity that is not the
sound speed. Replaced by a **threshold-free normal-mode period**, with the exact discrete
dispersion `ω = 2√(k/m)·sin(qa/2)` so the finite-N correction is derived too. The refuted
instrument is kept as a passing test so it cannot quietly return. (An earlier defect in the same
function is also recorded there: a run window of 3 oscillation periods, in which the front crosses
only ~19 of 60 grains — the other 41 never moved and the fit returned a *negative* speed.)

**THE BODY ON THE GROUND.** theHuman's published 668.7 N over its published 276 cm² foot rests on
**241,576** of theGround's published grains (d₅₀ = 0.35 mm, porosity 0.42). Elastic contact
settlement: **0.129 µm** over the footing's own equivalent width — the seam holds, the foot
neither floats nor sinks through. **THE REGIME SEPARATION is the real result:** theHuman publishes
a **3.122 mm** footprint, which is **24,148× larger** than the elastic answer — so that footprint
is theGround's Terzaghi *rearrangement*, not compression, and **the two mechanisms do not
double-count**. The finding survives softening the contact law by **1000×** (still 24× under the
published footprint), so it does not rest on the linear-vs-Hertz choice.

**NAMED LIMITS, measured not asserted.** Restitution is **exactly 1.000000** — the force is
conservative, so a dropped packet returns to its drop height forever; real ground damps, and a
dissipative term is UNBUILT (this is how a future one will be detected). And the linear law reads
**E_eff = 31.1 GPa** against solid quartz's 37 GPa at light load, because `k` does not vanish at
zero penetration — exactly what a **Hertzian** `k ∝ √h` refinement would fix, still named unbuilt.
Deliberately *not* claimed: theGround's 0.58 solid fraction is `1 − POROSITY` with porosity
**declared**, so reading it back as "the random-loose-packing fraction of spheres" would be
circular, and it is not used as a prediction anywhere.

### Stage 10 — Damping is the medium, not a coefficient. And friction. — **BUILT, PASSED**
Every contact model in the world carries a damping constant somebody chose. This one does not.

**THE STATEMENT.** A struck grain does not lose energy to a fitted number — it launches a
compression wave into the material behind it, and that energy never comes back. What a truncated
simulation calls "damping" is the **impedance of the medium it truncated**:
`Z = √(km) = √(2/3)·√(Bρ₀)·πR²` — the same computed linear packing fraction that set the wave
speed in Stage 9, because a chain carrying a rod's stiffness with 2/3 a rod's mass carries √(2/3)
of a rod's impedance. Both routes agree to float64. A consequence with nothing chosen in it: a
packet meeting its own medium is **exactly half-critically damped** (ζ = Z/2√(km) = ½).

**TWO INDEPENDENT ROUTES TO Z, both measured.** *Wave route* — a chain terminated at Z must not
reflect: measured **R = 0.0012** at Z, **0.1122** at both 2Z and 0.5Z (transmission-line theory
says ((f−1)/(f+1))² = 0.1111), and **0.9988** at a free end (theory 1). Energy books close to
1.7e-5. *Impact route* — a mass striking a semi-infinite medium decays as `v = v₀e^(−Zt/M)`:
measured **0.50%** from Z/M at M/m = 100 and **1.27%** at M/m = 40, R² = 1.000000, in a code path
**containing no damping term at all**. The control confirms the measurement can fail (it sits 101%
from Z/2 and 50% from 2Z), and the rate is insensitive to the fit window across 2–4 e-foldings.

**THE TOPOLOGY THE CHAIN CORRECTED, kept as a test.** The lumped model was first wired with the
dashpot **parallel** to the contact spring (Kelvin–Voigt), giving ζ = 0.05 and a lively e = 0.859.
The radiating chain — which has no damping term to argue with — returned ~0. The chain was right:
the impactor pushes the contact spring and the spring pushes a medium that radiates, so they act
**in series** (Maxwell), which inverts the damping ratio to ζ = √(kM)/2Z = 5 — overdamped, and
**the body lands instead of bouncing**. *A wrong topology has the right units and the right
constants*; only a model that could disagree found it. Stage 9's undamped contact returned exactly
1.0; restitution is now ~0.

**FRICTION, labelled honestly.** `μ = tan(φ)` is the *definition* of a friction angle, so this is
a restatement, not a derivation — what is not trivial is that φ was **grown**: theGround's repose
angle emerged at **40.03°** from the granular trainer's local stochastic rule, inside the
researched lunar-regolith band. The consequence is a prediction: the terrain this world grew is
walkable by the repose angle it grew — aTerrain's p95 slope 33.00° and mean 19.46° sit under
40.03°, a 1.29× margin at the steepest published slope — and **aTerrain independently publishes
`slopes_below_repose = true`**. Two routes, one answer. A standing body has 561.7 N of shear
available against its own 668.7 N of weight.

**THREE MORE INSTRUMENT DEFECTS, each caught by a run and kept as code.** (1) A hand-integrated
potential had the **sign backwards**, so pulse energy went negative and every ratio blew to −1e8
— fixed by deriving U from the form that already has a referee. (2) The `imbalance <= tol` check
**passed vacuously on that negative number**; it now reads `0 <= imbalance <= tol`. (3) A
pre-compressed chain with free ends **is not in equilibrium** — it relaxed explosively and the
dashpots absorbed the static release instead of the pulse (R and T both ~3.8e5). A confining end
clamp equal to the pre-compression's own force fixes it, which is what confining pressure is.
Also: `slopes_below_repose` belongs to **aTerrain**, not theGround — guessing which membrane owns
a number is the same error class as matching names instead of definitions.

### Stage 11 — Hertzian contact and the Mindlin tangential force — **BUILT, PASSED**
The refinement Stage 9 named, and the tangential half the seam was missing.

**TWO CITED MODULI, AND EXACTLY TWO.** An isotropic elastic solid needs two independent moduli;
bulk alone cannot produce a contact theory. `story/matter.py` now publishes **G** alongside B (both
measured, entering as theStar's fusion constants do) and E, ν follow — α-quartz's unusually low
**ν = 0.0742** among them. **Water is deliberately absent and `hertz.py` REFUSES it**: a fluid has
no shear modulus, so Hertzian contact does not apply, and that is a scope boundary rather than a
missing number to substitute.

**THE DEFECT IS FIXED.** Hertzian stiffness `k_n = 2E*√(R_eff·h)` is **exactly zero** at zero
penetration, where the linear law held 1.0e7 N/m all the way down. Under a foot the pack softens
from **31.1 GPa to 303 MPa** — 103×, into the range a real soil's small-strain modulus occupies.

**THE FLAGSHIP: the textbook exponent EMERGES.** Because stiffness rises with the load it carries,
sound speed in a granular pack must go as `c ∝ F^(1/6)`. Measured through Stage 9's
already-validated threshold-free mode instrument over a 100× force range: **0.1666 against the
derived 0.1667**, speeds 286 → 904 m/s (dry sand's own measured band). The **linear law is run
through the identical instrument as a control and returns exponent ~0** (0.74% spread over the
same range, at solid-quartz speed 4576 m/s) — so the test can come out two ways, which is what
makes it a test.

**THE IDENTITY EVERY MODULUS CANCELS OUT OF.** `k_t/k_n = 2(1−ν)/(2−ν) = 0.9615` — a pure function
of Poisson's ratio, checked against the full Mindlin/Hertz expressions and independent of
penetration, so a contact's stick-to-slip character does not drift as it loads.

**A PRIOR CLAIM CLOSED HONESTLY.** Stage 9 asserted its elastic-vs-plastic finding "survives 1000×
softening" without knowing the real factor. Hertz supplies it: **103×, inside the bracket tested**,
and settlement 13.3 µm remains **235×** under theHuman's published 3.122 mm footprint. The
mechanisms stay separate; the hypothetical is now a measurement.

**THE TANGENTIAL FORCE, AND A SIMULATED EXPERIMENT.** Mindlin `k_t = 8G*a(h)` under a Coulomb
ceiling at μ = tan(grown repose). A **simulated tilt table** — quasi-static by construction, which
is literally how a friction angle is measured in a lab — releases at **40.030000°**, the angle the
granular trainer GREW by piling grains up. Two unrelated experiments, one number. On aTerrain's
steepest published slope each of the 241,576 contacts under a foot carries its 1.508 mN share
without slipping, deforming **14.5 nm** first — tribology's pre-sliding displacement, falling out
of Mindlin + Coulomb rather than being smoothed in. Past the ceiling it slides at exactly μF_n, and
a foot skidding 1 cm turns **4.71 J** into heat: **the first genuinely irreversible process in this
contact model** (Stage 10's damping is radiation — transfer, not loss).

### Stage 12 — Rolling resistance and contact torque — **BUILT, PASSED**
The last place in a contact model where a coefficient normally gets plugged in.

**CONTACT TORQUE is not a new law.** Stage 11's tangential force acts at a lever arm R from the
centre, so `τ = R·F_t` — the moment of a force already derived, and the whole reason a grain can
spin rather than merely translate.

**ROLLING RESISTANCE IS THE MOMENT OF A DISSIPATION ALREADY DERIVED.** A rolling sphere loads the
material at the front of its contact patch and unloads it at the back. Stage 10's radiative damping
pressure is proportional to the local indentation *rate*, which is antisymmetric across the patch —
so it adds **no net force and a net moment**:
`τ_r = ∫ s·(ζ_A·v·s/R) dA = ζ_A·v·πa⁴/(4R)`, with ζ_A = ρc_p the half-space impedance per unit
area, a from Hertz, and nothing chosen. **Two independent integrals confirm it**: the closed form
matches quadrature to 1e-6, and the *moment* route's `τ_r·ω` equals the *energy* route's direct
`∫ζ_A(ḣ)²dA` to 1e-6 — different integrals of the same physics, which is how wrong algebra gets
caught.

**TWO PREDICTIONS THAT DISAGREE WITH THE TEXTBOOK MODEL, on the record.** Resistance is **viscous**
— exactly 3× at 3× the speed, and **exactly zero at rest**, where a constant-μᵣ model wrongly
resists a parked sphere and then needs a stiction hack to hide it. And it stiffens as **N^(4/3)**
(measured 16.000× at 8× load, against 8^(4/3) = 16.000).

**THE FLAGSHIP: 5/7, and it must not move.** A sphere launched sliding transitions to rolling at
`v = (5/7)v₀` — a fraction that depends on nothing but the 2/5 in a solid sphere's moment of
inertia, and that **appears nowhere in the code**. Measured **0.71427–0.71428 against 0.71429** at
the grown friction, at half that friction, at Earth gravity, and at 64× the mass with 4× the
radius. Friction, gravity, mass, radius and material all cancel out of it, so one measurement tests
the lever arm, the Coulomb ceiling, the inertia and the integrator simultaneously.

**A FREE CHECK ON BOTH CITED MODULI.** The solid's longitudinal speed `c_p = √((B+4G/3)/ρ)` comes
out at **6008 m/s** — quartz's measured value — confirming neither cited constant is wrong. (Stage
9's √(B/ρ) is the *fluid* speed, correct for water and 3737 m/s here, which is why a solid needs
the shear term.)

**THE HONEST SCOPE, and it is the useful finding.** μᵣ = 7.8e-07 at 1 m/s — rolling is **~1,000,000×
cheaper than sliding**, which is why a wheel is worth having, but it is also **orders below any
handbook μᵣ** (steel-on-steel ~1e-3). That is not hidden and not fitted around: this model contains
only the **acoustic** term. Real rolling resistance is dominated by **bulk hysteresis**, which needs
a published loss tangent that **no membrane in this world has** — so the gap *is* the missing
measurement, named UNBUILT. Plastic rearrangement (theGround's Terzaghi mechanism) is likewise
absent here.

### Stage 13 — Hysteretic rolling loss — **BUILT, PASSED — and it CORRECTS Stage 12**
**THE CORRECTION FIRST.** Stage 12 recorded that hysteretic rolling loss "needs a published loss
tangent that no membrane has." **That was too broad, and building it is how the error surfaced.**
There are two hysteresis mechanisms, not one: **contact microslip** (Mindlin–Deresiewicz) is
derivable from μ and G*, both already in hand — this stage — while **bulk viscoelastic loss** (a
material loss tangent) genuinely still needs a citation and remains UNBUILT. The lumped claim is
replaced by the sharp split.

**WHY STAGE 11 HAD NO HYSTERESIS, precisely.** Its tangential law is a linear spring under a hard
cap: loading traces δ = T/k_t and unloading traces the *same line*, so the loop encloses **exactly
zero area** — computed with the same integral, not asserted. The absence of dissipation was **the
linear approximation, never a missing material constant.** Mindlin's real contact doesn't stick
uniformly: an annulus at the rim slips while the centre holds and grows with load, so the paths
differ and the loop has area. Its tangent at the origin *is* Stage 11's k_t (that law was the
tangent, which is why it was right at small load and lossless everywhere), and full slip arrives
**1.5× further out** than the linear model put it — the approximation stated as a number.

**THE FLAGSHIP: the cubic law.** Derived here by expanding the Masing loop:
`ΔW ≈ 2T³/(9μN·k_t)` — cubic in tangential amplitude, the known signature of fretting/microslip
damping. Measured log-log slope **3.0056** against 3 in the asymptotic regime, and the exact loop
integral converges to the derived asymptote within **0.67%** — two routes, one number.

**A TEST OF MINE WAS WRONG AND THE MODEL WAS RIGHT.** The first exponent fit ran at 2–16% of the
Coulomb ceiling, read 3.0474, and called the model wrong. Varying the quadrature from 5k to 320k
points moved the integral only in the **ninth significant figure**, so the rise is physics, not
discretisation: **the cubic law is an asymptote**, and the loop stiffens as full slip approaches
(slope 3.17 at 10–40% of the ceiling). The test now asks in the regime where the law holds *and*
records the departure as a measured fact — a wheel worked near its friction limit pays
disproportionately, which the constant-μᵣ model cannot say at all.

**ROLLING.** One load cycle happens per 2a of travel, so `F_r = ΔW/(2a)` and μᵣ = F_r/N — and
because ΔW ∝ T³, **microslip rolling loss grows cubically with transmitted tractive force**
(measured 8.054× for 2× traction). At 90% traction μᵣ = 4.66e-04, **597× Stage 12's radiative
floor**, and the two add, being different mechanisms. Both together still sit under a handbook
steel-on-steel ~1e-3 — the remainder is bulk viscoelastic hysteresis, still awaiting a loss
tangent, still named.

### Stage 14 — Bulk viscoelastic hysteresis — **BUILT, PASSED** (the third and last dissipation)
Stage 12 added radiation (energy leaving as sound), Stage 13 added contact microslip (a slip
annulus at the rim). This is the one acting *inside* the material: compress a solid and it warms,
the warm region conducts heat outward, and on the return stroke that heat does not come back —
Zener's thermoelastic damping, which needs **no loss tangent handed to it**, only thermal
constants (α, c_p, k, newly cited in `story/matter.py` the way B and G were).

**IT READS THE WORLD'S OWN TEMPERATURE.** `Δ = Eα²T/(ρc_p) = 1.96e-03` at aBlueWorld's published
`T_surface = 279.19 K`, and doubling T doubles Δ exactly — **a colder world's rock is a better
spring**, as a consequence rather than a setting.

**THE SHAPE IS THE PREDICTION, with two different zeros.** `tan δ → 0` as ω→0 because a slow cycle
stays **isothermal** (heat equilibrates, no gradient ever forms), and `tan δ → 0` as ω→∞ because a
fast cycle is **adiabatic** (heat has no time to move). Measured 1.96e-09 at both ends — the same
zero for opposite reasons — with the peak exactly at ωτ = 1 and exactly Δ/2.

**THE FLAGSHIP: a rolling speed of maximum loss.** Since a rolling contact loads at ω = πv/a, the
awkward middle happens at a *speed*: **v_peak = D/(πa) = 5.41 mm/s** for the 198 µm contact tested,
with tan δ falling away by 50× at a hundredth and a hundred times that speed. A 4× bigger contact
peaks at exactly a quarter the speed, because heat has four times as far to go. The constant-μᵣ
model cannot express any of this.

**THE LOAD LAW.** μᵣ = (2π/5)·tan δ·(a/R), giving the classic hysteretic **N^(1/3)** scaling —
measured exponent **0.3333** over a 512× load range.

**THE CLOSING DECOMPOSITION — three mechanisms, and they are not interchangeable.** A **freely
coasting** wheel pays radiation (7.8e-07) and hysteresis (5.3e-08) but **exactly nothing** to
microslip, whose T³ dependence vanishes with the tractive force (1.3e-31). A **hard-driven** wheel
is dominated by microslip (4.7e-04), 600× everything else. And for hard quartz, thermoelastic
hysteresis is the *smallest* of the three — a soft polymer inverts that completely, since tan δ ≈
0.1 is four orders above quartz's thermoelastic 1.1e-05, **which is why rubber tyres and rock
behave nothing alike**. Which mechanism rules is now a question with a computed answer.

**ROBUSTNESS AND THE NAMED REMAINDER.** The conclusion survives varying **every** cited thermal
constant by 3× in both directions (worst case 4.75e-07, still far under a handbook ~1e-3), so it
does not rest on the precision of a citation. And `rolling_coefficient` takes tan δ as an
**argument**: hand it the derived thermoelastic value today, or a measured total loss tangent the
day one is published. **Anelastic bulk loss (dislocation motion, grain-boundary sliding) remains
UNBUILT and still needs a real measurement** — but nothing has to be rewritten to accept one.

### Stage 15 — Anelastic bulk loss — **BUILT, PASSED — the microstructure CANCELS**
Stage 14 deliberately left `rolling_coefficient`'s tan δ as an *argument* so a measured loss tangent
could plug in later. **It is filled here by a derivation instead** — the third time in this lane a
"needs a citation" note turned out to be reachable, and for the same reason each time: the question
was never what value the constant should take, but what physical thing it is.

**WHAT ANELASTIC LOSS ACTUALLY IS IN A GRANULAR SOLID.** The dominant internal-friction mechanism
in rock and soil is not dislocation motion — it is **frictional sliding on internal surfaces**, and
in a granular medium those surfaces are the grain contacts. Stage 13 already derived what one
contact dissipates per cycle; the bulk loss is that summed over the contacts a cubic metre holds,
and the contact count comes from theGround's own **published porosity and median grain size**.

**THE RESULT, and the ending is the surprise:**
`tan δ = 2τ/(9π·μ·σ)` — **every microstructural term cancels.** Grain size, porosity, contact
stiffness, both elastic moduli: all gone. The bulk anelastic loss of a frictional granular medium
depends on nothing but the ratio of shear amplitude to confining stress, and on μ. Nobody chose
that simplification; it is what the sum does — and it is why measured Q for granular materials is so
stubbornly universal across wildly different mineralogies. **Verified numerically, not just on
paper**: a 100× sweep of grain size and the full loose-to-dense porosity range both move tan δ by
**0.000%**.

**THE MAGNITUDE, unfitted.** **Q = 109** at τ/σ = 0.1 — squarely in the order-10² band crustal rock
and soil are measured in. The inputs were theGround's published porosity and d₅₀, its **grown**
repose angle, and two cited elastic moduli. The two routes (closed form vs explicit per-contact sum
with Stage 13's exact loop) agree to **0.80%** in the asymptotic regime, and the exact loop runs
**8.7% hot** at larger amplitude — the same super-cubic approach to full slip Stage 13 measured,
recorded rather than hidden.

**TWO ORTHOGONAL SIGNATURES, which is the real payoff.** Frictional loss is **amplitude-dependent**
(exponent 1.027 against 1) and **frequency-independent** — there is no rate anywhere in it. Stage
14's thermoelastic loss is the mirror image: amplitude-independent and **peaked in frequency**
(50× swing over the same span). So a medium's damping can be **decomposed by experiment** — sweep
amplitude at fixed frequency to see one, frequency at fixed amplitude to see the other. A single
fitted loss tangent could never have separated them. It also means **"the" loss tangent of a
granular medium is not a constant of the material**, and rock Q genuinely falls with strain.

**THE HONEST REMAINDER.** This is the frictional mechanism. **Granato–Lücke dislocation damping**
needs dislocation densities and pinning lengths, and **point-defect relaxation** needs activation
energies — neither is published, both remain UNBUILT, and for room-temperature quartz both are
genuinely small. The asymptotic ceiling 2/(9π) = 0.0707 is a small-amplitude formula pushed to full
slip; the exact loop gives 0.189 near it, so the ceiling is labelled an order of magnitude rather
than a limit.

### Stage 16 — Specular-to-specular bounce chains — **BUILT, PASSED — no new pass needed**
Stage 6's one-bounce gather was diffuse-receive only and named specular chains unbuilt. They need
**no new render pass at all**, for the reason that justifies this lane's whole framing:

**A SPECULAR LOBE IS A GAUSSIAN, AND GAUSSIANS ADD VARIANCES.** So an N-bounce chain is not N
passes — it collapses to **one** Gaussian lobe: `s_chain = √(Σsᵢ²)` (variances add) and
`F_chain = ΠFᵢ(θ)` (Fresnel multiplies). Those are exactly the two numbers
`story/matter.paint_specular` already takes, so **a chain renders through the Stage 1 kernel
unchanged** — one more reader of one field, again. Verified against a 400,000-ray Monte Carlo, with
a control proving the test can distinguish the right law from the wrong one (summing standard
deviations instead of variances lands 36% wide).

**THE MONTE CARLO FOUND A REAL OMISSION IN MY MODEL.** The first version carried one lobe width and
read 2.4% low — not noise, at 400k rays. Resolving the spread along and across the incidence plane
showed why: **the mirror gain is 2 in the plane of incidence and 2·cos θ out of it**, so a rough
mirror's lobe is an *ellipse*, not a disc. Measured 0.07% and 0.10% against those two laws. This is
the foreshortening that makes a grazing reflection on water **smear into a long streak** instead of
a round highlight — a real phenomenon the single-width model could not have produced.

**THE CHAIN DEPTH IS DERIVED FROM THE OUTPUT FORMAT.** The compositor writes uint8, so nothing under
half a channel step (1/510) can move a pixel by more than one LSB; energy decays as the Fresnel
product, so `n_max(θ) = ⌊ln(1/510)/ln F(θ)⌋`. For water that is a strong statement: **n_max = 1 at
normal incidence** — a second specular bounce off water is invisible — and **n_max = 6 at 80°**.
Specular chains are a *grazing-angle phenomenon*, derived, which is exactly where people see them.
Same discipline as `gpu_pipeline.FOOTPRINT`, derived from the compositor's own weight cutoff.

**PROVEN IN A FRAME, and an overclaim corrected.** One bounce shows (25,134 subpixels), two bounces
are a visibly distinct term (24,582 differ from one), and a three-bounce water chain **cannot move
any channel by more than 1 LSB** — 83 of 921,600 subpixels (0.01%) shift at all. My first version
asserted **bit-identity** there and failed: a sub-step contribution still flips the rounding of any
channel already sitting within it of an integer boundary. The derivation bounds the error to one
LSB; it never promised zero, and the test now says so.

**NAMED UNBUILT — one a real physical omission, not a scope choice.** **Polarization**: successive
specular bounces polarize the beam and real Fresnel differs for s- and p-polarization, so a long
chain's energy is not truly the product of unpolarized coefficients (Schlick's unpolarized form is
used throughout). **Curved-mirror focusing**: composition assumes lobes stay narrow and the geometry
does not converge — a concave specular surface focuses, which is Stage 5's caustic machinery pointed
at reflection rather than refraction.

### Stage 17 — Polarization — **BUILT, PASSED — and it CORRECTS Stage 16 by up to 26×**
Stage 16 flagged polarization as a *real physical omission* rather than a scope choice. It was, and
the size of the error is now measured.

**WHY A CHAIN GETS IT WRONG.** s-polarized light always reflects better off a dielectric than
p-polarized light, so every bounce filters the beam further toward s — **a chain polarizes itself.**
Convexity then guarantees the direction of the error:
`(R_sⁿ + R_pⁿ)/2 ≥ ((R_s+R_p)/2)ⁿ`, so **Stage 16 UNDERESTIMATED chain energy**, worse the deeper the
chain. Measured for water at 60°: **1.00× / 1.87× / 3.61× / 6.97× / 26.03×** at depths 1/2/3/4/6.
Meanwhile the degree of polarization climbs 0.932 → 0.998 → 1.000 — after a few bounces essentially
all surviving light is in the strongly-reflecting state.

**A NEVER-FITTED PREDICTION FROM DENSITY.** Brewster's angle is arctan(n), and n comes from
aSaltOcean's **published density** through Lorentz–Lorenz (Stage 0). So the world's own ocean density
predicts **θ_B = 53.34°** against water's measured ~53.1° — the angle at which glare goes perfectly
polarized, reached from a number that knows nothing about optics. At that angle R_p is float-zero
(4.8e-33, gate eps²) while R_s holds at **8.24%** — a ratio of 1.7e31, and that surviving 8% is
exactly what a polarising filter removes.

**SCHLICK, HONESTLY ASSESSED.** Stages 1, 11 and 16 all use Schlick's approximation. Measured against
exact Fresnel: max absolute error **0.0101 out to 60°** (validating those stages where they operate),
drifting to **0.0567 near grazing**. And being one scalar, it cannot represent the s/p split at any
angle — which is the structural reason it could not have produced this stage's correction.

**TWO CHECKS THAT CATCH REAL BUGS.** `R + T = 1` for **each** polarization at every angle to
**4.4e-16** — the check that catches a dropped (n₂cosθₜ)/(n₁cosθᵢ) factor or an inverted sign
convention. And the **critical angle agrees with Stage 4's refraction kernel**: θ_c = 48.098° from
arcsin(1/n), where the kernel's TIR discriminant k = 1.1e-16 — two independent routes to one
boundary, three stages apart.

**THE CORRECTED DEPTH BOUND AND THE FRAME.** Stage 16 said 6 visible bounces at 80°; polarization
says **7**, because the s-component decays more slowly than the average. And the correction renders
**through Stage 1's own kernel** — F₀ 1.41e-04 → 8.46e-04 (6.0×), 4,764 subpixels brighter — with no
polarization state in the renderer, just a corrected number. Frames:
`agent_logs/optics_chain_{polarized,unpolarized}.png`.

**TWO INSTRUMENT CORRECTIONS, both mine, both the same species.** The Brewster test first used a
round `1e-24` for "float zero" and failed on a correct 4.8e-33 — R_p is r_p *squared*, so its floor
is eps², not eps; the gate is now derived from machine epsilon. It then demanded `R_s > 0.1` and
failed on water's true 0.0824 — a threshold invented rather than read, replaced by the ratio, which
is what the physics actually claims.

**NAMED UNBUILT.** **Circular/elliptical polarization** needs complex amplitudes with a relative
phase (TIR's phase shift is dropped here). **Metals** have a complex refractive index and are
**refused**, not approximated. And a genuine **per-grain polarization state** in the renderer would
need two columns plus an incidence-plane frame — the *chain* correction needs neither, which is why
it shipped.

### Stage 18 — Multi-interface & the curved floor — **BUILT, PASSED** (the last original Part II item)
**THE TELESCOPING THEOREM, which is why Stage 4 survives intact.** Across parallel interfaces
`n·sinθ` is conserved, so the exit direction depends only on first and last medium — **Stage 4's
single-η kernel was already ANGLE-EXACT for any layered stack** (verified: inserting an ice layer
changes the exit direction by 0.00e+00). What a stack adds is only a lateral walk-off,
`t(tanθ₁−tanθ₂)` — closed form matches the exact trace, and its **visibility bound is derived**:
ice up to 0.36 scene units thick renders CELL-exactly through the existing kernel, thicker needs the
walk-off term. (Convention note, paid for: the textbook "beam displacement" is the *perpendicular*
offset, smaller by cosθ — the *horizontal* one decides which cell a ray reads.)
**ICE COMES FREE — the stage's never-fitted prediction.** Lorentz–Lorenz is additive in mass, so
water's refractivity at ice's density (917 kg/m³) predicts **n_ice = 1.3034 vs measured 1.31
(0.5%)** — the phase change costs nothing and no ice constant is cited anywhere.
**THE CURVED FLOOR, which aSaltOcean actually has** (mean depth 2861 m, deepest 8582 m — the plane
was always an approximation). The declared model is **one fixed-point step on the floor's own
height field**: intersect the mean plane, read that cell's published height, re-intersect, read the
colour where the ray actually lands. Against the exact paraboloid referee over 400 refracted rays
into a 35%-sag bowl: plane error 0.223 → one-step **0.032 (6.9× better)**. In the kernel: an
explicit flat height field renders **bit-identical** (the step recomputes identical numbers), and a
bowl floor moves 154,991 subpixels through the same water — the floor's own published depths now
bend what you see.

### Stage 19 — Curved-mirror focusing — **BUILT, PASSED** (Stage 5's machinery pointed at reflection)
A caustic never cared whether the bend came from Snell or a mirror. The deposit instrument is
reused verbatim; only the gain changes — and **the SIGN is the physics**: a mirror throws the ray
to the *opposite* side of the normal, so the fold sits on the minus branch
(`sin(kx*) = −1/(2DAk²)`). My first version carried refraction's sign and **the deposition
histogram refuted it** — the measured bands (0.3175/0.4325) landed exactly on the correct branch
(0.3205/0.4295, err 0.003). Conservation exact (24,000 = 24,000).
**THE CROSS-STAGE IDENTITY:** the same sine surface over the same drop folds at depths in the ratio
**(1−η)/2 = 0.1279**, measured equal to 12 digits — Stages 5, 16 and 19 in one line.
**THE R/2 FLAGSHIP:** a spherical mirror focuses parallel light at **−1.0006 vs −R/2 = −1.0000
(0.06%)** inside an aperture **derived from the instrument** (a < √(2R·cell)); opening it 4× walks
the focus **short, toward the mirror** (−1.0006 → −1.0112) — spherical aberration as a measured
prediction. (And a second sign lesson, kept in the test: naming a direction and checking its sign
are two different acts.)

### Stage 20 — Complex Fresnel: TIR phase, circularity, metals — **BUILT, PASSED**
The full complex amplitudes — what Stage 17's power-only model structurally could not say.
**Its dielectric limit IS Stage 17's module** (worst diff 0.00e+00 over 88 angles), and under TIR
both amplitudes have unit magnitude with **different phases** — the dropped physics.
**THE FRESNEL RHOMB, DERIVED:** max single-bounce retardance is closed-form in the index ratio
(`tan(Δ/2) = (1−n²)/2n`) — glass gives **45.94°** (closed form = numeric sweep to 6 digits), the
45° crossing sits at the classic **48.6°** cut (of the 48.6/54.6 pair), and two bounces drive
Stokes **|V| = 1.00000000** — a quarter-wave plate from glass and geometry, circularity reached.
**AND THE IMPOSSIBILITY:** water's max retardance is **33.4° < 45°** — *a Fresnel rhomb cannot be
made of water*, a derived impossibility as falsifiable as any possibility.
**METALS** enter as cited complex indices (Johnson & Christy Cu, Rakić Al) and colour comes OUT:
aluminium reflects **(0.913, 0.921, 0.920)** — the measured ~92%, nearly neutral, why it makes a
colourless mirror — while copper reflects **(0.944, 0.668, 0.577)**: **copper's redness is
derived**, nothing tuned. A colour is a measurement, again. And a metal has **no Brewster zero** —
R_p bottoms at 0.747 — which is why a polarising filter kills water glare but not metallic glare.

---

# THE LEDGER CLOSES (2026-08-05)

Twenty stages, twelve gate suites (**244 checks**), every falsifier named before its build. What
remains unbuilt is not a queue — it is three **measured refusals**, each with its reason on record:

1. **A per-grain polarization state in the renderer.** A Stokes state needs three components;
   `PROP3` (col 15) is the buffer's **last free column**. The chain-level correction (Stage 17)
   ships through the existing scalar F₀, and burning the final column for a sub-LSB refinement
   fails the house's own budget discipline. Refused on a counted budget, not forgotten.
2. **Granato–Lücke dislocation damping & point-defect relaxation.** These name *microstructural
   inventories* (dislocation densities, pinning lengths, activation energies) that no membrane
   publishes and no process already in hand supplies — the citation claim survived the same
   scrutiny that overturned it three times elsewhere. Bounded: literature rock values put them
   ~100× below the derived frictional Q⁻¹ at any strain that matters here.
3. **Circular polarization *in the render path*** (as opposed to the derivation, which Stage 20
   completes). Same column budget as refusal 1, and no membrane yet emits circularly polarized
   light for a renderer to carry.

The theory stands as built: **two forces, one density field, and every reader derived** — optics
(specular, refraction, caustics, dispersion, bounce, chains, polarization, interfaces, mirrors,
metals), contact (Hertz, Mindlin, the seam), sound (impedance, the chain speed), and dissipation
(radiation, microslip, thermoelastic, frictional-anelastic — decomposable by experiment). Along the
way the method refuted five of its own instruments, two of its own models, and three of its own
"needs a citation" claims — each conviction pinned as a test that goes red if the record drifts.

### Stage 21 — The adoption: aSaltOcean's glint becomes a READER (2026-08-05)

The ledger's three refusals stand, but one gap was not a refusal: the world's own ocean was still
PAINTING its glint. The old `sunglint_intensity = 0.02111` was a typed constant from a sourced
n = 1.34; the emit added it to the water's colour as a warm patch, so the light half of the theory
had derived F₀ for test membranes while the flagship ocean kept a hand-written number. **The
membrane now reads its own glint**: `derive()` pushes its published density through Lorentz–Lorenz
to n and on to Fresnel F₀ (`0.02149`, +1.8% from the typed value — the dissolved load is what the
glint is), and `emit()` paints the READER columns instead of the colour: `paint_specular` with the
derived F₀ and the sea's own slope, the ice **refusing** the water's reader (its optics are not
published, so the columns are a silence), and a `sun_direction(t)` declaration that the renderer's
light and the baked diffuse must agree on. **No light set, no glint rendered — nothing painted, ever.**

**THE FALSIFIERS (T11, 11 checks pre-registered before the renderer read a pixel):**
  a. published `sunglint_intensity` == `fresnel_f0(refractive_index(density))` **exactly** (1e-12) —
     the typed n = 1.34 is gone, the published number and the derived number are the SAME number;
  b. the real buffer carries the reader: SPEC_F0/SPEC_SLOPE on every water grain, and the 10,757 ice
     grains carry both columns exactly 0.0;
  c. rendered under the membrane's OWN sun, the kernel's glint matches the float64 referee
     (max |diff| = 1.21e-06 vs EPS_KERNEL_MAX 1e-03), lights a tight patch (2,257 of 23,243 water
     grains, 9.7%), and shows in the frame (21,887 subpixels);
  d. the old paint is PROVABLY gone: at the sub-solar point the colour is the float64 diffuse
     replica bit-for-bit (max |diff| = 0.00e+00);
  e. the clay controls hold on the real buffer: zeroed columns under the sun, and populated columns
     under no light, are both bit-identical to the emitted baseline.

**THE ONE DECLARATION:** `sun_direction(t)` — same phase as theTerrain's sun, unit length, in the
water's own frame. The emit bakes the diffuse with it, the live viewer sets the renderer's light
with it, and the renderer's specular kernel draws the glint where the half-vector says. **Baked
diffuse and glint can never disagree about where the sun is, because neither chose.**

## THE GATE (all of it)

```bash
python ChimeraEngine/test_optics.py          # 58 checks: closure, referee, controls, lensing chain, bounce, adoption
python ChimeraEngine/test_overlap.py         # 22 checks: v1 machinery + pinned refutation + v2 seam closure
python ChimeraEngine/test_seam.py            # 17 checks: stiffness identity, sound speed, body-on-ground
python ChimeraEngine/test_damping.py         # 25 checks: impedance, reflection, decay rate, friction
python ChimeraEngine/test_hertz.py           # 21 checks: Hertz, the P^(1/6) exponent, Mindlin, tilt table
python ChimeraEngine/test_rolling.py         # 13 checks: contact torque, rolling resistance, the 5/7 law
python ChimeraEngine/test_hysteresis.py      # 17 checks: Mindlin microslip, the cubic law, the Stage 12 correction
python ChimeraEngine/test_viscoelastic.py    # 13 checks: Zener damping, the peak rolling speed, the decomposition
python ChimeraEngine/test_anelastic.py       # 13 checks: the cancellation, Q ~ 100, the two signatures
python ChimeraEngine/test_chains.py          # 16 checks: lobe composition, the anisotropy, the derived depth
python ChimeraEngine/test_polarization.py    # 20 checks: Brewster from density, R+T=1, the Stage 16 correction
python ChimeraEngine/test_final_optics.py    # 22 checks: telescoping, curved floor, R/2 focus, rhomb, metals
python ChimeraEngine/test_render_pipeline.py # 47/47 baseline terms, bit-level
python ChimeraEngine/test_perf_guard.py      # 11 checks
python ChimeraEngine/benchmark_optics.py     # specular cost A/B; --refraction for the lensing arm
```
