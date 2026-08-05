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

## THE GATE (all of it)

```bash
python ChimeraEngine/test_optics.py          # 47 checks: closure, referee, controls, lensing chain, bounce
python ChimeraEngine/test_overlap.py         # 22 checks: v1 machinery + pinned refutation + v2 seam closure
python ChimeraEngine/test_seam.py            # 17 checks: stiffness identity, sound speed, body-on-ground
python ChimeraEngine/test_damping.py         # 25 checks: impedance, reflection, decay rate, friction
python ChimeraEngine/test_render_pipeline.py # 47/47 baseline terms, bit-level
python ChimeraEngine/test_perf_guard.py      # 11 checks
python ChimeraEngine/benchmark_optics.py     # specular cost A/B; --refraction for the lensing arm
```
