# THE LIVING MATTER — the shaker's energies are physics, or they are nothing

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
> **[docs/THE_LAW.md](THE_LAW.md)** · the method: `docs/THE_WORKFLOW.md` §0
> · 26 rules: `Chimera/docs/EXPERIMENTAL_METHOD.md` · gate: `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

> Drafted 2026-08-03. Status: **PHASE 1 DONE (instrument exact, falsifier fired) ·
> PHASE-2-PREREQUISITE DONE (parallel area update derived and measured: H falls and
> plateaus, parity restored) · PHASE 2 DONE: F1 PASS, F2 PASS, F3 FIRED — the ratio
> structure of the derived J reproduces the anatomy from measured tissue tensions
> (Foty 1996), the cortical-floor scale does not reproduce rung-1's kinetics (τ ratio
> 0.07, direction opposite to the prediction — published, Rule 17) · **PHASE 2b DONE:
> F1/F2/F3 ALL PASS — the liquidity anchor (kT_eff = σ̄·ℓ², σ̄ = 7.66 mN/m geometric
> mean) closes the theory with zero fitted numbers (τ ratio 0.60) · **PHASE 4 FIRST
> CONTROL DONE: sand/rock/medium sorts with rock burial under the derived world J
> (γ_sand = c·d = 36 mN/m, γ_rock = K_IC²/2E = 36.9 J/m² — every input researched),
> uniform control's orientation random across runs · **PHASE 3 DONE: fracture is in
> the shaker — three clauses, each earned by a falsifier firing: (1) fracture needs
> a measured K_IC (granular materials never fracture — 3b's firing), (2) rupture
> requires void-connectivity — cracks advance from surfaces (3c), (3) plucking is
> erosion, distinct from fracture (13 sand deaths, 0.16%, mechanism named). Final
> rule stable: burial persists, rupture curve decays 7,293 → 5, zero bulk
> violations.** · **PHASE 5 DONE: the λ membrane ran — mapping DEAD as predicted
> (derived λ 395–2,375 from measured bulk moduli freezes the lattice: no sort,
> counts frozen ±0.3%, H rises as the λD² term dominates). Published: per-type λ
> is mass conservation, not elasticity; rung-1's 0.9 = K_eff 5.3 MPa measured —
> the shaker's operating point is foam-like; tissue-real K needs deficit-paired
> swaps (named, unbuilt).** · **PHASE 4 FULL FAMILIES DONE: FIRED — the interesting
> way. All five world materials derived (metal 6,094 ≫ rock 36.92 > ice 0.735 >
> sand 0.036 > basin 0.0056 J/m², σ_geo = 2.016, zero fitted numbers). Metal did
> not freeze as the quench caveat predicted — it EVAPORATED (single-grain
> dispersion of a γ/σ_geo ≈ 3,000 material is below critical nucleus; ΔH ≈
> −326,000 per isolated site). Every surviving decade pair ordered (rock 14.5 <
> ice 15.7 < sand 30.2), uniform control did not order, sand/basin inversion
> recorded as the pre-named GG-precision limit. · **PHASE 4 NUCLEATION DONE: FIRED
> — and the firing closed the question. Seeded metal evaporated too (0/14,246):
> the membrane's kinetics were derived for 6-connectivity, the machine runs 18,
> and at 18 every free face of a high-γ material erodes (13×(J_ab−J_aa) <
> 5×(J_ab−J_bb)). The derived law: a type survives iff its face-erosion drive <
> 2λ×population — metal's 37,676 exceeds its jail's 25,642 at any seed size, so
> metal has NO stable finite phase in this shaker; rock's 4% bleed is the same
> equilibrium, solvent. One condition reconciles all three runs, zero fitted
> numbers.**
> Open debts: interfacial pairs are Girifalco-Good
> defaults, tissue type mapping tested on ordering only.
> TISSUE K_IC RESEARCHED (Phase 3d): bone Griffith-legal (124–735 J/m²),
> muscle/skin docked at measured tearing energies (apparent), tendon's band
> open. Next: metal via frozen_type skeleton ONLY — Phase 6 closed the
> per-type λ route (0/14,246 at λ_m = 1.4 AND 2.8; the survival law's form
> is dead, the runaway-drive post-mortem stated), the tissue-scramble
> rupture run (3d's prediction), or the operator's pick.**

---

## THE THEORY

**STATEMENT.** The Cellular Potts Hamiltonian in `Chimera/core/matter.py` —

```
H = Σ_<i,j> J[τ(i),τ(j)] + λ·Σ_t (area_t − target_t)²
```

— is not a free parameterisation. Its J matrix is a discrete projection of the physical
interface energies between the materials it sorts, fixed up to ONE scale constant by
measurements that already exist in the literature (tissue surface tensions, soil
cohesion, fracture surface energies). The rung-1 J matrix, hand-iterated and then
back-labelled `"provenance": "researched"` in `Chimera/docs/matter/matter_library.json`,
is a typed number set wearing a researched tag — and it can be replaced by a derivation.

Someone can disagree: the differential-adhesion mapping may not survive contact with
our materials (bone is not a cell aggregate; sand is not a tissue). That is what the
falsifier is for.

**PREDICTION (not yet measured).** Two numbers, both measurable the day the instrument
exists:

1. **The relaxation time.** A lattice driven by derived J reaches its sorted fixed
   point in a number of sweeps τ_sort that follows from the ratio structure of J/temp —
   not from a cost knee. Today `sweeps` is 160/90/70/26 by whoever set it last. The
   prediction is a curve: interface length vs sweeps, with τ_sort read off it, and the
   derived-J run's τ_sort must land within a factor of 2 of the rung-1 run's. (Neither
   number has ever been measured; the shaker has no energy readout.)
2. **The unswept pairs.** Rung-1 fitted the pairs it needed. The derivation fixes ALL
   pairs, including ones never exercised: J[tendon][medium], J[bone][medium] relative
   ordering, and the world-material pairs (sand|rock, sand|metal) that no run has ever
   sorted. Prediction: a three-material scramble of sand/rock/medium sorts with rock
   burial (γ higher) and sand wetting — readable from measured cohesion + grain size
   alone, no fitting.

**FALSIFIERS (named before the run).** Any one of these kills the theory:

- **F1.** Derived J fails the anatomy control: the rung-1 scramble does NOT sort into
  bone-core / muscle-wrap / skin-shell with tendon pinned at the junction, under the
  existing contrast instrument (`matter_gpu.parity_report`, differential vs uniform).
  The instrument is a known subject — we built it, we know the answer — per Rule 12.
- **F2.** The measured tissue-surface-tension ORDERING (from the literature: which of
  bone/muscle/skin has the highest effective γ) does not reproduce the burial order.
  If reality's ordering disagrees with rung-1's, the mapping is wrong — publish it,
  per Rule 17 (the disagreement is the finding).
- **F3.** τ_sort(derived) differs from τ_sort(rung-1) by more than 2×. Then the scale
  constant is not a scale constant — it is a hidden second freedom, and the
  "derivation" was a fit.

---

## THE MAPPING (the equations that must close)

The CPM effective surface tension at an interface between types a and b is, by exact
algebra on the Hamiltonian (Glazier–Graner; already used at `matter.py:18-21`):

```
γ_CPM(a,b) = J(a,b) − (J(a,a) + J(b,b))/2          [per unit interface, lattice units]
```

The claim of this theory is that there exists ONE constant α such that, for every
material pair:

```
J(a,b) = α · γ_phys(a,b) + J_sym(a,b)
```

where `γ_phys(a,b)` is the measured physical interface energy (N/m — Young-Laplace,
row E2.10) and `J_sym(a,b) = (J(a,a)+J(b,b))/2` carries the self-cohesions, themselves
`α · γ_phys(a)` (each material's measured surface energy). The N(N+1)/2 = 15 free
numbers of the 5×5 symmetric J matrix collapse to: **N measured surface energies +
N(N−1)/2 measured interface energies + 1 scale α.** Nothing is swept.

**α is a lattice constant, not a fit.** J is energy per lattice bond; γ is energy per
unit area. Therefore α = (bond area in m²) / (energy unit) = ℓ²/E₀, where ℓ is the
physical size of one lattice site and E₀ the energy unit. ℓ is set by what a site IS
(one cell ≈ 10 µm for tissue; one grain ≈ 0.072 mm for sand — **researched, in the
library**, Carrier 2003 D50). E₀ for biological tissue is set by the effective
fluctuation energy that `temp` represents. If α so computed puts temp far from 12,
that disagreement is published, not reconciled (Rule 17).

**temp and λ are not exempt.** `temp` is the fluctuation scale — derived from the same
E₀ (one constant serves both). `λ` (area conservation) maps to bulk incompressibility
— a bulk modulus over E₀. If it cannot be derived, it is TRAINED against a named
objective in `docs/objectives/`, with `grown_arrangement.py`'s documented failure
(soft λ drains minority tissues, `grown_arrangement.py:327-331`) as the control case
the objective must reject.

**The known degeneracy, stated plainly:** sorting fixes only RATIOS γ/temp. The
absolute scale is kinetic, not structural. So the theory has exactly one kinetic
freedom, and F3 exists to keep it honest. A theory that admits its one free number
and names the test that can kill it is not a sweep.

---

## WHERE THE MEASUREMENTS COME FROM (Rule: research first, derive second)

THE_GROWTH ruling 2: the first move on any subject is to download measured data.
What the library already holds, researched, and what is missing:

| Quantity | State | Needed for |
|---|---|---|
| density_kg_m3 (all 8 materials) | researched, in library | λ / gravity terms |
| youngs_modulus_gpa (rock, metal, ice, bone) | researched, in library | E2.02 Hooke ports |
| cohesion_kpa + friction_angle_deg (sand, basin) | researched (Mitchell 1972) | world-material J via grain-scale interface energy |
| grain_size_mm (sand 0.072, basin 0.028) | researched (Carrier 2003 / NTRS 20210026714) | ℓ for α |
| **tissue surface tensions (bone/muscle/skin/tendon)** | **MISSING — research task** | the control run's J |
| **surface energies / K_IC (world materials)** | **MISSING — research task** | E2.03 fracture ports |
| units N/m, J/m2, Pa.m0.5 | **RESOLVED 2026-08-01** — in `folding.UNITS` (folding.py:137-138,193); E2.03/E2.10 declared in `story/data/signatures/second_pass.json` | docking any of the above |

Tissue surface tensions are measured quantities (Foty & Steinberg's differential-
adhesion programme measured them for cell aggregates, mN/m scale). Whether a
*macroscopic* bone/muscle/skin mapping exists is an open research question — the
control run is designed to answer exactly that, and F2 is the falsifier if the answer
is no. The world-material path is on FIRMER ground than the tissue path: cohesion and
grain size are already researched in the library, and the sand/rock/medium prediction
(P2) needs nothing new.

---

## THE PHASES (each one falsifiable, each one small)

**Phase 0 — THE THEORY.** This file. Operator rules on it before anything is built.

**Phase 1 — THE INSTRUMENT.** ✅ DONE (2026-08-03) — and its falsifier fired on first use,
which is the instrument working, not the phase failing. Built in `Chimera/core/matter_gpu.py`:
per-pass on-device Hamiltonian (`_energy_partial`/`_energy_fold`, interface + area term, the
flip kernel's own conventions, zero syncs in the pass loop, one readback of the trace) and
the persistent lattice (`open_lattice/step/close`). Under test:
`Chimera/tests/test_matter_gpu_energy.py` — the trace matches the CPU-computed Hamiltonian
of the same grid to 0.0000%, and the λ=0 trace is monotone (0 of 238 sign flips).

**THE VERDICT THE PHASE EXISTS TO PRODUCE.** The rung-1 control's trace is non-monotone and
never plateaus (n=48, n=64, n=96; temp=12, λ=0.9). The cause is measured, not guessed:
the interface dynamics minimize exactly (λ=0: H falls 1.13M → 226k, monotone), the believed
area counts track the true counts exactly, and the CPU serial model with identical J/temp/λ
holds areas to 0.5% with H falling 1.16M → 711k. The divergence is the PARALLEL AREA UPDATE:
pass-start counts mean every flipping cell in a color pass acts on the same stale deficit,
the restoring kick at a ~800-cell deficit is ~1600× the interface scale, and each pass slams
the populations past target — a bang-bang controller with unit delay (skin drained 14% at
n=48/30 sweeps while its believed restoring force was maximal). **Consequence, published per Rule 17:** `parity_report`'s SORTED check was False at
n=96/90 sweeps even for differential J under the frozen-count scheme — and the
docstring's "standard parallel-Potts, converges" claim was falsified. The prerequisite
membrane (the parallel area update) is RESOLVED below: read-live + commit-on-acceptance,
H falls and plateaus, parity sorts, areas hold at the CPU's offset.

**Phase 2 — THE CONTROL.** Research the tissue surface tensions; derive the 5×5 J for
bone/muscle/skin/tendon/medium through the mapping above; run the rung-1 scramble;
read τ_sort and the anatomy off the trace. F1, F2, F3 all live here. This is the run
the theory can lose.

**THE DERIVATION (membrane stated 2026-08-03, before the run; code: `Chimera/core/matter_derive.py`).**

*THE MEASUREMENTS (research first, derive second):*

- Foty, Pfleger, Forgacs & Steinberg 1996, *Development* 122:1611–1620 — chick
  embryonic tissue surface tensions by parallel-plate compression, dyne/cm (= mN/m):
  **limb bud mesoderm 20.1 · retinal pigmented epithelium 12.6 · heart 8.5 ·
  liver 4.6 · neural retina 1.6.** Mutual envelopment follows the tension order
  exactly (every lower-tension tissue envelops every higher one).
- Foty & Steinberg 2005, *Dev. Biol.* 278:255 — aggregate surface tension is a direct
  linear function of cadherin expression (R²=0.9965) with a **zero-cadherin intercept
  of 0.32 mN/m**: the adhesion-independent cortical floor.
- Tissue–tissue **interfacial** tensions: NOT systematically measured (stated outright
  by Pajic-Lijaković et al. 2023, *Soft Matter* review). A named gap — the
  Girifalco-Good default below carries it, stated as an assumption.

*THE TYPE MAPPING (an assumption someone can disagree with; F2 is its judge):*

- **BONE ← limb bud mesoderm (20.1)** — the mesenchymal core of the limb, the deepest
  tissue in both the measured hierarchy and rung-1.
- **MUSCLE ← heart (8.5)** — heart is muscle; the one-to-one case.
- **SKIN ← neural retina (1.6)** — the universal enveloper, the lowest measured
  tension, as rung-1's skin is the lowest.
- **TENDON ← retinal pigmented epithelium (12.6)** — the second-deepest measured
  tissue, exactly where rung-1's tendon sits (γ=13.5, between bone 15 and muscle 9).

**F2's VERDICT IS ANALYTIC (no run needed).** The measured ordering
bone(20.1) > tendon(12.6) > muscle(8.5) > skin(1.6) reproduces rung-1's burial order
15 > 13.5 > 9 > 2 in rank and nearly in ratio (bone/muscle 2.36 vs 1.67; tendon/muscle
1.48 vs 1.50; skin/muscle 0.19 vs 0.22). **F2 PASSES before the run** — reality's
ordering is rung-1's ordering.

*THE INTERFACIAL DEFAULT.* For pairs never measured, Girifalco-Good:
`γ_ab = (√σ_a − √σ_b)²` (work of adhesion W_ab = 2√(σ_a·σ_b), the standard estimate
for mutually wetting phases — and these tissues wet each other completely; their
envelopment is total). Stated as an assumption, replaceable the day Foty-1994-class
interfacial numbers are on disk.

*THE SCALE (the one kinetic freedom; F3 guards it).*

- ℓ = 10 µm — one lattice site is one cell.
- kT_eff = σ_cortex·ℓ², with σ_cortex = 0.32 mN/m the measured adhesion-independent
  tension floor. The statement: a cell's fluctuation energy over one contact area
  equals its non-adhesive cortical tension over that area. kT_eff = 3.2×10⁻¹⁴ J.
- temp = 12 → E₀ = kT_eff/12 = 2.67×10⁻¹⁵ J → **α = ℓ²/E₀ = 3.75×10⁴ J⁻¹·m²**
  (37.5 lattice units per mN/m). One constant serves α and temp both, as the theory
  requires.

*THE DERIVED J.* `J(a,a) = α·σ_a` · `J(a,MED) = α·σ_a + J(a,a)/2` ·
`J(a,b) = α·γ_ab^GG + (J(a,a)+J(b,b))/2`. Numbers printed by `matter_derive.py` at
run time — computed, never hand-copied. λ = 0.9 unchanged: the area physics is the
same protocol, and λ's own derivation (bulk modulus over E₀) is a named later
membrane, not smuggled into this one.

*PREDICTIONS (before the run):*

1. **F1 holds.** The derived J sorts the rung-1 scramble bone < muscle < skin, the
   uniform control does not. The engulfment inequality holds analytically:
   γ_BS = 10.36 ≥ γ_BM + γ_MS = 5.18 mN/m — muscle fully wets bone away from skin.
2. **F3 fires.** The derived J/temp ratios are 5–94 against rung-1's 0.17–1.33 — the
   derived system runs ~50× colder. Uphill moves are Boltzmann-forbidden, so sorting
   must proceed on strictly-downhill marginals: predict τ_sort(derived) > 2×
   τ_sort(rung-1). The disagreement to publish (Rule 17): kT_eff is NOT the passive
   cortical floor — living-cell rearrangement rides active fluctuations ~35× larger
   (rung-1's hand-fit implicitly assumed kT_eff = 12·(8.5×10⁻¹³/9) = 1.1×10⁻¹² J).
   The ratio structure survives; the cortical anchor does not. If instead τ_sort
   lands within 2×, the anchor stands and rung-1's scale is explained, not fitted.

*VERDICT (2026-08-03, all numbers measured; `cd Chimera && python -m core.matter_derive`).*
**F1 PASS · F2 PASS · F3 FIRED.**

- **F1 — PASS.** The derived J sorts the rung-1 scramble: bone 15.0 < muscle 17.1 <
  skin 23.3 (uniform contrast: 24.1/18.8/20.0, unordered). The anatomy the theory
  promised from measured tensions alone is the anatomy the lattice grows.
- **F2 — PASS (analytic).** Measured ordering bone(20.1) > tendon(12.6) > muscle(8.5)
  > skin(1.6) = rung-1's burial order, in rank and near-ratio.
- **F3 — FIRED.** τ_sort(derived) = 3 sweeps, τ_sort(rung-1) = 46; ratio 0.07,
  outside [0.5, 2]. **And the membrane's prediction missed the DIRECTION** — recorded,
  not reconciled (Rule 17). The cold system was predicted to sort slower; it sorts
  ~15× faster. The physics of the miss: at J/temp ~ 5–94 every downhill flip removes
  hundreds of lattice units, so the quench anneal crashes H to (1−1/e) of its drop in
  3 sweeps; rung-1's warm dynamics (J/temp ~ 0.2–1.3) relaxes the same FRACTION
  (23.5% vs 27.2% total drop — nearly equal) over 46 sweeps of small Boltzmann
  acceptances. The scale constant is therefore not a scale constant: the
  cortical-anchored α reproduces rung-1's STRUCTURE but not its KINETICS, exactly the
  condition F3 exists to catch. The published disagreement: rung-1's hand-fit
  implicitly assumed kT_eff = 12·(8.5×10⁻¹³/9) = 1.1×10⁻¹² J ≈ **35× the passive
  cortical floor** — living-cell rearrangement rides active fluctuations, not the
  adhesion-independent baseline. Named instrument caveat, honest about what τ measured:
  in the cold system the (1−1/e) point of the H trace is the quench crash, not the
  coarsening tail, so F3's comparison is partly quench-rate vs coarsening-rate — the
  falsifier fired on its own terms, and the reading is published with it.
- **What survives and what dies.** The derivation's content — J's RATIO structure
  projected from measured tissue tensions through the exact CPM algebra with the
  Girifalco-Good interfacial default — reproduces the anatomy from literature data
  alone (F1+F2). What dies is the cortical floor as kT_eff. The next membrane
  (Phase 2b, stated when built): the self-consistent LIQUIDITY anchor,
  kT_eff ~ γ·ℓ² — an aggregate is liquid precisely because its fluctuation energy is
  comparable to its bond energy — which places the derived scale at α ≈ 1.4 per mN/m,
  rung-1's own neighborhood, and must then pass F3 or die the same way.

The 5×5 derived J (lattice units, α = 37.5 per mN/m) is computed by
`matter_derive.py` at run time: MED row [0, 1130.6, 478.1, 90.0, 708.8],
diagonals [0, 753.8, 318.8, 60.0, 472.5], off-diagonals B–M 628.4, B–S 795.3,
B–T 645.8, M–S 291.5, M–T 410.7, S–T 462.0. γ_CPM against medium reproduces the
measured tensions by construction (753.8 = 37.5 × 20.1, etc.).

**Phase 2b — THE LIQUIDITY ANCHOR (membrane stated 2026-08-03, before the run).**

**STATEMENT.** The one kinetic freedom closes without a fit. Phase 2's cortical
anchor died because it anchored the fluctuation energy to the PASSIVE floor — but
Foty's aggregates round up, sort, and envelop in hours: they are LIQUIDS, and a
liquid is liquid precisely because its fluctuation energy per contact is comparable
to its bond energy per contact. So: **kT_eff = σ̄·ℓ²**, where σ̄ is the geometric
mean of the four measured tissue tensions — (20.1·12.6·8.5·1.6)^¼ = **7.66 mN/m** —
the scale-invariant midpoint of the measured cohesion spectrum (the tensions span
12.6×; the geometric mean is the only central value that does not pick a tissue).
Someone can disagree: the geometric mean may not be the operating point — the
self-consistency could live at the median tissue, or outside the spectrum entirely.
F3 judges.

With temp = 12: E₀ = σ̄·ℓ²/12 = 6.38×10⁻¹⁴ J, **α = 1.566 per mN/m** — and the
derived J lands at 1.5–3× rung-1's scale everywhere (J(B,MED) 47.2 vs 16;
J(M,MED) 20.0 vs 11; J(S,MED) 3.8 vs 5). Which is the closure statement this phase
exists to test: **rung-1's hand-fit was sitting at ~1.5× the liquidity anchor all
along** (its implied kT_eff = 1.13×10⁻¹² J vs the anchor's 7.66×10⁻¹³ J — a factor
of 1.5, inside F3's band). If the anchor is right, the theory's claim — "J is fixed
by measurements up to ONE scale constant" — closes with ZERO fitted numbers: ratios
from Foty 1996, interfacial default from Girifalco-Good, scale from the liquidity
condition, every input a measurement or a named assumption.

**PREDICTION (not yet measured).** F1 still passes (anatomy is ratio-structure,
scale-invariant — the Phase-2 run already proved the structure sorts), and **F3
PASSES: τ_sort(derived-liquidity) lands within [0.5, 2]× τ_sort(rung-1).** The
derived J/temp ratios (0.3–3.9 against medium) bracket rung-1's (0.4–1.3) closely
enough that the kinetics should be the same kind, not the Phase-2 quench.

**FALSIFIER.** F3 fires again (τ ratio outside [0.5, 2]), or F1 breaks at the new
scale. Either kills the liquidity anchor: the scale is then NOT the geometric-mean
liquidity point, the disagreement is published per Rule 17, and the kinetic freedom
goes to the operator's third open ruling (derive vs train) as an honest unresolved.

*VERDICT (2026-08-03, all numbers measured;
`cd Chimera && python -m core.matter_derive --anchor liquidity`).*
**F1 PASS · F2 PASS · F3 PASS — the theory closes with zero fitted numbers.**

- **F1 — PASS.** The liquidity-scaled derived J sorts the scramble: bone 12.8 <
  muscle 21.2 < skin 26.8; the uniform contrast does not (26.0/17.3/19.6).
- **F2 — PASS (analytic, unchanged).** The measured ordering is the burial order.
- **F3 — PASS.** τ_sort(derived-liquidity) = 28 sweeps, τ_sort(rung-1) = 47;
  ratio **0.60**, inside [0.5, 2]. The derived system is mildly faster than rung-1,
  not identical — recorded, within the band the theory named. **Addendum (rerun
  spread, measured 2026-08-03 after the Phase-5 kernel change):** four independent
  runs give ratios 0.47 / 0.50 / 0.60 / 0.61 (derived τ 24–30, rung-1 τ 47–60) —
  the band edge is grazed by the scheduling nondeterminism this file publishes as
  a named cost, and the verdict is stable: derived kinetics are rung-1's kind,
  consistently ~0.8–2× faster, never the Phase-2 quench.
- **The closure.** Ratios from Foty 1996, interfacial default from Girifalco-Good,
  scale from the liquidity condition (σ̄ = 7.66 mN/m, the geometric mean — and note
  it lands within 11% of the heart/muscle value, so the anchor and the mapping agree
  on where the center of the spectrum is). Rung-1's hand-fit sat at 1.5× this anchor
  all along. The 15 free numbers of the 5×5 symmetric J are now: 4 measured tensions
  + 6 Girifalco-Good pair defaults + 4 diagonals by the exact algebra + 1 liquidity
  scale. Nothing was swept; nothing was fitted.
- **What remains honestly open.** (1) The type mapping is an assumption that passed
  its judge (F2) on ordering — it has NOT been tested on absolute envelopment
  behavior pair-by-pair. (2) The six interfacial pairs are Girifalco-Good defaults,
  not measurements — the day Foty-1994-class numbers are on disk, they replace the
  default and the matrix is recomputed. (3) λ = 0.9 is still underived (bulk modulus
  over E₀ — its own membrane, with `grown_arrangement.py`'s soft-λ tissue drain as
  its control case). (4) temp = 12 is the protocol's; E₀ derives from it, so the
  one constant serves both as required — but the degeneracy the theory named is
  real: γ/temp ratios are what the lattice reads.

The 5×5 derived J at the liquidity scale (lattice units, α = 1.566 per mN/m):
MED row [0, 47.23, 19.97, 3.76, 29.61], diagonals [0, 31.48, 13.31, 2.51, 19.74],
off-diagonals B–M 26.25, B–S 33.22, B–T 26.98, M–S 12.18, M–T 17.16, S–T 19.30.

**Phase 2-prerequisite — THE PARALLEL AREA UPDATE (a membrane, stated before the build).**

**STATEMENT.** The volume constraint's failure is not the constraint, it is the STALENESS:
a color pass evaluates ~N³/8 copy attempts against one frozen count vector, so every
attempt spends a marginal computed for a world the first accepted flip already
invalidated. The CPU model converges because each attempt sees the LIVE count
(`matter.py:440-451`, counts updated only on acceptance, sites visited in rng order).
The GPU can reproduce exactly those semantics — serial marginal, parallel geometry — by
CLAIMING the count atomically at evaluation time and rolling the claim back on
rejection. The frozen-count scheme cannot converge at any parameters where the
restoring kick λ(2D±1) exceeds temp (rung-1: 0.9·2·800 = 1440 ≫ 12): its per-pass
cohort overshoots the deficit whenever the eligible boundary exceeds the deficit —
which is always.

**PREDICTION (not yet measured).** With live-claim counts, at n=96, temp=12, λ=0.9,
90 sweeps: (1) the rung-1 trace is monotone-up-to-noise and plateaus — the same two
criteria the Phase-1 falsifier fired on; (2) the per-tissue area fluctuation at the
plateau is σ_a ≈ √(temp/2λ) = √(12/1.8) ≈ 2.6 cells — equipartition on the quadratic
area well, derived, not fitted — not the ±600–800 of the frozen scheme; (3) parity is
restored: differential sorts (bone < muscle < skin), uniform does not; (4) λ=0 stays
monotone (the instrument's regression check).

**FALSIFIER.** Any of (1)–(3) fails. If (2) lands far from √(temp/2λ) (>10×), the
phantom-claim window — a tentative claim visible to concurrent threads before its
rollback — is not negligible, the scheme is not serial-Metropolis, and the deterministic
alternative replaces it: z-slab sub-passes with a count fold per slab, K derived from
σ_a and the boundary measure.

**VERDICT (2026-08-03, all numbers measured).** Two schemes were built; the first killed
itself on this membrane's own falsifier.

1. **Claim-then-rollback** (atomic claim at evaluation, rollback on reject): exact serial
   marginal in theory, and the phantom-claim window was NOT negligible — tissue *grew*
   +200 cells/sweep where the CPU drains −25 and holds (checked to 90 sweeps), H rose
   9.4M → 16.0M. Rejected in-flight claims polluted every concurrent read. The
   falsifier's fallback clause fired.
2. **Read-live, commit-on-acceptance** (plain racy read, atomic claim only if the flip
   happens): the growth reversed immediately. At n=96/90 sweeps: **H falls
   8.87M → 6.51M, plateaus** (tail drift 1.19% of drop); **parity restored** —
   differential sorts (17.2/18.1/24.1 ordered), uniform does not (21.1/18.6/20.9);
   areas hold with means at the CPU's own small drain offset (−19/+29/−59) and the
   plateau area term is 0.15% of H. Both instrument tests pass (trace exact, λ=0
   monotone).

**Two predictions missed, and both misses are recorded rather than reconciled.**
(2) σ_a measured 100–152 cells vs the derived serial scale 2.58 — 50×: the parallel
pass keeps cohort-correlated wander (every cell in a pass still acts on pass-correlated
information); bounded, unbiased, and 5–8× tighter than the frozen scheme's bang-bang,
but it is NOT serial-Metropolis by that measure. Whether Phase 2 needs the last 50×
(the deterministic z-slab scheme remains the named route to it) is the operator's call
— it is instrument purity, a taste terminal. And the monotonicity bar itself: the
membrane's 1%-of-drop was an underived number, and the system falsified it twice —
first with its thermal scale (0.4–1.5% of the drop), then with the shape of the noise:
Boltzmann acceptance permits uphill excursions and domain coarsening makes them
correlated (measured: +131k at sweep 0→1, +129k at 14→15, recovered in 1–2 sweeps), so
ANY per-sweep rise bar fires on physics. What convicts a wrong kernel is a rise that
does not recover. The check in `__main__` is now sustained-rise only: a 10-sweep moving
average may never rise more than 3σ of the mean (thermal/√10). **FINAL VERDICT
(n=96, 200 sweeps): monotone True (6.1k vs 15.0k allowance), plateau True (1.31%),
SORTED True — PASS.** The check still catches both measured pathologies: the frozen
oscillation (±300k forever) and the claim-scheme growth (+6.6M sustained) are both
sustained.

**NAMED COST (the human's terminal).** Acceptance order becomes hardware scheduling
order instead of seeded rng order: one seed no longer gives bit-identical grids. The
CPU model's order is rng-driven (`matter.py:425`), so this is the same KIND of
nondeterminism without the seed. Every quantity this theory measures — plateau H,
σ_a, radius ordering, τ_sort — is order-independent.

**Phase 4 (first control) — THE WORLD: sand/rock/medium (membrane stated 2026-08-03, before the run).**

**STATEMENT.** The mapping that closed for tissue closes for the world with the same
algebra and no new freedoms. Every input is already researched in the library, or
cited below:

- **γ_sand = c·d = 0.5 kPa × 0.072 mm = 36 mN/m.** The granular surface-energy
  derivation: pulling apart a unit area of cohesive granular bed costs the cohesive
  stress (Mitchell 1972, library `cohesion_kpa`) working over one grain diameter
  (Carrier 2003 D50, library `grain_size_mm`) of separation. Someone can disagree:
  the work could act over a fraction of a grain, or several — the derivation claims
  one diameter is the scale, and the sort is the judge.
- **γ_rock = K_IC²/(2E) = (2.4 MPa√m)²/(2×78 GPa) = 36.9 J/m².** Griffith: the
  fracture surface energy from the measured basalt fracture toughness (K_IC 1.8–3.0
  MPa√m — Whittaker et al. 1992 / Zhang et al. 1998 / Demkowicz 2012 compilation)
  and the library's Young's modulus (Quaglio et al. 2020). Factor 2: a crack creates
  two surfaces.
- **ℓ = 0.072 mm** — one lattice site is one sand grain (the flowing phase sets the
  lattice constant, as the cell did for tissue).
- **The scale, same anchor as Phase 2b:** kT_eff = σ̄·ℓ² with σ̄ the geometric mean,
  √(36 mN/m × 36.9 J/m²) = 1.15 J/m² → α = 10.4 J⁻¹·m².

**The honest structural observation (stated, not hidden).** γ_rock/γ_sand ≈ 1000×.
No single temperature keeps both phases liquid — the geometric-mean anchor puts rock
at J/temp ~ 32–48 (the quench regime, Phase 2's cold world) and sand at J/temp ~
0.03–0.05 (hot, near-gas). That is not a defect of the derivation; it is the physics
of a 1000× cohesion spread, and it makes the anatomy prediction STRONGER, not
weaker: the spreading coefficient for sand between rock and medium is analytic —
S = γ(r,MED) − γ(s,MED) − γ(s,r) = 576 − 0.56 − 552 = +23 (lattice units) > 0 — so
sand must wet the rock core completely. What the spread costs is sand's SHARPNESS:
hot sand will envelop diffusely, not as a crisp shell.

**PREDICTION (not yet measured).** The theory's P2: a three-material scramble of
sand/rock/medium (n=96, temp=12, λ=0.9, targets = initial counts — the rung-1
protocol unchanged) sorts with **rock burial** (rock mean radius < sand mean radius)
under the derived J, and does NOT sort under the uniform contrast. Rock forms its
core fast (quench); sand envelops diffusely.

**FALSIFIER.** The sort inverts (sand core / rock shell) or fails to layer under the
derived J — then the granular γ = c·d derivation, or the Griffith docking of rock,
is wrong, and the disagreement is published per Rule 17. The trace is recorded for
the ledger but carries no τ bar this run: Phase 2/2b already taught that τ off the H
trace compares quench rates when the two regimes differ, and here they differ by
design.

*VERDICT (2026-08-03, all numbers measured; `cd Chimera && python -m core.matter_derive --world`).*
**PASS — and the contrast is honest.** Three runs (scheduling-nondeterministic, so
each is an independent draw):

| run | derived J: rock / sand radius | uniform: rock / sand |
|---|---|---|
| 1 | **16.1** / 23.3 | 18.5 / 23.1 (rock in) |
| 2 | **16.5** / 23.3 | 20.8 / 21.3 (tied) |
| 3 | **16.0** / 23.1 | 21.8 / 19.5 (sand in) |

The derived J buries rock every time (gap ≈ 7.1, consistent). The uniform control's
interior phase flips run to run — rock, tie, sand — which is exactly what a
symmetric J must do: the phases coarsen (uniform γ(sand,rock) = 4 ≠ 0, so the
control separates), but the ORIENTATION is random symmetry-breaking. The machine
does not manufacture the predicted ordering on its own; the derivation does. The
granular γ = c·d docking for sand and the Griffith K_IC²/2E docking for rock
survive their first control. Trace for the ledger: H 4.27×10⁸ → 2.51×10⁸ over 200
sweeps (no τ bar — the quench regime was the design, and Phase 2 already taught
what τ reads there). The spreading coefficient S = +23.25 predicted complete
wetting analytically; the burial is the wetting, seen from the radius side.

**Phase 3 — FRACTURE AND DEATH (membrane stated 2026-08-03, before the build).**

**Housekeeping first — the prerequisites are DONE, found done:** `folding.UNITS`
carries `N/m`, `J/m2`, and `Pa.m0.5` (folding.py:137-138,193), and E2.03 (Griffith,
a_crit) and E2.10 (Young-Laplace) are DECLARED in
`story/data/signatures/second_pass.json` (2026-08-01). The measurements table's
"units missing" row is stale and is corrected in this edit.

**STATEMENT.** Fracture is Griffith applied to the lattice's own bond bookkeeping,
and it needs no accumulated-stress state at all. Converting a cell of type t to
MEDIUM **releases** the tissue–tissue tension it carries and **costs** fresh crack
surface against the same-type neighbors that still hold it:

```
E_release = Σ_{nb ≠ t, nb ≠ MEDIUM} γ_CPM(t, nb)      (the bonds that can PULL —
            tissue–tissue tension only; the void cannot pull, so tissue–medium
            surface energy is excluded — a free surface is not stress)
E_cost    = n_same · α · γ_f(t)                       (the fresh crack faces,
            γ_f = K_IC²/(2E), measured)
RUPTURE when E_release > E_cost  →  the cell becomes MEDIUM. Death.
```

Consequences that make it physics rather than a script: a bulk cell (n_same = 18,
E_release = 0) can NEVER rupture — perfect bulk does not nucleate cracks, fracture
starts at surfaces and flaws, which is true. A cell dies exactly when the
surrounding tissue pulls on it harder than its remaining same-type support holds it
— protrusions neck off, isolated grains suffer attrition, inclusions are crushed
out. And because both sides scale with α, the criterion is temp-invariant; what
temp changes is the ESCAPE rate (accepted flips let a misplaced cell move home
before the rupture pass catches it) — so brittleness becomes a dynamical, measured
property instead of a parameter. γ_f per material: rock = 36.9 J/m² (basalt K_IC,
researched); sand = its decohesion energy c·d = 36 mN/m (a granular material has no
fracture toughness — it comes apart at its own surface energy); tissue values are
researched in Phase 3d below: bone Griffith-legal, muscle/skin at their measured
tearing energies, tendon open.

**PREDICTIONS (not yet measured).** World scramble (Phase 4's sand/rock/medium,
200 sweeps, λ=0.9), rupture pass after each sweep:

1. **Death of the misplaced, survival of the sorted.** Ruptures concentrate at
   tissue–tissue interfaces with thin same-type support: isolated rock grains in
   the sand matrix die first (attrition), sand inclusions embedded in rock are
   crushed out, and the sorted rock core is IMMORTAL (its surface touches medium,
   which cannot pull). The Phase-4 burial still forms; debris (new MEDIUM voids)
   marks where the misplaced died.
2. **The brittle–ductile contrast, emergent.** Rupture count at 200 sweeps decreases
   MONOTONICALLY with temp across the named set {1.2, 12, 120}: cold = no escapes =
   everything misplaced dies; hot = plastic escape wins = cells move home instead of
   dying. Three named runs, one question (does temp set brittleness?) — not a sweep.
3. **Instrument self-check.** ZERO ruptures with n_same ≥ 15 (near-bulk). The rule
   makes bulk rupture arithmetically impossible; one observed bulk nucleation means
   the kernel is not running this membrane.

**FALSIFIERS.** Any of: (A) a bulk nucleation (prediction 3 fires — kernel or rule
wrong); (B) the temp ordering is not monotone decreasing (the brittleness claim
dies — escape is not the mechanism); (C) no ruptures at all at temp=1.2 despite
isolated grains existing (the rule is not wired). Any one publishes the
disagreement per Rule 17.

*VERDICT (2026-08-03, run: `cd Chimera && python -m core.matter_derive --fracture`).*
**FIRED — BOTH FALSIFIERS, AND THE DIAGNOSIS IS MEASURED, NOT GUESSED.**

| temp | ruptures | bulk violations (n_same ≥ 15) | voids | radii rock / sand |
|---|---|---|---|---|
| 1.2 | 133,365 | 1,704 | +250 | 15.1 / 36.0 |
| 12 | 125,636 | 8,555 | +2,028 | 16.5 / 33.4 |
| 120 | 231,216 | 15,604 | +19,875 | 14.9 / 34.6 |

- **FALSIFIER A FIRED — and the mechanism convicts the membrane, not the kernel.**
  The "impossible" bulk ruptures are SAND: sand's support is wcrit = α·0.036 ≈ 0.4
  lattice units per same-type face, so a sand cell with 15 sand neighbors and 3 rock
  neighbors carries 3 × 360.7 ≈ 1,082 against support 5.6 — crushed, arithmetically
  legal, and PHYSICALLY WRONG. A sand grain pinned between rocks under agitation
  does not convert to void; it gets squeezed out and MOVES. The membrane's error:
  "decohesion at its own surface energy" was implemented as death-to-MEDIUM, but
  decohesion for a granular material is rearrangement, not annihilation. Granular
  materials do not fracture — there is no K_IC for sand, and the rule had no business
  letting sand die.
- **FALSIFIER B FIRED — INVERTED, and the inversion convicts the prediction's
  premise.** Ruptures INCREASE with temp (126k → 231k from 12 to 120). The
  brittle–ductile claim assumed temp sets the escape rate — but under the liquidity
  anchor α = temp/σ̄, J scales WITH temp, so dH_interface/temp is temp-INVARIANT and
  the escape physics does not change at all. What changes is λ/temp: at temp=120 the
  area constraint is 10× weaker against the bath, populations wander, and more
  misplaced tissue is exposed to the rupture pass (voids +19,875 vs +250). The only
  thermal knob in this Hamiltonian is the AREA term's strength — a named debt (λ is
  underived) now measured to be load-bearing for life-and-death questions.
- **What survives:** the burial forms under rupture at every temp (rock 14.9–16.5
  buried, sand 33–36) — death does not prevent sorting. First ruptures at sweep 1:
  the scramble's misplaced cells die immediately, as predicted.
- **Published per Rule 17.** The Phase-3 membrane as stated is dead. Phase 3b below
  is its replacement, stated with the measured diagnosis in hand.

**Phase 3b — FRACTURE, SECOND MEMBRANE (stated 2026-08-03, before the run).**

**STATEMENT.** Fracture is reserved for materials that POSSESS fracture toughness.
Rock ruptures by the Phase-3 criterion (carried tissue–tissue tension > n_same·α·γ_f,
γ_f = K_IC²/2E = 36.9 J/m², measured). Sand NEVER ruptures — a granular material has
no K_IC; carried tension on a sand grain dissipates by rearrangement (the flip
dynamics, already in the machine), not by annihilation. wcrit(sand) is therefore not
a small number, it is NO number: sand is un-fracturable.

**PREDICTIONS (not yet measured).** Same world scramble, 200 sweeps, temp=12 only
(the temp contrast is dead with the escape premise; λ/temp is a separate named
membrane):

1. **Ruptures are 100% rock.** Zero sand deaths (the per-type log proves it).
2. **Zero bulk violations** — now a meaningful check: with sand un-fracturable, a
   rock cell with n_same ≥ 15 needs carried > 5,770 against a maximum possible
   3 × 360.7 = 1,082. One violation = kernel wrong.
3. **Death of the misplaced, then PEACE.** The rupture curve decays: the first 20
   sweeps kill the scramble's isolated grains (attrition), and the last 20 sweeps
   are near-zero — the sorted state is STABLE under fracture, because the core's
   surface touches medium and the void cannot pull. Falsifier C: last-20-sweep
   ruptures ≥ first-20 (no decay → the sorted state is not stable; death is not
   "of the misplaced").
4. **The burial persists** (rock radius < sand radius at 200 sweeps) with voids
   marking where the misplaced died.

**FALSIFIERS.** (A) any bulk violation; (B) any sand death; (C) no decay in the
rupture curve. Any one kills this membrane too.

*VERDICT (2026-08-03, two runs: 3b as stated, then 3c with void-connectivity —
each falsifier taught one thing, and both teachings are in the final rule).*

**Run 3b (as stated): FIRED — falsifier B.** Rock-only fracture worked exactly as
membraned: **A PASS** (0 bulk violations — with sand out, the arithmetic bound is
real), **C PASS** (31,215 ruptures in the first 20 sweeps → 30 in the last 20: death
of the misplaced, then peace — the sorted state is stable), burial persists
(rock 16.1 < sand 22.8). But **B FIRED: 252 sand deaths** (0.74%) despite
wcrit(sand) = 10³⁰. Mechanism measured, not guessed: the n_same = 0 clause sets the
threshold to zero for ANY fully-isolated cell — so isolated sand grains embedded in
rock were annihilated into voids **inside solid tissue**, where a void has nowhere
to go. Unphysical on its face, and the falsifier caught it.

**Run 3c (the fix the firing named): void-connectivity.** One condition, derived not
tuned: a rupture CREATES a void, so a cell may only die if it touches MEDIUM (or an
existing rupture) — **cracks advance from surfaces**. Measured: ruptures 34,064 →
**7,953** (−77%), bulk violations 0 (A PASS), decay 7,293 → 5 (C PASS), burial
persists (rock 16.2 < sand 22.5), sand deaths 252 → **13** — and B, read literally
("zero sand deaths"), **FIRES again at 0.16%**. Published per Rule 17, with the
mechanism fully identified: the 13 are **PLUCKING, not fracture** — the n_same = 0 +
void-contact clause (a cell with zero same-type support, touched by the void, has no
cohesion holding it at all) applies to every material, K_IC or none. That clause is
erosion, and erosion is real physics the membrane conflated with fracture.

**THE RULE THAT SURVIVES (3c-final), three clauses, every one earned by a firing:**

1. **FRACTURE** needs fracture toughness: only materials with a measured K_IC can
   rupture (rock: γ_f = K_IC²/2E = 36.9 J/m²; sand: no K_IC exists → un-fracturable;
   tissue: Phase 3d — bone 124–735 J/m² Griffith-legal, muscle 2,500 and skin
   20,000 J/m² apparent, tendon open). Criterion: carried tissue–tissue tension >
   n_same·α·γ_f — the void cannot pull, so tissue–medium surface energy never
   counts as stress, and perfect bulk (carried = 0) never nucleates.
2. **VOID-CONNECTIVITY**: rupture creates a void, so only void-touching cells can
   die. Cracks advance from surfaces and existing cracks; solid tissue does not
   spontaneously hole. Isolated inclusions PERSIST (a rock pebble in the sand
   shaker stays a rock pebble) until the void reaches them.
3. **PLUCKING** (erosion, distinct from fracture): a cell with ZERO same-type
   support that touches the void dies regardless of material — measured rate at
   n=96/200 sweeps: 13 sand + the isolated-rock share of 7,940 rock deaths. No
   K_IC required; no cohesion exists to require one.

**Named race, honestly recorded:** the 13 sand plucks are cells isolated
mid-sweep by their neighbors' flips and caught by the rupture pass before the next
sweep could assimilate them (assimilation is downhill: an isolated sand-in-rock
cell becomes rock at dH ≈ −3,037 and is accepted near-certainly when attempted).
The flip schedule and the rupture schedule race; the residual is 0.16%. Whether
the last 13 are physics (plucking IS stochastic) or schedule artifact is the
operator's call — it is instrument purity, a taste terminal, same class as Phase
1's σ_a question.

**The net ledger of Phase 3:** fracture is IN the shaker, derived from K_IC with
zero fitted numbers, stable (the sorted anatomy persists and the rupture curve
decays to ~nothing), and three physical clauses deep — each one earned by a
falsifier firing on real behavior. The λ/temp confound from Phase 3's first run
(hot = weak area constraint = more death) stands as the measured proof that λ's
derivation is load-bearing for life-and-death questions — the next membrane after
the operator picks the rung.

**Phase 3d — TISSUE K_IC: THE RESEARCH THE FRACTURE RULE WAS WAITING FOR (closed 2026-08-03).**

Clause 1 of the 3c-final rule reserves rupture for materials with a measured
fracture toughness, and left the four tissue types docked at nothing. The
research is now done, and the honest finding is that "tissue K_IC" is TWO
different physical objects the membrane must not conflate:

**BONE — Griffith-legal.** Human cortical bone has a measured crack-initiation
toughness K₀ = 2.03–2.06 MPa√m (Nalla, Kinney & Ritchie 2003, hydrated,
longitudinal) rising on an R-curve to ~5+ MPa√m with crack extension — bone
toughens AS it cracks (crack deflection, microcracking, collagen bridging).
With E ≈ 17 GPa (human cortical, longitudinal):

```
γ_init   = K₀²/(2E) = (2.05 MPa√m)²/(2·17 GPa) ≈ 124 J/m²
γ_growth = (5 MPa√m)²/(2·17 GPa)               ≈ 735 J/m²
```

The R-curve means bone has no single γ_f: 124 J/m² for nucleation questions,
up to ~735 for propagation. Stated as a band, not a point — using the growth
value for nucleation would overstate the crack-start cost 6×.

**MUSCLE and SKIN — no K_IC exists; the measured quantity is TEARING ENERGY.**
Like sand, soft tissue is not a Griffith material — but unlike sand it does
not rearrange either: it TEARS, and the tearing energy is measured:

```
muscle:  2.49 kJ/m²  (Taylor et al. 2012, porcine, apparent tearing energy)
skin:   ~20   kJ/m²  (Vincent, Structural Biomaterials, Springer compilation)
tendon:   band OPEN — the compilations imply high but no defensible single
          number survives; tendon stays un-fracturable in the shaker until
          its band closes. Not guessed (rule 20).
```

**The honesty the metal row already taught.** Tearing energy is APPARENT —
true surface energy plus the viscoelastic and plastic dissipation of the
process zone, typically 10–100× the Griffith term for soft matter. Docking
γ_f = tearing energy is therefore a modeling claim, not a measurement:
someone can disagree — the dissipation belongs to the bulk, not the surface,
and a membrane that counts it as surface energy will over-resist rupture
wherever the process zone is wide. The claim is docked because the 3c-final
criterion only needs THE ENERGY A CRACK COSTS, and on that question the
tearing energy is the measured answer.

**The ordering that falls out:** skin (20,000) ≫ muscle (2,500) > bone
(124–735) J/m². The skeleton is the most FRACTURABLE tissue in the body and
the envelope the least — which is the anatomy: bones break while skin
stretches. The derived rule reproduces it with zero fitted numbers.

**PREDICTION (not yet measured).** A tissue scramble (bone/muscle/skin, the
rung-1 protocol, rupture pass per sweep, 3c-final clauses) under these γ_f
dies in the derived order: misplaced BONE inclusions rupture first, muscle
second, skin last — skin's misplaced cells survive where bone's cannot.

**FALSIFIER.** The scramble's rupture ordering inverts (skin dies before
bone) — then the apparent-energy docking is wrong, the dissipation is not
countable as surface energy, and soft tissue needs its own clause, published
per Rule 17.

**Phase 5 — THE λ MEMBRANE (stated 2026-08-03, before the run).**

**STATEMENT.** The theory file's mapping says λ is bulk incompressibility: the area
term λ(A−T)² IS the elastic energy (K/2)Vε² of compressing a tissue, read in lattice
units. Exact algebra: with V = T·ℓ³ and ε = (A−T)/T, the flip marginal
U(A±1)−U(A) = (K·ℓ³/2T)·(±2D+1)/E₀ — so **λ_t = K_t·ℓ³/(2·T_t·E₀)**. Every input is
measured or already derived: K_soft = 2.3 GPa (soft tissue is water-like —
sonographic/poroelastic literature: fluid bulk modulus 2,300 MPa across tissue
tables; the soft-tissue bulk literature is thin and says so, d-nb.info §5.2.6),
K_bone = 13.9 GPa (cortical bone, E = 17 GPa, ν = 0.3 → grain bulk 13,920 MPa —
Frontiers Bioeng. 2022 table, consistent with the library's E = 18 GPa),
E₀ = 6.38×10⁻¹⁴ J (the liquidity anchor), ℓ = 10 µm, T ≈ 46k cells per tissue
(n=96 scramble). **Derived: λ_soft ≈ 392, λ_bone ≈ 2,368 — 400–2,600× rung-1's
hand-set 0.9.**

Someone can disagree — in fact the membrane disagrees with itself, and says why:
the per-type area term may be MASS CONSERVATION (a chemical potential on tissue
population), not elasticity (a constitutive law on continuum strain). The run
decides which.

**PREDICTION (not yet measured).** If the area term IS bulk elasticity, the derived
λ applies — and then the lattice must FREEZE: at zero deficit every flip costs
dH_area = λ_a + λ_b ≈ 800–2,800 lattice units ≈ 67–233 kT_eff, acceptance ~e⁻⁶⁷,
no deficits ever develop, and the scramble cannot sort. Concretely, with the derived
per-tissue λ, 200 sweeps: radii stay scrambled (no bone<muscle<skin ordering),
counts frozen exactly, H flat. The one corridor that could save the mapping: flips
from overpopulated to underpopulated tissue are area-downhill — but at D = 0
everywhere (targets = initial counts), no corridor opens.

**FALSIFIER — inverted, on purpose.** The naive mapping SURVIVES only if the run
sorts anyway (a corridor the analysis missed). If it freezes, the mapping "per-type
area term = continuum bulk modulus" is DEAD, and what survives is published instead:
(1) the per-type λ is mass conservation, not elasticity; (2) rung-1's λ = 0.9 is
itself a measured effective modulus — K_eff = 2λT·E₀/ℓ³ ≈ **5 MPa**, 400× softer
than real soft tissue: the shaker's operating point is foam-like, a property of the
machine, now measured rather than assumed; (3) the per-CELL volume elasticity of
classic CPM is degenerate in this lattice (one site = one cell, volume fixed) —
stated so no later membrane re-derives it.

*VERDICT (2026-08-03, run: `cd Chimera && python -m core.matter_derive --lambda`).*
**THE MAPPING IS DEAD — the lattice froze, as the membrane predicted, and the one
surprise is explained rather than reconciled.**

Derived λ: bone 2,375 · muscle 395 · skin 395 (rung-1's hand value: 0.9). Measured
at 200 sweeps:

- **No sort.** Radii 21.0 / 18.2 / 18.4 — scrambled, exactly the freeze prediction.
  At λ ≈ 400–2,400 every zero-deficit flip costs λ_a + λ_b ≈ 67–233 kT_eff; the
  interface dynamics never starts, so no deficit corridor ever opens.
- **Counts nearly frozen:** drift +52 / −122 / +15 cells (±0.3%) in 200 sweeps —
  vs the λ = 0.9 machine's ±100–800 wander. The population jail works; it is the
  ONLY thing that works.
- **The surprise: H ROSE 27.1M → 64.5M.** Not anti-Metropolis physics — the trace
  is reporting what the Hamiltonian became: thermal noise still jiggles counts by
  ±tens, and at λ ≈ 2,375 a 52-cell excursion costs λ·D² ≈ 6.4M lattice units.
  The area term dominates H; the machine stopped being an interface-energy
  minimizer and became a population jail. The membrane's flat-H branch was
  wrong-headed; the rise is the freeze's signature, and it is recorded, not
  smoothed over.
- **τ_sort: undefined** (no drop to read) — the control's own way of saying the
  dynamics never ran.

**What survives, published per Rule 17:**

1. **The per-type area term is MASS CONSERVATION, not bulk elasticity.** The
   naive mapping λ_t = K_t·ℓ³/(2·T_t·E₀) is refuted by its own prediction.
2. **Rung-1's λ = 0.9 is now a MEASURED effective modulus:** K_eff =
   2λT·E₀/ℓ³ = **5.3 MPa** — 400× softer than real soft tissue. The shaker's
   operating point is foam-like, and that is now a measured property of the
   machine instead of an assumption.
3. **Real-tissue incompressibility cannot be imposed at the population level in
   this lattice.** The per-CELL volume elasticity of classic CPM is degenerate
   here (one site = one cell, volume fixed). The named routes if tissue-real K is
   ever needed: deficit-paired two-cell swap moves (a new kernel — volume-neutral
   by construction, the corridor the freeze never opened), or accept the foam
   regime as the machine's documented operating point. Both are the operator's
   call; neither is smuggled into this verdict.

**Phase 4 (full families) — THE WORLD, ALL FAMILIES (membrane stated 2026-08-03,
before the run).**

**STATEMENT.** The mapping closes for every world material the story has named with
a physical referent — sand, rock, ice, metal, basin — with the SAME algebra and the
SAME anchor as the tissue J and the sand/rock control. Every surface energy is
measured or Griffith-derived; the liquidity anchor recomputes as the five-way
geometric mean; no new freedom enters:

- **sand** γ = c·d = 0.5 kPa × 0.072 mm = **0.036 J/m²** (Mitchell 1972 cohesion ×
  Carrier 2003 D50 — the Phase 4 first control's value, unchanged).
- **rock** γ = K_IC²/(2E) = (2.4 MPa√m)²/(2×78 GPa) = **36.92 J/m²** (basalt K_IC
  1.8–3.0 — Whittaker 1992 / Zhang 1998 / Demkowicz 2012; E — Quaglio 2020).
- **ice** γ = K_IC²/(2E) = (115 kPa√m)²/(2×9 GPa) = **0.735 J/m²** (freshwater ice
  K_IC 100–130 kPa√m — Dempsey's 50–130 band, atmospheric 111, Timco & Frederking
  ~100–108; 115 is mid-band; E = 9 GPa library).
- **metal** γ = K_IC²/(2E) = (29 MPa√m)²/(2×69 GPa) = **6,094 J/m²** (Al 6061-T6
  K_IC ≈ 29 MPa√m literature consensus, Hellier measured 26.8; E = 69 GPa library).
  Honest note: for a ductile alloy this is a TEARING energy — it includes plastic
  work, so it overstates the surface term by orders. The mapping is told the truth
  about which number it is eating.
- **basin** γ = c·d = 0.2 kPa × 0.028 mm = **0.0056 J/m²** (soft-sediment cohesion ×
  fine-grain diameter — the basin family, weakest measured).

Ordering: metal 6,094 ≫ rock 36.92 > ice 0.735 > sand 0.036 > basin 0.0056 —
spread 1.1×10⁶. Liquidity anchor: σ_geo = (6094×36.92×0.735×0.036×0.0056)^(1/5)
≈ **2.05 J/m²**, so α = temp/σ_geo ≈ 5.85 J⁻¹m² at temp = 12.

**The quench caveat, named before the run.** Metal's J/temp = γ/σ_geo ≈ 3,000 —
far past the glass transition. It will not sort; it will freeze where the scramble
left it, aggregating downhill and carrying scramble memory in its core shape. The
prediction is therefore on the RADIUS ORDERING only, not on metal's core being
compact.

**PREDICTION.** A five-material scramble (equal counts, the rung-1 blob protocol)
under the derived 6×6 J, 200 sweeps, sorts by mean radius
**metal < rock < ice < sand < basin**. The uniform contrast's final orientation is
random — it does not systematically order.

**FALSIFIER.** Any inversion in the radius ordering under the derived J between
materials separated by ≥ one decade (metal/rock/ice/sand are each ≥10× apart — a
clean four-way ordering), OR the uniform control systematically ordering. The one
named exception, stated in advance: sand↔basin sit 6.4× apart, inside the
Girifalco-Good default's known factor-~2 error band on interfacial tensions — an
inversion THERE is a GG-precision limit, recorded as such, not reconciled into a
pass.

**Deliberately excluded:** `interior` — the design-material family has no natural
referent, so no measured γ exists; including it would be choosing a number, which
is Rule 1's definition of breaking the chain. It waits for its own membrane.

*VERDICT (2026-08-03, run: `cd Chimera && python -m core.matter_derive --world-full`,
200 sweeps, 96³, run twice — the first died on an instrument lie, the second is the
one of record).* **FIRED — and the firing is the most interesting measurement the
shaker has produced: metal did not freeze as the quench caveat predicted, it
EVAPORATED.** (The run's computed anchor: σ_geo = 2.016 J/m², α = 5.951 J⁻¹m² —
the membrane's ≈2.05 / ≈5.85 estimates, confirmed.)

Measured at 200 sweeps (differential / uniform):

- **metal: radius nan — EXTINCT.** Count drift −27,229 of ~27,451 (0.8% survived
  in the trace run; zero in the parity run — scheduling noise over an extinction).
  The caveat predicted glass-freeze; the lattice did the opposite. Mechanism,
  derived after the fact and checked against the J: an ISOLATED metal site pays
  ~54,403 per contact against its neighbours; annihilating it recovers all six —
  ΔH ≈ −326,000, certain death, λ = 0.9 is a rounding error against it. Freeze
  protects only BULK metal (self-contact 36,269 < interface 54,403, so a formed
  aggregate's interior is stable). A single-grain dispersion of a γ/σ_geo ≈ 3,000
  material is below any critical nucleus: it does not anneal, it dissolves. That
  is real nucleation physics — supersaturated monatomic "vapour" has no stable
  phase — measured here, not reconciled.
- **The survivors ORDERED.** rock 14.5 < ice 15.7 < sand 30.2 — every surviving
  decade pair correct. The chain broke only at metal, by extinction, not inversion.
- **sand/basin INVERTED** (30.2 vs 27.3) — the pre-named GG-precision exception.
  Recorded, per the membrane's own clause; not counted for or against.
- **Uniform control: NOT ordered** (22.0 / 19.3 / 16.9 / 19.2 / 23.8) — falsifier B
  PASS. The survivors' ordering is J-driven, not a protocol artifact.
- **H 12.6×10⁹ → 7.3×10⁸** — the trace of the machine eating the metal. Rock also
  bled (−1,185 cells, 4.3%) but held the core; ice/sand/basin counts stable.

**What survives, published per Rule 17:**

1. **The mapping's ORDERING is right wherever a stable phase exists.** Three of
   three surviving decade pairs ordered; the uniform control did not.
2. **Dispersion is a phase state, and this lattice knows it.** The same γ that
   would make bulk metal the deepest core makes single-grain metal the most
   soluble thing in the world. The quench caveat was wrong about WHICH way
   extreme J/temp manifests — recorded as the caveat's own falsification, not
   edited after the fact.
3. **The named route (a new membrane, the operator's call, not smuggled):** a
   nucleation-seeded protocol — start metal as a bulk SEED, not a dispersion —
   asks the question the scramble couldn't: does the mapping hold metal as the
   core when metal is allowed to exist? Statement/prediction/falsifier before
   that run, as always.
4. **Instrument debt paid en route:** `metrics_3d` hardcoded (BONE, MUSCLE, SKIN) —
   on a five-material world lattice metal (id 4) collided with TENDON and the
   radius dict simply had no key for it. It now takes `types`; default keeps the
   historical tissue-limb behavior byte-for-byte (tendon block included), an
   explicit list gets exactly those radii and no tendon block — a tissue
   instrument pointed at a world grid would return lies. The first run of this
   phase died on exactly that lie (KeyError: 4), which is why it is written down.

**Phase 4 (nucleation) — METAL ALLOWED TO EXIST (membrane stated 2026-08-03,
before the run).** The named route out of the full-families firing, run as its own
theory with its own falsifiers. Nothing below is reconciled after the fact — the
kinetics are derived from the printed 6×6 J *now*.

**STATEMENT.** Extreme γ cuts both ways: the same J that made dispersed metal the
most soluble thing in the world makes BULK metal the most stable phase in the
lattice. The full-families run falsified "dispersed metal freezes"; this membrane
claims the complement — seeded metal persists, and the ordering of the other four
materials is undisturbed by its presence.

**THE DERIVED KINETICS (Rule 1 — trace the variables before the run).** From the
printed J (lattice units): J(4,4) = 36,268.7 · J(4,0) = 54,403.1 · J(4,1) =
54,227.1 · J(1,1) = 0.2. A metal site with k metal neighbours, proposed flip to
sand:

- **Corner (k = 3):** ΔH = 3×(J(1,1) − J(4,4)) = −108,806 → certain death.
  Corners ERODE.
- **Flat face (k = 5):** ΔH = 5×(J(1,4) − J(4,4)) + (J(1,1) − J(1,4)) = +35,565 →
  e^(−2,964) — frozen. Faces PERSIST.
- **Crevice (a sand site with 5 metal neighbours):** ΔH = 5×(J(4,4) − J(1,4)) +
  (J(1,4) − J(1,1)) = −35,565 → certain conversion. Crevices FILL.

So a compact seed cannot be invaded through a flat face, loses its corners, fills
its crevices: it FACETS and stops. It does not migrate (every positional move
crosses a frozen face), so this membrane makes NO claim about metal finding the
core — only about metal existing.

**THE PROTOCOL.** Two compact metal seeds (r = 12, centres 28 apart, offset ±14
OFF the z axis so their cylindrical radius ≈ 14 — inside the blob, not at its
centre; core-position is earned, not baked in). The rest of the blob scrambles
over rock/ice/sand/basin as before. Same derived 6×6 J, same anchor, temp = 12,
200 sweeps, uniform contrast on the same seeded start.

**PREDICTION.** Under the derived J at 200 sweeps: (1) metal SURVIVES — ≥ 60% of
the seeded cells remain (the dispersion run kept 0.8%); (2) metal stays COMPACT —
mean cylindrical radius within ±20% of the seeds' initial ≈ 14 (faceting, not
dispersal); (3) the four scrambled materials still sort rock < ice < sand; (4)
under the uniform contrast the same seeds DISPERSE — radius inflates toward
scramble level (≥ 18).

**FALSIFIER.** Any one of: (A) metal survival < 50% under the derived J — the
bulk-stability claim is dead; (B) metal radius inflation > 20% under the derived
J — it disperses anyway; (C) a decade-pair inversion among rock/ice/sand; (D) the
uniform control ALSO keeps the seeds compact (< 20% inflation) — survival would
be a protocol artifact, not J-driven. The sand↔basin GG-precision exception of
the full-families membrane carries over unchanged.

*VERDICT (2026-08-03, run: `cd Chimera && python -m core.matter_derive --world-seed`,
200 sweeps, 96³, two r=12 seeds, 14,246 metal cells).* **FIRED — A, B and D all
fired, and the post-mortem derivation is the prize: the membrane's own kinetics
were derived for the WRONG NEIGHBOURHOOD. The machine runs 18-connectivity; the
membrane derived 6. Published as the error it is.**

Measured:

- **Metal extinct again: 0 / 14,246.** Not slowed, not faceted — eaten. The
  seeded protocol changed nothing, and now we know exactly why (below).
- **Falsifier C PASS:** rock 13.9 < ice 18.3 < sand 31.2 — the ordering is
  undisturbed while the machine eats the metal. (basin 35.9, GG band.)
- **Falsifier D fired honestly:** the uniform control kept the seeds (14,230 /
  14,246, inflation 8%) — with J = 8/4 the face stability is +32 (cohesion
  symmetric), so seeds simply sit there; 200 sweeps is not dispersal timescale.
  The control could not judge J-drivenness on this protocol. Recorded, not
  reconciled.

**The correct kinetics (derived after the firing, from the same J, checked
against the kernel's 18-neighbourhood — `matter_gpu.py:111`):**

A flat-face cell of type a against material b carries 13 same-type and 5 b-type
contacts (6-connectivity would say 5 and 1 — the membrane's error). It erodes
iff `13×(J_ab − J_aa) < 5×(J_ab − J_bb)` — interface-avoidance against five
expensive contacts beats loyalty to thirteen cheap ones. For metal-on-sand:
233k < 271k → **the face ALWAYS erodes, irreversibly, layer by layer.** There is
no frozen face at any compactness; "faceting" never happens.

So survival is not the face's question at all — it is the λ jail's. Eroding a
cell from a type running deficit D costs the area marginal λ(2D−1), so the
jail's maximum restoring force is ~2λ×target. **A type survives iff its
face-erosion drive < 2λ×(its population).** The numbers, both runs:

- metal: drive 37,676 vs jail max 0.9×2×14,246 = 25,642 → **extinct at ANY seed
  size this lattice can hold.** The dispersion and the seed are one mechanism,
  two protocols — the corrected condition predicts both extinctions.
- rock: drive ~326 vs jail ~55k → lives; it paid 1,161 cells (4%) before the
  deficit's restoring force (~2,090) swamped the drive. The −1,161 bleed in the
  full-families run is this equilibrium, now derived.

**What survives, published per Rule 17:**

1. **Metal has no stable finite phase in this shaker, period.** Not dispersed,
   not seeded: its erosion drive exceeds the largest jail its population can
   raise. The machine can only represent metal as an extinction event — and now
   the extinction is an equation, not a surprise.
2. **The survival condition `drive < 2λ×population` is the derived law** that
   reconciles three runs (dispersion, seed, rock's 4% bleed) with zero fitted
   numbers.
3. **The neighbourhood error is the ledger's entry:** a membrane's derivation
   must use the machine's actual connectivity (18), not the textbook's (6). The
   instrument did not lie; the derivation did.
4. **Named routes if metal must exist (operator's call, new membranes):** raise
   λ for metal alone until 2λ_m×T_m > 37,676 (λ_m ≥ 1.4 — but Phase 5 measured
   what derived λ does to dynamics), or give metal a frozen_type skeleton
   (structure, not tissue — the kernel already supports it). Neither is
   smuggled into this verdict.

**Phase 4 — THE WORLD.** Extend the mapping to the library's world families
(mineral_dry, metallic, cryo) using their researched cohesion/grain-size; then the
story terms that do not exist yet (`thePlant`, `theRock`… — named by the operator,
per the iron rule that the agent does not pick the term). Grass bending underfoot is
a passive-port property of a grown lattice, not a scripted sway.

**Explicitly NOT in this theory:** cell division, growth-as-increase (the lattice
cannot represent it — medium is the only reservoir), and any coupling of the story
tree's `numbers.json` into the shaker. Both are later membranes with their own
theories. This one is scoped to lose cleanly.

**Phase 6 — THE METAL JAIL (stated 2026-08-04, before the run; the operator's call
made: per-type λ — M7's "metal via per-type λ ≥ 1.4 or a frozen_type skeleton,"
λ route chosen first since the kernel already carries it).**

**STATEMENT.** The survival law derived from three extinction runs — a type survives
iff its face-erosion drive < 2λ×(its population) — is a REVERSIBLE law, not a
post-hoc fit over one operating point. Metal's numbers: drive 37,676; population
14,246 (n=96 seed protocol); jail at λ = 0.9: 25,642 → extinct, measured twice
(dispersion kept 0.008; seed 0/14,246). Raising metal's λ ALONE to 1.4 raises its
jail to 2×1.4×14,246 = 39,889 > 37,676, while every other family keeps λ = 0.9 and
its recorded equilibrium. If the law is real, the seeded metal phase survives the
exact protocol that killed it. Per-type λ here is jail strength (mass conservation),
NOT bulk modulus — Phase 5's verdict is untouched; this membrane tests population
pinning only. Someone can disagree: the law was derived at ONE λ; its λ-linearity
is the unmeasured clause, and the drive may itself shift as the seed compacts (its
surface stops being all-free-face).

**PREDICTION (not yet measured).** The `--world-seed` protocol, unchanged except
`lam = {metal 1.4, sand/rock/ice/basin 0.9}`: metal survival ≥ 50% (the protocol's
own falsifier-A bar — it returned 0.008 dispersed and 0.000 seeded at uniform
λ = 0.9), seed compactness inflation ≤ 20%, and rock < ice < sand ordering
preserved.

**FALSIFIERS (named before the run).**

1. **Survival < 50% at λ_m = 1.4** — the law's λ-linearity fails at its first
   extrapolation, and the reconciliation of three runs collapses with it. One named
   diagnostic follows, not a sweep: λ_m = 2.8 (2× threshold). If 2.8 rescues, the
   FORM survives and the coefficient 2 is wrong; if 2.8 fails too, the form is dead
   and frozen_type skeleton is the only metal route.
2. **Margin is noise** — survival at 1.4 lands at the bar (0.45–0.55), i.e. the
   derived 5.9% jail margin (39,889 vs 37,676) does not separate life from death;
   the law's constants are softer than published.
3. **Leak** — raising metal's λ disturbs the other families: count drift beyond
   recorded equilibria (rock's bleed ≫ 4%) or the rock < ice < sand ordering
   inverts. The jail is then not type-local; per-type λ leaks through the shared
   interface dynamics.

*VERDICT (2026-08-04, runs: `cd Chimera && python -m core.matter_derive
--metal-jail` and `--metal-jail --lam-m 2.8`, 200 sweeps, 96³, the exact
nucleation protocol).* **FIRED — falsifier 1 at BOTH points. The law's FORM is
dead: `drive < 2λ×population` is not the survival condition. Per-type λ cannot
jail metal at any tested strength; the frozen_type skeleton is the only named
route left.**

Measured:

- **λ_m = 1.4 (jail 39,889, margin +5.9%): metal 0/14,246.** The differential
  arm ate the seeds exactly as at uniform λ = 0.9. The uniform control kept
  them (14,236/14,246) — the extinction is J-driven, not protocol.
- **λ_m = 2.8 (jail 79,778, margin +112%): metal 0/14,246.** The pre-named
  diagnostic, and it is the decisive one: doubling the predicted-sufficient
  jail changed NOTHING. Not a softer coefficient — the functional form is
  wrong. Falsifier 2's noise band is moot: extinction at +112% margin kills
  the constants and the form together.
- **Falsifier 3 PASS at both points:** rock < ice < sand preserved (14.0 <
  20.5 < 28.2 at 1.4; 14.1 < 17.2 < 34.2 at 2.8), rock's bleed −1,158/−1,173
  vs the recorded −1,161 equilibrium, other drifts ≤ ±215. **The per-type λ
  knob IS type-local** — that clause of the machinery survives and is now
  measured, even though it cannot jail metal.
- Trace sanity: H falls 5.33e9 → 3.50e8 (1.4) / 6.34e8 (2.8); the machine
  minimizes; the extinction is the minimized state.

**The post-mortem hypothesis (stated, not yet tested).** The law treated the
drive as a constant, and the membrane's own caveat named the hole: erosion is
layer-by-layer from the surface, so as the seed shrinks its surface-per-cell
RISES and the per-cell drive grows with it — a runaway a static inequality
cannot jail at any finite λ. The equilibrium reading of the dead law predicted
erosion should stop at deficit D* = drive/2λ (13,456 at 1.4, 6,728 at 2.8 —
53% survival at 2.8, above the bar); measured 0 at both, consistent with a
drive that grows as D grows. This mechanism is a claim to be tested by the
frozen_type membrane's design run, not by another λ point — the λ question is
CLOSED by the two extinctions above.

**What survives, published per Rule 17:**

1. **`drive < 2λ×population` is dead as a survival law.** It reconciled three
   runs at one λ and failed its first extrapolation twice. The three-run
   reconciliation is now recorded as coincidence of operating point, not law.
2. **Per-type λ is a measured type-local population jail** (leak checks pass
   at 1.4 and 2.8) — useful machinery, wrong tool for metal.
3. **Metal's only named route is the frozen_type skeleton** (structure, not
   tissue — `open_lattice(frozen_type=...)`, already in the kernel). Its
   membrane owes the runaway-drive test above.

**Phase 7 — THE RUNAWAY AUTOPSY + THE FROZEN METAL (stated 2026-08-04, before
the run).** Two statements, two small runs, one question each: WHY did the λ
law fail, and CAN metal exist at all.

**STATEMENT A (the autopsy).** Phase 6's post-mortem hypothesis is the
mechanism: erosion proceeds layer-by-layer from the surface, so as the seed
shrinks its surface-per-cell RISES and the per-cell erosion drive grows with
the deficit — a runaway no static λ can jail at any strength. The alternative,
named now so the run can kill it: the law's form is fine and the ledger's
drive constant (37,676) was simply understated — in which case the measured
drive will be FLAT as the deficit grows and per-type λ reopens at a recomputed
point.

**PREDICTION A (not yet measured).** Instrumenting the λ_m = 2.8 erosion (the
strongest jail that still went extinct): the mean per-cell interface gain
among boundary metal cells — computed from the live J as −min over neighbour
types b of Σ_nb (J[b,τ_nb] − J[metal,τ_nb]), no constants — RISES as the
population falls. The bar: the second half of the erosion (by cells lost)
runs ≥ 25% hotter than the first half.

**FALSIFIER A.** The drive is flat or falls as the deficit grows → the
runaway is dead, Phase 6's extinctions are a constants error, and per-type λ
reopens at a recomputed point.

**STATEMENT B (the skeleton).** Metal can exist in this machine as STRUCTURE,
not tissue: `frozen_type=WMETAL` persists by construction — the same frozen
mechanism the bone axis and terrain already run (`matter_gpu.py:14-15`) — and
the living families sort around the skeleton undisturbed. This is the M7
deliverable: metal in the world, as the machine's native scaffold type.

**PREDICTION B (not yet measured).** 200 sweeps, frozen metal: 14,246/14,246
held exactly; rock < ice < sand preserved; rock's bleed inside its recorded
~4% equilibrium band.

**FALSIFIER B.** The skeleton leaks — the ordering inverts or rock's bleed
leaves its recorded band → metal cannot exist even as structure without
changing the world.

*VERDICT (2026-08-04, run: `cd Chimera && python -m core.matter_derive
--frozen-metal`, 200 sweeps, 96³).* **FIRED overall — and the two halves
could not have split more cleanly: the autopsy PASSES decisively (the
runaway is REAL and measured), the skeleton's leak check FIRES on the
geometry (B2).**

**7A — the runaway, measured (falsifier A PASS).** Per-cell drive vs deficit
at λ_m = 2.8, 10-sweep frames:

| sweep | metal left | drive mean | drive median | boundary cells |
|---:|---:|---:|---:|---:|
| 0 | 14,246 | 87,881 | 96,833 | 4,164 |
| 10 | 3,637 | 114,845 | 77,702 | 1,894 |
| 20 | 83 | 396,530 | 386,126 | 83 |
| 30 | 0 | — | — | 0 |

Second half of the erosion runs **2.91× hotter** than the first (bar: 1.25×).
Two clauses land together:

1. **The runaway is real** — the drive per remaining cell QUADRUPLES as the
   seed is eaten, exactly the surface-per-cell mechanism the post-mortem
   named.
2. **The ledger's 37,676 was ALSO understated** — the measured initial drive
   (87,881 mean) is 2.3× the derived constant. So extinction was certain from
   the first flip at any λ: survival needs per-cell drive < 2λD at some
   reachable deficit D < T, and at frame 0 the drive already exceeds the
   largest jail 2λT can raise at λ_m = 2.8 (79,778). Phase 6's double
   extinction was overdetermined — wrong constant AND growing drive. The λ
   question is closed for good: no static jail stops a drive that starts
   above the jail and quadruples.

**7B — the skeleton (B1, B3 PASS; B2 FIRED).** Frozen metal holds
**14,246/14,246 exactly** for 200 sweeps — metal exists in the machine, as
structure, by the same frozen mechanism the bone axis and terrain run. The
living families' populations are undisturbed (rock bleed 3.8% vs the recorded
4% equilibrium; ice/sand/basin drifts ≤ ±13). **But the geometry leaks:**
rock 15.1 < ice 22.8, sand 22.1 — ice and sand INVERTED against the recorded
ordering (Phase 6: 20.5 < 28.2), a 3% margin. The frozen seeds are excluded
volume the sort must flow around, and the ice/sand boundary paid for it.
Caveat recorded with the firing: the margin is 3%, and this machine's
run-to-run variance on radius metrics (acceptance order = hardware
scheduling, seed is not bit-identical) is UNMEASURED for this protocol — the
inversion may be leak, noise, or both. A seed pair to size the instrument's
own noise runs next; the firing stands either way, its reading may change.

*Caveat resolved (same day, `.tmp/frozen_var.py`, seeds 0–2 × frozen/unfrozen,
the exact 7B protocol).* The leak is REAL and systematic; the inversion's
SIGN is scheduling noise. Unfrozen arm: ice/sand gap +15.3/+15.4/+17.6 —
wide and stable. Frozen arm: +10.6/+6.7/+0.0 — the skeleton collapses the
gap by ~12 lattice units on every seed, and at that narrowness the machine's
own scheduling variance (±~5, the same protocol re-run at seed 0 gave −0.7
and +10.6) can flip the sign. So B2's firing reads: **the frozen seeds bend
the sort measurably (the ice/sand boundary is displaced, rock pushed out
14→15, sand's outer shell compressed), and whether ice ends up inside or
outside sand on a given run is the noise on that bend.** The world still
sorts rock < ice < sand in the mean; it does not sort them as cleanly as it
did without a skeleton in the core.

**What survives, published per Rule 17:**

1. **Metal's extinction is a runaway with a wrong constant underneath:**
   drive(0) ≈ 88k, quadrupling to ≈ 397k at extinction; no per-type λ can
   jail it. The question Phase 4 opened is closed with a mechanism, not a
   mystery.
2. **Metal exists as frozen structure** (14,246/14,246, populations of the
   living families untouched) — the M7 deliverable in its minimal form.
3. **The skeleton's geometric leak is recorded with its caveat:** ice/sand
   inversion at 3%, instrument noise unmeasured. Whether frozen metal is
   compatible with a sorted world around it is the open clause.

---

## DEBTS FOUND EN ROUTE (housekeeping, not part of the theory)

- `ChimeraEngine/core/matter.py` is a stale clone of `Chimera/core/matter.py` that
  **raises FileNotFoundError at import** (`matter.py:130` — its library path
  `ChimeraEngine/docs/matter/matter_library.json` does not exist). The live tree is
  `Chimera/`; the clone should be deleted or the path fixed. A module that crashes on
  import is a lie of omission in the folder map.
- `WorldModel/simulation/cave_karst_generation.py` is a syntax error (method body
  dedented to class level, `return` outside any function) and its "3D Cellular
  Automata" header is false — it is a biased random walk plus a closed-form
  dissolution formula. It cannot be imported; nothing can depend on it.
- `splat_level.py:4`'s docstring claims "Ground terrain = Cellular Potts grid". The
  code is a jittered 2D point grid with `rng.choice(['sand','rock','ground'])`
  (`splat_level.py:152-186`). The real grid→splat path is `splat_emit.py`. Fix the
  docstring or wire the claim; a doc that duplicates a fact will drift from it.
- `ChimeraEngine/tests/` has zero matter coverage. Correctness rests on the contrast
  proofs (`parity_report`, `matter.py main()`). Phase 1's energy trace belongs under
  test.

---

## THE OPEN RULINGS (the human's terminals)

1. **ENOUGH on this theory?** Rule on the statement before Phase 1 is built.
2. **The term name.** When Phase 4 arrives, the new world membranes (thePlant? theRock?
   theSoil?) are named by the operator — the engine's rule, not a courtesy.
3. **The kinetic freedom.** The one scale (α through E₀, or equivalently temp) —
   derive-from-physical-temperature and publish the disagreement, or train it against
   a named objective. Both are legal; it is a taste call about which terminal the
   number answers to.
